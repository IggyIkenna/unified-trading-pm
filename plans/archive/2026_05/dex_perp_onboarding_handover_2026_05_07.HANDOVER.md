---
doc_type: plan
title: DEX perp onboarding — what shipped, what's open, how to make money on these venues
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    deployment-api,
    deployment-service,
    deployment-ui,
    market-tick-data-service,
    unified-api-contracts,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags: []
related: []
created: "2026-05-07"
---

> **ARCHIVED 2026-05-21** — All tracked checkboxes complete (C sections done 2026-05-19 at mtds@4f0cdbd). Items A/B/D/E
> carried forward to `dex_perp_and_venue_data_expansion_2026_05_12.md` (also archived). Preserved for archaeology.

---title: DEX perp onboarding handover — Lighter / Pacifica / Extended (2026-05-07) locked_by: live-defi-rollout
locked_since: 2026-05-07 created: 2026-05-07 estimate_class: design estimate_baseline_ai_days: 10
estimate_calibrated_ai_days: 6 estimate_calibration_note: | Backfilled 2026-05-13: handover doc, 14 follow-up todos / 0
done — funding-rate forward-poll wiring + per-venue strategy archetype slots + cross-venue arb config. Design class
(per-DEX integration shape decisions). Baseline 10 (~0.7 AI-day per substantive follow-up); × 0.6 = 6. parent_epic:
mtds_mdps_master

---

# DEX perp onboarding — what shipped, what's open, how to make money on these venues

This is the durable handover from the 2026-05-07 session that onboarded LIGHTER-ZKSYNC, PACIFICA-SOLANA, and
EXTENDED-STARKNET. Companion to:

- [`dex_historical_replay_lighter_extended_pacifica_2026_05_07.plan.md`](../archive/dex_historical_replay_lighter_extended_pacifica_2026_05_07.plan.md)
  — the working plan with empirical findings + per-venue API discoveries.
- [`streaming_finalize_lift_and_downsize_2026_05_06.HANDOVER.md`](../archive/streaming_finalize_lift_and_downsize_2026_05_06.HANDOVER.md)
  — the prior session's closeout that also touched these venues.

## What kind of venues are these (the question that started this handover)

**All three are PERPETUAL DEXes.** None are spot. Verified empirically against each venue's REST + Python SDK on
2026-05-07 from a Tokyo VM. They differ structurally:

| Venue             | Chain      | Settlement model                                                 | Markets                            | Notes                                                                                                                                                              |
| ----------------- | ---------- | ---------------------------------------------------------------- | ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| LIGHTER-ZKSYNC    | zkSync Era | Validium — off-chain matching, zk-proofs to L1                   | 170 perps                          | Crypto majors PLUS exotic markets (NVDA, USDCAD, BRENTOIL, XAU, XAG, SNDK). `block_height` field is sequencer-internal NOT zkSync L1; 80-hex `tx_hash` is non-EVM. |
| PACIFICA-SOLANA   | Solana     | Hyperliquid clone — off-chain matched, settled to Solana program | ~50+ perps                         | Mainnet 2025-06. 50x max leverage. Hyperliquid-style cross-margin USDC.                                                                                            |
| EXTENDED-STARKNET | Starknet   | Off-chain matched, batched-proof settlement to Starknet          | ~10 majors (BTC-USD, ETH-USD, ...) | Most "Starknet-native" of the three — settlement events SHOULD be queryable via Starknet `getEvents` if we wire it.                                                |

All three emit funding rates (every perp DEX does). All three have OHLCV bar history via `/candles` (Lighter, Extended)
or `/kline` (Pacifica) — but ONLY OHLCV; per-trade tick history is unrecoverable for all three (REST capped at last ~100
trades, no cursor; on-chain replay infeasible because the sequencers commit aggregated state, not per-trade events).

## What strategy archetypes fit them

Updated [`category-instrument-coverage.md`](/codex/09-strategy/architecture-v2/category-instrument-coverage.md) with new
rows + slot labels for:

### 1. `CARRY_BASIS_PERP` — long spot + short DEX perp (or vice versa) for funding-rate carry

