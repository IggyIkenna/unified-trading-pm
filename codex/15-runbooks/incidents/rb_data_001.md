---
doc_type: codex-runbook
title: RB-DATA-001 — Data-Pipeline Cascade (consolidator → MTDS → features)
summary:
  "On-call runbook for the #data-pipeline-alerts DP_* capture-cascade failures (instruments-service → MTDS → MDPS →
  features); RTO<30min / RPO<5min; most heal via auto_recover/file_issue tiers — only page_operator cases
  (DP_MISSING_CREDENTIAL, DP_RUN_MOSTLY_EMPTY, DP_VM_GONE_NO_CAPTURE, etc.) need a human."
status: current
nature: process
asset_group: [meta]
stage: [meta]
repos: [instruments-service]
scope: [admin, engineer]
tags: [runbook, incident, data-pipeline, manifest, self-healing, disaster-recovery, monitoring]
related: [/codex/15-runbooks/incidents/README.md, codex/05-infrastructure/data-pipeline-alerts.registry.yaml]
created: 2026-06-22
owner: ikenna@odum-research.com
cadence: Quarterly game-day
verifier: manifest_hygiene_daily.py (defi) live-relay proof 2026-06-22
last_executed: never
code_refs:
authoritative_for: [RB-DATA-001 operator runbook — data-pipeline cascade DR]
referenced_by:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
    /plans/archive/2026_08/data_pipeline_hardening_self_monitoring_2026_06_22.md,
  ]
---

# RB-DATA-001 — Data-Pipeline Cascade (consolidator → MTDS → features)

> **What this is:** the on-call stop when a `#data-pipeline-alerts` DP_* alert fires for the capture cascade
> (instruments-service → MTDS → MDPS → features). Most of this is **already self-healing** — read the auto-recovery
> scope FIRST and only act where it says human.

## TL;DR

Category: **Data pipeline** · Runbook ID: **RB-DATA-001** · Channel: `#data-pipeline-alerts`. **RTO < 30 min · RPO < 5
min** (consolidated `_index` is the recoverable artifact; per-VM shards are the WAL). The failure-mode registry
(`data-pipeline-alerts.registry.yaml`) tags every DP_* with an `escalation` tier — **`auto_recover` self-heals,
`file_issue` auto-spawns a worker, only `page_operator` needs you.**

## Auto-recovery scope — what heals WITHOUT a human (do NOT pre-empt it)

Per `autonomous-recovery-matrix.md` (protective + in-scope-reversible = autonomous):

| DP event                                           | Auto-actuator (Layer-0)                                                                                | Bound                             |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------------------ | --------------------------------- |
| `CONSOLIDATOR_DOWN`                                | `scripts/recovery/relaunch_consolidator.py` re-executes the `manifest-consolidator-{ag}` Cloud Run Job | 1 / 120s cooldown                 |
| `DP_VM_EXIT_NONZERO` (exit 137 OOM)                | `scripts/recovery/relaunch_backfill_vm.py` re-launches (resize-up) the backfill                        | ≤2 / (vm-prefix, day) → then page |
| `DP_RATELIMIT_AS_EMPTY` / `DP_SOURCE_RATE_LIMITED` | backoff + `refetch_feed.py` (stale-feed)                                                               | 300→600→1200→3600s ladder         |
| `DP_KEY_POOL_EXHAUSTED`                            | 429-aware key rotation already rotated; exhaustion = all keys 429'd in-window                          | emits CRITICAL → page             |

A `file_issue`-tier finding (e.g. `DP_DIVERGENT_EMPTY`, `DP_PHANTOM_ROWS`, `DP_NOT_V9`) **auto-files
`plans/active/issues/<dp>_<date>.md`** and (via wall-type `data_pipeline_failure`) can **auto-spawn a worker** that
diagnoses + fixes + ships. **You only get paged for `page_operator`-tier** (DP_MISSING_CREDENTIAL, DP_RUN_MOSTLY_EMPTY,
DP_VM_GONE_NO_CAPTURE, DP_CATALOG_NOT_RUNNING, DP_WATCHER/CRON down) — the genuinely-novel cases.

## First 60 seconds — scope (page_operator only)

1. Acknowledge. Open the alert's `/deployments` + data-status deep-links (in the Slack message buttons).
2. Read the `details`: which `(asset_group, venue, data_type, day)` + `exit_code` / `error_signal`.
3. Confirm the consolidator is up: `assert_consolidator_healthy(bucket)` / the `*/2` liveness watchdog last-emit.

## Diagnose (the cascade, upstream→downstream)

- **Consolidator down + per-VM shards exist** → stale `_index`. If the auto-relaunch already fired (check
  `CONSOLIDATOR_RECOVERED`) and it's still down → the Cloud Run Job itself is failing (read its run.log via the
  `/deployments/{name}` drill-down); not a transient → fix the job, not the data.
- **`DP_MISSING_CREDENTIAL`** → a venue key didn't resolve (SM access / wrong secret name). Fix the SM grant; this is
  the #1 silent-zero cause. NOT a data gap.
- **`DP_RUN_MOSTLY_EMPTY`** (≥X% empty) → a venue/source changed shape or a code path regressed (the FetchEvidence gate
  should have caught a fall-through — if it's `empty_confirmed` at scale, the source genuinely returned 200+empty OR the
  adapter mis-stamps). Cross-check with the daily empty-reprobe (`DP_EMPTY_REPROBE_DISAGREEMENT`).
- **`DP_VM_GONE_NO_CAPTURE`** (drained but captured flat) → OOM/hang masked by self-delete; read the persisted
  `vm-logs/{vm}/EXIT_STATUS` + `run.log` (survive self-delete). If 137 → the OOM relaunch budget is spent → resize the
  launcher machine type permanently.
- **`DP_READER_WRITER_BUCKET_MISMATCH`** → a preflight reader resolves env-less vs the env-short writer bucket (the
  DeFi-stuck-at-6% class). Align the reader's `resolve_bucket_name` env.

## Recover (human, where auto-scope ended)

1. Fix the root cause on `live-defi-rollout`, ship via `quickmerge --agent --files`.
2. Re-run the affected capture: the MTDS CLI for the specific `(asset_group, day, venue)` (NEVER copy instrument defs
   between dates). For a consolidator job, `gcloud run jobs execute manifest-consolidator-{ag}`.
3. Verify recovery: the manifest 4-state for the cells flips to `captured`; the hygiene audit goes GREEN next run; the
   `#data-pipeline-alerts` RESOLVED bookend posts.

## RTO / RPO

- **RPO < 5 min**: per-VM shards (`_index/per_vm/{vm}.parquet`) are the write-ahead log; the consolidator merges them →
  no data lost beyond the last unconsolidated shard write.
- **RTO < 30 min**: consolidator relaunch (auto, ≤2min) + a single-cell re-capture. A full corpus re-walk is NOT on the
  RTO path (it's a weekly hygiene job).
- **Pre-migration drain** (before any bucket SSOT cutover): stop all VMs (GCP+AWS) + consolidate + snapshot
  `_index/snapshots/pre_migration_<date>.parquet` (see `code_freeze_migrate_backfill_sequencing`).

## Post-mortem

- Was the failure mode already in `data-pipeline-alerts.registry.yaml`? If not → **append a new DP-<CAT> mode** (the
  registry is the shared pool; an unmonitored class recurs).
- Should it have auto-recovered? If a `page_operator` case is actually deterministic → move it to `auto_recover` + add
  the actuator. Drive the alert's `status` `verbose → baselined → zeroed`.
