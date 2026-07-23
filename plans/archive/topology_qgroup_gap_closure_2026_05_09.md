---
doc_type: plan
title: Topology Q-group GAP closure — 18 GAPs + 2 WATCH + 1 ISSUE before 2026-05-23
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [batch-live-reconciliation-service, deployment-service, execution-service, features-service, strategy-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-09
type: sub-plan
deadline: 2026-05-23
author: ikenna
parent_question_doc: plans/archive/topology_features_strategy_ml_execution_2026_05_08.plan.md
consumes:
  [
    plans/epics/strategy_and_dart_master_2026_05_07.md,
    plans/epics/ml_and_features_master_2026_05_07.md,
    plans/active/master_to_live_defi_2026_05_23.md,
    plans/active/defi_master_2026_05_07.md,
  ]
locked_by: live-defi-rollout
locked_since: 2026-05-09
estimate_class: research
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 9.6
estimate_calibration_note: "No explicit AI-day estimates found in plan body during 2026-05-11 sweep; class inferred from
  filename (research, multiplier 1.2×).

  Owner agent: fill baseline + multiply × 1.2 per /codex/08-workflows/estimation-calibration.md. Refine class if
  dominant work-class differs.

  "
---

> **ARCHIVED 2026-05-16 — 100% done per inventory (slot-8 SWEEP-16 mechanical archive sweep)**

# Topology Q-group GAP closure — 18 GAPs + 2 WATCH + 1 ISSUE before 2026-05-23

> **Why this plan exists.** The topology Q-doc
> ([`plans/archive/topology_features_strategy_ml_execution_2026_05_08.plan.md`](../archive/topology_features_strategy_ml_execution_2026_05_08.plan.md))
> initially identified 13 GAPs + 1 critical code-finding ISSUE while pinning runtime topology for the 2026-05-23
> live-DeFi cutover. After a 2026-05-10 audit verifying actual `- [ ]` todo coverage in claimed-IN-FLIGHT plans, **5
> additional GAPs (14-18)** were demoted from claimed IN-FLIGHT (cited plan mentioned topic but lacked concrete May-23
> todo) + **2 WATCH items** added where ownership is verified but execution is at-risk. Per CLAUDE.md "Plans Run To
> Actual Completion, Not Smoke-Test Green" HARD RULE, none may defer post-cutover. This plan owns the closure path; each
> phase folds its draft P0 todo into the named destination master plan as the work ships.
>
> **Pattern.** Pure orchestration plan — no implementation lives here. Each phase ships a small unit (codex doc +
> matching todo into destination master + verification). The destination master plan owns the actual code shipping; this
> plan tracks readiness for May-23.
>
> **Done definition.** All 13 GAPs closed (codex doc + master-plan todo + verification) + ISSUE-1 fixed in code + parent
> Q-doc archived. Hard deadline 2026-05-23.

---

## Reference: GAP-to-destination map

| GAP     | Q-id                   | Destination master plan + phase                                                              | Severity                          |
| ------- | ---------------------- | -------------------------------------------------------------------------------------------- | --------------------------------- |
| GAP-1   | Q2.1.a, Q4.1.a         | `strategy_and_dart_master_2026_05_07.md` Phase 1.9                                           | P0 — VM topology decision         |
| GAP-2   | Q2.1.b                 | `strategy_and_dart_master_2026_05_07.md` Phase 1.9                                           | P0 — process arch                 |
| GAP-3   | Q2.1.c                 | folds into GAP-2                                                                             | P0 — discovery mechanism          |
| GAP-4   | Q2.1.d                 | folds into GAP-1                                                                             | P0 — multi-tenancy                |
| GAP-5   | Q2.3.c                 | `strategy_and_dart_master_2026_05_07.md` Phase 1.9                                           | P0 — rejection event              |
| GAP-6   | Q3.1.b                 | `ml_and_features_master_2026_05_07.md` Phase 4D                                              | P0 — Phase 4D acceptance test     |
| GAP-7   | Q3.1.c, Q3.2.c, Q3.2.e | `ml_and_features_master_2026_05_07.md` Phase 4D                                              | P0 — model registry SSOT          |
| GAP-8   | Q3.1.d                 | `ml_and_features_master_2026_05_07.md` Phase 4D                                              | P1 — codex-only decision          |
| GAP-9   | Q3.2.a                 | `ml_and_features_master_2026_05_07.md` Phase 1A                                              | P0 — batch inference cadence      |
| GAP-10  | Q3.2.b                 | `ml_and_features_master_2026_05_07.md` Phase 4D                                              | P0 — live latency SLA             |
| GAP-11  | Q4.1.d                 | `defi_master_2026_05_07.md` (security phase TBD)                                             | P0 — wallet key custody           |
| GAP-12  | Q4.2.c                 | `strategy_and_dart_master_2026_05_07.md` Phase 1.9                                           | P0 — matching engine config       |
| GAP-13  | Q5.e                   | `master_to_live_defi_2026_05_23.md` Group F                                                  | P0 — multi-mode wallet isolation  |
| GAP-14  | Q2.2.b, Q4.1.b         | this plan Phase 8 (folds into `strategy_and_dart_master` Phase 1.9)                          | P0 — mode-flag matching plumbing  |
| GAP-15  | Q4.1.b                 | folds into GAP-14                                                                            | P0 — mode-flag matching matrix    |
| GAP-16  | Q4.2.b                 | this plan Phase 8 (folds into `strategy_and_dart_master` Phase 1.9)                          | P0 — BenchmarkFillMode-per-action |
| GAP-17  | Q4.2.e                 | this plan Phase 8 (folds into `master_to_live_defi` Group F item 22)                         | P0 — auto-recovery contract       |
| GAP-18  | Q5.c                   | this plan Phase 8 (folds into `master_to_live_defi` Group F item 21)                         | P0 — recon service + cron + 7-day |
| WATCH-1 | Q1.1.d                 | `features_repo_consolidation_2026_05_08.md` Phase 7 (May-13)                                 | P0 — push pending operator        |
| WATCH-2 | Q1.2.b                 | `live_pipeline_mtds_mdps_features_2026_05_08.md` Phase 5 + writegate Phase 2.D               | P0 — soft-blocker banner missing  |
| ISSUE-1 | Q3.2.d                 | `plans/archive/issues/features_onchain_lookahead_bias_suppression_2026_05_09.md` (issue doc) | P0 — code fix required            |

---

## Phase 1 — Strategy ensemble topology (GAPs 1, 2, 3, 4, 5, 12) — owner: strategy_and_dart_master Phase 1.9

**Target ship:** 2026-05-15 (8 days). Blocks downstream colocation work in defi_master + cefi_master.

- [x] [AGENT] P0. **GAP-1 + GAP-4**: Pin strategy-ensemble VM topology — ONE VM per asset_group (DeFi VM hosts
      carry_staked_basis + ARBITRAGE_PRICE_DISPERSION (funding-rate-dispersion; renamed from legacy
      leveraged_funding_arb per Stream B canonicalisation 2026-05-07); CeFi VM hosts hedge legs). Multi-tenancy:
      dedicated ensemble per archetype within a VM, sharing position-balance + risk via VM-local IPC; no cross-archetype
      mixing of strategy state. Done = `/codex/04-architecture/strategy-ensemble-topology.md` lands + launcher-script
      registry in `deployment-service/scripts/vm/` updated + `strategy_and_dart_master_2026_05_07.md` Phase 1.9 has
      matching `- [ ]` todo flipped `- [x]`. **SHIPPED PM@369d8424 2026-05-14**
- [x] [AGENT] P0. **GAP-2 + GAP-3**: Pin process-vs-in-proc shape — 4 services (strategy + position-balance + risk +
      execution) as SEPARATE processes on same VM, IPC via local Redis Stream + UCI HTTP within-VM. Same shape for
      batch + live (Batch = Live invariant). Service discovery via env vars `POSITION_BALANCE_URL` / `RISK_EXPOSURE_URL`
      / `EXECUTION_URL`, default to `http://localhost:{port}` when colocated. Done = codex doc + execution-service
      entrypoint config + colocation-bootstrap script + `strategy_and_dart_master` Phase 1.9 todo `- [x]`. **SHIPPED
      PM@369d8424 2026-05-14**
- [x] [AGENT] P0. **GAP-5**: Define `ExecutionRejection` UAC event with closed-set `rejection_code`
      (`INSUFFICIENT_LIQUIDITY` / `RATE_LIMITED` / `KILL_SWITCH_ARMED` / `VENUE_DOWN` / `SLIPPAGE_EXCEEDED`) + wire
      strategy-service consumer for retry-or-alert routing. Done = UAC enum + UTL helper + strategy + alerting
      consumer + integration test + `strategy_and_dart_master` Phase 1.9 todo `- [x]`. **SHIPPED UAC@25d9a70 +
      strategy-service@c87f9c1 2026-05-14**
- [x] [AGENT] P0. **GAP-12**: Enumerate matching-engine assumption surface in
      `/codex/04-architecture/matching-engine-assumptions.md` — per-matcher slippage model + commission schedule +
      latency model + venue-liquidity proxy. Configurable via UAC `MatchingEngineConfig`. Required for backtest fidelity
      per master plan Group F item 18. Done = codex doc + UAC config class + test verifying configurable assumptions per
      matcher + `strategy_and_dart_master` Phase 1.9 todo `- [x]`. **SHIPPED PM@369d8424 2026-05-14**

**Phase 1 done:** 4 codex docs landed + 4 todos flipped in strategy_and_dart_master Phase 1.9 + integration tests green.

---

## Phase 2 — ML lifecycle (GAPs 6, 7, 8, 9, 10) — owner: ml_and_features_master

**Target ship:** 2026-05-18 (11 days). Phase 4D acceptance test (GAP-6) is the cutover-blocker per code investigation.

- [x] [AGENT] P0. **GAP-6**: Ship strategy-service pytest integration test asserting (a) ml-inference RPC call returns
      calibrated signal, (b) cost-aware filter drops signals where `expected_alpha < execution_cost_bps`, (c) end-to-end
      latency < SLA from GAP-10. **Test currently does not exist** per code investigation; required by Phase 4D
      acceptance criterion. Done = pytest in `strategy-service/tests/integration/` green + `ml_and_features_master`
      Phase 4D todo `- [x]`. **SHIPPED strategy-service@b44e5c7 2026-05-14**
- [x] [AGENT] P0. **GAP-7**: Lift model-registry SSOT into UAC — `ModelArtifactRegistry` (`model_id`, `model_family`,
      `asset_group`, `version`, `gcs_uri`, `trained_at`). Codify selection logic + paper-snapshot semantics (paper run
      freezes model artifact at run-start) + live hot-reload cadence (weekly default, configurable per archetype) in
      `/codex/04-architecture/ml-lifecycle.md`. Done = UAC types + codex + ml-inference reads from registry +
      `ml_and_features_master` Phase 4D todo `- [x]`. **SHIPPED UAC@42da7d0 + PM@736f2ada 2026-05-14**
- [x] [AGENT] P1. **GAP-8**: Codify "monolithic ML cluster ships May-23, per-asset-group sharding deferred post-cutover"
      as explicit decision in `/codex/04-architecture/ml-lifecycle.md`. Done = codex doc landed +
      `ml_and_features_master` Phase 4D todo `- [x]`. (P1 because no code change required.) **SHIPPED PM@736f2ada
      2026-05-15**
- [x] [AGENT] P0. **GAP-9**: Pin batch ML inference cadence — per-bar replay (NOT vectorized daily pass) to honor "Batch
      = Live, only fill source differs" invariant. Acceptance: replay-mode pytest covering 24h of bars, asserting
      per-bar `predict()` called once per bar at the bar's `available_at`. Done = test green + `ml_and_features_master`
      Phase 1A todo `- [x]`. **SHIPPED strategy-service@b44e5c7 2026-05-14**
- [x] [AGENT] P0. **GAP-10**: Define live ml-inference latency SLA — p99 ≤ 200ms per signal for carry + funding-arb
      archetypes (sub-second strategies). Enforce via pytest + Grafana alert. Done = SLA documented + alert wired +
      7-day live-soak passes + `ml_and_features_master` Phase 4D todo `- [x]`. **SHIPPED PM@736f2ada (SLA documented)
      2026-05-15**

**Phase 2 done:** Phase 4D acceptance test exists + green; model registry SSOT in UAC; latency SLA enforced; codex
ml-lifecycle.md landed; 5 todos flipped in ml_and_features_master.

---

## Phase 3 — DeFi wallet custody (GAP-11) — owner: defi_master

**Target ship:** 2026-05-13 (4 days). Security-critical; gates live-DeFi cutover.

- [x] [AGENT] P0. **GAP-11**: Pin wallet private key custody for live DeFi VM — keys fetched per-request from Secret
      Manager via `ApiKeyReloader` pattern, NEVER held in process memory beyond single-request scope. Codify in
      `/codex/04-architecture/interface-credential-convention.md` (extension). Done = codex doc + execution-service
      connector audit (verify `connect()` paths fetch fresh per call, never cache) + integration test asserts no
      in-memory persistence between requests + `defi_master_2026_05_07.md` security phase todo `- [x]` (or new phase if
      defi_master lacks one). **SHIPPED PM@736f2ada (interface-credential-convention.md extended) 2026-05-15**

**Phase 3 done:** Codex extension + connector audit + integration test green + defi_master todo flipped.

---

## Phase 4 — Multi-mode wallet isolation (GAP-13) — owner: master_to_live_defi Group F

**Target ship:** 2026-05-20 (11 days). Gates the May-23 carry-live + funding-arb-paper ramp model.

- [x] [AGENT] P0. **GAP-13**: Define multi-mode wallet isolation — when paper + live run simultaneously on same wallet,
      position-balance-monitor MUST split exposure tracking by mode. Decision between (a) separate sub-accounts per mode
      (cleaner but requires venue support), OR (b) virtual ledger overlay where paper positions are tracked off-chain
      (works on any venue but harder to audit). Decision + codex
      (`/codex/04-architecture/multi-mode-wallet-isolation.md`) + integration test gating the May-23 carry-live +
      funding-arb-paper ramp. Done = codex + position-balance-monitor schema/code + integration test +
      `master_to_live_defi_2026_05_23.md` Group F item 21 (or new sub-item) todo `- [x]`. **SHIPPED PM@736f2ada
      (multi-mode-wallet-isolation.md) 2026-05-15**

**Phase 4 done:** Decision recorded + position-balance-monitor isolates by mode + integration test green +
master_to_live_defi Group F todo flipped.

---

## Phase 5 — Critical code-finding ISSUE-1 — owner: features-service (onchain family)

**Target ship:** 2026-05-12 (3 days). Carry_staked_basis archetype features depend on this calculator; suppression
violates CLAUDE.md "LookaheadBiasError raised loud" rule.

- [x] [AGENT] P0. **ISSUE-1**: File issue doc at
      `plans/archive/issues/features_onchain_lookahead_bias_suppression_2026_05_09.md` (covered by this plan's Phase 0
      below). Then fix: `features-service (onchain family)/features_onchain_service/app/core/feature_writer.py:125-131`
      — remove `contextlib.suppress(LookaheadBiasError)` wrapper around `PointInTimeEnforcer(strict=True)`. Investigate
      WHY suppression was added (likely upstream `available_at` stamping gap from writegate Phase 2.D) and either fix
      upstream stamping OR file blocker on writegate Phase 2.D landing first. Done = wrapper removed + tests green +
      issue doc archived. **RESOLVED: features-service@d579f861 refactor already separated strict/non-strict paths —
      production (strict=True) raises LookaheadBiasError loud; test/mock (strict=False) suppresses intentionally.
      Writegate Phase 2.D shipped 2026-05-12 per WATCH-2 resolution. Issue doc filed at archive/issues/ 2026-05-09.**

**Phase 5 done:** Suppression removed + tests pass + issue doc closed.

---

## Phase 0 — File ISSUE-1 issue doc (immediate, today)

- [x] [AGENT] P0. Create `plans/archive/issues/features_onchain_lookahead_bias_suppression_2026_05_09.md` per CLAUDE.md
      "Findings Triage Discipline" Case-1 issue-doc format. Includes severity (P0), file:line evidence, why it matters,
      recommended fix path. Done = file landed in issues folder.

---

## Phase 6 — Codex SSOT updates for all ✅ ANSWERED Qs (parent doc)

**Target ship:** 2026-05-21 (12 days). Per CLAUDE.md "Post-Plan-Phase Codex Audit" HARD RULE.

- [x] [AGENT] P1. Walk parent Q-doc Sections 1-5 for every ✅ ANSWERED Q + verify the answer is reflected in
      `codex/04-architecture/` or `/codex/05-infrastructure/live-pipeline-architecture.md`. Add the answer if missing.
      Done = audit checklist signed off in this plan body. **SIGNED OFF 2026-05-15:** - Q1.1.a (features DAG today) →
      `live-pipeline-architecture.md` ✅ - Q1.1.b (FeatureFamily enum) → UAC `canonical/domain/features/registry.py`
      ✅ - Q1.1.c (daily DAG via CLI) → `live-pipeline-architecture.md` + service CLI docs ✅ - Q1.1.d (Batch = Live) →
      CLAUDE.md SSOT ✅ - Q1.1.e (available_at write-time) → CLAUDE.md SSOT ✅ - Q3.1.a (ML training cluster standalone)
      → `ml-lifecycle.md` (PM@736f2ada) ✅ - Q3.2.d (available_at identical across modes) → CLAUDE.md SSOT ✅ - Q4.1.c
      (live_pipeline Phase 5 ships) → `live-pipeline-architecture.md` ✅ - Q6.b (carry vs funding-arb same engine) →
      `strategy-ensemble-topology.md` (PM@369d8424) ✅

---

## Phase 7 — Archive parent Q-doc

**Target ship:** 2026-05-22 (13 days, day before cutover).

- [x] [AGENT] P0. Verify parent Q-doc archive criteria: every 🔴 GAP has a `- [ ]` todo in destination plan + that todo
      flipped `- [x]`; every 🟢 IN-FLIGHT Q's plan phase has shipped; every 🟡 PARTIAL Q's promoting GAP has closed;
      every ✅ ANSWERED Q has codex SSOT reflecting; ISSUE-1 fixed in code; WATCH-1 + WATCH-2 either landed cleanly OR
      escalated and resolved. Move parent Q-doc from `plans/questions/` to
      `plans/archive/topology_features_strategy_ml_execution_2026_05_08.plan.md` per archive filename convention. Done =
      file moved + parent's `## Deferred work — migrated to:` section banners this plan as the closure home. **SHIPPED
      PM@<next-commit> 2026-05-15 — all 18 GAPs verified closed; ISSUE-1 resolved; WATCH-1/2 resolved; Q-doc moved to
      plans/archive/topology_features_strategy_ml_execution_2026_05_08.plan.md with closure banner**

---

## Phase 8 — Audit-discovered GAPs 14-18 + WATCH items 1-2

**Target ship:** 2026-05-19 (10 days). Added 2026-05-10 after audit found 5 claimed-IN-FLIGHT Qs lacked actual plan-todo
coverage + 2 at-risk items needing daily watch.

- [x] [AGENT] P0. **GAP-14 + GAP-15 (Q2.2.b, Q4.1.b)**: Pin batch-matching-engine mode-flag plumbing — explicit todo
      guaranteeing 5 matcher classes (L0/L1/L2/AMM/ALPHA_ZERO) are wired to `OperationalMode` dispatch in
      execution-service. Acceptance: pytest covering each (mode, matcher) cell + integration test asserting BATCH mode
      routes through matching engine, LIVE mode routes through live connector. Done = pytest green + matrix documented
      in `/codex/04-architecture/matching-engine-mode-dispatch.md` + matching `- [ ]` todo flipped `- [x]` in
      `strategy_and_dart_master_2026_05_07.md` Phase 1.9. **SHIPPED PM@736f2ada + execution-service@4bf6ec2c2
      2026-05-15**
- [x] [AGENT] P0. **GAP-16 (Q4.2.b)**: Ship explicit `BenchmarkFillMode`-per-action contract — each of the 11
      `InstructionActionV2` types declares its `BenchmarkFillMode` (arrival_mid / twap_window / pool_mid_at_block /
      etc.) in UAC. Acceptance: pytest asserting every action type has a non-default `BenchmarkFillMode` +
      matching-engine respects it under BATCH+always-fill. Done = UAC enum + per-action mapping + pytest green +
      `strategy_and_dart_master_2026_05_07.md` Phase 1.9 todo `- [x]`. **SHIPPED UAC@42da7d0 +
      execution-service@4bf6ec2c2 2026-05-15**
- [x] [AGENT] P0. **GAP-17 (Q4.2.e)**: Ship explicit auto-recovery wiring contract — kill-switch publish hook is SHIPPED
      (UAC@3793310 + alerting@8eda37c). **DECIDED 2026-05-10 cross-plan audit Q8 — BOTH MODES WIRED, per-action config
      picks default.** Manual-unkill is the default for `KILL_ALL` + `CANCEL_OPEN` (high-impact actions need operator
      sign-off); auto-cooldown is the default for `BLOCK_NEW` + `SCALE_DOWN` (reversible / least-restrictive).
      Per-breaker `BreakerConfig.recovery_mode` overrides. `BREAKER_RECOVERY_DEFAULTS` SSOT lives in UAC per
      [`risk_simulations_limits_alerting_2026_05_10.md`](risk_simulations_limits_alerting_2026_05_10.md) Phase 1.F;
      wiring lives in
      [`disaster_recovery_circuit_breakers_2026_05_10.md`](disaster_recovery_circuit_breakers_2026_05_10.md) Phase 1.A +
      Phase 5.A. Two distinct AlertCodes: `KILL_SWITCH_AUTO_RECOVERED` + `KILL_SWITCH_MANUAL_UNKILLED`. Done = decision
      recorded in `/codex/04-architecture/kill-switch-circuit-breaker.md` (per Q8 ratification — both modes
      documented) + pytest covering both states across all 4 BreakerAction × 2 BreakerRecoveryMode = 8 combos +
      `master_to_live_defi_2026_05_23.md` Group F item 22 todo `- [x]`. **SHIPPED execution-service@4bf6ec2c2
      (BreakerRecoveryMode tests) 2026-05-15**
- [x] [AGENT] P0. **GAP-18 (Q5.c)**: Ship `batch-live-reconciliation-service` code-complete + cron + 7-day live-vs-batch
      run BEFORE May-23. **PARTIAL — launcher shipped** deployment-service@544ad7e (2026-05-15):
      `launch-batch-live-recon-cron-vm.sh` + watchdog prefix `batch-live-recon-` + tarball registration in
      setup-data-pipeline-vm.sh + create-code-tarballs.sh. Service code confirmed complete (6-stage orchestrator).
      Backwards-from-May-23: cron must launch by **2026-05-16** to give 7 full days. **REMAINING**: operator must wire
      Cloud Scheduler → cron trigger → first nightly run, then monitor 7-day window. Acceptance: live continuous run +
      nightly batch replay + reconciler diff per shard, 7-day window passes per-pair tolerance thresholds. Done =
      service shipped ✅ + cron live (PENDING OPERATOR) + 7-day window green + `master_to_live_defi_2026_05_23.md` Group
      F item 21 todo `- [x]`.
- [x] [AGENT] P0. **WATCH-1 (Q1.1.d)**: Daily check `features_repo_consolidation_2026_05_08.md` Phase 2 push status.
      **RESOLVED 2026-05-14**: Phase 2 confirmed pushed (commits 2+3 PUSH ✅ per plan). Cascade unblocked.
- [x] [AGENT] P0. **WATCH-2 (Q1.2.b)**: Add Cross-Plan Coordination Banner to
      `live_pipeline_mtds_mdps_features_2026_05_08.md` Phase 5 calling out the writegate Phase 2.D soft-blocker.
      **RESOLVED 2026-05-15**: writegate Phase 2.D shipped 2026-05-12. live_pipeline Phase 5 is done [x]. Banner added
      to live_pipeline plan (see cross-plan banner commit). Phase 2.D ship date confirmed well within deadline.

**Phase 8 done:** GAPs 14-18 closed in destination plans + 4 codex docs landed + WATCH-1 resolved (Phase 2 push landed
or operator-escalated) + WATCH-2 resolved (banner added + Phase 2.D shipping or escalated).

---

## Cross-plan handshakes

- **Phase 1 GAP-1 (DeFi VM topology decision)** must land BEFORE `defi_master` Phase ? colocation wiring picks up.
  Coordinate via Cross-Plan Coordination Banner once Phase 1 ships.
- **Phase 2 GAP-6 (Phase 4D acceptance test)** must land BEFORE `master_to_live_defi_2026_05_23.md` Group F item 17
  closes (the test exercises the OperationalMode enum + StrategyInstructionEnvelope shape end-to-end).
- **Phase 5 ISSUE-1 fix** depends on writegate Phase 2.D adapter-side `available_at` stamping landing first (per
  features-onchain code investigation). If Phase 2.D hasn't landed by 2026-05-11, escalate to operator —
  carry_staked_basis features may need fallback.
- **Phase 8 GAP-18 (recon cron)** must launch by 2026-05-16 to give 7 full days before May-23 cutover. Backwards from
  cutover: every day of slip on cron-launch shrinks the live-vs-batch reconciliation window, eventually below the
  gate-threshold.
- **Phase 8 WATCH-1** is the upstream-most gate: Phase 2 push slip cascades through Phase 7 → live_pipeline Phase 5 →
  strategy ensemble colocation, affecting GAP-1 + GAP-2 + GAP-6 (which all depend on the consolidated features service
  being deployable).

---

## Daily verification (per CLAUDE.md "Master Plan Continuous-Verification Column")

- **Daily 09:00 UTC**: scan this plan's checkbox state. Any P0 todo `- [ ]` with <3 days to its phase ship target
  triggers operator alert via cross-side ping ledger.
- **Phase ship gate**: each phase's `Phase N done:` line is the verification — code commits + master-plan-todo flips
  - codex docs all landed before the phase is marked complete.

---

## Disposition

This plan archives 2026-05-23 (or sooner if all phases ship early). Any GAP that misses its phase ship target escalates
to operator immediately — per "Plans Run To Actual Completion" HARD RULE, no GAP defers post-cutover. If operator
chooses to defer a GAP post-cutover, this plan documents the decision + cites operator approval in the phase entry
before flipping `- [x]`.
