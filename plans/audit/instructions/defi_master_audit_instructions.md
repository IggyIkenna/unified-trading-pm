---
name: defi_master_audit_instructions
type: audit-instructions
epic: defi_master
assigned_vm: vm-defi
tier: L0
last_updated: 2026-06-01
codex_ssots_to_check_drift_against:
  - codex/02-data/defi-data-types-catalog.md
  - codex/02-data/defi-data-pipeline.md
  - codex/02-data/data-lineage-MTDS-features-ml.md
  - codex/02-data/availability-manifest-and-data-status.md
  - codex/02-data/data-status-drilldown.md
  - codex/02-data/venue-availability.md
  - codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md
  - codex/09-strategy/architecture-v2/archetypes/carry-basis-perp.md
  - codex/09-strategy/architecture-v2/archetypes/carry-basis-dated.md
  - codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md
---

# DeFi Master — Audit Instructions

> **🔄 ALIGNED 2026-06-08 — pre-apply readiness audit + source-aware/Era-B model (SSOT wins where this differs).**
> Data-form SSOT = `canonical_form_cross_service_audit_checklist.md` (**CF-1…CF-14**, incl. **CF-13** source-aware
> `pipeline_mode={mode}_{source}[_{transport}]` + **CF-14** IS-catalogue could-exist root) + the **①–⑫ pre-apply
> readiness audit** in `plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md` (esp. ⑪
> **batch=live / no-regression**; ⑧ catalogue completeness; ⑨ source-aware pipeline_mode; ⑫ rollback snapshot). Any text
> below assuming coarse `pipeline_mode=batch` or a non-source-aware manifest is STALE — audit against the SSOT.

## Epic Scope

DeFi adapters, on-chain execution, Copper custody path, and the DeFi MVP archetypes. Two audit dimensions share this
doc:

| Dimension                                                              | What it checks                                                                                                                                                                              | Section                                                                                                 |
| ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| **Code ↔ codex correctness**                                           | Adapter parity, error codes, RPC templates, data_type/venue naming SSOT, code↔codex drift                                                                                                   | [Checklist](#checklist) items (a)–(n)                                                                   |
| **Strategy data-coverage** (the operator's data-availability question) | _For each MVP strategy_: honest coverage per data_type × venue/chain (CeFi perp venues **in totality**), over the required history — what's present, what's missing, what needs downloading | [Strategy Data-Coverage Audit](#strategy-data-coverage-audit-data-availability-dimension) items (o)–(z) |

### Archetypes / strategies in scope (operator's words → codebase archetype)

The operator audits these as **"funding rate arb, staked basis carry, basis carry"** plus the price-dispersion MVP. The
canonical archetype files live under `codex/09-strategy/architecture-v2/archetypes/`:

| Operator's name        | Canonical archetype                                          | Archetype file                  | Strategy-engine file                                               |
| ---------------------- | ------------------------------------------------------------ | ------------------------------- | ------------------------------------------------------------------ |
| **staked basis carry** | `carry_staked_basis`                                         | `carry-staked-basis.md`         | `strategy-service/.../v2/carry_and_yield/staked_basis.py`          |
| **funding rate arb**   | `carry_basis_perp` (incl. `funding_rate_dispersion` variant) | `carry-basis-perp.md`           | `.../carry_and_yield/basis_perp.py` + `funding_rate_dispersion.py` |
| **basis carry**        | `carry_basis_dated`                                          | `carry-basis-dated.md`          | `.../carry_and_yield/basis_dated.py`                               |
| (price-dispersion MVP) | `arbitrage_price_dispersion`                                 | `arbitrage-price-dispersion.md` | (DEX/CEX cross-venue dispersion)                                   |

Inverse / dated variants also exist (`carry-basis-perp-inv.md`, `carry-basis-dated-inv.md`,
`carry-staked-basis-dated.md`) — audit them only when a slot uses them. **DeFi+CeFi hybrid (CRITICAL)**: DeFi = the
long/stake/lend leg (on-chain); the hedge/short leg runs on CeFi perp venues. So a "DeFi" strategy's data coverage spans
BOTH `asset_group=defi` (LST rates, lending indices, DEX, oracle) AND `asset_group=cefi` (perp funding, perp marks) —
the coverage audit MUST cover both legs or it is incomplete.

**Active MVP critical path — Solana basis trade (2026-06-01)**: the concrete first-live target is
[`plans/active/solana_basis_trading_mvp_2026_06_01.md`](../../active/solana_basis_trading_mvp_2026_06_01.md)
(`parent_epic: mtds_mdps_master`) — **long SOL spot on Orca (Whirlpool SOL/USDC, primary) / Raydium + short SOL-PERP on
Drift V2 = funding carry**. It re-scopes the Solana data sources after the Bug-D Drift-backfill saga
(`issues/bug_d_prime_drift_backfill_2026_05_31.md`). Audit implications this doc MUST honour:

- **Drift V2 funding/trades come from the Velocity Data API** (`data.api.drift.trade/market/SOL-PERP/...`), free tier,
  full history verified — NOT from Helius signature-walking (explicitly out of MVP scope). When auditing `perp_funding`
  coverage for Solana, the source of truth is this API + the `perp-funding-*` bucket, not the `market-data-tick-defi`
  grid.
- **New canonical data_types the plan introduces** (audit their bucket + manifest presence once landed): `perp_trades`,
  `perp_mark_oracle`, `perp_open_interest`, `dex_pool_state` (time-series, distinct from snapshot `dex_pools`),
  `dex_trades`, `dex_spot_price`. The existing `solana_defi_handler.py` routes Orca→`dex_pools/orca/SOLANA/`,
  Raydium→`dex_pools/raydium/SOLANA/` (snapshots) — the MVP needs the per-swap/time-series extension.
- **Solana chain coverage is the live gate** — in the per-chain breakdown (item v), `SOLANA` rows for `perp_funding`
  (Drift), `dex_pool_state`/`dex_trades` (Orca/Raydium), and `oracle_prices` (Pyth) are the cells that actually block
  go-live; weight them accordingly.

Key code surfaces:

- LST APR adapters: Lido (stETH), RocketPool (rETH), Coinbase (cbETH), Solana JitoSOL, mSOL
- On-chain rate readers: Aave v3 / Compound v3 base rates
- DEX price feed adapters: Uniswap V3, Curve, Balancer, Sushi, PancakeSwap, Phoenix, Orca, Raydium, Drift
- On-chain execution: `UniswapConnector.swap_exact_input()` via SwapRouter02
- Flash loan: `deployment-service/contracts/FlashLoanReceiver.sol`
- Custody: `CLOUD_KMS_ENCRYPTED` path (May-23); Copper post-June-1
- Pyth oracle: Solana-only on-chain price feeds
- Chain RPC: `CHAIN_RPC_TEMPLATES` in UAC `registry/capability_declarations/_defi.py`
- Error classification: 35 `DefiErrorCode` values in UAC (13 Aave-family + 7 `RECURSIVE_*` + 8 `HL_*` + 2 `ORACLE_*` + 5
  `CCTP_*`; **count the enum, do not trust this number**)

## Triggers

- Weekly (minimum cadence)
- After any DeFi protocol version bump (Aave v4, Uniswap v4, etc.)
- After any new chain or LST is added to the universe
- When `manifest_master` audit surfaces new `empty_confirmed` rows for `asset_group=defi`
- When `batch_live_symmetry_master` audit surfaces adapter parity gaps for DeFi adapters
- **Before any DeFi archetype goes to paper/live** — run the
  [Strategy Data-Coverage Audit](#strategy-data-coverage-audit-data-availability-dimension) first; a strategy cannot
  paper-trade on a data_type that isn't backfilled over its required history
- After any manifest schema bump (the corpus must be re-checked against the new version per-data_type — code constant ≠
  data state; see incident: 0% of 7.4M rows at v8 despite the constant, 2026-05-20)

## Checklist

- [ ] (a) **35 DefiErrorCode coverage**: all 35 codes (13 Aave-family + 7 `RECURSIVE_*` + 8 `HL_*` + 2 `ORACLE_*` + 5
      `CCTP_*`; **count the enum, don't trust this number** — it grows) present in UAC
      `unified_api_contracts.canonical.crosscutting.errors.defi.DefiErrorCode`. Count members:
      `awk '/class DefiErrorCode/{f=1;next} f&&/^class /{exit} f&&/^    [A-Z_]+ =/{c++} END{print c}' unified-api-contracts/unified_api_contracts/canonical/crosscutting/errors/defi.py`

- [ ] (b) **CHAIN_RPC_TEMPLATES coverage**: every supported chain has an entry. Read:
      `unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py`

- [ ] (c) **TestnetContractRegistry**: validates `config/testnet_contracts.yaml` at load (no missing keys). Run:
      `cd execution-service && python -c "from unified_trading_library.config_interface.testnet_contracts import TestnetContractRegistry; TestnetContractRegistry()"`

- [ ] (d) **Batch + live adapter parity**: every LST APR adapter and DEX price adapter has both batch and live modes.
      Check: `a6_batch_live_adapter_parity.py` output for asset_group=defi rows

- [ ] (e) **FlashLoanReceiver.sol matches codex**: architecture description in
      `codex/04-architecture/flash-loan-receiver.md` matches the actual contract. Grep:
      `rg "FlashLoanReceiver" deployment-service/contracts/`

- [ ] (f) **No hardcoded RPC URLs**: QG `no_hardcoded_venue_urls.sh` passes for all DeFi service dirs. Run:
      `bash scripts/quality-gates/no_hardcoded_venue_urls.sh` in each affected service

- [ ] (g) **Archetype manifest rows**: `carry_staked_basis` and `arbitrage_price_dispersion` archetypes produce manifest
      rows with correct `schema_version`, `asset_group=defi`, and non-null `available_at`. Check: manifest divergence A3
      shows zero `MISSING_EXPECTED` for defi + these data_types

- [ ] (h) **No removed providers**: no imports/URLs of Elysium, Arkham, Bloxroute, or Infura anywhere. Grep MUST include
      `market-tick-data-service/` and `unified-trading-pm/codex/` (the prior scope omitted MTDS — that is how a live
      `bloxroute` relay URL survived in `mev_events_handler.py`, found 2026-05-27). Grep:
      `rg "elysium|arkham|bloxroute|infura" --ignore-case -g '!*.venv*' unified-api-contracts/ execution-service/ market-tick-data-service/ unified-trading-pm/codex/`
      (Allowed false-positive: the **client** "Elysium Capital" in `client_registry.py` is a customer name, not the MEV
      provider — distinguish before flagging.)

- [ ] (i) **Pyth oracle scope**: Pyth used for Solana on-chain only; other chains use Chainlink. Read:
      `codex/04-architecture/defi-execution-overview.md` and verify code matches

### Code ↔ Codex drift (added 2026-05-27)

Verify the data-pipeline codex SSOTs (`codex/02-data/defi-*.md`, `data-lineage-MTDS-features-ml.md`) match code. Method:
grep code truth, compare to the doc, classify each as `aligned` / `codex-stale` / `code-bug`. Reference run + format:
[`defi-data-pipeline.md`](../../../codex/02-data/defi-data-pipeline.md) §1 drift register.

- [ ] (j) **data_type names**: handler constants `_*_DATA_TYPE` in MTDS `cli/handlers/*.py` match the `data_type=` names
      documented in `codex/02-data/defi-data-types-catalog.md`. Canonical = `dex_swaps` / `dex_pool_state` /
      `lending_indices` / `perp_funding` / `lst_rates` / `vault_share_price` (NOT `swap_events` / `pool_state` /
      `lending_metrics` / `funding_rates`). Grep: `rg "_DATA_TYPE\s*=" market-tick-data-service/*/cli/handlers/`
- [ ] (k) **data_type completeness**: every `collect-*` DeFi operation in MTDS `cli/main.py` is documented in the
      catalog. Any operation not in the catalog = `codex-stale`. (2026-05-27: code emits ~22, catalog had 14.)
- [ ] (l) **storage bucket per data_type**: each handler's `get_write_bucket_name(kind)` / `resolve_bucket_name(kind=)`
      matches the bucket the codex claims — dedicated `lst-rates-*` / `lending-indices-*` / `dex-pools-*` /
      `oracle-prices-*` / `perp-funding-*`, vs `market-data-tick-defi-*` for `dex_swaps` / `vault_share_price` /
      `dex_pool_state`. No live writes to legacy in-bucket prefixes (`market-data-tick-defi-*/lst_rates/` etc.).
- [ ] (m) **MDPS processed-vs-bypass scope**: the DeFi adapters imported in MDPS `app/adapters/__init__.py` + UAC
      `needs_candle_processing()` agree with the bypass list in `data-lineage-MTDS-features-ml.md`. Flag any adapter
      registered-by-decorator but **not imported** in the top-level `__init__.py` (dead — e.g.
      `DefiLendingIndicesAdapter` 2026-05-27), and any `needs_candle_processing=True` for a bypass type.
- [ ] (n) **venue/capability consistency**: every venue in `registry/defi_venues.py` (`ALL_DEFI_VENUES`,
      `DEFI_VENUE_PHASE=live`) has a matching `PROTOCOL_CAPABILITIES` + `SUBGRAPH_IDS` entry — no live venue without
      capability backing (e.g. RADIANT 2026-05-27) — and `defi-venue-protocol-catalogue.md` lists the same venues, with
      `EMPTY_OR_DEPRECATED_DEFI_VENUES` flagged.

### Dual-source provenance (the `source` column + SOURCE_PRIORITY)

> Codified 2026-06-01 (crosscutting plan: `plans/active/data_source_provenance_all_asset_groups_2026_06_01.md`). **DeFi
> is the workspace's strongest multi-source case** — the same metric routinely comes from several providers, and
> `SOURCE_PRIORITY` already declares multi-source lists: `("defi","oracle_prices")=["pyth_hermes","chainlink"]`,
> `("defi","native_staking_rates")=["solana_rpc","helius_rpc"]`, plus APR/rate metrics available from DefiLlama vs
> protocol subgraph vs direct on-chain read. Design (operator-confirmed 2026-06-01): same hive drop, disambiguated by a
> **row-level `source` column** (NOT a path key), resolved downstream via `select_primary_available_source()`.
> **Provenance is UNIVERSAL** (operator 2026-06-01): every DeFi cell stamps its `source` (`onchain_subgraph` etc.) — not
> just the 2 multi-source cells — for swap-resilience. The multi-source cells (`oracle_prices`, `native_staking_rates`)
> _additionally_ need resolution.
>
> **Current state (audit 2026-06-01, RED): DeFi writes `source=""` with no gate and no read-time reconciliation.**
> `DefiManifestRecorder.record_captured()` routes through the legacy `ManifestWriter.add()` path, which has no `source`
> parameter — so the column is blank everywhere, and the two multi-source providers for one `(protocol/feed, day)`
> **collapse last-write-wins**, silently dropping the divergent value. All items below are data-state verifiable.

- [ ] (n1) **DeFi writers carry `source` on EVERY cell**: `DefiManifestRecorder.record_captured()` accepts + forwards
      `source` via `ManifestWriter.record_captured()` (not the legacy `add()`); every DeFi handler passes `source` from
      the `SOURCE_PRIORITY` closed set. `market-tick-data-service/.../cli/handlers/_defi_manifest.py` + every
      `*_handler.py`. Read ACTUAL prod rows — **RED on any blank `source`** (all defi cells, not only multi-source
      ones).
- [ ] (n2) **Per-row source on multi-provider handlers**: oracle (`pyth_hermes`/`chainlink`) and native-staking
      (`solana_rpc`/`helius_rpc`) handlers already resolve per-row `pipeline_mode` at the callsite — stamp the matching
      `source` on each row in the same place. APR/rate handlers stamp the actual provider used (`defillama` vs
      `onchain_subgraph` vs `solana_rpc`).
- [ ] (n3) **`source` is a column, not a path key**: no `source=`/`data_source=` hive segment in DeFi GCS paths — all
      providers co-mingle on the dedicated-bucket layout; disambiguate by the column.
- [ ] (n4) **Read-time reconciliation wired**: 2-source fixture (e.g. Pyth + Chainlink for the same feed+ts, or
      DefiLlama + on-chain APR for the same protocol+day) → consumer emits exactly ONE resolved row via
      `select_primary_available_source()`; divergence surfaced via `detect_dual_source_conflicts()`
      (`VALUE_DIVERGENCE`/`DUAL_SOURCE_DUPLICATE`), never silent last-write-wins. Cover features-onchain consumers.

## Strategy Data-Coverage Audit (data-availability dimension)

> **This is the operator's standing question** ("fresh look at funding rate arb, staked basis carry, basis carry — audit
> instruments-service, MTDS, MDPS, features data available for those strategies and over what timeframe; what's missing,
> what needs downloading"). The items above (a–n) check that the _code_ is correct. The items below check that the
> _corpus_ is actually present for each strategy to run. **Both must be GREEN before an archetype papers/lives.**
>
> Method per cell: do NOT trust code constants or catalog docs — **read the actual manifest / data-status rows**
> (`asset_group`, `venue`, `data_type`, `schema_version`, min/max `available_at`). Composes with the
> `Data Pipeline Correctness Is The Heartbeat` HARD RULE: every cell is either `captured` over the full required window,
> or `empty_confirmed` with a typed reason, or a **download backlog item** — never a silent gap. No asset_group, no
> venue, no time-range is skipped to hit a date.

### Three integrity layers — audit each SEPARATELY (codified 2026-06-01)

The operator's framing: coverage is not one number — it is **three distinct things** that must each be checked, end to
end across the pipeline **instruments-service → MTDS → MDPS → features-service** for on-chain / DeFi / perp. Do not
collapse them; a layer can be green while the one beneath it is broken.

| Layer                                    | Question                                                                                                                                      | What a finding looks like                                                                                                                                                                                                                 | Items               |
| ---------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------- |
| **L1 — Manifest integrity** (deepest)    | Are ALL the scattered data_types + schemas + buckets recorded **correctly and completely INTO** the manifest?                                 | An actual GCS parquet object with no manifest row (orphan); a manifest row with no object (phantom); a data_type/venue/chain/schema field mis-recorded; a dedicated bucket whose index never reaches the canonical manifest the API reads | (x) + items (r)/(s) |
| **L2 — API faithfulness**                | Does the **data-status API query** honestly reflect the manifest — right numerator, IS∩UAC denominator, per-venue/chain breakdown?            | API coverage % ≠ a direct manifest aggregation; self-referential denominator; missing scope gate; no per-chain split                                                                                                                      | (w)                 |
| **L3 — Pipeline coverage IS→…→features** | Is honest coverage **propagated up the chain** — IS universe → MTDS raw → MDPS processed → features-service derived — for defi/perp/on-chain? | A cell `captured` at MTDS (`lst_rates`/`perp_funding`) but the derived feature (`staking_apy_bps`/`funding_rate_apy_bps`/`basis_bps`) is absent in `features-onchain-defi-*` / `features-delta-one-*` over the same window                | (o) + (u) + (y)     |

The per-strategy matrix (Step 1) + items (o)–(z) below are the concrete checks; (x)/(y) are the L1/L3 integrity checks
added for this framing. **The result MUST report all three layers separately** — "the API says 90%" is not an answer to
"is the manifest complete?" nor to "did it reach features?".

### Step 1 — Build the per-strategy data-dependency matrix (the expected set)

For each in-scope archetype, derive the cells it consumes from its archetype file + strategy-engine `Features expected`
list. The matrix is `strategy → data_type → venue(s) → asset_group → producing service → feature → required history`.
This is the **expected coverage** baseline (regenerate from code/codex each run; the snapshot below is the 2026-06-01
reference, not a substitute for reading the source):

**staked basis carry (`carry_staked_basis`)** — DeFi long/stake leg + CeFi hedge leg:

| data_type         | venue(s)                                                                                                                                                | asset_group     | producing service         | feature consumed                                                  | required history                                                                                      |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- | ------------------------- | ----------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `lst_rates`       | LIDO/stETH, ROCKETPOOL/rETH, ETHERFI/weETH, COINBASE/cbETH, JITO/jitoSOL, MARINADE/mSOL (+ ANKR/STADER/SWELL/PUFFER/MANTLE/STAKEWISE as universe grows) | defi            | MTDS → features-onchain   | `staking_apy_bps`, `lst_native_rate`, `lst_native_rate_ts`        | ≥ enough daily snapshots to compute rate-diff APY (≥30d for a stable APY; ≥1y preferred for backtest) |
| `perp_funding`    | DRIFT, HYPERLIQUID, GMX (DeFi perps); DERIBIT, BYBIT, BINANCE, OKX (CeFi hedge)                                                                         | defi + **cefi** | MTDS → features-delta-one | `funding_rate_apy_bps`                                            | full funding-cycle history over backtest window (4–8h cadence)                                        |
| `oracle_prices`   | Chainlink (ETHEREUM/ARBITRUM/BASE/OPTIMISM/POLYGON), Pyth (Solana)                                                                                      | defi            | MTDS → features-onchain   | spot price, health-factor inputs                                  | continuous over window                                                                                |
| `lending_indices` | AAVE_V3, SPARK, COMPOUND_V3                                                                                                                             | defi            | MTDS → features-onchain   | `usdc_idle_yield_apy_bps` (optional; defaults 0), `health_factor` | window length                                                                                         |

**funding rate arb (`carry_basis_perp` / `funding_rate_dispersion`)** — CeFi-perp-heavy:

| data_type                             | venue(s)                                                                                                  | asset_group         | producing service                | feature consumed                   | required history                                                           |
| ------------------------------------- | --------------------------------------------------------------------------------------------------------- | ------------------- | -------------------------------- | ---------------------------------- | -------------------------------------------------------------------------- |
| `perp_funding`                        | BINANCE, OKX, BYBIT, DERIBIT, HYPERLIQUID, ASTER, KRAKEN (dispersion needs **all** venues simultaneously) | cefi (+ defi perps) | MTDS → features-delta-one        | `funding_rate_annualised_bps`      | full funding-cycle history; dispersion needs same timestamps across venues |
| `book_snapshot_5` / derivative_ticker | same perp venues (Tardis)                                                                                 | cefi                | MTDS → MDPS → features-delta-one | mark price, index, current funding | window length                                                              |
| `trades` (spot leg)                   | BINANCE/OKX/BYBIT spot; UNISWAP_V3, JUPITER (DEX spot)                                                    | cefi + defi         | MTDS → MDPS candles              | spot fills / slippage sim          | window length                                                              |
| processed candles `1h`/`4h`           | (derived)                                                                                                 | per leg             | MDPS                             | `realized_vol_20` (vol-cap clamp)  | ≥ vol-lookback window                                                      |

**basis carry (`carry_basis_dated`)** — dated future vs spot:

| data_type                      | venue(s)                                                         | asset_group      | producing service | feature consumed                     | required history                                                |
| ------------------------------ | ---------------------------------------------------------------- | ---------------- | ----------------- | ------------------------------------ | --------------------------------------------------------------- |
| `trades` (spot leg)            | DERIBIT (BTC/ETH), CME/Databento (TradFi), UNISWAP_V3 (DEX spot) | defi/cefi/tradfi | MTDS → MDPS       | `basis_bps` numerator                | window length                                                   |
| `trades` (dated future leg)    | DERIBIT quarterly, CME/ICE (TradFi)                              | cefi/tradfi      | MTDS → MDPS       | `basis_bps`                          | per-contract life + roll window (`rollover_days_before_expiry`) |
| `ohlcv_1m` / processed candles | Databento pass-through (TradFi), MDPS (crypto)                   | tradfi/cefi/defi | MTDS/MDPS         | basis convergence + `realized_vol_*` | window + roll                                                   |

> Sources for the expected set (read these, don't copy the snapshot): archetype files in
> `codex/09-strategy/architecture-v2/archetypes/`; `Features expected` lists in the
> `strategy-service/.../v2/carry_and_yield/*.py` engines; canonical data_type names + buckets in
> `codex/02-data/defi-data-types-catalog.md`; venue/capability backing in
> `unified-api-contracts/unified_api_contracts/registry/defi_venues.py`; lineage in
> `codex/02-data/data-lineage-MTDS-features-ml.md`.
>
> **The expected set is driven by the canonical coverage SSOT, NOT the snapshot above.** The denominator for "in
> totality" is `EXPECTED_COVERAGE_BY_ASSET_GROUP` in
> `unified-api-contracts/unified_api_contracts/registry/expected_coverage.py` (per-asset_group `_CEFI` / `_DEFI` /
> `_TRADFI` venue→data_type maps, with `is_expected()` + `get_source_coverage_start_for_data_type()` +
> `is_before_source_coverage_start()` helpers). Enumerate **every** venue × data_type that map declares for the
> strategy's data_types — do not trim to a representative subset. The venue universe is the union of `_CEFI` (the full
> CeFi perp set — Binance/Bybit/OKX/Deribit/Kraken + on-chain perps Hyperliquid/Aster/Pacifica/Lighter/GMX/Drift), the
> DeFi venues in `registry/defi_venues.py` (`ALL_DEFI_VENUES`), and the chain dimension `ChainKind`
> (`canonical/crosscutting/defi.py`, 22 chains). `perp_funding_cadence.py` gives per-venue funding cadence for the
> window check.

### Step 1.5 — Find the data before declaring it missing (MANDATORY — anti "0% captured" lie)

> **Genesis (2026-06-01)**: a first run of this audit read only
> `market-data-tick-defi-*/_index/availability_index.parquet` and reported **"0% captured / lst_rates absent / data
> genuinely missing"** for every DeFi data_type. That was FALSE. The real data lives in **dedicated per-data_type
> buckets** (`lst-rates-*` 92% captured back to 2020, `lending-indices-*` 91%, `oracle-prices-*` 79%, `perp-funding-*`
> 55%, `dex-pools-*` 96%, `dex-swaps-*` 93%), each with its **own** `_index/availability_index.parquet`. The
> `market-data-tick-defi` index held only a **phantom empty grid** (a cartesian `data_type × venue` cross-product in
> legacy `VENUE-CHAIN` format with everything `empty_confirmed`). Reading one index and concluding "missing" is a
> **grep-then-conclude** violation. **Data is almost never genuinely missing — it is in the wrong bucket, under a
> hyphen/underscore alias, on an old schema version, or behind a phantom placeholder grid.**

Before any cell can be called "missing", **exhaust where the data could be hiding**:

- [ ] **Enumerate ALL candidate buckets per data_type, not just `market-data-tick-{ag}`.** DeFi data_types have
      **dedicated buckets**: `lst-rates-*`, `lending-indices-*`, `oracle-prices-*`, `perp-funding-*`, `dex-pools-*`,
      `dex-swaps-*` (+ `evm-defi-*`, `features-onchain-defi-*` for derived). Resolve the canonical bucket per
      `(data_type, kind)` from `resolve_bucket_name()` / `deployment-service/configs/cloud-providers.yaml`, then list
      **every** bucket whose name matches the data_type.
      `gcloud storage ls | grep -iE 'lst-rates|lending-indic|perp-funding|oracle-price|dex-pool|dex-swap'`. Each has its
      own `_index/availability_index.parquet` — read **all** of them and the `market-data-tick-*` one, then reconcile.
- [ ] **Check object reality, not just the index.** If an index says empty but `gcloud storage ls gs://<bucket>/day=*/`
      returns thousands of parquet files, the **index is stale/phantom** — that is a manifest-consolidation finding, not
      an absence. Count objects (`... | grep -c '\.parquet'`) and sample recent `day=` partitions.
- [ ] **Look under aliases + wrong forms of the same data_type.** The same logical data_type appears as: hyphen vs
      underscore (`lending-indices` AND `lending_indices`, `dex-pools` AND `dex_pools`, `dex-swaps` AND `dex_swaps` all
      coexist in their buckets — 2026-06-01); legacy semantic name (`staking_yields` vs canonical `lst_rates`); legacy
      `VENUE-CHAIN`-embedded venue strings (`UNISWAPV3-ETHEREUM`) vs flat venue + `chain` column. Query
      `df.data_type.unique()` and `df.venue.unique()` in **every** index and treat any alias/variant as the SAME data —
      it is data-in-wrong-form to be cleaned up, NOT missing data.
- [ ] **Two indexes disagreeing = phantom-grid finding.** When the dedicated bucket shows `captured` but
      `market-data-tick-defi` shows `empty_confirmed` for the same `(data_type, venue, date)`, the `market-data-tick`
      row is a phantom placeholder. Flag it for deletion/reconciliation — never let the phantom drive a "missing"
      verdict.
- [ ] **Classify every gap into one of: wrong-bucket / wrong-name-alias / phantom-index-grid / old-schema-version /
      genuinely-partial-window / genuinely-missing.** Only the last is "download more"; the rest are **cleanup /
      consolidation / migration** of data that already exists. The result MUST state which of these each gap is — a bare
      "X% captured" with no wrong-form classification is review-blocking.

### Step 2 — Coverage checklist (compare expected set vs actual corpus)

- [ ] (o) **instruments-service universe present + IS-grounded denominator**: every venue × symbol the matrix needs is
      an active `InstrumentRecord` in instruments-service (IS is SSOT for the universe; MTDS derives URLs from it —
      never hardcoded). For each strategy, confirm the LST tokens, perp contracts, dated-future contracts, and DEX pools
      it trades are listed (not phantom / not deprecated). Gap here = MTDS will never attempt the cell → silent
      `MISSING_EXPECTED` downstream. **The IS active-instrument set per (data_type, venue, chain) is the denominator
      base for coverage % — NOT the count of rows the manifest happened to enumerate.**

- [ ] (p) **Expected-coverage denominator = IS ∩ UAC, NOT manifest self-enumeration (CRITICAL — codified 2026-06-01)**:
      a captured % is meaningless unless its denominator is the **possible-availability** set. Build it from two SSOTs,
      not from the manifest's own row count: **(1) instruments-service** active `InstrumentRecord`s (the universe that
      should exist), gated by **(2) UAC** `EXPECTED_COVERAGE_BY_ASSET_GROUP` + `is_expected()` + `venue_launch_dates` +
      `ChainKind` genesis + `get_source_coverage_start_for_data_type()` (the windows where data is _possible_).
      Materialise it: `python3 plans/audit/results/a2_materialize_expected_coverage_dump.py` (the `expected_coverage()`
      oracle already composes UAC scope + launch + genesis + source-coverage-start). Then report **TWO numbers per
      (data_type, venue, chain)**, never just one: - **enumerated-coverage** = `captured / rows-the-manifest-enumerated`
      (what a naive bucket read gives — e.g. `lst_rates` 92%). High here only means "of what was attempted". -
      **true-coverage** = `captured / (IS ∩ UAC-expected cells)`. The gap between the two is **manifest
      under-enumeration** — venues/chains UAC says are expected but the manifest never created a row for. 2026-06-01:
      manifest enumerated only `lst_rates` 14/22, `lending_indices` 6/21, `perp_funding` 5/8 of the UAC-expected venue
      keys (some of that gap is the `VENUE-CHAIN`-vs-flat naming split — reconcile that first per Step 1.5 — but genuine
      absentees remained: `DRIFT-SOLANA`, `FRAX`, `MORPHO`, `FLUID`). **A coverage % quoted without its IS∩UAC
      denominator + the under-enumeration list is review-blocking.**

- [ ] (q) **Manifest divergence for the strategy cells = 0 — across ALL candidate buckets (per Step 1.5)**: run the
      divergence scan and filter to the matrix cells. Run: `python3 plans/audit/results/a3_manifest_divergence.py` (and
      the all-services variant `a3v2_manifest_divergence_all_services.py`). **`a3` reads only `market-data-tick-{ag}` —
      for DeFi data_types that is the phantom grid; you MUST also read the dedicated-bucket indexes** (`lst-rates-*`,
      `lending-indices-*`, `oracle-prices-*`, `perp-funding-*`, `dex-pools-*`, `dex-swaps-*`) and use the **max**
      captured state across buckets as truth. For every `data_type` in the matrix, **zero** `MISSING_EXPECTED` and
      **zero** `DIVERGENT_EMPTY` once the dedicated buckets are included. A cell that is `captured` in the dedicated
      bucket but `empty_confirmed` in `market-data-tick-defi` is a **phantom-grid finding** (cleanup), not a download
      item.

- [ ] (r) **Per-data_type schema-version compliance read from DATA (not the constant)**: the manifest is on **v9**
      (`MANIFEST_SCHEMA_VERSION = 9`; v9 added the tradfi `source` column). Read the actual `schema_version` column
      distribution **per data_type** for each strategy's cells — ≥95% at v9. Run / adapt
      `plans/audit/results/a4_manifest_v8_compliance.py` (rename target → v9; the script name still says v8 — that is a
      **stale-tooling finding**, fix it). **Do not trust the code constant** — incident 2026-05-20: 0% of 7.4M prod rows
      were at v8 despite the constant being bumped. Read the dedicated buckets (Step 1.5): 2026-06-01 found a **schema
      spread v4–v8 with ZERO v9** (`lst-rates` v6/7/8, `lending-indices` v4/6/7/8, `dex-pools` v4/5/6). Old-version rows
      are **data-in-wrong-form → re-version migration of existing data**, NOT missing data and NOT a re-download.

- [ ] (s) **Venue + data_type names migrated to SSOT in the actual rows (data-in-wrong-form sweep)**: the manifest rows'
      `data_type` and `venue` string values use the **canonical** names, not legacy aliases. Canonical data_types:
      `dex_swaps` / `dex_pool_state` / `lending_indices` / `perp_funding` / `lst_rates` / `vault_share_price` /
      `oracle_prices` (NOT `swap_events` / `pool_state` / `lending_metrics` / `funding_rates`). Query **every** index
      (dedicated buckets + `market-data-tick`) for distinct `data_type` and `venue` values and flag each wrong-form
      found 2026-06-01: **(1) hyphen-vs-underscore duplicates of the same data_type coexisting** (`lending-indices` +
      `lending_indices`; `dex-pools` + `dex_pools`; `dex-swaps` + `dex_swaps`) — pick the underscore canonical, migrate
      the hyphen rows; **(2) legacy semantic alias** (`staking_yields` rows that are really `lst_rates`); **(3) legacy
      `VENUE-CHAIN`-embedded venue strings** (`UNISWAPV3-ETHEREUM`) that should be flat `venue` + a populated `chain`
      column. Any alias/variant in **written rows** = an un-migrated-SSOT finding → **rename/normalise migration** (the
      data exists; this is cleanup, not download). Per-corpus expression of code items (j)/(l)/(n) above. **(4)
      INDEX-venue ≠ OBJECT-venue ≠ UAC-canonical (codified 2026-06-01)** — the manifest INDEX may carry a venue string
      that differs from the venue in the actual GCS object paths AND from UAC `ALL_DEFI_VENUES`. 2026-06-01: index
      `UNISWAPV3`/`AERODROMEV3`/`PANCAKESWAPV3`/`SUSHISWAPV3`/`CAMELOTV3`/`TRADER_JOEV2`/`VELODROMEV2` vs objects + UAC
      `UNISWAP_V3`/`AERODROME_V3`/… (underscore before the version). This silently breaks any index↔object join (a
      coverage-vs-objects walk falsely reports 74% "phantom"). **Check**:
      `set(index.venue) == set(object-path venue) ==     flat(UAC ALL_DEFI_VENUES)` per bucket. **Fix = MIGRATE the
      index venue values to the UAC/object canonical — do NOT normalise venue names in read-path code** (a runtime
      band-aid causes downstream issues; the data must be canonical at rest). Same applies to chain strings.

- [ ] (t) **Required-history window actually covered (timeframe audit)**: for each strategy's cells, read min/max
      `available_at` from the manifest and confirm the **continuous** window meets the strategy's lookback need (Step 1
      `required history` column — e.g. ≥30d of daily `lst_rates` snapshots for a stable staking APY; full funding-cycle
      history with no multi-day holes for funding dispersion; per-contract life + roll window for dated basis). A
      data_type that exists but only for the last N days, or with interior gaps, is a **partial-coverage** finding →
      backfill item with the exact missing date range. Cross-check interior gaps against `is_in_known_gap()` /
      documented source-coverage windows before flagging (a real source gap → `empty_confirmed`, typed; everything else
      → download).

- [ ] (u) **features-service emits the consumed feature over the same window**: for each `feature consumed` in Step 1
      (`staking_apy_bps`, `funding_rate_apy_bps`/`funding_rate_annualised_bps`, `basis_bps`, `realized_vol_*`,
      `lst_native_rate`, `health_factor`, `usdc_idle_yield_apy_bps`), confirm features-service actually produces it for
      the strategy's instruments over the required window — feature presence in code ≠ feature rows in the corpus. A
      feature that is wired but never backfilled, or defaults silently to 0 (e.g. `usdc_idle_yield_apy_bps`), is a
      coverage finding, not "fine because it has a default". Cross-ref the features-and-ml audit
      (`features_and_ml_master_audit_instructions.md`) per-feature backfill state.

- [ ] (v) **Honest-coverage totality breakdown — per data_type × venue/chain (THE deliverable)**: do not report a single
      roll-up % per strategy. Produce the full breakdown where **every** expected cell carries one of the 4-state
      honest-coverage verdicts read from the manifest — `captured` / `empty_confirmed[reason=<typed>]` /
      `attempted_failed` / `expected_unattempted` — or `MISSING_EXPECTED` if the manifest has no row at all. Two
      breakdowns are mandatory, both enumerated from the SSOTs (no representative subsetting): - **Per data_type × venue
      (in totality)**: for `perp_funding`, enumerate the **complete** CeFi perp venue set from `_CEFI` in
      `expected_coverage.py` (Binance/Bybit/OKX/Deribit/Kraken) **plus** the on-chain perps
      (Hyperliquid/Aster/Pacifica/Lighter/GMX/Drift) — every venue gets a row even if the current strategy only hedges
      on a subset, because funding-dispersion needs the whole set and the operator wants the venue universe assessed in
      totality. Likewise `lst_rates` → every LST venue, `lending_indices` → every lending venue, `dex_swaps`/
      `dex_pool_state` → every DEX, `oracle_prices` → every oracle. - **Per data_type × chain**: for chain-scoped
      data_types (`lst_rates`, `oracle_prices`, `lending_indices`, `dex_swaps`, `dex_pool_state`), break coverage down
      across `ChainKind` (Ethereum, Arbitrum, Base, Optimism, Polygon, …, Solana, plus the perp L1s) — a data_type
      "captured" on Ethereum but absent on Arbitrum/Base is a per-chain gap, not a green cell. A cell counts as
      honest-green only when its verdict is `captured` over the required window (item t) at v9 (item r) with canonical
      names (item s). `empty_confirmed` is green **only** when the typed reason is verified against
      `is_before_source_coverage_start()` / `is_in_known_gap()`; an `empty_confirmed` on an owed-data branch is a
      silent-lie finding, not coverage. Everything else is a download/migration backlog row (Step 3). **Both breakdowns
      are PER-VENUE AND PER-CHAIN — never a single data_type roll-up.** The per-venue/chain cut is where the real gaps
      hide (2026-06-01: aggregate `lst_rates` 92% hid `MARINADE` 61% / `ETHERFI` 70% / Solana 70%; aggregate
      `oracle_prices` 79% hid `PYTH` 48% and **Solana 0% captured**; aggregate `perp_funding` 55% hid `LIGHTER` 0% /
      `PACIFICA` 28% / **`DRIFT` absent**). Each cell's % MUST carry its **IS∩UAC denominator** (item p) — both
      enumerated-coverage and true-coverage — so an under-enumerated venue/chain reads as a gap, not a green.

- [ ] (w) **The data-status tab (deployment-ui/API) must produce these honest numbers BY DEFAULT — verify code alignment
      (codified 2026-06-01)**: the dashboard, not just the audit, must use the right numerator/denominator/ breakdown.
      The audit MUST read the data-status code and confirm it matches items (p)/(v). Code surfaces:
      `deployment-api/deployment_api/services/data_status_service.py` (`_build_coverage_for_cat` ~L3454,
      `_get_coverage_summary_sync` ~L3498, `_read_defi_merged_index` ~L2931, `_mtds_honest_coverage_for_venue` ~L1414,
      `_mtds_expected_dates_cached` ~L1130) + route `deployment-api/.../routes/data_status.py` (`/api/coverage-summary`,
      `/api/manifest-status`) + the deployment-ui data-status view + the rollup worker
      `deployment-api/.../scripts/data_status_rollup_worker.py`. Verify each: - **Denominator = IS ∩ UAC expected, NOT
      manifest row count.** `manifest-status` (`_mtds_expected_dates_cached`) does this correctly (clips by
      `chain_genesis` + `venue_launch` + `source_coverage_start`). **`coverage-summary` (`_build_coverage_for_cat`) does
      NOT — it uses `len(index)` as both numerator and denominator (self-referential, 2026-06-01 finding).** Both
      endpoints must share the expected-dates oracle so they never contradict. - **`is_expected()` scope gate applied to
      the denominator** (drop out-of-scope `(venue, data_type)` before counting) — currently only used in the per-row
      `_classify_datum_scope`, not in the coverage-summary total. - **Reads the dedicated per-data_type buckets** (not
      just `market-data-tick-defi` phantom grid). `coverage-summary` already does via `_read_defi_merged_index` +
      `_filter_to_canonical_defi_venues` ✅ — confirm it stays that way and that the rollup worker does too. -
      **Per-venue AND per-chain breakdown surfaced** (DeFi venues are PROTOCOL-CHAIN; split them). Currently
      per-venue-string only — per-chain is computed for expected-dates but not displayed. - **Drilldown (the most useful
      "where's the missing data" UI)**: `/api/data-status/drilldown/{service}/{asset_group}` →
      `data_status_hierarchical.get_hierarchical_drilldown` + `data_status_drilldown.get_shard_info`. Verify it shows
      the **full 4-state validity per cell** incl. `expected_unattempted`/`MISSING_EXPECTED` (2026-06-01: only 3-state →
      genuinely-missing cells absent from the tree, invisible to the operator), and its denominator is IS∩UAC expected,
      not `captured/(captured+empty+failed)`. It already reads dedicated buckets + breaks down per venue×chain×date +
      shows `error_reason` ✅. Any divergence = a code-alignment finding → fix in `data_status_service.py` /
      `data_status_hierarchical.py` so the tab is honest by default, then the audit just re-confirms. **The audit and
      the dashboard must compute coverage the SAME way.**

- [ ] (x) **L1 — Manifest integrity: are all the scattered data_types/schemas recorded correctly + completely IN?**
      (codified 2026-06-01). The DeFi corpus is spread across many dedicated buckets each with its own schema spread and
      its own `_index/availability_index.parquet`; the canonical manifest the API/consolidator reads MUST faithfully
      include them all. Check, per dedicated bucket (`lst-rates-*`, `lending-indices-*`, `oracle-prices-*`,
      `perp-funding-*`, `dex-pools-*`, `dex-swaps-*`, `evm-defi-*`, `solana-defi-*`, `gas-fees-*`, `liquidations-*`): -
      **No orphan objects**: every actual GCS parquet (`day=*/…parquet`) has a corresponding manifest row. Sample-count
      objects vs manifest rows per `(venue, chain, day)`; object-count >> manifest-row-count = un-recorded data (the
      manifest is blind to real data). 2026-06-01 reference: lst-rates had **34,843 objects** but the index had **16,766
      rows** — confirm that ratio is the bundling factor, not un-recorded objects. - **No phantom rows**: every manifest
      row maps to a real object (the `market-data-tick-defi` cartesian grid is the known phantom — quantify it). -
      **Fields recorded correctly**: `data_type` / `venue` / `chain` / `schema_version` populated + canonical (composes
      with (r)/(s) — but here the question is _manifest completeness/correctness_, not just naming). Flag rows with
      `chain` null but venue embedding the chain (`UNISWAPV3-ETHEREUM`). - **Consolidation reaches the canonical
      surface**: confirm the manifest consolidator (Cloud Run jobs) folds every dedicated-bucket index into whatever the
      data-status API + a3 read — a bucket whose index never reaches the canonical manifest is invisible to every
      downstream consumer. This is the root of the phantom/0% confusion. Output a per-bucket integrity table:
      `bucket | objects | manifest-rows | orphans? | phantoms? | schema-spread | reaches-canonical?`.

- [ ] (y) **L3 — Pipeline coverage propagates IS → MTDS → MDPS → features (defi/perp/on-chain)** (codified 2026-06-01).
      Coverage is not done at the raw-tick layer — track it **up to features-service**, which is what strategy actually
      consumes. For each strategy cell, confirm the derived feature exists over the same window in the features buckets:
      `features-onchain-defi-*` (`staking_apy_bps`, `lst_native_rate`, `funding_rate_apy_bps`, `health_factor`),
      `features-delta-one-*` (`funding_rate_annualised_bps`, `basis_bps`), `features-volatility-defi-*`
      (`realized_vol_*`). Read each features bucket's `_index/availability_index.parquet`. A cell `captured` at MTDS
      (`lst_rates` 92%) but the feature absent/partial at `features-onchain-defi` over that window = an **L3 propagation
      gap** (the strategy still can't run). Report coverage **per stage** (IS-listed → MTDS-captured →
      MDPS-processed-where-applicable → feature-emitted) so the stage that drops the cell is named. Composes with
      `features_and_ml_master_audit_instructions.md`.

- [ ] (z0) **Migrate-to-canonical BEFORE backfill (HARD sequencing, operator 2026-06-01)**: a bucket must be in
      **canonical form** — env-split (`{kind}-{env}-{project}`), `asset_group=` (not `category=`),
      `pipeline_mode={mode}` hive partition present, schema v9, underscore data_type names, flat venue + populated
      chain, typed empty reasons — **before** any backfill writes into it. Backfilling into the legacy layout
      manufactures more non-canonical data ("this is why we keep having mess"). The audit MUST flag any backfill/run
      proposed against a non-canonical bucket as review-blocking. Check the actual object paths (`gcloud storage ls`)
      for `category=`/missing-`pipeline_mode=`/ no-env-suffix, and the index for v<9 / hyphen-names / blank-chain. SSOT:
      `plans/active/defi_manifest_canonicalisation_2026_06_01.md` § "Sequencing" + "Canonical target form".

- [ ] (z) **`expected_unattempted` materialised + manifest-annotates-once principle (codified 2026-06-01)**: the
      manifest MUST carry the full 4-state — `captured` / `empty_confirmed[reason]` / `attempted_failed` /
      **`expected_unattempted`** — so a cell that IS-lists + is post-genesis/post-launch but has **no data** appears in
      the denominator (not silently absent). Verify: (1) `expected_unattempted` is in the UAC `CaptureStatus` closed
      set; (2) the manifest consolidator (`unified_trading_library/manifest_consolidator.py`) materialises owed cells
      from the `expected_coverage()` oracle at consolidation (index-layer only, no placeholder parquets); (3) read the
      actual manifest —
      `% captured = captured / (captured + empty_confirmed + attempted_failed + expected_unattempted)`, and
      `expected_unattempted` count > 0 where data is owed (2026-06-01: it was **never materialised** — 0 source hits,
      `expected=True` on every present row = useless). **Consumers (data-status summary + drilldown + strategy/features
      preflight) READ this 4-state; none re-derives the expected set.** A consumer computing its own denominator (the
      `coverage-summary` self-referential bug, the drilldown 3-state) = a review-blocking divergence. The audit confirms
      all consumers read the same canonical manifest 4-state. SSOT:
      `plans/active/defi_manifest_canonicalisation_2026_06_01.md`.

- [ ] (aa) **Fetch-failure must be `attempted_failed`, NOT `empty_confirmed` — per-adapter swallow audit (codified
      2026-06-01, operator)**. Applies to **EVERY adapter/handler that does external I/O in instruments-service, MTDS,
      and features-service** (RPC reads, REST/HTTP fetches, subgraph queries, vendor SDKs). The bug pattern: a fetch
      helper does `except Exception: … return []` (or `return None` / empty DataFrame), **swallowing** the error, so the
      caller sees "zero rows + no error" and records `record_empty(SOURCE_RETURNED_ZERO)` = `empty_confirmed` — a
      **silent lie** that the data is genuinely empty when the fetch actually **failed** (timeout / DNS / RPC / auth). A
      transient network failure then pollutes the manifest as honest-empty, corrupting coverage + downstream
      preflight. - **Find every site**:
      `rg -U "except\b[^\n]*:\s*\n(\s*[^\n]*\n)?\s*return (\[\]|None|\{\}|pd\.DataFrame\(\))"       instruments-service/ market-tick-data-service/ features-service/ --include="*.py" -g '!*test*'`
      — plus read each adapter's outermost fetch try/except. - **For each**: confirm the failure path reaches
      `record_failed` (`attempted_failed`), not `record_empty`. A swallow that returns empty → caller's `error` var
      stays None → `record_empty` is the bug. Fix = **re-raise** (or return a typed failure sentinel) so the caller's
      existing `record_failed` fires. **Only a genuine source-zero with no exception may be `empty_confirmed`.** -
      2026-06-01 instances found + fixed (mtds): `lst_rates_handler` Solana fetch (L697), `oracle_prices_handler` Pyth
      L820/L948 → now re-raise. **Still open**: `lending_indices_handler` Aave RPC-fallback L989 (nested), + sweep
      instruments-service + features-service. **Every adapter must be checked** — this is a closed per-adapter
      checklist, not a spot-check. Composes with the `record_empty` honest-absence rules + UAC `classify_venue_error()`.

### Step 3 — Output: classify every gap (cleanup vs download), then backlog it

Every RED/AMBER cell from items (o)–(z) becomes an explicit, actionable backlog line — **not** a "deferred" note. **Most
DeFi "gaps" are data-in-wrong-form (the data already exists), NOT missing data — classify before you write "download".**
Per `External Data Is Always Available` + `Data Pipeline Correctness Is The Heartbeat`, each cell is exactly one of:

1. **Cleanup — wrong bucket / phantom index** (most common, 2026-06-01): data is `captured` in a dedicated bucket
   (`lst-rates-*` etc.) but the `market-data-tick-defi` grid shows it empty → reconcile/delete the phantom grid + point
   the data-status denominator at the real index.
   `- [ ] [CLEANUP] P#. Reconcile <data_type> phantom-empty grid in market-data-tick-defi vs captured rows in <dedicated-bucket> — parent_epic: defi_master`.
2. **Cleanup — alias / name normalisation** (item s): hyphen-vs-underscore duplicates, `staking_yields`→`lst_rates`,
   `VENUE-CHAIN`→flat venue+chain.
   `- [ ] [MIGRATION] P#. Normalise <alias> → <canonical> in <bucket> (data exists) — …`.
3. **Migration — re-version** (item r): present at v4–v8, needs v9. Bundle into the single-walk migration window (no new
   whole-corpus GCS walk without operator ack).
4. **Download/backfill** — genuinely-partial window or venue truly never captured (only after Step 1.5 exhausted all
   buckets/aliases): `- [ ] [DATA] P#. Backfill <data_type> <venue> <ag> over <start>..<end> via <collect-op> — …`.
5. **`BLOCKED-CREDENTIALS`** — public/free path exhausted; file the credential ask ping. Status stays
   `BLOCKED-CREDENTIALS`, NOT `DEFERRED`.
6. **Genuine `empty_confirmed`** — source truly has no data over that window (verified via `is_in_known_gap()` /
   `is_before_source_coverage_start()`) → typed reason, **excluded** from the backlog (the only legitimate "missing").

Render the result as a coverage matrix (rows = strategy × data_type × **venue × chain**; columns =
`enumerated-cov / true-cov (IS∩UAC denom) / captured / v-spread / window-covered / which-bucket / verdict (one of the 6 above)`)
plus the classified backlog list. **A bare "X% captured" with no IS∩UAC denominator, no per-venue/chain split, no
wrong-form classification, and no list of buckets searched is review-blocking.** Wire each backlog line into an active
plan under `parent_epic: defi_master` immediately (Capture Discoveries HARD RULE). Item (w) code-alignment gaps →
`deployment_and_user_management_master` / `observability_master` backlog.

### E2E Batch, Paper, and Live Verification

- (e2e-batch) **Batch e2e**: For the MVP archetypes of this domain, run a dry-run batch audit using mock upstream
  fixtures (`CLOUD_MOCK_MODE=true CLOUD_PROVIDER=local`) — confirm signals are generated end-to-end from adapter output
  through strategy. If real upstream unavailable, synthetic fixtures from `tests/e2e/fixtures/` suffice; the test MUST
  exercise the downstream code regardless of upstream readiness.
- (e2e-paper) **Paper trading audit** (once paper is running): confirm paper PnL events flow from strategy → execution →
  PnL calculator for ≥1 MVP archetype in this domain. Check manifest for strategy_output rows with
  `capture_status=captured` for the date range. If paper not yet running, verify the code path is wired (not
  BLOCKED-CREDENTIALS level — code exists, paper not started).
- (e2e-live) **Live trading audit** (once live is running): verify live execution produces execution_record rows in
  manifest with no DIVERGENT_EMPTY. Alert thresholds fire within SLA. PnL reported correctly.
- (mock-upstream) **Mock upstream pattern**: this domain's audit MUST be runnable WITHOUT live upstream data. Document
  the exact `pytest` fixtures or `CLOUD_MOCK_MODE=true` invocation in `## Output Format` so any slot can run the
  downstream-only audit independently.

## Canonical-form coverage (CF-1…CF-12)

> Cites the SSOT `plans/audit/instructions/canonical_form_cross_service_audit_checklist.md`. Run CF-1…CF-12 against the
> `market-data-tick-defi-prd-…` `_index` + objects (DATA-STATE, not constants). Remediation owner =
> `defi_manifest_canonicalisation_2026_06_01.md` §C. CF-4 (`source` column) is covered by the Dual-source provenance
> section above (defi multi-source: `oracle_prices`=pyth+chainlink, `native_staking_rates`=solana_rpc+helius_rpc).

- [ ] (CF-1/2/3/8/9/10/12) SSOT checks on `market-data-tick-defi-prd-…`: schema_version=v9 (data-state) · `asset_group=`
      not `category=` (paths+rows) · `pipeline_mode=` partition · honest `available_at` · env-split bucket · no
      phantom/date-impossible captured · batch=live. GREEN = all data-state.
- [ ] (CF-5 defi reasons) every empty defi cell typed: `EXPECTED_PRE_GENESIS_CHAIN` / `EXPECTED_PRE_VENUE_LAUNCH` (UAC
      `DEFI_VENUE_LAUNCH_DATES`) / genuine `SOURCE_RETURNED_ZERO`; 0 blank/mislabeled.
- [ ] (CF-7 defi names) underscore data_type
      (`dex_pools`/`lst_rates`/`lending_indices`/`oracle_prices`/`perp_funding`) + flat `venue` + populated `chain` +
      `{VENUE}_V{N}` (`UNISWAP_V3`/`TRADER_JOE_V2`/`VELODROME_V2`).

## DeFi-specific standing checks (added 2026-06-08) — source-aware migrator + venue-launch honesty

- [ ] (defi-srcaware) **migrator + rebuild stamp source-aware pipeline_mode** — `migrate_defi_full_v9_canonical` and
      `rebuild_defi_manifest` stamp `pipeline_mode=batch_<source>` via `derive_pipeline_mode_for_row` (DeFi was the LAST
      coarse writer — the C-PATH WRITE fix). Regression guard: `rebuild_defi_manifest.py` never re-introduces the
      blank/coarse stamp (the `:302` class); grep MTDS for `DEFAULT_PIPELINE_MODE = "batch"` → 0.
- [ ] (defi-zero) **`record_zero_rows` is venue-launch-date-aware** — DeFi zero-row shards route through
      `DefiManifestRecorder.record_zero_rows` (pre-launch → `EXPECTED_PRE_VENUE_LAUNCH`, not `SOURCE_RETURNED_ZERO`);
      the A10c QG ratchet enforces routing.
- [ ] (defi-launch) **`DEFI_VENUE_LAUNCH_DATES` populated** for every venue-chain (A2a) — the genesis/launch rules that
      drive `expected_unattempted` honesty; no venue-chain missing its launch date.
- [ ] (defi-sources) **per-data_type sources** — `onchain_subgraph`/`onchain_rpc` (DEX/gas) · `pyth_hermes` (Solana
      oracle) · `chainlink` (EVM oracle) · `hyperliquid` (perp; NOT `hyperliquid_rest`); every cell a non-blank
      `source`.
- [ ] (defi-backstop) **`EmptyFromLiveInstrumentError` backstop wired + enforced** (A10) — defined AND raised, not
      defined-only.
- [ ] (defi-dexpool-name) **canonical DEX data_type = `dex_pool_state` / `dex_pool_swaps`, NEVER `dex_pools`** (operator
      SSOT `defi-canonical-naming-ssot.md`, 2026-06-01 — the `→dex_pools` rename was REVERSED). `dex_pools_handler.py`
      writes `dex_pool_state` to BOTH path AND manifest (no 2-layer split); migrator stamps `dex_pool_state` (no remap);
      features read `dex_pool_state`. Grep handler/migrator/features for a `data_type="dex_pools"` write or a
      `dex_pool_state→dex_pools` remap → 0. Guards against a future agent acting on the `mtds_mdps_master.md` Phase 9
      dead-letter (SUPERSEDED) and re-introducing the manifest≠data split that D14 originally (mis-)reported.

## Success Criteria

- All code-correctness checklist items GREEN (incl. code↔codex drift items j–n)
- **All strategy data-coverage items (o)–(z) GREEN** for each in-scope archetype — every matrix cell `captured` over its
  required window at v9, or a verified typed `empty_confirmed`, or a tracked download-backlog line (no silent gap)
- **Honest-coverage totality breakdown (item v) rendered in full** — both per data_type × venue (complete CeFi perp
  universe + on-chain perps + LST/lending/DEX/oracle venues) and per data_type × chain (`ChainKind`), every expected
  cell carrying a 4-state verdict; no roll-up % stands in for the breakdown
- `a6_batch_live_adapter_parity.py` shows 100% parity for `asset_group=defi` rows
- Manifest divergence A3: zero `MISSING_EXPECTED` and zero `DIVERGENT_EMPTY` for the strategy cells across
  `asset_group ∈ {defi, cefi, tradfi}`
- Per-data_type schema-version read from actual rows ≥95% at v9 for every strategy cell
- No legacy data_type/venue alias appearing in written manifest rows for `asset_group=defi`
- QG exits 0 for all DeFi-touching services (execution-service, strategy-service)
- e2e batch audit produces signals for ≥1 MVP archetype using mock upstream data (CLOUD_MOCK_MODE=true green)
- Paper trading goal post: ≥1 archetype runs ≥7 continuous paper days without silent failures

## Output Format

Result file at `plans/audit/results/defi_master_audit_YYYY_MM_DD.md` must contain:

1. Frontmatter: `type: audit-result`, `epic: defi_master`, `instructions_ref: this file`, `auditor:`, `date:`, `status:`
2. Each checklist item (a)–(u): GREEN / AMBER / RED + grep output or script result as evidence
3. **Honest-coverage totality breakdown (item v)** — TWO tables, every expected cell present (no subsetting): (a) **per
   data_type × venue** with the complete CeFi perp set + on-chain perps + LST/lending/DEX/oracle venues, and (b) **per
   data_type × chain** across `ChainKind` for the chain-scoped data_types. Each cell column set:
   `expected | capture_status (captured/empty_confirmed[reason]/attempted_failed/expected_unattempted/MISSING) | v9% | window-covered | verdict`.
   This is the per-data_type, per-venue/chain answer the operator asked for.
4. **Download backlog**: one `- [ ] [DATA|BLOCKED-CREDENTIALS] P#. <venue × data_type × date-range × collect-op>` line
   per missing/partial/mis-versioned cell, each already wired into an active plan under `parent_epic: defi_master`
5. Gap items: `- [ ] [TYPE] P#. <description> — parent_epic: defi_master` for each RED/AMBER code item
6. Table: `gap item | active plan absorbing it | plan status`
7. Archive condition: "Archives when all gap items below are `- [x]` in their parent plans"

## Linked Results

| Date       | Result file                                                                                                       | Status                                                                                                                                                                          |
| ---------- | ----------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-06-01 | [`results/defi_master_audit_2026_06_01.md`](../results/defi_master_audit_2026_06_01.md)                           | **AMBER** — strategy data-coverage (o–v): data EXISTS 79–96% in dedicated buckets; real issues are wrong-form (phantom grid + alias dupes + v4–v8 schema). Genesis of Step 1.5. |
| 2026-05-27 | [`results/defi_pipeline_code_codex_drift_2026_05_27.md`](../results/defi_pipeline_code_codex_drift_2026_05_27.md) | active (code↔codex drift, items j–n)                                                                                                                                            |
