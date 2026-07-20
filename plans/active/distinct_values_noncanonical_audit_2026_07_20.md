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
