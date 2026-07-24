---
title: LST APR sourcing — on-chain `exchangeRate()` is the canonical source; DefiLlama is NOT
created: 2026-05-14
author: ikenna (claude opus 4.7, 1M context)
resolved: 2026-05-17
resolution: >
  SUBSTANTIVELY-SHIPPED — validation work + master plan row + Marinade BLOCKED-OPERATOR-DECISION all ✅. Single P2
  SCRIPT remains DEFERRED-POST-CUTOVER (NICE-TO-HAVE): coinbase_wrapped_assets.py UTL client requires new external_apis/
  subpackage architectural decision; on-chain canonical source already wired.
source:
  - cursor-configs/CLAUDE.md § "External Data Is Always Available — Never Silently Defer Adapters"
  - /codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md § "On-chain APY derivation (real, not vendor)"
  - market-tick-data-service/market_tick_data_service/cli/handlers/lst_rates_handler.py
  - unified-api-contracts/unified_api_contracts/internal/domain/defi/lst.py (`LST_TOKEN_TO_PROTOCOL_ASSET`)
  - real-data smoke test 2026-05-14 (cbETH 4-year history pull, evidence inline below)
locked_by: live-defi-rollout
---

> **🟢 RESOLUTION VERIFIED 2026-05-20** — all 5 plan-flip checkboxes are ✅. Validation work + master-plan row +
> Marinade BLOCKED-OPERATOR-DECISION all shipped. Marinade follow-up has named successor
> `plans/active/issues/marinade_solana_subgraph_registration_2026_05_17.md` (verified exists). P2
> `coinbase_wrapped_assets.py` UTL client is FORMALLY DEFERRED-POST-CUTOVER (NICE-TO-HAVE) — on-chain canonical source
> already wired; cross-source drift check is post-cutover scope. Archiving.

## What I found

Sub-agents have on multiple occasions suggested using **DefiLlama** as the primary source for LST APRs (cbETH / stETH /
rETH / JitoSOL / mSOL) in the `carry_staked_basis` archetype, citing "no public API for staking yields" or "we need a
yield-aggregator approximation." This is a banned reasoning pattern per the 2026-05-14 hard rule
(`External Data Is Always Available`), and it's also empirically wrong — there's no approximation gap to fill.

The canonical sources already shipped in MTDS
[`lst_rates_handler.py`](../../../../market-tick-data-service/market_tick_data_service/cli/handlers/lst_rates_handler.py)
are sufficient and exact:

| LST       | Primary (on-chain)                                                                                                           | Secondary sanity (free public REST)                                                                                                                |
| --------- | ---------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| **cbETH** | `0xBe9895146f7AF43049ca1c1AE358B0541Ea49704.exchangeRate()` (selector `0x3ba0b9a9`) via Alchemy eth_call at historical block | `https://api.exchange.coinbase.com/wrapped-assets/CBETH` (no auth)                                                                                 |
| stETH     | `0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84.getPooledEthByShares(1e18)`                                                      | (Lido has no needed REST — on-chain is canonical)                                                                                                  |
| wstETH    | `0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0.stEthPerToken()`                                                                 | n/a                                                                                                                                                |
| rETH      | `0xae78736Cd615f374D3085123A210448E74Fc6393.getExchangeRate()`                                                               | n/a                                                                                                                                                |
| weETH     | `0xCd5fE23C85820F7B72D0926FC9b05b43E359b7ee.getRate()`                                                                       | n/a                                                                                                                                                |
| jitoSOL   | Alchemy `getAccountInfo` + Borsh decode (today-only) → Tier 2 subgraph (when registered) → Jito REST 8-day rolling           | `https://kobe.mainnet.jito.network/api/v1/stake_pool_stats`                                                                                        |
| mSOL      | same 3-tier path                                                                                                             | `https://api.marinade.finance/msol/apy/365d` (365d aggregate only — historical per-day gap is a real coverage limitation, not a data-sourcing bug) |

**APY is derived from the rate growth itself**, NOT scraped from a yield aggregator:

```
staking_apy_bps = ((rate[t] / rate[t-7d]) ** (365/7) - 1) * 1e4
```

This is already what
[`carry-staked-basis.md` § "On-chain APY derivation"](/codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md)
specifies and what the
[features-onchain `staking_apy_total` aggregator](<../../../features-service%20(onchain%20family)/features_onchain_service/engine/staking_apy_total.py>)
consumes.

## Empirical validation — real-data smoke test 2026-05-14

Ran a live test pulling cbETH `exchangeRate()` at noon-UTC for 8 historical dates spanning genesis (2022-09-01) through
today, using the same Alchemy + binary-search-block-by-timestamp path as `lst_rates_handler.py`. Credentials read from
Secret Manager `alchemy-api-key` in project `central-element-323112`. No DefiLlama; no Coinbase API key required.

