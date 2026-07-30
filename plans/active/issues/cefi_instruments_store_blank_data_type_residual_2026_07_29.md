---
doc_type: issue
title: cefi instruments-store-cefi-prd — 6.87% blank data_type residual (post v8→v9 walk)
summary: >-
  Live cf_manifest_audit re-run against instruments-store-cefi-prd found the parent v8→v9 single-walk todo's named
  criteria (CF-1/3/4/8, capture_status null%) fully GREEN, but a distinct blank-data_type residual (6.87% of rows) is
  not yet resolved -- filed as its own bounded follow-up.
status: open
nature: guideline
asset_group: [cefi]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [cefi, instruments-store, manifest, data-type, data-correctness]
related: [/plans/active/data_completion_cefi_2026_07_15.md]
created: 2026-07-29
parent_epic: mtds_mdps_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.2
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on:
assigned_role: data_engineering
source: [data_completion_cefi_2026_07_15.md, cf_manifest_audit live re-run 2026-07-29]
drift_direction: advance-code
---

## What I found

Re-ran `unified_trading_library.cf_manifest_audit.audit()` live (read-only, `mode="changed"`, no `--apply`) against
`instruments-store-cefi-prd-central-element-323112` (84,542 rows) as part of closing
`data_completion_cefi_2026_07_15.md`'s "cefi `instruments-store` `_index` v8→v9 single-walk" todo. The core v8→v9
migration criteria named by that todo are now fully GREEN: CF-1 schema_version=100% v9, CF-3 pipeline_mode
populated=100%, CF-4 source blank=0%, CF-8 available_at non-null=100%, `capture_status` null=0% (was ~40% at the
2026-06-07 baseline).

One named residual from that same original diagnosis is NOT fully resolved: **blank `data_type` = 6.87% (5,807/84,542
rows)**, down from "blank on every row" (100%) at the 2026-06-07 baseline but not zero. Breakdown by `capture_status`:

- `empty_confirmed`: 4,935
- `expected_unattempted`: 856
- `attempted_failed`: 15
- `captured`: **1** ← the one row that looks like a genuine gap (a captured cell should always carry a typed
  `data_type`)

All 5,807 blank rows have `service_name=instruments-service`. By venue: POLYMARKET-PERP 1,435 / KALSHI-PERP 1,428 /
COINBASE-CDE 1,420 / LIGHTER-ZKSYNC 976 / PACIFICA-SOLANA 489 / BINANCE-DELIVERY 32 / DERIBIT-COMBO 7 / a handful of
others. The non-blank rows (78,735) all carry `data_type=instruments` (the IS reference index is venue×date-keyed, not
literally data_type-keyed, per the original 2026-06-07 diagnosis — this file's `data_type` column is a bolt-on typing
rather than a native key column).

## Why it matters

Per the data-pipeline-correctness HARD RULE, a manifest cell in a non-empty `capture_status` state should carry
complete, typed columns — a blank `data_type` on 6.87% of rows is a residual gap in the "canonical form should still
type it" recommendation from the original diagnosis, even though it doesn't block the v8→v9 schema/column migration
itself (which is what the parent todo's CF-1/3/4/8 named criteria actually gate). The 1 blank-`data_type` row with
`capture_status=captured` is the highest-priority sub-case — a captured cell with no data_type is a genuine typing gap,
not a structural non-issue.

## Recommended decision

- [ ] [DATA] P3. Diagnose the 1 `instruments-store-cefi-prd` row with `capture_status=captured` and blank `data_type` —
      identify it (venue/date/instrument_id) and either backfill its `data_type` or confirm+document why a captured row
      can legitimately lack one. (repo: instruments-service)
- [ ] [DATA] P3. For the 5,806 non-captured (`empty_confirmed`/`expected_unattempted`/`attempted_failed`)
      blank-`data_type` rows, concentrated in POLYMARKET-PERP/KALSHI-PERP/COINBASE-CDE/LIGHTER-ZKSYNC/PACIFICA-SOLANA:
      confirm whether these venues structurally never produce a typed `data_type` for the IS reference index (in which
      case document the exemption, mirroring the finding-144-style waiver pattern used for the analogous
      market-data-tick-cefi-prd path-scheme residuals) or backfill the type if it's a genuine writer gap. (repo:
      instruments-service)
