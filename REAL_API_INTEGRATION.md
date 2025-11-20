# Real Jenkins API Integration

## ✅ What's Now Working

The following commands now connect to your **real Jenkins instance** instead of using mock data:

### 1. Pipeline List (`jctl pipeline list`)
- Fetches actual jobs from Jenkins API
- Shows real build statuses (SUCCESS, FAILED, RUNNING, ABORTED)
- Displays actual timestamps and durations
- Supports filtering and status filters

### 2. Pipeline Describe (`jctl pipeline describe <job> <build>`)
- Gets real build information from Jenkins
- Shows pipeline stages with actual status
- Displays real durations and timestamps
- Works with workflow API for stage details

### 3. Pipeline Cancel (`jctl pipeline cancel <job> <build>`)
- Actually stops running builds in Jenkins
- Uses Jenkins stop build API
- Requires confirmation before canceling

## Authentication

All commands now use the authentication system:
- **API Token** (recommended for testing)
- **OAuth** (when configured)

The helper function `get_jenkins_client()` automatically:
1. Checks for API token authentication first
2. Falls back to OAuth if available
3. Shows helpful error if neither is configured

## Testing the Integration

### Step 1: Configure Your Jenkins URL

Make sure your config points to the right Jenkins:

```bash
jctl config get production.jenkins.url
```

Expected: `https://jenkins-stg.managed-cloud.h2o.dev`

If not set correctly:
```bash
jctl config set production.jenkins.url "https://jenkins-stg.managed-cloud.h2o.dev"
```

### Step 2: Get Your Jenkins API Token

1. Go to https://jenkins-stg.managed-cloud.h2o.dev/
2. Log in with your H2O.ai Okta credentials
3. Click your name (top right) → **Configure**
4. Scroll to **"API Token"** section
5. Click **"Add new Token"**
6. Name it: `jctl-cli`
7. Click **"Generate"**
8. **Copy the token immediately!**

### Step 3: Configure API Token in jctl

```bash
jctl auth token
```

When prompted:
- **Username**: your.email@h2o.ai
- **API Token**: [paste the token you copied]

You should see:
```
✓ API token configured successfully!
Username: your.email@h2o.ai

You can now use Jenkins commands:
  jctl pipeline list
  jctl job trigger <job-name>
```

### Step 4: Test Pipeline List

```bash
jctl pipeline list
```

**Expected Output:**
```
Using API token authentication as your.email@h2o.ai
Fetching pipelines from Jenkins...
Found X pipeline(s)

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Name                       ┃ Status  ┃ Last Run        ┃ Duration ┃ Build Number ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ hamc-new-environment       │ SUCCESS │ 2025-11-19 14:23│ 12m 34s  │ 142          │
│ hamc-wipe-environment      │ FAILED  │ 2025-11-19 10:15│ 8m 12s   │ 67           │
│ hamc-monitor-drift         │ RUNNING │ 2025-11-19 15:45│ Running  │ 89           │
... (more jobs)
└────────────────────────────┴─────────┴─────────────────┴──────────┴──────────────┘
```

**Filter by name:**
```bash
jctl pipeline list --filter hamc
```

**Filter by status:**
```bash
jctl pipeline list --status SUCCESS
jctl pipeline list --status FAILED
jctl pipeline list --status RUNNING
```

**Limit results:**
```bash
jctl pipeline list --limit 10
```

**JSON output:**
```bash
jctl pipeline list --output json
```

### Step 5: Test Pipeline Describe

Pick a job and build number from the list above:

```bash
jctl pipeline describe hamc-new-environment 142
```

**Expected Output:**
```
Using API token authentication as your.email@h2o.ai
Fetching build info for hamc-new-environment #142...

hamc-new-environment #142

                      Pipeline Stages
┏━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Stage                 ┃ Status        ┃ Duration ┃
┡━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ Checkout              │ ✓ SUCCESS     │ 12s      │
│ Validate Parameters   │ ✓ SUCCESS     │ 3s       │
│ Create Environment    │ ✓ SUCCESS     │ 8m 45s   │
│ Deploy Services       │ ✓ SUCCESS     │ 3m 22s   │
│ Run Tests             │ ✓ SUCCESS     │ 1m 12s   │
│ Send Notification     │ ✓ SUCCESS     │ 2s       │
└───────────────────────┴───────────────┴──────────┘

Overall Status: ✓ SUCCESS
Total Duration: 12m 34s
Result: SUCCESS
Started At: 2025-11-19 14:23:15
```

