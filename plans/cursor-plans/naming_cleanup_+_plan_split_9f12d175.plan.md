---
name: Naming Cleanup + Plan Split
overview: |
  Clean up all naming inconsistencies across codex/deployment-v3/configs to match the two SSOT SVG diagrams, resolve SSOT doc conflicts, and split the consolidated plan into 3 correctly-ordered phases (Foundation → Library Tiers → Services+Integration).
todos:
  - id: naming-cleanup-deployment-v3
    content: |
      Fix all old names in unified-trading-deployment-v3/configs/: market-tick-data-handler → market-tick-data-service (~50 hits across dependencies.yaml, PARADISE_WORKFLOW.yaml, checklist files, data-catalogues, sharding_config.yaml, stable_versions.yaml, etc.), position-balance-monitor → position-balance-monitor-service (data-catalogue.pnl-attribution-service.yaml x14, RUNTIME_TOPOLOGY_DECISIONS.md x2), client-reporting-api → client-reporting-api (RUNTIME_TOPOLOGY_DECISIONS.md x1), bare 'infra' type example in RUNTIME_TOPOLOGY_DECISIONS.md Section 1. Also fix unified-trading-system-repos.code-workspace (1 hit).
    status: completed
  - id: naming-cleanup-codex
    content: |
      Fix all old names in unified-trading-codex/ active docs: alerting-service → alerting-service in service-registry.yaml; market-tick-data-handler → market-tick-data-service across service-registry.yaml, 10-audit files, 06-coding-standards, 05-infrastructure/ci-cd.md, 02-data, 03-observability, 07-security/fca-compliance.md, validators, scripts; client-reporting-api → client-reporting-api across 00-SSOT-INDEX.md, 06-coding-standards, 10-audit, 03-observability, etc. Skip archive/ subdirs.
    status: completed
  - id: naming-cleanup-plan
    content: |
      Fix old names in consolidated_remaining_work.plan.md task descriptions: codex-orphan-repos-doc uses 'client-reporting-api (CRS)'; dag-api-services-cluster uses 'CRS (client-reporting-api)'; ui-local-dev-setup uses 'client-reporting-api (8003)'. Replace all with 'client-reporting-api'.
    status: completed
  - id: ssot-index-update
    content: |
      Update unified-trading-codex/00-SSOT-INDEX.md: (1) Add WORKSPACE_MANIFEST_DAG.svg as canonical visual for topological build order; (2) Add RUNTIME_DEPLOYMENT_TOPOLOGY_DAG.svg as canonical visual for runtime topology; (3) Fix row 'client-reporting-api' references to 'client-reporting-api'; (4) Note that SERVICE_DEPENDENCY_DIAGRAM.md and SERVICE_DEPENDENCY_GRAPH.md are archived and superseded by INTERNAL_DEPENDENCY_GRAPH.md + TOPOLOGY-DAG.md + SVGs.
    status: completed
  - id: codex-tier-arch-header
    content: |
      Add clarifying scope header to unified-trading-codex/05-infrastructure/unified-libraries/TIER-ARCHITECTURE.md: states this doc covers library-layer tiers (T0-T2 only) and defers to 04-architecture/TIER-ARCHITECTURE.md for full system tier model. Also add missing libs: EAL, UIC_INT, MEL (T0), UDEI, USEI (T2).
    status: completed
  - id: codex-api-services-cluster-doc
    content: |
      Create unified-trading-codex/04-architecture/api-services-cluster.md: document the 4 API service repos that sit between service tier and UIs: execution-results-api (ERA), market-data-api (MDA), client-reporting-api (CRA), strategy-ui. For each: repo URL, status, FastAPI+OAuth pattern, which service it proxies, which UI it serves. Use canonical names only.
    status: completed
  - id: codex-ui-separation-doc
    content: |
      Create unified-trading-codex/06-coding-standards/ui-service-separation.md: mirror .cursor/rules/ui-service-separation.mdc content as a codex reference doc. Cover: UI must be separate git repo, services expose FastAPI+SSE, UIs consume via HTTP/SSE only, no direct library imports from service engine repos in UI.
    status: completed
  - id: codex-service-pair-flows-doc
    content: |
      Create unified-trading-codex/08-workflows/service-pair-flows.md: document all data flows per canonical DAG edges in YAML service-pairs format. Include: MTDH→GCS/PubSub, GCS→features/ML/ strategy/exec, PubSub→features/strategy/ML, EXEC→ERA, IS→UMI/UDC. Each entry has: producer, consumer, message_bus (GCS/PubSub/Redis), batch_schema_class, live_schema_class. This is the SSOT for e2e-service-pair-registry.
    status: completed
  - id: dag-tier-corrections-codex
    content: |
      Apply dag-tier-corrections across codex + manifest: update any codex doc that says URDI=Tier2 to Tier0; UDC=Tier2 to Tier3; EAL=Tier0; MEL=Tier0. Add manifest note for UDC arch_tier field. Update lib-phase3 description in plan to correctly say URDI is Tier 0 hardening, not Tier 2.
    status: completed
  - id: split-plan-phase1
    content: |
      Create unified-trading-pm/plans/cursor-plans/phase1_foundation_prep.plan.md with: naming cleanup tracking, SSOT doc tasks, Phase 0 STREAM A (CI/CD rollout to 55 repos), Phase 0 STREAM B (deployment structure split: UTD V3 → deployment-engine+api+ui, visualizer-ui/api extraction, system-integration-tests repo, infra-merge-utdv3), Phase 0 STREAM C (QG baseline audit), cursor rules (arch-ui-separation-rule, aws-migration-cursor-rule, dag-enforcement.mdc). Done criteria: all 55 repos have quickmerge + commit-msg hook, CI/CD live, naming consistent.
    status: completed
  - id: split-plan-phase2
    content: |
      Create unified-trading-pm/plans/cursor-plans/phase2_library_tier_hardening.plan.md with: global violation sweep, then T0 (8 parallel repos with Layer 0 contract tests), T1 (UTS), T2 (7 parallel repos), T3 (UDC). Each tier: Step A (deploy structure) → B (tests first) → C (code rewrite) → D (--unit-only) → E (full quickmerge). Progressive validation: --lint-only → --unit-only → --qg-only → --quick → full. Tier green = full quickmerge exits 0. All T0-T3 todos from consolidated plan.
    status: completed
  - id: split-plan-phase3
    content: |
      Create unified-trading-pm/plans/cursor-plans/phase3_service_hardening_integration.plan.md with: T4 services in DAG pipeline order (IS→MTDH/MDPS→Features→ML→Strategy+Exec→Monitoring), T5 API services (3 parallel), T6 UIs (11 parallel), Integration Layer 1 per service, Layer 2 infra-verify, Layer 3a smoke + Layer 3b full e2e, cross-cutting auth/codex tasks, post-refactor validation (sandbox deploy→Layer2→3a→3b→healthy). Full quickmerge with act is LAST gate.
    status: completed
  - id: update-consolidated-as-index
    content: |
      Update consolidated_remaining_work.plan.md: keep Agent Bootstrap + Preflight Checklist unchanged. Convert Execution Order section to a phase index pointing to phase1_, phase2_, phase3_ plan files. Keep Priority Quick-Reference and Auth Items Summary for cross-reference.
    status: completed
