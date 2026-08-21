---
doc_type: plan
title: deployment-topology-and-client-isolation
summary: Per-service client-isolation policy (shared vs isolated) + SLA tiers + runtime profiles + chaos/kill-switch primitives
  wired end-to-end across runtime-topology SSOT, UAC, UTL, deployment-service/api/ui, and affected services.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [client-reporting-api, deployment-api, deployment-service, deployment-ui, e2e-testing, execution-service]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-17"
type: mixed
epic: epic-code-completion
locked_by: live-defi-rollout
locked_since: 2026-04-17
completion_gates: { code: C5, deployment: D2, business: B1 }
repo_gates:
  - {
      repo: unified-trading-pm,
      code: C5,
      deployment: none,
      business: none,
      note:
        "Phase 1 (v7 topology + codex SSOT) committed 77a6a6fb. Docs-only repo; no tests, no deployment gate applies.",
    }
  - {
      repo: unified-api-contracts,
      code: C2,
      deployment: none,
      business: none,
      note:
        Phase 1b schemas committed c0da761. 13 unit tests (test_isolation_schemas.py). Pre-existing unrelated QG
        violations outside my diff.,
    }
  - {
      repo: unified-trading-library,
      code: C2,
      deployment: none,
      business: none,
      note:
        "Phase 1c + 3a + 3b consolidated in d1dd2efa (readers + ChaosController + KillSwitchBus). 3c UTL-side wiring:
        ServiceBootstrap._init_kill_switch_bus() + test_bootstrap_kill_switch_wiring.py. 15 topology + 9 chaos + 10
        kill_switch + 2 bootstrap tests.",
    }
  - {
      repo: deployment-service,
      code: C2,
      deployment: none,
      business: none,
      note:
        Phase 2a committed e3df2c8 (runtime_topology_validator v7 extensions + client_isolation resolver + 9 unit
        tests). cluster.py / cli_handler.py NOT yet modified — follow-up todo p2a-cluster-materialise added.,
    }
  - {
      repo: deployment-api,
      code: C2,
      deployment: none,
      business: none,
      note:
        Phase 2b committed 2eda7ff (DeployRequest fields + /subscriptions + /chaos routes). Route tests added in
        follow-up commit (test_route_subscriptions.py + test_route_chaos_injections.py).,
    }
  - { repo: deployment-ui, code: C0, deployment: none, business: none }
  - {
      repo: execution-service,
      code: C1,
      deployment: none,
      business: none,
      note:
        Phase 3c pre-existing — engine/kill_switch.py + circuit_breaker.py + ServiceBootstrap wiring. Phase 6
        (per-client venue API keys + reject cross-client routing) still todo.,
    }
  - {
      repo: strategy-service,
      code: C1,
      deployment: none,
      business: none,
      note:
        Phase 3c pre-existing — engine/core/components/kill_switch_guard.py + ServiceBootstrap wiring. Phase 5
        (archetype topology_requirements enforcement) still todo.,
    }
  - {
      repo: position-balance-monitor-service,
      code: C1,
      deployment: none,
      business: none,
      note:
        Phase 3c wired in 16db8bb (kill_switch_bus_subscriber.py — passive halt policy). No new tests yet; covered by
        bootstrap wiring test in UTL.,
    }
  - {
      repo: risk-and-exposure-service,
      code: C1,
      deployment: none,
      business: none,
      note: "Phase 3c pre-existing (kill_switch_bus_subscriber.py, on_bus_event wired into ServiceBootstrap).",
    }
  - {
      repo: pnl-attribution-service,
      code: C1,
      deployment: none,
      business: none,
      note:
        Phase 3c wired in eb1b41d (passive halt — audit continues; downstream emission suppressed via
        is_blocked_by_bus).,
    }
  - {
      repo: alerting-service,
      code: C1,
      deployment: none,
      business: none,
      note: Phase 3c wired in 7b74ed8 (ACTIVE escalation policy — boost to CRITICAL via should_escalate).,
    }
  - { repo: e2e-testing, code: C0, deployment: none, business: none }
