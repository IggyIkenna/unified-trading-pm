# iCloud Migration — 60 Repos Rollout Agent Prompt

Copy this prompt to the next agent to roll out the iCloud migration script across 60 repos.

---

## Script Location (SSOT)

**Absolute path:**

```
/Users/ikennaigboaka/Library/Mobile Documents/com~apple~CloudDocs/Documents/Documents - Mac/repos/unified-trading-system-repos/unified-trading-pm/scripts/icloud-migrate-commit.sh
```

---

## Agent Task

Roll out the iCloud migration script to 60 repos. Each repo lives on iCloud Drive (slow). Adapt the script per-repo and ensure it:

1. **Copies the script** into each repo's `scripts/` (create if missing)
2. **Adapts batches** to that repo's top-level directories (discover dynamically; don't hardcode PM-specific paths like cursor-rules, github-integration)
3. **Splits staging into one directory at a time** — log each, check for hangs
4. **If a directory hangs** — further split by subdirectory until the problematic path is identified; skip or exclude that path and continue
5. **Ensures .gitignore and .cursorignore** include common large regeneratable paths — scan each repo for what exists: `.venv/`, `venv/`, `__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `.cache/`, `node_modules/`, `.next/`, `dist/`, `build/`, `.turbo/`, `coverage/`, `.nyc_output/`, `.venv-workspace/`, `.DS_Store`

---

## Script Adaptation Rules

- **Discover top-level dirs:** `ls -d */ 2>/dev/null || true` plus root files
- **One directory per batch** — log `[N/M] dirname/ (X files)` and `-> done` after each
- **Hang detection:** if no `-> done` within ~30s, consider subdirectory split or skip
- **Exclude paths:** use `git add -A -- ':!path/to/skip'` for known problematic dirs
- **Kill bird** at start and again before commit/push
- **Run in background:** `nohup bash scripts/icloud-migrate-commit.sh &` — script has tendency to hang on iCloud
- **Push:** `git push --force-with-lease origin main` (or `--force` if needed)

---

## .gitignore / .cursorignore Template

Append if missing (repo-specific):

```gitignore
# .gitignore
.venv/
venv/
__pycache__/
*.pyc
.pytest_cache/
.mypy_cache/
.ruff_cache/
.cache/
.venv-workspace/
node_modules/
.next/
dist/
build/
.turbo/
coverage/
.nyc_output/
.DS_Store
```

```gitignore
# .cursorignore
**/.venv/**
**/venv/**
**/node_modules/**
**/.next/**
**/dist/**
**/build/**
**/.turbo/**
**/__pycache__/**
**/.cache/**
**/.venv-workspace/**
```

---

## Execution Order

1. For each repo: ensure `.gitignore` and `.cursorignore` have the template entries
2. Copy and adapt `icloud-migrate-commit.sh` — replace hardcoded batches with dynamic discovery
3. Run: `killall bird; sleep 5; nohup bash scripts/icloud-migrate-commit.sh &`
4. Monitor log; if hang, identify dir, add `--resume-from N` or exclude path, retry

---

## Dynamic Batch Discovery (Pseudocode)

```bash
# Discover top-level dirs (exclude .git, .venv, node_modules, etc.)
DIRS=( $(ls -d */ 2>/dev/null | grep -v -E '^\.(git|venv)|node_modules' | sed 's|/$||') )
N=0
for d in "${DIRS[@]}"; do
  ((N++))
  log "  [$N/${#DIRS[@]}] $d/ ($(find "$d" -type f 2>/dev/null | wc -l) files)"
  timeout 60 git add "$d" 2>/dev/null || { log "  HANG/SKIP: $d"; continue; }
  log "      -> done"
  sleep 2
done
git add .gitignore .cursorignore 2>/dev/null
git add -A -- ':!path/to/exclude'  # exclude known problematic dirs
```

---

## Reference: PM Repo Script (Template)

The PM script batches: .gitignore/.cursorignore, cursor-rules/, docs/, plans/, scripts/security/tests/, github-integration/, .cursor/, root files, then `git add -A` with exclusions. Other repos will have different structures — discover and adapt.
