"""Smoke tests for Stage 3 (Match): deterministic scorer, LLM-judge mock,
rank pipeline, and CLI integration. All tests are offline — no network.

Patterns established by Stage 2 tests:
  - Config YAML resolved via Path(__file__).resolve().parents[1] / "config".
  - CLI tests redirect stdout/stderr through io.StringIO.
  - LLM judge mocked via monkeypatch on ai_agent_core.execution.generate_json.
"""

from __future__ import annotations

import io
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from ai_agent_core.execution import (
    AgentHandoffRequired,
    ExecutionConfig,
    ExecutionMode,
)

from ai_job_seeker.ingest import (
    JobListing,
    ListingSource,
    load_search_config,
    run_ingest_dry,
)
from ai_job_seeker.match import (
    ScoredListing,
    rank_listings,
    score_deterministic,
    score_with_llm,
)
from ai_job_seeker.match.deterministic import score_deterministic as _score_d
from ai_job_seeker.match.schema import ScoredListing as _SL

DEFAULT_SEARCH = Path(__file__).resolve().parents[1] / "config" / "search.yaml"


def _base_profile(**updates):
    base = {
        "identity": {"name": "Test Candidate"},
        "target": {
            "roles": ["Data Engineer", "Python Engineer"],
            "locations": ["London", "Manchester"],
            "remote": "hybrid_or_remote_ok",
            "expected_salary_min": 60000,
        },
        "summary": "Test summary",
        "skills": ["Python", "SQL", "ETL"],
        "experience": [{"role": "DE", "years": 5}],
    }
    target = dict(base["target"])
    target.update(updates.pop("target", {}) or {})
    base.update(updates)
    base["target"] = target
    return base


def _listing(
    title="Data Engineer",
    location="London",
    remote=True,
    salary_min=60000,
    salary_max=80000,
    days_ago=2,
    sid="1",
    source=ListingSource.ADZUNA,
    company="Acme",
    description="Build data pipelines with Python and SQL",
):
    return JobListing(
        source=source,
        source_id=sid,
        title=title,
        company=company,
        location=location,
        description=description,
        url=f"https://example.com/{sid}",
        posted_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
        salary_min=salary_min,
        salary_max=salary_max,
        remote=remote,
        contract_type="permanent",
    )


def test_deterministic_role_keyword_match_vs_mismatch():
    p_match = _base_profile()
    p_mismatch = _base_profile(target={"roles": ["Veterinarian", "Dentist"]})
    l = _listing(title="Senior Data Engineer")
    s_match, e_match = _score_d(p_match, l)
    s_mismatch, e_mismatch = _score_d(p_mismatch, l)
    assert s_match > s_mismatch
    assert any("keyword" in b.lower() or "role" in b.lower() for b in e_match)


def test_deterministic_location_match_vs_mismatch():
    p_match = _base_profile()
    p_mismatch = _base_profile(target={"locations": ["Glasgow", "Bristol"]})
    l = _listing(location="London, UK")
    s_match, _ = _score_d(p_match, l)
    s_mismatch, _ = _score_d(p_mismatch, l)
    assert s_match > s_mismatch


def test_deterministic_remote_match_vs_mismatch():
    p_remote_only = _base_profile(target={"remote": "remote_only"})
    p_onsite_only = _base_profile(target={"remote": "onsite_only"})
    l_remote = _listing(remote=True)
    s_rem, _ = _score_d(p_remote_only, l_remote)
    s_onsite, e_onsite = _score_d(p_onsite_only, l_remote)
    assert s_rem > s_onsite
    assert any("remote" in b.lower() for b in e_onsite)


def test_deterministic_salary_below_minimum_penalises():
    p = _base_profile()
    l_ok = _listing(salary_min=65000, salary_max=85000)
    l_low = _listing(salary_min=40000, salary_max=45000)
    s_ok, _ = _score_d(p, l_ok)
    s_low, e_low = _score_d(p, l_low)
    assert s_low < s_ok
    assert any("salary" in b.lower() and "below" in b.lower() for b in e_low)


def test_deterministic_no_salary_preference_neutral():
    p = _base_profile()
    del p["target"]["expected_salary_min"]
    l = _listing(salary_min=40000, salary_max=50000)
    s, e = _score_d(p, l)
    assert 0.0 <= s <= 100.0
    assert any("no salary preference" in b.lower() for b in e)


def test_deterministic_missing_fields_no_crash():
    p_empty = _base_profile()
    p_empty["target"] = {}
    l_bare = JobListing(
        source=ListingSource.REED,
        source_id="bare",
        title="",
        company="C",
        location="",
        description="",
        url="u",
        posted_at=None,
        salary_min=None,
        salary_max=None,
        remote=None,
    )
    s, e = _score_d(p_empty, l_bare)
    assert 0.0 <= s <= 100.0
    assert isinstance(e, list) and len(e) >= 1


