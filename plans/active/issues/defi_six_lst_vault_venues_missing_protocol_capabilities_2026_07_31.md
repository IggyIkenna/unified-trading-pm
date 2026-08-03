---
doc_type: issue
title:
  6 newly-live LST/vault venues (ANKR/STADER/STAKEWISE/SWELL/MANTLE/MAKER) have no PROTOCOL_CAPABILITIES entry — Layer-1
  completeness_pct silently excludes them regardless of DEFI_VENUE_PHASE
summary: >-
  While completing defi_venue_pipeline_to_live_ao_build_2026_07_30.md todo 5 (flipping DEFI_VENUE_PHASE to "live" for
  these 6 venues, confirming VENUES_BY_ASSET_GROUP["defi"] picks up the flip), re-measured Layer-1 completeness_pct via
  `instruments-service/scripts/measure_honest_coverage.py --asset-group defi --diagnose-layer1` per the todo's own
  instruction. Before/after were BYTE-IDENTICAL (EXPECTED=102 aligned, matched=45, missing=57, completeness_pct= 44.1%,
  same first-5-example tuples) despite VENUES_BY_ASSET_GROUP["defi"] and instruments-service's own _build_defi_venues()
  both genuinely growing from 94 to 100 venues (verified directly, not assumed). Root-caused:
  `expected_universe.py::build_expected("defi")` gates every (venue, instrument_type) pair through
  `_venue_itype_is_valid`, which for defi looks up the venue's PROTOCOL in UAC's
  `unified_api_contracts.registry.capability_declarations._defi.PROTOCOL_CAPABILITIES` dict
  (`_get_defi_protocol_itypes()`). None of ankr/stader/stakewise/swell/mantle/maker exist as keys in that dict
  (confirmed via direct grep — zero hits), so `_venue_itype_is_valid` returns False for every itype/data_type
  combination for these 6 venues, and they contribute ZERO tuples to EXPECTED no matter what DEFI_VENUE_PHASE says. This
  is a THIRD input the plan's own historical citation (`defi_venue_phase_live_definition_contradiction_2026_07_22 .md`)
  did not know about — it said only "DEFI_VENUE_PHASE/VENUES_BY_ASSET_GROUP['defi']" feed this metric, but
  PROTOCOL_CAPABILITIES is a genuinely separate, undocumented third gate.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [unified-api-contracts, instruments-service]
scope: [engineer]
tags: [defi, honest-coverage, layer1, protocol-capabilities, expected-universe, denominator]
related:
  [
    /plans/archive/2026_08/defi_venue_pipeline_to_live_ao_build_2026_07_30.md,
    /plans/archive/2026_07/defi_venue_phase_live_definition_contradiction_2026_07_22.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-07-31"
last_updated: "2026-07-31"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.48
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
source: >-
  Found by slot-16 (data_engineering craft) while re-measuring completeness_pct for
  defi_venue_pipeline_to_live_ao_build_2026_07_30.md todo 5's own required before/after check. Not fixed inline: an
  already-live precedent (PUFFER, PROTOCOL_CAPABILITIES declares data_types=["staking_yields","oracle_prices"]) does NOT
  match what lst_rates_handler.py actually writes for it (data_type="lst_rates") — this whole area has demonstrated,
  pre-existing declared-vs-actual drift (Layer-1 is currently only 44.1% complete, 57 missing + 83 stray tuples
  system-wide), so a rushed new entry risked introducing fresh stray/missing tuples rather than fixing anything. Needs a
  deliberate per-venue check of what MTDS actually writes (already known from this session:
  data_type=lst_rates/instrument_type=lst for the 5 LST venues, data_type=vault_share_price/instrument_type=
  yield_bearing for MAKER) before adding entries.
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    /codex/02-data/honest-coverage-model.md,
    /plans/archive/2026_08/defi_venue_pipeline_to_live_ao_build_2026_07_30.md,
    unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py,
    instruments-service/scripts/expected_universe.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/lst_rates_handler.py,
  ]
---

# 6 newly-live LST/vault venues missing PROTOCOL_CAPABILITIES

## What I found

`unified_api_contracts.registry.capability_declarations._defi.PROTOCOL_CAPABILITIES` is a dict keyed by lowercase
protocol name (e.g. `"puffer"`, `"karak"`, `"renzo"`) declaring each protocol's `instrument_types` + `data_types` — the
SSOT `expected_universe.py::_venue_itype_is_valid` uses to gate which (venue, instrument_type, data_type) tuples are
genuinely EXPECTED for Layer-1 honest coverage. `ankr`/`stader`/`stakewise`/`swell`/`mantle`/`maker` have no entry in
this dict at all (confirmed via `grep -n '"ankr"\|"stader"\|"stakewise"\|"swell"\|"mantle"\|"maker"' _defi.py` — zero
hits for any casing). Consequently these 6 venues, despite now being `DEFI_VENUE_PHASE="live"` and present in both
`VENUES_BY_ASSET_GROUP["defi"]` and `_build_defi_venues()` (verified: both sets = 100 members, includes all 6),
contribute ZERO tuples to the Layer-1 EXPECTED matrix — `measure_honest_coverage.py --diagnose-layer1`'s
`completeness_pct` for `defi` is completely blind to whether these venues are captured or not.

