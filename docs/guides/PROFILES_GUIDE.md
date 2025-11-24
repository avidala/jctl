# Using Profiles with jctl

jctl supports multiple configuration profiles, allowing you to easily switch between different Jenkins environments (dev, staging, production, etc.).

## Overview

Profiles let you maintain separate configurations for:
- Different Jenkins servers (dev, staging, production)
- Different Okta domains
- Different SSL/TLS settings
- Different output preferences

## Quick Start

### 1. Initialize Configuration

First, create your initial configuration:

```bash
jctl config init
```

This creates a default `production` profile in `~/.jctl/config.yaml`.

### 2. Add More Profiles

Edit your config file to add dev and staging profiles:

```bash
nano ~/.jctl/config.yaml
```

Or use the `jctl config set` command to add profile-specific settings.

## Authentication Options

You can configure profiles with:
1. **API Tokens Only** - Simpler setup, no OAuth configuration needed
2. **Okta OAuth** - Full SSO integration with Okta
3. **Both** - Flexibility to use either method

For API token-only profiles, see [PROFILES_WITH_TOKENS.md](PROFILES_WITH_TOKENS.md).

## Example Configuration

Here's an example `~/.jctl/config.yaml` with dev, stg, and prd profiles:

```yaml
version: '1.0'
default_profile: production

profiles:
  # Development environment
  dev:
    jenkins:
      url: https://jenkins-dev.example.com
      api_version: '2.0'
      verify_ssl: true
      timeout: 30
    okta:
      domain: company-dev.okta.com
      client_id: jenkins-cli-dev
      redirect_uri: http://localhost:8989/callback
      scopes:
        - openid
        - profile
        - email
    output:
      format: table
      color: auto
      pager: false
    ssl:
      verify: true

  # Staging environment
  stg:
    jenkins:
      url: https://jenkins-stg.example.com
      api_version: '2.0'
      verify_ssl: true
      timeout: 30
    okta:
      domain: company-stg.okta.com
      client_id: jenkins-cli-stg
      redirect_uri: http://localhost:8989/callback
      scopes:
        - openid
        - profile
        - email
    output:
      format: table
      color: auto
      pager: false
    ssl:
      verify: true

  # Production environment
  production:
    jenkins:
      url: https://jenkins.example.com
      api_version: '2.0'
      verify_ssl: true
      timeout: 30
    okta:
      domain: company.okta.com
      client_id: jenkins-cli
      redirect_uri: http://localhost:8989/callback
      scopes:
        - openid
        - profile
        - email
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
  ne: job trigger hamc-new-environment
  we: job trigger hamc-wipe-environment
  drift: job trigger hamc-monitor-drift
```

## Using Profiles

### Use Default Profile

By default, jctl uses the profile specified in `default_profile`:

```bash
# Uses 'production' profile (default)
jctl pipeline list
```

### Use Specific Profile

Use the `--profile` flag to specify which profile to use:

```bash
# Use dev profile
jctl --profile dev pipeline list

# Use staging profile
jctl --profile stg pipeline run managed-cloud/hamc-upgrade-pipeline

# Use production profile explicitly
jctl --profile production pipeline logs managed-cloud/hamc-upgrade-pipeline 123
```

### Profile with Any Command

The `--profile` flag works with all jctl commands:

```bash
# List pipelines in dev
jctl --profile dev pipeline list

# Run pipeline in staging
jctl --profile stg pipeline run managed-cloud/hamc-upgrade-pipeline \
  --param environment_name=staging-test

# Check auth status in production
jctl --profile production auth status

# Trigger job in dev
jctl --profile dev job trigger hamc-new-environment \
  --param environment_name=dev-test
```

## Managing Profiles

### View Current Configuration

```bash
# Show full config file
jctl config show

# List all configuration values
jctl config list

# Get specific value
jctl config get default_profile
```

### Modify Profile Settings

Update profile settings using dot notation:

```bash
# Change default profile
jctl config set default_profile dev

# Update dev Jenkins URL
jctl config set dev.jenkins.url https://jenkins-dev-new.example.com

# Update staging Okta domain
jctl config set stg.okta.domain company-staging.okta.com

# Change production output format
jctl config set production.output.format json
```

### Add New Profile

To add a new profile, manually edit the config file or use set commands:

```bash
# Add a new profile by setting its Jenkins URL
jctl config set profiles.uat.jenkins.url https://jenkins-uat.example.com
jctl config set profiles.uat.okta.domain company-uat.okta.com
jctl config set profiles.uat.okta.client_id jenkins-cli-uat
```

## Authentication Per Profile

Each profile can have its own authentication credentials:

### API Token Authentication

Set up API tokens for each environment:

```bash
# Authenticate to dev
jctl --profile dev auth token
# Enter dev username and token

# Authenticate to staging
jctl --profile stg auth token
# Enter staging username and token

# Authenticate to production
jctl --profile production auth token
# Enter production username and token
```

