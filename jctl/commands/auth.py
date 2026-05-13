"""Authentication commands for Jenkins API tokens."""

import sys

import click
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from jctl.auth.api_token import APITokenAuthenticator
from jctl.constants import EXIT_AUTH_ERROR, EXIT_GENERAL_ERROR
from jctl.utils.logging import get_logger
from jctl.utils.output import OutputFormatter

console = Console()
logger = get_logger(__name__)


@click.group()
def auth() -> None:
    """Manage Jenkins API token authentication."""
    pass


@auth.command()
@click.pass_context
def logout(ctx: click.Context) -> None:
    """Clear stored Jenkins credentials."""
    api_auth = APITokenAuthenticator()

    if not api_auth.is_authenticated():
        console.print("[yellow]Not currently authenticated[/yellow]")
        return

    try:
        api_auth.clear_token()
        console.print("[green]✓ Logged out successfully[/green]")
        console.print("[dim]Cleared: Jenkins API token[/dim]")
    except Exception as e:
        console.print(f"[red]Error during logout:[/red] {e}")
        sys.exit(EXIT_GENERAL_ERROR)


@auth.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show authentication status."""
    output_format = ctx.obj.get("output", "table")
    formatter = OutputFormatter(console)

    api_auth = APITokenAuthenticator()
    api_auth_info = api_auth.get_auth_info()

    if output_format == "json" or output_format == "yaml":
        formatter.format(api_auth_info, output_format)
        return

    console.print("[cyan]Authentication Status[/cyan]\n")

    if not api_auth_info["authenticated"]:
        console.print("[yellow]Not authenticated[/yellow]")
        console.print("Run 'jctl auth token' to configure a Jenkins API token")
        return

    table = Table(show_header=False, title="[bold]Jenkins API Token[/bold]")
    table.add_column("Property", style="cyan")
    table.add_column("Value")

    table.add_row("Status", "[green]✓ Configured[/green]")
    table.add_row("Username", api_auth_info["username"] or "Unknown")
    table.add_row("Has Token", "✓" if api_auth_info["has_token"] else "✗")

    console.print(table)


@auth.command()
@click.option("--username", help="Jenkins username (your email)")
@click.option("--token", help="Jenkins API token")
@click.pass_context
def token(ctx: click.Context, username: str | None, token: str | None) -> None:
    """Configure Jenkins API token authentication."""
    api_auth = APITokenAuthenticator()

    if api_auth.is_authenticated() and not username and not token:
        console.print("[yellow]API token already configured![/yellow]")
        console.print("Run 'jctl auth status' to see details")
        console.print("Run 'jctl auth logout' to clear and reconfigure")
        return

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
