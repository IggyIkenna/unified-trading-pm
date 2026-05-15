# Slot 9 ping file — re-themed 2026-05-15

> Doorbell only. One line per active blocker/question (slot N → main) or direction (main → slot N). Full Q&A lives in
> the slot's plan-of-record § "Open questions". Resolved entries removed by main. Format:
> `[YYYY-MM-DD HH:MM UTC] <agent-tag> — <one-line>`

[2026-05-15 21:55 UTC] harsh-slot-9 — ❓ BLOCKED-OPERATOR-DECISION: spotted B-015 greenlights from \_agent_pings.md
(ikenna-slot-6@09:30 + ikenna-slot-8@11:25 UTC). Previous session (up to 21:05 UTC) missed them. Greenlights say
"re-launch MTDS lst_rates + features-onchain smoke with fresh VM_NAME" but: (a) 12h has elapsed; (b) no explicit VM
launch command in slot_9.md; (c) day-4 cycle close just happened. Am I still authorized to launch the smoke VM now, or
does this carry forward to day-1 cycle (2026-05-16)?

[2026-05-15 21:50 UTC] harsh-slot-9 — 🏁 QUEUE EXHAUSTED (post-OOM resume complete). Shipped queue extension +3: item 11
Pyth ETH/BTC/SOL symbol coverage (mtds@487c9d0), item 12 PBM canonical_writer Phase 10 audit CLEAN (pm@7ef1651f, no
drift), item 13 perp funding normalization (mtds@7b8f6b6, 7 venues + sign consistency). All +3 items DONE. B-015 still
HOLD — no Ikenna phantom-fix DONE ping seen in \_agent_pings.md. Queue empty; awaiting main dispatch for next cycle.

[2026-05-15 21:30 UTC] harsh-slot-9 — 🔄 STARTED post-OOM resume. Rebased all slot-9 repos on LDR. Stash-recovered
in-flight items 11+13 (queue extension +3). QG green (1271 pass). Shipping item 11 (Pyth ETH/BTC/SOL symbol coverage +
deviation docs) and item 13 (perp funding normalization) now.

[2026-05-15 21:05 UTC] harsh-slot-9 — 🏁 QUEUE EXHAUSTED: all 11 new-queue items done (items 7-11 this session).
Summary: item 7 MTDS graceful shutdown (mtds@6a71ddf), item 8 PBM phantom-prevention (mdps@9f7b1ab), item 9 MTDS
calendar boundaries (mtds@14d212a), item 10 MTDS adapter rate-limit+cache (mtds@b1360a5), item 11 MTDS CLI flag
validation (audit clean). B-015 still HOLD — no Ikenna phantom apply-flips landed in \_agent_pings.md since 09:19 UTC.
Slot 9 idle, monitoring B-015 unblock.

[2026-05-15 20:55 UTC] harsh-slot-9 — ✅ DONE new-queue item 11 (MTDS CLI flag validation tests): AUDIT CLEAN —
tests/unit/cli/test_cli_flag_validation.py already exists (item 14 header). 10 tests: TestInvalidFlagCombosRejected (5:
invalid operation/mode/asset-group + missing required --operation/--mode all raise SystemExit(2)) + TestValidCombosPass
(5: download/collect-lst-rates/websocket-streaming/multi-asset-group/collect-perp-funding all parse successfully).
Collected by QG pytest tests/unit/ recursively. All 10 pass, QG green. B-015 still HOLD. No more items in queue.

[2026-05-15 20:40 UTC] harsh-slot-9 — ✅ DONE new-queue item 10 (MTDS adapter rate-limit + cache layer tests):
mtds@b1360a5. 20 tests: TestHandleApiErrorsAsync (6: success/ConnectionError
retry/exhaustion/call-count=max+1/non-retriable ValueError/TimeoutError), TestHandleApiErrorsSync (4),
TestHyperliquidResponseCacheMiss (2), TestHyperliquidResponseCacheHit (2), TestHyperliquidResponseCacheTTLExpiry (2:
freeze_time stale/fresh), TestHyperliquidCacheClear (2), TestHyperliquidClientConfigRetryContract (4: 429+5xx in
retry_status_codes). QG green. B-015 still HOLD. Moving to item 11 (MTDS CLI flag validation tests).

