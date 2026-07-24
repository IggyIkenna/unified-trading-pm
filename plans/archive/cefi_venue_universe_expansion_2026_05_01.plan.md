---
doc_type: plan
title:
  CeFi venue universe expansion — Bitfinex/Bitget/Kraken (Tardis) + Extended/Pacifica/Lighter (DEX perp adapters) +
  Opinion.trade (prediction)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-01
priority: P1
owner: agent
type: feature
epic: cefi-data-pipeline
locked_by: live-defi-rollout
locked_since: 2026-05-01
completion_gates: { code: C2, deployment: D2, business: B2 }
repo_gates:
  - { repo: unified-api-contracts, deployment: D0 }
  - { repo: market-tick-data-service, deployment: D1 }
  - { repo: deployment-service, deployment: D2 }
depends_on: []
isProject: false
---

## Deferred work — migrated to: `plans/active/cefi_consolidated_closeout_2026_07_18.md` — successor:

cefi_consolidated_closeout_2026_07_18 (all 20 open items — Phase 1 UAC/MTDS/launcher wiring + backfill for
BITFINEX/BITGET/KRAKEN, Phase 2 DEX-perp adapters for EXTENDED/PACIFICA/LIGHTER — are CONFIRMED SHIPPED per direct grep
of the current CeFi umbrella plan, which discusses canonical-id coverage for all six venues at length (KRAKEN-FUTURES
`FI_/FF_` reconstruct, BITFINEX-FUTURES canonicalisation, BITGET-FUTURES letter-month decode, EXTENDED-STARKNET
marker-less ids, and a live backfill launch command naming `KRAKEN-FUTURES BITFINEX-FUTURES BITGET-FUTURES` explicitly).
The venues exist and are actively being data-quality-hardened in this plan — this archived plan's remaining scope (Phase
3 Opinion.trade was explicitly out-of-scope/deferred-to-a-separate-plan in the body already) is superseded by the
ongoing canonicalisation work there. Verified via grep, not a guess.

## Context

7 venues missing from our universe per the 2026-05-01 audit:

| Venue         | Class                | Integration cost          | Notes                                                                              |
| ------------- | -------------------- | ------------------------- | ---------------------------------------------------------------------------------- |
| Bitfinex      | CeFi spot+derivs     | LOW (Tardis)              | Tardis Machine name `bitfinex` — already supported                                 |
| Bitget        | CeFi spot+perps      | LOW (Tardis)              | Tardis Machine name `bitget` (also `bitget-futures`)                               |
| Kraken        | CeFi spot+derivs     | LOW (Tardis)              | Tardis name `kraken` (spot) + `kraken-futures` (derivs)                            |
| Extended      | DEX perp (Solana)    | MED (custom REST adapter) | hyperliquid-style orderbook; no Tardis support                                     |
| Pacifica      | DEX perp (Solana)    | MED (custom REST adapter) | hyperliquid clone; possibly S3 archive                                             |
| Lighter       | DEX perp (zkSync L2) | MED (custom REST adapter) | dYdX-class L2 perp                                                                 |
| Opinion.trade | Prediction market    | HIGH (custom)             | Indian-market platform (cricket/sports/elections); separate from Polymarket/Kalshi |

Phase 1 ships immediately (Tardis additions are pure data — no adapter code). Phase 2 ships DEX-perp adapters following
the existing Hyperliquid + Aster pattern in
[umi_tick_provider.py](../../../market-tick-data-service/market_tick_data_service/adapters/umi_tick_provider.py). Phase
3 (Opinion.trade) is gated on a research spike — its API surface and market schema differ enough from Polymarket/Kalshi
to warrant a dedicated plan.

Manifest data-status integration: each new venue gets a row in UAC `VENUES_BY_ASSET_GROUP['cefi']` (or `prediction` for
Opinion.trade) plus a `coverage_starts.py` entry. The data-status check loops `VENUES_BY_ASSET_GROUP` so adding the
venue automatically extends expected-coverage denominators. No changes needed to the data-status check itself.

## Phase 1 — Tardis venues (Bitfinex / Bitget / Kraken)

### UAC additions (`unified-api-contracts`)

- [ ] [AGENT] P0. `unified_api_contracts/registry/venue_mapping.py` — extend `all_tardis_exchanges` with `bitfinex`,
      `bitget`, `bitget-futures`, `kraken`, `kraken-futures`. Extend `tardis_to_venue` map: `bitfinex → BITFINEX-SPOT`,
      `bitget → BITGET-SPOT`, `bitget-futures → BITGET-FUTURES`, `kraken → KRAKEN-SPOT`,
      `kraken-futures → KRAKEN-FUTURES`.
- [ ] [AGENT] P0. `unified_api_contracts/registry/market_data_categories.py` — extend `VENUES_BY_ASSET_GROUP['cefi']`
      with `BITFINEX-SPOT`, `BITGET-SPOT`, `BITGET-FUTURES`, `KRAKEN-SPOT`, `KRAKEN-FUTURES`. Update
      `VENUE_TO_ASSET_GROUP` reverse map.
