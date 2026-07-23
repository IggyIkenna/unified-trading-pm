---
doc_type: codex-ssot
title: Strategy Catalogue
summary:
  Strategy Catalogue — the canonical 4-catalogue-pattern implementation (shipped Phase 10, 2026-04-19) — 18 archetypes x
  5 categories, 4 lock states (PUBLIC/IM_RESERVED/CLIENT_EXCLUSIVE/RETIRED), an 8-stage maturity ladder, and role x lock
  x maturity visibility slicing via UAC slots_visible_to().
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin, sales]
tags: [catalogue, strategy, ui, uac, maturity, visibility]
related:
  [
    /codex/14-customer-journeys/playbook-concepts/catalogues.md,
    /codex/14-customer-journeys/playbook-concepts/visibility-slicing.md,
    ../../09-strategy/architecture-v2/README.md,
    ../../09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md,
  ]
created: 2026-04-19
authoritative_for: [strategy catalogue as canonical 4-catalogue-pattern reference]
referenced_by:
  [
    /codex/14-customer-journeys/playbook-concepts/README.md,
    /codex/14-customer-journeys/playbook-concepts/catalogue-ml-model.md,
    /codex/14-customer-journeys/playbook-concepts/catalogues.md,
    /codex/14-customer-journeys/playbook-concepts/visibility-slicing.md,
    /codex/14-customer-journeys/playbooks/02b-research-dart.md,
    /codex/14-customer-journeys/playbooks/03c-demo-dart.md,
    /codex/14-customer-journeys/roadmap/plan-references.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Strategy Catalogue

The canonical implementation of the 4-catalogue pattern (see [catalogues.md](catalogues.md)). Shipped as Phase 10 of the
strategy-architecture-v2 plan on 2026-04-19.

## Status: ✅ CANONICAL

## Service SSOT

- [strategy-service/engine/strategies/v2/archetype_build_registry.py](https://) — `ArchetypeBuildRegistry` (thread-safe
  append-only per-archetype history)
- [strategy-service/availability/](https://) — `StrategyAvailabilityRegistry` (lock_state + maturity store)
- Backed by GCS JSONL via `make_ledger_sink()` factory

## UAC registry

- `unified_api_contracts/strategy_availability/` — typed declarations exposing catalogue entries externally
- Helpers: `availability_for(slot_label)`, `slots_visible_to(role)`, `validate_allocation_authorised(role)` (see Phase
  10.5)

## UI route

- `/services/strategy-catalogue/` — landing
- `/services/strategy-catalogue/coverage` — master matrix (archetype × category × instrument type)
- `/services/strategy-catalogue/coverage/by-combination` — leg-picker for pairs/arbs
- `/services/strategy-catalogue/coverage/blocked` — BL-\* codes + remediation
- `/services/strategy-catalogue/strategies/[archetype]/[slot]` — per-strategy detail
- `/services/strategy-catalogue/admin/lock-state` — admin toggle (lock + maturity edit)

## Dimensions

Each entry has:

- `archetype` — one of 18 (MM_CONTINUOUS, ML_DIRECTIONAL, STAT_ARB_PAIRS_FIXED, etc.) — see
  [../../09-strategy/architecture-v2/README.md](../../09-strategy/architecture-v2/README.md)
- `category` — one of 4 (DEFI, CEFI, TRADFI, SPORTS, PREDICTION)
- `instrument_type` — spot / perp / option / dated-future / sports-fixture / prediction-market / etc.
- `slot_label` — deterministic identifier combining the above
- `lock_state` — PUBLIC / IM_RESERVED / CLIENT_EXCLUSIVE / RETIRED
- `maturity` — CODE_NOT_WRITTEN → CODE_WRITTEN → CODE_AUDITED → BACKTESTED → PAPER_TRADING → PAPER_TRADING_VALIDATED →
  LIVE_TINY → LIVE_ALLOCATED
- `exclusive_client_id` (if CLIENT_EXCLUSIVE)
- `reserving_business_unit_id` (if IM_RESERVED)

## Lock state transitions

Admin triggers via `/services/strategy-catalogue/admin/lock-state`. Transitions fire `STRATEGY_AVAILABILITY_CHANGED`
events.

Allowed transitions:

- PUBLIC → IM_RESERVED (pull strategy back from DART/SaaS offering to IM-only)
- IM_RESERVED → PUBLIC (offer back to SaaS)
- PUBLIC → CLIENT_EXCLUSIVE (assign to a specific client)
- CLIENT_EXCLUSIVE → PUBLIC (release back to shared pool)
- Any → RETIRED (archive)
- RETIRED → Any (resurrect — rare)

## Maturity ladder

Auto-advancement watchdog:

- CODE_NOT_WRITTEN → CODE_WRITTEN: manual
- CODE_WRITTEN → CODE_AUDITED: manual after review
- CODE_AUDITED → BACKTESTED: auto on first backtest run
- BACKTESTED → PAPER_TRADING: manual
- PAPER_TRADING → PAPER_TRADING_VALIDATED: 14-day paper gate via `ShadowDeploymentPolicy.evaluate_shadow_deployment`
  PROMOTE
- PAPER_TRADING_VALIDATED → LIVE_TINY: manual (go-live approval)
- LIVE_TINY → LIVE_ALLOCATED: auto on first non-zero `AllocationDirective`

Manual interventions (ops only):

- Incident-response demotion (e.g. LIVE_ALLOCATED → PAPER_TRADING due to drawdown)

## Visibility slicing (role × lock_state × maturity)

External visibility threshold: `maturity ≥ BACKTESTED` AND `lock_state ∈ visible_states_for(role)`.

| Role                               | Visible lock states                     | Visible maturity floor       |
| ---------------------------------- | --------------------------------------- | ---------------------------- |
| admin                              | All                                     | All (incl. CODE_NOT_WRITTEN) |
| im_desk                            | PUBLIC + IM_RESERVED + CLIENT_EXCLUSIVE | CODE_WRITTEN                 |
| im_client                          | PUBLIC + own CLIENT_EXCLUSIVE           | BACKTESTED                   |
| trading_platform_subscriber (DART) | PUBLIC + own CLIENT_EXCLUSIVE           | BACKTESTED                   |
| saas                               | PUBLIC + own CLIENT_EXCLUSIVE           | BACKTESTED                   |

Implemented via UAC `slots_visible_to(role)` helper.

## Cross-playbook surface

The strategy catalogue appears in ALL three playbook families:

- **pb1 (marketing)** — teased on homepage (card "Build & Run" → /platform → strategy-catalogue coverage)
- **pb2b (DART briefing)** — deep-linked for browsing the archetype taxonomy
- **pb3b (IM demo)** — IM prospects see IM_RESERVED strategies they might allocate to
- **pb3c (DART demo)** — DART prospects see PUBLIC strategies they can build on
- Admin — sees everything including CODE_NOT_WRITTEN placeholders

Same data, different views via visibility slicing.

## Related

- Umbrella pattern: [catalogues.md](catalogues.md)
- Visibility slicing: [visibility-slicing.md](visibility-slicing.md)
- Strategy architecture v2: [../../09-strategy/architecture-v2/README.md](../../09-strategy/architecture-v2/README.md)
- Phase 10 memory entry: MEMORY.md "Phase 10 UI complete"
- Phase 10.5 memory entry: MEMORY.md "Phase 10.5 backend shipped"
- Availability & locking SSOT:
  [../../09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md](../../09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md)
