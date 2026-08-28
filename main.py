import sys
import traceback
from datetime import datetime
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from ui.main_window import MainWindow


def _handle_exception(exc_type, exc_value, exc_tb):
    detail = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crash.log")
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] {detail}\n")
    except OSError:
        pass
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        return
    try:
        QMessageBox.critical(None, "gNet crashed",
                             f"An unexpected error occurred:\n\n{exc_value}\n\n"
                             f"Details saved to crash.log")
    except Exception:
        pass


def main():
    sys.excepthook = _handle_exception
    app = QApplication(sys.argv)

    from ui.main_window import style
    app.setStyleSheet(style)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()