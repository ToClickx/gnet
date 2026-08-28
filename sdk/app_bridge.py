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

    # --- App Metadata ---

    def modify_gbalance(self, amount: float, card_id: str):
        self.check_permission(AppPermission.MODIFY_GBALANCE)

        card = self.current_user.get_debit_card(card_id)
        if not card or not card.is_enabled:
            raise PermissionError(f"Invalid or disabled debit card: {card_id}")

        gBalance = self.current_user.get_field("gBalance", 0)

        # --- App-wide spending % limit ---
        max_percent = self.manifest.gbalance_spend_limit_percent or 0
        max_allowed = gBalance * (max_percent / 100.0)
        app_spend_key = f"_app_spent::{self.app_id}"
        app_spent = self.current_user.get_field(app_spend_key, 0)

        if amount > 0:
            raise PermissionError("Apps cannot increase gBalance directly.")

        # Negative amount = debit, so compare against app limit
        if abs(app_spent + amount) > max_allowed:
            raise PermissionError(f"App {self.app_id} exceeded its gBalance spending limit ({max_percent}%)")

        # --- Card hard cap & time window logic ---
        now = time.time()
        window = card.time_window_sec
        card_spend_key = f"_card_spend_history::{card.card_id}"
        history = self.current_user.get_field(card_spend_key, [])
        history = [t for t in history if now - t < window]  # purge old

        if len(history) >= card.hard_cap:
            raise PermissionError(f"Debit card {card.card_id} exceeded its hard cap of {card.hard_cap} in last {window}s.")

        # --- Sufficient balance check ---
        new_balance = gBalance + amount
        if new_balance < 0:
            raise PermissionError("Insufficient gBalance.")

        # --- Apply changes ---
        self.current_user.set_field("gBalance", new_balance)
        self.current_user.set_field(app_spend_key, app_spent + amount)

        history.append(now)
        self.current_user.set_field(card_spend_key, history)

        self.current_user.save()

        self.current_user.log_transaction(
            type_="app_gbalance_modification",
            amount=amount,
            description=f"App {self.app_id} modified gBalance by {amount} via card {card_id}"
        )

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
        app_data = self._get_app_data_dict(create=False)
        return app_data.get(key)

    def set_user_field(self, key: str, value):
        self.check_permission(AppPermission.WRITE_USER_FIELD)
        app_data = self._get_app_data_dict(create=True)
        app_data[key] = value
        self.current_user.set_field("app_data", app_data)  # save whole app data subdict
        self.current_user.save()

    def delete_user_field(self, key: str):
        self.check_permission(AppPermission.DELETE_USER_FIELD)
        app_data = self._get_app_data_dict(create=False)
        if key in app_data:
            del app_data[key]
            self.current_user.set_field("app_data", app_data)
            self.current_user.save()

    def _get_app_data_dict(self, create=False):
        # Each app’s data is stored under user.data["app_data"][app_id]
        app_data = self.current_user.get_field("app_data", {})
        if self.app_id not in app_data:
            if create:
                app_data[self.app_id] = {}
            else:
                return {}
        return app_data[self.app_id]

    # --- gBalance Operations ---

    def modify_gbalance(self, amount: float, card_id: str):
        self.check_permission(AppPermission.MODIFY_GBALANCE)
        card = self.current_user.get_debit_card(card_id)
        if not card or not card.is_enabled:
            raise PermissionError(f"Invalid or disabled debit card: {card_id}")

        # Check limits: amount and % of user balance in card’s time window
        if not card.can_spend(amount, self.current_user.get_field("gBalance", 0)):
            raise PermissionError(f"Debit card limit exceeded for amount: {amount}")

        new_balance = self.current_user.get_field("gBalance", 0) + amount
        if new_balance < 0:
            raise PermissionError("Insufficient gBalance")

        # Update gBalance
        self.current_user.set_field("gBalance", new_balance)
        card.record_spend(amount)
        self.current_user.save()

        # Log transaction (with card and app info)
        self.current_user.log_transaction(
            type_="app_gbalance_modification",
            amount=amount,
            description=f"App {self.app_id} modified gBalance by {amount} via card {card_id}"
        )

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