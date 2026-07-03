---
doc_type: issue
title:
  cefi Layer-1 denominator silently omits whole venues with real captured data (gate-authority gaps + one writer itype
  mis-stamp)
summary:
  'Found 2026-07-03 while implementing the UAC↔writer matrix reconciliation: the cefi Layer-1 EXPECTED matrix (44
  tuples) substantially under-counts the real could-exist universe. Two gate authorities silently zero-out whole venues:
  (1) the (venue,itype) gate reads VenueMapping.venue_instrument_type_to_tardis, which lacks the Tier-3 venues
  (BITFINEX-SPOT/BITGET-*/KRAKEN-SPOT) and all non-Tardis venues
  (HYPERLIQUID/ASTER/EXTENDED-STARKNET/PACIFICA/LIGHTER/KALSHI-PERP/POLYMARKET-PERP) — venues with REAL captured data
  get expected=0/0; (2) venues wholly absent from VENUE_DATA_TYPE_CAPABILITIES
  (BINANCE-DELIVERY/DERIBIT-COMBO/BYBIT-SPOT/COINBASE-FUTURES/KALSHI-PERP/POLYMARKET-PERP/PACIFICA/EXTENDED/LIGHTER)
  have every data_type carved out. Separately, the MTDS writer stamps BYBIT-SPOT rows instrument_type=PERPETUAL (spot
  venue). Net: cefi completeness % is measured over a fraction of the real universe — the "entire venue absent from the
  denominator" dishonesty class Honest-Coverage v2 exists to kill.'
status: open
nature: notes
asset_group: [cefi]
stage: [data, meta]
repos: [unified-api-contracts, instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags: [honest-coverage, denominator-audit, layer-1, data-correctness, cefi]
related:
  [
    honest_coverage_uac_writer_matrix_reconciliation_2026_06_29.md,
    ../honest_coverage_v2_instrument_denominator_2026_06_28.md,
    ../../../codex/02-data/honest-coverage-model.md,
  ]
created: 2026-07-03
parent_epic: infrastructure_master
priority: P1
source: honest_coverage_uac_writer_matrix_reconciliation_2026_06_29.md implementation session (Harsh)
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: design
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.2
last_updated: 2026-07-03
supersedes:
superseded_by:
depends_on:
assigned_role: data_engineering
drift_direction: advance-code
locked_since:
---

> **NOTIFY-OPERATOR class finding (data-correctness).** Surfaced 2026-07-03 while implementing
> `honest_coverage_uac_writer_matrix_reconciliation_2026_06_29.md` (ground-truthing the cefi venue dialect from
> `coverage.json` `by_venue_instrument_type` + `layer_1.by_asset_group.cefi.by_venue`). NOT fixed in that pass — it
> changes the certified cefi denominator structurally and needs owner decisions on the gate authorities.

## Evidence (coverage.json 2026-07-02, layer_1.by_asset_group.cefi.by_venue)

Venues with `expected_tuples == 0` while the manifest holds REAL captured rows for them (Layer-2 strays today):

| Venue                                                                                               | expected | manifest itypes present          | why expected=0                                                                                                                                                         |
| --------------------------------------------------------------------------------------------------- | -------- | -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| BITFINEX-SPOT / BITGET-SPOT / BITGET-FUTURES / KRAKEN-SPOT                                          | 0/0      | SPOT_PAIR / PERPETUAL + captures | absent from `VenueMapping.venue_instrument_type_to_tardis` (the checker's cefi (venue,itype) gate authority) — the Tier-3 2026-05-01 expansion never extended that map |
| HYPERLIQUID / ASTER / EXTENDED-STARKNET                                                             | 0/0      | PERPETUAL + captures             | non-Tardis venues — same gate reads only the Tardis map; `INSTRUMENT_TYPES_BY_VENUE` (which HAS them) is not consulted                                                 |
| BYBIT-SPOT / COINBASE-FUTURES                                                                       | 0/0      | rows present                     | wholly absent from `VENUE_DATA_TYPE_CAPABILITIES` → carve-out 1 removes EVERY data_type                                                                                |
| BINANCE-DELIVERY / DERIBIT-COMBO / PACIFICA-SOLANA / LIGHTER-ZKSYNC / KALSHI-PERP / POLYMARKET-PERP | (absent) | —                                | both gates blind to them (no Tardis-map keys AND no capability entries)                                                                                                |

Consequence: cefi Layer-1 "completeness" (65.91% certified 2026-06-29) is measured over a 44-tuple denominator that
omits whole venues UAC declares in `VENUES_BY_ASSET_GROUP["cefi"]` — the exact "entire venue absent from the
denominator" failure mode the v2 model exists to surface (`codex/02-data/honest-coverage-model.md` § Why v1 was not
enough). The % is neither an upper nor lower bound of the real value.

## Separate writer defect found in the same pass

- **BYBIT-SPOT rows are stamped `instrument_type=PERPETUAL`** (manifest `by_venue_instrument_type`: BYBIT-SPOT →
  {PERPETUAL} only; no SPOT_PAIR). Root cause candidate (verified 2026-07-03): MTDS
  `symbol_rules._VENUE_INSTRUMENT_TYPE` has `"BYBIT": "perpetual"` but **NO `BYBIT-SPOT` entry** (unlike
  BITFINEX-SPOT/BITGET-SPOT/KRAKEN-SPOT which map → spot) — BYBIT-SPOT rows fall through to whatever default stamped
  PERPETUAL. Add the map entry, fix the writer path, and corrective-relabel the existing rows. Until then (BYBIT,
  spot_pair, trades|book_snapshot_5) remain honest Layer-1 holes.

## Todos

- [ ] [DESIGN] P1. Decide the cefi (venue,itype) gate authority for Layer-1 EXPECTED: extend
      `venue_instrument_type_to_tardis` (fetch-routing table — extending it has fetch blast radius), or switch the
      checker's `_get_cefi_venue_itypes` to UAC `INSTRUMENT_TYPES_BY_VENUE` (declarative, already covers
      HYPERLIQUID/ASTER/BYBIT-FUTURES/Tier-3), or a dedicated Layer-1 map. Owner call — changes the certified
      denominator materially.
