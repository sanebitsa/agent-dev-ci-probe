# Executable orchestration roadmap

`agentdev/contracts.py`, `agentdev/scheduler.py` and `agentdev/review.py` provide deterministic reference primitives. They are not a service and do not launch agents.

Pending production adapters:

- `coordinator/`: GitHub Issue dispatcher with authoritative serialized writes, leases/recovery and dependency reconciliation.
- `runtime-adapters/`: isolated local Codex CLI executor, managed hosted executor, and bounded ChatGPT handoff.
- `review-gate/`: independently authenticated reviewer service and trusted GitHub App status publisher.
- `integration/`: event-triggered, source-verified merges and post-merge verification/repair.

Do not infer a completed milestone from these directory names. The current `integration.yml` is a manually dispatched, fail-closed entrypoint only.
