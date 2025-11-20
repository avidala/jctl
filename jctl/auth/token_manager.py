"""Token lifecycle management."""

import time
from typing import Any

from jctl.auth.keystore import SecureKeystore
from jctl.utils.logging import get_logger

logger = get_logger(__name__)


class TokenManager:
    """Manage OAuth token lifecycle."""

    def __init__(self, keystore: SecureKeystore | None = None):
        """Initialize token manager.

        Args:
            keystore: Keystore instance (creates new if None)
        """
        self.keystore = keystore or SecureKeystore()

    def store_tokens(
        self,
        access_token: str,
        refresh_token: str | None = None,
        id_token: str | None = None,
        expires_in: int | None = None,
    ) -> None:
        """Store authentication tokens.

        Args:
            access_token: OAuth access token
            refresh_token: OAuth refresh token
            id_token: OpenID Connect ID token
            expires_in: Token expiry in seconds
        """
        tokens = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "id_token": id_token,
            "expires_at": int(time.time()) + expires_in if expires_in else None,
            "stored_at": int(time.time()),
        }

        self.keystore.store_tokens(tokens)
        logger.info("Stored authentication tokens")

    def get_tokens(self) -> dict[str, Any] | None:
        """Get stored tokens.

        Returns:
            Token dictionary or None if not found
        """
        return self.keystore.retrieve_tokens()

    def get_access_token(self) -> str | None:
        """Get access token.

        Returns:
            Access token or None if not found/expired
        """
        tokens = self.get_tokens()
        if not tokens:
            return None

        # Check if token is expired
        if self.is_expired():
            logger.warning("Access token is expired")
            return None

        return tokens.get("access_token")

    def get_refresh_token(self) -> str | None:
        """Get refresh token.

        Returns:
            Refresh token or None if not found
        """
        tokens = self.get_tokens()
        if not tokens:
            return None

        return tokens.get("refresh_token")

    def is_expired(self, buffer_seconds: int = 300) -> bool:
        """Check if access token is expired.

        Args:
            buffer_seconds: Consider token expired N seconds before actual expiry

        Returns:
            True if token is expired or will expire soon
        """
        tokens = self.get_tokens()
        if not tokens:
            return True

        expires_at = tokens.get("expires_at")
        if not expires_at:
            # No expiry info, assume valid
            return False

        current_time = int(time.time())
        return current_time >= (expires_at - buffer_seconds)

    def needs_refresh(self, buffer_seconds: int = 600) -> bool:
        """Check if token should be refreshed.

        Args:
            buffer_seconds: Refresh if expiring within N seconds

        Returns:
            True if token should be refreshed
        """
        tokens = self.get_tokens()
        if not tokens:
            return False

        if not tokens.get("refresh_token"):
            return False

        expires_at = tokens.get("expires_at")
        if not expires_at:
            return False

        current_time = int(time.time())
        return current_time >= (expires_at - buffer_seconds)

    def is_authenticated(self) -> bool:
        """Check if user is authenticated with valid token.

        Returns:
            True if authenticated with non-expired token
        """
        tokens = self.get_tokens()
        if not tokens or not tokens.get("access_token"):
            return False

        return not self.is_expired()

    def clear_tokens(self) -> None:
        """Clear all stored tokens."""
        self.keystore.delete_tokens()
        logger.info("Cleared authentication tokens")

    def get_token_info(self) -> dict[str, Any]:
        """Get information about stored tokens.

        Returns:
            Dictionary with token status information
        """
        tokens = self.get_tokens()

        if not tokens:
            return {
                "authenticated": False,
                "has_tokens": False,
            }

        expires_at = tokens.get("expires_at")
        current_time = int(time.time())

        if expires_at:
            expires_in = expires_at - current_time
            expired = expires_in <= 0
        else:
            expires_in = None
            expired = False

        return {
            "authenticated": not expired,
            "has_tokens": True,
            "has_access_token": bool(tokens.get("access_token")),
            "has_refresh_token": bool(tokens.get("refresh_token")),
            "has_id_token": bool(tokens.get("id_token")),
            "expired": expired,
            "expires_in": expires_in,
            "expires_at": expires_at,
            "stored_at": tokens.get("stored_at"),
        }
