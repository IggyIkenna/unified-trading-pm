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

## Canonical required check name (post-Option-D, 2026-05-29)

The workspace-canonical required status check is **`quality-gates-v2`** (NOT the legacy `quality-gates`).

**Why the rename?** A 2026-05-26 bad-YAML incident in `python-quality-gates.yml` caused GitHub to cache a "BuildFailed"
ghost workflow registration that fired startup_failure on every subsequent push across 10+ workspace repos. The fix
(Option D, shipped 2026-05-29 via `ci_canonical_v2_migration_2026_05_29` plan) renames the entire caller+callee chain to
new file paths (`quality-gates-v2.yml` + `python-quality-gates-v2.yml`) and a new job key (`quality-gates-v2`) so GitHub
registers a fresh validation context that bypasses the cached ghost.

**Status across workspace** (per `codex/06-coding-standards/feature-branch-workflow.md` § "Per-repo required-check
matrix"):

- v2 deployed on canonical branches of all **17** workspace repos (includes the 10 ghost-affected + 3 priority: PM, UAC,
  UTL + remaining service repos)
- Branch protection / ruleset enforcement updated to require `quality-gates-v2` across all 17 repos
- Sentinel-write logic (commit `a8b758c58`) ensures local `quality-gates.sh` writes `.qg_last_passed_sha` on clean
  full-pass exit, enabling quickmerge `--agent` fast-path

**v1 cleanup**: v1 caller workflows (`quality-gates.yml`, `workspace-qg.yml`) on the rotated repos are now orphaned but
NOT yet deleted — held until GH Support ticket #4422570 resolves the cached ghost (after which the v1 callee
`python-quality-gates.yml` can also be removed). Tracked in `ci_canonical_v2_migration_2026_05_29.md` Phase 5.

---

## Branch-protection mechanism — RULESET + classic, both (codified 2026-06-01)

Every workspace repo carries **TWO** server-side protections on `main` (and usually `staging`), and BOTH must agree or
merges silently dead-lock:

1. **Ruleset** `require-quality-gates` (and `require-staging-lock-check` on staging) — the **canonical** mechanism.
   Required context is **derived from the live workflow file** (`<job name:> / quality-gates-v2`), so a wrong job
   `name:` = a context no run ever emits = a permanently-unsatisfiable required check. Verify with
   `scripts/repo-management/verify_branch_protection_check_names.py`; apply with `pin_branch_protection_rulesets.py`
   (derives from `--ref`, default `live-defi-rollout`). **`pin --apply` re-pins main AND staging from the same ref** —
   don't run it globally unless v2 exists on staging too, or it blocks staging.
2. **Classic branch protection** `required_status_checks` — legacy, still enforced. Historically pinned to the **bare**
   context `quality-gates-v2` (or v1 `quality-gates`), which **no Actions run emits** (the real context has the
   `Quality Gates (<repo>) / ` prefix) → blocks every **non-admin** merge while `enforce_admins=false` lets admins
   bypass (masking it). Fix: `gh api -X PATCH repos/IggyIkenna/<repo>/branches/<br>/protection/required_status_checks`
   with `checks=[{context:"Quality Gates (<repo>) / quality-gates-v2"}]`. Swept workspace-wide 2026-06-01.

**`enforce_admins`** (classic) makes the required check bind admins too — so once on, you can no longer admin-bypass a
red/blocked branch. Only enable it on a branch whose v2 is **green** (enabling on red blocks all merges). Target state
(Phase 2): true on every protected `main`. `[skip ci]` automation reaches `main` via the staging→main PR flow, so
enforce_admins does not strand it.

## Force-push vs let-CI/CD — the decision rule (codified 2026-06-01)

**Admin force (relax ruleset + `enforce_admins` → do it → RE-ENABLE, guaranteed) is for the initial clean-slate ONLY,
where the normal flow is structurally circular** — the branch's required check cannot run / be satisfied by a PR:

- adding a **missing / wrong-named** `quality-gates-v2.yml` to a branch whose ruleset already requires the v2 context;
- **FF-ing a default branch strictly behind** its integration branch to resolve drift + land workflow files
  (`merge-base --is-ancestor main LDR` true → relax → `git push origin <ldr-sha>:refs/heads/main` → re-enable);
- landing the workflow / GHA / versioning **fixes themselves** when the branch is blocked by the breakage being fixed.

