---
doc_type: issue
title:
  DP-VM-001 exit_code=1 on mdps-defi-2026-20260815-040833 — root cause is a CONSOLIDATOR_LOCK_TTL_SECONDS (9000s) vs
  staleness-alert budget (3600s) mismatch for market-data-tick-defi-prd, causing recurring FALSE CONSOLIDATOR_DOWN
  during legitimate long merges — page not relaunch (already 2/2 relaunch bound for this launcher-family today)
summary: >-
  A data-pipeline fleet monitor (exit-code-aware, `deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py`)
  detected VM `mdps-defi-2026-20260815-040833` terminated with durable non-zero `exit_code=1` (not 137/OOM). Per
  DP-VM-001's own routing table (`/codex/05-infrastructure/data-pipeline-alerts.md`: "OOM: auto-recover then file
  issue · non-OOM: page") this is a page case; the boot context additionally noted `mdps-defi-` had already hit its
  2/2 relaunch-dispatch bound for today (RB-INFRA-RELAUNCH), so this worker did NOT relaunch and instead diagnosed the
  in-container root cause via the GCS SDK (`_gcs.read_text`/`read_terminal_exit_code`, never subprocess
  `gsutil`/`gcloud storage`).

  `run.log` (via `_gcs.RUN_LOG_BLOB`) shows the VM processed 227 dates (2026-01-01..2026-08-15) cleanly, then failed
  ONLY the final in-window date (2026-08-14) with: `ERROR Error processing defi: Manifest consolidator appears DOWN
  for bucket='market-data-tick-defi-prd-central-element-323112': consolidated _index/availability_index.parquet
  heartbeat is 5314s old (> 3600s budget)`, which flipped the handler's overall exit code to 1.

  Live investigation (this session, ~20:05Z) found the consolidator is NOT actually down — it is a MISCONFIGURED
  false-positive:
  - The Cloud Scheduler job `uts-prod-manifest-consolidator-market-data-defi-cron` is `ENABLED` (re-enabled
    2026-08-12T19:02:58Z, after the 2026-08-07 canonical-migration pause documented in
    `/plans/active/issues/defi_consolidator_paused_by_inflight_rebuild_vm_2026_08_07.md` — that earlier incident is
    CLOSED/resolved, this is a genuinely new/distinct occurrence).
  - The Cloud Run job `uts-prod-manifest-consolidator-market-data-defi` IS firing every ~60s and reports
    `Execution completed successfully` every time (confirmed via `gcloud run jobs executions list`).
  - Cloud Logging for those "successful" executions shows every single cycle is a NO-OP:
    `ManifestConsolidator: skipping cycle for bucket=market-data-tick-defi-prd-central-element-323112 — fresh lock
    present (sibling cron still running)` / `success=True shards=0 rows_in=0 rows_out=0 ... error=locked`.
  - The live lock blob (`_index/consolidator.lock`) reads `{"started_at": "2026-08-15T19:40:49.184965+00:00",
    "instance": "1-9a9786a2"}` — a single instance legitimately holding the merge lock for an extended run.
  - The Cloud Run job's own env carries `CONSOLIDATOR_LOCK_TTL_SECONDS=9000` (2.5h) — a deliberate per-bucket override
    in `unified_trading_library/manifest_consolidator.py` (`_LOCK_TTL_SECONDS`, "a bucket whose merges legitimately
    run longer than the 300s default") acknowledging this bucket's merges can legitimately run up to 9000s.
  - BUT the downstream staleness-alert budget that both the VM's own preflight check AND (very likely, not
    independently re-verified this session — see Open question below) the fleet CONSOLIDATOR_DOWN monitor apply to
    `_index/availability_index.parquet` freshness is hardcoded at **3600s (1h)** — well BELOW the bucket's own
    9000s legitimate-merge TTL. Every VM/monitor that checks this bucket's manifest freshness during a legitimate
    long merge (which, per the TTL override, can run up to 2.5h) will see a false `CONSOLIDATOR_DOWN` for up to
    ~1.5h of every such merge, even though the consolidator is healthy and actively working (not stalled — lock
    `started_at` is fresh, cycles ARE firing every minute, and the 2026-08-05 stale-lock-detection safety net
    (`defi_manifest_consolidator_stale_lock_silent_stall_2026_08_05.md`, `_check_stall_on_lock_skip`) correctly does
    NOT fire because the lock genuinely isn't stale).
  - `_index/availability_index.parquet` itself is currently 120 min stale (checked live this session) — consistent
    with an in-progress legitimate merge, not a genuine stall.

  This is the SAME underlying budget-vs-TTL class as the two related open docs below (both about
  `market-data-tick-defi-prd` CONSOLIDATOR_DOWN false-positives), but pins down a THIRD, more precise root cause:
  a hardcoded 3600s staleness-alert budget that was never raised to match this bucket's own
  `CONSOLIDATOR_LOCK_TTL_SECONDS=9000` override. Every VM/monitor recheck during this bucket's routine long merges
  will keep re-triggering non-OOM exit_code=1 DP-VM-001 pages until the budget is aligned (or the TTL is lowered, if
  9000s is no longer actually needed).

  NOT fixed inline (out of one-shot escalation scope — the fix requires deciding/aligning the correct staleness
  budget for this specific bucket across every consumer of it, a cross-cutting change touching the VM preflight
  check and the fleet monitor, not a single-file root-cause patch): filed as a tracked issue + paged the operator,
  per the DP-VM-001 non-OOM routing table and this session's explicit boot directive (relaunch bound already hit
  2/2 for `mdps-defi-` today — do not relaunch, check for an existing issue, page instead).