def test_deterministic_freshness_bonus_applies():
    p = _base_profile()
    cfg = load_search_config(DEFAULT_SEARCH)
    half = cfg.max_age_days // 2
    l_fresh = _listing(days_ago=max(1, half - 1))
    l_stale = _listing(days_ago=cfg.max_age_days - 1, sid="stale")
    s_fresh, e_fresh = _score_d(p, l_fresh, max_age_days=cfg.max_age_days)
    s_stale, _ = _score_d(p, l_stale, max_age_days=cfg.max_age_days)
    assert s_fresh >= s_stale
    assert any("fresh" in b.lower() or "freshness" in b.lower() or "threshold" in b.lower() for b in e_fresh)


def test_score_normalised_to_zero_100_bounds():
    p_very_good = _base_profile()
    p_very_good["target"]["expected_salary_min"] = 30000
    l_ideal = _listing(
        title="Senior Data Engineer Python ETL",
        location="Central London",
        remote=True,
        salary_min=90000,
        salary_max=120000,
        days_ago=1,
    )
    s, _ = _score_d(p_very_good, l_ideal, max_age_days=21)
    assert 0.0 <= s <= 100.0

    p_bad = _base_profile(target={"remote": "remote_only", "expected_salary_min": 200000})
    p_bad["target"]["roles"] = ["Chef"]
    p_bad["target"]["locations"] = ["Sydney"]
    l_terrible = _listing(
        title="Head Chef",
        location="Sydney NSW",
        remote=False,
        salary_min=40000,
        salary_max=50000,
        days_ago=30,
    )
    s2, _ = _score_d(p_bad, l_terrible, max_age_days=7)
    assert 0.0 <= s2 <= 100.0


def test_llm_judge_mock_merges_scores_into_final(monkeypatch):
    p = _base_profile()
    l1 = _listing(title="Data Engineer", sid="de1")
    l2 = _listing(title="Python Engineer", sid="pe1", source=ListingSource.REED)
    listings = [l1, l2]

    fake_result = {
        "per_listing": [
            {
                "source": "adzuna",
                "source_id": "de1",
                "phase2_score_0_100": 92.5,
                "fit_rationale_3_bullets": ["a", "b", "c"],
                "fabricated_claim_flags": [],
            },
            {
                "source": "reed",
                "source_id": "pe1",
                "phase2_score_0_100": 55.0,
                "fit_rationale_3_bullets": ["x", "y", "z"],
                "fabricated_claim_flags": ["requires 10y Fortran not in profile"],
            },
        ]
    }

    calls = []

    def _fake_generate_json(cfg, prompt_text, **kw):
        calls.append((cfg, prompt_text, kw))
        return fake_result

    monkeypatch.setattr(
        "ai_job_seeker.match.llm_judge.generate_json",
        _fake_generate_json,
    )

    cfg = ExecutionConfig()
    mode = ExecutionMode.OLLAMA
    scored = rank_listings(p, listings, cfg=cfg, mode=mode, top_n=10)

    assert len(calls) == 1
    _, prompt_text, kw = calls[0]
    assert "PROFILE DATA" in prompt_text and "LISTINGS" in prompt_text
    assert "INSTRUCTIONS" in prompt_text
    instructions_end = prompt_text.find("END OF INSTRUCTIONS")
    listings_fence = prompt_text.find("```LISTINGS")
    assert instructions_end > 0 and listings_fence > instructions_end, (
        "instructions section must terminate before listings fence begins"
    )
    fenced = prompt_text.split("```LISTINGS", 1)
    after_fence_label = fenced[1] if len(fenced) > 1 else ""
    after_ticks = after_fence_label.split("\n", 1)[1] if "\n" in after_fence_label else ""
    assert "instructions" not in after_ticks.lower(), (
        "raw listings content (after fence header line) must not contain the word instructions"
    )
    assert kw.get("require_dict") is True

    assert len(scored) == 2
    by_sid = {s.listing.source_id: s for s in scored}
    de = by_sid["de1"]
    pe = by_sid["pe1"]
    assert de.phase2_score == 92.5
    assert pe.phase2_score == 55.0
    assert de.final_score == pytest.approx(de.phase1_score * 0.4 + 92.5 * 0.6)
    assert pe.final_score == pytest.approx(pe.phase1_score * 0.4 + 55.0 * 0.6)
    assert pe.fabricated_claim_flags == ["requires 10y Fortran not in profile"]
    assert de.final_score > pe.final_score


def test_llm_judge_agent_handoff_prints_and_reraises(monkeypatch, capsys):
    from ai_job_seeker.match.llm_judge import score_with_llm as _sllm

    def _fake_raise(cfg, prompt_text, **kw):
        raise AgentHandoffRequired("need agent")

    monkeypatch.setattr(
        "ai_job_seeker.match.llm_judge.generate_json",
        _fake_raise,
    )

    cfg = ExecutionConfig()
    p = _base_profile()
    l = _listing()
    with pytest.raises(AgentHandoffRequired):
        _sllm(cfg, p, [l])
    out = capsys.readouterr().out
    lowered = out.lower()
    assert "coding agent" in lowered or "agent handoff" in lowered or "handoff" in lowered