- [ ] [DESIGN] P1. Decide `VENUE_DATA_TYPE_CAPABILITIES` semantics for wholly-absent venues: today "absent venue = all
      data_types carved out" in the checker but "absent venue = not gated" in the enumerator seeding (deliberate
      asymmetry, see `_row_data_types` CEFI ONLY comment). Add owner-verified capability entries for
      BYBIT-SPOT/COINBASE-FUTURES/BINANCE-DELIVERY/KALSHI-PERP/etc., or codify the no-entry semantics.
- [ ] [CODE] P1. Diagnose + fix the BYBIT-SPOT `PERPETUAL` itype stamp; corrective-relabel existing rows
      (market-tick-data-service + manifest surgery).
- [ ] [SCRIPT] P2. After the gate fixes: re-measure and re-certify the cefi Layer-1 row of the CK3 table (expect the
      denominator to GROW substantially and the % to drop — that is the honest direction).

## Related fragility (observed live 2026-07-03)

- **Freshest-bucket PRIMARY selection is fragile to manifest surgery.** `measure_honest_coverage._read_manifest` picks
  the candidate with the newest `blob.updated` as PRIMARY (full frame) and reads the other as SECONDARY (**eu-only**).
  Rewriting the legacy cefi index (the ASTER corrective pass) bumped its mtime past prd → roles flipped → prd's
  captured-only tuples (e.g. BINANCE-FUTURES `future` rows consolidated 06-29) dropped from ENUMERATED and 3 artifact
  "holes" appeared. Mitigated in-session by a metadata bump restoring prd as freshest, but any future surgery on the
  older bucket re-triggers it. Consider content-based freshness (max manifest date) or pinning prd as primary. This may
  also explain the anomalous 05:07 UTC 2026-07-03 cefi-only measure (61.36%, present 29→27).
- [ ] [CODE] P2. Harden `_read_manifest` primary selection against surgery-bumped mtimes (content-based freshness or
      pinned-primary with explicit override).

## Progress Log

- **2026-07-03** — Filed from the reconciliation implementation session. Context: the venue-suffix fold + ASTER
  carve-out shipped in `instruments-service` (see the reconciliation issue doc); this finding is the structural
  remainder. Also noted: `INSTRUMENT_TYPES_BY_VENUE` exists in UAC and already covers most of the gate-blind venues —
  strongest candidate for the (venue,itype) authority.
