---
doc_type: issue
title: Trading Incident Alerting, Auto-Recovery, Human Escalation + Audit Operating Model
summary:
status: resolved-into-active-plans
nature: record
asset_group: [infrastructure]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-20
parent_epic: observability_master
resolved: 2026-05-23
parent: master_to_live_defi_2026_05_23
locked_by: live-defi-rollout
locked_since: 2026-05-23
priority: P2
---

> **✅ ARCHIVED 2026-05-27 `[unlock-plan]`** — CAPTURED — all 11 spawned plans shipped + archived under
> `plans/epics/observability_master.md`; operator-action residuals migrated to that epic's P3 block.
>
> Operator-authorized archival 2026-05-27 (issue-doc lifecycle: work shipped or fully captured in a named plan). Lock
> `live-defi-rollout` removed via `[unlock-plan]` in the archival commit.

> **🟢 RESOLVED-INTO-PLANS 2026-05-23**. This operator-supplied target operating model (sections §1-22) is the source
> for the disaster-recovery gap audit at
> [`../../audit/results/observability_disaster_recovery_audit_2026_05_23.md`](../../audit/results/observability_disaster_recovery_audit_2026_05_23.md).
> The audit spawned **11 active plans** under `parent_epic: observability_master` totalling ~86 cal AI-days. Per the
> Issue-Doc Lifecycle Discipline HARD RULE (`/codex/11-project-management/issue-doc-lifecycle.md`), this issue doc
> archives once all 11 plans flip to `status: complete`.
>
> **Spawned plans** (all carry `parent_epic: observability_master`):
>
> 1. [`incident_gateway_and_state_machine_2026_05_23`](../incident_gateway_and_state_machine_2026_05_23.md) — closes §3
>    #1, §6, §14
> 2. [`agent_recovery_controller_layer0_deterministic_2026_05_23`](../agent_recovery_controller_layer0_deterministic_2026_05_23.md)
>    — closes §3 #2, §11
> 3. [`ai_recovery_audit_signoff_agent_2026_05_23`](../ai_recovery_audit_signoff_agent_2026_05_23.md) — operator-added
>    Layer-1 LLM audit
> 4. [`reconciliation_age_tracking_and_escalation_2026_05_23`](../reconciliation_age_tracking_and_escalation_2026_05_23.md)
>    — closes §3 #3, §7
> 5. [`drawdown_liquidation_policy_and_strategy_risk_config_2026_05_23`](../drawdown_liquidation_policy_and_strategy_risk_config_2026_05_23.md)
>    — closes §3 #4, §8, §9
> 6. [`connectivity_dependency_buffer_policy_2026_05_23`](../connectivity_dependency_buffer_policy_2026_05_23.md) —
>    closes §3 #5, §10
> 7. [`audit_acknowledgement_sla_and_state_2026_05_23`](../audit_acknowledgement_sla_and_state_2026_05_23.md) — closes
>    §6, §20 #6/#7
> 8. [`independent_fallback_twilio_voice_2026_05_23`](../independent_fallback_twilio_voice_2026_05_23.md) — closes §3
>    #9, §12.4/§12.5
> 9. [`physical_pager_research_and_webhook_prototype_2026_05_23`](../physical_pager_research_and_webhook_prototype_2026_05_23.md)
>    — closes §3 #10, §13
> 10. [`incident_runbooks_and_evidence_store_2026_05_23`](../incident_runbooks_and_evidence_store_2026_05_23.md) —
>     closes §3 #6, §15, §17
> 11. [`deployment_ui_safety_ops_tab_2026_05_23`](../deployment_ui_safety_ops_tab_2026_05_23.md) — operator-added
>     manual-override UI
>
> **New codex SSOTs** (2026-05-23):
>
> - [`/codex/04-architecture/incident-gateway-state-machine.md`](/codex/04-architecture/incident-gateway-state-machine.md)
> - [`/codex/04-architecture/recovery-defence-in-depth-layers.md`](/codex/04-architecture/recovery-defence-in-depth-layers.md)
> - [`/codex/05-infrastructure/physical-pager-layer.md`](/codex/05-infrastructure/physical-pager-layer.md)
> - [`/codex/15-runbooks/alerting/audit-acknowledgement-flow.md`](/codex/15-runbooks/alerting/audit-acknowledgement-flow.md)
>
> **Audit instructions extended** (2026-05-23):
> [`plans/audit/instructions/observability_master_audit_instructions.md`](../../audit/instructions/observability_master_audit_instructions.md)
> now covers sections A-T including 10 E2E flow tests + 11 inter-plan handshake checks + 4 cross-domain composition
> checks + 5 operator-persona walkthroughs + 3 data-pipeline-correctness composition checks.

# Trading Incident Alerting, Auto-Recovery, Human Escalation, and Audit Operating Model

## 1. Purpose

This document defines the target operating model for production trading incidents across automated recovery agents,
trading risk controls, human alerting, audit acknowledgement, third-party incident tooling, physical fallback devices,
and runbooks.

It is designed for a 24/7 trading environment where automated systems must act immediately to reduce risk, while humans
remain accountable for reviewing material production events, investigating unresolved or unusual behaviour, and
acknowledging audit reports within defined time windows.

The core principle is:

> Automation acts first to protect capital. Humans are alerted when risk is live, unresolved, unusual, repeated, or
> material enough to require accountability.

This document should be handed to an engineering agent or internal auditor to compare against the current
infrastructure, repos, deployment configs, monitoring rules, incident tools, and runbooks.

---

## 2. Operating Philosophy

### 2.1 Humans should not be the first repair mechanism

The system should not rely on a sleeping human to restart services, resize machines, redeploy containers, fail over
feeds, cancel stale orders, or move a strategy into safe mode. Agents should handle pre-approved recovery actions
automatically.

Examples of actions that agents may perform without prior human approval:

- Restart a crashed service.
- Restart a failed container or pod.
- Redeploy a known-good previous image.
- Scale memory or CPU after an OOM event.
- Move a service to a larger machine.
- Fail over from a bad market data source to a backup source.
- Pause new order generation for a strategy.
- Cancel open orders where venue/order state is stale or unsafe.
- Disable a venue for a strategy or strategy group.
- Move a strategy into safe mode.
- Trigger read-only/reconciliation mode.
- Continue running unaffected strategies or execution threads where risk isolation is proven.

