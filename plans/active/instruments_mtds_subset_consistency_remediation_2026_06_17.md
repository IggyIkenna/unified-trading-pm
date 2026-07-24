---
doc_type: plan
title: Instruments ↔ MTDS subset + consistency remediation
summary: >-
  COORDINATION INDEX (trimmed 2026-07-24, plan-hygiene line-cap remediation). This plan's substantive content (114
  todos, all Progress Log narrative) was split 3-way into
  `instruments_store_cf_canonicalization_single_walk_2026_07_24.md` (26 todos -- inherited CF-1..CF-12 canonical-form
  single-walk lineage), `instruments_mtds_consistency_remediation_residuals_2026_07_24.md` (43 todos -- this plan's own
  core F1-F7/N1-N9 audit-remediation scope), and `mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md` (45
  todos -- venue-onboarding + ops-hardening residuals). This file is now an entry-point index only; no todos remain
  here. See the "Where the content went" table below for the exact provenance of every moved section.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos:
  [deployment-api, deployment-service, e2e-testing, features-service, instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags:
  [
    instruments,
    mtds,
    manifest,
    canonicalisation,
    data-correctness,
    audit,
    backfill,
    pipeline-mode,
    reconciliation,
    single-walk,
    sports,
    defi,
    plan-hygiene,
    plan-split,
  ]
related:
  [
    plans/audit/results/instruments_mtds_subset_and_consistency_audit_2026_06_17.md,
    plans/active/instruments_foundation_completeness_2026_06_24.md,
    instruments_store_cf_canonicalization_single_walk_2026_07_24,
    instruments_mtds_consistency_remediation_residuals_2026_07_24,
    mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/pipeline-mode-partition.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
  ]
created: 2026-06-17
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: data_engineering
entry_point_for:
  [
    instruments_store_cf_canonicalization_single_walk_2026_07_24,
    instruments_mtds_consistency_remediation_residuals_2026_07_24,
    mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24,
  ]
last_updated: "2026-07-24"
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  [
    "plans/audit/results/instruments_mtds_subset_and_consistency_audit_2026_06_17.md (findings F1–F7, full-index walk)",
    operator 2026-06-17 (deep-dive audit dispatch),
    "plans/active/issues/plan_line_cap_remediation_2026_07_23.md (2026-07-24 line-cap clean-partition split, operator
    [unlock-plan] grant)",
  ]
drift_direction: advance-code
---

# Instruments ↔ MTDS subset + consistency remediation

> **🟢 TRIMMED TO A COORDINATION INDEX (2026-07-24) — plan-hygiene line-cap remediation.** This plan was 2168 lines
> (over the 1000-line hard-fail cap; `locked_by: live-defi-rollout`). Per
> `plans/active/issues/plan_line_cap_remediation_2026_07_23.md`'s bucket-(c) classification, the operator granted
> `[unlock-plan]` for a 3-way clean-partition split. **Every substantive line of the original body — every todo, every
> Progress Log entry, every finding — moved verbatim into one of the 3 child plans below; nothing was summarized,
> rewritten, or dropped.** `locked_by`/`locked_since` are cleared on this trimmed original per the operator's explicit
> unlock grant. This file now carries **zero todos** and is a pure entry-point index (`entry_point_for:` the 3 children,
> which stay the live execution surface).

## The 3 child plans

| Child plan                                                         | Todos (open/done)           | Scope                                                                                                                                                                                                                                                                                                                                                       |
| ------------------------------------------------------------------ | --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `instruments_store_cf_canonicalization_single_walk_2026_07_24.md`  | 26 (21 open / 5 done)       | Inherited canonical-form (CF-1..CF-12) single-walk code-remediation lineage -- the instruments-store bucket legacy-GCS audit + `_index` canonicalisation this plan ran directly, plus the still-open CF-numbered items migrated in 2026-06-26 from 2 archived sibling plans.                                                                                |
| `instruments_mtds_consistency_remediation_residuals_2026_07_24.md` | 43 (14 open / 29 done)      | This plan's own **core original scope** -- the F1-F7/N1-N9 findings from the 2026-06-17 subset+consistency audit, the pre-`--apply` blocker gate, the GCS delete-safety invariant, the execution sequence, v9 `_index` column population + N6r venue-spelling canonicalisation, migration-unmappable-residue diagnosis, and Phase A-D findings/remediation. |
| `mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md`    | 45 (22 open / 23 done)      | Venue-onboarding (Kraken/Lighter-zkSync/Pacifica-Solana/Extended-Starknet/Bitget/Drift/Aave_v3-Optimism/Deribit-Combo/Kalshi/SFI/Transfermarkt) + ops-hardening (Databento subscription contract, gas-fees/SFI VM parallelisation + rate-limit fixes, consolidator coverage) + the TradFi ICE/CME + DeFi EIGENLAYER legacy chain-tail fixes.                |
| **Total**                                                          | **114 (57 open / 57 done)** | Conserved exactly from the original 114-todo body.                                                                                                                                                                                                                                                                                                          |

