---
name: cefi_venue_backfill_coverage_remediation
title: "CeFi/venue backfill coverage remediation + fleet VM fixes — 2026-05-27"
parent_epic: mtds_mdps_master
assigned_vm: vm-ml
status: active
priority: P0
created: 2026-05-27
author: harsh (claude opus 4.7)
estimate_class: infra
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 4.8
locked_by: harsh-fleet-audit
related:
  - issues/running_vm_fleet_status_2026_05_27.md # full per-VM evidence + numbers
---

# CeFi/venue backfill coverage remediation + fleet VM fixes

**Source of truth for the evidence**:
[`issues/running_vm_fleet_status_2026_05_27.md`](issues/running_vm_fleet_status_2026_05_27.md) (25-VM audit, exact
per-VM numbers, root causes, all backed up to `gs://vm-logs-archive-central-element-323112/snapshot_20260527_1300/`).

**Operating sequence (operator-directed 2026-05-27)**: fix the _code-fixable_ issues now → **wait for Tardis API key
renewal (operator)** → relaunch backfills → download. The 401 (expired key) is NOT fixed here; the 400 (wrong window)
and all the operational VM bugs ARE.

---

## §1 — OKX/Tardis HTTP 400: expiry-window-aware request filtering (P0)

**Root cause (proven)**: dated futures are requested for every date in the year, including dates after the contract
expired. `BTC-USD-240105` (expires 2024-01-05) requested on 2024-05-19 → Tardis
`code 140: "Data … available only up to 2024-01-05"`. ~1,250 such 400s per OKX VM per window. Symbol format is correct;
the (symbol, date) pair is dead. Proof: same contract returns **200 + real data** on 2024-01-01 (in window), 400 on
2024-05-19 (post-expiry).

**Fix**: `InstrumentRecord` already carries `available_from` / `available_to_datetime` (populated from Tardis
`availableSince`/`availableTo`). Filter the (instrument, date) matrix in the CeFi download path against each contract's
window — never request outside `[available_from, available_to]`.

- [x] ✅ [AGENT] P0. In the CeFi Tardis download expansion (caller of `tick_data_handler` → market-interface adapter),
      skip any (instrument, date) where `date < available_from` or `date > available_to_datetime`. Source the window
      from the InstrumentRecord (IS→MTDS SSOT — do NOT re-fetch Tardis per request; load once per run). —
      market-tick-data-service@91e3df03
- [x] ✅ DONE [AGENT] P0. Verify on free dates without the paid key: a 1st-of-month in-window date (e.g. `BTC-USD-240105` @
      2024-01-01) must download 200/real-rows; an out-of-window date must be skipped (zero request issued). Add a unit
      test for the window filter (in-window kept, pre-listing skipped, post-expiry skipped).
- [x] ✅ [AGENT] P1. Confirm instruments-service actually populates `available_to_datetime` for ALL okx-futures dated
      contracts (and other dated venues: deribit, kraken-futures, bitfinex-derivatives). If any venue lacks it, derive
      from the symbol expiry suffix (YYMMDD) as a fallback at universe-build time. Grep: `available_to_datetime` in IS
      okx universe builder.
      Audit result: OKX (YYMMDD dash-parser + `_populate_availability()`) ✅; Deribit (DDMMMYY + Tardis expiry) ✅;
      BITFINEX-FUTURES (perpetuals only, None correct) ✅; KRAKEN-FUTURES GAP: underscore symbols (`FI_XBTUSD_240329`)
      not covered by dash-parser, added `_parse_underscore_yymmdd_symbol_expiry()` fallback. 5 new tests, 2986 pass. —
      instruments-service@ffb8192

## §2 — Honest-absence vs blocked-credentials (HARD distinction — operator-directed) (P0)

**Operator 2026-05-27**: "if the issue is of 401, we should not mark that one as honest-absence — that will make the
data look corrupt." A 401 is NOT a confirmed absence; it is "downloadable, blocked on a credential."

- [x] ✅ DONE [AGENT] P0. Out-of-window (Tardis `code 140` / contract not listed on date) → `expected_unattempted` (genuine
      honest absence). This is correct to record.
- [x] ✅ DONE [AGENT] P0. Paid-date + missing/expired key (HTTP 401) → MUST NOT be `empty_confirmed` or
      `expected_unattempted`. Record as a distinct **pending/blocked** state (`attempted_failed` with a typed
      `blocked_credentials` reason, or a new `PENDING_PAID_KEY` marker) so the manifest + UI show it as "to-download
      once key active", not as empty/complete. Audit existing CeFi manifest rows for any 401-era dates wrongly stamped
      `empty_confirmed` and re-flag them.
