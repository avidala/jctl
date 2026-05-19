"""Okta OAuth 2.0 authentication with PKCE."""

import base64
import hashlib
import secrets
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse

import httpx

from jctl.auth.token_manager import TokenManager
from jctl.utils.logging import get_logger

logger = get_logger(__name__)


class OktaAuthError(Exception):
    """Okta authentication error."""

    pass


class CallbackHandler(BaseHTTPRequestHandler):
    """HTTP server handler for OAuth callback.

    Class-level attributes are used to carry results across to the calling
    `login()` because BaseHTTPServer instantiates handlers per request.
    `reset()` MUST be called before each login flow to clear stale state.
    """

    auth_code: str | None = None
    error: str | None = None
    expected_state: str | None = None

    @classmethod
    def reset(cls) -> None:
        cls.auth_code = None
        cls.error = None
        cls.expected_state = None

    def do_GET(self) -> None:
        """Handle GET request with OAuth callback."""
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if "code" in params:
            # CSRF: validate the state echoed back by Okta matches what we sent.
            returned_state = (params.get("state") or [None])[0]
            if (
                not CallbackHandler.expected_state
                or returned_state != CallbackHandler.expected_state
            ):
                CallbackHandler.error = "state_mismatch"
                self._send_error_page(
                    "Authentication Failed",
                    "State parameter mismatch (possible CSRF).",
                )
                return

            CallbackHandler.auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <head><title>Authentication Successful</title></head>
                <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                    <h1 style="color: green;">&#10003; Authentication Successful!</h1>
                    <p>You can close this window and return to the terminal.</p>
                </body>
                </html>
                """)
        elif "error" in params:
            CallbackHandler.error = params["error"][0]
            error_desc = params.get("error_description", ["Unknown error"])[0]
            self._send_error_page("Authentication Failed", error_desc)
        else:
            self.send_response(400)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Invalid callback")

    def _send_error_page(self, title: str, desc: str) -> None:
        self.send_response(400)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        body = f"""
            <html>
            <head><title>{title}</title></head>
            <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                <h1 style="color: red;">&#10007; {title}</h1>
                <p>{desc}</p>
                <p>Please return to the terminal and try again.</p>
            </body>
            </html>
            """
        self.wfile.write(body.encode())

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress log messages."""
        pass


