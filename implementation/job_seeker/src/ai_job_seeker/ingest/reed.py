"""Reed.co.uk job-search API client.

API docs: https://www.reed.co.uk/developers/jobseeker
Auth: Basic auth with API key as username, empty password.
Canonical secret sources (first hit wins):
  1. ~/Documents/__cfg/apikey/reed/api_key
  2. env: REED_API_KEY (e.g. via gitignored .env)
"""

from __future__ import annotations

import base64
import os
import urllib.parse
from typing import Any, Iterable

import requests

from ai_job_seeker.ingest.pipeline import IngestSourceSkip
from ai_job_seeker.ingest.schema import JobListing, ListingSource, _parse_date
from ai_job_seeker.secrets import SecretNotFound, require_secret


class ReedClientError(RuntimeError):
    """Raised when Reed API call fails or returns non-200."""


def _get_creds() -> str:
    """Return Reed API key from canonical sources.

    Prefers the on-disk layout under ~/Documents/__cfg/apikey/reed/ so that
    secrets live outside the repo. Falls back to env var REED_API_KEY so
    .env-based setups keep working.

    Raises IngestSourceSkip (not ReedClientError) when the key is missing from
    both canonical sources — the pipeline skips Reed and continues with the
    other sources. Actual HTTP / parse failures still raise ReedClientError.
    """
    try:
        key = require_secret("reed", "api_key", "REED_API_KEY") or ""
    except SecretNotFound as e:
        raise IngestSourceSkip(
            "reed",
            f"api_key not set — {e}",
        ) from None
    if not key:
        raise IngestSourceSkip(
            "reed",
            "api_key empty — populate either "
            "~/Documents/__cfg/apikey/reed/api_key or REED_API_KEY",
        )
    return key


def _auth_header() -> str:
    token = base64.b64encode(f"{_get_creds()}:".encode("utf-8")).decode("ascii")
    return f"Basic {token}"


def _build_url(
    base_url: str,
    search_terms: Iterable[str] = (),
    location: str = "",
    results_to_take: int = 100,
) -> str:
    what = " ".join(t.strip() for t in search_terms if t and t.strip())
    params: dict[str, Any] = {"resultsToTake": int(results_to_take)}
    if what:
        params["keywords"] = what
    if location:
        params["locationName"] = location
    qs = urllib.parse.urlencode(params)
    return f"{base_url.rstrip('/')}?{qs}"


def _normalise(raw: dict[str, Any]) -> JobListing:
    source_id = str(raw.get("jobId") or "").strip() or str(hash(raw.get("jobUrl") or raw.get("jobTitle") or ""))
    salary_min = raw.get("minimumSalary")
    salary_max = raw.get("maximumSalary")
    try:
        smin = int(salary_min) if salary_min is not None else None
    except (TypeError, ValueError):
        smin = None
    try:
        smax = int(salary_max) if salary_max is not None else None
    except (TypeError, ValueError):
        smax = None
    remote_raw = str(raw.get("workFromHomeOnly") or "").strip().lower()
    remote = True if remote_raw in {"1", "true", "yes"} else (False if remote_raw else None)
    return JobListing(
        source=ListingSource.REED,
        source_id=source_id,
        title=str(raw.get("jobTitle") or "").strip(),
        company=str(raw.get("employerName") or "").strip(),
        location=str(raw.get("locationName") or "").strip(),
        description=str(raw.get("jobDescription") or "").strip(),
        url=str(raw.get("jobUrl") or "").strip(),
        posted_at=_parse_date(raw.get("date")),
        salary_min=smin,
        salary_max=smax,
        contract_type=_norm_contract(raw.get("contractType")),
        remote=remote,
        raw=raw,
    )


def _norm_contract(value: Any) -> str | None:
    if not value:
        return None
    v = str(value).strip().lower()
    if v in {"permanent", "contract", "full_time", "part_time", "temp"}:
        return v
    return None


def fetch_reed(
    source,
    search_terms: Iterable[str] = (),
    location: str = "",
    *,
    timeout_s: float = 30.0,
) -> list[JobListing]:
    """Fetch listings from Reed.

    `source` is an IngestSource from load_search_config(); `results_to_take`
    comes from its extras.
    """
    extras = source.extras or {}
    results_to_take = int(extras.get("results_to_take") or 100)
    base_url = source.base_url

    _get_creds()

    url = _build_url(base_url, search_terms, location, results_to_take)
    headers = {"Authorization": _auth_header()}
    resp = requests.get(url, headers=headers, timeout=timeout_s)
    if resp.status_code != 200:
        raise ReedClientError(
            f"Reed HTTP {resp.status_code}: {resp.text[:200]}"
        )
    data = resp.json() or {}
    results = data.get("results") or data.get("jobs") or []
    listings: list[JobListing] = []
    for raw in results:
        try:
            listings.append(_normalise(raw))
        except Exception:
            continue
    return listings