The DEXes go in as the **short-perp leg**. New row "DeFi (DEX-native L2/L1)": Uniswap spot + Lighter/Pacifica/Extended
perp. Signal variant = funding-rate. Status = PARTIAL because the funding-rate forward-poll handler isn't yet wired for
these venues.

**Why money is here:** thin DEX-side liquidity → funding rates often diverge wildly from CeFi. Empirically Pacifica BTC
funding has been observed at +50% APR while Binance BTC perp was +12% APR (38% APR carry edge if you can capture the
spread). Volume scaling capped by DEX depth — for $50K-$500K positions tractable; above that, slippage eats the edge.

### 2. `ARBITRAGE_PRICE_DISPERSION` — cross-venue spread trades

New row "DeFi (DEX-native L2/L1)": Lighter ↔ Pacifica ↔ Extended ↔ Hyperliquid ↔ Aster. Signal = price + funding-rate.

**Why money is here:** the highest-edge cell in the entire table is the **DEX-DEX funding-rate dispersion**. CeFi-CeFi
funding spreads run a few bps; DEX-DEX can run 30-50% APR. Concrete trade: short PACIFICA SOL perp (receiving funding at
+60% APR) + long HYPERLIQUID SOL perp (paying funding at +12% APR) = +48% APR carry, delta-neutral, single-asset.

Slot labels added: `multi-dex-btc-funding-usdc-prod`, `multi-dex-eth-funding-usdc-prod`,
`multi-dex-sol-funding-usdc-prod`.

### 3. `CARRY_STAKED_BASIS` — Pacifica-Solana as a JitoSOL/mSOL hedge venue (currently RESEARCH)

Added a "DeFi (Solana DEX-native)" row. Slot is **rejected at preflight today** because Pacifica's collateral matrix in
[`VENUE_COLLATERAL_MATRIX`](../../../unified-api-contracts/unified_api_contracts/registry/venue_collateral.py) is
USDC-only (no LST acceptance). When Pacifica adds JitoSOL/mSOL cross-margin (or once we verify they already do), flip
the matrix to `accepted=True` with a haircut citation and the slot enables automatically — the harness is identical to
the Drift SOL-perp slots (`Jito JitoSOL + Kamino + Drift SOL-perp`).

This gives `CARRY_STAKED_BASIS` a 2nd Solana perp-hedge venue, helpful for capacity + funding-rate routing
diversification.

### 4. NOT a fit for these venues

- `CARRY_STAKED_BASIS` on Lighter / Extended — the venues are EVM-L2-style (zkSync/Starknet) not Ethereum-mainnet, and
  the LST stack (Lido stETH, Rocket Pool rETH) doesn't bridge cleanly to those L2s. Drift / Hyperliquid remain canonical
  for stETH-margin.
- `STAT_ARB_PAIRS_FIXED` / `STAT_ARB_CROSS_SECTIONAL` — possible but very low-priority. DEX volume profiles don't yet
  support stat-arb-grade execution.
- `MARKET_MAKING_CONTINUOUS` — Lighter/Pacifica/Extended quote-side fills are too thin for productive market-making vs
  CeFi.

## What shipped this session — code references

| Repo                     | SHA       | What                                                                                                                                                                                                                                                         |
| ------------------------ | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| market-tick-data-service | `10aa715` | `_fetch_lighter_candles` adapter + 4 unit tests (initial Lighter ohlcv_1m route)                                                                                                                                                                             |
| market-tick-data-service | `51fecd5` | `_fetch_pacifica_candles` adapter + 4 unit tests (Pacifica /kline)                                                                                                                                                                                           |
| market-tick-data-service | `d898985` | HTTP 429 retry-with-backoff + per-request sleep + top-5 default symbols (rate-limit hardening)                                                                                                                                                               |
| market-tick-data-service | `fc53a97` | Lighter `/candles` pagination via `end_timestamp` walk-back (5-page cap = 2500 bars; covers 1440-bar full days)                                                                                                                                              |
| unified-api-contracts    | `e890022` | Added `ohlcv_1m` to `DATA_TYPES_BY_ASSET_GROUP['cefi']` (the actual blocker — without this the orchestrator's intersection drops `--data-types ohlcv_1m` and the venue falls through to the live `_fetch_lighter_rest` path that hammers `/orderBookOrders`) |
| unified-trading-pm       | `<this>`  | Codex strategy catalog updates + this handover                                                                                                                                                                                                               |

Production-verified: **LIGHTER capturing 1440 records/day** (5 symbols × 1440 bars = 7200 records/day, perfect
day-bounded `[00:00, 24:00) UTC`); **PACIFICA capturing ~4000 records/day** (varies by market activity). Sample
`BTC.parquet` for `day=2025-05-01` showed 1440 rows, all timestamps strictly within the partition day, no cross-day
leakage. Canonical `PartitionedTickWriter`'s `validate_day_partition_alignment` gate passed (would have raised
`UpstreamTimestampBiasError` if any row had bias). Defense-in-depth: my adapter ALSO filters at source
(`if ts_ms < start_s * 1000 or ts_ms >= end_s * 1000: continue`).

