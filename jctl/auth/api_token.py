"""Jenkins API Token authentication (simpler alternative to OAuth)."""

from jctl.auth.keystore import SecureKeystore
from jctl.utils.logging import get_logger

logger = get_logger(__name__)


class APITokenAuthenticator:
    """Simple API token authentication for Jenkins."""

    def __init__(self):
        """Initialize API token authenticator."""
        self.keystore = SecureKeystore()

    def store_token(self, username: str, token: str) -> None:
        """Store Jenkins API token.

        Args:
            username: Jenkins username (your email)
            token: Jenkins API token
        """
        # Store individually for easier retrieval
        self.keystore.store("jenkins_username", username)
        self.keystore.store("jenkins_token", token)

        logger.info(f"Stored API token for user: {username}")

    def get_username(self) -> str | None:
        """Get stored Jenkins username.

        Returns:
            Username or None if not found
        """
        return self.keystore.retrieve("jenkins_username")

    def get_token(self) -> str | None:
        """Get stored Jenkins API token.

        Returns:
            API token or None if not found
        """
        return self.keystore.retrieve("jenkins_token")

    def get_credentials(self) -> tuple[str, str] | None:
        """Get stored credentials.

        Returns:
            Tuple of (username, token) or None if not found
        """
        username = self.get_username()
        token = self.get_token()

        if username and token:
            return (username, token)
        return None

    def is_authenticated(self) -> bool:
        """Check if API token is configured.

        Returns:
            True if username and token are stored
        """
        return bool(self.get_username() and self.get_token())

    def clear_token(self) -> None:
        """Clear stored API token."""
        self.keystore.delete("jenkins_username")
        self.keystore.delete("jenkins_token")
        logger.info("Cleared Jenkins API token")

    def get_auth_info(self) -> dict[str, bool | str | None]:
        """Get authentication information.

        Returns:
            Dictionary with auth status and username
        """
        username = self.get_username()
        token = self.get_token()

        return {
            "authenticated": bool(username and token),
            "username": username,
            "has_token": bool(token),
            "auth_method": "api_token",
        }
