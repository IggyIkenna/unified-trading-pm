---
doc_type: plan
title: Re-verify DeFi instruments-store _index v9 GATE C is still accurate before any --apply-write (operator-ruled 2026-08-16)
summary: >-
  Operator asked to dispatch the DeFi instruments-store `_index` v9 `--apply` walk
  (master_data_canonicalisation_migration_catalogue_2026_06_07.md slot-2, distinct from the already-applied MTDS
  raw-tick v9 walk). Operator explicitly asked to confirm accuracy and adjust for the latest code first, given
  the doc is old and may need merges/tweaks — NOT a blind apply. This is a multi-gate migration (GATE C:
  instruments-store-defi _index must be v9-canonical, currently 0% v9 as of the 2026-08-12 /plan-reconcile
  correction; AND defi instrument_availability/by_date/ must be populated in the -prd bucket, currently empty) —
  and Big Finding #1 from the na-eligibility-audit (defi_migration_dedicated_bucket_architecture_retired_2026_08_14.md)
  found a SIBLING defi doc's bucket-architecture premise had gone stale without anyone noticing, so this doc's
  premise needs the same fresh-read treatment before trusting its gates. Scoping this dispatch to
  RE-VERIFICATION ONLY — confirm current GATE C status against live code/data, and flag if the doc's
  architecture assumptions have drifted — NOT the --apply-write itself, which stays gated on both prerequisites
  clearing for real.
status: resolved
nature: process
asset_group: [defi]
stage: [data]
repos: [instruments-service, market-tick-data-service]
scope: [engineer]
tags: [defi, v9, canonicalization, gate-c, reverify]
related:
  [
    /plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md,
    /plans/active/defi_migration_audit_log_2026_07_24.md,
    /plans/active/issues/defi_migration_dedicated_bucket_architecture_retired_2026_08_14.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.5
assigned_role: data_engineering
effort: max
drift_direction: none
depends_on: []
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A round 10, 2026-08-16 — operator asked to confirm accuracy + adjust for latest code before dispatching"
locked_by:
context_scope:
  [
    /plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md,
    /plans/active/defi_migration_audit_log_2026_07_24.md,
    /plans/active/issues/defi_migration_dedicated_bucket_architecture_retired_2026_08_14.md,
  ]
locked_since:
resolved_by: slot-13, 2026-08-16
---

> **🟢 RESOLVED + ARCHIVED 2026-08-16.** GATE C re-verified against live code/data: the on-disk `_index` is now
> 100% schema_version=9 (organic consolidator convergence, not the explicit migration, which has never run) with
> a residual 12% data-quality delta; `instrument_availability/by_date/` is populated but its capture cron is
> stale 21 days (new issue filed). Findings written into `master_data_canonicalisation_migration_catalogue_2026_06_07.md`
> and `defi_migration_audit_log_2026_07_24.md`. Follow-on work: `/plans/active/defi_instruments_store_v9_gate_c_apply_write_2026_08_16.md`
> (the explicit `--apply-write`, draft/operator-gated) and `/plans/active/issues/defi_by_date_capture_cron_stale_2026_08_16.md`
> (the capture-cron staleness). This plan's own single todo is done; no further action here.

# Re-verify DeFi instruments-store _index v9 GATE C before any --apply-write

## Todos

- [x] ✅ [DIAG] P1. **Re-verify GATE C's current status against live code/data — DONE 2026-08-16 (slot-13).**
      (1) `instruments-store-defi` `_index` schema_version — **NO LONGER 0% v9**: fresh live read
      (`migrate_instruments_store_v9.py --asset-group defi --skip-objects`, dry-run, `instruments-service`
      at `3a8079ee`) shows **100% schema_version=9 on disk today (138,612 rows, v8_before=0, v9_before=138612)**
      — up from the 2026-08-12 measurement of 125,242 v8 rows / 0% v9. Object `last_modified=2026-08-16T22:01:20Z`.
      Root-caused (see the new issue doc below): this is **NOT** the explicit one-time
      `migrate_instruments_store_v9.py --apply` migration (never run — confirmed via git log, this doc's own
      still-open state until today, and the archived `defi_manifest_index_catastrophic_shrink_2026_08_16.md`
      investigation's 40+-hour Cloud Run execution-log trace showing `rows_out` stably ~138.5k since 2026-08-15).
      It's **organic convergence via the routine hourly `uts-prod-manifest-consolidator-instruments-defi` cron**:
      ordinary live capture writes already stamp `schema_version=9` natively (have since the G0 source-aware
      writer landed 2026-06-16), and the consolidator's UNION-ALL merge drops stale null-`capture_status` v8
      placeholder rows over cycles — so the manifest self-healed to v9-canonical without the explicit backfill
      ever running. **Residual**: the dry-run's own transform still reports `data_type_set: 16750` (12% of rows)
      — a real, smaller data-quality delta the explicit `--apply` would still correct; NOT a full no-op.
      (2) `defi instrument_availability/by_date/` in the `-prd` bucket — **NOT empty**: 78,449 rows already
      rolled into the catalogue (`build_instrument_catalogue --asset-group defi --dry-run --max-blobs 5`,
      monotonic guard ACCEPTED, current=78,449 > 78,445). **New finding**: the catalogue builder itself flags
      `CATALOGUE_STALE_BY_DATE — newest by_date day is 2026-07-26 (21d old) — upstream download cron unhealthy`
      — the raw DeFi IS capture pipeline appears to have STALLED ~3 weeks ago, a genuine, separate data-pipeline
      health issue. Filed as `/plans/active/issues/defi_by_date_capture_cron_stale_2026_08_16.md` (P1).
      (3) Architecture cross-check: CONFIRMED still accurate — `instruments-store` is a separate bucket `kind`
      from the `market-data`/`tick-data` family the dedicated-bucket-retirement issue doc covers; GATE C's target
      bucket (`instruments-store-defi-prd-{pid}`) is unaffected, still live/provisioned, no retirement marker.
      (4) Given the residual 12% `data_type_set` delta and the still-un-run explicit migration, filed the
      follow-on `--apply-write` plan per this todo's own instruction:
      `/plans/active/defi_instruments_store_v9_gate_c_apply_write_2026_08_16.md` (status: draft, `[OPERATOR]`-gated
      on the actual write — NOT fired from this dispatch). Findings written into
      `master_data_canonicalisation_migration_catalogue_2026_06_07.md`'s slot-2 row + Gate-State Board, and
      `defi_migration_audit_log_2026_07_24.md` GATE C section (both same-turn). Repos: instruments-service,
      market-tick-data-service (read-only dry-runs only, no code changed).

## Progress Log

- **2026-08-16 (na-eligibility-audit follow-up Q&A round 10, operator ruling — scoped)**: operator asked to
  dispatch the v9 walk, with an explicit caution to confirm accuracy against latest code first (doc is old,
  might need merges/tweaks). Scoped to re-verification only, given Big Finding #1's precedent of a sibling defi
  doc's architecture premise having silently gone stale.
- **2026-08-16 (slot-13, re-verify complete)**: live-measured both gates — schema_version is now 100% v9
  on-disk (organic consolidator convergence, not the explicit migration) and by_date is populated (not empty,
  but its upstream capture cron is stale 21 days — new issue filed). Architecture assumptions hold. Filed the
  follow-on `--apply-write` plan (draft, operator-gated) and the capture-staleness issue doc. All todos done —
  archiving this plan per the archival discipline hard rule.
