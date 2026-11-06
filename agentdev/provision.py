"""Fail-closed, idempotent GitHub repository provisioning through the user's gh CLI.

No secrets are accepted and no admin credentials are stored. The connection that
runs this code must have GitHub administration rights. All claimed applied
settings are checked again using the GitHub API.
"""
from __future__ import annotations

import base64
import json
import re
import subprocess
from dataclasses import asdict, dataclass, field
from typing import Any, Protocol
from urllib.parse import quote

LANGUAGES = ("python", "rust", "cpp", "dotnet")
REPOSITORY = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})/[A-Za-z0-9_.-]{1,100}$")


class GitHubError(Exception):
    def __init__(self, message: str, status: int | None = None):
        self.status = status
        super().__init__(message)


class Api(Protocol):
    def request(self, method: str, endpoint: str, payload: dict[str, Any] | None = None) -> Any: ...


class GhApi:
    """Use existing `gh auth` credentials, without accepting tokens as arguments."""

    def request(self, method: str, endpoint: str, payload: dict[str, Any] | None = None) -> Any:
        args = ["gh", "api", "--method", method, "--header", "Accept: application/vnd.github+json", endpoint]
        if payload is not None:
            args += ["--input", "-"]
        try:
            proc = subprocess.run(args, input=json.dumps(payload) if payload is not None else None,
                                  text=True, capture_output=True, timeout=45, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise GitHubError(f"gh API unavailable: {exc}") from exc
        if proc.returncode != 0:
            status = re.search(r"\bHTTP\s+([45]\d\d)\b", proc.stderr)
            raise GitHubError(proc.stderr.strip() or "GitHub API request failed",
                              int(status.group(1)) if status else None)
        if not proc.stdout.strip():
            return None
        try:
            return json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            raise GitHubError(f"GitHub returned non-JSON for {method} {endpoint}") from exc


@dataclass
class Step:
    name: str
    status: str
    detail: str


@dataclass
class Report:
    repository: str
    dry_run: bool
    foundation_only: bool = False
    steps: list[Step] = field(default_factory=list)

    def add(self, name: str, status: str, detail: str) -> None:
        self.steps.append(Step(name, status, detail))

    @property
    def blocked(self) -> bool:
        return any(step.status == "blocked" for step in self.steps)

    def as_dict(self) -> dict[str, Any]:
        return {"repository": self.repository, "dry_run": self.dry_run,
                "foundation_only": self.foundation_only,
                "foundation_ready": self.foundation_only and not self.blocked and not self.dry_run,
                "complete": not self.blocked and not self.dry_run and not self.foundation_only,
                "autonomous_development_ready": False,
                "steps": [asdict(step) for step in self.steps]}


SETTINGS = {"has_issues": True, "allow_squash_merge": True, "allow_merge_commit": False,
            "allow_rebase_merge": False, "delete_branch_on_merge": True}
LABELS = {"agent:ready": "238636", "agent:working": "0969da", "agent:reviewing": "8250df",
          "agent:blocked": "b42318"}


def required_checks(profile: str, *, actions_app_id: int, review_app_id: int | None = None,
                    release_app_id: int | None = None, branch: str) -> list[dict[str, Any]]:
    checks = ["template-contracts", "secret-scan"]
    if branch == "development":
        checks.extend([f"{lang}-smoke" for lang in LANGUAGES] if profile == "all" else [f"{profile}-smoke"])
    else:
        checks.append("release-candidate")
    result = [{"context": check, "integration_id": actions_app_id} for check in checks]
    if branch == "development" and review_app_id:
        result.append({"context": "agent-independent-review", "integration_id": review_app_id})
    if branch == "main" and release_app_id:
        result.append({"context": "human-release-approval", "integration_id": release_app_id})
    return result


def desired_ruleset(branch: str, profile: str, *, actions_app_id: int, review_app_id: int,
                    release_app_id: int) -> dict[str, Any]:
    checks = required_checks(profile, actions_app_id=actions_app_id,
                             review_app_id=review_app_id, release_app_id=release_app_id, branch=branch)
    return {"name": f"agentdev-{branch}", "target": "branch", "enforcement": "active",
            "bypass_actors": [],
            "conditions": {"ref_name": {"include": [f"refs/heads/{branch}"], "exclude": []}},
            "rules": [
                {"type": "deletion"}, {"type": "non_fast_forward"},
                {"type": "pull_request", "parameters": {
                    "dismiss_stale_reviews_on_push": True, "require_code_owner_review": False,
                    "require_last_push_approval": False, "required_approving_review_count": 0,
                    "required_review_thread_resolution": True,
                }},
                {"type": "required_status_checks", "parameters": {
                    "strict_required_status_checks_policy": True,
                    "required_status_checks": checks,
                }},
            ]}


def matches_ruleset(actual: dict[str, Any], expected: dict[str, Any]) -> bool:
    if any(actual.get(k) != expected[k] for k in ("name", "target", "enforcement", "conditions")):
        return False
    # Never claim security with unknown/hidden bypass permissions.
    if actual.get("bypass_actors", "unknown") != []:
        return False
    by_type = {rule.get("type"): rule for rule in actual.get("rules", [])}
    for wanted in expected["rules"]:
        observed = by_type.get(wanted["type"])
        if observed is None:
            return False
        params = wanted.get("parameters", {})
        present = observed.get("parameters", {})
        for key, value in params.items():
            if key == "required_status_checks":
                observed_checks = present.get(key, [])
                for wanted_check in value:
                    same_name = [x for x in observed_checks if x.get("context") == wanted_check["context"]]
                    if len(same_name) != 1 or same_name[0].get("integration_id") != wanted_check["integration_id"]:
                        return False
            elif key == "required_approving_review_count":
                if not isinstance(present.get(key), int) or present[key] < value:
                    return False
            elif present.get(key) != value:
                return False
    return True


class Provisioner:
    def __init__(self, api: Api, repo: str, *, dry_run: bool = False, template: bool = False,
                 actions_app_id: int | None = None, review_app_id: int | None = None,
                 release_app_id: int | None = None, foundation_only: bool = False):
        if not REPOSITORY.fullmatch(repo) or ".." in repo or repo.endswith(".git"):
            raise ValueError("repository must be OWNER/REPO")
        for ident in (actions_app_id, review_app_id, release_app_id):
            if ident is not None and ident <= 0:
                raise ValueError("GitHub App IDs must be positive integers")
        if foundation_only and any(ident is not None for ident in
                                   (actions_app_id, review_app_id, release_app_id)):
            raise ValueError("--foundation-only cannot be combined with trusted identity options")
        self.api, self.repo, self.dry_run, self.template = api, repo, dry_run, template
        self.foundation_only = foundation_only
        self.actions_app_id = actions_app_id
        self.review_app_id = review_app_id
        self.release_app_id = release_app_id
        self.base = f"repos/{repo}"
        self.report = Report(repo, dry_run, foundation_only=foundation_only)

    def get(self, path: str) -> Any:
        return self.api.request("GET", f"{self.base}/{path}")

    def apply(self, name: str, method: str, endpoint: str, payload: dict[str, Any],
              check: Any, *, explanation: str) -> None:
        if self.dry_run:
            self.report.add(name, "planned", explanation)
            return
        try:
            self.api.request(method, f"{self.base}/{endpoint}".rstrip("/"), payload)
            if not check():
                raise ValueError("GitHub read-back disagrees with desired configuration")
        except (GitHubError, ValueError) as exc:
            self.report.add(name, "blocked", f"Could not apply/verify: {exc}")
            return
        self.report.add(name, "verified", "Applied and verified through GitHub API")

    def run(self) -> Report:
        try:
            repo = self.api.request("GET", self.base)
        except GitHubError as exc:
            self.report.add("repository", "blocked", f"Could not read repository: {exc}")
            return self.report
        if repo.get("default_branch") != "main":
            self.report.add("default-branch", "blocked", "Expected main; refusing to change the default branch")
            return self.report
        if not repo.get("permissions", {}).get("admin"):
            self.report.add("administration", "blocked", "Admin permission required to provision settings")
            return self.report
        self.report.add("repository", "verified", "Authenticated repository and administrator access")
        changes = {key: value for key, value in SETTINGS.items() if repo.get(key) != value}
        if self.template and repo.get("is_template") is not True:
            changes["is_template"] = True
        if changes:
            self.apply("settings", "PATCH", "", changes,
                       lambda: all(self.api.request("GET", self.base).get(k) == v for k, v in changes.items()),
                       explanation=f"Would configure: {', '.join(sorted(changes))}")
        else:
            self.report.add("settings", "verified", "Repository settings already match")

        try:
            main = self.get("git/ref/heads/main")
            main_sha = main["object"]["sha"]
            try:
                dev = self.get("git/ref/heads/development")
            except GitHubError as exc:
                if exc.status != 404:
                    raise
                self.apply("development-branch", "POST", "git/refs",
                           {"ref": "refs/heads/development", "sha": main_sha},
                           lambda: self.get("git/ref/heads/development")["object"]["sha"] == main_sha,
                           explanation=f"Would create development from main {main_sha}")
            else:
                if not dev.get("object", {}).get("sha"):
                    raise ValueError("development has no commit")
                compare = self.get("compare/main...development")
                if not (compare.get("merge_base_commit") or {}).get("sha"):
                    raise ValueError("development and main have no common ancestor")
                self.report.add("development-branch", "verified", "Existing development shares main history")
        except (GitHubError, KeyError, ValueError, TypeError) as exc:
            self.report.add("development-branch", "blocked", f"Could not verify branch ancestry: {exc}")

        self.configure_labels()
        if self.foundation_only:
            self.report.add("rulesets", "deferred",
                            "Explicit foundation-only mode; no branch protections applied or verified. "
                            "Upgrade to an eligible GitHub plan and rerun full setup before autonomous integration")
        else:
            self.configure_rulesets()
        self.report.add("runtime-readiness", "pending",
                        "Trusted reviewer publisher, integration and release identities, and end-to-end negative tests are not provisioned by this command")
        return self.report

    def configure_labels(self) -> None:
        try:
            existing = {label["name"] for label in self.get("labels?per_page=100")}
            for name, color in LABELS.items():
                if name in existing:
                    self.report.add(f"label:{name}", "verified", "Preserved existing label")
                    continue
                encoded = quote(name, safe="")
                self.apply(f"label:{name}", "POST", "labels", {"name": name, "color": color},
                           lambda: self.get(f"labels/{encoded}").get("name") == name,
                           explanation="Would create missing label")
        except (GitHubError, KeyError, TypeError) as exc:
            self.report.add("labels", "blocked", f"Could not inspect labels: {exc}")

    def profile(self) -> str:
        try:
            marker = self.get("contents/.agentdev-profile")
        except GitHubError as exc:
            if exc.status == 404:
                return "all"
            raise
        if marker.get("encoding") != "base64":
            raise ValueError("Unsupported .agentdev-profile encoding")
        raw = base64.b64decode(marker.get("content", ""), validate=False).decode("utf-8").strip()
        if raw not in LANGUAGES:
            raise ValueError("Invalid .agentdev-profile")
        return raw

    def configure_rulesets(self) -> None:
        try:
            existing = self.get("rulesets?per_page=100")
            if not isinstance(existing, list):
                raise ValueError("Unexpected rulesets response")
        except GitHubError as exc:
            self.report.add("rulesets", "blocked",
                            "GitHub rulesets unavailable (plan/permission): " + str(exc))
            return
        except ValueError as exc:
            self.report.add("rulesets", "blocked", str(exc))
            return
        if not (self.actions_app_id and self.review_app_id and self.release_app_id):
            self.report.add("trusted-identities", "blocked",
                            "Provide --actions-app-id, --review-app-id and --release-app-id after installing distinct trusted GitHub Apps; never substitute the implementing agent")
            return
        try:
            profile = self.profile()
        except (GitHubError, ValueError) as exc:
            self.report.add("profile", "blocked", str(exc))
            return
        for branch in ("development", "main"):
            desired = desired_ruleset(branch, profile, actions_app_id=self.actions_app_id,
                                      review_app_id=self.review_app_id, release_app_id=self.release_app_id)
            name = desired["name"]
            matches = [r for r in existing if r.get("name") == name]
            if len(matches) > 1:
                self.report.add(f"ruleset:{branch}", "blocked", "Duplicate managed ruleset names")
            elif matches:
                try:
                    observed = self.get(f"rulesets/{matches[0]['id']}")
                    if matches_ruleset(observed, desired):
                        self.report.add(f"ruleset:{branch}", "verified", "Existing active ruleset verified")
                    else:
                        self.report.add(f"ruleset:{branch}", "blocked",
                                        "Existing managed ruleset differs; refusing to overwrite restrictions")
                except (GitHubError, KeyError) as exc:
                    self.report.add(f"ruleset:{branch}", "blocked", f"Could not read ruleset: {exc}")
            else:
                # A new policy is created active and fail-closed. Missing check providers will block merges.
                def check_created() -> bool:
                    found = [r for r in self.get("rulesets?per_page=100") if r.get("name") == name]
                    return len(found) == 1 and matches_ruleset(self.get(f"rulesets/{found[0]['id']}"), desired)
                self.apply(f"ruleset:{branch}", "POST", "rulesets", desired, check_created,
                           explanation=f"Would create active ruleset {name} (merges blocked until checks exist)")


