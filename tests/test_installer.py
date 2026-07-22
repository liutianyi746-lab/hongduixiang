import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
MODULE_PATH = ROOT / "install.py"


def load_module():
    spec = importlib.util.spec_from_file_location("dual_skill_installer", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_skill(directory: Path, name: str, marker: str = "content") -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: Use when testing\n---\n\n# {marker}\n",
        encoding="utf-8",
    )
    return directory


class InstallerPlanningTests(unittest.TestCase):
    def test_targets_cover_codex_claude_and_both(self):
        module = load_module()
        home = Path("/example/home")

        codex = module.installation_targets(home, "codex")
        claude = module.installation_targets(home, "claude")
        both = module.installation_targets(home, "both")

        self.assertEqual(2, len(codex))
        self.assertEqual(2, len(claude))
        self.assertEqual(4, len(both))
        self.assertEqual(
            home / ".codex" / "skills" / "goutoujunshi",
            codex["codex:goutoujunshi"],
        )
        self.assertEqual(
            home / ".claude" / "skills" / "girlfriend-reply-coach",
            claude["claude:girlfriend-reply-coach"],
        )

    def test_targets_reject_unknown_target(self):
        module = load_module()
        with self.assertRaisesRegex(module.InstallError, "target"):
            module.installation_targets(Path("/tmp/home"), "cursor")

    def test_find_goutoujunshi_accepts_root_or_named_child(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root_repo = Path(tmp) / "root-repo"
            child_repo = Path(tmp) / "child-repo"
            write_skill(root_repo, "goutoujunshi")
            child = write_skill(child_repo / "goutoujunshi", "goutoujunshi")

            self.assertEqual(root_repo, module.find_goutoujunshi_skill(root_repo))
            self.assertEqual(child, module.find_goutoujunshi_skill(child_repo))

    def test_find_goutoujunshi_rejects_missing_or_wrong_name(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing = root / "missing"
            missing.mkdir()
            wrong = write_skill(root / "wrong", "another-skill")

            with self.assertRaisesRegex(module.InstallError, "SKILL.md"):
                module.find_goutoujunshi_skill(missing)
            with self.assertRaisesRegex(module.InstallError, "name"):
                module.find_goutoujunshi_skill(wrong)


if __name__ == "__main__":
    unittest.main()
