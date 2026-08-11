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
status: resolved
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [data-correctness, attempted-failed, cefi, tardis, dns, aiodns, resolver, dp-fetch-009]
related:
  [
    /plans/archive/issues/cefi_high_attempted_failed_batch_cluster_2026_07_23.md,
    /plans/archive/issues/tardis_concurrent_ip_lockout_2026_07_12.md,
    /plans/archive/issues/cefi_threaded_resolver_dns_starvation_risk_2026_07_26.md,
    /plans/archive/issues/databento_default_executor_dns_starvation_risk_2026_07_17.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
created: 2026-07-28
author: unknown
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
last_updated: 2026-08-03
context_scope:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /plans/archive/issues/cefi_high_attempted_failed_batch_cluster_2026_07_23.md,
    /plans/archive/issues/dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md,
    market-tick-data-service/market_tick_data_service/adapters/hyperliquid_s3.py,
    market-tick-data-service/market_tick_data_service/_http_resolver.py,
  ]
---

> **ARCHIVED 2026-08-10** — all 10 todos done. Root causes #1 (aiodns @6a067cf1), #2 (HYPERLIQUID 429 @6c6fab03), #3
> (K*-symbol KeyError @6c6fab03) fixed and shipped; VM cycled (2026-08-06, verified); Follow-ups
> fetch_l2_book/book_snapshot_5 case-sensitivity hypothesis CONFIRMED + FIXED (@a8e98742). All 6 k-prefixed symbols now
> resolve case-insensitively against HL's /info universe before S3 key construction. Successor: none — all root causes +
> follow-ups closed.

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

| error_reason                                                       | rows | root cause                                                         |
| ------------------------------------------------------------------ | ---: | ------------------------------------------------------------------ |
| `(429, None, 'null', None, {'Content-Type'...` (truncated)         | 1733 | **ROOT-CAUSED + FIXED session 2** (agt-27e235, below)              |
| `Resolver requires aiodns library`                                 |  280 | **ROOT-CAUSED + FIXED session 1** (agt-7a4d1d, below)              |
| `UNCLASSIFIED:404 GET https`                                       |  122 | not investigated (small, plausible transient)                      |
| `UNCLASSIFIED:UpstreamTimestampBiasError`                          |   50 | not investigated (existing writer clip path, `tardis_shared.py`)   |
| `'KPEPE'`/`'KFLOKI'`/`'KBONK'`/`'KNEIRO'`/`'KLUNC'`/`'KSHIB'`/etc. |  ~90 | **ROOT-CAUSED + FIXED session 2** -- was a case bug, NOT delisting |
| `UNCLASSIFIED:Resolver requires aiodns library`                    |   10 | same root cause as above, different code_token prefix              |

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

## Root cause #2 (CONFIRMED, fixed) -- HYPERLIQUID `(429, None, 'null', ...)` raw-tuple leak (1,733 of 2,258 fresh rows, 76.8%)

Second escalation dispatch (agt-27e235) for the SAME re-firing `DP_RUN_MOSTLY_EMPTY` alert (a duplicate/re-fire of the
identical CRITICAL condition session 1 responded to, per the "static manifest-cell signal" behavior documented in
`cefi_high_attempted_failed_batch_cluster_2026_07_23.md`) -- picked up the two Open Questions session 1 (agt-7a4d1d)
explicitly left unchased, rather than re-doing session 1's already-complete aiodns work.

`data_type=derivative_ticker` for HYPERLIQUID is sourced from `hyperliquid_s3.py::fetch_asset_ctxs()` (S3
`hyperliquid-archive/asset_ctxs`), which falls back to `_fetch_funding_via_rest()` (the `hyperliquid-python-sdk`'s
`Info.funding_history()`, a synchronous `requests`-based call, NOT an `aiohttp`/Tardis code path) on any S3 read
failure. The SDK's own `hyperliquid/utils/error.py`:

```python
class ClientError(Error):
    def __init__(self, status_code, error_code, error_message, header, error_data=None):
        self.status_code = status_code
        ...  # never calls super().__init__(...) with a formatted message
```

`BaseException.__new__` still captures the raw constructor args as `self.args` regardless, so Python's default
`Exception.__str__` renders the positional-args TUPLE verbatim. `_handle_exception` in the SDK's `api.py` raises
`ClientError(429, None, response.text, None, response.headers)` on a 429 whose body is literally `"null"` -- so
`str(exc) == "(429, None, 'null', None, {'Content-Type': ...})"`, EXACTLY matching (byte-for-byte, before the manifest's
80-char truncation) the observed `error_reason`. This propagates uncaught out of `_fetch_funding_via_rest` (not
`OSError`/`ValueError`/`RuntimeError`, so not caught by its existing except clause) through `fetch_asset_ctxs`, and
`onchain_perp_batch_handler.py::_record_failed`'s `code_token = str(error).split(":", 1)[0].strip()[:80]` extracts the
garbage pre-first-colon fragment (`"(429, None, 'null', None, {'Content-Type'"`) -- exactly the observed manifest text.
Confirmed the correct manifest SEMANTICS were never wrong (this uncaught-exception path correctly lands as
`attempted_failed`, never a false `empty_confirmed`) -- only the `error_reason` TEXT was unclassifiable garbage.

**Confirmed this is NOT a dead end**: `unified-api-contracts` ALREADY has a `classify_venue_error` registry entry for
`hyperliquid` + `"429"` (`unified_api_contracts/canonical/crosscutting/errors/onchain_perps.py`:
`retry=True, action=ErrorAction.RETRY, desc="HTTP rate limit exceeded"`) that would fire correctly if `code_token` were
the bare string `"429"` instead of the raw tuple fragment.

**Fix**: `hyperliquid_s3.py::_fetch_funding_via_rest` now catches `(ClientError, ServerError)` from
`hyperliquid.utils.error` and re-raises
`RuntimeError(f"{status}: Hyperliquid REST API error fetching funding_history for {coin}")` -- `code_token` after the
`:` split becomes the bare status code (`"429"`, `"500"`, etc.), matching the EXISTING registry entries for all 5
already-declared hyperliquid HTTP codes (429/500/503/400/401), not just this one. Preserves the correct
`attempted_failed` classification (the exception still propagates); only the text is now clean.

