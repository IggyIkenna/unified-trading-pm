---
doc_type: plan
title: Distinct-Values non-canonical audit — all asset_groups × all axes
summary: >-
  Audit every value the data-status /distinct-values panel badges non-canonical, across all five asset_groups (defi,
  cefi, tradfi, prediction, sports) and all four axes (venues/instrument_types/data_types/chains) from the live nightly
  honest-coverage rollup — not just the DEFI screenshot. Classify each into (1) naming-drift owned by an in-flight
  consolidation/migration plan, (2) detector/SSOT gap — value is legit, fix the detector rule or add to the UAC
  canonical set, (3) wrong-axis contamination / writer mis-stamp, (4) genuine junk to PURGE from manifest+catalogue.
  Execute (1)/(2)/(3) code+SSOT fixes to completion; stage (4) as a verified worklist gated BLOCKED-OPERATOR-DECISION
  (destructive-beyond-local = human-only hard-stop). Headline finding: the DeFi venue axis is a detector naming-model
  bug — bare manifest venue compared against chain-qualified canonical.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [unified-api-contracts, deployment-api, instruments-service, market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags: [canonicalisation, manifest, data-correctness, ssot-audit, distinct-values, drift, audit]
related:
  [
    defi-canonical-naming-ssot.md,
    master_data_canonicalisation_migration_catalogue_2026_06_07.md,
    cefi_consolidated_closeout_2026_07_18.md,
    defi_consolidated_closeout_2026_07_18.md,
    tradfi_consolidated_closeout_2026_07_18.md,
    sports_consolidated_closeout_2026_07_19.md,
    prediction_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-07-20"
last_updated: "2026-07-20"
parent_epic: manifest_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: data_engineering
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  operator ask 2026-07-20 (data-status Distinct Values screenshot — "audit all these not just ones from screenshot")
---

# Distinct-Values non-canonical audit — all asset_groups × all axes

> **Operator ask (2026-07-20):** the Distinct Values panel (data-status, IS view) badges far more values non-canonical
> than expected (e.g. `UNISWAP_V2` as a venue). "We should audit all these not just ones from screenshot. Some may fix
> during manifest rebuild that are underway as part of each AG's consolidated plans and migration plans; else some may
> be bugs and some should truly be purged from manifest and catalogues."

## Mechanism (SSOT-verified)

The panel is `GET /distinct-values/{asset_group}`
([deployment-api `_distinct_values.py`](../../deployment-api/deployment_api/routes/data_status/_distinct_values.py)).
For each axis it reads the raw distinct values from the nightly honest-coverage rollup
(`gs://central-element-323112-honest-coverage/{date}/coverage.json`) and badges each `is_canonical` by an **EXACT,
case-sensitive membership test** against a UAC canonical set:

- `venues` → `VENUES_BY_ASSET_GROUP[asset_group]`
- `instrument_types` → `InstrumentType` enum member values (global)
- `data_types` → `DATA_TYPES_BY_ASSET_GROUP[asset_group]`
- `chains` → `MAINNET_CHAIN_IDS` keys

It deliberately does NOT canonicalise (no case-fold, no suffix-strip) — the panel is a drift **detector**. So a badge
means only "not an exact member of the canonical set for its axis"; it does not say WHY. This audit decides the why.

## Ground truth (nightly rollup source_date 2026-07-20, generated_at 2026-07-20T00:35Z)

Full non-canonical inventory saved to the Progress Log below. Counts (non-canonical / total distinct):

| asset_group | venues | instrument_types | data_types | chains |
| ----------- | ------ | ---------------- | ---------- | ------ |
| defi        | 76/76  | 11/17            | 10/36      | 2/23   |
| cefi        | 2/24   | 4/8              | 0/4        | 4/4    |
| tradfi      | 1/8    | 9/16             | 2/12       | 0/0    |
| prediction  | 0/2    | 0/1              | 0/4        | 0/1    |
| sports      | 29/37  | 15/15            | 7/13       | 3/3    |

## Headline finding — DeFi venue axis is a detector naming-model bug (NOT manifest drift)

The DeFi canonical naming SSOT (`codex/02-data/defi-canonical-naming-ssot.md`, operator-locked) mandates **bare venue +
a separate `chain=` path segment**. So the manifest storing bare `UNISWAP_V2` is _correct by the SSOT_. But the detector
badges the DeFi `venues` axis against `VENUES_BY_ASSET_GROUP['defi']`, whose members are **chain-qualified composites**
(`UNISWAP_V2-ETHEREUM`, `AAVE_V3-BASE`, …). Bare-vs-composite can never match → **all 76 DeFi venues badge non-canonical
(canonical_n = 0)**, which is a false alarm on the majority. Comparing the bare manifest venue against the **bare
bases** of the canonical set (`{v.split('-')[0]}`) collapses 76 → ~28 genuine drifts. → This is a category-2 detector
fix, and an SSOT-contradiction big-finding (surfaced to operator). Only defi is affected; cefi's `-SPOT`/ `-FUTURES` are
market-type suffixes (the composite IS the venue) and cefi matched 22/24.

## Classification framework

1. **Drift owned by an in-flight plan** — case/suffix/version spelling the manifest rebuild/consolidation already
   rewrites. Action: LINK the owning plan, confirm coverage, do NOT duplicate (findings-triage "fits another plan →
   annotate").
2. **Detector / SSOT gap** — value is legit; fix the detector rule (defi bare-base compare) or ADD to the UAC canonical
   set. Safe code change (execute).
3. **Wrong-axis contamination / writer mis-stamp** — a value stamped into the wrong column (bookmaker as
   instrument_type, bet-market as chain, `KALSHI_PERP` as a defi chain/venue, `futures_chain` as instrument_type,
   `BARCHART`/source as venue). Root cause is upstream (writer/consolidator). Fix the writer if clearly a bug we own;
   otherwise file/annotate.
4. **Genuine junk to PURGE** — decommissioned (`DECOMMISSIONED_VENUE_BASES = {DRIFT,FLASH,MANGO,PACIFICA,ZETA}`) or
   garbage. Manifest+catalogue deletion = destructive-beyond-local = **human-only hard-stop** → verified worklist, gated
   `BLOCKED-OPERATOR-DECISION`. **NOTE (corrected 2026-07-20):** the original framing above cited `BARCHART`/`UNKNOWN`
   as cat-4 examples while ALSO citing `BARCHART` as a cat-3 wrong-axis example — an internal contradiction caught by
   adversarial verification. Both resolved to cat-3-with-quarantine, NOT purge; see the Progress Log verdicts.

## Codex SSOTs

- `codex/02-data/defi-canonical-naming-ssot.md` (bare-venue + chain= model — the headline finding rests on this)
- `codex/02-data/availability-manifest-and-data-status.md`, `codex/02-data/honest-coverage-model.md`
- UAC `unified_api_contracts/registry/` (`VENUES_BY_ASSET_GROUP`, `DATA_TYPES_BY_ASSET_GROUP`, `InstrumentType`,
  `MAINNET_CHAIN_IDS`, `venue_adapter_keys.DECOMMISSIONED_VENUE_BASES`)

## Todos

- [x] [DATA] P0. ✅ Run the classification fan-out (Workflow) over the full ground truth — 47 agents, **175 findings**
      classified cat1-4 with root cause + owning plan + safety class; every cat3/cat4 call adversarially verified (8
      rate-limited verifiers re-run separately). Evidence: workflow `wf_4d089da8-4db`; synthesis + per-finding JSON in
      the Progress Log. Outcome: 22 owned / 105 detector-SSOT-gap / 41 wrong-axis / **0 executable purges**.
- [ ] [BACKEND] P0. Detector fix (deployment-api `_distinct_values.py`): DeFi `venues` axis compares the bare manifest
      venue against the bare bases of `VENUES_BY_ASSET_GROUP['defi']` (keep other axes/AGs exact). Unit-test the
      bare-base reduction (76 → ~28). Ship + flip.
- [ ] [DATA] P1. UAC SSOT additions (category 2) that are unambiguous and NOT contested by an in-flight migration —
      legit-but-missing venues/data_types/instrument_types — added to the correct `VENUES_BY_ASSET_GROUP` /
      `DATA_TYPES_BY_ASSET_GROUP` / `InstrumentType`. Each addition cited against a source (adapter/registry/SSOT).
- [ ] [DATA] P1. Wrong-axis writer root-cause (category 3): for each mis-stamp cluster, locate the writer/consolidator
      that populates the wrong column; fix the clearly-ours bugs; annotate the rest to their owning plan/issue.
- [ ] [DATA] P1. Reconcile every drift cluster (category 1) to its owning in-flight plan; any cluster owned by NO plan →
      file an issue doc or add a P-todo to the right plan (no orphan drift).
- [ ] [OPERATOR] P1. BLOCKED-OPERATOR-DECISION — verified PURGE worklist (category 4): exact (asset_group, axis, value,
      row_count, GCS/catalogue locations, why-junk) for operator one-tap approval. NO blind deletion.
- [ ] [REVIEW] P2. Post-audit: update `codex/02-data/defi-canonical-naming-ssot.md` / manifest SSOT if the
      detector-model finding changes a documented contract; confirm the panel now reflects true drift.

## Progress Log

### 2026-07-20 — foundation + headline finding

- Traced the badge mechanism to `_distinct_values.py` (exact case-sensitive membership vs UAC canonical sets). Confirmed
  the panel is a deliberate non-canonicalising drift detector.
- Pulled the full non-canonical inventory for all 5 asset_groups from the live nightly rollup (source_date 2026-07-20)
  via a scratchpad enumerator reusing the endpoint's exact logic. Full JSON below.
- Headline: DeFi `venues` 76/76 non-canonical is a detector naming-model mismatch (bare manifest venue vs
  chain-qualified canonical), per the operator-locked defi-canonical-naming SSOT. Fixing the compare to bare-base
  collapses it to ~28.

#### Full non-canonical inventory (source_date 2026-07-20)

```
defi.venues (76): AAVE, AAVEV3, AAVE_V3, ACROSS, AERODROME_V3, ALCHEMY, ANKR, ASTER, BALANCER, BEEFY, BENQI, BINANCE,
  BLAZESTAKE, CAMELOT_V3, CHAINLINK, COINBASE, COMPOUND, COMPOUND_V3, CONVEX, CURVE, EIGENLAYER, ETHENA, ETHERFI,
  EULER_V2, EXTENDED, FLASHBOTS, FLUID, FRAX, GMX, IDLE, JITO, JITORESTAKING, JUPITER, KALSHI_PERP, KAMINO,
  KAMINO_LENDING, KARAK, KELPDAO, LIDO, LIGHTER, MAKER, MANTLE, MARGINFI, MARINADE, MORPHO, MORPHOVAULTS, ORCA,
  PANCAKESWAP_V3, PENDLE, PHOENIX, POLYMARKET_PERP, PUFFER, PYTH, RADIANT, RAYDIUM, RENZO, ROCKETPOOL, SANCTUM, SOLEND,
  SPARK, STADER, STAKEWISE, STARGATE, SUSHISWAP, SUSHISWAP_V3, SWELL, SYMBIOTIC, TRADER_JOE_V2, UNISWAP, UNISWAP_V2,
  UNISWAP_V3, UNISWAP_V4, VELODROME_V2, VENUS, YEARNV3, YEARN_V3
defi.instrument_types (11): a_token, lending, liquidation, lst, perpetual, pool, restaking, spot_asset, spot_pair,
  staking, yield_bearing
defi.data_types (10): dex_pools, dex_swaps, rate_indices, swaps_ohlcv_15m, swaps_ohlcv_15s, swaps_ohlcv_1d,
  swaps_ohlcv_1h, swaps_ohlcv_1m, swaps_ohlcv_4h, swaps_ohlcv_5m
defi.chains (2): KALSHI_PERP, POLYMARKET_PERP
cefi.venues (2): OKX-FUTURES, OKX-SWAP
cefi.instrument_types (4): futures_chain, options_chain, perpetual, spot
cefi.chains (4): ASTER, EXTENDED-STARKNET, HYPERLIQUID, LIGHTER-ZKSYNC
tradfi.venues (1): BARCHART
tradfi.instrument_types (9): FUTURES, UNKNOWN, combo, equity, etf, future, futures, futures_chain, options_chain
tradfi.data_types (2): futures_chain, options_chain
sports.venues (29): BETMGM, BETONLINEAG, BETOPENLY, BETRIVERS, BETSSON, BETVICTOR, BETWAY, BOVADA, CASUMO, CORAL,
  FOOTBALL, KALSHI, LADBROKES_UK, LIVESCOREBET, MATCHBOOK, NOVIG, ONEXBET, PADDYPOWER, POLYMARKET, PROPHETX, SKYBET,
  SMARKETS, SPORT888, UNIBET, UNIBET_EU, UNIBET_UK, UNKNOWN, VIRGINBET, WILLIAMHILL
sports.instrument_types (15): PADDYPOWER, PINNACLE, SPORT, betmgm, betway, bovada, coral, fanduel, ladbrokes_uk, odds,
  paddypower, pinnacle, skybet, unibet_uk, williamhill
sports.data_types (7): ARBITRAGE_OPPORTUNITY, ODDS_MOVEMENT, ODDS_SNAPSHOT, odds_horizon_bucket_15m,
  odds_horizon_bucket_1d, odds_horizon_bucket_1h, odds_horizon_bucket_4h
sports.chains (3): H2H, MATCH_ODDS, SPREADS
(prediction: clean — 0 non-canonical on every axis)
```

### 2026-07-20 — classification fan-out COMPLETE (175 findings) + adversarial verification

**Method.** 5 per-asset_group classifier agents over the full ground truth → adversarial verify on every cat-3/cat-4
(wrong-axis / purge) call → synthesis. 47 agents, 175 findings. 8 verify agents died on API rate-limiting and were
RE-RUN separately (they covered the 3 most consequential purge calls — see verdicts below).

**Counts.** cat1 (owned by an in-flight plan) 22 · cat2 (detector/SSOT gap) 105 · cat3 (wrong-axis mis-stamp) 41 · cat4
(junk) 5 claimed → **0 survive as executable purges**.

#### RESULT 1 — the detector grain bug is the dominant root cause (SHIPPED FIX)

~75 of 175 findings are FALSE ALARMS from one file comparing at the wrong grain. Fixed two of the four grains
(`_distinct_values.py::_comparison_set`), **measured** against the live rollup: **175 → 115 non-canonical (60 false
badges cleared, 34%)**; defi venues 76→25, defi instrument_types 11→2.

- **D1 defi venues bare-base** — canonical is chain-qualified, manifest is bare (operator-locked
  `defi-canonical-naming-ssot.md`). ⚠️ The synthesis proposed `v.split('-')[0]`, which is WRONG — it maps canonical
  `SOLANA-NATIVE-SOLANA` to `SOLANA`. Implemented as "strip a trailing `-{CHAIN}` validated against
  `MAINNET_CHAIN_IDS`".
- **D3 defi instrument_types case-insensitive** — the DeFi SSOT declares canonical itypes in LOWER case (`pool`,
  `a_token`, `lst`, `spot_asset`, `perpetual`, `lending`) while the enum is UPPER. Scoped to defi ONLY: cefi/tradfi are
  canonically UPPERCASE and their lowercase spellings are REAL drift owned by in-flight migrations. An existing test
  asserting defi `lending` was drift encoded a stale assumption and was updated with the SSOT citation.
- **D4 (gate the `chains` axis to defi-only) DELIBERATELY NOT APPLIED** — verification proved the cefi chain values are
  a LIVE WRITER BUG, so gating the axis would have HIDDEN a production defect. See RESULT 3.
- D2 (cefi `_CEFI_VENUE_FOLD`) deferred: correct fix is a UAC registry export first — hardcoding the fold map in
  deployment-api would violate the "canonical sets imported from UAC, never hardcoded" contract.

#### RESULT 2 — the PURGE worklist is EMPTY. Every purge call was walked back.

Adversarial verification refuted or downgraded **all** of them; several contradicted standing operator rulings:

| Value                                                                                                              | Original call   | Verified verdict                                                                                                                                                                                                                     |
| ------------------------------------------------------------------------------------------------------------------ | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `BARCHART` (tradfi.venues)                                                                                         | cat4 purge      | **REVISED → quarantine-with-tracking.** Same-day operator ruling (`tradfi_consolidated_closeout` Progress Log 2026-07-20): "barchart + ICE qualifier variants quarantine-with-tracking". Rows are 100% `empty_confirmed`/captured=0. |
| `UNKNOWN` (tradfi.instrument_types)                                                                                | cat4 purge      | **REVISED → classify-or-quarantine.** Operator ruling 2026-07-18: "`<null>`/`''`/`UNKNOWN` classify or quarantine". 77 rows; precedent verified-then-reclassified, never blind-dropped.                                              |
| `KALSHI_PERP` (defi.chains)                                                                                        | cat3/cat4 purge | **REFUTED.** Explicit operator KEEP ruling + REAL captured funding rows written 2026-07-12/13/14 (39/39/26). A chain-scoped delete would destroy live data.                                                                          |
| `POLYMARKET_PERP`, `EXTENDED`, `LIGHTER`, sports `UNKNOWN`, `odds_horizon_bucket_{15m,1d}`                         | purge           | REVISED → re-stamp / migrate / already-executed / keep.                                                                                                                                                                              |
| `odds_horizon_bucket_1h`                                                                                           | purge           | **BLOCKED — verified unsafe**: `_legacy_seed.parquet` resurrection re-supplies deleted atoms.                                                                                                                                        |
| `options_chain` (tradfi.data_types)                                                                                | relabel         | **REFUTED** — live `SchemaContract` keyed on it under an operator PRESERVE decision.                                                                                                                                                 |
| **Standing rule confirmed across AGs: the default disposition for a wrong-axis value is RE-STAMP, never DELETE.**  |
| Recurring blockers: `_legacy_seed.parquet` resurrection · `empty_confirmed` honest-absence rows (deleting converts |
| KNOWN-ABSENT → UNKNOWN) · raw-name collisions (ASTER↔ASTEROID, `odds_horizon_bucket*`↔the 124k aggregate,          |
| `UNKNOWN`↔by-design `""`).                                                                                         |

#### RESULT 3 — genuine live writer bug found (cefi chain axis)

UAC `SHARD_AXIS_MATRIX[("market-tick-data-service","cefi")]` has **no `chain` axis**, so `chain` is meaningless for
cefi. instruments-service already excised this defect (`writers.py::_canonical_manifest_venue_chain` short-circuits cefi
→ `chain=""`, with regression tests). **MTDS never got the fix**:
`market-tick-data-service/.../cli/handlers/onchain_perp_batch_handler.py:131-139` `_VENUE_CHAIN` stamps each venue as
its own chain (HYPERLIQUID/ASTER/EXTENDED-STARKNET/LIGHTER-ZKSYNC), mirrored in the live-WS recorder + perp_funding
handler. → tracked as a P1 writer fix mirroring the IS pattern.

#### RESULT 4 — corrections to the synthesis (verified against the live registry)

- `CHAINLINK`, `PYTH`, `PHOENIX` are **already in** `VENUES_BY_ASSET_GROUP['defi']` (98 entries, not 89) — RC-4 listed
  them as missing. No UAC action needed; D1 makes them canonical for free.
- Genuinely absent: ANKR, FRAX, MAKER, STADER, STAKEWISE, SWELL, MANTLE, ACROSS, STARGATE, FLASHBOTS, ALCHEMY, JUPITER,
  BLAZESTAKE, KAMINO_LENDING, MORPHOVAULTS.
- **UAC canonical-set additions are NOT "safe-code"** (synthesis mislabel).
  `instruments-service/scripts/ enumerate_expected_universe.py` builds the coverage DENOMINATOR from
  `VENUES_BY_ASSET_GROUP`, and `measure_honest_coverage.py` derives `denominator_complete`/`completeness_pct` from it —
  adding venues EXPANDS the denominator and DROPS measured coverage fleet-wide (rule-11 blast radius). → operator-gated,
  not autonomous.
- `futures_chain` in tradfi.data_types: the naive "add to the registry" fix is WRONG (`futures_chain` is an
  `instrument_type`; the data_type for those rows is `trades`). `options_chain` has a documented T-OLD-2b carve-out;
  `futures_chain` has none. Needs a live row-count to choose registry-exception vs writer-fix.

## Refined worklist (post-verification, 2026-07-20)

### Executable safe-code (no manifest mutation, no denominator shift)

- [x] [BACKEND] P0. ✅ Detector grain fix D1+D3 — `_distinct_values.py::_comparison_set`. Measured on the live rollup:
      **175 → 115 non-canonical (60 false badges cleared)**; defi venues 76→25, defi itypes 11→2. 23 tests green.
      _(implemented + reviewed; ships with the deployment-api batch once the contended host gate clears)_
- [ ] [BACKEND] P2. D2 — cefi venue fold (`OKX-SWAP`/`OKX-FUTURES` → `OKX`) in the detector. BLOCKED-ON-DESIGN: the fold
      map lives in `instruments-service/scripts/check_enumeration_completeness.py::_CEFI_VENUE_FOLD`; the correct fix
      promotes it to a UAC registry export FIRST (hardcoding it in deployment-api violates "canonical sets imported from
      UAC, never hardcoded"). 2-repo change.
- [ ] [DATA] P2. D5/D6 — bundle-grain (`futures_chain`/`options_chain`/`combo`) recognition + scoping the `data_types`
      axis away from MDPS `processed_candles` (`swaps_ohlcv_*`). Needs the live-count evidence below first.

### D4 — DELIBERATELY REJECTED (do not implement)

- The synthesis proposed gating the `chains` axis to `asset_group=='defi'`. **Verification proved this would HIDE two
  live defects**: (a) the cefi chain values are a real MTDS writer bug (below), (b) sports `H2H`/`MATCH_ODDS`/`SPREADS`
  are real drift whose faithful detectors must keep surfacing it. Leaving the axis un-gated is CORRECT.

### Writer bugs — real, but each needs a PAIRED manifest re-stamp (operator-gated)

- [ ] [DATA] P1. **MTDS `onchain_perp_batch_handler.py:131-139` `_VENUE_CHAIN`** stamps each cefi on-chain-perp venue as
      its own chain (HYPERLIQUID/ASTER/EXTENDED-STARKNET/LIGHTER-ZKSYNC), contradicting UAC
      `SHARD_AXIS_MATRIX[("market-tick-data-service","cefi")]` which has NO `chain` axis. instruments-service already
      excised this exact defect (`writers.py::_canonical_manifest_venue_chain` → `(venue, "")`, regression-tested); MTDS
      never got it, and the same pattern is mirrored in the live-WS recorder + perp_funding handler. ⚠️ **The writer fix
      ALONE is unsafe**: `chain` is a ROW-KEY column (`unified-trading-library/manifest_writer/     _rows.py:99`), so
      flipping it to `""` gives future writes a DIFFERENT row identity than the historical `chain=<VENUE>` rows →
      fragmented shards, broken `expected_unattempted`→`captured` supersede, double-counted coverage. Requires writer
      fix + paired re-stamp of existing rows, applied together. **BLOCKED-OPERATOR-DECISION** (manifest mutation =
      destructive-beyond-local).
- [ ] [DATA] P1. **MDPS `canonical_writer_shaping.py::_type_token_from_canonical_id`** — highest-yield single bug in the
      corpus. It assumes a 3-segment cefi `VENUE:TYPE:SYMBOL` id and takes `parts[1]`; sports ids are 8-segment
      `SPORT:BOOKMAKER:MARKET:...`, so `parts[1]` is the BOOKMAKER, and it OUTRANKS the explicit `instrument_type`
      column. One function produces the entire 13-value bookmaker-in-instrument_type cluster (and, via
      `build_instrument_catalogue.py::_instrument_type_from_id`, the same shape in the IS catalogue). Fix the PARSE, not
      the readers. Owned by `sports_consolidated_closeout_2026_07_19.md` Track C F1/F2 — annotate there, do not fork.
- [ ] [DATA] P2. MTDS `liquidations_handler.py:534` stamps `instrument_type="liquidation"` into the manifest while the
      same handler writes `InstrumentType.LENDING` to disk (L645) — manifest contradicts disk. Fix + update
      `tests/unit/test_liquidations_handler.py:238`, then re-stamp. (`liquidation_events_handler.py` is CLEAN.)
- [ ] [BACKEND] P3. instruments-service `writers.py::_LEGACY_INSTRUMENT_TYPE_ALIASES` — add `'options_chain': 'OPTION'`
      for parity with the existing `'futures_chain': 'FUTURE'`. Smallest genuine code delta in the cefi itype cluster.

### Operator-gated (NOT autonomous) — decisions for the operator

- [ ] [OPERATOR] P1. BLOCKED-OPERATOR-DECISION — **UAC canonical-venue additions**. 15 defi protocols (ANKR, FRAX,
      MAKER, STADER, STAKEWISE, SWELL, MANTLE, ACROSS, STARGATE, FLASHBOTS, ALCHEMY, JUPITER, BLAZESTAKE,
      KAMINO_LENDING, MORPHOVAULTS) + 19 sports ODDS_API fan-out bookmakers. **NOT safe-code**:
      `instruments-service/     scripts/enumerate_expected_universe.py` builds the coverage DENOMINATOR from
      `VENUES_BY_ASSET_GROUP` and `measure_honest_coverage.py` derives `denominator_complete`/`completeness_pct` from it
      — adding venues EXPANDS the denominator and DROPS measured coverage fleet-wide (rule-11 blast radius). The sports
      half also supersedes the 2026-05-12 scraper deferral. Needs an operator call + a measured before/after coverage
      delta.
- [ ] [OPERATOR] P2. BLOCKED-OPERATOR-DECISION — `restaking` has no canonical `InstrumentType`. Add `RESTAKING` to the
      enum, or re-stamp ezETH/rsETH/pufETH to `lst`/`yield_bearing`. Closeout Track1 P1 ratifies only
      lst/staking/yield_bearing, so nothing owns this today.
- [ ] [OPERATOR] P2. BLOCKED-OPERATOR-DECISION — `odds_horizon_bucket_{15m,1h,4h,1d}`: canonical is bare
      `ODDS_HORIZON_BUCKET` with `timeframe` as its own column. Mechanism MUST be a seed-aware re-stamp/tombstone that
      PARSES the suffix into `timeframe` — a row DELETE is verified-unsafe (`_legacy_seed.parquet` re-supplies deleted
      atoms) and the 2026-07-13 rebuild cohort has `timeframe` NULL, making the suffix the only record of the horizon.
      Scope the predicate away from the deliberate 124,294-row `mdps_odds_horizon_bucket` aggregate.
- [ ] [DATA] P2. Live-count `data_type=="futures_chain"` in the tradfi availability index to choose the remedy: zero-row
      non-issue / small legacy cohort (→ documented carve-out like `options_chain`'s T-OLD-2b) / active writer bug. Do
      NOT add it to `DATA_TYPES_BY_ASSET_GROUP['tradfi']` — `futures_chain` is an instrument_type; the data_type for
      those rows is `trades`.

### PURGE worklist — **EMPTY** (this is the audit's answer to "some should truly be purged")

Every purge candidate was walked back by adversarial verification. There is **no safe manifest/catalogue delete** in
this corpus today. `BARCHART` → quarantine-with-tracking (same-day operator ruling). tradfi `UNKNOWN` → classify-or-
quarantine (operator ruling). `KALSHI_PERP`/`POLYMARKET_PERP` → KEEP (operator ruling + real captured funding rows).
sports `UNKNOWN` → normalize-in-place (~6 phantom rows; blank is by-design at league grain). `odds_horizon_bucket_*` →
re-stamp, delete blocked by seed resurrection. `options_chain` → REFUTED, is canonical.

### 2026-07-20 — LIVE row-count evidence (tradfi `_index/availability_index.parquet`, 5,208,647 rows)

Read directly from `market-data-tick-tradfi-prd-central-element-323112` to settle the open remedies with measured counts
rather than inference:

| Query                          | Rows        | capture_status         |
| ------------------------------ | ----------- | ---------------------- |
| `data_type == 'options_chain'` | **242,210** | 100% `captured`        |
| `data_type == 'futures_chain'` | **8**       | 100% `captured`        |
| `instrument_type == 'UNKNOWN'` | 77          | 100% `empty_confirmed` |
| `venue == 'BARCHART'`          | 9,119       | 100% `empty_confirmed` |

**Consequences:**

- **`options_chain` — the REFUTED verdict is vindicated with a hard number.** The original finding proposed relabelling
  it to trades/ohlcv; that would have mislabelled **242,210 rows of REAL captured** options-chain snapshots (the
  greeks/IV-surface cohort the registry's operator PRESERVE decision exists to protect). Do not touch.
- **`futures_chain` (data_type) = 8 captured rows.** A tiny genuine legacy cohort — NOT a zero-row non-issue and NOT a
  registry gap. Remedy = a documented carve-out exactly parallel to `options_chain`'s T-OLD-2b exception, or a re-stamp
  of 8 rows. Do NOT add it to `DATA_TYPES_BY_ASSET_GROUP['tradfi']` (it is an instrument_type; the data_type for those
  rows is `trades`), and do NOT delete captured rows.
- **`BARCHART` (9,119) and tradfi `UNKNOWN` (77) are 100% `empty_confirmed`** — zero captured rows, so no real trading
  data was ever at risk; both counts match the audit's estimates exactly. This CONFIRMS the walked-back purge verdicts
  on the facts, and the standing operator rulings (quarantine / classify-or-quarantine) govern the remedy. Deleting
  honest-absence rows would still convert KNOWN-ABSENT → UNKNOWN, the recurring hazard.

### 2026-07-20 — OPERATOR DECISIONS (unblocks the three gated items)

1. **`restaking` → ADD `RESTAKING` to the `InstrumentType` enum.** Rationale accepted: liquid restaking carries
   genuinely distinct risk (EigenLayer AVS slashing stacked on base ETH staking slashing; ezETH depegged 2024), so
   folding ezETH/rsETH/pufETH into `lst` would lose real signal for collateral/risk modelling. Downstream consumers must
   handle the new member.
2. **MTDS venue-as-chain → writer fix + re-stamp in ONE pass.** Mirror `instruments-service`'s
   `_canonical_manifest_venue_chain` (cefi → `chain=""`). Mechanism: snapshot the `_index` first, CAS-apply, then verify
   the change HOLDS across 2 consolidator cycles including one `--force`. Leaves a single consistent row identity.
3. **UAC venue additions → BOTH (15 defi protocols + 19 sports bookmakers).** Operator accepts the coverage-denominator
   expansion: measured coverage % will visibly DROP because the denominator becomes honest — the underlying data does
   not change. The sports half SUPERSEDES the 2026-05-12 scraper deferral. **EXCLUDED from the addition either way:**
   `ALCHEMY` (unreconciled ALCHEMY-vs-ALCHEMIX spelling across chain_env/venue_launch_dates/manifest — reconcile to ONE
   form first) and `JUPITER` (UAC registry comment says "not integrated"; confirm capture-integration first).

## Deferred work after 2026-07-20

| Item                                                                                                                                                               | State                                                                                                                                                                                                                                                                                                                | Why deferred                                                                                                                                                                                                                                                                                                                               | Recovery                                                                                                                                                                                                                                                                                         |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **MTDS venue-as-chain writer fix** (`onchain_perp_batch_handler.py` `_VENUE_CHAIN` → `_venue_chain()` resolving via UAC `VENUE_TO_ASSET_GROUP`, + regression test) | **WRITTEN, NOT SHIPPED.** Code complete and reviewed; the handler's own stale docstring claim was verified and corrected (neither the live-WS recorder nor `perp_funding_handler._chain_map` still mirrors the venue-as-chain convention — those dropped it 2026-07-08, so this handler is the ONLY remaining site). | market-tick-data-service is a **LIVE claim by another agent** — its dirty set GREW during this session (10 files: aster adapter/ws/client, polymarket_adapter, 2 migrate scripts, 3 test files). Running a gate there would gate their in-flight work; committing would race them. Multi-agent rule: live claim → PROTECT, do not inherit. | Working tree change is intact; also snapshotted as dangling commit `dded7f544` (tag `wip-slot3-venue-chain-fix`) + copies in the session scratchpad. Ship once MTDS is quiet: gate + commit ONLY `cli/handlers/onchain_perp_batch_handler.py` + `tests/unit/test_onchain_perp_batch_handler.py`. |
| **Paired manifest re-stamp** for the above (operator-approved "one pass")                                                                                          | NOT STARTED                                                                                                                                                                                                                                                                                                          | Blocked on the writer fix landing. `chain` is a ROW-KEY column, so the re-stamp must run WITH the writer fix or row identity forks.                                                                                                                                                                                                        | Sequence: snapshot `_index` → dry-run counts → **collision pre-flight (HARD GATE — abort if any post-blank row_key collides)** → CAS-apply → verify HOLDS across 2 consolidator cycles incl. one `--force`.                                                                                      |
| **Detector D1b** (defi venues vs `ALL_DEFI_VENUES` vocabulary, not the phase-gated live subset)                                                                    | NOT STARTED                                                                                                                                                                                                                                                                                                          | Discovered late in the session while executing the (invalid) defi venue additions.                                                                                                                                                                                                                                                         | Tracked as a todo above. No registry/denominator impact — pure detector change.                                                                                                                                                                                                                  |
| **IS `_LEGACY_INSTRUMENT_TYPE_ALIASES`** add `'options_chain': 'OPTION'`                                                                                           | NOT STARTED                                                                                                                                                                                                                                                                                                          | instruments-service also has foreign WIP (catalogue + enumerate_expected_universe + a new dedup script).                                                                                                                                                                                                                                   | Single-line addition + test; ship when IS is quiet.                                                                                                                                                                                                                                              |
| **MDPS `_type_token_from_canonical_id` `parts[1]` parse**                                                                                                          | NOT STARTED — annotate only                                                                                                                                                                                                                                                                                          | Owned by `sports_consolidated_closeout_2026_07_19.md` Track C F1/F2; do NOT fork the fix.                                                                                                                                                                                                                                                  | Annotate the finding on that plan.                                                                                                                                                                                                                                                               |

### 2026-07-20 — UAC additions SHIPPED, and RC-4's "missing defi venues" premise was WRONG

**Shipped:** `uac@bb42d8ee` (RESTAKING enum) + `uac@b6a1d83a` (20 ODDS_API bookmakers). Runtime-verified against the
shipped registry: `InstrumentType.RESTAKING` resolves; `VENUES_BY_ASSET_GROUP['sports']` 8 → 28.

Adding an enum member / venue is never a one-line change here — the registry's own guards caught **two** consumers I had
missed, each a test failure rather than a silent gap: `INSTRUMENT_TYPE_FOLDER_MAP` (RESTAKING), then
`VENUE_TO_ADAPTER_KEY` + the declared `EXPECTED_SENTINEL_VENUES` set (bookmakers). All 20 bookmakers map to
`NO_ADAPTER_YET` with the reason stated, because their odds arrive via the ODDS_API aggregator (Decision C, MTDS-owned)
and no per-bookmaker IS adapter exists or is planned — sentineling is a decision the guard forces you to declare.

**The defi half was CANCELLED as invalid.** RC-4 claimed 15 defi protocols were "missing from
`VENUES_BY_ASSET_GROUP['defi']`". They are not missing — every one already exists in
`registry/defi_venues.py::ALL_DEFI_VENUES` (170 entries) with `phase="pipeline"`. That key is DERIVED and phase-gated:

```python
"defi": list(dict.fromkeys(v for v in _ALL_DEFI_VENUES if _DEFI_VENUE_PHASE.get(v) == "live"))
```

Measured: 170 total = 93 `live` + 42 `pipeline`. ANKR/FRAX/MAKER/STADER/STAKEWISE/SWELL/ACROSS/STARGATE/FLASHBOTS/
MANTLE-ETHEREUM are ALL present, all `pipeline`. `defi_venues.py:424` states the invariant:

> `# INVARIANT: phase=="live" ⟺ venue is IS-producible (in _build_defi_venues()).`

`phase` is a CAPABILITY assertion, not a naming one. Flipping these to `live` would assert instruments-service can
produce them when it cannot (no adapter), break the `set(_build_defi_venues()) == VENUES_BY_ASSET_GROUP['defi']` guard
(`instruments-service/.../orchestrator/defi.py:107`), and pad the honest-coverage denominator with venues that CANNOT be
captured — making that coverage permanently unachievable, the opposite of the honest-denominator intent.

**INDEPENDENT CONFIRMATION (same day, different agent).** While this was being shipped, `uac@83f17c46` landed:

> `fix(defi): revert CHAINLINK-* to phase=pipeline, no adapter key — chainlink.py was never built in instruments-service, breaking the IS adapter-routing invariant on the LDR->main promotion gate (instruments-service#873, quality-gates-v2 red).`
> Exactly the predicted failure mode, reached independently: a defi venue flipped to `live` without a real IS adapter
> turned **quality-gates-v2 RED on the promotion gate** and had to be reverted. Executing RC-4 as filed would have
> reproduced that breakage fifteen-fold. Corrected remedy stays **detector D1b** — compare the manifest against the
> `ALL_DEFI_VENUES` VOCABULARY, never the phase-gated capability subset.

### 2026-07-20 — UAC additions SHIPPED, and RC-4's "missing defi venues" premise was WRONG

**Shipped:** `uac@bb42d8ee` (RESTAKING enum) + `uac@b6a1d83a` (20 ODDS_API bookmakers). Runtime-verified against the
shipped registry: `InstrumentType.RESTAKING` resolves; `VENUES_BY_ASSET_GROUP['sports']` 8 → 28.

Adding an enum member / venue is never a one-line change here — the registry's guards caught **two** consumers missed on
the first pass, each as a test failure rather than a silent gap: `INSTRUMENT_TYPE_FOLDER_MAP` (RESTAKING), then
`VENUE_TO_ADAPTER_KEY` + the declared `EXPECTED_SENTINEL_VENUES` set (bookmakers). All 20 bookmakers map to
`NO_ADAPTER_YET` with the reason stated — their odds arrive via the ODDS_API aggregator (Decision C, MTDS-owned), no
per-bookmaker IS adapter exists or is planned; the guard forces sentineling to be a declared decision.

**The defi half was CANCELLED as invalid.** RC-4 claimed 15 defi protocols were "missing from
`VENUES_BY_ASSET_GROUP['defi']`". They are NOT missing — every one already exists in
`registry/defi_venues.py::ALL_DEFI_VENUES` (170 entries) with `phase="pipeline"`. That key is DERIVED and phase-gated:

```python
"defi": list(dict.fromkeys(v for v in _ALL_DEFI_VENUES if _DEFI_VENUE_PHASE.get(v) == "live"))
```

Measured: 170 total = 93 `live` + 42 `pipeline`. ANKR / FRAX / MAKER / STADER / STAKEWISE / SWELL / ACROSS / STARGATE /
FLASHBOTS / MANTLE (-ETHEREUM) are ALL present, all `pipeline`. `defi_venues.py:424` states the invariant:

> `# INVARIANT: phase=="live" <=> venue is IS-producible (in _build_defi_venues()).`

`phase` is a CAPABILITY assertion, not a naming one. Flipping these to `live` would assert instruments-service can
produce them when it cannot (no adapter), break the `set(_build_defi_venues()) == VENUES_BY_ASSET_GROUP['defi']` guard
(`instruments-service/.../orchestrator/defi.py:107`), and pad the honest-coverage denominator with venues that CANNOT be
captured — permanently unachievable coverage, the opposite of the honest-denominator intent.

**INDEPENDENT CONFIRMATION (same day, different agent).** While this shipped, `uac@83f17c46` landed:
`fix(defi): revert CHAINLINK-* to phase=pipeline, no adapter key — chainlink.py was never built in instruments-service, breaking the IS adapter-routing invariant on the LDR->main promotion gate (instruments-service#873, quality-gates-v2 red).`
Exactly the predicted failure mode, reached independently: a defi venue flipped to `live` without a real IS adapter
turned quality-gates-v2 RED on the promotion gate and had to be reverted. Executing RC-4 as filed would have reproduced
that breakage fifteen-fold. Corrected remedy stays **detector D1b** — compare the manifest against the `ALL_DEFI_VENUES`
VOCABULARY, never the phase-gated capability subset.

**Process note:** three earlier attempts to record this were silently lost. Root cause = the `check-branch-drift`
pre-commit hook performs its own pull/rebase ("files were modified by this hook"), which resets an UNCOMMITTED working
file to origin's version mid-commit. Lesson: in this repo, `git pull --ff-only` FIRST, then edit, then commit
immediately — never append while behind origin.

### 2026-07-20 15:46 local — MTDS still NOT shippable; index hazard found + neutralised

Re-checked whether market-tick-data-service had gone quiet enough to ship the venue-as-chain fix. It has **not** — the
repo is in a worse state than at the first check:

1. **Orphaned merge conflict.** `tests/unit/test_pipeline_e2e_prediction_canonical.py` is `UU` with 4 conflict markers,
   but there is NO `.git/MERGE_HEAD`, `REBASE_HEAD`, `rebase-merge` or `rebase-apply`. A merge/rebase died mid-conflict
   and left the index wedged; nobody is actively resolving it. Committing anything from this index would commit an
   unresolved conflicted file.
2. **A `git add -A`-style sweep staged EVERYTHING**, including this session's two unrelated venue-as-chain files. All 10
   modified files were `M ` (staged). Had any agent, hook, or cron committed from that index, the venue-as-chain fix
   would have been swept into an unrelated aster/cefi-migration commit — wrong attribution, no gate run on it, bundled
   with a conflicted file. This is exactly the failure the "stage by name, never `git add .`/`-A`" rule prevents.

**Action taken (surgical, non-destructive):** `git restore --staged` on ONLY the two files owned by this session
(`cli/handlers/onchain_perp_batch_handler.py`, `tests/unit/test_onchain_perp_batch_handler.py`). Working-tree content is
unchanged and still present; the other 9 staged files and the conflicted file were left exactly as found — the other
agent's work and its resolution remain entirely theirs. Verified after: 0 of my files staged, 9 of theirs still staged,
my change still in the working tree, `UU` state preserved.

**Ship gate for the venue-as-chain fix (unchanged, all must hold):** (a) `UU` conflict resolved by its owner and the
index clean of foreign staged files; (b) MTDS dirty set quiet; (c) `quality-gates.sh` green; (d) commit ONLY the two
named files; (e) then the paired manifest re-stamp with snapshot → dry-run → **collision pre-flight HARD GATE** → CAS →
HOLD-verify across 2 consolidator cycles incl. one `--force`. Recovery if the working tree is ever clobbered: dangling
commit `dded7f544` (tag `wip-slot3-venue-chain-fix`) + copies under the session scratchpad `wip-mtds/`.

### 2026-07-20 ~19:30 UTC — watcher v1 retired (wrong metric), v2 armed (functional check)

v1 gated on `foreign_dirty==0`. Measured wrong: MTDS's dirty set grew 1→14→21 files under a live multi-file refactor
(orchestrator `__init__.py`/`venue_fetch.py`/`symbol_rules.py`, live connectors, 3 new scripts) — exact-zero foreign
dirt may never occur on a shared branch, and it doesn't even measure what matters. Confirmed HEAD (last landed commit)
imports cleanly; the noise is uncommitted WIP, not a broken base. **v2 replaces the file-count proxy with a functional
check**: `unmerged==0 AND staged==0 AND` my own test module (`tests/unit/test_onchain_perp_batch_handler.py`) COLLECTS
AND PASSES. That's false exactly when someone's mid-refactor break the shared package import (observed once:
`_SPORTS_TIER2_BOOKMAKER_CATEGORIES` transiently missing from `venue_fetch.py`, self-resolved within minutes) and true
the moment it clears, regardless of how many unrelated files are still dirty. Re-armed, same 15-min cadence, 8h cap.

**Found and left untouched:** `git stash list` carries 3 stale `autostash` entries (2026-07-09, 2026-07-10,
2026-07-20T15:45+01:00) — all pre-date or are unrelated to this session's work, none contain venue-as-chain content.
Likely orphaned by `check-branch-drift`/`git pull --rebase --autostash` cycles from other agents over the past ~11 days.
NOT dropped or popped (destructive, not mine to judge whose WIP that is) — flagged for awareness only. Separately
confirmed my OWN stash/pop cycle (used to verify HEAD importability) completed cleanly with no leftover.

**Caution logged:** an accidental `bash scripts/quality-gates.sh --help` (unrecognized flag) started a REAL gate run
without `--no-fix` before being cut short by a `| head -40` SIGPIPE. Verified no harm: process confirmed dead, no
unexpected diffs, package still imports, `git stash list` shows nothing new. It died in the ENVIRONMENT phase, well
before any lint/format auto-fix stage. Lesson: never invoke this project's `quality-gates.sh` with an unrecognized flag
expecting a no-op `--help` — it silently runs the real gate.
