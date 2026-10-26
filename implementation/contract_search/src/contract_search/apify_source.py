"""Fetch listings from configured Apify actors and map them to JobListing.

Opt-in and failure-tolerant: a missing token, an Apify refusal (credit used up, permissions) or a bad
response becomes a recorded skip for that actor, never an aborted run.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
import yaml

from ai_job_seeker.ingest.schema import JobListing

from contract_search.config import CONFIG_DIR, ConfigError, Profile

DEFAULT_APIFY_CFG = CONFIG_DIR / "apify.yaml"
TOKEN_ENV = "APIFY_API_TOKEN"
_TOP_KEYS = {"base_url", "request_timeout_s", "poll_interval_s", "max_wait_s", "max_queries", "actors"}
_ACTOR_KEYS = {"actor", "query_field", "query_suffix", "location_field", "input", "fields"}
_FIELD_KEYS = {"id", "title", "company", "location", "description", "url", "posted_at", "contract_type", "rate", "ir35"}


class SourceTag(str):
    """Source label that quacks like ListingSource (`.value`) without editing the shared enum."""

    @property
    def value(self) -> str:
        return str(self)


@dataclass(frozen=True)
class ApifyActor:
    name: str
    actor: str
    query_field: str
    query_suffix: str
    location_field: str
    input: dict[str, Any]
    fields: dict[str, str]


@dataclass(frozen=True)
class ApifyConfig:
    base_url: str
    request_timeout_s: int
    poll_interval_s: int
    max_wait_s: int
    max_queries: int
    actors: tuple[ApifyActor, ...]


def load_apify_config(path: str | Path = DEFAULT_APIFY_CFG) -> ApifyConfig:
    path = Path(path)
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as e:
        raise ConfigError(f"cannot read {path}: {e}") from e
    if not isinstance(raw, dict) or set(raw) != _TOP_KEYS:
        raise ConfigError(f"{path}: top-level keys must be exactly {sorted(_TOP_KEYS)}")
    actors = []
    for name, block in (raw["actors"] or {}).items():
        if not isinstance(block, dict) or set(block) != _ACTOR_KEYS:
            raise ConfigError(f"{path} actors.{name}: keys must be exactly {sorted(_ACTOR_KEYS)}")
        fields = block["fields"]
        if not isinstance(fields, dict) or set(fields) != _FIELD_KEYS:
            raise ConfigError(f"{path} actors.{name}.fields: keys must be exactly {sorted(_FIELD_KEYS)}")
        actors.append(ApifyActor(name, block["actor"], block["query_field"], block["query_suffix"],
                                 block["location_field"], dict(block["input"]), dict(fields)))
    return ApifyConfig(str(raw["base_url"]).rstrip("/"), int(raw["request_timeout_s"]), int(raw["poll_interval_s"]),
                       int(raw["max_wait_s"]), int(raw["max_queries"]), tuple(actors))


def _parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def to_listing(actor: ApifyActor, item: dict[str, Any]) -> JobListing:
    f = actor.fields
    get = lambda key: item.get(f[key])  # noqa: E731
    rate = str(get("rate") or "").strip()
    desc = str(get("description") or "").strip()
    contract = str(get("contract_type") or "").strip().lower() or None
    return JobListing(
        source=SourceTag(actor.name),
        source_id=str(get("id") or get("url") or ""),
        title=str(get("title") or "").strip(),
        company=str(get("company") or "").strip(),
        location=str(get("location") or "").strip(),
        description=(f"Rate: {rate}\n{desc}" if rate else desc),
        url=str(get("url") or "").strip(),
        posted_at=_parse_dt(get("posted_at")),
        contract_type=contract,
        raw={"ir35": str(get("ir35") or "").strip().lower() or None},
    )


_TERMINAL = {"SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"}


def _api_error(resp: requests.Response) -> str:
    try:
        err = resp.json().get("error", {})  # a non-dict body raises AttributeError, caught by gather_apify
        return f"HTTP {resp.status_code} {err.get('type', '')}: {str(err.get('message', ''))[:160]}".strip()
    except ValueError:
        return f"HTTP {resp.status_code}"


def fetch_actor(cfg: ApifyConfig, actor: ApifyActor, profile: Profile, token: str) -> list[JobListing]:
    """Start a run, poll until it ends, then read its dataset. A run that outlives max_wait_s is aborted."""
    headers = {"Authorization": f"Bearer {token}"}
    body = dict(actor.input)
    body[actor.query_field] = [q + actor.query_suffix for q in profile.queries[: cfg.max_queries]]
    if profile.locations:
        body[actor.location_field] = profile.locations[0].title()
    resp = requests.post(f"{cfg.base_url}/acts/{actor.actor}/runs", json=body, headers=headers,
                         timeout=cfg.request_timeout_s)
    if resp.status_code not in (200, 201):
        raise RuntimeError(_api_error(resp))
    run = resp.json()["data"]
    run_id, dataset_id = run["id"], run["defaultDatasetId"]
    deadline = time.monotonic() + cfg.max_wait_s
    status = run.get("status")
    while status not in _TERMINAL:
        if time.monotonic() > deadline:
            try:
                requests.post(f"{cfg.base_url}/actor-runs/{run_id}/abort", headers=headers, timeout=cfg.request_timeout_s)
            except requests.RequestException:
                raise RuntimeError(f"run exceeded {cfg.max_wait_s}s; abort request failed, check the Apify console") from None
            raise RuntimeError(f"run exceeded {cfg.max_wait_s}s and was aborted")
        time.sleep(cfg.poll_interval_s)
        st = requests.get(f"{cfg.base_url}/actor-runs/{run_id}", headers=headers, timeout=cfg.request_timeout_s)
        if st.status_code != 200:
            raise RuntimeError(_api_error(st))
        status = st.json()["data"]["status"]
    if status != "SUCCEEDED":
        raise RuntimeError(f"run ended {status}")
    items = requests.get(f"{cfg.base_url}/datasets/{dataset_id}/items", params={"clean": "true", "format": "json"},
                         headers=headers, timeout=cfg.request_timeout_s)
    if items.status_code != 200:
        raise RuntimeError(_api_error(items))
    data = items.json()
    if not isinstance(data, list):
        raise RuntimeError("unexpected response shape")
    return [to_listing(actor, it) for it in data if isinstance(it, dict)]


def gather_apify(cfg: ApifyConfig, profile: Profile) -> tuple[list[JobListing], list[tuple[str, str]]]:
    token = os.environ.get(TOKEN_ENV, "").strip()
    if not token:
        return [], [(a.name, f"{TOKEN_ENV} not set") for a in cfg.actors]
    listings: list[JobListing] = []
    skips: list[tuple[str, str]] = []
    for actor in cfg.actors:
        try:
            listings.extend(fetch_actor(cfg, actor, profile, token))
        except (requests.RequestException, RuntimeError) as e:
            skips.append((actor.name, str(e)[:200]))
        except (KeyError, TypeError, AttributeError) as e:
            skips.append((actor.name, f"unexpected response shape ({type(e).__name__})"))
    return listings, skips
