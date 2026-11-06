# Dependency-ordered Kanban backlog

**Status: TEMPLATE. Contains no approved tasks or ready implementation work.**

## Purpose

The approved **implementation plan** derived from `docs/PRD.md`. Decompose requirements into **small, independently executable, testable vertical slices** that demonstrate observable behavior across relevant system components, rather than building an entire architectural layer at once.

## Each project task must record

- Stable task identifier and title, linked GitHub Issue, milestone and priority.
- **Mode: AFK or HUMAN**, with exact reason and required decision/evidence for HUMAN work.
- Prerequisite task IDs; a task is Ready only after every predecessor has verified acceptance evidence.
- Related PRD requirement IDs, a bounded vertical slice, and observable acceptance criteria with tests.
- Relevant write boundaries or integration risks when needed.

## Execution modes and gates

- **AFK:** An agent can execute independently with synthetic/local or approved automated evidence **after** all dependencies and required HUMAN decisions are satisfied.
- **HUMAN:** A person must provide a product decision, permission, real-world/target-host access, live acceptance evidence, or release authorization. Never silently turn a HUMAN task into AFK.
- When HUMAN work blocks a task, record the exact blocker in its GitHub Issue and dispatch unrelated dependency-ready AFK tasks instead.
- Do not mark work Done without reproducible acceptance evidence and post-merge verification.

## Source of truth

- This document records the **approved dependency plan** and stable identifiers; GitHub Issues own live status, assignment, ownership, PRs, and blocker updates.
- Keep identifiers and dependencies aligned with GitHub Issues. Do not maintain a second independently editable live status board here.
- The coordinator must not interpret this untouched template as a backlog or schedule implementation from it. Populate it from an approved project PRD first.