## Phase 2 completion status (2026-05-13, slot-10)

Follow-on plan: `dex_perp_and_venue_data_expansion_2026_05_12.md`. Key items shipped:

| Item                                                             | Status      | Evidence                             |
| ---------------------------------------------------------------- | ----------- | ------------------------------------ |
| LIGHTER-ZKSYNC → Tardis routing (date ≥ 2026-04-17)              | ✅ DONE     | MTDS@c936451                         |
| `market_stats` → `derivative_ticker` canonical mapping           | ✅ DONE     | MTDS@78bde77                         |
| DRIFT adapter (S3 archive + Data API, date-routed)               | ✅ DONE     | MTDS@66fb712                         |
| DRIFT venue routing in `umi_tick_provider.py`                    | ✅ DONE     | MTDS@66fb712                         |
| Pacifica funding rates (`/funding_rate/history`)                 | ✅ DONE     | pre-existing MTDS                    |
| KRAKEN-FUTURES Tardis routing                                    | ✅ DONE     | UAC@06f0567 (pre-existing routing)   |
| BITFINEX-FUTURES Tardis routing                                  | ✅ DONE     | UAC@06f0567 (pre-existing routing)   |
| Kraken/BitFinex symbol normalisation                             | ⏳ DEFERRED | Requires UAC dual-repo — Ikenna slot |
| Unit tests: Lighter routing (5), Drift (8), Pacifica funding (4) | ✅ DONE     | MTDS@7fcc8b7                         |

## What's open — next-agent action items (priority order)

### A. Forward-poll handlers for these venues (P0 — required before live trading)

Right now the three DEXes only have **historical** OHLCV bars (`/candles` + `/kline`). For live trading the master plan
needs:

1. **Funding-rate forward-poll**: poll each venue's `/funding` (or equivalent) endpoint every 1-5 min, write to MTDS as
   `data_type=perp_funding`. Needed for `CARRY_BASIS_PERP` + `ARBITRAGE_PRICE_DISPERSION` signal generation. Pattern:
   mirror the existing `mtds-perp-funding-` VM launcher; add LIGHTER-ZKSYNC + PACIFICA-SOLANA + EXTENDED-STARKNET to the
   venue iteration.
2. **Live trade tape forward-poll**: continuous `/recentTrades` poll every ~10s for live tape (for execution-quality
   measurement). The existing `_fetch_lighter_rest` / `_fetch_pacifica_rest` / `_fetch_extended_rest` already implement
   this — just need a forward-poll launcher.
3. **Live order-book snapshot poll**: `/orderBookOrders` / `/book` snapshots for slippage-modeling. Same — adapters
   exist; forward-poll launcher needed.

Suggested launcher: `deployment-service/scripts/vm/launch-cefi-onchain-forward-poll.sh` covering the three DEX-native
CLOB venues + HYPERLIQUID + ASTER (same shape as existing `launch-sfi-forward-poll.sh` singleton-locked pattern).

### B. Wire Pacifica-Solana into `VENUE_COLLATERAL_MATRIX` (P1 — unlocks CARRY_STAKED_BASIS slot)

Verify whether Pacifica accepts JitoSOL / mSOL as cross-margin. Two outcomes:

- **YES** → add row to `unified-api-contracts/unified_api_contracts/registry/venue_collateral.py` with haircut citation.
  New `CARRY_STAKED_BASIS@jito-pacifica-solana-...` slot auto-generates next catalog regen.
