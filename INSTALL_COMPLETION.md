# Installation Instructions for Shell Completion

When users install `jctl`, they can get shell completion by default using one of these methods:

## Method 1: Automatic Installation (Recommended for Users)

After installing jctl, users simply run:

```bash
jctl completion --install
source ~/.zshrc  # or ~/.bashrc for bash users
```

This will:
1. Automatically detect their shell (bash, zsh, or fish)
2. Add the appropriate completion setup to their shell config file
3. Configure everything correctly without manual intervention

## Method 2: Manual Instructions

Users can also run:

```bash
jctl completion
```

This will display shell-specific instructions for manual setup.

## What Was Implemented

### 1. Automated Setup Script
- **File**: `scripts/setup-completion.py`
- **Purpose**: Automatically detects shell and adds completion to config files
- **Features**:
  - Detects user's shell from `$SHELL` environment variable
  - Finds the appropriate RC file (`.zshrc`, `.bashrc`, `.config/fish/config.fish`)
  - Checks if completion is already installed (avoids duplicates)
  - Adds the completion setup to the RC file
  - Provides clear feedback on success/failure

### 2. Enhanced `jctl completion` Command
- **File**: `jctl/cli.py`
- **New Option**: `--install` flag
- **Behavior**:
  - When `--install` is used, runs the automated setup script
  - Without `--install`, shows manual instructions (original behavior)
  - Auto-detects shell if not specified

### 3. Package Configuration
- **File**: `pyproject.toml`
- **Added**: Package data to include completion scripts in distribution
- **Scripts Included**:
  - `scripts/jctl-completion.zsh` - Static zsh completion script
  - `scripts/setup-completion.py` - Automated setup script

### 4. Documentation Updates

#### README.md
- Added "Shell Completion" section after installation
- Shows the quick `jctl completion --install` command
- Links to COMPLETION_GUIDE.md for details

#### COMPLETION_GUIDE.md
- Updated to prominently feature `--install` option as recommended method
- Kept manual setup instructions as fallback
- Improved structure and clarity

## For Distribution

When you publish jctl to PyPI or distribute it internally, users will:

1. **Install jctl**:
   ```bash
   pip install jctl
   ```

2. **Enable completion** (one-time setup):
   ```bash
   jctl completion --install
   source ~/.zshrc
   ```

3. **Start using tab completion**:
   ```bash
   jctl pipe<Tab>              # completes to: jctl pipeline
   jctl pipeline li<Tab>       # completes to: jctl pipeline list
   jctl pipeline run --<Tab>   # shows: --param, --wait, --notify
   ```

## What Gets Completed

The completion supports:

### Main Commands
- `auth` - Authentication commands
- `config` - Configuration commands
- `job` - Job management commands
- `pipeline` - Pipeline management commands
- `completion` - Completion setup

### Pipeline Subcommands
- `list` - List pipelines
- `describe` - Show pipeline details
- `logs` - View/stream logs
- `run` - Execute pipeline
- `cancel` - Cancel pipeline
- `pause` - Pause pipeline
- `resume` - Resume pipeline
- `replay` - Replay pipeline
- `restart` - Restart pipeline
- `validate` - Validate pipeline
- `search` - Search pipelines

### Job Subcommands
- `trigger` - Trigger job
- `status` - Get job status
- `logs` - View/stream logs
- `stop` - Stop job
- `history` - Show history
- `params` - List parameters

### Options
- Command-specific options like `--param`, `--wait`, `--follow`, `--filter`, etc.
- Global options like `--profile`, `--debug`, `--output`, `--help`

## Testing

To test the installation process:

```bash
# Test the --install flag
jctl completion --install

# Verify completion was added to RC file
tail ~/.zshrc  # or ~/.bashrc

# Test completion works (after sourcing RC file)
jctl pipe<Tab>
jctl pipeline li<Tab>
```

## Benefits for Users

✅ **One command setup** - No manual editing of config files
✅ **Shell auto-detection** - Works for bash, zsh, and fish automatically
✅ **Duplicate prevention** - Won't add completion twice if run again
✅ **Clear instructions** - Shows exactly what to do after installation
✅ **No typing full commands** - Tab completion speeds up workflow
✅ **Discover commands** - See available options as you type
✅ **Fewer typos** - Auto-completion ensures correct command names
