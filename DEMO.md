# jctl Demo Mode

The CLI is now running in **demo mode** with mock data! This lets you see how all the commands work without connecting to a real Jenkins server.

## ✅ Working Commands

### Pipeline Commands

#### List Pipelines
```bash
# List all pipelines
jctl pipeline list

# Filter by name
jctl pipeline list --filter "new"

# Filter by status
jctl pipeline list --status RUNNING
jctl pipeline list --status FAILED

# Limit results
jctl pipeline list --limit 3

# JSON output
jctl --output json pipeline list

# YAML output
jctl --output yaml pipeline list
```

#### Describe Pipeline (with stages!)
```bash
# Show detailed pipeline with stage breakdown
jctl pipeline describe hamc-new-environment 142

# This shows:
# - Overall status
# - Each stage with status icons (✓ ✗ ⟳ ⋯ ⏸)
# - Duration per stage
# - Total duration
```

#### Cancel Pipeline
```bash
# Cancel with confirmation
jctl pipeline cancel hamc-wipe-environment 89

# Cancel with reason (for audit logs)
jctl pipeline cancel hamc-wipe-environment 89 --reason "Wrong account selected"

# Skip confirmation (use --yes flag)
echo y | jctl pipeline cancel hamc-backup-check 234
```

### Config Commands (Fully Working!)

```bash
# Show configuration
jctl config show

# List all config
jctl config list

# Get specific value
jctl config get jenkins.url
jctl config get defaults.timeout

# Set value
jctl config set defaults.log_level DEBUG

# JSON output
jctl --output json config list
```

## 🎨 Output Formats

All commands support multiple output formats:

```bash
# Table format (default - beautiful!)
jctl pipeline list

# JSON format (for scripts/automation)
jctl --output json pipeline list

# YAML format
jctl --output yaml pipeline list

# Plain text (for simple parsing)
jctl --output plain pipeline list
```

## 📊 Demo Data

The mock data includes:

**6 Sample Pipelines:**
- hamc-new-environment (SUCCESS, build #142)
- hamc-wipe-environment (RUNNING, build #89)
- hamc-backup-check (FAILED, build #234)
- hamc-monitor-drift (SUCCESS, build #156)
- hamc-new-aws-account (SUCCESS, build #78)
- hamc-pause-environments (ABORTED, build #45)

**Pipeline Stages:**
Each pipeline has 5 stages showing different states:
- ✓ Completed stages (SUCCESS)
- ⟳ Running stages (IN_PROGRESS)
- ⋯ Pending stages (NOT_EXECUTED)
- ✗ Failed stages (FAILED)
- ⏸ Paused stages (PAUSED)

## 🎯 Real-World Usage Examples

### Scenario 1: Find Running Pipelines
```bash
jctl pipeline list --status RUNNING
```

### Scenario 2: Check Pipeline Details
```bash
# Find the pipeline
jctl pipeline list --filter "environment"

# Get details with stages
jctl pipeline describe hamc-new-environment 142
```

### Scenario 3: Cancel Stuck Pipeline
```bash
# List running pipelines
jctl pipeline list --status RUNNING

# Cancel with reason
jctl pipeline cancel hamc-wipe-environment 89 \
  --reason "Pipeline stuck, restarting"
```

### Scenario 4: Export Data for Reporting
```bash
# Get all failed pipelines in JSON
jctl --output json pipeline list --status FAILED > failed-pipelines.json

# Get specific pipeline details in YAML
jctl --output yaml pipeline describe hamc-backup-check 234 > pipeline-234.yaml
```

### Scenario 5: Filter and Limit
```bash
# Find specific pipelines
jctl pipeline list --filter "hamc-new" --limit 2

# Get successful pipelines only
jctl pipeline list --status SUCCESS
```

## 🚧 Stub Commands (Not Yet Implemented)

These show the structure but don't execute yet:

```bash
# Auth commands
jctl auth login
jctl auth status
jctl auth logout

# Job commands
jctl job trigger hamc-new-environment --param env=test
jctl job status hamc-new-environment
jctl job logs hamc-new-environment-142 --follow

# Other pipeline commands
jctl pipeline pause hamc-monitor-drift 156
jctl pipeline resume hamc-monitor-drift 156
jctl pipeline replay hamc-new-environment 142
jctl pipeline restart hamc-backup-check 234
jctl pipeline validate hamc-new-environment
```

## 🔮 Next Steps

To make these stub commands work, we need to implement:

1. **Okta SSO Authentication** - OAuth 2.0 flow for secure login
2. **Connect to Real Jenkins** - Wire commands to the Jenkins API client
3. **Token Management** - Secure token storage and refresh

For now, enjoy the demo mode to see the beautiful CLI in action!

## 💡 Tips

**Beautiful Terminal:**
- The CLI uses Rich library for beautiful output
- Tables automatically adjust to terminal width
- Colors help you quickly spot status (green=success, red=failed, yellow=running)

**Scriptable:**
- JSON/YAML output for automation
- Exit codes indicate success/failure
- Filters and limits for precise queries

**Safe:**
- Confirmation prompts for dangerous operations
- Audit logging with --reason flags
- Dry-run modes (coming soon)

**Fast:**
- Alias support (defined in config)
- Command shortcuts
- Tab completion (can be added)

Try it out and see how much easier Jenkins management can be from the terminal!
