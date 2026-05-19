"""Tests for configuration manager."""

import sys
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from jctl.config.manager import ConfigManager
from jctl.config.schemas import Config


class TestConfigManager:
    """Tests for configuration management."""

    def test_init_default_path(self):
        """Test ConfigManager initialization with default path."""
        manager = ConfigManager()
        assert manager.config_dir == Path.home() / ".jctl"
        assert manager.config_file == Path.home() / ".jctl" / "config.yaml"

    def test_init_custom_path(self, temp_config_dir):
        """Test ConfigManager initialization with custom path."""
        manager = ConfigManager(config_dir=temp_config_dir)
        assert manager.config_dir == temp_config_dir
        assert manager.config_file == temp_config_dir / "config.yaml"

    @pytest.mark.skipif(
        sys.platform == "win32", reason="Unix file permissions don't apply on Windows"
    )
    def test_ensure_config_dir(self, temp_config_dir):
        """Test ensuring config directory exists."""
        config_dir = temp_config_dir / "new_config"
        manager = ConfigManager(config_dir=config_dir)

        assert not config_dir.exists()
        manager.ensure_config_dir()
        assert config_dir.exists()

        stat_info = config_dir.stat()
        assert oct(stat_info.st_mode)[-3:] == "700"

    def test_load_config_not_found(self, temp_config_dir):
        """Test loading config when file doesn't exist."""
        manager = ConfigManager(config_dir=temp_config_dir)

        with pytest.raises(FileNotFoundError) as exc_info:
            manager.load()

        assert "Configuration file not found" in str(exc_info.value)
        assert "jctl config init" in str(exc_info.value)

    def test_load_config_success(self, temp_config_dir):
        """Test loading valid configuration."""
        config_data = {
            "version": "1.0",
            "default_profile": "production",
            "profiles": {
                "production": {
                    "jenkins": {
                        "url": "https://jenkins.example.com",
                        "api_version": "2.0",
                    },
                }
            },
        }

        config_file = temp_config_dir / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(config_dir=temp_config_dir)
        config = manager.load()

        assert isinstance(config, Config)
        assert config.version == "1.0"
        assert config.default_profile == "production"
        assert "production" in config.profiles

    def test_save_config(self, temp_config_dir):
        """Test saving configuration."""
        manager = ConfigManager(config_dir=temp_config_dir)
        manager.ensure_config_dir()

        from jctl.config.schemas import JenkinsConfig, ProfileConfig

        config = Config(
            version="1.0",
            default_profile="test",
            profiles={
                "test": ProfileConfig(
                    jenkins=JenkinsConfig(
                        url="https://jenkins.test.com",
                        api_version="2.0",
                    ),
                )
            },
        )

        manager.save(config)

        assert manager.config_file.exists()

        if sys.platform != "win32":
            stat_info = manager.config_file.stat()
            assert oct(stat_info.st_mode)[-3:] == "600"

        with open(manager.config_file) as f:
            saved_data = yaml.safe_load(f)

        assert saved_data["version"] == "1.0"
        assert saved_data["default_profile"] == "test"

    def test_get_profile(self, temp_config_dir):
        """Test getting a specific profile."""
        config_data = {
            "version": "1.0",
            "default_profile": "production",
            "profiles": {
                "production": {
                    "jenkins": {
                        "url": "https://jenkins.prod.com",
                        "api_version": "2.0",
                    },
                },
                "staging": {
                    "jenkins": {
                        "url": "https://jenkins.staging.com",
                        "api_version": "2.0",
                    },
                },
            },
        }

        config_file = temp_config_dir / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(config_dir=temp_config_dir)
        config = manager.load()

        prod_profile = config.get_profile("production")
        assert str(prod_profile.jenkins.url).rstrip("/") == "https://jenkins.prod.com"

        staging_profile = config.get_profile("staging")
        assert str(staging_profile.jenkins.url).rstrip("/") == "https://jenkins.staging.com"

        default_profile = config.get_profile()
        assert str(default_profile.jenkins.url).rstrip("/") == "https://jenkins.prod.com"

    def test_get_profile_not_found(self, temp_config_dir):
        """Test getting non-existent profile."""
        config_data = {
            "version": "1.0",
            "default_profile": "production",
            "profiles": {
                "production": {
                    "jenkins": {
                        "url": "https://jenkins.prod.com",
                        "api_version": "2.0",
                    },
                },
            },
        }

        config_file = temp_config_dir / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(config_dir=temp_config_dir)
        config = manager.load()

        with pytest.raises(ValueError):
            config.get_profile("nonexistent")

    def test_set_value(self, temp_config_dir):
        """Test setting a configuration value."""
        config_data = {
            "version": "1.0",
            "default_profile": "production",
            "profiles": {
                "production": {
                    "jenkins": {
                        "url": "https://jenkins.old.com",
                        "api_version": "2.0",
                    },
                },
            },
        }

        config_file = temp_config_dir / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(config_dir=temp_config_dir)
        manager.load()

        manager.set_value("profiles.production.jenkins.url", "https://jenkins.new.com")

        config = manager.get()
        assert (
            str(config.profiles["production"].jenkins.url).rstrip("/") == "https://jenkins.new.com"
        )

    def test_set_value_coerces_string_to_int(self, temp_config_dir):
        """set_value('defaults.timeout', '60') should store the int 60."""
        manager = ConfigManager(config_dir=temp_config_dir)
        manager.ensure_config_dir()

        from jctl.config.schemas import JenkinsConfig, ProfileConfig

        manager.save(
            Config(
                default_profile="p",
                profiles={
                    "p": ProfileConfig(jenkins=JenkinsConfig(url="https://j.example.com")),
                },
            )
        )

        manager.set_value("defaults.timeout", "60")
        assert manager.get_value("defaults.timeout") == 60

    def test_set_value_rejects_bad_type(self, temp_config_dir):
        """set_value with non-coercible string must raise, not corrupt the file."""
        manager = ConfigManager(config_dir=temp_config_dir)
        manager.ensure_config_dir()

        from jctl.config.schemas import JenkinsConfig, ProfileConfig

        manager.save(
            Config(
                default_profile="p",
                profiles={
                    "p": ProfileConfig(jenkins=JenkinsConfig(url="https://j.example.com")),
                },
            )
        )

        with pytest.raises(ValidationError):
            manager.set_value("defaults.timeout", "notanumber")

        # Reloading must still produce a valid config — file was not corrupted.
        fresh = ConfigManager(config_dir=temp_config_dir)
        loaded = fresh.load()
        assert loaded.defaults.timeout == 30

    def test_set_value_rejects_unknown_root_key(self, temp_config_dir):
        """set_value must refuse unknown top-level fields (no silent extras)."""
        manager = ConfigManager(config_dir=temp_config_dir)
        manager.ensure_config_dir()

        from jctl.config.schemas import JenkinsConfig, ProfileConfig

        manager.save(
            Config(
                default_profile="p",
                profiles={
                    "p": ProfileConfig(jenkins=JenkinsConfig(url="https://j.example.com")),
                },
            )
        )

        with pytest.raises(KeyError):
            manager.set_value("bogus", "value")

    def test_set_value_coerces_string_to_bool(self, temp_config_dir):
        """set_value('p.jenkins.verify_ssl', 'false') should store False (bool)."""
        manager = ConfigManager(config_dir=temp_config_dir)
        manager.ensure_config_dir()

        from jctl.config.schemas import JenkinsConfig, ProfileConfig

        manager.save(
            Config(
                default_profile="p",
                profiles={
                    "p": ProfileConfig(jenkins=JenkinsConfig(url="https://j.example.com")),
                },
            )
        )

        manager.set_value("p.jenkins.verify_ssl", "false")
        v = manager.get_value("p.jenkins.verify_ssl")
        assert v is False
        assert isinstance(v, bool)
