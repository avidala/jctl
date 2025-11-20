"""Tests for API token authentication."""

from unittest.mock import MagicMock, patch

from jctl.auth.api_token import APITokenAuthenticator


class TestAPITokenAuthenticator:
    """Tests for API token authentication."""

    @patch("jctl.auth.api_token.SecureKeystore")
    def test_init(self, mock_keystore_class):
        """Test APITokenAuthenticator initialization."""
        mock_keystore = MagicMock()
        mock_keystore_class.return_value = mock_keystore

        auth = APITokenAuthenticator()
        assert auth.keystore == mock_keystore

    @patch("jctl.auth.api_token.SecureKeystore")
    def test_store_token(self, mock_keystore_class):
        """Test storing API token."""
        mock_keystore = MagicMock()
        mock_keystore_class.return_value = mock_keystore

        auth = APITokenAuthenticator()
        auth.store_token("test-user", "test-token")

        # Verify keystore methods were called
        assert mock_keystore.store.call_count == 2
        mock_keystore.store.assert_any_call("jenkins_username", "test-user")
        mock_keystore.store.assert_any_call("jenkins_token", "test-token")

    @patch("jctl.auth.api_token.SecureKeystore")
    def test_get_username(self, mock_keystore_class):
        """Test getting stored username."""
        mock_keystore = MagicMock()
        mock_keystore.retrieve.return_value = "test-user"
        mock_keystore_class.return_value = mock_keystore

        auth = APITokenAuthenticator()
        username = auth.get_username()

        assert username == "test-user"
        mock_keystore.retrieve.assert_called_once_with("jenkins_username")

    @patch("jctl.auth.api_token.SecureKeystore")
    def test_get_token(self, mock_keystore_class):
        """Test getting stored token."""
        mock_keystore = MagicMock()
        mock_keystore.retrieve.return_value = "test-token"
        mock_keystore_class.return_value = mock_keystore

        auth = APITokenAuthenticator()
        token = auth.get_token()

        assert token == "test-token"
        mock_keystore.retrieve.assert_called_once_with("jenkins_token")

    @patch("jctl.auth.api_token.SecureKeystore")
    def test_get_credentials(self, mock_keystore_class):
        """Test getting credentials."""
        mock_keystore = MagicMock()
        mock_keystore.retrieve.side_effect = ["test-user", "test-token"]
        mock_keystore_class.return_value = mock_keystore

        auth = APITokenAuthenticator()
        credentials = auth.get_credentials()

        assert credentials == ("test-user", "test-token")

    @patch("jctl.auth.api_token.SecureKeystore")
    def test_get_credentials_missing(self, mock_keystore_class):
        """Test getting credentials when none exist."""
        mock_keystore = MagicMock()
        mock_keystore.retrieve.return_value = None
        mock_keystore_class.return_value = mock_keystore

        auth = APITokenAuthenticator()
        credentials = auth.get_credentials()

        assert credentials is None

    @patch("jctl.auth.api_token.SecureKeystore")
    def test_is_authenticated(self, mock_keystore_class):
        """Test authentication status check."""
        mock_keystore = MagicMock()
        mock_keystore.retrieve.side_effect = ["test-user", "test-token"]
        mock_keystore_class.return_value = mock_keystore

        auth = APITokenAuthenticator()
        assert auth.is_authenticated() is True

    @patch("jctl.auth.api_token.SecureKeystore")
    def test_is_not_authenticated(self, mock_keystore_class):
        """Test authentication status when not authenticated."""
        mock_keystore = MagicMock()
        mock_keystore.retrieve.return_value = None
        mock_keystore_class.return_value = mock_keystore

        auth = APITokenAuthenticator()
        assert auth.is_authenticated() is False

    @patch("jctl.auth.api_token.SecureKeystore")
    def test_clear_token(self, mock_keystore_class):
        """Test clearing stored token."""
        mock_keystore = MagicMock()
        mock_keystore_class.return_value = mock_keystore

        auth = APITokenAuthenticator()
        auth.clear_token()

        # Verify keystore delete methods were called
        assert mock_keystore.delete.call_count == 2
        mock_keystore.delete.assert_any_call("jenkins_username")
        mock_keystore.delete.assert_any_call("jenkins_token")

    @patch("jctl.auth.api_token.SecureKeystore")
    def test_get_auth_info(self, mock_keystore_class):
        """Test getting authentication info."""
        mock_keystore = MagicMock()
        mock_keystore.retrieve.side_effect = ["test-user", "test-token"]
        mock_keystore_class.return_value = mock_keystore

        auth = APITokenAuthenticator()
        info = auth.get_auth_info()

        assert info["authenticated"] is True
        assert info["username"] == "test-user"
        assert info["has_token"] is True
        assert info["auth_method"] == "api_token"
