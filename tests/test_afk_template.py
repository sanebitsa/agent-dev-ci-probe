import tempfile
import unittest
from pathlib import Path
from agentdev.cli import bootstrap_project
from agentdev.validator import validate_tree

ROOT = Path(__file__).resolve().parents[1]


class AfkTemplateTests(unittest.TestCase):
    def test_source_docs_are_instructional(self):
        for name in ("PRD", "KANBAN"):
            content = (ROOT / "docs" / f"{name}.md").read_text()
            self.assertIn("Status: TEMPLATE", content)
            self.assertIn("## Purpose", content)
        self.assertIn("small, independently executable, testable vertical slices",
                      (ROOT / "docs/KANBAN.md").read_text())
        self.assertIn("## Start here", (ROOT / "AGENTS.md").read_text())

    def test_validator_requires_both_docs(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "project"
            bootstrap_project("python", "project", out)
            self.assertEqual(validate_tree(out), [])
            (out / "docs/KANBAN.md").unlink()
            errors = validate_tree(out)
            self.assertTrue(any("docs/KANBAN.md" in error for error in errors))