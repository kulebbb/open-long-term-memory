from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_SCRIPT = REPO_ROOT / "scripts" / "memory-sync.sh"


@unittest.skipUnless(shutil.which("git"), "git is required")
class MemorySyncTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.remote = self.root / "remote.git"
        self.seed = self.root / "seed"
        self.local = self.root / "local"

        self.git(self.root, "init", "--bare", "--initial-branch=main", str(self.remote))
        self.git(self.root, "init", "--initial-branch=main", str(self.seed))
        self.git(self.seed, "config", "user.name", "Test User")
        self.git(self.seed, "config", "user.email", "test@example.invalid")
        (self.seed / "scripts").mkdir()
        shutil.copy2(SOURCE_SCRIPT, self.seed / "scripts" / "memory-sync.sh")
        (self.seed / "scripts" / "memory-sync.sh").chmod(0o755)
        self.git(self.seed, "add", "scripts/memory-sync.sh")
        (self.seed / "README.md").write_text("# Test memory\n", encoding="utf-8")
        self.commit_file(self.seed, "README.md", "initial commit")
        self.git(self.seed, "remote", "add", "origin", str(self.remote))
        self.git(self.seed, "push", "-u", "origin", "main")
        self.git(self.root, "clone", "-q", str(self.remote), str(self.local))
        self.git(self.local, "config", "user.name", "Test User")
        self.git(self.local, "config", "user.email", "test@example.invalid")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def git(self, cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )

    def commit_file(self, repo: Path, relative_path: str, message: str) -> None:
        path = repo / relative_path
        path.write_text(path.read_text(encoding="utf-8") + f"\n{message}\n", encoding="utf-8")
        self.git(repo, "add", relative_path)
        self.git(repo, "commit", "-q", "-m", message)

    def sync(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["sh", "scripts/memory-sync.sh"],
            cwd=self.local,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_reports_ok_when_clone_matches_remote(self) -> None:
        result = self.sync()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(result.stdout.startswith("OK main@"), result.stdout)

    def test_reports_ahead_for_unpushed_local_commit(self) -> None:
        self.commit_file(self.local, "README.md", "local only")
        result = self.sync()
        self.assertEqual(result.returncode, 5, result.stdout + result.stderr)
        self.assertTrue(result.stdout.startswith("AHEAD main@"), result.stdout)

    def test_reports_stale_when_uncommitted_changes_prevent_pull(self) -> None:
        other = self.root / "other"
        self.git(self.root, "clone", "-q", str(self.remote), str(other))
        self.git(other, "config", "user.name", "Other User")
        self.git(other, "config", "user.email", "other@example.invalid")
        self.commit_file(other, "README.md", "remote update")
        self.git(other, "push", "origin", "main")

        readme = self.local / "README.md"
        readme.write_text(readme.read_text(encoding="utf-8") + "\nlocal edit\n", encoding="utf-8")
        result = self.sync()
        self.assertEqual(result.returncode, 4, result.stdout + result.stderr)
        self.assertTrue(result.stdout.startswith("STALE main@"), result.stdout)

    def test_reports_diverged_when_both_sides_advance(self) -> None:
        other = self.root / "other"
        self.git(self.root, "clone", "-q", str(self.remote), str(other))
        self.git(other, "config", "user.name", "Other User")
        self.git(other, "config", "user.email", "other@example.invalid")
        self.commit_file(other, "README.md", "remote update")
        self.git(other, "push", "origin", "main")
        self.commit_file(self.local, "README.md", "local update")

        result = self.sync()
        self.assertEqual(result.returncode, 5, result.stdout + result.stderr)
        self.assertTrue(result.stdout.startswith("DIVERGED main@"), result.stdout)

    def test_reports_offline_when_remote_cannot_be_fetched(self) -> None:
        self.git(self.local, "remote", "set-url", "origin", str(self.root / "missing.git"))
        result = self.sync()
        self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
        self.assertTrue(result.stdout.startswith("OFFLINE "), result.stdout)


if __name__ == "__main__":
    unittest.main()
