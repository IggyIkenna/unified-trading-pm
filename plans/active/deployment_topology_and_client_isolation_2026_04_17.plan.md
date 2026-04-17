---
name: deployment-topology-and-client-isolation
overview:
  Per-service client-isolation policy (shared vs isolated) + SLA tiers + runtime profiles + chaos/kill-switch primitives
  wired end-to-end across runtime-topology SSOT, UAC, UTL, deployment-service/api/ui, and affected services.
type: mixed
epic: epic-code-completion
status: active
locked_by: live-defi-rollout
locked_since: 2026-04-17

completion_gates:
  code: C5
  deployment: D2
  business: B1

repo_gates:
  - repo: unified-trading-pm
    code: C0
    deployment: none
    business: none
  - repo: unified-api-contracts
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-library
    code: C0
    deployment: none
    business: none
  - repo: deployment-service
    code: C0
    deployment: none
    business: none
  - repo: deployment-api
    code: C0
    deployment: none
    business: none
  - repo: deployment-ui
    code: C0
    deployment: none
    business: none
  - repo: execution-service
    code: C0
    deployment: none
    business: none
  - repo: strategy-service
    code: C0
    deployment: none
    business: none
  - repo: position-balance-monitor-service
    code: C0
    deployment: none
    business: none
  - repo: risk-and-exposure-service
    code: C0
    deployment: none
    business: none
  - repo: pnl-attribution-service
    code: C0
    deployment: none
    business: none
  - repo: alerting-service
    code: C0
    deployment: none
    business: none
  - repo: e2e-testing
    code: C0
    deployment: none
    business: none

depends_on: []

