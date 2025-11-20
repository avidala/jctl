# Testing Guide for jctl

## Test Infrastructure

The jctl project uses pytest for testing with the following setup:

- **Test Framework**: pytest
- **Async Support**: pytest-asyncio
- **Coverage Reporting**: pytest-cov
- **Mocking**: pytest-mock, unittest.mock
- **HTTP Mocking**: responses

## Running Tests

### Install Test Dependencies

```bash
pip install -r requirements-dev.txt
```

### Run All Tests

```bash
# Run all tests with coverage
pytest tests/ --cov=jctl --cov-report=html --cov-report=term-missing

# Run only unit tests
pytest tests/unit/

# Run specific test file
pytest tests/unit/test_auth_api_token.py

# Run with verbose output
pytest -v

# Run with debug output
pytest -vv -s
```

### Coverage Reports

Coverage reports are generated in two formats:

1. **Terminal Output**: Shows coverage summary and missing lines
2. **HTML Report**: Detailed coverage report in `htmlcov/index.html`

```bash
# Generate and view HTML coverage report
pytest --cov=jctl --cov-report=html
open htmlcov/index.html  # macOS
```

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_auth_api_token.py
│   ├── test_auth_keystore.py
│   ├── test_auth_okta.py
│   ├── test_config_manager.py
│   └── test_jenkins_client.py
└── integration/             # Integration tests (slower, may require external services)
    └── __init__.py
```

## Current Test Coverage

As of last run:

- **`jctl/auth/api_token.py`**: 100% ✅
- **`jctl/auth/keystore.py`**: 82% 🟡
- **Overall project**: ~6% (initial setup, more tests needed)

## Test Fixtures

Common fixtures are defined in `tests/conftest.py`:

- `temp_config_dir`: Temporary directory for config files
- `mock_jenkins_url`: Mock Jenkins server URL
- `mock_okta_config`: Mock Okta configuration
- `sample_tokens`: Sample authentication tokens
- `sample_jenkins_job_info`: Sample Jenkins job data
- `sample_build_info`: Sample build information

## Writing New Tests

### Unit Test Template

```python
"""Tests for module_name."""

import pytest
from unittest.mock import MagicMock, patch

from jctl.module.name import ClassName


class TestClassName:
    """Tests for ClassName."""

    def test_initialization(self):
        """Test object initialization."""
        obj = ClassName()
        assert obj is not None

    @patch("jctl.module.name.dependency")
    def test_with_mock(self, mock_dep):
        """Test with mocked dependency."""
        mock_dep.return_value = "mocked_value"
        obj = ClassName()
        result = obj.method()
        assert result == "expected_value"

    @pytest.mark.asyncio
    async def test_async_method(self):
        """Test async method."""
        obj = ClassName()
        result = await obj.async_method()
        assert result is not None
```

### Integration Test Template

```python
"""Integration tests for feature."""

import pytest

pytestmark = pytest.mark.integration


class TestFeatureIntegration:
    """Integration tests for feature."""

    @pytest.mark.asyncio
    async def test_end_to_end_flow(self):
        """Test complete workflow."""
        # Setup
        # Execute
        # Verify
        pass
```

## Known Issues

### Tests That Need Fixes

The following test files have failures due to mismatches with the actual implementation:

1. **`test_auth_okta.py`**: Methods don't match actual OktaAuthenticator API
2. **`test_config_manager.py`**: Schema validation requires Okta config in all profiles
3. **`test_jenkins_client.py`**: Mock setup needs adjustment for actual client behavior

These tests provide a good starting point but need to be updated to match the current implementation.

## CI/CD Integration

### GitHub Actions Workflow Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run tests
        run: pytest tests/ --cov=jctl --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Test Best Practices

1. **Isolation**: Each test should be independent and not rely on other tests
2. **Mocking**: Mock external dependencies (file system, network, keystore)
3. **Clear Names**: Test names should describe what they test
4. **Arrange-Act-Assert**: Structure tests with setup, execution, and verification
5. **Fast Tests**: Unit tests should run in milliseconds
6. **Coverage**: Aim for >80% coverage on critical paths

## Debugging Tests

### Run Specific Test

```bash
pytest tests/unit/test_auth_api_token.py::TestAPITokenAuthenticator::test_store_token -v
```

### Drop into Debugger on Failure

```bash
pytest --pdb
```

### Show Print Statements

```bash
pytest -s
```

### Show Full Tracebacks

```bash
pytest --tb=long
```

## Next Steps

To improve test coverage:

1. Fix failing tests in `test_auth_okta.py`, `test_config_manager.py`, and `test_jenkins_client.py`
2. Add tests for command modules (`jctl/commands/`)
3. Add tests for utility modules (`jctl/utils/`)
4. Add integration tests for end-to-end workflows
5. Set up CI/CD to run tests automatically
6. Add coverage requirements (e.g., fail if coverage drops below 70%)

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
