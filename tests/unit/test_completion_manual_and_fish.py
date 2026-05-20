"""Close the remaining `jctl/cli.py` coverage gap.

The existing `test_completion_install.py` covers the bash/zsh
`--install` path. This module adds:
  * the manual-instructions path (no `--install`) for each of
    bash / zsh / fish;
  * the fish `--install` path (subprocess-driven generation, the
    overwrite prompt, dry-run, and subprocess failure).
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from jctl.cli import cli


@pytest.fixture
def fake_home(tmp_path, monkeypatch):
    """Sandbox `Path.home()` so tests never touch the real ~."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    return tmp_path


# --- manual-instruction paths -------------------------------------------


def test_manual_instructions_for_zsh(fake_home, monkeypatch):
    """`jctl completion zsh` (no --install) prints the eval snippet
    and the source-rc hint, but doesn't touch any file."""
    monkeypatch.setenv("SHELL", "/bin/zsh")
    result = CliRunner().invoke(cli, ["completion", "zsh"])
    assert result.exit_code == 0
    assert "_JCTL_COMPLETE=zsh_source jctl" in result.output
    assert "Manual setup" in result.output or "manual setup" in result.output
    # Tab-completion examples appear.
    assert "Tab-complete" in result.output
    # No rc file created.
    assert not (fake_home / ".zshrc").exists()


def test_manual_instructions_for_bash(fake_home, monkeypatch):
    monkeypatch.setenv("SHELL", "/bin/bash")
    result = CliRunner().invoke(cli, ["completion", "bash"])
    assert result.exit_code == 0
    assert "_JCTL_COMPLETE=bash_source jctl" in result.output


def test_manual_instructions_for_fish(fake_home, monkeypatch):
    """The fish branch in the manual path takes a different code path
    (no rc file — it uses the `_JCTL_COMPLETE=fish_source` redirect)."""
    monkeypatch.setenv("SHELL", "/usr/local/bin/fish")
    result = CliRunner().invoke(cli, ["completion", "fish"])
    assert result.exit_code == 0
    assert "_JCTL_COMPLETE=fish_source jctl" in result.output
    assert "~/.config/fish/completions/jctl.fish" in result.output


# --- fish --install -----------------------------------------------------


@patch("subprocess.run")
def test_fish_install_writes_completion_file(mock_run, fake_home, monkeypatch):
    """`jctl completion fish --install` shells out to generate the
    completion script and writes it under ~/.config/fish/completions/."""
    monkeypatch.setenv("SHELL", "/usr/local/bin/fish")
    mock_run.return_value = MagicMock(returncode=0, stdout="# fish completion body\n")

    result = CliRunner().invoke(cli, ["completion", "fish", "--install"])
    assert result.exit_code == 0, result.output

    target = fake_home / ".config" / "fish" / "completions" / "jctl.fish"
    assert target.exists()
    assert "fish completion body" in target.read_text()

    # The subprocess fired with the magic env var.
    call_env = mock_run.call_args.kwargs["env"]
    assert call_env["_JCTL_COMPLETE"] == "fish_source"


@patch("subprocess.run")
def test_fish_install_dry_run_does_not_write(mock_run, fake_home, monkeypatch):
    monkeypatch.setenv("SHELL", "/usr/local/bin/fish")

    result = CliRunner().invoke(cli, ["completion", "fish", "--install", "--dry-run"])
    assert result.exit_code == 0
    assert "Would write" in result.output

    # No subprocess fired in dry-run.
    mock_run.assert_not_called()
    target = fake_home / ".config" / "fish" / "completions" / "jctl.fish"
    assert not target.exists()


@patch("subprocess.run")
def test_fish_install_overwrite_declined_makes_no_changes(mock_run, fake_home, monkeypatch):
    """If the completion file already exists and the user says 'no'
    to Overwrite?, the file is preserved untouched."""
    monkeypatch.setenv("SHELL", "/usr/local/bin/fish")
    target = fake_home / ".config" / "fish" / "completions" / "jctl.fish"
    target.parent.mkdir(parents=True)
    target.write_text("# pre-existing\n")

    result = CliRunner().invoke(cli, ["completion", "fish", "--install"], input="n\n")
    assert result.exit_code == 0
    assert "Aborted" in result.output
    # Untouched.
    assert target.read_text() == "# pre-existing\n"
    mock_run.assert_not_called()


@patch("subprocess.run")
def test_fish_install_overwrite_confirmed_proceeds(mock_run, fake_home, monkeypatch):
    monkeypatch.setenv("SHELL", "/usr/local/bin/fish")
    target = fake_home / ".config" / "fish" / "completions" / "jctl.fish"
    target.parent.mkdir(parents=True)
    target.write_text("# old\n")

    mock_run.return_value = MagicMock(returncode=0, stdout="# new body\n")
    result = CliRunner().invoke(cli, ["completion", "fish", "--install"], input="y\n")
    assert result.exit_code == 0
    assert "new body" in target.read_text()


@patch("subprocess.run")
def test_fish_install_subprocess_failure_exits_1(mock_run, fake_home, monkeypatch):
    """If the Click-completion subprocess fails (broken install, missing
    binary), we surface the stderr and exit 1 — no half-written file."""
    monkeypatch.setenv("SHELL", "/usr/local/bin/fish")
    mock_run.return_value = MagicMock(returncode=2, stdout="", stderr="some completion error")

    result = CliRunner().invoke(cli, ["completion", "fish", "--install"])
    assert result.exit_code == 1
    assert "Failed to generate fish completion" in result.output
    target = fake_home / ".config" / "fish" / "completions" / "jctl.fish"
    assert not target.exists()
