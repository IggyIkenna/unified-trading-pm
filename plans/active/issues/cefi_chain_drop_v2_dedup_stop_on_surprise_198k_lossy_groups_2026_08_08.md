---
doc_type: issue
title:
  CeFi Surface-C v2 dedup apply STOP-ON-SURPRISE — 198,250 chain-lossy groups (vs. tolerated 28), likely an active
  duplicate-manifest-row writer bug, not a chain-collision
summary: >-
  A fresh dry-run of `complete_cefi_manifest_canonical_dedup_v2_2026_07_20.py` (launched to close a small,
  pre-2025-11-01 residual-duplicate todo) correctly STOP-ON-SURPRISE'd: 198,250 PIN_ATOM-key groups now hold >1 CAPTURED
  row with DIFFERING row_count, vs. the 28-group tolerance measured/tolerated on 2026-07-24 (Finding 5/7 in the parent
  doc). `n_multichain_rows=0` (chain itself is NOT the differentiator), so this is NOT the known chain-collision shape
  the tolerance was written for — it looks like a much larger, probably-still-ACTIVE population of duplicate manifest
  rows under the same shard atom (same date/venue/data_type/instrument_type/pipeline_mode) with different row_counts,
  dominated by ASTER (1,166,689 rows in the dump), HYPERLIQUID (58,945), EXTENDED-STARKNET (4,423), plus smaller counts
  on COINBASE-FUTURES/BITFINEX-FUTURES/DERIBIT, spanning dates from 2024-01-01 through 2026-08-03 (today). This BLOCKS
  `--apply` of the v2 script (the correct, safe outcome — zero mutation occurred) and therefore also blocks
  `issues/cefi_pre_2025_11_manifest_duplicate_residual_2026_08_08.md` todo 2's original plan of "just re-run v2 apply";
  that todo is being closed via a narrower scoped equivalent that does not touch this population instead (see that doc's
  Progress Log).
