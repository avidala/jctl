# Quick Start Guide

## You're All Set! 🎉

The repository is configured with best practices. Here's what you need to know:

## Current Branch: `develop` (Default)

You're currently on the **develop** branch, which is now the default branch for the repository.

### Daily Development (Simple!)

```bash
# You're already on develop, just start coding!
# Make your changes...

# Commit and push (no PR needed for develop)
git add .
git commit -m "feat: your awesome feature"
git push origin develop

# That's it! CI/CD runs automatically ✅
```

## Branch Overview

| Branch   | Purpose              | Protection | Push Style    |
|----------|----------------------|------------|---------------|
| develop  | Daily development    | ❌ None    | ✅ Direct push |
| main     | Production releases  | ⚠️ Manual  | 🚫 Avoid      |

## Quick Commands

### Everyday Development
```bash
# Check current branch
git branch --show-current

# Make sure you're on develop
git checkout develop

# Update from remote
git pull origin develop

# After making changes
git add .
git commit -m "type: description"
git push origin develop
```

### View CI/CD Status
```bash
# Check latest workflow runs
gh run list --limit 5

# Watch a specific run
gh run watch
```

### When Ready to Release
```bash
# Create PR from develop to main
gh pr create --base main --head develop --title "Release v0.X.Y"

# After PR is merged and you're on main
git checkout main
git pull origin main
git tag -a v0.X.Y -m "Release v0.X.Y"
git push origin v0.X.Y

# Sync back to develop
git checkout develop
git merge main
git push origin develop
```

## Commit Message Format

Use conventional commits:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `refactor:` - Code refactoring
- `test:` - Tests
- `chore:` - Maintenance

**Examples:**
```bash
git commit -m "feat: add retry logic to HTTP client"
git commit -m "fix: resolve authentication timeout issue"
git commit -m "docs: update API documentation"
```

## What Happens on Push

Every push to develop triggers:
- ✅ **Tests** - Runs on Ubuntu, macOS, Windows with Python 3.10, 3.11, 3.12
- ✅ **Lint** - Black, Ruff, Bandit, Safety checks
- ✅ **Coverage** - Reports test coverage to Codecov

View results: https://github.com/avidala/jctl/actions

## Current Status

- ✅ Default branch: `develop`
- ✅ CI/CD workflows: Running
- ✅ Dependabot: Active (8 PRs created)
- ✅ Issue/PR templates: Ready
- ✅ Documentation: Complete

## Need Help?

- **Development Workflow**: See `.github/DEVELOPMENT_WORKFLOW.md`
- **Repository Setup**: See `.github/REPOSITORY_SETUP.md`
- **Issues**: https://github.com/avidala/jctl/issues

## Pro Tips

1. **Always pull before starting work**
   ```bash
   git checkout develop && git pull origin develop
   ```

2. **Run tests locally before pushing**
   ```bash
   pytest
   ```

3. **Check formatting before committing**
   ```bash
   black jctl/ tests/ --check
   ruff check jctl/ tests/
   ```

4. **View recent commits**
   ```bash
   git log --oneline -10
   ```

5. **Undo last commit (if not pushed)**
   ```bash
   git reset --soft HEAD~1
   ```

## You're Ready to Go! 🚀

Start coding on `develop` and push directly. No PRs needed for daily work!

```bash
# You're already on develop, just start coding!
git add .
git commit -m "feat: amazing new feature"
git push origin develop
```
