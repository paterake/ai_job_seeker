import pytest

from contract_search import apify_source as ap
from contract_search.config import ConfigError, Profile

PROFILE = Profile(name="T", queries=("data architect",), title_weights={"data architect": 100},
                  locations=("london",), remote="hybrid_or_remote_ok", skills=("aws",))


def test_shipped_config_loads_and_actors_are_named():
    cfg = ap.load_apify_config()
    assert {a.name for a in cfg.actors} == {"cwjobs", "jobserve"}


def test_loader_rejects_missing_field_mapping(tmp_path):
    bad = tmp_path / "a.yaml"
    bad.write_text("base_url: x\nrequest_timeout_s: 5\npoll_interval_s: 1\nmax_wait_s: 5\nmax_queries: 1\nactors:\n  a: {actor: x, query_field: q, query_suffix: '', "
                   "location_field: l, input: {}, fields: {id: id}}\n")
    with pytest.raises(ConfigError, match="fields"):
        ap.load_apify_config(bad)


def test_to_listing_maps_fields_rate_and_ir35():
    actor = ap.load_apify_config().actors[0]
    item = {"id": "9", "title": "Data Architect", "company_name": "Acme", "location": "London",
            "description_full": "Great role", "job_url": "https://x", "posted_at_datetime": "2026-10-25T10:00:00Z",
            "employment_type": "Contract", "salary_text": "£600 per day", "ir35_status": "Outside"}
    lst = ap.to_listing(actor, item)
    assert lst.source.value == "cwjobs" and lst.contract_type == "contract"
    assert lst.description.startswith("Rate: £600 per day") and lst.raw == {"ir35": "outside"}
    assert lst.posted_at is not None


def test_missing_token_skips_every_actor(monkeypatch):
    monkeypatch.delenv(ap.TOKEN_ENV, raising=False)
    listings, skips = ap.gather_apify(ap.load_apify_config(), PROFILE)
    assert listings == [] and {n for n, _ in skips} == {"cwjobs", "jobserve"}


class Resp:
    def __init__(self, status=200, body=None):
        self.status_code, self._body = status, body

    def json(self):
        return self._body


def _cfg(max_wait=1):
    cfg = ap.load_apify_config()
    return ap.ApifyConfig(cfg.base_url, 1, 0, max_wait, 2, cfg.actors)


def test_apify_refusal_becomes_a_skip_not_an_abort(monkeypatch):
    monkeypatch.setenv(ap.TOKEN_ENV, "t")
    monkeypatch.setattr(ap.requests, "post", lambda *a, **k: Resp(403, {"error": {"type": "usage-limit", "message": "credit used up"}}))
    listings, skips = ap.gather_apify(_cfg(), PROFILE)
    assert listings == [] and all("usage-limit" in r for _, r in skips)


def test_run_is_started_polled_and_read(monkeypatch):
    calls = []
    def post(url, json=None, headers=None, timeout=None):
        calls.append(("POST", url, json))
        return Resp(201, {"data": {"id": "r1", "defaultDatasetId": "d1", "status": "RUNNING"}})
    def get(url, params=None, headers=None, timeout=None):
        calls.append(("GET", url, params))
        if "actor-runs" in url:
            return Resp(200, {"data": {"status": "SUCCEEDED"}})
        return Resp(200, [{"title": "Data Architect", "company_name": "A", "description_full": "x", "employment_type": "contract"}])
    monkeypatch.setenv(ap.TOKEN_ENV, "t")
    monkeypatch.setattr(ap.requests, "post", post)
    monkeypatch.setattr(ap.requests, "get", get)
    listings, skips = ap.gather_apify(_cfg(), PROFILE)
    assert skips == [] and len(listings) == 2          # one per actor
    body = next(c[2] for c in calls if c[0] == "POST" and "cwjobs" in c[1])
    assert body["searchQueries"] == ["data architect contract"] and body["location"] == "London"


def test_slow_run_is_aborted_and_skipped(monkeypatch):
    aborted = []
    def post(url, json=None, headers=None, timeout=None):
        if url.endswith("/abort"):
            aborted.append(url)
            return Resp(200, {})
        return Resp(201, {"data": {"id": "r1", "defaultDatasetId": "d1", "status": "RUNNING"}})
    monkeypatch.setenv(ap.TOKEN_ENV, "t")
    monkeypatch.setattr(ap.requests, "post", post)
    monkeypatch.setattr(ap.requests, "get", lambda *a, **k: Resp(200, {"data": {"status": "RUNNING"}}))
    monkeypatch.setattr(ap.time, "sleep", lambda s: None)
    listings, skips = ap.gather_apify(_cfg(max_wait=-1), PROFILE)
    assert listings == [] and len(aborted) == 2 and all("aborted" in r for _, r in skips)


def test_queries_are_capped_by_config(monkeypatch):
    seen = []
    profile = Profile(name="T", queries=("a", "b", "c", "d"), title_weights={"a": 5}, locations=("london",),
                      remote="any", skills=("aws",))
    monkeypatch.setenv(ap.TOKEN_ENV, "t")
    monkeypatch.setattr(ap.requests, "post", lambda url, json=None, **k: (seen.append(json), Resp(500, {}))[1])
    ap.gather_apify(_cfg(), profile)
    assert seen[0]["searchQueries"] == ["a contract", "b contract"]


def test_malformed_start_reply_is_a_skip(monkeypatch):
    monkeypatch.setenv(ap.TOKEN_ENV, "t")
    monkeypatch.setattr(ap.requests, "post", lambda *a, **k: Resp(201, {}))
    listings, skips = ap.gather_apify(_cfg(), PROFILE)
    assert listings == [] and all("unexpected response shape" in r for _, r in skips)


def test_failed_abort_is_reported(monkeypatch):
    def post(url, json=None, headers=None, timeout=None):
        if url.endswith("/abort"):
            raise ap.requests.ConnectionError("down")
        return Resp(201, {"data": {"id": "r1", "defaultDatasetId": "d1", "status": "RUNNING"}})
    monkeypatch.setenv(ap.TOKEN_ENV, "t")
    monkeypatch.setattr(ap.requests, "post", post)
    monkeypatch.setattr(ap.requests, "get", lambda *a, **k: Resp(200, {"data": {"status": "RUNNING"}}))
    monkeypatch.setattr(ap.time, "sleep", lambda s: None)
    _, skips = ap.gather_apify(_cfg(max_wait=-1), PROFILE)
    assert all("abort request failed" in r for _, r in skips)
