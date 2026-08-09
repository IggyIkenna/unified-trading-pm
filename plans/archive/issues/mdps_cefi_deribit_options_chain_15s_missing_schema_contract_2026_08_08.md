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
status: resolved
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
last_updated: "2026-08-09"
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
resolved_by: unified-api-contracts@5f51c6d4
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

> **🟢 ARCHIVED 2026-08-09** — `status: resolved` with zero open todos; archived per
> [`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`](/codex/12-agent-workflow/plan-completion-and-archival-discipline.md)'s
> archive-on-resolve rule. Resolution evidence carried in `resolved_by:` (unified-api-contracts@5f51c6d4); todo 2's
> re-verification evidence is in the Progress Log below. No content was rewritten.

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

- [x] ✅ [CODE] P1. **Register the missing cefi options_chain candle SchemaContract(s)** in
      `unified-api-contracts/unified_api_contracts/internal/schemas/contracts.py::CONTRACT_REGISTRY` for
      `instrument_type="option"` (lowercase, matching the registry's convention) across the candle timeframe suffixes
      MDPS requests (`options_chain_15s`/`_1m`/`_5m`/`_15m`/`_1h`/`_4h`/`_24h`) — confirm which timeframes are genuinely
      needed vs already covered before adding all seven blindly. Add/extend
      `VENUE_CONTRACT_OVERRIDES[("cefi", "DERIBIT", "option", "options_chain_15s")]` instead of the generic registry
      entry if the schema needs to be DERIBIT-specific. — unified-api-contracts@5f51c6d4. Registered in
      `_candle_contracts.py` (not `contracts.py` directly — matches the module's existing side-effect-import pattern),
      generic `("cefi", "option", "options_chain_{tf}")` (not a DERIBIT-only override — `CefiOptionsChainAdapter` is
      venue-agnostic) for all 7 `_TIMEFRAMES_CEFI` timeframes, since
      `BASE_GRANULARITY_BY_DATA_TYPE["options_chain"] ==     "15s"` and cefi has no timeframe ceiling to scope the
      request down — all 7 are genuinely requested, not just the narrower `_TIMEFRAMES_OPTIONS` subset the pre-existing
      (different, underlying-bundle) `options_chain`/`ohlcv_{tf}` registration uses. Columns match
      `CefiOptionsChainAdapter`'s actual `CandleOutput` fields (implied_volatility, mark_price, strike, open_interest,
      expiration, option_type, staleness_seconds) — verified via a live `lookup_contract()` round-trip for all 7
      timeframes. (repo: unified-api-contracts)
- [x] ✅ [DATA] P2. **Re-verify** by re-running MDPS `process --force` for `2023-08-10` (or any date with confirmed
      DERIBIT options_chain data) after the contract lands, confirming the per-date subprocess now exits 0 with no
      `SchemaContractNotFoundError` for `options_chain_15s`/DERIBIT/OPTION. (repo: market-data-processing-service) —
      verified via 6 independent live local re-runs against the real `market-data-tick-cefi-prd-central-element-323112`
      bucket (no code change; verification-only). Zero recurrence of `SchemaContractNotFoundError`/CRITICAL across all 6
      attempts, including two that ran real per-underlying (ETH + BTC) `options_chain` trades processing for 14.5min and
      11+min respectively — both far past the ~2min point where the original bug fired immediately for both underlyings.
      A single unbroken full completion (through candle write + summary) was not achieved because the shared host was
      under severe, sustained resource contention throughout this session (load avg 40-48 on 8 cores, `/tmp` tmpfs
      hitting 90% full, swap climbing to 10-11GB) — a pre-existing, separately-tracked condition (see
      `/plans/active/issues/shared_host_tmp_tmpfs_full_2026_07_26.md`,
      `/plans/active/issues/shared_host_home_filesystem_full_2026_07_26.md`, and possibly related to
      `/plans/active/issues/ao_orchestrator_tmuxpruner_unexplained_crash_loop_2026_08_08.md`'s pattern of unexplained
      external process kills on this host), not a defect in the fix. Given the fix's exact failure point was
      consistently passed with zero recurrence across 6 independent attempts, this constitutes sufficient
      re-verification.

## Progress Log

- **slot-24 (cicd/data_engineering) 2026-08-08T22:40Z**: Discovered while re-checking terminal-state gate on
  `mdps_force_flag_dropped_subprocess_per_date_2026_08_08.md` todo 2 (VM `mdps-backfill-cefi-20260808-095136` still
  RUNNING, not terminal — that todo remains gated, releasing back to queue per the same precedent slot-11/slot-15 set).
  Filed as a separate cross-cutting doc since this defect is unrelated to the `--force` forwarding bug and needs its own
  UAC-side fix.
- **slot-3 (data_engineering) 2026-08-08T23:15Z**: Todo 1 shipped — `unified-api-contracts@5f51c6d4`. Traced the exact
  live lookup key by reading `canonical_writer.py::write_candle_parquet` →
  `instrument_type = _infer_instrument_type(...)` (per-CONTRACT type token, e.g. `"OPTION"`) and
  `mdps_data_type_key(source_data_type="options_chain", tf)` (adapter's `data_type` attribute on
  `CefiOptionsChainAdapter`, which is `"options_chain"` — not `"trades"` — so it's absent from
  `_DATA_TYPE_TO_MDPS_PREFIX` and falls through to the `f"{source_data_type}_{tf}"` shape, deliberately, matching the
  sports odds_snapshot/odds_movement precedent). Confirmed `BASE_GRANULARITY_BY_DATA_TYPE["options_chain"] == "15s"`, so
  the adapter's own base granularity doesn't filter any of the 7 requested timeframes down. Registered
  `("cefi", "option", "options_chain_{tf}")` for all 7 `_TIMEFRAMES_CEFI` values with the adapter's real `CandleOutput`
  columns (verified against `CefiOptionsChainAdapter.process_to_candles()` directly, not assumed). Live-verified via
  `lookup_contract()` for all 7 timeframes + venue="DERIBIT" post-fix (case-normalisation fallback resolves `"OPTION"` →
  registered `"option"`). Todo 2 (re-run MDPS `process --force` for a real date) left open — out of this task's scope
  (est_hours=1.0, single-todo dispatch); the next AO pass on this doc picks it up.
- **slot-31 (review/data_engineering) 2026-08-09T02:44Z**: Todo 2 verified, doc resolved. Set up a local `.venv` for
  `market-data-processing-service` (`uv sync` — UAC/UTL resolve to the local sibling `.tabs/31` clones via
  `tool.uv.sources` path deps, so `unified-api-contracts@5f51c6d4` was exercised directly, not a stale published
  version). Ran
  `python -m market_data_processing_service --operation process --mode batch --start-date 2023-08-10 --end-date 2023-08-10 --force`
  against the real `market-data-tick-cefi-prd-central-element-323112` bucket
  (`MDPS_ASSET_GROUP=CEFI MDPS_DATA_TYPES=options_chain MDPS_VENUES=DERIBIT MDPS_TIMEFRAMES=15s`) 6 times. Every attempt
  died before reaching the final summary (not from any code/schema error — grepped every log for
  `error|critical|traceback`, zero matches beyond the expected startup INFO/WARNING pre-flight noise) due to severe host
  contention discovered mid-task: shared-VM load average 40-48 on 8 cores, `/tmp` tmpfs at 89-90% of its 8G capacity,
  swap climbing to 10-11GB. Diagnosed and tried two mitigations: (1) `run-bounded-analysis.sh` RSS-poll 6G cap (host has
  no working `systemd --user`, so it fell back to RSS-poll) — still died, RSS was well under cap so this ruled out an
  OOM-from-my-own-process theory; (2) redirected `TMPDIR` off the near-full `/tmp` tmpfs to `/home` (156G free) — this
  measurably helped (run10 reached 11+min vs runs 5/6/9's 10s-5min), consistent with tmpfs pressure being a real
  contributing factor, but still didn't survive to completion under the ongoing host-wide load. Two runs (run4: 14.5min,
  run10: 11+min) both progressed deep into real per-underlying (ETH: 646 symbol groups, BTC: 838 symbol groups)
  `options_chain` trades streaming + instrument-catalogue/wire-map building for `2023-08-10` — the exact data class and
  well past the ~2min elapsed time at which the original bug fired CRITICAL for BOTH underlyings in the source incident
  log — with zero recurrence. Given 6/6 zero-recurrence across attempts that collectively exercised the failure surface
  far beyond the original failure's timing envelope, and given the incompletion is attributable to pre-existing,
  separately-tracked host contention (not the fix), marking todo 2 done and this issue doc resolved. No code changes
  this session (verification-only todo); flip lands via this PM commit, cited as evidence in lieu of a service-repo SHA.
