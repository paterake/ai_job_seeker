"""Thin YAML → shared-lib bridge for backend.yaml.

Keeps < 200 lines; all heavy lifting defers to ai_agent_core.execution.
Also exposes profile-level defaults (cv_dir + expected stems) read from the
same YAML — keeps mechanism config in one file.

ai_agent_core imports are deliberately lazy in the two functions that actually
need it (load_backend_defaults / apply_backend_overrides) — the profile
defaults function (load_profile_defaults) has zero dependency on ai_agent_core
so profile/ingest keep working even when the ai_agent_core sibling checkout
is missing on disk.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from ai_agent_core.execution import (  # noqa: F401 — used lazily at runtime
        ArgDefaults,
        ExecutionConfig,
        ExecutionConfigError,
    )

_DEFAULT_BACKEND_CFG_REL = "implementation/job_seeker/config/backend.yaml"


def _resolve_workspace_relative(rel_path: str) -> Path:
    """Resolve a workspace-relative config path (works from any cwd)."""
    here = Path(__file__).resolve()
    raw_candidates: list[Path] = []
    for parent in [here, *here.parents][:7]:
        if (parent / "pyproject.toml").is_file():
            raw_candidates.append(parent)
    cwd = Path.cwd().resolve()
    for parent in [cwd, *cwd.parents][:7]:
        if (parent / "pyproject.toml").is_file() and parent not in raw_candidates:
            raw_candidates.append(parent)

    def _is_workspace_root(p: Path) -> bool:
        if (p / "ai_context").is_dir():
            return True
        target = (p / rel_path).resolve()
        if target.is_file():
            return True
        return False

    candidates = [p for p in raw_candidates if _is_workspace_root(p)]
    if not candidates:
        candidates = list(raw_candidates)
    for root in candidates:
        target = (root / rel_path).resolve()
        if target.is_file():
            return target
    return (Path(candidates[0]) / rel_path).resolve() if candidates else Path(rel_path).resolve()


DEFAULT_BACKEND_CFG = str(_resolve_workspace_relative(_DEFAULT_BACKEND_CFG_REL))


@dataclass(frozen=True)
class ProfileDefaults:
    """Default CV locations resolved from backend.yaml profile section.

    cv_dir is resolved verbatim — if absolute (recommended) it stays absolute;
    if relative it's interpreted relative to the workspace root.
    """

    cv_dir: Path
    cv_docx: Path
    cv_pdf: Path

    def with_existing_docx(self) -> Path | None:
        """Return cv_docx if it exists on disk, else the first *.docx in cv_dir.

        Never raises — returns None if neither the named file nor any *.docx
        exists inside cv_dir. Callers decide whether to error loudly.
        """
        if self.cv_docx.is_file():
            return self.cv_docx
        if self.cv_dir.is_dir():
            for cand in sorted(self.cv_dir.glob("*.docx")):
                if cand.is_file():
                    return cand
        return None

    def with_existing_pdf(self) -> Path | None:
        """Same shape as with_existing_docx but for the PDF copy."""
        if self.cv_pdf.is_file():
            return self.cv_pdf
        if self.cv_dir.is_dir():
            for cand in sorted(self.cv_dir.glob("*.pdf")):
                if cand.is_file():
                    return cand
        return None


def _load_yaml(cfg_path: str | Path) -> dict[str, Any]:
    with open(cfg_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_backend_defaults(
    cfg_path: str | Path = DEFAULT_BACKEND_CFG,
) -> Any:
    """Read backend.yaml and project-preferred ArgDefaults for the parser.

    ai_agent_core.execution is imported lazily — this is only called while
    building the match/draft subparsers, never by profile or ingest.
    """
    try:
        from ai_agent_core.execution import ArgDefaults
    except ImportError as e:
        raise ImportError(
            "ai_agent_core.execution.ArgDefaults is unavailable — needed only "
            "to build the match/draft CLI subparsers (they carry LLM-mode "
            "flags). Clone/checkout ai_agent_core next to ai_job_seeker at "
            "../ai_agent_core/ or install as a released package. Profile and "
            "ingest commands work without ai_agent_core."
        ) from e

    cfg = _load_yaml(cfg_path)
    local = cfg.get("local", {}) or {}
    return ArgDefaults(
        ollama_url=str(local.get("base_url") or ArgDefaults.ollama_url),
        ollama_timeout_s=float(local.get("timeout_s") or ArgDefaults.ollama_timeout_s),
    )


def load_profile_defaults(
    cfg_path: str | Path = DEFAULT_BACKEND_CFG,
    workspace_root: str | Path | None = None,
) -> ProfileDefaults:
    """Return profile defaults (cv_dir + named docx/pdf paths) from YAML.

    cv_dir may be absolute or workspace-relative; when relative it is resolved
    against workspace_root (defaults to cfg_path's great-great-grandparent, i.e.
    the workspace root for the canonical config path).
    """
    raw = _load_yaml(cfg_path)
    profile = raw.get("profile", {}) or {}

    cv_dir_str = str(profile.get("cv_dir") or "").strip()
    stem_docx = str(profile.get("cv_docx_stem") or "").strip() or "CV"
    stem_pdf = str(profile.get("cv_pdf_stem") or "").strip() or "CV"

    cfg_abs = Path(cfg_path).resolve()
    if workspace_root is None:
        workspace_root = cfg_abs.parents[3]
    root = Path(workspace_root).resolve()

    if cv_dir_str:
        cv_dir = Path(cv_dir_str)
    else:
        cv_dir = root / "implementation" / "job_seeker" / "config" / "profile"
    if not cv_dir.is_absolute():
        cv_dir = (root / cv_dir).resolve()

    return ProfileDefaults(
        cv_dir=cv_dir,
        cv_docx=cv_dir / f"{stem_docx}.docx",
        cv_pdf=cv_dir / f"{stem_pdf}.pdf",
    )


def apply_backend_overrides(
    cfg: Any,
    cfg_path: str | Path = DEFAULT_BACKEND_CFG,
) -> Any:
    """Merge backend.yaml intent into an already-built ExecutionConfig.

    Only fills fields the CLI left empty. Preserves the "never default cloud"
    invariant: cloud is filled only when backend.yaml already has BOTH
    provider AND model. If YAML has one without the other, raises
    ExecutionConfigError loudly instead of silently proceeding.

    ai_agent_core.execution types are imported lazily — this is only called
    by match/draft after they've already imported the core successfully.
    """
    try:
        from ai_agent_core.execution import ExecutionConfigError
    except ImportError as e:
        raise ImportError(
            "ai_agent_core.execution.ExecutionConfigError unavailable — "
            "apply_backend_overrides needs ai_agent_core on the import path."
        ) from e

    raw = _load_yaml(cfg_path)
    default_mode = str(raw.get("default_mode") or "agent").strip().lower()
    local = raw.get("local", {}) or {}
    cloud = raw.get("cloud", {}) or {}

    local_model = str(local.get("model") or "").strip()
    if default_mode == "local" and local_model and not getattr(cfg.ollama, "model", ""):
        cfg.ollama.model = local_model

    cloud_provider = str(cloud.get("provider") or "").strip()
    cloud_model = str(cloud.get("model") or "").strip()
    if bool(cloud_provider) ^ bool(cloud_model):
        raise ExecutionConfigError(
            "backend.yaml cloud section is incomplete: set BOTH provider AND model, "
            "or leave both empty (cloud is opt-in only). "
            f"Got provider={cloud_provider!r} model={cloud_model!r}."
        )
    if cloud_provider and cloud_model:
        if not cfg.cloud.provider:
            cfg.cloud.provider = cloud_provider
        if not cfg.cloud.model:
            cfg.cloud.model = cloud_model

    return cfg