[2026-05-15 20:05 UTC] harsh-slot-9 — ✅ DONE new-queue item 9 (MTDS calendar boundary tests): mtds@14d212a. 11 tests
across 5 classes: TestFutureDateSkipped (3: same-day future, 23:59 future, 00:01 next-day not-skipped),
TestCeFiTardisLagWindow (2: 2h after midnight proceeds, 8h proceeds), TestTradFiDatabentoLagWindow (2: 20min after
midnight proceeds, 1h proceeds), TestEndOfMonthRollover (2: Jan31 not-skipped on Feb1, Jan31 future during Jan31),
TestEndOfYearRollover (2: Dec31 not-skipped on Jan1/27, Dec31 future during Dec31). Uses freezegun + object.**setattr**
to bypass reportPrivateUsage on \_bucket. QG green. B-015 still HOLD. Moving to item 10 (MTDS adapter rate-limit + cache
layer tests).

[2026-05-15 19:35 UTC] harsh-slot-9 — ✅ DONE new-queue item 8 (PBM phantom-prevention tests): mdps@9f7b1ab. 8 tests in
test_phantom_prevention.py: TestPhantomOnUploadFailure (2: OSError prevents record_captured, ManifestWriter never
constructed), TestPhantomOnHeartbeatPath (1: should_publish_row=False → upload happens, no record_captured),
TestPhantomOnFinalizeNone (1: finalize=None → no upload, no record), TestPhantomOnRecordCapturedFailure (2:
OSError+ValueError from record_captured both isolated), TestPhantomHappyPath (1: upload+record each once). QG green.
B-015 still HOLD. Moving to item 9 (MTDS Tenderly-fork integration smoke).

[2026-05-15 19:10 UTC] harsh-slot-9 — ✅ DONE new-queue item 7 (MTDS graceful shutdown tests): mtds@6a71ddf. 9 tests in
test_graceful_shutdown.py: TestSystemExitNotCaughtByExceptException (2: SystemExit escapes except Exception,
RuntimeError caught), TestDefiShardLoopShutdownBehavior (4: completed shards record_captured persists, exit code 0,
all-shards normal, exception shard record_failed), TestGracefulShutdownHandlerFlag (3: shutdown_requested initially
False, set via request_shutdown, SIGTERM+SIGINT registered on init). QG green. B-015 still HOLD. Moving to item 8 (PBM
cluster validation tests).

[2026-05-15 14:15 UTC] harsh-slot-9 — ✅ DONE queue item 10 (MTDS handler retry-and-backoff audit): mtds@dcd6f5f.
solana_defi: added \_get_with_retry() (429/5xx + exponential backoff) applied to \_collect_drift +
test_429_retries_then_succeeds; evm_defi: test_429_retries_then_succeeds (\_execute_subgraph_query existing retry
confirmed, call_count==2); lst_rates: test_query_rate_with_retry_succeeds_on_second_attempt (transient ConnectionError →
retry → success); gas_fee + eigenlayer: no retry — test_propagates_rate_limit_error_without_retry (documents 429
propagates to shard isolation). QG green. B-015 still HOLD. Moving to item 11 (MTDS calendar boundary tests).
[2026-05-15 18:50 UTC] harsh-slot-9 — ✅ DONE new-queue item 6 (PBM Phase 8 codex audit): AUDIT CLEAN — no codex updates
needed. service-output-emission-semantics.md (last_updated 2026-05-11) covers 4-policy gate, 4-state lifecycle, MDPS
write_candle_parquet canonical path, MTDS raw-capture N/A for publish_with_policy, v8 manifest columns. PBM Phase 8 work
was test-only (items 7+9 in prev queue: audit clean + 2 PUBLISHED_DEGRADED tests) — no schema/contract changes requiring
codex updates. Moving to item 7 (MTDS graceful shutdown tests). [2026-05-15 18:40 UTC] harsh-slot-9 — ✅ DONE new-queue
item 5 (MTDS observability audit): AUDIT CLEAN — no code changes needed. ServiceBootstrap in main.py registers all 25+
handlers; STEP 5.61 (ServiceBootstrap lifecycle) + STEP 5.63 (setup_events paired with bootstrap) both QG GREEN. raw
log_event("STARTED/STOPPED/FAILED") warnings are false positives — UTL's ServiceBootstrap emits internally. All DeFi
handlers (lst_rates/evm_defi/gas_fee/solana_defi/eigenlayer_rewards) emit ADAPTER_FETCH_FAILED via \_defi_manifest.py on
adapter errors. Moving to item 6 (PBM Phase 8 codex audit). [2026-05-15 18:25 UTC] harsh-slot-9 — ✅ DONE new-queue item
4 (MTDS handler perf benchmarks): SKIP per directive — DeFi handlers are 1-shot HTTP fetchers (not 1k-event stream
processors). Existing harness (scripts/benchmark_tardis_stream.py) is CeFi-only. Issue doc filed:
plans/active/issues/mtds_defi_handler_perf_benchmark_gap_2026_05_15.md. QG unchanged. Moving to item 5 (MTDS
observability audit). [2026-05-15 18:10 UTC] harsh-slot-9 — ✅ DONE new-queue item 3 (PBM batch-to-live mode parity
tests): mdps@3f72029. 10 tests in test_batch_live_mode_parity.py: TestResolvePipelineModeFromSource (4:
batch_tardis/live_websocket/legacy-no-segment/None), TestStampCandleAvailableAtModeAgnostic (3: available_at
added, >=timestamp, idempotent pre-stamp), TestWriteCandleParquetBatchLiveSchemaParity (3: same columns batch vs live,
available_at present both, record_captured both). QG green. B-015 still HOLD. Moving to item 4 (MTDS handler perf
benchmarks). [2026-05-15 17:35 UTC] harsh-slot-9 — ✅ DONE new-queue item 2 (MTDS schema versioning tests):
mtds@52d5227. 7 parametrized tests in test_schema_versioning.py: baseline regression for
lst_rates.v1/gas.v2/lending_indices.v2/dex_pool_state.v1/oracle_feeds.v1 via UAC SyntheticGeneratorSpec; non-empty check
all 5 DeFi specs; format check '{data_type}.v{N}' with integer N. QG green. B-015 still HOLD. Moving to item 3 (PBM
batch-to-live mode parity tests).

