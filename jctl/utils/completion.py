"""Shell completion utilities for jctl."""

import asyncio
import time
from typing import Any

import click

from jctl.auth.api_token import APITokenAuthenticator
from jctl.auth.token_manager import TokenManager
from jctl.config.manager import ConfigManager
from jctl.jenkins.client import JenkinsClient

# Cache for job list completion (5-minute TTL)
_job_cache: dict[str, Any] = {
    "jobs": [],
    "timestamp": 0,
    "ttl": 300,  # 5 minutes in seconds
}


def get_jenkins_client_for_completion(ctx: click.Context) -> JenkinsClient | None:
    """Get authenticated Jenkins client for completion (silently fails)."""
    try:
        config_manager = ConfigManager()
        config = config_manager.get()
        profile = config.get_profile(ctx.obj.get("profile") if ctx.obj else None)

        jenkins_url = str(profile.jenkins.url)
        verify_ssl = profile.jenkins.verify_ssl

        # Try API token first
        api_auth = APITokenAuthenticator()
        if api_auth.is_authenticated():
            username, token = api_auth.get_credentials()
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
            return JenkinsClient(
                url=jenkins_url,
                username="oauth-user",
                password=access_token,
                verify_ssl=verify_ssl,
            )

        return None
    except Exception:
        # Silently fail for completion
        return None


def complete_job_name(ctx: click.Context, param: click.Parameter, incomplete: str) -> list[str]:
    """Complete job/pipeline names from Jenkins with 5-minute cache.

    Uses a simple time-based cache to avoid hitting Jenkins API on every tab completion.
    Cache is shared across all completion calls and expires after 5 minutes.

    Args:
        ctx: Click context
        param: Click parameter
        incomplete: Partial job name typed by user

    Returns:
        List of matching job names
    """
    global _job_cache

    current_time = time.time()
    cache_age = current_time - _job_cache["timestamp"]

    # Check if cache is valid (less than TTL seconds old and not empty)
    if cache_age < _job_cache["ttl"] and _job_cache["jobs"]:
        job_names = _job_cache["jobs"]
    else:
        # Cache miss or expired - fetch from Jenkins
        client = get_jenkins_client_for_completion(ctx)
        if not client:
            return []

        try:
            # Fetch jobs from Jenkins
            async def fetch_jobs():
                try:
                    jobs = await client.get_jobs()
                    return jobs
                except Exception:
                    return []

            jobs = asyncio.run(fetch_jobs())

            # Extract job names
            job_names = [job.get("fullName", job["name"]) for job in jobs]

            # Update cache
            _job_cache["jobs"] = job_names
            _job_cache["timestamp"] = current_time

        except Exception:
            return []

    # Filter by what user has typed so far
    if incomplete:
        matching = [name for name in job_names if name.startswith(incomplete)]
        return matching

    return job_names
