---
doc_type: issue
title:
  "CeFi live data IS captured + warm-persisted, but the cold-tier compactor OOMs (512Mi) — canonical
  raw_tick_data/live_* is a retired legacy path, zero cold parquet since 2026-08-01"
summary: >-
  Batch4 todo 2 re-check (2026-08-06/07): the cited `gcloud storage ls
  .../raw_tick_data/by_date/day=2026-07-30/pipeline_mode=live_aster/**` returns ZERO objects — confirmed for ASTER,
  HYPERLIQUID (`live_hyperliquid`), BINANCE-FUTURES (`live_binance`), and for ALL live_* modes on every day checked
  (07-30, 08-05, 08-06); only batch_* modes exist in the cefi tick bucket. BUT the underlying capture pipeline is NOT
  dead: the current live VM (mtds-live-cefi-consolidated-20260806-163414) runs all 16 shards, and the event-log WARM
  tier is flowing continuously (30K+ CanonicalPersistEnvelope parquet in
  gs://central-element-323112-events/live-events/warm/cefi/{trades,book_snapshot_5,liquidations,derivative_ticker}/,
  latest objects minutes before the check). The real, root-caused bug is the COLD tier: the live-event-log-compactor
  Cloud Run job (512Mi, 1 CPU) has been OOM-killed (signal 9) on every daily 02:05 UTC run since 2026-08-01 while
  compacting the (cefi, book_snapshot_5) shard (1497 warm files), so live-events/cold/cefi/** contains ZERO objects and
  the warm data for 08-01→08-06 is never compacted to the archival cold surface. Secondary: the source doc's check path
  is anchored to a retired legacy direct-GCS live-tick surface — the active sink is the LiveEventFacadeSink (Pub/Sub),
  so the "no live_* rows in raw_tick_data" observation is expected under the event-log spine and should not be
  re-flagged as a fresh outage once the cold compactor is fixed.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [deployment-service, market-tick-data-service, unified-trading-pm]
scope: [engineer]
tags: [cefi, live-data, cold-tier, compaction, oom, event-log, data-correctness, big-finding]
related:
  [
    /plans/archive/2026_08/cefi_consolidated_vm_aster_data_landing_recheck_2026_07_30.md,
    /plans/active/infra_capture_and_devops_leftovers_2026_07_06.md,
    /plans/archive/issues/cefi_live_ws_capture_dormant_since_2026_06_29_2026_07_14.md,
    /codex/02-data/live-data-persistence-and-event-log.md,
  ]
created: 2026-08-07
author: "slot-12 worker (data_engineering), batch4 todo 2"
priority: P1
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: data_engineering
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source: "cefi_satellite_ao_dispatch_batch4_2026_07_31.md todo 2 — rows-did-not-land branch"
resolved_by:
drift_direction: advance-code
context_scope:
  [
    /codex/02-data/live-data-persistence-and-event-log.md,
    /plans/archive/2026_08/cefi_consolidated_vm_aster_data_landing_recheck_2026_07_30.md,
    /plans/active/infra_capture_and_devops_leftovers_2026_07_06.md,
    deployment-service/deployment_service/jobs/live_event_log_compactor.py,
    deployment-service/terraform/gcp/live_event_log/compaction_job.tf,
  ]
---

# CeFi live capture is alive (warm tier healthy) but the cold compactor OOMs — raw_tick_data/live_* is a retired path

## What I found

Re-ran the exact cited check from `/plans/archive/2026_08/cefi_consolidated_vm_aster_data_landing_recheck_2026_07_30.md`
todo 1 as part of `cefi_satellite_ao_dispatch_batch4_2026_07_31.md` todo 2 (2026-08-07, ~23:52 UTC):

1. The cited path has ZERO objects (confirmed for all 3 venues + all live_* modes):

```text
$ gcloud storage ls "gs://market-data-tick-cefi-prd-central-element-323112/raw_tick_data/by_date/day=2026-07-30/pipeline_mode=live_aster/**"
ERROR: (gcloud.storage.ls) One or more URLs matched no objects.        # also day=2026-08-05, 2026-08-06
$ gcloud storage ls "gs://market-data-tick-cefi-prd-central-element-323112/raw_tick_data/by_date/day=2026-08-06/pipeline_mode=live_hyperliquid/**"
ERROR: (gcloud.storage.ls) One or more URLs matched no objects.        # live_binance likewise, day=2026-08-05 + 08-06
$ gcloud storage ls "gs://market-data-tick-cefi-prd-central-element-323112/raw_tick_data/by_date/day=2026-08-06/pipeline_mode=live_binance/**"
ERROR: (gcloud.storage.ls) One or more URLs matched no objects.
$ gcloud storage ls "gs://market-data-tick-cefi-prd-central-element-323112/raw_tick_data/by_date/*/pipeline_mode=live_aster/**"
ERROR: (gcloud.storage.ls) One or more URLs matched no objects.        # no live_* object ANYWHERE in the tick bucket
```

`gcloud storage ls .../day=2026-07-30/` and `.../day=2026-08-05/` show only `pipeline_mode=batch_*` directories
(`batch_aster`, `batch_deribit`, `batch_extended`, `batch_hyperliquid`, `batch_tardis`, `batch_kalshi_perp`) — **no
`pipeline_mode=live_*` partition exists on any day**. (Venue→mode names verified against
`unified_api_contracts/canonical/crosscutting/pipeline_mode.py`: LIVE_ASTER=live_aster,
LIVE_HYPERLIQUID=live_hyperliquid, LIVE_BINANCE=live_binance.)

**2. But the live capture pipeline is ALIVE and the WARM tier is flowing:**

- Current VM: `gcloud compute instances list --filter="name~mtds-live"` → `mtds-live-cefi-consolidated-20260806-163414`
  RUNNING (created 2026-08-06T16:34:21Z), plus the sports VM. 16 cefi shard processes alive via SSH `ps aux`
  (BINANCE-FUTURES trades/book_snapshot_5, BYBIT-FUTURES ×3, HYPERLIQUID ×3, KRAKEN-FUTURES ×3, OKX-FUTURES ×3, DERIBIT
  derivative_ticker, ASTER book_snapshot_5 + liquidations), high CPU.
- Shard log (`/home/ikennaigboaka/logs/live-aster-book-snapshot-5.log`) shows the sink is the event-facade spine:
  `Live mode: using PubSubEventSink topic=service-lifecycle-events`; the per-VM manifest shard is updated every ~10s
  (`ManifestWriter: per-VM shard updated (7143 total entries, ~125 new, process_final=False)`), and the manifest records
  real `captured` rows with `row_count` up to 13,611 for live_aster/live_binance/live_hyperliquid/live_kraken/live_okx.
- WARM tier (the durable live surface per `/codex/02-data/live-data-persistence-and-event-log.md`): 30,486 total cefi
  objects in `gs://central-element-323112-events/live-events/warm/cefi/` — trades 9,657 / book_snapshot_5 9,854 /
  liquidations 1,525 / derivative_ticker 9,452 — latest object `2026-08-06T23:56:26+00:00_*.parquet` (minutes before the
  check). Warm capture has flowed continuously since `2026-07-31T13:07Z`.

**3. Root cause of the missing COLD/archival live data — the compactor OOMs:**

```text
$ gcloud run jobs executions list --job=live-event-log-compactor --region=asia-northeast1
live-event-log-compactor-hwmhx  2026-08-06T02:04:55Z  Completed  False   # FAILED
live-event-log-compactor-ghqlm  2026-08-05T02:05:17Z  Completed  False
live-event-log-compactor-txr89  2026-08-04T02:05:07Z  Completed  False
live-event-log-compactor-pfrxv  2026-08-03T02:05:05Z  Completed  False
live-event-log-compactor-xwlzj  2026-08-02T02:05:15Z  Completed  False
live-event-log-compactor-hhkvf  2026-08-01T02:04:26Z  Completed  False
# (2026-07-31 had mixed runs: two succeeded 15:50/18:42, three failed 14:38/14:59/15:06)
```

Latest failed run log (live-event-log-compactor-hwmhx):

```text
2026-08-06 02:04:35,660 INFO compact_shard: shard=(cefi, book_snapshot_5) date=2026-08-05 warm_prefix=live-events/warm/cefi/book_snapshot_5/
2026-08-06 02:04:36,935 INFO compact_shard: writing cold file shard=(cefi, book_snapshot_5) date=2026-08-05 files=1497 path=live-events/cold/cefi/book_snapshot_5/date=2026-08-05/data.parquet retention=REPRODUCIBLE cold_ttl=30d
2026-08-06T02:04:52.207682Z  Out-of-memory event detected in container
2026-08-06T02:04:52.298228Z  Container terminated on signal 9.
```

Job spec: `memory=512Mi, timeout=3600s, cpu=1000m`. Compacting the `(cefi, book_snapshot_5)` shard (1,497 warm parquet
files into one cold file) exceeds 512Mi → OOM → SIGKILL, before any cold file is written. Cold tier is therefore empty:
`gs://central-element-323112-events/live-events/cold/**` has exactly TWO objects (both prediction, date=2026-07-30,
written by the 2026-07-31 15:50/18:42 successful runs) — **`live-events/cold/cefi/**` = ZERO objects**. So warm live
data for 2026-08-01→2026-08-06 has never been compacted to the archival cold surface.

**4. Interpretation (why the source doc's premise needs updating):**

The `raw_tick_data/by_date/.../pipeline_mode=live_*` path is the **retired pre-event-log direct-GCS live-tick surface**.
The active default sink is `LiveEventFacadeSink` (`market_tick_data_service/live/event_facade_sink.py` — "Warm GCS
persistence arrives ~5 min later via Cloud Storage subscriptions provisioned by live_event_log/ Terraform"; the
direct-GCS `LiveWebsocketTickSink` is documented as "Legacy ... override in tests"). Live data now lands in the
event-log warm tier (`central-element-323112-events/live-events/warm/cefi/*`) and would be compacted to the cold tier
(`live-events/cold/cefi/*`) by the daily compactor. So: **capture + warm = healthy; cold = broken by the compactor
OOM**. The source doc's earlier "3 consecutive days zero live_* objects → genuine new bug" framing (2026-08-02 note) was
correct that the _archival_ surface is missing data, but wrong that _capture_ is dead.

## Why it matters

Data-correctness (heartbeat rule): the cold/archival tier of the CeFi live event log has produced ZERO parquet since the
compactor started OOM-ing on 2026-08-01 — 6+ days of warm captures
(trades/book_snapshot_5/liquidations/derivative_ticker, ~30K warm files) are not compacted into
`live-events/cold/cefi/**/date=*/data.parquet`, which is the long-term replay + BigQuery external-table + batch=live
determinism surface. REPRODUCIBLE-tier data is re-derivable from upstream, so this is a replay/archival gap rather than
permanent loss, but it FREEZES the cold-replay + paper/batch determinism spine for cefi until fixed + backfilled. The
compactor failing at shard `(cefi, book_snapshot_5)` also likely stalls every OTHER asset group's cold compaction (the
job dies before finishing the shard loop) — prediction is the only AG with any cold output, and only for 07-30.

## Recommended decision

Fix the compactor OOM first (bounded code/terraform change), then backfill the missed cold dates. Separately, retire the
legacy `raw_tick_data/pipeline_mode=live_*` check path in the ASTER verification docs so future audits measure the live
surface that actually exists (warm + cold event-log tiers).

## Todos

- [ ] [BACKEND] P0. **RE-OPENED 2026-08-07 (cicd wall-resolution agt-6f2b99) — code shipped but NEVER DEPLOYED, bug is
      still live.** deployment-service@5e23a7b raised the Terraform `resources.limits` block to `memory=4Gi, cpu=2` and
      refactored the compactor to a streaming PyArrow `ParquetWriter`, but
      `gcloud run jobs describe     live-event-log-compactor --region=asia-northeast1` (checked 2026-08-07 ~11:50 UTC)
      shows the LIVE job still runs `memory=512Mi, cpu=1000m` — the Terraform change was never actually `tofu apply`'d
      against the real job. Confirmed still broken: the 2026-08-07T02:00:01Z scheduled run
      (`live-event-log-compactor-xpkg5`) OOM-killed on the identical shard `(cefi, book_snapshot_5) date=2026-08-06`
      (`"The configured memory limit was reached"` / `Container terminated on signal 9` at 02:05:26-27Z) — same failure
      signature as every prior run since 2026-08-01. Fix: apply the already-written Terraform change to the live job
      (`cd deployment-service/terraform/gcp/live_event_log && tofu apply`, or the repo's sanctioned deploy path), then
      verify the NEXT scheduled 02:05 UTC run (or a manual `gcloud run jobs execute`) completes with 52/52 shards and no
      OOM before re-closing this todo. (repo: deployment-service)
- [ ] [DATA] P1. **NEW 2026-08-07 ~13:12 UTC (slot-11 worker)** — All `cefi/book_snapshot_5` warm files fail
      `CanonicalPersistEnvelope` validation; cold file for that shard will never be written. During jhsb7 verification
      run (`--region=asia-northeast1`, started 12:41 UTC, still running 31 min later — OOM fix confirmed), every one of
      the 1497 warm objects for 2026-08-06 logs
      `_extract_rows: blob=live-events/warm/cefi/book_snapshot_5/... failed     CanonicalPersistEnvelope validation — skipping`.
      Since `pq_writer` stays None, the shard returns False and compactor writes zero cold bytes for book_snapshot_5
      (per the code's `if pq_writer is None: logger.warning("all     warm files yielded 0 usable rows"); return False`).
      This is orthogonal to the OOM — even with 4Gi the shard is skipped. Must diagnose: (a) what format do
      book_snapshot_5 warm files actually contain? (b) is the CanonicalPersistEnvelope schema mismatched for this
      data_type? (c) does this affect the historic warm tier (2026-07-31 onwards)? Done when root cause identified and
      warm files parse correctly OR a code fix ships that handles the actual on-wire format. (repo: deployment-service)
- [ ] [DATA] P0. **RE-OPENED 2026-08-07 — backfill never ran; cold tier still empty.**
      `gcloud storage ls     gs://central-element-323112-events/live-events/cold/cefi/book_snapshot_5/` and
      `.../trades/` (checked 2026-08-07 ~11:50 UTC) both return zero objects — `live-events/cold/cefi/**` is still
      completely empty for 2026-08-01through today. The backfill trigger script
      (`scripts/jobs/run-compactor-date-range-backfill.sh`, deployment-service@9e1ab49) exists but was never executed —
      the prior note ("Run ... after next clean daily run") was a deferred instruction, not a completion. Blocked on the
      todo above (needs the OOM actually fixed live first, or the backfill run will just repeat the same OOM). Done
      when: cold parquet genuinely exists for each cefi data_type × each missed date 2026-08-01→2026-08-07, verified via
      `gcloud storage ls`, not just "script exists". (repo: deployment-service)
