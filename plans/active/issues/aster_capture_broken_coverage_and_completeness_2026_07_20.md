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
- **GAP 4 (pre-launch proxied trades, SHIPPED 2026-07-21 — all 3 repos):** `expected_start_dates.yaml:59,143,162` set
  ASTER trades genesis `2021-08-30` (annotated proxy/aggregated) vs UAC native `2023-07-22`. `fapi.asterdex.com` serves
  deep pre-launch history that is Astherus-pre-rebrand data mirroring Binance values. Any backfill of
  2021-08-30→2023-07-22 ingests Binance-origin values tagged `venue=ASTER`. Clip trades genesis to the native 2023-07-22
  (+ recalculated derived +200d/+9d dates). **Shipped in all 3 repos:** execution-service@e11e6a136,
  unified-trading-pm@12b0d9db8 (deployment-service via symlink), and market-tick-data-service@d8efc6d6. MTDS's ship was
  delayed by two genuinely unrelated whole-program regressions discovered and fixed along the way (not the config change
  itself): (1) `market-tick-data-service@08f15f26` — 2 stale regression-guard tests asserting the OLD,
  now-operator-ruled-wrong `build_instrument_id` passthrough behavior for symbols carrying an embedded `:` (uac@502ef57e
  made this fail loud; one of the exact test fixtures, Bitfinex Futures' real `ADAF0:USTF0` wire symbol, is cited by
  name in the ruling as the bug's real-world case); (2) `market-tick-data-service@327eef73` — re-pinned the RULE-11 DEFI
  shard-count regression guard 2646→2673 after verifying `uac@6bdbc31d` legitimately flipped the pre-existing
  AAVE-ETHEREUM venue from `phase=pipeline` to `phase=live` (LST rate honest-coverage Phase 1), which this enumerator
  counts as a newly-appearing venue (+27 shards, confirmed via direct measurement: 99 distinct DEFI venues,
  AAVE-ETHEREUM contributing exactly 27).

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

- ✅ **A. Trades pagination fix** — SHIPPED mtds@accd8aa4 (correction: the real batch path is
  `market_interface/adapters/onchain_perps/aster_adapter.py`, not `_umi_aster.py` — that module is the separate
  UMI/Tardis-side path, unused by `onchain_perp_batch_handler._fetch_aster`). `_fetch_agg_trades_response` now pages on
  `fromId` up to `_AGG_TRADES_MAX_PAGES` until a short page or a record crossing `end_ms` signals the tail, instead of a
  single `limit=1000` request truncating the day. Also bundled: `AsterBaseClient.throttle()` enforces the
  previously-dead `rate_limit_per_second` config (2026-07-20 429 incident), handler-level adapter reuse, exchangeInfo
  failure cooldown, and 429/transport → raise (not fabricated `empty_confirmed`). +4 regression tests.
- ✅ **B. Universe: admit the 1000-multiplier bases** — SHIPPED uac@34580d92. All 10 ASTER 1000-multiplier bases
  (1000PEPE/1000BONK/1000SHIB/1000FLOKI/1000LUNC/1000CHEEMS/1000SATS/1000WOJAK/1000NEX/1000XEC) added to
  `CEFI_BASE_ASSET_UNIVERSE`; `is_in_mvp_capture_universe(ASTER, 1000PEPE)` verified True. Catalogue rebuild + backfill
  still pending (folds into STEP 3 of the HL k-coin plan — same UAC-deploy-gated blocker, see
  `hl_multiplier_kcoins_excluded_from_mvp_universe_2026_07_20.md`).
- ✅ **C. Run the ASTER trades backfill — COMPLETE + VERIFIED.**
  - ✅ **1000-multiplier coins.** Surgical run
    `VENUES=ASTER DATA_TYPES=trades FORCE=true SYMBOLS="1000PEPE;1000BONK;1000SHIB;1000FLOKI;1000LUNC;1000CHEEMS; 1000SATS;1000WOJAK;1000NEX;1000XEC" YEARS="2024 2025 2026" SHARD_DAYS=21`
    (RUN_TS 20260720-205932, 32 VMs, all self-shut-down clean, real rows confirmed for 1000PEPE/1000SHIB/1000FLOKI in
    spot-checks).
  - ✅ **Full 448-perp universe re-run — COMPLETE.** mtds@accd8aa4 (rate-limit bundle) + mtds@aa72787b (row_key fix) via
    `VENUES=ASTER DATA_TYPES=trades FORCE=true SYMBOLS=ALL YEARS="2024 2025 2026" SHARD_DAYS=21` (RUN_TS
    20260720-203019, 46 VMs, all 46/46 self-shut-down over ~3.7h). VERIFIED: instrument-parquet counts across the full
    range (2024-01-01 → 2026-07-20) grow from 60 → 453 tracking ASTER's real universe growth over time (sampled 12
    dates); `capture_status` for 2026-07-01 ties out EXACTLY against GCS (441 `captured` manifest rows = 441 real
    parquet files); **zero `attempted_failed` rows across the entire backfill** — the rate-limit fix worked well enough
    that no persistent 429 exhaustion occurred at all (no failure-path exercise needed, so the row_key fix's correctness
    here is unexercised-but-present, confirmed separately via the earlier 1000-coin run's 105 logged
    429-retry-then-succeed sequences). Total canonical manifest rows grew 9,847,687 → 10,409,187 organically (matches
    the ~561k new ASTER/trades rows written), confirming the earlier 429-incident CAS cleanup remained durable
    throughout (no resurrected poisoned rows).
  - Genesis clip to the native 2023-07-22 (currently backfilling from ASTER's UAC start_date 2024-01-01, which already
    excludes the pre-launch Astherus-proxied window — GAP-4's specific clip to the databento-verified date was a
    separate, smaller item): **shipped 2026-07-21 in all 3 repos** — execution-service@e11e6a136,
    unified-trading-pm@12b0d9db8 (deployment-service via symlink), market-tick-data-service@d8efc6d6.
