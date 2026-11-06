# Workflow and authority specification

## Authority

The human product owner authorizes product scope and releases. Agents may autonomously implement accepted work on branches and prepare release candidates, but must not alter product scope unilaterally or update `main`. An integration controller may merge eligible PRs to `development` only when its separate identity and all protected checks are verified.

Authoritative sources in order by domain:

1. Product scope: approved `docs/PRD.md`; architecture: `docs/ARCHITECTURE.md` and ADRs. A `TEMPLATE` PRD is not approved scope.
2. Approved task plan and AFK/HUMAN gates: `docs/KANBAN.md`; live task ownership, dependencies and state: GitHub Issues (never just a local state file).
3. Implementation: Git commits, PRs and exact head SHAs.
4. Tests and security: results emitted by trusted GitHub CI sources.
5. Independent review: attestation from a separately authenticated reviewer service.
6. Integration: passing checks against the integrated `development` commit.
7. Release: human-controlled `main` commit or signed release tag.

An Issue that contradicts approved scope cannot silently supersede the versioned product document. Escalate the scope decision.

## State machine

`ready -> claimed -> implementing -> pr_open -> reviewing -> review_approved -> integrating -> verifying -> done`.

`reviewing -> changes_requested -> implementing` re-enters review when the head SHA changes. `awaiting_human`, `blocked` and `failed` branches are explicit and retryable only under policy. HUMAN gates require real documented human evidence. The executable transition mapping is in `agentdev/contracts.py`.

## Coordination

The trusted coordinator assigns up to two independent tasks, later three after acceptance. Serialize authoritative GitHub claims (e.g. one GitHub Actions concurrency group for a single control-plane writer). Never treat filesystem locks as distributed GitHub claims. Assign only AFK tasks after verified project approval and task ownership are persisted; refuse HUMAN tasks, overlapping write paths, or incomplete dependencies (including HUMAN decisions). If a HUMAN gate blocks one slice, record the decision needed and continue independent ready AFK work. A template Kanban is not an actionable backlog. When reviewer resources are constrained, complete reviews before starting new implementation work.

## Branch and integration rules

Agents may push to `agent/*` branches based on `development`. They open PRs into `development`. Require unforgeable CI checks, secrets checks and a reviewer attestation against the current head SHA. The integration controller checks the latest base, review and protected-source status immediately before merge. Post-merge failures block dependent work and open a repair or revert task. Only the human identity can authorize a PR into `main`.

## Failure handling

No fabricated evidence, silent skips, forced merges, or self-reviewed PRs. Missing tooling/permissions is `blocked`, not `passed`. Record issue number, execution ID, observed error, bounded retry count, next action and preserved artifacts.