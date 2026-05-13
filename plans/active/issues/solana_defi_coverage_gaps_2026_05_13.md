---
title: "Solana DeFi data coverage gaps — LST + swap + lending + perp + native staking + restaking + oracle prices"
created: 2026-05-13
author: slot-3-ikenna
source:
  - defi_master_2026_05_07
  - defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07
  - bucket_name_ssot_canonicalisation_2026_05_10
severity: P0
locked_by: live-defi-rollout
locked_since: 2026-05-13
---

## What I found

2026-05-13 ~16:50 BST slot 3 audit across UAC registries + instruments-service
adapters + MTDS source + actual manifest capture state. Solana DeFi coverage is
**critically thin** for the May-23 cutover DeFi archetypes (`carry_staked_basis`
needs Solana LST instruments; `arbitrage_price_dispersion` needs Solana perp).

### Naming convention drift surfaces here

TWO parallel naming conventions exist in the defi manifest:

1. **Bare protocol name** (e.g., `MARINADE`, `RAYDIUM`, `ORCA`, `KAMINO`,
   `SOLEND`, `MARGINFI`, `DRIFT`, `JITO`): 29-64 rows each, mostly 100% captured
   but only 1-2 data_types each. Appears to be a thin sample / pre-MVP coverage.
2. **PROTOCOL-SOLANA** (e.g., `MARINADE-SOLANA`, `RAYDIUM-SOLANA`,
   `KAMINO-SOLANA`, `DRIFT-SOLANA`): 22-33k rows each, **0% captured**, 20
   data_types each, dates 2018-01-01 → pre-launch. These are the
   pre-populated rows the enumerator wrote (most just got corrected to
   `empty_confirmed/EXPECTED_PRE_VENUE_LAUNCH` by slot 3 corrector this session
   — see `defi_legacy_blank_reclassification_2026_05_13.md`).

Both naming conventions are live in the manifest simultaneously. Whichever
naming is canonical, the OTHER needs cleanup. **Open question**: which is the
"real" naming target — `MARINADE` or `MARINADE-SOLANA`?

### Coverage matrix (per category)

#### LST (liquid staking) — critical for `carry_staked_basis`

| Venue | UAC | adapter | MTDS | Manifest captured | Data_types captured |
|---|---|---|---|---|---|
| JITO | 🟡 partial (chain_env only) | ❌ none | ✅ ref | 0 of 30 | 0 |
| **JITO-SOLANA** | ❌ no registry | ✅ `jito.py` | ✅ ref | **0 of 33,740** | 0 |
| MARINADE | 🟡 partial | ❌ none | ✅ ref | 30 of 30 (✅) | `lst_rates` (30) |
| **MARINADE-SOLANA** | ❌ no registry | ✅ `marinade.py` | ✅ ref | **0 of 26,180** | 0 |
| BLAZESTAKE / SOLBLAZE | 🟡 partial (env mention) | ✅ `solblaze.py` | ❌ no MTDS | not in manifest | — |
| SANCTUM | ❌ | ❌ | ❌ | not in manifest | — |
| LIDO-SOLANA | ❌ | ❌ | ✅ ref | not in manifest | — |

**Gaps**:

- **SANCTUM** — not wired anywhere. Sanctum is the LST aggregator on Solana (xSOL token + INF + LST router). MAJOR gap for staked-basis archetype which needs LST market access. See <https://app.sanctum.so>.
- **LIDO-SOLANA** (stSOL): historically active 2021-2023, project wound down 2023 — may be intentionally deferred.
- **BLAZESTAKE / SOLBLAZE** (bSOL): adapter exists but no MTDS integration → no data captured.
- **Staked token oracle prices**: no dedicated `staked_token_oracle_prices` data_type captured for JITOSOL / mSOL / bSOL / INF (xSOL). Pyth feeds exist for these (per the 2026-05-06 Pyth unban decision: _"Pyth — UNBANNED 2026-05-06 for Solana on-chain price feeds (Hermes batch + PythNet live)"_) but no captured rows.
- **Native staking rates** (Solana validator commission + epoch rewards): no `native_staking_rates` data_type. Required for staked-basis archetype to compute base SOL yield. Solana Foundation publishes via RPC; Helius / Jito Labs aggregate. **NO ADAPTER EXISTS**.
- **Seasonal rewards accrual**: no data_type for sustained-rewards tracking (e.g., MEV revenue accruing to Jito stakers, MEV from Marinade, Helium staking rewards). Important for accurate carry computation.

#### Swap (AMM) — needed for hedge-leg fills + oracle prices

