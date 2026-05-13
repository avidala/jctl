# Shell Completion for jctl

The jctl CLI supports intelligent tab completion for commands, subcommands, and options, making it much easier to work with Jenkins without typing full paths.

## Quick Setup

### Automatic Installation (Recommended)

The easiest way to enable completion:

```bash
# Automatically install completion for your shell
jctl completion --install

# Then reload your shell
source ~/.zshrc  # for zsh
source ~/.bashrc # for bash
exec $SHELL      # or restart your shell
```

This will automatically:
- Detect your shell (bash, zsh, or fish)
- Add the completion setup to your shell config file
- Configure everything correctly

### Manual Setup

If you prefer manual setup or the automatic installation doesn't work:

#### For Zsh (macOS default)

Add this line to your `~/.zshrc`:

```bash
eval "$(_JCTL_COMPLETE=zsh_source jctl)"
```

Then reload your shell:

```bash
source ~/.zshrc
```

#### For Bash

Add this line to your `~/.bashrc`:

```bash
eval "$(_JCTL_COMPLETE=bash_source jctl)"
```

Then reload your shell:

```bash
source ~/.bashrc
```

#### For Fish

Run this command once:

```bash
_JCTL_COMPLETE=fish_source jctl > ~/.config/fish/completions/jctl.fish
```

Then reload your shell:

```bash
source ~/.config/fish/config.fish
```

## Getting Help

Run this command to see shell-specific instructions:

```bash
jctl completion         # Auto-detect shell and show instructions
jctl completion zsh     # Show zsh instructions
jctl completion bash    # Show bash instructions
jctl completion fish    # Show fish instructions
```

## What Gets Auto-Completed

### 1. Command Names
```bash
jctl pipe<Tab>       # Completes to: jctl pipeline
jctl pipeline r<Tab> # Completes to: jctl pipeline run
```

### 2. Job/Pipeline Names
```bash
jctl pipeline run managed-<Tab>
# Shows:
#   deploy/release-pipeline
#   deploy/monitor-infrastructure
#   qa/run-pre-commit
#   ...

jctl pipeline run deploy/release-<Tab>
# Shows:
#   deploy/release-pipeline
#   deploy/monitor-infrastructure
#   deploy/provision-environment
#   ...
```

### 3. Options and Flags
```bash
jctl pipeline run deploy/release-pipeline --<Tab>
# Shows:
#   --param
#   --wait
#   --notify
#   --help
```

## Examples

### Pipeline Completion
```bash
# Type this:
jctl pipeline run man<Tab>

# Get this:
jctl pipeline run deploy/

# Continue typing:
jctl pipeline run deploy/release-u<Tab>

# Get this:
jctl pipeline run deploy/release-pipeline
```

### Job Completion
```bash
# Type this:
jctl job logs deploy/ch<Tab>

# Get this:
jctl job logs qa/run-pre-commit
```

### Logs Completion
```bash
# Type this:
jctl pipeline logs man<Tab>

# Get this:
jctl pipeline logs deploy/

# Then add build number:
jctl pipeline logs deploy/release-pipeline 123
```

## How It Works

1. **Dynamic Completion**: When you press Tab, jctl queries your Jenkins instance in real-time
2. **Authentication Required**: You must be authenticated (`jctl auth token` or `jctl auth login`) for completion to work
3. **Folder Structure**: Completion respects Jenkins folder structure (e.g., `deploy/release-*`)
4. **Fast Caching**: Results are fetched quickly using the Jenkins API

## Troubleshooting

### Completion not working?

1. **Check authentication:**
   ```bash
   jctl auth status
   ```

2. **Reload your shell:**
   ```bash
   source ~/.zshrc  # or ~/.bashrc
   ```

3. **Verify completion is installed:**
   ```bash
   jctl completion
   ```

4. **Test manually:**
   ```bash
   _JCTL_COMPLETE=zsh_complete jctl
   ```

### Completion is slow?

The first time you press Tab, jctl fetches all jobs from Jenkins. This might take 1-2 seconds depending on:
- Number of jobs in Jenkins
- Network latency
- Jenkins server load

Subsequent completions should be faster as the shell caches results.

### No jobs shown in completion?

Check that:
1. You're authenticated: `jctl auth status`
2. You have access to jobs in Jenkins
3. Jenkins is reachable: `jctl pipeline list`

## Benefits

✅ **No more typing long paths** - Just use Tab to complete
✅ **Discover jobs** - See what's available as you type
✅ **Prevent typos** - Auto-completion ensures correct names
✅ **Faster workflow** - Spend less time typing, more time doing
✅ **Works with folders** - Respects Jenkins folder structure

## Commands with Completion

All these commands support job/pipeline name completion:

- `jctl pipeline run <name>`
- `jctl pipeline describe <name>`
- `jctl pipeline logs <name>`
- `jctl pipeline cancel <name>`
- `jctl job trigger <name>`
- `jctl job logs <name>`

Enjoy faster Jenkins CLI workflows with auto-completion! 🚀
