"""Jenkins API token authentication."""

from jctl.auth.keystore import SecureKeystore
from jctl.utils.logging import get_logger

logger = get_logger(__name__)


class APITokenAuthenticator:
    """Simple API token authentication for Jenkins."""

    def __init__(self) -> None:
        """Initialize API token authenticator."""
        self.keystore = SecureKeystore()

    def store_token(self, username: str, token: str) -> None:
        """Store Jenkins API token.

        Args:
            username: Jenkins username (your email)
            token: Jenkins API token
        """
        self.keystore.store("jenkins_username", username)
        self.keystore.store("jenkins_token", token)

        logger.info(f"Stored API token for user: {username}")

    def get_username(self) -> str | None:
        """Get stored Jenkins username."""
        return self.keystore.retrieve("jenkins_username")

    def get_token(self) -> str | None:
        """Get stored Jenkins API token."""
        return self.keystore.retrieve("jenkins_token")

    def get_credentials(self) -> tuple[str, str] | None:
        """Get stored credentials, or None if either piece is missing."""
        username = self.get_username()
        token = self.get_token()

        if username and token:
            return (username, token)
        return None

    def is_authenticated(self) -> bool:
        """Check if API token is configured."""
        return bool(self.get_username() and self.get_token())

    def clear_token(self) -> None:
        """Clear stored API token."""
        self.keystore.delete("jenkins_username")
        self.keystore.delete("jenkins_token")
        logger.info("Cleared Jenkins API token")

    def get_auth_info(self) -> dict[str, bool | str | None]:
        """Get authentication status info for display."""
        username = self.get_username()
        token = self.get_token()

        return {
            "authenticated": bool(username and token),
            "username": username,
            "has_token": bool(token),
            "auth_method": "api_token",
        }
