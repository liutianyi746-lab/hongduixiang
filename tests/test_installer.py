import importlib.util
import shutil
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


class TransactionalInstallTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.home = self.root / "home"
        self.local = write_skill(
            self.root / "sources" / "girlfriend-reply-coach",
            "girlfriend-reply-coach",
            "new local",
        )
        self.goutou = write_skill(
            self.root / "sources" / "goutoujunshi",
            "goutoujunshi",
            "new goutou",
        )

    def tearDown(self):
        self.temporary.cleanup()

    def test_installs_both_skills_into_both_environments(self):
        targets = self.module.installation_targets(self.home, "both")

        installed = self.module.install_sources(
            self.local, self.goutou, targets, force=False
        )

        self.assertEqual(set(targets.values()), set(installed))
        for key, target in targets.items():
            self.assertTrue((target / "SKILL.md").is_file(), key)

    def test_any_existing_target_prevents_all_writes_without_force(self):
        targets = self.module.installation_targets(self.home, "both")
        existing = targets["claude:goutoujunshi"]
        write_skill(existing, "goutoujunshi", "old")

        with self.assertRaisesRegex(self.module.InstallError, "已存在"):
            self.module.install_sources(self.local, self.goutou, targets, force=False)

        self.assertIn("# old", (existing / "SKILL.md").read_text(encoding="utf-8"))
        for target in targets.values():
            if target != existing:
                self.assertFalse(target.exists())

    def test_force_replaces_all_existing_targets(self):
        targets = self.module.installation_targets(self.home, "both")
        for key, target in targets.items():
            write_skill(target, target.name, f"old {key}")

        self.module.install_sources(self.local, self.goutou, targets, force=True)

        for target in targets.values():
            text = (target / "SKILL.md").read_text(encoding="utf-8")
            self.assertNotIn("# old", text)

    def test_force_failure_restores_every_existing_target(self):
        targets = self.module.installation_targets(self.home, "both")
        old_contents = {}
        for key, target in targets.items():
            write_skill(target, target.name, f"old {key}")
            old_contents[target] = (target / "SKILL.md").read_text(encoding="utf-8")

        calls = 0

        def failing_copytree(source, destination):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("simulated copy failure")
            return shutil.copytree(source, destination)

        with self.assertRaisesRegex(self.module.InstallError, "simulated copy failure"):
            self.module.install_sources(
                self.local,
                self.goutou,
                targets,
                force=True,
                copytree=failing_copytree,
            )

        for target, expected in old_contents.items():
            self.assertEqual(expected, (target / "SKILL.md").read_text(encoding="utf-8"))
            self.assertEqual([], list(target.parent.glob(f".{target.name}.*")))

    def test_clone_wraps_git_failure(self):
        class Result:
            returncode = 1
            stderr = "network unavailable"

        commands = []

        def runner(command, **kwargs):
            commands.append(command)
            return Result()

        with self.assertRaisesRegex(self.module.InstallError, "network unavailable"):
            self.module.clone_goutoujunshi(
                "https://example.invalid/goutoujunshi.git",
                self.root / "clone",
                runner=runner,
            )
        self.assertEqual("git", commands[0][0])
        self.assertIn("--depth", commands[0])


if __name__ == "__main__":
    unittest.main()