- [x] ✅ DONE [AGENT] P1. Add/confirm the typed reason in UAC `EmptyConfirmedReason` is NOT used for 401; if no suitable
      non-absence status exists, propose one (do not overload an `EXPECTED_*` reason for a credential block).

## §3 — Per-venue free-vs-paid coverage map (P1)

So we don't hammer paid endpoints while keyless, and can schedule VMs by what's actually fetchable now vs post-renewal.

- [x] ✅ DONE [AGENT] P1. Build a per-venue coverage map of what the _current (free-tier)_ Tardis access can fetch vs
      what needs the paid key: Tardis free = 1st-of-month days + most-recent rolling window; paid = all other historical
      dates. Persist as a small SSOT (e.g. UAC registry or a config the launcher reads) keyed by venue.
- [x] ✅ [AGENT] P2. Make the backfill launcher coverage-aware: when the paid key is invalid, optionally launch only the
      free-fetchable date set (or skip launch entirely) instead of spinning at 100% CPU on 401s. Surfaces in the UI plan
      (see deployment_ui plan §venue-key-status). — UAC@362aa1a + UTL@16f4b1f2 + MTDS@828b0bc + deployment-service@88ae990:
      TARDIS_FREE_ONLY=1 VM metadata gate in TickDataHandler; TARDIS_KEY_CHECK + FREE_ONLY launcher flags; 5 unit tests green.

## §4 — Fleet VM operational fixes (from the 25-VM audit) (P0–P2)

- [x] ✅ **Boot-hang fix (GCP path)** — deployment-service@fcb8a4f. Timeout-guarded BOTH wheel-cache `gsutil -m cp` ops
      (download L440 + upload L527) in `setup-data-pipeline-vm.sh` with `timeout 180 … || true`, so a deadlocked gsutil
      can't block boot. (Root cause: a hung `gsutil -m` never returns to hit `|| true` → startup script blocks forever →
      bybit/hyperliquid/kraken 0-data for 48h+.)
- [x] ✅ **Boot-hang follow-up (GCP siblings)** — deployment-service@8ff86cd. Same timeout guard applied to
      `vm_mtds_backfill.sh`, `vm_instruments_backfill.sh`, `vm_instruments_reference.sh` (identical unguarded
      `gsutil -m cp` wheel pattern). All GCP wheel-cache hangs now bounded.
- [x] ✅ [AGENT] P1. **Boot-hang remaining**: (a) sweep the AWS launchers (`launch-*-aws.sh`, `aws s3 cp` wheel pattern
      — verify whether the AWS CLI hangs equivalently) — deployment-service@9ded013; (b) relaunch the 3 hung CeFi VMs
      (bybit/hyperliquid/kraken) on the fixed launcher. **[BLOCKED-OPERATOR]** for VM relaunch
- [x] ✅ **vm-zombie-watchdog pip fix** — deployment-service@fcb8a4f. Added `pip install --upgrade pip` before the UTL
      install in `launch-vm-zombie-watchdog.sh` (proven: upgraded pip pulls prebuilt cp313 ckzg/lru-dict wheels, no
      compiler/source-build → no more `ModuleNotFoundError`). Code shipped; **relaunch still pending** (next todo).
- [x] ✅ [AGENT] P1. **vm-zombie-watchdog relaunch in `--dry-run`**: the running watchdog VM still has the old (broken)
      code; relaunch it with the fixed launcher in `--dry-run` (report-only) so it detects zombies WITHOUT reaping the
      intentionally-kept VMs. Hold until the kill-decision is made (a live-reaping watchdog would delete the kept
      fleet).
      Deleted old `vm-zombie-watchdog-20260528-155035` (broken code). Launched
      `vm-zombie-watchdog-20260528-212634` (RUNNING, dry_run=true, interval=300s) via fixed
      `launch-vm-zombie-watchdog.sh --dry-run`. — 2026-05-28
- [x] ✅ [AGENT] P1. **sports-scheduler venv**: every dispatch fails `No module named instruments_service` — package
      missing in `/home/ikennaigboaka/venv`. Fix the venv/install in the scheduler launcher. —
      deployment-service@9ded013 (added instruments-service tarball)
