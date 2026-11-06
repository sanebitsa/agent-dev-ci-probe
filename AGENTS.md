# Repository instructions

## Start here

- Read `README.md` for the project overview, `docs/PRD.md` for requirements and exclusions, and `docs/KANBAN.md` for dependency-ordered work and **AFK/HUMAN** gates.
- Follow `docs/DEVELOPMENT.md` for TDD, independent review, and merge procedures.
- `docs/PRD.md` and `docs/KANBAN.md` begin as **TEMPLATE**, not approved plans. Do not begin implementation until project scope is approved and dependency-ready issues exist.

## Implementation principles

- **Implement small, testable vertical slices.** Each task delivers observable functionality across the relevant components, not an entire architectural layer. Keep it independently reviewable, with explicit acceptance tests.
- **AFK** tasks may proceed only after all dependencies and approvals have verified evidence. **HUMAN** tasks require the designated human decision, authorization, environment access, or acceptance evidence. Never fabricate or waive a HUMAN gate.
- If a HUMAN gate blocks one task, record the blocker and continue other independent, dependency-ready AFK work.

## Non-negotiable development rules

- GitHub Issues own live task state and assignment; `docs/KANBAN.md` describes the approved dependency plan. `docs/PRD.md` owns product scope. Resolve conflicts rather than silently changing authority.
- Human approval is required for product-scope changes and releases to `main`.
- Implementers work on isolated `agent/<issue>-<slug>` branches based on `development`; never push directly to `development` or `main`.
- Use TDD for behavior changes: observed failing test, implementation, refactor, then required validation. Never claim unrun tests passed.
- Every implementation PR needs a separate independent reviewer and trusted exact-SHA review check. Never self-approve, forge status, or bypass protection.
- Verify the integrated `development` commit after merging before calling a task Done.
- Do not commit credentials, secrets, private keys, tokens or sensitive production data.
- If required permissions, runtime, CI, independent review, or trust configuration is unavailable, stop the affected integration and report a blocker instead of weakening controls.

Workflow contracts: `docs/TASK-CONTRACT.md`, `docs/REVIEW-CONTRACT.md`, and `docs/SECURITY.md`.