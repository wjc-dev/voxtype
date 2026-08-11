import asyncio
import io
import os
import threading
import time
import unittest
from unittest.mock import patch

import numpy as np

import main as app_main


class _Recorder:
    def __init__(self):
        self.recording = False
        self.current_device = "测试麦克风"
        self.sample_rate = 16000
        self.started = threading.Event()

    def set_auto_stop_callback(self, callback):
        self.auto_stop = callback

    def set_device_disconnect_callback(self, callback):
        self.disconnect = callback

    def start_streaming_recording(self):
        self.recording = True
        self.started.set()

    def stop_streaming_recording(self, abort=False):
        self.recording = False
        return None if abort else io.BytesIO(b"test-audio")

    def reset_streaming_state(self, reason=""):
        self.recording = False

    async def stream_audio_chunks(self, **_kwargs):
        chunk = np.full(1600, 1000, dtype=np.int16).tobytes()
        yield chunk
        yield chunk
        while self.recording:
            await asyncio.sleep(0.005)


class _Archive:
    def save_audio_bytes(self, _audio):
        return None

    def save_transcription_result(self, *_args, **_kwargs):
        return None


class _Preview:
    def show(self):
        pass

    def hide(self):
        pass

    def update_level(self, _level):
        pass

    def update_text(self, _text):
        pass


class _Status:
    def __init__(self, **_kwargs):
        pass

    def update_state(self, _state, **_kwargs):
        pass

    def open_settings(self):
        pass


class _Diagnostics:
    def __init__(self):
        self.values = {}

    def update(self, **values):
        self.values.update(values)


class _Learner:
    class Store:
        @staticmethod
        def apply(text):
            return text

    store = Store()


class _Keyboard:
    def __init__(self, **callbacks):
        self.callbacks = callbacks
        self.typed = []
        self.recovered = []
        self.correction_learner = _Learner()
        self.target = object()
        self.voice_hotkey_label = "右 Option"

    def _voice_hotkey_display_label(self):
        return "右 Option"

    def capture_output_target(self):
        return self.target

    def mark_streaming(self):
        pass

    def reset_state(self):
        pass

    def show_warning(self, _message):
        pass

    def show_error(self, _message):
        pass

    def retain_recovery_text(self, text, reason):
        self.recovered.append((text, reason))

    def type_text(self, text, target=None):
        self.typed.append((text, target))
        return True


class _Qwen:
    def is_available(self):
        return True

    def recognition_context(self):
        return ""

    async def process_audio_stream(
        self,
        chunks,
        on_preview,
        on_final,
        on_complete,
        _on_error,
        **_kwargs,
    ):
        async for _chunk in chunks:
            on_preview("只应输入一次")
        on_final("只应输入一次")
        on_final("只应输入一次")
        on_complete()


class VoiceSessionTests(unittest.TestCase):
    def make_assistant(self):
        stack = patch.multiple(
            app_main,
            AudioRecorder=_Recorder,
            AudioArchiveManager=_Archive,
            FloatingPreviewWindow=_Preview,
            StatusBarController=_Status,
            KeyboardManager=_Keyboard,
            DiagnosticsStore=_Diagnostics,
        )
        stack.start()
        self.addCleanup(stack.stop)
        return app_main.VoiceAssistant(_Qwen())

    @staticmethod
    def wait_for_thread(assistant):
        deadline = time.time() + 2
        while time.time() < deadline:
            thread = assistant._streaming_thread
            if thread is None:
                return
            thread.join(timeout=0.05)
        raise AssertionError("streaming thread did not finish")

    def test_duplicate_final_callbacks_commit_exactly_once(self):
        with patch.dict(
            os.environ,
            {
                "AUDIO_ARCHIVE_ENABLED": "false",
                "MINIMUM_AUDIO_MS": "100",
                "MINIMUM_VOICED_AUDIO_MS": "60",
                "VOICE_RMS_THRESHOLD": "20",
            },
        ):
            assistant = self.make_assistant()
            assistant.start_streaming()
            self.assertTrue(assistant.audio_recorder.started.wait(1))
            assistant.stop_streaming()
            self.wait_for_thread(assistant)

        self.assertEqual(
            assistant.keyboard_manager.typed,
            [("只应输入一次", assistant.keyboard_manager.target)],
        )
        self.assertEqual(assistant.diagnostics.values["last_session_outcome"], "committed")
        self.assertTrue(assistant.diagnostics.values["last_session_committed"])
        self.assertGreaterEqual(assistant.diagnostics.values["last_session_preview_count"], 1)
        self.assertNotIn("只应输入一次", repr(assistant.diagnostics.values))

    def test_cancelled_session_never_commits_late_callback(self):
        with patch.dict(
            os.environ,
            {
                "AUDIO_ARCHIVE_ENABLED": "false",
                "MINIMUM_AUDIO_MS": "100",
                "MINIMUM_VOICED_AUDIO_MS": "60",
                "VOICE_RMS_THRESHOLD": "20",
            },
        ):
            assistant = self.make_assistant()
            assistant.start_streaming()
            self.assertTrue(assistant.audio_recorder.started.wait(1))
            assistant.cancel_streaming()
            self.wait_for_thread(assistant)

        self.assertEqual(assistant.keyboard_manager.typed, [])
        self.assertEqual(assistant.diagnostics.values["last_session_outcome"], "cancelled")
        self.assertFalse(assistant.diagnostics.values["last_session_committed"])


if __name__ == "__main__":
    unittest.main()
