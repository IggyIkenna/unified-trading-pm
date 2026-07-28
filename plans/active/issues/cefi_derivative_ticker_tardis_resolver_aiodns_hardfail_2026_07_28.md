---
doc_type: issue
title:
  "DP_RUN_MOSTLY_EMPTY (DP-FETCH-009) CRITICAL for cefi derivative_ticker (158085/1410602 attempted_failed, 11.2%, Fresh
  0d) -- 75% is the already-tracked Tardis 403 concurrent-IP-lock backlog, but a genuinely FRESH 2026-07-28 batch of
  2,258 rows in the last 24h traces to TardisBaseClient/TardisStreamClient hard-failing on a missing aiodns install
  (uncaught 'Resolver requires aiodns library' RuntimeError landing raw as manifest error_reason) -- fixed by routing
  both through the existing make_resilient_connector() graceful-degrade helper"
summary: >-
  Escalation worker (data_pipeline_failure role) investigated a CRITICAL DP_RUN_MOSTLY_EMPTY (DP-FETCH-009) alert for
  asset_group=cefi data_type=derivative_ticker (158,085 attempted_failed of 1,410,602 attempted, 11.2%, labeled "Fresh
  -- newest attempted_failed activity 0d ago" per the 2026-07-28 staleness-labeling shipped in
  `cefi_high_attempted_failed_batch_cluster_2026_07_23.md`). A live, bounded, column-projected manifest read confirmed
  the count and split it: 75.0% (118,503 rows) is the ALREADY-TRACKED, ALREADY-ROOT-CAUSED Tardis concurrent-IP-lock 403
  historical backlog (`tardis_concurrent_ip_lockout_2026_07_12.md`), 19.6% (30,934) is the already-normalized
  `VENUE_FETCH_FAILED` bucket (no further action without run.log archaeology, per that doc's P3 todo) -- both are
  STATIC, not this alert's "Fresh" signal. The GENUINELY FRESH slice (2,258 rows, `attempted_at` clustered exactly
  2026-07-28T09:03:12Z, i.e. one automated sweep) breaks down: 1,733 rows `error_reason="(429, None, 'null', None,
  {'Content-Type'..."` (HYPERLIQUID, `pipeline_mode=batch_hyperliquid` -- a separate, NOT-yet-investigated mechanism,
  see Open Questions), and 290 rows (280 + 10 `UNCLASSIFIED:` variant) `error_reason="Resolver requires aiodns library"`
  (DERIBIT + other Tardis venues, `pipeline_mode=batch_tardis`). Traced the second signature to root cause:
  `TardisBaseClient.initialize_async_session()` and `TardisStreamClient.initialize_async_session()` both hard-construct
  `TCPConnector(resolver=AsyncResolver(), ...)` with no fallback -- when the deployed VM's venv lacks a working `aiodns`
  install, `AsyncResolver()` raises `RuntimeError("Resolver requires aiodns library")` uncaught, and
  `TardisAdapter._classify_tardis_error()`'s `classify_venue_error()` lookup returns `None` for this infra-level
  (non-venue-specific) message, so the raw exception text falls through directly into the manifest's `error_reason` and
  the whole per-symbol shard is recorded `attempted_failed`. This is the EXACT SAME failure mode already root-caused and
  fixed once before for the Solana LST-rates leg (`market_tick_data_service/_http_resolver.py`, 2026-07-22,
  `make_resilient_connector()`) -- that fix was never applied to these two Tardis clients. FIXED (this session):
  extended `make_resilient_connector()` to accept `**kwargs` (connection-pool tuning) and routed both Tardis clients
  through it, so a missing/broken `aiodns` now degrades to aiohttp's default resolver instead of failing the shard.
  Code: `market-tick-data-service` (see Todos for SHA).
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [data-correctness, attempted-failed, cefi, tardis, dns, aiodns, resolver, dp-fetch-009]
related:
  [
    /plans/active/issues/cefi_high_attempted_failed_batch_cluster_2026_07_23.md,
    /plans/archive/issues/tardis_concurrent_ip_lockout_2026_07_12.md,
    /plans/active/issues/cefi_threaded_resolver_dns_starvation_risk_2026_07_26.md,
    /plans/archive/issues/databento_default_executor_dns_starvation_risk_2026_07_17.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
created: 2026-07-28
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.15
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source:
  "POST /api/escalate wall_type=data_pipeline_failure, escalation agt-7a4d1d, DP_RUN_MOSTLY_EMPTY (DP-FETCH-009)
  CRITICAL, asset_group=cefi data_type=derivative_ticker, 158085/1410602 attempted_failed (11.2%), Fresh 0d"
last_updated: 2026-07-28
---

# CeFi derivative_ticker DP-FETCH-009 -- Tardis clients hard-fail without aiodns (fixed) + open HYPERLIQUID 429 question

## Alert as received

```
Event: DP_RUN_MOSTLY_EMPTY (DP-FETCH-009, CRITICAL), asset_group=cefi, data_type=derivative_ticker
158,085 attempted_failed of 1,410,602 attempted (ratio 11.2%; threshold abs>=500 or ratio>=10%)
Label: Fresh -- newest attempted_failed activity 0d ago
Description: "A backfill exited 0 / captured climbed but failed this batch invisibly."
```

## Method

Bounded, column-projected, filtered live read of
`gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet` via
`unified_trading_library.read_availability_index(bucket, columns=[...], filters=[("data_type","=","derivative_ticker"), ("capture_status","=","attempted_failed")])`
-- single-walk discipline, no full-corpus GCS listing. No manifest/GCS write. Confirmed 158,085 rows (exact match to the
alert).

## Split: static historical backlog vs genuinely fresh

| Slice                                                     |    rows | % of 158,085 | Status                                                                                    |
| --------------------------------------------------------- | ------: | -----------: | ----------------------------------------------------------------------------------------- |
| 403-family (`error_reason` contains "403")                | 118,503 |        75.0% | STATIC -- already-tracked Tardis concurrent-IP-lock backlog                               |
| `VENUE_FETCH_FAILED` (normalized label)                   |  30,934 |        19.6% | STATIC -- already-normalized, no further action without archaeology                       |
| `attempted_at` within last 24h (as of 2026-07-28T~09:15Z) |   2,258 |         1.4% | **FRESH** -- one automated sweep, `attempted_at` clustered exactly `2026-07-28T09:03:12Z` |

The 403-family (venue=DERIBIT 113,814 of 118,503) is the same population documented in
`cefi_high_attempted_failed_batch_cluster_2026_07_23.md` (that doc measured 16.9%/239,095 rows on 2026-07-23; today's
11.2%/158,085 is LOWER, consistent with ongoing partial recovery, not a fresh regression of that mechanism).
`VENUE_FETCH_FAILED` is the same already-normalized bucket that doc's P3 todo left as un-attributed. **Neither slice
needed a new investigation** -- this doc's actual contribution is the FRESH 2,258-row slice, which that prior
investigation's snapshot (2026-07-23) predates.

## Fresh slice (2,258 rows, `attempted_at` = 2026-07-28T09:03:12Z, one sweep)

| venue            | rows | pipeline_mode     |
| ---------------- | ---: | ----------------- |
| HYPERLIQUID      | 1796 | batch_hyperliquid |
| COINBASE-FUTURES |  159 | batch_tardis      |
| OKX-FUTURES      |  121 | batch_tardis      |
| BYBIT            |   50 | batch_tardis      |
| ASTER            |   50 | batch_aster       |
| BINANCE-FUTURES  |   46 | batch_tardis      |
| DERIBIT          |   26 | batch_tardis      |
| OKX              |   10 | batch_tardis      |

`error_reason` breakdown of the fresh slice:

| error_reason                                                       | rows | root cause                                                           |
| ------------------------------------------------------------------ | ---: | -------------------------------------------------------------------- |
| `(429, None, 'null', None, {'Content-Type'...` (truncated)         | 1733 | HYPERLIQUID -- **NOT investigated this session, see Open Questions** |
| `Resolver requires aiodns library`                                 |  280 | **ROOT-CAUSED + FIXED this session** (below)                         |
| `UNCLASSIFIED:404 GET https`                                       |  122 | not investigated (small, plausible transient)                        |
| `UNCLASSIFIED:UpstreamTimestampBiasError`                          |   50 | not investigated (existing writer clip path, `tardis_shared.py`)     |
| `'KPEPE'`/`'KFLOKI'`/`'KBONK'`/`'KNEIRO'`/`'KLUNC'`/`'KSHIB'`/etc. |  ~90 | not investigated (looks like per-symbol delisting/rename edge cases) |
| `UNCLASSIFIED:Resolver requires aiodns library`                    |   10 | same root cause as above, different code_token prefix                |

## Root cause (CONFIRMED, fixed) -- `Resolver requires aiodns library` (290 of 2,258 fresh rows, 12.8%)

`market_tick_data_service/market_interface/clients/tardis_base_client.py::initialize_async_session()` and
`market_tick_data_service/market_interface/clients/tardis_stream_client.py::initialize_async_session()` both constructed
their `aiohttp.TCPConnector` as:

```python
connector = TCPConnector(resolver=AsyncResolver(), limit=..., limit_per_host=..., ttl_dns_cache=300, force_close=False)
```

with NO try/except around `AsyncResolver()`. On a deployed VM whose venv lacks a working `aiodns` install,
`aiohttp.resolver.AsyncResolver()` raises `RuntimeError("Resolver requires aiodns library")` immediately at session init
-- before any HTTP request is even attempted. This propagates up through the per-symbol download coroutine
(`market_tick_data_service/market_interface/adapters/tradfi/tardis_batch_download.py`, which fans out CeFi's
per-underlying Tardis downloads despite living under the `tradfi/` package -- shared code) to
`TardisAdapter._classify_tardis_error(venue, exc)`:

```python
raw = str(exc).strip()  # "Resolver requires aiodns library" (no colon -> code_token = the whole string)
code_token = raw.split(":", 1)[0].strip()[:80] if raw else type(exc).__name__
classification = classify_venue_error(venue, code_token)
return classification.error_code if classification is not None else code_token
```

`classify_venue_error()` has no entry for this infra-level, non-venue-specific message, so it returns `None`, and the
raw exception text becomes the manifest's `error_reason` verbatim -- exactly what was observed. The whole per-symbol
shard is then written `attempted_failed`, even though NOTHING about the actual venue/instrument was tried (DNS
resolution failed before any request left the process).

**This is the identical failure class already root-caused and fixed once for a different leg**:
`market_tick_data_service/_http_resolver.py` (`make_resilient_connector()`, 2026-07-22) was built exactly for this --
prefer `AsyncResolver` opportunistically, degrade to aiohttp's default resolver on
`ImportError`/`RuntimeError`/`OSError` instead of raising. That fix was applied to the Solana LST-rates leg
(`cli/handlers/lst_rates_handler.py`) and two other handlers (`deribit_options_chain_handler.py`,
`oracle_prices_handler.py`), but never to `TardisBaseClient`/`TardisStreamClient` -- the two classes that actually
handle CeFi's (and TradFi's) Tardis per-symbol downloads. `cefi_threaded_resolver_dns_starvation_risk_2026_07_26.md`
(open, P3) flagged a RELATED-but-DIFFERENT gap (aster/hyperliquid clients still using the old `ThreadedResolver()` -- a
thread-starvation risk, not a hard-fail-on-missing-aiodns risk) and explicitly noted "aiodns is already a direct
dependency as of the Tardis fix" -- true in `pyproject.toml`, but declaring a dependency doesn't guarantee it's actually
importable on every deployed VM's built venv (the `_http_resolver.py` docstring documents exactly this gap from the
2026-07-22 LST-rates incident: a tarball-built venv omitted a declared dependency).

