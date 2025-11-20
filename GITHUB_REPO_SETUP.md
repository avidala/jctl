# GitHub Repository Setup Guide

Complete guide for setting up the jctl CLI in its own GitHub repository with CI/CD pipelines.

---

## 📁 Repository Structure

```
jctl/
├── .github/
│   ├── workflows/
│   │   ├── test.yml              # Run tests on PR/push
│   │   ├── lint.yml              # Code quality checks
│   │   ├── security.yml          # Security scanning
│   │   └── release.yml           # Build and publish releases
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   ├── feature_request.md
│   │   └── config.yml
│   ├── pull_request_template.md
│   └── CODEOWNERS
├── jctl/                         # Source code
├── tests/                        # Test suite
├── docs/                         # Documentation
├── scripts/                      # Utility scripts
├── .gitignore
├── .pre-commit-config.yaml      # Pre-commit hooks
├── pyproject.toml               # Project metadata
├── requirements.txt             # Runtime dependencies
├── requirements-dev.txt         # Development dependencies
├── README.md
├── CHANGELOG.md
├── LICENSE
├── CONTRIBUTING.md
└── SECURITY.md
```

---

## 🔧 Repository Settings

### Branch Protection Rules

**Branch**: `main`

- [x] Require a pull request before merging
  - [x] Require approvals: 1
  - [x] Dismiss stale pull request approvals when new commits are pushed
  - [x] Require review from Code Owners
- [x] Require status checks to pass before merging
  - [x] Require branches to be up to date before merging
  - Required checks:
    - `test (3.10)`
    - `test (3.11)`
    - `test (3.12)`
    - `lint`
    - `security`
- [x] Require conversation resolution before merging
- [x] Require signed commits (optional but recommended)
- [ ] Require linear history
- [x] Do not allow bypassing the above settings (except for admins)

**Branch**: `develop` (optional)

- Same settings as `main` but with:
  - Require approvals: 1 (can be same person)
  - Auto-merge allowed

---

## 🤖 GitHub Actions Workflows

### 1. Test Workflow (`.github/workflows/test.yml`)

```yaml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Run tests with coverage
        run: |
          pytest --cov=jctl --cov-report=xml --cov-report=term

      - name: Upload coverage to Codecov
        if: matrix.os == 'ubuntu-latest' && matrix.python-version == '3.11'
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: unittests
          name: codecov-umbrella

      - name: Test installation
        run: |
          pip install -e .
          jctl --version
          jctl --help
```

### 2. Lint Workflow (`.github/workflows/lint.yml`)

```yaml
name: Lint

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  lint:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Run Black (formatter)
        run: |
          black --check --diff jctl tests

      - name: Run Ruff (linter)
        run: |
          ruff check jctl tests

      - name: Run mypy (type checker)
        run: |
          mypy jctl --ignore-missing-imports

      - name: Check for print statements
        run: |
          ! grep -r "print(" jctl/ --include="*.py" || (echo "Found print() statements. Use logger instead." && exit 1)
```

### 3. Security Workflow (`.github/workflows/security.yml`)

```yaml
name: Security

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  schedule:
    # Run daily at 2 AM UTC
    - cron: '0 2 * * *'

jobs:
  security:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install bandit safety

      - name: Run Bandit (security linter)
        run: |
          bandit -r jctl/ -f json -o bandit-report.json || true
          bandit -r jctl/ -ll

      - name: Upload Bandit report
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: bandit-report
          path: bandit-report.json

      - name: Check dependencies with Safety
        run: |
          safety check --json || true
          safety check

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v2
        if: always()
        with:
          sarif_file: 'trivy-results.sarif'
```

### 4. Release Workflow (`.github/workflows/release.yml`)

```yaml
name: Release

on:
  release:
    types: [published]
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to release (e.g., 0.1.0-alpha.1)'
        required: true
        type: string

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install build tools
        run: |
          python -m pip install --upgrade pip
          pip install build twine

      - name: Build package
        run: |
          python -m build

      - name: Check package
        run: |
          twine check dist/*

      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: dist-packages
          path: dist/

  publish-pypi:
    needs: build
    runs-on: ubuntu-latest
    if: github.event_name == 'release'
    environment:
      name: pypi
      url: https://pypi.org/p/jctl
    permissions:
      id-token: write  # For trusted publishing

    steps:
      - name: Download artifacts
        uses: actions/download-artifact@v3
        with:
          name: dist-packages
          path: dist/

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1

  publish-github:
    needs: build
    runs-on: ubuntu-latest
    if: github.event_name == 'release'
    permissions:
      contents: write

    steps:
      - name: Download artifacts
        uses: actions/download-artifact@v3
        with:
          name: dist-packages
          path: dist/

      - name: Upload to GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          files: dist/*
```

