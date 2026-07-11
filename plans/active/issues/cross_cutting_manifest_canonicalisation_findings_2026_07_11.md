---
doc_type: issue
title:
  "Cross-cutting manifest-canonicalisation findings + per-AG CF-state assessment (2026-07-11 /autonomous) — 2 shared
  bugs root-caused & fixed (schema_version-as-string, audit-tool _probe_paths backup-descent); precise per-AG
  remaining-work map for cefi/defi/tradfi/sports so each can be driven to E7-green + E8-delete applying prediction's
  proven lessons"
summary:
  "While driving the prediction manifest-canonicalisation to E7-GREEN + E8/E8b legacy-bucket deletes, two CROSS-CUTTING
  bugs affecting ALL migrated AGs were root-caused and fixed: (1) the shared v9 populator
  (populate_v9_index_columns_inplace.py) only rewrote NON-'9' schema_version rows to int 9, so rows already stored as
  the STRING '9' survived the str-guard and left the column mixed-object — which breaks readers doing schema_version >=
  9 (int compare) and makes CF-1 audit falsely RED on cefi/defi/tradfi (FIXED: forces int64 dtype); (2) the CF-audit's
  _probe_paths descended into _migration_backup/ (only _index/_vm_staging/snapshots were excluded), sampling a
  non-partitioned backup parquet and reporting false CF-2-paths/CF-3-partition RED on every AG (FIXED pm PR#928: skips
  ALL _-prefixed meta trees). Fresh CF-audits of all 5 AG canonical surfaces give the precise remaining-work map below.
  CF-8 (available_at absent, written_at proxy) is RED on ALL AGs and is a separate lookahead concern
  (predictions_lookahead_and_reader_migration_2026_06_20.md), not a per-AG blocker."
status: open
nature: notes
asset_group: [cross-cutting]
stage: [meta]
repos: [market-tick-data-service, unified-api-contracts, unified-trading-library, unified-trading-pm]
scope: [engineer]
tags: [manifest, canonicalisation, cf-audit, schema-version, cross-cutting, findings]
related:
  [
    prediction_manifest_canonicalisation_2026_06_01.md,
    cefi_manifest_canonicalisation_2026_06_01.md,
    defi_manifest_canonicalisation_2026_06_01.md,
    tradfi_manifest_canonicalisation_2026_06_01.md,
    sports_manifest_canonicalisation_2026_06_01.md,
    master_data_canonicalisation_migration_catalogue_2026_06_07.md,
  ]
created: 2026-07-11
parent_epic: manifest_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.2
assigned_role: data-engineer
drift_direction: advance-code
depends_on: []
locked_by: live-defi-rollout
locked_since: 2026-07-11
source:
  ["/autonomous 2026-07-11 prediction canonicalisation drive — surfaced 2 cross-cutting bugs + per-AG CF-audit state"]
resolved_by:
---

# Cross-cutting manifest-canonicalisation findings (2026-07-11 /autonomous)

> Companion to the 5 per-AG `*_manifest_canonicalisation_2026_06_01.md` plans + the master catalogue. Written after
> driving PREDICTION to full completion (E7-green manifest content + E8 tick-bucket delete + E8b instruments-store
> migrate+delete). Records the two shared bugs that were root-caused & fixed here, and the precise per-AG CF-state so
> cefi/defi/tradfi/sports can each be finished applying the same proven playbook.

## Two CROSS-CUTTING bugs — root-caused & FIXED this session

### 1. `schema_version` stored as STRING `'9'` (not int 9) — breaks reader int-comparison + false CF-1 RED

- **Symptom**: CF-audit reports `CF-1 [RED] v9=0/N (0.0%)` on cefi/defi/tradfi even though the value-distribution shows
  `'9'` at ~100%. The canonical `_index` `schema_version` column is `dtype=object` holding the string `'9'`.
