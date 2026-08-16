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
status: active
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
resolved_by:
---

# Re-verify DeFi instruments-store _index v9 GATE C before any --apply-write

## Todos

- [ ] [DIAG] P1. **Re-verify GATE C's current status against live code/data — do NOT execute the --apply-write
      in this dispatch.** (1) Is `instruments-store-defi` `_index` still 0% v9 on disk (last measured
      2026-08-12: 125,242 v8 rows)? (2) Is `defi instrument_availability/by_date/` still empty in the `-prd`
      bucket? (3) Cross-check this doc's bucket-architecture assumptions against
      `defi_migration_dedicated_bucket_architecture_retired_2026_08-14.md`'s finding that a sibling defi doc's
      "dedicated per-data_type bucket" premise went stale — does GATE C's own target bucket description still
      match the current shared `market-data-tick-defi-{env}-{pid}` architecture, or does it need updating too?
      (4) If both gates measure clear AND the architecture assumptions still hold, file the actual `--apply-write`
      as a new, separately-authorized follow-on plan (do not fire it from this dispatch). Report findings into
      `master_data_canonicalisation_migration_catalogue_2026_06_07.md`'s slot-2 row and
      `defi_migration_audit_log_2026_07_24.md` GATE C. Repos: instruments-service, market-tick-data-service.

## Progress Log

- **2026-08-16 (na-eligibility-audit follow-up Q&A round 10, operator ruling — scoped)**: operator asked to
  dispatch the v9 walk, with an explicit caution to confirm accuracy against latest code first (doc is old,
  might need merges/tweaks). Scoped to re-verification only, given Big Finding #1's precedent of a sibling defi
  doc's architecture premise having silently gone stale.