- ✅ **D. Provenance hardening (host-guard half)** — SHIPPED mtds@accd8aa4. `_assert_aster_host()` guards all 3 ASTER
  live-WS connector construction sites (`aster_book_liq_ws.py`) against the latent Binance-host footgun; +3 regression
  tests (`test_aster_ws_connector.py::TestAsterHostGuard`). GAP-4 genesis clip to 2023-07-22 DONE in all 3 repos —
  execution-service@e11e6a136, unified-trading-pm@12b0d9db8 (deployment-service via symlink),
  market-tick-data-service@d8efc6d6.

## Status (2026-07-21): A, B, C, D(host-guard), and GAP-4 all shipped + verified with real data, in all 3 repos —

execution-service@e11e6a136, unified-trading-pm@12b0d9db8 (deployment-service via symlink),
market-tick-data-service@d8efc6d6. The MTDS ship was delayed by two unrelated, genuinely-real whole-program test
regressions (fixed along the way, not swept under the rug — see the GAP-4 bullet above for both). Remaining open: the
"why did capture stop 2026-06-20" historical question (moot now — full backfill re-run supersedes it). All tracked fix
items (A/B/C/D/GAP-4) are now shipped; ready for a final read-through before flipping frontmatter `status:` to
`resolved`.

## INCIDENT 2026-07-21 — duplicate instrument_id from explicit-symbol surgical re-runs (found + fixed)

Surfaced while verifying, for the operator, that MTDS writes exactly one parquet per instrument for the 10
1000-multiplier coins. It doesn't — 8-10 of the 10 coins had trade data written under **two different canonical
instrument_ids** for the SAME real trades: `ASTER:PERPETUAL:1000BONK-USDT@LIN` (correct) and
`ASTER:PERPETUAL:1000BONK@LIN` (wrong, quote-less). Spot-checked pairs were byte-identical (same row counts, timestamp
ranges, price sums) — a genuine mechanical duplicate, not two real markets.

