---
doc_type: issue
title:
  DP-VM-001 exit_code=1 on mdps-tradfi-2025-20260815-020059 — non-OOM exit routes to page per DP-VM-001's own routing
  table, not relaunch (5th same-shape mdps-tradfi-/tradfi-bf- page in under 48h)
summary: >-
  A data-pipeline fleet monitor (exit-code-aware, `deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py`)
  detected VM `mdps-tradfi-2025-20260815-020059` terminated with a durable non-zero `exit_code=1` (not 137/OOM) — the
  capture did not complete cleanly. This worker's dispatch context carried a generic "RELAUNCH" instruction, but per
  DP-VM-001's own routing table (`/codex/05-infrastructure/data-pipeline-alerts.md`: "OOM: auto-recover (resize-up
  relaunch) then file issue · non-OOM: page"), a non-OOM nonzero exit is UNCONDITIONALLY a page case, independent of the
  relaunch-bound question — verified directly against the codex SSOT this session, not assumed from the dispatch
  wording. Confirmed via `gcloud compute instances list --filter="name~'^mdps-tradfi-'"` that only
  `mdps-tradfi-2021-20260815-175230` is currently RUNNING — the tradfi-2025 cell is not covered by a running VM, and the
  target VM itself is absent from the live fleet (terminated, consistent with the finding). This worker did NOT
  relaunch. This is the FIFTH same-shape non-OOM `mdps-tradfi-`/`tradfi-bf-` relaunch-bound-page doc in under 48h
  (2026-08-14 x2, 2026-08-15 x2, this one 2026-08-16) — reinforcing the prior recommendation that this pattern warrants a
  dedicated root-cause pass on the tradfi MDPS backfill launcher/adapter rather than continuing to treat each occurrence
  as an isolated page.
status: resolved
nature: issue
asset_group: [tradfi]
stage: [meta]
repos: [deployment-service, market-data-processing-service]
scope: [engineer, admin]
tags: [dp-vm-001, exit-code-monitor, mdps-tradfi, page, data-pipeline-monitors, recurring-pattern]
related:
  [
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /plans/archive/issues/dp_vm_001_mdps_tradfi_2023_exit_nonzero_relaunch_bound_page_2026_08_15.md,
    /plans/active/issues/dp_vm_001_mdps_tradfi_2026_exit_nonzero_relaunch_bound_page_2026_08_14.md,
    /plans/active/issues/dp_vm_001_tradfi_bf_cme_ohlcv_1m_es_2020_exit137_stall_relaunch_bound_page_2026_08_15.md,
    /plans/active/issues/dp_vm_001_tradfi_bf_cme_ohlcv_1m_g01_6a_6l_2020_exit137_stall_relaunch_bound_page_2026_08_15.md,
    /plans/active/issues/mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
  ]
context_scope: [/codex/15-runbooks/incidents/rb_infra_relaunch.md, /codex/05-infrastructure/data-pipeline-alerts.md, deployment-service/deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py, deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py]
created: "2026-08-16"
parent_epic: infrastructure_master
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
  Escalation agt-a55cdc (wall_type=data_pipeline_failure, dispatched to slot 6, 2026-08-16). Boot context named the
  finding + a "RELAUNCH" instruction directly ("Filed issue: (none — alert carries the details)"). This worker
  independently verified against `/codex/05-infrastructure/data-pipeline-alerts.md`'s DP-VM-001 routing table that a
  non-OOM `exit_code=1` routes to page, not relaunch, and confirmed the `deployment-service` fix for the mdps-* fleet
  duplicate-relaunch explosion (`4d96b24adb`) is present on `origin/live-defi-rollout` (not relevant to this page since
  no relaunch was dispatched, but checked before considering the relaunch path).
---

# DP-VM-001 — mdps-tradfi-2025-20260815-020059 exit_code=1, non-OOM, page not relaunch

## What happened

- VM: `mdps-tradfi-2025-20260815-020059` (asset_group=tradfi, year-shard=2025, launcher-family prefix `mdps-tradfi-` →
  `launch-mdps-sharded-backfill.sh` per `launcher_registry.py`).
- Terminal state: `exit_code=1` (non-zero, non-OOM) — captured did not complete cleanly.
- This worker's dispatch context said "RELAUNCH vm=mdps-tradfi-2025-20260815-020059 ... asset_group=tradfi" — but that
  instruction is generic dispatch boilerplate, not gated on the OOM-vs-non-OOM distinction. Read
  `/codex/05-infrastructure/data-pipeline-alerts.md`'s DP-VM-001 row directly this session: "OOM: auto-recover
  (resize-up relaunch) then file issue · non-OOM: page" — unconditional on exit code class, independent of any
  relaunch-count bound. `exit_code=1` is non-OOM (OOM is 137). Routing = **page**.
