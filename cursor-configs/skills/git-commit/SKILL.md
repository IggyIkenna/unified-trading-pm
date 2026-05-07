---
name: git-commit
description: Create a local git commit for the current session's changes. Generates a clear conventional-commit title, a summary of issues solved and fixes applied, and stages only files touched during the current agent session (unless the user asks to include specific files or all files). Use when the user types /git-commit or asks to commit the current session's work locally.
---
# Git Commit

Creates a focused local commit from the current agent session — scoped to touched files, with a clear title and fix summary.

## Workflow

### 1. Identify touched files

Run `git status` and `git diff --name-only HEAD` to see all modified/untracked files.

Cross-reference against files that were **actually read or edited during this session** (visible in the conversation's tool calls). Only stage those files.

**Exceptions — always follow user's explicit instruction:**

- User says "commit all files" → stage everything
- User says "also include X" → add X
- User says "only commit Y" → stage only Y

### 2. Draft the commit message

Use this structure (HEREDOC to preserve formatting):

```
<type>(<scope>): <imperative title, ≤72 chars>

Issues solved:
- <what was broken or missing>
- <what was broken or missing>

Fixes applied:
- <specific change made>
- <specific change made>
```

**Type**: `feat`, `fix`, `chore`, `refactor`, `docs`, `style`
**Scope**: component name, module, or area (e.g. `trading-nav`, `service-tabs`, `promote`)
**Title**: imperative verb, no period — "add X", "fix Y", "update Z"

Follow the workspace conventional-commits rule: `feat!:` for breaking changes.

### 3. Stage only the session-touched files

```bash
git add -- path/to/file1 path/to/file2 ...
```

Never use `git add .` unless the user explicitly asks to stage everything.

### 4. Commit locally (no push)

```bash
git commit -m "$(cat <<'EOF'
type(scope): title

Issues solved:
- ...

Fixes applied:
- ...
EOF
)"
```

### 5. Verify

Run `git status` after commit to confirm success. Show the user:

- The commit hash (short)
- Files included
- A one-line confirmation that nothing was pushed

## Rules

- **Never `--no-verify`** — always run pre-commit hooks
- **Never `git add .`** unless user explicitly requests it
- **Never amend** an already-pushed commit
- Staged files must reflect session work only — not unrelated pre-existing changes

## Examples

**Minimal (one file changed):**

```
style(trading-nav): increase icon size and contrast in vertical nav

Issues solved:
- Icons were barely visible at 16px with muted-foreground colour

Fixes applied:
- Increased icon size to 18px expanded, 20px collapsed
- Changed inactive icon colour from text-muted-foreground to text-foreground/60
```

**Multi-file feature:**

```
feat(service-tabs): add icons and vertical nav for trading section

Issues solved:
- Trading tabs had no icons, making collapsed nav unusable
- Horizontal tab bar wasted vertical space

Fixes applied:
- Added LucideIcon to each entry in TRADING_TABS
- Created TradingVerticalNav component with collapse/expand toggle
- Updated trading layout to use vertical nav with bottomSlot for LiveAsOfToggle
```