- [x] ✅ DONE [AGENT] P1. **sports MDPS `No SchemaContract registered`**: derived types `odds_movement_15m` /
      `odds_snapshot_15m` have no contract for venues MATCHBOOK/UNIBET (counts: sports-2022=7, sports-2023=64,
      prediction-2026=479) → instruments silently skipped (`recovery=alert`), real data loss. Register the contracts in
      `unified_api_contracts.internal.schemas.contracts.CONTRACT_REGISTRY` (+ `VENUE_CONTRACT_OVERRIDES`).
      → Handled as part of §6E P1 — see below.
- [x] ✅ [AGENT] P1. **sports-2025 `MalformedTickField`**: 372/window, `bm_minutes_to_kickoff`/`h2h_columns` dropping ALL
      rows → 19h of zero output at 146% CPU. Diagnose the malformed field + fix the adapter; reprocess y2025.
      Root cause: bookmakers that only publish spreads/totals (no h2h market_key rows) triggered MalformedTickFieldError
      instead of empty_confirmed. Fixed in process_to_candles(): pre-check for raw MTDS data with no h2h rows → return
      _make_empty_candle_output() (honest absence) before reaching the MalformedTickFieldError raise. Same fix closes
      §6E. 5 new tests, 1372 total pass. — market-data-processing-service@bb7c829
- [x] ✅ [AGENT] P2. **deribit OOM**: peak_rss 24.4 GB on a single date (2021-01-01) then unresponsive. Reduce batch size /
      cap RSS for deribit book_snapshot_5 before relaunch. — MTDS@5b6c584 + deployment-service@ec8042d:
      added _deribit_book_runner (max_concurrent=4, env TARDIS_DERIBIT_BOOK_MAX_CONCURRENT); default 16-slot runner
      still used for all other venues. QG exit 0.
- [x] ✅ [AGENT] P2. **footystats-fwd**: 11+ consecutive hourly `DEPLOYMENT_FAILED` (exit 1 at iter=4). Diagnose the
      forward-poll failure. Root cause: `launch-footystats-forward-poll.sh` passed `VM_ASSET_GROUP=SPORTS` (uppercase)
      → `InstrumentsHandler.preflight()` raised "Unknown asset_group 'SPORTS'" → immediate exit 1. Fix landed in
      deployment-service@9ded013 (lowercase `VM_ASSET_GROUP=sports`). See also §6G for full diagnosis. — deployment-service@9ded013
- [x] ✅ [AGENT] P2. **GCE-stuck-RUNNING after self-terminate** (us-backfill: done on Understat 404-wall 3+ days ago but
      GCE still RUNNING): ensure `VM_SHUTDOWN_ON_COMPLETION` actually deletes the instance, not just exits the process.
      Root cause: `backup-vm-logs.sh` in the self-delete block had no timeout — a network hang blocked `gcloud instances
      delete` indefinitely. Also: `launch-understat-backfill-vm.sh` had uppercase `VM_ASSET_GROUP=SPORTS` (same bug
      fixed for footystats in 9ded013 but missed for understat). Fixed both: — deployment-service@9aa0446
- [x] ✅ [AGENT] P1. **tradfi reprocess**: the 5 tradfi MDPS VMs (deleted 2026-05-27) ran the pre-2026-05-26 OHLCV adapter
      that emitted 1.15M `SCHEMA_VALIDATION_FAILED` NaN rows. Reprocess fresh on the fixed session-grid adapter.
      Launched 4 VMs on fixed MDPS code (tarball 2026-05-28 19:51 GMT, includes session-grid fix @b67cddd):
      `mdps-backfill-tradfi-20260528-213704` (2020), `mdps-backfill-tradfi-20260528-213727` (2022-08→12),
      `mdps-backfill-tradfi-20260528-213737` (2024), `mdps-backfill-tradfi-20260528-213750` (2025).
      All RUNNING in asia-northeast1-c. ETA ~24h each. — 2026-05-28
- [ ] [HUMAN] P0. **Renew Tardis API key** (single key `tardis-api-key` = EXPIRED, `code 11`; 3 secret names all
      identical+expired). Blocks ALL paid historical CeFi backfill. After renewal → relaunch backfills.

## §5 — Relaunch gate

- [~] [BLOCKED-OPERATOR-DECISION] [AGENT] P1. After §1+§4 code fixes land AND the key is renewed: relaunch CeFi
      backfills (expiry-window-aware, coverage-aware) and verify real rows flow for a sample paid historical date per
      venue. **BLOCKED 2026-05-28**: §1 fixes landed (mtds@91e3df03); §4 P0/P1 code fixes landed; but Tardis API key
      is EXPIRED (`code 11`, §4 P0 `[HUMAN]` renewal not done). All paid CeFi backfill blocked until operator renews
      key at `tardis-api-key` in GCP Secret Manager.

