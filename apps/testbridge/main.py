import os
import sys
from sdk.app_base import GNetAppBase
from sdk.app_bridge import AppBridge


def _ok(msg):
    print("[OK]  " + msg, flush=True)


def _check(msg):
    _ok(msg)


def _denied(msg):
    print("[DENIED] " + msg, flush=True)


class App(GNetAppBase):
    def main(self):
        print("Starting AppBridge tests...\n")

        bridge: AppBridge = self.bridge

        # Test 1: File read/write in sandbox
        sandbox_file = os.path.join(self.path, "sandbox_test.txt")
        try:
            bridge.write_file(sandbox_file, "Hello sandbox!")
            data = bridge.read_file(sandbox_file)
            _check("Sandbox file write & read: " + data)
        except Exception as e:
            _denied("Sandbox file error: " + str(e))

        # Test 2: Empty sandbox file cleanup
        try:
            bridge.delete_file(sandbox_file)
            _check("Sandbox file cleaned up")
        except Exception as e:
            _denied("Sandbox file cleanup failed: " + str(e))

        # Test 3: User data field test
        try:
            bridge.set_user_field("test_key", "test_value")
            val = bridge.get_user_field("test_key")
            _check("User field set/get: " + str(val))
        except Exception as e:
            _denied("User field access failed: " + str(e))

        # Test 4: Internet access
        try:
            content = bridge.http_get("https://example.com")
            _check("Internet access (example.com): " + content[:40] + "...")
        except Exception as e:
            _denied("Internet access failed: " + str(e))

        # Test 5: Localhost denied (no LOCAL_NETWORK permission)
        try:
            bridge.http_get("http://localhost:5000")
            _denied("Localhost access should not have worked!")
        except Exception as e:
            _check("Localhost correctly denied: " + str(e)[:70])

        # Test 6: gBalance spend via a debit card
        try:
            card_id = self.user.get_default_debit_card_id()
            if not card_id:
                _denied("No debit card present to spend from (create one first).")
            else:
                bridge.modify_gbalance(-2.0, card_id)
                _check("gBalance spent 2.0 via card " + card_id)
        except Exception as e:
            _denied("gBalance modification failed: " + str(e))

        # Test 7: Apps cannot increase balance directly
        try:
            card_id = self.user.get_default_debit_card_id()
            bridge.modify_gbalance(+5.0, card_id or "")
            _denied("Apps should not be able to increase gBalance!")
        except Exception as e:
            _check("Balance increase blocked (expected): " + str(e)[:60])

        # Test 8: Metadata modification blocked without permission
        try:
            bridge.modify_app_metadata(display_name="Hacked Name")
            _denied("Should not be able to modify metadata!")
        except Exception as e:
            _check("Metadata modification blocked: " + str(e)[:60])

        print("\nAll tests completed.", flush=True)