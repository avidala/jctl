"""Coverage for `--wait` polling loops in `jctl job trigger` and
`jctl pipeline run`.

These paths poll Jenkins twice — once for the queue item to acquire
a build number, then for the build's `result` to transition from
None to SUCCESS/FAILURE/ABORTED. We patch `asyncio.sleep` to a no-op
so the tests run in milliseconds.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner

from jctl.cli import cli
from jctl.constants import EXIT_JENKINS_API_ERROR


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    """Make all `asyncio.sleep` calls return immediately.

    Patches into both modules that import asyncio (job.py and
    pipeline.py); the inner async functions reach `asyncio.sleep`
    through the module-global import.
    """

    async def _instant(_):
        return None

    monkeypatch.setattr("jctl.commands.job.asyncio.sleep", _instant)
    monkeypatch.setattr("jctl.commands.pipeline.asyncio.sleep", _instant)


def _runner() -> CliRunner:
    return CliRunner()


# --- job trigger --wait --------------------------------------------------


@patch("jctl.commands.job.get_jenkins_client")
def test_job_trigger_wait_success(mock_factory):
    """Happy path: queue resolves to a build number, then the build
    transitions from running to SUCCESS."""
    mock_client = mock_factory.return_value
    mock_client.trigger_job = MagicMock(return_value=100)

    # First queue poll has no executable yet, second one does.
    mock_client.get_queue_item = AsyncMock(
        side_effect=[
            {"blocked": False},
            {"executable": {"number": 7}},
        ]
    )
    # First build poll: still running (result=None). Second: SUCCESS.
    mock_client.get_build_info = AsyncMock(
        side_effect=[
            {"result": None, "duration": 0},
            {"result": "SUCCESS", "duration": 5000},
        ]
    )

    result = _runner().invoke(cli, ["job", "trigger", "deploy/app", "--wait"])
    assert result.exit_code == 0, result.output
    assert "Job started - Build #7" in result.output
    assert "completed successfully" in result.output


@patch("jctl.commands.job.get_jenkins_client")
def test_job_trigger_wait_failure_exits_4(mock_factory):
    mock_client = mock_factory.return_value
    mock_client.trigger_job = MagicMock(return_value=100)
    mock_client.get_queue_item = AsyncMock(return_value={"executable": {"number": 7}})
    mock_client.get_build_info = AsyncMock(return_value={"result": "FAILURE"})

    result = _runner().invoke(cli, ["job", "trigger", "deploy/app", "--wait"])
    assert result.exit_code == EXIT_JENKINS_API_ERROR
    assert "Build #7 failed" in result.output


@patch("jctl.commands.job.get_jenkins_client")
def test_job_trigger_wait_aborted_exits_4(mock_factory):
    mock_client = mock_factory.return_value
    mock_client.trigger_job = MagicMock(return_value=100)
    mock_client.get_queue_item = AsyncMock(return_value={"executable": {"number": 7}})
    mock_client.get_build_info = AsyncMock(return_value={"result": "ABORTED"})

    result = _runner().invoke(cli, ["job", "trigger", "deploy/app", "--wait"])
    assert result.exit_code == EXIT_JENKINS_API_ERROR
    assert "was aborted" in result.output


@patch("jctl.commands.job.get_jenkins_client")
def test_job_trigger_wait_unknown_result_does_not_error(mock_factory):
    """Other result strings (UNSTABLE, NOT_BUILT, etc.) finish without
    raising — they're reported as the literal status."""
    mock_client = mock_factory.return_value
    mock_client.trigger_job = MagicMock(return_value=100)
    mock_client.get_queue_item = AsyncMock(return_value={"executable": {"number": 7}})
    mock_client.get_build_info = AsyncMock(return_value={"result": "UNSTABLE"})

    result = _runner().invoke(cli, ["job", "trigger", "deploy/app", "--wait"])
    assert result.exit_code == 0
    assert "UNSTABLE" in result.output


@patch("jctl.commands.job.get_jenkins_client")
def test_job_trigger_wait_queue_blocked_then_starts(mock_factory):
    """`blocked` and `stuck` in the queue produce a status line but
    don't fail."""
    mock_client = mock_factory.return_value
    mock_client.trigger_job = MagicMock(return_value=100)
    mock_client.get_queue_item = AsyncMock(
        side_effect=[
            {"blocked": True},
            {"stuck": True},
            {"executable": {"number": 7}},
        ]
    )
    mock_client.get_build_info = AsyncMock(return_value={"result": "SUCCESS"})

    result = _runner().invoke(cli, ["job", "trigger", "deploy/app", "--wait"])
    assert result.exit_code == 0
    assert "blocked" in result.output
    assert "stuck" in result.output


@patch("jctl.commands.job.get_jenkins_client")
def test_job_trigger_wait_queue_never_starts(mock_factory):
    """If the queue never produces an executable in 60 polls, we
    print a 'did not start' message and exit 0 (the trigger itself
    succeeded; we just can't observe the build)."""
    mock_client = mock_factory.return_value
    mock_client.trigger_job = MagicMock(return_value=100)
    mock_client.get_queue_item = AsyncMock(return_value={"blocked": False})

    result = _runner().invoke(cli, ["job", "trigger", "deploy/app", "--wait"])
    assert result.exit_code == 0
    assert "did not start within 60 seconds" in result.output


