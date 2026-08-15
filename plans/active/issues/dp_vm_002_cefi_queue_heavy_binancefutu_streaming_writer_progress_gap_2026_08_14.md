---
doc_type: issue
title:
  DP-VM-002 FALSE POSITIVE — VM cefi-queue-heavy-binancefutu-x17-20260809-083733 wrote ~91MB of real CeFi tick data but
  classified SILENT (missing _PROGRESS_RE marker, now fixed)
summary: >-
  Escalation agt-a49b7e: VM cefi-queue-heavy-binancefutu-x17-20260809-083733 (MTDS CeFi queue-heavy sharded backfill,
  launch-cefi-sharded-backfill.sh SINGLE_VM_QUEUE=1 mode) drained with manifest captured 0->0 and was classified
  GONE_NO_CAPTURE/SILENT by the exit-code fleet monitor. Direct GCS read of the persisted run.log (91MB, spanning
  2026-08-09 08:37 to 2026-08-11 15:21 UTC) proves the VM streamed real tick data for ~1,234+ instruments across
  BINANCE-FUTURES/-SPOT, BYBIT, DERIBIT, COINBASE, OKX, KRAKEN, BITFINEX, BITGET, UPBIT — millions of rows via UTL's
  StreamingParquetWriter, reaching chunk ~104/397 (day 2020-12-27) of the 2019-01-01..present coverage window before
  being killed (no EXIT_STATUS, no PREEMPTED marker). Root cause: this launcher family (launch-cefi-sharded-backfill.sh)
  never sets MANIFEST_PER_VM_SHARDS=true — deliberately, to avoid a reader-side OOM class on the CeFi bucket's 1700+
  existing per-VM shards — so `_index/per_vm/{vm}.parquet` never exists and the manifest-shard captured-climb signal is
  permanently blind for the whole family; the run.log-text fallback is the ONLY working no-capture-reason signal, and it
  had no alternative that reliably matched this launcher's real write marker ("StreamingParquetWriter: uploaded ...
  rows"). This run only survived classification by incidentally matching an unrelated Tier-3 sentinel-fan-out
  "captured=N" diagnostic line — a run.log without that coincidence would have false-fired regardless. Fix shipped:
  deployment-service@b7812347ce adds the StreamingParquetWriter marker to `_PROGRESS_RE` + a regression test. VM should
  be re-launched to resume from the 2020-12-21 checkpoint.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [deployment-service, market-tick-data-service]