---

## 📋 Issue Templates

### Bug Report (`.github/ISSUE_TEMPLATE/bug_report.md`)

```markdown
---
name: Bug Report
about: Report a bug or unexpected behavior
title: '[BUG] '
labels: bug
assignees: ''
---

## Description
A clear and concise description of the bug.

## To Reproduce
Steps to reproduce the behavior:
1. Run command: `jctl ...`
2. See error

## Expected Behavior
What you expected to happen.

## Actual Behavior
What actually happened.

## Environment
- OS: [e.g., macOS 14.1, Ubuntu 22.04, Windows 11]
- Python Version: [e.g., 3.11.5]
- jctl Version: [e.g., 0.1.0]
- Installation Method: [pip, git clone, etc.]

## Additional Context
- Error messages/logs
- Screenshots
- Configuration (sanitized)

## Debug Output
```bash
jctl --debug <command>
# Paste debug output here
```
```

### Feature Request (`.github/ISSUE_TEMPLATE/feature_request.md`)

```markdown
---
name: Feature Request
about: Suggest a new feature or enhancement
title: '[FEATURE] '
labels: enhancement
assignees: ''
---

## Feature Description
A clear and concise description of the feature.

## Use Case
Describe the problem this feature would solve.

## Proposed Solution
How you envision this feature working.

## Alternatives Considered
Other approaches you've thought about.

## Additional Context
Screenshots, examples, references to similar features in other tools.
```

### Pull Request Template (`.github/pull_request_template.md`)

```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Refactoring (no functional changes)
- [ ] Performance improvement
- [ ] Test coverage improvement

## Related Issues
Fixes #(issue number)

## Changes Made
- Change 1
- Change 2
- Change 3

## Testing
- [ ] Tests added/updated
- [ ] All tests pass locally
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines (black, ruff)
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests provide sufficient coverage
- [ ] Dependent changes merged
- [ ] CHANGELOG.md updated (if applicable)

## Screenshots (if applicable)
```

---

## 👥 Code Owners (`.github/CODEOWNERS`)

```
# Global owners
* @yourusername

# Core authentication
/jctl/auth/ @yourusername

# Jenkins client
/jctl/jenkins/ @yourusername

# Documentation
/docs/ @yourusername
*.md @yourusername

# CI/CD
/.github/ @yourusername

# Security-sensitive
/jctl/auth/keystore.py @yourusername
/jctl/auth/okta.py @yourusername
```

---

## 🔒 Security Policy (`SECURITY.md`)

```markdown
# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to: security@yourcompany.com

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

You should receive a response within 48 hours. We'll keep you updated on the progress.

## Security Best Practices

When using jctl:
1. Always use the latest version
2. Never commit `~/.jctl/config.yaml` to version control
3. Use `--profile` flag instead of default profile in shared scripts
4. Rotate Jenkins API tokens regularly
5. Use OAuth when possible instead of API tokens
6. Review permissions granted to OAuth applications

## Known Security Considerations

- Credentials stored in OS keychain (Keychain/SecretService/Credential Manager)
- Config file permissions set to 0600 (user read/write only)
- OAuth uses PKCE flow for added security
- HTTPS enforced for all API communication
```

---

## 📝 Contributing Guide (`CONTRIBUTING.md`)

```markdown
# Contributing to jctl

Thank you for your interest in contributing!

## Development Setup

1. Fork and clone the repository
```bash
git clone https://github.com/yourusername/jctl.git
cd jctl
```

2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install in development mode
```bash
pip install -e ".[dev]"
```

4. Install pre-commit hooks
```bash
pre-commit install
```

## Development Workflow

1. Create a feature branch
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes

3. Run tests
```bash
pytest
```

4. Run linters
```bash
black jctl tests
ruff check jctl tests
mypy jctl
```

5. Commit changes
```bash
git commit -m "feat: add new feature"
```

6. Push and create PR
```bash
git push origin feature/your-feature-name
```

## Commit Message Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test changes
- `refactor:` Code refactoring
- `perf:` Performance improvements
- `chore:` Maintenance tasks

## Code Style

- Use `black` for formatting
- Follow PEP 8
- Use type hints
- Write docstrings for public APIs
- Keep functions focused and small

## Testing

- Write tests for new features
- Maintain >80% code coverage
- Test on multiple Python versions (3.10, 3.11, 3.12)
- Test on multiple platforms (Mac, Linux, Windows)

## Pull Request Process

1. Update README/docs if needed
2. Add tests for new functionality
3. Ensure all tests pass
4. Update CHANGELOG.md
5. Request review from maintainers
6. Address review feedback
7. Squash commits if requested

## Questions?

Open an issue or discussion on GitHub.
```

