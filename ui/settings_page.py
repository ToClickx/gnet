from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QGroupBox, QFormLayout, QMessageBox,
)


class SettingsPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        title = QLabel("Settings")
        title.setStyleSheet("font-size: 26px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)

        store_box = QGroupBox("App Store (GitHub)")
        store_box.setStyleSheet("""
            QGroupBox { color: #dddddd; font-weight: bold; border: 1px solid #3b82f6;
                        border-radius: 12px; margin-top: 10px; padding: 12px; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
        """)
        store_form = QFormLayout(store_box)

        self.owner_edit = QLineEdit()
        self.repo_edit = QLineEdit()
        self.branch_edit = QLineEdit()
        store_form.addRow("Owner:", self.owner_edit)
        store_form.addRow("Repository:", self.repo_edit)
        store_form.addRow("Branch:", self.branch_edit)

        store_hint = QLabel(
            "Apps are downloaded from the apps/ folder of this GitHub repository."
        )
        store_hint.setStyleSheet("color: #888888; font-size: 12px;")
        store_form.addRow(store_hint)

        save_btn = QPushButton("Save")
        save_btn.setFixedSize(120, 36)
        save_btn.clicked.connect(self.save_settings)
        store_form.addRow(save_btn)

        layout.addWidget(store_box)

        about_box = QGroupBox("About")
        about_box.setStyleSheet("""
            QGroupBox { color: #dddddd; font-weight: bold; border: 1px solid #444444;
                        border-radius: 12px; margin-top: 10px; padding: 12px; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
        """)
        about_form = QFormLayout(about_box)
        about_form.addRow("Version:", QLabel("gNet 2.0.0"))
        about_form.addRow("Made with:", QLabel("Python + PyQt6"))
        layout.addWidget(about_box)

        layout.addStretch()

    def load_settings(self):
        self.owner_edit.setText(self.main_window.settings.get("store_owner"))
        self.repo_edit.setText(self.main_window.settings.get("store_repo"))
        self.branch_edit.setText(self.main_window.settings.get("store_branch"))

    def save_settings(self):
        self.main_window.settings.set("store_owner", self.owner_edit.text().strip() or "ToClickx")
        self.main_window.settings.set("store_repo", self.repo_edit.text().strip() or "gnet")
        self.main_window.settings.set("store_branch", self.branch_edit.text().strip() or "main")
        self.main_window.settings.save()
        self.main_window.app_browser_page.load_settings_into_edits()
        QMessageBox.information(self, "Saved", "Settings saved.")