# Platform Testing Guide

This guide provides instructions for testing jctl on macOS, Linux, and Windows platforms.

## Testing Checklist

Use this checklist when testing jctl on each platform:

### ✅ macOS (Primary Development Platform)
- [x] Installation works
- [x] Virtual environment setup
- [x] All dependencies install correctly
- [x] Keystore (Keychain) integration works
- [x] Authentication (API token) works
- [x] All commands execute successfully
- [x] Tab completion works
- [x] Tests pass

**Status**: ✅ Complete

---

### ⏳ Linux (Ubuntu 22.04 / Debian-based)

#### Prerequisites
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.10+
sudo apt install python3.10 python3.10-venv python3-pip -y

# Install development dependencies
sudo apt install build-essential libssl-dev libffi-dev python3-dev -y

# Install keyring dependencies for SecretService
sudo apt install gnome-keyring libsecret-1-0 libsecret-1-dev -y
```

#### Installation
```bash
# Clone repository
git clone https://github.com/avidala/jctl.git
cd public-cloud-infrastructure/cli/jenkins

# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate

# Install jctl
pip install -e ".[dev]"
```

#### Testing Steps
- [ ] **Installation**: Does `pip install -e ".[dev]"` complete successfully?
- [ ] **Version check**: Does `jctl --version` work?
- [ ] **Config init**: Does `jctl config init` run and create `~/.jctl/config.yaml`?
- [ ] **File permissions**: Are permissions correct (0700 for dir, 0600 for config)?
- [ ] **Keystore (SecretService)**: Test storing/retrieving credentials
  ```bash
  jctl auth token
  # Enter username and token
  jctl auth status
  # Should show authenticated
  ```
- [ ] **Keystore fallback**: If SecretService unavailable, does encrypted fallback work?
- [ ] **Commands**: Test each command group
  ```bash
  jctl config list
  jctl auth status
  jctl pipeline list
  jctl job trigger --help
  ```
- [ ] **Tab completion**: Does zsh/bash completion work?
  ```bash
  jctl completion --install
  source ~/.bashrc  # or ~/.zshrc
  jctl pipe<Tab>
  ```
- [ ] **Tests**: Do pytest tests pass?
  ```bash
  pytest
  pytest --cov=jctl
  ```
- [ ] **Debug mode**: Does `--debug` flag work?
  ```bash
  jctl --debug auth status
  ```

#### Known Linux Issues
1. **SecretService not available**: Ensure `gnome-keyring` is running
   ```bash
   # Start keyring
   gnome-keyring-daemon --start

   # Check if running
   ps aux | grep gnome-keyring
   ```

2. **DBus session issues**: May need to set up DBus session
   ```bash
   export $(dbus-launch)
   ```

3. **Headless servers**: Use encrypted fallback (automatic if SecretService unavailable)

---

### ⏳ Windows (Windows 10/11)

#### Prerequisites
```powershell
# Install Python 3.10+ from https://www.python.org/downloads/
# Ensure "Add Python to PATH" is checked during installation

# Verify installation
python --version
pip --version

