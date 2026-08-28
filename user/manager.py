import user.storage as storage
from user.account import User
from typing import Optional


class UserManager:
    def __init__(self):
        self.users = storage.load_all_users()
        self._current_user: Optional[User] = None

    def create_user(self, username: str, password: str) -> User:
        if username in self.users:
            raise ValueError(f"User '{username}' already exists.")
        user = User(username, password)
        self._ensure_default_card(user)
        self.users[username] = user
        user.save()
        return user

    def delete_user(self, username: str) -> None:
        if username not in self.users:
            raise ValueError(f"User '{username}' does not exist.")
        storage.delete_user(username)
        del self.users[username]
        if self._current_user and self._current_user.username == username:
            self._current_user = None

    def get_user(self, username: str) -> Optional[User]:
        return self.users.get(username)

    def list_users(self) -> list[str]:
        return list(self.users.keys())

    def login(self, username: str, password: str) -> User:
        user = self.get_user(username)
        if not user:
            raise ValueError("User not found.")
        if not user.check_password(password):
            raise ValueError("Incorrect password.")
        self._ensure_default_card(user)
        self._current_user = user
        return user

    def auto_login(self, username: str) -> User | None:
        user = self.get_user(username)
        if user:
            self._ensure_default_card(user)
            self._current_user = user
        return user

    # ---- helpers ----
    @staticmethod
    def _ensure_default_card(user: User) -> None:
        if not user.debit_cards:
            user.add_debit_card(
                "default", "Default", limit_amount=1000.0,
                limit_percent=1.0, time_window_seconds=86400,
            )

    def logout(self) -> None:
        self._current_user = None

    def is_logged_in(self) -> bool:
        return self._current_user is not None

    def current_user(self) -> Optional[User]:
        return self._current_user
