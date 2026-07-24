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
  diagnostic (`client.symbology.resolve(...)`) is needed to confirm which. RESOLVED 2026-07-14
  (market-tick-data-service@69d226dc): that original narrowing was WRONG — the SDK was never called on the smoke-check
  path at all. `_apply_instrument_filter` could not match the smoke-checker's raw dated-contract `--instrument-ids`
  ('ESM26'/'VXU26') against curated parent symbols ('ES.FUT') or exchange_codes ('ES'), so `by_dataset` collapsed to
  `{}` before the fetch loop; entitlement/symbology hypotheses moot. Production backfills (no --instrument-ids) were
  always immune."
status: resolved
nature: notes
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [tradfi, databento, ohlcv, adapter-bugs, silent-empty, smoke-test, data-correctness]
related:
  [
    ../data_pipeline_e2e_check_2026_07_10.md,
    /plans/archive/issues/tradfi_manifest_row_loss_regression_2026_07_12.md,
    /plans/archive/issues/tradfi_manifest_cf4_source_and_cf7_phantom_gaps_2026_07_07.md,
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
resolved_by: market-tick-data-service@69d226dc
locked_by:
execution_scope: local-only
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.7
assigned_role: data_engineering
drift_direction: unknown
depends_on: []
---

# TradFi Databento OHLCV — silent zero-row success, no local guard involved

## RESOLVED 2026-07-14 — root cause: the SDK was NEVER called; the filter ate the request

**Fixed in market-tick-data-service@69d226dc.** The "clean 0-record success" was never a vendor-API mystery — the live
Databento SDK call was **never made** on the smoke-check path. The actual chain:

1. `scripts/pipeline_e2e_check.py` falls back to `scripts/smoke_matrix.py`'s `_REPRESENTATIVE_SYMBOL` map, which
   supplies a **raw dated-contract symbol** as `--instrument-ids` — `"ESM26"` for CME/NYSE/NASDAQ and a
   `_resolve_current_cboe_vx_symbol()`-derived `"VX<M><YY>"` (e.g. `"VXU26"`) for CBOE.
2. `_apply_instrument_filter()` (`market_tick_data_service/market_interface/adapters/tradfi/databento_enrichment.py`)
   only matched a caller-supplied id against a curated def's parent `symbol` (`"ES.FUT"`) or exact `exchange_code`
   (`"ES"`). A dated-contract symbol (`"ESM26"`) matches **neither**, so `by_dataset` collapsed to `{}`.
3. With `by_dataset == {}`, the fetch loop in `download_batch_df` never iterates — zero `_fetch_and_stream_chunks`
   calls, zero SDK calls — and the unconditional `"DatabentoAdapter.download_batch_df: %s %s — %d records"` log line
   prints "— 0 records" as a clean success.

**Both live-API hypotheses (i entitlement, ii symbology) are therefore moot** — they were already directly ruled out by
the 2026-07-13 live diagnostic below (parent-symbol `get_range` returned 1,628 real rows for 2026-07-09), and the true
discrepancy vs. production was exactly the "mvp_mode-like filter unexpectedly narrowing defs to zero" family that entry
predicted: an instrument_ids filter, not the dataset bucket.

**Production backfills are immune**: they pass no `--instrument-ids`, so `_apply_instrument_filter` never runs — this
bug only broke the smoke-checker's diagnostic accuracy (false-negative "0 rows").

Fix (additive-only, market-tick-data-service@69d226dc):

- `_dated_contract_root()` + `_FUTURES_MONTH_CODES` in `databento_enrichment.py`: parses ROOT+MONTHCODE+1-3-digit-year
  shapes (`"ESM26"`→`"ES"`, `"VXU26"`→`"VX"`); `_apply_instrument_filter` now also accepts a curated symbol whose
  `exchange_code` matches a dated contract's root — a strict superset of the old matching (exact symbol/exchange_code
  matches cannot regress).
- Hardening: `download_batch_df` now logs a WARNING when a non-empty pre-filter `by_dataset` narrows to `{}`, naming the
  dropped instrument_ids and the available curated symbols — this silent-empty class can never be invisible again.
- Tests: `tests/market_interface/adapters/tradfi/test_databento_instrument_filter.py` (11 tests: parent-symbol match,
  exchange_code match, ESM26/VXU26 dated-root matches, non-matching id still filters to empty, warning-path regression).
- Repro (repo `.venv`, real CME/CBOE registry inputs): BEFORE — `instrument_ids=["ESM26"]` → 0 symbols matched,
  `by_dataset={}`; AFTER — 2 symbols (`ES.FUT`, `ES.OPT`) on `GLBX.MDP3`. CBOE `["VXU26"]`: BEFORE 0 → AFTER 1 (`VX.FUT`
  on `XCBF.PITCH`).

**Correction to an earlier side-claim**: the diagnosis pass's side-claim that "CME has zero manifest rows ever" was
**REFUTED** by the orchestrator against the live manifest (CME: 2,430,317 rows, 1,077,959 captured as of 2026-07-14). Do
not propagate that claim.

**Residual note**: the smoke-checker false-negative is fixed; real production tradfi gaps are tracked elsewhere (OOM
completion run, fleet drain).