**Otherwise, let CI/CD do it (normal PR → quickmerge auto-merge, NO admin):** any code/test/coverage/lint/codex fix that
_makes the gate pass_ goes through a PR and auto-merges green. Once a branch has a working green v2 gate, all changes
use the normal flow. **Invariants:** never leave a ruleset `enforcement=disabled` or `enforce_admins` off; resolve
conflicts ON `live-defi-rollout` (never a throwaway branch — that re-drifts); blocked-on-actionable-red is the SAFE
direction (protected > unprotected).

## Operational status — promotion automation (snapshot 2026-06-01; being repaired)

The **PR→staging gate** (`quality-gates-v2`) is healthy + enforced workspace-wide. The **staging→main half is being
revived** — as of 2026-06-01 it was found DEAD and bypassed via admin force-merge. Progress (2026-06-01 evening):

- **Loud alerting — SHIPPED** (`scripts/repo-management/ci_failure_watcher.py` +
  `.github/workflows/ci-failure-watcher.yml`, cron `*/15`): cross-repo `workflow_run` failure→recovery transitions
  (stateless, recency-guarded) + auto-merge-stuck PR poller → Slack `#ci-failures` via `notify-slack.yml`. This is the
  antidote to the silent rot that hid the breakage.
- **`sit-debounce` notify guard — SHIPPED**: `notify-slack.yml` now skips (exit 0) on any non-`https://` webhook —
  notifications are best-effort, never fail the caller (was raising uncaught `ValueError: unknown url type` on a
  masked/misconfigured `SLACK_WEBHOOK_URL` inherited via `secrets: inherit`).
- **`staging_versions` baseline — RESTORED** in `workspace-manifest.json` (was reset to `{}`; semver reads it as the
  bump baseline). Repopulated from the per-repo `versions` SSOT.
- `semver-agent` — **SHIPPED 2026-06-01**: trigger `quality-gates-v2`; covers **24 repos**; callee contract requires
  `timeout-minutes: 135` + `if: failure()||cancelled()` cleanup step. Rolled out to all repo default branches.
- SIT chain (`sit-gate` ← `sit-lock`; `staging-to-main` ← `staging-validated`) — PM-side mapped: `sit-debounce-trigger`
  (cron `*/2`) dispatches `staging-changed` to the `system-integration-tests` repo; the dead link is on the SIT-repo
  side (zero `sit-gate` runs ⇒ `sit-lock`/`staging-validated` never re-dispatched). Cross-repo trace remaining.
- orchestrator-dispatch escalation for judgment cases (conflict / label-mismatch / SIT-triage) via the setup-token
  worker fleet — NOT API credits in GHA — remaining.

