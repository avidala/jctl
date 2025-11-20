# Config Init Workflow

The `jctl config init` command provides a streamlined setup that configures everything in one place: profile name, Jenkins URL, authentication method, and credentials.

## Interactive Flow

### Option 1: API Token Authentication (Recommended)

This is the simplest and most common flow. Everything is configured in one session:

```
$ jctl config init

Initializing jctl configuration...

Profile Setup:
Profile name (production): dev

Choose authentication method:
  1. API Token - Simple, uses Jenkins username and API token
  2. Okta OAuth - SSO integration with Okta

Authentication method [1/2/token/okta] (1): 1

Jenkins URL (https://jenkins.h2oai.com): https://jenkins-dev.h2oai.com

✓ Configuration saved to: /Users/avnervidal/.jctl/config.yaml
✓ Profile 'dev' created and set as default

Authentication Setup:
Let's set up your Jenkins API token now.

Jenkins username: avidal
Jenkins API token (hidden): ●●●●●●●●●●●●

✓ API token saved securely

You're all set! Try these commands:
  jctl pipeline list
  jctl pipeline run <pipeline-name>

Or use explicit profile:
  jctl --profile dev pipeline list
```

**That's it!** Profile created, Jenkins URL configured, and authenticated - all in one flow!

### Option 2: Okta OAuth Authentication

For organizations using Okta SSO:

```
$ jctl config init

Initializing jctl configuration...

Profile Setup:
Profile name (production): production

Choose authentication method:
  1. API Token - Simple, uses Jenkins username and API token
  2. Okta OAuth - SSO integration with Okta

Authentication method [1/2/token/okta] (1): 2

Jenkins URL (https://jenkins.h2oai.com): https://jenkins.h2oai.com

Okta OAuth Configuration:
Okta domain (h2oai.okta.com): h2oai.okta.com
Okta client ID (jenkins-cli): jenkins-cli

Verify SSL certificates? [y/n] (y): y

✓ Configuration saved to: /Users/avnervidal/.jctl/config.yaml
✓ Profile 'production' created and set as default

Next steps:
  1. Authenticate with API token: jctl auth token
  2. Or authenticate with Okta OAuth: jctl auth login

  Then start using jctl:
    jctl pipeline list
    jctl pipeline run <pipeline-name>
```

## Input Options

The authentication method prompt accepts:
- `1` or `token` - For API token authentication
- `2` or `okta` - For Okta OAuth authentication

## What Gets Configured

### API Token Profile

When you choose API token (option 1), the config looks like:

```yaml
version: '1.0'
default_profile: production

profiles:
  production:
    jenkins:
      url: https://jenkins-dev.h2oai.com
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
  ne: job trigger hamc-new-environment
  we: job trigger hamc-wipe-environment
  drift: job trigger hamc-monitor-drift
```

### Okta OAuth Profile

When you choose Okta OAuth (option 2), the config includes your Okta settings:

```yaml
version: '1.0'
default_profile: production

profiles:
  production:
    jenkins:
      url: https://jenkins.h2oai.com
      api_version: '2.0'
      verify_ssl: true
      timeout: 30
    okta:
      domain: h2oai.okta.com
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

# ... rest of config
```

## After Initialization

### API Token Authentication

```bash
# Authenticate with your Jenkins username and API token
jctl auth token

# Then use jctl
jctl pipeline list
jctl pipeline run managed-cloud/hamc-upgrade-pipeline
```

### Okta OAuth Authentication

```bash
# Option A: Use API token
jctl auth token

# Option B: Use Okta OAuth
jctl auth login

# Then use jctl
jctl pipeline list
jctl pipeline run managed-cloud/hamc-upgrade-pipeline
```

## Reinitializing

To reinitialize configuration (e.g., to change auth method):

```bash
# This will prompt to overwrite existing config
jctl config init --force
```

## Multiple Profiles

After initial setup, you can add more profiles with different auth methods:

```bash
# Add dev profile with API token only
jctl config add-profile dev --jenkins-url https://jenkins-dev.h2oai.com

# Add staging profile with Okta
jctl config add-profile stg \
  --jenkins-url https://jenkins-stg.h2oai.com \
  --okta-domain h2oai-stg.okta.com \
  --okta-client-id jenkins-cli-stg
```

## Best Practices

1. **Choose API Token for simplicity** - Easiest to set up, works everywhere
2. **Choose Okta OAuth for SSO** - Better for organizations with SSO policies
3. **Test with dev first** - Initialize with dev environment to test
4. **Use profiles** - Set up multiple environments (dev/stg/prd) after init

## Troubleshooting

### Wrong Auth Method?

If you picked the wrong authentication method:

```bash
# Reinitialize
jctl config init --force

# Choose the correct option this time
```

### Need Both Auth Methods?

You can add Okta configuration to an API token profile later:

```bash
# Update existing profile with Okta settings
jctl config set production.okta.domain h2oai.okta.com
jctl config set production.okta.client_id jenkins-cli
```

### Want to Skip Prompts?

Use `jctl config add-profile` for non-interactive profile creation:

```bash
# Non-interactive profile creation
jctl config add-profile production \
  --jenkins-url https://jenkins.h2oai.com
```

## Complete Multi-Environment Setup

Here's how to set up dev, staging, and production in one go:

```bash
# 1. Setup dev environment
jctl config init
# Profile name: dev
# Auth method: 1 (API Token)
# Jenkins URL: https://jenkins-dev.h2oai.com
# Username: avidal
# Token: <your-dev-token>

# 2. Add staging
jctl config add-profile stg --jenkins-url https://jenkins-stg.h2oai.com
jctl --profile stg auth token
# Username: avidal
# Token: <your-stg-token>

# 3. Add production
jctl config add-profile prd --jenkins-url https://jenkins.h2oai.com --set-default
jctl --profile prd auth token
# Username: avidal
# Token: <your-prd-token>

# 4. Use them!
jctl --profile dev pipeline list
jctl --profile stg pipeline run managed-cloud/hamc-upgrade-pipeline
jctl pipeline list  # Uses prd (default)
```

## Key Improvements

The new init flow:
- ✅ **One place for everything** - Profile name, URL, and auth in one session
- ✅ **Immediate authentication** - Set up token right away for API token auth
- ✅ **No unnecessary prompts** - Removed output format and SSL prompts for token auth
- ✅ **Clear profile naming** - Choose your own profile name (dev, stg, prd, etc.)
- ✅ **Ready to use** - Fully configured and authenticated when init completes
- ✅ **Conditional prompts** - Only asks for Okta if using OAuth

This makes initial setup much clearer and faster! 🚀
