[2026-05-19 15:00 UTC] slot-1-main → slot 4 (Harsh side) — 🔴 OPERATOR BROADCAST: commit + push your dirty work to slot branch + FF to LDR. See [`plans/active/_operator_broadcast_2026_05_19_commit_dirty_work.md`](../../plans/active/_operator_broadcast_2026_05_19_commit_dirty_work.md). Ack here once your tab is clean.

---

> **⚠️ STALE LEDGER — superseded by 2026-05-19 work split.** Booting agents: ignore history below. Read
> `plans/active/work_split_2026_05_19_harsh.md` § Slot 4 for your tasks today. This file is kept for audit trail only.

---

# Slot 4 ping file — re-themed 2026-05-15

> Doorbell only. One line per active blocker/question (slot N → main) or direction (main → slot N). Full Q&A lives in
> the slot's plan-of-record § "Open questions". Resolved entries removed by main. Format:
> `[YYYY-MM-DD HH:MM UTC] <agent-tag> — <one-line>`

[2026-05-15 04:40 UTC] [main → slot 4] — RE-THEMED via --reset-slot. Prior theme: TBD (main fills from yesterday's
LEDGER + prior plan's DONE block on first read). New theme: TBD (main fills from today's work-split + plan-of-record +
spawn prompt).

[2026-05-15 04:18 UTC] [main → slot 4] — 🌅 **DAY-1 START (Lever 1+2)**. Read
[`../../plans/active/continuation_prompts_harsh_2026_05_15.md`](../../plans/active/continuation_prompts_harsh_2026_05_15.md)
§ "Slot 4". Yesterday: B-006 ✅ + strategy Wave 4 ✅ (1582 passed). New theme = Test Failures Absorption & Service
Lifecycle Coverage. Queue: (1) features-service per-family CLI lifecycle audit; (2) risk+execution lifecycle
re-validation; (3) ml-inference Phase 6.6 emission policy coverage. Self-pivot.

[2026-05-15 05:07 UTC] slot-4 — STARTED slot 4 (Test Failures Absorption & Service Lifecycle Coverage); beginning item
1: features-service per-family CLI lifecycle audit

[2026-05-15 07:30 UTC] slot-4 — 🏁 **CYCLE-CLOSE slot 4**. All 3 queue items complete. (1) features-service per-family
lifecycle audit ✅ — 8 test_lifecycle_events.py files added (8 per-family CLIs); QG passed; pushed 8545412c. (2)
risk+execution re-validation ✅ — existing tests verified passing; no code changes needed. (3) ml-inference Phase 6.6
emission policy ✅ — 7 new tests (TestFilterByEmissionPolicy ×4 + TestPartialOkNanFillOutcomes ×3); pre-existing
batch_handler.py QG violations fixed (method size, DependencyFailure type, import patterns); QG passed; pushed 320ac6e.

[2026-05-15 07:38 UTC] [main → slot 4] — ✅ CYCLE-CLOSE acked. All BACKLOG items are DONE/DISPATCHED — no new dispatch
available. Pull from reserve queue per continuation_prompts § Slot 4: (1) features-service Phase 6 emission policy
parity check (delta_one + cross_instrument + onchain publish_with_policy coverage); (2) instruments-service test
extensions on Phase 3 migration script; (3) cross-repo test diagnostic backlog (any pre-existing failures → file issue
docs). Self-pivot through reserve. Ping main only on BLOCKED/BIG finding.

[2026-05-15 09:15 UTC] slot-4 — Reserve item 1 ✅ features-service Phase 6.5 P2 emission policy parity: found + fixed
BIG FINDING — features-onchain-service AND features-cross-instrument-service both had wrong UAC service key
("features-service" instead of per-service name), causing all groups to fall back to STRICT_FAIL including
BLOCK_CRITICAL risk_params/health_factor (no P0 alerts firing). Fixed in UAC (8c70dc5 + d3b9528); added
TestUACPolicyParity classes to 3 family test files (541cb9ee). Beginning reserve item 2: instruments-service Phase 3
migration script test extensions.

[2026-05-15 10:45 UTC] slot-4 — Reserve item 2 ✅ instruments-service Phase 3 migration script test extensions: 15→23
tests (8 new — PUT option parse, invalid-date-digits→None, non-tradfi blob rejection, corrupt-bytes read failure, upload
failure, mixed OCC+non-OCC partial repair, no-expiration-column skip, dry-run unresolvable reporting); fixed 2
pre-existing QG violations (qg-deep-import + qg-os-env noqa comments); QG passed (85s); pushed e29ebf3. Beginning
reserve item 3: cross-repo test diagnostic backlog.

[2026-05-15 11:20 UTC] slot-4 — Reserve item 3 ✅ cross-repo test diagnostic: features-service QG structurally broken
(pytest tests/unit/ → 3.16% coverage, always fails; 350 per-family unit test files invisible to gate including 26 new
TestUACPolicyParity tests). UAC QG passes (66s), ml-inference QG passes (69s) — both within tolerance. Issue doc filed:
plans/active/issues/features_service_qg_test_path_mismatch_2026_05_15.md. Fix requires main/Ikenna: add per-repo PYTEST
path override to base-service.sh SSOT. 🏁 All 3 reserve items complete.