- Confirmed via `gcloud compute instances list --filter="name~'^mdps-tradfi-'"` that only
  `mdps-tradfi-2021-20260815-175230` is RUNNING — the tradfi-2025 cell is not currently covered by a running VM (not a
  duplicate-relaunch situation either way), and the target VM itself is absent (terminated).
- Also checked (before ruling out relaunch): `deployment-service`'s mdps-* fleet duplicate-relaunch-explosion fix
  (`4d96b24adb`, see `mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md`) IS present on
  `origin/live-defi-rollout` (`git merge-base --is-ancestor 4d96b24adb origin/live-defi-rollout` succeeded) — not
  actionable here since routing says page regardless, but recorded so a future reader doesn't have to re-derive it.
- No prior issue doc named this specific VM (grepped `plans/active/issues/` for `mdps-tradfi-2025-20260815-020059` and
  `mdps_tradfi_2025` — zero hits before this doc).
- **Recurring-pattern signal, now stronger**: this is the FIFTH `mdps-tradfi-`/`tradfi-bf-` non-OOM relaunch-bound-page
  doc in under 48h (2026-08-14 x2: `dp_vm_001_mdps_tradfi_2026_...`, `dp_vm_001_tradfi_bf_cme_ohlcv_1m_g01_6a_6l_2020_...`;
  2026-08-15 x2: `dp_vm_001_mdps_tradfi_2023_...`, `dp_vm_001_tradfi_bf_cme_ohlcv_1m_es_2020_...`; this doc,
  2026-08-16). Not diagnosed in this session either (no `run.log` pull this pass — mirrors the prior sibling docs'
  scoping) — flagged again, more strongly, for the operator / a devops-tagged follow-up.

## Per DP-VM-001's own routing table (`data-pipeline-alerts.md`)

> "OOM: auto-recover (resize-up relaunch) then file issue · non-OOM: page"

`exit_code=1` is non-OOM (not 137). Routing = **page**.

## What this worker did NOT do (scope of this session)

