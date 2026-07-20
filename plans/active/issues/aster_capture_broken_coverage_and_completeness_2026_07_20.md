---
doc_type: issue
title: >-
  ASTER data: provenance is TRUE-ASTER (clean), but capture is BROKEN — only ~9 majors captured (stale since
  2026-06-20), trades hard-capped at 1000 rows/day, and the 448-perp universe (incl. 1000-multiplier meme perps) is
  never downloaded
summary: >-
  Multi-agent audit (2026-07-20) of the ASTER perp-DEX pipeline. PROVENANCE (the "are we proxied with Binance data"
  worry): RESOLVED — every ASTER fetch path hits a *.asterdex.com host (fapi.asterdex.com batch REST + reference data,
  api.asterdex.com spot, fstream.asterdex.com live WS); ZERO *.binance.com host anywhere in the ASTER path; base URLs
  hardcoded, no env override; captured parquets carry venue=ASTER + ASTER-native instruments (ASTER-USDT, tokenized
  equities) absent from Binance. COVERAGE + COMPLETENESS: BROKEN on three axes — (1) batch_aster trades on GCS = exactly
  9 majors (ADA/AVAX/BNB/BTC/DOGE/ETH/LINK/SOL/XRP-USDT) on day=2026-06-20 and ZERO on every day 2026-06-25→2026-07-20
  (stale >1 month; the expanded 448-perp catalogue universe was NEVER captured); (2) even the 9 captured are hard-capped
  at 1000 rows/day (aggTrades limit=1000 not paginated → partial day, ~00:01→11:05 UTC on the sampled ADA parquet); (3)
  the MVP gate drops 59-62 of ~510 live perps whose base isn't in CEFI_BASE_ASSET_UNIVERSE, INCLUDING 10 1000-multiplier
  perps (1000PEPE/1000BONK/1000SHIB/1000FLOKI/1000LUNC/1000CHEEMS/1000SATS/1000WOJAK/1000NEX/1000XEC) — the exact
  HL-kPEPE/kBONK analog (plain + K-form bases ARE in the universe, but "1000X" matches neither). Two latent provenance
  risks: a host FOOTGUN (ASTER live-WS connectors subclass Binance connector classes defaulting to fstream.binance.com;
  correct only because each subclass explicitly passes url=_ASTER_STREAM_URL — one future omission = silent Binance data
  tagged ASTER) and GAP 4 (expected_start_dates.yaml trades genesis 2021-08-30 is pre-launch Astherus-pre-rebrand data
  mirroring Binance values vs UAC native 2023-07-22 — must be clipped).
status: open
nature: issue
asset_group: [cefi]
stage: [meta]
repos: [market-tick-data-service, unified-api-contracts, instruments-service, deployment-service]
scope: [engineer, admin]
tags:
  [aster, hyperliquid, capture-universe, data-completeness, provenance, binance-proxy, mvp-universe, cefi-onchain-perp]
related:
  [
    hl_multiplier_kcoins_excluded_from_mvp_universe_2026_07_20.md,
    cefi_hl_aster_batch_data_gaps_2026_06_22.md,
    cefi_backfill_per_day_catalogue_reload_2026_07_20.md,
  ]
created: 2026-07-20
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: brand-new
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 2.0
assigned_role: data-pipeline
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
source:
  ["multi-agent ASTER audit 2026-07-20 (operator asked: is ASTER working, all coins, were we proxied with Binance)"]
---

# ASTER capture: clean provenance, broken coverage + completeness

## Q — Binance-proxy worry: TRUE ASTER (resolved)

Every ASTER fetch path points at a `*.asterdex.com` host, NOT binance.com:

- Batch REST trades/funding/premium: `_umi_aster.py:62` `base_url="https://fapi.asterdex.com"` → `/fapi/v1/aggTrades`,
  `/fundingRate`, `/premiumIndex`.
- Reference data: `instruments-service .../adapters/cefi/aster.py:44` `_BASE="https://fapi.asterdex.com"` →
  `/exchangeInfo`, `/fundingRate`, `/premiumIndex`, `/klines`.
- onchain-perp batch alt client: `aster_base_client.py:84-85` `base_url_futures=https://fapi.asterdex.com`,
  `base_url_spot=https://api.asterdex.com`; `from_env` injects only api_key/secret — NO base-url override.
- Live WS: `aster_book_liq_ws.py` `wss://fstream.asterdex.com/{stream,ws}` for book_snapshot_5/trades/liquidations.

Live curl proof: `fapi.asterdex.com` (IP 99.86.12.43, 528 perps incl. ASTER's own ASTER-USDT) vs `fapi.binance.com` (IP
108.156.39.10, 841 symbols) — different host, IP, and universe. The Binance-compatible SCHEMA is reused (parsers +
subclassed Binance WS connector classes), but the HOST is correctly ASTER everywhere. **No active proxy.**

## Q — all the coins? NO — capture is broken on three axes

1. **Stale + tiny (headline).** `gs://market-data-tick-cefi-prd-central-element-323112` `pipeline_mode=batch_aster`
   trades = **9 instruments** (ADA/AVAX/BNB/BTC/DOGE/ETH/LINK/SOL/XRP-USDT) on `day=2026-06-20`, and **ZERO** parquets
   on 2026-06-25 / 07-01 / 07-10 / 07-15 / 07-19 (verified 2026-07-20). The expanded **448 mvp=True** catalogue universe
   was NEVER captured; actual coverage is the 9-major pre-BUG#4 seed, and no new batch_aster trades in >1 month. **Open
   question: WHY did capture stop on 2026-06-20** (deliberate pause vs. broken cron/launcher)?
