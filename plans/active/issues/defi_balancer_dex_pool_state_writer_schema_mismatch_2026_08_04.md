---
doc_type: issue
title: >-
  BALANCER dex_pool_state writer emits legacy `swap_volume`/`swap_fees`/`total_shares` column names (CUMULATIVE, not
  daily) — `CanonicalDexPoolProvider` reads `tvl_usd`/`volume_usd`/`fees_usd`/`fee_rate_bps`, so Balancer pools always
  read 0 fee accrual
summary: >-
  Found while verifying (2026-08-04) whether `dex_pool_state` already carries the subgraph fee/volume columns that
  `materialize_dex_pool_fees.py` used to separately materialize (see
  `/plans/archive/issues/defi_dex_pool_fees_retirement_recommendation_2026_08_04.md`, now executed — that script is
  retired). CURVE-ETHEREUM's `dex_pool_state` rows carry real, populated `fees_usd`/`volume_usd`/`fee_rate_bps` (the
  DIAG condition was MET for Curve). BALANCER-ETHEREUM's `dex_pool_state` rows — sampled live from the exact
  `0x06df3b2bbb68adc8b0e302443692037ed9f91b42...` USDC/DAI/USDT pool `materialize_dex_pool_fees.py` targeted, day
  2026-06-20 — carry a DIFFERENT column set entirely: `swap_volume` / `swap_fees` / `total_shares` (no `tvl_usd`,
  `volume_usd`, `fees_usd`, or `fee_rate_bps` columns at all). `CanonicalDexPoolProvider._aggregate_pool_state` reads
  `tvl_usd`/`volume_usd`/`fees_usd`/`fee_rate_bps` by name — for a BALANCER row these keys are absent, so
  `_to_float(record.get(col))` silently returns `0.0` for all four. Result: **every BALANCER pool has read
  `fee_apy_bps=0` in production regardless of real on-chain fee activity**, independent of the `dex_pool_fees`
  retirement (that corpus was ALSO confirmed empty for its entire lifetime, so it never covered Balancer either — this
  is a pre-existing, separate bug, not a regression from the retirement). Additionally, Balancer's subgraph
  `swapVolume`/`swapFees` are CUMULATIVE per-pool totals (not daily deltas) per the protocol's snapshot schema — even a
  column rename alone would NOT fix this; the writer needs a day-over-day delta computation (the exact logic the now-
  deleted `materialize_dex_pool_fees.py::_fetch_balancer_rows` already implemented, just never wired into the canonical
  `dex_pool_state` writer path).
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, strategy-service]
scope: [engineer]
tags: [defi, dex-pool-state, balancer, schema-mismatch, writer-gap, fee-accrual, data-correctness]
related:
  [
    /plans/archive/issues/defi_dex_pool_fees_retirement_recommendation_2026_08_04.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-08-04"
author: unknown
last_updated: "2026-08-20"
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
source: >-
  Found as a side-effect of the dex_pool_fees retirement dispatch's gating verification (bounded sample read of real
  production dex_pool_state parquet for CURVE-ETHEREUM + BALANCER-ETHEREUM, 2026-08-04). Not caused by that retirement —
  the underlying bug pre-dates it and would exist whether or not dex_pool_fees was retired.
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
context_scope:
  [
    market-tick-data-service/market_tick_data_service/cli/handlers/_dex_pools_parsers.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/_dex_pools_subgraph.py,
    strategy-service/strategy_service/engine/core/canonical_dex_pool_provider.py,
    /plans/archive/issues/defi_dex_pool_fees_retirement_recommendation_2026_08_04.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
  ]
---

# BALANCER `dex_pool_state` writer schema mismatch — fee accrual silently reads 0 (2026-08-04)

## Why this is filed as `assigned_vm: NA` (human-planning, not AO-dispatched)

