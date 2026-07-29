---
doc_type: issue
title:
  TradFi manifest carries 1,314,705 legacy `COMBO`-uppercase `instrument_type` rows (vs 23,428 correctly-lowercase
  `combo`) — a pre-2026-06-22 writer-casing residual never reconciled, real production census attached
summary: >-
  While wiring the UAC underlying-naming reverse-lookup into the G1-ENUM present-set rollup fix
  (`tradfi_combo_underlying_naming_mismatch_blocks_g1_enum_present_rollup_2026_07_28.md`), a real census of the live
  tradfi manifest (`market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet`, 5,456,407
  rows) confirmed the legacy-casing residual that issue flagged as "worth a dedicated reconciliation pass": 1,314,705
  rows carry `instrument_type=COMBO` (uppercase) vs only 23,428 carrying the canonical `instrument_type=combo`
  (lowercase) — a ~56:1 ratio, pre-dating the 2026-06-22 `_canonical_writer_instrument_type` writer-grain-alignment fix
  that made new captures write the lowercase form. This is a MANIFEST INDEX column-value residual (the
  `availability_index.parquet`'s `instrument_type` column), NOT a GCS object-path casing issue (that class is already
  covered by the existing `scripts/migrate_instrument_type_lowercase.py`, which rewrites hive-partitioned
  `instrument_type=` path segments in the actual data files — a different target, not reusable as-is for this
  manifest-index residual).
