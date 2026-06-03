---
scope: [engineer]
---

# Feature Branch Workflow

**Last Updated:** 2026-02-28 **SSOT:** This document. Cross-refs: `always-use-quickmerge.mdc`,
`conventional-commits.mdc`, `library-versioning.mdc`, `path-dependency-ci.mdc`, `never-revert-local-changes.mdc`

This document defines the complete development workflow for feature branches across the 50+ repo workspace — from local
development through CI to main merge.

---

## Mental Model: Branch = Snapshot

When you check out a git branch or tag, `pyproject.toml` comes with it at that commit's version. The version in the file
IS the snapshot. You never need to manually edit version numbers on a branch — the git state already includes the right
toml.

```
git checkout v1.2.3          # pyproject.toml says version = "1.2.3" ✅
git checkout feat/rollback   # pyproject.toml says whatever it said at last commit ✅
# No manual toml editing needed on branches
```

---

## Branch Model

| Branch type             | Quickmerge behaviour                     | When to use                |
| ----------------------- | ---------------------------------------- | -------------------------- |
| `feat/*` or `feature/*` | QG only — no PR, branch pushed to remote | Active feature development |
| `staging`               | QG + auto-PR to main                     | Ready to integrate to main |
| `main`                  | Branch protection — no direct push       | Production                 |

**Promoting feature → main:**

```bash
git checkout staging
git merge feat/my-feature
bash scripts/quickmerge.sh "feat: my feature description"
# → quality gates run on staging → auto-PR to main → auto-merge when CI passes
```

**Nothing to commit on staging (everything worked first time):**

```bash
git commit --allow-empty -m "chore: promote feat/X to staging"
bash scripts/quickmerge.sh "chore: promote feat/X to staging"
```

---

## Conventional Commits (Required)

All commit messages must use the conventional format. The GitHub Action on main reads the prefix to determine the
version bump.

| Prefix                                         | Pre-1.0.0 bump (current) | Post-1.0.0 bump       | Example                              |
| ---------------------------------------------- | ------------------------ | --------------------- | ------------------------------------ |
| `feat:`                                        | minor (0.1.0 → 0.2.0)    | minor (1.2.0 → 1.3.0) | `feat: add ConfigReloader to UTS`    |
| `fix:`                                         | patch (0.1.0 → 0.1.1)    | patch (1.2.3 → 1.2.4) | `fix: correct tier boundary check`   |
| `feat!:` / `BREAKING CHANGE:`                  | minor (0.1.0 → 0.2.0) \* | major (1.x.x → 2.0.0) | `feat!: remove ConfigStore from UCI` |
| `chore:`, `docs:`, `refactor:`, `test:`, `ci:` | none                     | none                  | `chore: update .gitignore`           |

\* Pre-1.0.0: BREAKING is treated as minor — the version NEVER crosses to 1.0.0 automatically. `1.0.0` is only set when
all plan items for that repo/tier are done and the final quickmerge PR lands on main.

**Never bump version locally on branches.** The GitHub Action does it on merge to main.

---

## Dependency Cascade

When you have changes in multiple repos that depend on each other (e.g., T1 depends on T0 which you also changed),
quickmerge cascades automatically.

```bash
# You have changes in both unified-config-interface (T1) and unified-trading-services (T1)
# Run quickmerge on T1 (the higher-tier repo):
cd unified-trading-services
bash scripts/quickmerge.sh "feat: ConfigReloader extraction" --dep-branch "feat/config-reloader"
```

What happens:

1. Stage 1 detects `unified-config-interface` has local changes
2. **Cascades into UCI**: runs
   `quickmerge.sh "feat: ConfigReloader extraction" --dep-branch "feat/config-reloader" --quick` inside UCI
3. UCI's changes are committed and pushed to the `feat/config-reloader` branch
4. UTS quality gates run using UCI's local path dep (already updated)
5. UTS `feat/config-reloader` branch is pushed with a PR

Cascade order is topological: T0 always processed before T1, T1 before T2, etc., determined by
`workspace-manifest.json (SSOT)`.

