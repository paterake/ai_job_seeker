"""Stage 2 — Ingest: pull job postings from configured sources, normalise,
dedupe, and apply generic filters.

Public surface re-exports everything the CLI or downstream match stage needs.
"""

from ai_job_seeker.ingest.config import IngestConfig, IngestSource, load_search_config
from ai_job_seeker.ingest.pipeline import (
    apply_filters,
    dedupe_listings,
    run_ingest,
    run_ingest_dry,
)
from ai_job_seeker.ingest.schema import JobListing, ListingSource

__all__ = [
    "IngestConfig",
    "IngestSource",
    "JobListing",
    "ListingSource",
    "apply_filters",
    "dedupe_listings",
    "load_search_config",
    "run_ingest",
    "run_ingest_dry",
]
