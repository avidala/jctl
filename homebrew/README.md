# Homebrew distribution

jctl is distributed via the [`avidala/homebrew-jctl`](https://github.com/avidala/homebrew-jctl) tap.

## For users

```bash
brew install avidala/jctl/jctl
```

Or tap first, then install:

```bash
brew tap avidala/jctl
brew install jctl
```

Updating:

```bash
brew update
brew upgrade jctl
```

## For maintainers

The formula source of truth lives in the tap repo at `Formula/jctl.rb`. Do not hand-edit a copy in this repo — there is no duplicate to drift.

### Automatic bumps on release

The workflow at `.github/workflows/bump-homebrew-formula.yml` runs on every published (non-prerelease) GitHub release and:

1. Waits for the `jctl-<version>.tar.gz` release asset to be available.
2. Computes its SHA256.
3. Checks out `avidala/homebrew-jctl`, rewrites `url` and `sha256` in `Formula/jctl.rb`, and pushes to `main`.

It can also be triggered manually via `workflow_dispatch` with a `version` input — useful for backfilling or recovery.

### Required secret

The workflow needs a repository secret named `HOMEBREW_TAP_TOKEN`: a fine-grained PAT (or classic PAT with `repo` scope) with write access to `avidala/homebrew-jctl`. Add it under **Settings → Secrets and variables → Actions**.

### When a dependency changes (manual update)

The auto-bump only refreshes `url` and `sha256`. If you change Python dependencies in `pyproject.toml`, regenerate the resource blocks in the tap:

```bash
brew tap avidala/jctl
brew update-python-resources avidala/jctl/jctl --install-dependencies --print-only
```

Paste the output over the existing `resource` blocks, then audit:

```bash
brew audit --strict --online avidala/jctl/jctl
```

### Local formula testing

```bash
brew untap avidala/jctl 2>/dev/null
brew tap avidala/jctl /path/to/your/homebrew-jctl/checkout
brew install --build-from-source avidala/jctl/jctl
brew test avidala/jctl/jctl
```
