"""Jenkins API client."""

import asyncio
import re
from typing import Any

import httpx
from jenkins import Jenkins as JenkinsBase
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from jctl.utils.logging import get_logger

logger = get_logger(__name__)


class JenkinsAPIError(Exception):
    """Jenkins API error."""

    pass


_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")


def _clean_response_body(text: str, max_len: int = 200) -> str:
    """Strip HTML tags so Jenkins' HTML 404 pages don't end up dumped raw
    into the user's terminal.

    Prefer the <title> when present (Jenkins error pages put the actual
    message there); fall back to a length-capped, whitespace-collapsed
    text-only render.
    """
    if not text:
        return ""
    title = re.search(r"<title>([^<]+)</title>", text, re.IGNORECASE)
    if title and title.group(1).strip():
        return title.group(1).strip()
    stripped = _WHITESPACE_RE.sub(" ", _HTML_TAG_RE.sub(" ", text)).strip()
    if len(stripped) > max_len:
        stripped = stripped[: max_len - 1].rstrip() + "…"
    return stripped


def _format_network_error(exc: httpx.RequestError) -> str:
    """Build a useful one-line message from an httpx ConnectError/etc."""
    name = type(exc).__name__
    detail = str(exc).strip()
    host: str | None = None
    try:
        host = exc.request.url.host  # type: ignore[union-attr]
    except Exception:  # noqa: BLE001
        host = None
    if host and not detail:
        return f"{name}: could not reach {host}"
    if host:
        return f"{name}: {detail} ({host})"
    return f"{name}: {detail}" if detail else name


def _should_retry_http_error(exception: Exception) -> bool:
    """Determine if HTTP error should be retried.

    Args:
        exception: The exception to check

    Returns:
        True if the error should be retried
    """
    if isinstance(exception, httpx.HTTPStatusError):
        # Retry on rate limit, service unavailable, and gateway timeout
        return exception.response.status_code in [429, 503, 504]
    if isinstance(exception, httpx.RequestError):
        # Retry on network errors
        return True
    return False


