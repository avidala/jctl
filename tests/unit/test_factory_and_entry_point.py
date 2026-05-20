"""Cover the two small gaps:
- `utils/jenkins_client_factory.py` — exit branches when there's no
  config or no stored API token.
- `__main__.main()` — wraps cli() and maps KeyboardInterrupt → 130 and
  generic Exception → 1.
"""

import sys
from pathlib import Path

import pytest

from jctl.__main__ import main
from jctl.constants import EXIT_USER_CANCELLED
from jctl.utils.jenkins_client_factory import get_jenkins_client


def _ctx(profile: str | None = None):
    """Click contexts in production are full objects; the factory only
    reads `ctx.obj.get("profile")` so a small stand-in is enough."""
    from unittest.mock import MagicMock

    ctx = MagicMock()
    ctx.obj = {"profile": profile}
    return ctx


# --- jenkins_client_factory ---------------------------------------------


def test_factory_exits_when_config_file_missing(tmp_path, monkeypatch):
    """No `~/.jctl/config.yaml` → friendly message + sys.exit(1)."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    with pytest.raises(SystemExit) as exc_info:
        get_jenkins_client(_ctx())
    assert exc_info.value.code == 1


def test_factory_exits_when_no_auth_configured(tmp_path, monkeypatch, capsys):
    """Config exists but no API token stored → 'Not authenticated' + sys.exit(1).
    Uses the file-based keyring backend so the test doesn't touch the OS
    keychain, and writes a minimal valid config to disk."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("PYTHON_KEYRING_BACKEND", "keyrings.alt.file.PlaintextKeyring")
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "keyring"))

    (tmp_path / ".jctl").mkdir()
    (tmp_path / ".jctl" / "config.yaml").write_text(
        "version: '1.0'\n"
        "default_profile: dev\n"
        "profiles:\n"
        "  dev:\n"
        "    jenkins:\n"
        "      url: https://jenkins.example.com\n"
    )

    with pytest.raises(SystemExit) as exc_info:
        get_jenkins_client(_ctx())
    assert exc_info.value.code == 1
    err = capsys.readouterr().out
    assert "Not authenticated" in err
    assert "jctl auth token" in err


def test_factory_returns_client_when_auth_present(tmp_path, monkeypatch):
    """When the OS keystore (or the file fallback) has both username +
    token, factory returns a JenkinsClient with those creds plumbed in."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("PYTHON_KEYRING_BACKEND", "keyrings.alt.file.PlaintextKeyring")
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "keyring"))

    (tmp_path / ".jctl").mkdir()
    (tmp_path / ".jctl" / "config.yaml").write_text(
        "version: '1.0'\n"
        "default_profile: dev\n"
        "profiles:\n"
        "  dev:\n"
        "    jenkins:\n"
        "      url: https://jenkins.example.com\n"
    )

    # Seed credentials via the same path the CLI uses.
    from jctl.auth.api_token import APITokenAuthenticator

    APITokenAuthenticator().store_token("user@example.com", "TOKEN")

    client = get_jenkins_client(_ctx())
    assert client.username == "user@example.com"
    assert client.password == "TOKEN"
    # And the configured URL was passed through (rstrip removes the
    # trailing slash Pydantic's HttpUrl adds during validation).
    assert client.url == "https://jenkins.example.com"


def test_factory_respects_jctl_jenkins_url_env_override(tmp_path, monkeypatch):
    """JCTL_JENKINS_URL overrides the profile's URL — handy for one-off
    runs without editing config."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("PYTHON_KEYRING_BACKEND", "keyrings.alt.file.PlaintextKeyring")
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "keyring"))
    monkeypatch.setenv("JCTL_JENKINS_URL", "https://override.example.com")

    (tmp_path / ".jctl").mkdir()
    (tmp_path / ".jctl" / "config.yaml").write_text(
        "version: '1.0'\n"
        "default_profile: dev\n"
        "profiles:\n"
        "  dev:\n"
        "    jenkins:\n"
        "      url: https://jenkins.example.com\n"
    )
    from jctl.auth.api_token import APITokenAuthenticator

    APITokenAuthenticator().store_token("u", "t")

    client = get_jenkins_client(_ctx())
    assert client.url == "https://override.example.com"


# --- __main__.main ------------------------------------------------------


def test_main_returns_0_on_normal_exit(monkeypatch):
    """`jctl --version` etc. — cli() exits internally via Click, which
    raises SystemExit(0). The wrapper catches that and we return 0
    only in the "no exception" path; SystemExit propagates."""
    # `cli` with --version uses click.exit, which calls sys.exit. We
    # patch cli to do nothing so main() reaches its `return 0`.
    monkeypatch.setattr("jctl.__main__.cli", lambda obj: None)
    assert main() == 0


def test_main_returns_130_on_keyboard_interrupt(monkeypatch, capsys):
    """Ctrl+C maps to EXIT_USER_CANCELLED (130) — the conventional
    signal-derived code."""

    def _raise(obj):
        raise KeyboardInterrupt

    monkeypatch.setattr("jctl.__main__.cli", _raise)
    assert main() == EXIT_USER_CANCELLED
    assert "cancelled by user" in capsys.readouterr().out


def test_main_returns_1_on_unexpected_exception(monkeypatch, capsys):
    """A non-SystemExit exception is mapped to rc=1 with a stderr msg."""

    def _raise(obj):
        raise RuntimeError("oops")

    monkeypatch.setattr("jctl.__main__.cli", _raise)
    assert main() == 1
    captured = capsys.readouterr()
    # The message goes to stderr in main().
    assert "oops" in captured.err


def test_main_module_dunder_entry_point():
    """Smoke-check the `if __name__ == '__main__'` line by invoking the
    module file directly. The cli() call short-circuits with --help, so
    we never actually execute a command."""
    import subprocess

    result = subprocess.run(
        [sys.executable, "-m", "jctl", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "Jenkins Control CLI" in result.stdout
