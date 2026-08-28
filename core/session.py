import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSION_PATH = os.path.join(BASE_DIR, "session.json")


def save(username: str) -> None:
    with open(SESSION_PATH, "w", encoding="utf-8") as f:
        json.dump({"username": username}, f)


def load() -> str | None:
    if os.path.isfile(SESSION_PATH):
        try:
            with open(SESSION_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("username")
        except (json.JSONDecodeError, OSError):
            return None
    return None


def clear() -> None:
    if os.path.isfile(SESSION_PATH):
        try:
            os.remove(SESSION_PATH)
        except OSError:
            pass