# jctl Repository Migration Plan

**Version**: v0.1.0-beta.1
**Date**: 2025-01-20
**Status**: Ready for Migration

## Overview

Migrate jctl from `public-cloud-infrastructure/cli/jenkins` to a standalone GitHub repository with full CI/CD automation.

## Migration Readiness

**Status**: ✅ READY

All critical criteria met:
- ✅ All critical bugs fixed (Week 1)
- ✅ All high priority issues resolved (Week 2)
- ✅ All medium priority improvements complete (Week 3)
- ✅ Code quality: 94/100
- ✅ Security: 0 vulnerabilities
- ✅ Test coverage: 50%+ on core modules
- ✅ Documentation: 95% complete

---

## Phase 1: Repository Setup (Day 1)

### 1.1 Create New Repository

**Repository Owner**: `avidala` (your personal GitHub account)
**Repository Name**: `jctl` or `jenkins-cli`

**Visibility**: Public (or Private initially, then Public)

**Initial Settings**:
```yaml
Name: jctl
Description: Command-line interface for managing Jenkins pipelines with Okta SSO
Topics: jenkins, cli, python, okta, sso, devops, pipeline-management
License: MIT
.gitignore: Python
README: Yes (will be replaced)
```

### 1.2 Initialize Repository Structure

```bash
# Create new repo on GitHub under your account
gh repo create avidala/jctl --public --description "CLI for Jenkins pipeline management"

# Clone locally
git clone https://github.com/avidala/jctl.git
cd jctl

# Copy files from cli/jenkins
cp -r /path/to/public-cloud-infrastructure/cli/jenkins/* .

# Remove monorepo-specific files
rm -rf .git
git init
```

### 1.3 Clean Up Files

**Files to Keep**:
- All `.py` files in `jctl/`
- All test files in `tests/`
- All `.md` documentation files
- All user guides (API_TOKEN_GUIDE.md, etc.)
- `pyproject.toml`
- `requirements.txt`, `requirements-dev.txt`
- `scripts/` directory
- `.pre-commit-config.yaml`
- `.gitignore`

**Files to Remove/Update**:
- Monorepo-specific paths
- References to `public-cloud-infrastructure`
- Internal H2O-specific URLs (if any)

**Files to Update**:
- `README.md` - Update repository URLs
- `CONTRIBUTING.md` - Update clone instructions
- `pyproject.toml` - Update repository URL

---

## Phase 2: CI/CD Setup (Day 1-2)

### 2.1 GitHub Actions Workflows

Create `.github/workflows/` directory with these workflows:

#### a. Test Workflow (`.github/workflows/test.yml`)

```yaml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ['3.10', '3.11', '3.12']

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Run tests
        run: pytest --cov=jctl --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
```

#### b. Lint Workflow (`.github/workflows/lint.yml`)

```yaml
name: Lint

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install black ruff bandit safety

      - name: Run black
        run: black jctl/ tests/ --check

      - name: Run ruff
        run: ruff check jctl/ tests/

      - name: Run bandit
        run: bandit -r jctl/ -ll

      - name: Run safety
        run: safety check
```