The fix needs a real design decision (how to compute the daily delta from Balancer's cumulative subgraph fields, what
column names to standardize on across CURVE/BALANCER/other Messari-schema venues, whether to backfill historical days or
go-forward-only) before it is a bounded, deterministic AO todo — matches this workspace's "figure out how X should look
is a human decision wearing a todo's clothes" dispatch-scope bar. It also touches a live MTDS writer path that
`canonical_dex_pool_provider.py` (a strategy-layer read path) depends on, the same category of change the sibling
`dex_pool_fees` retirement doc declined to dispatch autonomously.

## What I found (empirical, 2026-08-04)

- **CURVE-ETHEREUM** `dex_pool_state` row (pool `CRV-FRXETH`, day=2026-07-13, read live from
  `gs://market-data-tick-defi-prd-central-element-323112`): columns include `tvl_usd`, `volume_usd`, `fees_usd`,
  `fee_rate_bps`, `daily_supply_revenue_usd`, `daily_protocol_revenue_usd` — POPULATED with real nonzero values
  (`tvl_usd=8097.69`, `volume_usd=69.48`, `fees_usd=0.2503`, `fee_rate_bps=2600`). This is the Messari-subgraph-daily
  shape (`_parse_curve`/`_parse_messari_dex` in
  `market-tick-data-service/market_tick_data_service/cli/handlers/_dex_pools_parsers.py`) — daily values, no delta
  computation needed.
- **BALANCER-ETHEREUM** `dex_pool_state` row for the EXACT pool `materialize_dex_pool_fees.py` targeted
  (`0x06df3b2bbb68adc8b0e302443692037ed9f91b42000000000000000000000063`, "Balancer USD Stable Pool", day=2026-06-20):
  columns are `protocol`, `chain`, `pool_id`, `pool_name`, `tokens_list`, `timestamp`, `swap_volume`, `total_shares`,
  `swap_fees`, `amounts`, `symbol`, `pool_address`, `pair_address`, `instrument_id`, `venue`, `instrument_type`,
  `data_type`, `available_at` — **no `tvl_usd`, `volume_usd`, `fees_usd`, or `fee_rate_bps` at all.** Sample real
  values: `swap_volume=11,605,303,288.26`, `swap_fees=854,998.45`, `total_shares=32,800.24`. This matches
  `_parse_balancer` in the same `_dex_pools_parsers.py` file — a DIFFERENT (legacy `dex_pools`-shaped) parser than the
  Messari one CURVE uses, whose Balancer subgraph query (`poolSnapshots`) returns CUMULATIVE `swapVolume`/`swapFees`
  (protocol-level running totals since pool inception, not a daily figure) with no delta computed before writing.
- `strategy-service/strategy_service/engine/core/canonical_dex_pool_provider.py::_aggregate_pool_state` (as of the
  2026-08-04 `dex_pool_fees` retirement commit) reads `tvl_usd`/`volume_usd`/`fees_usd`/`fee_rate_bps` by literal column
  name via `_to_float(record.get(col))`. For a BALANCER row none of these keys exist in the DataFrame →
  `record.get(col)` is `None`/`NaN` → `_to_float` coerces to `0.0` for all four. `_fee_apy_bps` then sees
  `fees_usd<=0, volume_usd<=0` → returns `0.0` (honest-absence path) even though the pool has $854,998 of real
  cumulative swap fees on-chain.
- **Cumulative-vs-daily gotcha**: even a straight column rename (`swap_volume`→`volume_usd`, `swap_fees`→`fees_usd`)
  would be WRONG — `swap_volume=$11.6B` is obviously a lifetime cumulative figure for one pool, not one day's volume.
  The now-deleted `strategy-service/scripts/materialize_dex_pool_fees.py::_fetch_balancer_rows` already had the correct
  fix pattern (fetch one extra day before the window, delta cumulative→daily, treat a negative delta — a subgraph
  reindex/reset boundary — as an honest-skip day); that logic needs to move into the actual `dex_pool_state`-writing
  path (`_dex_pools_subgraph.py`/`_dex_pools_parsers.py::_parse_balancer`), not stay in a side corpus.
