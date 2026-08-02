---
doc_type: issue
title:
  UAC VENUE_DATA_AVAILABILITY still declares a live "POLYGON" TradFi provider entry — surfaced in generated UI reference
  data despite Polygon.io's 2026-07-19 removal
summary: >-
  Follow-up from `instruments_satellite_ao_dispatch_batch1_2026_07_27.md` todo 4's "MTDS/reference-data conflation risk
  — anywhere else?" audit. The specific site the audit was pointed at (`market_data_categories.py`'s
  `VENUE_DATA_TYPE_CAPABILITIES["POLYGON"]`) is already fixed (`unified-api-contracts@e34afc1d`, 2026-07-31). But a
  SIBLING registry in the same file family — `data_availability.py`'s `VENUE_DATA_AVAILABILITY["POLYGON"]` — was missed.
  Unlike the already-cleaned dict, this one is NOT dead code:
  `unified-trading-pm/scripts/openapi/generate_ui_reference_data.py`'s `extract_venue_data_availability()` iterates
  every key unconditionally and emits it into the UI-facing `ui-reference-data.json`, so a regeneration run currently
  surfaces POLYGON as a live TradFi data provider ("Real-time + historical equities/options data") that no longer has
  any adapter, venue registration, or capture code behind it.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [unified-api-contracts]
scope: [engineer, admin]
tags: [tradfi, polygon, stale-registry, reference-data, conflation, ui-reference-data, hygiene]
related:
  [
    /plans/active/instruments_satellite_ao_dispatch_batch1_2026_07_27.md,
    /plans/active/issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md,
    /plans/active/issues/tradfi_adapter_dead_code_fallback_audit_2026_07_25.md,
    /plans/active/issues/breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md,
    /plans/active/issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
  ]
created: "2026-08-02"
parent_epic: instruments_master
assigned_vm: NA
resolved_by:
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.08
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    unified-api-contracts/unified_api_contracts/registry/data_availability.py,
    unified-trading-pm/scripts/openapi/generate_ui_reference_data.py,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
  ]
supersedes:
superseded_by:
depends_on:
source: >-
  instruments_satellite_ao_dispatch_batch1_2026_07_27.md todo 4 ([VERIFY] P2 "Audit whether the same MTDS/reference-data
  conflation risk exists anywhere else"), worked 2026-08-02.
---

# UAC `VENUE_DATA_AVAILABILITY["POLYGON"]` is a stale, live-consumed registry entry

## What I found

Auditing `instruments_satellite_ao_dispatch_batch1_2026_07_27.md` todo 4 (re-verifying whether the TradFi
`POLYGON`/`FRED` "reference-data-in-the-wrong-registry" risk from
`honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md` still holds), I re-checked every venue-shaped
UAC registry, not just the one line reference the source doc cited:

1. **`market_data_categories.py`'s `VENUE_DATA_TYPE_CAPABILITIES["POLYGON"]`** (the site the audit named) — **already
   fixed**. `unified-api-contracts@e34afc1d` (2026-07-31, verified reachable on `origin/live-defi-rollout`) removed this
   stale entry, citing "Polygon.io, removed as a tradfi source 2026-07-19, never cleaned up here." Confirmed:
   `VENUES_BY_ASSET_GROUP["tradfi"]` has no bare `"POLYGON"` venue key today (only `NASDAQ`/`NYSE`/`CME`/`ICE`/
   `CBOE`/`KRX`/`FX`/`FRED`).
2. **`FRED`** — correctly placed, not a conflation instance. Added to `VENUES_BY_ASSET_GROUP["tradfi"]` 2026-07-29 with
   a real adapter (`market-tick-data-service/.../market_interface/adapters/tradfi/fred_adapter.py`); its
   `VENUE_DATA_TYPE_CAPABILITIES["FRED"]` entry (`{"yield_curve": ..., "ohlcv_1d": ...}`) was corrected the same day to
   match what `FredAdapter.write_canonical_shard` actually emits (verified directly in the adapter's
   `data_type = "yield_curve" if instrument_type is InstrumentType.BOND else "ohlcv_1d"` — never `macro_result`, which
   the registry wrongly declared before the fix).
3. **The adjacent real bug this audit traces back to** — `corporate_action_confirmed`/`earnings_result` seeded into the
   MTDS tick manifest despite MTDS never writing them (real writer = features-service's calendar module) — is also
   already fixed, via two verified-reachable commits: `instruments-service@03f71c81` (2026-07-15, stopped the
   forward-seed in `enumerate_expected_universe.py`) and `market-tick-data-service@c24db4cf` (2026-07-28, deleted
   428,343 already-orphaned rows, 0 captured rows lost). `enumerate_expected_universe.py`'s "TRADFI IS DELIBERATELY NOT
   GATED" comment (line 711) is still present and still operator-ratified design, not an open bug.
4. **But — `data_availability.py`'s `VENUE_DATA_AVAILABILITY["POLYGON"]` was missed.** Currently (verified 2026-08-02,
   lines ~323-329):
   ```python
   "POLYGON": ProviderDataAvailability(
       venue_name="POLYGON",
       asset_group="tradfi",
       availability_lag_hours=0.0,
       available_after_utc_hour=None,
       is_t_plus_one=False,
       notes="Real-time + historical equities/options data",
   ),
   ```
   This is a DIFFERENT dict, in a DIFFERENT file, than the one `e34afc1d` fixed. Unlike that one — which was confirmed
   dead/unreachable code because expected-universe producers iterate `VENUES_BY_ASSET_GROUP`, never the capability
   dict's own keys — this dict is NOT dead. `unified-trading-pm/scripts/openapi/generate_ui_reference_data.py`'s
   `extract_venue_data_availability()` (~line 550) does `for venue_name, entry in VENUE_DATA_AVAILABILITY.items():`
   unconditionally and writes every entry into the generated `ui-reference-data.json`, which UI-facing consumers read. A
   regen run today would surface `"POLYGON"` with `asset_group: "tradfi"` and the above "Real-time + historical
   equities/options data" note — a currently-nonexistent data source presented as live.
5. **This specific registry was known to need cleanup alongside the others, and wasn't.**
   `tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md` (line 270-272) documents the
   established removal pattern for a retired venue: strip it from **all 5** venue-shaped registries —
   `VENUES_BY_ASSET_GROUP` + `VENUE_DATA_TYPE_CAPABILITIES` (`market_data_categories.py`), `expected_coverage.py`,
   `venue_adapter_keys.py`, **and `data_availability.py`** — proven live on the `YAHOO_FINANCE` removal
   (`unified-api-contracts@fec3f110`, 2026-07-15). I confirmed `expected_coverage.py`, `venue_adapter_keys.py`, and
   `venue_launch_dates.py`/`venue_mapping.py` carry no bare TradFi `"POLYGON"` key today — only `data_availability.py`
   was left behind when POLYGON's turn came.
6. **Separately, and more significantly: instruments-service's actual `massive.py` adapter (the real Polygon.io
   reference-data adapter code) is still live, tested, and fully wired** — this is
   `tradfi_adapter_dead_code_fallback_audit_2026_07_25.md` Finding I-2 (filed 2026-07-31, still open as
   `[OPERATOR] P1`), which found the 2026-07-19 removal never touched instruments-service at all. I am NOT re-filing
   that finding — it's already tracked and awaiting an operator decision — but it directly corroborates that the
   "Polygon.io removal" was scoped/executed inconsistently across repos, which is exactly the failure class producing
   finding 4 above.

