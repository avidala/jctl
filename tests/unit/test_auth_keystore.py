"""Tests for secure keystore."""

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
    def test_store_falls_back_to_file_when_keystore_unusable(
        self, mock_keyring, monkeypatch, tmp_path
    ):
        """When `keyring.set_password` raises, value must land in the file fallback."""
        monkeypatch.setenv("JCTL_CONFIG_DIR", str(tmp_path))
        mock_keyring.set_password.side_effect = Exception("Keystore locked")
        # Encryption-key retrieval also fails so we exercise machine-derived key path.
        mock_keyring.get_password.side_effect = Exception("Keystore locked")

        keystore = SecureKeystore()
        keystore.store("jenkins_token", "s3cr3t")

        # File fallback must have been created with 0600 mode.
        cred_file = tmp_path / "credentials.enc"
        assert cred_file.exists()
        import sys

        if sys.platform != "win32":
            assert oct(cred_file.stat().st_mode)[-3:] == "600"

        # Round-trip: retrieve must find it via the file fallback too.
        # The keyring lookup will return None (no real entry); file fallback wins.
        mock_keyring.get_password.side_effect = Exception("Keystore locked")
        got = keystore.retrieve("jenkins_token")
        assert got == "s3cr3t"

    @patch("jctl.auth.keystore.keyring")
    def test_retrieve_from_keystore(self, mock_keyring):
        """Test retrieving credential from keystore."""
        mock_keyring.get_password.return_value = "test_value"

        keystore = SecureKeystore()
        value = keystore.retrieve("test_key")

        assert value == "test_value"
        mock_keyring.get_password.assert_called_once_with("jctl", "test_key")

    @patch("jctl.auth.keystore.keyring")
    def test_retrieve_falls_back_to_file(self, mock_keyring, monkeypatch, tmp_path):
        """retrieve() should consult the file fallback when keystore has no entry."""
        monkeypatch.setenv("JCTL_CONFIG_DIR", str(tmp_path))
        # OS keystore has nothing; file fallback has the credential.
        mock_keyring.get_password.return_value = None
        mock_keyring.set_password.side_effect = Exception("Keystore locked")

        # Seed the file fallback by going through store() while keystore is
        # broken — same path the bug-fix exercises in production.
        keystore = SecureKeystore()
        keystore.store("jenkins_token", "s3cr3t-from-file")

        # New instance to ensure we're not reading from in-memory cache.
        keystore2 = SecureKeystore()
        assert keystore2.retrieve("jenkins_token") == "s3cr3t-from-file"

    @patch("jctl.auth.keystore.keyring")
    def test_retrieve_not_found(self, mock_keyring):
        """Test retrieving non-existent credential."""
        mock_keyring.get_password.return_value = None

        keystore = SecureKeystore()
        value = keystore.retrieve("nonexistent_key")

        assert value is None

    @patch("jctl.auth.keystore.keyring")
    def test_delete_success(self, mock_keyring):
        """delete() removes the entry from the OS keystore (one call)."""
        mock_keyring.delete_password = MagicMock()

        keystore = SecureKeystore()
        keystore.delete("test_key")

        mock_keyring.delete_password.assert_called_once_with("jctl", "test_key")

    @patch("jctl.auth.keystore.keyring")
    def test_clear_all(self, mock_keyring):
        """Test clearing all credentials."""
        mock_keyring.delete_password = MagicMock()

        keystore = SecureKeystore()
        keystore.clear_all()

        # username + token + encryption_key, each tries plain + _encrypted = 6 calls
        assert mock_keyring.delete_password.call_count >= 3
