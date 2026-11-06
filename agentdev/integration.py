"""Fail-closed check of trusted GitHub integration prerequisites.

All inputs must come from authenticated GitHub APIs, not a PR-authored file.
This pure validator is useful for negative tests and integration audits.
"""
from __future__ import annotations

from fnmatch import fnmatchcase
from typing import Any
from .review import approved_review


def checked_status(check_runs: list[dict[str, Any]], head_sha: str, name: str, app_id: int) -> bool:
    return app_id > 0 and any(
        run.get("name") == name
        and run.get("head_sha", "").lower() == head_sha.lower()
        and run.get("app", {}).get("id") == app_id
        and run.get("status") == "completed"
        and run.get("conclusion") == "success"
        for run in check_runs
    )


def active_ruleset_protects(rulesets: list[dict[str, Any]], checks: dict[str, int],
                            branch: str = "development") -> bool:
    found_rules = set()
    found_checks: set[str] = set()
    strict = False
    branch_ref = "refs/heads/" + branch
    for policy in rulesets:
        if policy.get("enforcement") != "active" or policy.get("target") != "branch":
            continue
        if policy.get("bypass_actors"):
            return False
        conditions = policy.get("conditions") or {}
        ref = conditions.get("ref_name") or {}
        patterns = ref.get("include") or []
        excluded = ref.get("exclude") or []
        if not any(pattern == branch_ref or fnmatchcase(branch_ref, pattern) for pattern in patterns):
            continue
        if any(pattern == branch_ref or fnmatchcase(branch_ref, pattern) for pattern in excluded):
            continue
        for rule in policy.get("rules") or []:
            rule_type = rule.get("type")
            if rule_type in {"pull_request", "non_fast_forward", "deletion"}:
                found_rules.add(rule_type)
            if rule_type == "required_status_checks":
                params = rule.get("parameters") or {}
                strict = strict or params.get("strict_required_status_checks_policy") is True
                for status in params.get("required_status_checks") or []:
                    context = status.get("context")
                    if context in checks and status.get("integration_id") == checks[context]:
                        found_checks.add(context)
    return (found_rules == {"pull_request", "non_fast_forward", "deletion"}
            and strict and found_checks == set(checks))


def integration_allowed(*, pr: dict[str, Any], check_runs: list[dict[str, Any]],
                        rulesets: list[dict[str, Any]], compare: dict[str, Any],
                        current_development_sha: str, reviewer_app_id: int,
                        actions_app_id: int, required_smoke_checks: list[str]) -> bool:
    sha = pr.get("headRefOid", "")
    author = (pr.get("author") or {}).get("login", "")
    if pr.get("baseRefName") != "development" or pr.get("isDraft") is not False:
        return False
    if pr.get("baseRefOid", "").lower() != current_development_sha.lower():
        return False
    if compare.get("behind_by") != 0 or compare.get("status") not in ("ahead", "identical"):
        return False
    checks = {"template-contracts": actions_app_id, "secret-scan": actions_app_id,
              "agent-independent-review": reviewer_app_id}
    for name in required_smoke_checks:
        if name not in {"python-smoke", "rust-smoke", "cpp-smoke", "dotnet-smoke"}:
            return False
        checks[name] = actions_app_id
    if not active_ruleset_protects(rulesets, checks):
        return False
    if not approved_review(check_runs, head_sha=sha, trusted_app_id=reviewer_app_id, author_login=author):
        return False
    return all(checked_status(check_runs, sha, name, app_id) for name, app_id in checks.items()
               if name != "agent-independent-review")
