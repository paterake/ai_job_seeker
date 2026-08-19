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

# Keyword sets used for cohort-specific ranking (see rank_listings docstring).
# These are kept in the scorer module so the CLI can also use them to split
# listings into two cohorts without duplicating the token lists.

# Marketing / comms cohort — what Kiera broadly said she's targeting.
MARKETING_COHORT_KEYWORDS = {
    "marketing", "content", "communications", "pr", "brand", "social",
    "copywriting", "strategy", "production", "audience", "seo",
    "account", "coordinator", "executive", "assistant", "officer",
}

# Historian/academic/research cohort — creative, broader than just
# "library assistant". A History BA with explicit Research & Analysis
# skill + 3+ years of academic support / marking experience can
# credibly apply for all of these.
HISTORY_COHORT_KEYWORDS = {
    # Research / insight / data (her numeracy + R&A skill)
    "research", "insight", "analyst", "analysis", "analyst", "data",
    "researcher", "research assistant", "research associate", "insight executive",
    # Information / knowledge / records (libraries, archives — what she
    # mentioned applying to, closed)
    "library", "librarian", "archivist", "archive", "records", "information",
    "knowledge", "cataloguing", "metadata", "collections",
    # Heritage / culture / museums / galleries (direct use of History degree)
    "heritage", "museum", "gallery", "curatorial", "curator", "exhibition",
    "conservation", "historic", "history", "arts", "culture",
    # Policy / civil service / public sector (analytical writing, argument
    # structure — directly transfers from essay-based History degree)
    "policy", "civil service", "fast stream", "policy officer", "policy advisor",
    "public affairs", "government", "regulatory",
    # Bid / fundraising / editorial / journalist / writer (written
    # communication strength + research capability = great fit)
    "bid", "fundraising", "fundraiser", "editorial", "editor",
    "journalist", "journalism", "writer", "copywriter", "author",
    "content editor", "proofreader",
    # Education / academic support / tutoring (she has 3+ years of this on CV)
    "academic", "tutor", "tutoring", "teaching", "marker", "exam marker",
    "learning", "education", "lecturer", "teaching assistant", "sen",
    # Legal-adjacent (she said "almost paralegal, but not paralegal") —
    # these use the same research/evidence/argument skills without
    # requiring a law conversion.
    "paralegal", "legal assistant", "contracts", "compliance", "due diligence",
    "caseworker", "case work",
    # Generalist grad routes
    "graduate scheme", "graduate programme", "graduate", "associate",
    "rotational", "business analyst", "project assistant", "project coordinator",
    "administration", "administrator", "office", "operations",
}


def _tokens(s: str) -> set[str]:
    return {t.lower() for t in _WORD_RE.findall(s or "")}


