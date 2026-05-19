"""Tests for the small error-formatting helpers in jctl.jenkins.client."""

from unittest.mock import MagicMock

import httpx
import pytest

from jctl.jenkins.client import _clean_response_body, _format_network_error


class TestCleanResponseBody:
    def test_empty(self):
        assert _clean_response_body("") == ""

    def test_prefers_title(self):
        html = "<html><head><title>Not Found - Jenkins</title></head><body><h1>404</h1>noise</body></html>"
        assert _clean_response_body(html) == "Not Found - Jenkins"

    def test_no_title_falls_back_to_stripped_text(self):
        html = "<html><body><h1>Something Broke</h1><p>Try again later</p></body></html>"
        cleaned = _clean_response_body(html)
        assert "<" not in cleaned
        assert "Something Broke" in cleaned
        assert "Try again later" in cleaned

    def test_collapses_whitespace(self):
        text = "line one\n\n\n   line two\t\tline three"
        assert _clean_response_body(text) == "line one line two line three"

    def test_truncates_long_bodies(self):
        cleaned = _clean_response_body("x" * 500, max_len=100)
        assert len(cleaned) <= 100
        assert cleaned.endswith("…")


class TestFormatNetworkError:
    def _mock_request(self, host: str = "jenkins.example.com") -> httpx.Request:
        return httpx.Request("GET", f"https://{host}/api/json")

    def test_connect_error_with_host(self):
        exc = httpx.ConnectError("Name or service not known")
        exc._request = self._mock_request("jenkins.example.com")  # type: ignore[attr-defined]
        msg = _format_network_error(exc)
        assert "ConnectError" in msg
        # Host is appended in parens by the formatter (avoids a bare-substring
        # check that CodeQL py/incomplete-url-substring-sanitization flags).
        assert "(jenkins.example.com)" in msg
        assert "Name or service not known" in msg

    def test_empty_message_still_includes_host(self):
        exc = httpx.ConnectTimeout("")
        exc._request = self._mock_request("ghost.example")  # type: ignore[attr-defined]
        msg = _format_network_error(exc)
        # Host is the trailing token in the "could not reach <host>" form.
        assert msg.endswith("ghost.example")
        assert "ConnectTimeout" in msg

    def test_no_request_attached(self):
        """If httpx hasn't attached a request, we still produce a useful one-liner."""
        exc = httpx.RequestError("transport failure")
        # No request attached
        msg = _format_network_error(exc)
        assert msg.startswith("RequestError")
        assert "transport failure" in msg


@pytest.fixture
def mock_response_404():
    response = MagicMock(spec=httpx.Response)
    response.status_code = 404
    response.text = "<html><head><title>Not Found - Jenkins</title></head><body></body></html>"
    return response