class JenkinsClient:
    """Jenkins API client with extended pipeline support."""

    def __init__(
        self,
        url: str,
        username: str | None = None,
        password: str | None = None,
        token: str | None = None,
        verify_ssl: bool = True,
        timeout: int = 30,
    ):
        """Initialize Jenkins client.

        Args:
            url: Jenkins server URL
            username: Jenkins username (optional with token auth)
            password: Jenkins password
            token: Authentication token
            verify_ssl: Verify SSL certificates
            timeout: Request timeout in seconds
        """
        self.url = url.rstrip("/")
        self.username = username
        self.password = password
        self.token = token
        self.verify_ssl = verify_ssl
        self.timeout = timeout

        # Initialize base Jenkins client for basic operations
        self._jenkins = JenkinsBase(
            url, username=username, password=password or token, timeout=timeout
        )

        # HTTP client for custom endpoints
        # Use password (which contains API token) for authentication
        auth_value = None
        if username and (password or token):
            auth_value = (username, password or token)

        # Configure separate connect and read timeouts for better performance
        timeout_config = httpx.Timeout(
            timeout=30.0,  # Default read/write timeout
            connect=10.0,  # Connect timeout
        )

        self._client = httpx.AsyncClient(
            base_url=self.url,
            timeout=timeout_config if timeout == 30.0 else timeout,
            verify=verify_ssl,
            auth=auth_value,
            # Jenkins POST endpoints like /stop and /build return 302 to the
            # job page on success. Without follow_redirects, raise_for_status
            # treats the 302 as an error.
            follow_redirects=True,
        )

        self._crumb: dict[str, str] | None = None

    async def _get_crumb(self) -> dict[str, str]:
        """Get CSRF crumb token.

        Returns:
            Dict with crumb header name and value
        """
        if self._crumb:
            return self._crumb

        try:
            response = await self._client.get("/crumbIssuer/api/json")
            response.raise_for_status()
            data = response.json()
            self._crumb = {data["crumbRequestField"]: data["crumb"]}
            return self._crumb
        except (httpx.HTTPStatusError, KeyError):
            # Jenkins may not have CSRF protection enabled
            return {}

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make HTTP request to Jenkins API with automatic retry logic.

        Wraps `_do_request` so the final RequestError after tenacity exhausts
        retries surfaces as a `JenkinsAPIError` with a readable message
        (httpx ConnectError's `str()` is often empty).
        """
        try:
            return await self._do_request(method, path, **kwargs)
        except httpx.RequestError as e:
            raise JenkinsAPIError(_format_network_error(e)) from e

    @retry(
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.RequestError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
        before_sleep=lambda retry_state: logger.debug(
            f"Retrying request (attempt {retry_state.attempt_number}) after error: {retry_state.outcome.exception()}"
        ),
    )
    async def _do_request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Inner retry-decorated request. Do not call directly.

        Automatically retries on:
        - Network errors (httpx.RequestError)
        - 429 (Rate Limited)
        - 503 (Service Unavailable)
        - 504 (Gateway Timeout)

        Uses exponential backoff: 1s, 2s, 4s (max 3 attempts)
        """
        # Add crumb for POST requests
        if method.upper() in ["POST", "PUT", "DELETE"]:
            crumb = await self._get_crumb()
            headers = kwargs.get("headers", {})
            headers.update(crumb)
            kwargs["headers"] = headers

        try:
            response = await self._client.request(method, path, **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            # Only retry on specific status codes
            if e.response.status_code in [429, 503, 504]:
                logger.debug(f"Retryable HTTP error {e.response.status_code}: {e.response.text}")
                raise  # Let tenacity handle the retry
            # Don't retry other HTTP errors (4xx, 5xx). Strip HTML so the
            # message stays readable in the terminal.
            body = _clean_response_body(e.response.text)
            msg = f"Jenkins API error: {e.response.status_code}"
            if body:
                msg = f"{msg} — {body}"
            raise JenkinsAPIError(msg) from e
        except httpx.RequestError as e:
            logger.debug(f"Network error (will retry): {e}")
            raise  # Let tenacity handle the retry

    # Job operations

    def get_job_info(self, name: str) -> dict[str, Any]:
        """Get job information.

        Args:
            name: Job name

        Returns:
            Job information dict
        """
        return self._jenkins.get_job_info(name)

    def trigger_job(self, name: str, parameters: dict[str, Any] | None = None) -> int:
        """Trigger a job.

        Args:
            name: Job name
            parameters: Job parameters

        Returns:
            Queue item ID
        """
        if parameters:
            return self._jenkins.build_job(name, parameters=parameters)
        return self._jenkins.build_job(name)

    async def get_jobs(self, folder: str | None = None) -> list[dict[str, Any]]:
        """Get all jobs from Jenkins, optionally from a specific folder.

        Args:
            folder: Optional folder path (e.g., "deploy" or "deploy/staging")

        Returns:
            List of job information dicts with full paths
        """
        if folder:
            # Get jobs from specific folder
            folder_path = "/job/" + "/job/".join(folder.split("/"))
            path = f"{folder_path}/api/json?tree=jobs[name,url,color,lastBuild[number,result,timestamp,duration],jobs[name,url,color,lastBuild[number,result,timestamp,duration]]]"
        else:
            # Get all jobs recursively
            path = "/api/json?tree=jobs[name,url,color,lastBuild[number,result,timestamp,duration],jobs[name,url,color,lastBuild[number,result,timestamp,duration]]]"

        response = await self._request("GET", path)
        data = response.json()
        jobs = data.get("jobs", [])

        # Flatten nested jobs (folders contain jobs)
        flattened = []
        self._flatten_jobs(jobs, flattened, folder or "")
        return flattened

    def _flatten_jobs(
        self, jobs: list[dict[str, Any]], result: list[dict[str, Any]], prefix: str = ""
    ) -> None:
        """Recursively flatten nested job structure from folders.

        Args:
            jobs: List of job/folder dicts from Jenkins API
            result: Output list to append flattened jobs to
            prefix: Current folder path prefix
        """
        for item in jobs:
            # Check if it's a folder (contains nested jobs)
            if "jobs" in item and item["jobs"]:
                # It's a folder, recurse into it
                folder_name = item["name"]
                new_prefix = f"{prefix}/{folder_name}" if prefix else folder_name
                self._flatten_jobs(item["jobs"], result, new_prefix)
            else:
                # It's a job, add it with full path
                job_copy = item.copy()
                if prefix:
                    job_copy["fullName"] = f"{prefix}/{item['name']}"
                else:
                    job_copy["fullName"] = item["name"]
                result.append(job_copy)

    async def get_build_info(self, name: str, number: int) -> dict[str, Any]:
        """Get build information.

        Args:
            name: Job name (can include folder path like "folder/job-name")
            number: Build number

        Returns:
            Build information dict
        """
        # Convert folder/job structure to /job/folder/job/job-name
        job_path = "/job/" + "/job/".join(name.split("/"))
        path = f"{job_path}/{number}/api/json"
        response = await self._request("GET", path)
        return response.json()

    async def get_build_log(self, name: str, number: int) -> str:
        """Get build console log.

        Args:
            name: Job name (can include folder path like "folder/job-name")
            number: Build number

        Returns:
            Console log text
        """
        # Convert folder/job structure to /job/folder/job/job-name
        job_path = "/job/" + "/job/".join(name.split("/"))
        path = f"{job_path}/{number}/consoleText"
        response = await self._request("GET", path)
        return response.text

    async def stream_build_log(self, name: str, number: int, callback: Any) -> None:
        """Stream build log in real-time.

        Args:
            name: Job name (can include folder path like "folder/job-name")
            number: Build number
            callback: Callback function for log lines
        """
        # Convert folder/job structure to /job/folder/job/job-name
        job_path = "/job/" + "/job/".join(name.split("/"))
        path = f"{job_path}/{number}/logText/progressiveText"
        start = 0

        while True:
            response = await self._request("GET", path, params={"start": start})
            text = response.text

            if text:
                # Call callback with new log lines
                for line in text.splitlines():
                    callback(line)

            # Check if build is complete
            more_data = response.headers.get("X-More-Data", "false")
            if more_data == "false":
                break

            # Update start position
            start = int(response.headers.get("X-Text-Size", start))

            # Wait before next poll
            await asyncio.sleep(1)

    # Pipeline actions

    async def stop_build(self, name: str, number: int) -> None:
        """Stop/abort a running build.

        Args:
            name: Job name (can include folder path like "folder/job-name")
            number: Build number
        """
        # Convert folder/job structure to /job/folder/job/job-name
        job_path = "/job/" + "/job/".join(name.split("/"))
        path = f"{job_path}/{number}/stop"
        await self._request("POST", path)
        logger.info(f"Stopped build {name} #{number}")

    async def kill_build(self, name: str, number: int) -> None:
        """Force kill a running build.

        Args:
            name: Job name (can include folder path like "folder/job-name")
            number: Build number
        """
        # Convert folder/job structure to /job/folder/job/job-name
        job_path = "/job/" + "/job/".join(name.split("/"))
        path = f"{job_path}/{number}/kill"
        await self._request("POST", path)
        logger.info(f"Killed build {name} #{number}")

    async def get_workflow_info(self, name: str, number: int) -> dict[str, Any]:
        """Get workflow/pipeline information.

        Args:
            name: Job name (can include folder path like "folder/job-name")
            number: Build number

        Returns:
            Workflow information with stages
        """
        # Convert folder/job structure to /job/folder/job/job-name
        job_path = "/job/" + "/job/".join(name.split("/"))
        path = f"{job_path}/{number}/wfapi/describe"
        response = await self._request("GET", path)
        return response.json()

    async def get_pending_inputs(self, name: str, number: int) -> list[dict[str, Any]]:
        """Get pending input actions for a build.

        Args:
            name: Job name (can include folder path like "folder/job-name")
            number: Build number

        Returns:
            List of pending input actions
        """
        # Convert folder/job structure to /job/folder/job/job-name
        job_path = "/job/" + "/job/".join(name.split("/"))
        path = f"{job_path}/{number}/wfapi/pendingInputActions"
        response = await self._request("GET", path)
        return response.json()

    async def abort_input(self, name: str, number: int, input_id: str) -> None:
        """Abort/skip an input step (pause pipeline).

        Args:
            name: Job name (can include folder path like "folder/job-name")
            number: Build number
            input_id: Input action ID
        """
        # Convert folder/job structure to /job/folder/job/job-name
        job_path = "/job/" + "/job/".join(name.split("/"))
        path = f"{job_path}/{number}/input/{input_id}/abort"
        await self._request("POST", path)
        logger.info(f"Aborted input {input_id} for {name} #{number}")

    async def submit_input(
        self, name: str, number: int, input_id: str, parameters: dict[str, Any] | None = None
    ) -> None:
        """Submit input to resume pipeline.

        Args:
            name: Job name (can include folder path like "folder/job-name")
            number: Build number
            input_id: Input action ID
            parameters: Input parameters
        """
        # Convert folder/job structure to /job/folder/job/job-name
        job_path = "/job/" + "/job/".join(name.split("/"))
        path = f"{job_path}/{number}/input/{input_id}/submit"
        json_data = {"parameter": [{"name": k, "value": v} for k, v in (parameters or {}).items()]}
        await self._request("POST", path, json=json_data)
        logger.info(f"Submitted input {input_id} for {name} #{number}")

    async def replay_build(self, name: str, number: int) -> dict[str, Any]:
        """Get replay configuration for a build.

        Args:
            name: Job name (can include folder path like "folder/job-name")
            number: Build number

        Returns:
            Replay configuration
        """
        # Convert folder/job structure to /job/folder/job/job-name
        job_path = "/job/" + "/job/".join(name.split("/"))
        path = f"{job_path}/{number}/replay"
        response = await self._request("GET", path)
        return response.json()

    async def replay_run(self, name: str, number: int, script: str) -> None:
        """Execute replay with modified script.

        Args:
            name: Job name (can include folder path like "folder/job-name")
            number: Build number to replay
            script: Modified pipeline script
        """
        # Convert folder/job structure to /job/folder/job/job-name
        job_path = "/job/" + "/job/".join(name.split("/"))
        path = f"{job_path}/{number}/replay/run"
        crumb = await self._get_crumb()
        data = {"mainScript": script}
        data.update(crumb)
        await self._request("POST", path, data=data)
        logger.info(f"Replayed build {name} #{number}")

    async def get_queue_item(self, item_id: int) -> dict[str, Any]:
        """Get queue item information.

        Args:
            item_id: Queue item ID

        Returns:
            Queue item information
        """
        path = f"/queue/item/{item_id}/api/json"
        response = await self._request("GET", path)
        return response.json()

    async def cancel_queue_item(self, item_id: int) -> None:
        """Cancel a queued item.

        Args:
            item_id: Queue item ID
        """
        path = f"/queue/cancelItem?id={item_id}"
        await self._request("POST", path)
        logger.info(f"Cancelled queue item {item_id}")

    def list_jobs(self) -> list[dict[str, Any]]:
        """List all jobs.

        Returns:
            List of job information dicts
        """
        return self._jenkins.get_jobs()

    async def validate_jenkinsfile(self, jenkinsfile: str) -> dict[str, Any]:
        """Validate a Jenkinsfile.

        Args:
            jenkinsfile: Jenkinsfile content

        Returns:
            Validation result
        """
        path = "/pipeline-model-converter/validate"
        response = await self._request("POST", path, data={"jenkinsfile": jenkinsfile})
        return response.json()

    async def close(self) -> None:
        """Close HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> "JenkinsClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()