**Gotcha (local ≠ CI, codified 2026-06-01):** `quality-gates.sh` runs prettier + numpy/pandas/UTL-resolved typecheck
locally that the CI clone does NOT reproduce — prettier only runs in `FIX_MODE` (skipped under CI's `--no-fix`), and CI
clones a thin `dep_repos` set so cross-repo imports (numpy, `unified_trading_library`) go unresolved → a local green can
hide a CI-red basedpyright/test. Always read the CI log on a campaign-PR red; don't infer from a local pass.

**Live SSOT for this repair + the full ordered backlog**: `plans/active/cicd_contract_hardening_2026_06_01.md` § "Phase
6 — CONSOLIDATED HAND-OFF EXECUTION PLAN".

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

## Workflow-file editing — GH_TOKEN scope (HARD RULE, codified 2026-06-01)

Any edit to a `.github/workflows/*.yml` file **requires a GH_TOKEN with `Workflows: write` scope**. The default keyring
token (standard `gh auth login` session) does NOT carry this scope and will return a
`403 Resource not accessible by integration` error when trying to push or create a PR that modifies workflow files.

**Required before touching any workflow file:**

```bash
source unified-trading-pm/scripts/workspace/load-gh-token.sh
```

This script fetches the Workflows-write-capable token from Secret Manager (SM secret `GH_PAT`) and exports it as
`GH_TOKEN` + `GITHUB_TOKEN`. All subsequent `gh` + `git push` calls in the same shell session use it.

**Verification**: `verify-slot-host-symmetry.sh` checks that a valid `GH_TOKEN` with Workflows scope is present on the
host. A missing / insufficient token shows as a failure in the symmetry check output.

**Scope**: applies to any PR or direct push that adds, modifies, or renames a file under `.github/workflows/` in any
workspace repo. PRs that touch only non-workflow files do not require the elevated token.

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

## quality-gates-v2 — canonical required-check name (codified 2026-05-29)

**Job key**: `quality-gates-v2` (was `quality-gates` in v1 callers — retired).

The v1 `quality-gates` check context was poisoned by GitHub's server-side BuildFailed ghost cache (GH Support ticket
#4422570). Option D escape (2026-05-29): rename BOTH caller workflow file AND job key, reference a new callee path
(`python-quality-gates-v2.yml`). GitHub has no prior cache entry for the new context.

**Canonical workflow files** (as of 2026-05-29):

| Repo type    | Caller                                   | Callee                                                                                          |
| ------------ | ---------------------------------------- | ----------------------------------------------------------------------------------------------- |
| PM           | `.github/workflows/quality-gates-v2.yml` | `.github/workflows/python-quality-gates-v2.yml` (local ref — PM calls itself)                   |
| Service repo | `.github/workflows/quality-gates-v2.yml` | `IggyIkenna/unified-trading-pm/.github/workflows/python-quality-gates-v2.yml@live-defi-rollout` |

**Required status check across all repos**: `quality-gates-v2` (all 17 repos on v2 as of 2026-06-01).

**v1 cleanup status**: `quality-gates.yml` / `workspace-qg.yml` deleted from PM, UAC, UTL, alerting-service, ml-service,
execution-service (2026-05-30). Keep `python-quality-gates.yml` in PM until GH ticket clears.

**Plan reference**: `plans/active/ci_canonical_v2_migration_2026_05_29.md`

---

## Workspace-qg unified trigger surface (codified 2026-05-16 — Phase B rollout complete)

**SSOT template**: `unified-trading-pm/scripts/workflow-templates/quality-gates-v2.yml.tmpl` (renamed from
`workspace-qg.yml.tmpl`; the v1 `python-quality-gates.yml` is kept only as a ghost-target until GH Support ticket
#4422570 clears). All **17** Python service repos now use this canonical template (main + staging branches all on
`quality-gates-v2`); per-repo `quality-gates.yml` files have been retired.

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
all 17 repos. Estimated time: ~5 min.

### Roll-forward future workflow changes

1. Edit the template in `unified-trading-pm/scripts/workflow-templates/quality-gates-v2.yml.tmpl`.
2. Run `rollout-workflow-templates.sh --template quality-gates-v2.yml.tmpl` (rendered to every Python repo).
3. Each repo's owner commits + pushes the auto-rendered `workspace-qg.yml`. Auto-FF mirror lands on LDR.
4. Per-repo first run on the change surfaces any pre-existing QG failures (per Findings Triage HARD RULE, "pre-existing
   is NOT a triage criterion — fix now if you can").

### dep_repos auto-rendering

`{{DEP_REPOS}}` is resolved at rollout time via **BFS-transitive closure over `pyproject.toml` `path="../<repo>"`
editable dependencies** — i.e. the set of repos that appear as `path =` deps, transitively. This means the rendered
`dep_repos` list reflects what the repo _actually_ depends on at the code level. `workspace-manifest.json` is consulted
only as a **fallback** when the BFS graph is incomplete or a repo is not yet declared as an editable dep.

Hand-crafted phantom-dep references in old per-repo files (`unified-cloud-interface` / `unified-config-interface` /
`unified-internal-contracts` — duplicate `unified-trading-library`) were silently corrected by the Phase B migration;
future drift is prevented by the pyproject-BFS contract.

### Continuous verification

| Field                   | Value                                                                                                  |
| ----------------------- | ------------------------------------------------------------------------------------------------------ |
| Item                    | CI workflow consistency across 17 Python repos (main + staging, all on `quality-gates-v2`)             |
| Cutover criterion       | All 17 repos have `quality-gates-v2.yml`; required check = `quality-gates-v2`; v1 callers deleted      |
| Continuous verification | `gh run list --repo IggyIkenna/<repo> --workflow quality-gates-v2 --limit 1` shows `completed success` |
| Cadence                 | Weekly drift-check (one repo per day across the week)                                                  |
| Owner                   | vm-cross-cutting (ci_canonical_v2_migration plan)                                                      |
| Last verified           | 2026-06-01: all 17 repos on v2; semver-agent SHIPPED (24 repos, trigger `quality-gates-v2`)            |