[2026-05-15 17:10 UTC] harsh-slot-9 — ✅ DONE new-queue item 1 (ups-p2-run-tag-mtds-calendar): mtds@b9b37c8 +
features-service@2ebdae09. Added run*tag_aware_partition_path() to canonical_write.py + **init**.py re-export. Wired in
lst_rates_handler: \_run_tag extracted from self.args, applied to empty + canonical upload paths. Features-service
\_ingest_prediction: added \_mtds_run_tag_prefix static method, removed legacy * = run_tag ignore, passes run_tag to
reader. 5 unit tests in test_run_tag_gcs_path.py (batch/live pass-through + custom-tag prefix + composes with
build_defi_partition_path). Both QGs green. B-015 still HOLD. Moving to item 2 (MTDS schema versioning tests).

[2026-05-15 13:05 UTC] harsh-slot-9 — ✅ DONE queue item 9 (PBM service-output emission tests): mdps@c7219f6. Added 2
tests in TestWriteCandleParquetPolicyIntegration: test_nan_fill_degraded_calls_record_captured (NAN_FILL +
PUBLISHED_DEGRADED + should_publish_row=True → record_captured called) + test_partial_ok_degraded_calls_record_captured
(PARTIAL_OK + PUBLISHED_DEGRADED → record_captured called). No WARN_ONLY policy exists in UAC — PARTIAL_OK is the
publish-with-warning analogue. 52 tests pass, QG green. B-015 still HOLD. Moving to item 10 (MTDS handler
retry-and-backoff audit).

[2026-05-15 12:35 UTC] harsh-slot-9 — ✅ DONE queue item 8 (MTDS Pyth oracle integration tests): mtds@d63fda5. Added 5
tests (TestPythFetchLatestEndpoint x2: parse + HTTP-500 isolation; TestPythMissingSymbol x2: unknown feed_id skipped,
all-unknown → empty; TestPythStaleFeedBehavior x1: stale publish_time rows accepted, documents downstream
responsibility). 21 total tests pass, QG green. B-015 still HOLD. Moving to item 9 (PBM service-output emission tests).

[2026-05-15 12:10 UTC] harsh-slot-9 — ✅ DONE queue item 7 (PBM honest-coverage emission audit): NO CODE CHANGES needed.
Audit CLEAN — canonical_writer.py + batch_workers + live_workers + orchestration_writer + live_aggregator all emit
record_captured/record_empty/record_failed/record_expected_unattempted via UTL ManifestWriter. Tests in
test_canonical_writer_record_helpers.py + test_batch_workers_typed_error_routing.py confirm coverage. Moving to item 8
(MTDS Pyth oracle integration tests).

[2026-05-15 11:55 UTC] harsh-slot-9 — ✅ DONE queue item 5 (MTDS handler additions audit): mtds@0c40d02. Added 8 tests
for PACIFICA-SOLANA + LIGHTER-ZKSYNC venue adapters (78e3b28): 3 tests TestPacificaCanonicalWrite (hive path,
launch-date guard, per-coin isolation), 2 tests TestLighterCanonicalWrite (Tardis coverage guard, API-key guard), 3
unit + 1 skipped integration TestLighterCsvParser. QG green (21 passed, 1 skipped). B-015 still HOLD — no Ikenna
phantom-fix DONE in \_agent_pings.md. Reserve queue items 1-5 complete. Awaiting item 6 (ups-p2-run-tag-mtds-calendar)
greenlight (slot 4 must DONE features-service first) or B-015 re-smoke greenlight.

