import os
import shutil
from core.app_discovery import discover_apps
from core import app_store

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPS_DIR = os.path.join(BASE_DIR, "apps")


class AppManager:
    def __init__(self):
        self._installed = []
        self.refresh()

    def refresh(self, settings=None) -> list:
        self._installed = discover_apps()
        return self._installed

    def installed_apps(self) -> list:
        return self._installed

    def find_installed(self, app_id: str):
        for app in self._installed:
            if app["id"] == app_id:
                return app
        return None

    def is_installed(self, app_id: str) -> bool:
        return os.path.isdir(os.path.join(APPS_DIR, app_id))

    def installed_store_apps(self, store_apps) -> list:
        """Annotate remote apps with whether they are already installed locally."""
        for sa in store_apps:
            sa.installed = self.is_installed(sa.name)
        return store_apps

    def uninstall(self, app_id: str) -> None:
        folder = os.path.join(APPS_DIR, app_id)
        if os.path.isdir(folder):
            shutil.rmtree(folder, ignore_errors=True)
        self.refresh()

    def download(self, remote: "app_store.RemoteApp") -> str:
        path = app_store.download_app(remote)
        self.refresh()
        return path