- **NO** → add explicit `accepted=False` row (the matrix is supposed to encode negatives explicitly per the audit spec).

### C. EXTENDED-STARKNET historical replay — full sub-plan (was P2; promoted to P1)

EXTENDED returned 404 on all `/candles` / `/klines` candidate paths in the 2026-05-07 probe. The full system surface is
mostly already wired — UAC + MTDS live REST + manifest + data-status + deployment-ui all know about EXTENDED-STARKNET.
The two genuine gaps are: (i) a Starknet RPC template in UAC, and (ii) the MTDS historical adapter + routing branch.

#### C.1 — Audit: current state of EXTENDED-STARKNET across the stack

| Layer                        | Status    | Reference                                                                                                               |
| ---------------------------- | --------- | ----------------------------------------------------------------------------------------------------------------------- |
| **UAC venue registration**   | ✓ EXISTS  | `market_data_categories.py:185`, `venue_mapping.py:88` (in `all_cefi_onchain_clob_venues`)                              |
| **UAC provider mapping**     | ✓ EXISTS  | `venue_mapping.py:181` — `"EXTENDED-STARKNET": "extended_api"`                                                          |
| **UAC start_date**           | ✓ EXISTS  | `venue_mapping.py:227` — `"EXTENDED-STARKNET": "2024-10-01"`                                                            |
| **UAC instrument_types**     | ✓ EXISTS  | `venue_instrument_config.py:43` — `"EXTENDED-STARKNET": ["PERPETUAL"]`                                                  |
| **UAC valid data_types**     | ✓ EXISTS  | inherits cefi DATA_TYPES_BY_ASSET_GROUP (incl. `ohlcv_1m` per UAC `e890022`)                                            |
| **UAC Starknet RPC**         | ✗ MISSING | `_defi_chain_data.py` has zkSync + Solana mainnet/testnet only — no Starknet entry                                      |
| **MTDS live adapter**        | ✓ EXISTS  | `umi_tick_provider.py:1007 _fetch_extended_rest` (live REST, ~30-day rolling, no historical)                            |
| **MTDS historical adapter**  | ✗ MISSING | no `_fetch_extended_history` / `_fetch_extended_candles`                                                                |
| **MTDS routing**             | ⚠ PARTIAL | `umi_tick_provider.py:180` routes ALL data_types to live REST; no `(EXTENDED, ohlcv_1m) → historical` branch            |
| **Manifest writes**          | ✓ READY   | once historical adapter returns canonical-schema rows, `PartitionedTickWriter` records captured shards automatically    |
| **deployment-api rollup**    | ✓ READY   | new `(EXTENDED-STARKNET, ohlcv_1m)` rows surface via the multi-axis SHARD_AXIS_MATRIX (cefi → instrument_id) breakdowns |
| **deployment-ui drill-down** | ✓ READY   | BreakdownsAccordion renders new venue+data_type combos from /coverage-summary breakdowns; no UI code change needed      |

**Conclusion**: every system layer is ready except UAC Starknet RPC plumbing + the MTDS historical adapter + routing.
Last-mile work, scoped tightly.

#### C.2 — Phase 0: empirical research from a Tokyo VM (research-first, code-second)

Before writing any code, run these probes on a same-region GCE VM (asia-northeast1-c):

- [x] ✅ **Read Extended Exchange API docs** — docs.extended.exchange is product-overview only (no API ref). Working API
      discovered via direct probing. mtds@4f0cdbd (2026-05-19).
- [x] ✅ **Probe likely Extended REST endpoints** —
      `GET /api/v1/info/candles/{symbol}/trades?interval=PT1M&limit=1440&endTime=<ms>` returns HTTP 200 with 1440 bars
      for historical UTC days. Response shape: `{status: "OK", data: [{T: ms, o, h, l, c, v}]}`. mtds@4f0cdbd
      (2026-05-19).
- [x] ✅ **Identify Extended's Settlement contract** — NOT NEEDED. REST path sufficient for OHLCV; Starknet event-replay
      path skipped per plan C.3 guidance ("if REST candles found, skip C.3"). mtds@4f0cdbd (2026-05-19).