| Venue | UAC | adapter | MTDS | Manifest captured | Data_types captured |
|---|---|---|---|---|---|
| RAYDIUM | 🟡 partial | ❌ none | ✅ ref | 31 of 31 (✅) | `dex_pools` (31) |
| **RAYDIUM-SOLANA** | ❌ no registry | ✅ `raydium.py` | ✅ ref | **0 of 22,940** | 0 |
| ORCA | 🟡 partial | ❌ none | ✅ ref | 31 of 31 (✅) | `dex_pools` (31) |
| **ORCA-SOLANA** | ❌ no registry | ✅ `orca.py` | ✅ ref | **0 of 22,700** | 0 |
| METEORA | ❌ | ❌ | ❌ | not in manifest | — |
| PHOENIX | ❌ | ❌ | ❌ | not in manifest | — |
| JUPITER | 🟡 partial | ❌ | ❌ | not in manifest | — |
| LIFINITY | ❌ | ❌ | ❌ | not in manifest | — |

**Gaps**:

- **METEORA** (CLMM + DLMM + dynamic AMM): major Solana DEX, no coverage. SOL/USDC routes a lot of volume through Meteora.
- **PHOENIX** (orderbook DEX): high-liquidity orderbook venue; needs `book_snapshot` + `trades`.
- **JUPITER** (aggregator + perps): the routing aggregator that defines real fills. No coverage = no realistic slippage model.
- **LIFINITY** (proactive market maker): smaller TVL but unique design (oracle-priced PMM).
- **dex_swaps** data_type: captured only at the protocol-only level (31 rows each). No per-swap event capture.
- **oracle_prices** data_type for Pyth feeds: needs `pyth_oracle_prices` or `oracle_prices/source=pyth` rows. Pyth was unbanned 2026-05-06 but no captured rows for Solana oracle feeds visible.

#### Lending — needed for borrow legs of `arbitrage_price_dispersion`

| Venue | UAC | adapter | MTDS | Manifest captured | Data_types captured |
|---|---|---|---|---|---|
| KAMINO | 🟡 partial | ❌ none | ✅ ref | 32 of 64 (50%) | `lending_indices` (32) |
| **KAMINO-SOLANA** | ❌ | ✅ `kamino.py` | ✅ ref | **0 of 33,900** | 0 |
| SOLEND | 🟡 partial | ❌ none | ✅ ref | 29 of 29 (✅) | `lending_indices` (29) |
| MARGINFI | 🟡 partial | ❌ none | ✅ ref | 16 of 30 (53%) | `lending_indices` (16) |
| MANGO / MANGO-SOLANA | ❌ | ❌ | ❌ | not in manifest | — |
| JET | ❌ | ❌ | ❌ | not in manifest | — |
| PORT | ❌ | ❌ | ✅ ref | not in manifest | — |
| LARIX | ❌ | ❌ | ❌ | not in manifest | — |

**Gaps**:

- **MANGO** (Mango V4): lending + perps on Solana, no coverage.
- **rate_indices** equivalent: only `lending_indices` captured (the supply/borrow index). Need `borrow_rate`, `supply_rate`, `utilization` time series for proper carry modeling.
- **liquidations** data_type: no captured rows for any Solana lending venue. Liquidation events are critical for risk attribution + downside-tail modeling.
- **position_data**: per-position health / collateral / debt — not captured.

#### Perp DEXes — CRITICAL for `arbitrage_price_dispersion` hedge leg

| Venue | UAC | adapter | MTDS | Manifest captured | Data_types captured |
|---|---|---|---|---|---|
| DRIFT | 🟡 partial | ❌ none | ✅ ref | 0 of 29 | 0 |
| **DRIFT-SOLANA** | ❌ | ✅ `drift.py` | ✅ ref | **0 of 28,340** | 0 |
| MANGO-SOLANA | ❌ | ❌ | ❌ | not in manifest | — |
| ZETA | ❌ | ❌ | ❌ | not in manifest | — |
| FLASH | ❌ | ❌ | ✅ ref | not in manifest | — |

**Gaps**:

- **DRIFT 0% capture** — the lead Solana perp venue, used for SOL-perp hedges
  in `carry_staked_basis`. Adapter exists, MTDS references it, but ZERO captured
  rows. CRITICAL gap.
- **perp_funding** data_type: no captured Solana perp funding rates. Required
  for accurate funding-adjusted carry computation.
- **MANGO V4 perps**: not wired.
- **ZETA** (Solana options + perps): not wired.
- **FLASH** (Solana leveraged trading): MTDS references it but no instruments-service adapter.

#### Restaking + secondary primitives