- **Why it's a REAL bug, not cosmetic**: the UTL native writer types `schema_version: int = MANIFEST_SCHEMA_VERSION`
  (`unified_trading_library/manifest_writer/_rows.py`), and readers gate on
  `date_df["schema_version"] >= MANIFEST_SCHEMA_VERSION` (`_queries.py`) — a **str-vs-int comparison** that raises /
  misbehaves against string `'9'`.
- **Root cause**: `market_tick_data_service/scripts/populate_v9_index_columns_inplace.py` computed
  `not_v9 = df["schema_version"].apply(lambda v: str(v) != "9")` then set only `df.loc[not_v9] = 9`. Rows already stored
  as the STRING `'9'` pass the `str(v) != "9"` guard → never rewritten → column stays mixed-`object` → parquet stores
  string.
- **FIX (shipped, MTDS, landed on live-defi-rollout)**: append
  `df["schema_version"] = pd.to_numeric(df["schema_version"]).astype("int64")` after the bump. Every future `--apply`
  emits canonical int schema_version.
- **Existing-manifest remediation**: prediction's `_index` was normalised in-place (int64) → CF-1 GREEN.
  cefi/defi/tradfi `_index`es still hold string `'9'` and will be corrected when their migration re-runs the fixed
  populator (OR via a targeted `pd.to_numeric(...).astype("int64")` normalisation of the one
  `_index/availability_index.parquet` — snapshot first; prediction's normalisation script pattern is in that plan's
  Progress Log).

### 2. CF-audit `_probe_paths` descended into `_migration_backup/` → false CF-2-paths/CF-3-partition RED

- **Symptom**: every AG showed `CF-2-paths [RED]` / `CF-3-partition [RED]` even when the actual data objects are
  canonically partitioned (`raw_tick_data/by_date/day=…/pipeline_mode=…/asset_group=…/venue=…/data_type=…/`).
- **Root cause**: `cf_manifest_audit_2026_06_01.py::_probe_paths` excluded only `_index`/`_vm_staging`/`backfill-logs`/
  `snapshots`, NOT `_migration_backup/` (or `_migration_backups/`, `_backups/`) — so the shallow descent picked the
  alphabetically-first child `_migration_backup/…/<non-partitioned>.parquet` and reported no `pipeline_mode=`/
  `asset_group=`.
