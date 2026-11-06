# Independent review contract

Each implementation PR receives a review from a **different execution context and authenticated identity** than its implementer. The reviewer checks correctness, explicit acceptance criteria, regressions, tests, security, data handling and relevant architectural choices.

Possible decisions: `APPROVED`, `CHANGES_REQUESTED` or `BLOCKED`. No decision is an implicit approval. A corrected head SHA always requires a fresh review.

## Trusted attestation

Only a configured trusted GitHub App may publish the `agent-independent-review` check. The check must be attached to the current PR head commit, with `status=completed`, `conclusion=success`, and App ID equal to the trusted configured ID. The App must attach a JSON `external_id` including:

```json
{"reviewed_sha":"<40 hex PR head>","reviewer_identity":"separate-reviewer","review_run_id":"unique-run","verdict":"APPROVED"}
```

The trusted publisher is responsible for establishing actual reviewer identity, proof of independent execution and content of findings. Matching metadata alone is not a cryptographic review and is **not** evidence if published by an untrusted identity. `agentdev gate-review` checks the App source, SHA, completion and metadata; it cannot install or authenticate a reviewer by itself.

Reviewers have read-only PR access. They cannot edit implementation, set their own authorized review check status, or merge. A dedicated trusted publisher may post the check only after verifying a separately produced review artifact.

## Merge policy

Pass only if current head, base state, required checks from trusted GitHub Apps, external review, branch rulesets, permissions and no blocking findings all agree. Missing or stale data blocks. Re-check immediately before merge; post-merge verify the integrated commit separately.
