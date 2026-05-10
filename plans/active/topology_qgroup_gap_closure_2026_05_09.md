---
title: Topology Q-group GAP closure — 13 GAPs + 1 ISSUE before 2026-05-23
type: sub-plan
status: active
created: 2026-05-09
deadline: 2026-05-23
author: ikenna
parent_question_doc: plans/questions/topology_features_strategy_ml_execution_2026_05_08.md
consumes:
  - plans/epics/strategy_and_dart_master_2026_05_07.md
  - plans/epics/ml_and_features_master_2026_05_07.md
  - plans/active/master_to_live_defi_2026_05_23.md
  - plans/active/defi_master_2026_05_07.md
locked_by: live-defi-rollout
locked_since: 2026-05-09
---

# Topology Q-group GAP closure — 13 GAPs + 1 ISSUE before 2026-05-23

> **Why this plan exists.** The topology Q-doc
> ([`plans/questions/topology_features_strategy_ml_execution_2026_05_08.md`](../questions/topology_features_strategy_ml_execution_2026_05_08.md))
> identified 13 GAPs (no plan owns them) + 1 critical code-finding ISSUE while pinning runtime topology for the
> 2026-05-23 live-DeFi cutover. Per CLAUDE.md "Plans Run To Actual Completion, Not Smoke-Test Green" HARD RULE, none may
> defer post-cutover. This plan owns the closure path; each phase folds its draft P0 todo into the named destination
> master plan as the work ships.
>
> **Pattern.** Pure orchestration plan — no implementation lives here. Each phase ships a small unit (codex doc +
> matching todo into destination master + verification). The destination master plan owns the actual code shipping; this
> plan tracks readiness for May-23.
>
> **Done definition.** All 13 GAPs closed (codex doc + master-plan todo + verification) + ISSUE-1 fixed in code + parent
> Q-doc archived. Hard deadline 2026-05-23.

---

## Reference: GAP-to-destination map

| GAP     | Q-id                   | Destination master plan + phase                                                             | Severity                         |
| ------- | ---------------------- | ------------------------------------------------------------------------------------------- | -------------------------------- |
| GAP-1   | Q2.1.a, Q4.1.a         | `strategy_and_dart_master_2026_05_07.md` Phase 1.9                                          | P0 — VM topology decision        |
| GAP-2   | Q2.1.b                 | `strategy_and_dart_master_2026_05_07.md` Phase 1.9                                          | P0 — process arch                |
| GAP-3   | Q2.1.c                 | folds into GAP-2                                                                            | P0 — discovery mechanism         |
| GAP-4   | Q2.1.d                 | folds into GAP-1                                                                            | P0 — multi-tenancy               |
| GAP-5   | Q2.3.c                 | `strategy_and_dart_master_2026_05_07.md` Phase 1.9                                          | P0 — rejection event             |
| GAP-6   | Q3.1.b                 | `ml_and_features_master_2026_05_07.md` Phase 4D                                             | P0 — Phase 4D acceptance test    |
| GAP-7   | Q3.1.c, Q3.2.c, Q3.2.e | `ml_and_features_master_2026_05_07.md` Phase 4D                                             | P0 — model registry SSOT         |
| GAP-8   | Q3.1.d                 | `ml_and_features_master_2026_05_07.md` Phase 4D                                             | P1 — codex-only decision         |
| GAP-9   | Q3.2.a                 | `ml_and_features_master_2026_05_07.md` Phase 1A                                             | P0 — batch inference cadence     |
| GAP-10  | Q3.2.b                 | `ml_and_features_master_2026_05_07.md` Phase 4D                                             | P0 — live latency SLA            |
| GAP-11  | Q4.1.d                 | `defi_master_2026_05_07.md` (security phase TBD)                                            | P0 — wallet key custody          |
| GAP-12  | Q4.2.c                 | `strategy_and_dart_master_2026_05_07.md` Phase 1.9                                          | P0 — matching engine config      |
| GAP-13  | Q5.e                   | `master_to_live_defi_2026_05_23.md` Group F                                                 | P0 — multi-mode wallet isolation |
| ISSUE-1 | Q3.2.d                 | `plans/active/issues/features_onchain_lookahead_bias_suppression_2026_05_09.md` (issue doc) | P0 — code fix required           |

---

## Phase 1 — Strategy ensemble topology (GAPs 1, 2, 3, 4, 5, 12) — owner: strategy_and_dart_master Phase 1.9

**Target ship:** 2026-05-15 (8 days). Blocks downstream colocation work in defi_master + cefi_master.

- [ ] [AGENT] P0. **GAP-1 + GAP-4**: Pin strategy-ensemble VM topology — ONE VM per asset_group (DeFi VM hosts
      carry_staked_basis + ARBITRAGE_PRICE_DISPERSION (funding-rate-dispersion; renamed from legacy
      leveraged_funding_arb per Stream B canonicalisation 2026-05-07); CeFi VM hosts hedge legs). Multi-tenancy:
      dedicated ensemble per
      archetype within a VM, sharing position-balance + risk via VM-local IPC; no cross-archetype mixing of strategy
      state. Done = `codex/04-architecture/strategy-ensemble-topology.md` lands + launcher-script registry in
      `deployment-service/scripts/vm/` updated + `strategy_and_dart_master_2026_05_07.md` Phase 1.9 has matching `- [ ]`
      todo flipped `- [x]`.
