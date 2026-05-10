---
name: git-commit
description:
  Create a focused commit + push (and optional plan-checkbox flip) for the current session's changes. Stages only files
  touched during the agent session, runs the mandatory pre-commit safety check (`git diff --cached --stat` with no path
  arg), drafts a conventional-commit title with `Co-Authored-By` footer, commits, and pushes directly to the working
  branch — quickmerge is intentionally NOT in the flow because parallel agents make dep repos dirty almost continuously,
  and quickmerging with dirty deps lies to CI. If the work shipped a plan todo, also covers the 4-step
  plan-checkbox-flip protocol. Trigger on /git-commit, "commit this", "ship this", "push the change", or any time you're
  about to call git commit / git push.
---

# Git Commit

Creates a focused commit + push from the current agent session — scoped to touched files, with a clear title, the
mandatory pre-commit safety check, and (when applicable) the same-logical-unit plan-checkbox flip. **Default direct
push; do not reach for quickmerge.**

## TL;DR — the dance-free default flow

When you're committing one or two files and concurrent agents may be active in the same repo, the cleanest path is
**three commands**:

```bash
git add -- path/to/my/file              # stage by path; never `git add .`
git commit -m "..."                     # HEREDOC message; never --no-verify
git push origin live-defi-rollout       # direct; never quickmerge by default
```

If foreign work is already in the staged set (a concurrent agent landed something between your `git add` and your
`git commit`), use the **pathspec commit form** to bypass the index entirely:

```bash
git commit -- path/to/my/file -m "..."  # commits ONLY this path's worktree state, ignores index
```

That single change dissolves 90% of the multi-agent commit pain — no stash dance, no `git restore --staged`, no
foreign-bundling risk. **Reach for stash + restore-staged ceremony only when the pathspec form genuinely can't express
your commit.**

## DO NOT do these (anti-patterns, all observed to lose work or scramble state)

| Don't                                         | Why                                                                                                                                            | Do instead                                                                                                                                              |
| --------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `git add .` / `git add -A`                    | Sweeps in foreign uncommitted work, `.env` files, large binaries                                                                               | `git add -- <specific-paths>`                                                                                                                           |
| `git stash --keep-index --include-untracked`  | Combination INVERTS the staged set in some versions — your staged file ends up unstaged, foreign untracked end up staged. Observed 2026-05-08. | `git commit -- <my-file>` (pathspec form) — no stash needed                                                                                             |
| `git restore --staged .`                      | Mass-unstage drops YOUR staged work too when concurrent agents are mid-staging. Observed 2026-05-08.                                           | `git restore --staged <specific-foreign-file>` by name only                                                                                             |
| `git stash drop <index>` blindly              | Concurrent agents can insert NEW stashes at index 0 between your stash list read and your drop. Observed 2026-05-08.                           | Read stash NAME (`git stash list`) before drop; use `git stash drop stash@{<name>}` — or dump first: `git stash show -p stash@{N} > /tmp/stash-N.patch` |
| `git checkout origin/<branch> -- .`           | Pulls foreign just-landed work into your tree as if yours                                                                                      | If you need a clean file, `git checkout HEAD -- <file>` (single path)                                                                                   |
| `--no-verify` / `git commit --no-verify`      | Skips pre-commit hooks (banned by workspace rule)                                                                                              | Fix the hook failure root cause                                                                                                                         |
| `SKIP_BRANCH_DRIFT=1 git commit ...`          | The `check-branch-drift.sh` hook explicitly says "Human-only — agents MUST NOT use this override"                                              | `git pull origin <branch>` then retry the commit                                                                                                        |
| `git push --force` to main / staging          | Overwrites remote-only work (e.g. semver-agent version bumps)                                                                                  | Investigate divergence; never force-push shared branches                                                                                                |
| Manual version bumps (`pyproject.toml`, etc.) | semver-agent handles bumps on merge to main                                                                                                    | Use conventional commit prefixes; semver-agent does the rest                                                                                            |
| `--amend` on any commit                       | Pre-commit hook failure means commit DIDN'T happen — `--amend` modifies the PREVIOUS commit                                                    | Create a new commit                                                                                                                                     |

## Workflow

### 1. Identify touched files

Run `git status` and `git diff --name-only HEAD` to see all modified/untracked files.

Cross-reference against files that were **actually read or edited during this session** (visible in the conversation's
tool calls). Only stage those files.

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

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

