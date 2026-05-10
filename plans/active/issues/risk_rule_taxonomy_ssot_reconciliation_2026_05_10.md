---
title: "Spawned plan risk_simulations_limits_alerting_2026_05_10 introduces RiskRuleConsequence enum without § 7 reconciliation against 5 existing canonical risk SSOTs"
created: 2026-05-10
author: main-orchestrator-agent
source:
  - plans/active/risk_simulations_limits_alerting_2026_05_10.md (spawned plan, Phase 1 Day 2-3)
  - plans/questions/risk_simulations_limits_alerting_2026_05_08.md (question doc, first-pass reconstruction PM@6e504f0b)
  - codex/09-strategy/architecture-v2/cross-cutting/risk-gates.md (canonical SSOT)
  - codex/04-architecture/kill-switch-circuit-breaker.md (canonical SSOT)
  - codex/04-architecture/autonomous-recovery-matrix.md (canonical SSOT)
  - plans/active/alerting_service_live_rules_2026_05_07.md (UAC@d00326d AlertCode SSOT)
locked_by: live-defi-rollout
locked_since: 2026-05-10
---

# Spawned plan introduces RiskRuleConsequence enum without § 7 SSOT reconciliation

> **Severity**: P0 — May-23 cutover plan; Phase 1 ships UAC contracts on Day 2-3 (so 2026-05-11–12); downstream service
> migration (Phase 4) wires those contracts. Post-Phase-1 reconciliation is much costlier than pre-Phase-1.
> **Blast radius**: 8 repos per the plan's pre-audit (UAC + UTL + risk-and-exposure-service + execution-service +
> strategy-service + alerting-service + deployment-api + deployment-ui).
> **Suggested owner**: spawned-plan author (whoever picks up `risk_simulations_limits_alerting_2026_05_10` Phase 1) +
> operator decision on layering.

## What I found

Spawned plan `plans/active/risk_simulations_limits_alerting_2026_05_10.md` (status: active, deadline: 2026-05-23,
spawned_from: question doc PM@6e504f0b first-pass reconstruction) proposes in Phase 1 a new UAC enum:

```python
RiskRuleConsequence = BLOCK | SCALE_DOWN | MONITOR | TEST_ONLY
```

The plan body **does not reference** any of these 5 existing canonical workspace SSOTs:

1. **4-layer risk-gates model**
   ([`codex/09-strategy/architecture-v2/cross-cutting/risk-gates.md`](../../codex/09-strategy/architecture-v2/cross-cutting/risk-gates.md))
   — Layer 1 strategy self-check / Layer 2 risk-and-exposure-service pre-flight / Layer 3 execution-service pre-trade /
   Layer 4 venue-side. Each layer emits canonical events on veto: `INSTRUCTION_REJECTED_SELF_CHECK`,
   `INSTRUCTION_REJECTED_RISK`, `ORDER_REJECTED_EXECUTION`, `ORDER_REJECTED_VENUE`.
2. **3 canonical circuit-breaker actions** per
   [`alerting_service_live_rules_2026_05_07.md`](../alerting_service_live_rules_2026_05_07.md) — `stop_new_signals` /
   `force_exit_only` / `halt_strategy`. Per-venue adaptive state machine (CLOSED / DEGRADED / OPEN / HALF_OPEN) per
   [`codex/04-architecture/kill-switch-circuit-breaker.md`](../../codex/04-architecture/kill-switch-circuit-breaker.md).
3. **5 kill-switch trigger types** — DISABLED / DAILY_LOSS_BREACH / MAX_DRAWDOWN_BREACH / DATA_STALE /
   KILL_SWITCH_TRIGGERED + 4 strategy kill-switch behaviours (STOP_NEW_ONLY / FAST_UNWIND / SLOW_UNWIND / DELTA_HEDGE).
4. **ErrorAction taxonomy** per
   [`codex/04-architecture/autonomous-recovery-matrix.md`](../../codex/04-architecture/autonomous-recovery-matrix.md)
   — RETRY / RECONNECT / SKIP / FAIL via `classify_venue_error()`.
5. **39-code closed-set AlertCode + AlertSeverity + AlertChannel** at UAC@d00326d per the alerting plan; with per-rule
   `triggers_kill_switch: bool` flag in `AlertRule`.

## Two possible framings (operator decides)

### Framing 1 — legitimate layered extension

`RiskRuleConsequence` and the 3 circuit-breaker actions live at **different abstraction layers**:

- `RiskRuleConsequence` = "what does this specific rule say to do for this single pending instruction?" (per-rule
  per-instruction, evaluated at Layer 2 of the risk-gates model).
- Circuit-breaker actions = "what does this venue's adaptive state machine do once it transitions to OPEN?" (per-venue
  per-state-transition, applied at Layer 3 / venue surface).