todos:
  # ===================================================================
  # PHASE 1 — SSOT: topology schema v7 + UAC types + UTL reader + codex
  # All items in Phase 1 run SEQUENTIALLY in one repo cluster (PM, UAC, UTL).
  # Phase 1 unblocks every subsequent phase.
  # ===================================================================
  - id: p1a-topology-v7
    content: |
      - [ ] [AGENT] P0. Bump `unified-trading-pm/configs/runtime-topology.yaml` v6→v7.
        Add four top-level sections (non-breaking additions):
        (1) `isolation_policies` — per-service `{default: shared|isolated, allowed: [...], reason: str}`
            for every service in clusters (L5/L6 get non-trivial policies; L1-L4 default shared).
        (2) `sla_tiers` — `{premium, standard, basic}` each with `{cost_multiplier, allowed_isolations, min_isolated_services[]}`.
        (3) `runtime_profiles` — `{backtest, paper, mock-live, staging, prod}` each declaring
            `{mock_mode, auth_disabled, chaos_allowed, client_isolation_required,
              storage_namespace, cloud_mock_mode, mock_state_mode}`.
        (4) `chaos_hooks` — list of supported injection points with target service/boundary.
        Bump `version: 6 → 7`. Update SSV generator script if needed.
    status: todo
  - id: p1b-uac-schemas
    content: |
      - [ ] [AGENT] P0. Add UAC module
        `unified-api-contracts/unified_api_contracts/internal/domain/deployment_service/isolation.py`
        with:
        - `IsolationPolicy(StrEnum)`: SHARED, ISOLATED
        - `SLATier(StrEnum)`: PREMIUM, STANDARD, BASIC
        - `RuntimeProfile(StrEnum)`: BACKTEST, PAPER, MOCK_LIVE, STAGING, PROD
        - `ChaosInjectionPoint(StrEnum)`: VENUE_LATENCY, RPC_TIMEOUT, RECON_MISMATCH,
          PRICE_SHOCK, INSTRUMENT_DELIST, CONFIG_FLIP, KILL_SWITCH_FIRE, COMPONENT_FAILURE
        - `ServiceIsolationSpec(BaseModel)`: default, allowed[], reason
        - `SLATierSpec(BaseModel)`: tier, cost_multiplier, allowed_isolations[], min_isolated_services[]
        - `RuntimeProfileSpec(BaseModel)`: profile, mock_mode, auth_disabled, chaos_allowed,
          client_isolation_required, storage_namespace, cloud_mock_mode, mock_state_mode
        - `ClientServiceOverride(BaseModel)`: service_name, isolation
        - `ClientSubscription(BaseModel)`: client_id, sla_tier, service_overrides[], active_from, active_until
        - `ChaosInjectionSpec(BaseModel)`: point, target_service, parameters, active_from, active_until
        Export from `deployment_service/__init__.py`. Add matching tests under
        `unified-api-contracts/tests/internal/deployment_service/test_isolation.py`.
    status: todo
  - id: p1c-utl-reader
    content: |
      - [ ] [AGENT] P0. Extend `unified-trading-library/unified_trading_library/topology/topology_reader.py`
        with five new readers:
        - `get_isolation_policy(service: str) -> ServiceIsolationSpec`
        - `resolve_deployment(service: str, client_id: str, override: IsolationPolicy | None = None) -> IsolationPolicy`
        - `get_sla_tier_spec(tier: SLATier) -> SLATierSpec`
        - `get_runtime_profile_spec(profile: RuntimeProfile) -> RuntimeProfileSpec`
        - `list_chaos_injection_points() -> list[ChaosInjectionPoint]`
        Replace the local `_*Config` TypedDicts with imports from UAC (SSOT — audit flagged
        this as "not ideal but functional"). Add tests under
        `unified-trading-library/tests/topology/test_isolation_readers.py`.
    status: todo
  - id: p1d-codex-ssot
    content: |
      - [ ] [AGENT] P0. Write NEW codex doc
        `unified-trading-pm/codex/04-architecture/client-isolation-sla-and-runtime-profiles.md` as SSOT.
        Cover: the model (per-service isolation choice), SLA tiers with cost passthrough,
        runtime profiles (backtest/paper/mock-live/staging/prod), chaos injection contract,
        the archetype→isolation-requirement mapping (MM needs execution+strategy isolated and
        co-located; ML-directional batch can run fully shared; event-settled sports runs
        shared until fixture close then isolates execution). Include worked examples
        (one small client on premium, one large client on standard, one multi-tenant pool).
    status: todo
  - id: p1e-codex-crosslinks
    content: |
      - [ ] [AGENT] P0. Update codex cross-links:
        (1) `codex/04-architecture/RUNTIME_TOPOLOGY_DECISIONS.md` — add §22 "Multi-Tenant
            Isolation + SLA Tiers + Runtime Profiles" linking to new SSOT.
        (2) `codex/05-infrastructure/runtime-tiers-and-deployment.md` — add §6 explaining
            that runtime_profiles are the single axis collapsing the 5 mode env vars
            (CLOUD_MOCK_MODE, MOCK_STATE_MODE, DISABLE_AUTH, VITE_MOCK_API, VITE_SKIP_AUTH).
        (3) `codex/09-strategy/architecture-v2/README.md` — add §"Deployment & Isolation"
            pointing to SSOT; each family/archetype doc gets one line declaring typical
            isolation need.
        (4) `.cursor/CLAUDE.md` Key Rules table — add one line referencing the SSOT doc.
    status: todo
  - id: p1f-qg-p1
    content: |
      - [ ] [SCRIPT] P0. Phase 1 QG gate: run `bash scripts/quality-gates.sh` on
        unified-api-contracts and unified-trading-library. PM is docs-only (no tests).
        Both MUST pass before moving to Phase 2.
    status: todo
  - id: p1g-commit-p1
    content: |
      - [ ] [SCRIPT] P0. Phase 1 commits via quickmerge --agent (three separate):
        (1) unified-api-contracts: "feat: add ClientSubscription / IsolationPolicy / SLATier / RuntimeProfile / ChaosInjection schemas"
        (2) unified-trading-library: "feat(topology): add isolation + sla + runtime-profile + chaos readers"
        (3) unified-trading-pm: "feat(topology): bump runtime-topology.yaml to v7 with isolation_policies / sla_tiers / runtime_profiles / chaos_hooks + codex SSOT"
    status: todo

  # ===================================================================
  # PHASE 2 — Deployment materialisation (deployment-service + deployment-api)
  # Blocked on Phase 1.
  # ===================================================================
  - id: p2a-deployment-service
    content: |
      - [ ] [AGENT] P1. deployment-service `cluster.py` and `cli/handlers/cluster_handler.py`:
        resolve isolation policy per service via UTL `resolve_deployment()`; for
        `ISOLATED` services, materialise a per-client instance (pod/VM/Cloud Run job with
        `CLIENT_ID` env var); for `SHARED`, route all clients to the shared pool.
        Add `client_subscriptions/` config loader and surfacing via the state manager.
    status: todo
    blocked_by: p1g-commit-p1
  - id: p2b-deployment-api
    content: |
      - [ ] [AGENT] P1. deployment-api new endpoints:
        - `GET/POST /subscriptions` — list + create client subscriptions (uses UAC ClientSubscription)
        - `PATCH /subscriptions/{client_id}` — update overrides/SLA tier
        - `POST /deployments` now accepts `runtime_profile` (UAC RuntimeProfile) and optional `client_id`
        - `POST /chaos/inject` — register chaos injections against a live/staging deployment (uses UAC ChaosInjectionSpec)
        - `GET /chaos/active` — list active chaos injections
        Validate all inputs against UAC models (no dict munging).
    status: todo
    blocked_by: p1g-commit-p1
  - id: p2c-qg-p2
    content: |
      - [ ] [SCRIPT] P1. Phase 2 QG gate: quality-gates.sh on deployment-service + deployment-api. Commit.
    status: todo
    blocked_by: p2b-deployment-api

  # ===================================================================
  # PHASE 3 — Chaos primitives + KillSwitchBus in UTL
  # Blocked on Phase 1 (can run parallel to Phase 2).
  # ===================================================================
  - id: p3a-utl-chaos
    content: |
      - [ ] [AGENT] P1. Add `unified-trading-library/unified_trading_library/chaos/`:
        - `ChaosController` — reads active injections from config/env, exposes hooks:
          `maybe_inject_latency(point, target)`, `maybe_inject_failure(point, target)`,
          `maybe_shock_price(instrument, pct)`, `maybe_flip_config(key, value)`,
          `maybe_delist_instrument(symbol)`, `maybe_mismatch_recon(field, delta)`.
        - Controller is no-op unless the `runtime_profile` declares `chaos_allowed: true`.
        - Hook injection points in UCI (cloud SDK wrappers — latency/failure),
          UAC `classify_venue_error` (failure simulation), and execution-service venue adapters.
    status: todo
    blocked_by: p1g-commit-p1
  - id: p3b-utl-killswitch
    content: |
      - [ ] [AGENT] P1. Add `unified-trading-library/unified_trading_library/kill_switch/`:
        - `KillSwitchBus` — single SSOT primitive with `fire(scope: KillSwitchScope)`,
          `is_active(scope)`, `subscribe(callback)`. Scopes: GLOBAL, CLIENT, VENUE,
          STRATEGY, ARCHETYPE, INSTRUMENT.
        - Uses UAC `KillSwitchSignal` (add if missing) over the configured live transport
          (pubsub/sqs) or in-memory for colocated.
        - Delta-neutral exit mode must be the default for live halt.
    status: todo
    blocked_by: p1g-commit-p1
  - id: p3c-service-subscribers
    content: |
      - [ ] [AGENT] P1. Wire KillSwitchBus subscribers into strategy-service,
        execution-service, risk-and-exposure-service. Each service MUST respect
        GLOBAL + (its scope). Replace any ad-hoc halt code with the bus.
    status: todo
    blocked_by: p3b-utl-killswitch
  - id: p3d-qg-p3
    content: |
      - [ ] [SCRIPT] P1. Phase 3 QG gate on UTL + strategy-service + execution-service +
        risk-and-exposure-service. Commit.
    status: todo
    blocked_by: p3c-service-subscribers

  # ===================================================================
  # PHASE 4 — Runtime profile axis in deployment-api + UI
  # Blocked on Phase 2.
  # ===================================================================
  - id: p4a-deployment-api-profile
    content: |
      - [ ] [AGENT] P1. deployment-api: one `runtime_profile` axis collapses the 5
        legacy env vars. Controller fans out to the correct env var set at VM/pod boot.
        Storage namespace prefix for `backtest` profile = `backtest/<run_id>/`
        so it cannot collide with live GCS paths.
    status: todo
    blocked_by: p2c-qg-p2
  - id: p4b-deployment-ui
    content: |
      - [ ] [AGENT] P1. deployment-ui new pages:
        - `/client-subscriptions` — list/create/edit subscriptions, SLA tier assignment,
          per-service isolation override picker (reads ServiceIsolationSpec.allowed).
        - `/chaos` — active injections + form to create new ones against staging only.
        - `/deployments` form gains `runtime_profile` + optional `client_id` fields.
    status: todo
    blocked_by: p4a-deployment-api-profile
  - id: p4c-qg-p4
    content: |
      - [ ] [SCRIPT] P1. Phase 4 QG gate: quality-gates.sh on deployment-api + vitest on
        deployment-ui. Commit.
    status: todo
    blocked_by: p4b-deployment-ui

  # ===================================================================
  # PHASE 5 — Archetype→topology requirements in strategy docs
  # Blocked on Phase 1.
  # ===================================================================
  - id: p5a-archetype-topology
    content: |
      - [ ] [AGENT] P2. For every archetype in `codex/09-strategy/architecture-v2/families/`:
        add a frontmatter block `topology_requirements: { isolation: {service: policy},
        co_location: [services], latency_budget_ms: N, min_sla_tier: tier }`.
        Examples: MARKET_MAKING → execution+strategy ISOLATED + co_located; ML_DIRECTIONAL_CONTINUOUS →
        all SHARED acceptable; ARBITRAGE_STRUCTURAL → execution ISOLATED, strategy SHARED.
    status: todo
    blocked_by: p1g-commit-p1
  - id: p5b-strategy-service-enforce
    content: |
      - [ ] [AGENT] P2. strategy-service: on start, read its archetype's
        topology_requirements via UAC + UTL and fail loud if the materialised deployment
        doesn't satisfy them (wrong isolation, missing co-location, SLA tier too low).
    status: todo
    blocked_by: p5a-archetype-topology

  # ===================================================================
  # PHASE 6 — Downstream service client_id plumbing
  # Blocked on Phase 2.
  # ===================================================================
  - id: p6a-position-risk-pnl
    content: |
      - [ ] [AGENT] P2. position-balance-monitor, risk-and-exposure, pnl-attribution:
        all three must read the client isolation policy for themselves on boot. In
        SHARED mode they multiplex by client_id (existing topic_template already supports
        this — verify); in ISOLATED mode they bind to a single client_id and refuse
        cross-client events.
    status: todo
    blocked_by: p2c-qg-p2
  - id: p6b-execution-service
    content: |
      - [ ] [AGENT] P2. execution-service: enforce ISOLATED policy (default for this
        service) — one instance per client, per-client venue API keys loaded from
        Secret Manager at `clients/<client_id>/<venue>/api_key` path. Reject any
        cross-client order routing at the bus layer.
    status: todo
    blocked_by: p2c-qg-p2
  - id: p6c-qg-p6
    content: |
      - [ ] [SCRIPT] P2. Phase 6 QG gate on PBM + R&E + PnL-attribution + execution-service. Commit.
    status: todo
    blocked_by: p6b-execution-service

  # ===================================================================
  # PHASE 7 — Simulation / chaos scenarios in e2e-testing
  # Blocked on Phase 3.
  # ===================================================================
  - id: p7a-chaos-scenarios
    content: |
      - [ ] [AGENT] P2. e2e-testing: add chaos scenario scripts (one per ChaosInjectionPoint)
        that run against a `backtest` runtime profile AND a `staging` profile.
        Scenarios must exercise: 20% massive price drop, 5s venue latency injection,
        reconciliation mismatch recovery, dynamic instrument delist mid-run, config
        flip mid-run, kill-switch fire with delta-neutral exit, component failure (one
        feature service dies). Each scenario declares pass/fail criteria.
    status: todo
    blocked_by: p3d-qg-p3
  - id: p7b-backtest-protection
    content: |
      - [ ] [AGENT] P2. e2e-testing: verify `backtest` profile writes only under
        `backtest/<run_id>/` GCS prefix and uses a dedicated Pub/Sub topic namespace
        so concurrent live runs are not affected.
    status: todo
    blocked_by: p7a-chaos-scenarios

  # ===================================================================
  # PHASE 8 — Full workspace QG + INDEX update
  # Final phase. Blocked on all prior.
  # ===================================================================
  - id: p8a-workspace-qg
    content: |
      - [ ] [SCRIPT] P0. Run quality-gates.sh on ALL affected repos (13 listed in repo_gates)
        in batches of max-20-parallel. Report per-repo PASS/FAIL. Zero FAILs allowed to archive.
    status: todo
    blocked_by: p6c-qg-p6
  - id: p8b-index
    content: |
      - [ ] [AGENT] P0. Update `unified-trading-pm/plans/active/INDEX.md` under
        `epic-code-completion` with this plan's entry + progress summary.
    status: todo
    blocked_by: p8a-workspace-qg

