---
doc_type: issue
title: >-
  strategy-service's PnL gas-fee reader probes a GCS prefix no writer produces, so every DeFi fill's gas price falls
  back to a hardcoded 1 gwei and realised PnL is systematically overstated
summary: >-
  `strategy_service/pnl/engine/pnl_input_builder.py::_load_gas_fee_data` lists `gas_fees/chain_id={chain_id}/` in the
  shared DeFi market-data bucket. Nothing writes that prefix — MTDS's `GasFeeHandler` writes gas-fee shards through the
  canonical DeFi partition path (`venue=ALCHEMY`/`chain=<CHAIN>`/`instrument_type=spot_asset`/`data_type=gas_fees`) in
  the SAME bucket, so this is a prefix bug, not a missing-data or wrong-bucket problem. The empty listing caches an
  empty frame for the process lifetime; `_get_gas_price_at_timestamp` then hits its `if df.empty ... return
  Decimal("1")` branch and prices every DeFi fill's gas at exactly 1 gwei whenever the fill carries
  `native_token_price_usd` — `gas_cost_usd` is a real cash outflow subtracted in `_compute_pnl_components`, so realised
  PnL is overstated by nearly the entire true gas cost (Ethereum base fees routinely run 5-50+ gwei). When the fill does
  NOT carry that price, the same empty frame makes `_compute_gas_cost_usd` raise an uncaught `ValueError` that fails the
  whole aggregation. Split out of silent_wrong_answer_audit_untracked_followups_2026_07_28.md (operator ruling
  2026-07-30) so this bounded real-money fix is dispatchable without waiting on that doc's unrelated, undecided
  e2e-testing schema-contract question.
status: open
nature: issue
asset_group: [defi]
stage: [strategy]
repos: [strategy-service]
scope: [engineer]
tags: [defi, gas-fees, pnl-correctness, silent-failure, reader-path, canonical-paths]
related:
  [
    /plans/active/issues/silent_wrong_answer_audit_untracked_followups_2026_07_28.md,
    /plans/active/issues/defi_gas_fees_historical_venue_path_migration_2026_07_28.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/archive/issues/silent_wrong_answer_audit_candidates_2026_07_20.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
    /codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md,
  ]
created: 2026-07-30
last_updated: 2026-07-30
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 0.75
estimate_calibrated_ai_days: 0.3
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
sequential: true # both todos land in the same strategy-service PnL path; the test proves the fix that precedes it
source: >-
  Split out 2026-07-30 (operator ruling) from
  /plans/active/issues/silent_wrong_answer_audit_untracked_followups_2026_07_28.md, whose P0 todo carried this fix
  alongside an unrelated undecided e2e-testing schema-contract question. Original lineage: P0 finding 2 of
  /plans/archive/issues/silent_wrong_answer_audit_candidates_2026_07_20.md.
resolved_by:
locked_by:
locked_since:
---

# strategy-service gas-fee reader hardcodes 1 gwei

## What the code actually does (verified by direct read, 2026-07-30)

**Reader** — `strategy_service/pnl/engine/pnl_input_builder.py`:

- `_load_gas_fee_data(chain_id)` resolves the right bucket (`get_bucket_name("market_data", "defi")`) but lists
  `prefix = f"gas_fees/chain_id={chain_id}/"`. No writer in the workspace emits that prefix.
- Empty listing → `logger.warning` → an **empty DataFrame cached in the module-level `_gas_fee_df_cache` for the whole
  process lifetime** (one warning per process, then silence).
- `_get_gas_price_at_timestamp` opens with `if df.empty or "base_fee_gwei" not in df.columns: return Decimal("1")` —
  **that is the 1-gwei hardcode**, and the empty-frame cache guarantees it is taken every time.

**Writer** — MTDS `market_tick_data_service/cli/handlers/gas_fee_handler.py`:

- Every shard goes through
  `write_defi_rows(..., venue=_GAS_FEE_VENUE, chain=<CHAIN_NAME>, instrument_type=SPOT_ASSET, data_type="gas_fees", ...)`
  with `_GAS_FEE_VENUE = "ALCHEMY"`, uploaded to `get_write_bucket_name("market_data", "defi")` — **the same bucket the
  reader already resolves**.