### 2.2 Human acknowledgement is still required after material events

Even when agents recover correctly, material production actions need a human acknowledgement and audit review.

Human acknowledgement is not always needed before action. In many cases, waiting for a human increases trading risk.

However, the system must preserve accountability by requiring a responsible human to acknowledge the incident report
within the appropriate SLA.

Default audit acknowledgement SLA:

- Material auto-action with recovery confirmed: human acknowledgement within 6 hours.
- Material auto-action with partial or uncertain recovery: immediate operational escalation.
- Critical unresolved risk: immediate wake-up escalation.

### 2.3 Not every restart should wake someone up

A clean restart, machine resize, or failover should not automatically wake a human if all of the following are true:

- No live capital risk remains.
- Recovery is confirmed.
- Positions reconcile.
- Open orders reconcile.
- Strategy state is consistent.
- Market data is fresh.
- The incident is not repeating.
- The event is within a pre-approved runbook.

But it should still create an audit event if it affected live trading infrastructure.

### 2.4 Human wake-up is for live, unresolved, unproven, or escalating risk

Humans should be woken up when one or more of the following are true:

- Positions remain unreconciled beyond the allowed buffer.
- Open orders cannot be confirmed or cancelled.
- PnL drawdown exceeds strategy-defined investigation or action thresholds.
- Liquidation occurs or liquidation risk becomes credible.
- Connectivity remains degraded beyond the expected recovery window plus buffer.
- Kill switch or safe mode fails.
- The agent cannot prove recovery.
- The system enters a repeated repair loop.
- The alerting provider is unavailable during a serious incident.
- A production action is unusual, outside the runbook, or high impact.

---

## 3. Target Architecture

### 3.1 Main components

The production incident stack should include the following components:

1. **Incident Gateway**
   - Central internal service that receives all production alerts and recovery events.
   - Owns severity classification, deduplication, routing, escalation, acknowledgement state, and audit linkage.
   - Avoids every microservice sending directly to Slack, SIGNL4, Better Stack, Twilio, or Pushover independently.

2. **Agent Recovery Controller**
   - Executes pre-approved remediation runbooks.
   - Handles restarts, redeploys, scaling, failover, safe mode, venue disablement, and close/cancel scripts.
   - Emits structured action reports to the Incident Gateway.

3. **Reconciliation Service**
   - Compares internal state against venue state.
   - Tracks positions, balances, orders, fills, fees, transfers, funding, borrowing, and collateral state.
   - Maintains age-based reconciliation status.

4. **Risk and PnL Monitor**
   - Tracks live PnL, drawdown, exposure, leverage, margin, collateral, liquidation distance, VaR-style thresholds, and
     strategy-specific risk limits.
   - Emits warning, investigation, close/flatten, and liquidation events.

5. **Connectivity Health Monitor**
   - Tracks internal and external dependency health.
   - Measures heartbeat age, feed lag, API error rate, WebSocket disconnects, message backlog, stale data, Pub/Sub lag,
     broker lag, database lag, and execution venue availability.

6. **Audit Event Store**
   - Durable store of incidents, agent actions, acknowledgements, reports, evidence, runbook versions, config hashes,
     and post-incident outcomes.
   - Should be queryable by incident ID, strategy, venue, environment, severity, service, date, and human owner.

7. **Primary Incident Provider**
   - One main external provider for phone/SMS/push escalation and on-call rotation.
   - Candidate providers: SIGNL4, Better Stack, Spike, or equivalent.

8. **Slack Notification Layer**
   - Used for low and medium-severity visibility, audit reports, operational summaries, and alert-provider-health
     warnings.
   - Should not be the only path for critical incidents.

9. **Independent Emergency Fallback**
   - A separate channel for severe incidents if the primary incident provider is unavailable.
   - Candidate fallback: Twilio direct voice/SMS, Pushover emergency priority, or a second lightweight provider.

10. **Physical Alert Layer**
    - Dedicated on-call phone, loud alarm/siren, backup SIM/GSM alarm, UPS-backed router/device, or satellite
      communicator for edge cases.
    - Used only for SEV0 or non-acknowledged severe incidents.

---

## 4. Event Flow

### 4.1 Normal auto-recovery flow

```text
Problem detected
  ↓
Service/risk/reconciliation monitor emits structured event
  ↓
Incident Gateway classifies event
  ↓
Agent Recovery Controller executes approved action
  ↓
Recovery checks run
  ↓
Incident Gateway updates state
  ↓
Notification sent according to severity
  ↓
Audit report generated
  ↓
Human acknowledgement required if material
```

### 4.2 Critical unresolved risk flow

```text
Problem detected
  ↓
Agent attempts protective action immediately
  ↓
Recovery cannot be proven or risk remains live
  ↓
Incident Gateway upgrades to SEV0
  ↓
Primary incident provider calls on-call human
  ↓
If no acknowledgement, escalate to secondary human
  ↓
If no acknowledgement, trigger fallback voice/SMS/push
  ↓
If still no acknowledgement, trigger physical alert layer
  ↓
Incident remains open until human acknowledges and risk state is resolved
```

### 4.3 Audit-only material event flow

```text
Material event occurs
  ↓
Agent acts and recovery is confirmed
  ↓
Incident Gateway creates audit incident
  ↓
Slack notification posted
  ↓
Human acknowledgement due within 6 hours
  ↓
If not acknowledged, escalate to responsible human
  ↓
If still not acknowledged, escalate to founder/responsible officer
```

---

## 5. Severity Model

Severity should be determined by live risk, recovery certainty, materiality, duration, and repetition.

### 5.1 SEV3 — Informational

Description:

- No live trading risk.
- No material production impact.
- Useful for operational visibility.

Examples:

- Non-production job failed.
- Backtest worker OOM occurred and recovered.
- Non-critical service restarted.
- Data job delayed but no live dependency affected.
- Agent performed a harmless maintenance action.

Routing:

- Slack only.
- No phone call.
- No physical alert.
- No immediate human acknowledgement.
- Include in periodic operational summary.

### 5.2 SEV2 — Auto-fixed, low live risk, material enough for audit

