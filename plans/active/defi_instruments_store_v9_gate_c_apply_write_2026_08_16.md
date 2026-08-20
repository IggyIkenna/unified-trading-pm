---
doc_type: plan
title: DeFi instruments-store _index v9 GATE C — explicit --apply-write (follow-on, operator-gated)
summary: >-
  Follow-on to defi_instruments_store_v9_gate_c_reverify_ao_dispatch_2026_08_16.md (archived), which re-verified
  GATE C against live code/data and found the on-disk `instruments-store-defi` `_index` is now 100%
  schema_version=9 (138,612 rows) — but via ORGANIC convergence through the routine hourly manifest-consolidator
  cron, NOT the explicit one-time `migrate_instruments_store_v9.py --apply` migration, which has never been run.
  The dry-run transform still reports a residual `data_type_set: 16,750`/138,612-row (12%) data-quality delta the
  explicit migration would still correct, and the §H doubled-`day=` object-path migration gate (tracked
  separately in defi_migration_audit_log_2026_07_24.md) is unaffected by this finding. This plan tracks the
  actual `--apply-write` decision + execution — status draft until the operator authorizes firing it, per the
  reverify dispatch's own instruction ("file... as a new, separately-authorized follow-on plan, do not fire it").
status: draft
nature: process
asset_group: [defi]
stage: [data]
repos: [instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags: [defi, v9, canonicalization, gate-c, apply-write, operator-gated]
related:
  [
    /plans/archive/2026_08/defi_instruments_store_v9_gate_c_reverify_ao_dispatch_2026_08_16.md,
    /plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md,
    /plans/active/defi_migration_audit_log_2026_07_24.md,
    /plans/archive/issues/defi_by_date_capture_cron_stale_2026_08_16.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: manifest_master # was: defi_master (epic-assignment audit 2026-08-19) -- executes the shared cross-AG
  # v9 manifest-schema migration (migrate_instruments_store_v9.py, tracked in the cross-AG
  # master_data_canonicalisation_migration_catalogue), just scoped to defi's corpus -- same script/gate runs per-AG
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 0.64
assigned_role: data_engineering
effort: max
drift_direction: none
depends_on: [] # was [defi_by_date_capture_cron_stale_2026_08_16] — cleared 2026-08-18 (plan_reconciler): that
  # issue was archived 2026-08-16 as a false positive (see this doc's own body § "Why this is status: draft" (b)),
  # so the target no longer exists; depends_on here was always informational context per the 2026-08-17
  # plan_reconciler finding, not a machine gate
supersedes:
superseded_by:
source: >-
  defi_instruments_store_v9_gate_c_reverify_ao_dispatch_2026_08_16.md todo item 4 ("if both gates measure clear
  AND architecture assumptions hold, file the actual --apply-write as a new, separately-authorized follow-on
  plan — do not fire it from this dispatch").
locked_by:
context_scope:
  [
    /plans/active/defi_migration_audit_log_2026_07_24.md,
    /plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md,
    /plans/archive/issues/defi_by_date_capture_cron_stale_2026_08_16.md,
    instruments-service/scripts/migrate_instruments_store_v9.py,
  ]
locked_since:
resolved_by:
---

# DeFi instruments-store _index v9 GATE C — explicit --apply-write

## Why this is `status: draft`, not `active`

The reverify dispatch found GATE C's headline criterion (schema_version=9) already true on disk today — but via
routine writes, not the migration this plan would run. Firing `--apply` now would run against a manifest that
is ALREADY 88% clean by the migrator's own accounting, which changes the risk/reward calculus from the original
plan's premise (a 100%-v8, fully-dirty corpus). Before this plan is promoted to `active` and its `--apply` todo
dispatched, the operator should confirm: (a) is the residual 12% delta (`data_type_set`) still worth a
whole-corpus `--apply` walk, or small enough to fix a narrower way; (b) **RESOLVED 2026-08-16 (slot-32)**: the
sibling by_date-capture-cron issue (`/plans/archive/issues/defi_by_date_capture_cron_stale_2026_08_16.md`) was a
false positive — the job was never down, so there is no pending "resumption" to wait on; (c) re-run the dry-run
fresh immediately before firing, since this corpus is evidently still moving under routine writes (do not trust
the 2026-08-16 numbers in this doc as still-current by the time this plan is picked up).

## Todos

- [ ] [DIAG] P2. **Pre-flight**: immediately before firing `--apply`, re-run
      `migrate_instruments_store_v9.py --asset-group defi --skip-objects` (dry-run) fresh and confirm the
      schema_version / `data_type_set` numbers haven't materially changed from this doc's 2026-08-16 baseline
      (138,612 rows, 100% v9, 16,750 `data_type_set` delta) — the corpus is under active routine writes, so a
      stale baseline risks the same "0% v9" mistake this plan's parent dispatch caught. Repo: instruments-service.
- [ ] [OPERATOR] P1. **Fire the explicit `--apply` write**: `migrate_instruments_store_v9.py --asset-group defi
      --apply`, on a VM/tarball per the master coordinator's standard `--apply` runbook (in-region, not the
      shared planning host — this is a whole-corpus write). Rollback = `pre_migration_2026_06_08.parquet`
      snapshot (already staged per the master coordinator doc). This closes the residual 12% `data_type_set`
      delta and makes the `_index` state deliberate/verified rather than an incidental byproduct of routine
      writes. Requires explicit operator authorization to dispatch (irreversible single-walk over prod data,
      per CLAUDE.md's hard-stop list). Repos: instruments-service + market-tick-data-service.
- [ ] [DIAG] P2. **Post-apply verification**: re-run the dry-run once more post-`--apply` and confirm
      `v8_before=0` AND `data_type_set` has dropped to 0 (the residual delta this plan exists to close). Report
      the verdict into `defi_migration_audit_log_2026_07_24.md` GATE C section + flip the master coordinator's
      Gate-State Board defi G4 cell if this was the last blocking GATE. Repo: instruments-service.

## Progress Log

- **2026-08-16 (slot-13, filed per reverify dispatch todo item 4)**: created as `status: draft` — the reverify
  found both of GATE C's original blocking conditions no longer hold as literally stated, but a residual 12%
  data-quality delta remains and the explicit migration has never run, so this plan tracks that closure without
  auto-firing the irreversible `--apply` write. See
  `/plans/archive/2026_08/defi_instruments_store_v9_gate_c_reverify_ao_dispatch_2026_08_16.md` for the full
  live-measurement evidence this plan is based on.
