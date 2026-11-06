# ADR-0001: GitHub as durable control plane

Status: Accepted, 2026-11-05.

GitHub Issues own state and ownership, Git commits/PRs own implementation, protected checks own CI/review evidence, `development` is the autonomous integration target, and `main` is human-controlled. A filesystem-only scheduler cannot act as a distributed ownership source. The reference implementation is for deterministic contract tests only. Production coordination uses a serialized trusted controller with GitHub-backed state and recovery.
