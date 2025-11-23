"""Configuration management commands."""

import sys

import click
from rich.console import Console

from jctl.config.manager import ConfigManager
from jctl.constants import EXIT_CONFIG_ERROR
from jctl.utils.output import OutputFormatter

console = Console()


@click.group()
def config() -> None:
    """Manage jctl configuration."""
    pass


@config.command()
@click.option("--force", is_flag=True, help="Overwrite entire configuration file")
@click.pass_context
def init(ctx: click.Context, force: bool) -> None:
    """Initialize configuration with interactive setup.

    If config already exists, this will ADD a new profile.
    Use --force to completely overwrite the config file.
    """
    manager = ConfigManager()

    if manager.exists() and force:
        console.print("[yellow]Warning:[/yellow] This will overwrite your entire configuration!")
        from rich.prompt import Confirm

        if not Confirm.ask("Are you sure?"):
            console.print("Aborted")
            sys.exit(0)

    try:
        # If config exists and not forcing, add a profile instead
        if manager.exists() and not force:
            console.print("[cyan]Adding new profile to existing configuration...[/cyan]\n")
            manager.init_interactive_add_profile()
        else:
            # Fresh init or force overwrite
            manager.init_interactive()

        console.print()
        console.print("[green]✓[/green] Configuration saved successfully")
        console.print(f"[dim]Config file: {manager.config_file}[/dim]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(EXIT_CONFIG_ERROR)


@config.command()
@click.argument("key")
@click.argument("value")
@click.pass_context
def set(ctx: click.Context, key: str, value: str) -> None:  # noqa: A001
    """Set a configuration value."""
    manager = ConfigManager()

    try:
        manager.set_value(key, value)
        console.print(f"[green]✓[/green] Set {key} = {value}")
    except FileNotFoundError:
        console.print("[red]Error:[/red] Configuration not found")
        console.print("Run 'jctl config init' first")
        sys.exit(EXIT_CONFIG_ERROR)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(EXIT_CONFIG_ERROR)


@config.command()
@click.argument("key")
@click.pass_context
def get(ctx: click.Context, key: str) -> None:
    """Get a configuration value."""
    manager = ConfigManager()
    output_format = ctx.obj.get("output", "table")

    try:
        value = manager.get_value(key)

        if output_format == "plain":
            console.print(value)
        else:
            console.print(f"{key} = [cyan]{value}[/cyan]")

    except FileNotFoundError:
        console.print("[red]Error:[/red] Configuration not found")
        console.print("Run 'jctl config init' first")
        sys.exit(EXIT_CONFIG_ERROR)
    except KeyError:
        console.print(f"[red]Error:[/red] Configuration key not found: {key}")
        sys.exit(EXIT_CONFIG_ERROR)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(EXIT_CONFIG_ERROR)


@config.command()
@click.pass_context
def list(ctx: click.Context) -> None:  # noqa: A001
    """List all configuration values."""
    manager = ConfigManager()
    output_format = ctx.obj.get("output", "table")

    try:
        config = manager.get()
        formatter = OutputFormatter(console)

        # Convert config to dict for display
        config_dict = config.model_dump(mode="json", exclude_none=True)

        formatter.format(config_dict, output_format)

    except FileNotFoundError:
        console.print("[red]Error:[/red] Configuration not found")
        console.print("Run 'jctl config init' first")
        sys.exit(EXIT_CONFIG_ERROR)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(EXIT_CONFIG_ERROR)


@config.command()
@click.pass_context
def show(ctx: click.Context) -> None:
    """Show full configuration file."""
    manager = ConfigManager()

    try:
        if not manager.config_file.exists():
            console.print("[red]Error:[/red] Configuration not found")
            console.print("Run 'jctl config init' first")
            sys.exit(EXIT_CONFIG_ERROR)

        console.print(f"[cyan]Configuration file:[/cyan] {manager.config_file}")
        console.print()

        # Read and display the YAML file
        with open(manager.config_file) as f:
            content = f.read()
            console.print(content)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(EXIT_CONFIG_ERROR)


@config.command("add-profile")
@click.argument("profile_name")
@click.option("--jenkins-url", required=True, help="Jenkins server URL")
@click.option(
    "--okta-domain", help="Okta domain (e.g., company.okta.com) - optional for API token auth"
)
@click.option("--okta-client-id", help="Okta OAuth client ID - optional for API token auth")
@click.option("--verify-ssl/--no-verify-ssl", default=True, help="Verify SSL certificates")
@click.option("--set-default", is_flag=True, help="Set as default profile")
@click.pass_context
def add_profile(
    ctx: click.Context,
    profile_name: str,
    jenkins_url: str,
    okta_domain: str | None,
    okta_client_id: str | None,
    verify_ssl: bool,
    set_default: bool,
) -> None:
    """Add a new configuration profile.

    You can create profiles with or without Okta OAuth configuration.
    If you only use API tokens, you can omit --okta-domain and --okta-client-id.

    Examples:
        # Profile with Okta OAuth
        jctl config add-profile dev \\
          --jenkins-url https://jenkins-dev.h2oai.com \\
          --okta-domain h2oai-dev.okta.com \\
          --okta-client-id jenkins-cli-dev

        # Profile with only API token auth (no Okta)
        jctl config add-profile dev \\
          --jenkins-url https://jenkins-dev.h2oai.com

        # Set as default profile
        jctl config add-profile stg \\
          --jenkins-url https://jenkins-stg.h2oai.com \\
          --set-default
    """
    from jctl.config.schemas import JenkinsConfig, OktaConfig, ProfileConfig

    manager = ConfigManager()

    try:
        config = manager.get()

        # Check if profile already exists
        if profile_name in config.profiles:
            console.print(f"[yellow]Warning:[/yellow] Profile '{profile_name}' already exists")
            from rich.prompt import Confirm

            if not Confirm.ask("Overwrite?"):
                console.print("Aborted")
                sys.exit(0)

        # Create Okta config if domain and client_id provided
        if okta_domain and okta_client_id:
            okta_config = OktaConfig(domain=okta_domain, client_id=okta_client_id)
        else:
            # Use default/placeholder Okta config for API token auth
            okta_config = OktaConfig(domain="not-configured.okta.com", client_id="not-configured")

        # Create new profile
        new_profile = ProfileConfig(
            jenkins=JenkinsConfig(url=jenkins_url, verify_ssl=verify_ssl),
            okta=okta_config,
        )

        # Add profile to config
        config.profiles[profile_name] = new_profile

        # Set as default if requested
        if set_default:
            config.default_profile = profile_name

        # Save config
        manager.save(config)

        console.print(f"[green]✓[/green] Profile '{profile_name}' added successfully")
        if set_default:
            console.print("[green]✓[/green] Set as default profile")

        console.print("\n[dim]To use this profile:[/dim]")
        console.print(f"  jctl --profile {profile_name} <command>")

        console.print("\n[dim]To authenticate:[/dim]")
        if okta_domain and okta_client_id:
            console.print(f"  jctl --profile {profile_name} auth token  # API token")
            console.print(f"  jctl --profile {profile_name} auth login  # Okta OAuth")
        else:
            console.print(f"  jctl --profile {profile_name} auth token  # API token only")
            console.print("\n[yellow]Note:[/yellow] Okta OAuth not configured for this profile.")
            console.print("       Use API token authentication or add Okta settings later.")

    except FileNotFoundError:
        console.print("[red]Error:[/red] Configuration not found")
        console.print("Run 'jctl config init' first")
        sys.exit(EXIT_CONFIG_ERROR)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(EXIT_CONFIG_ERROR)
