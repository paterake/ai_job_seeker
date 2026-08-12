"""TheMuse job-search API client.

API docs: https://www.themuse.com/developers/api/v2
Auth: optional `api_key` query param. Keyless calls are rate-limited.
Secret (optional) lives in env: THEMUSE_API_KEY.
"""

from __future__ import annotations

import os
import urllib.parse
from typing import Any, Iterable

import requests

from ai_job_seeker.ingest.schema import JobListing, ListingSource, _parse_date


class MuseClientError(RuntimeError):
    """Raised when Muse API call returns non-200."""


def _get_creds() -> str:
    return os.environ.get("THEMUSE_API_KEY", "").strip()


def _build_url(
    base_url: str,
    search_terms: Iterable[str] = (),
    location: str = "",
    page: int = 1,
) -> str:
    params: dict[str, Any] = {"page": int(page)}
    key = _get_creds()
    if key:
        params["api_key"] = key
    qs = urllib.parse.urlencode(params)
    return f"{base_url.rstrip('/')}?{qs}"


def _normalise(raw: dict[str, Any]) -> JobListing:
    source_id = str(raw.get("id") or "").strip() or str(hash(raw.get("refs", {}).get("landings_page") if isinstance(raw.get("refs"), dict) else (raw.get("name") or "")))
    locs = raw.get("locations") or []
    location_bits: list[str] = []
    for l in locs:
        if isinstance(l, dict):
            name = l.get("name")
            if name:
                location_bits.append(str(name))
        elif l:
            location_bits.append(str(l))
    company_name = ""
    co = raw.get("company") or {}
    if isinstance(co, dict):
        company_name = str(co.get("name") or "").strip()
    levels = raw.get("levels") or []
    categories = raw.get("categories") or []
    remote = any("remote" in str(x).lower() for x in (list(levels) + list(categories) + list(location_bits) + [raw.get("name", "")]))

    return JobListing(
        source=ListingSource.THEMUSE,
        source_id=source_id,
        title=str(raw.get("name") or "").strip(),
        company=company_name,
        location=", ".join(location_bits),
        description=str(raw.get("contents") or raw.get("description") or "").strip(),
        url=str(
            (raw.get("refs") or {}).get("landings_page")
            if isinstance(raw.get("refs"), dict)
            else (raw.get("url") or "")
        ).strip(),
        posted_at=_parse_date(raw.get("publication_date")),
        remote=True if remote else None,
        raw=raw,
    )


def fetch_themuse(
    source,
    search_terms: Iterable[str] = (),
    location: str = "",
    *,
    timeout_s: float = 30.0,
    max_pages: int = 3,
) -> list[JobListing]:
    """Fetch listings from TheMuse (keyless or with API key)."""
    base_url = source.base_url
    listings: list[JobListing] = []
    for page in range(1, max_pages + 1):
        url = _build_url(base_url, search_terms, location, page)
        resp = requests.get(url, timeout=timeout_s)
        if resp.status_code != 200:
            raise MuseClientError(
                f"TheMuse HTTP {resp.status_code} page={page}: {resp.text[:200]}"
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
    return listings
