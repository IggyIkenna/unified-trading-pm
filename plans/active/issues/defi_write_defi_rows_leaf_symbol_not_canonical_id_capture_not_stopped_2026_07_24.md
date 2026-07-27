---
doc_type: issue
title:
  "write_defi_rows() writes the bare SYMBOL as the filename leaf (not the ruled canonical_instrument_id), and DeFi batch
  capture is NOT stopped — both measured live during the 2026-07-24 raw-tick reconciliation run"
summary: >-
  Two compounding facts measured directly against PROD during /data-pipeline-reconciliation --asset-group defi
  (raw-tick, 2026-07-24). (1) canonical-cutover-register.md §5 and defi-canonical-naming-ssot.md's WRITE-MODEL banner
  both state DeFi capture is fully STOPPED pending the per-instrument writer fix, with the consequence "there are no new
  defi writes" post-2026-07-20 and defi leaf-shape findings should be unknown-vintage, not regressions. Directly
  measured: raw_tick_data/by_date/day=2026-07-24/.../UNISWAP_V2/.../COMP-WETH-30.0.parquet has time_created=
  2026-07-24T22:46:34Z (today, ~1h before probe); batch_onchain_subgraph/batch_chainlink/batch_onchain_rpc/batch_aave
  pipeline_modes are all actively writing new objects through day=2026-07-24. (2) The shipped write_defi_rows() (R1,
  market-tick-data-service, marked SHIPPED in defi_track01_per_instrument_and_canon_id_2026_07_24.md) builds the
  filename leaf from ONLY the raw symbol column (`f"{_sanitize_defi_symbol(group_symbol)}.parquet"`), discarding the
  full instrument_id it groups by — contradicting both pattern #1's hard rule (filename stem == instrument_id column)
  and the SAME plan's own "Confirmed decisions" bullet 8 lines above the shipped checkbox (example filename
  AAVE_V3-ETHEREUM:A_TOKEN:aUSDC.parquet). Measured 13/13 real sampled objects fail the UAC oracle's id-form check
  (canonical_path_violations, _ID_FORM_CHECKED_ASSET_GROUPS={cefi,defi}, shipped uac@d40c5d7d 2026-07-20). Because (1)
  is false, this defect is actively growing, not frozen historical residue. Neither fact appears flagged anywhere in the
  plan/codex text read during this audit.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    defi,
    canonicalisation,
    instrument-id,
    write-defi-rows,
    filename-leaf,
    capture-status,
    ssot-contradiction,
    data-correctness,
  ]
related:
  [
    /plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /codex/02-data/canonical-cutover-register.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
    /codex/02-data/cross-asset-canonical-target-ssot.md,
    /plans/audit/results/data_pipeline_reconciliation_defi_2026_07_24.md,
    /plans/audit/results/data_pipeline_reconciliation_defi_2026_07_20.md,
  ]
created: 2026-07-24
last_updated: 2026-07-24
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: research
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.72
assigned_role: data_engineering
drift_direction: worsening-slowly
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source:
  ["measured live during the /data-pipeline-reconciliation --asset-group defi (raw-tick) run, 2026-07-24/2026-07-25"]
---

# write_defi_rows() leaf-symbol defect + DeFi capture-not-stopped correction (2026-07-24)

## What was measured (direct GCS + code reads, not inferred)

### Fact 1 — DeFi batch capture is active today, contradicting the "capture STOPPED" planning premise

`canonical-cutover-register.md` §5: _"DeFi capture is STOPPED (11 collect + 3 forward crons PAUSED ~40 days)... The
correct `effective_from` for the defi leaf axis is the date capture resumes with the fixed writer, which is not yet set.
Until then defi leaf-shape findings are `unknown-vintage`, not regressions."_ `defi-canonical-naming-ssot.md`'s
WRITE-MODEL SUPERSEDED banner: _"DeFi capture is STOPPED pending the writer fix."_

Directly probed (GCS `time_created` metadata, not inferred from `day=` partition value):

```
raw_tick_data/by_date/day=2026-07-24/pipeline_mode=batch_onchain_subgraph/asset_group=defi/
  venue=UNISWAP_V2/chain=ETHEREUM/instrument_type=pool/data_type=dex_pool_state/COMP-WETH-30.0.parquet
  time_created = 2026-07-24T22:46:34.687000+00:00   (probe was 2026-07-24T23:5x-2026-07-25T00:0x UTC)
```