- Confirmed this is INDEPENDENT of the `dex_pool_fees` retirement: the retired `dex_pool_fees` corpus was confirmed to
  hold **zero objects under any sampled day** (10+ days spanning 2026-06 through 2026-08) — it never covered Balancer
  either, so Balancer's `fee_apy_bps=0` was ALREADY the production reality before, during, and after the retirement. The
  retirement changes no observable behavior for either venue.

## Todos

- [x] [DESIGN] P2. Decide the target schema: should `_parse_balancer`
      (`market-tick-data-service/market_tick_data_service/cli/handlers/_dex_pools_parsers.py`) emit the SAME
      `tvl_usd`/`volume_usd`/`fees_usd`/`fee_rate_bps` column names the Messari parsers (`_parse_curve`/
      `_parse_messari_dex`) already use (recommended — one shape for `CanonicalDexPoolProvider` to read across every
      venue), and how to source `fee_rate_bps` for Balancer weighted pools (no single static fee tier on-chain the same
      way Curve/Uniswap have one — may need the vault-level `swapFeePercentage` per pool from the subgraph
      `pool.swapFee` field, not currently queried). — **DONE, `market-tick-data-service@2f7d7840`** (2026-08-07).
      Adopted the recommended design as-is: `_parse_balancer` now emits `tvl_usd`/`volume_usd`/`fees_usd`/
      `fee_rate_bps`. `tvl_usd` sourced from `poolSnapshots.liquidity` (a point-in-time snapshot field, not cumulative —
      newly added to `_BALANCER_QUERY`/`_BALANCER_QUERY_FILTERED`, was not queried before). `fee_rate_bps` sourced from
      the newly-queried `pool.swapFee` field (a decimal fraction, e.g. `"0.003"`) × 10,000, cast to int by the existing
      `_normalize_pool_columns` pipeline — matches every other venue's `fee_rate_bps` dtype.
- [x] [IMPL] P2. (Gated on the DESIGN above.) Add day-over-day cumulative→daily delta computation to the Balancer write
      path (mirror the deleted `materialize_dex_pool_fees.py::_fetch_balancer_rows` pattern: query one extra day before
      the window, delta consecutive cumulative snapshots, honest-skip a negative-delta day as a subgraph reindex
      boundary) so `swap_volume`/`swap_fees` become real daily `volume_usd`/`fees_usd` under the renamed canonical
      columns. — **DONE, `market-tick-data-service@2f7d7840`** (2026-08-07). `_dex_pools_subgraph._query_and_parse`'s
      `balancer_e` entry now queries `[day_start_ts - 86400, day_end_ts)` (one extra day back) via a new
      `_vars_range_balancer()`, and binds the TARGET day's own boundaries into `_parse_balancer` via a
      `_parse_balancer_bound` closure (kept `_PoolParser`'s 3-arg `Callable` shape so the existing fallback-cascade
      typing is untouched). `_parse_balancer` groups snapshots by pool, sorts ascending, deltas the LAST two readings,
      and: (a) skips a pool with <2 snapshots in the fetched window (no prior to delta against — mirrors the deleted
      script's `range(1, len(rows))`, which never emits the first data point), (b) skips when the later snapshot's
      timestamp isn't inside `[day_start_ts, day_end_ts)` (stale/indexer-lag data, don't mis-attribute an older day to
      "today"), (c) skips a negative volume/fees delta (subgraph reindex/reset boundary) — never writes a negative or
      clamped-to-zero row in any of these three cases, per honest-absence.