## Root cause #3 (CONFIRMED, fixed) -- HYPERLIQUID K\*-symbol bare `KeyError` (~90 of 2,258 fresh rows, ~4%)

The `'KPEPE'`/`'KBONK'`/`'KFLOKI'`/`'KNEIRO'`/`'KLUNC'`/`'KSHIB'` rows are Python's default `KeyError.__str__` (wraps
the missing key in `repr()`) -- a bare, uncaught `KeyError`, same failure CLASS as root cause #2 (unclassified exception
text reaching the manifest verbatim) but a DIFFERENT and more consequential mechanism: **these 6 symbols fail on EVERY
attempted date** (observed `attempted_at` spanning 2023-05-12 through 2026-07-28 in this same investigation's broader
manifest read), not just this fresh batch -- a permanent, 100%-reproducible capture gap, not a transient blip. The prior
session's "looks like per-symbol delisting/rename edge cases" guess was WRONG; these are live, actively-traded
HYPERLIQUID perpetuals.

**Root cause**: HYPERLIQUID redenominates extremely-high-supply meme coins with a lowercase `"k"` prefix (kilo, e.g.
`kPEPE` = 1000 PEPE per contract unit) -- confirmed live:
`instruments-store-cefi-prd-central-element-323112/prod/ catalog.parquet` stores these 6 instrument_ids UPPERCASED
(`HYPERLIQUID:PERPETUAL:KPEPE-USD@LIN`, verified via a direct catalogue read, not just inferred). The
`hyperliquid-python-sdk`'s `Info` client does a case-SENSITIVE dict lookup (`hyperliquid/info.py:423`,
`coin = self.name_to_coin[name]`, populated from HL's real `/info` universe at `Info. __init__`) -- passing
catalogue-derived `"KPEPE"` raises `KeyError('KPEPE')` since only `"kPEPE"` (real mixed case) is a key. This is a
FUNCTIONAL gap, not just a cosmetic one: these 6 symbols have never successfully fetched via this path, for any date,
ever. (Did not trace WHERE in the catalogue-build pipeline -- instruments-service, a different repo -- the uppercasing
first happens; out of scope for this MTDS-repo fix. The fix below is robust to that regardless of cause, since it
resolves case at the point of actual use rather than requiring the upstream catalogue to be case-correct.)

**Fix**: `_fetch_funding_via_rest` now resolves `coin` case-insensitively against the SDK's own freshly-populated
`info.name_to_coin` (built from HL's real universe on every `Info(...)` construction, already happening -- no extra
network cost) before calling `funding_history()` -- mirrors the case-insensitive match `_parse_asset_ctxs_csv` (same
file) already does for the S3 CSV path. A coin still unresolvable even case-insensitively (genuinely unknown/delisted)
now re-raises a clean `RuntimeError` (defense-in-depth) instead of leaking the bare `KeyError` repr.

**Verification**: `market-tick-data-service` `.venv/bin/python` script directly querying
`instruments-store-cefi-prd-central-element-323112/prod/catalog.parquet` confirmed the 6 uppercased instrument_ids live;
`hyperliquid/info.py` source inspection confirmed the case-sensitive `name_to_coin[name]` lookup at the exact line
implicated. 5 new regression tests added (`TestFetchFundingViaRestErrorHandling` in `test_hyperliquid_s3_coverage.py`)
covering case-insensitive resolution, already-correct-case passthrough, `ClientError`/`ServerError` reclassification,
and the residual-KeyError defense-in-depth path.

## Open Questions (NOT investigated -- flagged, not claimed)

- **404/`UpstreamTimestampBiasError`/small tails (~262 rows, BINANCE-FUTURES/BYBIT/DERIBIT/ASTER)**: not investigated in
  either session -- small enough to be ordinary transient/edge-case noise, not sized or attributed further. Worth a
  follow-up only if pursued for completeness, not urgent given their small share of the fresh batch.
- Did not verify which specific VM or Cloud Run execution produced the 2026-07-28T09:03:12Z batch, nor whether its
  venv's `aiodns` install was genuinely absent/broken vs. some other resolver-init failure sharing the same message.
- Did not trace WHERE in the instruments-service catalogue-build pipeline the HYPERLIQUID k-prefixed coins get
  uppercased (a different repo; the MTDS-side fix above is robust regardless of that cause, but the upstream bug -- if
  it IS a bug and not an intentional catalogue-wide uppercase-everything convention -- still exists and could affect
  other consumers of the same catalogue field).