- [ ] [AGENT] P0. **GAP-2 + GAP-3**: Pin process-vs-in-proc shape — 4 services (strategy + position-balance + risk +
      execution) as SEPARATE processes on same VM, IPC via local Redis Stream + UCI HTTP within-VM. Same shape for
      batch + live (Batch = Live invariant). Service discovery via env vars `POSITION_BALANCE_URL` / `RISK_EXPOSURE_URL`
      / `EXECUTION_URL`, default to `http://localhost:{port}` when colocated. Done = codex doc + execution-service
      entrypoint config + colocation-bootstrap script + `strategy_and_dart_master` Phase 1.9 todo `- [x]`.
- [ ] [AGENT] P0. **GAP-5**: Define `ExecutionRejection` UAC event with closed-set `rejection_code`
      (`INSUFFICIENT_LIQUIDITY` / `RATE_LIMITED` / `KILL_SWITCH_ARMED` / `VENUE_DOWN` / `SLIPPAGE_EXCEEDED`) + wire
      strategy-service consumer for retry-or-alert routing. Done = UAC enum + UTL helper + strategy + alerting
      consumer + integration test + `strategy_and_dart_master` Phase 1.9 todo `- [x]`.
- [ ] [AGENT] P0. **GAP-12**: Enumerate matching-engine assumption surface in
      `codex/04-architecture/matching-engine-assumptions.md` — per-matcher slippage model + commission schedule +
      latency model + venue-liquidity proxy. Configurable via UAC `MatchingEngineConfig`. Required for backtest fidelity
      per master plan Group F item 18. Done = codex doc + UAC config class + test verifying configurable assumptions per
      matcher + `strategy_and_dart_master` Phase 1.9 todo `- [x]`.

**Phase 1 done:** 4 codex docs landed + 4 todos flipped in strategy_and_dart_master Phase 1.9 + integration tests green.

---

## Phase 2 — ML lifecycle (GAPs 6, 7, 8, 9, 10) — owner: ml_and_features_master

**Target ship:** 2026-05-18 (11 days). Phase 4D acceptance test (GAP-6) is the cutover-blocker per code investigation.

- [ ] [AGENT] P0. **GAP-6**: Ship strategy-service pytest integration test asserting (a) ml-inference RPC call returns
      calibrated signal, (b) cost-aware filter drops signals where `expected_alpha < execution_cost_bps`, (c) end-to-end
      latency < SLA from GAP-10. **Test currently does not exist** per code investigation; required by Phase 4D
      acceptance criterion. Done = pytest in `strategy-service/tests/integration/` green + `ml_and_features_master`
      Phase 4D todo `- [x]`.
- [ ] [AGENT] P0. **GAP-7**: Lift model-registry SSOT into UAC — `ModelArtifactRegistry` (`model_id`, `model_family`,
      `asset_group`, `version`, `gcs_uri`, `trained_at`). Codify selection logic + paper-snapshot semantics (paper run
      freezes model artifact at run-start) + live hot-reload cadence (weekly default, configurable per archetype) in
      `codex/04-architecture/ml-lifecycle.md`. Done = UAC types + codex + ml-inference reads from registry +
      `ml_and_features_master` Phase 4D todo `- [x]`.
- [ ] [AGENT] P1. **GAP-8**: Codify "monolithic ML cluster ships May-23, per-asset-group sharding deferred post-cutover"
      as explicit decision in `codex/04-architecture/ml-lifecycle.md`. Done = codex doc landed +
      `ml_and_features_master` Phase 4D todo `- [x]`. (P1 because no code change required.)
- [ ] [AGENT] P0. **GAP-9**: Pin batch ML inference cadence — per-bar replay (NOT vectorized daily pass) to honor "Batch
      = Live, only fill source differs" invariant. Acceptance: replay-mode pytest covering 24h of bars, asserting
      per-bar `predict()` called once per bar at the bar's `available_at`. Done = test green + `ml_and_features_master`
      Phase 1A todo `- [x]`.
- [ ] [AGENT] P0. **GAP-10**: Define live ml-inference latency SLA — p99 ≤ 200ms per signal for carry + funding-arb
      archetypes (sub-second strategies). Enforce via pytest + Grafana alert. Done = SLA documented + alert wired +
      7-day live-soak passes + `ml_and_features_master` Phase 4D todo `- [x]`.

**Phase 2 done:** Phase 4D acceptance test exists + green; model registry SSOT in UAC; latency SLA enforced; codex
ml-lifecycle.md landed; 5 todos flipped in ml_and_features_master.

---

## Phase 3 — DeFi wallet custody (GAP-11) — owner: defi_master

**Target ship:** 2026-05-13 (4 days). Security-critical; gates live-DeFi cutover.