def score_deterministic(
    profile: dict[str, Any],
    listing: JobListing,
    *,
    max_age_days: int = 21,
    cohort: str | None = None,
) -> tuple[float, list[str]]:
    """Return (score_0_100, evidence_bullets) for a single listing.

    Never raises on absent fields; missing data contributes 0 and an
    evidence bullet is added if the component is genuinely informative.

    ``cohort`` can be ``None`` (default single-score mode), ``"marketing"``,
    or ``"history"``. The two cohort modes add a weighted bonus tied to
    Kiera's CV strengths:

    * ``marketing`` — adds a small bonus for any MARKETING_COHORT_KEYWORDS
      overlap against title/description (keeps today's top-25 ordering
      stable against the marketing pool).
    * ``history`` — adds a larger bonus for HISTORY_COHORT_KEYWORDS overlap,
      weighted by explicit CV strengths: Research & Analysis hard skill
      + 3+ years of academic support/marker roles + History BA itself.
      This elevates research/editorial/library/archive/policy/fundraising/
      bid/grad-scheme roles that otherwise score neutrally under the broad
      marketing-role target set.
    """
    raw = 0.0
    evidence: list[str] = []

    target = profile.get("target", {}) or {}

    roles = [str(r) for r in (target.get("roles") or []) if str(r).strip()]
    role_tokens: set[str] = set()
    for r in roles:
        role_tokens |= _tokens(r)

    # For the historian cohort, also accept history/research-adjacent tokens as
    # "pseudo target roles" for the role-overlap component. Otherwise the
    # marketing-heavy target.roles list (from the profile) keeps genuine
    # research / policy / archive / grad-scheme roles from ever reaching the
    # top of Section B, even with the cohort bonus bands below.
    #
    # This augmentation applies ONLY to score_deterministic(cohort="history") —
    # Section A (marketing cohort = None / "marketing") uses the vanilla
    # target.roles tokens, so Section A's top-25 ordering is preserved
    # byte-for-byte as the user requested.
    if cohort == "history":
        augmented: set[str] = set(role_tokens)
        for kw in HISTORY_COHORT_KEYWORDS:
            augmented |= _tokens(kw)
        role_tokens = augmented

    title_tokens = _tokens(listing.title)
    desc_tokens = _tokens(listing.description or "")
    title_desc_tokens = title_tokens | desc_tokens

    if role_tokens and title_desc_tokens:
        overlap = role_tokens & title_tokens
        # Also give partial credit for role keywords only in the description
        # (e.g. a policy role title might only say "Officer" but description
        # mentions "research and analysis").
        desc_only_overlap = (role_tokens & desc_tokens) - overlap
        bonus = min(25.0, 5.0 * len(overlap))
        bonus += min(8.0, 1.0 * len(desc_only_overlap))
        if bonus > 0:
            raw += bonus
            matched = sorted(overlap | desc_only_overlap)
            evidence.append(
                f"role keyword overlap: {len(matched)} match(es) "
                f"({', '.join(matched[:6])}) → +{bonus:.0f}"
            )
    else:
        evidence.append("role keywords: no overlap (no profile roles or empty title)")

    # --- Cohort-specific bonus (new) ----------------------------------------
    if cohort == "marketing":
        coh_tokens: set[str] = set()
        for kw in MARKETING_COHORT_KEYWORDS:
            coh_tokens |= _tokens(kw)
        coh_overlap = coh_tokens & title_desc_tokens
        bonus = min(6.0, 0.75 * len(coh_overlap))
        if bonus > 0:
            raw += bonus
            evidence.append(
                f"marketing cohort boost: {len(coh_overlap)} keyword match(es) → +{bonus:.0f}"
            )
    elif cohort == "history":
        # Weighted to her CV: 1) explicit hard skill "Research & Analysis"
        # signal (heavy weight — matches her real strongest capability),
        # 2) 3+ years academic support/marker on CV (medium), 3) History BA
        # (medium — direct degree fit for heritage/archive/library/editorial
        # categories). These are surfaced as *three separate bonus bands* in
        # the evidence so Kiera can see "why this role fits my academic
        # strengths".
        coh_tokens = set()
        for kw in HISTORY_COHORT_KEYWORDS:
            coh_tokens |= _tokens(kw)

        # Band 1: title match — strongest single signal, highest weight.
        title_overlap = coh_tokens & title_tokens
        band1 = min(10.0, 2.0 * len(title_overlap))

        # Band 2: description-only match (research-heavy job titles that
        # don't say "research" in the title) — medium weight.
        desc_overlap = (coh_tokens & desc_tokens) - title_overlap
        band2 = min(7.0, 0.9 * len(desc_overlap))

        # Band 3: explicit hard-skill "Research & Analysis" + her
        # academic-support CV roles vs a few extra synonyms that history-fit
        # roles also use.
        strengths_extra = {
            "essay", "dissertation", "archive", "archives", "primary",
            "secondary", "sources", "citation", "literature", "review",
            "argument", "briefing", "paper", "report", "editing",
            "copyedit", "proofread", "heritage", "interpretation",
        }
        strength_tokens = _tokens(
            "Research & Analysis Written Communication Numeracy academic support "
            "teaching marking tutoring"
        ) | strengths_extra
        strength_overlap = strength_tokens & title_desc_tokens
        band3 = min(5.0, 0.6 * len(strength_overlap))

        bonus = band1 + band2 + band3
        if bonus > 0:
            raw += bonus
            pieces: list[str] = []
            if band1:
                pieces.append(f"title={band1:.0f}")
            if band2:
                pieces.append(f"desc={band2:.0f}")
            if band3:
                pieces.append(f"strengths={band3:.0f}")
            evidence.append(
                f"historian/research-academic boost: +{bonus:.0f}  "
                f"({', '.join(pieces)})  "
                f"— {len(title_overlap | desc_overlap)} cohort keyword(s) + "
                f"{len(strength_overlap)} strength synonym(s)"
            )
    # end cohort bonus --------------------------------------------------------

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
