import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class ReadmeContractTests(unittest.TestCase):
    def test_readme_describes_runtime_link_and_three_modes(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("运行时联动", text)
        self.assertIn("联动模式（默认）", text)
        self.assertIn("纯改写模式", text)
        self.assertIn("降级模式", text)
        self.assertIn("voice-delta.json", text)

    def test_public_docs_do_not_claim_to_copy_or_learn_from_goutoujunshi(self):
        for relative in ("README.md", "THIRD_PARTY_NOTICES.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("本项目参考了", text)
            self.assertNotIn("结合关系判断工作流", text)

    def test_public_docs_do_not_contain_known_private_identifiers(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for private_identifier in ("私聊_",):
            self.assertNotIn(private_identifier, text)

    def test_readme_documents_dual_skill_installer(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for command in (
            "python install.py --target codex",
            "python install.py --target claude",
            "python install.py --target both",
        ):
            self.assertIn(command, text)
        self.assertIn("--force", text)
        self.assertIn("https://github.com/powerycy/goutoujunshi", text)
        self.assertIn("PolyForm Noncommercial License 1.0.0", text)


if __name__ == "__main__":
    unittest.main()