[2026-05-15 06:45 UTC] [main → slot 4] — ✅ All reserve items acked. UAC service key fix (BLOCK_CRITICAL) ✅ +
instruments@e29ebf3 ✅. 🚨 BIG FINDING relayed to operator (features-service QG test path mismatch — surfaced in chat).
Issue doc noted. Fix to base-service.sh SSOT is queued for main/Ikenna triage. STAND-DOWN — excellent Day-1 work.

[2026-05-15 07:00 UTC] [main → slot 4] — 🔄 **RE-ACTIVATE — continuation_prompts reserve queue**. **STEP 0 (mandatory
first)**: rebase ALL repos to latest LDR (`git fetch origin && git rebase origin/live-defi-rollout`) for each repo in
your worktree — pick up PYTEST_UNIT_DIR fix (PM@c7786b2f + features@ccd44d97) and other morning commits. Then work in
order from continuation_prompts § Slot 4 Day-1 queue: (1) **B-006 extension** — features-service per-family CLI
(delta_one, volatility, sports, etc.) STARTED/STOPPED/FAILED test coverage; each family CLI gets lifecycle test OR
documented exemption; (2) **B-006 verification** — read
`risk-and-exposure-service/tests/unit/test_lifecycle_events.py` +
`execution-service/tests/unit/test_lifecycle_events.py`; confirm coverage matches spec; fix gaps; (3)
**ml-inference-service Phase 6.6 emission policy coverage** — WARN_ONLY / NAN_FILL / STRICT_FAIL policy outcome tests
for ml-inference publish_with_policy path. Reserve: features-service Phase 6 emission policy parity (delta_one +
cross_instrument + onchain). Done-def: items 1-3 + QG green per repo. Ping DONE with SHAs.

[2026-05-15 07:09 UTC] [main → slot 4] — 📋 **EXTENDED QUEUE — work through in order, self-pivot, ping only on DONE or
BLOCKED (not between items)**. Estimated ~15 AI-days. No inter-item blocking deps.

Queue:

1. **features-service per-family CLI lifecycle coverage** (from re-activate): each family CLI (delta_one, volatility,
   sports, onchain, commodity, multi_timeframe, calendar) gets STARTED/STOPPED/FAILED test OR documented exemption. QG
   green. SHA → next.
2. **B-006 verification — risk + execution lifecycle re-validation**: read
   `risk-and-exposure-service/tests/unit/test_lifecycle_events.py` +
   `execution-service/tests/unit/test_lifecycle_events.py`; confirm vs B-006 spec; fix gaps. QG green.
3. **ml-inference-service Phase 6.6 emission policy tests**: WARN_ONLY / NAN_FILL / STRICT_FAIL outcomes for
   ml-inference `publish_with_policy` path. QG green.
4. **features-service Phase 6 emission policy parity check**: delta_one + cross_instrument + onchain families — each
   calls `publish_with_policy` at write boundary. Verify or add. QG green.
5. **instruments-service Phase 3 migration script tests**: `instruments-service/scripts/migration_*.py` — unit tests for
   any migration scripts lacking coverage. Done-def: migration scripts ≥70% covered.
6. **Cross-repo test diagnostic backlog**: grep for `@pytest.mark.skip` without reason comments across features-service,
   instruments-service, execution-service; fix or file issue docs for each.
7. **master plan `rdt-p4-workspace-qg`**: Run `bash scripts/quality-gates.sh` on the 5 repos touched by Phase 3 TradFi
   migration (instruments-service, market-tick-data-service, features-service, execution-service,
   risk-and-exposure-service). Report pass/fail per repo. File issue doc for any new failures.
8. Self-pivot to reserve if queue exhausts. Ping DONE per item or grouped — your call on granularity, but at minimum one
   ping per major milestone.

[2026-05-15 13:30 UTC] slot-4 — 🏁 **CYCLE-CLOSE (Re-activate queue items 1-3)**. All 3 items complete. (1)
features-service per-family lifecycle coverage ✅ — 8 test files (3 tests each) confirmed passing; PM worktree rebased
to c7786b2f fixing PYTEST_UNIT_DIR; QG now runs 5006+ tests; features@2afd4337. (2) B-006 verification — risk +
execution ✅ — both lifecycle test files read and confirmed complete (STARTED/STOPPED/FAILED coverage matches B-006
spec); both QGs passed (exit 0). (3) ml-inference Phase 6.6 ✅ — TestPublishWithPolicyDecisionPassthrough (3 tests:
PARTIAL_OK/NAN_FILL/STRICT_FAIL passthrough via publish_with_policy mock); QG passed 68s; ml-inference@d4f524b. 🚨 BIG
FINDING: features-service QG now reveals 48 pre-existing volatility failures (3 root causes:
VolatilityOrchestrationService→VolatilityFeaturesOrchestrator API change, live_data_source module deleted, xdist
interference). Fixed 1 sports test (LookaheadBiasError update, features@7ef55a7f). Issue doc:
plans/active/issues/features_service_volatility_test_failures_2026_05_15.md. Volatility failures need slot with
volatility ownership — outside slot-4 scope. Continuing with queue items 4-8.

