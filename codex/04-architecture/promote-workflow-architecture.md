# Promote Workflow Architecture — May-23 SSOT

> **Scope**: May-23 subset. Post-cutover Phase 2 ships full pinned-shas `CandidateManifest`, state-machine
> consolidation, and cross-service auto-registration. This doc describes the minimal May-23 shape only.
>
> SSOT plan: `plans/active/promote_workflow_may23_cli_path_2026_05_10.md` Post-cutover successor:
> `plans/active/promote_workflow_post_cutover_ui_pipeline_2026_05_10.md`

---

## Dual-Track Promote (May-23)

```
OPERATOR
    │
    ├─── CLI TRACK (PRIMARY) ─────────────────────────────────────────────┐
    │    run-paper.sh → preflight-cutover.sh → launch-strategy-paper-vm.sh│
    │    colocated_engine.py (paper mode)                                  │
    │    [≥7d pass] run-live.sh → launch-strategy-live-vm.sh              │
    │                                                                       │
    └─── UI TRACK (SECONDARY) ────────────────────────────────────────────┤
         UTS-UI Promote button                                              │
             └→ POST /api/promote/{strategy_id}/{manifest_id}              │
                 └→ 5 pre-flight gates                                     │
                     └→ event: STRATEGY_PROMOTED_TO_PAPER / _TO_LIVE       │
                         └→ deployment-api emits launch event              │
                             └→ launch-strategy-paper-vm.sh / live-vm.sh  │
                                                                            │
Both tracks converge at ─────────────────────────────────────────────────►┘
    VM running on GCE (strategy-paper-{archetype} / strategy-live-{archetype})
    ServiceBootstrap → STARTED event → event archive (GCS + PubSub)
    DART terminal → DartThreeWayView (batch / paper / live comparison)
    ManualTradeGateDialog (first 3 trading days — operator approves each fill)
```

---

## Phase Map

| Phase    | Description                                                             | Status      |
| -------- | ----------------------------------------------------------------------- | ----------- |
| Phase 1  | VM launcher scripts + `colocated_engine.py` wiring                      | ✅ Shipped  |
| Phase 2  | CLI track (`run-paper.sh` / `run-live.sh` / `preflight-cutover.sh`)     | ✅ Shipped  |
| Phase 3  | Phase 3 backtest + candidate selection                                  | ✅ Shipped  |
| Phase 4  | Custody (CLOUD_KMS_ENCRYPTED), Copper MPC scaffold, alerting            | ✅ Shipped  |
| Phase U1 | `MinimalCandidateManifest` (Firestore) + `CandidateManifestStore` (UTL) | ✅ Shipped  |
| Phase U2 | `GET /strategy/{id}/runs?mode=batch\|paper\|live` (deployment-api)      | ✅ Shipped  |
| Phase U3 | `POST /promote/{strategy_id}/{manifest_id}` (deployment-api)            | ✅ Shipped  |
| Phase U4 | UI promote workflow wired to real backend                               | ✅ Shipped  |
| Phase U5 | DART 3-way visualization (DartThreeWayView)                             | ✅ Shipped  |
| Phase U6 | ManualTradeGateDialog + execution-service manual-pending queue          | ✅ Shipped  |
| Phase 7  | Codex SSOTs (this doc + cli-promote-paths.md + others)                  | ✅ Shipping |

---

## Backend Services

### deployment-api

Primary backend for the promote workflow.

**Endpoints**:

- `POST /api/promote/{strategy_id}/{candidate_manifest_id}` — validate + emit promote event
  - Body: `{ target_phase, promoter, reason }`
  - 5 pre-flight gates (mock-passthrough in non-prod): Copper sandbox, venue API keys, alerting config, kill-switch
    YAML, recon green
  - Emits `STRATEGY_PROMOTED_TO_PAPER` or `STRATEGY_PROMOTED_TO_LIVE` via UTL `log_event`
  - Auth: `X-API-Key` (operator gate); Firebase `execution-full` enforced at UI layer (May-23)
