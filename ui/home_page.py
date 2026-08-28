from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt


class HomePage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(16)

        title = QLabel("gNet 2")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 40px; font-weight: bold; color: #3b82f6;")
        layout.addWidget(title)

        self.subtitle = QLabel()
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle.setStyleSheet("font-size: 16px; color: #aaaaaa;")
        layout.addWidget(self.subtitle)

        self.status = QLabel()
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setStyleSheet("font-size: 14px; color: #dddddd;")
        layout.addWidget(self.status)

        spacer = QWidget()
        spacer.setFixedHeight(30)
        layout.addWidget(spacer)

        row = QHBoxLayout()
        row.addStretch()

        btn_apps = QPushButton("Browse Apps")
        btn_apps.setFixedSize(180, 44)
        btn_apps.clicked.connect(lambda: self.main_window.show_page("apps"))
        row.addWidget(btn_apps)

        btn_settings = QPushButton("Settings")
        btn_settings.setFixedSize(180, 44)
        btn_settings.clicked.connect(lambda: self.main_window.show_page("settings"))
        row.addWidget(btn_settings)

        btn_profile = QPushButton("Profile")
        btn_profile.setFixedSize(180, 44)
        btn_profile.clicked.connect(lambda: self.main_window.show_page("profile"))
        row.addWidget(btn_profile)

        row.addStretch()
        layout.addLayout(row)

        layout.addStretch()

    def refresh(self):
        user = self.main_window.user_manager.current_user()
        apps = self.main_window.app_manager.installed_apps()
        if user:
            self.subtitle.setText(f"Welcome back, {user.username}!")
            self.status.setText(
                f"Installed apps: {len(apps)}    |    gBalance: ${user.gBalance:.2f}"
            )
        else:
            self.subtitle.setText("A sandboxed desktop app platform")
            self.status.setText(
                f"Installed apps: {len(apps)}\nLog in on the Profile page to use apps."
            )