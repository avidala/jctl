# Development Workflow

This document describes the PR-based development workflow for the jctl project.

## Overview

We use a **trunk-based development** workflow with two main branches:

- **`develop`** - Development branch for beta releases
- **`main`** - Production branch for stable releases

**⚠️ Important**: Direct pushes to `develop` and `main` are not allowed. All changes must go through pull requests.

## Workflow Process

### 1. Feature Development → Beta Release (Automated)

```
feature-branch → PR to develop → Tests run → Merge → 🤖 Auto-create beta release
```

**Steps:**

1. **Create a feature branch** from `develop`:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/my-feature
   ```

2. **Make your changes** and commit:
   ```bash
   git add .
   git commit -m "feat: add new feature"
   git push origin feature/my-feature
   ```

3. **Open a pull request** to `develop`:
   - Go to GitHub and create a PR from `feature/my-feature` to `develop`
   - Fill in the PR template with description and test plan
   - Wait for CI checks to pass (tests run automatically on PR)

4. **Merge the PR**:
   - Once approved and tests pass, merge the PR to `develop`
   - Delete the feature branch after merge

5. **🤖 Automated beta release** (happens automatically):
   - CI/CD automatically reads version from `pyproject.toml`
   - Creates incrementing beta tag (e.g., `v0.1.0-beta.1`, `v0.1.0-beta.2`, etc.)
   - Builds the package
   - Creates a GitHub pre-release with generated release notes

   **No manual tagging required!** ✨

### 2. Beta → Production Release (Fully Automated)

```
develop → PR to main → Tests run → Merge → 🤖 Auto-increment version & create release
```

**Steps:**

1. **Create PR from develop to main**:
   - Open a pull request from `develop` to `main`
   - Title: "Release to production"
   - Description: Summarize all changes since last production release
   - Wait for CI checks to pass

2. **Merge the PR**:
   - Once approved and tests pass, merge the PR to `main`

3. **🤖 Automated production release** (happens automatically):
   - CI/CD finds the latest production tag (e.g., `v0.1.5`)
   - Auto-increments patch version (e.g., `v0.1.5` → `v0.1.6`)
   - Updates version in `pyproject.toml` and commits to main
   - Creates the production tag
   - Builds the package
   - Creates a GitHub release (stable) with generated release notes

   **No manual version updates or tagging required!** ✨

## CI/CD Automation

### Automated Tests

Tests run automatically on:
- ✅ Every push to `main` and `develop`
- ✅ Every pull request to `main` and `develop`

The test workflow runs on multiple platforms and Python versions:
- **OS**: Ubuntu, macOS, Windows
- **Python**: 3.10, 3.11, 3.12

### Automated Releases

**🎉 Releases are fully automated!** No manual versioning or tagging needed.

#### When you merge to `develop`:
- ✅ Reads base version from `pyproject.toml` (e.g., `0.1.0`)
- ✅ Automatically increments beta number (e.g., `v0.1.0-beta.1` → `v0.1.0-beta.2`)
- ✅ Creates and pushes the beta tag
- ✅ Builds the Python package
- ✅ Creates a GitHub **pre-release** with auto-generated notes

#### When you merge to `main`:
- ✅ Finds the latest production tag (e.g., `v0.1.5`)
- ✅ **Auto-increments patch version** (e.g., `v0.1.5` → `v0.1.6`)
- ✅ Updates `pyproject.toml` with new version and commits to main
- ✅ Creates and pushes the production tag
- ✅ Builds the Python package
- ✅ Creates a GitHub **release** (stable) with auto-generated notes

**Smart duplicate prevention**: If a tag already exists, the workflow skips release creation.

**Version strategy**: Production releases auto-increment the **patch** version. For major or minor version bumps, manually update `pyproject.toml` before merging to main.

## Branch Protection (Recommended)

To enforce this workflow, configure branch protection rules on GitHub:

### For `develop` branch:

1. Go to: Settings → Branches → Add rule
2. Branch name pattern: `develop`
3. Enable:
   - ☑️ Require a pull request before merging
   - ☑️ Require status checks to pass before merging
   - ☑️ Require branches to be up to date before merging
   - ☑️ Status checks: `test`
4. Save changes

### For `main` branch:

1. Go to: Settings → Branches → Add rule
2. Branch name pattern: `main`
3. Enable:
   - ☑️ Require a pull request before merging
   - ☑️ Require approvals: 1
   - ☑️ Require status checks to pass before merging
   - ☑️ Require branches to be up to date before merging
   - ☑️ Status checks: `test`
4. Save changes

## Version Numbering

We follow [Semantic Versioning](https://semver.org/) with **automatic patch version incrementing**:

- **MAJOR.MINOR.PATCH** (e.g., `1.2.3`)
- **MAJOR.MINOR.PATCH-beta.N** (e.g., `1.2.3-beta.1`)

### Automatic Version Progression:

**Production releases** (merging to main):
```
v0.1.0 → v0.1.1 → v0.1.2 → v0.1.3 (auto-incremented patch)
```

**Beta releases** (merging to develop):
```
v0.1.0-beta.1 → v0.1.0-beta.2 → v0.1.0-beta.3 (auto-incremented beta number)
```

### Manual Version Bumps:

For **major** or **minor** version changes, update `pyproject.toml` before merging to main:

```bash
# For a minor version bump (new features)
git checkout develop
# Edit pyproject.toml: version = "0.2.0"
git commit -am "chore: bump minor version to 0.2.0"
git push origin develop