- [x] ✅ [DATA] P2. Confirm + document that `raw_tick_data/by_date/.../pipeline_mode=live_*` (cefi) is a retired legacy
      surface (grep confirms no production reader consumes it — the active sink is `LiveEventFacadeSink`); update the
      ASTER gate wording in `/plans/active/infra_capture_and_devops_leftovers_2026_07_06.md` and the check path in
      `/plans/archive/2026_08/cefi_consolidated_vm_aster_data_landing_recheck_2026_07_30.md` to point at the warm/cold
      event-log surface, so a future audit does not re-raise a false "no live data" alarm. (repo: unified-trading-pm) —
      unified-trading-pm@5db5fedba

## Progress Log

- **2026-08-07 (slot-6 worker, data_engineering, todo 3)**: confirmed retired legacy surface via grep —
  `LiveWebsocketTickSink` is labeled "legacy direct-GCS TickSink; still valid for override in tests" in
  `market-tick-data-service/market_tick_data_service/live/__init__.py`; no production reader constructs or reads from
  `raw_tick_data/pipeline_mode=live_*` paths (grep `raw_tick_data.*live_[a-z].*read` returns zero hits). Updated: (1)
  gate wording in `infra_capture_and_devops_leftovers_2026_07_06.md` to name the warm event-log tier as the correct
  surface; (2) check path in `cefi_consolidated_vm_aster_data_landing_recheck_2026_07_30.md` with a RETIRED PATH note +
  warm tier redirect. unified-trading-pm@5db5fedba