| Adapter | Purpose | Captured rows |
|---|---|---|
| `jito_restaking.py` | Jito restaking (VRT tokens) | not in manifest (untested) |
| `eigenlayer.py` | EigenLayer (Ethereum) | captured rows under EIGENLAYER (Ethereum) |

**Gaps**:

- **Jito Restaking rewards**: adapter exists but coverage state unverified.
  Need `restaking_rewards` data_type for VRT-issuing protocols (Solayer, Picasso,
  Cambrian).
- **Solayer**, **Picasso**, **Cambrian** (Solana restaking ecosystem): not wired.

## Why it matters

**P0 for May-23 cutover** — the two lead DeFi archetypes both have Solana
dependencies that are currently unmet:

- **`carry_staked_basis`** (lead): needs Solana LST (JitoSOL + mSOL) as margin
  per CLAUDE.md "carry_staked_basis requires LST_AS_MARGIN (...DRIFT/JitoSOL+mSOL)".
  Today: DRIFT 0% captured + JITO-SOLANA 0% captured + MARINADE-SOLANA 0%
  captured. Hedge leg is non-operational.
- **`arbitrage_price_dispersion`**: needs cross-venue price-dispersion data
  including Solana CLOB venues (PHOENIX) + Solana AMM-aggregator routes
  (JUPITER). Today: 0% capture on both.

**Operational risk on cutover day**: the system has the *intent* to trade
on Solana (adapters exist, archetype configs reference Solana venues) but the
*data* required to do so safely is mostly absent.

## What we need (canonical data types — operator-prioritized list per slot 3 read)

1. **Perp funding rates** — `perp_funding` data_type captured per (venue, instrument, hour) for at least DRIFT (lead), MANGO V4 (secondary), JUPITER perps.
2. **Rate indices equivalent** — `borrow_rate` / `supply_rate` / `utilization` per (venue, instrument, day) for KAMINO + SOLEND + MARGINFI + MANGO. Existing `lending_indices` is per-day cumulative; we need the per-block rate series.
3. **Pools** — `dex_pools` per venue per day (TVL, fees collected, reserves, sqrtPrice for CLMM) for RAYDIUM + ORCA + METEORA + PHOENIX + JUPITER + LIFINITY.
4. **Staked token oracle prices** — `staked_token_oracle_prices` (Pyth Hermes batch + PythNet live) for JITOSOL / mSOL / bSOL / INF (xSOL). Sources: Pyth (UNBANNED 2026-05-06 per CLAUDE.md), Switchboard.
5. **Native staking rates** — `native_staking_rates` (per-epoch validator commission + base reward + Helius / Jito aggregated APY). Source: Solana RPC `getInflationRate` + `getValidators` + Helius API.
6. **Restaking rewards with seasonal accrual** — `restaking_rewards` per VRT issuer. Sources: Jito Restaking API + Solayer / Picasso / Cambrian protocol APIs.

## Recommended decision (operator triage)

This is too big for one slot. Recommend splitting into multiple successor plans:

1. **Successor plan A — Solana LST + native staking adapters** (~3-4 slot days):
   - Add SANCTUM (router + INF) adapter
   - Wire BLAZESTAKE / SOLBLAZE MTDS data flow
   - Add `native_staking_rates` adapter (Solana RPC + Helius)
   - Add `staked_token_oracle_prices` adapter (Pyth Hermes for SOL LSTs)
   - Backfill JITO-SOLANA / MARINADE-SOLANA from 2022-08 launch dates
2. **Successor plan B — Solana perp DEX adapters** (~3-4 slot days):
   - Debug DRIFT-SOLANA 0% capture (read events, identify failure)
   - Add MANGO V4 perps adapter
   - Add ZETA + FLASH adapters
   - Backfill `perp_funding` for DRIFT from 2021-11 launch
3. **Successor plan C — Solana AMM coverage expansion** (~2-3 slot days):
   - Add METEORA + PHOENIX + JUPITER + LIFINITY adapters
   - Expand `dex_swaps` capture beyond the 31-row sample
   - Add Pyth oracle price capture for major SOL pairs
4. **Successor plan D — Naming convention reconciliation** (~1 slot day):
   - Operator decision: `MARINADE` vs `MARINADE-SOLANA` canonical naming
   - Migrate the parallel-naming rows to the canonical shape
   - Update DEFI_VENUE_LAUNCH_DATES if needed
5. **Successor plan E — Restaking rewards coverage** (~2 slot days):
   - Test Jito Restaking adapter capture
   - Add Solayer + Picasso + Cambrian adapters