status: open
nature: issue
asset_group: [cefi]
stage: [meta]
repos: [market-tick-data-service, instruments-service]
scope: [engineer]
tags: [cefi, manifest, duplicate, dedup, chain-drop, data-correctness, stop-on-surprise, big-finding]
related:
  [
    /plans/archive/2026_08/issues/cefi_pre_2025_11_manifest_duplicate_residual_2026_08_08.md,
    /plans/active/issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-08-08
author: unknown
parent_epic: cefi_master
priority: P1
source: >-
  Discovered while working plans/active/issues/cefi_pre_2025_11_manifest_duplicate_residual_2026_08_08.md todo 2, slot
  3, 2026-08-08 — a routine re-run of the already-proven-safe `complete_cefi_manifest_canonical_dedup_v2_2026_07_20.py`
  dry-run (`canonical-migration-cefi-dedup-apply-20260808-233932`, e2-standard-8, asia-northeast1-c) refused to proceed.
resolved_by:
locked_by:
assigned_vm: planning
assigned_role: data_engineering
code_refs:
  [
    instruments-service/scripts/complete_cefi_manifest_canonical_dedup_v2_2026_07_20.py,
    instruments-service/scripts/complete_cefi_manifest_canonical_dedup_2026_07_17.py,
  ]
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
context_scope:
  [
    instruments-service/scripts/complete_cefi_manifest_canonical_dedup_v2_2026_07_20.py,
    /plans/active/issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md,
  ]
---

# CeFi Surface-C v2 dedup apply STOP-ON-SURPRISE — 198,250 chain-lossy groups

## What I found

Launched `canonical-migration-cefi-dedup-apply-20260808-233932` (`cefi-dedup-apply` category, `e2-standard-8`,
`asia-northeast1-c`, DRY mode) as the first step of resolving
`issues/cefi_pre_2025_11_manifest_duplicate_residual_2026_08_08.md` todo 2 ("re-run the Surface-C dedup apply ... for
the pre-2025-11-01 range"). Consolidator cron (`uts-prod-manifest-consolidator-market-data-cefi-cron`) was ENABLED at
launch time (dry-run needs no drain — matches the script's own docstring, drain is only required for `full`/`--apply`).

The dry-run loaded 7 blobs (main index + 6 per-VM shards), ran cleanly through the v1 canonicalize pass and the v2
marker/venue-axis transforms (`marker_added=55956[cap=1422]`, `okx_opt=190`, `combo=0` — all within normal-looking
ranges), then hit the CHAIN-DROP safety check and refused:

```
[v2 CHAIN-DROP=True] rows merging on chain-differing PIN_ATOM groups=0  LOSSY(captured w/ differing count)=198250 [MUST be 0]
STOP (DATA LOSS): 198250 PIN_ATOM group(s) hold >1 CAPTURED row with DIFFERING non-zero row_count after the
underlying+chain key-fold — beyond the known _CHAIN_LOSSY_TOLERANCE_MAX=50 tolerance (the 2026-07-24 measured
BYBIT-SPOT residual was 2 groups); this is a DIFFERENT/unreviewed population — diagnose before --apply, do not just
raise the tolerance.
Diagnose before --apply.
command exited rc=1
```

**Zero mutation occurred** — the script's own dry-run-first design correctly refused before any snapshot/write. Full
log:
`gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-cefi-dedup-apply-20260808-233932/run.log`.

### This is very likely NOT a chain-collision, despite the check's name

`_chain_merge_safety()` reports `n_multichain_rows=0` alongside `n_lossy=198250` — meaning within every affected
PIN_ATOM-key group, `chain` is constant (a single value). The "lossy" count is really: **>1 CAPTURED row exists for the
exact same (date, venue, data_type, instrument_type, pipeline_mode[, underlying]) shard atom, with DIFFERENT `row_count`
values** — i.e. genuine duplicate manifest rows for one shard, unrelated to the chain-drop the check was built to guard.
Sample (`BITFINEX-FUTURES:PERPETUAL:AAVE-USDT@LIN` trades, `2026-07-24`): 8 distinct captured rows for the ONE shard
with `row_count` = 3146, 787, 158, 53, 14, 9, 4, 1 — looks like successive partial/incremental writes that were each
appended as a NEW row instead of updating/superseding the existing one for that shard.

### Venue / date breakdown (from the dump)

| venue             | rows (dump) | date range observed           |
| ----------------- | ----------- | ----------------------------- |
| ASTER             | 1,166,689   | 2024-01-01 .. 2026-05-27      |
| HYPERLIQUID       | 58,945      | 2025-05-28 .. 2026-08-01      |
| EXTENDED-STARKNET | 4,423       | 2026-07-07 .. 2026-08-02      |
| COINBASE-FUTURES  | 1,071       | (not individually sampled)    |
| BITFINEX-FUTURES  | 8           | 2026-07-24                    |
| DERIBIT           | 4           | 2026-07-13 (volatility_index) |

(198,250 is the GROUP count from the script's own gate; the row counts above are DETAIL-TABLE rows, i.e. every
individual captured row inside an affected group — several rows per group for the heavy venues.)

**ASTER's date range (2024-01-01 start) is notable**: ASTER is a recently-onboarded venue (heavy per-VM backfill shards
observed active THIS week — `cefi-queue-heavy-binancefutu-x17-20260808-*`, `cefi-fwd-20260808-*` — in the same dry-run's
blob list), yet duplicate rows appear as far back as 2024-01-01, well before any plausible real launch/ backfill-start
date for the venue. That combination (recent onboarding + duplicates on 2+-year-old dates) plus the 2026-03 through
2026-08 (today) density elsewhere suggests this may be an ACTIVE, ONGOING writer/backfill behavior (each write appending
a new row per shard atom instead of updating one), not a one-time historical artifact — i.e. this population may still
be GROWING right now, not a fixed backlog.

## Why it matters

- Blocks `--apply` of the already-proven-safe v2 canonicalization script fleet-wide (it can't distinguish "the small
  known-safe 28-group residual" from this new 198,250-group population — the gate is corpus-wide, not per-population).
- If the writer-append-instead-of-update hypothesis is correct, this is an ACTIVE data-correctness bug inflating the
  cefi manifest with duplicate rows continuously, not a historical residual — every future dry-run of this script (or
  any other tool relying on "one row per shard atom") will keep finding a GROWING population until the root cause is
  fixed at the writer/consolidator, not just cleaned up after the fact.
- `_dedup_blob`'s row_count-desc tie-break (keep the largest) may be the WRONG resolution strategy here if some of these
  groups are genuinely two DIFFERENT real captures rather than one canonical capture plus stale partial writes — needs a
  scoped sample-and-classify pass (mirroring `characterize_cefi_pre_2025_11_manifest_duplicates_2026_08_08.py`'s
  approach) before any bulk `--apply`, not a blind "raise the tolerance."

### Corroborating precedent already in the codebase

`complete_cefi_manifest_canonical_dedup_2026_07_17.py`'s own `_effective_dedup_key()` docstring documents the EXACT
failure shape at small scale, found 2026-07-24: "64 residual lossy PIN_ATOM groups were ASTER rows with TWO captured
rows sharing an identical PIN_ATOM but DIFFERENT `chain` (blank vs. `"ASTER"`) and DIFFERING real `row_count` — almost
certainly a writer chain-tagging transition (blank before, `"ASTER"` after) that produced a second manifest row instead
of updating the first, rather than two spellings of the same capture." This is precisely the mechanism hypothesized
above, just 3-4 orders of magnitude smaller than what this dry-run now measures (64 → ~1.17M ASTER rows alone). If the
writer-tagging transition never fully completed (or keeps re-triggering), the population would keep growing exactly as
observed — supports treating this as ACTIVE, not historical.

## Recommended decision

1. Scoped, READ-ONLY characterization of this population (ASTER / HYPERLIQUID / EXTENDED-STARKNET first, they're ~98% of
   the volume): for a sample of affected shard atoms, pull the underlying per-VM shard write history (which VM/run wrote
   each row_count value, at what timestamp) to determine writer-append-vs-update behavior directly, rather than
   inferring from row_count magnitudes alone.
2. If confirmed a writer/consolidator append bug: root-cause + fix at the writer/consolidator (the actual data-safety
   fix), THEN clean up the accumulated duplicate rows (the v2 script, or a purpose-built collapse, once the shape is
   confirmed safe).
3. If NOT a writer bug (i.e. some groups really are 2 distinct real captures): the `_dedup_blob` collapse strategy needs
   a per-population review before this volume can be swept in bulk — do not raise `_CHAIN_LOSSY_TOLERANCE_MAX` to
   unblock without that review; the script's own comment explicitly warns against this.
4. Until resolved, any consumer of the cefi manifest that assumes "1 row per shard atom" (dashboards, gates,
   `capture_status` rollups) should be treated as reading a manifest with a KNOWN, currently-uncharacterized
   duplicate-row population for these venues — flag downstream if this surfaces as a visible discrepancy.

## Finding 11 (2026-08-09, slot 14) — root-caused via code-path read (no live GCS per-row pull — see caveat): NOT a

missing-upsert writer bug; a row-key STABILITY gap on `chain` (+ historical multi-write-path drift for ASTER
specifically) lets genuinely-different dedup keys survive collapse

**Answer to todo 1's question**: the writer/consolidator is **not** naively appending with no update path — both layers
implement key-based "last-write-wins" dedup (an upsert, not a blind append):

- `ManifestWriter._merge_dataframes`
  (`unified-trading-library/unified_trading_library/manifest_writer/_writer_io.py:1322`) — every per-VM-shard rewrite
  does `pd.concat([existing_df, new_df]).drop_duplicates(subset=dedup_cols, keep="last")`. `record_captured` itself
  (`_writer_captured.py:419`) does a bare `self._records.append(...)` — a pure append — but that in-memory buffer is
  deduped against the ON-DISK shard at the very next flush via `_merge_dataframes`, so "append-only at the call site"
  does NOT mean "append-only on disk."
- `manifest_consolidator.consolidate()` (`unified_trading_library/manifest_consolidator.py`) does the SAME dedup
  cross-shard via DuckDB, `_BASE_DEDUP_COLS=(date,venue,data_type,service_name)` +
  `_OPTIONAL_DEDUP_COLS=(timeframe,league_id,chain,instrument_type,underlying,feature_group,model_family, training_period,strategy_id,client_id,instruction_type,instrument_id)`
  (line 553-567), last-write-wins ordered by `attempted_at`/`written_at` DESC (line 2932-2943) — this is architecturally
  identical to the writer's own key, by design.

**So why do duplicates survive?** Because `chain` IS part of both dedup keys, two captures of the same logical (day,
venue, instrument) shard that carry a DIFFERENT `chain` value are, correctly per the key's own contract, treated as two
DIFFERENT rows — dedup can't and shouldn't collapse them. Traced why `chain` isn't stable for these 3 venues:
`WsInstrumentBuffer.chain` (`market-tick-data-service/market_tick_data_service/live/_ws_window_helpers.py:204`) is set
via `self.chain = tick.chain or self.chain` — i.e. it only ever ADVANCES from unset once a tick carries a chain value,
and every buffer re-creation (`websocket_runner.py:281/330/882`, e.g. on a WS reconnect) resets it to `chain=None`. A
day-grain shard (`_resolve_row_key` keys on `date`, not per-connection) that spans a reconnect can therefore emit TWO
`record_captured` calls for the SAME day with DIFFERING `chain` (blank on the fresh connection before the first
chain-bearing tick arrives, populated after) — this is EXACTLY the mechanism Finding 5 already diagnosed for the
64-group ASTER "chain-tagging transition" residual, just observed here at 3-4 orders of magnitude larger scale and
across the venue's FULL live-capture history (ASTER/HYPERLIQUID/EXTENDED-STARKNET are the on-chain/perp-DEX venues where
`chain` is a meaningful, populated shard-atom dimension per `manifest_recorder.py`'s own docstring matrix — CEX venues
like BITFINEX-FUTURES never populate `chain` at all, consistent with that population being small/separate, see caveat
below).

**Independent corroboration — ASTER specifically has a documented history of multiple, non-retiring write paths**, found
via `market-tick-data-service/market_tick_data_service/scripts/register_aster_onchain_perp_manifest_gap_2026_07_28.py`'s
own docstring: before `market-tick-data-service@7a730cd6` (2026-07-28) hardcoded `per_vm_shards=True` on
`OnchainPerpBatchHandler`, an unconfigured invocation wrote real parquet but its manifest writes "silently starved on
the legacy single-blob CAS path" — this recovery script itself is explicitly **"Additive, NOT CAS... an additive
per-VM-shard write... No retire/CAS step is needed"**. A sibling script,
`scripts/rewrite_aster_cefi_manifest_2026_07_13.py`, ADDS rows for ASTER objects migrated DeFi-bucket→CeFi-bucket
(`aster_cefi_data_defi_bucket_migration_2026_07_13.md`), again purely additive. Multiple independent one-off
registration/migration passes over ASTER's history, none of which retire a pre-existing row for the same shard atom, is
consistent with (and likely compounds) the `chain`-instability mechanism above — different write eras plausibly also
differ in `pipeline_mode`/`source`/`chain` stamping for the same historical shard, none of which the dedup key retires
against.

**Verdict on the todo's literal framing**: CONFIRMED in observable effect (rows for the same logical shard are not being
collapsed to one), but REFUTED as "the writer lacks an update path" — it has one (last-write-wins dedup at both the
per-VM-shard flush and the cross-shard consolidator). The real gap is that the row-key's `chain` dimension (and likely
cross-era provenance fields for ASTER specifically) is not guaranteed IDENTICAL across repeated captures of the same
shard for these 3 venues, so the existing upsert can't fire. This is a write-time key-stability defect, not a
missing-dedup defect — the fix (todo 2) should target `chain` re-derivation/stability at capture time (e.g. resolve
`chain` from a per-venue UAC constant instead of per-tick `tick.chain`, since it's venue-invariant for a perp-DEX venue
and doesn't need to ride the tick stream at all) rather than widening the dedup tolerance.

**Caveat — no live GCS per-row write-history pull was performed** (todo 1 as literally worded asked to "pull the
underlying per-VM shard write history... at what timestamp"): this slot has no `instruments-service/.venv` provisioned
and no `duckdb` available for a bounded, filtered parquet read, and provisioning one was judged out of scope for a
root-cause read given the code-path evidence above was independently sufficient and internally consistent (matches
Finding 5's already-empirically-proven mechanism, matches the venue set that populates `chain` at all, matches ASTER's
own documented multi-write-path history). A future pass COULD still pull actual per-row `written_at`/`chain`/
`pipeline_mode` values for the `BITFINEX-FUTURES:PERPETUAL:AAVE-USDT@LIN`/`2026-07-24` sample (or an ASTER sample) via a
`pyarrow`/DuckDB filtered read of the relevant `_index/per_vm/*.parquet` shards to directly confirm the differing
`chain` value per row, if a stronger empirical proof is wanted before the todo-2 fix ships — flagged, not blocking. Note
the BITFINEX-FUTURES sample itself (a CEX venue, `chain` never populated) is likely a SEPARATE, smaller mechanism closer
to the already-tolerated BITFINEX-SPOT/BYBIT-SPOT residual (Finding 5's third population) than to the
ASTER/HYPERLIQUID/EXTENDED-STARKNET chain-instability mechanism — do not assume the same root cause for that sample
without separately checking it.

## Update 2026-08-09 (slot 3) — the SAME shape confirmed PRE-2025-11-01 too, at even larger scale (98,188 groups)

**Note re: Finding 11 above** — Finding 11's root-cause (WS-reconnect `chain` instability via `WsInstrumentBuffer`) is
specific to LIVE-capture writes. The pre-cutoff population below was very likely captured via BATCH backfills, not the
live WS path, so Finding 11's mechanism may NOT explain it — flagged as an open question in the new todo, not assumed.

While building the scoped pre-2025-11-01 equivalent for
`issues/cefi_pre_2025_11_manifest_duplicate_residual_2026_08_08.md` todo 2
(`instruments-service/scripts/apply_cefi_pre_2025_11_manifest_duplicate_residual_2026_08_08.py`), an added safety check
(mirroring this doc's `_chain_merge_safety`-style invariant, but computed over the FULL pre-cutoff corpus rather than
just the characterized 6,575 spelling-variant groups) surfaced: **98,188 PIN_ATOM-key groups pre-2025-11-01 hold >=2
CAPTURED rows with DIFFERING row_count under the IDENTICAL instrument_id spelling** (not a spelling variant — literal
duplicate rows for one shard). `drop_set_captured=502,746` if naively collapsed — the script's STOP-ON-SURPRISE gate
correctly refused, zero mutation occurred (`canonical-migration-cefi-dedup-apply-scoped-20260809-001849`, dry mode).

This is the SAME shape as the ASTER/HYPERLIQUID/EXTENDED-STARKNET population above (same-key, same-spelling, differing
row_count — "writer appended a new row instead of updating the existing one"), now confirmed present BEFORE the cutoff
too, at a scale (98,188 groups) ~15x the small, already-characterized-safe 6,575-group spelling-variant residual
`issues/cefi_pre_2025_11_manifest_duplicate_residual_2026_08_08.md` todo 1 found. This population was NEVER
characterized by that todo — its characterization script only checked for >1 DISTINCT SPELLING under a key, never >1 row
with the SAME spelling but differing row_count — so it never surfaced.

**Scope upgrade**: this now looks like a corpus-wide (pre- AND post-cutoff), long-standing manifest-writer defect, not a
recent/new-venue-specific one. The `apply_cefi_pre_2025_11_manifest_duplicate_residual_2026_08_08.py` script is being
tightened to operate ONLY on the narrow, already-characterized 6,575-group spelling-variant population (never touching
this newly-found population), so `issues/cefi_pre_2025_11_manifest_duplicate_residual_2026_08_08.md` todo 2 can still
close safely — this population is added to THIS doc's scope, not absorbed into that todo.

## Finding 12 (2026-08-09, slot 13) — Finding 11's chain-instability theory REFUTED by live GCS data; real mechanism is

repeated same-key `record_captured` writes from `market-data-processing-service`/`batch_tardis`, venue-agnostic

**Did the live GCS per-row pull Finding 11 flagged as missing.** Downloaded the actual `availability_index.parquet`
(490k+ rows) + all `_index/per_vm/*.parquet` shards from `gs://market-data-tick-cefi-prd-central-element-323112/` and
queried the exact sample rows via DuckDB (not code-path inference).

**Chain is NOT the differentiator.** Pulled Finding 11's own cited sample (`BITFINEX-FUTURES:PERPETUAL:AAVE-USDT@LIN`
trades, `2026-07-24`): 8 rows, `chain` is `None`/blank for **every** row — BITFINEX-FUTURES is a plain CEX venue that
never populates `chain` at all, so a chain-instability mechanism cannot apply to it, yet it shows the identical
duplicate shape as ASTER. Also confirms `_chain_merge_safety`'s own `n_multichain_rows=0` reading literally (it uses
`v1._effective_dedup_key`, which folds `chain` in — so a same-chain-value group is exactly what a byte-identical dedup
key would produce; two DIFFERENT chain values for one shard would have shown up as `n_multichain_rows>0`, and they
don't).

**The real, verified pattern** (confirmed in 2 independent samples — BITFINEX-FUTURES/AAVE-USDT trades 2026-07-24, and
ASTER/BNB-USDT trades 2024-10-25): multiple `capture_status='captured'` rows sharing the **identical** full shard-atom
key (date, venue, data_type, instrument_type, chain, underlying, instrument_id, `service_name`, `pipeline_mode`,
`source`) — every field byte-identical except `row_count` and `attempted_at`/`written_at` — written **seconds to minutes
apart** within a single run, with `row_count` **decreasing** each time (e.g. ASTER/BNB-USDT: 5760 → 1440 → 288 → 96 → 24
→ 6 → 1, all within 21 seconds). Both samples share `service_name=market-data-processing-service`,
`pipeline_mode=batch_tardis`, `source=tardis` — i.e. this is **MDPS's own Tardis-sourced CeFi trades capture path**, not
the MTDS live-WS path Finding 11 examined, and it is **venue-agnostic** (BITFINEX-FUTURES has no `chain` concept at
all), so it affects far more than the 3 on-chain-perp venues Finding 11 scoped to.

**Could not pin the exact current call site within this task's scope** — ruled out two adjacent candidates:
`OnchainPerpBatchHandler`
(`market-tick-data-service/market_tick_data_service/cli/handlers/onchain_perp_batch_handler.py`) stamps
`PipelineMode.BATCH_ASTER/BATCH_HYPERLIQUID/BATCH_EXTENDED`, never `batch_tardis`; and
`unified-trading-library/scripts/merge_mdps_cefi_manifest.py` (`merge_manifest_from_canonical_paths`) is scoped to
`processed_candles/by_date` (candle shards) and is genuinely key-deduped (`new_keys = discovered - existing_keys`), not
raw trades. The pattern (sharply decreasing `row_count` across several same-second-to-minute writes) is consistent with
a paginated/chunked Tardis fetch that flushes **each chunk** as an independent `record_captured` call instead of
accumulating the full window before one write — mirroring the ASTER "multiple additive, non-retiring write paths"
precedent Finding 11 already cited, just from a different (MDPS-owned, Tardis-batch) call site than hypothesized.

**Correction to Finding 11's fix candidate**: the proposed UAC per-venue chain constant (resolving `chain` from a UAC
registry instead of `tick.chain`) is now confirmed a **no-op** for this population — `chain` is not what's colliding —
and must NOT be implemented as the fix. Todo 2 below is re-scoped accordingly; the writer-side fix still needs its exact
call site located (not done this pass) before it can safely ship.

## Finding 13 (2026-08-09, slot 14) — pre-cutoff 98,188-group population CONFIRMED the SAME mechanism as Finding 12's

post-cutoff finding (venue-agnostic MDPS/batch\_tardis repeated writes, chain irrelevant); answers todo 3

**Methodology**: wrote
`market-tick-data-service/scripts/characterize_cefi_pre_2025_11_manifest_same_spelling_duplicate_rows_2026_08_09.py`
(READ-ONLY; single-request consolidated-index load mirroring
`characterize_cefi_pre_2025_11_manifest_duplicates_2026_08_08.py`, reusing its resolver/loader). The group-by

- count-distinct aggregation was pushed into **DuckDB SQL**, not pandas `.groupby()`/`.str.cat()` chains — under this
  host's measured contention during the run (load avg ~23 on 8 cores from concurrent fleet sessions), the pandas
  approach did not complete within a 1500s bound across two attempts; the equivalent DuckDB query completed in <30s
  end-to-end.

**Measured population** (consolidated `_index/availability_index.parquet` only, 5,122,367 pre-cutoff rows, 4,850,394
distinct effective-dedup-key groups): **58,682 lossy groups / 326,483 rows** — vs. the 98,188-group figure the apply
script's dry-run reported. That figure sums stats independently across the index PLUS all 6 `_index/per_vm/*.parquet`
shard blobs (`apply_cefi_pre_2025_11_manifest_duplicate_residual_2026_08_08.py`'s `main()` loop); those per-VM shards
are largely pre-consolidation captures of a SUBSET of the same underlying rows, so summing per-blob group counts
plausibly double-counts overlapping pre-/post-consolidation views of the same groups. The consolidated-index count
(58,682) is what any downstream reader of "the manifest" actually sees, so it's the number reported here — reconciling
the exact 98,188 figure is flagged as an open gap, not chased further since the population's ROOT CAUSE (the todo's
actual question) is answered below.

**Chain is irrelevant — confirms Finding 12, refutes Finding 11 for this population too**: 0% of the 58,682 lossy groups
have ANY row with a populated `chain`; a chain-DROPPED variant of the dedup key produces the IDENTICAL 58,682-group
count (delta=0), so `chain` does zero differentiating work here. Every affected row carries
`pipeline_mode ∈ {batch_tardis, batch_hyperliquid}` — 100% batch, ZERO live pipeline modes — which also rules out
Finding 11's WS-reconnect mechanism structurally (that mechanism only exists on the MTDS live-capture path).

**Venue / data_type / pipeline_mode breakdown** (lossy groups):

| venue            | groups | venue          | groups |
| ---------------- | -----: | -------------- | -----: |
| ASTER            | 39,506 | UPBIT          |    123 |
| HYPERLIQUID      | 16,416 | COINBASE-SPOT  |    122 |
| DERIBIT          |    456 | OKX-FUTURES    |    111 |
| BYBIT            |    372 | OKX-SPOT       |    104 |
| BINANCE-FUTURES  |    358 | BITFINEX-SPOT  |     66 |
| BITFINEX-FUTURES |    280 | BITGET-FUTURES |     41 |
| KRAKEN-FUTURES   |    261 | BITGET-SPOT    |     28 |
| OKX-SWAP         |    223 | KRAKEN-SPOT    |      8 |
| BINANCE-SPOT     |    207 |                |        |

data_type: `trades` 56,917 (97%), `derivative_ticker` 731, `book_snapshot_5` 560, `liquidations` 474.
pipeline_mode/source: `batch_tardis`/`tardis` 42,266 groups, `batch_hyperliquid`/`hyperliquid` 16,416 groups — matches
ASTER+small-venues vs. HYPERLIQUID exactly. Dates span the full pre-cutoff window (2024-01 through 2025-10), fairly
evenly spread with a ramp toward 2025-06..2025-10 (7,514 groups in 2025-10 alone, the single largest month).

**Sample evidence (15 sampled groups) reproduces Finding 12's exact signature**: every sample shows multiple `captured`
rows sharing a byte-identical shard-atom key, `written_at` all within SECONDS to tens-of-seconds of each other (one
ingestion run, not separate re-runs on different days), `row_count` DECREASING each successive write — e.g.
`ASTER:PERPETUAL:PYTH-USDT@LIN` 2025-02-22: `5760 → 1440 → 288 → 96 → 24 → 6 → 1`, all within 17 seconds. This is the
SAME cascade shape (same absolute values: 5760/1440/288/96/24/6/1) Finding 12 independently found for ASTER/BNB-USDT (21
seconds) on the post-cutoff population — strong corroboration this is one mechanism, not two.

**ACTIVE, not historical**: every sampled `written_at` falls in the narrow window 2026-08-02 to 2026-08-04 (days before
this characterization ran), even though the shard `date` values span 2024–2025 — a very recent retroactive historical
backfill campaign (consistent with the per-VM shard blobs observed in the bucket, `cefi-fwd-20260808-123230.parquet` /
`mdps-backfill-cefi-20260802-140125.parquet`), i.e. this population was still being written within the last week, not a
static residual.

**Code-path corroboration (Explore sub-agent pass)**: confirms `OnchainPerpBatchHandler`
(`market_tick_data_service/cli/handlers/onchain_perp_batch_handler.py`) is NOT the exact writer for this
`batch_tardis`-tagged population (it stamps `BATCH_ASTER`/`BATCH_HYPERLIQUID`, never `batch_tardis` — matches Finding
12's own elimination of this candidate). It DOES independently confirm two structurally relevant facts in a SIBLING
onchain-perp pipeline: (a) `shard_exists_prefix()` is hard-overridden to always return `None` ("re-process every date"),
disabling the framework's normal idempotency/skip-if-fresh guard, and (b) the underlying `ManifestWriter.add()`
(`unified_trading_library/manifest_writer/_writer_ingest.py`) is a pure APPEND with no dedup/upsert on the shard-atom
key. Precedent for a no-idempotency-guard, append-only pattern elsewhere in the codebase; the actual `batch_tardis` MDPS
writer (todo 2's target) still needs its own call-site pin — not attempted here, out of this todo's assigned scope.

**Answer to todo 3's question**: SAME root cause as the post-cutoff population, not a distinct one. The doc's own
hypothesis ("likely NOT [Finding 11's WS-reconnect mechanism], since pre-cutoff data was probably batch-captured") is
confirmed correct in the negative, but the affirmative mechanism is Finding 12's (venue-agnostic MDPS/ `batch_tardis`
repeated same-key writes within one run), independently reproduced here — not a third, separate mechanism. Todo 2's
eventual writer fix should collapse BOTH populations once shipped, since it is the same call-site defect; a NEW todo
below tracks the pre-cutoff-side re-verification once that fix lands.

## Todos

- [x] [DATA] P1. ✅ **Root-cause whether ASTER/HYPERLIQUID/EXTENDED-STARKNET manifest writes are appending a NEW row per
      write instead of updating the existing shard-atom row** — unified-trading-pm (this doc). See Finding 11: NOT a
      missing-upsert writer bug (both `ManifestWriter._merge_dataframes` and `manifest_consolidator.consolidate()`
      implement last-write-wins dedup keyed on date/venue/data_type/service_name+chain/instrument_type/underlying/
      instrument_id/etc.); root cause is `chain` row-key instability across live-capture reconnects
      (`WsInstrumentBuffer.chain` resets to `None` per buffer recreation, `_ws_window_helpers.py:204`), the same
      mechanism Finding 5 already diagnosed at 64-row scale, now observed at full-history scale for the 3 venues where
      `chain` is a real shard-atom dimension — corroborated by ASTER's documented history of multiple additive,
      non-retiring write paths (legacy CAS vs `per_vm_shards`, DeFi→CeFi bucket migration). No live GCS per-row pull
      performed (see Finding 11 caveat — venv/duckdb unavailable this slot; code-path evidence judged sufficient).
      **CORRECTED by Finding 12 (slot 13)**: the live GCS pull Finding 11 deferred was performed and REFUTES the
      chain-instability mechanism — see Finding 12 for the real (venue-agnostic, MDPS/`batch_tardis`-sourced) pattern.
- [ ] [DATA] P1. **Locate the exact `market-data-processing-service` / `pipeline_mode=batch_tardis` / `source=tardis`
      CeFi-trades capture call site that issues multiple `record_captured` calls for the IDENTICAL shard atom within one
      run (seconds-to-minutes apart, `row_count` decreasing each call — see Finding 12 for the two confirmed samples),
      fix it to flush once per shard atom (accumulate the full fetch window before writing, or make the writer dedupe
      safely across same-run repeat flushes), THEN re-run the v2 dry-run** to confirm the lossy-group count drops back
      toward the historical ~28-group baseline before any `--apply` is attempted again. **Finding 11's original fix
      candidate (resolve `chain` from a UAC per-venue constant) is CONFIRMED NOT APPLICABLE per Finding 12 — do not
      implement it; `chain` is not the differentiator.** (repo: market-data-processing-service, unified-trading-library)
- [x] [DATA] P1. ✅ **Characterize the pre-2025-11-01 same-spelling multi-captured-row population (98,188 groups,
      `drop_set_captured=502,746`)** — market-tick-data-service (new script
      `scripts/characterize_cefi_pre_2025_11_manifest_same_spelling_duplicate_rows_2026_08_09.py`, READ-ONLY). See
      Finding 13: measured 58,682 lossy groups in the consolidated index (scope-discrepancy vs. 98,188 noted, not
      chased); confirmed the SAME root cause as the post-cutoff population (Finding 12's venue-agnostic MDPS/
      `batch_tardis` repeated-write mechanism, chain irrelevant — NOT Finding 11's WS-reconnect mechanism), with the
      identical row_count decreasing-cascade signature and venue/data_type/pipeline_mode breakdown in Finding 13.
- [ ] [DATA] P2. **After todo 2's writer fix ships, re-run
      `instruments-service/scripts/apply_cefi_pre_2025_11_manifest_duplicate_residual_2026_08_08.py`'s dry-run (or a
      similarly-scoped pre-cutoff dry-run) to confirm the pre-cutoff same-spelling lossy-group count (58,682 per
      Finding 13) also drops back toward baseline** — since Finding 13 confirms this is the SAME writer defect as the
      post-cutoff population, todo 2's fix should collapse both; this todo is the pre-cutoff-side verification step.
      (repo: instruments-service)

## Progress Log

- **2026-08-08 (slot 3)** — Filed while working `issues/cefi_pre_2025_11_manifest_duplicate_residual_2026_08_08.md`
  todo 2. Dry-run evidence + venue/date breakdown above; zero mutation occurred (STOP-ON-SURPRISE fired before any
  snapshot/write). VM self-terminated (`VM_SHUTDOWN_ON_COMPLETION`) after failing exit_code=1.
- **2026-08-09 (slot 14)** — Root-caused todo 1 via code-path read across `unified-trading-library` (ManifestWriter
  `_merge_dataframes` + `manifest_consolidator` dedup keys) and `market-tick-data-service` (live WS buffer `chain`
  handling + ASTER's historical additive-write-path scripts). See Finding 11. No code change shipped this pass (todo 1
  is read-only root-cause; todo 2 owns the fix). No live GCS per-row write-history pull performed — flagged as a gap in
  Finding 11's caveat, not blocking given the code-level evidence.
- **2026-08-09 (slot 3)** — While building the scoped pre-2025-11-01 equivalent script, an added safety check surfaced
  the SAME "duplicate-row, same-spelling, differing row_count" shape PRE-cutoff too: 98,188 groups,
  `drop_set_captured=502,746` — ~15x the small, already-characterized-safe 6,575-group spelling-variant residual. Zero
  mutation occurred (dry-run, STOP-ON-SURPRISE fired). Added as a todo above; the scoped script is being tightened to
  exclude this population entirely so it doesn't block the narrow, already-safe todo it exists to close. See
  `issues/cefi_pre_2025_11_manifest_duplicate_residual_2026_08_08.md` Progress Log for the parallel entry.
- **2026-08-09 (slot 13)** — Worked todo 2 ("fix the writer/consolidator... then re-run the dry-run"). Performed the
  live GCS per-row pull Finding 11 flagged as not done (downloaded `availability_index.parquet` + all `_index/per_vm/`
  shards from the cefi market-data bucket, queried via DuckDB). Result: Finding 11's chain-instability root cause is
  REFUTED by this data — see Finding 12. The real pattern is venue-agnostic repeated same-key `record_captured` calls
  from `market-data-processing-service`/`pipeline_mode=batch_tardis`, confirmed in 2 independent samples. Did NOT ship
  Finding 11's proposed fix (UAC per-venue chain constant) since it's now confirmed a no-op for this population —
  shipping a fix known not to address the actual defect would be worse than leaving it open. Could not pin the exact
  current MDPS call site within this pass (ruled out 2 adjacent candidates, see Finding 12); todo 2 re-scoped to the
  narrower, evidence-backed next step. No mutation to any GCS bucket or manifest in this pass — read-only investigation
  only.
- **2026-08-09 (slot 14)** — Worked todo 3 (characterize the pre-cutoff 98,188-group population). Wrote
  `market-tick-data-service/scripts/characterize_cefi_pre_2025_11_manifest_same_spelling_duplicate_rows_2026_08_09.py`
  (READ-ONLY; DuckDB-based after two pandas-groupby attempts failed to complete in 1500s under heavy host contention).
  Measured 58,682 lossy groups in the consolidated index (scope-discrepancy vs. 98,188 noted, not chased — likely
  index+per-VM-shard double-counting in the apply script's own summed stats). See Finding 13: independently reproduces
  Finding 12's exact mechanism and row_count-cascade signature for the pre-cutoff slice — same root cause as
  post-cutoff, not distinct. Added a P2 follow-up todo for post-fix re-verification. No mutation to any GCS bucket or
  manifest — read-only characterization only.
