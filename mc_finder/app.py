import sys

from PySide6.QtWidgets import QApplication

from .window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Minecraft Structure Finder")
    app.setOrganizationName("MC Finder")
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    return app.exec()