### Fix shipped this session

1. `market_tick_data_service/_http_resolver.py`: extended `make_resilient_connector()` to accept `**kwargs` and forward
   them to `TCPConnector(...)` on both the `AsyncResolver` and fallback paths, so callers needing connection-pool tuning
   (`limit`, `limit_per_host`, `ttl_dns_cache`, `force_close`) don't have to duplicate the resolver-fallback logic
   themselves.
2. `tardis_base_client.py` / `tardis_stream_client.py`: replaced the bare `TCPConnector(resolver=AsyncResolver(), ...)`
   construction with `make_resilient_connector(limit=..., limit_per_host=..., ttl_dns_cache=300, force_close=False)`.
3. Updated `tests/market_interface/unit/test_tardis_stream_client.py`'s `TestAsyncResolverWiring` (previously asserted a
   raw `AsyncResolver` instance was passed to `TCPConnector` directly -- now asserts each client requests the correct
   connection-pool kwargs from `make_resilient_connector`, since the resolver-fallback behavior itself is already
   covered by `tests/unit/test_http_resolver.py`).
4. Added two new regression cases to `tests/unit/test_http_resolver.py` covering the new `**kwargs` passthrough on both
   the `AsyncResolver`-available and fallback paths, plus renamed the existing RuntimeError test's message to the exact
   real-world string ("Resolver requires aiodns library") for clarity.

