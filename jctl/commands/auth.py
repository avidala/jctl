"""Authentication commands for Okta SSO and API tokens."""

import sys

import click
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from jctl.auth.api_token import APITokenAuthenticator
from jctl.auth.okta import OktaAuthenticator, OktaAuthError
from jctl.auth.token_manager import TokenManager
from jctl.config.manager import ConfigManager
from jctl.constants import (
    EXIT_AUTH_ERROR,
    EXIT_CONFIG_ERROR,
    EXIT_GENERAL_ERROR,
    EXIT_USER_CANCELLED,
)
from jctl.utils.logging import get_logger
from jctl.utils.output import OutputFormatter, format_duration

console = Console()
logger = get_logger(__name__)


def get_authenticator(ctx: click.Context) -> OktaAuthenticator:
    """Get Okta authenticator from config.

    Args:
        ctx: Click context

    Returns:
        OktaAuthenticator instance
    """
    try:
        config_manager = ConfigManager()
        config = config_manager.get()
        profile = config.get_profile(ctx.obj.get("profile"))

        return OktaAuthenticator(
            domain=profile.okta.domain,
            client_id=profile.okta.client_id,
            redirect_uri=profile.okta.redirect_uri,
            scopes=profile.okta.scopes,
        )
    except Exception as e:
        console.print(f"[red]Configuration error:[/red] {e}")
        console.print("Run 'jctl config init' to set up configuration")
        sys.exit(EXIT_CONFIG_ERROR)


@click.group()
def auth() -> None:
    """Manage authentication with Okta SSO."""
    pass


@auth.command()
@click.pass_context
def login(ctx: click.Context) -> None:
    """Login with Okta SSO authentication."""
    debug = ctx.obj.get("debug", False)

    authenticator = get_authenticator(ctx)

    # Check if already authenticated
    if authenticator.is_authenticated():
        console.print("[yellow]Already authenticated![/yellow]")
        console.print("Run 'jctl auth status' to see details")
        console.print("Run 'jctl auth logout' to clear current session")
        return

    try:
        # Perform OAuth login
        tokens = authenticator.login()

        console.print()
        console.print("[green]✓ Successfully authenticated![/green]")

        # Get user info
        try:
            user_info = authenticator.get_user_info()
            console.print(f"[dim]Logged in as: {user_info.get('email', 'Unknown')}[/dim]")
        except Exception as e:
            logger.debug(f"Could not retrieve user info: {e}")

        if debug:
            console.print(
                f"[dim]Token expires in: {tokens.get('expires_in', 'unknown')} seconds[/dim]"
            )

    except OktaAuthError as e:
        console.print(f"[red]Authentication failed:[/red] {e}")
        sys.exit(EXIT_AUTH_ERROR)
    except KeyboardInterrupt:
        console.print("\n[yellow]Authentication cancelled[/yellow]")
        sys.exit(EXIT_USER_CANCELLED)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        if debug:
            raise
        sys.exit(EXIT_GENERAL_ERROR)


@auth.command()
@click.pass_context
def logout(ctx: click.Context) -> None:
    """Logout and clear stored credentials."""
    # Check both authentication methods
    api_auth = APITokenAuthenticator()
    has_api_token = api_auth.is_authenticated()

    token_manager = TokenManager()
    has_oauth = token_manager.get_tokens() is not None

    if not has_oauth and not has_api_token:
        console.print("[yellow]Not currently authenticated[/yellow]")
        return

    try:
        cleared_items = []

        # Clear OAuth tokens if present
        if has_oauth:
            authenticator = get_authenticator(ctx)
            authenticator.logout()
            cleared_items.append("OAuth tokens")

        # Clear API token if present
        if has_api_token:
            api_auth.clear_token()
            cleared_items.append("Jenkins API token")

        console.print("[green]✓ Logged out successfully[/green]")
        console.print(f"[dim]Cleared: {', '.join(cleared_items)}[/dim]")
    except Exception as e:
        console.print(f"[red]Error during logout:[/red] {e}")
        sys.exit(EXIT_GENERAL_ERROR)


