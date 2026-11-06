"""Common interface for language-specific verification commands."""
from __future__ import annotations

import os
import subprocess
import tomllib
from pathlib import Path

OPS = ("setup", "format_check", "lint", "static", "test", "build")
VERIFY_OPS = ("format_check", "lint", "static", "build", "test")
LANGUAGES = ("python", "rust", "cpp", "dotnet")


def load_profile(root: Path, language: str) -> dict[str, list[str]]:
    if language not in LANGUAGES:
        raise ValueError(f"unsupported language: {language}")
    with (root / "profiles" / language / "profile.toml").open("rb") as f:
        data = tomllib.load(f)
    commands = data["commands"]
    for op in OPS:
        argv = commands.get(op)
        if not isinstance(argv, list) or not argv or not all(isinstance(x, str) and x for x in argv):
            raise ValueError(f"invalid command for {language}:{op}")
    return commands


def run_profile(root: Path, language: str, project: Path, *, operation: str = "verify",
                include_setup: bool = False, dry_run: bool = False) -> list[str]:
    commands = load_profile(root, language)
    if not project.is_dir():
        raise ValueError(f"project directory does not exist: {project}")
    if operation != "verify" and operation not in OPS:
        raise ValueError(f"unknown operation: {operation}")
    steps = (["setup"] if include_setup else []) + (list(VERIFY_OPS) if operation == "verify" else [operation])
    result = []
    for step in steps:
        cmd = commands[step]
        print(f"[{language}:{step}] {' '.join(cmd)}", flush=True)
        result.append(step)
        if not dry_run:
            subprocess.run(cmd, check=True, cwd=project, env=os.environ.copy())
    return result