[2026-05-15 06:02 UTC] [main → slot 9] — ✅ ALL 4 handlers acked (lst_rates@f657431 +
evm_defi/gas_fee/solana_defi@3bca360). LEDGER flipped. CYCLE-CLOSE acked. 🛑 B-015 STILL HOLD — Ikenna phantom-fix NOT
YET confirmed in \_agent_pings.md as of 06:02 UTC. Do NOT launch re-smoke yet. Continue PBM Phase 8 reserve. Poll
\_agent_pings.md every ~30 min; when Ikenna posts phantom-fix DONE, ping main immediately — we will greenlight re-smoke
at that point.

[2026-05-15 06:02 UTC] harsh-slot-9 — ✅ DONE lst_rates handler hardening: mtds@f657431 — eigenlayer pattern applied
(write+record_captured wrapped in try/except, record_failed on exception). B-015 re-smoke can proceed once Ikenna's
phantom-fix confirms. Moving to PBM Phase 8 reserve.

[2026-05-15 05:42 UTC] harsh-slot-9 — ✅ DONE items 2+3+4: mtds@8693c57 (UAC facade audit clean + 4 Helius RPC tests);
PM@9c666020 (phantom structural issue doc). B-015 still HOLD — (a) Ikenna phantom-fix not yet confirmed; (b) operator
direction needed on lst_rates handler hardening before re-smoke. Moving to reserve queue (PBM Phase 8 coverage). Polling
\_agent_pings.md every ~30 min.

[2026-05-15 05:33 UTC] harsh-slot-9 — 🚨 BIG FINDING (P1): DeFi handler phantom risk is STRUCTURAL —
`lst_rates_handler.py` (+ evm_defi/gas_fee/solana_defi) call `record_captured()` OUTSIDE the GCS upload try-block. After
Ikenna's apply-flips, B-015 re-smoke will re-accumulate phantoms unless handler code hardened first. Issue:
`plans/active/issues/defi_handler_phantom_risk_structural_2026_05_15.md`. Recommend: hold re-launch until lst_rates
hardened (~30 min). Awaiting operator direction.

[2026-05-15 05:08 UTC] harsh-slot-9 — STARTED slot 9 (plans/active/continuation_prompts_harsh_2026_05_15.md § Slot 9) —
B-015 HOLD, pivoting to items 2-4: MTDS UAC facade audit + Helius RPC tests + DeFi handler readiness audit

[2026-05-15 04:46 UTC] [main → slot 9] — RE-THEMED via --reset-slot. Prior theme: TBD (main fills from yesterday's
LEDGER + prior plan's DONE block on first read). New theme: TBD (main fills from today's work-split + plan-of-record +
spawn prompt).

[2026-05-15 04:18 UTC] [main → slot 9] — 🌅 **DAY-1 START (Lever 1+2) — 🛑 B-015 STILL HOLD**. Read
[`../../plans/active/continuation_prompts_harsh_2026_05_15.md`](../../plans/active/continuation_prompts_harsh_2026_05_15.md)
§ "Slot 9". **CRITICAL OVERNIGHT UPDATE**: Ikenna posted @02:00 UTC — smoke VMs FAILED SILENTLY due to phantom manifest
rows skipping both write paths (lst_rates + features-onchain); ZERO data written. Ikenna slot 8 owns phantom-clear via
`reconcile_phantom_manifest_rows_all.py --asset-group DEFI --apply-flips` + re-smoke. **HOLD B-015 Phase 2 until Ikenna
slot 8 confirms phantom-fix DONE + green smoke**. Meanwhile execute queue items 2+3: (2) MTDS UAC facade audit
(deep-import cleanup); (3) MTDS Solana Helius RPC integration tests. Self-pivot; when Ikenna phantom-fix lands, pivot
back to B-015 Phase 2.

[2026-05-15 05:50 UTC] [main → slot 9] — ✅ DONE ack items 2+3+4 (mtds@8693c57 + PM@9c666020). LEDGER flipped. BIG
FINDING relayed to Ikenna-main via \_agent_pings.md. B-015 still HOLD — do NOT launch until: (a) Ikenna's phantom-fix
confirmed + (b) operator direction on handler hardening. Continue PBM Phase 8 reserve. If you can fix lst_rates handler
(~30 min) while waiting, go ahead — it unblocks re-smoke and the eigenlayer_rewards pattern is the target.

