---
doc_type: issue
title: Live pipeline — decouple persistence from production hot path (overwrite race + GCS-on-hot-path)
summary:
  "The live pipeline flushes each closed window's ticks to a GCS path keyed by day+instrument with NO window key, so
  window N+1 overwrites N in-place (a live CORRECTNESS RACE if MDPS lags, plus the raw bucket is not a replayable
  archive — breaks paper(W)==batch-rerun(W)); and MDPS reads the just-flushed tick parquet back FROM GCS on the
  production hot path. Decided direction (operator 2026-06-25): Option 2 log-spine — HOT Pub/Sub-with-retention + COLD
  batched hive GCS parquet + BigQuery analytics, off ONE windowing via a UAC envelope + UTL transport facade. Hot-path
  decoupling shipped (LiveEventFacadeSink default at websocket_runner.py:242); status blocked because the durable
  warm-tier (Pub/Sub→Cloud-Storage→GCS parts→daily aggregate) is NOT yet built — tracked in
  mtds_plan_reconciliation_2026_06_29 § Section F M-C7."
status:
  open # corrected 2026-08-10 (plan_reconciler) — the blocking condition (dead compaction job) is live-verified
  # resolved; only item (4) of the sole open todo remains (paper==batch-rerun re-test). (was: blocked)
nature: notes
asset_group: [cross-cutting]
stage: [meta]
repos: [market-data-processing-service, market-tick-data-service]
scope: [engineer, admin]
tags: [live-trading, reconciliation, mtds, mdps, data-correctness, pipeline-mode, uac]
related: [mtds_plan_reconciliation_2026_06_29]
created: 2026-06-24
author: unknown
parent_epic: batch_live_symmetry_master
priority: P2
source:
  [
    operator review 2026-06-24 (prediction arb detector depth-history question),
    market-tick-data-service/market_tick_data_service/live/websocket_runner.py,
    market-data-processing-service/market_data_processing_service/app/core/live_aggregator.py,
    unified-api-contracts/unified_api_contracts/events/streaming.py,
  ]
assigned_vm: NA
resolved_by: live_data_persistence_central_event_log_2026_06_25.md # ANNOTATION 2026-07-14 (verify-rerun-2 finding 21): doc-frontmatter-schema.md requires resolved_by only when status=resolved, but status here is `blocked` per the 2026-06-30 body banner (hot-path decoupling shipped; durable warm-tier still not built) — left populated as a forward-pointer to the plan that partially resolved this issue rather than cleared, because this doc is locked_by: live-defi-rollout (annotate-not-flip per HARD GATE, not a status/archival edit); re-evaluate resolved_by when unlocking for archival
locked_by:
locked_since:
context_scope:
  [
    /codex/02-data/live-data-persistence-and-event-log.md,
    /plans/active/live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md,
    /plans/archive/2026_06/live_data_persistence_central_event_log_2026_06_25.md,
    deployment-service/deployment_service/jobs/live_event_log_compactor.py,
    deployment-service/terraform/gcp/live_event_log/compaction_job.tf,
  ]
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

> **🟡 STATUS CORRECTED 2026-06-30 (consolidation §6 A3.2): `resolved` → `blocked`.** The hot-path decoupling shipped
> (`LiveEventFacadeSink` is the default sink at `websocket_runner.py:242`, publishing off the hot path via the UTL
> transport facade) and the architecture plan `live_data_persistence_central_event_log_2026_06_25` is done/archived —
> BUT the **durable warm-tier (Pub/Sub → Cloud-Storage subscription → GCS parts → daily cron aggregate) is NOT built**
> and is `BLOCKED-CREDENTIALS` / awaiting build greenlight. So `paper(W)==batch-rerun(W)` is not yet provable for live
> data. The remaining build is the operator-decided warm-GCS-parts path tracked in `mtds_plan_reconciliation_2026_06_29`
> **§ Section F M-C7**. Verified in live code by the consolidation pass.

