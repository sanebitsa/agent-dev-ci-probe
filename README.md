# Agent Dev

**A reusable foundation for autonomous development with human-controlled releases.**

A short name for the agentic development workflow template. The goal is to coordinate ChatGPT, local Codex and hosted coding agents using one GitHub-based source of truth and four common engineering procedures.

> **Status: foundation v0.1, not autonomous v1.0.** The language manifests, task-contract validation, local claim reference backend and exact-SHA review verifier are executable. Hosted dispatch, trusted reviewer installation, GitHub-backed atomic claims, automatic integration, branch protection and full cross-runtime acceptance are **not** activated by copying this repository. CI and documentation must never be mistaken for security enforcement.

## Quick start

```bash
python3 -m agentdev validate
python3 -m agentdev doctor --profile python
python3 -m agentdev verify --profile python --project examples/python --dry-run
python3 -m agentdev bootstrap --profile python --name demo --output ../demo
```

The generated project is local until published and provisioned with verified GitHub protections.

## Repository layout

| Path | Purpose |
|---|---|
| `AGENTS.md` | Small durable rules shared by coding agents |
| `.agents/skills/` | Coordinator, implementation, verification and review playbooks |
| `docs/` | Instructional PRD/Kanban templates; workflow, authority, task, review and security contracts |
| `profiles/` | Language-specific command manifests |
| `agentdev/` | Executable structural checks, runner, local claim model, review verifier |
| `examples/` | Testable Python, Rust, C/C++ and .NET pilot projects |
| `.github/workflows/` | Quality, secrets, fail-closed review, gated integration and release validation |
| `provisioning/` | Desired GitHub settings and administrative audit guidance |
| `scripts/` | Portable entrypoints, publishing and environment diagnostics |

## AFK-first project initialization

`docs/PRD.md` and `docs/KANBAN.md` are **instructional templates**, not fabricated requirements or a populated backlog. When creating a project, approve the product-specific PRD, derive small testable **vertical slices** in Kanban, mark each task **AFK** or **HUMAN**, and create GitHub Issues for the approved work. Only dependency-ready AFK issues may be assigned without human involvement. The coordinator continues independent AFK work while genuine HUMAN gates are pending. See `AGENTS.md` and `docs/DEVELOPMENT.md`.

No untouched template is implementation-ready and the reference scheduler is not a production GitHub coordinator.

## Unified validation

The profile interface is `setup`, `format_check`, `lint`, `static`, `test`, `build` and combined `verify`.

```bash
python3 -m agentdev verify --profile rust --project examples/rust --include-setup
python3 -m agentdev verify --profile cpp --project examples/cpp --include-setup
python3 -m agentdev verify --profile dotnet --project examples/dotnet --include-setup
```

A local run needs the corresponding compiler/SDK and tools. Hosted CI can install them independently. No required operation is silently skipped.

## GitHub setup

Run the GitHub setup tool using an **authenticated admin `gh` CLI**. It checks
repository configuration, creates a compatible `development` branch when needed,
and configures safe defaults and labels. It can also configure active branch
rulesets when your GitHub plan supports them **and** trusted GitHub App identities
are installed:

```bash
# GitHub Free, for building the template before enabling protected automation:
python3 -m agentdev setup github OWNER/agent-dev --foundation-only --template --json

# Full secured setup, when independent Apps and ruleset support exist:
python3 -m agentdev setup github OWNER/REPO --dry-run --json
python3 -m agentdev setup github OWNER/REPO --json
```

`--dry-run` never modifies the repo. An apply run reports a **blocker** instead
of silently weakening a missing security feature. For private GitHub Free
repositories, enforceable rulesets require GitHub Pro or an eligible plan.
The tool does not activate unattended mergers, install reviewer Apps or
provision production/release secrets. See `provisioning/README.md`.

Generate new projects from **main only**, then create `development` from the
new project's own history.

## First milestones

- **M1: Foundation (partially implemented):** contracts, skills, four profiles, example projects and tests. Toolchain smoke validation still required on hosted CI.
- **M2: Protected workflow (pending):** real admin-backed rulesets, trusted check sources and single-writer GitHub coordinator.
- **M3: Autonomous development (pending):** bounded local/hosted runtime adapters, independent review service and trusted automatic integration.
- **M4: Reusable template (pending):** idempotent GitHub provisioning and clean-room failure-injection tests.
- **M5: v1.0 (pending):** all 15 system-level acceptance gates and a human-controlled release rehearsal.

See `docs/ROADMAP.md` for detailed milestones and `docs/DEVELOPMENT.md` for agent procedures.

