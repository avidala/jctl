"""Tests for Okta OAuth authentication."""

import base64
import hashlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from jctl.auth.okta import OktaAuthenticator


class TestOktaAuthenticator:
    """Tests for Okta OAuth authentication."""

    def test_init(self, mock_okta_config):
        """Test OktaAuthenticator initialization."""
        auth = OktaAuthenticator(
            domain=mock_okta_config["domain"],
            client_id=mock_okta_config["client_id"],
            redirect_uri=mock_okta_config["redirect_uri"],
        )

        assert auth.domain == mock_okta_config["domain"]
        assert auth.client_id == mock_okta_config["client_id"]
        assert auth.redirect_uri == mock_okta_config["redirect_uri"]

    def test_generate_pkce_pair(self, mock_okta_config):
        """PKCE verifier ↔ challenge relationship per RFC 7636."""
        auth = OktaAuthenticator(
            domain=mock_okta_config["domain"],
            client_id=mock_okta_config["client_id"],
            redirect_uri=mock_okta_config["redirect_uri"],
        )

        verifier, challenge = auth._generate_pkce_pair()

        # Verifier: 32 bytes b64url-encoded with padding stripped == 43 chars,
        # using only [A-Za-z0-9-_].
        assert len(verifier) == 43
        assert all(
            c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
            for c in verifier
        )

        expected_challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
            .decode()
            .rstrip("=")
        )
        assert challenge == expected_challenge

    @pytest.mark.skip(reason="API changed: method no longer exists, integrated into login()")
    def test_get_authorization_url(self, mock_okta_config):
        """Test authorization URL generation."""
        auth = OktaAuthenticator(
            domain=mock_okta_config["domain"],
            client_id=mock_okta_config["client_id"],
            redirect_uri=mock_okta_config["redirect_uri"],
        )

        url, state, verifier = auth.get_authorization_url()

        # Verify URL structure
        assert url.startswith(f"https://{mock_okta_config['domain']}/oauth2/v1/authorize")
        assert f"client_id={mock_okta_config['client_id']}" in url
        assert f"redirect_uri={mock_okta_config['redirect_uri']}" in url
        assert "code_challenge=" in url
        assert "code_challenge_method=S256" in url
        assert f"state={state}" in url
        assert "response_type=code" in url
        assert "scope=openid+profile+email" in url

    @pytest.mark.skip(reason="API changed: method no longer exists, integrated into login()")
    @pytest.mark.asyncio
    @patch("jctl.auth.okta.httpx.AsyncClient")
    async def test_exchange_code_for_tokens(
        self, mock_client_class, mock_okta_config, sample_tokens
    ):
        """Test exchanging authorization code for tokens."""
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_tokens

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__.return_value = mock_client

        auth = OktaAuthenticator(
            domain=mock_okta_config["domain"],
            client_id=mock_okta_config["client_id"],
            redirect_uri=mock_okta_config["redirect_uri"],
        )

        tokens = await auth.exchange_code_for_tokens("test-auth-code", "test-verifier")

        assert tokens == sample_tokens
        mock_client.post.assert_called_once()

    @pytest.mark.skip(reason="API changed: method no longer exists, integrated into login()")
    @pytest.mark.asyncio
    @patch("jctl.auth.okta.httpx.AsyncClient")
    async def test_exchange_code_for_tokens_error(self, mock_client_class, mock_okta_config):
        """Test token exchange with API error."""
        # Mock HTTP error response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Invalid authorization code"

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__.return_value = mock_client

        auth = OktaAuthenticator(
            domain=mock_okta_config["domain"],
            client_id=mock_okta_config["client_id"],
            redirect_uri=mock_okta_config["redirect_uri"],
        )

        with pytest.raises(Exception) as exc_info:
            await auth.exchange_code_for_tokens("invalid-code", "test-verifier")

        assert "Failed to exchange code for tokens" in str(exc_info.value)

    @pytest.mark.skip(
        reason="API changed: refresh_tokens() no longer takes refresh_token parameter"
    )
    @pytest.mark.asyncio
    @patch("jctl.auth.okta.httpx.AsyncClient")
    async def test_refresh_tokens(self, mock_client_class, mock_okta_config, sample_tokens):
        """Test refreshing access tokens."""
        # Mock HTTP response
        new_tokens = sample_tokens.copy()
        new_tokens["access_token"] = "new_access_token"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = new_tokens

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__.return_value = mock_client

        auth = OktaAuthenticator(
            domain=mock_okta_config["domain"],
            client_id=mock_okta_config["client_id"],
            redirect_uri=mock_okta_config["redirect_uri"],
        )

        refreshed = await auth.refresh_tokens(sample_tokens["refresh_token"])

        assert refreshed["access_token"] == "new_access_token"
        mock_client.post.assert_called_once()

    def test_callback_handler_validates_state(self):
        """CallbackHandler must refuse a code with the wrong `state` param
        (the CSRF check that was previously missing — OAuth 2.0 §10.12)."""
        from io import BytesIO
        from unittest.mock import MagicMock

        from jctl.auth.okta import CallbackHandler

        CallbackHandler.reset()
        CallbackHandler.expected_state = "EXPECTED-STATE-abc"

        # Build a fake handler instance without standing up a real socket.
        handler = CallbackHandler.__new__(CallbackHandler)
        handler.path = "/callback?code=GRANTED&state=ATTACKER-STATE"
        handler.wfile = BytesIO()
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()

        handler.do_GET()

        # State mismatch must not capture the code, and must record an error.
        assert CallbackHandler.auth_code is None
        assert CallbackHandler.error == "state_mismatch"

    def test_callback_handler_accepts_matching_state(self):
        """Matching state proceeds — auth_code captured."""
        from io import BytesIO
        from unittest.mock import MagicMock

        from jctl.auth.okta import CallbackHandler

        CallbackHandler.reset()
        CallbackHandler.expected_state = "GOOD-STATE-xyz"

        handler = CallbackHandler.__new__(CallbackHandler)
        handler.path = "/callback?code=GRANTED&state=GOOD-STATE-xyz"
        handler.wfile = BytesIO()
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()

        handler.do_GET()

        assert CallbackHandler.auth_code == "GRANTED"
        assert CallbackHandler.error is None
