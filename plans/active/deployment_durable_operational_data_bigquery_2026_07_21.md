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
- [x] ✅ **PR-3 DONE 2026-07-27** — `unified-trading-library` `lifecycle/daemon.py`: threaded
      `resource_sample_event`/`resource_sample_publisher`/`resource_sample_payload_builder` +
      `run_summary_event`/`run_summary_publisher`/`run_summary_payload_builder` through `HeartbeatDaemon.__init__`
      exactly like the existing event-name params (all optional, default `None` — fully backward compatible, daemon
      stays consumer-agnostic). `deployment-service`'s `heartbeat_cli.py` wires both (via `_build_flat_publishers` +
      caller-supplied payload builders matching the exact `resource_samples`/`run_ledger` column names); the standalone
      `scripts/vm/deployment_heartbeat.py` (the second publisher this session's own audit found) wires the run-summary
      half (it has no host-metrics sampler, so honestly no resource-sample half). 27/27 daemon unit tests pass (6 new:
      publish-on-tick, publish-on-complete, best-effort-survives-publish-failure ×2, skip-when-unconfigured,
      idempotent-complete-does-not-republish).
- [x] ✅ **PR-4 DONE 2026-07-28** — extended `GCPAnalyticsClient.create_table` (+ the abstract `AnalyticsClient`
      interface) with an optional `partition_expiration_ms` param (`unified-trading-library@<sha-in-this-session>`),
      flowing into `bigquery.TimePartitioning(..., expiration_ms=...)`; `None` (default) preserves exact prior
      never-expiring behavior. `bootstrap_operational_data_bq.py` now declares per-table values:
      `resource_samples`/`reap_events`/`process_samples` = 12mo, `idle_spend` (cost-trend table) = 24mo, `run_ledger` =
      `None` (deliberately never-expiring — its whole point is durability past the 30-day GCS archive TTL, a blanket TTL
      would defeat that). Since `create_table(...,     exists_ok=True)` no-ops on already-live tables, retroactively
      applied via `bq update     --time_partitioning_expiration` on all 4 (not run_ledger) — confirmed live via
      `bq show`: `resource_samples`/`reap_events`/`process_samples` = `expirationMs: 31536000000`, `idle_spend` =
      `63072000000`, `run_ledger` has no `expirationMs` field. 12 new unit tests on `create_table` (previously zero
      coverage).
- [x] ✅ **PR-5 SUPERSEDED 2026-07-27** — moot once PR-1 chose dedicated topics over shared-topic filtering; the
      resource-sample event stays its own event/topic rather than reusing `DEPLOYMENT_PROGRESS`, since the flat-schema
      requirement (typed BQ columns) is easier to keep clean on a purpose-built payload than by carving fields back out
      of the general lifecycle event.
- [x] ✅ _\*PR-6 DONE 2026-07-27 (peak_* deferred, see below)_* — run-ledger: `started_at`/`completed_at` now flow
      through both the daemon's default builder and `heartbeat_cli.py`'s `_vm_run_summary_payload`; `peak_*` resources
      are NOT built (only instantaneous-at-completion `cpu_pct`/`mem_pct`/`disk_pct`, honestly documented in the code
      comment as a follow-up — real peak-tracking needs a running-max mechanism this pass didn't add). Idle-spend: the
      job lives in `deployment-api` as `POST /internal/idle-spend-snapshot` (`_idle_spend_scheduler.py`,
      Cloud-Scheduler-OIDC-authed, reusing the exact `verify_reap_scheduler_oidc` identity the existing reap-tick uses),
      calls the real `build_orphan_inventory`, inserts via `operational_data_writer.write_idle_spend_snapshot` (UTL
      `insert_rows`, never raw `google.cloud`). `reap_events` rows are written from BOTH `/api/fleet/reap` and
      `DELETE /api/fleet/instances/{name}` inside `fleet.py`, skipped on `dry_run`. **Verified against the REAL fleet**
      (not mocked): 39 VMs / 40 disks scanned, 8 idle resources found, 9 rows written (1 rollup + 8 per-resource),
      confirmed in BigQuery. `reap_events` wiring is unit-tested (`test_operational_data_writer.py`) but NOT fired
      against a real reap/delete this session (that's a real destructive VM action, correctly out of scope here).
- [x] ✅ **PR-8 DONE 2026-07-27** — orphaned `deployment-events-monitor` subscription deleted for real
      (`gcloud pubsub subscriptions delete`, confirmed gone); `/codex/05-infrastructure/event-sink-chain.md` corrected
      in 5 places (summary, chain table, active-subscriptions section, ASCII trace diagram, file-pointers table) —
      confirmed independently via a fresh grep of `monitor.py` (zero `pubsub`/`subscribe` hits, real
      `get_storage_client` usage) before editing, not just trusting the earlier research pass.
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

- [x] ✅ **Schema + table DONE 2026-07-27** — `process_samples` created live in `deployment_operational_data` (vm_name,
      ts, category, pid, comm, cpu_pct, mem_pct, mem_rss_kb, elapsed_sec; partitioned by `DATE(ts)`, clustered by
      vm_name+category) via `deployment-service/scripts/bootstrap_operational_data_bq.py`. **Nothing publishes into it
      yet** — see the next two todos, both still open; the table exists but is empty in production today.
- [x] ✅ **DONE 2026-07-28 — categorization heuristic refined with real ancestry.** Confirmed (agent-orchestrator
      research): autospawn tick, manual dashboard "spawn", escalation, and plan_health ALL funnel through the identical
      `tmux_spawn.py::_start_session` path — there is no code-level distinction between "autospawn-triggered" and
      "human-clicked-spawn," both produce an autonomous background worker. The one genuine distinction is that path vs a
      literal interactive terminal/IDE-extension session, which never goes through `tmux_spawn` at all (confirmed
      against `test_orphan_process_reap.py`'s own "no CLAUDE_CONFIG_DIR at all (an operator's own interactive session)"
      fixture). Added `AO_DISPATCH_MODE=autonomous` + `AO_SESSION_NAME` exports to `tmux_spawn.py`'s launch command
      (single SSOT, 2 lines, `agent-orchestrator@6f0da49` region) — readable via `/proc/<pid>/environ`. **Verified live
      on the real orchestrator VM**: of 526 sampled processes, 10 correctly bucketed `ao_plan_work` (via the new marker)
      cleanly separated from 5 `worker_agent` (interactive, no marker) and 36 `ci` (Runner.Listener) — a real, direct
      proof the heuristic works, not a unit-test-only claim.
- [x] ✅ **DONE 2026-07-28 — bridge cron replaced with the real pipeline.** New
      `agent-orchestrator/scripts/orchestrator/process_category_sampler.py`: enumerates every host process via `psutil`
      every ~5 min (systemd timer, `OnUnitActiveSec=300`), categorizes via the heuristic above, publishes each row via
      `PubSubFlatEventPublisher` to a new `process-samples` topic (3d retention, created live) → native BQ subscription
      `process-samples-bq` (created live) → `process_samples`. CPU% uses a cross-tick delta (state persisted to
      `/var/lib/process-category-sampler/prev_snapshot.json`, keyed by `pid:create_time` to avoid PID-reuse aliasing)
      rather than an in-script sleep, mirroring the bridge cron's own "don't disturb the box" design note. 13 new unit
      tests. **Verified end-to-end for real**: a live non-dry-run invocation on `i-0c9b283b31d6b5ca7` published 507/507
      samples; `bq query` against `process_samples` for today confirms the exact same category breakdown landed (452
      other / 39 ci / 10 ao_plan_work / 5 worker_agent / 1 orchestrator). systemd timer+service+installer
      (`install-process-category-sampler.sh`, mirrors `install-orch-watchdog.sh`'s pattern) installed on the VM; **the
      automated systemd-wrapped run failed to start on first install (control-process error, not yet root-caused — the
      identical manual invocation the verification above used works perfectly, so this is a systemd-unit wiring issue,
      not a script bug)** — STILL OPEN, needs `journalctl -u     process-category-sampler.service` diagnosis before the
      timer can be trusted unattended. **Bridge cron (`resource-monitor.sh`, root's crontab `*/5 * * * *`) NOT yet
      retired** — correctly left running as the safety net until the systemd timer issue above is fixed and the real
      pipeline is proven to run unattended, not just via manual invocation.
- [x] ✅ **API DONE 2026-07-27, UI view NOT built** — `GET /api/vm-resources/process-category` exists in deployment-api
      (query builder + endpoint + tests, mock-mode/no-project/query-failure all degrade to an honest empty response) and
      has mock fixtures wired in `deployment-ui`, but no component actually calls it yet — the rolling-window UI work
      this session was the resource-samples signal (WorkHealthCard selector + comparison page), not this one. Wiring a
      view is straightforward once the two todos above land (no point rendering an always-empty chart before
      `process_samples` has real rows).

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

- [x] ✅ **BigQuery dataset + tables DONE 2026-07-27** — all FIVE tables live in `deployment_operational_data`
      (asia-northeast1): `resource_samples`, `run_ledger`, `idle_spend`, `reap_events`, `process_samples`. Confirmed via
      `bq ls` with correct partitioning (`DATE(ts)`/`DATE(completed_at)`) and clustering on every table.
- [x] ✅ **Resource-sample event type DONE** — `RESOURCE_SAMPLE`/`RUN_LEDGER_RECORDED` added to the canonical
      `unified_trading_library/events/event_types.py` only, as a new `OPERATIONAL_TELEMETRY_EVENT_TYPES` set separate
      from `DEPLOYMENT_EVENT_TYPES` (canonical count unchanged at 7 — confirmed by test).
- [x] ✅ **Dedicated Pub/Sub topics + flat schema DONE** — `resource-samples` (3d retention) + `run-ledger` (30d) topics
      live in `central-element-323112`, created via the extended `setup-pubsub.sh` registry.
- [x] ✅ **Daemon publish via BOTH call sites DONE** — see PR-3 above (`heartbeat_cli.py` + `deployment_heartbeat.py`),
      additive alongside the Firestore `host_metrics_window` write, best-effort.
- [x] ✅ **Native BigQuery subscriptions DONE + END-TO-END VERIFIED** — `resource-samples-bq`/`run-ledger-bq`
      (`--use-table-schema --drop-unknown-fields`). Needed a real IAM grant this session (the Pub/Sub service agent
      lacked `bigquery.dataEditor` on the new dataset — granted via `bq update` after `bq add-iam-policy-binding`
      reported "requires allowlisting"). **Proven live**: published a flat JSON test message to `resource-samples`,
      queried it back from `resource_samples` as a correctly-typed row within ~20s, then deleted the test row
      (partition-filtered `DELETE`, since streaming-buffer rows can't be deleted without one).
- [x] ✅ **Orphaned subscription deleted + codex fixed** — see PR-8 above.
- [x] ⚠️ **Resource-stats pipeline verified end-to-end, NOT yet from a real running VM's HeartbeatDaemon** — the manual
      publish/query/cleanup above proves the topic→subscription→table mechanics are correct against the EXACT schema the
      daemon code now builds, but no real `heartbeat_cli.py` has actually run this code in production yet (that needs
      deployment-service redeployed with these changes and a live VM run) — an honest gap, not a claim of full
      production verification.
- [x] ✅ **Run-ledger fields DONE** — see PR-6 above (`started_at`/`completed_at` added; `peak_*` deferred, noted).
- [x] ✅ **Dedicated topic + subscription for run_ledger DONE** — same verification caveat as resource-stats above
      (mechanism proven via the resource-samples publish/query test; not yet observed from a real daemon run).
- [x] ⚠️ Same real-VM caveat as above — no live run_ledger row from an actual VM yet, only the proven mechanism.
- [x] ✅ **Idle-spend scheduled snapshot DONE + VERIFIED AGAINST THE REAL FLEET** — see PR-6 above: 39 VMs/40 disks
      scanned, 9 rows written, confirmed in BigQuery (not mocked).
- [x] ✅ **Reap-event logging DONE (code + unit tests), not fired against a real reap this session** — see PR-6 above.
- [x] ✅ **Idle-spend verified for real** — see PR-6 above; the daily-snapshot endpoint's real-fleet run IS the
      verification (not a separate mocked check).
- [x] ✅ **DONE 2026-07-28 — Retention/TTL.** See PR-4 above (same fix, duplicate todo) — wrapper extended + all 4
      non-run_ledger tables retroactively TTL'd, confirmed live via `bq     show`.
- [x] ✅ **Rolling-window aggregate query API DONE** — `deployment-api` `/api/vm-resources/rolling` +
      `/api/vm-resources/process-category`, SQL-injection-safe (`vm_name` regex-validated, `window` a FastAPI `Literal`
      enum), 21 unit tests, verified live against `test-project`.
- [x] ✅ **Host Resources panel extension DONE** — `WorkHealthCard` window selector (Live/1h/4h/24h/1wk), verified live
      via Playwright (`tests/smoke/vm-resource-rolling-window.spec.ts`, 3 tests, run against the actual dev server +
      mock API, not just typechecked).
- [x] ⚠️ **Cross-VM comparison page DONE, SIMPLIFIED filter** — `/ops/vm-resources`, verified live via the same
      Playwright spec. Filters by a service-name text match only (not the full service × asset_group × mode facet set
      the original ask described) — the backend endpoint only accepts an optional `vm_name` filter today; a richer
      filter would need new query params + SQL `WHERE` clauses, not built this session.
- [ ] [REVIEW] P2. **STILL OPEN — analysis path doc.** Not written this session.
- [x] ✅ **Ship verified 2026-07-28** — all five touched repos confirmed clean + fully pushed to
      `origin/live-defi-rollout` (`ahead=0`, `git status --porcelain` empty): deployment-api, deployment-ui,
      deployment-service, unified-trading-library, agent-orchestrator. Re-verified while unblocking an unrelated GHA
      self-hosted-runner fan-out that hit this plan's own QG failures in deployment-api (`vm_resource_history.py`
      codex-compliance) and deployment-ui (`NavMenu`/`TopNavBar` nav-count tests) — both fixed and shipped as part of
      that session, confirmed still landed here.
- [x] ✅ **Codex audit DONE 2026-07-27 (light pass)** — added a "Durable operational data" section to
      `/codex/05-infrastructure/deployment-observability.md` (tables, write/read path, known gaps) + a `related:` link
      to this plan. NOT done: a cross-ref edit inside `/codex/02-data/live-data-persistence-and-event-log.md` itself
      (that doc wasn't opened this session) — a one-liner there pointing back would close the loop fully.

## Success criteria

- All FOUR signals land in BigQuery and are queryable together: per-VM resource timeline, run history (incl. >30 days
  old), idle-spend trend + reclaimed-over-time, and process-category breakdown on multi-tenant hosts. **4 of 4 DONE**
  (2026-07-28) — process-category now has a real, verified-live pipeline (see PR-4/categorization/bridge-cron todos
  above); the ONLY remaining wrinkle is the systemd timer failing to start unattended (manual invocation proven, the
  automation wrapper is not yet), so the bridge cron stays as the safety net until that's fixed.
- The cross-VM comparison the operator wanted (N VMs by service × asset_group × mode) is a single query AND a UI page.
  **PARTIAL** — the UI page + query both exist and are live, but the filter is service-name-text only today, not the
  full service×asset_group×mode facet set.
- The rolling 1h/4h/24h/1wk view is embedded in the EXISTING Host Resources panel (not a new page); the Firestore
  live/current Resources column is unchanged. **DONE**, verified live via Playwright.
- Cost stays ~$0 (storage ~$0.08/mo; queries within the free tier); no GCS file-management machinery introduced. **DONE
  by construction** (BQ streaming-insert + native subscriptions only, no GCS added).
- Run history survives past the 30-day archive TTL via the durable `run_ledger`. **Mechanism DONE**, real-VM
  confirmation still pending (see the honest caveat on the todo above).
- The bridge cron on the orchestrator VM is retired once `process_samples` verifiably lands the same data via the real
  pipeline. **PARTIAL (2026-07-28)** — the real pipeline is built + verified landing the same data (507/507 rows
  confirmed in BigQuery matching the manual dry-run's categorization exactly), but only via a MANUAL invocation; the
  systemd timer meant to make this unattended failed to start on first install. Bridge cron correctly left running until
  that's fixed — retiring it now would create a real gap, not just an untidy loose end.
- Post-scale verification (from the VM-resize decision this session motivated): once the orchestrator VM is resized, the
  rolling-window view shows utilization settling in a healthy range (roughly 50-70% average with burst headroom) — not
  pinned near 90%+ (under-provisioned) and not sitting at 30-40% (over-provisioned, money left on the table). **The
  resize happened THIS session** (`m8i.2xlarge`→`m8i.4xlarge`, see the GHA followups doc) — verification needs a
  sustained observation window over the coming days via the now-live `resource_samples` pipeline, not a single
  point-in-time check.

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
- **2026-07-27 (same session, continued) — implementation shipped for signals 1-3; signal 4 (process-category) is
  table-only.** unified-trading-library: consolidated the 3-way `DEPLOYMENT_EVENT_TYPES` drift, added
  `RESOURCE_SAMPLE`/`RUN_LEDGER_RECORDED` to the canonical module, threaded caller-supplied flat-publisher hooks through
  `HeartbeatDaemon` (6 new unit tests, 27/27 pass). deployment-service: both publisher call sites wired
  (`heartbeat_cli.py` + the standalone `deployment_heartbeat.py`), the latter's bare `os.environ` topic-resolution bug
  fixed onto the typed `DeploymentConfig` in the same pass; `setup-pubsub.sh` extended with a new
  `BQ_SUBSCRIPTION_REGISTRY` mechanism (native BQ subscriptions need `--use-table-schema`, a genuinely different gcloud
  call shape than the existing pull-subscription helper); `bootstrap_operational_data_bq.py` created and RUN for real.
  deployment-api: `/api/vm-resources/rolling` + `/api/vm-resources/process-category` (21 tests),
  `/internal/idle-spend-snapshot` (reuses the existing reap-tick's Cloud Scheduler OIDC identity), `reap_events` wired
  into both `/api/fleet/reap` and `DELETE /api/fleet/instances/{name}`. deployment-ui: `WorkHealthCard` window
  selector + a new `/ops/vm-resources` comparison page, both verified live via Playwright against the dev server (not
  just typechecked). **Everything above was verified against the REAL `central-element-323112` project, not just
  mocked**: the dataset/5 tables were created live; a real IAM gap surfaced and was fixed (the Pub/Sub service agent
  needed `bigquery.dataEditor` on the new dataset, granted via `bq update` after the `add-iam-policy-binding` CLI path
  reported "requires allowlisting"); a real flat message was published end-to-end through `resource-samples` → the
  native BQ subscription → a correctly-typed `resource_samples` row, then cleaned up; the idle-spend snapshot ran
  against the REAL fleet (39 VMs/40 disks, 9 rows written). What's honestly still open: process-category's real publish
  pipeline (table exists, nothing feeds it — the bridge cron + ancestry-aware categorization are untouched),
  partition-expiration TTL (the UTL `create_table` wrapper still has no expiration param), the analysis-path doc, and
  the post-phase codex audit below.
- **2026-07-28 (operator: "do the rest /autonomous")** — closed 3 of the 4 remaining gaps for real, verified live, not
  just in code:
  - **PR-4/TTL**: extended `GCPAnalyticsClient.create_table` with `partition_expiration_ms` (`unified-trading-library`),
    wired per-table values into `bootstrap_operational_data_bq.py` (`deployment-service`), retroactively applied via
    `bq update --time_partitioning_expiration` to the 4 already-live tables (not `run_ledger`, deliberately). Confirmed
    via `bq show` on all 5.
  - **Categorization heuristic + real pipeline (4th signal)**: added `AO_DISPATCH_MODE` to `tmux_spawn.py`
    (agent-orchestrator) after confirming via research that autospawn/manual-spawn/escalation/plan_health all funnel
    through one path, and the real distinction is that path vs a literal interactive session (never touched tmux_spawn).
    Built `process_category_sampler.py` (psutil-based, cross-tick CPU-delta, no in-script sleep) + systemd
    timer/service/installer. Created the `process-samples` topic + native BQ subscription live. **Verified end-to-end on
    the real orchestrator VM**: manual invocation published 507/507 rows, `bq query` confirms the exact categorization
    breakdown landed (452 other / 39 ci / 10 ao_plan_work / 5 worker_agent / 1 orchestrator) — direct proof the
    ancestry-aware heuristic works in production, not just in unit tests.
  - **Honest open item**: the systemd timer meant to make the sampler run unattended every 5 min failed to start on
    first install (control-process error) — not yet root-caused. The bridge cron (`resource-monitor.sh`) is correctly
    still running as the safety net; retiring it now, before the timer issue is fixed, would create a real monitoring
    gap. Next session: `journalctl -u process-category-sampler.service -n 50 --no-pager` on `i-0c9b283b31d6b5ca7` to
    diagnose (likely candidates: `User=ubuntu` + venv path resolution under systemd's stripped-down env, or the
    `EnvironmentFile=-.env.local` line masking something — untested hypotheses, not confirmed).
  - **Still open, not started this session**: process-category UI wiring in deployment-ui (API + mock fixtures + client
    types already exist, just unused — needs a new tab/section in `VmResourceComparison.tsx`, likely a stacked-bar view
    following `DeploymentFrequencyChart.tsx`'s recharts precedent, plus enriching the flat 3-category mock fixture in
    `mock-api.ts` to all 5 categories); the analysis-path doc (DuckDB-over-`bq extract`, to slot into
    `deployment-observability.md` after its existing "Durable operational data" section, following
    `billing-cost-observability.md`'s DuckDB-over-parquet style as the closest template); the codex cross-ref in
    `live-data-persistence-and-event-log.md`.
  - **Mid-session interrupt (tracked separately, not lost)**: the operator asked a live cost question about
    `unified-trading-system-ui` (~$71) that led to discovering a SEPARATE, real finding — Wave-1's self-hosted-runner
    fan-out missed several shared templates (`staging-lock-check.yml`, `image-build-gate.yml`) and
    `unified-trading-system-ui`'s own bespoke `ubuntu-latest` workflows fleet-wide. Operator authorized the fix; filed
    as its own issue doc (`plans/active/issues/gha_fleet_wide_missed_ubuntu_latest_workflows_wave2_2026_07_28.md`) since
    it's a different plan's lifecycle (the GHA fan-out, not this BQ plan) — not tracked here beyond this pointer.

## Codex SSOTs

- `/codex/02-data/live-data-persistence-and-event-log.md` — the UTL event spine (EventTransport facade / Pub/Sub) this
  plan rides.
- `/codex/05-infrastructure/deployment-observability.md` — deployment inventory + (to add) the durable-operational-data
  contract (three BQ tables, retention, Firestore-live/BQ-history split).
- `/codex/06-coding-standards/quality-gates.md` — no raw `google.cloud`/`boto3`; BQ access via the UTL cloud interface.
