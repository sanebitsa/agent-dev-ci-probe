# GitHub provisioning and audit

This template includes an **idempotent, fail-closed setup command** that operates
through your already authenticated GitHub CLI. It does **not** take a token on
the command line, store credentials, or silently lower a branch security policy.

```bash
# Inspect the repository and show proposed changes. Does not write to GitHub.
python3 -m agentdev setup github OWNER/REPO --dry-run --json

# Apply safe defaults, create development from main if needed, and add task labels.
# The command reports any unfulfilled protection requirements as blockers.
python3 -m agentdev setup github OWNER/REPO --json

# On the source template only, mark the repo as a GitHub template:
python3 -m agentdev setup github OWNER/agent-dev --template
```

## Free-plan template setup

Until you upgrade to GitHub Pro, use the explicit **foundation-only** option:

```bash
python3 -m agentdev setup github OWNER/agent-dev --template --foundation-only --dry-run --json
python3 -m agentdev setup github OWNER/agent-dev --template --foundation-only --json
```

This verifies safe repository settings, same-history development branch, and issue
labels without requiring paid-plan rulesets or creating trusted credentials. Its
report sets `foundation_ready=true` after successful application while keeping
`complete=false` and `autonomous_development_ready=false`. The protection step is
explicitly `deferred`, not `verified`. Without `--foundation-only`, missing
required protections remain a blocking error. Never use an unprotected
foundation for unattended agent merges or real production work.

The command requires a local `gh` installation authenticated with a user having
administrative access to the target repository (`gh auth login`). The credentials
used by your ChatGPT GitHub connection do not grant this script permission to
configure repository administration.

## What the command configures

- Verifies repository administrative access and requires `main` as the default branch.
- Enables Issues, squash merges, automatic deletion of merged branches, and disables
  merge-commit and rebase merge strategies.
- Creates `development` from the **same repository's** `main` SHA if absent.
- Preserves existing branches and labels, verifying that `development` shares history
  with `main`; refuses to overwrite or reset an unrelated branch.
- Creates task-state labels if missing without modifying existing label colors.
- Inspects current rulesets and reports private-GitHub-Free plan limitations.
- With installed, **distinct trusted identity App IDs**, installs fail-closed
  `agentdev-development` and `agentdev-main` rulesets with pinned check sources,
  up-to-date PR checks, force-push/deletion blocking, and no bypass actors. Existing
  managed rulesets are verified, never silently overwritten.

These prerequisites are *not* installed by the command. Supplying invented App
IDs does not make an app trusted or create its check runs. Do not use an agent
identity as the release App.

```bash
python3 -m agentdev setup github OWNER/REPO \
  --actions-app-id <verified-actions-id> \
  --review-app-id <independent-review-app-id> \
  --release-app-id <human-controlled-release-app-id> --json
```

The JSON report has machine-readable per-step statuses: `verified`, `planned`,
`deferred`, `blocked`, and `pending`. A blocked setup exits nonzero; `--dry-run` never writes
and never claims completion. Successful configuration **does not** mean that
runtime adapters, independent reviews, integration credentials, negative
security tests, or unattended merging are ready. `autonomous_development_ready`
remains `false` until those separate services are implemented and audited.

## Hard boundaries

- Private repositories on GitHub Free cannot enforce repository rulesets.
  The command reports GitHub HTTP 403 as a blocker; it does not make the repo
  public or replace mandatory checks with documentation.
- No release secrets, App private keys, or privileged GitHub API tokens are
  written to a repository or supplied to untrusted PR workflows.
- The command never enables unattended integration. That requires a dedicated
  integration credential, a real independent-review publisher, and negative
  end-to-end tests against bad/forged/stale checks.
- Existing rulesets with drift require an explicit security review; the tool
  does not replace user-created restrictions or reduce protections.
- If a PATCH/POST succeeds but GitHub read-back disagrees, the status is
  `blocked`. The safe default is to stop and diagnose, not to proceed.

After the setup command is complete, validate the project profiles through
Actions and perform disposable PR failure-injection tests before using the
repository for autonomous development. See `docs/ROADMAP.md`.