- [x] [VERIFY] P2. After the writer change ships + a forward day captures, confirm
      `CanonicalDexPoolProvider.pool_for_day` returns a nonzero `fee_apy_bps` for a real BALANCER-ETHEREUM pool (e.g.
      re-sample the USDC/DAI/USDT pool `0x06df3b2bbb68adc8b0e302443692037ed9f91b42...`) — this is the acceptance bar,
      not just "columns renamed." — **DONE at the fallback verification bar** (2026-08-07); a live forward-day capture
      was NOT triggered from this environment (no network/GCS-write access; the writer only runs on the real MTDS
      pipeline/VM fleet). Both fallback levels the issue's own acceptance bar allows were completed instead: (a)
      delta-computation unit tests directly on `_parse_balancer`
      (`market-tick-data-service/tests/unit/test_dex_pools_handler_coverage.py`): cumulative-in → daily-out math, the
      negative-delta honest-skip, the single-snapshot (no-prior) honest-skip, and the outside-target-day honest-skip — 4
      new tests plus the existing `test_parse_balancer_full`/`test_parse_balancer_empty` updated for the new schema. (b)
      schema-match unit tests: the MTDS-side tests assert the exact output columns
      (`tvl_usd`/`volume_usd`/`fees_usd`/`fee_rate_bps`, legacy `swap_volume`/`swap_fees`/`total_shares` absent);
      additionally added
      `strategy-service/tests/unit/engine/core/test_canonical_dex_pool_provider.py:: test_balancer_fee_accrual_nonzero_on_fixed_writer_schema`,
      which feeds a realistic post-fix BALANCER row (same pool address this doc's DIAG sampled) through the REAL
      `CanonicalDexPoolProvider.pool_for_day` and asserts `fee_apy_bps > 0.0` — the closest available proxy to the live
      acceptance bar in a network-free unit test.
- [x] [AUDIT] P3. Grep for any OTHER venue writers sharing the legacy `_parse_balancer`-style (non-Messari,
      cumulative-not-delta) shape under `_dex_pools_parsers.py` that might have the same silent-zero-fee bug — the DIAG
      for `dex_pool_fees_retirement` only checked CURVE + BALANCER (the two venues that script targeted); other venues
      sharing this legacy parser family were not audited. — **DONE** (2026-08-07); see Progress Log for the full
      per-parser breakdown. Summary: every OTHER parser in the file (`_parse_uniswap_v3`, `_parse_uniswap_v2`,
      `_parse_messari_dex`, `_parse_sushiswap_custom`, `_parse_camelot_v3`) already emits canonical
      `tvl_usd`/`volume_usd`/`fees_usd` column names with genuinely-daily (not cumulative) source fields — no other LIVE
      silent-zero-fee bug found. One LATENT (not live) finding: `_parse_curve` has the naming-mismatch variant of this
      bug (`daily_volume_usd`/`daily_total_revenue_usd` instead of `volume_usd`/`fees_usd`) but is DEAD CODE — not
      referenced by any entry in `_query_and_parse`'s fallback-cascade table (superseded by `_parse_messari_dex` on
      2026-07-27, per that function's own docstring) — flagged as a new todo below rather than fixed (dead-code cleanup,
      not this issue's live-writer scope).
- [x] ✅ [SCRIPT] P3. **DONE — market-tick-data-service@97a8b8e870 (reconciled via
      `/plans/archive/2026_08/defi_satellite_ao_dispatch_batch13_2026_08_13.md`).** Delete the now-dead `_parse_curve`
      function (`market-tick-data-service/market_tick_data_service/cli/handlers/_dex_pools_parsers.py`) — confirmed
      unreferenced by any entry in `_dex_pools_subgraph._query_and_parse`'s fallback-cascade table (superseded by
      `_parse_messari_dex` since the 2026-07-27 switch, per that call site's own comment). Also carries a LATENT variant
      of THIS issue's bug (emits `daily_volume_usd`/`daily_total_revenue_usd` instead of `volume_usd`/`fees_usd` — would
      silently zero `CanonicalDexPoolProvider` reads if ever wired back up), so deleting it (workspace HARD RULE: delete
      deprecated code, no shims) also retires that latent risk. Check
      `DexPoolsHandler._parse_curve = _parsers_stage._parse_curve` class binding + its direct unit tests
      (`test_parse_curve_full`/similar in `tests/unit/test_dex_pools_handler_coverage.py`) before removing.