- **HYPOTHESIS, NOT VERIFIED**: the same uppercased `coin`/`symbol` also feeds `HyperliquidS3Downloader.fetch_l2_book`
  (`book_snapshot_5`) and `fetch_trades` (`trades`) -- `fetch_l2_book` builds its S3 object key directly as
  `f"market_data/{date}/{hour}/l2Book/{coin}.lz4"`, and S3 object keys are case-sensitive, so if HL's real archive keys
  use the real mixed case (`l2Book/kPEPE.lz4`) the uppercased request (`l2Book/KPEPE.lz4`) would 404 on every hour for
  these same 6 symbols -- a SILENT absence (routed through `_log_l2_book_all_absent`'s
  honest-`EXPECTED_SOURCE_DELIVERY_ LAG`-vs-genuinely-empty branching, not a loud failure) rather than the loud
  `attempted_failed` this doc's derivative_ ticker fix addresses. Different `data_type`, different symptom shape, NOT
  covered by this session's fix (only `_fetch_funding_via_rest` was touched) -- flagged as a plausible follow-up, not
  chased (out of this alert's `data_type=derivative_ticker` scope), not confirmed against the live manifest.

## Todos

- [x] ✅ [CODE] P1. **DONE 2026-07-28 (data_pipeline_failure escalation, agt-7a4d1d) —
      `market-tick-data-service@6a067cf1`.** Routed `TardisBaseClient.initialize_async_session()` and
      `TardisStreamClient.initialize_async_session()` through the existing `make_resilient_connector()` graceful-degrade
      helper (extended with `**kwargs` passthrough) instead of hard-constructing
      `TCPConnector(resolver=AsyncResolver())` with no fallback. `quality-gates.sh` green (7320 passed, 0 failed, 80.42%
      coverage); regression tests updated (`TestAsyncResolverWiring` now asserts connection-pool kwargs reach
      `make_resilient_connector` instead of asserting a raw `AsyncResolver` instance) + 2 new `test_http_resolver.py`
      cases for the `**kwargs` passthrough. Shipped via quickmerge, landed on `live-defi-rollout`.
- [x] ✅ [DATA] P2. **DONE 2026-07-28 (data_pipeline_failure escalation, agt-27e235) —
      `market-tick-data-service@6c6fab03` (verified ancestor of `origin/live-defi-rollout`).** Traced the HYPERLIQUID
      `(429, None, 'null', None,     {'Content-Type'...` fresh signature to `hyperliquid_s3.py::_fetch_funding_via_rest`
      -- a LEAKED/UNCLASSIFIED raw-response repr (the SDK's `ClientError` never formats a message), not a
      rate-limit-exhaustion dead end. See Root cause #2 above. `quality-gates.sh` green (7337 passed, 0 failed).
- [x] ✅ [DATA] P2. **DONE 2026-07-28 (data_pipeline_failure escalation, agt-27e235) — same commit
      `market-tick-data-service@6c6fab03`.** Traced the `'KPEPE'`/`'KBONK'`/etc. bare-`KeyError` signature (~90 fresh
      rows, but a PERMANENT gap across every date ever attempted for these 6 symbols) to a case-sensitivity bug: the IS
      catalogue stores HYPERLIQUID's k-prefixed meme coins uppercased, but the SDK's coin lookup is case-sensitive. See
      Root cause #3 above. Corrects the prior session's "delisting/rename" guess.
- [x] ✅ [DATA] P3. If pursued: retry the 290 historical `Resolver requires aiodns library` rows (now fixed going
      forward, not retroactively) via a normal idempotent backfill re-attempt -- no code change needed, purely
      operational. — **DISPOSITION 2026-08-05 (slot-9 data_engineering):** Both fix commits
      (`market-tick-data-service@6a067cf1` aiodns, `@6c6fab03` HYPERLIQUID) verified ancestors of
      `origin/live-defi-rollout`. No new aiodns rows since the 2026-07-28 sweep — the 290 are static. Retrying requires
      a VM launch (`launch-cefi-sharded-backfill.sh` or `launch-cefi-forward-poll.sh`), which is infra craft (not
      data_engineering). The 290 rows (0.18% of total derivative_ticker attempted_failed) don't warrant a dedicated VM
      launch — fold into the next cefi backfill sweep that naturally covers the affected Tardis venues (DERIBIT,
      COINBASE-FUTURES, OKX-FUTURES, BYBIT, BINANCE-FUTURES, OKX) and dates (~2026-07-28). No code change needed (fix
      already shipped).
- [x] ✅ [DATA] P3. If pursued: retry the ~90 historical K\*-symbol rows (now fixed going forward via the
      case-insensitive resolution, not retroactively) -- same "normal idempotent backfill re-attempt" shape as P3, not
      urgent. — **DISPOSITION 2026-08-05 (slot-10 data_engineering):** Fix commit `market-tick-data-service@6c6fab03`
      verified present in source (`_resolve_hyperliquid_coin_case` + `_reraise_hyperliquid_sdk_error` in
      `hyperliquid_s3.py`) and MTDS HEAD is ancestor of `origin/live-defi-rollout`. The ~90 K\*-symbol rows
      (KPEPE/KBONK/KFLOKI/KNEIRO/KLUNC/KSHIB) are HYPERLIQUID `derivative_ticker` `attempted_failed` in the manifest —
      no new rows since the 2026-07-28 sweep (static). Retrying requires a backfill VM launch with `--force` on these 6
      instruments (`launch-cefi-hl-aster-historical-backfill.sh` is the target launcher, HYPERLIQUID-specific, not
      subject to the Tardis concurrency cap), which is infra craft (not data_engineering). The 6 symbols' date range
      spans ~2023-05-12 through 2026-07-28 (~3y, ~90 instrument-date shards). No code change needed (fix already
      shipped).
- [x] ✅ [DATA] P3. **DONE 2026-08-05 (slot-15 data_engineering) — investigated, no code change needed.** Small residual
      tails (~262 rows: `UNCLASSIFIED:404 GET https` on BINANCE-FUTURES/BYBIT/DERIBIT,
      `UNCLASSIFIED:UpstreamTimestampBiasError` on ASTER) — both signatures are static and already handled by
      currently-shipped code going forward. See Progress Log for full investigation findings.
- [x] ✅ [DOCS] P3. **DONE 2026-07-29 (data_pipeline_failure escalation, agt-0df274) — `unified-trading-pm` (this
      commit).** Appended the missing `DP-FETCH-009` row to `codex/05-infrastructure/data-pipeline-alerts.registry.yaml`
      and `.md` so the SSOT matches what both prior escalations already shipped/referenced.
- [x] ✅ [INFRA] P1. **DONE 2026-08-06 (slot-9, backend_engineer, task
      cefi_derivative_ticker_tardis_resolver_aiodns_hardfail-006) — VM cycle already executed by another session before
      this dispatch arrived; verified complete.** New VM `mtds-live-cefi-consolidated-20260806-163414` (RUNNING, 17 MVP
      shards healthy per `ps aux`, `=== VM SETUP COMPLETE ===` at 2026-08-06T16:36:48Z); tarball SHA `55d88025` uploaded
      2026-08-06T16:31:19Z; `git merge-base --is-ancestor 6a067cf1 55d88025` = true AND
      `git merge-base --is-ancestor 6c6fab03 55d88025` = true (both fix commits confirmed ancestors of the deployed
      tarball). Old VM `mtds-live-cefi-consolidated-20260802-142543` DELETED (absent from
      `gcloud compute instances list`). No code change needed (all fixes already shipped). **RULED 2026-08-06
      (operator): approved, AO-dispatchable.** `[INFRA]` tag (was `[OPERATOR]`) — the diagnosis is not in question
      (root-caused, fix already shipped and correct); the gate was self-service SSH/delete access, not judgment. The
      additive-then-subtractive design (new VM up + verified healthy BEFORE the old one is deleted, shard-isolated
      writes so no corruption risk from briefly running both) is itself the safety mechanism — dispatch to a
      worker/session with `unified-trading-sa`-class access. **New finding (agt-829d55, 2026-08-03, slot-9): the
      numerator IS genuinely moving again — NOT the static backlog every prior dispatch found — and traces to a
      specific, currently-RUNNING live VM stuck on pre-fix code, not a new code bug.** A fresh, bounded,
      column-projected `read_availability_index` read (`data_type=derivative_ticker`, `capture_status=attempted_failed`)
      found 158,815 total rows (vs the 158,475-static reading every dispatch since agt-40f31f on 2026-07-30 confirmed) —
      the FIRST numerator movement in 4 days. Filtering to `written_at` within the last 24h found 1,821 fresh rows,
      1,730 of them `venue=HYPERLIQUID` (`pipeline_mode=batch_hyperliquid`) with `error_reason` EXACTLY matching the two
      signatures this doc's `market-tick-data-service@6c6fab03` fix already root-caused and fixed: 1,696 rows
      `"(429, None, 'null', None, {'Content-Type'..."` (Root cause #2) + 28 rows `'KBONK'`/`'KLUNC'`/`'KSHIB'`/
      `'KNEIRO'`/`'KFLOKI'`/`'KPEPE'` bare `KeyError` (Root cause #3), plus 31 `Tardis HTTP 403 code=274` (BYBIT,
      unrelated pre-existing 403-family) and 10 `UNCLASSIFIED:404`. Verified `6c6fab03` IS an ancestor of
      `origin/live-defi-rollout` (`git merge-base --is-ancestor` = true) and re-read the current `hyperliquid_s3.py`
      source — `_fetch_funding_via_rest`, `_reraise_hyperliquid_sdk_error`, and `_resolve_hyperliquid_coin_case` are
      present and correct exactly as documented, so **this is NOT a regression in the fix, and NOT a new code bug** —
      the shipped fix is genuinely correct and would prevent these exact rows if the code producing them ran it.
      `attempted_at`≈`written_at` (lag ~0.2s) confirms these are REAL-TIME writes, not delayed consolidation of old
      shards. Traced the source: `gcloud compute instances list` shows `mtds-live-cefi-consolidated-20260802-142543`
      (RUNNING, `VM_OPERATION=live_websocket`, `VM_ASSET_GROUP=CEFI`) created 2026-08-02T14:25:51Z — its serial console
      log shows `Extracted mtds-code` at boot (2026-08-02T14:27:29Z), i.e. a ONE-TIME code install at launch (per the
      documented VM-tarball-deployment model —
      `market-tick-data-service/scripts/vm/launch-mtds-live-cefi-     consolidated.sh` does have a
      `lc_verify_tarball_freshness` pre-launch guard, but whatever it let through at that boot did not include the fix,
      going by this VM's own output). This VM has been running continuously for ~34h at investigation time and its own
      writes exactly explain the fresh slice (first fresh row 2026-08-02 16:58:46Z, ~2.5h after this VM's boot —
      consistent with it being the sole active writer of these rows). **NOT executed this session** (no SSH access from
      this identity — `whoami`=`github-actions-deploy@central-element-323112.iam.gserviceaccount.com`, a genuinely
      different identity from the self-service `unified-trading-sa`/`uts-orchestrator-epic-role` per
      `SUB_AGENT_MANDATORY_RULES.md` §"When escalating", so not self-granted; also this doc's own launcher script
      carries an explicit historical warning — `zombie_watchdog_relaunch_reaped_live_backfills_2026_06_23.md` — against
      reflexively deleting a live VM off a copy-pasteable suggestion, which this exact refusal-path shape is): **cycle
      `mtds-live-cefi-consolidated-20260802-142543`** — launch a fresh `mtds-live-cefi-consolidated-<newtimestamp>` via
      the existing launcher (`--force`, since the singleton lock will refuse otherwise), verify it boots healthy
      (`ps aux | grep websocket` shows all MVP shards running, `run.log` STARTED), THEN (only after confirming the new
      one is genuinely healthy) delete the old `-20260802-142543` instance. This is additive-then-subtractive (new VM
      first), and `MANIFEST_PER_VM_SHARDS=true` makes both VMs' writes shard-isolated so no risk of corruption if both
      are briefly up — the risk is solely "did the new launch actually pick up the fix" (verify: fresh HYPERLIQUID
      derivative_ticker `attempted_failed` rows post-cycle should show ZERO recurrences of the
      429-raw-tuple/K\*-KeyError signatures) and "brief live-data gap for other shards on that VM during the cycle"
      (recoverable per Live=batch architecture, not data loss). Tagged `[OPERATOR]` per the live-service risk + the
      doc's own documented incident precedent about VM deletion, not because the diagnosis is ambiguous.
- [x] ✅ [PROCESS] P2. **New finding (agt-0df274, 2026-07-29):** a THIRD escalation worker (agt-0df274) was dispatched
      for this byte-identical static condition (158,085 attempted_failed unchanged; only `captured` grew, dropping the
      ratio 11.2%→10.9%) — see Progress Log below. `dp_run_mostly_empty_no_recurring_dedup_2026_07_15.md` (archived, all
      3 todos done) fixed the _Slack_ re-page cadence (cooldown-map + persisted re-nag interval), but nothing checks
      whether an OPEN, already-diagnosed issue doc already covers the exact `(asset_group, data_type, event)` tuple
      before the escalation fast path (`repository_dispatch escalate-to-orchestrator`) spawns another full
      `data_pipeline_failure` worker. Filed
      `/plans/archive/issues/dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md` to track a real fix
      (agent-orchestrator/deployment-service, out of this doc's `market-tick-data-service` scope) — not fixed here.
      **Flipped 2026-08-05 (slot-15):** finding documented + tracked; implementation blocked on unresolved DESIGN
      decision (Option A/B/C) in the referenced issue doc — code fix lives there, not here.

## Progress Log

- **2026-07-28 (data_pipeline_failure escalation worker, escalation agt-7a4d1d):** Diagnosed and fixed the
  `Resolver requires aiodns library` root cause (see above); code shipped, quality gates verified green. Flagged the
  HYPERLIQUID 429 signature and small tails as open questions for a follow-up, not chased further this session per the
  one-shot escalation scope.
- **2026-07-28 (data_pipeline_failure escalation worker, escalation agt-27e235):** Same alert re-fired (static
  manifest-cell signal, per `cefi_high_attempted_failed_batch_cluster_2026_07_23.md`) and dispatched a second escalation
  worker. Verified agt-7a4d1d's aiodns fix was already shipped (`market-tick-data-service@6a067cf1`, confirmed ancestor
  of `origin/live-defi-rollout`) -- did not duplicate it. Picked up both Open Questions instead: root-caused and fixed
  the HYPERLIQUID 429 raw-tuple leak (Root cause #2) and the K\*-symbol case-sensitivity `KeyError` (Root cause #3),
  both in `market_tick_data_service/adapters/hyperliquid_s3.py::_fetch_funding_via_rest`. Verified live against the
  actual instrument catalogue (confirmed the 6 uppercased instrument_ids) and the installed `hyperliquid-python-sdk`
  source (confirmed the exact case-sensitive dict-lookup line + the exact un-formatted-exception constructors). Added 5
  regression tests (`TestFetchFundingViaRestErrorHandling`). First `quality-gates.sh` run failed codex compliance
  (`_fetch_funding_via_rest` hit `MAX_METHOD_LINES=50` at 70L after the additions) -- extracted
  `_resolve_hyperliquid_coin_case` + `_reraise_hyperliquid_sdk_error` as module-level helpers (verified locally against
  the exact AST line-counter QG uses before re-running). Second run green (304s, 7337 passed/0 failed). Shipped via
  `quickmerge --agent --files` -- landed as `market-tick-data-service@6c6fab03` on `live-defi-rollout` (verified
  `git merge-base --is-ancestor`). Also flagged (not fixed, out of `derivative_ticker` scope) a hypothesis that the same
  uppercased-`coin` bug may silently affect `book_snapshot_5`'s `fetch_l2_book` S3-key construction for the same 6
  symbols -- see Open Questions.
- **context-scout 2026-08-01**: populated context_scope (5 entries).
- **2026-07-29 (data_pipeline_failure escalation worker, escalation agt-0df274):** Same alert re-fired a THIRD time
  (asset_group=cefi, data_type=derivative_ticker, 158,085/1,450,501 attempted_failed, 10.9%). Confirmed via this doc's
  own numbers that the `attempted_failed` NUMERATOR is byte-identical to the 2026-07-28 reading (158,085 == 158,085) --
  only `captured` grew (+39,899), which is exactly what a STATIC backlog + ongoing forward-progress looks like, not a
  new regression. Did not re-run the live bounded manifest read this session (the exact-numerator match across two
  independent readings a day apart is already strong evidence of zero new activity); if a future escalation on this same
  doc sees the numerator move, that reopens the investigation for real. Verified both prior code fixes
  (`market-tick-data-service@6a067cf1`, `@6c6fab03`) are ancestors of `origin/live-defi-rollout` -- nothing to re-ship.
- **2026-07-29 (separate audit, not an escalation — verifying `derivative_ticker` is the sole canonical funding-rate
  route across all 14 cefi perp venues):** Arrived at this doc from the OTHER direction — per-venue, not aggregate.
  Fresh `read_availability_index` breakdown confirms this doc's static-backlog finding at venue granularity: DERIBIT's
  113,814 attempted_failed are 100% the SEPARATE, already-resolved `tardis_concurrent_ip_lockout_2026_07_12.md` 403
  debris (not aiodns); COINBASE-FUTURES's 429 attempted_failed are 98% (421/429) the aiodns signature this doc already
  fixed, all `written_at` predating `@6a067cf1`; bare-OKX's 20 attempted_failed are 100% the same aiodns signature, also
  pre-dating the fix. No new post-fix aiodns/403 rows for any of these 3 venues — corroborates the "static, not
  regressing" conclusion above from a venue-scoped angle instead of the aggregate one. Also confirmed (separately, out
  of this doc's scope) that no `perp_funding`/ohlcv-embedded funding-rate leak exists for any of the 14 venues —
  `derivative_ticker` is the sole live route. No code or todo changes needed; the existing P3 "retry historical aiodns
  rows" todo above already covers the COINBASE-FUTURES/OKX-bare cleanup. Closed the DOCS P3 (appended `DP-FETCH-009` to
  the registry SSOT). Investigated why the alert still labels this "Fresh -- 0d ago" despite being static:
  `attempted_failed_staleness.py`'s `STATIC_BACKLOG_STALE_DAYS_THRESHOLD=1` buckets by WHOLE days since the last write,
  so any re-fire within 24h of the last write timestamp reads "Fresh" even though it's the same 2026-07-28T09:03:12Z
  data -- a labeling-precision quirk, not a bug worth fixing (the module's own docstring already disclaims it only
  labels, never gates paging cadence). The real, worth-fixing gap is that a THIRD full escalation-worker session got
  spent re-confirming a condition two prior sessions already fully diagnosed -- filed as its own process issue (see new
  P2 todo above) since the fix belongs in agent-orchestrator/ deployment-service's escalation dispatch, not this repo.
- **2026-07-30 (data_pipeline_failure escalation worker, escalation agt-40f31f) — 5th+ dispatch, confirmed still static,
  no new work.** Alert re-fired: 158,475/1,502,222 attempted_failed (10.5%), labeled "STATIC BACKLOG — no new
  attempted_failed activity in 1d". Ran a fresh live, bounded, column-projected `read_availability_index` read
  (`data_type=derivative_ticker`, `capture_status=attempted_failed`) before assuming the label was correct, since the
  raw numerator had moved (+390 vs the 2026-07-29 reading of 158,085 — NOT byte-identical this time, unlike the prior
  three re-fires). Confirmed the delta is fully explained, not a regression: `written_at` max across all 158,475 rows is
  `2026-07-29T09:07:42Z` — **zero rows written in the last 24h** (0 within 1d; the +390 are rows written 2026-07-29,
  i.e. before or concurrent with the prior session's same-day reading, not a new event). Full `error_reason` breakdown
  confirms every bucket is a subset of the already-documented static backlog: `UNCLASSIFIED:Tardis HTTP 403` +
  `Tardis HTTP 403` + `Tardis HTTP 403 code=274 concurrent-IP-lock` = 118,584 (the 403-family), `VENUE_FETCH_FAILED` =
  30,934 (exact match to the prior doc's figure), the 2,258-row 2026-07-28T09:03:12Z fresh-slice signatures (429
  raw-tuple, aiodns, K\*-symbol KeyError) all present at their expected counts, plus a handful of older/smaller
  historical buckets not previously itemized here (`Tardis HTTP 500`/`503`/`400`: 2,784 rows combined;
  `schema contract violated for cefi/COINBASE-FUTURES/perpetual/derivative_ticker`: 115 rows, 100% COINBASE-FUTURES;
  `StreamingParquetWriter pre-write validation failed`: 81; `In CSV column #N`: 68) — none of these wrote anything in
  the last 7 days either (confirmed via the same read filtered to `written_at`), so they're pre-existing static debris,
  not a new failure class. Verified both prior fix commits (`market-tick-data-service@6a067cf1`, `@6c6fab03`) remain
  ancestors of `origin/live-defi-rollout` — nothing to re-ship. **No code change, no new todo** — this is exactly the
  redundant-dispatch waste `dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md` already tracks (still
  `status: open`, P2, awaiting an operator/design decision on Option A/B/C); adding this as further corroborating
  evidence there rather than duplicating the todo here.
- **2026-07-30 (data_pipeline_failure escalation worker, escalation agt-14f171) — 6th+ dispatch, byte-identical
  numerator to the immediately-prior reading, no manifest read needed.** Alert re-fired: 158,475/1,503,839
  attempted_failed (10.5%), labeled "STATIC BACKLOG — no new attempted_failed activity in 1d". Numerator (158,475) is
  byte-identical to agt-40f31f's reading minutes/hours earlier the same day (also 158,475/1,502,222) — only `attempted`
  (denominator, `captured`) grew by 1,617, consistent with ordinary forward-progress on other cells, not this backlog
  moving. Per agt-40f31f's own finding (this doc's prior entry), a byte-identical numerator against the
  immediately-prior verified reading does not warrant re-running the live bounded manifest read — skipped it this
  session. Verified both fix commits (`market-tick-data-service@6a067cf1` aiodns, `@6c6fab03` HYPERLIQUID 429/K*-symbol)
  remain ancestors of `origin/live-defi-rollout` (`git merge-base --is-ancestor`, both true). **No code change, no new
  todo** — same redundant-dispatch waste `dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md` tracks;
  adding this as further corroborating evidence there.
- **2026-07-31 (data_pipeline_failure escalation worker, agt-794496, slot 5) — 7th+ dispatch, numerator still
  byte-identical.** Re-fired again: 158,475/1,506,427 attempted_failed (10.5%), labeled "STATIC BACKLOG — no new
  attempted_failed activity in 1d". Numerator (158,475) is byte-identical to agt-40f31f's and agt-14f171's prior
  verified readings — only `attempted` (denominator) grew (1,503,839 → 1,506,427, +2,588), consistent with ordinary
  forward-progress elsewhere, not this backlog moving. Per the established "no new `written_at` activity since the last
  verified reading" skip rule, did not re-run the live bounded manifest read — did only a `git merge-base --is-ancestor`
  check on both shipped fix commits (`market-tick-data-service@6a067cf1` aiodns, `@6c6fab03` HYPERLIQUID
  429/K\*-symbol), both still ancestors of `origin/live-defi-rollout`; working tree clean, no uncommitted changes in
  this slot's `market-tick-data-service` clone. **No code change, no new todo** — same redundant-dispatch waste
  `dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md` already tracks (still `status: open`, P2, awaiting
  an operator/design decision).
- **2026-07-31 (data_pipeline_failure escalation worker, agt-bd4088, slot 2) — 8th+ dispatch, numerator still
  byte-identical.** Re-fired again: 158,475/1,508,151 attempted_failed (10.5%), labeled "STATIC BACKLOG — no new
  attempted_failed activity in 1d". Numerator (158,475) is byte-identical to agt-794496's immediately-prior verified
  reading — only `attempted` (denominator) grew (1,506,427 → 1,508,151, +1,724), consistent with ordinary
  forward-progress elsewhere, not this backlog moving. Per the established skip rule, did not re-run the live bounded
  manifest read — did only a `git merge-base --is-ancestor` check on both shipped fix commits
  (`market-tick-data-service@6a067cf1` aiodns, `@6c6fab03` HYPERLIQUID 429/K\*-symbol), both still ancestors of
  `origin/live-defi-rollout`; working tree clean, no uncommitted changes in this slot's `market-tick-data-service`
  clone. **No code change, no new todo** — same redundant-dispatch waste
  `dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md` already tracks (still `status: open`, P2, awaiting
  an operator/design decision that this 8th+ redundant dispatch further corroborates the need for).
- **2026-07-31 (data_pipeline_failure escalation worker, agt-fc78d0, slot 5) — 9th+ dispatch, numerator still
  byte-identical.** Re-fired again: 158,475/1,509,137 attempted_failed (10.5%), labeled "STATIC BACKLOG — no new
  attempted_failed activity in 1d". Numerator (158,475) is byte-identical to agt-bd4088's immediately-prior verified
  reading — only `attempted` (denominator) grew (1,508,151 → 1,509,137, +986), consistent with ordinary forward-progress
  elsewhere, not this backlog moving. Per the established skip rule, did not re-run the live bounded manifest read — did
  only a `git merge-base --is-ancestor` check on both shipped fix commits (`market-tick-data-service@6a067cf1` aiodns,
  `@6c6fab03` HYPERLIQUID 429/K\*-symbol), both still ancestors of `origin/live-defi-rollout`; working tree clean, no
  uncommitted changes in this slot's `market-tick-data-service` clone. **No code change, no new todo** — same
  redundant-dispatch waste `dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md` already tracks (still
  `status: open`, P2, awaiting an operator/design decision that this 9th+ redundant dispatch further corroborates the
  need for).
- **2026-07-31 (data_pipeline_failure escalation worker, agt-7f0c1a, slot 9) — 10th+ dispatch, numerator still
  byte-identical.** Re-fired again: 158,475/1,518,154 attempted_failed (10.4%), labeled "STATIC BACKLOG — no new
  attempted_failed activity in 2d". Numerator (158,475) is byte-identical to agt-fc78d0's immediately-prior verified
  reading — only `attempted` (denominator) grew (1,509,137 → 1,518,154, +9,017), consistent with ordinary
  forward-progress elsewhere, not this backlog moving. Per the established skip rule, did not re-run the live bounded
  manifest read — did only a `git merge-base --is-ancestor` check on both shipped fix commits
  (`market-tick-data-service@6a067cf1` aiodns, `@6c6fab03` HYPERLIQUID 429/K\*-symbol), both still ancestors of
  `origin/live-defi-rollout`; working tree clean, no uncommitted changes in this slot's `market-tick-data-service`
  clone. **No code change, no new todo** — same redundant-dispatch waste
  `dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md` already tracks (still `status: open`, P2, awaiting
  an operator/design decision that this 10th+ redundant dispatch further corroborates the need for).
- **2026-08-01 (data_pipeline_failure escalation worker, agt-7f0c1a, slot 8) — 11th+ dispatch, and this time the SAME
  escalation_id (`agt-7f0c1a`) as the entry directly above, not just the same condition.** This is the literal same
  escalation event dispatched to two different slots (slot 9, then slot 8) with byte-identical alert numbers
  (158,475/1,518,154 attempted_failed, "STATIC BACKLOG — no new attempted_failed activity in 2d"). This is the first
  confirmed exact-duplicate-escalation_id case for `(cefi, derivative_ticker)` specifically — the same shape already
  seen 3 times for `(cefi, book_snapshot_5)` (`agt-ccb54c` 2026-07-30, `agt-0bf4a3` and `agt-406c1f` both 2026-07-31,
  per `dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md`'s Progress Log). Not addressed by any
  materiality fix (that changes classification/paging severity for a condition, it cannot deduplicate two dispatches of
  the identical event) — squarely Option A/B/C's territory in the meta-issue. Working tree clean; both fix commits
  (`market-tick-data-service@6a067cf1` aiodns, `@6c6fab03` HYPERLIQUID 429/K\*-symbol) confirmed still ancestors of
  `origin/live-defi-rollout` via `git merge-base --is-ancestor`. **No code change, no new todo** — cross-referenced into
  `dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md`'s Progress Log as well.
- **2026-08-01 (data_pipeline_failure escalation worker, agt-066ced, slot 7) — `(cefi, derivative_ticker)`'s 12th+
  dispatch, a fresh (non-duplicate) escalation_id, still zero new work.** Re-fired again: 158,475/1,522,499
  attempted_failed (10.4%), labeled "STATIC BACKLOG — no new attempted_failed activity in 3d". Numerator (158,475) is
  byte-identical to every verified reading since agt-40f31f's 2026-07-30 confirmation — only `attempted` (denominator)
  grew (1,518,154 → 1,522,499, +4,345), consistent with ordinary forward-progress elsewhere, not this backlog moving.
  Per the established skip rule (no new `written_at` activity since the last verified reading), did not re-run the live
  bounded manifest read — did only a `git merge-base --is-ancestor` check on both shipped fix commits
  (`market-tick-data-service@6a067cf1` aiodns, `@6c6fab03` HYPERLIQUID 429/K\*-symbol), both still ancestors of
  `origin/live-defi-rollout`; working tree clean, no uncommitted changes in this slot's `market-tick-data-service`
  clone. **No code change, no new todo** — same redundant-dispatch waste
  `dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md` already tracks (still `status: open`, P2, awaiting
  an operator/design decision on Option A/B/C that this 12th+ dispatch further corroborates the need for).
- **2026-08-03 (data_pipeline_failure escalation worker, agt-829d55, slot-9) — 13th+ dispatch, but the FIRST since
  2026-07-30 where the numerator actually moved (158,475 → 158,815), and the first to trace the fresh slice to a root
  cause distinct from "static backlog."** DID re-run the live bounded manifest read (numerator moved, so the established
  skip rule did not apply) and found the fresh 24h slice (1,821 rows) is 95% HYPERLIQUID rows carrying the EXACT
  `error_reason` signatures this doc's own `market-tick-data-service@6c6fab03` fix (Root causes #2/#3) already
  root-caused and fixed — re-verified the fix is still correctly present in source and still an ancestor of
  `origin/live-defi-rollout`, so this is NOT a regression or a new bug. Traced it instead to a currently-RUNNING live VM
  (`mtds-live-cefi-consolidated-20260802-142543`, launched 2026-08-02, i.e. 5 days AFTER the fix shipped) whose serial
  console confirms a one-time `mtds-code` tarball extraction at boot — consistent with this VM having been launched from
  a tarball that, despite the launcher's own `lc_verify_tarball_freshness` guard, did not carry the fix, and which
  (being long-running, `VM_SHUTDOWN_ON_COMPLETION=false`) has been continuously reproducing the already-fixed bugs in
  real time ever since (`attempted_at`≈`written_at` lag ~0.2s rules out delayed-consolidation of old shards). No SSH
  access from this session's identity (`github-actions-deploy`, a genuinely different identity from the self-service
  `unified-trading-sa`) to directly confirm the VM's installed source, so this is the strongest available evidence, not
  a certainty — filed as a new `[OPERATOR]` P1 todo (cycle the VM via the existing launcher) rather than executed, both
  because of the identity gap and because this doc's own launcher script carries an explicit historical warning against
  reflexively deleting a live VM (`zombie_watchdog_relaunch_reaped_live_backfills_2026_06_23.md`). No code change (none
  needed — the fix is already correct and shipped), no GCS/manifest write, no VM launched/deleted this session.
- **context-scout 2026-08-03**: refreshed context_scope (6 entries) — swapped the now-superseded
  `tardis_concurrent_ip_lockout` background pointer for the two artifacts the new `[OPERATOR]` P1 todo (cycle the stuck
  live VM) actually needs: the launcher script to run and the VM-deletion-caution precedent doc it cites.
- **2026-08-05 (slot-15 data_engineering, task `cefi_derivative_ticker_tardis_resolver_aiodns_hardfail-003`) —
  investigated the residual ~262-row tails, both confirmed static, code already handles them going forward.**
  **`UpstreamTimestampBiasError` on ASTER (~50 rows):** Fixed in `unified-api-contracts@4dfe960a` (2026-08-03) —
  `classify_venue_error`'s `internal` fallback bucket now has an entry for `UpstreamTimestampBiasError` with
  `ErrorAction.RETRY`, so any new occurrence is correctly classified. The ~50 historical ASTER rows predate this fix
  (2026-07-28 batch). No new `UpstreamTimestampBiasError` rows observed in subsequent manifest reads. **No code change
  needed** (fix already shipped, historical rows static). **`UNCLASSIFIED:404 GET https` on
  BINANCE-FUTURES/BYBIT/DERIBIT (~122 rows originally, 10 in 2026-08-03 reading):** Traced through the Tardis download
  paths. `tardis_csv_transport.py` (the CSV/batch download path used by `derivative_ticker`) already handles
  `TardisHTTPError(404)` as honest absence (skip sentinel, lines 548-550 and 638-639). `tardis_stream_client.py` handles
  HTTP 404 by returning empty bytes (lines 197-199). The `UNCLASSIFIED:404 GET https` error format does not match the
  current `TardisHTTPError.__str__` format (`"Tardis HTTP 404"`), suggesting these rows were produced by a code path (or
  code version) that no longer exists in the current tree — possibly a direct `aiohttp`/`httpx` error that escaped
  before the Tardis-specific error wrapping was added, or an older error-string format. The decline from 122→10 rows
  (2026-07-28→2026-08-03 readings) is consistent with the fix having shipped between the original batch and subsequent
  sweeps. The 10 residual rows are likely from the stuck `mtds-live-cefi-consolidated-20260802-142543` VM (see
  `[OPERATOR]` P1 above) running pre-fix code. **No code change needed** (current code handles 404 correctly; historical
  rows will be retried by the next natural cefi backfill sweep, same disposition as the other P3 retry todos).
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (6 entries), unchanged.
- **2026-08-06 (backend_engineer, slot-9, task cefi_derivative_ticker_tardis_resolver_aiodns_hardfail-006) — VM cycle
  confirmed COMPLETE (done by another session before this dispatch arrived); [INFRA] P1 checkbox flipped.** Arrived to
  find the VM cycle already executed: `gcloud compute instances list` shows
  `mtds-live-cefi-consolidated-20260806-163414` RUNNING in `asia-northeast1-c` (created 2026-08-06T16:34:xx), 17 MVP
  shards healthy per serial console `ps aux` output, `=== VM SETUP COMPLETE ===` at 16:36:48Z. Old VM
  `mtds-live-cefi-consolidated-20260802-142543` absent from `gcloud compute instances list` (DELETED). Tarball
  freshness: `gs://deployment-scripts-central-element-323112/code/mtds-code@55d88025.tar.gz` uploaded at
  2026-08-06T16:31:19Z (immediately pre-launch). Verified both fix commits are ancestors of the deployed tarball SHA
  `55d88025`: `git merge-base --is-ancestor 6a067cf1 55d88025` = true; `git merge-base --is-ancestor 6c6fab03 55d88025`
  = true. No code change this session (all fixes already shipped in prior sessions). Plan checkbox flipped; all todos
  now `[x]`.
- **context-scout 2026-08-07**: refreshed context_scope (5 entries) -- swapped the now-completed VM-cycle launcher +
  zombie-watchdog precedent doc (that [INFRA] P1 todo is done and verified) for
  `market_tick_data_service/adapters/hyperliquid_s3.py`, the actual file carrying root causes #2/#3 (>80% of the fresh
  rows this doc fixed) and the sole still-open Follow-ups item (fetch_l2_book/book_snapshot_5 case-sensitivity
  hypothesis) -- this file was missing from context_scope despite being the doc's primary source-code target.
- **context-scout 2026-08-07 (batch11 independent re-verify)**: all 5 entries confirmed resolving on disk; content
  unchanged.

## Follow-ups

- [x] ✅ [DATA] P3. **CONFIRMED 2026-08-10 — market-tick-data-service@a8e98742.** Chase the flagged-but-unconfirmed
      fetch_l2_book / book_snapshot_5 case-sensitivity hypothesis — CONFIRMED: the IS catalogue stores the 6 k-prefixed
      HYPERLIQUID meme coins UPPERCASED (KPEPE, KBONK, KFLOKI, KNEIRO, KLUNC, KSHIB), but HL's S3 archive keys use the
      real mixed case (l2Book/kPEPE.lz4). S3 keys are case-sensitive → the uppercased key 404s on every hour as a SILENT
      absence (empty_confirmed). Manifest evidence: all 6 symbols show empty_confirmed across their entire history
      (~1,335 instrument-date shards each, ~8,010 total), zero captured rows ever. Fixed by adding a lazy
      _hl_coin_universe property + _resolve_l2_book_coin helper (case-insensitive resolution against HL's /info
      universe, cached per instance) and resolving the coin before building the S3 key in fetch_l2_book. Row coin/symbol
      retain canonical uppercase form matching expected-universe catalogue keys. 3 regression tests added.

> **2026-08-06 archive-candidate audit**: All 9 todos are [x] and the three root causes + VM cycle are fixed/verified
> (aiodns @6a067cf1, HYPERLIQUID @6c6fab03, VM cycled 2026-08-06, tarball ancestors verified). But the Open Questions
> section explicitly leaves a plausible follow-up 'flagged... not chased, not confirmed' for a different data_type
> (book_snapshot_5) — a prose-only open question/follow-up, never a tracked todo. Conservative bias -> NEEDS_TODO (the
> untraced catalogue uppercasing source is out-of-repo and noted as non-blocking).
