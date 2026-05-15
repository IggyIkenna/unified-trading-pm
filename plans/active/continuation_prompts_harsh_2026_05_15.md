---
title: Continuation prompts — Harsh side, 2026-05-15 Day-1
type: orchestration-spec
status: active
created: 2026-05-14
adopted: 2026-05-15 04:00 UTC
locked_by: live-defi-rollout
locked_since: 2026-05-14
---

# Continuation Prompts — Harsh side, 2026-05-15 Day-1

> **Status: ADOPTED 🟢** — operator authorized Lever 1+2 pattern @04:00 UTC. Slots execute their queue + self-pivot; auto-poll script tracks STARTED/DONE/BLOCKED; main only intervenes on BLOCKED/cross-side/BIG findings.
>
> **Day-1 deltas from yesterday EOD** (verified against overnight commits):
> - Slot 4 ✅ shipped B-006 (mtds@504bf34 + instruments@4063e08) overnight; queue updated below
> - Slot 5 ✅ shipped B-009 (risk@ac021a7 + execution@7de7385c) + Phase 3 TradFi migration overnight
> - Slot 7 ✅ shipped B-018 (36/36 repos snapshot live) + Wave 4 carry-forward overnight
> - Slot 8 ✅ shipped B-014 STEP 5.79-5.82 to base-service.sh + 13/15 service repos QG stub; **2 repos remain (features-service + others; full set preserved in `.tabs/8/<repo>/` stash list with msg `slot-8 B-014-ROLLOUT-COMPLETION`)**
> - Slot 9 🛑 STILL BLOCKED on B-015 — Ikenna posted update @02:00 UTC: smoke FAILED SILENTLY (phantom manifest skipped both VMs, ZERO data written); Ikenna slot 8 owns phantom-clear via `reconcile_phantom_manifest_rows_all.py --asset-group DEFI --apply-flips` then re-smoke; HOLD Phase 2 until Ikenna confirms phantom-fix DONE + green smoke
> - Slot 6 self-completed Cluster A+B follow-on + codex audit overnight
>
> See [`harsh_orchestrator/THEMATIC_CLUSTERS.md`](../../harsh_orchestrator/THEMATIC_CLUSTERS.md) for the stable theme map this draws from.
>
> **Companion docs**:
> - [`harsh_orchestrator/LEDGER.md`](../../harsh_orchestrator/LEDGER.md) § "End-of-shift summary 2026-05-14" — what shipped yesterday + open blockers
> - [`harsh_orchestrator/BACKLOG.md`](../../harsh_orchestrator/BACKLOG.md) — full dispatch queue with item details
> - [`plans/active/_agent_pings.md`](_agent_pings.md) — cross-side ping ledger

## How slots use this doc

1. Read **only your slot section** below.
2. Execute items in order. After each item DONE + pushed (commit on `live-defi-rollout`): ping DONE in your slot ping file with SHAs.
3. **Immediately start next item** in your queue — do NOT wait for main dispatch.
4. After your numbered queue is empty, pull from your "Reserve" list.
5. Ping main ONLY on: BLOCKED (genuine gap, ≥30 min investigation), cross-side coordination needed, BIG finding (data correctness / multi-repo).
6. EOD: write a brief "🏁 Slot N — Day-1 close" ping summarising what shipped + what's deferred.

## Tomorrow's main-orchestrator tasks (slot 1)

Before slots start, main does:
1. Run `bash scripts/agents/harsh_auto_poll.sh --dry-run` once to verify the auto-poll script reads state correctly.
2. Schedule auto-poll via cron OR run `--watch` in a tmux pane.
3. Triage 2 open cross-side blockers from yesterday EOD:
   - **B-016 (slot 3) Ikenna ACK** — check `plans/active/_agent_pings.md` for response
   - **B-015 (slot 9) BLOCKED** — DeFi features pipeline gap + MTDS lst_rates stale; operator decision on resolution path
4. Verify B-014 rollout (slot 8) completed cleanly; flip BACKLOG status if DONE.
5. Run `regenerate_active_plan_inventory.py`.
6. Drop ONE "Day-1 START" ping per slot pointing to their section here. Then stand back.