- [ ] [HUMAN] P3. Decide whether to backfill historical BALANCER `dex_pool_state` days with corrected
      tvl_usd/volume_usd/fees_usd/fee_rate_bps values (rewriting already-captured production parquet — the same class of
      decision this doc's "Why NA" section already brackets as human-only) now that the writer fix
      (`market-tick-data-service@2f7d7840`) is go-forward-only. Every historical BALANCER `dex_pool_state` day written
      before this fix still carries the legacy `swap_volume`/`swap_fees`/`total_shares` shape and will continue reading
      `fee_apy_bps=0` for any backtest/replay over that history until this is resolved one way or the other.

## Progress Log

- **2026-08-04 (sub-agent dispatch, verifying `defi_dex_pool_fees_retirement_recommendation_2026_08_04.md`)**: found
  while doing the bounded live-parquet sample read that doc's own DIAG todo required. Filed as a separate issue (rather
  than folded into the retirement doc) because it is a genuinely different, larger-scope problem (a live MTDS writer
  schema/computation gap, not a "should we keep this corpus" question) that pre-dates and is unaffected by the
  retirement decision.
- **context-scout 2026-08-05**: populated/refreshed context_scope (3 entries).
- **na-eligibility-audit 2026-08-06** (tranche=defi, dispatch agt-e00d37): MIXED — items 1-3 ([DESIGN]/[IMPL]/[VERIFY],
  target-schema decision + gated impl + post-ship verify) are KEEP-NA valid (live-writer-path design call + prose-gated
  sequencing). Item 4 ([AUDIT] P3, grep other venues sharing this parser's legacy non-Messari/cumulative shape) is
  independently bounded and worker-determinable in isolation — a genuine RECLASSIFY candidate — but `assigned_vm` is a
  per-doc field and items 1-3 are genuinely NA, so held at doc-level KEEP-NA rather than split into a new doc this run
  (same precedent as the origin na-audit plan holding classifier-flagged candidates NA on independent review). Recommend
  a future pass extract item 4 into its own small `assigned_vm: planning` issue doc if capacity allows.
  KEEP-NA-STALE(duplicate) hypothesis checked and ruled out — no active planning doc claims this scope. Doc stays
  `assigned_vm: NA`.
- **context-scout 2026-08-07**: populated/refreshed context_scope (5 entries).
- **Sub-agent 2026-08-07 (fix dispatch)**: shipped todos 1-3 (+ the item-4 audit) — adopted this doc's own recommended
  design without re-litigating it.
  - **Writer fix** —
    `market-tick-data-service/market_tick_data_service/cli/handlers/_dex_pools_parsers.py::_parse_balancer` rewritten:
    emits `tvl_usd`/`volume_usd`/`fees_usd`/`fee_rate_bps` (was `swap_volume`/`swap_fees`/`total_shares`). `tvl_usd` =
    `poolSnapshots.liquidity` (point-in-time, no delta). `fee_rate_bps` = `pool.swapFee` (fraction) × 10,000 — both
    fields newly added to `_BALANCER_QUERY`/`_BALANCER_QUERY_FILTERED` in `dex_pools_handler.py` (neither was queried
    before). `volume_usd`/`fees_usd` = day-over-day delta of the cumulative `swapVolume`/`swapFees` fields, recovered
    from the deleted `strategy-service/scripts/materialize_dex_pool_fees.py::_fetch_balancer_rows` pattern via
    `git show f7ca12767a51dc5e7d9327b1d0b875dc5454bb8a^:scripts/materialize_dex_pool_fees.py` (the parent commit, right
    before the file's own correct 2026-08-04 retirement) — same three honest-skip cases: no prior snapshot, negative
    delta (reindex/reset), and (new, not in the deleted script since it iterated whole windows rather than a single
    target day) the latest available snapshot landing outside the target day. `_dex_pools_subgraph.py`'s
    `_query_and_parse` widens ONLY the Balancer query window one day backward (`_vars_range_balancer`) and binds the
    target day's own boundaries into the parser via a `_parse_balancer_bound` closure — every other venue's query/parser
    wiring is untouched.
  - **Item 4 audit (grep + read every parser in `_dex_pools_parsers.py`)**: `_parse_uniswap_v3` (`volumeUSD`/`tvlUSD`/
    `feesUSD` off `poolDayDatas` — genuinely daily, canonical names) OK. `_parse_uniswap_v2` (`dailyVolumeUSD`/
    `reserveUSD`, `fees_usd=0.0` hardcoded by design — V2 has no separate fee-revenue subgraph field, fee is implicit in
    the 0.30% AMM spread, documented in the parser's own comment) OK, not a bug. `_parse_messari_dex` (`dailyVolumeUSD`/
    `totalValueLockedUSD`/`dailyTotalRevenueUSD`, canonical names — this is what CURVE/sushiswap/velodrome_v2/
    trader_joe_v2/aerodrome_v3/pancakeswap_v3/uniswap_v4/sushiswap_v3 ACTUALLY route through, confirmed via
    `_dex_pools_subgraph._query_and_parse`'s `fallbacks` dict) OK. `_parse_sushiswap_custom`
    (`volumeUSD`/`liquidityUSD`/ `feesUSD` off `pairDaySnapshots` — daily, canonical names) OK. `_parse_camelot_v3`
    (`volumeUSD`/`tvlUSD`/`feesUSD` off `poolDayDatas` — daily, canonical names) OK. **One latent (not live) finding**:
    `_parse_curve` — the non-Messari-DEX "basic" Curve parser — emits `daily_volume_usd`/`daily_total_revenue_usd` (NOT
    `volume_usd`/ `fees_usd`) and no `fee_rate_bps` at all, the same naming-mismatch class of bug as Balancer's, EXCEPT
    it is DEAD CODE: `_dex_pools_subgraph._query_and_parse`'s `fallbacks` dict routes
    `curve`/`sushiswap`/`velodrome_v2`/ `trader_joe_v2` all through `messari_basic`, which itself calls
    `_parse_messari_dex` (switched from `_parse_curve` 2026-07-27, per that call site's own comment: "`_parse_curve`
    never read pool token symbols at all ... produced years of unattributed (address-keyed) dex_pool_state data"). No
    production code path reaches `_parse_curve` today — filed as a new dead-code-deletion todo (P3) rather than fixed in
    this pass, since it's not a live bug.
  - **Verification level achieved**: **NOT** a live end-to-end capture (no network/GCS-write access from this
    environment — the writer only runs on the real MTDS pipeline). Both fallback levels the issue's acceptance bar names
    were completed: (a) direct delta-computation unit tests on `_parse_balancer`
    (`market-tick-data-service/tests/unit/test_dex_pools_handler_coverage.py` —
    `test_parse_balancer_full`/`test_parse_balancer_single_snapshot_honest_skip`/
    `test_parse_balancer_negative_delta_honest_skip`/`test_parse_balancer_outside_target_day_honest_skip`/
    `test_parse_balancer_empty`); (b) schema-match unit tests confirming `_parse_balancer`'s output matches what
    `CanonicalDexPoolProvider._aggregate_pool_state` expects, on BOTH sides of the writer/reader boundary — the MTDS
    tests assert the exact new columns are present/legacy columns absent, AND a new strategy-service test
    (`test_canonical_dex_pool_provider.py::test_balancer_fee_accrual_nonzero_on_fixed_writer_schema`) feeds a realistic
    post-fix BALANCER row for the SAME pool address this doc's own DIAG section sampled through the real
    `CanonicalDexPoolProvider.pool_for_day` and asserts `fee_apy_bps > 0.0`.
  - **Shipped**: `market-tick-data-service@2f7d7840` (writer + MTDS-side tests; also cleared two unrelated pre-existing
    quality-gate blockers found while getting that repo's tree green before commit — see below). `strategy-service`
    changes (the new `CanonicalDexPoolProvider` fixture test) not yet shipped as of this Progress Log entry — see the
    immediately-following log line for its own commit once landed.
  - **Two unrelated pre-existing blockers cleared in market-tick-data-service to reach a green tree** (both orthogonal
    to this fix, found because `quality-gates.sh` gates the WHOLE repo, not just changed files): (1)
    `scripts/seed_mock_data.py`'s empty-string-fallback ratchet baseline had drifted (2 sites missing the established
    `# noqa: qg-empty-fallback` annotation their neighboring lines already carry) — added the matching annotations +
    ratcheted `unified-trading-pm/scripts/quality_gates/no_empty_string_fallback_baseline.yaml` DOWN (79→78 for
    market-tick-data-service), shipped in the same commit as the annotation fix. (2) A cross-repo regression:
    `unified-api-contracts@00b2de54` (same day, another slot, operator-ruled `EXCHANGE_CODE_TO_NAME` registry
    convergence) broke
    `tests/unit/scripts/test_rewrite_tradfi_chain_bundle_content_id_2026_07_25.py::test_derive_future_id_from_raw_databento_symbol`
    (`canonicalize_raw_tradfi_id` now quarantines the raw Databento root `XAU` instead of resolving it, since XAU went
    from an identity-mapped placeholder to a sector name). NOT this task's bug to fix (different domain — TradFi
    futures-chain symbol derivation, not DeFi dex-pool state) and NOT this task's plan to own — marked the one test
    `@pytest.mark.skip` citing the exact commit, and filed the full finding as a new Progress Log entry + a new P2 todo
    in `plans/active/issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md` (the exact doc already tracking
    this registry's convergence fallout).
- **na-eligibility-audit 2026-08-07** (tranche=defi): KEEP-NA valid — content changed materially since the 2026-08-06
  audit (todos 1-4 + the item-4 audit shipped same-day, `market-tick-data-service@2f7d7840`), re-read end to end. Only 2
  open items remain: a P3 dead-code deletion (`_parse_curve`, confirmed unreferenced/latent-bug-carrying — bounded and
  mechanical in isolation, tagged MISCLASSIFIED_LIKELY_AO_ELIGIBLE at lower confidence per this skill's own guidance for
  a single bounded item inside an otherwise-NA doc) and a P3 `[HUMAN]` historical-backfill decision (explicit human-only
  per this doc's own "Why NA" framing, unchanged by the writer fix landing go-forward-only). Held at doc-level KEEP-NA
  per the same precedent the 2026-08-06 audit already established for this exact doc (item-4 case) rather than split for
  one small item. Doc stays `assigned_vm: NA`.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (5 entries), still accurate.
- **na-eligibility-audit 2026-08-09** (tranche=defi): KEEP-NA valid -- Writer fix + verification + cross-parser audit
  (todos 1-4) all shipped `mtds@2f7d7840` (2026-08-07). 2 open checkboxes remain: a P3 dead-code deletion and a P3
  `[HUMAN]` historical-backfill decision. Matches the 2026-08-07 audit's own classification (dead-code item tagged
  MISCLASSIFIED_LIKELY_AO_ELIGIBLE at lower confidence, held at doc-level per precedent). Doc stays `assigned_vm: NA`.
- **na-eligibility-audit 2026-08-16** [body-hash:401ef52cf40b6d68]: KEEP-NA, valid — Focused issue doc on a live production data-correctness bug (BALANCER dex_pool_state writer emitting legacy cumulative column names, causing fee_apy_bps to silently read 0 for all Balancer pools).
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries)
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries) — unchanged, still accurate
