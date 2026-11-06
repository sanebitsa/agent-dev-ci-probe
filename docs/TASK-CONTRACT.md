# Task assignment contract

An assigned task is derived from an **approved** PRD and dependency plan. `issue_number` refers to the authoritative GitHub Issue. Every task must represent a small, testable vertical slice with observable acceptance criteria.

| Field | Requirement |
|---|---|
| `issue_number` | Positive GitHub Issue number |
| `objective` | One bounded, independently testable vertical-slice outcome |
| `mode` | **Required**: `AFK` or `HUMAN` |
| `milestone` | Project delivery milestone (production task planning) |
| `prd_refs` | Stable PRD requirement IDs (production task planning) |
| `human_gate` | Required decision, authority, or evidence for **HUMAN** tasks; empty for AFK |
| `evidence_required` | Planned acceptance/test evidence (production task planning) |
| `acceptance` | Nonempty, verifiable pass/fail criteria |
| `dependencies` | Issue numbers already verified Done before AFK dispatch |
| `base_sha` | Exact 40-hex development HEAD at assignment |
| `branch` | Unique `agent/<issue>-<slug>` ref for implementation |
| `write_paths` | Conservative relative paths reserved for this task |
| `risk` | `standard`, `elevated`, or `restricted` |
| `runtime` | Authorized runtime adapter |
| `run_id` | Coordinator-generated unique execution ID |
| `agent_identity` | Authenticated implementation identity |
| `retry_budget` | Bounded retries before Blocked |

The local model validates mode, HUMAN gate description, dependency shape, branch and scope, and optional planning metadata; production coordination must verify approved PRD, GitHub issue state and true acceptance evidence using authenticated sources. It must not infer readiness from prose, template files, or a local state snapshot. Neither HUMAN tasks nor restricted tasks may enter the AFK implementation queue.

## Example reference-scheduler task snapshot

```json
[{"issue_number": 12, "objective": "Validate user input through the CLI", "mode": "AFK", "milestone": "M1", "prd_refs": ["FR-01"], "evidence_required": ["CLI test and validation logs"], "acceptance": ["Invalid input is rejected by the CLI test"], "dependencies": [], "base_sha": "1111111111111111111111111111111111111111", "branch": "agent/12-input-validation", "write_paths": ["src/validation"], "risk": "standard", "runtime": "local-codex"}]
```

`agentdev schedule --tasks tasks.json --state .agentdev/state.json` remains a **local reference scheduler**, not a GitHub-authoritative claim or production dispatcher. Its `done` list is local simulation data, not authenticated acceptance evidence.

## Implementation and human-gate results

AFK execution returns issue/run IDs, PR URL, head SHA, changed paths, acceptance mapping, literal test output, blockers, retry count, and measured cost when available. HUMAN issues require an explicit dated human decision/acceptance evidence, not an agent-produced success assertion. Every merged AFK task requires CI against the integrated `development` commit before Done.