Description:

- Live production was affected, but recovery is confirmed.
- No immediate capital risk remains.
- Human should review later.

Examples:

- Live service restarted cleanly.
- Machine resized after OOM.
- Data feed failed over to backup.
- Strategy paused briefly and resumed after checks.
- Deployment rolled back automatically.
- Connectivity issue recovered within buffer.
- Reconciliation lag occurred but resolved before escalation threshold.

Routing:

- Slack notification.
- Audit incident created.
- Human acknowledgement required within 6 hours if live trading or production control plane was affected.
- Escalate if not acknowledged within SLA.

### 5.3 SEV1 — Material trading event or unresolved degradation

Description:

- Trading was materially affected, or risk protection is active but requires human investigation.
- System may continue trading in protected mode if isolation is proven.
- Human should actively investigate.

Examples:

- Execution service restarted during live trading.
- Venue disabled automatically.
- Strategy entered safe mode.
- Orders were cancelled automatically.
- PnL drawdown exceeded investigation threshold but not close-all threshold.
- Connectivity degraded beyond expected recovery window plus buffer.
- Reconciliation remained unresolved beyond buffer but risk is contained.
- Agent produced an investigation report requiring human review.

Routing:

- Slack notification.
- Primary incident provider alert.
- Phone/SMS/app alert depending on time, impact, and configured policy.
- Human acknowledgement required.
- Audit report due.
- Escalate to secondary human if no acknowledgement within configured operational window.

### 5.4 SEV0 — Critical live or unproven risk

Description:

- Capital may be at immediate risk.
- Recovery is not proven.
- System safety cannot be guaranteed.
- Human must be woken up.

Examples:

- Positions remain unreconciled beyond hard threshold.
- Open orders cannot be confirmed, cancelled, or reconciled.
- Kill switch failed or only partially succeeded.
- Liquidation occurred.
- Liquidation risk is credible or imminent.
- Unexpected account balance movement.
- Margin/collateral danger.
- Unknown exposure after disconnect.
- Agent is stuck in repeated repair loop.
- Critical dependency failure during live risk state.
- Primary incident provider down during a critical incident.

Routing:

- Slack notification.
- Primary incident provider phone call/SMS/push.
- Escalate to secondary human if no acknowledgement.
- Use independent fallback channel if primary provider cannot confirm delivery.
- Use physical alerting if no human acknowledgement.
- Keep escalating until acknowledged.

---

## 6. Human Acknowledgement Model

There are two separate acknowledgement types.

### 6.1 Operational acknowledgement

This means a human confirms they are actively investigating or taking ownership.

Required for:

- SEV0 always.
- SEV1 when unresolved or materially trading-impacting.
- Any incident where the system is in safe mode, degraded mode, or uncertain mode.

Operational acknowledgement should be fast. The exact SLA should be configured per severity and on-call schedule, but
SEV0 should escalate within minutes.

### 6.2 Audit acknowledgement

This means a human has reviewed the incident report after the system handled it.

Required for:

- Material live restarts.
- Production redeployments.
- Machine resize after live OOM.
- Venue disablement.
- Strategy pause/resume.
- Automatic order cancellation.
- Automatic close/flatten scripts.
- Liquidation event.
- PnL drawdown investigation.
- Reconciliation breach.
- Connectivity degradation beyond expected buffer.

Default SLA:

- Audit acknowledgement due within 6 hours.
- If not acknowledged within 6 hours, escalate to the next responsible human.
- If still not acknowledged, escalate to founder/responsible officer.

### 6.3 Incident state machine

Each incident should have explicit state transitions.

```text
DETECTED
AUTO_ACTION_STARTED
AUTO_ACTION_SUCCEEDED
AUTO_ACTION_FAILED
RECOVERY_VERIFICATION_STARTED
RECOVERY_CONFIRMED
RECOVERY_UNCERTAIN
SAFE_MODE_ACTIVE
HUMAN_OPERATIONAL_ACKED
AUDIT_REPORT_GENERATED
HUMAN_AUDIT_ACKED
ESCALATED
RESOLVED
CLOSED
```

The system must not treat `AUTO_ACTION_SUCCEEDED` as equivalent to `RESOLVED`.

A restart can succeed while reconciliation remains unresolved.

---

## 7. Reconciliation Policy

### 7.1 Principle

Unreconciled state should not immediately become a critical incident. There must be a buffer to allow normal venue
latency, API delays, fill timing, and reconciliation cycles.

However, unreconciled state must be age-tracked and escalated if it persists beyond allowed thresholds.

### 7.2 Required timestamp fields

Every reconciliation issue should include:

- `first_seen_at`
- `last_seen_at`
- `event_time`
- `venue_trade_time`
- `internal_trade_time`
- `last_successful_reconciliation_at`
- `unreconciled_age_seconds`
- `oldest_unreconciled_trade_age_seconds`
- `oldest_unreconciled_order_age_seconds`
- `oldest_unreconciled_position_age_seconds`

### 7.3 Reconciliation dimensions

The reconciliation service should separately track:

- Orders.
- Fills.
- Positions.
- Balances.
- Funding payments.
- Fees.
- Transfers.
- Borrow/lending balances.
- Collateral balances.
- Margin mode and leverage.
- Strategy-level allocation state.
- Account-level aggregate state.

### 7.4 Reconciliation escalation thresholds

Default policy:

```text
0–5 minutes unresolved:
  Internal warning only unless risk is obviously live.

5–15 minutes unresolved:
  Slack warning and agent investigation.

>15 minutes unresolved:
  SEV1. Human must acknowledge they are investigating.

>30 minutes unresolved, or any evidence of live capital risk:
  SEV0. Wake-up escalation.
```

These should be configurable by venue, strategy, instrument type, and account.

### 7.5 Immediate SEV0 overrides

Even before 15 minutes, escalate immediately to SEV0 if:

- There is unknown net exposure.
- Open orders may be live but cannot be confirmed.
- Kill switch cannot confirm cancellation.
- Venue reports balances inconsistent with internal state in a way that implies loss or liquidation risk.
- A position exists externally that internal state does not know about.
- A material balance movement is unexplained.
- Margin/collateral safety is uncertain.

