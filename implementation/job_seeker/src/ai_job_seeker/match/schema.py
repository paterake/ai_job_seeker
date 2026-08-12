"""ScoredListing schema — the output of Stage 3 match scoring.

Wraps a JobListing with phase-1 (deterministic) and optional phase-2 (LLM)
scores plus human-readable evidence. Ranked position is assigned after sort.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

from ai_job_seeker.ingest.schema import JobListing


@dataclass(slots=True)
class ScoredListing:
    """A JobListing with phase scores, evidence, and a final rank."""

    listing: JobListing
    phase1_score: float
    phase1_evidence: list[str] = field(default_factory=list)
    phase2_score: float | None = None
    phase2_rationale: list[str] | None = None
    fabricated_claim_flags: list[str] = field(default_factory=list)
    final_score: float = 0.0
    ranked_position: int | None = None

    def to_dict(self) -> dict[str, Any]:
        d = {
            "listing": self.listing.to_dict(),
            "phase1_score": self.phase1_score,
            "phase1_evidence": list(self.phase1_evidence),
            "phase2_score": self.phase2_score,
            "phase2_rationale": list(self.phase2_rationale) if self.phase2_rationale else None,
            "fabricated_claim_flags": list(self.fabricated_claim_flags),
            "final_score": self.final_score,
            "ranked_position": self.ranked_position,
        }
        return d
