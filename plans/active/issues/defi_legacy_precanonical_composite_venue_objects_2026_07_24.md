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

## Todos

- [ ] [DATA] P1. Measure the true scale of this legacy population — either extend `rebuild_defi_manifest`'s own
      `unparseable` counter into a logged sample of the actual unparseable paths (cheap — the counter already exists, it
      just isn't currently surfacing WHICH paths hit it), or run a manifest-driven cross-check (days/venues with real
      GCS presence per a bounded listing vs. zero manifest rows for that venue/day). Definition-of-done: a real count
      (or a tight bounded estimate) of how many objects across the full date range carry this legacy composite- venue
      shape, cited against the method used (not a fresh whole-corpus GCS walk — single-walk discipline applies).
- [ ] [DIAG] P1. Gather the fact needed for the fold-vs-migrate decision below: for a sample of objects in this legacy
      shape (beyond the single ETHENA example already confirmed), read the parquet content directly and confirm whether
      they are all small (1-row-scale) valid-data objects like the ETHENA sample, or whether some carry substantial
      historical data. Definition-of-done: a stated distribution (e.g. "N of M sampled objects are single-row", or a
      size histogram) that the decision todo below can be answered against.
- [ ] [OPERATOR] P1. **Decision needed**: fold (migrate each object onto its correct canonical path, parsing the
      parquet's own `instrument_key`/`data_type` columns to re-derive it) vs. some other disposition — gated on the
      scale + sample-distribution facts from the two todos above. This is a genuine judgment call, not a mechanical fix
      (per task_template.md's bounded-outcome rule) — do not execute a fold/migrate without this decision.
- [ ] [PM] P2. File a proper migration plan once scale + the fold-vs-migrate decision are both in hand — this issue doc
      is the scoping step per CLAUDE.md's findings triage ("audit-scope → wrapper plan"), not the execution surface.