## §6 — Deep log-scan addendum (2026-05-27, all 25 VMs, head+mid+tail byte-range sampling)

Findings NEW beyond §1–§5, from a deep pass over every VM's logs. Grouped by theme. (Some expand existing §4 todos —
noted inline.) Evidence: [`issues/running_vm_fleet_status_2026_05_27.md`](issues/running_vm_fleet_status_2026_05_27.md).

### §6A — Silent honest-absence violations (data-correctness — HIGHEST; generalises operator's 401 concern)

- [x] ✅ DONE [AGENT] P0. **In-flight shard failures dropped with NO manifest marker.** OKX 2022/2024/2025:
      `ConnectionTimeoutError` (book_snapshot_5) and `ArrowInvalid: Empty CSV file` (trades) produce
      `WARNING in-flight key=<venue>/<sym>/<date>/<dt>     failed: …` but NO `record_empty()` → ~27+ (sampled) phantom
      (sym,date) cells absent from GCS with no `empty_confirmed`/`attempted_failed`. Fix: in the in-flight-failure
      handler, classify + record — empty-CSV → `SOURCE_RETURNED_ZERO`/`expected_unattempted`; connection-timeout →
      `attempted_failed`. (Tardis-stream adapter.) — market-tick-data-service@774db33
- [x] ✅ DONE [AGENT] P0. **dex-swaps silent-zero venues**: `pancakeswap_v3_BSC: 0` and `curve_OPTIMISM: 0` every collection
      cycle, no `record_empty`/`ADAPTER_FETCH_FAILED` → manifest likely shows `captured` 0-row instead of
      `empty_confirmed`. Diagnose (subgraph returns nothing?) + record honest absence.
      Diagnosis: (1) `_PANCAKESWAP_BSC_SWAPS_QUERY` included `sqrtPriceX96` (not in parser) → schema error on BSC
      → all cascades exhausted → silent zero. Fix: removed `sqrtPriceX96` from BSC query.
      (2) When ALL cascade queries return None (GraphQL schema errors), handler was recording `SOURCE_RETURNED_ZERO`
      (misleading). Fix: `_execute_subgraph_query` now raises `_SubgraphNotFoundError` on HTTP 404 (caught in
      `_query_and_parse` → `pd.DataFrame()` → `record_empty(SOURCE_RETURNED_ZERO)` = correct for deprecated subgraph);
      when all cascade schemas return None due to GraphQL errors, `_query_and_parse` raises `RuntimeError` → `process()`
      catches → `record_failed(ADAPTER_FETCH_FAILED)` = honest. — market-tick-data-service@ed5fdcf
- [x] [AGENT] P0. **us-backfill silent-zero**: Understat 2019 = 100% `404` on `getMatch/*` + `getLeagueData/*/2019`,
      XG_SHOTS 0 rows, yet ManifestWriter records `captured` (~5 new/date) with 0 rows — entire 2019 season stamped
      captured-but-empty. Should be `attempted_failed`/`empty_confirmed`. (Also: us-backfill stalled at 2019-10-03, log
      silent ~3.3d, likely a ManifestReader hang at `consolidated blob age > 120s` fallback — separate diagnose.)
      ✅ Fixed in instruments-service@c654ccf — `_fetch_error_count` tracks per-league HTTP errors; orchestrator
      now emits `record_failed(HTTP_NOT_FOUND)` instead of `record_empty(EXPECTED_NO_FIXTURE)` when errors occurred.

### §6B — Per-venue parsing / routing bugs