- [ ] [AGENT] P0. `unified_api_contracts/canonical/coverage_starts.py` — add launch dates: `BITFINEX 2013-04-15`,
      `BITGET 2018-07-30`, `KRAKEN 2011-07-28`.
- [ ] [AGENT] P0. `unified_api_contracts/registry/capability_declarations/_cefi.py` — add SourceCapability declarations
      (or auto-extend if Tardis venues share a template). Symbology conventions: Bitfinex uses `tBTCUSD` /
      `tBTCF0:USTF0`; Bitget uses `BTCUSDT` / `BTCUSDT_UMCBL`; Kraken uses `XBT/USD` (spot, lowercase) / `PI_XBTUSD`
      (futures).
- [ ] [AGENT] P0.
      `cd unified-api-contracts && bash scripts/quality-gates.sh && bash scripts/quickmerge.sh "feat: add Bitfinex/Bitget/Kraken to CeFi venue universe (Tardis-supported)" --agent`.

### MTDS adapter routing (`market-tick-data-service`)

- [ ] [AGENT] P0. `market_tick_data_service/adapters/umi_tick_provider.py` — update `_TARDIS_CEFI_VENUES` (the
      `frozenset(_VM.tardis_to_venue.values())` derivation already handles this, no manual edit needed once UAC ships).
- [ ] [AGENT] P0. Add coverage_start clipping per-venue in adapter pre-fetch (the existing pattern via
      `unified_api_contracts.coverage_starts` should already cover; verify with a smoke).
- [ ] [AGENT] P0.
      `cd market-tick-data-service && bash scripts/quality-gates.sh && bash scripts/quickmerge.sh "feat: route Bitfinex/Bitget/Kraken via Tardis adapter" --agent`.

### Launcher (`deployment-service`)

- [ ] [AGENT] P0. `scripts/vm/launch-cefi-sharded-backfill.sh` — add symbol lists:
  - `SYMBOLS_BITFINEX_SPOT="tBTCUSD;tETHUSD;tSOLUSD;tXRPUSD;tDOGEUSD;tADAUSD;tAVAXUSD;tLINKUSD"` (Bitfinex `t` prefix
    for spot)
  - `SYMBOLS_BITGET_SPOT="BTCUSDT;ETHUSDT;SOLUSDT;XRPUSDT;BNBUSDT;DOGEUSDT;ADAUSDT;AVAXUSDT;LINKUSDT"`
  - `SYMBOLS_BITGET_FUTURES="BTCUSDT_UMCBL;ETHUSDT_UMCBL;SOLUSDT_UMCBL;XRPUSDT_UMCBL;BNBUSDT_UMCBL;DOGEUSDT_UMCBL;ADAUSDT_UMCBL;AVAXUSDT_UMCBL;LINKUSDT_UMCBL"`
    (Bitget USDT-margined perps)
  - `SYMBOLS_KRAKEN_SPOT="XBT/USD;ETH/USD;SOL/USD;XRP/USD;DOGE/USD;ADA/USD;AVAX/USD;LINK/USD"` (Kraken slash convention;
    XBT not BTC)
  - `SYMBOLS_KRAKEN_FUTURES="PI_XBTUSD;PI_ETHUSD;PI_SOLUSD;PI_XRPUSD;PI_DOGEUSD;PI_ADAUSD;PI_AVAXUSD;PI_LINKUSD"`
    (Kraken Futures perpetual `PI_` prefix)
- [ ] [AGENT] P0. Add `launch_cefi_shard` calls for each new venue × heavy/light × year-shard (2020..today).
- [ ] [AGENT] P0. `bash scripts/vm/create-code-tarballs.sh --asset-group CEFI` then
      `bash launch-cefi-sharded-backfill.sh` (will pick up new venues from launcher list).

### Verification

- [ ] [AGENT] P0. After 2-4h: query manifest for new venues; confirm `captured` rows for spot + futures.
- [ ] [AGENT] P0. Sanity-check parquets at
      `gs://market-data-tick-cefi-{pid}/raw_tick_data/by_date/day=*/asset_group=cefi/venue={BITFINEX-SPOT|BITGET-FUTURES|KRAKEN-SPOT|...}/`.

## Phase 2 — DEX perp adapters (Extended / Pacifica / Lighter)

### Common pattern (mirror Hyperliquid + Aster in `umi_tick_provider.py`)

Each DEX perp gets:

1. **REST adapter function** in `umi_tick_provider.py` (e.g. `_fetch_extended_rest`, `_fetch_pacifica_rest`,
   `_fetch_lighter_rest`). Hyperliquid uses S3 archive + REST; Aster is REST-only via Binance-Futures-compatible API.
   Choose pattern per venue:
   - **Extended**: REST-only (no public S3 archive). Endpoints: `GET /api/v1/markets`, `GET /api/v1/orderbook`,
     `GET /api/v1/trades`. Solana on-chain for settlement.
   - **Pacifica**: REST-only. `https://api.pacifica.fi/api/v1/...`. Solana.
   - **Lighter**: REST + WS. `https://mainnet.zklighter.elliot.ai/api/...`. zkSync Era.