- **FIX (shipped, pm PR#928)**: skip ALL `_`-prefixed meta trees generically (data partitions never start with `_`).
  After the fix, prediction correctly reads CF-3-partition GREEN.
- **Residual note**: CF-2-paths can still read RED when the probe samples `processed_candles/` (MDPS candle scheme
  validly omits `asset_group=` — the per-AG bucket name encodes the AG; raw_tick DOES carry it). This is a
  check-altitude nuance, not a data gap — do NOT "fix" it by stamping `asset_group=` into candle paths.

## Per-AG CF-state (fresh audits 2026-07-11, `market-data-tick-<AG>-prd`)

| AG             | rows  | manifest-content CFs                                                                                     | remaining work to E7-green → E8-delete                                                                                                                                                                                         |
| -------------- | ----- | -------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **prediction** | 755k  | **ALL GREEN** (CF-1/2/3/4/5/6/7/13/Era-B)                                                                | ✅ DONE. E8 tick-delete executing; residual audit REDs = CF-2-paths candle-scheme + CF-8 (both cross-cutting, not data gaps).                                                                                                  |
| **sports**     | 1.80M | CF-1/3/4/5/Era-B **GREEN**; CF-7 has `ODDS`/`odds` + `ODDS_MOVEMENT`/`odds_movement` **case-drift**      | CF-7 data_type case-normalise (relabel, migrator has `_CF7_DATA_TYPE_NORMALISE`); physical relabel VM (objects lack `pipeline_mode=` segment → CF-3-partition); then E8 delete `market-data-tick-sports`. Closest of the four. |
| **defi**       | 27.4M | CF-4 near-green (2,477 blank), CF-5 GREEN, Era-B GREEN; CF-1 string-schema; physical paths               | apply schema_version int (re-run fixed populator OR normalise `_index`); populate 2,477 blank source; physical relabel VM; E8.                                                                                                 |
| **cefi**       | 7.22M | CF-1 string-schema; **CF-4 source 54% blank (3.9M)**; CF-5 189,665 untyped; **Era-B 521,513 chain-rows** | biggest data-content gap: source backfill, CF-5 typed-reason, Era-B chain→trades reclassify (options_chain/futures_chain must be data_type=trades); schema int; relabel; E8.                                                   |
| **tradfi**     | 5.09M | CF-1 string-schema; CF-4 near-green (14,003 blank); **Era-B 242,210 chain-rows**                         | Era-B chain→trades; schema int; source top-up; physical relabel; E8. VM had OOM history — `canonical-migration-tradfi` on e2-standard-16 SPOT per master catalogue D3.                                                         |

**CF-8 (available_at)** is RED on ALL five AGs (column absent, `written_at` proxy present). This is a shared
point-in-time/lookahead concern owned by `predictions_lookahead_and_reader_migration_2026_06_20.md`, NOT a per-AG E7
blocker.

## Recurring-bug playbook (prediction's proven lessons → apply per AG)

1. **schema_version → int** (bug #1 above; populator now fixed — re-run or normalise the `_index`).
2. **CF-15 live-path templates** — the phantom reconciler only enumerated `pipeline_mode=batch_<source>/` prefixes and
   false-phantomed LIVE-captured cells at `live_<source>/` paths. FIXED in `possible_manifest`
   (`_canonical_pipeline_mode_prefixes` now emits batch AND live prefixes per non-legacy source, uac@83ed5765). Any AG
   with live captures benefits; re-run `--unphantom-only --apply` if an AG shows spurious `attempted_failed[phantom_…]`.
3. **Phantom bundle-atom exemption** — manifest-only bundle atoms (`MANIFEST_ONLY_BUNDLE_DATA_TYPES`) must be EXEMPT
   from the object-existence phantom check (they have no on-disk path segment). Prediction's
   `prediction_canonical_question_group` was wiped before this; check each AG for manifest-only atoms before an
   `--apply` phantom pass.
4. **data_type case-drift + exact-dup collapse** — e.g. prediction had `MARKET_LIFECYCLE` as an EXACT case-drift
   duplicate of `market_lifecycle` (same 2,280 keys) → drop uppercase; sports has `ODDS`/`odds`. Normalise data_type to
   canonical-lowercase and collapse dups (verify key-membership first, don't blind-relabel).
5. **Vestigial blank-`data_type` rows** — malformed atoms (an atom requires a data_type). Prediction had 17 → dropped.
6. **Era-B chain rows** — `options_chain`/`futures_chain` data_type must be 0 (chains write `data_type=trades` with the
   chain distinction in `instrument_type`). cefi 521k + tradfi 242k need this reclassify.
7. **CF-4 source population** — `record_captured(source=…)` is required; cefi has 54% blank. Backfill from the
   pipeline*mode `{mode}*{source}` or the venue→source map.
8. **Physical-path relabel is a VM `--apply`** — objects lacking `pipeline_mode=`/`asset_group=` segments (sports)
   require the migrator's operational relabel run (fleet-drain-gated), not a manifest-only fix.

## Remaining scope is VM-scale (documented, not a descope)

Each of cefi/defi/tradfi/sports still needs its operational migrator `--apply` (physical relabel) + rebuild + CF-audit +
legacy-bucket delete — hours-long, fleet-drain-gated VM runs (tracked in each AG's plan + the master catalogue).
`populate_v9` fix + the audit-tool fix + this playbook remove the shared blockers; the per-AG data-content fixes (Era-B,
source, CF-5, case-drift) are code+rebuild work homed in each AG plan.