**Root cause:** `resolve_venue_symbols()` (`_onchain_perp_batch_symbols.py`) passes an explicit `--onchain-perp-symbols`
list through **verbatim** ("surgical re-run path") — correct for HYPERLIQUID/LIGHTER/EXTENDED, whose
`native_symbol_to_instrument_id` branches never need to recover a quote asset from the input string. ASTER's branch
does: it suffix-matches the input against `_ASTER_QUOTE_SUFFIXES` to split `base` from `quote`. The catalogue-driven
`ALL` path always passes the real wire symbol (`1000BONKUSDT`), so suffix-matching works. My earlier surgical 1000-coin
backfill this session passed **bare base-asset names** (`1000BONK`, matching the UAC universe naming convention used
everywhere else) — no suffix matches, so the function silently fell through to a quote-less id. Two different valid ways
of naming the same instrument → two different canonical ids → duplicate writes. Measured scope: **2,390 (day, coin)
pairs** with wrong-form data across the full 2025-05-25→2026-07-20 range (2,373 true duplicates + 17
initially-bare-only, see remediation below); **4,715 manifest rows** under the 10 wrong bare-form instrument_ids (all
`data_type=trades` — `derivative_ticker` was never affected).

**Fix — SHIPPED mtds@a7f7769a.** `native_symbol_to_instrument_id`'s quote-split logic extracted into
`_aster_native_quote_split()`; new `_resolve_aster_native_symbols()` cross-references the day's catalogue-native symbols
(already real wire form) by base-asset so an explicit ASTER symbol resolves to the SAME id the `ALL` path would produce
for the identical instrument. A symbol absent from that day's catalogue (not yet listed) passes through unchanged — no
regression on the not-yet-listed case. +5 regression tests (`TestAsterExplicitSymbolQuoteResolution`). Other venues
unaffected (verbatim passthrough unchanged).

**Remediation — COMPLETE + VERIFIED:**

1. Rebuilt + uploaded the UAC/UTL/MTDS/deployment-service code tarballs (VMs deploy from GCS tarballs, not a live git
   pull — the fix needed a fresh tarball before any new backfill VM would pick it up).
2. Corrective re-backfill:
   `VENUES=ASTER DATA_TYPES=trades FORCE=true SYMBOLS="<the 10 coins>" YEARS="2025 2026" SHARD_DAYS=21 OVERRIDE_START_DATE=2025-05-25`
   (RUN_TS 20260721-025937, 21 VMs, ~18min to full self-shutdown — much faster than the ~3.7h general 46-VM run since
   this is a narrow 10-symbol universe per VM). Post-run sweep found 2 of 422 days (2026-06-19/20) still bare-only — a
   transient VM-startup hiccup, not a code defect (a narrow 3-day retry, RUN_TS 20260721-032600, resolved it cleanly on
   the first attempt).
3. Deleted all 2,390 wrong-form (bare, no `-USDT`) parquet files, each individually re-verified to have a non-empty
   `-USDT` replacement immediately before deletion (0 skipped for safety). A final full-range sweep confirms **zero**
   bare-form files remain anywhere.
4. Manifest cleanup: paused `uts-prod-manifest-consolidator-market-data-cefi-cron`, removed the 4,715
   wrong-instrument-id rows via generation-matched CAS. **Gotcha (documented for next time):** a raw CAS write that
   doesn't carry the consolidator's `consolidator_content_write_at` blob-metadata marker forward gets treated by the
   next consolidator cycle as an unprovable-cutoff out-of-band rewrite — it fails closed and re-merges every per-VM
   shard, and (this session) the bad rows briefly resurrected from that path before self-clearing. Second pass: redid
   the CAS removal, then immediately called `manifest_consolidator.consolidate(bucket, force=True)` directly (the
   officially-supported write path) rather than waiting on the cron, so the marker is stamped correctly in the same
   operation. Verified 0 bad rows immediately after, and via a follow-up multi-cycle check.

**Lesson:** an explicit `--onchain-perp-symbols` surgical list is safe for venues whose `native_symbol_to_instrument_id`
never has to recover information from the input string — it is NOT safe by inspection alone for a venue that
suffix-guesses a quote asset. Any future venue added with similar quote-suffix inference needs the same
catalogue-cross-reference treatment `_resolve_aster_native_symbols` provides.

