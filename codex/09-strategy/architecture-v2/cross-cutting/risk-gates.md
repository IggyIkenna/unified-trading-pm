---
doc_type: codex-ssot
title: "Cross-Cutting: Risk Gates (4-Layer Model)"
summary:
  "The 4-layer risk enforcement model between a strategy instruction and the venue order: L1 strategy self-check → L2
  risk-and-exposure-service portfolio pre-flight → L3 execution-service venue-account pre-trade → L4 venue-side.
  Instance kill-switches live in L2; layers traverse in order and are idempotent by `instruction_id`."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, strategy-service]
scope: [engineer, admin]
tags: [risk, strategy, execution, self-healing, monitoring]
related:
  [
    /codex/09-strategy/architecture-v2/cross-cutting/venue-account-coordination.md,
    ../../../04-architecture/kill-switch-circuit-breaker.md,
    ../../../04-architecture/autonomous-recovery-matrix.md,
    ../../../04-architecture/strategy-risk-config-schema.md,
  ]
created: 2026-04-17
authoritative_for:
  [4-layer risk-gate model (strategy self-check / risk-exposure preflight / execution pre-trade / venue-side)]
referenced_by:
  [
    /codex/04-architecture/capital-efficiency-patterns.md,
    /codex/04-architecture/risk-breaker-seam.md,
    /codex/04-architecture/risk-preflight-flow.md,
    /codex/04-architecture/risk-rule-taxonomy.md,
    /codex/04-architecture/strategy-execution-protocol.md,
    /codex/04-architecture/strategy-risk-config-schema.md,
    /codex/09-strategy/_archived_pre_v2/cross-cutting/margin-health.md,
    /codex/09-strategy/architecture-v2/README.md,
  ]
owner:
last_reviewed: 2026-05-25
code_refs:
---

# Cross-Cutting: Risk Gates (4-Layer Model)

> **What it is:** The risk enforcement layers between a strategy's emitted instruction and the actual venue order. Four
> distinct gates, each with a specific responsibility and authority to reject/modify.

> **Per-strategy risk config** (drawdown thresholds, expected-drawdown model, response policy): see
> [`/codex/04-architecture/strategy-risk-config-schema.md`](../../../04-architecture/strategy-risk-config-schema.md).
> Every live strategy MUST declare all 3 blocks. The strategy-service `config_loader.py` enforces at load time.

## The 4 layers

```
┌───────────────────────────────────────────────────────────────┐
│  STRATEGY                                                      │
│  - Emits `StrategyInstruction` with intent (action, venues,   │
│    expression, size, urgency, attestations)                    │
└───────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌───────────────────────────────────────────────────────────────┐
│  LAYER 1 — STRATEGY SELF-CHECK (inside strategy-service)      │
│  Pre-emit validation. Before publishing the instruction:      │
│  - Position delta sanity (not absurd vs current position)     │
│  - Config self-limits (max_position_pct, max_daily_loss)      │
│  - Kill-switch state for THIS instance                         │
│  - Share-class invariant                                       │
│  - Attestations present (model version, feature hashes)        │
│  Failures: drop instruction, emit REJECTED_SELF_CHECK event.   │
└───────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌───────────────────────────────────────────────────────────────┐
│  LAYER 2 — RISK-AND-EXPOSURE-SERVICE PRE-FLIGHT               │
│  Portfolio-level guards spanning multiple strategies:          │
│  - Firm-wide instrument concentration                          │
│  - Firm-wide venue concentration                               │
│  - Client/fund-wide exposure limits                            │
│  - Family-level limits (e.g., total vol-trading vega)          │
│  - Correlation limits                                          │
│  - Regulatory position limits                                  │
│  - Greek aggregate limits                                      │
│  Failures: veto instruction, emit REJECTED_RISK event.         │
└───────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌───────────────────────────────────────────────────────────────┐
│  LAYER 3 — EXECUTION-SERVICE PRE-TRADE CHECKS                 │
│  Venue-account feasibility at the moment of order placement:   │
│  - Venue-account balance sufficient for full instruction       │
│  - Venue-account available margin sufficient                   │
│  - Rate-limit headroom on this venue                           │
│  - Credential valid + fresh                                    │
│  - Venue capability confirmed (instrument tradeable)           │
│  - Venue health (SOR skip if degraded)                         │
│  Failures: veto or reduce size; emit REJECTED_EXECUTION or    │
│  RESIZED_EXECUTION event.                                      │
└───────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌───────────────────────────────────────────────────────────────┐
│  LAYER 4 — VENUE-SIDE RISK (EXTERNAL)                         │
│  Venue's own pre-trade risk rules:                             │
│  - Margin / haircut                                            │
│  - Position limits                                             │
│  - Self-trade prevention                                       │
│  - Exchange circuit breakers                                   │
│  Failures: venue returns rejection; execution-service         │
│  interprets and emits ORDER_REJECTED event.                    │
└───────────────────────────────────────────────────────────────┘
```

## Layer responsibilities

### Layer 1 — strategy self-check

Enforced **inside** each strategy engine. Uses only local state (config + last-known position + this instance's kill
switch). Cheap, fast, catches bugs early.

```python
def self_check(self, instruction: StrategyInstruction) -> CheckResult:
    if not self.is_enabled():
        return CheckResult.reject("kill switch active")
    if abs(instruction.notional) > self.config.max_position_notional:
        return CheckResult.reject("exceeds self-limit")
    if not instruction.attestations.has_all_required():
        return CheckResult.reject("missing attestations")
    return CheckResult.approve()
```