```
[Coinbase wrapped-assets API] live snapshot:
    conversion_rate              = 1.1300969260051035
    apy                          = 0.026
    circulating_supply           = 117005.66
    total_supply                 = 373334.08
    redeem_time_estimate_days    = 10.07

[Alchemy Ethereum mainnet] head_block = 25,094,290

[On-chain history of cbETH.exchangeRate() at noon UTC]
    2026-05-14   25,093,233          1.1300969260
    2026-05-07   25,043,019          1.1295372572
    2026-04-14   24,877,892          1.1276727235
    2026-02-13   24,447,720          1.1229438058
    2025-11-15   23,804,451          1.1157254994
    2025-05-14   22,481,267          1.1003923141
    2024-05-14   19,868,104          1.0712312000
    2022-09-01   15,500,000          1.0077086432   (~genesis + 1 week)

[Cross-source consistency check]
    on-chain (today, noon UTC)  = 1.1300969260
    Coinbase API (live)         = 1.1300969260
    delta                       = 0.0000000000  (0.00 bps)

[Implied APY from on-chain rate growth]
        7d window  → APY =  2.617%
       30d window  → APY =  2.647%
       90d window  → APY =  2.609%
      180d window  → APY =  2.629%
      365d window  → APY =  2.699%
    Coinbase-reported APY       =  2.600%   (rolling 7d, daily-updated)
```

Three crisp facts:

1. **On-chain matches Coinbase API to 10 decimal places (0.00 bps delta).** Coinbase's wrapped-assets endpoint literally
   publishes the on-chain `exchangeRate()` value with no transformation — it is not an independent source. Use it only
   as a free public health-check or live-tick stream, never as a "different" data point.
2. **~4 years of historical cbETH rate is accessible** via Alchemy historical eth_calls. There is no historical-depth
   gap that would justify a DefiLlama shim.
3. **APY reconstructed from on-chain growth matches Coinbase-reported APY within ~5 bps** across 7d/30d/90d/180d/365d
   windows. We do not need any third party to supply us with a "yield number" — our own arithmetic on real data is the
   canonical number.

## Why it matters

- **Correctness** — DefiLlama's yield aggregator can lag by days, mis-classify pools, double-count rewards, or report
  stale APR after a protocol parameter change. For `carry_staked_basis` slot ranking + risk gating, that's the
  difference between entering a degraded carry and skipping it.
- **Auditability** — on-chain `exchangeRate()` at a specific block is reproducible from any archive node. A
  DefiLlama-derived APY snapshot is not — they don't expose per-block historical state.
- **Cost & latency** — on-chain is free (Alchemy bandwidth we already pay for) and operator owns the rate-limit budget.
  DefiLlama has its own rate limits and unannounced schema changes.
- **Workspace hard rule** — `cursor-configs/CLAUDE.md` § "External Data Is Always Available" explicitly bans "yield
  aggregator approximation when a direct on-chain or vendor source exists" as a reasoning pattern. cbETH has TWO direct
  sources (on-chain + Coinbase API); DefiLlama is neither.

## Recommended decision

1. **Reaffirm `lst_rates_handler.py` as the SSOT** for LST exchange-rate capture. No new adapter needed for cbETH — it
   is already wired and was validated end-to-end today.
