---
doc_type: plan
title: data-status-operations-dropdown-cli-derived
summary: Wire the deployment-ui service-operations dropdown to a CLI-derived SSOT so dropdown items match each service's
  actual `--operation` axis and are click-through into the deploy form.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    deployment-api,
    deployment-service,
    deployment-ui,
    execution-service,
    instruments-service,
    market-data-processing-service,
  ]
scope: [engineer, admin]
tags: []
related:
  [
    data_status_multi_axis_shard_propagation_2026_05_06.plan.md,
    shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md,
    master_to_live_defi_2026_05_23.plan.md,
  ]
created: "2026-05-07"
type: code
epic: epic-code-completion
locked_by: live-defi-rollout
locked_since: 2026-05-07
completion_gates: { code: C5, deployment: none, business: none }
repo_gates:
  - { repo: unified-trading-library, code: C0, deployment: none, business: none }
  - { repo: unified-api-contracts, code: C0, deployment: none, business: none }
  - { repo: deployment-api, code: C0, deployment: none, business: none }
  - { repo: deployment-ui, code: C0, deployment: none, business: none }
  - { repo: instruments-service, code: C0, deployment: none, business: none }
  - { repo: market-tick-data-service, code: C0, deployment: none, business: none }
  - { repo: market-data-processing-service, code: C0, deployment: none, business: none }
  - { repo: features-delta-one-service, code: C0, deployment: none, business: none }
  - { repo: features-volatility-service, code: C0, deployment: none, business: none }
  - { repo: features-onchain-service, code: C0, deployment: none, business: none }
  - { repo: features-sports-service, code: C0, deployment: none, business: none }
  - { repo: features-calendar-service, code: C0, deployment: none, business: none }
  - { repo: features-cross-instrument-service, code: C0, deployment: none, business: none }
  - { repo: features-multi-timeframe-service, code: C0, deployment: none, business: none }
  - { repo: features-commodity-service, code: C0, deployment: none, business: none }
  - { repo: ml-training-service, code: C0, deployment: none, business: none }
  - { repo: ml-inference-service, code: C0, deployment: none, business: none }
  - { repo: strategy-service, code: C0, deployment: none, business: none }
  - { repo: execution-service, code: C0, deployment: none, business: none }
  - { repo: unified-trading-pm, code: C0, deployment: none, business: none }
