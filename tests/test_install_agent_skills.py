from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_INSTALLER = REPO_ROOT / "scripts" / "install-agent-skills.sh"
SOURCE_SKILLS = REPO_ROOT / "skills"
BEGIN_MARK = "<!-- open-long-term-memory:begin -->"
END_MARK = "<!-- open-long-term-memory:end -->"


@unittest.skipUnless(os.name == "posix", "installer uses POSIX shell and symlinks")
class InstallAgentSkillsTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.repo = self.root / "repo"
        self.home = self.root / "home"
        (self.repo / "scripts").mkdir(parents=True)
        self.home.mkdir()
        shutil.copy2(SOURCE_INSTALLER, self.repo / "scripts" / "install-agent-skills.sh")
        shutil.copytree(SOURCE_SKILLS, self.repo / "skills")
        self.env = os.environ.copy()
        self.env["HOME"] = str(self.home)
        self.env.pop("CODEX_HOME", None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def run_installer(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["sh", "scripts/install-agent-skills.sh", *args],
            cwd=self.repo,
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_codex_install_creates_links_and_is_idempotent(self) -> None:
        instructions = self.home / ".codex" / "AGENTS.md"
        instructions.parent.mkdir()
        instructions.write_text("# Existing instructions\n", encoding="utf-8")

        first = self.run_installer("--agent", "codex")
        self.assertEqual(first.returncode, 0, first.stderr)

        for name in ("recall-long-term-memory", "write-long-term-memory"):
            link = self.home / ".codex" / "skills" / name
            self.assertTrue(link.is_symlink())
            self.assertEqual(link.resolve(), (self.repo / "skills" / name).resolve())

        text = instructions.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# Existing instructions\n"))
        self.assertEqual(text.count(BEGIN_MARK), 1)
        self.assertEqual(text.count(END_MARK), 1)
        self.assertIn(str(self.repo.resolve()), text)

        second = self.run_installer("--agent", "codex")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(instructions.read_text(encoding="utf-8"), text)

    def test_uninstall_removes_only_managed_state(self) -> None:
        instructions = self.home / ".codex" / "AGENTS.md"
        instructions.parent.mkdir()
        instructions.write_text("# Existing instructions\n\nKeep this line.\n", encoding="utf-8")

        self.assertEqual(self.run_installer("--agent", "codex").returncode, 0)
        result = self.run_installer("--agent", "codex", "--uninstall")
        self.assertEqual(result.returncode, 0, result.stderr)

        for name in ("recall-long-term-memory", "write-long-term-memory"):
            self.assertFalse((self.home / ".codex" / "skills" / name).exists())
        text = instructions.read_text(encoding="utf-8")
        self.assertNotIn(BEGIN_MARK, text)
        self.assertIn("Keep this line.", text)

    def test_refuses_to_replace_an_existing_skill_directory(self) -> None:
        conflict = self.home / ".codex" / "skills" / "recall-long-term-memory"
        conflict.mkdir(parents=True)

        result = self.run_installer("--agent", "codex")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refusing to replace existing path", result.stderr)
        self.assertFalse((self.home / ".codex" / "skills" / "write-long-term-memory").exists())
        self.assertFalse((self.home / ".codex" / "AGENTS.md").exists())

    def test_dry_run_changes_nothing(self) -> None:
        result = self.run_installer("--agent", "codex", "--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.home / ".codex").exists())
        self.assertIn("dry run complete", result.stdout)

    def test_claude_and_generic_paths(self) -> None:
        claude = self.run_installer("--agent", "claude")
        self.assertEqual(claude.returncode, 0, claude.stderr)
        self.assertTrue((self.home / ".claude" / "skills" / "recall-long-term-memory").is_symlink())
        self.assertTrue((self.home / ".claude" / "CLAUDE.md").is_file())

        generic_skills = self.root / "generic" / "skills"
        generic_instructions = self.root / "generic" / "INSTRUCTIONS.md"
        generic = self.run_installer(
            "--agent",
            "generic",
            "--skills-dir",
            str(generic_skills),
            "--instructions-file",
            str(generic_instructions),
        )
        self.assertEqual(generic.returncode, 0, generic.stderr)
        self.assertTrue((generic_skills / "recall-long-term-memory").is_symlink())
        self.assertIn(str(self.repo.resolve()), generic_instructions.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
