import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = (
    Path(__file__).parents[1]
    / "girlfriend-reply-coach"
    / "scripts"
    / "profile_store.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("profile_store", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ProfileStoreTests(unittest.TestCase):
    def test_self_voice_status_distinguishes_missing_empty_valid_and_corrupt(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "private-data"
            self.assertEqual("missing", module.self_voice_status(root)["status"])

            root.mkdir()
            voice = root / "self-voice.json"
            voice.write_text(
                '{"schema_version": 1, "patterns": []}', encoding="utf-8"
            )
            self.assertEqual("empty", module.self_voice_status(root)["status"])

            voice.write_text(
                json.dumps(
                    {"schema_version": 1, "patterns": [{"name": "短句"}]},
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            self.assertEqual("valid", module.self_voice_status(root)["status"])

            voice.write_text("{broken", encoding="utf-8")
            self.assertEqual("corrupt", module.self_voice_status(root)["status"])

    def test_create_profile_keeps_private_data_outside_skill(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "private-data"
            profile_dir = module.create_profile(root, "current", "女朋友代号")

            self.assertTrue((profile_dir / "profile.json").exists())
            self.assertTrue((root / "self-voice.json").exists())
            self.assertTrue((root / "manifest.json").exists())
            voice_delta = profile_dir / "voice-delta.json"
            self.assertTrue(voice_delta.exists())
            profile = json.loads((profile_dir / "profile.json").read_text(encoding="utf-8"))
            delta = json.loads(voice_delta.read_text(encoding="utf-8"))
            manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual("女朋友代号", profile["alias"])
            self.assertEqual([], profile["claims"])
            self.assertEqual("current", delta["person_id"])
            self.assertEqual([], delta["patterns"])
            self.assertEqual(
                "people/current/voice-delta.json",
                manifest["profiles"]["current"]["voice_delta_path"],
            )

    def test_create_profiles_keeps_voice_deltas_isolated_by_person(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "private-data"
            alice = module.create_profile(root, "alice", "对象甲")
            bob = module.create_profile(root, "bob", "对象乙")

            alice_delta_path = alice / "voice-delta.json"
            bob_delta_path = bob / "voice-delta.json"
            self.assertNotEqual(alice_delta_path, bob_delta_path)
            alice_delta = json.loads(alice_delta_path.read_text(encoding="utf-8"))
            bob_delta = json.loads(bob_delta_path.read_text(encoding="utf-8"))
            self.assertEqual("alice", alice_delta["person_id"])
            self.assertEqual("bob", bob_delta["person_id"])

    def test_add_claim_requires_evidence_class_and_preserves_conflicts(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "private-data"
            profile_dir = module.create_profile(root, "current", "女朋友代号")

            first_id = module.add_claim(
                profile_dir,
                content="难过时更希望先被倾听",
                classification="高置信度模式",
                evidence=["聊天片段 A", "聊天片段 B"],
                confidence=0.85,
                contexts=["工作受挫", "家庭压力"],
            )
            second_id = module.add_claim(
                profile_dir,
                content="难过时更希望直接给建议",
                classification="待验证推测",
                evidence=["聊天片段 C"],
                confidence=0.35,
                contexts=["身体不适"],
                conflicts_with=[first_id, first_id],
            )

            profile = module.read_profile(profile_dir)
            self.assertEqual(2, len(profile["claims"]))
            self.assertIn(first_id, profile["claims"][1]["conflicts_with"])
            self.assertEqual(second_id, profile["claims"][1]["id"])
            self.assertIn(second_id, profile["claims"][0]["conflicts_with"])
            self.assertEqual(0.70, profile["claims"][0]["confidence"])
            self.assertEqual(0.20, profile["claims"][1]["confidence"])
            self.assertEqual([first_id], profile["claims"][1]["conflicts_with"])

            with self.assertRaises(ValueError):
                module.add_claim(
                    profile_dir,
                    content="无依据判断",
                    classification="确定人格",
                    evidence=[],
                    confidence=1.0,
                    contexts=[],
                )

            with self.assertRaisesRegex(ValueError, "独立情境"):
                module.add_claim(
                    profile_dir,
                    content="只在一个场景出现",
                    classification="高置信度模式",
                    evidence=["聊天片段 D", "聊天片段 E"],
                    confidence=0.8,
                    contexts=["同一场景"],
                )

    def test_create_profile_rejects_git_worktree_storage(self):
        module = load_module()
        repository_private_root = Path(__file__).parents[1] / "private-data-test"
        with self.assertRaisesRegex(ValueError, "Git"):
            module.create_profile(repository_private_root, "current", "女朋友代号")

    def test_add_claim_rejects_manually_created_profile_inside_git_worktree(self):
        module = load_module()
        repository_root = Path(__file__).parents[1]
        with tempfile.TemporaryDirectory(dir=repository_root) as tmp:
            profile_dir = Path(tmp)
            (profile_dir / "profile.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "alias": "测试",
                        "created_at": "2026-07-22T00:00:00+00:00",
                        "updated_at": "2026-07-22T00:00:00+00:00",
                        "claims": [],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "Git"):
                module.add_claim(
                    profile_dir,
                    content="不得写入",
                    classification="已确认事实",
                    evidence=["测试证据"],
                    confidence=1.0,
                    contexts=["测试情境"],
                )

    def test_delete_profile_removes_profile_and_derived_data_only_inside_root(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "private-data"
            profile_dir = module.create_profile(root, "current", "女朋友代号")
            derived_dir = root / "derived" / "current"
            derived_dir.mkdir(parents=True)
            (derived_dir / "summary.json").write_text("{}", encoding="utf-8")
            raw_dir = root / "raw" / "current"
            raw_dir.mkdir(parents=True)
            (raw_dir / "chat.txt").write_text("private", encoding="utf-8")
            outside = Path(tmp) / "keep.txt"
            outside.write_text("keep", encoding="utf-8")

            plan = module.deletion_plan(root, "current")
            module.delete_profile(root, "current", plan["confirmation_token"])

            self.assertFalse(profile_dir.exists())
            self.assertFalse(derived_dir.exists())
            self.assertFalse(raw_dir.exists())
            self.assertTrue(outside.exists())


if __name__ == "__main__":
    unittest.main()
