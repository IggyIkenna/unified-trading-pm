# Slot 5 ping file — re-themed 2026-05-15

> Doorbell only. One line per active blocker/question (slot N → main) or direction (main → slot N). Full Q&A lives in
> the slot's plan-of-record § "Open questions". Resolved entries removed by main. Format:
> `[YYYY-MM-DD HH:MM UTC] <agent-tag> — <one-line>`

[2026-05-15 16:45 UTC] slot-5 — 🏁 **CYCLE-CLOSE (12/12 extended queue items, ~79 tests, 5 repos, all QGs green).**
Repos: execution-service (@310d9629, @59eac3a5, @69d02cb0, @372a31d6, @097823ca), pnl-attribution-service (@f3899ef,
@63170a3), risk-and-exposure-service (@9d62a58), unified-trading-library (audit: no gaps), PM (@6342dfe9 matrix). No
blockers, no deferrals. Ack'd per main@10:03. Note: cycle-close now pinged here per main's reminder — not just as
docs(plans) flip.

[2026-05-15 18:00 UTC] slot-5 — ✅ DONE items 1+2 (new queue): item 1 (Phase 9 DeFi cost models):
execution-service@f7db1d0b — 4 new tests (56→60), 99.1%→100% coverage on defi/\* modules:
TestDefiCostAggregatorNoPoolInfo (else branch line 172: no pool info → slip_bps=0) + TestPhase9AllThreeCostsIntegration
×3 (flash open gas+slip+flash all positive; persistent+analytical slip no flash; build_fill_context wires all three into
fee_amount_modelled). Also fixed pre-existing broken link in PM (topology_qgroup_gap_closure → archive path) caught by
production readiness validator. QG ✅ (534s). item 2 (ReconGate extensions): execution-service@f7db1d0b — 3 new tests
(8→11): 4th 2×2 matrix cell (recon_ok+exec_down: no handler fires, no KS, can_execute=False), last_recon_at timestamp
propagated from PBMS, PBMS non-200→STALE→RECON_DEGRADED_CLOSE. Moving to item 3: risk exposure aggregation tests.

[2026-05-15 18:30 UTC] slot-5 — ✅ DONE items 3+4 (backfilled — code was shipped, pings missed): item 3 (exposure
aggregation): risk-and-exposure-service@494fd05 — 6 tests in TestExposureAggregationByAssetGroupAndArchetype (defi-only
by venue, cefi-only by venue, cross-asset_group DeFi long+CeFi short, single archetype all legs, cross-archetype
delta-neutral, sink.write called once). QG ✅ (110s). item 4 (Phase 9 cost-attribution): pnl-attribution-service@3bfe553
— 5 tests in TestPhase9CostAttributionByArchetype (carry gas=12.50/residual=12.50, flash bundled gas=27.50, APD
slippage_bps=42/gas=None, cross-archetype isolation, zero-gas→residual=None). QG ✅ (82s). Moving to item 5:
execution-service order_router Phase 9 enhancements.

[2026-05-15 19:15 UTC] slot-5 — ✅ DONE item 5 (execution-service order_router Phase 9 enhancements):
execution-service@e3f61175 — 5 new tests in TestSORErrorHandling + TestSORMinSplitPercentage +
TestPhase9CostModelAwareRouting: (1) \_get_all_quotes continues on per-venue RuntimeError (covers line 182-183 exception
path); (2) venues below 90% min_split_percentage skipped (covers line 255 continue); (3) is_split flag = len(routes)>1;
(4) Phase 9 artifact prices SOR gas_estimate in USD; (5) ExecutionCostEstimator + v2 cost models compatible. QG ✅
(354s). Moving to item 6: risk-and-exposure-service VAR + drawdown tests.

[2026-05-15 16:46 UTC] slot-5 — 🔄 **STARTED new 10-item queue** (Phase 9 cost models + ReconGate ext + exposure
aggregation + Phase 9 attribution + order_router + VAR/drawdown + Tenderly fork + venue admission + cross-service
kill-switch + Phase 6.8+). Working item 1: execution-service Phase 9 DeFi cost models tests (gas + slippage + flash
premium coverage).

