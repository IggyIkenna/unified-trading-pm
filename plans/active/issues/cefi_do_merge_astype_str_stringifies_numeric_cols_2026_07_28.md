---
doc_type: issue
title: "cefi migration do_merge() heterogeneous-dtype fix stringifies ANY disagreeing column, not just id/symbol keys"
summary: >-
  market-tick-data-service/scripts/migrate_cefi_tardis_filename_canonical_2026_07_17.py do_merge() normalizes
  heterogeneous-dtype columns across a venue merge group by .astype(str). The detection is generic: it stringifies every
  column whose dtype disagrees across the group, not just the id/symbol key columns it was written for. Harmless for the
  cefi run that shipped (only the id/symbol col disagreed; verified on PROD, 0 rows dropped — mtds@feeb8a6e), but
  do_merge is reusable, so a FUTURE venue group where a numeric MEASUREMENT column disagrees in dtype (e.g.
  int64-vs-float64 from a NaN in one shard) would silently stringify that measurement column, corrupting the merged
  output. P3 robustness/DRY follow-up: narrow the stringify to the key columns.
status: open
nature: issue
asset_group: [cefi]
stage: [meta]
repos: [unified-trading-pm, market-tick-data-service]
scope: [engineer]
tags: [dtype, pandas, astype, do_merge, cefi, migration, robustness, footgun, latent]
related: [/plans/active/issues/solana_address_primitives_duplicated_across_mtds_handlers_2026_07_28.md]
created: 2026-07-28
last_updated: 2026-07-28
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.08
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  REVIEW-craft finding 2026-07-28 (msg 2500, non-blocking P3 LATENT) reviewing slot-5 cefi_native-010 (mtds@feeb8a6e).
  Reviewer verified the shipped run on PROD (0 rows dropped, canonical target gcs-confirmed); this is a reusability
  footgun, NOT a redo of the shipped work.
---

## Finding

`do_merge()` in `market-tick-data-service/scripts/migrate_cefi_tardis_filename_canonical_2026_07_17.py` handles
heterogeneous column dtypes across a venue merge group by coercing disagreeing columns with `.astype(str)`. The
detection is **generic** — it applies to any column whose dtype differs across the group, not only the id/symbol key
columns the fix targeted.

For the cefi run that shipped this was harmless: only the id/symbol column disagreed, and the run was verified on PROD
(0 rows dropped, canonical target gcs-confirmed, mtds@feeb8a6e). But `do_merge()` is reusable across venue groups, so
the fix is a latent footgun: if a future merge group has a numeric **measurement** column that disagrees in dtype
(classically `int64` vs `float64` because one shard carried a NaN), `.astype(str)` would silently stringify that
measurement column and corrupt the merged output.

## Suggested fix (P3, non-blocking)

Narrow the coercion to the join/id key columns (the ones legitimately expected to vary in string form), rather than
stringifying every dtype-disagreeing column. Options: (a) explicitly whitelist the key columns to normalize; (b) for
numeric columns, up-cast to a common numeric dtype (e.g. `float64`) instead of `str`; (c) fail loud if a non-key column
disagrees in dtype, so a real data problem surfaces instead of being papered over.

## Notes

- Non-blocking: the shipped cefi run is correct and verified; nothing to redo.
- Only bites if this migration script is re-run for a different venue group whose measurement columns disagree in dtype.
- `assigned_vm: NA` — tracked, NOT auto-dispatched. Operator can flip to `planning` + `active` to dispatch as a
  data_engineering cleanup, ideally bundled with any future re-use of this migration.

## Progress Log

- 2026-07-28: Filed by main from REVIEW-craft finding (msg 2500). Acked to reviewer; endorsed non-blocking, tracked NA
  pending a dispatch/re-use decision.
