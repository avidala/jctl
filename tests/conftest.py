"""Pytest configuration and shared fixtures."""

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture
def temp_config_dir() -> Generator[Path, None, None]:
    """Create a temporary config directory for tests.

    Yields:
        Path to temporary config directory
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir)
        yield config_dir


@pytest.fixture
def mock_jenkins_url() -> str:
    """Mock Jenkins server URL.

    Returns:
        Mock Jenkins URL
    """
    return "https://jenkins.example.com"


@pytest.fixture
def mock_okta_config() -> dict[str, str]:
    """Mock Okta configuration.

    Returns:
        Mock Okta config dictionary
    """
    return {
        "domain": "example.okta.com",
        "client_id": "test-client-id",
        "redirect_uri": "http://localhost:8989/callback",
    }


@pytest.fixture
def sample_tokens() -> dict[str, str]:
    """Sample authentication tokens for testing.

    Returns:
        Sample token dictionary
    """
    return {
        "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.test_access_token",
        "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.test_refresh_token",
        "id_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.test_id_token",
        "expires_at": 1234567890,
        "token_type": "Bearer",
    }


@pytest.fixture
def sample_jenkins_job_info() -> dict:
    """Sample Jenkins job info for testing.

    Returns:
        Sample job info dictionary
    """
    return {
        "name": "test-job",
        "url": "https://jenkins.example.com/job/test-job/",
        "buildable": True,
        "builds": [
            {"number": 1, "url": "https://jenkins.example.com/job/test-job/1/"},
            {"number": 2, "url": "https://jenkins.example.com/job/test-job/2/"},
        ],
        "lastBuild": {"number": 2, "url": "https://jenkins.example.com/job/test-job/2/"},
        "property": [
            {
                "_class": "hudson.model.ParametersDefinitionProperty",
                "parameterDefinitions": [
                    {
                        "name": "environment",
                        "type": "StringParameterDefinition",
                        "defaultParameterValue": {"value": "dev"},
                    },
                    {
                        "name": "account_id",
                        "type": "StringParameterDefinition",
                        "defaultParameterValue": None,
                    },
                ],
            }
        ],
    }


@pytest.fixture
def sample_build_info() -> dict:
    """Sample Jenkins build info for testing.

    Returns:
        Sample build info dictionary
    """
    return {
        "number": 42,
        "building": False,
        "result": "SUCCESS",
        "duration": 120000,
        "timestamp": 1234567890000,
        "url": "https://jenkins.example.com/job/test-job/42/",
        "actions": [
            {
                "_class": "hudson.model.ParametersAction",
                "parameters": [
                    {"name": "environment", "value": "staging"},
                    {"name": "account_id", "value": "123456"},
                ],
            }
        ],
    }
