---
doc_type: issue
title: MDPS CeFi DERIBIT options_chain candle derivation fails at the 15s tier — no SchemaContract registered
summary: >-
  market-data-processing-service's candle-derivation path raises a CRITICAL SchemaContractNotFoundError for
  asset_group='cefi' instrument_type='OPTION' data_type='options_chain_15s' venue='DERIBIT', causing the per-date
  subprocess to exit rc=1 for every date containing DERIBIT options_chain data. Root cause: unified-api-contracts'
  CONTRACT_REGISTRY has no "option" instrument_type entries at all for candle-derived data_types, while MDPS
  deliberately does NOT scope cefi's timeframe ceiling down (config.py comment: "cefi/defi are deliberately OMITTED:
  their UAC constants already equal the full 7-timeframe default"), so cefi keeps requesting the 15s tier with nothing
  registered to serve it.
status: open
nature: process
asset_group: [cefi]
stage: [data]
repos: [unified-api-contracts, market-data-processing-service]
scope: [engineer]
tags: [mdps, uac, schema-contract, options-chain, cefi, deribit, data-correctness, cross-cutting]
related:
  [
    /plans/active/issues/mdps_force_flag_dropped_subprocess_per_date_2026_08_08.md,
    /plans/active/issues/cefi_track7_candle_bundle_regeneration_vm_2026_08_04.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
author: slot-24 (cicd/data_engineering)
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.3
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
locked_by:
locked_since:
resolved_by:
source: >-
  Discovered while re-checking terminal state of mdps-backfill-cefi-20260808-095136 for
  mdps_force_flag_dropped_subprocess_per_date_2026_08_08.md todo 2 (gated, VM still RUNNING).
context_scope:
  [
    unified-api-contracts/unified_api_contracts/internal/schemas/contracts.py,
    market-data-processing-service/market_data_processing_service/config.py,
    /plans/active/issues/mdps_force_flag_dropped_subprocess_per_date_2026_08_08.md,
  ]
---

# MDPS CeFi DERIBIT options_chain candle derivation fails at the 15s tier

## What I found

While re-checking the terminal state of `mdps-backfill-cefi-20260808-095136` (gated relaunch todo, see the related
force-flag issue doc), its live `run.log` showed a CRITICAL error + a `rc=1` per-date subprocess failure for
`2023-08-10`:

```
2026-08-08 22:37:41,173 ERROR [CRITICAL] unknown error in market-data-processing-service.process_instrument_file:
  No SchemaContract registered for asset_group='cefi' instrument_type='OPTION' data_type='options_chain_15s'
  venue='DERIBIT'. Add a contract to unified_api_contracts.internal.schemas.contracts.CONTRACT_REGISTRY
  (and VENUE_CONTRACT_OVERRIDES if the schema is venue-specific) before rerunning the read/migration pipeline.
  (instrument=.../asset_group=cefi/venue=DERIBIT/instrument_type=options_chain/data_type=trades/underlying=ETH/...)
2026-08-08 22:39:25,259 ERROR [CRITICAL] ... same error, underlying=BTC ...
2026-08-08 22:39:28,205 ERROR subprocess-per-date: date=2023-08-10 rc=1 (FAILED)
```

Root cause, confirmed by reading both sides:

1. `market_data_processing_service/config.py::_TIMEFRAME_CEILING_BY_ASSET_GROUP` deliberately omits `cefi`/`defi`
   (comment at config.py:73-75: "their UAC constants already equal the full 7-timeframe default, so scoping them would
   be a no-op") — so `resolve_timeframes()` requests the FULL 7-timeframe set (incl. `15s`) for every cefi candle job,
   unscoped.
2. `unified_api_contracts/internal/schemas/contracts.py::CONTRACT_REGISTRY` has **zero** `instrument_type="option"` (or
   `"OPTION"`) entries for any candle-derived (`*_15s`/`*_1m`/`*_5m`/.../`*_24h`) `data_type` — confirmed via grep, no
   matches anywhere in the file. `VENUE_CONTRACT_OVERRIDES` was not checked for a DERIBIT-specific override but the
   generic registry gap alone is sufficient to explain the failure (the fallback chain in `lookup_contract()` only
   case-normalises `instrument_type`/`data_type`, it does not synthesize a missing contract).

This is the SAME failure shape as two already-fixed bugs (`market-data-processing-service@034c1df` for tradfi
`ohlcv_15s`/CME UNKNOWN, and the sports `_4h`/`_5m`/`_15s`/`_24h` storm fix, both referenced in config.py's own
comments) — a candle tier requested by the timeframe-ceiling resolution logic with no corresponding `SchemaContract`
registered to serve it. Unlike those two, the fix here is NOT "narrow the ceiling" (the config.py comment explicitly
asserts cefi's declared UAC timeframe set is correct and complete at 7 tiers) — it means the CONTRACT_REGISTRY itself is
missing the `option`/`OPTION` candle contracts it should have for cefi, which is a UAC gap, not an MDPS gap.

**Impact confirmed live**: every per-date subprocess touching DERIBIT `options_chain` data (both `underlying=ETH` and
`underlying=BTC` observed) hits this CRITICAL + `rc=1`, meaning that date's candle-derivation run for `options_chain` at
the 15s tier silently fails while the subprocess-per-date loop's shard-level isolation lets the overall backfill
continue to the next date (masking the failure from the top-level exit code — the run still completes/relaunches
normally). This affects every CeFi options backfill run using the default subprocess-per-date path since it went default
(`mdps_polars_engine_cost_sharpening_2026_06_28`), not just this one VM.

## Why it matters

DERIBIT (and likely any other venue/asset publishing CeFi `options_chain` data) never gets a 15s candle tier
materialized, and every date that includes such data logs a CRITICAL + exits its per-date subprocess non-zero — a
genuine data-correctness gap that has been silently present since the CONTRACT_REGISTRY was populated for cefi options
in the first place, invisible because the top-level backfill run still exits 0.

## Recommended decision

Register the missing `CONTRACT_REGISTRY` entries for cefi options candle data_types (at minimum
`("cefi", "option", "options_chain_15s")` and its sibling timeframes, or a `VENUE_CONTRACT_OVERRIDES` entry if the 15s
options-chain candle schema is genuinely venue-specific to DERIBIT) — mirroring the existing `CEFI_OPTIONS_CHAIN_TRADES`
raw-tick contract shape. Needs a maintainer with UAC schema-design context to confirm the correct column shape for a 15s
options-chain candle before registering it (not a blind copy of the raw-trades contract) — scoped here as a todo, not
resolved in this doc.

## Todos

- [ ] [CODE] P1. **Register the missing cefi options_chain candle SchemaContract(s)** in
      `unified-api-contracts/unified_api_contracts/internal/schemas/contracts.py::CONTRACT_REGISTRY` for
      `instrument_type="option"` (lowercase, matching the registry's convention) across the candle timeframe suffixes
      MDPS requests (`options_chain_15s`/`_1m`/`_5m`/`_15m`/`_1h`/`_4h`/`_24h`) — confirm which timeframes are genuinely
      needed vs already covered before adding all seven blindly. Add/extend
      `VENUE_CONTRACT_OVERRIDES[("cefi", "DERIBIT", "option", "options_chain_15s")]` instead of the generic registry
      entry if the schema needs to be DERIBIT-specific. (repo: unified-api-contracts)
- [ ] [DATA] P2. **Re-verify** by re-running MDPS `process --force` for `2023-08-10` (or any date with confirmed DERIBIT
      options_chain data) after the contract lands, confirming the per-date subprocess now exits 0 with no
      `SchemaContractNotFoundError` for `options_chain_15s`/DERIBIT/OPTION. (repo: market-data-processing-service)

## Progress Log

- **slot-24 (cicd/data_engineering) 2026-08-08T22:40Z**: Discovered while re-checking terminal-state gate on
  `mdps_force_flag_dropped_subprocess_per_date_2026_08_08.md` todo 2 (VM `mdps-backfill-cefi-20260808-095136` still
  RUNNING, not terminal — that todo remains gated, releasing back to queue per the same precedent slot-11/slot-15 set).
  Filed as a separate cross-cutting doc since this defect is unrelated to the `--force` forwarding bug and needs its own
  UAC-side fix.
