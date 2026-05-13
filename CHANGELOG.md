# Changelog

<div align="center">
<img src="assets/logo.svg" alt="jctl" width="300"/>
</div>

All notable changes to jctl (Jenkins Control CLI) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

*Part of the AVIDALA DevOps Tools suite*

## [Unreleased]

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
