# Changelog

<div align="center">
<img src="assets/logo.svg" alt="jctl" width="300"/>
</div>

All notable changes to jctl (Jenkins Control CLI) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

*Part of the AVIDALA DevOps Tools suite*

## [0.2.2](https://github.com/avidala/jctl/compare/v0.2.1...v0.2.2) (2026-05-13)


### Bug Fixes

* **ci:** keep END marker's indent when splicing resources block ([#31](https://github.com/avidala/jctl/issues/31)) ([f5ca7e6](https://github.com/avidala/jctl/commit/f5ca7e6a9ba721119e2e494f387e1229a4e2e72a))
* **ci:** make resources block replacement idempotent ([#29](https://github.com/avidala/jctl/issues/29)) ([7bef420](https://github.com/avidala/jctl/commit/7bef42064321e34faee869b78d0481873ef981f8))

## [0.2.1](https://github.com/avidala/jctl/compare/v0.2.0...v0.2.1) (2026-05-13)


### Bug Fixes

* **ci:** dedent poet output before re-indenting, to fix 4-space indent bug ([#26](https://github.com/avidala/jctl/issues/26)) ([f269a97](https://github.com/avidala/jctl/commit/f269a9782ace63a0900d6ceeda0a4bed7609cbb8))
* **ci:** install jctl from GitHub release sdist instead of PyPI ([#22](https://github.com/avidala/jctl/issues/22)) ([97ac7a8](https://github.com/avidala/jctl/commit/97ac7a865ea3e706a3fdf679b40effef61e80fbd))
* **ci:** install setuptools so poet can import pkg_resources ([#24](https://github.com/avidala/jctl/issues/24)) ([6bcb612](https://github.com/avidala/jctl/commit/6bcb61229fc51ee5eb202a4a2128b15fb9108df6))
* **ci:** normalize bump resource names + idempotent PR creation ([#28](https://github.com/avidala/jctl/issues/28)) ([c16bd3f](https://github.com/avidala/jctl/commit/c16bd3f5d2ce9198581d56e4e94b936d5643bdb3))
* **ci:** pin setuptools&lt;81 so poet can import pkg_resources ([#25](https://github.com/avidala/jctl/issues/25)) ([a07af5f](https://github.com/avidala/jctl/commit/a07af5f190ec0df6e0b166cb278b083728cfa148))
* **ci:** use plain --force in bump workflow's push ([#27](https://github.com/avidala/jctl/issues/27)) ([4fbd30d](https://github.com/avidala/jctl/commit/4fbd30d078a1cfda52a66376aa4aedae369ccac3))

## [0.2.0](https://github.com/avidala/jctl/compare/v0.1.0...v0.2.0) (2026-05-13)


### Features

* add comprehensive GitHub repository configuration ([7f264d5](https://github.com/avidala/jctl/commit/7f264d590de4183a303d3a2add60c08ca6c1df94))


### Bug Fixes

* handle no-change case in production release workflow ([b0afdcb](https://github.com/avidala/jctl/commit/b0afdcbb7d931d2b180b85194baf395bde839d57))


### Documentation

* add branch protection and repository setup guides ([538e229](https://github.com/avidala/jctl/commit/538e229c9a799bd6b5f9794e7812bf71db34ee84))


### Code Refactoring

* reorganize documentation for better clarity ([dadeba2](https://github.com/avidala/jctl/commit/dadeba28a246d02bbfb278c9f602207b92f68449))

## [Unreleased]

### Removed (Breaking)

- Okta OAuth / SSO authentication has been removed. The `jctl auth login` and `jctl auth refresh` commands, the `OktaConfig` profile section, the `JCTL_OKTA_*` environment variables, the `--okta-domain` / `--okta-client-id` flags on `jctl config add-profile`, and the `authlib` dependency are all gone. Jenkins API token (`jctl auth token`) is now the only supported authentication method. Existing OAuth tokens in the OS keystore are no longer read. Existing configs containing an `okta:` block still load (Pydantic config is `extra = "allow"`), but the field is ignored.

### Added

- `LICENSE` file at the repo root (MIT). `pyproject.toml` already declared `license = "MIT"` and the README had the badge — only the file itself was missing, which blocked Homebrew/PyPI license validation.
- `Python 3.13` added to the CI test matrix. Coverage now matches the Homebrew formula which installs onto `python@3.13`.
- Advisory `typecheck` job in `.github/workflows/lint.yml` that runs `mypy jctl/` with `continue-on-error: true`. Type drift is now visible in CI without blocking PRs; flip the flag once the codebase is fully typed.

### Changed

- `README.md`: removed internal `hamc-*` Jenkins job names from the usage examples — replaced with generic `deploy-staging`, `provision-environment`, etc., so the docs don't leak project-internal pipeline naming.
- `CLAUDE.md`: corrected the claim that the project has 80%+ unit test coverage. Actual coverage is ~14% (auth + config + jenkins client). Roadmap target unchanged; reality now documented.
- `SECURITY.md`: replaced a broken placeholder Slack line with a working private-disclosure path. Preferred channel is now a private GitHub Security Advisory; email is the backup.
- `softprops/action-gh-release` pinned to a commit SHA (`da05d55…` / v2.2.2) across the three release workflows, per supply-chain hardening guidance for third-party actions.
- `bump-homebrew-formula.yml` now uses `actions/checkout@v6`, matching every other workflow in the repo.

### Removed

- `requirements.txt` and `requirements-dev.txt`. They had drifted from `pyproject.toml` (e.g. `httpx>=0.25.2,<0.28` in requirements vs. `<0.29` in pyproject, with the Homebrew formula actually shipping `0.28.1`). `pyproject.toml` is the single source of truth; `pip install -e ".[dev]"` is the supported install path. `docs/DEVELOPMENT.md` and `docs/development/TESTING.md` updated to match.
- `scripts/install.sh` and `scripts/jctl-wrapper.sh`. These were the pre-Homebrew install path (shell alias pointing at a venv); now superseded by `brew install` and `pipx install` and referenced by no docs.

### Docs

- Fix install instructions: `pip install jctl` was pointing users at an unrelated Jamf Pro CRUD package owned by another author on PyPI. README now recommends Homebrew or `pipx install` from the git tag, and `ROADMAP.md` flags that a future PyPI release must use a non-colliding name (e.g. `avidala-jctl`).

### Tooling

- Pin lint tool versions in CI (`black==24.10.0`, `ruff==0.9.2`, `bandit==1.9.1`) to match `.pre-commit-config.yaml` so upstream releases cannot break the build.
- Drop deprecated `safety check` from the Lint workflow (the legacy command was retired upstream).
- Gitignore `.claude/worktrees/` so local Claude Code worktrees do not leak into commits.

## [0.1.0-beta.1] - 2025-01-20

### 🎉 Initial Beta Release

First beta release of jctl - Jenkins Control CLI with Okta SSO authentication.

### ✨ Features

#### Authentication
- **Okta SSO Login** - OAuth 2.0 with PKCE flow for secure authentication
- **API Token Support** - Alternative authentication using Jenkins API tokens
- **Secure Credential Storage** - OS-native keystore integration (macOS Keychain, Linux SecretService, Windows Credential Manager) with encrypted fallback
- **Token Management** - Automatic token refresh and status checking
- **Multiple Auth Commands**:
  - `jctl auth login` - Login with Okta SSO
  - `jctl auth logout` - Logout and clear credentials
  - `jctl auth status` - Show authentication status
  - `jctl auth token` - Login with Jenkins API token
  - `jctl auth refresh` - Force token refresh

#### Job Management
- **Job Triggering** - Trigger Jenkins jobs with parameters
- **Build Monitoring** - Wait for job completion with real-time status
- **Log Streaming** - Stream or fetch job logs
- **Job Commands**:
  - `jctl job trigger <job-name>` - Trigger job with parameters
  - `jctl job logs <job-name> [build-number]` - View or stream job logs

#### Pipeline Management
- **Pipeline Listing** - List all available pipelines with filtering
- **Pipeline Execution** - Run pipelines with parameters
- **Pipeline Monitoring** - Track pipeline execution with stage details
- **Build Control** - Cancel/abort running pipelines
- **Pipeline Commands**:
  - `jctl pipeline list` - List available pipelines
  - `jctl pipeline run <pipeline-name>` - Execute pipeline
  - `jctl pipeline describe <pipeline-name> <build-number>` - Show detailed pipeline status
  - `jctl pipeline logs <pipeline-name> [build-number]` - View or stream logs
  - `jctl pipeline cancel <pipeline-name> <build-number>` - Cancel running pipeline

#### Configuration Management
- **Profile Support** - Multiple configuration profiles (production, staging, etc.)
- **Interactive Setup** - Guided configuration initialization
- **Config Commands**:
  - `jctl config init` - Initialize configuration
  - `jctl config set <key> <value>` - Set configuration value
  - `jctl config get <key>` - Get configuration value
  - `jctl config list` - List all configuration values
  - `jctl config show` - Show full configuration file
  - `jctl config add-profile` - Add new profile

#### Developer Experience
- **Shell Completion** - Tab completion for commands, options, and job/pipeline names
- **Rich Terminal Output** - Colored output with tables and progress indicators
- **Multiple Output Formats** - Table, JSON, YAML, and plain text
- **Debug Mode** - Verbose logging with `--debug` flag
- **Profile Selection** - Switch between profiles with `--profile` flag

### 🔧 Technical Improvements

#### Week 1 - Critical Fixes
- **Fixed Hard-coded Path** in completion script (scripts/jctl-completion.zsh:206)
- **Fixed Keystore Encryption Bug** - Now uses deterministic key derivation (jctl/auth/keystore.py:55-66)
- **Added Test Suite** - 54 tests with 50%+ coverage on core modules
- **Fixed Exception Handling** - Added logging to 8 silent exception handlers

#### Week 2 - High Priority Fixes
- **Removed Unimplemented Commands** - Deleted 10 stub commands for clean beta release
- **Deduplicated Code** - Removed 150 lines of duplicate `get_jenkins_client()` code
- **Fixed HTTP Timeouts** - Separate connect (10s) and read (30s) timeouts
- **Fixed Async Sleep Calls** - Replaced 4 blocking `time.sleep()` with `await asyncio.sleep()`
- **Added Dependency Version Constraints** - Upper bounds on all 10 dependencies
- **Fixed Job Name Validator** - Now supports folder paths like `managed-cloud/job-name`

#### Week 3 - Medium Priority Improvements
- **Proper Logging** - Initialized at CLI entry point with DEBUG/INFO levels
- **Distinct Exit Codes** - 6 exit codes for better error handling in scripts:
  - `0` - Success
  - `1` - General error
  - `2` - Configuration error
  - `3` - Authentication error
  - `4` - Jenkins API error
  - `130` - User cancelled
- **Retry Logic** - Automatic retry with exponential backoff for:
  - Network errors
  - HTTP 429 (Rate Limited)
  - HTTP 503 (Service Unavailable)
  - HTTP 504 (Gateway Timeout)
- **Completion Performance** - 5-minute cache for job list (40-500x faster)
- **Python Version Declaration** - Updated to require Python ≥3.10 (was ≥3.9)

#### Code Quality & Security
- **Code Formatting** - 100% Black compliant (10 files reformatted)
- **Linting** - Ruff auto-fixed 61/74 issues
- **Security Scanning** - Bandit found 0 real security vulnerabilities
- **Dependency Security** - All dependencies verified secure with Safety
- **Test Coverage** - 100% on API token auth, 82% on keystore

### 📦 Dependencies

```
click>=8.1.7,<9.0
rich>=13.7.0,<14.0
httpx>=0.25.2,<0.28
authlib>=1.3.0,<2.0
keyring>=24.3.0,<26.0
pydantic>=2.5.0,<3.0
python-jenkins>=1.8.1,<2.0
pyyaml>=6.0.1,<7.0
cryptography>=41.0.7,<43.0
python-dotenv>=1.0.0,<2.0
tenacity>=8.2.0,<9.0
```

### 🔒 Security

- Secure credential storage using OS-native keystore
- Fallback to Fernet encryption with machine-derived keys
- OAuth 2.0 with PKCE flow for authentication
- No hardcoded credentials or secrets
- All API calls use secure HTTPS
- Proper SSL certificate verification (configurable)

### 📚 Documentation

- Complete README with installation and usage instructions
- Quick Start guide for common workflows
- Shell completion setup guide
- Implementation status tracking
- Architecture documentation
- Development setup guide

### 🐛 Bug Fixes

- Fixed encryption key generation in keystore (deterministic instead of random)
- Fixed hard-coded absolute path in completion script
- Fixed async sleep calls blocking event loop
- Fixed job name validator to support Jenkins folder paths
- Fixed HTTP timeout configuration (separate connect/read)
- Fixed exception handling (added logging to silent handlers)

### 🗑️ Removed

#### Unimplemented Command Stubs (Will be added in v0.2.0)
- `jctl job status` - Get job status
- `jctl job stop` - Stop running job
- `jctl job history` - Show job history
- `jctl job params` - List job parameters
- `jctl pipeline search` - Search pipelines
- `jctl pipeline pause` - Pause pipeline
- `jctl pipeline resume` - Resume paused pipeline
- `jctl pipeline replay` - Replay pipeline run
- `jctl pipeline restart` - Restart pipeline
- `jctl pipeline validate` - Validate pipeline config

**Rationale**: Removed to provide clean user experience without "Not yet implemented" errors.

### 📊 Statistics

- **Total Commands**: 18 working commands (100% functional rate)
- **Lines of Code**: ~3,218 lines (production + tests)
- **Code Removed**: 306 lines (duplicates + stubs)
- **Test Coverage**: 50%+ on core modules
- **Files Modified**: 11 files across 3 weeks of development

### 🎯 Roadmap for v0.2.0

Planned features for next release:

**High Priority**:
- `jctl job stop` - Stop running builds
- `jctl job status` - Quick status check
- Enhanced pipeline cancel with pause/resume

**Medium Priority**:
- `jctl job history` - Build history
- `jctl pipeline replay` - Replay with same parameters
- `jctl pipeline validate` - Pre-flight configuration checks

**Low Priority**:
- `jctl job params` - Parameter discovery
- `jctl pipeline search` - Fuzzy search for pipelines
- `jctl pipeline restart` - Restart from failure point

### ⚠️ Breaking Changes

None - this is the initial beta release.

### 🔄 Migration Notes

Not applicable - initial release.

### 🙏 Acknowledgments

Built by the Avner Vidal for DevOps workflows.

---

## Version History

### Beta Releases
- **0.1.0-beta.1** (2025-01-20) - Initial beta release

### Development Milestones
- **Week 1** (2025-01-20) - Critical fixes completed
- **Week 2** (2025-01-20) - High priority improvements completed
- **Week 3** (2025-01-20) - Medium priority enhancements completed
- **Code Quality** (2025-01-20) - Security and linting checks passed

---

## Links

- **Homepage**: https://github.com/avidala/jctl
- **Issues**: https://github.com/avidala/jctl/issues
- **Documentation**: https://github.com/avidala/jctl/tree/main/cli/jenkins

---

## Feedback

For bug reports, feature requests, or questions:
- Open an issue on GitHub
- Email: avnervidal27@gmail.com

---

**Note**: This is a beta release. While all implemented features are tested and functional, the API may change in future versions. Please report any issues you encounter.
