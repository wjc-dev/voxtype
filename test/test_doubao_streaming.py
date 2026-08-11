import gzip
import json
import os
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.transcription.doubao_streaming import DoubaoStreamingProcessor


class DoubaoProtocolTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(
            os.environ,
            {"DOUBAO_APP_KEY": "1234567890", "DOUBAO_ACCESS_KEY": "x" * 32},
            clear=False,
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def test_credentials_and_context_contract(self):
        processor = DoubaoStreamingProcessor()
        self.assertTrue(processor.is_available())
        self.assertEqual(processor.recognition_context(), "")
        self.assertEqual(processor.engine_id, "doubao")

    def test_initial_request_enables_second_pass_and_vocabulary(self):
        with tempfile.TemporaryDirectory() as directory:
            vocabulary_file = Path(directory) / "custom_vocabulary.txt"
            vocabulary_file.write_text("项目代号\nLightGBM\n", encoding="utf-8")
            with patch.dict(
                os.environ,
                {
                    "CUSTOM_VOCABULARY_FILE": str(vocabulary_file),
                    "DOUBAO_BOOSTING_TABLE_ID": "hotword-table-123",
                    "EXPERIMENTAL_CORRECTION_LEARNING": "true",
                    "CORRECTION_CONTEXT_ENABLED": "true",
                },
                clear=False,
            ):
                processor = DoubaoStreamingProcessor()
                processor.correction_store = type(
                    "CorrectionStoreStub",
                    (),
                    {
                        "rules": staticmethod(
                            lambda: [
                                {
                                    "wrong": "错误写法",
                                    "correct": "正确写法",
                                    "count": 2,
                                    "enabled": True,
                                }
                            ]
                        )
                    },
                )()
                packet = processor._full_request()
        payload_size = struct.unpack(">I", packet[8:12])[0]
        payload = json.loads(gzip.decompress(packet[12 : 12 + payload_size]))
        self.assertEqual(payload["audio"]["rate"], 16000)
        self.assertTrue(payload["request"]["enable_ddc"])
        self.assertTrue(payload["request"]["enable_nonstream"])
        context = json.loads(payload["request"]["context"])
        self.assertEqual(
            context["hotwords"],
            [{"word": "项目代号"}, {"word": "LightGBM"}],
        )
        self.assertEqual(context["correct_words"]["lightgbm"], "LightGBM")
        self.assertEqual(context["correct_words"]["错误写法"], "正确写法")
        self.assertEqual(
            payload["request"]["corpus"],
            {"boosting_table_id": "hotword-table-123"},
        )

    def test_parses_definite_pending_and_final(self):
        processor = DoubaoStreamingProcessor()
        data = {
            "result": {
                "text": "完整结果",
                "utterances": [
                    {"text": "已经", "definite": True},
                    {"text": "确定", "definite": False},
                ],
            }
        }
        compressed = gzip.compress(json.dumps(data).encode())
        packet = bytearray((0x11, 0x93, 0x11, 0x00))
        packet.extend(struct.pack(">i", -2))
        packet.extend(struct.pack(">I", len(compressed)))
        packet.extend(compressed)
        result = processor._parse_response(bytes(packet))
        self.assertEqual(result.definite_text, "已经")
        self.assertEqual(result.pending_text, "确定")
        self.assertTrue(result.is_final)


if __name__ == "__main__":
    unittest.main()
