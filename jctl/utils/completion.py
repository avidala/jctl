"""Shell completion utilities for jctl.

Shell completion fires in a fresh Python process every time the user hits
Tab, so a module-level in-memory cache never lived past a single
invocation. We persist the job list to `~/.jctl/cache/jobs.json` (TTL
controlled here) so warm completions are a single file read instead of a
full Jenkins round-trip.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from pathlib import Path

import click

from jctl.auth.api_token import APITokenAuthenticator
from jctl.config.manager import ConfigManager
from jctl.jenkins.client import JenkinsClient

_CACHE_TTL_SECONDS = 300  # 5 minutes


def _cache_path() -> Path:
    """Where the on-disk completion cache lives.

    Honors `JCTL_CONFIG_DIR` so tests (and users with non-standard layouts)
    don't have to pollute the real `~/.jctl`.
    """
    override = os.environ.get("JCTL_CONFIG_DIR")
    base = Path(override) if override else Path.home() / ".jctl"
    return base / "cache" / "jobs.json"


def _read_cache() -> list[str] | None:
    """Return cached job names if the file exists and is fresh, else None."""
    path = _cache_path()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    ts = data.get("timestamp", 0)
    if not isinstance(ts, (int, float)) or time.time() - ts > _CACHE_TTL_SECONDS:
        return None
    jobs = data.get("jobs")
    if not isinstance(jobs, list):
        return None
    return [str(j) for j in jobs]


def _write_cache(jobs: list[str]) -> None:
    """Persist the job-name list with a current timestamp.

    Atomic via tmp+rename so a crash mid-write can't leave the cache in a
    half-written state. We silently swallow IO errors — completion must
    never break the user's shell.
    """
    path = _cache_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        return
    payload = json.dumps({"timestamp": int(time.time()), "jobs": jobs})
    tmp = path.with_suffix(".tmp")
    try:
        tmp.write_text(payload)
        try:
            tmp.chmod(0o600)
        except OSError:
            pass
        tmp.replace(path)
    except OSError:
        # If anything goes wrong (read-only fs, full disk, etc.) just
        # skip caching — next completion will fetch again.
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass


def get_jenkins_client_for_completion(ctx: click.Context) -> JenkinsClient | None:
    """Get authenticated Jenkins client for completion (silently fails)."""
    try:
        config_manager = ConfigManager()
        config = config_manager.get()
        profile = config.get_profile(ctx.obj.get("profile") if ctx.obj else None)

        jenkins_url = str(profile.jenkins.url)
        verify_ssl = profile.jenkins.verify_ssl

        api_auth = APITokenAuthenticator()
        if api_auth.is_authenticated():
            credentials = api_auth.get_credentials()
            if credentials is None:
                return None
            username, token = credentials
            return JenkinsClient(
                url=jenkins_url,
                username=username,
                password=token,
                verify_ssl=verify_ssl,
            )
        return None
    except Exception:
        return None


def complete_job_name(ctx: click.Context, param: click.Parameter, incomplete: str) -> list[str]:
    """Suggest job/pipeline names matching `incomplete` (case-insensitive
    substring).

    The previous implementation only matched `startswith`, which made it
    useless for deeply-folder-nested jobs — e.g. typing `hamc<Tab>` would
    return nothing even when
    `managed-cloud/MC-26.05.1/hamc-upgrade-environment` was indexed.
    """
    job_names = _read_cache()
    if job_names is None:
        client = get_jenkins_client_for_completion(ctx)
        if not client:
            return []

        async def _fetch() -> list[dict]:
            try:
                return await client.get_jobs()
            except Exception:
                return []

        try:
            jobs = asyncio.run(_fetch())
        except Exception:
            return []

        job_names = [job.get("fullName", job["name"]) for job in jobs]
        _write_cache(job_names)

    if not incomplete:
        return job_names

    needle = incomplete.lower()
    return [name for name in job_names if needle in name.lower()]