[2026-05-15 07:41 UTC] [main → slot 4] — 📋 **QUEUE EXTENSION** — add 3 more items after your 7-item batch. Total ~20
AI-days. 8. **features-service Phase 6 emission parity — sports + commodity families** — extend item 4 to the remaining
2 families. Each must call `publish_with_policy` at write boundary with STRICT*FAIL seed in UAC. Done-def: parity tests
for all 5 families + QG green. 9. **instruments-service contract migration pre/post-state tests** — Phase 3 migrations
(`scripts/migration*\*.py`) should assert (a) pre-state expected schema; (b) post-state matches new schema; (c) row
count preserved. Add tests for any migration missing these. Done-def: every migration has pre/post assertion test. 10.
**execution-service test_lifecycle_events.py expansion (if item 2 found gaps)** — add comprehensive
STARTED/STOPPED/FAILED + correlation_id propagation + duration_ms on COMPLETED tests. Done-def: coverage matches B-006 +
QG green.

[2026-05-15 14:45 UTC] slot-4 — 🏁 **CYCLE-CLOSE (Re-activate queue items 4-8)**. All items complete. (4)
features-service Phase 6 emission policy parity ✅ — done in prior reserve cycle (UAC service key fix +
TestUACPolicyParity, features@541cb9ee). (5) instruments-service Phase 3 migration tests ✅ — done in prior reserve
cycle (15→23 tests, instruments@e29ebf3). (6) Cross-repo skip markers diagnostic ✅ — grep across features-service,
instruments-service, execution-service: only execution-service test_twap_timing.py had @pytest.mark.skip; existing #
reason: comments above decorators already satisfy QG check. No violations requiring fix. (7) Phase 3 workspace QG
(rdt-p4-workspace-qg) ✅: instruments-service: ✅ PASSED (191s) market-tick-data-service: ✅ PASSED (169s, non-blocking
PENDING-RATCHET warnings only) execution-service: ✅ PASSED (372s) risk-and-exposure-service: ✅ PASSED (150s, required
setup.sh to install pytest-timeout) features-service: ❌ FAILING (201 pre-existing failures — not Phase 3 TradFi
related) No new Phase 3-specific failures detected. Fixed 1 additional failure: sports batch_handler row_key schema
drift (data_type="" now included); features@15acdad8. (8) Self-pivot: all 7-item queue + reserve items complete. Queue
extension items 8-10 received from main — starting now. 🚨 NOTE: features-service has ~198 remaining pre-existing
failures (beyond volatility's 48 and the 3 just fixed). Commodity CLI (2 failures): xdist interference (pass in
isolation). Other families: ~150 additional failures across all per-family test dirs. Full audit needed.

[2026-05-15 16:10 UTC] slot-4 — 🏁 **CYCLE-CLOSE (Queue extension items 8-10)**. All 3 items complete. (8)
features-service Phase 6 emission parity — sports + commodity ✅ BIG FINDING (fixed): sports UAC seeds were under
"features-service" instead of "features-sports-service" — 7 groups silently fell back to STRICT_FAIL. Fixed UAC
service_emission_policy.py (uac@49323dd). TestUACPolicyParity added to sports (3 tests) + commodity (3 tests); 6 tests
passing; features@880826bb. Commodity \_SERVICE_NAME="features-commodity-service" was already correct — only needed
parity tests. (9) instruments-service migration pre/post-state tests ✅ Added TestPrePostMigrationState (5 tests) to
test_migrate_tradfi_expiry_schema.py asserting: pre-state schema columns, post-state columns match, row count preserved,
no null expiration post-migration, DatetimeTZDtype dtype. instruments@4fb84fc. QG passed (132s). (10) execution-service
test_lifecycle_events.py expansion ✅ 3→7 tests: added modes=['batch','live'] verification, description kwarg check,
no-explicit-correlation_id assertion, FAILED path .run()-called-once. execution@ef01a59f. QG passed (592s). All repos QG
green. Standing by — 3-min poll active. [2026-05-15 09:09 UTC] [main → slot 4] — 🏁 **CYCLE-CLOSE acked — all 10 items
done.** Items 1-10 all shipped: features-service per-family CLI lifecycle ✅ + B-006 risk/execution verification ✅ +
ml-inference Phase 6.6 ✅ + features Phase 6 parity (delta_one/cross_instrument/onchain) ✅ + instruments migrations
✅ + cross-repo skip-grep ✅ + rdt-p4-workspace-qg ✅ + sports/commodity parity ✅ (BIG FIND: UAC@49323dd sports key fix
— well caught) + instruments pre/post-state tests ✅ + execution lifecycle expansion ✅.

📋 **NEW QUEUE — ~20 AI-days test coverage + lifecycle**:

1. **ml-training-service test coverage extensions** — coverage report → bring weak modules to ≥70%. Especially
   train_pipeline.py + experiment_manifest validation. Done-def: ≥70% coverage + QG green.
2. **system-integration-tests new DeFi-flow scenarios** — mocked end-to-end carry_staked_basis paper flow + APD paper
   flow. Uses Tenderly fixtures. Done-def: 2+ test scenarios + sit QG green.
3. **alerting-service additional alert code coverage** — verify every `AlertCode` in UAC has at least one integration
   test asserting it fires correctly. Done-def: alert-code-test parity confirmed + alerting QG green.
4. **batch-live-reconciliation-service test coverage extensions** — coverage gap fill. Focus on `reconcile_shard`
   (UTL@089deda exported it). Done-def: ≥70% coverage + QG green.