**Local changes are NEVER discarded during cascade.** The stash/pop mechanism preserves everything.

---

## Never Revert Local Changes

When quickmerge detects a dependency conflict (dep has changes not on main), the **only valid response** is
`--dep-branch`. Never `git reset --hard`.

```bash
# ❌ FORBIDDEN — destroys your feature branch changes in the dep
cd unified-config-interface && git reset --hard origin/main

# ✅ CORRECT — preserves all changes, cascades automatically
bash scripts/quickmerge.sh "feat: X" --dep-branch "feat/X"
```

The local changes in the dependency repo ARE the feature. Discarding them defeats the entire purpose of the feature
branch.

---

## Versioning on Feature Branches

### Pre-Stable Policy (all repos, current state)

All repos are `0.x.x` until they pass a full quickmerge on `main` under the Phase 0-CI pipeline. **`1.0.0` = first
stable release = first successful CI-validated merge to main.**

- `0.x.y` preserves relative evolution (e.g. UTS `0.2.2` has more history than AC `0.1.0`)
- No repo should be `>=1.0.0` in `workspace-manifest.json` until it is proven stable on CI
- `pyproject.toml` versions in all repos must match the manifest (a CI check verifies this)

### Behaviour by location

| Location                           | Behaviour                                                                   |
| ---------------------------------- | --------------------------------------------------------------------------- |
| `pyproject.toml` on feature branch | Unchanged from last main merge — do NOT edit                                |
| `workspace-manifest.json`          | SSOT for all versions; all `0.x.x` until first stable CI merge              |
| Artifact Registry (production)     | Only receives clean semver (e.g. `0.1.1`, eventually `1.0.0`) on main merge |
| Artifact Registry (feature)        | Receives `0.1.0+feat-branch.sha` from feature Cloud Build                   |
| GitHub Action on main merge        | Auto-bumps pyproject.toml + workspace-manifest.json based on commit prefix  |

Feature branch artifacts use ephemeral version injection in the Cloud Build container (never committed):

```bash
# Cloud Build ephemeral step — only inside the container, never touches the repo
VERSION=$(grep '^version' pyproject.toml | sed 's/version = "//;s/"//')
BRANCH_TAG=$(echo $BRANCH_NAME | tr '/' '-' | cut -c1-20)
sed -i "s/version = \"$VERSION\"/version = \"$VERSION+$BRANCH_TAG.$SHORT_SHA\"/" pyproject.toml
python -m build --wheel
# Wheel: unified_config_interface-1.3.0+feat-config-reloader.abc123-py3-none-any.whl
```

PEP 440 local versions (`+`) are only matched by exact pin — they are never accidentally installed by `>=1.3.0`
constraints.

---

## CI: Feature Branch Dep Resolution

GitHub Actions clones dependencies using `${DEP_BRANCH:-main}` with a fallback:

```yaml
- name: Clone unified-config-interface
  run: |
    # Read dep-branch label from PR (set by quickmerge --dep-branch)
    DEP_BRANCH=$(gh pr view $PR_NUMBER --json labels \
      --jq '.labels[].name | select(startswith("dep-branch: ")) | ltrimstr("dep-branch: ")' \
      2>/dev/null || echo "")
    BRANCH="${DEP_BRANCH:-main}"
    # Fall back to main if branch doesn't exist in dep repo (already merged/deleted)
    if git ls-remote --heads https://github.com/org/unified-config-interface "$BRANCH" | grep -q "$BRANCH"; then
      git clone -b "$BRANCH" .../unified-config-interface ../unified-config-interface
    else
      git clone .../unified-config-interface ../unified-config-interface
    fi
```

**How the label gets there:** quickmerge Stage 5 adds a `dep-branch: feat/X` label to the PR body and label when
`--dep-branch` is set.

---

## Temporary Manifests (Dev Cycle Snapshots)

For complex multi-repo refactors where you want to share the "current state" of what branches are being tested:

Location: `unified-trading-pm/feature-manifests/*.json`

