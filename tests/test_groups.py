"""Common-circle correctness vs an independent exhaustive subset oracle."""

import itertools
import math
import random
import unittest
from dataclasses import replace

from mc_finder.domain import Dimension, SearchMode, SearchRequest, StructureLocation
from mc_finder.groups import enclosing_circle, find_groups
from mc_finder.services import SearchCancelledError, SearchService


def hut(x, z):
    return StructureLocation("minecraft:swamp_hut", Dimension.OVERWORLD, x, z)


def brute_radius(points):
    """Enumerate every possible 1/2/3-point support of the optimal circle."""
    circles = [(x, z, 0) for x, z in points]
    for a, b in itertools.combinations(points, 2):
        circles.append(((a[0]+b[0])/2, (a[1]+b[1])/2, math.dist(a, b)/2))
    for a, b, c in itertools.combinations(points, 3):
        ax, az, bx, bz = b[0]-a[0], b[1]-a[1], c[0]-a[0], c[1]-a[1]
        det = 2*(ax*bz-az*bx)
        if not det:
            continue
        aa, bb = ax*ax+az*az, bx*bx+bz*bz
        cx, cz = a[0]+(bz*aa-az*bb)/det, a[1]+(ax*bb-bx*aa)/det
        circles.append((cx, cz, math.dist((cx, cz), a)))
    return min(r for cx, cz, r in circles if all(math.dist((cx, cz), p) <= r+1e-7 for p in points))


class GroupGeometryTests(unittest.TestCase):
    def test_center_need_not_be_a_structure(self):
        groups = find_groups([hut(-3, -4), hut(3, -4), hut(3, 4), hut(-3, 4)], 4, 5, 0, 0)
        self.assertEqual(len(groups), 1)
        self.assertEqual((groups[0].center_x, groups[0].center_z, groups[0].radius), (0, 0, 5))

    def test_chains_and_pairwise_only_triangles_are_rejected(self):
        self.assertEqual(find_groups([hut(0, 0), hut(10, 0), hut(20, 0)], 3, 6, 0, 0), [])
        self.assertEqual(find_groups([hut(0, 0), hut(10, 0), hut(5, 9)], 3, 5.5, 0, 0), [])

    def test_overlapping_groups_without_redundant_subsets(self):
        groups = find_groups([hut(0, 0), hut(8, 0), hut(16, 0)], 2, 5, 0, 0)
        self.assertEqual([{p.x for p in g.members} for g in groups], [{0, 8}, {8, 16}])
        self.assertEqual(find_groups([hut(0, 0)]*4, 4, 200, 0, 0), [])

    def test_minimum_circle_matches_exhaustive_reference(self):
        rng = random.Random(42)
        for _ in range(100):
            points = [(rng.randint(-100, 100), rng.randint(-100, 100)) for _ in range(8)]
            self.assertAlmostEqual(enclosing_circle(points)[2], brute_radius(points), places=6)
        points = [(29_999_970, -29_999_970), (29_999_976, -29_999_962), (29_999_970, -29_999_962)]
        self.assertAlmostEqual(enclosing_circle(points)[2], 5)

    def test_group_enumeration_matches_exhaustive_subsets(self):
        rng = random.Random(51)
        for _ in range(30):
            coords = sorted({(rng.randint(-10, 10), rng.randint(-10, 10)) for _ in range(7)})
            feasible = []
            for size in range(3, len(coords)+1):
                for subset in itertools.combinations(coords, size):
                    if brute_radius(subset) <= 5+1e-7:
                        feasible.append(frozenset(subset))
            expected = {s for s in feasible if not any(s < other for other in feasible)}
            actual = {frozenset((p.x, p.z) for p in g.members)
                      for g in find_groups([hut(*p) for p in coords], 3, 5, 0, 0)}
            self.assertEqual(actual, expected)

    def test_cancellation_and_validation(self):
        with self.assertRaises(SearchCancelledError):
            find_groups([hut(0, 0), hut(1, 0)], 2, 200, 0, 0, cancelled=lambda: True)
        for minimum, radius in [(1, 200), (2, 0), (2, 5001)]:
            with self.assertRaises(ValueError):
                find_groups([], minimum, radius, 0, 0)


class GroupEngineTests(unittest.TestCase):
    def test_seed_groups_members_and_progress(self):
        request = SearchRequest(5067257298883736067, "26.3", Dimension.OVERWORLD,
                                "minecraft:swamp_hut", SearchMode.GROUP, -2599, 1953, 10000, 2, 200)
        events = []
        service = SearchService()
        groups = service.search(request, progress=lambda done, total: events.append(done/total))
        self.assertEqual(len(groups), 3)
        self.assertEqual((groups[0].center_x, groups[0].center_z), (-2552, 616))
        self.assertEqual([(p.x, p.z) for p in groups[0].members], [(-2736, 576), (-2368, 656)])
        area = set(service.search(replace(request, mode=SearchMode.AREA)))
        for group in groups:
            self.assertGreaterEqual(len(group.members), 2)
            self.assertLessEqual(group.radius, 200+1e-7)
            self.assertTrue(set(group.members) <= area)
            self.assertTrue(all(math.hypot(p.x-group.center_x, p.z-group.center_z) <= 200+1e-7 for p in group.members))
        self.assertEqual(events, sorted(events))
        self.assertEqual(events[-1], 1)
        self.assertEqual(service.search(replace(request, minimum_count=4)), [])
        with self.assertRaises(ValueError):
            service.search(replace(request, group_radius=5001))
        stop = [False]

        def cancel_during_grouping(done, total):
            if done/total > .75:
                stop[0] = True

        with self.assertRaises(SearchCancelledError):
            service.search(request, progress=cancel_during_grouping, cancelled=lambda: stop[0])


if __name__ == "__main__":
    unittest.main()
