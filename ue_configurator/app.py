"""Application entry point for UE Config Assistant."""

import logging
import sys
from PySide6.QtWidgets import QApplication

from .ui.project_chooser import ProjectChooser


def main() -> None:
    """Launch the application and configure basic logging."""
    logging.basicConfig(level=logging.INFO)

    def handle_exception(exc_type, exc, tb) -> None:
        logging.exception("Uncaught exception", exc_info=(exc_type, exc, tb))

    sys.excepthook = handle_exception

    app = QApplication([])
    chooser = ProjectChooser()
    chooser.show()
    app.exec()


if __name__ == "__main__":
    main()
