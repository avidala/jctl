# Using Profiles with API Tokens

This guide shows how to use multiple Jenkins environments with API token authentication (without Okta OAuth).

## Why Use API Tokens?

API tokens are simpler than OAuth and work great when:
- You don't need Okta SSO integration
- You want quick setup without OAuth app configuration
- Your Jenkins instance supports API tokens
- You're working in a local/development environment

## Quick Setup

### 1. Create Profiles (Without Okta)

```bash
# Initialize config if not already done
jctl config init

# Add dev profile (API token only, no Okta)
jctl config add-profile dev \
  --jenkins-url https://jenkins-dev.example.com

# Add staging profile
jctl config add-profile stg \
  --jenkins-url https://jenkins-stg.example.com

# Add production profile
jctl config add-profile prd \
  --jenkins-url https://jenkins.example.com \
  --set-default
```

**Note:** When you omit `--okta-domain` and `--okta-client-id`, the profile is configured for API token authentication only.

### 2. Authenticate Each Profile with API Tokens

```bash
# Authenticate to dev
jctl --profile dev auth token
# Enter your dev Jenkins username and API token

# Authenticate to staging
jctl --profile stg auth token
# Enter your staging Jenkins username and API token

# Authenticate to production
jctl --profile prd auth token
# Enter your production Jenkins username and API token
```

### 3. Start Using

```bash
# Use dev environment
jctl --profile dev pipeline list

# Use staging environment
jctl --profile stg pipeline run deploy/release-pipeline

# Use production environment (default)
jctl pipeline list
```

## Example Configuration

After setup, your `~/.jctl/config.yaml` will look like:

```yaml
version: '1.0'
default_profile: prd

profiles:
  dev:
    jenkins:
      url: https://jenkins-dev.example.com
      api_version: '2.0'
      verify_ssl: true
      timeout: 30
    okta:
      domain: not-configured.okta.com
      client_id: not-configured
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
    okta:
      domain: not-configured.okta.com
      client_id: not-configured
    output:
      format: table
      color: auto
      pager: false
    ssl:
      verify: true

  prd:
    jenkins:
      url: https://jenkins.example.com
      api_version: '2.0'
      verify_ssl: true
      timeout: 30
    okta:
      domain: not-configured.okta.com
      client_id: not-configured
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
  ne: job trigger deploy-staging
  we: job trigger teardown-environment
  drift: job trigger monitor-infrastructure
```

**Note:** The Okta config shows `not-configured` which indicates API token authentication is used.

## How API Token Authentication Works

### Per-Profile Credentials

Each profile stores its own API token credentials in your system keychain:

```bash
# Check authentication status for each profile
jctl --profile dev auth status
jctl --profile stg auth status
jctl --profile prd auth status
```

### Credentials Storage

Credentials are stored securely in your OS keychain:
- **macOS**: Keychain Access
- **Linux**: Secret Service / libsecret
- **Windows**: Windows Credential Manager

Keys are stored per profile:
- `jctl-jenkins-username-{profile}` - Jenkins username for profile
- `jctl-jenkins-token-{profile}` - API token for profile

### Getting Jenkins API Tokens

For each Jenkins environment:

