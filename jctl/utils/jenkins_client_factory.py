"""Jenkins client factory for creating authenticated clients."""

import sys

import click
from rich.console import Console

from jctl.auth.api_token import APITokenAuthenticator
from jctl.auth.okta import OktaAuthenticator
from jctl.auth.token_manager import TokenManager
from jctl.config.manager import ConfigManager
from jctl.jenkins.client import JenkinsClient
from jctl.utils.logging import get_logger

console = Console()
logger = get_logger(__name__)


def get_jenkins_client(ctx: click.Context) -> JenkinsClient:
    """Get authenticated Jenkins client.

    Tries API token first, then OAuth tokens.

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

        jenkins_url = str(profile.jenkins.url)
        verify_ssl = profile.jenkins.verify_ssl

        # Try API token first (simpler)
        api_auth = APITokenAuthenticator()
        if api_auth.is_authenticated():
            username, token = api_auth.get_credentials()
            console.print(f"[dim]Using API token authentication as {username}[/dim]")
            return JenkinsClient(
                url=jenkins_url,
                username=username,
                password=token,
                verify_ssl=verify_ssl,
            )

        # Try OAuth tokens
        token_manager = TokenManager()
        if token_manager.is_authenticated():
            access_token = token_manager.get_access_token()
            # Get user info for username
            try:
                okta_auth = OktaAuthenticator(
                    domain=profile.okta.domain,
                    client_id=profile.okta.client_id,
                    redirect_uri=profile.okta.redirect_uri,
                    scopes=profile.okta.scopes,
                )
                user_info = okta_auth.get_user_info()
                username = user_info.get("email", "unknown")
                console.print(f"[dim]Using OAuth authentication as {username}[/dim]")
            except Exception as e:
                logger.debug(f"Could not retrieve user info from OAuth token: {e}")
                username = "oauth-user"
                console.print("[dim]Using OAuth authentication[/dim]")

            return JenkinsClient(
                url=jenkins_url,
                username=username,
                password=access_token,
                verify_ssl=verify_ssl,
            )

        # No authentication found
        console.print("[red]Error:[/red] Not authenticated")
        console.print("\nPlease authenticate first:")
        console.print("  • [cyan]jctl auth token[/cyan] - Quick setup with API token")
        console.print("  • [cyan]jctl auth login[/cyan] - OAuth SSO authentication")
        sys.exit(1)

    except FileNotFoundError:
        console.print("[red]Error:[/red] Configuration not found")
        console.print("Run [cyan]jctl config init[/cyan] to set up configuration")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
