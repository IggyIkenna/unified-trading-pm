---
doc_type: codex-ssot
title: Recovery Defence-In-Depth Layers (5+1)
summary:
  The 5+1 layered recovery model — Layer-0 deterministic Python (closed-set 10 scripts, never LLM on the critical path),
  Layer-1 LLM audit-signoff (parallel; can DISPUTE), Layer-1.5 LLM-as-backup-actuator, Layer-2 PagerDuty, Layer-3
  Twilio, Layer-4 physical pager, Layer-5 human audit-ack (required even on APPROVED), Layer-M operator override; each
  layer independent, all emit to the Incident Gateway.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, alerting-service, deployment-service, deployment-ui, execution-service, strategy-service]
scope: [engineer, admin]
tags: [recovery, self-healing, escalation, kill-switch, alerting, orchestrator]
related:
  [
    /codex/04-architecture/incident-gateway-state-machine.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
    /codex/04-architecture/kill-switch-circuit-breaker.md,
    /codex/05-infrastructure/disaster-recovery.md,
    /codex/04-architecture/safety-ops-tab.md,
  ]
created: 2026-05-23
authoritative_for: [defence-in-depth-layers, layer-0-scripts, llm-audit-signoff]
referenced_by:
  [
    /codex/03-observability/alerting.md,
    /codex/04-architecture/incident-gateway-state-machine.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
    /codex/04-architecture/kill-switch-circuit-breaker.md,
    /codex/05-infrastructure/disaster-recovery.md,
    /codex/15-runbooks/physical-pager-layer.md,
    /codex/15-runbooks/alerting/audit-acknowledgement-flow.md,
    plans/archive/incident_gateway_and_state_machine_2026_05_23.plan.md,
    plans/active/agent_recovery_controller_layer0_deterministic_2026_05_23.md,
    plans/archive/ai_recovery_audit_signoff_agent_2026_05_23.plan.md,
  ]
owner:
last_reviewed: 2026-05-23
code_refs:
---

# Recovery Defence-In-Depth Layers (5+1)

> SSOT for the layered recovery model. Codified 2026-05-23 per operator directive: "recovery scripts as first line of
> defence, then ai/lmm automations as next line, then slack, pager duty style cascading flow management on escalations,
> and twillio then pager and final human gates for audit report acks and ultimate disaster human intervention".

## Principle

Multiple independent layers fire in parallel. Each layer is independently sufficient for its scope; together they form
belt-and-suspenders coverage. The LLM agent NEVER sits on the critical path of Layer-0 — Layer-0 is deterministic
Python. The LLM is a parallel observer (Layer-1) and a backup actuator (Layer-1.5) when Layer-0 fails.

## The 5+1 layer stack

```
[Layer 0]  Deterministic Python scripts (closed-set 10 actions, idempotent + dry-run + runbook-ID-tagged)
              ↓ AgentActionEvent emitted (PubSub `agent-recovery-actions`)
[Layer 1]  LLM Recovery-Audit-Signoff agent (agent-orchestrator role=custom, runs in parallel, NOT on critical path)
              │  • audits every Layer-0 action
              │  • writes RecoveryAuditSignoff doc (verdict ∈ APPROVED / APPROVED_WITH_NOTES / ESCALATE_TO_HUMAN /
              │    DISPUTE_AUTOMATED_ACTION)
              │  • can DISPUTE → forces SAFE_MODE_ACTIVE + SEV0 escalation
              ↓
[Layer 1.5] LLM-as-backup-actuator (fires only when Layer-0 action_status=FAILED)
              │  • invokes Layer-0 scripts via wrapper `llm_invoke_layer0.py`
              │  • CLOSED-SET authority — no arbitrary shell
              ↓ if Layer-1.5 also fails OR Layer-0 + Layer-1 succeed but recovery NOT confirmed
[Layer 2]  PagerDuty cascading escalation (primary on-call → secondary → founder per SLA matrix)
              │  • Telegram notification in parallel
              │  • channel routing by severity per LIVE_ALERT_RULES (UAC)
              ↓ if no ack within window OR PagerDuty API down
[Layer 3]  Twilio direct voice + SMS (permanent fallback — works when PagerDuty is down + survives phone-on-DND)
              │  • separate billing + separate API → independent of Layer-2
              │  • voice call narrates incident summary via TwiML <Say voice=alice>
              ↓ if no ack within founder-after window OR primary phone unreachable
[Layer 4]  Physical pager device (operator-purchased — LoRa pager / dedicated SIM phone / GSM siren / sat messenger)
              │  • independent network from primary phone
              │  • wall-mounted GSM siren survives operator-phone-dead entirely
              │  • Twilio voice bridge is the permanent equivalent until device is procured
              ↓ at AUDIT_REPORT_GENERATED transition
[Layer 5]  Human audit ack (6h default; per-severity override; secondary-human + founder escalation)
              │  • operational ack ≠ audit ack (distinct buttons in DART Safety Ops tab)
              │  • EVEN APPROVED LLM verdict requires human audit ack (operator HARD RULE 2026-05-23)
[Layer M]  Operator manual override (DART Safety Ops tab — orthogonal to layers 0-5; can act at any layer's scope)
              • typed-confirm-string required per action (e.g. CANCEL_ALL_binance)
              • manual actions flow THROUGH the Incident Gateway (provenance=MANUAL_OPERATOR)
              • LLM agent signs off on manual actions too — full audit trail
```