## Where the content went (original-file line provenance, for audit-trail)

Original file: `instruments_mtds_subset_consistency_remediation_2026_06_17.md` (pre-split, 2168 lines). Line numbers
below refer to that pre-split revision (recoverable via `git log`/`git show` on this path).

| Original section (## header)                                                                           | Original lines | Moved to                                                           |
| ------------------------------------------------------------------------------------------------------ | -------------- | ------------------------------------------------------------------ |
| Pre-`--apply` BLOCKER GATE / SCRIPT-COVERAGE MAP / GCS DELETE SAFETY INVARIANT banners                 | 63-109         | `instruments_mtds_consistency_remediation_residuals_2026_07_24.md` |
| GCS delete safety — path/schema migration prerequisite map                                             | 110-135        | same                                                               |
| Execution sequence (end-to-end)                                                                        | 136-179        | same                                                               |
| AUTONOMOUS COMPLETION PLAN (2026-06-18)                                                                | 180-215        | same                                                               |
| Progress Log — B0/B1/B2 autonomous run (per-venue instrument backfill diagnosis)                       | 216-436        | `mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md`    |
| GCS object-migration COMPLETE + delete-list sizing (+ Fresh audit 2026-07-13)                          | 437-541        | `instruments_mtds_consistency_remediation_residuals_2026_07_24.md` |
| MARKET-DATA `_index` v9 COLUMN POPULATION                                                              | 542-584        | same                                                               |
| MARKET-DATA `_index` venue/instrument_type SPELLING canonicalisation (N6r)                             | 585-659        | same                                                               |
| INSTRUMENTS-STORE buckets — legacy GCS audit + `_index` canonicalisation COMPLETE                      | 660-734        | `instruments_store_cf_canonicalization_single_walk_2026_07_24.md`  |
| CME event contracts (v9-certification dependency)                                                      | 735-748        | `instruments_mtds_consistency_remediation_residuals_2026_07_24.md` |
| Forthcoming credentials (Kalshi/Extended) + Databento SUBSCRIPTION CONTRACT                            | 749-838        | `mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md`    |
| Autonomous-run residuals + Migration unmappable residue (10,250 objects)                               | 839-979        | `instruments_mtds_consistency_remediation_residuals_2026_07_24.md` |
| Phase A — subset violations                                                                            | 980-1000       | same                                                               |
| Phase B — instruments internal consistency                                                             | 1001-1028      | same                                                               |
| Phase C — file-level verification                                                                      | 1029-1036      | same                                                               |
| Phase D — file-level correctness findings                                                              | 1037-1229      | same                                                               |
| SPORTS E2E audit + twin-migration drive (through Kalshi Q&A canonical parser)                          | 1230-1909      | `mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md`    |
| Folded-in (I-2 consolidation 2026-06-26) — inherited CF-1..CF-12 lineage from 2 archived sibling plans | 1910-2003      | `instruments_store_cf_canonicalization_single_walk_2026_07_24.md`  |
| TradFi ICE/CME pre-cutover legacy chain-tail                                                           | 2004-2060      | `mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md`    |
| DeFi EIGENLAYER combined-venue legacy + mis-shaped-canonical-twin                                      | 2061-2153      | same                                                               |
| Deferred work — migrated to: (closing note)                                                            | 2154-2168      | same                                                               |

**Conservation check**: 2106 body lines (L63-2168) accounted for across the 3 children with zero gaps/overlaps; 114 todo
checkboxes (57 `- [x]` + 57 `- [ ]`) counted before the split and after the split — both totals match exactly (26 + 43 +
45 = 114).

**Known residual finding (flagged, not actioned here)**: `mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md`
lands at ~1237 lines post-split — still over the 1000-line hard-fail cap (though a large reduction from the 2168-line
original). This 3-way split was the exact action specified for this remediation job; a further split of that child
(e.g., peeling its ~680-line "SPORTS E2E audit + twin-migration drive" section into its own file) is flagged as
follow-up work, not executed unilaterally here since it was outside this job's approved 3-way scope.
