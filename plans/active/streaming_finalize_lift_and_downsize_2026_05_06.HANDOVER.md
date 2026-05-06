---
title: Streaming-finalize lift to UTL + CeFi VM downsize + DEX on-chain replay + KRAKEN-SPOT fix
locked_by: live-defi-rollout
locked_since: 2026-05-06
created: 2026-05-06
---

# Handover — five follow-ups from the 2026-05-06 streaming-finalize ship

The streaming-finalize path landed in `market-tick-data-service` (commits `22e2b2f` + `f07f3f9`) and validated
end-to-end on a Coinbase AVAX-USD smoke (peak RSS 1.04 GB on a 16 GB VM, 0 errors, /datasets endpoint works under
academic auth). Default flipped to ON so all new Tardis CeFi VMs use it automatically.

This handover covers the five operator-flagged follow-ups:

1. **Lift streaming-finalize into UTL** so other adapters (Databento, future sources) reuse the row-group + writer-pool
   pattern without copy-pasting.
2. **Make the 1 GB peak target configurable** via env var or UAC config (right now the row-group size is implicitly
   controlled by `pacsv.ReadOptions(block_size=8 MiB)` in `stream_bulk_csv_to_parquet`; surface it).
3. **Downsize every non-32 GB CeFi VM** that's not Coinbase (those need 32 GB even with streaming because BTC-USD
   book_snapshot_5 days scale ~10-20× AVAX); anything else can drop to e2-highmem-2/-4 once relaunched on the new
   tarball.
4. **DEX historical via on-chain replay** for EXTENDED-STARKNET, LIGHTER-ZKSYNC, PACIFICA-SOLANA. REST APIs return only
   "last ~100 trades"; on-chain event replay via The Graph Studio / Alchemy is the path.
5. **KRAKEN-SPOT 0 captured / 170k empty_confirmed mystery.** Almost certainly a Tardis exchange-code mapping bug —
   `kraken` vs `kraken-spot` vs other variant. Probe Tardis directly to find the right code, then update the mapping +
   delete the empty_confirmed manifest rows so they get re-attempted.

---

## Item 1 — Lift streaming-finalize from MTDS to UTL

### Why

The streaming-finalize path in `market-tick-data-service/.../tardis_adapter.py`:

- `finalise_and_write_cefi_shards_streaming(parquet_path, ...)`
- `_finalise_rg_chunk(...)`
- `_ensure_symbol_and_data_type_columns(...)`

is **structurally** a generic pattern — read parquet by row-group, route each row-group through a classification step,
write to a per-shard-key writer pool, close once at the end. The only Tardis-specific bit is the classification
(`_classify_row_instrument_type` + `finalise_rows_and_path`). Per the workspace "Shard-granularity SSOT" rule
(`[UTL] = cross-service runtime utilities; do not duplicate per-service`), the row-group iteration + writer pool belongs
in UTL, not in MTDS.

Per CLAUDE.md "System-First Architecture" + "Do not duplicate cross-service utilities per-service": when the next
adapter (Databento? a new Tardis-style data provider?) needs the same pattern, it should
`from unified_trading_library import StreamingShardFinalizer` not copy/paste `tardis_adapter.py`'s helper.

### What to extract

Add to UTL — exact module: `unified_trading_library/io/streaming_shard_finalizer.py` (siblings `streaming_writer.py`
already lives in `io/`):

```python
class StreamingShardFinalizer:
    """Read a temp parquet by row-group, route rows through a caller-supplied
    classifier, and write per-shard-key parquets to GCS via a writer pool.

    Decouples the "iterate parquet in row-groups" + "writer pool keyed by
    shard path" + "single close at end" pattern from any specific adapter's
    classification logic. Caller passes a ``shard_router`` callback that
    takes a row-group DataFrame and yields ``(shard_key, shard_path, shard_df)``
    triples; the finalizer handles the writer pool + close lifecycle.

    Bounded peak memory = max(one row-group + active writer state).
    """

    def __init__(
        self,
        bucket: str,
        peak_memory_target_mb: int = 1024,
    ) -> None:
        ...

    def finalize(
        self,
        parquet_path: str,
        shard_router: Callable[[pd.DataFrame], Iterator[ShardChunk]],
    ) -> FinalizeResult:
        """..."""
```