Ground truth for what MTDS actually writes (read directly from this session's own real backfilled GCS objects, not
guessed):

- ANKR/STADER/STAKEWISE/SWELL/MANTLE: `instrument_type="lst"`, `data_type="lst_rates"` (via `lst_rates_handler.py`)
- MAKER: `instrument_type="yield_bearing"`, `data_type="vault_share_price"` (via `vault_share_price_handler.py`)

## Why it matters

- The todo that flipped these venues to "live" explicitly required re-measuring `completeness_pct` before/after as proof
  the flip did something — it silently did NOT, for a reason the todo's own historical baseline citation didn't know
  existed. Any FUTURE similar phase-flip todo will hit the identical silent no-op unless this gate is either fixed or
  explicitly documented as a known limitation to check first.
- Honest-coverage correctness: these 6 venues now have 90 real captured days each (verified
  `defi_venue_pipeline_to_live_ao_build_2026_07_30.md` todo 3) but Layer-1 will report them as permanently
  "not-expected" — the inverse of the phantom-expected-but-never-captured failure this whole system exists to catch.
- Demonstrated precedent risk (PUFFER's declared vs. actual data_type mismatch) means this needs a careful,
  evidence-checked fix per venue, not a blind copy-paste of an existing entry's shape.

## Todos

- [x] ✅ [DATA] P2. Add `PROTOCOL_CAPABILITIES` entries for `ankr`/`stader`/`stakewise`/`swell`/`mantle` (protocol_class
      matching UAC's existing LST taxonomy — check whether `_RESTAKING`/`_STAKING`/an `_LST`-specific instrument-type
      set is the right constant to reuse; PUFFER's own entry uses `_RESTAKING` + `staking_yields`/`oracle_prices`
      despite writing `lst_rates` in practice, so do NOT blindly copy it — verify against what `lst_rates_handler.py`
      ACTUALLY writes for each: `instrument_type="lst"`, `data_type="lst_rates"`) and `maker`
      (`instrument_type="yield_bearing"`, `data_type="vault_share_price"`, matching `vault_share_price_handler.py`).
      Done-when: `measure_honest_coverage.py --asset-group defi --diagnose-layer1` shows these 6 venues' tuples now
      appearing in EXPECTED (not necessarily fully matched — that depends on real capture — but no longer silently
      excluded), and re-running the full Layer-1 check does not introduce NEW stray/missing tuples beyond the
      already-known pre-existing 57/83 baseline (compare before/after counts explicitly). (repo: unified-api-contracts)
      — unified-api-contracts@314af7b8: entries landed for ankr/stader/stakewise/swell/mantle (instrument_type="lst",
      data_type="lst_rates") and maker (instrument_type="yield_bearing", data_type="vault_share_price"); commit's own
      A-B test shows EXPECTED 102→108 (+6), matched 83→89 (+6), missing unchanged (19), stray 671→665 (-6), no
      regression.
- [ ] [DATA] P3. Audit whether OTHER already-`phase="live"` DeFi venues have the same PUFFER-style declared-vs-actual
      data_type mismatch in `PROTOCOL_CAPABILITIES` (a quick per-protocol cross-check: does the declared `data_types`
      list match what the corresponding MTDS handler actually stamps via `write_defi_rows(data_type=...)`?) — this
      session found ONE clear mismatch (PUFFER) while investigating a different question; there may be more contributing
      to the system's current 57-missing/83-stray Layer-1 baseline. (repo: unified-api-contracts,
      market-tick-data-service)

## Progress Log

- **2026-07-31 (slot-16, data_engineering craft)**: filed after diagnosing the zero-delta completeness_pct measurement
  required by `defi_venue_pipeline_to_live_ao_build_2026_07_30.md` todo 5. Not fixed inline — see `source:` above for
  why.
- **context-scout 2026-08-01**: populated context_scope (5 entries).
- **slot-15 2026-08-02**: flipped todo 1's checkbox — code was already shipped by another slot
  (unified-api-contracts@314af7b8, confirmed on origin/live-defi-rollout) but the plan checkbox was never flipped. Todo
  2 (P3 audit) remains open, out of scope for this task.
