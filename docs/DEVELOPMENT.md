# Development workflow and quality gates

Read `AGENTS.md`, the approved project `docs/PRD.md` and `docs/KANBAN.md`, and the relevant GitHub Issue before implementing. A `TEMPLATE` PRD or Kanban is **not** authorization to start product work.

## Plan small vertical slices

1. Decompose the approved PRD into small, reviewable **vertical slices** with observable end-to-end behavior, verifiable acceptance criteria, requirement links, and dependencies. Do not build an entire layer before exposing behavior.
2. Classify every task as **AFK** or **HUMAN**. AFK means independently testable once prerequisites are met; HUMAN requires recorded human permission, decision, live validation, host access, or release authorization.
3. Keep `docs/KANBAN.md` as the approved dependency plan and GitHub Issues as the live state/assignment record. A dependency is Done only with recorded acceptance evidence, including post-merge validation when applicable.
4. Never silently weaken a HUMAN gate. Record what is needed, mark the issue awaiting human action, and let the coordinator continue unrelated Ready AFK tasks.

## Required test-driven development

For every behavior change or bug fix: **red** (run a focused failing test), **green** (smallest change that passes), **refactor** (rerun relevant tests). Prefer synthetic fixtures; do not claim unavailable real-environment tests passed. Documentation-only edits require consistency/link review, not contrived failing tests. Record actual commands, results, and missing evidence in the PR.

## AFK implementation and review lifecycle

1. Coordinator verifies project approval, GitHub issue, declared mode **AFK**, dependency completion, exact `development` base SHA, assigned scopes, and an available agent slot. A local scheduler snapshot is not authoritative.
2. Implementer checks out an isolated `agent/<issue>-<slug>` branch and implements one bounded vertical slice with TDD.
3. Run focused tests, full language-profile checks, and secret scanning; open a PR to `development` with requirement traceability, actual test evidence, blockers, and the current head SHA.
4. An **independent reviewer**, different from the implementer, checks acceptance, regressions, safety, and evidence. Any change to the head SHA invalidates previous review. Missing independent review leaves the PR unmerged.
5. Only an authorized integration controller may merge into protected `development` after verifying all trusted checks and review. Until protections and trusted identities exist, use manual review/integration and do not describe it as autonomous.
6. Verify CI and applicable integration tests on the **merged `development` SHA**. Record results before updating the GitHub Issue to Done. Failed integration blocks dependent work and triggers repair or revert.

## HUMAN gates and release

- A HUMAN issue must specify the exact decision/authorization/evidence required and who can provide it. The agent can prepare a safe proposal but cannot resolve or falsify the gate.
- Once that evidence is recorded and approved, update the issue and its dependent tasks; keep other ready AFK work moving in parallel.
- Major milestones require independent acceptance review against PRD and Kanban; unverified HUMAN criteria remain blockers.
- Only the product owner authorizes scope changes and releases to `main`; implementation/review agents have no release credentials.

## Operational constraints

Keep tasks scoped, prioritize reviewers over launching extra implementers, and never commit secrets. Missing tools, CI, protections, or permissions are Blocked, not Passed. For first adoption use a single unprivileged agent; only enable unattended integration after trusted reviewer and branch protections are independently verified.