### 7.6 Agent responsibilities for reconciliation incidents

For reconciliation incidents, the agent should:

1. Freeze new trading for affected strategy/venue/symbol if required.
2. Pull latest venue orders, fills, balances, positions, and account state.
3. Compare against internal ledger.
4. Identify whether the mismatch is likely due to lag, missing fill, duplicated fill, cancelled order uncertainty,
   funding/fee adjustment, transfer, liquidation, or API inconsistency.
5. Produce an investigation report.
6. Recommend whether to continue, pause, cancel orders, flatten, disable venue, or escalate.
7. Preserve evidence and raw API snapshots.

---

## 8. PnL Drawdown and Strategy Risk Policy

### 8.1 Principle

PnL drawdown should be strategy-configurable. Some strategies may automatically close all positions at defined
thresholds. Others may continue operating while requiring human review and agent investigation.

The alerting layer must not assume all drawdowns require immediate close-all.

The risk layer should distinguish:

- Expected volatility.
- Strategy-normal drawdown.
- Investigation-level drawdown.
- Human-action-level drawdown.
- Automatic risk-off or close-all drawdown.
- Liquidation-risk drawdown.

### 8.2 Required strategy config fields

Each live strategy should define:

```yaml
risk_thresholds:
  pnl_drawdown:
    observation_window: "strategy_specific"
    warning_threshold: null
    investigation_threshold: null
    human_escalation_threshold: null
    auto_pause_threshold: null
    auto_reduce_threshold: null
    auto_close_all_threshold: null
    liquidation_risk_threshold: null

  expected_drawdown_model:
    basis: "historical_backtest | live_volatility | VaR | ES | max_adverse_excursion | custom"
    confidence_level: null
    lookback_window: null
    regime_adjustment: null

  response_policy:
    allow_agent_investigation: true
    allow_auto_pause: true
    allow_auto_reduce: false
    allow_auto_close_all: false
    require_human_for_resume: true
```

### 8.3 Drawdown severity mapping

Default policy:

```text
Drawdown below warning threshold:
  No alert or dashboard only.

Warning threshold breached:
  Slack notification.
  No human wake-up.

Investigation threshold breached:
  Agent investigates and writes report.
  Slack alert.
  Audit event created.

Human escalation threshold breached:
  SEV1.
  Agent investigates concurrently.
  Human must acknowledge active investigation.

Auto-pause / auto-reduce threshold breached:
  Agent executes configured strategy response.
  Human acknowledgement required within 6 hours, or immediately if risk remains live.

Auto-close-all / liquidation-risk threshold breached:
  SEV0 unless the close-all has fully completed and risk is proven neutral.
```

### 8.4 Agent investigation report for drawdowns

The agent should produce a report covering:

- Strategy ID.
- Account and venue scope.
- Drawdown amount and percentage.
- Realised vs unrealised PnL.
- Time window.
- Market move context.
- Exposure before and after event.
- Open orders.
- Position concentration.
- Venue-specific issues.
- Data quality issues.
- Whether the drawdown matches expected strategy distribution.
- Whether signals behaved normally.
- Whether execution slippage contributed.
- Whether fees/funding/borrow costs contributed.
- Whether any risk limits were breached.
- Recommended action: continue, pause, reduce, close all, disable venue, or manual review.

### 8.5 Strategy-specific close-all scripts

Some strategies may define automatic close-all scripts. These should be configured per strategy, not globally assumed.

Required controls:

- Close-all script must be idempotent.
- It must be dry-run testable.
- It must have venue-specific order handling.
- It must understand reduce-only vs normal order semantics.
- It must account for derivatives, spot, options, margin, collateral, and cross-account hedges.
- It must generate a post-close reconciliation report.
- It must not accidentally close hedges belonging to another strategy.

---

## 9. Liquidation Policy

### 9.1 Principle

Liquidations should never be treated as normal or expected production behaviour.

If a liquidation occurs, the system may continue operating in protected mode where safe, but human acknowledgement and
investigation are required.

### 9.2 Liquidation event handling

Any actual liquidation should create at least a SEV1 event.

Escalate to SEV0 if:

- The liquidation is material.
- More liquidation risk remains.
- The cause is unknown.
- The strategy is still trading.
- Margin/collateral state is uncertain.
- Other accounts or venues may be affected.
- Internal state did not predict the liquidation risk.

### 9.3 Liquidation-risk handling

Credible liquidation risk should be SEV0 if delay could cause capital loss.

Examples:

- Margin ratio breaches configured hard threshold.
- Liquidation distance falls below configured threshold.
- Collateral transfer fails.
- Auto-deleveraging/insurance fund risk appears.
- Venue API cannot confirm margin state.
- Price gap exceeds model assumptions.

### 9.4 Required liquidation investigation report

The agent report should include:

- Venue.
- Account.
- Strategy.
- Instrument.
- Liquidated quantity.
- Liquidation price.
- Mark/index price path.
- Margin mode.
- Collateral balances before and after.
- Open orders before liquidation.
- Risk limits in force.
- Whether alerts fired before liquidation.
- Whether the strategy expected the risk.
- Whether close/reduce logic failed.
- Whether venue/API data was stale.
- Whether human escalation was triggered.
- Remediation recommendations.

---

## 10. Connectivity and Dependency Policy

### 10.1 Principle

Connectivity issues should be buffered according to expected recovery time and dependency criticality.

A transient disconnect should not wake a human. A dependency that remains degraded beyond expected recovery time plus
buffer should force human acknowledgement and investigation.

### 10.2 Dependency classes

Dependencies should be classified as:

1. **Execution-critical external**
   - Exchange REST APIs.
   - Exchange WebSockets.
   - Broker APIs.
   - Custody/wallet infrastructure.
   - Order gateways.

2. **Market-data critical external**
   - Primary market data feeds.
   - Backup market data feeds.
   - Venue order book streams.
   - Index/mark price feeds.

3. **Internal control plane**
   - Kubernetes/control plane.
   - Deployment system.
   - Config registry.
   - Secrets manager.
   - Feature flag service.
   - Agent orchestration system.

4. **Internal data plane**
   - Pub/Sub/Kafka/Redis streams.
   - Databases.
   - BigQuery/GCS sinks.
   - Feature stores.
   - Ledgers.
   - Reconciliation stores.

