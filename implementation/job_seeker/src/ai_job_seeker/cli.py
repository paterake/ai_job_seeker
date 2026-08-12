"""Thin CLI entry point. Each subcommand is a thin wrapper over an importable
phase module. Stage 1 ships `profile` only; further phases add subcommands.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from ai_agent_core.execution import (
    ExecutionConfigError,
    add_execution_args,
    execution_config_from_namespace,
    resolve_cloud_endpoint_and_key,
    resolve_execution_mode,
)

from ai_job_seeker.backend import apply_backend_overrides, load_backend_defaults
from ai_job_seeker.ingest import (
    IngestConfig,
    IngestSource,
    JobListing,
    load_search_config,
    run_ingest,
    run_ingest_dry,
)
from ai_job_seeker.ingest.config import SearchConfigError
from ai_job_seeker.profile.loader import ProfileError, load_profile

DEFAULT_PROFILE = "implementation/job_seeker/config/profile/kiera.yaml"
DOTENV_PATH = ".env"


def _load_dotenv(path: str | Path = DOTENV_PATH) -> None:
    """Best-effort load of a .env file into os.environ (no extra dep needed)."""
    p = Path(path)
    if not p.is_file():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        os.environ.setdefault(k, v)


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


def _cmd_ingest(args: argparse.Namespace) -> int:
    try:
        cfg = load_search_config(args.search_config)
    except SearchConfigError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    enabled = [s.name for s in cfg.enabled_sources()]
    if args.dry_run:
        listings = run_ingest_dry(cfg)
        print(f"[dry-run] Enabled sources: {', '.join(enabled) if enabled else '(none)'}")
    else:
        if not enabled:
            print("error: no sources enabled in search.yaml", file=sys.stderr)
            return 1
        terms = [t.strip() for t in (args.search or "").split(",") if t.strip()]
        location = (args.location or "").strip()
        try:
            listings = run_ingest(cfg, search_terms=terms, location=location)
        except Exception as e:
            print(f"error: ingest failed: {e}", file=sys.stderr)
            return 1

    by_src: dict[str, int] = {}
    for lst in listings:
        by_src[lst.source.value] = by_src.get(lst.source.value, 0) + 1

    print(f"Listings fetched : {len(listings)}")
    for src in sorted(by_src):
        print(f"  {src:<8}      : {by_src[src]}")
    print(f"Filter (max_age) : {cfg.max_age_days} days")
    print(f"Dedupe key       : {', '.join(cfg.dedupe_on)}")

    if args.json:
        out_path = args.json.strip()
        out_dir = Path(out_path).parent
        if out_dir and not out_dir.exists():
            out_dir.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump([l.to_dict() for l in listings], f, indent=2, ensure_ascii=False)
        print(f"Wrote JSON       : {out_path}")

    return 0


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
    _load_dotenv()
    parser = argparse.ArgumentParser(prog="ai-job-seeker", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_profile = sub.add_parser("profile", help="Load and summarise a candidate profile")
    p_profile.add_argument("--candidate", default=DEFAULT_PROFILE, help="Path to profile YAML")
    p_profile.set_defaults(func=_cmd_profile)

    p_ingest = sub.add_parser(
        "ingest",
        help="Stage 2 — pull job postings from configured sources and normalise",
    )
    p_ingest.add_argument(
        "--search-config",
        default="implementation/job_seeker/config/search.yaml",
        help="Path to search.yaml (sources + filters)",
    )
    p_ingest.add_argument(
        "--dry-run",
        action="store_true",
        help="Use synthetic sample listings instead of calling APIs (no keys needed)",
    )
    p_ingest.add_argument(
        "--search",
        default="",
        help="Comma-separated search terms to pass to sources (e.g. 'data engineer,etl')",
    )
    p_ingest.add_argument(
        "--location",
        default="",
        help="Location filter passed to sources (e.g. 'London')",
    )
    p_ingest.add_argument(
        "--json",
        default="",
        help="Write normalised listings to this JSON file path",
    )
    p_ingest.set_defaults(func=_cmd_ingest)

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
