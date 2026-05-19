# Development Guide

Complete guide for setting up a development environment and contributing to jctl.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Initial Setup](#initial-setup)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Code Quality](#code-quality)
- [Debugging](#debugging)
- [Common Tasks](#common-tasks)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

- **Python 3.10+** - [Download](https://www.python.org/downloads/)
- **Git** - [Download](https://git-scm.com/downloads)
- **pip** - Included with Python

### Recommended Tools

- **pyenv** - Python version management ([Install](https://github.com/pyenv/pyenv#installation))
- **direnv** - Environment management ([Install](https://direnv.net/docs/installation.html))
- **VS Code** or **PyCharm** - IDEs with Python support

### Optional (for testing)

- **Jenkins instance** - For integration testing

## Initial Setup

### 1. Clone the Repository

```bash
# Clone the main repository
git clone https://github.com/avidala/jctl.git
cd public-cloud-infrastructure/cli/jenkins

# Or clone your fork
git clone https://github.com/YOUR-USERNAME/public-cloud-infrastructure.git
cd public-cloud-infrastructure/cli/jenkins
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate  # On Windows

# Verify Python version
python --version  # Should be 3.10+
```

### 3. Install Development Dependencies

```bash
# Install jctl in editable mode with dev dependencies
pip install -e ".[dev]"

# Verify installation
jctl --version
jctl --help
```

### 4. Install Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Set up hooks
pre-commit install

# Test hooks (optional)
pre-commit run --all-files
```

### 5. Configure Development Environment

```bash
# Copy example configuration (if available)
cp config.example.yaml ~/.jctl/config.yaml

# Or initialize fresh config
jctl config init
```

## Development Workflow

### Daily Workflow

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Pull latest changes
git checkout develop
git pull origin develop

# 3. Create feature branch
git checkout -b feature/your-feature-name

# 4. Make changes...
# Edit code, add features, fix bugs

# 5. Run tests
pytest

# 6. Check code quality
black jctl/ tests/
ruff check jctl/ tests/ --fix

# 7. Commit changes
git add .
git commit -m "feat: add awesome feature"

# 8. Push and create PR
git push origin feature/your-feature-name
```

### Branch Strategy

- **develop** - Main development branch
- **main** - Production releases
- **feature/*** - New features
- **fix/*** - Bug fixes
- **docs/*** - Documentation updates

### Making Changes

#### Step 1: Pick an Issue

```bash
# Find an issue on GitHub
# Comment to claim it
# Understand requirements before starting
```

#### Step 2: Create Branch

```bash
# Always branch from develop
git checkout develop
git pull origin develop
git checkout -b feature/descriptive-name
```

#### Step 3: Implement

```python
# Example: Adding a new command

# 1. Create command file
# jctl/commands/new_command.py

import click
from rich.console import Console

console = Console()

@click.group()
def new_command() -> None:
    """Description of new command."""
    pass

@new_command.command()
@click.argument("arg_name")
@click.option("--option", help="Option description")
def subcommand(arg_name: str, option: str | None) -> None:
    """Subcommand description."""
    console.print(f"Running with {arg_name}")

# 2. Register in jctl/cli.py
from jctl.commands import new_command
cli.add_command(new_command.new_command)

# 3. Add tests
# tests/unit/test_new_command.py

def test_new_command():
    """Test new command functionality."""
    # Test implementation
    pass
```

#### Step 4: Test

```bash
# Run unit tests
pytest tests/unit/test_new_command.py

# Run all tests
pytest

# Check coverage
pytest --cov=jctl --cov-report=html
open htmlcov/index.html
```

#### Step 5: Document

```markdown
# Update relevant documentation
- README.md - Add to command reference
- CHANGELOG.md - Add to [Unreleased] section
- Command help text - Ensure --help is clear
```

#### Step 6: Commit

```bash
# Stage changes
git add .

# Commit with conventional commit message
git commit -m "feat: add new command for X

- Implement core functionality
- Add comprehensive tests
- Update documentation
"
```

## Testing

### Test Structure

```
tests/
├── unit/                 # Fast, isolated tests
│   ├── test_auth_*.py   # Authentication tests
│   ├── test_commands_*.py
│   └── test_jenkins_*.py
├── integration/         # Slower, with dependencies
│   └── test_flows.py
└── conftest.py         # Shared fixtures
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_auth_api_token.py

# Run specific test function
pytest tests/unit/test_auth_api_token.py::test_store_token

# Run tests matching pattern
pytest -k "auth"

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=jctl --cov-report=term-missing

# Run with coverage HTML report
pytest --cov=jctl --cov-report=html
open htmlcov/index.html
```

### Writing Tests

```python
# Example unit test
import pytest
from jctl.auth.api_token import APITokenAuthenticator

def test_api_token_storage(temp_config_dir):
    """Test API token storage and retrieval."""
    # Arrange
    auth = APITokenAuthenticator()
    username = "testuser"
    token = "test-token-123"

    # Act
    auth.store_token(username, token)
    retrieved_username, retrieved_token = auth.get_credentials()

    # Assert
    assert retrieved_username == username
    assert retrieved_token == token

# Example async test
import pytest
from jctl.jenkins.client import JenkinsClient

@pytest.mark.asyncio
async def test_jenkins_client_get_jobs():
    """Test Jenkins client job listing."""
    # Arrange
    client = JenkinsClient(url="https://jenkins.test.com")

    # Act
    jobs = await client.get_jobs()

    # Assert
    assert isinstance(jobs, list)
```

### Test Fixtures

```python
# In conftest.py
import pytest
from pathlib import Path

@pytest.fixture
def temp_config_dir(tmp_path):
    """Create temporary config directory."""
    config_dir = tmp_path / ".jctl"
    config_dir.mkdir()
    return config_dir

@pytest.fixture
def mock_jenkins_client(mocker):
    """Mock Jenkins client."""
    client = mocker.Mock()
    client.get_jobs.return_value = []
    return client
```

### Test Coverage Goals

- **Unit Tests**: long-term target is 80%+ — current line coverage is
  ~37% overall (run `pytest --cov=jctl` to reproduce). Strongest areas
  are `config/schemas.py` (100%), `auth/keystore.py` (~83%), and
  `utils/completion.py` (~66%); the weakest is `commands/*` (17-28%).
- **Integration Tests**: Key workflows
- **Edge Cases**: Error conditions
- **Security**: Authentication flows

## Code Quality

### Formatting

```bash
# Format with Black (line length: 100)
black jctl/ tests/

# Check formatting
black jctl/ tests/ --check

# Format single file
black jctl/commands/job.py
```

### Linting

```bash
# Run ruff linter
ruff check jctl/ tests/

# Auto-fix issues
ruff check jctl/ tests/ --fix

# Check specific file
ruff check jctl/commands/job.py
```

### Type Checking

```bash
# Run mypy
mypy jctl/

# Check specific file
mypy jctl/commands/job.py

# Generate type coverage report
mypy jctl/ --html-report mypy-report
```

### Security Scanning

```bash
# Run bandit security scanner
bandit -r jctl/ -ll

# Check for dependency vulnerabilities
safety check

# Full security audit
bandit -r jctl/ && safety check
```

### Pre-commit Hooks

Pre-commit hooks run automatically on `git commit`:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.10.0
    hooks:
      - id: black
        args: [--line-length=100]

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.9.2
    hooks:
      - id: ruff
        args: [--fix]

  - repo: https://github.com/PyCQA/bandit
    rev: 1.9.1
    hooks:
      - id: bandit
        args: [-ll, -r, jctl/]
```

Run manually:
```bash
# Run all hooks
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files
```

## Debugging

### Debug Mode

```bash
# Run with debug logging
jctl --debug pipeline list

# View detailed error traces
jctl --debug job trigger my-job --param foo=bar
```

### Python Debugger

```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use Python 3.7+ built-in
breakpoint()

# Run command to hit breakpoint
jctl pipeline list
```

### VS Code Debugging

```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug jctl",
      "type": "python",
      "request": "launch",
      "module": "jctl",
      "args": ["--debug", "pipeline", "list"],
      "console": "integratedTerminal"
    }
  ]
}
```

### Logging

```python
from jctl.utils.logging import get_logger

logger = get_logger(__name__)

# Add debug logging
logger.debug("Detailed diagnostic information")
logger.info("General informational message")
logger.warning("Warning about unexpected situation")
logger.error("Error message for failure")
```

### Common Debugging Scenarios

#### Authentication Issues

```bash
# Check authentication status
jctl --debug auth status

# Clear and re-authenticate
jctl auth logout
jctl --debug auth token

# Check stored credentials
python -c "from jctl.auth.keystore import SecureKeystore; k = SecureKeystore(); print(k.retrieve('jenkins_token'))"
```

#### API Connection Issues

```bash
# Test Jenkins connectivity
jctl --debug pipeline list

# Check configuration
jctl config show

# Verify Jenkins URL
curl -I https://jenkins.your-domain.com
```

#### Import Errors

```python
# Check if module installed correctly
python -c "import jctl; print(jctl.__version__)"

# Reinstall in dev mode
pip install -e ".[dev]" --force-reinstall
```

## Common Tasks

### Adding a New Command

```bash
# 1. Create command file
touch jctl/commands/my_command.py

# 2. Implement command
# (See example in Development Workflow section)

# 3. Register in cli.py
# Add import and register command

# 4. Add tests
touch tests/unit/test_my_command.py

# 5. Update documentation
# - README.md
# - CHANGELOG.md
```

### Adding a New Dependency

```bash
# 1. Add to pyproject.toml
# Under [project] dependencies

# 2. Add a version constraint
# Example: "new-package>=1.0.0,<2.0"

# 3. Re-install the project so the new dep is picked up
pip install -e ".[dev]"
```

`pyproject.toml` is the single source of truth — there are no standalone
`requirements.txt` / `requirements-dev.txt` files.

### Running Local Changes

```bash
# After making changes, run locally
jctl --version  # Should show editable install

# Test your changes
jctl your-new-command

# Debug if needed
jctl --debug your-new-command
```

### Updating Documentation

```bash
# Update user documentation
vim README.md
vim docs/GUIDE.md

# Update API documentation
# Add docstrings to functions

# Update changelog
vim CHANGELOG.md
# Add entry under [Unreleased]

# Preview markdown
# Use VS Code, PyCharm, or grip
grip README.md
```

### Creating a Release

```bash
# 1. Update version in pyproject.toml
vim pyproject.toml
# Change version = "0.1.0" to "0.2.0"

# 2. Update CHANGELOG.md
vim CHANGELOG.md
# Move [Unreleased] to [0.2.0] with date

# 3. Commit version bump
git add pyproject.toml CHANGELOG.md
git commit -m "chore: bump version to 0.2.0"

# 4. Create tag
git tag -a v0.2.0 -m "Release v0.2.0"

# 5. Push tag
git push origin v0.2.0

# 6. Create GitHub release
# Use GitHub UI or gh CLI
```

## Troubleshooting

### Common Issues

#### Import Error After Installing

```bash
# Problem: Can't import jctl module
# Solution: Reinstall in editable mode
pip uninstall jctl
pip install -e ".[dev]"
```

#### Pre-commit Hook Failures

```bash
# Problem: Pre-commit hooks failing
# Solution: Run hooks manually and fix
pre-commit run --all-files
black jctl/ tests/
ruff check jctl/ tests/ --fix
git add .
git commit -m "fix: address pre-commit issues"
```

#### Test Failures

```bash
# Problem: Tests failing locally
# Solution: Check environment
pytest -v  # Verbose output
pytest --tb=short  # Short traceback
pytest --lf  # Run last failed
pytest --sw  # Stop on first failure
```

#### Virtual Environment Issues

```bash
# Problem: Wrong Python version
# Solution: Recreate virtual environment
deactivate
rm -rf venv
python3.10 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

#### Permission Errors

```bash
# Problem: Can't write to config directory
# Solution: Fix permissions
chmod 755 ~/.jctl
chmod 600 ~/.jctl/config.yaml
```

### Getting Help

1. **Check Documentation**: README, guides, docstrings
2. **Search Issues**: GitHub issues for similar problems
3. **Ask Team**: Slack avnervidal27@gmail.com
4. **Create Issue**: If bug or unclear documentation

## Development Tips

### Productivity

- **Use IDE**: VS Code or PyCharm with Python support
- **Enable Autosave**: Reduces forgotten changes
- **Use Debugger**: More efficient than print statements
- **Write Tests First**: TDD approach
- **Small Commits**: Easier to review and revert

### Best Practices

- **Read Code First**: Understand existing patterns
- **Follow Style Guide**: Consistency matters
- **Write Docstrings**: Future you will thank you
- **Test Edge Cases**: Not just happy path
- **Review Your Own PR**: Catch issues before review

### Resources

- **Python Docs**: https://docs.python.org/3/
- **Click Docs**: https://click.palletsprojects.com/
- **pytest Docs**: https://docs.pytest.org/
- **Jenkins API**: https://www.jenkins.io/doc/book/using/remote-access-api/

---

**Document Version**: 1.0
**Last Updated**: 2025-01-20
**Maintained By**: Avner Vidal