isProject: true
---

# Naming Cleanup, SSOT Alignment & Plan Split

## Canonical Reference: The Two SSOT SVGs

All repo and service names must align to these two diagrams — they are the ground truth:

- `[WORKSPACE_MANIFEST_DAG.svg](unified-trading-codex/04-architecture/WORKSPACE_MANIFEST_DAG.svg)` — 55 repos across 9 levels (L0–L8), topological build order, SSOT: `workspace-manifest.json`
- `[RUNTIME_DEPLOYMENT_TOPOLOGY_DAG.svg](unified-trading-deployment-v3/configs/RUNTIME_DEPLOYMENT_TOPOLOGY_DAG.svg)` — runtime interaction topology, SSOT: `runtime-topology.yaml`

---

## Part 1: Naming Inconsistencies (No Backward Compatibility)

Old names must be replaced everywhere — no aliases, no legacy comments, no fallback references.

### Violations found

`**unified-trading-deployment-v3/configs/` — ~50+ total occurrences**


| Old Name                   | Canonical Name                     | Files (key)                                                                                                                                                                                                                                                                                                                                                                                                                                             | Count |
| -------------------------- | ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----- |
| `market-tick-data-handler` | `market-tick-data-service`         | `dependencies.yaml`, `PARADISE_WORKFLOW.yaml`, `checklist.market-tick-data-service.yaml` (internal), `sharding_config.yaml`, `expected_start_dates.yaml`, `stable_versions.yaml`, `checklist.prerequisites.yaml`, `checklist.execution-service.yaml`, `checklist.market-data-processing-service.yaml`, `data-catalogue.*.yaml`, `cloud-providers.yaml`, `data-providers.yaml`, `representative_instruments.yaml`, `RUNTIME_DEPLOYMENT_TOPOLOGY_DAG.dot` | ~50   |
| `position-balance-monitor` | `position-balance-monitor-service` | `data-catalogue.pnl-attribution-service.yaml` (14×), `RUNTIME_TOPOLOGY_DECISIONS.md` (2×)                                                                                                                                                                                                                                                                                                                                                               | ~17   |
| `client-reporting-api` | `client-reporting-api`             | `RUNTIME_TOPOLOGY_DECISIONS.md`                                                                                                                                                                                                                                                                                                                                                                                                                         | 1     |
| `infra` (bare type)        | `ibkr-gateway-infra`               | `RUNTIME_TOPOLOGY_DECISIONS.md` §1 naming-pattern table                                                                                                                                                                                                                                                                                                                                                                                                 | 1     |


