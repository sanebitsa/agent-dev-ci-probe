# Milestones and acceptance status

This repository starts as an honest foundation release. A complete autonomous v1.0 requires all listed gates.

| Milestone | Deliverable | Status |
|---|---|---|
| M1 | Contracts, four skills, profile manifests and sample projects | Foundation files implemented; CI toolchain validation pending |
| M2 | GitHub-authoritative coordinator, admin-enforced checks and locked claims | Not implemented; local reference scheduler only |
| M3 | Actual local and hosted dispatch, independent reviewer publisher, automatic integration | Not implemented; fail-closed verification and manual integration workflow scaffolds only |
| M4 | Idempotent GitHub API provisioning and end-to-end failure injection | Not implemented; publishing script and governance guides provided |
| M5 | Three-agent tested operation, metrics, and human-approved v1.0 | Not implemented |

## v1.0 system acceptance (all required)

- [ ] Fresh repository has verified branch protections and required checks.
- [ ] Python, Rust, C/C++ and .NET pass toolchain smoke tests.
- [ ] Concurrent coordinators never duplicate issue ownership.
- [ ] Two independent tasks execute on isolated branches.
- [ ] Each implementation PR receives a separate reviewer.
- [ ] Review rejection blocks merge until fixed and re-reviewed.
- [ ] Outdated, self-authored and forged evidence cannot authorize merge.
- [ ] Required failing CI or secret scan blocks merge.
- [ ] A correct PR merges to `development` without human involvement.
- [ ] Post-merge CI verifies integrated commit before issue Done.
- [ ] Failed post-merge validation blocks dependent work and triggers repair.
- [ ] Implementer cannot write or merge into `main`.
- [ ] Release requires distinct human authorization.
- [ ] Provisioning is idempotent and reports unsupported protection.
- [ ] All decisions, retries, findings and costs are traceable.

## Initial PR backlog

1. Foundation contracts and authority model.
2. Skills and template layout.
3. Toolchain profiles and smoke test environments.
4. Admin-configured trusted checks and rulesets.
5. GitHub-backed single-writer issue coordinator.
6. Isolated Codex CLI and hosted runtime adapters.
7. Independent reviewer App and autonomous safe integration.
8. Idempotent repository provisioning and diagnostics.
9. Four-language and mixed-runtime end-to-end tests.
10. Pilot, measure cost and release v1.0.

The first three are represented as a single foundation snapshot in this bundle; they have not yet met all their independent acceptance gates.