isProject: false
---

## Context

### Problem

1. **Isolation is all-or-nothing today.** `runtime-topology.yaml` v6 has a two-plane model (shared L1-L4,
   client-specific L5-L6) but cannot express _per-service_ isolation choices within the client-specific plane. A client
   who pays more should get an isolated execution-service but can share position/risk/pnl with the multi-tenant pool.
   Today they either get everything isolated or everything shared.

2. **No SLA + cost passthrough model.** Neither UAC nor deployment-api knows about tiers. Cost is implicit.

3. **Runtime mode axis is scattered.** Five env vars (`CLOUD_MOCK_MODE`, `MOCK_STATE_MODE`, `DISABLE_AUTH`,
   `VITE_MOCK_API`, `VITE_SKIP_AUTH`) each set separately. No single `runtime_profile` for deployment-api callers.

4. **Simulation primitives do not exist.** No `ChaosController`, no `KillSwitchBus`. Today: cannot simulate massive
   price drops, component latency, reconciliation mismatches, dynamic instruments, config flips, kill-switch fires in a
   backtest — which means staging-vs-prod parity can't be stress-tested.

5. **Strategy archetypes (v2) are silent on deployment.** Which services must co-locate? What isolation does the
   archetype demand? What is the min SLA tier? Today: undocumented.

