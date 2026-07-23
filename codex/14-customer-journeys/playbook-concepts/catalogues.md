---
doc_type: codex-ssot
title: The four catalogues — umbrella doc
summary:
  Umbrella doc for Odum's four catalogues (Data, Strategy, ML Model, Execution Algo) — each an SSOT across service code,
  UAC registry, and /services/<catalogue>/* UI, sharing lock-state, maturity ladder, and visibility slicing, and forming
  a Data -> ML -> Strategy <- Execution DAG.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    execution-service,
    instruments-service,
    market-tick-data-service,
    strategy-service,
    unified-api-contracts,
    unified-trading-library,
  ]
scope: [engineer, admin, sales]
tags: [catalogue, ssot, uac, ui, strategy, visibility]
related:
  [
    /codex/14-customer-journeys/playbook-concepts/catalogue-data.md,
    /codex/14-customer-journeys/playbook-concepts/catalogue-strategy.md,
    /codex/14-customer-journeys/playbook-concepts/catalogue-ml-model.md,
    /codex/14-customer-journeys/playbook-concepts/catalogue-execution-algo.md,
    /codex/14-customer-journeys/playbook-concepts/visibility-slicing.md,
  ]
created: 2026-04-19
authoritative_for: [four-catalogue umbrella pattern (service/UAC/UI three-layer model)]
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/glossary.md,
    /codex/14-customer-journeys/information-architecture.md,
    /codex/14-customer-journeys/playbook-concepts/README.md,
    /codex/14-customer-journeys/playbook-concepts/catalogue-data.md,
    /codex/14-customer-journeys/playbook-concepts/catalogue-execution-algo.md,
    /codex/14-customer-journeys/playbook-concepts/catalogue-ml-model.md,
    /codex/14-customer-journeys/playbook-concepts/catalogue-strategy.md,
  ]
owner:
last_reviewed:
code_refs:
---

# The four catalogues — umbrella doc

Odum has FOUR catalogues, each an SSOT in service code, UAC, and UI. The same structural pattern applies to each — lock
states, maturity ladder, visibility slicing, promotion flow. Catalogues show up in ALL three playbook families (pb1
teaser, pb2 briefing, pb3 demo) with different depths of reveal.

> User quote: "There's data catalogue and strategy catalogue and ml model catalogue and execution algo catalogues. We
> might as well have all of these because we have the understanding of them. I'm pretty sure in Unified API contracts
> and certainly in the Strategy service, Machine Learning service, and Execution service by now. There should be a
> single source of truth system anyway in the code base, and then in UAC, and then really the UI."

## The pattern

Each catalogue has three layers of truth:

1. **Service-code SSOT** — a Python registry/class living in the relevant service (market-tick-data-service,
   strategy-service, ML package in UTL, execution-service)
2. **UAC registry** — typed declarations in `unified-api-contracts/` exposing the catalogue to other services + to the
   UI
3. **UI surface** — a route under `/services/<catalogue>/` with overview / coverage / by-combination / per-entry detail
   / admin pages

And three cross-cutting mechanisms:

- **Lock state** — one of {PUBLIC, IM_RESERVED, CLIENT_EXCLUSIVE, RETIRED} (per the Strategy Catalogue pattern; other
  catalogues may adapt)
- **Maturity ladder** — {CODE_NOT_WRITTEN → CODE_WRITTEN → CODE_AUDITED → BACKTESTED → PAPER_TRADING →
  PAPER_TRADING_VALIDATED → LIVE_TINY → LIVE_ALLOCATED}
- **Visibility slicing** — admin sees all; demo/prod sliced by role × entitlements × lock_state × maturity. See
  [visibility-slicing.md](visibility-slicing.md).

## The four instances

| Catalogue      | Service SSOT                                                                                                   | UAC registry                                                                   | UI route                                                   | Maturity today                                     |
| -------------- | -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ | ---------------------------------------------------------- | -------------------------------------------------- |
| Data           | [market-tick-data-service](https://) availability manifest + [instruments-service](https://) registry          | `unified_api_contracts/registry/capability_declarations/`                      | `/services/data/*` (fragmented — needs unification)        | Partial — data exists, not surfaced as "catalogue" |
| Strategy       | [strategy-service/engine/strategies/v2/archetype_build_registry.py](https://) + `StrategyAvailabilityRegistry` | `unified_api_contracts/strategy_availability/` (Phase 10.5 shipped 2026-04-19) | `/services/strategy-catalogue/*` (shipped Phase 10)        | ✅ canonical                                       |
| ML Model       | [unified-trading-library/ml/](https://) sub-package — model registry (verify existence/completeness)           | UAC declarations (verify)                                                      | `/services/research/ml/*` (fragmented — needs unification) | Needs SSOT audit                                   |
| Execution Algo | [execution-service/algo_library/](https://) + matching_engine registry                                         | UAC execution capabilities (verify)                                            | `/services/execution/*` (fragmented — needs unification)   | Needs SSOT audit                                   |

## Per-catalogue docs

- [catalogue-data.md](catalogue-data.md)
- [catalogue-strategy.md](catalogue-strategy.md) — the canonical implementation
- [catalogue-ml-model.md](catalogue-ml-model.md)
- [catalogue-execution-algo.md](catalogue-execution-algo.md)

## Common features every catalogue UI must have

Parity goal: every catalogue is inter-navigable and feels the same to a user moving between them.

1. **Overview page** `/services/<catalogue>/` — landing with counts, coverage %, quick navigation
2. **Coverage matrix** `/services/<catalogue>/coverage` — all entries × classification dimensions (different per
   catalogue)
3. **By-combination / filter** `/services/<catalogue>/by-combination` (or `/filter`) — search + filter
4. **Per-entry detail** `/services/<catalogue>/<identifier>` — deep-dive on one entry
5. **Admin** `/services/<catalogue>/admin/lock-state` — admin-only lock + maturity editor
6. **Blocked** `/services/<catalogue>/coverage/blocked` — entries blocked with remediation notes (where relevant)

Current state (2026-04-19):

- Strategy Catalogue has all 6 ✅
- Data, ML-Model, Execution-Algo — partial; needs refactor per per-catalogue docs

## Cross-catalogue movement

Catalogue entries can **move between catalogues** in some cases. For example:

- A Strategy entry uses ML Model entries and Execution Algo entries — strategy's dependencies.
- A Data entry (dataset) feeds into ML Model training runs.

This forms a DAG:

```
Data Catalogue ──▶ ML Model Catalogue ──▶ Strategy Catalogue
                                      ╲
                                       ╲
                                        ▶ Execution Algo Catalogue ──▶ Strategy Catalogue
```

The Strategy Catalogue is the downstream integrator — its entries reference entries in the other three catalogues.

## Proprietary vs client-offered transitions

Per the user's direction, catalogue entries (especially in the Strategy Catalogue) can transition between:

- **Proprietary only** — Odum trades this for own book only (`lock_state: IM_RESERVED`)
- **IM-offered** — Odum runs this for allocator clients (`lock_state: PUBLIC` visible on IM playbook)
- **DART-offered** — made available to DART clients to use themselves (`lock_state: PUBLIC` visible on DART playbook)
- **Client-exclusive** — reserved for a specific client (`lock_state: CLIENT_EXCLUSIVE`)
- **Retired** — no longer in use (`lock_state: RETIRED`)

Same lock_state field, different visibility impact. See [catalogue-strategy.md](catalogue-strategy.md) for the detailed
transition model and [visibility-slicing.md](visibility-slicing.md) for the slicing mechanics.

## Related

- Strategy catalogue deep dive: [catalogue-strategy.md](catalogue-strategy.md)
- Visibility slicing: [visibility-slicing.md](visibility-slicing.md)
- Strategy availability Phase 10.5 memory entry: see MEMORY.md "Phase 10.5 backend shipped"
