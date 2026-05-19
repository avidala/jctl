"""Tests for `jctl auth` (logout / status / token).

Coverage push: commands/auth.py was 28% before this file. We mock
`APITokenAuthenticator` rather than the keystore so the tests don't
need a working keyring backend.
"""

import json
import re
from unittest.mock import patch

import yaml
from click.testing import CliRunner

from jctl.cli import cli
from jctl.constants import EXIT_AUTH_ERROR, EXIT_GENERAL_ERROR


def _auth_info(authenticated: bool, username: str | None = None) -> dict:
    """Build a get_auth_info()-shaped dict for the mocked authenticator."""
    return {
        "authenticated": authenticated,
        "username": username,
        "has_token": authenticated,
        "auth_method": "api_token",
    }


# --- logout --------------------------------------------------------------


@patch("jctl.commands.auth.APITokenAuthenticator")
def test_logout_when_not_authenticated_is_a_no_op(mock_cls):
    mock_cls.return_value.is_authenticated.return_value = False
    runner = CliRunner()
    result = runner.invoke(cli, ["auth", "logout"])
    assert result.exit_code == 0
    assert "Not currently authenticated" in result.output
    mock_cls.return_value.clear_token.assert_not_called()


@patch("jctl.commands.auth.APITokenAuthenticator")
def test_logout_clears_token(mock_cls):
    mock_cls.return_value.is_authenticated.return_value = True
    runner = CliRunner()
    result = runner.invoke(cli, ["auth", "logout"])
    assert result.exit_code == 0
    assert "Logged out successfully" in result.output
    mock_cls.return_value.clear_token.assert_called_once()


@patch("jctl.commands.auth.APITokenAuthenticator")
def test_logout_propagates_clear_failure_as_rc_1(mock_cls):
    mock_cls.return_value.is_authenticated.return_value = True
    mock_cls.return_value.clear_token.side_effect = RuntimeError("keyring locked")
    runner = CliRunner()
    result = runner.invoke(cli, ["auth", "logout"])
    assert result.exit_code == EXIT_GENERAL_ERROR
    assert "Error during logout" in result.output


# --- status --------------------------------------------------------------


@patch("jctl.commands.auth.APITokenAuthenticator")
def test_status_not_authenticated_table(mock_cls):
    mock_cls.return_value.get_auth_info.return_value = _auth_info(False)
    runner = CliRunner()
    result = runner.invoke(cli, ["auth", "status"])
    assert result.exit_code == 0
    assert "Not authenticated" in result.output


@patch("jctl.commands.auth.APITokenAuthenticator")
def test_status_authenticated_table(mock_cls):
    mock_cls.return_value.get_auth_info.return_value = _auth_info(True, "user@example.com")
    runner = CliRunner()
    result = runner.invoke(cli, ["auth", "status"])
    assert result.exit_code == 0
    assert "Configured" in result.output
    assert "user@example.com" in result.output


@patch("jctl.commands.auth.APITokenAuthenticator")
def test_status_json_is_parsable(mock_cls):
    mock_cls.return_value.get_auth_info.return_value = _auth_info(True, "user@example.com")
    runner = CliRunner()
    result = runner.invoke(cli, ["--output", "json", "auth", "status"])
    assert result.exit_code == 0
    payload = json.loads(re.search(r"\{.*\}", result.output, re.DOTALL).group(0))
    assert payload["authenticated"] is True
    assert payload["username"] == "user@example.com"


@patch("jctl.commands.auth.APITokenAuthenticator")
def test_status_yaml_is_parsable(mock_cls):
    mock_cls.return_value.get_auth_info.return_value = _auth_info(True, "u")
    runner = CliRunner()
    result = runner.invoke(cli, ["--output", "yaml", "auth", "status"])
    assert result.exit_code == 0
    payload = yaml.safe_load(result.output)
    assert payload["authenticated"] is True


@patch("jctl.commands.auth.APITokenAuthenticator")
def test_status_plain_is_flat_kv(mock_cls):
    mock_cls.return_value.get_auth_info.return_value = _auth_info(True, "u")
    runner = CliRunner()
    result = runner.invoke(cli, ["--output", "plain", "auth", "status"])
    assert result.exit_code == 0
    assert "authenticated=True" in result.output
    assert "username=u" in result.output


@patch("jctl.commands.auth.APITokenAuthenticator")
def test_status_handles_missing_username(mock_cls):
    """Regression: `api_auth_info['username']` can be None; the table cell
    used to type-error as `Literal[True] | str` in mypy. Now coerced to str."""
    mock_cls.return_value.get_auth_info.return_value = _auth_info(True, None)
    runner = CliRunner()
    result = runner.invoke(cli, ["auth", "status"])
    assert result.exit_code == 0
    assert "Unknown" in result.output


# --- token ---------------------------------------------------------------


@patch("jctl.commands.auth.APITokenAuthenticator")
def test_token_already_configured_warns_without_overwriting(mock_cls):
    mock_cls.return_value.is_authenticated.return_value = True
    runner = CliRunner()
    result = runner.invoke(cli, ["auth", "token"])
    assert result.exit_code == 0
    assert "already configured" in result.output
    mock_cls.return_value.store_token.assert_not_called()


@patch("jctl.commands.auth.APITokenAuthenticator")
def test_token_stores_with_explicit_args(mock_cls):
    mock_cls.return_value.is_authenticated.return_value = False
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["auth", "token", "--username", "u@example.com", "--token", "secret-token"],
    )
    assert result.exit_code == 0
    assert "configured successfully" in result.output
    mock_cls.return_value.store_token.assert_called_once_with("u@example.com", "secret-token")


@patch("jctl.commands.auth.APITokenAuthenticator")
def test_token_store_failure_exits_auth_error(mock_cls):
    mock_cls.return_value.is_authenticated.return_value = False
    mock_cls.return_value.store_token.side_effect = RuntimeError("keyring locked")
    runner = CliRunner()
    result = runner.invoke(cli, ["auth", "token", "--username", "u@example.com", "--token", "t"])
    assert result.exit_code == EXIT_AUTH_ERROR
    assert "Error storing token" in result.output


@patch("jctl.commands.auth.APITokenAuthenticator")
def test_token_re_store_explicit_overrides_already_configured(mock_cls):
    """`auth token --username u --token t` should re-store even when
    already authenticated — the explicit args mean "I want to update"."""
    mock_cls.return_value.is_authenticated.return_value = True
    runner = CliRunner()
    result = runner.invoke(cli, ["auth", "token", "--username", "new@x", "--token", "new-tok"])
    assert result.exit_code == 0
    mock_cls.return_value.store_token.assert_called_once_with("new@x", "new-tok")
