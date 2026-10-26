from datetime import datetime, timezone

import pytest

from ai_job_seeker.ingest.schema import JobListing, ListingSource
from contract_search.config import ConfigError, Profile, load_profile, load_scoring
from contract_search.score import Scored, score_listing

NOW = datetime(2026, 10, 26, tzinfo=timezone.utc)


@pytest.fixture(scope="module")
def policy():
    return load_scoring()


@pytest.fixture()
def profile():
    return Profile(
        name="Test",
        queries=("data architect",),
        title_weights={"data architect": 100, "data governance": 85, "data engineer": 35},
        locations=("london",),
        remote="hybrid_or_remote_ok",
        skills=("aws", "spark", "data governance"),
    )


def make(title="Data Architect", desc="Contract. Outside IR35. AWS and Spark.", location="London, UK",
         contract_type=None, remote=None, posted=NOW):
    return JobListing(source=ListingSource.ADZUNA, source_id="1", title=title, company="Acme",
                      location=location, description=desc, url="https://x", posted_at=posted,
                      contract_type=contract_type, remote=remote)


def score(listing, profile, policy):
    return score_listing(listing, profile, policy, max_age_days=14, now=NOW)


def test_architect_title_is_not_blocked(profile, policy):
    assert isinstance(score(make(), profile, policy), Scored)


def test_outside_ir35_outranks_inside_and_unstated(profile, policy):
    out = score(make(desc="Contract. Outside IR35."), profile, policy)
    unstated = score(make(desc="Contract role, 6 month contract."), profile, policy)
    inside = score(make(desc="Contract. Inside IR35."), profile, policy)
    assert out.ir35 == "outside" and inside.ir35 == "inside" and unstated.ir35 == "unstated"
    assert out.score > unstated.score > inside.score


def test_permanent_is_dropped(profile, policy):
    r = score(make(desc="Permanent role, £90,000 per annum.", contract_type="permanent"), profile, policy)
    assert r == "contract type permanent"


def test_no_contract_signal_is_dropped(profile, policy):
    assert score(make(desc="Great team, hybrid working."), profile, policy) == "no contract signal"


def test_labelled_contract_with_no_text_signal_is_kept(profile, policy):
    assert isinstance(score(make(desc="Great team.", contract_type="contract"), profile, policy), Scored)


def test_day_rate_is_parsed_and_counts_as_contract(profile, policy):
    r = score(make(desc="£650 - £750 per day, London."), profile, policy)
    assert isinstance(r, Scored) and r.day_rate == "£650-£750/day"


def test_title_outside_targets_is_dropped(profile, policy):
    assert score(make(title="Marketing Manager (Contract)"), profile, policy) == "title not in target roles"


def test_junior_title_is_dropped(profile, policy):
    assert score(make(title="Junior Data Architect"), profile, policy).startswith("blocked title phrase")


def test_location_gate(profile, policy):
    assert score(make(location="Manchester"), profile, policy) == "not in target location and not remote"
    assert isinstance(score(make(location="Manchester", desc="Contract, fully remote, outside IR35."), profile, policy), Scored)


def test_loader_rejects_undeclared_key(tmp_path):
    bad = tmp_path / "p.yaml"
    bad.write_text("identity: {name: x}\nsummary: s\nskills: [a]\ntarget: {queries: [q], title_weights: {a: 5}, "
                   "locations: [], remote: any, extra: 1}\n")
    with pytest.raises(ConfigError, match="undeclared"):
        load_profile(bad)


def test_not_inside_ir35_is_scored_outside(profile, policy):
    r = score(make(desc="Contract role, not inside IR35 per the client."), profile, policy)
    assert r.ir35 == "outside"


def test_actor_stated_ir35_is_honoured(profile, policy):
    lst = make(desc="Great team.", contract_type="contract")
    lst.raw = {"ir35": "inside"}
    assert score(lst, profile, policy).ir35 == "inside"