# Install Git for Windows from https://git-scm.com/download/win
```

#### Installation
```powershell
# Clone repository
git clone https://github.com/avidala/jctl.git
cd public-cloud-infrastructure\cli\jenkins

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install jctl
pip install -e ".[dev]"
```

#### Testing Steps
- [ ] **Installation**: Does `pip install -e ".[dev]"` complete successfully?
- [ ] **Version check**: Does `jctl --version` work?
- [ ] **Config init**: Does `jctl config init` run and create `%USERPROFILE%\.jctl\config.yaml`?
- [ ] **File permissions**: Are permissions appropriate for Windows?
- [ ] **Keystore (Credential Manager)**: Test storing/retrieving credentials
  ```powershell
  jctl auth token
  # Enter username and token
  jctl auth status
  # Should show authenticated
  ```
- [ ] **Keystore fallback**: If Credential Manager fails, does encrypted fallback work?
- [ ] **Commands**: Test each command group
  ```powershell
  jctl config list
  jctl auth status
  jctl pipeline list
  jctl job trigger --help
  ```
- [ ] **Tab completion**: PowerShell completion (if supported)
- [ ] **Tests**: Do pytest tests pass?
  ```powershell
  pytest
  pytest --cov=jctl
  ```
- [ ] **Debug mode**: Does `--debug` flag work?
  ```powershell
  jctl --debug auth status
  ```

#### Known Windows Issues
1. **Path issues**: Windows uses `\` instead of `/` in paths
   - jctl should handle this automatically with `pathlib`

2. **Credential Manager**: May require admin privileges for first use
   - Test both with and without admin rights

3. **PowerShell execution policy**: May need to adjust
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

4. **Color output**: Windows Terminal supports colors, cmd.exe may not
   - Test in both Windows Terminal and cmd.exe

---

## Platform-Specific Features

### Keystore Integration

**macOS (Keychain)**:
- Location: macOS Keychain (`Keychain Access.app`)
- Service: `jctl`
- Items stored: `jenkins_username`, `jenkins_token`, `encryption_key`

**Linux (SecretService)**:
- Location: GNOME Keyring / KDE Wallet
- Service: `jctl`
- Items stored: Same as macOS
- Fallback: Encrypted file at `~/.jctl/.credentials.enc`

**Windows (Credential Manager)**:
- Location: Windows Credential Manager (`Control Panel > Credential Manager`)
- Service: `jctl`
- Items stored: Same as macOS
- Fallback: Encrypted file at `%USERPROFILE%\.jctl\.credentials.enc`

### Configuration Paths

**macOS/Linux**:
- Config: `~/.jctl/config.yaml`
- Cache: `~/.jctl/cache/`
- Logs: `~/.jctl/logs/`

**Windows**:
- Config: `%USERPROFILE%\.jctl\config.yaml`
- Cache: `%USERPROFILE%\.jctl\cache\`
- Logs: `%USERPROFILE%\.jctl\logs\`

---

## Automated Testing

### CI/CD Pipeline Testing

When setting up GitHub Actions, test on all platforms:

```yaml
strategy:
  matrix:
    os: [ubuntu-latest, macos-latest, windows-latest]
    python-version: ['3.10', '3.11', '3.12']
```

### Docker Testing (Linux)

Test in a clean Ubuntu container:

```bash
docker run -it --rm ubuntu:22.04 /bin/bash

# Inside container
apt update && apt install -y python3.10 python3.10-venv git
git clone https://github.com/avidala/jctl.git
cd public-cloud-infrastructure/cli/jenkins
python3.10 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
pytest
```

---

## Reporting Issues

When reporting platform-specific issues, include:

1. **Platform details**:
   - OS and version (e.g., Ubuntu 22.04, macOS 14.2, Windows 11)
   - Python version (`python --version`)
   - Architecture (x86_64, ARM64)

2. **Installation logs**:
   ```bash
   pip install -e ".[dev]" > install.log 2>&1
   ```

3. **Debug output**:
   ```bash
   jctl --debug auth status > debug.log 2>&1
   ```

4. **Environment info**:
   ```bash
   jctl config show
   env | grep JCTL
   ```

---

## Platform Testing Status

| Platform | Version | Status | Tested By | Date |
|----------|---------|--------|-----------|------|
| macOS | 14.x (Sonoma) | ✅ Working | @avnervidal | 2025-01-20 |
| Linux | Ubuntu 22.04 | ⏳ Pending | - | - |
| Linux | Ubuntu 24.04 | ⏳ Pending | - | - |
| Linux | Debian 12 | ⏳ Pending | - | - |
| Windows | Windows 11 | ⏳ Pending | - | - |
| Windows | Windows 10 | ⏳ Pending | - | - |

---

## Next Steps

1. **Test on Linux**: Set up Ubuntu VM or use Docker
2. **Test on Windows**: Set up Windows VM or use WSL2
3. **Document issues**: Create GitHub issues for platform-specific bugs
4. **Update CI/CD**: Add multi-platform testing to GitHub Actions

---

**Document Version**: 1.0
**Last Updated**: 2025-01-20
**Status**: Linux and Windows testing pending
