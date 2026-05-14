---
title: "cross_asset not in instruments-service scope — needs design call"
created: 2026-05-14
author: harsh-slot-7
source:
  - plans/active/data_status_ui_phase_2f.md
locked_by: live-defi-rollout
locked_since: 2026-05-14
---

## What I found

During the 6C UI-drilldown smoke (2026-05-14), `cross_asset` was absent from the Asset Groups filter
buttons in the Data Status tab for `instruments-service`. This is by design.

`instruments-service` processes: **CEFI, TRADFI, DEFI, SPORTS, PREDICTION** — confirmed via
`deployment-ui/src/components/ServiceList.tsx:145` and the sharding config
`deployment-api/pm-configs/sharding.instruments-service.yaml:24`.

`instruments-service` does NOT produce cross_asset instrument definitions. Cross-asset instruments
(cross-exchange pairs, multi-leg synthetic instruments) would require a separate service or an
instruments-service extension. Adding a CROSS_ASSET filter button for instruments-service would be
misleading — it would always return 0 data even if data exists (wrong service→asset_group mapping).

## Why it matters

The Data Status breakdown shows 5 asset groups (from API manifest data when files exist). The filter
buttons for instruments-service show the same 5 (CEFI, TRADFI, DEFI, SPORTS, PREDICTION) which is
correct. `cross_asset` appearing in the turbo breakdown for other services (features-service) is fine
because those services DO produce cross-asset data.

Severity: **P2** — design gap / scope question. Not a bug in the current implementation.

## Recommended decision

**Design call needed**: Does cross_asset instrument definition generation belong in instruments-service
(as an additional shard dimension) or in a new `cross-instruments-service`?

Options:
1. **Extend instruments-service**: Add `CROSS_ASSET` to the sharding config + implement cross-asset
   instrument generation (pairs, synthetic indices). Cleanest — one service for all instruments.
2. **New cross-instruments-service**: Separate service for cross-asset instrument definitions.
   Higher overhead but cleaner separation of concerns.
3. **Features-service owns cross-asset derivation**: Cross-asset features already exist; instrument
   definitions could live there. Blurs the instruments/features boundary.

Suggested owner: **Ikenna** (architecture call) or operator.

execution:
  owner: operator
  cadence: one-shot (design decision)
  verifier: cross_asset appears in sharding.instruments-service.yaml + produces manifest rows
  last_executed: NEVER