### OAuth Authentication

OAuth tokens are also stored per profile:

```bash
# Login to dev
jctl --profile dev auth login

# Login to staging
jctl --profile stg auth login

# Login to production
jctl --profile production auth login
```

### Check Auth Status

```bash
# Check dev authentication
jctl --profile dev auth status

# Check staging authentication
jctl --profile stg auth status

# Check production authentication
jctl --profile production auth status
```

## Environment Variables

You can override the profile using environment variables:

```bash
# Use dev profile via environment variable
export JCTL_PROFILE=dev
jctl pipeline list  # Uses dev profile

# Override Jenkins URL
export JCTL_JENKINS_URL=https://jenkins-custom.example.com
jctl pipeline list  # Uses custom URL

# Override output format
export JCTL_OUTPUT_FORMAT=json
jctl pipeline list  # Outputs JSON
```

## Shell Aliases for Quick Switching

Add these to your `~/.bashrc` or `~/.zshrc` for quick profile switching:

```bash
# Quick aliases for different environments
alias jctl-dev='jctl --profile dev'
alias jctl-stg='jctl --profile stg'
alias jctl-prd='jctl --profile production'

# Usage:
jctl-dev pipeline list
jctl-stg pipeline run managed-cloud/hamc-upgrade-pipeline
jctl-prd auth status
```

## Best Practices

### 1. **Use Descriptive Profile Names**
   - `dev`, `stg`, `prd` are clear and concise
   - Or use full names: `development`, `staging`, `production`

### 2. **Set Appropriate Default**
   - Set your most-used environment as default
   - For safety, consider making `dev` the default

### 3. **Different Client IDs Per Environment**
   - Use separate Okta client IDs for each environment
   - Examples: `jenkins-cli-dev`, `jenkins-cli-stg`, `jenkins-cli-prod`

### 4. **Verify SSL in Production**
   - Always set `verify_ssl: true` for production
   - You can disable for local dev environments if needed

### 5. **Separate Credentials**
   - Keep separate API tokens for each environment
   - Don't reuse production credentials in dev/staging

### 6. **Use Aliases for Common Operations**
   - Add shortcuts in the `aliases` section
   - Profiles don't affect aliases - they work across all profiles

## Troubleshooting

### Profile Not Found

If you get an error like "Profile 'dev' not found":

1. Check available profiles:
   ```bash
   jctl config show
   ```

2. Verify the profile exists in `~/.jctl/config.yaml`

3. Check for typos in the profile name

### Wrong Jenkins Server

If commands are hitting the wrong Jenkins:

1. Verify you're using the correct profile:
   ```bash
   jctl --profile dev config get jenkins.url
   ```

2. Check the default profile:
   ```bash
   jctl config get default_profile
   ```

3. Always specify `--profile` to be explicit

### Authentication Issues

If authentication fails for a specific profile:

1. Check auth status:
   ```bash
   jctl --profile dev auth status
   ```

2. Re-authenticate:
   ```bash
   jctl --profile dev auth token
   # or
   jctl --profile dev auth login
   ```

3. Verify Jenkins URL is correct:
   ```bash
   jctl --profile dev config get jenkins.url
   ```

## Examples

### Complete Workflow Across Environments

```bash
# 1. Test in dev
jctl --profile dev pipeline run managed-cloud/hamc-upgrade-pipeline \
  --param environment_name=dev-test \
  --wait

# 2. If successful, test in staging
jctl --profile stg pipeline run managed-cloud/hamc-upgrade-pipeline \
  --param environment_name=stg-test \
  --wait

# 3. If staging passes, run in production
jctl --profile production pipeline run managed-cloud/hamc-upgrade-pipeline \
  --param environment_name=prd-001 \
  --wait
```

### Monitor Different Environments

```bash
# Monitor dev
jctl --profile dev pipeline logs managed-cloud/hamc-monitor-drift --follow

# Monitor staging
jctl --profile stg pipeline logs managed-cloud/hamc-monitor-drift --follow

# Monitor production
jctl --profile production pipeline logs managed-cloud/hamc-monitor-drift --follow
```

### Check Status Across All Environments

```bash
# Create a script to check all environments
for env in dev stg production; do
  echo "=== $env ==="
  jctl --profile $env auth status
  jctl --profile $env pipeline list --limit 5
  echo
done
```

## Summary

- ✅ **Multiple Profiles** - Manage dev, stg, prd, and more
- ✅ **Easy Switching** - Use `--profile` flag to switch environments
- ✅ **Separate Auth** - Independent authentication per profile
- ✅ **Profile-Specific Settings** - Different Jenkins URLs, Okta domains, etc.
- ✅ **Default Profile** - Set your most-used environment as default
- ✅ **Environment Variables** - Override profiles via env vars
- ✅ **Works with All Commands** - Profiles work with every jctl command

Now you can safely work with multiple Jenkins environments without mixing up configurations! 🎯