5. **features-service multi_timeframe + calendar family lifecycle tests** — same pattern as your item 1 (you did
   delta_one/volatility/sports/onchain/commodity). Multi_timeframe + calendar need same. Done-def: lifecycle tests + QG
   green.
6. **features-onchain Phase 6.6 emission tests** — features-onchain bucket. WARN_ONLY / NAN_FILL / STRICT_FAIL outcome
   coverage. Done-def: 3+ outcome tests + QG green.
7. **Workspace-wide pytest marker hygiene** — second pass: `@pytest.mark.xfail` + `@pytest.mark.skipif` audit across all
   repos; verify reasons documented. Done-def: 0 undocumented markers.
8. **instruments-service ETF/ADR migration coverage gap** — if any open migration scripts lack tests, add them following
   your item 9 pattern (pre/post-state + row-count + dtype assertions). Done-def: every active migration has pre/post
   test.
9. **execution-service order_router test gaps** — coverage gap fill on order_router.py module. Done-def: ≥85% coverage +
   QG green.
10. **Cross-repo @pytest.mark.live audit** — find tests that should be marked `live` (touch real services) but aren't;
    mark correctly so they're properly skipped in CI. Done-def: live-marker hygiene confirmed. Self-pivot. Ping DONE per
    item with SHA.

[2026-05-15 09:39 UTC] [main → slot 4] — ✅ **3 CYCLE-CLOSE pings acked**: items 1-3 (re-activate) ✅ @13:30 + items 4-8
(re-activate) ✅ @14:45 + items 8-10 (extension) ✅ @16:10. All 10 items of the prior queue shipped + UAC BIG
FIND@49323dd already noted. Fresh 10-item queue is in your file above (ml-training + sit DeFi flows + alerting +
reconciliation + multi_tf/calendar + features-onchain + marker hygiene + migration gaps + order_router + live-marker
audit). Self-pivot when you pick it up.

[2026-05-15 10:35 UTC] [main → slot 4] — 📋 **QUEUE EXTENSION +5** (after items 1-10 from fresh queue). Push to ~25
AI-days. 11. **ml-training-service experiment manifest validation tests** — verify experiment YAMLs validate cleanly +
reject malformed inputs (missing required fields, type errors, unknown hyperparameters). Done-def: 6+ validation tests +
ml-training QG green. 12. **system-integration-tests Phase 8 honest-coverage scenarios** — sit/ tests for
honest-coverage emission flow: VM emits → manifest writer → coverage.json → API endpoint. Done-def: 2+ scenarios + sit
QG green. 13. **alerting-service alert routing tests** — verify alert routing by severity (P0 → pager, P1 → email, P2 →
slack mock); add tests if missing. Done-def: routing test parity + alerting QG green. 14.
**batch-live-reconciliation-service reconcile_shard edge cases** — empty shard, single-row shard, schema-drift shard,
very large shard (memory). Done-def: 4+ edge-case tests + QG green. 15. **workspace-wide unused-import audit** — scan
all repos for unused imports surviving ruff sweep; file issue doc per repo with count + fix mechanical ones. Done-def:
cleanup report + 5+ fixes.

[2026-05-15 16:40 UTC] [slot 4 → main] — ✅ **ITEM 1 DONE**: ml-training-service coverage ≥80% + 15 pre-existing
failures fixed + 43 type errors resolved. ml-training-service@7e18af8. QG ALL GATES PASSED (284s). Added conftest.py
autouse event-logging fixture, test_defi_target_generator.py (27 tests), test_feature_data_adapter.py (28 tests),
extended test_data_filters.py (+15 tests). Fixed slow tests via tuning_method='default' + timeout markers + lgb.train
mock. Fixed 43 pyright ignores in 7 source files. Moving to item 2.

[2026-05-15 17:15 UTC] slot-4 — STARTED item 2: system-integration-tests new DeFi-flow scenarios (carry_staked_basis +
APD paper flows using Tenderly fixtures)

[2026-05-15 17:45 UTC] slot-4 — ✅ ITEM 2 DONE: system-integration-tests DeFi paper-flow scenarios. 16 new tests:
TestCarryStakedBasisPaperFlow (6), TestArbitragePriceDispersionPaperFlow (6), TestDefiPaperFlowCrossArchetypeInvariants
(3) + 1 invariant test — all 16 passed. Fixed 3 pre-existing QG lint failures (E741×4, C901×2). SIT QG ✅ (74s).
sit@fba72b7. Moving to item 3.

[2026-05-15 18:10 UTC] slot-4 — ✅ ITEM 3 DONE: alerting-service alert-code parity. New test file
tests/unit/test_alert_code_parity.py: 3-tier coverage — (1) parametrized sweep (77 tests): every AlertCode matches ≥1
LIVE_ALERT_RULES rule; (2) explicit-rule ratchet: exactly 2 codes (CHAOS_DRILL_FAILED + RECON_DEGRADED) are
catch-all-only; 75/77 have explicit rules; (3) family spot-checks: DeFi Family 1/2 (5 codes) + risk-rule (4 codes) +
stablecoin + QG_SNAPSHOT_STALE + RECON_DEGRADED_CLOSE. Alerting QG ✅ (122s). alerting@c1c9a68. Moving to item 4.

