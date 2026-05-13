"""Input validation utilities."""

import re
from typing import Any


def validate_job_name(name: str) -> bool:
    """Validate Jenkins job name.

    Args:
        name: Job name to validate

    Returns:
        True if valid
    """
    # Jenkins job names can contain alphanumeric, dash, underscore, and forward slash (for folders)
    # Examples: "my-job", "folder/my-job", "deploy/release-pipeline"
    pattern = r"^[a-zA-Z0-9_/-]+$"
    return bool(re.match(pattern, name))


def validate_build_number(number: Any) -> bool:
    """Validate build number.

    Args:
        number: Build number to validate

    Returns:
        True if valid
    """
    try:
        num = int(number)
        return num > 0
    except (ValueError, TypeError):
        return False


def validate_parameter_format(param: str) -> tuple[str, str] | None:
    """Validate and parse parameter in key=value format.

    Args:
        param: Parameter string

    Returns:
        Tuple of (key, value) if valid, None otherwise
    """
    if "=" not in param:
        return None

    parts = param.split("=", 1)
    if len(parts) != 2:
        return None

    key, value = parts
    if not key.strip():
        return None

    return (key.strip(), value.strip())


def validate_url(url: str) -> bool:
    """Validate URL format.

    Args:
        url: URL to validate

    Returns:
        True if valid
    """
    pattern = r"^https?://[a-zA-Z0-9.-]+(:[0-9]+)?(/.*)?$"
    return bool(re.match(pattern, url))


def validate_okta_domain(domain: str) -> bool:
    """Validate Okta domain format.

    Args:
        domain: Okta domain to validate (e.g., company.okta.com)

    Returns:
        True if valid
    """
    pattern = r"^[a-zA-Z0-9.-]+\.okta(preview)?\.com$"
    return bool(re.match(pattern, domain))


def validate_aws_account_id(account_id: str) -> bool:
    """Validate AWS account ID format.

    Args:
        account_id: AWS account ID to validate

    Returns:
        True if valid
    """
    # AWS account IDs are 12-digit numbers
    pattern = r"^\d{12}$"
    return bool(re.match(pattern, account_id))


def validate_environment_name(name: str) -> bool:
    """Validate environment name format.

    Args:
        name: Environment name to validate

    Returns:
        True if valid
    """
    # Environment names: alphanumeric, dash, underscore, no spaces
    pattern = r"^[a-zA-Z0-9_-]+$"
    return bool(re.match(pattern, name))


class ValidationError(Exception):
    """Validation error."""

    pass
