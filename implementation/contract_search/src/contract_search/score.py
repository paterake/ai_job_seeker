"""Score one listing against the profile and scoring policy. Pure rules, no model.

Every signal is an explicit phrase or pattern from config (data-driven, per
code-architecture.md → Driver Selection): nothing here infers meaning.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

from ai_job_seeker.ingest.schema import JobListing

from contract_search.config import Profile, Scoring


@dataclass
class Scored:
    listing: JobListing
    score: int
    ir35: str                      # "outside" | "inside" | "unstated"
    day_rate: str | None
    remote: bool
    evidence: list[str] = field(default_factory=list)


def _has_phrase(text: str, phrase: str) -> bool:
    return re.search(rf"(?<![A-Za-z0-9]){re.escape(phrase)}(?![A-Za-z0-9])", text) is not None


def _any(patterns, text: str) -> bool:
    return any(p.search(text) for p in patterns)


def score_listing(
    listing: JobListing,
    profile: Profile,
    policy: Scoring,
    *,
    max_age_days: int,
    now: datetime | None = None,
) -> Scored | str:
    """Return a Scored listing, or a short drop-reason string."""
    now = now or datetime.now(timezone.utc)
    title = (listing.title or "").lower()
    desc = (listing.description or "")
    text = f"{listing.title}\n{desc}"
    location = (listing.location or "").lower()
    w = policy.weights
    evidence: list[str] = []

    for phrase in policy.blocked_title_phrases:
        if _has_phrase(title, phrase):
            return f"blocked title phrase {phrase!r}"

    title_weight = max((v for k, v in profile.title_weights.items() if _has_phrase(title, k)), default=0)
    if title_weight == 0:
        return "title not in target roles"

    rate_match = policy.day_rate.search(text)
    strong_contract = rate_match is not None or _any(policy.contract_patterns, text)
    title_contract = _any(policy.contract_title_patterns, listing.title or "")
    is_contract = listing.contract_type == "contract" or strong_contract or title_contract
    if listing.contract_type in policy.blocked_contract_types and not (strong_contract or title_contract):
        return f"contract type {listing.contract_type}"
    if policy.require_contract and not is_contract:
        return "no contract signal"

    if (listing.salary_min or 0) >= policy.yearly_salary_min and not (strong_contract or title_contract):
        if _any(policy.yearly_salary_permanent, text) or not _any(policy.yearly_salary_contract, text):
            return "yearly salary without contract wording"

    remote = listing.remote is True or (
        _any(policy.remote, f"{listing.title}\n{listing.location}\n{desc[:1000]}") and not _any(policy.hybrid, text)
    )
    in_location = any(loc in location for loc in profile.locations)
    if not remote and not in_location:
        return "not in target location and not remote"

    score = round(title_weight * w["title_max"] / 100)
    evidence.append(f"title match +{score}")

    stated = (listing.raw or {}).get("ir35")
    outside = _any(policy.ir35_outside, text) or stated == "outside"
    inside = _any(policy.ir35_inside, text) or stated == "inside"
    if outside and not inside:
        ir35 = "outside"
        score += w["ir35_outside"]
        evidence.append(f"outside IR35 +{w['ir35_outside']}")
    elif inside and not outside:
        ir35 = "inside"
        score += w["ir35_inside"]
        evidence.append(f"inside IR35 {w['ir35_inside']}")
    else:
        ir35 = "unstated"

    if remote:
        score += w["remote"]
        evidence.append(f"remote +{w['remote']}")
    elif in_location:
        score += w["in_target_location"]
        evidence.append(f"target location +{w['in_target_location']}")

    if any(_has_phrase(title, p) for p in policy.seniority_phrases):
        score += w["seniority"]
        evidence.append(f"seniority +{w['seniority']}")

    if _any(policy.clearance, text):
        score += w["clearance_required"]
        evidence.append(f"clearance required {w['clearance_required']}")

    haystack = text.lower()
    matched = sorted({s for s in profile.skills if _has_phrase(haystack, s)})
    skills_pts = min(w["skills_max"], w["skills_per_match"] * len(matched))
    if skills_pts:
        score += skills_pts
        evidence.append(f"skills {len(matched)} +{skills_pts}: {', '.join(matched[:8])}")

    age = listing.age_days(now)
    if age is not None and age <= max_age_days / 2:
        score += w["fresh"]
        evidence.append(f"posted {age}d ago +{w['fresh']}")

    day_rate = None
    if rate_match:
        lo, hi = rate_match.group("lo"), rate_match.groupdict().get("hi")
        day_rate = f"£{lo}-£{hi}/day" if hi else f"£{lo}/day"
        score += w["day_rate_stated"]
        evidence.append(f"day rate {day_rate} +{w['day_rate_stated']}")

    return Scored(listing, max(0, min(100, score)), ir35, day_rate, remote, evidence)