@patch("jctl.commands.job.get_jenkins_client")
def test_job_trigger_wait_queue_get_failure_keeps_polling(mock_factory):
    """A transient `get_queue_item` failure is logged at debug and
    polling continues."""
    mock_client = mock_factory.return_value
    mock_client.trigger_job = MagicMock(return_value=100)
    mock_client.get_queue_item = AsyncMock(
        side_effect=[
            RuntimeError("transient"),
            {"executable": {"number": 7}},
        ]
    )
    mock_client.get_build_info = AsyncMock(return_value={"result": "SUCCESS"})

    result = _runner().invoke(cli, ["job", "trigger", "deploy/app", "--wait"])
    assert result.exit_code == 0
    # The transient error didn't surface to the user; the build still
    # got monitored to completion.
    assert "Build #7 completed successfully" in result.output


# --- pipeline run --wait -------------------------------------------------


@patch("jctl.commands.pipeline.get_jenkins_client")
def test_pipeline_run_wait_success(mock_factory):
    """Happy path through the pipeline-specific --wait loop, which
    additionally renders workflow stages on every change."""
    mock_client = mock_factory.return_value
    mock_client.trigger_job = MagicMock(return_value=100)
    mock_client.get_queue_item = AsyncMock(return_value={"executable": {"number": 9}})
    mock_client.get_build_info = AsyncMock(
        side_effect=[
            {"result": None},
            {"result": "SUCCESS"},
        ]
    )
    mock_client.get_workflow_info = AsyncMock(
        side_effect=[
            {"stages": [{"name": "Build", "status": "IN_PROGRESS"}]},
            {"stages": [{"name": "Build", "status": "SUCCESS"}]},
        ]
    )

    result = _runner().invoke(cli, ["pipeline", "run", "deploy/app", "--wait"])
    assert result.exit_code == 0, result.output
    assert "Pipeline started - Build #9" in result.output
    assert "Pipeline completed successfully" in result.output


@patch("jctl.commands.pipeline.get_jenkins_client")
def test_pipeline_run_wait_failure_exits_4(mock_factory):
    mock_client = mock_factory.return_value
    mock_client.trigger_job = MagicMock(return_value=100)
    mock_client.get_queue_item = AsyncMock(return_value={"executable": {"number": 9}})
    mock_client.get_build_info = AsyncMock(return_value={"result": "FAILURE"})
    mock_client.get_workflow_info = AsyncMock(return_value={"stages": []})

    result = _runner().invoke(cli, ["pipeline", "run", "deploy/app", "--wait"])
    assert result.exit_code == EXIT_JENKINS_API_ERROR
    assert "Pipeline failed" in result.output


@patch("jctl.commands.pipeline.get_jenkins_client")
def test_pipeline_run_wait_aborted_exits_4(mock_factory):
    mock_client = mock_factory.return_value
    mock_client.trigger_job = MagicMock(return_value=100)
    mock_client.get_queue_item = AsyncMock(return_value={"executable": {"number": 9}})
    mock_client.get_build_info = AsyncMock(return_value={"result": "ABORTED"})
    mock_client.get_workflow_info = AsyncMock(return_value={"stages": []})

    result = _runner().invoke(cli, ["pipeline", "run", "deploy/app", "--wait"])
    assert result.exit_code == EXIT_JENKINS_API_ERROR
    assert "Pipeline was aborted" in result.output


@patch("jctl.commands.pipeline.get_jenkins_client")
def test_pipeline_run_notify_only_runs_through_simpler_loop(mock_factory):
    """`--notify` without `--wait` enters a separate polling branch that
    skips workflow-stage rendering."""
    mock_client = mock_factory.return_value
    mock_client.trigger_job = MagicMock(return_value=100)
    mock_client.get_queue_item = AsyncMock(return_value={"executable": {"number": 9}})
    mock_client.get_build_info = AsyncMock(return_value={"result": "SUCCESS"})

    result = _runner().invoke(cli, ["pipeline", "run", "deploy/app", "--notify"])
    assert result.exit_code == 0
    assert "Pipeline completed successfully" in result.output


@patch("jctl.commands.pipeline.get_jenkins_client")
def test_pipeline_run_wait_workflow_api_missing_keeps_going(mock_factory):
    """If the workflow API is unavailable (non-pipeline job), --wait
    still tracks the build via get_build_info."""
    mock_client = mock_factory.return_value
    mock_client.trigger_job = MagicMock(return_value=100)
    mock_client.get_queue_item = AsyncMock(return_value={"executable": {"number": 9}})
    mock_client.get_build_info = AsyncMock(return_value={"result": "SUCCESS"})
    mock_client.get_workflow_info = AsyncMock(side_effect=RuntimeError("no wfapi"))

    result = _runner().invoke(cli, ["pipeline", "run", "deploy/app", "--wait"])
    assert result.exit_code == 0
    assert "Pipeline completed successfully" in result.output
