"""Local developer CLI for portable verification, scheduling and gate checks."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from .contracts import Task
from .integration import integration_allowed
from .profiles import LANGUAGES, run_profile
from .review import approved_review
from .scheduler import claim_ready
from .validator import validate_tree

ROOT = Path(__file__).resolve().parent.parent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agentdev", description="Agent Dev workflow toolkit")
    command = parser.add_subparsers(dest="command", required=True)
    command.add_parser("validate", help="validate repository skills, contracts and manifests")
    verify = command.add_parser("verify", help="run normalized language profile operations")
    verify.add_argument("--profile", choices=LANGUAGES, required=True)
    verify.add_argument("--project", type=Path, required=True)
    verify.add_argument("--operation", default="verify", choices=("verify", "setup", "format_check", "lint", "static", "test", "build"))
    verify.add_argument("--include-setup", action="store_true")
    verify.add_argument("--dry-run", action="store_true")
    doctor = command.add_parser("doctor", help="check local prerequisites; does not modify GitHub")
    doctor.add_argument("--profile", choices=LANGUAGES, default="python")
    scheduler = command.add_parser("schedule", help="claim from a local JSON task snapshot (reference backend only)")
    scheduler.add_argument("--tasks", required=True, type=Path)
    scheduler.add_argument("--state", required=True, type=Path)
    scheduler.add_argument("--max-agents", type=int, default=2)
    gate = command.add_parser("gate-review", help="check exact-SHA GitHub App attestation")
    gate.add_argument("--checks-json", type=Path, required=True)
    gate.add_argument("--sha", required=True)
    gate.add_argument("--trusted-app-id", required=True, type=int)
    gate.add_argument("--author-login", required=True)
    integration = command.add_parser("gate-integration", help="verify protected rulesets and exact SHA CI/review evidence")
    integration.add_argument("--evidence-json", type=Path, required=True)
    integration.add_argument("--trusted-review-app-id", type=int, required=True)
    integration.add_argument("--actions-app-id", type=int, required=True)
    integration.add_argument("--required-smoke", nargs="+", required=True)
    setup = command.add_parser("setup", help="provision and verify GitHub repository configuration")
    setup.add_argument("provider", choices=("github",))
    setup.add_argument("repository", help="GitHub OWNER/REPO")
    setup.add_argument("--dry-run", action="store_true", help="inspect and plan without modifying GitHub")
    setup.add_argument("--foundation-only", action="store_true",
                       help="apply GitHub Free-compatible setup; explicitly defer protected automation")
    setup.add_argument("--json", action="store_true", help="emit machine-readable setup report")
    setup.add_argument("--template", action="store_true", help="mark this source repository as a template")
    setup.add_argument("--actions-app-id", type=int, help="trusted GitHub Actions App ID")
    setup.add_argument("--review-app-id", type=int, help="independent reviewer App ID")
    setup.add_argument("--release-app-id", type=int, help="human release attestation App ID")
    bootstrap = command.add_parser("bootstrap", help="generate a single-language local project")
    bootstrap.add_argument("--profile", choices=LANGUAGES, required=True)
    bootstrap.add_argument("--name", required=True)
    bootstrap.add_argument("--output", type=Path, required=True)
    return parser


def bootstrap_project(profile: str, name: str, output: Path) -> None:
    if not name or any(c in name for c in ("/", "\\", "\x00")) or name in (".", ".."):
        raise ValueError("invalid project name")
    if output.exists():
        raise ValueError(f"output already exists (refusing overwrite): {output}")
    output.mkdir(parents=True)
    for path in ("AGENTS.md", ".gitignore", ".editorconfig", "agentdev.toml"):
        shutil.copy2(ROOT / path, output / path)
    for directory in ("agentdev", "profiles", "scripts", "templates", "docs", ".agents", ".github", "provisioning"):
        shutil.copytree(ROOT / directory, output / directory, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    example = ROOT / "examples" / profile
    for item in example.iterdir():
        dest = output / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)
    # docs/PRD.md and docs/KANBAN.md are copied as intentionally unapproved, instructional templates.
    for doc in ("ARCHITECTURE.md",):
        (output / "docs" / doc).write_text((ROOT / "templates" / doc).read_text().replace("{{PROJECT_NAME}}", name))
    (output / ".agentdev-profile").write_text(profile + "\n")
    (output / "README.md").write_text(
        f"# {name}\n\nGenerated from Agent Dev using the `{profile}` profile.\n\n"
        "## Start\n\n1. Approve project requirements in `docs/PRD.md` and architecture in `docs/ARCHITECTURE.md`.\n"
        "2. Derive dependency-ordered AFK/HUMAN vertical slices in `docs/KANBAN.md` and create GitHub Issues.\n"
        "3. Run `python3 -m agentdev validate`.\n"
        f"4. Run `python3 -m agentdev verify --profile {profile} --project . --include-setup`.\n"
        "5. Provision protected GitHub branches, a trusted external reviewer and integration identities using `provisioning/README.md`.\n\n"
        "**PRD/KANBAN status: TEMPLATE. No implementation is authorized by these files alone.**\n\n"
        "**No automatic merging or release is authorized by this scaffold alone.**\n"
    )
    config_path = output / "agentdev.toml"
    config_path.write_text(config_path.read_text().replace('name = "agent-dev"', f'name = "{name}"'))


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "validate":
            errors = validate_tree(ROOT)
            for err in errors:
                print(f"ERROR: {err}")
            print("Template structural validation:", "PASS" if not errors else "FAIL")
            return int(bool(errors))
        if args.command == "setup":
            from .provision import GhApi, Provisioner
            report = Provisioner(GhApi(), args.repository, dry_run=args.dry_run, template=args.template,
                                 actions_app_id=args.actions_app_id, review_app_id=args.review_app_id,
                                 release_app_id=args.release_app_id, foundation_only=args.foundation_only).run()
            if args.json:
                print(json.dumps(report.as_dict(), indent=2))
            else:
                for step in report.steps:
                    print(f"{step.status.upper():8} {step.name}: {step.detail}")
                print("GitHub configuration:", "BLOCKED" if report.blocked else
                      "PLAN ONLY" if args.dry_run else
                      "FOUNDATION READY (unprotected; no automated integration)" if args.foundation_only else
                      "COMPLETE (runtime still requires separate acceptance)")
            return 1 if report.blocked else 0
        if args.command == "verify":
            run_profile(ROOT, args.profile, args.project.resolve(), operation=args.operation,
                        include_setup=args.include_setup, dry_run=args.dry_run)
        elif args.command == "doctor":
            from .profiles import load_profile
            profile = load_profile(ROOT, args.profile)
            missing = sorted({cmd[0] for cmd in profile.values() if not shutil.which(cmd[0])})
            print(json.dumps({"profile": args.profile, "missing_commands": missing,
                              "gh_available": bool(shutil.which("gh")),
                              "note": "No GitHub permissions, rulesets, or external reviewer are asserted by this check."}, indent=2))
            return int(bool(missing))
        elif args.command == "schedule":
            tasks = [Task.from_dict(x) for x in json.loads(args.tasks.read_text())]
            print(json.dumps(claim_ready(tasks, args.state, max_agents=args.max_agents), indent=2))
        elif args.command == "gate-review":
            raw = json.loads(args.checks_json.read_text())
            runs = raw["check_runs"] if isinstance(raw, dict) else raw
            passed = approved_review(runs, head_sha=args.sha, trusted_app_id=args.trusted_app_id,
                                     author_login=args.author_login)
            print("Trusted independent review:", "PASS" if passed else "BLOCKED")
            return 0 if passed else 1
        elif args.command == "gate-integration":
            evidence = json.loads(args.evidence_json.read_text())
            passed = integration_allowed(
                pr=evidence["pr"], check_runs=evidence["checks"]["check_runs"],
                rulesets=evidence["rulesets"], compare=evidence["compare"],
                current_development_sha=evidence["development_sha"],
                reviewer_app_id=args.trusted_review_app_id, actions_app_id=args.actions_app_id,
                required_smoke_checks=args.required_smoke)
            print("Trusted integration:", "PASS" if passed else "BLOCKED")
            return 0 if passed else 1
        elif args.command == "bootstrap":
            bootstrap_project(args.profile, args.name, args.output)
            print(f"Created {args.output} ({args.profile}). GitHub security configuration remains required.")
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except __import__("subprocess").CalledProcessError as exc:
        print(f"command failed with exit status {exc.returncode}", file=sys.stderr)
        return exc.returncode or 1


if __name__ == "__main__":
    raise SystemExit(main())

