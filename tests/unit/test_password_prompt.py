"""Tests for jctl.utils.password_prompt.

The termios path is tty-only and not testable in a vanilla pytest run.
We cover:
  * the fallback path through `getpass.getpass`, simulated by making
    termios.tcgetattr raise (the same failure mode the production code
    catches);
  * `password_prompt_rich`, which is what the rest of the codebase
    actually calls.
"""

import sys
from unittest.mock import patch

import pytest

import jctl.utils.password_prompt as pp

# The termios module is Unix-only; the production code lazily imports
# it inside `_password_prompt_termios` so importing the module on
# Windows is fine, but the patch-based tests need a real termios to
# monkey with.
_skip_no_termios = pytest.mark.skipif(sys.platform == "win32", reason="termios is Unix-only")


@pytest.fixture
def fake_termios_failure(monkeypatch):
    """Make `termios.tcgetattr` raise so the production code falls back
    to `getpass`."""
    import termios

    monkeypatch.setattr(
        termios, "tcgetattr", lambda fd: (_ for _ in ()).throw(termios.error("no tty"))
    )


@_skip_no_termios
def test_password_prompt_falls_back_to_getpass(fake_termios_failure):
    """When termios isn't available (no TTY, CI, etc.) we use getpass."""
    with patch("getpass.getpass", return_value="s3cret") as mock_getpass:
        result = pp.password_prompt("Password: ", mask="*")
    assert result == "s3cret"
    mock_getpass.assert_called_once_with("Password: ")


@_skip_no_termios
def test_password_prompt_termios_attribute_error_falls_back(monkeypatch):
    """The AttributeError branch — same fallback target."""

    def _raise_attr(fd):
        raise AttributeError("no fileno")

    import termios

    monkeypatch.setattr(termios, "tcgetattr", _raise_attr)
    with patch("getpass.getpass", return_value="from-getpass"):
        assert pp.password_prompt("X") == "from-getpass"


def test_password_prompt_on_windows_uses_getpass(monkeypatch):
    """On Windows there's no termios module, so the import inside
    `_password_prompt_termios` raises ImportError → fallback.
    Simulate this on every platform by removing the cached termios."""
    monkeypatch.setitem(sys.modules, "termios", None)
    with patch("getpass.getpass", return_value="from-windows") as mock_getpass:
        assert pp.password_prompt("Pwd: ") == "from-windows"
    mock_getpass.assert_called_once_with("Pwd: ")


def test_password_prompt_rich_prints_prompt_and_delegates(capsys):
    """`password_prompt_rich` prints a colored prompt then delegates."""
    with patch.object(pp, "password_prompt", return_value="entered") as mock_pp:
        result = pp.password_prompt_rich("Jenkins API token")
    assert result == "entered"
    mock_pp.assert_called_once_with("", mask="*")
    # The Rich-styled prompt was written to stdout.
    captured = capsys.readouterr().out
    assert "Jenkins API token" in captured


def test_password_prompt_rich_default_label(capsys):
    with patch.object(pp, "password_prompt", return_value=""):
        pp.password_prompt_rich()
    assert "Password" in capsys.readouterr().out


def test_password_prompt_non_tty_stdin_falls_back():
    """Regression for the OSError catch: pytest's captured stdin has no
    fileno(), which raises io.UnsupportedOperation (a subclass of OSError)
    in the production termios path. Same shape as `echo TOKEN | jctl
    auth token` and any CI run with piped stdin. The fallback to
    getpass must absorb it."""
    with patch("getpass.getpass", return_value="from-pipe") as mock_getpass:
        assert pp.password_prompt("Pwd: ") == "from-pipe"
    mock_getpass.assert_called_once_with("Pwd: ")
