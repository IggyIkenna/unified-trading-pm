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
    /plans/archive/issues/cefi_threaded_resolver_dns_starvation_risk_2026_07_26.md,
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
last_updated: 2026-07-31
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
- [ ] [DATA] P3. If pursued: retry the 290 historical `Resolver requires aiodns library` rows (now fixed going forward,
      not retroactively) via a normal idempotent backfill re-attempt -- no code change needed, purely operational.
- [ ] [DATA] P3. If pursued: retry the ~90 historical K\*-symbol rows (now fixed going forward via the case-insensitive
      resolution, not retroactively) -- same "normal idempotent backfill re-attempt" shape as P3, not urgent.
- [ ] [DATA] P3. Small residual tails (~262 rows: `UNCLASSIFIED:404 GET https` on BINANCE-FUTURES/BYBIT/DERIBIT,
      `UNCLASSIFIED:UpstreamTimestampBiasError` on ASTER) -- not investigated in either session, left open per both
      sessions' scope discipline (small share of the fresh batch, ordinary-transient-looking).
- [x] ✅ [DOCS] P3. **DONE 2026-07-29 (data_pipeline_failure escalation, agt-0df274) — `unified-trading-pm` (this
      commit).** Appended the missing `DP-FETCH-009` row to `codex/05-infrastructure/data-pipeline-alerts.registry.yaml`
      and `.md` so the SSOT matches what both prior escalations already shipped/referenced.
- [ ] [PROCESS] P2. **New finding (agt-0df274, 2026-07-29):** a THIRD escalation worker (agt-0df274) was dispatched for
      this byte-identical static condition (158,085 attempted_failed unchanged; only `captured` grew, dropping the ratio
      11.2%→10.9%) — see Progress Log below. `dp_run_mostly_empty_no_recurring_dedup_2026_07_15.md` (archived, all 3
      todos done) fixed the _Slack_ re-page cadence (cooldown-map + persisted re-nag interval), but nothing checks
      whether an OPEN, already-diagnosed issue doc already covers the exact `(asset_group, data_type, event)` tuple
      before the escalation fast path (`repository_dispatch escalate-to-orchestrator`) spawns another full
      `data_pipeline_failure` worker. Filed
      `/plans/active/issues/dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md` to track a real fix
      (agent-orchestrator/deployment-service, out of this doc's `market-tick-data-service` scope) — not fixed here.

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
