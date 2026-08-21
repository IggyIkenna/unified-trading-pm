---
doc_type: issue
title:
  DP-VM-001 exit_code=1 on mdps-tradfi-2026-20260810-034610 — mdps-tradfi- launcher family already at the 2/(prefix,day)
  relaunch bound, page instead of relaunch
summary: >-
  A data-pipeline fleet monitor (exit-code-aware,
  `deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py`) detected VM `mdps-tradfi-2026-20260810-034610`
  terminated with a durable non-zero `exit_code=1` (not 137/OOM) — the capture did not complete cleanly. Per DP-VM-001's
  own routing table (`/codex/05-infrastructure/data-pipeline-alerts.md`: "OOM: auto-recover (resize-up relaunch) then
  file issue · non-OOM: page"), a non-OOM nonzero exit is a PAGE case, not an auto-recover case, independent of any
  relaunch-count bound. The dispatching escalation additionally reported the `mdps-tradfi-` launcher-family had already
  hit the `≤2/(vm-prefix, day)` relaunch bound (RB-INFRA-RELAUNCH) earlier today, reinforcing that a further relaunch
  here would be a further blind retry, not new information. No prior issue doc named this specific VM. A near-identical
  sibling finding for `mdps-cefi-2019-20260810-043116` (same 2026-08-10 launch wave, different asset_group) was filed by
  another slot earlier the same day (`dp_vm_001_mdps_cefi_2019_exit_nonzero_relaunch_bound_page_2026_08_14.md`) — the
  reap list from 2026-08-11 also shows `mdps-cefi-2023-20260810-034610`, `mdps-defi-2025-20260810-034610`, and
  `mdps-defi-2026-20260810-034610` sharing this VM's exact `20260810-034610` launch timestamp across three other
  asset_groups, suggesting a shared fleet-launch batch with a possible common root cause worth checking across
  asset_groups, not just tradfi. This worker did NOT relaunch and did NOT diagnose the in-container root cause (no
  run.log content was pulled this session — see Progress Log); it files this doc and pages the operator per the
  escalation's explicit instruction.
status: open
nature: issue
asset_group: [tradfi]
stage: [meta]
repos: [deployment-service, market-data-processing-service]
scope: [engineer, admin]
tags: [dp-vm-001, exit-code-monitor, mdps-tradfi, relaunch-bound, page, data-pipeline-monitors]
related:
  [
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /plans/active/issues/dp_vm_001_mdps_cefi_2019_exit_nonzero_relaunch_bound_page_2026_08_14.md,
    /plans/active/issues/mdps_backfill_vm_fleet_wedged_mid_shutdown_and_monitor_blind_2026_08_11.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
  ]
context_scope:
  [
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    deployment-service/deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py,
    deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py,
    /plans/active/data_completion_tradfi_2026_07_15.md,
  ]
created: "2026-08-14"
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.2
assigned_role: devops
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  Escalation agt-01725f (wall_type=data_pipeline_failure, dispatched to slot 31, 2026-08-14) carried the finding
  directly — no separate audit CSV/candidate list was attached ("Filed issue: (none — alert carries the details)"). VM
  confirmed absent from the live fleet this session (`gcloud compute instances list
  --filter="name~mdps-tradfi-2026-20260810"` returned zero rows) — consistent with a terminated/self-deleted VM, not
  evidence of anything further.
---

# DP-VM-001 — mdps-tradfi-2026-20260810-034610 exit_code=1, relaunch-bound, page not relaunch

## What happened

- VM: `mdps-tradfi-2026-20260810-034610` (asset_group=tradfi, year-shard=2026, launcher-family prefix `mdps-tradfi-` →
  `launch-mdps-sharded-backfill.sh` per `launcher_registry.py`).
- Terminal state: `exit_code=1` (non-zero, non-OOM) — captured did not complete cleanly.
- The `mdps-tradfi-` launcher family had already used its `≤2/(vm-prefix, day)` relaunch allowance today per the
  dispatching monitor/escalation, per `RB-INFRA-RELAUNCH`'s bound.
- No issue doc previously named this VM. A sibling finding for `mdps-cefi-2019-20260810-043116` (same day, different
  asset_group) was filed earlier by another slot — same failure shape, same escalation class.
- **Possible shared-batch signal**: the 2026-08-11 VM reap list contains three OTHER VMs sharing this VM's exact
  `20260810-034610` launch timestamp: `mdps-cefi-2023-20260810-034610`, `mdps-defi-2025-20260810-034610`,
  `mdps-defi-2026-20260810-034610`. That four VMs across three asset_groups (cefi/defi/tradfi) launched at the identical
  second suggests a single fleet-launch batch, not independent per-shard launches — worth checking whether they share a
  common root cause (e.g. a bad tarball pin, a shared launcher-arg bug) rather than treating each as an isolated
  exit_code=1.

## Why this is a PAGE case, not a relaunch

`/codex/05-infrastructure/data-pipeline-alerts.md` DP-VM-001 routing: **"OOM: auto-recover (resize-up relaunch) then
file issue · non-OOM: page."** `exit_code=1` is not 137 — this was never eligible for blind auto-recover in the first
place, independent of the family's relaunch-count bound (which is additional, reinforcing evidence, not the primary
reason). `RB-INFRA-RELAUNCH`'s ≤2/day bound + "if it re-fails the SAME way twice... STOP relaunching, file an issue"
guidance both point the same direction: stop and page.