> **🔴 CORRECTION 2026-07-31**: the 2026-07-29 annotation below states "52 `warm-sink-persist-*` Cloud Storage
> subscriptions, confirmed live" — that was true AT THE TIME but is **no longer current**. Live-verified 2026-07-31:
> `gcloud pubsub subscriptions list --filter="name:warm-sink" --project=central-element-323112` returns only **2** of
> the 52 (`warm-sink-persist-prediction-trades`, `warm-sink-persist-prediction-book-snapshot-5`). This is NOT a "never
> applied" bug — Cloud Audit Logs confirm all 52 were genuinely created via `CreateSubscription` on 2026-06-29
> (`c540cd03`) — it is **GCP's native `Subscriber.InternalExpireInactiveSubscription` auto-expiry**: 50 audit-log
> entries of that exact method name, one per now-missing subscription. Pub/Sub auto-deletes a subscription after ~31
> days with zero delivered messages unless `expiration_policy { ttl = "" }` (never-expire) is set; `warm_sink.tf`'s 52
> resource blocks do NOT set `expiration_policy` at all, so every subscription whose topic never received a single real
> published message (i.e. every asset_group×data_type except the 2 prediction ones, which is consistent with the
> SINK_MATRIX finding that only those 2 producers were ever actually wired to publish) silently expired ~2026-07-30.
> **Fix requires BOTH**: (1) add `expiration_policy { ttl = "" }` to all 52 resources so this doesn't recur, AND (2)
> `terraform apply` to recreate the 50 missing ones — a `terraform apply` alone without the policy change will recreate
> them but they will silently expire again in ~31 days if their producer still isn't publishing. Tracked in the new
> fleet-wide plan being drafted per operator instruction 2026-07-31 ("yeah we should do it").

> **🟢 Retagged 2026-07-29 (corpus hygiene pass): resolved-by-reference — see
> `plans/active/june_2026_vintage_audit_findings_2026_07_27.md` §5-RESOLVED item 17 ("M-C7 warm-GCS-parts durable sink
> -- APPROVED to build real code").** The operator build-greenlight this doc's banner above was awaiting is granted —
> the gate itself is resolved, so the todo asking for it is closed below. **Live-verified 2026-07-29 (not assumed) that
> the actual build is still partial**: the warm tier is real (Terraform-applied `deployment-service@c540cd03`
> 2026-06-29, 52 `warm-sink-persist-*` Cloud Storage subscriptions; `gcloud pubsub subscriptions list` confirms all 52
> live; `gs://central-element-323112-events/live-events/warm/prediction/{book_snapshot_5,trades}/` confirms real data
> landing) — but the daily cold-compaction Cloud Run Job (`live-event-log-compactor`) has never once run successfully:
> `gcloud run jobs describe` shows `Ready: False` / `ContainerMissing`
> (`gcr.io/central-element-323112/live-event-log-compactor:latest` was never built/pushed — no `cloudbuild.yaml` step
> references it), `gcloud run jobs executions list` returns zero executions since the job's creation (2026-06-29), and
> `live-events/cold/` is empty in GCS. So `paper(W)==batch-rerun(W)` is still NOT provable for live data. The real
> remaining work is tracked in the new `[CODE]` todo below.

## What I found

The live data pipeline today (verified in code, all asset_groups — surfaced via the prediction Kalshi↔Polymarket book
capture):

1. **MTDS live producer** (`LiveWebsocketRunner`) consumes a continuous WS stream → `UTCAlignedScheduler` windows it
   into UTC-aligned bars (`base_timeframe`). On each closed window boundary it does TWO things:
   - **(persist)** `LiveWebsocketTickSink.flush` writes that window's ticks to GCS at
     `raw_tick_data/by_date/day=<period_end.date()>/pipeline_mode=live_<src>/…/{instrument_id}.parquet` — **path keyed
     by day + instrument only, NO window key**, and the sink writes ONLY the closed window's ticks (no
     read-existing-concat, `websocket_runner.py:155-181`).
   - **(signal)** publishes a `CandleBoundaryCrossedEvent` (period_start/end, tick_count, data_freshness — a SIGNAL, not
     the data) to the Redis stream `streaming.{asset_group}.candle_boundary_crossed` (`StreamPublisher`).
2. **MDPS** (`live_aggregator.py`) is **event-driven** off that Redis stream (good — not a poll), but on each boundary
   event its `_MDPSTickFetcher` **reads the just-flushed tick parquet back FROM GCS** (`default_tick_blob_path(event)`),
   aggregates OHLCV, then publishes `CandleComputedEvent` to `streaming.{asset_group}.candle_computed` for downstream
   (features/strategy).

