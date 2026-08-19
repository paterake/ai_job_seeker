"""Adzuna job-search API client.

API docs: https://developer.adzuna.com/overview
Auth: `app_id` + `app_key` as query-string params on every request.
Canonical secret sources (first hit wins):
  1. ~/Documents/__cfg/apikey/adzuna/app_id  +  app_key
  2. env: ADZUNA_APP_ID, ADZUNA_APP_KEY (e.g. via gitignored .env)
"""

from __future__ import annotations

import os
import urllib.parse
from typing import Any, Iterable

import requests

from ai_job_seeker.ingest.schema import JobListing, ListingSource, _parse_date
from ai_job_seeker.secrets import SecretNotFound, require_secret


class AdzunaClientError(RuntimeError):
    """Raised when Adzuna API call fails creds check or returns HTTP error."""


def _get_creds() -> tuple[str, str]:
    """Return (app_id, app_key) from canonical sources.

    Prefers the on-disk layout under ~/Documents/__cfg/apikey/adzuna/ so that
    secrets live outside the repo and are reusable across repos. Falls back
    to env vars (the previous behaviour) so .env-based setups keep working.
    """
    try:
        app_id = require_secret("adzuna", "app_id", "ADZUNA_APP_ID") or ""
        app_key = require_secret("adzuna", "app_key", "ADZUNA_APP_KEY") or ""
    except SecretNotFound as e:
        raise AdzunaClientError(str(e)) from None
    if not app_id or not app_key:
        raise AdzunaClientError(
            "Adzuna credentials not set. Populate either\n"
            "  ~/Documents/__cfg/apikey/adzuna/app_id and app_key,\n"
            "  or env vars ADZUNA_APP_ID + ADZUNA_APP_KEY."
        )
    return app_id, app_key


def _build_url(
    base_url: str,
    country: str,
    results_per_page: int,
    page: int,
    search_terms: Iterable[str] = (),
    location: str = "",
) -> str:
    country = (country or "gb").lower().strip()
    what = " ".join(t.strip() for t in search_terms if t and t.strip())
    params: dict[str, Any] = {
        "app_id": _get_creds()[0],
        "app_key": _get_creds()[1],
        "results_per_page": int(results_per_page),
    }
    if what:
        params["what"] = what
    if location:
        params["where"] = location
    qs = urllib.parse.urlencode(params)
    return f"{base_url.rstrip('/')}/{country}/search/{int(page)}?{qs}"


def _normalise(raw: dict[str, Any]) -> JobListing:
    source_id = str(raw.get("id") or "").strip() or str(hash(raw.get("redirect_url") or raw.get("title") or ""))
    salary_min = raw.get("salary_min")
    salary_max = raw.get("salary_max")
    try:
        smin = int(salary_min) if salary_min is not None else None
    except (TypeError, ValueError):
        smin = None
    try:
        smax = int(salary_max) if salary_max is not None else None
    except (TypeError, ValueError):
        smax = None
    return JobListing(
        source=ListingSource.ADZUNA,
        source_id=source_id,
        title=str(raw.get("title") or "").strip(),
        company=str(raw.get("company", {}).get("display_name") if isinstance(raw.get("company"), dict) else (raw.get("company") or "")).strip(),
        location=str(raw.get("location", {}).get("display_name") if isinstance(raw.get("location"), dict) else (raw.get("location") or "")).strip(),
        description=str(raw.get("description") or "").strip(),
        url=str(raw.get("redirect_url") or raw.get("url") or "").strip(),
        posted_at=_parse_date(raw.get("created")),
        salary_min=smin,
        salary_max=smax,
        contract_type=_norm_contract(raw.get("contract_type")),
        remote=None,
        raw=raw,
    )


def _norm_contract(value: Any) -> str | None:
    if not value:
        return None
    v = str(value).strip().lower()
    if v in {"permanent", "contract", "full_time", "part_time"}:
        return v
    return None


def fetch_adzuna(
    source,
    search_terms: Iterable[str] = (),
    location: str = "",
    *,
    timeout_s: float = 30.0,
) -> list[JobListing]:
    """Fetch all pages from Adzuna for the given search terms.

    `source` is an IngestSource from load_search_config(). Its extras carry
    `country`, `results_per_page`, `max_pages`.
    """
    extras = source.extras or {}
    country = str(extras.get("country") or "gb").strip()
    rpp = int(extras.get("results_per_page") or 50)
    max_pages = int(extras.get("max_pages") or 3)
    base_url = source.base_url

    _get_creds()

    listings: list[JobListing] = []
    for page in range(1, max_pages + 1):
        url = _build_url(base_url, country, rpp, page, search_terms, location)
        resp = requests.get(url, timeout=timeout_s)
        if resp.status_code != 200:
            raise AdzunaClientError(
                f"Adzuna HTTP {resp.status_code} page={page}: {resp.text[:200]}"
            )
        data = resp.json() or {}
        results = data.get("results") or []
        if not results:
            break
        for raw in results:
            try:
                listings.append(_normalise(raw))
            except Exception:
                continue
        if len(results) < rpp:
            break
    return listings
