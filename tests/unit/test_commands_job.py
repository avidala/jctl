"""Tests for `jctl job` (trigger / logs).

Coverage push: commands/job.py was 17% before this file. We mock
`get_jenkins_client` so the tests never reach a real Jenkins.
"""

import json
import re
from unittest.mock import AsyncMock, MagicMock, patch

import yaml
from click.testing import CliRunner

from jctl.cli import cli
from jctl.constants import EXIT_JENKINS_API_ERROR


def _runner() -> CliRunner:
    return CliRunner()


# --- trigger -------------------------------------------------------------


@patch("jctl.commands.job.get_jenkins_client")
def test_trigger_dry_run_does_not_call_jenkins(mock_factory):
    """--dry-run prints the plan and returns before touching the client."""
    result = _runner().invoke(cli, ["job", "trigger", "--dry-run", "some/job"])
    assert result.exit_code == 0
    assert "Dry run" in result.output
    # `get_jenkins_client` should not be invoked at all.
    mock_factory.assert_not_called()


@patch("jctl.commands.job.get_jenkins_client")
def test_trigger_with_params_parses_kv(mock_factory):
    """--param key=value pairs are split and shown back to the user."""
    mock_client = mock_factory.return_value
    mock_client.trigger_job = MagicMock(return_value=42)

    result = _runner().invoke(
        cli,
        ["job", "trigger", "deploy/app", "-p", "env=prod", "-p", "version=1.2.3"],
    )
    assert result.exit_code == 0, result.output
    assert "env = prod" in result.output
    assert "version = 1.2.3" in result.output
    mock_client.trigger_job.assert_called_once_with(
        "deploy/app", {"env": "prod", "version": "1.2.3"}
    )
    assert "Job triggered successfully" in result.output


@patch("jctl.commands.job.get_jenkins_client")
def test_trigger_no_params_passes_none(mock_factory):
    """Without -p, trigger_job receives None (not an empty dict) so
    python-jenkins picks its default-args codepath."""
    mock_client = mock_factory.return_value
    mock_client.trigger_job = MagicMock(return_value=7)

    result = _runner().invoke(cli, ["job", "trigger", "deploy/app"])
    assert result.exit_code == 0
    mock_client.trigger_job.assert_called_once_with("deploy/app", None)


@patch("jctl.commands.job.get_jenkins_client")
def test_trigger_jenkins_failure_exits_4(mock_factory):
    mock_client = mock_factory.return_value
    mock_client.trigger_job = MagicMock(side_effect=RuntimeError("Jenkins is down"))

    result = _runner().invoke(cli, ["job", "trigger", "x"])
    assert result.exit_code == EXIT_JENKINS_API_ERROR
    assert "Error triggering job" in result.output


# --- logs ----------------------------------------------------------------


@patch("jctl.commands.job.get_jenkins_client")
def test_logs_explicit_build_number(mock_factory):
    """`job logs <name> <build>` skips the lookup and goes straight to fetch."""
    mock_client = mock_factory.return_value
    mock_client.get_build_log = AsyncMock(return_value="hello world\nsecond line\n")

    result = _runner().invoke(cli, ["job", "logs", "deploy/app", "42"])
    assert result.exit_code == 0
    assert "hello world" in result.output
    mock_client.get_build_log.assert_awaited_once_with("deploy/app", 42)


@patch("jctl.commands.job.get_jenkins_client")
def test_logs_no_build_number_uses_latest(mock_factory):
    """Without a build #, we scan `get_jobs()` and pick `lastBuild.number`."""
    mock_client = mock_factory.return_value
    mock_client.get_jobs = AsyncMock(
        return_value=[
            {"fullName": "other/job", "lastBuild": {"number": 1}},
            {"fullName": "deploy/app", "lastBuild": {"number": 99}},
        ]
    )
    mock_client.get_build_log = AsyncMock(return_value="log body")

    result = _runner().invoke(cli, ["job", "logs", "deploy/app"])
    assert result.exit_code == 0
    assert "Using latest build #99" in result.output
    mock_client.get_build_log.assert_awaited_once_with("deploy/app", 99)


@patch("jctl.commands.job.get_jenkins_client")
def test_logs_no_build_number_unknown_job_exits_4(mock_factory):
    mock_client = mock_factory.return_value
    mock_client.get_jobs = AsyncMock(return_value=[])

    result = _runner().invoke(cli, ["job", "logs", "missing/job"])
    assert result.exit_code == EXIT_JENKINS_API_ERROR
    assert "Job 'missing/job' not found" in result.output


@patch("jctl.commands.job.get_jenkins_client")
def test_logs_no_build_number_job_has_no_builds_exits_4(mock_factory):
    mock_client = mock_factory.return_value
    mock_client.get_jobs = AsyncMock(return_value=[{"fullName": "deploy/app", "lastBuild": None}])

    result = _runner().invoke(cli, ["job", "logs", "deploy/app"])
    assert result.exit_code == EXIT_JENKINS_API_ERROR
    assert "No builds found" in result.output


@patch("jctl.commands.job.get_jenkins_client")
def test_logs_output_json_is_parsable(mock_factory):
    """--output json wraps the log in {job, build_number, log}."""
    mock_client = mock_factory.return_value
    mock_client.get_build_log = AsyncMock(return_value="line1\nline2\n")

    result = _runner().invoke(cli, ["--output", "json", "job", "logs", "deploy/app", "5"])
    assert result.exit_code == 0
    payload = json.loads(re.search(r"\{.*\}", result.output, re.DOTALL).group(0))
    assert payload["job"] == "deploy/app"
    assert payload["build_number"] == 5
    assert "line1" in payload["log"]


@patch("jctl.commands.job.get_jenkins_client")
def test_logs_output_yaml_is_parsable(mock_factory):
    mock_client = mock_factory.return_value
    mock_client.get_build_log = AsyncMock(return_value="log body")

    result = _runner().invoke(cli, ["--output", "yaml", "job", "logs", "x", "1"])
    assert result.exit_code == 0
    payload = yaml.safe_load(result.output)
    assert payload["job"] == "x"
    assert payload["log"] == "log body"


@patch("jctl.commands.job.get_jenkins_client")
def test_logs_output_plain_is_raw_text(mock_factory):
    """plain emits raw log content, no 'Logs for:' header — so the output
    is directly tailable / greppable."""
    mock_client = mock_factory.return_value
    mock_client.get_build_log = AsyncMock(return_value="line1\nline2\n")

    result = _runner().invoke(cli, ["--output", "plain", "job", "logs", "x", "1"])
    assert result.exit_code == 0
    assert "Logs for:" not in result.output
    assert "line1" in result.output


@patch("jctl.commands.job.get_jenkins_client")
def test_logs_fetch_failure_exits_4(mock_factory):
    mock_client = mock_factory.return_value
    mock_client.get_build_log = AsyncMock(side_effect=RuntimeError("network down"))

    result = _runner().invoke(cli, ["job", "logs", "x", "1"])
    assert result.exit_code == EXIT_JENKINS_API_ERROR
    assert "Error fetching logs" in result.output
