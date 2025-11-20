# Contributing to jctl

Thank you for your interest in contributing to jctl! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Release Process](#release-process)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of experience level, gender identity, sexual orientation, disability, personal appearance, body size, race, ethnicity, age, religion, or nationality.

### Expected Behavior

- Be respectful and considerate in your communication
- Welcome newcomers and help them get started
- Focus on what is best for the community
- Show empathy towards other community members
- Accept constructive criticism gracefully

### Unacceptable Behavior

- Harassment, discriminatory jokes, or offensive comments
- Personal or political attacks
- Publishing others' private information without permission
- Other conduct that could reasonably be considered inappropriate

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- Access to a Jenkins instance for testing (optional but recommended)
- Basic understanding of Jenkins, OAuth 2.0, and CLI tools

### Finding Issues to Work On

1. Check the [GitHub Issues](https://github.com/h2oai/public-cloud-infrastructure/issues) page
2. Look for issues labeled:
   - `good first issue` - Great for newcomers
   - `help wanted` - We need community assistance
   - `bug` - Bug fixes needed
   - `enhancement` - New features or improvements
3. Comment on the issue to express interest before starting work

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR-USERNAME/public-cloud-infrastructure.git
cd avidala/jctl
```

### 2. Set Up Development Environment

```bash
# Create a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### 3. Verify Installation

```bash
# Run tests to ensure everything is working
pytest

# Try the CLI
jctl --help
```

### 4. Set Up Testing Configuration (Optional)

If you have access to a Jenkins instance for testing:

```bash
# Initialize configuration
jctl config init

# Configure authentication (use a test instance!)
jctl auth token  # or jctl auth login for OAuth
```

## How to Contribute

### Reporting Bugs

Before creating a bug report:
1. Check existing issues to avoid duplicates
2. Verify the bug exists in the latest version
3. Collect relevant information (version, OS, Python version, error messages)

Create a bug report including:
- Clear, descriptive title
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details
- Error messages and logs (use `--debug` flag)

### Suggesting Enhancements

Enhancement suggestions should include:
- Clear use case and motivation
- Proposed solution or implementation ideas
- Any potential drawbacks or alternatives considered
- Examples of how the feature would be used

### Code Contributions

#### Step 1: Create a Branch

```bash
# Ensure you're on the latest develop branch
git checkout develop
git pull origin develop

# Create a feature branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

**Branch naming conventions:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions or fixes

#### Step 2: Make Your Changes

- Write clean, readable code
- Follow the [Coding Standards](#coding-standards)
- Add tests for new functionality
- Update documentation as needed
- Keep commits focused and atomic

#### Step 3: Test Your Changes

```bash
# Run the full test suite
pytest

# Run with coverage
pytest --cov=jctl --cov-report=term-missing

# Run linters
black jctl/ tests/
ruff check jctl/ tests/ --fix

# Run security checks
bandit -r jctl/
safety check
```

#### Step 4: Commit Your Changes

```bash
# Stage your changes
git add .

# Commit with a descriptive message
git commit -m "feat: add pipeline search functionality

- Implement fuzzy search for pipeline names
- Add --query parameter to pipeline list command
- Include tests for search functionality
- Update documentation"
```

**Commit message format:**
```
<type>: <short summary>

<detailed description>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions or modifications
- `refactor`: Code refactoring
- `chore`: Maintenance tasks
- `security`: Security improvements

#### Step 5: Push and Create Pull Request

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create a pull request on GitHub
```

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with some modifications:

- **Line Length**: 100 characters (enforced by Black)
- **String Quotes**: Prefer double quotes for user-facing strings
- **Imports**: Organized by `black` and `ruff`
- **Type Hints**: Required for all function signatures
- **Docstrings**: Required for all public functions, classes, and modules

### Code Formatting

```bash
# Format code with Black
black jctl/ tests/

# Check and fix linting issues
ruff check jctl/ tests/ --fix
```

### Type Checking

```bash
# Run mypy for type checking
mypy jctl/
```

### Code Organization

**File Structure:**
- Keep files focused and single-purpose
- Group related functionality into modules
- Use clear, descriptive names

**Function Design:**
- Functions should do one thing well
- Keep functions short (< 50 lines when possible)
- Use descriptive parameter names
- Return early to reduce nesting

**Class Design:**
- Follow single responsibility principle
- Use composition over inheritance
- Keep classes focused and cohesive

### Error Handling

```python
# Good: Specific exception handling with logging
try:
    result = api_call()
except httpx.HTTPStatusError as e:
    logger.error(f"API call failed: {e.response.status_code}")
    raise JenkinsAPIError(f"Failed to fetch data: {e}") from e

# Bad: Bare except that swallows errors
try:
    result = api_call()
except:
    pass
```

### Logging

```python
from jctl.utils.logging import get_logger

logger = get_logger(__name__)

# Use appropriate log levels
logger.debug("Detailed diagnostic information")
logger.info("General informational messages")
logger.warning("Warning messages for unexpected situations")
logger.error("Error messages for failures")
```

### Security

- Never hardcode credentials or secrets
- Use environment variables or secure storage for sensitive data
- Validate all user input
- Use parameterized queries (if applicable)
- Follow principle of least privilege

## Testing

### Test Structure

```
tests/
├── unit/              # Unit tests (isolated, fast)
│   ├── test_auth_*.py
│   ├── test_jenkins_*.py
│   └── test_commands_*.py
├── integration/       # Integration tests (with dependencies)
│   └── test_flows.py
└── conftest.py       # Shared fixtures
```

### Writing Tests

```python
import pytest
from jctl.auth.api_token import APITokenAuthenticator

def test_api_token_storage(temp_config_dir):
    """Test that API tokens are stored correctly."""
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
```

### Test Guidelines

- **Test Coverage**: Aim for 80%+ coverage on new code
- **Test Names**: Descriptive names explaining what is tested
- **AAA Pattern**: Arrange, Act, Assert
- **Fixtures**: Use pytest fixtures for common setup
- **Mocking**: Mock external dependencies (Jenkins API, Okta, etc.)
- **Async Tests**: Use `pytest-asyncio` for async code

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_auth_api_token.py

# Run tests matching pattern
pytest -k "test_api_token"

# Run with coverage
pytest --cov=jctl --cov-report=html

# Run in verbose mode
pytest -v

# Run with debug output
pytest -s
```

## Documentation

### Code Documentation

```python
def trigger_job(self, name: str, parameters: dict[str, Any] | None = None) -> int:
    """Trigger a Jenkins job with parameters.

    Args:
        name: Job name (can include folder path like "folder/job-name")
        parameters: Job parameters as key-value pairs

    Returns:
        Queue item ID for the triggered job

    Raises:
        JenkinsAPIError: If the job trigger fails

    Example:
        >>> client.trigger_job("my-job", {"param1": "value1"})
        12345
    """
```

### User Documentation

- **README.md**: Overview, quick start, examples
- **Command Help**: Use Click's `help` parameter
- **Guides**: Step-by-step instructions for common tasks
- **CHANGELOG.md**: Document all changes

### Documentation Updates

When making changes:
- Update relevant documentation
- Add examples for new features
- Update CHANGELOG.md
- Keep documentation in sync with code

## Pull Request Process

### Before Submitting

- [ ] All tests pass (`pytest`)
- [ ] Code is formatted (`black`, `ruff`)
- [ ] Type checking passes (`mypy`)
- [ ] Security checks pass (`bandit`, `safety`)
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated
- [ ] Commit messages follow conventions

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests pass locally
- [ ] CHANGELOG.md updated
```

### Review Process

1. **Automated Checks**: CI/CD runs tests, linting, security scans
2. **Code Review**: At least one maintainer reviews the PR
3. **Feedback**: Address review comments
4. **Approval**: PR approved by maintainer
5. **Merge**: Maintainer merges to develop branch

### Review Criteria

Reviewers check for:
- Code quality and readability
- Test coverage and quality
- Documentation completeness
- Security considerations
- Performance implications
- Breaking changes

## Release Process

### Versioning

We follow [Semantic Versioning](https://semver.org/):
- **MAJOR** (1.0.0): Breaking changes
- **MINOR** (0.1.0): New features, backwards compatible
- **PATCH** (0.1.1): Bug fixes, backwards compatible

### Release Workflow

1. **Feature Freeze**: No new features, only bug fixes
2. **Testing**: Comprehensive testing on all platforms
3. **Documentation**: Update all docs, finalize CHANGELOG
4. **Version Bump**: Update version in `pyproject.toml`
5. **Tag Release**: Create git tag (e.g., `v0.1.0`)
6. **Build**: Create distribution packages
7. **Publish**: Release to GitHub, PyPI (if applicable)
8. **Announce**: Notify team and users

## Communication

### Channels

- **GitHub Issues**: Bug reports, feature requests
- **Pull Requests**: Code contributions, discussions
- **Slack**: #h2o-managed-cloud (https://h2oai.slack.com/archives/C03F53QQEBX)
- **Email**: managed-cloud@h2o.ai

### Getting Help

- Check existing documentation
- Search closed issues for similar problems
- Ask in Slack #h2o-managed-cloud
- Mention `@managed-cloud` team for urgent issues

## Recognition

Contributors are recognized in:
- Git commit history
- GitHub contributors page
- Release notes (for significant contributions)
- Project README (for major features)

## License

By contributing to jctl, you agree that your contributions will be licensed under the MIT License.

## Questions?

If you have questions about contributing:
- Open a GitHub Discussion
- Ask in Slack #h2o-managed-cloud
- Email the team at managed-cloud@h2o.ai

---

**Thank you for contributing to jctl!** 🎉

Your contributions help make Jenkins automation better for everyone.
