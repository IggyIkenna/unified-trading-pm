---
doc_type: issue
title:
  "14 mdps-backfill-tradfi ES/MES year-shard VMs (2020-2026, `es`+`es3` groups) failed overnight on the
  instruments-tradfi consolidator staleness-budget gap; fix already shipped, an in-flight relaunch wave covers the `es`
  shards, the `es3` shards remain un-relaunched as of this writing"
summary:
  "DP-VM-001 escalation agt-c7efe2 (data_pipeline_failure worker, slot 8) was dispatched to relaunch
  mdps-backfill-tradfi-y2020es-20260730-235735 (exit_code=1). Root cause: instruments-tradfi's manifest consolidator
  cadence moved to hourly 2026-07-29/30 but AG_STALENESS_BUDGET_SEC never got a tradfi override (120s default), so
  `assert_consolidator_healthy` false-raised `ManifestConsolidatorStaleError` on a healthy consolidator — hit by ALL 14
  ES/MES year-shard VMs in this fleet (7 `es` + 7 `es3`, 2020-2026) between ~21:00Z 2026-07-30 and ~01:00Z 2026-07-31.
  The fix (unified-trading-library@75b5735, 'tradfi': 7200 added to AG_STALENESS_BUDGET_SEC) landed 2026-07-31T00:34:02Z
  and is confirmed baked into the current floating code tarball (manifest commit 2fa09f1db921, an ancestor of 75b5735,
  created 01:06:47Z). By the time this worker started, ANOTHER relaunch wave (RUN_TS 20260731-011358, origin not
  identified by this worker) was already re-running all 7 `es` shards including this worker's assigned VM — confirmed
  healthy (real CPU/network activity, fresh heartbeats) as of 01:29Z. This worker's own relaunch of the same shard
  (mdps-backfill-tradfi-y2020es-20260731-011628) was therefore a duplicate; it self-terminated ~23s after task launch
  (exit_code=125, registry reap_reason=vm_not_running, 0 rows written — harmless, no data written twice). The 7 `es3`
  shards have NOT been relaunched by anyone as of this writing."
status: open
priority: P1
nature: notes
asset_group: [tradfi, meta]
stage: [data]
repos: [unified-trading-library, deployment-api, deployment-service, market-data-processing-service]
scope: [engineer, admin]
tags: [manifest, consolidator, staleness, tradfi, data-correctness, false-stale, vm-fleet, dp-vm-001]
related: [manifest-consolidator-ssot.md, sports_manifest_read_staleness_budget_missing_2026_07_15.md]
created: 2026-07-31
parent_epic: infrastructure_master
source:
  "data_pipeline_failure worker (slot 8, planning VM), escalation agt-c7efe2, 2026-07-31, dispatched to relaunch
  mdps-backfill-tradfi-y2020es-20260730-235735 (DP-VM-001, exit_code=1). Investigated via
  unified_trading_library.DeploymentsRegistry (active + 1-day archive) + GCS run.log/LAUNCH_PARAMS.json reads + gcloud
  compute instances/operations."
locked_by:
resolved_by:
execution_scope: orchestrator-agent
assigned_role: backend_engineer
model_tier: sonnet-doable
drift_direction: advance-code
assigned_vm: planning
depends_on: []
---

## What I found

Fleet impact (`DeploymentsRegistry`, prefix `mdps-backfill-tradfi-`, 1-day archive as of 2026-07-31T01:30Z):