5. **Alerting and observability**
   - Primary incident provider.
   - Slack.
   - Twilio/Pushover fallback.
   - Logging backend.
   - Metrics backend.
   - Tracing backend.

### 10.3 Expected time plus buffer model

Each dependency should define:

```yaml
dependency_health_policy:
  dependency_id: null
  dependency_class: null
  expected_recovery_time_seconds: null
  warning_buffer_seconds: null
  human_investigation_buffer_seconds: 900
  hard_escalation_seconds: null
  fallback_available: true
  protected_mode_available: true
```

Default policy:

```text
Short transient issue:
  No human alert if fallback works and recovery is within expected time.

Expected time exceeded:
  Slack warning and agent investigation.

Expected time + 15 minutes exceeded:
  SEV1. Human must acknowledge active investigation.

Risk is live or fallback fails:
  SEV0. Wake-up escalation.
```

### 10.4 Connectivity examples

Examples that should eventually force human investigation:

- Exchange WebSocket disconnected longer than expected and backup is stale.
- REST API failure prevents order cancellation confirmation.
- Pub/Sub lag exceeds configured threshold for live trading topics.
- Redis/cache unavailable and system is relying on degraded path.
- Deployment system unavailable during auto-recovery.
- Secrets/config access fails for live services.
- Alerting provider API fails or billing disables account.
- Logs/metrics unavailable during a live incident.

---

## 11. Restart, OOM, Redeploy, and Scaling Policy

### 11.1 Principle

Restarts, redeploys, and scaling actions should be automated where runbook-approved.

They do not need prior human approval when delay increases risk or downtime.

They may require audit acknowledgement after the fact.

### 11.2 Clean restart policy

A clean restart should not wake a human if:

- The service restarts successfully.
- Health checks pass.
- No repeated crash loop occurs.
- Positions reconcile.
- Orders reconcile.
- Strategy state is restored or safely paused.
- Market data is fresh.

Routing:

- Slack if live service.
- Audit acknowledgement within 6 hours if material.

### 11.3 OOM policy

An OOM event should trigger:

1. Capture memory profile if possible.
2. Restart or redeploy service.
3. Optionally respawn larger machine/container.
4. Run recovery verification.
5. Check for repeated OOM loop.
6. Produce report.

Escalation:

```text
Single non-live OOM:
  SEV3.

Single live OOM with clean recovery:
  SEV2, audit acknowledgement within 6 hours.

Repeated OOM or recovery uncertain:
  SEV1.

OOM affecting execution while exposure/order state cannot be confirmed:
  SEV0.
```

### 11.4 Redeploy policy

Agent redeployments must include:

- Trigger reason.
- Previous version.
- New version.
- Config hash.
- Image digest.
- Environment.
- Services affected.
- Rollback status.
- Post-deploy health checks.
- Reconciliation status if live trading affected.

Production redeployments during live trading should always create an audit event.

### 11.5 Repeated repair loop policy

A repeated repair loop is dangerous because it may hide deeper instability.

Escalate if:

- Same service restarts more than N times in M minutes.
- Same strategy enters safe mode repeatedly.
- Same venue toggles enabled/disabled repeatedly.
- Same dependency fails repeatedly.
- Agent retries the same action without durable resolution.

Default:

```text
2 repeated repairs within short window:
  Slack + agent report.

3+ repeated repairs or material live impact:
  SEV1.

Repeated repair with uncertain capital/order/position state:
  SEV0.
```

---

## 12. Alert Provider and Notification Tooling

### 12.1 Recommended provider structure

Use one primary incident provider, not two full expensive providers by default.

Recommended structure:

```text
Primary incident provider:
  Better Stack, SIGNL4, Spike, or equivalent

Slack:
  Low/medium severity visibility and provider-health alerts

Independent fallback:
  Twilio direct calls/SMS or Pushover emergency priority

Physical fallback:
  Dedicated phone, GSM alarm, siren, UPS-backed device, or satellite device
```

### 12.2 Primary incident provider requirements

The primary provider must support:

- Incoming webhook/API alert creation.
- Phone call alerts.
- SMS alerts.
- Push notifications.
- On-call rotations.
- Escalation policies.
- Acknowledgement tracking.
- Outbound webhook/callback on acknowledgement or incident state changes.
- Metadata routing by severity, service, strategy, venue, and environment.
- Billing/account status visibility.
- Test incident creation.

### 12.3 Slack requirements

Slack should be used for:

- SEV3 and SEV2 notifications.
- Audit reports.
- Daily operational summaries.
- Primary alert provider degradation.
- Agent investigation reports.
- Runbook links.
- Human coordination during active incidents.

Slack should not be the only channel for SEV0.

Recommended Slack channels:

```text
#prod-alerts
#prod-audit
#prod-incidents-sev0
#prod-agent-actions
#prod-alerting-health
#prod-reconciliation
#prod-risk
#prod-deployments
```

### 12.4 Independent fallback requirements

The fallback channel should be independent enough that a failure in the primary provider does not also kill fallback
alerting.

Requirements:

- Separate account from primary provider.
- Separate billing method where possible.
- Separate API key storage.
- Direct API call path from Incident Gateway.
- Works even if primary provider API is down.
- Can call or repeatedly notify humans.
- Can be tested automatically.

Possible options:

- Twilio direct voice/SMS.
- Pushover emergency priority.
- GSM alarm with SMS trigger.
- Secondary lightweight provider.

### 12.5 Alert provider health checks

The Incident Gateway should continuously check:

- Can primary provider API be reached?
- Can a test incident be created?
- Did provider acknowledge receipt?
- Are escalation policies enabled?
- Is billing active?
- Are phone/SMS credits available if applicable?
- Did recent incidents trigger provider callbacks?
- Are on-call schedules populated?
- Are any users missing phone numbers or app tokens?

If primary provider health check fails:

```text
Slack alert to #prod-alerting-health
Incident Gateway enters fallback-ready mode
SEV0 incidents use independent fallback immediately
Audit incident created for alerting provider degradation
```

---

## 13. Physical Fallback Layer

### 13.1 Purpose

The physical layer protects against failures of normal phone-based alerting:

- Phone battery dead.
- Phone lost.
- Phone on silent or Focus/DND misconfigured.
- Mobile network outage.
- Push notifications delayed.
- User asleep and phone vibration insufficient.
- User travelling with poor signal.
- Alert provider failure.

### 13.2 Recommended physical setup

Minimum setup:

- Dedicated on-call phone.
- Different mobile network from main phone.
- Always plugged in.
- Loud ringtone.
- DND bypass configured.
- Battery optimisation disabled.
- Primary incident app installed.
- Pushover or fallback app installed.
- Kept near bed/desk.

Better setup:

- Dedicated on-call phone.
- Cellular smartwatch.
- UPS-backed router.
- 4G/5G backup router with different network.
- Local alarm device/siren.
- GSM alarm box with separate SIM.

Extreme setup:

- Satellite messenger or satellite phone/hotspot for travel/no-signal environments.
- Backup human rotation when primary person is travelling or unreachable.

### 13.3 When physical alerting should trigger

Physical alerting should not trigger for every incident.

Trigger physical alerting only when:

- SEV0 remains unacknowledged after primary and secondary escalation.
- Primary provider is down during a SEV0.
- No human acknowledgement within configured window for live unresolved risk.
- Liquidation risk is active and no human has acknowledged.
- Kill switch failed and no human acknowledged.
- Positions/orders remain unreconciled beyond hard threshold.

---

## 14. Incident Payload Schema

All services should emit structured events to the Incident Gateway.

### 14.1 Base incident event

```json
{
  "event_id": "uuid",
  "incident_key": "stable-dedupe-key",
  "timestamp": "2026-05-23T12:00:00Z",
  "environment": "prod",
  "severity_hint": "SEV1",
  "domain": "live_trading",
  "service": "execution-engine",
  "component": "order-router",
  "strategy_id": "cefi-mean-reversion-prod",
  "strategy_family": "mean_reversion",
  "venue": "binance",
  "account_id": "account-alias",
  "instrument_id": "BTC-USDT-PERP",
  "problem_type": "position_reconciliation_lag",
  "problem_summary": "Position mismatch persisted beyond buffer",
  "risk_state": "protected_mode",
  "capital_at_risk": true,
  "auto_action_allowed": true,
  "auto_action_taken": null,
  "recovery_confirmed": false,
  "human_operational_ack_required": true,
  "human_audit_ack_required": true,
  "audit_ack_due_at": "2026-05-23T18:00:00Z",
  "runbook_id": "RB-RECON-001",
  "dashboard_url": "https://...",
  "logs_url": "https://...",
  "kill_switch_url": "https://...",
  "config_hash": "sha256:...",
  "code_version": "git-sha-or-image-digest"
}
```

### 14.2 Agent action event

```json
{
  "event_id": "uuid",
  "parent_incident_key": "stable-dedupe-key",
  "timestamp": "2026-05-23T12:03:00Z",
  "agent_id": "agent-recovery-controller",
  "action_type": "resize_and_restart",
  "action_status": "succeeded",
  "runbook_id": "RB-OOM-001",
  "pre_action_state": {
    "service_status": "crashed",
    "risk_state": "unknown",
    "open_orders_known": false
  },
  "post_action_state": {
    "service_status": "healthy",
    "risk_state": "safe_mode",
    "open_orders_known": true
  },
  "recovery_verification": {
    "health_checks_passed": true,
    "positions_reconciled": true,
    "orders_reconciled": true,
    "market_data_fresh": true,
    "strategy_state_restored": false,
    "strategy_paused": true
  },
  "human_audit_ack_required": true,
  "report_url": "https://..."
}
```

### 14.3 Drawdown event

```json
{
  "event_id": "uuid",
  "timestamp": "2026-05-23T12:15:00Z",
  "environment": "prod",
  "strategy_id": "strategy-prod",
  "venue": "deribit",
  "account_id": "account-alias",
  "problem_type": "pnl_drawdown_threshold_breach",
  "drawdown": {
    "window": "24h",
    "realised_pnl": -10000,
    "unrealised_pnl": -18000,
    "total_pnl": -28000,
    "drawdown_pct": 4.2,
    "threshold_breached": "human_escalation_threshold",
    "expected_band": "outside_expected_distribution"
  },
  "configured_response": {
    "auto_pause": true,
    "auto_close_all": false,
    "agent_investigation": true,
    "human_required": true
  },
  "auto_action_taken": "strategy_paused",
  "human_operational_ack_required": true,
  "human_audit_ack_required": true
}
```

---

## 15. Required Runbooks

The following runbooks should exist before relying on this operating model.

### 15.1 Core incident runbooks

1. **RB-INC-001: SEV0 Incident Handling**
   - How to acknowledge.
   - How to check current risk.
   - How to identify affected strategies/accounts/venues.
   - How to confirm safe mode.
   - How to escalate.
   - How to close incident.

2. **RB-INC-002: SEV1 Investigation Handling**
   - How to review agent report.
   - How to confirm protected mode.
   - How to decide continue/pause/disable/close.
   - How to document outcome.

3. **RB-INC-003: Audit Acknowledgement Handling**
   - What counts as acknowledgement.
   - What must be reviewed.
   - How to sign off.
   - How to escalate if report is insufficient.

### 15.2 Reconciliation runbooks

4. **RB-RECON-001: Position Reconciliation Lag**
   - Check venue positions.
   - Check internal ledger.
   - Check fills and orders.
   - Identify oldest unreconciled item.
   - Apply buffer policy.
   - Decide safe mode vs continue.

5. **RB-RECON-002: Open Order Uncertainty**
   - Pull open orders from venue.
   - Attempt cancellation.
   - Confirm cancel state.
   - Handle unknown order state.
   - Escalate if cancel cannot be proven.

6. **RB-RECON-003: Balance/Collateral Mismatch**
   - Pull balances.
   - Check transfers, funding, fees, borrowing.
   - Check account movements.
   - Check collateral and margin mode.
   - Escalate unexplained movement.

### 15.3 Risk and PnL runbooks

7. **RB-RISK-001: Strategy Drawdown Investigation**
   - Determine threshold breached.
   - Compare to expected drawdown model.
   - Attribute realised/unrealised PnL.
   - Check exposure, execution, slippage, fees, funding, data quality.
   - Recommend continue/pause/reduce/close.

