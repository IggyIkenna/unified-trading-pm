---
doc_type: plan
title: Producer-silence protocol — flatten risk when strategy-service goes quiet, and know when we cannot
summary: >-
  Operator decision 2026-08-14, answering "what should happen when a producer goes silent". If strategy-service stops
  producing the cross-cutting data an instruction needs (risk, position) then: reconciliation UP means START FLATTENING
  RISK, with the protocol owned by the execution algo and aggressiveness strategy-dependent; reconciliation DOWN means
  we do not know our position, so it is a Slack alert and an operator physically checks the venues. Flattening is NOT
  close-everything — spreads are allowed, the objective is net delta per underlying, and the trade is chosen by
  post-trade leverage. Requires real code in strategy-service and execution-service, not just monitoring: a concept of
  flattening, strategy-aware position knowledge, and cross-venue long/short selection. SLAs must be long enough that
  ordinary restarts never trigger it.
status: active
nature: design
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service, strategy-service, batch-live-reconciliation-service, alerting-service, unified-api-contracts]
scope: [engineer, admin]
tags: [live-trading, safety, flattening, deleverage, staleness, risk, reconciliation]
related:
  [
    /plans/active/issues/live_path_has_no_stale_producer_revocation_2026_08_14.md,
    /codex/04-architecture/exposure-reduction-unification.md,
    /codex/04-architecture/dependency-health-policy.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
    /codex/04-architecture/kill-switch-circuit-breaker.md,
    /codex/09-strategy/operational/paper-batch-live-reconciliation.md,
    /plans/active/cross_cutting_closeout_observability_and_monitoring_2026_08_09.md,
  ]
created: "2026-08-14"
last_updated: 2026-08-14
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: design
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 3.6
assigned_role: infra
effort: xhigh
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    /codex/04-architecture/exposure-reduction-unification.md,
    execution-service/execution_service/algo_library/deleverage_executor.py,
    execution-service/execution_service/validation/freshness_gate.py,
    execution-service/execution_service/engine/kill_switch_bus_bridge.py,
    strategy-service/strategy_service/supervisor/health_aggregator.py,
    deployment-service/configs/dependency_health_policies.yaml,
  ]
supersedes:
superseded_by:
depends_on:
source: operator decision 2026-08-14 (verbatim requirements captured below)
---

# Producer-silence protocol

> **This is the operator's risk decision, recorded before implementation.** The question was: when a producer goes
> silent, do we hold new orders only, or also flatten existing exposure? The answer is neither-simply — it is
> conditional on whether we still know our position.

## The protocol

**Trigger.** strategy-service stops producing the data execution-service needs for a given instruction — including the
cross-cutting inputs (risk, position), not just the instruction itself.

**Branch A — reconciliation is UP (we know our position): START FLATTENING RISK.**

- The flattening protocol lives in the **execution algo**, not in the monitor. The monitor decides THAT we flatten; the
  algo decides HOW.
- **Aggressiveness is strategy-dependent** and must be wired through, because at this moment strategy-service is
  unreachable — so whatever the algo needs to know has to have been published in advance.

**Branch B — reconciliation is DOWN too (we do NOT know our position): ALERT, do not act.**

- Slack alert now; PagerDuty later. Deliberately not automated: an operator physically logs into the venues to see the
  real positions, then either flattens manually or instructs execution-service to flatten.
- Acting on an unknown position is worse than not acting. This branch exists precisely to stop the system from
  "flattening" against a position it cannot see.

**Reconciliation-down is itself fixable, and must be fixed first.** It routes through the normal escalation path —
restart, more memory, whatever the runbook says — with **retries and waits baked in**. Flattening is a worst-case last
resort; the system must try hard not to reach it.

## What flattening MEANS (this is the part with no code today)

- **NOT close every position.** Spreads are allowed and often correct. The objective is to bring exposure down, not to
  go flat on every leg.
- **Net delta per underlying** is the target, not per-instrument or per-venue position.
- **Choose the trade by POST-TRADE LEVERAGE.** Reducing a long and increasing a short can be delta-equivalent while
  differing materially in leverage after the fact — pick the better one.
- Longs and shorts already exist **across exchanges**; selection is cross-venue.
- **Model-agnostic and strategy-agnostic where it can be, specific where it must be.** The condition-based responses all
  flow through one path.

## SLA discipline (the requirement that prevents this being a nuisance)