Slot 3 will NOT take these in this session — out of scope (PART B was bucket-name
SSOT). Flagged for slot 1 / operator triage. Each successor plan needs its own
slot assignment + cycle allocation.

## Cross-references

- Related: `defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md` (the venue-eligibility matrix that says Solana venues should work).
- Related: `defi_master_2026_05_07.md` (umbrella for DeFi cutover work).
- Related: `emerging_perp_venue_adapters_broken_2026_05_13.md` (filed in this same session — covers ASTER/EXTENDED/PACIFICA/LIGHTER/HYPERLIQUID failures).
- Related: `defi_legacy_blank_reclassification_2026_05_13.md` (also filed this session — the 599,486 Solana-included corrections to EXPECTED_PRE_VENUE_LAUNCH).

## UPDATE 2026-05-13 ~18:30 BST — refined research (slot 3)

Per operator direction "research all options before assuming things don't exist", deeper grep across the workspace reveals more existing infrastructure than the initial audit captured:

- **SANCTUM**: NOT a phantom name — `_SANCTUM_RULES` exists in `unified-api-contracts/unified_api_contracts/registry/risk_rules/venue.py:318` (risk rule set), so SANCTUM IS recognised in UAC. Just no instruments-service adapter file yet. Adapter implementation is the gap; UAC capability declarations would extend the existing pattern.

- **Pyth Hermes IS wired in MTDS**: `market-tick-data-service/market_tick_data_service/cli/handlers/oracle_prices_handler.py:375,708` has `_fetch_pyth_hermes_latest` calling `https://hermes.pyth.network/v2/updates/price/latest`. Pyth Hermes is the primary source priority for oracle_prices per `unified_api_contracts/canonical/crosscutting/source_priority.py:162,269`. So staked-token oracle price capture is NOT blocked on adapter — it's blocked on:
  1. UAC `staked_token_oracle_prices` (or extending `oracle_prices`) per-instrument config for JITOSOL / mSOL / bSOL / INF (xSOL) feeds.
  2. Actual MTDS batch run scheduling for these feeds.

- **native_staking_apr**: declared in `unified-api-contracts/unified_api_contracts/internal/domain/defi/sim_schemas.py:101-103` (as a schema field on simulation events). So native staking is acknowledged at the schema layer. No CAPTURE adapter — needs Solana RPC + Helius / Jito Labs APIs.

- **strategy_family** SSOT already references _"Solana on-chain oracle depeg (Pyth Hermes), LST tracking-error vs SOL, restaking yields"_ as the target strategy archetype at `unified-api-contracts/unified_api_contracts/canonical/crosscutting/strategy_family.py:72,151`. So the **strategy-design layer expects** these data feeds — but the **adapter/capture layer** hasn't shipped them.

- **`_defi_oracle_coverage.py:12`** references Pyth Hermes archive at `https://hermes.pyth.network/v2/updates/price/{publish_time}` — so historical backfill path is also identified.

### Refined successor-plan scope (per the deeper research)

The 5 successor plans (A-E) in the body above remain the right shape, but with refined entry-points:

- **Plan A (Solana LST + native staking)**: SANCTUM adapter can extend the existing risk-rules pattern (`_SANCTUM_RULES` already in UAC); `staked_token_oracle_prices` may not need a new data_type — could extend `oracle_prices` with per-feed config (JITOSOL/mSOL/bSOL/INF) routed through the already-wired Pyth Hermes path; native_staking adapter needs new code BUT the schema field (`native_staking_apr`) already exists.

- **Plan B (Solana perps)**: DRIFT adapter exists (`instruments-service/.../drift.py`); 0% capture suggests adapter-debug needed, not new code. MANGO V4 / ZETA / FLASH need new adapters.

- **Plan C-E**: scope unchanged.

**Net**: the actual implementation work is smaller than initial issue body suggested. ~5-10 slot-AI-days total across the 5 successor plans (was estimated 12-18). Slot 3 hands off without claiming the implementation.

---

## Pre-audit verification commands (for the slot picking this up)

```bash
# Confirm adapter file existence:
ls instruments-service/instruments_service/reference_data/adapters/defi/

# Confirm factory mapping:
grep -n "SOLANA\|MARINADE\|JITO\|DRIFT\|KAMINO\|SANCTUM" \
    instruments-service/instruments_service/reference_data/factory.py

# Confirm UAC registry coverage:
grep -rn "MARINADE\|JITO\|DRIFT" \
    unified-api-contracts/unified_api_contracts/registry/defi_protocol_registry.py

# Re-run capture audit (slot 3's script):
cat /tmp/audit_solana_defi.py  # in slot-3 worktree
```