So the live trigger is pub/sub, but **the raw tick DATA round-trips GCS on the hot path**, and the **raw GCS object is
overwritten every window** (only the latest ~10-min window per instrument per day survives — confirmed empirically:
biggest prediction book files cap at 7–13 min spans; identical re-download 6 min apart).

## Why it matters

Three distinct problems (operator 2026-06-24):

1. **Per-window overwrite is a live CORRECTNESS RACE, not just history loss.** Because the flush path is keyed
   `day+instrument` with no window key, window N+1 overwrites window N's blob in-place. MDPS addresses the blob via the
   boundary event's `default_tick_blob_path(event)` — if MDPS lags one window (backpressure / restart / slow GCS), it
   reads window N's event but the path now holds window N+1's ticks → it aggregates the WRONG window or trips a
   period-mismatch. Under steady state MDPS usually wins the race, but any lag = silent wrong/lost bars. It also means
   the raw bucket is not a replayable archive (breaks the Live=Batch determinism guarantee that
   paper(W)==batch-rerun(W), `citadel_paper_batch_live_reconciliation_2026_06_19.md`).
2. **GCS is on the production hot path.** Boundary event → GCS read of the tick blob → aggregate → publish. A GCS read
   per window per instrument adds latency + a failure surface + cost to the live trading path. At slow bar cadence (15m)
   the ~100–300 ms read is tolerable; at fast timeframes / thousands of instruments it is not. As a production-trading
   principle the hot path should not depend on a GCS round-trip.
3. **Persistence and production are entangled.** The continuous→batch bridge already exists (the scheduler bars the
   stream; a live window-bar == a batch bar == the shared atom, so there is NO real continuous-vs-batch impedance
   mismatch). The problem is that the SAME synchronous GCS write serves both (a) the durable archive and (b) the data
   the hot path reads back — so a slow/failed archive write degrades trading, and a trading-path read failure and the
   archive share one object. They should be two independent fan-out legs of the one windowed bar.

## Recommended decision

Treat these as one coherent change: **one windowing → fan out to (1) an immutable async archive + (2) a hot stream that
carries the bar payload**, with the UTC-aligned bar as the shared Live=Batch atom.

- **Fix #1 (overwrite race) — window-key the raw object, append-only.** Change the flush path to
  `…/{instrument_id}/{period_end_compact}.parquet` (or `{instrument_id}.{period_end}.parquet`) so every window is a
  distinct immutable object; update `default_tick_blob_path(event)` (it already has `period_end`) to address the exact
  window. Removes the race AND makes the raw store a complete append-only archive. Lowest-risk, highest-value; do this
  first. Repos: market-tick-data-service (writer) + market-data-processing-service (reader path) — coordinated, same
  contract.
- **Fix #2 (GCS off the hot path) — carry the bar payload on the stream.** Put the window's ticks/aggregate on the
  `candle_boundary_crossed` event (or a Redis hot-cache of the last N windows) so MDPS + downstream never read GCS in
  the hot path; GCS becomes async, fire-and-forget cold persistence off the critical path. Scope the urgency by
  timeframe × instrument count. Repos: UAC (event schema) + UTL streaming + MTDS + MDPS.