## Why it matters

Low real-world severity (this doesn't touch capture, backfill, or the manifest — `data_availability.py` is consumed only
by the UI-reference-data generator), but it's a genuine correctness bug in generated, UI-facing data: anyone
regenerating `ui-reference-data.json` today gets a phantom "POLYGON" TradFi provider entry with fabricated present-tense
availability characteristics, 2+ weeks after that source was removed. It's also a second confirmed instance (after
Finding I-2 above) of the same root cause: the 2026-07-19 Polygon.io removal was never swept against the full,
already-documented 5-registry checklist, so cleanup happened piecemeal, registry-by-registry, as each was separately
noticed.

## Recommended decision

Remove the `"POLYGON"` entry from `VENUE_DATA_AVAILABILITY` in
`unified-api-contracts/unified_api_contracts/registry/data_availability.py`, mirroring the exact pattern already proven
twice (`e34afc1d` for the capability dict; `fec3f110` for the full 5-registry `YAHOO_FINANCE` removal). No design call
needed — this is a mechanical parity fix. Optionally (not blocking): re-run
`unified-trading-pm/scripts/openapi/generate_ui_reference_data.py` afterward and confirm `"POLYGON"` no longer appears
in the regenerated `ui-reference-data.json`.

## Todos

- [ ] [DATA] P2. **Remove the stale `"POLYGON"` entry from `VENUE_DATA_AVAILABILITY`** in
      `unified-api-contracts/unified_api_contracts/registry/data_availability.py` (currently ~lines 323-329, under the
      "── TradFi reference data ──" section header, immediately after the `FRED` entry) — mirror the exact removal
      pattern used for the sibling `VENUE_DATA_TYPE_CAPABILITIES["POLYGON"]` fix (`unified-api-contracts@e34afc1d`) and
      the full 5-registry `YAHOO_FINANCE` removal (`unified-api-contracts@fec3f110`). Repo: unified-api-contracts. Done
      when: the entry is gone, `quality-gates.sh` is green, and re-running `generate_ui_reference_data.py`'s
      `extract_venue_data_availability()` (or a targeted unit test) confirms `"POLYGON"` no longer appears in the
      output.

## Progress Log

- **2026-08-02**: Filed from `instruments_satellite_ao_dispatch_batch1_2026_07_27.md` todo 4's audit. See that plan for
  the full definitive yes/no verdict + evidence trail.
