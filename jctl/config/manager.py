"""Configuration management."""

import os
from pathlib import Path
from typing import Any

import yaml

from jctl.config.schemas import Config, DefaultsConfig, JenkinsConfig, OktaConfig, ProfileConfig


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
        # Set directory permissions to 0700 (user only)
        self.config_dir.chmod(0o700)

    def load(self) -> Config:
        """Load configuration from file.

        Returns:
            Loaded configuration

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValidationError: If config is invalid
        """
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
        """Save configuration to file.

        Args:
            config: Configuration to save
        """
        self.ensure_config_dir()

        # Convert to dict and save as YAML
        data = config.model_dump(mode="json", exclude_none=True)

        with open(self.config_file, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        # Set file permissions to 0600 (user read/write only)
        self.config_file.chmod(0o600)

        self._config = config

    def get(self) -> Config:
        """Get current configuration, loading if necessary.

        Returns:
            Current configuration
        """
        if self._config is None:
            self._config = self.load()
        return self._config

    def exists(self) -> bool:
        """Check if configuration file exists.

        Returns:
            True if config file exists
        """
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

        # Special handling for profile-specific keys
        if parts[0] in config.profiles:
            profile = config.profiles[parts[0]]
            value = profile
            for part in parts[1:]:
                value = getattr(value, part)
            return value

        # Default handling
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
            key: Configuration key (e.g., 'defaults.timeout' or 'production.okta.client_id')
            value: Value to set
        """
        config = self.get()
        parts = key.split(".")

        # Special handling for profile-specific keys (e.g., production.okta.client_id)
        if parts[0] == "profiles" or parts[0] in config.profiles:
            # Handle: production.okta.client_id -> profiles.production.okta.client_id
            if parts[0] != "profiles":
                parts.insert(0, "profiles")

            # Navigate through the config structure
            obj: Any = config
            for part in parts[:-1]:
                if isinstance(obj, dict):
                    obj = obj[part]
                else:
                    obj = getattr(obj, part)

            # Set the value
            last_key = parts[-1]
            setattr(obj, last_key, value)
        else:
            # Regular key navigation
            obj: Any = config
            for part in parts[:-1]:
                if isinstance(obj, dict):
                    obj = obj[part]
                else:
                    obj = getattr(obj, part)

            # Set the value
            last_key = parts[-1]
            if isinstance(obj, dict):
                obj[last_key] = value
            else:
                setattr(obj, last_key, value)

        self.save(config)

    def create_default_config(self) -> Config:
        """Create a default configuration.

        Returns:
            Default configuration object
        """
        # Create default profile
        default_profile = ProfileConfig(
            jenkins=JenkinsConfig(url="https://jenkins.example.com"),
            okta=OktaConfig(domain="company.okta.com", client_id="jenkins-cli"),
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
        """Initialize configuration interactively.

        Returns:
            Created configuration
        """
        from rich.console import Console
        from rich.prompt import Confirm, Prompt

        console = Console()

        console.print("[cyan]Initializing jctl configuration...[/cyan]\n")

        # Ask for profile name
        console.print("[bold]Profile Setup:[/bold]")
        profile_name = Prompt.ask("Profile name", default="production")

        # Ask about authentication method
        console.print("\n[bold]Choose authentication method:[/bold]")
        console.print("  1. API Token - Simple, uses Jenkins username and API token")
        console.print("  2. Okta OAuth - SSO integration with Okta")
        console.print()

        auth_method = Prompt.ask(
            "Authentication method", choices=["1", "2", "token", "okta"], default="1"
        )

        use_okta = auth_method in ["2", "okta"]

        # Get Jenkins URL
        console.print()
        jenkins_url = Prompt.ask("Jenkins URL", default="https://jenkins.example.com")

        # Get Okta configuration only if using OAuth
        if use_okta:
            console.print("\n[cyan]Okta OAuth Configuration:[/cyan]")
            okta_domain = Prompt.ask("Okta domain", default="company.okta.com")
            okta_client_id = Prompt.ask("Okta client ID", default="jenkins-cli")
            # Only ask about SSL for OAuth since it's more complex
            verify_ssl = Confirm.ask("\nVerify SSL certificates?", default=True)
        else:
            okta_domain = "not-configured.okta.com"
            okta_client_id = "not-configured"
            # Always verify SSL for token auth (simpler, more secure)
            verify_ssl = True

        # Create profile
        profile = ProfileConfig(
            jenkins=JenkinsConfig(url=jenkins_url, verify_ssl=verify_ssl),
            okta=OktaConfig(domain=okta_domain, client_id=okta_client_id),
        )

        # Create config
        config = Config(
            version="1.0",
            default_profile=profile_name,
            profiles={profile_name: profile},
            defaults=DefaultsConfig(),
            aliases={},
        )

        # Save config
        self.save(config)

        console.print(f"\n[green]✓[/green] Configuration saved to: {self.config_file}")
        console.print(f"[green]✓[/green] Profile '{profile_name}' created and set as default")

        # Authenticate immediately for API token
        if not use_okta:
            console.print("\n[cyan]Authentication Setup:[/cyan]")
            console.print("Let's set up your Jenkins API token now.\n")

            # Import and use the API token authenticator
            from jctl.auth.api_token import APITokenAuthenticator

            api_auth = APITokenAuthenticator()
            username = Prompt.ask("Jenkins username")

            # Use custom password prompt (shows asterisks)
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
        else:
            # Show next steps for OAuth
            console.print("\n[cyan]Next steps:[/cyan]")
            console.print("  1. Authenticate with API token: [bold]jctl auth token[/bold]")
            console.print("  2. Or authenticate with Okta OAuth: [bold]jctl auth login[/bold]")
            console.print("\n  Then start using jctl:")
            console.print("    [bold]jctl pipeline list[/bold]")
            console.print("    [bold]jctl pipeline run <pipeline-name>[/bold]")

        return config

    def init_interactive_add_profile(self) -> Config:
        """Add a new profile to existing configuration interactively.

        Returns:
            Updated configuration
        """
        from rich.console import Console
        from rich.prompt import Confirm, Prompt

        console = Console()

        console.print("[cyan]Initializing jctl configuration...[/cyan]\n")

        # Load existing config
        config = self.get()

        # Ask for profile name
        console.print("[bold]Profile Setup:[/bold]")
        while True:
            profile_name = Prompt.ask("Profile name", default="production")

            # Check if profile already exists
            if profile_name in config.profiles:
                console.print(f"[yellow]Warning:[/yellow] Profile '{profile_name}' already exists")
                if Confirm.ask("Overwrite this profile?"):
                    break
                # Ask for a different name
                continue
            break

        # Ask about authentication method
        console.print("\n[bold]Choose authentication method:[/bold]")
        console.print("  1. API Token - Simple, uses Jenkins username and API token")
        console.print("  2. Okta OAuth - SSO integration with Okta")
        console.print()

        auth_method = Prompt.ask(
            "Authentication method", choices=["1", "2", "token", "okta"], default="1"
        )

        use_okta = auth_method in ["2", "okta"]

        # Get Jenkins URL
        console.print()
        jenkins_url = Prompt.ask("Jenkins URL", default="https://jenkins.example.com")

        # Get Okta configuration only if using OAuth
        if use_okta:
            console.print("\n[cyan]Okta OAuth Configuration:[/cyan]")
            okta_domain = Prompt.ask("Okta domain", default="company.okta.com")
            okta_client_id = Prompt.ask("Okta client ID", default="jenkins-cli")
            # Only ask about SSL for OAuth since it's more complex
            verify_ssl = Confirm.ask("\nVerify SSL certificates?", default=True)
        else:
            okta_domain = "not-configured.okta.com"
            okta_client_id = "not-configured"
            # Always verify SSL for token auth (simpler, more secure)
            verify_ssl = True

        # Create profile
        profile = ProfileConfig(
            jenkins=JenkinsConfig(url=jenkins_url, verify_ssl=verify_ssl),
            okta=OktaConfig(domain=okta_domain, client_id=okta_client_id),
        )

        # Add profile to existing config
        config.profiles[profile_name] = profile

        # Ask if this should be the default
        if Confirm.ask(f"\nSet '{profile_name}' as default profile?", default=False):
            config.default_profile = profile_name

        # Save config
        self.save(config)

        console.print(f"\n[green]✓[/green] Configuration saved to: {self.config_file}")
        console.print(f"[green]✓[/green] Profile '{profile_name}' added")
        if config.default_profile == profile_name:
            console.print("[green]✓[/green] Set as default profile")

        # Authenticate immediately for API token
        if not use_okta:
            console.print("\n[cyan]Authentication Setup:[/cyan]")
            console.print("Let's set up your Jenkins API token now.\n")

            # Import and use the API token authenticator
            from jctl.auth.api_token import APITokenAuthenticator

            api_auth = APITokenAuthenticator()
            username = Prompt.ask("Jenkins username")

            # Use custom password prompt (shows asterisks)
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
        else:
            # Show next steps for OAuth
            console.print("\n[cyan]Next steps:[/cyan]")
            console.print(
                f"  1. Authenticate with API token: [bold]jctl --profile {profile_name} auth token[/bold]"
            )
            console.print(
                f"  2. Or authenticate with Okta OAuth: [bold]jctl --profile {profile_name} auth login[/bold]"
            )
            console.print("\n  Then start using jctl:")
            console.print(f"    [bold]jctl --profile {profile_name} pipeline list[/bold]")

        return config

    def get_env_overrides(self) -> dict[str, Any]:
        """Get configuration overrides from environment variables.

        Returns:
            Dict of environment variable overrides
        """
        overrides: dict[str, Any] = {}

        # Map environment variables to config keys
        env_mappings = {
            "JCTL_PROFILE": "profile",
            "JCTL_JENKINS_URL": "jenkins.url",
            "JCTL_OKTA_DOMAIN": "okta.domain",
            "JCTL_OKTA_CLIENT_ID": "okta.client_id",
            "JCTL_OUTPUT_FORMAT": "output.format",
            "JCTL_LOG_LEVEL": "defaults.log_level",
            "JCTL_NO_COLOR": "output.color",
        }

        for env_var, config_key in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                # Special handling for JCTL_NO_COLOR
                if env_var == "JCTL_NO_COLOR":
                    overrides[config_key] = "never" if value == "1" else "auto"
                else:
                    overrides[config_key] = value

        return overrides
