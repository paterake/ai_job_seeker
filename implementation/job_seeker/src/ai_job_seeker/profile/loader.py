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


def save_profile(profile: dict[str, Any], path: str | Path, *, overwrite: bool = False) -> Path:
    """Write a profile dict to YAML at ``path``, creating parent dirs.

    - Uses yaml.safe_dump with sort_keys=False so sections keep the order we
      wrote them in (identity → summary → skills → experience → education →
      … → target — easy to review).
    - Refuses to overwrite unless overwrite=True (guard against clobbering a
      hand-edited profile YAML by accident).
    - Creates the parent directory with 0o700 perms — profile files are PII,
      gitignored, and should not be world-readable.
    """
    p = Path(path)
    if p.exists() and not overwrite:
        raise ProfileError(
            f"Refusing to overwrite existing profile: {p}. "
            "Pass overwrite=True to regenerate."
        )
    p.parent.mkdir(parents=True, exist_ok=True)
    try:
        import os as _os
        _os.chmod(p.parent, 0o700)
    except OSError:
        pass

    dumped = yaml.safe_dump(profile, sort_keys=False, allow_unicode=True, width=120)
    p.write_text(dumped, encoding="utf-8")
    try:
        import os as _os
        _os.chmod(p, 0o600)
    except OSError:
        pass
    return p
