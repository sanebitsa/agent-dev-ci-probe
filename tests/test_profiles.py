import unittest
from pathlib import Path
from agentdev.profiles import LANGUAGES, VERIFY_OPS, load_profile, run_profile
from agentdev.validator import validate_tree

ROOT = Path(__file__).resolve().parent.parent


class ProfileTests(unittest.TestCase):
    def test_all_profiles_expose_operations(self):
        for lang in LANGUAGES:
            with self.subTest(lang=lang):
                commands = load_profile(ROOT, lang)
                self.assertEqual(len(commands), 6)
                self.assertTrue(all(commands[step] for step in VERIFY_OPS))

    def test_combined_verify_orders_required_checks(self):
        self.assertEqual(run_profile(ROOT, "rust", ROOT / "examples/rust", dry_run=True), list(VERIFY_OPS))

    def test_python_build_has_isolated_backend(self):
        # A fresh CI runner need not install setuptools globally to build a project.
        build = load_profile(ROOT, "python")["build"]
        self.assertEqual(build[:3], ["python", "-m", "build"])
        self.assertNotIn("--no-isolation", build)

    def test_unknown_profile_blocked(self):
        with self.assertRaises(ValueError):
            load_profile(ROOT, "ruby")

    def test_complete_skills_and_contracts(self):
        self.assertEqual(validate_tree(ROOT), [])
