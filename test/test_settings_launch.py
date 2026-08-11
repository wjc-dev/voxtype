import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.ui import status_bar


class SettingsLaunchTests(unittest.TestCase):
    def test_status_item_uses_accessory_activation_policy(self):
        source = (Path(__file__).resolve().parents[1] / "src/ui/status_bar.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("NSApplicationActivationPolicyAccessory", source)
        self.assertNotIn("NSApplicationActivationPolicyProhibited", source)

    def test_status_controller_has_no_recording_callback(self):
        with self.assertRaises(TypeError):
            status_bar.StatusBarController(on_toggle_recording=lambda: None)

    def test_new_helper_is_not_signalled_before_handler_is_ready(self):
        process = MagicMock()
        process.pid = 43210
        process.wait.return_value = 0
        process.poll.return_value = None

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "native_settings").mkdir()
            log_dir = root / "data" / "logs"
            data_dir = root / "data"
            with (
                patch.object(status_bar, "_settings_process", None),
                patch.object(status_bar, "IS_FROZEN", True),
                patch.object(status_bar, "RESOURCE_ROOT", root),
                patch.object(status_bar, "LOG_DIR", log_dir),
                patch.object(status_bar, "DATA_DIR", data_dir),
                patch.object(status_bar, "app_bundle_path", return_value=None),
                patch.object(status_bar.subprocess, "Popen", return_value=process),
                patch.object(status_bar, "_activate_settings_process") as activate,
            ):
                pid = status_bar._launch_settings_window()

        self.assertEqual(pid, process.pid)
        activate.assert_not_called()

    def test_status_item_left_click_opens_settings(self):
        handler = status_bar._MenuActionHandler.alloc().init()

        with (
            patch.object(status_bar, "_current_event_type", return_value=2),
            patch.object(status_bar, "_launch_settings_window") as launch,
        ):
            handler.handleStatusItem_(None)

        launch.assert_called_once()

    def test_status_item_right_click_opens_settings(self):
        handler = status_bar._MenuActionHandler.alloc().init()

        with (
            patch.object(
                status_bar,
                "_current_event_type",
                return_value=status_bar.NSEventTypeRightMouseUp,
            ),
            patch.object(status_bar, "_launch_settings_window") as launch,
        ):
            handler.handleStatusItem_(None)

        launch.assert_called_once()


if __name__ == "__main__":
    unittest.main()
