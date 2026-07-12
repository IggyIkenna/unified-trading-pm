---
doc_type: issue
title:
  TradFi Databento OHLCV (CME/CBOE/NYSE/NASDAQ, ohlcv_1s/ohlcv_1m) returns a clean 0-record success on a normal trading
  day, with no error/warning anywhere in the pipeline — root cause narrowed to the live SDK response itself, not any
  local guard
summary:
  "Found 2026-07-12 while re-verifying `data_pipeline_e2e_check_2026_07_10.md`'s TradFi OHLCV `--source` fix
  (deployment-service@29561c4, market-tick-data-service@42a55bc). The fix correctly routes these shards through
  DatabentoAdapter now (confirmed: 'API keys validated', 'DatabentoAdapter initialized' in the run.log), but 12/12
  re-verified shards (CME/CBOE/NYSE/NASDAQ/ICE ohlcv_1m+1s, CBOE ohlcv_15m, YAHOO_FINANCE ohlcv_15m+24h) still show zero
  parquet written for day=2026-07-09 (a normal Thursday, 3 days before 'today', well inside any lookback window). A
  follow-up investigation (this doc) narrowed 4 of those 12 (CME/CBOE/NYSE/NASDAQ ohlcv_1m/1s — the ICE/YAHOO_FINANCE
  ones are separately explained as non-Databento venues, already fixed in the same commit) to a genuine, unexplained
  empty response from Databento's live `timeseries.get_range()` call itself — every local guard that could short-circuit
  before the network call (billing/lookback allowlist, schema allowlist, instrument-preflight, IS_TEST_RUN) was traced
  and confirmed either inert or explicitly bypassed for TradFi, and every exception-handling branch that could mask a
  real failure was confirmed NOT to have fired (no matching log text anywhere in the full run.log). The SDK call
  genuinely executed and genuinely returned zero rows for all 4 venues simultaneously — pointing at ONE systemic cause
  (a dataset/date entitlement edge, or requested parent/raw symbols not resolving to any instrument_id for that specific
  day) rather than 4 independent coincidences. Static code reading alone cannot distinguish those two hypotheses; a live
  diagnostic (`client.symbology.resolve(...)`) is needed to confirm which."
status: open
nature: notes
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [tradfi, databento, ohlcv, adapter-bugs, silent-empty, smoke-test, data-correctness]
related:
  [
    ../data_pipeline_e2e_check_2026_07_10.md,
    tradfi_manifest_row_loss_regression_2026_07_12.md,
    tradfi_manifest_cf4_source_and_cf7_phantom_gaps_2026_07_07.md,
  ]
created: 2026-07-12
parent_epic: mtds_mdps_master
priority: P2
source:
  [
    pipeline_e2e_check TradFi OHLCV re-verification,
    day=2026-07-09,
    real VM run.log evidence,
    Databento Historical API docs (timeseries.get_range,
    symbology,
    errors reference),
  ]
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.7
assigned_role: data-pipeline-engineer
drift_direction: unknown
depends_on: []
---

# TradFi Databento OHLCV — silent zero-row success, no local guard involved

## Context

`data_pipeline_e2e_check_2026_07_10.md`'s earlier triage round found TradFi OHLCV shards were never even attempting a
fetch (`ValueError: --source databento|massive is REQUIRED`) and fixed it (deployment-service@29561c4,
market-tick-data-service@42a55bc — `--source` now correctly plumbed through the launcher and the checker). A
re-verification of all 12 affected shards for day=2026-07-09 confirmed the fix works (DatabentoAdapter now genuinely
engages) but **all 12 still write zero parquet rows**. Splitting the 12:

- **ICE** (ohlcv_1m): registered in `umi_tick_provider._DATABENTO_VENUES` but has zero rows in
  `TRADFI_DATABENTO_INSTRUMENTS` — Yahoo-DXY-only, IFUS.IMPACT explicitly removed per
  `codex/02-data/tradfi-databento-sourcing-ssot.md`. `--source databento` is a silent no-op for it (early-return before
  any network call). **Explained, not a bug** — the checker's own `--source` forcing logic has already been narrowed to
  exclude ICE (see market-tick-data-service commit `0dd8eaba`, same day).
- **YAHOO_FINANCE** (ohlcv_15m/24h): not in `_DATABENTO_VENUES` at all — `--source databento` is a complete no-op; its
  own 0-row cause is unrelated to Databento and not traced further here. **Also excluded from the checker's `--source`
  forcing as of the same commit.**
- **CBOE ohlcv_15m**: Databento only serves `ohlcv-1s`/`ohlcv-1m` per
  `umi_tick_provider._DATABENTO_SUPPORTED_DATA_TYPES`; coarser bars are aggregated downstream, never fetched directly.
  **Also excluded from the checker's `--source` forcing as of the same commit.**
