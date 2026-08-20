---
doc_type: issue
title: >-
  `backfill-defi-legacy-datatype-fold-` relaunch: DeFi manifest consolidator confirmed genuinely caught up, but 2/2
  relaunch attempts failed for distinct VM-infra reasons (zero-heartbeat zombie-reap, then a real OOM under `--workers
  24`) — worker count fixed, dex_swaps fold still not actually re-run to completion
summary: >-
  Per `defi_manifest_allow_stale_fallback_incomplete_for_long_pause_2026_08_07.md`'s [DATA] P1 todo, verified the DeFi
  manifest consolidator has genuinely caught up (a real `read_availability_index(...)` call for `(defi, dex_swaps,
  captured)` WITHOUT `MANIFEST_ALLOW_STALE_FALLBACK` succeeded: 3,454,808 rows across 9 venues — consistent with the
  doc's ~3.46M-row expectation, a dramatic contrast to the 2026-08-07 false-completion's 46,263 rows/4 venues) and
  attempted the relaunch. Both attempts today failed, but NOT via the stale-fallback/false-completion mechanism the
  source doc guards against — two distinct, genuine VM-infra failures: (1) `backfill-defi-legacy-datatype-fold-
  20260815-001819` never wrote a heartbeat or `run.log` at all and was reaped by `vm_zombie_watchdog.py` (verdict
  `zombie_no_heartbeat`) ~20min after launch — root cause not found (VM was already deleted by the time this was
  investigated, no serial console available); (2) `backfill-defi-legacy-datatype-fold-20260815-004142` DID start cleanly
  (heartbeat + run.log confirmed) but the fold script itself was OOM-killed (`rc=137`, `mem_pct=90.9%`, `cpu_pct=100%`)
  after ~6 minutes — root-caused: the launcher hardcoded `--workers 24`, DOUBLE the fold script's own tested default of
  12 (`fold_legacy_dex_pools_swaps_rate_indices_2026_08_04.py --workers`'s own `default=12`), on an `e2-standard-4` (4
  vCPU / 16GB) box. Fixed the launcher to `--workers 12` (matching the script's own default) — shipped
  `deployment-service@7480588f57`. Per RB-INFRA-RELAUNCH's `≤2/(vm-prefix,day)` bound, did NOT attempt a 3rd relaunch of
  this prefix today; the actual dex_swaps/dex_pools/rate_indices fold re-run (the source doc's underlying ask) is still
  NOT complete.
status: open
nature: issue
asset_group: [defi, infrastructure]
stage: [data]
repos: [deployment-service, market-tick-data-service, unified-trading-library]
scope: [engineer, admin]
tags:
  [
    manifest-consolidator,
    vm-launcher,
    zombie-watchdog,
    oom,
    workers-oversubscription,
    rb-infra-relaunch,
    defi,
    dex-swaps,
    fold-script,
  ]
related:
  [
    /plans/archive/2026_08/defi_satellite_ao_dispatch_batch13_2026_08_13.md,
    /plans/active/issues/defi_manifest_allow_stale_fallback_incomplete_for_long_pause_2026_08_07.md,
    /plans/archive/2026_08/issues/defi_rebuild_vm_oom_root_cause_and_relaunch_carveout_2026_08_10.md,
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
  ]
created: "2026-08-15"
author: unknown
last_updated: "2026-08-20"
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.25
source: >-
  AO-dispatched satellite batch todo (/plans/archive/2026_08/defi_satellite_ao_dispatch_batch13_2026_08_13.md), the
  "relaunch dex_swaps fold without --allow-stale-fallback" item — precondition (consolidator freshness) was verified and
  met, but the relaunch itself hit unrelated VM-infra failures.
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
context_scope:
  [
    deployment-service/scripts/vm/launch-backfill-defi-legacy-datatype-fold-vm.sh,
    deployment-service/scripts/vm/vm_zombie_watchdog.py,
    market-tick-data-service/scripts/fold_legacy_dex_pools_swaps_rate_indices_2026_08_04.py,
    /plans/active/issues/defi_manifest_allow_stale_fallback_incomplete_for_long_pause_2026_08_07.md,
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
  ]
---

# `backfill-defi-legacy-datatype-fold-` relaunch: consolidator fresh, but VM infra failed twice (2026-08-15)

## What I found

**Consolidator freshness — CONFIRMED genuinely caught up.** Direct evidence (not just log inference):

- `gcs_describe_object` on `_index/availability_index.parquet` (bucket
  `market-data-tick-defi-prd-central- element-323112`): 6.66GB, `last_modified=2026-08-14T23:02:42Z`.
- At the time of the first check (00:12Z), the consolidated blob was ~4200s stale and a `consolidator.lock` blob's
  `started_at` was stuck at the SAME timestamp across two reads ~20s apart (age growing 1:1 with wall clock) despite
  `gcloud run jobs executions list --job=uts-prod-manifest-consolidator-market-data-defi` showing real ~40s
  "successfully completed" executions every ~60-70s throughout that window — i.e. the cron was alive but not actually
  advancing the lock/blob. This self-resolved within ~1 minute of the first observation (a fresh lock with a new
  `started_at` appeared, a real merge ran to completion) — did not chase further since it was transient and outside this
  todo's scope; flagging here in case it recurs (possible race in the writer's own stale-lock-reclaim path, since the
  write-side `_LOCK_TTL_SECONDS` default is only 300s — the lock should have been reclaimed within ~5min of going stale,
  not ~70min).
- Direct real read (no `MANIFEST_ALLOW_STALE_FALLBACK`):
  `read_availability_index(bucket, columns=[...], filters=[("capture_status","==","captured"),("data_type","==","dex_swaps")])`
  succeeded, returning **3,454,808 rows across 9 venues** (AERODROME_V3, BALANCER, CAMELOT_V3, CURVE, PANCAKESWAP_V3,
  SUSHISWAP, SUSHISWAP_V3, UNISWAP_V2, UNISWAP_V3) — consistent with the source doc's ~3.46M-row/22-venue expectation
  (venue count differs, plausibly real population drift over the intervening week of DeFi canonicalization work, not a
  freshness artifact given the row-count match). This is the correct verification method for "has the consolidator
  genuinely caught up" — a real filtered read either succeeds cleanly or raises `ManifestConsolidatorStaleError` loudly;
  there is no silent-partial-success mode without the flag.

**Relaunch attempt 1 — `backfill-defi-legacy-datatype-fold-20260815-001819` (00:18Z–00:39Z): zero-heartbeat zombie.**
Launched via `launch-backfill-defi-legacy-datatype-fold-vm.sh` (default args, no `--allow-stale-fallback`, no `--only`).
20 minutes later, `vm-logs/.../` for this VM contained ONLY `LAUNCH_PARAMS.json` — no `run.log`, no
`WATCHDOG_TRACE.log`, no `EXIT_STATUS`, meaning the startup script never reached its log-tee stage.
`gcloud compute operations list` confirmed a `delete` operation by `uts-prd-sa@...` at `00:39:59Z` — the automated
`vm-zombie-watchdog` (global defaults `--min-age=15min`/`--heartbeat-stale=15min`; no per-prefix override for this
launcher's `backfill-defi-legacy-datatype-fold-` prefix in `PREFIX_IDLE_THRESHOLDS`) correctly classified this as
`zombie_no_heartbeat` and reaped it — the watchdog behaved as designed given zero heartbeat ever appeared. Root cause of
WHY the heartbeat/log pipeline never started is NOT found (VM was already gone by the time this was investigated; no
serial console retained after deletion). Not reproduced on attempt 2.

**Relaunch attempt 2 — `backfill-defi-legacy-datatype-fold-20260815-004142` (00:41Z–00:52Z): real OOM.** Same launcher,
same args. This time heartbeat + `run.log` DID start correctly (`UAC OK: 390 leagues`, deploy steps all succeeded per
serial console). At `00:52:30Z`, the deployment archive's `host_metrics_window` shows `mem_pct=90.9, cpu_pct=100.0`;
seconds later the fold script's own process was `Killed` (kernel OOM), `rc=137`, and `VM_SHUTDOWN_ON_COMPLETION=true`
self-deleted the VM. **Root cause**: the launcher hardcodes `--workers 24` in `BACKFILL_CMD`, but the fold script's own
CLI declares `--workers ... default=12` — the launcher was silently running at 2x the script author's own tested/safe
concurrency on an `e2-standard-4` (4 vCPU / 16GB) box. 24 concurrent `ThreadPoolExecutor` workers each downloading +
decoding a legacy parquet shard + building canonical rows via `write_defi_rows()` is a plausible, unremarkable
explanation for the measured memory pressure — no further investigation needed given the mismatch is self-evident from
the two files' own declared defaults diverging.

## Fix shipped

`deployment-service@7480588f57` — reduced the launcher's `--workers` override from `24` to `12` (matching the fold
script's own default), updated the two inline comments that referenced the old thread count, and added a comment citing
this incident so the mismatch doesn't silently recur.

## What's still open

The dex_swaps/dex_pools/rate_indices legacy fold itself is **still not re-run to completion** — the source doc's [DATA]
P1 todo ("relaunch WITHOUT `--allow-stale-fallback` once the consolidator has genuinely caught up") is
precondition-satisfied but not yet executed to completion. Per `/codex/15-runbooks/incidents/rb_infra_relaunch.md`'s
`≤2/(vm-prefix,day)` bound, this session did not attempt a 3rd `backfill-defi-legacy-datatype-fold-` launch today.

## Todos

- [ ] [CODE] P2. Relaunch `launch-backfill-defi-legacy-datatype-fold-vm.sh` (now with the fixed `--workers 12`) for the
      DeFi `dex_pools`/`dex_swaps`/`rate_indices` legacy fold — re-verify manifest freshness first (a real
      `read_availability_index` call, no `--allow-stale-fallback`, per this doc's own verification method above), then
      launch + arm a bounded watchdog through to a terminal `EXIT_STATUS`/`totals=` line. (repo: deployment-service)
- [ ] [INFRA] P3. If a `backfill-defi-legacy-datatype-fold-` VM again shows zero heartbeat/run.log within its first ~10
      minutes (matching attempt 1's signature), capture the serial console BEFORE it gets zombie-reaped
      (`gcloud compute instances get-serial-port-output`) to actually root-cause the startup-script hang — this
      session's attempt 1 evidence was lost because the VM was already deleted by the time it was investigated. (repo:
      deployment-service)
- [ ] [INFRA] P3. Investigate the observed ~70min gap between the DeFi consolidator's `consolidator.lock` going stale
      (`_LOCK_TTL_SECONDS=300s`) and it actually being reclaimed, despite
      `uts-prod-manifest-consolidator-market- data-defi` Cloud Run executions completing "successfully" every ~60-70s
      throughout that window — either a reclaim-race in `_is_fully_empty_confirmed_leaf`-adjacent lock logic
      (`manifest_consolidator.py`'s `_is_lock_fresh`/`_acquire_lock`) or the "successful" executions aren't actually
      attempting the defi bucket per cycle. Self-resolved before full diagnosis this session; only 1 occurrence observed
      so far — investigate if it recurs. (repo: unified-trading-library)

## Progress Log

- **2026-08-16 (plan_reconciler, defi-tranche Phase -1) — cross-link, not independently re-verified**: hunter batch B
  of the 2026-08-16 defi-tranche `/plan-reconcile` run found `dex_swaps` migration-completion claims conflicting by
  ~3.26M rows across 4 docs that don't cross-reference each other, this one included:
  `/plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md`,
  `/plans/active/issues/defi_legacy_data_type_names_manifest_migration_scope_2026_08_04.md`,
  `/plans/archive/2026_08/defi_dex_swaps_gap_rootcause_ao_dispatch_2026_08_16.md` (archived 2026-08-17). Both this
  doc's VM-infra failures AND the
  cross-doc row-count conflict involve the same manifest-consolidator/rebuild machinery and the same bucket — they may
  share a root cause. Added per `plan_reconciler_findings_defi_2026_08_16.md`'s Contradiction #2 recommendation so a
  worker on any one of these 4 docs sees the others; the row-count conflict itself is NOT resolved here (needs a fresh
  live manifest read, out of scope for this cross-link).
- **2026-08-15 (AO-dispatched satellite batch worker, slot 20)**: verified consolidator freshness live, attempted the
  relaunch twice, root-caused attempt 2's OOM, shipped the worker-count fix. Filed this doc per the findings-closure
  hard rule since the underlying relaunch is not yet complete and both failure signatures are worth tracking separately
  from the source doc's original (already-resolved) stale-fallback concern.
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries)
- **na-eligibility-audit 2026-08-17** (infra tranche) [body-hash:e05a7064c41c987a]: KEEP-NA-STALE (already-duplicated)
  — all 3 open todos (relaunch with fixed workers; capture serial console if zero-heartbeat recurs; investigate the
  lock-reclaim gap) are already claimed as ONE combined todo in `defi_satellite_ao_dispatch_batch14_2026_08_16.md`
  (not yet executed there). Checkboxes annotated with that citation rather than re-extracted — the batch14 finalize
  plan's own review todo already flags this exact source-doc-not-yet-flipped gap; this run closes it from the infra
  side. Doc stays `assigned_vm: NA` (its own scope is now fully superseded by the batch14 claim, not independently
  actionable).
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries) — unchanged, still accurate
