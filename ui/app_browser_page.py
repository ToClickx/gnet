import os
import traceback

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QMessageBox, QFrame, QTabWidget, QLineEdit, QProgressBar,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from core import app_store
from sdk.app_manifest import AppManifest, SemanticVersion
from sdk.app_bridge import AppBridge
from sdk.permissions import AppPermission


class StoreLoader(QThread):
    finished = pyqtSignal(list)
    failed = pyqtSignal(str)

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings

    def run(self):
        try:
            apps = app_store.list_store_apps(
                self.settings.get("store_owner", "ToClickx"),
                self.settings.get("store_repo", "gnet"),
                self.settings.get("store_branch", "main"),
            )
            self.finished.emit(apps)
        except Exception as e:
            self.failed.emit(str(e))


class AppFrame(QFrame):
    def __init__(self, app_info, on_open, on_uninstall=None):
        super().__init__()
        self.app_info = app_info
        self.setStyleSheet("""
            QFrame { background-color: #2a2a2a; border-radius: 12px; padding: 12px; }
            QLabel#name { font-size: 17px; font-weight: bold; color: #ffffff; }
            QLabel#meta { font-size: 12px; color: #888888; }
            QLabel#desc { font-size: 13px; color: #bbbbbb; }
        """)

        layout = QVBoxLayout(self)
        name_row = QHBoxLayout()
        name = QLabel(app_info["name"])
        name.setObjectName("name")
        name_row.addWidget(name)
        name_row.addStretch()
        version = QLabel(f"v{app_info['version']}")
        version.setObjectName("meta")
        name_row.addWidget(version)
        layout.addLayout(name_row)

        desc = QLabel(app_info.get("description") or "No description provided.")
        desc.setObjectName("desc")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        if on_uninstall and self.app_info.get("id"):
            uninstall = QPushButton("Uninstall")
            uninstall.setFixedSize(120, 36)
            uninstall.clicked.connect(lambda: on_uninstall(self.app_info["id"]))
            btn_row.addWidget(uninstall)
        open_btn = QPushButton("Open")
        open_btn.setFixedSize(120, 36)
        open_btn.clicked.connect(lambda: on_open(self.app_info))
        btn_row.addWidget(open_btn)
        layout.addLayout(btn_row)


class StoreAppFrame(QFrame):
    def __init__(self, remote, on_download, on_uninstall, parent_window):
        super().__init__()
        self.remote = remote
        self.parent_window = parent_window
        self.setProperty("store", True)
        self.setStyleSheet("""
            QFrame[store="true"] { background-color: #2f2f2f; border-radius: 12px; padding: 12px; }
            QLabel name { font-size: 17px; font-weight: bold; color: #ffffff; }
            QLabel meta { font-size: 12px; color: #888888; }
        """)

        layout = QVBoxLayout(self)
        row = QHBoxLayout()
        name = QLabel(remote.name)
        name.setStyleSheet("font-size: 17px; font-weight: bold; color: #ffffff;")
        row.addWidget(name)
        row.addStretch()
        meta = QLabel(f"GitHub: {remote.owner}/{remote.repo} @ {remote.branch}")
        meta.setStyleSheet("font-size: 12px; color: #888888;")
        row.addWidget(meta)
        layout.addLayout(row)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        installed = getattr(remote, "installed", False)
        if installed:
            btn = QPushButton("Uninstall")
            btn.setFixedSize(120, 36)
            btn.clicked.connect(lambda: on_uninstall(remote.name))
            btn_row.addWidget(btn)
            btn = QPushButton("Update")
            btn.setFixedSize(120, 36)
            btn.clicked.connect(lambda: on_download(remote))
            btn_row.addWidget(btn)
        else:
            btn = QPushButton("Install")
            btn.setFixedSize(120, 36)
            btn.clicked.connect(lambda: on_download(remote))
            btn_row.addWidget(btn)
        layout.addLayout(btn_row)


class AppBrowserPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.remote_apps = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Apps")
        title.setStyleSheet("font-size: 26px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setStyleSheet("QTabBar::tab { padding: 8px 18px; }")
        layout.addWidget(self.tabs)

        # ——— Installed apps tab ———
        installed_tab = QWidget()
        self._build_installed_tab(installed_tab)
        self.tabs.addTab(installed_tab, "Installed")

        # ——— Store tab ———
        store_tab = QWidget()
        self._build_store_tab(store_tab)
        self.tabs.addTab(store_tab, "Store")

    # ---------- installed ----------
    def _build_installed_tab(self, tab):
        layout = QVBoxLayout(tab)

        bar = QHBoxLayout()
        bar.addStretch()
        refresh = QPushButton("Refresh")
        refresh.setFixedSize(120, 36)
        refresh.clicked.connect(self.refresh)
        bar.addWidget(refresh)
        layout.addLayout(bar)

        self.installed_list = QScrollArea()
        self.installed_list.setWidgetResizable(True)
        self.installed_list.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.installed_container = QWidget()
        self.installed_list.setWidget(self.installed_container)
        self.installed_grid = QVBoxLayout(self.installed_container)
        self.installed_grid.setContentsMargins(4, 4, 4, 4)
        self.installed_grid.setSpacing(12)
        self.installed_grid.addStretch()
        layout.addWidget(self.installed_list)

    # ---------- store ----------
    def _build_store_tab(self, tab):
        layout = QVBoxLayout(tab)

        at_hud = QHBoxLayout()
        at_hud.addWidget(QLabel("Owner:"))
        self.owner_edit = QLineEdit()
        at_hud.addWidget(self.owner_edit)
        at_hud.addWidget(QLabel("Repo:"))
        self.repo_edit = QLineEdit()
        at_hud.addWidget(self.repo_edit)
        at_hud.addWidget(QLabel("Branch:"))
        self.branch_edit = QLineEdit()
        at_hud.addWidget(self.branch_edit)
        at_hud.addStretch()
        self.store_load_btn = QPushButton("Load")
        self.store_load_btn.setFixedSize(120, 36)
        self.store_load_btn.clicked.connect(self.load_store)
        at_hud.addWidget(self.store_load_btn)
        layout.addLayout(at_hud)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        self.store_list = QScrollArea()
        self.store_list.setWidgetResizable(True)
        self.store_container = QWidget()
        self.store_grid = QVBoxLayout(self.store_container)
        self.store_grid.setContentsMargins(4, 4, 4, 4)
        self.store_grid.setSpacing(12)
        self.store_list.setWidget(self.store_container)
        layout.addWidget(self.store_list)

        self.store_status = QLabel("")
        self.store_status.setStyleSheet("color: #888888;")
        layout.addWidget(self.store_status)

    # ---------- actions ----------
    def load_settings_into_edits(self):
        self.owner_edit.setText(self.main_window.settings.get("store_owner"))
        self.repo_edit.setText(self.main_window.settings.get("store_repo"))
        self.branch_edit.setText(self.main_window.settings.get("store_branch"))

    def save_edits_to_settings(self):
        self.main_window.settings.set("store_owner", self.owner_edit.text().strip())
        self.main_window.settings.set("store_repo", self.repo_edit.text().strip())
        self.main_window.settings.set("store_branch", self.branch_edit.text().strip())

    def load_store(self):
        self.save_edits_to_settings()
        self.main_window.settings.save()
        self.progress.setVisible(True)
        self.store_status.setText("Fetching apps from GitHub...")
        self.loader = StoreLoader(self.main_window.settings, self)
        self.loader.finished.connect(self.on_store_loaded)
        self.loader.failed.connect(self.on_store_failed)
        self.loader.start()

    def on_store_loaded(self, apps):
        self.progress.setVisible(False)
        self.remote_apps = self.main_window.app_manager.installed_store_apps(apps)
        self.render_store()

    def on_store_failed(self, msg):
        self.progress.setVisible(False)
        self.store_status.setText("Store load failed.")
        QMessageBox.warning(self, "Store Error", f"Could not reach GitHub store:\n{msg}")

    def render_store(self):
        self._clear_layout(self.store_grid)
        if not self.remote_apps:
            placeholder = QLabel("No apps found in this repository's apps/ folder.")
            placeholder.setStyleSheet("color: #888888; padding: 20px;")
            self.store_grid.addWidget(placeholder)
        else:
            for remote in self.remote_apps:
                self.store_grid.addWidget(StoreAppFrame(
                    remote, self.download_remote, self.uninstall_remote, self,
                ))
            self.store_grid.addStretch()
        self.store_list.setWidget(self.store_container)

    def download_remote(self, remote):
        try:
            path = self.main_window.app_manager.download(remote)
        except Exception as e:
            QMessageBox.critical(
                self, "Download failed",
                f"Could not install app '{remote.name}':\n{e}"
            )
            return
        remote.installed = True
        self.store_status.setText(f"Installed {remote.name}.")
        self.render_store()
        self.refresh()

    def uninstall_remote(self, app_id):
        if not QMessageBox.question(
            self, "Uninstall", f"Remove app '{app_id}' from your device?",
        ) == QMessageBox.StandardButton.Yes:
            return
        try:
            self.main_window.app_manager.uninstall(app_id)
        except Exception as e:
            QMessageBox.warning(self, "Uninstall failed", str(e))
        self.store_status.setText(f"Uninstalled {app_id}.")
        for remote in self.remote_apps:
            if remote.name == app_id:
                remote.installed = False
        self.render_store()
        self.refresh()

    # ---------- installed list ----------
    def refresh(self):
        apps = self.main_window.app_manager.refresh()
        self._render_installed(apps)

    def _render_installed(self, apps):
        self._clear_layout(self.installed_grid)
        if not apps:
            label = QLabel("No apps installed yet. Check the Store tab to download apps.")
            label.setStyleSheet("color: #888888; padding: 20px;")
            self.installed_grid.addWidget(label)
        else:
            for app in apps:
                self.installed_grid.addWidget(
                    AppFrame(app, self.open_app, on_uninstall=self.uninstall_installed)
                )
            self.installed_grid.addStretch()
        self.installed_container.setLayout(self.installed_grid)

    def uninstall_installed(self, app_id):
        self.uninstall_remote(app_id)

    def open_app(self, app_info):
        user = self.main_window.user_manager.current_user()
        if not user:
            QMessageBox.information(
                self, "Login required",
                "Log in on the Profile page before launching apps."
            )
            return

        # build the app widget and show it
        try:
            app_class = app_info.get("class")
            manifest = app_info.get("manifest")
            if not app_class:
                QMessageBox.warning(self, "Open failed",
                                    "No application class found for this app.")
                return

            if not manifest:
                manifest = self._build_manifest(app_info)

            bridge = AppBridge(manifest, user)
            widget = app_class(bridge)
            if not hasattr(widget, "path"):
                widget.path = app_info.get("folder", "")
            if not hasattr(widget, "user"):
                widget.user = user
            widget.setWindowTitle(app_info["name"])
            if hasattr(widget, "main"):
                widget.main()
            widget.on_open()
            widget.show()
        except Exception:
            QMessageBox.critical(
                self, "Open failed",
                "The app crashed on launch:\n\n" + traceback.format_exc()
            )

    @staticmethod
    def _build_manifest(app_info):
        perms = [
            AppPermission.READ_APP_FILES,
            AppPermission.WRITE_APP_FILES,
            AppPermission.READ_USERNAME,
            AppPermission.READ_USER_FIELD,
            AppPermission.WRITE_USER_FIELD,
        ]
        import uuid
        return AppManifest(
            app_id=app_info.get("id", "app"),
            uuid=uuid.uuid4(),
            display_name=app_info.get("name", "App"),
            description=app_info.get("description", ""),
            developer="gNet",
            version=SemanticVersion(1, 0, 0),
            icon_path="",
            entry_point="main.py",
            permissions=perms,
        )

    # ---------- helpers ----------
    @staticmethod
    def _clear_layout(layout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def refresh_all(self):
        self.load_settings_into_edits()
        self.refresh()