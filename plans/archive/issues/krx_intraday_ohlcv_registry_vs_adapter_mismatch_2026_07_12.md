---
doc_type: issue
title: KRX ohlcv_1m/ohlcv_15m are declared expected coverage but the Yahoo adapter can only ever serve ohlcv_24h
summary:
  "Found 2026-07-12 while triaging the 2026-07-09 452-shard sweep's TRADFI/KRX failures (all 9 non-ohlcv_24h data_types
  failed for KRX — corporate_action_confirmed, earnings_result, macro_result, mbp_10, ohlcv_15m, ohlcv_1m, ohlcv_1s,
  tbbo, trades). Root-caused and fixed the mechanical bug (umi_tick_provider.py's FX/KRX dispatch ignored the requested
  `data_types` entirely, always calling the Yahoo daily-bar fetch and hardcoding `data_type=ohlcv_24h` on every written
  row — market-tick-data-service@e128c5bc). That fix makes 7 of the 9 an honest, correctly-labeled empty result
  (corporate_action_confirmed/earnings_result/macro_result/mbp_10/ohlcv_1s/tbbo/trades — Yahoo genuinely has no
  intraday/tick/fundamental feed for these Korean tickers, matches the ASTER/HYPERLIQUID
  'EXPECTED_SOURCE_DOES_NOT_OFFER_DATA_TYPE' pattern already in the honest-coverage registry). BUT 2 of the 9 — ohlcv_1m
  and ohlcv_15m — are NOT structurally impossible in the same way: `unified_api_contracts/registry/
  expected_coverage.py` line 170 explicitly declares `'KRX': ['ohlcv_1m', 'ohlcv_15m', 'ohlcv_24h']` as KRX's expected
  data_types, but the ONLY fetch path that exists (`_fetch_yahoo_equities` -> `YahooFinanceAdapter.download_daily`) has
  no intraday capability at all — it will keep honestly reporting 'no data' for ohlcv_1m/15m forever, not because Yahoo
  can't serve intraday KRX bars (yfinance DOES support an `interval=` param for shorter bars on many tickers), but
  because the adapter was never built to request it. This is a genuine open question: is the registry entry aspirational
  (adapter incomplete, should be built) or wrong (registry should only declare ohlcv_24h for KRX, matching what the
  adapter's docstring says: 'venue=KRX, source=yahoo, data_type=ohlcv_24h')?"
status: resolved
nature: notes
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags: [tradfi, krx, yahoo-finance, expected-coverage, honest-coverage, data-correctness, registry-adapter-mismatch]
related:
  [
    ../data_pipeline_e2e_check_2026_07_10.md,
    ../../../codex/02-data/honest-coverage-model.md,
    ../../../codex/02-data/tradfi-databento-sourcing-ssot.md,
  ]
created: 2026-07-12
parent_epic: infrastructure_master
priority: P3
source: [pipeline_e2e_check todo-25 triage, real VM run.log evidence + direct code read, 2026-07-12]
assigned_vm: NA
resolved_by: operator-decision-2026-07-12
locked_by:
execution_scope: local-only
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
drift_direction: unknown
depends_on: []
---

# KRX ohlcv_1m/ohlcv_15m: registry says expected, adapter can never serve it

## Context

`data_pipeline_e2e_check_2026_07_10.md` todo 25 flagged TRADFI/KRX as failing across ALL 9 of its non-ohlcv_24h
data_types in the 2026-07-09 452-shard sweep — a strong venue-level signal. Live re-verification (real VM,
`mtds-backfill-tradfi-pipelinecheck-20260712-095739`, `--data-types trades`) confirmed the mechanism: the real run.log
shows the VM wrote `data_type=ohlcv_24h` parquet objects (`005380.parquet`/`005930.parquet`/`000660.parquet`) despite
`trades` being requested — `market_tick_data_service/adapters/umi_tick_provider.py`'s KRX branch called
`_fetch_yahoo_equities()` unconditionally, ignoring the `data_types` filter entirely (unlike every other branch in the
same function — Databento, Massive, Tardis all filter `data_types` against what they can serve).

## Fixed (mechanical bug)

`market-tick-data-service@e128c5bc` — KRX (and FX) dispatch now honours the requested `data_types`: if `ohlcv_24h` isn't
in the request, returns honest-empty instead of silently writing mislabeled ohlcv_24h data. 3 new regression tests. This
closes the SILENT MISLABELING half of the bug (a real, mechanical, safe fix — matches the already-established
`_route_databento` filtering pattern in the same file).

## Open question (not resolved — needs a decision, not a fix)

After the mechanical fix, KRX/`ohlcv_1m` and KRX/`ohlcv_15m` will keep failing `no_parquet_under` — now for the HONEST
reason (Yahoo integration has no intraday fetch path), but `expected_coverage.py`'s
`"KRX": ["ohlcv_1m", "ohlcv_15m", "ohlcv_24h"]` entry (line 166-170, "added 2026-06-24 (KRX venue close-out)")
explicitly declares these as expected coverage. Two ways to resolve, genuinely requiring a call:

1. **Adapter is incomplete — build intraday KRX fetch.** `yfinance`'s `download()`/`history()` supports an `interval=`
   param (`"1m"`, `"15m"`, etc.) for many tickers, though intraday history windows on Yahoo are typically much shorter
   (recent days only, not arbitrary historical backfill) and per-ticker availability for Korean `.KS` tickers
   specifically is unverified — would need a real live check before committing to this direction.
2. **Registry is wrong — KRX should only declare `ohlcv_24h`.** Matches `_fetch_yahoo_equities`'s own docstring
   ("venue=KRX, source=yahoo, data_type=ohlcv_24h") and the adapter's actual, only-ever-built capability. Lower-risk,
   smaller change (one registry entry), but narrows KRX's documented coverage — worth confirming this doesn't contradict
   a downstream consumer (features/strategy) that expects intraday KRX bars for the 3 Binance-tradfi-perp underliers
   this venue exists to serve (`KRX_EQUITIES` docstring: "Korean underliers of the Binance tradfi-perps").

Not resolved here — flagging for an operator/architecture decision rather than guessing at product intent.

## Resolution — option 2 chosen (registry narrowed)

Operator decision (2026-07-12): option 2 — Yahoo doesn't reliably serve intraday granularity over long historical
backfill windows, so build-the-adapter (option 1) was rejected. Narrowed `expected_coverage.py`'s KRX entry to
`["ohlcv_24h"]`. Shipped `unified-api-contracts@a2751f36`.

**Follow-on discovery during implementation**: KRX is ALSO hardcoded as a TradFi "equity-basis" MVP venue
(`_mvp_scope_predicate.py`'s equity-basis carve-out, alongside NASDAQ/NYSE/ARCA/AMEX/BATS) whose MVP data_type was the
shared `rule.data_types = {"ohlcv_1m"}` — i.e. the MVP layer would have kept claiming KRX ohlcv_1m is business-critical
(for Binance tradfi-perp basis tracking) even after `expected_coverage.py` stopped expecting it, a real cross-registry
inconsistency the original open question didn't anticipate. Operator confirmed: drop KRX ohlcv_1m from MVP too, so KRX's
equity-basis carve-out now checks `ohlcv_24h` specifically (separately from the US-listed venues, which keep
`rule.data_types`/ohlcv_1m). Same commit (`unified-api-contracts@a2751f36`) — both registries narrowed in lockstep, plus
`test_krx_basis_cells_are_mvp`/`_tradfi_mvp_equity_cells` updated to match.

## Progress log

- 2026-07-12: Filed after fixing the mechanical silent-mislabeling bug (`market-tick-data-service@e128c5bc`) and
  confirming, via real VM run.log evidence, that the ohlcv_1m/ohlcv_15m portion of KRX's declared expected coverage is
  genuinely unreachable by the current adapter — not a bug to fix blindly, a registry-vs-capability decision to make.
- 2026-07-12: Operator chose option 2 (narrow the registry). Shipped `unified-api-contracts@a2751f36` — both
  `expected_coverage.py` and the MVP scope's equity-basis carve-out narrowed to ohlcv_24h for KRX, keeping the two
  registries in sync (the MVP-layer inconsistency was found and closed in the same pass, not left as a new gap).
