# Homebrew Formula for jctl

This directory contains the Homebrew formula for installing jctl.

## For Users: Installing jctl via Homebrew

Once the tap is published, users can install jctl with:

```bash
# Tap the repository
brew tap avidala/jctl

# Install jctl
brew install jctl

# Verify installation
jctl --version
```

Or install in one command:

```bash
brew install avidala/jctl/jctl
```

## For Maintainers: Publishing the Tap

### Step 1: Create the Tap Repository

Create a new GitHub repository named `homebrew-jctl`:

```bash
# Using GitHub CLI
gh repo create avidala/homebrew-jctl --public --description "Homebrew tap for jctl"

# Clone it
git clone https://github.com/avidala/homebrew-jctl.git
cd homebrew-jctl
```

### Step 2: Add the Formula

Copy the formula to the tap repository:

```bash
# Create Formula directory
mkdir -p Formula

# Copy the formula
cp /path/to/jctl/homebrew/jctl.rb Formula/jctl.rb

# Create README
cat > README.md << 'EOF'
# Homebrew Tap for jctl

Official Homebrew tap for [jctl](https://github.com/avidala/jctl) - Jenkins Control CLI with Okta SSO.

## Installation

```bash
brew install avidala/jctl/jctl
```

## Usage

After installation, run:

```bash
jctl --help
```

For more information, visit the [main repository](https://github.com/avidala/jctl).
EOF

# Commit and push
git add .
git commit -m "feat: add jctl formula v0.1.0"
git push origin main
```

### Step 3: Test the Installation

```bash
# Tap your repository
brew tap avidala/jctl

# Install jctl
brew install jctl

# Test it
jctl --version
```

### Step 4: Updating the Formula for New Releases

When you release a new version:

1. Download the new release tarball
2. Calculate the new SHA256:
   ```bash
   curl -sL https://github.com/avidala/jctl/releases/download/vX.X.X/jctl-X.X.X.tar.gz | shasum -a 256
   ```
3. Update `Formula/jctl.rb`:
   - Change the `url` line to point to the new version
   - Update the `sha256` with the new hash
4. Commit and push:
   ```bash
   git add Formula/jctl.rb
   git commit -m "chore: update jctl to vX.X.X"
   git push origin main
   ```

Users will get the update with:
```bash
brew update
brew upgrade jctl
```

## Formula Details

The formula:
- Uses Python 3.10+
- Creates a virtualenv
- Installs all dependencies automatically
- Provides the `jctl` command

## Testing the Formula Locally

Before publishing, test the formula:

```bash
# Audit the formula
brew audit --strict --online Formula/jctl.rb

# Install from local formula
brew install --build-from-source Formula/jctl.rb

# Test it
jctl --version
```

## Troubleshooting

**Problem**: Formula fails to install

**Solution**: Check:
1. The release URL is accessible
2. The SHA256 matches the tarball
3. All dependencies are available
4. Python version compatibility

**Problem**: Command not found after install

**Solution**:
```bash
brew link jctl
```

## Resources

- [Homebrew Formula Cookbook](https://docs.brew.sh/Formula-Cookbook)
- [Python Formula Guide](https://docs.brew.sh/Python-for-Formula-Authors)
- [Homebrew Tap Documentation](https://docs.brew.sh/How-to-Create-and-Maintain-a-Tap)
