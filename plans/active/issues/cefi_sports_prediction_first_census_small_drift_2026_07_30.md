---
doc_type: issue
title: >-
  cefi/sports/prediction first-ever distinct-value census (2026-07-30) — small residual venue/instrument_type/data_type
  drift not covered by any existing tracked finding
summary: >-
  Phase G of data_pipeline_reconciliation_skill_2026_07_20.md ran the /data-pipeline-reconciliation distinct-value
  census (G1) for cefi/tradfi/sports/prediction for the first time ever (only defi had been measured, H6 in
  reference-defi.md). tradfi's findings and sports' market-token instrument_type findings turned out byte-identical to
  two already-open 2026-07-28 issue docs — good independent confirmation, no new action there. Root-causing the
  remaining findings (2026-07-30 follow-up pass) fixed the genuine cefi venue-underscore writer bug, a sports SMARKETS
  registry omission, and a prediction bulk-seed-script typo; corrected two real false positives in the ORIGINAL filing —
  3 of the "6 non-canonical sports bookmaker venues" (FOOTYSTATS/BET888SPORT/LADBROKES, a census methodology gap) AND
  the cefi `chain=<VENUE>` finding itself, which was misdiagnosed as drift and briefly "fixed" into a real production
  regression (chain=<VENUE> is the required non-blank-chain workaround for a chain-less venue, not a bug — caught +
  reverted same day, zero real writes lost, full incident writeup in
  `cefi_perp_funding_kalshi_polymarket_residual_and_capture_gap_2026_07_30.md`) — and escalated the one finding
  (`instrument_type=spot`) that turned out to be the tip of a much larger, live, ongoing instrument-id defect across 6
  CeFi spot connectors into its own properly-scoped P1 doc rather than rushing a partial fix.
