"""Tests for `jctl completion --install` safety / portability.

The original installer (1) silently appended to `~/.zshrc` with no
confirmation prompt and (2) baked in the absolute path to a machine-
local `scripts/jctl-completion.zsh` file that isn't in the wheel. We
replaced it with a confirmation-gated, Click-native eval snippet.
"""

from pathlib import Path

from click.testing import CliRunner

from jctl.cli import cli


def _rc_for(home: Path, shell: str) -> Path:
    if shell == "bash":
        return home / ".bashrc"
    if shell == "zsh":
        return home / ".zshrc"
    raise AssertionError(f"unsupported in test helper: {shell}")


def test_dry_run_does_not_touch_file(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("SHELL", "/bin/zsh")
    runner = CliRunner()

    result = runner.invoke(cli, ["completion", "--install", "--dry-run"])
    assert result.exit_code == 0, result.output
    assert "Would append to" in result.output
    # No rc file created on dry-run.
    assert not _rc_for(tmp_path, "zsh").exists()


def test_prompt_declined_makes_no_changes(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("SHELL", "/bin/zsh")
    rc = _rc_for(tmp_path, "zsh")
    rc.write_text("# pre-existing line\n")
    runner = CliRunner()

    # input='n\n' answers the Confirm prompt with "no".
    result = runner.invoke(cli, ["completion", "--install"], input="n\n")
    assert result.exit_code == 0, result.output
    assert "Aborted" in result.output
    # rc file untouched.
    assert rc.read_text() == "# pre-existing line\n"


def test_yes_flag_bypasses_prompt(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("SHELL", "/bin/zsh")
    runner = CliRunner()

    result = runner.invoke(cli, ["completion", "--install", "--yes"])
    assert result.exit_code == 0, result.output

    rc = _rc_for(tmp_path, "zsh")
    assert rc.exists()
    content = rc.read_text()
    assert "_JCTL_COMPLETE=zsh_source jctl" in content
    # No machine-absolute repo paths leaked into the rc file.
    assert "scripts/jctl-completion" not in content
    assert "/Users/" not in content


def test_idempotent_install(tmp_path, monkeypatch):
    """A second --install on an already-installed rc must be a no-op,
    not duplicate the snippet."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("SHELL", "/bin/zsh")
    runner = CliRunner()

    runner.invoke(cli, ["completion", "--install", "--yes"])
    rc = _rc_for(tmp_path, "zsh")
    first_content = rc.read_text()

    result = runner.invoke(cli, ["completion", "--install", "--yes"])
    assert result.exit_code == 0, result.output
    assert "already installed" in result.output
    assert rc.read_text() == first_content


def test_install_explicit_bash_shell(tmp_path, monkeypatch):
    """Passing `bash` explicitly overrides `$SHELL` auto-detection."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("SHELL", "/bin/zsh")
    (tmp_path / ".bashrc").touch()
    runner = CliRunner()

    result = runner.invoke(cli, ["completion", "bash", "--install", "--yes"])
    assert result.exit_code == 0, result.output

    bashrc = tmp_path / ".bashrc"
    assert "_JCTL_COMPLETE=bash_source jctl" in bashrc.read_text()
    # The zshrc must not have been touched.
    assert not (tmp_path / ".zshrc").exists()


def test_install_errors_when_shell_unknown(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("SHELL", raising=False)
    runner = CliRunner()

    result = runner.invoke(cli, ["completion", "--install"])
    assert result.exit_code == 1
    assert "Could not detect shell" in result.output