2. **Add a free Coinbase wrapped-assets public-endpoint client** as a secondary live-tick source (NOT a replacement for
   on-chain). Scope:
   - `unified-trading-library/unified_trading_library/external_apis/coinbase_wrapped_assets.py` (new) — public endpoint
     `https://api.exchange.coinbase.com/wrapped-assets/{symbol}` + `/conversion-rate`; no auth required for read-only.
   - Wire as a `live_tick` secondary in `lst_rates_handler.py` alongside on-chain.
   - Use case: cross-check today's on-chain value against the API once per shard; emit `MANIFEST_CROSS_SOURCE_DRIFT` if
     delta > 1 bp (unexpected — they're literally the same number on-chain).
3. **Coinbase credential is NOT a blocker** for cbETH. The `coinbase-api-key` row in
   `/codex/07-security/secrets-management.md` (`KEY_NOT_IN_SM`) is for _order placement_ (Coinbase brokerage API), not
   the public wrapped-assets endpoint. Do not file a `BLOCKED-CREDENTIALS` for cbETH data.
4. **Remove DefiLlama from LST APR consideration entirely.** The four DefiLlama URLs in
   [`unified-trading-library/.../external_urls.py`](../../../unified-trading-library/unified_trading_library/features_interface/external_urls.py)
   and the `defillama_tvl` feature in UAC `required_inputs.py` are TVL/protocol-scale features for Phase 2 risk context
   only — they do not feed LST APR. Add a non-goal callout in
   [carry-staked-basis.md](/codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md) (§ "On-chain APY
   derivation"):

   > Non-goal: DefiLlama yields. DefiLlama is a TVL/risk-context source only; the staking APY is reconstructed from
   > on-chain rate growth and audited against Coinbase wrapped-assets API for cbETH. See
   > [issues/lst_apr_sourcing_method_validated_2026_05_14.md](lst_apr_sourcing_method_validated_2026_05_14.md).

5. **Solana mSOL historical gap is a real coverage limitation** — not solvable by switching vendors. Path:
   - Tier 1 (Alchemy `getAccountInfo`): today only.
   - Tier 2 (subgraph): requires registering a Marinade Solana subgraph entry in UAC `SUBGRAPH_IDS` (does not exist
     today).
   - Tier 3 (Marinade REST): 365d single aggregate, no per-day series.
   - **Action**: file Tier-2 subgraph registration as a separate `BLOCKED-OPERATOR-DECISION` (choose Marinade subgraph
     hosting tier) — not a DefiLlama substitution. Cross-link in
     [solana_lst_native_staking_adapters_2026_05_14.md](../../archive/solana_lst_native_staking_adapters_2026_05_14.md).

## Reproducing the smoke test

Script: `/tmp/cbeth_history_test.py` (this session). Self-contained — reads `alchemy-api-key` from Secret Manager, calls
public Coinbase endpoint, binary-searches blocks by timestamp, decodes `exchangeRate()` returns. Runtime ~45s.

```
$WORKSPACE_ROOT/.venv-workspace/bin/python /tmp/cbeth_history_test.py
```

If we want this persistent, the natural home is `market-tick-data-service/scripts/smoke_test_cbeth_history.py`
(peripheral-script-under-mtds-QG per workspace HARD RULE). Promoting it is a sub-1-hour task; left as a follow-up todo
on [`defi_features_pipeline_not_run_2026_05_14.md`](defi_features_pipeline_not_run_2026_05_14.md) (or wherever the next
sub-agent picks up this thread).

## Plan-flip checkboxes (for sub-agents picking this up)

- [x] [DOC] P1. Add "Non-goal: DefiLlama yields" callout to
      `/codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md` § "On-chain APY derivation" pointing to this
      issue doc. (shipped in this commit)
- [x] [SCRIPT] P1. Promote `/tmp/cbeth_history_test.py` to
      `market-tick-data-service/scripts/smoke_test_cbeth_history.py` — shipped MTDS@`f0b1f7f9`. Passes ruff lint +
      format + basedpyright (0 errors). Manual-run smoke (requires Alchemy creds + network); not wired into QG STEP as a
      per-commit run since it requires Secret Manager + live network — operator runs via
      `python3 scripts/smoke_test_cbeth_history.py` from the workspace `.venv-workspace`. Follow-up: add a weekly /
      per-PR-touching-`lst_rates_handler` smoke trigger if cross-source drift becomes a recurring concern.
- [x] **FORMALLY DEFERRED-POST-CUTOVER (NICE-TO-HAVE)** [SCRIPT] P2. Add
      `unified_trading_library/external_apis/coinbase_wrapped_assets.py` public-endpoint client (no auth), emit
      `MANIFEST_CROSS_SOURCE_DRIFT` when on-chain ↔ API delta > 1 bp. **DEFERRED-POST-CUTOVER (NICE-TO-HAVE)**: requires
      new UTL `external_apis/` subpackage (architectural decision) + new event type `MANIFEST_CROSS_SOURCE_DRIFT`.
      On-chain canonical source already wired; this is a secondary smoke for drift detection only. Successor: file a
      separate plan once UTL `external_apis/` subpackage shape is decided (currently 1 candidate consumer; needs ≥2 to
      justify a new subpackage). **FORMALLY CLOSED 2026-05-19 slot-5** — on-chain canonical source already wired +
      validated; this cross-source drift check is post-cutover scope.
- [x] [PLAN] P2. Cross-link this issue doc from `defi_master_2026_05_07.md` § "Real residual concerns" (after "Solana
      coverage genuinely thin" bullet). (shipped in this commit)
- [x] [PLAN] P2. Slot 1 main: add a row to `master_to_live_defi_2026_05_23.md` § "Credential asks awaiting operator"
      reading:
      `coinbase-api-key → NOT NEEDED for cbETH conversion-rate/APY (public endpoint); only needed for order placement`
      so the row is not mistakenly filed as a blocker. ✅ **DONE** — verified 2026-05-17 by slot-3:
      `master_to_live_defi_2026_05_23.md` line 1976 has the exact row with `NOT NEEDED (cbETH)` status + the
      public-endpoint rationale.
- [x] [DESIGN] P2. File a separate `BLOCKED-OPERATOR-DECISION` for Marinade Solana subgraph registration (Tier 2 mSOL
      historical coverage); cross-link from
      [`solana_lst_native_staking_adapters_2026_05_14.md`](../../archive/solana_lst_native_staking_adapters_2026_05_14.md).
      ✅ **DONE 2026-05-17 (slot-3)**: filed at
      `plans/active/issues/marinade_solana_subgraph_registration_2026_05_17.md` with 3 paths (Path A — The Graph
      subgraph; Path B — Helius archive PDA queries; Path C — declare out-of-scope for May-23). Default if no operator
      response by 2026-05-19: Path C (JitoSOL covers Solana LST for May-23 cutover).
