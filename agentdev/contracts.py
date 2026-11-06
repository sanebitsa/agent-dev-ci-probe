"""Deterministic validation for task and workflow contracts.

These checks do not grant GitHub permissions or substitute for trusted CI.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import PurePosixPath
from typing import Any

_SHA = re.compile(r"^[0-9a-fA-F]{40}$")


class State(str, Enum):
    READY = "ready"
    CLAIMED = "claimed"
    IMPLEMENTING = "implementing"
    PR_OPEN = "pr_open"
    REVIEWING = "reviewing"
    CHANGES_REQUESTED = "changes_requested"
    REVIEW_APPROVED = "review_approved"
    INTEGRATING = "integrating"
    VERIFYING = "verifying"
    DONE = "done"
    AWAITING_HUMAN = "awaiting_human"
    BLOCKED = "blocked"
    FAILED = "failed"


TRANSITIONS: dict[State, frozenset[State]] = {
    State.READY: frozenset({State.CLAIMED, State.AWAITING_HUMAN, State.BLOCKED}),
    State.AWAITING_HUMAN: frozenset({State.READY, State.BLOCKED}),
    State.CLAIMED: frozenset({State.IMPLEMENTING, State.BLOCKED, State.FAILED}),
    State.IMPLEMENTING: frozenset({State.PR_OPEN, State.BLOCKED, State.FAILED}),
    State.PR_OPEN: frozenset({State.REVIEWING, State.BLOCKED}),
    State.REVIEWING: frozenset({State.REVIEW_APPROVED, State.CHANGES_REQUESTED, State.BLOCKED}),
    State.CHANGES_REQUESTED: frozenset({State.IMPLEMENTING, State.BLOCKED, State.FAILED}),
    State.REVIEW_APPROVED: frozenset({State.INTEGRATING, State.REVIEWING, State.BLOCKED}),
    State.INTEGRATING: frozenset({State.VERIFYING, State.BLOCKED, State.FAILED}),
    State.VERIFYING: frozenset({State.DONE, State.BLOCKED, State.FAILED}),
    State.DONE: frozenset(),
    State.BLOCKED: frozenset({State.READY, State.FAILED}),
    State.FAILED: frozenset({State.READY}),
}


def transition(current: State, requested: State) -> State:
    if requested not in TRANSITIONS[current]:
        raise ValueError(f"invalid task transition: {current.value} -> {requested.value}")
    return requested


def valid_path(path: str) -> str:
    """Ensure all write scopes are relative repository paths, never parent traversal."""
    if not isinstance(path, str) or not path or path.startswith("/") or "\\" in path:
        raise ValueError(f"invalid write scope: {path!r}")
    if path != "*" and ("*" in path or "?" in path or "[" in path):
        raise ValueError(f"write scope glob not supported: {path!r}")
    p = PurePosixPath(path)
    if any(part in ("..", ".") for part in path.split("/")) or str(p) in ("", "."):
        raise ValueError(f"invalid write scope: {path!r}")
    return str(p).rstrip("/")


def scopes_overlap(left: list[str], right: list[str]) -> bool:
    for a in left:
        a = valid_path(a)
        for b in right:
            b = valid_path(b)
            if a == "*" or b == "*" or a == b or a.startswith(b + "/") or b.startswith(a + "/"):
                return True
    return False


@dataclass(frozen=True)
class Task:
    issue_number: int
    objective: str
    acceptance: tuple[str, ...]
    dependencies: tuple[int, ...]
    base_sha: str
    branch: str
    write_paths: tuple[str, ...]
    mode: str
    milestone: str = ""
    prd_refs: tuple[str, ...] = ()
    human_gate: str = ""
    evidence_required: tuple[str, ...] = ()
    risk: str = "standard"
    runtime: str = "local-codex"

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Task":
        if "mode" not in raw:
            raise ValueError("task requires explicit AFK or HUMAN mode")
        task = cls(
            issue_number=raw["issue_number"], objective=raw["objective"],
            acceptance=tuple(raw["acceptance"]), dependencies=tuple(raw.get("dependencies", [])),
            base_sha=raw["base_sha"], branch=raw["branch"],
            write_paths=tuple(raw["write_paths"]), mode=raw["mode"],
            milestone=raw.get("milestone", ""), prd_refs=tuple(raw.get("prd_refs", [])),
            human_gate=raw.get("human_gate", ""),
            evidence_required=tuple(raw.get("evidence_required", [])), risk=raw.get("risk", "standard"),
            runtime=raw.get("runtime", "local-codex"),
        )
        task.validate()
        return task

    def validate(self) -> None:
        if type(self.issue_number) is not int or self.issue_number <= 0:
            raise ValueError("task requires a positive GitHub Issue number")
        if not self.objective.strip() or not self.acceptance or any(not x.strip() for x in self.acceptance):
            raise ValueError("task objective and nonempty acceptance criteria are mandatory")
        if not _SHA.fullmatch(self.base_sha):
            raise ValueError("task must be pinned to a 40-character development SHA")
        if not re.fullmatch(r"agent/[a-zA-Z0-9._/-]+", self.branch) or ".." in self.branch or self.branch.endswith("/"):
            raise ValueError("implementation branch must begin with agent/ and be unambiguous")
        if self.mode not in {"AFK", "HUMAN"}:
            raise ValueError("mode must be AFK or HUMAN")
        if self.mode == "HUMAN" and (not isinstance(self.human_gate, str) or not self.human_gate.strip()):
            raise ValueError("HUMAN task requires a human_gate description")
        if self.mode == "AFK" and self.human_gate:
            raise ValueError("AFK task cannot carry an unresolved human_gate")
        if not isinstance(self.milestone, str) or any(not isinstance(x, str) or not x.strip() for x in self.prd_refs + self.evidence_required):
            raise ValueError("invalid task planning metadata")
        if self.risk not in {"standard", "elevated", "restricted"}:
            raise ValueError("unknown task risk")
        if not self.write_paths:
            raise ValueError("task must declare write boundaries")
        for path in self.write_paths:
            valid_path(path)
        if self.issue_number in self.dependencies or any(type(n) is not int or n < 1 for n in self.dependencies):
            raise ValueError("invalid task dependencies")
        if len(set(self.dependencies)) != len(self.dependencies):
            raise ValueError("duplicate task dependencies")