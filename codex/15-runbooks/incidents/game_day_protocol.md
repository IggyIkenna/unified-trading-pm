---
title: "Game-Day Protocol — 3+ Scratch Scenarios End-to-End Acceptance"
scope: [admin, engineer]
owner: ikenna@odum-research.com
cadence: Pre-cutover (single run) + quarterly post-cutover
verifier: Operator + secondary on-call observe full Layer-0..5 stack fire
last_executed: never
authoritative_for: [game-day-acceptance-protocol]
referenced_by:
  - plans/active/incident_gateway_and_state_machine_2026_05_23.md
  - plans/audit/instructions/observability_master_audit_instructions.md
related:
  - codex/04-architecture/recovery-defence-in-depth-layers.md
  - plans/active/scratch_scenarios_day1/
---

# Game-Day Protocol — 3+ Scenarios End-to-End Acceptance

> **Purpose**: prove the 5+1 defence-in-depth recovery stack works end-to-end by running at least 3 of the 17 scratch
> scenarios in `plans/active/scratch_scenarios_day1/` against the staging stack with all Layer-0..5 components live.
> **Pre-cutover gate**: this protocol MUST be GREEN before any new strategy promotes to `live_full`.
>
> Plan-of-record: `plans/active/incident_gateway_and_state_machine_2026_05_23.md` Phase 6 + cross-cutting acceptance for
> the observability_master epic.
>
> Audit-instructions Section O.10 enumerates the 7 per-scenario asserts that MUST all pass for the audit to flip GREEN.

## When to run

- **Pre-cutover** (single mandatory pass) — before May-23 live DeFi cutover.
- **Quarterly** — verify the stack still works as the codebase evolves.
- **After any change** to Layer-0 scripts / Incident Gateway / LLM agent / notifiers / DART Safety Ops tab.

## Pre-flight (operator action — 30 minutes)

