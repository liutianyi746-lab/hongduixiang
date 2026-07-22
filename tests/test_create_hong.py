import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
MODULE_PATH = ROOT / "girlfriend-reply-coach" / "scripts" / "create_hong.py"


def load_module():
    spec = importlib.util.spec_from_file_location("create_hong", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def valid_profile(root: Path, slug: str = "xiaoyu") -> Path:
    person = root / "people" / slug
    write_json(root / "self-voice.json", {"schema_version": 1, "patterns": [], "corrections": []})
    write_json(
        person / "profile.json",
        {
            "schema_version": 1,
            "alias": "对象甲",
            "authorization": {"confirmed": True},
            "sender_mapping": {"self": ["我"], "partner": ["对象甲"]},
            "text_message_counts": {"self": 2, "partner": 3},
            "claims": [],
        },
    )
    write_json(
        person / "voice-delta.json",
        {"schema_version": 1, "person_id": slug, "patterns": [], "corrections": []},
    )
    return person


class ProfileGateTests(unittest.TestCase):
    def test_slug_validation_rejects_reserved_and_unsafe_values(self):
        module = load_module()
        self.assertEqual("xiao-yu2", module.validate_slug("xiao-yu2"))
        for invalid in ("XiaoYu", "-xiaoyu", "xiao_yu", "hong", "create-hong", "../x"):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                module.validate_slug(invalid)

    def test_gate_returns_all_missing_requirements(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            issues = module.generation_issues(
                Path(tmp), "xiaoyu", confirmed_summary_hash="wrong", target="both"
            )
        joined = "\n".join(issues)
        self.assertIn("self-voice.json", joined)
        self.assertIn("profile.json", joined)
        self.assertIn("voice-delta.json", joined)
        self.assertIn("授权", joined)
        self.assertIn("摘要", joined)

    def test_valid_profile_passes_only_with_current_summary_hash(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            valid_profile(root)
            summary = module.build_summary(root, "xiaoyu")
            confirmation = module.summary_hash(summary)
            self.assertEqual([], module.generation_issues(root, "xiaoyu", confirmation, "both"))
            self.assertTrue(module.profile_version(root, "xiaoyu"))
            self.assertTrue(module.generation_issues(root, "xiaoyu", "stale", "both"))

    def test_mapping_and_text_evidence_are_mandatory(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            person = valid_profile(root)
            profile_path = person / "profile.json"
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            profile["sender_mapping"] = {"self": ["same"], "partner": ["same"]}
            profile["text_message_counts"] = {"self": 0, "partner": 0}
            write_json(profile_path, profile)
            issues = module.generation_issues(root, "xiaoyu", "none", "codex")
            joined = "\n".join(issues)
            self.assertIn("重叠", joined)
            self.assertIn("本人文本", joined)
            self.assertIn("对象文本", joined)


class ThinSkillTests(unittest.TestCase):
    def test_rendered_skill_is_bound_and_forbids_fallback(self):
        module = load_module()
        rendered = module.render_thin_skill("xiaoyu", "version-123")
        skill = rendered["SKILL.md"]
        binding = json.loads(rendered["binding.json"])
        self.assertIn("name: hong-xiaoyu", skill)
        self.assertIn("goutoujunshi", skill)
        self.assertIn("固定绑定 `xiaoyu`", skill)
        self.assertIn("不得生成临时回复", skill)
        self.assertEqual("xiaoyu", binding["slug"])
        self.assertEqual("version-123", binding["expected_profile_version"])
        self.assertEqual("environment-or-default", binding["private_root_resolution"])

    def test_written_skill_contains_no_profile_content_or_absolute_path(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "private-root"
            valid_profile(root)
            version = module.profile_version(root, "xiaoyu")
            destination = Path(tmp) / "generated" / "hong-xiaoyu"
            module.write_thin_skill(destination, "xiaoyu", version)
            combined = "\n".join(
                path.read_text(encoding="utf-8") for path in destination.iterdir()
            )
            self.assertNotIn("对象甲", combined)
            self.assertNotIn(str(root), combined)
            self.assertNotIn("new secret chat", combined)
            self.assertEqual({"SKILL.md", "binding.json"}, {p.name for p in destination.iterdir()})


if __name__ == "__main__":
    unittest.main()