```json
{
  "name": "feat-config-reloader-extraction",
  "created_at": "2026-02-28T...",
  "description": "Moving ConfigReloader from UCI to UTS",
  "branches": {
    "unified-config-interface": "feat/config-reloader",
    "unified-trading-services": "feat/config-reloader"
  },
  "artifact_versions": {
    "unified-config-interface": "0.1.0+feat-config-reloader.abc123",
    "unified-trading-services": "0.2.2+feat-config-reloader.def456"
  },
  "status": "in_progress"
}
```

Cloud Build reads this file (clones `unified-trading-pm` via GH_PAT in pre-step) to resolve which branch/artifact to
install for each dependency.

---

## Refactor Scope (Multi-Repo Refactor Mode)

When doing a large multi-repo refactor where tests are intentionally failing:

In `unified-trading-pm/workspace-manifest.json`:

```json
"refactor_scope": {
  "active": true,
  "reason": "Extracting ConfigReloader from UCI to UTS — tests expected to fail until both repos pass",
  "in_flight_repos": ["unified-config-interface", "unified-trading-services"],
  "ci_mode": "warn-only",
  "started": "2026-02-28"
}
```

When `refactor_scope.active = true`:

- Quickmerge warns on test failures instead of exiting 1
- GitHub Actions posts a comment "refactor_scope active" but does not block merge
- Agents do NOT attempt to revert code or versions to fix tests

---

## Tier Ordering Invariant

**NEVER change service code without having a passing library tier it depends on.**

```
T0 green → T1 green → T2 green → T3 green → T4 (services) green → T5 (API) green → T6 (UIs) green
```

Within each tier, always work in dependency order (check `workspace-manifest.json`). Tiers have no inter-lib deps within
the same level — repos at the same tier can be worked in parallel.

## Meta-Flow Per Tier (always in this order)

```
STEP A: Fix deploy structure (cloudbuild.yaml, quality-gates.sh, pyproject.toml)
STEP B: Write/fix tests FIRST (import smoke test, unit tests, contract tests)
STEP C: Code rewrite (tier violations, type errors, import paths, QG violations)
STEP D: quickmerge --unit-only   ← fast feedback, catches critical issues
STEP E: quickmerge (full)        ← tier is only "green" when this passes
```

## Two-Step Quickmerge

```bash
# STEP D: fast feedback
bash scripts/quickmerge.sh "feat: rewrite UCI imports" --unit-only
# → lint + type check + unit tests only; skips integration tests + act
# → CI may fail on integration tests — expected and acceptable at this stage
# → catches: import errors, syntax errors, type errors, unit test regressions

# Fix any critical issues from --unit-only, then:

# STEP E: full validation
bash scripts/quickmerge.sh "feat: rewrite UCI imports"
# → all tests + act simulation; tier is "green" only when this passes
```

## Two-Pass Model (Agents and CI)

Agents and CI scripts should split quality validation into two passes to avoid re-running slow tests unnecessarily:

```bash
# Pass 1 — full quality gates (all checks)
bash scripts/quality-gates.sh
# → lint, format, tests, typecheck, codex, security — everything

# Pass 2 — quickmerge lightweight verify (no tests, no act)
bash scripts/quickmerge.sh "feat: ..." --agent
# → lint + format + typecheck + codex only
# → tests already passed in Pass 1; act is wasted overhead in automated sessions
```

`--agent` implies `--skip-tests` + skip act. It is **required** for all agent callers (Claude Code, `run-agent.sh`,
GitHub Actions). NEVER use `--quick` from an automated caller — use `--agent` so intent is documented.

To also skip typecheck in quickmerge (if it ran in Pass 1): `--agent --skip-typecheck`.

## Documentation & Config Repo Versioning

`unified-trading-pm` and `unified-trading-codex` are not deployed services, but they carry `pyproject.toml` with semver
versioning and a `version-bump.yml` GitHub Action. This serves three purposes:

1. **Audit trail**: know which version of docs/manifest was "reality" at any point in time
2. **Agent context**: Cursor agents operating on these docs know what version of the spec they are reading
3. **CI/CD validation**: the PM repo's version-bump also updates `workspace-manifest.json` versions map for its own
   entry

