#!/bin/bash
# Migration script for jctl to avidala/jctl repository
# This script automates the repository migration process

set -e  # Exit on error

echo "🚀 jctl Repository Migration Script"
echo "===================================="
echo ""

# Configuration
GITHUB_OWNER="avidala"
REPO_NAME="jctl"
FULL_REPO="${GITHUB_OWNER}/${REPO_NAME}"
SOURCE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TEMP_DIR="/tmp/jctl-migration"

echo "📋 Configuration:"
echo "  Owner: ${GITHUB_OWNER}"
echo "  Repository: ${REPO_NAME}"
echo "  Full name: ${FULL_REPO}"
echo "  Source: ${SOURCE_DIR}"
echo ""

# Step 1: Check prerequisites
echo "🔍 Checking prerequisites..."

if ! command -v gh &> /dev/null; then
    echo "❌ Error: GitHub CLI (gh) is not installed"
    echo "   Install: brew install gh"
    exit 1
fi

if ! gh auth status &> /dev/null; then
    echo "❌ Error: Not authenticated with GitHub CLI"
    echo "   Run: gh auth login"
    exit 1
fi

echo "✅ Prerequisites OK"
echo ""

# Step 2: Confirm migration
echo "⚠️  This will create a new repository: ${FULL_REPO}"
echo ""
read -p "Do you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Migration cancelled"
    exit 0
fi

echo ""

# Step 3: Check if repository already exists
echo "🔍 Checking if repository exists..."

if gh repo view "${FULL_REPO}" &> /dev/null; then
    echo "⚠️  Repository ${FULL_REPO} already exists!"
    read -p "Do you want to continue anyway? (yes/no): " continue_existing
    if [ "$continue_existing" != "yes" ]; then
        echo "❌ Migration cancelled"
        exit 0
    fi
else
    # Step 4: Create repository
    echo "📦 Creating repository ${FULL_REPO}..."

    gh repo create "${FULL_REPO}" \
        --public \
        --description "Command-line interface for managing Jenkins pipelines with Okta SSO" \
        --homepage "https://github.com/${FULL_REPO}" \
        --enable-issues \
        --enable-wiki=false

    echo "✅ Repository created"
fi

echo ""

# Step 5: Prepare temporary directory
echo "📁 Preparing temporary directory..."

if [ -d "${TEMP_DIR}" ]; then
    echo "  Cleaning existing temp directory..."
    rm -rf "${TEMP_DIR}"
fi

mkdir -p "${TEMP_DIR}"
cd "${TEMP_DIR}"

echo "✅ Temporary directory ready: ${TEMP_DIR}"
echo ""

# Step 6: Clone new repository
echo "📥 Cloning repository..."

git clone "https://github.com/${FULL_REPO}.git" .

echo "✅ Repository cloned"
echo ""

# Step 7: Copy files
echo "📋 Copying files from source..."

# Copy all files except .git
rsync -av --exclude='.git' --exclude='venv' --exclude='__pycache__' \
    --exclude='.pytest_cache' --exclude='.mypy_cache' --exclude='.ruff_cache' \
    --exclude='*.pyc' --exclude='.DS_Store' \
    "${SOURCE_DIR}/" "${TEMP_DIR}/"

echo "✅ Files copied"
echo ""

# Step 8: Update repository URLs in files
echo "🔧 Updating repository URLs..."

# Update pyproject.toml
if [ -f "pyproject.toml" ]; then
    sed -i '' "s|h2oai/jctl|${FULL_REPO}|g" pyproject.toml
    sed -i '' "s|public-cloud-infrastructure/cli/jenkins|${FULL_REPO}|g" pyproject.toml
    echo "  ✅ Updated pyproject.toml"
fi

# Update README.md
if [ -f "README.md" ]; then
    sed -i '' "s|h2oai/jctl|${FULL_REPO}|g" README.md
    sed -i '' "s|public-cloud-infrastructure/cli/jenkins|${FULL_REPO}|g" README.md
    echo "  ✅ Updated README.md"
fi

# Update CONTRIBUTING.md
if [ -f "CONTRIBUTING.md" ]; then
    sed -i '' "s|h2oai/jctl|${FULL_REPO}|g" CONTRIBUTING.md
    sed -i '' "s|public-cloud-infrastructure/cli/jenkins|${FULL_REPO}|g" CONTRIBUTING.md
    echo "  ✅ Updated CONTRIBUTING.md"
fi

echo "✅ Repository URLs updated"
echo ""

# Step 9: Git operations
echo "📝 Committing files..."

git add .
git commit -m "Initial commit: v0.1.0-beta.1

Migrated from public-cloud-infrastructure/cli/jenkins

Features:
- 18 working commands across 4 groups (auth, job, pipeline, config)
- Dual authentication (OAuth 2.0 + API tokens)
- OS-native keystore integration
- Comprehensive documentation
- Test suite with 50%+ coverage
- Code quality: 94/100
- Security: 0 vulnerabilities

See CHANGELOG.md for complete details.
"

echo "✅ Files committed"
echo ""

# Step 10: Push to GitHub
echo "📤 Pushing to GitHub..."

git push origin main

echo "✅ Pushed to main branch"
echo ""

# Step 11: Create develop branch
echo "🌿 Creating develop branch..."

git checkout -b develop
git push -u origin develop

echo "✅ Develop branch created"
echo ""

# Step 12: Create initial tag
echo "🏷️  Creating initial tag v0.1.0-beta.1..."

git checkout main
git tag -a v0.1.0-beta.1 -m "Beta release v0.1.0-beta.1

First public beta release of jctl.

See CHANGELOG.md for full release notes.
"
git push origin v0.1.0-beta.1

echo "✅ Tag created and pushed"
echo ""

# Step 13: Summary
echo "🎉 Migration Complete!"
echo "===================="
echo ""
echo "Repository: https://github.com/${FULL_REPO}"
echo "Main branch: https://github.com/${FULL_REPO}/tree/main"
echo "Develop branch: https://github.com/${FULL_REPO}/tree/develop"
echo "Release: https://github.com/${FULL_REPO}/releases/tag/v0.1.0-beta.1"
echo ""
echo "📋 Next Steps:"
echo "  1. Set up branch protection: https://github.com/${FULL_REPO}/settings/branches"
echo "  2. Add GitHub Actions workflows (see MIGRATION_PLAN.md Phase 2)"
echo "  3. Configure Dependabot"
echo "  4. Update old repository with redirect"
echo "  5. Announce migration to team"
echo ""
echo "📁 Migration files are in: ${TEMP_DIR}"
echo ""
echo "✅ All done!"
