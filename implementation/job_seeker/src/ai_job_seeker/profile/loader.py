"""Load and validate a candidate profile YAML.

The profile is the single source of truth the pipeline matches and drafts
against. It is PII and lives under the gitignored config/profile/ directory.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REQUIRED_KEYS = ("identity", "target", "summary", "skills", "experience")


class ProfileError(ValueError):
    """Raised when a profile file is missing, unreadable, or incomplete."""


def load_profile(path: str | Path) -> dict[str, Any]:
    """Read a profile YAML and return it as a dict, validating required keys.

    Raises ProfileError with an actionable message rather than returning a
    partial profile — a silently incomplete profile produces bad matches and
    fabricated-looking drafts downstream.
    """
    p = Path(path)
    if not p.is_file():
        raise ProfileError(f"Profile not found: {p}")

    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise ProfileError(f"Profile is not valid YAML ({p}): {e}") from e

    if not isinstance(data, dict):
        raise ProfileError(f"Profile must be a YAML mapping; got {type(data).__name__} ({p})")

    missing = [k for k in REQUIRED_KEYS if k not in data or data[k] in (None, "", [])]
    if missing:
        raise ProfileError(f"Profile {p} is missing required fields: {', '.join(missing)}")

    return data
