# Config Init Workflow

The `jctl config init` command configures everything in one place: profile
name, Jenkins URL, and Jenkins API token credentials.

## Interactive Flow

```
$ jctl config init

Initializing jctl configuration...

Profile Setup:
Profile name (production): dev

Jenkins URL (https://jenkins.example.com): https://jenkins-dev.example.com

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

That's it — profile created, Jenkins URL configured, and authenticated, all in
one flow.

## What Gets Configured

```yaml
version: '1.0'
default_profile: dev

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

defaults:
  timeout: 30
  retry_count: 3
  log_level: INFO
  cache_ttl: 300
```

The Jenkins username and API token are stored separately in the OS keystore,
not in the YAML file.

## Reinitializing

To reinitialize configuration (e.g., to change the Jenkins URL):

```bash
jctl config init --force
```

This will prompt to overwrite the existing config.

## Multiple Profiles

After initial setup, add more profiles:

```bash
# Add dev profile
jctl config add-profile dev --jenkins-url https://jenkins-dev.example.com

# Add staging profile as default
jctl config add-profile stg \
  --jenkins-url https://jenkins-stg.example.com \
  --set-default
```

Each profile stores its own credentials in the keystore — authenticate each
with `jctl --profile <name> auth token`.

## Complete Multi-Environment Setup

```bash
# 1. Setup dev environment
jctl config init
# Profile name: dev
# Jenkins URL: https://jenkins-dev.example.com
# Username: avidal
# Token: <your-dev-token>

# 2. Add staging
jctl config add-profile stg --jenkins-url https://jenkins-stg.example.com
jctl --profile stg auth token

# 3. Add production as the default
jctl config add-profile prd --jenkins-url https://jenkins.example.com --set-default
jctl --profile prd auth token

# 4. Use them
jctl --profile dev pipeline list
jctl --profile stg pipeline run deploy/release-pipeline
jctl pipeline list  # uses prd (default)
```
