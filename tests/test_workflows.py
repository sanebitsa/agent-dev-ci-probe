import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class WorkflowTests(unittest.TestCase):
    def test_review_diagnostic_requires_trusted_app(self):
        content = (ROOT / ".github/workflows/agent-review.yml").read_text()
        self.assertIn("AGENTDEV_REVIEW_APP_ID", content)
        self.assertIn("gate-review", content)
        self.assertIn("ref: main", content)
        self.assertNotIn("pull_request_target:", content)

    def test_integration_does_not_use_pr_checkout(self):
        content = (ROOT / ".github/workflows/integration.yml").read_text()
        self.assertIn("environment: trusted-integration", content)
        self.assertIn("ref: main", content)
        self.assertIn("gate-integration", content)
        self.assertIn("rulesets", content)
        self.assertNotIn("pull_request_target:", content)

    def test_security_does_not_skip_secret_scan(self):
        content = (ROOT / ".github/workflows/security.yml").read_text()
        self.assertIn("gitleaks/gitleaks-action@v3", content)

    def test_release_does_not_merge(self):
        content = (ROOT / ".github/workflows/release-validation.yml").read_text()
        self.assertNotIn("gh pr merge", content)
