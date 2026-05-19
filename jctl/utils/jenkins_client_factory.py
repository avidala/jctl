"""Jenkins client factory for creating authenticated clients."""

import os
import sys

import click
from rich.console import Console

from jctl.auth.api_token import APITokenAuthenticator
from jctl.config.manager import ConfigManager
from jctl.jenkins.client import JenkinsClient
from jctl.utils.logging import get_logger

# Auth banner ("Using API token …") goes to stderr so json/yaml/plain
# consumers see only their data on stdout. Errors go to stdout's Console.
console = Console()
stderr_console = Console(stderr=True)
logger = get_logger(__name__)


def get_jenkins_client(ctx: click.Context) -> JenkinsClient:
    """Get authenticated Jenkins client using stored API token credentials.

    Args:
        ctx: Click context

    Returns:
        Authenticated JenkinsClient instance

    Raises:
        SystemExit: If no valid authentication found
    """
    try:
        config_manager = ConfigManager()
        config = config_manager.get()
        profile = config.get_profile(ctx.obj.get("profile"))

        # JCTL_JENKINS_URL lets the user point at a different Jenkins
        # without touching their config — useful for one-off commands
        # against e.g. a staging instance.
        jenkins_url = os.environ.get("JCTL_JENKINS_URL") or str(profile.jenkins.url)
        verify_ssl = profile.jenkins.verify_ssl

        api_auth = APITokenAuthenticator()
        if api_auth.is_authenticated():
            credentials = api_auth.get_credentials()
            assert credentials is not None  # guarded by is_authenticated
            username, token = credentials
            stderr_console.print(f"[dim]Using API token authentication as {username}[/dim]")
            return JenkinsClient(
                url=jenkins_url,
                username=username,
                password=token,
                verify_ssl=verify_ssl,
            )

        console.print("[red]Error:[/red] Not authenticated")
        console.print("\nPlease authenticate first:")
        console.print("  [cyan]jctl auth token[/cyan] - Configure a Jenkins API token")
        sys.exit(1)

    except FileNotFoundError:
        console.print("[red]Error:[/red] Configuration not found")
        console.print("Run [cyan]jctl config init[/cyan] to set up configuration")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
