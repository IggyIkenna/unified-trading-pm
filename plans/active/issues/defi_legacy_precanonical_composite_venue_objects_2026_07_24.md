---
doc_type: issue
title:
  "DeFi corpus contains a legacy pre-hive-path population (composite `venue=X-Y` segment, no chain=/instrument_type=/
  data_type= segments) that is unparseable by rebuild_defi_manifest and completely invisible to the manifest — distinct
  from, and predating, the timestamp-glued-id defect class"
summary: >-
  Operator spotted a specific object
  (`raw_tick_data/by_date/day=2025-08-06/asset_group=defi/venue=ETHENA-ETHEREUM/ticks_migrated_20260418T162244Z.parquet`)
  and asked whether the canonicalization migrations this session claimed complete actually covered it. They did not —
  this is a structurally different, EARLIER category of legacy object than anything targeted this session. Confirmed via
  direct read: the object holds 1 real row (`data_type=oracle_prices`,
  `instrument_key=ETHENA-ETHEREUM:YIELD_BEARING:sUSDe`, a validly-formed canonical ID STRING) but sits at a path with no
  `chain=`, `instrument_type=`, or `data_type=` hive segments — `parse_hive_path()` returns `None` for it, so
  `rebuild_defi_manifest.py` counts it toward `unparseable` and it never gets ANY manifest row (not CAPTURED, not
  honest-absence). A bounded prefix probe on this ONE day found 8 sibling venues with the same composite-venue shape
  (AAVEV3-ETHEREUM, CURVE-ETHEREUM, ETHERFI-ETHEREUM, LIDO-ETHEREUM, MORPHO-ETHEREUM, UNISWAPV2/V3/V4-ETHEREUM) — this
  is a systemic pattern, not a one-off. The structural blind spot is already documented
  (`/codex/02-data/orphan-object-detection.md` §2d, "Blind spot 3") but this concrete population was never enumerated or
  swept.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer]
tags: [defi, canonicalisation, legacy, unparseable, orphan-objects, manifest-coverage, data-correctness]
related:
  - /plans/active/defi_consolidated_closeout_2026_07_18.md
  - /codex/02-data/orphan-object-detection.md
  - /plans/active/issues/canonical_path_oracle_blind_to_filename_stem_2026_07_20.md
  - /plans/active/issues/defi_lst_oracle_timestamp_glued_instrument_id_2026_07_20.md
created: 2026-07-24
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: data-engineer
drift_direction: none
depends_on: []
locked_by:
locked_since:
source: >-
  Operator question 2026-07-24, mid-session, prompted by a specific GCS path they encountered directly and asked whether
  it was really canonical / how downstream code reads it.
resolved_by:
context_scope:
  [
    /plans/archive/issues/defi_dex_pools_delete_order_stale_2026_07_20.md,
    /plans/archive/issues/defi_fold_manifest_registration_pending_2026_07_21.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    market-tick-data-service/market_tick_data_service/scripts/rebuild_defi_manifest.py,
    /codex/02-data/orphan-object-detection.md,
  ]
---

## What was found (measured, not inferred)

Object:
`gs://market-data-tick-defi-prd-central-element-323112/raw_tick_data/by_date/day=2025-08-06/asset_group=defi/venue=ETHENA-ETHEREUM/ticks_migrated_20260418T162244Z.parquet`

- Exists: yes. `Content-Length=4221`, `Storage class=COLDLINE`, `Creation time=2026-05-12`, `Update time=2026-06-27`.
- Content (downloaded + read directly): 1 row —
  `timestamp=2025-08-06T00:00:00Z, price_usd=1.0, source=aave_oracle, data_type=oracle_prices, instrument_key=ETHENA-ETHEREUM:YIELD_BEARING:sUSDe, date=2025-08-06`.
  The `instrument_key` column value is a validly-shaped canonical ID string (`VENUE-CHAIN:TYPE:SYMBOL`, matching the
  documented grammar) — the DATA is fine.
- Path shape: `.../asset_group=defi/venue=ETHENA-ETHEREUM/ticks_migrated_20260418T162244Z.parquet` — no `chain=`,
  `instrument_type=`, or `data_type=` segments at all; a generic (not per-instrument) filename. This predates the
  current canonical hive-path convention entirely (compare to a proper shard:
  `venue={venue}/chain={chain}/instrument_type={type}/data_type={dt}/{instrument_id}.parquet`).
- `market_tick_data_service.scripts.rebuild_defi_manifest.parse_hive_path()` called directly on this exact blob path
  returns `None`.
