"""Thin YAML → shared-lib bridge for backend.yaml.

Keeps < 150 lines; all heavy lifting defers to ai_agent_core.execution.
Also exposes profile-level defaults (cv_dir + expected stems) read from the
same YAML — keeps mechanism config in one file.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from ai_agent_core.execution import (
    ArgDefaults,
    ExecutionConfig,
    ExecutionConfigError,
)

DEFAULT_BACKEND_CFG = "implementation/job_seeker/config/backend.yaml"


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
) -> ArgDefaults:
    """Read backend.yaml and project-preferred ArgDefaults for the parser."""
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
    cfg: ExecutionConfig,
    cfg_path: str | Path = DEFAULT_BACKEND_CFG,
) -> ExecutionConfig:
    """Merge backend.yaml intent into an already-built ExecutionConfig.

    Only fills fields the CLI left empty. Preserves the "never default cloud"
    invariant: cloud is filled only when backend.yaml already has BOTH
    provider AND model. If YAML has one without the other, raises
    ExecutionConfigError loudly instead of silently proceeding.
    """
    raw = _load_yaml(cfg_path)
    default_mode = str(raw.get("default_mode") or "agent").strip().lower()
    local = raw.get("local", {}) or {}
    cloud = raw.get("cloud", {}) or {}

    local_model = str(local.get("model") or "").strip()
    if default_mode == "local" and local_model and not cfg.ollama.model:
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