`raw_tick_data/by_date/day=2026-07-24/pipeline_mode=batch_onchain_subgraph/` alone contains many freshly-created objects
at that same ~22:46 UTC timestamp. `day=2026-07-23`'s `pipeline_mode=batch_kalshi_perp/` objects show
`time_created=2026-07-24T01:22:45Z` (i.e. written the day after their `day=` partition — normal backfill lag, not stale
data). Every `pipeline_mode` value found in the day=2026-07-22 census (`batch_aave`, `batch_chainlink`,
`batch_kalshi_perp`, `batch_onchain_rpc`, `batch_onchain_subgraph`) is `batch_*`, never `live_*` — this is an active
**batch/backfill** capture process, not a resumed live feed.

**Consequence**: the register's "no new defi writes ⇒ leaf-shape findings are unknown-vintage" classification does not
hold for the batch lane. The writer fix is racing against an actively-growing corpus, not a frozen one.

### Fact 2 — the shipped write_defi_rows() leaf convention doesn't match the ruled target

`market-tick-data-service/market_tick_data_service/market_interface/adapters/defi/canonical_write.py`, function
`write_defi_rows()` (current HEAD):

```python
# Shard by instrument_id → one parquet per instrument. venue/chain/type are
# fixed per batch, so each instrument_id maps 1:1 to a symbol; leaf = sanitized
# symbol (matching the migration sanitiser). Caller ``file_name`` is empty-only.
shards: list[tuple[pd.DataFrame, str]] = []
for _inst_id, group in df.groupby("instrument_id", sort=True):
    group_df = group.reset_index(drop=True)
    group_symbol = str(group_df[resolved_symbol_column].iloc[0])
    leaf = f"{_sanitize_defi_symbol(group_symbol)}.parquet"
    group_path = build_defi_partition_path(
        venue=v, chain=c, instrument_type=instrument_type, data_type=data_type,
        day=day, file_name=leaf, pipeline_mode=pipeline_mode,
    )
    shards.append((group_df, run_tag_aware_partition_path(group_path, run_tag)))
```

The loop groups on the FULL `instrument_id` (`_inst_id`, e.g. `UNISWAP_V2-ETHEREUM:POOL:COMP-WETH-30.0`) but then
discards it (leading underscore) and rebuilds the leaf from only `group_symbol` (the raw `symbol` column, e.g.
`"COMP-WETH-30.0"`). Verified against the real object above: content column
`instrument_id = "UNISWAP_V2-ETHEREUM:POOL:COMP-WETH-30.0"`, on-disk filename = `COMP-WETH-30.0.parquet`.

This contradicts:

1. **pattern #1's hard rule** — `cross-asset-canonical-target-ssot.md` §0/§1 and
   `four-surface-reconciliation-procedure.md` §2: _"filename stem == the `instrument_id` column == the manifest key,
   byte-identical"_.
2. **The SAME plan's own stated target**, 8 lines above the R1 "✅ SHIPPED" checkbox in
   `plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md`: _"Confirmed decisions (operator 2026-07-18):
   (1) shard key = the symbolic `canonical_instrument_id` (human-readable filename
   `AAVE_V3-ETHEREUM:A_TOKEN:aUSDC.parquet`; address = a content column + IS-def/join key)"_ — the shipped code produces
   `aUSDC.parquet`, not `AAVE_V3-ETHEREUM:A_TOKEN:aUSDC.parquet`.

**Measured impact**: fetched 13 real on-disk objects (UNISWAP_V3 `dex_pool_swaps` ×5, UNISWAP_V2 `dex_pool_state` ×8,
days 2026-07-22/2026-07-24) and ran the UAC oracle (`canonical_path_violations()`) on each — **13/13 (100%) fail** the
id-form check:

```
"defi single-instrument shard filename 'COMP-WETH-30.0.parquet' is not a canonical instrument_id
('VENUE-CHAIN:TYPE:SYMBOL') — raw venue wire symbol / bare symbol or a double-wrapped catalogue-miss id"
```

R1's own changelog states **6 of 7 defi handlers already route through `write_defi_rows`** (dex_pools, dex_swaps,
oracle_prices, risk_params, lending_indices, lst_rates) — so this is the estate-wide leaf convention for every EVM
single-instrument shard being captured today, not a single-venue anomaly.

## Why this wasn't caught before now