---

## Slot 2 — Deployment Infra & Lint Sweep

**Theme** (per `THEMATIC_CLUSTERS.md`): deployment-service VM infra + lint sweeps
**Status at start of Day-1**: B-011 DONE ✅ (deployment-service@cf6bb83 yesterday). Standing by.

### Day-1 queue

1. **VM_PREFIX_TO_BUCKET watchdog blindspot audit** — yesterday's B-011 work flagged 8 known blindspot prefixes. Investigate each: (a) is the VM type still active? (b) which bucket should map? (c) file fix per-prefix or batched. Done-def: `vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET` dict updated; relaunch watchdog VM per CLAUDE.md (`deployment-service/scripts/vm/vm_zombie_watchdog.py` SSOT).
2. **Codex audit on deployment-and-qg-strategy.md** — Phase 8.A surfaces shipped yesterday should be reflected in codex. Verify `codex/05-infrastructure/deployment-and-qg-strategy.md` + `codex/05-infrastructure/vm-tarball-deployment.md` reflect: new VM_PREFIX entries, B-018 cron VM pattern, Phase 8.A coverage targets. Done-def: codex doc updated OR confirmed already current.
3. **alerting-service codex violations follow-up** — issue doc `plans/active/issues/alerting_service_codex_violations_d5_d7_2026_05_14.md` filed yesterday by slot 6. If still open: triage + fix or escalate to operator.

### Reserve queue

- Cross-repo shellcheck sweep on launchers in deployment-service/scripts/vm/ (any not yet covered by B-011 tests)
- ml-training-service ARIMA / catboost backfill QG cleanup
- deployment-service VM launcher template consolidation (DRY common patterns)

### Coordination

- deployment-service overlap with slot 7 (Phase 4 cron VM) — coordinate file-level
- DO NOT touch `deployment-service/scripts/base-service.sh` template — that's slot 8's B-014 work in flight

---

## Slot 3 — Strategy Service & DeFi Paper Backtests

**Theme**: archetype coverage + DeFi paper backtests (APD half)
**Status at start of Day-1**: B-010 DONE ✅, B-016 Phase 1 BLOCKED on Ikenna ACK (cross-side ping filed @~15:30 UTC 2026-05-14). Phase 3 P&L report template drafted.

### Day-1 queue

1. **Check Ikenna ACK on B-016 cross-side ping** — read `plans/active/_agent_pings.md` tail. If Ikenna acked: proceed to item 2. If still waiting: proceed to item 3 (parallel work). If Ikenna escalated: re-read their response + adjust.
2. **(IF Ikenna ACK landed) B-016 Phase 2 launch** — run colocated_engine paper mode for arbitrage_price_dispersion. Capture VM name + correlation_id. Ping STARTED-Phase-2 immediately on VM launch. Phase 3 is autonomous 30-day monitor (survives session shutdown).
3. **strategy-service execution alpha smoke test extensions** — yesterday slot 3 added execution alpha smoke tests (`strategy-service@fc634e3`). Extend coverage: add scenarios for (a) APD multi-venue slippage, (b) carry archetype hedge leg fill simulation, (c) edge cases (zero-volume venue, paused leagues). Done-def: 5+ new scenarios; QG green.
4. **archetype_slot_resolver test coverage** — yesterday's alias fix (strategy-service@0ca3fac) shipped without tests. Add unit tests: (a) `archetype_slot_resolver.resolve("arbitrage_price_dispersion")` returns slot ID; (b) `resolve("APD")` (uppercase alias) returns same; (c) unknown string raises with helpful error. Done-def: tests added + QG green.

### Reserve queue

