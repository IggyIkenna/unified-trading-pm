---
doc_type: issue
title:
  "Build the 3-layer feature/market-data subscription model (archetype-allows / instance-selects /
  deployment-aggregates) — operator architecture direction, 2026-08-21"
summary: >-
  Found MeanReversionConfig.feature_subscriptions is a declared-but-dead schema field (zero consumers anywhere)
  during a strategy-config audit — every archetype today hardcodes its feature/MDPS provider calls directly,
  with no declarative subscription mechanism. Operator's direction: build a real 3-layer model instead of
  deleting the field outright - archetype declares its ALLOWED general subscriptions, strategy INSTANCE config
  narrows to the specific shards it wants (avoiding over-querying), and the DEPLOYMENT level aggregates/dedupes
  calls across co-located strategy instances needing the same feed (avoiding double-streaming). Not built - this
  is architecture direction to scope into buildable todos, not a shipped design.
status: open
nature: design
asset_group: [cefi, defi, tradfi]
stage: [strategy, features]
repos: [strategy-service, features-service, deployment-service]
scope: [engineer, admin]
tags: [features, subscriptions, mdps, architecture, operator-direction, deployment]
related:
  [
    /codex/02-data/feature-formula-versioning.md,
    /plans/active/strategy_service_expansion_overlays_config_and_wizard_2026_08_12.md,
  ]
created: "2026-08-21"
author: unknown
last_updated: "2026-08-21"
source: operator-request-2026-08-21
parent_epic: security_and_cross_cutting_master
resolved_by:
locked_by:
context_scope:
  [
    strategy-service/strategy_service/strategy_yaml_config_types.py,
    unified-api-contracts/unified_api_contracts/internal/architecture_v2/archetype_capability.py,
  ]
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: design
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.9
assigned_role: strategy_engineering
drift_direction: advance-code
---

# 3-layer feature/market-data subscription model

## Context — how this surfaced

A strategy-config audit (2026-08-21) found `MeanReversionConfig.feature_subscriptions: list[str]`
(`strategy_service/strategy_yaml_config_types.py:255`) is declared but has ZERO consumers anywhere in
strategy-service — a config author could set it expecting it to do something, and nothing would happen. In
practice, every archetype's engine code calls hardcoded per-purpose feature/MDPS provider classes directly
(`canonical_perp_funding_provider.py`, `canonical_lending_supply_apy_provider.py`,
`canonical_aave_borrow_index_provider.py`, `canonical_lst_yields_index_provider.py`, `gcs_feature_provider.py`,
etc.), with keys baked into the provider/caller — no declarative subscription list resolves anything. Asked the
operator whether to delete the dead field or build the mechanism for real.

## OPERATOR DIRECTION 2026-08-21 (verbatim)

> "archetype should do the allowed general subscriptions. strategy instance config should define which shards
> it wants to avoid too much data being queried. the deployment level then by definition aggregates the calls
> so we don't double stream where multiple strategies in a strategy server need the same feed."

Translation / what this means architecturally — THREE layers, do not collapse them (same pattern this
workspace already applies elsewhere, e.g. the DeFi-universe-curtailment 3-layer design in
`defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md` — check that doc for a possibly-reusable
pattern/precedent before designing from scratch):

1. **Archetype layer — declares ALLOWED subscriptions.** Each archetype type (not each instance) declares the
   universe of feature/MDPS shards it's capable of consuming — a capability declaration, similar in spirit to
   the venue-capability registry work. This is the ARCHETYPE's contract: "I can consume these shard types."
2. **Strategy-instance layer — SELECTS a subset.** A specific strategy instance's config narrows the
   archetype's allowed set down to the specific shards IT actually wants (per client/axis/version) — this is
   what prevents over-querying: an instance only pulls the data it needs, not everything the archetype type
   could theoretically use.
3. **Deployment layer — AGGREGATES across instances.** When multiple strategy instances run co-located in one
   deployment (a "strategy server") and need the same feed, the deployment layer dedupes the underlying calls
   so the same feed isn't streamed/queried multiple times redundantly — a real efficiency requirement, not just
   a config nicety.

## What already exists (verify before building)

- The dead `feature_subscriptions` field (delete once the real mechanism supersedes it — do not keep it as a
  parallel dead path).
- The per-purpose provider classes (`canonical_*_provider.py`, `gcs_feature_provider.py`) — these are the
  actual DATA-FETCHING mechanism today; the new subscription model should likely resolve TO these providers
  (i.e., "shard X" maps to "call provider Y with these params"), not replace them with a new fetch mechanism.
- Whether any deployment-level aggregation/dedup mechanism already exists elsewhere in the codebase for a
  DIFFERENT purpose (e.g. MTDS/MDPS's own subscription fan-out, if any) that this could reuse rather than
  build fresh — not checked this session.

## Todos

- [ ] [BACKEND] P1. **Design the archetype-layer allowed-subscription declaration shape** — likely a new field
      or registry entry per archetype TYPE (not instance), enumerating shard types it can consume. Check
      whether `ARCHETYPE_CAPABILITY_REGISTRY` (found during the venue-capability audit, same day —
      `unified_api_contracts/internal/architecture_v2/archetype_capability.py`) is a reusable pattern/home for
      this, or a genuinely separate concern (venue capability vs. data capability may be orthogonal enough to
      need separate tables — don't force them together if they don't naturally fit).
- [ ] [BACKEND] P1. **Design the instance-layer selection mechanism** — likely resurrects/redesigns
      `feature_subscriptions`'s intent but validated against the archetype's allowed set (fail closed on an
      instance requesting a shard its archetype type doesn't declare).
- [ ] [BACKEND] P1. **Design the deployment-layer aggregation/dedup mechanism** — this is the piece most likely
      to require new infrastructure (a per-deployment shared subscription resolver/cache) rather than a config
      schema change. Scope where this lives (strategy-service's own deployment bootstrap? A shared
      `unified-trading-library` component?) once the first two layers are designed, since they inform what the
      deployment layer needs to aggregate.
- [ ] [BACKEND] P2. **Delete `feature_subscriptions`'s current dead form and wire archetypes' real provider
      calls through the new mechanism** — start with one archetype as the proof case (mirroring this
      workspace's usual "exemplar first" pattern) before rolling out to all.
- [ ] [DOC] P3. Codex SSOT for the 3-layer model once designed, so it doesn't get re-litigated per-archetype.

## Progress Log

- **2026-08-21** — Filed from an interactive session after the operator gave this architecture direction in
  response to a dead-field-cleanup question. Not investigated further this session (session/time constrained)
  — todo 1 is the real next step, not yet started.