status: resolved
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [manifest, g1-enum, tradfi, combo, instrument_type, casing, migration]
related:
  [
    /plans/active/issues/tradfi_combo_underlying_naming_mismatch_blocks_g1_enum_present_rollup_2026_07_28.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: 2026-07-28
priority: P3
parent_epic: infrastructure_master
source:
  "autonomous dispatch, tradfi combo underlying-naming reverse-lookup wiring task, discovered while investigating the
  naming-mismatch issue's flagged casing residual, 2026-07-28"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
assigned_vm: NA
resolved_by: "instruments-service@f3cd7dd1 — migration applied live to prod 2026-07-29"
locked_by:
locked_since:
---

# TradFi manifest `COMBO`-uppercase casing residual (1.3M rows) never reconciled to lowercase

## What I found

A real census of the live tradfi manifest index
(`gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet`, 5,456,407 total rows,
columns `instrument_type`/`capture_status`/`underlying` projected):

```
instrument_type=COMBO (uppercase, legacy):   1,314,705 rows
instrument_type=combo (lowercase, canonical):   23,428 rows

COMBO-uppercase breakdown by capture_status:
  empty_confirmed        718,567
  attempted_failed       360,571
  captured               235,321
  expected_unattempted        246

combo-lowercase breakdown by capture_status:
  captured                23,428  (100%)
```

These numbers exactly match the direct-probe figures cited in
`tradfi_combo_underlying_naming_mismatch_blocks_g1_enum_present_rollup_2026_07_28.md` ("1,314,705 rows" / "23,428 rows"
/ "246" `expected_unattempted`) — this issue is the dedicated write-up that source issue's "Why it matters" section
flagged as a separate follow-up ("Worth a dedicated reconciliation pass independent of this naming-mismatch fix...
reconcile/backfill the 1.3M-row legacy `COMBO`-uppercase residual... once the naming mismatch is resolved, so the
manifest converges on the single lowercase-canonical `combo` instrument_type going forward").

The residual pre-dates the 2026-06-22 `_canonical_writer_instrument_type` writer-grain-alignment fix (referenced in the
sibling issue) — captures written before that fix stamped `instrument_type=COMBO` (uppercase); captures written after
stamp the canonical `combo` (lowercase). The manifest has carried both forms side-by-side ever since, with no
reconciliation pass to collapse the legacy rows onto the canonical casing.

## Why this is filed separately, not fixed inline

This was investigated (not guessed at) during the reverse-lookup wiring task and judged bigger than a bounded add-on for
that session, because:

1. **Scale + mixed state**: 1.3M rows spanning ALL FOUR `capture_status` values (not just `captured`) — a safe
   reconciliation must decide the correct handling for `attempted_failed` (360,571) and `empty_confirmed` (718,567) rows
   too, not just relabel `captured` rows. That is a design question (does an `attempted_failed` COMBO row's
   underlying/instrument_id shape need the SAME naming-mismatch reconciliation the present-set rollup fix applies at
   read-time, or does the manifest row itself need rewriting?), not a mechanical find-and-replace.
2. **No ready-made script targets this surface**: `scripts/migrate_instrument_type_lowercase.py` (the obvious
   same-shaped precedent) rewrites GCS **object paths** (hive `instrument_type=` path segments in the actual parquet
   data files) via server-side copy+delete — a different surface from the **manifest index's own `instrument_type`
   column value** this residual lives in. A new script is needed; it should follow the SAME conventions (backup before
   write, `--dry-run` default, idempotent, per-shard failure isolation) but targets the manifest index parquet, not GCS
   object paths.
3. **Live production artifact**: `availability_index.parquet` is actively read/written by the manifest consolidator and
   every writer/enumerator run — a bulk rewrite needs the standard backup-then-write protocol
   (`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`) and ideally a brief drain/quiesce window, not an ad hoc
   in-session rewrite of a live 82MB prod index.

## Recommended next step

Scope a new migration script (e.g. `migrate_tradfi_combo_manifest_casing.py`, mirroring
`migrate_instrument_type_lowercase.py`'s dry-run-default + backup-then-write + idempotent conventions but targeting
`availability_index.parquet`'s `instrument_type` column instead of GCS object paths):

1. Read the manifest index, identify every `instrument_type=COMBO` row.
2. Decide the per-`capture_status` handling (a design call, not mechanical — likely: relabel `instrument_type` to
   `combo` in place for all four states, since the value itself is what's being corrected, not the row's meaning).
3. Backup the pre-migration index (timestamped snapshot, mirroring the existing `_index/snapshots/`/`_index/backups/`
   convention already visible in the bucket).
4. Dry-run report (counts + a sample diff) before any `--apply`.
5. Apply + verify: post-migration census shows `instrument_type=COMBO` (uppercase) at 0 rows, `combo` (lowercase) at the
   pre-migration sum (1,314,705 + 23,428 = 1,338,133).
6. Re-run the G1-ENUM present-set tradfi quantification (per the sibling issue's methodology) to confirm the
   `expected_unattempted` count doesn't regress (the reconciled rows should either stay suppressed via the present-set
   rollup or close further phantom cells if any were keyed on the uppercase form).

Not urgent (P3) — the manifest reads today already tolerate both casings via the grain-symmetry + naming-mismatch fixes
(`bundle_instrument_type_for_leaf`/`grain_for_instrument_type` normalise `instrument_type.strip().lower()` before
lookup), so this is a cleanliness/consolidation migration, not a correctness blocker.

## Progress Log

- 2026-07-29 (autonomous session, resumed after a session-limit crash mid-workflow): built + ran
  `instruments-service/scripts/migrate_tradfi_combo_manifest_casing.py`, following exactly the recommended-next-step
  shape (dry-run default, timestamped backup, CAS-conditional live-index overwrite with retry-on-concurrent-write,
  fresh-read post-apply verification gate — using the UTL `gcs_conditional_put`/`gcs_read_object_with_generation`
  wrappers, not the precedent script's now-superseded direct `google.cloud.storage` import). 13 unit tests (relabel
  logic, all-4-capture_status coverage, idempotency, row-identity preservation). **Ran the real `--apply` against live
  prod** (`market-data-tick-tradfi-prd-central-element-323112/_index/ availability_index.parquet`): pre-migration census
  (generation `1785287282530951`, 5,855,418 total rows — the manifest has grown since this issue was filed, real drift
  noted per the script's own sanity-window log) showed `COMBO`(upper)=1,315,878 across the same 4 capture_status buckets
  / `combo`(lower)=23,428; snapshot backed up to
  `_index/backups/availability_index.pre_combo_casing_relabel_20260729T042832Z.parquet`; CAS-write succeeded first
  attempt (new generation `1785299530346811`); **fresh-read post-apply verification (a second, independent read, not the
  script's own in-memory frame) confirmed GATE PASSED: `COMBO`(upper)=0 residual, `combo`(lower)=1,339,306 — exactly
  matching the pre-migration sum.** Item 6 of the recommended next steps (re-run the G1-ENUM tradfi quantification to
  confirm no regression) was covered as part of the sibling
  `tradfi_combo_composite_id_misparse_mvp_gate_false_exclusion_2026_07_28.md` fix's own before/after production
  verification, run against the manifest AFTER this migration landed — no regression, `combo` now correctly appears in
  the `expected_unattempted` breakdown. **DONE — `instruments-service@f3cd7dd1`.**
