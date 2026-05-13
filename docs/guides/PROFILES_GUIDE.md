# Using Profiles with jctl

jctl supports multiple configuration profiles so you can switch between
Jenkins environments (dev, staging, production, etc.) without rewriting your
config each time.

## Overview

Profiles let you maintain separate configurations for:
- Different Jenkins servers
- Different SSL/TLS settings
- Different output preferences

Each profile also has its own credentials in the OS keystore — `jctl --profile
dev auth token` stores a separate username/token from `jctl --profile prd auth
token`.

## Quick Start

### 1. Initialize Configuration

```bash
jctl config init
```

This creates a default profile in `~/.jctl/config.yaml` and prompts you for a
Jenkins URL, username, and API token.

### 2. Add More Profiles

```bash
jctl config add-profile dev --jenkins-url https://jenkins-dev.example.com
jctl --profile dev auth token

jctl config add-profile stg --jenkins-url https://jenkins-stg.example.com
jctl --profile stg auth token
```

Or run `jctl config init` again — when a config already exists, it adds a new
profile instead of overwriting.

## Example Configuration

```yaml
version: '1.0'
default_profile: production

profiles:
  dev:
    jenkins:
      url: https://jenkins-dev.example.com
      api_version: '2.0'
      verify_ssl: true
      timeout: 30
    output:
      format: table
      color: auto
      pager: false
    ssl:
      verify: true

  stg:
    jenkins:
      url: https://jenkins-stg.example.com
      api_version: '2.0'
      verify_ssl: true
      timeout: 30
    output:
      format: table
      color: auto
      pager: false
    ssl:
      verify: true

  production:
    jenkins:
      url: https://jenkins.example.com
      api_version: '2.0'
      verify_ssl: true
      timeout: 30
    output:
      format: table
      color: auto
      pager: false
    ssl:
      verify: true

defaults:
  timeout: 30
  retry_count: 3
  log_level: INFO
  cache_ttl: 300

aliases:
  deploy: job trigger deploy/release-pipeline
  rollback: job trigger deploy/rollback
  smoke: job trigger qa/smoke-tests
```

## Using Profiles

### Default Profile

```bash
# Uses 'production' (the configured default)
jctl pipeline list
```

### Specific Profile

```bash
jctl --profile dev pipeline list
jctl --profile stg pipeline run deploy/release-pipeline
jctl --profile production pipeline logs deploy/release-pipeline 123
```

The `--profile` flag works with every jctl command.

## Managing Profiles

```bash
# Show full config file
jctl config show

# Show specific key
jctl config get default_profile

# Change default profile
jctl config set default_profile dev

# Update a profile's Jenkins URL
jctl config set dev.jenkins.url https://jenkins-dev-new.example.com

# Add a profile non-interactively
jctl config add-profile uat --jenkins-url https://jenkins-uat.example.com
```

## Authentication Per Profile

Each profile stores its own username/token in the OS keystore:

```bash
jctl --profile dev auth token
jctl --profile stg auth token
jctl --profile production auth token

# Check status
jctl --profile dev auth status
jctl --profile production auth status

# Clear credentials for one profile
jctl --profile dev auth logout
```

## Environment Variables

```bash
# Use dev profile via environment variable
export JCTL_PROFILE=dev

# Override Jenkins URL
export JCTL_JENKINS_URL=https://jenkins-custom.example.com

# Override output format
export JCTL_OUTPUT_FORMAT=json
```

## Shell Aliases for Quick Switching

```bash
alias jctl-dev='jctl --profile dev'
alias jctl-stg='jctl --profile stg'
alias jctl-prd='jctl --profile production'

# Usage
jctl-dev pipeline list
jctl-stg pipeline run deploy/release-pipeline
jctl-prd auth status
```

## Best Practices

1. **Use descriptive profile names** — `dev`, `stg`, `prd` or full names like `development`, `staging`, `production`.
2. **Set a safe default** — many teams default to `dev` to avoid accidentally hitting prod.
3. **Keep SSL verification on in production** — `verify_ssl: true`.
4. **Use separate tokens per environment** — don't reuse production credentials in dev/staging.

## Troubleshooting

### "Profile 'X' not found"

```bash
# See available profiles
jctl config show

# Check default profile
jctl config get default_profile
```

### Wrong Jenkins server

```bash
# Verify which URL a profile points to
jctl --profile dev config get jenkins.url
```

### Authentication issues

```bash
jctl --profile dev auth status
jctl --profile dev auth token   # re-enter credentials
```

## Examples

### Complete Workflow Across Environments

```bash
jctl --profile dev pipeline run deploy/release-pipeline \
  --param environment_name=dev-test \
  --wait

jctl --profile stg pipeline run deploy/release-pipeline \
  --param environment_name=stg-test \
  --wait

jctl --profile production pipeline run deploy/release-pipeline \
  --param environment_name=prd-001 \
  --wait
```

### Status Across All Environments

```bash
for env in dev stg production; do
  echo "=== $env ==="
  jctl --profile $env auth status
  jctl --profile $env pipeline list --limit 5
  echo
done
```