## Per-layer detail

### Layer 0 — Deterministic Python (no AI, no LLM)

Owned by `plans/active/agent_recovery_controller_layer0_deterministic_2026_05_23.md`. Closed-set 10 scripts in
`deployment-service/scripts/recovery/`:

| Script                         | Action                                           | Runbook       |
| ------------------------------ | ------------------------------------------------ | ------------- |
| `restart_service.py`           | Cloud Run revision flip OR GCE systemctl restart | RB-INFRA-001  |
| `restart_container.py`         | Cloud Run revision OR Docker restart             | RB-INFRA-001  |
| `redeploy_known_good.py`       | Flip Cloud Run traffic to previous revision      | RB-DEPLOY-001 |
| `resize_machine_after_oom.py`  | gcloud compute instance resize                   | RB-INFRA-001  |
| `failover_feed.py`             | MTDS handler primary→backup feed                 | RB-CONN-001   |
| `pause_strategy.py`            | strategy-service pause endpoint                  | RB-RISK-004   |
| `cancel_open_orders.py`        | execution-service cancel-all-orders              | RB-RECON-002  |
| `disable_venue.py`             | circuit-breaker force-open                       | RB-CONN-001   |
| `enter_safe_mode.py`           | strategy-service safe-mode entry                 | RB-RISK-004   |
| `enter_readonly_recon_mode.py` | service reads but rejects writes                 | RB-CONN-004   |

Each MUST: support `--dry-run`, emit AgentActionEvent (STARTED + SUCCEEDED|FAILED), check RepeatedRepairLoopDetector and
bail at 3+ identical actions in 15min, be idempotent, be runbook-ID-tagged.

