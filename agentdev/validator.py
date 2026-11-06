"""Static checks for template completeness and discoverable agent skills."""
from __future__ import annotations

from pathlib import Path
from .profiles import LANGUAGES, load_profile

SKILLS = ("development-coordinator", "implementation-workflow", "change-verification", "independent-review")
REQUIRED = (
    "AGENTS.md", "README.md", "docs/TASK-CONTRACT.md", "docs/REVIEW-CONTRACT.md",
    "docs/SECURITY.md", "docs/DEVELOPMENT.md", "docs/WORKFLOW.md",
    "docs/PRD.md", "docs/KANBAN.md",
    ".github/workflows/ci.yml", ".github/workflows/security.yml",
    ".github/workflows/agent-review.yml", ".github/workflows/integration.yml",
    ".github/workflows/release-validation.yml",
)


def validate_tree(root: Path) -> list[str]:
    errors = [f"missing required file: {p}" for p in REQUIRED if not (root / p).is_file()]
    for skill in SKILLS:
        path = root / ".agents" / "skills" / skill / "SKILL.md"
        if not path.is_file():
            errors.append(f"missing skill: {skill}")
            continue
        content = path.read_text()
        if not content.startswith("---\n") or "\nname: " not in content or "\ndescription: " not in content:
            errors.append(f"invalid skill front matter: {skill}")
    for language in LANGUAGES:
        try:
            load_profile(root, language)
        except (OSError, KeyError, ValueError) as exc:
            errors.append(f"{language} profile: {exc}")
    return errors