**The down-timeout must be long enough that ordinary breaks and short restarts never trigger flattening.** This is the
recurring operator instruction and it governs every threshold in this plan: a deploy, a rolling restart or a brief
network blip must not cost a flatten. Calibrate the SLA to observed restart duration plus margin, and state the
measurement that justified the number.

## Todos

### Phase 1 — the decision inputs must exist before they are needed

- [ ] [CODE] P0. Define what execution-service must ALREADY hold to flatten without strategy-service. At the moment of
      the trigger the producer is unreachable, so every input has to have been published ahead of time: per-strategy
      flatten aggressiveness, the strategy's own notion of which legs are hedges vs directional, and the underlying each
      instrument maps to. Write it as a UAC contract, not per-service structs. **Decided 2026-08-21 (same
      pass as the SLA number below)**: the flatten ACTION must be a per-strategy-slot/id CHOICE, not one behavior
      for everyone — model it as an enum (e.g. `FULL_FLATTEN` / `GRADUAL_REDUCE` / `DELTA_ONLY_FLATTEN`), not a
      scalar aggressiveness knob alone; each strategy config declares which action it wants. Repo: unified-api-contracts.
- [ ] [CODE] P0. Publish that contract from strategy-service on every instruction, so the last-known value is always
      available. Repo: strategy-service.
- [ ] [TEST] P0. A test proving the flatten path needs NO call to strategy-service — construct the flatten decision with
      strategy-service mocked as hard-down. If it cannot, the contract above is incomplete. Repo: execution-service.

### Phase 2 — net-delta flattening, chosen by post-trade leverage

- [ ] [CODE] P0. Net-delta-per-underlying calculator over current cross-venue positions. Spreads must survive it: the
      output is a delta reduction target per underlying, never a per-leg close list. Repo: execution-service.
- [ ] [CODE] P0. Candidate-trade generator + selector: enumerate the ways to reduce a given delta (reduce long, increase
      short, across venues) and choose by POST-TRADE leverage. Delta-equivalent candidates are the normal case; leverage
      is the tiebreak that matters. Repo: execution-service.
- [ ] [CODE] P0. Wire the selector into an execution algo, reusing `algo_library/deleverage_executor.py`'s existing
      asset-group-aware actions rather than paralleling them. That module is MarginEvent-driven today; this adds a
      second trigger with different semantics (net-delta target vs margin-severity tactic) — keep the actions, do not
      duplicate them. Repo: execution-service.
- [ ] [TEST] P0. Assert a spread is NOT closed: a delta-neutral long/short pair must survive a flatten that targets a
      different underlying. This is the test that distinguishes flattening from panic-closing. Repo: execution-service.

### Phase 3 — the trigger, and the branch that refuses to act

- [x] ✅ [CODE] P0. Producer-liveness detection for strategy-service: a last-complete-instruction clock per
      strategy/client, checked where `assert_market_data_fresh()` is checked. Note the distinction that made this
      necessary — the existing gate checks INPUT age, and a silent producer emits no record to age. Repo:
      execution-service. — `execution-service@fca9b729fa` (2026-08-21). Built
      `execution_service/validation/producer_liveness_gate.py`: a per-`(strategy_instance_id, client_id)`
      last-seen clock (`record_instruction_received()` / `is_producer_stale()`), using the 15-minute SLA ruled
      above in Phase 4. Wired as the 6th armed kill-switch condition: `strategy_instruction_subscriber.py`
      records the clock on every successfully-processed real instruction and sweeps
      `check_all_producers_liveness()` every poll cycle (independent of whether that cycle found anything — a
      silent producer produces no envelope for `poll_once()` to see, so the sweep has to run on the timer, not
      on arrival). A stale producer arms `kill_switch.activate()` (blocks new orders via the same
      `_route_kill_switch_guard()` every other condition gates through) and emits the existing `FEED_UNHEALTHY`
      alert (reused, not a new AlertCode — no UAC change needed). Deliberately does NOT build this todo's
      sibling two (branch on reconciliation health, dedicated Slack copy) or the flatten/reduce machinery in
      Phases 1-2/5a — this is the detection piece only, scoped narrowly per
      `/plans/active/issues/live_path_has_no_stale_producer_revocation_2026_08_14.md`. Tests:
      `tests/validation/test_producer_liveness_gate.py` — fresh producer doesn't trigger, never-seen producer
      isn't stale, a stale producer (mocked clock) arms the kill switch + alerts once per silence episode and
      is proven (via `InstructionRouter._route_kill_switch_guard`) to place no order, and recovery clears the
      alert marker for the next episode.