**Type**: `feat`, `fix`, `chore`, `refactor`, `docs`, `style`, `test`, `perf`, `ci`, `plan(<plan-name>)` **Scope**:
component name, module, or area (e.g. `trading-nav`, `service-tabs`, `promote`) **Title**: imperative verb, no period —
"add X", "fix Y", "update Z"

Follow the workspace conventional-commits rule: `feat!:` for breaking changes (post-1.0.0 only — pre-1.0.0 it's a MINOR
bump per the semver-agent override). **Never bump versions manually** — the semver-agent does it on merge to main.

### 3. Stage only the session-touched files

```bash
git add -- path/to/file1 path/to/file2 ...
```

Never use `git add .` or `git add -A` unless the user explicitly asks to stage everything — accidentally sweeps in
`.env`, credentials, large binaries, and (worse) other agents' uncommitted work.

### 4. Pre-commit safety check (catches accidental bundling of foreign work)

Two teammates × multiple parallel agents means another agent may have staged or modified files in this repo while you
worked. Before EVERY `git commit`:

```bash
git status                        # full picture: modified, staged, untracked
git diff --cached --stat          # NO PATH ARGUMENT — see the entire index
git diff --cached --name-status   # confirm YOUR renames/adds/deletes are still there
```

If anything is in the staged set or working tree that isn't yours:

- `git restore --staged <file>` to un-stage foreign content
- OR `git stash --keep-index` the unrelated stuff before committing
- OR use `git add -p <file>` to stage only your hunks
- OR commit with explicit pathspec: `git commit -- <my-file-1> <my-file-2>` (creates a commit from only those paths'
  worktree state, leaves the rest of the index alone)

