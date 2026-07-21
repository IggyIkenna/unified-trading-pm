---
doc_type: plan
title: durable operational data — BigQuery via the event spine (VM resource stats + run-ledger + idle-spend)
summary: >-
  Persist three operational signals that are currently ephemeral, all into one BigQuery dataset via the existing UTL
  event spine, so they survive for long-run analysis. (1) VM resource stats — the 30s/1min CPU/RAM/disk samples the
  heartbeat daemon already takes but only keeps as a rolling ~10-sample window on the registry entry; publish each as an
  event to a native BigQuery subscription. (2) VM run-ledger — the daemon already emits DEPLOYMENT_COMPLETED/FAILED
  events; a BigQuery subscription on them becomes a never-expiring run history that outlives the 30-day archive TTL. (3)
  Idle/orphan spend — computed centrally by the orphan logic, so a small scheduled job snapshots the rollup totals +
  per-resource rows daily, plus reap-event rows on each reap/delete. The live/current UI column stays on Firestore
  (unchanged); there is NO live interactive timeline chart (operator decision) — analysis is download + local DuckDB.
status: draft
nature: process
asset_group: [meta]
stage: [meta]
repos: [deployment-service, deployment-api, unified-trading-library]
scope: [engineer]
tags: [observability, bigquery, event-spine, resource-metrics, run-history, idle-spend]
related:
  - deployment_ui_observability_ux_tracker_2026_07_17.md
  - deployment_ui_fleet_tab_consolidation_2026_07_21.md
created: "2026-07-21"
last_updated: "2026-07-21"
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 4.8
assigned_role: backend_engineer
drift_direction: advance-code
sequential: true
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source: operator design session 2026-07-21 (WS-6 resolved — event-spine→BigQuery finalized; git-health history dropped)
---

# durable operational data — BigQuery via the event spine

> **🔴 HELD `draft` — BLOCKED on an operator design decision (2026-07-21).** A pre-activation review (verified against
> live code) found the plan's central write-path premise does not hold against the real event wire format — see **##
> Pre-activation review** below. Operator will revisit **2026-07-22**. Do NOT activate until finding **PR-1** is
> resolved. Authored in the tabs-3 worktree (new work off the root repo where other agents are active).
>
> **This realizes the tracker's WS-6** ("durable resource-metrics timeline"), now decided and expanded to three signals.
> Git-health snapshot history — a candidate raised in the same discussion — was **dropped** (operator: not necessary).

## Pre-activation review (2026-07-21) — MUST resolve before activation

A read-only pre-activation review (verified against live code) found the write-path premise partly wrong. The fixes
below block dispatch; each references symbols, not line numbers (grep to locate).

- [ ] [BACKEND] P0. **PR-1 (BLOCKING — operator design decision) — "native BQ subscription → typed tables, no
      consolidator" is not achievable as written.** All deployment events publish to ONE shared topic
      (`deployment-events`, configured in deployment-service's `deployment_config.py`; sink wired in
      `heartbeat_cli.py`), and `PubSubEventSink.write_event` (in UTL `event_sink.py`) publishes with NO message
      attributes — so a subscription filter cannot separate one signal from another; two native subscriptions on that
      topic each receive EVERY event type. The body is also a doubly-nested envelope
      (`{event, service, metadata:{…, details:{…real fields…}}}`) and no topic schema is registered, so a native
      subscription can only land raw JSON in a single `data` column — it cannot populate the typed
      `resource_samples`/`run_ledger` columns. The "no sink change + native subscription + typed tables" trio cannot all
      hold. OPERATOR picks one: (A) dedicated topic per signal + registered flat topic schema; (B) add message
      attributes (`event=<name>`) in `PubSubEventSink` + subscription filters (still needs a flat schema for typed
      columns); or (C) accept a raw-JSON `data` column + query-time extraction (contradicts the typed-schema todos). The
      `[DATA] P0` + `[INFRA] P0/P1` todos are mutually inconsistent until this is chosen.
- [ ] [BACKEND] P0. **PR-2 (BLOCKING) — resource-sample event constant needs the FULL re-export chain.** The daemon
      caller (`heartbeat_cli.py`) imports the DEPLOYMENT_* constants from the top-level `unified_trading_library`
      package, not from `events_interface`. Adding the new constant only to `events_interface/schemas.py` will
      `ImportError` at the caller. Add it to `events_interface/schemas.py` AND `events_interface/__init__.py` AND the
      top-level `unified_trading_library/__init__.py` (both the import and `__all__`).
