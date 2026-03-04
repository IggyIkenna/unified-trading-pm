# Rollout Ignore Files + Git History Purge

**Goal:** Roll out unified-trading-pm `.cursorignore` and `.gitignore` to all workspace repos, then purge from git history any files matching those patterns (credentials, secrets, build artifacts). After a fresh pull, those files no longer exist.

## Phase 1: Rollout ignore files

```bash
cd unified-trading-pm
bash scripts/rollout-ignore-files.sh              # dry-run
bash scripts/rollout-ignore-files.sh --execute     # copy to all repos
```

Then commit and push in each repo (or use quickmerge per repo):

```bash
# Per repo, after rollout:
cd <repo>
git add .cursorignore .gitignore
bash scripts/quickmerge.sh "chore: align .cursorignore and .gitignore with PM SSOT"
```

## Phase 2: Purge from history

**Prerequisites:**

- `git-filter-repo` installed: `pip install git-filter-repo` or `brew install git-filter-repo`
- Force-push permission: branch protection on `main` may need to be temporarily relaxed
- Team coordination: everyone must re-clone or `git fetch --all && git reset --hard origin/main` after purge

**Scripts:**

- `scripts/gitignore-purge-paths.txt` — patterns to remove (matches PM .gitignore)
- `scripts/purge-gitignore-from-history.sh` — runs filter-repo per repo

**Execution:**

```bash
cd unified-trading-pm
bash scripts/purge-gitignore-from-history.sh              # dry-run
bash scripts/purge-gitignore-from-history.sh --execute    # purge only (no push)
bash scripts/purge-gitignore-from-history.sh --execute --push  # purge + force push
```

**Per-repo (alternative):**

```bash
cd <repo>
git filter-repo --paths-from-file ../unified-trading-pm/scripts/gitignore-purge-paths.txt --invert-paths --force
git push --force-with-lease origin main
```

## Post-purge

- All team members: `git fetch --all && git reset --hard origin/main` (or re-clone)
- Open PRs and branches will have invalid history; recreate from new main
- Rotate any credentials that may have been committed (treat as compromised)

## Files created

| File                                      | Purpose                                        |
| ----------------------------------------- | ---------------------------------------------- |
| `scripts/rollout-ignore-files.sh`         | Copy .cursorignore and .gitignore to all repos |
| `scripts/gitignore-purge-paths.txt`       | Path patterns for git filter-repo              |
| `scripts/purge-gitignore-from-history.sh` | Run filter-repo per repo, optional push        |
