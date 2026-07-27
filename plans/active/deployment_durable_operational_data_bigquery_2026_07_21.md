---
doc_type: plan
title: durable operational data — BigQuery via the event spine (VM resource stats + run-ledger + idle-spend)
summary: >-
  Persist FOUR operational signals that are currently ephemeral, all into one BigQuery dataset via the existing UTL
  event spine, so they survive for long-run analysis. (1) VM resource stats — the 30s/1min CPU/RAM/disk samples the
  heartbeat daemon already takes but only keeps as a rolling ~10-sample window on the registry entry. (2) VM run-ledger
  — the daemon already emits DEPLOYMENT_COMPLETED/FAILED events; a BigQuery subscription on them becomes a
  never-expiring run history that outlives the 30-day archive TTL. (3) Idle/orphan spend — computed centrally by the
  orphan logic, so a small scheduled job snapshots the rollup totals + per-resource rows daily, plus reap-event rows on
  each reap/delete. (4) NEW 2026-07-27 — per-process category breakdown (worker-agent / orchestrator / CI /
  AO-dispatched plan-work) for genuinely multi-tenant hosts, motivated by the orchestrator VM's own resize decision
  needing real utilization evidence. PR-1 (the write-path blocker) is RESOLVED this session — dedicated topics + a
  registered flat schema for the BQ-bound signals, chosen after confirming there are ZERO real Pub/Sub consumers of the
  shared deployment-events topic today (verified by code search, not assumed), so migration cost is near-zero. The "no
  live UI chart" decision is REVERSED — embed rolling 1h/4h/24h/1wk views into the EXISTING deployment-ui Host Resources
  panel, not a new page.
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [deployment-service, deployment-api, unified-trading-library, deployment-ui, agent-orchestrator]
scope: [engineer]
tags: [observability, bigquery, event-spine, resource-metrics, run-history, idle-spend, process-categorization]
related:
  - /plans/active/deployment_ui_observability_ux_tracker_2026_07_17.md
  - /plans/archive/2026_07/deployment_ui_fleet_tab_consolidation_2026_07_21.md
  - /plans/active/github_actions_operator_gated_followups_2026_07_17.md
created: "2026-07-21"
last_updated: "2026-07-27"
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 9
estimate_calibrated_ai_days: 7.2
assigned_role: backend_engineer
drift_direction: advance-code
sequential: true
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  - "operator design session 2026-07-21 (WS-6 resolved — event-spine->BigQuery finalized; git-health history dropped)"
  - "operator session 2026-07-27 (VM-resize decision needed real utilization history; resolved PR-1; reversed the
    no-live-chart call; added process-category breakdown) -- corrected execution_scope: orchestrator-agent -> local-only
    (was inconsistent with assigned_vm: NA per plans/active/task_template.md)"
---

# durable operational data — BigQuery via the event spine

> **🟢 UNBLOCKED 2026-07-27 — PR-1 resolved, expanded to a 4th signal, UI decision reversed.** Held `draft` since
> 2026-07-21 pending an operator design decision that was supposed to be revisited 2026-07-22 and never was (5 days
> stale) until this session's VM-resize decision needed real utilization history and surfaced it again. See **## PR-1
> resolution** below for the decision + the FULL consumer-migration map (a real risk-check, not an assumption).
>
> **This realizes the tracker's WS-6** ("durable resource-metrics timeline"), now decided and expanded to FOUR signals
> (added: per-process category breakdown). Git-health snapshot history — a candidate raised in the 2026-07-21 discussion
> — stays **dropped** (operator: not necessary).

## PR-1 resolution (2026-07-27) — dedicated topics + flat schema, migration cost verified near-zero

**Decision: option (A), applied more thoroughly than originally scoped** — dedicated Pub/Sub topics + a registered flat
schema for every BQ-bound signal, not just the new resource-sample event. Operator ruling: "I don't care if schemas need
changes for things currently consuming them, as long as you map out what the consumption changes would need to look like
and fix those as part of the plan too — otherwise I just want the best, most robust solution."

**The consumer-migration map that ruling required — verified via full codebase search, not assumed:**

- **There are ZERO real Pub/Sub consumers of the `deployment-events` topic today.** No code anywhere pulls/subscribes to
  it and parses the message body. The GCS-backed deployment registry (source of truth for the live dashboard) is written
  DIRECTLY by `HeartbeatDaemon`/`DeploymentsRegistry` and reconciled by deployment-api's own GCS/API polling
  (`deployment_processor.py`, `event_processor.py`) — Pub/Sub is, and always was, fire-and-forget. `agent-orchestrator`
  has zero references to these event types.
