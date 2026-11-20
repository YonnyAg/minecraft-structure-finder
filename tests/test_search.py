"""Integration fixtures from Cubiomes; these are not in-game verification."""
import os
import time
import unittest
from dataclasses import replace
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication, QEvent
from mc_finder.domain import Dimension, SearchMode, SearchRequest
from mc_finder.engine import CubiomesEngine
from mc_finder.services import EngineNotAvailableError, SearchCancelledError, SearchService
from mc_finder.window import MainWindow

EXAMPLE = SearchRequest(5067257298883736067, "26.3", Dimension.OVERWORLD,
                        "minecraft:swamp_hut", SearchMode.AREA, -2599, 1953, 10_000)


class SearchIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.service = SearchService()

    def test_sorted_results_and_nearest(self):
        results = self.service.search(EXAMPLE)
        self.assertEqual(len(results), 24)
        self.assertEqual((results[0].x, results[0].z), (-2368, 656))
        distances = [(p.x-EXAMPLE.origin_x)**2 + (p.z-EXAMPLE.origin_z)**2 for p in results]
        self.assertEqual(distances, sorted(distances))
        self.assertTrue(all(d <= EXAMPLE.search_radius**2 for d in distances))
        self.assertEqual(len({(p.x, p.z) for p in results}), len(results))
        self.assertEqual(self.service.search(replace(EXAMPLE, mode=SearchMode.NEAREST)), results[:1])

    def test_circle_boundary_and_negative_regions(self):
        request = replace(EXAMPLE, origin_x=-2371, origin_z=652, search_radius=5)
        self.assertEqual([(p.x, p.z) for p in self.service.search(request)], [(-2368, 656)])
        self.assertEqual(self.service.search(replace(request, search_radius=4)), [])
        self.assertEqual(self.service.search(replace(request, origin_x=-2372)), [])

    def test_extreme_and_negative_seeds(self):
        for seed in (0, -1, -(2**63), 2**63-1):
            with self.subTest(seed=seed):
                request = replace(EXAMPLE, seed=seed, search_radius=1000)
                self.assertEqual(self.service.search(request), self.service.search(request))

    def test_progress_and_cancellation(self):
        progress = []
        self.service.search(EXAMPLE, progress=lambda done, total: progress.append((done, total)))
        self.assertEqual(progress[0][0], 0)
        self.assertEqual(progress[-1][0], progress[-1][1])
        self.assertEqual([v[0] for v in progress], sorted(v[0] for v in progress))
        with self.assertRaises(SearchCancelledError):
            self.service.search(EXAMPLE, cancelled=lambda: True)
        self.assertEqual(len(self.service.search(EXAMPLE)), 24)

    def test_unsupported_queries_fail_explicitly(self):
        for request in (replace(EXAMPLE, mode=SearchMode.GROUP, minimum_count=1),
                        replace(EXAMPLE, dimension=Dimension.NETHER, structure_id="minecraft:fortress"),
                        replace(EXAMPLE, search_radius=50_001),
                        replace(EXAMPLE, origin_x=30_000_000), replace(EXAMPLE, seed=2**63)):
            with self.subTest(request=request), self.assertRaises(ValueError):
                self.service.search(request)

    def test_missing_library_is_not_empty_results(self):
        with self.assertRaises(EngineNotAvailableError):
            CubiomesEngine(Path("missing.dll")).search(EXAMPLE)


class WindowIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = MainWindow()
        self.window.show()
        self.app.processEvents()

    def wait_for_search(self):
        deadline = time.monotonic() + 10
        while self.window.worker is not None and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(.005)
        self.assertIsNone(self.window.worker)

    def tearDown(self):
        self.window.cancel_search()
        self.wait_for_search()
        self.window.close()
        self.window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.window = None
        self.app.processEvents()

    def test_real_search_copy_and_invalidation(self):
        w = self.window
        w.load_example()
        w.mode.setCurrentIndex(1)
        w.prepare_button.click()
        self.assertFalse(w.world_panel.isEnabled())
        self.wait_for_search()
        self.assertEqual(w.table.rowCount(), 24)
        self.assertEqual(w.table.item(0, 1).text(), "-2368")
        w.table.selectRow(0)
        w.copy_coordinates_button.click()
        self.assertEqual(self.app.clipboard().text(), "X: -2368, Z: 656")
        self.assertTrue(w.world_panel.isEnabled())
        self.assertGreater(w.origin_x.lineEdit().width(), 20)
        w.origin_x.setValue(0)
        self.assertEqual(w.table.rowCount(), 0)
        self.assertFalse(w.copy_coordinates_button.isEnabled())

    def test_cancel_and_close_while_searching(self):
        w = self.window
        w.load_example()
        w.search_radius.setValue(50_000)
        w.start_search()
        w.cancel_button.click()
        self.wait_for_search()
        self.assertIn("cancelada", w.feedback.text())
        self.assertEqual(w.table.rowCount(), 0)
        w.start_search()
        w.close()
        self.wait_for_search()
        self.assertFalse(w.isVisible())

    def test_group_search_details_copy_and_empty_results(self):
        w = self.window
        w.load_example()
        w.mode.setCurrentIndex(2)
        w.minimum_count.setValue(2)
        w.start_search()
        self.wait_for_search()
        self.assertTrue(w.results_tabs.isTabVisible(w.groups_tab_index))
        self.assertEqual(w.group_table.rowCount(), 3)
        self.assertEqual(w.table.rowCount(), 2)
        w.copy_group_button.click()
        self.assertIn("X: -2552.000000, Z: 616.000000", self.app.clipboard().text())
        self.assertIn("no es un punto AFK", self.app.clipboard().text())
        w.group_perimeter_button.click()
        self.assertEqual(w.results_tabs.currentIndex(), w.perimeter_tab_index)
        self.assertEqual(w.perimeter_panel.plan.center_x, -2552)
        self.assertEqual(w.perimeter_panel.plan.total_chunks, 289)
        w.group_table.selectRow(2)
        self.assertEqual(w.table.rowCount(), 3)
        w.view_group_button.click()
        self.assertEqual(w.results_tabs.currentIndex(), 0)
        w.minimum_count.setValue(4)
        self.assertIsNone(w.perimeter_panel.plan)
        self.assertEqual(w.group_table.rowCount(), 0)
        self.assertFalse(w.copy_group_button.isEnabled())
        w.start_search()
        self.wait_for_search()
        self.assertEqual(w.table.rowCount(), 0)
        self.assertIn("No se encontraron grupos", w.groups_hint.text())
        w.mode.setCurrentIndex(0)
        self.assertFalse(w.results_tabs.isTabVisible(w.groups_tab_index))

    def test_errors_restore_controls(self):
        w = self.window
        w.seed.setText("abc")
        w.start_search()
        self.assertIsNone(w.worker)
        w.service = SearchService(CubiomesEngine(Path("missing-engine.dll")))
        w.load_example()
        w.start_search()
        self.wait_for_search()
        self.assertIn("Falta el motor", w.feedback.text())
        self.assertEqual(w.table.rowCount(), 0)
        self.assertTrue(w.prepare_button.isEnabled())


if __name__ == "__main__":
    unittest.main()
