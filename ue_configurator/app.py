"""Application entry point for UE Config Assistant."""

from PySide6.QtWidgets import QApplication

from .ui.project_chooser import ProjectChooser


def main():
    app = QApplication([])
    chooser = ProjectChooser()
    chooser.show()
    app.exec()


if __name__ == "__main__":
    main()
