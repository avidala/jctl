"""Configuration schemas using Pydantic."""

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

# validate_assignment=True rejects bad values at `config set` time instead of
# silently writing them and breaking the next config load.
_MODEL_CONFIG = ConfigDict(validate_assignment=True, extra="allow")


class JenkinsConfig(BaseModel):
    """Jenkins server configuration."""

    model_config = _MODEL_CONFIG

    url: HttpUrl = Field(..., description="Jenkins server URL")
    api_version: str = Field(default="2.0", description="Jenkins API version")
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")
    timeout: int = Field(default=30, description="Request timeout in seconds")


class OutputConfig(BaseModel):
    """Output formatting configuration."""

    model_config = _MODEL_CONFIG

    format: str = Field(default="table", description="Default output format")
    color: str = Field(default="auto", description="Color output (auto/always/never)")
    pager: bool = Field(default=False, description="Use pager for long output")


class SSLConfig(BaseModel):
    """SSL/TLS configuration."""

    model_config = _MODEL_CONFIG

    verify: bool = Field(default=True, description="Verify SSL certificates")
    cert_path: str | None = Field(default=None, description="Path to custom CA bundle")


class ProfileConfig(BaseModel):
    """Configuration profile."""

    model_config = _MODEL_CONFIG

    jenkins: JenkinsConfig
    output: OutputConfig = Field(default_factory=OutputConfig)
    ssl: SSLConfig = Field(default_factory=SSLConfig)


class DefaultsConfig(BaseModel):
    """Default settings."""

    model_config = _MODEL_CONFIG

    timeout: int = Field(default=30, description="Default timeout in seconds")
    retry_count: int = Field(default=3, description="Number of retries for failed requests")
    log_level: str = Field(default="INFO", description="Logging level")
    cache_ttl: int = Field(default=300, description="Cache TTL in seconds")


class Config(BaseModel):
    """Main configuration."""

    model_config = _MODEL_CONFIG

    version: str = Field(default="1.0", description="Config file version")
    default_profile: str = Field(default="production", description="Default profile to use")
    profiles: dict[str, ProfileConfig] = Field(
        default_factory=dict, description="Configuration profiles"
    )
    defaults: DefaultsConfig = Field(default_factory=DefaultsConfig)
    aliases: dict[str, str] = Field(default_factory=dict, description="Command aliases")

    def get_profile(self, name: str | None = None) -> ProfileConfig:
        """Get profile by name, or default profile."""
        profile_name = name or self.default_profile
        if profile_name not in self.profiles:
            raise ValueError(f"Profile '{profile_name}' not found")
        return self.profiles[profile_name]
