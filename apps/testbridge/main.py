from sdk.app_base import GNetAppBase
from sdk.app_manifest import AppManifest
from sdk.app_bridge import AppBridge
import os

class App(GNetAppBase):
    def main(self):
        print("Starting AppBridge tests...\n")

        bridge: AppBridge = self.bridge

        # Test 1: File read/write in sandbox
        sandbox_file = os.path.join(self.path, "sandbox_test.txt")
        try:
            bridge.write_file(sandbox_file, "Hello sandbox!")
            data = bridge.read_file(sandbox_file)
            print("[✔] Sandbox file write & read:", data)
        except Exception as e:
            print("[✘] Sandbox file error:", e)

        # Test 2: File read outside sandbox (should fail: WRITE not granted)
        outside_path = os.path.abspath("outside_test.txt")
        try:
            data = bridge.read_file(outside_path)
            print("[✔] Global file read:", data)
        except Exception as e:
            print("[✘] Global file read failed (expected):", e)

        # Test 3: User data field test
        try:
            bridge.set_user_field("test_key", "test_value")
            val = bridge.get_user_field("test_key")
            print("[✔] User field set/get:", val)
        except Exception as e:
            print("[✘] User field access failed:", e)

        # Test 4: Network request (internet)
        try:
            content = bridge.http_get("https://example.com")
            print("[✔] Internet access (example.com):", content[:60], "...")
        except Exception as e:
            print("[✘] Internet access failed:", e)

        # Test 5: Localhost request (should fail: no permission)
        try:
            content = bridge.http_get("http://localhost:5000")
            print("[✘] Localhost access should not have worked!")
        except Exception as e:
            print("[✔] Localhost access correctly denied:", e)

        # Test 6: gBalance modification
        try:
            card_id = self.user.get_default_debit_card_id()
            bridge.modify_gbalance(5.0, card_id)
            print("[✔] gBalance modified by +5.0")
        except Exception as e:
            print("[✘] gBalance modification failed:", e)

        # Test 7: Forbidden action (e.g. modifying app metadata)
        try:
            bridge.modify_app_metadata(display_name="Hacked Name")
            print("[✘] Should not be able to modify metadata!")
        except Exception as e:
            print("[✔] Metadata modification blocked (expected):", e)

        print("\nAll tests completed.")