Wrapped existing safety actions (don't duplicate — wrap the entry point):

- execution-service `kill_switch.activate()` / `deactivate()`
- alerting-service `circuit_breaker.force_open()` / `force_close()`
- strategy-service `safe_mode.enter()` / `exit()`
- execution-service `cancel_all_for_venue()`

### Layer 1 — LLM recovery-audit-signoff agent

> **✅ PRODUCER REWIRED 2026-08-13 — the Layer-1 producer is now the standalone
> `deployment-service/scripts/recovery/recovery_audit_signoff_producer.py`.** The AO `recovery-audit` **worker-role**
> remains removed (correct AO-roster outcome — do NOT restore `agents/recovery-audit.md`). The standalone producer
> consumes PubSub `agent-recovery-actions` (topic + `-sub` subscription provisioned in
> `deployment-service/terraform/gcp/main.tf`) and POSTs `RecoveryAuditSignoff`s to the live alerting-service
> `POST /safety-ops/signoffs` ingest. The **consuming half of Layer-1 is fully live**: alerting-service ingests signoffs
> + acts on `DISPUTE_AUTOMATED_ACTION`→SAFE_MODE / `ESCALATE_TO_HUMAN`→shortened-ack
> (`alerting_service/gateway/gateway_state.py`), and the DART Safety-Ops verdict feed renders them (real producer data;
> `_mock_signoffs()` only in `CLOUD_MOCK_MODE=true`). The producer's verdict is a **closed deterministic rule set**
> (FAILED/BLOCKED_BY_LOOP_DETECTOR/verification-incomplete → ESCALATE_TO_HUMAN; verified-success → APPROVED;
> success-no-verification → APPROVED_WITH_NOTES); it does NOT emit DISPUTE_AUTOMATED_ACTION (that judgment is left to a
> future LLM/human pass). Tracking:
> `plans/active/issues/ao_recovery_audit_layer1_deleted_2026_07_15.md`. The description below is the design contract.

Design owner: `plans/archive/ai_recovery_audit_signoff_agent_2026_05_23.plan.md` (archived). Prior agent template
`agent-orchestrator/agents/recovery-audit.md` (deleted) — superseded by the standalone producer (NOT an AO worker-role).
Registered contract: `role: custom, label: recovery-audit-signoff`.

Polls PubSub `agent-recovery-actions` (via the `agent-recovery-actions-sub` subscription); for each terminal
AgentActionEvent decides a deterministic verdict from the event payload (closed rule set — see the banner above) and
POSTs the RecoveryAuditSignoff to the live alerting-service `POST /safety-ops/signoffs`, which records it into the
Incident Gateway state + drives the verdict-mandated gateway reaction. (The original design wrote signoffs to GCS at
`gs://<kill-switch-audit>/incidents/{date}/{key}/signoffs/{event_id}.json`; the rewire routes through the HTTP ingest
so the gateway + DART feed see each signoff immediately.)

`SignoffVerdict` StrEnum (closed 4-set):

- `APPROVED` — automation was right; no operator action required beyond audit-ack.
- `APPROVED_WITH_NOTES` — automation was right; notes surface in DART as info banner.
- `ESCALATE_TO_HUMAN` — automation may have been right but is ambiguous; audit-ack-due-at shortened to 1h.
- `DISPUTE_AUTOMATED_ACTION` — automation was wrong; gateway forces SAFE_MODE_ACTIVE + SEV0 escalation + invokes
  `pause_strategy` for the affected strategy.

### Layer 1.5 — LLM-as-backup-actuator

When Layer-0 returns `action_status=FAILED`, the LLM agent invokes the same closed-set scripts via
`deployment-service/scripts/recovery/llm_invoke_layer0.py`. Validates `action_type` against the
`RecoveryScriptRegistry`; emits AgentActionEvent with `provenance=LLM_LAYER15`. **No arbitrary shell.** Only the
wrapper.

### Layer 2 — PagerDuty cascading escalation

Existing infrastructure (Phase 4 of `alerting_service_live_rules_2026_05_07.md` shipped Telegram primary; PagerDuty
deferred-per-operator pending Phase 7 quietness baseline). Per-severity SLA matrix in `audit-acknowledgement-flow.md`.

### Layer 3 — Twilio voice/SMS (permanent fallback)

Owned by `plans/archive/independent_fallback_twilio_voice_2026_05_23.plan.md` (shipped 2026-05-23). Twilio account is
dedicated (not shared with any other workspace tool). Triggers automatically on:

- Primary provider health probe failure (router enters fallback_mode).
- SEV0 incident routing (defence-in-depth — fires alongside PagerDuty + Telegram).
- audit-ack escalation reaches founder_after_seconds window.

Voice survives phone-on-DND (operator configures Twilio number as a recognized contact).

### Layer 4 — Physical pager

Owned by `plans/active/physical_pager_research_and_webhook_prototype_2026_05_23.md`. Recommended: dedicated SIM phone
(different carrier) + wall-mounted GSM siren (different SIM). Triggers ONLY by the 5 closed-set conditions per
`disaster_recovery.md` §13.3 (SEV0 unacked after primary + secondary, primary provider down during SEV0, liquidation
risk + no ack, kill switch failed + no ack, reconciliation breach beyond hard threshold).

Until device arrives: Twilio voice serves as Layer-4 bridge. After device arrives: BOTH fire (defence-in-depth).

### Layer 5 — Human audit ack

Owned by `plans/active/audit_acknowledgement_sla_and_state_2026_05_23.md`. 6h default SLA + per-severity override.
**Even APPROVED LLM verdict requires the human ack** — operator HARD RULE 2026-05-23. Operational ack ≠ audit ack
(distinct buttons in DART Safety Ops tab).

### Layer M — Operator manual override

Owned by `plans/active/deployment_ui_safety_ops_tab_2026_05_23.md`. DART Safety Ops tab + deployment-ui mirror. Every
Layer-0 + Layer-1 action surfaces as a button with typed-confirm-string. Manual actions flow through Incident Gateway
with `provenance=MANUAL_OPERATOR` — full audit trail + LLM signoff applies.

## Out of scope: agent-orchestrator's own FailoverLoop

`agent-orchestrator/server/failover.py`'s `FailoverLoop` (re-routes AGENT dev-fleet task-worker assignments off an
offline VM host) is **NOT** one of the 5+1 layers above and does not participate in this incident-recovery stack — it is
a separate, orthogonal self-heal mechanism scoped to the agent-orchestrator dev fleet itself, not to
trading/venue/service incidents. Don't confuse it with `failover_feed.py` (Layer 0, MTDS primary→backup feed failover)
in the table above — same word, different system, different owner.

