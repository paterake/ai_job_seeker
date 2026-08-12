"""Load and validate search.yaml — source enablement, base URLs, limits,
and cross-source filter knobs.

Secrets (API keys) are never in this YAML; they come from the environment
(.env). This file only carries non-PII, non-secret configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

DEFAULT_SEARCH_CFG = "implementation/job_seeker/config/search.yaml"

KNOWN_SOURCES = ("adzuna", "reed", "themuse")


@dataclass(slots=True)
class IngestSource:
    name: str
    enabled: bool
    base_url: str
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class IngestConfig:
    sources: dict[str, IngestSource]
    max_age_days: int
    dedupe_on: list[str]

    def enabled_sources(self) -> list[IngestSource]:
        return [s for s in self.sources.values() if s.enabled]


class SearchConfigError(ValueError):
    """Raised when search.yaml is missing, malformed, or semantically invalid."""


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise SearchConfigError(f"search.yaml is not valid YAML ({path}): {e}") from e
    except FileNotFoundError as e:
        raise SearchConfigError(f"search.yaml not found: {path}") from e
    if not isinstance(data, dict):
        raise SearchConfigError(f"search.yaml must be a mapping; got {type(data).__name__}")
    return data


def load_search_config(cfg_path: str | Path = DEFAULT_SEARCH_CFG) -> IngestConfig:
    """Parse search.yaml into an IngestConfig. Raises SearchConfigError loudly."""
    path = Path(cfg_path)
    raw = _load_yaml(path)

    raw_sources = raw.get("sources") or {}
    if not isinstance(raw_sources, dict):
        raise SearchConfigError("search.yaml 'sources' must be a mapping")

    sources: dict[str, IngestSource] = {}
    for name in KNOWN_SOURCES:
        block = raw_sources.get(name) or {}
        if not isinstance(block, dict):
            raise SearchConfigError(f"search.yaml sources.{name} must be a mapping")
        base_url = str(block.get("base_url") or "").strip()
        if not base_url:
            raise SearchConfigError(f"search.yaml sources.{name} is missing base_url")
        extras = {k: v for k, v in block.items() if k not in ("enabled", "base_url")}
        sources[name] = IngestSource(
            name=name,
            enabled=bool(block.get("enabled", False)),
            base_url=base_url,
            extras=extras,
        )

    filters = raw.get("filters") or {}
    if not isinstance(filters, dict):
        raise SearchConfigError("search.yaml 'filters' must be a mapping")

    max_age = filters.get("max_age_days")
    if max_age is None:
        max_age = 21
    try:
        max_age_days = int(max_age)
    except (TypeError, ValueError) as e:
        raise SearchConfigError(f"search.yaml filters.max_age_days must be int, got {max_age!r}") from e
    if max_age_days <= 0:
        raise SearchConfigError(f"search.yaml filters.max_age_days must be > 0, got {max_age_days}")

    dedupe_on = filters.get("dedupe_on") or ["title", "company"]
    if not isinstance(dedupe_on, list) or not all(isinstance(s, str) for s in dedupe_on):
        raise SearchConfigError("search.yaml filters.dedupe_on must be list[str]")

    return IngestConfig(sources=sources, max_age_days=max_age_days, dedupe_on=dedupe_on)