- Consequence, traced through `rebuild_defi_manifest.py`'s scan loop: a `None` parse result increments the `unparseable`
  counter and the object is `continue`d past — **it never reaches `emit_captured` or `emit_honest_absence`. Zero
  manifest representation of any kind.** This is a different, earlier failure mode than the timestamp-glued-id defect
  class (`defi_lst_oracle_timestamp_glued_instrument_id_2026_07_20.md`) — glued objects at least get a (wrong) CAPTURED
  row; these get none.
- Scale check (bounded — single day, NOT a corpus-wide walk, single-walk discipline preserved): listing
  `asset_group=defi/` for `day=2025-08-06` and filtering to entries lacking a `chain=` sub-segment found **9 distinct
  composite-venue directories**: `AAVEV3-ETHEREUM`, `CURVE-ETHEREUM`, `ETHENA-ETHEREUM`, `ETHERFI-ETHEREUM`,
  `LIDO-ETHEREUM`, `MORPHO-ETHEREUM`, `UNISWAPV2-ETHEREUM`, `UNISWAPV3-ETHEREUM`, `UNISWAPV4-ETHEREUM`. Every major DeFi
  venue this corpus tracks has at least one object in this legacy shape on this one sampled day — this reads as
  systemic, not an isolated artifact, though the TRUE total population size across the full 2020-2026 date range is NOT
  yet measured (would require either a manifest-driven query for `capture_status` absent + presence inference, or a
  bounded multi-day/multi-venue sample — NOT a fresh whole-corpus GCS walk, which is review-blocking per the single-walk
  discipline HARD RULE).

## Why this matters (scope correction on this session's completion claims)

This session ran a 6-VM full-corpus `rebuild_defi_manifest` sweep and separately fixed/verified a 0-glued-ids
precondition for the `_migrated_` marker delete gate. Neither of those efforts touched, measured, or claimed anything
about this category — they operate entirely on objects that already sit at a canonical (or near-canonical,
glued-filename) hive path. This population sits OUTSIDE that scope structurally (the objects were never parseable in the
first place, so they never entered the manifest for either effort to see). Confirming or fixing this is **net-new
scope**, not something this session's "0 glued ids" or "6 VMs complete" claims cover, and should not be read as implying
it.

## What is NOT claimed

- The true corpus-wide population size (could be dozens, could be thousands — one day's 9-venue sample is not a
  corpus-wide count).
- Whether ALL objects in this legacy shape are as small/single-row as the ETHENA sample, or whether some carry
  substantial real historical data currently completely absent from coverage reporting.
- Whether this predates the 2026-06-18 DeFi foundational migration (`canonical-migration-defi-20260618-180603`) or is a
  separate legacy tree the foundational migration didn't sweep — not traced.
- A fix design — this issue is the finding + scoping, not a remediation plan.

## 2026-07-28 update — parquet content sampled across all 9 venues x 5 days (43 objects)

Per `defi_satellite_ao_dispatch_batch1_2026_07_25.md`'s `[DIAG] P1` todo, downloaded and read the actual parquet content
(not just object size/metadata) for every one of the 9 known composite-venue objects across 5 sampled days
(`2024-06-15`, `2025-01-15`, `2025-03-15`, `2025-06-01`, `2025-08-06` — bounded, not a corpus-wide walk; UNISWAPV4 only
present from `2025-03-15` onward, giving 43 objects total). Bucket:
`gs://market-data-tick-defi-prd-central-element-323112`.

**Distribution: 5/43 sampled objects (all ETHENA-ETHEREUM) are single-row-scale; 38/43 (8 of the 9 venues) carry
substantial multi-row historical data.** The single-ETHENA-row assumption in this doc's original scoping does NOT
generalize to the other 8 venues:

| venue              | rows/day (range across sample) | data_type(s)                                          | distinct instrument_keys |
| ------------------ | ------------------------------ | ----------------------------------------------------- | ------------------------ |
| ETHENA-ETHEREUM    | 1 (every day)                  | oracle_prices                                         | 1                        |
| LIDO-ETHEREUM      | 96 (constant)                  | oracle_prices                                         | 1                        |
| CURVE-ETHEREUM     | 96–950                         | liquidity(, swaps from 2025-08)                       | 1–7                      |
| ETHERFI-ETHEREUM   | 97 (constant)                  | oracle_prices, rewards                                | 1                        |
| MORPHO-ETHEREUM    | 240–724 (growing)              | rate_indices, utilization                             | 25–49                    |
| AAVEV3-ETHEREUM    | 2920–2929 (constant)           | oracle_prices, rate_indices, risk_params, utilization | 40–50                    |
| UNISWAPV2-ETHEREUM | 3030–10878                     | liquidity, swaps                                      | 17–18                    |
| UNISWAPV4-ETHEREUM | 6062–12393                     | liquidity, swaps                                      | 40–67                    |
| UNISWAPV3-ETHEREUM | 24563–53854 (largest)          | liquidity, swaps                                      | 138–155                  |