**What this does NOT do**: it does not retry the 290 historical rows already sitting in the manifest as
`attempted_failed` -- that is a normal idempotent backfill re-attempt (no code change needed), not tracked as a separate
todo here since it is the same "historical poisoned rows never retried" class already named in
`cefi_high_attempted_failed_batch_cluster_2026_07_23.md`'s own analysis. It also does not diagnose WHY the specific VM
that ran this 2026-07-28T09:03Z batch had a broken/missing `aiodns` install (declared in `pyproject.toml`,
`>=3.0.0,<5.0.0`) -- that would need identifying which VM/Cloud Run execution ran this batch and inspecting its actual
installed packages, out of scope for this manifest-level investigation.

## Open Questions (NOT investigated this session -- flagged, not claimed)

- **HYPERLIQUID `(429, None, 'null', None, {'Content-Type'...` (1,733 of 2,258 fresh rows, 76.8% -- the LARGER fresh
  signature, not chased this session)**: truncated tuple-shaped `error_reason` (looks like a raw response/args tuple
  string, not a classified label -- possibly the manifest column's max-length truncating a longer repr mid-dict). This
  is `pipeline_mode=batch_hyperliquid`, a DIFFERENT code path from the Tardis clients fixed above (HYPERLIQUID data
  under the cefi bucket does not go through `TardisBaseClient`). Did not identify which module constructs this exact
  error string, did not confirm whether it represents a genuine rate-limit exhaustion (no further fix needed beyond what
  already exists) or a leaked/unclassified raw-response repr (same "falls through `classify_venue_error()`" class as the
  fix above, needing its own targeted trace). **Worth a dedicated follow-up** given it is the majority of the fresh
  batch.
- **404/`UpstreamTimestampBiasError`/per-symbol-delisting tails (~262 rows)**: not investigated -- small enough to be
  ordinary transient/edge-case noise, not sized or attributed further.
- Did not verify which specific VM or Cloud Run execution produced the 2026-07-28T09:03:12Z batch, nor whether its
  venv's `aiodns` install was genuinely absent/broken vs. some other resolver-init failure sharing the same message.

## Todos

- [x] ✅ [CODE] P1. **DONE 2026-07-28 (data_pipeline_failure escalation, agt-7a4d1d) —
      `market-tick-data-service@6a067cf1`.** Routed `TardisBaseClient.initialize_async_session()` and
      `TardisStreamClient.initialize_async_session()` through the existing `make_resilient_connector()` graceful-degrade
      helper (extended with `**kwargs` passthrough) instead of hard-constructing
      `TCPConnector(resolver=AsyncResolver())` with no fallback. `quality-gates.sh` green (7320 passed, 0 failed, 80.42%
      coverage); regression tests updated (`TestAsyncResolverWiring` now asserts connection-pool kwargs reach
      `make_resilient_connector` instead of asserting a raw `AsyncResolver` instance) + 2 new `test_http_resolver.py`
      cases for the `**kwargs` passthrough. Shipped via quickmerge, landed on `live-defi-rollout`.
- [ ] [DATA] P2. Trace the HYPERLIQUID `(429, None, 'null', None, {'Content-Type'...` fresh signature (1,733 rows, the
      LARGER share of the 2026-07-28 fresh batch) to its actual construction site and root cause -- confirm whether it
      is a genuine rate-limit exhaustion (no code fix needed, just a heavier backfill wave hitting HYPERLIQUID's limits)
      or a leaked/unclassified raw-response repr needing the same `classify_venue_error()` fallthrough fix applied
      above.
- [ ] [DATA] P3. If pursued: retry the 290 historical `Resolver requires aiodns library` rows (now fixed going forward,
      not retroactively) via a normal idempotent backfill re-attempt -- no code change needed, purely operational.

## Progress Log

- **2026-07-28 (data_pipeline_failure escalation worker, escalation agt-7a4d1d):** Diagnosed and fixed the
  `Resolver requires aiodns library` root cause (see above); code shipped, quality gates verified green. Flagged the
  HYPERLIQUID 429 signature and small tails as open questions for a follow-up, not chased further this session per the
  one-shot escalation scope.