### Design — Single Addition, Four New Concepts

Extend `runtime-topology.yaml` (v6→v7) with four new concepts; everything else follows.

- **`isolation_policies`** — per-service `{default: shared|isolated, allowed, reason}`. Deployer's choice to override
  within `allowed`.
- **`sla_tiers`** — premium/standard/basic, each declaring cost multiplier, allowed isolations, and which services MUST
  be isolated for that tier. Premium clients pay more → get dedicated execution + strategy; basic clients share
  everything.
- **`runtime_profiles`** — `backtest | paper | mock-live | staging | prod` collapsing the 5 env vars into one choice.
- **`chaos_hooks`** — list of injection points the system exposes, consumed by `ChaosController` in UTL.

### Pre-Audit Manifest (from cross-repo scan, 2026-04-17)

| Area               | File / Path                                                                                                    | Action                                                      |
| ------------------ | -------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| SSOT               | `unified-trading-pm/configs/runtime-topology.yaml`                                                             | v6→v7                                                       |
| Reader             | `unified-trading-library/unified_trading_library/topology/topology_reader.py`                                  | Extend (line 109 reserved-for-future hook is already there) |
| Schemas            | `unified-api-contracts/unified_api_contracts/internal/domain/deployment_service/`                              | New module `isolation.py`                                   |
| Deployment API     | `deployment-api/deployment_api/routes/deployments.py` + new `subscriptions.py`, `chaos.py`                     | Extend + new routes                                         |
| Deployment Service | `deployment-service/deployment_service/cluster.py` + `cli/handlers/cluster_handler.py`                         | Materialisation per isolation policy                        |
| Topology Validator | `deployment-service/deployment_service/runtime_topology_validator.py`                                          | Extend with new sections                                    |
| UI                 | `deployment-ui/src/components/DeployForm.tsx`, new `/client-subscriptions`, `/chaos`                           | New pages + form fields                                     |
| Chaos              | `unified-trading-library/unified_trading_library/chaos/` (new)                                                 | ChaosController primitive                                   |
| KillSwitch         | `unified-trading-library/unified_trading_library/kill_switch/` (new)                                           | KillSwitchBus primitive                                     |
| Subscribers        | strategy-service, execution-service, risk-and-exposure-service (+ PBM, PnL-attribution for client_id plumbing) | Wire bus + policy reader                                    |
| Archetypes         | `codex/09-strategy/architecture-v2/families/*.md` + archetype docs                                             | Add `topology_requirements` frontmatter                     |
| Simulation         | `e2e-testing/`                                                                                                 | Chaos scenarios per ChaosInjectionPoint                     |
| Docs               | New `codex/04-architecture/client-isolation-sla-and-runtime-profiles.md`                                       | SSOT                                                        |

