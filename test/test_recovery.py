import tempfile
import unittest
from pathlib import Path

from src.recovery import RecoveryStore


class RecoveryStoreTests(unittest.TestCase):
    def test_keeps_only_the_latest_private_results(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "recovery.json"
            store = RecoveryStore(path, limit=2)
            store.add("第一条", "失焦")
            store.add("第二条", "失败")
            store.add("第三条", "失败")

            self.assertEqual([entry["text"] for entry in store.load()], ["第三条", "第二条"])
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_delete_and_clear(self):
        with tempfile.TemporaryDirectory() as directory:
            store = RecoveryStore(Path(directory) / "recovery.json")
            store.add("可恢复文字", "失焦")
            entry_id = store.load()[0]["id"]
            self.assertTrue(store.delete(entry_id))
            self.assertEqual(store.load(), [])
            store.add("再次失败", "失败")
            store.clear()
            self.assertEqual(store.load(), [])


if __name__ == "__main__":
    unittest.main()
