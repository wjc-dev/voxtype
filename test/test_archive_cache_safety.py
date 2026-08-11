import json
import tempfile
import threading
import unittest
from pathlib import Path

from src.audio.archive import AudioArchiveManager


class ArchiveCacheSafetyTests(unittest.TestCase):
    def make_manager(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        return AudioArchiveManager(str(Path(temporary.name) / "archive"))

    def test_cache_round_trip_is_valid_json(self):
        manager = self.make_manager()
        manager.save_transcription_cache({"a.wav": {"transcription": "测试"}})
        self.assertEqual(
            manager.load_transcription_cache()["a.wav"]["transcription"],
            "测试",
        )
        json.loads(Path(manager.cache_path).read_text(encoding="utf-8"))

    def test_corrupt_cache_is_quarantined_and_backup_is_used(self):
        manager = self.make_manager()
        original = {"old.wav": {"transcription": "旧记录"}}
        manager.save_transcription_cache(original)
        # A second save creates cache.json.bak pointing to the first version.
        manager.save_transcription_cache(
            {**original, "new.wav": {"transcription": "新记录"}}
        )
        Path(manager.cache_path).write_text('{"broken":', encoding="utf-8")

        recovered = manager.load_transcription_cache()

        self.assertEqual(recovered, original)
        quarantined = list(Path(manager.archive_dir).glob("cache.json.corrupt-*"))
        self.assertEqual(len(quarantined), 1)
        self.assertEqual(quarantined[0].read_text(encoding="utf-8"), '{"broken":')

    def test_concurrent_result_updates_do_not_drop_entries(self):
        manager = self.make_manager()
        audio_paths = []
        for index in range(20):
            path = Path(manager.audio_dir) / f"{index}.wav"
            path.write_bytes(b"wav")
            audio_paths.append(path)

        threads = [
            threading.Thread(
                target=manager.save_transcription_result,
                args=(str(path), f"text-{index}"),
                kwargs={"service": "qwen", "model": "test"},
            )
            for index, path in enumerate(audio_paths)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(len(manager.load_transcription_cache()), 20)

    def test_migration_moves_only_audio_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "archive"
            root.mkdir()
            (root / "legacy.wav").write_bytes(b"audio")
            (root / "notes.md").write_text("keep", encoding="utf-8")
            manager = AudioArchiveManager(str(root))

            self.assertTrue((Path(manager.audio_dir) / "legacy.wav").exists())
            self.assertTrue((root / "notes.md").exists())


if __name__ == "__main__":
    unittest.main()