2. **UAC declaration** in `VENUES_BY_ASSET_GROUP['cefi']` (DEX perps land under cefi alongside Hyperliquid/Aster, not
   defi — they're orderbook venues, not AMM pools).
3. **Chain metadata** in UAC (Solana for Extended/Pacifica; zkSync for Lighter).
4. **Symbol convention** per venue (BTC, ETH for hyperliquid-style; verify per docs).
5. **Launcher entry** in `launch-cefi-sharded-backfill.sh`.

### Per-venue todos

- [ ] [AGENT] P0. **Extended** — UAC: `VENUES_BY_ASSET_GROUP['cefi'] += ['EXTENDED']`. Adapter: `_fetch_extended_rest`
      in `umi_tick_provider.py` (mirror `_fetch_hyperliquid_s3` + Aster patterns; pull trades + book snapshots via
      REST). Symbols: `BTC;ETH;SOL;HYPE;...` (per Extended's market list). Launch dates: ~2024-08-01 (verify).
- [ ] [AGENT] P0. **Pacifica** — UAC: `+= ['PACIFICA']`. Adapter: `_fetch_pacifica_rest`. Hyperliquid clone — schema
      near-identical. Symbols: `BTC;ETH;SOL;...`.
- [ ] [AGENT] P0. **Lighter** — UAC: `+= ['LIGHTER']`. Adapter: `_fetch_lighter_rest`. zkSync L2; different RPC stack.
      Symbols per Lighter's market list.
- [ ] [AGENT] P0. Update `_DATABENTO_VENUES` / `_TARDIS_CEFI_VENUES` / DEX-perp set in `umi_tick_provider.py` so the
      dispatch routes correctly.
- [ ] [AGENT] P0. Each adapter must: (a) implement `record_empty(row_key=...)` for empty source responses, (b) call
      `classify_venue_error()` on exceptions, (c) emit `ADAPTER_FETCH_FAILED` events per
      `/codex/04-architecture/shard-level-failure-isolation.md`.
- [ ] [AGENT] P0. Quality gates + quickmerge.

### Backfill

- [ ] [AGENT] P0. Refresh CEFI tarball → launch backfill VMs per venue × year-shard.

## Phase 3 — Opinion.trade (deferred)

Opinion.trade is an Indian prediction-market platform (cricket, sports, elections, Bollywood). Schema:

- Markets are binary YES/NO outcome contracts
- Volume + outcome resolution may not match Polymarket's CTF / Kalshi's CFTC-regulated format
- API surface unverified (likely REST + WS)

Spike: 1 day to confirm API + schema, then either reuse `base_prediction_adapter.py` or build dedicated. Out of scope
for this plan; file a separate plan post-spike.

## Manifest data-status integration

The data-status check (`deployment-service/cli/utils/data_status_*.py`) loops `VENUES_BY_ASSET_GROUP['cefi']` and
`['prediction']` to build expected-coverage denominators. **Adding a venue to UAC automatically extends the data-status
denominators — no code change needed.** Coverage_starts.py entries clip pre-launch dates so new venues don't show 0% for
early years.

The phantom-recon script (`reconcile_phantom_manifest_rows.py`) follows the same SSOT and will scan new venues' manifest
rows automatically.

The vm-zombie-watchdog (deployed 2026-05-01, `vm_zombie_watchdog.py`) covers any new VM that follows the existing prefix
conventions (`cefi-bitfinex-*`, `cefi-bitget-*`, `cefi-extended-*`, etc.). Add the prefix → cefi-bucket mapping to
`VM_PREFIX_TO_BUCKET` in the watchdog script (re-uploads on next poll, no daemon restart needed).

## Out of scope

- Opinion.trade (Phase 3 — separate plan)
- Backfilling pre-launch dates per venue (clipped via coverage_starts)
- Building Tardis-Machine self-hosted instances (we use the SaaS for now)
- Migrating existing CeFi data to a new layout (not needed; new venues land in same hive partitions)

## Success criteria

Per phase:

- **Phase 1**: 5 new Tardis venues (BITFINEX-SPOT, BITGET-SPOT, BITGET-FUTURES, KRAKEN-SPOT, KRAKEN-FUTURES) in UAC;
  CeFi backfill VMs running for them; >0 captured rows after 4h.
- **Phase 2**: 3 new DEX perp venues (EXTENDED, PACIFICA, LIGHTER) with working REST adapters; backfill VMs producing
  real records (per docs verify min Hyperliquid-equivalent record-rate per day).
- **Phase 3**: deferred.

Final QG: `cd unified-api-contracts && bash scripts/quality-gates.sh` clean;
`cd market-tick-data-service && bash scripts/quality-gates.sh` clean; manifest reflects new venues; data-status report
includes them.