### Execution DAG

```
Phase 1 (PM + UAC + UTL + codex)
    │
    ├─► Phase 2 (deployment-service + deployment-api)
    │       │
    │       └─► Phase 4 (runtime_profile axis + deployment-ui)
    │       │
    │       └─► Phase 6 (downstream service client_id plumbing)
    │               │
    │               └─► Phase 8 (workspace QG + INDEX)
    │
    ├─► Phase 3 (UTL chaos + kill-switch + subscribers)
    │       │
    │       └─► Phase 7 (e2e-testing chaos scenarios)
    │
    └─► Phase 5 (archetype topology_requirements in strategy docs)
```

Phases 2, 3, 5 are parallel after Phase 1. Phases 4, 6, 7 can run in parallel after their respective gates. Phase 8 is
the workspace-wide seal.

### Success Criteria per Phase

- **Phase 1**: PM yaml lint green, UAC pytest green (new test file passes), UTL pytest green (new test file passes),
  codex SSOT doc exists and is linked from 3 cross-link targets.
- **Phase 2**: deployment-service and deployment-api quality-gates.sh PASS; new endpoints have tests; validator accepts
  v7 schema.
- **Phase 3**: UTL QG PASS; ChaosController no-ops cleanly when chaos_allowed=false; KillSwitchBus in-memory + pubsub
  backends tested.
