import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.correction_learning import (
    CorrectionLearner,
    CorrectionStore,
    extract_correction_pairs,
)
from src.transcription.qwen_streaming import QwenStreamingProcessor


class CorrectionExtractionTests(unittest.TestCase):
    def test_extracts_spoken_term_replacement(self):
        self.assertEqual(
            extract_correction_pairs(
                "我觉得锤道需要讨论",
                "我觉得trade off需要讨论",
            ),
            [("锤道", "trade off")],
        )

    def test_ignores_continued_typing(self):
        self.assertEqual(
            extract_correction_pairs("这是语音输入", "这是语音输入，继续打字"),
            [],
        )

    def test_keeps_english_correction_but_not_following_continuation(self):
        self.assertEqual(
            extract_correction_pairs(
                "我觉得锤道",
                "我觉得trade off 然后继续输入",
            ),
            [("锤道", "trade off")],
        )

    def test_ignores_punctuation_only_edits(self):
        self.assertEqual(
            extract_correction_pairs("你好，世界。", "你好 世界。"),
            [],
        )


class CorrectionStoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.auto_replace = patch.dict(
            os.environ,
            {
                "EXPERIMENTAL_CORRECTION_LEARNING": "true",
                "CORRECTION_AUTO_REPLACE": "true",
                "CORRECTION_REPLACE_MIN_COUNT": "2",
            },
        )
        self.auto_replace.start()
        self.store = CorrectionStore(
            Path(self.temporary_directory.name) / "corrections.json"
        )

    def tearDown(self):
        self.auto_replace.stop()
        self.temporary_directory.cleanup()

    def test_single_observation_is_not_applied(self):
        self.store.record("锤道", "trade off")
        self.assertEqual(
            self.store.apply("这个锤道需要讨论"),
            "这个锤道需要讨论",
        )

    def test_applies_after_two_matching_observations(self):
        self.store.record("锤道", "trade off")
        self.store.record("锤道", "trade off")
        self.assertEqual(self.store.apply("这个锤道需要讨论"), "这个trade off需要讨论")

    def test_conflicting_tie_is_not_applied(self):
        self.store.record("锤道", "trade off")
        self.store.record("锤道", "trade-off")
        self.assertEqual(self.store.apply("锤道"), "锤道")

    def test_higher_frequency_wins_and_enters_context(self):
        self.store.record("锤道", "trade off")
        self.store.record("锤道", "trade-off")
        self.store.record("锤道", "trade off")
        self.assertEqual(self.store.apply("锤道"), "trade off")
        with patch.dict(os.environ, {"CORRECTION_CONTEXT_ENABLED": "true"}):
            self.assertEqual(
                self.store.context_lines(minimum_count=2),
                ["锤道 → trade off（已人工纠正 2 次）"],
            )

    def test_switch_can_disable_local_replacement(self):
        self.store.record("锤道", "trade off")
        with patch.dict(os.environ, {"CORRECTION_AUTO_REPLACE": "false"}):
            self.assertEqual(self.store.apply("锤道"), "锤道")

    def test_experimental_gate_disables_replacement_and_context(self):
        self.store.record("锤道", "trade off")
        self.store.record("锤道", "trade off")
        with patch.dict(
            os.environ,
            {"EXPERIMENTAL_CORRECTION_LEARNING": "false"},
        ):
            self.assertEqual(self.store.apply("锤道"), "锤道")
            self.assertEqual(self.store.context_lines(minimum_count=1), [])

    def test_rules_persist_across_new_store_instance(self):
        self.store.record("锤道", "trade off")
        self.store.record("锤道", "trade off")
        reopened = CorrectionStore(self.store.path)
        self.assertEqual(reopened.apply("讨论锤道"), "讨论trade off")

    def test_english_rules_respect_word_boundaries(self):
        self.store.record("off", "of")
        self.store.record("off", "of")
        self.assertEqual(self.store.apply("office off"), "office of")

    def test_replacements_do_not_cascade(self):
        for _ in range(2):
            self.store.record("锤道", "trade off")
            self.store.record("trade off", "权衡")
        self.assertEqual(self.store.apply("锤道"), "trade off")

    def test_common_short_phrase_is_never_auto_replaced(self):
        self.store.record("这个", "那个")
        self.store.record("这个", "那个")
        self.assertEqual(self.store.apply("这个方案"), "这个方案")

    def test_latest_learning_event_can_be_undone(self):
        self.store.record("锤道", "trade off")
        self.store.record("锤道", "trade off")
        self.assertEqual(self.store.undo_last_record(), ("锤道", "trade off"))
        self.assertEqual(self.store.rules()[0]["count"], 1)
        self.assertEqual(self.store.apply("锤道"), "锤道")

    def test_learned_rule_enters_next_qwen_recognition_context(self):
        self.store.record("锤道", "trade off")
        with patch.dict(
            os.environ,
            {
                "CORRECTION_STORE_FILE": str(self.store.path),
                "EXPERIMENTAL_CORRECTION_LEARNING": "true",
                "CORRECTION_CONTEXT_ENABLED": "true",
                "CORRECTION_CONTEXT_MIN_COUNT": "1",
            },
        ):
            processor = QwenStreamingProcessor()
            context = processor.recognition_context()
        self.assertIn("锤道 → trade off", context)


