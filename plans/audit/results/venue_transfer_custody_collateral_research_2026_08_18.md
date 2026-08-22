---
doc_type: audit-result
title: Per-venue transfer rails, custody eligibility, collateral and cross-margin — research findings
summary: >-
  Research deliverable for client_artefact_remediation_2026_08_18.md § E's [RESEARCH] P1 todo. Corrects that
  todo's own premise ("no UAC registry field answers these") for the collateral/cross-margin half — a real,
  actively-consumed schema (VenueCapabilityV2.collateral_rules / margin_spec) exists but is populated for zero
  real venues. Custody eligibility and transfer-rail per-venue declarations remain genuinely absent. Written for
  the elysium/nickai children to pull from directly for their `assumption`/`needs-check` artefact insertions.
status: partial
nature: record
audited_scope: >-
  Whether any UAC registry field answers per-venue transfer-rail eligibility, custody eligibility, collateral
  usability or cross-margin logic — re-checking the parent plan's own "no UAC registry field answers these" claim
  against the live unified-api-contracts, execution-service and strategy-service source, not just its originally
  cited grep pattern.
date: 2026-08-18
auditor: >-
  Single interactive session (sonnet, high effort) — direct source reads and greps against unified-api-contracts
  (architecture_v2/{enums,schemas,custody_surfaces}.py), execution-service (transfer_coordinator.py), and
  strategy-service (risk/v2/{margin_sim,preflight,orchestrator}.py), plus a workspace-wide grep for every
  consumer of the schemas found.
severity: P1
resulting_plan: /plans/archive/2026_08/client_artefact_remediation_2026_08_18.md
lib_version:
doc_versions_checked:
asset_group: [cross-cutting]
stage: [strategy, execution, meta]
repos: [unified-trading-pm, unified-api-contracts, execution-service, strategy-service]
scope: [engineer, admin]
tags: [client-disclosure, venue-registry, custody, collateral, cross-margin, transfer-rails, artifact-remediation]
related:
  [
    /plans/active/client_artefact_remediation_nickai_2026_08_18.md,
    /plans/epics/system_readiness_master.md,
  ]
created: 2026-08-18
last_updated: "2026-08-18"
parent_epic: system_readiness_master
---

# Per-venue transfer rails, custody eligibility, collateral and cross-margin — research findings