| Shard    | Original failure                            | Relaunch status as of 01:30Z                                                                             |
| -------- | ------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| y2020es  | failed exit=1 (00:00-01:00Z)                | **covered** — `mdps-backfill-tradfi-y2020es-20260731-011358` RUNNING, healthy (cpu 14%, fresh heartbeat) |
| y2021es  | failed exit=1                               | **covered** — `...-y2021es-20260731-011358-r2` RUNNING                                                   |
| y2022es  | failed exit=125 (reaped, likely same class) | **covered** — `...-y2022es-20260731-011358-r2` RUNNING                                                   |
| y2023es  | failed exit=125 (reaped)                    | **covered** — `...-y2023es-20260731-011358` RUNNING                                                      |
| y2024es  | failed exit=125 (reaped)                    | **covered** — `...-y2024es-20260731-011358` RUNNING                                                      |
| y2025es  | failed exit=1                               | **covered** — `...-y2025es-20260731-011358` RUNNING                                                      |
| y2026es  | failed exit=1                               | **covered** — `...-y2026es-20260731-011358` RUNNING                                                      |
| y2020es3 | failed exit=1                               | **NOT relaunched**                                                                                       |
| y2021es3 | failed exit=1                               | **NOT relaunched**                                                                                       |
| y2022es3 | failed exit=1                               | **NOT relaunched**                                                                                       |
| y2023es3 | failed exit=1                               | **NOT relaunched**                                                                                       |
| y2024es3 | failed exit=1                               | **NOT relaunched**                                                                                       |
| y2025es3 | failed exit=1                               | **NOT relaunched**                                                                                       |
| y2026es3 | failed exit=1                               | **NOT relaunched**                                                                                       |

**Root cause** (all 14 shards, same signature — `run.log` tail on the original y2020es VM):

```
ERROR Error processing tradfi: Manifest consolidator appears DOWN for bucket=
'instruments-store-tradfi-prd-central-element-323112': consolidated _index/availability_index.parquet
heartbeat is 3428s old (> 120s budget) while per-VM shards exist. ... Set MANIFEST_ALLOW_STALE_FALLBACK=true
to force the recovery merge.
```