class CorrectionObserverTests(unittest.TestCase):
    def test_capture_target_returns_the_focused_editor(self):
        with patch.dict(
            os.environ,
            {
                "EXPERIMENTAL_CORRECTION_LEARNING": "true",
                "CORRECTION_LEARNING_ENABLED": "true",
            },
        ):
            learner = CorrectionLearner(CorrectionStore(Path("/tmp/unused-corrections.json")))

        class FrontmostApplication:
            @staticmethod
            def processIdentifier():
                return 314

        class Workspace:
            @staticmethod
            def sharedWorkspace():
                return Workspace()

            @staticmethod
            def frontmostApplication():
                return FrontmostApplication()

        focused_editor = object()
        fake_ax = {
            "workspace": Workspace,
            "copy": lambda _app, attribute, _unused: (
                (0, focused_editor) if attribute == "focused" else (1, None)
            ),
            "create": lambda pid: {"pid": pid},
            "get_value": lambda *_args: None,
            "focused": "focused",
            "selection": "selection",
            "value": "value",
            "range_type": "range",
        }

        with (
            patch("src.correction_learning.sys_platform", return_value="darwin"),
            patch.object(learner, "_ax_modules", return_value=fake_ax),
        ):
            target = learner.capture_target()

        self.assertIsNotNone(target)
        self.assertEqual(target.pid, 314)
        self.assertIs(target.element, focused_editor)

    def test_observer_turns_a_manual_edit_into_a_persistent_rule(self):
        with tempfile.TemporaryDirectory() as directory:
            store = CorrectionStore(Path(directory) / "corrections.json")
            learner = CorrectionLearner(store)
            baseline = ("我觉得锤道", len("我觉得锤道"), len("我觉得锤道"))
            edited = ("我觉得trade off", len("我觉得trade off"), len("我觉得trade off"))
            snapshots = iter([baseline, edited])

            with (
                patch.object(learner, "_snapshot", side_effect=lambda _target: next(snapshots)),
                patch("src.correction_learning.time.sleep", return_value=None),
                patch(
                    "src.correction_learning.time.monotonic",
                    side_effect=[0.0, 0.0, 1.0, 2.0, 4.1],
                ),
            ):
                learner._observe(0, object(), "我觉得锤道")

            reopened = CorrectionStore(store.path)
            self.assertEqual(reopened.rules()[0]["wrong"], "锤道")
            self.assertEqual(reopened.rules()[0]["correct"], "trade off")
            self.assertEqual(reopened.rules()[0]["count"], 1)


if __name__ == "__main__":
    unittest.main()