scope: [engineer]
tags: [dp-vm-002, false-positive, mtds, cefi, streaming-parquet-writer, fixed, relaunch-needed]
related:
  [
    /plans/archive/issues/dp_vm_002_mdps_cefi_2021_silent_zero_false_positive_2026_08_11.md,
    /plans/active/issues/dp_vm_002_detector_generic_alert_text_and_bucket_kind_blindness_2026_08_09.md,
    /plans/active/cefi_track2_coverage_backfill_checkpoints_2026_07_25.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
source: dp-fleet-monitor
resolved_by: ""
locked_by: ""
created: 2026-08-14
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
    deployment-service/deployment_service/data_pipeline_monitors/_gcs.py,
    deployment-service/scripts/vm/launch-cefi-sharded-backfill.sh,
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
---

## What I found

**DP-VM-002 CRITICAL alert `agt-a49b7e` for `cefi-queue-heavy-binancefutu-x17-20260809-083733` is a FALSE POSITIVE.**

Direct GCS read (via UTL `get_storage_client()`, never the blocked `gcloud storage` CLI) of
`gs://deployment-scripts-central-element-323112/vm-logs/cefi-queue-heavy-binancefutu-x17-20260809-083733/run.log`:

| Signal                          | Value                                                                                                                                                                                 |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Run.log size                    | 91,869,131 bytes (91MB)                                                                                                                                                               |
| Run window                      | 2026-08-09 08:37 UTC → 2026-08-11 15:21 UTC (~55h)                                                                                                                                    |
| Launcher                        | `launch-cefi-sharded-backfill.sh`, `SINGLE_VM_QUEUE=1`, `LAUNCH_GROUPS=heavy`                                                                                                         |
| Venues                          | BINANCE-FUTURES, BINANCE-SPOT, BYBIT, BYBIT-SPOT, DERIBIT, COINBASE-SPOT/-FUTURES, OKX-SPOT/-SWAP/-FUTURES, KRAKEN-SPOT/-FUTURES, BITFINEX-SPOT/-FUTURES, BITGET-SPOT/-FUTURES, UPBIT |
| Progress checkpoint             | `last_completed_date=2020-12-21`, `monotonic=true` (chunk ~104/397 of the 2019-01-01..present window)                                                                                 |
| `_index/per_vm/{vm}.parquet`    | **does not exist** (`blob_exists` → False)                                                                                                                                            |
| EXIT_STATUS blob                | Absent (VM killed, no terminal marker)                                                                                                                                                |
| PREEMPTED blob                  | Absent (not a SPOT preemption)                                                                                                                                                        |
| `make_captured_reader()` result | 0 (structurally, for every VM in this launcher family)                                                                                                                                |

The run.log's last 80 lines (right before the VM was killed) show continuous real writes, e.g.
`StreamingParquetWriter: uploaded market-data-tick-cefi-prd-central-element-323112/ raw_tick_data/by_date/day=2020-12-27/.../OKX-SPOT:SPOT_PAIR:UNI-USDT.parquet (1248921 rows, 29 chunks, 39.6 MB)`
— this pattern repeats thousands of times across the 91MB log.

## Root cause confirmed

Two independent, compounding gaps:

1. **`launch-cefi-sharded-backfill.sh` never sets `MANIFEST_PER_VM_SHARDS=true`** (unlike sibling launchers
   `launch-cefi-forward-poll.sh` / `launch-mtds-backfill-vm.sh` / `launch-mtds-live.sh`, which do). This is DELIBERATE —
   the launcher's own comment explains `MANIFEST_CONSOLIDATED_STALENESS_SEC=86400` exists specifically because the CeFi
   bucket already carries 1700+ per-VM shards and reading/merging more causes a reader-side OOM (rc=137) at startup. So
   `_index/per_vm/{vm}.parquet` structurally never exists for this whole launcher family (`cefi-queue-*`,
   `cefi-binance-*`, `cefi-bybit-*`, etc.), and the manifest-shard captured-climb check
   (`captured_before`/`captured_after`) is permanently blind for it — `writes_manifest_shard_for_vm()` still reports
   `writes_shard=True` for this family (registry `bucket=_TICK_CEFI`), so the classifier falls all the way through to
   the run.log-text `no_capture_reason` fallback every time.
2. **`_PROGRESS_RE` had no reliable marker for this launcher's real write signal.** MTDS's CeFi streaming writer logs
   `"StreamingParquetWriter: uploaded ... (<N> rows, ...)"` (via UTL, only ever logged after a genuine non-empty GCS
   write — `row_count==0` returns early with no log line) — but until this fix, no `_PROGRESS_RE` alternative matched
   that text. This specific VM's run.log only survived classification because an UNRELATED Tier-3 per-instrument
   sentinel-fan-out diagnostic line (`"...captured=44)"`) happened to satisfy the separate `captured=(?!0\b)\d+`
   alternative by coincidence — a run.log without that coincidental early match (plausible: the sentinel fan-out only
   runs for pre-genesis dates) would have false-fired `GONE_NO_CAPTURE` despite ~91MB of genuine writes.

**Fix shipped**: `deployment-service@b7812347ce` — added a dedicated `StreamingParquetWriter: uploaded` alternative to
`_PROGRESS_RE` (`deployment_service/data_pipeline_monitors/_gcs.py`)

- a regression test (`test_no_capture_reason_progress_streaming_parquet_writer_uploaded` in
  `tests/unit/test_data_pipeline_monitors.py`). Verified locally: `classify_no_capture_reason()` now resolves this exact
  run.log to `PROGRESS` (was structurally reachable via the coincidental match before the fix too, but is now a durable,
  non-coincidental signal for the whole launcher family). Full `quality-gates.sh` green (298s), landed on
  `live-defi-rollout`.

**Deliberately NOT fixed here** (scope discipline, avoids reintroducing the documented OOM risk): enabling
`MANIFEST_PER_VM_SHARDS=true` for this launcher family so the manifest-shard signal itself becomes non-blind. That is a
real, separate improvement but carries genuine regression risk (the CeFi bucket's existing 1700+-shard OOM class) and
needs its own sizing/ consolidator-load analysis — not a same-turn fix for a false-positive escalation.

## Why it matters

Real, multi-day, multi-million-row CeFi backfill progress was about to be — and for any future run without the
coincidental sentinel-line match, WOULD have been — silently misreported as a total capture failure, right up until this
fix. The DP-VM-002 alert existing to catch genuine silent zeros (auth failure / 0-universe / unexpected empty) is
undermined every time it also fires on real, healthy backfills — each false CRITICAL page erodes trust in the channel
and burns escalation-worker cycles (this one included).

## Recommended decision

1. **Code fix already shipped** — `deployment-service@b7812347ce`. No further code change needed for THIS specific
   false-positive.
2. **Re-launch the VM** — it was killed mid-run (no terminal `EXIT_STATUS`, real progress only to 2020-12-21 of the
   2019-01-01..present window, ~104/397 chunks). Real tick data is already in GCS through 2020-12-27; MTDS's per-shard
   writer is idempotent (skip-if-present), so a fresh `launch-cefi-sharded-backfill.sh` run for the same (group=heavy,
   venues=BINANCE-FUTURES ...) selection should resume forward from the existing coverage rather than re-downloading it.
3. **Close this escalation** once the relaunch is confirmed RUNNING (or already covered by an existing/active CeFi
   coverage-backfill plan — check `/plans/active/cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` first per the
   pre-task plan-conflict-check rule before launching a duplicate VM).

## Todos

- [ ] [OPERATOR] P2. Confirm no `cefi-queue-heavy-binancefutu-x17-*` (or equivalent `LAUNCH_GROUPS=heavy`
      BINANCE-FUTURES-inclusive) VM is already running/queued before re-launching
      (`gcloud compute instances list --filter="name~cefi-queue-heavy"`), then re-launch via
      `launch-cefi-sharded-backfill.sh` with the same venue/group selection to resume CeFi coverage forward from
      2020-12-21. VM launch is [OPERATOR]-tagged per the plan-authoring HARD RULE (any todo with a VM launch needs
      operator sign-off or a stated safe-idempotent justification) — idempotent-skip write path is the stated
      justification; operator confirms no duplicate-VM collision before launch. Repo: deployment-service.

## Progress Log

- 2026-08-14 (data_pipeline_failure escalation agt-a49b7e, slot 30): Read escalation context + domain SSOTs
  (data-pipeline-alerts.md, availability-manifest-and-data-status.md, honest-absence-downstream-handling.md) + the two
  related open DP-VM-002 issue docs. Confirmed the VM terminated (`gcloud compute instances list` — no match) and read
  its 91MB run.log directly via UTL `get_storage_client()`. Confirmed real multi-day writes via
  `StreamingParquetWriter: uploaded` log lines and `PROGRESS.json` checkpoint (`last_completed_date=2020-12-21`).
  Confirmed `_index/per_vm/{vm}.parquet` never existed (launcher never sets `MANIFEST_PER_VM_SHARDS=true`). Traced the
  classifier's actual `_PROGRESS_RE` match to an incidental Tier-3 sentinel-fan-out line, confirming the launcher's real
  write marker had no dedicated regex alternative. Shipped the fix (`deployment-service@b7812347ce`, full
  `quality-gates.sh` green) + this issue doc. Pinged authoring slot `dp-fleet-monitor`.
