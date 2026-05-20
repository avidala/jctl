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

- 🔐 **API Token Authentication** — Username + Jenkins API token, stored in the OS keychain (macOS Keychain / Linux Secret Service / Windows Credential Manager) with an encrypted file fallback at `~/.jctl/credentials.enc` for headless / CI environments.
- 🚀 **Pipeline & Job Management** — List, run, describe, cancel; stream logs with `--follow`; `--wait` for completion.
- 🎯 **Multiple Profiles** — `dev` / `stg` / `production` switchable per-invocation via `--profile` or `JCTL_PROFILE`.
- 📦 **Machine-readable output** — `--output json|yaml|plain` (global flag, placed before the subcommand); status banners and progress lines auto-route to stderr so stdout stays parseable for `jq` / `yq` pipelines.
- 🌐 **Env-var configuration** — `JCTL_OUTPUT_FORMAT`, `JCTL_LOG_LEVEL`, `JCTL_JENKINS_URL`, `JCTL_PROFILE`, `JCTL_NO_COLOR`.
- ⌨️ **Shell Completion** — Persistent on-disk cache (5-min TTL) + case-insensitive substring matching, so `jctl pipeline run hamc<Tab>` matches `managed-cloud/MC-26.05.1/hamc-upgrade-environment`. Confirmation-gated installer (`--install --dry-run` / `--install --yes`).
- 🔁 **Resilient HTTP** — Automatic retry with exponential backoff on 429/503/504 and network errors; HTML stripped from Jenkins error pages; readable `ConnectTimeout: could not reach <host>` messages.
- 🎨 **Rich terminal UI** — Tables, colors, sub-second durations rendered as `228ms` instead of `0s`.

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
# Install the latest tagged release in an isolated env
pipx install "git+https://github.com/avidala/jctl.git@v0.3.0"

# Or track main
pipx install "git+https://github.com/avidala/jctl.git"
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
# Trigger a Jenkins job and block until it finishes
jctl job trigger deploy-staging \
  --param environment=staging \
  --param branch=main \
  --wait

# List pipelines, freshest first (substring filter, case-insensitive)
jctl pipeline list --filter deploy

# Just the failed ones, machine-readable
jctl --output json pipeline list --status FAILED | jq '.[] | {name, last_run}'

# Stream logs for build #142 in real-time
jctl job logs deploy-staging 142 --follow

# Tail the latest build (build number is optional)
jctl pipeline logs deploy-staging --follow

# Cancel a running build (--yes skips the confirmation prompt)
jctl pipeline cancel deploy-staging 142 --yes
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
# Interactive setup
jctl auth token

# Non-interactive (for setup scripts / CI)
jctl auth token --username you@example.com --token "$JENKINS_TOKEN"

