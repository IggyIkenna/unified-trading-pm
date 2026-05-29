---
scope: [engineer]
created: 2026-05-15
---

# CI/CD Flow

> SSOT for the workspace's CI/CD pipeline architecture. Covers the quickmerge two-pass model, branch policy, agent vs
> human paths, and the dep-branch flow for cross-repo feature isolation.
>
> Cross-references: `CLAUDE.md` § "Git discipline"; `codex/08-workflows/dependency-cascade.md`;
> `codex/08-workflows/version-graduation.md`.

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
Pass 1 — Quality Gates (MANDATORY — FULL run, no skip flags)
  bash scripts/quality-gates.sh
  • ruff format + check (lint + format)
  • pytest (tests, coverage)
  • basedpyright (type check)
  • STEP 5.x codex compliance (60+ rules)
  • pip-audit (CVE scan)
  On clean exit with NO skip flags → writes .qg_last_passed_sha = git rev-parse HEAD
  Partial runs (--skip-tests / --skip-lint / --skip-codex / --quick) do NOT write sentinel

Pass 2 — Quickmerge (--agent fast-path)
  bash scripts/quickmerge.sh "feat: description" --agent --files '...'
  • Reads .qg_last_passed_sha — verifies SHA matches current HEAD
    SHA mismatch / sentinel missing → EXIT 1: "Run quality-gates.sh on current HEAD first"
    SHA match → skips all Pass 2 QG re-runs (sentinel IS the guarantee)
  • commits, creates PR targeting staging, enables auto-merge
  • --to-staging routes to staging instead of main (for breaking changes)
```

**Why the sentinel?** Eliminates the staleness gap where an agent calls quickmerge after incremental edits without
re-running Pass 1. The SHA check is the enforcement mechanism — no partial run can fake a full pass. Pass 2 no longer
re-runs lint/typecheck/codex: the sentinel guarantees they passed.

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

## Full CI/CD Flow (LDR → Cloud Build)

Canonical flow is in `codex/08-workflows/deployment-flow.md`. Summary:

```
LDR: quality-gates.sh (full) → sentinel written → quickmerge --agent (SHA check)
  → staging PR (auto-merge on) → workspace-qg GHA (full, ubuntu-latest, fresh deps)
  → on failure: #ci-failures Slack alert with PR link + source/target branch
  → staging merge → semver-agent bump → staging-to-main
  → main: Cloud Build (docker build + QG --quick inside image + CVE scan + push)
```

**workspace-qg GHA vs local quality-gates.sh**: same script, different env. GHA resolves deps against published git tags
on Linux; local uses workspace path deps on macOS. The dep-resolution gap is the only meaningful divergence — caught at
the staging PR boundary.

**workspace-qg triggers**: `push: [main, staging]` + `pull_request: [main, staging]`. LDR is explicitly excluded — local
QG + sentinel is the only gate on LDR (by design).

---

## Agent vs Human Paths

| Operation          | Agent                                                    | Human                                                    |
| ------------------ | -------------------------------------------------------- | -------------------------------------------------------- |
| Run quality gates  | `bash scripts/quality-gates.sh` (FULL — no skip flags)   | Same                                                     |
| Quickmerge         | `bash scripts/quickmerge.sh "..." --agent --files '...'` | `bash scripts/quickmerge.sh "..."`                       |
| SHA sentinel check | Automatic in `--agent` — blocks on mismatch              | Not enforced (human responsibility)                      |
| Push to LDR        | quickmerge pushes branch, creates staging PR             | Same via quickmerge                                      |
| Promote LDR → main | ❌ NOT ALLOWED (operator only)                           | Via staging→main PR flow                                 |
| Dep-branch work    | ❌ NOT ALLOWED (`--dep-branch` human-only)               | `bash scripts/quickmerge.sh "..." --dep-branch "feat/X"` |
| Version graduation | ❌ NOT ALLOWED                                           | `gh workflow run request-major-bump.yml ...`             |
| Kill-switch arming | ❌ NOT ALLOWED                                           | Manual via deployment-service API                        |
| Wallet key ops     | ❌ NOT ALLOWED                                           | Hardware wallet / KMS console                            |

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
| Quickmerge flags + mechanics       | `codex/08-workflows/deployment-flow.md`                                  |
| Dep-branch full flow               | `codex/08-workflows/dependency-cascade.md`                               |
| Version graduation                 | `codex/08-workflows/version-graduation.md`                               |
| Per-tab worktrees (slot isolation) | `codex/05-infrastructure/per-tab-worktrees.md`                           |
| QG two-pass model (detailed)       | `codex/06-coding-standards/quality-gates.md` § "Two-Pass Workflow Model" |
| Branch policy enforcement          | `.cursorrules` § "Git"                                                   |

---

## Workspace-qg unified trigger surface (codified 2026-05-16 — Phase B rollout complete)

**SSOT template**: `unified-trading-pm/scripts/workflow-templates/workspace-qg.yml.tmpl`. All 21 Python service repos
now use this canonical template; per-repo `quality-gates.yml` files have been retired.

### Pre-cutover trigger surface (until 2026-05-23)

```yaml
on:
  push:
    branches: [main, staging, live-defi-rollout]
  pull_request:
    branches: [main, staging]
  workflow_dispatch:
