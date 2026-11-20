"""Exact common-disc grouping of structure reference positions.

This is not connected-component clustering: chains are not accepted unless all
members fit in the same disc. Supersets replace redundant subsets.
"""

import math
import random
from collections import defaultdict
from itertools import combinations

from .domain import StructureGroup, StructureLocation
from .services import Cancelled, Progress, SearchCancelledError

MAX_GROUP_RADIUS = 5_000
EPSILON = 1e-7  # Blocks, independent of absolute world coordinates.


def enclosing_circle(points: list[tuple[float, float]]) -> tuple[float, float, float]:
    """Randomized incremental minimum enclosing circle, with a fixed local RNG.

Translate first to preserve precision close to Minecraft's world border.
"""
    if not points:
        raise ValueError("Un círculo necesita al menos un punto.")
    ox, oz = points[0]
    shuffled = [(x-ox, z-oz) for x, z in points]
    random.Random(0).shuffle(shuffled)
    cx, cz, radius = shuffled[0][0], shuffled[0][1], 0.0
    for i, p in enumerate(shuffled):
        if math.hypot(p[0]-cx, p[1]-cz) <= radius + EPSILON:
            continue
        cx, cz, radius = p[0], p[1], 0.0
        for j, q in enumerate(shuffled[:i]):
            if math.hypot(q[0]-cx, q[1]-cz) <= radius + EPSILON:
                continue
            cx, cz = (p[0]+q[0])/2, (p[1]+q[1])/2
            radius = math.hypot(p[0]-q[0], p[1]-q[1])/2
            for r in shuffled[:j]:
                if math.hypot(r[0]-cx, r[1]-cz) <= radius + EPSILON:
                    continue
                # Circumcenter relative to p, avoiding large-coordinate squares.
                ax, az = q[0]-p[0], q[1]-p[1]
                bx, bz = r[0]-p[0], r[1]-p[1]
                det = 2 * (ax*bz - az*bx)
                if abs(det) < 1e-12:
                    a, b = max(combinations((p, q, r), 2),
                               key=lambda pair: math.dist(*pair))
                    cx, cz = (a[0]+b[0])/2, (a[1]+b[1])/2
                    radius = math.dist(a, b)/2
                else:
                    aa, bb = ax*ax+az*az, bx*bx+bz*bz
                    cx = p[0] + (bz*aa-az*bb)/det
                    cz = p[1] + (ax*bb-bx*aa)/det
                    radius = math.hypot(cx-p[0], cz-p[1])
    # Account for floating rounding when reporting the actual covering radius.
    radius = max(math.hypot(x-cx, z-cz) for x, z in shuffled)
    return cx+ox, cz+oz, radius


def find_groups(locations: list[StructureLocation], minimum_count: int, radius: float,
                origin_x: int, origin_z: int, *, progress: Progress | None = None,
                cancelled: Cancelled | None = None) -> list[StructureGroup]:
    if minimum_count < 2 or not 0 < radius <= MAX_GROUP_RADIUS:
        raise ValueError("Usa al menos 2 cabañas y un radio de grupo de hasta 5.000 bloques.")

    def check_cancelled():
        if cancelled and cancelled():
            raise SearchCancelledError("Búsqueda cancelada. No se muestran grupos incompletos.")

    check_cancelled()
    if not locations:
        if progress:
            progress(1, 1)
        return []
    if len({(p.dimension, p.structure_id) for p in locations}) != 1:
        raise ValueError("Los grupos deben usar una misma estructura y dimensión.")
    # Unique reference positions prevent duplicate structures inflating a group.
    points = sorted({(p.x, p.z): p for p in locations}.values(), key=lambda p: (p.x, p.z))
    if len(points) < minimum_count:
        if progress:
            progress(1, 1)
        return []
    width = 2 * radius
    grid: dict[tuple[int, int], list[int]] = defaultdict(list)
    for i, p in enumerate(points):
        grid[math.floor(p.x/width), math.floor(p.z/width)].append(i)

    def nearby(x, z):
        gx, gz = math.floor(x/width), math.floor(z/width)
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                yield from grid.get((gx+dx, gz+dz), ())

    candidates: set[frozenset[int]] = set()

    def collect(cx, cz):
        check_cancelled()
        members = frozenset(i for i in nearby(cx, cz)
                            if math.hypot(points[i].x-cx, points[i].z-cz) <= radius+EPSILON)
        if len(members) >= minimum_count:
            candidates.add(members)

    if progress:
        progress(0, len(points))
    for i, p in enumerate(points):
        check_cancelled()
        collect(p.x, p.z)
        for j in nearby(p.x, p.z):
            if j <= i:
                continue
            q = points[j]
            dx, dz = q.x-p.x, q.z-p.z
            distance = math.hypot(dx, dz)
            if distance > 2*radius+EPSILON:
                continue
            # Two possible centers of a radius-R disc through p and q.
            mx, mz = (p.x+q.x)/2, (p.z+q.z)/2
            h = math.sqrt(max(0.0, radius*radius-distance*distance/4))
            nx, nz = -dz/distance*h, dx/distance*h
            collect(mx+nx, mz+nz)
            collect(mx-nx, mz-nz)
        if progress:
            progress(i+1, len(points))

    maximal: list[frozenset[int]] = []
    for candidate in sorted(candidates, key=lambda ids: (-len(ids), tuple(sorted(ids)))):
        check_cancelled()
        if not any(candidate <= other for other in maximal):
            maximal.append(candidate)
    groups = []
    for ids in maximal:
        check_cancelled()
        members = tuple(points[i] for i in sorted(ids))
        cx, cz, required = enclosing_circle([(p.x, p.z) for p in members])
        if required <= radius+EPSILON:
            groups.append(StructureGroup(members, cx, cz, required))
    groups.sort(key=lambda g: ((g.center_x-origin_x)**2+(g.center_z-origin_z)**2,
                              g.radius, -len(g.members), g.center_x, g.center_z))
    check_cancelled()
    return groups
