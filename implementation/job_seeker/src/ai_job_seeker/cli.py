"""Thin CLI entry point. Each subcommand is a thin wrapper over an importable
phase module. Stage 1 ships `profile` only; further phases add subcommands.

ai_agent_core.execution is only used by the match (phase-2 LLM judge) and
draft (LLM generation) stages. For the stages that don't need it (profile,
ingest), we deliberately defer that import to the point of use so the whole
tool keeps working even if the ai_agent_core sibling checkout is missing on
disk — the failure becomes a clear per-subcommand message instead of a
venv-resolution failure at `uv run` time.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, TYPE_CHECKING

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
from ai_job_seeker.profile.extractor import extract_profile_from_docx
from ai_job_seeker.profile.loader import ProfileError, load_profile, save_profile

if TYPE_CHECKING:
    from ai_agent_core.execution import (  # noqa: F401 — used at runtime, re-imported lazily below
        AgentHandoffRequired,
        ExecutionConfig,
        ExecutionConfigError,
        ArgDefaults,
    )

_DEFAULT_PROFILE_REL = "implementation/job_seeker/config/profile/kiera.yaml"
_DEFAULT_SEARCH_CFG_REL = "implementation/job_seeker/config/search.yaml"


def _resolve_workspace_relative(rel_path: str) -> str:
    """Resolve a workspace-relative config path (works from any cwd)."""
    here = Path(__file__).resolve()
    raw_candidates: list[Path] = []
    for parent in [here, *here.parents][:7]:
        if (parent / "pyproject.toml").is_file():
            raw_candidates.append(parent)
    cwd = Path.cwd().resolve()
    for parent in [cwd, *cwd.parents][:7]:
        if (parent / "pyproject.toml").is_file() and parent not in raw_candidates:
            raw_candidates.append(parent)

    def _is_workspace_root(p: Path) -> bool:
        if (p / "ai_context").is_dir():
            return True
        target = (p / rel_path).resolve()
        if target.is_file():
            return True
        # For gitignored paths like the profile YAML (tests create it),
        # accept a workspace-like root if the *directory* exists under the
        # candidate. That disambiguates workspace vs facet subproject roots
        # even when the final file hasn't been materialised yet.
        rel_parent = Path(rel_path).parent
        if rel_parent != Path(".") and (p / rel_parent).is_dir():
            return True
        return False

    candidates = [p for p in raw_candidates if _is_workspace_root(p)]
    if not candidates:
        candidates = list(raw_candidates)
    for root in candidates:
        target = (root / rel_path).resolve()
        if target.is_file():
            return str(target)
    # For intentionally-gitignored paths (like the profile YAML) we still
    # want a stable absolute default — workspace-root-relative.
    return str((Path(candidates[0]) / rel_path).resolve()) if candidates else rel_path


DEFAULT_PROFILE = _resolve_workspace_relative(_DEFAULT_PROFILE_REL)
DEFAULT_SEARCH_CFG = _resolve_workspace_relative(_DEFAULT_SEARCH_CFG_REL)
def _resolve_workspace_relative_dir(rel_dir: str) -> str:
    """Resolve a workspace-relative dir default (works from any cwd)."""
    sentinel = _resolve_workspace_relative(f"{rel_dir}/.gitkeep")
    return str(Path(sentinel).parent)
DEFAULT_OUTPUT_DIR = _resolve_workspace_relative_dir("implementation/job_seeker/config/output")
DOTENV_PATH = ".env"

_AI_AGENT_CORE_IMPORT_ERR_HINT = (
    "ai_agent_core could not be imported. It is declared as a sibling path "
    "dependency in the workspace pyproject.toml — clone/checkout "
    "ai_agent_core next to ai_job_seeker at "
    "../ai_agent_core/ (relative to the workspace root), or install it as a "
    "released package. It is only required for the match (phase-2 LLM judge) "
    "and draft (LLM generation) stages; profile + ingest work without it."
)


def _require_ai_agent_core(what: str) -> Any:
    """Import and return the ai_agent_core.execution module.

    Called only from the commands that actually need it (_build_mode →
    match/draft). If unavailable, prints a remediation hint and exits 2 —
    never raises ImportError silently, never blames a missing transitive.
    """
    try:
        import ai_agent_core.execution as mod  # noqa: WPS433 — lazy by design
    except ImportError as e:
        print(f"error: cannot run {what}: {_AI_AGENT_CORE_IMPORT_ERR_HINT}", file=sys.stderr)
        print(f"       import trace: {e}", file=sys.stderr)
        raise SystemExit(2)
    return mod


def _add_execution_args(parser: argparse.ArgumentParser, *, defaults: Any) -> None:
    """Mirror the shared-lib add_execution_args call; import lazily.

    Used only for match/draft parsers; profile/ingest never hit this path so
    they stay 100% PyPI-dep-only.
    """
    mod = _require_ai_agent_core(parser.prog)
    mod.add_execution_args(parser, defaults=defaults)


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
    cv_defaults = load_profile_defaults()
    docx = cv_defaults.with_existing_docx() if hasattr(cv_defaults, "with_existing_docx") else None
    if args.extract:
        src = (args.cv_docx or "").strip() or (str(docx) if docx else "")
        if not src or not Path(src).is_file():
            print(
                f"error: --extract requires a CV .docx path (via --cv-docx or backend.yaml profile.cv_dir+cv_docx_stem). "
                f"Got: {src!r}",
                file=sys.stderr,
            )
            return 1
        try:
            result = extract_profile_from_docx(src)
        except ProfileError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1

        out_path = (args.output or "").strip() or args.candidate
        try:
            written = save_profile(result.profile, out_path, overwrite=args.force)
        except ProfileError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        ident = result.profile["identity"]
        target = result.profile.get("target", {})
        print(f"Extracted CV      : {src}")
        print(f"Wrote profile to  : {written}")
        print(f"Candidate         : {ident.get('name', '?')}")
        print(f"Skills (hard/soft): {len(result.profile['skills'].get('hard', []))}/{len(result.profile['skills'].get('soft', []))}")
        print(f"Experience roles  : {len(result.profile.get('experience', []))}")
        print(f"Education entries : {len(result.profile.get('education', []))}")
        print(f"Achievements      : {len(result.profile.get('achievements_and_awards', []))}")
        if target.get("roles"):
            print(f"Target roles (hint): {', '.join(target['roles'])}")
        if result.required_review:
            print()
            print("Required review (populate in the YAML, then re-run `ai-job-seeker profile`):")
            for field in result.required_review:
                print(f"  - {field}")
        return 0

    try:
        profile = load_profile(args.candidate)
    except ProfileError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    ident = profile["identity"]
    target = profile.get("target", {})
    print(f"Candidate : {ident.get('name', '?')}")
    print(f"Roles     : {', '.join(target.get('roles', [])) or '-'}")
    print(f"Locations : {', '.join(target.get('locations', [])) or '-'}")
    print(f"Remote    : {target.get('remote', '-')}")
    print(f"Min salary: {target.get('salary_min_gbp', '-')}")
    print(f"Skills    : {sum(len(v) for v in profile.get('skills', {}).values()) if isinstance(profile.get('skills'), dict) else len(profile.get('skills', []))} listed")
    print(f"Experience: {len(profile.get('experience', []))} roles")

    cv_defaults = load_profile_defaults()
    docx = cv_defaults.with_existing_docx() if hasattr(cv_defaults, "with_existing_docx") else None
    pdf = cv_defaults.with_existing_pdf() if hasattr(cv_defaults, "with_existing_pdf") else None
    print()
    print(f"CV dir    : {cv_defaults.cv_dir}")
    print(f"CV docx   : {docx if docx else f'(not found — expected {cv_defaults.cv_docx})'}")
    print(f"CV pdf    : {pdf if pdf else f'(not found — expected {cv_defaults.cv_pdf})'}")
    return 0


def _build_mode(args: argparse.Namespace) -> tuple:
    mod = _require_ai_agent_core("match/draft backend-mode resolution")
    cfg = mod.execution_config_from_namespace(args)
    apply_backend_overrides(cfg)
    try:
        mode = mod.resolve_execution_mode(cfg)
    except mod.ExecutionConfigError as e:
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
        result = run_ingest_dry(cfg)
        listings = result.listings
        skips: list[tuple[str, str]] = []
        print(f"[dry-run] Enabled sources: {', '.join(enabled) if enabled else '(none)'}")
    else:
        if not enabled:
            print("error: no sources enabled in search.yaml", file=sys.stderr)
            return 1
        terms = [t.strip() for t in (args.search or "").split(",") if t.strip()]
        location = (args.location or "").strip()
        try:
            result = run_ingest(cfg, search_terms=terms, location=location)
            listings = result.listings
            skips = list(result.source_skips)
        except Exception as e:
            print(f"error: ingest failed: {e}", file=sys.stderr)
            return 1

    by_src: dict[str, int] = dict(result.source_counts) if hasattr(result, "source_counts") else {}
    if not by_src:
        for lst in listings:
            by_src[lst.source.value] = by_src.get(lst.source.value, 0) + 1

    print(f"Listings fetched : {len(listings)}")
    for src in sorted(by_src):
        print(f"  {src:<8}      : {by_src[src]}")
    for src_name, reason in skips:
        print(f"  {src_name:<8}      : SKIP — {reason}")
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


def _write_shortlist_markdown(
    scored: list[Any],
    out_path: str | Path,
    *,
    candidate_name: str,
    search_terms: str = "",
    location: str = "",
) -> Path:
    """Write a ranked shortlist as Markdown — clickable links, for review.

    Output shape intentionally simple so Kiera can open it in any editor /
    Markdown preview and click links directly.
    """
    from datetime import datetime

    p = Path(out_path)
    if str(p.parent).strip():
        p.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append(f"# Job Shortlist — {candidate_name}")
    lines.append("")
    meta_bits = [f"Generated: {datetime.now().isoformat(timespec='seconds')}"]
    if search_terms:
        meta_bits.append(f"Search: `{search_terms}`")
    if location:
        meta_bits.append(f"Location: `{location}`")
    lines.append(" · ".join(meta_bits))
    lines.append("")
    lines.append(f"**{len(scored)}** shortlisted roles (sorted by final score, descending).")
    lines.append("")

    # Table
    hdr = "| # | Score | Source | Role | Company | Location | Salary | Posted |"
    sep = "|---|---:|---|---|---|---|---|---|"
    lines.append(hdr)
    lines.append(sep)
    for s in scored:
        lst = s.listing
        url = lst.url or ""
        role = (lst.title[:80] + "…") if len(lst.title) > 80 else lst.title
        if url:
            role_md = f"[{role}]({url})"
        else:
            role_md = role
        salary = ""
        if lst.salary_min and lst.salary_max:
            salary = f"£{lst.salary_min:,}–£{lst.salary_max:,}"
        elif lst.salary_min:
            salary = f"£{lst.salary_min:,}+"
        elif lst.salary_max:
            salary = f"≤£{lst.salary_max:,}"
        posted = lst.posted_at.strftime("%Y-%m-%d") if lst.posted_at else ""
        remote_bit = f" ({lst.remote})" if lst.remote else ""
        location_txt = f"{lst.location}{remote_bit}" if lst.location else remote_bit.strip()
        lines.append(
            f"| {s.ranked_position} "
            f"| {s.final_score:.1f} "
            f"| {lst.source.value} "
            f"| {role_md} "
            f"| {lst.company or ''} "
            f"| {location_txt} "
            f"| {salary} "
            f"| {posted} |"
        )
    lines.append("")
    lines.append("## Score breakdown per role")
    lines.append("")
    for s in scored:
        lst = s.listing
        lines.append(f"### {s.ranked_position}. {lst.title} — {lst.company or ''}")
        lines.append("")
        lines.append(f"- **Final score:** {s.final_score:.1f}  ")
        lines.append(f"  · Phase-1 (deterministic): {s.phase1_score:.1f}")
        if s.phase2_score is not None:
            lines.append(f"  · Phase-2 (LLM judge): {s.phase2_score:.1f}")
            if s.phase2_rationale:
                lines.append(f"  · Phase-2 rationale: {s.phase2_rationale}")
        else:
            lines.append(f"  · Phase-2 (LLM judge): skipped (agent mode — default for 8GB M3 Air)")
        lines.append(f"- **Source:** {lst.source.value} — `{lst.source_id}`")
        if lst.url:
            lines.append(f"- **Apply link:** {lst.url}")
        evidence = getattr(s, "phase1_evidence", None)
        if evidence:
            lines.append("- **Phase-1 evidence:**")
            if isinstance(evidence, dict):
                for k, v in evidence.items():
                    if isinstance(v, float):
                        lines.append(f"  - {k}: {v:.1f}")
                    else:
                        lines.append(f"  - {k}: {v}")
            elif isinstance(evidence, list):
                for item in evidence:
                    lines.append(f"  - {item}")
            else:
                lines.append(f"  - {evidence}")
        flags = getattr(s, "fabricated_claim_flags", None) or []
        if flags:
            lines.append(f"- **Fabricated-claim flags:** {flags}")
        lines.append("")

    p.write_text("\n".join(lines), encoding="utf-8")
    return p


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
    except _require_ai_agent_core("match phase-2 AgentHandoffRequired handling").AgentHandoffRequired:
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

    md_path = (args.md or "").strip()
    if md_path:
        name = (profile.get("identity") or {}).get("name") or "Candidate"
        # If --ingest-json came from ingest --search X --location Y we won't
        # have those strings here; leave them blank and the md just omits them.
        _write_shortlist_markdown(
            scored,
            md_path,
            candidate_name=name,
            search_terms=(args.search or "") if hasattr(args, "search") else "",
            location=(args.location or "") if hasattr(args, "location") else "",
        )
        print(f"Wrote shortlist MD : {md_path}")

    return 0


def _cmd_draft(args: argparse.Namespace) -> int:
    mod = _require_ai_agent_core("draft LLM backend resolution")
    cfg, mode = _build_mode(args)
    print(f"Selected backend mode: {mode.value}")
    if mode.value == "cloud":
        base_url, _ = mod.resolve_cloud_endpoint_and_key(cfg.cloud)
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


def _needs_execution_args(argv0: str | None) -> bool:
    """True iff the chosen subcommand is match or draft (they carry LLM flags).

    Used to defer the ai_agent_core import at parse-time, not just at
    command-time — otherwise running *any* `ai-job-seeker profile/ingest`
    command would still build the match/draft subparsers unconditionally and
    try to import ai_agent_core via _add_execution_args.
    """
    return argv0 in {"match", "draft"}


def _build_base_parser(
    argv0: str | None,
) -> tuple[argparse.ArgumentParser, argparse._SubParsersAction]:  # type: ignore[name-defined]
    """Build the common parser + profile + ingest subparsers unconditionally.

    The match/draft subparsers (which carry LLM-mode flags via
    _add_execution_args and therefore require ai_agent_core on the import
    path) are added separately by main() only when argv0 says so.
    """
    parser = argparse.ArgumentParser(prog="ai-job-seeker", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_profile = sub.add_parser("profile", help="Load and summarise a candidate profile")
    p_profile.add_argument("--candidate", default=DEFAULT_PROFILE, help="Path to profile YAML")
    p_profile.add_argument(
        "--extract",
        action="store_true",
        help="Generate a profile YAML by extracting facts from a CV .docx (source-of-truth path via backend.yaml profile defaults, or --cv-docx).",
    )
    p_profile.add_argument(
        "--cv-docx",
        default="",
        help="Override the .docx path used by --extract (default: backend.yaml profile.cv_dir + cv_docx_stem)",
    )
    p_profile.add_argument(
        "--output",
        default="",
        help="Override the output profile YAML path used by --extract (default: --candidate path)",
    )
    p_profile.add_argument(
        "--force",
        action="store_true",
        help="Allow --extract to overwrite an existing profile YAML (default: refuse, to preserve hand-edits).",
    )
    p_profile.set_defaults(func=_cmd_profile)

    p_ingest = sub.add_parser(
        "ingest",
        help="Stage 2 — pull job postings from configured sources and normalise",
    )
    p_ingest.add_argument(
        "--search-config",
        default=DEFAULT_SEARCH_CFG,
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

    # Even for match/draft we add a stub parser *without* the LLM flags first,
    # so --help and unknown-arg errors stay clean when ai_agent_core is
    # missing. The real flags (--ollama-model etc.) are layered on top below
    # only when argv0 actually matches.
    if argv0 == "match":
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
        p_match.add_argument("--md", default="", help="Write a reviewable Markdown shortlist (clickable links) to this path")
        p_match.add_argument("--search", default="", help="Informational only — written into Markdown shortlist header")
        p_match.add_argument("--location", default="", help="Informational only — written into Markdown shortlist header")
        p_match.set_defaults(func=_cmd_match)
    elif argv0 == "draft":
        p_draft = sub.add_parser(
            "draft",
            help="Stage 4 — draft tailored cover letter + CV per shortlist (placeholder)",
        )
        p_draft.set_defaults(func=_cmd_draft)

    return parser, sub


def main(argv: list[str] | None = None) -> int:
    _load_dotenv()

    real_argv = list(sys.argv[1:] if argv is None else argv)
    argv0 = next((a for a in real_argv if a and not a.startswith("-")), None)

    parser, sub = _build_base_parser(argv0)

    if _needs_execution_args(argv0):
        # ai_agent_core is required only now (match or draft command). The
        # import is nested here to keep profile/ingest 100% PyPI-dep-only — if
        # ai_agent_core is missing, execution fails with the remediation hint
        # from _require_ai_agent_core rather than an ImportError at import.
        try:
            backend_defaults = load_backend_defaults()
        except ImportError as e:
            print(f"error: cannot build {argv0} parser: {e}", file=sys.stderr)
            return 2
        # Layer the LLM-mode flags onto the already-registered match/draft
        # subparser via the shared add_execution_args helper.
        chosen: argparse.ArgumentParser | None = None
        for act in sub._choices_actions:  # type: ignore[attr-defined]
            if act.dest == argv0:
                chosen = sub.choices[act.dest]
                break
        if chosen is None:  # pragma: no cover — _needs_execution_args gated argv0
            print(f"error: subparser for {argv0!r} not registered", file=sys.stderr)
            return 2
        _add_execution_args(chosen, defaults=backend_defaults)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