```

**Rationale**: strict superset of the 5 trigger patterns that existed across repos before unification:

- `[main, staging, live-defi-rollout]` (9 repos pre-unification — fires hundreds/day on LDR)
- `[main]` only (9 repos — slow cadence; now elevated to LDR cadence)
- `[main, staging]` (2 repos)
- `[main, develop]` (1 repo — stale `develop` retired)

### Post-cutover trigger surface (after 2026-05-23 — LDR retired)

Edit the template to:

```yaml
on:
  push:
    branches: [main, staging]
  pull_request:
    branches: [main, staging]
  workflow_dispatch:
```

Then run `bash unified-trading-pm/scripts/workflow-templates/rollout-workflow-templates.sh` to propagate the change to
all 21 repos. Estimated time: ~5 min.

### Roll-forward future workflow changes

1. Edit the template in `unified-trading-pm/scripts/workflow-templates/workspace-qg.yml.tmpl`.
2. Run `rollout-workflow-templates.sh --template workspace-qg.yml.tmpl` (rendered to every Python repo).
3. Each repo's owner commits + pushes the auto-rendered `workspace-qg.yml`. Auto-FF mirror lands on LDR.
4. Per-repo first run on the change surfaces any pre-existing QG failures (per Findings Triage HARD RULE, "pre-existing
   is NOT a triage criterion — fix now if you can").

### dep_repos auto-rendering

`{{DEP_REPOS}}` is substituted at rollout time from `workspace-manifest.json` (canonical). Hand-crafted phantom-dep
references in old per-repo files (`unified-cloud-interface` / `unified-config-interface` / `unified-internal-contracts`

- duplicate `unified-trading-library`) were silently corrected by the Phase B migration; future drift is prevented by
  the manifest-as-SSOT contract.

### Continuous verification

| Field                   | Value                                                                                                                         |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| Item                    | CI workflow consistency across 21 Python repos                                                                                |
| Cutover criterion       | All 21 repos have `workspace-qg.yml` (not `quality-gates.yml`); template rendered from PM SSOT                                |
| Continuous verification | `gh workflow list --repo IggyIkenna/<repo> --json name` returns `workspace-qg`; per-repo `quality-gates.yml` no longer exists |
| Cadence                 | Weekly drift-check (one repo per day across the week)                                                                         |
| Owner                   | Slot 1 main pre-cutover; post-cutover cron VM (see `plans/epics/infrastructure_master.md` for VM assignment)                  |
| Last verified           | 2026-05-16 (Phase B rollout — see `plans/active/issues/workspace_qg_yml_redesign_2026_05_15.md` § "PHASE B FULLY ROLLED OUT") |