#### c. Release Workflow (`.github/workflows/release.yml`)

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Build package
        run: |
          pip install build
          python -m build

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          files: dist/*
          generate_release_notes: true
```

### 2.2 Branch Protection

**Main Branch** (`main`):
- Require pull request reviews (1 approver)
- Require status checks to pass:
  - Tests (all OS/Python combinations)
  - Linting (black, ruff, bandit)
- Require branches to be up to date
- Enforce for administrators
- Restrict who can push (maintainers only)

**Develop Branch** (`develop`):
- Require pull request reviews (1 approver)
- Require status checks to pass
- Allow force pushes by maintainers

### 2.3 Dependabot

Create `.github/dependabot.yml`:

```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

---

## Phase 3: Documentation Updates (Day 2)

### 3.1 Update README.md

**Changes**:
- Update clone URL:
  ```bash
  git clone https://github.com/avidala/jctl.git
  cd jctl
  ```
- Add badges:
  ```markdown
  ![Tests](https://github.com/avidala/jctl/workflows/Tests/badge.svg)
  ![Lint](https://github.com/avidala/jctl/workflows/Lint/badge.svg)
  ![Python](https://img.shields.io/badge/python-3.10%2B-blue)
  ![License](https://img.shields.io/badge/license-MIT-green)
  ```
- Update issue reporting URL
- Update support Slack channel link

### 3.2 Update CONTRIBUTING.md

**Changes**:
- Update clone instructions
- Update repository URL references
- Add CI/CD pipeline information
- Update issue submission link

### 3.3 Update pyproject.toml

**Changes**:
```toml
[project]
name = "jctl"
version = "0.1.0-beta.1"

[project.urls]
Homepage = "https://github.com/avidala/jctl"
Documentation = "https://github.com/avidala/jctl/blob/main/README.md"
Repository = "https://github.com/avidala/jctl"
Issues = "https://github.com/avidala/jctl/issues"
Changelog = "https://github.com/avidala/jctl/blob/main/CHANGELOG.md"
```

---

## Phase 4: Repository Configuration (Day 2)

### 4.1 GitHub Settings

**General**:
- ✅ Issues enabled
- ✅ Projects enabled (optional)
- ✅ Wiki disabled (use README)
- ✅ Discussions enabled (for community)
- ✅ Sponsorships disabled (unless needed)

**Features**:
- ✅ Automatically delete head branches after merge
- ✅ Allow merge commits
- ✅ Allow squash merging (preferred)
- ✅ Allow rebase merging

**Pull Requests**:
- ✅ Require linear history
- ✅ Auto-merge enabled

### 4.2 Issue Templates

Create `.github/ISSUE_TEMPLATE/`:

**bug_report.md**:
```yaml
name: Bug Report
about: Report a bug in jctl
labels: bug
```

**feature_request.md**:
```yaml
name: Feature Request
about: Suggest a new feature
labels: enhancement
```

### 4.3 Pull Request Template

Create `.github/pull_request_template.md`:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Manual testing performed
- [ ] All tests pass

## Checklist
- [ ] Code follows style guidelines (black, ruff)
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
```

### 4.4 Code Owners

Create `.github/CODEOWNERS`:

```
# Default owner for everything
* @managed-cloud-team

# Specific owners for critical areas
/jctl/auth/ @security-team
/jctl/config/ @devops-team
/.github/ @ci-cd-team
```

---

## Phase 5: Migration Execution (Day 3)

### 5.1 Pre-Migration Checklist

- [ ] All Week 1-3 tasks complete
- [ ] All tests passing locally
- [ ] All documentation up to date
- [ ] Version bumped to v0.1.0-beta.1
- [ ] CHANGELOG.md finalized
- [ ] Team notified of migration

### 5.2 Migration Steps

1. **Create GitHub Repository**
   ```bash
   gh repo create avidala/jctl --public
   ```

2. **Copy Files**
   ```bash
   # From public-cloud-infrastructure
   cd public-cloud-infrastructure/cli/jenkins

   # Copy to new repo
   cp -r . /path/to/jctl/
   cd /path/to/jctl
   ```

3. **Clean Git History** (Optional - Start Fresh)
   ```bash
   rm -rf .git
   git init
   git add .
   git commit -m "Initial commit: v0.1.0-beta.1

   - 18 working commands
   - Dual authentication (OAuth + API tokens)
   - Comprehensive documentation
   - Test suite with 50%+ coverage
   "
   ```

4. **Push to GitHub**
   ```bash
   git branch -M main
   git remote add origin https://github.com/avidala/jctl.git
   git push -u origin main
   ```

5. **Create Develop Branch**
   ```bash
   git checkout -b develop
   git push -u origin develop
   ```

6. **Set Up CI/CD**
   - Add GitHub Actions workflows
   - Configure branch protection
   - Enable Dependabot

7. **Create Initial Release**
   ```bash
   git tag -a v0.1.0-beta.1 -m "Beta release v0.1.0-beta.1"
   git push origin v0.1.0-beta.1
   ```

### 5.3 Post-Migration Verification

- [ ] CI/CD pipelines running
- [ ] Tests passing on all platforms
- [ ] Linting passing
- [ ] Documentation rendering correctly
- [ ] Issues/PRs work
- [ ] Branch protection active
- [ ] Release created successfully

---

## Phase 6: Post-Migration Tasks (Week 1)

### 6.1 Update Old Repository

In `public-cloud-infrastructure/cli/jenkins/README.md`:

```markdown
# jctl - Moved

**⚠️ This project has moved to its own repository:**

👉 **https://github.com/avidala/jctl**

Please update your bookmarks and clone from the new location.

## New Installation

\`\`\`bash
git clone https://github.com/avidala/jctl.git
cd jctl
pip install -e ".[dev]"
\`\`\`

See the new repository for latest updates and documentation.
```

### 6.2 Announce Migration

**Slack (#h2o-managed-cloud)**:
```
🎉 jctl has migrated to its own repository!

📦 New Repo: https://github.com/avidala/jctl
🚀 Version: v0.1.0-beta.1
📚 Docs: https://github.com/avidala/jctl/blob/main/README.md

What's new:
✅ 18 working commands
✅ CI/CD with GitHub Actions
✅ Multi-platform testing
✅ Comprehensive documentation

Please clone from the new location for all future work!
```

**Email (managed-cloud@h2o.ai)**:
Similar announcement with migration details.

### 6.3 Monitor First Week

- **Day 1**: Watch CI/CD pipelines
- **Day 2-3**: Monitor issues/questions
- **Day 4-7**: Gather user feedback
- **Week 2**: First maintenance release if needed

---

## Phase 7: Future Enhancements (Post-Migration)

### 7.1 Package Distribution (v0.2.0)

**PyPI Publishing**:
```bash
# Build and publish
python -m build
python -m twine upload dist/*

# Install from PyPI
pip install jctl
```

**Homebrew Formula** (macOS):
```ruby
# Formula/jctl.rb
class Jctl < Formula
  desc "CLI for Jenkins pipeline management"
  homepage "https://github.com/avidala/jctl"
  url "https://github.com/avidala/jctl/archive/v0.2.0.tar.gz"

  depends_on "python@3.10"

  def install
    virtualenv_install_with_resources
  end
end
```

### 7.2 Documentation Site (v0.3.0)

**GitHub Pages** or **ReadTheDocs**:
- API documentation
- User guide
- Examples and tutorials
- Architecture diagrams

### 7.3 Community Growth

- **GitHub Discussions** for Q&A
- **Contributing guidelines** enhancement
- **Good first issue** labels
- **Hacktoberfest** participation

---

## Rollback Plan

If migration fails, rollback steps:

1. **Keep old location working**:
   - Don't delete `cli/jenkins` immediately
   - Keep it for 30 days minimum

2. **If critical issues found**:
   ```bash
   # Revert to old location
   cd public-cloud-infrastructure/cli/jenkins
   # Continue development here
   ```

3. **Archive new repo if needed**:
   - Archive avidala/jctl repository
   - Update README with rollback notice

---

## Success Criteria

**Migration is successful when**:

1. ✅ New repository accessible
2. ✅ CI/CD passing on all platforms
3. ✅ Documentation renders correctly
4. ✅ v0.1.0-beta.1 release created
5. ✅ Team successfully clones and uses from new location
6. ✅ No critical bugs reported in first week
7. ✅ Old repository updated with redirect

---

## Timeline

| Phase | Duration | Start | End |
|-------|----------|-------|-----|
| Phase 1: Repo Setup | 2 hours | Day 1 AM | Day 1 AM |
| Phase 2: CI/CD Setup | 4 hours | Day 1 PM | Day 1 PM |
| Phase 3: Doc Updates | 2 hours | Day 2 AM | Day 2 AM |
| Phase 4: Config | 2 hours | Day 2 PM | Day 2 PM |
| Phase 5: Migration | 2 hours | Day 3 AM | Day 3 AM |
| Phase 6: Post-Migration | 1 week | Day 3 | Week 2 |

**Total Active Time**: ~12 hours over 3 days
**Total Monitoring**: 1 week

---

## Contacts

**Migration Lead**: @avnervidal
**Team**: H2O Managed Cloud (@managed-cloud)
**Slack**: #h2o-managed-cloud
**Email**: managed-cloud@h2o.ai

---

## Appendix: Commands Checklist

**Quick verification after migration**:

```bash
# Clone new repo
git clone https://github.com/avidala/jctl.git
cd jctl

# Setup
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Verify installation
jctl --version  # Should show v0.1.0-beta.1
jctl --help     # Should show all commands

# Run tests
pytest

# Run linters
black jctl/ tests/ --check
ruff check jctl/ tests/
bandit -r jctl/ -ll

# Test authentication
jctl config init
jctl auth token
jctl auth status

# Test commands
jctl pipeline list
jctl config show

# Success! ✅
```

---

**Document Version**: 1.0
**Last Updated**: 2025-01-20
**Status**: Ready for Execution
