"""Conservative chunk coverage and reference UI without a world excavation."""
import math
import os
import random
import unittest
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication, QEvent
from mc_finder.perimeter import WORLD_LIMIT, calculate_perimeter
from mc_finder.perimeter_panel import PerimeterPanel


class PerimeterGeometryTests(unittest.TestCase):
    def test_example_reference_and_inclusive_edges(self):
        plan = calculate_perimeter(-2552, 616)
        self.assertEqual((plan.min_chunk_x, plan.max_chunk_x), (-168, -152))
        self.assertEqual((plan.min_chunk_z, plan.max_chunk_z), (30, 46))
        self.assertEqual((plan.min_x, plan.max_x, plan.min_z, plan.max_z), (-2688, -2417, 480, 751))
        self.assertEqual(plan.total_chunks, 289)
        self.assertEqual([d.additional_chunks for d in plan.directions], [8, 8, 8, 8])
        self.assertEqual([d.block for d in plan.directions], [480, 751, -2688, -2417])
        self.assertEqual(plan.max_x-plan.min_x+1, plan.width_chunks*16)

    def test_negative_fractional_coordinates_use_floor(self):
        plan = calculate_perimeter(-.001, -.001)
        self.assertEqual((plan.min_chunk_x, plan.max_chunk_x), (-9, 7))
        self.assertEqual((plan.min_x, plan.max_x), (-144, 127))
        self.assertEqual(calculate_perimeter(0, 0).min_chunk_x, -8)

    def test_projected_circle_fits_and_directions_add_up(self):
        rng = random.Random(128)
        for _ in range(100):
            cx, cz = rng.uniform(-100000, 100000), rng.uniform(-100000, 100000)
            plan = calculate_perimeter(cx, cz)
            self.assertLessEqual(plan.min_x, cx-128)
            self.assertGreaterEqual(plan.max_x+1, cx+128)
            self.assertLessEqual(plan.min_z, cz-128)
            self.assertGreaterEqual(plan.max_z+1, cz+128)
            n, s, w, e = plan.directions
            self.assertEqual(w.additional_chunks+1+e.additional_chunks, plan.width_chunks)
            self.assertEqual(n.additional_chunks+1+s.additional_chunks, plan.depth_chunks)
            for angle in range(0, 360, 5):
                x, z = cx+128*math.cos(math.radians(angle)), cz+128*math.sin(math.radians(angle))
                self.assertLessEqual(plan.min_chunk_x, math.floor(x/16))
                self.assertGreaterEqual(plan.max_chunk_x, math.floor(x/16))
                self.assertLessEqual(plan.min_chunk_z, math.floor(z/16))
                self.assertGreaterEqual(plan.max_chunk_z, math.floor(z/16))

    def test_invalid_values_and_world_edges_fail(self):
        for x, z, radius in [(float("nan"), 0, 128), (0, float("inf"), 128), (0, 0, 0),
                              (0, 0, -1), (0, 0, 1.5), (WORLD_LIMIT, 0, 128), (WORLD_LIMIT-128, 0, 128)]:
            with self.subTest(x=x, z=z, radius=radius), self.assertRaises(ValueError):
                calculate_perimeter(x, z, radius)


class PerimeterPanelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_import_copy_manual_edit_and_failure(self):
        panel = PerimeterPanel()
        panel.use_reference(-2552, 616, "Grupo de ejemplo", 188.3)
        self.assertEqual(panel.boundaries.rowCount(), 4)
        self.assertEqual(panel.plan.total_chunks, 289)
        self.assertIn("supera 128", panel.summary.text())
        panel.copy_button.click()
        text = self.app.clipboard().text()
        self.assertIn("X [-2688, -2417]", text)
        self.assertIn("no activa todas", text)
        panel.invalidate_imported_reference()
        self.assertIsNone(panel.plan)
        self.assertFalse(panel.copy_button.isEnabled())
        panel.calculate()
        self.assertIsNotNone(panel.plan)
        panel.reference_x.setValue(0)
        self.assertIsNone(panel.plan)
        panel.calculate()
        panel.invalidate_imported_reference()
        self.assertIsNotNone(panel.plan)
        panel.reference_x.setValue(WORLD_LIMIT)
        panel.calculate()
        self.assertIsNone(panel.plan)
        self.assertEqual(panel.boundaries.rowCount(), 0)
        self.assertFalse(panel.copy_button.isEnabled())
        panel.close()
        panel.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
