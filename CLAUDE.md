# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**jctl** (Jenkins Control CLI) is a Python command-line tool for managing Jenkins pipelines with dual authentication support (Okta OAuth 2.0 and API tokens).

**Key Technologies:**
- Click 8.1.7+ (CLI framework)
- httpx 0.25.2+ (async HTTP client)
- Authlib 1.3.0+ (OAuth 2.0)
- keyring 24.3.0+ (OS keystore integration)
- Pydantic 2.5.0+ (config validation)
- Rich 13.7.0+ (terminal UI)

## Common Commands

### Development Setup
```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=jctl --cov-report=html

# Run specific test file
pytest tests/unit/test_auth_api_token.py

# Run tests matching pattern
pytest -k "auth"
```

### Code Quality
```bash
# Format code (line length: 100)
black jctl/ tests/

# Lint code
ruff check jctl/ tests/ --fix

# Type check
mypy jctl/

# Security scan
bandit -r jctl/ -ll

# Run all pre-commit hooks manually
pre-commit run --all-files
```

### Running Locally
```bash
# Run jctl commands during development
jctl --debug pipeline list
jctl --version

# The package is installed in editable mode via pip install -e
```

## Architecture Overview

### Layer Structure

1. **CLI Layer** (`jctl/commands/`) - Click command groups for user interaction
2. **Business Logic Layer** - Core functionality:
   - `jctl/auth/` - Authentication (Okta OAuth, API tokens)
   - `jctl/jenkins/` - Jenkins API integration
   - `jctl/config/` - Configuration management
   - `jctl/utils/` - Utilities (output, logging, completion)
3. **Storage Layer** - OS keystore (primary) with encrypted fallback
4. **External Services** - Jenkins REST API, Okta OAuth API

### Key Architectural Patterns

**Dual Authentication Strategy:**
- **API Tokens**: Simple username/token auth for automation (CI/CD, scripts)
- **OAuth 2.0**: Okta SSO with PKCE for interactive use
- Factory pattern in `utils/jenkins_client_factory.py` tries API token first, falls back to OAuth

**Credential Storage Hierarchy:**
1. OS-native keystore (macOS Keychain, Linux Secret Service, Windows Credential Manager)
2. Encrypted fallback using Fernet symmetric encryption with machine-derived keys
3. Files stored in `~/.jctl/` with 0600 permissions

**Jenkins Client (`jenkins/client.py`):**
- Async HTTP client with httpx
- Automatic retry with exponential backoff (via tenacity)
- Retries on network errors, 429, 503, 504
- Does NOT retry on 400, 401, 403, 404
- CSRF token handling (crumb)
- Support for folder paths in job names

### Module Organization

```
jctl/
├── __init__.py              # Package version
├── __main__.py              # Entry point (calls cli.py)
├── cli.py                   # Main CLI definition, Click groups
├── constants.py             # Global constants
├── auth/                    # Authentication modules
│   ├── okta.py             # OAuth 2.0 with PKCE implementation
│   ├── api_token.py        # Simple API token auth
│   ├── token_manager.py    # OAuth token lifecycle management
│   └── keystore.py         # Secure credential storage
├── jenkins/                 # Jenkins integration
│   ├── client.py           # Jenkins REST API client
│   └── mock.py             # Mock client for testing
├── config/                  # Configuration management
│   ├── manager.py          # Config file handling
│   └── schemas.py          # Pydantic models for validation
├── utils/                   # Utilities
│   ├── completion.py       # Shell completion (5-min cache)
│   ├── jenkins_client_factory.py  # Client creation logic
│   ├── logging.py          # Rich logging setup
│   ├── output.py           # Output formatting (table/json/yaml/plain)
│   ├── password_prompt.py  # Secure password input
│   └── validators.py       # Input validation
└── commands/                # CLI command implementations
    ├── auth.py             # Authentication commands
    ├── config.py           # Configuration commands
    ├── job.py              # Job commands (trigger, logs)
    └── pipeline.py         # Pipeline commands (list, run, describe, logs, cancel)
```

## Important Implementation Details

### Authentication Flow

**Okta OAuth (PKCE flow):**
1. Generate PKCE code_verifier and code_challenge
2. Build authorization URL and open browser
3. User authenticates with Okta
4. Receive callback with authorization code
5. Exchange code for access_token and refresh_token
6. Store tokens in OS keystore
7. Use access_token for Jenkins API calls (Authorization: Bearer)
8. Auto-refresh when expired

**API Token:**
- Username + Jenkins API token
- Stored in OS keystore (service: "jctl", username: "{profile}_jenkins_username")
- No expiration, no refresh needed

### Configuration