[2026-05-15 18:45 UTC] slot-4 — ✅ ITEM 4 DONE: batch-live-reconciliation-service reconcile_shard coverage. Expanded
test_stages.py with 20 new tests (4 classes): TestServiceReconResultProperties (5), TestReconcileShardPath (5 —
MATCH/SCHEMA_MISMATCH/VALUE_MISMATCH/exception/args), TestNdjsonCounting (3), TestBlobCountingEdgeCases (4).
Stage0_data_pipeline_recon.py coverage: 77.8% → 95.1%. Overall: 80.65% → 83.29% ≥ 70% target. QG ✅ (pre-existing
pip-audit + codex violations only). batch-live-reconciliation-service@50c1f6e. Moving to item 5.

[2026-05-15 19:00 UTC] slot-4 — ✅ ITEM 5 CONFIRMED DONE (pre-existing): features-service multi_timeframe + calendar
lifecycle tests already exist from prior session (B-006 Phase 8.A). tests/multi_timeframe/unit/test_lifecycle_events.py
(3 tests) + tests/calendar/unit/test_lifecycle_events.py (3 tests) — all 6 pass. PYTEST_UNIT_DIR="tests/" override
already in scripts/quality-gates.sh. Calendar family has 45 pre-existing failures in smoke_matrix/other files (NOT
lifecycle tests — not caused by slot-4). No new code needed. Moving to item 6.

[2026-05-15 19:30 UTC] slot-4 — ✅ ITEM 6 DONE: features-onchain Phase 6.6 emission policy tests. Added
TestCheckEmissionPolicyPhase66 (4 tests) to tests/onchain/unit/test_emission_policy.py: BLOCK_CRITICAL full window
publishes; BLOCK_CRITICAL with NaN suppresses write + should_alert=True (P0 alert path); NAN_FILL with NaN publishes
PUBLISHED_DEGRADED; empty DataFrame sends completeness=0.0. Fixed \_make_decision helper to accept should_alert kwarg
(EmissionDecision is frozen dataclass — cannot mutate post-init). All 12 onchain emission tests pass. Volatility
failures are pre-existing (confirmed baseline 47 failures before any slot-4 changes). features-service@a17d85b0. Moving
to item 7.

[2026-05-15 19:45 UTC] slot-4 — ✅ ITEM 7 DONE: workspace-wide pytest marker hygiene audit. Grepped xfail + skipif
across all worktree repos (37 files, 96 markers total). Result: 0 undocumented markers. Every @pytest.mark.xfail and
@pytest.mark.skipif has explicit reason= string (multi-line or inline). Repos checked: unified-api-contracts,
system-integration-tests, instruments-service, unified-trading-library, execution-service, strategy-service,
market-tick-data-service, deployment-api, features-service, batch-live-reconciliation-service. No code changes needed.
Moving to item 8.

---

## [2026-05-15 19:50 UTC] [main → slot 4] — 📋 ACTIVE QUEUE — please flip checkboxes as you ship

> Re-anchoring as todo-checkbox list per operator request. Items 1-7 already shipped — flipped here with SHAs from your
> ping entries above. Items 8-15 remain (~16 AI-days). Going forward, flip in-place as you ship: `- [ ]` →
> `- [x] @ <sha> + brief evidence`.

### Already done this cycle

- [x] **1. ml-training-service coverage ≥70%** — ml-training-service@7e18af8 (70 new tests + 43 pyright fixes)
- [x] **2. system-integration-tests new DeFi-flow scenarios** — sit@fba72b7 (16 tests)
- [x] **3. alerting-service alert code parity** — alerting@c1c9a68 (3-tier sweep)
- [x] **4. batch-live-reconciliation reconcile_shard coverage** — batch-live-reconciliation-service@50c1f6e (80.65 →
      83.29%)
- [x] **5. features-service multi_timeframe + calendar lifecycle tests** — pre-existing, confirmed (6 tests pass)
- [x] **6. features-onchain Phase 6.6 emission policy tests** — features-service@a17d85b0 (4 new tests)
- [x] **7. workspace-wide pytest marker hygiene audit** — AUDIT CLEAN (96 markers across 37 files, all documented)
- [x] **8. instruments-service ETF/ADR migration coverage gap** — instruments-service@f14f39a (38 tests:
      migrate_instrument_type_lowercase + migrate_defi_bare_to_asset_group; pre/post + mocked GCS; QG ✅)

### Remaining (in-progress = 9; pending = 10-15)

- [x] **9. execution-service order_router test gaps** — execution-service@bcb3771a (17 tests, 9 new: property getters,
      compose_validation paths, gas tracking, error codes; QG ✅ ALL GATES PASSED 437s)

- [x] **10. Cross-repo `@pytest.mark.live` audit** — instruments-service@06c7248 (3 markers applied:
      test_defi_instruments_e2e + test_tradfi_instruments_e2e + test_write_to_test_bucket_not_prod; also fixed
      pytest.ini missing live marker registration)

- [x] **11. ml-training-service experiment manifest validation tests** — ml-training-service@9a3f581
      (validate()/validate_or_raise() + 12 tests: TestExperimentManifestValidation ×10 + TestHyperparameterRoundtrip ×2;
      QG ✅ ALL GATES PASSED 329s)

- [ ] **12. system-integration-tests Phase 8 honest-coverage scenarios** — sit/ tests for honest-coverage emission flow
      (VM emits → manifest writer → coverage.json → API endpoint). Done-def: 2+ scenarios + sit QG green.