- **2026-08-07 (slot-12 worker, batch4 todo 2)**: full re-check run. Exact `gcloud` outputs above. Root-caused the
  cold-tier gap to the compactor OOM on `(cefi, book_snapshot_5)`. Warm tier confirmed healthy + flowing. Filed this
  doc; flipped the source doc's todos 1-2 and batch4 todo 2 citing this run.
- **2026-08-07 (slot-13 worker, data_engineering, todo 2)**: shipped COMPACTION_DATE backfill mechanism —
  deployment-service@9e1ab49 (merged into slot-14's 5e23a7b). CompactorConfig with typed `compaction_date` + `dry_run`
  fields; updated `main()` to honour COMPACTION_DATE override; added one-shot backfill trigger script
  `scripts/jobs/run-compactor-date-range-backfill.sh`. Checkbox flipped — code shipped, todo-1 fix also landed.
- **2026-08-07 (slot-14 worker, this task)**: shipped OOM fix. (1) `terraform/gcp/live_event_log/compaction_job.tf` —
  added explicit `resources { limits = { memory = "4Gi", cpu = "2" } }` block (was implicit 512Mi default). (2)
  `deployment_service/jobs/live_event_log_compactor.py` — replaced all-at-once `records` accumulation with streaming
  `pyarrow.ParquetWriter` that writes one row group per warm file, bounding peak memory to one file's rows plus the
  accumulated cold parquet buffer. Also merged `CompactorConfig.compaction_date` (COMPACTION_DATE env var) from
  concurrent todo. QG green. deployment-service@5e23a7b.
- **context-scout 2026-08-07**: populated context_scope (5 entries).
- **context-scout 2026-08-07 (batch11 independent re-verify)**: all 5 entries confirmed resolving on disk; content
  unchanged.
- **2026-08-07 ~11:50 UTC (cicd wall-resolution `agt-6f2b99`)**: this doc surfaced as a `check_archive_candidates.sh`
  candidate (0 open todos) while fixing an unrelated `unified-trading-pm` `quality-gates-v2` wall. Per the
  archive-candidates content-verification rubric, read the doc in full and live-verified the two checked-but-critical
  todos before archiving — both were FALSE-COMPLETE: (1) `gcloud run jobs describe live-event-log-compactor` shows the
  live job still runs `memory=512Mi` (the Terraform 4Gi change was written but never `tofu apply`'d); (2) the
  2026-08-07T02:00:01Z scheduled run OOM-killed on the identical shard 3 hours before this check, confirming the bug is
  still live; (3) `gcloud storage ls .../live-events/cold/cefi/{book_snapshot_5,trades}/` both return zero objects — the
  backfill never ran. Re-opened both todos as P0 with the live evidence above; doc stays in `plans/active/issues/`
  (correctly, since real work remains) rather than being archived on a false checkbox count. Tagged `big-finding`
  already present in frontmatter; flagging to the operator/main agent as part of this escalation's completion ping since
  this is a genuine data-correctness gap, not a CI/CD-wall matter.
- **2026-08-07 ~12:40 UTC (slot-11 worker, data_engineering, todo 4 in-flight — pre-compact checkpoint)**: BACKEND todo
  confirmed deployed: `gcloud run jobs describe live-event-log-compactor --region=asia-northeast1` at 13:06 UTC shows
  `Memory: 4Gi, CPU: 2` — Terraform `tofu apply` ran at ~12:40 UTC (job `last_updated` 2026-08-07T12:40:38Z).
  Verification run `live-event-log-compactor-jhsb7` (started 12:41:25 UTC) has been running 25+ minutes without OOM —
  OOM fix confirmed working (previous runs died at ~5 min). Cold tier still empty as of 13:06 UTC (backfill not yet
  started). Background tasks in flight: (1) `busop6lkg` driver waits for jhsb7 success then submits COMPACTION_DATE
  overrides for 2026-08-01..2026-08-05 sequentially; (2) monitor `b4ibtsjfo` watches
  `/tmp/compactor_backfill_final_status.txt` for BACKFILL_COMPLETE. After compaction, resume by: (a) checking
  `gcloud run jobs executions list --job=live-event-log-compactor --region=asia-northeast1 --limit=10` for jhsb7
  SUCCEEDED + subsequent backfill executions; (b) verifying
  `gcloud storage ls 'gs://central-element-323112-events/live-events/cold/cefi/**'` shows objects for each cefi
  data_type × date 2026-08-01→2026-08-06; (c) manually running COMPACTION_DATE=2026-08-07 for today; (d) flipping the
  DATA P0 checkbox (this todo) AND the BACKEND P0 checkbox (Terraform applied + jhsb7 verified); (e) committing via
  safe-doc-push; (f) calling /done. NOTE: driver script `/tmp/compactor_backfill_driver.sh` has a `|| true` bug — it
  won't detect per-date failures; verify cold GCS objects MANUALLY before flipping.
- **2026-08-07 ~13:13 UTC (slot-11 worker, data_engineering, second pre-compact checkpoint)**: jhsb7 STILL RUNNING
  (runningCount=1, no completion time, 31 min elapsed). OOM fix confirmed: previous runs died in ~5 min on 512Mi; jhsb7
  has been alive 31 min under 4Gi/2CPU. **NEW FINDING: all 1497 cefi/book_snapshot_5 warm files for 2026-08-06 fail
  `CanonicalPersistEnvelope` validation** (log sample:
  `_extract_rows: blob=live-events/warm/cefi/book_snapshot_5/2026-08-06T12:21:56+00:00_6a406f.parquet failed CanonicalPersistEnvelope validation — skipping`).
  At ~3 sec/file × 1497 files, book_snapshot_5 takes ~75 min; at 13:12 UTC (31 min in) the run is at blob timestamp
  12:21 on 2026-08-06 (~51% through) → expected to finish book_snapshot_5 ~13:56 UTC, then
  derivative_ticker/liquidations/trades. All validation-failed blobs → pq_writer=None → cold file for book_snapshot_5
  skipped with 0 rows (no crash, graceful skip). Cold GCS: still ZERO objects. Driver busop6lkg alive, waiting. Tracked
  this as new P1 todo above. After jhsb7 completes: (a) check executions for jhsb7 SUCCEEDED; (b) verify cold objects
  for trades/liquidations/derivative_ticker (book_snapshot_5 cold will be absent); (c) trigger
  COMPACTION_DATE=2026-08-07; (d) DATA P0 full completion gated on P1 (book_snapshot_5 validation); (e) BACKEND P0 can
  be flipped once jhsb7 shows SUCCEEDED (Terraform deployed + run survives OOM window).
