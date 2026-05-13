# jctl Quick Start Guide

Get up and running with jctl in under 2 minutes!

## Initial Setup

```bash
# Install jctl
cd cli/jenkins
pip install -e ".[dev]"

# One command to set up everything
jctl config init

# Follow the prompts:
# - Profile name: dev (or stg, prd, production, etc.)
# - Auth method: 1 (API Token)
# - Jenkins URL: https://jenkins-dev.example.com
# - Username: your-username
# - API Token: your-token

# ✓ Done! You're authenticated and ready to use jctl
```

## Enable Tab Completion (Optional)

```bash
# Automatic installation
jctl completion --install
source ~/.zshrc

# Now you have tab completion!
jctl pipe<Tab>  # completes to 'jctl pipeline'
```

## Common Commands

### List Pipelines

```bash
jctl pipeline list
jctl pipeline list --filter "deploy-*"
jctl pipeline list --folder deploy
```

### Run a Pipeline

```bash
# Basic run
jctl pipeline run deploy/release-pipeline

# With parameters
jctl pipeline run deploy/release-pipeline \
  --param environment_name=dev-test \
  --param region=us-east-1

# Run and wait for completion
jctl pipeline run deploy/release-pipeline \
  --param environment_name=dev-test \
  --wait
```

### View Logs

```bash
# View latest build logs
jctl pipeline logs deploy/release-pipeline

# View specific build
jctl pipeline logs deploy/release-pipeline 123

# Stream logs in real-time
jctl pipeline logs deploy/release-pipeline --follow
```

### Check Pipeline Status

```bash
# Detailed pipeline information
jctl pipeline describe deploy/release-pipeline 123
```

### Cancel a Running Pipeline

```bash
jctl pipeline cancel deploy/release-pipeline 123
```

## Working with Multiple Environments

### Setup Additional Profiles

**Option 1: Using `jctl config init` (Interactive)**

```bash
# Add staging profile (config already exists, so it adds a profile)
jctl config init
# Profile name: stg
# Auth method: 1 (API Token)
# Jenkins URL: https://jenkins-stg.example.com
# Username & token
# Set as default? [y/n]: n

# Add production profile
jctl config init
# Profile name: prd
# Auth method: 1
# Jenkins URL: https://jenkins.example.com
# Username & token
# Set as default? [y/n]: y
```

**Option 2: Using `jctl config add-profile` (Quick)**

```bash
# Add staging
jctl config add-profile stg --jenkins-url https://jenkins-stg.example.com
jctl --profile stg auth token

# Add production
jctl config add-profile prd --jenkins-url https://jenkins.example.com --set-default
jctl --profile prd auth token
```

### Use Different Profiles

```bash
# Use dev
jctl --profile dev pipeline list

# Use staging
jctl --profile stg pipeline run deploy/release-pipeline

# Use production (default)
jctl pipeline list
```

### Shell Aliases (Optional)

```bash
# Add to ~/.zshrc
alias jdev='jctl --profile dev'
alias jstg='jctl --profile stg'
alias jprd='jctl --profile prd'

# Then use:
jdev pipeline list
jstg pipeline run deploy/release-pipeline
jprd auth status
```

## Typical Workflow

```bash
# 1. List available pipelines
jctl pipeline list --filter "deploy-*"

# 2. Run pipeline in dev
jctl --profile dev pipeline run deploy/release-pipeline \
  --param environment_name=dev-test \
  --wait

# 3. If successful, run in staging
jctl --profile stg pipeline run deploy/release-pipeline \
  --param environment_name=stg-test \
  --wait

# 4. If staging passes, run in production
jctl --profile prd pipeline run deploy/release-pipeline \
  --param environment_name=prd-001 \
  --wait

# 5. Monitor logs
jctl --profile prd pipeline logs deploy/release-pipeline --follow
```

## Checking Status

```bash
# Auth status
jctl auth status

# Show current config
jctl config show

# List all profiles
jctl config list

# Get specific config value
jctl config get default_profile
```

## Troubleshooting

### Authentication Failed

```bash
# Re-authenticate
jctl auth token

# Check status
jctl auth status
```

### Wrong Profile

```bash
# Check default profile
jctl config get default_profile

# Change default
jctl config set default_profile dev

# Or always specify explicitly
jctl --profile dev pipeline list
```

### Can't Find Pipeline

```bash
# List all pipelines to find the correct name
jctl pipeline list

# Search for specific pipeline
jctl pipeline list --filter "upgrade"
```

## Tips

1. **Use tab completion** - Makes commands much faster
2. **Always test in dev first** - Before staging or production
3. **Use `--wait` flag** - To monitor pipeline completion
4. **Use `--follow` for logs** - Real-time log streaming
5. **Set up profiles** - Easier to switch between environments

## Next Steps

- [PROFILES_GUIDE.md](PROFILES_GUIDE.md) - Detailed profile setup
- [COMPLETION_GUIDE.md](COMPLETION_GUIDE.md) - Tab completion setup
- [README.md](README.md) - Full command reference

## Complete Example: New Environment Setup

```bash
# 1. Initialize jctl with dev profile
jctl config init
# Profile: dev
# Jenkins URL: https://jenkins-dev.example.com
# Username & token

# 2. Add other environments
jctl config add-profile stg --jenkins-url https://jenkins-stg.example.com
jctl --profile stg auth token

jctl config add-profile prd --jenkins-url https://jenkins.example.com --set-default
jctl --profile prd auth token

# 3. Enable completion
jctl completion --install
source ~/.zshrc

# 4. Set up aliases
cat >> ~/.zshrc << 'EOF'
alias jdev='jctl --profile dev'
alias jstg='jctl --profile stg'
alias jprd='jctl --profile prd'
EOF
source ~/.zshrc

# 5. Start using jctl!
jdev pipeline list
jstg pipeline run deploy/release-pipeline --param env=stg-test --wait
jprd pipeline list --filter "deploy-*"
```

You're all set! 🚀
