"""Verify the documented JCTL_* env vars actually drive the CLI.

These were previously dead code — `ConfigManager.get_env_overrides()` named
them but nothing in `cli.py` consumed them, so `JCTL_OUTPUT_FORMAT=json
jctl auth status` silently printed a table. This file pins each env var to
the CLI behavior it advertises.
"""

from click.testing import CliRunner

from jctl.cli import cli


def test_jctl_profile_env_var_sets_profile(monkeypatch):
    monkeypatch.setenv("JCTL_PROFILE", "staging")
    runner = CliRunner()

    captured = {}

    @cli.command(name="_probe")
    def _probe():
        import click

        captured["profile"] = click.get_current_context().obj.get("profile")

    try:
        result = runner.invoke(cli, ["_probe"])
        assert result.exit_code == 0, result.output
        assert captured["profile"] == "staging"
    finally:
        # Click groups don't expose a clean unregister; pop from the
        # internal commands dict so other tests don't see the probe.
        cli.commands.pop("_probe", None)


def test_jctl_output_format_env_var_sets_output(monkeypatch):
    monkeypatch.setenv("JCTL_OUTPUT_FORMAT", "json")
    runner = CliRunner()

    captured = {}

    @cli.command(name="_probe_out")
    def _probe_out():
        import click

        captured["output"] = click.get_current_context().obj.get("output")

    try:
        result = runner.invoke(cli, ["_probe_out"])
        assert result.exit_code == 0, result.output
        assert captured["output"] == "json"
    finally:
        cli.commands.pop("_probe_out", None)


def test_jctl_log_level_env_var_sets_level(monkeypatch):
    monkeypatch.setenv("JCTL_LOG_LEVEL", "DEBUG")
    runner = CliRunner()

    captured = {}

    @cli.command(name="_probe_log")
    def _probe_log():
        import click

        captured["log_level"] = click.get_current_context().obj.get("log_level")

    try:
        result = runner.invoke(cli, ["_probe_log"])
        assert result.exit_code == 0, result.output
        assert captured["log_level"] == "DEBUG"
    finally:
        cli.commands.pop("_probe_log", None)


def test_explicit_flag_overrides_env(monkeypatch):
    """If the user passes --output yaml AND has JCTL_OUTPUT_FORMAT=json set,
    the explicit flag wins. (Click envvar semantics: env is a default, the
    flag overrides.)"""
    monkeypatch.setenv("JCTL_OUTPUT_FORMAT", "json")
    runner = CliRunner()

    captured = {}

    @cli.command(name="_probe_flag")
    def _probe_flag():
        import click

        captured["output"] = click.get_current_context().obj.get("output")

    try:
        result = runner.invoke(cli, ["--output", "yaml", "_probe_flag"])
        assert result.exit_code == 0, result.output
        assert captured["output"] == "yaml"
    finally:
        cli.commands.pop("_probe_flag", None)


def test_no_color_env_var_disables_color(monkeypatch):
    """JCTL_NO_COLOR (or NO_COLOR) sets the global Rich console to no_color."""
    # Re-import the module so the module-level Console picks up the env var.
    import importlib

    import jctl.cli as cli_mod

    monkeypatch.setenv("JCTL_NO_COLOR", "1")
    importlib.reload(cli_mod)
    assert cli_mod.console.no_color is True


def test_no_color_default_keeps_color(monkeypatch):
    import importlib

    import jctl.cli as cli_mod

    monkeypatch.delenv("JCTL_NO_COLOR", raising=False)
    monkeypatch.delenv("NO_COLOR", raising=False)
    importlib.reload(cli_mod)
    assert cli_mod.console.no_color is False