- **Phase 4**: deployment-api QG PASS; deployment-ui vitest PASS; UI form-field integration test confirms
  runtime_profile fans out to correct env vars.
- **Phase 5**: Every archetype doc has `topology_requirements`; strategy-service refuses to start if requirements unmet
  (tested with a failing fixture).
- **Phase 6**: execution-service rejects cross-client orders (test); PBM/R&E/PnL-attribution route by client_id
  correctly in both SHARED and ISOLATED modes.
- **Phase 7**: 7+ chaos scenarios green; backtest namespace isolation verified (no GCS path collision with live).
- **Phase 8**: Zero FAILs in workspace QG sweep; INDEX.md updated.

### Non-Goals (explicit, to prevent scope creep)

- Not building a cost-billing system. SLA tier cost multipliers are metadata; actual invoicing lives in
  `client-reporting-api` future work.
- Not migrating existing live deployments to v7 automatically. v7 adds fields with safe defaults; migration is a
  follow-up plan.
- Not implementing kernel-bypass transport. `in_memory` remains the co-located fast path.

### Downstream Consumer Updates (required by this plan)

Per CLAUDE.md §6 "Downstream Consumer Updates": every repo in `repo_gates` is touched in one plan; no "fix later". Phase
8 enforces zero workspace FAILs.
