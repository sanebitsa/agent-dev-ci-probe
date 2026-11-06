import tempfile
import unittest
from pathlib import Path
from agentdev.cli import bootstrap_project
from agentdev.validator import validate_tree


class BootstrapTests(unittest.TestCase):
    def test_python_project_has_real_test_and_agent_guidance(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "demo"
            bootstrap_project("python", "demo", out)
            self.assertTrue((out / "tests/test_hello.py").is_file())
            self.assertTrue((out / "docs/PRD.md").is_file())
            self.assertTrue((out / "docs/KANBAN.md").is_file())
            self.assertFalse((out / "docs/PRODUCT.md").exists())
            self.assertIn("Status: TEMPLATE", (out / "docs/PRD.md").read_text())
            self.assertIn("Status: TEMPLATE", (out / "docs/KANBAN.md").read_text())
            self.assertIn("docs/PRD.md", (out / "AGENTS.md").read_text())
            self.assertIn("docs/KANBAN.md", (out / "README.md").read_text())
            self.assertEqual((out / ".agentdev-profile").read_text().strip(), "python")
            self.assertTrue((out / ".agents/skills/independent-review/SKILL.md").is_file())
            with self.assertRaises(ValueError):
                bootstrap_project("python", "demo", out)

    def test_other_profiles_bootstrap(self):
        with tempfile.TemporaryDirectory() as tmp:
            for lang, filename in (("rust", "Cargo.toml"), ("cpp", "CMakeLists.txt"),
                                   ("dotnet", "AgentDev.slnx")):
                out = Path(tmp) / lang
                bootstrap_project(lang, lang, out)
                self.assertTrue((out / filename).is_file())
                self.assertIn("Status: TEMPLATE", (out / "docs/PRD.md").read_text())
                self.assertIn("Status: TEMPLATE", (out / "docs/KANBAN.md").read_text())
                self.assertFalse((out / "docs/PRODUCT.md").exists())