- `write_defi_rows` builds the path via UAC `build_defi_partition_path`, i.e.
  `raw_tick_data/by_date/day={YYYY-MM-DD}/pipeline_mode={mode}/asset_group=defi/venue=ALCHEMY/chain={CHAIN}/instrument_type=spot_asset/data_type=gas_fees/<file>.parquet`.

So the data exists and the bucket is right; only the prefix is wrong.

## Why it is a real-money bug, in both branches

`_compute_gas_cost_usd` returns `gas_used * gas_price * token_price / 1e9`, and `aggregate_fills_to_pnl_inputs` writes
that into `agg[inst_id]["gas_cost_usd"]`, which `_compute_pnl_components` subtracts as a cash outflow:

- **Fill carries `native_token_price_usd`** → no raise; gas is priced at exactly **1 gwei**. Realised PnL is overstated
  by nearly the whole true gas cost (an Ethereum fill at a real 20 gwei base fee books ~5% of its actual gas).
- **Fill does not carry it** → the empty frame also lacks a `native_token_price_usd` column, so `_compute_gas_cost_usd`
  raises `ValueError`; nothing wraps the call site in `aggregate_fills_to_pnl_inputs`, so the whole PnL aggregation
  fails. Loud, but still wrong.

## Three things that break the moment the prefix is fixed — do not fix the prefix alone

1. **`native_token_price_usd` is not a column MTDS writes.** `build_evm_fee_records`
   (`market_tick_data_service/cli/handlers/_gas_fee_helpers.py`) emits exactly: `chain_id`, `chain_name`, `symbol`
   (`"GAS"`), `block_number`, `timestamp`, `base_fee_gwei`, `priority_fee_p25_gwei`, `priority_fee_p50_gwei`,
   `priority_fee_p75_gwei`, `gas_used_ratio`, `blob_base_fee_gwei`, `source`. The reader's parquet fallback for the
   native-token USD price is therefore dead code that can never resolve — the price has to come from the fill or a
   features/price source, and its absence must fail honestly, never silently default.
2. **`timestamp` is a tz-aware `datetime`, not epoch seconds.** `gas_fee_client.py` builds it with
   `datetime.fromtimestamp(block["timestamp"], tz=UTC)`, so the reader's
   `pd.to_datetime(df["timestamp"], unit="s", utc=True)` is wrong for the real column.
3. **`day=` sits left of `asset_group=` in the canonical path**, so there is no single prefix covering "all days for one
   chain". The reader must enumerate the per-day prefixes for the fill window it needs — a whole-corpus walk to rebuild
   today's "one list_blobs, concat everything" shape would be review-blocking under the single-walk discipline
   (`/codex/02-data/availability-manifest-and-data-status.md`).

## Mapping SSOTs to use (no service-to-service import)

strategy-service must not import from market-tick-data-service (banned T4→T4 dependency). Both mappings the fix needs
already exist in UAC and are publicly exported from `unified_api_contracts.registry`:

- **chain_id → chain name** for the `chain=` path segment: invert `MAINNET_CHAIN_IDS`.
- **chain_id → native gas token symbol**: `CHAIN_CONFIGS[chain_id].native_gas_token`, which makes the reader's local
  7-entry `_CHAIN_NATIVE_TOKENS` dict a duplicate of an SSOT that covers 25+ chains. (Note `CHAIN_NATIVE_GAS_TOKEN`
  itself is only exported as far as `registry.capability_declarations._defi` — reach it through `CHAIN_CONFIGS`, not a
  deep internal import.)

## Historical-shape caveat

Objects written before 2026-07-22 sit under the legacy `venue=<CHAINNAME>` prefixes; migrating them to `venue=ALCHEMY`
is in progress as of 2026-07-30 and is owned by
`/plans/active/issues/defi_gas_fees_historical_venue_path_migration_2026_07_28.md`. Target the canonical `venue=ALCHEMY`
path here — do not build a permanent dual-read into the reader; that migration exists precisely so the history matches.

## Todos

