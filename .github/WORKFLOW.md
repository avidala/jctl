# Development Workflow

This document describes the PR-based development workflow for the jctl project.

## Overview

We use a **trunk-based development** workflow with two main branches:

- **`develop`** - Development branch for beta releases
- **`main`** - Production branch for stable releases

**⚠️ Important**: Direct pushes to `develop` and `main` are not allowed. All changes must go through pull requests.

## Workflow Process

### 1. Feature Development → Beta Release

```
feature-branch → PR to develop → Tests run → Merge → Beta release tag
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

5. **Create a beta release tag** (after merging to develop):
   ```bash
   git checkout develop
   git pull origin develop
   git tag v0.2.0-beta.1
   git push origin v0.2.0-beta.1
   ```

   This will trigger the release workflow and create a **pre-release** on GitHub.

### 2. Beta → Production Release

```
develop → PR to main → Tests run → Merge → Production release tag
```

**Steps:**

1. **After several beta releases**, when ready for production, open a PR from `develop` to `main`:
   ```bash
   # Ensure develop is up to date
   git checkout develop
   git pull origin develop

   # Push to remote if needed
   git push origin develop
   ```

2. **Create PR on GitHub**:
   - Open a pull request from `develop` to `main`
   - Title: "Release v0.2.0" (or appropriate version)
   - Description: Summarize all changes since last production release
   - Wait for CI checks to pass

3. **Merge the PR**:
   - Once approved and tests pass, merge the PR to `main`

4. **Create a production release tag**:
   ```bash
   git checkout main
   git pull origin main
   git tag v0.2.0
   git push origin v0.2.0
   ```

   This will trigger the release workflow and create a **production release** on GitHub.

## CI/CD Automation

### Automated Tests

Tests run automatically on:
- ✅ Every push to `main` and `develop`
- ✅ Every pull request to `main` and `develop`

The test workflow runs on multiple platforms and Python versions:
- **OS**: Ubuntu, macOS, Windows
- **Python**: 3.10, 3.11, 3.12

### Automated Releases

Releases are created automatically when you push version tags:

- **Beta releases**: Tags containing "beta" (e.g., `v0.2.0-beta.1`)
  - Marked as pre-release on GitHub
  - Used for testing in development

- **Production releases**: Tags without "beta" (e.g., `v0.2.0`)
  - Marked as latest release on GitHub
  - Used for stable, production-ready versions

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

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR.MINOR.PATCH** (e.g., `1.2.3`)
- **MAJOR.MINOR.PATCH-beta.N** (e.g., `1.2.3-beta.1`)

Example progression:
```
v0.1.0-beta.1 → develop
v0.1.0-beta.2 → develop
v0.1.0-beta.3 → develop
v0.1.0        → main (production)

v0.2.0-beta.1 → develop
v0.2.0-beta.2 → develop
v0.2.0        → main (production)
```

## Quick Reference

| Action | Command |
|--------|---------|
| Create feature branch | `git checkout -b feature/name` |
| Push feature | `git push origin feature/name` |
| Create beta tag | `git tag v0.2.0-beta.1 && git push origin v0.2.0-beta.1` |
| Create production tag | `git tag v0.2.0 && git push origin v0.2.0` |
| List tags | `git tag -l` |
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

# 4. Create beta release
git checkout develop
git pull origin develop
git tag v0.2.0-beta.1
git push origin v0.2.0-beta.1

# 5. After more features, promote to production
# (open PR from develop to main on GitHub, merge)

# 6. Create production release
git checkout main
git pull origin main
git tag v0.2.0
git push origin v0.2.0
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

**Q: How do I delete a beta tag if I made a mistake?**

A:
```bash
git tag -d v0.2.0-beta.1              # Delete locally
git push origin --delete v0.2.0-beta.1  # Delete on GitHub
```

**Q: Can I push hotfixes directly to main?**

A: No. Even urgent hotfixes should go through a PR. You can expedite the process by:
1. Creating a hotfix branch from main
2. Opening a PR
3. Requesting immediate review
4. Merging once tests pass

---

**Need help?** Open an issue or contact the maintainers.
