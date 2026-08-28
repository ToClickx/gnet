import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QStackedWidget,
)
from PyQt6.QtCore import Qt

from user.manager import UserManager
from core.settings import AppSettings
from core.app_manager import AppManager
from ui.home_page import HomePage
from ui.app_browser_page import AppBrowserPage
from ui.settings_page import SettingsPage
from ui.user_profile_page import UserProfilePage

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STYLE_QSS = os.path.join(BASE_DIR, "style.qss")
with open(STYLE_QSS, encoding="utf-8") as _f:
    style = _f.read()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("gNet 2")
        self.setMinimumSize(1200, 800)

        self.settings = AppSettings()
        self.user_manager = UserManager()
        self.app_manager = AppManager()

        # Set up main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create sidebar
        sidebar = QWidget()
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet("background-color: #2a2a2a; border-right: 2px solid #3b82f6;")
        nav_layout = QVBoxLayout(sidebar)
        nav_layout.setContentsMargins(25, 40, 25, 40)
        nav_layout.setSpacing(12)

        logo = QLabel("gNet 2")
        logo.setStyleSheet("color: #3b82f6; font-size: 22px; font-weight: bold; padding-bottom: 20px;")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_layout.addWidget(logo)

        # navigation buttons
        self.nav_buttons = {}
        for name, key in [
            ("Home", "home"),
            ("Apps", "apps"),
            ("Settings", "settings"),
            ("Profile", "profile"),
        ]:
            btn = QPushButton(name)
            btn.setFixedSize(200, 48)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, k=key: self.show_page(k))
            nav_layout.addWidget(btn)
            self.nav_buttons[key] = btn

        nav_layout.addStretch()

        self.user_label = QLabel("Not logged in")
        self.user_label.setStyleSheet("color: #888888;")
        self.user_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_layout.addWidget(self.user_label)

        # Create content area with stacked pages
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color: #1e1e1e;")

        self.home_page = HomePage(self)
        self.app_browser_page = AppBrowserPage(self)
        self.settings_page = SettingsPage(self)
        self.profile_page = UserProfilePage(self)

        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.app_browser_page)
        self.stack.addWidget(self.settings_page)
        self.stack.addWidget(self.profile_page)

        layout.addWidget(sidebar)
        layout.addWidget(self.stack, 1)

        # Apply custom style
        self.setStyleSheet(style)

        self.show_page("home")

    def show_page(self, key: str):
        pages = {
            "home": self.home_page,
            "apps": self.app_browser_page,
            "settings": self.settings_page,
            "profile": self.profile_page,
        }
        widget = pages.get(key)
        if widget is None:
            return
        self.stack.setCurrentWidget(widget)
        for k, btn in self.nav_buttons.items():
            btn.setChecked(k == key)

        # refresh page-specific content
        if key == "apps":
            self.app_browser_page.refresh_all()
        elif key == "settings":
            self.settings_page.load_settings()
        elif key == "profile":
            self.profile_page.refresh()
        elif key == "home":
            self.home_page.refresh()

    def on_user_changed(self):
        user = self.user_manager.current_user()
        if user:
            self.user_label.setText(user.username)
        else:
            self.user_label.setText("Not logged in")
        self.home_page.refresh()
        self.profile_page.refresh()