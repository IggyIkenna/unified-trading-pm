---
doc_type: issue
title: Live path has no stale-producer detection — a silent strategy-service triggers no execution-side action
summary: >-
  Measured 2026-08-14: if strategy-service goes down or stops publishing, execution-service does NOT detect it. It gates
  on INPUT freshness (market-data age vs venue SLA), never on PRODUCER liveness. The kill switch is armed by exactly 5
  risk conditions, none of which is "an internal service went silent". The dependency-health policy has 27 entries and
  ZERO are our own microservices — all 27 are external venues, RPCs, cloud primitives or notification channels — and it
  emits alerts only, with zero consumers in execution-service or strategy-service. The batch/data pipeline just got
  exactly this mechanism (alert-driven dependency revocation); live has no equivalent.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service, strategy-service, alerting-service, unified-api-contracts]
scope: [engineer, admin]
tags: [live-trading, safety, kill-switch, dependency-health, staleness, revocation]
related:
  [
    /codex/04-architecture/dependency-health-policy.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
    /codex/04-architecture/kill-switch-circuit-breaker.md,
    /plans/active/alert_driven_dependency_revocation_2026_08_12.md,
    /plans/active/revocation_arming_2026_08_14.md,
  ]
created: "2026-08-14"
last_updated: 2026-08-14
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P0
assigned_role: infra
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
source: operator question 2026-08-14 — measured while arming /plans/active/revocation_arming_2026_08_14.md
drift_direction: advance-code
depends_on: []
---

# Live path has no stale-producer detection

**The operator's question, 2026-08-14:** _"The strategy service goes down. There's a delay, it doesn't send a heartbeat.
The execution service has to respond to that... it would itself do the retries or shutdowns, and that would trigger the
action downstream. Is that the flow?"_

**Measured answer: no. That flow does not exist today.** Everything below is measurement, not inference.

## What actually exists

| Mechanism                                           | What it keys on                       | What it does                                  |
| --------------------------------------------------- | ------------------------------------- | --------------------------------------------- |
| `execution_service.validation.freshness_gate`       | MARKET DATA age vs venue SLA          | raises `DataStalenessError`, blocks the order |
| `LIVE_ALERT_RULES` with `triggers_kill_switch=True` | 5 named risk conditions               | arms the kill switch via the UTL bus          |
| `dependency_health_policy` (UAC + alerting-service) | per-dependency outage seconds         | emits WARN / SEV1 / SEV0 — **alerts only**    |
| `strategy_service.supervisor.health_aggregator`     | per-ClientWorker subprocess heartbeat | strategy-service's OWN health endpoint        |

**The five kill-switch-arming rules, in full** (`triggers_kill_switch=True` in `LIVE_ALERT_RULES`):
`KILL_SWITCH_DEFI_LIQUIDATION_RISK` (global) · `KILL_SWITCH_PORTFOLIO_DRAWDOWN` (global) ·
`KILL_SWITCH_VENUE_DISCONNECT` (venue) · `KILL_SWITCH_ML_MODEL_FAILURE` (archetype) · `KILL_SWITCH_ORACLE_DIVERGENCE`
(global).

`VENUE_DISCONNECT` is the closest, and it is about an EXTERNAL venue, not an internal producer.

## The three gaps, precisely

1. **Freshness is checked on the INPUT, not on the PRODUCER.** `assert_market_data_fresh()` asks "is this tick within
   its venue's SLA". It cannot fire because strategy-service stopped publishing instructions — there is no instruction
   whose age it would be checking. A producer that goes silent produces no stale record; it produces NO record, and
   nothing on the live path treats absence as a signal. This is the live analogue of the honest-absence rule the data
   pipeline already enforces.

2. **The dependency-health policy is inert on the trading path, AND does not describe our services.** It carries
   `expected_recovery_time_seconds` / `warning_buffer_seconds` / `hard_escalation_seconds` / `fallback_available` /
   `protected_mode_available` per dependency, and alerting-service evaluates it. But all **27** registered dependencies
   are EXTERNAL venues/RPCs, cloud primitives, or notification channels — **zero** are execution-service,
   strategy-service, risk or reconciliation. `INTERNAL_CONTROL_PLANE` means _cloud infra_, not _our services_. A silent
   strategy-service breaches no policy because no policy describes it. But `rg -l 'health_policy|DependencyHealth'` over
   execution-service (1384 py files) and strategy-service (1033 py files) returns **zero** consumers. It pages a human;
   it changes no behaviour. This is the same shape as the defect just found in the batch path — a policy with no
   actuator — one layer up.

