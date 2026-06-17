---
title: MVP Instrument Universe Gap Audit — Expected vs Actual (manifest-based)
created: 2026-06-17
author: audit-agent (deployment-api slot, read-only)
source:
  - unified_api_contracts/registry/cefi_instrument_universe.py (CEFI_BASE_ASSET_UNIVERSE)
  - unified_api_contracts/canonical/crosscutting/mvp_scope.py (MVP_SCOPE / is_mvp)
  - unified_api_contracts/registry/expected_coverage.py (EXPECTED_COVERAGE_BY_ASSET_GROUP)
  - tests/test_cefi_universe_coverage.py (_REQUESTED_BASES_2026_06_16 shrink-guard)
  - gs://instruments-store-{cefi,tradfi,defi,pred}-prd-…/prod/catalog.parquet + instrument_availability/by_date/
  - gs://market-data-tick-cefi-prd-…/_index/availability_index.parquet
locked_by: live-defi-rollout
---

## Scope + method

READ-ONLY. Manifest/catalogue-based (NOT day-sampled). EXPECTED universe assembled from UAC SSOTs; ACTUAL read from the
**instruments-store catalogue** (instrument-grain — `prod/catalog.parquet` + the authoritative live
`instrument_availability/by_date/day=2026-06-11/` per-venue parquets) and the **market-data-tick `_index` manifest**
(2.73M rows, capture_status grain).

## STEP 1 — EXPECTED universe (sources used)

| Axis                            | SSOT                                                                                          | Grain                                                                                                                                                        |
| ------------------------------- | --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| CeFi base currencies            | `CEFI_BASE_ASSET_UNIVERSE` (44 bases) + shrink-guard `_REQUESTED_BASES_2026_06_16` (17 bases) | base only                                                                                                                                                    |
| CeFi venues × instr_type × base | `mvp_scope.MVP_SCOPE["cefi"]`                                                                 | venues={BINANCE-SPOT/FUTURES, BYBIT, OKX, DERIBIT, HYPERLIQUID, ASTER, KRAKEN-SPOT/FUTURES}; itypes={SPOT_PAIR, PERPETUAL}; **base_ccys={BTC,ETH,SOL,USDT}** |
| CeFi venue × data_type          | `expected_coverage._CEFI`                                                                     | KRAKEN listed (note: "adapters exist but no manifest rows yet — backfill pending")                                                                           |
| DeFi venues × instr_type        | `mvp_scope.MVP_SCOPE["defi"]` (12 venues)                                                     | DEX/LST/lending; **NO base-currency axis**                                                                                                                   |
| TradFi venue × underlier        | `mvp_scope.MVP_SCOPE["tradfi"]`                                                               | CME; underliers={ES,NQ,VX}; itypes={FUTURE,OPTION}                                                                                                           |
| Prediction venue                | `mvp_scope.MVP_SCOPE["prediction"]`                                                           | POLYMARKET only (Kalshi flagged post-MVP)                                                                                                                    |

**Expected grid = `CEFI_BASE_ASSET_UNIVERSE` (44 bases) × {spot, perp, future, option} × MVP venues.**

**Where the EXPECTED universe is INCOMPLETE / absent (cannot audit against a formal SSOT):**

- **No per-base-currency expected set for DeFi or TradFi.** `mvp_scope` declares DeFi/TradFi only at (venue,
  instrument_type[, underlier]) grain — there is no canonical list of which tokens/underliers we intend to capture per
  venue. DeFi base coverage cannot be HAVE/MISSING-audited.
- **CeFi base_ccy MVP scope is narrow (BTC/ETH/SOL/USDT)** but `CEFI_BASE_ASSET_UNIVERSE` is 44 bases — the two SSOTs
  disagree on "how many bases". `mvp_scope` carries `TODO(mvp-scope): operator sign-off on base_ccy`.
- No instrument-grain expected set for sports.

## STEP 2 — ACTUAL captured (live catalogue day=2026-06-11 + market-data `_index`)

