---
doc_type: issue
title: >-
  TradFi `pipeline_mode~live` manifest shard-atom has 24 rows (max `written_at=2026-08-04T08:51:36Z`) attributed to no
  currently-known writer — the now-deleted `mtds-live-tradfi-cme-trades-20260623-095619` VM was gone 5 weeks before that
  write
summary: >-
  `tradfi_live_cme_capture_stopped_2026_08_09.md`'s diagnosis (slot-5) confirmed the last real tradfi live producer,
  `mtds-live-tradfi-cme-trades-20260623-095619`, was manually `v1.compute.instances.delete`'d by
  `harshkantariya@odum-research.com` at 2026-06-30T06:53:16Z. But the tradfi `availability_index.parquet`'s 24
  `pipeline_mode` containing "live" rows have a max `written_at` of 2026-08-04T08:51:36Z — over a month AFTER that VM
  was deleted. Since the deleted VM cannot have written those rows, some OTHER process (a backfill, a manifest
  reconciler, or a mis-tagged batch writer) is writing to the same `pipeline_mode~live` shard-atom for tradfi. Flagged
  as a smaller, non-blocking finding in the parent diagnosis but never turned into a tracked todo — this doc closes that
  gap per `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` § 2 ("every follow-up is a canonical
  todo, never prose").
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [tradfi, live-capture, manifest, pipeline-mode, data-pipeline-correctness]
related:
  [
    /plans/archive/2026_08/issues/tradfi_live_cme_capture_stopped_2026_08_09.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /codex/02-data/pipeline-mode-partition.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-08-09
author: slot-17
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.36
assigned_role: data_engineering
drift_direction: advance-code
sequential: false
locked_by:
resolved_by:
source: >-
  Migrated out of tradfi_live_cme_capture_stopped_2026_08_09.md's todo 2 Progress Log aside (slot-5, 2026-08-09) at
  archival time — the finding was written as prose ("worth a separate, smaller finding but not blocking this diagnosis")
  and never became a tracked todo.
depends_on: []
---

# TradFi live manifest shard-atom has an unidentified writer post-VM-deletion

## What I found

`tradfi_live_cme_capture_stopped_2026_08_09.md` todo 2's diagnosis (slot-5) established via `gcloud logging read` (Admin
Activity, 60d freshness) that the last real tradfi live producer VM, `mtds-live-tradfi-cme-trades-20260623-095619`, was
deleted by a deliberate authenticated API call (`v1.compute.instances.delete`, `harshkantariya@odum-research.com`) at
**2026-06-30T06:53:16Z** — confirmed NOT a `compute.instances.preempted` systemevent. Yet the original finding's own
manifest read (full `_index/availability_index.parquet` filtered to `pipeline_mode` containing `"live"`) showed 24 rows
total for `venue=CME`, with the most recent `written_at` = **2026-08-04T08:51:36.343931+00:00** — over a month AFTER the
VM that would have written them was already gone.

## Why it matters

Either (a) some other, currently-unidentified process is writing to the tradfi live shard-atom (a backfill/reconciler
mis-tagging `pipeline_mode`, a stale/orphaned script, or a shared shard-atom collision with another pipeline_mode
family), or (b) the 24-row read itself is stale/cached and doesn't reflect current manifest state. Either way this is
unexplained and worth a small, bounded investigation before assuming it's benign — an unidentified writer touching a
`live` shard-atom could also explain other TradFi manifest anomalies not yet surfaced.

## Recommended decision

- [ ] [DATA] P3. Identify what process wrote the 24 `pipeline_mode~live` / `venue=CME` rows in the tradfi
      `availability_index.parquet` (max `written_at=2026-08-04T08:51:36Z`), given the only known live producer VM for
      this shard was deleted 2026-06-30 — over a month earlier. Grep every `market-tick-data-service` /
      `deployment-service` write call site that could plausibly tag `pipeline_mode` containing `"live"` for
      `asset_group=tradfi`, cross-check against VM launch history (`gcloud logging read` / `vm-census/*.json`) for
      anything active around 2026-08-04, and report the actual source (or confirm the read was stale/mis-scoped). No
      code change required unless a genuine mis-tagging bug is found — if one is, fix it and cite this doc. (repo:
      market-tick-data-service)