- **Fix #3 (decouple legs) — the windowed bar fans out to two independent consumers:** an async immutable archive write
  (never blocks trading, never overwrites — #1) and a hot stream with payload (the production path — #2). A slow/failed
  archive must not degrade trading; a trading-path hiccup must not corrupt the archive. The bar atom stays identical on
  both legs (Live=Batch).

Governing SSOT this refines: **Live = Batch** (CLAUDE.md §"Live = batch" +
`writegate_honest_coverage_endtoend_2026_05_06.md`

- `/codex/02-data/pipeline-mode-and-batch-live-reconciliation.md`) and the determinism spine
  `citadel_paper_batch_live_reconciliation_2026_06_19.md`. This issue does NOT contradict Live=Batch — it makes the live
  leg actually honor it (immutable per-bar persistence + a hot path that doesn't silently drop bars).

Cross-link: prediction plan `prediction_venue_perps_and_live_clob_depth_2026_06_20.md` P2 (depth-history retention) is a
subset of this — its verify folds into Fix #1/#3.

## Decided direction (operator 2026-06-25) — Option 2: Pub/Sub-with-retention log spine + 3-tier persistence

Chosen: **Option 2 (full log spine)**, realised as a **transport facade** so it stays minimal-blast-radius. Three
independent tiers off ONE windowing, applied uniformly across MTDS / MDPS / features / strategy / ml / execution via a
UAC envelope + UTL facade (the pipeline is identical for every strategy + config):

1. **HOT transport = GCP Pub/Sub (with retention) — the production path.** MTDS publishes the closed-bar envelope
   (payload INLINE — small bars/aggregates fit the 10 MB cap; a rare high-volume raw-tick burst uses a fast hot-cache or
   chunking, NEVER a GCS read) → MDPS + downstream consume on the **event trigger** (sub-second), no store round-trip on
   the hot path. Pub/Sub message retention (≤31d, set to the cleanup window) + `seek`/snapshot = native short-range
   **replay**. **Transport is a facade**: in-memory bus when colocated (paper/backtest single process), Pub/Sub when
   distributed (live) — same envelope + consumer code, so batch==paper==live is "which transport + which read offset,"
   not different code. (Redis is faster/simpler but Pub/Sub-with-retention wins for native replay; the facade keeps it
   swappable.)
2. **COLD archive = GCS parquet, hive-partitioned, BATCHED flush (NOT per-tick).** Do not flush every tick (GCS
   small-file death). Buffer + roll a flush every configurable interval (e.g. 5 min) writing ONE immutable file per
   `(venue, data_type, flush-window)` covering ALL instruments (per-instrument addressing = an `instrument_id` COLUMN +
   predicate pushdown, not per-instrument files). Append-only, never overwrite (kills the race). Layout stays
   hive-friendly: `…/pipeline_mode=…/asset_group=…/venue=…/data_type=…/day=…/[hour=…]/part-<flush_ts>.parquet`. This is
   the long-term + batch-replay store (read beyond the Pub/Sub retention window).
3. **ANALYTICS = BigQuery over the GCS parquet — for plotting/large tick queries.** External table on the hive parquet
   (or a 5-min batch LOAD job) — NOT per-event streaming inserts (cost/quota). The ~5-min flush adds a small delay to
   analytics-table freshness ONLY; it does NOT touch the hot path (which is Pub/Sub-real-time). Two cadences, decoupled:
   real-time (Pub/Sub trigger) for trading; ~5-min batched for archive/analytics.

**Retention class drives the lifecycle** (UAC `RETENTION_CLASS[(asset_group, data_type)]`): REPRODUCIBLE → Pub/Sub
retention + GCS TTL (~7d) then delete (re-derive/backfill beyond; longer TTL / `keep` flag for
reproducible-but-charged-to-refetch e.g. Databento history); STREAM_ONLY/IRREPRODUCIBLE (prediction CLOB depth, live
L2/L3, instantaneous funding, execution fills/positions/PnL + the paper ledger) → GCS + BQ **forever, no TTL** (system
of record; execution/PnL already durable on the UAC global ledger — it just declares `stream_only` through the same
table). Determinism: the cold flush is a FAITHFUL COPY of what was streamed (never a recompute), so batch-replay reads
the identical bars the live consumer saw → paper(W)==batch-rerun(W) holds.

**Minimal-blast-radius:** the policy lives in UAC (the `RETENTION_CLASS` table + the canonical persist/message
envelope), the mechanism in a UTL facade (`publish` → Pub/Sub-or-in-memory; `archive` → batched GCS; `analytics` → BQ;
`read` → offset/replay); the six services change only their I/O call sites to the facade, not their logic. Open
decisions: (a) exact Pub/Sub retention window (7d vs longer) vs GCS handoff point; (b) BQ external-table vs
scheduled-load; (c) hot-cache choice for the rare >10 MB raw-tick burst (Redis vs chunked Pub/Sub).

## PROMOTED to plan (2026-06-25)

Acked into the full phased plan **`plans/active/live_data_persistence_central_event_log_2026_06_25.md`** (parent_epic
`batch_live_symmetry_master`, assigned_vm `human-planning`). Final refinement folded into the plan: **persistence
consumers are native Pub/Sub subscriptions (config, not code)** — a **BigQuery subscription** (warm table) + a **Cloud
Storage subscription** (warm 5-min GCS), and the **GCS archive is TWO tiers** — warm 5-min (BQ-queryable, ~7d) + a
**daily compaction job that rolls the warm 5-min files into cold long-term parquet** (no in-memory buffering, no
per-tick files). This issue doc is the problem-record; the plan is the executable SSOT.

## Todos

- [x] ✅ [DECISION] P2. **Retagged 2026-07-29 (corpus hygiene pass): resolved-by-reference — see
      `plans/active/june_2026_vintage_audit_findings_2026_07_27.md` §5-RESOLVED item 17 ("M-C7 warm-GCS-parts durable
      sink -- APPROVED to build real code").** Build the durable warm-tier (Pub/Sub → Cloud-Storage subscription → GCS
      parts → daily cron aggregate) — previously gated on an operator build-greenlight decision, now granted
      (2026-07-27); without the actual build landing end-to-end, `paper(W)==batch-rerun(W)` is not yet provable for live
      data. Executable SSOT: `plans/active/live_data_persistence_central_event_log_2026_06_25.md` (archived,
      `plans/archive/2026_06/`). **The ask this todo raised — permission to build — is resolved.** The real remaining
      implementation gap is tracked in the new todo below (verified NOT fully landed as of 2026-07-29).

> **🟢 RE-VERIFIED LIVE 2026-08-10 (plan_reconciler).** Original items (1)-(3) below are resolved. Not flipping the
> checkbox since item (4) is unverified.
>
> 5 consecutive successful daily compactor runs, most recently 2026-08-09 (`gcloud run jobs executions list`). Items (1)
> and (2) are moot — real executions are happening on their own.
>
> The cold-tier GCS path now has real `cefi/` and `prediction/` data (`gcloud storage ls`) — no longer empty. This
> confirms item (3): the scheduler is genuinely firing.
>
> Matches an independent fix already on record in the infra-health-audit findings-fix doc (done 2026-08-07/08,
> re-verified live 2026-08-09 — root cause was a separate NDJSON-parsing bug, not just the missing image).
> `status: blocked` becomes `open` below since the original blocker is gone.
>
> Remaining scope is only item (4): re-run the paper-equals-batch-rerun determinism test now that the full three-tier
> pipeline actually executes end-to-end. Not run by this session — leaving the checkbox open on that one remaining
> sub-item rather than flipping on 3-of-4.

- [ ] [CODE] P2. **Finish the warm-GCS-parts durable sink — the compaction leg never landed (STALE, see banner above).**
      Verified live 2026-07-29: the warm tier is real and receiving data (Terraform-applied
      `deployment-service@c540cd03` 2026-06-29 — 52 `warm-sink-persist-*` Cloud Storage subscriptions, confirmed live
      via `gcloud pubsub subscriptions list`. The warm-tier path
      `gs://central-element-323112-events/live-events/warm/prediction/{book_snapshot_5,trades}/` confirms real data
      landing. But the daily cold-compaction Cloud Run Job (`live-event-log-compactor`,
      `deployment-service/deployment_service/jobs/live_event_log_compactor.py` +
      `deployment-service/terraform/gcp/live_event_log/compaction_job.tf`) has been non-functional since its creation
      (2026-06-29): its image `gcr.io/central-element-323112/live-event-log-compactor:latest` was never built/pushed (no
      `cloudbuild.yaml` step references it), so the Job sits `Ready: False` / `ContainerMissing` with ZERO executions
      ever (`gcloud run jobs describe` + `executions list`, confirmed 2026-07-29), and `live-events/cold/` is empty in
      GCS.

## Progress Log

- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — swapped in the actual active successor plan
  (`live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md`, which now carries the remaining compaction-job
  build work) and the better-matching codex SSOT (`/codex/02-data/live-data-persistence-and-event-log.md`) in place of
  the now-superseded vintage-audit-findings pointer and a less-specific pipeline-mode codex doc.

- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.
