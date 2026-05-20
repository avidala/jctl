"""Coverage for the async helper methods on JenkinsClient.

Strategy: replace `client._client` (the httpx.AsyncClient) with an
AsyncMock so the helpers go through their real path-building +
parameter-passing logic without ever touching the network. Then assert
the request was issued with the URL, method, and body we expect.

This lifts jctl/jenkins/client.py from ~42% to the high 80s.
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from jctl.jenkins.client import JenkinsClient


def _response(
    *,
    status_code: int = 200,
    json_body: Any | None = None,
    text: str = "",
    headers: dict | None = None,
) -> MagicMock:
    """Build a stand-in for `httpx.Response` that mimics the methods our
    code touches (`raise_for_status`, `json()`, `.text`, `.headers`).
    """
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.text = text
    resp.headers = headers or {}
    if json_body is not None:
        resp.json.return_value = json_body
    if status_code >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            f"{status_code}", request=MagicMock(), response=resp
        )
    else:
        resp.raise_for_status.return_value = None
    return resp


@pytest.fixture
def client() -> JenkinsClient:
    """Real JenkinsClient with `_client` (the AsyncClient) replaced by a
    mock so we never open a socket. `request` is the only method we
    touch on the AsyncClient — `_get_crumb` does `client.get` which is
    a separate attribute, mocked individually per-test."""
    c = JenkinsClient(url="https://j.test", username="u", password="t")
    c._client = MagicMock()
    c._client.request = AsyncMock()
    c._client.get = AsyncMock()
    return c


# --- _get_crumb ---------------------------------------------------------


@pytest.mark.asyncio
async def test_get_crumb_caches_after_first_call(client):
    client._client.get.return_value = _response(
        json_body={"crumbRequestField": "Jenkins-Crumb", "crumb": "abc"}
    )
    crumb = await client._get_crumb()
    assert crumb == {"Jenkins-Crumb": "abc"}

    # Second call must NOT hit the server again (cached on the instance).
    client._client.get.reset_mock()
    crumb2 = await client._get_crumb()
    assert crumb2 == {"Jenkins-Crumb": "abc"}
    client._client.get.assert_not_called()


@pytest.mark.asyncio
async def test_get_crumb_empty_when_csrf_disabled(client):
    """Jenkins without CSRF returns 404 on /crumbIssuer; we swallow and
    return {} so POSTs keep working."""
    client._client.get.return_value = _response(status_code=404)
    assert await client._get_crumb() == {}


# --- stop_build / kill_build --------------------------------------------


@pytest.mark.asyncio
async def test_stop_build_posts_to_stop_endpoint(client):
    client._client.request.return_value = _response()
    client._client.get.return_value = _response(json_body={})  # crumb lookup

    await client.stop_build("deploy/app", 42)

    # Assert the POST was made to the right URL. The crumb fetch is GET,
    # the stop itself is POST.
    posts = [call for call in client._client.request.call_args_list if call.args[0] == "POST"]
    assert len(posts) == 1
    assert posts[0].args[1] == "/job/deploy/job/app/42/stop"


@pytest.mark.asyncio
async def test_kill_build_posts_to_kill_endpoint(client):
    client._client.request.return_value = _response()
    client._client.get.return_value = _response(json_body={})

    await client.kill_build("deploy/app", 5)

    posts = [call for call in client._client.request.call_args_list if call.args[0] == "POST"]
    assert posts[0].args[1] == "/job/deploy/job/app/5/kill"


# --- get_workflow_info / get_pending_inputs -----------------------------


@pytest.mark.asyncio
async def test_get_workflow_info_returns_stages_dict(client):
    payload = {"stages": [{"name": "Build", "status": "SUCCESS"}]}
    client._client.request.return_value = _response(json_body=payload)

    out = await client.get_workflow_info("deploy/app", 1)
    assert out == payload
    call = client._client.request.call_args
    assert call.args == ("GET", "/job/deploy/job/app/1/wfapi/describe")


@pytest.mark.asyncio
async def test_get_pending_inputs_returns_list(client):
    client._client.request.return_value = _response(json_body=[{"id": "Approve"}])

    out = await client.get_pending_inputs("deploy/app", 1)
    assert out == [{"id": "Approve"}]
    assert (
        client._client.request.call_args.args[1]
        == "/job/deploy/job/app/1/wfapi/pendingInputActions"
    )


# --- input lifecycle ----------------------------------------------------


@pytest.mark.asyncio
async def test_abort_input_targets_correct_endpoint(client):
    client._client.request.return_value = _response()
    client._client.get.return_value = _response(json_body={})

    await client.abort_input("deploy/app", 1, "Approve")

    posts = [c for c in client._client.request.call_args_list if c.args[0] == "POST"]
    assert posts[0].args[1] == "/job/deploy/job/app/1/input/Approve/abort"


@pytest.mark.asyncio
async def test_submit_input_passes_parameters_as_json(client):
    client._client.request.return_value = _response()
    client._client.get.return_value = _response(json_body={})

    await client.submit_input("deploy/app", 1, "Approve", {"env": "prod"})

    posts = [c for c in client._client.request.call_args_list if c.args[0] == "POST"]
    submit_call = posts[0]
    assert submit_call.args[1] == "/job/deploy/job/app/1/input/Approve/submit"
    assert submit_call.kwargs["json"] == {"parameter": [{"name": "env", "value": "prod"}]}


@pytest.mark.asyncio
async def test_submit_input_with_no_parameters_sends_empty_list(client):
    client._client.request.return_value = _response()
    client._client.get.return_value = _response(json_body={})

    await client.submit_input("deploy/app", 1, "Approve")

    posts = [c for c in client._client.request.call_args_list if c.args[0] == "POST"]
    assert posts[0].kwargs["json"] == {"parameter": []}


# --- replay -------------------------------------------------------------


@pytest.mark.asyncio
async def test_replay_build_returns_config(client):
    client._client.request.return_value = _response(json_body={"mainScript": "echo"})

    out = await client.replay_build("deploy/app", 1)
    assert out == {"mainScript": "echo"}


@pytest.mark.asyncio
async def test_replay_run_posts_with_crumb_in_body(client):
    """The replay_run path is unusual — it folds the crumb into the POST
    body (not the headers) for legacy compatibility."""
    client._client.request.return_value = _response()
    client._client.get.return_value = _response(
        json_body={"crumbRequestField": "Jenkins-Crumb", "crumb": "XYZ"}
    )

    await client.replay_run("deploy/app", 1, "new script")

    posts = [c for c in client._client.request.call_args_list if c.args[0] == "POST"]
    call = posts[0]
    assert call.args[1] == "/job/deploy/job/app/1/replay/run"
    assert call.kwargs["data"]["mainScript"] == "new script"
    # Crumb folded into the body data dict.
    assert call.kwargs["data"]["Jenkins-Crumb"] == "XYZ"


# --- queue --------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_queue_item_uses_correct_path(client):
    client._client.request.return_value = _response(json_body={"id": 17, "blocked": False})

    out = await client.get_queue_item(17)
    assert out == {"id": 17, "blocked": False}
    assert client._client.request.call_args.args == ("GET", "/queue/item/17/api/json")


@pytest.mark.asyncio
async def test_cancel_queue_item_posts_with_id_param(client):
    client._client.request.return_value = _response()
    client._client.get.return_value = _response(json_body={})

    await client.cancel_queue_item(17)

    posts = [c for c in client._client.request.call_args_list if c.args[0] == "POST"]
    assert posts[0].args[1] == "/queue/cancelItem?id=17"


# --- validate_jenkinsfile ----------------------------------------------


@pytest.mark.asyncio
async def test_validate_jenkinsfile_posts_form_data(client):
    client._client.request.return_value = _response(json_body={"valid": True})
    client._client.get.return_value = _response(json_body={})

    out = await client.validate_jenkinsfile("pipeline { agent any }")
    assert out == {"valid": True}

    posts = [c for c in client._client.request.call_args_list if c.args[0] == "POST"]
    assert posts[0].args[1] == "/pipeline-model-converter/validate"
    assert posts[0].kwargs["data"] == {"jenkinsfile": "pipeline { agent any }"}


# --- folder-path encoding (cross-cutting) ------------------------------


@pytest.mark.asyncio
async def test_folder_path_is_jenkins_url_encoded(client):
    """A 3-level path managed-cloud/MC-26.05.1/app should become
    /job/managed-cloud/job/MC-26.05.1/job/app — once per folder segment."""
    client._client.request.return_value = _response(json_body={})

    await client.get_workflow_info("managed-cloud/MC-26.05.1/app", 1)

    assert (
        client._client.request.call_args.args[1]
        == "/job/managed-cloud/job/MC-26.05.1/job/app/1/wfapi/describe"
    )


# --- stream_build_log --------------------------------------------------


@pytest.mark.asyncio
async def test_stream_build_log_calls_callback_per_line_then_stops(client, monkeypatch):
    """Two polls: first returns text with X-More-Data=true, second
    finishes with X-More-Data=false. asyncio.sleep is patched to a
    no-op so the test doesn't actually wait between polls."""

    async def _no_sleep(_):
        return None

    monkeypatch.setattr("jctl.jenkins.client.asyncio.sleep", _no_sleep)

    client._client.request.side_effect = [
        _response(
            text="line one\nline two\n",
            headers={"X-More-Data": "true", "X-Text-Size": "18"},
        ),
        _response(text="line three\n", headers={"X-More-Data": "false"}),
    ]

    seen: list[str] = []
    await client.stream_build_log("deploy/app", 1, seen.append)
    assert seen == ["line one", "line two", "line three"]
    # Two polls.
    assert client._client.request.call_count == 2
    # Second poll uses the X-Text-Size advance.
    second_call = client._client.request.call_args_list[1]
    assert second_call.kwargs["params"] == {"start": 18}


# --- close --------------------------------------------------------------


@pytest.mark.asyncio
async def test_close_aclose_is_awaited(client):
    client._client.aclose = AsyncMock()
    await client.close()
    client._client.aclose.assert_awaited_once()


# --- async context manager ----------------------------------------------


@pytest.mark.asyncio
async def test_async_context_manager_closes_on_exit(client):
    client._client.aclose = AsyncMock()
    async with client as c:
        assert c is client
    client._client.aclose.assert_awaited_once()