depends_on: []
todos:
  - { id: phase-0-ssot-decision, content: '- [ ] [AGENT] P0. Phase 0 (SEQUENTIAL — gates everything else). SSOT decision
        for service-operation metadata. Pre-audit each of the 15 services (`instruments-service`,
        `market-tick-data-service`, `market-data-processing-service`, `features-delta-one-service`,
        `features-volatility-service`, `features-onchain-service`, `features-sports-service`,
        `features-calendar-service`, `features-cross-instrument-service`, `features-multi-timeframe-service`,
        `features-commodity-service`, `ml-training-service`, `ml-inference-service`, `strategy-service`,
        `execution-service`) to confirm they use `unified_trading_library.service_cli.ServiceCLI` for argparse
        construction. Search per repo: `rg "ServiceCLI\(" --type py --glob ''!.venv*'' --glob ''!tests''`. Build a
        coverage table embedded in this plan (service → uses ServiceCLI Y/N → file:line of the construction).

        - **Decision rule**: if ≥13/15 use `ServiceCLI` → preferred path = lift operations into UTL `ServiceCLI` itself
        (single SSOT, every service inherits introspection automatically). If <13/15 → fallback path = create a UAC
        `registry/service_operations.py` declaration with one entry per service.

        - **Output**: a single short codex page `unified-trading-pm/codex/04-architecture/service-operations-ssot.md`
        documenting the chosen direction + the contract shape (`(name, label, description, requires_modes: list[str],
        requires_asset_groups: list[str])`). Defines the JSON shape returned by the new endpoint; keeps deployment-ui +
        UTL/UAC in lock-step.

        - **Acceptance**: every service in the table has a row; SSOT direction is named (UTL or UAC); contract shape is
        one Python class + one TypeScript interface declared in the codex page.

        ', status: todo, note: "" }
  - { id: phase-1a-utl-or-uac-ssot, content: "- [ ] [AGENT] P0. Phase 1A (PARALLEL inside Phase 1, gated by Phase 0).
        Land the chosen SSOT.

        - **If UTL path** (preferred): extend `unified_trading_library/service_cli.py::ServiceCLI` with a non-breaking
        constructor kwarg `operation_metadata: dict[str, OperationMetadata] | None = None` where `OperationMetadata` is
        a frozen `dataclass(frozen=True, slots=True)` with fields `(label: str, description: str, requires_modes:
        tuple[str, ...], requires_asset_groups: tuple[str, ...])`. Default `None` → labels derive from operation key
        (title-case), description empty. Add classmethod `ServiceCLI.introspect_operations(self) -> list[dict[str, str |
        list[str]]]` that returns the JSON-serialisable shape declared in the codex page. Add 4 unit tests in
        `unified-trading-library/tests/unit/test_service_cli_introspection.py`: (1) defaults work without metadata, (2)
        metadata respected when supplied, (3) frozen dataclass rejects mutation, (4) JSON shape matches codex contract.

        - **If UAC path**: create `unified_api_contracts/registry/service_operations.py` with
        `ServiceOperationDeclaration` dataclass + `SERVICE_OPERATIONS: dict[str, list[ServiceOperationDeclaration]]`
        registered for all 15 services. Export from UAC root facade. Add 2 unit tests covering registry shape +
        completeness (every service in the keys).

        - **Acceptance**: chosen module ships with tests passing per `cd <repo> && bash scripts/quality-gates.sh`.

        ", status: todo, note: "" }
  - { id: phase-1b-deployment-api-endpoint, content: '- [ ] [AGENT] P0. Phase 1B (PARALLEL inside Phase 1, gated by
        Phase 0). Add `GET /api/services/{service_name}/operations` to
        `deployment-api/deployment_api/routes/services.py` (file already hosts `@router.get("/{service_name}")` at line
        92 + `/{service_name}/dimensions` at line 166, sibling pattern is direct). New module
        `deployment-api/deployment_api/services/operations_introspector.py` resolves operations from the SSOT chosen in
        Phase 1A: if UTL path, dynamically import each service''s CLI entrypoint module and call
        `ServiceCLI.introspect_operations()` (cached at module-load time, NOT per-request, since CLI shape is
        process-static); if UAC path, just read `SERVICE_OPERATIONS[service_name]`.

        - **No `os.getenv()`** — read everything from `UnifiedCloudConfig`. **No `from google.cloud import storage`** —
        endpoint is pure read of in-process metadata, no GCS round-trip. Add the endpoint to UTL
        `RequestAuditMiddleware` `_SKIP_PREFIXES` (idempotent UI read; same shape as `/api/data-status/` etc — see the
        2026-05-06 audit-middleware feedback).

        - **Tests**: `deployment-api/tests/unit/test_routes_services_operations.py` covering (1) endpoint returns 200
        with non-empty list for every of the 15 services, (2) 404 for unknown service, (3) shape matches the codex
        contract.

        - **Acceptance**: `cd deployment-api && bash scripts/quality-gates.sh` clean; manual probe `curl
        localhost:8004/api/services/instruments-service/operations` returns the operations list.

        ', status: todo, note: "" }
  - { id: phase-1c-cli-confirmation-pass, content: '- [ ] [AGENT] P0. Phase 1C (PARALLEL inside Phase 1, gated by Phase
        0). Per-service CLI-confirmation pass. For each service that does NOT yet route through `ServiceCLI` (per Phase
        0 table), file a follow-up todo against the service''s own active plan in `unified-trading-pm/plans/active/`. DO
        NOT mass-edit service CLIs in this plan — that''s a separate per-service migration. Goal of this todo: ensure
        none of the 15 services regress. Cross-reference the cli-convention.md SSOT
        (`/codex/06-coding-standards/cli-convention.md`) to confirm `--operation` is the canonical axis everywhere; flag
        (don''t fix) any service whose CLI uses a different flag name.

        - **Acceptance**: a single audit findings comment block appended to this plan after Phase 0 lists "service X CLI
        uses flag Y instead of `--operation` — backfill plan ref Z".

        ', status: todo, note: "" }
  - { id: phase-2a-service-list-fetch, content: "- [ ] [AGENT] P0. Phase 2A (SEQUENTIAL — depends on Phase 1B).
        `deployment-ui/src/components/ServiceList.tsx` — replace the static `SERVICE_REGISTRY` operations field (lines
        47-229) with a TanStack Query hook `useServiceOperations(serviceName)` calling `GET
        /api/services/{service_name}/operations`. Keep the rest of the static fields (`description`, `dimensions`,
        `modes`, `categories`, `operationalModes`) for now — only `operations` becomes dynamic in this phase. While the
        query is loading, render a skeleton row; on error render a small inline error chip with a retry button (do NOT
        fall back to the static registry — that re-introduces drift).

        - **Acceptance**: `cd deployment-ui && CI=true npm test -- --run` passes, `VITE_MOCK_API=true npx vite build`
        succeeds, manual probe via deployment-ui at `http://localhost:5183` shows the same operations list per service
        that the API returns (verify via dev-tools network tab).

        ", status: todo, note: "" }
  - { id: phase-2b-deploy-form-prefill, content: "- [ ] [AGENT] P0. Phase 2B (SEQUENTIAL — depends on Phase 2A).
        `deployment-ui/src/components/DeployForm.tsx` — accept an optional `prefillOperation?: string` (and
        `prefillMode?: string` for execution-service-style multi-mode services where Phase 0 metadata declared
        `requires_modes`) prop. ServiceList.tsx wires a click-handler on each rendered operation: `onClick={() =>
        openDeployForm({ service, prefillOperation: op.value, prefillMode: op.requires_modes?.[0] })}`. DeployForm seeds
        the `--operation` argparse builder with the prefilled value but allows the operator to change it (keeps the
        dropdown free).

        - **Acceptance**: vitest suite covering (1) clicking an operation opens DeployForm with `--operation=<op>`
        pre-selected, (2) default empty when opened directly, (3) operator can override pre-fill before submit. Smoke
        build clean.

        ", status: todo, note: "" }
  - { id: phase-3-cross-service-axis-standardisation, content: '- [ ] [AGENT] P1. Phase 3 (SEQUENTIAL — depends on Phase
        2). Reconcile execution-service `operationalModes` (`live | manual | paper | backtest`) and similar shape
        mismatches with cli-convention.md axes. Two paths: (a) if `operationalModes` IS the same surface as `--mode
        batch/live`, fold it into the `requires_modes` metadata field in the SSOT and delete the parallel field from the
        UI registry; (b) if `operationalModes` is a different axis (e.g. `paper` / `manual` are NOT runtime modes but
        submission policies), document it as a separate per-service axis in
        `/codex/06-coding-standards/cli-convention.md` and surface it as a SECOND dropdown beneath operations.

        - **Decision rule**: read the execution-service CLI source first; if `argparse` declares `--operational-mode`
        separately from `--mode`, it''s case (b); if not, it''s case (a). Default expectation = case (a) per
        cli-convention.md "`--mode` (batch/live)" SSOT.

        - **Acceptance**: cli-convention.md updated with the operational-mode axis decision; deployment-ui renders it
        consistently across the 1-2 services that have it (today: strategy-service + execution-service +
        trading-agent-service).

        ', status: todo, note: "" }
  - { id: phase-4-tests-and-playwright-smoke, content: "- [ ] [AGENT] P1. Phase 4 (SEQUENTIAL — depends on Phase 3).
        Tests + Playwright smoke walk.

        - **Backend**: `deployment-api/tests/integration/test_operations_endpoint_all_services.py` parametrises over the
        full 15-service list, asserts `(status_code == 200) AND (len(operations) >= 1) AND (every op has the
        codex-contract fields)`.

        - **Frontend**: vitest in `deployment-ui/src/components/__tests__/ServiceList.test.tsx` covering loading / error
        / success rendering for the dynamic dropdown.

        - **Playwright**: extend an existing smoke script in `deployment-ui/tests/playwright/` (or create one if none
        exists) that walks each of the 15 service tabs, opens the operations dropdown, clicks each operation, and
        asserts the deploy form opens with the correct `--operation` prefill. Marked `@playwright.allow_network` for the
        localhost backend.

        - **Acceptance**: per-repo `bash scripts/quality-gates.sh` clean for deployment-api + deployment-ui; Playwright
        smoke green against a `restart-deployment-stack.sh` local stack.

        ", status: todo, note: "" }
  - { id: phase-5-codex-update, content: '- [ ] [AGENT] P2. Phase 5 (PARALLEL with Phase 4 — pure docs). Codex update.

        - Extend `unified-trading-pm/codex/06-coding-standards/cli-convention.md` with a new "Operation discovery
        contract" section pointing at the SSOT chosen in Phase 0 + the new `/api/services/{service_name}/operations`
        endpoint shape.

        - Update the deployment-ui codex page (search for `codex/05-infrastructure/deployment-ui*.md` or
        `codex/14-playbooks/deployment-ui*.md`; create one if absent under
        `/codex/14-playbooks/operator-ui/operations-dropdown.md`) to document the click-through behaviour + the prefill
        prop contract.

        - **Acceptance**: PM `bash scripts/quality-gates.sh` clean (markdown lint + scope-registry); both codex pages
        link to this plan + the parent `data_status_multi_axis_shard_propagation_2026_05_06.plan.md`.

        ', status: todo, note: "" }
  - { id: phase-6-workspace-wide-validation, content: "- [ ] [AGENT] P0. Phase 6 (SEQUENTIAL — last gate).
        Workspace-wide QG validation of all 4 directly-modified repos: unified-trading-library OR unified-api-contracts
        (per Phase 0 outcome), deployment-api, deployment-ui, unified-trading-pm. Per-repo `cd <repo> && bash
        scripts/quality-gates.sh`. Confirm none of the 15 service repos regressed (their CLIs are READ in this plan, not
        modified) by spot-checking 3 of them (`instruments-service`, `market-tick-data-service`, `execution-service`)
        with their full QG.

        - **Acceptance**: 4 modified repos green; 3 spot-checked services green.

        ", status: todo, note: "" }
isProject: false
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

## Why

The deployment-ui service-operations dropdown — the sub-items beneath each service tab in
`deployment-ui/src/components/ServiceList.tsx` (e.g. for `market-tick-data-service`: "Download / Gas Fees / Solana DeFi
/ EVM DeFi"; for `instruments-service`: "instruments"; for `execution-service`: "live_execution / backtest") — is
**hardcoded** in a static `SERVICE_REGISTRY` dictionary at lines 47-229. This causes three problems:

1. **Silent drift.** Every time a service adds, removes, or renames an `--operation` value, the UI dropdown is the last
   thing anyone remembers to update. The dropdown lies until someone notices.
2. **Not click-through.** Today the sub-items are pure visual chrome; clicking them does nothing. Operators have no way
   to discover what a service can do AND no way to act on the discovery.
3. **Shape inconsistency.** `execution-service` declares an `operationalModes` field
   (`live / manual / paper / backtest`) at line 173 that the UI doesn't even render, while strategy-service and
   trading-agent-service have it too. The cli-convention.md SSOT (`--operation` / `--mode` / `--asset-group`) says these
   axes are universal across all 15 services; the UI's per-service shape says otherwise.

Operator-UX prerequisite for the master live-DeFi-trading 2026-05-23 cutover (group G item 23 of the readiness
checklist). Operators need to discover + invoke per-service operations from the deployment-ui without having to read
each service's argparse source.

## System-first check (before writing any code)

Per the System-First decision tree (SUB_AGENT_MANDATORY_RULES.md §0):

- Events / logging: `unified-trading-library` already covers it — no new event surface needed.
- New schema / data model: the `OperationMetadata` shape is a candidate for `unified_api_contracts.internal` if Phase 0
  picks the UAC path; if UTL path, lives co-located with `service_cli.py`. NEVER inline in deployment-api or
  deployment-ui.
- Cloud / config: `UnifiedCloudConfig`, no `os.getenv()`.
- Existing UI to extend: deployment-ui already exists for this domain — no new UI repo needed.
- Existing endpoint to extend: `deployment-api/deployment_api/routes/services.py` already hosts `services/{name}` and
  `services/{name}/dimensions` — operations is a sibling, not a new file/router.

No new repos. No new ad-hoc solutions. Single SSOT for service-operation metadata (UTL or UAC, decided in Phase 0).

## Pre-audit blast radius

Embedded so executing agents do not need to re-scan.

| Repo                                  | File                                                                                   | Lines / target                                                                                                         | Action                                                                                                                           |
| ------------------------------------- | -------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `deployment-ui`                       | `src/components/ServiceList.tsx`                                                       | Lines 47-229: static `SERVICE_REGISTRY.operations` per service                                                         | Replace with dynamic fetch via `useServiceOperations(serviceName)` (Phase 2A)                                                    |
| `deployment-ui`                       | `src/components/DeployForm.tsx`                                                        | Add `prefillOperation?: string` prop + thread into `--operation` form field                                            | Phase 2B                                                                                                                         |
| `deployment-api`                      | `deployment_api/routes/services.py`                                                    | After line 166 (after `/{service_name}/dimensions`)                                                                    | Add `@router.get("/{service_name}/operations")` (Phase 1B)                                                                       |
| `deployment-api`                      | `deployment_api/services/operations_introspector.py`                                   | New module                                                                                                             | Resolve operations from SSOT chosen in Phase 1A (Phase 1B)                                                                       |
| `unified-trading-library`             | `unified_trading_library/service_cli.py`                                               | If UTL path: extend `ServiceCLI.__init__` with `operation_metadata` kwarg + add `introspect_operations()` classmethod  | Phase 1A                                                                                                                         |
| `unified-trading-library`             | `unified_trading_library/audit_middleware.py` (or wherever `_SKIP_PREFIXES`)           | Add `/api/services/.*/operations` to skip set (idempotent UI read; same shape as 2026-05-06 audit-middleware feedback) | Phase 1B                                                                                                                         |
| `unified-api-contracts`               | `unified_api_contracts/registry/service_operations.py` + facade re-export              | If UAC path (alternative)                                                                                              | Phase 1A                                                                                                                         |
| Each of 15 services (READ-only audit) | their CLI entrypoint module                                                            | `ServiceCLI(...)` or argparse `add_argument("--operation", ...)`                                                       | Phase 0 audit — confirm operation choices match codex contract; flag (don't fix) drift; backfill via per-service plan (Phase 1C) |
| `unified-trading-pm`                  | `/codex/04-architecture/service-operations-ssot.md`                                    | New page                                                                                                               | Phase 0                                                                                                                          |
| `unified-trading-pm`                  | `/codex/06-coding-standards/cli-convention.md`                                         | New "Operation discovery contract" section                                                                             | Phase 5                                                                                                                          |
| `unified-trading-pm`                  | `/codex/14-playbooks/operator-ui/operations-dropdown.md` (new) or existing UI playbook | Document click-through + prefill                                                                                       | Phase 5                                                                                                                          |

**What this plan canNOT verify** without running it: the actual count of services using `ServiceCLI` vs raw argparse
(executing agent runs the Phase 0 audit). Plan assumes ≥13/15 use ServiceCLI based on workspace-wide adoption history;
if the audit returns <13/15, agent flips to UAC path per the Phase 0 decision rule.

## Per-service axis matrix (current `SERVICE_REGISTRY` vs target CLI-derived)

The 15 in-scope services. "Current dropdown" = what `SERVICE_REGISTRY` declares today
(`deployment-ui/src/components/ServiceList.tsx` lines 47-229). "Actual CLI operations" = filled by Phase 0 audit.
"Drift" = mismatch surface to fix.

| Service                             | Current dropdown ops                                                         | Actual CLI operations (filled by Phase 0) | Drift / notes                                                                  |
| ----------------------------------- | ---------------------------------------------------------------------------- | ----------------------------------------- | ------------------------------------------------------------------------------ |
| `instruments-service`               | `instruments`                                                                | TBD                                       |                                                                                |
| `market-tick-data-service`          | `download` / `collect-gas-fees` / `collect-solana-defi` / `collect-evm-defi` | TBD                                       |                                                                                |
| `market-data-processing-service`    | `process`                                                                    | TBD                                       |                                                                                |
| `features-delta-one-service`        | `compute`                                                                    | TBD                                       |                                                                                |
| `features-volatility-service`       | `compute`                                                                    | TBD                                       |                                                                                |
| `features-onchain-service`          | `compute`                                                                    | TBD                                       |                                                                                |
| `features-sports-service`           | `compute`                                                                    | TBD                                       |                                                                                |
| `features-calendar-service`         | `calendar` / `corporate_actions`                                             | TBD                                       |                                                                                |
| `features-cross-instrument-service` | `compute`                                                                    | TBD                                       |                                                                                |
| `features-multi-timeframe-service`  | `compute`                                                                    | TBD                                       |                                                                                |
| `features-commodity-service`        | `compute`                                                                    | TBD                                       |                                                                                |
| `ml-training-service`               | `train` / `evaluate`                                                         | TBD                                       |                                                                                |
| `ml-inference-service`              | `infer`                                                                      | TBD                                       | dropdown label "Inference" but value `infer` — contract decision in Phase 0    |
| `strategy-service`                  | `backtest` / `trade`                                                         | TBD                                       | also has `operationalModes: live/paper/backtest` not currently rendered        |
| `execution-service`                 | `live_execution` / `backtest`                                                | TBD                                       | also has `operationalModes: live/manual/paper/backtest` not currently rendered |

The Phase 0 audit fills this table inline before any code change.

## Phased execution DAG

```
Phase 0 (SSOT decision + audit table) ──────┐
                                            │
                                            ▼
                            ┌──── Phase 1A (UTL or UAC SSOT)         ────┐
                            │                                              │
                            ├──── Phase 1B (deployment-api endpoint)  ────┤   (1A/1B/1C parallel)
                            │                                              │
                            └──── Phase 1C (per-service audit findings) ──┘
                                            │
                                            ▼
                            Phase 2A (ServiceList.tsx dynamic fetch)
                                            │
                                            ▼
                            Phase 2B (DeployForm prefill)
                                            │
                                            ▼
                            Phase 3 (cross-service axis standardisation)
                                            │
                                            ▼
                ┌───── Phase 4 (tests + Playwright)         ─────┐
                │                                                  │   (4/5 parallel)
                └───── Phase 5 (codex update)                ─────┘
                                            │
                                            ▼
                            Phase 6 (workspace-wide QG)
```

QG gate between every phase boundary (next phase cannot start until prior phase QG passes per affected repo).

## Success criteria per phase

| Phase | Success criteria                                                                                                                                                                                        |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0     | Codex SSOT page `service-operations-ssot.md` shipped; per-service audit table embedded in this plan filled for all 15 services; SSOT direction (UTL or UAC) chosen per the ≥13/15 rule.                 |
| 1A    | UTL or UAC SSOT lands; 4 unit tests pass per `cd <repo> && bash scripts/quality-gates.sh`.                                                                                                              |
| 1B    | `GET /api/services/{name}/operations` returns 200 with non-empty list for every of the 15 services; 404 on unknown; 3 unit tests + 1 integration test green; endpoint added to UTL middleware skip set. |
| 1C    | Audit findings comment block listing per-service CLI flag drift (if any) appended to this plan; backfill todos filed against the relevant per-service plans (NOT this plan).                            |
| 2A    | `cd deployment-ui && CI=true npm test -- --run` clean; smoke build clean; manual probe shows dynamic operations match API response.                                                                     |
| 2B    | Vitest suite covers loading/error/success + click-through prefill + operator override; smoke build clean.                                                                                               |
| 3     | cli-convention.md updated; deployment-ui renders operationalModes consistently across strategy-service / execution-service / trading-agent-service.                                                     |
| 4     | Backend integration test parametrises over 15 services, all green; vitest suite green; Playwright smoke green against local `restart-deployment-stack.sh` stack.                                        |
| 5     | cli-convention.md + operations-dropdown.md codex pages shipped; PM markdown-lint + scope-registry QG clean.                                                                                             |
| 6     | All 4 directly-modified repos pass full QG; 3 spot-checked services (instruments-service / market-tick-data-service / execution-service) pass full QG.                                                  |

## Parallelisation strategy

- Phases 1A / 1B / 1C run **in parallel** — A and B both depend on the Phase 0 SSOT decision but not on each other; C is
  read-only audit. Use 3 sub-agents for the 3 streams.
- Phases 4 / 5 run **in parallel** — tests vs docs, no overlap.
- Within Phase 0, the 15-service CLI audit can be sub-agent-parallelised (5 sub-agents × 3 services each), each
  reporting back its row of the per-service axis matrix.

## What this plan does NOT do (out of scope)

- **The wider Phase 1 writer fixes** from `data_status_multi_axis_shard_propagation_2026_05_06.plan.md` — that's
  manifest write-side correctness for the multi-axis shard atom. This plan is purely the operations-dropdown wiring on
  the read-side / UI surface.
- **Per-service CLI migrations** away from raw argparse to `ServiceCLI` — if Phase 0 finds <13/15 using ServiceCLI, this
  plan goes UAC-route and files per-service migration todos in their respective plans, not here.
- **A wholesale dropdown UX redesign** (drag-to-reorder, favourites, search) — Phase 2 is "click an operation, deploy
  form opens prefilled". Anything beyond that is a follow-up plan.
- **Deployment-flow changes** (the deploy-form submit flow itself, VM launch wiring, env-var injection) — covered by the
  existing deployment-service plans. This plan only changes how the operation gets INTO the deploy form, not what the
  deploy form does after submit.
- **`SERVICE_REGISTRY` dimensions / modes / categories fields** — only `operations` becomes dynamic in this plan.
  `dimensions`, `modes`, `categories` continue to live in the static registry until a follow-up plan chooses to derive
  them from CLI introspection too.

## Temporary states + their canonical follow-up plans

- **`SERVICE_REGISTRY` static fields beyond `operations`** (`dimensions`, `modes`, `categories`, `operationalModes`)
  remain hardcoded after this plan ships. If Phase 3 promotes `operationalModes` to the SSOT, the others stay static
  pending a follow-up plan `data_status_service_registry_full_cli_derivation_TBD.plan.md` (filename + creation deferred
  until this plan reaches Phase 5; not silently accepted as final).
- **15 services may have heterogeneous `--operation` flag names** (most use `--operation` per cli-convention.md, but
  Phase 0 may surface drift). Per-service migration to canonical `--operation` is tracked in each service's own active
  plan, not this one.

## References

- Parent plan that surfaced this as a follow-up Phase 3 sub-slice:
  `unified-trading-pm/plans/archive/data_status_multi_axis_shard_propagation_2026_05_06.plan.md`
- Writer-side companion: `unified-trading-pm/plans/archive/shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md`
- CLI axes SSOT: `unified-trading-pm/codex/06-coding-standards/cli-convention.md` (`--operation` / `--mode` /
  `--asset-group`)
- Operator-UX prerequisite: `unified-trading-pm/plans/active/master_to_live_defi_2026_05_23.plan.md` (group G item 23:
  DART manual-trade gate + operator UX)
- deployment-api endpoint host: `deployment-api/deployment_api/routes/services.py`
- deployment-ui dropdown host: `deployment-ui/src/components/ServiceList.tsx` (lines 47-229)
- deployment-ui form host: `deployment-ui/src/components/DeployForm.tsx`
- UTL ServiceCLI: `unified-trading-library/unified_trading_library/service_cli.py`
- 2026-05-06 audit-middleware skip-set precedent: feedback memo `feedback_audit_middleware_skip_idempotent_ui_reads.md`