The oracle's id-form check (`_stem_id_form_violations`, `_ID_FORM_CHECKED_ASSET_GROUPS = {"cefi", "defi"}`) shipped
`unified-api-contracts@d40c5d7d` on **2026-07-20** — the same day the R1 changelog marks the fan-out as shipped, and the
same day `four-surface-reconciliation-procedure.md` was last reviewed (that doc still states, as of this audit, that
only tradfi carries a stem check — see the companion codex-currency finding in this run's report, §9/FIND-09 of
`plans/audit/results/data_pipeline_reconciliation_defi_2026_07_24.md`). It is plausible R1 was verified against the
oracle's PRE-`d40c5d7d` behavior (structure-only), which would have reported these same objects as clean.

## What is NOT claimed

- The true corpus-wide count of leaf-symbol-only objects (13 objects sampled across 3 days; not a corpus walk).
- Whether the sanitizer's `{sanitized_symbol}.parquet` choice was a deliberate, undocumented simplification of the
  "Confirmed decisions" bullet (e.g. to keep filenames short / match a legacy migration sanitiser byte-for-byte) or an
  unnoticed gap — this doc reports the measured divergence, not its intent.
- A fix design.
- The scale of Fact 1 beyond the specific pipeline_modes/days probed (5 pipeline_modes confirmed active through
  day=2026-07-23/24; other defi pipeline_modes/venues not individually re-checked for write recency).

## Todos

- [ ] [OPERATOR] P0. **Decide the sequencing implication of Fact 1**: since batch capture has not actually stopped, does
      the writer-fix-then-migrate plan need to (a) stop the active batch/backfill crons until the leaf-naming fix ships,
      (b) accept the growing backlog and let the eventual migration sweep it up, or (c) ship the leaf-naming fix on an
      expedited timeline given it's now measurably live-growing rather than static? Options, not a recommendation from
      this doc — needs the plan owner's call.
- [x] [DIAG] P1. **Measure the scale**: how many `pipeline_mode=batch_*` DeFi objects have been written since 2026-07-20
      (the register's implicit "capture stopped" reference point) under the bare-symbol leaf shape? A bounded
      per-day-since-2026-07-20 delimiter descent (not a corpus walk) would answer this. — already covered by
      defi_satellite_ao_dispatch_batch1_2026_07_25.md (see that doc for execution).
- [x] [CODE] P1. **Fix `write_defi_rows()`'s leaf construction** to use the full `instrument_id` (or
      `canonical_instrument_id` once that column is populated — see the companion FIND-06 in this run's report about the
      missing `canonical_instrument_id`/`asset_group`/`pipeline_mode`/`source`/`schema_version` columns) instead of the
      bare `symbol`, matching the "Confirmed decisions" target. Coordinate with whoever owns
      `defi_track01_per_instrument_and_canon_id_2026_07_24.md`'s R1 item — this is a correction to an item already
      marked shipped, not new scope. — already covered by defi_satellite_ao_dispatch_batch1_2026_07_25.md (see that doc
      for execution).
- [x] [PM] P2. **Update `canonical-cutover-register.md` §5** to reflect that the "no new defi writes" premise does not
      hold for the batch lane as of 2026-07-24 — either narrow the claim to the live/websocket lane specifically, or
      remove it and substitute the measured fact. — already covered by defi_satellite_ao_dispatch_batch1_2026_07_25.md
      (see that doc for execution).
- [x] [PM] P3. **Update `four-surface-reconciliation-procedure.md` §4/§4.3 and `reconciliation-finding-taxonomy.md`
      §2.2** — both currently state the oracle's filename id-form check is tradfi-only; it now covers cefi+defi by
      default (`unified-api-contracts@d40c5d7d` 2026-07-20, refined `@1cd27478` 2026-07-23). Their own worked example
      (`ADAF0:USTF0.parquet`, cited as "0 violations == CANONICAL, false-clean") now returns a real violation when
      re-tested directly. — already covered by defi_satellite_ao_dispatch_batch1_2026_07_25.md (see that doc for
      execution).

## Codex SSOTs

- `/codex/02-data/canonical-cutover-register.md` §5 (defi leaf axis premise)
- `/codex/02-data/defi-canonical-naming-ssot.md` (WRITE-MODEL banner)
- `/codex/02-data/cross-asset-canonical-target-ssot.md` §0/§1 (pattern #1 hard rule)
- `/codex/02-data/four-surface-reconciliation-procedure.md` §4/§4.3 (oracle id-form scope, stale)
- `/codex/02-data/reconciliation-finding-taxonomy.md` §2.2 (same staleness)