### Layer 2 — risk-and-exposure-service

Reads **aggregated positions across all strategies** from PBMS. Enforces cross-strategy guards. Each strategy's kill
switch lives here. Family-level limits (all vol strategies combined, all ML directional combined).

```python
def pre_flight(instruction: StrategyInstruction) -> CheckResult:
    agg = position_aggregator.snapshot(client_id=instruction.client_id)
    # Firm-wide concentration
    if agg.instrument_concentration(instruction.instrument) + instruction.delta > LIMITS.instrument:
        return CheckResult.reject("instrument concentration")
    # Family limit
    if agg.family_vega_total(FAMILY.VOL_TRADING) + instruction.vega > LIMITS.vol_family:
        return CheckResult.reject("family vega limit")
    # ... etc.
```

### Layer 3 — execution-service pre-trade

Hits live venue state via PBMS venue-account snapshot (not just aggregated positions, but the specific venue account).

```python
def execution_pre_trade(instruction: StrategyInstruction) -> CheckResult:
    for venue in instruction.eligible_venues:
        va = pbms.venue_account(instruction.client_id, venue)
        if va.available_margin < instruction.required_margin(venue):
            continue  # try next venue
        if not credentials.valid(instruction.client_id, venue):
            continue
        return CheckResult.approve_on(venue)
    return CheckResult.reject("no feasible venue")
```

### Layer 4 — venue-side

External to us. We observe only via execution outcomes (ORDER_REJECTED with reason).

## Ordering and idempotency

Every instruction carries an `instruction_id` (content-hashed) and traverses all 4 layers in order. If Layer 2 vetoes,
Layers 3+4 never run. Rejections are logged with the rejecting layer. Re-emission of the same instruction id is a no-op
(idempotent by construction).

## Kill switches

Instance kill switches live in **Layer 2** (risk-and-exposure-service), so they persist across strategy restarts. Types:

- `DISABLED` (operator command)
- `DAILY_LOSS_BREACH` (auto-triggered)
- `MAX_DRAWDOWN_BREACH` (auto-triggered)
- `DATA_STALE` (auto-triggered)
- `KILL_SWITCH_TRIGGERED` (firm-wide emergency)

Killed instance still goes through Layer 1 self-check (which also sees the kill switch locally via consumer-side reload)
— Layer 2 is the authoritative source. See
[../../../04-architecture/kill-switch-circuit-breaker.md](../../../04-architecture/kill-switch-circuit-breaker.md).

## Multi-venue kill switch behaviour

When a strategy's venue is killed but another eligible venue is alive, the strategy MUST NOT "fight" the kill switch by
flooding alternate venues. Instead:

- Delta-neutral exit default (close position cheapest)
- If kill is `DISABLED`, new entries blocked everywhere
- If kill is `DATA_STALE`, only reductions allowed

See feedback memory `kill_switch_multi_venue_rules.md` and
[../../../04-architecture/kill-switch-circuit-breaker.md](../../../04-architecture/kill-switch-circuit-breaker.md).

## Recon gates

Layer 2 AND Layer 3 both require **reconciliation freshness** (PBMS data not stale). If recon is down and execution is
down, the strategy is **human-required** — 0.1% of cases. See feedback memory `reconciliation_gates_execution.md` and
[../../../04-architecture/autonomous-recovery-matrix.md](../../../04-architecture/autonomous-recovery-matrix.md).

## Events emitted

| Event                             | Emitted by | Meaning                  |
| --------------------------------- | ---------- | ------------------------ |
| `INSTRUCTION_EMITTED`             | Strategy   | After Layer 1 passes     |
| `INSTRUCTION_REJECTED_SELF_CHECK` | Strategy   | Layer 1 vetoed           |
| `INSTRUCTION_ACCEPTED_PREFLIGHT`  | Risk       | Layer 2 approved         |
| `INSTRUCTION_REJECTED_RISK`       | Risk       | Layer 2 vetoed           |
| `ORDER_SUBMITTED`                 | Execution  | Layer 3 approved         |
| `ORDER_REJECTED_EXECUTION`        | Execution  | Layer 3 vetoed           |
| `ORDER_REJECTED_VENUE`            | Execution  | Layer 4 (venue) rejected |
| `ORDER_FILLED`                    | Execution  | Venue acknowledged fill  |

## Not in this doc

- **Post-trade risk** — PBMS + risk service continuously monitor; drawdown/DD triggers re-enter kill-switch machinery
- **Execution slippage / fill quality** — [benchmark-fills.md](benchmark-fills.md)
- **Slow-moving venue eligibility** — [../axes/venue-eligibility.md](../axes/venue-eligibility.md); this doc is
  fast-moving pre-trade checks
- **Kill switch policy details** —
  [../../../04-architecture/kill-switch-circuit-breaker.md](../../../04-architecture/kill-switch-circuit-breaker.md)

## Cross-references

- Kill switch:
  [../../../04-architecture/kill-switch-circuit-breaker.md](../../../04-architecture/kill-switch-circuit-breaker.md)
- Autonomous recovery:
  [../../../04-architecture/autonomous-recovery-matrix.md](../../../04-architecture/autonomous-recovery-matrix.md)
- Venue-account coordination: [venue-account-coordination.md](venue-account-coordination.md)
- Strategy execution protocol:
  [../../../04-architecture/strategy-execution-protocol.md](../../../04-architecture/strategy-execution-protocol.md)
