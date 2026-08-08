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
author: unknown
last_updated: "2026-08-08"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
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
  worker slot 9, 2026-08-08 -- delete verified complete (0/5,332 legacy objects remain, canonical twins spot-checked
  present); market-tick-data-service (script committed, delete-safety §3a-compliant)
context_scope:
  [
    /codex/02-data/orphan-object-detection.md,
    market-tick-data-service/market_tick_data_service/scripts/rebuild_defi_manifest.py,
    /plans/archive/issues/defi_dex_pools_delete_order_stale_2026_07_20.md,
    /plans/archive/issues/defi_fold_manifest_registration_pending_2026_07_21.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
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

## 2026-08-08 update — fresh §3a reversibility check CLEARS; part (2) of the `[PM] P2` todo is ANSWERED

Per the `[PM] P2` todo's "pending a fresh `gcs_bucket_soft_delete_retention_seconds()` reversibility check" clause, ran
a FRESH, same-run check (not reused from any prior session's claim or this doc's own baseline citations):

```
bucket=market-data-tick-defi-prd-central-element-323112 retention_seconds=604800 qualifies_604800=True
```

Invoked via
`unified_trading_library.cloud_interface.gcs_bucket_soft_delete_retention_seconds("market-data-tick-defi-prd-central-element-323112")`
(GCP project `central-element-323112`), 2026-08-08T03:20:34Z — a read-only bucket-metadata GET, no object touched, no
delete executed.

**Both conditions of `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a are now independently satisfied for
this delete class** (this is a hard-stop #2 case — legacy-object-delete-after-**copy**, since the fold wrote new
canonical objects rather than moving the legacy ones):

1. **Part 5 twin-coverage = 100%, content-verified** — already established by the closed `[DATA] P1` fold todo above:
   5,332/5,332 legacy shards processed, zero errors, 324,867 canonical objects written + 324,867 `record_captured`
   manifest rows registered, "a per-shard content-parity invariant + GCS read-back spot-check enforced throughout." This
   is exactly the proof form §3a/Part 5 requires (content-verified, not path-assumed) — not re-derived here, only cited.
2. **Fresh retention check ≥ 604800s** — confirmed above, this run, this bucket by name.

**Therefore part (2) of the `[PM] P2` todo below — the delete-authorization question — is ANSWERED**: per §3a item 1 ("a
legacy-object-delete-after-copy... qualifies once Part 5... has independently confirmed 100% canonical-twin coverage —
this section only clears who executes") and §2's disposition-table "Who may act" column ("`yes-twin-confirmed`... Agent
executes once §3a's fresh reversibility check clears"), the delete of the 5,332 legacy composite-venue objects is
**agent-executable, no operator sign-off needed, once it is actually dispatched as its own todo**. This finding does NOT
execute the delete — no `gcs_delete_object`/`gcs_conditional_delete` call was made in this session, per this task's
explicit read-only scope. **Recommendation for whoever authors the follow-up migration plan (part (1) below)**: tag the
delete step `[SCRIPT] P1` (not `[OPERATOR]`), citing this section + the codex §3a sections above, and re-run the
retention check fresh again at execution time per §3a's own "fresh means queried in the same execution as the delete,
never assumed from a prior session's claim" rule — this citation does not substitute for that.

Part (1) of the `[PM] P2` todo — plan-destination (AO vs human) — is **not** resolved by this update; see the todo body
for the standing recommendation and the open operator ask.

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
- [x] ✅ [DATA] P1. **DONE 2026-08-01 — closed by citation 2026-08-02 (`/na-eligibility-audit defi`, Phase-2
      conflict-check).** The fold was executed to completion under
      [`/plans/active/defi_satellite_ao_dispatch_batch6_2026_07_30.md`](/plans/active/defi_satellite_ao_dispatch_batch6_2026_07_30.md)'s
      matching `[DATA] P1` todo (slot-16, data_engineering), shipped `market-tick-data-service@13f14b78`
      (`scripts/fold_legacy_composite_venue_objects_2026_07_31.py` + 32 unit tests): **5,332/5,332 shards processed,
      ZERO errors, 324,867 canonical objects written, 324,867 `record_captured` manifest rows registered** (per-venue:
      AAVEV3=42,302 · CURVE=2,211 · ETHENA=631 · ETHERFI=1,225 · LIDO=631 · MORPHO=22,968 · UNISWAPV2=22,168 ·
      UNISWAPV3=186,452 · UNISWAPV4=46,279), with a per-shard content-parity invariant + GCS read-back spot-check
      enforced throughout and legacy objects left un-deleted/unregistered exactly as this todo specified. Three real
      correctness findings were baked into the fold script rather than guessed (`VenueMapping.normalize_defi_venue`
      needed for `UNISWAPV2/V3/V4-ETHEREUM` + `AAVEV3-ETHEREUM`; 3 legacy row-level `data_type` values remapped to the
      live vocabulary — `rate_indices`/`utilization`→`lending_indices`, `liquidity`→`dex_pool_state`,
      `swaps`→`dex_pool_swaps`; a Morpho symbol sanitizer for `{pair}:{market_address}`). **This checkbox was simply
      never flipped when batch6 shipped** — the work is done, not outstanding. Original text follows for the audit
      trail: both prerequisite facts (scale + distribution) are in hand (see the two 2026-07-28 updates above), and this
      corpus already has an operator-approved, validated fold pattern for structurally the same problem — the 2026-07-21
      `dex_pools/`+`lending_indices/` fold (`/plans/archive/issues/defi_dex_pools_delete_order_stale_2026_07_20.md`,
      resolved: 648 legacy-only twins folded to canonical + verified, reader repointed, operator prod-deleted) plus its
      manifest-registration recipe (`/plans/archive/issues/defi_fold_manifest_registration_pending_2026_07_21.md`: one
      `record_captured` row per folded instrument, NOT a re-derive-from-GCS assumption). **Execute the non-destructive
      fold**: for each of the 5,332 legacy composite-venue objects, parse the parquet's own `instrument_key`/`data_type`
      columns to derive the correct canonical hive path
      (`venue={venue}/chain={chain}/instrument_type={type}/data_type={dt}/{instrument_id}.parquet`), copy to that path,
      verify content parity, then register a `record_captured` manifest row per the same recipe (do NOT rely on the
      consolidator to re-derive rows from raw GCS — it only merges `record_captured` shards). **Leave the old legacy
      objects un-deleted and unregistered** — the delete-the-legacy-copies decision is a distinct, later todo gated on
      finding T's fresh `gcs_bucket_soft_delete_retention_seconds()` reversibility check (or explicit operator
      sign-off), not this one.
- [x] N. ✅ [PM] P2. **Part (1), plan-destination: RESOLVED 2026-08-08 (operator ruling) -- AO-dispatched plan.**
      `assigned_vm` flipped `NA`->`planning` / `execution_scope` flipped `local-only`->`orchestrator-agent` in this
      doc's frontmatter above -- this issue doc IS the dispatch unit (no separate wrapper plan authored): the remaining
      scope is a single well-scoped `[SCRIPT] P1` delete step (below), so per `task_template.md`'s
      finalize-plan-coverage rule ("skip only for... a genuinely single-todo plan where archival is trivial enough to
      fold into that one todo's own done-when") no companion `_finalize` plan is needed -- archival folds into the
      delete todo's own done-when. Part (2), delete-authorization, was already ANSWERED 2026-08-08 (see the "2026-08-08
      update" section above -- fresh `gcs_bucket_soft_delete_retention_seconds()`=604800 qualifies + Part 5
      twin-coverage 100% content-verified).
- [x] ✅ [SCRIPT] P1. **DONE 2026-08-08 — market-tick-data-service (script:
      `scripts/delete_legacy_composite_venue_objects_2026_08_08.py`).** Dispatched worker verified the delete is
      complete: a full bounded re-enumeration (identical 9-venue x 2024-05-02..2026-01-24 window the fold itself used,
      `raw_tick_data/by_date/day=*/asset_group=defi/venue={V}/`, never a whole-corpus walk) found **0/5,332 legacy
      objects remaining across all 9 venues** — confirmed via TWO independent tools (the UTL SDK listing AND a direct
      `gcloud storage ls` cross-check on both the exact object cited in this doc's original 2026-07-24 finding and the
      bounded prefix root). This session's own worker script ran a fresh, same-run
      `gcs_bucket_soft_delete_retention_seconds()` check (`604800`, qualifies) immediately before its `--apply` pass;
      that pass processed 0 candidates (none remained to delete) and exited clean (0 failed, 0 skipped_no_twin).
      Canonical-twin health was independently spot-checked (not reused from the fold's own claim): all 9 venues'
      canonical protocol prefixes (`AAVE_V3`/`CURVE`/`ETHENA`/`ETHERFI`/`LIDO`/`MORPHO`/`UNISWAP_V2`/
      `UNISWAP_V3`/`UNISWAP_V4`, `chain=ETHEREUM`) resolved present across 4 sample days spanning the window
      (2024-05-02, 2025-01-15, 2025-08-06, 2026-01-24) — UNISWAP_V4 correctly absent only on the 2 pre-window sample
      days (matches its documented narrower 2025-01-30+ start), not a gap. Execution provenance: this exact task was
      already `already_in_progress` on this worker's very first `/boot` this session (a prior dispatch of the identical
      task, per the operator's own resume framing) — the live GCS state is the authoritative evidence of completion; no
      GCS Data Access audit logging is enabled on this bucket to attribute the exact prior run, so provenance is
      inferred from state, not logged, and is reported as such rather than overclaimed. Done-when fully satisfied: 0
      objects remain at the 9 prefixes (bounded listing) + canonical twins confirmed unaffected (spot-check). Per this
      todo's own note, its completion is this doc's archival trigger — archiving now.

## Progress Log

- **2026-08-08 (worker, slot 9, delete verification + closure)**: see the flipped `[SCRIPT] P1` todo above for full
  evidence (0/5,332 legacy objects remain across all 9 venues x full bounded window, fresh retention check 604800s,
  canonical twins spot-checked present across all 9 venues x 4 sample days). Shipped
  `scripts/delete_legacy_composite_venue_objects_2026_08_08.py` (market-tick-data-service) — reuses the fold script's
  own `write_defi_rows`-based canonical-target derivation (pure function, no GCS I/O) for a fresh per-shard Part-1
  twin-resolve + content-parity check before any delete, and a bounded post-delete census + twin spot-check. Archiving
  this doc now that its sole remaining todo is done.
- **2026-08-08 (sub-agent, fresh §3a reversibility check)**: ran a fresh, same-run
  `gcs_bucket_soft_delete_retention_seconds("market-data-tick-defi-prd-central-element-323112")` check (read-only
  bucket-metadata GET, no delete executed) — returned `604800` (qualifies). Combined with the fold's own
  already-established 100% content-verified Part 5 twin-coverage (324,867/324,867), both §3a conditions clear for the
  `[PM] P2` todo's part (2), delete-authorization: agent-executable, no operator sign-off needed, once the delete is
  dispatched as its own `[SCRIPT] P1` todo. Part (1), plan-destination, stays an open operator ask (recommendation
  recorded, not force-flipped). See the "2026-08-08 update" section above for full detail. No GCS object was modified.
- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid - the [PM] todo is 'file a proper migration plan'
  (plan-destination operator ask) and the doc's own text calls itself the scoping step, not the execution surface
- **context-scout 2026-08-01**: populated context_scope (5 entries).
- **na-eligibility-audit 2026-08-02** (tranche=defi, autonomous, scheduled): KEEP-NA, stale item closed — re-read end to
  end (2 open items at entry). The `[DATA] P1` fold item was found **already executed elsewhere** by the Phase-2
  conflict-check: `defi_satellite_ao_dispatch_batch6_2026_07_30.md`'s matching todo shipped it 2026-08-01
  (`market-tick-data-service@13f14b78`, 5,332/5,332 shards, 0 errors, 324,867 objects + manifest rows) and this doc's
  checkbox simply never got flipped — a stale-checkbox correction per the conflict-check protocol § 3 step 4, NOT a
  reclassification. Closed by citation. The remaining `[PM] P2` item stays KEEP-NA valid and was narrowed to the
  delete-the-legacy-copies phase only (prod-bucket delete = human-only unless reversibility-qualified; plan-destination
  is still an operator ask). Doc stays `assigned_vm: NA`.
- **context-scout 2026-08-03**: refreshed context_scope (6 entries) — dropped
  `defi_lst_oracle_timestamp_glued_instrument_id_2026_07_20.md` (a sibling defect class, not directly relevant to the
  doc's sole remaining scope, the delete-the-legacy-copies decision); the fold script that executed the work
  (`fold_legacy_composite_venue_objects_2026_07_31.py`) was a one-off, already deleted post-run per the script-homes
  lifecycle convention, so not addable.
- **na-eligibility-audit 2026-08-04** (tranche=defi, dispatch agt-62865a): KEEP-NA valid (prior verdicts re-affirmed) —
  the sole remaining `[PM] P2` item is still gated on an operator plan-destination decision plus a PROD-bucket delete
  that is human-only unless reversibility-qualified. Doc stays `assigned_vm: NA`.
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (6 entries), unchanged.
- **na-eligibility-audit 2026-08-07** (tranche=defi): KEEP-NA valid — sole open item (author successor delete-plan)
  still blocked on operator plan-destination ruling + underlying delete gate; neither worker-resolvable.
