# Security and trust boundaries

## Non-negotiable separation

- Implementer: task branch writes and PR creation only. No branch protection admin or production credentials.
- Reviewer: read-only PR code, separate execution. Cannot modify code or publish its own trusted attestation.
- Trusted review service: separate GitHub App identity permitted to publish `agent-independent-review`; must check author separation and exact commit.
- Integration controller: distinct privileged identity for merging to protected `development` only, after verifying required checks from approved sources.
- Human: sole release authorizer and `main` integration identity. Never provide this credential to an agent.

The supplied local CLI and sample GitHub Actions do **not** create these identities. GitHub branch protections/rulesets and GitHub App restrictions must be configured by an administrator before unattended execution.

## Workflow safety

Ordinary `pull_request` workflows use read-only tokens. Never execute code from untrusted PR heads inside a privileged `pull_request_target` or `workflow_run` checkout. Never treat PR-authored labels, comments, files, self-reported tests or checks from an unapproved publisher as trusted approval. Avoid interpolating untrusted issue/PR strings into a shell command.

CI and review workflows are not enforcement without corresponding GitHub rulesets. Define required checks with their trusted GitHub App sources; use least-privilege token settings; disable force pushes, deletion and direct branch writes. Restrict workflow editing on agent branches where possible with repository governance.

## Secrets policy

Do not store passwords, access tokens, API credentials, SSH keys, environment secrets or customer data in commits. Pre-commit local checks are helpful but cannot be the sole gate. CI runs independent secret scanning; configure GitHub secret scanning and push protection where the plan supports it. Rotate any exposed credential immediately, even if the commit or branch was later deleted.

Provisioning must mark any unsupported protection as `BLOCKER` and must never silently relax security to make a sample pass.