- [ ] [AGENT] P0. **GAP-11**: Pin wallet private key custody for live DeFi VM — keys fetched per-request from Secret
      Manager via `ApiKeyReloader` pattern, NEVER held in process memory beyond single-request scope. Codify in
      `codex/04-architecture/interface-credential-convention.md` (extension). Done = codex doc + execution-service
      connector audit (verify `connect()` paths fetch fresh per call, never cache) + integration test asserts no
      in-memory persistence between requests + `defi_master_2026_05_07.md` security phase todo `- [x]` (or new phase if
      defi_master lacks one).

**Phase 3 done:** Codex extension + connector audit + integration test green + defi_master todo flipped.

---

## Phase 4 — Multi-mode wallet isolation (GAP-13) — owner: master_to_live_defi Group F

**Target ship:** 2026-05-20 (11 days). Gates the May-23 carry-live + funding-arb-paper ramp model.

- [ ] [AGENT] P0. **GAP-13**: Define multi-mode wallet isolation — when paper + live run simultaneously on same wallet,
      position-balance-monitor MUST split exposure tracking by mode. Decision between (a) separate sub-accounts per mode
      (cleaner but requires venue support), OR (b) virtual ledger overlay where paper positions are tracked off-chain
      (works on any venue but harder to audit). Decision + codex
      (`codex/04-architecture/multi-mode-wallet-isolation.md`) + integration test gating the May-23 carry-live +
      funding-arb-paper ramp. Done = codex + position-balance-monitor schema/code + integration test +
      `master_to_live_defi_2026_05_23.md` Group F item 21 (or new sub-item) todo `- [x]`.

**Phase 4 done:** Decision recorded + position-balance-monitor isolates by mode + integration test green +
master_to_live_defi Group F todo flipped.

---

## Phase 5 — Critical code-finding ISSUE-1 — owner: features-onchain-service

**Target ship:** 2026-05-12 (3 days). Carry_staked_basis archetype features depend on this calculator; suppression
violates CLAUDE.md "LookaheadBiasError raised loud" rule.

- [ ] [AGENT] P0. **ISSUE-1**: File issue doc at
      `plans/active/issues/features_onchain_lookahead_bias_suppression_2026_05_09.md` (covered by this plan's Phase 0
      below). Then fix: `features-onchain-service/features_onchain_service/app/core/feature_writer.py:125-131` — remove
      `contextlib.suppress(LookaheadBiasError)` wrapper around `PointInTimeEnforcer(strict=True)`. Investigate WHY
      suppression was added (likely upstream `available_at` stamping gap from writegate Phase 2.D) and either fix
      upstream stamping OR file blocker on writegate Phase 2.D landing first. Done = wrapper removed + tests green +
      issue doc archived.

**Phase 5 done:** Suppression removed + tests pass + issue doc closed.

---

## Phase 0 — File ISSUE-1 issue doc (immediate, today)

- [ ] [AGENT] P0. Create `plans/active/issues/features_onchain_lookahead_bias_suppression_2026_05_09.md` per CLAUDE.md
      "Findings Triage Discipline" Case-1 issue-doc format. Includes severity (P0), file:line evidence, why it matters,
      recommended fix path. Done = file landed in issues folder.

---

## Phase 6 — Codex SSOT updates for all ✅ ANSWERED Qs (parent doc)

**Target ship:** 2026-05-21 (12 days). Per CLAUDE.md "Post-Plan-Phase Codex Audit" HARD RULE.

- [ ] [AGENT] P1. Walk parent Q-doc Sections 1-5 for every ✅ ANSWERED Q + verify the answer is reflected in
      `codex/04-architecture/` or `codex/05-infrastructure/live-pipeline-architecture.md`. Add the answer if missing.
      Done = audit checklist signed off in this plan body.

---

## Phase 7 — Archive parent Q-doc

**Target ship:** 2026-05-22 (13 days, day before cutover).

- [ ] [AGENT] P0. Verify parent Q-doc archive criteria: every 🔴 GAP has a `- [ ]` todo in destination plan; every 🟢
      IN-FLIGHT Q's plan phase has shipped; every ✅ ANSWERED Q has codex SSOT reflecting; ISSUE-1 fixed in code. Move
      parent Q-doc from `plans/questions/` to `plans/archive/topology_features_strategy_ml_execution_2026_05_08.plan.md`
      per archive filename convention. Done = file moved + parent's `## Deferred work — migrated to:` section banners
      this plan as the closure home.

---

## Cross-plan handshakes

- **Phase 1 GAP-1 (DeFi VM topology decision)** must land BEFORE `defi_master` Phase ? colocation wiring picks up.
  Coordinate via Cross-Plan Coordination Banner once Phase 1 ships.
- **Phase 2 GAP-6 (Phase 4D acceptance test)** must land BEFORE `master_to_live_defi_2026_05_23.md` Group F item 17
  closes (the test exercises the OperationalMode enum + StrategyInstructionEnvelope shape end-to-end).
- **Phase 5 ISSUE-1 fix** depends on writegate Phase 2.D adapter-side `available_at` stamping landing first (per
  features-onchain code investigation). If Phase 2.D hasn't landed by 2026-05-11, escalate to operator —
  carry_staked_basis features may need fallback.

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
