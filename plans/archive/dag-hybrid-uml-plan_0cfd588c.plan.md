---
doc_type: plan
title: dag-hybrid-uml-plan
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service, instruments-service]
scope: [engineer, admin]
tags: []
related: []
created: "2026-02-28"
overview:
  Apply DAG-first refactor with UML protocol-based storage decoupling (Option 1) and hybrid live coupling policy, then
  synchronize manifest/codex/rules/plan before broad testing.
todos:
  - {
      id: dag-ssot-align,
      content: Reconcile manifest + topology/dependency docs and reorder consolidated plan to DAG-first.,
      status: pending,
    }
  - {
      id: uml-protocol-refactor,
      content: Refactor UML ModelRegistry to protocol-based artifact store; remove direct UDC imports.,
      status: pending,
    }
  - {
      id: udc-artifact-impl,
      content: Add UDC implementation of UML artifact store protocol and wire in ML services.,
      status: pending,
    }
  - {
      id: remove-service-deps,
      content: "Eliminate explicit service->service dependencies in pyproject/manifest (EXEC, MLIN, MTDH clusters).",
      status: pending,
    }
  - {
      id: hybrid-live-seam,
      content: Implement/document hybrid live in-memory adapter seam for MDPS without service coupling.,
      status: pending,
    }
  - {
      id: uts-v5-cleanup,
      content: Clean UTS optional extras to remove tier leakage and stale package naming.,
      status: pending,
    }
  - {
      id: governance-sync,
      content: Update codex and cursor rules to enforce final DAG and hybrid coupling policy.,
      status: pending,
    }
  - {
      id: target-dag-svg,
      content: Create post-fix annotated DAG SVG next to existing architecture visuals.,
      status: pending,
    }
  - {
      id: runtime-topology-ssot,
      content:
        "Add deployment runtime-topology SSOT manifest, wire deployment consumer, and sync codex/cursor rules/plan
        references.",
      status: pending,
    }
isProject: false
---

# DAG-First Refactor Plan (UML Option 1 + Hybrid Live Coupling)

## Locked decisions

- **UML:** Use **Option 1** — keep interface/types in `UML`, define storage protocol there, implement in `UDC`, inject
  from services.
- **Live coupling policy:** **Hybrid** — allow same-VM in-memory bridge in live mode, but **no service→service pyproject
  dependency** and no cross-repo service imports.

## Phase 0 — DAG gate (must complete before tier tests)

- Normalize `workspace-manifest.json` as SSOT (remove duplicate repo keys, remove stale violation/orphan statements that
  are already resolved).
- Reconcile architecture docs with manifest:
  - `unified-trading-/codex/04-architecture/TOPOLOGY-DAG.md`
  - `unified-trading-/codex/05-infrastructure/unified-libraries/LIBRARY-DEPENDENCY-MATRIX.md`
  - `unified-trading-/codex/05-infrastructure/unified-libraries/INTERNAL_DEPENDENCY_GRAPH.md`
- Update `.cursor/plans/consolidated_remaining_work.md` so DAG cleanup is explicitly before broad test execution.

## Phase 1 — Remove hard dependency violations

- Remove `UML -> UDC` direct coupling in `unified-ml-interface`:
  - Define `ModelArtifactStore` protocol in `UML`.
  - Refactor `ModelRegistry` to consume protocol only (no `CloudTarget` / `StandardizedDomainCloudService` imports).
- Add `UDC` implementation (e.g., `GcsModelArtifactStore`) that satisfies the protocol.
- Wire `ml-training-service` and `ml-inference-service` to inject the `UDC` implementation.
- Remove service→service deps from pyproject/manifest:
  - `execution-service -> instruments-service` (and related service deps)
  - `ml-inference-service -> ml-training-service`
  - `market-tick-data-handler -> instruments-service`

## Phase 2 — Hybrid live bridge formalization

- Introduce an explicit **live transport seam** (contract/adaptor) used by `MDPS` for live mode:
  - `mode=batch` uses storage-backed flow.
  - `mode=live` can use process-local/in-memory adapter when co-deployed.
- Ensure this seam is implemented via shared contracts/libraries, not service imports.
- Document deployment-level behavior as infra/config responsibility, with service mode selecting the adapter path.
- Add and maintain runtime topology SSOT in deployment config:
  - `unified-trading-deployment-v3/configs/runtime-topology.yaml` defines transport by mode/profile.
  - Deployment tooling consumes this manifest to decide dependency-check behavior (`gcs` vs `none`).
  - `in_memory` transport is only valid under `co_located_vm` profile.

## Phase 3 — Resolve V5 packaging drift (UTS optional extras)

- In `unified-trading-services/pyproject.toml`, clean `split-libraries` optional extras:
  - Remove Tier-2 library references from Tier-1 package extras.
  - Replace stale package names (e.g., `unified-order-interface` → canonical naming).
- Update package comments/docs to make migration state and allowed dependency direction explicit.

## Phase 4 — Governance updates (codex + cursor rules)

- Update codex docs and relevant cursor rules to codify:
  - UML protocol/implementation split pattern.
  - Hybrid live coupling constraints (allowed behavior + forbidden coupling forms).
  - Runtime topology SSOT ownership and consumption points.
  - DAG validation precedence over broad testing.
- Add/strengthen DAG guard checks in quality gates so forbidden edges fail early.

## Phase 5 — New visual artifacts

- Create a second architecture SVG (next to DAG docs) showing **post-fix target DAG** with:
  - clear edge annotations (what each dependency is for)
  - short justification notes for key boundaries
  - hybrid live path called out as deployment-mode adapter, not service coupling

## Acceptance criteria

- No T2→T3 dependency in `UML`.
- No service→service dependency declarations in pyproject/manifest.
- Hybrid live path works via adapter/contract seam without cross-service imports.
- Runtime topology decisions are declared in `runtime-topology.yaml` and consumed by deployment code.
- Codex/rules/plan/manifest all consistent with the final DAG.
- New annotated target SVG available for agent guidance.
