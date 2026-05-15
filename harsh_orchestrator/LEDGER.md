---
title: Main Agent Ledger — Harsh side
type: orchestration-ledger
status: active
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# Main Agent Ledger (Harsh side)

> Tracks today's slot assignments and live state. Universal mechanics and reading order →
> [`AGENT_ONBOARDING.md`](AGENT_ONBOARDING.md). Full task briefs → today's work-split. History → `git log`.

---

## Current shift: 2026-05-14 afternoon — Phase 0 QG clean-start (Harsh-side)

> 🚨 **FINAL WAVE — DAY WRAP-UP @12:41 UTC**: Each slot has been pinged with their FINAL assignment for today's session.
> No new dispatches will follow. Slots ship what they can in remaining time + stand down at DONE or BLOCKED. Phase 0 is
> fully green (all clusters); Phase 8.A surfaces in flight. May-23 critical path resumes tomorrow.

**Work-split**: [`plans/active/work_split_2026_05_14_harsh.md`](../plans/active/work_split_2026_05_14_harsh.md)
**Model**: Sonnet 4.6 / thinking: high (all slots). **Cycle context**: Day-3 of 4-day density push (2026-05-12 →
2026-05-15). Phase 0 = QG clean-start sweep needed before Phase 8 surface-coverage. **Operator direction**: All Wave 1-3
agents done. Reset all 8 slots. Spawn Phase 0 clusters simultaneously. Slot 3 = reserve (peripheral scripts
pipeline_mode sweep from old slot 9 Wave 2 Part A).

**Phase 0 cluster structure (Harsh side)**:

- **Cluster B** — slots 2/5/6/7 — C901+N802+B008 lint sweep (parallel, mechanical).
- **Cluster D** — slots 4/9 — test failures in MDPS + features-service + PBM after UTL@67c532bd. Ready NOW (UTL on LDR).
- **Cluster E** — slot 8 — UTS-UI tsc (+ batch_live Tab 3 carry-forward deferred).
- **Reserve** — slot 3 — peripheral scripts pipeline_mode kwarg sweep (10 scripts).