- Kill-switch trigger types + strategy kill-switch behaviours = "what state is the strategy / venue / firm in, and
  which exit playbook executes?" (per-firm or per-strategy state).

  Under this framing, `RiskRuleConsequence` is a NEW enum at a NEW abstraction layer. SCALE_DOWN maps to existing
  `RESIZED_EXECUTION` event (Layer 3 size reduction). MONITOR (allow + flag) and TEST_ONLY (route to paper / matching
  engine) are genuinely new modes the existing taxonomy doesn't express.

  **What's required even under this framing**: spawned plan body MUST explicitly cite the 5 existing SSOTs + draw the
  abstraction-layer seam diagram + declare which existing canonical taxonomy each `RiskRuleConsequence` value composes
  with (e.g. "BLOCK at Layer 2 produces `INSTRUCTION_REJECTED_RISK` event + may transition the venue circuit-breaker
  via `triggers_kill_switch: true` rule flag"). Without this reconciliation, downstream service migration creates SSOT
  divergence.

### Framing 2 — contamination from question-doc first-pass reconstruction

The question doc `plans/questions/risk_simulations_limits_alerting_2026_05_08.md` was lost overnight 2026-05-08
parallel-agent activity (per
[`missing_question_docs_orphan_references_2026_05_10.md`](missing_question_docs_orphan_references_2026_05_10.md)).
First-pass reconstruction (PM@6e504f0b) **invented** a `BLOCK / MONITOR / TEST` action taxonomy because the
reconstructor (me) didn't audit existing workspace SSOTs before writing. The spawned plan extended this invention to
`BLOCK / SCALE_DOWN / MONITOR / TEST_ONLY`.

Under this framing, the spawned plan is downstream-contaminated and the right fix is to retire `RiskRuleConsequence`
in favor of the 3 existing circuit-breaker actions + the 4-layer risk-gates events.

## Why it matters

- **§ 7 SSOT** — workspace cannot have two competing canonical taxonomies for "what to do when a risk rule fires"
  without explicit abstraction-layer separation declared in code + docs. Whether Framing 1 or Framing 2 wins, the
  outcome MUST be one canonical decomposition + the answers to "Which event is emitted when?" / "Which rule transitions
  the kill-switch?" / "Which rule transitions the circuit-breaker?" must be unambiguous.
- **Phase 1 timing** — UAC contracts ship Day 2-3 (around 2026-05-11–12). After UAC ships + downstream services migrate
  in Phase 4, retroactive reconciliation is multi-repo refactor cost; pre-Phase-1 reconciliation is doc-edit cost.
- **Audit-pass risk** — the question doc's audit pass (which the operator + future agents will run) currently has no
  warning that the framing might be invented. Without a banner, the audit pass treats the question doc body as
  canonical and the spawned plan as legitimately consuming it.
- **Cross-plan coordination** — `simulation_scenarios_topology_price_shocks_2026_05_09.md` already names this question
  doc as the upstream owner of the rule taxonomy. Whatever the spawned plan ships, that consumer-plan inherits.

## Recommended decision

**Pre-Phase-1 reconciliation**: spawned plan author (whoever picks up Phase 1 Day 2-3) MUST add a section
"§ 7 SSOT reconciliation" to the plan body, before any UAC contract design. The section answers:

1. Is `RiskRuleConsequence` legitimately new abstraction (Framing 1) or invented contamination (Framing 2)?
2. If Framing 1 — draw the seam: which `RiskRuleConsequence` value maps to which existing canonical (event / kill-
   switch trigger / circuit-breaker action / strategy kill-switch behaviour). Enumerate every cell of the cross-product.
3. If Framing 2 — retire `RiskRuleConsequence`; use the existing 3 circuit-breaker actions + 8-event lifecycle.

   **Operator decides Framing 1 vs 2** — too consequential for an implementation agent to choose unilaterally.

After reconciliation: Phase 1 UAC contracts cite the 5 SSOTs in their docstrings + Phase 4 downstream migration
references the same.

## Disposition tracking

- [ ] Spawned plan author reads this issue doc + adds § 7 SSOT reconciliation section to plan body BEFORE Phase 1
      Day 2-3 UAC contract design.
- [ ] Operator picks Framing 1 (layered extension) or Framing 2 (contamination retirement).
- [ ] Plan body cites the 5 canonical SSOTs explicitly with the abstraction-layer seam declared.
- [ ] Question doc archaeology banner added (this issue doc's existence flagged in question doc top + iteration log).
- [ ] Issue doc closes when reconciliation lands in spawned plan body.

## Composes with

- **Findings Triage Discipline** (CLAUDE.md) — case-5 (big) finding: contradicts workspace SSOT + on May-23 critical
  path + would change work-split.
- **§ 1 Pre-Audit** + **§ 7 SSOT** (Citadel-Grade Planning Standards) — the pre-audit recipe (workspace-grep for
  every reference to a moved/renamed symbol) generalises to "every taxonomy declaration cites existing workspace
  taxonomies".
- **Plans Run To Actual Completion** — incomplete-reconciliation-at-Phase-1 = code-shipped-but-architecturally-broken.
- [`missing_question_docs_orphan_references_2026_05_10.md`](missing_question_docs_orphan_references_2026_05_10.md) —
  precondition incident; this finding is a downstream consequence.