3. **No scope arms on internal-service silence.** The kill switch has a `STRATEGY` scope in its taxonomy, and nothing
   publishes to it for a silent strategy-service.

## WORSE THAN "ALERTS ONLY" — the system is inert at THREE levels (measured 2026-08-14)

Found while attempting to register our services. Registering them would have produced rows nothing can observe, so it
was deliberately NOT done — that would be coverage-shaped inaction, the same pattern as a policy with no actuator.

1. **Nothing probes.** `dependency_health_prober`'s built-in per-method probes are, in its own module docstring,
   "SCAFFOLDS that report healthy by default — fail-open". A real probe must be injected via `probe_fn`, and `probe_fn`
   has **zero** production injection sites — the only references are its own parameter declaration and assignment. So
   every registered dependency reports healthy forever, and **no dependency-health alert has ever fired or can fire.**
2. **Even if one fired, nothing acts** — zero consumers in execution-service or strategy-service.
3. **Our own services are not registered** — all 27 entries are external venues, RPCs, cloud primitives or notification
   channels.

The escalation ladder, the buffers, the runbook links and all 27 policies are real, tested, and unreachable. Same defect
as the batch revocation actuator, three layers deep: each layer is individually complete and the chain never executes.

**Sequencing this implies — do not reorder, each step is inert without the one before it:** inject a real `probe_fn` →
register our services so there is something to probe → wire an actuator that consumes the verdict. Registering first is
the tempting cheap step and produces rows that report healthy forever.

## Admission-gate coverage for the lightweight launcher path — BLOCKED by a guardrail (2026-08-14)

The ~158 launchers using `launcher_common.sh`'s `lc_` helper have no admission gate. The obvious fix — read the hold
marker from object storage inside the emitted startup snippet, since that path deliberately has no venv and the helper
already shells out to the cloud CLI for its own log streaming — is **blocked by the orchestrator guardrail banning
subprocess cloud-CLI object operations**, which covers reads, and would fail QG STEP 5.105 at commit time anyway.

Not circumvented, per the guardrail's own instruction to escalate. Three options for the operator:

- **Migrate the lightweight launchers onto `vm-exec-with-gcs-tee.sh`** — removes the second path rather than duplicating
  the gate into it. Most work, best end state.
- **Grant a narrow documented exception** for a single-object read in a VM startup script. The rule's stated rationale
  is recursive listing buffering through `/tmp` and exhausting it; a one-object read does not do that.
- **Accept the lightweight path as deliberately ungated** and record it in the codex, so 148/184 stops reading as an
  accident.

## Why this matters more than "no new orders"

A stopped strategy-service is not fail-safe by default. New target positions stop arriving, so execution holds — but
**existing exposure keeps running unmanaged**: no rebalancing, no exits, no deleverage instructions. The positions that
were open when the producer died stay open, at whatever the market does next, until a human notices the page. For a
delta-neutral book that is a slow bleed; for a leveraged one it is the liquidation ladder with nobody on it.

## Relationship to the batch work

`/plans/active/alert_driven_dependency_revocation_2026_08_12.md` built exactly this mechanism for the DATA PIPELINE:
alert identity → `DependentAction` → markers a dependent reads → hold admission / drain in flight. The live path has the
same shape of problem and none of the machinery. **Do not simply reuse the batch actuator**: its delivery is GCS markers
polled on a heartbeat tick, which is right for a VM doing hour-long shards and far too slow for an execution loop. The
reusable parts are the POLICY shape (an identity → action table with a machine-checked ceiling) and the lesson that a
policy without a wired actuator reads as done and does nothing.

## The kill switch cannot help when execution-service is the thing that failed

Worth stating because it is structural, not a bug: the kill switch is IN-PROCESS. `kill_switch_bus_bridge.on_bus_event`
is subscribed by `ServiceBootstrap` **on boot**, and cancel-on-arm works through callbacks the order owner (OMS / live
orchestrator) registers in that same process. If execution-service is down there is no subscriber, so arming the bus
reaches nothing and no open order is cancelled. The kill switch protects against _bad trading decisions_ by a running
execution-service; it is not a lever over a dead one.

That is what makes execution / risk / reconciliation categorically different from strategy: a silent strategy-service
leaves a live execution-service that can still hedge, exit and be halted, whereas a dead execution-service leaves
positions with no automated actor at all. The operator's read (2026-08-14) is the right one — strategy can be down for a
while; execution/risk/reconciliation down is the escalation, and the honest answer there is redundancy or a human, not a
kill switch.

