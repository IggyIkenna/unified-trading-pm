---
doc_type: issue
title:
  DP-VM-002 CRITICAL for mdps-defi-2022-20260815-040833 — root cause was MDPS never recording expected_unattempted for a
  zero-raw-file (data_type, date) cell (fixed); residual detector blind spot documented
summary: >-
  Escalation agt-cf60fa: VM mdps-defi-2022-20260815-040833 (MDPS DeFi 2022 year-shard candle-derivation catch-up,
  launch-mdps-sharded-backfill.sh) drained clean (EXIT_STATUS=0, no errors/exceptions in its 513KB run.log) but manifest
  captured stayed 0->0, firing DP-VM-002 CRITICAL. Direct GCS read confirmed all 61 dates (2022-11-01..2022-12-31)
  processed with "0/0 succeeded, 0 errors" — the ONLY data_type MDPS still considered "missing" for this window was
  defi/dex_pool_swaps, and raw MTDS dex_pool_swaps coverage for defi genuinely starts 2023-01-01 (confirmed via direct
  bucket listing: 0 dex_pool_swaps blobs at day=2022-11-01/2022-12-31, thousands present from day=2023-01-01 onward) —
  every other data_type (oracle_prices, gas_fees, lending_indices, etc.) DOES have 2022-11/12 coverage and was already
  fresh from a prior run.

  Root cause: `CandleOrchestrationService._resolve_files_to_process` (market-data-processing-service) returns `None`
  when `_list_instrument_files` finds zero raw files for a (data_type, date), but never wrote ANY manifest row for that
  cell — unlike the category-level "MTDS not yet run" skip path (`_record_expected_unattempted_on_skip`), which already
  writes an honest `expected_unattempted` marker. With no manifest trace, `check_shard_freshness` treats the cell as
  permanently "missing" forever, so every future mdps-defi-2022 run re-lists + re-skips the same pre-genesis
  dex_pool_swaps window — wasted VM compute on every run, and a structural inability for `_index/per_vm/{vm}.parquet` to
  ever record anything for that data_type, which is part of why DP-VM-002's captured-delta signal reads 0->0.

  **Fix shipped**: `market-data-processing-service@e146759701` — `_resolve_files_to_process` now calls the existing
  `_record_expected_unattempted_on_skip(data_types=[data_type])` on a zero-file listing, mirroring the category-level
  pattern. Regression test added (`TestResolveFilesToProcess.test_no_instrument_files_returns_none`, asserts
  `record_expected_unattempted_for_shard` is called with the right kwargs). Full `quality-gates.sh` green (71s), landed
  on `live-defi-rollout` (quickmerge verified ancestor of origin).

  **Residual, NOT fixed here** (detector-side, different component/root cause — folded into the existing tracked
  detector-blindspot doc instead of a new fix): even after this MDPS fix, once a pre-genesis-bounded shard (like
  mdps-defi-2022's dex_pool_swaps window) is fully converged (nothing left to capture — everything is either `captured`
  from an earlier VM's run or now honestly `expected_unattempted`), a FRESH VM launch for that same year-shard writes
  ZERO rows to ITS OWN `_index/per_vm/{new-vm-name}.parquet` (skip-if-fresh means it never gets far enough to write
  anything at all) — so `exit_code_fleet_monitor`'s captured-delta reads 0->0 for that run too, on every future dispatch
  of the shard, indefinitely. DP-VM-002 cannot currently distinguish "genuinely fully caught up, nothing to do" from
  "silently broken" at the per-VM-shard granularity. This is the same detector limitation class already tracked in
  `dp_vm_002_detector_generic_alert_text_and_bucket_kind_blindness_2026_08_09.md` (added as finding 4 there, not
  duplicated as a new doc).
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-data-processing-service, deployment-service]
scope: [engineer]
tags: [dp-vm-002, mdps, defi, expected-unattempted, honest-absence, pre-genesis, false-positive, fixed]
related:
  [
    /plans/active/issues/dp_vm_002_detector_generic_alert_text_and_bucket_kind_blindness_2026_08_09.md,
    /plans/active/issues/dp_vm_002_cefi_queue_heavy_binancefutu_streaming_writer_progress_gap_2026_08_14.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
source: dp-fleet-monitor
resolved_by: ""
locked_by: ""
created: 2026-08-15
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: small
estimate_baseline: 0.05
calibrated_ai_days: 0.05
assigned_role: infra
drift_direction: advance-code
depends_on: []
context_scope:
  [
    market-data-processing-service/market_data_processing_service/app/core/orchestration_service.py,
    deployment-service/deployment_service/data_pipeline_monitors/_captured_reader.py,
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
---

## What I found

**DP-VM-002 CRITICAL alert `agt-cf60fa` for `mdps-defi-2022-20260815-040833` was a genuine (now-fixed) honest-absence
gap, not a broken VM.** Full evidence chain in the Progress Log below (direct GCS reads of `run.log`, `EXIT_STATUS`, and
the raw `market-data-tick-defi-prd-central-element-323112` bucket).

## Why it matters

A candle-derivation catch-up shard with a permanently-empty pre-genesis window for even ONE of its ~34 data_types would
otherwise re-list and re-skip that same window on every future dispatch forever — wasted VM compute, and (per this
alert) a recurring CRITICAL page indistinguishable from a real silent-zero failure. The MDPS honest-absence gap is now
closed; the residual detector-side blind spot (documented above) is tracked as an addition to the existing DP-VM-002
detector issue doc rather than duplicated here.

## Recommended decision

1. **Code fix already shipped** — `market-data-processing-service@e146759701`. No further code change needed for THIS
   specific alert.
2. **Close this escalation** once folded into the tracked detector-blindspot doc (see Progress Log).
3. Operator note: this same pre-genesis-within-a-year-shard pattern likely recurs for other MDPS asset_group/year
   combinations (e.g. any data_type whose real genesis lands mid-way through a launcher's year-shard window) — worth a
   fleet-wide sweep if DP-VM-002 pages recur for other `mdps-<ag>-<year>-*` VMs after this fix, to confirm each is the
   same already-fixed class vs a genuinely new gap.

## Todos

- [x] [CODE] P2. Fix `_resolve_files_to_process` to record `expected_unattempted` on a zero-raw-file (data_type, date)
      cell instead of leaving no manifest trace. Repo: market-data-processing-service. Evidence:
      market-data-processing-service@e146759701 (quality-gates.sh green, verified ancestor of origin/live-defi-rollout).
- [ ] [DATA] P3. If DP-VM-002 pages again for another `mdps-<asset_group>-<year>-*` VM after this fix, confirm via the
      same direct-run.log-read method whether it is the identical pre-genesis-data_type class (already covered by this
      fix) or a genuinely new gap before treating it as resolved. Repo: market-data-processing-service.

## Progress Log

- 2026-08-15 (data_pipeline_failure escalation agt-cf60fa, slot 31): Read escalation context + domain SSOTs
  (data-pipeline-alerts.md, availability-manifest-and-data-status.md, honest-absence-downstream-handling.md) + the two
  related open DP-VM-002 issue docs (generic-alert-text/bucket-kind-blindness; cefi-queue-heavy false-positive
  precedent). Confirmed the target VM is MDPS (market-data-processing-service), not MTDS — `mdps-defi-` prefix routes to
  `launch-mdps-sharded-backfill.sh` via `launcher_registry.py`. Confirmed via `gcloud compute instances list` the VM is
  gone (5 sibling `mdps-defi-2022-*`-era VMs currently running are the SAME launcher's per-year DeFi fan-out —
  2022/2023/2024/2025/2026 — not repeated relaunches of just 2022). Read `EXIT_STATUS` (0, clean) and the full 513KB
  `run.log` directly via UTL `get_storage_client()`: all 61 dates (2022-11-01..2022-12-31) show "0/0 succeeded, 0
  errors", zero exceptions/tracebacks. Isolated the cause to `dex_pool_swaps` being the only "missing" data_type every
  date, with `Listed 0 files ... for data_type=dex_pool_swaps` on all 122 checks. Directly listed the raw
  `market-data-tick-defi-prd-central-element-323112` bucket for `day=2022-11-01`/`2022-12-31` (0 dex_pool_swaps blobs,
  but real oracle_prices/gas_fees/lending_indices blobs present) vs `day=2023-01-01` onward (2000-9000+ dex_pool_swaps
  blobs) — confirmed dex_pool_swaps genuinely has no defi coverage before 2023-01-01, a real upstream MTDS genesis
  boundary the launcher's own `DEFI_YEARS="2022 2023 2024 2025 2026"` comment ("raw_tick_data begins 2022-11-01")
  doesn't account for per-data_type. Read `orchestration_service.py`'s `_resolve_files_to_process` /
  `_process_data_type` / `_record_expected_unattempted_on_skip` and confirmed the category-level honest-absence write
  pattern exists but was never applied at the per-data_type zero-files branch. Shipped the fix
  (`market-data-processing-service@e146759701`) + a regression test asserting the honest-absence write now fires; full
  `quality-gates.sh` green. Filed this issue doc + appended finding 4 to
  `dp_vm_002_detector_generic_alert_text_and_bucket_kind_blindness_2026_08_09.md` for the residual detector-side blind
  spot. Pinging authoring slot `dp-fleet-monitor` (not a numbered slot — skipping per role instructions).