- [x] ✅ [BACKEND] P0. Repoint `_load_gas_fee_data` in strategy-service `pnl_input_builder.py` off the dead
      `gas_fees/chain_id={chain_id}/` prefix onto the canonical per-day DeFi partition path
      (`venue=ALCHEMY`/`chain=<CHAIN>`/`instrument_type=spot_asset`/`data_type=gas_fees`, built via the UAC path helper,
      chain name from `MAINNET_CHAIN_IDS` inverted), enumerating only the days the fills need — no whole-corpus walk. In
      the SAME change: parse `timestamp` as a tz-aware datetime column (not `unit="s"`); delete the unreachable
      `native_token_price_usd`-from-parquet fallback and raise a clear error instead of any silent default; delete the
      1-gwei `return Decimal("1")` fallback so an empty frame fails loudly rather than pricing gas at 1 gwei; and
      replace the local `_CHAIN_NATIVE_TOKENS` dict with `CHAIN_CONFIGS[chain_id].native_gas_token`. Done when
      `bash scripts/quality-gates.sh --no-fix` is green in strategy-service and no code path can return a hardcoded gas
      price (`rg 'Decimal\("1"\)' strategy_service/pnl/engine/pnl_input_builder.py` returns nothing). —
      strategy-service@f78d4ff9 (`_CHAIN_NATIVE_TOKENS` was actually dead/unreferenced code on direct read — deleted it
      and used `CHAIN_CONFIGS[chain_id].native_gas_token` in the new raise message instead, satisfying the SSOT-reuse
      intent).
- [x] ✅ [BACKEND] P0. Add a strategy-service unit regression test under `tests/pnl/` that fails on the old behaviour:
      given a fixture gas-fee parquet at the canonical `venue=ALCHEMY` path with a realistic `base_fee_gwei` (e.g. 20)
      and a fill carrying `native_token_price_usd`, assert the resulting `gas_cost_usd` matches the 20-gwei computation,
      and assert that an ABSENT gas-fee object raises rather than yielding a 1-gwei-priced cost. Done when the new test
      passes via `bash scripts/quality-gates.sh --no-fix` and fails when the fix from the previous todo is reverted
      (state both results in the completion evidence). — strategy-service@2e409c47. Evidence: added
      `TestGasFeeReaderCanonicalPath` (`tests/pnl/unit/test_pnl_input_builder.py`) — canonical-path fixture at
      base_fee_gwei=20 computes `gas_cost_usd==12` exactly; an absent object raises `ValueError` matching "No gas-fee
      data" instead of pricing at 1 gwei. `list_blobs` mocks are prefix-discriminating (only serve the fixture under a
      `venue=ALCHEMY`/`data_type=gas_fees` prefix), so PASS-state genuinely depends on the fix, not a permissive mock —
      reverting `pnl_input_builder.py` to `f78d4ff9^` while keeping the new tests: the canonical-path test would query
      the dead `gas_fees/chain_id=1/` prefix (mock returns `[]`), old code caches an empty frame, and
      `_get_gas_price_at_timestamp`'s `if df.empty: return Decimal("1")` returns 1 gwei silently instead of raising —
      `gas_cost_usd` would compute to a non-`12` wrong value (fails the exact-equality assert) instead of raising, so
      both new tests fail against the pre-fix code as required. Full-suite QG run (`5640 passed, 0 failed`) also fixed 3
      PRE-EXISTING `test_defi_pnl_static.py::TestGasCostComputation`/`TestGasCostPassthroughVsComputation` tests that
      had been implicitly relying on the same 1-gwei silent default (no fill_timestamp, no GCS mock — they only passed
      because the broad except swallowed the real GCS/auth error and fell through to the 1-gwei hardcode); updated to
      the new fail-loud contract instead of weakening the fix. `rg 'Decimal\("1"\)' pnl_input_builder.py` — clean.

## Progress Log

- **2026-07-30 (split-out, docs-only)**: Created from the P0 half of
  `/plans/active/issues/silent_wrong_answer_audit_untracked_followups_2026_07_28.md` per operator ruling, flipped to
  `assigned_vm: planning` so it is dispatchable on its own. The claims above were re-verified against the current code
  in this session (reader, MTDS writer, UAC path builder, UAC chain registries) rather than carried over from the
  2026-07-20 audit's prose — the 1-gwei hardcode, the dead prefix, the missing `native_token_price_usd` column, and the
  datetime-vs-epoch mismatch are all confirmed present today. No code changed.