1. Log in to Jenkins web UI
2. Click your name (top right) → Configure
3. Under "API Token" section, click "Add new Token"
4. Give it a name (e.g., "jctl-dev")
5. Click "Generate"
6. Copy the token immediately (it won't be shown again)
7. Use it with `jctl --profile {profile} auth token`

## Common Workflows

### Test Across All Environments

```bash
# 1. Test in dev
jctl --profile dev pipeline run deploy/release-pipeline \
  --param environment_name=dev-test \
  --wait

# 2. If successful, promote to staging
jctl --profile stg pipeline run deploy/release-pipeline \
  --param environment_name=stg-test \
  --wait

# 3. If staging passes, deploy to production
jctl --profile prd pipeline run deploy/release-pipeline \
  --param environment_name=prd-001 \
  --wait
```

### Monitor Different Environments

```bash
# Monitor dev pipeline
jctl --profile dev pipeline logs deploy/release-pipeline --follow

# Check staging status
jctl --profile stg pipeline describe deploy/release-pipeline 123

# List production pipelines
jctl --profile prd pipeline list --filter "deploy-*"
```

### Manage Credentials

```bash
# Re-authenticate a profile
jctl --profile dev auth token

# Check authentication status
jctl --profile dev auth status

# Clear credentials (logout)
jctl --profile dev auth logout
```

## Shell Aliases

Add these to your `~/.bashrc` or `~/.zshrc` for convenience:

```bash
# Profile shortcuts
alias jctl-dev='jctl --profile dev'
alias jctl-stg='jctl --profile stg'
alias jctl-prd='jctl --profile prd'

# Common operations with shortcuts
alias jdev-list='jctl --profile dev pipeline list'
alias jstg-list='jctl --profile stg pipeline list'
alias jprd-list='jctl --profile prd pipeline list'
```

Usage:
```bash
jctl-dev pipeline list
jctl-stg pipeline run deploy/release-pipeline
jctl-prd auth status
```

## Adding Okta Later

If you decide to add Okta OAuth to a profile later:

```bash
# Update profile with Okta settings
jctl config set dev.okta.domain company-dev.okta.com
jctl config set dev.okta.client_id jenkins-cli-dev

# Then you can use OAuth
jctl --profile dev auth login
```

## Switching Between Token and OAuth

Each profile can use either authentication method:

```bash
# Use API token
jctl --profile dev auth token

# Or use OAuth (if Okta is configured)
jctl --profile dev auth login
```

The CLI will try API token first, then OAuth if needed.

## Best Practices

### 1. Use Separate Tokens Per Environment
- Generate different API tokens for dev, stg, and prd
- Don't reuse production tokens in lower environments
- Rotate tokens regularly

### 2. Token Naming Convention
- Use descriptive names: `jctl-dev`, `jctl-stg`, `jctl-prd`
- Include your username: `jctl-dev-avidal`
- Makes it easier to identify in Jenkins

### 3. Security
- Keep tokens secure - they're like passwords
- Don't commit tokens to git
- Use `jctl auth logout` on shared machines
- Set short token expiration in Jenkins if possible

### 4. Profile Organization
- Use clear profile names: `dev`, `stg`, `prd`
- Set production as default for safety
- Document which profile maps to which environment

### 5. Testing Flow
- Always test in dev first
- Promote to staging after dev success
- Only deploy to production after staging validation

## Troubleshooting

### Authentication Failed

If you get "Authentication failed":

1. Check your token is valid:
   ```bash
   jctl --profile dev auth status
   ```

2. Re-authenticate:
   ```bash
   jctl --profile dev auth token
   ```

3. Verify Jenkins URL:
   ```bash
   jctl --profile dev config get jenkins.url
   ```

### Wrong Environment

If commands hit the wrong Jenkins:

1. Always specify `--profile` explicitly
2. Or check/change default profile:
   ```bash
   jctl config get default_profile
   jctl config set default_profile dev
   ```

### Token Expired

Tokens can expire. If you get 401/403 errors:

1. Generate new token in Jenkins
2. Re-run:
   ```bash
   jctl --profile dev auth token
   ```

## Example: Complete Setup Script

```bash
#!/bin/bash
# setup-jctl-profiles.sh

# Initialize
jctl config init

# Create profiles
echo "Setting up dev profile..."
jctl config add-profile dev \
  --jenkins-url https://jenkins-dev.example.com

echo "Setting up staging profile..."
jctl config add-profile stg \
  --jenkins-url https://jenkins-stg.example.com

echo "Setting up production profile..."
jctl config add-profile prd \
  --jenkins-url https://jenkins.example.com \
  --set-default

# Authenticate
echo -e "\n=== Authenticate to DEV ==="
jctl --profile dev auth token

echo -e "\n=== Authenticate to STAGING ==="
jctl --profile stg auth token

echo -e "\n=== Authenticate to PRODUCTION ==="
jctl --profile prd auth token

# Verify
echo -e "\n=== Verification ==="
jctl --profile dev auth status
jctl --profile stg auth status
jctl --profile prd auth status

echo -e "\n✓ Setup complete!"
```

## Summary

- ✅ **Simple Setup** - No OAuth configuration needed
- ✅ **Multiple Environments** - Separate profiles for dev/stg/prd
- ✅ **Independent Credentials** - Each profile has its own token
- ✅ **Secure Storage** - Tokens stored in OS keychain
- ✅ **Easy Switching** - Use `--profile` flag
- ✅ **Works Everywhere** - Profile support in all commands

Using API tokens with profiles gives you a simple, secure way to manage multiple Jenkins environments! 🔑