Stored in `~/.jctl/config.yaml`:
```yaml
version: "1.0"
default_profile: production
profiles:
  production:
    jenkins:
      url: https://jenkins.example.com
      verify_ssl: true
    okta:
      domain: company.okta.com
      client_id: jenkins-cli
      redirect_uri: http://localhost:8989/callback
defaults:
  timeout: 30
  retry_count: 3
  log_level: INFO
```

### Shell Completion

- Job list cached for 5 minutes (`utils/completion.py`)
- Cache TTL: 300 seconds
- Silent failure (doesn't break completion)
- Supports bash, zsh, fish

### Error Handling

- Custom exceptions for different error types
- Retry logic with exponential backoff (tenacity)
- Clear error messages via Rich console
- Debug mode shows full tracebacks

## Testing Strategy

### Test Organization
```
tests/
├── unit/                   # Fast, isolated unit tests
│   ├── test_auth_*.py
│   ├── test_commands_*.py
│   └── test_jenkins_*.py
├── integration/           # Integration tests with dependencies
└── conftest.py           # Shared pytest fixtures
```

### Coverage Goals
- Unit tests: 80%+ coverage
- Test edge cases and error conditions
- Security-critical paths (authentication) need thorough testing

### Running Tests
- Use pytest with `-v` for verbose output
- Use `--cov=jctl` for coverage reports
- Use `-k "pattern"` to run specific test groups
- Async tests use `@pytest.mark.asyncio` decorator

## Common Development Tasks

### Adding a New Command

1. Create command file in `jctl/commands/my_command.py`
2. Define Click command group using `@click.group()` decorator
3. Implement subcommands with proper options and arguments
4. Register in `jctl/cli.py`: `cli.add_command(my_command.my_command)`
5. Add tests in `tests/unit/test_my_command.py`
6. Update README.md command reference
7. Add entry to CHANGELOG.md under [Unreleased]

### Adding a New Jenkins API Operation

1. Add method to `JenkinsClient` class in `jctl/jenkins/client.py`
2. Use async/await pattern with httpx
3. Add retry decorator for transient failures
4. Handle CSRF tokens if needed (use `_get_crumb()`)
5. Add unit tests with mocked responses
6. Call from command in `jctl/commands/`

### Modifying Authentication

- Authentication methods in `jctl/auth/`
- Credential storage via `SecureKeystore` in `jctl/auth/keystore.py`
- Client factory logic in `jctl/utils/jenkins_client_factory.py`
- Always maintain backward compatibility with stored credentials

## Security Considerations

- Never log sensitive data (tokens, passwords)
- All Jenkins API calls use HTTPS
- Credentials stored in OS keystore when available
- Fallback encryption uses Fernet with machine-derived keys
- Config files have 0600 permissions
- No password storage (OAuth or API tokens only)
- Input validation on all user-provided data

## Code Style

- **Formatting**: Black with line length 100
- **Linting**: Ruff (pycodestyle, pyflakes, isort, bugbear, comprehensions)
- **Type Hints**: Required on all functions (enforced by mypy)
- **Docstrings**: Use for public APIs and complex logic
- **Imports**: Sorted by isort (standard lib, third-party, local)
- **Error Messages**: Use Rich console for colored, formatted output

## Configuration Files

- `pyproject.toml` - Project metadata, dependencies, tool configs
- `.pre-commit-config.yaml` - Pre-commit hooks (black, ruff, bandit)
- `pytest.ini_options` - In pyproject.toml under [tool.pytest.ini_options]
- `mypy` config - In pyproject.toml under [tool.mypy]

## Environment Variables

- `JCTL_PROFILE` - Active profile name
- `JCTL_JENKINS_URL` - Override Jenkins URL
- `JCTL_OKTA_DOMAIN` - Override Okta domain
- `JCTL_OUTPUT_FORMAT` - Output format (table/json/yaml/plain)
- `JCTL_LOG_LEVEL` - Log level (DEBUG/INFO/WARNING/ERROR)
- `JCTL_NO_COLOR` - Disable colored output

## Working with Multiple Profiles

- Profiles stored in `~/.jctl/config.yaml` under `profiles` key
- Each profile can have different Jenkins URL and auth settings
- Use `--profile dev` flag to select specific profile
- Default profile set via `default_profile` in config
- Credentials stored per-profile in keystore with prefix `{profile}_`

## Design Philosophy

- **User-Friendly**: Clear error messages, helpful --help text
- **Secure by Default**: OS keystore, HTTPS only, no password storage
- **Fast**: Async operations, caching, optimized for common workflows
- **Reliable**: Retry logic, proper error handling, robust API integration
- **Extensible**: Modular design for easy feature additions
- **Well-Tested**: High coverage, unit + integration tests