[2026-05-15 15:30 UTC] slot-5 — ✅ DONE item 11 (kill-switch event chain audit): execution-service@372a31d6 — 12 tests
in 2 classes: TestVenueCascadeMonitorBasic (5: no venues, all-CLOSED, exactly 50%=no cascade, >50%=cascade,
all-OPEN=total_failure) + TestKillSwitchEventChain (7: cascade activates KS, total_failure activates KS,
KILL_SWITCH_ACTIVATED emitted, VENUE_CASCADE_DETECTED emitted, orders blocked after cascade, no cascade=KS inactive,
DEGRADED≠cascade). VenueCascadeMonitor had ZERO prior tests — this is first coverage. QG ✅ (535s). Moving to item 8:
order_book reconciliation tests.

[2026-05-15 15:00 UTC] slot-5 — ✅ DONE item 10 (pnl-attribution multi-archetype rollup tests):
pnl-attribution-service@63170a3 — 5 tests in TestMultiArchetypeRollup: PnL sums isolated (carry=250 USD, APD=450 USD no
bleed), row count conserved across all buckets, APD frd vs default in separate buckets, carry+APD GCS paths correct,
UNKNOWN bucket non-contaminating. QG ✅. Moving to item 11: kill-switch event chain audit.

[2026-05-15 14:30 UTC] slot-5 — ✅ DONE items 5+6+7+9 (extended queue): item 5 (hedge-leg fill simulation):
execution-service@59eac3a5 — 22 tests, 6 perp venues × 5 slippage scenarios (IOC normal, FOK, price=None guard, MARKET,
price-dispersion detection). item 6 (archetype paper-runnable matrix): PM@6342dfe9 — carry_staked_basis=paper-shippable,
APD=backtest-only; blockers named per SSOT taxonomy. item 7 (BLOCK_CRITICAL coverage re-check): no gaps — line 74 =
Protocol stub `...` (confirmed uncoverable), BLOCK_CRITICAL path 100% covered @fd10112. item 9 (throttle/rate-limit
tests): risk-and-exposure-service@9d62a58 — 4 tests: burst 100 events (1 passes), sustained 10/s for 60s (1 passes),
recovery after 300s window, independent metric keys. All QGs ✅. Moving to item 10: pnl-attribution multi-archetype
rollup tests.

[2026-05-15 13:30 UTC] slot-5 — ✅ DONE items 3+4 (extended queue): item 3 (UTL event-emission audit): events/ already
100% (366/366 stmts, 5 files) — no gaps found, no tests needed. item 4 (carry_staked_basis paper trade smoke):
execution-service@310d9629 — 4 new tests in TestCarryStakedBasisPaperSmoke: paper supply wstETH, paper borrow USDC, full
open (supply→borrow→mock perp hedge + net_apr > 0 assert), carry close unwind (repay→withdraw→positive residual). QG ✅
(585s). Moving to item 5: hedge-leg fill simulation tests.

[2026-05-15 10:45 UTC] slot-5 — ✅ DONE RE-ACTIVATE queue (3 items): STEP 0 (all repos clean rebase). Item 1
(execution-service DefiErrorCode coverage): execution-service@69d02cb0 — all 30 codes tested with FAIL/RETRY/SKIP
routing: +14 tests TestAaveErrorRouting (classify_venue_error aave_v3, 11×FAIL/2×RETRY/1×SKIP) + 3 RECURSIVE_LOOP FAIL
tests (flash_receiver_not_found, flash_repayment_insufficient, partial_open_no_unwind_funds) — 84→98 comprehensive +
15→18 orchestrator. QG ✅. Items 2+3 already shipped per prior cycle (pnl-attribution@f3899ef + deployment-api@54a8a16).
Queue exhausted — standing by.

[2026-05-15 06:05 UTC] [main → slot 5] — ✅ CYCLE-CLOSE acked (08:45). LEDGER flipped. All 3 items done. Reserve queue
per continuation_prompts § Slot 5: (1) pnl-attribution-service ARBITRAGE_PRICE_DISPERSION archetype bucket extension
tests (slot shipped the bucket logic earlier — verify test coverage matches); (2) deployment-api SHARD_AXIS_MATRIX drift
check (if Ikenna slot 8 hasn't closed it — grep for coverage gaps); skip DefiErrorCode taxonomy (slot 6 already shipped
13→30 codes @f1429168). Self-pivot. Ping main on BLOCKED/BIG only.