Same conventional commit rules apply. `chore:` and `docs:` do NOT bump version (no-op). `feat:` bumps minor, `fix:`
bumps patch. Same pre-1.0.0 safety: BREAKING never bumps to 1.0.0 within 0.x.x range.

**Cross-repo manifest sync:** PM's `version-bump.yml` updates its own entry in `workspace-manifest.json` directly (same
repo). For all other repos (codex, services, libraries), their `version-bump.yml` bumps their own `pyproject.toml` but
cannot push to the PM repo. The PM manifest is updated by either: (a) the PM `version-bump.yml` detecting a repository
dispatch event, or (b) a periodic sync workflow. Until cross-repo triggers are wired, pull the PM manifest manually
after each repo's main merge and check the `versions` map.

**All 53 repos** must have a `version-bump.yml` GitHub Action. This is propagated as part of Phase 0 Stream A
(quickmerge template propagation). Each workflow bumps the repo's own `pyproject.toml` (or `package.json` for UIs).

---

## `require-quality-gates` ruleset set + the one exemption (codified 2026-06-01)

Every active workspace repo carries a `require-quality-gates` repository **ruleset** (`target: branch`, condition
`~DEFAULT_BRANCH`, `bypass_actors: []`, rule `required_status_checks` → context
`Quality Gates (<repo>) / quality-gates-v2`, or the UI gate `… / quality-gates` for TS/Vite repos). It is the canonical
server-side gate; classic branch protection mirrors the same context (see § Branch model / `ci-cd-flow.md`).

**The single exemption is `agent-orchestrator`** — it is operator/agent tooling, not production trading code, so it
bypasses the production hardening path (its integration target axis is documented in CLAUDE.md § "Git discipline" /
`agent-orchestrator-overview.md`). It does NOT get a `require-quality-gates` ruleset.

**Per-repo prerequisite (HARD — DEADLOCK otherwise):** before creating a repo's ruleset, confirm its v2 job `name:`
emits `Quality Gates (<repo>) / quality-gates-v2` (NOT the hand-copied `alerting-service` name) AND a GREEN run exists
on the **default branch**. For **LDR-default repos** (`features-service`, `greeks-service`, `unified-trading-api`) the
v2 workflow MUST also trigger on `live-defi-rollout` (add it to `push`/`pull_request` branches, like features-service)
so the required check runs on the default branch — otherwise the ruleset blocks slot pushes to LDR.

Ruleset additions (the 7 non-`agent-orchestrator` repos surfaced 2026-06-01):

| Repo                          | Default br | Ruleset id | Status (2026-06-01)                                                             |
| ----------------------------- | ---------- | ---------- | ------------------------------------------------------------------------------- |
| `unified-trading-api`         | LDR        | 17135955   | ✅ active (LDR added to v2 triggers; green LDR run)                             |
| `ml-service`                  | main       | 17136124   | ✅ active (job-name `(alerting-service)`→`(ml-service)` fixed; green main)      |
| `features-service`            | LDR        | 17136160   | ✅ active (green LDR v2 already; LDR already in triggers)                       |
| `greeks-service`              | LDR        | —          | ⏳ v2-RED (MIN_COVERAGE=0 floor + codex + C901); GH_PAT secret provisioned      |
| `fund-administration-service` | main       | —          | ⏳ v2-RED (`uv sync` starlette↔utl conflict); caller rolled out                |
| `e2e-testing`                 | main       | —          | ⏳ v2-RED (14 ruff lint); caller rolled out                                     |
| `unified-trading-system-ui`   | main       | —          | ⏳ no UI gate yet — roll out `ui-quality-gates`; ruleset on `… / quality-gates` |

The 4 ⏳ rows are HARD-GATED on a green default-branch run first (never create the ruleset on a red repo — the required
check would be unsatisfiable and freeze the branch). Tracked per-repo in
`plans/active/cicd_contract_hardening_2026_06_01.md` § Phase 1.

### Zero human-approvals — the green gate IS the review (autonomous CI/CD, codified 2026-06-02)

