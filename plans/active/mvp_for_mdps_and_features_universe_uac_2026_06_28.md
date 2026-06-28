---
doc_type: plan
title: UAC — MVP-for-MDPS (= MDS MVP) + MVP-for-features (most-liquid-spot selector)
summary:
  "Codify in UAC that MDPS MVP == instruments-catalogue MVP, and build the missing feature-MVP contract: delta-one
  features only on the most-liquid spot representative per base (Binance default for crypto), options/dated-futures get
  MDPS candles only."
status: active
nature: spec
asset_group: [cross-cutting]
stage: [data, features]
repos: [unified-api-contracts]
scope: [engineer, admin]
tags: [uac, mvp, feature-universe, most-liquid-spot, delta-one, options, futures, contract]
related: [./mdps_features_reduced_artifact_tracker_2026_06_28.md, ../epics/features_and_ml_master.md]
created: 2026-06-28
parent_epic: features_and_ml_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: design
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.8
assigned_role: backend-engineer
model_tier: opus-required
thinking_tier: high
drift_direction: advance-code
last_updated: 2026-06-28
locked_by: NA
locked_since:
supersedes:
superseded_by:
depends_on:
source: [operator request 2026-06-28]
---

# UAC — MVP-for-MDPS + MVP-for-features

Two governing concepts, both owned by UAC so they are greppable + checkable.

**Execution model:** Opus / thinking high — a cross-cutting contract in the SSOT types library that every AG's MDPS +
features run reads; needs simultaneous reasoning over `mvp_scope.py`, `features_mvp_universe.py`, and the instrument
registry.

## Concept 1 — MVP-for-MDPS = MVP-for-MDS

MDPS processes exactly the instruments-catalogue MVP capture universe MDS already uses. No separate screen. State it as
a derived helper so "what must MDPS cover" is computed from the MDS/UAC MVP, not hand-maintained.

## Concept 2 — MVP-for-features (NEW — does not exist today)

Research confirms `FeatureFamilyUniverseConfig` exists and delta-one already rejects `OPTIONS/OPTION/FUTURE` via
`NON_LINEAR_TYPES`, but the **most-liquid representative selector is MISSING** — features process whatever venue is in
the manifest. This plan builds it:

- Options + dated futures → **MDPS candles only, no delta-one features** (formalise + test the existing exclusion).
- Delta-one features computed on the **most-liquid PERP representative per base, selected BY VOLUME** — NOT spot. Every
  MVP base has a perp (perp-gate rule) and perps are almost always the most liquid leg (higher OI via leverage), so the
  representative is the highest-**volume** perp across available venues (Binance usually wins for crypto, but it is
  _chosen by measured volume_, not hardcoded). TradFi has no perp → the representative is the most-liquid 1m source.
- **Separate most-liquid-SPOT selector (also volume-based) for EXECUTION, not features** — Plan 9 consumes it. Both
  selectors live in this one UAC home so the volume basis (venue volumes we already have) is computed once.

## Todos

- [ ] [DESIGN] P1. (opus) Write the MVP-for-MDPS helper: a UAC function returning the MDPS processing universe from the
      MDS/instruments MVP (`mvp_scope.py` v10), proving identity (same venue/instrument set). — Gate:
      `mdps_mvp_universe(asset_group)` returns a set equal to the MDS capture MVP for that AG; unit test asserts
      equality.
- [ ] [DESIGN] P1. (opus) Define the **most-liquid-PERP representative** selector: per base asset, the highest-VOLUME
      perp across available venues for delta-one features (volume from the manifest/candle volume we already have — not
      hardcoded to Binance). TradFi (no perp) → most-liquid 1m source. Make the volume basis + deterministic tie-break
      explicit. — Gate: `feature_perp_representative(base, asset_group)` returns a single (venue, instrument) chosen by
      measured volume; documented basis + tie-break.
- [ ] [DESIGN] P1. (opus) Define the **most-liquid-SPOT representative** selector (volume-based) for EXECUTION use
      (consumed by Plan 9), from the same venue-volume basis. — Gate: `execution_spot_representative(base, asset_group)`
      returns a single (venue, instrument) by volume; unit test.
- [ ] [IMPLEMENT] P1. Extend `features_mvp_universe.py` so `filter_instruments_for_family` (a) drops options/dated
      futures from delta-one families, (b) collapses each base to its most-liquid-PERP representative for delta-one.
      Keep family configs that legitimately include dated futures (e.g. `futures_basis`) intact. — Gate: given a mixed
      instrument list, the filter returns exactly the perp reps for delta-one families and excludes non-linear types.
- [ ] [TEST] P1. Unit tests across all 5 AGs: options/futures excluded from delta-one; non-CeFi pass-through behaviour
      decided + tested (TradFi reps chosen, DeFi handled); the perp representative is chosen by measured volume (Binance
      usually wins for crypto but via volume, not hardcode) and tie-breaks deterministically. — Gate: tests pass in UAC
      `quality-gates.sh`; no `Any`/`type: ignore`.

## Current-state delta (audited 2026-06-28)

- **Exists:** `unified_api_contracts/canonical/crosscutting/features_mvp_universe.py` (`FeatureFamilyUniverseConfig`:
  per-family `base_asset_universe`, `include_dated_futures`, `include_options_underlyings`);
  `features_service/delta_one/cli/handlers/instrument_type_filter.py` (`NON_LINEAR_TYPES = [OPTIONS, OPTION, FUTURE]`)
  already excludes non-linear payoffs; `filter_instruments_for_family`
  - `filter_delta_one_instruments` wire it.
- **MISSING (the delta):** any most-liquid-representative selection. `data_loader.get_available_instruments(date)` reads
  the MDPS manifest and features process EVERY venue present — no collapse-to-one-representative;
  `mvp_universe_filter.py` passes NON-CeFi AGs through untouched. No volume-based selection anywhere.
- **Build:** the perp-by-volume (features) + spot-by-volume (execution) selectors, and wire the perp collapse into
  `filter_instruments_for_family`; keep `futures_basis`-style dated-futures families intact.
- [ ] [AGENT] P1. UAC QG green; quickmerge `--agent --files`. Pre-audit + update the two downstream consumers
      (features-service selection, and Plan 6's harness) if the signature changes — no "fix later". — Gate: QG green; CI
      `quality-gates-v2` green; downstream consumers compile against the new signature.

## Notes

- This is the contract Plan 6 (coverage harness) and Plan 9 (execution fidelity) read to know _what_ to smoke-test and
  _which_ instruments carry features vs candles-only.
- SSOT direction: this is `advance-code` — UAC is the right home for the universe contract; do not duplicate it in
  features-service or MDPS.
