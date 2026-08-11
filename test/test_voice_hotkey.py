import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from Quartz import (
    kCGEventFlagMaskAlternate,
    kCGEventFlagMaskCommand,
    kCGEventFlagsChanged,
    kCGEventKeyDown,
    kCGEventKeyUp,
)

from src.keyboard.listener import (
    KeyboardManager,
    _PassiveGlobalMonitorListener,
    _PassiveTapListener,
    _RegisteredHotKeyListener,
)


class VoiceHotkeyTests(unittest.TestCase):
    def make_manager(self, value):
        manager = KeyboardManager.__new__(KeyboardManager)
        manager.single_fn_hotkey = True
        manager._voice_hotkey_pressed = False
        manager._fn_hotkey_mode = "hold"
        manager.voice_hotkey = value
        manager.voice_hotkey_label = ""
        manager._voice_hotkey_spec = manager._parse_voice_hotkey(value)
        manager.actions = []
        manager.start_recording = lambda: manager.actions.append("start")
        manager.stop_recording = lambda: manager.actions.append("stop")
        manager.toggle_recording = lambda: manager.actions.append("toggle")
        return manager

    def test_right_option_press_and_release(self):
        manager = self.make_manager("right_option")
        self.assertTrue(
            manager._handle_configured_hotkey(
                kCGEventFlagsChanged, 61, kCGEventFlagMaskAlternate
            )
        )
        self.assertTrue(manager._handle_configured_hotkey(kCGEventFlagsChanged, 61, 0))
        self.assertEqual(manager.actions, ["start", "stop"])

    def test_right_command_is_side_specific(self):
        manager = self.make_manager("right_command")
        self.assertFalse(
            manager._handle_configured_hotkey(
                kCGEventFlagsChanged, 55, kCGEventFlagMaskCommand
            )
        )
        self.assertTrue(
            manager._handle_configured_hotkey(
                kCGEventFlagsChanged, 54, kCGEventFlagMaskCommand
            )
        )
        self.assertEqual(manager.actions, ["start"])

    def test_toggle_mode_starts_and_stops_on_successive_presses(self):
        manager = self.make_manager("right_option")
        manager._fn_hotkey_mode = "toggle"
        manager.is_recording = False

        def toggle():
            manager.actions.append("toggle")
            manager.is_recording = not manager.is_recording

        manager.toggle_recording = toggle
        for _ in range(2):
            self.assertTrue(
                manager._handle_configured_hotkey(
                    kCGEventFlagsChanged, 61, kCGEventFlagMaskAlternate
                )
            )
            self.assertTrue(
                manager._handle_configured_hotkey(kCGEventFlagsChanged, 61, 0)
            )
        self.assertEqual(manager.actions, ["toggle", "toggle"])

    def test_recorded_combo_uses_keycode_and_modifiers(self):
        manager = self.make_manager("keycode:49;mods:command+option")
        flags = kCGEventFlagMaskCommand | kCGEventFlagMaskAlternate
        self.assertTrue(manager._handle_configured_hotkey(kCGEventKeyDown, 49, flags))
        self.assertTrue(manager._handle_configured_hotkey(kCGEventKeyUp, 49, flags))
        self.assertEqual(manager.actions, ["start", "stop"])

    def test_recorded_combo_does_not_trigger_without_modifier(self):
        manager = self.make_manager("keycode:49;mods:command")
        self.assertFalse(manager._handle_configured_hotkey(kCGEventKeyDown, 49, 0))
        self.assertEqual(manager.actions, [])

    def test_shortcut_capture_lock_temporarily_passes_current_hotkey_through(self):
        manager = self.make_manager("right_option")
        manager._suppress_vks = {61}
        manager._suppress_modifier_mask = kCGEventFlagMaskAlternate
        manager._listener = None
        with tempfile.TemporaryDirectory() as directory:
            lock = Path(directory) / ".shortcut-capture"
            lock.write_text(str(os.getpid()), encoding="utf-8")
            manager._shortcut_capture_lock_file = lock
            manager._shortcut_capture_checked_at = 0.0
            manager._shortcut_capture_is_active = False
            event = object()
            with (
                patch("Quartz.CGEventGetIntegerValueField", return_value=61),
                patch("Quartz.CGEventGetFlags", return_value=kCGEventFlagMaskAlternate),
            ):
                self.assertIs(
                    manager._darwin_intercept(kCGEventFlagsChanged, event),
                    event,
                )
        self.assertEqual(manager.actions, [])

    def test_passive_listener_never_swallows_observed_event(self):
        observed = []
        listener = _PassiveTapListener(
            lambda event_type, event: observed.append((event_type, event)) or None
        )
        event = object()

        returned = listener._deliver(None, kCGEventFlagsChanged, event, None)

        self.assertIs(returned, event)
        self.assertEqual(observed, [(kCGEventFlagsChanged, event)])

    def test_appkit_monitor_has_no_suppressing_return_value(self):
        observed = []
        listener = _PassiveGlobalMonitorListener(observed.append)
        event = object()

        self.assertIsNone(listener._deliver(event))
        self.assertEqual(observed, [event])

    def test_appkit_monitor_drives_right_option_press_and_release(self):
        manager = self.make_manager("right_option")
        manager.is_recording = False
        manager._suppress_vks = {61}
        manager._shortcut_capture_active = lambda **_kwargs: False

        class Event:
            def __init__(self, event_type, flags):
                self._event_type = event_type
                self._flags = flags

            def type(self):
                return self._event_type

            def keyCode(self):
                return 61

            def modifierFlags(self):
                return self._flags

        manager._nsevent_intercept(Event(kCGEventFlagsChanged, kCGEventFlagMaskAlternate))
        manager._nsevent_intercept(Event(kCGEventFlagsChanged, 0))

        self.assertEqual(manager.actions, ["start", "stop"])

    def test_registered_hotkey_dispatches_only_press_and_release(self):
        states = []
        listener = _RegisteredHotKeyListener(
            {"kind": "key", "vk": 49, "modifiers": ["control", "option"]},
            states.append,
        )

        self.assertEqual(listener._dispatch_kind(listener._EVENT_HOTKEY_PRESSED), 0)
        self.assertEqual(listener._dispatch_kind(999), 0)
        self.assertEqual(listener._dispatch_kind(listener._EVENT_HOTKEY_RELEASED), 0)

        self.assertEqual(states, [True, False])


if __name__ == "__main__":
    unittest.main()