- `GET /api/strategy/{strategy_id}/runs?mode=batch|paper|live` — per-run P&L/fill records
  - Reads from backtest GCS path (batch) or event archive (paper / live)
  - Returns `StrategyRunsResponse` with `RunRecord[]` per run_date

### deployment-service / VM launchers

`deployment-service/scripts/vm/launch-strategy-paper-vm.sh` `deployment-service/scripts/vm/launch-strategy-live-vm.sh`

Full shape spec: `codex/05-infrastructure/strategy-vm-launcher-shape.md`.

### execution-service (manual gate path)

Strategy-service emits instruction in `MANUAL` mode → execution-service holds in `manual_pending_queue` → DART UI calls
`POST /api/manual/pending/{id}/approve` → `MANUAL_APPROVED` event emitted → execution-service unholds + executes.

Full flow: `codex/14-customer-journeys/dart/mode-toggle.md`.

---

## State Machine — `StrategyMaturityPhase`

```
IDEATION
    └─ [Phase 3 backtest passes] ──→ CANDIDATE
                                          └─ [promote to paper_1d] ──→ PAPER_1D
                                                                             └─ [promote to live_early] ──→ LIVE_EARLY
                                                                                                                └─ [post-cutover] ──→ LIVE_FULL
```

Only `CANDIDATE → PAPER_1D` and `PAPER_1D → LIVE_EARLY` are valid promote targets for May-23. `LIVE_FULL` is
post-cutover.

UTL enum: `unified_trading_library.strategy.strategy_maturity_phase.StrategyMaturityPhase`.

---

## MinimalCandidateManifest (Phase U1 shape)

```python
class MinimalCandidateManifest(BaseModel):
    manifest_id: str          # UUID
    strategy_instance_id: str
    version_id: str | None
    archetype: StrategyArchetype
    config_json: dict[str, Any]
    score_vector: GroupBMetrics
    target_phase: StrategyMaturityPhase
    created_at: datetime
    created_by: str
    reason: str

    # Post-cutover Phase 2 (None for May-23):
    pinned_shas: dict[str, str] | None = None
    model_refs: list[ModelRef] | None = None
    features_manifest_version: str | None = None
    chain_rpc_pins: dict[str, str] | None = None
```

Stored in Firestore `strategy_candidate_manifests` collection. UAC type:
`unified_api_contracts.internal.domain.strategy_service.candidate_manifest.MinimalCandidateManifest`.

---

## UTL Event Constants

| Constant                         | When emitted                                |
| -------------------------------- | ------------------------------------------- |
| `STRATEGY_PROMOTED_TO_CANDIDATE` | Strategy passes Phase 3 backtest gates      |
| `STRATEGY_PROMOTED_TO_PAPER`     | Promote endpoint: `target_phase=paper_1d`   |
| `STRATEGY_PROMOTED_TO_LIVE`      | Promote endpoint: `target_phase=live_early` |
| `STRATEGY_PROMOTE_REJECTED`      | Promote endpoint: pre-flight gate failure   |

All 4 in `PROMOTE_WORKFLOW_EVENT_TYPES` set + `STANDARD_LIFECYCLE_EVENTS`.

---

## Post-Cutover Deferred Items

> These are explicitly out of May-23 scope. Named successor plan:
> `plans/active/promote_workflow_post_cutover_ui_pipeline_2026_05_10.md`

- Full `CandidateManifest` enrichment (pinned shas, model refs, features manifest version)
- Firebase `execution-full` backend enforcement (currently at UI layer only)
- Cross-service auto-registration on promote event
- Full pre-flight pipeline (9+ gates)
- CEFFU custody integration (June-1+ per custody-providers.md § CEFFU)
- `LIVE_FULL` maturity phase
- UI as primary track without CLI fallback