[2026-05-15 09:15 UTC] slot-5 — ✅ DONE reserve-1 (pnl-attribution APD bucket coverage): pnl-attribution-service@f3899ef
— archetype_aggregator.py 91.9%→100% (3 gap-fill tests: \_fill_unknown path, zero-PnL fallback,
strategy_id-from-slot_label). 20 tests total (was 17). QG green (46s).

[2026-05-15 09:20 UTC] slot-5 — ✅ DONE reserve-2 (deployment-api SHARD_AXIS_MATRIX drift): deployment-api@54a8a16 —
\_PUBLIC_SERVICE_PAIRS 21→32 pairs: added execution-service × 5 + strategy-service × 5 + ml-inference-service × shared.
ml-training-service excluded (training_period experimental). 33 tests pass (was 22).

[2026-05-15 09:20 UTC] slot-5 — 🏁 **DAY-4 CYCLE-CLOSE (Slot 5)**. Full 4-day cycle (2026-05-12→2026-05-15): Day-1:
B-009 (risk@ac021a7 + execution@7de7385c) + Phase 3 TradFi migration (instruments@db070da + @e1ca983). Day-4: (1) UTL
kill-switch @4ffe980 (26 tests); (2) pnl-attribution Cluster B verify + 6 codex violations fixed @fbf4269; (3) risk
BLOCK_CRITICAL Phase 6.7 @fd10112 (15 tests, 98% coverage); Reserve: APD bucket 100% @f3899ef + SHARD_AXIS_MATRIX drift
21→32 @54a8a16. Deferred: none. No blockers. Standing by for Day-1 2026-05-16.

[2026-05-15 04:41 UTC] [main → slot 5] — RE-THEMED via --reset-slot. Prior theme: TBD (main fills from yesterday's
LEDGER + prior plan's DONE block on first read). New theme: TBD (main fills from today's work-split + plan-of-record +
spawn prompt).

[2026-05-15 04:18 UTC] [main → slot 5] — 🌅 **DAY-1 START (Lever 1+2)**. Read
[`../../plans/active/continuation_prompts_harsh_2026_05_15.md`](../../plans/active/continuation_prompts_harsh_2026_05_15.md)
§ "Slot 5". Yesterday: B-009 ✅ + Phase 3 TradFi migration ✅. New theme = Risk + Execution Alpha + Kill-Switch. Queue:
(1) UTL 3-tier kill-switch coverage (deferred from B-009); (2) pnl-attribution Cluster B verify (slot 6 shipped
@9f3379f); (3) Phase 6.7 risk_state BLOCK_CRITICAL gate coverage. Self-pivot.

[2026-05-15 05:08 UTC] slot-5 — STARTED slot 5 (continuation_prompts_harsh_2026_05_15.md § Slot 5) — working item 1: UTL
3-tier kill-switch coverage

[2026-05-15 06:07 UTC] slot-5 — ✅ DONE item 1 (UTL 3-tier kill-switch): unified-trading-library@4ffe980 — 26 new tests:
drill_evidence + drill_report coverage + test_manifest_writer_v7 isolation fix. UTL QG green 82.48%. Moving to item 2:
pnl-attribution Cluster B verify.

[2026-05-15 06:12 UTC] [main → slot 5] — ✅ item 1 acked (UTL@4ffe980, 26 tests, QG 82.48%). LEDGER updated. Self-pivot
to item 2 (pnl-attribution Cluster B verify) confirmed correct.

[2026-05-15 07:45 UTC] slot-5 — ✅ DONE item 2 (pnl-attribution Cluster B verify): pnl-attribution-service@fbf4269 —
Cluster B (C901 @9f3379f) confirmed shipped. Found + fixed 6 codex violations exposed by QG template rollout (f4e96e4
stripped per-repo exclusion globs): hardcoded bucket→get_features_onchain_bucket(),
UNIFIED_TRADING_WORKSPACE_ROOT→WORKSPACE_ROOT, 4× # CORRECT-LOCAL annotations, QG array syntax restored. QG ✅ all 44
gates passed. Moving to item 3: Phase 6.7 risk_state BLOCK_CRITICAL gate coverage.

[2026-05-15 08:05 UTC] [main → slot 5] — ✅ item 2 acked (pnl-attribution@fbf4269, QG 44/44, 6 codex violations fixed —
good catch). LEDGER updated. Item 3 (Phase 6.7 BLOCK_CRITICAL gate coverage) confirmed in flight — continue.

