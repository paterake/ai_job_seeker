"""Stage 3 — Match scoring: deterministic pre-pass + optional LLM judge.

Public surface re-exports everything the CLI or downstream draft stage needs.
"""

from __future__ import annotations

from typing import Any

from ai_agent_core.execution import ExecutionConfig, ExecutionMode

from ai_job_seeker.ingest.schema import JobListing
from ai_job_seeker.match.deterministic import score_deterministic
from ai_job_seeker.match.llm_judge import score_with_llm
from ai_job_seeker.match.schema import ScoredListing

__all__ = [
    "ScoredListing",
    "rank_listings",
    "score_deterministic",
    "score_with_llm",
]

_DEFAULT_W1 = 0.4
_DEFAULT_W2 = 0.6


def _listing_key(l: JobListing) -> str:
    return f"{l.source.value}::{l.source_id}"


def rank_listings(
    profile: dict[str, Any],
    listings: list[JobListing],
    *,
    cfg: ExecutionConfig | None = None,
    mode: ExecutionMode | None = None,
    top_n: int = 10,
    w1: float = _DEFAULT_W1,
    w2: float = _DEFAULT_W2,
    max_age_days: int = 21,
) -> list[ScoredListing]:
    """Score listings, optionally run LLM judge, sort, and assign rank.

    Phase weights: final = phase1*w1 + (phase2 or phase1)*w2 (so phase-2
    absent collapses to phase-1 only). Sort is (final_score desc, source_id
    asc) for stable ties.
    """
    scored: list[ScoredListing] = []
    for lst in listings:
        p1, evidence = score_deterministic(profile, lst, max_age_days=max_age_days)
        scored.append(
            ScoredListing(
                listing=lst,
                phase1_score=p1,
                phase1_evidence=evidence,
            )
        )

    run_phase2 = (
        cfg is not None
        and mode is not None
        and mode.value != "agent"
    )
    if run_phase2 and scored:
        phase2 = score_with_llm(cfg, profile, [s.listing for s in scored])
        for s in scored:
            key = _listing_key(s.listing)
            p2_row = phase2.get(key)
            if p2_row:
                s.phase2_score = p2_row.get("phase2_score")
                s.phase2_rationale = p2_row.get("rationale")
                s.fabricated_claim_flags = p2_row.get("fabricated_claim_flags") or []

    for s in scored:
        p2 = s.phase2_score if s.phase2_score is not None else s.phase1_score
        s.final_score = s.phase1_score * w1 + p2 * w2

    scored.sort(key=lambda s: (-s.final_score, _listing_key(s.listing)))

    if top_n and top_n > 0:
        scored = scored[:top_n]

    for i, s in enumerate(scored, start=1):
        s.ranked_position = i

    return scored