Also: `unified-trading-system-repos.code-workspace` — 1 `market-tick-data-handler` hit.

`**unified-trading-codex/` — active docs (skip `archive/` subdirs)**


| Old Name                   | Canonical Name                     | Key files                                                                                                                                                                                    |
| -------------------------- | ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `alerting-service`          | `alerting-service`                 | `11-project-management/service-registry.yaml` (1×)                                                                                                                                           |
| `market-tick-data-handler` | `market-tick-data-service`         | `service-registry.yaml` (6×), `10-audit/` files, `06-coding-standards/`, `05-infrastructure/ci-cd.md`, `02-data/`, `03-observability/`, `07-security/fca-compliance.md`, validators, scripts |
| `client-reporting-api` | `client-reporting-api`             | `00-SSOT-INDEX.md`, `06-coding-standards/README.md`, `testing.md`, `quality-gates.md`, multiple `10-audit/` files, multiple `03-observability/` files                                        |
| `position-balance-monitor` | `position-balance-monitor-service` | Various active docs                                                                                                                                                                          |


`**consolidated_remaining_work.plan.md` — task description text**


| Task ID                    | Old text                          | Fix                           |
| -------------------------- | --------------------------------- | ----------------------------- |
| `codex-orphan-repos-doc`   | `client-reporting-api (CRS)`  | `client-reporting-api (CRA)`  |
| `dag-api-services-cluster` | `CRS (client-reporting-api)`  | `CRA (client-reporting-api)`  |
| `ui-local-dev-setup`       | `client-reporting-api (8003)` | `client-reporting-api (8003)` |


**Already clean** (no changes needed):

- `.cursor/rules/` — all clean
- `workspace-manifest.json` — uses canonical names
- `LIBRARY-DEPENDENCY-MATRIX.md`, `INTERNAL_DEPENDENCY_GRAPH.md` — clean

---

## Part 2: SSOT Doc Alignment

### Conflicts to resolve (existing plan tasks)

- `**codex-tier-arch-conflict-resolve`** (P1): `05-infrastructure/unified-libraries/TIER-ARCHITECTURE.md` lacks a scope header — add one clarifying it covers library tiers (T0-T2) only, defer to `04-architecture/TIER-ARCHITECTURE.md` for full system; also add missing libs: EAL, UIC_INT, MEL (T0), UDEI, USEI (T2)
- `**dag-tier-corrections`** (pending in plan): Fix tier numbering in codex + manifest — URDI=Tier0 (not T2), UDC=Tier3, EAL=Tier0, MEL=Tier0; update `lib-phase3` description in plan
- `**topology-ssot-index-update**`: Update `00-SSOT-INDEX.md` — add rows for `WORKSPACE_MANIFEST_DAG.svg` (topological build order visual) and `RUNTIME_DEPLOYMENT_TOPOLOGY_DAG.svg` (runtime topology visual) as canonical SSOT entries
- `**codex-service-dependency-diagram-v3**`: The old `04-architecture/archive/SERVICE_DEPENDENCY_*.md` are already archived — update SSOT-INDEX to explicitly note they are superseded by `INTERNAL_DEPENDENCY_GRAPH.md` + `TOPOLOGY-DAG.md` + the two SVGs

### Missing docs to create (existing plan tasks)

