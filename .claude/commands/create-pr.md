# Create Pull Request Command

Create a new branch, commit changes, and submit a pull request.

## Usage
```
/create-pr [issue-number]
```

## Arguments
- `issue-number` (optional): GitHub issue number to link to this PR (e.g., `123` for issue #123)

## Behavior
- **Creates a new branch** with naming convention: `{username}/{issue-number}/{description}`
  - Gets username from git config (`git config user.name`)
  - Uses issue number if provided
  - Generates descriptive kebab-case name from changes
  - Example: `avner/5900/update-gitignore-and-refactor-dns-expiration`
- Runs pre-commit hooks (terraform fmt, validate, etc.)
- Analyzes changes and automatically splits into logical commits when appropriate
- **MUST use commit conventions from `.claude/commands/commit.md`** including:
  - Emoji conventional commit format
  - Proper commit message structure
  - Atomic commits for single purposes
- Each commit focuses on a single logical change or feature
- Creates descriptive commit messages for each logical unit
- Pushes branch to remote
- **Creates pull request as DRAFT by default**
- **Targets `main` branch by default**
- **PR title MUST follow format: `chore(scope): description`** or similar conventional commit format
- **If issue number provided**: Links PR to the issue and adds "Closes #[issue-number]" to PR body

## PR Configuration
- **Base branch**: `main` (not `develop`)
- **Status**: Draft (use `--draft` flag)
- **Branch naming**: `{username}/{issue-number}/{description}`
  - Username: From `git config user.name` (lowercase, spaces to hyphens)
  - Issue number: If provided via argument
  - Description: Kebab-case summary of changes
  - Examples: `avner/5900/update-gitignore-and-refactor-dns-expiration`, `john/456/add-cloudfront-support`
- **Title format**: `chore(scope): description` where scope identifies the area (e.g., `chore(infrastructure):`, `feat(jenkins):`, `fix(dns):`)
- **Issue linking**: If issue number is provided via `/create-pr [issue-number]`:
  - Add "Closes #[issue-number]" to the PR body
  - GitHub will automatically link and close the issue when PR is merged

## Guidelines for Automatic Commit Splitting
- Split commits by feature, component, or concern
- Keep related file changes together in the same commit
- Separate refactoring from feature additions
- Ensure each commit can be understood independently
- Multiple unrelated changes should be split into separate commits
- Follow ALL conventions from `.claude/commands/commit.md` for each commit

## Commit Message Format (from commit.md)
Use emoji conventional commit format:
- ✨ `feat`: New feature
- 🐛 `fix`: Bug fix
- 📝 `docs`: Documentation
- 💄 `style`: Formatting/style
- ♻️ `refactor`: Code refactoring
- ⚡️ `perf`: Performance improvements
- ✅ `test`: Tests
- 🔧 `chore`: Tooling, configuration
- 🙈 `chore`: Update .gitignore
- And many more (see commit.md for full list)

## Important Notes
- Always check git status and diff before committing
- Run pre-commit checks to ensure code quality
- Create atomic commits for better review and rollback
- PR titles must use conventional commit format with scope
- PRs are created as drafts by default to allow for review before marking ready
- If an issue number is provided, the PR will automatically close the issue when merged
- Use `gh` CLI to create PRs with proper issue linking: `gh pr create --draft --body "...Closes #123..."`
- **Branch naming is mandatory**: Get username via `git config user.name`, convert to lowercase, replace spaces with hyphens
- If no issue number provided, omit it from branch name: `{username}/{description}` instead of `{username}/{issue-number}/{description}`

## Examples

**Create PR without issue:**
```
/create-pr
```
- Branch: `avner/update-gitignore-and-refactor-dns-expiration`
- PR body: Standard summary without issue link

**Create PR linked to issue #456:**
```
/create-pr 456
```
- Branch: `avner/456/add-cloudfront-distribution-lookup`
- PR body: Includes "Closes #456"
- GitHub will automatically link the PR to issue #456 and close it when merged

**Workflow:**
1. Run `/create-pr [issue-number]`
2. Command gets username from `git config user.name`
3. Creates branch: `{username}/{issue-number}/{description}`
4. Makes atomic commits with emoji conventional format
5. Pushes branch and creates draft PR on `main`
6. PR title uses conventional commit format: `chore(scope): description`