"""Thin CLI entry point. Each subcommand is a thin wrapper over an importable
phase module. Stage 1 ships `profile` only; further phases add subcommands.
"""

from __future__ import annotations

import argparse
import sys

from ai_agent_core.execution import (
    ExecutionConfigError,
    add_execution_args,
    execution_config_from_namespace,
    resolve_cloud_endpoint_and_key,
    resolve_execution_mode,
)

from ai_job_seeker.backend import apply_backend_overrides, load_backend_defaults
from ai_job_seeker.profile.loader import ProfileError, load_profile

DEFAULT_PROFILE = "implementation/job_seeker/config/profile/kiera.yaml"


def _cmd_profile(args: argparse.Namespace) -> int:
    try:
        profile = load_profile(args.candidate)
    except ProfileError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    ident = profile["identity"]
    target = profile["target"]
    print(f"Candidate : {ident.get('name', '?')}")
    print(f"Roles     : {', '.join(target.get('roles', [])) or '-'}")
    print(f"Locations : {', '.join(target.get('locations', [])) or '-'}")
    print(f"Remote    : {target.get('remote', '-')}")
    print(f"Skills    : {len(profile.get('skills', []))} listed")
    print(f"Experience: {len(profile.get('experience', []))} roles")
    return 0


def _build_mode(args: argparse.Namespace) -> tuple:
    cfg = execution_config_from_namespace(args)
    apply_backend_overrides(cfg)
    try:
        mode = resolve_execution_mode(cfg)
    except ExecutionConfigError as e:
        print(f"error: {e}", file=sys.stderr)
        raise SystemExit(2)
    return cfg, mode


def _cmd_match(args: argparse.Namespace) -> int:
    _, mode = _build_mode(args)
    print(f"Selected backend mode: {mode.value}")
    print("Stage 3 (match scoring) not implemented yet.")
    return 0


def _cmd_draft(args: argparse.Namespace) -> int:
    cfg, mode = _build_mode(args)
    print(f"Selected backend mode: {mode.value}")
    if mode.value == "cloud":
        base_url, _ = resolve_cloud_endpoint_and_key(cfg.cloud)
        print(f"Resolved cloud base_url: {base_url}")
    print("Stage 4 (draft) not implemented yet.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ai-job-seeker", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_profile = sub.add_parser("profile", help="Load and summarise a candidate profile")
    p_profile.add_argument("--candidate", default=DEFAULT_PROFILE, help="Path to profile YAML")
    p_profile.set_defaults(func=_cmd_profile)

    backend_defaults = load_backend_defaults()

    p_match = sub.add_parser(
        "match",
        help="Stage 3 — score ingested listings against the profile (placeholder)",
    )
    add_execution_args(p_match, defaults=backend_defaults)
    p_match.set_defaults(func=_cmd_match)

    p_draft = sub.add_parser(
        "draft",
        help="Stage 4 — draft tailored cover letter + CV per shortlist (placeholder)",
    )
    add_execution_args(p_draft, defaults=backend_defaults)
    p_draft.set_defaults(func=_cmd_draft)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