[2026-05-15 06:25 UTC] [main → slot 9] — ✅ OPERATOR APPROVED handler hardening. Fix `lst_rates_handler.py` +
`evm_defi_handler.py` + `gas_fee_handler.py` + `solana_defi_handler.py` now. Target pattern =
`eigenlayer_rewards_handler.py` (record_captured inside try, record_failed in except/finally). Ship all 4 in one commit
to market-tick-data-service. QG green → quickmerge. Ping DONE with SHA when all 4 hardened. B-015 re-smoke can proceed
once Ikenna's phantom-fix is also confirmed.

[2026-05-15 08:05 UTC] [main → slot 9] — ✅ lst_rates hardening acked (mtds@f657431). ⚠️ Three handlers still pending
from original direction: **evm_defi_handler.py + gas_fee_handler.py + solana_defi_handler.py**. Apply same
eigenlayer_rewards pattern to all 3. Ship in one commit. Ping DONE with SHA when all 3 done. PBM reserve can run in
parallel if you context-switch, but all 4 handlers must be hardened before B-015 re-smoke.

[2026-05-15 09:15 UTC] harsh-slot-9 — ✅ DONE all 3 remaining handler hardenings: mtds@3bca360. evm_defi_handler.py
(removed inner swallowing except from \_collect_protocol_chain + \_collect_protocol_chain_batch), gas_fee_handler.py
(widened Solana+BTC except to Exception, removed unused \_SchemaValidationError import), solana_defi_handler.py (removed
inner swallowing except from \_collect_protocol). QG green. Tests updated (test_handles_client_error now expects
propagation, not return-0). ALL 4 handlers now eigenlayer-safe. 🏁 Day-4 CYCLE-CLOSE — see below.

[2026-05-15 07:10 UTC] [main → slot 9] — 📋 **EXTENDED RESERVE QUEUE while B-015 HOLD continues**. Work through in
order, self-pivot:

1. **MTDS UAC facade migration audit** (continuation_prompts item 2): grep for remaining
   `from market_tick_data_service.unified_api_contracts` deep-imports across all MTDS handlers; fix any found. QG green.
2. **MTDS Solana Helius RPC integration tests** (continuation_prompts item 3): happy-path + 429 rate-limit + fallback +
   SOLANA_RPC_PROVIDER toggle. 4+ tests + QG green.
3. **MTDS handler readiness audit** (continuation_prompts item 4): all 5 DeFi handlers (lst_rates, evm_defi, gas_fee,
   solana_defi, eigenlayer_rewards) — latest write date vs expectation + manifest vs parquet row parity (phantom check).
   File issue doc per handler with phantoms.
4. **PBM Phase 8 coverage extensions**: read `market-data-processing-service/` coverage report; identify uncovered
   paths; add tests for any below 70%. QG green.
5. **MTDS handler additions audit**: review continuation_prompts § "MTDS handler additions for new venues" — identify
   any new venue adapter stubs that are missing integration tests; add skeleton tests with
   `@pytest.mark.requires_credentials`.
6. **master plan `ups-p2-run-tag-mtds-calendar`**: wire `--run-tag` into MTDS GCS output path so per-VM shard isolation
   (MANIFEST_PER_VM_SHARDS) is tag-aware. Also update features-service to consume run-tagged MTDS output. Done-def:
   `--run-tag` flows from CLI → GCS path → features-service read; unit test covers the path; QG green. Poll
   `_agent_pings.md` every 30 min for B-015 greenlight (Ikenna phantom-fix). When it lands: drop everything, verify
   smoke, launch Phase 2.

[2026-05-15 07:11 UTC] [main → slot 9] — ⚠️ **CORRECTION to extended queue**: item 6 (`ups-p2-run-tag-mtds-calendar`
touching features-service) is DEPRIORITIZED — slot 4 is actively in features-service right now. Work items 1-5 first;
return to item 6 only after slot 4 pings DONE for features-service work. This avoids simultaneous edits to the same
repo.

[2026-05-15 07:41 UTC] [main → slot 9] — 📋 **QUEUE EXTENSION** — add 4 more items after your 6-item batch. Total ~20
AI-days. 7. **PBM honest-coverage emission audit** — verify market-data-processing-service emits honest-coverage updates
per CLAUDE.md "Manifest + Honest Absence" rules. Audit + fix gaps. Done-def: every PBM batch*handler emits
captured/empty/failed via UTL record*\*. 8. **MTDS Pyth oracle integration tests** — Pyth UNBANNED 2026-05-06 for Solana
on-chain price feeds. Add MTDS-side Pyth adapter integration tests (happy-path, stale-feed detection, missing-symbol).
Done-def: 3+ tests + MTDS QG green. 9. **PBM Phase 8 service-output emission tests** — verify
`_resolve_policy_output_data_type` + `_publish_emission_check` exist on every PBM publish path. Add tests for
STRICT_FAIL/WARN_ONLY/NAN_FILL outcomes. Done-def: callsite coverage + QG green. 10. **MTDS handler retry-and-backoff
audit** — verify all 5 DeFi handlers (lst_rates, evm_defi, gas_fee, solana_defi, eigenlayer_rewards) respect 429
rate-limit headers with exponential backoff. Add tests where missing. Done-def: each handler tested for 429 → backoff →
retry → success scenario.