**Never pass a `<path>` argument to `git diff --cached --stat`** — that filters output to just that path and masks other
staged hunks. **Never run `git checkout origin/<branch> -- .`** as a recovery move — it dumps remote changes (including
other agents' just-landed work) into your tree.

If `git status` reports "ahead by N commits" mid-session and you didn't make N commits, a concurrent agent moved HEAD —
check `git log origin/<branch>..HEAD` before proceeding. After every `git mv` / `git rm` / `git add`, before committing,
verify YOUR entries are still in the index — a parallel reset can erase staged renames without surfacing any error.

Reference incidents (all bundled or wiped foreign work, all 2026-05-07 PM repo):

- PM@961980db — `git add <plan-file>` picked up a teammate's local-uncommitted hunks in the same file.
- PM@611b9501 — `git diff --cached --stat <single-path>` masked a teammate's `git mv` already in the index.
- PM@34075d84 → reset to PM@7de75819 — parallel agent reset wiped another agent's staged renames silently.

### 5. Commit

```bash
git commit -m "$(cat <<'EOF'
type(scope): title

Issues solved:
- ...

Fixes applied:
- ...

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

If the index has foreign work staged by a parallel agent and you only want to commit your file, use the explicit
pathspec form:

```bash
git commit -- <my-file-1> <my-file-2> -m "$(cat <<'EOF'
...
EOF
)"
```

This creates a commit from only those paths' worktree state and leaves the rest of the index untouched.

### 6. Push (default direct push — do NOT quickmerge)

```bash
git push origin <branch>          # default branch: live-defi-rollout (per workspace-manifest.json)
```

**Why not quickmerge:** parallel agents (Harsh + Ikenna, multiple Cursor + Claude Code sessions) make upstream dep repos
(UAC / UTL / UCI / UEI / MTDS / URDI / instruments-service / etc.) dirty almost continuously. Quickmerging a downstream
consumer with dirty upstream deps is misleading — the consumer's local `uv pip install -e ../<dep>` resolves to the
dirty tree, but the pushed branch links to `origin/<dep>` which lacks those edits → CI green locally, red remotely, the
PR is a lie. Plus quickmerge's stash + auto-staging behaviour has been the root cause of multiple foreign-file-bundling
incidents. **In practice, default to direct push and don't reach for quickmerge.** The legitimate exception
(verified-clean-dep-graph finished feature being landed) is rare enough to ask the user before invoking
`scripts/quickmerge.sh`.

**`live-defi-rollout` is the working branch.** VMs pull from it; CI runs against it. Rapid iteration doesn't need a
quickmerge → main promotion.

**Two-pass model becomes:** Pass 1 = `bash scripts/quality-gates.sh` (full — tests + lint + format + typecheck + codex).
Pass 2 = `git push` (no separate re-run; QG already covered everything).

**QG failure attribution:**

- QG fails on code YOU wrote → fix + re-run + commit + push.
- QG fails on code another agent wrote (verify via `git blame` / `git log`) → continue staging + committing + pushing
  your work anyway; they fix their breakage on their own commits.

### 7. Flip plan checkbox (only if the commit shipped a todo from `plans/active/`)

Plan checkbox flips happen in the SAME logical unit of work as the code commit — not at session end, not "after next
agent picks it up." If your push above completed a plan todo:

1. Edit the plan file in `unified-trading-pm/plans/active/<plan>.plan.md`:
   ```
   - [ ] [SCRIPT] P0. Description...
   →
   - [x] [SCRIPT] P0. Description... (<repo>@<sha> + brief evidence)
   ```
2. Commit the plan flip as a SEPARATE commit in PM with `plan(...)` prefix referencing the work commits:

   ```bash
   git commit -m "$(cat <<'EOF'
   plan(<plan-name>): flip <Phase>.<Tier> checkboxes (<one-line summary>)

   * <repo>@<sha> — <one-line>
   * <repo>@<sha> — <one-line>

   Plan: <plan-filename>.

   Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
   EOF
   )"
   ```

3. `git push` the plan flip.
4. Only then move to the next todo.

**Don't flip a checkbox unless the work is actually shipped.** Pushed commits count; local commits do NOT. If half-done
(helper shipped but consumer wiring deferred), flip only the half that landed and append `**DEFERRED**:` to the
unshipped half explaining why.

### 8. Verify

Run `git status` and `git log -1 --format='%h %s'` after pushing to confirm. Show the user:

- The commit hash (short)
- Files included
- The remote branch name + that the push succeeded
- If a plan flip went out, the plan-flip commit hash too

## Rules

- **Never `--no-verify`** — always run pre-commit hooks. If a hook fails, investigate and fix the root cause; don't
  bypass it.
- **Never `git add .` or `git add -A`** unless user explicitly requests it.
- **Never amend** — create new commits. Pre-commit hook failure means the commit didn't happen, so `--amend` would
  modify the PREVIOUS commit and destroy work.
- **Never `--dep-branch` in agent sessions** — quickmerge exits(1) when combined with `--agent`. Branch read
  automatically from `active_feature_branch` in `workspace-manifest.json`. (Moot under the default-direct-push rule, but
  still applies on the rare quickmerge exception.)
- **Never force-push to main / master** — warn the user if asked.
- **Never `git checkout origin/<branch> -- .`** as a recovery move — pulls in other agents' just-landed work as if
  yours.
- **Never edit files outside your clear context** to clear a QG / lint / scope-registry gate. Untracked files in any dep
  repo are almost always another agent's WIP — tell the user instead.
- **Never bump versions manually** — not in `pyproject.toml`, not in `workspace-manifest.json`, not in floor
  constraints. The semver-agent handles bumps on merge to main.
- **Never quickmerge by default** — direct push to `live-defi-rollout` is the rule. Quickmerge is an exception for
  landing a finished feature with a verified-clean dep graph; ask the user before invoking it.
- **Cadence is per shippable unit, not per session.** Five shippable units = five commit+push cycles. Pushed = real;
  local-only commits are invisible to other agents, CI, and VMs that pull from `live-defi-rollout`.
- Staged files must reflect session work only — not unrelated pre-existing changes, not foreign agents' WIP.
- Pre-commit safety check (step 4) is mandatory for every commit, not optional.

## Examples

**Minimal (one file changed):**

```
style(trading-nav): increase icon size and contrast in vertical nav

Issues solved:
- Icons were barely visible at 16px with muted-foreground colour

Fixes applied:
- Increased icon size to 18px expanded, 20px collapsed
- Changed inactive icon colour from text-muted-foreground to text-foreground/60

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
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

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

**Plan-flip commit (PM repo, after the work commit is pushed):**

```
plan(writegate_honest_coverage_endtoend_2026_05_06): flip Phase 3.B checkboxes (features-sports reconciler shipped)

* features-sports-service@f123069 — NEW scripts/features_sports_reconcile_available_at.py 462 lines + 9 tests
* PM@896c9bc5 — codify HARD RULE for same-logical-unit plan-flip cadence

Plan: writegate_honest_coverage_endtoend_2026_05_06.plan.md.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

## Full canonical sequence (one shippable unit)

```bash
# 1. QG (Pass 1 — full)
cd <repo> && bash scripts/quality-gates.sh

# 2. Stage only your files
git add -- <my-file-1> <my-file-2>

# 3. Pre-commit safety check — full picture, NO path filtering
git status
git diff --cached --stat       # NO path argument
git diff --cached --name-status

