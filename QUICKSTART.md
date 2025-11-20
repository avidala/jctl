# jctl Quick Start Guide

## Installation

### 1. Set up virtual environment

```bash
cd cli/jenkins
python3 -m venv venv
source venv/bin/activate
```

### 2. Install jctl

```bash
pip install -e .
```

## Verify Installation

```bash
jctl --version
jctl --help
```

## Current Status

The CLI skeleton is complete with all command structures in place:

### ✅ Completed
- Project structure setup
- All command groups (auth, job, pipeline, config)
- All pipeline action commands (run, cancel, pause, resume, replay, restart, validate)
- Beautiful CLI with Rich library integration
- Configuration management structure

### 🚧 To Be Implemented
- Okta SSO authentication flow
- Jenkins API client integration
- Token management and keystore
- Actual command implementations
- Configuration file handling

## Testing the CLI

### View all commands

```bash
jctl --help
```

### Test authentication commands

```bash
jctl auth --help
jctl auth login    # Shows stub implementation
jctl auth status   # Shows stub implementation
```

### Test pipeline commands

```bash
jctl pipeline --help
jctl pipeline cancel --help
jctl pipeline replay --help
```

### Test with parameters

```bash
# These show what the commands will look like when implemented
jctl pipeline run hamc-new-environment \
  --param environment_name=test \
  --param aws_account_id=123456

jctl pipeline cancel hamc-test 142 \
  --reason "Testing cancellation"

jctl job trigger hamc-monitor-drift --dry-run
```

## Project Structure

```
cli/jenkins/
├── jctl/                          # Main package
│   ├── __init__.py
│   ├── __main__.py               # Entry point
│   ├── cli.py                    # Main CLI setup
│   ├── auth/                     # Auth module (to implement)
│   │   └── __init__.py
│   ├── jenkins/                  # Jenkins API (to implement)
│   │   └── __init__.py
│   ├── config/                   # Config management (to implement)
│   │   └── __init__.py
│   ├── utils/                    # Utilities (to implement)
│   │   └── __init__.py
│   └── commands/                 # CLI commands
│       ├── __init__.py
│       ├── auth.py              # Auth commands
│       ├── job.py               # Job commands
│       ├── pipeline.py          # Pipeline commands ✅
│       └── config.py            # Config commands
├── tests/                        # Test suite (to add)
├── docs/                         # Documentation
├── pyproject.toml               # Project config
├── requirements.txt             # Dependencies
├── README.md                    # Full documentation
└── QUICKSTART.md               # This file
```

## Next Steps

See the implementation guide in:
- `../../jenkins-cli-design.md` - Architecture and design
- `../../jenkins-cli-implementation-prompt.md` - Implementation details

The next priority implementations are:
1. Configuration management (config module)
2. Jenkins API client (jenkins module)
3. Okta SSO authentication (auth module)
4. Command implementations (filling in the TODO sections)

## Development

### Format code

```bash
black jctl tests
```

### Run linter

```bash
ruff check jctl tests
```

### Run tests

```bash
pytest
```

## Notes

- All commands currently show "⚠ Not yet implemented" messages
- The CLI structure follows the design specification exactly
- Pipeline action commands (cancel, pause, resume, replay, restart, validate) are all in place
- Ready for implementation according to the design docs
