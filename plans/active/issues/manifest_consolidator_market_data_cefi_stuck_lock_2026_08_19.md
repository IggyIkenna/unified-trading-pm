---
doc_type: issue
title: "Manifest consolidator for market-data-tick-cefi stuck on a phantom lock since ~2026-08-18T02:14Z — 40+ hourly cycles skipped, zero alerts fired"
summary: >-
  LIVE, ONGOING P0 (as of 2026-08-19T19:50Z). The `uts-prod-manifest-consolidator-market-data-cefi` Cloud Run job IS
  running on its documented hourly schedule and reporting `Completed / True` every cycle — this is NOT a job-down
  incident. Its own Cloud Logging output shows every cycle short-circuits on `error=locked` ("fresh lock present —
  sibling cron still running") and writes ZERO rows while still exiting 0. The canonical
  `market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet` has not changed (same
  generation/last_modified) in ~41.6h against an 86400s/24h budget. This is the actual, currently-live root cause of
  why the liquidations wrong-inverse-notional re-derive (data_pipeline_alert_storm_root_cause_batch_2026_08_10.md P0)
  died with `ManifestConsolidatorStaleError`-class failures on 2026-08-18 — NOT the margin_type/contract_size bugs
  previously tracked (all fixed, see cefi_inverse_contract_size_wrong_and_missing_2026_08_12.md). Blocks ANY
  market-data-tick-cefi backfill/reprocess hitting the loud-fail read guard, not just liquidations. Zero
  CONSOLIDATOR_DOWN/CONSOLIDATOR_STALE/MANIFEST_CONSOLIDATION_FAILED alerts found in #data-pipeline-alerts across the
  full 72h window despite a documented dedicated liveness watchdog that should catch exactly this.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [unified-trading-library, deployment-service, market-data-processing-service]
scope: [engineer, admin]
tags: [manifest, consolidator, infrastructure, data-correctness, stuck-lock, cefi, incident]
related:
  [
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md,
    /plans/active/issues/cefi_inverse_contract_size_wrong_and_missing_2026_08_12.md,
  ]
context_scope:
  [
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    unified-trading-library/unified_trading_library/manifest_consolidator.py,
  ]
created: 2026-08-19
author: claude-agent
source: "plan_reconciler sports-tranche run (agt-07473e), live-status check ordered by operator ruling BLK-7d1f4a2d"
priority: P0
parent_epic: mtds_mdps_master
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
---

# Manifest consolidator for market-data-tick-cefi stuck on a phantom lock — 2026-08-19

## What's confirmed (all measured live, this session, 2026-08-19T19:4x-19:5xZ)

1. **Canonical index frozen.** UTL `get_storage_client().get_blob_metadata('market-data-tick-cefi-prd-central-element-323112', '_index/availability_index.parquet')` →
   `last_modified='2026-08-18T02:13:57.708000+00:00'`, `generation=1787019237694916`, `metadata=None`. Current time at
   measurement: `2026-08-19T19:50:38Z` → **staleness ≈ 149,801s (~41.6h)**, vs the documented 86400s/24h loud-fail
   budget (`manifest-consolidator-ssot.md` § "Liveness + health contract").
2. **The Cloud Run job itself is healthy and on-schedule — this is NOT a "job not running" incident.**
   `gcloud run jobs executions list --job=uts-prod-manifest-consolidator-market-data-cefi --region=asia-northeast1
   --project=central-element-323112 --limit=15` shows clean hourly firings all through 2026-08-19 (12:00, 13:00,
   13:34, 14:00, 15:00, 15:35, 15:49, 16:00, 16:34, 17:00, 18:00, 19:00, 19:34), every one `status.conditions[0].status=True
   "Execution completed successfully"` — matching the documented hourly `0 * * * *` schedule for the `market-data-cefi`
   category (`manifest-consolidator-ssot.md` line ~76-82). Two executions ran anomalously long vs the typical ~1min:
   `rsgbc` 13:34:59→15:36:14 (2h1m15s) and `nfgs5` 16:34:58→18:33:05 (1h58m7s) — every other execution both before and
   after these two completed in 50s-2min as normal.
3. **Root cause, direct from Cloud Logging** (most recent completed execution,
   `uts-prod-manifest-consolidator-market-data-cefi-wx25q`, 2026-08-19T19:00:53Z→19:01:26Z):
   ```
   19:00:53 INFO Event logging initialized: mode=live, service=manifest-consolidator
   19:01:02 INFO ManifestConsolidator: skipping cycle for bucket=market-data-tick-cefi-prd-central-element-323112 — fresh lock present (sibling cron still running)
   19:01:18 manifest-consolidator bucket=market-data-tick-cefi-prd-central-element-323112 success=True shards=0 rows_in=0 rows_out=0 dedup_dropped=0 legacy_seeded=False pruned_shards=0 latency_ms=25371.0 error=locked at=2026-08-19T19:01:18.886709+00:00
   19:01:20 Container called exit(0).
   ```
   **Every hourly cycle reports `success=True` while doing ZERO work (`shards=0 rows_in=0 rows_out=0`) because it
   believes a sibling cron is still running and defers to it.** This is why the job "completing successfully" every
   hour (point 2) is fully consistent with the canonical index never actually moving (point 1) — the job isn't failing,
   it's perpetually no-op'ing on a lock it never clears.
4. **Direct causal chain to the operator's original question** (BLK-7d1f4a2d, answered decision A: "dispatch a
   live-status check now"). The liquidations re-derive VM `mdps-backfill-cefi-20260816-162418` (relaunched 2026-08-16
   16:24 UTC, `--date-concurrency 2`, tracked in
   `cefi_inverse_contract_size_wrong_and_missing_2026_08_12.md`'s "Still open" P0 monitor-to-completion item) ran its
   full 2223-date range to completion (`🏁 Date range complete: 2020-01-01..2026-01-31`) but exited
   `Handler returned non-zero exit code: 1` at 2026-08-18T02:04:52Z, `VM_SHUTDOWN_ON_COMPLETION=true` self-deleted it
   immediately after. Its own `run.log` tail (read via UTL `gcs_read_object_range`, bucket
   `deployment-scripts-central-element-323112`, `vm-logs/mdps-backfill-cefi-20260816-162418/run.log`, last 60KB) shows
   **every date from at least 2026-01-22 through 2026-01-31 failed identically**:
   `Error processing cefi: Manifest consolidator appears DOWN for bucket='market-data-tick-cefi-prd-central-element-323112':
   consolidated _index/availability_index.parquet heartbeat is 96769s old (> 86400s budget) while per-VM shards exist.`
   — staleness climbing 96769s→96824s across the tail (consistent with the canonical having last genuinely updated
   ~2026-08-16T23:11Z, i.e. **before** the one write this doc's point 1 canonical shows at 02:13:57 on 08-18 — meaning
   the phantom lock most likely first armed sometime shortly after that 02:13:57 write, and has held continuously
   since). `PROGRESS.json`'s own checkpoint (`last_completed_date="2023-05-13"`, `updated="2026-08-17T23:06:51Z"`)
   froze there because it only advances on genuine success — the job kept iterating dates for another ~3h afterward
   with zero further progress, all absorbed by this same consolidator-stale guard, before the handler gave up.
   **This is a NEW root cause, distinct from and downstream of everything already fixed in
   `cefi_inverse_contract_size_wrong_and_missing_2026_08_12.md`** (contract_size, margin_type, shard-isolation,
   NaN-warning — all genuinely shipped and correct). The margin_type/contract_size population itself has NOT been
   re-verified against a fresh, uncorrupted-by-this-outage re-derive attempt.
5. **Zero alerting found.** `scripts/dev/slack-read-channel.py data-pipeline-alerts 72` (7,584 alert lines, 2026-08-16
   through 2026-08-19) has **zero** hits for `CONSOLIDATOR_DOWN`, `CONSOLIDATOR_STALE`, `ManifestConsolidatorStale`,
   `consolidator appears down`, or `MANIFEST_CONSOLIDATION_FAILED` — despite `manifest-consolidator-ssot.md` §
   "Liveness + health contract" documenting a dedicated `uts-prod-consolidator-liveness-watchdog` Cloud Run Job +
   `*/2 * * * *` Cloud Scheduler cron specifically built to emit `CONSOLIDATOR_DOWN` (ERROR severity) on exactly this
   condition, "Live since 2026-06-01 — executions complete 1/1 every 2 min." Either that watchdog isn't actually
   catching this bucket/condition, or its alert isn't reaching `#data-pipeline-alerts` — not independently checked
   this pass (see Next steps).

## Not yet confirmed — needs someone reading the lock's own code path

- **What/where the lock actually is** (a metadata field on the canonical blob, a separate sentinel object, an
  in-memory/Cloud-Run-concurrency assumption) and **why it never expires/clears** — `manifest_consolidator.py`'s lock
  acquire/release logic was not read this pass (outside this role's `plans/**`-only write scope; this is a code-reading
  task for whoever picks this up, not a plans-doc question).
- **Whether either of the two abnormally-long executions today** (`rsgbc` 2h1m, `nfgs5` 1h58m — see point 2) **is the
  lock's actual holder**, still technically live per Cloud Run's own bookkeeping (a hung/zombie container not yet
  reaped) rather than a purely stale/never-released marker. This is the single cheapest thing to check next — if one
  of those executions is provably still running or was force-terminated without cleanup, that's a simpler, more
  contained explanation (and fix — cancel the zombie) than a code bug in the lock's release path.
- The blob's `metadata=None` (point 1) is suggestive of — but not proof of — the exact "marker-strip" incident class
  `manifest-consolidator-ssot.md` already documents as a past, fixed incident. UTL's `get_blob_metadata()` wrapper may
  simply not surface custom object metadata the same way `gcloud storage objects describe --format="value(custom_fields...)"`
  does; this needs the `custom_fields` read specifically, not re-derived from `get_blob_metadata()` alone.
- Whether this same phantom-lock condition affects any of the OTHER 12 hourly-scheduled consolidator categories
  (`instruments-{cefi,tradfi,defi,prediction}`, `features-{cefi,defi,tradfi,calendar}`, `strategy`, `execution`,
  `ml-training-artifacts`) or is scoped to `market-data-cefi` alone — not checked this pass.

## Todos

- [ ] [SCRIPT] P0. **Check whether either of the two abnormally-long executions today is the phantom lock's holder** —
      `gcloud run jobs executions describe uts-prod-manifest-consolidator-market-data-cefi-rsgbc` and `-nfgs5`
      (`--region=asia-northeast1 --project=central-element-323112`; the two runs from point 2 above, 13:34:59→15:36:14
      and 16:34:58→18:33:05, both ~2h vs the normal ~1min). If either is still shown as running, or was force-cancelled
      without releasing its lock, that is the (contained, code-free) explanation — reap/clear it and re-verify point 1
      (canonical blob `generation` advances on the next hourly cycle). Done when: confirmed cause either way.
- [ ] [SCRIPT] P0. **If the zombie-execution check doesn't explain it, read `unified_trading_library/manifest_consolidator.py`'s
      lock acquire/release + staleness-check code**, confirm whether it has any TTL/expiry at all, and fix the gap
      (this workspace's own `manifest-consolidator-ssot.md` already documents a structurally similar "no fallback /
      fails closed" fix for the content-write-marker — the lock most likely needs the same kind of TTL-based
      self-healing, so a crashed/killed holder can't wedge every future cycle forever). Ship via quickmerge, gate
      green. Done when: the fix is live and a fresh hourly cycle genuinely merges (not just reports `success=True`).
- [ ] [SCRIPT] P0. **Verify recovery end-to-end**: confirm the canonical
      `market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet` blob's `generation`/
      `last_modified` has advanced (via UTL `get_storage_client().get_blob_metadata(...)`, never a subprocess
      `gcloud storage`/`gsutil` call — QG-enforced) past `2026-08-18T02:13:57.708000+00:00` /
      `generation=1787019237694916`. If not yet cleared naturally, `gcloud run jobs execute
      uts-prod-manifest-consolidator-market-data-cefi --region=asia-northeast1 --project=central-element-323112`
      (documented SAFE in the SSOT) after the above fix lands. Once confirmed, **re-launch the liquidations re-derive**
      (`cefi_inverse_contract_size_wrong_and_missing_2026_08_12.md`'s own P0 monitor-to-completion item) — the
      contract_size/margin_type fixes are already shipped and correct; this outage was the only remaining blocker.
- [ ] [SCRIPT] P1. **Investigate why the dedicated liveness watchdog (`uts-prod-consolidator-liveness-watchdog`) did
      not alert** on this 41+-hour outage despite being documented live/healthy (point 5 above) — either fold into
      this fix or file as its own follow-up once root-caused; a watchdog that misses the exact condition it exists
      for is itself a gap.

## Progress Log

- **2026-08-19T19:5xZ (plan_reconciler, agt-07473e)**: filed, live-measured as above, alerted via `/blocked` (see
  `plan_reconciler_findings_sports_2026_08_19.md`'s Filed section for the escalation id) and cited into
  `data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`'s Progress Log answering the operator's BLK-7d1f4a2d
  live-status-check order.
- **2026-08-19T20:00:32Z**: `BLK-336884f2` answered by operator — **A** (dispatch an engineer/session to
  investigate+fix the consolidator lock now). Doc flipped `assigned_vm: NA` → `assigned_vm: planning` +
  `execution_scope: orchestrator-agent` this same edit, options above converted to tracked `- [ ]` todos, so AO
  backlog regen picks this up per the operator's decision rather than it sitting as inert prose.