status: resolved
nature: issue
asset_group: [cefi, sports, prediction]
stage: [data]
repos: [unified-api-contracts, market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags: [canonicalisation, census, distinct-values, venue, instrument_type, data_type, cefi, sports, prediction]
related:
  [
    data_pipeline_reconciliation_skill_2026_07_20,
    sports_instrument_type_market_token_ssot_gap_2026_07_28,
    tradfi_distinct_values_net_new_clusters_2026_07_28,
    cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20,
  ]
created: 2026-07-30
last_updated: 2026-07-30
parent_epic: manifest_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  "operator request 2026-07-30 — audit /data-pipeline-reconciliation's coverage against its own stated criteria across
  all 5 AGs"
resolved_by:
  "unified-api-contracts@b936abad (KALSHI_PERP/POLYMARKET_PERP registry constants, SMARKETS bookmaker exception) +
  market-tick-data-service@4d147d9a (canonical venue writes, prediction typo fix, SPORTS shard-count re-pin — NOTE: this
  same commit's chain='' change was WRONG and reverted same day, see item 3 above) — cefi item 2 escalated to
  cefi_live_spot_connectors_noncanonical_instrument_id_2026_07_30.md (now resolved + archived:
  market-tick-data-service@46e85d94, all 8 live spot venues fixed to SPOT_PAIR + canonical hyphenation); item 4 (stray
  ohlcv_* data_type) and the OKX-OPTIONS/FUTURES-chain sub-items are documented HISTORICAL-ONLY/UNCLEAR residue, not
  fixes"
depends_on: []
---

# cefi/sports/prediction first census — small residual drift

> **Priority rationale** (per `/codex/11-project-management/plan-priority-tier-and-dispatch-ordering.md`): not a
> CI/audit escalation; within the asset-group tier ordering cefi ranks second only to cross-cutting, but every item
> below is small-scale canonicalisation hygiene, not data-completion/backfill-critical — matches the **P2** precedent
> set by the two sibling 2026-07-28 census-finding docs this one is modeled on.

## cefi (9,492,020 rows measured)

1. ✅ **RESOLVED — Venue underscore/hyphen dupes.** `POLYMARKET_PERP` (4 rows) / `KALSHI_PERP` (4 rows) were the same
   venues as the registered `POLYMARKET-PERP` (1,020 rows) / `KALSHI-PERP` (1,666 rows), wrong separator — root cause
   `perp_funding_handler.py`'s `venue=protocol` passthrough (never mapped the internal `kalshi_perp`/`polymarket_perp`
   dispatch key to the registry's hyphenated constant) + a hardcoded `venue="KALSHI_PERP"` literal in
   `_perp_funding_kalshi_polymarket.py:441`. Fixed via a `_canonical_venue()` lookup + importing the real
   `KALSHI_PERP`/`POLYMARKET_PERP` registry constants. `OKX-OPTIONS` (2 rows) investigated separately — no current code
   writes this literal (HISTORICAL-ONLY, most likely a one-off exploratory test during the 2026-07-12/13 OKX-options
   routing fix; the shipped fix writes bare `venue="OKX"`), left as-is.
2. **ESCALATED — see `cefi_live_spot_connectors_noncanonical_instrument_id_2026_07_30.md`.** Root-causing
   `instrument_type=spot` (4,923 rows, lowercase) found the defect is NOT a stray content-dict field — it's a bare
   `SPOT` ITYPE token baked into the `instrument_id`/FILENAME construction itself (`f"{VENUE}:SPOT:{symbol}"`), across 6
   live spot WS connectors, several of which ALSO emit a non-hyphenated BASE-QUOTE symbol (a second, independent
   canonicality defect). Empirically confirmed via `is_canonical_instrument_id()`: `SPOT` is never canonical, only
   `SPOT_PAIR` is. This is a live, ongoing writer defect with a bigger, not-yet-fully-measured blast radius — properly
   scoped and tracked in the new doc rather than rushed here (a partial fix touching only the manifest axis would have
   made the manifest and the object's own filename disagree, which is worse than the pre-existing state).
3. ✅ **RESOLVED (2 of 3) — wrong-axis values in the `chain` content column.** `POLYMARKET_PERP` (3 rows) /
   `KALSHI_PERP` (3 rows) — **RETRACTED, this was a MISDIAGNOSIS, not a bug.** The original finding (and the fix shipped
   for it, briefly, same day) assumed `perp_funding_handler.py`'s `_chain_map` stamping `chain=<VENUE>` was the same
   class of defect as item 1's venue-underscore bug and "fixed" it by removing `_chain_map` (chain always `""`). This
   was WRONG: `DefiManifestRecorder` enforces a hard, deliberate A4-full invariant
   (`_defi_manifest.py::BlankChainError`) that every DeFi-family shard — perp_funding included — carries a **non-blank**
   `chain`; the docstring states the last caller that ever keyed a blank chain (a GMX pattern) was removed 2026-07-25
   specifically to close this off. The `chain=""` "fix" shipped (`market-tick-data-service@4d147d9a`, 2026-07-30T14:12
   UTC) and every `record_captured`/`record_failed` call for kalshi_perp/polymarket_perp/hyperliquid perp_funding
   silently raised `BlankChainError`, caught by shard-level isolation, and dropped the row with only a WARNING log — no
   manifest write at all. Caught and reverted the same day (`market-tick-data-service`, see
   `cefi_perp_funding_kalshi_polymarket_residual_and_capture_gap_2026_07_30.md` for the full incident writeup); blast
   radius measured as **zero real production rows lost** (the daily batch cron runs once ~01:15 UTC and did not fire
   again inside the ~2h15m regression window). `chain=<VENUE>` for a venue with no underlying blockchain is the
   established, load-bearing workaround for the A4-full invariant — not drift, and not something this doc should have
   flagged for correction. `FUTURES` (8 rows) root cause remains UNCLEAR after investigation — no current cefi write
   path found assigning this value to a chain field; left untouched (regression-risk-averse), and now doubly so given
   the lesson above. Refines `reference-cefi.md` H7 (with a caution, not a "fixed" claim).
4. **Still open — 5 stray candle-timeframe-shaped `data_type` values** (2 rows each) — `ohlcv_5m`/`ohlcv_1h`/`ohlcv_1d`/
   `ohlcv_15s`/`ohlcv_15m` on the raw-tick bucket, vs the legitimate `ohlcv_1m` (4,604 rows). Investigated: no current
   cefi write path can produce this (the only cefi-adjacent `ohlcv_*` code is `ccxt_adapter.py::fetch_ohlcv`, whose sole
   caller is a liveness heartbeat, never a writer) — HISTORICAL-ONLY, pre-MDPS-candle-split residue. No fix needed; left
   as a documented, dead-end finding.

## sports (628,349 rows measured)

5. **CORRECTED — most of the original "6 non-canonical bookmaker venues" finding was a false positive from the census's
   own incomplete canonical-vocabulary set, not real drift.**
   - `FOOTYSTATS` (22,962 rows) — **NOT a finding, and independently confirmed while this doc was in flight.** A
     concurrent session's `unified-api-contracts@c022a60e` (landed 2026-07-30 11:45 UTC, minutes before this
     investigation) moved `FOOTYSTATS` from `VENUES_BY_ASSET_GROUP['sports']` into
     `SPORTS_ODDS_API_ACCEPTED_NONCANONICAL_BOOKMAKERS` — the literal string collides with a DIFFERENT, already-
     canonical `FOOTYSTATS` reference-data-provider venue owned by instruments-service, and UAC/IS's sports venue sets
     are a deliberate two-registry model required to stay disjoint (operator Decision C, 2026-06-29). Same practical
     outcome either way (suppressed as an accepted exception, not flagged) — this doc's earlier read of _why_ (a
     `SPORTS_DATA_VENUES` grouping) was based on a stale pre-c022a60e checkout; the real reason is the disjoint-registry
     collision above.
   - `BET888SPORT` (18,903 rows) / `LADBROKES` (12,210 rows) — **NOT a finding.** These are the canonical FOLD TARGETS
     `SPORTS_VENUE_FOLD` writes (`venue_constants.py:116,123`) — i.e. the CORRECT output, not raw drift. The census's
     badging set doesn't currently recognize the fold-target vocabulary as a distinct tier from the base 8-entry
     `VENUES_BY_ASSET_GROUP['sports']` list, which is what produced the false flag.
   - ✅ **RESOLVED — `SMARKETS`** (8,518 rows). Genuinely missing from
     `SPORTS_ODDS_API_ACCEPTED_NONCANONICAL_BOOKMAKERS` despite being actively requested every cycle
     (`odds_api_adapter.py`'s `REQUESTED_ODDS_API_BOOKMAKERS`) — a real registry omission, not a writer bug. Fixed by
     adding it to the accepted-exceptions frozenset.
   - **Still open — `LADBROKES_UK`** (13,560 rows) / **`SPORT888`** (20,066 rows). Real historical residue: a raw-tick
     restamp (live since 2026-07-25/27, `odds_api_adapter.py:763`'s `SPORTS_VENUE_FOLD`) already fixed the primary shape
     going forward, but these specific rows are pre-restamp and the restamp tool structurally can't reach 4
     derived-candle data_types per the already-tracked `sports_venue_restamp_derived_candle_gap_2026_07_27.md` (open,
     P2) — not re-diagnosed here, just cross-linked.
   - `KALSHI` (20,785 rows) — unchanged from the original filing: the already-tracked, harmless (`row_count=0`) cross-AG
     artifact (archived `cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md` todo 15).

## prediction (1,661,267 rows measured)

6. **Investigated — `instrument_type` case drift is HISTORICAL-ONLY, already fixed forward.** `prediction_market`
   lowercase (9,720 rows): the live Kalshi adapter (`kalshi_adapter.py:594-607`) already stamps the canonical
   `InstrumentType.PREDICTION_MARKET.value` as of a 2026-07-27 fix; all live WS connectors were always correct. No live
   writer produces this today — historical residue only, no action needed. `prediction` (76 rows, truncated) — ✅
   **RESOLVED.** Root cause: `scripts/ingest_kalshi_bulk_to_canonical.py` (a one-off deep-history bulk-seed campaign
   script, not a daily writer) hardcoded the literal string `"prediction"` in its `row_key` dicts, inconsistent with the
   live path's `InstrumentType.PREDICTION_MARKET.value`. Fixed + added a regression assertion to the script's existing
   test (`test_convert_day_emits_cqg_bundle_manifest_batch_kalshi`).
7. **Investigated — `data_type=prediction_trades` (2,477 rows) is HISTORICAL-ONLY.** No live writer emits this (zero
   hits); it's pre-v9-canonical legacy residue, already aliased by the one-shot
   `scripts/migrate_prediction_to_pred_prd_v9.py` (`_CF7_DATA_TYPE_ALIASES = {"prediction_trades": "trades"}`). No fix
   needed.

## Todos

- [x] [DATA] P2. **cefi item 1 (venue underscore) fixed; item 3 (chain "wrong-axis") RETRACTED as a misdiagnosis** — the
      venue fix root-caused + landed in `market-tick-data-service` (`perp_funding_handler.py`,
      `_perp_funding_kalshi_polymarket.py`) + registered the `KALSHI_PERP`/`POLYMARKET_PERP` constants in
      `unified-api-contracts/registry/__init__.py`'s public re-export. The SAME commit's `chain=""` change (item 3) was
      WRONG — it violated `DefiManifestRecorder`'s hard non-blank-chain invariant and silently dropped every
      kalshi_perp/polymarket_perp/hyperliquid perp_funding manifest write for ~2h15m — caught same-session, reverted
      (`market-tick-data-service`, second commit), zero real writes lost (verified: no `written_at` in the regression
      window). Full incident writeup + the corrected manifest re-stamp (using `chain=<VENUE>`, not `""`) in
      `cefi_perp_funding_kalshi_polymarket_residual_and_capture_gap_2026_07_30.md`. `OKX-OPTIONS` and the `FUTURES`
      chain value investigated, left as historical/unclear respectively (see § cefi item 1/3 above). Evidence:
      `unified-api-contracts@b936abad` + `market-tick-data-service@4d147d9a` (venue fix + prediction typo + shard-count
      re-pin, QG-green) + a follow-up `market-tick-data-service` commit (chain revert, QG-green), all pushed, `ahead=0`.
      Two genuine merge conflicts hit and resolved during the FIRST commit's shipping (both from concurrent sessions,
      not this doc's own scope): a concurrently-restored HYPERLIQUID perp_funding collector touching the exact same
      `_chain_map` region (ironically, reverting my own change restored what that conflict resolution had correctly
      preserved); and an unrelated pre-existing DeFi vault-share-price `pipeline_mode`/ `source` desync regression
      (`defi_pipeline_mode_source_desync_yearn_v3_2026_07_21.md`, already tracked, fixed upstream by another session
      mid-ship — pulled in, not fixed here).
- [x] [DATA] P2. **cefi item 2 escalated** — see `cefi_live_spot_connectors_noncanonical_instrument_id_2026_07_30.md`
      (new P1 doc, the true scope + fix live there, not here).
- [x] [DATA] P2. **cefi item 4** — investigated, confirmed HISTORICAL-ONLY (no live cefi write path), no fix needed.
- [x] [DATA] P2. **sports item 5** — corrected the FOOTYSTATS/BET888SPORT/LADBROKES false-positive misclassification
      (census methodology gap, not real drift; FOOTYSTATS additionally independently fixed by a concurrent session,
      `unified-api-contracts@c022a60e`, for a related-but-different reason — see § sports item 5 above); fixed the
      genuine `SMARKETS` registry omission (`unified-api-contracts@b936abad`); `LADBROKES_UK`/`SPORT888` residue
      cross-linked to the already-tracked `sports_venue_restamp_derived_candle_gap_2026_07_27.md` rather than
      re-diagnosed.
- [x] [DATA] P2. **prediction items 6-7** — investigated, both confirmed HISTORICAL-ONLY except the `prediction`
      truncated-token case, which was a real, now-fixed bug in a bulk-seed campaign script (with a new regression test).
      Evidence: `market-tick-data-service@4d147d9a`.
