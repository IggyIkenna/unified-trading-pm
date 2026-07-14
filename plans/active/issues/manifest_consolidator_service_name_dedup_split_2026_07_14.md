---
doc_type: issue
title:
  'manifest_consolidator: the TEAMS `expected_unattempted`-won''t-drop symptom is a `service_name` dedup-key split, NOT
  the plan''s diagnosed optional-column NULL/`""`-normalization gap (that normalization has been complete + correct
  since unified-trading-library@f5ec2291, 2026-07-06) — reproduced locally'
summary:
  'data_engineering investigation (slot-5, 2026-07-14) of sports_data_sources_canonical_completion task -016. The
  plan''s P1 todo attributes the TEAMS `expected_unattempted` count not dropping after the 61-league backfill to a
  NULL-vs-empty dedup-key normalization gap across optional dimension columns
  (chain/instrument_type/instrument_id/quote_asset/ margin_type/combo_type/fixture_id/job_id). VERIFIED FALSE:
  `manifest_consolidator._dedup_key_sql` already collapses NULL == '''' for every dedup-key column via the `part_norm`
  used in EVERY `PARTITION BY` (incl. the `--force` full-rebuild path at line 2324), and it landed 2026-07-06 (f5ec2291)
  — BEFORE the 2026-07-13 observation. The REAL, reproduced root cause: the backfill script writes
  `service_name="backfill-teams-61-leagues"` (backfill_teams_61_leagues_2026_07_13.py:212,230) while the enumerator
  `expected_unattempted` seed writes `service_name="instruments-service"`. `service_name` is a BASE dedup key
  (consolidator SSOT line 152), so the two twin rows land in DIFFERENT dedup groups and the captured row can never
  supersede its seed. The plan''s own aggregate proof (165,148 TEAMS `(source,data_type,league_id,date,venue)` keys with
  >1 distinct capture_status — a key that EXCLUDES service_name) is exactly the signature of a service_name-only split.
  Fixing this is a fleet-wide dedup-key semantics decision (does service_name belong to cell IDENTITY or to PROVENANCE,
  like `source` which was already excluded from the key?) and needs an operator ruling before any code lands.'
status: blocked
nature: notes
asset_group: [cross-cutting, defi, cefi, tradfi, prediction, sports, meta]
stage: [meta]
repos: [unified-trading-library, instruments-service]
scope: [engineer, admin]
tags:
  [manifest-consolidator, dedup-key, service_name, expected_unattempted, sports, teams, data-correctness, misdiagnosis]
related: [../sports_data_sources_canonical_completion_2026_07_13.md, ../understat_bulk_download_backfill_2026_06_29.md]
created: 2026-07-14
parent_epic: infrastructure_master
priority: P1
source:
  "data_engineering worker (slot-5, planning VM), 2026-07-14, executing AO task
  sports_data_sources_canonical_completion-016. Static code read + git-blame of unified_trading_library/
  manifest_consolidator.py + a local DuckDB reproduction of the exact `part_norm` PARTITION BY over the AUSTRALIA_CUP/
  2020-05-15 twin row-pair, plus confirmation of the two service_name values in source."
assigned_vm: planning
locked_by:
resolved_by:
execution_scope: local-only
model_tier: sonnet-doable
---

## What I found

The plan `sports_data_sources_canonical_completion_2026_07_13.md` P1 todo -016 ("manifest_consolidator dedup-key
NULL/`""`-normalization gap") states that TEAMS `expected_unattempted` didn't drop after the 61-league backfill because
several optional dimension columns (`chain`/`instrument_type`/`instrument_id`/`quote_asset`/`margin_type`/`combo_type`/
`fixture_id`/`job_id`) differ between `None` (enumerator seed) and `""` (captured backfill rows), so DuckDB's dedup
`PARTITION BY` never groups the captured row with its `expected_unattempted` seed twin.

**This diagnosis is incorrect.** Two independent proofs:

1. **The NULL/`""` normalization already exists and is complete.** `manifest_consolidator._dedup_key_sql(col)` =
   `coalesce(nullif(cast(col AS VARCHAR), ''), '<sentinel>')` collapses BOTH NULL and `""` to one sentinel. It is
   applied to EVERY dedup-key column via `part_norm = ", ".join(_dedup_key_sql(c) for c in dedup)`
   (manifest_consolidator.py:2049), and `part_norm` is used in EVERY `PARTITION BY` in the file — the incremental
   anti-join AND the `--force` full-rebuild window (line 2324, which is the path the plan's `--force` rebuild took). It
   landed in `f5ec2291` on **2026-07-06**, a week BEFORE the 2026-07-13 observation. So at observation time, optional
   columns already collapsed NULL == "".

2. **Local reproduction of the exact partition.** Replaying the consolidator's `_dedup_key_sql` + `_resolve_dedup_cols`
   - `part_norm` over the AUSTRALIA_CUP/2020-05-15 twin row-pair the plan cites: the optional columns
     (chain/instrument_type/instrument_id) with NULL vs `""` BOTH normalize to `__UTL_CONSOLIDATOR_NULL_4e8a2__` — they
     do NOT split. The rows split into 2 dedup groups **solely because of `service_name`**: `backfill-teams-61-leagues`
     (captured) vs `instruments-service` (seed). Dropping `service_name` from the key collapses them to 1 group.

**The real root cause:** `service_name` is a BASE dedup key
(`_BASE_DEDUP_COLS = (date, venue, data_type, service_name)`; consolidator SSOT line 152). The backfill script
deliberately instantiates `ManifestWriter(service_name="backfill-teams-61-leagues")`
(`instruments-service/scripts/ backfill_teams_61_leagues_2026_07_13.py:212,230`), a different value from the enumerator
seed's `instruments-service`. Two genuinely-distinct, non-empty `service_name` values → different dedup groups → the
captured row never enters the same group as its `expected_unattempted` seed, so the existing "captured outranks recency"
tie-break (unified-trading-library@a05d69c7) never fires. The plan's own aggregate metric — 165,148 TEAMS
`(source,data_type,league_id,date,venue)` keys with >1 distinct capture_status, on a key that EXCLUDES `service_name` —
is precisely the fingerprint of a service_name-only split.

## Why it matters

- **The task as written cannot succeed.** Extending `_dedup_key_sql`/`_OPTIONAL_DEDUP_COLS` to the remaining optional
  columns (the plan's prescribed fix) is a no-op for this symptom (those columns are not the splitter) and is
  directionally counter-productive: adding a column to the dedup key can only ADD split axes, never remove the
  `service_name` one. Shipping it would flip the checkbox on false progress while `expected_unattempted` stays inflated.
- **Fleet-wide data-correctness.** Any backfill/one-off that writes a distinct `service_name` for a cell already seeded
  by the main service will leave permanent non-collapsing `expected_unattempted` twins across EVERY asset_group, not
  just sports. This understates real captured coverage on every coverage gate/UI that reads the manifest.

## Reproduction

`scratchpad/repro_dedup.py` (local, no GCS needed) — builds the two twin rows, applies the current `part_norm`, prints:
`distinct dedup groups: 2 => SPLIT`; and with `service_name` removed from the key: `1 => COLLAPSE`. The optional-column
sentinels are identical across both rows (proving they are not the splitter).

## Recommended decision (operator ruling required — fleet-wide dedup semantics)

The core question: **is `service_name` cell IDENTITY or PROVENANCE?** The consolidator already treats `source` (vendor)
as provenance and deliberately EXCLUDES it from the dedup key (manifest_consolidator.py:2106-2108: "source is vendor
provenance, not venue identity — collapsing two vendors' rows for one cell is CORRECT for coverage purposes"). By the
same logic `service_name` = which service/script wrote the row = provenance, and two services capturing the same
`(date, venue, data_type, +optional dims)` cell should collapse for coverage.

- **Option A (recommended): exclude `service_name` from the consolidator dedup key** (drop it from `_BASE_DEDUP_COLS`,
  and from the writer's mirror), exactly as `source` already is. The status-aware tie-break then keeps the captured
  survivor; its `service_name` provenance is preserved on the winning row. Cleanest, principled, matches the `source`
  precedent. Requires a rule-11 fleet blast-radius proof (confirm no asset_group legitimately keeps DISTINCT-coverage
  rows that differ ONLY on service_name) — and that proof needs GCS/ADC read access this slot currently lacks.
- **Option B: status-aware cross-`service_name` collapse only.** Keep `service_name` in the key for the general case,
  but when a `captured` row and a non-captured row are identical on all OTHER dedup dims, collapse them keeping the
  captured one (mirrors the existing source-aware `row_count` collapse). More surgical, preserves multi-service cells,
  but more complex SQL and murkier semantics.
- **Option C: data remediation only.** Rewrite the 165,148 backfill rows' `service_name` to `instruments-service` so
  they collapse under the current key. One-off, does NOT prevent recurrence, and contradicts the plan's own ruling
  (lines 120-128) that the custom `service_name` is "honest provenance… NOT a service_name-drift bug."

## Todos (gated on the operator ruling above)

- [ ] [DATA] P1. Apply the operator-chosen fix (A/B/C) to `unified_trading_library/manifest_consolidator.py`'s dedup key
      (+ the writer mirror `manifest_writer/_writer_io.py::_OPTIONAL_DEDUP_DIMS_NULL_NORMALIZE` / `_rows.py` if the key
      set changes), with a rule-11 blast-radius proof against a representative sample from ≥2 non-sports asset_groups
      before landing (repo: unified-trading-library). BLOCKED-OPERATOR-DECISION until the identity-vs-provenance ruling
      is given.
