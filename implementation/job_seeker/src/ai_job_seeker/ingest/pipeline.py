"""Ingest pipeline: fan out to enabled sources, dedupe, apply filters.

Exposes:
- run_ingest(cfg, profile_target) -> IngestResult     — live API calls (per-source graceful skip when credentials are missing)
- run_ingest_dry(...) -> IngestResult                 — synthetic samples, no API
- dedupe_listings(listings, cfg) -> list[JobListing]
- apply_filters(listings, cfg) -> list[JobListing]

Trifecta isolation: this module is the boundary between "untrusted posting
text" (data) and the rest of the pipeline. It never interprets posting
content as instructions; it just carries and filters it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable

from ai_job_seeker.ingest.config import IngestConfig
from ai_job_seeker.ingest.schema import JobListing, ListingSource


class IngestSourceSkip(RuntimeError):
    """Raised by a fetch_* client when a source should be skipped gracefully.

    Carries (source_name, reason). The pipeline catches this and records the
    skip rather than failing the whole ingest run — used specifically for
    "required credentials not yet populated" kinds of skips where the rest
    of the pipeline still succeeds.

    Non-credential failures (HTTP non-200, parse failures, etc.) still raise
    their original client exceptions and fail hard, as they should.
    """

    def __init__(self, source_name: str, reason: str) -> None:
        super().__init__(f"{source_name}: {reason}")
        self.source_name = source_name
        self.reason = reason


@dataclass
class IngestResult:
    """Return value of run_ingest / run_ingest_dry.

    Listings + per-source reporting so the CLI (or match stage, or tests) can
    show what came from where and which sources were skipped, without
    leaking secrets or failing the whole pipeline because one source is
    misconfigured.
    """

    listings: list[JobListing] = field(default_factory=list)
    source_counts: dict[str, int] = field(default_factory=dict)
    source_skips: list[tuple[str, str]] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.listings)

    def __iter__(self):
        return iter(self.listings)

    def __getitem__(self, idx):
        return self.listings[idx]


def _fetch_by_source(
    source,
    search_terms: Iterable[str] = (),
    location: str = "",
) -> list[JobListing]:
    name = source.name
    if name == "adzuna":
        from ai_job_seeker.ingest.adzuna import fetch_adzuna
        return fetch_adzuna(source, search_terms, location)
    if name == "reed":
        from ai_job_seeker.ingest.reed import fetch_reed
        return fetch_reed(source, search_terms, location)
    if name == "themuse":
        from ai_job_seeker.ingest.themuse import fetch_themuse
        return fetch_themuse(source, search_terms, location)
    raise ValueError(f"Unknown ingest source: {name!r}")


def dedupe_listings(
    listings: list[JobListing],
    cfg: IngestConfig,
) -> list[JobListing]:
    """Cross-source dedupe using the configured key fields.

    First listing with a given key wins (stable order).
    """
    fields = tuple(f for f in cfg.dedupe_on if f in ("title", "company"))
    if not fields:
        fields = ("title", "company")
    seen: set[tuple[str, ...]] = set()
    result: list[JobListing] = []
    for listing in listings:
        key_parts: list[str] = []
        if "title" in fields:
            key_parts.append(_norm_str(listing.title))
        if "company" in fields:
            key_parts.append(_norm_str(listing.company))
        if not any(key_parts):
            result.append(listing)
            continue
        key = tuple(key_parts)
        if key in seen:
            continue
        seen.add(key)
        result.append(listing)
    return result


def apply_filters(
    listings: list[JobListing],
    cfg: IngestConfig,
    *,
    now: datetime | None = None,
) -> list[JobListing]:
    """Apply generic filters (age threshold; drop empty title/company)."""
    if now is None:
        now = datetime.now(timezone.utc)
    result: list[JobListing] = []
    for listing in listings:
        if not listing.title.strip() or not listing.company.strip():
            continue
        age = listing.age_days(now)
        if age is not None and age > cfg.max_age_days:
            continue
        result.append(listing)
    return result


def run_ingest(
    cfg: IngestConfig,
    search_terms: Iterable[str] = (),
    location: str = "",
    *,
    now: datetime | None = None,
) -> IngestResult:
    """Fan-out to all enabled sources, recording skips per source, then dedupe + filter.

    Skips (e.g. required credentials not populated) are caught and recorded
    in the returned IngestResult.source_skips; they never abort the run.
    Hard failures (HTTP errors, malformed responses, etc.) still raise as
    before.
    """
    listings: list[JobListing] = []
    source_counts: dict[str, int] = {}
    source_skips: list[tuple[str, str]] = []
    for source in cfg.enabled_sources():
        try:
            fetched = _fetch_by_source(source, search_terms, location)
        except IngestSourceSkip as skip:
            source_skips.append((skip.source_name, skip.reason))
            continue
        listings.extend(fetched)
        source_counts[source.name] = source_counts.get(source.name, 0) + len(fetched)
    deduped = dedupe_listings(listings, cfg)
    filtered = apply_filters(deduped, cfg, now=now)
    final_counts: dict[str, int] = {}
    for lst in filtered:
        k = lst.source.value
        final_counts[k] = final_counts.get(k, 0) + 1
    return IngestResult(
        listings=filtered,
        source_counts=final_counts,
        source_skips=source_skips,
    )


def run_ingest_dry(
    cfg: IngestConfig,
    *,
    now: datetime | None = None,
) -> IngestResult:
    """Return synthetic IngestResult so CLI + match/draft dev works without API keys.

    Dry-run listings cover every source marked enabled in search.yaml, so
    the dedupe + filter pipeline is exercised end-to-end. Trifecta note:
    these synthetic strings are never stored and never reach an LLM in the
    default flow — they exist purely for plumbing tests.
    """
    if now is None:
        now = datetime.now(timezone.utc)
    samples: list[JobListing] = []
    if cfg.sources.get("adzuna") and cfg.sources["adzuna"].enabled:
        samples.append(_sample(ListingSource.ADZUNA, now))
        samples.append(_sample(ListingSource.ADZUNA, now, idx=2, title="  SENIOR DATA ENGINEER  ", company="Acme Corp"))
    if cfg.sources.get("reed") and cfg.sources["reed"].enabled:
        samples.append(_sample(ListingSource.REED, now))
        samples.append(_sample(ListingSource.REED, now, idx=2, title="Data Engineer", company="  ACME CORP  "))
    if cfg.sources.get("themuse") and cfg.sources["themuse"].enabled:
        samples.append(_sample(ListingSource.THEMUSE, now))
        samples.append(_sample(ListingSource.THEMUSE, now, idx=2, title="Staff Data Engineer", company="OtherCo"))
    deduped = dedupe_listings(samples, cfg)
    filtered = apply_filters(deduped, cfg, now=now)
    final_counts: dict[str, int] = {}
    for lst in filtered:
        k = lst.source.value
        final_counts[k] = final_counts.get(k, 0) + 1
    return IngestResult(
        listings=filtered,
        source_counts=final_counts,
        source_skips=[],
    )


def _sample(src: ListingSource, now: datetime, *, idx: int = 1, title: str = "Data Engineer", company: str = "Acme Ltd") -> JobListing:
    from datetime import timedelta
    posted = now - timedelta(days=2)
    return JobListing(
        source=src,
        source_id=f"{src.value}-sample-{idx}",
        title=title,
        company=company,
        location="London, UK",
        description=f"Synthetic {src.value} sample posting #{idx}. Build data pipelines.",
        url=f"https://example.com/{src.value}/{idx}",
        posted_at=posted,
        salary_min=60000 if idx == 1 else None,
        salary_max=85000 if idx == 1 else None,
        remote=True if idx == 1 else None,
        contract_type="permanent",
    )


def _norm_str(s: str) -> str:
    return " ".join((s or "").strip().lower().split())
