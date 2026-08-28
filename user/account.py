import hashlib
import datetime
import user.storage as storage
from typing import Optional, Dict, Any
from user.debit_card_manager import DebitCardManager


class User:
    """
    Represents a user account with authentication, persistent data storage, transaction logging,
    app-specific data, and debit card management.
    """

    def __init__(self, username: str, password_plain: Optional[str] = None, data: Optional[Dict[str, Any]] = None):
        if data:
            self.username = data["username"]
            self.password_hash = data["password_hash"]
            self.gBalance = data.get("gBalance", 0.0)
            self.app_data = data.get("app_data", {})
            self.debit_cards = data.get("debit_cards", {})
            self.transaction_log = data.get("transaction_log", [])
        else:
            if password_plain is None:
                raise ValueError("Password required when creating a new user")
            self.username = username
            self.password_hash = self._hash_password(password_plain)
            self.gBalance = 10.0
            self.app_data = {}
            self.debit_cards = {}
            self.transaction_log = []

    def get_card_manager(self) -> DebitCardManager:
        return DebitCardManager(self)

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password: str) -> bool:
        return self.password_hash == self._hash_password(password)

    def to_dict(self) -> dict:
        return {
            "username": self.username,
            "password_hash": self.password_hash,
            "gBalance": self.gBalance,
            "app_data": self.app_data,
            "debit_cards": self.debit_cards,
            "transaction_log": self.transaction_log,
        }

    def save(self) -> None:
        storage.save_user(self)

    # ---- gBalance methods ----
    def add_gbalance(self, amount: float, app_id: Optional[str] = None, card_id: Optional[str] = None,
                     description: Optional[str] = None) -> None:
        self.gBalance = round(self.gBalance + amount, 2)
        self.save()
        self.log_transaction("gBalance_add", amount, app_id, card_id, description)

    def subtract_gbalance(self, amount: float, app_id: Optional[str] = None, card_id: Optional[str] = None,
                          description: Optional[str] = None) -> None:
        if self.gBalance - amount < 0:
            raise ValueError("Insufficient gBalance")
        self.gBalance = round(self.gBalance - amount, 2)
        self.save()
        self.log_transaction("gBalance_subtract", -amount, app_id, card_id, description)

    # ---- App-specific data access ----
    def get_app_data(self, app_id: str, key: str, default=None):
        app_space = self.app_data.get(app_id, {})
        return app_space.get(key, default)

    def set_app_data(self, app_id: str, key: str, value) -> None:
        if app_id not in self.app_data:
            self.app_data[app_id] = {}
        self.app_data[app_id][key] = value
        self.save()

    def delete_app_data_key(self, app_id: str, key: str) -> None:
        if app_id in self.app_data and key in self.app_data[app_id]:
            del self.app_data[app_id][key]
            self.save()

    # ---- Debit card management ----
    def add_debit_card(self, card_id: str, name: str, limit_amount: float, limit_percent: float,
                       time_window_seconds: int, enabled: bool = True) -> None:
        self.debit_cards[card_id] = {
            "name": name,
            "limit_amount": limit_amount,
            "limit_percent": limit_percent,
            "time_window_seconds": time_window_seconds,
            "enabled": enabled,
            "spend_log": [],  # List of {"timestamp": ISO8601, "amount": float}
        }
        self.save()

    def remove_debit_card(self, card_id: str) -> None:
        if card_id in self.debit_cards:
            del self.debit_cards[card_id]
            self.save()

    def log_card_spend(self, card_id: str, amount: float) -> None:
        now = datetime.datetime.utcnow().isoformat() + "Z"
        if card_id not in self.debit_cards:
            raise ValueError("Card does not exist")
        self.debit_cards[card_id]["spend_log"].append({"timestamp": now, "amount": amount})
        self.save()

    def get_recent_card_spend(self, card_id: str, window_seconds: Optional[int] = None) -> float:
        if card_id not in self.debit_cards:
            return 0.0
        card = self.debit_cards[card_id]
        if window_seconds is None:
            window_seconds = card.get("time_window_seconds", 86400)  # default 1 day

        now = datetime.datetime.utcnow()
        cutoff = now - datetime.timedelta(seconds=window_seconds)
        total = 0.0
        for entry in card["spend_log"]:
            ts = datetime.datetime.fromisoformat(entry["timestamp"].rstrip("Z"))
            if ts > cutoff:
                total += entry["amount"]
        return round(total, 2)

    # ---- Transaction logging ----
    def log_transaction(self, type_: str, amount: float, app_id: Optional[str] = None, card_id: Optional[str] = None,
                        description: Optional[str] = None) -> None:
        timestamp = datetime.datetime.utcnow().isoformat() + "Z"
        if description is None:
            description = f"{type_} {amount}"
        transaction = {
            "type": type_,
            "amount": amount,
            "timestamp": timestamp,
            "app_id": app_id,
            "card_id": card_id,
            "description": description,
        }
        self.transaction_log.append(transaction)
        self.save()
