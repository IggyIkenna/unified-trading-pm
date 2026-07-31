---
doc_type: issue
title: deployment-ui unit-coverage floor RED — FALSE POSITIVE from stale slot node_modules (not a real regression)
summary:
  deployment-ui's `quality-gates.sh` unit-test coverage step appeared to fail the global 70%/67%/70%/64%
  (lines/functions/statements/branches) threshold at ~24-25% actual. RESOLVED — this was a stale per-slot `node_modules`
  artifact from the 2026-07-29 npm→pnpm migration (`de5b7af`) + jsdom→happy-dom switch (`ee269ec`) — `happy-dom` was
  never installed in the pre-existing slot clones, causing every component test to error at setup and contribute ~0
  coverage. `pnpm install` fixes it locally (coverage returns to 71.85/64.32/68.05/74.04 — all above floor). CI on
  `live-defi-rollout` was GREEN throughout (`quality-gates-v2` run 30570814932, 2026-07-30T18:32:00Z, success) — this
  never actually broke shipping, only local/slot QG reproduction for clones not yet reinstalled post-migration.
status: resolved
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-ui]
scope: [engineer]
tags: [coverage, quality-gates, deployment-ui, repo-blocker, false-positive, pnpm-migration]
related: []
created: 2026-07-31
parent_epic: deployment_and_user_management_master
priority: P2
source: [features_service_coverage_and_script_canon_2026_06_10.md script-canon sweep, slot 10 session 2026-07-31]
assigned_vm: planning
resolved_by: slot 11 (cicd escalation agt-1e392c, repo-blocker RB-398669f0), 2026-07-31
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

## What I found (original, slot 10)

While shipping a purely mechanical change (adding the required `# Epic:`/`# Lifecycle:`/`# Delete-when:`
lifecycle-marker header to 4 `deployment-ui/scripts/*.sh` files, per `/codex/06-coding-standards/script-homes.md` —
`scripts/` is explicitly excluded from coverage by design), `bash scripts/quality-gates.sh` failed at the unit-test
coverage step:

```
Statements   : 24.42% ( 693/2837 )
Branches     : 16.16% ( 401/2480 )
Functions    : 22.58% ( 168/744 )
Lines        : 25.11% ( 634/2524 )
ERROR: Coverage for lines (25.11%) does not meet global threshold (70%)
ERROR: Coverage for functions (22.58%) does not meet global threshold (67%)
ERROR: Coverage for statements (24.42%) does not meet global threshold (70%)
ERROR: Coverage for branches (16.16%) does not meet global threshold (64%)
```

Verified pre-existing (not caused by this session's diff) per the RULES.md § 4b protocol:
`git stash push --include-untracked`, re-ran `npx vitest run --coverage` on the clean tree at `origin/live-defi-rollout`
HEAD — reproduced the same failure, coverage numbers within noise. `git stash pop` restored the diff afterward.

## ROOT CAUSE (corrected, slot 11 cicd escalation agt-1e392c, 2026-07-31)

The stash+clean-tree reproduction protocol proves a diff didn't CAUSE the red — it does **not** prove the red reflects
real repo state, because it still runs against whatever `node_modules` happens to be on disk in that slot clone. That's
exactly the gap here:

- `de5b7af` (2026-07-29) migrated deployment-ui npm→pnpm: deleted `package-lock.json`, added `pnpm-lock.yaml`.
- `ee269ec` (2026-07-29) switched `vitest.config.ts` `environment: "jsdom"` → `"happy-dom"` and added `happy-dom` as a
  devDependency.
- Neither commit re-ran `pnpm install` inside already-checked-out slot clones (slot provisioning —
  `scripts/dev/slot-cron-ff-pull.sh` — only `git pull`s, it never refreshes `node_modules`), and `quality-gates.sh` /
  `base-ui.sh` never runs an install step either — it assumes `node_modules` is already in sync.
- Result: on any slot clone checked out before 2026-07-29 and not manually reinstalled, `happy-dom` is **MISSING**
  (`npx vitest run` reports `MISSING DEPENDENCY happy-dom`). Every component test errors at environment setup, so the
  corresponding source files execute ~0 lines under coverage instrumentation — producing the ~24-25% reading. This is
  not a real coverage regression; it's every DOM-dependent test silently failing to even start.
- Fix verified live in slot 11's clone: `pnpm install` (378 packages were missing/stale) → re-ran
  `npx vitest run --coverage` → **Statements 71.85% / Branches 64.32% / Functions 68.05% / Lines 74.04%** — all four
  clear the 70/64/67/70 floor (branches passes by a thin 0.32pp margin — worth a proper follow-up test to widen the
  buffer, not urgent).
- Independently confirmed the repo was **never actually broken**:
  `gh run list --branch live-defi-rollout --repo IggyIkenna/deployment-ui` shows `quality-gates-v2` GREEN on every run
  since the migration (latest: run `30570814932`, success, 3m22s, 2026-07-30T18:32:00Z) — CI always does a fresh
  install, so it never hit the stale-`node_modules` trap.

**No code or config fix was needed or made in deployment-ui.** `git status` is clean; nothing was committed. The wall
was a slot-local environment artifact, not a repo defect — closing repo-blocker RB-398669f0 accordingly.

## Why it mattered

Any slot whose deployment-ui clone predates 2026-07-29 and hasn't been reinstalled will reproduce this same false red on
its NEXT local QG run (not just slot 10's) — this is a recurring trap for the whole fleet, not a one-off. Original "why
it matters" framing (blocks all shipping) was itself part of the misdiagnosis: shipping was never actually blocked at
the integration-branch/CI level, only local pre-commit QG reproduction in stale clones.

## Follow-up (prevent recurrence — NOT done in this escalation, filed as real todos)

- [ ] [BACKEND] P2. `unified-trading-pm/scripts/quality-gates-base/base-ui.sh`: harden the `node_modules` freshness
      check (currently only checks `node_modules/.bin/vitest` exists, ~line 230) to detect a stale/incomplete install
      after a lockfile change — e.g. `pnpm install --frozen-lockfile` (fast no-op when already in sync) as an early
      guard step, or at minimum compare `pnpm-lock.yaml` mtime/hash against an install marker and `log_fail` with the
      correct remedy command (currently says "run npm install", wrong for pnpm-migrated repos). Roll out via
      `rollout-quality-gates-unified.py` to all UI repos, not just deployment-ui. Repo: unified-trading-pm.
- [ ] [SCRIPT] P3. `unified-trading-pm/scripts/dev/slot-cron-ff-pull.sh`: consider a lightweight post-pull check per
      repo (e.g. lockfile hash changed since last install → warn or auto `pnpm install`) so a package-manager / lockfile
      migration doesn't silently desync every long-lived slot clone. Repo: unified-trading-pm.