**Status**: dormant-but-kept (operator ruling 2026-07-20). It has never fired in production and `fleet_registry.json` is
empty under the current single-VM topology, so today it is not a live recovery layer for anything. It is being kept (not
deleted) because multi-VM is expected to return. Do not cite it as an active recovery mechanism until it has been
re-enabled per its own checklist — see
[`/codex/15-runbooks/agent-orchestrator-failover-re-enable-checklist.md`](/codex/15-runbooks/agent-orchestrator-failover-re-enable-checklist.md).

## Failure modes covered

| Failure                                            | First layer that catches                                                                          |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| Transient venue API 5xx                            | Layer 0 (retry/reconnect via classify_venue_error)                                                |
| Venue down > expected_recovery_time                | Layer 0 (failover_feed) + Layer 2 PagerDuty if not auto-recoverable                               |
| Service OOM, clean restart                         | Layer 0 (resize_machine_after_oom) + Layer 1 LLM signoff APPROVED + Layer 5 audit-ack             |
| Service OOM, repeated 3+ in 15min                  | Layer 0 RepeatedRepairLoopDetector blocks 4th + escalates to SEV0 + Layer 2                       |
| Recon breach > 30min                               | Layer 0 (freeze) + Layer 2 + Layer 1 ESCALATE_TO_HUMAN                                            |
| Recon immediate-SEV0 (one of 7 overrides)          | Direct SEV0 routing → Layer 2 + Layer 3 + Layer 5 with shortened SLA                              |
| Drawdown breach (auto-close-all threshold)         | Layer 0 (close-all script per strategy) + Layer 1 signoff + Layer 5 with require_human_for_resume |
| Liquidation event                                  | LiquidationEventDetector → SEV1 minimum → Layer 2 + Layer 1                                       |
| Liquidation-risk (margin/ADL/etc — 6 triggers)     | LiquidationRiskPredetector → SEV0 → Layer 2 + Layer 3                                             |
| PagerDuty API outage during SEV0                   | Layer 3 Twilio voice                                                                              |
| Operator phone dead / DND / silent                 | Layer 3 Twilio voice (DND bypass) → Layer 4 physical pager / GSM siren                            |
| Operator unreachable entirely                      | Layer 5 founder escalation → Layer 4 physical pager + Twilio voice to founder                     |
| Automation was WRONG (race condition / stale data) | Layer 1 LLM DISPUTE verdict → forces SAFE_MODE + SEV0                                             |
| Layer-0 script fails to execute                    | Layer 1.5 LLM-as-backup-actuator                                                                  |

## Invariants

1. **No layer is on the critical path of another**: Layer-0 runs without waiting for Layer-1; Layer-2 fires
   independently of Layer-1. Failure of any layer doesn't block the others.
2. **AUTO_ACTION_SUCCEEDED ≠ RESOLVED**: every closed incident must reach HUMAN_AUDIT_ACKED.
3. **LLM is parallel + auditing, not gatekeeping** on automated actions.
4. **Closed-set authority for the LLM**: only the 10 Layer-0 scripts; no arbitrary shell.
5. **Every layer emits to the Incident Gateway**: state machine sees everything.
6. **Every manual action flows through the gateway too**: Layer-M is not a backdoor.

## Related

- `04-architecture/incident-gateway-state-machine.md` — 13-state machine + dedup-key + audit-ack queue.
- `04-architecture/autonomous-recovery-matrix.md` — per-failure decision tree.
- `04-architecture/kill-switch-circuit-breaker.md` — kill-switch + circuit-breaker.
- `15-runbooks/agent-orchestrator-failover-re-enable-checklist.md` — the DORMANT, out-of-scope agent-orchestrator
  `FailoverLoop` (dev-fleet task re-routing, not a member of this 5+1 stack).
- `05-infrastructure/disaster-recovery.md` — RTO/RPO targets + DR procedures.
- `15-runbooks/physical-pager-layer.md` — Layer-4 device comparison.
- `15-runbooks/alerting/audit-acknowledgement-flow.md` — Layer-5 ack flow.