- [ ] [CODE] P0. Branch on reconciliation health: UP → flatten; DOWN → alert only, act on nothing. The DOWN branch must
      be structurally incapable of placing an order. Repo: execution-service.
- [ ] [CODE] P0. Slack alert for the DOWN branch naming what the operator must do — log into the venues, read the real
      positions, then flatten manually or instruct execution-service. PagerDuty is a later upgrade, not a blocker. Repo:
      alerting-service.
- [ ] [CODE] P1. An operator-facing flatten instruction path into execution-service, so the manual branch is a typed
      command rather than venue-by-venue clicking. Repo: execution-service.

### Phase 4 — try hard not to get here

- [ ] [CODE] P0. Reconciliation-down escalation with retries and waits BEFORE any flatten: restart, resource bump, per
      the runbook. Flattening only after the escalation path is exhausted. Repo: batch-live-reconciliation-service.
- [x] ✅ [OPERATOR] P0. **RULED 2026-08-21 — down-timeout = 15 minutes.** Measured 2026-08-21 via
      `gcloud run revisions describe`/`gcloud builds describe` (real Cloud Run revision history,
      execution-service + strategy-service, `asia-northeast1`): longest observed routine rollout-to-ready
      window was 78s (execution-service); the ~10.5min Cloud Build image-build phase does NOT cause producer
      silence since the old revision keeps serving traffic throughout. 15min is ~11.5x the largest observed
      rollout, well clear of any routine deploy/restart (sample thin, n=2-3 revisions per service — revisit if
      more revision history accumulates). **Same answer, second decision**: the flatten ACTION
      itself (not just the SLA) must be configurable per strategy slot/id — full flatten vs. gradual reduction
      vs. delta-only flatten, since strategies differ. This refines, not replaces, Phase 1's first todo below
      ("per-strategy flatten aggressiveness") — that UAC contract must model the action CHOICE as an enum, not
      just an aggressiveness scalar.
- [ ] [TEST] P0. A restart-does-not-flatten test: bounce strategy-service for a normal restart duration and assert no
      flatten is triggered. This is the regression guard for the operator's standing instruction.

### Phase 5a — consolidate the four exposure-reduction implementations

> **Design SSOT: `/codex/04-architecture/exposure-reduction-unification.md`** (written 2026-08-15). Close-all, flatten
> and margin-deleverage are one operation at three points on one axis; the todos below are that doc's
> migrate-then-delete order, which is gated so nothing is deleted before its replacement is live. Read it before
> starting any of them — the reasoning for each step lives there, not here.

- [ ] [CODE] P0. Generalise the flatten contract into `ReductionMandate` + `ReductionTrigger` (margin / producer-silence
      / drawdown-close-all / liquidation-imminent / operator), so all three behaviours differ by CONSTRUCTION rather
      than by code path. Deletes nothing. Repo: unified-api-contracts.
- [ ] [CODE] P0. Expand `algo_library/deleverage_executor.py` to accept a mandate, keeping `handle_margin_event()` as a
      thin adapter over the same core. Its asset-group action table (`repay_debt`/`top_up_collateral`/`close_risky_leg`/
      `unwind_to_mm`/`cap_bound_block`) is the asset and is retained verbatim — the module's defect is its intake, not
      its tactics. Repo: execution-service.
- [ ] [CODE] P0. Give it a real caller and a `margin-events` subscriber. Until this lands, steps above have only moved
      inert code around: `handle()` has had no caller, no subscriber and no order path since it was written. Repo:
      execution-service.
- [ ] [CODE] P0. Publish `ExposureSnapshot` from PBMS over the UTL event bus (NOT an HTTP call from execution-service —
      that both violates the no-service↔service-dependency rule and fails in exactly the situation the mandate exists
      for). Repo: strategy-service.
- [ ] [CODE] P0. Enable `PBMSPositionPublisher` (defaults `enabled=False`) so execution fills reach PBMS for
      reconciliation. **No PBMS deployment work is needed** — CORRECTED 2026-08-15: PBMS is mounted inside
      strategy-service (`strategy_service/api/main.py:182`, `app.mount("/position", …)`) and ships with it. An earlier
      version of this todo asked the operator to "deploy PBMS", from a probe that searched Cloud Run for a service by
      NAME and never read the consumer. The real constraint is that PBMS is CO-LOCATED with the producer whose silence
      triggers this protocol — one process, one failure — which is why the snapshot must be pre-published rather than
      fetched. Repo: execution-service.