## Context

`data_pipeline_e2e_check_2026_07_10.md`'s earlier triage round found TradFi OHLCV shards were never even attempting a
fetch (`ValueError: --source databento|massive is REQUIRED`) and fixed it (deployment-service@29561c4,
market-tick-data-service@42a55bc — `--source` now correctly plumbed through the launcher and the checker). A
re-verification of all 12 affected shards for day=2026-07-09 confirmed the fix works (DatabentoAdapter now genuinely
engages) but **all 12 still write zero parquet rows**. Splitting the 12:

- **ICE** (ohlcv_1m): registered in `umi_tick_provider._DATABENTO_VENUES` but has zero rows in
  `TRADFI_DATABENTO_INSTRUMENTS` — Yahoo-DXY-only, IFUS.IMPACT explicitly removed per
  `/codex/02-data/tradfi-databento-sourcing-ssot.md`. `--source databento` is a silent no-op for it (early-return before
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
- 2026-07-13: Picked up uncommitted work left by a crashed prior session (API server error, not a code bug) — two real
  diffs in `market-tick-data-service`. Completed and evaluated both:
  1. **`DatabentoBaseClient._resolve_api_key_for_index` secret-name fix — real bug, but NOT the root cause of this
     issue.** The old code unconditionally requested `{prefix}-{key_index}` (e.g. `databento-api-key-1`) from Secret
     Manager even in single-key mode (`use_multi_key_rotation=False`, the default since the 2026-06-18 subscription
     cutover, where only the bare `databento-api-key` is provisioned) — verified live via
     `gcloud secrets describe databento-api-key-1 --project=central-element-323112` → `NOT_FOUND`, vs.
     `databento-api-key` → present. This is a genuine, independently-correct bug (confirmed consistent with
     `DatabentoClientConfig.secret_name`'s existing, correct branch on `use_multi_key_rotation` — the two were simply
     out of sync) and was finished + tested (3 new tests in
     `tests/market_interface/unit/test_databento_key_cache_and_config.py::TestResolveApiKeyForIndex`). **However, full
     static trace proves this method is DEAD CODE on the TradFi OHLCV production fetch path**: the real key comes from
     `ApiKeyReloader` → UTL `validate_api_keys_for_venues` → UAC
     `DATA_SOURCE_TO_SECRET["databento"] = "databento-api-key"` (bare name — a completely separate resolution path,
     which is why "API keys validated for 1 data source(s)" appeared in the original run.log) → threaded explicitly
     through `TickDataHandler._resolve_fetch_params` → `process_ticks(api_keys=...)` →
     `venue_fetch._resolve_api_key(venue, api_keys)` → `_route_databento` → `DatabentoAdapter(api_key=<real_key>)` →
     `DatabentoBaseClient.__init__(api_key=<real_key>)` → `self._api_key` is truthy, so the `.api_key` property
     short-circuits at `if self._api_key: return self._api_key` and **never calls `_resolve_api_key_for_index`**.
     Confirmed empirically, not just by code-reading: after shipping this fix, a real VM re-verification
     (`pipeline_e2e_check.py --day 2026-07-09 --asset-group TRADFI --venue CME --data-types ohlcv_1m --legs force --project central-element-323112`)
     still shows CME ohlcv_1m writing **0 parquet rows** for day=2026-07-09 (report:
     `plans/audit/results/data_pipeline_e2e_check_mtds_2026_07_09.md`, status=failed,
     `no_parquet_under:gs://market-data-tick-tradfi-test-central-element-323112/.../venue=CME/`). Shipped anyway as an
     honest, separately-labeled fix (real latent bug for any future caller that doesn't pre-supply an explicit key, e.g.
     a bare `DatabentoBaseClient`/instruments-service consumer) — NOT bundled with or claimed to resolve this issue.
  2. **`DATABENTO_EMPTY_BUT_VALID` observability (the doc's own "Recommended next step") — shipped, root cause still
     open.** Added `_emit_empty_but_valid()` in `databento_fetch.py`, wired into `_fetch_and_stream_chunks` to fire
     whenever `failure is None and rows_emitted == 0` — logs `DBNStore.metadata` (mapped-symbol count, echoed start/end,
     partial/not_found) and emits a structured `DATABENTO_EMPTY_BUT_VALID` event, so this failure class is greppable
     going forward and distinguishable from an honest "no trading that day" result. Covered by a new regression test
     (`tests/unit/test_databento_path_streaming.py::test_zero_row_response_emits_databento_empty_but_valid`).
  - **Net effect at that point: the root cause was still open.** Hypotheses (i) entitlement/date-window edge and (ii)
    symbol-resolution failure (both from the original filing) remained untested.
- 2026-07-13 (same day, follow-up): **Ran the recommended live diagnostic directly — BOTH original hypotheses (i) and
  (ii) are now RULED OUT, and the real cause is narrower than either.** Using the exact same `DatabentoBaseClient`
  construction the production code uses (bare `databento-api-key` secret, not the dead-code path above):
  1. `client.symbology.resolve(dataset="GLBX.MDP3", symbols=["ES.FUT"], stype_in="parent", stype_out="instrument_id", start_date="2026-07-09", end_date="2026-07-10")`
     — returned a full, real mapping: 39 real CME contract instrument_ids (`ESZ7`→`17740`, `ESZ6`→`10252`, etc.),
     `not_found: []`, `partial: []`, `status: 0`, `message: 'OK'`. **Hypothesis (ii) is RULED OUT** — `ES.FUT` (the
     exact `raw_symbol`/`stype_in` pair `TRADFI_DATABENTO_INSTRUMENTS`'s CME entry declares,
     `tradfi_instrument_universe.py:89`) resolves fine.
  2. Called
     `client.timeseries.get_range(dataset="GLBX.MDP3", schema="ohlcv-1m", symbols=["ES.FUT"], stype_in="parent", stype_out="instrument_id", start="2026-07-09", end="2026-07-10")`
     directly (the EXACT call shape `_fetch_timeseries_range`, `databento_fetch.py:141-200`, makes) — this returned
     **1628 real rows**, not zero. **Hypothesis (i) is RULED OUT** — the account's subscription genuinely has real
     OHLCV-1m data for CME/`ES.FUT` on 2026-07-09; there is no entitlement/date-window gap. Cross-checked against other
     days to rule out a fluke: 2026-06-09 → 3660 rows, 2025-07-09 → 1585 rows, 2026-07-05 (Sunday evening session) → 139
     rows, 2026-07-11 (Saturday, market closed) → 0 rows as expected — all consistent with a normal, healthy trading
     calendar. **2026-07-09 itself, via the parent symbol, has plenty of real data.**
  3. A single-contract sanity probe (`symbols=["ESZ7"], stype_in="raw_symbol"`, before broadening to the parent symbol)
     DID reproduce a genuine `BentoWarning: No data found` / 0 rows — but this was almost certainly the wrong diagnostic
     symbol (a far-dated/inactive-that-day specific contract, not the active front-month), not evidence of a real gap;
     the parent-symbol query (#2 above, matching what our registry+adapter actually request) proves real data exists.
  - **Conclusion: the root cause is neither (i) nor (ii) as originally framed — it must be a difference between this
    successful direct call and the EXACT runtime args production actually constructs**, since `_fetch_timeseries_range`
    (`databento_fetch.py:559-583`, verified by direct code read) passes through `dataset`/`schema`/`symbols`/`stype_in`
    unchanged from its caller, and `_resolve_by_dataset` (`databento_enrichment.py:233-271`) builds those args from
    `TRADFI_DATABENTO_INSTRUMENTS` the same way this diagnostic did — so on paper the production request SHOULD be
    identical to the one just proven to work. **Not yet found**: the actual discrepancy. Next step for whoever picks
    this up: either (a) add temporary DEBUG logging of the exact `dataset`/`schema`/`symbols`/`stype_in`/`start`/`end`
    values immediately before the real `get_range` call in a live re-run and diff them byte-for-byte against this
    diagnostic's working values, or (b) rely on the newly-shipped `DATABENTO_EMPTY_BUT_VALID` event's `metadata` payload
    (logs the DBNStore's own echoed request/mapping) the next time this VM check runs, which should make the actual
    production args visible without new instrumentation. Given real data is now proven to exist and be fetchable with
    the registry's own declared symbol shape, this is very likely a solvable, narrow bug (e.g. `schema` string mismatch,
    a `mvp_mode` filter unexpectedly narrowing `defs` to zero for the CME dataset bucket, or a subtly different
    `start`/`end` window) rather than an external/unfixable issue — re-prioritize accordingly (was P2, arguably still P2
    but now much closer to resolvable than "root cause unknown" implied).
- 2026-07-14: **RESOLVED — market-tick-data-service@69d226dc** (see the "RESOLVED 2026-07-14" section at the top for the
  full mechanism). The 2026-07-13 "narrow, solvable bug" prediction was exactly right: the discrepancy between the
  working direct diagnostic and the production smoke run was the `--instrument-ids` filter — `pipeline_e2e_check.py`
  (via `smoke_matrix.py`'s `_REPRESENTATIVE_SYMBOL`) passes raw dated-contract symbols ("ESM26"/"VXU26") that
  `_apply_instrument_filter` could not match against parent symbols ("ES.FUT") or exchange_codes ("ES"), collapsing
  `by_dataset` to `{}` BEFORE any SDK call — the SDK was never called on this path, so the entitlement/symbology
  hypotheses were moot from the start. Evidence: `- [x]` fix + matched-nothing warning + 11-test regression file shipped
  — market-tick-data-service@69d226dc; repro before/after: CME `["ESM26"]` 0→2 matched symbols (`ES.FUT`, `ES.OPT`),
  CBOE `["VXU26"]` 0→1 (`VX.FUT`) (repo `.venv`, real registry inputs); QG green (sentinel == HEAD at ship).
  Smoke-checker false-negative fixed; real production tradfi gaps tracked elsewhere (OOM completion run, fleet drain).
  CME zero-manifest side-claim refuted (live manifest: 2,430,317 rows / 1,077,959 captured, 2026-07-14).