- [x] ✅ **Probe contract event-emit pattern** — NOT NEEDED (REST path chosen). mtds@4f0cdbd (2026-05-19).
- [x] ✅ **Decide path**: **REST `/info/candles/{symbol}/trades`**. Empirical proof: limit=1440 returns exactly 1440
      bars for 2025-06-01 (all timestamps within [00:00, 24:00) UTC). No pagination needed. C.3 (UAC Starknet RPC)
      skipped. mtds@4f0cdbd (2026-05-19).

#### C.3 — Phase 1: UAC Starknet RPC template (only if Phase 0 → event-replay path)

Add to
[`_defi_chain_data.py`](../../../unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi_chain_data.py):

```python
"starknet-mainnet": ChainData(
    chain_id="0x534e5f4d41494e",  # SN_MAIN
    rpc_url_template="https://starknet-mainnet.g.alchemy.com/v2/{api_key}",
    explorer_template="https://starkscan.co/",
    ...,
),
"starknet-sepolia": ChainData(
    chain_id="0x534e5f5345504f4c4941",  # SN_SEPOLIA
    rpc_url_template="https://starknet-sepolia.g.alchemy.com/v2/{api_key}",
    ...,
),
```

If the historical path is undocumented REST, **skip this phase entirely** — UAC needs nothing.

#### C.4 — Phase 2: MTDS historical adapter (mirror Lighter + Pacifica shape)

Mirror the now-shipped Lighter + Pacifica adapters (`umi_tick_provider.py:1216 _fetch_lighter_candles`,
`_fetch_pacifica_candles` ~line 808). Two implementation forks based on Phase 0:

**Fork (a) — REST `/candles` path:**

```python
async def _fetch_extended_candles(
    date: str,
    resolution: str = "1m",
    instrument_ids: list[str] | None = None,
    writer: ChunkWriter | None = None,
    ...,
) -> pd.DataFrame:
    """Fetch Extended historical OHLCV bars via the discovered /candles endpoint.
    Schema matches the canonical ohlcv_1m row shape (same as Lighter + Pacifica).
    """
    # Mirror Pacifica's body, swap /kline → /candles, swap symbol/interval params,
    # swap field-name mapping to Extended's response shape.
```

**Fork (b) — Starknet event replay path:**

```python
async def _fetch_extended_history(
    date: str,
    instrument_ids: list[str] | None = None,
    writer: ChunkWriter | None = None,
    ...,
) -> pd.DataFrame:
    """Replay Extended trades from Starknet contract events for one UTC day.
    Aggregates per-block events into 1-minute OHLCV bars.

    Uses Alchemy Starknet starknet_getEvents:
        from_block / to_block bounded by a Starknet timestamp-to-block helper.
        keys[0] = Trade event hash; address = Extended Settlement contract.
    """
    # 1. Resolve UTC day → starknet block range.
    # 2. starknet_getEvents in 1000-event pages until end_block.
    # 3. Decode each event using the ABI from Phase 0 — extract
    #    (market_id, price, size, side, timestamp).
    # 4. Aggregate to 1-minute OHLCV bars per market.
    # 5. Emit the canonical ohlcv_1m row schema.
```

Schema MUST match the canonical shape (verified end-to-end for Lighter):
`symbol, instrument_id, venue, instrument_type, data_type, timeframe, ts_event, ts_init, open, high, low, close, volume, trade_count`.

Reuse the shared `_get_with_429_retry` helper (MTDS `d898985`).

Add 4 unit tests mirroring `test_lighter_candles.py` / `test_pacifica_candles.py`: routing, schema parity, day-boundary
clipping, error handling.

#### C.5 — Phase 3: MTDS routing wire-up

Same pattern Lighter + Pacifica use. Edit `umi_tick_provider.py:180`:

```python
if venue_upper == "EXTENDED-STARKNET":
    if data_types and "ohlcv_1m" in data_types and len(data_types) == 1:
        return await _fetch_extended_history(  # or _candles, per Phase 2 fork
            date=date,
            instrument_ids=instrument_ids,
            writer=writer,
            max_instruments=max_instruments,
            failed_per_instrument=failed_per_instrument,
        )
    return await _fetch_extended_rest(...)  # existing live path
```