## RESOLVED into a plan — the operator made the risk decision 2026-08-14

The decision this issue was blocked on is made, and the work is now
`/plans/active/producer_silence_flatten_protocol_2026_08_14.md` (15 todos). The answer was not the binary this issue
posed (hold vs flatten) — it is conditional on whether we still know our position:

- **strategy-service silent + reconciliation UP** → START FLATTENING RISK. Protocol owned by the execution algo,
  aggressiveness strategy-dependent, and the inputs must be published in advance because the producer is unreachable at
  that moment.
- **strategy-service silent + reconciliation DOWN** → we do not know our position, so ALERT ONLY. An operator checks the
  venues physically, then flattens manually or instructs execution-service. The system must be structurally incapable of
  trading against a position it cannot see.
- **Reconciliation-down is fixed first** — escalation with retries and waits. Flattening is a last resort, not a reflex.
- **Flattening is NOT close-everything**: spreads are allowed, the target is net delta per underlying, and the trade is
  chosen by POST-TRADE leverage (reducing a long and increasing a short can be delta-equivalent but not
  leverage-equivalent).
- **SLAs must exceed ordinary restart and deploy durations** so routine operations never trigger a flatten.

This issue stays open for the parts the plan does not cover: the dependency-health chain's three-level inertness, and
the launcher-gate guardrail question.

## Follow-up todos

Items 1-2 below (the risk decision + producer-liveness gating) are **superseded** by
`/plans/active/producer_silence_flatten_protocol_2026_08_14.md` (15 todos) — do not redo them here. Items 3-5 are the
genuinely open remainder this issue is tracking (the dependency-health chain's three-level inertness + its doc claim);
none of them appear as todos in that plan.

- [x] ~~Decide the intended live behaviour when a producer goes silent~~ — SUPERSEDED, resolved by the operator
      2026-08-14 into `/plans/active/producer_silence_flatten_protocol_2026_08_14.md`.
- [x] ~~Add producer-liveness gating to the execution path~~ — SUPERSEDED, covered by the same plan.
- [ ] [CODE] P0. Wire `dependency_health_policy` to an actuator rather than only to alerts. Sequencing matters (see
      "WORSE THAN 'ALERTS ONLY'" above — each step is inert without the one before it): (a) inject a real `probe_fn` for
      at least execution-service/strategy-service so a probe result exists at all (today every registered dependency
      fail-opens to healthy forever), (b) register our own services in the policy (currently 0/27 entries are internal),
      (c) only then wire an SEV0 breach on a registered internal service to reach the kill-switch bus at its declared
      scope. Repo: alerting-service.
- [ ] [TEST] P0. An anti-inertness guard for the live path, mirroring the batch one: assert the dependency-health policy
      has a non-test consumer that changes behaviour (not just logs/pages) — so a future regression back to alerts-only
      fails CI instead of silently reverting to today's inert state. Repo: alerting-service.
- [ ] [DOC] P1. `/codex/04-architecture/dependency-health-policy.md` reads as though the policy governs behaviour; it
      governs alerting only (and today, per the three-level-inertness finding above, does not even reliably alert —
      every built-in probe fail-opens). State that explicitly until an actuator + real probes exist. Repo:
      unified-trading-pm.
- [ ] [OPERATOR] P1. Decide the lightweight-launcher admission-gate question (see "Admission-gate coverage for the
      lightweight launcher path" above) — one of: migrate the ~158 `launcher_common.sh` launchers onto
      `vm-exec-with-gcs-tee.sh`; grant a narrow documented exception to the cloud-CLI-in-startup-script guardrail for a
      single-object hold-marker read; or accept the lightweight path as deliberately ungated and record it in the codex.
      Blocked on this decision, not further investigation.

## Evidence

- `LIVE_ALERT_RULES` arming set enumerated at runtime via the deployment-service venv (5 rules, listed above).
- `rg -l 'health_policy|DependencyHealth' execution-service/ strategy-service/` → no matches, against populated trees
  (1384 / 1033 `.py` files — verified populated, because an earlier run of this same grep from the wrong working
  directory returned a misleading zero).
- `freshness_gate.py` module docstring: "checks whether the market data for an instrument is within its venue's
  freshness SLA before allowing order submission".
- `health_aggregator.py` module docstring: "per-ClientWorker heartbeat rollup... Consumed by
  `strategy_service/api/main.py`'s health endpoint" — intra-service, not cross-service.
