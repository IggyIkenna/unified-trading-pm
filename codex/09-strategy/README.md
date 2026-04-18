# 09 — Strategy Documentation

> **SSOT:** [`architecture-v2/`](architecture-v2/README.md) is the canonical organisation for every trading strategy in
> the Unified Trading System. Legacy category-based docs (cefi / defi / sports / tradfi / templates + 7 absorbed
> cross-cutting docs) have moved to [`_archived_pre_v2/`](_archived_pre_v2/README.md) with pointers.

## Where to go first

- **Architecture v2 README**: [`architecture-v2/README.md`](architecture-v2/README.md) — full taxonomy (8 families × 18
  archetypes × 7 axes × 10 cross-cutting concerns) + Capital Flow Lifecycle.
- **Migration audit**: [`architecture-v2/MIGRATION.md`](architecture-v2/MIGRATION.md) — every legacy doc / code module /
  config mapped to its v2 placement. Nothing is silently dropped.
- **Archive index**: [`_archived_pre_v2/README.md`](_archived_pre_v2/README.md) — if you're looking for a legacy doc.

## What's still in this directory (not archived)

These docs remain live because they cover non-strategy concerns or operational playbooks that v2 explicitly links out
to, rather than absorbing:

### `cross-cutting/` — still authoritative

- [`cross-cutting/client-onboarding.md`](cross-cutting/client-onboarding.md) — client-specific onboarding workflow.
  Referenced from `architecture-v2/cross-cutting/capital-client-isolation.md`.
- [`cross-cutting/client-strategy-config.md`](cross-cutting/client-strategy-config.md) — per-client strategy config
  surface. Extended by `architecture-v2/cross-cutting/portfolio-allocator.md`.
- [`cross-cutting/instrument-filtering.md`](cross-cutting/instrument-filtering.md) — major-asset whitelist + pool TVL
  rules. Referenced by every DeFi-touching archetype.
- [`cross-cutting/onboarding-checklist.md`](cross-cutting/onboarding-checklist.md) — operational checklist.
- [`cross-cutting/operational-modes-matrix.md`](cross-cutting/operational-modes-matrix.md) — batch/live mode matrix.
  Referenced from `architecture-v2/cross-cutting/benchmark-fills.md`.
- [`cross-cutting/pnl-attribution.md`](cross-cutting/pnl-attribution.md) — strategy-alpha vs execution-alpha split.
  Enhanced with benchmark-fills contract.
- [`cross-cutting/prediction-markets.md`](cross-cutting/prediction-markets.md) — prediction-market-specific details.
- [`cross-cutting/rate-impact-model.md`](cross-cutting/rate-impact-model.md) — rate impact curves. Referenced by Carry &
  Yield archetypes.
- [`cross-cutting/reward-lifecycle.md`](cross-cutting/reward-lifecycle.md) — DeFi reward lifecycle.

### Top-level

- [`TIER_ZERO_UI_DEMO_AND_PARITY.md`](TIER_ZERO_UI_DEMO_AND_PARITY.md) — UI Tier-0 playbook (fixtures, cross-strategy
  UX, promotion path). UI-facing; not superseded by v2.

## What moved

Every category-organised strategy doc (`cefi/`, `defi/`, `sports/`, `tradfi/`, `templates/`) and the 7 cross-cutting
docs absorbed into v2's axes / cross-cutting primitives now live under
[`_archived_pre_v2/`](_archived_pre_v2/README.md). Git history is preserved; the archive README lists the v2 target for
each archived doc.

Three top-level docs that were superseded are in the archive too:

- `strategy-registry.md` → UAC `StrategyInstanceDefinition` + `StrategyInstanceIdentity` types are the registry now.
- `STRATEGY_CATALOG_AND_WORKFLOW_ALIGNMENT.md` → superseded by
  [`architecture-v2/MIGRATION.md`](architecture-v2/MIGRATION.md).
- `execution-modes.md` → absorbed into [`../04-architecture/backtest-groups.md`](../04-architecture/backtest-groups.md)
  - [`architecture-v2/cross-cutting/benchmark-fills.md`](architecture-v2/cross-cutting/benchmark-fills.md).

## Legacy implementation code

Legacy strategy code in `strategy-service/strategy_service/engine/strategies/{cefi,defi,sports,tradfi,...}/` is still
load-bearing via the batch-dispatch factory `cli/handlers/batch_utils.create_strategy_instance()`. **Do not delete it
yet** — deletion is gated on the factory cutover to v2 archetype engines + shadow-deployment promotion per
`architecture-v2/MIGRATION.md` § 15 ("Legacy Code Deletion Schedule"). Tracked separately in
[`architecture-v2/MIGRATION.md`](architecture-v2/MIGRATION.md).
