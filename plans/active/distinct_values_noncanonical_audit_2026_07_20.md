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
    /codex/02-data/defi-canonical-naming-ssot.md,
    /plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/active/market_tick_data_service_lending_instrument_type_historical_restamp_2026_07_24.md,
    /plans/archive/2026_07/distinct_values_noncanonical_audit_history_2026_07_24.md,
  ]
created: "2026-07-20"
last_updated: "2026-07-24"
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

The DeFi canonical naming SSOT (`/codex/02-data/defi-canonical-naming-ssot.md`, operator-locked) mandates **bare venue +
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

- `/codex/02-data/defi-canonical-naming-ssot.md` (bare-venue + chain= model — the headline finding rests on this)
- `/codex/02-data/availability-manifest-and-data-status.md`, `/codex/02-data/honest-coverage-model.md`
- UAC `unified_api_contracts/registry/` (`VENUES_BY_ASSET_GROUP`, `DATA_TYPES_BY_ASSET_GROUP`, `InstrumentType`,
  `MAINNET_CHAIN_IDS`, `venue_adapter_keys.DECOMMISSIONED_VENUE_BASES`)

## Todos

- [x] [DATA] P0. ✅ Run the classification fan-out (Workflow) over the full ground truth — 47 agents, **175 findings**
      classified cat1-4 with root cause + owning plan + safety class; every cat3/cat4 call adversarially verified (8
      rate-limited verifiers re-run separately). Evidence: workflow `wf_4d089da8-4db`; synthesis + per-finding JSON in
      the Progress Log. Outcome: 22 owned / 105 detector-SSOT-gap / 41 wrong-axis / **0 executable purges**.
- [x] [BACKEND] P0. ✅ Detector fix (deployment-api `_distinct_values.py`): DeFi `venues` axis compares the bare
      manifest venue against the bare bases of `VENUES_BY_ASSET_GROUP['defi']` (keep other axes/AGs exact). Unit-test
      the bare-base reduction (76 → ~28). Ship + flip. **RECONCILIATION 2026-07-22**: shipped in two passes —
      `deployment-api@96499dd` (D1+D3 grain fix, measured 175→115 non-canonical) then further corrected by
      `deployment-api@ea56fff` (D1b: compare against `ALL_DEFI_VENUES` vocabulary, not the phase-gated `live` subset;
      defi venues 25→9). Both verified ancestors of `origin/live-defi-rollout`. See "Refined worklist" first bullet +
      the Deferred-work table's "Detector D1b" row below for the full evidence — not duplicated here.
- [ ] [DATA] P1. UAC SSOT additions (category 2) that are unambiguous and NOT contested by an in-flight migration —
      legit-but-missing venues/data_types/instrument_types — added to the correct `VENUES_BY_ASSET_GROUP` /
      `DATA_TYPES_BY_ASSET_GROUP` / `InstrumentType`. Each addition cited against a source (adapter/registry/SSOT).
      **PARTIALLY RESOLVED 2026-07-22** — every unambiguous cat-2 addition identified has an executed disposition: the
      `RESTAKING` `InstrumentType` (uac@bb42d8ee, unambiguous, done); the 15 defi-protocol "additions" resolved to NOT a
      registry add (already present in `ALL_DEFI_VENUES` phase-gated `pipeline`, correctly left there — see "UAC
      additions SHIPPED, and RC-4's premise was WRONG" below — addressed instead via detector D1b + the additive
      `DEFI_VENUE_MTDS_ADAPTER_VERIFIED_NOT_YET_SCHEDULED` marker for 6 of them, `uac@91b6f094`); the 20 sports ODDS_API
      bookmakers resolved to an explicit NON-addition/revert per operator ruling (`uac@9908520b`). **RESOLVED
      2026-07-22** — the two remaining category-2 detector/SSOT gaps from the "Refined worklist → Executable safe-code"
      section have both now shipped: D2 (cefi venue fold `OKX-SWAP`/`OKX-FUTURES`→`OKX` dialect spellings, 3-repo ship,
      see the "D2 shipped" Progress Log entry) and D5 (bundle-grain `futures_chain`/`options_chain` recognition on the
      tradfi+cefi `instrument_types` axis, `unified-api-contracts@030d64d8` + `deployment-api@7f0fc1cd`, see the D5/D6
      Refined-worklist item below). D6 (scoping `data_types` away from MDPS `swaps_ohlcv_*`) was investigated and
      correctly stopped short of a UAC canonical-set addition whose denominator blast radius needs measuring first —
      filed as `plans/active/issues/defi_swaps_ohlcv_candle_data_types_axis_gap_2026_07_22.md` (mirrors the sibling
      `perp_daily_ctx` stop-short precedent on this same plan). No category-2 items remain open in this todo's own
      scope; D6's remainder is tracked on its issue doc, not here.
