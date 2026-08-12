"""Ingest pipeline: fan out to enabled sources, dedupe, apply filters.

Exposes:
- run_ingest(cfg, profile_target) -> list[JobListing]  — live API calls
- run_ingest_dry(...) -> list[JobListing]              — synthetic samples, no API
- dedupe_listings(listings, cfg) -> list[JobListing]
- apply_filters(listings, cfg) -> list[JobListing]

Trifecta isolation: this module is the boundary between "untrusted posting
text" (data) and the rest of the pipeline. It never interprets posting
content as instructions; it just carries and filters it.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from ai_job_seeker.ingest.config import IngestConfig
from ai_job_seeker.ingest.schema import JobListing, ListingSource


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
) -> list[JobListing]:
    """Fan-out to all enabled sources, then dedupe + filter.

    Raises any client errors for sources whose credentials are missing;
    callers handle the UX (e.g. skip on --dry or surface clearly).
    """
    listings: list[JobListing] = []
    for source in cfg.enabled_sources():
        try:
            listings.extend(_fetch_by_source(source, search_terms, location))
        except Exception:
            raise
    listings = dedupe_listings(listings, cfg)
    listings = apply_filters(listings, cfg, now=now)
    return listings


def run_ingest_dry(
    cfg: IngestConfig,
    *,
    now: datetime | None = None,
) -> list[JobListing]:
    """Return synthetic listings so CLI + match/draft dev works without API keys.

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
    samples = dedupe_listings(samples, cfg)
    samples = apply_filters(samples, cfg, now=now)
    return samples


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