- batch_live symmetry strategy-service items (any remaining from Tab 3)
- V2BatchHarness GCS mock conftest extensions (yesterday's @8e478de baseline; can extend)
- DeFi paper backtest report template refinement (`e2e-testing/reports/defi_paper_runs/`)

### Coordination

- Pair with slot 9 on cross-side DeFi prereqs — shared start_date + venue confirmations
- strategy-service overlaps with slot 4 (general tests) — coordinate file-level

---

## Slot 4 — Test Failures Absorption & Service Lifecycle Coverage

**Theme**: Phase 0 test failure absorption + ServiceBootstrap lifecycle coverage
**Status at start of Day-1**: B-006 DONE ✅ (mtds + instruments lifecycle tests). ml-inference Phase 0 DONE ✅.

### Day-1 queue

1. **B-006 extension — features-service ServiceBootstrap** — yesterday's note: "features-service top-level is a pure dispatcher (no ServiceBootstrap), per-family CLIs have it + static scan tests verify markers". Verify: does each per-family CLI (delta_one, volatility, sports, etc.) have lifecycle test coverage? If any family CLI is missing, add it. Done-def: every per-family CLI in features-service has STARTED/STOPPED/FAILED test OR a documented exemption with rationale.
2. **B-006 verification — risk + execution lifecycle re-validation** — yesterday's claim: "execution + risk already had full lifecycle tests". Verify by reading: `risk-and-exposure-service/tests/unit/test_lifecycle_events.py` (or equivalent) + `execution-service/tests/unit/test_lifecycle_events.py`. Confirm coverage matches B-006 spec. If gaps, fix.
3. **ml-inference-service Phase 6.6 emission policy coverage extensions** — yesterday's `b43da70 fix(qg): ml-inference-service` got QG green. Look for coverage gaps in `publish_with_policy` per-strategy-signal path. Add tests for: WARN_ONLY, NAN_FILL, STRICT_FAIL policy outcomes for ml-inference. Done-def: ml-inference-service coverage ≥ pre-existing + new lines covered.

### Reserve queue

- Cross-repo test diagnostic backlog (any remaining pre-existing failures filed as issue docs)
- features-service Phase 6 emission policy parity check (delta_one + cross_instrument + onchain)
- instruments-service test extensions on Phase 3 migration script

### Coordination

- execution-service overlap with slot 5 (kill switch) + slot 6 (custody) — coordinate file-level
- features-service overlap with slot 9 (peripheral) — usually distinct concerns

---

## Slot 5 — Risk Engine + Execution Alpha + Kill-Switch

**Theme**: risk + execution coverage + kill switch + circuit breaker
**Status at start of Day-1**: B-009 DONE ✅ (risk@ac021a7 + execution@7de7385c). Phase 3 TradFi migration shipped (instruments@db070da + @e1ca983).

### Day-1 queue

1. **B-009 extension — UTL 3-tier kill-switch coverage** — yesterday's DONE ping noted "DEFERRED: UTL 3-tier coverage is separate scope". Ship that now: add tests in `unified-trading-library/tests/` for the 3-tier kill switch helpers (if separate from service-side). Done-def: UTL QG green + coverage target met.
2. **pnl-attribution-service Cluster B follow-up audit** — slot 6 shipped pnl-attribution-service@9f3379f yesterday (C901 noqa + extract). Verify QG green + audit for any remaining Cluster B items. If clean: stand down on this item.
3. **Phase 6.7 risk_state BLOCK_CRITICAL gate coverage** — risk-and-exposure-service@df4849f shipped earlier this week. Add coverage tests: (a) state transitions trigger BLOCK_CRITICAL, (b) emission policy STRICT_FAIL fires correctly, (c) deactivation re-arms. Done-def: BLOCK_CRITICAL paths 100% covered.

### Reserve queue

- execution-service DeFi error classification taxonomy (13 DefiErrorCode entries — slot 6 mentioned as optional in their Final Wave; pick up if they didn't)
- pnl-attribution-service ARBITRAGE_PRICE_DISPERSION archetype bucket extensions (slot earlier added; may need test extensions)
- deployment-api SHARD_AXIS_MATRIX drift (if not closed by Ikenna slot 8)

### Coordination

- execution-service overlap with slot 4 (lifecycle) + slot 6 (custody) — coordinate file-level
- Phase 6.7 work overlaps with slot 8 (UTL emission publisher coverage)

---

## Slot 6 — Custody, Signing, UTL Coverage, Codex Audits

**Theme**: execution-service custody + UTL helpers + codex audits
**Status at start of Day-1**: B-012 DONE ✅ + Cluster A+B follow-on DONE ✅ + B-012 codex audit DONE ✅ (yesterday's full close-out).

### Day-1 queue

1. **codex audit — verify execution-service custody patterns are documented** — yesterday's codex audit was on `codex/04-architecture/custody-providers.md` + `interface-credential-convention.md`. Extend: verify `codex/04-architecture/flash-loan-receiver.md` + DeFi error classification taxonomy in codex are current vs shipped code. Done-def: codex docs reflect current code OR gaps filed as TODO.
2. **DeFi error classification coverage extension** — if slot 5 didn't take this from reserve: 13 DefiErrorCode entries (`unified_api_contracts.canonical.crosscutting.errors.defi`). Verify each has test coverage in execution-service consumers (aave.py, etc.). Done-def: each DefiErrorCode has a test exercising FAIL/RETRY/SKIP routing.
3. **UTL legacy_reason_classifier extension** — yesterday's UTL work shipped `e75bb0d` (PLAYER_VALUES cadence). Audit: are all `EmptyConfirmedReason` taxonomy entries handled in legacy_reason_classifier? Done-def: every reason in the enum has classifier coverage.

### Reserve queue

- UAC ×→x cleanup (if any new RUF003 occurrences crept in — slot 6 shipped UAC@046f9d6 for 2 remaining yesterday)
- codex/06-coding-standards/ doc currency (any new pattern from Phase 8 work)
- UTL test coverage for new helpers (signing helpers if not at parity with execution-service custody)

### Coordination

- execution-service overlap with slot 4 + slot 5 — coordinate file-level
- UAC overlap with Ikenna side primary — check `_agent_pings.md` before touching UAC

---

## Slot 7 — Deployment API + UI + Phase 4 Cron Infra

**Theme**: deploy-readiness + Phase 4 snapshot infra
**Status at start of Day-1**: B-018 DONE ✅ (Phase 4.A snapshot writer + cron VM live; 36/36 repos in `quality_gates_snapshot/`). B-013 deploy-ready endpoint live.

### Day-1 queue

1. **B-018 Phase 4.A monitoring + alerting** — yesterday's B-018 shipped cron VM + Cloud Scheduler. Add: (a) alerting hook if snapshot.sh fails for N consecutive days (alerting-service integration); (b) UI badge on deployment-ui showing "last snapshot age" per repo. Done-def: alerting fires on snapshot stale, UI badge live.
2. **Phase 4.B downstream items** — deployment-and-qg-strategy plan Phase 4.B (anything downstream of 4.A snapshot writer). Check plan for unflipped checkboxes. Done-def: Phase 4.B items shipped OR explicit DEFERRED annotation.
3. **deployment-api SHARD_AXIS_MATRIX drift coverage** — slot 7 worked it `40f7769` yesterday. Verify tests + ensure consumers aligned. Done-def: 13 failing tests now pass; cross-side issue doc `deployment_api_shard_axis_matrix_uac_drift_2026_05_14` closed.

### Reserve queue

- deployment-ui vitest coverage extensions
- client-reporting-api coverage (if backfill data lands)
- Cloud Scheduler trigger SSOT consolidation (any drift between deployment-service/scripts/vm and PM scripts)

### Coordination

- deployment-service overlap with slot 2 (VM infra) — coordinate launcher file-level
- deployment-api/ui pair — almost always yours; if slot 5 needs deployment-api touch (env-locking), coordinate

---

## Slot 8 — UTL Coverage + QG Ratchet Rollout + Meta-QG

**Theme**: UTL + base-service.sh + STEP rollouts
**Status at start of Day-1**: B-007+B-008 DONE ✅. B-014 rollout in flight (4 service repos got QG stub yesterday). Maybe completed overnight.

### Day-1 queue

1. **B-014 rollout completion verification** — yesterday's rollout touched execution + deployment-api + deployment-service + e2e-testing. Verify: (a) all remaining service repos (~16 not yet touched) have the QG stub propagated; (b) QG green across ALL repos with new STEPs; (c) plan Phase 3 checkbox flipped. Done-def: full rollout complete OR specific repos called out as deferred with reason.
2. **codex_vs_citadel audit follow-up** — Ikenna slot 8 originally owned this; verify Harsh-side surfaces are covered (UTL, deployment-service template, anything Harsh owns). If anything's stale, update or file issue doc.
3. **UTL emission publisher coverage edge cases** — yesterday's B-008 hit 100% on `emission_publisher.py`. Audit related modules: `publish_with_policy` callsites across services — are all consumer-side patterns tested? Done-def: any consumer-side gap filed as issue OR fixed.

### Reserve queue

- codex/06-coding-standards/quality-gates.md updates (new STEP additions if any from B-014)
- batch_live_symmetry follow-on (L4/L5/L6 sweeps if Ikenna slot 5 punted)
- base-service.sh template DRY (any common patterns across QG steps that could be helpers)

### Coordination

- B-014 rollout touches every service repo — be careful of in-flight work from other slots; coordinate via ping ledger
- UTL overlap with slot 4 (test utils) + slot 6 (helpers) — coordinate file-level

---

## Slot 9 — MTDS + PBM + DeFi Carry Backtest

**Theme**: MTDS + PBM + DeFi carry paper backtest (B-015 half)
**Status at start of Day-1**: 🛑 BLOCKED on B-015 (DeFi features pipeline gap + MTDS lst_rates stale; operator decision pending).

### Day-1 queue

1. **B-015 BLOCKED — wait for operator/Ikenna decision** — read `plans/active/_agent_pings.md` for response to your 13:10 UTC BLOCKED ping. THREE possible paths:
   - **(Path A — fix upstream)** Operator/Ikenna assigns DeFi features pipeline + MTDS lst_rates fix to slots. You stand by until those land, then re-run Phase 1.
   - **(Path B — scope-down)** Operator authorizes paper-launch with stale data OR with subset of features. Adjust B-015 launch config + proceed to Phase 2 launch.
   - **(Path C — defer)** Operator defers B-015 to post-fix cycle. You pivot to item 2.
2. **(IF Path C OR while waiting for Path A/B)** MTDS UAC facade migration follow-up — yesterday's `mtds@1b62d0f` + `@05aaeaa` shipped UAC facade migration. Audit: any remaining deep imports? Done-def: MTDS QG green + no deep-imports.
3. **MTDS Solana handler — Helius RPC integration verification** — `mtds@05b705a` shipped Helius wiring yesterday (Task 3). Add tests: (a) Helius adapter happy-path, (b) rate-limit handling, (c) fallback to alternative provider. Done-def: Helius integration tested + QG green.

### Reserve queue

- PBM Phase 8 coverage extensions
- MTDS handler additions for new venues (post-Solana plan progression)
- DeFi data-pipeline gap reporting (you're the natural slot for this — keep monitoring)

### Coordination

- B-015 directly paired with slot 3's B-016 — share cross-side prereq content
- MTDS overlap with slot 4 (test failures) — coordinate if slot 4 picks up MTDS items

---

## EOD pattern

At end of each session:
1. Each slot writes a "🏁 Slot N Day-N close" ping summarising:
   - Items shipped from queue (with SHAs)
   - Items deferred (with reason)
   - Items pulled from reserve
   - Open BLOCKED if any
2. Main reviews all 8 EOD pings in ~10 min.
3. Main writes ONE EOD scoreboard block in LEDGER (mirrors Ikenna pattern).
4. Auto-poll continues overnight to catch any late commits.

## Adoption checklist (operator pre-adoption)

- [ ] Review THEMATIC_CLUSTERS.md — slot theme assignments match expectation
- [ ] Review this continuation_prompts doc — items make sense vs current BACKLOG state
- [ ] Test `bash scripts/agents/harsh_auto_poll.sh --dry-run` works
- [ ] Set up cron OR tmux pane for `--watch` mode
- [ ] Drop ONE Day-1 START ping per slot pointing to their section here
- [ ] Stand back and let slots self-pivot
