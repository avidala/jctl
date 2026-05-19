"""Tests for the on-disk completion cache + substring filter."""

import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import click

from jctl.utils.completion import (
    _CACHE_TTL_SECONDS,
    _cache_path,
    _read_cache,
    _write_cache,
    complete_job_name,
)


def _make_ctx() -> click.Context:
    """Click contexts for completion don't go through `cli()`, so we make a
    minimal one with `ctx.obj = {}` to match the production shape."""
    ctx = MagicMock(spec=click.Context)
    ctx.obj = {}
    return ctx


def test_cache_path_uses_jctl_config_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("JCTL_CONFIG_DIR", str(tmp_path))
    assert _cache_path() == tmp_path / "cache" / "jobs.json"


def test_write_then_read_round_trip(monkeypatch, tmp_path):
    monkeypatch.setenv("JCTL_CONFIG_DIR", str(tmp_path))
    _write_cache(["a/b", "c/d", "e"])
    assert _read_cache() == ["a/b", "c/d", "e"]


def test_stale_cache_returns_none(monkeypatch, tmp_path):
    monkeypatch.setenv("JCTL_CONFIG_DIR", str(tmp_path))
    path = _cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    # Write a cache that's older than the TTL.
    stale_ts = int(time.time()) - _CACHE_TTL_SECONDS - 10
    path.write_text(json.dumps({"timestamp": stale_ts, "jobs": ["x"]}))
    assert _read_cache() is None


def test_corrupt_cache_returns_none(monkeypatch, tmp_path):
    monkeypatch.setenv("JCTL_CONFIG_DIR", str(tmp_path))
    path = _cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("not json {")
    assert _read_cache() is None


def test_substring_match_finds_deeply_nested(monkeypatch, tmp_path):
    """The QA fixture lives at managed-cloud/MC-26.05.1/hamc-upgrade-environment.
    Typing `hamc` must surface it — `startswith` did not."""
    monkeypatch.setenv("JCTL_CONFIG_DIR", str(tmp_path))
    _write_cache(
        [
            "managed-cloud/MC-26.05.1/hamc-upgrade-environment",
            "managed-cloud/MC-26.05.1/hamc-env-cycling",
            "managed-cloud/other/unrelated-job",
        ]
    )
    suggestions = complete_job_name(_make_ctx(), MagicMock(), "hamc")
    assert sorted(suggestions) == [
        "managed-cloud/MC-26.05.1/hamc-env-cycling",
        "managed-cloud/MC-26.05.1/hamc-upgrade-environment",
    ]


def test_substring_match_is_case_insensitive(monkeypatch, tmp_path):
    monkeypatch.setenv("JCTL_CONFIG_DIR", str(tmp_path))
    _write_cache(["managed-cloud/Foo-Bar/JOB"])
    assert complete_job_name(_make_ctx(), MagicMock(), "foo-bar") == ["managed-cloud/Foo-Bar/JOB"]


def test_empty_incomplete_returns_all(monkeypatch, tmp_path):
    monkeypatch.setenv("JCTL_CONFIG_DIR", str(tmp_path))
    _write_cache(["a", "b", "c"])
    assert complete_job_name(_make_ctx(), MagicMock(), "") == ["a", "b", "c"]


@patch("jctl.utils.completion.get_jenkins_client_for_completion")
def test_cache_miss_populates_from_jenkins(mock_factory, monkeypatch, tmp_path):
    monkeypatch.setenv("JCTL_CONFIG_DIR", str(tmp_path))
    client = mock_factory.return_value
    client.get_jobs = AsyncMock(
        return_value=[
            {"fullName": "a/b", "name": "b"},
            {"fullName": "c", "name": "c"},
        ]
    )

    # No file yet → first call hits Jenkins and writes the cache.
    suggestions = complete_job_name(_make_ctx(), MagicMock(), "")
    assert suggestions == ["a/b", "c"]
    assert _cache_path().exists()

    # Second call should read from cache; mock the client to fail so we
    # prove we didn't go back to Jenkins.
    client.get_jobs = AsyncMock(side_effect=AssertionError("should not be called"))
    suggestions2 = complete_job_name(_make_ctx(), MagicMock(), "a")
    assert suggestions2 == ["a/b"]


@patch("jctl.utils.completion.get_jenkins_client_for_completion")
def test_no_client_means_silent_empty(mock_factory, monkeypatch, tmp_path):
    """Completion must never break the user's shell. No auth = no suggestions."""
    monkeypatch.setenv("JCTL_CONFIG_DIR", str(tmp_path))
    mock_factory.return_value = None
    assert complete_job_name(_make_ctx(), MagicMock(), "anything") == []