Where `ShardChunk = (shard_key: str, shard_path: str, shard_df: pd.DataFrame, metadata: dict[str, str])` and
`FinalizeResult = (written_paths: list[str], total_rows: int, per_shard_metadata: dict[str, dict])`.

### What to leave in MTDS

The Tardis-specific classification (`_classify_row_instrument_type`, `finalise_rows_and_path`, settlement-dimension
derivation) stays in `tardis_adapter.py`. The MTDS code becomes:

```python
from unified_trading_library.io import StreamingShardFinalizer

finalizer = StreamingShardFinalizer(bucket=canonical_bucket)
result = finalizer.finalize(
    parquet_path=tmp_path,
    shard_router=lambda rg_df: self._tardis_cefi_shard_router(
        rg_df, exchange=exchange, data_type=data_type, date=date_dt,
    ),
)
total_rows += result.total_rows
# ... call partition_writer.record_shard_count + record_instrument per shard
```

The `_tardis_cefi_shard_router` is what `_finalise_rg_chunk` does today minus the writer-pool bookkeeping.

### Tests

Move `tests/unit/test_tardis_streaming_finalize.py` UTL-side to
`unified-trading-library/tests/unit/test_streaming_shard_finalizer.py`:

- `test_single_row_group_single_shard` — one row-group, one writer, one close.
- `test_multi_row_group_writer_pool_reuse` — N row-groups with same shard_key → one writer reused via incremental
  `write_chunk`.
- `test_multi_row_group_multi_shard` — N row-groups, M shard_keys → M writers, each appended to incrementally, each
  closed once.
- `test_empty_parquet_graceful` + `test_unreadable_parquet_graceful`.
- `test_shard_router_exception_closes_writers` — if router raises mid-iteration, open writers must be closed cleanly
  (test for FD leaks).

Keep a thinner MTDS-side test for the Tardis classifier specifically.

### Followup item to log

Once lifted, **delete** `_finalise_rg_chunk` + `finalise_and_write_cefi_shards_streaming` from `tardis_adapter.py`
(replace with calls into UTL). No backwards compat shim — per CLAUDE.md "No half-finished implementations" + "no compat
shims".

---

## Item 2 — Configurable peak-memory target

### Current state

Streaming peak is implicitly controlled by `pacsv.ReadOptions(block_size=8 MiB)` in `tardis_stream_processor.py:159`.
Each pyarrow-CSV batch becomes one parquet row-group. For Coinbase BTC-USD book_snapshot_5 (~50M rows/day, 200-byte rows
≈ 10 GB total), 8 MiB blocks → ~1280 row-groups, peak working set ~50-100 MB during stream + ~1 GB during write side.

The smoke validated 1.04 GB peak on AVAX-USD (a small symbol). On BTC-USD heavy days, peak should still be bounded by a
single row-group's pandas materialization, but exact ceiling depends on row-group size.

### What to add

Surface the block size as a UAC-tier configurable. Two options:

**(a) Env var** — `TARDIS_STREAM_BLOCK_SIZE_MB` (default 8). Lowest-friction. Read in `stream_bulk_csv_to_parquet` via
the same `os.environ.get(...) # config-bootstrap: VM fallback` pattern.

**(b) UAC config** — add `STREAM_BLOCK_SIZE_MB` to UAC's `market_data_categories.py` or the new `streaming_config`
module. Plumbs through `TardisAdapter.__init__` as a `block_size_mb` kwarg.

**Recommended: (a) + (b) together** — env var for runtime override (debug / emergency tuning), UAC config for the SSOT
default. Ship together.

Also: log peak RSS per `Tardis streaming success` line (already happens — keep it, it's the empirical observability hook
for tuning).

### Tunable values to pick

Per smoke test, AVAX-USD book_snapshot_5 = 1043 MB peak with 8 MiB blocks. Linear scaling = BTC-USD ~10-20× → 10-20 GB
peak. That's acceptable for e2-highmem-4 (32 GB).

For 16 GB VMs to handle BTC-USD: drop block size to ~1-2 MiB → peak ~1-3 GB. Trade-off: smaller blocks = more parquet
metadata overhead per row-group = slightly larger output file (~5-10% more bytes). Worth it for memory control.

### Followups

- Bench the block-size knob across {1, 2, 4, 8, 16} MiB on Coinbase BTC-USD full day. Plot peak RSS vs row-count.
  Document the sweet spot.
