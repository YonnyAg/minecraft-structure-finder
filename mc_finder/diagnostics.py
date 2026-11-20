"""Developer smoke check run by the frozen executable, using its actual GUI.

Invoked only by --self-test-report <file>; not part of the normal user flow.
"""

import json
import sys
import traceback
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from .window import MainWindow


def run(report_path: str) -> int:
    output = Path(report_path).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    app = QApplication([])
    app.setStyle("Fusion")
    window = MainWindow()
    checks: list[str] = []
    stage = [0]
    finished = [False]
    return_code = [1]

    def stop_when_ready():
        if window.worker is not None:
            window.cancel_search()
            QTimer.singleShot(20, stop_when_ready)
        else:
            window.close()
            app.quit()

    def finish(error: str | None = None):
        if finished[0]:
            return
        finished[0] = True
        return_code[0] = 1 if error else 0
        report = {"ok": error is None, "frozen": bool(getattr(sys, "frozen", False)),
                  "executable": sys.executable, "checks": checks, "error": error}
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        stop_when_ready()

    def poll():
        if finished[0]:
            return
        try:
            if window.worker is not None:
                QTimer.singleShot(20, poll)
                return
            if stage[0] == 0:
                window.load_example()
                window.start_search()
            elif stage[0] == 1:
                assert window.table.rowCount() == 1, window.feedback.text()
                assert window.table.item(0, 1).text() == "-2368"
                checks.append("nearest_hut")
                window.mode.setCurrentIndex(1)
                window.start_search()
            elif stage[0] == 2:
                assert window.table.rowCount() == 24, window.feedback.text()
                checks.append("24_huts_in_area")
                window.mode.setCurrentIndex(2)
                window.minimum_count.setValue(2)
                window.start_search()
            elif stage[0] == 3:
                assert window.group_table.rowCount() == 3, window.feedback.text()
                checks.append("3_groups")
                window.group_perimeter_button.click()
                plan = window.perimeter_panel.plan
                assert plan.total_chunks == 289
                assert (plan.min_x, plan.max_x, plan.min_z, plan.max_z) == (-2688, -2417, 480, 751)
                checks.append("perimeter_289_chunks")
                window.perimeter_panel.copy_button.click()
                assert "-2688" in app.clipboard().text()
                checks.append("clipboard")
                window.grab().save(str(output.with_suffix(".png")))
                window.search_radius.setValue(50_000)
                window.start_search()
                window.cancel_search()
            elif stage[0] == 4:
                assert "cancelada" in window.feedback.text(), window.feedback.text()
                checks.append("cancellation")
                finish()
                return
            stage[0] += 1
            QTimer.singleShot(20, poll)
        except Exception:
            finish(traceback.format_exc())

    window.show()
    QTimer.singleShot(0, poll)
    QTimer.singleShot(60_000, lambda: finish("Self-test timed out"))
    app.exec()
    return return_code[0]
