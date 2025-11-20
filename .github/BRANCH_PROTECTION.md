# Branch Protection Configuration

## Requirements

Branch protection requires either:
- A **public repository**, OR
- **GitHub Pro** subscription

To make the repository public:
```bash
gh repo edit avidala/jctl --visibility public
```

## Recommended Settings for Main Branch

Once the repository is public or you have GitHub Pro, apply these settings:

### Via GitHub CLI

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

### Via GitHub Web UI

Navigate to: `https://github.com/avidala/jctl/settings/branches`

**Main Branch Protection:**
- ✅ Require a pull request before merging
  - ✅ Require approvals: 1
  - ✅ Dismiss stale pull request approvals when new commits are pushed
  - ✅ Require review from Code Owners
- ✅ Require status checks to pass before merging
  - ✅ Require branches to be up to date before merging
  - Required checks:
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
- ✅ Require conversation resolution before merging
- ✅ Require linear history
- ⬜ Do not allow bypassing the above settings (optional - keep unchecked to allow admins to bypass)
- ✅ Do not allow force pushes
- ✅ Do not allow deletions

## Develop Branch (Optional)

If you create a `develop` branch for active development:

```bash
gh api repos/avidala/jctl/branches/develop/protection -X PUT -H "Accept: application/vnd.github+json" --input - <<'EOF'
{
  "required_status_checks": {
    "strict": false,
    "contexts": ["test (ubuntu-latest, 3.11)", "lint"]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": null,
  "restrictions": null,
  "required_linear_history": false,
  "allow_force_pushes": true,
  "allow_deletions": false
}
EOF
```

## Verification

After applying branch protection, verify with:
```bash
gh api repos/avidala/jctl/branches/main/protection | jq
```
