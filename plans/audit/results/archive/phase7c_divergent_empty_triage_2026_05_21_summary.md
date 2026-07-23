---
doc_type: audit-result
title: Phase 7C — DIVERGENT_EMPTY Triage Summary
summary:
  Phase 7C triage of all 765 DIVERGENT_EMPTY cells from the A3 manifest divergence parquet — every cell
  (AAVE_V3-OPTIMISM 5 data_types + COMPOUND_V3-BASE 4) routed to phase_11_rebackfill (adapter wrote a single
  empty_confirmed row where SHOULD_HAVE_DATA); 0 label-flips (no captured parquet exists, a flip would be dishonest).
status: partial
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: [audit, manifest, data-correctness, defi, backfill, reconciliation]
related: [/plans/audit/results/archive/manifest_divergence_2026_05_20_summary.md]
created: 2026-05-21
audited_scope:
  All 765 DIVERGENT_EMPTY cells in plans/audit/results/manifest_divergence_2026_05_20.parquet (AAVE_V3-OPTIMISM +
  COMPOUND_V3-BASE DeFi lending data_types) — per-cell triage into label-flip / phase_11_rebackfill / operator-scope
  buckets
date: 2026-05-21
auditor: slot-5
parent_epic: infrastructure_master
severity: P1
resulting_plan:
lib_version:
doc_versions_checked:
---

# Phase 7C — DIVERGENT_EMPTY Triage Summary

_Generated: 2026-05-21_ _Triaged by: slot-5_ _Input: plans/audit/results/manifest_divergence_2026_05_20.parquet_

## Triage decision

All 765 DIVERGENT_EMPTY cells → **phase_11_rebackfill**

**Rationale**: every cell has `any_captured=False, any_empty=True, any_failed=False, row_count=1`. This means the MTDS
adapter wrote exactly one `empty_confirmed` manifest row when `expected_state=SHOULD_HAVE_DATA`. This is an
adapter-level bug (handler returned 0 data when protocol had activity) — NOT a mislabelled captured row. A label-flip to
`captured` would be dishonest (there is no captured parquet). The correct fix is operational re-backfill under Phase 11
(MTDS handler investigation + historical data re-fetch).

## Distribution

| venue            | data_type          | cells   | triage_decision     |
| ---------------- | ------------------ | ------- | ------------------- |
| AAVE_V3-OPTIMISM | flash_loan_events  | 141     | phase_11_rebackfill |
| AAVE_V3-OPTIMISM | lending_indices    | 141     | phase_11_rebackfill |
| AAVE_V3-OPTIMISM | liquidation_events | 141     | phase_11_rebackfill |
| AAVE_V3-OPTIMISM | position_data      | 141     | phase_11_rebackfill |
| AAVE_V3-OPTIMISM | risk_params        | 141     | phase_11_rebackfill |
| COMPOUND_V3-BASE | lending_indices    | 15      | phase_11_rebackfill |
| COMPOUND_V3-BASE | liquidation_events | 15      | phase_11_rebackfill |
| COMPOUND_V3-BASE | position_data      | 15      | phase_11_rebackfill |
| COMPOUND_V3-BASE | risk_params        | 15      | phase_11_rebackfill |
| **TOTAL**        |                    | **765** |                     |

## Triage buckets (master_coord § Phase 7(c))

| Bucket                                         | Count | Action                                      |
| ---------------------------------------------- | ----- | ------------------------------------------- |
| label-flip-applied (captured-but-mislabelled)  | 0     | N/A                                         |
| phase_11_rebackfill (genuinely needs re-fetch) | 765   | Track under D4 plan (MTDS handler backfill) |
| operator-scope (out of scope)                  | 0     | N/A                                         |

## Next steps

- Phase 11 owner: queue MTDS handler investigation for AAVE_V3-OPTIMISM (5 data_types) + COMPOUND_V3-BASE (4 data_types)
- D4 plan (`plans/active/...`) should track the per-venue re-backfill tasks
- 0 label-flip actions needed in Phase 7 — no capture_status changes in Phase 7 for these cells
