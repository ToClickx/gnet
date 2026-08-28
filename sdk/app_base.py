# sdk/app_base.py

from PyQt6.QtWidgets import QWidget
from abc import ABC, abstractmethod


class GNetAppBase(QWidget, ABC):
    """
    Base class all gNet apps must inherit from.

    The app is initialized with a permission-restricted AppBridge,
    rather than direct access to user data or system APIs.
    """

    def __init__(self, app_bridge, parent=None):
        super().__init__(parent)
        self.bridge = app_bridge

    @abstractmethod
    def app_name(self) -> str:
        """Returns the human-readable name of the app."""
        pass

    @abstractmethod
    def app_id(self) -> str:
        """Returns the unique app ID (e.g. 'com.example.myapp')"""
        pass

    @abstractmethod
    def app_version(self) -> str:
        """Returns the app version as a string (e.g. '1.0.0')"""
        pass

    def on_open(self):
        """Called when the app is launched. Override if needed."""
        pass

    def on_close(self):
        """Called when the app is closed. Override if needed."""
        pass