| Slot | Theme                                                                                                                                                   | State                                                                                                                                                                                                                                                                                                                                                                               | Plan-of-record                                                   | Branch      |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- | ----------- |
| 1    | Main orchestrator + Phase 0 monitoring + spawn cadence                                                                                                  | 🟢 ONLINE                                                                                                                                                                                                                                                                                                                                                                           | (this LEDGER)                                                    | `tab/hk/1`  |
| 2    | **Day-1 Deployment Infra & Lint Sweep** — VM_PREFIX watchdog audit + codex audit + alerting-service issue follow-up (per continuation_prompts § Slot 2) | ✅ CYCLE-CLOSE @08:25 — item 2 ✅ deployment-service@97298f3 (8 prefixes+6 tests); item 3 ✅ PM@0f52f0da (codex launcher-ssot+deploy-qg); item 4 ✅ alerting-service@6a01b98 (D.5+D.7 resolved); BUG FIX ✅ deployment-service@4b8d5b4 (honest-coverage launcher); re-smoke measure-honest-coverage-20260515-112048 RUNNING; item 1 🟡 BLOCKED-IAM (Cloud Scheduler pending Ikenna) | `plans/active/continuation_prompts_harsh_2026_05_15.md` § Slot 2 | `tab/hk/2`  |
| 3    | **Day-1 Strategy & DeFi APD Backtest** — B-016 Phase 2 launch + items 2-4                                                                               | 🔴 B-016 DEFERRED @08:00 (no valid 7-day CeFi tick window, best=3 days); item 2 ✅ strategy@a4dba55 (APD alias + 4 regression tests); 🟢 IN FLIGHT item 3: execution alpha smoke test extensions                                                                                                                                                                                     | `plans/active/continuation_prompts_harsh_2026_05_15.md` § Slot 3 | `tab/hk/3`  |
| 4    | **Day-1 Test Failures Absorption & Lifecycle Coverage** — CYCLE-CLOSE @07:30 (all 3 items done); now in reserve queue                                   | ✅ DONE all 3 main items @07:30 (no BACKLOG items remain); 🟢 IN FLIGHT reserve: features-service Phase 6 emission policy parity + instruments-service migration test extensions                                                                                                                                                                                                    | `plans/active/continuation_prompts_harsh_2026_05_15.md` § Slot 4 | `tab/hk/4`  |
| 5    | **Day-1 Risk + Execution Alpha + Kill-Switch** — UTL 3-tier kill-switch coverage + pnl-attribution verify + Phase 6.7 BLOCK_CRITICAL gate               | ✅ CYCLE-CLOSE @08:45 — item 1 ✅ UTL@4ffe980 (26 tests, QG 82.48%); item 2 ✅ pnl-attribution@fbf4269 (QG 44/44, 6 codex violations fixed); item 3 ✅ risk@fd10112 (15 tests, risk_snapshot_sink 89%→98%); 🟡 AWAITING reserve (continuation_prompts § Slot 5)                                                                                                                     | `plans/active/continuation_prompts_harsh_2026_05_15.md` § Slot 5 | `tab/hk/5`  |
| 6    | **Day-1 Custody, Signing, UTL Coverage, Codex Audits** — CYCLE-CLOSE @05:35 (all 3 items + prior work); now in extended reserve                         | ✅ DONE all 3 @05:35 (MISSED by poll — idle since); 🟢 IN FLIGHT extended reserve @08:00: UTL signing-helper test parity + codex/06 doc currency + execution-service custody integration smoke                                                                                                                                                                                      | `plans/active/continuation_prompts_harsh_2026_05_15.md` § Slot 6 | `tab/hk/6`  |
| 7    | **Day-1 Deployment API + UI + Phase 4 Infra** — B-018 Phase 4.A monitoring/alerting hooks + Phase 4.B downstream + SHARD_AXIS_MATRIX coverage           | 🟢 IN FLIGHT (STARTED @05:08)                                                                                                                                                                                                                                                                                                                                                       | `plans/active/continuation_prompts_harsh_2026_05_15.md` § Slot 7 | `tab/hk/7`  |
| 8    | **Day-1 UTL + B-014 rollout completion** — B-014 Phase 3 complete; all service repos updated                                                            | ✅ DONE B-014 Phase 3 rollout @~09:28 — workspace grep "unified-trading-codex"=0 hits; SHAs: ml-inference@8116b23 + mdps@2ff9258 + ml-training@00a97aa + alerting@4795ccf + mtds@acec41d + risk@55d7611; deferred work table updated in deployment_and_qg_strategy_implementation_2026_05_13.md; 🟡 AWAITING reserve (continuation_prompts § Slot 8)                                | `plans/active/continuation_prompts_harsh_2026_05_15.md` § Slot 8 | `tab/hk/8`  |
| 9    | **Day-1 MTDS + PBM + DeFi Carry (B-015 HOLD)** — all 4 handlers hardened; Day-4 CYCLE-CLOSE                                                             | ✅ ALL 4 handlers hardened: lst_rates@f657431 + evm_defi/gas_fee/solana_defi@3bca360; 🏁 CYCLE-CLOSE @09:15; 🛑 B-015 STILL HOLD — Ikenna phantom-fix not yet confirmed via \_agent_pings.md; reserve: PBM Phase 8 coverage                                                                                                                                                         | `plans/active/continuation_prompts_harsh_2026_05_15.md` § Slot 9 | `tab/hk/9`  |
| 10   | (✅ DONE 2026-05-13 — yesterday's dex_perp shipped; idle today)                                                                                         | ✅ DONE (idle)                                                                                                                                                                                                                                                                                                                                                                      | `dex_perp_and_venue_data_expansion_2026_05_12.md`                | `tab/hk/10` |

**Wave 1 closeout** (commits on LDR for the record):

- Slot 2 ✅ DONE (PM@3b317e65) — propagation chain Gate 1 fired
- Slot 3 ✅ DONE (PM@3a16656d) — GCP 3 buckets shipped, AWS deferred Phase 2.6
- Slot 4 ✅ DONE (PM@42755747) — Phase 8A-D rescued via cherry-pick (execution-service@38b3e8a5, foot-gun #5 intercept)
- Slots 5-9 ✅ DONE (PM@3d3d5c14) — batch closure; full per-slot detail in pings/slot_N.md
- Slot 10 ✅ DONE — all in-scope tasks shipped to LDR; 4 items DEFERRED with successor annotations in
  `dex_perp_and_venue_data_expansion_2026_05_12.md` scoreboard PM@6090e183

**Wave 2 reset status (2026-05-13 09:35-09:40 UTC, PM@7ca204a6)**:

- Slots 2, 3, 4, 6, 7, 9 — reset clean to origin/live-defi-rollout ✅
- Slot 5 — rebase failed (collision casualty cc62f02 in MTDS); deferred to manual cleanup
- Slot 8 — UAC rebase failed (collision casualty 949185c); deferred to manual cleanup
- Slot 10 — skipped per operator (still working at reset time); finished after reset

**Cleanup queue (DONE 2026-05-13 ~11:55 UTC)**:

- ✅ Slot 5 reset: local tab/hk/5 hard-reset to LDR; cc62f02 preserved on origin/tab/hk/5
- ✅ Slot 8 reset: local tab/hk/8 hard-reset to LDR; 949185c preserved on origin/tab/hk/8
- ✅ Slot 10 foot-gun #5 intercept: MDPS@0c92b91 (19-test fix) was NOT on LDR despite slot 10's "all work synced" claim.
  Main cherry-picked to LDR as MDPS@c30d8e0; slot 10 worktree reset clean.

All 10 slots are now in clean known state on LDR (or as ✅ DONE for slot 10).

---

## 🏁 End-of-shift summary — 2026-05-14 afternoon (operator stand-down @13:16 UTC)

**Cycle**: 2026-05-14 afternoon (~10:00 UTC → 13:16 UTC, ~3h 16m elapsed). **Commits landed on LDR**: 262 across 19
repos.

### Phase milestones closed today

- ✅ **Phase 0 fully green** across all clusters (B+D+E+F+A all closed). Closed @12:24 UTC (slot 4 ml-inference + slot 9
  MTDS final pieces); Cluster A+B taken proactively by slot 5 + slot 6.
- ✅ **Phase 1 env-locking** — B-001 (deployment-api tarball-block) + B-002 (deployment-ui env selector lock) shipped by
  slot 7.
- ✅ **Phase 2 deploy-ready tracking** — B-013 endpoint + UI tab shipped by slot 7.
- ✅ **Phase 4.A QG snapshot writer + cron VM** — B-018 shipped by slot 7 (36/36 repos snapshot live in
  `gs://central-element-323112-deployment-events/quality_gates_snapshot/`).
- ✅ **Phase 8.A surface coverage shipped**: B-006 (slot 4) + B-007/B-008 (slot 8) + B-009 (slot 5) + B-010 (slot 3) +
  B-012 (slot 6). 5 surfaces at coverage target.
- 🟢 **Phase 3 QG ratchet rollout (B-014)** — slot 8 STARTED unilaterally @~12:50 UTC; QG stub propagated to 4 service
  repos (execution + deployment-api + deployment-service + e2e-testing). Full rollout in progress at shift-end.
- ✅ **Wallet Treasury Phase 1 HMAC withdrawal approval chain** — shipped by slot 5 (deployment-api@4282d6a +
  UAC@0fa2b59 with 10 compliance tests + audit trail).
- ✅ **Phase 6 STEPs 5.79–5.82** — flipped per `PM@f09b37f4`.

### Open blockers at shift-end

1. **B-015 (slot 9) BLOCKED** — Phase 1 prereq check found: (a) DeFi features pipeline gap; (b) MTDS lst_rates stale.
   Documented at `PM@aff98449`. **Needs Ikenna or fresh main to scope-down or fix before paper backtest launch.**
2. **B-016 (slot 3) AWAITING Ikenna ACK** — cross-side prereq ping filed in `plans/active/_agent_pings.md` @~15:30 UTC.
   APD backtest config: start_date 2026-04-14, bankroll $250k USDT, 6-venue hedge list. **No code-side blocker; just
   needs Ikenna confirm.**

### In-flight at shift-end (will continue autonomously or carry to tomorrow)

- **Slot 2** — B-011 deployment-service@cf6bb83 SHIPPED ✅ (VM zombie watchdog tests + shellcheck fix; QG green 77s;
  plan flipped).
- **Slot 8** — B-014 ratchet rollout in flight; expect remaining service repos to flip green over next ~1-2h.
- **Slot 3 + slot 9** — paper backtest pre-launch state, gated on Ikenna ACK (slot 3) and pipeline-gap decision (slot
  9).
- **Slot 7** — B-018 shipped ✅; standby.
- **Slots 4, 5, 6** — assignments DONE ✅; standby.

### Major findings worth surfacing

- 🐛 **Slot 3 APD alias bug** (data-correctness, found during Phase 1 prereq): `arbitrage_price_dispersion` lowercase
  alias was missing from `STRATEGY_TYPE_TO_SLOT` — would have caused `sys.exit(1)` on paper launch. Fixed:
  strategy-service@0ca3fac + e2e-testing@d55e7eb. System worked as designed (Phase 1 check catches launch-time bugs).
- 🐛 **Slot 6 fixture drift bug** (pre-existing): CanonicalOptionsChainEntry fixture expiration drift discovered during
  B-012 work. Fixed under Findings Triage in execution-service@fe8b1d3e.
- 📉 **Slot 9 BLOCKED finding** (data correctness, NEW): DeFi features pipeline incomplete + MTDS lst_rates stale. NOT a
  paper-launch bug; a real pipeline gap. **Requires operator decision before resuming B-015.**

### Tomorrow's main-orchestrator pickup

1. Triage slot 9 BLOCKED finding (DeFi features + MTDS lst_rates).
2. Watch for Ikenna ACK on slot 3 B-016 cross-side ping; if green, slot 3 launches paper VM and runs autonomous 30-day
   monitor.
3. Verify B-014 rollout (slot 8) completed cleanly across all consumer service repos; if any QG failures, fix.
4. Verify B-011 (slot 2) work is complete; check plan checkbox status.
5. Run `regenerate_active_plan_inventory.py` to refresh master plan dashboard.
6. **NEW (Lever 1+2 adoption)** — Review draft orchestration upgrade docs before slot dispatch:
   - [`THEMATIC_CLUSTERS.md`](THEMATIC_CLUSTERS.md) (stable per-slot theme map; review for accuracy)
   - [`../plans/active/continuation_prompts_harsh_2026_05_15.md`](../plans/active/continuation_prompts_harsh_2026_05_15.md)
     (Day-1 instance with per-slot multi-item queues)
   - [`../scripts/agents/harsh_auto_poll.sh`](../scripts/agents/harsh_auto_poll.sh) (mechanical poller; run `--dry-run`
     once, then cron-schedule or tmux `--watch`)
7. Drop ONE "Day-1 START" ping per slot pointing to their continuation_prompts section — stand back, let slots
   self-pivot.
8. Begin morning slot reset (only if themes shift; per Lever 3, themes are stable across cycles).

---

## Phase 0 QG clean-start task briefs — 2026-05-14 afternoon (all slots fresh)

> All 8 slots (2-9) reset via `setup-tab-worktrees.sh --reset-slot N`. Worktrees on `tab/hk/N` matching
> `origin/live-defi-rollout`. UTL@67c532bd confirmed on LDR — Cluster D unblocked. Cluster A+C closed by Ikenna. Cluster
> F on Ikenna slot 1.

### Slot 6 — Phase 0 Cluster D+E: instruments-service failures + deployment-ui vitest (Sonnet 4.6 / thinking: medium)

> ✅ **Previous task DONE**: alerting-service N802 lint sweep (alerting-service@74761a5 + @75f0404; 451 tests pass; 4
> D.5+D.7 codex violations filed as issue doc).

- **Owned repos**: `instruments-service` + `deployment-ui`
- **Task — 2 items, work in order**:

  **Item 1 — Cluster D: instruments-service 74 test failures (diagnose-first)**
  - `instruments-service`: 74 failed (`test_new_orchestrator`, `test_sports_fixtures_daily_repoll`). This is the biggest
    unknown in Phase 0. Diagnose-first rule applies.
  - Run `bash scripts/quality-gates.sh` and capture the full failure output. Read failing test bodies + code-under-test.
    Determine: (a) test drifted from new UTL@67c532bd API → fix test; (b) code drifted → fix code; (c) unrelated
    pre-existing failure → file issue doc + noqa if scope-limited.
  - Fix what you can diagnose clearly. If root cause ambiguous after 30 min, file
    `plans/active/issues/instruments_service_test_failures_<YYYY_MM_DD>.md` and proceed.
  - Commit + push per fix. Flip plan checkbox with SHA evidence.

  **Item 2 — Cluster E: deployment-ui 21 vitest failures**
  - `deployment-ui`: 21 vitest failures across 6 files (start with `TreasuryTab.tsx` failures per plan).
  - Run `cd deployment-ui && pnpm test --run 2>&1 | head -100` to see failure summary. Diagnose-first: read failing
    test + component. Likely MSW mock drift or prop type change from Phase 1 env-locking guard additions. Fix tests.
    `pnpm build` must also pass.
  - Commit + push. Flip plan Cluster E checkbox.

- **Done-def**: instruments-service QG green OR issue doc filed for ambiguous failures; deployment-ui 21 vitest green +
  `pnpm build` passes. Ping DONE with SHAs.

### Slot 2 — Phase 0 remaining: Cluster B alerting-service + Cluster D MDPS/features/ml-inference + Cluster F deployment-service (Sonnet 4.6 / thinking: medium)

> ✅ **Previous task DONE**: ml-training-service C901 clean (ml-training-service@5b60d5f + PM@eac0774d). Wave 2
> verification also done.

- **Owned repos**: `alerting-service` + `market-tick-data-service` + `features-service` + `ml-inference-service` +
  `deployment-service`
- **Task — 4 items, work in order (slots 4 + 6 are silent — you absorb their remaining Phase 0 work)**:

  **Item 1 — Cluster B: alerting-service N802 (slot 6's work)**
  - `alerting-service/tests/unit/notifiers/test_router_*.py`: 4 N802 violations — SHOUTY_CASE test names. Add
    `# noqa: N802` to each (they're event-code documentation, not snake_case fixable). Run
    `bash scripts/quality-gates.sh`. Commit + push.

  **Item 2 — Cluster D: MDPS 2 test failures (slot 4's work)**
  - `market-tick-data-service`: 2 failures in `test_canonical_writer_record_helpers`. Near-pass. Diagnose-first: read
    test + code-under-test. Likely UTL@67c532bd signature drift (new `pipeline_mode` kwarg). Fix code or test per SSOT.
    `bash scripts/quality-gates.sh` green. Commit + push.

  **Item 3 — Cluster D: features-service 1 import error (slot 4's work)**
  - `features-service`: 1 import error in `test_volatility_expected_unattempted`. Diagnose-first: re-run
    `bash scripts/quality-gates.sh`. Likely resolved by UTL@67c532bd already on LDR. If import still fails: check UTL
    venv (`uv pip install -e .` in features-service). Commit + push if any fix needed.

  **Item 4 — Cluster D: ml-inference-service (slot 4's work)**
  - `ml-inference-service`: 6f + 33e in `test_prediction_publisher_helpers` +
    `test_emission_policy_per_strategy_signal`. Re-run `bash scripts/quality-gates.sh` after UTL propagation. If
    failures remain: diagnose-first, fix code or test per SSOT. Commit + push.

  **Item 5 — Cluster F: deployment-service timeout re-run**
  - `deployment-service`: prior QG run timed out >5min. Re-run `bash scripts/quality-gates.sh` with extended budget
    (15min). If passes: flip Cluster F checkbox in plan + commit. If fails: diagnose and fix.

- **Done-def**: All 5 items QG green + plan checkboxes flipped per item. Ping DONE with per-repo SHAs.

### Slot 4 — Phase 0 ml-inference absorption + B-006 follow-on (Sonnet 4.6 / thinking: medium)

> ✅ **Previous task DONE**: Phase 0 Cluster D — features-service@38b43ea6 QG green; strategy-service@3ff75a2 2 failures
> fixed.

- **Owned repos**: `ml-inference-service` + then `execution-service` + `risk-and-exposure-service` +
  `features-service` + `market-tick-data-service` + `instruments-service` (for B-006) + `unified-trading-pm`
- **Task — 2 items, work in sequence**:

  **Item 1 (immediate) — Phase 0 Cluster D absorption: ml-inference-service 6f+33e**
  - Absorbed from slot 2 (slot 2 redirected; do NOT wait for slot 2 to do it).
  - `ml-inference-service`: 6 failures + 33 errors in `test_prediction_publisher_helpers` +
    `test_emission_policy_per_strategy_signal`. Diagnose-first: run
    `bash scripts/quality-gates.sh 2>&1 | grep -E "FAILED|ERROR"` from `ml-inference-service/`. Read failing test +
    code-under-test. Likely UTL@67c532bd import path drift. Fix import paths to canonical UTL surface OR fix logic if
    code drifted. QG green. Commit + push. Flip plan Cluster D ml-inference checkbox.

  **Item 2 (after Phase 0 green) — B-006: Phase 8.A service startup coverage**
  - Wait until Phase 0 all clusters report QG green (slots 6, 9, 2 will ping DONE when done). Then start B-006.
  - Target: 100% coverage on STARTED/STOPPED/FAILED bootstrap paths across 5 services (execution, risk, features, MDPS,
    instruments).
  - Sub-agent fan-out per service (within this slot, serialise commits). For each: run `bash scripts/quality-gates.sh`;
    identify uncovered lines in `ServiceBootstrap` call path; add unit tests hitting STARTED/STOPPED/FAILED lifecycle
    events.
  - QG green per service. Commit + push per service. Flip plan Phase 8.A "service startup" checkbox.

- **Done-def for Item 1**: ml-inference-service QG green, plan checkbox flipped.
- **Done-def for Item 2**: 0 uncovered lines in startup/shutdown paths for all 5 services; QG green; plan checkbox
  flipped.
- **NOTE**: Do NOT start Item 2 until Phase 0 is all clear. Ping main if you complete Item 1 and Phase 0 is still red
  (pick up B-011 instead if deployment-service Cluster F is done but Phase 0 still has open items).

### Slot 5 — Phase 0 Cluster F absorption + B-009 follow-on (Sonnet 4.6 / thinking: medium)

> ✅ **Previous task DONE**: B-005 (Writegate Phase 6.9 — features-service@0de7fee6 already wired by prior commits;
> confirmed) + B-017 (defi_recursive_borrow successor plan filed by slot 9; confirmed). Both done by prior agents.

- **Owned repos**: `deployment-service` + then `risk-and-exposure-service` + `execution-service` (for B-009) +
  `unified-trading-pm`
- **Task — 2 items, work in sequence**:

  **Item 1 (immediate) — Phase 0 Cluster F absorption: deployment-service QG timeout re-run**
  - Absorbed from slot 2 (slot 2 redirected).
  - `deployment-service`: prior QG run timed out >5min (VM script tests). Re-run `bash scripts/quality-gates.sh` with
    extended budget (15min). If passes: flip Cluster F checkbox in
    `deployment_and_qg_strategy_implementation_2026_05_13.md` + commit + push.
  - If still fails: read the failure. Diagnose-first: is it a real test failure OR just a timeout from slow VM launch
    simulation? If fixable: fix. If ambiguous: file issue doc with full QG output excerpt. QG as clean as you can get
    it.

  **Item 2 (after Phase 0 green) — B-009: Phase 8.A kill switch + circuit breaker coverage**
  - Wait until Phase 0 all clusters green. Then start B-009.
  - Target: 100% coverage on `KILL_SWITCH_ACTIVATED` + `CIRCUIT_BREAKER_OPEN` event paths in
    `risk-and-exposure-service` + `execution-service`.
  - Tests: (a) kill switch fires → no further orders emitted; (b) circuit breaker trips on N consecutive failures →
    `CIRCUIT_BREAKER_OPEN` event emitted; (c) deactivation re-arms. Verify: no order emitted after kill switch without
    explicit deactivation.
  - QG green per service. Commit + push per service. Flip plan Phase 8.A "kill switch" checkbox.

- **Done-def for Item 1**: deployment-service QG result recorded (green + checkbox flipped OR issue doc filed).
- **Done-def for Item 2**: 100% coverage on kill switch + circuit breaker paths; plan checkbox flipped.
- **NOTE**: Do NOT start Item 2 until Phase 0 is all clear.

### Slot 3 — B-010: Phase 8.A archetype validation coverage (Sonnet 4.6 / thinking: medium)

> ✅ **Previous task DONE**: Phase 0 Reserve peripheral scripts pipeline_mode sweep (features-service@9e3339d1; all 10
> scripts confirmed upstream; MTDS 53-failure P1 issue doc filed).

- **Owned repos**: `strategy-service` + `unified-trading-pm`
- **Task**: 90% coverage on per-archetype calc validation paths in `strategy-service`.
  - Target archetypes: `carry_staked_basis` + `arbitrage_price_dispersion` validation branches.
  - Sub-agent fan-out per archetype is allowed WITHIN this slot (same worktree, serialise commits).
  - Step 1: `bash scripts/quality-gates.sh 2>&1 | grep "coverage"` from `strategy-service/` — confirm current coverage
    baseline for validation paths.
  - Step 2: Locate validation logic per archetype:
    `grep -rn "validate\|_validate\|ValidationError" strategy_service/archetypes/ --include="*.py"`.
  - Step 3: Add unit tests hitting each validation branch: good input passes, bad input raises specific error, edge
    cases (None, out-of-range) handled.
  - Step 4: Re-run QG — coverage ≥ 90% on validation paths.
  - Step 5: Commit + push per archetype group. Flip plan Phase 8.A "archetype calcs" checkbox with SHA evidence.
- **Done-def**: strategy-service QG green; ≥90% coverage on `carry_staked_basis` + `arbitrage_price_dispersion`
  validation branches; plan checkbox flipped with SHAs.
- **Note**: B-004 prerequisite is fully met (UTL@67c532bd propagation resolved all 4 strategy-service failures; 1544
  tests pass). Do NOT re-fix B-004.

### Slot 7 — B-013: Phase 2 deploy-ready tracking endpoint + UI panel (Sonnet 4.6 / thinking: medium)

> ✅ **Previous tasks DONE**: B-001 (deployment-api@0574e9e tarball-block) + B-002 (deployment-api@f0c0c43 +
> deployment-ui@2c8de22 env selector lock; 18 vitest pass). ⚠️ **STOP B-004**: strategy-service failures already
> resolved (UTL@67c532bd propagation; 1544 tests pass; no code change needed). B-004 is DONE. Do NOT work on it.

- **Owned repos**: `deployment-api` + `deployment-ui` + `unified-trading-pm`
- **Task**:
  1. **deployment-api** — new endpoint `GET /api/repos/deploy-ready`: walks last 5 daily QG snapshots per repo; returns
     `{"repo": ..., "deploy_ready": true/false, "reason": "..."}` per repo. Rules: `deploy_ready: true` iff all 5
     snapshots green AND zero open P0 issue docs AND no `🟡 IN-FLIGHT REFACTOR` banner in the repo's active plan. Add
     endpoint to router + unit tests (mock snapshot store; test green-5 case + failing-snapshot case + P0-issue-doc
     case). `bash scripts/quality-gates.sh` green.
  2. **deployment-ui** — new panel showing per-repo readiness table from above endpoint. Minimal:
     `repo | deploy_ready | reason` columns, auto-refreshes every 60s. Integrate with existing deployment-ui component
     structure. `pnpm build` + vitest green.
  3. Flip plan Phase 2 checkbox with SHA evidence. Commit + push per repo.
- **Done-def**: `/api/repos/deploy-ready` endpoint live in deployment-api with unit tests; deployment-ui panel renders
  readiness table + `pnpm build` passes; plan checkbox flipped.
- **No big decisions**: if QG snapshot store location is ambiguous, grep deployment-api for existing snapshot read
  patterns (`grep -rn "snapshot\|qg_result\|quality_gate" deployment_api/`).

### Slot 6 — B-012: Phase 8.A custody + wallet signing coverage (Sonnet 4.6 / thinking: medium)

> ✅ **Previous task DONE**: Phase 0 Cluster D+E — instruments-service 74 failures already resolved (UTL
> legacy_reason_classifier patch unified-trading-library@d78dd02) + deployment-ui 21 vitest failures → 0
> (deployment-ui@b6e4e22; pnpm build green).

- **Owned repos**: `execution-service` + `unified-trading-library` + `unified-trading-pm`
- **Task**: 100% coverage on `WalletProvisioningConfig` load + `signing_surface` dispatch in `execution-service`.
  - Step 1: `bash scripts/quality-gates.sh 2>&1 | grep "coverage"` from `execution-service/` — baseline coverage on
    wallet + signing paths.
  - Step 2: Locate `WalletProvisioningConfig` and `signing_surface` in `execution-service/` —
    `grep -rn "WalletProvisioningConfig\|signing_surface\|CLOUD_KMS_ENCRYPTED" execution_service/ --include="*.py"`.
  - Step 3: Add unit tests (mock at KMS client level — NO real keys):
    - (a) `CLOUD_KMS_ENCRYPTED` path: `signing_surface` dispatches to KMS mock → signs correctly → no exception.
    - (b) Wrong/missing `signing_surface` config → raises loud error at boot (not at trade time). Assert exception
      raised on `WalletProvisioningConfig.load()`.
    - (c) Config validation: required fields missing → `ValueError` at config-parse time.
  - Step 4: If UTL `signing_surface` helpers are undertested, add parallel tests in `unified-trading-library/` using
    same mock pattern.
  - Step 5: `bash scripts/quality-gates.sh` green in both repos. Commit + push per repo. Flip plan Phase 8.A "custody +
    wallet" checkbox.
- **Done-def**: 100% coverage on `WalletProvisioningConfig` load + `signing_surface` dispatch; QG green in both repos;
  plan checkbox flipped with SHA evidence.
- **Note**: **Start immediately** — execution-service + UTL are Phase-0-clean (no Phase 0 blocker on these repos). No
  need to wait for other Phase 0 clusters.
- **Mock rule**: mock at the KMS client level. Never hit real KMS endpoints. Use `unittest.mock.patch` on the KMS
  client's `sign` method.

### Slot 2 — B-011: Phase 8.A VM deploy scripts coverage (Sonnet 4.6 / thinking: medium)

> ✅ **Previous task DONE**: Phase 0 remaining (alerting-service already done by slot 6; features-service QG green
> @38b43ea6; ml-inference absorbed by slot 4; deployment-service Cluster F absorbed by slot 5). Stand by: verify
> features-service QG green, then start B-011.

- **Owned repos**: `deployment-service` + `unified-trading-pm`
- **Task**: 95% coverage on `deployment-service/scripts/vm/launch-*.sh` paths + Python helpers.
  - **Start condition**: wait for Phase 0 all clusters green (slots 5, 6, 9 will DONE-ping; slot 4 also). Do NOT start
    B-011 work until Phase 0 is fully clear.
  - Step 1: `shellcheck deployment-service/scripts/vm/launch-*.sh` — fix any warnings/errors. These are bash scripts;
    shellcheck is the linter.
  - Step 2: For each launcher: identify the Python-level singleton-lock check
    (`grep -rn "singleton_lock\|is_vm_running\|VM_PREFIX_TO_BUCKET" deployment_service/` — find the dict + check
    function). Add unit tests:
    - (a) Singleton-lock fires: same-prefix VM already RUNNING → launcher refuses (exits non-zero or raises).
    - (b) No collision: VM not running → launcher proceeds.
  - Step 3: Zombie-watchdog dict registration: `VM_PREFIX_TO_BUCKET` in `vm_zombie_watchdog.py` — test that all VM
    prefixes from `launch-*.sh` scripts appear as keys in this dict.
  - Step 4: Tarball URI construction: test that the tarball path resolves to the correct bucket name via
    `resolve_bucket_name()` (NOT an inline f-string).
  - Step 5: `bash scripts/quality-gates.sh` green. Commit + push. Flip plan Phase 8.A "VM deploy scripts" checkbox.
- **Done-def**: shellcheck clean; unit tests covering singleton-lock + zombie-watchdog registration + tarball-URI; QG
  green; plan checkbox flipped.
- **Key rule**: VM naming — first segment must be a prefix in `VM_PREFIX_TO_BUCKET`. If any new VM prefixes are
  discovered that are NOT registered → file issue doc immediately (silent zombie-watchdog blindspot = silent money
  burn).

### Slot 3 — B-016: DeFi arbitrage_price_dispersion paper backtest run (Sonnet 4.6 / thinking: medium)

> ✅ **Previous task DONE**: B-010 (Phase 8.A archetype validation coverage — strategy-service@4ede3b2 — 38 new tests;
> archetype coverage 88.37% → 93.18%; basis_dated 59%→100%, staked_basis 82%→99%; QG green; plan checkbox flipped
> @PM@4f4df625).

- **Owned repos**: `strategy-service` + `execution-service` + `e2e-testing` + `unified-trading-pm`
- **Task — 3-phase, MIRRORS B-015 pattern for the second archetype**: (1) cross-side prereq check; (2) launch paper
  backtest; (3) 30-day monitor + verify.
- **PARALLEL with slot 9 B-015**: same pipeline, different archetype. Coordinate launch timing with slot 9 — if slot 9's
  Phase 1 prereq check files a cross-side ping first, you can ride on Ikenna's response for shared prereqs (start_date,
  hedge venue list); only need separate confirm on bankroll-per-archetype.

  **Phase 1 — Cross-side prereq check (FIRST, before any launch)**:
  - Read `plans/active/defi_master_2026_05_07.md` § "paper-trade gate" for context on what "DeFi pipeline green
    end-to-end" means for `arbitrage_price_dispersion`.
  - Verify pipeline state on-disk: (a) `instruments-service` DeFi instrument refdata exists for the dispersion-eligible
    pairs (USDC-margin perps across Binance/Bybit/OKX/Deribit/Kraken/Hyperliquid/Aster); (b) MTDS DeFi market-data
    parquets exist for last 30 days; (c) `features-service` price-dispersion feature parquets exist; (d)
    `strategy-service` `arbitrage_price_dispersion` archetype factory resolves cleanly (B-010 verified at 99% coverage
    on dispersion validation branches); (e) `execution-service` paper-mode adapter responds across ALL 6+ perp venues
    (not just LST-margin subset).
  - Check `plans/active/_agent_pings.md` for slot 9's B-015 cross-side ping FIRST: if slot 9 has already filed
    `harsh-slot-9 → ikenna-main` with start_date + hedge venue confirm, ride on it. Append a sibling ping:
    `[YYYY-MM-DD HH:MM UTC] harsh-slot-3 → ikenna-main — B-016 pipeline-readiness check: list of (a)-(e) verified green. Riding on slot 9's start_date + hedge venue confirm; need ONLY arbitrage_price_dispersion bankroll cap separately. BLOCKING B-016 launch until confirm.`
    Otherwise file the full prereq ping (start_date + bankroll + hedge venue list + archetype-specific dispersion
    threshold config).
  - Wait for Ikenna ACK before Phase 2.

  **Phase 2 — Launch paper backtest** (after Ikenna ACK):
  - Launch via `e2e-testing` colocated_engine in paper mode with start_date + bankroll per Ikenna's confirm. Command
    shape (verify exact CLI per `e2e-testing/scripts/defi/` README):
    `python scripts/defi/colocated_engine.py --archetype arbitrage_price_dispersion --mode paper --start-date <YYYY-MM-DD> --duration 30d --asset-group defi`.
  - Tag the run with `correlation_id` for event-stream tracking. Capture VM name + PID for reference. Cross-link with
    slot 9's B-015 run correlation_id in your STARTED ping.

  **Phase 3 — 30-day monitor + verify**:
  - Watch event stream at `gs://central-element-323112-events/events/strategy-service/.../*.jsonl` — confirm STARTED +
    per-day progress events.
  - Verify per-day: (a) P&L attribution row written; (b) hedge leg fills observed at applicable CeFi perp venues; (c)
    USDC margin positions tracked across 6+ venues; (d) dispersion thresholds firing as expected per archetype calc; (e)
    no kill-switch / circuit-breaker events.
  - At day-30 STOPPED event: pull P&L summary + commit attribution report to
    `e2e-testing/reports/defi_paper_runs/arbitrage_price_dispersion_<YYYY-MM-DD>.md`. Ping DONE with full SHA list +
    report path.

- **Done-def**: Phase 1 cross-side ping landed + Ikenna ACK; Phase 2 launch verified via event stream STARTED; Phase 3
  30-day STOPPED event + P&L attribution report committed.
- **NOTE — cross-side gate**: do NOT skip Phase 1. Same rule as B-015 — invalid backtest config = wasted compute. Wait
  for ACK.
- **NOTE — parallel with slot 9**: if slot 9 hits a Phase 1 blocker (missing instrument refdata, broken adapter), expect
  a similar blocker on your side. Coordinate via cross-side ping ledger, not parallel duplicate diagnosis.
- **Escalation**: if Phase 1 reveals dispersion-specific pipeline gap (e.g., missing per-venue dispersion feature,
  broken multi-venue execution adapter), file P1 issue doc + ping main.

### Slot 7 — B-018: Phase 4.A daily QG snapshot writer + cron VM (Sonnet 4.6 / thinking: medium)

> ✅ **Previous task DONE**: B-013 Phase 2 deploy-ready tracking (deployment-api@1f22e22 GET /api/repos/deploy-ready +
> 19 unit tests; deployment-ui@2dfefa1 DeploymentReadinessTab + 6 vitest tests; PM plan Phase 4.B checkboxes flipped @
> PM@b6e58906).

- **Owned repos**: `unified-trading-pm` (snapshot.sh script) + `deployment-service` (cron VM launcher) +
  `unified-trading-pm` (plan checkbox)
- **Task — 4 items, work in order**:

  **Item 1 — Author `snapshot.sh` writer (Phase 4 line 1)**:
  - Create `unified-trading-pm/scripts/quality_gates/snapshot.sh`. Walks all repos in `workspace-manifest.json`. For
    each repo: `cd <repo> && bash scripts/quality-gates.sh --quick 2>&1 | tee /tmp/qg-<repo>.log; EXIT=$?`. Capture:
    `repo`, `pull_sha` (current `git rev-parse HEAD`), `qg_status` (green if EXIT=0 else red), `failing_step` (extract
    from log if red), `first_error_line` (extract from log if red), `duration_seconds`, `snapshot_at` (UTC ISO).
  - Output: Python helper `unified-trading-pm/scripts/quality_gates/snapshot_to_parquet.py` — collects per-repo dicts →
    writes `quality_gates_snapshot_YYYY_MM_DD.parquet` to `gs://${PROJECT_ID}-deployment-events/quality_gates_snapshot/`
    via UCI `get_storage_client()`.
  - Parallelize: run 8 repos in parallel batches (`xargs -P 8`). Total runtime target ≤ 5 min for full workspace.

  **Item 2 — Cron VM launcher (Phase 4 line 1 cron requirement)**:
  - Author `deployment-service/scripts/vm/launch-qg-snapshot-vm.sh` — boots e2-small VM in `asia-northeast1`, pulls
    latest `unified-trading-library:latest`, runs `bash unified-trading-pm/scripts/quality_gates/snapshot.sh`, then
    auto-shutdown.
  - Singleton-locked (refuse launch if same-prefix VM running). Register `qg-snapshot` prefix in
    `deployment-service/scripts/vm/vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET` dict.
  - Cloud Scheduler trigger: daily at 06:00 UTC. Schedule via `gcloud scheduler jobs create`.

  **Item 3 — Smoke test then full run**:
  - Smoke-test snapshot on 3 repos first (`unified-trading-pm`, `deployment-api`, `unified-trading-library`). Verify
    parquet lands in GCS + readable via deployment-api's `/api/repos/deploy-ready` endpoint (Phase 4.B read-side from
    B-013).
  - Then full workspace run. Verify all 60+ repos covered.

  **Item 4 — Plan checkbox flip + commit/push**:
  - Flip `- [ ]` → `- [x]` for Phase 4 line 1 in `deployment_and_qg_strategy_implementation_2026_05_13.md`.
  - Commit + push per repo. Ping DONE with SHAs.

- **Done-def**: snapshot.sh + cron VM launcher shipped; smoke test passes on 3 repos; full workspace run succeeds;
  `/api/repos/deploy-ready` endpoint reads snapshot data; plan checkbox flipped.
- **Note — coordinates with B-013**: B-013's read endpoint already exists. Verify B-018's snapshot data shape matches
  B-013's expected parquet schema (re-read `deployment_api/services/deploy_ready.py` to confirm column names + types).

### Slot 9 — B-015: DeFi carry_staked_basis paper backtest run (Sonnet 4.6 / thinking: medium)

> ✅ **Previous task DONE**: Phase 0 Cluster D (PBM@8837338) + Day-3 Part A peripheral pipeline_mode
> (features-service@268919ad + mtds@bc77f94) + Day-3 Part B QG step 6 (PM@5c1cfc7f) + B-004 verification + MTDS
> remaining failures (per operator @12:04).

- **Owned repos**: `strategy-service` + `execution-service` + `e2e-testing` + `unified-trading-pm`
- **Task — 3-phase**: (1) cross-side prereq check; (2) launch paper backtest; (3) 30-day monitor + verify.

  **Phase 1 — Cross-side prereq check (FIRST, before any launch)**:
  - Read `plans/active/defi_master_2026_05_07.md` § "paper-trade gate" for context on what "DeFi pipeline green
    end-to-end" means.
  - Verify pipeline state on-disk: (a) `instruments-service` DeFi instrument refdata exists in GCS at
    `gs://central-element-323112-instruments-defi/...`; (b) MTDS DeFi market-data parquets exist for last 30 days; (c)
    `features-service` DeFi feature parquets exist; (d) `strategy-service` `carry_staked_basis` archetype factory
    resolves cleanly (`bash scripts/quality-gates.sh` on strategy-service passes for archetype paths); (e)
    `execution-service` paper-mode adapter for DeFi venues responds.
  - File cross-side ping at `plans/active/_agent_pings.md`:
    `[YYYY-MM-DD HH:MM UTC] harsh-slot-9 → ikenna-main — B-015 pipeline-readiness check: list of (a)-(e) verified green. Need Ikenna confirmation of: backtest start_date, paper-mode bankroll cap, hedge venue list for short leg. BLOCKING B-015 launch until confirm.`
    Wait for Ikenna ACK before Phase 2.

  **Phase 2 — Launch paper backtest** (after Ikenna ACK):
  - Launch via `e2e-testing` colocated_engine in paper mode with start_date + bankroll per Ikenna's confirm. Command
    shape (verify exact CLI per `e2e-testing/scripts/defi/` README):
    `python scripts/defi/colocated_engine.py --archetype carry_staked_basis --mode paper --start-date <YYYY-MM-DD> --duration 30d --asset-group defi`.
  - Tag the run with `correlation_id` for event-stream tracking. Capture VM name + PID for reference.

  **Phase 3 — 30-day monitor + verify**:
  - Watch event stream at `gs://central-element-323112-events/events/strategy-service/.../*.jsonl` — confirm STARTED +
    per-day progress events.
  - Verify per-day: (a) P&L attribution row written; (b) hedge leg fills observed at CeFi perp venues
    (Bybit/Deribit/OKX); (c) LST margin positions tracked; (d) no kill-switch / circuit-breaker events.
  - At day-30 STOPPED event: pull P&L summary + commit attribution report to
    `e2e-testing/reports/defi_paper_runs/carry_staked_basis_<YYYY-MM-DD>.md`. Ping DONE with full SHA list + report
    path.

- **Done-def**: Phase 1 cross-side ping landed + Ikenna ACK; Phase 2 launch verified via event stream STARTED; Phase 3
  30-day STOPPED event + P&L attribution report committed.
- **NOTE — cross-side gate**: do NOT skip Phase 1. Launching paper backtest without Ikenna's confirm on
  start-date/bankroll/hedge-list risks invalid backtest config + wasted compute. Wait for ACK.
- **Escalation**: if Phase 1 reveals pipeline gap (e.g., missing instrument refdata, broken adapter), file P1 issue
  doc + ping main; do NOT silently work around it.

### Slot 8 — B-014: Phase 3 QG ratchet STEPs enable + rollout (Sonnet 4.6 / thinking: medium)

> ✅ **Previous task DONE**: B-007 (UTL manifest writer coverage — 100%) + B-008 (UTL emission publisher coverage —
> 100%; unified-trading-library QG green; plan checkboxes flipped).

- **Owned repos**: `deployment-service` (base-service.sh template) + all service repos that consume it +
  `unified-trading-pm`
- **Task**: Enable new QG STEP X.N1 (tarball-env-block) + X.N2 (coverage-targets-enforcement) + X.N3 in
  `base-service.sh` template, then roll out to all service repos.
  - **START CONDITION (CRITICAL)**: Do NOT start rollout until ALL of B-006 + B-009 + B-010 + B-011 + B-012 are DONE
    (all DONE pings from slots 4, 5, 3, 2, 6). Use the wait time to prep: read the plan, read `base-service.sh`,
    identify exactly which STEP lines to enable.
  - **Prep (do now while waiting)**:
    - Read `plans/active/deployment_and_qg_strategy_implementation_2026_05_13.md` § Phase 3 for exact STEP identifiers.
    - Read `deployment-service/scripts/base-service.sh` — find the STEP X.N1/X.N2/X.N3 lines (grep:
      `grep -n "STEP\|X\.N" deployment-service/scripts/base-service.sh`).
    - Identify which lines are disabled (commented-out or gated) vs enabled.
    - Draft the exact edits needed (line numbers + replacement text). Do NOT apply yet.
  - **Rollout (after all B-006-B-012 DONE)**:
    1. Apply STEP enables in `base-service.sh` template in PM SSOT
       (`unified-trading-pm/scripts/workflow-templates/base-service.sh` or wherever the template lives).
    2. Run: `bash unified-trading-pm/scripts/propagation/rollout-quality-gates-unified.py` — propagates updated template
       to all service repos.
    3. Run `bash scripts/quality-gates.sh` in each service repo — verify all pass with new STEPs (if any fail, fix the
       underlying coverage/env-block issue in that repo before moving on).
    4. Commit + push per repo. Flip plan Phase 3 checkbox.
  - **Never**: skip a service repo that fails; fix the root cause, then rollout continues.
- **Done-def**: All service repos pass QG with new STEP X.N1+X.N2+X.N3 enabled; template propagated; plan checkbox
  flipped.
- **Ping pattern**: When all B-006-B-012 DONE pings land (watch LEDGER), ping main
  `slot-8 — READY TO ROLLOUT, B-006/B-009/B-010/B-011/B-012 all confirmed DONE` — then proceed without waiting for main
  acknowledgment.

### Slot 5 — B-005 + B-017: Writegate Phase 6.9 + defi_recursive_borrow successor plan (Sonnet 4.6 / thinking: medium)

> ✅ **Previous task DONE**: deployment-api C901 sweep (deployment-api@3040a1b + PM@910eb257). 13 pre-existing test
> failures (SHARD_AXIS_MATRIX UAC alignment) — NOT yours, filed as issue, skip.

- **Owned repos**: `features-service` + `unified-api-contracts` (if seed missing) + `unified-trading-pm`
- **Task — 2 items, work in order**:

  **Item 1 — B-005: Writegate Phase 6.9 features-sports emission policy**
  - Read `plans/active/writegate_honest_coverage_endtoend_2026_05_06.md` § Phase 6.9 for context. Wire
    `publish_with_policy` at the sports live-handler write boundary in `features-service` — same pattern as Phase 6.5
    batch_handler (committed at features-service@a93dc3b4). Open `features_service/sports/cli/handlers/live_handler.py`
    — find the write boundary — add `_check_emission_policy()` call.
  - If UAC STRICT_FAIL policy seed for the sports live data_type is missing from `SERVICE_OUTPUT_POLICIES`: add it (same
    structure as nearby entries). `bash scripts/quality-gates.sh` green in both repos.
  - Commit + push per repo. Flip plan Phase 6.9 checkbox with SHA evidence.

  **Item 2 — B-017: defi_recursive_borrow DESCOPE successor plan**
  - Read `plans/active/defi_recursive_borrow_archetypes_2026_05_10.md` — understand shipped vs unshipped phases (UAC
    half ~7% done; Solidity + execution + strategy + codex + UI halves unshipped per Ikenna audit PM@e1e67656).
  - Annotate plan body with descope block: "May-23 scope = archetype documented only; Phase 2-3 Solidity + execution
    deferred to successor."
  - File `plans/active/defi_recursive_borrow_archetypes_post_cutover_2026_06_01.md` with `migrated_from:` frontmatter +
    all unshipped todos migrated with `**MIGRATED FROM:**` provenance.
  - Add successor banner to current plan. Run `python3 scripts/plans/regenerate_active_plan_inventory.py`. Commit + push
    (PM).

- **Done-def**: Phase 6.9 `publish_with_policy` wired + QG green; recursive_borrow successor plan filed + inventory
  regenerated.

### Slot 8 — B-007 + B-008: Phase 8.A UTL coverage — manifest writer + emission publisher (Sonnet 4.6 / thinking: medium)

> ✅ **Previous task DONE**: batch_live Tab 3 L2 fix-batch + STEP 5.77 + L7 sweep (PM@06c6213c).

- **Owned repos**: `unified-trading-library` + `unified-trading-pm`
- **Task — 2 items, work sequentially in same repo**:

  **Item 1 — B-007: manifest writer coverage**
  - Target: 100% coverage on `ManifestWriter.record_*` call paths in UTL.
  - Run `bash scripts/quality-gates.sh` from `unified-trading-library/` first — confirm current coverage baseline.
  - Add tests under `unified-trading-library/tests/` covering: `record_captured` happy-path with `available_at` stamp;
    `record_empty` with 3+ distinct `EmptyConfirmedReason` entries; `record_failed` with `attempted_at` set;
    `record_expected_unattempted`; `assert_available_at_present` fires on every `record_captured` call.
  - Re-run QG — coverage must be >= prior baseline + new lines covered.
  - Commit + push. Flip plan checkbox.

  **Item 2 — B-008: emission publisher coverage**
  - Target: 100% coverage on `publish_with_policy` + `_publish_emission_check` + `_resolve_policy_output_data_type` in
    UTL.
  - Add tests: STRICT_FAIL policy blocks when output data_type mismatches policy; WARN_ONLY policy logs warning but
    passes through; NAN_FILL fills NaN columns per policy config; unknown policy → raises loud at config-load time.
  - Re-run QG — all tests green + coverage target met.
  - Commit + push. Flip plan checkbox.

- **Done-def**: Both UTL coverage targets met; `bash scripts/quality-gates.sh` green; plan checkboxes flipped with SHA
  evidence.
- **Note**: Both items are UTL-only. Use repo-local `.venv` (NOT `.venv-workspace`) per venv split rule.

### Slot 2 — Phase 0 Cluster B: ml-training-service C901 lint sweep (Sonnet 4.6 / thinking: high)

- **Owned repos**: `ml-training-service` + `unified-trading-pm`
- **Plan-of-record**:
  [`plans/active/deployment_and_qg_strategy_implementation_2026_05_13.md`](../plans/active/deployment_and_qg_strategy_implementation_2026_05_13.md)
  § "Phase 0 Cluster B"
- **Task**: 6 C901 violations in `ml-training-service/ml_training_service/cloud_feature_provider.py`. Mixed extract +
  noqa:
  1. `bash scripts/quality-gates.sh 2>&1 | grep "C901\|N802\|B008"` from `ml-training-service/` root — confirm exact
     violations + line numbers.
  2. For each: read the function body first (grep-then-read rule). Assess: multiple-concern function → `extract-method`;
     legitimate pipeline-stage orchestrator → `# noqa: C901 — <rationale>`.
  3. Fix all 6. Run `bash scripts/quality-gates.sh` again — must be clean (0 C901/N802/B008 in ml-training-service).
  4. Commit + push: `fix(ml-training-service): Phase 0 C901 lint sweep — extract + noqa`.
  5. Flip `- [ ]` checkbox for ml-training-service in the plan. Commit + push (PM).
- **Done-def**: QG clean for ml-training-service on C901; plan checkbox flipped with commit SHA evidence.
- **C901 policy**: mixed-noqa (per-callsite). UAC carveout does NOT apply to service code. Per-noqa comment required.
  SSOT: `codex/05-infrastructure/deployment-and-qg-strategy.md` § "QG complexity (C901) policy".

### Slot 3 — Phase 0 Reserve: peripheral scripts pipeline_mode kwarg sweep (Sonnet 4.6 / thinking: high)

- **Owned repos**: `market-tick-data-service` + `features-service` + `unified-trading-library` + `instruments-service` +
  `unified-trading-pm`
- **Plan-of-record**:
  [`plans/active/writegate_honest_coverage_endtoend_2026_05_06.md`](../plans/active/writegate_honest_coverage_endtoend_2026_05_06.md)
  Phase 4 (manifest writer API, peripheral scripts follow-up)
- **Task**: 10 peripheral scripts still call `record_captured/record_empty/record_failed/record_expected_unattempted`
  without `pipeline_mode` kwarg — will fail at runtime. Sweep:
  1. `market-tick-data-service/scripts/mtds_reconcile_partial_bundles.py`
  2. `market-tick-data-service/scripts/build_continuous_es.py`
  3. `market-tick-data-service/market_tick_data_service/scripts/rebuild_prediction_manifest.py`
  4. `features-service/scripts/sports/features_sports_reconcile_available_at.py`
  5. `features-service/scripts/sports/backfill_fixture_features_manifest.py`
  6. `features-service/scripts/sports/compute_sfi_progressive_only.py`
  7. `unified-trading-library/unified_trading_library/manifest_completeness.py`
  8. `unified-trading-library/unified_trading_library/options_cluster_lookup.py`
  9. `instruments-service/scripts/backfill_drift_funding_2026_05_13.py`
  10. `unified-trading-library/unified_trading_library/manifest_freshness.py` For each: **read the callsite** →
      determine correct `pipeline_mode` from context (batch/reconcile scripts → `PipelineMode.BATCH`) → add
      `pipeline_mode=PipelineMode.BATCH` kwarg → commit + push per repo (one commit per repo, not per file).
- **Done-def**: All 10 scripts have `pipeline_mode` kwarg; `bash scripts/quality-gates.sh` green in each touched repo;
  plan checkbox flipped.
- **GREP-THEN-READ**: read 1 callsite per script before adding kwarg — confirm the import path for `PipelineMode` in
  each file's context.

### Slot 4 — Phase 0 Cluster D: MDPS + features-service test failures (Sonnet 4.6 / thinking: high)

- **Owned repos**: `market-tick-data-service` + `features-service` + `unified-trading-pm`
- **Plan-of-record**:
  [`plans/active/deployment_and_qg_strategy_implementation_2026_05_13.md`](../plans/active/deployment_and_qg_strategy_implementation_2026_05_13.md)
  § "Phase 0 Cluster D"
- **Context**: UTL@67c532bd exported `EmissionDecision` + `publish_with_policy` + related symbols. Downstream repos that
  imported these from private paths will now see import resolution changes → test failures.
- **Task**:
  1. `bash scripts/quality-gates.sh 2>&1 | grep -E "FAILED|ERROR|ImportError|ModuleNotFoundError"` from
     `market-tick-data-service/` root — reproduce + count failures.
  2. Same from `features-service/` root.
  3. For each failure: diagnose-first. Read import path in failing test/module vs new UTL export surface. Fix import to
     use the canonical UTL export path (`from unified_trading_library import ...`).
  4. Re-run QG for each repo — must be green.
  5. Commit + push per repo. Flip plan checkboxes.
- **Done-def**: MDPS `bash scripts/quality-gates.sh` green; features-service `bash scripts/quality-gates.sh` green; plan
  checkboxes flipped with SHA evidence.
- **Diagnose-first**: if a failure is NOT an import error but a logic failure → read both sides of the contract. Fix
  code if code drifted; fix test if test drifted from new SSOT. File issue doc if ambiguous.

### Slot 5 — Phase 0 Cluster B: deployment-api C901 lint sweep (Sonnet 4.6 / thinking: high)

- **Owned repos**: `deployment-api` + `unified-trading-pm`
- **Plan-of-record**:
  [`plans/active/deployment_and_qg_strategy_implementation_2026_05_13.md`](../plans/active/deployment_and_qg_strategy_implementation_2026_05_13.md)
  § "Phase 0 Cluster B"
- **Task**: 9 C901 violations in `deployment-api/` — specifically `_build_leaf_parquet_candidates` (21>10) and
  `_sports_honest_coverage` (22>10) in `services/data_status_drilldown.py` + `data_status_service.py`. Extract-method
  3-4 of them; noqa the rest:
  1. `bash scripts/quality-gates.sh 2>&1 | grep "C901"` from `deployment-api/` root — confirm violations + exact
     functions.
  2. For each: read body. Functions doing 3+ distinct concerns → extract private helpers. Functions that are legitimate
     linear-query pipelines → `# noqa: C901 — <rationale>`.
  3. Fix all. `bash scripts/quality-gates.sh` clean.
  4. Commit + push. Flip plan checkbox.
- **Done-def**: QG clean for deployment-api on C901; plan checkbox flipped.

### Slot 6 — Phase 0 Cluster B: alerting-service N802 lint sweep (Sonnet 4.6 / thinking: high)

- **Owned repos**: `alerting-service` + `unified-trading-pm`
- **Plan-of-record**:
  [`plans/active/deployment_and_qg_strategy_implementation_2026_05_13.md`](../plans/active/deployment_and_qg_strategy_implementation_2026_05_13.md)
  § "Phase 0 Cluster B"
- **Task**: 4 N802 SHOUTY*CASE test names in `alerting-service/tests/unit/notifiers/test_router*\*.py`. N802 = function
  names that are lowercase-only in Python convention; test names that use UPPER_CASE trigger it:
  1. `bash scripts/quality-gates.sh 2>&1 | grep "N802"` from `alerting-service/` root — confirm exact 4 functions.
  2. Assess each: if function names encode event codes intentionally (e.g.,
     `test_ALERT_THRESHOLD_BREACHED_routes_correctly`) → `# noqa: N802 — event code in name; intentional`. If purely
     stylistic and rename is safe → rename to `test_alert_threshold_breached_routes_correctly`.
  3. Fix all 4. `bash scripts/quality-gates.sh` clean.
  4. Commit + push. Flip plan checkbox.
- **Done-def**: QG clean for alerting-service on N802; plan checkbox flipped.

### Slot 7 — B-001 + B-002 + B-004: Phase 1 env-locking + strategy test fixes (Sonnet 4.6 / thinking: medium)

> ✅ **Previous task DONE**: client-reporting-api B008 sweep (client-reporting-api@e936eb4 + PM@130dcd5e). 358 tests
> pass. P2 coverage gap issue filed.

- **Owned repos**: `deployment-api` + `deployment-ui` + `strategy-service` + `unified-trading-pm`
- **Task — 3 items, work in order**:

  **Item 1 — B-001: deployment-api env-locking (tarball-block)**
  - Add env-aware validation in `deployment-api`: reject tarball deploy method when `DEPLOYMENT_ENV` is `staging` or
    `prod` → HTTP 400 with clear error message referencing the codex SSOT.
  - Add `--override-tarball-block` emergency flag (logs audit entry, allows through).
  - Unit tests: dev allows both tarball + image; staging/prod reject tarball without override; override succeeds + audit
    row written.
  - `bash scripts/quality-gates.sh` green. Commit + push (`deployment-api`). Flip plan checkbox in
    `deployment_and_qg_strategy_implementation_2026_05_13.md` Phase 1. Commit + push (`unified-trading-pm`).

  **Item 2 — B-002: deployment-ui env selector lock**
  - In deployment-ui: grey out / disable the tarball deploy option in the deploy modal when env selector shows `staging`
    or `prod`. Show tooltip: `"Tarball deploy blocked in staging/prod — use image deploy"`.
  - Read existing env selector component first (`grep -rn "tarball\|DEPLOYMENT_ENV\|envSelector" deployment-ui/src/`).
  - `pnpm build` + vitest green. Commit + push (`deployment-ui`).

  **Item 3 — B-004: strategy-service 2 remaining test failures**
  - Slot 4 Wave 2 fixed 15/17 test failures. 2 remain — diagnose-first. Run `bash scripts/quality-gates.sh` from
    `strategy-service/`. Read both sides (test + code) for each failure. Fix code if drifted; fix test if drifted from
    SSOT; file issue doc if ambiguous.
  - Commit + push (`strategy-service`).

- **Done-def**: All 3 items shipped: deployment-api QG green + tarball-block active; deployment-ui build green + UI
  locks in staging/prod; strategy-service 2 failures resolved or issue docs filed.
- **No big decisions needed** — if tarball-block implementation is ambiguous (e.g., unclear how DEPLOYMENT_ENV is read
  in deployment-api), grep for existing env-check patterns in the codebase first.

### Slot 7 — Phase 0 Cluster B: client-reporting-api B008 lint sweep (Sonnet 4.6 / thinking: high)

- **Owned repos**: `client-reporting-api` + `unified-trading-pm`
- **Plan-of-record**:
  [`plans/active/deployment_and_qg_strategy_implementation_2026_05_13.md`](../plans/active/deployment_and_qg_strategy_implementation_2026_05_13.md)
  § "Phase 0 Cluster B"
- **Task**: B008 = `Query()` / mutable-default used as function argument default in
  `client-reporting-api/client_reporting_api/attribution.py:237+`. FastAPI pattern; requires default-factory refactor:
  1. `bash scripts/quality-gates.sh 2>&1 | grep "B008"` from `client-reporting-api/` root — confirm exact callsites.
  2. Read line 237+ of `attribution.py`. B008 fires when `Depends(...)` or `Query(...)` are default arg values. FastAPI
     canonical fix: move to `Annotated[T, Depends(...)]` signature or use `= fastapi.Depends(...)` with explicit
     `Optional` typing.
  3. Also check `cluster A` residual: `rg "×" client_reporting_api/ --type py` — if any `×` symbols from RUF002 →
     replace with `x`. (Cluster A sed sweep, Ikenna-owned, but this is 1 file — absorb it if found.)
  4. `bash scripts/quality-gates.sh` clean.
  5. Commit + push. Flip plan checkbox.
- **Done-def**: QG clean for client-reporting-api on B008 (and residual RUF002 if any); plan checkbox flipped.

### Slot 8 — Phase 0 Cluster E: UTS-UI tsc errors (Sonnet 4.6 / thinking: high)

- **Owned repos**: `unified-trading-system-ui` + `unified-trading-pm`
- **Plan-of-record**:
  [`plans/active/deployment_and_qg_strategy_implementation_2026_05_13.md`](../plans/active/deployment_and_qg_strategy_implementation_2026_05_13.md)
  § "Phase 0 Cluster E"
- **Task**: UTS-UI has tsc type errors blocking QG:
  1. `cd unified-trading-system-ui && npx tsc --noEmit 2>&1 | head -60` — reproduce + count errors.
  2. Fix each: read the failing line, understand the type contract. Common patterns: missing type annotation, `any`
     types introduced by Ikenna-side slot work, React prop types mismatches.
  3. Run `npx tsc --noEmit` again — must be clean (0 errors).
  4. Run `pnpm build` — must succeed.
  5. Commit + push. Flip plan checkbox.
  - **Time-boxed**: if tsc errors are >15 files or require design decisions → file issue doc per file with proposed fix;
    flip partial done.
  - **batch_live Tab 3 carry-forward**: L2 fix-batch (21 violations across features-\*/strategy/MDPS) is the deferred
    Tab 3 work from slot 8 Wave 3. Only pick this up if UTS-UI tsc finishes in <2h. If time remains, read
    `batch_live_symmetry_2026_05_10.md` § Tab 3 for the L2 fix list.
- **Done-def**: `npx tsc --noEmit` exits 0; `pnpm build` exits 0; plan checkbox flipped.

### Slot 9 — Phase 0 Cluster D: position-balance-monitor-service test failures (Sonnet 4.6 / thinking: high)

- **Owned repos**: `position-balance-monitor-service` + `unified-trading-pm`
- **Plan-of-record**:
  [`plans/active/deployment_and_qg_strategy_implementation_2026_05_13.md`](../plans/active/deployment_and_qg_strategy_implementation_2026_05_13.md)
  § "Phase 0 Cluster D"
- **Context**: UTL@67c532bd changes to `EmissionDecision` / `publish_with_policy` export paths may cascade into PBM test
  failures.
- **Task**:
  1. `bash scripts/quality-gates.sh 2>&1 | grep -E "FAILED|ERROR|ImportError"` from `position-balance-monitor-service/`
     — reproduce + count.
  2. Diagnose-first for each failure (import path change vs logic drift vs pre-existing).
  3. Fix import paths to use canonical UTL export surface. Fix logic if code drifted from SSOT.
  4. Re-run QG — green.
  5. Commit + push. Flip plan checkbox.
- **Done-def**: PBM `bash scripts/quality-gates.sh` green; plan checkbox flipped with SHA.

---

## Day-3 Wave 2 continuation — 2026-05-14 (slots 2/6/7 post-second-task)

### Slot 2 — P1 bug fixes: pool_state_result ImportError + deployment-api missing dep (Sonnet 4.6 / thinking: high)

- **Owned repos**: `execution-service` + `deployment-api` + `unified-trading-pm`
- **Issue docs**:
  - [`plans/active/issues/pool_state_result_import_error_2026_05_13.md`](../plans/active/issues/pool_state_result_import_error_2026_05_13.md)
    (P1 — blocks all execution-service test collection)
  - [`plans/active/issues/deployment_api_missing_position_balance_dep_2026_05_14.md`](../plans/active/issues/deployment_api_missing_position_balance_dep_2026_05_14.md)
    (P1 — Docker/CI broken)
- **Task**:
  1. **Fix PoolStateResult import** (execution-service): `execution_service/defi_execution/protocols/__init__.py:78`
     imports `PoolStateResult` which was renamed. Run `git -C execution-service log --all --oneline -20 | head -20` +
     `grep -r "PoolStateResult\|class.*PoolState" execution_service/` to find the new symbol name. Fix the import. Run
     `bash scripts/quality-gates.sh` — test collection must unblock. FF-push.
  2. **Fix deployment-api missing dep**: Add `position-balance-monitor-service` to `deployment-api/pyproject.toml`
     `[project.dependencies]` + `workspace-manifest.json` `deps` list for deployment-api. Run
     `bash unified-trading-pm/scripts/repo-management/run-version-alignment.sh` to align versions. FF-push per repo.
     Mark both issue docs as RESOLVED with SHAs.
- **Done-def**: execution-service `bash scripts/quality-gates.sh` step 3 (test collection) passes (no ImportError);
  deployment-api Docker build would succeed (verify with `cd deployment-api && bash scripts/quality-gates.sh`); both
  issue docs flipped to RESOLVED.
- **No big decisions needed** — diagnose-first rule applies (read function body before patching; if PoolStateResult was
  deleted vs renamed, that's different fixes).

### Slot 6 — instruments-service bug fixes: enrichment preflight + zero-fixture bypass (Sonnet 4.6 / thinking: high)

- **Owned repos**: `instruments-service` + `unified-trading-pm`
- **Issue docs**:
  - [`plans/active/issues/api_football_enrichment_preflight_runtime_mismatch_2026_05_13.md`](../plans/active/issues/api_football_enrichment_preflight_runtime_mismatch_2026_05_13.md)
    (P1)
  - [`plans/active/issues/orchestrator_zero_fixture_path_recovery_bypass_bug_2026_05_14.md`](../plans/active/issues/orchestrator_zero_fixture_path_recovery_bypass_bug_2026_05_14.md)
    (P2)
- **Task**:
  1. **Enrichment preflight fix**: Read the issue doc carefully. Locate the enrichment entry point in
     `instruments-service/` (grep `enrichment_mode\|preflight\|instruments.parquet`). The issue: enrichment mode entered
     without verifying the instruments parquet exists first. Fix: add existence check before entering enrichment path;
     if missing → either auto-build mapping from fixtures OR raise clear `DependencyError`. Use `Findings Triage` rule:
     read BOTH sides of the contract before picking fix direction. FF-push.
  2. **Zero-fixture bypass bug**: Read the issue doc. Locate `recovery_fixture_ids` usage in the orchestrator. The bug:
     zero-fixture fast path fires even when `recovery_fixture_ids` are provided. Fix: guard the fast path with
     `if not recovery_fixture_ids:`. FF-push.
  3. Mark both issue docs as RESOLVED with SHAs in body. FF-push (PM).
- **Done-def**: Both issue docs marked RESOLVED; `bash scripts/quality-gates.sh` green in instruments-service;
  enrichment mode doesn't crash on missing instruments.parquet.
- **No big decisions needed** — diagnose-first rule applies. Both fixes are single-repo surgical.

### Slot 7 — UAC ice_us_softs fix + honest-coverage 404 graceful UI (Sonnet 4.6 / thinking: high)

- **Owned repos**: `unified-api-contracts` + `deployment-ui` + `unified-trading-pm`
- **Issue docs**:
  - [`plans/active/issues/ice_us_softs_dataset_disambiguation_2026_05_14.md`](../plans/active/issues/ice_us_softs_dataset_disambiguation_2026_05_14.md)
    (P2 — UAC TRADFI_ROOTS missing 6 ICE US softs)
  - [`plans/active/issues/honest_coverage_cron_vm_scheduling_2026_05_14.md`](../plans/active/issues/honest_coverage_cron_vm_scheduling_2026_05_14.md)
    (P2 — honest-coverage 404 shows error state instead of graceful message)
- **Task**:
  1. **ICE US softs UAC fix**: Read `unified_api_contracts/canonical/domain/derivatives/tradfi_roots.py` (or wherever
     TRADFI_ROOTS lives). Add CT/CC/KC/SB/OJ/DX to TRADFI_ROOTS with `IFUS.IMPACT` venue. Fix any stale CME entries for
     CT. Run QG (`bash scripts/quality-gates.sh`). FF-push. Mark issue doc RESOLVED.
  2. **Honest-coverage graceful 404 in UI**: Locate the honest-coverage fetch in deployment-ui (grep
     `honest-coverage\|honestCoverage\|honest_coverage`). The fetch currently returns 404 when no data for the date → UI
     shows error state. Change: treat HTTP 404 from `/api/data-status/honest-coverage` as "data not yet computed" — show
     a neutral info message (`"Coverage data not yet computed for this date"`) instead of an error state. Run
     `pnpm build` + QG. FF-push.
  3. Update both issue docs with RESOLVED + SHAs. FF-push (PM).
- **Done-def**: TRADFI_ROOTS includes CT/CC/KC/SB/OJ/DX with IFUS.IMPACT; UAC QG green; deployment-ui shows graceful
  message on 404 from honest-coverage; both issue docs RESOLVED.
- **GREP-THEN-READ warning**: Read the TRADFI_ROOTS source dict body before adding — confirm CT is actually CME vs ICE
  before patching. Don't assume from the issue doc alone.

---

## Day-3 continuation task briefs — 2026-05-14 (slots 4/6/7/9 post-first-task)

### Slot 4 — writegate Phase 6.8 instruments-service (Sonnet 4.6 / thinking: high)

- **Owned repos**: `instruments-service` + `unified-api-contracts` (if seed dict missing) + `unified-trading-pm`
- **Plan-of-record**:
  [`plans/active/writegate_honest_coverage_endtoend_2026_05_06.md`](../plans/active/writegate_honest_coverage_endtoend_2026_05_06.md)
  § "Phase 6.8 — instruments-service catalog snapshot"
- **Task**: Phase 6.8 decision = Option (a): migrate all 41 `.add()` callsites in instruments-service to
  `record_captured()`. Steps:
  1. `grep -rn "\.add(" instruments_service/ --include="*.py" | grep -v test | grep -v venv` — count + locate all 41
     callsites.
  2. Read 3 representative callsites to understand the shape: what positional args does `.add()` receive today? Map to
     `record_captured(date, data_type, venue, pipeline_mode=..., shard_id=..., row_count=...)`.
  3. Sweep: replace `.add(` → `record_captured(` with correct kwargs. Add `pipeline_mode` from the CLI `--mode` arg
     (already wired in most instruments-service handlers).
  4. Wire `publish_with_policy` at the write boundary (same pattern as Phase 6.3 features-volatility
     @features-service@d7514a08 — read that commit for the template).
  5. `bash scripts/quality-gates.sh` from instruments-service root — all tests green.
  6. Plan-flip Phase 6.8 `[x]` with evidence + FF-push per shippable unit.
- **Reference**: Phase 6.3 template commit features-service@d7514a08. Phase 6.8 plan body at writegate plan line ~3458.
- **Done-def**: All 41 `.add()` callsites migrated + `publish_with_policy` wired + QG green + Phase 6.8 checkbox
  flipped.
- **Scope boundary**: Do NOT touch Phase 6.7 (strategy-service / execution-service / position-balance / risk) —
  Ikenna-owned.

### Slot 6 — writegate Phase 6.5 remaining open todos (Sonnet 4.6 / thinking: high)

- **Owned repos**: `features-service` + `unified-api-contracts` (if seed dict missing) + `unified-trading-pm`
- **Plan-of-record**:
  [`plans/active/writegate_honest_coverage_endtoend_2026_05_06.md`](../plans/active/writegate_honest_coverage_endtoend_2026_05_06.md)
  § "Phase 6.5" — scan for `- [ ]` todos only.
- **Task**: Phase 6.5 main wiring is ✅ done. Open items are:
  1. **Sports live_handler** — `live_feature_subset` STRICT_FAIL wiring deferred per task boundary. Wire
     `_check_emission_policy()` in `features_service/sports/cli/handlers/live_handler.py` (same pattern as
     batch_handler@a93dc3b4 but for live mode path).
  2. **P2 delta-one finding** — ~24 ohlcv-derived feature_groups share NAN_FILL policy but policy not seeded
     individually; either verify the catch-all covers them or add explicit UAC seed entries.
  3. **P2 cross-instrument seed drift** — `paired_spec` + registry drift flag; verify `_SEEDED_FEATURE_GROUPS` dict is
     in sync with `features_service/cross_instrument/schemas/`.
  4. **P2 multi-timeframe ambiguity** — `intraday_regime` + `tf_risk_reward` + `wedge_confluence` cross-TF aggregate
     classification; verify STRICT_FAIL is correct policy per plan notes.
  - For each: grep-then-read before changing. Fix if clear; file P2 issue doc if needs design call.
  5. Run `bash scripts/quality-gates.sh` from features-service root after each fix.
  6. Plan-flip each `[ ]` todo as shipped. FF-push per unit.
- **Done-def**: All open `- [ ]` Phase 6.5 todos resolved (fixed or filed as issue doc) + QG green.
- **Scope boundary**: Do NOT touch Phase 6.6 (ml-training / ml-inference) — Ikenna-owned.

### Slot 7 — Data Status UI Phase 2F: deployment-api/UI gap fixes from 6C smoke (Sonnet 4.6 / thinking: high)

- **Owned repos**: `deployment-api` + `deployment-ui` + `unified-trading-pm`
- **Plan-of-record**: First action = create `plans/active/data_status_ui_phase_2f.md` as the plan file for these 4 gaps
  (referenced from cross_asset plan line ~610 but never filed). Use it as your single plan-of-record for this slot.
- **Context**: Slot 7 Day-3 Wave 1 ran the 6C UI-drilldown smoke (deployment-stack up, Data Status panel loaded) and
  found 4 gaps. Implement what's unambiguous; file issue doc for anything needing spec/design.
- **Task — 4 gaps, work in order**:
  1. **GAP-2 — `cross_asset` absent from breakdown/filter** (mechanical UI fix):
     - `grep -rn "asset_group\|assetGroup\|CEFI\|TRADFI\|DEFI" deployment-ui/src/ --include="*.ts" --include="*.tsx" | grep -i filter | head -20`
     - Find the filter button array that lists CEFI/TRADFI/DEFI and add `CROSS_ASSET` (or `cross_asset`). Also check
       deployment-api router for `/data-status` — add `cross_asset` to any hardcoded allowlist.
     - Verify: `pnpm build` in deployment-ui; `bash scripts/quality-gates.sh` in deployment-api.
  2. **GAP-3 — SPORTS/PREDICTION absent from Asset Groups filter** (mechanical UI fix, same pattern as GAP-2):
     - Add `SPORTS` + `PREDICTION` to the same filter array. Check backend asset_group allowlist too.
  3. **GAP-4 — asset group rows not interactive** (UI behavior change):
     - Find the Data Status breakdown table/component. Add `onClick` → navigate to `?asset_group=X` or existing
       drilldown route. If no drilldown route exists for these groups → file as issue doc (scope too large for this
       slot, needs route design).
  4. **GAP-1 — `GET /api/data-status/honest-coverage` → 404** (new deployment-api endpoint):
     - Grep deployment-api router files for the endpoint. If endpoint spec is clear from adjacent code (e.g.,
       `/data-status/coverage` or `/data-status/summary` already exists and this is a variant) → implement it.
     - If spec is ambiguous (unclear response shape, unclear data source) → file issue doc with proposed spec. Do NOT
       guess implementation for a new public API endpoint.
- **Plan file**: Create `data_status_ui_phase_2f.md` with standard format (`estimate_class: design`, baseline ~3
  AI-days, calibrated ~1.8), enumerate all 4 gaps as `- [ ]` todos, flip each as you ship.
- **Done-def**: `data_status_ui_phase_2f.md` plan created; GAP-2 + GAP-3 implemented + QG green; GAP-4 implemented OR
  issue doc filed; GAP-1 implemented OR issue doc filed with proposed spec. FF-push per shippable unit.
- **Scope boundary**: Do NOT touch data_status_drilldown_shard_atom_alignment plan Phase 3 (Ikenna-adjacent). Do NOT
  touch honest-coverage Python script (`measure_honest_coverage.py`). UI + deployment-api only.

### Slot 9 — peripheral scripts pipeline_mode fix + workspace-manifest QG step 6 investigation (Sonnet 4.6 / thinking: high)

- **Owned repos**: `market-tick-data-service` + `features-service` + `unified-trading-library` + `instruments-service` +
  `strategy-service` (QG investigation only) + `unified-trading-pm`
- **Plan-of-record**:
  [`plans/active/writegate_honest_coverage_endtoend_2026_05_06.md`](../plans/active/writegate_honest_coverage_endtoend_2026_05_06.md)
  Phase 4 (manifest writer API) + strategy-service QG step 6 flag from slot 4.
- **Task Part A — peripheral scripts pipeline_mode sweep** (mechanical): The following 10 scripts still call
  `record_captured/record_empty/record_failed/record_expected_unattempted` without `pipeline_mode` kwarg — they will
  fail at runtime:
  - `market-tick-data-service/scripts/mtds_reconcile_partial_bundles.py`
  - `market-tick-data-service/scripts/build_continuous_es.py`
  - `market-tick-data-service/market_tick_data_service/scripts/rebuild_prediction_manifest.py`
  - `features-service/scripts/sports/features_sports_reconcile_available_at.py`
  - `features-service/scripts/sports/backfill_fixture_features_manifest.py`
  - `features-service/scripts/sports/compute_sfi_progressive_only.py`
  - `unified-trading-library/unified_trading_library/manifest_completeness.py`
  - `unified-trading-library/unified_trading_library/options_cluster_lookup.py`
  - `instruments-service/scripts/backfill_drift_funding_2026_05_13.py`
  - `unified-trading-library/unified_trading_library/manifest_freshness.py` For each: read the callsite → determine
    correct `pipeline_mode` from context (batch scripts → `PipelineMode.BATCH`; reconcilers → `PipelineMode.BATCH`) →
    add kwarg → commit + push per repo.
- **Task Part B — workspace-manifest QG step 6 investigation**: Slot 4 flagged strategy-service QG step 6 (production
  readiness) failing on `workspace-manifest.json`. Investigate:
  `cd strategy-service && bash scripts/quality-gates.sh 2>&1 | grep -A 20 "step 6\|STEP 6\|workspace-manifest"`.
  Determine root cause: version misalignment, missing field, or stale dep? If it's a version alignment issue:
  `cd unified-trading-pm && bash scripts/repo-management/run-version-alignment.sh --fix`. If code-level: fix it
  directly. File issue doc if diagnosis is ambiguous.
- **Done-def**: All 10 scripts updated + QG step 6 diagnosed (fixed or issue doc filed) + plan todos flipped.

---

## Day-3 Wave 1 task briefs — 2026-05-14 (clear/stable; spawn first)

### Slot 2 — api_football Phase 3.C EPL forward-poll VM + UI verify (Sonnet 4.6 / thinking: high)

- **Owned repos**: `instruments-service` + `deployment-service` (tarball + VM launcher) + `unified-trading-pm`
- **Plan-of-record**:
  [`plans/active/api_football_phase_3b_3c_smoke_forward_poll_2026_05_13.md`](../plans/active/api_football_phase_3b_3c_smoke_forward_poll_2026_05_13.md)
  (Phase 3.B ✅ DONE 2026-05-13; this is Phase 3.C only)
- **Task**:
  1. Refresh VM tarball: `bash deployment-service/scripts/vm/create-code-tarballs.sh --sports-only`. Verify tarball @
     `gs://deployment-scripts-${PID}/code/`.
  2. Launch EPL forward-poll VM:
     `bash deployment-service/scripts/vm/launch-sports-instruments-reference-vm.sh --asset-group sports --start-date 2026-05-13 --end-date 2026-05-13`.
     NOT a reconciliation VM — Ikenna's hold does NOT apply.
  3. Monitor execution 1-2 hours wall clock — `gs://${PROJECT_ID}-events/events/instruments-service/` for
     `INSTRUMENT_ENTITY_CAPTURED` events; abort on `ADAPTER_FETCH_FAILED`.
  4. Verify data-status panel schema: open deployment-ui → Data Status → Sports → Match → Fixtures → Schema modal:
     FIXTURE_STATS shows ~18 columns (not old 2-column schema). Screenshot.
  5. Spot-check features-sports calculator if any depend on fixture_stats (skip if no calculator exists yet).
  6. Plan-flip Phase 3.C `[x]` with VM-run evidence + screenshot. Write DONE-2026-05-14 block. FF-push per shippable
     unit.
- **Done-def**: Plan body Phase 3.C `[x]` flipped with VM-run evidence + screenshot + features verification (or
  skip-noted); api_football plan DONE-2026-05-14 block. Schema rows on UI match expected per-data_type column counts.
- **Credentials**: `gcloud secrets versions access latest --secret=api-football-api-key` (already-verified in Phase 3.B
  2026-05-13).
- **No big decisions needed.**

### Slot 6 — Phase 1 freeze-gate readiness audit (Sonnet 4.6 / thinking: high; read-only audit)

- **Owned repos**: `unified-trading-pm` (output only) + workspace-wide read-only grep
- **Plan-of-record**:
  [`plans/active/master_to_live_defi_2026_05_23.md`](../plans/active/master_to_live_defi_2026_05_23.md) § "Phase 1
  freeze-gate items status (post Day-1 EOD)" +
  [`writegate_honest_coverage_endtoend_2026_05_06.md`](../plans/active/writegate_honest_coverage_endtoend_2026_05_06.md)
  Phase 4
- **Task**: For each of the 6 freeze-gate items, run workspace-wide grep + verification — confirm plan-flip matches
  on-disk reality. Items #3 (PipelineMode 37-callsite migration) + #6 (LookaheadBiasError strict-mode features-\*) are
  the two 🟡 partials from Day-2 EOD; specifically:
  1. Item #3: workspace-grep for `pipeline_mode=` at every `record_*` callsite + verify QG STEP 5.68 baseline
     `0 new occurrences`. If any callsite still uses default, file as P0 with file:line.
  2. Item #6: workspace-grep for `LookaheadBiasError` strict-mode wire-ins across `features-*-service/`. Verify all 8
     families (delta_one / volatility / calendar / commodity / cross_instrument / multi_timeframe / onchain / sports)
     have `strict=True` enforcement at writer boundary.
  3. Items #1-#2, #4-#5: spot-check evidence cited in master plan against actual SHA + grep proof.
  4. Write audit report at `plans/active/issues/freeze_gate_readiness_audit_2026_05_14.md` if ANY mismatch found; OR ack
     as report at master plan inline + ping `harsh_orchestrator/pings/slot_6.md`.
- **Done-def**: All 6 items confirmed green-on-disk; if mismatch found, P0 issue doc filed + slot 1 main pinged.
- **No big decisions needed.**

### Slot 7 — Slot 7 Wave 4 carry-forward sweep (Sonnet 4.6 / thinking: high)

- **Owned repos**: `unified-trading-system-ui` + `unified-trading-pm` + read-only on UAC + instruments-service
- **Plan-of-record**:
  [`plans/active/cross_asset_group_catalogue_audit_2026_05_10.md`](../plans/active/cross_asset_group_catalogue_audit_2026_05_10.md)
  Phase 6C + Phase 1D consumer migration
- **Task**: 3 items, ship in order:
  1. **UI `ui-reference-data.json` copies** — slot 7 Wave 4 shipped TRADER_JOEV2 producer-side migration across 3
     backend repos (UAC@`da3ef9b` + instruments-service@`dd03a15` + MTDS@`3cf0f09`). Consumer side: 4
     `ui-reference-data.json` copies in `unified-trading-system-ui` need the same TRADER_JOEV2/TRADERJOEV2 fix. Find via
     `grep -rn TRADER unified-trading-system-ui/`. Update each + run UI build smoke (`pnpm build`) to confirm no schema
     breakage.
  2. **6C UI-drilldown smoke** — start deployment-stack
     (`bash unified-trading-pm/scripts/dev/restart-deployment-stack.sh`). Verify which UI panels work pre-cutover. Walk
     Data Status → cross_asset drilldown for at least 1 venue per asset_group; capture screenshots OR report gaps as
     issue doc.
  3. **ICE US softs (CT/CC/KC/SB/OJ/DX) dataset disambiguation** — `tradfi_symbology.py` (IFUS.IMPACT) vs
     `tradfi_instrument_universe.py` (GLBX.MDP3) — reconcile to single dataset per softs symbol OR file design-call
     issue doc with proposed dataset + reasoning.
- **Done-def**: 4 UI copies updated + build green; 6C smoke walk-through done with screenshots OR gap report; ICE US
  softs disambiguated or filed.
- **No big decisions needed** (DF-5 sDAI design call DEFERRED post-cutover per master plan scope; do NOT touch).

### Slot 9 — defi_recursive_borrow DESCOPE successor plan + plan-body annotation (Sonnet 4.6 / thinking: high)

- **Owned repos**: `unified-trading-pm` only (no code changes)
- **Plan-of-record**:
  [`plans/active/defi_recursive_borrow_archetypes_2026_05_10.md`](../plans/active/defi_recursive_borrow_archetypes_2026_05_10.md)
  descope + new successor plan
- **Task**:
  1. Read current plan body — understand which phases are shipped vs unshipped vs partial. Per Ikenna audit batch
     PM@`e1e67656`: ~7% truly done (UAC half), Solidity (`RecursiveLeverageReceiver.sol`) + execution-service
     orchestrator + strategy-service tracer + codex + deployment-ui halves genuinely unshipped.
  2. Annotate current plan body with descope decision: "May-23 ships archetype documented; Phase 2-3 Solidity +
     execution halves deferred to successor". Reference master plan only commits `carry_staked_basis` +
     `arbitrage_price_dispersion` for May-23 live (recursive_borrow not in live cutover scope).
  3. File new successor plan `plans/active/defi_recursive_borrow_archetypes_post_cutover_2026_06_01.md` (or
     `_2026_06_15.md`) with:
     - `migrated_from: defi_recursive_borrow_archetypes_2026_05_10.md`
     - `estimate_class: design` + `estimate_baseline_ai_days` + `estimate_calibrated_ai_days` (use Ikenna's audit
       estimate: Solidity + execution + strategy + codex + UI halves, multi-week scope)
     - Migrated todos with `**MIGRATED FROM:** defi_recursive_borrow_archetypes_2026_05_10.md` provenance per CLAUDE.md
       "Plan Archival" HARD RULE
     - Successor-plan banner on current plan
  4. Update master plan inventory dashboard line for recursive_borrow (rerun
     `python3 scripts/plans/regenerate_active_plan_inventory.py`).
- **Done-def**: Current plan annotated with descope decision + successor banner; successor plan filed at
  `plans/active/`; master plan inventory regenerated.
- **No big decisions needed** (descope decision pre-confirmed by operator this morning).

---

## Day-3 Wave 2 task briefs — 2026-05-14 (queued; spawn after Wave 1 in flight)

### Slot 3 — 117 UTL test-fixture sweep (Sonnet 4.6 / thinking: high; mechanical sweep)

- **Owned repos**: `unified-trading-library` + `unified-trading-pm`
- **Plan-of-record**: UTL@`547ff3c` API drift (file issue doc if root-cause needs design) +
  [`writegate_honest_coverage_endtoend_2026_05_06.md`](../plans/active/writegate_honest_coverage_endtoend_2026_05_06.md)
  Phase 4 follow-up
- **Task**: UTL Phase 4.DEFAULT-REMOVAL (UTL@`547ff3c`) added `pipeline_mode` as a required kwarg to all
  `ManifestWriter.record_*` methods. Test fixtures across UTL test suite call the old signature → 117 test failures
  yesterday per slot 9's side-finding. Sweep:
  1. Use repo-local `.venv` (NOT workspace `.venv-workspace`) per CLAUDE.md venv rule. Run
     `bash scripts/quality-gates.sh` from `unified-trading-library/` to reproduce + count failures.
  2. Sweep tests under `unified-trading-library/tests/` — add `pipeline_mode="batch"` (or
     `pipeline_mode=PipelineMode.BATCH` if importing the enum) to all `record_captured` / `record_empty` /
     `record_failed` / `record_expected_unattempted` callsites that lack it. Scope: ~35 `record_empty` + ~37
     `record_captured` + ~14 `record_failed` + ~4 `record_expected_unattempted` test callsites.
  3. Re-run QG; surface any non-mechanical failures as issue docs (file under `plans/active/issues/` with
     `severity: P1`).
  4. Plan-flip the writegate plan Phase 4 follow-up checkbox (if exists) OR file issue doc closing 117-test-failure
     side-finding.
- **Done-def**: 117 UTL tests pass via `bash scripts/quality-gates.sh`; pre-existing-foreign issues (non-mechanical)
  filed as issue docs with owner-tag.
- **GREP-THEN-READ warning**: before mass-replacing, read 3 sample test callsites + the UTL `record_*` signature to
  confirm correct kwarg name + value. Don't grep-then-replace blindly.
- **No big decisions needed.**

### Slot 4 — 2-of-17 remaining strategy-service test failures (Sonnet 4.6 / thinking: high; diagnose-first)

- **Owned repos**: `strategy-service` + `unified-trading-pm` (for issue docs if needed)
- **Plan-of-record**: strategy-service test suite (slot 4's Wave 4 carry-forward from strategy-service@`114f8b2`)
- **Task**: Slot 4 yesterday fixed 15 of 17 pre-existing strategy-service test failures at strategy-service@`114f8b2`. 2
  remaining — identify which 2 from yesterday's 14:30 UTC slot 4 ping list (TestResolverFactoryCoverage +
  test_factory_builds_all_v1_archetypes + test_target_universe + test_coverage_uncovered_modules +
  test_risk_preflight_gate + test_error_handling). Apply Findings Triage HARD RULE diagnose-first principle:
  1. Use strategy-service local `.venv` (NOT workspace venv) per CLAUDE.md venv rule. Run
     `bash scripts/quality-gates.sh` from `strategy-service/` to identify the 2 remaining failures.
  2. For each failure: read BOTH sides of the contract (test + code-under-test). Diagnose: is code stale or is test
     stale per current SSOT?
  3. If code stale → fix code; if test stale → fix test; if genuinely ambiguous → file issue doc with explicit "needs
     design call" diagnosis.
  4. Plan-flip OR file issue.
- **Done-def**: 2 remaining strategy-service tests EITHER fixed OR filed as issue doc with explicit "needs design call"
  diagnosis.
- **No big decisions needed** (Findings Triage HARD RULE codified yesterday in CLAUDE.md — diagnose-first, don't just
  patch tests blindly).

---

## Day-3 Wave 3 — batch_live_symmetry (2026-05-14)

### Slots 5 + 8 — batch_live_symmetry Tabs 1-3 (Sonnet 4.6 / thinking: high; paired slot work)

- **Status**: ✅ CLEARED — operator override 2026-05-14. Cross-side handshake deferred; Harsh-side ownership of Tabs 1-3
  confirmed by operator. Slots 5 + 8 ready to spawn fresh.
- **Owned repos**: `unified-trading-pm` (codex) + `unified-api-contracts` + per-service test wiring
- **Plan-of-record**:
  [`plans/active/batch_live_symmetry_2026_05_10.md`](../plans/active/batch_live_symmetry_2026_05_10.md) Tabs 1-3

---

### Day-3 Wave 3 task briefs — Slot 5 (batch_live_symmetry Tabs 1-2)

**Model**: Sonnet 4.6 / thinking: high **Worktree**: `.tabs/5/` — fresh spawn, align all repos to
origin/live-defi-rollout before starting **Owned repos**: `unified-trading-pm` (codex docs) + `unified-api-contracts`
(Tab 2 UAC contract)

**Scope — Tab 1 (codex SSOT batch)**:

- NEW `codex/04-architecture/cefi-batch-live.md` — per-asset-group narrative for cefi (matcher pattern + shard
  atomicity + venue list per pre-audit § 1 Tab 1). Cross-link to `batch-live-architecture.md` § 5.
- NEW `codex/06-coding-standards/mode-axis-discipline.md` — cartesian product table for `RuntimeMode` ×
  `OperationalMode` × `BatchExecutionMode` × `MaturityPhase`. Anti-pattern list. Cite pre-audit § 1.
- UPDATE `codex/04-architecture/batch-live-architecture.md` — add cross-asset-group meta section + UI mode-context
  guidance + consolidated anti-patterns.
- UPDATE `codex/06-coding-standards/quality-gates.md` — STEP entries for L1/L2/L3/L7. Defer L4/L5/L6.
- UPDATE `codex/05-infrastructure/replay-subsystem.md` — implementation status + REPLAY_BACKSTOP_REACHED wiring note.
- UPDATE `codex/04-architecture/features-service-architecture.md` — sports + calendar live-handler timeline.
- Land 4 IN-FLIGHT REFACTOR banners at top of cross-plan target files.

**Scope — Tab 2 (UAC + UTL)**:

- Ship `unified_api_contracts/canonical/crosscutting/execution/batch_execution_mode.py` — `BatchExecutionMode` enum.
- Ship `unified_api_contracts/canonical/crosscutting/alerting/thresholds.py` — `RECON_GREEN_THRESHOLDS` dict with
  initial values for `carry_staked_basis` + `leveraged_funding_arb`.
- ServiceEmissionPolicy: audit existing `SERVICE_OUTPUT_POLICIES` (71 rows already shipped per slot 3 audit). Verify the
  9 originally-specified entries are present; flip that checkbox if ✅.
- L7 verification sweep — confirm 3 violations at MDPS (`storage_dispatch_worker.py:49`, `output_writer_service.py:318`,
  `orchestration_writer.py:388`); audit 2 at UTL `domain/standardized_service.py:100,299`; produce fix-list (NOT fixes —
  hand to Tab 3/MDPS owner).
- J1 helper: ship design stub only at `unified_api_contracts/internal/domain/strategy_service/lifecycle.py:91-116`
  (wire-in deferred post-cutover per defaults #2).
- QG green on both repos before push.

**Done-def**:

- Tab 1: 2 NEW + 4 UPDATE codex docs committed to PM + pushed. 4 cross-plan banners landed. Plan checkboxes flipped.
- Tab 2: BatchExecutionMode enum + RECON_GREEN_THRESHOLDS + L7 fix-list committed to UAC + pushed. QG green.

**Pre-reads** (before any work):

1. `plans/active/batch_live_symmetry_2026_05_10.md` § Tab 1 + § Tab 2
2. `plans/questions/batch_live_design_symmetry_preaudit_2026_05_10.md` § 1.Tab1 + § 1.Tab2 + § 3 + § 7
3. `cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
4. The 6 codex docs in plan frontmatter `related_codex`

---

### Day-3 Wave 3 task briefs — Slot 8 (batch_live_symmetry Tab 3)

**Model**: Sonnet 4.6 / thinking: high **Worktree**: `.tabs/8/` — fresh spawn, align all repos to
origin/live-defi-rollout before starting **Owned repos**: `unified-trading-pm` (base-service.sh template) + all service
repos touched by L1/L2/L3/L7 STEPs

**Scope — Tab 3 (QG STEPs L2/L3/L7 workspace AST sweeps)**:

- L1 + L5 DAY-1 ENABLE — add STEP entries to `scripts/quality-gates-base/base-service.sh`. Pre-flight = 0 violations so
  no fixes needed first.
- L2 violation fix-batch — ~21 violations across features-\*/strategy/MDPS per pre-audit § 1 Tab 3. Audit each:
  move-to-seam OR unify-path. Fan out to ~5 service commits; serialise commits within this slot to avoid collision per
  pre-audit § 7.
- L2 STEP enable — only AFTER fix-batch lands + workspace CI green.
- L3 violation fix-batch — UAC re-export RuntimeMode from UTL canonical (1 PR);
  `unified-trading-system-ui/context/internal-contracts/schemas/modes.py` re-export from UAC (1 PR).
- L3 STEP enable — only after fix-batch lands.
- L7 enforcement verification sweep — AST-walk every `record_captured(` callsite; ensure UTL
  `assert_available_at_present` fires on every write path.
- PM QG green + push after each STEP enable.

**Critical sequencing constraint**: Tab 3 depends on Tab 2's `BatchExecutionMode` enum being on LDR first (Slot 5 ships
Tab 2). Check that `unified_api_contracts/canonical/crosscutting/execution/batch_execution_mode.py` exists on
origin/live-defi-rollout before enabling L3 STEP. If Slot 5 is still in flight, do L1/L5/L2 work first and hold L3 until
UAC is visible on LDR.

**Done-def**:

- 4 STEPs (L1+L5+L2+L3) enabled in `base-service.sh` template + rollout-propagated to all service repos.
- L2 fix-batch: ~5 service commits on LDR.
- L3 fix-batch: UAC + UI redeclaration replaced with re-export imports.
- L7 audit complete with fix-list issued.
- Workspace CI green for 2h continuous post-L2-enable.
- Plan checkboxes flipped per shippable unit.

**Pre-reads** (before any work):

1. `plans/active/batch_live_symmetry_2026_05_10.md` § Tab 3
2. `plans/questions/batch_live_design_symmetry_preaudit_2026_05_10.md` § 1.Tab3
3. `scripts/quality-gates-base/base-service.sh` (understand existing STEP structure)
4. `cursor-configs/SUB_AGENT_MANDATORY_RULES.md`

---

## 2026-05-13 PM shift end — final closeout (harsh-main, 2026-05-13 15:30 UTC ish)

**Shift status**: ✅ ALL 6 active implementor slots reported DONE. Slots 5/8/10 idle/closed; slot 1 main online.

**Per-slot final state** (all verified on LDR via commit-sha checks):

- **Slot 2** ✅ Wave 4 DONE — data_status_drilldown Phase 7 P1+P2 across deployment-{service,api,ui} (PM@531f04f3
  closeout). Plan 31/41 + scoreboard.
- **Slot 3** ✅ Wave 4 DONE — execution-service C901 + 7 pre-existing test fixes (execution-service@2dee623f +
  @9758f9fc + @6a993bdb partial codex). Surfaced 2 issue docs for defi 604,951-row finding.
- **Slot 4** ✅ Wave 4 DONE — arbitrage 20/20 + 15-of-17 pre-existing strategy-service test fixes
  (strategy-service@114f8b2) + sigma RUF002 + C901 refactor + service_entry --synthetic-input-uri stash-pop. BIG FINDING
  (defi 604k rows) now tracked in 2 issue docs.
- **Slot 6** ✅ Wave 3 DONE — wave3x_residual_ssots + per_agent_worktrees 30/30 + api_football 13/16. Reported "honest
  gap": LEDGER regression from Ikenna merge `634e15d9` was unflagged — fixed in this consolidated re-flip.
- **Slot 7** ✅ Wave 4 SHIFT-END DONE — TRADER_JOEV2 producer migration (3 repos: UAC@da3ef9b +
  instruments-service@dd03a15 + MTDS@3cf0f09) + STEP 5.72 QG ratchet (PM@fd9aee9e) + force-push recovery (UAC@e7c12fa
  wallet_treasury Phase 1 + UAC@861d2a6 RUF003 cherry-picked from reflog).
- **Slot 9** ✅ Wave 3 DONE — sports classifier extension (UTL@3928e3a, 52 tests) + Script 3 sports DRY-RUN (0
  upgrades).

**🔴 Force-push incidents today** (4 in PM + 2 in UAC + ≥1 in instruments-service):

- Source: `semver-rollout[bot]` (Ikenna-side committer pattern). Every force-push target was a sports-flatten /
  sports_master commit (C.4 Transfermarkt / C.6 SPORTS_FIXTURES / C.7 STANDINGS / sports-fixtures-lifecycle).
- Operator flagged to Ikenna directly. Slot 7 cherry-picked + restored all Harsh-side work; Ikenna-side casualties
  (writegate Phase 6.6/6.7/6.9, data_status_drilldown Phase 7 P2, api_football Phase 3.B) handed to Ikenna-main triage.
- Each repo's reflog preserved as evidence (`git reflog origin/live-defi-rollout` shows `forced-update` markers).

**Operator-pending carry-forward** (not blocking):

1. Telegram OPS chat_id (DEFERRED-PER-USER).
2. AWS bucket creation (Phase 2.6 window 2026-05-15→19, needs GCE VM with aws CLI).
3. **117 UTL test failures** from UTL@547ff3c `ManifestWriter.record_empty()` `pipeline_mode` kwarg API drift —
   unassigned, Harsh-side API hardening that didn't sweep test fixtures.
4. defi 604,951 rows reclassification scope (2 issue docs filed) — awaits design call.
5. DF-5 sDAI protocol-attribution split — needs operator/ikenna design call (audit recommends MAKER consolidation;
   blocked by hard-asserting test at `tests/unit/test_lst_protocol_asset.py:73`).
6. Slot 6 / api_football 3 DEFERRED items — operator-executable post-cutover.
7. UI-drilldown half of cross_asset Phase 6C — needs deployment-stack live.
8. wallet_treasury_client_flow_2026_05_10.md Phase 1 was `[x]` while UAC@ca36caa was missing from LDR for hours — now
   consistent with UAC@e7c12fa (cherry-pick recovery).

**Cron loop (3-min poll, ID `4269c2cc`) stopped at shift end.**

**Critical-path sequencing (slot 1 monitors during Wave 2)**:

1. Slot 4 ships Script 3 classifier fix → unblocks defi/sports/prediction legacy-blank reclassification (deferred
   apply-flips still pending post-cutover)
2. Slot 9 ships mock_data Phase 3.D → benchmark report has real 6-stage timings (not extrapolated)
3. Slots 2/3/6/7 fully independent — run in parallel
4. New HARD RULE: LDR-alignment cadence (codified 2026-05-13 PM@f49d5f7d). Slots that boot must rebase ALL owned repos;
   FF-push per shippable unit, not end-of-session

**Wave 1 audit retrospective**: 3 critical follow-ups pushed PM@7ca204a6 — see
`plans/active/issues/audit_wave1_quality_2026_05_13.md` for synthesis. Two impact Wave 2 spawn:

1. Slot 9 Task 3 strategy-paper VM was never actually launched in Wave 1 — re-opened in
   `promote_workflow_may23_cli_path_2026_05_10.md` Phase 1 as P0. Available for any slot that finishes early to absorb.
2. Sports classifier extension never shipped (slot 9 Wave 1 grep-then-conclude miss) — re-filed as
   `plans/active/issues/sports_classifier_extension_followup_2026_05_13.md` P1. Available for reserve pickup.

**Operator-pending**: None blocking Wave 2 spawn. Carry-forward (post-cycle operator decisions): slot 8's A/B/C UAC
architecture triage (deferred; lives in cross-side `_agent_pings.md`); Telegram OPS chat_id (operator action); AWS
bucket creation (Phase 2.6 window, needs GCE VM with aws CLI).

---

## Wave 2 task briefs (slot N agents — read your row)

Each row is a full task brief. After `--reset-slot N` (done 2026-05-13 09:35 UTC), your worktree at `.tabs/N/` is clean
on `tab/hk/N` matching `origin/live-defi-rollout`. Just boot + read your row + start.

### Slot 2 — risk_simulations finalisation (Sonnet 4.6 / thinking: high)

- **Owned repos**: `risk-and-exposure-service` + `unified-api-contracts` + `unified-trading-pm`
- **Plan-of-record**:
  [`plans/active/risk_simulations_limits_alerting_2026_05_10.md`](../plans/active/risk_simulations_limits_alerting_2026_05_10.md)
  (currently 33/40 P0 = 82%)
- **Task**: Ship the 7 open P0 items:
  1. Phase 4.A — risk-and-exposure-service rule migration to UAC registry; rule_evaluator wired
  2. Phase 8.A — Per-rule synthetic-fire test (uses `simulation_scenarios_topology_price_shocks_2026_05_09`)
  3. Phase 8.B — Per-archetype suite: ≥10 rules per archetype fire on schedule + alert routes per archetype
  4. Phase 8.C — Evidence capture
  5. Phase 9.A — Master plan Group F item 20 row gains "risk rule taxonomy + pre-flight + alerting wire"
  6. Phase 9.B — Banners removed
  7. (4 P1 stablecoin items D.2/D.5/D.6/D.7 — only if time after P0s done)
- **Done-def**: 33/40 → 40/40 P0; rule_evaluator wired; per-archetype suite green; Group F item 20 flipped.
- **No big decisions needed.**

### Slot 3 — DR finalisation (Sonnet 4.6 / thinking: high)

- **Owned repos**: `deployment-service` + `unified-trading-library` + `unified-trading-pm`
- **Plan-of-record**:
  [`plans/active/disaster_recovery_circuit_breakers_2026_05_10.md`](../plans/active/disaster_recovery_circuit_breakers_2026_05_10.md)
  (currently 28/42 = 67%)
- **Task**: Write scripts + master-plan rows. **DO NOT LAUNCH ANY VMs** — Ikenna's hold direction on backfill/recon VMs
  is conservative; treat DR-drill VM launches the same and gate execution on operator OK.
  1. Phase 6.A — Cron VM `disaster-drill-cron-` launcher SCRIPT (writes only; no launch)
  2. Phase 6.B — Drill-report tooling (pass/fail per scenario; alerting rule on red >24h)
  3. Phase 9.A — Per-archetype `dr-drill-cutover-` launcher SCRIPT (arm `KILL_PER_ARCHETYPE`, etc.)
  4. Phase 9.B — Evidence-capture format
  5. Phase 10.A — Master plan rows Group F item 20 + 21 green
  6. Phase 10.B — Banners removed
- **Done-def**: 28/42 → ~38/42; SCRIPT artifacts written + linted + dry-run validated locally; ping `pings/slot_3.md`
  when scripts ready for operator OK to launch VMs.
- **No big decisions needed.**

### Slot 4 — 🐛 Script 3 classifier P1 + arbitrage final (Sonnet 4.6 / thinking: high)

- **Owned repos**: `instruments-service` + `unified-trading-library` + `strategy-service` + `unified-trading-pm`
- **Plans-of-record**:
  - [`plans/active/issues/classify_blank_reason_fixture_manifest_kwarg_2026_05_13.md`](../plans/active/issues/classify_blank_reason_fixture_manifest_kwarg_2026_05_13.md)
    (P1 bug, slot 6 Wave-1 filed)
  - [`plans/active/arbitrage_price_dispersion_finalisation_2026_05_09.md`](../plans/active/arbitrage_price_dispersion_finalisation_2026_05_09.md)
    (18/20 = 90%, 2 P1 items left)
- **Task**:
  1. **Fix `classify_blank_reason_row()` `fixture_manifest` kwarg mismatch**: Read UTL
     `unified_trading_library.manifest.classify_blank_reason_row` signature; read
     `instruments-service/scripts/reconcile_legacy_blank_to_typed_reason.py` call-site; align (add `fixture_manifest`
     handling to reconciler OR drop from UTL — pick per which is canonical intent). FF-push.
  2. **Re-run Script 3 DRY-RUN** for defi/sports/prediction (NO `--apply-flips` — Ikenna's hold direction on manifest
     reconciliation VMs still applies). Update the issue doc with dry-run upgrade counts. FF-push.
  3. **Arbitrage final 2 items**: canonical BTC/USDT slot entry in strategy-service + tests (per plan-of-record line
     `^- \[ \]`). FF-push.
- **Done-def**: Script 3 classifier signature aligned + dry-run shows non-zero upgrades for defi/sports/prediction;
  arbitrage_price_dispersion 18/20 → 20/20.
- **No big decisions needed.**

### Slot 6 — wave3x_residual_ssots finalisation (Sonnet 4.6 / thinking: high)

- **Owned repos**: `unified-api-contracts` + `unified-trading-library` + per-asset_group services (as items dictate) +
  `unified-trading-pm`
- **Plan-of-record**:
  [`plans/active/wave3x_residual_ssots_2026_05_08.md`](../plans/active/wave3x_residual_ssots_2026_05_08.md) (currently
  16/22 = 73%, 6 items left across Tracks B/C/D/E)
- **Task**: Read the plan. Scan open `- [ ]` todos under Tracks B (sports per-source SSOTs) / C (reconcilers) / D
  (zero-activity-bar audit) / E (sports availability stamping cascade). Ship in plan order. FF-push per shippable unit.
- **Done-def**: 16/22 → 22/22; all Wave 3.X dimensions covered.
- **No big decisions needed.**

### Slot 7 — cross_asset Phase 5 TradFi consolidation (**Opus 4.7 / thinking: high** ⬆ — multi-callsite refactor)

- **Owned repos**: `unified-api-contracts` + `instruments-service` + `market-tick-data-service` + `unified-trading-pm`
- **Plan-of-record**:
  [`plans/active/cross_asset_group_catalogue_audit_2026_05_10.md`](../plans/active/cross_asset_group_catalogue_audit_2026_05_10.md)
  § Phase 5 + reference
  [`plans/archive/issues/catalogue_audit_tradfi_2026_05_12.md`](../plans/archive/issues/catalogue_audit_tradfi_2026_05_12.md)
  for TF-1..TF-10 detail
- **Task**:
  1. **Phase 5A — `tradfi_etfs.py`**: Diff-merge 4 ETF universes → single SSOT at
     `unified_api_contracts/canonical/domain/derivatives/tradfi_etfs.py`. Sources: `tradfi_symbology.py:459`
     `KNOWN_ETFS` + `tradfi_ticker_universe.py:295` `ETF_TICKERS` + `tradfi_instrument_universe.py:151`
     `_BTC_SPOT_ETFS`+`_ETH_SPOT_ETFS` + `TRADFI_TICKER_COVERAGE_START` ETF subset. **READ each source file body** — do
     not grep-then-conclude on membership equivalence. Escalate membership conflicts to operator via `pings/slot_7.md`.
  2. **Phase 5B — `tradfi_roots.py`**: Diff-merge 3 futures-roots universes (`TRADFI_INSTRUMENTS` +
     `TRADFI_DATABENTO_INSTRUMENTS` + `databento_cme_converter.py:57` `SUPPORTED_UNDERLYINGS`) → single SSOT.
  3. **Phase 5C — `asset_group_registry.py`**: TradFi entries point at new SSOTs.
  4. **Phase 7 (small) — VIX-15m doc-pointer fix (TF-7)**: VIX-15m constants live in
     `registry/data_source_continuity.py` NOT `canonical/crosscutting/honest_coverage.py` as CLAUDE.md L535 claims. Fix
     the doc reference in CLAUDE.md + any codex doc that mirrors the wrong pointer.
- **Done-def**: 4 ETF universes → 1 SSOT (membership diff documented in plan body); 3 futures-roots → 1 SSOT;
  cross_asset audit Phase 5 checkboxes flipped with evidence; VIX-15m doc-pointer corrected.
- **GREP-THEN-READ warning**: This is multi-callsite refactor. Wave 1 audit found Sonnet had grep-then-conclude failures
  on this exact shape (3 of 3 slots). Read each source file's actual dict/tuple contents — don't trust the variable name
  to imply the contents.
- **Escalated to Opus 4.7** per Wave 1 audit recommendation.

### Slot 9 — mock_data Phase 3.D per-reader threading (**Opus 4.7 / thinking: high** ⬆ — 3-reader bespoke wire-in)

- **Owned repos**: `market-tick-data-service` + `ml-inference-service` + `strategy-service` +
  `unified-trading-library` + `unified-trading-pm`
- **Plan-of-record**:
  [`plans/active/mock_data_pipeline_benchmarking_2026_05_10.md`](../plans/active/mock_data_pipeline_benchmarking_2026_05_10.md)
  § Phase 3.D (currently 19/29 = 66%)
- **Task**: Wire `default_subprocess_pipeline()` benchmark harness into 3 readers that bypass `resolve_bucket_uri`. For
  EACH reader, OPEN the function body before deciding the wire-in shape:
  1. **MTDS Tardis/Databento fetch**: External-API non-GCS readers. Needs benchmark-specific instrumentation hook (NOT
     standard `resolve_bucket_uri` override since these don't go through GCS).
  2. **ml-inference direct feature-vector loader**: Add bespoke `_STAGE_COMMAND_TEMPLATES` entry.
  3. **strategy direct signal+features loader**: Same pattern as (b). Then verify with subprocess-pipeline benchmark on
     1-day batch.
- **Done-def**: mock_data 19/29 → ~25/29; Phase 3.D `[x]` flipped with shipped SHAs; benchmark report includes all 6
  pipeline stages with REAL timings (currently extrapolated for these 3).
- **GREP-THEN-READ warning**: Slot 9 in Wave 1 had a grep-then-conclude failure on sports classifier. Don't repeat —
  open each reader's function body before declaring shape.
- **Escalated to Opus 4.7** per Wave 1 audit recommendation.

---

## Spawned tab — boot

You are slot N. Do this in order, nothing else until done:

1. Read [`AGENT_ONBOARDING.md`](AGENT_ONBOARDING.md) — git discipline, LDR-alignment HARD RULE, workspace-drift
   recognition, communication bus, pre-commit check, sub-agent rules.
2. Find your **Slot N task brief** in this LEDGER § "Wave 2 task briefs" above → that's your full assignment (owned
   repos + scope items + done-def + model tier).
3. Read your **plan-of-record** (named in your brief) — scan open `- [ ]` todos for your phase.
4. Append boot ack to [`pings/slot_N.md`](pings/) using `date -u` for timestamp, then start work.

**COMPACT-CYCLE GUARD**: Do NOT read repo-level `.claude/CLAUDE.md` files from repos you're working in — the workspace
CLAUDE.md (auto-loaded in system context) covers all critical cross-cutting rules. Only read a repo's CLAUDE.md if it's
explicitly named in your task brief.

---

## Default agent-spawn workflow (HARD RULE — codified 2026-05-13)

**This is the default for every wave / morning / mid-day relaunch.** Operator should NEVER receive a verbose paste-ready
spawn prompt from main unless they explicitly ask for one. Task briefs live in this LEDGER § "Wave N task briefs" —
agents read them from there.

**Step 1 (slot 1 main runs, background, parallel)** — reset all 6 slots in one shot:

```bash
cd /home/hk/unified-trading-system-repos
for n in 2 3 4 6 7 9; do
  (
    find ".tabs/$n" -maxdepth 2 -name ".git" 2>/dev/null | while read g; do
      git -C "$(dirname $g)" checkout -- . 2>/dev/null
    done
    bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --reset-slot $n 2>&1 | grep -E "Resetting|complete|ERROR" | sed "s/^/[slot $n] /"
  ) &
done
wait
```

Swap the slot list `2 3 4 6 7 9` for whichever slots the operator wants to spawn this wave. The `git checkout -- .` step
silently discards any leftover uncommitted state from the prior agent (usually a STARTED ack — no real work lost). Reset
then rebases `tab/hk/N` cleanly onto `origin/live-defi-rollout`.

**Step 2 (operator opens N terminals)** — paste this lean prompt (swap `N`):

```
You are Harsh-side slot N. Pull origin/live-defi-rollout in unified-trading-pm, read harsh_orchestrator/LEDGER.md to find your Slot N task brief, then start working on it. If any owned repo in your worktree at /home/hk/unified-trading-system-repos/.tabs/N/ is behind LDR, fetch + rebase first. Follow harsh_orchestrator/AGENT_ONBOARDING.md for git discipline + ping mechanics + LDR-alignment HARD RULE.
```

That's it. No COMPACT-CYCLE GUARD lectures, no LDR-alignment explanations, no GREP-THEN-READ warnings inline — all that
lives in `AGENT_ONBOARDING.md` (universal mechanics) and the LEDGER task brief (per-slot specifics including model
tier + grep-then-read warnings on multi-callsite scopes).

**Step 3 (main monitors)** — agent reads LEDGER + plan-of-record + boots. If agent asks clarifying questions, the answer
is "the LEDGER brief is the SSOT — re-read it; if still unclear, ping `pings/slot_N.md`". Don't expand the prompt;
expand the LEDGER brief.

**Deviation only when operator explicitly says**: "give me a direct prompt for slot N" or "use a custom prompt for X
reason". Otherwise: default workflow.

---

## Main orchestrator — fresh boot (slot 1)

Fresh main-agent chat (context window died, new session):

1. `git -C /home/hk/unified-trading-system-repos/unified-trading-pm fetch origin --quiet && git -C /home/hk/unified-trading-system-repos/unified-trading-pm log --oneline -5 origin/live-defi-rollout`
   — see recent origin activity.
2. `cat harsh_orchestrator/pings/slot_{2..10}.md 2>/dev/null` — intra-side pings.
3. `cat plans/active/_agent_pings.md` — cross-side pings.
4. Read this LEDGER § "Current shift" table — note each slot's state; update any SPAWN PENDING → IN FLIGHT based on ping
   acks.
5. Ack to operator: "Main online. Slots in flight: N. Pings: M intra / K cross. Standing by."

---

## 🏁 Slot 9 Day-4 CYCLE-CLOSE — 2026-05-15 (harsh-slot-9)

**Theme**: MTDS DeFi handler hardening (eigenlayer phantom-safe pattern) + PBM Phase 8 coverage

### Shipped this session

| Item                                           | SHA             | Repo | Notes                                                                              |
| ---------------------------------------------- | --------------- | ---- | ---------------------------------------------------------------------------------- |
| lst_rates handler hardening                    | `f657431`       | mtds | record_captured inside try, record_failed in except — eigenlayer pattern           |
| evm_defi/gas_fee/solana_defi handler hardening | `3bca360`       | mtds | All 3 remaining handlers hardened; inner swallowing excepts removed; tests updated |
| PBM STEP 5.37 QG carve-outs                    | (prior session) | pbm  | `# noqa: qg-inline-threshold` on 4 simulation Decimal("1.5") values                |
| PBM transfer_reconciler broken import fix      | (prior session) | pbm  | `DeFiTransferRecord` → `TransferRecord` (module was unimportable)                  |
| DualFailureDetector unit tests                 | (prior session) | pbm  | 15 tests, full coverage                                                            |
| TransferReconciler unit tests                  | (prior session) | pbm  | 19 tests, full coverage                                                            |

### ALL 4 DeFi handlers now eigenlayer-safe

- `lst_rates_handler.py` ✅ `f657431`
- `evm_defi_handler.py` ✅ `3bca360`
- `gas_fee_handler.py` ✅ `3bca360`
- `solana_defi_handler.py` ✅ `3bca360`

### Remaining blocker

B-015 re-smoke still **HOLD** — pending Ikenna phantom-fix confirmation. Once Ikenna's slot confirms
`reconcile_phantom_manifest_rows_all.py --apply-flips` ran + green smoke, B-015 can re-launch with all 4 handlers
hardened.
