---
doc_type: issue
title:
  "dex_pool_state: 33 build_instrument_id errors — root cause is `:` in pool symbol triggering UAC colon-delimiter check"
summary: >
  Investigation of dex_pool_state's build_instrument_id errors. Root cause: some pool symbols contain `:` (the canonical
  ID's own VENUE:TYPE:SYMBOL delimiter), triggering a hard ValueError in `build_instrument_id`. 33 rows across 4
  venue+chain pairs.
status: resolved
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [defi, dex-pools, instrument-id, build-instrument-id, colon-in-symbol, manifest-hygiene]
related:
  [
    mvp_backfill_defi_onchain_v10_2026_06_27,
    defi_dex_pool_swaps_733_row_indexer_health_findings_2026_07_27,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-08-04
parent_epic: defi_master
priority: P2
author: slot-5 (data_engineering)
assigned_vm: planning
source: [mvp_backfill_defi_onchain_v10-005]
locked_by: ""
resolved_by: "slot-15, 2026-08-15 (archival) — fix + rerun shipped market-tick-data-service@badbcbde, 2026-08-05"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
context_scope:
  [
    unified-api-contracts/unified_api_contracts/internal/reference/canonical_id_builder.py,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/defi/canonical_write.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/_defi_manifest.py,
    /plans/active/issues/canonical_path_oracle_blind_to_filename_stem_2026_07_20.md,
  ]
---

> **🟢 ARCHIVED 2026-08-15** — status=resolved, archived per `/codex/11-project-management/issue-doc-lifecycle.md`'s
> ACKED-INTO-CODE rule. Both todos shipped: per-row `build_instrument_id` failure isolation
> (`market-tick-data-service@badbcbde`) and the 33-shard re-run recovering all blocked pool data (`ok=31 fail=0`, base
> index verified clean of `attempted_failed`/`build_instrument_id` rows).

## What I found

**33 `attempted_failed` rows** in the defi availability manifest for `data_type=dex_pool_state` with
`error_reason="build_instrument_id"` (the plan cited 19 — count has grown). All have `instrument_id=None` and
`instrument_type=None`. Each row represents a FULL shard failure (one protocol+chain+date), not an individual pool
failure — because `write_defi_rows` iterates all pools in the shard and raises on the first `build_instrument_id`
failure, aborting the entire shard.

**Affected venue+chain pairs:**

| venue         | chain     | count | date range             |
| ------------- | --------- | ----- | ---------------------- |
| SUSHISWAP     | ARBITRUM  | 10    | 2021-09-15..2023-02-18 |
| TRADER_JOE_V2 | AVALANCHE | 5     | 2021-11-26..2022-01-12 |
| UNISWAP_V4    | ETHEREUM  | 17    | 2025-04-02..2026-07-09 |
| ORCA          | SOLANA    | 1     | 2026-07-22             |

## Why it matters

**Root cause confirmed**: `build_instrument_id` (UAC `canonical_id_builder.py:851`) raises `ValueError` when the symbol
contains `:` — the canonical ID's own `VENUE:TYPE:SYMBOL` delimiter. This is a hard loud-fail (operator ruling
2026-07-20, `canonical_path_oracle_blind_to_filename_stem_2026_07_20.md` §7 — "remove the silent fallback that mints
double-wrapped ids").

**Error propagation chain**:

1. `resolve_pool_symbol()` produces a symbol containing `:` (from subgraph token metadata, or catalogue, or the fallback
   pool address — most likely the subgraph's `token0.symbol`/`token1.symbol` fields for certain pools)
2. `canonical_write.py:327`: `build_instrument_id(v, instrument_type, symbol, chain=c)` raises `ValueError`
3. `write_defi_rows` aborts the entire shard (all pools for that protocol+chain+date)
4. Exception propagates to `apply_dex_pools_shard_results` → `recorder.record_failed(error=value)`
5. `_defi_manifest.py:461`: `code_token = raw_message.split(":", 1)[0]` → `"build_instrument_id"`
6. Manifest row written as `attempted_failed` with `error_reason="build_instrument_id"`

**Only the colon-in-symbol check produces this exact error token.** All other `build_instrument_id` error messages (e.g.
`"POOL requires a non-empty symbol"`, `"Unsupported instrument_type"`) would produce different `code_token` values.
Confirmed by code review of every `ValueError` raise site in `canonical_id_builder.py`.

The colon check was added 2026-07-20 as a loud-fail guard against the CeFi double-wrapped-id bug
(`BITFINEX-FUTURES:PERPETUAL:ADAF0:USTF0`). DeFi pool symbols hitting it is the same bug class in a different asset
group — a symbol with `:` reaching the builder without prior resolution.

**UNISWAP_V4/ETHEREUM is the largest bucket (17 rows) and the most recent** (through 2026-07-09). The subgraph itself is
healthy (confirmed by live probe in
`/plans/archive/2026_08/issues/defi_dex_pool_swaps_733_row_indexer_health_findings_2026_07_27.md`, archived 2026-08-09),
so this is NOT a subgraph-availability issue — it's a symbol-resolution issue in the MTDS handler.

## Recommended decision

**Fix in `resolve_pool_symbol` or in the caller** — sanitise the symbol before passing it to `build_instrument_id`.
Options:

- **(A) Sanitise in `resolve_pool_symbol`**: Strip/replace `:` from token symbols before building the pool symbol.
  Low-risk but could mask upstream data quality issues.
- **(B) Catch and handle in `_collect_protocol_chain`/`_collect_solana_dex`**: Before calling `write_defi_rows`,
  validate each row's symbol and skip/flag pools whose symbols contain `:`. More surgical — only the problematic pools
  are skipped instead of the entire shard failing.
- **(C) Handle in `write_defi_rows`**: Catch `ValueError` from `build_instrument_id` per-row instead of failing the
  entire batch. This is the most robust fix — a single malformed pool shouldn't block every other pool in the shard.

**Recommendation: (C)** — per-row failure isolation in `write_defi_rows` is the correct architectural fix. The current
all-or-nothing behavior means one malformed pool symbol blocks the entire protocol+chain+date shard. Each individual
`build_instrument_id` failure should be recorded as `attempted_failed` for that specific pool (with the full error
details preserved), while other pools in the same shard succeed normally.

- [x] ✅ [DATA] P1. Per-row `build_instrument_id` failure isolation in `write_defi_rows` — catch ValueError per-row
      instead of aborting the entire batch, so one malformed pool symbol doesn't block the whole protocol+chain+date
      shard. Repo: `market-tick-data-service`. — market-tick-data-service@badbcbde
- [x] ✅ [SCRIPT] P2. Re-run the 33 failing shard-dates after the fix to recover the blocked pool data. Repo:
      `market-tick-data-service`. — batch re-run `ok=31 fail=0` (`/tmp/rerun_dex_32.log`, all `RESULT … OK`); per-shard
      row counts sushiswap (87,80,262,339,302,407,469,588 + 2021-09-15=238 probe), trader_joe_v2 (412,538,624,570,565),
      uniswap_v4 (50,56,76,106,109,106,111,110,103,106,112,117,135,136,130,135,133,128); ORCA 2026-07-22 already
      honestly `empty_confirmed SOURCE_RETURNED_ZERO` (forward-only RPC, no write needed). Stale all-blank coarse
      `attempted_failed` rows overwritten via `DefiManifestRecorder.record_captured` (all-blank key,
      `batch_onchain_subgraph`, source=onchain_subgraph) — 32 captured overwrites absorbed by the consolidator.
      Verified: base index clean of `attempted_failed` (updated 2026-08-05T00:37:50); reader census
      `remaining attempted_failed build_instrument_id dex_pool_state rows: 0`.

- **context-scout 2026-08-06**: populated context_scope (4 entries). No "## Progress Log" section existed in this doc;
  appended as a new final section instead.
