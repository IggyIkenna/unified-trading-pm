---
scope: [engineer]
created: 2026-05-15
---

# CI/CD Flow

> SSOT for the workspace's CI/CD pipeline architecture. Covers the quickmerge two-pass model, branch policy, agent vs
> human paths, and the dep-branch flow for cross-repo feature isolation.
>
> Cross-references: `CLAUDE.md` § "Git discipline"; `codex/08-workflows/dependency-cascade.md`;
> `codex/08-workflows/version-graduation.md`; `cursor-rules/venv-usage-ssot.mdc`.

---

## Three-Tier Branch Model

```
feat/* ──────► (QG only, no PR, no CI)
                    │
staging ────────────► PR CI + SIT
                    │
main ───────────────► always stable; triggers version bump + image build
```

| Branch                    | Purpose                                                 | CI runs               | Who merges                |
| ------------------------- | ------------------------------------------------------- | --------------------- | ------------------------- |
| `feat/*`                  | Feature isolation; dep-branch for cross-repo work       | None (local QG only)  | quickmerge `--agent`      |
| `staging`                 | Convergence point for breaking changes + SIT            | Full CI               | quickmerge `--to-staging` |
| `main`                    | Always stable; semver bump + image build triggered here | Full CI + image build | quickmerge (standard)     |
| `live-defi-rollout` (LDR) | Active rollout branch (workspace-specific May-23)       | None (local QG only)  | slot quickmerge `--agent` |
| `tab/hk/<N>`              | Per-slot worktree branch                                | None                  | local work                |

**Never** push directly to `main` — always via quickmerge. The quickmerge script is the **only** sanctioned merge path
(it runs QG, handles dep-branch resolution, and respects the two-pass model).

---

## Two-Pass Workflow Model (the unit of work)

Every shippable unit goes through exactly two passes:

```
Pass 1 — Quality Gates
  bash scripts/quality-gates.sh
  • ruff format + check (lint + format)
  • pytest (tests, coverage)
  • basedpyright (type check)
  • STEP 5.x codex compliance (60+ rules)
  Must exit 0 before Pass 2

Pass 2 — Quickmerge
  bash scripts/quickmerge.sh "feat: description" --agent
  • ruff + basedpyright re-run (fast — no tests)
  • commits, creates PR, merges to target branch
  • --agent skips act + tests (already passed in Pass 1)
  • --to-staging routes to staging instead of main
```

**Why two passes?** Pass 1 runs tests with xdist parallelism (slow); Pass 2 skips tests to avoid double-running.
Separating them ensures tests run once (and catch regressions) while the merge path stays fast.

---

## Quickmerge Variants

```bash
# Standard (feat → main)
bash scripts/quickmerge.sh "feat: description"

# Breaking change (feat → staging)
bash scripts/quickmerge.sh "feat!: breaking" --to-staging

# Cross-repo feature isolation (deps on non-main branch)
bash scripts/quickmerge.sh "feat: work" --dep-branch "feat/X"

# Agent session (skip act + tests — Pass 1 already ran)
bash scripts/quickmerge.sh "feat: work" --agent

# Human shortcut (skip act, keep tests)
bash scripts/quickmerge.sh "feat: work" --quick
```

**`--dep-branch`** is human-only — it pins the dep resolver to a non-main branch. Agents must not use it (agents always
merge to LDR where deps are on main).

**`--agent`** is for agent sessions — it skips the GitHub Actions simulation (act) and test re-run. Only valid if Pass 1
(full QG) has already completed and exited 0.

---

## Dep-Branch Flow (Cross-Repo Feature Isolation)

When a feature spans multiple repos (e.g. `unified-trading-library` → `execution-service`):

```
Step 1: Ship UTL change to feat/my-feature
  cd unified-trading-library
  bash scripts/quickmerge.sh "feat: new UTL API" --to-staging

Step 2: Wire execution-service on the same feat branch
  cd execution-service
  # Update pyproject.toml to depend on feat/my-feature
  bash scripts/quickmerge.sh "feat: wire new UTL API" --dep-branch "feat/my-feature"

Step 3: Converge on staging
  # Both repos converge; integration test runs
  bash scripts/quickmerge.sh "feat!: new UTL API + wiring" --to-staging

Step 4: Promote to main
  # UTL merges first (lower tier), then execution-service
  bash scripts/run-version-alignment.sh
  bash scripts/quickmerge.sh "release: new UTL API" (UTL)
  bash scripts/quickmerge.sh "release: wire new UTL API" (execution-service)
```

**Rule**: Never use `--dep-branch` in agent sessions. Agents always work on repos whose deps are already on main.

---

## Version Bump Flow (Semver Agent)