**`required_approving_review_count = 0` on `main` + `staging`, fleet-wide.** For autonomous operation a green
`quality-gates-v2` required check is the merge criterion — a mandatory human approval on top blocks agent-opened PRs
from auto-merging (a green-gated PR sits `BLOCKED` waiting on an approval that never comes, since an author can't
approve their own PR and `enforce_admins` binds admins to the review). So the human-approval layer is removed;
**everything else stays**:

- the `require-quality-gates` ruleset (v2 context, `bypass_actors: []`) — REQUIRED; **no one (incl. admins) merges past
  a red gate**;
- `enforce_admins: true` — the gate binds everyone;
- "require a PR before merging" stays (`count = 0` still requires a PR — just no approval), so the PR + gate flow is
  intact.

Net: a green `quality-gates-v2` → the PR auto-merges, hands-off. SSOTs updated so it does not regress on
re-provisioning: `ops/branch-protection-template.json` (`required_approving_review_count: 0`),
`scripts/repo-management/admin-force-sync-all-to-main.sh` (`// 0` default). Operator decision 2026-06-02. Re-introduce
human review only as a deliberate per-repo policy, never the default. Tracked:
`plans/active/cicd_contract_hardening_2026_06_01.md`.

---

## Quick Reference

```bash
# Agent/CI — two-pass (recommended for all automated sessions)
bash scripts/quality-gates.sh                                         # Pass 1: full validation
bash scripts/quickmerge.sh "feat: ..." --agent                        # Pass 2: lint+format+typecheck+codex, no tests, no act
bash scripts/quickmerge.sh "feat: ..." --agent --skip-typecheck       # Pass 2: lint+format+codex only

# Human — feature branch work (auto --no-pr on feat/* branches)
bash scripts/quickmerge.sh "feat: add new adapter"

# Human — fast feedback: unit tests only (catches critical issues)
bash scripts/quickmerge.sh "feat: add new adapter" --unit-only

# Human — skip act only (tests still run)
bash scripts/quickmerge.sh "feat: add new adapter" --quick

# Feature with dep changes (cascade + branch isolation)
bash scripts/quickmerge.sh "feat: multi-repo change" --dep-branch "feat/my-feature"

# Force no-PR on any branch
bash scripts/quickmerge.sh "chore: update config" --no-pr

# Promote feature to main (via staging)
git checkout staging && git merge feat/my-feature
bash scripts/quickmerge.sh "feat: my feature description"

# NEVER
git reset --hard origin/main      # destroys local changes
bash scripts/quality-gates.sh     # bypasses dep validation + PR (use as Pass 1 only, not instead of quickmerge)
git push origin main              # bypasses branch protection
```

---

## Integration Testing Layers

Quickmerge runs Layers 0 and 1 as part of quality gates. Layers 2 and 3 run post-deploy.

| Layer | Scope                                                           | In quickmerge?                       |
| ----- | --------------------------------------------------------------- | ------------------------------------ |
| 0     | Contract alignment (AC↔UIC schema pairs)                       | Yes                                  |
| 1     | Schema robustness per-service                                   | Yes                                  |
| 1.5   | Per-component integration tests with mocked direct dependencies | Yes — last local gate before Layer 2 |
| 2     | Infrastructure verify (GCS, PubSub, IAM)                        | No — post-deploy                     |
| 3a    | Pipeline smoke (fast happy path)                                | No — post-deploy                     |
| 3b    | Full E2E (corner cases, auth, perf)                             | No — post-deploy                     |

**SSOT:** `06-coding-standards/integration-testing-layers.md`

---

## Periodic Reflog Audit

Weekly check for unintended `reset --hard` or `reset to origin/main`. Alerts via macOS notification on failure.

**SSOT:** `unified-trading-pm/docs/audit-reflog-scheduled-job.md`