Full per-object table (day, venue, filename, size, row count, data_types, distinct keys, ts range) — 43 rows — is
recorded in the session transcript for `defi_satellite_ao_dispatch_batch1-018`/`-020`; reproducible via
`google.cloud.storage.Client.list_blobs()` + `pandas.read_parquet()` over the 9 venue prefixes x the 5 sample days above
(no new tooling needed).

**Secondary finding — filename pattern split.** 8 of the 9 venues' objects carry a `ticks_migrated_20260418T*.parquet`
filename (a fixed migration-run timestamp, `2026-04-18`), consistent with a single one-time backfill/migration batch.
UNISWAPV4-ETHEREUM's objects are instead named plain `ticks.parquet` — no migration-run timestamp. Checked whether this
means UNISWAPV4 is an ACTIVELY GROWING leak into this legacy shape (as opposed to a frozen historical artifact): probed
`day=2026-07-20/2026-07-25/2026-07-27` (near-present) for `venue=UNISWAPV4-ETHEREUM/` under this same non-canonical
prefix — **zero objects found**, and the sampled `ticks.parquet` objects' own GCS `Creation time` is `2026-05-12` (same
batch/day as the other 8 venues' `_migrated_` objects, confirmed via `gcloud storage ls -l`). So this is NOT an active
ongoing writer bug — just a naming inconsistency WITHIN the same one-time 2026-05-12 migration batch (UNISWAPV4
presumably came from a different source script in that batch that didn't apply the `_migrated_<ts>` naming convention
the other 8 got). Flagging for whoever executes the fold: UNISWAPV4's objects need the same fold treatment but won't
match a filename-pattern-based `_migrated_` selector if one is used — must select by path shape (missing
`chain=`/`instrument_type=`/`data_type=` segments), not by filename.

**Answers the fold-vs-migrate decision's data prerequisite**: this is NOT a "handful of trivial single-row objects" —
it's substantial captured historical data (up to ~54k rows/day for UNISWAPV3) sitting completely outside manifest
coverage. A "some other disposition" (delete/ignore) reading of the operator decision below would silently discard real
historical DeFi tick data; fold (re-derive the canonical path from each object's own `instrument_key`/`data_type`
columns) is the only disposition that doesn't lose data, for at least the 8 non-ETHENA venues.

## 2026-07-28 update — true corpus-wide scale measured (5,332 objects, bounded scoped scan)

Per `defi_satellite_ao_dispatch_batch1_2026_07_25.md`'s `[DATA] P1` scale todo. Method: a BOUNDED, scoped listing per
known composite venue —
`gcloud storage ls "gs://market-data-tick-defi-prd-central-element-323112/raw_tick_data/by_date/day=*/asset_group=defi/venue={V}/**"`
for each of the 9 already-enumerated venue names (AAVEV3-ETHEREUM, CURVE-ETHEREUM, ETHENA-ETHEREUM, ETHERFI-ETHEREUM,
LIDO-ETHEREUM, MORPHO-ETHEREUM, UNISWAPV2-ETHEREUM, UNISWAPV3-ETHEREUM, UNISWAPV4-ETHEREUM), run in parallel
(~70s/venue, all 9 completed in one batch). This is a **prefix-scoped listing bounded to the 9 known venue names**, NOT
a fresh whole-corpus GCS walk — single-walk discipline preserved (the walk is pruned to exactly the 9 composite `venue=`
directories already identified, never touching the canonical `venue=` tree).

**Total: 5,332 objects** — AAVEV3-ETHEREUM=632, CURVE-ETHEREUM=631, ETHENA-ETHEREUM=631, ETHERFI-ETHEREUM=631,
LIDO-ETHEREUM=631, MORPHO-ETHEREUM=557, UNISWAPV2-ETHEREUM=632, UNISWAPV3-ETHEREUM=628, UNISWAPV4-ETHEREUM=359.