Research deliverable for
[`client_artefact_remediation_2026_08_18.md`](/plans/archive/2026_08/client_artefact_remediation_2026_08_18.md) § E's
`[RESEARCH] P1` todo: *"Research real per-venue transfer rails / custody eligibility / collateral / cross-margin,
then write the best current answer into the artefact marked `assumption` or `needs-check`."* This doc does not
touch either artefact HTML directly (out of scope for this todo's owning session — the elysium and nickai children
own that file work); it hands them the researched content to insert, each marked per
[rule 13's evidence-tier spec](/codex/14-customer-journeys/_ssot-rules/13-artefact-claim-marks.md).

## Correction to the todo's own premise

The todo as written claims *"no UAC registry field answers these — `VenueCapabilityRecord` is market-data only
(`route` + `data_types`); `VenueCapability` covers actions (`spot_trade`…`stake`); a registry-wide grep for
`cross_margin|collateral_eligib|transfer_rail|withdraw_enabled|margin_asset` returns empty."* Re-verified
2026-08-18: **true for the two classes it names, false as a whole-registry claim.** A grep for `cross_margin`
(no `_eligib` suffix) returns real hits:

- `unified-api-contracts/unified_api_contracts/internal/architecture_v2/schemas.py` declares
  `CollateralRulesV2` (`eligible_assets: list[LtvAndHaircut]`, `cross_margin_supported: bool`,
  `portfolio_margin_supported: bool`) and `MarginSpec` (`mode`, `initial_margin_pct`, `maintenance_margin_pct`,
  `netting_rules`, `portfolio_margin_greek_model`, `min_cross_margin_pct_hedged`) — both fields on
  `VenueCapabilityV2` (`collateral_rules`, `margin_spec`), a **different, richer class** from the
  `VenueCapabilityRecord` the todo checked (that one, in `registry/market_data_categories.py`, really is
  market-data-only — the todo's claim about it stands).
- `VenueCapabilityV2` is not dead scaffolding — it's imported and consumed by
  `strategy-service/strategy_service/risk/v2/{margin_sim.py,preflight.py,orchestrator.py}` and covered by
  `e2e-testing/tests/integration/test_architecture_v2_roundtrip.py`.
- **But zero instantiations of `CollateralRulesV2(` or `MarginSpec(` exist anywhere outside `schemas.py` itself**
  (grepped across the whole workspace). The type is real, wired into live risk-computation code paths, and
  carries exactly the shape this todo asked for (collateral eligibility with LTV/haircut per asset, cross-margin
  and portfolio-margin support flags, netting rules) — but **no real venue has ever had one populated.** At
  runtime `collateral_rules` and `margin_spec` are `None` for every venue (the field defaults), so
  `margin_sim.py`'s `capability.margin_spec.portfolio_margin_greek_model` reads necessarily degrade to "no
  Greek model available" for every venue today, not because the concept isn't modelled but because the registry
  entries were never written.

This is the more useful and more actionable finding than either extreme ("doesn't exist" or "fully built"): the
schema is **declared and consumed, not populated.**

> **Correction (2026-08-22)**: a follow-up pass re-verified this framing before building against it and found it
> was itself incomplete — grepping fleet-wide for `VenueCapabilityV2(` (real construction, not the class
> definition) turned up **zero production call sites**, only test fixtures. The registry/resolver mechanism that
> would let a caller GET a populated `VenueCapabilityV2` for a real venue didn't exist either — there was no
> `dict[venue_id, VenueCapabilityV2]` and no resolver function anywhere in `unified-api-contracts`, so "populate
> the schema" had nowhere to populate INTO. This was a **skeleton-and-population gap, not a population-only
> gap.** The skeleton (`unified_api_contracts/registry/capability_declarations/venue_capability_v2/` — split by
> venue family into `_cefi_derivatives.py` / `_defi_lending.py`, aggregated by an `__init__.py` exposing
> `VENUE_CAPABILITY_V2: dict[str, VenueCapabilityV2]` and `get_venue_capability_v2(venue) -> VenueCapabilityV2 |
> None`) now exists, seeded with 2 real venues (`BINANCE-FUTURES`, `AAVE_V3-ETHEREUM`) and wired into one real
> caller (`strategy-service`'s `FourLayerGateOrchestrator.evaluate(venue_id=...)`). The registry-extension todo
> below is updated accordingly — it is now genuinely "populate the remaining ~50-58 venues," not "design," but it
> was NOT that narrow before this correction.

Custody eligibility and transfer-rail eligibility remain genuinely absent — no field on `VenueCapabilityV2` or
anywhere else declares "Copper-eligible / Ceffu-eligible / manual-transfer-eligible / automated-prime-broker-
eligible (per broker) / IBKR-eligible / Alpaca-eligible" per venue. That part of the todo's premise holds.

## What's real today, per topic (cite these, mark `machine-verified` in the artefacts)

### Custody / signing surfaces

Sourced from `/codex/04-architecture/custody-providers.md` via
`unified-api-contracts/unified_api_contracts/internal/architecture_v2/custody_surfaces.py` (re-verified
2026-08-18, matches the elysium plan's own re-verification cited in § A of the parent plan):

- **`CLOUD_KMS_ENCRYPTED`** — `active_may23`. `CloudKmsCustodyProvider` shipped (HSM-backed CMK envelope
  encryption).
- **`COPPER_MPC`** — `active_june1`. `CopperCustodyProvider` is the production MPC provider for DeFi (every
  chain) + non-Binance CeFi, per-wallet flip on POD-provided credentials.
- **CEFFU** — a June-1 custody provider, but **not** a `SigningSurface` enum member by design: its signing
  routes *via Copper* (`CEFFU_ROUTES_VIA_COPPER_NOTE`); `CeffuCustodyProvider` is logged as "STUB pending API
  spec." There is no distinct CEFFU signing surface to name without inventing an enum member.
- **`FIREBLOCKS_MPC`** — enum member retained for future flexibility, `SigningSurfaceStatus.OUT_OF_SCOPE` (POD
  stack choice is Copper + CEFFU only, not a May-23/June-1 target).

### Transfer rails

Sourced from `execution-service/execution_service/transfer_coordinator.py` (re-verified 2026-08-18, same file the
parent plan's § A already cites for its §11 rewrite):

- **`SUBACCOUNT_MOVE`** — the only rail that auto-registers a handler.
- **`CEX_WITHDRAW`** — commented "NOT WIRED" in source.
- **Gas top-up / floor** — no implementation anywhere in the codebase.
- **`REBALANCE`** — enum-only, no handler.
- `TransferCoordinator` itself is never instantiated in production code today — every rail above is target-state,
  not live, regardless of which handlers exist.

### Collateral / cross-margin

See "Correction" above: `VenueCapabilityV2.collateral_rules` (`CollateralRulesV2`) and `.margin_spec`
(`MarginSpec`) are declared and consumed by strategy-service's risk-v2 module, populated for **zero** real
venues today.

## Best current answer for the artefacts (mark `assumption` / `needs-check`, per rule 13)

Suggested wording for the elysium/nickai children — adapt to each artefact's register, keep the tier marks:

> **Transfer rails and custody, per venue** — <b class="ev ev-verified">✓ verified</b>. Custody today is
> `CLOUD_KMS_ENCRYPTED` (shipped) with a per-wallet flip to `COPPER_MPC` (Copper — every DeFi chain, non-Binance
> CeFi); Binance-side custody routes through Copper as well, with a CEFFU integration stubbed pending its API
> spec. Automated transfer is live for one rail (`SUBACCOUNT_MOVE`); withdrawal, gas management and rebalancing
> are specified but not wired to a running handler today.
>
> **Collateral usability and cross-margin, per venue** — <b class="ev ev-assumed">~ assumed</b>. The schema
> exists (per-asset LTV/haircut collateral rules, cross-margin and portfolio-margin support flags, netting
> rules) and is already read by strategy-service's risk simulation. As of 2026-08-22 a registry/resolver skeleton
> exists with 2 venues populated (`BINANCE-FUTURES`, `AAVE_V3-ETHEREUM`); every other venue still resolves to "no
> collateral/margin data available." See the 2026-08-22 correction above — this was a skeleton-and-population
> gap, not a population-only gap; the skeleton is now built, population of the remaining venues is not.

## Registry-extension todo spawned under W5

Per the parent todo's own requirement ("this todo's output must spawn a registry-extension todo under W5, so the
artefact ends up downstream of a machine SSOT instead of becoming one"), added to
[`system_readiness_master.md`](/plans/epics/system_readiness_master.md) W5:

- **Populate `VenueCapabilityV2.collateral_rules` / `.margin_spec` for the remaining ~50-58 relevant venues** —
  the schema (`CollateralRulesV2`, `MarginSpec`) is real and already consumed by `strategy-service/
  strategy_service/risk/v2/{margin_sim,preflight,orchestrator}.py`. **2026-08-22 update**: the registry/resolver
  skeleton this todo assumed already existed did not — it has now been built
  (`unified_api_contracts/registry/capability_declarations/venue_capability_v2/`, split by venue family,
  `get_venue_capability_v2(venue) -> VenueCapabilityV2 | None`) and seeded with 2 real venues
  (`BINANCE-FUTURES`, `AAVE_V3-ETHEREUM`, both wired into a real strategy-service caller). Every other relevant
  CeFi-derivatives/DeFi-lending venue still resolves to `None` (no data). This is genuinely population-only work
  now — the skeleton exists, per-family files avoid concurrent-edit collisions on a shared host.
- **Add per-venue custody-eligibility and transfer-rail-eligibility declarations** — genuinely absent, no
  existing type to extend (unlike collateral/margin above). New fields on `VenueCapabilityV2` or a sibling
  registry: Copper-eligible / Ceffu-eligible / manual-transfer-eligible / automated-prime-broker-eligible (per
  broker) / IBKR-eligible / Alpaca-eligible, declared rather than inferred at runtime — matches W5's existing
  P0 "Transfer capability per venue as explicit eligibility flags" item exactly; this is that item's concrete
  implementation target now that the schema landing spot (`VenueCapabilityV2`) is identified.

See the W5 edit itself for the tracked todo text and priority.
