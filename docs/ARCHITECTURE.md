# jctl Architecture

This document describes the architecture, design decisions, and technical implementation of jctl (Jenkins Control CLI).

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Component Design](#component-design)
- [Data Flow](#data-flow)
- [Security Architecture](#security-architecture)
- [Technology Stack](#technology-stack)
- [Design Decisions](#design-decisions)
- [Extension Points](#extension-points)

## Overview

jctl is a command-line interface tool for managing Jenkins pipelines using Jenkins API token authentication, optimized for DevOps workflows.

### Key Design Goals

1. **User-Friendly**: Simple, intuitive CLI with excellent UX
2. **Secure**: Credentials stored in the OS keystore, HTTPS-only API calls
3. **Reliable**: Retry logic, proper error handling, and robust API integration
4. **Fast**: Caching, async operations, and optimized performance
5. **Extensible**: Modular design allowing easy feature additions
6. **Well-Tested**: High test coverage and comprehensive validation

### Architecture Principles

- **Separation of Concerns**: Clear boundaries between layers
- **Single Responsibility**: Each module has one well-defined purpose
- **Dependency Injection**: Loosely coupled components
- **Fail Fast**: Early validation and clear error messages
- **Async-First**: Non-blocking operations for better performance

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        User                              │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   CLI Layer (Click)                      │
│  ┌────────────┬───────────┬──────────┬────────────────┐ │
│  │   auth     │    job    │ pipeline │     config     │ │
│  │  commands  │  commands │ commands │   commands     │ │
│  └────────────┴───────────┴──────────┴────────────────┘ │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  Business Logic Layer                    │
│  ┌──────────────────┬─────────────────────────────────┐ │
│  │  Authentication  │     Jenkins Integration         │ │
│  │  ┌────────────┐  │  ┌──────────┬────────────────┐  │ │
│  │  │ API Token  │  │  │  Client  │   Operations   │  │ │
│  │  └────────────┘  │  │          │   (Jobs/Pipes) │  │ │
│  └──────────────────┴──┴──────────┴────────────────┘─┘ │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   Storage Layer                          │
│  ┌──────────────┬───────────────┬────────────────────┐  │
│  │  OS Keystore │  Encrypted    │   Configuration    │  │
│  │  (Primary)   │  Fallback     │   (YAML)           │  │
│  └──────────────┴───────────────┴────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              External Services                           │
│  ┌──────────────────────────────────────────────────────┐│
│  │ Jenkins API (REST/JSON)                              ││
│  └──────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

#### 1. CLI Layer (`jctl/commands/`)
- **Purpose**: User interaction, command parsing, output formatting
- **Components**: Command groups (auth, job, pipeline, config)
- **Technology**: Click framework
- **Responsibilities**:
  - Parse command-line arguments
  - Validate user input
  - Invoke business logic
  - Format and display output
  - Handle user interrupts (Ctrl+C)

#### 2. Business Logic Layer
- **Purpose**: Core functionality, business rules, orchestration
- **Components**:
  - Authentication (`jctl/auth/`)
  - Jenkins integration (`jctl/jenkins/`)
  - Configuration management (`jctl/config/`)
  - Utilities (`jctl/utils/`)
- **Responsibilities**:
  - Implement business logic
  - Orchestrate operations
  - Handle retries and error recovery
  - Validate business rules

#### 3. Storage Layer
- **Purpose**: Persistent storage of credentials and configuration
- **Components**:
  - OS-native keystore integration
  - Encrypted fallback storage
  - YAML configuration files
- **Responsibilities**:
  - Securely store credentials
  - Manage configuration persistence
  - Handle storage failures gracefully

#### 4. External Services Layer
- **Purpose**: Integration with external APIs
- **Components**:
  - Jenkins REST API
- **Responsibilities**:
  - HTTP communication
  - API authentication (HTTP Basic auth with API token)
  - Response parsing
  - Error handling

## Component Design

### Authentication Module (`jctl/auth/`)

```
auth/
├── __init__.py
├── api_token.py         # Jenkins API token auth
└── keystore.py          # Secure credential storage
```

#### API Token Authenticator (`api_token.py`)

**Purpose**: Username + Jenkins API token authentication

**Features**:
- Stores username and API token via `SecureKeystore`
- No browser interaction required
- Works equally well for interactive use and CI/CD

**Flow**:
1. User runs `jctl auth token` (or supplies values via flags)
2. Credentials are written to the OS keystore (`jenkins_username`, `jenkins_token`)
3. `JenkinsClient` uses them as HTTP Basic auth on every request

#### Secure Keystore (`keystore.py`)

**Purpose**: Secure credential storage with multiple backends

**Storage Hierarchy**:
1. **OS-Native Keystore** (Primary)
   - macOS: Keychain
   - Linux: SecretService (GNOME Keyring, KWallet)
   - Windows: Credential Manager
2. **Encrypted Fallback** (When keystore unavailable)
   - Fernet symmetric encryption
   - Machine-derived encryption key (PBKDF2)

**Key Derivation**:
```python
machine_id = f"{platform.node()}-{platform.system()}"
key = hashlib.pbkdf2_hmac(
    "sha256",
    machine_id.encode(),
    b"jctl-salt-v1",
    100000,  # iterations
    32       # key length
)
encryption_key = base64.urlsafe_b64encode(key)
```

### Jenkins Integration Module (`jctl/jenkins/`)

```
jenkins/
├── __init__.py
└── client.py           # Jenkins API client
```

#### Jenkins Client (`client.py`)

**Purpose**: Unified interface to Jenkins REST API

**Features**:
- Async HTTP client (httpx)
- Automatic retry with exponential backoff
- CSRF token handling (crumb)
- Support for folder paths in job names
- Streaming log support

**Retry Logic**:
```python
@retry(
    retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.RequestError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
)
```

**Retries on**:
- Network errors (connection failures, timeouts)
- HTTP 429 (Rate Limited)
- HTTP 503 (Service Unavailable)
- HTTP 504 (Gateway Timeout)

**Does NOT retry**:
- HTTP 400 (Bad Request)
- HTTP 401 (Unauthorized)
- HTTP 403 (Forbidden)
- HTTP 404 (Not Found)

### Configuration Module (`jctl/config/`)

```
config/
├── __init__.py
├── manager.py          # Configuration management
└── schemas.py          # Pydantic models
```

#### Configuration Manager (`manager.py`)

**Purpose**: Manage configuration files and profiles

**Features**:
- YAML-based configuration
- Multiple profiles support
- Environment variable overrides
- Validation with Pydantic

**Configuration Structure**:
```yaml
version: "1.0"
default_profile: production

profiles:
  production:
    jenkins:
      url: https://jenkins.example.com
      verify_ssl: true

defaults:
  timeout: 30
  retry_count: 3
  log_level: INFO
```

#### Pydantic Schemas (`schemas.py`)

**Purpose**: Type-safe configuration validation

**Models**:
- `Config`: Root configuration model
- `ProfileConfig`: Individual profile configuration
- `JenkinsConfig`: Jenkins-specific settings

### Utilities Module (`jctl/utils/`)

```
utils/
├── __init__.py
├── completion.py       # Shell completion
├── jenkins_client_factory.py  # Client creation
├── logging.py          # Logging setup
├── output.py           # Output formatting
└── validators.py       # Input validation
```

#### Completion (`completion.py`)

**Purpose**: Shell completion for commands and job names

**Features**:
- 5-minute cache for job list
- Async job fetching
- Silent failure (doesn't break completion)

#### Jenkins Client Factory (`jenkins_client_factory.py`)

**Purpose**: Centralized client creation logic

**Features**:
- Reads username and API token from the keystore via `APITokenAuthenticator`
- Returns an authenticated `JenkinsClient` ready for use
- Exits with a clear error message when no credentials are stored

#### Logging (`logging.py`)

**Purpose**: Structured logging with Rich output

#### Output Formatting (`output.py`)

**Formats**:
- **Table**: Rich tables with colors
- **JSON**: Machine-readable JSON
- **YAML**: Human-readable YAML
- **Plain**: Simple text output

## Data Flow

### Authentication Flow

```
┌──────┐                 ┌──────┐                ┌─────────┐
│ User │                 │ jctl │                │ Jenkins │
└───┬──┘                 └──┬───┘                └────┬────┘
    │                       │                         │
    │ jctl auth token       │                         │
    ├──────────────────────>│                         │
    │ <username> <token>    │                         │
    │                       │                         │
    │                       │ Store in OS keystore    │
    │                       │ (jenkins_username,      │
    │                       │  jenkins_token)         │
    │                       │                         │
    │ ✓ Configured          │                         │
    │<──────────────────────┤                         │
    │                       │                         │
    │ jctl pipeline list    │                         │
    ├──────────────────────>│                         │
    │                       │                         │
    │                       │ GET /api/json           │
    │                       │ Authorization: Basic …  │
    │                       ├────────────────────────>│
    │                       │                         │
    │                       │ 200 + pipelines         │
    │                       │<────────────────────────┤
    │                       │                         │
    │ Display pipelines     │                         │
    │<──────────────────────┤                         │
```

### Job Trigger Flow

```
┌──────┐                 ┌──────┐                ┌─────────┐
│ User │                 │ jctl │                │ Jenkins │
└───┬──┘                 └──┬───┘                └────┬────┘
    │                       │                         │
    │ jctl job trigger      │                         │
    │ --param env=staging   │                         │
    │ --wait                │                         │
    ├──────────────────────>│                         │
    │                       │                         │
    │                       │ Get Jenkins client      │
    │                       │ (with API token auth)   │
    │                       │                         │
    │                       │ POST /job/trigger       │
    │                       │ with parameters         │
    │                       ├────────────────────────>│
    │                       │                         │
    │                       │ Return queue_item_id    │
    │                       │<────────────────────────┤
    │                       │                         │
    │ Job triggered         │                         │
    │<──────────────────────┤                         │
    │                       │                         │
    │                       │ Poll build status       │
    │                       │ GET /job/build/{num}    │
    │                       ├────────────────────────>│
    │                       │                         │
    │                       │ Return build info       │
    │                       │<────────────────────────┤
    │                       │                         │
    │ Build succeeded       │                         │
    │<──────────────────────┤                         │
```

## Security Architecture

### Defense in Depth

jctl implements multiple security layers:

#### Layer 1: Authentication
- **Jenkins API Tokens**: Scoped permissions on the Jenkins side
- **No Password Storage**: Never store user passwords; only the API token

#### Layer 2: Credential Storage
- **OS-Native Keystore**: Leverages system security
- **Encrypted Fallback**: Fernet encryption with derived keys
- **Permissions**: Files set to 0600 (user-only)

#### Layer 3: Network Security
- **HTTPS Only**: All API calls encrypted
- **Certificate Verification**: SSL validation (configurable)
- **Timeout Configuration**: Prevents hanging connections

#### Layer 4: Application Security
- **Input Validation**: All user input validated
- **No Code Injection**: Parameterized API calls
- **Error Handling**: Sensitive data never logged
- **Exit Codes**: Distinct codes for error types

#### Layer 5: Dependencies
- **Security Scanning**: Bandit and Safety checks
- **Version Constraints**: Upper bounds prevent breaking changes
- **Regular Updates**: Dependencies kept current

### Threat Model

**Threats Mitigated**:
- ✅ Credential theft from filesystem
- ✅ Man-in-the-middle attacks
- ✅ Token exposure in logs
- ✅ Unauthorized API access
- ✅ Command injection
- ✅ Dependency vulnerabilities

**Threats NOT Mitigated** (user responsibility):
- ❌ Compromised user machine
- ❌ Malicious Jenkins server
- ❌ Network-level attacks (use VPN)

## Technology Stack

### Core Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| CLI Framework | Click | 8.1.7+ | Command-line interface |
| HTTP Client | httpx | 0.25.2+ | Async HTTP requests |
| Credential Storage | keyring | 24.3.0+ | OS keystore integration |
| Encryption | cryptography | 41.0.7+ | Fernet encryption |
| Config Validation | Pydantic | 2.5.0+ | Type-safe config |
| Terminal UI | Rich | 13.7.0+ | Beautiful output |
| Retry Logic | tenacity | 8.2.0+ | Exponential backoff |

### Development Tools

| Tool | Purpose |
|------|---------|
| pytest | Testing framework |
| black | Code formatting |
| ruff | Linting |
| mypy | Type checking |
| bandit | Security scanning |
| pre-commit | Git hooks |

## Design Decisions

### Why Click over argparse?

**Decision**: Use Click for CLI framework

**Rationale**:
- Better UX (help messages, error handling)
- Built-in support for subcommands
- Easy parameter validation
- Shell completion support
- Cleaner, more readable code

### Why httpx over requests?

**Decision**: Use httpx for HTTP client

**Rationale**:
- Native async/await support
- Better timeout handling
- HTTP/2 support
- Modern, actively maintained
- Compatible with requests API

### Why API Tokens Only?

**Decision**: API token authentication is the only supported method

**Rationale**:
- Works for both interactive use and automation (CI/CD)
- No external identity provider dependency
- Simple to rotate (generate a new token in Jenkins, run `jctl auth token` again)
- A prior OAuth/SSO implementation was removed in favor of this single, simpler path

### Why OS Keystore with Encrypted Fallback?

**Decision**: Primary keystore, encrypted fallback

**Rationale**:
- OS keystore: Best security when available
- Encrypted fallback: Works everywhere
- No dependency on specific OS
- Graceful degradation

### Why Async/Await?

**Decision**: Use async for I/O operations

**Rationale**:
- Non-blocking API calls
- Better performance for concurrent operations
- Modern Python best practice
- Enables streaming logs

### Why 5-Minute Completion Cache?

**Decision**: Cache job list for 5 minutes

**Rationale**:
- Balance between freshness and performance
- Tab completion should be fast
- Jenkins job list changes infrequently
- 5 min: Good trade-off

## Extension Points

### Adding New Commands

1. Create command file in `jctl/commands/`
2. Define Click command group
3. Implement command functions
4. Register in `jctl/cli.py`
5. Add tests in `tests/unit/`

### Adding New Output Formats

1. Add format to `utils/output.py`
2. Implement formatter function
3. Update CLI `--output` choices
4. Add format tests

### Adding New Storage Backends

1. Extend `keystore.py` with new backend
2. Implement store/retrieve/delete methods
3. Add fallback logic
4. Test on target platform

---

**Document Version**: 2.0
**Last Updated**: 2026-05-13
**Status**: Current — Okta/OAuth removed
