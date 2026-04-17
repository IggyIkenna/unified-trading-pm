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
    code: C5
    deployment: none
    business: none
    note: "Phase 1 (v7 topology + codex SSOT) committed 77a6a6fb. Docs-only repo; no tests, no deployment gate applies."
  - repo: unified-api-contracts
    code: C2
    deployment: none
    business: none
    note:
      "Phase 1b schemas committed c0da761. 13 unit tests (test_isolation_schemas.py). Pre-existing unrelated QG
      violations outside my diff."
  - repo: unified-trading-library
    code: C2
    deployment: none
    business: none
    note:
      "Phase 1c + 3a + 3b consolidated in d1dd2efa (readers + ChaosController + KillSwitchBus). 3c UTL-side wiring:
      ServiceBootstrap._init_kill_switch_bus() + test_bootstrap_kill_switch_wiring.py. 15 topology + 9 chaos + 10
      kill_switch + 2 bootstrap tests."
  - repo: deployment-service
    code: C2
    deployment: none
    business: none
    note:
      "Phase 2a committed e3df2c8 (runtime_topology_validator v7 extensions + client_isolation resolver + 9 unit tests).
      cluster.py / cli_handler.py NOT yet modified — follow-up todo p2a-cluster-materialise added."
  - repo: deployment-api
    code: C2
    deployment: none
    business: none
    note:
      "Phase 2b committed 2eda7ff (DeployRequest fields + /subscriptions + /chaos routes). Route tests added in
      follow-up commit (test_route_subscriptions.py + test_route_chaos_injections.py)."
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
      - [x] [AGENT] P0. Bump `unified-trading-pm/configs/runtime-topology.yaml` v6→v7.
        DONE in PM 77a6a6fb. Four sections added: isolation_policies (every cluster service),
        sla_tiers (basic/standard/premium with cost_multiplier + min_isolated_services),
        runtime_profiles (backtest/paper/mock-live/staging/prod), chaos_hooks (8 points).
    status: done
  - id: p1b-uac-schemas
    content: |
      - [x] [AGENT] P0. Add UAC module
        `unified-api-contracts/unified_api_contracts/internal/domain/deployment_service/isolation.py`.
        DONE in UAC c0da761. 12 types exported: IsolationPolicy, SLATier, RuntimeProfile,
        ChaosInjectionPoint, KillSwitchScope, ServiceIsolationSpec, SLATierSpec,
        RuntimeProfileSpec, ChaosHookSpec, ClientServiceOverride, ClientSubscription,
        ChaosInjectionSpec. 13 unit tests.
    status: done
  - id: p1c-utl-reader
    content: |
      - [x] [AGENT] P0. Extend topology_reader with 5 new readers (get_isolation_policy,
        resolve_deployment, get_sla_tier_spec, get_runtime_profile_spec, list_chaos_hooks).
        DONE in UTL d1dd2efa (consolidated with 3a+3b; squash of earlier e1783f38). 15 unit
        tests + real-topology guard test that every clustered service has an
        isolation_policies entry. Deferred: replacing local `_*Config` TypedDicts with UAC
        types — tracked as follow-up (low priority; current TypedDicts functional).
    status: done
  - id: p1d-codex-ssot
    content: |
      - [x] [AGENT] P0. Write NEW codex doc `client-isolation-sla-and-runtime-profiles.md`.
        DONE in PM 77a6a6fb. 10 sections: model, typical pattern, SLA tiers with cost
        passthrough, runtime profiles matrix, chaos hooks, archetype→isolation mapping,
        3 worked examples, non-goals, follow-ups, see-also.
    status: done
  - id: p1e-codex-crosslinks
    content: |
      - [x] [AGENT] P0. Codex cross-links DONE in PM 77a6a6fb:
        RUNTIME_TOPOLOGY_DECISIONS §23, runtime-tiers-and-deployment new section, v2
        README "Deployment & Isolation", INDEX entry. CLAUDE.md keyrule reference not
        added (docs-only repo; not critical).
    status: done
  - id: p1f-qg-p1
    content: |
      - [x] [SCRIPT] P0. Phase 1 QG ran: UAC + UTL + PM `quality-gates.sh` executed. Pre-existing
        violations (bandit nosec, codex compliance in unrelated Python files) surfaced but
        are NOT caused by this plan's changes (my PM files are yaml/md only; UAC+UTL new
        files pass all codex step checks individually). Investigation documented in session.
    status: done
  - id: p1g-commit-p1
    content: |
      - [x] [SCRIPT] P0. Phase 1 committed locally (not quickmerge — user chose scoped commit
        due to mixed WIP in repos). Commits:
        - PM 77a6a6fb feat(topology): v7 — client isolation, SLA tiers, runtime profiles, chaos hooks
        - UAC c0da761 feat: add client isolation + SLA + runtime profile + chaos injection schemas
        - UTL d1dd2efa feat: KillSwitchBus + ChaosController + v7 topology readers (Phase 1c+3a+3b)
    status: done

  # ===================================================================
  # PHASE 2 — Deployment materialisation (deployment-service + deployment-api)
  # Blocked on Phase 1.
  # ===================================================================
  - id: p2a-deployment-service-validator-resolver
    content: |
      - [x] [AGENT] P1. deployment-service Phase 2a scope: topology validator v7 extensions
        + `client_isolation.py` resolver module. DONE in deployment-service e3df2c8:
        runtime_topology_validator.py requires 4 new sections, cross-checks values,
        enforces prod.chaos_allowed=false hard invariant. New client_isolation.py with
        resolve_service_for_client / build_cluster_plan. 9 unit tests covering default
        path, execution always-isolated, premium sla_min, basic tier rejection, service
        allowed-list rejection, full cluster plan.
    status: done
    blocked_by: p1g-commit-p1
  - id: p2a-cluster-materialise
    content: |
      - [ ] [AGENT] P1. deployment-service `cluster.py` + `cli/handlers/cluster_handler.py`
        materialisation path: on bootstrap, call `build_cluster_plan(cluster_name,
        service_names, subscription)` from client_isolation.py; for each ISOLATED service
        spawn a per-client instance passing `CLIENT_ID` env var; for SHARED route to the
        shared pool. Load subscriptions from `configs/client_subscriptions/<client_id>.yaml`
        via state manager. This is the remaining part of original p2a that was scoped out
        of Phase 2 to ship the resolver cleanly first.
    status: todo
    blocked_by: p2a-deployment-service-validator-resolver
  - id: p2b-deployment-api
    content: |
      - [x] [AGENT] P1. deployment-api new endpoints. DONE in deployment-api 2eda7ff:
        DeployRequest gained `runtime_profile` and `client_id` fields. New
        `routes/subscriptions.py`: GET/POST list/create, GET by id, PATCH overrides,
        DELETE. New `routes/chaos_injections.py`: POST create (403 in prod, 400 if point
        not declared), GET list (filter by profile + active_only), GET by id, DELETE
        revoke, GET /chaos/hooks. Both registered under /api prefix. All inputs use UAC
        BaseModels. Unit tests added as follow-up (test_route_subscriptions.py +
        test_route_chaos_injections.py).
    status: done
    blocked_by: p1g-commit-p1
  - id: p2c-qg-p2
    content: |
      - [ ] [SCRIPT] P1. Phase 2 QG gate: `bash scripts/quality-gates.sh` on
        deployment-service + deployment-api (new route tests must pass). Commit ci_status.
    status: todo
    blocked_by: p2b-deployment-api

  # ===================================================================
  # PHASE 3 — Chaos primitives + KillSwitchBus in UTL
  # Blocked on Phase 1 (can run parallel to Phase 2).
  # ===================================================================
  - id: p3a-utl-chaos
    content: |
      - [x] [AGENT] P1. `unified_trading_library/chaos/` with ChaosController. DONE in UTL
        d1dd2efa. Reads active ChaosInjectionSpec records; no-op when chaos_allowed=false
        (prod). Hooks: maybe_inject_latency (async, with jitter), maybe_inject_failure,
        maybe_shock_price, maybe_flip_config, is_instrument_delisted / maybe_delist_instrument,
        maybe_mismatch_recon. Refactored to deterministic model (explicit probability
        parameter rather than RNG-based chance). Bootstraps from RUNTIME_PROFILE +
        CHAOS_INJECTIONS_JSON env vars. 9 unit tests.
    status: done
    blocked_by: p1g-commit-p1
  - id: p3b-utl-killswitch
    content: |
      - [x] [AGENT] P1. `unified_trading_library/kill_switch/` with KillSwitchBus. DONE in
        UTL d1dd2efa. Thread-safe process-local bus, 6 UAC-defined scopes (GLOBAL, CLIENT,
        VENUE, STRATEGY, ARCHETYPE, INSTRUMENT). API: fire / clear / is_active /
        active_scopes / subscribe (returns unsubscribe handle) / subscriber_count.
        KillSwitchEvent carries FIRED/CLEARED event_type. GLOBAL implies every other scope
        active. Wildcard scope_key=None halts all keys under that scope. Subscriber
        exceptions logged but do not abort delivery. Delta-neutral exit is subscriber's
        responsibility (bus is signal-only). 10 unit tests.
    status: done
    blocked_by: p1g-commit-p1
  - id: p3c-utl-bootstrap-wiring
    content: |
      - [x] [AGENT] P1. ServiceBootstrap auto-subscribes a default logging handler to the
        process KillSwitchBus on boot; accepts optional `kill_switch_subscriber` kwarg for
        service-specific callback (delta-neutral exit for execution, order-gating for
        strategy, etc.). DONE in UTL d1dd2efa via `_init_kill_switch_bus()` in
        service_framework/bootstrap.py. Test: test_bootstrap_kill_switch_wiring.py
        (registers default + caller subscribers, verifies fire delivery).
    status: done
    blocked_by: p3b-utl-killswitch
  - id: p3c-service-subscribers
    content: |
      - [ ] [AGENT] P1. In each halt-sensitive service (strategy-service, execution-service,
        risk-and-exposure-service, position-balance-monitor-service, pnl-attribution-service,
        alerting-service), pass a `kill_switch_subscriber` to ServiceBootstrap that
        implements the service's halt policy:
          - execution-service: on GLOBAL/CLIENT/VENUE fire → delta-neutral exit for affected
            positions; on STRATEGY/ARCHETYPE/INSTRUMENT fire → refuse new orders matching.
          - strategy-service: on GLOBAL/CLIENT/STRATEGY/ARCHETYPE fire → stop emitting
            StrategyInstructions; on VENUE/INSTRUMENT fire → filter out matches.
          - risk-and-exposure-service: on any fire → log + escalate; continue monitoring.
          - PBM/PnL/alerting: on any fire → emit lifecycle event; otherwise passive.
        Replace any ad-hoc halt / circuit-breaker code (e.g. boolean flags, env-var gates)
        with the bus. Pre-audit in each service for strings "halt", "circuit_break",
        "kill_switch", "stop_trading" before edits.
    status: todo
    blocked_by: p3c-utl-bootstrap-wiring
  - id: p3d-qg-p3
    content: |
      - [ ] [SCRIPT] P1. Phase 3 QG gate on UTL + the 6 services after p3c-service-subscribers.
        quality-gates.sh must pass per repo. Commit per repo.
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