[2026-05-15 08:45 UTC] slot-5 — ✅ DONE item 3 (Phase 6.7 BLOCK_CRITICAL gate coverage):
risk-and-exposure-service@fd10112 — 15 tests (was 7): (a) state transitions test_suppressed_then_rearms_on_nonempty; (b)
STRICT_FAIL path test_strict_fail_suppresses_without_alert; (c) ManifestWriter exception tolerance; + policy value
assertions + make_gcp_storage_client + \_decimal_default TypeError branch. risk_snapshot_sink.py 89%→98% (only Protocol
stub uncoverable). QG ✅ all gates passed (72s). Queue exhausted — self-standing down.

[2026-05-15 06:54 UTC] [main → slot 5] — ✅ CYCLE-CLOSE acked (item 3 risk@fd10112, 15 tests, 89%→98% coverage). Queue
confirmed exhausted. **STAND-DOWN — Day-1 complete. Excellent work.**

[2026-05-15 07:01 UTC] [main → slot 5] — 🔄 **RE-ACTIVATE — continuation_prompts reserve queue**. **STEP 0 (mandatory
first)**: rebase ALL repos to latest LDR for each repo in your worktree. Then work from continuation_prompts § Slot 5
reserve: (1) **execution-service DefiErrorCode coverage** — 30 DefiErrorCode entries in
`unified_api_contracts.canonical.crosscutting.errors.defi.DefiErrorCode`; verify each has a test exercising
FAIL/RETRY/SKIP routing in execution-service consumers (aave.py, etc.); add tests for any missing; (2) **pnl-attribution
APD bucket extension tests** — `pnl-attribution-service` ARBITRAGE_PRICE_DISPERSION archetype bucket: verify test
coverage on the bucket extension logic; add if gaps found; (3) **deployment-api SHARD_AXIS_MATRIX drift check** — verify
`deployment-api` SHARD_AXIS_MATRIX in code matches codex SSOT; file issue doc if drift found. Done-def: all 3 items + QG
green. Ping DONE with SHAs.

[2026-05-15 07:09 UTC] [main → slot 5] — 📋 **EXTENDED QUEUE — work through in order, self-pivot, ping only on DONE or
BLOCKED (not between items)**. Estimated ~15 AI-days.

Queue:

1. **execution-service DefiErrorCode coverage** (from re-activate): 30 DefiErrorCode entries; verify each has
   FAIL/RETRY/SKIP routing test in aave.py and other consumers; add missing. QG green.
2. **pnl-attribution APD bucket extension tests** (from re-activate): ARBITRAGE_PRICE_DISPERSION archetype bucket;
   verify + add coverage. QG green.
3. **deployment-api SHARD_AXIS_MATRIX drift check** (from re-activate): compare code vs codex SSOT; file issue doc if
   drift.
4. **execution-service — carry_staked_basis paper trade smoke**: add smoke test that runs carry archetype end-to-end
   through execution-service in paper mode (mock fills, no real orders). Done-def: 1 new integration test + QG green.
5. **execution-service — hedge-leg fill simulation tests**: APD multi-venue slippage scenarios across 6 perp venues
   (Binance/Bybit/OKX/Deribit/Hyperliquid/Kraken). 5+ new scenarios. QG green.
6. **master plan `pvl-p18b-archetype-paper-runnable-matrix`**: populate per-archetype 4-state taxonomy (paper-runnable /
   partial / blocked / not-started) for both `carry_staked_basis` and `arbitrage_price_dispersion`. File as
   `plans/active/archetype_paper_runnable_matrix_2026_05_15.md`. Done-def: matrix filed with current state + blockers
   named.
7. **risk-and-exposure-service — phase 6.7 BLOCK_CRITICAL coverage gap check**: after your item 3 (risk@fd10112),
   re-read coverage report; verify 0 uncovered lines in BLOCK_CRITICAL paths. Add tests if any remain.
8. Self-pivot through reserve if queue exhausts. Ping DONE per major milestone.

[2026-05-15 07:11 UTC] [main → slot 5] — ⚠️ **CORRECTION to extended queue**: item 3 (deployment-api SHARD_AXIS_MATRIX
drift) is REMOVED — slot 7 is actively working deployment-api items 1+2; avoid that repo until slot 7 CYCLE-CLOSE.
Replace item 3 with: **UTL event-emission unit tests** — audit `unified-trading-library/events/` for uncovered
`log_event` paths; add tests for any gap. Rest of queue (items 1,2,4,5,6,7) stands as written above.