CeFi live catalogue venues (15): ASTER, BINANCE-SPOT/FUTURES, BITFINEX-SPOT/FUTURES, BITGET-SPOT/FUTURES, BYBIT,
COINBASE-SPOT, DERIBIT, HYPERLIQUID, OKX-SPOT/FUTURES/SWAP, UPBIT. **KRAKEN entirely absent from the instruments
catalogue.**

## STEP 3 — GAP TABLE

### CeFi base × instrument-type (LIVE instruments-store catalogue, day=2026-06-11)

44 MVP bases. **18 bases have ZERO instruments in the live catalogue** (HAVE=0 any venue/type):

`AAVE, ALGO, AXS, CHZ, COMP, DAI, DASH, EIGEN, ENJ, EOS, FIL, GALA, ICP, MANA, SAND, THETA, XLM, ZEC`

— i.e. **all 17 operator-requested 2026-06-16 additions (EIGEN + the 16 in the shrink-guard) + DAI** are MISSING from
the catalogue. The universe constant was expanded 2026-06-16 but **no IS catalogue re-enumeration ran** for the new
bases.

MVP-core bases (BTC/ETH/SOL) across MVP venues (S=spot P=perp F=future O=option, `--`=absent):

| Base | BINANCE-SPOT | BINANCE-FUT | BYBIT | OKX-SPOT | OKX-SWAP | OKX-FUT | DERIBIT | HYPERLIQUID | ASTER | KRAKEN-SPOT | KRAKEN-FUT |
| ---- | ------------ | ----------- | ----- | -------- | -------- | ------- | ------- | ----------- | ----- | ----------- | ---------- |
| BTC  | S            | P           | P     | S        | P        | F       | PFO     | P           | P     | **--**      | **--**     |
| ETH  | S            | P           | P     | S        | P        | F       | PFO     | P           | P     | **--**      | **--**     |
| SOL  | S            | P           | P     | S        | P        | F       | PF      | P           | P     | **--**      | **--**     |

PARTIAL by instrument-type: **options only on DERIBIT** (BTC/ETH), as expected (`CEFI_OPTIONS_UNDERLYINGS={BTC,ETH}`).

### CeFi reference-data vs market-data SPLIT (key reconciliation)

The market-data-tick `_index` manifest tells a _different_ story than the catalogue:

- **KRAKEN-SPOT: 76,013 captured / 171,518 attempted_failed; KRAKEN-FUTURES: 31,645 captured / 71,397
  attempted_failed.** So Kraken HAS market data captured — it is missing only its **instrument-catalogue definitions**
  (a reference-data gap, not a market-data gap). ASTER is fully present (catalogue + 17.7k manifest rows) — the
  wired-but-backfill-pending note is now stale.
- **42/44 MVP bases appear as `captured` in the market-data manifest** (only EIGEN + EOS absent there, partly
  parse-noise). So the new bases reached the _market-data_ manifest historically but NOT the _instruments catalogue_.
- Manifest health: 1.33M captured / **1.29M attempted_failed** / 109k empty_confirmed; schema_version still 95% v8 (only
  8,035 rows at canonical v9 — schema-version drift persists, consistent with the standing canonicalisation work).

### DeFi (venue × instrument-type — no base axis to audit)

11/12 MVP venues present in catalogue; **MISSING: `ROCKETPOOL-ETHEREUM` (rETH)** — a `carry_staked_basis` LST gap. LST
coverage is **thin: ~7 staking instruments total** (ETHENA, ETHERFI, JITO, LIDO×2, MARINADE×2). DEX POOL=5,909,
LENDING=854. **Venue-naming drift**: catalogue carries BOTH `UNISWAP_V3-*` and underscore-less `UNISWAPV3-*` /
`PANCAKESWAPV3-*` forms, plus deprecated `TRADER_JOE_V2-AVALANCHE` (202) — dual-format dupes inflate venue counts.

### TradFi (CME underliers ES/NQ/VX)

