import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = (
    Path(__file__).parents[1]
    / "girlfriend-reply-coach"
    / "scripts"
    / "import_weflow.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("import_weflow", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ImportWeFlowTests(unittest.TestCase):
    def test_txt_parses_sender_time_multiline_and_message_kinds(self):
        module = load_module()
        text = """2025-04-04 21:10:39 '对象甲'
第一行
第二行

2025-04-04 21:11:42 '我'
[表情包]

2025-04-04 21:15:36 '对象甲'
\"对象甲\" 撤回了一条消息
"""

        result = module.parse_txt(text)

        self.assertEqual(3, len(result.messages))
        self.assertEqual("对象甲", result.messages[0].sender)
        self.assertEqual("第一行\n第二行", result.messages[0].content)
        self.assertEqual("text", result.messages[0].kind)
        self.assertEqual("media", result.messages[1].kind)
        self.assertEqual("system", result.messages[2].kind)

    def test_json_and_jsonl_normalize_common_fields_and_skip_incomplete_rows(self):
        module = load_module()
        records = [
            {"timestamp": "2025-04-04 21:10:39", "sender": "我", "content": "你好"},
            {"time": "2025-04-04 21:11:00", "senderName": "对象甲", "text": "嗯"},
            {"timestamp": "2025-04-04 21:12:00", "content": "缺少发送者"},
        ]

        json_result = module.parse_json(json.dumps(records, ensure_ascii=False))
        jsonl_result = module.parse_jsonl(
            "\n".join(json.dumps(row, ensure_ascii=False) for row in records)
        )

        for result in (json_result, jsonl_result):
            self.assertEqual(2, len(result.messages))
            self.assertEqual(1, result.skipped_count)
            self.assertTrue(result.warnings)

    def test_import_file_rejects_unknown_extensions(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "chat.html"
            path.write_text("<html></html>", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "不支持"):
                module.import_file(path)

    def test_evidence_view_excludes_system_and_media_content(self):
        module = load_module()
        result = module.parse_txt(
            """2025-04-04 21:10:39 '我'
真实文字

2025-04-04 21:11:42 '对象甲'
[表情包]

2025-04-04 21:15:36 '对象甲'
\"对象甲\" 撤回了一条消息
"""
        )

        evidence = module.to_evidence(result)

        self.assertEqual(["真实文字"], [row["content"] for row in evidence["messages"]])
        self.assertEqual({"media": 1}, evidence["message_type_counts"])
        self.assertNotIn("撤回", json.dumps(evidence, ensure_ascii=False))

    def test_malformed_txt_and_non_object_json_rows_are_not_silent(self):
        module = load_module()
        txt_result = module.parse_txt("这不是受支持的聊天格式")
        json_result = module.parse_json(
            '[{"timestamp":"2025-01-01 00:00:00","sender":"我","content":"好"},42]'
        )

        self.assertEqual(0, len(txt_result.messages))
        self.assertGreater(txt_result.skipped_count, 0)
        self.assertTrue(txt_result.warnings)
        self.assertEqual(1, json_result.skipped_count)
        self.assertTrue(json_result.warnings)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.txt"
            path.write_text("这不是受支持的聊天格式", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "可靠消息"):
                module.import_file(path)


if __name__ == "__main__":
    unittest.main()