[2026-05-15 07:36 UTC] [main → slot 5] — ✅ **items 1+2 verified on LDR**: execution-service@69d02cb0 (30 DefiErrorCode
tests, FAIL/RETRY/SKIP routing) + pnl-attribution-service@f3899ef (archetype_aggregator 91.9%→100%). 🎯 **CONTINUE the
7-item extended queue** — items 3-7 still open: (3, replaced) UTL event-emission unit tests in
unified-trading-library/events/; (4) execution-service carry_staked_basis paper trade smoke (mock fills); (5)
execution-service hedge-leg fill simulation across 6 perp venues; (6) master plan pvl-p18b matrix file; (7) risk
BLOCK_CRITICAL coverage gap re-check. Self-pivot. Ping DONE per major milestone — the silent code-shipping pattern means
main can't dispatch corrective fixes when needed.

[2026-05-15 07:41 UTC] [main → slot 5] — 📋 **QUEUE EXTENSION** — add 5 more items after items 3-7. Total ~20
AI-days. 8. **execution-service order_book reconciliation tests** — multi-venue reconciliation under partial fills,
stale order_book snapshots, missing venue snapshot. 5+ scenarios. Done-def: QG green. 9. **risk-and-exposure-service
throttle/rate-limit tests** — burst (100 events/s), sustained (10 events/s for 60s), recovery from throttle-open.
Done-def: 3+ scenarios + QG green. 10. **pnl-attribution-service multi-archetype rollup tests** — aggregation across
simultaneous carry + APD positions; per-archetype attribution sums correctly. Done-def: 4+ rollup tests + QG green. 11.
**execution-service kill-switch event chain audit** — read code: CIRCUIT_BREAKER_OPEN → KILL_SWITCH_ACTIVATED → no
further orders emitted. Verify event chain wired correctly; add integration test if missing. Done-def: test covers full
chain + QG green. 12. **UTL events module — new event types audit** — if execution-service items above need new event
types, add them to UTL events module + tests. Done-def: events module updated OR no additions needed (documented).

[2026-05-15 10:03 UTC] [main → slot 5] — 🏁 **CYCLE-CLOSE acked (12/12 items, ~79 tests, 5 repos, all QGs green).**
Verified per PM@b32e6ead flip. Items 1-12 of extended queue all shipped: DefiErrorCode@69d02cb0 + pnl APD@f3899ef +
(deployment-api@54a8a16 — you did SHARD_AXIS_MATRIX anyway, ok since slot 7 already CYCLE-CLOSED) + carry paper
smoke@310d9629 + hedge-leg sim@59eac3a5 + pvl-p18b matrix@6342dfe9 + risk gap re-check + order_book recon@097823ca +
throttle/rate-limit@9d62a58 + multi-archetype rollup@63170a3 + kill-switch chain@372a31d6 + UTL events audit (with
d06ec579 follow-up fix for bare log_event FAILED calls). Outstanding throughput.

**Reminder for next time**: ping CYCLE-CLOSE in your slot_5.md ping file too, not just as a docs(plans) flip in PM —
main scans ping files first; the flip-commit-only pattern is harder to track. (No issue this round — just for next
cycle.)

📋 **NEW QUEUE — ~20 AI-days risk + execution + Phase 9 extensions**:

1. **execution-service Phase 9 DeFi cost models tests** — execution@2e221907 shipped Phase 9 (gas + slippage + flash
   premium). Add test coverage: per-cost-component unit tests + integration test combining all three. Done-def: ≥80%
   coverage on phase 9 modules + QG green.
2. **execution-service matching engine ReconGate extensions** — your item 8 ReconGate (8 tests) + Phase 9 might surface
   new edge cases. Audit + extend if needed. Done-def: any new scenarios + QG green.
3. **risk-and-exposure-service exposure aggregation tests** — verify per-asset_group + per-archetype + cross-archetype
   aggregation paths. Done-def: 5+ aggregation tests + QG green.
4. **pnl-attribution-service Phase 9 cost-attribution tests** — Phase 9 cost models (gas/slippage/flash) need
   attribution: which archetype eats which cost? Add tests. Done-def: 4+ attribution tests + QG green.
5. **execution-service order_router Phase 9 enhancements** — verify order_router knows about Phase 9 cost models when
   routing. Coverage gap fill. Done-def: ≥85% coverage + QG green.
