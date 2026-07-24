---
doc_type: issue
title: workspace-qg CI startup_failure — GitHub BuildFailed ghost + cached validation failures
summary:
status: resolved
nature: record
asset_group: [infrastructure]
stage: [meta]
repos:
  [
    alerting-service,
    batch-live-reconciliation-service,
    client-reporting-api,
    deployment-api,
    deployment-service,
    deployment-ui,
  ]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-26
source: [workspace_qg_sweep_2026_05_23.md (archived)]
last_updated: 2026-05-29
remediation_plan: plans/active/ci_canonical_v2_migration_2026_05_29.md
parent_epic: infrastructure_master
priority: P2
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

> **2026-06-01 RESOLVED (obsolete — superseded by v2 migration)**: Verified on LDR — affected repos (alerting-service,
> features-service, …) now ship **`quality-gates-v2.yml`** as their CI workflow and the legacy **`workspace-qg.yml`
> ghost no longer exists** in-repo. The v1 `workspace-qg` BuildFailed-ghost this issue tracked is gone; v2 is canonical
> (per `ci_canonical_v2_migration_2026_05_29` + the v1-retirement on 2026-05-30). **No GitHub Support action needed**
> (operator confirmed). Archive this issue.
>
> **Residual (one real finding, P2)**: `ml-service` is MISSING `quality-gates-v2.yml` (alerting + features have it) —
> ml-service is not running v2 quality-gates in CI. Roll the v2 workflow template to ml-service
> (`scripts/workflow-templates/` → `rollout-workflow-templates.sh`). Tracked here; fold into the v2-migration plan's
> coverage check.

> **2026-05-29 status**: Operator-acked plan-of-record is
> [`plans/active/ci_canonical_v2_migration_2026_05_29.md`](../ci_canonical_v2_migration_2026_05_29.md) (parent epic
> `infrastructure_master`). Implements **Option D** below (v2 caller + v2 callee + new job-key rotation). Operator
> verbatim 2026-05-29: "you yourself need to do all the work and then get PM repo, then UAC then UTL fully working off
> those... following the new canonical form with quality gates initially bypassed AFTER WE ARE SURE THEY PASSED LOCALLY
> IN FULL as per new canonical".
>
> **New canonical CI flow SSOT**: `/codex/08-workflows/ci-cd-flow.md` (sentinel-based two-pass: full local QG writes
> `.qg_last_passed_sha` → quickmerge --agent verifies SHA match → push to staging → PR auto-merges on workspace-qg green
> → semver-agent bump → staging-to-main → Cloud Build on main).

## What I found

6 service repos have persistent `startup_failure` on workspace-qg CI runs after a bad PM commit window (19:15–20:58 UTC
May 26). GitHub has cached "BuildFailed" validation state for these specific workspace-qg workflow registrations. This
is a **GitHub server-side infrastructure issue**, not fixable by changing workflow file content.

**Affected repos** (startup_failure on every dispatch/push):

- alerting-service (ghost: 283775571, real wf: 277289280)
- ml-service (ghost: 283725320, real wf: 280028487)
- features-service
- batch-live-reconciliation-service
- execution-service
- instruments-service
- **unified-api-contracts** (ghost: 283776088 — confirmed 2026-05-27T12:58Z on staging push; was missing from original
  list)

**Repos working normally** (success/failure/queued — no startup_failure):

- strategy-service ✅ success
- market-tick-data-service ✅ success
- deployment-service ✅ success
- deployment-api ✅ success
- client-reporting-api (failure = QG checks failed, not startup_failure)
- ml-inference-service (queued — startup passes, waiting for runner)
- ml-training-service (queued — startup passes, waiting for runner)

## Why it matters

Workspace-qg badge is broken for 6 repos. Cannot use `gh run list` to verify CI green before merging PRs in those repos.
**Does NOT block local development** — `bash scripts/quality-gates.sh` exits 0 locally for all affected repos.

## Root cause diagnosis

**Timeline:**

- 14:39–14:56 UTC: alerting-service workspace-qg SUCCESS (PM reusable workflow working)
- 15:37 UTC: ml-service workspace-qg running (jobs start, QG checks fail — startup OK)
- 20:25 UTC: PM commit f2f836647 adds bad trailing comment to python-quality-gates.yml
- 20:51 UTC: alerting-service push to main triggers workspace-qg → startup_failure → BuildFailed ghost 283775571 created
- 20:58 UTC: PM commit 7ca446080 removes the trailing comment (PM workflow restored)
- 21:24+ UTC: All dispatches to affected repos get startup_failure (both ghost and real workflows)

