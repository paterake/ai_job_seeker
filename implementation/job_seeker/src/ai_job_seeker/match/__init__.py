"""Stage 3 — Match scoring: deterministic pre-pass + optional LLM judge.

Public surface re-exports everything the CLI or downstream draft stage needs.

ExecutionConfig/ExecutionMode (from ai_agent_core) are used only by the LLM
judge gate (phase-2). They are imported lazily by rank_listings() so the rest
of the pipeline (profile + ingest) works even when ai_agent_core is missing
on disk. That keeps profile/ingest 100% PyPI-dep-only.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from ai_job_seeker.ingest.schema import JobListing
from ai_job_seeker.match.deterministic import score_deterministic
from ai_job_seeker.match.llm_judge import score_with_llm
from ai_job_seeker.match.schema import ScoredListing

if TYPE_CHECKING:
    from ai_agent_core.execution import ExecutionConfig, ExecutionMode  # noqa: F401

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


def _require_ai_agent_core_for_phase2() -> tuple[Any, Any]:
    """Return (ExecutionConfig, ExecutionMode) classes — or import loudly.

    Used only when the caller actually passes cfg AND mode (i.e. phase-2 LLM
    judge will run). If ai_agent_core isn't installed, phase-1 still works
    (caller passes cfg=None, mode=None) — this is the "agent mode" default.
    """
    try:
        from ai_agent_core.execution import ExecutionConfig as _EC, ExecutionMode as _EM
    except ImportError as e:
        raise ImportError(
            "ai_agent_core could not be imported — needed only for phase-2 LLM "
            "judge scoring. Clone/checkout ai_agent_core next to ai_job_seeker "
            "at ../ai_agent_core/ or skip phase-2 by running match without "
            "--ollama-model / --llm-provider flags (agent default = phase-1 only)."
        ) from e
    return _EC, _EM


def rank_listings(
    profile: dict[str, Any],
    listings: list[JobListing],
    *,
    cfg: Any = None,
    mode: Any = None,
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
        and getattr(mode, "value", None) != "agent"
    )
    if run_phase2 and scored:
        # Type-check the user-passed cfg/mode against ai_agent_core types only
        # when phase-2 is actually requested — otherwise keep the import cold.
        _EC, _EM = _require_ai_agent_core_for_phase2()
        if not isinstance(cfg, _EC) or not isinstance(mode, _EM):
            raise TypeError(
                "rank_listings(..., cfg=X, mode=Y) types when phase-2 is "
                f"requested must be ExecutionConfig + ExecutionMode; got "
                f"{type(cfg).__name__} and {type(mode).__name__}."
            )
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
