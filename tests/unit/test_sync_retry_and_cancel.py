"""Tests for sync-path retry on python-jenkins + cancel exit-code mapping."""

from unittest.mock import MagicMock, patch

import pytest
import requests
from click.testing import CliRunner

from jctl.cli import cli
from jctl.constants import EXIT_USER_CANCELLED
from jctl.jenkins.client import JenkinsClient


@pytest.fixture
def client() -> JenkinsClient:
    return JenkinsClient(url="https://jenkins.test.example", username="u", password="t")


class TestSyncRetry:
    """python-jenkins calls used to bypass tenacity entirely. Each of these
    should now retry the transient exception once before succeeding."""

    def test_get_job_info_retries_on_connection_error(self, client):
        mock_inner = MagicMock()
        mock_inner.get_job_info.side_effect = [
            requests.exceptions.ConnectionError("boom"),
            {"name": "x", "buildable": True},
        ]
        client._jenkins = mock_inner
        info = client.get_job_info("x")
        assert info == {"name": "x", "buildable": True}
        assert mock_inner.get_job_info.call_count == 2

    def test_trigger_job_retries_on_socket_timeout(self, client):
        mock_inner = MagicMock()
        mock_inner.build_job.side_effect = [TimeoutError("slow"), 42]
        client._jenkins = mock_inner
        assert client.trigger_job("x") == 42
        assert mock_inner.build_job.call_count == 2

    def test_list_jobs_retries_on_network_error(self, client):
        mock_inner = MagicMock()
        mock_inner.get_jobs.side_effect = [
            requests.exceptions.ReadTimeout("slow"),
            [{"name": "j"}],
        ]
        client._jenkins = mock_inner
        assert client.list_jobs() == [{"name": "j"}]
        assert mock_inner.get_jobs.call_count == 2

    def test_does_not_retry_non_network_errors(self, client):
        """Auth/404 are terminal — retrying just adds latency before the
        user sees the real error."""

        class FakeJenkinsException(Exception):
            pass

        mock_inner = MagicMock()
        mock_inner.get_job_info.side_effect = FakeJenkinsException("404 not found")
        client._jenkins = mock_inner
        with pytest.raises(FakeJenkinsException):
            client.get_job_info("x")
        # Only one call — no retry on non-network errors.
        assert mock_inner.get_job_info.call_count == 1


class TestCancelExitCode:
    """The old `@click.confirmation_option` decorator mapped 'no' to exit 1
    (Click's generic Abort), indistinguishable from real errors. We now
    map it to EXIT_USER_CANCELLED=130."""

    @patch("jctl.commands.pipeline.get_jenkins_client")
    def test_cancel_declined_exits_130(self, _mock_factory, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("JCTL_CONFIG_DIR", str(tmp_path / ".jctl"))
        runner = CliRunner()
        result = runner.invoke(cli, ["pipeline", "cancel", "some/job", "1"], input="n\n")
        assert result.exit_code == EXIT_USER_CANCELLED, result.output
        assert "aborted by user" in result.output.lower()

    @patch("jctl.commands.pipeline.get_jenkins_client")
    def test_cancel_yes_flag_skips_prompt(self, mock_factory, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("JCTL_CONFIG_DIR", str(tmp_path / ".jctl"))

        from unittest.mock import AsyncMock

        mock_factory.return_value.stop_build = AsyncMock(return_value=None)
        runner = CliRunner()
        result = runner.invoke(cli, ["pipeline", "cancel", "some/job", "1", "--yes"])
        assert result.exit_code == 0, result.output
        assert "Cancelling" in result.output
        # Confirm prompt did NOT appear.
        assert (
            "Cancel pipeline" not in result.output
            or "?" not in result.output.split("Cancelling")[0]
        )
