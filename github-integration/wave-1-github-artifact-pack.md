# Wave 1 GitHub Artifact Pack

Ready-to-create backlog artifacts from `feature-request-cards-wave-1.md` and current wave-1 locks.

---

## Milestones

- `Batch85` (audit remediation + batch readiness)
- `Live90` (live readiness + production hardening)
- `TechReadiness` (cross-service technical gate completion)
- `Commercialization` (UI/client/commercial-operational gate completion)

---

## Epics and Project v2 Defaults

Use these fields for each epic unless overridden:

- `status`: `pending`
- `priority`: `P1-high`
- `iteration`: next weekly slot
- `target_cloud`: `dual_cloud_ready`
- `uat_required`: `yes`

### Epic: `ExchangeInterfaceCore`

- lane: `capability_request`
- assignee_group: `strategy_ml`
- owner_default: `Ikenna`
- readiness_tier: `smoke_tested`
- commercial_stage: `strategy_candidate`
- milestone: `TechReadiness`

### Epic: `PositionBalanceTruth`

- lane: `capability_request`
- assignee_group: `strategy_ml`
- owner_default: `Ikenna`
- readiness_tier: `smoke_tested`
- commercial_stage: `strategy_candidate`
- milestone: `Batch85`, `Live90`

### Epic: `ExposureControls`

- lane: `capability_request`
- assignee_group: `strategy_ml`
- owner_default: `Ikenna`
- readiness_tier: `smoke_tested`
- commercial_stage: `strategy_candidate`
- milestone: `Live90`

### Epic: `RiskPolicyEnforcement`

- lane: `capability_request`
- assignee_group: `hardening_finishline`
- owner_default: `Ikenna`
- readiness_tier: `history_validated`
- commercial_stage: `strategy_candidate`
- milestone: `Live90`

### Epic: `PnlAttributionCore`

- lane: `capability_request`
- assignee_group: `strategy_ml`
- owner_default: `Ikenna`
- readiness_tier: `smoke_tested`
- commercial_stage: `signal_candidate`
- milestone: `TechReadiness`, `Commercialization`

### Epic: `ObservabilityHardening`

- lane: `audit_remediation`
- assignee_group: `infra`
- owner_default: `Femi`
- readiness_tier: `history_validated`
- commercial_stage: `strategy_candidate`
- milestone: `Batch85`, `Live90`

### Epic: `SecurityRebaseline`

- lane: `audit_remediation`
- assignee_group: `infra`
- owner_default: `Femi`
- readiness_tier: `history_validated`
- commercial_stage: `strategy_candidate`
- milestone: `Batch85`, `Live90`

### Epic: `DualCloudReadiness`

- lane: `audit_remediation`
- assignee_group: `infra`
- owner_default: `Femi`
- readiness_tier: `live_stability_validated`
- commercial_stage: `strategy_commercial_ready`
- milestone: `Live90`

### Epic: `OpsDeploymentUI`

- lane: `capability_request`
- assignee_group: `hardening_finishline`
- owner_default: `Harsh`
- readiness_tier: `smoke_tested`
- commercial_stage: `strategy_candidate`
- milestone: `Live90`

### Epic: `MlDeploymentUI`

- lane: `capability_request`
- assignee_group: `strategy_ml`
- owner_default: `Ikenna`
- readiness_tier: `smoke_tested`
- commercial_stage: `signal_candidate`
- milestone: `Commercialization`

### Epic: `ClientOnboardingReporting`

- lane: `capability_request`
- assignee_group: `hardening_finishline`
- owner_default: `Harsh`
- readiness_tier: `smoke_tested`
- commercial_stage: `strategy_candidate`
- milestone: `Commercialization`

---

## Standard Subtasks (Create Under Every Epic)

1. implementation
2. tests (unit/integration/regression as relevant)
3. observability and alerting
4. docs and runbooks
5. checklist and PM sync verification

---

## Discovery Issues for Remaining Targeted Unknowns

Create one issue each, with `status=pending` and linked to owning epic.

1. `Define venue-specific circuit-break threshold presets`
   - Epic: `ExchangeInterfaceCore`
   - lane: `capability_request`
   - owner_default: `Ikenna`

2. `Define reconciliation guardrail tuning by risk tier (2%-10% band)`
   - Epic: `PositionBalanceTruth`
   - lane: `capability_request`
   - owner_default: `Ikenna`

3. `Define numeric residual thresholds by asset and risk tier`
   - Epic: `PnlAttributionCore`
   - lane: `capability_request`
   - owner_default: `Ikenna`

4. `Define alert threshold numeric table for severity transitions`
   - Epic: `ObservabilityHardening`
   - lane: `audit_remediation`
   - owner_default: `Femi`

5. `Define service token model and rotation standard beyond phase-1 baseline`
   - Epic: `SecurityRebaseline`
   - lane: `audit_remediation`
   - owner_default: `Femi`

6. `Define external-client auth boundary model beyond operator/internal baseline`
   - Epic: `OpsDeploymentUI`, `ClientOnboardingReporting`
   - lane: `capability_request`
   - owner_default: `Harsh`

---

## Locked Wave-1 Decisions Embedded in Artifacts

- Reconciliation baseline:
  - `<2%`: background auto-reconcile
  - `2% to <10%`: background + priority refresh signal
  - `>=10%`: immediate consumer refresh/re-sync expectation
- Non-prod alert testing: daily synthetic heartbeat + weekly failure-injection
- ML metadata source-of-truth: GCS manifests + BigQuery index
- Role model: Admin, Operator, Viewer, ClientViewer, ClientAnalyst
