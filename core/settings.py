import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_PATH = os.path.join(BASE_DIR, "config.json")

DEFAULTS = {
    "store_owner": "ToClickx",
    "store_repo": "gnet",
    "store_branch": "main",
}

class AppSettings:
    def __init__(self, path: str = SETTINGS_PATH):
        self.path = path
        self.data = dict(DEFAULTS)
        self.load()

    def load(self) -> None:
        if os.path.isfile(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self.data.update(json.load(f))
            except (json.JSONDecodeError, OSError):
                pass

    def save(self) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4)

    def get(self, key: str, default=None):
        return self.data.get(key, default)

    def set(self, key: str, value) -> None:
        self.data[key] = value

    def reset(self) -> None:
        self.data = dict(DEFAULTS)