---

## 🔖 Version Management Strategy

### Version Scheme

```
MAJOR.MINOR.PATCH[-PRERELEASE]

Examples:
0.1.0-alpha.1    # First alpha
0.1.0-alpha.2    # Second alpha
0.1.0-beta.1     # First beta
0.1.0-rc.1       # Release candidate
0.1.0            # GA release
0.1.1            # Patch release
0.2.0            # Minor release
1.0.0            # Major release
```

### Release Process

#### Alpha Releases
- Purpose: Early testing, incomplete features
- Frequency: Weekly during development
- Quality Bar: Core features work, may have bugs
- Command: `jctl 0.1.0-alpha.X`

#### Beta Releases
- Purpose: Feature complete, bug fixing
- Frequency: Bi-weekly
- Quality Bar: All features implemented, most bugs fixed
- Command: `jctl 0.1.0-beta.X`

#### Release Candidates
- Purpose: Final testing before GA
- Frequency: As needed
- Quality Bar: Production ready, final polish
- Command: `jctl 0.1.0-rc.X`

#### GA (General Availability)
- Purpose: Stable production release
- Frequency: After successful RC
- Quality Bar: Fully tested, documented, stable
- Command: `jctl 0.1.0`

### Creating a Release

```bash
# 1. Update version in pyproject.toml
version = "0.1.0-alpha.1"

# 2. Update CHANGELOG.md
## [0.1.0-alpha.1] - 2025-01-20
### Added
- Initial authentication system
- Basic pipeline commands

# 3. Commit changes
git commit -am "chore: prepare release 0.1.0-alpha.1"
git push origin develop

# 4. Create and push tag
git tag -a v0.1.0-alpha.1 -m "Release 0.1.0-alpha.1"
git push origin v0.1.0-alpha.1

# 5. Create GitHub Release
# Use GitHub UI or gh CLI:
gh release create v0.1.0-alpha.1 \
  --title "v0.1.0-alpha.1" \
  --notes "First alpha release with authentication and basic commands" \
  --prerelease
```

---

## 📊 Badges for README

Add these badges to the top of README.md:

```markdown
# jctl - Jenkins Control CLI

[![Tests](https://github.com/yourusername/jctl/workflows/Tests/badge.svg)](https://github.com/yourusername/jctl/actions/workflows/test.yml)
[![Lint](https://github.com/yourusername/jctl/workflows/Lint/badge.svg)](https://github.com/yourusername/jctl/actions/workflows/lint.yml)
[![Security](https://github.com/yourusername/jctl/workflows/Security/badge.svg)](https://github.com/yourusername/jctl/actions/workflows/security.yml)
[![codecov](https://codecov.io/gh/yourusername/jctl/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/jctl)
[![Python Version](https://img.shields.io/pypi/pyversions/jctl)](https://pypi.org/project/jctl/)
[![PyPI version](https://badge.fury.io/py/jctl.svg)](https://badge.fury.io/py/jctl)
[![License](https://img.shields.io/github/license/yourusername/jctl)](LICENSE)
```

---

## 🚀 Initial Repository Setup Commands

```bash
# 1. Create new repository on GitHub
# (Use GitHub web UI or gh CLI)

# 2. Clone the new empty repo
git clone https://github.com/yourusername/jctl.git
cd jctl

# 3. Copy all files from old location
cp -r /Users/avnervidal/Documents/worktree-2/public-cloud-infrastructure/cli/jenkins/* .

# 4. Create new branch structure
git checkout -b develop

# 5. Add all files
git add .

# 6. Initial commit
git commit -m "chore: initial commit"

# 7. Push to GitHub
git push -u origin develop
git push -u origin main

# 8. Set up branch protection (use GitHub UI)

# 9. Create first alpha release
git tag -a v0.1.0-alpha.1 -m "First alpha release"
git push origin v0.1.0-alpha.1
gh release create v0.1.0-alpha.1 --prerelease

# 10. Set up secrets for CI/CD
# Go to Settings > Secrets and variables > Actions
# Add: PYPI_API_TOKEN (for publishing)
```

---

## 📝 Post-Setup Checklist

After repository setup:

- [ ] Branch protection rules configured
- [ ] All workflows passing
- [ ] Code owners file active
- [ ] Issue templates working
- [ ] PR template working
- [ ] Pre-commit hooks tested
- [ ] First alpha release created
- [ ] Badges added to README
- [ ] Documentation updated
- [ ] CHANGELOG.md initialized
- [ ] Contributors invited
- [ ] Dependabot configured

---

Good luck with your new repository! 🎉
