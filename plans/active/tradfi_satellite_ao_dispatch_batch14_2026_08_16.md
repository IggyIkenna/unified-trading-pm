---
doc_type: plan
title: tradfi satellite AO dispatch batch 14 — underlying-rename delete-safety hardening + DP-VM-001 stale-tarball cross-VM confirm
summary: >-
  na-eligibility-audit (tradfi tranche, 2026-08-16) per-todo RECLASSIFY extraction. Two conflict-cleared, bounded items
  pulled out of NA docs that otherwise carry a mix of bounded and genuinely operator-gated work: (1) harden the
  short-code underlying-rename migration's size-only destination-exists check to a real content comparison
  (tradfi_underlying_rename_apply_size_only_verification_gap_2026_08_12.md todo 1); (2) pull run.log for the 4 other
  recent mdps-tradfi-/tradfi-bf- VMs to confirm/refute the stale-MDPS-tarball root cause already proven for
  mdps-tradfi-2021 — consolidates dp_vm_001_mdps_tradfi_2021_exit_nonzero_stale_tarball_rootcause_2026_08_16.md's own
  todo (which already named all 4 siblings) with dp_vm_001_mdps_tradfi_2023_exit_nonzero_relaunch_bound_page_2026_08_15.md's
  narrower ask for the same 2023 VM specifically, so the identical action isn't dispatched twice.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [tradfi, ao-dispatch, satellite-batch, delete-safety, dp-vm-001, stale-tarball, na-audit-extraction]
related:
  [
    /plans/active/issues/tradfi_underlying_rename_apply_size_only_verification_gap_2026_08_12.md,
    /plans/active/issues/dp_vm_001_mdps_tradfi_2021_exit_nonzero_stale_tarball_rootcause_2026_08_16.md,
    /plans/active/issues/dp_vm_001_mdps_tradfi_2023_exit_nonzero_relaunch_bound_page_2026_08_15.md,
    /plans/active/issues/dp_vm_001_mdps_tradfi_2025_exit_nonzero_page_2026_08_16.md,
    /plans/active/issues/dp_vm_001_mdps_tradfi_2026_exit_nonzero_relaunch_bound_page_2026_08_14.md,
    /plans/active/issues/dp_vm_001_tradfi_bf_cme_ohlcv_1m_es_2020_exit137_stall_relaunch_bound_page_2026_08_15.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.5
assigned_role: data_engineering
effort: max
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  na-eligibility-audit (tradfi tranche, dispatch agt-45ad7b, 2026-08-16) — per-todo RECLASSIFY_PER_TODO_SPLIT extraction
  (2026-08-10 fix: extraction is per-todo, not whole-doc). Both source docs otherwise carry genuinely operator-gated
  items (a real prod-bucket-delete launch decision; a VM-relaunch resource-spend decision) that stay assigned_vm: NA.
context_scope:
  [
    market-tick-data-service/market_tick_data_service/scripts/migrate_tradfi_underlying_display_names_2026_08.py,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/05-infrastructure/vm-tarball-deployment.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
---

# tradfi satellite AO dispatch batch 14

> Extracted from 2 NA docs by na-eligibility-audit's per-todo split path — each source doc keeps its remaining
> genuinely operator-gated item(s) and stays `assigned_vm: NA`; only the conflict-cleared bounded items below dispatch
> through this batch.

## Todos

- [ ] [SCRIPT] P1. Harden `_apply_one`'s destination-exists branch in
      `market-tick-data-service/market_tick_data_service/scripts/migrate_tradfi_underlying_display_names_2026_08.py`
      to do a real content/byte comparison (not size only) before deleting the short-code source object — mirror the
      compound-key content-comparison pattern already proven earlier in the same investigation for a similar
      duplicate-verification task (sort/compare on a stable row key, not a coarse size/row-count proxy). Repo:
      market-tick-data-service. Done when: the size-only check is replaced with a real content comparison, unit-tested,
      QG green. Source: `tradfi_underlying_rename_apply_size_only_verification_gap_2026_08_12.md` todo 1.
- [ ] [SCRIPT] P1. **Time-sensitive — vm-logs/ GCS objects age out on a 14-day retention window.** Pull `run.log` (via
      `deployment_service.data_pipeline_monitors._gcs.read_text`, UTL storage client — never subprocess
      `gsutil`/`gcloud storage`) for the 4 other recent `mdps-tradfi-`/`tradfi-bf-` VMs — `mdps-tradfi-2023-20260815-040118`,
      `mdps-tradfi-2025-20260815-020059`, the `mdps-tradfi-2026` shard, `tradfi-bf-cme-ohlcv-1m-es-2020` — and grep
      each for the same `ERROR [<data_type>] : No adapter for tradfi/<data_type>` pattern that
      `mdps-tradfi-2021-20260816-040255` showed (root-caused there to an unpinned/floating MDPS tarball fetched stale
      at boot, refreshed hours later). Confirm or refute the shared-root-cause hypothesis. Report findings back as a
      dated note in each of the 5 source docs' own Progress Log (2021's included). If confirmed shared, this converts
      "5-6 isolated pages" into "one incident, one fix" — flag the tarball-refresh-cadence gap
      (`/codex/05-infrastructure/vm-tarball-deployment.md` § "The tarball refresh cycle") as a new tracked todo if so.
      Done when: each of the 4 VMs' run.log is checked and its verdict (confirmed / refuted / log unavailable —
      retention expired) is recorded. Source: `dp_vm_001_mdps_tradfi_2021_exit_nonzero_stale_tarball_rootcause_2026_08_16.md`
      todo 2 (named all 4 siblings) — consolidates `dp_vm_001_mdps_tradfi_2023_exit_nonzero_relaunch_bound_page_2026_08_15.md`
      todo 1's narrower ask for the 2023 VM specifically, so the identical run.log pull isn't dispatched twice.
