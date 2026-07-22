import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
PYTHON = Path(sys.executable)
IMPORT_SCRIPT = ROOT / "girlfriend-reply-coach" / "scripts" / "import_weflow.py"
PROFILE_SCRIPT = ROOT / "girlfriend-reply-coach" / "scripts" / "profile_store.py"


class ScriptCliTests(unittest.TestCase):
    def test_profile_cli_reports_voice_status_for_first_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "private"
            result = subprocess.run(
                [
                    str(PYTHON),
                    str(PROFILE_SCRIPT),
                    "voice-status",
                    "--root",
                    str(root),
                ],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            self.assertEqual("missing", json.loads(result.stdout)["status"])

    def test_profile_cli_marks_all_generated_profiles_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "private"
            result = subprocess.run(
                [
                    str(PYTHON),
                    str(PROFILE_SCRIPT),
                    "mark-all-stale",
                    "--root",
                    str(root),
                ],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            self.assertEqual({"marked_stale": []}, json.loads(result.stdout))

    def test_import_cli_prints_summary_without_message_content_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "chat.txt"
            source.write_text(
                "2025-04-04 21:10:39 '我'\n这是私人正文\n", encoding="utf-8"
            )
            result = subprocess.run(
                [str(PYTHON), str(IMPORT_SCRIPT), str(source)],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            summary = json.loads(result.stdout)
            self.assertEqual(1, summary["message_count"])
            self.assertNotIn("这是私人正文", result.stdout)

    def test_profile_cli_creates_and_deletes_only_selected_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "private"
            subprocess.run(
                [
                    str(PYTHON),
                    str(PROFILE_SCRIPT),
                    "create",
                    "--root",
                    str(root),
                    "--slug",
                    "current",
                    "--alias",
                    "女朋友代号",
                ],
                check=True,
                capture_output=True,
            )
            self.assertTrue((root / "people" / "current" / "profile.json").exists())

            preview_result = subprocess.run(
                [
                    str(PYTHON),
                    str(PROFILE_SCRIPT),
                    "preview-delete",
                    "--root",
                    str(root),
                    "--slug",
                    "current",
                ],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            preview = json.loads(preview_result.stdout)
            self.assertTrue(all(Path(item).is_absolute() for item in preview["targets"]))

            failed = subprocess.run(
                [
                    str(PYTHON),
                    str(PROFILE_SCRIPT),
                    "delete",
                    "--root",
                    str(root),
                    "--slug",
                    "current",
                    "--confirm",
                    "wrong-token",
                ],
                capture_output=True,
            )
            self.assertNotEqual(0, failed.returncode)
            self.assertTrue((root / "people" / "current").exists())

            subprocess.run(
                [
                    str(PYTHON),
                    str(PROFILE_SCRIPT),
                    "delete",
                    "--root",
                    str(root),
                    "--slug",
                    "current",
                    "--confirm",
                    preview["confirmation_token"],
                ],
                check=True,
                capture_output=True,
            )
            self.assertFalse((root / "people" / "current").exists())

    def test_import_cli_rejects_private_output_inside_git_worktree(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "chat.txt"
            source.write_text(
                "2025-04-04 21:10:39 '我'\n私人正文\n", encoding="utf-8"
            )
            with tempfile.TemporaryDirectory(dir=ROOT) as repository_tmp:
                output = Path(repository_tmp) / "messages.json"
                result = subprocess.run(
                    [str(PYTHON), str(IMPORT_SCRIPT), str(source), "--output", str(output)],
                    capture_output=True,
                )

                self.assertNotEqual(0, result.returncode)
                self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
