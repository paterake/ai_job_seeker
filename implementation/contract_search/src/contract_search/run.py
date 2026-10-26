"""Gather listings (shared ingest, one pass per query), score them, write the shortlist."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from ai_job_seeker.ingest import IngestConfig, dedupe_listings, run_ingest, run_ingest_dry
from ai_job_seeker.ingest.schema import JobListing

from contract_search.config import ConfigError, Profile, Scoring
from contract_search.score import Scored, score_listing


@dataclass
class RunResult:
    shortlist: list[Scored] = field(default_factory=list)
    fetched: int = 0
    drops: dict[str, int] = field(default_factory=dict)
    skips: list[tuple[str, str]] = field(default_factory=list)


def gather(cfg: IngestConfig, profile: Profile, policy: Scoring, *, dry_run: bool) -> tuple[list[JobListing], list[tuple[str, str]]]:
    """One ingest pass per query. Remote roles are not tied to a place, so each query
    also runs without a location unless the profile is on-site only."""
    if dry_run:
        res = run_ingest_dry(cfg)
        return list(res.listings), list(res.source_skips)
    places = [profile.locations[0]] if profile.locations else [""]
    if profile.remote not in policy.remote_modes_without_location_pass:
        places.append("")
    listings: list[JobListing] = []
    skips: list[tuple[str, str]] = []
    for query in profile.queries:
        for place in places:
            res = run_ingest(cfg, [query], place)
            listings.extend(res.listings)
            skips.extend(s for s in res.source_skips if s not in skips)
    return dedupe_listings(listings, cfg), skips


def run_search(
    cfg: IngestConfig,
    profile: Profile,
    policy: Scoring,
    *,
    dry_run: bool = False,
    top: int = 25,
    now: datetime | None = None,
) -> RunResult:
    if profile.remote not in policy.remote_modes:
        raise ConfigError(f"profile target.remote {profile.remote!r} is not one of {sorted(policy.remote_modes)}")
    listings, skips = gather(cfg, profile, policy, dry_run=dry_run)
    result = RunResult(fetched=len(listings), skips=skips)
    for listing in listings:
        out = score_listing(listing, profile, policy, max_age_days=cfg.max_age_days, now=now)
        if isinstance(out, str):
            reason = out.split(" '")[0]
            result.drops[reason] = result.drops.get(reason, 0) + 1
        else:
            result.shortlist.append(out)
    result.shortlist.sort(key=lambda s: (-s.score, s.listing.title.lower(), s.listing.company.lower()))
    result.shortlist = result.shortlist[:top]
    return result


def render_markdown(result: RunResult, profile: Profile, stamp: str) -> str:
    lines = [
        f"# Contract shortlist - {stamp}",
        "",
        f"Fetched {result.fetched} listings; kept {len(result.shortlist)}. "
        "Dropped: " + (", ".join(f"{k} ({v})" for k, v in sorted(result.drops.items())) or "none") + ".",
    ]
    if result.skips:
        lines.append("Skipped sources: " + ", ".join(f"{n}: {r}" for n, r in result.skips) + ".")
    lines += ["", "IR35 is read only from advert text; 'unstated' means the advert did not say.", ""]
    for i, s in enumerate(result.shortlist, 1):
        L = s.listing
        lines += [
            f"## {i}. {L.title} - {L.company} ({s.score})",
            f"- Location: {L.location or 'n/a'}{' (remote)' if s.remote else ''}",
            f"- IR35: {s.ir35}; day rate: {s.day_rate or 'not stated'}; source: {L.source.value}",
            f"- {L.url}",
            f"- Why: {'; '.join(s.evidence)}",
            "",
        ]
    return "\n".join(lines)


def write_outputs(result: RunResult, profile: Profile, out_dir: Path, now: datetime | None = None) -> tuple[Path, Path]:
    now = now or datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%d_%H%M")
    archive = out_dir / "_archive"
    archive.mkdir(parents=True, exist_ok=True)
    md = render_markdown(result, profile, stamp)
    js = json.dumps(
        [{"score": s.score, "ir35": s.ir35, "day_rate": s.day_rate, "remote": s.remote,
          "evidence": s.evidence, **s.listing.to_dict()} for s in result.shortlist],
        indent=2,
    )
    for suffix, body in ((".md", md), (".json", js)):
        (archive / f"shortlist_{stamp}{suffix}").write_text(body, encoding="utf-8")
        (out_dir / f"latest_shortlist{suffix}").write_text(body, encoding="utf-8")
    return out_dir / "latest_shortlist.md", out_dir / "latest_shortlist.json"
