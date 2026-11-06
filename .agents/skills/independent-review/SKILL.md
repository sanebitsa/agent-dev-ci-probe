---
name: independent-review
description: Independently review an implementation PR for correctness, coverage, security, regressions and contract compliance without editing the implementation.
---

1. Verify reviewer identity and execution context are distinct from the implementation author.
2. Inspect the PR diff at the exact current head SHA, issue acceptance criteria and relevant architecture, not the implementer's narrative alone.
3. Check behavior, regression risks, test quality, credentials, trust boundaries, error handling and changes outside declared write scopes.
4. Record precise findings with file/line and reproduction when possible. Decide `APPROVED`, `CHANGES_REQUESTED` or `BLOCKED`.
5. Do not edit implementation files, approve your own work, or publish the trusted GitHub App check directly. Give findings to the separate attestation publisher.
6. Approval is valid for a single head SHA; any new commit requires re-review before integration.