8. **RB-RISK-002: Liquidation Event**
   - Confirm liquidation details.
   - Check remaining risk.
   - Freeze or reduce affected strategy.
   - Generate liquidation report.
   - Escalate to human.

9. **RB-RISK-003: Liquidation Risk / Margin Danger**
   - Check margin ratio.
   - Check liquidation distance.
   - Check collateral availability.
   - Reduce or close if configured.
   - Escalate SEV0 if risk remains.

10. **RB-RISK-004: Strategy Safe Mode**
    - Define safe mode per strategy.
    - Pause new orders.
    - Cancel or retain orders according to strategy policy.
    - Confirm positions and hedges.
    - Define human requirements for resume.

### 15.4 Connectivity runbooks

11. **RB-CONN-001: Exchange WebSocket Degradation**
    - Check disconnect duration.
    - Check backup feed.
    - Check order book freshness.
    - Decide whether to pause strategy.

12. **RB-CONN-002: Exchange REST API Failure**
    - Check order placement/cancellation capability.
    - Check rate limits.
    - Check authentication.
    - Escalate if cancellation cannot be confirmed.

13. **RB-CONN-003: Internal Messaging Lag**
    - Check Pub/Sub/Kafka/Redis lag.
    - Check consumers.
    - Check dead letter queues.
    - Fail over or scale consumers.

14. **RB-CONN-004: Database/Storage Degradation**
    - Check ledger writes.
    - Check read-only mode.
    - Check replay/recovery capability.
    - Decide whether trading can continue safely.

15. **RB-CONN-005: Alert Provider Failure**
    - Confirm provider API status.
    - Trigger fallback route.
    - Notify Slack.
    - Verify phone/SMS fallback.
    - Create audit incident.

### 15.5 Deployment and infrastructure runbooks

16. **RB-DEPLOY-001: Production Rollback**
    - Identify version.
    - Roll back to known-good image.
    - Verify service health.
    - Verify trading state.
    - Create audit report.

17. **RB-INFRA-001: OOM Recovery**
    - Capture memory profile.
    - Restart/resize.
    - Check repeated OOM.
    - Verify reconciliation.
    - Create audit report.

18. **RB-INFRA-002: Machine/Node Failure**
    - Cordon node.
    - Move workload.
    - Verify service recovery.
    - Verify risk state.

19. **RB-INFRA-003: Secret/Config Failure**
    - Verify config registry.
    - Verify secret access.
    - Prevent unsafe default config.
    - Escalate if production config unknown.

### 15.6 Physical alerting runbooks

20. **RB-ALERT-001: Dedicated On-Call Phone Setup**
    - Carrier.
    - Apps.
    - DND bypass.
    - Charger/UPS.
    - Test schedule.

21. **RB-ALERT-002: Physical Siren/GSM Alarm Setup**
    - Trigger path.
    - SIM provider.
    - Power backup.
    - Test procedure.

22. **RB-ALERT-003: Satellite / No-Signal Fallback**
    - When used.
    - Who carries it.
    - Test procedure.
    - Known limitations.

---

## 16. Configuration Requirements

### 16.1 Strategy-level config

Each strategy must define:

- Trading mode: live, paper, simulation.
- Capital allocation.
- Venue/account scope.
- Instrument scope.
- Drawdown thresholds.
- Exposure limits.
- Liquidation-risk thresholds.
- Safe mode behaviour.
- Close-all behaviour.
- Human resume requirements.
- Agent action permissions.
- Reconciliation buffers.
- Connectivity buffers.
- Alert severity overrides.

### 16.2 Venue-level config

Each venue must define:

- Expected API latency.
- Expected WebSocket reconnect time.
- Reconciliation polling frequency.
- Order cancellation semantics.
- Reduce-only behaviour.
- Position mode.
- Margin mode.
- Liquidation data availability.
- Backup data source.
- Rate limits.
- Known quirks.

### 16.3 Dependency-level config

Each internal/external dependency must define:

- Criticality.
- Expected recovery time.
- Human investigation buffer.
- Fallback path.
- Protected mode behaviour.
- Owner.
- Runbook.
- Test method.

### 16.4 Alert routing config

The Incident Gateway must be able to route by:

- Severity.
- Environment.
- Service.
- Strategy.
- Venue.
- Account.
- Asset class.
- Time of day.
- On-call rota.
- Whether recovery is confirmed.
- Whether human acknowledgement is required.
- Whether primary provider is healthy.

---

## 17. Dashboards and Evidence

Each incident should link to dashboards and evidence.

Required dashboards:

- Global live trading health.
- Strategy health.
- Venue connectivity.
- Execution health.
- Open orders.
- Position reconciliation.
- Balance/collateral reconciliation.
- PnL and drawdown.
- Margin and liquidation risk.
- Agent actions.
- Deployment history.
- Alert provider health.
- Human acknowledgement queue.

Required evidence capture:

- Raw venue API snapshots.
- Internal ledger snapshot.
- Order/fill records.
- Position records.
- Balance records.
- Logs.
- Metrics.
- Traces if available.
- Agent action logs.
- Config hash.
- Code/image version.
- Runbook version.
- Human acknowledgement trail.

---

## 18. Agent Audit Checklist

The auditing agent should inspect the current system and answer the following.

### 18.1 Architecture

- Does an Incident Gateway exist?
- Do services send structured events to it rather than directly spamming providers?
- Is there a durable incident/audit store?
- Is there an agent recovery controller?
- Are agent actions tied to runbook IDs?
- Are recovery checks separate from action completion?

### 18.2 Severity and routing

- Are SEV0/SEV1/SEV2/SEV3 definitions implemented?
- Does routing depend on recovery certainty and live risk, not only service status?
- Is Slack used for low/medium visibility?
- Is the primary incident provider used for human escalation?
- Is physical alerting reserved for SEV0/no-ack cases?
- Is audit acknowledgement separated from operational acknowledgement?

### 18.3 Reconciliation

