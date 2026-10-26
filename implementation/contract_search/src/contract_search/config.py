"""Load and validate the scoring policy and the candidate profile.

Both files are project-owned config: each loader names its key surface and
fails on an undeclared or missing key (code-architecture.md → Config Purity).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"
DEFAULT_SCORING_CFG = CONFIG_DIR / "scoring.yaml"
DEFAULT_SEARCH_CFG = CONFIG_DIR / "search.yaml"
PROFILE_DIR = CONFIG_DIR / "profile"
DEFAULT_OUTPUT_DIR = CONFIG_DIR / "output"


class ConfigError(ValueError):
    pass


def default_profile_path(profile_dir: Path = PROFILE_DIR) -> Path:
    """The single candidate profile in the profile folder; anything else is ambiguous."""
    found = sorted(profile_dir.glob("*.yaml")) if profile_dir.is_dir() else []
    if len(found) != 1:
        raise ConfigError(f"expected exactly one profile YAML in {profile_dir}, found {len(found)}; pass --profile")
    return found[0]


_SCORING_KEYS = {
    "require_contract": bool,
    "blocked_contract_types": list,
    "contract_patterns": list,
    "day_rate_pattern": str,
    "contract_title_patterns": list,
    "ir35_outside_patterns": list,
    "ir35_inside_patterns": list,
    "remote_patterns": list,
    "remote_modes": list,
    "remote_modes_without_location_pass": list,
    "blocked_title_phrases": list,
    "seniority_phrases": list,
    "weights": dict,
}
_WEIGHT_KEYS = {
    "title_max", "ir35_outside", "ir35_inside", "remote", "in_target_location",
    "seniority", "skills_per_match", "skills_max", "fresh", "day_rate_stated",
}
_PROFILE_KEYS = {"identity", "target", "skills", "summary"}
_TARGET_KEYS = {"queries", "title_weights", "locations", "remote"}


@dataclass(frozen=True)
class Scoring:
    require_contract: bool
    blocked_contract_types: frozenset[str]
    contract_patterns: tuple[re.Pattern, ...]
    day_rate: re.Pattern
    contract_title_patterns: tuple[re.Pattern, ...]
    ir35_outside: tuple[re.Pattern, ...]
    ir35_inside: tuple[re.Pattern, ...]
    remote: tuple[re.Pattern, ...]
    remote_modes: frozenset[str]
    remote_modes_without_location_pass: frozenset[str]
    blocked_title_phrases: tuple[str, ...]
    seniority_phrases: tuple[str, ...]
    weights: dict[str, int]


@dataclass(frozen=True)
class Profile:
    name: str
    queries: tuple[str, ...]
    title_weights: dict[str, int]
    locations: tuple[str, ...]
    remote: str
    skills: tuple[str, ...]


def _read_mapping(path: Path) -> dict[str, Any]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as e:
        raise ConfigError(f"cannot read {path}: {e}") from e
    if not isinstance(raw, dict):
        raise ConfigError(f"{path}: top level must be a mapping")
    return raw


def _check_keys(where: str, raw: dict, allowed: set[str], required: set[str]) -> None:
    extra = set(raw) - allowed
    missing = required - set(raw)
    if extra:
        raise ConfigError(f"{where}: undeclared key(s) {sorted(extra)}")
    if missing:
        raise ConfigError(f"{where}: missing key(s) {sorted(missing)}")


def _patterns(where: str, values: list) -> tuple[re.Pattern, ...]:
    out = []
    for v in values:
        try:
            out.append(re.compile(str(v), re.IGNORECASE))
        except re.error as e:
            raise ConfigError(f"{where}: bad regex {v!r}: {e}") from e
    return tuple(out)


def load_scoring(path: str | Path = DEFAULT_SCORING_CFG) -> Scoring:
    path = Path(path)
    raw = _read_mapping(path)
    keys = set(_SCORING_KEYS)
    _check_keys(str(path), raw, keys, keys)
    for k, typ in _SCORING_KEYS.items():
        if not isinstance(raw[k], typ):
            raise ConfigError(f"{path}: {k} must be {typ.__name__}")
    weights = raw["weights"]
    _check_keys(f"{path} weights", weights, _WEIGHT_KEYS, _WEIGHT_KEYS)
    if not all(isinstance(v, int) and not isinstance(v, bool) for v in weights.values()):
        raise ConfigError(f"{path}: every weight must be an int")
    return Scoring(
        require_contract=raw["require_contract"],
        blocked_contract_types=frozenset(str(x).lower() for x in raw["blocked_contract_types"]),
        contract_patterns=_patterns("contract_patterns", raw["contract_patterns"]),
        day_rate=_patterns("day_rate_pattern", [raw["day_rate_pattern"]])[0],
        contract_title_patterns=_patterns("contract_title_patterns", raw["contract_title_patterns"]),
        ir35_outside=_patterns("ir35_outside_patterns", raw["ir35_outside_patterns"]),
        ir35_inside=_patterns("ir35_inside_patterns", raw["ir35_inside_patterns"]),
        remote=_patterns("remote_patterns", raw["remote_patterns"]),
        remote_modes=frozenset(str(x) for x in raw["remote_modes"]),
        remote_modes_without_location_pass=frozenset(str(x) for x in raw["remote_modes_without_location_pass"]),
        blocked_title_phrases=tuple(str(x).lower() for x in raw["blocked_title_phrases"]),
        seniority_phrases=tuple(str(x).lower() for x in raw["seniority_phrases"]),
        weights=dict(weights),
    )


def load_profile(path: str | Path | None = None) -> Profile:
    path = Path(path) if path else default_profile_path()
    raw = _read_mapping(path)
    _check_keys(str(path), raw, _PROFILE_KEYS, _PROFILE_KEYS - {"summary"})
    target = raw["target"]
    if not isinstance(target, dict):
        raise ConfigError(f"{path}: target must be a mapping")
    _check_keys(f"{path} target", target, _TARGET_KEYS, _TARGET_KEYS)
    weights = target["title_weights"]
    if not isinstance(weights, dict) or not weights:
        raise ConfigError(f"{path}: target.title_weights must be a non-empty mapping")
    if not all(isinstance(v, int) and 0 < v <= 100 for v in weights.values()):
        raise ConfigError(f"{path}: target.title_weights values must be ints in 1..100")
    queries = target["queries"]
    if not isinstance(queries, list) or not queries:
        raise ConfigError(f"{path}: target.queries must be a non-empty list")
    skills = raw["skills"]
    if not isinstance(skills, list) or not skills:
        raise ConfigError(f"{path}: skills must be a non-empty list")
    identity = raw["identity"]
    if not isinstance(identity, dict) or not str(identity.get("name") or "").strip():
        raise ConfigError(f"{path}: identity.name is required")
    return Profile(
        name=str(identity["name"]).strip(),
        queries=tuple(str(q).strip() for q in queries if str(q).strip()),
        title_weights={str(k).lower(): v for k, v in weights.items()},
        locations=tuple(str(x).lower() for x in (target["locations"] or [])),
        remote=str(target["remote"]),
        skills=tuple(str(s).lower() for s in skills),
    )