# Then create PR to main
# Result: v0.2.0 (instead of auto-incremented v0.1.4)
```

Example full progression:
```
v0.1.0-beta.1 → develop (auto)
v0.1.0-beta.2 → develop (auto)
v0.1.0        → main (first production)
v0.1.1        → main (auto-incremented)
v0.1.2        → main (auto-incremented)

# Manual bump for new features
v0.2.0-beta.1 → develop (auto)
v0.2.0-beta.2 → develop (auto)
v0.2.0        → main (uses version from pyproject.toml)
v0.2.1        → main (auto-incremented)
```

## Quick Reference

| Action | Command |
|--------|---------|
| Create feature branch | `git checkout -b feature/name` |
| Push feature | `git push origin feature/name` |
| Update version | Edit `version = "X.Y.Z"` in `pyproject.toml` |
| List tags | `git tag -l` |
| View releases | `gh release list` |
| Delete local tag | `git tag -d v0.2.0-beta.1` |
| Delete remote tag | `git push origin --delete v0.2.0-beta.1` |

## Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat: add new feature` - New feature
- `fix: resolve bug` - Bug fix
- `docs: update documentation` - Documentation only
- `style: format code` - Code style changes
- `refactor: restructure code` - Code refactoring
- `test: add tests` - Adding tests
- `chore: update dependencies` - Maintenance tasks

## Example Workflow

Here's a complete example of adding a feature and releasing it:

```bash
# 1. Start feature development
git checkout develop
git pull origin develop
git checkout -b feature/add-completion

# 2. Make changes and commit
git add jctl/utils/completion.py
git commit -m "feat: add shell completion support"
git push origin feature/add-completion

# 3. Open PR on GitHub to develop
# (wait for review and tests to pass, then merge)

# 4. 🤖 Beta release happens automatically after merge!
# Example: v0.1.0-beta.1 created automatically
# Check: https://github.com/avidala/jctl/releases

# 5. After more features and testing, promote to production
# Open PR from develop to main on GitHub
# (wait for review and tests to pass, then merge)

# 6. 🤖 Production release happens automatically after merge!
# Example: v0.1.0 → v0.1.1 (auto-incremented!)
# pyproject.toml updated automatically
# Check: https://github.com/avidala/jctl/releases
```

**For major/minor version bumps only:**
```bash
# If you need v0.2.0 instead of v0.1.x
git checkout develop
# Edit pyproject.toml: version = "0.2.0"
git commit -am "chore: bump minor version to 0.2.0"
git push origin develop
# Then create PR to main as usual
```

## Troubleshooting

**Q: Tests are failing on my PR. How do I see the details?**

A: Click on "Details" next to the failing check in the PR. This will show you the full test output.

**Q: I accidentally pushed directly to develop. What should I do?**

A: If branch protection is not enabled yet, you can revert the commit and create a PR instead:
```bash
git checkout develop
git revert HEAD
git push origin develop
```

**Q: The auto-release didn't trigger. What happened?**

A: Check the Actions tab on GitHub. Common issues:
- The workflow file might not be on the target branch yet
- There might be a syntax error in the workflow
- The version in `pyproject.toml` hasn't changed
- A tag with the same version already exists

**Q: How do I delete a release if I made a mistake?**

A:
```bash
# Delete the tag
git tag -d v0.2.0-beta.1              # Delete locally
git push origin --delete v0.2.0-beta.1  # Delete on GitHub

# Delete the release on GitHub
gh release delete v0.2.0-beta.1 --yes
```

**Q: Can I manually trigger a release?**

A: Yes, you can re-run the workflow from the Actions tab, or manually create and push a tag if needed.

**Q: Can I push hotfixes directly to main?**

A: No. Even urgent hotfixes should go through a PR. You can expedite the process by:
1. Creating a hotfix branch from main
2. Opening a PR
3. Requesting immediate review
4. Merging once tests pass

---

**Need help?** Open an issue or contact the maintainers.