### Step 6: Test Pipeline Cancel (Optional - be careful!)

**⚠️ WARNING**: This will actually stop a running build!

Find a running build first:
```bash
jctl pipeline list --status RUNNING
```

Then cancel it (requires confirmation):
```bash
jctl pipeline cancel hamc-monitor-drift 89
```

You'll be prompted:
```
Are you sure you want to cancel this pipeline? [y/N]:
```

If you confirm with `y`:
```
Using API token authentication as your.email@h2o.ai
Cancelling: hamc-monitor-drift #89
Stopping pipeline...
✓ Pipeline hamc-monitor-drift #89 cancelled
```

You can add a reason for audit:
```bash
jctl pipeline cancel hamc-test-job 10 --reason "Testing jctl cancel command"
```

## Troubleshooting

### Error: "Not authenticated"

```
Error: Not authenticated

Please authenticate first:
  • jctl auth token - Quick setup with API token
  • jctl auth login - OAuth SSO authentication
```

**Solution**: Run `jctl auth token` and configure your API token

### Error: "401 Unauthorized"

This means your API token is invalid or expired.

**Solution**:
1. Check your token in Jenkins (might be revoked)
2. Generate a new token
3. Update jctl:
   ```bash
   jctl auth logout
   jctl auth token
   ```

### Error: "403 Forbidden"

Your Jenkins user doesn't have permission to access that resource.

**Solution**:
1. Verify you can see the job in Jenkins web UI
2. Contact Jenkins admin if you need permissions

### Error: "404 Not Found"

The job or build doesn't exist.

**Solution**:
- Check the job name spelling (case-sensitive!)
- Verify the build number exists
- List available jobs: `jctl pipeline list`

### Error: "Connection failed"

Can't reach Jenkins server.

**Solution**:
1. Check if you're on VPN (if required)
2. Verify Jenkins URL: `jctl config get production.jenkins.url`
3. Test connectivity: `curl -I https://jenkins-stg.managed-cloud.h2o.dev/`

### No Pipelines Found

If `jctl pipeline list` returns empty:

**Check:**
1. Are you authenticated? `jctl auth status`
2. Do you have access to any jobs in Jenkins web UI?
3. Try without filters: `jctl pipeline list --limit 50`

### SSL Certificate Errors

If you see SSL verification errors:

**Temporary workaround** (not recommended for production):
```bash
jctl config set production.jenkins.verify_ssl false
```

**Better solution**: Ensure proper SSL certificates are in place

## What's Different from Mock Data

| Aspect | Mock Data (Before) | Real API (Now) |
|--------|-------------------|----------------|
| **Data Source** | Hardcoded in `mock.py` | Live from Jenkins API |
| **Job Names** | Only 6 HAMC jobs | All jobs you have access to |
| **Build Numbers** | Fake (142, 67, etc.) | Real build numbers |
| **Timestamps** | Static fake times | Actual build times |
| **Durations** | Hardcoded values | Real execution times |
| **Status** | Fake statuses | Live build status |
| **Pipeline Stages** | Fake stage info | Real pipeline stages from Workflow API |
| **Cancel Action** | Simulated (did nothing) | Actually stops builds |

## Commands Still Using Mock/Stub

These commands still need implementation:
- `jctl pipeline search` - Search for pipelines
- `jctl pipeline run` - Execute a pipeline
- `jctl pipeline pause` - Pause at input step
- `jctl pipeline resume` - Resume paused pipeline
- `jctl pipeline replay` - Replay with modifications
- `jctl pipeline restart` - Restart from beginning
- `jctl pipeline validate` - Validate configuration
- `jctl job *` - All job commands (trigger, logs, etc.)

## Next Steps

1. **Test the integration** with your staging Jenkins
2. **Report any issues** you encounter
3. **Let me know** if you want me to implement more commands (job trigger, logs, etc.)

## Example Workflow

Here's a typical workflow you can test:

```bash
# 1. Configure and authenticate
jctl config init
jctl auth token

# 2. List all HAMC pipelines
jctl pipeline list --filter hamc

# 3. Get details on the latest new-environment build
jctl pipeline describe hamc-new-environment 142

# 4. Check for running jobs
jctl pipeline list --status RUNNING

# 5. Get JSON output for scripting
jctl pipeline list --output json --filter hamc | jq '.[] | {name, status, build_number}'
```

## Success! 🎉

You're now using **real Jenkins API integration** with secure authentication!

The CLI is fetching live data from your Jenkins instance and can actually control builds.