# 4. Commit (with Co-Authored-By footer; use pathspec form if foreign work is staged)
git commit -m "$(cat <<'EOF'
<type>(<scope>): <summary>

Issues solved:
- ...

Fixes applied:
- ...

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"

# 5. Push directly — NOT quickmerge (deps are almost always dirty)
git push origin live-defi-rollout

# 6. Plan flip (only if a plan todo just shipped) — separate commit in PM repo
cd unified-trading-pm
# edit plans/active/<plan>.plan.md: - [ ] → - [x] with sha + evidence
git add plans/active/<plan>.plan.md
git commit -m "$(cat <<'EOF'
plan(<plan-name>): flip <Phase>.<Tier> checkboxes (<summary>)

* <repo>@<sha> — <one-line>

Plan: <plan-filename>.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push

# 7. Verify
git log -1 --format='%h %s'
```

## Workspace anti-patterns (banned — observed to lose work or scramble state 2026-05-08)

| Anti-pattern                                 | What goes wrong                                                                               | Use instead                                                                              |
| -------------------------------------------- | --------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| `git stash --keep-index --include-untracked` | INVERTS staged set in some prek+git versions — staged file unstaged, foreign untracked staged | `git commit -- <my-file>` pathspec form (no stash needed)                                |
| `git restore --staged .` (mass-unstage)      | Drops YOUR own staged work when concurrent agents are mid-staging                             | `git restore --staged <specific-file>` by name only                                      |
| `git stash drop <index>` blindly             | Concurrent agents insert NEW stashes at index 0 between your `list` read and `drop` call      | Read NAME first; dump via `git stash show -p stash@{N} > /tmp/stash-N.patch` before drop |
| `SKIP_BRANCH_DRIFT=1`                        | `check-branch-drift.sh` script: "agents MUST NOT use this override"                           | `git pull origin <branch>` then retry the commit                                         |
| `git checkout origin/<branch> -- .`          | Pulls foreign just-landed work into your tree as if yours                                     | `git checkout HEAD -- <single-file>` for targeted reset                                  |

**Pathspec form is the dance-free default for multi-agent staging collisions:**

```bash
git commit -- path/to/my/file -m "..."         # commits ONLY this path's worktree state, ignores index
git commit --only -- path/to/my/file -m "..."  # explicit form, same semantics — `--only` is default with paths
```

**Foot-gun #4 escalation** (per CLAUDE.md § "Foot-gun #4 — auto-revert hook racing your edits"): when `Edit` succeeds
but file is unmodified after, OR commit lands under wrong author with empty diff, OR
`Restored working tree changes from .../prek/patches/` appears in commit output — bundle Edit → stage → commit → push
into ONE Bash call:

```bash
git add <my-file> \
  && git diff --cached --name-status \
  && git commit --only --no-verify -- <my-file> -m "..." \
  && git push origin <branch>
```

`--no-verify` is operator-authorized for this specific failure mode per 2026-05-08 direction _"fix to keep your work"_ —
do NOT use it outside foot-gun #4 conditions.

**Reference incidents (2026-05-08 ikenna_orchestrator bootstrap session):**

- `git stash --keep-index --include-untracked` inverted the staged set: staged `_agent_pings.md` ended up unstaged, 19
  foreign files appeared in the index after stash pop.
- `git restore --staged .` (mass) dropped CLAUDE.md edit alongside foreign files; had to be re-applied.
- Wrong-stash drop: `claude-codex-sync-park-foreign-prek-2026-05-08` was at index 0 where MY stash had been seconds
  earlier (concurrent agent inserted between read + drop). Recovery SHA preserved in `git fsck --unreachable`:
  `09c3ad0af469ad3421c9d3e7621513c45d673040`.

## See also

- `.claude/CLAUDE.md` § _Commit + Push + Flip Plan Checkboxes As You Ship Each Item (HARD RULE)_ — full rule text + the
  mandatory pre-commit check + reference incidents.
- `.claude/CLAUDE.md` § _Two teammates × multiple parallel agents — don't edit unfamiliar files_ — file-ownership
  discipline.
- `.claude/CLAUDE.md` § _DO NOT quickmerge when dep repos are dirty_ — original 2026-05-06 dirty-deps rule (refined
  2026-05-07 to "default direct push, don't reach for quickmerge").
- `unified-trading-pm/plans/PLAN_FORMAT.md` § _Cursor-Friendly Todo Checkboxes_ — `- [x]` / `- [ ]` rendering rule.
