---
doc_type: codex-runbook
title: ML Alerting Rules — Live ML Inference + Signal Lifecycle
summary:
  Design contract for the 4 live-ML alerting rules (ML_SIGNAL_STALE, ML_MODEL_DRIFT_DETECTED, ML_PNL_DEVIATION,
  ML_INFERENCE_LATENCY_SLO) layered on the live-pipeline tier-up + KillSwitchBus taxonomy. Codes are NOT yet in
  alerting/codes.py (2026-05-12 LIFT); drift_monitor.py ships accuracy-drop / MODEL_RETUNE_REQUESTED instead of PSI/KL.
status: current
nature: process
asset_group: [meta]
stage: [meta]
repos: [alerting-service, execution-service, features-service, strategy-service]
scope: [engineer, admin]
tags: [runbook, ml, escalation, monitoring, live-trading, model-tier, reconciliation]
related:
  [
    /codex/15-runbooks/alerting/alert-code-taxonomy.md,
    /codex/15-runbooks/alerting/operator-playbook.md,
    /codex/05-infrastructure/live-pipeline-architecture.md,
    /codex/16-strategy-playbooks/ml/cefi-ml-live-serving.md,
  ]
created: 2026-05-08
owner: ikenna
cadence: on-demand
verifier: operator
last_executed:
code_refs:
authoritative_for:
  [
    live-ML alerting rule design contract (ML_SIGNAL_STALE / ML_MODEL_DRIFT_DETECTED / ML_PNL_DEVIATION /
    ML_INFERENCE_LATENCY_SLO),
  ]
---

# ML Alerting Rules — Live ML Inference + Signal Lifecycle

> **STATUS** — Design doc landed 2026-05-08 by Tab 2 of Ikenna's 6-tab work-split, in service of the
> [`cefi_ml_may_23_2026.epic.md`](../../../plans/archive/cefi_ml_may_23_2026.epic.md) success criterion "model-drift
> alerting wired through alerting-service". Rule wiring lands on Tab 5; this doc is the design contract Tab 5 implements
> against alerting-service rule structure.
>
> **🟡 LIFT 2026-05-12 (ML-4 + ML-5 PRE_CUTOVER, slot 8 audit)** — gaps between this design contract and what
> alerting-service / ml-inference-service actually ship:
>
> - **The 4 AlertCodes (`ML_SIGNAL_STALE` / `ML_MODEL_DRIFT_DETECTED` / `ML_PNL_DEVIATION` / `ML_INFERENCE_LATENCY_SLO`)
>   are NOT in `alerting/codes.py`** as of 2026-05-12 — workspace grep returns 0 hits in `alerting-service/`. Tab 5
>   never wired them. Operator disposition required: ship via slot 4 / alerting-service owner before cutover OR demote
>   this doc to design-only with `**DEFERRED-AFTER-CUTOVER**` banner + named successor plan.
> - **`drift_monitor.py` ships a DIFFERENT signal**: it tracks **rolling prediction-accuracy drop**
>   (`retune_accuracy_drop_threshold`, default 0.15, over `retune_window_days`) and emits `MODEL_RETUNE_REQUESTED` (an
>   INTERNAL retune trigger, not an `AlertCode` fire / kill action). The PSI/KL input-feature drift path described in
>   Rule 2 below is **unbuilt design** — operator decision pending: (a) add PSI/KL path to `drift_monitor.py` + wire
>   `ML_MODEL_DRIFT_DETECTED` AlertCode, OR (b) re-baseline Rule 2 around the accuracy-drop signal that actually ships,
>   OR (c) deprecate Rule 2 to POST_CUTOVER.
>
> Tracked in `plans/archive/issues/codex_audit_ml_2026_05_12.md` ML-4 + ML-5 (PRE_CUTOVER, owner: ml-inference +
> alerting
>
> - slot 4).

## TL;DR

Live ML adds 4 new alerting rules layered on top of the live-pipeline tier-up rules
([`../../05-infrastructure/live-pipeline-architecture.md`](../../05-infrastructure/live-pipeline-architecture.md) §
"Live-pipeline alerting tier-up"):

1. **Signal staleness threshold** — no new strategy signal in N minutes when expected (catch dead inference)
2. **Model drift detection** — PSI / KL-divergence on input feature distribution vs training distribution
3. **P&L deviation** — live realised P&L vs simulated batch P&L deviation > threshold (catch live execution issues)
4. **ML inference latency SLO** — p99 inference latency > 50ms (catch model-loading regressions)

All four wire through Tab 5's alerting-service `AlertCode` taxonomy + KillSwitchBus rule structure
([`alert-code-taxonomy.md`](alert-code-taxonomy.md) extends with the codes below).

## AlertCode taxonomy entries (proposed for Tab 5)

| AlertCode                  | Tier | Description                                                             | KillSwitch action      |
| -------------------------- | ---- | ----------------------------------------------------------------------- | ---------------------- |
| `ML_SIGNAL_STALE`          | 1    | No new strategy signal in N minutes when expected per archetype cadence | Page on-call (no kill) |
| `ML_MODEL_DRIFT_DETECTED`  | 2    | PSI > 0.25 OR KL-divergence > 0.5 on any input feature for >30min       | `force_exit_only`      |
| `ML_PNL_DEVIATION`         | 2    | Realised P&L deviates > 200bps from simulated for the last 1h window    | `force_exit_only`      |
| `ML_INFERENCE_LATENCY_SLO` | 1    | p99 inference latency > 50ms over 10min window                          | Page on-call (no kill) |

