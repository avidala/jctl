"""Secure credential storage using OS keystore with file-based fallback.

Strategy:
* First-class storage path is the OS-native keystore via the ``keyring``
  package (macOS Keychain / Linux Secret Service / Windows Credential
  Manager).
* When the OS keystore is unavailable (locked, headless CI runner,
  permission-denied subprocess, etc.) we fall back to a per-user file
  ``~/.jctl/credentials.enc`` containing Fernet-encrypted ciphertext,
  with mode 0600 on the file and 0700 on the directory.

The previous implementation "encrypted the value and then wrote it back
into the same broken keyring backend", which was not a fallback at all
and meant headless/CI installs of jctl could not store credentials.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import platform
from collections.abc import Callable
from pathlib import Path

import keyring
from cryptography.fernet import Fernet, InvalidToken

from jctl.utils.logging import get_logger

logger = get_logger(__name__)

SERVICE_NAME = "jctl"


class KeystoreError(Exception):
    """Keystore error."""

    pass


def _config_dir() -> Path:
    """Resolve the jctl config dir, honoring ``$JCTL_CONFIG_DIR`` for tests."""
    override = os.environ.get("JCTL_CONFIG_DIR")
    if override:
        return Path(override)
    return Path.home() / ".jctl"


class _FileStore:
    """Encrypted file fallback for credentials when the OS keystore is unusable.

    Format: ``credentials.enc`` is a JSON object ``{key: ciphertext_b64}``
    where each ciphertext was produced by ``Fernet(<machine-derived key>)``.
    """

    def __init__(self, key_provider: Callable[[], bytes]) -> None:
        self.path = _config_dir() / "credentials.enc"
        self._key_provider = key_provider

    def _load(self) -> dict[str, str]:
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text())
            # json.loads is typed `Any`; the on-disk format is a
            # `{str: str}` dict — reject other shapes defensively.
            if not isinstance(data, dict):
                return {}
            return {str(k): str(v) for k, v in data.items()}
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Could not read fallback credentials file: {e}")
            return {}

    def _save(self, data: dict[str, str]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.path.parent.chmod(0o700)
        except OSError:
            pass
        # Write to a sibling tmp then rename so a crash mid-write can't
        # leave the file half-written.
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data))
        try:
            tmp.chmod(0o600)
        except OSError:
            pass
        tmp.replace(self.path)

    def store(self, key: str, value: str) -> None:
        cipher = Fernet(self._key_provider())
        data = self._load()
        data[key] = cipher.encrypt(value.encode()).decode()
        self._save(data)

    def retrieve(self, key: str) -> str | None:
        data = self._load()
        token = data.get(key)
        if not token:
            return None
        cipher = Fernet(self._key_provider())
        try:
            return cipher.decrypt(token.encode()).decode()
        except InvalidToken:
            logger.warning(f"Could not decrypt fallback entry for '{key}' — wrong key?")
            return None

    def delete(self, key: str) -> None:
        data = self._load()
        if key in data:
            del data[key]
            self._save(data)


class SecureKeystore:
    """Secure credential storage using OS-native keystore with encrypted fallback."""

    def __init__(self) -> None:
        self.system = platform.system()
        self._encryption_key: bytes | None = None
        self._file_store = _FileStore(key_provider=self._get_encryption_key)

    def _get_encryption_key(self) -> bytes:
        """Get or create the Fernet key used by the file-store fallback.

        Tries the OS keystore first (so the key survives across machines
        sharing the user's profile via secret-service). If that fails we
        derive a stable key from machine info — less robust but enables
        non-interactive contexts to keep working.
        """
        if self._encryption_key:
            return self._encryption_key

        try:
            key_str = keyring.get_password(SERVICE_NAME, "encryption_key")
            if key_str:
                self._encryption_key = key_str.encode()
                logger.debug("Retrieved encryption key from OS keystore")
                return self._encryption_key

            key = Fernet.generate_key()
            keyring.set_password(SERVICE_NAME, "encryption_key", key.decode())
            self._encryption_key = key
            logger.debug("Generated new encryption key in OS keystore")
            return key

        except Exception as e:  # noqa: BLE001
            logger.warning(f"Failed to manage encryption key in keystore: {e}")
            machine_id = f"{platform.node()}-{platform.system()}"
            derived = hashlib.pbkdf2_hmac(
                "sha256", machine_id.encode(), b"jctl-salt-v1", 100000, 32
            )
            self._encryption_key = base64.urlsafe_b64encode(derived)
            logger.debug("Using machine-derived encryption key")
            return self._encryption_key

    def store(self, key: str, value: str) -> None:
        """Store a credential.

        Tries the OS keystore first; if that fails (headless CI, locked
        keychain, etc.) writes an encrypted blob to the file fallback.
        """
        try:
            keyring.set_password(SERVICE_NAME, key, value)
            logger.debug(f"Stored credential '{key}' in OS keystore ({self.system})")
            return
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Failed to store in OS keystore, using file fallback: {e}")

        try:
            self._file_store.store(key, value)
            logger.debug(f"Stored credential '{key}' in encrypted file fallback")
        except Exception as e2:  # noqa: BLE001
            raise KeystoreError(f"Failed to store credential: {e2}") from e2

    def retrieve(self, key: str) -> str | None:
        """Retrieve a credential. Checks OS keystore then the file fallback."""
        try:
            value = keyring.get_password(SERVICE_NAME, key)
            if value:
                logger.debug(f"Retrieved credential '{key}' from OS keystore")
                return value
        except Exception as e:  # noqa: BLE001
            logger.warning(f"OS keystore unreadable, trying file fallback: {e}")

        try:
            value = self._file_store.retrieve(key)
            if value is not None:
                logger.debug(f"Retrieved credential '{key}' from file fallback")
            return value
        except Exception as e:  # noqa: BLE001
            logger.error(f"Failed to retrieve credential '{key}': {e}")
            return None

    def delete(self, key: str) -> None:
        """Delete a credential from both OS keystore and the file fallback."""
        try:
            keyring.delete_password(SERVICE_NAME, key)
            logger.debug(f"Deleted credential '{key}' from OS keystore")
        except keyring.errors.PasswordDeleteError:
            pass  # not present
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Failed to delete from OS keystore: {e}")  # nosec B608

        try:
            self._file_store.delete(key)
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Failed to delete file-fallback entry: {e}")

    def clear_all(self) -> None:
        """Clear all stored credentials."""
        self.delete("jenkins_username")
        self.delete("jenkins_token")
        self.delete("encryption_key")
        logger.info("Cleared all credentials from keystore")
