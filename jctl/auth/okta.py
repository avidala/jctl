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
    """HTTP server handler for OAuth callback."""

    auth_code: str | None = None
    error: str | None = None

    def do_GET(self) -> None:
        """Handle GET request with OAuth callback."""
        # Parse query parameters
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if "code" in params:
            CallbackHandler.auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"""
                <html>
                <head><title>Authentication Successful</title></head>
                <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                    <h1 style="color: green;">&#10003; Authentication Successful!</h1>
                    <p>You can close this window and return to the terminal.</p>
                </body>
                </html>
                """
            )
        elif "error" in params:
            CallbackHandler.error = params["error"][0]
            error_desc = params.get("error_description", ["Unknown error"])[0]
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                f"""
                <html>
                <head><title>Authentication Failed</title></head>
                <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                    <h1 style="color: red;">&#10007; Authentication Failed</h1>
                    <p>{error_desc}</p>
                    <p>Please return to the terminal and try again.</p>
                </body>
                </html>
                """.encode()
            )
        else:
            self.send_response(400)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Invalid callback")

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

    def login(self) -> dict[str, Any]:
        """Perform OAuth login with PKCE.

        Returns:
            Token response dictionary

        Raises:
            OktaAuthError: If authentication fails
        """
        logger.info("Starting Okta OAuth authentication...")

        # Generate PKCE pair
        code_verifier, code_challenge = self._generate_pkce_pair()

        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)

        # Build authorization URL
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

        # Open browser
        webbrowser.open(auth_url)

        # Start local server to receive callback
        server_address = ("", 8989)
        httpd = HTTPServer(server_address, CallbackHandler)

        logger.info("Waiting for OAuth callback...")
        print("⏳ Waiting for authentication in browser...")

        # Wait for one request (the callback)
        httpd.handle_request()

        # Check for error
        if CallbackHandler.error:
            error_msg = f"OAuth error: {CallbackHandler.error}"
            logger.error(error_msg)
            raise OktaAuthError(error_msg)

        # Get authorization code
        auth_code = CallbackHandler.auth_code
        if not auth_code:
            raise OktaAuthError("No authorization code received")

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