- [x] [DATA] P1. ✅ Wrong-axis writer root-cause (category 3): for each mis-stamp cluster, locate the
      writer/consolidator that populates the wrong column; fix the clearly-ours bugs; annotate the rest to their owning
      plan/issue. **PARTIALLY RESOLVED 2026-07-22** — every identified cluster has been either fixed or correctly
      annotated elsewhere: MTDS `onchain_perp_batch_handler.py` venue-as-chain (writer fixed `mtds@accd8aa4` +
      historical re-stamp APPLIED AND VERIFIED — see the line-290 item below, now flipped); IS `writers.py`
      `options_chain`→ `OPTION` legacy alias (`instruments-service@981c5061`, shipped); MDPS
      `canonical_writer_shaping.py::     _type_token_from_canonical_id` `parts[1]` bookmaker/chain mis-stamp (correctly
      NOT forked here — already annotated on its owning plan, `sports_consolidated_closeout_2026_07_19.md` Track C
      F1/F2, confirmed present there, cross-linking back to this doc's RESULT/RC-3). **FORKED 2026-07-24** — the one
      remaining writer half-fix (MTDS `liquidations_handler.py`'s lending `instrument_type` writer, disk+manifest stamp
      fixed `mtds@fec20de2`, historical rows still stamped `instrument_type="liquidation"` and not yet re-stamped) is
      now its own dedicated plan,
      `/plans/active/market_tick_data_service_lending_instrument_type_historical_restamp_2026_07_24.md` (size-cap split
      of this doc). No open work remains directly on this todo — see that plan for the re-stamp todos.
- [ ] [DATA] P1. Reconcile every drift cluster (category 1) to its owning in-flight plan; any cluster owned by NO plan →
      file an issue doc or add a P-todo to the right plan (no orphan drift). **PARTIALLY RESOLVED 2026-07-22** — the 22
      cat1 findings' owning-plan attribution was performed AS PART OF the classification fan-out itself (todo #1 above),
      scoped against this doc's `related:` frontmatter (the 5 AG consolidated-closeout + migration-catalogue plans); the
      one cat1-adjacent cluster that surfaced through later cat3 investigation (MDPS `parts[1]` parse, covering both the
      sports bookmaker-in-instrument_type AND `H2H`/`MATCH_ODDS`/`SPREADS`-as-chain clusters) is confirmed explicitly
      annotated on its owning plan (`sports_consolidated_closeout_2026_07_19.md` Track C F1/F2, cross-linked both
      directions — checked directly, present). **Still open / not independently re-verifiable** — the raw 175-finding
      per-cluster JSON (which would let a reader individually confirm all 22 cat1 owning-plan citations, not just the
      one spot-checked above) was later deleted from the scratchpad during the 2026-07-21 pre-compact sweep as
      "regenerable/superseded" (see that entry below); there is no remaining text-traceable enumeration of the other 21
      cat1 clusters' specific owning-plan citations inside this doc or the repo. Absent a re-run of the 47-agent
      classification workflow (impractical per the 2026-07-22 tick-3 entry's own assessment), this cannot be fully
      closed out from documentation alone — keep open as a "spot-checked, not exhaustively re-verified" item rather than
      either blank-flipping it or claiming a false-negative-free guarantee.
- [x] [OPERATOR] P1. ✅ BLOCKED-OPERATOR-DECISION — verified PURGE worklist (category 4): exact (asset_group, axis,
      value, row_count, GCS/catalogue locations, why-junk) for operator one-tap approval. NO blind deletion. **RESOLVED
      2026-07-22** — the worklist WAS produced and adversarially verified per-item; its answer is that the worklist is
      EMPTY (every candidate walked back to quarantine/re-stamp/keep, several against standing operator rulings — see
      "PURGE worklist — EMPTY" section below for the full verdict table). Producing a verified worklist that turns out
      to contain zero executable purges is a complete, correct answer to this todo's ask, not a non-answer — there is
      nothing left requiring operator one-tap approval.
- [x] [REVIEW] P2. ✅ Post-audit: update `/codex/02-data/defi-canonical-naming-ssot.md` / manifest SSOT if the
      detector-model finding changes a documented contract; confirm the panel now reflects true drift. **RESOLVED
      2026-07-22** — (a) no codex SSOT edit was needed: the headline finding (see "Headline finding" section above)
      established the DOCUMENTED CONTRACT (bare venue + separate `chain=` segment) was already correct all along — the
      bug was in the DETECTOR's comparison code, never in the SSOT text, so there was no stale contract to correct; (b)
      "confirm the panel now reflects true drift" is directly measured and shipped: `deployment-api@96499dd` (175→115) +
      `@ea56fff` (D1b, defi venues 25→9) + `@5295c76` (sports bookmaker accepted-exceptions) are all live on
      `origin/live-defi-rollout` (verified via `git merge-base --is-ancestor`), each with its own before/after
      measurement cited in the Progress Log below.

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
- [x] ✅ [BACKEND] P2. **D2 — cefi venue fold, SHIPPED across 3 repos (2026-07-22).** Promoted `_CEFI_VENUE_FOLD` from
      an instruments-service-local dict to a UAC export (`unified-api-contracts@21dbaf0c` + a correctness fix
      `@f6051e1b`); instruments-service now imports it instead of hardcoding its own copy
      (`instruments-service@13cda0dc`); deployment-api wires it into `_ACCEPTED_EXCEPTIONS[     ("venues", "cefi")]`
      (`deployment-api@d1a82696`). **Real finding caught by the existing test suite mid-ship**: `OKX-SWAP`/`OKX-FUTURES`
      were SEPARATELY promoted to direct `VENUES_BY_ASSET_GROUP['cefi']` membership on 2026-07-21 (a different, prior
      fix — real, actively-captured venues in their own right), so a naive "fold-map-keys = accepted-exceptions"
      derivation would have wrongly hidden them from the panel instead of showing them correctly badged
      `is_canonical: true`. Fixed by deriving the accepted-exceptions set as
      `CEFI_VENUE_FOLD keys MINUS VENUES_BY_ASSET_GROUP['cefi']` — the remaining 8 (COINBASE, BYBIT-FUTURES,
      COINBASE-INTERNATIONAL, OKEX, OKEX-SWAP, OKEX-FUTURES, CRYPTOFACILITIES, BITFINEX-DERIVATIVES) are the
      genuinely-still-non-canonical dialect spellings this fix actually targets. All 3 repos' quality-gates.sh green,
      `test_cefi_venue_axis_keeps_exact_compare` (which asserts OKX-FUTURES badges canonical) still passes.
- [x] ⚠️ [DATA] P2. **D5/D6 — INVESTIGATED + D5 SHIPPED, D6 stopped short 2026-07-22 (dispatched sub-agent).** D5
      (bundle-grain `futures_chain`/`options_chain` recognition on the tradfi+cefi `instrument_types` axis — `combo`
      deliberately excluded, its leg-aware id format is unsettled, mirroring this registry's own
      `TRADFI_CHAIN_INSTRUMENT_TYPES` exclusion) **SHIPPED**: `unified-api-contracts@030d64d8` (new
      `CHAIN_BUNDLE_ACCEPTED_NONCANONICAL_INSTRUMENT_TYPES` export, mirrors
      `TRADFI_CHAIN_SNAPSHOT_ACCEPTED_NONCANONICAL_DATA_TYPES`'s exact mechanism) + `deployment-api@7f0fc1cd` (wires it
      into `_ACCEPTED_EXCEPTIONS[("instrument_types","tradfi")]`/`[("instrument_types","cefi")]`), both verified
      ancestors of `origin/live-defi-rollout`. Measured on the 2026-07-21 live rollup: tradfi.instrument_types
      non-canonical 9→7 (options_chain/futures_chain cleared; `combo`/`equity`/`etf`/`future`/`index` lowercase
      case-drift correctly still flagged, untouched — owned by the in-flight tradfi uppercase migration, not this fix),
      cefi.instrument_types 4→2 (options_chain/futures_chain cleared; `perpetual`/`spot` lowercase still flagged). Real
      captured rows this recognises: tradfi `futures_chain` 154,147 + `options_chain` 121,031 at this axis (cefi's are 0
      captured, 100% empty_confirmed/expected_unattempted — real registered adapters, just no captured data yet). D6
      (scoping `data_types` away from MDPS `swaps_ohlcv_*`) **investigated but NOT shipped** — confirmed these are real,
      correctly-produced MDPS Phase-5b.1 processed-candle output (not a "wrong coverage.json section" bug:
      `_AXIS_SOURCES` correctly reads the same section for every asset_group; the gap is that
      `DATA_TYPES_BY_ASSET_GROUP['defi']` never got these 7 keys added, while cefi's `ohlcv_1m` / tradfi's
      `ohlcv_{1s,1m,15m,24h}` / sports' `odds_horizon_bucket` — the analogous MDPS candle keys for THEIR asset_groups —
      already are present). The conceptually-correct fix genuinely is a `DATA_TYPES_BY_ASSET_GROUP` addition, but traced
      the exact denominator mechanism (`enumerate_expected_universe.py::enumerate_v2`'s generic branch cross-joins
      `DATA_TYPES_BY_ASSET_GROUP[ag]` against the full catalog × date_axis) and found a directly analogous precedent
      already patched for tradfi (`_TRADFI_MTDS_TICK_MANIFEST_EXCLUDED_DATA_TYPES`, guarding against exactly this "real
      producer is a DIFFERENT service/bucket" shape) with no defi-scoped equivalent existing today — adding the 7 keys
      without one would very likely repeat that permanently-unsatisfiable-cell failure mode fleet-wide for defi.
      Declined per this plan's own RESULT 4 caution + the AUTONOMOUS_AGENT_RULES stop-short precedent (mirrors the
      sibling `perp_daily_ctx` outcome on this same plan). Full evidence + two remediation paths (build the exclusion
      guard first vs. an accepted-exception stopgap) + live row-count table filed as
      `plans/active/issues/defi_swaps_ohlcv_candle_data_types_axis_gap_2026_07_22.md`. Also checked: `dex_pools`
      (454,077 captured) / `dex_swaps` (3,458,668 captured) / `rate_indices` (49,096 captured) — the other 3 of the
      original 10 `defi.data_types` non-canonical values — are STILL live today, but confirmed cat-1
      (kebab/snake/legacy-name naming drift already extensively tracked by
      `master_data_canonicalisation_migration_catalogue_2026_06_07.md`'s own dedicated migration scripts); the "FOLDED +
      DELETED 2026-07-21" Progress Log note refers to a DIFFERENT thing (legacy GCS object-path PREFIXES, not this
      manifest COLUMN VALUE) — not touched here, not this plan's scope. No code changed in
      market-data-processing-service or instruments-service for D6.
- [x] ⚠️ [DATA] P1. **`perp_daily_ctx` / `perp_funding` manifest-invisibility — INVESTIGATED 2026-07-22,
      `derivative_ticker` migration DECLINED (live-reader risk), safe alternative proposed instead.** Original framing
      (below, kept for record) was only half right: `perp_funding` is ALREADY a registered canonical data_type with a
      full `SchemaContract` (`DEFI_PERPETUAL_PERP_FUNDING`, `contracts.py:745-758`; `DATA_TYPES_BY_ASSET_GROUP['defi']`)
      — only `perp_daily_ctx` is the genuine gap. More importantly: `CanonicalPerpFundingProvider`
      (`strategy-service/.../canonical_perp_funding_provider.py`) reads EXACTLY `perp_funding`+`perp_daily_ctx` TODAY,
      and is instantiated directly by the live paper-trading CLI (`paper_run_handler.py:931-932`) — the shared bucket
      already holds YEARS of real, migrated HYPERLIQUID/GMX/CeFi funding+mark history at this exact shape (the
      2026-07-13 `defi_dedicated_bucket_shared_migration` copied it forward, verified via `funding_for_day(2026-05-18)`
      → 697 real observations). Migrating onto `derivative_ticker` as originally proposed would require rewriting that
      live reader + backfilling/dual-reading real production history, and would pre-empt an already-gated,
      NOT-yet-approved separate design decision
      (`defi_perp_funding_canonicalisation_derivative_     ticker_all_perps_2026_07_15.md`'s open `[DESIGN] P1` "demote
      perp_funding to a derived view" todo — explicitly "do NOT execute before parity evidence exists", and scoped to
      `perp_funding` only, not even `perp_daily_ctx`). Declined per this task's explicit safety override. **Full
      investigation + safe incremental proposal (register `perp_daily_ctx` as its own canonical data_type, add manifest
      writes to both ad-hoc writers with NO schema change, backfill manifest rows for already-migrated historical
      shards) filed as `plans/active/issues/defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md`** — that doc's
      own todos are the real next steps; not duplicated here. Also found: the MTDS HL backfill script
      (`backfill_hl_mark_price_from_s3_asset_ctxs_2026_06_17.py`) targets a bucket CONFIRMED DELETED
      (`gcloud storage     buckets describe gs://perp-funding-central-element-323112` → 404) — its disposition is
      already an open P3 todo in `defi_dedicated_bucket_shared_migration_2026_07_13.md`, not duplicated/touched here to
      avoid collision. No code changed in market-tick-data-service, features-service, or strategy-service.
      <details><summary>Original framing (2026-07-22 side investigation, superseded by the above)</summary>

      structurally invisible to this audit's detector, found by a 2026-07-22 side investigation, not by the panel.
                                                                                                          Neither is a canonical `data_type` (no member in `DATA_TYPES_BY_ASSET_GROUP['defi']`), and neither shows up in
                                                                                                          this doc's non-canonical inventory at all — both are written via raw `gcsfs` calls with **zero manifest writes**
                                                                                                          (`market-tick-data-service/scripts/backfill_hl_mark_price_from_s3_asset_ctxs_2026_06_17.py:15,44`,
                                                                                                          `features-service/features_service/cefi/calculators/perp_funding_corpus.py:304,314`; corroborated by
                                                                                                          `plans/active/issues/mtds_plan_reconciliation_2026_06_29.md:384` "MD5 `perp_daily_ctx` manifest-invisible —
                                                                                                          CONFIRMED"). Per operator ruling 2026-07-15, UAC already defines the target shape —
                                                                                                          `unified_api_contracts/internal/schemas/contracts.py:766-782` `DEFI_PERPETUAL_DERIVATIVE_TICKER`
                                                                                                          (`asset_group=defi, instrument_type=perpetual, data_type=derivative_ticker`) carries `funding_rate`/`mark_price`/
                                                                                                          `open_interest`/`index_price` as EMBEDDED FIELDS, mirroring `CEFI_PERPETUAL_DERIVATIVE_TICKER` exactly. Todo:
                                                                                                          migrate both writers onto `derivative_ticker` (real manifest rows, real schema) and retire the raw-gcsfs path —
                                                                                                          until then this cluster will keep costing real coverage/completeness accuracy without ever tripping the
                                                                                                          distinct-values panel, since the panel only ever sees what's in the manifest.
                                                                                                          </details>

### D4 — DELIBERATELY REJECTED (do not implement)

- The synthesis proposed gating the `chains` axis to `asset_group=='defi'`. **Verification proved this would HIDE two
  live defects**: (a) the cefi chain values are a real MTDS writer bug (below), (b) sports `H2H`/`MATCH_ODDS`/`SPREADS`
  are real drift whose faithful detectors must keep surfacing it. Leaving the axis un-gated is CORRECT.

### Writer bugs — real, but each needs a PAIRED manifest re-stamp (operator-gated)

- [x] [DATA] P1. ✅ **MTDS `onchain_perp_batch_handler.py:131-139` `_VENUE_CHAIN`** stamps each cefi on-chain-perp venue
      as its own chain (HYPERLIQUID/ASTER/EXTENDED-STARKNET/LIGHTER-ZKSYNC), contradicting UAC
      `SHARD_AXIS_MATRIX[("market-tick-data-service","cefi")]` which has NO `chain` axis. instruments-service already
      excised this exact defect (`writers.py::_canonical_manifest_venue_chain` → `(venue, "")`, regression-tested); MTDS
      never got it, and the same pattern is mirrored in the live-WS recorder + perp_funding handler. ⚠️ **The writer fix
      ALONE is unsafe**: `chain` is a ROW-KEY column (`unified-trading-library/manifest_writer/     _rows.py:99`), so
      flipping it to `""` gives future writes a DIFFERENT row identity than the historical `chain=<VENUE>` rows →
      fragmented shards, broken `expected_unattempted`→`captured` supersede, double-counted coverage. Requires writer
      fix + paired re-stamp of existing rows, applied together. **RECONCILIATION 2026-07-22 — BOTH HALVES NOW CLOSED,
      verified before flipping**: writer fix `mtds@accd8aa4` re-confirmed an ancestor of `origin/live-defi-rollout`
      (`git merge-base --is-ancestor`, re-checked this session); the paired historical-row re-stamp is APPLIED AND
      VERIFIED per the Deferred-work table row below ("Paired manifest re-stamp for the above") and the "2026-07-22 —
      Operator authorized the cron pause" Progress Log entry — `10,493,523 → 10,490,576` rows, 952 deduped + 1,995
      promoted, 0 duplicate row_keys post-write, cron resumed + confirmed `ENABLED`. No longer BLOCKED-OPERATOR-DECISION
      — the operator decision was obtained and executed.
- [ ] [DATA] P1. **MDPS `canonical_writer_shaping.py::_type_token_from_canonical_id`** — highest-yield single bug in the
      corpus. It assumes a 3-segment cefi `VENUE:TYPE:SYMBOL` id and takes `parts[1]`; sports ids are 8-segment
      `SPORT:BOOKMAKER:MARKET:...`, so `parts[1]` is the BOOKMAKER, and it OUTRANKS the explicit `instrument_type`
      column. One function produces the entire 13-value bookmaker-in-instrument_type cluster (and, via
      `build_instrument_catalogue.py::_instrument_type_from_id`, the same shape in the IS catalogue). Fix the PARSE, not
      the readers. Owned by `sports_consolidated_closeout_2026_07_19.md` Track C F1/F2 — annotate there, do not fork.
- [x] [DATA] P2. ✅ Writer half fixed — `market-tick-data-service@fec20de2` ("single-resolution-point instrument_type
      for market/event lending writers"), verified ancestor of `origin/live-defi-rollout`. Both the manifest stamp
      (`liquidations_handler.py:441`, `.value.lower()`) and the disk write (`:551`) now derive from the SAME
      `resolve_lending_instrument_type(protocol)` call — no more manifest-vs-disk desync going forward. **FORKED
      2026-07-24**: the deferred historical-row re-stamp (rows still stamped `instrument_type="liquidation"`, the count
      the distinct-values census reads) is now tracked as its own plan,
      `/plans/active/market_tick_data_service_lending_instrument_type_historical_restamp_2026_07_24.md` (size-cap split
      of this doc) — not duplicated here.
- [x] [BACKEND] P3. ✅ instruments-service `writers.py::_LEGACY_INSTRUMENT_TYPE_ALIASES` — add
      `'options_chain': 'OPTION'` for parity with the existing `'futures_chain': 'FUTURE'`. **SHIPPED —
      instruments-service@981c5061.** Test extended
      (`test_split_by_instrument_type_canonicalizes_extended_legacy_aliases`), verified on origin.

### Operator decisions — RULED 2026-07-22 (chat, this session), now executable todos

**DeFi venue additions (15 protocols) — operator ruling**: "test the adaptors, try a sample day backfill for data types
across each venue. If they are already built and work great, [add them]. If not and [an adapter is] easy enough given
our existing protocols/data sources, try them out and build the adaptors. If it's not working, drop them." — i.e. NOT a
blind UAC addition; each of the 15 gets a real capture attempt first, and only proven-working venues get added to
`VENUES_BY_ASSET_GROUP['defi']`.

- [x] [DATA] P1. For each of ANKR, FRAX, MAKER, STADER, STAKEWISE, SWELL, MANTLE, ACROSS, STARGATE, FLASHBOTS, ALCHEMY,
      JUPITER, BLAZESTAKE, KAMINO_LENDING, MORPHOVAULTS: check whether an `instruments-service`/MTDS adapter already
      exists and captures real data (sample-day backfill test); if none exists, assess whether one is buildable quickly
      against an existing protocol pattern/data source already in the codebase and attempt it; if a venue's capture
      genuinely doesn't work (no adapter feasible / API unavailable / not actually a distinct protocol), drop it from
      the UAC-addition list rather than adding a venue with structural 0% coverage. Add ONLY the venues that end up with
      verified working capture to `VENUES_BY_ASSET_GROUP['defi']`, cited against the adapter/test evidence. Measure +
      document the before/after `completeness_pct` delta from whatever subset actually gets added (per the original
      rule-11 blast-radius concern) — this is now expected, not a red flag, since the denominator only grows for venues
      we can actually now capture.

      **DONE 2026-07-22.** Real sample-day backfill against all 15: 14/15 already had working, production-proven
                                                                                                                                                                                                                  capture (verified with real on-chain/API calls, no code changes needed for 12 of them); ACROSS + STARGATE
                                                                                                                                                                                                                  needed and got real fixes (`market-tick-data-service@a32dd58c`/`@4c21c7f6` — dead subgraph replaced with real
                                                                                                                                                                                                                  on-chain Swap-log queries); FLASHBOTS' pipeline_mode was wrong (subgraph→onchain_rpc, `mtds@6bf6012a`);
                                                                                                                                                                                                                  MORPHOVAULTS had a wrong on-chain vault address resolving to a different vault entirely (`mtds@6bf6012a`,
                                                                                                                                                                                                                  verified correct via `convertToAssets` at block 25573787); MAKER's capture moved handlers (vault_share_price→
                                                                                                                                                                                                                  lst_rates) without the capability registry following (`uac@328a5cea`). All 15 were **already** in
                                                                                                                                                                                                                  `ALL_DEFI_VENUES` (the full registry) — the literal "add" instruction against that registry was a no-op.

                                                                                                                                                                                                                  **CORRECTION (same day, follow-up investigation) — this was NOT the whole picture.** `ALL_DEFI_VENUES`
                                                                                                                                                                                                                  membership is NOT what the honest-coverage denominator actually reads.
                                                                                                                                                                                                                  `VENUES_BY_ASSET_GROUP['defi']` (the list `expected_universe.py`/`check_enumeration_completeness.py` actually
                                                                                                                                                                                                                  iterate to build the `completeness_pct` denominator) is a PHASE-FILTERED subset —
                                                                                                                                                                                                                  `unified-api-contracts/.../market_data_categories.py:395` keeps only `DEFI_VENUE_PHASE=="live"` entries. 11 of
                                                                                                                                                                                                                  these 15 venues (ANKR/FRAX/MAKER/STADER/STAKEWISE/SWELL/MANTLE/ACROSS/STARGATE/FLASHBOTS/ALCHEMY) are
                                                                                                                                                                                                                  `phase=="pipeline"`, so despite being real, working, verified captures shipped today, they are STILL
                                                                                                                                                                                                                  structurally excluded from `completeness_pct` for `defi` — confirmed via a full code trace (Step
                                                                                                                                                                                                                  A→B→C: `market_data_categories.py:395` → `expected_universe.py:287` →
                                                                                                                                                                                                                  `check_enumeration_completeness.py:512`), not a guess. The "measure the before/after `completeness_pct` delta"
                                                                                                                                                                                                                  instruction in this todo's own text was therefore never actually actionable — there IS no delta yet, because
                                                                                                                                                                                                                  the venues never entered the denominator in the first place. See
                                                                                                                                                                                                                  `plans/active/issues/defi_venue_phase_live_definition_contradiction_2026_07_22.md` (upgraded P2→P1,
                                                                                                                                                                                                                  `nature: issue`, 2026-07-22) for the full trace + the operator decision needed before this can actually be
                                                                                                                                                                                                                  fixed. **This todo stays flipped `[x]` because the CAPTURE work (the actual ask) is done and verified — the
                                                                                                                                                                                                                  denominator-visibility gap is real but is now separately tracked, not silently rolled into "done" here.**

                                                                                                                                                                                                                  JUPITER: router-only, swap volume already flows through directly-captured pools (Raydium/Orca/Meteora/Phoenix)
                                                                                                                                                                                                                  — kept as-is per the survey's "may be architecturally redundant" read, not force-built.

                                                                                                                                                                                                                  ~~**One real finding NOT resolved, filed separately**: `DEFI_VENUE_PHASE` still labels 11 of these
                                                                                                                                                                                                                  (ANKR/FRAX/MAKER/STADER/STAKEWISE/SWELL/MANTLE/ACROSS/STARGATE/FLASHBOTS/ALCHEMY) `"pipeline"` despite verified
                                                                                                                                                                                                                  real MTDS capture, because the registry carries two contradictory definitions of `"live"` (2026-05-07
                                                                                                                                                                                                                  data-availability vs 2026-06-29 IS-producibility invariant) — a genuine SSOT contradiction, not something to
                                                                                                                                                                                                                  silently resolve by picking one side.~~ (superseded by the CORRECTION paragraph above — this is confirmed a
                                                                                                                                                                                                                  real coverage-math exclusion, not just a documentation contradiction.) See
                                                                                                                                                                                                                  `plans/active/issues/defi_venue_phase_live_definition_contradiction_2026_07_22.md` for the full finding + the
                                                                                                                                                                                                                  design decision needed before either flipping the phase or correcting the misleading comment.

**Sports ODDS_API bookmakers (19) — operator ruling**: "do NOT add them, in fact remove them everywhere so they don't
come up in audit" — stronger than the original ask (not just "hold," but actively purge references so this class of
finding stops resurfacing).

- [x] [DATA] P1. ✅ Find every place the 19 ODDS_API-fan-out bookmakers appear in the audit's non-canonical-value
      findings / detector output / any registry that currently lists them as "expected but uncaptured," and remove those
      references so they stop generating findings. Do NOT touch the underlying 2026-05-12 scraper-deferral decision
      itself (the operator did not ask to reopen it) — this is purely about the audit/detector no longer flagging
      bookmakers nobody has decided to capture. Confirm via a clean re-run of the audit's classification pass that these
      19 no longer appear. **SHIPPED — `unified-api-contracts@9908520b` + `deployment-api@5295c76`**, both verified
      ancestors of `origin/live-defi-rollout`. See "2026-07-22 (tick 3)" Progress Log entry below for the before/after
      re-run evidence and the 19-vs-20 count discrepancy resolution.

**`restaking` InstrumentType — operator ruling**: add `RESTAKING` as its own canonical `InstrumentType` (confirmed,
matches the recommendation) — PLUS two follow-up questions the operator raised that need answering before the re-stamp:
should eETH/weETH be classified as `RESTAKING` too, and do other LRTs need their WRAPPED variants represented separately
if that's the form AAVE (or other lending venues) actually accepts as collateral?

- [x] [DATA] P2. ✅ `RESTAKING` enum was already shipped earlier this session (`uac@bb42d8ee`) before this todo was
      picked up. Answered the operator's two follow-ups (full research + code citations in the Progress Log below): (a)
      eETH/weETH — **YES, same RESTAKING class as ezETH/rsETH/pufETH**, confirmed by mechanism not name (weETH is
      ether.fi's non-rebasing EigenLayer-restaking receipt wrapper; only weETH is discovered as an instrument in this
      workspace — `etherfi.py` never enumerates the unwrapped rebasing eETH as a separate instrument, so there is no
      base-eETH row to reclassify). (b) AAVE_V3-ETHEREUM (the only lending venue with a `venue_collateral.py` row)
      accepts **only the wrapped weETH**, never base eETH, as collateral — and since ezETH/rsETH/pufETH are already
      non-rebasing exchange-rate-accrual tokens by protocol design (same shape as wstETH, no wrapped variant exists),
      **no base/wrapped row split is needed for any of the 4 tokens** — weETH already existed as its own single row.
      Shipped: instrument_type LST→RESTAKING in the 4 IS adapters (renzo/kelpdao/puffer/etherfi.py, `instrument_key`
      strings deliberately left unchanged — values-only reclassification) + filter-guard extension +
      `_SINGLE_ASSET_DEFI_TYPES` quote_asset-validation gap found+fixed (would have silently rejected every future
      RESTAKING capture in the live orchestrator write-gate) — `unified-api-contracts@b11c3ad6` (SHIPPED, verified on
      origin). Catalogue re-stamp (`prod/catalog.parquet`, 5/5 target rows: ETHERFI-ETHEREUM:LST:WEETH,
      KELPDAO-ETHEREUM:LST:RSETH, PUFFER-ETHEREUM:LST:PUFETH, RENZO-{ARBITRUM,ETHEREUM}:LST:EZETH) **APPLIED AND
      VERIFIED** — 12,171 rows before/after (unchanged), 5 rows changed LST→RESTAKING, every other row byte-identical
      (full-frame equality check, not just the touched column). This bucket (`instruments-store-defi-prd-*`
      `prod/catalog.parquet`) is NOT `*/1`-cron-consolidated (rebuilt only by one-off scripts, last touched
      2026-07-22T01:01:40Z, ~13.5hr gap to the next-oldest backup) — safe to CAS-write directly, matching the task's own
      "small enough to safely write without production-writer contention" escape valve. IS-side availability_index
      re-stamp (`instruments-store-defi-*` `_index/availability_index.parquet`, 36 target rows at venue-day grain) is
      **script-ready + dry-run-verified, NOT applied** — this bucket IS one of the `*/1`
      `uts-prod-manifest-consolidator-instruments-defi-cron` targets (same high-frequency-consolidator-cron class the
      venue-as-chain fix hit), so per the mandatory-rules note this session did not pause the cron itself; needs an
      operator-authorized paused-writer window (mirrors this plan's own 2026-07-22 venue-as-chain precedent exactly).
      **instruments-service code ship (adapters + tests + both re-stamp scripts) is BLOCKED, not shipped**: a concurrent
      commit that landed on `live-defi-rollout` mid-session (`instruments-service@a9be6ce9`, unrelated "R2
      instrument_availability full-hive canonicalisation") introduced 4 new codex-compliance violations in files this
      session never touched (`tests/unit/test_smoke_matrix.py` hardcoded prod project ID,
      `engine/orchestrator/writers.py::_write_venue()` 211L > 200L limit) — confirmed pre-existing/not-mine: a full
      `quality-gates.sh` run at the PRIOR HEAD (`f33c2ec0`) was 100% green before this commit landed. quickmerge
      requires a fresh whole-tree-passing sentinel regardless of `--files` scope, so this blocks ANY commit to the repo
      right now, not just this one. Also fixed + ready to ship alongside (not part of the RESTAKING scope, but blocking
      the same shared gate): `tests/unit/scripts/goldens/expected_universe/sports.json` — stale after `uac@9908520b`'s
      ODDS_API bookmaker purge landed mid-session; regenerated via the documented
      `regenerate_expected_universe_golden.py` recipe with UAC/UTL both clean; verified the other 4 asset-group goldens
      (cefi/defi/tradfi/prediction) are content-identical (order-only diff, reverted to avoid unrelated noise). All 12
      files sit staged-ready in the instruments-service working tree; ship the moment `instruments-service@a9be6ce9`'s
      regression is fixed by its owner (or an operator authorizes bypassing it).

**`odds_horizon_bucket_{15m,1h,4h,1d}` re-stamp — operator ruling**: "Yes, go ahead" — implement the seed-aware
re-stamp/tombstone mechanism (bare `ODDS_HORIZON_BUCKET` + parsed `timeframe` column, row DELETE ruled unsafe per the
`_legacy_seed.parquet` re-supply risk, scope the predicate away from the deliberate 124,294-row
`mdps_odds_horizon_bucket` aggregate) and run it, verifying before/after like the venue-as-chain re-stamp.

- [x] [DATA] P1. Implement + run the `odds_horizon_bucket_{15m,1h,4h,1d}` → `odds_horizon_bucket` (bare canonical
      lowercase — corrected from the ruling text's uppercase, see 2026-07-22 tick below) + parsed `timeframe` seed-aware
      re-stamp — `market-tick-data-service/scripts/restamp_sports_odds_horizon_bucket_2026_07_22.py@2f3fb7cc`.
      Contention CONFIRMED (`uts-prod-manifest-consolidator-market-data-sports-cron`, same `*/1` class as
      venue-as-chain) — paused via `unified-trading-sa` impersonation, ran `--apply`, verified, resumed. Result:
      1,977,165 → 1,977,165 rows, 1,337 re-stamped (0 escalated), 0 post-write duplicate keys, 124,294-row aggregate +
      2,486-row seed population untouched (verified by count). Pre-apply snapshot:
      `gs://market-data-tick-sports-prd-central-element-323112/_index/backups/availability_index.pre_odds_horizon_bucket_restamp_apply_20260722T043109Z.parquet`.
      Old generation 1784694651727289 → new generation 1784694702854020. Cron resumed + verified ENABLED; downstream
      consolidator health independently verified (not just scheduler state) — one transient execution (`...-7bz4j`)
      failed on an unrelated `:latest` image-tag miss (self-healed, next execution `...-kvm49` succeeded in 57s against
      a pinned `@sha256` digest) — not a manifest-write or contention artifact.
- [x] ✅ [DATA] P2. Live-count `data_type=="futures_chain"` in the tradfi availability index to choose the remedy:
      zero-row non-issue / small legacy cohort (→ documented carve-out like `options_chain`'s T-OLD-2b) / active writer
      bug. Do NOT add it to `DATA_TYPES_BY_ASSET_GROUP['tradfi']` — `futures_chain` is an instrument_type; the data_type
      for those rows is `trades`. **RESOLVED — this todo was left unchecked despite being fully executed**: the
      2026-07-20 "LIVE row-count evidence" section (above) already measured 8 captured rows (100% captured, a small
      genuine legacy cohort, not zero-row and not an active writer bug), and the "2026-07-22 19:41 UTC — `futures_chain`
      tradfi remedy SHIPPED both legs" Progress Log entry (below) confirms the documented-carve-out remedy was
      implemented + shipped (`unified-api-contracts@27a84e44` + `deployment-api@d220b6f0`, both verified ancestors of
      `origin/live-defi-rollout`) — exactly the disposition this todo asked for. Flipping now to reflect
      already-completed work (found stale while investigating the adjacent D5/D6 item this session).
- [x] [OPERATOR] P1. **DeFi honest-coverage denominator exclusion — operator ruling received 2026-07-22 ("make it both
      Definition #2 and Definition #1 to be live for safety" / OR-semantics); first attempt BLOCKED by adversarial
      verify (false "months-long" claim); operator re-confirmed with the corrected, honest scope; PARTIALLY SHIPPED.**
      Of the 11 originally-investigated venues, adversarial verification found only 6
      (ANKR/STADER/STAKEWISE/SWELL/MANTLE/MAKER) have accuracy-verified data (independently re-derived on-chain at the
      exact historical block, exact match) — written by a manual/ad-hoc invocation, not the production cron, which
      crash-loops and targets the wrong date regardless. Shipped: `unified-api-contracts@91b6f094` —
      `DEFI_VENUE_MTDS_ADAPTER_VERIFIED_NOT_YET_SCHEDULED`, honestly worded (no "months-long", no "verified working"),
      inert/additive, `DEFI_VENUE_PHASE` untouched. The other 5 (FRAX/ALCHEMY/FLASHBOTS/ACROSS/STARGATE) each have a
      real, distinct, currently-open defect (dead migration artifact / crash-looping cron + venue mislabel /
      never-scheduled + missing schema contract) — deferred to a separate in-progress fix effort, not silently folded
      in. Full detail: `plans/active/issues/defi_venue_phase_live_definition_contradiction_2026_07_22.md` § "RESOLVED
      (partial) 2026-07-22, later same day".

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

The exhaustive Deferred-work table + the full dated Progress Log narrative from 2026-07-20 through 2026-07-22 (MTDS
venue-as-chain re-stamp saga, RESTAKING InstrumentType workstream, sports `odds_horizon_bucket` re-stamp,
`futures_chain` tradfi remedy, D2/D5/D6, `perp_daily_ctx` investigation) was split out **2026-07-24** into
`/plans/archive/2026_07/distinct_values_noncanonical_audit_history_2026_07_24.md` (size-cap split; every item in that
range was already fully resolved — `status: complete`, archive-bound, zero open todos). Read that doc for the full
historical record and evidence citations.

**Still genuinely open on THIS plan** (see `## Todos` above for the live checkboxes): the category-2 UAC SSOT additions
reconciliation, the category-1 owning-plan citation re-verification, and the MDPS `parts[1]` parse annotation (owned by
`sports_consolidated_closeout_2026_07_19.md`, not forked here).

**Forked out 2026-07-24** (not archived — still open, dispatchable work): the MTDS lending `instrument_type` historical
manifest re-stamp is now its own plan,
`/plans/active/market_tick_data_service_lending_instrument_type_historical_restamp_2026_07_24.md`.