**Corrects the "full 2020-2026 defi date range" framing in this doc's original scoping**: every venue's object dates
cluster tightly in **2024-05-02 through 2026-01-24** (UNISWAPV4 narrower still, 2025-01-30 onward) — roughly 20 months,
not the full ~6.5-year corpus history. This is consistent with (and now fully explains) the earlier finding that all
objects share a single `Creation time=2026-05-12` GCS timestamp and `ticks_migrated_<batch-ts>`/`ticks.parquet`
filenames from one one-time migration batch: that batch evidently only ever covered this ~20-month source window, so the
legacy population's true bound is ~20 months × 9 venues, not 6.5 years × 9 venues. Days-with-an-object per venue run
557–632 out of the ~630-day window (not every calendar day has an object for every venue — gaps exist, not investigated
further here as out of this todo's scope).

**Scale prerequisite for the `[OPERATOR]` fold-vs-migrate decision below is now satisfied**: 5,332 objects, combined
with the 2026-07-28 distribution finding above (38/43 sampled objects carry substantial multi-row data, up to ~54k
rows/day for UNISWAPV3), means fold would recover real, non-trivial historical DeFi tick data currently invisible to the
manifest — both prerequisite facts (scale + distribution) are now in hand for that decision.

## Todos

- [x] [DATA] P1. Measure the true scale of this legacy population — either extend `rebuild_defi_manifest`'s own
      `unparseable` counter into a logged sample of the actual unparseable paths (cheap — the counter already exists, it
      just isn't currently surfacing WHICH paths hit it), or run a manifest-driven cross-check (days/venues with real
      GCS presence per a bounded listing vs. zero manifest rows for that venue/day). Definition-of-done: a real count
      (or a tight bounded estimate) of how many objects across the full date range carry this legacy composite- venue
      shape, cited against the method used (not a fresh whole-corpus GCS walk — single-walk discipline applies). —
      already covered by defi_satellite_ao_dispatch_batch1_2026_07_25.md (see that doc for execution).
- [x] [DIAG] P1. Gather the fact needed for the fold-vs-migrate decision below: for a sample of objects in this legacy
      shape (beyond the single ETHENA example already confirmed), read the parquet content directly and confirm whether
      they are all small (1-row-scale) valid-data objects like the ETHENA sample, or whether some carry substantial
      historical data. Definition-of-done: a stated distribution (e.g. "N of M sampled objects are single-row", or a
      size histogram) that the decision todo below can be answered against. — already covered by
      defi_satellite_ao_dispatch_batch1_2026_07_25.md (see that doc for execution).
- [ ] [DATA] P1. **Retagged from [OPERATOR] 2026-07-28** (auto-resolvable under the existing self-service rules — no
      fresh operator ask needed): both prerequisite facts (scale + distribution) are in hand (see the two 2026-07-28
      updates above), and this corpus already has an operator-approved, validated fold pattern for structurally the same
      problem — the 2026-07-21 `dex_pools/`+`lending_indices/` fold
      (`/plans/archive/issues/defi_dex_pools_delete_order_stale_2026_07_20.md`, resolved: 648 legacy-only twins folded
      to canonical + verified, reader repointed, operator prod-deleted) plus its manifest-registration recipe
      (`/plans/archive/issues/defi_fold_manifest_registration_pending_2026_07_21.md`: one `record_captured` row per
      folded instrument, NOT a re-derive-from-GCS assumption). **Execute the non-destructive fold**: for each of the
      5,332 legacy composite-venue objects, parse the parquet's own `instrument_key`/`data_type` columns to derive the
      correct canonical hive path
      (`venue={venue}/chain={chain}/instrument_type={type}/data_type={dt}/{instrument_id}.parquet`), copy to that path,
      verify content parity, then register a `record_captured` manifest row per the same recipe (do NOT rely on the
      consolidator to re-derive rows from raw GCS — it only merges `record_captured` shards). **Leave the old legacy
      objects un-deleted and unregistered** — the delete-the-legacy-copies decision is a distinct, later todo gated on
      finding T's fresh `gcs_bucket_soft_delete_retention_seconds()` reversibility check (or explicit operator
      sign-off), not this one.
- [ ] [PM] P2. File a proper migration plan once scale + the fold-vs-migrate decision are both in hand — this issue doc
      is the scoping step per CLAUDE.md's findings triage ("audit-scope → wrapper plan"), not the execution surface.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid - the [PM] todo is 'file a proper migration plan'
  (plan-destination operator ask) and the doc's own text calls itself the scoping step, not the execution surface
- **context-scout 2026-08-01**: populated context_scope (5 entries).
