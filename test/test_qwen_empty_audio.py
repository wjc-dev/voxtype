import asyncio
import unittest

from src.transcription.qwen_streaming import QwenStreamingProcessor


class _WaitingWebSocket:
    closed = False

    async def receive(self):
        await asyncio.Future()


class EmptyAudioTests(unittest.IsolatedAsyncioTestCase):
    async def test_empty_stream_finishes_locally_without_commit_or_error(self):
        processor = QwenStreamingProcessor()
        processor.api_key = "test-key-present-only-in-memory"
        sent = []
        completed = []
        errors = []

        async def connect():
            processor._ws = _WaitingWebSocket()

        async def disconnect():
            processor._ws = None

        async def wait_until_ready():
            return None

        async def send_json(event):
            sent.append(event)

        async def no_audio():
            if False:
                yield b""

        processor._connect = connect
        processor._disconnect = disconnect
        processor._wait_until_ready = wait_until_ready
        processor._send_json = send_json

        await processor.process_audio_stream(
            no_audio(),
            lambda _text: None,
            lambda _text: self.fail("empty audio must not emit final text"),
            lambda: completed.append(True),
            errors.append,
        )

        self.assertEqual(completed, [True])
        self.assertEqual(errors, [])
        self.assertFalse(
            any(
                (event.get("header") or {}).get("action") == "finish-task"
                for event in sent
            )
        )


if __name__ == "__main__":
    unittest.main()
