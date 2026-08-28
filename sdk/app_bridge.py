import os
import json
import time
import datetime
import threading
import requests  # For network calls - ensure requests is installed
from enum import Enum
from sdk.app_manifest import AppManifest
from sdk.permissions import AppPermission
import user

LOGS_DIR = os.path.join(os.path.dirname(__file__), '..', 'user', 'logs')
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)


class PermissionError(Exception):
    pass


class AppBridge:
    def __init__(self, app_manifest: AppManifest, current_user: user.account.User):
        self.manifest = app_manifest
        self.app_id = app_manifest.app_id
        self.uuid = str(app_manifest.uuid)
        self.permissions = set(app_manifest.permissions)
        self.current_user = current_user
        self.sandbox_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'apps', self.app_id))
        self.lock = threading.Lock()  # For thread-safe logging

    # --- Permission Checks ---

    def check_permission(self, permission: AppPermission):
        if permission not in self.permissions:
            self.log_violation(permission)
            raise PermissionError(f"Permission {permission.name} not granted for app {self.app_id}.")

    # --- Logging ---

    def log_violation(self, permission: AppPermission):
        message = f"[{self._now_iso()}] VIOLATION: App {self.app_id} ({self.uuid}) attempted to use permission {permission.name} without authorization.\n"
        self._write_log(message)

    def log_action(self, action: str, success: bool, details: str = ""):
        status = "ALLOWED" if success else "DENIED"
        message = f"[{self._now_iso()}] {status}: App {self.app_id} ({self.uuid}) performed {action}. {details}\n"
        self._write_log(message)

    def _write_log(self, message: str):
        with self.lock:
            # Write to app-specific log file
            log_path = os.path.join(LOGS_DIR, f"{self.uuid}.log")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(message)

            # Could also write to a global log if desired

    def _now_iso(self):
        return datetime.datetime.utcnow().isoformat() + "Z"

    # --- Path Helpers ---

    def _is_in_sandbox(self, path: str) -> bool:
        abs_path = os.path.abspath(path)
        return abs_path.startswith(self.sandbox_path + os.sep) or abs_path == self.sandbox_path

    def _assert_path_allowed(self, path: str, write=False):
        if self._is_in_sandbox(path):
            # Inside sandbox
            perm = AppPermission.WRITE_APP_FILES if write else AppPermission.READ_APP_FILES
            self.check_permission(perm)
        else:
            # Outside sandbox
            perm = AppPermission.WRITE_GLOBAL_FILES if write else AppPermission.READ_GLOBAL_FILES
            self.check_permission(perm)

    # --- File Operations ---

    def read_file(self, path: str) -> str:
        try:
            self._assert_path_allowed(path, write=False)
            with open(path, "r", encoding="utf-8") as f:
                data = f.read()
            self.log_action(f"read_file({path})", True)
            return data
        except Exception as e:
            self.log_action(f"read_file({path})", False, str(e))
            raise

    def write_file(self, path: str, content: str):
        try:
            self._assert_path_allowed(path, write=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            self.log_action(f"write_file({path})", True)
        except Exception as e:
            self.log_action(f"write_file({path})", False, str(e))
            raise

    def append_file(self, path: str, content: str):
        try:
            self._assert_path_allowed(path, write=True)
            with open(path, "a", encoding="utf-8") as f:
                f.write(content)
            self.log_action(f"append_file({path})", True)
        except Exception as e:
            self.log_action(f"append_file({path})", False, str(e))
            raise

    def delete_file(self, path: str):
        try:
            self._assert_path_allowed(path, write=True)
            if os.path.isfile(path):
                os.remove(path)
                self.log_action(f"delete_file({path})", True)
            else:
                raise FileNotFoundError(f"File {path} not found.")
        except Exception as e:
            self.log_action(f"delete_file({path})", False, str(e))
            raise

    # --- Network Operations ---

    def http_get(self, url: str, params=None, headers=None):
        self._check_network_access(url)
        try:
            resp = requests.get(url, params=params, headers=headers)
            self.log_action(f"http_get({url})", True)
            return resp.text
        except Exception as e:
            self.log_action(f"http_get({url})", False, str(e))
            raise

    def http_post(self, url: str, data=None, json_data=None, headers=None):
        self._check_network_access(url)
        try:
            resp = requests.post(url, data=data, json=json_data, headers=headers)
            self.log_action(f"http_post({url})", True)
            return resp.text
        except Exception as e:
            self.log_action(f"http_post({url})", False, str(e))
            raise

    def _check_network_access(self, url: str):
        from urllib.parse import urlparse
        parsed = urlparse(url)

        # Determine if localhost / local network or external
        hostname = parsed.hostname or ""
        if hostname in ["localhost", "127.0.0.1", "::1"] or hostname.startswith("192.") or hostname.startswith("10.") or hostname.startswith("172."):
            # Local network
            self.check_permission(AppPermission.ACCESS_LOCAL_NETWORK)
        else:
            self.check_permission(AppPermission.ACCESS_INTERNET)

    # --- Lifecycle Operations (Placeholders) ---

    def request_restart(self):
        # Example placeholder; requires special permission
        self.check_permission(AppPermission.EXECUTE_EXTERNAL_BINARIES)
        self.log_action("request_restart", True)
        # Integration with app host lifecycle manager required

    def request_shutdown(self):
        self.check_permission(AppPermission.EXECUTE_EXTERNAL_BINARIES)
        self.log_action("request_shutdown", True)
        # Integration with app host lifecycle manager required

    # --- User Data Operations ---

    def get_username(self):
        self.check_permission(AppPermission.READ_USERNAME)
        return self.current_user.username

    def get_user_field(self, key: str):
        self.check_permission(AppPermission.READ_USER_FIELD)
        return self.current_user.get_app_data(self.app_id, key)

    def set_user_field(self, key: str, value):
        self.check_permission(AppPermission.WRITE_USER_FIELD)
        self.current_user.set_app_data(self.app_id, key, value)

    def delete_user_field(self, key: str):
        self.check_permission(AppPermission.DELETE_USER_FIELD)
        self.current_user.delete_app_data_key(self.app_id, key)

    def list_user_fields(self) -> list:
        self.check_permission(AppPermission.READ_USER_FIELD)
        app_space = self.current_user.app_data.get(self.app_id, {})
        return list(app_space.keys())

    # --- gBalance Operations ---

    def modify_gbalance(self, amount: float, card_id: str):
        """Spend money from a user's gBalance through an enabled debit card."""
        from user.debit_card_manager import DebitCardManager

        self.check_permission(AppPermission.MODIFY_GBALANCE)

        if amount > 0:
            self.log_action("modify_gbalance", False, "positive amount")
            raise PermissionError("Apps cannot increase gBalance directly.")

        card = self.current_user.debit_cards.get(card_id)
        if not card or not card.get("enabled", False):
            raise PermissionError(f"Invalid or disabled debit card: {card_id}")

        spend = abs(amount)
        if not DebitCardManager.can_spend(self.current_user, card_id, spend):
            self.log_action("modify_gbalance", False, "card limit hit")
            raise PermissionError(f"Debit card {card_id} limit exceeded for spend {spend}.")

        try:
            self.current_user.log_card_spend(card_id, spend)
            self.current_user.subtract_gbalance(
                spend,
                app_id=self.app_id,
                card_id=card_id,
                description=f"App {self.app_id} spent {spend} via card {card_id}",
            )
        except ValueError as e:
            raise PermissionError(str(e))

        self.log_action("modify_gbalance", True, f"{spend} via {card_id}")

    # --- Metadata (dev mode) ---

    def modify_app_metadata(self, **kwargs):
        self.check_permission(AppPermission.MODIFY_APP_METADATA)
        self.log_action(f"modify_app_metadata({kwargs})", True)

    # --- gBalance read / spend / award helpers ---

    def get_gbalance(self):
        """Read the user's current gBalance."""
        self.check_permission(AppPermission.READ_GBALANCE)
        return self.current_user.gBalance

    def get_default_card_id(self):
        return self.current_user.get_default_debit_card_id()

    def spend_gbalance(self, amount: float, card_id: str = None):
        """Spend from the user's gBalance through a debit card (negative modify)."""
        if amount <= 0:
            raise PermissionError("Spend amount must be positive.")
        if card_id is None:
            card_id = self.current_user.get_default_debit_card_id()
            if not card_id:
                raise PermissionError("No debit card available to spend from.")
        return self.modify_gbalance(-amount, card_id)

    AWARD_CAP_PER_TRANSACTION = 1000.0
    AWARD_CAP_PER_DAY = 5000.0

    def award_gbalance(self, amount: float):
        """Award winnings/earnings into the user's gBalance, capped per day."""
        self.check_permission(AppPermission.MODIFY_GBALANCE)
        if amount <= 0:
            raise PermissionError("Award amount must be positive.")
        if amount > self.AWARD_CAP_PER_TRANSACTION:
            raise PermissionError(f"Award exceeds {self.AWARD_CAP_PER_TRANSACTION:g} per transaction.")

        import datetime as _dt
        today = _dt.datetime.utcnow().date().isoformat()
        app_space = self.current_user.app_data.setdefault(self.app_id, {})
        awards = app_space.get("_award_log", {})
        day = awards.get("day")
        total = awards.get("total", 0.0) if day == today else 0.0
        if total + amount > self.AWARD_CAP_PER_DAY:
            raise PermissionError("This app has reached its daily earning cap.")
        awards["day"] = today
        awards["total"] = round(total + amount, 2)
        app_space["_award_log"] = awards

        self.current_user.add_gbalance(
            amount,
            app_id=self.app_id,
            description=f"Earnings from {self.app_id}",
        )
        self.current_user.set_app_data(self.app_id, "_award_log", awards)
        self.log_action("award_gbalance", True, f"+{amount}")

    # --- Utility ---

    def list_app_files(self):
        # List files in sandbox folder
        self.check_permission(AppPermission.READ_APP_FILES)
        files = []
        for root, dirs, filenames in os.walk(self.sandbox_path):
            for file in filenames:
                files.append(os.path.relpath(os.path.join(root, file), self.sandbox_path))
        self.log_action("list_app_files", True)
        return files