"""Secure credential storage using OS keystore."""

import json
import platform
from typing import Any

import keyring
from cryptography.fernet import Fernet

from jctl.utils.logging import get_logger

logger = get_logger(__name__)

SERVICE_NAME = "jctl"


class KeystoreError(Exception):
    """Keystore error."""

    pass


class SecureKeystore:
    """Secure credential storage using OS-native keystore with encrypted fallback."""

    def __init__(self):
        """Initialize keystore."""
        self.system = platform.system()
        self._encryption_key: bytes | None = None

    def _get_encryption_key(self) -> bytes:
        """Get or create encryption key for fallback storage.

        Returns:
            Encryption key
        """
        if self._encryption_key:
            return self._encryption_key

        try:
            # Try to get existing key from keystore
            key_str = keyring.get_password(SERVICE_NAME, "encryption_key")
            if key_str:
                self._encryption_key = key_str.encode()
                logger.debug("Retrieved encryption key from keystore")
                return self._encryption_key

            # Generate new key
            key = Fernet.generate_key()
            keyring.set_password(SERVICE_NAME, "encryption_key", key.decode())
            self._encryption_key = key
            logger.debug("Generated new encryption key")
            return key

        except Exception as e:
            logger.warning(f"Failed to manage encryption key in keystore: {e}")
            # Use a static key derived from machine info (less secure but works)
            import base64
            import hashlib

            machine_id = f"{platform.node()}-{platform.system()}"
            key = hashlib.pbkdf2_hmac("sha256", machine_id.encode(), b"jctl-salt-v1", 100000, 32)
            # Convert the derived key to Fernet-compatible base64url format
            self._encryption_key = base64.urlsafe_b64encode(key)
            logger.debug("Using machine-derived encryption key")
            return self._encryption_key

    def store(self, key: str, value: str) -> None:
        """Store a credential securely.

        Args:
            key: Credential key
            value: Credential value

        Raises:
            KeystoreError: If storage fails
        """
        try:
            # Try OS keystore first
            keyring.set_password(SERVICE_NAME, key, value)
            logger.debug(f"Stored credential '{key}' in OS keystore ({self.system})")
        except Exception as e:
            logger.warning(f"Failed to store in OS keystore, using encrypted fallback: {e}")
            # Fallback to encrypted storage
            try:
                cipher = Fernet(self._get_encryption_key())
                encrypted = cipher.encrypt(value.encode())
                keyring.set_password(SERVICE_NAME, f"{key}_encrypted", encrypted.decode())
                logger.debug(f"Stored encrypted credential '{key}'")
            except Exception as e2:
                raise KeystoreError(f"Failed to store credential: {e2}")

    def retrieve(self, key: str) -> str | None:
        """Retrieve a credential.

        Args:
            key: Credential key

        Returns:
            Credential value or None if not found

        Raises:
            KeystoreError: If retrieval fails
        """
        try:
            # Try OS keystore first
            value = keyring.get_password(SERVICE_NAME, key)
            if value:
                logger.debug(f"Retrieved credential '{key}' from OS keystore")
                return value

            # Try encrypted fallback
            encrypted_value = keyring.get_password(SERVICE_NAME, f"{key}_encrypted")
            if encrypted_value:
                try:
                    cipher = Fernet(self._get_encryption_key())
                    decrypted = cipher.decrypt(encrypted_value.encode())
                    logger.debug(f"Retrieved encrypted credential '{key}'")
                    return decrypted.decode()
                except Exception as e:
                    logger.error(f"Failed to decrypt credential '{key}': {e}")
                    return None

            return None

        except Exception as e:
            logger.error(f"Failed to retrieve credential '{key}': {e}")
            return None

    def delete(self, key: str) -> None:
        """Delete a credential.

        Args:
            key: Credential key
        """
        try:
            # Delete from OS keystore
            keyring.delete_password(SERVICE_NAME, key)
            logger.debug(f"Deleted credential '{key}' from OS keystore")
        except keyring.errors.PasswordDeleteError:
            pass  # Credential doesn't exist
        except Exception as e:
            logger.warning(f"Failed to delete from OS keystore: {e}")

        try:
            # Delete encrypted version
            keyring.delete_password(SERVICE_NAME, f"{key}_encrypted")
            logger.debug(f"Deleted encrypted credential '{key}'")
        except keyring.errors.PasswordDeleteError:
            pass  # Credential doesn't exist
        except Exception as e:
            logger.warning(f"Failed to delete encrypted credential: {e}")

    def store_tokens(self, tokens: dict[str, Any]) -> None:
        """Store authentication tokens.

        Args:
            tokens: Token dictionary (access_token, refresh_token, etc.)

        Raises:
            KeystoreError: If storage fails
        """
        try:
            tokens_json = json.dumps(tokens)
            self.store("tokens", tokens_json)
            logger.info("Stored authentication tokens")
        except Exception as e:
            raise KeystoreError(f"Failed to store tokens: {e}")

    def retrieve_tokens(self) -> dict[str, Any] | None:
        """Retrieve authentication tokens.

        Returns:
            Token dictionary or None if not found

        Raises:
            KeystoreError: If retrieval fails
        """
        try:
            tokens_json = self.retrieve("tokens")
            if tokens_json:
                tokens = json.loads(tokens_json)
                logger.debug("Retrieved authentication tokens")
                return tokens
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve tokens: {e}")
            return None

    def delete_tokens(self) -> None:
        """Delete authentication tokens."""
        self.delete("tokens")
        logger.info("Deleted authentication tokens")

    def clear_all(self) -> None:
        """Clear all stored credentials."""
        self.delete_tokens()
        self.delete("encryption_key")
        logger.info("Cleared all credentials from keystore")
