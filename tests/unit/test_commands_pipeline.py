"""Tests for `jctl pipeline` (describe / logs / run / list extras / cancel
extras).

`list` and `cancel` already have dedicated test files
(`test_pipeline_list_sort.py`, `test_sync_retry_and_cancel.py`); this file
fills in the gaps for `describe`, `logs`, and `run` (without --wait so
we don't have to mock long-poll loops).

Coverage push: commands/pipeline.py was 24% before this file.
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


# --- describe ------------------------------------------------------------


@patch("jctl.commands.pipeline.get_jenkins_client")
def test_describe_table_with_stages(mock_factory):
    """Happy path: workflow API returns stages → table mode renders them."""
    mock_client = mock_factory.return_value
    mock_client.get_build_info = AsyncMock(
        return_value={"result": "SUCCESS", "duration": 100_000, "timestamp": 1, "url": "u"}
    )
    mock_client.get_workflow_info = AsyncMock(
        return_value={
            "stages": [
                {"name": "Build", "status": "SUCCESS", "durationMillis": 5000},
                {"name": "Test", "status": "SUCCESS", "durationMillis": 12_000},
            ]
        }
    )

    result = _runner().invoke(cli, ["pipeline", "describe", "deploy/app", "1"])
    assert result.exit_code == 0, result.output
    assert "Build" in result.output
    assert "Test" in result.output
    assert "SUCCESS" in result.output


@patch("jctl.commands.pipeline.get_jenkins_client")
def test_describe_table_without_workflow_api(mock_factory):
    """If wfapi is missing (non-pipeline job), we still print the build
    summary without stages."""
    mock_client = mock_factory.return_value
    mock_client.get_build_info = AsyncMock(
        return_value={"result": "SUCCESS", "duration": 100, "timestamp": 1, "url": "u"}
    )
    mock_client.get_workflow_info = AsyncMock(side_effect=RuntimeError("no wfapi"))

    result = _runner().invoke(cli, ["pipeline", "describe", "deploy/app", "1"])
    assert result.exit_code == 0
    assert "Overall Status" in result.output
    # Stage table header isn't rendered when there's no workflow info.
    assert "Pipeline Stages" not in result.output


@patch("jctl.commands.pipeline.get_jenkins_client")
def test_describe_json_includes_stages(mock_factory):
    mock_client = mock_factory.return_value
    mock_client.get_build_info = AsyncMock(
        return_value={
            "result": "FAILURE",
            "duration": 60_000,
            "timestamp": 17_000_000,
            "url": "https://j/x/1",
        }
    )
    mock_client.get_workflow_info = AsyncMock(
        return_value={"stages": [{"name": "Build", "status": "FAILED", "durationMillis": 999}]}
    )

    result = _runner().invoke(cli, ["--output", "json", "pipeline", "describe", "x", "1"])
    assert result.exit_code == 0
    payload = json.loads(re.search(r"\{.*\}", result.output, re.DOTALL).group(0))
    assert payload["job"] == "x"
    assert payload["result"] == "FAILURE"
    assert payload["duration_ms"] == 60_000
    assert len(payload["stages"]) == 1
    assert payload["stages"][0]["name"] == "Build"


@patch("jctl.commands.pipeline.get_jenkins_client")
def test_describe_yaml_round_trips(mock_factory):
    mock_client = mock_factory.return_value
    mock_client.get_build_info = AsyncMock(
        return_value={"result": "SUCCESS", "duration": 100, "timestamp": 1, "url": "u"}
    )
    mock_client.get_workflow_info = AsyncMock(return_value={"stages": []})

    result = _runner().invoke(cli, ["--output", "yaml", "pipeline", "describe", "x", "1"])
    assert result.exit_code == 0
    payload = yaml.safe_load(result.output)
    assert payload["result"] == "SUCCESS"


@patch("jctl.commands.pipeline.get_jenkins_client")
def test_describe_404_exits_4(mock_factory):
    mock_client = mock_factory.return_value
    mock_client.get_build_info = AsyncMock(side_effect=RuntimeError("404 Not Found"))

    result = _runner().invoke(cli, ["pipeline", "describe", "x", "99999"])
    assert result.exit_code == EXIT_JENKINS_API_ERROR


@patch("jctl.commands.pipeline.get_jenkins_client")
def test_describe_without_build_uses_latest(mock_factory):
    """`pipeline describe JOB` (no build) resolves lastBuild and proceeds."""
    mock_client = mock_factory.return_value
    mock_client.get_jobs = AsyncMock(
        return_value=[{"fullName": "x", "name": "x", "lastBuild": {"number": 7}}]
    )
    mock_client.get_build_info = AsyncMock(
        return_value={"result": "SUCCESS", "duration": 1000, "timestamp": 1, "url": "u"}
    )
    mock_client.get_workflow_info = AsyncMock(return_value={"stages": []})

    result = _runner().invoke(cli, ["pipeline", "describe", "x"])
    assert result.exit_code == 0, result.output
    assert "Using latest build #7" in result.output
    mock_client.get_build_info.assert_awaited_once_with("x", 7)


@patch("jctl.commands.pipeline.get_jenkins_client")
def test_describe_without_build_pipeline_not_found_exits_4(mock_factory):
    mock_client = mock_factory.return_value
    mock_client.get_jobs = AsyncMock(return_value=[])

    result = _runner().invoke(cli, ["pipeline", "describe", "missing/x"])
    assert result.exit_code == EXIT_JENKINS_API_ERROR
    assert "Pipeline 'missing/x' not found" in result.output


@patch("jctl.commands.pipeline.get_jenkins_client")
def test_describe_without_build_no_builds_exits_4(mock_factory):
    mock_client = mock_factory.return_value
    mock_client.get_jobs = AsyncMock(
        return_value=[{"fullName": "x", "name": "x", "lastBuild": None}]
    )

    result = _runner().invoke(cli, ["pipeline", "describe", "x"])
    assert result.exit_code == EXIT_JENKINS_API_ERROR
    assert "No builds found" in result.output


# --- logs ----------------------------------------------------------------


@patch("jctl.commands.pipeline.get_jenkins_client")
def test_logs_explicit_build_number(mock_factory):
    mock_client = mock_factory.return_value
    mock_client.get_build_log = AsyncMock(return_value="log body line\n")

    result = _runner().invoke(cli, ["pipeline", "logs", "x", "1"])
    assert result.exit_code == 0
    assert "log body line" in result.output


@patch("jctl.commands.pipeline.get_jenkins_client")
def test_logs_latest_via_get_jobs(mock_factory):
    """Without a build #, we look up the job in `get_jobs()` and use
    `lastBuild.number`."""
    mock_client = mock_factory.return_value
    mock_client.get_jobs = AsyncMock(
        return_value=[{"fullName": "x", "name": "x", "lastBuild": {"number": 42}}]
    )
    mock_client.get_build_log = AsyncMock(return_value="log body")

    result = _runner().invoke(cli, ["pipeline", "logs", "x"])
    assert result.exit_code == 0
    assert "Using latest build #42" in result.output


@patch("jctl.commands.pipeline.get_jenkins_client")
def test_logs_pipeline_not_found_exits_4(mock_factory):
    mock_client = mock_factory.return_value
    mock_client.get_jobs = AsyncMock(return_value=[])

    result = _runner().invoke(cli, ["pipeline", "logs", "missing/pipeline"])
    assert result.exit_code == EXIT_JENKINS_API_ERROR
    assert "Pipeline 'missing/pipeline' not found" in result.output


@patch("jctl.commands.pipeline.get_jenkins_client")
def test_logs_output_json(mock_factory):
    mock_client = mock_factory.return_value
    mock_client.get_build_log = AsyncMock(return_value="body")

    result = _runner().invoke(cli, ["--output", "json", "pipeline", "logs", "x", "1"])
    assert result.exit_code == 0
    payload = json.loads(re.search(r"\{.*\}", result.output, re.DOTALL).group(0))
    assert payload["build_number"] == 1
    assert payload["log"] == "body"


@patch("jctl.commands.pipeline.get_jenkins_client")
def test_logs_output_plain_is_raw(mock_factory):
    mock_client = mock_factory.return_value
    mock_client.get_build_log = AsyncMock(return_value="abc\ndef\n")

    result = _runner().invoke(cli, ["--output", "plain", "pipeline", "logs", "x", "1"])
    assert result.exit_code == 0
    assert "Logs for:" not in result.output
    assert "abc" in result.output


# --- run -----------------------------------------------------------------


@patch("jctl.commands.pipeline.get_jenkins_client")
def test_run_no_wait_triggers_and_returns(mock_factory):
    """`pipeline run` without --wait should just trigger and exit."""
    mock_client = mock_factory.return_value
    mock_client.trigger_job = MagicMock(return_value=99)

    result = _runner().invoke(cli, ["pipeline", "run", "deploy/app"])
    assert result.exit_code == 0
    assert "Pipeline triggered successfully" in result.output
    assert "Queue item ID: 99" in result.output
    mock_client.trigger_job.assert_called_once_with("deploy/app", None)


@patch("jctl.commands.pipeline.get_jenkins_client")
def test_run_with_params(mock_factory):
    mock_client = mock_factory.return_value
    mock_client.trigger_job = MagicMock(return_value=1)

    result = _runner().invoke(
        cli, ["pipeline", "run", "deploy/app", "-p", "env=prod", "-p", "v=1.2"]
    )
    assert result.exit_code == 0
    mock_client.trigger_job.assert_called_once_with("deploy/app", {"env": "prod", "v": "1.2"})


@patch("jctl.commands.pipeline.get_jenkins_client")
def test_run_trigger_failure_exits_4(mock_factory):
    mock_client = mock_factory.return_value
    mock_client.trigger_job = MagicMock(side_effect=RuntimeError("Jenkins is down"))

    result = _runner().invoke(cli, ["pipeline", "run", "deploy/app"])
    assert result.exit_code == EXIT_JENKINS_API_ERROR


# --- list extras --------------------------------------------------------
# (the sort behavior is covered by test_pipeline_list_sort.py; here we
#  cover the --status filter and the empty-result code path).


@patch("jctl.commands.pipeline.get_jenkins_client")
def test_list_status_filter_failed_is_alias_for_failure(mock_factory):
    """--status FAILED (user-friendly) maps to Jenkins' "FAILURE"."""
    mock_client = mock_factory.return_value
    mock_client.get_jobs = AsyncMock(
        return_value=[
            {
                "fullName": "a",
                "name": "a",
                "lastBuild": {
                    "number": 1,
                    "result": "SUCCESS",
                    "timestamp": 1_700_000_000_000,
                    "duration": 1000,
                },
            },
            {
                "fullName": "b",
                "name": "b",
                "lastBuild": {
                    "number": 1,
                    "result": "FAILURE",
                    "timestamp": 1_700_000_001_000,
                    "duration": 1000,
                },
            },
        ]
    )

    result = _runner().invoke(cli, ["--output", "json", "pipeline", "list", "--status", "FAILED"])
    assert result.exit_code == 0
    rows = json.loads(re.search(r"\[.*\]", result.output, re.DOTALL).group(0))
    assert len(rows) == 1
    assert rows[0]["name"] == "b"


@patch("jctl.commands.pipeline.get_jenkins_client")
def test_list_no_pipelines_table_shows_message(mock_factory):
    mock_client = mock_factory.return_value
    mock_client.get_jobs = AsyncMock(return_value=[])

    result = _runner().invoke(cli, ["pipeline", "list"])
    assert result.exit_code == 0
    assert "No pipelines found" in result.output


@patch("jctl.commands.pipeline.get_jenkins_client")
def test_list_filter_substring_case_insensitive(mock_factory):
    """`--filter hamc` matches `…/hamc-upgrade-environment` regardless of case."""
    mock_client = mock_factory.return_value
    mock_client.get_jobs = AsyncMock(
        return_value=[
            {
                "fullName": "deploy/HAMC-upgrade",
                "name": "HAMC-upgrade",
                "lastBuild": {"number": 1, "result": "SUCCESS", "timestamp": 1, "duration": 1},
            },
            {"fullName": "other/job", "name": "job", "lastBuild": None},
        ]
    )

    result = _runner().invoke(cli, ["pipeline", "list", "--filter", "hamc"])
    assert result.exit_code == 0
    assert "HAMC-upgrade" in result.output
    # The unrelated job must not appear.
    assert "other/job" not in result.output
