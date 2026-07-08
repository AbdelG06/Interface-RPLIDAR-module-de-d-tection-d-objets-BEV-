import sys
import logging
from pathlib import Path

from PySide6.QtWidgets import QApplication

from main_window import MainWindow
from theme import DARK_THEME


def main():

    # Configure logging to file and stdout
    log_dir = Path(__file__).with_name("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "app.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(str(log_file), encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )

    logging.getLogger(__name__).info("Starting application")

    app = QApplication(sys.argv)

    app.setStyleSheet(
        DARK_THEME
    )

    window = MainWindow()

    window.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()