`instruments-tradfi`'s Cloud Scheduler cadence moved to **hourly** (`0 * * * *`) on 2026-07-29/30 (cost-reduction pass,
`manifest_consolidator_cadence_cost_audit_2026_07_20.md`), but `AG_STALENESS_BUDGET_SEC` (the read-path gate
`assert_consolidator_healthy()`/`read_availability_index()` actually enforce) never got a `tradfi` entry, so it fell
through to the generic 120s default — false-tripping on ~95%+ of reads outside the ~2-3min window right after each
hourly consolidator run. Identical class to the sports (2026-07-15) and defi (2026-07-29) gaps already fixed the same
way. **Already fixed**: `unified-trading-library@75b5735` ("fix(manifest-writer): add missing tradfi staleness-budget
override"), landed **2026-07-31T00:34:02Z**, adds `"tradfi": 7200` to `AG_STALENESS_BUDGET_SEC`
(`unified_trading_library/manifest_writer/_staleness_budget.py`). Confirmed baked into the current floating code
tarball: `code/unified-trading-library-code.manifest.json` pins commit `2fa09f1db921` (created 2026-07-31T01:06:47Z),
and `git merge-base --is-ancestor 75b5735 2fa09f1d` returns true.

**Why the original VMs failed despite the fix landing mid-fleet**: every one of the 14 original VMs launched between
21:00Z (2026-07-30) and 00:02Z (2026-07-31) — all BEFORE the 00:34:02Z fix — and each pinned whatever UTL tarball was
floating at ITS launch time (VM code doesn't hot-reload). The fix only helps a FRESH launch.

**My own relaunch was a harmless duplicate.** I (slot 8, escalation agt-c7efe2) relaunched
`mdps-backfill-tradfi-y2020es-20260731-011628` at 01:16:31Z with the exact original scope (recovered from the dead VM's
`LAUNCH_PARAMS.json`: `MDPS_INSTRUMENT_IDS='CME:FUTURE:ES CME:FUTURE:MES'`, 2020-01-01..2020-12-31, full), correctly
pinned to the fixed tarball. It self-terminated ~23s after the MDPS process started (`exit_code=125`,
`extras.reap_reason=vm_not_running`, 0 rows written) — no crash log survived (VM instance itself was deleted, so
`get-serial-port-output` 404s and `run.log` was never uploaded). By then an UNRELATED, earlier relaunch wave
(`RUN_TS=20260731-011358`, started ~01:13:58Z — origin/author not identified by this worker; possibly another escalation
worker or an operator-driven batch) had ALREADY relaunched all 7 `es` shards, including this exact one, 3 minutes before
mine. That VM (`...-y2020es-20260731-011358`) is confirmed healthy (cpu_pct=14.2%, real network throughput, fresh
heartbeats through 01:29:39Z) — my duplicate very likely died to a concurrency/duplicate-in-flight guard I did not
directly locate in code, though I did not find an explicit named guard in `setup-data-pipeline-vm.sh`; an early
SPOT-capacity contention (7+ e2-standard-8 SPOT VMs launched in the same ~1-2min window in the same zone) is an equally
plausible alternate explanation. Either way: zero data-correctness impact (0 rows written by the duplicate), and the
shard IS being correctly reprocessed by the other wave.

## Why it matters

- **Real, if bounded, overnight impact**: 14 backfill VM-hours wasted on a false staleness read (SPOT, so bounded $
  cost, but genuine wall-clock/compute waste) before the class-level fix was diagnosed and shipped.
- **The `es3` shards (7 of 14) are currently NOT covered by any known in-flight relaunch** — whoever launched the
  `011358` wave scoped it to the `es` group only. If nothing else is already tracking them, they will sit
  `failed`/un-retried until someone (an operator, another dp-fleet-monitor escalation, or a follow-up relaunch) re-runs
  them with the now-fixed code.
- **Confirms the class-level fix works in practice**: the `011358`-wave VMs are progressing normally (unlike the
  original run's ~57min-to-failure or my duplicate's ~23s self-termination), consistent with the staleness-budget gap
  being the actual, now-closed root cause.

## Recommended decision

No code action needed here (the fix already shipped and is validated in-flight). Remaining open items are pure
ops/follow-up:

- [ ] [OPS] P1. Confirm ownership of the `es3` relaunch — either the `011358`-wave's author intends to cover them next,
      or they need an explicit relaunch
      (`bash deployment-service/scripts/vm/launch-mdps-backfill-vm.sh --env prod     --vm-name mdps-backfill-tradfi-y2020es3-<ts> tradfi 2020-01-01 2020-12-31 full`
      with the `es3` group's original `MDPS_INSTRUMENT_IDS` recovered from each dead VM's
      `vm-logs/<vm>/LAUNCH_PARAMS.json` — do not guess the instrument-id filter). Check `DeploymentsRegistry` for a
      fresh `es3` relaunch before acting (avoid a 3rd duplicate).
- [ ] [OPS] P2. Once the `011358`-wave VMs complete, spot-check `rows_out`/manifest coverage for the `es`/`es3`
      2020-2026 range to confirm the backfill actually completed (this doc only confirms the VMs are alive, not that the
      full year ranges finished cleanly).
- [ ] [INFRA] P3. Identify what launched the `011358` wave (not found by this worker — check `agent-orchestrator`
      dispatch logs / other `dp-fleet-monitor` escalations around 01:13Z) so future incidents don't need to re-derive
      "who else might already be fixing this" from the registry by hand. If it was another `data_pipeline_failure`
      escalation worker, no action needed — just confirms the multi-escalation dispatch model is working as intended for
      a fleet-wide failure.

## Progress Log

- **2026-07-31 (slot 8, escalation agt-c7efe2)**: diagnosed root cause (tradfi consolidator staleness-budget gap,
  already fixed in `unified-trading-library@75b5735`), confirmed fix is in the live floating tarball, attempted a
  relaunch of the assigned VM (duplicate of an already-in-flight relaunch, self-terminated harmlessly), filed this doc
  to flag the `es3` gap and close the loop on the wider fleet impact.