- `**codex-orphan-repos-doc**` (P1): `04-architecture/api-services-cluster.md` — ERA (`execution-results-api`), MDA (`market-data-api`), `client-reporting-api`, `strategy-ui` with canonical names, status, FastAPI+OAuth pattern, proxied service, served UI
- `**codex-ui-service-separation-doc**` (P1): `06-coding-standards/ui-service-separation.md` — mirror `.cursor/rules/ui-service-separation.mdc` as a codex reference doc
- `**codex-service-pair-flows-doc**` (P0): `08-workflows/service-pair-flows.md` — YAML service-pairs registry derived from DAG edges; becomes SSOT for `e2e-service-pair-registry`

---

## Part 3: Plan Split into 3 Phases

### Ordering rationale

```
Phase 1 — Foundation & Prep
  No quickmerge runs yet. Purpose: set up the runway.
  Naming + SSOT docs + CI/CD rollout + deployment structure split.
  DONE WHEN: all 55 repos have quickmerge template + commit-msg hook,
             CI/CD pipeline live, naming consistent, SSOT docs clean.

Phase 2 — Library Tier Hardening
  Progressive QG. No service work.
  Global violation sweep → T0 → T1 → T2 → T3.
  Each tier: Step A (deploy structure) → B (tests first) → C (code)
             → D1 (--lint-only) → D2 (--unit-only) → D3 (--qg-only)
             → D4 (--quick) → D5 (full quickmerge)
  DONE WHEN: T0+T1+T2+T3 all green — full quickmerge exits 0.

Phase 3 — Service Hardening & Integration
  T4 services in DAG pipeline order → T5 API services → T6 UIs.
  Integration tests build in layers:
    Layer 0 (contract alignment) — done in Phase 2 T0
    Layer 1 (schema robustness)  — per service as each tier runs
    Layer 2 (infra verify)       — post-deploy, needs deployment-engine from Phase 1
    Layer 3a smoke + 3b full e2e — AFTER all tiers green
  Post-refactor validation: sandbox deploy → L2 → L3a → L3b → declare healthy.
  Full quickmerge with act simulation is the FINAL gate.
```

### Phase 1 file: `phase1_foundation_prep.plan.md`

Contains all of (from consolidated plan):

- Naming cleanup tasks (new work above)
- SSOT doc fixes: `codex-tier-arch-conflict-resolve`, `codex-orphan-repos-doc`, `codex-ui-service-separation-doc`, `codex-service-pair-flows-doc`, `codex-service-dependency-diagram-v3`, `dag-tier-corrections`, `topology-ssot-index-update`
- **Phase 0 STREAM A** (CI/CD — gates all multi-repo work, must finish first):
  - Steps A0 (DAG validation) → A1 (quickmerge template + version-bump to 55 repos) → A2 (commit-msg hooks) → A3 (CI/CD pipeline: dep-branch clone, Cloud Build feature trigger, version-bump GH Action)
- **Phase 0 STREAM B** (deployment structure, parallel with A):
  - `arch-exec-services-visualizer-extract`, `deployment-v3-four-way-split` + `arch-deployment-v3-ui-extract`, `ui-service-separation-audit-full`, `integration-system-integration-tests-repo`, `infra-merge-utdv3`, `hybrid-live-seam`
- **Phase 0 STREAM C** (QG baseline audit, parallel with A+B):
  - `aws-migration-cursor-rule`, `ci-manifest-status-fields`, add `quality-gates.sh` to 12 repos missing it, run QG baseline on all 30 repos, verify cloudbuild.yaml invokes QG inside Docker, `aws-compute-stubs-wire`, `aws-secret-naming-parity`, `aws-cloudbuild-parity`
- New cursor rules: `arch-ui-separation-rule`, `dag-enforcement.mdc`

### Phase 2 file: `phase2_library_tier_hardening.plan.md`

Contains:

- **Global violation sweep** (mechanical find-and-replace across all repos — runs once before tier work)
- **Tier 0** (8 repos parallel: AC, UIC_INT, UCI, UEI, UCLI, URDI, EAL, MEL)
  - Integration Layer 0 contract tests (AC↔UIC alignment) live here
  - All `ic-`*, `ac-`*, `vcr-public-venues`, `vcr-urdi-parse-raw-umi-stubs`, `lib-phase3-urdi-setup`, `mel-deps-remove`, `dag-mel-tier-mismatch` todos
