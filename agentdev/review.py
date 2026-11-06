"""Validate external, trusted GitHub App review evidence for one PR head.

Only the GitHub Checks API is authoritative for this gate. A PR body, issue
comment, local file, or implementation-agent status cannot replace it.
"""
from __future__ import annotations

import json
import re
from typing import Any

_SHA = re.compile(r"^[0-9a-fA-F]{40}$")


def approved_review(check_runs: list[dict[str, Any]], *, head_sha: str,
                    trusted_app_id: int, author_login: str) -> bool:
    if not _SHA.fullmatch(head_sha) or trusted_app_id <= 0 or not author_login:
        return False
    for check in check_runs:
        if check.get("name") != "agent-independent-review":
            continue
        if check.get("head_sha", "").lower() != head_sha.lower():
            continue
        if check.get("app", {}).get("id") != trusted_app_id:
            continue
        if check.get("status") != "completed" or check.get("conclusion") != "success":
            continue
        try:
            metadata = json.loads(check.get("external_id") or "")
        except (ValueError, TypeError):
            continue
        reviewer = metadata.get("reviewer_identity", "")
        if (metadata.get("reviewed_sha", "").lower() == head_sha.lower()
                and metadata.get("verdict") == "APPROVED"
                and reviewer and reviewer.casefold() != author_login.casefold()
                and metadata.get("review_run_id")):
            return True
    return False