class OktaAuthenticator:
    """Okta OAuth 2.0 authenticator with PKCE."""

    def __init__(
        self,
        domain: str,
        client_id: str,
        redirect_uri: str = "http://localhost:8989/callback",
        scopes: list[str] | None = None,
    ):
        """Initialize Okta authenticator.

        Args:
            domain: Okta domain (e.g., company.okta.com)
            client_id: OAuth client ID
            redirect_uri: OAuth redirect URI
            scopes: OAuth scopes
        """
        self.domain = domain.rstrip("/")
        self.client_id = client_id
        self.redirect_uri = redirect_uri
        self.scopes = scopes or ["openid", "profile", "email", "offline_access"]

        # Okta endpoints
        self.authorization_endpoint = f"https://{self.domain}/oauth2/v1/authorize"
        self.token_endpoint = f"https://{self.domain}/oauth2/v1/token"
        self.userinfo_endpoint = f"https://{self.domain}/oauth2/v1/userinfo"

        self.token_manager = TokenManager()

    def _generate_pkce_pair(self) -> tuple[str, str]:
        """Generate PKCE code verifier and challenge.

        Returns:
            Tuple of (code_verifier, code_challenge)
        """
        # Generate code verifier (43-128 characters)
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("utf-8")
        code_verifier = code_verifier.rstrip("=")

        # Generate code challenge (SHA256 hash of verifier)
        code_challenge = hashlib.sha256(code_verifier.encode("utf-8")).digest()
        code_challenge = base64.urlsafe_b64encode(code_challenge).decode("utf-8")
        code_challenge = code_challenge.rstrip("=")

        return code_verifier, code_challenge

    def login(self, callback_timeout: int = 120) -> dict[str, Any]:
        """Perform OAuth login with PKCE.

        Args:
            callback_timeout: Seconds to wait for the browser to redirect
                back before giving up.

        Returns:
            Token response dictionary

        Raises:
            OktaAuthError: If authentication fails or times out.
        """
        logger.info("Starting Okta OAuth authentication...")

        # Reset class-level handler state so a previous login attempt can't
        # leak its code/error/expected_state into this one.
        CallbackHandler.reset()

        code_verifier, code_challenge = self._generate_pkce_pair()
        state = secrets.token_urlsafe(32)
        CallbackHandler.expected_state = state

        auth_params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(self.scopes),
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        auth_url = f"{self.authorization_endpoint}?{urlencode(auth_params)}"

        logger.info(f"Opening browser for authentication: {self.domain}")
        print("\n🔐 Opening browser for Okta authentication...")
        print(f"    If browser doesn't open, visit: {auth_url}\n")
        webbrowser.open(auth_url)

        # Bind to loopback only so the callback URL isn't reachable from
        # other interfaces on the same network. Set a timeout on the server
        # so a never-completed browser flow doesn't block forever.
        server_address = ("127.0.0.1", 8989)
        httpd = HTTPServer(server_address, CallbackHandler)
        httpd.timeout = callback_timeout

        logger.info(f"Waiting for OAuth callback (timeout={callback_timeout}s)...")
        print("⏳ Waiting for authentication in browser...")

        # handle_request returns without setting code/error if the socket
        # times out; treat that as a clear error rather than blocking.
        httpd.handle_request()

        if CallbackHandler.error:
            error_msg = f"OAuth error: {CallbackHandler.error}"
            logger.error(error_msg)
            raise OktaAuthError(error_msg)

        auth_code = CallbackHandler.auth_code
        if not auth_code:
            raise OktaAuthError(
                f"OAuth callback timed out after {callback_timeout}s — "
                "did you complete the browser flow?"
            )

        logger.info("Received authorization code, exchanging for tokens...")

        # Exchange code for tokens
        token_params = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "code_verifier": code_verifier,
        }

        try:
            response = httpx.post(
                self.token_endpoint,
                data=token_params,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            tokens = response.json()

            logger.info("Successfully received tokens")

            # Store tokens
            self.token_manager.store_tokens(
                access_token=tokens["access_token"],
                refresh_token=tokens.get("refresh_token"),
                id_token=tokens.get("id_token"),
                expires_in=tokens.get("expires_in"),
            )

            return tokens

        except httpx.HTTPStatusError as e:
            error_msg = f"Token exchange failed: {e.response.status_code} - {e.response.text}"
            logger.error(error_msg)
            raise OktaAuthError(error_msg) from e
        except Exception as e:
            error_msg = f"Authentication failed: {e}"
            logger.error(error_msg)
            raise OktaAuthError(error_msg) from e

    def refresh_tokens(self) -> dict[str, Any]:
        """Refresh access token using refresh token.

        Returns:
            New token response

        Raises:
            OktaAuthError: If refresh fails
        """
        refresh_token = self.token_manager.get_refresh_token()
        if not refresh_token:
            raise OktaAuthError("No refresh token available")

        logger.info("Refreshing access token...")

        token_params = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "scope": " ".join(self.scopes),
        }

        try:
            response = httpx.post(
                self.token_endpoint,
                data=token_params,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            tokens = response.json()

            logger.info("Successfully refreshed tokens")

            # Update stored tokens
            self.token_manager.store_tokens(
                access_token=tokens["access_token"],
                refresh_token=tokens.get("refresh_token", refresh_token),
                id_token=tokens.get("id_token"),
                expires_in=tokens.get("expires_in"),
            )

            return tokens

        except httpx.HTTPStatusError as e:
            error_msg = f"Token refresh failed: {e.response.status_code} - {e.response.text}"
            logger.error(error_msg)
            raise OktaAuthError(error_msg) from e
        except Exception as e:
            error_msg = f"Token refresh failed: {e}"
            logger.error(error_msg)
            raise OktaAuthError(error_msg) from e

    def get_user_info(self) -> dict[str, Any]:
        """Get user information from Okta.

        Returns:
            User info dictionary

        Raises:
            OktaAuthError: If request fails
        """
        access_token = self.token_manager.get_access_token()
        if not access_token:
            raise OktaAuthError("Not authenticated")

        try:
            response = httpx.get(
                self.userinfo_endpoint, headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            error_msg = f"Failed to get user info: {e.response.status_code}"
            logger.error(error_msg)
            raise OktaAuthError(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to get user info: {e}"
            logger.error(error_msg)
            raise OktaAuthError(error_msg) from e

    def logout(self) -> None:
        """Logout and clear stored tokens."""
        self.token_manager.clear_tokens()
        logger.info("Logged out successfully")

    def is_authenticated(self) -> bool:
        """Check if user is authenticated.

        Returns:
            True if authenticated with valid token
        """
        return self.token_manager.is_authenticated()