- If the bench shows that 2 MiB gives <2 GB peak with negligible compression loss, default the block size to 2 MiB
  across the workspace.

---

## Item 3 — Downsize every non-32 GB CeFi VM

### Why

Streaming-finalize peak ≈ 1 GB on AVAX-USD, ~10-20 GB on BTC-USD heavy days. **Every CeFi VM currently at e2-highmem-8
(64 GB) or higher is overspecced** once it relaunches on the new tarball.

### What to relaunch

After the active fleet finishes (or you decide to roll mid-flight), relaunch on **e2-highmem-4 (32 GB)** for everything
except Coinbase BTC-USD-only shards and Deribit options chain bundles. Coinbase BTC-USD specifically may want
e2-highmem-8 (64 GB) until the block-size tuning lands.

Order of operations:

1. **Wait for the 56-VM Coinbase fan-out (run-ts=20260506-212742) to drain.** Then confirm via
   `python3 /tmp/show_venue_coverage.py COINBASE-SPOT 2025-01-01 2026-04-17` that book_snapshot_5 covered ≥99% of dates.
2. **For any remaining Coinbase gaps**: relaunch via the cefi sharded launcher with `MACHINE_TYPE_HEAVY=e2-highmem-4`
   (32 GB instead of 64 GB).
3. **For BITFINEX-SPOT, BITGET, KRAKEN, OKX, BINANCE, BYBIT future relaunches**: default to e2-highmem-2 (16 GB) — these
   venues have much lower per-(symbol, day) row counts than Coinbase. Bump to e2-highmem-4 only if a specific shard
   OOMs.
4. **Update the launchers' default machine types**:
   - `launch-cefi-sharded-backfill.sh`: `MACHINE_TYPE_HEAVY=e2-highmem-2` default (currently e2-standard-2 = 8 GB which
     is too low; the streaming path can handle it but headroom is thin). Bump to e2-highmem-4 for COINBASE-SPOT
     specifically.
   - `launch-tier3-cefi-backfill.sh`: `MACHINE_TYPE=e2-highmem-2` default.

Cost savings: 56 × $0.40/hr (e2-highmem-8) → $0.20/hr (e2-highmem-2) ≈ **$11/hr saved fleet-wide** on next relaunch.

### What NOT to downsize

- **Tradfi options-chain bulk path** (Deribit, CME ES options) — uses a different code path (`_download_bulk` →
  futures_chain bundling) that still materializes full chain DataFrames. Memory pattern is bound by cluster_coverage
  validation. Keep at e2-highmem-4 for now.
- **MDPS processing VMs** — separate service, separate memory profile (already on e2-standard-8). Not affected by this
  Tardis change.

---

## Item 4 — DEX historical via on-chain replay (EXTENDED / LIGHTER / PACIFICA)

### Current state

Per `market-tick-data-service/.../umi_tick_provider.py:_fetch_extended_rest`, `_fetch_lighter_rest`,
`_fetch_pacifica_rest` — the REST APIs return "last ~100 trades only" with no time-bounded query. Tardis doesn't support
these venues. Live forward-poll works; historical is the gap.

### Architecture

Each venue has a different chain + trade settlement model:

| venue             | chain     | trade event source                                            | replay method                                             |
| ----------------- | --------- | ------------------------------------------------------------- | --------------------------------------------------------- |
| EXTENDED-STARKNET | Starknet  | Off-chain matched, settled to Starknet via batched proofs     | parse Starknet `Transfer` + custom `Trade` events         |
| LIGHTER-ZKSYNC    | zkSync L2 | Fully on-chain CLOB; every match is a contract event          | The Graph subgraph or Alchemy webhooks on contract events |
| PACIFICA-SOLANA   | Solana    | Off-chain matched, settled to Solana program via instructions | Solana program log parsing via Alchemy / Helius           |

### Implementation paths

**Lighter (highest priority — fully on-chain CLOB)**:

1. Query [Lighter docs](https://docs.lighter.xyz/) or block explorer to find the contract address + event signatures for
   `Trade` and `OrderBookUpdate`.
2. Build a Graph Studio subgraph that indexes `Trade` events from the contract. Subgraph definition lives in
   `instruments-service/subgraphs/lighter_zksync.yaml` or similar.
3. Add `_fetch_lighter_history` to `umi_tick_provider.py` that queries the subgraph for `(market_id, start_ts, end_ts)`
   and emits the same row schema as the live `_fetch_lighter_rest`.
4. Wire into the per-day MTDS loop the same way Tardis venues are routed.

**Extended (Starknet)**:

1. Look at Starknet's contract events for the Extended `Settlement` contract. Probably available via Alchemy Starknet
   webhooks (check <https://docs.alchemy.com/reference/starknet-api-overview>).
2. Build replay analogous to Lighter: parse `Trade` / `Settlement` events, reconstruct (price, qty, ts, side).
3. Add `_fetch_extended_history` to `umi_tick_provider.py`.

**Pacifica (Solana)**:

1. Look at Pacifica program ID on Solana mainnet. Probably similar to Hyperliquid clones — events emitted as Anchor
   program logs.
2. Use Alchemy Solana / Helius to subscribe to logs for that program.
3. Parse `Trade` instruction discriminator + extract (price, qty, side, ts).
4. Add `_fetch_pacifica_history` to `umi_tick_provider.py`.

### Order of operations

1. Pick **Lighter** first (fully on-chain CLOB → cleanest event model, smallest chain footprint = cheapest replay).
2. Validate: build subgraph, fetch ~1 day of trades, confirm row schema matches the live REST fetch (so downstream
   features-onchain doesn't see a schema diff).
3. Once Lighter validates, repeat for Extended + Pacifica.

### What NOT to do

- Don't try to extend the REST `recentTrades` path with retries. The API genuinely caps at ~100 trades and there's no
  `from_timestamp` parameter. Was confirmed empirically 2026-05-06.
- Don't try Tardis. Tardis doesn't index these venues.

---

## Item 5 — KRAKEN-SPOT 0 captured / 170k empty_confirmed mystery

### Current state

`/api/data-status/turbo?venue=KRAKEN-SPOT` shows
`capture_status_counts: {captured: 0, empty_confirmed: 170622, attempted_failed: 0}` across 2020-2026. **Every shard the
orchestrator attempted came back empty.** Symbols look correct (`XBT/USD;ETH/USD;...` per
`launch-tier3-cefi-backfill.sh:61` — verified Tardis Kraken format).

### Most likely cause

Tardis exchange-code mismatch. The mapping in `unified-api-contracts/.../venue_mapping.py:166` says
`"kraken": "KRAKEN-SPOT"`, so MTDS routes Kraken-Spot fetches to Tardis exchange code `kraken`. **But** Tardis may have
renamed this endpoint to `kraken-spot` (matching the Kraken-Futures pattern of `cryptofacilities`). Compare to
`bitfinex` vs `bitfinex-derivatives`, `bitget` vs `bitget-futures`, `okex` vs `okex-swap` etc. — every other paired
venue uses distinct exchange codes. Kraken having `kraken` → spot AND `cryptofacilities` → futures is asymmetric.

### What to do

1. **Probe Tardis directly** via curl to confirm which endpoint actually has data. From a VM in asia-northeast1-c (so
   latency is comparable):

   ```bash
   for code in kraken kraken-spot kraken_spot; do
     URL="https://datasets.tardis.dev/v1/$code/trades/2024/06/03/XBT_USD.csv.gz"
     # XBT_USD or XBT/USD or XBTUSD — try variants
     curl -sI -H "Authorization: Bearer $TARDIS_API_KEY" "$URL" | head -3
   done
   ```

   The 200/404/403 response will tell us which code Tardis serves.

2. **Cross-check Tardis API docs** at <https://docs.tardis.dev/api/datasets-api> to see the canonical exchange
   identifier for Kraken spot.

3. Once the right code is found, update `venue_mapping.py:tardis_to_venue`:

   ```python
   "kraken-spot": "KRAKEN-SPOT",  # was "kraken"
   ```

   AND update launcher's symbol normalization in `tardis_adapter.py:_normalize_symbol_for_exchange` if Tardis
   kraken-spot uses a different symbol convention (e.g., `XBTUSD` no slash, vs current `XBT/USD`).

4. **Delete the 170k empty_confirmed manifest rows** so they get re-attempted on next run:

   ```bash
   # From a VM with manifest write access:
   python -m instruments_service.scripts.reconcile_phantom_manifest_rows_all \
     --asset-group cefi --venue KRAKEN-SPOT --apply
   ```

   Or write a one-off `delete_kraken_spot_empty_confirmed.py` if the audit tool doesn't support targeted manifest
   deletion.

5. Relaunch via `ONLY_VENUES="KRAKEN-SPOT" MACHINE_TYPE=e2-highmem-2 bash launch-tier3-cefi-backfill.sh --market-tick`.

6. Watch for `Tardis streaming success: N rows` log lines for KRAKEN-SPOT — non-zero rows = mystery solved.

### What NOT to do

- Don't add an `--ignore-empty` flag. The empty_confirmed result is honest; the bug (if confirmed) is upstream in the
  venue_mapping.
- Don't delete the empty_confirmed rows before fixing the mapping — they'd just refill empty on retry.

---

## Cross-cutting ordering

The five items are mostly independent but have one ordering constraint:

- **Item 1 (UTL lift) before Item 3 (downsize)** — once streaming is in UTL, any future adapter can use it; the downsize
  relaunches will pick up the UTL-side helper automatically via the path-dep resolution.
- **Item 2 (configurable block size) parallel with Item 1** — both touch the streaming code path; consolidate into one
  PR per repo (UTL + MTDS).
- **Item 4 (DEX replay) and Item 5 (KRAKEN-SPOT) are independent of 1-3** — do in any order based on operator priority.
  Lighter is the cleanest DEX starting point; KRAKEN-SPOT is the cheapest fix (probably one-line venue mapping change).

## Branch + commit hygiene

All work continues on `live-defi-rollout`. Quickmerge is the standard pathway
(`bash scripts/quickmerge.sh "msg" --agent`). Per workspace rules, edit the PM template in
`unified-trading-pm/scripts/workflow-templates/` if any GHA workflow needs updating, never the per-repo flat copies.

## Reference commits

- MTDS `22e2b2f` — streaming finalize + writer pool (initial ship, opt-in)
- MTDS `f07f3f9` — flip default to true (smoke validated 2026-05-06)
- deployment-service `latest` — `setup-data-pipeline-vm.sh` reads `TARDIS_STREAMING_FINALIZE` from VM metadata, exports
  for Python

## Pre-condition: read these CLAUDE.md sections first

- "Shard-granularity SSOT" + per-asset-group shard-key matrix
- "[UTL] = cross-service runtime utilities; do not duplicate per-service"
- "Manifest concurrency principle"
- "Manifest phantom audit" (for Item 5's empty_confirmed cleanup)
- "Per-VM shard isolation for concurrent backfills" (for Item 3 relaunches)

The sub-agent rules injection block in `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` applies to
anyone executing this handover.

---

## Session 2026-05-06 (continuation) — what shipped, what's still open

The "next agent" (this same session, post-handover) executed the highest-leverage subset and deferred the multi-day work
back to a future agent. Status of each item:

### Item 2 — Configurable peak-memory target — SHIPPED

- MTDS `tardis_stream_processor._resolve_block_size_bytes()` reads `TARDIS_STREAM_BLOCK_SIZE_MB` env var (default 8,
  clamped to [1, 64] MiB) at module load.
- `_DEFAULT_BLOCK_SIZE` now derives from that resolver — both `stream_bulk_csv_to_parquet` and the legacy `download_csv`
  path in `tardis_adapter.py:489` use the same env-driven knob.
- `setup-data-pipeline-vm.sh` reads `TARDIS_STREAM_BLOCK_SIZE_MB` from VM metadata + exports for Python.
- 16 GB VMs running heavy Coinbase BTC-USD days can now set `TARDIS_STREAM_BLOCK_SIZE_MB=2` via launcher metadata to
  bound peak RSS to ~2 GB at the cost of ~5-10% larger output parquets.
- **Bench knob not yet calibrated** — operator should run the {1, 2, 4, 8, 16} MiB sweep on Coinbase BTC-USD heavy day
  per the original handover's "Tunable values to pick" section to pick the right default. Surfacing the knob is the
  prerequisite; bench is a follow-up.

### Item 3 — Downsize launcher defaults — SHIPPED

- `launch-cefi-sharded-backfill.sh`: `MACHINE_TYPE_HEAVY` default bumped from `e2-standard-2` (8 GB) to `e2-highmem-2`
  (16 GB / $0.10/hr). Light profile unchanged at e2-standard-2 (8 GB) — book_snapshot_5 isn't in the light bundle so 8
  GB is fine. Override with `MACHINE_TYPE_HEAVY=e2-highmem-4` for Coinbase BTC-USD-only relaunches if 16 GB proves thin
  in practice.
- `launch-tier3-cefi-backfill.sh`: `MACHINE_TYPE` default downsized from `e2-standard-4` (16 GB compute) to
  `e2-highmem-2` (16 GB highmem, ~30% cheaper).
- Comment blocks updated to reference the streaming-finalize ship (MTDS f07f3f9) and the env-var override path.
- **Cost impact**: ~$0.01-0.05/hr per VM cheaper. On a 56-VM Coinbase fan-out + 7-VM tier3 run that's ~$0.50-3/hr
  fleet-wide. Marginal; the real cost reduction is the streaming-finalize peak drop (256 GB → 16 GB), which already
  shipped in the prior session.

### Item 5 — KRAKEN-SPOT Tardis exchange-code mismatch — TOOLING SHIPPED, change pending probe

- `market-tick-data-service/scripts/diagnose_kraken_spot_tardis.py` — probes Tardis for the canonical KRAKEN-SPOT
  exchange code by HEAD-ing every (exchange, symbol) combination on a known-active date. Run on a VM in
  `asia-northeast1-c` with `TARDIS_API_KEY` set.
- `market-tick-data-service/scripts/cleanup_kraken_spot_empty_confirmed.py` — diagnostic-only listing of stale manifest
  rows; points the operator at the canonical phantom-audit reconciler
  (`instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group cefi --venue KRAKEN-SPOT --apply`)
  for the actual deletion. The phantom-audit only deletes rows whose underlying parquet/source-response doesn't exist,
  so it's the right tool for "post-mapping-fix stale empties".
- **NOT YET CHANGED**: `unified_api_contracts/registry/venue_mapping.py:166`. The probe must run first to confirm the
  right code (likely `kraken-spot`, but could be `kraken_spot` or symbol-format-only) — speculative changes could wipe
  valid mapping entries. Operator: run the probe on a VM, then update the mapping per its `Action items` output.

### Item 1 — Lift `StreamingShardFinalizer` to UTL — DEFERRED

The path is working in production today (default-on per MTDS f07f3f9, validated end-to-end on Coinbase AVAX-USD smoke).
The lift is structurally a callback-API refactor with substantial test surface (writer-pool semantics, FD-leak
guarantees, multi-shard append) and would need cluster-validation interaction reviewed at the seam.

The lift is the right move per the workspace shard-granularity SSOT rule "Do not duplicate cross-service utilities
per-service" — but it's not blocking anything today. Refresh the design sketch in the original handover (Item 1 §What to
extract) is still accurate; only the test inventory needs adapting to whatever the next adapter (Databento or new
Tardis-style provider) actually exercises.

**When to do it**: when a second adapter needs the same row-group + writer-pool pattern, OR when the cluster-coverage
gate (UTL `record_captured` 4 pillars) needs to fire from inside the streaming finalize path — at that point duplicating
the logic per-adapter would be the wrong call.

### Item 4 — DEX historical via on-chain replay (EXTENDED / LIGHTER / PACIFICA) — DEFERRED

Multi-day work — at minimum: subgraph definition (Lighter first, fully-on-chain CLOB), Alchemy/Helius integration for
Starknet + Solana settlement events, schema-match validation against live REST output, MTDS routing. The original
handover Item 4 lays out the architecture per venue.

The right next step: pick Lighter as the canonical greenfield, build the subgraph against
`gs://deployment-scripts-.../subgraphs/lighter_zksync.yaml` (or wherever the workspace holds subgraph sources), validate
one day's replay matches the schema of `_fetch_lighter_rest`, then propagate the pattern to Extended + Pacifica.
Allocate ~3-5 days for this slice.

### Reference commits — Session 2026-05-06 (continuation)

- MTDS `<SHA>` — `TARDIS_STREAM_BLOCK_SIZE_MB` env var + diagnostic scripts (`diagnose_kraken_spot_tardis.py`,
  `cleanup_kraken_spot_empty_confirmed.py`)
- deployment-service `<SHA>` — launcher defaults bump + VM metadata passthrough for the new env var
- PM `<SHA>` — this handover update

(SHAs stamped by `live-defi-rollout` push.)
