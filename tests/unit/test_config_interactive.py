"""Coverage for the interactive flows in ConfigManager.

`init_interactive` and `init_interactive_add_profile` chain through
`rich.prompt.Prompt.ask` / `Confirm.ask` and `password_prompt_rich`.
We mock those three to drive the flow deterministically and verify
the produced config + the calls to `APITokenAuthenticator.store_token`.

Also covers `ConfigManager.get_env_overrides` — the JCTL_* env-var
mapping table that was previously untested.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from jctl.config.manager import ConfigManager


@pytest.fixture
def manager(tmp_path: Path) -> ConfigManager:
    """A ConfigManager rooted at tmp_path/.jctl. Tests that need a
    pre-seeded config build one first with `manager.save(...)`."""
    return ConfigManager(config_dir=tmp_path / ".jctl")


def _prompt_returning(*answers: str):
    """Build a side_effect list for `Prompt.ask` that returns the
    given answers in order. Extra calls return the last answer."""
    answers = list(answers)

    def _ask(*_args, **_kwargs):
        return answers.pop(0) if answers else _ask.last

    _ask.last = answers[-1] if answers else ""
    return _ask


# --- init_interactive ---------------------------------------------------


def test_init_interactive_creates_profile_and_stores_token(manager):
    """Happy path: user enters profile name + URL + username + token,
    config is written, token is stored."""
    with (
        patch("rich.prompt.Prompt.ask") as mock_prompt,
        patch("jctl.utils.password_prompt.password_prompt_rich", return_value="s3cret"),
        patch("jctl.auth.api_token.APITokenAuthenticator") as mock_auth,
    ):
        mock_prompt.side_effect = [
            "production",  # profile name
            "https://jenkins.example.com",  # Jenkins URL
            "user@example.com",  # username
        ]
        config = manager.init_interactive()

    # Config is saved + on-disk.
    assert manager.config_file.exists()
    assert config.default_profile == "production"
    assert "production" in config.profiles
    # Token store hit with the right args.
    mock_auth.return_value.store_token.assert_called_once_with("user@example.com", "s3cret")


def test_init_interactive_with_non_default_profile_name(manager, capsys):
    """A non-'production' profile triggers the 'use explicit profile'
    hint in the final summary."""
    with (
        patch("rich.prompt.Prompt.ask") as mock_prompt,
        patch("jctl.utils.password_prompt.password_prompt_rich", return_value="t"),
        patch("jctl.auth.api_token.APITokenAuthenticator"),
    ):
        mock_prompt.side_effect = ["staging", "https://x", "u"]
        manager.init_interactive()

    out = capsys.readouterr().out
    assert "--profile staging" in out


def test_init_interactive_token_save_failure_is_warned_not_fatal(manager, capsys):
    """If store_token raises (e.g. keyring locked), the flow finishes
    with a Warning and a hint to run `jctl auth token` later."""
    with (
        patch("rich.prompt.Prompt.ask") as mock_prompt,
        patch("jctl.utils.password_prompt.password_prompt_rich", return_value="t"),
        patch("jctl.auth.api_token.APITokenAuthenticator") as mock_auth,
    ):
        mock_auth.return_value.store_token.side_effect = RuntimeError("keyring locked")
        mock_prompt.side_effect = ["production", "https://x", "u"]
        config = manager.init_interactive()

    # Config still saved; warning surfaced.
    assert manager.config_file.exists()
    assert config.profiles  # has the new profile
    out = capsys.readouterr().out
    assert "Could not save token" in out
    assert "jctl auth token" in out


# --- init_interactive_add_profile ---------------------------------------


def test_add_profile_to_existing_config_via_interactive(manager):
    """User runs `config init` against an existing config — we land in
    init_interactive_add_profile, which appends a new profile."""
    # Seed an existing config first.
    with (
        patch("rich.prompt.Prompt.ask") as mock_prompt,
        patch("jctl.utils.password_prompt.password_prompt_rich", return_value="t1"),
        patch("jctl.auth.api_token.APITokenAuthenticator"),
    ):
        mock_prompt.side_effect = ["production", "https://prod", "u"]
        manager.init_interactive()

    # Now add a 'staging' profile.
    with (
        patch("rich.prompt.Prompt.ask") as mock_prompt,
        patch("rich.prompt.Confirm.ask") as mock_confirm,
        patch("jctl.utils.password_prompt.password_prompt_rich", return_value="t2"),
        patch("jctl.auth.api_token.APITokenAuthenticator") as mock_auth,
    ):
        mock_prompt.side_effect = ["staging", "https://staging", "u2"]
        mock_confirm.return_value = False  # don't make it default
        config = manager.init_interactive_add_profile()

    assert "production" in config.profiles
    assert "staging" in config.profiles
    # Default still production (we said "no" to the prompt).
    assert config.default_profile == "production"
    mock_auth.return_value.store_token.assert_called_once_with("u2", "t2")


def test_add_profile_overwrite_existing_when_confirmed(manager):
    """Entering a profile name that already exists prompts Overwrite?;
    answering yes proceeds and overwrites."""
    with (
        patch("rich.prompt.Prompt.ask") as mock_prompt,
        patch("jctl.utils.password_prompt.password_prompt_rich", return_value="t"),
        patch("jctl.auth.api_token.APITokenAuthenticator"),
    ):
        mock_prompt.side_effect = ["production", "https://old", "u"]
        manager.init_interactive()

    # Re-enter 'production' on add → Overwrite? yes → proceed.
    with (
        patch("rich.prompt.Prompt.ask") as mock_prompt,
        patch("rich.prompt.Confirm.ask") as mock_confirm,
        patch("jctl.utils.password_prompt.password_prompt_rich", return_value="new-tok"),
        patch("jctl.auth.api_token.APITokenAuthenticator"),
    ):
        mock_prompt.side_effect = ["production", "https://new", "u"]
        # First Confirm = Overwrite?, second Confirm = set as default?
        mock_confirm.side_effect = [True, False]
        config = manager.init_interactive_add_profile()

    assert str(config.profiles["production"].jenkins.url).rstrip("/") == "https://new"


def test_add_profile_overwrite_declined_then_use_different_name(manager):
    """Overwrite? declined re-loops the prompt for a fresh name."""
    with (
        patch("rich.prompt.Prompt.ask") as mock_prompt,
        patch("jctl.utils.password_prompt.password_prompt_rich", return_value="t"),
        patch("jctl.auth.api_token.APITokenAuthenticator"),
    ):
        mock_prompt.side_effect = ["production", "https://prod", "u"]
        manager.init_interactive()

    with (
        patch("rich.prompt.Prompt.ask") as mock_prompt,
        patch("rich.prompt.Confirm.ask") as mock_confirm,
        patch("jctl.utils.password_prompt.password_prompt_rich", return_value="t"),
        patch("jctl.auth.api_token.APITokenAuthenticator"),
    ):
        # First "production" → conflict; second "qa" → accepted.
        mock_prompt.side_effect = ["production", "qa", "https://qa", "u"]
        # Overwrite? = no; set as default? = no.
        mock_confirm.side_effect = [False, False]
        config = manager.init_interactive_add_profile()

    assert "qa" in config.profiles


def test_add_profile_can_become_default(manager):
    """'Set as default profile?' = yes flips default_profile."""
    with (
        patch("rich.prompt.Prompt.ask") as mock_prompt,
        patch("jctl.utils.password_prompt.password_prompt_rich", return_value="t"),
        patch("jctl.auth.api_token.APITokenAuthenticator"),
    ):
        mock_prompt.side_effect = ["production", "https://prod", "u"]
        manager.init_interactive()

    with (
        patch("rich.prompt.Prompt.ask") as mock_prompt,
        patch("rich.prompt.Confirm.ask", return_value=True),
        patch("jctl.utils.password_prompt.password_prompt_rich", return_value="t"),
        patch("jctl.auth.api_token.APITokenAuthenticator"),
    ):
        mock_prompt.side_effect = ["staging", "https://staging", "u"]
        config = manager.init_interactive_add_profile()

    assert config.default_profile == "staging"


def test_add_profile_token_save_failure_is_warned(manager, capsys):
    with (
        patch("rich.prompt.Prompt.ask") as mock_prompt,
        patch("jctl.utils.password_prompt.password_prompt_rich", return_value="t"),
        patch("jctl.auth.api_token.APITokenAuthenticator"),
    ):
        mock_prompt.side_effect = ["production", "https://prod", "u"]
        manager.init_interactive()

    with (
        patch("rich.prompt.Prompt.ask") as mock_prompt,
        patch("rich.prompt.Confirm.ask", return_value=False),
        patch("jctl.utils.password_prompt.password_prompt_rich", return_value="t"),
        patch("jctl.auth.api_token.APITokenAuthenticator") as mock_auth,
    ):
        mock_auth.return_value.store_token.side_effect = RuntimeError("keyring locked")
        mock_prompt.side_effect = ["staging", "https://staging", "u"]
        manager.init_interactive_add_profile()

    out = capsys.readouterr().out
    assert "Could not save token" in out
    assert "--profile staging" in out


# --- create_default_config ---------------------------------------------


def test_create_default_config_returns_runnable_shape(manager):
    """A bare-bones helper used by some callers. Just verify it produces
    a valid Config with the expected default profile name."""
    cfg = manager.create_default_config()
    assert cfg.default_profile == "production"
    assert "production" in cfg.profiles


# --- get_env_overrides --------------------------------------------------


def test_get_env_overrides_empty_when_no_vars_set(manager, monkeypatch):
    for var in (
        "JCTL_PROFILE",
        "JCTL_JENKINS_URL",
        "JCTL_OUTPUT_FORMAT",
        "JCTL_LOG_LEVEL",
        "JCTL_NO_COLOR",
    ):
        monkeypatch.delenv(var, raising=False)
    assert manager.get_env_overrides() == {}


def test_get_env_overrides_maps_each_var(manager, monkeypatch):
    monkeypatch.setenv("JCTL_PROFILE", "staging")
    monkeypatch.setenv("JCTL_JENKINS_URL", "https://j")
    monkeypatch.setenv("JCTL_OUTPUT_FORMAT", "json")
    monkeypatch.setenv("JCTL_LOG_LEVEL", "DEBUG")

    overrides = manager.get_env_overrides()
    assert overrides == {
        "profile": "staging",
        "jenkins.url": "https://j",
        "output.format": "json",
        "defaults.log_level": "DEBUG",
    }


def test_get_env_overrides_no_color_normalizes_to_never(manager, monkeypatch):
    """JCTL_NO_COLOR=1 → 'never'; any other truthy value → 'auto' (so the
    user has an escape hatch if Rich's auto-detect goes wrong)."""
    monkeypatch.setenv("JCTL_NO_COLOR", "1")
    assert manager.get_env_overrides()["output.color"] == "never"

    monkeypatch.setenv("JCTL_NO_COLOR", "yes")
    assert manager.get_env_overrides()["output.color"] == "auto"
