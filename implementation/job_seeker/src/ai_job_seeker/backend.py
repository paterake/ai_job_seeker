"""Thin YAML → shared-lib bridge for backend.yaml.

Keeps < 100 lines; all heavy lifting defers to ai_agent_core.execution.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from ai_agent_core.execution.config import (
    ExecutionConfig,
    ExecutionConfigError,
)
from ai_agent_core.execution.parser import ArgDefaults

DEFAULT_BACKEND_CFG = "implementation/job_seeker/config/backend.yaml"


def _load_yaml(cfg_path: str | Path) -> dict[str, Any]:
    with open(cfg_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_backend_defaults(
    cfg_path: str | Path = DEFAULT_BACKEND_CFG,
) -> ArgDefaults:
    """Read backend.yaml and project-preferred ArgDefaults for the parser."""
    cfg = _load_yaml(cfg_path)
    local = cfg.get("local", {}) or {}
    cloud = cfg.get("cloud", {}) or {}
    return ArgDefaults(
        ollama_url=str(local.get("base_url") or ArgDefaults.ollama_url),
        ollama_timeout_s=float(local.get("timeout_s") or ArgDefaults.ollama_timeout_s),
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