- The one subscription that exists (`deployment-events-monitor`, pull, 7-day retention, provisioned by
  `deployment-service/scripts/setup-pubsub.sh`) is **orphaned** — `deployment_service/monitor.py` has no `pubsub` import
  at all; it reads GCS directly. `/codex/05-infrastructure/event-sink-chain.md`'s claim that `monitor.py` pulls this
  subscription is **stale/wrong** — flagged as its own fix below, not actioned as part of this plan's main scope. **Net:
  migration cost for the topic/schema redesign is effectively zero** — nothing real consumes the current shape.
- The only things that DO assert on today's envelope (and need a one-line update if the shape changes for the signals
  we're moving): `unified-trading-library/tests/unit/test_event_sink.py`,
  `unified-trading-library/tests/events/unit/test_event_logging.py` (+ its `events_interface` mirror). Deployment-api's
  `test_vm_events.py`/`test_vm_events_ws.py`/`test_deploy_events_sse.py`/`test_deploy_events_filter.py` assert on a
  DIFFERENT sink (`GcsEventSink`, different topic/vocabulary) — unaffected, do not touch.
- **Side finding, real and worth fixing in the same pass**: `DEPLOYMENT_EVENT_TYPES` is defined **three times**, drifted
  — legacy `events_interface/schemas.py` (4 members), canonical `events/event_types.py` (7 members; its own docstring
  says "import from here exclusively"), and a third independent copy in `unified-api-contracts/internal/events.py` +
  `internal/domain/events_service/lifecycle.py`. `DEPLOYMENT_ROLLED_BACK` and `DEPLOYMENT_ORPHANED` are defined in all
  three but **never emitted anywhere** (0 call sites).
- **Second side finding**: two independent, duplicated publisher implementations for the SAME topic — `heartbeat_cli.py`
  (via the real `HeartbeatDaemon`) and a standalone `deployment_heartbeat.py` script that reimplements its own sink init
  (topic resolved via a bare `os.environ.get`, not the typed `DeploymentConfig` field the daemon path uses) — real drift
  risk if only one gets updated.

**The design, concretely:**

1. Consolidate the 3-way `DEPLOYMENT_EVENT_TYPES` drift into ONE canonical source —
   `unified_trading_library/events/event_types.py` (per its own docstring). `events_interface/schemas.py` re-exports
   from it (deprecate the standalone copy); flag the UAC copy to its own owners as a follow-up (out of this plan's repo
   scope to fix directly).
2. Drop `DEPLOYMENT_ROLLED_BACK`/`DEPLOYMENT_ORPHANED` from active use, or note explicitly if something else plans to
   emit them — don't carry dead constants into the new design without a decision.
3. Keep the GENERIC nested-envelope `log_event()` path unchanged for everything that isn't BQ-bound (it has other uses
   elsewhere in the codebase this plan doesn't touch) — do NOT reshape it globally.