## Rule 1 — Signal staleness threshold

**Trigger**: For each `(asset_group, archetype, model_family)`, if no `STRATEGY_DECISION_EMITTED` event arrives within
`expected_cadence * 1.5` (e.g. carry_staked_basis emits every 1h → trigger if no signal in 90min).

**Source**: `streaming.{asset_group}.strategy_decision_emitted` last-event-age via `StreamingHealthSnapshot`.

**Action**: Tier 1 page-only. Operator investigates: feature compute stuck? Model inference dead? Strategy logic guard
firing?

## Rule 2 — Model drift detection

**Trigger**: PSI (Population Stability Index) > 0.25 OR KL-divergence > 0.5 on any input feature for >30min sliding
window. Compute by accumulating live feature distribution vs training distribution snapshot (saved alongside model
artefact).

**Source**: `FEATURE_COMPUTED` events stream into a UTL `feature_drift_monitor.py` (greenfield helper; lift from any
inline drift code per the workspace "no double SSOT" rule). Monitor publishes `MODEL_DRIFT_SCORE` events;
alerting-service subscribes.

**Action**: Tier 2 `force_exit_only` — strategy refuses NEW signals (avoiding entries on out-of-distribution features),
allows EXIT signals to flatten existing positions. Operator decision: wait for distribution to revert OR retrain.

**Why force_exit_only not halt_strategy**: drift may be transient (regime shift; brief dislocation). Halting blocks
exit-side risk management. force_exit_only preserves operational continuity while preventing new exposure.

## Rule 3 — P&L deviation

**Trigger**: For each `(asset_group, archetype, model_family)`, compute `live_pnl_1h - simulated_pnl_1h`. If
`abs(deviation) > 200bps` of NAV for the last hour, fire.

**Source**: position-balance-monitor's `FILL_RECORDED` events (live) + execution-service matching engine's simulated
fills (batch shadow). Reuse the
[`unified_trading_library.batch_live_reconciler`](../../05-infrastructure/live-pipeline-architecture.md) primitive
shipped UTL@908b1647 — same shape, applied to P&L instead of OHLCV.

**Action**: Tier 2 `force_exit_only`. Operator investigates: market microstructure regime change? Adverse selection?
Latency degradation? Model misfit? Each diagnosis routes to a different remediation.

**Why this matters**: master plan Group F readiness criterion is batch=live. P&L deviation is the strongest signal that
batch≠live in production. Rule fires within 1h of the divergence so the operator has time to react before the divergence
compounds.

## Rule 4 — ML inference latency SLO

**Trigger**: p99 inference latency (from the `inference_latency_ms` field on `FEATURE_COMPUTED` events) > 50ms over a
10min window.

**Source**: `FEATURE_COMPUTED` event stream. Latency histogram per `(asset_group, model_family)`.

**Action**: Tier 1 page-only. Operator investigates: model artefact bloat? Memory pressure on features-service VM? Hot
swap to a stale model?

**Why 50ms**: candle cadence is 1m minimum (live OHLCV); 50ms is 0.08% of the cadence — comfortable budget. If a model
needs > 50ms, the model is too heavy for the live path; retrain a smaller variant.

## DART manual-override of ML trades

Per epic success criterion. DART (the operator UI) renders every ML-driven open position with a "manual override" button
that:

- Sends a `STRATEGY_OVERRIDE_INSTRUCTION` to strategy-service (UAC event)
- Strategy-service routes to execution-service as a `MANUAL_EXIT` order
- Position-balance-monitor flags the resulting fill with `override_reason="DART_MANUAL"` so audit trail captures the
  human-in-the-loop decision

Override is tier 0 — pre-empts all ML signals on that position. Cooldown: 60min before ML can re-enter the same
instrument (configurable per archetype).

## Anti-patterns

- **Don't fire kill_switch on transient drift.** PSI > 0.25 needs >30min duration; spurious 1-tick drift noise must not
  page or kill.
- **Don't compute P&L deviation on absolute dollar values.** Always normalise to NAV / position-size-weighted basis
  points.
- **Don't bypass DART override cooldown.** Re-entering immediately after a manual exit defeats the purpose of the
  override.
- **Don't put ML rules in a separate alerting service.** All alerts go through the same alerting-service rule structure;
  ML rules are just additional `AlertCode` entries.

## Cross-references

- Epic: [`cefi_ml_may_23_2026.epic.md`](../../../plans/archive/cefi_ml_may_23_2026.epic.md)
- Sibling: [`alert-code-taxonomy.md`](alert-code-taxonomy.md) (Tab 5 extends with the 4 ML codes above)
- Foundation:
  [`../../05-infrastructure/live-pipeline-architecture.md`](../../05-infrastructure/live-pipeline-architecture.md)
- Live serving: [`../ml/cefi-ml-live-serving.md`](../../16-strategy-playbooks/ml/cefi-ml-live-serving.md)
- UTL primitive: `unified_trading_library.batch_live_reconciler` (UTL@908b1647)