1. Confirm Tier-1 UAC schemas + Tier-2 alerting gateway + Tier-3 Layer-0 scripts + Tier-4 LLM agent are deployed to
   staging (see commit log in `plans/active/incident_gateway_and_state_machine_2026_05_23.md` "Tier-1-4 implementation
   log").
2. Confirm Twilio account creds + (optional) physical pager creds are in the STAGING SM project (separate from prod).
3. Confirm 2 dummy strategies with risk_thresholds configured + paper positions on staging venues.
4. Confirm the `recovery-audit-signoff` LLM agent is running on the staging `recovery-audit-staging-*` VM (per
   `agent-orchestrator/agents/recovery-audit.md`).
5. Open DART Safety Ops tab in browser; confirm 3 sections render.
6. Open PagerDuty mobile app + ensure operator phone is on charging.
7. Operator + secondary on-call on Zoom call so both observe firing.

## Recommended scenarios (pick at least 3)

Per audit-instructions Section O.10:

### Scenario 1: `01_cefi_venue_circuit_breaker_trip` (Layer-0 disable/cancel/pause)

**What it tests**: circuit breaker auto-trips when a venue WebSocket disconnects

- REST returns 503 mid-trading. Validates `disable_venue` + `cancel_open_orders`
- `pause_strategy` Layer-0 scripts.

Steps:

1. Pre-fill staging positions on Binance perp BTC-USDT.
2. Run `e2e-testing/scripts/defi/scenarios/inject_venue_outage.sh --venue binance --duration 300s`.
3. Observe via DART Safety Ops tab: incident appears with severity=CRITICAL.
4. Watch incident transition DETECTED → AUTO_ACTION_STARTED → AUTO_ACTION_SUCCEEDED → RECOVERY_VERIFICATION_STARTED →
   RECOVERY_CONFIRMED → AUDIT_REPORT_GENERATED.
5. Verify LLM signoff doc appears in DART LLM Audit Verdicts panel within 90s of AUDIT_REPORT_GENERATED.
6. Verify ack-queue shows the incident with 5min countdown (CRITICAL SLA).
7. Operator clicks Audit Ack → incident closes.

### Scenario 2: `15_liquidation_proximity_auto_deleverage` (Risk pre-detector + close-all)

**What it tests**: liquidation-risk pre-detector fires before liquidation + auto-deleverage runs +
DrawdownInvestigationReport generated. Validates `enter_safe_mode` + per-strategy close-all script.

Steps:

1. Pre-fill staging position with HF ≈ 1.3 (close to threshold).
2. Run `e2e-testing/scripts/defi/scenarios/inject_oracle_price_drop.sh --asset weETH --pct 0.05`.
3. Verify LiquidationRiskPredetector fires SEV0 within 10s.
4. Verify Layer-0 `enter_safe_mode` runs for affected strategy.
5. Verify per-strategy close-all `CarryStakedBasisCloseAll.execute()` runs in dry-run.
6. Verify LiquidationInvestigationReport has 16/16 fields populated.
7. Verify LLM signoff narrative references the report.

### Scenario 3: `04_defi_oracle_deviation_30sigma` (Provider-outage + Twilio fallback)

**What it tests**: alerting provider goes down DURING a SEV0; router enters fallback_mode; Twilio voice fires + reaches
operator within 90s.

Steps:

1. Synthetically kill the PagerDuty probe in staging.
2. Run `e2e-testing/scripts/defi/scenarios/inject_oracle_deviation.sh --magnitude 30sigma`.
3. Verify within 60s: provider_health_probe emits `ALERTING_PROVIDER_DEGRADED`.
4. Verify router fallback_mode=True.
5. Verify Twilio voice call arrives at operator phone within 90s.
6. Verify operator can Audit Ack via DART even with PagerDuty down.

## The 7 per-scenario asserts (all 3 scenarios MUST pass all 7)

Per audit-instructions Section O.10.d, every scenario MUST satisfy:

- [ ] (1) **Layer-0 acts within expected time** — script exits 0 within 60s of trigger.
- [ ] (2) **AgentActionEvent rows persist** — JSONL row written to GCS audit store at `incidents/{date}/{key}/actions/`.
- [ ] (3) **LLM signoff lands non-DISPUTE** within 90s (or DISPUTE_AUTOMATED_ACTION if the automated action was
      intentionally wrong — that's a separate pass case).
- [ ] (4) **Layer-2/3 cascade fires if SEV0** — PagerDuty page (or Twilio if fallback_mode).
- [ ] (5) **Ack-queue countdown active** with correct SLA per severity.
- [ ] (6) **Safety Ops tab shows the incident** with manual override buttons enabled.
- [ ] (7) **Incident closes** via HUMAN_AUDIT_ACKED → RESOLVED → CLOSED state transitions.

## Acceptance criterion

All 3 scenarios × 7 asserts = **21/21 GREEN** OR documented failure with named remediation plan in `plans/active/`.
Anything less = audit RED.

## Verification artifacts

After each game-day run, the operator records:

- Date + scenarios run + pass/fail per assert
- GCS path to the persisted incident envelopes + signoffs
- Screenshots of DART Safety Ops tab during each scenario
- Twilio voice call recordings (if applicable)

Stored in `plans/audit/results/game_day_<yyyy_mm_dd>.md`.

## Failure-handling

If any assert fails:

1. STOP the cutover preparation.
2. File a remediation plan at `plans/active/<failure>_remediation_<date>.md`.
3. Dispatch the plan to the appropriate epic (observability_master / strategy_master / etc).
4. Re-run the full 3-scenario protocol after remediation lands.

## Composes with

- `codex/04-architecture/recovery-defence-in-depth-layers.md` — the 5+1 layer model
- `codex/04-architecture/incident-gateway-state-machine.md` — 14-state lifecycle
- `codex/15-runbooks/alerting/audit-acknowledgement-flow.md` — SLA matrix
- `plans/audit/instructions/observability_master_audit_instructions.md` Section O — E2E flow checks

## Last executed

_never — run pre-cutover_

---

## Bash-runnable game-day kit (operator-facing)

> **⚠️ STAGING-INFRA-REQUIRED**: this section needs the live staging stack to be running (alerting-service +
> execution-service + strategy-service + recovery-audit-signoff agent + dev:mock UI dev server on 3100). A single-host
> session WITHOUT staging infrastructure cannot complete the end-to-end gate — it can only run the unit + Playwright
> legs.
>
> Operator runs each block from a fresh tmux pane while watching:
>
> - DART Safety Ops tab (`/safety-ops` after admin auth)
> - PagerDuty mobile app (acks)
> - Twilio voice call ring on configured number
> - Tail of `gs://<kill-switch-audit>/incidents/$(date +%Y-%m-%d)/` for envelopes + signoffs

### Pre-flight checklist (operator, 30 min)

```bash
# 1. Tarball + verify Tier-1-4 + Tier-5 + Tier-5 follow-up shipped
cd ${WORKSPACE_ROOT}/unified-trading-pm
git log origin/live-defi-rollout --oneline -20 | grep -E "Tier-1-4|Tier-2 follow-up|Tier-3|Tier-5"

# 2. Confirm secrets in STAGING SM (separate from prod)
gcloud secrets list --project=central-element-323112 --filter="name:alerting-* OR name:twilio-*" --format="value(name)" | sort

# 3. Confirm recovery-audit-signoff GCE VM running in staging
gcloud compute instances list --filter="name:recovery-audit-staging-* AND status:RUNNING" --format=table

# 4. UI dev server up on 3100 (if running locally)
curl -sf http://localhost:3100/safety-ops > /dev/null && echo "UI :3100 OK" || echo "UI :3100 DOWN"

# 5. Open DART Safety Ops in browser + admin-login via seeded persona
open http://localhost:3100/safety-ops
```

### Scenario 1 launcher — `01_cefi_venue_circuit_breaker_trip`

```bash
# Inject synthetic venue outage; observe Layer-0..5 cascade
cd ${WORKSPACE_ROOT}/e2e-testing
bash scripts/defi/scenarios/inject_venue_outage.sh \
    --venue binance \
    --duration 300 \
    --staging \
    --incident-key "game-day-$(date +%Y%m%d-%H%M%S)-scenario-01"

# Real-time observation (open in 2 panes):
gcloud pubsub subscriptions pull agent-recovery-actions-staging \
    --project=central-element-323112 --auto-ack --limit=20 \
    --format=json | jq -r '.[] | "\(.publishTime) \(.message.attributes.action_type) \(.message.attributes.action_status)"'

# Tail incident envelopes
gcloud storage cat \
    "gs://kill-switch-audit-staging/incidents/$(date +%Y-%m-%d)/*/envelope.json" \
    --project=central-element-323112 2>&1 | jq -r '.state'

# Per-assert pass/fail recording (operator types Y/N):
echo "(1) Layer-0 acts within 60s? (Y/N):"
read pass_1
echo "(2) AgentActionEvent rows persisted? (Y/N):"
read pass_2
# ... continue through (3)-(7) per Section O.10.d ...
```

### Scenario 2 launcher — `15_liquidation_proximity_auto_deleverage`

```bash
cd ${WORKSPACE_ROOT}/e2e-testing
bash scripts/defi/scenarios/inject_oracle_price_drop.sh \
    --asset weETH \
    --pct 0.05 \
    --staging \
    --incident-key "game-day-$(date +%Y%m%d-%H%M%S)-scenario-15"

# Observe:
# - LiquidationRiskPredetector fires SEV0 within 10s
# - Layer-0 enter_safe_mode runs for carry_staked_basis
# - Per-strategy close-all dry-run plan generated
# - LiquidationInvestigationReport 16/16 fields
# - LLM signoff verdict references the report
```

### Scenario 3 launcher — `04_defi_oracle_deviation_30sigma` (with provider-outage layered)

```bash
cd ${WORKSPACE_ROOT}/e2e-testing

# Step A — kill the PagerDuty probe to force fallback_mode
bash scripts/alerting/simulate_provider_outage.sh --provider pagerduty --duration 300 --staging

# Step B — inject the oracle deviation
bash scripts/defi/scenarios/inject_oracle_deviation.sh \
    --magnitude 30sigma \
    --staging \
    --incident-key "game-day-$(date +%Y%m%d-%H%M%S)-scenario-04"

# Verify:
# - provider_health_probe emits ALERTING_PROVIDER_DEGRADED within 60s
# - router fallback_mode=True
# - Twilio voice call arrives within 90s
# - Operator can Audit Ack via DART even with PagerDuty down

# Restore PagerDuty probe after run
bash scripts/alerting/restore_provider.sh --provider pagerduty --staging
```

### Acceptance recorder

```bash
cd ${WORKSPACE_ROOT}/unified-trading-pm
DATE_TAG="$(date +%Y_%m_%d)"
RESULT_FILE="plans/audit/results/game_day_${DATE_TAG}.md"

cat > "$RESULT_FILE" <<RESULT_EOF
---
title: "Game-Day Acceptance — ${DATE_TAG}"
type: audit-result
epic: observability_master
parent: master_to_live_defi_2026_05_23
locked_by: live-defi-rollout
locked_since: ${DATE_TAG//_/-}
---

# Game-Day Acceptance Result — ${DATE_TAG}

Operator: <name>
Secondary on-call: <name>
Start: <UTC>
End: <UTC>

## Per-scenario × per-assert pass/fail (21/21 = GREEN)

| Scenario | (1) Layer-0 acts | (2) AgentActionEvent | (3) LLM signoff non-DISPUTE | (4) Layer-2/3 cascade | (5) Ack queue countdown | (6) Safety Ops UI | (7) HUMAN_AUDIT_ACKED → CLOSED |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 01_cefi_venue_circuit_breaker_trip |   |   |   |   |   |   |   |
| 15_liquidation_proximity_auto_deleverage |   |   |   |   |   |   |   |
| 04_defi_oracle_deviation_30sigma |   |   |   |   |   |   |   |

**Total: __ / 21**. Required for GREEN: 21/21.

## Evidence

- GCS incident envelopes: \`gs://kill-switch-audit-staging/incidents/${DATE_TAG//_/-}/<keys>/\`
- DART screenshots (3 per scenario, total 9): \`<linked here>\`
- Twilio voice call recordings (if applicable): \`<call SIDs>\`
- PagerDuty incidents (acked): \`<incident IDs>\`

## Sign-off

| Role | Name | Signature | Date |
| --- | --- | --- | --- |
| Operator | | | |
| Secondary on-call | | | |
| (If 21/21 GREEN) Cutover-go decision | | | |
RESULT_EOF

echo "Result template written to: $RESULT_FILE"
```

### What to do if a scenario fails an assert

1. STOP cutover preparation.
2. File `plans/active/game_day_<scenario>_failure_<date>.md` (parent_epic: observability_master).
3. Reproduce the failure on staging via the same script.
4. Bisect: which Tier-1-4 / Tier-5 piece broke?
5. Ship fix + re-run the full 3-scenario protocol.
6. Do NOT promote any strategy to `live_full` until 21/21 GREEN.

### Why a single-agent session can't ship this gate alone

| Requirement                                                                                | Available in single-agent session?                                                    |
| ------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------- |
| Staging GCE VMs (alerting-service + execution + strategy + recovery-audit-signoff) running | ❌ — needs operator-driven deploy                                                     |
| Synthetic-injection scripts under `e2e-testing/scripts/defi/scenarios/`                    | ❌ — need separate authoring + staging-stack wiring (out of observability epic scope) |
| Twilio account + paid voice minutes (for live calls)                                       | ❌ — operator-only per ping doc item #1                                               |
| Operator phone receiving Twilio calls + acking via mobile                                  | ❌ — physical operator                                                                |
| Secondary on-call observing in parallel                                                    | ❌ — second human                                                                     |

Therefore: this gate is **operator-driven**. The agent provides the protocol + the bash-runnable kit + the
result-recorder template; the operator runs it. The agent flips the audit checkbox to GREEN ONLY after the operator
posts the `plans/audit/results/game_day_<date>.md` result with 21/21 + signs the row.