**Why ml-inference-service is fine**: Its workspace-qg registration (ID 277973103) was unaffected — no dispatch during
the bad window. Its workspace-qg.yml is IDENTICAL to alerting-service's except service name in comments. Clear proof the
issue is per-registration, not per-file-content.

**Verified NOT the cause** (all tried, none fixed startup_failure):

- GH_PAT required:true vs required:false in PM workflow
- Removing/adding col-0 trailing comments in PM workflow
- Removing dispatch-cloud-build job from caller
- Deleting and re-adding workspace-qg.yml on LDR
- Renaming workspace-qg.yml → workspace-qg-v2.yml (GitHub registration tracks by file path in main, not LDR)
- Multiple PM workflow content changes to force re-validation

## Investigation update — 2026-05-27 slot-1

**Option B tried and ruled out (2026-05-27T11:30–12:00 UTC):**

Attempted to rename `workspace-qg.yml` → `workspace-qg-v2.yml` in alerting-service and quickmerge to main. Result:
**workspace-qg-v2.yml (brand new registration) also gets startup_failure immediately on first trigger.**

Root cause confirmed: GitHub caches the callee validation result for
`IggyIkenna/unified-trading-pm/.github/workflows/python-quality-gates.yml@live-defi-rollout` per caller workflow
registration. Any new registration that uses this callee is ALSO cached as BuildFailed on its very first trigger.
Renaming creates a fresh registration, but it gets contaminated on first push to main (which immediately triggers and
caches the BuildFailed callee).

**Evidence**: workspace-qg-v2.yml (new ID) → push to main at 11:44 UTC → startup_failure at 11:45 UTC. Run 26509150899
confirms the new registration got BuildFailed immediately.

**Why ml-inference-service works**: Its workspace-qg.yml is NOT on main (HTTP 404 confirmed). Dispatches to
`--ref live-defi-rollout` with no main-branch registration bypass the startup validation entirely (GitHub runs LDR
content without the main-registration validation path).

**Additional damage from investigation**: alerting-service now has:

- workspace-qg.yml on main: ghost 283775571 + real registration 277289280 (startup_failure)
- workspace-qg-v2.yml on main: new registration (also startup_failure from first trigger) Both staging and main merged
  (PRs #13, #14) — staging is now synced to main.

**No code-level fix possible**: The callee validation cache is a GitHub server-side artifact that persists regardless of
file renames, deletions, or content changes in the caller.

**Option C tried and ruled out (2026-05-27T12:03 UTC):**

Tested `workspace-qg-v3.yml` — a fresh file NEVER on main, no ghost, no registration. Pushed to LDR as commit `3bb7a78`.
Result: push triggered ghost 283775571 (run 26509913630) → startup_failure. workspace-qg-v3.yml itself did not trigger
at all (no push trigger in file; workflow_dispatch requires file on default branch → 404).

Confirms: the ghost fires on EVERY push to live-defi-rollout regardless of which file changed. The ghost's trigger
conditions (push + workflow_dispatch) are baked into GitHub's server-side registration and cannot be changed from LDR.

**Final conclusion** (2026-05-27): callee cache is global (not per-registration), AND ghost fires on every push
regardless of file changes. Both mechanisms require GitHub server-side intervention. GitHub Support (Option A) was
filed.

> **2026-05-29 SUPERSEDED by Option D below** — operator directive to roll out a code-level fix via the new canonical CI
> flow (caller AND callee renamed simultaneously, new job key, branch-protection rotation) rather than continue waiting
> on GH Support ticket #4422570. See § "Option D" + the remediation plan
> [`plans/active/ci_canonical_v2_migration_2026_05_29.md`](../ci_canonical_v2_migration_2026_05_29.md).

## Option D: caller+callee rename WITH new job key (operator-acked 2026-05-29)

**Why Options B and C failed**: they renamed only ONE end of the chain (the caller workspace-qg.yml). GitHub's cache
keys on the **callee path** (`python-quality-gates.yml@live-defi-rollout`) — so any new caller that references the same
callee inherits the BuildFailed validation cache on first trigger.

**Option D design** (must change BOTH ends + the required-check name):

1. **New caller**: `.github/workflows/quality-gates-v2.yml` — new `name:` field + new job key (e.g.
   `quality-gates-2026-06`)
2. **New callee**: `.github/workflows/python-quality-gates-v2.yml` — new `name:` + new `workflow_call:` signature. The
   v2 caller references the v2 callee — **zero reference to the v1 callee path**, so GitHub has no prior cache key to
   hit
3. **Required-check rotation**: drop v1 `quality-gates` from main branch protection (frees blocked PRs immediately) →
   wait for v2 to register on first PR-against-main trigger → add v2 job key (`quality-gates-2026-06`) as new required
   check
4. **Optional Plan-B**: if v2 ALSO ghosts (cache keys deeper than path), inline QG steps directly in the v2 caller. One
   job, no reusable. GitHub can't ghost what doesn't reference anything

**Operational sequencing** (per `/codex/08-workflows/ci-cd-flow.md` canonical flow):

1. Local `bash scripts/quality-gates.sh` IN FULL (no skip flags) → writes `.qg_last_passed_sha` sentinel
2. `quickmerge.sh "msg" --agent` verifies sentinel SHA matches HEAD → PR to staging → auto-merge
3. After staging→main lands, rotate branch protection to v2 check
4. Verify v2 reports cleanly on next PR

**Affected repos** (per "What I found"): PM (canonical host), UAC, UTL prioritized in this plan; alerting-service,
ml-service, features-service, batch-live-reconciliation-service, execution-service, instruments-service, deployment-ui
as Phase 4 rollout.

**Note on Option B's failed evidence**: Option B's caller-rename used a fresh CALLER but same CALLEE
(`python-quality-gates.yml`). Option D differs by renaming the CALLEE too. Worth re-testing with this diff; if still
ghosts, Plan-B (inline) is the escape hatch.

## Recommended decision

### Option A: GitHub Support (fastest, safest) ← FILED 2026-05-27

**Ticket**: https://support.github.com/ticket/personal/0/4422570

Contact GitHub Support at https://support.github.com:

- **Repo**: IggyIkenna/alerting-service
- **Issue**: BuildFailed ghost workflow ID 283775571 is firing on every push/PR and returning startup_failure. Also,
  real workspace-qg workflow ID 277289280 consistently returns startup_failure even though the workflow file is valid
  (PyYAML + actionlint pass). The reusable callee (PM's python-quality-gates.yml) works fine for repos without cached
  failure state (ml-inference-service ID 277973103 queues successfully).
- **Request**: Clear the BuildFailed ghost 283775571 and reset the validation cache for workflows 277289280 AND any new
  registration created for workspace-qg-v2.yml (added 2026-05-27 during investigation). Also reset the callee validation
  cache for `IggyIkenna/unified-trading-pm/.github/workflows/python-quality-gates.yml@live-defi-rollout` — the
  startup_failure is caused by a cached bad validation of this callee that poisons ANY new registration.
- **Repeat for**: ml-service (ghost 283725320, real 280028487), features-service, batch-live-reconciliation-service,
  execution-service, instruments-service (find their ghost IDs via
  `gh run list --branch live-defi-rollout --workflow workspace-qg`).

### Option B: Rename workspace-qg.yml in each affected repo's main branch

This forces a new workflow registration (new ID, no cached failure). Requires quickmerge per repo:

1. On LDR: rename `.github/workflows/workspace-qg.yml` → `.github/workflows/workspace-qg-v2.yml`
2. Quickmerge to staging → main (creates new workflow registration)
3. Verify dispatch works (queued instead of startup_failure)
4. Update PM rollout template to use `workspace-qg-v2.yml` filename
5. Rollout to all 20 repos

Downsides: Significant ceremony per repo. CI badge URL changes. Rollout template drift risk.

### Option C: Wait

GitHub's validation cache may expire naturally. No known TTL — could be 24–72 hours or indefinite. Lowest effort but
unknown timeline.

**Recommendation**: Option A (GitHub Support) — fastest and cleanest.

## Local QG status (not blocked)

All repos that were worked on this session have local QG passing:

- features-service ✅ (2c1fe688 — deep import fix: `from unified_trading_library import resolve_bucket_name`)
- ml-service ✅ (cd266ff — asyncio.run() fix: 4 locations in test_cli_handlers_coverage.py)
- alerting-service ✅ (previously verified)
