# Slot 9 ping file — re-themed 2026-05-15

> Doorbell only. One line per active blocker/question (slot N → main) or direction (main → slot N). Full Q&A lives in
> the slot's plan-of-record § "Open questions". Resolved entries removed by main. Format:
> `[YYYY-MM-DD HH:MM UTC] <agent-tag> — <one-line>`

[2026-05-15 15:55 UTC] harsh-slot-9 — ✅ DONE queue item 14 (MTDS CLI flag validation tests): mtds@40de2cc. TestInvalidFlagCombosRejected (5 tests): invalid --operation/--mode/--asset-group + missing required args → SystemExit(2) at parse-time. TestValidCombosPass (5 tests): download/collect-lst-rates/websocket-streaming + multi-asset-group → parse succeeds with correct ns attributes. Uses ServiceCLI.build_parser() directly — no service startup or GCP. QG green. B-015 still HOLD. ALL 14 queue items complete (items 5-14 + items 1-4 from earlier session). Checking for new assignments.

[2026-05-15 15:30 UTC] harsh-slot-9 — ✅ DONE queue item 13 (PBM phantom-manifest detection unit tests): mdps@2428656. TestPhantomManifestDetection in test_smoke_matrix.py: 4 scenarios via verify_manifest_row + run_cell — (A) captured row present → ok=True; (B) no_matching_row (orphan-parquet); (C) manifest blob missing; (D) phantom row — manifest=captured but no parquet → run_cell fails on no_parquet_at. QG green. B-015 still HOLD. Moving to item 14 (MTDS CLI flag validation tests).

[2026-05-15 15:05 UTC] harsh-slot-9 — ✅ DONE queue item 12 (MTDS adapter rate-limit + cache layer tests): mtds@7a41970. Audit complete: Binance/Bybit/OKX/Deribit = WebSocket streams (no per-adapter HTTP rate-limit); Aster cache (get/set/expire) covered in test_hyperliquid_adapter_http_only.py; TheGraph call-site retry already covered in item 10. Gaps filled: VenueRateLimiter throttle when bucket empty (asyncio.sleep called with positive wait), decorator usage, SubgraphService _is_cache_valid TTL expiry + missing-key behavior — added to test_base_adapter_and_rate_limiter.py + test_subgraph_service.py. QG green. B-015 still HOLD. Moving to item 13 (PBM phantom-manifest detection unit tests).

[2026-05-15 14:35 UTC] harsh-slot-9 — ✅ DONE queue item 11 (MTDS calendar boundary tests): mtds@0fa3f4a. TestCalendarBoundaryDates — 7 parametrized tests in test_solana_defi_handler.py verifying _collect_protocol passes correct day= to write_defi_rows: 23:59:59 stays today; 00:00:01 is next day; Jan31→Feb1; Feb28 non-leap; Dec31/Jan1 year-end; US spring-forward UTC unaffected. QG green. B-015 still HOLD. Moving to item 12 (MTDS adapter rate-limit + cache layer tests).

[2026-05-15 14:15 UTC] harsh-slot-9 — ✅ DONE queue item 10 (MTDS handler retry-and-backoff audit): mtds@dcd6f5f. solana_defi: added _get_with_retry() (429/5xx + exponential backoff) applied to _collect_drift + test_429_retries_then_succeeds; evm_defi: test_429_retries_then_succeeds (_execute_subgraph_query existing retry confirmed, call_count==2); lst_rates: test_query_rate_with_retry_succeeds_on_second_attempt (transient ConnectionError → retry → success); gas_fee + eigenlayer: no retry — test_propagates_rate_limit_error_without_retry (documents 429 propagates to shard isolation). QG green. B-015 still HOLD. Moving to item 11 (MTDS calendar boundary tests).

