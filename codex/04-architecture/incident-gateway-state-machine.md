---
doc_type: codex-ssot
title: Incident Gateway State Machine
summary:
  13-state incident lifecycle owned by alerting-service as the central Incident Gateway — AUTO_ACTION_SUCCEEDED≠RESOLVED
  (separate recovery-verification gate), IncidentEnvelope schema, dedup incident_key, audit-ack queue, 7 immediate-SEV0
  overrides.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [alerting-service, batch-live-reconciliation-service, execution-service, strategy-service]
scope: [engineer, admin]
tags: [alerting, observability, escalation, self-healing, runbook]
related:
  [
    /codex/04-architecture/recovery-defence-in-depth-layers.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
    /codex/15-runbooks/alerting/audit-acknowledgement-flow.md,
    /codex/03-observability/alerting.md,
  ]
created: 2026-05-23
authoritative_for: [incident-state-machine, audit-ack-queue, dedup-key]
referenced_by:
  [
    /codex/03-observability/alerting.md,
    /codex/04-architecture/recovery-defence-in-depth-layers.md,
    plans/archive/incident_gateway_and_state_machine_2026_05_23.plan.md,
    plans/audit/instructions/observability_master_audit_instructions.md,
  ]
owner:
last_reviewed: 2026-05-23
code_refs:
---

# Incident Gateway State Machine

> SSOT for the 13-state incident lifecycle owned by `alerting-service` as the central Incident Gateway. Pairs with
> `recovery-defence-in-depth-layers.md` (the 5-layer model) and `autonomous-recovery-matrix.md` (per-failure-scenario
> decision tree).

## Principle

Every production incident transitions through a strict state machine. **`AUTO_ACTION_SUCCEEDED ≠ RESOLVED`** — recovery
verification is a separate gate from action completion. A restart can succeed while reconciliation remains unresolved;
we never close the incident until recovery is **proven**, not assumed.

## States (13, closed set)

```
DETECTED
  ↓
AUTO_ACTION_STARTED
  ↓
  ├── AUTO_ACTION_SUCCEEDED ─┐
  │                          ↓
  │                          RECOVERY_VERIFICATION_STARTED
  │                            ↓
  │                            ├── RECOVERY_CONFIRMED ─┐
  │                            │                       ↓
  │                            │                       AUDIT_REPORT_GENERATED
  │                            │                         ↓
  │                            │                         HUMAN_AUDIT_ACKED ─→ RESOLVED ─→ CLOSED
  │                            │
  │                            └── RECOVERY_UNCERTAIN ─→ SAFE_MODE_ACTIVE
  │
  └── AUTO_ACTION_FAILED ──────→ SAFE_MODE_ACTIVE
                                   ↓
                                   HUMAN_OPERATIONAL_ACKED (operator takes ownership)
                                     ↓
                                     ESCALATED ←→ audit-ack queue
                                       ↓
                                       AUDIT_REPORT_GENERATED → HUMAN_AUDIT_ACKED → RESOLVED → CLOSED
```

**Forbidden transitions** (enforced by `_ALLOWED_TRANSITIONS` const in
`unified_api_contracts/canonical/crosscutting/incident/state.py`):

- `AUTO_ACTION_SUCCEEDED → RESOLVED` (must go via RECOVERY_VERIFICATION_STARTED → RECOVERY_CONFIRMED).
- `DETECTED → CLOSED` (must be at least HUMAN_AUDIT_ACKED first if `human_audit_ack_required=True`).
- `RECOVERY_CONFIRMED → CLOSED` skipping AUDIT_REPORT_GENERATED + HUMAN_AUDIT_ACKED (the operator audit ack is mandatory
  per the 6h SLA — see `/codex/15-runbooks/alerting/audit-acknowledgement-flow.md`).

## IncidentEnvelope schema

Pydantic model in `unified_api_contracts/canonical/crosscutting/incident/envelope.py`. Required fields:

| Field                                            | Type              | Purpose                                                                   |
| ------------------------------------------------ | ----------------- | ------------------------------------------------------------------------- |
| `event_id`                                       | UUID              | Unique per event                                                          |
| `incident_key`                                   | str               | Stable dedup key — same root cause across N retries = 1 incident          |
| `timestamp`                                      | datetime (tz=UTC) | Event time                                                                |
| `environment`                                    | str               | prod / staging / dev                                                      |
| `severity_hint`                                  | AlertSeverity     | Initial guess — gateway may override per immediate-SEV0-overrides         |
| `domain`                                         | str               | live_trading / batch / reference_data / ...                               |
| `service` / `component`                          | str               | Source service + component path                                           |
| `strategy_id` / `strategy_family`                | str / None        | If strategy-scoped                                                        |
| `venue` / `account_id` / `instrument_id`         | str / None        | If venue/account/instrument-scoped                                        |
| `problem_type`                                   | str               | Closed-set fnmatch pattern for routing                                    |
| `problem_summary`                                | str               | One-line human description                                                |
| `risk_state`                                     | str               | safe / protected_mode / unknown / live_unresolved                         |
| `capital_at_risk`                                | bool              | True if capital exposure exists in current state                          |
| `auto_action_allowed`                            | bool              | True if Layer-0 may act without human approval                            |
| `auto_action_taken`                              | str / None        | Action that fired, if any                                                 |
| `recovery_confirmed`                             | bool              | Set only after RECOVERY_CONFIRMED transition                              |
| `human_operational_ack_required`                 | bool              | Operator must indicate "I'm investigating now"                            |
| `human_audit_ack_required`                       | bool              | Operator must review after-the-fact (default True for material incidents) |
| `audit_ack_due_at`                               | datetime / None   | SLA timer — see audit-acknowledgement-flow.md                             |
| `runbook_id`                                     | str / None        | RB-INC / RB-RECON / etc — link to the operator playbook                   |
| `dashboard_url` / `logs_url` / `kill_switch_url` | str / None        | Convenience links                                                         |
| `config_hash` / `code_version`                   | str               | Reproducibility — what code was running at incident time                  |
| `evidence`                                       | IncidentEvidence  | Populated at AUDIT_REPORT_GENERATED transition                            |

## Dedup-key `incident_key`

Stable hash over `(service, component, problem_type, strategy_id, venue, instrument_id)`. Same root cause across N
retries collapses to 1 incident. Window = 5 minutes; older `incident_key` matches expire.

5 OOM events on the same `execution-service` within 5 minutes = 1 IncidentEnvelope with 5 AgentActionEvent children. NOT
5 IncidentEnvelopes.

## Audit-ack queue

Redis Streams backed durable queue at `alerting-service/alerting_service/gateway/audit_ack_queue.py`. Incidents with
`human_audit_ack_required=True` land here with their `audit_ack_due_at` timestamp. A sorted set (`due_at_index`) keyed
by due-at provides O(log N) due-soon polling.

Escalation cron runs every 30s; on breach, escalates per the per-severity SLA matrix in
`/codex/15-runbooks/alerting/audit-acknowledgement-flow.md`:

| Severity | default | secondary_human_after | founder_after |
| -------- | ------- | --------------------- | ------------- |
| CRITICAL | 300s    | 600s                  | 1800s         |
| HIGH     | 7200s   | 10800s                | 21600s        |
| WARN     | 21600s  | 43200s                | 86400s        |
| INFO     | None    | n/a                   | n/a           |

## Immediate-SEV0 overrides (closed set, 7)

Pre-evaluated before severity-hint routing. ANY override = True forces SEV0 + Twilio voice + physical pager regardless
of severity_hint. UAC `ImmediateSev0Override` StrEnum:

1. `UNKNOWN_NET_EXPOSURE` — venue total ≠ internal total + no explanation row.
2. `OPEN_ORDERS_UNCONFIRMABLE` — venue REST 5xx + we have N open orders internally.
3. `KILL_SWITCH_CANNOT_CONFIRM_CANCEL` — activate ran but cancel-all returned partial.
4. `VENUE_INTERNAL_BALANCE_MISMATCH` — abs(venue - internal) > threshold.
5. `POSITION_EXISTS_EXTERNALLY_UNKNOWN_INTERNALLY` — venue reports position we don't know about.
6. `MATERIAL_BALANCE_MOVEMENT_UNEXPLAINED` — balance moved > threshold + no transfer/fill/funding row.
7. `MARGIN_COLLATERAL_SAFETY_UNCERTAIN` — venue API can't confirm margin OR ADL/insurance-fund signal.

## Recovery verification

5-tuple of booleans recorded on `RECOVERY_VERIFICATION_STARTED` transition:

- `health_checks_passed`
- `positions_reconciled`
- `orders_reconciled`
- `market_data_fresh`
- `strategy_state_restored` (OR `strategy_paused` if intentional pause)

ALL 5 must be True for `RECOVERY_CONFIRMED`. ANY False → `RECOVERY_UNCERTAIN` → `SAFE_MODE_ACTIVE`.

Per-service callbacks register at gateway startup:

| Service                                            | Callback covers                                                                                                              |
| -------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| execution-service                                  | orders match venue REST, positions match venue, fills reconciled, no kill_switch                                             |
| strategy-service (incl. `position/` — merged PBMS) | strategy_state_restored, target-tracking-enabled, no safe-mode; holds the live recon age fields (`unreconciled_age_seconds`) |
| mtds / mdps                                        | market_data_fresh (last tick within staleness window)                                                                        |
| risk-and-exposure-service                          | margin/HF inside healthy band, no liquidation risk                                                                           |

> **CORRECTION (BLRS audit D1, 2026-05-27)**: a prior row attributed a "`oldest_unreconciled_age` < threshold across 12
> dimensions" callback to `batch-live-reconciliation-service`. BLRS is a T+1 batch auditor and registers **no** recovery
> callback. No per-dimension recon-age recovery gate is wired today; if added it belongs with the live-recon owner
> (`strategy-service/position`). See `reconciliation-age-tracking.md` § "Recovery-verification callback".

## Provenance taxonomy

Every IncidentEnvelope + AgentActionEvent carries
`provenance ∈ {AUTOMATIC, MANUAL_OPERATOR, LLM_LAYER15, GATEWAY_DISPUTE, BREAKER_AUTO}`:

- **AUTOMATIC** — Layer-0 deterministic script fired due to a detector trigger.
- **MANUAL_OPERATOR** — operator clicked a Safety Ops tab button (typed-confirm-string required).
- **LLM_LAYER15** — LLM recovery-audit-signoff agent invoked Layer-0 script as backup actuator (only via the closed-set
  wrapper `llm_invoke_layer0.py`).
- **GATEWAY_DISPUTE** — incident state machine itself fired an action because the LLM agent verdict was
  DISPUTE_AUTOMATED_ACTION (e.g. pause_strategy).
- **BREAKER_AUTO** — circuit breaker tripped from threshold breach (e.g. failure_rate > 60%).

## Persistence

`alerting-service/alerting_service/gateway/incident_persister.py` writes append-only JSONL to GCS at
`gs://<kill-switch-audit>/incidents/{YYYY-MM-DD}/{incident_key}/` with files:

- `envelope.json` — IncidentEnvelope (snapshot at each state transition)
- `actions/<event_id>.json` — AgentActionEvent rows
- `signoffs/<event_id>.json` — RecoveryAuditSignoff rows from LLM agent
- `evidence/<type>.json` — populated at AUDIT_REPORT_GENERATED transition
- `escalation_history.jsonl` — append-only audit_ack escalation rows

Retention: 1 year (regulatory).

## Related

- `04-architecture/recovery-defence-in-depth-layers.md` — the 5-layer defence model
- `04-architecture/autonomous-recovery-matrix.md` — per-failure decision tree
- `15-runbooks/alerting/audit-acknowledgement-flow.md` — 6h ack SLA + escalation ladder
- `03-observability/alerting.md` — channel routing
- `plans/active/incident_gateway_and_state_machine_2026_05_23.md` — implementation plan
