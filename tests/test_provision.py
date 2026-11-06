"""Offline security and idempotency tests for GitHub administration setup."""
from __future__ import annotations

import base64
import copy
import unittest

from agentdev.cli import build_parser
from agentdev.provision import (GhApi, GitHubError, Provisioner, desired_ruleset, matches_ruleset)

REPO = "repos/sanebitsa/demo"
MAIN_SHA = "a" * 40


class FakeAPI:
    def __init__(self, *, ruleset_status=200, admin=True, dev=False, profile=None):
        self.ruleset_status = ruleset_status
        self.settings = {
            "default_branch": "main", "permissions": {"admin": admin}, "is_template": False,
            "has_issues": False, "allow_squash_merge": False, "allow_merge_commit": True,
            "allow_rebase_merge": True, "delete_branch_on_merge": False,
        }
        self.branches = {"main": MAIN_SHA}
        if dev:
            self.branches["development"] = MAIN_SHA
        self.labels: dict[str, dict] = {}
        self.rulesets: list[dict] = []
        self.writes: list[tuple[str, str]] = []
        self.profile_name = profile
        self.error_on_create_ref = False
        self.fail_settings_once = False
        self.no_common_ancestor = False

    def request(self, method, endpoint, payload=None):
        if method != "GET":
            self.writes.append((method, endpoint))
        if endpoint == REPO:
            if method == "GET":
                return copy.deepcopy(self.settings)
            if method == "PATCH":
                if self.fail_settings_once:
                    self.fail_settings_once = False
                    raise GitHubError("HTTP 403 admin write denied", 403)
                self.settings.update(payload)
                return copy.deepcopy(self.settings)
        path = endpoint.removeprefix(REPO + "/")
        if path in ("git/ref/heads/main", "git/ref/heads/development") and method == "GET":
            key = path.rsplit("/", 1)[-1]
            if key not in self.branches:
                raise GitHubError("HTTP 404 branch not found", 404)
            return {"object": {"sha": self.branches[key]}}
        if path == "git/refs" and method == "POST":
            if self.error_on_create_ref or "development" in self.branches:
                raise GitHubError("HTTP 422 duplicate ref", 422)
            self.branches["development"] = payload["sha"]
            return {"ref": payload["ref"]}
        if path == "compare/main...development" and method == "GET":
            return {"merge_base_commit": None if self.no_common_ancestor else {"sha": MAIN_SHA}}
        if path == "labels?per_page=100" and method == "GET":
            return copy.deepcopy(list(self.labels.values()))
        if path.startswith("labels/") and method == "GET":
            from urllib.parse import unquote
            return copy.deepcopy(self.labels[unquote(path[7:])])
        if path == "labels" and method == "POST":
            self.labels[payload["name"]] = payload
            return payload
        if path == "contents/.agentdev-profile" and method == "GET":
            if self.profile_name is None:
                raise GitHubError("HTTP 404 not found", 404)
            return {"encoding": "base64", "content": base64.b64encode(self.profile_name.encode()).decode()}
        if path == "rulesets?per_page=100" and method == "GET":
            if self.ruleset_status != 200:
                raise GitHubError("HTTP 403 Upgrade to GitHub Pro or make repository public", self.ruleset_status)
            return [{"id": r["id"], "name": r["name"]} for r in self.rulesets]
        if path == "rulesets" and method == "POST":
            record = copy.deepcopy(payload)
            record["id"] = len(self.rulesets) + 1
            self.rulesets.append(record)
            return record
        if path.startswith("rulesets/") and method == "GET":
            idx = int(path.rsplit("/", 1)[1])
            return copy.deepcopy(self.rulesets[idx - 1])
        raise AssertionError(f"Unexpected API {method} {endpoint} {payload}")


