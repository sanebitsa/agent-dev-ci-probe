import json
import unittest
from copy import deepcopy
from agentdev.integration import active_ruleset_protects, integration_allowed

HEAD = "b" * 40
BASE = "a" * 40
CHECKS = {"template-contracts": 12, "secret-scan": 12, "agent-independent-review": 34,
          "python-smoke": 12}


def evidence():
    runs = [{"name": name, "head_sha": HEAD, "app": {"id": app},
             "status": "completed", "conclusion": "success"} for name, app in CHECKS.items()]
    runs[2]["external_id"] = json.dumps({"reviewed_sha": HEAD, "reviewer_identity": "reviewer",
                                           "review_run_id": "r1", "verdict": "APPROVED"})
    return {
        "pr": {"baseRefName": "development", "baseRefOid": BASE, "headRefOid": HEAD,
               "isDraft": False, "author": {"login": "implementer"}},
        "checks": runs,
        "rulesets": [{"enforcement": "active", "target": "branch", "bypass_actors": [],
                      "conditions": {"ref_name": {"include": ["refs/heads/development"], "exclude": []}},
                      "rules": [{"type": t} for t in ("pull_request", "non_fast_forward", "deletion")]
                      + [{"type": "required_status_checks", "parameters": {
                          "strict_required_status_checks_policy": True,
                          "required_status_checks": [{"context": name, "integration_id": app}
                                                     for name, app in CHECKS.items()]}}]}],
        "compare": {"behind_by": 0, "status": "ahead"}
    }


def allowed(e):
    return integration_allowed(pr=e["pr"], check_runs=e["checks"], rulesets=e["rulesets"],
                               compare=e["compare"], current_development_sha=BASE,
                               reviewer_app_id=34, actions_app_id=12, required_smoke_checks=["python-smoke"])


class IntegrationTests(unittest.TestCase):
    def test_all_trust_checks_required(self):
        self.assertTrue(allowed(evidence()))

    def test_no_ruleset_blocks(self):
        e = evidence()
        e["rulesets"] = []
        self.assertFalse(allowed(e))

    def test_bypass_blocks(self):
        e = evidence()
        e["rulesets"][0]["bypass_actors"] = [{"actor_id": 1}]
        self.assertFalse(allowed(e))

    def test_source_must_be_pinned(self):
        e = evidence()
        e["rulesets"][0]["rules"][3]["parameters"]["required_status_checks"][0]["integration_id"] = -1
        self.assertFalse(allowed(e))

    def test_stale_base_blocks(self):
        e = evidence()
        e["compare"]["behind_by"] = 1
        self.assertFalse(allowed(e))

    def test_stale_head_review_blocks(self):
        e = evidence()
        e["checks"][2]["head_sha"] = "c" * 40
        self.assertFalse(allowed(e))

    def test_failing_secret_scan_blocks(self):
        e = evidence()
        e["checks"][1]["conclusion"] = "failure"
        self.assertFalse(allowed(e))

    def test_main_target_blocks(self):
        e = evidence()
        e["pr"]["baseRefName"] = "main"
        self.assertFalse(allowed(e))

    def test_no_smoke_check_blocks(self):
        e = evidence()
        e["checks"] = [x for x in e["checks"] if x["name"] != "python-smoke"]
        self.assertFalse(allowed(e))
