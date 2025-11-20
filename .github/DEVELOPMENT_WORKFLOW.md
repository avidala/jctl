# Development Workflow

**Default Branch**: `develop`
**Protected Branch**: `main` (production releases only)

## Branch Strategy

### develop (Default Branch)
- **Purpose**: Active development and feature integration
- **Protection**: None - direct push allowed
- **CI/CD**: All tests and lint checks run on push
- **Use for**: Day-to-day development work

### main (Protected Branch)
- **Purpose**: Production-ready stable code
- **Protection**: Manual protection (avoid direct push)
- **Updates**: Only via PR from develop or hotfix branches
- **Releases**: All release tags created from main

## Daily Development Workflow

### 1. Working on develop (Direct Push)

```bash
# Make sure you're on develop
git checkout develop
git pull origin develop

# Make your changes
# ... edit files ...

# Commit and push directly
git add .
git commit -m "feat: your feature description"
git push origin develop

# CI/CD will run automatically
```

### 2. Working on Feature Branches (Optional)

```bash
# Create feature branch from develop
git checkout develop
git pull origin develop
git checkout -b feature/your-feature

# Make changes and commit
git add .
git commit -m "feat: your feature"
git push origin feature/your-feature

# Create PR to develop
gh pr create --base develop --title "Your feature" --body "Description"

# After PR is merged, delete feature branch
git checkout develop
git pull origin develop
git branch -d feature/your-feature
```

## Releasing to Production (main)

### Option 1: Direct PR from develop to main

```bash
# Ensure develop is ready for release
git checkout develop
git pull origin develop

# Run all checks locally
pytest
black jctl/ tests/ --check
ruff check jctl/ tests/
bandit -r jctl/ -ll

# Create PR from develop to main
gh pr create --base main --head develop --title "Release v0.X.Y" --body "$(cat <<'EOF'
## Release v0.X.Y

### Changes
- Feature 1
- Feature 2
- Bug fix 3

### Testing
- [x] All tests pass
- [x] Manual testing complete
- [x] Changelog updated
EOF
)"

# After PR is merged to main, create release tag
git checkout main
git pull origin main
git tag -a v0.X.Y -m "Release v0.X.Y"
git push origin v0.X.Y

# Switch back to develop
git checkout develop
```

### Option 2: Merge main back to develop after release

```bash
# After releasing to main, sync back to develop
git checkout main
git pull origin main

git checkout develop
git merge main
git push origin develop
```

## Hotfix Workflow

For urgent production fixes:

```bash
# Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b hotfix/critical-bug

# Fix the bug
git add .
git commit -m "fix: critical bug description"

# Create PR to main
gh pr create --base main --title "Hotfix: critical bug" --body "Description"

# After merge, tag the hotfix
git checkout main
git pull origin main
git tag -a v0.X.Y -m "Hotfix v0.X.Y"
git push origin v0.X.Y

# Merge back to develop
git checkout develop
git merge main
git push origin develop
```

## CI/CD Behavior

### On develop branch:
- ✅ Tests run (all platforms, all Python versions)
- ✅ Lint checks run
- ✅ Coverage reported
- ℹ️ No release created

### On main branch:
- ✅ Tests run (all platforms, all Python versions)
- ✅ Lint checks run
- ✅ Coverage reported
- ℹ️ Release created only when tag is pushed

### On Pull Requests:
- ✅ Tests run
- ✅ Lint checks run
- ✅ PR template enforced
- ✅ Code owners notified

## Quick Commands

```bash
# Check current branch
git branch --show-current

# Switch to develop (your working branch)
git checkout develop

# Update from remote
git pull origin develop

# View recent commits
git log --oneline -10

# Create and push a commit
git add .
git commit -m "type: description"
git push origin develop

# Check CI/CD status
gh run list --limit 5

# View all branches
git branch -a
```

## Branch Protection Summary

| Branch   | Default | Protected | Direct Push | Release Tags |
|----------|---------|-----------|-------------|--------------|
| develop  | ✅ Yes  | ❌ No     | ✅ Allowed  | ❌ No        |
| main     | ❌ No   | ⚠️ Manual | ⚠️ Avoid    | ✅ Yes       |

## Best Practices

1. **Always work on develop** for daily development
2. **Keep main stable** - only merge tested, production-ready code
3. **Use conventional commits**: `feat:`, `fix:`, `docs:`, `refactor:`, etc.
4. **Run tests locally** before pushing to develop
5. **Update CHANGELOG.md** before releasing to main
6. **Create release tags** from main branch only
7. **Sync develop with main** after releases

## Conventional Commit Types

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks
- `perf:` - Performance improvements
- `ci:` - CI/CD changes
- `build:` - Build system changes

## Example Scenarios

### Scenario 1: Quick bug fix
```bash
git checkout develop
# Fix bug
git add .
git commit -m "fix: resolve authentication timeout issue"
git push origin develop
```

### Scenario 2: New feature with PR
```bash
git checkout -b feature/add-retry-logic
# Implement feature
git commit -m "feat: add exponential backoff retry logic"
git push origin feature/add-retry-logic
gh pr create --base develop
```

### Scenario 3: Release to production
```bash
# On develop, ensure everything is ready
git checkout develop
pytest && black . --check && ruff check .

# Create release PR
gh pr create --base main --head develop --title "Release v0.2.0"

# After merge, tag release
git checkout main
git pull
git tag -a v0.2.0 -m "Release v0.2.0"
git push origin v0.2.0

# Sync back
git checkout develop
git merge main
git push origin develop
```

## Troubleshooting

**Accidentally pushed to main:**
```bash
# If not yet pushed to remote
git checkout develop

# If already pushed to remote
# Contact repository admin or reset (be careful!)
```

**Need to sync develop with main:**
```bash
git checkout develop
git pull origin main
git push origin develop
```

**Conflicts when merging main to develop:**
```bash
git checkout develop
git merge main
# Resolve conflicts in your editor
git add .
git commit -m "chore: merge main into develop"
git push origin develop
```
