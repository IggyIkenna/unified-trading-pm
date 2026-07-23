---
doc_type: codex-ssot
title: ML Model Catalogue
summary:
  ML Model Catalogue playbook-concept — the UAC<->UTL boundary was resolved 2026-05-13 (UAC owns ModelMetadata /
  TrainingRun / ModelFamily schemas; UTL owns the runtime ModelRegistry + model loading); the 10 /services/research/ml/*
  pages still need elevation to catalogue parity.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service, unified-api-contracts, unified-trading-library]
scope: [engineer, admin, sales]
tags: [catalogue, ml, uac, ui, strategy, registry]
related:
  [
    /codex/14-customer-journeys/playbook-concepts/catalogues.md,
    /codex/14-customer-journeys/playbook-concepts/catalogue-strategy.md,
    /codex/14-customer-journeys/playbook-concepts/visibility-slicing.md,
    ../roadmap/next-waves.md,
  ]
created: 2026-04-19
authoritative_for: [ML-model catalogue UI-surface parity gap]
referenced_by:
  [
    /codex/14-customer-journeys/page-triage/broken-links.md,
    /codex/14-customer-journeys/playbook-concepts/README.md,
    /codex/14-customer-journeys/playbook-concepts/catalogues.md,
    /codex/14-customer-journeys/playbooks/02b-research-dart.md,
    /codex/14-customer-journeys/playbooks/03c-demo-dart.md,
    /codex/14-customer-journeys/roadmap/plan-references.md,
  ]
owner:
last_reviewed: 2026-05-13
code_refs:
---

# ML Model Catalogue

One of the four catalogues. See [catalogues.md](catalogues.md) for the umbrella pattern.

## Status: ✅ SSOT resolved — UAC schemas + UTL registry boundary clarified 2026-05-13

## Service SSOT — UAC ↔ UTL boundary (ML-12 resolution, 2026-05-13)

**Boundary (verified 2026-05-13 per Sweep 3 of `codex_doc_currency_and_consolidation_post_cutover_2026_05_12.md`):**

| Concern                                                                                | Lives in                  | Files                                                                            |
| -------------------------------------------------------------------------------------- | ------------------------- | -------------------------------------------------------------------------------- |
| **UAC schemas** (typed `ModelMetadata`, `TrainingRun`, `ModelFamily`, ML domain enums) | `unified-api-contracts`   | `unified_api_contracts/internal/ml.py`, `internal/domain/ml/schemas.py`          |
| **UTL registry** (runtime `ModelRegistry`, training run abstractions, model loading)   | `unified-trading-library` | `unified_trading_library/ml/model_registry.py`, `ml/models.py`, `ml/__init__.py` |

UTL `ModelRegistry` consumes UAC ML schemas as its typed contract surface; ML domain types are NOT duplicated. Consuming
services (strategy-service for `ML_DIRECTIONAL` archetypes, features-\* services) import from UTL for runtime, UAC for
typing. This was the historical gap flagged in the prior § "Audit needed" — closed by Sweep 3.

- [unified-trading-library/ml/](https://) sub-package — ML registry + training run abstractions + model families
- Consuming services: strategy-service (uses ML models in ML_DIRECTIONAL archetypes), features-\* services

## UAC registry

ML schemas live at `unified-api-contracts/unified_api_contracts/internal/ml.py` + `internal/domain/ml/schemas.py`. No
UAC gap — closed 2026-05-13.

## UI route (today)

10 pages under `/services/research/ml/`:

- `ml` (overview), `registry`, `training`, `analysis`, `config`, `governance`, `grid-config`, `monitoring`
- Most are orphans (tab-only access; no inbound links from dashboard or overview)

## Gap vs canonical pattern

| Parity feature        | Strategy Catalogue |                                  ML Model Catalogue                                   |
| --------------------- | :----------------: | :-----------------------------------------------------------------------------------: |
| Overview page         |         ✅         | ⚠ `/services/research/ml` exists but as sub-section, not standalone catalogue landing |
| Coverage matrix       |         ✅         |   — (needs: model families × asset class × training-data range × validation status)   |
| By-combination filter |         ✅         |                                           —                                           |
| Per-entry detail      |         ✅         |            ⚠ `/services/research/ml/registry` has list but no detail page             |
| Admin lock-state      |         ✅         |                                           —                                           |
| Blocked               |         ✅         |                                           —                                           |

## What to build for parity

1. **Unify under `/services/ml-catalogue/` or elevate `/services/research/ml/` to catalogue status**
2. **Coverage matrix**: model_family × asset_group × training_period × maturity × lock_state
3. **Per-entry detail**: one page per model registry entry with training history, performance, governance state
4. **Lock state + maturity mirror**: same 4 lock states + 8 maturity stages as strategy catalogue
5. **Governance tab**: who-signed-off, audit trail, incident history

Tracked in [../roadmap/next-waves.md](../roadmap/next-waves.md).

## Relationship to other catalogues

ML Model Catalogue is CONSUMED by Strategy Catalogue — strategies of type `ML_DIRECTIONAL` reference a specific model
registry entry. Strategy catalogue UI should deep-link to ML model detail.

## Cross-playbook surface

- **pb2b (DART briefing)** — mentioned as one of four catalogues
- **pb3c (DART demo)** — demo user sees model catalogue filtered to their entitlements
- **pb3a/b (IM / Reg)** — NOT surfaced (IM clients care about P&L outcomes; models are implementation detail)

## Related

- Umbrella: [catalogues.md](catalogues.md)
- Strategy catalogue (consumer): [catalogue-strategy.md](catalogue-strategy.md)
- Visibility slicing: [visibility-slicing.md](visibility-slicing.md)
- UAC gap flagging: [../roadmap/next-waves.md](../roadmap/next-waves.md)