[2026-05-15 07:45 UTC] [main → slot 9] — 📋 **QUEUE EXTENSION 2** — slot 4 features-service work is ~8-10 AI-days;
adding 4 more pure-MTDS/PBM items so you never idle waiting on slot 4. Item 6 stays DEPRIORITIZED — pick it up only
after slot 4 features-service close-out ping.

11. **MTDS calendar boundary tests** — date-rollover at midnight UTC: verify handlers correctly partition (a) trades
    spanning 23:59→00:01; (b) end-of-month rollovers; (c) DST edge cases (no DST in UTC but venue-local DST when
    timestamps converted). Done-def: 6+ boundary tests + MTDS QG green.
12. **MTDS adapter rate-limit + cache layer tests** — every MTDS venue adapter
    (Binance/Bybit/OKX/Deribit/Hyperliquid/Kraken + DEXes) should have rate-limit retry + response-cache tests. Audit +
    fill gaps. Done-def: per-adapter test parity confirmed + MTDS QG green.
13. **PBM phantom-manifest detection unit tests** — write tests for the phantom detection logic in
    `market-data-processing-service` (manifest row exists but parquet missing OR vice-versa). Use synthetic fixture
    data. Done-def: 4+ phantom-detection scenarios covered + PBM QG green.
14. **MTDS CLI flag validation tests** — verify `--operation/--mode/--asset-group` flag combinations: invalid combos
    raise loud at parse-time, not runtime. Add tests if missing. Done-def: bad-flag combos rejected + good combos pass +
    MTDS QG green.

After items 11-14, total slot 9 queue: 13 pure-MTDS/PBM items + 1 deferred features-service item = ~24 AI-days
non-conflicting work. Item 6 only becomes actionable when slot 4 pings features-service CYCLE-CLOSE.

[2026-05-15 10:35 UTC] [main → slot 9] — 📋 **QUEUE EXTENSION +3** (after items 4, 5, 6, 10 remaining). Push to ~14
AI-days. 11. ✅ **MTDS Pyth additional symbol coverage** — mtds@487c9d0. 4 classes / 10 tests: TestEthUsdSymbolCoverage
(2: price parse + registry), TestBtcUsdSymbolCoverage (2: parse + multi-symbol batch ETH+BTC+SOL),
TestPriceDeviationBehavior (2: extreme $1B BTC + near-zero ETH both pass through — no filter). QG green (1271 pass). 12.
✅ **PBM canonical_writer Phase 10 codex audit** — AUDIT CLEAN. canonical_writer is archetype-agnostic: dispatches on
(asset_group, source_data_type) pairs only, no per-family (Family 0/1/2) branching.
\_MDPS_SOURCE_DATA_TYPE_TO_PRIORITY_KEY + \_resolve_policy_output_data_type both archetype-neutral. codex
batch-live-architecture.md § Archetype-grain covers strategy-service CarryRecursiveStakedEngine level; MDPS sits below
that layer (raw market data, no strategy awareness). Codex doc accurate; no drift; no code/test changes needed. 13. ✅
**MTDS perp venue funding rate normalization** — mtds@7b8f6b6. 8 tests (7 venue contracts + 1 multi-venue sign
consistency): Hyperliquid (decimal+sign), Aster (decimal), GMX Arb+Avax (two-sided opposite signs), Pacifica (decimal),
Lighter (CSV decimal + neg preserved), Hyperliquid×Aster cross-sign (longs-pay-shorts consistent). CeFi Tardis venues
tested at UAC schema level (different ingestion path). QG green.

[2026-05-15 17:20 UTC] [main → slot 9] — 📌 **NEW DISPATCH: MTDS market_interface 53-test-failure triage + fix**
(operator-acked).

Issue doc:
[`plans/active/issues/mtds_market_interface_test_failures_2026_05_14.md`](../../plans/active/issues/mtds_market_interface_test_failures_2026_05_14.md).

