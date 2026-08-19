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
    AgentHandoffRequired,
    ExecutionConfigError,
    add_execution_args,
    execution_config_from_namespace,
    resolve_cloud_endpoint_and_key,
    resolve_execution_mode,
)

from ai_job_seeker.backend import apply_backend_overrides, load_backend_defaults, load_profile_defaults
from ai_job_seeker.ingest import (
    IngestConfig,
    IngestSource,
    JobListing,
    ListingSource,
    load_search_config,
    run_ingest,
    run_ingest_dry,
)
from ai_job_seeker.ingest.config import SearchConfigError
from ai_job_seeker.match import rank_listings
from ai_job_seeker.profile.loader import ProfileError, load_profile

DEFAULT_PROFILE = "implementation/job_seeker/config/profile/kiera.yaml"
DEFAULT_SEARCH_CFG = "implementation/job_seeker/config/search.yaml"
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

    cv_defaults = load_profile_defaults()
    docx = cv_defaults.with_existing_docx()
    pdf = cv_defaults.with_existing_pdf()
    print()
    print(f"CV dir    : {cv_defaults.cv_dir}")
    print(f"CV docx   : {docx if docx else f'(not found — expected {cv_defaults.cv_docx})'}")
    print(f"CV pdf    : {pdf if pdf else f'(not found — expected {cv_defaults.cv_pdf})'}")
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


def _load_listings_from_json(path: str) -> list[JobListing]:
    """Load JobListing records from a JSON file written by `ingest --json`.

    Tolerant of extra keys; coerces source strings back to ListingSource
    enums. Never raises on bad rows — skips them with a stderr warning.
    """
    p = Path(path)
    if not p.is_file():
        print(f"error: ingest JSON not found: {p}", file=sys.stderr)
        raise SystemExit(1)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"error: could not read ingest JSON ({p}): {e}", file=sys.stderr)
        raise SystemExit(1)

    from ai_job_seeker.ingest.schema import _parse_date

    if not isinstance(data, list):
        print(f"error: ingest JSON must be a list of listing dicts ({p})", file=sys.stderr)
        raise SystemExit(1)

    out: list[JobListing] = []
    for i, row in enumerate(data):
        if not isinstance(row, dict):
            print(f"warning: skipping row {i} (not a dict)", file=sys.stderr)
            continue
        try:
            src_val = str(row.get("source", "")).strip()
            source = ListingSource(src_val) if src_val else ListingSource.ADZUNA
        except ValueError:
            print(f"warning: skipping row {i} (unknown source {src_val!r})", file=sys.stderr)
            continue
        try:
            out.append(
                JobListing(
                    source=source,
                    source_id=str(row.get("source_id", f"json-{i}")),
                    title=str(row.get("title", "")),
                    company=str(row.get("company", "")),
                    location=str(row.get("location", "")),
                    description=str(row.get("description", "")),
                    url=str(row.get("url", "")),
                    posted_at=_parse_date(row.get("posted_at")),
                    salary_min=row.get("salary_min"),
                    salary_max=row.get("salary_max"),
                    remote=row.get("remote"),
                    contract_type=row.get("contract_type"),
                )
            )
        except Exception as e:
            print(f"warning: skipping row {i}: {e}", file=sys.stderr)
    return out


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
    try:
        profile = load_profile(args.candidate)
    except ProfileError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    try:
        search_cfg = load_search_config(args.search_config)
    except SearchConfigError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    cfg, mode = _build_mode(args)
    print(f"Backend mode: {mode.value}")

    ingest_json = (args.ingest_json or "").strip()
    if ingest_json:
        listings = _load_listings_from_json(ingest_json)
        print(f"Listings (from --ingest-json): {len(listings)}")
    else:
        listings = run_ingest_dry(search_cfg)
        print(f"Listings (ingest dry-run): {len(listings)}")

    try:
        scored = rank_listings(
            profile,
            listings,
            cfg=cfg if mode.value != "agent" else None,
            mode=mode if mode.value != "agent" else None,
            top_n=args.top,
            max_age_days=search_cfg.max_age_days,
        )
    except AgentHandoffRequired:
        return 2

    if mode.value == "agent":
        print("Note: phase-2 LLM judge skipped — AGENT mode. Phase-1 scores only.")

    print()
    hdr = f"{'#':>3}  {'Final':>5}  {'P1':>5}  {'P2':>5}  {'Src':<7}  Title"
    print(hdr)
    print("-" * len(hdr))
    for s in scored:
        p2 = f"{s.phase2_score:5.1f}" if s.phase2_score is not None else "   -"
        title = s.listing.title[:50]
        print(
            f"{s.ranked_position:3d}  {s.final_score:5.1f}  "
            f"{s.phase1_score:5.1f}  {p2}  {s.listing.source.value:<7}  {title}"
        )

    print()
    print(f"Shortlisted: {len(scored)} (--top {args.top})")
    if scored:
        fabricated_total = sum(len(s.fabricated_claim_flags) for s in scored)
        if fabricated_total:
            print(f"Fabricated-claim flags: {fabricated_total}")

    json_path = (args.json or "").strip()
    if json_path:
        out_dir = Path(json_path).parent
        if out_dir and not out_dir.exists():
            out_dir.mkdir(parents=True, exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump([s.to_dict() for s in scored], f, indent=2, ensure_ascii=False)
        print(f"Wrote ranked JSON: {json_path}")

    return 0


def _cmd_draft(args: argparse.Namespace) -> int:
    cfg, mode = _build_mode(args)
    print(f"Selected backend mode: {mode.value}")
    if mode.value == "cloud":
        base_url, _ = resolve_cloud_endpoint_and_key(cfg.cloud)
        print(f"Resolved cloud base_url: {base_url}")

    cv_defaults = load_profile_defaults()
    docx = cv_defaults.with_existing_docx()
    print(f"CV dir (default)    : {cv_defaults.cv_dir}")
    if docx:
        print(f"CV source .docx     : {docx}")
    else:
        print(f"CV source .docx     : (not found in {cv_defaults.cv_dir} — no source CV for drafting)")
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
        help="Stage 3 — score ingested listings against the profile and rank",
    )
    p_match.add_argument("--candidate", default=DEFAULT_PROFILE, help="Path to profile YAML")
    p_match.add_argument(
        "--search-config",
        default=DEFAULT_SEARCH_CFG,
        help="Path to search.yaml (for dry-run defaults and max_age)",
    )
    p_match.add_argument(
        "--ingest-json",
        default="",
        help="Path to a listings JSON file written by `ingest --json` (bypasses dry-run)",
    )
    p_match.add_argument("--top", type=int, default=10, help="Cap ranked shortlist to N (default 10)")
    p_match.add_argument("--json", default="", help="Write ranked ScoredListing dicts to this JSON path")
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
