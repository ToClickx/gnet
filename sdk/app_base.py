# sdk/app_base.py

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import pyqtSignal


class GNetAppBase(QWidget):
    """
    Base class all gNet apps must inherit from.

    The app is initialized with a permission-restricted AppBridge,
    rather than direct access to user data or system APIs.
    """

    closed = pyqtSignal()

    # Display metadata - apps override these as class attributes
    app_name = "Untitled App"
    app_id = "unknown"
    app_version = "0.0.0"
    app_description = ""
    app_icon = None

    def __init__(self, app_bridge, parent=None):
        super().__init__(parent)
        self.bridge = app_bridge

    def closeEvent(self, event):
        try:
            self.on_close()
        finally:
            self.closed.emit()
            event.accept()

    def main(self):
        """Entry point called when the app is launched. Override if needed."""
        pass

    def on_open(self):
        """Called when the app is launched. Override if needed."""
        pass

    def on_close(self):
        """Called when the app is closed. Override if needed."""
        pass