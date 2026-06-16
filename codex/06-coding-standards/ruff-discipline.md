---
scope: [engineer, admin]
title: Ruff discipline — workspace-safe lint fix workflow
last_reviewed: 2026-05-12
status: canonical
audience: every-agent-pushing-to-live-defi-rollout
---

# Ruff discipline

Lint failures are the most common red-CI cause this cycle — almost always a missing `ruff format` / `ruff check --fix`
on recently-pushed files (especially new test files). This doc is the workspace SSOT for how to handle them safely in a
multi-agent + per-tab-worktree environment.

**Bar for a Telegram page worth keeping**: something only the operator or another agent's owner can fix — a real bug, a
missing schema, a regression a test caught, a cross-side coordination need. Lint violations on your own new files don't
qualify — they're yours to clear before you push.

If your repo's CI goes red on lint, the fix is yours to make **immediately**, before you continue your current task.
Don't wait for the next session.

## Common ruff codes

- **E501** — line too long (check repo's `line-length` in `pyproject.toml`; workspace default 120).
- **I001** — import block unsorted / unformatted. Auto-fix.
- **RUF003** — ambiguous unicode character in string or comment (`×` instead of `x`, `–` instead of `-`, curly quotes,
  ellipsis `…`). **Not auto-fixable**, hand-fix.

## Rule zero — NEVER `ruff check .` or `ruff format .` on whole repo

Two teammates × multiple parallel agents = a whole-repo ruff sweep WILL modify other agents' uncommitted files and cause
unrecoverable WIP loss. Reference: `cursor-configs/CLAUDE.md` § "Two teammates × multiple parallel agents (CRITICAL)" +
foot-gun #2 (2026-05-08 incident: `ruff check . --fix --unsafe-fixes` modified 116 files including 12 with a foreign
agent's uncommitted WIP; `git checkout --` to revert lost ~12 files of consolidation work).

**Always scope ruff to your own changed files by explicit path.**

## The 3-step workflow

### Step 1 — identify your changed files

```bash
# Files modified vs last commit (working tree)
git diff --name-only HEAD | grep '\.py$'

# Untracked new files
git status --porcelain | grep '\.py$' | awk '{print $2}'
```

### Step 2 — run ruff on those files only

```bash
ruff format <file1> <file2> ...
ruff check --fix <file1> <file2> ...
```

### Step 3 — verify only your files changed, then commit

```bash
git status --short          # confirm only files you own appear
git diff --cached --stat    # NO path arg — see entire index pre-commit
# If anything foreign appears: git restore <foreign-file> BEFORE staging.
# Never `git checkout origin/<branch> -- .` (dumps remote work into your tree).

git add <your-files>
git commit --no-verify -m "fix(lint): ruff format + check --fix on <files>"
git push origin live-defi-rollout
```

## Per-tab worktree caveat (`.tabs/<N>/`)

Per-tab worktrees often have no per-repo `.venv`, so `ruff` may not be on PATH. Order of fallbacks:

1. **System python**: `python3 -m ruff format <file>` / `python3 -m ruff check --fix <file>`.
2. **`.venv-workspace`**: `source ${WORKSPACE_ROOT}/.venv-workspace/bin/activate` then run `ruff` normally; deactivate
   when done.
3. **`uv tool run`**: `uv tool run ruff format <file>`.

If none reach ruff, that's a real environment problem — surface in your `[main → slot N]` ping file instead of pushing
un-linted code.

## Sub-agent fan-out — extra care

When orchestrating a sub-agent fan-out:

- Each sub-agent runs ruff on its OWN files only (scope-by-explicit-path applies inside sub-agents too).
- After each sub-agent batch: parent agent runs `git diff --name-only` to confirm no sub-agent's edits leaked into
  another's territory.
- Per-shippable-unit commit + push after each sub-agent's batch — makes leaks auditable and recoverable.

## For RUF003 (ambiguous unicode — NOT auto-fixable)

ruff won't auto-fix this. The error message gives `file:line:col` — go there and substitute:

| Unicode   | ASCII | Common context                      |
| --------- | ----- | ----------------------------------- |
| `×`       | `x`   | "5×8 grid", "2×2 matrix"            |
| `–`       | `-`   | "10 – 20" range expressions         |
| `—`       | `--`  | em-dash in docstrings               |
| `…`       | `...` | ellipsis in docstrings              |
| curly `"` | `"`   | curly quotes (copy-paste artifacts) |
| curly `'` | `'`   | curly apostrophes                   |
| `→`       | `->`  | arrows in docstrings or comments    |

## `# noqa` guidance — use sparingly

`# noqa` suppresses a violation without fixing it. Hides real problems, pollutes the codebase.

**Only use `# noqa: <CODE>` when ALL of:**

1. The violation is a genuine false-positive (ruff is wrong for this specific line).
2. You've tried the real fix and it breaks something concrete.
3. You include the specific code (`# noqa: E501`) — bare `# noqa` is invalid in newer ruff and emits its own warning.

**Never use `# noqa` for:**

- Long lines that can be wrapped — wrap them.
- Unsorted imports — `ruff check --fix` sorts them.
- "I'll fix it later" deferrals — fix it now; CI stays red until you do.
- Hiding architectural violations (the `# type: ignore` equivalent) — fix the root cause.

**Workspace custom suppression codes** (`# noqa: qg-deep-import`, `# noqa: qg-no-fallback`, `# noqa: qg-empty-fallback`,
etc.) are valid and intentional — they suppress workspace-specific QG rules registered in repo `pyproject.toml`. Don't
strip these.

## Pre-push checklist (the discipline)

Before every push to `live-defi-rollout` or `tab/<op>/<N>`:

1. `ruff format` + `ruff check --fix` on your changed files only (one-liner below).
2. `git status` — confirm only your files are modified.
3. If anything foreign appears: `git restore <foreign-file>` BEFORE staging.
4. `git diff --cached --stat` (no path arg — see the entire index).
5. Commit with conventional prefix (`feat:` / `fix:` / `docs:` / `test:` / `chore:` / `ci:`).
6. `git fetch origin` + check incoming-touching-my-files (foot-gun protection).
7. Push with `--no-verify` if pre-commit hook fights you (per CLAUDE.md foot-gun #4 mitigation — authorized when hook
   auto-restore would lose real work).

One-liner:

```bash
files=$(git diff --name-only HEAD | grep '\.py$')
[ -z "$files" ] && files=$(git diff --cached --name-only | grep '\.py$')
[ -n "$files" ] && echo "$files" | xargs -r ruff format && echo "$files" | xargs -r ruff check --fix
```

## When a Telegram alert IS real

After this discipline lands, expected real-alert classes (worth keeping):

- **TYPECHECK failure** — basedpyright caught an actual type error; can't ship without addressing.
- **TESTS failure** — a real regression. Don't push past it.
- **[6/6] PRODUCTION READINESS VALIDATORS** — `workspace-manifest.json` drift or plan-discipline rules; often needs
  cross-side coordination.
- **Schema-provenance drift / deep-import drift / inline-bucket-uri drift** — workspace SSOT violations (CLAUDE.md §
  "Service Infrastructure Requirements" + § "Bucket-name SSOT").
- **STEP 5.70 `pipeline_mode=` baseline regression** — new implicit-mode callsites past the baseline.

These ARE worth paging. The lint failures this doc eliminates are not.

## Cross-references

- `cursor-configs/CLAUDE.md` § "Two teammates × multiple parallel agents (CRITICAL)" — foot-gun #2 (ruff sweep) +
  recovery rules.
- `cursor-configs/CLAUDE.md` § "Commit + Push + Flip Plan Checkboxes As You Ship Each Item (HARD RULE)" —
  per-shippable-unit cadence + mandatory pre-commit check.
- `cursor-configs/CLAUDE.md` § "CI Verification After Every Push (HARD RULE)" — what red CI means for `main` vs
  `live-defi-rollout`.
- `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` — paste at top of every Task-tool spawn so sub-agents inherit these
  rules and don't run `ruff check .` blindly.
- `codex/06-coding-standards/quality-gates.md` — broader local QG workflow (this doc is a scoped sub-discipline within
  that workflow).

## Provenance

Promoted to codex 2026-05-12 from `plans/active/issues/ci_lint_failures_ruff_fix_guidance_2026_05_12.md` (authored by
harsh-main 2026-05-12 after multiple repos went red at STEP [2/6] LINT on live-defi-rollout). The issue was
discipline-prescriptive, not a bug — moving to permanent codex home so future agents see it via codex search rather than
rediscovering through red-CI cycles.