- **CME/CBOE/NYSE/NASDAQ ohlcv_1m + ohlcv_1s (this doc's actual scope, 8 of the 12)**: genuinely reach the live
  Databento SDK call and return 0 rows with a clean, unexplained success.

## What was ruled out (file:line-confirmed)

1. **Not an early-return before the network call.** `download_batch_df`
   (`market_interface/adapters/tradfi/databento_enrichment.py:324-404`) has a guard at line 358-360 that returns early
   (and skips the "— %d records" log line entirely) when `_resolve_by_dataset` finds no instruments — this guard did NOT
   fire (the log line printed), and `TRADFI_DATABENTO_INSTRUMENTS` genuinely has real rows for all 4 venues
   (`unified-api-contracts/unified_api_contracts/registry/tradfi_instrument_universe.py`).
2. **Not a caught exception disguised as success.** The only paths from a failed/None SDK response to a log line are
   `_fetch_dbn_store` (`databento_fetch.py:515-546`, logs `"...failed [%s]: %s"` on any exception) and
   `_build_null_response_failure` → `log_event("ADAPTER_FETCH_FAILED", ...)` (`databento_fetch.py:244`) on a `None`
   return. Neither pattern appears anywhere in the full run.log for any of the 4 venues.
3. **Not the billing/lookback allowlist guard.** `_fetch_timeseries_range` (`databento_fetch.py:141-200`) gates the real
   SDK call (`self.base_client.client.timeseries.get_range(...)`, line 188) on
   `assert_databento_request_allowed(dataset, schema, start_date_str)` (line 175,
   `unified-api-contracts/.../databento_subscription_allowlist.py:228-243`) — this guard raises loudly (fail-closed)
   when it fires; it did not (no "failed" log). 2026-07-09 is well inside the L0 16-year free window for
   `ohlcv-1s`/`ohlcv-1m` (`databento_subscription_allowlist.py:90-95`).
4. **Not an IS_TEST_RUN artifact.** Zero references to `IS_TEST_RUN` anywhere in
   `databento_adapter.py`/`databento_fetch.py`/`databento_enrichment.py`/`databento_base_client.py` — it only gates GCS
   bucket resolution elsewhere in MTDS, never the Databento client or a mock/DRY_RUN path.
5. **Not the instrument-preflight fallback mismatching symbols.** `_VENUES_NEEDING_INSTRUMENT_PREFLIGHT`
   (`engine/orchestrator/preflight.py:141-150`) explicitly EXCLUDES TradFi/Databento venues by design comment
   ("TradFi/Databento (UAC registry)") — `instrument_ids` reaches `download_batch_df` unfiltered (`None`) for these
   venues, so a stale/wrong sampled instrument_id from the smoke check itself is ruled out too.
6. **Not a degraded/placeholder API key.** `databento_base_client.py:172-232,573-611` resolves the real key from Secret
   Manager with a TTL cache — consistent with the confirmed "API keys validated" log line; nothing here silently falls
   back to a placeholder.

## What's left: a genuine live-API empty response

Every local guard is ruled out. The SDK call at `databento_fetch.py:188` genuinely executed and `dbn_store.to_df()`
(`databento_fetch.py:589`, via `_iterate_dbn_chunks`) genuinely yielded zero rows — a real HTTP-200 round-trip with an
empty (but not erroring) result. This fired **identically and simultaneously** across CME/CBOE/NYSE/NASDAQ, which argues
for one systemic cause rather than 4 independent "no trading that day" coincidences (implausible on a Thursday for all 4
major US exchanges at once).

Two live-API-level hypotheses remain, NOT distinguishable from static code alone:

- **(i) Entitlement/date-window edge**: the account's actual live Databento subscription doesn't cover 2026-07-09
  despite the local allowlist code believing the L0 window is 16 years.
- **(ii) Symbol-resolution failure**: the requested parent/raw symbols (`ES.FUT`, etc., `stype_in="parent"`) don't
  resolve to any `instrument_id` for that specific day (e.g. a stale/rolled contract mapping) — Databento's SDK is
  documented to silently drop non-resolving symbols under `map_symbols=True` rather than erroring.

## Recommended next step (not attempted in this pass — needs live API access)

Run a live diagnostic outside the smoke-check path:

```python
client.symbology.resolve(
    dataset="GLBX.MDP3", symbols=["ES.FUT"], stype_in="parent", stype_out="instrument_id",
    start_date="2026-07-09", end_date="2026-07-10",
)
```

An empty mapping back would confirm hypothesis (ii) definitively; a non-empty mapping combined with the real `get_range`
call still returning zero rows would point at (i) instead. Separately, add explicit "zero-but-not-null" instrumentation
right after the SDK call in `_fetch_dbn_store` (`databento_fetch.py:528-538`) or `_fetch_timeseries_range`
(`databento_fetch.py:182-200`) — log the returned `DBNStore.metadata` (symbol mappings, echoed `start`/`end`) whenever
`to_df()` yields zero rows, and emit a distinct structured event (e.g. `DATABENTO_EMPTY_BUT_VALID`) with
`dataset`/`schema`/`symbols`/`start_str`/`end_str` so this class of failure is greppable and distinguishable from an
honest "no trading that day" result going forward.

## Progress log

- 2026-07-12: Filed from the `data_pipeline_e2e_check_2026_07_10.md` TradFi OHLCV re-verification round. Full
  local-guard elimination completed via static code trace; live-API root cause (entitlement vs. symbol-resolution)
  requires a live diagnostic not run in this pass — diagnosis handoff only, no fix attempted.
