# Pre-commit Hooks for jctl

## Status

✅ Pre-commit hooks are configured in `.pre-commit-config.yaml`

## Current Limitation

Since jctl is currently in a subdirectory of the `public-cloud-infrastructure` monorepo, pre-commit hooks will run on the entire repository. Once jctl is migrated to its own repository, the hooks will work perfectly.

## What's Configured

- **trailing-whitespace**: Remove trailing whitespace
- **end-of-file-fixer**: Ensure files end with newline
- **check-yaml**: Validate YAML syntax
- **check-json**: Validate JSON syntax
- **check-merge-conflict**: Detect merge conflicts
- **detect-private-key**: Prevent committing private keys
- **black**: Python code formatting (line length 100)
- **ruff**: Python linting with auto-fix
- **bandit**: Security scanning

## Manual Usage (Current)

Since we're in a monorepo, manually run pre-commit on jctl files:

```bash
# Format jctl Python files
black jctl/ tests/

# Lint jctl files
ruff check jctl/ tests/ --fix

# Security scan
bandit -r jctl/ -ll
```

## After Migration

Once jctl is in its own repository, pre-commit will work automatically:

```bash
# Install hooks (one-time)
pre-commit install

# Hooks run automatically on git commit
git commit -m "your message"

# Or run manually
pre-commit run --all-files
```

## Configuration

The `.pre-commit-config.yaml` file is ready for the standalone repository. No changes needed after migration.

## Testing

To test the configuration now:

```bash
# In virtual environment
source venv/bin/activate

# Test on jctl files only
black jctl/ tests/ --check
ruff check jctl/ tests/
bandit -r jctl/ -ll
```

All checks should pass! ✅
