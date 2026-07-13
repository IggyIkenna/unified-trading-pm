---
doc_type: issue
title:
  qg-host-governor K=1 + high live-defi-rollout commit cadence makes unified-trading-pm quickmerge structurally
  unwinnable during busy periods
summary: >
  Shipping a 1-file unified-trading-pm fix via the normal quickmerge flow took 8 failed attempts over ~50 minutes.
  quality-gates.sh on this repo took 400-900s per run because qg-host-governor's shared token bucket is configured
  QG_HOST_CONCURRENCY=1 (not the CLAUDE.md-documented floor of 2), so runs queue behind every other slot's QG. Meanwhile
  live-defi-rollout received a new commit roughly every 60-180s from other slots (heavy docs(plans) + fix traffic this
  session). Every time local QG finished green, quickmerge's auto-rebase picked up a newer HEAD first, invalidating the
  just-written sentinel before Stage 3 could check it — a race that gets LESS winnable the longer QG takes, not more.
  Landed this one fix via the CLAUDE.md scripts/** carve-out (operator-approved, BLK-b6ed5e28) rather than keep retrying
  indefinitely.
status: open
nature: notes
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [qg-governor, contention, quickmerge, race-condition, host-resource-contention]
related: [plans/active/issues/mtds_adapter_contract_regression_stale_baseline_2026_07_13.md]
created: 2026-07-13
parent_epic: infrastructure_master
priority: P2
source: mtds_adapter_contract_regression_stale_baseline-001 dispatch, slot 3, 2026-07-13
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: infra
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-13
locked_by:
resolved_by:
---

# qg-host-governor K=1 vs. high branch churn — quickmerge race for unified-trading-pm

## What I found

Shipping `scripts/quality_gates/adapter_contract_baseline.yaml` (a 1-file regen, no code) to `unified-trading-pm`
required 8 quickmerge attempts:

1. Ran `bash scripts/quality-gates.sh --no-fix` → green, sentinel written at HEAD=X.
2. Ran `quickmerge.sh --agent` → Stage 0 auto-rebases onto a newer `origin/live-defi-rollout` HEAD (another slot pushed
   in the interim) → Stage 3 rejects: sentinel (X) != new HEAD (Y).
3. Repeat from 1.

`bash scripts/quality-gates-base/qg-host-governor.sh --status` showed `K=1` (`QG_HOST_CONCURRENCY=1` set in the session
env), not the CLAUDE.md-documented `max(2, floor(cores/4))` floor (`nproc`=16 on this host → floor(16/4)=4, well above
the `>=2` floor). With only 1 host-wide token, `quality-gates.sh` on `unified-trading-pm` queued 30s-840s behind other
slots' QG runs before even starting its own ~60-90s of actual work — total wall time 400-900s per attempt. One attempt
(`qg_pm_run5`) passed every individual gate but FAILED the wall-clock meta-gate itself
(`Quality gates must complete in <600s (took 893s)`) purely because the queue wait counts toward `DUR`.

Meanwhile `live-defi-rollout` (this session, ~10 active slots) received a new commit roughly every 60-180s. A 400-900s
QG window against a 60-180s commit-arrival cadence means the probability of zero commits landing during the window is
low — the race gets structurally _worse_ the more contended the host is, which is exactly when slots most need to ship
the fix (many slots calling `bash scripts/quality-gates.sh` at once is often itself the underlying cause of the failures
they're trying to fix).

## Why it matters

- Any future single-file `unified-trading-pm` fix (QG-config regens, baseline files, dependency floors) that arrives
  during a high-churn window will hit the same race. This session's fix specifically qualified for the CLAUDE.md
  `scripts/**` direct-push carve-out, so it had an escape hatch — but that carve-out doesn't cover arbitrary PM content
  (docs, non-scripts config), and isn't meant to be reached for routinely.
- The wall-clock meta-gate (`MAX_DURATION=600` for PM) can fail an otherwise-fully-green run purely due to queue wait,
  which is a false negative unrelated to the change under review.

## Recommended decision (not mine to make — routing to infra/operator)

- Consider whether `QG_HOST_CONCURRENCY=1` is an intentional RAM-pressure choice for this session's host, or a
  drifted-from-default setting — CLAUDE.md's own text documents a `>=2` floor and
  `≤2 full QGs at once (max(2, floor(cores/4)))` as the intended shared-host policy.
- Consider excluding `qg_governor_acquire` wait time from the `MAX_DURATION` wall-clock check (measure actual gate work,
  not queue time) so contention doesn't fail the meta-gate on an otherwise-green run.
- Consider whether quickmerge's sentinel-then-rebase ordering could be inverted for low-risk, single-file, non-code
  changes (rebase-then-verify against the FINAL rebased HEAD in one shot) to shrink the exposure window.

## Todos

- [ ] [INFRA] P2. Investigate whether `QG_HOST_CONCURRENCY=1` (vs. the CLAUDE.md-documented `>=2` floor) is intentional
      for this host; if not, restore the floor or document why 1 is correct here. (repo: unified-trading-pm,
      scripts/quality-gates-base/qg-host-governor.sh)
- [ ] [INFRA] P2. Consider excluding `qg_governor_acquire` queue-wait time from the `MAX_DURATION` wall-clock check in
      `scripts/quality-gates-base/base-service.sh` (~line 3637-3654) so host contention can't fail an otherwise
      fully-green run. (repo: unified-trading-pm)
