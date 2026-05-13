"""Configuration management."""

import os
from pathlib import Path
from typing import Any

import yaml

from jctl.config.schemas import Config, DefaultsConfig, JenkinsConfig, ProfileConfig


class ConfigManager:
    """Manage jctl configuration."""

    def __init__(self, config_dir: Path | None = None):
        """Initialize config manager.

        Args:
            config_dir: Configuration directory. Defaults to ~/.jctl
        """
        self.config_dir = config_dir or Path.home() / ".jctl"
        self.config_file = self.config_dir / "config.yaml"
        self._config: Config | None = None

    def ensure_config_dir(self) -> None:
        """Ensure configuration directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.chmod(0o700)

    def load(self) -> Config:
        """Load configuration from file."""
        if not self.config_file.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_file}\n"
                "Run 'jctl config init' to create one"
            )

        with open(self.config_file) as f:
            data = yaml.safe_load(f)

        self._config = Config(**data)
        return self._config

    def save(self, config: Config) -> None:
        """Save configuration to file."""
        self.ensure_config_dir()

        data = config.model_dump(mode="json", exclude_none=True)

        with open(self.config_file, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        self.config_file.chmod(0o600)

        self._config = config

    def get(self) -> Config:
        """Get current configuration, loading if necessary."""
        if self._config is None:
            self._config = self.load()
        return self._config

    def exists(self) -> bool:
        """Check if configuration file exists."""
        return self.config_file.exists()

    def get_value(self, key: str) -> Any:
        """Get configuration value by dot-notation key.

        Args:
            key: Configuration key (e.g., 'jenkins.url', 'defaults.timeout')

        Returns:
            Configuration value

        Raises:
            KeyError: If key not found
        """
        config = self.get()
        parts = key.split(".")

        if parts[0] in config.profiles:
            profile = config.profiles[parts[0]]
            value = profile
            for part in parts[1:]:
                value = getattr(value, part)
            return value

        value: Any = config
        for part in parts:
            if isinstance(value, dict):
                value = value[part]
            else:
                value = getattr(value, part)

        return value

    def set_value(self, key: str, value: Any) -> None:
        """Set configuration value by dot-notation key.

        Args:
            key: Configuration key (e.g., 'defaults.timeout' or 'production.jenkins.url')
            value: Value to set
        """
        config = self.get()
        parts = key.split(".")

        if parts[0] == "profiles" or parts[0] in config.profiles:
            if parts[0] != "profiles":
                parts.insert(0, "profiles")

            obj: Any = config
            for part in parts[:-1]:
                if isinstance(obj, dict):
                    obj = obj[part]
                else:
                    obj = getattr(obj, part)

            last_key = parts[-1]
            setattr(obj, last_key, value)
        else:
            obj: Any = config
            for part in parts[:-1]:
                if isinstance(obj, dict):
                    obj = obj[part]
                else:
                    obj = getattr(obj, part)

            last_key = parts[-1]
            if isinstance(obj, dict):
                obj[last_key] = value
            else:
                setattr(obj, last_key, value)

        self.save(config)

    def create_default_config(self) -> Config:
        """Create a default configuration."""
        default_profile = ProfileConfig(
            jenkins=JenkinsConfig(url="https://jenkins.example.com"),
        )

        config = Config(
            version="1.0",
            default_profile="production",
            profiles={"production": default_profile},
            defaults=DefaultsConfig(),
            aliases={},
        )

        return config

    def init_interactive(self) -> Config:
        """Initialize configuration interactively."""
        from rich.console import Console
        from rich.prompt import Prompt

        console = Console()

        console.print("[cyan]Initializing jctl configuration...[/cyan]\n")

        console.print("[bold]Profile Setup:[/bold]")
        profile_name = Prompt.ask("Profile name", default="production")

        console.print()
        jenkins_url = Prompt.ask("Jenkins URL", default="https://jenkins.example.com")

        profile = ProfileConfig(
            jenkins=JenkinsConfig(url=jenkins_url, verify_ssl=True),
        )

        config = Config(
            version="1.0",
            default_profile=profile_name,
            profiles={profile_name: profile},
            defaults=DefaultsConfig(),
            aliases={},
        )

        self.save(config)

        console.print(f"\n[green]✓[/green] Configuration saved to: {self.config_file}")
        console.print(f"[green]✓[/green] Profile '{profile_name}' created and set as default")

        console.print("\n[cyan]Authentication Setup:[/cyan]")
        console.print("Let's set up your Jenkins API token now.\n")

        from jctl.auth.api_token import APITokenAuthenticator

        api_auth = APITokenAuthenticator()
        username = Prompt.ask("Jenkins username")

        from jctl.utils.password_prompt import password_prompt_rich

        token = password_prompt_rich("Jenkins API token")

        try:
            api_auth.store_token(username, token)
            console.print("\n[green]✓[/green] API token saved securely")

            console.print("\n[cyan]You're all set![/cyan] Try these commands:")
            console.print("  [bold]jctl pipeline list[/bold]")
            console.print("  [bold]jctl pipeline run <pipeline-name>[/bold]")

            if profile_name != "production":
                console.print("\n[dim]Or use explicit profile:[/dim]")
                console.print(f"  [bold]jctl --profile {profile_name} pipeline list[/bold]")
        except Exception as e:
            console.print(f"\n[yellow]Warning:[/yellow] Could not save token: {e}")
            console.print("You can authenticate later with: [bold]jctl auth token[/bold]")

        return config

    def init_interactive_add_profile(self) -> Config:
        """Add a new profile to existing configuration interactively."""
        from rich.console import Console
        from rich.prompt import Confirm, Prompt

        console = Console()

        console.print("[cyan]Adding profile to jctl configuration...[/cyan]\n")

        config = self.get()

        console.print("[bold]Profile Setup:[/bold]")
        while True:
            profile_name = Prompt.ask("Profile name", default="production")

            if profile_name in config.profiles:
                console.print(f"[yellow]Warning:[/yellow] Profile '{profile_name}' already exists")
                if Confirm.ask("Overwrite this profile?"):
                    break
                continue
            break

        console.print()
        jenkins_url = Prompt.ask("Jenkins URL", default="https://jenkins.example.com")

        profile = ProfileConfig(
            jenkins=JenkinsConfig(url=jenkins_url, verify_ssl=True),
        )

        config.profiles[profile_name] = profile

        if Confirm.ask(f"\nSet '{profile_name}' as default profile?", default=False):
            config.default_profile = profile_name

        self.save(config)

        console.print(f"\n[green]✓[/green] Configuration saved to: {self.config_file}")
        console.print(f"[green]✓[/green] Profile '{profile_name}' added")
        if config.default_profile == profile_name:
            console.print("[green]✓[/green] Set as default profile")

        console.print("\n[cyan]Authentication Setup:[/cyan]")
        console.print("Let's set up your Jenkins API token now.\n")

        from jctl.auth.api_token import APITokenAuthenticator

        api_auth = APITokenAuthenticator()
        username = Prompt.ask("Jenkins username")

        from jctl.utils.password_prompt import password_prompt_rich

        token = password_prompt_rich("Jenkins API token")

        try:
            api_auth.store_token(username, token)
            console.print("\n[green]✓[/green] API token saved securely")

            console.print("\n[cyan]You're all set![/cyan] Try these commands:")
            console.print(f"  [bold]jctl --profile {profile_name} pipeline list[/bold]")
            console.print(
                f"  [bold]jctl --profile {profile_name} pipeline run <pipeline-name>[/bold]"
            )

            if config.default_profile == profile_name:
                console.print("\n[dim]Or use without profile (uses default):[/dim]")
                console.print("  [bold]jctl pipeline list[/bold]")
        except Exception as e:
            console.print(f"\n[yellow]Warning:[/yellow] Could not save token: {e}")
            console.print(
                f"You can authenticate later with: [bold]jctl --profile {profile_name} auth token[/bold]"
            )

        return config

    def get_env_overrides(self) -> dict[str, Any]:
        """Get configuration overrides from environment variables."""
        overrides: dict[str, Any] = {}

        env_mappings = {
            "JCTL_PROFILE": "profile",
            "JCTL_JENKINS_URL": "jenkins.url",
            "JCTL_OUTPUT_FORMAT": "output.format",
            "JCTL_LOG_LEVEL": "defaults.log_level",
            "JCTL_NO_COLOR": "output.color",
        }

        for env_var, config_key in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                if env_var == "JCTL_NO_COLOR":
                    overrides[config_key] = "never" if value == "1" else "auto"
                else:
                    overrides[config_key] = value

        return overrides
