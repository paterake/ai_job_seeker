"""Smoke tests for Stage 2 (Ingest): schema, config load, dedupe, filters,
client normalisers, and CLI dry-run.

All tests are offline — no real API calls. Client normalisers are exercised
against hand-written sample payloads that mirror the real API shapes.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from ai_job_seeker.ingest import (
    apply_filters,
    dedupe_listings,
    load_search_config,
    run_ingest_dry,
)
from ai_job_seeker.ingest.config import IngestConfig, SearchConfigError
from ai_job_seeker.ingest.schema import JobListing, ListingSource


DEFAULT_SEARCH = (
    Path(__file__).resolve().parents[1] / "config" / "search.yaml"
)


@pytest.fixture
def cfg() -> IngestConfig:
    return load_search_config(DEFAULT_SEARCH)


def test_search_config_loads_and_has_all_three_sources(cfg):
    for name in ("adzuna", "reed", "themuse"):
        assert name in cfg.sources
        assert cfg.sources[name].enabled is True
        assert cfg.sources[name].base_url.startswith("https://")


def test_search_config_filters_defaults(cfg):
    assert cfg.max_age_days == 21
    assert cfg.dedupe_on == ["title", "company"]


def test_search_config_bad_path(tmp_path):
    with pytest.raises(SearchConfigError):
        load_search_config(tmp_path / "no.yaml")


def _listing(src=ListingSource.ADZUNA, sid="1", title="Data Engineer", company="Acme", days_ago=2):
    return JobListing(
        source=src,
        source_id=sid,
        title=title,
        company=company,
        location="London",
        description="desc",
        url="https://example.com/1",
        posted_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
        salary_min=50000,
        salary_max=70000,
        remote=True,
        contract_type="permanent",
    )


def test_dedupe_across_sources_stable(cfg):
    l1 = _listing(ListingSource.ADZUNA, "a1", "Data Engineer", "Acme Co")
    l2 = _listing(ListingSource.REED, "r1", "  DATA engineer  ", "  ACME CO  ")
    l3 = _listing(ListingSource.THEMUSE, "m1", "Different Title", "Acme Co")
    out = dedupe_listings([l1, l2, l3], cfg)
    assert len(out) == 2
    assert out[0].source_id == "a1"
    assert out[1].source_id == "m1"


def test_age_filter_drops_stale_listings(cfg):
    fresh = _listing(days_ago=1)
    stale = _listing(days_ago=cfg.max_age_days + 5, sid="old")
    unknown_age = JobListing(
        source=ListingSource.ADZUNA,
        source_id="u",
        title="T",
        company="C",
        location="L",
        description="d",
        url="u",
        posted_at=None,
    )
    out = apply_filters([fresh, stale, unknown_age], cfg)
    ids = [l.source_id for l in out]
    assert "1" in ids
    assert "old" not in ids
    assert "u" in ids


def test_empty_title_or_company_dropped(cfg):
    bad_title = _listing(title="   ")
    bad_company = _listing(company="")
    good = _listing()
    out = apply_filters([bad_title, bad_company, good], cfg)
    assert len(out) == 1
    assert out[0].source_id == "1"


def test_dry_run_returns_samples(cfg):
    listings = run_ingest_dry(cfg)
    assert len(listings) >= 1
    sources_seen = {l.source for l in listings}
    for s in cfg.enabled_sources():
        assert ListingSource(s.name) in sources_seen
    for l in listings:
        assert l.title and l.company and l.url
        d = l.to_dict()
        assert d["source"] == l.source.value
        assert isinstance(d["posted_at"], str)
        assert "raw" not in d


def test_joblisting_dedupe_key_normalises():
    a = _listing(title="  DATA  ENGINEER  ", company="ACME")
    b = _listing(title="data engineer", company="acme", sid="2")
    assert a.dedupe_key == b.dedupe_key


def test_adzuna_normaliser_sample_payload():
    from ai_job_seeker.ingest.adzuna import _normalise
    raw = {
        "id": "adz123",
        "title": "Senior Python Engineer",
        "company": {"display_name": "TechCo"},
        "location": {"display_name": "Manchester"},
        "description": "Build APIs in Python.",
        "redirect_url": "https://adzuna/go/123",
        "created": "2026-08-10T12:00:00Z",
        "salary_min": 55000,
        "salary_max": 75000,
        "contract_type": "permanent",
    }
    l = _normalise(raw)
    assert l.source == ListingSource.ADZUNA
    assert l.source_id == "adz123"
    assert l.title == "Senior Python Engineer"
    assert l.company == "TechCo"
    assert l.location == "Manchester"
    assert l.url == "https://adzuna/go/123"
    assert l.salary_min == 55000
    assert l.salary_max == 75000
    assert l.contract_type == "permanent"
    assert l.posted_at is not None


def test_reed_normaliser_sample_payload():
    from ai_job_seeker.ingest.reed import _normalise
    raw = {
        "jobId": 456,
        "jobTitle": "Backend Engineer",
        "employerName": "BigCo",
        "locationName": "Edinburgh",
        "jobDescription": "Python backend systems.",
        "jobUrl": "https://reed/jobs/456",
        "date": "2026-08-09",
        "minimumSalary": "60000",
        "maximumSalary": 80000,
        "contractType": "Full Time",
        "workFromHomeOnly": "true",
    }
    l = _normalise(raw)
    assert l.source == ListingSource.REED
    assert l.source_id == "456"
    assert l.title == "Backend Engineer"
    assert l.company == "BigCo"
    assert l.remote is True
    assert l.salary_min == 60000
    assert l.salary_max == 80000


def test_themuse_normaliser_sample_payload():
    from ai_job_seeker.ingest.themuse import _normalise
    raw = {
        "id": 789,
        "name": "Data Engineer (Remote)",
        "company": {"name": "StartupX"},
        "locations": [{"name": "New York, NY"}, {"name": "Remote"}],
        "contents": "Build data pipelines.",
        "refs": {"landings_page": "https://muse/j/789"},
        "publication_date": "2026-08-08",
        "categories": [{"name": "Data"}],
        "levels": [{"name": "Senior"}],
    }
    l = _normalise(raw)
    assert l.source == ListingSource.THEMUSE
    assert l.source_id == "789"
    assert l.remote is True
    assert "New York" in l.location and "Remote" in l.location


def test_cli_ingest_dry_run():
    from ai_job_seeker.cli import main
    import io
    import sys
    old = sys.stdout, sys.stderr
    buf = io.StringIO()
    try:
        sys.stdout = buf
        rc = main(["ingest", "--dry-run"])
    finally:
        sys.stdout, sys.stderr = old
    assert rc == 0
    out = buf.getvalue()
    assert "[dry-run]" in out
    assert "Listings fetched" in out
    assert "adzuna" in out or "reed" in out or "themuse" in out


def test_cli_ingest_dry_run_json_output(tmp_path):
    from ai_job_seeker.cli import main
    import io
    import json
    import sys
    out_file = tmp_path / "listings.json"
    old = sys.stdout, sys.stderr
    buf = io.StringIO()
    try:
        sys.stdout = buf
        rc = main(["ingest", "--dry-run", "--json", str(out_file)])
    finally:
        sys.stdout, sys.stderr = old
    assert rc == 0
    assert out_file.is_file()
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert isinstance(data, list) and len(data) >= 1
    assert all("title" in d and "company" in d and "source" in d for d in data)