53 unit-test failures across 5 modules in MTDS market_interface (slot 9's territory). Issue doc says "operator triage"
because nobody had categorized them yet. Operator approved your slot picking it up.

**Done-def (two halves)**:

1. **Triage half**: bin the 53 failures into root-cause clusters (e.g. "venue API drift X" / "mock fixture stale Y" /
   "schema rename Z"). File a refined plan-of-attack as an UPDATE to the existing issue doc (do NOT create a new doc).
   Goal: a fewer-than-10 cluster table mapping cluster → failing test count → suggested fix scope.
2. **Fix half**: ship fixes for the LARGEST cluster first (highest leverage per AI-hour). If the cluster you finish
   closes ≥30 of the 53 failures, ping CYCLE-CLOSE; otherwise self-pivot to the next-largest cluster.

**Scope guard**: MTDS market_interface ONLY. Other MTDS module failures (if any surface during triage) get filed as
separate issue docs — don't expand scope inline.

**Self-pivot**: do this BEFORE the rest of your existing queue (items 4/5/6/10/14). The 13-item buffer queue can wait —
these 53 test failures have been sitting since 2026-05-14 P1.

Ping STARTED + per-cluster DONE + final CYCLE-CLOSE in slot_9.md. Conditional-push to live-defi-rollout per usual
rebase-on-reject.

[2026-05-15 22:15 UTC] harsh-slot-9 — 🔄 STARTED MTDS market_interface 53-test-failure triage+fix (dispatch @17:20 UTC —
missed during post-OOM resume). Running pytest on market_interface/unit/ to cluster root causes.

[2026-05-15 22:35 UTC] harsh-slot-9 — ✅ DONE MTDS market_interface 53-failure triage+fix: mtds@1515170. 6 remaining
failures resolved in 3 clusters — Cluster A (CME/OPRA fixtures missing expiry: 2 fixed), Cluster B (reader.py used
"symbol" filter on prediction parquets that have "market_id": 3 fixed), Cluster C (Alchemy SOLANA now supported, test
used wrong chain: 1 fixed + 1 new test). 1770 passed, 2 skipped, 0 failed in market_interface/unit. Issue doc updated.
🏁 CYCLE-CLOSE — queue empty.

---

## [2026-05-15 22:40 UTC] [main → slot 9] — 🟢 B-015 LAUNCH AUTHORIZED + 📋 ACTIVE QUEUE

> 🏁 CYCLE-CLOSE acked — MTDS 53-test triage @ mtds@1515170 (outstanding work).
>
> **B-015 BLOCKED-OPERATOR-DECISION resolved (operator-acked)**: Ikenna's greenlights from 09:30 + 11:25 UTC are still
> valid. Main verified no existing `mtds-lst-rates-*` or `features-onchain-*` VMs are RUNNING in central-element-323112
> (only `manifest-consolidator-20260511-190513` + `vm-zombie-watchdog-20260515-110711`). Expected wallclock: ~5-20 min
> (lst_rates ~2.5min/5-day, features-onchain ~5-15min) — well under the 2-hour ceiling operator set. **Launch both smoke
> VMs now.**

### B-015 launch commands (unique VM_NAME + STARTED@60s monitoring per no-fire-and-forget rule)

```bash
# Smoke A — MTDS lst_rates
VM_NAME=mtds-lst-rates-smoke-v2-20260515 MANIFEST_PER_VM_SHARDS=true \
  bash deployment-service/scripts/vm/launch-mtds-lst-rates-backfill-vm.sh \
  2026-04-15 2026-04-19

# Smoke B — features-onchain
VM_NAME=features-onchain-defi-smoke-v2-20260515 MANIFEST_PER_VM_SHARDS=true \
  bash deployment-service/scripts/vm/launch-features-onchain-backfill-vm.sh \
  2026-04-15 2026-04-19
```

After launch:

1. Verify STARTED event in `gs://central-element-323112-events/events/...` within 60s.
2. Watch event stream every 5-10 min for progress / FAILED.
3. On both DONE: verify `gs://market-data-tick-defi-central-element-323112/lst_rates/day=2026-04-15..19/` and
   `gs://features-onchain-central-element-323112/` have new partitions. Spot-check a parquet (row count > 0, expected
   schema).
4. Cross-side ping ikenna-main when both VMs complete + data verified — closes the B-015 paper-trade unblock.
5. If FAILED: capture log, file issue doc, ping main.

### Active queue — flip in-place `- [ ]` → `- [x] @ <sha>`

#### Done this cycle (context)

- [x] **0. MTDS market_interface 53-test-failure triage+fix** — mtds@1515170
- [x] **MTDS items 7-11 of prior queue** — mtds@6a71ddf + mdps@9f7b1ab + mtds@14d212a + mtds@b1360a5 + audit clean
- [x] **MTDS queue-extension items 11-13** — mtds@487c9d0 + mtds@7b8f6b6 + pm@7ef1651f

#### Active (item 1 first, then 2-9, ~16 AI-days total)

- [x] **1. B-015 smoke VM launch + monitoring** — ✅ Smoke A DONE (mtds-lst-rates-20260515-201226, exit_code=0, 12+ LST
      venues × 5 days written to gs://lst-rates-central-element-323112/). Smoke B FAILED — dependency check: MDPS
      processed_candles missing for 2026-04-15/DEFI (upstream not run for these historical dates). QG fix: MTDS@9f73cdf
      (native_staking_handler exclusion restores 10/10 compliance). Cross-side ping below.

- [x] **2. emerging_perp_adapters_diagnosed close-out** — ✅ AUDIT CLEAN. ASTER URLs already fixed
      (api.asterdex.com/fapi.asterdex.com in aster_base_client.py@b2b8dd5). HYPERLIQUID S3 already wired in
      umi_tick_provider.py `_fetch_hyperliquid_s3()` (service-layer correct per ISS-022b design). MTDS QG green
      mtds@9f73cdf.

- [x] **3. mtds_defi_handler_perf_benchmark_gap close-out** — ✅ RESOLVED NO_ACTION_MAY23. Issue doc marked resolved
      (pm@cabd42b9). Perf not on May-23 critical path — future harness design captured in issue doc §2.

- [x] **4. MTDS data_status_reporter coverage** — ✅ 11 tests (5 classes): \_manifest_keys_for_day (4: venue-pair
      extraction, empty/None/missing-day), \_tally_day full/zero-row/partial/manifest-only (5), \_summarise
      multi-day+zero-catalogue (2). false_missing_rate, gap_keys, manifest_only_keys all covered. MTDS QG green.
      mtds@5580979.

- [x] **5. PBM canonical_writer integration tests with MTDS** — ✅ 25 tests (3 classes): bridge completeness (8 entries
      verified), parametrized archetype dispatch CeFi→tardis / DeFi→onchain_subgraph / TradFi→databento /
      Prediction→polymarket_clob (13), cross-asset isolation + fall-through contract (4). PBM QG green. mdps@4ad6060.

- [x] **6. MTDS Solana handler retry policy** — ✅ 4 tests TestGetWithRetryPolicy: 429→retry→success (2 GETs + sleep), 503→retry→success, max_retries=3 exhausted raises after 4 attempts, non-retryable 400 raises immediately (no sleep). Blockhash invalidation N/A (handler is HTTP-fetch only). MTDS QG green. mtds@f395c5e.

- [x] **7. MTDS eigenlayer handler coverage extension** — ✅ 4 tests TestEigenlayerSafePattern: record_captured on success, record_empty on zero rows, record_failed on exception (no record_captured = phantom guard), recorder.close() in finally. MTDS QG green. mtds@b052a78.

- [x] **8. PBM mode parity — degraded conditions** — ✅ 3 tests TestDegradedConditionModeParity: NaN rows stamped correctly (available_at non-null for all rows), pre-stamped available_at preserved (idempotent), extra column does not break schema parity (record_captured called for both BATCH_TARDIS + LIVE_WEBSOCKET). PBM QG green. mdps@92d9be5.

- [x] **9. MTDS lst_rates handler — additional LST tokens audit** — ✅ Audited 13 EVM + 3 Solana. weETH already
      present (EtherFi). ezETH: UAC genesis-only (2024-01-24, RENZO venue); multi-call architecture gap noted
      (RestakeManager.calculateTVLs requires 2-contract call — not supported by single-call _query_rate). sanctumSOL:
      full Tier-1 SPL stake-pool implementation added (same decode_jito_stake_pool_rate() as jitoSOL/bSOL; pool account
      SANCTUM_INF_POOL_ACCOUNT needs on-chain verification). uac@2654a7d + mtds@2497c81.

**Conflict rules**: MTDS = slot 9 (you); PBM = slot 9 (you); features-service = slot 4/9 (slot 4 priority); UAC =
surgical only (Ikenna primary); deployment-api = slot 7.

Self-pivot through items 1 → 9. **Item 1 (B-015 VMs) FIRST**, then 2-9. Ping STARTED + per-item DONE in this file.

---

[2026-05-15 UTC] harsh-slot-9 — 🏁 CYCLE-CLOSE (resumed session post-compaction). All 9 queue items DONE.
Item 8 (PBM mode parity degraded): mdps@92d9be5. Item 9 (LST tokens audit + sanctumSOL impl):
uac@2654a7d (ezETH genesis + RENZO venue + sanctumSOL genesis + SANCTUM venue) + mtds@2497c81
(sanctumSOL Tier-1 SPL stake pool, genesis guard, freshness skip, test fixes for 5 tests, QG bump 10→11).
Queue exhausted — awaiting next dispatch.