status: open
nature: issue
asset_group: [defi, meta]
stage: [data]
repos: [market-tick-data-service, deployment-service, unified-trading-library]
scope: [engineer, admin]
tags:
  [dp-vm-001, exit-code-monitor, mdps-defi, manifest-consolidator, lock-ttl, staleness-budget-mismatch, false-alarm,
   page, data-pipeline-monitors]
related:
  [
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /plans/active/issues/defi_consolidator_paused_by_inflight_rebuild_vm_2026_08_07.md,
    /plans/archive/issues/defi_lst_yields_backfill_blocked_manifest_consolidator_and_hyperliquid_perp_funding_gap_2026_08_08.md,
    /plans/active/issues/dp_vm_001_mdps_defi_2022_exit_nonzero_singledate_hang_2026_08_15.md,
  ]
context_scope:
  [
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    unified-trading-library/unified_trading_library/manifest_consolidator.py,
    deployment-service/deployment_service/data_pipeline_monitors/_gcs.py,
  ]
created: "2026-08-15"
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.4
assigned_role: devops
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  Escalation agt-24861c (wall_type=data_pipeline_failure, dispatched to slot 30, 2026-08-15) — client context carried
  vm_name=mdps-defi-2026-20260815-040833, event=DP_VM_EXIT_NONZERO (DP-VM-001), no attached candidate CSV ("Filed
  issue: none — alert carries the details"), plus an explicit relaunch-bound directive: `mdps-defi-` already hit
  2/2 relaunch dispatches today, do not relaunch again, check for an existing open issue and page the operator
  instead. VM confirmed absent from the live fleet this session (self-deleted per `VM_SHUTDOWN_ON_COMPLETION=true`,
  `run.log` tail). `run.log`/exit-code pulled via `deployment_service.data_pipeline_monitors._gcs`/`_gcs_tail`
  (SDK, never subprocess `gsutil`/`gcloud storage`). Consolidator live state (scheduler, Cloud Run job executions +
  logs, lock blob, env) checked live via `gcloud scheduler jobs describe` / `gcloud run jobs executions list` /
  `gcloud logging read` (read-only, no destructive verbs) + the storage-client `download_bytes` SDK path.
---

# DP-VM-001 — mdps-defi-2026-20260815-040833 exit_code=1, consolidator lock-TTL vs staleness-budget mismatch, page

## What happened

- VM `mdps-defi-2026-20260815-040833` ran the defi MDPS incremental candle pass over 2026-01-01..2026-08-15 (227
  dates), completed 226/227 dates cleanly, then failed the last date (2026-08-14) because its preflight dependency
  check saw `market-data-tick-defi-prd-central-element-323112`'s consolidated manifest as stale
  (`heartbeat is 5314s old (> 3600s budget)`) and refused to proceed — correctly conservative (it did NOT fall back
  to a per-VM OOM-risk merge, per the error's own remediation text), but the overall handler exit code flipped to 1,
  triggering this DP-VM-001 page.
- The consolidator is NOT down. It is mid a legitimate long-running merge: Cloud Scheduler `ENABLED`, Cloud Run job
  firing every ~60s and reporting `success=True`, but every cycle is a lock-contention no-op
  (`shards=0 rows_in=0 rows_out=0 error=locked`) because instance `1-9a9786a2` acquired the merge lock at
  `2026-08-15T19:40:49Z` and — per this bucket's own `CONSOLIDATOR_LOCK_TTL_SECONDS=9000` env override — is entitled
  to hold it for up to 2.5h before any other instance/the stale-lock safety net would reclaim it.
- The bug: the staleness-alert budget that VMs (and, presumptively, the fleet CONSOLIDATOR_DOWN monitor — not
  independently re-verified this session) apply to `_index/availability_index.parquet` freshness is a flat 3600s,
  never raised to match this bucket's own 9000s TTL override. Every legitimately-long merge on this bucket will
  produce up to ~1.5h of false `CONSOLIDATOR_DOWN`/non-OOM-exit-1 pages.

## Why not fixed inline / why paged instead of relaunched

- Boot directive explicitly said do not relaunch `mdps-defi-2026-20260815-040833` (2/2 relaunch bound already hit
  today for the `mdps-defi-` launcher family) — and a relaunch would not help anyway: the VM already correctly
  self-deleted after a clean 226/227-date run; relaunching would just re-hit the SAME stale-manifest preflight
  refusal until the in-progress merge finishes.
- The actual fix (deciding + aligning the correct staleness budget for THIS bucket across every consumer — the MDPS
  preflight check, the fleet monitor, and any other reader of `availability_index.parquet` freshness) is a
  cross-cutting, multi-consumer change, not a single-file root-cause patch a one-shot escalation worker should guess
  at. Filed here + paging per the DP-VM-001 non-OOM routing table.

## Recommended decision (for whoever picks this up)

Align the two numbers for `market-data-tick-defi-prd` specifically — either:

- **A** (recommended): raise the staleness-alert budget consumers apply to this bucket's manifest freshness to
  `>= CONSOLIDATOR_LOCK_TTL_SECONDS` (9000s) for this bucket, so a legitimate long merge is never misread as down; or
- **B**: if 9000s is no longer actually needed for this bucket's current shard volume, lower
  `CONSOLIDATOR_LOCK_TTL_SECONDS` back toward the 300s default and re-verify merges still complete within it.

Either requires re-checking `defi_consolidator_paused_by_inflight_rebuild_vm_2026_08_07.md` and
`defi_lst_yields_backfill_blocked_manifest_consolidator_and_hyperliquid_perp_funding_gap_2026_08_08.md` for whether
they're the SAME budget-mismatch class (they predate this session's TTL-override discovery) and can be closed
together once the real fix lands.

## Todos

- [ ] [BACKEND] P1. Align the staleness-alert budget every consumer applies to `market-data-tick-defi-prd`'s manifest
      freshness with its `CONSOLIDATOR_LOCK_TTL_SECONDS=9000` override — either (A, recommended) raise the
      staleness-alert budget for this bucket to `>= 9000s` across every consumer (the MDPS preflight check, the fleet
      CONSOLIDATOR_DOWN monitor, and any other reader of `availability_index.parquet` freshness), or (B) if 9000s is no
      longer needed for this bucket's current shard volume, lower `CONSOLIDATOR_LOCK_TTL_SECONDS` back toward the 300s
      default and re-verify merges still complete within it. Repos: deployment-service, unified-trading-library.
- [ ] [DATA] P2. Re-check `defi_consolidator_paused_by_inflight_rebuild_vm_2026_08_07.md` and
      `defi_lst_yields_backfill_blocked_manifest_consolidator_and_hyperliquid_perp_funding_gap_2026_08_08.md` for
      whether they're the SAME budget-mismatch class (both predate this doc's TTL-override discovery) — close together
      with the fix above if so.

## Progress Log

- 2026-08-15: Filed by escalation agt-24861c (slot 30). Diagnosed root cause live (scheduler/job/lock/env, GCS SDK
  reads only). Paged operator per DP-VM-001 non-OOM routing table + boot directive. Not fixed inline (cross-cutting
  budget decision, out of one-shot scope).
- **2026-08-16 (plan_reconciler, defi tranche, dispatch agt-1a88e0)**: converted this doc's prose "Recommended decision"
  into tracked checkboxes (Phase 2 zero-checkbox-doc sweep) — it previously contributed zero dispatchable work despite
  `assigned_vm: planning`.
- **na-eligibility-audit 2026-08-16** [body-hash:a6972d17406fe69b]: KEEP-NA, valid — Live operational escalation doc (filed 2026-08-15), correctly in scope -- no na-eligibility-audit marker exists yet; a same-day 2026-08-16 plan_reconciler Progress Log entry only converted prose into checkboxes (Phase 2 zero-checkbox-doc sweep), it is not a na-eligibility-audit verdict marker.
**context-scout 2026-08-17**: populated/refreshed context_scope (4 entries)
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)
