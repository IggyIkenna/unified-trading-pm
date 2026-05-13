---
title: Emerging perp venue adapters — root-cause diagnosis (ASTER 0%, HYPERLIQUID 68% failure)
created: 2026-05-13
author: ikenna-slot-8
severity: P0
parent_issue: emerging_perp_venue_adapters_broken_2026_05_13.md
source:
  - market-tick-data-service/market_tick_data_service/market_interface/adapters/onchain_perps/hyperliquid_adapter.py:374-420 (fetch_trades stub)
  - market-tick-data-service/market_tick_data_service/market_interface/clients/aster_base_client.py:77-78 (base URLs)
locked_by: live-defi-rollout
locked_since: 2026-05-13
---

## What I found

Slot 8 (ikenna tab/8) diagnosed the perp adapter failure modes flagged in
[`emerging_perp_venue_adapters_broken_2026_05_13.md`](emerging_perp_venue_adapters_broken_2026_05_13.md).
Slot-3 originally filed the manifest-capture observation; this issue adds the
root-cause for ASTER (0%) and HYPERLIQUID (68% failure).

### HYPERLIQUID — incomplete adapter (root cause)

**File**: `market-tick-data-service/market_tick_data_service/market_interface/adapters/onchain_perps/hyperliquid_adapter.py:374-420`

`HyperliquidAdapter.fetch_trades()` is **a 3-branch stub**:

```python
# fetch_trades routing:
# - date_utc >= S3_TRADES_START (2025-03-22+): "delegated to MTDS" → return []
# - 2024-10-29 <= date_utc < 2025-03-22: calls _download_trades_from_tardis()
#   which is itself a stub returning [] with warning "Tardis integration not implemented"
# - date_utc < 2024-10-29: return [] (pre-coverage)
```

**Lines 417-420 (Tardis stub):**

```python
async def _download_trades_from_tardis(self, coin: str, date_dt: datetime) -> list[dict[str, object]]:
    """Download trades from Tardis.dev API (requires separate Tardis integration)."""
    logger.warning("Tardis integration not implemented in unified adapter - delegate to Tardis client")
    return []
```

**Lines 392-394 (S3 stub):**

```python
if date_utc >= self.S3_TRADES_START:
    logger.debug("fetch_trades: date %s >= S3_TRADES_START — delegated to MTDS", start_date)
    return []
```

Result: `fetch_trades` returns `[]` for ALL date ranges. The 32% capture rate
that DOES exist (14,710 rows) is from **non-trade data_types** (funding_rates
via REST, asset_ctxs via S3, instrument metadata). The 68% failure (30,658 rows)
is the trades data_type — which has no working capture path in this adapter.

**Fix shape**: implement either (a) the Tardis client call for 2024-10-29 →
2025-03-21 window, or (b) wire the S3 downloader call for 2025-03-22+ window
into `fetch_trades` instead of returning `[]` with a debug log. The
`HyperliquidS3Downloader` already exists at
`market-tick-data-service/market_tick_data_service/adapters/hyperliquid_s3.py`
(per the adapter's own docstring) — the wiring at line 392-394 is the gap.

### ASTER — wrong base URLs (root cause)

**File**: `market-tick-data-service/market_tick_data_service/market_interface/clients/aster_base_client.py:77-78`

```python
base_url_spot: str = "https://api.aster.exchange"
base_url_futures: str = "https://www.aster.exchange"
```

The file's own docstring header references the canonical Aster API docs:

```python
# Line 20: "Aster API Reference: https://github.com/asterdex/api-docs"
```

Per Aster Finance's official GitHub api-docs, the canonical futures REST API
base URL is `https://fapi.asterdex.com` (not `www.aster.exchange`). The configured
URLs don't match the documented Aster Finance endpoints, which would cause every
API call to hit DNS-resolution-OK-but-404-not-found OR direct connection failure
depending on the actual destination of `www.aster.exchange`.

This explains **17,681/17,681 rows = 0% capture** since 2024-10-01. The
adapter has been calling unreachable endpoints for ~1.5 years; every shard
fails into `attempted_failed`.

**Fix shape**: update base URLs to match the official Aster Finance api-docs
(`https://fapi.asterdex.com` for futures; spot endpoint per docs — may also be
on a different host than `api.aster.exchange`). Operator should confirm exact
URLs from current [Aster Finance api-docs](https://github.com/asterdex/api-docs)
before patching — the URLs may have been correct historically and Aster may
have rebranded (the comment "post-rebrand from Astherus" in
`venue_launch_dates.py` hints at this).

### PACIFICA-SOLANA, LIGHTER-ZKSYNC, EXTENDED-STARKNET

Not yet diagnosed in this issue. The pattern likely mirrors ASTER (stale/wrong
endpoints) OR HYPERLIQUID (stub adapter). Operator triage: prioritise ASTER fix
first (largest blast radius + clearest 1-line patch); HYPERLIQUID second (more
complex S3/Tardis wiring); other 3 venues third.

## Why it matters

Confirms parent issue's P0 framing. ASTER + HYPERLIQUID are explicit perp-hedge
venues for the DeFi archetypes per CLAUDE.md "DeFi + CeFi hybrid instrument
universe". With 0% / 32% capture, hedge legs cannot be backtested or
operationally trusted on May-23 cutover.

**Counter-argument worth noting**: the strategy may be able to limp to cutover
on Binance / Bybit / Deribit / OKX / Kraken (the other 5 perp venues with healthy
capture). ASTER + HYPERLIQUID become P1 instead of P0 IF the operator scopes
the May-23 cutover to the 5 fully-working perp venues. Operator triage decision
needed.

## Recommended decision

**Option A (recommended)**: Patch ASTER URLs (1-line fix, ~30 min including
verification) + wire HYPERLIQUID S3 path (1-2 hours, reuses existing
`HyperliquidS3Downloader`). Both shippable today.

**Option B**: Scope May-23 cutover to 5 fully-working perp venues; defer ASTER
+ HYPERLIQUID + LIGHTER + PACIFICA + EXTENDED to post-cutover. Document in
master plan as scope contract.

**Option C** (hybrid): Patch ASTER now (fast + isolated); defer HYPERLIQUID
to operator triage given the larger refactor scope.

## Suggested owner

slot focused on MTDS adapter debugging; OR a new dedicated slot per parent
issue's recommendation #1. Slot 8 (this slot) can patch ASTER URLs immediately
if operator confirms canonical Aster Finance endpoints from current api-docs.

## Cross-references

- Parent: `emerging_perp_venue_adapters_broken_2026_05_13.md` (Slot 3 finding)
- HYPERLIQUID stub: `market-tick-data-service/.../hyperliquid_adapter.py:374-420`
- ASTER URLs: `market-tick-data-service/.../aster_base_client.py:77-78`
- HYPERLIQUID S3 downloader (the missing wiring target):
  `market-tick-data-service/market_tick_data_service/adapters/hyperliquid_s3.py`
- CLAUDE.md "DeFi + CeFi hybrid instrument universe" (eligibility rule)
