import asyncio
import queue
import unittest

import numpy as np

from src.audio.recorder import AudioRecorder


class StreamingAudioTests(unittest.IsolatedAsyncioTestCase):
    async def test_48khz_chunks_resample_continuously_to_16khz(self):
        recorder = AudioRecorder.__new__(AudioRecorder)
        recorder.sample_rate = 48000
        recorder.recording = False
        recorder.audio_queue = queue.Queue()
        source = np.linspace(-0.2, 0.2, 9600, dtype=np.float32).reshape(-1, 1)
        recorder.audio_queue.put(source[:4800])
        recorder.audio_queue.put(source[4800:])

        chunks = []
        async for chunk in recorder.stream_audio_chunks(
            chunk_duration_ms=100,
            target_sample_rate=16000,
        ):
            chunks.append(chunk)

        self.assertEqual(len(chunks), 2)
        self.assertEqual(sum(len(chunk) for chunk in chunks), 6400)
        samples = np.frombuffer(b"".join(chunks), dtype=np.int16)
        self.assertTrue(np.all(np.diff(samples.astype(np.int32)) >= 0))


if __name__ == "__main__":
    unittest.main()