- Did NOT relaunch `mdps-tradfi-2025-20260815-020059` (non-OOM exit routes to page per DP-VM-001's own table).
- Did NOT pull `run.log` / `LAUNCH_PARAMS.json` / `PROGRESS.json` content to diagnose the in-container root cause — a
  deeper root-cause pass (why `exit_code=1`, which shard/date range, timeout vs adapter error vs schema issue) is
  follow-up work, same scoping as the four prior sibling docs.

## Todos

- [ ] [OPERATOR] P1. **Root-cause the recurring `mdps-tradfi-`/`tradfi-bf-` non-OOM `exit_code=1` pattern** — FIVE
      same-shape pages in under 48h (this doc + the four `related:` sibling docs above) with no `run.log` pull yet on
      any of them. Pull `run.log` for at least this VM (`mdps-tradfi-2025-20260815-020059`,
      `gs://deployment-scripts-<project>/vm-logs/mdps-tradfi-2025-20260815-020059/run.log`, via UTL's
      `download_from_storage`/`get_storage_client`, never subprocess `gsutil`), diagnose the shared root cause across
      the family, and fix it in the launcher/adapter. Was recommendation A in this doc's "Recommended decision"
      section (converted to a tracked todo per the workspace's "every follow-up is a `- [ ]` todo, never prose" hard
      rule) — was PAGED to the operator via `/api/slots/6/blocked` (`BLK-8dd12ae8`) but no answer surfaced before the
      orchestrator API became unreachable (see Progress Log); still needs an answer/action.

## Recommended decision

A: Operator (or a devops-role worker) pulls `run.log` for `mdps-tradfi-2025-20260815-020059`
(`gs://deployment-scripts-<project>/vm-logs/mdps-tradfi-2025-20260815-020059/run.log`, read via UTL's
`download_from_storage`/`get_storage_client`, never a subprocess `gsutil`), diagnoses the `exit_code=1` root cause
shared across the mdps-tradfi-/tradfi-bf- family, and fixes it in the launcher/adapter — closing the recurring page
class rather than continuing to accumulate isolated page docs. Given FIVE same-shape pages in under 48h, this is now a
high-confidence systemic signal, not noise.

B: Treat as an isolated one-off VM failure, let the next scheduled relaunch try again with no further diagnosis.

**Recommendation: A** — five same-shape non-OOM tradfi pages in under 48h is a strong pattern; a root-cause pass on the
shared launcher/adapter code path is now clearly cheaper than continuing to burn escalation-worker time paging the same
class of failure repeatedly.

## Progress Log

- 2026-08-16: Filed by slot-6 data_pipeline_failure escalation worker (escalation agt-a55cdc). Verified DP-VM-001's
  routing table directly against the codex SSOT (non-OOM → page, unconditional). Confirmed VM absent from live fleet,
  no cell-coverage conflict, no prior issue doc for this VM. Confirmed the mdps-* fleet-duplicate-relaunch-explosion fix
  is live on `origin/live-defi-rollout` (not actionable here, recorded for future readers). Did not relaunch. Did not
  pull `run.log` (deferred, same scoping as the four prior sibling docs). Paged via `/api/slots/6/blocked`
  (`BLK-8dd12ae8`) with options A (devops root-cause pass, recommended) / B (isolated, no action). Polled
  `/api/slots/6/messages` for ~115s (the role's 2-min bound) — no answer surfaced via the API despite a session
  system-reminder stating "Operator answered your BLOCKED question — check your messages now" (checked twice more
  immediately after that reminder, still empty); `:8765` then became fully unreachable
  (`curl: (7) Failed to connect`), matching the SAME known-unreliable-orchestrator-connectivity pattern the
  `dp_vm_001_mdps_tradfi_2023_...` sibling doc hit yesterday. Per the role's 2-min-no-answer rule, stopped polling —
  this doc is the durable page artifact; a later operator answer (if it lands out-of-band) should be appended here
  rather than assumed lost.
- 2026-08-16 (later same day): a sixth same-shape occurrence (`mdps-tradfi-2021-20260816-040255`, escalation
  agt-ef6b00, slot 20) pulled the full `run.log` this doc's own todo asked for — see
  `/plans/active/issues/dp_vm_001_mdps_tradfi_2021_exit_nonzero_stale_tarball_rootcause_2026_08_16.md`. Root-caused to
  a STALE `market-data-processing-service` tarball (a floating/unpinned launch fetched a build that predated the
  long-since-landed `2dcccb85` ohlcv adapter registrations; the tarball has since been rebuilt fresh). Offered as the
  leading hypothesis for this doc's own `mdps-tradfi-2025` occurrence too, not yet directly confirmed for it
  specifically — that new doc's own follow-up todo covers checking this and the other sibling VMs before their
  `vm-logs/` GCS objects age out of the 14-day retention window.
- **na-eligibility-audit 2026-08-16** (tradfi tranche, dispatch agt-45ad7b): **KEEP-NA, valid.** Sole open todo is an
  explicit `[OPERATOR]` root-cause-and-decide judgment call; the mechanical confirm-for-2025 half is now tracked via
  `tradfi_satellite_ao_dispatch_batch14_2026_08_16.md` (this run's own extraction from the 2021 sibling doc).
  `assigned_vm` unchanged.
- **2026-08-16 (slot 12, batch14 todo 2 — cross-VM confirm/refute, closes the mechanical half of the open todo
  above).** Pulled this VM's `run.log` (4,742,244 lines) via `_gcs.read_text` and greped for
  `No adapter for tradfi/<data_type>`: **2518 occurrences** (ohlcv_1m + ohlcv_1s; first at 2026-08-15 02:12:01
  ohlcv_1s, last at 23:55:05 ohlcv_1m), same terminal `rc=1`/`DEPLOYMENT_FAILED` shape as `mdps-tradfi-2021`/`-2023`.
  **CONFIRMED — shares the stale-tarball root cause.** 3 of the 5-6 same-shape pages (2021, 2023, this one) now
  share one root cause, already self-resolved by the routine tarball rebuild; the remaining open work is the
  tarball-refresh-cadence P2 todo tracked in the `mdps-tradfi-2021` sibling doc, not a per-VM fix. The still-open
  `[OPERATOR]` todo above (root-cause-and-decide) is now answerable with this evidence — leaving the checkbox as-is
  since the decide half is still genuinely operator-gated, but the root-cause half is DONE. Full cross-VM roundup
  (incl. the 2 refuted VMs) recorded in the 2021 sibling doc's Progress Log.

- **na-eligibility-audit 2026-08-17 (tradfi tranche, dispatch agt-d99b5c) — ARCHIVE.** This doc's purpose (page +
  diagnose `mdps-tradfi-2025-20260815-020059`'s `exit_code=1` failure) is fulfilled: root cause confirmed (stale
  MDPS tarball, self-resolved by the routine 2026-08-16 11:06 rebuild) and the sole remaining substantive
  work — preventing recurrence via a tarball-refresh-cadence policy change — is tracked as its own design-gated
  item in the sibling `dp_vm_001_mdps_tradfi_2021_exit_nonzero_stale_tarball_rootcause_2026_08_16.md` doc, not
  unique to this VM. `status: resolved` above; archiving per the standard 6-step ritual (`doc_type: issue` →
  flat `plans/archive/issues/` per `issue-doc-lifecycle.md`'s 2026-08-16 ruling). Referrers fixed: the 2 still-active
  ones (`dp_vm_001_mdps_tradfi_2021_...md`, `tradfi_satellite_ao_dispatch_batch14_2026_08_16_finalize.md`); the 2
  already-archived referrers are left untouched as frozen historical record (fact-vs-path convention).
**context-scout 2026-08-17**: populated/refreshed context_scope (4 entries)