- Are positions, orders, fills, balances, fees, funding, transfers, collateral, and margin reconciled?
- Are unreconciled items timestamped?
- Is oldest unreconciled item age tracked?
- Is there a 15-minute human investigation threshold?
- Are immediate SEV0 overrides implemented?
- Does the system freeze/pause affected scope when reconciliation risk is live?

### 18.4 PnL and drawdown

- Does each strategy define expected drawdown thresholds?
- Are warning, investigation, human escalation, pause, reduce, and close-all thresholds separate?
- Does a drawdown investigation agent report exist?
- Can strategy-specific close-all scripts be executed safely?
- Is resume after drawdown controlled by strategy config?

### 18.5 Liquidation

- Are liquidation events detected?
- Is any liquidation at least SEV1?
- Is liquidation risk detected before liquidation?
- Does the system produce liquidation investigation reports?
- Are liquidation events impossible to silently ignore?

### 18.6 Connectivity

- Are internal and external dependencies classified?
- Does each dependency define expected recovery time?
- Is expected time plus 15 minutes used to force human investigation?
- Are fallback paths tested?
- Does the system degrade safely when dependencies fail?

### 18.7 Restarts, OOM, redeploys

- Are live restarts audited?
- Are OOM events captured and investigated?
- Can agents resize or redeploy safely?
- Is repeated repair loop detection implemented?
- Are production redeploys tied to image digest/config hash?

### 18.8 Third-party tooling

- Is there one primary incident provider?
- Are phone/SMS/push/on-call rotations configured?
- Are Slack channels configured?
- Is independent fallback configured?
- Are primary provider health checks configured?
- Is billing/account health monitored?
- Are test incidents sent regularly?

### 18.9 Physical fallback

- Is there a dedicated on-call phone?
- Is it on a different network?
- Is it always charged?
- Is DND bypass configured?
- Is there a local siren/GSM alarm for SEV0 no-ack?
- Is router/alert device power backed up?
- Is satellite/no-signal fallback considered for travel?

### 18.10 Runbooks

- Do all required runbooks exist?
- Are runbooks versioned?
- Are runbooks tested?
- Are runbooks executable by agents where appropriate?
- Do runbooks define human handoff points?
- Do runbooks define evidence to capture?

---

## 19. Implementation Roadmap

### Phase 1 — Minimum safe alerting

- Choose one primary incident provider.
- Create Slack channels.
- Implement Incident Gateway skeleton.
- Route SEV2/SEV3 to Slack.
- Route SEV0/SEV1 to primary provider.
- Implement audit acknowledgement queue.
- Add 6-hour audit acknowledgement SLA.
- Configure on-call rotation.
- Add dedicated on-call phone.

### Phase 2 — Trading-specific risk escalation

- Add reconciliation age tracking.
- Implement 15-minute reconciliation escalation.
- Add immediate SEV0 overrides.
- Add PnL drawdown threshold config.
- Add agent drawdown investigation report.
- Add liquidation event detection and report.
- Add connectivity expected-time-plus-buffer policy.

### Phase 3 — Auto-recovery and evidence

- Connect Agent Recovery Controller.
- Add runbook IDs to actions.
- Separate action success from recovery confirmation.
- Capture raw evidence snapshots.
- Add config hash/code version to incidents.
- Implement repeated repair loop detection.
- Add post-action reconciliation checks.

### Phase 4 — Fallback and physical resilience

- Add primary provider health checks.
- Add fallback Twilio/Pushover route.
- Add SEV0 no-ack physical alert.
- Add UPS-backed alert hardware.
- Add 4G/5G backup network.
- Define satellite/no-signal travel policy.

### Phase 5 — Governance and regular testing

- Run monthly game days.
- Test SEV0 wake-up flow.
- Test provider-down fallback.
- Test physical alert device.
- Test liquidation-risk scenario.
- Test reconciliation stale-order scenario.
- Test drawdown investigation report.
- Review missed/noisy alerts.
- Update thresholds and runbooks.

---

## 20. Key Design Decisions

1. Use one primary incident provider, not two full alert providers by default.
2. Use Slack for low/medium visibility and provider-health warnings.
3. Use independent fallback only for primary provider failure or SEV0 no-ack.
4. Agents can act immediately where delay increases risk.
5. Human approval is not required before ordinary approved recovery actions.
6. Human acknowledgement is required after material production actions.
7. Audit acknowledgement SLA defaults to 6 hours.
8. Unreconciled positions/orders should use age buffers, not instant escalation.
9. A 15-minute unresolved reconciliation/connectivity threshold should force human investigation.
10. PnL drawdown thresholds are strategy-specific.
11. Liquidations are never normal and always require human investigation.
12. Physical alerting is reserved for SEV0 or severe no-ack cases.
13. Recovery verification must be separate from action completion.
14. Every material incident must link to evidence, config version, code version, and runbook version.

---

## 21. Definition of Done

The operating model is implemented when:

- All live trading services emit structured incident events.
- Incident Gateway classifies and routes alerts.
- Primary provider handles on-call phone/SMS/push escalation.
- Slack handles audit and low-severity visibility.
- Independent fallback exists for provider failure.
- Physical fallback exists for SEV0 no-ack.
- Reconciliation issues are age-tracked.
- Drawdown thresholds are strategy-specific.
- Liquidation events cannot be ignored.
- Connectivity issues escalate after expected time plus buffer.
- Agent actions are tied to runbooks.
- Recovery confirmation checks trading state, not just process health.
- Audit acknowledgement within 6 hours is enforced.
- Runbooks exist and are tested.
- Game days prove the escalation waterfall works.

---

## 22. Agent Instruction Summary

When auditing the current system, compare implementation against this target model and produce:

1. A gap list by component.
2. A gap list by severity/routing rule.
3. A gap list by runbook.
4. A gap list by strategy config field.
5. A gap list by dependency health policy.
6. A gap list by physical/fallback alerting.
7. A proposed implementation plan ranked by capital-risk reduction.
8. A list of unclear assumptions requiring human decision.

Priority order for remediation:

1. SEV0 wake-up path.
2. Reconciliation age tracking and escalation.
3. Primary provider plus fallback health checks.
4. Audit acknowledgement SLA.
5. Drawdown investigation and strategy risk configs.
6. Liquidation detection/reporting.
7. Physical alerting.
8. Game-day testing.
