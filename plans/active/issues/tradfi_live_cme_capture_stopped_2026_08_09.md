---
doc_type: issue
title: >-
  TradFi live capture (CME trades) has been DOWN since 2026-08-04 — zero `mtds-live-tradfi-*` VMs exist in either cloud,
  last live-pipeline manifest write is ~5 days stale
summary: >-
  Re-verified the 2026-06-23 "9 live data VMs frozen" finding in
  `/plans/active/data_pipeline_hardening_self_monitoring_2026_06_22.md` per its 2026-08-09 RECLASSIFY done-when. CeFi
  live capture (deribit/hyperliquid) has RECOVERED — the consolidated launcher
  (`mtds-live-cefi-consolidated-20260809-121034`, GCP `central-element-323112`) is RUNNING and actively writing
  `capture_status=captured` rows for DERIBIT/HYPERLIQUID trades as of 2026-08-09T15:36 UTC (checked at 16:07 UTC, ~30min
  fresh). TradFi live capture is a DIFFERENT and CURRENT finding: `gcloud compute instances list` against
  `central-element-323112` (all zones, all statuses) has ZERO instances matching `mtds-live-tradfi-*` or any
  live/CME-trades name; AWS `427895769566`/`ap-northeast-1` has only the orchestrator + ci-escalation-runner VMs
  running. No `vm-heartbeat/mtds-live-tradfi*` blob and no `_index/per_vm/mtds-live-tradfi*.parquet` shard exist in the
  `market-data-tick-tradfi-prd-central-element-323112` bucket. Reading the full tradfi `availability_index.parquet` and
  filtering `pipeline_mode` containing "live" shows only 24 rows ever recorded for `venue=CME`, with the MOST RECENT
  `written_at` = **2026-08-04T08:51:36 UTC — ~5.3 days stale as of this check (2026-08-09T16:08 UTC)**. This is distinct
  from the original 2026-06-23 finding (which was about VMs silently RUNNING-but-frozen); the current state is that no
  tradfi live producer VM exists at all. `/codex/02-data/tradfi-databento-sourcing-ssot.md` confirms the live WS
  producer (`databento_tradfi_ws` via `launch-mtds-live.sh --asset-group tradfi`) was verified WORKING 2026-06-21 and is
  NOT subscription-blocked — this is an operational gap (nobody relaunched it after it stopped/was preempted), not a
  missing feature.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [deployment-service, market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags: [tradfi, live-capture, cme, mtds-live, vm-launcher, data-pipeline-correctness, silent-outage]
related:
  [
    /plans/active/data_pipeline_hardening_self_monitoring_2026_06_22.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/05-infrastructure/runtime-tiers-and-deployment.md,
  ]
created: 2026-08-09
author: slot-24
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
drift_direction: advance-code
sequential: false
locked_by:
context_scope:
  [
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/05-infrastructure/runtime-tiers-and-deployment.md,
    deployment-service/scripts/vm/launch-mtds-live.sh,
    deployment-service/deployment_service/vm_prefix_registry.py,
  ]
resolved_by:
source: >-
  data_pipeline_hardening_self_monitoring_2026_06_22.md's 2026-08-09 round11 RECLASSIFY note on the sole open P0 "9 live
  data VMs frozen" todo — its done-when required either naming current live VMs + fresh manifest recency, or filing a
  NEW P0 finding if live capture is genuinely stopped. TradFi resolved to the latter; CeFi resolved to the former
  (checkbox flipped in the parent plan, not forked here).
depends_on: []
---

# TradFi live capture (CME trades) has been down since 2026-08-04

## What I found

Live-VM census (2026-08-09, both clouds):

- **GCP `central-element-323112`** (`gcloud compute instances list`, all zones/statuses): zero instances match
  `mtds-live-tradfi-*`, `live-tradfi`, or `cme` in the name. Every currently-running `tradfi-*` VM is a `tradfi-bf-*`
  **batch backfill** launcher (CBOE/ICE index OHLCV, CME OHLCV-1m, FRED) — none is the live WS producer.
- **AWS `427895769566`/`ap-northeast-1`**: only `agent-orchestrator-vm-1` and `ci-escalation-runner-vm-1` running — no
  tradfi capture instance there either.
- `gs://market-data-tick-tradfi-prd-central-element-323112/vm-heartbeat/mtds-live-tradfi*` — no objects.
- `gs://market-data-tick-tradfi-prd-central-element-323112/_index/per_vm/mtds-live-tradfi*.parquet` — no objects.
- Full `_index/availability_index.parquet` read, filtered to `pipeline_mode` containing `"live"`: 24 rows total, all
  `venue=CME`, max `written_at` = `2026-08-04T08:51:36.343931+00:00` (~5.3 days stale at check time 2026-08-09T16:08
  UTC).

By contrast, CeFi's equivalent live producer IS healthy: `mtds-live-cefi-consolidated-20260809-121034` is RUNNING in
GCP, its `_index/per_vm/mtds-live-cefi-consolidated-20260809-121034.parquet` shard was last written
2026-08-09T16:07:18Z, and it carries `capture_status=captured` rows for DERIBIT/HYPERLIQUID trades with `written_at` up
to 2026-08-09T15:36 UTC (row_count 1-142 per tick batch) — actively flowing, not frozen.

## Why it matters

`/codex/02-data/tradfi-databento-sourcing-ssot.md` documents the tradfi live WS producer (`databento_tradfi_ws`, driven
by `launch-mtds-live.sh --asset-group tradfi`) as verified WORKING 2026-06-21 and explicitly IN the operator's Databento
subscription (not blocked). `deployment_service/vm_prefix_registry.py` still registers `mtds-live-tradfi-` as
`LifecycleClass.LONG_LIVED_LIVE` — i.e. this VM class is supposed to run 24/7 and be relaunched on preemption/exit, the
same as the now-healthy CeFi consolidated launcher. Its absence means CME live trades have not been captured for over 5
days — a silent gap the old infra-sidecar watcher (the same one this parent plan's Phase 2 replaced) would not have
caught, and per CLAUDE.md's data-pipeline-correctness HARD RULE this is heartbeat-class work, not deferrable.

## Recommended decision

Relaunch the tradfi live producer and verify it sticks (infra craft, AO-eligible — bounded, deterministic outcome):

- [ ] [INFRA] P0. Relaunch `mtds-live-tradfi` for CME trades via `deployment-service/scripts/vm/launch-mtds-live.sh`
      (`--asset-group tradfi --shard-spec tradfi:CME:trades`, instrument-ids per the live MVP coverage set
      `/codex/02-data/tradfi-databento-sourcing-ssot.md` names); confirm STARTED <60s, a fresh `vm-heartbeat/<vm>.txt`
      blob, and ≥1 `capture_status=captured` row written to `_index/per_vm/<vm>.parquet` within 10 min of launch (mirror
      the CeFi consolidated launcher's verified pattern above). (repo: deployment-service)
- [ ] [INFRA] P1. Diagnose why the previous tradfi live VM stopped/was never relaunched after 2026-08-04 (preemption
      without recovery vs. a crash vs. a manual stop) — check `/vm-preemption-billing-waste-audit`'s registry for a
      matching preempted-without-resume entry for any `mtds-live-tradfi-*` instance name; if the watchdog/relaunch path
      has a gap for this VM class specifically, file the systemic fix as its own todo in the parent hardening plan
      rather than just relaunching once more. (repo: deployment-service, unified-trading-pm)
