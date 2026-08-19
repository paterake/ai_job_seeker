"""Canonical secret sources for the ai_job_seeker pipeline.

Two ordered sources, first hit wins:
  1. $HOME/Documents/__cfg/apikey/<service>/<filename>  (preferred — lives
     outside the repo, PII/secret-safe, reusable across repos)
  2. environment variable (fallback — via .env, gitignored at repo root)

Secrets are NEVER hard-coded or returned in error messages that might leak
into logs. Failures raise typed exceptions with a remediation hint (file path
or env var name the user can populate).

The canonical on-disk layout inside ~/Documents/__cfg/apikey/ is:

  __cfg/apikey/
    adzuna/
      app_id
      app_key
    reed/
      api_key
    themuse/
      api_key          # optional — The Muse works keyless (rate-limited)
"""

from __future__ import annotations

import os
from pathlib import Path

CANONICAL_ROOT_ENV = "AI_JOB_SEEKER_APIKEY_ROOT"
CANONICAL_ROOT_DEFAULT = "~/Documents/__cfg/apikey"


class SecretNotFound(RuntimeError):
    """Raised when a required secret is missing from BOTH canonical sources."""


def _canonical_root() -> Path:
    override = os.environ.get(CANONICAL_ROOT_ENV, "").strip()
    base = Path(override) if override else Path(CANONICAL_ROOT_DEFAULT)
    return base.expanduser().resolve()


def _read_file_secret(service: str, filename: str) -> str | None:
    p = _canonical_root() / service / filename
    if not p.is_file():
        return None
    try:
        data = p.read_text(encoding="utf-8")
    except OSError:
        return None
    value = data.strip()
    return value or None


def _read_env_secret(env_var: str) -> str | None:
    value = os.environ.get(env_var, "").strip()
    return value or None


def require_secret(
    service: str,
    filename: str,
    env_var: str,
    *,
    optional: bool = False,
) -> str | None:
    """Return a secret from canonical file, else env. If required and missing,
    raise SecretNotFound with a remediation hint.

    When optional=True, returns None if both sources are empty instead of
    raising (used for keys that enable elevated quotas but aren't required,
    e.g. The Muse API key).
    """
    from_file = _read_file_secret(service, filename)
    if from_file:
        return from_file
    from_env = _read_env_secret(env_var)
    if from_env:
        return from_env
    if optional:
        return None
    file_path = _canonical_root() / service / filename
    raise SecretNotFound(
        f"Missing secret for service={service!r} key={filename!r}. "
        f"Populate either:\n"
        f"  - file: {file_path}\n"
        f"  - env : export {env_var}=<value>\n"
        f"Both sources checked; neither had a non-empty value."
    )