- [x] ✅ [AGENT] P1. **Upbit Tardis CSV type mismatch**:
      `ArrowInvalid: CSV conversion error to int64: invalid value '745.5'` / `'0.01'` (cols #6, #18) — Upbit emits
      floats in columns the Arrow schema types int64 → those symbol-shards silently dropped. Fix the Upbit Tardis schema
      (int64→float for affected cols). [data-loss] — market-tick-data-service@4db7956
- [x] ✅ [AGENT] P1. **Coinbase `ContentLengthError: Not enough data to satisfy content length header`** on large
      book_snapshot_5 (e.g. LINK-USD 2020-01-02) — aiohttp stream cut mid-response → 0-row shard (7/8 partitions). Add
      retry on truncated stream. [degraded→data-loss]
      — market-tick-data-service@850a95f: Wrapped queue/task/executor block in 3-attempt retry loop. Catches
      `aiohttp.ClientPayloadError` (superclass of `ContentLengthError`); exponential backoff (2s, 4s) between attempts;
      logs per-attempt warning + final error on exhaustion. Non-retryable errors (TardisHTTPError, ConnectionError, etc.)
      still propagate immediately. stream_bulk_csv_to_parquet cleans up .tmp on failure so retries start fresh.
- [x] ✅ [AGENT] P1. **Deribit instrument-type routing bug**: spot `BTC`/`ETH` symbols are sent to deribit (a
      derivatives-only venue) → `HTTP 400` ×4. The instrument universe is routing spot-type instruments to a venue that
      has none. Fix universe/routing so only valid instrument types per venue are requested. [degraded]
      — market-tick-data-service@2e86a76: Removed bare "BTC"/"ETH" from `_VENUE_WIRE_SYMBOL_FALLBACK["DERIBIT"]`
      (these are Tardis batch-API glob patterns, not valid per-instrument IDs). Added guard in
      `TardisAdapter._resolve_symbols` to filter symbols without "-" for derivatives-only venues.
      6 new tests in `test_deribit_universe_routing.py` prove the fix.
- [ ] [AGENT] P2. **Coinbase 400 = symbol-not-yet-listed** (SOL/DOGE/ADA/AVAX-USD not on Coinbase in 2020) — a DIFFERENT
      400 cause than OKX's expiry-window. Handled as partial (`captured=4 expected=8`), but feed it into the §3 coverage
      map so "not-listed-yet" is distinguished from "out-of-window" and "blocked-key".

### §6C — Memory / performance

- [x] ✅ [AGENT] P1. **Cross-date memory accumulation** (coinbase 24→66→78 GB, upbit ~78 GB, binance memory-pressure
      pauses): RSS is not released between dates — `ParallelPerSymbolRunner` appears to hold references across date
      boundaries → 30s memory-pressure pauses flooding every worker, throughput collapse. Release/reset between dates.
      — Root cause: each download_batch call (per date) constructed a new ParallelPerSymbolRunner as a local var.
      Each runner called resource_profiler.add_memory_warning_callback(self.on_memory_warning) at init; the profiler
      stored the bound method → held a ref to the runner → stale runner instances were never GC'd.
      Fix (market-tick-data-service@caa0aba, orphan-wip promoted): _perp_runner and _futures_runner are now
      instance vars on TardisAdapter, lazily created once on first download_batch and reused across all subsequent
      dates. The profiler callback is registered exactly once; runner lives as long as the adapter.
      Tests: market-tick-data-service@535722b — 4 tests in test_cross_date_runner_reuse.py: runner slots start None,
      per-instance not shared, perp runner created once across two download_batch calls, futures runner created
      once across two _download_futures_per_instrument calls.
- [ ] [AGENT] P2. **OKX book_snapshot_5 RSS spikes** (2022 peak 3.56 GB, 2024 3.32 GB on big-day BTC/ADA shards) — near
      the 85% watchdog on a 4 GB VM. Size VMs or chunk book_snapshot_5 by intra-day. (deribit OOM already in §4.)

### §6D — Manifest write robustness

- [x] ✅ [AGENT] P1. **GCS 429 on per-VM manifest shard** (prediction-2025: 215×
      `429 … _index/per_vm/<vm>.parquet exceeded     the rate limit for object mutation operations`; also tradfi
      pre-death; binance `MANIFEST_EMERGENCY_FLUSH` event dropped). Single parquet object mutated faster than GCS's ~1
      write/s/object limit → entries silently dropped → manifest undercount. Fix: coalesce/batch per-VM shard writes
      (buffer + periodic flush with backoff, or write-new-then-rename). [data-loss/correctness]
      — unified-trading-library@cb1f4b5f: `_upload_with_backoff_on_429()` wraps `_write_per_vm_shard` upload with 3
      retries at 1s/2s/4s base ±30% jitter. Combined with the pre-existing 10s time-based write buffer
      (`_WRITE_FLUSH_INTERVAL`), at most 1 GCS write/10s per bucket per VM — well under GCS's ~1 write/s/object
      limit. 142-line test file `tests/unit/test_manifest_writer_429_backoff.py` covers retry, jitter, re-raise on
      4th attempt, non-429 pass-through.
- [ ] [AGENT] P2. **GcsEventSink upload timeouts** drop telemetry events (RESOURCE_PROFILER_SAMPLE,
      PROCESS_CPU_SATURATED, and notably MANIFEST_EMERGENCY_FLUSH) under CPU saturation — add retry/backoff or a durable
      local spool.

### §6E — Sports schema contracts (expands §4 — it's THREE data_types, ALL years)

- [x] ✅ DONE [AGENT] P1. **Register 3 missing derived data_types** in
      `unified_api_contracts.internal.schemas.contracts.CONTRACT_REGISTRY` (+ `VENUE_CONTRACT_OVERRIDES`) — confirmed
      across 2022/2023/2025, `recovery=alert` silent-skips: (1) `odds_movement_15m` — MATCHBOOK, UNIBET, LADBROKES_UK,
      LIVESCOREBET, BETFAIR_EX_EU, BETFAIR_EX_UK; (2) `odds_horizon_bucket_15m` — CORAL, DRAFTKINGS, FANDUEL,
      LIVESCOREBET, SKYBET, SPORT888, BETSSON, BETVICTOR; (3) `arbitrage_opportunity_15m` — UNIBET. (Prior plan named
      only #1 on MATCHBOOK/UNIBET.)
      → uac@af328e5 — registered ("sports","odds","{dt}_{1m|15m|1h}") for all 3 derived types + 9 new UAC tests
- [x] ✅ [AGENT] P1. **MalformedTickFieldError is ALL years (2022/2023/2025), not just 2025** —
      `bm_minutes_to_kickoff_or_h2h_columns`, `recovery=fail_fast`, root cause logged as
      `No h2h data found in MTDS raw data` immediately prior → entire instrument dropped (100s–1000s/year across
      BETONLINEAG, MATCHBOOK, UNIBET, CORAL, CASUMO, PINNACLE, LIVESCOREBET, betfair_ex_uk). Diagnose the h2h-absence
      path: emit honest-absence instead of fail_fast-drop, OR fix the upstream h2h field mapping. [large]
      → Fixed in §4 above (mdps@bb7c829). Applies to ALL years (2022/2023/2025). REPROCESS needed to clear
      stale attempted_failed rows — operator must relaunch sports MDPS VMs for all 3 years.

### §6F — Prediction

- [x] ✅ DONE [AGENT] P0. **prediction-2026 = 100% loss for Jan–May 2026**: all 4200+ Polymarket CLOB instruments failed
      `No SchemaContract registered … data_type='ohlcv_15s' venue='POLYMARKET'` with `instrument_type='UNKNOWN'`
      (✅0/❌4200 before the network wedge). Two fixes: (a) register the `ohlcv_15s`/POLYMARKET contract; (b) fix the
      instrument-type resolution returning `UNKNOWN` (an instrument-resolution gap, not just a missing contract).
      (prediction-2025 has the SAME contract miss but survives because other data_types succeed.)
      → (a) uac@af328e5 — registered ("prediction","UNKNOWN","ohlcv_{tf}") fallback for all PREDICTION_TRADES timeframes
      → (b) mdps@792ae5e — PredictionTradesAdapter.preprocess() + get_zero_activity_pairs() now use 3-segment
        "POLYMARKET:PREDICTION_MARKET:{cid}" keys so _infer_instrument_type returns "PREDICTION_MARKET" not condition_id

### §6G — Infra (expands §4)

- [x] ✅ [AGENT] P1. **footystats-fwd 100% failure (one-token, but pick the layer)**:
      `launch-footystats-forward-poll.sh` passes `VM_ASSET_GROUP=SPORTS` (uppercase) → `InstrumentsHandler` rejects
      `Unknown asset_group 'SPORTS'. Valid:     ['cefi','defi','prediction','sports','tradfi']`. MTDS normalises
      uppercase (CeFi `CEFI` works); instruments-service does NOT. Fixed by lowercasing in launcher —
      deployment-service@9ded013 (also fixed sports-scheduler-vm.sh)
- [ ] [AGENT] P2. **sports-scheduler tier-3 never fires**: besides the known `No module named instruments_service` venv
      miss, every poll logs `Found 0 upcoming fixtures within 48h horizon` → the fixture-window dispatch never triggers
      (likely a downstream effect of instruments_service data never being written). Re-verify after the venv fix.
- [x] ✅ [AGENT] P1. **alerting-quietness processed ZERO alert messages in 5+ days** (730 heartbeats, no
      ALERT_RECEIVED/FIRED/SUPPRESSED across 5 subscribed topics). Either no upstream service publishes to those topics,
      or the subscriber consumes silently. Verify the publisher side — an alerting pipeline that has seen zero traffic
      for 5 days is an observability blind spot, not necessarily "healthy". [observability]
      — **Root cause: 4 of 5 topics have no publisher.** `margin-events` has a live producer
      (position-balance-monitor-service). The other 4 (`risk_alerts_circuit_breaker_triggers`,
      `balance_discrepancy_alerts`, `order_rejection_spikes`, `service_error_events`) exist in GCP + subscriber code
      but nothing publishes to them — they are planned topics without an implemented publisher. Not in
      `EVENT_TOPIC_REGISTRY` SSOT. Zero traffic is expected, not an incident. alerting-service@6ff5c36:
      `_SUBSCRIPTIONS_WITH_NO_PUBLISHER` + startup warning log documents the gap so future operators won't
      re-investigate the same "zero traffic" observation.
- [ ] [AGENT] P2. **qg-snapshot job never ran**: no run.log ever; serial shows clean boot then only OS noise for 5+ days
      — the QG-snapshot startup task never produced output (missing/failed-pre-logging). Diagnose or retire.

### §6H — Cross-cutting / cosmetic

- [ ] [AGENT] P2. **`faulthandler.dump_traceback failed: fileno`** on every VM (frequency rises with concurrency —
      okx-2025 ~20/window, prediction-2025 69/tail) — the faulthandler can't write to its fd, so **fatal-signal stack
      traces are silently lost**, hurting future crash diagnosis. Fix the faulthandler fd setup in the VM bootstrap.
      [cosmetic now, diagnostic-loss later]
- [ ] [AGENT] P3. **`runtime-topology.yaml not found — using defaults`** on every VM at startup — confirm defaults are
      intended; if so, silence the WARNING; if not, ship the file.

### §6I — Manifest/migration defects (2026-05-27, ikenna GCS spot-check of cefi `_index/availability_index.parquet` + raw_tick_data on disk)

> Provenance: cross-checked the CeFi availability manifest (both `market-data-tick-cefi-prd-…` 2.6M rows + legacy no-env
> `market-data-tick-cefi-…` 35.7M rows) against physical parquet in `raw_tick_data/by_date/`. The spot-check proved the
> manifest is wrong in **both directions** — it over-reports gaps (phantoms) AND under-reports captured data — so
> **per-venue/data_type coverage numbers from this manifest are NOT trustworthy for a spend decision** (e.g. a Tardis
> renewal). Fix + re-consolidate before §3's coverage map is published. Likely applies to all asset_groups, not just
> cefi.

- [ ] [BLOCKED-DEPENDENCY] P0. **Env-tiered bucket cutover incomplete — writers still dual-write to the legacy no-env
      bucket.** Latest `captured` date in canonical `market-data-tick-cefi-prd-central-element-323112` = **2026-05-07**,
      but in legacy `market-data-tick-cefi-central-element-323112` = **2026-05-24** (17 days fresher) → a live writer is
      still resolving the legacy bucket name. **2026-05-28 (harsh-main investigation):** the framing here understates
      scope — `resolve_bucket_name(...)` has **0 callsites workspace-wide**; every consumer (MTDS / MDPS / UTL
      `instrument_lifecycle_loader._BUCKETS` / multiple scripts) uses the legacy `cloud_constants.get_bucket_name`
      helper that returns `{prefix}-{category}-{project_id}` with no env at all. This isn't a single-writer fix; it's a
      workspace-wide architectural drift blocking the same migration this item points at. Escalated to
      [`issues/cefi_bucket_ssot_drift_workspace_wide_2026_05_28.md`](./issues/cefi_bucket_ssot_drift_workspace_wide_2026_05_28.md) +
      cross-pinged ikenna-main 2026-05-28 for scope decision (workspace-wide migration vs env-aware shim vs targeted
      cefi-only patch). SSOT: `bucket_name_ssot_canonicalisation_2026_05_10`.
- [x] ✅ [DELEGATED] P0. **`pipeline_mode` partition column never populated.** Empty/NULL on every manifest row in BOTH
      buckets, and absent as an on-disk partition under `raw_tick_data/by_date/day=…/`. **Resolved by**
      [`pipeline_mode_implementation_2026_05_28.md`](pipeline_mode_implementation_2026_05_28.md):
      UTL resolver + 30 tests (library@7bd14c43), BLRS stage0 fix (blrs@cf50965), QG STEP 5.85,
      backfill script (pm@9cf186cd), codex doc (pm@58115ffc). **Phase 3.2-3.4** (run backfill +
      verify + NOT NULL constraint) require operator execution — script ready at
      `scripts/migration/backfill_pipeline_mode.py --apply --all --project-id <PROJECT_ID>`.
- [x] ✅ [AGENT] P0. **Chain dimension-modeling bug → manifest massively UNDER-reports derivatives coverage.** On disk,
      option/future chains live at
      `instrument_type=options_chain|futures_chain / data_type=trades / underlying=… /     ticks.parquet` (verified
      present for DERIBIT @ 2023-06-15). But the enumerator ALSO emits phantom rows keyed
      `data_type=options_chain|futures_chain, instrument_type=''` marked `attempted_failed`. A naive coverage rollup on
      `data_type` then reports chains at ~0–2% captured when the data is actually present. Fix the enumerator to stop
      emitting `data_type=<chain>` rows and credit the `instrument_type=<chain>` rows. (This is why the first-pass
      coverage scan reported futures_chain 1.8% / options_chain 0.3% — false.) — market-tick-data-service@2e91d74f
- [x] ✅ [AGENT] P1. **Phantom `expected` rows for inapplicable venue × data_type.** e.g. `KRAKEN-SPOT` enumerated with
      `options_chain / futures_chain / derivative_ticker / liquidations` as expected+`attempted_failed`, though a SPOT
      venue has none of those products (confirmed genuinely absent on disk — correctly so). Gate the enumerator on the
      UAC capability matrix (which `(venue, data_type)` combos are real) so absent-and-inapplicable → not-enumerated,
      not `attempted_failed`. Generalises §6A honest-absence. (These phantoms dominated the false "gap" counts.) —
      market-tick-data-service@3fa29d70
- [x] ✅ DONE [AGENT] P1. **`instrument_type` case drift double-counts coverage.** Manifest holds both `PERPETUAL` and
      `perpetual` as `captured` for the same DERIBIT cell — breaks any `GROUP BY instrument_type` and inflates counts.
      Normalise instrument_type casing at the write/enumerate boundary + reconcile existing rows.
- [x] ✅ DONE [AGENT] P2. **Loose unpartitioned `*.parquet` at `raw_tick_data/by_date/` root.** Files like `BTCUSDT.parquet`,
      `BTC-PERPETUAL.parquet`, `KRW-LINK.parquet` sit directly under `by_date/` alongside the `day=…/` hive partitions —
      drift artifacts outside any day/venue/data_type partition (invisible to partition-pruned reads). Reconcile into
      the correct partition or delete. Mirrors the 2026-05-04 phantom-audit drift axes.
      → `scripts/cleanup_loose_root_parquets.py` (mtds@56fed3b) — dry-run + apply; supports --cefi-buckets.
- [x] ✅ DONE [AGENT] P0. **One-off sweep of existing phantom manifest rows** (added 2026-05-28 after post-fix diff).
      Slot 9's enumerator fixes (mtds@2e91d74f + @3fa29d70) are **preventive only** — they stop NEW backfill VMs
      emitting phantom rows but don't sweep the ~355K stale phantoms already in the live manifest (chain phantoms:
      176,270 LEGACY + 168,485 PRD; spot×derivative phantoms: 199,160 LEGACY + 79,852 PRD; counts from 2026-05-28 06:30Z
      re-download). Consolidator only aggregates per-VM shards — it doesn't re-enumerate, so re-consolidation alone
      changes nothing. Write a one-shot sweep job (or add a `--sweep-phantoms` mode to the consolidator) that DELETES
      rows matching slot 9's filter predicates: (a)
      `data_type IN ('options_chain','futures_chain') AND instrument_type IS NULL/''`, (b)
      `(venue, data_type) NOT IN VENUE_DATA_TYPE_CAPABILITIES`. Run on both `market-data-tick-cefi-{prd-,}` indexes.
      Until this lands the live manifest under-reports coverage and any spend decision must use the client-side
      corrected view, not the published index.

## Codex SSOT updates

- [ ] [AGENT] P2. Document the expiry-window request-filtering contract + the 401≠honest-absence rule in
      `codex/02-data/honest-absence-downstream-handling.md` (reason taxonomy) and the MTDS adapter docs.
- [ ] [AGENT] P2. Document the §6A honest-absence-violation classes (in-flight drop, silent-zero, captured-0-row) as
      anti-patterns + the required `record_empty`/`attempted_failed` call sites, in the same codex doc.