- [ ] **13. alerting-service alert routing tests** — routing by severity (P0 → pager, P1 → email, P2 → slack mock).
      Done-def: routing parity + alerting QG green.

- [ ] **14. batch-live-reconciliation reconcile_shard edge cases** — empty shard, single-row, schema-drift, very-large
      (memory). Done-def: 4+ edge-case tests + QG green.

- [ ] **15. workspace-wide unused-import audit** — scan repos for unused imports surviving ruff sweep. Issue doc per
      repo + fix mechanical ones. Done-def: cleanup report + 5+ fixes.

**Conflict rules**: features-service = slot 4 OWNS (you); deployment-api = slot 7; UAC = surgical only (Ikenna primary);
MTDS = slot 9; execution-service order_router separate from slot 5's Phase 9 surface.

Self-pivot through items 8 → 15. Ping STARTED + per-item DONE in this file.

[2026-05-15 20:15 UTC] slot-4 — ✅ ITEM 8 DONE: instruments-service migration coverage gap. Added 2 test files (38 tests
total) covering 2 previously-untested active migration scripts: (1) test_migrate_instrument_type_lowercase.py (19
tests): regex detection of uppercase GCS hive segments, path lowercasing transformation, pre/post path assertions,
mocked GCS copy+delete; (2) test_migrate_defi_bare_to_asset_group.py (19 tests): bare-path classification,
asset_group=defi/ insertion, pre/post segment count assertions, mocked GCS error+no-delete. QG ✅ ALL GATES PASSED
(96s). instruments-service@f14f39a. Moving to item 9.

[2026-05-15 20:50 UTC] slot-4 — ✅ ITEM 9 DONE: execution-service instruction_router test coverage gaps. Target was
"order_router.py" but that file doesn't exist — identified instruction_router.py at 80.5% as the correct target. Added 9
new tests (17 total): eth_balance_tracker/pnl_calculator property getters; compose_validation skipped for BET (unmapped
op); token_in colon-split instrument_type extraction; InstructionValidationError rejection path; sequential signal stops
on first failure; \_extract_error_code fallback + status_code attribute; \_track_gas_cost gas deduction. QG ✅ ALL GATES
PASSED (437s). execution-service@bcb3771a. Moving to item 10.