class ProvisionTests(unittest.TestCase):
    def run_provision(self, api, **kwargs):
        return Provisioner(api, "sanebitsa/demo", **kwargs).run()

    def test_cli_accepts_setup_github_and_dry_run(self):
        args = build_parser().parse_args(["setup", "github", "sanebitsa/demo", "--dry-run", "--json"])
        self.assertEqual(args.command, "setup")
        self.assertTrue(args.dry_run)

    def test_dry_run_never_mutates(self):
        api = FakeAPI()
        report = self.run_provision(api, dry_run=True)
        self.assertEqual(api.writes, [])
        self.assertFalse(report.as_dict()["complete"])
        self.assertIn("planned", [x.status for x in report.steps])

    def test_repeated_setup_is_idempotent(self):
        api = FakeAPI()
        opts = {"actions_app_id": 42, "review_app_id": 43, "release_app_id": 44, "template": True}
        first = self.run_provision(api, **opts)
        self.assertEqual(len(api.rulesets), 2)
        self.assertTrue(api.settings["is_template"])
        self.assertIn("development", api.branches)
        self.assertFalse(first.blocked)
        count = len(api.writes)
        again = self.run_provision(api, **opts)
        self.assertEqual(len(api.writes), count)
        self.assertFalse(again.blocked)
        self.assertFalse(again.as_dict()["autonomous_development_ready"])

    def test_explicit_foundation_only_succeeds_on_github_free(self):
        api = FakeAPI(ruleset_status=403)
        report = self.run_provision(api, foundation_only=True, template=True)
        data = report.as_dict()
        self.assertFalse(report.blocked)
        self.assertTrue(data["foundation_ready"])
        self.assertFalse(data["complete"])
        self.assertFalse(data["autonomous_development_ready"])
        self.assertTrue(api.settings["is_template"])
        self.assertEqual(api.rulesets, [])
        self.assertTrue(any(step.name == "rulesets" and step.status == "deferred" for step in report.steps))
        self.assertFalse(any("rulesets" in endpoint for _, endpoint in api.writes))

    def test_foundation_only_rejects_trusted_identity_options(self):
        with self.assertRaisesRegex(ValueError, "foundation-only"):
            self.run_provision(FakeAPI(), foundation_only=True, actions_app_id=42)

    def test_foundation_only_dry_run_has_no_writes(self):
        api = FakeAPI(ruleset_status=403)
        report = self.run_provision(api, foundation_only=True, dry_run=True)
        self.assertFalse(report.as_dict()["foundation_ready"])
        self.assertEqual(api.writes, [])

    def test_cli_accepts_foundation_only(self):
        args = build_parser().parse_args(["setup", "github", "sanebitsa/demo", "--foundation-only"])
        self.assertTrue(args.foundation_only)

    def test_private_free_rulesets_403_is_blocker_not_success(self):
        api = FakeAPI(ruleset_status=403)
        report = self.run_provision(api, actions_app_id=42, review_app_id=43, release_app_id=44)
        self.assertTrue(report.blocked)
        self.assertFalse(report.as_dict()["complete"])
        self.assertIn("GitHub Pro", next(s.detail for s in report.steps if s.name == "rulesets"))
        self.assertFalse(any(path.endswith("/rulesets") for method, path in api.writes))

    def test_missing_trusted_identities_blocks_protections(self):
        api = FakeAPI()
        report = self.run_provision(api)
        self.assertTrue(report.blocked)
        self.assertEqual(api.rulesets, [])
        self.assertIn("trusted-identities", [s.name for s in report.steps])

    def test_no_admin_access_cannot_mutate(self):
        api = FakeAPI(admin=False)
        report = self.run_provision(api)
        self.assertTrue(report.blocked)
        self.assertEqual(api.writes, [])

    def test_existing_labels_not_changed(self):
        api = FakeAPI()
        api.labels["agent:ready"] = {"name": "agent:ready", "color": "abcdef"}
        self.run_provision(api)
        self.assertEqual(api.labels["agent:ready"]["color"], "abcdef")

    def test_missing_development_created_from_main(self):
        api = FakeAPI()
        self.run_provision(api)
        self.assertEqual(api.branches["development"], MAIN_SHA)

    def test_conflicting_development_creation_blocks(self):
        api = FakeAPI()
        api.error_on_create_ref = True
        report = self.run_provision(api)
        self.assertTrue(any(s.name == "development-branch" and s.status == "blocked" for s in report.steps))

    def test_diverged_unrelated_histories_block(self):
        api = FakeAPI(dev=True)
        api.no_common_ancestor = True
        report = self.run_provision(api)
        self.assertTrue(any(s.name == "development-branch" and s.status == "blocked" for s in report.steps))

    def test_partial_failure_is_safe_to_retry(self):
        api = FakeAPI()
        api.fail_settings_once = True
        opts = {"actions_app_id": 42, "review_app_id": 43, "release_app_id": 44}
        first = self.run_provision(api, **opts)
        self.assertTrue(first.blocked)
        result = self.run_provision(api, **opts)
        self.assertFalse(result.blocked)
        self.assertTrue(result.as_dict()["complete"])

    def test_existing_drifted_ruleset_not_overwritten(self):
        api = FakeAPI(dev=True)
        rule = desired_ruleset("development", "all", actions_app_id=42, review_app_id=43, release_app_id=44)
        rule["id"] = 1
        rule["bypass_actors"] = [{"actor_id": 12, "actor_type": "Integration", "bypass_mode": "always"}]
        api.rulesets.append(rule)
        report = self.run_provision(api, actions_app_id=42, review_app_id=43, release_app_id=44)
        self.assertTrue(any(s.name == "ruleset:development" and s.status == "blocked" for s in report.steps))
        self.assertFalse(any(method == "PUT" for method, _ in api.writes))

    def test_missing_or_forged_check_provider_rejected(self):
        wanted = desired_ruleset("development", "all", actions_app_id=42, review_app_id=43, release_app_id=44)
        actual = copy.deepcopy(wanted)
        self.assertTrue(matches_ruleset(actual, wanted))
        next(r for r in actual["rules"] if r["type"] == "required_status_checks")["parameters"]["required_status_checks"][0]["integration_id"] = 999
        self.assertFalse(matches_ruleset(actual, wanted))
        actual = copy.deepcopy(wanted)
        entries = next(r for r in actual["rules"] if r["type"] == "required_status_checks")["parameters"]["required_status_checks"]
        entries.append({"context": "template-contracts", "integration_id": 777})
        self.assertFalse(matches_ruleset(actual, wanted))

    def test_release_policy_requires_human_app_check(self):
        wanted = desired_ruleset("main", "all", actions_app_id=42, review_app_id=43, release_app_id=44)
        checks = next(r for r in wanted["rules"] if r["type"] == "required_status_checks")["parameters"]["required_status_checks"]
        self.assertIn({"context": "human-release-approval", "integration_id": 44}, checks)

    def test_profile_marker_limits_smoke_checks(self):
        api = FakeAPI(profile="rust")
        self.run_provision(api, actions_app_id=42, review_app_id=43, release_app_id=44)
        dev = next(r for r in api.rulesets if r["name"] == "agentdev-development")
        checks = next(r for r in dev["rules"] if r["type"] == "required_status_checks")["parameters"]["required_status_checks"]
        self.assertTrue(any(x["context"] == "rust-smoke" for x in checks))
        self.assertFalse(any(x["context"] == "python-smoke" for x in checks))

    def test_invalid_repo_refused(self):
        for name in ("foo", "../etc", "owner/repo/extra", "org/.git"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                Provisioner(FakeAPI(), name)


if __name__ == "__main__":
    unittest.main()