| Action                    | Command                                                                                                                                                               |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Run manually (with alert) | `bash unified-trading-pm/scripts/repo-management/run-audit-reflog-with-alert.sh`                                                                                      |
| Start scheduled job       | `bash unified-trading-pm/scripts/repo-management/launchd/install-audit-reflog.sh` then `launchctl load ~/Library/LaunchAgents/com.unified-trading.audit-reflog.plist` |
| Cancel job                | `launchctl unload ~/Library/LaunchAgents/com.unified-trading.audit-reflog.plist`                                                                                      |
| Log                       | `/tmp/audit-reflog.log`                                                                                                                                               |

---

## Per-repo required-check matrix (post-v2 migration, 2026-05-29)

Workspace-canonical required check is **`quality-gates-v2`** (post-Option-D escape of the GitHub ghost cache). Per-repo
deviations documented here so future agents know what's expected without spelunking through `gh api`.

| Repo                                                                                                                                                                               | Default branch        | Branch protection (required) | Ruleset (required)                        | Notes                                                                         |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------- | ---------------------------- | ----------------------------------------- | ----------------------------------------------------------------------------- |
| unified-trading-pm                                                                                                                                                                 | main                  | `quality-gates-v2`           | `quality-gates-v2` (13647441)             | Hosts python-quality-gates-v2 callee                                          |
| unified-api-contracts                                                                                                                                                              | main                  | `quality-gates-v2`           | `quality-gates-v2` (13787580)             |                                                                               |
| unified-trading-library                                                                                                                                                            | main                  | `quality-gates-v2`           | `quality-gates-v2` (13787584)             |                                                                               |
| alerting-service                                                                                                                                                                   | main                  | `quality-gates-v2`           | `quality-gates-v2` (13787630)             |                                                                               |
| ml-service                                                                                                                                                                         | main                  | none                         | none                                      | No required checks today; future hardening                                    |
| features-service                                                                                                                                                                   | **live-defi-rollout** | `quality-gates-v2` (on LDR)  | none                                      | **Special: no `main` branch exists**                                          |
| batch-live-reconciliation-service                                                                                                                                                  | main                  | `quality-gates-v2`           | `quality-gates-v2` (13787691)             | Belt-and-suspenders — both layers                                             |
| execution-service                                                                                                                                                                  | main                  | none (branch prot empty)     | `check-staging-lock` + `quality-gates-v2` | Ruleset 13647462 (2-context Option A)                                         |
| instruments-service                                                                                                                                                                | main                  | none                         | `check-staging-lock` + `quality-gates-v2` | Ruleset 13787597                                                              |
| deployment-ui                                                                                                                                                                      | main                  | none                         | `check-staging-lock` + `quality-gates-v2` | Ruleset 13787657. **UI** — pw-smoke is additive enhancement, not enforced yet |
| unified-trading-system-ui                                                                                                                                                          | main                  | `quality-gates-v2`           | unknown (not surveyed)                    | **UI** — pw-smoke additive enhancement                                        |
| user-management-ui                                                                                                                                                                 | main                  | **N/A — repo ARCHIVED**      | **N/A — repo ARCHIVED**                   | Archived = stronger than protection (no pushes possible)                      |
| unified-trading-api                                                                                                                                                                | main                  | `quality-gates-v2`           | unknown (not surveyed)                    |                                                                               |
| (deployment-service, deployment-api, system-integration-tests, market-tick-data-service, client-reporting-api, trading-agent-service, greeks-service, fund-administration-service) | main                  | (not surveyed)               | (not surveyed)                            | Workspace-wide hygiene sweep follow-up                                        |

**Why two layers?** GitHub provides two independent enforcement systems — **branch protection** (legacy, repo-level
default-branch config) and **rulesets** (newer, multi-branch + multi-condition). Some workspace repos use one, some
both. The 2-context rulesets on execution/instruments/deployment-ui require BOTH `check-staging-lock` AND
`quality-gates-v2` for merge — canonical workspace pattern is to use both layers where both configured.

**Provenance**: matrix populated 2026-05-29 during ci_canonical_v2_migration Phase 4 +
workspace_repo_branch_protection_gaps Phase 3. Not-surveyed repos warrant a follow-up workspace-wide
branch-protection-hygiene sweep.
