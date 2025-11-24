# Branch Protection Setup Guide

This guide explains how to configure branch protection rules for the jctl repository to enforce the PR-based workflow.

## Prerequisites

- You must have **admin access** to the repository
- The repository must have at least one commit on each branch you want to protect
- **Branch protection requires**: A public repository OR GitHub Pro/Team/Enterprise subscription

## Quick Links

- **Repository Settings**: https://github.com/avidala/jctl/settings
- **Branch Protection Rules**: https://github.com/avidala/jctl/settings/branches

## Step-by-Step Instructions

### 1. Protect the `develop` Branch

1. **Navigate to branch protection settings**:
   - Go to: https://github.com/avidala/jctl/settings/branches
   - Or: Repository → Settings → Branches (left sidebar)

2. **Click "Add rule" or "Add branch protection rule"**

3. **Configure the rule**:

   **Branch name pattern:**
   ```
   develop
   ```

   **Enable these settings:**

   ☑️ **Require a pull request before merging**
   - ☑️ Require approvals: **0** (or 1 if you want code reviews)
   - ☐ Dismiss stale pull request approvals when new commits are pushed (optional)
   - ☑️ Require review from Code Owners (if you have a CODEOWNERS file)

   ☑️ **Require status checks to pass before merging**
   - ☑️ Require branches to be up to date before merging
   - **Add status checks**: Search and select:
     - `test (ubuntu-latest, 3.10)`
     - `test (ubuntu-latest, 3.11)`
     - `test (ubuntu-latest, 3.12)`
     - `test (macos-latest, 3.10)`
     - `test (macos-latest, 3.11)`
     - `test (macos-latest, 3.12)`
     - `test (windows-latest, 3.10)`
     - `test (windows-latest, 3.11)`
     - `test (windows-latest, 3.12)`
     - `lint`

   ☐ **Require conversation resolution before merging** (optional, but recommended)

   ☑️ **Require linear history** (prevents merge commits, enforces squash/rebase)

   ☑️ **Do not allow bypassing the above settings**

4. **Click "Create" or "Save changes"**

### 2. Protect the `main` Branch

1. **Add another rule** by clicking "Add rule" again

2. **Configure the rule**:

   **Branch name pattern:**
   ```
   main
   ```

   **Enable these settings:**

   ☑️ **Require a pull request before merging**
   - ☑️ Require approvals: **1** (require at least one review for production)
   - ☑️ Dismiss stale pull request approvals when new commits are pushed
   - ☑️ Require review from Code Owners (if applicable)

   ☑️ **Require status checks to pass before merging**
   - ☑️ Require branches to be up to date before merging
   - **Add the same status checks as for develop** (test matrix + lint)

   ☑️ **Require conversation resolution before merging**

   ☑️ **Require linear history**

   ☑️ **Do not allow bypassing the above settings**

   ☑️ **Restrict who can push to matching branches** (optional, for added security)
   - Add yourself or specific maintainers

3. **Click "Create" or "Save changes"**

## Alternative: Using GitHub CLI

If you prefer command-line configuration:

### Protect `develop` branch:

```bash
gh api repos/avidala/jctl/branches/develop/protection -X PUT -H "Accept: application/vnd.github+json" --input - <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "test (ubuntu-latest, 3.10)",
      "test (ubuntu-latest, 3.11)",
      "test (ubuntu-latest, 3.12)",
      "test (macos-latest, 3.10)",
      "test (macos-latest, 3.11)",
      "test (macos-latest, 3.12)",
      "test (windows-latest, 3.10)",
      "test (windows-latest, 3.11)",
      "test (windows-latest, 3.12)",
      "lint"
    ]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 0
  },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": false
}
EOF
```

### Protect `main` branch:

```bash
gh api repos/avidala/jctl/branches/main/protection -X PUT -H "Accept: application/vnd.github+json" --input - <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "test (ubuntu-latest, 3.10)",
      "test (ubuntu-latest, 3.11)",
      "test (ubuntu-latest, 3.12)",
      "test (macos-latest, 3.10)",
      "test (macos-latest, 3.11)",
      "test (macos-latest, 3.12)",
      "test (windows-latest, 3.10)",
      "test (windows-latest, 3.11)",
      "test (windows-latest, 3.12)",
      "lint"
    ]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "required_approving_review_count": 1
  },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": true
}
EOF
```

## Verification

After setting up branch protection, verify it's working:

1. **Test direct push prevention**:
   ```bash
   git checkout develop
   echo "test" >> test.txt
   git add test.txt
   git commit -m "test: direct push"
   git push origin develop
   ```

   You should see an error like:
   ```
   remote: error: GH006: Protected branch update failed for refs/heads/develop.
   ```

2. **Test PR workflow**:
   ```bash
   git checkout -b test/branch-protection
   git push origin test/branch-protection
   ```

   Then create a PR on GitHub - it should require checks to pass before merging.

3. **Verify via CLI**:
   ```bash
   gh api repos/avidala/jctl/branches/main/protection | jq
   gh api repos/avidala/jctl/branches/develop/protection | jq
   ```

## Summary of Protection Rules

| Branch | Require PR | Require Reviews | Status Checks | Linear History |
|--------|-----------|-----------------|---------------|----------------|
| `develop` | ✅ | Optional (0-1) | ✅ All tests + lint | ✅ |
| `main` | ✅ | ✅ (1+) | ✅ All tests + lint | ✅ |

## Status Checks Required

Both branches require these checks to pass:

**Test Matrix (9 checks):**
- `test (ubuntu-latest, 3.10)`
- `test (ubuntu-latest, 3.11)`
- `test (ubuntu-latest, 3.12)`
- `test (macos-latest, 3.10)`
- `test (macos-latest, 3.11)`
- `test (macos-latest, 3.12)`
- `test (windows-latest, 3.10)`
- `test (windows-latest, 3.11)`
- `test (windows-latest, 3.12)`

**Lint:**
- `lint`

**Total**: 10 required status checks

## Troubleshooting

### "Status check not found"

If you can't find the status checks when configuring branch protection:

1. Make sure you have at least one PR or commit that triggered the workflows
2. Wait for the workflows to complete at least once
3. Refresh the branch protection settings page
4. The status check names should now appear in the search dropdown

### "Cannot enable branch protection"

Possible causes:
- You don't have admin access to the repository
- The repository is private and you don't have GitHub Pro/Team/Enterprise
- The branch doesn't exist yet
- Solution: Ensure the branch has at least one commit, or make the repository public

### "Required status checks not available"

This means the workflows haven't run yet. To fix:
1. Create a test PR or push a commit to trigger the workflows
2. Wait for all checks to complete
3. Return to branch protection settings - checks should now be available

### Bypassing Protection (Emergency)

If you need to make an emergency change:

1. Temporarily disable the rule (Settings → Branches → Edit rule → Uncheck settings)
2. Make your change
3. Re-enable the rule immediately after

**Note**: This should only be done in true emergencies. Always prefer the PR workflow.

## Optional: Add CODEOWNERS

Create a `.github/CODEOWNERS` file to automatically request reviews:

```
# Default owners for everything
*       @avnervidal

# Specific paths
/jctl/auth/    @avnervidal
/.github/      @avnervidal
```

## Next Steps

After setting up branch protection:

1. ✅ Test that direct pushes are blocked
2. ✅ Create a test PR to verify checks run
3. ✅ Update team documentation
4. ✅ Communicate workflow changes to contributors

---

**Need help?** Check the GitHub documentation: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches
