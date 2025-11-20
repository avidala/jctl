"""Tests for secure keystore."""

import json
from unittest.mock import MagicMock, patch

from jctl.auth.keystore import SecureKeystore


class TestSecureKeystore:
    """Tests for secure credential storage."""

    def test_init(self):
        """Test keystore initialization."""
        keystore = SecureKeystore()
        assert keystore.system in ["Darwin", "Linux", "Windows"]
        assert keystore._encryption_key is None

    @patch("jctl.auth.keystore.keyring")
    def test_get_encryption_key_from_keystore(self, mock_keyring):
        """Test retrieving existing encryption key from keystore."""
        mock_keyring.get_password.return_value = "dGVzdC1lbmNyeXB0aW9uLWtleQ=="
        mock_keyring.set_password = MagicMock()

        keystore = SecureKeystore()
        key = keystore._get_encryption_key()

        assert key == b"dGVzdC1lbmNyeXB0aW9uLWtleQ=="
        mock_keyring.get_password.assert_called_once_with("jctl", "encryption_key")
        mock_keyring.set_password.assert_not_called()

    @patch("jctl.auth.keystore.keyring")
    def test_get_encryption_key_generate_new(self, mock_keyring):
        """Test generating new encryption key when none exists."""
        mock_keyring.get_password.return_value = None
        mock_keyring.set_password = MagicMock()

        keystore = SecureKeystore()
        key = keystore._get_encryption_key()

        assert len(key) == 44  # Fernet key is 44 bytes base64 encoded
        mock_keyring.get_password.assert_called_once_with("jctl", "encryption_key")
        mock_keyring.set_password.assert_called_once()

    @patch("jctl.auth.keystore.keyring")
    @patch("jctl.auth.keystore.platform")
    def test_get_encryption_key_fallback(self, mock_platform, mock_keyring):
        """Test fallback encryption key derivation when keystore fails."""
        mock_keyring.get_password.side_effect = Exception("Keystore unavailable")
        mock_platform.node.return_value = "test-machine"
        mock_platform.system.return_value = "Darwin"

        keystore = SecureKeystore()
        key = keystore._get_encryption_key()

        # Should return deterministic key derived from machine info
        assert len(key) == 44  # Fernet key format
        assert keystore._encryption_key == key

        # Calling again should return same key (deterministic)
        key2 = keystore._get_encryption_key()
        assert key2 == key

    @patch("jctl.auth.keystore.keyring")
    def test_store_success(self, mock_keyring):
        """Test storing credential successfully."""
        mock_keyring.set_password = MagicMock()

        keystore = SecureKeystore()
        keystore.store("test_key", "test_value")

        mock_keyring.set_password.assert_called_once_with("jctl", "test_key", "test_value")

    @patch("jctl.auth.keystore.keyring")
    def test_store_with_encryption_fallback(self, mock_keyring):
        """Test storing credential with encryption when keystore fails."""
        mock_keyring.set_password.side_effect = [
            Exception("Keystore unavailable"),  # First call fails
            None,  # Second call for encrypted value succeeds
        ]
        mock_keyring.get_password.side_effect = [None, "dGVzdC1rZXk="]  # For _get_encryption_key

        keystore = SecureKeystore()
        keystore.store("test_key", "test_value")

        # Should have called set_password twice (once failed, once for encrypted)
        assert mock_keyring.set_password.call_count == 3  # encryption key + failed + encrypted

    @patch("jctl.auth.keystore.keyring")
    def test_retrieve_from_keystore(self, mock_keyring):
        """Test retrieving credential from keystore."""
        mock_keyring.get_password.return_value = "test_value"

        keystore = SecureKeystore()
        value = keystore.retrieve("test_key")

        assert value == "test_value"
        mock_keyring.get_password.assert_called_once_with("jctl", "test_key")

    @patch("jctl.auth.keystore.keyring")
    def test_retrieve_encrypted(self, mock_keyring):
        """Test retrieving encrypted credential."""
        from cryptography.fernet import Fernet

        # Create a test encryption key and encrypt a value
        test_key = Fernet.generate_key()
        cipher = Fernet(test_key)
        encrypted = cipher.encrypt(b"test_value")

        mock_keyring.get_password.side_effect = [
            None,  # Regular key doesn't exist
            encrypted.decode(),  # Encrypted key exists
            test_key.decode(),  # Encryption key
        ]

        keystore = SecureKeystore()
        keystore._encryption_key = test_key  # Set the key directly
        value = keystore.retrieve("test_key")

        assert value == "test_value"

    @patch("jctl.auth.keystore.keyring")
    def test_retrieve_not_found(self, mock_keyring):
        """Test retrieving non-existent credential."""
        mock_keyring.get_password.return_value = None

        keystore = SecureKeystore()
        value = keystore.retrieve("nonexistent_key")

        assert value is None

    @patch("jctl.auth.keystore.keyring")
    def test_delete_success(self, mock_keyring):
        """Test deleting credential."""
        mock_keyring.delete_password = MagicMock()

        keystore = SecureKeystore()
        keystore.delete("test_key")

        assert mock_keyring.delete_password.call_count == 2  # Regular and encrypted versions

    @patch("jctl.auth.keystore.keyring")
    def test_store_tokens(self, mock_keyring, sample_tokens):
        """Test storing authentication tokens."""
        mock_keyring.set_password = MagicMock()

        keystore = SecureKeystore()
        keystore.store_tokens(sample_tokens)

        mock_keyring.set_password.assert_called_once()
        call_args = mock_keyring.set_password.call_args
        assert call_args[0][1] == "tokens"

        # Verify tokens were serialized to JSON
        stored_json = call_args[0][2]
        stored_tokens = json.loads(stored_json)
        assert stored_tokens["access_token"] == sample_tokens["access_token"]

    @patch("jctl.auth.keystore.keyring")
    def test_retrieve_tokens(self, mock_keyring, sample_tokens):
        """Test retrieving authentication tokens."""
        tokens_json = json.dumps(sample_tokens)
        mock_keyring.get_password.return_value = tokens_json

        keystore = SecureKeystore()
        tokens = keystore.retrieve_tokens()

        assert tokens == sample_tokens
        mock_keyring.get_password.assert_called_once_with("jctl", "tokens")

    @patch("jctl.auth.keystore.keyring")
    def test_retrieve_tokens_not_found(self, mock_keyring):
        """Test retrieving tokens when none exist."""
        mock_keyring.get_password.return_value = None

        keystore = SecureKeystore()
        tokens = keystore.retrieve_tokens()

        assert tokens is None

    @patch("jctl.auth.keystore.keyring")
    def test_delete_tokens(self, mock_keyring):
        """Test deleting authentication tokens."""
        mock_keyring.delete_password = MagicMock()

        keystore = SecureKeystore()
        keystore.delete_tokens()

        # Should delete both regular and encrypted versions
        assert mock_keyring.delete_password.call_count == 2

    @patch("jctl.auth.keystore.keyring")
    def test_clear_all(self, mock_keyring):
        """Test clearing all credentials."""
        mock_keyring.delete_password = MagicMock()

        keystore = SecureKeystore()
        keystore.clear_all()

        # Should delete tokens and encryption key
        assert mock_keyring.delete_password.call_count >= 2
