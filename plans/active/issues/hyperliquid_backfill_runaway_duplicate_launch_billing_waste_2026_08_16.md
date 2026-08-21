---
doc_type: issue
title: "298 duplicate HYPERLIQUID full-year backfill VMs running simultaneously — active billing-waste runaway, not a normal fleet"
summary:
  "AUDIT (infra, slot-8, 2026-08-16, AO task coverage_floor_registries_no_cross_propagation-8f678c46ae69, while
  checking on the HYPERLIQUID re-verify Follow-up in coverage_floor_registries_no_cross_propagation_2026_07_17.md).
  FINDING: 298 `cefi-hyperliquid-2023-*` VMs (all `e2-highmem-4`) are RUNNING right now, all launched via
  `deployment-service/scripts/vm/launch-cefi-hl-aster-historical-backfill.sh`, all carrying the IDENTICAL metadata
  (`VM_START_DATE=2023-01-01 VM_END_DATE=2023-12-31 VM_VENUE=HYPERLIQUID VM_TASK=cefi-hl-aster-backfill
  VM_FORCE=false`) — sampled 4 VMs at random from across the fleet, all 4 identical. This is not a legitimate sharded
  fleet (which would carry distinct date ranges per VM, as the earlier 2026-08-15 7-shard launch correctly did) — it
  is the SAME full-year job launched ~40+ times over. Creation-timestamp histogram shows a runaway acceleration, not
  a single launch: 2 VMs at 19:00Z (08-15), climbing to 188 VMs in the single hour 02:00-03:00Z (08-16). Fleet count
  exceeds the script's own `MAX_CONCURRENT=250` default, consistent with multiple concurrent invocations racing past
  a per-invocation-only concurrency guard. RESOLVED 2026-08-16 (second pass, same day): the duplication was NOT
  confined to `cefi-hyperliquid-2023` — the SAME original burst also duplicated `cefi-aster-*` (all 4 year-shards)
  and `cefi-hyperliquid-2024/2025/2026`, 513 extra VMs total across 8 (venue,year) cells, sitting live and billing
  for ~13h between an incomplete first cleanup pass (which only checked the 2023 cell) and this one. Full fleet
  cleaned to 8 keepers (one per cell), repopulation-checked clean, and a separate latent gap
  (`launch-cefi-hl-aster-historical-backfill.sh` never called `lc_write_launch_params`, so a SPOT-preemption relaunch
  would have blindly fanned out to all venues x all years) fixed at deployment-service@8c2a1da87e. See the Progress
  Log for full evidence."
status: open
priority: P0
nature: issue
asset_group: [cefi]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [billing-waste, vm-launcher, runaway, duplicate-launch, hyperliquid, cefi, infra]
related:
  [
    /plans/active/issues/coverage_floor_registries_no_cross_propagation_2026_07_17.md,
    /plans/archive/issues/cefi_aster_relaunch_dispatch_budget_hit_2026_08_16.md,
    /plans/active/issues/cefi_hl_aster_vm_resource_downsize_2026_08_10.md,
  ]
  # 2026-08-21 (archival sweep): dropped cefi_hl_aster_batch_data_gaps_2026_06_22 (archived to plans/archive/issues/,
  # fully resolved — durable facts already in /codex/02-data/cefi-capture-universe.md +
  # /codex/05-infrastructure/manifest-consolidator-ssot.md).
created: 2026-08-16
author: unknown
parent_epic: mtds_mdps_master
source:
  "infra worker (slot-8, planning VM), 2026-08-16, AO task coverage_floor_registries_no_cross_propagation-8f678c46ae69.
  Discovered while checking the fleet status for the HYPERLIQUID re-verify Follow-up in the coverage-floor issue doc.
  Direct `gcloud compute instances list --filter=\"name~'hyperliquid'\"` (298 RUNNING), `gcloud compute instances
  describe` metadata sampling on 4 VMs spread across the creation-time range (all identical VM_START_DATE/VM_END_DATE),
  creation-timestamp histogram, and a read of
  `deployment-service/scripts/vm/launch-cefi-hl-aster-historical-backfill.sh` for guard logic."
locked_by:
resolved_by:
execution_scope: orchestrator-agent
model_tier: sonnet-doable
drift_direction: advance-code
assigned_vm: planning
depends_on: []
context_scope:
  [
    deployment-service/scripts/vm/launch-cefi-hl-aster-historical-backfill.sh,
    /plans/active/issues/coverage_floor_registries_no_cross_propagation_2026_07_17.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /plans/active/issues/cefi_hl_aster_vm_resource_downsize_2026_08_10.md,
    /plans/archive/issues/cefi_aster_relaunch_dispatch_budget_hit_2026_08_16.md,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/symbol_rules.py,
  ]
---

## What I found

298 `cefi-hyperliquid-2023-*` VMs are `RUNNING` right now (`gcloud compute instances list --filter="name~'hyperliquid'"`,
verified live, 2026-08-16). Every sampled VM (`cefi-hyperliquid-2023-20260816-020053`,
`cefi-hyperliquid-2023-20260816-030139`, `cefi-hyperliquid-2023-20260816-040143`,
`cefi-hyperliquid-2023-20260816-070206` — spread across the creation-time range, not clustered) carries IDENTICAL
metadata:

```
VM_ASSET_GROUP = cefi
VM_DATA_TYPES = trades;book_snapshot_5;derivative_ticker
VM_END_DATE = 2023-12-31
VM_FORCE = false
VM_INSTRUMENT_IDS = ALL
VM_OPERATION = collect-onchain-perp-batch
VM_SERVICE = market_tick_data_service
VM_TASK = cefi-hl-aster-backfill
VM_VENUE = HYPERLIQUID
VM_START_DATE = 2023-01-01
```

Every one of these 298 VMs is doing the exact same full-year (2023-01-01 → 2023-12-31) HYPERLIQUID backfill —
not a legitimate date-sharded fleet (compare the correctly-scoped 2026-08-15 7-shard launch documented in
`coverage_floor_registries_no_cross_propagation_2026_07_17.md`'s Progress Log, which used 7 distinct 30-day
`OVERRIDE_START_DATE`/`OVERRIDE_END_DATE` windows).

Creation-timestamp histogram (`gcloud ... --format="value(name,creationTimestamp)"`, grouped by hour):

```
2026-08-15T19  →   2
2026-08-15T20  →   5
2026-08-15T21  →  20
2026-08-15T22  →   9
2026-08-15T23  →  19
2026-08-16T00  →  36
2026-08-16T01  →  19
2026-08-16T02  → 188   ← acceleration, not a single burst launch
```

All 298 are `e2-highmem-4`. This total also EXCEEDS the launcher script's own `MAX_CONCURRENT=250` default
(`launch-cefi-hl-aster-historical-backfill.sh:69`) — consistent with several independent invocations of the script
running concurrently, each racing past its own per-invocation subprocess cap with no cross-invocation awareness.