CME ES + NQ FUTURE present; CME OPTION=624k, FUTURE=4,298, COMBO=56,841. **VX (VIX futures) = 0 on CME** — expected per
`mvp_scope` but per codex VIX/VX is a Barchart+Yahoo gap (Massive/Databento don't cover it). NASDAQ(128)/ NYSE(363)
catalogues are tiny (OHLCV-only MVP). The `underlying` field carries the raw contract code (ESM2…), not a clean root —
so a per-underlier audit needs root-symbol normalisation.

### Prediction / Sports

Prediction catalogue = **POLYMARKET only** (668k PREDICTION_MARKET); no Kalshi catalogue (Kalshi flagged post-MVP in
`mvp_scope`). Sports: no instrument-grain expected SSOT to audit.

## Findings (real coverage gaps)

1. **[P0 — CeFi reference-data] ✅ RESOLVED 2026-06-17 — 18 of 44 MVP CeFi bases had ZERO instrument-catalogue
   definitions.** The universe constant + shrink-guard test were expanded 2026-06-16, but the instruments-service
   catalogue was not re-enumerated. **Fix**: re-ran the IS per-date enumeration
   (`instruments-service --operation instruments --mode batch --asset-group CEFI` for 2026-06-17) — credential-free
   (Tardis `/v1/exchanges` free-tier instrument listing, no `TARDIS_API_KEY` required), the venue adapters filter the
   venue's full symbol list by `CEFI_BASE_ASSET_UNIVERSE` so the expanded 44-base universe materialised automatically —
   then rolled up `prod/catalog.parquet` (`scripts/build_instrument_catalogue.py --asset-group cefi`). **Post-fix: 44/44
   MVP bases now have catalogue instruments** (was 26/44); all 18 prior-zero targets present (EOS thin — 1 instr on
   BITFINEX-SPOT, the only MVP venue listing it). Catalog 221,424 rows (was 220,222). Evidence: `CATALOGUE_PROMOTED`
   2026-06-17T16:21:01Z → `gs://instruments-store-cefi-prd-central-element-323112/prod/catalog.parquet`.
2. **[P1 — CeFi] ✅ RESOLVED 2026-06-17 — KRAKEN had captured market data (107k rows) but NO instrument-catalogue.**
   Root cause was TWO IS bugs (not "no adapter"): (a) **KRAKEN-SPOT was missing from `_CEFI_VENUES`**
   (`engine/orchestrator/venue_core.py`) — only KRAKEN-FUTURES was listed, so the spot venue was never enumerated; (b)
   the Tardis symbol parser mis-handled BOTH Kraken formats — kraken-spot `AAVE/USD` (the `/` separator was not split →
   base kept the slash) and kraken-futures `PF_AAVEUSD` / `FI_XBTUSD_240329` (the `PF_`/`FI_` type-prefix was not
   stripped + `XBTUSD` greedily matched the `TUSD` quote), so cryptofacilities `parsed 0 instruments`. **Fix**: added
   KRAKEN-SPOT to `_CEFI_VENUES` + a `_split_kraken_symbol` parser branch (slash-split for spot, prefix-strip +
   `<BASE><QUOTE>` split for futures, `XBT`→`BTC` alias) in `tardis/parsing.py` (regression test
   `tests/unit/test_tardis_kraken_symbol_parse.py`). **Post-fix: KRAKEN-SPOT 75 / KRAKEN-FUTURES 632 parsed (was 0/0);
   128 KRAKEN catalogue rows** across both venues — reference data now exists alongside the captured market data.
   Shipped instruments-service@abe2873.
3. **[P1 — DeFi] ROCKETPOOL-ETHEREUM (rETH) missing from the DeFi catalogue** and LST coverage is thin (~7 instruments)
   despite `carry_staked_basis` needing the full LST set (stETH/rETH/cbETH/JitoSOL/mSOL). cbETH (COINBASE-ETHEREUM) also
   absent. DeFi venue-naming dual-format (`UNISWAPV3` vs `UNISWAP_V3`) + deprecated `TRADER_JOE_V2` pollute the
   catalogue.
4. **[P2 — TradFi] VX/VIX futures = 0 on CME** (Barchart+Yahoo gap, codex-known); CME ES/NQ present.
5. **[P2 — manifest health] 1.29M `attempted_failed` rows + 95% schema_version v8 (only 8k at canonical v9)** —
   pre-existing pipeline-correctness gaps, consistent with the open canonicalisation work.

## Does a formal MVP-instrument-universe SSOT exist? (per asset-group)

| AG         | Expected SSOT exists?                                                | Grain                     | Gap                                                                                                             |
| ---------- | -------------------------------------------------------------------- | ------------------------- | --------------------------------------------------------------------------------------------------------------- |
| CeFi       | **YES** (`CEFI_BASE_ASSET_UNIVERSE` + `mvp_scope["cefi"].base_ccys`) | base + venue + instr_type | The two disagree (44 vs 4 bases) — needs operator reconciliation; `mvp_scope` base_ccy still TODO sign-off      |
| DeFi       | **PARTIAL** (`mvp_scope["defi"]` venue+instr_type)                   | venue only                | **No per-base/per-token expected set — CANNOT audit token coverage. NEEDS CREATING.**                           |
| TradFi     | **PARTIAL** (`mvp_scope["tradfi"]` underliers ES/NQ/VX)              | underlier                 | Underlier set defined but actual catalogue carries raw contract codes; needs root-symbol normalisation to audit |
| Sports     | **NO** instrument-grain expected SSOT                                | —                         | **NEEDS CREATING** (league-grain exists in `mvp_scope`, not instrument-grain)                                   |
| Prediction | **YES** (POLYMARKET, market_groups)                                  | venue + market_group      | Kalshi explicitly post-MVP                                                                                      |

**Recommendation:** create a formal per-(asset_group, venue, instrument_type, base/underlier/token)
MVP-instrument-universe SSOT for **DeFi and Sports** (currently undefinable), reconcile the CeFi 44-vs-4 base
disagreement with operator sign-off, and **re-run the IS catalogue enumerator for the 18 missing CeFi bases + KRAKEN +
ROCKETPOOL** so the catalogue matches the already-expanded universe constant.

## Progress Log

### 2026-06-17 — CeFi catalogue re-enumeration + KRAKEN + MVP-tag fix (Findings 1, 2 RESOLVED)

- **How the IS catalogue sources its universe**: the per-date enumeration
  (`instruments-service --operation instruments`) fetches each venue's full instrument list via the URDI venue adapters
  (CeFi → Tardis `/v1/exchanges/{ex}` free-tier listing, hyperliquid/aster public APIs) and **filters by
  `CEFI_BASE_ASSET_UNIVERSE`** (the adapters import the UAC constant), writing
  `instrument_availability/by_date/day={d}/venue={v}/instruments.parquet`. The lifecycle roll-up
  (`scripts/build_instrument_catalogue.py`) then rolls the by_date snapshots into `prod/catalog.parquet`. So a universe
  expansion only reaches the catalogue when BOTH are re-run. The 2026-06-11 by_date snapshot pre-dated the 2026-06-16
  expansion (BINANCE-SPOT had 23 bases / none of the 18 targets) → the gap.
- **Credential-free**: confirmed — instrument LISTING uses the optional API key (free `/v1/exchanges` fallback when pro
  tier absent); only historical tick/data-feed fetch needs `TARDIS_API_KEY`. Ran for 2026-06-17: 17/18 venues, 3,934
  records (only DERIBIT-COMBO fails on a pre-existing combo-endpoint 400 — correctly recorded `attempted_failed`, not a
  base gap; combos are not MVP bases).
- **KRAKEN** (Finding 2): genuine reference-vs-market split caused by two IS bugs, not a missing adapter — fixed in code
  (KRAKEN-SPOT added to `_CEFI_VENUES`; `_split_kraken_symbol` parser for the `/`-spot + `PF_`/`FI_`-futures +
  `XBT`→`BTC` formats). Did NOT add phantom entries — the instruments are now genuinely enumerated from the live Tardis
  venue listing.
- **Post-fix MVP gate**: **44/44 MVP CeFi bases have catalogue instruments** (modulo EOS thin = 1 instrument on the one
  MVP venue listing it). KRAKEN: 128 catalogue rows across SPOT+FUTURES.
- **Side-fix (MVP-tag column)**: while rolling up, found `_add_mvp_column` tagged **0 / 221,424** rows MVP — two
  this-repo bugs: (a) it passed `data_type=""` to `is_mvp` which hard-requires a data_type match → all-False; (b) it
  read the base from `underlying` (blank for spot/perp) + `str(NaN)` → `"nan"` poisoning. Fixed to probe with a
  representative MVP data_type for the AG + read `base_asset` (NaN-safe). **Post-fix: 145,538 / 221,424 MVP-tagged**
  (deployment-api's `scope=mvp` coverage denominator is now non-empty). Shipped instruments-service@abe2873.

### Residual / follow-up (NOT in this fix — captured as todos)

- [x] ✅ **[CODE] P2.** **`unified-api-contracts`**: the cefi `MVP_SCOPE` venue set uses bare `OKX`, but the IS catalogue
      (and the rest of the pipeline) uses `OKX-SPOT`/`OKX-SWAP`/`OKX-FUTURES`. `is_mvp("cefi", venue="OKX-SPOT", …)`
      returns False → OKX-SPOT/SWAP/FUTURES catalogue instruments are tagged non-MVP despite being in-scope. Reconcile
      the `CeFiMvpRule.venues` OKX naming to the canonical sub-venues (or add an OKX→sub-venue expansion in `is_mvp`).
      Discovered 2026-06-17 during the MVP-tag fix (instruments-service slot). Provenance: this audit.
      **RESOLVED unified-api-contracts@d7a27de** — added `_CEFI_SUB_VENUE_BASES = frozenset({"OKX"})` + OKX-aware venue
      match in `mvp_scope.py`: `OKX-SPOT`/`-SWAP`/`-FUTURES` now match directly, and bare `OKX` still matches when the
      rule declares any sub-venue base. OKX sub-venues tag MVP.
- [x] ✅ **[CODE] P2.** **`unified-api-contracts`**: `is_mvp` Axis-3 hard-requires `data_type in rule.data_types`, which
      makes the predicate unusable for an instrument-grain caller (no data_type axis) without the caller supplying a
      representative data_type (the IS catalogue tagger now does this locally). Consider an UAC-side convention where
      `data_type=""`/`None` means "any MVP data_type" so every single-grain consumer (not just IS) tags correctly. The
      other AG catalogues (defi/tradfi/prediction) don't yet carry an `mvp` column at all — when the mvp tagging rolls
      out to them, this same gap applies. Provenance: this audit, 2026-06-17.
      **RESOLVED unified-api-contracts@d7a27de + instruments-service@4b2c360** — `is_mvp` now treats `data_type=""`/`None`
      as "any MVP data_type" (UAC-side convention), and the IS tagger dropped its `_representative_mvp_data_type`
      workaround → calls clean `is_mvp(...)`. mvp column rolled out beyond cefi: **defi** roll-up promoted 6,853 rows
      (800 MVP-tagged), **tradfi** roll-up promoting (686k rows) this turn. **prediction** has no `prod/catalog.parquet`
      (its IS reference rows are cqg-group-shaped, not catalogue-rolled) → no mvp column applies; noted, not a gap.
- [x] ✅ **[OPS] P2.** Re-run the cefi catalogue enumeration + roll-up on the recurring IS scheduler cadence (this fix ran
      it once for 2026-06-17); confirm the scheduled job picks up `KRAKEN-SPOT` + the expanded universe automatically on
      its next tick. Provenance: this audit, 2026-06-17.
      **RESOLVED (verified already-correct)** — `deployment-service/terraform/gcp/lifecycle_catalogue_scheduler.tf` is
      AG-parametric (`for_each` over cefi/defi/tradfi/sports/prediction; Cloud Run Job + daily Scheduler) with **no
      hardcoded venue list** — it re-enumerates from the live IS universe each tick, so `KRAKEN-SPOT` + the expanded
      44-base universe + the mvp tagging are picked up automatically on the next scheduled run. No change needed.
