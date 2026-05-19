"""Verify `pipeline list` sorts by recency (freshest first), with NO_BUILDS
rows at the bottom. The previous behavior was the Jenkins-API alphabetical
order, which buried recent active pipelines under a heap of NO_BUILDS rows."""

from unittest.mock import AsyncMock, patch

from click.testing import CliRunner

from jctl.cli import cli


def _make_job(name: str, timestamp_ms: int | None, result: str | None = "SUCCESS") -> dict:
    """Build a Jenkins-shape job dict matching what get_jobs() returns."""
    if timestamp_ms is None:
        return {"fullName": name, "name": name}
    return {
        "fullName": name,
        "name": name,
        "lastBuild": {
            "number": 1,
            "result": result,
            "timestamp": timestamp_ms,
            "duration": 60_000,
        },
    }


@patch("jctl.commands.pipeline.get_jenkins_client")
def test_list_orders_by_lastbuild_desc_with_no_builds_last(mock_factory, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("JCTL_CONFIG_DIR", str(tmp_path / ".jctl"))
    # Bypass auth + provide a deterministic job set.
    mock_client = mock_factory.return_value
    mock_client.get_jobs = AsyncMock(
        return_value=[
            _make_job("z-old", 1_700_000_000_000),  # oldest with builds
            _make_job("a-no-builds", None),  # NO_BUILDS — alphabetically first
            _make_job("m-newest", 1_800_000_000_000),  # newest
            _make_job("b-middle", 1_750_000_000_000),
        ]
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["--output", "json", "pipeline", "list"], catch_exceptions=False)
    assert result.exit_code == 0, result.output

    import json
    import re

    # `pipeline list --output json` prints the count to stderr and JSON
    # to stdout; CliRunner combines them, so extract the JSON array.
    match = re.search(r"\[.*\]", result.output, re.DOTALL)
    assert match, result.output
    rows = json.loads(match.group(0))

    names_in_order = [r["name"] for r in rows]
    # Most recent first, NO_BUILDS last:
    assert names_in_order == ["m-newest", "b-middle", "z-old", "a-no-builds"], names_in_order

    # The internal sort-key must be stripped before output.
    assert "_ts" not in rows[0]
