"""Unit tests for session-pilot-lite."""
import io
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "session-pilot-lite" / "scripts"))


def skill(root, name, desc):
    d = root / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text(f"---\nname: {name}\ndescription: {desc}\n---\n# {name}\n", encoding="utf-8")


class SPLiteTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.skills = self.tmp / "skills"
        skill(self.skills, "fastapi-patterns", "FastAPI API backend, auth, pydantic")
        skill(self.skills, "react-testing", "React unit tests with testing library")
        skill(self.skills, "pdf-extractor", "Extract text from pdf documents")
        os.environ["SESSION_PILOT_LITE_HOME"] = str(self.tmp / "home")
        os.environ["SESSION_PILOT_LITE_NO_DEFAULTS"] = "1"
        os.environ["SESSION_PILOT_LITE_ROOTS"] = str(self.skills)
        os.environ["SESSION_PILOT_NO_AUTO_CONV"] = "1"
        import importlib
        import splite
        self.splite = importlib.reload(splite)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        os.environ.pop("SESSION_PILOT_LITE_HOME", None)
        os.environ.pop("SESSION_PILOT_LITE_NO_DEFAULTS", None)

    def run_sp(self, *args):
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.splite.main(list(args))
        return buf.getvalue().strip()

    def test_find_with_synonyms(self):
        self.run_sp("index", "--rebuild")
        # Searching 'api' triggers fastapi-patterns
        out = self.run_sp("find", "api endpoints")
        self.assertIn("match: strong", out)
        self.assertIn("fastapi-patterns", out)

        # Searching 'unittest' triggers react-testing via synonyms
        out = self.run_sp("find", "unittest react")
        self.assertIn("react-testing", out)

    def test_recall_and_save_minimal_tokens(self):
        self.assertEqual(self.run_sp("recall", "--session", "test-1"), "NEW SESSION test-1")
        save_out = self.run_sp("save", "--session", "test-1", "--goal", "ship feature", "--done", "setup", "--next", "test")
        self.assertEqual(save_out, "ok")  # Exact 2 characters, 1 token!
        rec_out = self.run_sp("recall", "--session", "test-1")
        self.assertEqual(rec_out, "SESSION test-1 | goal: ship feature | next: test")

    def test_auto_gc_on_project_deletion(self):
        pdir = self.tmp / "my-proj"
        pdir.mkdir(parents=True)
        self.run_sp("save", "--session", "proj-s", "--cwd", str(pdir), "--goal", "work")
        # Delete project folder
        shutil.rmtree(pdir)
        # Recall detects deletion and yields NEW SESSION
        out = self.run_sp("recall", "--session", "proj-s")
        self.assertEqual(out, "NEW SESSION proj-s")

    def test_import_wires_agents_md(self):
        pdir = self.tmp / "imported-proj"
        pdir.mkdir(parents=True)
        (pdir / "README.md").write_text("# Project Info\n", encoding="utf-8")
        out = self.run_sp("import", str(pdir))
        self.assertIn("imported imported-proj", out)
        # Verify AGENTS.md exists
        agents_md = pdir / "AGENTS.md"
        self.assertTrue(agents_md.exists())
        self.assertIn("session-pilot-lite", agents_md.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