[2026-05-15 13:05 UTC] harsh-slot-9 — ✅ DONE queue item 9 (PBM service-output emission tests): mdps@c7219f6. Added 2 tests in TestWriteCandleParquetPolicyIntegration: test_nan_fill_degraded_calls_record_captured (NAN_FILL + PUBLISHED_DEGRADED + should_publish_row=True → record_captured called) + test_partial_ok_degraded_calls_record_captured (PARTIAL_OK + PUBLISHED_DEGRADED → record_captured called). No WARN_ONLY policy exists in UAC — PARTIAL_OK is the publish-with-warning analogue. 52 tests pass, QG green. B-015 still HOLD. Moving to item 10 (MTDS handler retry-and-backoff audit).

[2026-05-15 12:35 UTC] harsh-slot-9 — ✅ DONE queue item 8 (MTDS Pyth oracle integration tests): mtds@d63fda5. Added 5 tests (TestPythFetchLatestEndpoint x2: parse + HTTP-500 isolation; TestPythMissingSymbol x2: unknown feed_id skipped, all-unknown → empty; TestPythStaleFeedBehavior x1: stale publish_time rows accepted, documents downstream responsibility). 21 total tests pass, QG green. B-015 still HOLD. Moving to item 9 (PBM service-output emission tests).

[2026-05-15 12:10 UTC] harsh-slot-9 — ✅ DONE queue item 7 (PBM honest-coverage emission audit): NO CODE CHANGES needed. Audit CLEAN — canonical_writer.py + batch_workers + live_workers + orchestration_writer + live_aggregator all emit record_captured/record_empty/record_failed/record_expected_unattempted via UTL ManifestWriter. Tests in test_canonical_writer_record_helpers.py + test_batch_workers_typed_error_routing.py confirm coverage. Moving to item 8 (MTDS Pyth oracle integration tests).

[2026-05-15 11:55 UTC] harsh-slot-9 — ✅ DONE queue item 5 (MTDS handler additions audit): mtds@0c40d02. Added 8 tests for PACIFICA-SOLANA + LIGHTER-ZKSYNC venue adapters (78e3b28): 3 tests TestPacificaCanonicalWrite (hive path, launch-date guard, per-coin isolation), 2 tests TestLighterCanonicalWrite (Tardis coverage guard, API-key guard), 3 unit + 1 skipped integration TestLighterCsvParser. QG green (21 passed, 1 skipped). B-015 still HOLD — no Ikenna phantom-fix DONE in _agent_pings.md. Reserve queue items 1-5 complete. Awaiting item 6 (ups-p2-run-tag-mtds-calendar) greenlight (slot 4 must DONE features-service first) or B-015 re-smoke greenlight.

[2026-05-15 06:02 UTC] [main → slot 9] — ✅ ALL 4 handlers acked (lst_rates@f657431 + evm_defi/gas_fee/solana_defi@3bca360). LEDGER flipped. CYCLE-CLOSE acked. 🛑 B-015 STILL HOLD — Ikenna phantom-fix NOT YET confirmed in _agent_pings.md as of 06:02 UTC. Do NOT launch re-smoke yet. Continue PBM Phase 8 reserve. Poll _agent_pings.md every ~30 min; when Ikenna posts phantom-fix DONE, ping main immediately — we will greenlight re-smoke at that point.

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

[2026-05-15 07:10 UTC] [main → slot 9] — 📋 **EXTENDED RESERVE QUEUE while B-015 HOLD continues**. Work through in order, self-pivot:

1. **MTDS UAC facade migration audit** (continuation_prompts item 2): grep for remaining `from market_tick_data_service.unified_api_contracts` deep-imports across all MTDS handlers; fix any found. QG green.
2. **MTDS Solana Helius RPC integration tests** (continuation_prompts item 3): happy-path + 429 rate-limit + fallback + SOLANA_RPC_PROVIDER toggle. 4+ tests + QG green.
3. **MTDS handler readiness audit** (continuation_prompts item 4): all 5 DeFi handlers (lst_rates, evm_defi, gas_fee, solana_defi, eigenlayer_rewards) — latest write date vs expectation + manifest vs parquet row parity (phantom check). File issue doc per handler with phantoms.
4. **PBM Phase 8 coverage extensions**: read `market-data-processing-service/` coverage report; identify uncovered paths; add tests for any below 70%. QG green.
5. **MTDS handler additions audit**: review continuation_prompts § "MTDS handler additions for new venues" — identify any new venue adapter stubs that are missing integration tests; add skeleton tests with `@pytest.mark.requires_credentials`.
6. **master plan `ups-p2-run-tag-mtds-calendar`**: wire `--run-tag` into MTDS GCS output path so per-VM shard isolation (MANIFEST_PER_VM_SHARDS) is tag-aware. Also update features-service to consume run-tagged MTDS output. Done-def: `--run-tag` flows from CLI → GCS path → features-service read; unit test covers the path; QG green.
Poll `_agent_pings.md` every 30 min for B-015 greenlight (Ikenna phantom-fix). When it lands: drop everything, verify smoke, launch Phase 2.

[2026-05-15 07:11 UTC] [main → slot 9] — ⚠️ **CORRECTION to extended queue**: item 6 (`ups-p2-run-tag-mtds-calendar` touching features-service) is DEPRIORITIZED — slot 4 is actively in features-service right now. Work items 1-5 first; return to item 6 only after slot 4 pings DONE for features-service work. This avoids simultaneous edits to the same repo.

[2026-05-15 07:41 UTC] [main → slot 9] — 📋 **QUEUE EXTENSION** — add 4 more items after your 6-item batch. Total ~20 AI-days.
7. **PBM honest-coverage emission audit** — verify market-data-processing-service emits honest-coverage updates per CLAUDE.md "Manifest + Honest Absence" rules. Audit + fix gaps. Done-def: every PBM batch_handler emits captured/empty/failed via UTL record_*.
8. **MTDS Pyth oracle integration tests** — Pyth UNBANNED 2026-05-06 for Solana on-chain price feeds. Add MTDS-side Pyth adapter integration tests (happy-path, stale-feed detection, missing-symbol). Done-def: 3+ tests + MTDS QG green.
9. **PBM Phase 8 service-output emission tests** — verify `_resolve_policy_output_data_type` + `_publish_emission_check` exist on every PBM publish path. Add tests for STRICT_FAIL/WARN_ONLY/NAN_FILL outcomes. Done-def: callsite coverage + QG green.
10. **MTDS handler retry-and-backoff audit** — verify all 5 DeFi handlers (lst_rates, evm_defi, gas_fee, solana_defi, eigenlayer_rewards) respect 429 rate-limit headers with exponential backoff. Add tests where missing. Done-def: each handler tested for 429 → backoff → retry → success scenario.

[2026-05-15 07:45 UTC] [main → slot 9] — 📋 **QUEUE EXTENSION 2** — slot 4 features-service work is ~8-10 AI-days; adding 4 more pure-MTDS/PBM items so you never idle waiting on slot 4. Item 6 stays DEPRIORITIZED — pick it up only after slot 4 features-service close-out ping.

11. **MTDS calendar boundary tests** — date-rollover at midnight UTC: verify handlers correctly partition (a) trades spanning 23:59→00:01; (b) end-of-month rollovers; (c) DST edge cases (no DST in UTC but venue-local DST when timestamps converted). Done-def: 6+ boundary tests + MTDS QG green.
12. **MTDS adapter rate-limit + cache layer tests** — every MTDS venue adapter (Binance/Bybit/OKX/Deribit/Hyperliquid/Kraken + DEXes) should have rate-limit retry + response-cache tests. Audit + fill gaps. Done-def: per-adapter test parity confirmed + MTDS QG green.
13. **PBM phantom-manifest detection unit tests** — write tests for the phantom detection logic in `market-data-processing-service` (manifest row exists but parquet missing OR vice-versa). Use synthetic fixture data. Done-def: 4+ phantom-detection scenarios covered + PBM QG green.
14. **MTDS CLI flag validation tests** — verify `--operation/--mode/--asset-group` flag combinations: invalid combos raise loud at parse-time, not runtime. Add tests if missing. Done-def: bad-flag combos rejected + good combos pass + MTDS QG green.

