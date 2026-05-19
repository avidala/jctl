"""Tests for `jctl config` (get / set / list / show / add-profile).

Coverage push: commands/config.py was 22% before this file. The
underlying ConfigManager already has its own tests; here we drive
the command layer end-to-end with a real config file under tmp_path.
"""

import json
import re
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from jctl.cli import cli
from jctl.constants import EXIT_CONFIG_ERROR


@pytest.fixture
def cfg_home(tmp_path, monkeypatch):
    """Point both ConfigManager and `Path.home()` at a tmp dir.

    Same Windows/POSIX-portable trick as the completion-install tests.
    """
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    cfg_dir = tmp_path / ".jctl"
    cfg_dir.mkdir()
    cfg_file = cfg_dir / "config.yaml"
    cfg_file.write_text(
        "version: '1.0'\n"
        "default_profile: dev\n"
        "profiles:\n"
        "  dev:\n"
        "    jenkins:\n"
        "      url: https://jenkins.example.com\n"
        "      verify_ssl: true\n"
        "defaults:\n"
        "  timeout: 30\n"
    )
    return tmp_path


def _runner() -> CliRunner:
    return CliRunner()


# --- get -----------------------------------------------------------------


def test_get_returns_value(cfg_home):
    result = _runner().invoke(cli, ["config", "get", "defaults.timeout"])
    assert result.exit_code == 0
    assert "30" in result.output


def test_get_unknown_key_exits_2(cfg_home):
    result = _runner().invoke(cli, ["config", "get", "bogus.path"])
    assert result.exit_code == EXIT_CONFIG_ERROR


def test_get_without_config_exits_2(tmp_path, monkeypatch):
    """No config file at all → friendly error, rc=2."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    result = _runner().invoke(cli, ["config", "get", "defaults.timeout"])
    assert result.exit_code == EXIT_CONFIG_ERROR
    assert "Configuration not found" in result.output


def test_get_output_plain_prints_just_value(cfg_home):
    """--output plain prints the value alone — easy to capture in shell."""
    result = _runner().invoke(cli, ["--output", "plain", "config", "get", "defaults.timeout"])
    assert result.exit_code == 0
    # Plain mode prints just the value (no "key = ..." prefix).
    assert "30" in result.output
    assert "defaults.timeout" not in result.output


# --- set -----------------------------------------------------------------


def test_set_coerces_string_to_int(cfg_home):
    """The QA-found data-corruption guard: '60' → int(60), not the
    literal string."""
    runner = _runner()
    runner.invoke(cli, ["config", "set", "defaults.timeout", "60"])
    result = runner.invoke(cli, ["config", "get", "defaults.timeout"])
    assert "60" in result.output
    # And the YAML on disk holds an int, not a quoted string.
    raw = (cfg_home / ".jctl" / "config.yaml").read_text()
    # YAML representation of int 60 has no quotes around the number.
    assert "timeout: 60" in raw


def test_set_rejects_bad_int_and_keeps_file_valid(cfg_home):
    runner = _runner()
    result = runner.invoke(cli, ["config", "set", "defaults.timeout", "notanumber"])
    assert result.exit_code == EXIT_CONFIG_ERROR
    assert "Invalid value" in result.output
    # File still loads cleanly — no corruption.
    follow_up = runner.invoke(cli, ["config", "get", "defaults.timeout"])
    assert follow_up.exit_code == 0


def test_set_rejects_unknown_root_key(cfg_home):
    """`config set bogus value` used to silently invent a root-level
    field; now it's rejected."""
    result = _runner().invoke(cli, ["config", "set", "bogus", "value"])
    assert result.exit_code == EXIT_CONFIG_ERROR
    assert "Unknown configuration key" in result.output


def test_set_without_config_exits_2(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    result = _runner().invoke(cli, ["config", "set", "defaults.timeout", "60"])
    assert result.exit_code == EXIT_CONFIG_ERROR


# --- list ----------------------------------------------------------------


def test_list_table_default(cfg_home):
    result = _runner().invoke(cli, ["config", "list"])
    assert result.exit_code == 0
    assert "default_profile" in result.output


def test_list_json_round_trips(cfg_home):
    result = _runner().invoke(cli, ["--output", "json", "config", "list"])
    assert result.exit_code == 0
    payload = json.loads(re.search(r"\{.*\}", result.output, re.DOTALL).group(0))
    assert payload["default_profile"] == "dev"
    assert "dev" in payload["profiles"]


def test_list_yaml_round_trips(cfg_home):
    result = _runner().invoke(cli, ["--output", "yaml", "config", "list"])
    assert result.exit_code == 0
    payload = yaml.safe_load(result.output)
    assert payload["default_profile"] == "dev"


# --- show ----------------------------------------------------------------


def test_show_table_mode_dumps_yaml_body(cfg_home):
    """In table mode `show` prints the raw config file with a header."""
    result = _runner().invoke(cli, ["config", "show"])
    assert result.exit_code == 0
    assert "Configuration file:" in result.output
    # `re.search` over a literal hostname avoids CodeQL's
    # py/incomplete-url-substring-sanitization false-positive on
    # `"<host>" in <string>` patterns. We're not validating a URL —
    # we're verifying the rendered YAML echoes the seed config.
    assert re.search(r"jenkins\.example\.com", result.output)


def test_show_json_is_parsable(cfg_home):
    result = _runner().invoke(cli, ["--output", "json", "config", "show"])
    assert result.exit_code == 0
    payload = json.loads(re.search(r"\{.*\}", result.output, re.DOTALL).group(0))
    # show with --output emits the structured config (no shell decoration).
    assert payload["default_profile"] == "dev"


def test_show_without_config_exits_2(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    result = _runner().invoke(cli, ["config", "show"])
    assert result.exit_code == EXIT_CONFIG_ERROR


# --- add-profile ---------------------------------------------------------


def test_add_profile_minimal(cfg_home):
    """Minimal profile addition: just --jenkins-url, no Okta block."""
    result = _runner().invoke(
        cli,
        ["config", "add-profile", "staging", "--jenkins-url", "https://staging.example.com"],
    )
    assert result.exit_code == 0, result.output
    assert "added successfully" in result.output

    # Read back via `config get` to confirm it actually persisted. Use
    # `re.search` for the host check — see the comment in
    # test_show_table_mode_dumps_yaml_body.
    follow_up = _runner().invoke(cli, ["config", "get", "staging.jenkins.url"])
    assert re.search(r"staging\.example\.com", follow_up.output)


def test_add_profile_with_set_default(cfg_home):
    """--set-default flips default_profile to the new profile."""
    _runner().invoke(
        cli,
        [
            "config",
            "add-profile",
            "prod",
            "--jenkins-url",
            "https://prod.example.com",
            "--set-default",
        ],
    )
    result = _runner().invoke(cli, ["config", "get", "default_profile"])
    assert "prod" in result.output


def test_add_profile_without_config_exits_2(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    result = _runner().invoke(
        cli,
        ["config", "add-profile", "x", "--jenkins-url", "https://x.example.com"],
    )
    assert result.exit_code == EXIT_CONFIG_ERROR
