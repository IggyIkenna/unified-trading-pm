---
doc_type: plan
title: DeFi phoenix delete + orphan-bucket delete verify + live-poller scoping
summary: >-
  Operator-ruled 2026-08-15 (na-eligibility-audit follow-up Q&A) — three DeFi items from
  cross_ag_live_capture_parity_2026_08_14.md and defi_migration_audit_log_2026_07_24.md: delete phoenix_ws.py dead code,
  verify-then-execute the duplicate/legacy DeFi orphan-bucket delete, and begin scoping the ~40 BLOCKED-BUILD DeFi live
  pollers the operator approved building.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-api-contracts, market-tick-data-service, instruments-service]
scope: [engineer]
tags: [defi, canonicalization, venue-registry, gcs-delete, live-capture]
related:
  [
    /plans/active/cross_ag_live_capture_parity_2026_08_14.md,
    /plans/active/defi_migration_audit_log_2026_07_24.md,
    /plans/active/issues/uac_venue_to_asset_group_defi_registry_gap_2026_08_09.md,
  ]
created: "2026-08-15"
last_updated: "2026-08-15"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 4
assigned_role: data_engineering
effort: max
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A, 2026-08-15"
locked_by:
context_scope:
  [
    /plans/active/cross_ag_live_capture_parity_2026_08_14.md,
    /plans/active/defi_migration_audit_log_2026_07_24.md,
    /plans/active/issues/uac_venue_to_asset_group_defi_registry_gap_2026_08_09.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
locked_since:
resolved_by:
---

# DeFi phoenix delete + orphan-bucket delete verify + live-poller scoping

## Todos

- [ ] [OPERATOR] P2. **Reconcile before deleting — a contradiction was found after the ruling, not before.**
      `cross_ag_live_capture_parity_2026_08_14.md` line 148-151 claims `PHOENIX-SOLANA` is "not in current UAC
      `VENUES_BY_ASSET_GROUP` at all" (verified live, 168-venue universe) and its REST API was deprecated 2026-05-15 —
      operator ruled 2026-08-15 to delete `phoenix_ws.py` as dead code on that basis. But that same source doc's own
      Progress Log (line 383-385) separately notes
      `/plans/active/issues/uac_venue_to_asset_group_defi_registry_gap_2026_08_09.md` (open, `assigned_vm: planning`)
      independently found `PHOENIX-SOLANA` **IS** present in `ALL_DEFI_VENUES`. These two findings directly disagree on
      whether `PHOENIX-SOLANA` exists in any UAC venue registry today. Read both docs, resolve which is current, and
      only THEN execute (or skip) the `phoenix_ws.py` deletion — do not delete blind on the operator's ruling alone,
      since the ruling was made without this contradiction surfaced. (repos: unified-api-contracts,
      market-tick-data-service)
- [ ] [DATA] P1. Verify the unique-gap migration (Aave 2022-03..10, marinade LST, KAMINO DEX pools —
      `defi_migration_audit_log_2026_07_24.md` line 575-577) has actually landed (query the manifest / check the
      migration script's completion evidence). If confirmed: execute the DELETE of the duplicate/legacy DeFi orphan
      buckets (`market-data-tick-defi{,-prd}`, `solana-defi{,-prd}`, `evm-defi{,-prd}`, post unique-gap migration). If
      not confirmed: do not delete — report back what's still missing. (repo: instruments-service)
- [ ] [DATA] P2. Enumerate the ~40 DeFi venues currently left as `BLOCKED-BUILD` live-poller placeholders
      (`cross_ag_live_capture_parity_2026_08_14.md` § Finding D) and produce a phased build plan (not a full 40-poller
      build in one pass — scope tranches by venue TVL/priority, identify shared connector patterns that reduce per-venue
      build cost). This todo's done-when is the phased plan existing and reviewed, not all 40 pollers built. Operator
      approved DeFi live capture as in-scope 2026-08-15. (repo: market-tick-data-service)

## Progress Log

- **2026-08-15 (na-eligibility-audit follow-up, operator ruling)**: extracted from
  `cross_ag_live_capture_parity_2026_08_14.md` and `defi_migration_audit_log_2026_07_24.md`. The `.bak*` retention
  question from the same source doc was answered "leave as-is indefinitely" (no dispatch) — recorded directly in that
  doc, not part of this plan. The phoenix contradiction (todo 1) was found during this extraction, after the operator's
  ruling — flagged rather than silently resolved either way.