2. **Partial day (completeness).** Sampled `ASTER:PERPETUAL:ADA-USDT@LIN.parquet` (day=2026-06-20) = exactly **1000
   rows**, span 00:01:12→11:05:50 UTC. Trades are hard-capped at the aggTrades `limit=1000` and NOT paginated across the
   day (`_umi_aster.py` aggTrades path) — even the captured majors are a partial day, not full coverage.
3. **MVP gate drops 59-62 of ~510 perps** (base not in `CEFI_BASE_ASSET_UNIVERSE`), incl. **10 1000-multiplier perps**
   (1000PEPE/1000BONK/1000SHIB/1000FLOKI/1000LUNC/1000CHEEMS/1000SATS/1000WOJAK/1000NEX/1000XEC) — the exact HL k-coin
   analog: plain (PEPE) + K-form (KPEPE) bases ARE in the universe, but "1000X" matches neither. Plus a legacy
   `_umi_aster.py:57` `default_limit=20` fallback (a 21-major list) that hard-caps enumeration to 20 when the caller
   passes `instrument_ids=None`.

## Latent provenance risks (not active bugs, but the operator's exact fear)

- **Host FOOTGUN:** `binance_futures_ws.py:207` defaults `url=wss://fstream.binance.com/ws`; the 3 ASTER live-WS
  subclasses (`aster_book_liq_ws.py:149,243,383`) are correct ONLY because each explicitly passes
  `url=_ASTER_STREAM_URL/_ASTER_WS_URL`. A future ASTER connector subclassing a Binance connector and omitting the
  `url=` override would SILENTLY connect to `fstream.binance.com` and emit Binance data tagged `venue=ASTER`. Add a
  guard (assert host endswith asterdex.com in the ASTER connectors' `__init__`).
- **GAP 4 (pre-launch proxied trades, still OPEN):** `expected_start_dates.yaml:59,143,162` set ASTER trades genesis
  `2021-08-30` (annotated proxy/aggregated) vs UAC native `2023-07-22`. `fapi.asterdex.com` serves deep pre-launch
  history that is Astherus-pre-rebrand data mirroring Binance values. Any backfill of 2021-08-30→2023-07-22 ingests
  Binance-origin values tagged `venue=ASTER`. Clip trades genesis to the native 2023-07-22.

## INCIDENT 2026-07-20 — the first fix attempt caused manifest corruption (resolved)

A 33-VM ASTER trades backfill (RUN_TS 20260720-122739) captured **zero** rows and wrote **412,697 FALSE
`empty_confirmed` manifest rows** across 2024-01-01→2026-07-20 — the manifest asserting "confirmed no trades" for
instrument-days that actually traded. Detected by verifying GCS output rather than trusting the clean VM exit (all 33
shards self-shut-down "successfully").

**Corrected root cause** (the first hypothesis — "33 VMs caused a cross-IP storm" — was WRONG): the 429 body names the
limit explicitly, `current limit of IP(34.85.20.67) is 2400 requests per minute`. The limit is **PER IP**, and each VM
had its own ephemeral external IP (launcher passes no `--no-address`; project has no Cloud NAT). So parallel VMs were
never the problem — **each single VM blew its own budget in ~5s** (measured ~200 req/s vs the 40 req/s budget) because:

1. `OnchainPerpBatchHandler._fetch_aster` built a **NEW `AsterAdapter` per instrument**, so the adapter's 6h
   exchangeInfo cache never survived → `/fapi/v1/exchangeInfo` refetched 1:1 with every trades call (**11,100
   exchangeInfo 429s vs 11,100 trades 429s**), doubling request volume.
2. The symbol cache is populated **only on success**, so once throttled it never cached and every instrument retried
   exchangeInfo — a self-perpetuating spiral.
3. No client-side pacing anywhere in the adapter.
4. A 429/transport failure returned `[]`, which the shard recorded as `empty_confirmed` — the "never silent
   placeholders" violation that minted the false rows.

**Remediation (done):** 31 poisoned per-VM shards deleted; the 412,697 canonical rows removed via generation-matched CAS
with the consolidator paused (10,259,899 → 9,847,687 rows), verified durable across consolidator cycles; pre-existing
rows (34,449, written 2026-04-23..07-16) and real `captured` rows (1,041) left intact. **Lesson:** a rate-limited venue
REST API needs per-PROCESS request discipline; VM count is irrelevant when the budget is per-IP.

## Fix plan (mirror the HL playbook this session)

- ⬜ **A. Trades pagination fix** — page aggTrades past `limit=1000` (loop on `fromId`/time until day complete) in
  `_umi_aster.py`; ensure the batch caller passes the FULL resolved instrument list (never `instrument_ids=None` →
  20-cap). Ship via quickmerge + rebuild MTDS tarball.
- ⬜ **B. Universe: admit the 1000-multiplier bases** (operator scope call — same decision class as the HL k-coins,
  which the operator approved 2026-07-20). Add `1000PEPE`/`1000BONK`/… to `CEFI_BASE_ASSET_UNIVERSE` OR normalize the
  `1000`/`k` multiplier prefix in the base-membership check. Then catalogue rebuild → mvp=True.
- ⬜ **C. Run the ASTER trades backfill** for the full 448-perp universe (2023-07-22→today, genesis-clipped) via
  `launch-cefi-hl-aster-historical-backfill.sh VENUES=ASTER` with the finer sharding shipped this session; verify the
  448-instrument coverage lands.
- ⬜ **D. Provenance hardening** — add the host-assertion guard (footgun) + clip GAP-4 genesis to 2023-07-22.
