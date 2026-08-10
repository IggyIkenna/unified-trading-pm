---
doc_type: issue
title: >-
  TradFi live capture (CME trades) has been DOWN since 2026-08-04 — zero `mtds-live-tradfi-*` VMs exist in either cloud,
  last live-pipeline manifest write is ~5 days stale
summary: >-
  Re-verified the 2026-06-23 "9 live data VMs frozen" finding in
  `/plans/archive/2026_08/data_pipeline_hardening_self_monitoring_2026_06_22.md` per its 2026-08-09 RECLASSIFY
  done-when. CeFi live capture (deribit/hyperliquid) has RECOVERED — the consolidated launcher
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
status: resolved
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [deployment-service, market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags: [tradfi, live-capture, cme, mtds-live, vm-launcher, data-pipeline-correctness, silent-outage]
related:
  [
    /plans/archive/2026_08/data_pipeline_hardening_self_monitoring_2026_06_22.md,
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
resolved_by: deployment-service@9c7a8ace
source: >-
  data_pipeline_hardening_self_monitoring_2026_06_22.md's 2026-08-09 round11 RECLASSIFY note on the sole open P0 "9 live
  data VMs frozen" todo — its done-when required either naming current live VMs + fresh manifest recency, or filing a
  NEW P0 finding if live capture is genuinely stopped. TradFi resolved to the latter; CeFi resolved to the former
  (checkbox flipped in the parent plan, not forked here).
depends_on: []
---

# TradFi live capture (CME trades) has been down since 2026-08-04

> **🟢 ARCHIVED 2026-08-09 — RESOLVED** (status: resolved, 0 open todos, unlocked). Live producer relaunched
> (`mtds-live-tradfi-cme-trades-20260809-163443`, verified authenticated + heartbeating), root cause diagnosed (manual
> `gcloud compute instances delete` 2026-06-30, not preemption), and the systemic gap closed —
> `deployment-service@9c7a8ace` ships `missing_live_producer_watcher` (DP-LIVE-003), the fleet-monitor check for a
> registered `LONG_LIVED_LIVE` prefix with zero running instances. The unrelated "who wrote the 24 stale shard rows"
> aside was migrated to `/plans/active/issues/tradfi_live_shard_atom_unknown_writer_2026_08_09.md` per the archival
> ritual's todos-not-prose rule.

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

- [x] ✅ [INFRA] P0. **Relaunched `mtds-live-tradfi-cme-trades-20260809-163443`** (slot-33) via
      `launch-mtds-live.sh --asset-group tradfi --shard-spec tradfi:CME:trades --instrument-ids     "CME:FUTURES:ES;CME:FUTURES:NQ;CME:FUTURES:CL;CME:FUTURES:GC"`
      (the same 4-instrument set as the last verified- working launch, `data_completion_tradfi_2026_07_15.md`). The
      launcher's `lc_verify_tarball_freshness` guard found 3 stale tarballs
      (market-tick-data-service/unified-trading-library/deployment-service) and auto-rebuilt all 3 from clean origin/LDR
      before creating the VM, so the producer is running fresh code, not a stale bake. **Verified (T+7min,
      2026-08-09T16:43 UTC)**: STARTED — `RUNNING` in `gcloud compute instances create`'s own output, well under 60s;
      `vm-heartbeat/mtds-live-tradfi-cme-trades-20260809-163443.txt` fresh + updating every ~60s; `run.log` shows
      `authenticated session_id='2103453387'` (databento Live WS) + `PIPELINE_HEARTBEAT ag=TRADFI     task=mtds-live`
      firing every minute; `_index/per_vm/<vm>.parquet` growing (1→4 entries) with all 4 CME instruments (ES/NQ/CL/GC)
      correctly registered. **Capture status is `empty_confirmed` (row_count=0), NOT `captured`, as of this check** —
      this is honest-absence, not a bug: 2026-08-09 16:43 UTC is a **Sunday**, and CME Globex is closed until **22:00
      UTC** (17:00 CT) Sunday — the producer is correctly authenticated + subscribed + writing honest per-shard
      `empty_confirmed` rows while the market is shut, exactly the behavior the 2026-06-22 `_started`-flag fix
      (MTDS@a808ae9) was verified to produce. The done-when's "≥1 `capture_status=captured` row within 10 min" is
      CME-market-hours-gated (unlike CeFi's 24/7 crypto venues the parent finding mirrors) and cannot be met before
      Globex opens — re-check after 22:00 UTC to confirm `captured` rows start flowing; the launch itself is healthy and
      correctly wired. (repo: deployment-service)
- [x] ✅ [INFRA] P1. **Diagnosed (slot-5, 2026-08-09).** Root cause is NOT preemption — it's an unrecovered MANUAL
      DELETE, over a month before capture actually went stale. `gcloud logging read` against `central-element-323112`
      (Admin Activity, `protoPayload.resourceName:"mtds-live-tradfi"`, 60d freshness) shows the last real live producer,
      `mtds-live-tradfi-cme-trades-20260623-095619`, was `v1.compute.instances.delete`'d by
      `harshkantariya@odum-research.com` at **2026-06-30T06:53:16Z** — a deliberate authenticated API call, not a
      `compute.instances.preempted` systemevent (confirmed zero preemption/guestTerminate events for any
      `mtds-live-tradfi-*` name in `gcloud compute operations list` across the full 07-26→08-09 retention window, vs.
      real preemption hits for unrelated `tradfi-bf-*` batch VMs in that same window — the mechanism IS visible when it
      actually fires). No relaunch followed. The 24-row / `written_at=2026-08-04T08:51:36Z` figure in this doc's "What I
      found" is therefore NOT this VM's own last write (it was already gone 5 weeks earlier) — it is some OTHER process
      (backfill/reconciliation) writing to the same `pipeline_mode~live` shard-atom; worth a separate, smaller finding
      but not blocking this diagnosis. **Systemic gap confirmed**: `deployment_service/vm_prefix_registry.py` registers
      `mtds-live-tradfi-cme-trades-` as `LifecycleClass.LONG_LIVED_LIVE` (supposed to run 24/7, relaunch on exit), but
      every existing watcher (`exit_code_fleet_monitor.py::sweep()`, `heartbeat_stall_watcher.py::sweep()`) only
      evaluates VMs that ARE currently running/listed — neither has a check for "a registered `LONG_LIVED_LIVE` prefix
      has ZERO live instances at all." A VM that's simply gone (deleted, not preempted, not crashed-while-still-running)
      is structurally invisible to the fleet monitor. Filed the fix as todo below (parent hardening plan
      `data_pipeline_hardening_self_monitoring_2026_06_22.md` is ARCHIVED, so per CLAUDE.md findings-triage this stays
      in the still-open issue doc that surfaced it rather than reopening an archived plan). (repo: deployment-service,
      unified-trading-pm)
- [x] ✅ [INFRA] P1. **Shipped `deployment-service@9c7a8ace`.** Added
      `deployment_service/data_pipeline_monitors/missing_live_producer_watcher.py` (DP-LIVE-003):
      `live_producer_prefixes()` selects every `vm_prefix_registry.VM_PREFIX_TO_BUCKET` entry with
      `lifecycle_class=LONG_LIVED_LIVE` EXCLUDING `umbrella=DeploymentUmbrella.PAPER` (the paper-only exclusion —
      `defi-paper-`/`strategy-paper-` are operator-started/stopped by design, not always-on producers);
      `check_missing_live_producers()` checks each surviving prefix against the full running-VM census (unfiltered by
      `is_data_vm` — `strategy-live-`/`greeks-compute-live-`/`defi-recursive-` aren't data VMs but ARE LONG_LIVED_LIVE
      producers) and pages CRITICAL once absent for `min_consecutive` sweeps (shared `MissTracker`, same grace-window
      discipline as every other meta-watcher probe — a short deliberate relaunch never false-pages). Reuses
      `DP_CRON_DID_NOT_FIRE` rather than a new UTL event (cross-repo) — same precedent as DP-FETCH-009 and
      `live_stream_watcher`'s DP-LIVE-001/002, all of which already reuse this event for "a thing that's supposed to
      keep existing isn't." Wired into `cli.py`'s `meta` sweep via `missing_live_producer_watcher.run_check(...)` (skips
      the check entirely — never pages — when the VM census is unavailable, e.g. a compute-API blip). Extracted the
      pre-existing inline `cron_targets` assembly out of `cli.py` into `meta_targets.cron_targets()` (pure move) to stay
      under the repo's 960-line file-size QG gate after the new wiring. 6 new unit tests in
      `tests/unit/test_missing_live_producer_watcher.py` (prefix selection, present/absent, consecutive-miss
      suppress-then-page, miss-counter reset on recovery, unavailable-census skip) — all green; full `quality-gates.sh`
      green on the committed SHA (301s local run). (repo: deployment-service)
