import os
import unittest
from unittest.mock import patch

from src.text_processing import (
    clean_spoken_disfluencies,
    format_transcription_text,
    has_sufficient_speech,
    is_context_echo,
    sanitize_inline_text,
)


class SpokenCleanupTests(unittest.TestCase):
    def test_removes_isolated_fillers(self):
        self.assertEqual(
            clean_spoken_disfluencies("嗯 而且 呃 我觉得这个方案可以", enabled=True),
            "而且 我觉得这个方案可以",
        )

    def test_removes_filler_between_repeated_phrase(self):
        self.assertEqual(
            clean_spoken_disfluencies("而且 嗯 而且我发现它有问题", enabled=True),
            "而且我发现它有问题",
        )

    def test_collapses_clear_stutter_but_keeps_single_character_words(self):
        self.assertEqual(clean_spoken_disfluencies("你好你好你好", enabled=True), "你好")
        self.assertEqual(clean_spoken_disfluencies("喂喂喂 我我我觉得", enabled=True), "喂 我觉得")
        self.assertEqual(clean_spoken_disfluencies("人人都可以常常看看", enabled=True), "人人都可以常常看看")

    def test_filter_can_be_disabled(self):
        with patch.dict(os.environ, {"DISFLUENCY_FILTER_ENABLED": "false"}):
            self.assertEqual(clean_spoken_disfluencies("嗯 你好你好"), "嗯 你好你好")

    def test_fillers_mode_does_not_rewrite_repeated_words(self):
        self.assertEqual(
            clean_spoken_disfluencies("嗯 你好你好你好", mode="fillers"),
            "你好你好你好",
        )

    def test_cleanup_composes_with_space_punctuation_mode(self):
        formatted = format_transcription_text("嗯，我觉得，嗯，这个可以？", "spaces")
        self.assertEqual(clean_spoken_disfluencies(formatted, enabled=True), "我觉得 这个可以？")

    def test_keeps_meaningful_discourse_words_and_repeated_emphasis(self):
        self.assertEqual(
            clean_spoken_disfluencies("然后这个方案就是非常非常重要", enabled=True),
            "然后这个方案就是非常非常重要",
        )
        self.assertEqual(clean_spoken_disfluencies("哈哈哈 666", enabled=True), "哈哈哈 666")


class InlineSafetyTests(unittest.TestCase):
    def test_line_breaks_can_never_become_chat_submit_events(self):
        self.assertEqual(
            sanitize_inline_text("第一行\r\n第二行\u2028第三行\t结束"),
            "第一行 第二行 第三行 结束",
        )


class ContextEchoSafetyTests(unittest.TestCase):
    context = (
        "用户从事软件开发。常用术语：LightGBM、trade-off、特征工程。"
        "近期主题：示例项目。"
    )

    def test_blocks_long_context_echo(self):
        self.assertTrue(is_context_echo(self.context, self.context))
        self.assertTrue(
            is_context_echo(
                "用户从事软件开发 常用术语 LightGBM trade-off 特征工程",
                self.context,
            )
        )

    def test_allows_short_real_vocabulary_utterance(self):
        self.assertFalse(is_context_echo("这个 LightGBM 模型怎么样", self.context))

    def test_silence_and_short_tap_do_not_open_speech_gate(self):
        self.assertFalse(has_sufficient_speech(1.3, 0.0))
        self.assertFalse(has_sufficient_speech(500.0, 80.0))
        self.assertTrue(has_sufficient_speech(400.0, 200.0))


if __name__ == "__main__":
    unittest.main()