def test_rank_listings_pipeline_length_and_dense_rank():
    cfg = load_search_config(DEFAULT_SEARCH)
    p = _base_profile()
    listings = run_ingest_dry(cfg)
    assert len(listings) >= 1
    scored = rank_listings(p, listings, top_n=10, max_age_days=cfg.max_age_days)
    assert len(scored) <= 10
    positions = [s.ranked_position for s in scored]
    assert positions == list(range(1, len(scored) + 1))
    seen_keys = {(s.listing.source.value, s.listing.source_id) for s in scored}
    assert len(seen_keys) == len(scored)


def test_rank_listings_agent_mode_skips_phase2():
    p = _base_profile()
    listings = [_listing(sid=str(i)) for i in range(3)]
    scored = rank_listings(p, listings, cfg=None, mode=None, top_n=10)
    assert all(s.phase2_score is None for s in scored)
    for s in scored:
        assert s.final_score == pytest.approx(s.phase1_score)


def test_rank_listings_ties_stable_sort():
    p = _base_profile()
    p["target"] = {}
    listings = [
        _listing(title="J1", company="A", sid="b", days_ago=1),
        _listing(title="J1", company="A", sid="a", days_ago=1),
    ]
    scored = rank_listings(p, listings, top_n=10)
    if scored[0].final_score == scored[1].final_score:
        assert scored[0].listing.source_id < scored[1].listing.source_id


def test_scored_listing_to_dict_roundtrippable():
    l = _listing()
    s = _SL(
        listing=l,
        phase1_score=70.0,
        phase1_evidence=["e1", "e2"],
        phase2_score=85.0,
        phase2_rationale=["r1", "r2", "r3"],
        fabricated_claim_flags=["f1"],
        final_score=79.0,
        ranked_position=1,
    )
    d = s.to_dict()
    assert "raw" not in d["listing"]
    assert d["phase1_score"] == 70.0
    assert d["phase2_rationale"] == ["r1", "r2", "r3"]
    assert d["ranked_position"] == 1
    text = json.dumps(d, default=str)
    assert json.loads(text)["listing"]["source"] == "adzuna"


def _ensure_test_profile():
    cfg_dir = Path(__file__).resolve().parents[1] / "config" / "profile"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    prof = cfg_dir / "kiera.yaml"
    if not prof.is_file():
        prof.write_text(
            """
identity:
  name: Kiera Test
  email: kiera@example.invalid
target:
  roles:
    - Data Engineer
    - Python Engineer
  locations:
    - London
    - Manchester
  remote: hybrid_or_remote_ok
  expected_salary_min: 60000
summary: Engineer with 5 years building data systems.
skills:
  - Python
  - SQL
  - ETL
  - Airflow
experience:
  - role: Senior Data Engineer
    years: 3
    company: TechCo
  - role: Data Engineer
    years: 2
    company: StartupX
""".strip()
            + "\n",
            encoding="utf-8",
        )
    return str(prof)


def test_cli_match_default_dry_run_no_flags_zero_exit():
    _ensure_test_profile()
    from ai_job_seeker.cli import main

    old = sys.stdout, sys.stderr
    buf = io.StringIO()
    errbuf = io.StringIO()
    try:
        sys.stdout = buf
        sys.stderr = errbuf
        rc = main(["match"])
    finally:
        sys.stdout, sys.stderr = old
    assert rc == 0, f"stderr: {errbuf.getvalue()}"
    out = buf.getvalue()
    assert "Backend mode: agent" in out
    assert "phase-2 LLM judge skipped" in out
    assert "Final" in out and "P1" in out and "Title" in out


def test_cli_match_agent_handoff_exits_2(monkeypatch):
    _ensure_test_profile()
    from ai_job_seeker.cli import main

    def _fake_generate_json_raises(cfg, prompt_text, **kw):
        raise AgentHandoffRequired("simulated phase-2 agent handoff")

    monkeypatch.setattr(
        "ai_job_seeker.match.llm_judge.generate_json",
        _fake_generate_json_raises,
    )

    old = sys.stdout, sys.stderr
    buf = io.StringIO()
    errbuf = io.StringIO()
    rc = 0
    try:
        sys.stdout = buf
        sys.stderr = errbuf
        rc = main(["match", "--ollama-model", "qwen3.5:9b"])
    except SystemExit as e:
        rc = e.code if isinstance(e.code, int) else 2
    finally:
        sys.stdout, sys.stderr = old
    combined = buf.getvalue().lower() + errbuf.getvalue().lower()
    assert rc == 2, f"expected exit=2, got rc={rc}. stdout+stderr:\n{combined[:1000]}"
    assert "coding agent" in combined or "handoff" in combined