### CORRECTION 2026-07-21 — remediation scope was wrong; real ASTER backfill starts 2024-01-01, not 2025-05-25

The remediation above only covered 2025-05-25→2026-07-20 because that range was copied verbatim from the parallel HL
k-coin fix's scope, without checking it against ASTER's own actual backfilled window. Verified directly (operator
question prompted the check): UAC's audited native (non-proxy) ASTER start is `2023-07-22`
(`unified_api_contracts/registry/venue_launch_dates.py`); what's actually backfilled in GCS starts `2024-01-01`
(confirmed nothing exists in GCS before that — 2021-09-01/2022-06-01/2023-07-22/2023-08-01 all 404, so the Astherus
pre-rebrand proxy window was never backfilled and needs no purge). The still-open gap is
`configs/expected_start_dates.yaml` (replicated per-repo) still declaring genesis `2021-08-30` — this was GAP-4, now
SHIPPED. (Update 2026-07-21, later same day: GAP-4 shipped in all 3 repos — execution-service@e11e6a136,
unified-trading-pm@12b0d9db8 (deployment-service via symlink), market-tick-data-service@d8efc6d6 — see the GAP-4
bullet + Status section above for the full history, including the 2 unrelated whole-program regressions found + fixed
along the way to unblock MTDS's ship.)

Checking 2024-01-01 directly (to answer "is this real ASTER data") surfaced that the SAME duplicate-instrument-id bug
was still present, uncorrected, for the entire 2024-01-01→2025-05-24 window — **1,923 more duplicate pairs**. The code
fix (mtds@a7f7769a) already covers this window (it's venue-general, not date-scoped) — only the corrective backfill +
cleanup had the wrong scope.

**Second remediation round — COMPLETE + VERIFIED:**

1. Corrective re-backfill:
   `VENUES=ASTER DATA_TYPES=trades FORCE=true SYMBOLS="<the 10 coins>" YEARS="2024 2025" SHARD_DAYS=21 OVERRIDE_START_DATE=2024-01-01 OVERRIDE_END_DATE=2025-05-24`
   (RUN_TS 20260721-091332, 25 VMs, ~18min to full self-shutdown). Post-run sweep: 0 bare-only pairs remained (clean on
   first attempt, no retry needed this time).
2. Deleted 1,923 wrong-form (bare) parquet files, each re-verified to have a non-empty `-USDT` replacement immediately
   before deletion (0 skipped for safety). A full-range sweep across the ENTIRE 2024-01-01→2026-07-21 backfill window
   (not just this round's window) confirms **zero** bare-form files remain anywhere.
3. Manifest cleanup: paused the consolidator cron, CAS-removed 510 wrong-instrument-id rows for this window, then
   immediately called `consolidate(bucket, force=True)` to stamp the marker correctly (applying the lesson from the
   first round's gotcha) before resuming the cron. Durability-verified across multiple consolidator cycles.

**Provenance re-confirmed while investigating**: `AsterBaseClient`'s REST base URLs (`fapi.asterdex.com` /
`api.asterdex.com`) are hardcoded with no env override — every fetch in both remediation rounds hit the real exchange,
not a Binance proxy.

**Funding-rate spot-check (separate, related finding)**: sampling `derivative_ticker` across the 10 coins found real,
moving funding rates for 8 of 10 (BTC/ETH/SOL controls: 113-146 distinct values over 183 observations; 1000PEPE: 31;
1000BONK: 4). Two show near-zero variance — `1000SHIB` (flat `0.0001`, confirmed via a LIVE `fapi.asterdex.com` call to
still be flat today, not a stale pipeline artifact) and `1000SATS` (flat, and live 24h quoteVolume is $6.04 on 1 trade —
essentially a dead market). This is genuine ASTER exchange behavior for illiquid instruments, not a pipeline defect —
tracked as a downstream feature-quality concern, not a data-correctness issue, in the new ADV-feature plan (see
`plans/active/aster_and_cefi_rolling_adv_feature_2026_07_21.md`).