@auth.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show authentication status."""
    output_format = ctx.obj.get("output", "table")
    formatter = OutputFormatter(console)

    # Check both OAuth and API token authentication
    api_auth = APITokenAuthenticator()
    api_auth_info = api_auth.get_auth_info()

    token_manager = TokenManager()
    token_info = token_manager.get_token_info()

    # Combine auth info for JSON/YAML output
    combined_info = {
        **token_info,
        "api_token": api_auth_info,
    }

    if output_format == "json" or output_format == "yaml":
        formatter.format(combined_info, output_format)
        return

    # Table format
    console.print("[cyan]Authentication Status[/cyan]\n")

    # Check if any authentication method is available
    has_oauth = token_info["has_tokens"]
    has_api_token = api_auth_info["authenticated"]

    if not has_oauth and not has_api_token:
        console.print("[yellow]Not authenticated[/yellow]")
        console.print("Authentication options:")
        console.print("  • Run 'jctl auth login' for Okta SSO (recommended)")
        console.print("  • Run 'jctl auth token' for Jenkins API token")
        return

    # Show OAuth status if available
    if has_oauth:
        table = Table(show_header=False, title="[bold]OAuth (Okta SSO)[/bold]")
        table.add_column("Property", style="cyan")
        table.add_column("Value")

        status_emoji = "✓" if token_info["authenticated"] else "✗"
        status_color = "green" if token_info["authenticated"] else "red"
        status_text = "Authenticated" if token_info["authenticated"] else "Token Expired"

        table.add_row("Status", f"[{status_color}]{status_emoji} {status_text}[/{status_color}]")
        table.add_row("Has Access Token", "✓" if token_info["has_access_token"] else "✗")
        table.add_row("Has Refresh Token", "✓" if token_info["has_refresh_token"] else "✗")

        if token_info.get("expires_in"):
            expires_in = token_info["expires_in"]
            if expires_in > 0:
                table.add_row("Expires In", format_duration(expires_in * 1000))
            else:
                table.add_row("Expires In", "[red]Expired[/red]")

        console.print(table)
        console.print()

        # Try to get user info if authenticated
        if token_info["authenticated"]:
            try:
                authenticator = get_authenticator(ctx)
                user_info = authenticator.get_user_info()
                console.print(f"[cyan]Logged in as:[/cyan] {user_info.get('email', 'Unknown')}")
                if user_info.get("name"):
                    console.print(f"[dim]Name: {user_info['name']}[/dim]")
            except Exception as e:
                logger.debug(f"Could not retrieve OAuth user info: {e}")
        console.print()

    # Show API token status if available
    if has_api_token:
        table = Table(show_header=False, title="[bold]Jenkins API Token[/bold]")
        table.add_column("Property", style="cyan")
        table.add_column("Value")

        table.add_row("Status", "[green]✓ Configured[/green]")
        table.add_row("Username", api_auth_info["username"] or "Unknown")
        table.add_row("Has Token", "✓" if api_auth_info["has_token"] else "✗")

        console.print(table)
        console.print()


@auth.command()
@click.option("--username", help="Jenkins username (your email)")
@click.option("--token", help="Jenkins API token")
@click.pass_context
def token(ctx: click.Context, username: str | None, token: str | None) -> None:
    """Login with Jenkins API token (simpler alternative to OAuth)."""
    api_auth = APITokenAuthenticator()

    # Check if already configured
    if api_auth.is_authenticated() and not username and not token:
        console.print("[yellow]API token already configured![/yellow]")
        console.print("Run 'jctl auth status' to see details")
        console.print("Run 'jctl auth logout' to clear and reconfigure")
        return

    # Prompt for credentials if not provided
    if not username:
        console.print("\n[cyan]Jenkins API Token Authentication[/cyan]\n")
        console.print("You can get your API token from Jenkins:")
        console.print("  1. Log into Jenkins")
        console.print("  2. Click your name (top right) → Configure")
        console.print("  3. Scroll to 'API Token' → Add new Token")
        console.print("  4. Copy the generated token\n")

        username = Prompt.ask("Jenkins username (email)", default=api_auth.get_username() or "")

    if not token:
        from jctl.utils.password_prompt import password_prompt_rich

        token = password_prompt_rich("Jenkins API token")

    if not username or not token:
        console.print("[red]Error:[/red] Both username and token are required")
        sys.exit(EXIT_GENERAL_ERROR)

    try:
        # Store the token
        api_auth.store_token(username, token)

        console.print()
        console.print("[green]✓ API token configured successfully![/green]")
        console.print(f"[dim]Username: {username}[/dim]")
        console.print()
        console.print("[cyan]You can now use Jenkins commands:[/cyan]")
        console.print("  jctl pipeline list")
        console.print("  jctl job trigger <job-name>")

    except Exception as e:
        console.print(f"[red]Error storing token:[/red] {e}")
        sys.exit(EXIT_AUTH_ERROR)


@auth.command()
@click.pass_context
def refresh(ctx: click.Context) -> None:
    """Force token refresh."""
    authenticator = get_authenticator(ctx)
    token_manager = TokenManager()

    if not token_manager.get_refresh_token():
        console.print("[red]Error:[/red] No refresh token available")
        console.print("Please login again with 'jctl auth login'")
        sys.exit(EXIT_AUTH_ERROR)

    console.print("[cyan]Refreshing authentication token...[/cyan]")

    try:
        tokens = authenticator.refresh_tokens()
        console.print("[green]✓ Token refreshed successfully[/green]")

        if tokens.get("expires_in"):
            console.print(
                f"[dim]New token expires in: {format_duration(tokens['expires_in'] * 1000)}[/dim]"
            )

    except OktaAuthError as e:
        console.print(f"[red]Refresh failed:[/red] {e}")
        console.print("Please login again with 'jctl auth login'")
        sys.exit(EXIT_AUTH_ERROR)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        sys.exit(EXIT_GENERAL_ERROR)