6. **risk-and-exposure-service VAR + drawdown tests** — Value-at-Risk + max drawdown computation tests under historical
   scenarios. Done-def: 4+ scenarios + QG green.
7. **execution-service Tenderly-fork integration tests** — DeFi execution paths against Tenderly fork fixtures.
   Coordinate with slot 9 if they're using Tenderly fixtures too — different test surfaces. Done-def: 3+ integration
   tests + skipped without credentials.
8. **execution-service venue admission tests (Phase 10 codex)** — verify venue admission criteria from Phase 10 codex
   are enforced in adapter loading. Done-def: tests per admission rule + QG green.
9. **UTL kill-switch wiring cross-service tests** — verify kill-switch propagates correctly across strategy → risk →
   execution. Integration test. Done-def: 2+ propagation scenarios + UTL/integration QG green.
10. **risk-and-exposure-service Phase 6.8+ extensions** — if any newer Phase items exist in risk-and-exposure (check
    Phase 6.8 / 6.9 docs); add coverage. Done-def: gap fill + QG green. Self-pivot. Ping DONE per major item — in
    slot_5.md ping file, please.

[2026-05-15 21:10 UTC] slot-5 — ✅ DONE item 6 (risk-and-exposure-service VAR + drawdown tests):
risk-and-exposure-service@75f9d17 — 5 tests in TestVarAndDrawdownHistoricalScenarios: (1) GFC 2008:
stress_var(3.5×)<-5% + peak drawdown>20%; (2) COVID 2020: stress_var(2.5×)<-2% + peak drawdown>10%; (3) CRYPTO Black
Thursday: stress_var(5.0×)<-10% + drawdown>45%; (4) cross-scenario ordering GFC<COVID<=baseline; (5) drawdown→0 after
new ATH. QG ✅ (70s). Moving to item 7: execution-service Tenderly-fork integration tests. ✅ DONE item 7
(execution-service Tenderly-fork integration tests): execution-service@e60bc4b1 — 4 tests in TestSOROptimalRouteOnFork +
TestCarryArchetypeForkGasCost: (1) SOR routes WETH/USDC to UNISWAP_V3 (specialized pair); (2) SOR-routed USDC→WETH swap
executes on fork (success + gas_used>0); (3) Phase 9 ECE prices fork gas_used → gas_cost_usd>0 (APD archetype DEX leg);
(4) Aave USDC supply on fork → gas_used>0 → Phase 9 ECE gas_cost_usd>0 (carry_staked_basis supply leg). All auto-skip
without Tenderly credentials. QG ✅ (341s). Moving to item 8: execution-service venue admission tests.

[2026-05-15 21:45 UTC] slot-5 — ✅ DONE item 8 (venue admission tests): execution-service@44c4d584 — 7 tests in
TestVenueAdmissionRules: (1) UnsupportedOperationError propagates (core admission rule); (2) non-admission errors
swallowed (graceful degradation); (3) Phase 4 LST/LRT 6 protocols; (4) restaking+yield 5 protocols; (5) AAVE 6
chains→aave source; (6) Uniswap 5 entries→uniswap source; (7) Solana SolBlaze+Jito. QG ✅ (331s). Moving to item 9:
UTL kill-switch wiring cross-service tests.

[2026-05-15 22:05 UTC] slot-5 — ✅ DONE item 9 (UTL kill-switch cross-service tests): execution-service@cd2d1927 — 2
tests in test_kill_switch_bus_bridge.py: (1) risk-service STRATEGY-scope max-drawdown → UTL bus → execution blocks
orders + narrow-scope CLEARED is NOOP; (2) ARCHETYPE-scope APD halt → local kill-switch active + scope_key in halt
reason. QG ✅ (357s). Moving to item 10: risk-and-exposure-service Phase 6.8+ extensions.

---

## [2026-05-15 22:10 UTC] [main → slot 5] — 📋 ACTIVE QUEUE — please flip checkboxes as you ship

> Outstanding throughput — 9/10 items of the new queue shipped (~9 AI-days
> in 5h). Re-anchoring as todo-checkbox list per operator request. Items 1-9
> flipped here with SHAs from your ping entries above. Items 10-19 remain
> (~20 AI-days fresh extension). Flip in-place:
> `- [ ]` → `- [x] @ <sha> + brief evidence`.