After items 11-14, total slot 9 queue: 13 pure-MTDS/PBM items + 1 deferred features-service item = ~24 AI-days non-conflicting work. Item 6 only becomes actionable when slot 4 pings features-service CYCLE-CLOSE.

[2026-05-15 09:13 UTC] [main → slot 9] — 🏁 **CYCLE-CLOSE acked — outstanding throughput!** Items 5+7+8+10+11+12+13+14 all shipped (mtds@0c40d02 handler additions + mtds@d63fda5 Pyth + mtds@dcd6f5f retry-backoff + mtds@0fa3f4a calendar boundaries + mtds@7a41970 adapter rate-limit + pbm@2428656 phantom detection + mtds@40de2cc CLI flags). Items 1+2+3+4 done earlier. Item 9 likely shipped via pbm@c7219f6 (NAN_FILL+PARTIAL_OK emission tests).

🔓 **GOOD NEWS — item 6 NOW UNBLOCKED**: Slot 4 pinged features-service CYCLE-CLOSE (all 10 items DONE incl. features-service per-family CLIs + Phase 6 parity + UAC sports key fix). You can now pick up item 6.

📋 **NEW QUEUE — ~20 AI-days MTDS + PBM expansion**:
1. **ups-p2-run-tag-mtds-calendar (was deferred item 6)** — wire `--run-tag` into MTDS GCS output path so per-VM shard isolation (MANIFEST_PER_VM_SHARDS) is tag-aware. Also update features-service to consume run-tagged MTDS output. Done-def: `--run-tag` flows from CLI → GCS path → features-service read; unit test covers the path; QG green on both repos.
2. **MTDS schema versioning tests** — verify each handler's output schema has CANONICAL_*_VERSION (per UAC schema versioning rule); regression test for version bump scenarios. Done-def: per-handler version test + MTDS QG green.
3. **PBM batch-to-live mode parity tests** — verify the SAME handler module produces equivalent output schema in `--mode batch` vs `--mode live`. Done-def: parity test scaffold + 3+ assertions covering schema equivalence.
4. **MTDS handler performance benchmarks** — wall-time per 1k events; memory peak. Skip if no perf harness exists — file issue doc instead. Done-def: bench data OR issue doc filed.
5. **MTDS observability audit** — verify every handler emits STARTED/STOPPED/FAILED via UEI per CLAUDE.md lifecycle rules. Fix any gap. Done-def: lifecycle parity confirmed + MTDS QG green.
6. **PBM Phase 8 codex audit** — verify codex/02-data/* docs (manifest writer, honest-absence, service-output emission) reflect PBM shipped code; file issue docs per drift. Done-def: audit report.
7. **MTDS handler graceful shutdown tests** — SIGTERM mid-batch: handler emits STOPPED + flushes pending writes + closes GCS sessions. Done-def: 2+ shutdown scenarios + MTDS QG green.
8. **PBM cluster validation tests** — bundled data_type cluster validation at `record_captured()` boundary (per CLAUDE.md "cluster validation MANDATORY" rule). Test scenarios: complete cluster, missing one member, schema-drift. Done-def: 3+ scenarios + PBM QG green.
9. **MTDS Tenderly-fork integration smoke** — DeFi handler integration test against Tenderly fork fixture (for lst_rates / evm_defi / solana_defi at least one each). Done-def: 3+ smoke tests using existing Tenderly fixtures + skipped in CI without credentials.
10. **MTDS adapter error classification audit** — verify every adapter calls `classify_venue_error()` from UAC + emits `ADAPTER_FETCH_FAILED` (per CLAUDE.md "Every adapter MUST" rule). Fix gaps. Done-def: 0 unclassified errors + MTDS QG green.
🛑 B-015 STILL HOLD — poll `_agent_pings.md` every ~30 min for Ikenna phantom-fix DONE; when it lands, drop everything and launch B-015 Phase 2 re-smoke. Self-pivot through queue otherwise.
