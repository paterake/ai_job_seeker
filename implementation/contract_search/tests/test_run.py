import json

from ai_job_seeker.ingest import load_search_config
from contract_search import config as cfg_mod
from contract_search.config import Profile
from contract_search.run import run_search, write_outputs


def test_dry_run_writes_outputs(tmp_path):
    ingest_cfg = load_search_config(cfg_mod.DEFAULT_SEARCH_CFG)
    profile = Profile(name="Test", queries=("data engineer",), title_weights={"data engineer": 100},
                      locations=("london",), remote="hybrid_or_remote_ok", skills=("python",))
    policy = cfg_mod.load_scoring()
    policy = type(policy)(**{**policy.__dict__, "require_contract": False})
    result = run_search(ingest_cfg, profile, policy, dry_run=True)
    assert result.fetched > 0
    md, js = write_outputs(result, profile, tmp_path)
    assert md.is_file() and isinstance(json.loads(js.read_text()), list)


def _profile(remote="hybrid_or_remote_ok"):
    return Profile(name="Test", queries=("data architect",), title_weights={"data architect": 100},
                   locations=("london",), remote=remote, skills=("python",))


def test_drops_are_counted_by_trimmed_reason(monkeypatch):
    from ai_job_seeker.ingest.schema import JobListing, ListingSource
    import contract_search.run as run_mod

    junior = JobListing(source=ListingSource.ADZUNA, source_id="1", title="Junior Data Architect", company="A",
                        location="London", description="Contract", url="u")
    monkeypatch.setattr(run_mod, "gather", lambda *a, **k: ([junior], []))
    result = run_search(load_search_config(cfg_mod.DEFAULT_SEARCH_CFG), _profile(), cfg_mod.load_scoring())
    assert result.drops == {"blocked title phrase": 1}


def test_real_policy_requires_a_contract_signal(monkeypatch):
    from ai_job_seeker.ingest.schema import JobListing, ListingSource
    import contract_search.run as run_mod

    def listing(i, desc):
        return JobListing(source=ListingSource.ADZUNA, source_id=str(i), title="Data Architect", company=f"C{i}",
                          location="London", description=desc, url="u")
    monkeypatch.setattr(run_mod, "gather", lambda *a, **k: ([listing(1, "Contract, outside IR35"), listing(2, "Great team")], []))
    result = run_search(load_search_config(cfg_mod.DEFAULT_SEARCH_CFG), _profile(), cfg_mod.load_scoring())
    assert [s.listing.company for s in result.shortlist] == ["C1"]
    assert result.drops == {"no contract signal": 1}


def test_unknown_remote_mode_is_rejected():
    import pytest
    with pytest.raises(cfg_mod.ConfigError, match="target.remote"):
        run_search(load_search_config(cfg_mod.DEFAULT_SEARCH_CFG), _profile("on_site_only"), cfg_mod.load_scoring(), dry_run=True)


def test_default_profile_must_be_unambiguous(tmp_path):
    import pytest
    with pytest.raises(cfg_mod.ConfigError, match="exactly one"):
        cfg_mod.default_profile_path(tmp_path)
    (tmp_path / "a.yaml").write_text("x: 1")
    assert cfg_mod.default_profile_path(tmp_path).name == "a.yaml"
