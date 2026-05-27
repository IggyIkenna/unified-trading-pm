---
title: workspace-qg CI startup_failure — GitHub BuildFailed ghost + cached validation failures
created: 2026-05-26
author: slot-1 (ikenna)
source:
  - workspace_qg_sweep_2026_05_23.md (archived)
---

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

## Recommended decision

### Option A: GitHub Support (fastest, safest)

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
