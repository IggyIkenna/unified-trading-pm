---
doc_type: issue
title:
  "167/187 manual VM launchers have NO dedup/collision check — the fleet-cap the one relevant family DID have wasn't
  real per-shard dedup either"
summary: >-
  Determination for the dxy_duplicate_vm_billing_waste_ao_outage_2026_08_12.md follow-up todo: measured every
  scripts/vm/launch-*.sh in deployment-service (187 total) for any singleton/lock call. Only 20 have one at all. The ONE
  family directly implicated in the DXY incident (tradfi-bf-* OHLCV launchers, via ohlcv_check_singleton_lock) did have
  a check, but it was a FLEET CONCURRENCY CAP on the whole "^tradfi-bf-" prefix, not a per-shard dedup — every vm_name
  embeds a fresh run_ts, so two concurrent invocations of the SAME launcher covering the SAME shard both get distinct
  names and both pass the cap as long as the fleet stays under it. That gap is now fixed (see Todos). The other 166
  launchers (some already covered by lc_singleton_check/lc_acquire_singleton_lock, most with nothing) are out of scope
  for a single P2 task — audit-scope follow-up.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [deployment-service]
scope: [engineer, admin]
tags: [billing-waste, vm-duplicate, dedup, singleton-lock, vm-launcher]
related:
  - /plans/active/issues/dxy_duplicate_vm_billing_waste_ao_outage_2026_08_12.md
  - /codex/05-infrastructure/vm-launcher-runbook.md
  - /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md
parent_epic: infrastructure_master
source:
  "tradfi_satellite_ao_dispatch_batch13_2026_08_13.md todo (Source:
  dxy_duplicate_vm_billing_waste_ao_outage_2026_08_12.md), 2026-08-15"
assigned_vm: NA
created: 2026-08-15
resolved_by:
locked_by:
priority: P2
execution_scope: local-only
drift_direction: advance-code
depends_on: []
---

# 167/187 manual VM launchers lack a dedup/collision check

## What I found

Determination requested by `dxy_duplicate_vm_billing_waste_ao_outage_2026_08_12.md`'s P2 todo: "Determine whether any
manual-launcher-invocation path has a dedup/collision check against already-running VMs for the same shard."

Measured `deployment-service/scripts/vm/launch-*.sh` (187 scripts) for any call to `lc_singleton_check`,
`lc_acquire_singleton_lock`, or `ohlcv_check_singleton_lock`:

```
total launchers: 187
with some singleton/lock call: 20
```

**The family actually implicated in the DXY incident** — the 11 `launch-tradfi-bf-*-ohlcv-*.sh` scripts that source
`_tradfi-ohlcv-launcher-lib.sh` — DID call `ohlcv_check_singleton_lock` before this fix. But reading that function
showed it is a **fleet concurrency cap**, not a per-shard singleton:

```bash
ohlcv_check_singleton_lock() {
    ...
    running_count="$(gcloud compute instances list \
        --filter='name~"^tradfi-bf-" AND status=RUNNING' ...)"
    if (( running_count >= OHLCV_FLEET_CONCURRENCY_CAP )); then exit 1; fi
}
```

It counts ALL `tradfi-bf-*` VMs regardless of which shard they cover, and every `vm_name` embeds a fresh
`run_ts=$(date +%Y%m%d-%H%M%S)`, so two concurrent invocations of the identical launcher for the identical year-shard
produce two distinct names and BOTH pass the cap as long as total fleet size stays under `OHLCV_FLEET_CONCURRENCY_CAP`.
This is exactly the confirmed shape of the DXY incident (5 repeated invocations in ~20 minutes, 30 concurrent VMs
spanning the same 8 year-shards 3-5x over).

**The remaining 166 launchers**: 9 more (`lc_singleton_check`/`lc_acquire_singleton_lock` — a real prefix-based
singleton, or the atomic GCS-lock variant that also closes the list-then-create TOCTOU race) already had a genuine
per-launch-family dedup before this issue. The other ~166 have no dedup/collision mechanism of any kind — a duplicate
manual invocation of any of those launchers (accidental re-run, two concurrent operator sessions, a forgotten background
job) can freely stack concurrent VMs for the same shard with zero refusal, exactly as
`tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md`'s `wave_launcher.py` dedup-bug entry and this DXY incident
both independently demonstrated for two DIFFERENT launcher families in the same week.

## Why it matters

Confirmed 100%-preventable billing waste has now hit twice in one week via two unrelated launcher families
(`tradfi-bf-cme-ohlcv-1m-*`, 167 stray VMs; `tradfi-bf-ice-idx-ohlcv-24h-*`/DXY, 26+ stray VMs) — the specific mechanism
differed each time (an automated dispatcher's dedup bug vs. a manual-invocation fleet-cap-not-dedup gap), but the root
pattern is identical: nothing stops two invocations of the same launcher covering the same shard from both proceeding.
166 launchers still have this exposure.

## Recommended decision

Fixed the ONE family directly implicated in this incident now (bounded, deterministic — see Todos). Extending real
per-shard dedup to the other 166 launchers is genuinely audit-scope (each launcher has its own shard-identity naming
convention; some are one-shot/non-idempotent and would need per-launcher judgment on collision semantics, not a single
mechanical sweep) — too large for this task. Recommend a follow-up `/ag-closeout-audit`-style batch: triage the 166 by
launcher family, and for the idempotent-backfill families (the common case), route them onto
`lc_singleton_check`/`lc_acquire_singleton_lock` from `scripts/vm/lib/launcher_common.sh` (already the shared, proven
mechanism 9 launchers use) rather than inventing a new pattern per family.

## Todos

- [x] ✅ [SCRIPT] P2. Fix `ohlcv_create_vm` in `deployment-service/scripts/vm/_tradfi-ohlcv-launcher-lib.sh` to add a
      real per-shard collision check (strip the `-<run_ts>` suffix to recover the shard identity, refuse if a RUNNING VM
      already shares it) alongside the existing fleet-cap — closes the exact gap this DXY incident exploited, for all 11
      tradfi-bf-ohlcv launchers at once (shared lib, no per-launcher-file changes needed). **DONE 2026-08-15 —
      deployment-service@<pending, see plan Progress Log>.**
- [ ] [SCRIPT] P3. Triage the other ~166 launchers without any dedup check
      (`grep -L 'lc_singleton_check\| lc_acquire_singleton_lock\|ohlcv_check_singleton_lock' scripts/vm/launch-*.sh`) by
      launcher family; for idempotent-backfill launchers, wire in `lc_singleton_check`/`lc_acquire_singleton_lock`.
      Genuinely audit-scope — size as its own plan, do not attempt as a single todo.

## Progress Log

- **2026-08-15 (slot-5, backend_engineer)**: filed this issue doc with the measured 20/187 finding and shipped the
  bounded fix for the incident's own launcher family (tradfi-bf-ohlcv, 11 scripts via the shared lib).
