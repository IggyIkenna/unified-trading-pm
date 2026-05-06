---
scope: [engineer, admin, sales]
---

<!-- POST_PLAN_BANNER_2026_05_06_FINAL -->

> **Post-2026-05-06** — read [`../POST_PLAN_REALITY_2026_05_06.md`](../POST_PLAN_REALITY_2026_05_06.md) before code/doc
> changes informed by this doc. Active plans: writegate-honest-coverage, predictions-canonical_question_group,
> data-status-multi-axis-shard. If this doc disagrees with active plans, the plans win. Flag conflicts to user.

# ML Model Catalogue

One of the four catalogues. See [catalogues.md](catalogues.md) for the umbrella pattern.

## Status: ⚠ SSOT exists in library; UAC + UI surface need audit + unification

## Service SSOT

- [unified-trading-library/ml/](https://) sub-package — ML registry + training run abstractions + model families
- Consuming services: strategy-service (uses ML models in ML_DIRECTIONAL archetypes), features-\* services

## UAC registry

**Audit needed** — verify whether model families / training runs are exposed as UAC types or remain service-local. If
missing, flag as a UAC gap.

## UI route (today)

10 pages under `/services/research/ml/`:

- `ml` (overview), `registry`, `training`, `analysis`, `config`, `governance`, `grid-config`, `monitoring`
- Most are orphans (tab-only access; no inbound links from dashboard or overview)

## Gap vs canonical pattern

| Parity feature        | Strategy Catalogue |                                   ML Model Catalogue                                   |
| --------------------- | :----------------: | :------------------------------------------------------------------------------------: |
| Overview page         |         ✅         | ⚠ `/services/research/ml` exists but as sub-section, not standalone catalogue landing |
| Coverage matrix       |         ✅         |   — (needs: model families × asset class × training-data range × validation status)    |
| By-combination filter |         ✅         |                                           —                                            |
| Per-entry detail      |         ✅         |            ⚠ `/services/research/ml/registry` has list but no detail page             |
| Admin lock-state      |         ✅         |                                           —                                            |
| Blocked               |         ✅         |                                           —                                            |

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