- [ ] [BACKEND] P0. **PR-3 (BLOCKING) — publish via the generic-daemon contract, not a hardcoded name.**
      `HeartbeatDaemon` is deliberately consumer-agnostic (takes event NAMES as constructor params; docstring: "callers
      pick their own event names, no consumer-specific imports"). Hardcoding a resource-sample event name inside the
      sampler violates that and fails review. Thread a new optional `resource_sample_event: str | None` (+ optional
      payload builder) through the constructor like the existing event-name params, emit only when set, and have
      `heartbeat_cli.py` pass the name.
- [ ] [DATA] P1. **PR-4 — partition-expiration TTL + `require_partition_filter`.** The UTL `create_table` wrapper
      exposes no partition-expiration parameter and sets `require_partition_filter=True`. Either extend the wrapper to
      accept a default partition expiration, or set the TTL out-of-band (bq/terraform) and say so; and note every
      verify/DuckDB example query MUST carry a `DATE(ts)` partition filter or it errors.
- [ ] [BACKEND] P2. **PR-5 — simplify: the resource data is ALREADY on the topic.** The existing `DEPLOYMENT_PROGRESS`
      event (emitted ~1/min) already carries every field listed for `resource_samples` (via the daemon's VM payload). A
      filtered subscription on `DEPLOYMENT_PROGRESS` captures resource samples with NO new event schema or publish path
      — which (with PR-1's decision) may collapse the two resource `[BACKEND] P0` todos. Operator weighs this vs a
      dedicated event.
- [ ] [BACKEND] P2. **PR-6 — run-ledger enrichment + idle-spend job home.** Run-ledger: the completion payload lacks
      wall-clock `started_at`/`completed_at` and `peak_*` resources (only instantaneous-at-completion) — name these as
      the fields to add. Idle-spend: pin the scheduled job INSIDE deployment-api (it calls `build_orphan_inventory` /
      `/api/fleet/orphans`, whose rollup fields
      `stopped_total`/`reapable_total`/`monthly_idle_usd`/`monthly_reapable_usd` are verified correct), insert via the
      UTL BQ client, write one `reap_events` row per successfully-deleted VM inside the reap loop, and SKIP writes on
      `dry_run`. Note `monthly_idle_usd` is a boot-disk-only estimate, not compute cost.
- [ ] [DATA] P3. **PR-7 — strip line numbers → symbol refs throughout this plan** (same rule the operator applied to
      WS-5B + Fleet on 2026-07-21): the Context/Todos below still cite `file:line`; replace each with a grep-able
      symbol/function name.

## Decisions (operator, 2026-07-21)

Reached after a design discussion that compared three write paths (GCS-batched, event-spine→BigQuery, Ops-Agent):

1. **Store = BigQuery, via the existing UTL event spine.** Cost is
   ~$0 at fleet scale (~4 GB logical / 6 months for
   100 VMs at 1/min; storage ~$0.08/mo; query within the 1 TB/month
   free tier). BigQuery removes ALL the GCS-specific complexity (flush cadence, per-day-vs-per-VM files,
   immutability/rewrite, compaction, object-count) — the VM just publishes an event. Chosen over GCS+DuckDB (B) because
   the write path is simpler, not despite it.
2. **No live interactive timeline chart** (operator: "we don't need it, it's a nice-to-have"). Analysis = download the
   slice + local DuckDB. The live/current Resources column stays on Firestore, unchanged.
3. **Three signals, one dataset** — resource stats, run-ledger, idle-spend (below).
4. **Git-health snapshot history — DROPPED** (not necessary).

## The three signals + their write triggers

| Signal                | Trigger                      | Mechanism                                                                                       |
| --------------------- | ---------------------------- | ----------------------------------------------------------------------------------------------- |
| **VM resource stats** | VM-emitted, ~1/min           | daemon publishes a resource-sample event → Pub/Sub → native BQ subscription                     |
| **VM run-ledger**     | VM-emitted, once per run end | BQ subscription on the EXISTING `DEPLOYMENT_COMPLETED`/`FAILED` events                          |
| **Idle/orphan spend** | central, scheduled           | daily job snapshots the orphan rollups + per-resource rows; reap-event rows on each reap/delete |

## Context — grounded facts (verified 2026-07-21)

- **Event spine exists** — `unified-trading-library/unified_trading_library/streaming/event_facade.py`,
  `events_interface/` with `DEPLOYMENT_STARTED/COMPLETED/FAILED/ROLLED_BACK` (`events_interface/schemas.py:477`,
  `events_interface/__init__.py:79-83`). CLAUDE.md's "live = batch event-log spine" endorses this path
  (`codex/02-data/live-data-persistence-and-event-log.md`).
- **Sampling already happens** — `unified_trading_library/lifecycle/daemon.py:229-258` samples host metrics into
  `host_metrics_window` (`HOST_METRICS_WINDOW_KEY`, last ~10 samples) on the registry entry → Firestore. **The sampling
  is there; only the rolling window survives.** This plan ADDS publishing each sample as an event; it does NOT remove
  the Firestore rolling window (that stays the live column).
- **No resource-sample event type yet** — the one genuinely new schema (grep-confirmed absent).
- **Run history is currently lost at 30 days** — `deployments/archive/` has a live-confirmed 30-day GCS lifecycle
  (oldest prefix exactly 30 days back). The run-ledger fixes this: a durable BQ table from the completion events the
  daemon already emits.
- **BQ dataset/client access via the UTL cloud interface** (`cloud_interface/providers/gcp.py` `_bq_client()` +
  create-dataset) — use it, never raw `google.cloud`/`boto3` (QG-enforced).
- **No local buffer to lose** — publishing per-minute means Pub/Sub owns delivery; preemption loses at most the
  in-flight sample. The GCS flush/SIGTERM/file-layout machinery is unnecessary here.

## Todos

- [ ] [DATA] P0. **BigQuery dataset + tables** — create the dataset and three tables via the UTL cloud interface (NOT
      raw `google.cloud`): `resource_samples` (vm_name, service, asset_group, mode, deployment_id, ts, cpu_pct, mem_pct,
      mem_slope, disk_pct, io_write_rate_bytes_sec, net_recv_rate_bytes_sec, workload_alive), `run_ledger`,
      `idle_spend` + `reap_events`. Partition each by `DATE(ts)`, cluster by `vm_name`/`service`. Set
      partition-expiration TTL per decision below.
- [ ] [BACKEND] P0. **Resource-sample event type** — add it to `unified_trading_library/events_interface/schemas.py`
      with the fields above. It is the only new event schema.
- [ ] [BACKEND] P0. **Publish the sample from the daemon** — in `lifecycle/daemon.py`, publish each host-metrics sample
      to the event bus (~1/min) ALONGSIDE the existing `host_metrics_window` Firestore write. Best-effort — MUST NOT
      block or fail the authoritative heartbeat/registry write (same contract as the dual-write mirror). Keep the
      rolling window (it's the live column).
- [ ] [INFRA] P0. **Pub/Sub → BigQuery subscription** for the resource-sample events → `resource_samples` (native BQ
      subscription, no consolidator to own; TTL via partition expiry). Infra via gcloud/terraform in the deployment
      infra home.
- [ ] [REVIEW] P1. **Verify resource stats on a real VM** — launch a short VM, confirm samples land in
      `resource_samples` queryable by vm+time, and the Firestore live Resources column is unaffected. Cite the query.
- [ ] [BACKEND] P1. **Run-ledger fields** — confirm `DEPLOYMENT_COMPLETED`/`FAILED` carry the run-summary the ledger
      needs (name, service, asset_group, mode, started_at, completed_at, outcome, rows_out/rows_error, peak resources,
      cost if available); enrich the event payload where missing.
- [ ] [INFRA] P1. **BigQuery subscription on the deployment lifecycle events → `run_ledger`** (long/never-expiring — it
      is the historic backbone). This is the durable answer to run history past the 30-day archive TTL, and it powers
      the WS-2 date-range filter beyond 30 days.
- [ ] [REVIEW] P1. **Verify run-ledger** — a completed VM produces a `run_ledger` row; a "what ran between A and B"
      query returns runs older than 30 days. Cite the query.
- [ ] [BACKEND] P1. **Idle-spend scheduled snapshot** — a daily scheduled job (Cloud Scheduler → Cloud Run, or a
      scheduled deployment task) runs the orphan computation (the `/api/fleet/orphans` logic) and writes the 4 rollup
      totals (stopped_total, reapable_total, monthly_idle_usd, monthly_reapable_usd) + per-resource idle rows to
      `idle_spend`. Reuse the existing list-rate estimate — no new cost model.
- [ ] [BACKEND] P1. **Reap-event logging** — when a reap/delete occurs (the existing `/api/fleet/reap` +
      `DELETE /api/fleet/instances/{name}` endpoints, also surfaced by the Fleet-consolidation plan), write a
      `reap_events` row (vm, age-at-reap, reclaimed $/mo, actor, ts). Hook the endpoints directly — no dependency on the
      UI plan.
- [ ] [REVIEW] P1. **Verify idle-spend** — the daily snapshot lands; a reap writes a `reap_events` row; the idle-spend
      trend and reclaimed-over-time are queryable. Cite the queries.
- [ ] [DATA] P1. **Retention / TTL** — set partition-expiration per table (proposed defaults, operator may adjust):
      `resource_samples` 12 months, `run_ledger` indefinite (historic backbone), `idle_spend`/`reap_events` indefinite.
      Document on the tables.
- [ ] [REVIEW] P2. **Analysis path doc (no UI chart)** — document that there is deliberately no live timeline chart;
      analysis is `bq extract` / download + local DuckDB. Provide example queries: per-VM run timeline, cross-VM
      comparison (service × asset_group × mode — the right-sizing workflow), idle-spend trend, run-history date-range.
- [ ] [INFRA] P1. Ship (`quickmerge.sh "msg" --agent --files '<paths>'` across the repos) + flip todos same turn
      (`docs(plans):`).
- [ ] [REVIEW] P2. Post-phase codex audit — document the durable-operational-data contract (event-spine→BigQuery, the
      three tables + schemas, retention, Firestore-stays-live, analysis-via-DuckDB) in
      `codex/05-infrastructure/deployment-observability.md`; cross-ref
      `codex/02-data/live-data-persistence-and-event-log.md`.

## Success criteria

- All three signals land in BigQuery and are queryable together: per-VM resource timeline, run history (incl. >30 days
  old), and idle-spend trend + reclaimed-over-time.
- The cross-VM comparison the operator wanted (N VMs by service × asset_group × mode) is a single query.
- The Firestore live/current Resources column is unchanged; no live timeline chart is built.
- Cost stays ~$0 (storage ~$0.08/mo; queries within the free tier); no GCS file-management machinery introduced.
- Run history survives past the 30-day archive TTL via the durable `run_ledger`.

## Progress Log

- **2026-07-21** — Authored after the operator finalized the write side. Design discussion compared GCS-batched vs
  event-spine→BigQuery vs Ops-Agent; operator chose **BigQuery via the event spine** on the basis that its write path is
  simpler (the VM just publishes an event — no flush cadence, file layout, immutability, compaction, or object-count
  management, all of which are GCS-only problems) and cost is ~$0 either way. **No live interactive timeline chart**
  (nice-to-have, dropped) — analysis via download + local DuckDB. Expanded from resource stats alone to three signals
  (resource stats, run-ledger, idle-spend), all → one BQ dataset. Git-health snapshot history dropped. Grounded the plan
  against code: event spine + `DEPLOYMENT_COMPLETED` events + daemon host-metrics sampling all exist; the only new
  schema is a resource-sample event; run history is live-confirmed lost at the 30-day archive TTL, which the run-ledger
  fixes.

## Codex SSOTs

- `codex/02-data/live-data-persistence-and-event-log.md` — the UTL event spine (EventTransport facade / Pub/Sub) this
  plan rides.
- `codex/05-infrastructure/deployment-observability.md` — deployment inventory + (to add) the durable-operational-data
  contract (three BQ tables, retention, Firestore-live/BQ-history split).
- `codex/06-coding-standards/quality-gates.md` — no raw `google.cloud`/`boto3`; BQ access via the UTL cloud interface.