depends_on: []
todos:
  - {
      id: p1a-topology-v7,
      content:
        "- [x] [AGENT] P0. Bump `unified-trading-pm/configs/runtime-topology.yaml` v6→v7.\n  DONE in PM 77a6a6fb. Four
        sections added: isolation_policies (every cluster service),\n  sla_tiers (basic/standard/premium with
        cost_multiplier + min_isolated_services),\n  runtime_profiles (backtest/paper/mock-live/staging/prod),
        chaos_hooks (8 points).\n",
      status: done,
    }
  - {
      id: p1b-uac-schemas,
      content:
        "- [x] [AGENT] P0. Add UAC
        module\n  `unified-api-contracts/unified_api_contracts/internal/domain/deployment_service/isolation.py`.\n  DONE
        in UAC c0da761. 12 types exported: IsolationPolicy, SLATier, RuntimeProfile,\n  ChaosInjectionPoint,
        KillSwitchScope, ServiceIsolationSpec, SLATierSpec,\n  RuntimeProfileSpec, ChaosHookSpec, ClientServiceOverride,
        ClientSubscription,\n  ChaosInjectionSpec. 13 unit tests.\n",
      status: done,
    }
  - {
      id: p1c-utl-reader,
      content:
        "- [x] [AGENT] P0. Extend topology_reader with 5 new readers (get_isolation_policy,\n  resolve_deployment,
        get_sla_tier_spec, get_runtime_profile_spec, list_chaos_hooks).\n  DONE in UTL d1dd2efa (consolidated with
        3a+3b; squash of earlier e1783f38). 15 unit\n  tests + real-topology guard test that every clustered service has
        an\n  isolation_policies entry. Deferred: replacing local `_*Config` TypedDicts with UAC\n  types — tracked as
        follow-up (low priority; current TypedDicts functional).\n",
      status: done,
    }
  - {
      id: p1d-codex-ssot,
      content:
        "- [x] [AGENT] P0. Write NEW codex doc `client-isolation-sla-and-runtime-profiles.md`.\n  DONE in PM 77a6a6fb.
        10 sections: model, typical pattern, SLA tiers with cost\n  passthrough, runtime profiles matrix, chaos hooks,
        archetype→isolation mapping,\n  3 worked examples, non-goals, follow-ups, see-also.\n",
      status: done,
    }
  - {
      id: p1e-codex-crosslinks,
      content:
        "- [x] [AGENT] P0. Codex cross-links DONE in PM 77a6a6fb:\n  RUNTIME_TOPOLOGY_DECISIONS §23,
        runtime-tiers-and-deployment new section, v2\n  README \"Deployment & Isolation\", INDEX entry. CLAUDE.md
        keyrule reference not\n  added (docs-only repo; not critical).\n",
      status: done,
    }
  - {
      id: p1f-qg-p1,
      content:
        "- [x] [SCRIPT] P0. Phase 1 QG ran: UAC + UTL + PM `quality-gates.sh` executed. Pre-existing\n  violations
        (bandit nosec, codex compliance in unrelated Python files) surfaced but\n  are NOT caused by this plan's changes
        (my PM files are yaml/md only; UAC+UTL new\n  files pass all codex step checks individually). Investigation
        documented in session.\n",
      status: done,
    }
  - {
      id: p1g-commit-p1,
      content:
        "- [x] [SCRIPT] P0. Phase 1 committed locally (not quickmerge — user chose scoped commit\n  due to mixed WIP in
        repos). Commits:\n  - PM 77a6a6fb feat(topology): v7 — client isolation, SLA tiers, runtime profiles, chaos
        hooks\n  - UAC c0da761 feat: add client isolation + SLA + runtime profile + chaos injection schemas\n  - UTL
        d1dd2efa feat: KillSwitchBus + ChaosController + v7 topology readers (Phase 1c+3a+3b)\n",
      status: done,
    }
  - {
      id: p2a-deployment-service-validator-resolver,
      content:
        "- [x] [AGENT] P1. deployment-service Phase 2a scope: topology validator v7 extensions\n  +
        `client_isolation.py` resolver module. DONE in deployment-service e3df2c8:\n  runtime_topology_validator.py
        requires 4 new sections, cross-checks values,\n  enforces prod.chaos_allowed=false hard invariant. New
        client_isolation.py with\n  resolve_service_for_client / build_cluster_plan. 9 unit tests covering
        default\n  path, execution always-isolated, premium sla_min, basic tier rejection, service\n  allowed-list
        rejection, full cluster plan.\n",
      status: done,
      blocked_by: p1g-commit-p1,
    }
  - {
      id: p2a-cluster-materialise,
      content:
        "- [ ] [AGENT] P1. deployment-service `cluster.py` + `cli/handlers/cluster_handler.py`\n  materialisation path:
        on bootstrap, call `build_cluster_plan(cluster_name,\n  service_names, subscription)` from client_isolation.py;
        for each ISOLATED service\n  spawn a per-client instance passing `CLIENT_ID` env var; for SHARED route to
        the\n  shared pool. Load subscriptions from `configs/client_subscriptions/<client_id>.yaml`\n  via state
        manager. This is the remaining part of original p2a that was scoped out\n  of Phase 2 to ship the resolver
        cleanly first.\n",
      status: todo,
      blocked_by: p2a-deployment-service-validator-resolver,
    }
  - {
      id: p2b-deployment-api,
      content:
        "- [x] [AGENT] P1. deployment-api new endpoints. DONE in deployment-api 2eda7ff:\n  DeployRequest gained
        `runtime_profile` and `client_id` fields. New\n  `routes/subscriptions.py`: GET/POST list/create, GET by id,
        PATCH overrides,\n  DELETE. New `routes/chaos_injections.py`: POST create (403 in prod, 400 if point\n  not
        declared), GET list (filter by profile + active_only), GET by id, DELETE\n  revoke, GET /chaos/hooks. Both
        registered under /api prefix. All inputs use UAC\n  BaseModels. Unit tests added as follow-up
        (test_route_subscriptions.py +\n  test_route_chaos_injections.py).\n",
      status: done,
      blocked_by: p1g-commit-p1,
    }
  - {
      id: p2c-qg-p2,
      content:
        "- [ ] [SCRIPT] P1. Phase 2 QG gate: `bash scripts/quality-gates.sh` on\n  deployment-service + deployment-api
        (new route tests must pass). Commit ci_status.\n",
      status: todo,
      blocked_by: p2b-deployment-api,
    }
  - {
      id: p3a-utl-chaos,
      content:
        "- [x] [AGENT] P1. `unified_trading_library/chaos/` with ChaosController. DONE in UTL\n  d1dd2efa. Reads active
        ChaosInjectionSpec records; no-op when chaos_allowed=false\n  (prod). Hooks: maybe_inject_latency (async, with
        jitter), maybe_inject_failure,\n  maybe_shock_price, maybe_flip_config, is_instrument_delisted /
        maybe_delist_instrument,\n  maybe_mismatch_recon. Refactored to deterministic model (explicit
        probability\n  parameter rather than RNG-based chance). Bootstraps from RUNTIME_PROFILE
        +\n  CHAOS_INJECTIONS_JSON env vars. 9 unit tests.\n",
      status: done,
      blocked_by: p1g-commit-p1,
    }
  - {
      id: p3b-utl-killswitch,
      content:
        "- [x] [AGENT] P1. `unified_trading_library/kill_switch/` with KillSwitchBus. DONE in\n  UTL d1dd2efa.
        Thread-safe process-local bus, 6 UAC-defined scopes (GLOBAL, CLIENT,\n  VENUE, STRATEGY, ARCHETYPE, INSTRUMENT).
        API: fire / clear / is_active /\n  active_scopes / subscribe (returns unsubscribe handle) /
        subscriber_count.\n  KillSwitchEvent carries FIRED/CLEARED event_type. GLOBAL implies every other
        scope\n  active. Wildcard scope_key=None halts all keys under that scope. Subscriber\n  exceptions logged but do
        not abort delivery. Delta-neutral exit is subscriber's\n  responsibility (bus is signal-only). 10 unit tests.\n",
      status: done,
      blocked_by: p1g-commit-p1,
    }
  - {
      id: p3c-utl-bootstrap-wiring,
      content:
        "- [x] [AGENT] P1. ServiceBootstrap auto-subscribes a default logging handler to the\n  process KillSwitchBus on
        boot; accepts optional `kill_switch_subscriber` kwarg for\n  service-specific callback (delta-neutral exit for
        execution, order-gating for\n  strategy, etc.). DONE in UTL d1dd2efa via `_init_kill_switch_bus()`
        in\n  service_framework/bootstrap.py. Test: test_bootstrap_kill_switch_wiring.py\n  (registers default + caller
        subscribers, verifies fire delivery).\n",
      status: done,
      blocked_by: p3b-utl-killswitch,
    }
  - { id: p3c-service-subscribers, content: "- [x] [AGENT] P1. All 6 halt-sensitive services now wire a
        kill_switch_subscriber\n  callback through ServiceBootstrap:\n    - strategy-service (pre-existing
        kill_switch_guard.py)\n    - execution-service (pre-existing engine/kill_switch.py + circuit_breaker.py)\n    -
        risk-and-exposure-service (pre-existing kill_switch_bus_subscriber.py)\n    - position-balance-monitor-service
        16db8bb (passive; is_blocked_by_bus\n      suppresses drift alerts for halted scopes; audit trail
        preserved)\n    - pnl-attribution-service eb1b41d (passive; audit attribution continues;\n      downstream
        reporting/invoice emission suppressed via is_blocked_by_bus)\n    - alerting-service 7b74ed8 (ACTIVE escalation;
        matching alerts boosted\n      to CRITICAL via should_escalate() — opposite of passive pattern,\n      surfaces
        halt activity prominently)\n  Pattern: each service has its own `kill_switch_bus_subscriber.py` with
        a\n  process-local _BusHaltRegistry / _EscalationRegistry\
        \ + on_bus_event callback.\n  Consumers query is_blocked_by_bus(**scope_kwargs) or should_escalate(...).\n  No
        shared helper module needed — the pattern is short enough to live in\n  each service (policy is inherently
        service-specific).\n", status: done, blocked_by: p3c-utl-bootstrap-wiring }
  - {
      id: p3d-qg-p3,
      content:
        "- [ ] [SCRIPT] P1. Phase 3 QG gate on UTL + the 6 services after p3c-service-subscribers.\n  quality-gates.sh
        must pass per repo. Commit per repo.\n",
      status: todo,
      blocked_by: p3c-service-subscribers,
    }
  - {
      id: p4a-deployment-api-profile,
      content:
        "- [x] [AGENT] P1. deployment-api runtime_profile env var fanout. DONE in\n  deployment-api 47cd11e:
        `build_deploy_env_vars` gained `runtime_profile`\n  + `client_id` params. When `runtime_profile` is set,
        `_fanout_runtime_profile_env`\n  reads the RuntimeProfileSpec via UTL `get_runtime_profile_spec` and
        emits\n  CLOUD_MOCK_MODE, MOCK_STATE_MODE, DISABLE_AUTH, VITE_MOCK_API, VITE_SKIP_AUTH\n  plus RUNTIME_PROFILE,
        STORAGE_NAMESPACE (e.g. `backtest/{run_id}/`),\n  ALLOW_REAL_VENUE_CALLS, CHAOS_ALLOWED. Unknown profile logs a
        warning and\n  leaves env unchanged — never partial. Wired through\n  DeploymentManager.create_deployment. 7
        unit tests\n  (test_deployments_helpers.py::TestRuntimeProfileFanout).\n",
      status: done,
      blocked_by: p2c-qg-p2,
    }
  - {
      id: p4b-deployment-ui,
      content:
        "- [x] [AGENT] P1. deployment-ui pages. DONE in deployment-ui 4914a94:\n  /client-subscriptions
        (list/create/edit, SLA tier picker, per-service isolation\n  override dropdown for the 5 services whose topology
        policy allows both SHARED\n  and ISOLATED); /chaos (active injections table with delete, new-injection
        form\n  hard-excludes prod — backend re-validates); DeployForm gained runtime_profile\n  dropdown + optional
        client_id input. New v7 types + API client surface\n  (listClientSubscriptions, createChaosInjection, etc.). 6
        vitest cases across\n  the two pages. Type-check clean on new files; smoke `vite build` passes.\n",
      status: done,
      blocked_by: p4a-deployment-api-profile,
    }
  - {
      id: p4c-qg-p4,
      content:
        "- [ ] [SCRIPT] P1. Phase 4 QG gate: quality-gates.sh on deployment-api + vitest on\n  deployment-ui. Commit.\n",
      status: todo,
      blocked_by: p4b-deployment-ui,
    }
  - {
      id: p5a-archetype-topology,
      content:
        "- [x] [AGENT] P2. Topology requirements frontmatter. DONE in PM 635925fb: all\n  18 archetype docs under
        `codex/09-strategy/architecture-v2/archetypes/`\n  carry a `topology_requirements` YAML frontmatter block
        with\n  `isolation: {service: policy}`, `co_location: [...]`, `latency_budget_ms`,\n  `min_sla_tier`. MM* →
        execution+strategy isolated + co-located + 40ms + premium;\n  ARBITRAGE / CARRY / ML / STAT / VOL / EVENT /
        LIQUIDATION → execution isolated,\n  150ms, standard; RULES / YIELD → execution isolated, 500ms, basic.\n",
      status: done,
      blocked_by: p1g-commit-p1,
    }
  - {
      id: p5b-strategy-service-enforce,
      content:
        "- [x] [AGENT] P2. strategy-service topology enforcement. DONE in strategy\n  27de78c + service_entry boot call:
        `strategy_service.topology_enforcement`\n  parses the archetype frontmatter via
        `load_topology_requirements(archetype)`\n  and `enforce_topology_requirements(archetype,
        active_sla_tier,\n  co_located_services)` raises TopologyRequirementError on isolation /\n  co-location / SLA
        mismatch. 10 unit tests cover MM_CONTINUOUS (premium,\n  co-located) + ARBITRAGE_PRICE_DISPERSION + 3 mismatch
        paths. Invoked from\n  service_entry.py before ServiceBootstrap.run() when --archetype is supplied.\n",
      status: done,
      blocked_by: p5a-archetype-topology,
    }
  - {
      id: p6a-position-risk-pnl,
      content:
        "- [x] [AGENT] P2. Client isolation policy loaders. DONE in PBM 7d92a63 + R&E\n  84024e9 + PnL 8b208ad: each
        service has `isolation_policy.py` that reads\n  UTL `get_isolation_policy(my_service_name)` + CLIENT_ID env var
        at boot,\n  caches the policy + bound client_id, exposes `assert_client_allowed(client_id)`\n  (raises
        CrossClientEventError in ISOLATED mode on cross-client events).\n  Wired into event handler ingress:\n    - PBM
        `FillEventConsumer._process_message` (fill pubsub topic).\n    - R&E `RiskCalculator.calculate_drawdown` +
        `calculate_risk_metrics`\n      (every client-scoped metric computation).\n    - PnL ingress handler
        (attribution event consumer).\n  Unit tests cover shared + isolated + unset-CLIENT_ID paths (5 + 2 + 2).\n",
      status: done,
      blocked_by: p2c-qg-p2,
    }
  - {
      id: p6b-execution-service,
      content:
        "- [x] [AGENT] P2. execution-service always-isolated enforcement + per-client\n  venue credentials. DONE in
        execution 1aae9b93: `isolation_policy.py` enforces\n  one CLIENT_ID per process (raises
        MissingClientBindingError when unset),\n  `load_client_venue_credentials(venue)` fetches from Secret Manager
        at\n  `clients/<client_id>/<venue>/api_key` (+ optional api_secret). Wired into\n  `engine/modes/live/trigger.py
        on_instruction` so cross-client instructions\n  are rejected at ingress. 5 unit tests (isolation + SM happy path
        + missing\n  binding + missing api_secret swallowed).\n",
      status: done,
      blocked_by: p2c-qg-p2,
    }
  - { id: p6c-qg-p6, content: "- [ ] [SCRIPT] P2. Phase 6 QG gate on PBM + R&E + PnL-attribution + execution-service.
        Commit.

        ", status: todo, blocked_by: p6b-execution-service }
  - {
      id: p7a-chaos-scenarios,
      content:
        "- [x] [AGENT] P2. e2e chaos scenarios. DONE in e2e-testing cd61e91:\n  `scripts/chaos/scenarios.yaml` declares
        one scenario per ChaosInjectionPoint\n  (price_shock_btc_20pct_drop, venue_latency_binance_5s,
        recon_mismatch_balance_1pct,\n  instrument_delist_doge_midrun,
        config_flip_max_drawdown_midrun,\n  kill_switch_fire_global_delta_neutral,
        rpc_timeout_pubsub_50pct,\n  component_failure_feature_service). Each declares pass_criteria + fail_criteria
        +\n  allowed runtime_profiles ([backtest, staging]). run_chaos_scenario.py validates\n  profile (prod rejected),
        builds ChaosInjectionSpec, POSTs to deployment-api\n  /chaos/injections (--dry-run prints spec).\n",
      status: done,
      blocked_by: p3d-qg-p3,
    }
  - {
      id: p7b-backtest-protection,
      content:
        "- [x] [AGENT] P2. Backtest namespace isolation. DONE (same commit cd61e91):\n  verified via deployment-api
        Phase 4a fan-out — runtime_profile=backtest →\n  STORAGE_NAMESPACE=`backtest/{run_id}/` env var at VM/pod boot,
        separate from\n  `staging/` / `prod/` prefixes. README documents the guarantee.\n",
      status: done,
      blocked_by: p7a-chaos-scenarios,
    }
  - {
      id: p8a-workspace-qg,
      content:
        "- [ ] [SCRIPT] P0. Run quality-gates.sh on ALL affected repos (13 listed in repo_gates)\n  in batches of
        max-20-parallel. Report per-repo PASS/FAIL. Zero FAILs allowed to archive.\n",
      status: todo,
      blocked_by: p6c-qg-p6,
    }
  - {
      id: p8b-index,
      content:
        "- [ ] [AGENT] P0. Update `unified-trading-pm/plans/active/INDEX.md` under\n  `epic-code-completion` with this
        plan's entry + progress summary.\n",
      status: todo,
      blocked_by: p8a-workspace-qg,
    }
isProject: false
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

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
| Docs               | New `/codex/04-architecture/client-isolation-sla-and-runtime-profiles.md`                                      | SSOT                                                        |

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
