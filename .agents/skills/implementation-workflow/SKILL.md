---
name: implementation-workflow
description: Implement one approved dependency-ready AFK GitHub issue as a small, testable vertical slice with TDD and independent review.
---

1. Read the assigned Issue and relevant `docs/PRD.md`, `docs/KANBAN.md`, `docs/DEVELOPMENT.md` excerpts. Confirm approved product scope, assigned **AFK** mode, fulfilled dependencies, authority, base SHA, and write boundaries. Never implement a HUMAN issue or unapproved template plan.
2. Use a fresh worktree/checkout and isolated `agent/<issue>-<slug>` branch from exact `development` base SHA.
3. Implement the **smallest testable vertical slice**, demonstrating behavior across the relevant components rather than delivering an entire disconnected layer.
4. Write a focused failing test, run it to observe failure, implement the minimal behavior, refactor, and rerun relevant tests. Do not fabricate red/green evidence.
5. Run required language-profile verification and secret scans. Open a PR to `development` with acceptance-to-test mapping, exact head SHA, TDD evidence and known HUMAN gates/blockers.
6. A separate reviewer must approve and trusted exact-SHA checks must pass. Changes invalidate prior review. Implementer cannot self-review or merge using release credentials.
7. After integration, verify the merged development SHA before Issue Done. If blocked by HUMAN prerequisites, record the request and allow other independent AFK tasks to continue.