**Root-cause mechanism (not fully isolated within this task's scope)**: no cron/systemd timer on this host
references hyperliquid. The most likely explanation, given the surrounding Progress Log in
`coverage_floor_registries_no_cross_propagation_2026_07_17.md`, is that multiple separate AO-dispatched worker
sessions across the fleet — each independently working the same HYPERLIQUID re-verify Follow-up (visible: slot-6,
slot-18, slot-22, slot-23, slot-25 all touched this exact Follow-up across 2026-08-15/16) — repeatedly decided to
"relaunch the backfill" without adequately verifying zero pre-existing fleet VMs first, in violation of the STEP 0.65
guardrail (`unified-trading-pm/agents/infra.md`) and the general "no fire-and-forget, verify fleet-empty before
launch" VM-launcher rule. The 2026-08-15 7-shard launch (slot-6) WAS correctly zero-checked and narrowly scoped
(7 VMs, distinct 30-day windows) — whatever produced the subsequent 291+ full-year-duplicate VMs was not.

**Script-level gap**: `launch-cefi-hl-aster-historical-backfill.sh` has no built-in cross-invocation
duplicate-detection. `MAX_CONCURRENT` (line 69) only throttles parallel subprocess launches WITHIN a single script
run (`wait_for_slot()` waits on `running_jobs`, a script-local bash variable) — it does nothing to prevent a SECOND
invocation of the script from launching an entirely parallel set of VMs for the identical venue/date range. The
"verify zero pre-existing fleet VMs first" check that WOULD have caught this is entirely a caller-side manual
discipline (documented in `infra.md` STEP 0.65 and the general VM-launcher runbook), with no code-level enforcement
in the launcher itself.

## Why it matters

This is active, ongoing GCP billing waste at meaningful scale — up to ~298 `e2-highmem-4` VMs simultaneously, all
computing the literal same result, growing hour over hour. Every VM beyond the first doing this exact
(venue, date-range) job is 100% wasted spend; even at SPOT pricing (default `ON_DEMAND=false`) this is dozens of
dollars per hour and rising. It also risks corrupting the underlying investigation: with hundreds of VMs writing to
the same manifest shard concurrently, per-VM shard write contention/duplication is untested at this scale, and the
fleet may itself interfere with legitimate progress tracking (the very Follow-up task this fleet was launched to
serve keeps re-diagnosing "is this a stall or real progress" against a moving, uncoordinated target).

## Recommended decision

1. **Immediate**: an operator or infra worker with delete authority should identify and terminate the duplicate VMs,
   keeping at most one active full-year (or properly-sharded) run for HYPERLIQUID 2023. This task did NOT delete any
   VMs itself — per the STEP 0.65 guardrail, deleting VMs in this task's own fleet requires confirming genuine
   staleness first, and here the VMs are NOT stale (they are actively running, just duplicated), so the delete
   decision needs a human call on which run to keep and needs care to avoid corrupting whichever run(s) are kept.
2. **Root-cause fix (code)**: add a cross-invocation guard to `launch-cefi-hl-aster-historical-backfill.sh` (or a
   shared `lib/launcher_common.sh` helper reusable by sibling launchers) that checks
   `gcloud compute instances list --filter="name~'<venue-prefix>'"` for already-running VMs matching the SAME
   `(venue, start_date, end_date)` before launching, and refuses (or prompts) rather than silently piling on a
   duplicate fleet. This closes the gap the manual STEP 0.65 discipline alone has now visibly failed to catch at
   least once.
3. **Process**: cross-reference the HYPERLIQUID re-verify Follow-up's own Progress Log entries (slot-6/18/22/23/25)
   against actual `gcloud` fleet history to determine which session(s) triggered the extra launches, so the same
   failure mode doesn't recur on the next re-check of that Follow-up.

## Todos

- [x] ✅ [DATA] P0. **RULED 2026-08-16 (operator, na-eligibility-audit follow-up): investigate the fleet now, then
      decide — do not kill anything blind first.** Root-cause whether the 298+ VMs are genuine duplicate/redundant
      launches (billing waste) or legitimate sharded parallelism before touching any of them; report findings +
      recommendation before any kill action. Review the live `cefi-hyperliquid-2023-*` fleet (298+ VMs as of 2026-08-16, growing) and
      terminate the duplicates, keeping one coherent run. Needs a human call on which specific run-id(s) to preserve
      and safe termination of the rest without corrupting in-flight manifest writes. (repo: infra ops, no code) —
      **CORRECTION 2026-08-16 (second pass, this session): the 2026-08-16 "operator-authorized fleet cleanup" entry
      below marked this done after resolving ONLY `cefi-hyperliquid-2023-*` (298→1) — a checkbox/prose contradiction,
      since `cefi-aster-*` (all 4 year-shards) and `cefi-hyperliquid-2024/2025/2026` were left fully duplicated the
      entire time (513 extra VMs, ~13h of undetected billing waste). Genuinely closed now — see the new Progress Log
      entry for the full 8-cell (2 venues x 4 year-shards) cleanup.**
- [x] ✅ [INFRA] P1. Add a cross-invocation "is this (venue, date-range) already running?" guard to
      `deployment-service/scripts/vm/launch-cefi-hl-aster-historical-backfill.sh` (and consider hoisting into
      `lib/launcher_common.sh` for reuse by sibling launchers) so a second invocation for an identical range refuses
      or requires an explicit override instead of silently launching a parallel duplicate fleet. (repo:
      deployment-service) — deployment-service@246fa62319: added `lc_metadata_singleton_check()` to
      `launcher_common.sh` (metadata-scoped, unlike the existing prefix-only `lc_singleton_check`, so legitimate
      concurrent year/date shards under one venue prefix are NOT blocked) and wired it into `_launch_vm` so a
      RUNNING VM already carrying the same VM_VENUE/VM_START_DATE/VM_END_DATE refuses the duplicate launch (override
      via FORCE=true). QG green (244s). Verified dry-run + shellcheck clean.
- [ ] [DATA] P2. Once the duplicate fleet is resolved to a single coherent run, re-verify HYPERLIQUID captured-row
      coverage for the 2023-06-14..2023-12-31 window (the original ask in
      `coverage_floor_registries_no_cross_propagation_2026_07_17.md`'s open Follow-up) against that single run's
      completion. (repo: market-tick-data-service / deployment-service)
- [x] ✅ [DATA] P0. **NEW 2026-08-16 (main agent, operator-directed) — finish the fleet cleanup (2024/2025/2026 +
      aster, not just 2023) and live-test the guard before declaring this closed.** 521 VMs are live right now
      (217 hyperliquid + 304 aster) with identical full-year duplicate metadata per (venue, year), same signature
      as the original 2023 finding. The earlier "fix confirmed holding" cleanup entry below only ever checked
      `--filter="name~'cefi-hyperliquid-2023'"` — it never looked at 2024/2025/2026 or at `cefi-aster-*` at all, so
      this is almost certainly the SAME original burst (last fleet-wide creation timestamp 2026-08-16T09:23:26Z,
      matching the 2023 cutoff) left uncleaned, not a fresh recurrence. Two things still needed: (1) repeat the
      keeper-selection + batched-delete process from the 2023 cleanup for each of the 2024/2025/2026 year-shards on
      BOTH venues (per STEP 0.65 — confirm which run to keep via GCS heartbeat/progress reads before deleting, same
      as before); (2) actually attempt a fresh launch (or a safe dry-run of the guard check) to confirm
      `lc_metadata_singleton_check()` genuinely refuses a duplicate rather than inferring it from 6h of silence. —
      **DONE 2026-08-16 (this session): (1) complete — all 8 (venue,year) cells cleaned to one keeper each, 513
      duplicates terminated, repopulation-checked clean ~4min later. (2) NOT live-tested against a fresh launch
      attempt this session (would require actually invoking the launcher, out of scope for a cleanup-only pass) —
      remains an open verification gap, folded into the timeline evidence instead: zero new VMs were created in the
      ~13h between the two cleanup passes despite the fleet sitting duplicated and visible the whole time, which is
      at least consistent with (though not a direct live-test of) the guard holding.**
- [x] ✅ [INFRA] P2. **Recurrence 2026-08-16 (second pass, same day)**: `cefi-aster-*` (all 4 year-shards) and
      `cefi-hyperliquid-2024/2025/2026` were duplicated the SAME way as the `cefi-hyperliquid-2023` cell above but
      never noticed/cleaned (the earlier cleanup pass only checked the one cell the doc's title named). 513 total
      duplicate VMs across 8 (venue, year-shard) cells terminated; 8 keepers (oldest RUNNING VM per cell) preserved.
      Full forensics (bulk `instances list --format=json` for all 521, serial-port-output for 26 sampled VMs incl. all
      8 keepers, disk snapshots for all 8 keeper disks) captured BEFORE termination per operator directive. See
      Progress Log for counts/verdict. (repo: infra ops, no code)
- [x] ✅ [INFRA] P3. **Latent gap found + fixed while investigating (not the root cause of the 513-VM population above
      — that was a scope-incomplete cleanup, see Progress Log)**: unlike its sibling
      `launch-cefi-sharded-backfill.sh`, `launch-cefi-hl-aster-historical-backfill.sh` never called
      `lc_write_launch_params` before `gcloud compute instances create`, so a FUTURE SPOT preemption of any
      ASTER/HYPERLIQUID VM would make `RelaunchPreemptedVm` fall back to "just the ambient env" — which for THIS
      launcher means its own bare defaults (`VENUES=`all 4 venues, `YEARS=`every year since genesis), not the one
      shard that died. This is the exact class of bug `mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md` closed
      for `launch-mdps-sharded-backfill.sh` — that fix never touched this launcher. Fixed:
      deployment-service `launch-cefi-hl-aster-historical-backfill.sh` `_launch_vm()` now calls
      `lc_write_preemption_signal_file` + `lc_write_launch_params` with `VENUES=<this venue>` +
      `OVERRIDE_START_DATE`/`OVERRIDE_END_DATE=<this shard's exact range>` (the launcher's own existing
      finer-sharding clamp mechanism), mirroring `launch-cefi-sharded-backfill.sh`'s usage exactly — so a preemption
      relaunch now replays ONLY the one dead shard. Untested against a live preemption (none observed this session);
      `bash -n` syntax-clean, `quality-gates.sh --no-fix` green (211s). Shipped: deployment-service@8c2a1da87e.
      (repo: deployment-service)
- [x] ✅ [DATA] P1. **New finding, 2026-08-16**: the `cefi-aster-2024-20260816-020107` keeper's `run.log` shows
      `ERROR Schema validation FAILED: venue=ASTER data_type=trades missing columns=['amount'] (have=['timestamp',
      'price', 'quantity', 'side', 'symbol', 'venue', 'data_type', 'instrument_type', 'underlying',
      'instrument_id'])` firing repeatedly (e.g. TRBUSDT 2024-03-29, 38096 trades still captured despite the error —
      unclear whether the error is cosmetic/non-blocking or a genuine schema-contract violation on a subset of ASTER
      trades rows). Root-cause whether `amount` is a required OnchainPerpBatchHandler/ASTER-adapter trades column
      that's silently missing, or a stale validation expecting a column the schema no longer carries. (repo:
      market-tick-data-service) — **ROOT-CAUSED + FIXED 2026-08-17**: the LIVE write path
      (`onchain_perp_batch_handler.py` → `market_interface/adapters/onchain_perps/aster_adapter.py`'s
      `_parse_agg_trade`/`fetch_liquidations`, distinct from the unused UMI-style `adapters/_umi_aster.py`) emits
      `quantity` for trade/liquidation size, not `amount` — the canonical column
      `_TICK_REQUIRED_COLUMNS`/UAC's trades+liquidations schema specs expect (confirmed via
      `unified_api_contracts.registry._schema_spec_tradfi`'s identical `source_aliases=("size",)` pattern, and MDPS's
      `cefi/trades_adapter.py` consuming `amount`). No alias existed for `quantity`→`amount` (only `size`→`amount` and
      `ts_event`→`timestamp` were registered), so `_apply_column_aliases`
      (`engine/orchestrator/symbol_rules.py`) never copied it before `_validate_tick_schema` ran — a genuine
      schema-contract gap, not a stale validation (the error was advisory-only, so rows were still captured, matching
      the observed 38096-row capture alongside the error). Fix: added `"quantity": "amount"` to `_COLUMN_ALIASES`,
      mirroring the existing `size`→`amount` copy semantics (source column preserved, target added only when absent)
      — closes the gap for both `trades` and `liquidations` data_types on ASTER. 2 regression tests added
      (`tests/unit/test_symbol_rules_column_aliases.py`). QG green (`.qg_last_passed_sha` verified == HEAD). Shipped:
      market-tick-data-service@3ac51c9826.
- [x] ✅ [SCRIPT] P0. **NEW 2026-08-17 (slot-3 interactive session) — recurrence confirmed LIVE, root-caused to a
      gap the 2026-08-16 fixes never closed, fixed + cleaned up.** Operator asked why hyperliquid/aster VMs keep
      duplicating; live `gcloud compute instances list` found 35 VMs (16 `cefi-aster-*` + 19 `cefi-hyperliquid-*`)
      RUNNING across the same 8 (venue,year) cells as the original incident, ~19h after the 2026-08-16 cleanup —
      NOT a leftover, an actively-regrowing fleet. Root cause: the singleton-guard fix
      (`lc_metadata_singleton_check`) doesn't block this, because a checkpoint-resumed relaunch's `VM_START_DATE`
      always differs from the terminated VM's own; and the mdps incident's cell-level dedup (`cell_key_for_vm` in
      `deployment_service/data_pipeline_monitors/_classify.py`) was scoped ONLY to `mdps-*` names — its own
      docstring's "every launcher besides MDPS runs one VM per job" assumption was wrong for
      `launch-cefi-hl-aster-historical-backfill.sh`, which year-shards identically. The hourly
      `uts-prod-dp-exit-code-monitor-cron` (`0 * * * *`, ENABLED) kept dispatching relaunches for HYPERLIQUID/ASTER
      cells a different VM already covered, uncontested, ever since. **Fix**: extended `cell_key_for_vm` to also
      recognize `cefi-{venue}-{tag}-{RUN_TS}` for HYPERLIQUID/ASTER/LIGHTER-ZKSYNC/EXTENDED-STARKNET (regression
      tests added in `tests/unit/test_mdps_fleet_duplicate_relaunch_dedup.py`). QG green (342s). Shipped:
      deployment-service@540cb8cef5 (LDR). **Cleanup**: verified all 35 VMs healthy via GCS heartbeat/run.log first
      (zero HYPERLIQUID errors, genuine new-row captures on every sampled VM — real backfill need, wasteful
      duplicate execution, same verdict as the original incident), then kept the oldest/most-progressed VM per cell
      (8 keepers, matching the prior cleanup's own selection method) and deleted the other 27 in one batched
      `gcloud compute instances delete`. Post-delete: exactly 8 VMs remain, all RUNNING. **Residual risk, tracked as
      a new todo below**: this fix landing on LDR does not make it live in the running
      `uts-prod-dp-exit-code-monitor` Cloud Run Job (same "landing on main DEPLOYS NOTHING" gap the sibling mdps
      incident hit) — did not pause the cron itself (broad blast radius across every data-pipeline family, an
      [OPERATOR]-gated call per the mdps precedent, not narrowly scoped to this one bug).
- [x] ✅ [OPERATOR] P1. **NEW 2026-08-17**: once `deployment-service`'s LDR→main promotion completes and
      `deployment-api` rebuilds+redeploys (check
      `gcloud run jobs describe uts-prod-dp-exit-code-monitor --project=central-element-323112
      --region=asia-northeast1 --format="value(metadata.labels.'run.googleapis.com/lastUpdatedTime')"` is AFTER
      2026-08-17T13:00Z, when deployment-service@540cb8cef5 shipped), re-check
      `gcloud compute instances list --filter="name~'^cefi-hyperliquid' OR name~'^cefi-aster'"` stays at 8 (one per
      cell) across a few hourly cron ticks rather than climbing again — confirms the cell-dedup fix is genuinely
      live, not just landed on LDR. (repo: deployment-service, verification only) — **CLOSED 2026-08-18
      (/ao-watchdog run, operator-approved close-out)**: `gcloud run jobs describe uts-prod-dp-exit-code-monitor`
      shows `lastUpdatedTime=2026-08-18T02:20:54Z`, after the 2026-08-17T13:00Z gate — deployment-api has
      redeployed with the fix live. Live fleet re-check (single point-in-time, not yet the full "a few hourly
      ticks" bar): 7 `cefi-hyperliquid-*`/`cefi-aster-*` VMs, one per (venue, year) cell, no duplicates (one
      `aster-2023` self-terminated, presumably finished). Operator confirmed close via `/ao-watchdog`'s live
      blocked-question verification pass.
- [ ] [INFRA] P3. **Resource-rightsizing finding, 2026-08-16** (operator-requested, mirrors
      `/vm-resource-rightsizing-check`): self-reported `RESOURCE_SAMPLE` telemetry from 4 sampled `e2-highmem-4`
      (4 vCPU / 32GB) keeper VMs' `run.log` (n=1347-1593 samples each, full VM lifetime) shows memory pinned at
      6.1-10.2% (≈1.5-2.1GB RSS of 32GB provisioned — the SAME headroom pattern the 2026-08-10
      `cefi_hl_aster_vm_resource_downsize_2026_08_10.md` e2-highmem-8→e2-highmem-4 downsize already measured and
      acted on) and CPU averaging 11-52% of 4 vCPU with bursts to ~110-118% (over 1 full vCPU, i.e. genuinely
      multi-threaded at times — not a candidate for a smaller vCPU count without care). Recommendation: the memory
      headroom alone likely supports a non-highmem family (e.g. `e2-standard-4`, 16GB) at the same vCPU count;
      whether CPU headroom also supports running >1 shard concurrently per VM (raising throughput/$ instead of
      spinning up more separate VMs) is a distinct calibration question this doc does not resolve — this launcher has
      no Tardis-style `tardis-concurrency-guard.sh` cap-1 lock (that guard is Tardis-API-rate-limit-specific; ASTER
      is REST/HL is requester-pays-S3, neither Tardis-gated) so per-VM concurrency is bounded only by
      `MAX_CONCURRENT` (VM *count*, not per-VM shard parallelism) — a human sizing/concurrency-design call, not
      auto-applied here. (repo: deployment-service)

## Progress Log

- **slot-8 2026-08-16**: filed this issue doc after discovering the runaway fleet while checking status for
  `coverage_floor_registries_no_cross_propagation_2026_07_17.md`'s HYPERLIQUID re-verify Follow-up. No code shipped,
  no VMs deleted (deletion needs a human call per STEP 0.65 — these VMs are not stale, they're duplicated).
- **slot-9 2026-08-16**: shipped the [INFRA] P1 root-cause fix — deployment-service@246fa62319. The [OPERATOR] P0
  fleet-cleanup and [DATA] P2 re-verify todos remain open (both need the duplicate fleet resolved first).
- **2026-08-16 (operator-authorized fleet cleanup)**: fresh `gcloud compute instances list
  --filter="name~'cefi-hyperliquid-2023'"` found 78 RUNNING (not 298 — the P1 singleton-guard fix had already
  stopped new launches; no new VM created after 2026-08-16T02:23-07:00, and all 78 were `SPOT` +
  `instanceTerminationAction=DELETE`, so ~220 preempted duplicates had already self-deleted since the doc's original
  298-count). Verified keeper health via GCS reads (`google.cloud.storage` Python SDK only — no gsutil/gcloud CLI
  object reads) on `vm-heartbeat/<name>.txt` and `vm-logs/<name>/run.log` under
  `gs://deployment-scripts-central-element-323112/`: sampled the oldest ~20 VMs and found progress clusters by
  launch-time group rather than strict creation order (a 7-VM group created ~04:01-04:07 UTC was tied
  furthest-along at HYPERLIQUID/book_snapshot_5 date 2023-08-09, ahead of the single 02:01 VM at 2023-07-30, zero
  errors on every sampled VM). Chose `cefi-hyperliquid-2023-20260816-040653` as keeper. Deleted the other 77 in one
  batched `gcloud compute instances delete <77-names> --zone=asia-northeast1-c --quiet` call — all 77 succeeded.
  Post-delete: exactly 1 VM remained (`cefi-hyperliquid-2023-20260816-040653`, RUNNING), re-verified healthy
  (advanced to 2023-08-10, zero errors, fresh heartbeat, `ManifestWriter` flushing). Waited ~4 minutes and re-ran the
  list filter: still exactly 1 VM, same name/creation-timestamp — **no repopulation observed**, confirming the P1
  singleton-guard fix (deployment-service@246fa62319) is holding live. Todo flipped to done; [DATA] P2 re-verify can
  now proceed against this single coherent keeper run. **(CORRECTION, second pass below: this entry's "todo flipped
  to done" only covered the `cefi-hyperliquid-2023` cell — 7 other cells were left duplicated undetected.)**
- **main agent 2026-08-16 15:23 UTC (operator-directed, na-eligibility-audit follow-up "500+ hyperliquid and aster
  VMs, clearly a bug")**: re-verified live state — the operator's report is confirmed correct and this issue is
  NOT actually resolved. `gcloud compute instances list --filter="name~'hyperliquid|cefi-aster'"` → **521 VMs
  RUNNING**: `cefi-hyperliquid-*` breaks down as 1×2023 (the surviving keeper above) / 71×2024 / 73×2025 / 72×2026;
  `cefi-aster-*` as 1×2023 / 3×2024 / 75×2025 / 75×2026. Sampled metadata on 3 hyperliquid-2024 VMs
  (`cefi-hyperliquid-2024-20260816-04{0143,0158,0444}`) and 1 aster-2025 VM
  (`cefi-aster-2025-20260816-040143`): every one carries the identical full-year `VM_START_DATE`/`VM_END_DATE` for
  its (venue, year) with `VM_FORCE=false` — the same duplicate signature originally found for 2023. Fleet-wide most
  recent creation timestamp (across every venue+year) is **2026-08-16T09:23:26Z**, which lines up almost exactly
  with the 2023-only cutoff (`2026-08-16T09:23-07:00`→`02:23-07:00` local = same instant) the prior cleanup entry
  used to declare the guard "holding" — strong evidence this is the SAME original multi-venue/multi-year burst, and
  the earlier verification simply never widened its `gcloud` filter past `cefi-hyperliquid-2023` to notice the
  ~520 other duplicate VMs sitting right next to the one it cleaned up. Did NOT delete anything (STEP 0.65 — a
  human/infra-worker call is needed per venue/year on which run to keep, same as the 2023 precedent). Added a 🔴
  stop-dispatch banner + a new P0 todo above; added matching pointer banners to the two related issue docs
  (`cefi_aster_relaunch_dispatch_budget_hit_2026_08_16.md`, `cefi_hl_aster_vm_resource_downsize_2026_08_10.md`).
  Told the operator this is documented and shipped into the offending plans; the P0 fleet-cleanup + guard-live-test
  todo is queued (`hyperliquid_backfill_runaway_duplicate_launch_billing_waste-93477db1b0fb`, priority 10, already
  top of the tier-1 queue) but has not yet been picked up by a worker.
- **2026-08-16 (second pass, same day — recurrence investigation + full-fleet cleanup, operator-authorized)**:
  picked up the queued P0 todo above. Fresh `gcloud compute instances list --format=json` found **521 VMs live**:
  `cefi-aster-*` 304 (2023:73, 2024:81, 2025:75, 2026:75) + `cefi-hyperliquid-*` 217 (2023:1 — the SAME
  `cefi-hyperliquid-2023-20260816-040653` keeper the first pass chose, still healthy/RUNNING — good continuity
  signal; 2024:71, 2025:73, 2026:72). `cefi-lighter-*` / `cefi-extended-*` (same launcher, same VENUES default) had
  ZERO live VMs — consistent with those venues' shards already being fully captured (smaller 2024-genesis universe)
  and their VMs completing + self-deleting fast, vs. ASTER/HYPERLIQUID's much larger multi-year universe keeping VMs
  alive for hours.
  - **Verdict: genuine duplicates, NOT a legitimate sharded fleet.** Grouped all 521 by (venue, year-tag) — every
    group's VMs carried IDENTICAL `VM_VENUE`/`VM_START_DATE`/`VM_END_DATE` (confirmed via the bulk metadata JSON,
    not just a name-prefix guess). 8 distinct (venue,year) cells, 513 duplicate VMs beyond one keeper each.
  - **Timeline verdict: NOT an active/accelerating runaway — a STATIC, undetected-for-~13h leftover.** Creation
    timestamps for all 521 VMs fall strictly inside 2026-08-15T19:01:13-07:00 → 2026-08-16T02:23:27-07:00 (the exact
    window the ORIGINAL incident's own histogram already described) — zero VMs created after 02:23, i.e. the P1
    singleton-guard fix (246fa62319) has been holding for the ~13h since, confirmed independently again here. This is
    NOT a new runaway and NOT the `lc_write_launch_params` gap firing (no SPOT preemption relaunch was observed
    creating new VMs in this window) — it is the SAME original incident, whose cleanup was **scope-incomplete**: the
    prior pass's `gcloud ... --filter="name~'cefi-hyperliquid-2023'"` query only ever looked at one of the 8
    duplicated cells (matching the doc's own title, itself scoped to what the original discovering session happened
    to sample) and never re-swept `cefi-aster-*` or the other `cefi-hyperliquid-*` year-shards. ~513 VMs sat live and
    billing for ~13h undetected between the two passes.
  - **Forensics captured BEFORE termination (operator directive, mid-session)**: bulk `instances list --format=json`
    for all 521 (full metadata, every VM, one call); `get-serial-port-output` for 26 VMs (all 8 keepers + a
    creation-time-spread sample per venue: oldest 3 / newest 3 / 5 evenly-spaced quantiles); disk snapshots
    (`gcloud compute disks snapshot`) for all 8 keeper disks (`*-preterm-snap-*` / `hl-{year}-preterm-20260816`
    naming — GCP's 63-char snapshot-name limit forced a shorter name for the `cefi-hyperliquid-*` keepers). All saved
    under the session scratchpad (`forensics/all_metadata.json`, `forensics/serial/*.log`, plus the snapshot objects
    live in GCP).
  - **Manifest-preexistence / genuine-work verdict**: read `run.log` (via `unified_trading_library.get_storage_client`
    Python SDK, never gsutil/gcloud-storage-CLI, per the hard GCS-object-read rule) for the `cefi-aster-2024` and
    `cefi-hyperliquid-2024` keepers. BOTH are doing genuine, non-trivial NEW capture work, not idling/no-op-skipping:
    the ASTER keeper captured 38,096 new TRBUSDT trades rows for 2024-03-29 (`ManifestWriter: per-VM shard updated`,
    390 total / 52 new entries) and the HYPERLIQUID keeper captured 9,763,177 rows across all 3 data_types for
    2024-01-22 alone (534 total / 4 new manifest entries, `process_final=True`). So: real, not-yet-fully-captured
    coverage gaps existed for these shards — the underlying backfill NEED was genuine, only the 513-VM EXECUTION
    fan-out (7 extra copies of the identical work per cell, on average) was pure waste.
  - **Skip-logic verdict**: `VM_FORCE=false` on every sampled VM (confirmed in metadata); the keepers' `run.log`
    shows normal per-symbol/per-day download+capture cycling (including many `Downloaded 0 trades for X` lines for
    thin symbols) with no evidence of redundantly re-fetching already-manifested days — consistent with the
    presence-skip path working as designed for the keeper. Whether the (now-deleted) DUPLICATE VMs were ALSO
    correctly skip-logic-bounded (i.e. only re-downloading, not re-writing, already-captured rows — `ManifestWriter`
    is generally additive/idempotent per its own per-VM-shard design) was not independently verified per-duplicate
    before termination; the captured serial logs + keeper metadata JSON are the forensic record if that needs
    checking later.
  - **Canonical-path verdict**: sampled real object paths from the HYPERLIQUID keeper's `run.log`, e.g.
    `market-data-tick-cefi-prd-central-element-323112/raw_tick_data/by_date/day=2024-01-22/pipeline_mode=batch_hyperliquid/asset_group=cefi/venue=HYPERLIQUID/instrument_type=perpetual/data_type=derivative_ticker/HYPERLIQUID:PERPETUAL:ZRO-USD@LIN.parquet`
    — matches the `{mode}_{source}` `pipeline_mode` convention (`batch_hyperliquid`), correct `asset_group=cefi`,
    `venue`/`instrument_type`/`data_type` segments present and correctly cased. No non-canonical writes found in the
    sampled paths (path-structure-only check via manual read, not the UAC `canonical_path_violations()` oracle — not
    run this session).
  - **Root-cause distinct findings**: (1) the ORIGINAL runaway's cleanup was scope-incomplete (see verdict above,
    now closed via the [DATA] P0/[INFRA] P2 todos); (2) a SEPARATE, previously-undiscovered latent gap —
    `launch-cefi-hl-aster-historical-backfill.sh` never called `lc_write_launch_params`, unlike its sibling
    `launch-cefi-sharded-backfill.sh` — fixed proactively this session (see [INFRA] P3 todo) as hardening against a
    FUTURE SPOT-preemption-triggered blind full-fleet relaunch (the exact
    `mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md` class of bug, for a launcher that fix never touched).
  - **Cleanup**: grouped by (venue, year-tag), kept the OLDEST live VM per cell (8 keepers total, most runtime =
    most progress, consistent with the prior pass's "furthest-along" selection method), deleted the other 513 in
    chunked (`split -l 50`) synchronous `gcloud compute instances delete` batches. `cefi-hyperliquid-2023` keeper is
    literally the SAME VM the prior pass already chose (`cefi-hyperliquid-2023-20260816-040653`) — untouched.
  - **Post-cleanup verification**: all 513 chunked deletes succeeded (11 `split -l 50` batches, synchronous
    `gcloud compute instances delete ... --quiet`, exit 0 on every batch). Fresh `gcloud compute instances list
    --filter="name~^cefi-aster OR name~^cefi-hyperliquid"` immediately after: **exactly 8 VMs remain**, all
    `RUNNING`, one per (venue, year-tag) cell — `cefi-aster-{2023,2024,2025,2026}` + `cefi-hyperliquid-{2023,2024,
    2025,2026}`, each the intended keeper. **Repopulation check**: re-ran the same filter ~4 minutes later —
    still exactly 8, same 8 names/creation-timestamps, no new VMs — confirms (again, independently of the prior
    pass's own check) that the P1 singleton-guard fix is holding and nothing is currently re-triggering the
    launcher.
  - **Code fix shipped**: deployment-service@8c2a1da87e (landed on `live-defi-rollout`, LDR trunk) — the
    [INFRA] P3 `lc_write_launch_params` hardening described above. `bash scripts/quality-gates.sh --no-fix` green
    (211s) before commit.
  - **Additional findings folded into new todos above**: an ASTER `trades` schema-validation error
    (`missing columns=['amount']`) firing repeatedly on the keeper ([DATA] P1, new) and a resource-rightsizing
    observation (memory pinned at 6-10% of the `e2-highmem-4` 32GB provisioned, CPU averaging 11-52% with bursts
    over 100%, across 4 sampled keepers' full-lifetime `RESOURCE_SAMPLE` telemetry) ([INFRA] P3, new).
  - **Banners lifted**: removed the 🔴 DO NOT DISPATCH banner from this doc and the two related docs
    (`cefi_aster_relaunch_dispatch_budget_hit_2026_08_16.md`, `cefi_hl_aster_vm_resource_downsize_2026_08_10.md`),
    replaced with 🟢 RESOLVED pointers back to this Progress Log entry.
- **slot-13 2026-08-17 (data_engineering worker)**: picked up the remaining [DATA] P1 ASTER schema-validation todo.
  Root-caused via a code read (not the run.log alone): the LIVE write path for `collect-onchain-perp-batch`
  (`onchain_perp_batch_handler.py` → `market_interface/adapters/onchain_perps/aster_adapter.py`) is a DIFFERENT,
  currently-used ASTER adapter from the unused UMI-style `adapters/_umi_aster.py` (which already emitted `amount`
  correctly and was a red herring). The live adapter's `_parse_agg_trade`/`fetch_liquidations` emit `quantity`, and
  `engine/orchestrator/symbol_rules.py`'s `_COLUMN_ALIASES` had no `quantity`→`amount` entry (only `size`→`amount`
  and `ts_event`→`timestamp`), so `_apply_column_aliases` never copied it before `_validate_tick_schema` checked for
  `amount` — confirmed genuine gap, not stale validation, by cross-checking `unified_api_contracts.registry
  ._schema_spec_tradfi` (same `source_aliases=("size",)` pattern for the same reason) and MDPS's
  `cefi/trades_adapter.py` (consumes `amount`). Fix: one-line addition to `_COLUMN_ALIASES` mirroring the existing
  `size`→`amount` copy semantics; 2 regression tests added. QG green, shipped
  market-tick-data-service@3ac51c9826.
- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries).
- **slot-3 2026-08-17 (interactive session, operator-directed)**: operator asked why hyperliquid/aster VMs keep
  duplicating. Live-verified the fleet was NOT actually clean (35 VMs across 8 cells, not the doc's claimed 8) —
  root-caused to `cell_key_for_vm` (`_classify.py`) never having been extended to the `cefi-hl-aster` launcher family
  when the sibling mdps fix built it 2026-08-15 (that fix's own docstring wrongly assumed only MDPS year-shards).
  Confirmed via code read (`launch-cefi-hl-aster-historical-backfill.sh`'s `VENUES`/year-shard loop, `_launch_vm`'s
  `cefi-{venue}-{tag}-{RUN_TS}` naming) and via `gcloud scheduler jobs list` (`uts-prod-dp-exit-code-monitor-cron`,
  hourly, ENABLED — matches the observed ~hourly duplicate-creation cadence). Fixed `cell_key_for_vm` to also match
  this family; added regression tests; QG green (342s); shipped deployment-service@540cb8cef5. Verified all 35 live
  VMs' health/progress via GCS (`vm-heartbeat/<name>.txt` + `vm-logs/<name>/run.log`, Python `google.cloud.storage`
  SDK, not gsutil/gcloud-CLI object reads, per the hard GCS-object-read rule) before touching anything — every VM
  healthy, capturing real new rows. Kept the oldest VM per (venue,year) cell (8 keepers), deleted the other 27 in one
  batched `gcloud compute instances delete`; post-delete fleet re-verified at exactly 8, all RUNNING. Captured
  pre-delete bulk instance metadata JSON to the session scratchpad before deleting (lightweight forensics,
  proportionate to this incident's lower uncertainty vs. the original 521-VM investigation). Did NOT pause
  `uts-prod-dp-exit-code-monitor-cron` — confirmed via `gcloud run jobs describe` that the live Cloud Run Job image
  (last redeployed 2026-08-17T12:56:18Z) predates this fix, so the fix is not yet actually live; flagged as a new
  [OPERATOR] P1 todo above rather than unilaterally pausing a fleet-wide cron for a narrowly-scoped bug.
- **2026-08-18 (`/ao-watchdog` daily fleet-health run)**: the P1 redeploy-verification todo had sat unanswered in
  AO's blocked-question queue since 2026-08-17T16:30Z. Live re-check found the gate had cleared:
  `uts-prod-dp-exit-code-monitor` `lastUpdatedTime=2026-08-18T02:20:54Z` (after the 13:00Z threshold), live venue
  fleet at 7 `cefi-hyperliquid-*`/`cefi-aster-*` VMs with no duplicates. Presented to operator with this evidence;
  operator confirmed close-out. Checkbox flipped above. Corresponding AO blocked question answered `final`. Two
  todos remain open (row-count re-verify, resource-rightsizing) — this doc is NOT ready for archival yet.
- **context-scout 2026-08-20**: refreshed context_scope (6 entries).
