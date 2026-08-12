"""Smoke tests for the tri-mode backend switch.

Covers AGENT / OLLAMA / CLOUD mode resolution via the shared lib pipeline.
End-to-end: Namespace → execution_config_from_namespace →
apply_backend_overrides → resolve_execution_mode.
"""

from __future__ import annotations

from ai_agent_core.execution import (
    execution_config_from_namespace,
    resolve_cloud_endpoint_and_key,
    resolve_execution_mode,
)
from ai_job_seeker.backend import apply_backend_overrides


def _make_ns(**overrides):
    defaults = dict(
        ollama_model="",
        ollama_url="http://localhost:11434",
        ollama_timeout_s=300.0,
        llm_provider="",
        llm_model="",
        llm_base_url="",
        llm_api_key="",
        llm_api_key_file="",
        llm_api_key_dir=str(
            __import__("pathlib").Path.home()
            / "Documents" / "__data" / "__cfg" / "api_key"
        ),
        llm_timeout_s=180.0,
        llm_temperature=0.0,
        llm_max_tokens=6000,
    )
    defaults.update(overrides)

    class NS:
        pass

    ns = NS()
    ns.__dict__.update(defaults)
    return ns


def _resolve_mode(**overrides):
    cfg = execution_config_from_namespace(_make_ns(**overrides))
    apply_backend_overrides(cfg)
    return resolve_execution_mode(cfg)


def test_mode_flags_agent():
    mode = _resolve_mode()
    assert mode.value == "agent"


def test_mode_flags_ollama():
    mode = _resolve_mode(ollama_model="qwen3.5:9b")
    assert mode.value == "ollama"


def test_mode_flags_cloud():
    mode = _resolve_mode(llm_provider="openrouter", llm_model="x")
    assert mode.value == "cloud"

    cfg = execution_config_from_namespace(
        _make_ns(llm_provider="openrouter", llm_model="x")
    )
    base_url, _ = resolve_cloud_endpoint_and_key(cfg.cloud)
    assert base_url == "https://openrouter.ai/api"
