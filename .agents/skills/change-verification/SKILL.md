---
name: change-verification
description: Run relevant focused checks plus mandatory full formatting, lint, static analysis, build and tests for the selected language profile.
---

1. Determine the selected profile from the assigned task or `.agentdev-profile`.
2. Inspect `profiles/<language>/profile.toml`, confirm required tools exist and do not skip absent tools.
3. During edits run targeted tests. Before PR, execute `python3 -m agentdev verify --profile <language> --project <path>` plus configured secret scanning.
4. Collect literal command, exit status, test counts where available and commit SHA; note missing tests as a blocker.
5. Full checks must run again in trusted GitHub CI against PR HEAD, and after merge against integrated `development` HEAD.
6. Never change a required gate to optional merely to obtain green CI.