[2026-05-15 21:15 UTC] slot-4 — ✅ ITEM 10 DONE: cross-repo @pytest.mark.live audit. Scope: all slot-4 repos. Only
instruments-service has @pytest.mark.live registered (conftest.py gates behind IS_TEST_RUN=true). Finding: 3 e2e tests
(test_defi_instruments_e2e, test_tradfi_instruments_e2e, test_write_to_test_bucket_not_prod) make real GCS writes +
external API calls but were missing @pytest.mark.live. Additional finding: pytest.ini (overrides pyproject.toml) didn't
have live marker registered → PytestUnknownMarkWarning. Fixed both. Other repos (execution-service, MTDS,
strategy-service) use @pytest.mark.requires_credentials + @pytest.mark.skip for real-service tests — no live marker
there (not registered in those repos' pyproject.toml/pytest.ini). instruments-service@06c7248. QG ✅ (101s). Moving to
item 11.

[2026-05-15 22:30 UTC] slot-4 — ✅ ITEM 11 DONE: ml-training experiment manifest validation — ml-training@9a3f581
(validate()/validate_or_raise() + 12 tests; QG ✅ ALL GATES PASSED 329s).

[2026-05-15 22:45 UTC] slot-4 — 🚨 BIG FINDING (UTL QG): User requested UTL QG after OOM fix. Pulled LDR (5 new
commits). Result: 102 failures with PYTEST_WORKERS=2 (default), 29 genuine failures when isolating xdist. Root causes:
(1) 11 event ratchet failures — other slots added STRATEGY_LIFECYCLE_CHANGED/SEEDED +
DEPLOYMENT_ORPHANED/ROLLED_BACK/PROGRESS + DATA_INSTRUMENTS_STALE without updating count tests; (2) 5 config_interface
failures — auth matrix api count 9→8, DEX venue validation changed, testnet contract registry changed, cloud_config mock
bridge changed; (3) 13 cloud_interface failures — OIDC auth implementation changed, workspace YAML missing DeFi AWS
buckets, bucket constant tests stale; (4) 73 xdist false failures — event system singleton leak across subprocess
workers (pre-existing structural issue). The OOM fix (base-service.sh default=1 worker) is correct but UTL overrides to
2 workers. Issue doc: plans/active/issues/utl_qg_failures_2026_05_15.md. PM@415e2f03. Slot-4 does NOT own UTL —
escalating to main for assignment.

[2026-05-18 17:15 UTC] [main → slot 4] — 🟡 **UNCOMMITTED RUFF FORMAT** — deep audit of `.tabs/4/features-service` shows
**8 files dirty** (`.pre-commit-config.yaml` + `batch_handler.py` source + 6 test files). All confirmed pure ruff
reformats (UTC import sort, line-wrap, no logic changes). Operator left as-is per "let slot 4 stay idle". On re-engage:

1. `cd .tabs/4/features-service && git status` — verify the 8 files still dirty.
2. `git add -A && git commit -m "chore(format): apply ruff format trailing artifacts"`
3. Then resume sustain queue items per work_split § Slot 4. Also: batch-live-reconciliation-service worktree is 4
   commits behind LDR — rebase on re-engage.

---

## 2026-05-18 session — features-service Wave 70-73 rolling coverage continuation

[2026-05-18 UTC] slot-4 — 📋 **SESSION SUMMARY (2026-05-18): features-service onchain/ coverage waves 70-73**. Continued
rolling coverage waves on `features_service/onchain/` after picking up the 2026-05-18 work-split queue items 1-3 (sit
honest-coverage scenarios ✅ + alerting routing ✅ + batch-live reconcile_shard edge cases ✅ per item 14 in
work_split). After queue items completed, pivoted to reserve queue items 5/6 and then the MEGA RESERVE coverage waves.

### Waves completed this session

**Wave 70** — `features-service@a55c053b` — NEW FILE: `tests/onchain/unit/test_lst_seasonal_rewards_orchestrator.py` (11
tests, 0 pre-existing). Target: `lst_seasonal_rewards_collector.py`. Coverage: closed 6 previously-uncovered branches.

- `EmptyChainEventScanner.scan_distributor_transfers` (lines 118-119) — always returns []
- `LSTSeasonalRewardsCollector.__init__` (lines 152-153) — null filter + set conversion
- `collect_for_day` lst_filter branch (line 166 continue) — pufETH excluded when filter=['weETH']
- `collect_for_day` logger.info block (lines 173-184) — all LSTs processed when no filter
- `_collect_one_stream` scanner-None debug path (lines 196-204) — empty when no scanner registered
- `_collect_one_stream` except block (lines 212-221) — ConnectionError / TimeoutError / ValueError all → []
- Key pattern learned: inner test classes implementing Scanner Protocol MUST keep original param names (to match keyword
  arg calls from source) and use `del param` in body (for basedpyright unused-param compliance). Prefixing with `_`
  causes `TypeError: got unexpected keyword argument` at runtime.

**Wave 71** — `features-service@4d1a6647` — Two near-100% modules closed in single commit:

1. `test_lst_seasonal_rewards_orchestrator.py` extended: `test_collect_for_day_non_seasonal_streams_skipped()` — mixed
   CARRY_BASE + CARRY_ISSUER_SEASONAL registry; only SEASONAL scanned; CARRY_BASE hits line 170 `continue`. Closed
   `lst_seasonal_rewards_collector.py` to ~100%.
2. `test_parser.py` extended: `test_incremental_mode_normalised_to_live_by_validate_args()` in `TestValidateArgs` —
   covers `cli/parser.py` line 142 where `validate_args()` itself normalises `incremental→live` (previously only
   `normalize_args` was tested for this branch). Closed `parser.py` to ~100%.

**Wave 72** — `features-service@bc212b1c` — `test_batch_handler.py` extended: 15 new tests across 5 new classes.
Coverage: `batch_handler.py` 64.6% → ~85%.

- `TestHandleDependencyReport`: `_handle_dependency_report` dependency-not-in-batch skip path (line 58-80) + all-failed
  result (lines 94-108) + partial-fail (line 125)
- `TestCheckDependencies`: parallel async dependency check loops (lines 152-161)
- `TestProcessGroups`: parallel group dispatch + first-fail fallthrough (lines 179-195)
- `TestPreflightGuard`: `_run_write_gate`-style preflight true→exits-early (lines 334-342) + run ConnectionError→False
  (lines 373+377-379)
- `TestLogRunError`: `_log_run_error` FEATURE_WRITE_FAILED emit (lines 424-436) + None df branch (lines 452-454)
- Plus 4 standalone async tests: `_initialize_services` sets attributes; `_process_feature_group` raises when
  uninitialized; preflight returns True exits early; connection error returns False.
- Fixed pre-existing type annotation: `list` → `list[MagicMock]` for basedpyright compliance.

**Wave 73** — `features-service@c3ef28af` — `test_feature_writer_pure.py` extended: 11 new tests across 7 new classes.
Coverage: `feature_writer.py` 66% → ~84%.

- `TestAddTimestampOutTypeBranches`: Utf8 string timestamp cast branch (line 304) + Int64 microsecond epoch branch
  (line 307)
- `TestHandleWriteError`: `_handle_write_error` emits FEATURE_WRITE_REJECTED with reason="exception" (lines 238-247)
- `TestRunWriteGate`: alignment-fail → `_emit_write_rejected` + return None (lines 170-177)
- `TestApplyEmissionGate`: suppressed+should_alert=True → `log_event` called (lines 214-225) + suppressed+no_alert → no
  event (line 233)
- `TestValidateAlignment`: invalid alignment result → return False (lines 371-378)
- `TestWriteSeasonalRewards`: empty rows → False (lines 476-478) + non-empty rows → group+write → True (lines 479-486)
  using `LstSeasonalRewardRow` from UAC `unified_api_contracts.internal`
- `TestCheckExists`: blob_exists=True → True + blob_exists=False → False (lines 490-496)

### Work-split plan state

Item 14 in `plans/active/work_split_2026_05_18_harsh.md` is **fully up to date** — all Wave 70-73 evidence already
recorded with SHAs in the MEGA RESERVE item 14 checkbox. Item was flipped ✅ in the same agent turn as each wave.

Queue items 12-15 from the 2026-05-15 extended queue:

- [x] 12. system-integration-tests Phase 8 honest-coverage — done ✅ sit@47a1e04 (work_split item 1)
- [x] 13. alerting-service alert routing tests — done ✅ alerting@af7122f (work_split item 2)
- [x] 14. batch-live-reconciliation reconcile_shard edge cases — done ✅ batch-live-reconciliation@a214cd1 (work_split
      item 3)
- [x] 15. workspace-wide unused-import audit — SKIPPED (slot 2 claimed; supplemental issue doc filed)

**All 4 carry-over items from the 2026-05-15 extended queue are now complete.**

### Current status

🏁 **STANDING BY** — all work-split queue items complete (work_split items 1-17 all ✅). Coverage waves 70-73 shipped.
Waiting for main orchestrator to assign next tasks. No open blockers. No cross-side dependencies.

Features-service QG note: pre-existing ~198 failures remain (volatility 48 + calendar + other families — NOT caused by
slot-4). New tests all pass in isolation. Basedpyright clean on all new test files.

[2026-05-18 UTC] slot-4 — STARTED re-engage: ruff format commit confirmed (0fb99ad7); features-service fast-forwarded to
0e73bc90; batch-live-reconciliation fast-forwarded to 64dc955. Beginning coverage Wave 74+ on features-service (owned
surface).

[2026-05-18 UTC] slot-4 — ✅ ITEM DONE: Wave 74 — FlashLoanCalculator + AaveLendingCalculator coverage. 28 new tests in
test_flash_loan_and_aave_lending_calculators.py; both calculators 0%→~100%
(source_name/feature_names/init/calculate_features/fetch_data all paths). Removed 2 stale run_batch/run_live tests from
test_cli_and_tradfi.py (pre-existing failures — methods not in canonical ModeHandler since UTL lift 2026-05-08). QG ✅ 0
failures from 7472. features-service@3482b22b. Moving to Wave 75.

[2026-05-18 UTC] slot-4 — ✅ ITEM DONE: Wave 75 — scanner_factories.py coverage. 18 new tests in
test_scanner_factories.py; make_etherscan_scanner (chain routing + key venue + empty-key warning + timeout kwarg) +
make_web3_scanner (alchemy key + empty-key/RPC warnings + bound factory delegation) + make_solana_scanner (Helius URL +
custom venue + empty-key + max_signatures + rpc pass-through). All 18 passed. features-service@9661f8ab. Moving to
Wave 76.

[2026-05-18 UTC] slot-4 — ✅ ITEM DONE: Wave 76 — default_factories.py coverage. 25 new tests: \_NullSolanaRpc +
\_to_signature_dict_list + \_to_transaction_dict + \_to_meta_dict + default_solana_rpc_factory (empty URL/construction
failure/normal) + \_resolve_block_for_timestamp+default_block_range_resolver
(success/fallback/unknown-chain/api_key_supplier paths). All 25 passed. features-service@10251ea3. Moving to Wave 77.

[2026-05-18 UTC] slot-4 — ✅ ITEM DONE: Wave 77 — parquet_dust_loader.py coverage. 25 new tests:
lst_holding_wallet_from_params (identity/params/fallback) + lst_target_denom_from_params (native_asset/asset/ETH
default) + \_row_to_dust_token (normal/missing-amount/bad-amount/isoformat) + ParquetDustLoader.**call**
(no-wallet/exception/empty/filter-miss/match) + \_safe_list_blobs (error+success) + \_read_partition_frames
(skip-non-parquet/read-failure/polars-append). All 25 passed. features-service@10467b52. Moving to Wave 78.

[2026-05-18 UTC] slot-4 — ✅ ITEM DONE: Wave 78 — lst_rewards_bootstrap.py coverage. 19 new tests:
discover_chains_in_registry (5) + \_build_required_venues (8) + bootstrap_seasonal_rewards_collector (6: BootstrapResult
type, chains_wired, reloader.start(), no-chains warning, prefer_etherscan_for, solana→make_solana_scanner). All 19
passed. features-service@35fa1725. Moving to Wave 79.

---

[2026-05-19 12:15 UTC] main → slot 4 — 🔄 RULES REFRESH + NEW WORK ASSIGNMENT (2026-05-19)

**Action required (in order)**:
1. Pull LDR in ALL your repos: `cd ${WORKSPACE_ROOT}/.tabs/4/<repo> && git fetch origin --quiet && git rebase origin/live-defi-rollout`
2. Re-read `harsh_orchestrator/AGENT_ONBOARDING.md` (updated boot context)
3. Read `plans/active/work_split_2026_05_19_harsh.md § Slot 4` — this is your slot's work for today

**Key rule change now in force** (QG STEP 5.83 — landed PM@429b64b2b):
- `base-service.sh` now runs `check_uac_hard_required_fields.py` as STEP 5.83
- Validates UAC `validate_instrument_records()` still present + bundled shard-key kwargs correct
- Any service that runs `bash scripts/quality-gates.sh` will hit this gate on next run
- If your QG fails at STEP 5.83 on a file you don't own: log it, skip, continue

**Today's assignment — Slot 4**:
hard_schema_enforcement (4.8 cal) + strategy_archetype_taxonomy (4.8 cal) + deployment_and_qg close

Ack this ping by appending `[2026-05-19 12:15 UTC] slot 4 — STARTED <first item>` below.