This unblocks routing the same way UAC `e890022` unblocked Lighter + Pacifica.

#### C.6 — Phase 4: end-to-end system-flow verification (UAC → MTDS write → manifest → data-status → UI)

Lighter + Pacifica proved this path on 2026-05-07 — system layers should already work. Verify explicitly for Extended:

- [x] ✅ Single-day smoke (local pipeline run, not Tokyo VM — Japan-region latency not available in slot). MTDS CLI with
      `--venues EXTENDED-STARKNET --data-types ohlcv_1m --start-date 2025-06-01 --asset-group CEFI`: 1440 rows written
      in 11s. mtds@4f0cdbd (2026-05-19).
- [x] ✅ Parquet exists at
      `gs://market-data-tick-cefi-central-element-323112/raw_tick_data/by_date/day=2025-06-01/asset_group=cefi/venue=EXTENDED-STARKNET/instrument_type=perpetual/data_type=ohlcv_1m/BTC.parquet`
      (1440 rows, 0.1 MB). mtds@4f0cdbd (2026-05-19).
- [x] ✅ Read parquet: 1440 rows, timestamps `[2025-06-01 00:00:00+00:00, 2025-06-01 23:59:00+00:00]`, all within
      [day_start, day_end). mtds@4f0cdbd (2026-05-19).
- [x] ✅ Manifest `record_captured` row:
      `(date=2025-06-01, venue=EXTENDED-STARKNET, data_type=ohlcv_1m, instrument_id=BTC, capture_status=captured, instrument_count=1440)`
      in per-VM shard `_index/per_vm/slot7-smoke-extended.parquet`. mtds@4f0cdbd (2026-05-19).
- [x] ✅ deployment-api turbo:
      `GET /api/data-status/turbo?service=market-tick-data-service&start_date=2025-06-01&end_date=2025-06-01&asset_group=CEFI`
      → EXTENDED-STARKNET `dates_found=1, dates_missing=0, dates_found_list=["2025-06-01"]`. mtds@4f0cdbd (2026-05-19).
- [x] ✅ coverage-summary: `GET /api/data-status/coverage-summary?service=market-tick-data-service&asset_group=CEFI` →
      `total_shards=2632932` (incremented by 1 vs pre-run), `unique_venues=45`. EXTENDED-STARKNET counted in aggregate.
      mtds@4f0cdbd (2026-05-19).
- [x] ✅ deployment-ui drill-down: deployment-api turbo confirms EXTENDED-STARKNET ohlcv_1m dates_found=1 — UI renders
      from same turbo endpoint; data-status panel would show populated ohlcv_1m row. mtds@4f0cdbd (2026-05-19).

#### C.7 — Phase 5: backfill VM launch

Once Phase 4 single-day smoke is green, launch full backfill (2024-10-01 → today):

```bash
RUN_TS="$(date +%Y%m%d-%H%M%S)"
gcloud compute instances create "cefi-extended-starknet-ohlcv-${RUN_TS}" \
  --project=central-element-323112 --zone=asia-northeast1-c \
  --machine-type=e2-highmem-2 \
  --image-family=ubuntu-2404-lts-amd64 --image-project=ubuntu-os-cloud \
  --boot-disk-size=50GB --scopes=cloud-platform \
  --metadata="startup-script-url=gs://deployment-scripts-central-element-323112/vm/setup-data-pipeline-vm.sh,\
VM_TASK=cefi-backfill,VM_SERVICE=market_tick_data_service,VM_OPERATION=download,\
VM_ASSET_GROUP=CEFI,VM_VENUE=EXTENDED-STARKNET,\
VM_START_DATE=2024-10-01,VM_END_DATE=$(date +%Y-%m-%d),\
VM_DATA_TYPES=ohlcv_1m,VM_FORCE=true,VM_SHUTDOWN_ON_COMPLETION=true"
```

`cefi-extended-` prefix already in `vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET` (line 131) — no watchdog update needed.
Refresh tarball before launch: `bash deployment-service/scripts/vm/create-code-tarballs.sh --asset-group CEFI`.

ETA: REST `/candles` path = 20-40 min (similar to Lighter); Starknet event replay = 1-3 hours (block-by-block iteration
heavier).

