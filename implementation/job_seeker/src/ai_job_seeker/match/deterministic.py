"""Phase-1 deterministic scorer — pure Python, no LLM.

Cheap rules applied per (profile, listing). Output is a normalised 0–100
score plus short evidence bullets. Trifecta-safe: only data-vs-data,
never assembles prompts or mixes untrusted posting text with instructions.
"""

from __future__ import annotations

import re
from typing import Any

from ai_job_seeker.ingest.schema import JobListing

_WORD_RE = re.compile(r"[A-Za-z0-9]+")


def _tokens(s: str) -> set[str]:
    return {t.lower() for t in _WORD_RE.findall(s or "")}


def score_deterministic(
    profile: dict[str, Any],
    listing: JobListing,
    *,
    max_age_days: int = 21,
) -> tuple[float, list[str]]:
    """Return (score_0_100, evidence_bullets) for a single listing.

    Never raises on absent fields; missing data contributes 0 and an
    evidence bullet is added if the component is genuinely informative.
    """
    raw = 0.0
    evidence: list[str] = []

    target = profile.get("target", {}) or {}

    roles = [str(r) for r in (target.get("roles") or []) if str(r).strip()]
    role_tokens: set[str] = set()
    for r in roles:
        role_tokens |= _tokens(r)
    title_tokens = _tokens(listing.title)
    if role_tokens and title_tokens:
        overlap = role_tokens & title_tokens
        bonus = min(25.0, 5.0 * len(overlap))
        if bonus > 0:
            raw += bonus
            evidence.append(
                f"role keyword overlap: {len(overlap)} match(es) "
                f"({', '.join(sorted(overlap)[:5])}) → +{bonus:.0f}"
            )
    else:
        evidence.append("role keywords: no overlap (no profile roles or empty title)")

    locations = [str(loc) for loc in (target.get("locations") or []) if str(loc).strip()]
    loc_match = False
    listing_loc = (listing.location or "").lower()
    for pref in locations:
        if pref.lower() in listing_loc:
            loc_match = True
            break
    if loc_match:
        raw += 15.0
        evidence.append(f"location match: listing in profile target locations → +15")
    elif locations:
        evidence.append(
            f"location mismatch: profile targets {locations} vs listing '{listing.location}'"
        )

    remote_pref = str(target.get("remote") or "").strip().lower()
    is_remote = bool(listing.remote)
    if remote_pref == "remote_only":
        if is_remote:
            raw += 10.0
            evidence.append("remote match: profile requires remote + listing remote → +10")
        else:
            raw -= 5.0
            evidence.append("remote mismatch: profile requires remote, listing not remote → −5")
    elif remote_pref == "hybrid_or_remote_ok":
        if is_remote:
            raw += 7.0
            evidence.append("remote bonus: profile ok with remote + listing remote → +7")
    elif remote_pref == "onsite_only":
        if is_remote:
            raw -= 5.0
            evidence.append("remote mismatch: profile onsite-only, listing remote → −5")

    salary_min_expected = target.get("expected_salary_min")
    if salary_min_expected is not None and isinstance(salary_min_expected, (int, float)):
        if listing.salary_max is not None and listing.salary_max < salary_min_expected:
            gap = salary_min_expected - listing.salary_max
            penalty = min(15.0, gap / 1000.0)
            raw -= penalty
            evidence.append(
                f"salary below minimum: listing max={listing.salary_max} < "
                f"profile min={salary_min_expected} → −{penalty:.1f}"
            )
        elif listing.salary_min is not None and listing.salary_min >= salary_min_expected:
            bonus = min(15.0, (listing.salary_min - salary_min_expected) / 2000.0)
            raw += bonus
            evidence.append(
                f"salary meets/exceeds minimum: listing min={listing.salary_min} ≥ "
                f"profile min={salary_min_expected} → +{bonus:.1f}"
            )
    else:
        evidence.append("no salary preference in profile (salary component neutral)")

    age = listing.age_days()
    if age is not None and max_age_days and max_age_days > 0:
        threshold = max_age_days // 2
        if age <= threshold:
            raw += 5.0
            evidence.append(f"fresh posting: {age}d ≤ {threshold}d threshold → +5")
    else:
        evidence.append("posting age unknown (age bonus not applied)")

    score = max(0.0, min(100.0, raw + 40.0))
    if not evidence:
        evidence.append("baseline score, no deterministic components triggered")

    return score, evidence