jctl --output json auth status   # status as JSON (--output is global; place it before the subcommand)
jctl auth status                 # Show authentication status
jctl auth logout                 # Clear stored credentials
```

**Documentation:**
- [API Token Guide](docs/guides/API_TOKEN_GUIDE.md) - Quick setup with Jenkins API tokens

### Job Commands

```bash
jctl job trigger <name>                       # Trigger a job with parameters
jctl job logs <name> [build] [--follow]       # View or stream job logs
```

**Options for `trigger`:**
- `-p, --param KEY=VALUE` - Pass job parameters (repeatable)
- `--wait` - Block until the build finishes; exit non-zero on FAILURE/ABORTED
- `--dry-run` - Print what would be triggered without calling Jenkins

**Options for `logs`:**
- `--follow, -f` - Stream logs in real-time (`X-More-Data` polling)
- If `[build]` is omitted, the latest build is auto-resolved via `lastBuild`.

### Pipeline Commands

```bash
jctl pipeline list                            # List available pipelines (sorted by recency)
jctl pipeline run <name>                      # Execute pipeline with parameters
jctl pipeline describe <name> [build]         # Show pipeline details with stages (latest build by default)
jctl pipeline logs <name> [build] [--follow]  # View or stream pipeline logs
jctl pipeline cancel <name> <build>           # Cancel running pipeline
```

**Options for `list`:**
- `-f, --filter PATTERN` - Substring filter, case-insensitive (matches anywhere in the full name)
- `--folder FOLDER` - Limit to a Jenkins folder (e.g. `deploy/staging`)
- `--status SUCCESS|FAILED|FAILURE|RUNNING|ABORTED` - Filter by last build status (`FAILED` is an alias for Jenkins' `FAILURE`)
- `-n, --limit N` - Limit rows (default 50)

**Options for `run`:**
- `-p, --param KEY=VALUE` - Pipeline parameters (repeatable)
- `--wait` - Block until the pipeline finishes; renders live stage progress
- `--notify` - Print a completion summary without rendering live stages

**Options for `cancel`:**
- `--reason TEXT` - Audit-log reason for cancellation
- `--yes, -y` - Skip the confirmation prompt. A declined prompt exits 130 (Ctrl+C convention).

### Configuration Commands

```bash
jctl config init                              # Interactive setup (profile + auth in one flow)
jctl config add-profile <name>                # Add a new profile (non-interactive)
jctl config set <key> <val>                   # Set configuration value (type-validated)
jctl config get <key>                         # Get configuration value
jctl config list                              # Pretty-print all config
jctl config show                              # Show the raw YAML
```

`config set` validates the value against the schema (an `int` field rejects `"notanumber"` instead of silently corrupting the file) and refuses unknown root-level keys.

### Planned Features

See [ROADMAP.md](ROADMAP.md) for the full picture. Top of the list:

- **Job**: `status`, `stop`, `history`, `params`
- **Pipeline**: `search`, `pause`, `resume`, `replay`, `restart`, `validate`

See [CHANGELOG.md](CHANGELOG.md) for version history.

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
jctl/
├── __main__.py               # Entry point: `python -m jctl` and the `jctl` script
├── cli.py                    # Click root group, global flags, completion installer
├── constants.py              # Exit codes (EXIT_AUTH_ERROR=3, EXIT_USER_CANCELLED=130, …)
├── auth/
│   ├── api_token.py          # Jenkins API token store/retrieve via SecureKeystore
│   └── keystore.py           # OS keychain + encrypted file fallback (~/.jctl/credentials.enc)
├── jenkins/
│   └── client.py             # Async + sync API client with retry, CSRF, redirect-following
├── config/
│   ├── manager.py            # YAML load/save, interactive init, env-var overrides
│   └── schemas.py            # Pydantic models (validate_assignment=True)
├── utils/
│   ├── output.py             # OutputFormatter (table/json/yaml/plain), format_duration
│   ├── completion.py         # On-disk completion cache + substring matcher
│   ├── jenkins_client_factory.py  # Build a JenkinsClient from config + stored creds
│   ├── logging.py            # Rich logging setup
│   └── password_prompt.py    # asterisk-masking prompt with getpass fallback
└── commands/
    ├── auth.py               # `jctl auth token | status | logout`
    ├── job.py                # `jctl job trigger | logs`
    ├── pipeline.py           # `jctl pipeline list | run | describe | logs | cancel`
    └── config.py             # `jctl config init | get | set | list | show | add-profile`

tests/unit/                   # ~200 tests, ~83% line coverage
docs/                         # Architecture, development, user guides
pyproject.toml
ROADMAP.md  CHANGELOG.md  SECURITY.md  CONTRIBUTING.md
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

- Credentials stored in OS-native keychains (macOS Keychain, Linux Secret Service, Windows Credential Manager).
- When the OS keystore is unusable (locked Keychain, headless Linux without Secret Service, CI runners), credentials fall back to `~/.jctl/credentials.enc` — a Fernet-encrypted JSON blob written atomically with mode `0600`.
- Jenkins API token sent over HTTP Basic auth; SSL certificate validation is on by default (toggle per-profile with `jenkins.verify_ssl`).
- `~/.jctl/config.yaml` is written with mode `0600` and the directory with `0700`.
- `jctl pipeline cancel <name> <build> --reason "<text>"` records a reason for the cancellation in the user-facing output; Jenkins itself logs the API call separately.

## Troubleshooting

### Authentication issues

```bash
jctl auth status                # check whether a token is configured
jctl auth logout && jctl auth token   # re-authenticate
```

If `auth token` fails with `Can't store password on keychain` (locked
macOS Keychain, headless Linux without Secret Service, CI runner),
jctl will automatically fall back to an encrypted file under
`~/.jctl/credentials.enc`. No action needed — but verify with
`ls -l ~/.jctl/credentials.enc`.

### Connection issues

```bash
# See every retry attempt + the exact URL/path being requested
jctl --log-level DEBUG pipeline list

# Point at a different Jenkins for one command without touching config
JCTL_JENKINS_URL=https://jenkins-staging.example.com jctl pipeline list

# What URL does my active profile actually point at?
jctl config get jenkins.url
```

### Token rotation

```bash
# Generate a new API token in Jenkins → Configure → API Token → Add new,
# then either:
jctl auth logout && jctl auth token                # interactive
jctl auth token --username you@example.com --token "$NEW"   # non-interactive
```

### Piping `jctl` into other tools

`jctl` separates streams so machine-readable output stays clean:
- Data (table / JSON / YAML / plain) → **stdout**
- `Using API token authentication as …`, `Found N pipeline(s)`, progress
  spinners, error messages → **stderr**

So `jctl --output json pipeline list | jq '.[].name'` is always safe; the
banners won't break your parser.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

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

MIT License — see [LICENSE](LICENSE).

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