- **Tier 1** (UTS single repo): `lib-phase1-uts-domain-cleanup`, `lib-phase2-uts-rename-step1`, `dag-uts-v22-feature-audit`, `uts-v5-cleanup`
- **Tier 2** (7 repos parallel: UMI, UTEI, UDEI, USEI, UML, UFC, UPI): `vcr-new-adapters-`*, `cohesion-umi-udc-dep-violation`, `p0-canonical-swap-fix`, `p0-umi-skipped-test`, `usei-v1-betfair-pinnacle`, `uml-protocol-refactor`, `cohesion-upi-pbm-dependency`
- **Tier 3** (UDC single repo): `lib-phase1-udc-tier2-compliance`, `lib-phase2-udc-rename-step1`, `lib-phase3-instruments-service-urdi-wire`, `udc-artifact-impl`

### Phase 3 file: `phase3_service_hardening_integration.plan.md`

Contains:

- **Tier 4** services in strict DAG pipeline order:
  - Batch A: `instruments-service` (IS) — gates all other services
  - Batch B: `market-tick-data-service`, `market-data-processing-service` (2 parallel)
  - Batch C: Features layer — `features-calendar-service`, `features-delta-one-service`, `features-volatility-service`, `features-onchain-service` (4 parallel)
  - Batch D: ML pipeline — `ml-training-service`, `ml-inference-service` (2 parallel)
  - Batch E: `strategy-service`, `execution-service` (2 parallel)
  - Batch F: Monitoring pipeline — `position-balance-monitor-service`, `pnl-attribution-service`, `risk-and-exposure-service`, `alerting-service` (4 parallel)
- **Tier 5** API services: `execution-results-api`, `market-data-api`, `client-reporting-api` (3 parallel)
- **Tier 6** UIs: 11 repos parallel
- **Integration Layer 2** (infra-verify — needs `deployment-engine` from Phase 1)
- **Integration Layer 3a + 3b** (system-integration-tests — needs Phase 1 repo + all tiers green)
- **Cross-cutting** (throughout Phase 3): auth/credentials, codex doc updates as tiers complete, final QG sweep (`p0-reportany-error-all-repos`, `vcr-quality-gates`, `ci-per-repo-status-run`)
- **Post-refactor validation** (strictly ordered, very last):
  1. Sandbox deploy via deployment-engine
  2. Layer 2 — `GET /infra/health` all checks pass
  3. Layer 3a — `pytest -m smoke` (must pass before 3b)
  4. Layer 3b — `pytest -m full_e2e`
  5. Declare healthy → merge staging → main → GitHub Action bumps to 1.0.0

### Updated `consolidated_remaining_work.plan.md`

Retains:

- Agent Bootstrap section (venv, SSOT refs — unchanged, agents still need this)
- Preflight checklist (blocking violations table — unchanged)
- Priority Quick-Reference table
- Auth Items Summary table

Replaces the Execution Order section with a phase index:

```
See phase files (execute in strict order):
  phase1_foundation_prep.plan.md       — naming, SSOT, CI/CD, deployment structure
  phase2_library_tier_hardening.plan.md — T0 → T1 → T2 → T3
  phase3_service_hardening_integration.plan.md — T4 → T5 → T6 → post-refactor validation
```

---

## Execution Sequence for This Plan

```
Step 1 — Naming cleanup (todos: naming-cleanup-deployment-v3, naming-cleanup-codex, naming-cleanup-plan)
  Run 3 parallel agents:
    Agent 1: deployment-v3/configs/ files (~50 hits)
    Agent 2: unified-trading-codex/ active docs
    Agent 3: consolidated_remaining_work.plan.md text fixes

Step 2 — SSOT doc updates (todos: ssot-index-update, codex-tier-arch-header, dag-tier-corrections-codex)
  Run 2 parallel agents:
    Agent 1: 00-SSOT-INDEX.md + dag-tier-corrections across codex
    Agent 2: 05-infrastructure/unified-libraries/TIER-ARCHITECTURE.md header

Step 3 — Create missing codex docs (todos: codex-api-services-cluster-doc, codex-ui-separation-doc, codex-service-pair-flows-doc)
  Run 3 parallel agents (all new files, no conflicts)

Step 4 — Write the 3 phase plan files (todos: split-plan-phase1, split-plan-phase2, split-plan-phase3)
  Run 3 parallel agents:
    Each agent writes one phase file, pulling relevant todos from consolidated plan

Step 5 — Update consolidated plan as index (todo: update-consolidated-as-index)
  1 agent rewrites the Execution Order section only
```