Semver is managed entirely by the semver-agent GitHub Action — never bump manually.

| Commit prefix                         | Triggers                      | Result        |
| ------------------------------------- | ----------------------------- | ------------- |
| `feat:`                               | MINOR bump on `0.x.x`         | 0.1.0 → 0.2.0 |
| `fix:` / `chore:` / `docs:`           | PATCH bump                    | 0.1.0 → 0.1.1 |
| `feat!:` or `BREAKING CHANGE:` footer | MAJOR bump (after 1.0.0)      | 1.0.0 → 2.0.0 |
| `feat!:` on `0.x.x`                   | MINOR bump (pre-1.0.0 policy) | 0.1.0 → 0.2.0 |

**Version graduation (1.0.0)**:
`gh workflow run request-major-bump.yml --repo IggyIkenna/<repo> -f proposed_version="1.0.0"` → comment `/approve`. Full
SSOT: `codex/08-workflows/version-graduation.md`.

---

## Full CI/CD Flow (main → prod)

```
1. Developer/agent: bash scripts/quality-gates.sh  (Pass 1)
2. Developer/agent: bash scripts/quickmerge.sh "..." --agent  (Pass 2)
   → creates PR → CI runs:
      a. ruff + basedpyright
      b. pytest (full suite, not just unit)
      c. STEP 5.x compliance (same as local QG)
      d. dependency alignment check
3. PR merges to main → semver-agent bumps version → image build triggered:
      a. Cloud Build: test-in-image → vulnerability scan → push image
      b. OR GitHub Actions: build + push to Artifact Registry
4. Deployment-service polls new version → deploys to staging VM
5. SIT smoke tests fire (L2 infrastructure verify tier)
6. Manual promotion (or auto-promote if configured): staging → prod
```

**Agents never reach step 4+** — agents push to LDR, not main. The full CI/CD flow runs when the operator promotes LDR
to main.

---

## Agent vs Human Paths

| Operation          | Agent                                      | Human                                                    |
| ------------------ | ------------------------------------------ | -------------------------------------------------------- |
| Run quality gates  | `bash scripts/quality-gates.sh`            | Same                                                     |
| Merge to branch    | `bash scripts/quickmerge.sh "..." --agent` | `bash scripts/quickmerge.sh "..."`                       |
| Push to LDR        | `git push origin HEAD:live-defi-rollout`   | Same                                                     |
| Promote LDR → main | ❌ NOT ALLOWED (operator only)             | `bash scripts/admin-sync-to-main.sh`                     |
| Dep-branch work    | ❌ NOT ALLOWED                             | `bash scripts/quickmerge.sh "..." --dep-branch "feat/X"` |
| Version graduation | ❌ NOT ALLOWED                             | `gh workflow run request-major-bump.yml ...`             |
| Kill-switch arming | ❌ NOT ALLOWED                             | Manual via deployment-service API                        |
| Wallet key ops     | ❌ NOT ALLOWED                             | Hardware wallet / KMS console                            |

---

## CI Verification After Push

After every push to a branch with CI:

```bash
# Check CI status
gh run list --branch <branch> --repo IggyIkenna/<repo> --limit 5

# Inspect failures
gh run view <run-id> --log-failed
```

Pushes to `feat/*` / `live-defi-rollout` → **no remote CI**. Quality enforced locally via `quality-gates.sh`. Pushes to
`main` / PRs → CI runs. Always verify CI green before reporting "shipped".

---

## Conditional Push Protocol (Multi-Agent Environment)

With 8+ slots running in parallel, always check for incoming commits before pushing:

```bash
git fetch origin <branch>
# If 0 incoming → push freely
git log HEAD..origin/<branch> --oneline
# If any incoming → STOP → rebase first
git rebase origin/<branch>
# Then push
git push origin HEAD:<branch>
```

**Never** `git push --force` or `--force-with-lease` to LDR. Always rebase. Rebase conflicts mean another slot edited
the same file — resolve with their changes in mind (likely their work should be preserved).

---

## SSOT Pointers

| Topic                              | SSOT                                                                     |
| ---------------------------------- | ------------------------------------------------------------------------ |
| Quickmerge flags + mechanics       | `cursor-rules/workspace-workflow.md`                                     |
| Dep-branch full flow               | `codex/08-workflows/dependency-cascade.md`                               |
| Version graduation                 | `codex/08-workflows/version-graduation.md`                               |
| Per-tab worktrees (slot isolation) | `codex/05-infrastructure/per-tab-worktrees.md`                           |
| QG two-pass model (detailed)       | `codex/06-coding-standards/quality-gates.md` § "Two-Pass Workflow Model" |
| Branch policy enforcement          | `.cursorrules` § "Git"                                                   |
