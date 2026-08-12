"""Unified job-listing schema and source-tag enum.

Every client (Adzuna, Reed, Muse) returns raw JSON that is immediately
normalised into a `JobListing`. The match and draft stages consume
`JobListing` exclusively — they never see source-specific shapes.

Posting text (title, description, company blurb) is **untrusted data** per
the trifecta-isolation contract. It is carried verbatim on the dataclass
but must never be treated as instructions.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ListingSource(str, Enum):
    """Known job-source identifiers. Matches the keys in search.yaml."""

    ADZUNA = "adzuna"
    REED = "reed"
    THEMUSE = "themuse"


@dataclass(slots=True)
class JobListing:
    """Normalised, source-agnostic job posting.

    Fields marked *derived* are filled by the normaliser and are the
    stable keys used for dedupe, filtering, and downstream matching.
    """

    source: ListingSource
    source_id: str
    title: str
    company: str
    location: str
    description: str
    url: str
    posted_at: datetime | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    remote: bool | None = None
    contract_type: str | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def dedupe_key(self) -> tuple[str, str]:
        """Cross-source dedupe key. Config-driven: (normalised_title, company)."""
        return (_norm_str(self.title), _norm_str(self.company))

    def age_days(self, now: datetime | None = None) -> int | None:
        """Days since posting. Returns None if posted_at is unknown."""
        if self.posted_at is None:
            return None
        if now is None:
            now = datetime.now(timezone.utc)
        if self.posted_at.tzinfo is None:
            posted = self.posted_at.replace(tzinfo=timezone.utc)
        else:
            posted = self.posted_at
        return (now - posted).days

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        if self.posted_at is not None:
            d["posted_at"] = self.posted_at.isoformat()
        d["source"] = self.source.value
        d.pop("raw", None)
        return d


def _norm_str(s: str) -> str:
    """Case-fold and collapse whitespace for stable string keys."""
    return " ".join((s or "").strip().lower().split())


def _parse_date(value: Any) -> datetime | None:
    """Best-effort parse of a date string or timestamp. Never raises."""
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        except (ValueError, OSError):
            return None
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        formats = [
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(s, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None