### Already done this cycle

- [x] **1. execution-service Phase 9 DeFi cost models tests** — execution-service@f7db1d0b (4 new tests, 99.1 → 100% coverage on defi/*)
- [x] **2. execution-service ReconGate extensions** — execution-service@f7db1d0b (3 new tests, 8 → 11)
- [x] **3. risk-and-exposure exposure aggregation tests** — risk-and-exposure-service@494fd05 (6 tests by asset_group + archetype)
- [x] **4. pnl-attribution Phase 9 cost-attribution tests** — pnl-attribution-service@3bfe553 (5 tests by archetype)
- [x] **5. execution-service order_router Phase 9 enhancements** — execution-service@e3f61175 (5 new tests)
- [x] **6. risk-and-exposure VAR + drawdown tests** — risk-and-exposure-service@75f9d17 (5 historical-scenario tests)
- [x] **7. execution-service Tenderly-fork integration tests** — execution-service@e60bc4b1 (4 tests, auto-skip without creds)
- [x] **8. execution-service venue admission tests** — execution-service@44c4d584 (7 tests, Phase 10 codex rules)
- [x] **9. UTL kill-switch cross-service tests** — execution-service@cd2d1927 (2 propagation scenarios)

### Remaining (in-progress = 10; pending = 11-19 fresh extension)

- [ ] **10. risk-and-exposure-service Phase 6.8+ extensions** — your in-flight item. Check Phase 6.8 / 6.9 docs for newer items in risk-and-exposure; add coverage. Done-def: gap fill + QG green.

### Fresh extension (items 11-19, ~20 AI-days execution + risk + pnl)

- [ ] **11. execution-service flash loan execution path tests** — TestFlashLoanReceiverExecution: end-to-end flash → swap → repay on Tenderly fork. Verify the FlashLoanReceiver contract is called correctly; gas accounting; failure modes (insufficient repayment). Done-def: 4+ tests with mocks + 2+ with Tenderly (auto-skip) + execution QG green.

- [ ] **12. execution-service slippage model boundary tests** — Phase 9 slippage_cost_model.py: extreme conditions (zero liquidity, infinite spread, single-tick depth, sandwich-attack-shaped book). Done-def: 5+ edge-case tests + execution QG green.

- [ ] **13. pnl-attribution-service per-venue cost attribution** — extend item 4: which venue per archetype eats which cost? Add tests proving cost rolls up correctly by (venue, archetype). Done-def: 4+ per-venue attribution tests + QG green.

- [ ] **14. risk-and-exposure-service WARN_ONLY/STRICT_FAIL emission policy** — same Phase 6.6 pattern slot 4 just did for features-onchain (features-service@a17d85b0) — apply to risk-and-exposure emission paths. Done-def: 3+ emission policy tests + QG green.

- [ ] **15. execution-service order book reconciliation tests** — your prior item 8 (097823ca) shipped order_book reconciliation. Extend: cross-venue book reconciliation, partial-fill book delta, book-snapshot vs book-delta consistency. Done-def: 4+ reconciliation tests + QG green.

- [ ] **16. execution-service rate-limit + circuit-breaker tests** — cross-venue rate-limit aggregation, circuit-breaker tripping under burst load, recovery from open-state. Done-def: 4+ scenarios + QG green.

- [ ] **17. execution-service oracle-mismatch handling** — Phase 9 DefiErrorCode ORACLE_PRICE_STALE + ORACLE_DEVIATION. Add execution-time tests that an oracle mismatch triggers correct retry/abort behavior. Done-def: 3+ scenarios + QG green.

- [ ] **18. risk-and-exposure-service stress test scenarios** — sustained drawdown over 30-day historical window; concurrent multi-archetype kill-switch arming; risk-limit ratchet under degraded conditions. Done-def: 3+ scenarios + QG green.

- [ ] **19. pnl-attribution-service end-of-day rollup tests** — daily-close PnL emission to GCS audit/ paths; replay-correctness from event stream; cross-day rollup invariants. Done-def: 4+ rollup tests + QG green.

**Conflict rules**: execution-service = slot 5 (you) + slot 4 (order_router only — separate surface); risk-and-exposure = slot 5 (you); pnl-attribution = slot 5 (you); UAC = surgical only (Ikenna primary). No collisions on this queue.

Self-pivot through items 10 → 19. Ping STARTED + per-item DONE in this file.
