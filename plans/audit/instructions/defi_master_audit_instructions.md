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

## Epic Scope

DeFi adapters, on-chain execution, Copper custody path, and the DeFi MVP archetypes. Two audit dimensions share this
doc:

| Dimension | What it checks | Section |
| --- | --- | --- |
| **Code ↔ codex correctness** | Adapter parity, error codes, RPC templates, data_type/venue naming SSOT, code↔codex drift | [Checklist](#checklist) items (a)–(n) |
| **Strategy data-coverage** (the operator's data-availability question) | _For each MVP strategy_: honest coverage per data_type × venue/chain (CeFi perp venues **in totality**), over the required history — what's present, what's missing, what needs downloading | [Strategy Data-Coverage Audit](#strategy-data-coverage-audit-data-availability-dimension) items (o)–(v) |

### Archetypes / strategies in scope (operator's words → codebase archetype)

The operator audits these as **"funding rate arb, staked basis carry, basis carry"** plus the price-dispersion MVP. The
canonical archetype files live under `codex/09-strategy/architecture-v2/archetypes/`:

| Operator's name | Canonical archetype | Archetype file | Strategy-engine file |
| --- | --- | --- | --- |
| **staked basis carry** | `carry_staked_basis` | `carry-staked-basis.md` | `strategy-service/.../v2/carry_and_yield/staked_basis.py` |
| **funding rate arb** | `carry_basis_perp` (incl. `funding_rate_dispersion` variant) | `carry-basis-perp.md` | `.../carry_and_yield/basis_perp.py` + `funding_rate_dispersion.py` |
| **basis carry** | `carry_basis_dated` | `carry-basis-dated.md` | `.../carry_and_yield/basis_dated.py` |
| (price-dispersion MVP) | `arbitrage_price_dispersion` | `arbitrage-price-dispersion.md` | (DEX/CEX cross-venue dispersion) |

Inverse / dated variants also exist (`carry-basis-perp-inv.md`, `carry-basis-dated-inv.md`, `carry-staked-basis-dated.md`)
— audit them only when a slot uses them. **DeFi+CeFi hybrid (CRITICAL)**: DeFi = the long/stake/lend leg (on-chain);
the hedge/short leg runs on CeFi perp venues. So a "DeFi" strategy's data coverage spans BOTH `asset_group=defi` (LST
rates, lending indices, DEX, oracle) AND `asset_group=cefi` (perp funding, perp marks) — the coverage audit MUST cover
both legs or it is incomplete.

Key code surfaces:

- LST APR adapters: Lido (stETH), RocketPool (rETH), Coinbase (cbETH), Solana JitoSOL, mSOL
- On-chain rate readers: Aave v3 / Compound v3 base rates
- DEX price feed adapters: Uniswap V3, Curve, Balancer, Sushi, PancakeSwap, Phoenix, Orca, Raydium, Drift
- On-chain execution: `UniswapConnector.swap_exact_input()` via SwapRouter02
- Flash loan: `deployment-service/contracts/FlashLoanReceiver.sol`
- Custody: `CLOUD_KMS_ENCRYPTED` path (May-23); Copper post-June-1
- Pyth oracle: Solana-only on-chain price feeds
- Chain RPC: `CHAIN_RPC_TEMPLATES` in UAC `registry/capability_declarations/_defi.py`
- Error classification: 35 `DefiErrorCode` values in UAC (13 Aave-family + 7 `RECURSIVE_*` + 8 `HL_*` + 2 `ORACLE_*` +
  5 `CCTP_*`; **count the enum, do not trust this number**)

## Triggers

- Weekly (minimum cadence)
- After any DeFi protocol version bump (Aave v4, Uniswap v4, etc.)
- After any new chain or LST is added to the universe
- When `manifest_master` audit surfaces new `empty_confirmed` rows for `asset_group=defi`
- When `batch_live_symmetry_master` audit surfaces adapter parity gaps for DeFi adapters
- **Before any DeFi archetype goes to paper/live** — run the [Strategy Data-Coverage Audit](#strategy-data-coverage-audit-data-availability-dimension)
  first; a strategy cannot paper-trade on a data_type that isn't backfilled over its required history
- After any manifest schema bump (the corpus must be re-checked against the new version per-data_type — code constant ≠
  data state; see incident: 0% of 7.4M rows at v8 despite the constant, 2026-05-20)

## Checklist

- [ ] (a) **35 DefiErrorCode coverage**: all 35 codes (13 Aave-family + 7 `RECURSIVE_*` + 8 `HL_*` + 2 `ORACLE_*` +
      5 `CCTP_*`; **count the enum, don't trust this number** — it grows) present in UAC
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

## Strategy Data-Coverage Audit (data-availability dimension)

> **This is the operator's standing question** ("fresh look at funding rate arb, staked basis carry, basis carry — audit
> instruments-service, MTDS, MDPS, features data available for those strategies and over what timeframe; what's missing,
> what needs downloading"). The items above (a–n) check that the *code* is correct. The items below check that the
> *corpus* is actually present for each strategy to run. **Both must be GREEN before an archetype papers/lives.**
>
> Method per cell: do NOT trust code constants or catalog docs — **read the actual manifest / data-status rows**
> (`asset_group`, `venue`, `data_type`, `schema_version`, min/max `available_at`). Composes with the
> `Data Pipeline Correctness Is The Heartbeat` HARD RULE: every cell is either `captured` over the full required window,
> or `empty_confirmed` with a typed reason, or a **download backlog item** — never a silent gap. No asset_group, no
> venue, no time-range is skipped to hit a date.

### Step 1 — Build the per-strategy data-dependency matrix (the expected set)

For each in-scope archetype, derive the cells it consumes from its archetype file + strategy-engine `Features expected`
list. The matrix is `strategy → data_type → venue(s) → asset_group → producing service → feature → required history`.
This is the **expected coverage** baseline (regenerate from code/codex each run; the snapshot below is the 2026-06-01
reference, not a substitute for reading the source):

**staked basis carry (`carry_staked_basis`)** — DeFi long/stake leg + CeFi hedge leg:

| data_type | venue(s) | asset_group | producing service | feature consumed | required history |
| --- | --- | --- | --- | --- | --- |
| `lst_rates` | LIDO/stETH, ROCKETPOOL/rETH, ETHERFI/weETH, COINBASE/cbETH, JITO/jitoSOL, MARINADE/mSOL (+ ANKR/STADER/SWELL/PUFFER/MANTLE/STAKEWISE as universe grows) | defi | MTDS → features-onchain | `staking_apy_bps`, `lst_native_rate`, `lst_native_rate_ts` | ≥ enough daily snapshots to compute rate-diff APY (≥30d for a stable APY; ≥1y preferred for backtest) |
| `perp_funding` | DRIFT, HYPERLIQUID, GMX (DeFi perps); DERIBIT, BYBIT, BINANCE, OKX (CeFi hedge) | defi + **cefi** | MTDS → features-delta-one | `funding_rate_apy_bps` | full funding-cycle history over backtest window (4–8h cadence) |
| `oracle_prices` | Chainlink (ETHEREUM/ARBITRUM/BASE/OPTIMISM/POLYGON), Pyth (Solana) | defi | MTDS → features-onchain | spot price, health-factor inputs | continuous over window |
| `lending_indices` | AAVE_V3, SPARK, COMPOUND_V3 | defi | MTDS → features-onchain | `usdc_idle_yield_apy_bps` (optional; defaults 0), `health_factor` | window length |

**funding rate arb (`carry_basis_perp` / `funding_rate_dispersion`)** — CeFi-perp-heavy:

| data_type | venue(s) | asset_group | producing service | feature consumed | required history |
| --- | --- | --- | --- | --- | --- |
| `perp_funding` | BINANCE, OKX, BYBIT, DERIBIT, HYPERLIQUID, ASTER, KRAKEN (dispersion needs **all** venues simultaneously) | cefi (+ defi perps) | MTDS → features-delta-one | `funding_rate_annualised_bps` | full funding-cycle history; dispersion needs same timestamps across venues |
| `book_snapshot_5` / derivative_ticker | same perp venues (Tardis) | cefi | MTDS → MDPS → features-delta-one | mark price, index, current funding | window length |
| `trades` (spot leg) | BINANCE/OKX/BYBIT spot; UNISWAP_V3, JUPITER (DEX spot) | cefi + defi | MTDS → MDPS candles | spot fills / slippage sim | window length |
| processed candles `1h`/`4h` | (derived) | per leg | MDPS | `realized_vol_20` (vol-cap clamp) | ≥ vol-lookback window |

**basis carry (`carry_basis_dated`)** — dated future vs spot:

| data_type | venue(s) | asset_group | producing service | feature consumed | required history |
| --- | --- | --- | --- | --- | --- |
| `trades` (spot leg) | DERIBIT (BTC/ETH), CME/Databento (TradFi), UNISWAP_V3 (DEX spot) | defi/cefi/tradfi | MTDS → MDPS | `basis_bps` numerator | window length |
| `trades` (dated future leg) | DERIBIT quarterly, CME/ICE (TradFi) | cefi/tradfi | MTDS → MDPS | `basis_bps` | per-contract life + roll window (`rollover_days_before_expiry`) |
| `ohlcv_1m` / processed candles | Databento pass-through (TradFi), MDPS (crypto) | tradfi/cefi/defi | MTDS/MDPS | basis convergence + `realized_vol_*` | window + roll |

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
> CeFi perp set — Binance/Bybit/OKX/Deribit/Kraken + on-chain perps Hyperliquid/Aster/Pacifica/Lighter/GMX/Drift),
> the DeFi venues in `registry/defi_venues.py` (`ALL_DEFI_VENUES`), and the chain dimension `ChainKind`
> (`canonical/crosscutting/defi.py`, 22 chains). `perp_funding_cadence.py` gives per-venue funding cadence for the
> window check.

### Step 2 — Coverage checklist (compare expected set vs actual corpus)

- [ ] (o) **instruments-service universe present**: every venue × symbol the matrix needs is an active `InstrumentRecord`
      in instruments-service (IS is SSOT for the universe; MTDS derives URLs from it — never hardcoded). For each
      strategy, confirm the LST tokens, perp contracts, dated-future contracts, and DEX pools it trades are listed (not
      phantom / not deprecated). Gap here = MTDS will never attempt the cell → silent `MISSING_EXPECTED` downstream.

- [ ] (p) **Expected-coverage dump regenerated**: materialise the expected `(asset_group, venue, data_type, date)` cell
      set for the in-scope archetypes. Run / adapt: `python3 plans/audit/results/a2_materialize_expected_coverage_dump.py`
      (writes `expected_coverage_dump_<date>.parquet`). This is the denominator for "what's missing".

- [ ] (q) **Manifest divergence for the strategy cells = 0**: run the divergence scan and filter to the matrix cells.
      Run: `python3 plans/audit/results/a3_manifest_divergence.py` (and the all-services variant
      `a3v2_manifest_divergence_all_services.py`). For every `data_type` in the matrix, **zero** `MISSING_EXPECTED` and
      **zero** `DIVERGENT_EMPTY` for `asset_group ∈ {defi, cefi, tradfi}` rows the strategy needs. Each non-zero cell
      becomes a download backlog item (Step 3), NOT a deferral.

- [ ] (r) **Per-data_type schema-version compliance read from DATA (not the constant)**: the manifest is on **v9**
      (`MANIFEST_SCHEMA_VERSION = 9`; v9 added the tradfi `source` column). Read the actual `schema_version` column
      distribution **per data_type** for each strategy's cells — ≥95% at v9. Run / adapt
      `plans/audit/results/a4_manifest_v8_compliance.py` (rename target → v9; the script name still says v8 — that is a
      **stale-tooling finding**, fix it). **Do not trust the code constant** — incident 2026-05-20: 0% of 7.4M prod rows
      were at v8 despite the constant being bumped. A data_type stuck at v4–v7 = a migration backlog item.

- [ ] (s) **Venue + data_type names migrated to SSOT in the actual rows**: the manifest rows' `data_type` and `venue`
      string values use the **canonical** names, not legacy aliases. Canonical data_types: `dex_swaps` / `dex_pool_state`
      / `lending_indices` / `perp_funding` / `lst_rates` / `vault_share_price` / `oracle_prices` (NOT `swap_events` /
      `pool_state` / `lending_metrics` / `funding_rates`). Query the manifest for distinct `data_type` and `venue` values
      for `asset_group=defi` and diff against the catalog + `defi_venues.py` `ALL_DEFI_VENUES`. Any legacy alias still
      appearing in **written rows** (not just code) = an un-migrated-SSOT finding → rename/backfill item. This is the
      per-corpus expression of code items (j)/(l)/(n) above.

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

- [ ] (v) **Honest-coverage totality breakdown — per data_type × venue/chain (THE deliverable)**: do not report a
      single roll-up % per strategy. Produce the full breakdown where **every** expected cell carries one of the
      4-state honest-coverage verdicts read from the manifest — `captured` / `empty_confirmed[reason=<typed>]` /
      `attempted_failed` / `expected_unattempted` — or `MISSING_EXPECTED` if the manifest has no row at all. Two
      breakdowns are mandatory, both enumerated from the SSOTs (no representative subsetting):
      - **Per data_type × venue (in totality)**: for `perp_funding`, enumerate the **complete** CeFi perp venue set from
        `_CEFI` in `expected_coverage.py` (Binance/Bybit/OKX/Deribit/Kraken) **plus** the on-chain perps
        (Hyperliquid/Aster/Pacifica/Lighter/GMX/Drift) — every venue gets a row even if the current strategy only hedges
        on a subset, because funding-dispersion needs the whole set and the operator wants the venue universe assessed in
        totality. Likewise `lst_rates` → every LST venue, `lending_indices` → every lending venue, `dex_swaps`/
        `dex_pool_state` → every DEX, `oracle_prices` → every oracle.
      - **Per data_type × chain**: for chain-scoped data_types (`lst_rates`, `oracle_prices`, `lending_indices`,
        `dex_swaps`, `dex_pool_state`), break coverage down across `ChainKind` (Ethereum, Arbitrum, Base, Optimism,
        Polygon, …, Solana, plus the perp L1s) — a data_type "captured" on Ethereum but absent on Arbitrum/Base is a
        per-chain gap, not a green cell.
      A cell counts as honest-green only when its verdict is `captured` over the required window (item t) at v9 (item r)
      with canonical names (item s). `empty_confirmed` is green **only** when the typed reason is verified against
      `is_before_source_coverage_start()` / `is_in_known_gap()`; an `empty_confirmed` on an owed-data branch is a
      silent-lie finding, not coverage. Everything else is a download/migration backlog row (Step 3).

### Step 3 — Output: the download backlog (what's missing, what to download)

Every RED/AMBER cell from items (o)–(u) becomes an explicit, actionable backlog line — **not** a "deferred" note. Per
the `External Data Is Always Available` + `Data Pipeline Correctness Is The Heartbeat` HARD RULES, a missing cell is one
of exactly:

1. **Download/backfill item** — data exists, just not captured yet → `- [ ] [DATA] P#. Backfill <data_type> for
   <venue> <asset_group> over <start>..<end> — parent_epic: defi_master`. Name the exact venue × data_type × date range
   and the MTDS `collect-*` operation that captures it.
2. **`BLOCKED-CREDENTIALS`** — public/free path exhausted; file the credential ask ping (vendor + tier + what's
   unblocked) per the workspace rule. Adapter scaffold + unit tests still ship; status stays `BLOCKED-CREDENTIALS`, NOT
   `DEFERRED`.
3. **Migration item** — present but wrong `schema_version` (item r) or legacy data_type/venue name (item s) → rename /
   re-version backfill, ideally bundled into the single-walk migration window (no new whole-corpus GCS walk without
   operator ack).
4. **Genuine `empty_confirmed`** — source truly has no data for that cell over that window (verified via
   `is_in_known_gap()` / source-coverage docs) → typed `EmptyConfirmedReason`, recorded, and **excluded** from the
   download backlog (this is the only legitimate "missing").

Render the result as a coverage matrix (rows = strategy × data_type × venue; columns = `expected / captured / v9% /
window-covered / verdict`) plus the download backlog list. Wire each backlog line back into an active plan under
`parent_epic: defi_master` immediately (Capture Discoveries As Plan Todos HARD RULE).

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

## Success Criteria

- All code-correctness checklist items GREEN (incl. code↔codex drift items j–n)
- **All strategy data-coverage items (o)–(v) GREEN** for each in-scope archetype — every matrix cell `captured` over its
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
3. **Honest-coverage totality breakdown (item v)** — TWO tables, every expected cell present (no subsetting):
   (a) **per data_type × venue** with the complete CeFi perp set + on-chain perps + LST/lending/DEX/oracle venues, and
   (b) **per data_type × chain** across `ChainKind` for the chain-scoped data_types. Each cell column set:
   `expected | capture_status (captured/empty_confirmed[reason]/attempted_failed/expected_unattempted/MISSING) | v9% |
   window-covered | verdict`. This is the per-data_type, per-venue/chain answer the operator asked for.
4. **Download backlog**: one `- [ ] [DATA|BLOCKED-CREDENTIALS] P#. <venue × data_type × date-range × collect-op>` line
   per missing/partial/mis-versioned cell, each already wired into an active plan under `parent_epic: defi_master`
5. Gap items: `- [ ] [TYPE] P#. <description> — parent_epic: defi_master` for each RED/AMBER code item
6. Table: `gap item | active plan absorbing it | plan status`
7. Archive condition: "Archives when all gap items below are `- [x]` in their parent plans"

## Linked Results

| Date       | Result file                                                                                                       | Status                                |
| ---------- | ----------------------------------------------------------------------------------------------------------------- | ------------------------------------- |
| 2026-05-27 | [`results/defi_pipeline_code_codex_drift_2026_05_27.md`](../results/defi_pipeline_code_codex_drift_2026_05_27.md) | active (code↔codex drift, items j–n) |
