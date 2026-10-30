from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_SCRIPT = REPO_ROOT / "scripts" / "build_memory_index.py"
CONTENT_DIRS = ("profile", "people", "projects", "decisions", "journal", "open-loops", "moc")


class MemoryIndexTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        for dirname in CONTENT_DIRS:
            (self.root / dirname).mkdir(parents=True, exist_ok=True)
        (self.root / "scripts").mkdir()
        self.script = self.root / "scripts" / "build_memory_index.py"
        shutil.copy2(SOURCE_SCRIPT, self.script)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def write_memory(
        self,
        relative_path: str,
        body: str = "Conclusion: A synthetic fact for testing.",
        **overrides: object,
    ) -> Path:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        entry_id = path.stem
        top_dir = relative_path.split("/", 1)[0]
        entry_type = {
            "profile": "profile",
            "people": "person",
            "projects": "project",
            "decisions": "decision",
            "journal": "journal",
            "open-loops": "open-loop",
        }[top_dir]
        values = {
            "id": entry_id,
            "type": entry_type,
            "status": "active",
            "created": "2026-01-15",
            "updated": "2026-01-15",
            "author": "test-agent",
            "tags": ["test"],
            "projects": [],
            "people": [],
            "links": [],
            "contradicts": [],
            "supersedes": "null",
            "source": "manual",
            "recall_hint": "synthetic test memory",
            "confirm_required": "false",
        }
        values.update(overrides)
        lines = ["---"]
        for key, value in values.items():
            if isinstance(value, list):
                rendered = "[" + ", ".join(str(item) for item in value) + "]"
            else:
                rendered = str(value)
            lines.append(f"{key}: {rendered}")
        lines.extend(["---", "", "# Test memory", "", textwrap.dedent(body).strip(), ""])
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    def run_indexer(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(self.script), *args],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )

    def create_project(self, slug: str = "demo", status: str = "active") -> Path:
        return self.write_memory(
            f"projects/{slug}/project-{slug}.md",
            body=(
                f"Conclusion: The `{slug}` project is a synthetic test fixture.\n"
            ),
            projects=[slug],
            status=status,
        )

    def test_generates_index_and_is_idempotent(self) -> None:
        self.create_project()
        self.write_memory(
            "decisions/dec-2026-01-18-test.md",
            body="Conclusion: Use the deterministic test stack.",
            projects=["demo"],
        )

        first = self.run_indexer()
        self.assertEqual(first.returncode, 0, first.stderr)
        index = (self.root / "INDEX.md").read_text(encoding="utf-8")
        self.assertIn("demo", index)
        self.assertIn("dec-2026-01-18-test", index)
        self.assertTrue((self.root / "moc" / "project-demo.md").exists())

        second = self.run_indexer()
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn("already current", second.stdout)

    def test_check_detects_stale_index(self) -> None:
        self.create_project()
        self.assertEqual(self.run_indexer().returncode, 0)
        self.write_memory(
            "journal/journal-2026-01-19-test.md",
            body="Conclusion: A new fact changes the generated index.",
            projects=["demo"],
        )

        result = self.run_indexer("--check")
        self.assertEqual(result.returncode, 2)
        self.assertIn("stale", result.stderr.lower())

    def test_dangling_relation_is_an_error(self) -> None:
        self.create_project()
        self.write_memory(
            "decisions/dec-2026-01-18-dangling.md",
            links=["missing-memory-id"],
            projects=["demo"],
        )

        result = self.run_indexer()
        self.assertEqual(result.returncode, 2)
        self.assertIn("missing id", result.stderr)
        self.assertFalse((self.root / "INDEX.md").exists())

    def test_filename_must_equal_id(self) -> None:
        path = self.create_project()
        content = path.read_text(encoding="utf-8").replace("id: project-demo", "id: project-different")
        path.write_text(content, encoding="utf-8")

        result = self.run_indexer()
        self.assertEqual(result.returncode, 2)
        self.assertIn("filename must equal id", result.stderr)

    def test_strict_upgrades_missing_anchor_to_error(self) -> None:
        self.write_memory("decisions/dec-2026-01-18-unfiled.md")

        normal = self.run_indexer()
        self.assertEqual(normal.returncode, 0, normal.stderr)
        self.assertIn("missing project/person anchor", normal.stderr)
        self.assertIn("dec-2026-01-18-unfiled", (self.root / "moc" / "unfiled.md").read_text())

        strict = self.run_indexer("--strict")
        self.assertEqual(strict.returncode, 2)
        self.assertIn("missing project/person anchor", strict.stderr)

    def test_suggest_links_uses_project_anchor(self) -> None:
        self.create_project()
        self.write_memory(
            "decisions/dec-2026-01-18-target.md",
            projects=["demo"],
            tags=["architecture"],
        )
        self.write_memory(
            "decisions/dec-2026-01-19-candidate.md",
            projects=["demo"],
            tags=["architecture"],
        )

        result = self.run_indexer("--suggest-links", "dec-2026-01-18-target")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("dec-2026-01-19-candidate", result.stdout)
        self.assertIn("shared: project demo, tag architecture", result.stdout)

    def test_handwritten_obsolete_project_page_is_preserved(self) -> None:
        project = self.create_project()
        self.assertEqual(self.run_indexer().returncode, 0)
        page = self.root / "moc" / "project-demo.md"
        page.write_text(
            page.read_text(encoding="utf-8") + "\nHand-written note.\n",
            encoding="utf-8",
        )

        content = project.read_text(encoding="utf-8").replace("status: active", "status: archived")
        project.write_text(content, encoding="utf-8")
        result = self.run_indexer()

        self.assertEqual(result.returncode, 2)
        self.assertIn("hand-written content", result.stderr)
        self.assertTrue(page.exists())

    @unittest.skipUnless(shutil.which("git"), "git is required")
    def test_gitignored_memory_is_not_indexed(self) -> None:
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        (self.root / ".gitignore").write_text("profile/ignored.md\n", encoding="utf-8")
        self.write_memory(
            "profile/profile-visible.md",
            body="Conclusion: This profile may appear in the generated index.",
        )
        self.write_memory(
            "profile/ignored.md",
            body="Conclusion: This ignored profile must never appear in the index.",
        )

        result = self.run_indexer()
        self.assertEqual(result.returncode, 0, result.stderr)
        index = (self.root / "INDEX.md").read_text(encoding="utf-8")
        standing = (self.root / "moc" / "standing-rules.md").read_text(encoding="utf-8")
        self.assertIn("profile-visible", standing)
        self.assertNotIn("ignored", index)
        self.assertNotIn("ignored", standing)


class RepositoryFixtureTest(unittest.TestCase):
    def test_demo_index_is_current(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SOURCE_SCRIPT), "--check"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
