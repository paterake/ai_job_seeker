"""The secret lookup root comes from backend.yaml, not the environment."""

from __future__ import annotations

from pathlib import Path

import pytest

from ai_job_seeker.secrets import _canonical_root


def test_root_read_from_config(tmp_path, monkeypatch):
    cfg = tmp_path / "backend.yaml"
    cfg.write_text(f'secrets:\n  apikey_root: "{tmp_path / "keys"}"\n', encoding="utf-8")
    monkeypatch.setenv("AI_JOB_SEEKER_APIKEY_ROOT", "/ignored")
    assert _canonical_root(cfg) == (tmp_path / "keys").resolve()


def test_root_expands_home(tmp_path):
    cfg = tmp_path / "backend.yaml"
    cfg.write_text('secrets:\n  apikey_root: "~/keys"\n', encoding="utf-8")
    assert _canonical_root(cfg) == (Path.home() / "keys").resolve()


def test_missing_root_is_an_error(tmp_path):
    cfg = tmp_path / "backend.yaml"
    cfg.write_text("default_mode: agent\n", encoding="utf-8")
    with pytest.raises(ValueError, match="secrets.apikey_root"):
        _canonical_root(cfg)


def test_committed_config_sets_root():
    assert _canonical_root().name == "apikey"
