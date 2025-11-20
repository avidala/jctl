# Profiles Quick Start

Quick reference for using multiple Jenkins environments with jctl.

## Setup (One-Time)

### Option 1: API Token Authentication (Simple)

```bash
# 1. Initialize configuration
jctl config init

# 2. Add dev profile (no Okta needed)
jctl config add-profile dev --jenkins-url https://jenkins-dev.h2oai.com

# 3. Add staging profile
jctl config add-profile stg --jenkins-url https://jenkins-stg.h2oai.com

# 4. Authenticate to each environment with API tokens
jctl --profile dev auth token
jctl --profile stg auth token
jctl --profile production auth token
```

### Option 2: With Okta OAuth

```bash
# 1. Initialize configuration
jctl config init

# 2. Add dev profile with Okta
jctl config add-profile dev \
  --jenkins-url https://jenkins-dev.h2oai.com \
  --okta-domain h2oai-dev.okta.com \
  --okta-client-id jenkins-cli-dev

# 3. Add staging profile with Okta
jctl config add-profile stg \
  --jenkins-url https://jenkins-stg.h2oai.com \
  --okta-domain h2oai-stg.okta.com \
  --okta-client-id jenkins-cli-stg

# 4. Authenticate (can use token OR OAuth)
jctl --profile dev auth token  # API token
jctl --profile dev auth login  # OAuth
```

## Daily Usage

```bash
# Use dev environment
jctl --profile dev pipeline list
jctl --profile dev pipeline run managed-cloud/hamc-upgrade-pipeline

# Use staging environment
jctl --profile stg pipeline list
jctl --profile stg pipeline logs managed-cloud/hamc-upgrade-pipeline 123

# Use production environment (default)
jctl pipeline list
jctl --profile production pipeline run managed-cloud/hamc-upgrade-pipeline
```

## Shell Aliases (Optional)

Add to `~/.bashrc` or `~/.zshrc`:

```bash
alias jctl-dev='jctl --profile dev'
alias jctl-stg='jctl --profile stg'
alias jctl-prd='jctl --profile production'
```

Then use:

```bash
jctl-dev pipeline list
jctl-stg pipeline run managed-cloud/hamc-upgrade-pipeline
jctl-prd auth status
```

## Common Tasks

### Check which profile you're using

```bash
jctl config get default_profile
```

### List all profiles

```bash
jctl config show
```

### Change default profile

```bash
jctl config set default_profile dev
```

### Run pipeline across all environments

```bash
# Test in dev first
jctl --profile dev pipeline run my-pipeline --wait

# If successful, run in staging
jctl --profile stg pipeline run my-pipeline --wait

# If staging passes, run in production
jctl --profile production pipeline run my-pipeline --wait
```

## Learn More

- [PROFILES_WITH_TOKENS.md](PROFILES_WITH_TOKENS.md) - Complete guide for API token authentication
- [PROFILES_GUIDE.md](PROFILES_GUIDE.md) - Full profile configuration guide