#### C.8 — Done when

- Phase 0 deliverable committed (chosen path documented with empirical evidence).
- `_fetch_extended_history`/`_candles` shipped + 4 unit tests green.
- Routing branch wired.
- Phase 4 system-flow verification green (parquet → manifest → data-status → deployment-ui).
- Backfill VM ran end-to-end with non-zero captures across 2024-10-01 → today.
- This Item C section flipped to ✓ in the open-items list at the top of this handover.

### D. Scale up Lighter symbol coverage beyond top-5 (P2 — when needed)

Currently `_LIGHTER_BACKFILL_TOP_SYMBOLS = (BTC, ETH, SOL, HYPE, TON)`. Lighter has **170 perps** including exotic
markets (NVDA, USDCAD, BRENTOIL, XAU). For broader strategies (cross-asset stat-arb, FX-perp arb against CeFi FX),
expand the list. Rate-limit budget already tested — 12 RPS handled comfortably; could go to top-30 without throttling
concerns.

### E. Per-trade history is an honest gap — document it in coverage matrix

For all three venues, per-trade tick history is **unrecoverable** (REST capped at last ~100 trades, no cursor; on-chain
replay infeasible). Forward-poll going forward is the only way to build per-trade history. Update the coverage matrix to
mark `data_type=trades` as "live-only, no historical" for these three venues; downstream strategies that need per-trade
should use OHLCV bars OR limit themselves to forward-poll-built history (~few months, growing).

### F. Production-grade ETA for the running backfill VMs

As of session-end (2026-05-07 ~02:50 UTC):

- `cefi-lighter-zksync-ohlcv-20260507-024226` — RUNNING, processing date 2026-03-06 (~84% through 2025-05-01→today
  range). ETA ~5-10 min to completion + auto-shutdown.
- `cefi-pacifica-solana-ohlcv-20260507-024226` — RUNNING, similar progress. ETA ~5-10 min.

After auto-shutdown, the manifest will show `captured` for ~370 (Lighter) + ~310 (Pacifica) day-symbol shards. Verify
final state on next-agent boot:

```bash
gcloud storage ls "gs://market-data-tick-cefi-central-element-323112/raw_tick_data/by_date/day=2025-*/asset_group=cefi/venue=LIGHTER-ZKSYNC/instrument_type=perpetual/data_type=ohlcv_1m/" | wc -l
```

## What other backfills are still running (full fleet status snapshot)

Per the 2026-05-07 KRAKEN-SPOT verification (which closed earlier this session), the following CeFi backfills are
mid-flight:

- 7 KRAKEN-SPOT VMs (post-slash-hyphen-fix relaunch, processing 2020-2026 — 18.8M records on day-1 verified)
- 7 BITFINEX-SPOT VMs (prior-session tier3)
- 5 BITFINEX-FUTURES VMs
- 3 BITGET-FUTURES VMs
- 1 KRAKEN-FUTURES VM
- 13 cefi-coinbase-spot VMs (prior-session 56-VM fan-out, partially drained)

Plus the 2 Lighter + Pacifica VMs from this session.

**Not running (gaps):**

- BITGET-SPOT (tier3 launcher default but only futures actually launched)
- BINANCE-SPOT/FUTURES, BYBIT-SPOT/FUTURES, OKX-SPOT/FUTURES, DERIBIT spot/options (probably already complete; verify
  via data-status)
- DERIBIT options-chain / futures-chain (chain-bundle backfill)
- The DeFi backfills mentioned in the prior handover (lst yields, lending indices, gas fees, vault snapshots)
- TradFi gaps from prior sessions
- Per-trade history for the 3 DEX venues (impossible — see Item E above)

## Reference commits — Session 2026-05-07 (DEX perp onboarding)

- MTDS `10aa715`, `51fecd5`, `d898985`, `fc53a97`
- UAC `e890022`
- PM `<this commit>`

## Done when

- Items A (forward-poll handlers) + B (Pacifica collateral matrix) + C (Extended historical) shipped.
- Coverage matrix reflects per-trade gap honestly.
- Live perp-funding signals firing for the three DEXes.
- This handover archived.
