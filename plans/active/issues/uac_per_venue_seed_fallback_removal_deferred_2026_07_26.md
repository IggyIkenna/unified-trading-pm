---
doc_type: issue
title:
  "UAC per-venue seed fallback stays IN for now — removal deferred until DEFI/TRADFI/PREDICTION get live catalogue
  providers and G1-G5 closes"
summary: >-
  Operator ruling (2026-07-26) on the `[OPERATOR]` todo in `cefi_misc_audits_and_hygiene_2026_07_25.md`: do NOT remove
  `unified_api_contracts.registry.market_data_categories.get_expected_instruments_for_venue`'s per-venue MVP-seed
  fallback yet. The gating blast-radius audit (candidate 9 of `cefi_consolidated_native_ao_extract_2026_07_25.md`) had
  never actually run — this doc records the audit performed to make the ruling. All 3 real production callers currently
  depend on the fallback firing, two by explicit documented design: MTDS's `_resolve_instrument_provider` (case 5 of its
  own resolution order) and deployment-api's `venue_resolution.py`, which builds a live catalogue provider ONLY for CEFI
  — DEFI/TRADFI/PREDICTION pass `instruments_provider=None` unconditionally today, making the UAC seed the sole source
  of the Tier-3 per-instrument honest-coverage denominator for those 3 asset groups' data-status UI. Removing the
  fallback now would reproduce, for DEFI/TRADFI/PREDICTION, the exact silent-coverage-loss failure mode the operator's
  2026-07-18 ruling (`mtds@3253cae3`, "catalogues FAIL LOUD") was meant to eliminate for CEFI — it would just move the
  blast radius rather than close it. This is a **deferred-not-declined** ruling: tracked here as the reusable revisit
  trigger instead of a dangling plan pointer.
status: open
nature: notes
asset_group: [cefi, defi, tradfi, prediction]
stage: [data, meta]
repos: [unified-api-contracts, market-tick-data-service, deployment-api, instruments-service]
scope: [engineer, admin]
tags: [uac, fallback, operator-ruling, honest-coverage, deferred]
related:
  [
    /plans/active/cefi_misc_audits_and_hygiene_2026_07_25.md,
    /plans/active/cefi_consolidated_native_ao_extract_2026_07_25.md,
    /plans/active/instruments_cefi_g1_g5_gate_execution_2026_07_24.md,
    /plans/active/instruments_tradfi_g1_g5_gate_execution_2026_07_24.md,
    /codex/02-data/instruments-foundation-and-catalogue-completeness.md,
  ]
created: 2026-07-26
last_updated: "2026-07-26"
parent_epic: cefi_master
assigned_vm: NA
execution_scope: local-only
priority: P2
resolved_by:
source: >-
  Operator ruling 2026-07-26 on the `[OPERATOR]` blast-radius-audit todo in `cefi_misc_audits_and_hygiene_2026_07_25.md`
  (candidate 9 of `cefi_consolidated_native_ao_extract_2026_07_25.md`) — the audit had never actually run before the
  removal todo was drafted; this doc is that audit's output plus the resulting deferred-not-declined ruling.
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
---

# UAC per-venue seed fallback — removal deferred

## Ruling

**Keep the fallback for now.**
`unified_api_contracts.registry.market_data_categories.get_expected_instruments_for_venue`
(`unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:2440-2532`) still falls through to
`_default_seed_instruments_for` (:2535-2622) whenever a caller passes `instruments_provider=None` outright. This is
narrower than the removal-candidate todo's summary implied: it does NOT fire when a supplied provider returns
`None`/`[]` for one specific venue (that path returns `[]`, no seed) — only when the caller never builds a provider
callable for that asset_group/venue at all.

## Blast-radius audit (performed here — the gating candidate-9 todo had never run)

Three real production call sites, deduped across worktree/branch clones:

1. **`market-tick-data-service/market_tick_data_service/engine/orchestrator/sentinels.py:638`** (`_emit_tier3_for_dt` ←
   `_resolve_instrument_provider`, :461-506) — MTDS's own docstring states the fallback is explicit case 5 of its
   resolution order ("None → UAC MVP seed tables (v1 fallback)"), reached whenever a venue's asset_group isn't yet wired
   into that asset_group's live `*_catalog_by_venue` dict. **Blocks removal as-is.**
2. **`market-tick-data-service/market_tick_data_service/engine/orchestrator/preflight.py:495`**
   (`_uac_seed_instruments_for_venue`) — calls `get_expected_instruments_for_venue(venue, dt)` with NO provider argument
   at all, by design, as the forward-poll bootstrap's last-resort wire-symbol source when the live instrument index is
   missing/stale. **Blocks removal.**
3. **`deployment-api/deployment_api/services/data_status/venue_resolution.py:220-282`** → `instrument_coverage.py:376` →
   `mtds.py:880-897` — builds a live CEFI catalogue provider ONLY (`if category.upper() == "CEFI":` — the module's own
   comment: _"For other asset_groups: instruments_provider=None falls back to UAC MVP seed tables (existing
   behaviour)"_). **Hard blocks removal for DEFI/TRADFI/PREDICTION** — this is the sole live source of the Tier-3
   per-instrument honest-coverage denominator on the data-status UI for those 3 asset groups today.

## Why removal isn't safe yet

- CEFI catalogue completeness (G1-G5) is itself still in-flight: `instruments_cefi_g1_g5_gate_execution_2026_07_24.md`
  is `status: active` with G4 OPEN, and a live-measured 211-row catalogue-rollup gap (`instruments-service@f6f16785`:
  OKX-SPOT 174, COINBASE-SPOT 4, BITGET-FUTURES 33) exists today.
- DEFI/TRADFI/PREDICTION have **no live-provider wiring path at all** in `venue_resolution.py` — this is a total
  absence, not a partial gap, so "catalogues are complete enough" is the wrong question for those 3 asset groups; the
  right question (wiring) hasn't been started.
- The cited precedent, `mtds@3253cae3` ("catalogues FAIL LOUD, remove UAC-seed fallback"), covers a narrower case —
  MTDS's own catalogue **readers** raising when a catalogue read fails/is absent/schema-drifted. It never touched this
  UAC-registry-level seed fallback for the "venue not yet catalog-wired" case, so "already applied" (per the original
  todo's phrasing) is true only for that narrower case.

## Revisit trigger — what unblocks a real removal decision

1. `deployment-api/venue_resolution.py` gets live catalogue-provider wiring for DEFI, TRADFI, and PREDICTION (mirroring
   the existing CEFI branch) — new engineering work, not yet drafted as a todo anywhere.
2. CEFI's G1-G5 gates (`instruments_cefi_g1_g5_gate_execution_2026_07_24.md`) close, specifically G4.
3. TRADFI's G1-G5 gates (`instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`) close.
4. Once (1)-(3) land, re-open this decision: at that point every real caller either no longer needs the fallback (live
   provider wired) or the underlying catalogue is proven complete, and removal can follow the same typed-exception
   pattern as `mtds@3253cae3` (raise, don't silently degrade; update tests in the same commit).

No code change ships from this doc. It exists so the deferred decision has a durable, re-discoverable home instead of
dangling inside a closed plan todo.