## What this worker did NOT do

- Did not relaunch `mdps-tradfi-2026-20260810-034610` or any other `mdps-tradfi-` VM.
- Did not pull `run.log` content for this VM (the VM is gone from the live fleet; a GCS SDK read of its archived
  `vm-logs/` blob would be the next diagnostic step for whoever picks this up — use
  `deployment_service.data_pipeline_monitors._gcs.read_text`/`read_terminal_exit_code`, never a subprocess
  `gsutil`/`gcloud storage` call, per the workspace GCS-object-ops hard rule).
- Did not diagnose the in-container root cause of the `exit_code=1` failure, and did not cross-check the sibling
  cefi/defi VMs sharing the same launch timestamp for a common cause — both are the actual open work this doc tracks.

## Recommended decision (for the operator)

1. Confirm whether the `mdps-tradfi-2026` shard's data is still outstanding (check the manifest for
   `asset_group=tradfi, year=2026` MDPS candle coverage) — if genuinely still missing, a relaunch is warranted but
   should wait for either (a) the family's daily bound to reset, or (b) a root-cause diagnosis of the `exit_code=1`
   failure first (the root-cause-diagnosed carve-out in `RB-INFRA-RELAUNCH` — "not blind retry... fix shipped... first
   attempt made WITH that fix live").
2. Pull `run.log` for `mdps-tradfi-2026-20260810-034610` AND the three same-timestamp sibling VMs (via the SDK helpers
   above) to identify whether they share one failure signature (exception, timeout, missing key, bad tarball pin) before
   any next relaunch attempt across any of the four asset_groups.

## Todos

- [ ] [OPERATOR] P1. Decide relaunch-vs-wait for `mdps-tradfi-2026-20260810-034610`'s shard (tradfi/2026 MDPS candles)
      per the recommended decision above; the `mdps-tradfi-` family relaunch bound is already exhausted for today.
- [x] ✅ [BACKEND] P2. **RESOLVED 2026-08-16 (slot 12, batch14 todo 2) — checkbox reconciled 2026-08-17 (finalize-plan
      review pass; the checkbox itself was left unflipped despite the Progress Log below already recording the
      finding — a checkbox-vs-prose gap, fixed here).** Pulled + read `run.log` for `mdps-tradfi-2026-20260810-034610`
      (5,841,296 lines): ZERO `No adapter for tradfi/<data_type>` occurrences — refutes the `mdps-tradfi-2021/-2023/
      -2025` stale-tarball hypothesis for this VM. Distinct root cause found instead: 109,853 occurrences of a missing
      `SchemaContract` for `asset_group='tradfi' instrument_type='OPTION' data_type='ohlcv_1s'/'ohlcv_1m'/'ohlcv_15m'
      venue='CME'`, cross-referenced into `data_completion_tradfi_2026_07_15.md`'s existing P3 live-re-verification
      todo. The three same-timestamp cefi/defi sibling VMs named in the original ask
      (`mdps-cefi-2023-20260810-034610`, `mdps-defi-2025-20260810-034610`, `mdps-defi-2026-20260810-034610`) were NOT
      pulled by batch14 (its cross-VM sweep scoped to the tradfi mdps-tradfi-/tradfi-bf- family only) — that
      cross-asset-group check remains genuinely unexplored; not re-opened as a new todo here since the na-eligibility-
      audit (2026-08-17) already assessed this todo's tradfi-scoped root-cause bar as met.

## Progress Log

- 2026-08-14 (slot 31, data_pipeline_failure escalation agt-01725f): Received escalation for DP-VM-001
  `mdps-tradfi-2026-20260810-034610` exit_code=1. Checked for an existing issue doc naming this VM — none found (grepped
  `plans/active/issues/*.md` for the VM name and `DP-VM-001`; found a same-day sibling finding for
  `mdps-cefi-2019-20260810-043116` filed by another slot, and confirmed via the 2026-08-11 VM reap list that three other
  VMs share this VM's exact `20260810-034610` launch timestamp across cefi/defi asset_groups). Confirmed via
  `gcloud compute instances list` the VM is no longer in the live fleet (0 rows). Per DP-VM-001's own routing table,
  non-OOM exit codes are a PAGE case regardless of relaunch-count bound, and the `mdps-tradfi-` family was additionally
  reported already at its `≤2/day` relaunch bound — did not relaunch. Filed this issue doc and paged the operator via
  `/blocked` per the escalation's explicit instruction. No code changed this session.

- **na-eligibility-audit 2026-08-16** (tradfi tranche, dispatch agt-45ad7b): **KEEP-NA, valid.** Sole open todo is an
  explicit [OPERATOR] relaunch-vs-wait judgment call (family relaunch bound exhausted, shard criticality unknown to
  a worker). Genuinely operator-gated. assigned_vm unchanged.
- **2026-08-16 (slot 12, batch14 todo 2 — cross-VM confirm/refute, closes the BACKEND diagnostic todo above).**
  Pulled this VM's `run.log` (5,841,296 lines) via `_gcs.read_text` and greped for `No adapter for tradfi/<data_type>`:
  **ZERO occurrences.** **REFUTED — this VM does NOT share the `mdps-tradfi-2021`/`-2023`/`-2025` stale-tarball root
  cause.** Distinct root cause found instead: **109,853** occurrences of
  `[CRITICAL] unknown error in market-data-processing-service.process_instrument_file: No SchemaContract registered
  for asset_group='tradfi' instrument_type='OPTION' data_type='ohlcv_1s'/'ohlcv_1m'/'ohlcv_15m' venue='CME'` across
  the run (dominant failure mode by far), plus one distinct, unrelated `DEPENDENCY CHECK FAILED` error for
  2026-08-06 (`Missing: instruments-service ... No data for 2026-08-06/tradfi`). This VM booted 2026-08-10, **six
  days before** `market-data-processing-service@2b2cc58ef3` (landed 2026-08-16) added `instrument_type=option` to
  `_INSTRUMENT_TYPES_EXCLUDED_FROM_COARSE_TIMEFRAMES` — but that exclusion only scopes `ohlcv_15m`/`ohlcv_24h`
  (COARSE timeframes); `ohlcv_1m`/`ohlcv_1s` are NOT covered, so this VM's `ohlcv_1m`/`ohlcv_1s` OPTION crashes are
  a **still-live gap post-fix too**, not fully explained by the fix's own scope. Noted this against the related P3
  live-re-verification todo in `/plans/active/data_completion_tradfi_2026_07_15.md` (same doc that already tracks
  the `2b2cc58ef3` verification) so the fine-timeframe gap isn't lost. Did not relaunch this VM or attempt a code
  fix — out of this todo's scope (confirm/refute the specific adapter hypothesis, not root-cause every VM from
  scratch); the `[OPERATOR]` relaunch-vs-wait decision above and the SchemaContract gap both remain open follow-ups.
**context-scout 2026-08-17**: populated/refreshed context_scope (4 entries)
- **na-eligibility-audit 2026-08-17** (tradfi tranche, dispatch agt-d99b5c): **KEEP-NA, valid.** Todo 1 (operator
  relaunch-vs-wait) stays genuinely gated. Todo 2 (BACKEND diagnostic): its root cause is now DONE (confirmed missing
  `tradfi`/`OPTION`/CME `SchemaContract` on fine timeframes) and cross-referenced into
  `data_completion_tradfi_2026_07_15.md`'s own live-re-verification todo — stale-duplicated-elsewhere, not an
  independent reclassify candidate; citation already present in this doc's own 2026-08-16 batch14 entry above.
  **Correction to the record**: the prior 2026-08-16 marker on this doc read "sole open todo" — this was a miscount
  (2 todos were open then too, both plain `- [ ] `, not an indentation/star-bullet edge case); flagging for
  corpus-hygiene awareness, not re-litigating the verdict itself (KEEP-NA was still correct either way).
  `assigned_vm` unchanged.
- **tradfi_satellite_ao_dispatch_batch14_2026_08_16_finalize review pass, 2026-08-17 (slot 20)**: found the BACKEND
  P2 todo's checkbox still `[ ]` despite the 2026-08-16 and 2026-08-17 Progress Log entries above both already
  declaring it done — a checkbox-vs-prose gap. Flipped `[x]` citing the same evidence already recorded above; no new
  diagnosis performed, no code changed.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
