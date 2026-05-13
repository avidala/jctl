# Jenkins API Token Authentication Guide

## Overview

`jctl` authenticates to Jenkins using a Jenkins API token. The token is sent
as HTTP Basic auth on every request and stored locally in your OS keystore.

## Getting Your Jenkins API Token

### Step 1: Log into Jenkins

Navigate to your Jenkins instance in a browser and log in normally (Jenkins
may delegate this to your IdP — that part is outside of jctl's scope).

### Step 2: Navigate to Your User Profile

1. Click on your **username** in the top-right corner of the Jenkins interface
2. Select **"Configure"** from the dropdown menu

This takes you to your personal user configuration page.

### Step 3: Generate API Token

1. Scroll down to the **"API Token"** section
2. Click **"Add new Token"**
3. Enter a descriptive name for the token:
   - Examples: `jctl-cli`, `laptop-automation`, `local-dev`
   - This helps you identify what the token is used for later
4. Click **"Generate"**
5. **IMPORTANT**: Copy the token immediately!
   - Jenkins will only show it once
   - If you lose it, you'll need to generate a new one

### Step 4: Store Token Securely

The token is a long alphanumeric string like:
```
11a1b2c3d4e5f67890abcdef1234567890
```

**Never share this token or commit it to version control!**

## Using the API Token with jctl

### Interactive Setup (Recommended)

Run the token configuration command:

```bash
jctl auth token
```

You'll see prompts like this:

```
Jenkins API Token Authentication

You can get your API token from Jenkins:
  1. Log into Jenkins
  2. Click your name (top right) → Configure
  3. Scroll to 'API Token' → Add new Token
  4. Copy the generated token

Jenkins username (email): your.email@example.com
Jenkins API token: [hidden input]

✓ API token configured successfully!
Username: your.email@example.com

You can now use Jenkins commands:
  jctl pipeline list
  jctl job trigger <job-name>
```

The token is securely stored in your OS keychain:
- **macOS**: Keychain Services
- **Linux**: Secret Service (gnome-keyring/KWallet)
- **Windows**: Windows Credential Manager

### Command-line Setup

You can also provide credentials directly:

```bash
jctl auth token --username your.email@example.com --token 11a1b2c3d4e5f67890abcdef1234567890
```

**Warning**: The token will be visible in your shell history. Interactive mode is safer.

## Verifying Authentication

Check your authentication status:

```bash
jctl auth status
```

Expected output:

```
Authentication Status

            Jenkins API Token
┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Property ┃ Value                     ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Status   │ ✓ Configured              │
│ Username │ your.email@example.com         │
│ Has Token│ ✓                         │
└──────────┴───────────────────────────┘
```

You can also get JSON output:

```bash
jctl auth status --output json
```

## Using jctl with API Token

Once configured, all Jenkins commands will automatically use your API token:

```bash
# List all pipelines
jctl pipeline list

# Get pipeline details
jctl pipeline describe deploy-staging 142

# Trigger a job
jctl job trigger deploy-staging

# Cancel a running build
jctl pipeline cancel monitor-infrastructure 55

# View job logs
jctl job logs backup-check 10
```

The API token is automatically included in requests to Jenkins.

## Managing API Tokens

### Viewing Current Token

Check which username is configured:

```bash
jctl auth status
```

### Updating Token

To change your token (e.g., if you regenerated it):

```bash
jctl auth token
```

If a token is already configured, you'll see:

```
API token already configured!
Run 'jctl auth status' to see details
Run 'jctl auth logout' to clear and reconfigure
```

Clear the old token first:

```bash
jctl auth logout
jctl auth token
```

### Revoking Tokens in Jenkins

To revoke a token you no longer use:

1. Log into Jenkins web interface
2. Click your username → **Configure**
3. Scroll to **"API Token"** section
4. Find the token by name
5. Click **"Revoke"** next to it

After revoking, that token will immediately stop working.

### Clearing Local Token

Remove the token from your local keychain:

```bash
jctl auth logout
```

This clears the stored API token from the OS keystore.

## Security Best Practices

### DO ✅

- **Use descriptive token names** - "jctl-macbook-pro" is better than "token1"
- **Rotate tokens periodically** - Generate new tokens every few months
- **Revoke unused tokens** - Clean up old tokens you're no longer using
- **Use separate tokens per device** - One for laptop, one for server, etc.
- **Store in OS keychain** - Let jctl handle secure storage

### DON'T ❌

- **Don't share tokens** - Each person should use their own
- **Don't commit tokens** - Keep them out of git repositories
- **Don't use same token everywhere** - Use different tokens for different purposes
- **Don't paste tokens in Slack** - Even in DMs
- **Don't hardcode tokens** - Let jctl store them securely

## Troubleshooting

### "401 Unauthorized" Errors

**Cause**: Token is invalid or revoked

**Solution**:
1. Log into Jenkins web interface
2. Check if the token still exists (Configure → API Token)
3. If revoked, generate a new one
4. Update jctl:
   ```bash
   jctl auth logout
   jctl auth token
   ```

### "403 Forbidden" Errors

**Cause**: Your Jenkins user lacks permissions

**Solution**:
1. Verify you can access the resource in Jenkins web interface
2. Contact Jenkins admin if you need additional permissions
3. Check if the job/pipeline exists and you have access

### Token Not Found

**Cause**: Keychain access denied or token not stored

**Solution**:
1. Try storing the token again:
   ```bash
   jctl auth logout
   jctl auth token
   ```
2. On macOS, check Keychain Access app:
   - Look for "jctl" service
   - Ensure "jenkins_token" and "jenkins_username" entries exist
3. On Linux, ensure Secret Service is available:
   ```bash
   apt-get install gnome-keyring  # Ubuntu/Debian
   yum install gnome-keyring      # RHEL/CentOS
   ```

### "Connection Refused" Errors

**Cause**: Can't reach Jenkins server

**Solution**:
1. Check if you're on VPN (if required)
2. Verify Jenkins URL in config:
   ```bash
   jctl config get production.jenkins.url
   ```
3. Test connectivity:
   ```bash
   curl -I https://jenkins-stg.example.com/
   ```

## Next Steps

Now that you have API token authentication configured:

1. **Test basic commands**:
   ```bash
   jctl pipeline list
   jctl pipeline describe deploy-staging 142
   ```

2. **Explore available commands**:
   ```bash
   jctl --help
   jctl pipeline --help
   jctl job --help
   ```

3. **Configure output format** (optional):
   ```bash
   jctl config set production.output.format json
   ```

4. **Set up aliases** (optional):
   ```bash
   jctl config set aliases.newenv "job trigger deploy-staging"
   jctl newenv  # Now triggers the job!
   ```

## Support

If you encounter issues:

1. Check authentication status: `jctl auth status`
2. Enable debug mode: `jctl --debug auth token`
3. Review logs: `~/.jctl/logs/jctl.log`
4. Check Slack: `avnervidal27@gmail.com` channel
5. Contact: Cloud Engineering team (@maintainers)

## Quick Reference

```bash
# Setup
jctl auth token                          # Configure API token
jctl auth status                         # Check auth status

# Using jctl
jctl pipeline list                       # List pipelines
jctl pipeline describe <name> <build>    # Pipeline details
jctl job trigger <name>                  # Trigger job

# Cleanup
jctl auth logout                         # Remove stored credentials
```
