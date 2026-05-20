<div align="center">

<!-- Project Logo -->
<img src="assets/logo.svg" alt="jctl logo" width="500"/>

# jctl - Jenkins Control CLI

[![Tests](https://github.com/avidala/jctl/workflows/Tests/badge.svg?branch=main)](https://github.com/avidala/jctl/actions/workflows/test.yml)
[![Lint](https://github.com/avidala/jctl/workflows/Lint/badge.svg?branch=main)](https://github.com/avidala/jctl/actions/workflows/lint.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**A flexible command-line interface tool for managing Jenkins pipelines using Jenkins API tokens.**

*Part of the AVIDALA DevOps Tools suite*

</div>

## Features

- 🔐 **API Token Authentication** - Username + Jenkins API token, stored in your OS keychain
- 🚀 **Pipeline Management** - List, run, describe, cancel pipelines with real-time monitoring
- 📊 **Real-time Monitoring** - Stream logs and track job status
- 🎨 **Beautiful Output** - Rich terminal UI with tables and colors
- 🔧 **DevOps Optimized** - Built for everyday platform engineering pipelines
- 🔒 **Secure Token Storage** - OS-native keychain integration
- ⌨️ **Shell Completion** - Tab completion for commands, subcommands, and options
- 🎯 **Multiple Profiles** - Manage dev, staging, and production environments separately

## Quick Start

### Installation

#### Option 1: Homebrew (macOS/Linux - Recommended)

```bash
# Tap the repository and install
brew install avidala/jctl/jctl

# Verify installation
jctl --version
```

#### Option 2: pipx (All platforms)

```bash
# install the latest tagged release in an isolated env
pipx install "git+https://github.com/avidala/jctl.git@v0.1.0"
```

> **Note:** the name `jctl` on PyPI belongs to an unrelated Jamf project,
> so this tool is **not** distributed via `pip install jctl`. Install via
> Homebrew (above), `pipx` from this git URL, or from source.

#### Option 3: From source

```bash
git clone https://github.com/avidala/jctl.git
cd jctl
pip install -e ".[dev]"
```

### Shell Completion (Optional but Recommended)

Enable tab completion for faster command entry:

```bash
# Preview what `--install` will append to your rc file (no changes made)
jctl completion --install --dry-run

# Install with a confirmation prompt
jctl completion --install

# Install non-interactively (for setup scripts / dotfile bootstrap)
jctl completion --install --yes

# Then reload your shell
source ~/.zshrc  # for zsh
source ~/.bashrc # for bash
```

`jctl completion --install` shows you the exact lines it would append and asks for confirmation before modifying your rc file. The snippet uses Click's built-in completion mechanism (`eval "$(_JCTL_COMPLETE=…_source jctl)"`), so it works regardless of how jctl is installed (Homebrew, pipx, editable). A second `--install` on an rc file that already contains the snippet is a no-op.

After installation, you can use Tab to auto-complete:
- Command names: `jctl pipe<Tab>` → `jctl pipeline`
- Subcommands: `jctl pipeline li<Tab>` → `jctl pipeline list`
- Options: `jctl pipeline run --<Tab>` → shows `--param`, `--wait`, `--notify`
- Job names (substring, case-insensitive): `jctl pipeline run hamc<Tab>` → matches `managed-cloud/MC-26.05.1/hamc-upgrade-environment`

See [docs/guides/COMPLETION_GUIDE.md](docs/guides/COMPLETION_GUIDE.md) for more details and manual setup.

### Initial Setup

One command sets up everything: profile, Jenkins URL, and authentication!

```bash
# Initialize configuration (everything in one flow)
jctl config init

# You'll be prompted for:
#   1. Profile name (e.g., 'dev', 'stg', 'production')
#   2. Jenkins URL
#   3. Jenkins username and API token (entered immediately)

# That's it! You're authenticated and ready to use jctl
jctl pipeline list
jctl pipeline run <pipeline-name>
```

**Example flow:**
```
$ jctl config init
Profile name (production): dev
Jenkins URL: https://jenkins-dev.example.com
Jenkins username: avidal
Jenkins API token: ●●●●●●●●

✓ Configuration saved
✓ Profile 'dev' created and set as default
✓ API token saved securely

You're all set! Try: jctl pipeline list
```

**Guides:**
- [docs/guides/INIT_WORKFLOW.md](docs/guides/INIT_WORKFLOW.md) - Detailed init workflow
- [docs/guides/API_TOKEN_GUIDE.md](docs/guides/API_TOKEN_GUIDE.md) - How to get Jenkins API tokens

### Basic Usage

```bash
# Trigger a Jenkins job
jctl job trigger deploy-staging \
  --param environment=staging \
  --param branch=main \
  --wait

# List pipelines matching a pattern
jctl pipeline list --filter "deploy-*"

# Stream logs for a specific build
jctl job logs deploy-staging-142 --follow

# Cancel a running build
jctl pipeline cancel deploy-staging 142
```

### Working with Multiple Environments

jctl supports multiple profiles for different Jenkins environments (dev, staging, production):

```bash
# Add profiles for different environments (API token auth only)
jctl config add-profile dev --jenkins-url https://jenkins-dev.example.com
jctl config add-profile stg --jenkins-url https://jenkins-stg.example.com

# Authenticate each profile with API tokens
jctl --profile dev auth token
jctl --profile stg auth token

# Use specific profile with --profile flag
jctl --profile dev pipeline list
jctl --profile stg pipeline run release/deploy-staging
jctl --profile production auth status
```

**Guides:**
- [docs/guides/PROFILES_GUIDE.md](docs/guides/PROFILES_GUIDE.md) - Complete profile configuration guide

## Command Reference

### Authentication Commands

```bash
jctl auth token          # Configure Jenkins API token
jctl auth status         # Show authentication status
jctl auth logout         # Clear stored credentials
```

**Documentation:**
- [API Token Guide](docs/guides/API_TOKEN_GUIDE.md) - Quick setup with Jenkins API tokens

### Job Commands

```bash
jctl job trigger <name>           # Trigger a job with parameters
jctl job logs <name> [--follow]   # View or stream job logs
```

**Options:**
- `--param KEY=VALUE` - Pass job parameters
- `--wait` - Wait for job completion
- `--follow` - Stream logs in real-time

### Pipeline Commands

```bash
jctl pipeline list                    # List available pipelines
jctl pipeline run <name>              # Execute pipeline with parameters
jctl pipeline describe <name> <num>   # Show pipeline details with stages
jctl pipeline logs <name> [num]       # View or stream pipeline logs
jctl pipeline cancel <name> <num>     # Cancel running pipeline
```

**Options:**
- `--param KEY=VALUE` - Pass pipeline parameters
- `--wait` - Wait for pipeline completion
- `--notify` - Get notification when pipeline completes
- `--follow` - Stream logs in real-time
- `--filter` - Filter pipeline list by pattern
- `--folder` - Filter by Jenkins folder

### Configuration Commands

```bash
jctl config init                      # Initialize configuration
jctl config add-profile <name>        # Add new profile
jctl config set <key> <val>           # Set configuration value
jctl config get <key>                 # Get configuration value
jctl config list                      # List all configurations
jctl config show                      # Show full configuration
```

### 🚧 Planned Features (v0.2.0)

The following commands are planned for future releases:

**Job Commands:**
- `jctl job status` - Get job status
- `jctl job stop` - Stop running job
- `jctl job history` - Show job history
- `jctl job params` - List job parameters

**Pipeline Commands:**
- `jctl pipeline search` - Search pipelines
- `jctl pipeline pause` - Pause at input step
- `jctl pipeline resume` - Resume paused pipeline
- `jctl pipeline replay` - Replay previous run
- `jctl pipeline restart` - Restart from beginning
- `jctl pipeline validate` - Validate configuration

See [CHANGELOG.md](CHANGELOG.md) for version history and roadmap.

## Configuration

Configuration is stored in `~/.jctl/config.yaml`:

```yaml
version: "1.0"
default_profile: production

profiles:
  production:
    jenkins:
      url: https://jenkins.example.com
    output:
      format: table
      color: auto

defaults:
  timeout: 30
  retry_count: 3
  log_level: INFO
```

## Environment Variables

Each variable is the env equivalent of a CLI flag (explicit flags still win):

| Variable | Equivalent | Notes |
|---|---|---|
| `JCTL_PROFILE` | `--profile <name>` | Active profile |
| `JCTL_OUTPUT_FORMAT` | `--output table\|json\|yaml\|plain` | Output format |
| `JCTL_LOG_LEVEL` | `--log-level DEBUG\|INFO\|WARNING\|ERROR\|CRITICAL` | Takes precedence over `--debug` |
| `JCTL_JENKINS_URL` | n/a (overrides the profile's `jenkins.url`) | Useful for one-off runs against a different host without editing config |
| `JCTL_NO_COLOR` | n/a (sets Rich `no_color=True`) | Any non-empty value disables ANSI. The wider `NO_COLOR` convention is also honored. |

```bash
# Examples
JCTL_OUTPUT_FORMAT=json jctl pipeline list | jq '.[].name'
JCTL_JENKINS_URL=https://jenkins-dev.example.com jctl pipeline list
JCTL_NO_COLOR=1 jctl auth status
```

## Development

### Setup Development Environment

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run with coverage
pytest --cov=jctl --cov-report=html

# Format code
black jctl tests

# Lint code
ruff check jctl tests

# Type check
mypy jctl
```

### Project Structure

```
cli/jenkins/
├── jctl/                      # Main package
│   ├── __init__.py
│   ├── __main__.py           # CLI entry point
│   ├── cli.py                # Click command groups
│   ├── auth/                 # Authentication module
│   │   ├── api_token.py     # Jenkins API token auth
│   │   └── keystore.py      # Secure credential storage
│   ├── jenkins/              # Jenkins integration
│   │   ├── client.py        # API client
│   │   ├── jobs.py          # Job operations
│   │   └── pipelines.py     # Pipeline operations
│   ├── config/               # Configuration management
│   │   ├── manager.py       # Config manager
│   │   └── schemas.py       # Pydantic models
│   ├── utils/                # Utilities
│   │   ├── output.py        # Output formatting
│   │   ├── logging.py       # Logging setup
│   │   └── validators.py    # Input validation
│   └── commands/             # CLI command implementations
│       ├── auth.py
│       ├── job.py
│       ├── pipeline.py
│       └── config.py
├── tests/                    # Test suite
│   ├── unit/                # Unit tests
│   └── integration/         # Integration tests
├── docs/                     # Documentation
├── scripts/                  # Utility scripts
├── pyproject.toml           # Project configuration
└── README.md                # This file
```

## Examples

### Common Workflows

```bash
# Provision new environment
jctl pipeline run provision-environment \
  --param environment_name=staging-001 \
  --param region=us-east-1 \
  --wait --notify

# Run a periodic monitoring job
jctl job trigger monitor-infrastructure --wait

# Emergency pipeline cancellation
jctl pipeline cancel teardown-environment 89 \
  --reason "Wrong account selected"

# View pipeline execution details
jctl pipeline describe provision-environment 142

# Stream pipeline logs in real-time
jctl pipeline logs provision-environment 142 --follow
```

### Integration with Scripts

```bash
#!/bin/bash
# Automated environment provisioning

# Trigger job and wait for completion
jctl job trigger provision-environment \
  --param environment_name=staging \
  --wait

if [ $? -eq 0 ]; then
  echo "✓ Environment provisioned successfully"
else
  echo "✗ Environment provisioning failed"
  # View the logs to troubleshoot
  jctl job logs provision-environment
  exit 1
fi
```

## Security

- Tokens stored in OS-native keychains (macOS Keychain, Linux Secret Service, Windows Credential Manager)
- Jenkins API token sent over HTTP Basic auth on HTTPS only
- SSL certificate validation by default
- Audit logging for all job triggers
- Config files set with 0600 permissions

## Troubleshooting

### Authentication Issues

```bash
# Check auth status
jctl auth status

# Re-authenticate
jctl auth logout
jctl auth token
```

### Connection Issues

```bash
# Test Jenkins connectivity
jctl --debug pipeline list

# Verify configuration
jctl config get jenkins.url
```

### Token Rotation

```bash
# Generate a new API token in Jenkins, then:
jctl auth logout
jctl auth token
```

## Contributing

See the main repository [CONTRIBUTING.md](../../CONTRIBUTING.md) for contribution guidelines.

## Support

- **Email**: avnervidal27@gmail.com
- **Issues**: [GitHub Issues](https://github.com/avidala/jctl/issues)


## 📚 Documentation

### Getting Started
- [Quick Start Guide](docs/guides/QUICK_START.md) - Get up and running in 2 minutes
- [Installation & Setup](docs/guides/INIT_WORKFLOW.md) - Detailed setup instructions

### Authentication
- [API Token Guide](docs/guides/API_TOKEN_GUIDE.md) - Authentication with Jenkins API tokens

### Configuration
- [Multiple Profiles](docs/guides/PROFILES_GUIDE.md) - Manage dev, staging, and production

### Advanced
- [Shell Completion](docs/guides/COMPLETION_GUIDE.md) - Enable tab completion for faster commands

### Technical Documentation
- [Architecture](docs/ARCHITECTURE.md) - System design and architecture
- [Development Guide](docs/DEVELOPMENT.md) - Contributing and development setup
- [Platform Testing](docs/PLATFORM_TESTING.md) - Testing across macOS, Linux, Windows

### Project Information
- [Changelog](CHANGELOG.md) - Version history and release notes
- [Roadmap](ROADMAP.md) - Future plans and features
- [Contributing](CONTRIBUTING.md) - How to contribute
- [Security](SECURITY.md) - Security policy and vulnerability reporting

## License

MIT License - See [LICENSE](../../LICENSE) for details.

---

<div align="center">

<img src="assets/org-avatar.svg" alt="AVIDALA" width="120"/>

<br/>

**Built by AVIDALA**
*DevOps Tools & Automation*

<br/>

[![GitHub](https://img.shields.io/badge/GitHub-avidala-181717?style=flat&logo=github)](https://github.com/avidala)
[![Email](https://img.shields.io/badge/Email-avnervidal27%40gmail.com-D14836?style=flat&logo=gmail&logoColor=white)](mailto:avnervidal27@gmail.com)

</div>