- [ ] [CODE] P1. Repurpose `UnifiedPositionTracker` as the no-snapshot fallback AND surface its divergence from the
      snapshot as a reconciliation signal — two independent derivations of the same quantity disagreeing is information,
      and it is discarded today. Not deleted. Repo: execution-service.
- [ ] [CODE] P1. Migrate the two `close_all` concrete scripts to emit mandates, THEN delete `close_all/_template.py`'s
      `ClosePosition`/`CloseAllPlan` — superseded by `ExposureLeg`/`ReductionMandate`, and not before. Repo:
      strategy-service.
- [ ] [CODE] P1. Replace the duplicated flatten vocabularies with the UAC enum — `_FLATTEN_SIDES`
      (unified-trading-library `ledger/materialize.py`) and `_FLAT_SIDES` (strategy-service `benchmark_fills.py`) — THEN
      delete both frozensets. Repos: unified-trading-library, strategy-service.

### Phase 5 — do not let it go inert

- [ ] [TEST] P0. Anti-inertness guards for every component here, per the pattern established 2026-08-14: assert each new
      decision component has a non-test caller. Three separate systems in this estate were individually complete,
      individually tested, and collectively inert; this plan adds several more components to that surface. Repo:
      execution-service.

## Progress Log

- **2026-08-21**: Shipped Phase 3's producer-liveness-detection todo only (`execution-service@fca9b729fa`) — the
  narrow detection clock this plan's Phase 3 scopes, closing the bounded piece of
  `/plans/active/issues/live_path_has_no_stale_producer_revocation_2026_08_14.md` that a dedicated task covered. The
  other 22 todos (flatten/reduce logic, branch-on-reconciliation-health, dedicated Slack alert, exposure-reduction
  unification) are untouched and remain open — this was a deliberately scoped slice, not a claim on the rest of the
  plan.
- **na-eligibility-audit 2026-08-17** [body-hash:9e6046fe7dd8ae5a]: KEEP-NA, valid -- source: frontmatter + body blockquote confirm this is the operator's own dated risk decision (2026-08-14), verbatim requirements captured. All 23 open todos (Phases 1-5a/5) are live-trading risk-management design+build spanning execution-service/strategy-service/batch-live-reconciliation-service/alerting-service/UAC -- nature:design, effort:xhigh, P0. Exactly the "multi-file, multi-day, live-dispatch-critical-path" class the bounded-outcome bar excludes even where individual todos read as one clean line. Cross-cutting tranche audit.
- **na-eligibility-audit 2026-08-17** [body-hash:d111b57d45b48364]: KEEP-NA, valid -- Operator risk-decision doc (2026-08-14) recording the producer-silence flatten protocol; the source field and intro blockquote explicitly cite the operator's own dated ruling as the doc's basis (NEVER-RE-LITIGATE criterion a). All 23 open todos are live-trading risk-management design+build work spanning execution-service/strategy-service/batch-live-reconciliation-service/alerting-service (net-delta calculators, post-trade-leverage trade selection, producer-liveness detection, the exposure-reduction unification per the cited /codex/04-architecture/exposure-reduction-unification.md design SSOT) -- genuine judgment-heavy work on live-dispatch-critical-path machinery, not mechanically bounded. One item is explicitly [OPERATOR]-tagged (SLA numbers); one downstream test depends on that SLA existing first.
- **context-scout 2026-08-17**: refreshed context_scope (6 entries) — added the Phase 5a Design SSOT
  (`/codex/04-architecture/exposure-reduction-unification.md`, explicitly cited in-doc but missing from the prior
  source-only list), kept all 5 existing source paths.
- **na-eligibility-audit 2026-08-17** [body-hash:9e6046fe7dd8ae5a]: KEEP-NA, valid -- re-verified, no content change (2 same-day 2026-08-17 markers already on record, both KEEP-NA valid, likely reflecting the corpus's own same-date marker tie-break bug tracked in na_eligibility_body_hash_unstable_across_marker_appends_2026_08_17.md rather than a genuine double-audit). All 23 open todos remain live-trading risk-management design+build spanning execution-service/strategy-service/batch-live-reconciliation-service/alerting-service/UAC (net-delta calculators, post-trade-leverage trade selection, producer-liveness detection, the exposure-reduction unification design) -- the operator's own dated 2026-08-14 risk decision, explicitly not worker-determinable per the doc's own citation. Cross-cutting tranche audit.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