4. For the BQ-bound signals specifically (resource-sample, run-ledger's completion events), publish via a NEW, dedicated
   topic per signal with a FLAT payload matching the target BQ table's columns directly — bypass the generic envelope
   for just these, rather than forcing every consumer of the general event system through a schema change it doesn't
   need.
5. Fix both publisher call sites (`heartbeat_cli.py` AND `deployment_heartbeat.py`) together — this is exactly the drift
   PR-3 (below) already flagged; the audit above confirms it's a real, not hypothetical, risk.
6. Delete the orphaned `deployment-events-monitor` subscription (dead cost/attack-surface for no benefit) and correct
   the stale `event-sink-chain.md` codex claim — tracked as its own small todo, not blocking the main build.

- [x] ✅ **PR-1 RESOLVED 2026-07-27** — see decision + migration map above. Superseded the original "OPERATOR picks
      A/B/C" framing: (A) is the pick, applied to all BQ-bound signals, with the consumer-migration cost verified at
      effectively zero.
- [x] ✅ **PR-2 SUPERSEDED 2026-07-27** — moot once the 3-way constant drift (found above) is consolidated to ONE
      canonical source; add the new resource-sample constant there only, not to three re-export chains.
- [ ] [BACKEND] P0. **PR-3 (BLOCKING) — publish via the generic-daemon contract, not a hardcoded name.**
      `HeartbeatDaemon` is deliberately consumer-agnostic (takes event NAMES as constructor params; docstring: "callers
      pick their own event names, no consumer-specific imports"). Hardcoding a resource-sample event name inside the
      sampler violates that and fails review. Thread a new optional `resource_sample_event: str | None` (+ optional
      payload builder) through the constructor like the existing event-name params, emit only when set, and have BOTH
      `heartbeat_cli.py` AND `deployment_heartbeat.py` pass the name (the second publisher the 2026-07-27 audit found).
- [ ] [DATA] P1. **PR-4 — partition-expiration TTL + `require_partition_filter`.** The UTL `create_table` wrapper
      exposes no partition-expiration parameter and sets `require_partition_filter=True`. Either extend the wrapper to
      accept a default partition expiration, or set the TTL out-of-band (bq/terraform) and say so; and note every
      verify/DuckDB example query MUST carry a `DATE(ts)` partition filter or it errors.
- [x] ✅ **PR-5 SUPERSEDED 2026-07-27** — moot once PR-1 chose dedicated topics over shared-topic filtering; the
      resource-sample event stays its own event/topic rather than reusing `DEPLOYMENT_PROGRESS`, since the flat-schema
      requirement (typed BQ columns) is easier to keep clean on a purpose-built payload than by carving fields back out
      of the general lifecycle event.
- [ ] [BACKEND] P2. **PR-6 — run-ledger enrichment + idle-spend job home.** Run-ledger: the completion payload lacks
      wall-clock `started_at`/`completed_at` and `peak_*` resources (only instantaneous-at-completion) — name these as
      the fields to add. Idle-spend: pin the scheduled job INSIDE deployment-api (it calls `build_orphan_inventory` /
      `/api/fleet/orphans`, whose rollup fields
      `stopped_total`/`reapable_total`/`monthly_idle_usd`/`monthly_reapable_usd` are verified correct), insert via the
      UTL BQ client, write one `reap_events` row per successfully-deleted VM inside the reap loop, and SKIP writes on
      `dry_run`. Note `monthly_idle_usd` is a boot-disk-only estimate, not compute cost.
- [ ] [INFRA] P2. **PR-8 (NEW 2026-07-27) — delete the orphaned `deployment-events-monitor` subscription + fix the stale
      codex claim.** Confirmed dead (no consumer, `monitor.py` reads GCS directly, not Pub/Sub). Delete the
      subscription; correct `/codex/05-infrastructure/event-sink-chain.md`'s claim that `monitor.py` pulls it.
- [x] ✅ **PR-7 (strip line numbers) — satisfied by this rewrite**; every reference in this doc as of 2026-07-27 cites a
      symbol, not a line number.

## Decisions (operator, 2026-07-21; #2 REVERSED and #5 ADDED 2026-07-27)

Reached after a design discussion that compared three write paths (GCS-batched, event-spine→BigQuery, Ops-Agent):

1. **Store = BigQuery, via the existing UTL event spine.** Cost is
   ~$0 at fleet scale (~4 GB logical / 6 months for 100
   VMs at 1/min; storage ~$0.08/mo; query within the 1 TB/month
   free tier). BigQuery removes ALL the GCS-specific complexity (flush cadence, per-day-vs-per-VM files,
   immutability/rewrite, compaction, object-count) — the VM just publishes an event. Chosen over GCS+DuckDB (B) because
   the write path is simpler, not despite it.
2. **~~No live interactive timeline chart~~ REVERSED 2026-07-27 — build one, embedded in the EXISTING panel.** The
   2026-07-21 call ("nice-to-have, dropped") is superseded by an explicit operator ask this session: "deployment ui
   panel to view it as much as possible, embed into the relevant existing [surface]." Target: extend the EXISTING Host
   Resources widget (`deployment-api/deployment_api/routes/_vm_health.py` D.1-metrics path, `deployment-ui`'s current
   live-snapshot panel) with rolling 1h/4h/24h/1wk aggregate views + the cross-VM comparison (service × asset_group ×
   mode) — not a brand-new page. `bq extract`/DuckDB analysis (item 5 below) stays available too, as the
   power-user/ad-hoc path alongside the UI, not instead of it.
3. **FOUR signals, one dataset** — resource stats, run-ledger, idle-spend, process-category breakdown (below; 4th added
   2026-07-27).
4. **Git-health snapshot history — DROPPED** (not necessary).
5. **Analysis-via-download/DuckDB stays available** (downgraded from "the only path" to "the ad-hoc/power-user path,
   alongside the UI panel from #2").

## The FOUR signals + their write triggers

| Signal                                          | Trigger                                    | Mechanism                                                                                                 |
| ----------------------------------------------- | ------------------------------------------ | --------------------------------------------------------------------------------------------------------- |
| **VM resource stats**                           | VM-emitted, ~1/min                         | daemon publishes a resource-sample event → dedicated Pub/Sub topic → native BQ subscription (flat schema) |
| **VM run-ledger**                               | VM-emitted, once per run end               | dedicated topic for the completion payload → native BQ subscription (flat schema)                         |
| **Idle/orphan spend**                           | central, scheduled                         | daily job snapshots the orphan rollups + per-resource rows; reap-event rows on each reap/delete           |
| **Process-category breakdown** (NEW 2026-07-27) | genuinely multi-tenant hosts only, ~1/5min | per-process CPU/RSS rollup, categorized worker-agent / orchestrator / CI / AO-plan-work — see below       |

## 4th signal detail — process-category breakdown (NEW 2026-07-27)

**Why this is separate from the other three**: `resource_samples` above is per-VM, which is correct for almost every
fleet VM (each runs ONE workload type). The orchestrator VM (`i-0c9b283b31d6b5ca7`) is the one genuine exception — it's
multi-tenant (the AO server process itself, N interactive slot-worker `claude` sessions, self-hosted CI glue-runner
jobs, and AO-dispatched autonomous plan-execution workers all share the same 8 cores). A single `cpu_pct` number for
that VM can't answer "is it the agents, the orchestrator, or CI eating the CPU" — exactly the question this session's
VM-resize decision needed and couldn't answer from the per-VM number alone.

**Bridge already running (2026-07-27)**: a lightweight cron (`*/5 * * * *`) is live on `i-0c9b283b31d6b5ca7` today —
`agent-orchestrator/scripts/orchestrator/resource-monitor.sh` (committed 2026-07-27; deployed copy at
`/opt/resource-monitor/resource-monitor.sh` on the VM — keep the two in sync, edit the git copy and redeploy, never the
reverse), appending JSON lines to `/var/log/resource-monitor/resource-monitor.jsonl` (30-day rolling window,
self-trimming). Each line: load average, `/proc/stat` CPU jiffies (deltas computed at read time, not in the logger, to
keep it cheap), memory/swap from `/proc/meminfo`, and the top 8 processes by `%CPU` with PID/command/elapsed. This is a
STOPGAP, not the design — retire it once the real pipeline below ships, but its schema is the reference for what fields
matter.

**Categorization heuristic (first pass, refine once real data is queried)**: `comm == "claude"` → worker-agent (but
split further by parent-process/ancestry once we can tell an INTERACTIVE session from an AO-dispatched autonomous one —
both currently show as `claude`); `comm` matching the orchestrator's own server entrypoint → orchestrator;
`Runner.Listener`/`Runner.Worker` → CI; anything else on the box → other/unclassified (don't force a category onto
something that doesn't fit — an honest "unclassified" bucket beats a wrong guess).

- [ ] [DATA] P1. **Process-category schema + table** — `process_samples` (vm_name, ts, category
      [worker_agent|orchestrator|ci|ao_plan_work|other], pid, comm, cpu_pct, mem_pct, mem_rss_kb, elapsed_sec). Only
      collected on hosts flagged multi-tenant (a small allowlist — start with just the orchestrator VM; do not build a
      per-VM opt-in UI for this, a config list is enough).
- [ ] [BACKEND] P1. **Refine the categorization heuristic against real ancestry** — distinguish an interactive
      operator-driven `claude` session from an AO-dispatched autonomous one (likely via parent-PID chain to the
      orchestrator's own dispatcher, or an env var the dispatcher already sets on spawned workers — check
      `agent-orchestrator/server/autospawn.py` / `dispatch.py` for what's already available before inventing a new
      marker). Land this BEFORE the "worker-agent vs plan-work" split is treated as reliable in the UI.
- [ ] [INFRA] P1. **Replace the bridge cron with the real pipeline** — same trigger/mechanism family as the other three
      signals (publish → dedicated topic → BQ subscription, ~1/5min not ~1/min given this is diagnostic not
      billing-grade); once verified landing correctly, delete `/opt/resource-monitor/` + its cron entry from
      `i-0c9b283b31d6b5ca7`.
- [ ] [UI] P1. **Process-category breakdown view** — part of the same VM drill-down/comparison work as the other
      signals, scoped to multi-tenant hosts only (don't show an empty breakdown chart on single-tenant VMs where it's
      meaningless).

## Context — grounded facts (verified 2026-07-21; expanded 2026-07-27)

- **Event spine exists** — `unified-trading-library/unified_trading_library/streaming/event_facade.py`,
  `events_interface/` with `DEPLOYMENT_STARTED/COMPLETED/FAILED/ROLLED_BACK` (`events_interface/schemas.py`,
  `events_interface/__init__.py`). CLAUDE.md's "live = batch event-log spine" endorses this path
  (`/codex/02-data/live-data-persistence-and-event-log.md`). **Canonical source is actually
  `unified_trading_library/events/event_types.py`** (2026-07-27 finding — 7 members incl. `DEPLOYMENT_PROGRESS`/
  `DEPLOYMENT_ORPHANED`/`DEPLOYMENT_DIGEST`, not the 4-member legacy copy this doc originally cited) — see PR-1
  resolution's constant-drift finding above.
- **Sampling already happens** — `unified_trading_library/lifecycle/daemon.py::HeartbeatDaemon` samples host metrics
  into `host_metrics_window` (`HOST_METRICS_WINDOW_KEY`, last ~10 samples) on the registry entry → Firestore. **The
  sampling is there; only the rolling window survives.** This plan ADDS publishing each sample as an event; it does NOT
  remove the Firestore rolling window (that stays the live column).
- **Envelope confirmed exactly, 2026-07-27**: `events/__init__.py::log_event()` builds
  `metadata = {timestamp, service_name, severity, details, ...}`; `event_sink.py::PubSubEventSink.write_event` wraps it
  `{"event": name, "service": ..., "metadata": metadata}` and calls `client.publish(topic, data)` — **positional only,
  no `attributes=`**, though the underlying GCP client already supports them. This is the exact shape PR-1 found
  couldn't yield typed BQ columns natively.
- **`InMemoryTransport`/`EventTransport` (streaming/event_facade.py) is a DIFFERENT, unrelated system** — it operates on
  `CanonicalPersistEnvelope` for MTDS/MDPS/features live=batch market-data persistence, not `DEPLOYMENT_*` lifecycle
  events. No cross-transport consistency concern for this plan.
- **No resource-sample event type yet** — the one genuinely new schema (grep-confirmed absent).
- **Run history is currently lost at 30 days** — `deployments/archive/` has a live-confirmed 30-day GCS lifecycle
  (oldest prefix exactly 30 days back). The run-ledger fixes this: a durable BQ table from the completion events the
  daemon already emits.
- **BQ dataset/client access via the UTL cloud interface** (`cloud_interface/providers/gcp.py::_bq_client()` +
  create-dataset) — use it, never raw `google.cloud`/`boto3` (QG-enforced).
- **No local buffer to lose** — publishing per-minute means Pub/Sub owns delivery; preemption loses at most the
  in-flight sample. The GCS flush/SIGTERM/file-layout machinery is unnecessary here.
- **Existing UI surface to extend** — `deployment-api/deployment_api/routes/_vm_health.py` (D.1 metrics classifiers,
  epic `observability_master`) backs the current live-snapshot Host Resources panel in `deployment-ui`. The rolling
  1h/4h/24h/1wk view (Decision #2 reversal) extends THIS surface, not a new one.

## Todos

- [ ] [DATA] P0. **BigQuery dataset + tables** — create the dataset and three tables via the UTL cloud interface (NOT
      raw `google.cloud`): `resource_samples` (vm_name, service, asset_group, mode, deployment_id, ts, cpu_pct, mem_pct,
      mem_slope, disk_pct, io_write_rate_bytes_sec, net_recv_rate_bytes_sec, workload_alive), `run_ledger`,
      `idle_spend` + `reap_events`. Partition each by `DATE(ts)`, cluster by `vm_name`/`service`. Set
      partition-expiration TTL per decision below.
- [ ] [BACKEND] P0. **Resource-sample event type** — add it to the CANONICAL
      `unified_trading_library/events/event_types.py` ONLY (per PR-1/PR-2 resolution — the 3-way constant drift found
      2026-07-27 means this is the one true source now; do not also add to `events_interface/schemas.py`, that file
      re-exports from the canonical one instead).
- [ ] [INFRA] P0. **Dedicated Pub/Sub topic + registered flat schema for resource-sample events** (PR-1 decision) — a
      NEW topic (not the shared `deployment-events`), payload flat (no nested `metadata.details` envelope), matching
      `resource_samples`' columns directly.
- [ ] [BACKEND] P0. **Publish the sample from the daemon, via BOTH publisher call sites** — `lifecycle/daemon.py` (real
      path, `heartbeat_cli.py`'s caller) AND `deployment_service/scripts/vm/deployment_heartbeat.py` (the standalone
      duplicate the 2026-07-27 audit found) publish each host-metrics sample to the NEW dedicated topic (~1/min)
      ALONGSIDE the existing `host_metrics_window` Firestore write. Best-effort — MUST NOT block or fail the
      authoritative heartbeat/registry write (same contract as the dual-write mirror). Keep the rolling window (it's the
      live column).
- [ ] [INFRA] P0. **Native BigQuery subscription** on the new dedicated topic → `resource_samples` (typed columns work
      now, since the topic carries a flat schema — this is what PR-1 was blocked on). TTL via partition expiry. Infra
      via gcloud/terraform in the deployment infra home.
- [ ] [INFRA] P2. **Delete the orphaned `deployment-events-monitor` pull subscription** (PR-8) + fix the stale
      `event-sink-chain.md` codex claim that `monitor.py` consumes it (it reads GCS directly, confirmed no `pubsub`
      import).
- [ ] [REVIEW] P1. **Verify resource stats on a real VM** — launch a short VM, confirm samples land in
      `resource_samples` queryable by vm+time, and the Firestore live Resources column is unaffected. Cite the query.
- [ ] [BACKEND] P1. **Run-ledger fields** — confirm `DEPLOYMENT_COMPLETED`/`FAILED` carry the run-summary the ledger
      needs (name, service, asset_group, mode, started_at, completed_at, outcome, rows_out/rows_error, peak resources,
      cost if available); enrich the event payload where missing.
- [ ] [INFRA] P1. **Dedicated topic + native BigQuery subscription for `run_ledger`** (long/never-expiring — it is the
      historic backbone). Per the PR-1 decision, `DEPLOYMENT_COMPLETED`/`FAILED` also need a flat-schema path off the
      shared `deployment-events` topic (same nested-envelope problem) — either publish a second, flat "run-summary"
      event on completion alongside the existing lifecycle event (existing consumers, if any resurface, are unaffected
      since the original event still fires unchanged), or register a schema AND have the daemon emit these two specific
      event types with a flat payload. This is the durable answer to run history past the 30-day archive TTL, and it
      powers the WS-2 date-range filter beyond 30 days.
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
- [ ] [BACKEND] P1. **Rolling-window aggregate query API** (NEW 2026-07-27, reverses the "no UI chart" decision) — a
      deployment-api endpoint alongside the existing `_vm_health.py` D.1-metrics path, serving 1h/4h/24h/1wk
      avg/min/max/p95 for `cpu_pct`/`mem_pct`/`disk_pct` per VM from `resource_samples`, plus the process-category
      breakdown from `process_samples` where available (multi-tenant hosts only).
- [ ] [UI] P1. **Extend the EXISTING Host Resources panel** in `deployment-ui` with the rolling-window view (a
      window-size selector: 1h/4h/24h/1wk) — embed into the current live-snapshot widget rather than a new page, per the
      reversed Decision #2. `pw:L2 ✓` + cited regression spec.
- [ ] [UI] P1. **Cross-VM comparison page** — overlay N VMs filtered by service × asset_group × mode (the right-sizing
      workflow the operator originally asked for 2026-07-17: "ten different VMs running instruments-service — what were
      their resources?"). `pw:L2 ✓` + cited regression spec.
- [ ] [REVIEW] P2. **Analysis path doc (UI is now primary, DuckDB stays as the power-user path)** — document the
      rolling-window UI as the primary surface; `bq extract`/download + local DuckDB remains available for ad-hoc
      queries beyond what the UI's fixed windows cover. Provide example queries: per-VM run timeline, cross-VM
      comparison, idle-spend trend, run-history date-range, process-category breakdown.
- [ ] [INFRA] P1. Ship (`quickmerge.sh "msg" --agent --files '<paths>'` across the repos) + flip todos same turn
      (`docs(plans):`).
- [ ] [REVIEW] P2. Post-phase codex audit — document the durable-operational-data contract (event-spine→BigQuery, the
      three tables + schemas, retention, Firestore-stays-live, analysis-via-DuckDB) in
      `/codex/05-infrastructure/deployment-observability.md`; cross-ref
      `/codex/02-data/live-data-persistence-and-event-log.md`.

## Success criteria

- All FOUR signals land in BigQuery and are queryable together: per-VM resource timeline, run history (incl. >30 days
  old), idle-spend trend + reclaimed-over-time, and process-category breakdown on multi-tenant hosts.
- The cross-VM comparison the operator wanted (N VMs by service × asset_group × mode) is a single query AND a UI page.
- The rolling 1h/4h/24h/1wk view is embedded in the EXISTING Host Resources panel (not a new page); the Firestore
  live/current Resources column is unchanged.
- Cost stays ~$0 (storage ~$0.08/mo; queries within the free tier); no GCS file-management machinery introduced.
- Run history survives past the 30-day archive TTL via the durable `run_ledger`.
- The bridge cron on the orchestrator VM is retired once `process_samples` verifiably lands the same data via the real
  pipeline.
- Post-scale verification (from the VM-resize decision this session motivated): once the orchestrator VM is resized, the
  rolling-window view shows utilization settling in a healthy range (roughly 50-70% average with burst headroom) — not
  pinned near 90%+ (under-provisioned) and not sitting at 30-40% (over-provisioned, money left on the table).

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
- **2026-07-27** — Unblocked after sitting `draft`/HELD 5 days past its own "revisit 2026-07-22" note. Triggered by an
  unrelated-seeming session: the orchestrator VM's resize decision
  (github_actions_operator_gated_followups_2026_07_17.md Phase 7) needed real utilization history, not a point-in-time
  snapshot — which is exactly what this plan was built to provide and had been sitting on. Installed a stopgap
  cron-based monitor on `i-0c9b283b31d6b5ca7` in the meantime (`/opt/resource-monitor/`, 5-min cadence, 30-day rolling
  JSONL) — this becomes the reference schema for the new 4th signal (process-category breakdown) and is retired once the
  real pipeline ships.
  - **PR-1 resolved**: dedicated topics + flat schema (option A), applied to ALL BQ-bound signals not just the new one.
    Operator ruling: don't optimize for minimal consumer disruption, map out and fix whatever changes, want the most
    robust design. Two research agents mapped the full publisher/consumer landscape — the key finding that made this
    easy: **zero real Pub/Sub consumers of `deployment-events` exist today** (the dashboard is populated by direct GCS
    writes/polling, not by consuming these events; the one existing subscription is orphaned/dead). Migration cost is
    near-zero. Also surfaced and fixed in the same pass: a 3-way drift in `DEPLOYMENT_EVENT_TYPES` definitions
    (legacy/canonical/UAC copies), two never-emitted event constants, and two independently-duplicated publisher call
    sites that both need updating together.
  - **Decision #2 reversed**: "no live chart" (2026-07-21) superseded by an explicit operator ask this session to embed
    a rolling-window view into the existing Host Resources panel. DuckDB/download analysis stays available as the ad-hoc
    path, not the only path.
  - **4th signal added**: process-category breakdown (worker-agent/orchestrator/CI/AO-plan-work), scoped to genuinely
    multi-tenant hosts (the orchestrator VM specifically) since per-VM resource stats can't answer "which process
    category is actually consuming this" on a shared box — exactly the question the VM-resize decision needed answered
    and the per-VM-only design couldn't.

## Codex SSOTs

- `/codex/02-data/live-data-persistence-and-event-log.md` — the UTL event spine (EventTransport facade / Pub/Sub) this
  plan rides.
- `/codex/05-infrastructure/deployment-observability.md` — deployment inventory + (to add) the durable-operational-data
  contract (three BQ tables, retention, Firestore-live/BQ-history split).
- `/codex/06-coding-standards/quality-gates.md` — no raw `google.cloud`/`boto3`; BQ access via the UTL cloud interface.
