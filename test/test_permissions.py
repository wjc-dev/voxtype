import tempfile
import unittest
from pathlib import Path

from src.permissions import PermissionMonitor, required_permissions_granted


class PermissionLogicTests(unittest.TestCase):
    def test_input_monitoring_is_required_for_modifier_only_hotkeys(self):
        self.assertFalse(
            required_permissions_granted(
                "granted", "granted", "missing", input_monitoring_required=True
            )
        )

    def test_registered_hotkey_does_not_require_input_monitoring(self):
        self.assertTrue(
            required_permissions_granted(
                "granted", "granted", "missing", input_monitoring_required=False
            )
        )

    def test_snapshot_identifies_the_exact_current_process(self):
        with tempfile.TemporaryDirectory() as directory:
            monitor = PermissionMonitor(
                version="9.8.7",
                hotkey_backend="registered",
                status_path=Path(directory) / "permissions.json",
                request_path=Path(directory) / "request.json",
            )
            self.assertEqual(monitor.identity["version"], "9.8.7")
            self.assertGreater(monitor.identity["pid"], 1)
            self.assertTrue(monitor.identity["executable_path"])
            self.assertTrue(monitor.identity["executable_fingerprint"])


if __name__ == "__main__":
    unittest.main()
