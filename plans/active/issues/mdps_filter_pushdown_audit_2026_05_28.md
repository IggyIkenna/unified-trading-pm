---
title: "MDPS filter-pushdown audit — instrument_ids dropped on venue-prefix match"
created: 2026-05-28
author: harsh (claude opus 4.7) — slot main
source:
  - mdps_filter_pushdown_memory_audit_and_fix_2026_05_28.md
locked_by: live-defi-rollout
locked_since: 2026-05-28
parent_epic: mtds_mdps_master
---

# MDPS filter-pushdown audit — `instrument_ids` dropped on venue-prefix match

Phase 1 audit of the parent plan
[`mdps_filter_pushdown_memory_audit_and_fix_2026_05_28.md`](../mdps_filter_pushdown_memory_audit_and_fix_2026_05_28.md).
Read-only investigation, no code edits. Phase 1.4 canary VM was **not** run — the static-trace evidence below is
unambiguous enough that the canary would only confirm what the code already says. Recommending we skip straight to
Phase 2.

## TL;DR

- Hypothesis **CONFIRMED with refinement**: the CLI's `--instrument-ids` filter IS wired into the read path, but the
  read-path filter logic at
  [`orchestration_scanner.py:441-449`](../../../../market-data-processing-service/market_data_processing_service/app/core/orchestration_scanner.py#L441-L449)
  **silently drops `instrument_ids`** whenever a blob's path contains a matching `venue=` segment (the common case for
  properly-partitioned data).
- Result: `--venues V1 V2 --instrument-ids I1 I2 I3 I4` enumerates _every instrument under V1 + V2_, not just I1-I4. And
  with no `--venues` set at all (the full-scope VM case), **both** filters are skipped — every parquet for the day is
  queued.
- The 70 GB bloat is **not** a per-instrument DataFrame retention leak. It is the scanner returning 100–1000× more blobs
  than the operator asked for, all of which get dispatched to the ThreadPoolExecutor and downloaded by workers. Memory
  grows roughly linearly with the queued-blob count.
- A sibling listing helper —
  [`orchestration_scheduling.py:243`](../../../../market-data-processing-service/market_data_processing_service/app/core/orchestration_scheduling.py#L243)
  in `OrchestrationSchedulingMixin._list_files_in_bucket()` — calls `filter_blob_by_criteria` **unconditionally**, with
  a comment explicitly citing the 2026-05-05 incident the same shape caused. That is the correct shape; the scanner path
  simply never inherited the fix.
- Fix is a 3-line replacement in `_collect_matching_parquet_blobs` (see § 5).

## 1 — Read-path call stack

```
cli/main.py:237-274                MarketDataProcessHandler.run()
  → cli/handlers/process_handler.py:404, 537, 653
       process_candles_handler() → orchestrator.process_category()
    → app/core/orchestration_service.py:117  CandleOrchestrationService.process_category()
       (inherits CandleOrchestrationWriter → OrchestrationWorkersMixin + CandleOrchestrationScanner)
      → app/core/orchestration_service.py:539-610  _process_data_type()
        → app/core/orchestration_service.py:612-661  _resolve_files_to_process()
          → app/core/orchestration_scanner.py:292   CandleOrchestrationScanner._list_instrument_files()
            → storage_client.list_blobs(prefix="raw_tick_data/by_date/day={date}/")  [line 351]
            → _collect_matching_parquet_blobs()                                       [lines 371-378]   ← BUG IS HERE
          → app/core/batch_workers.py:317  BatchOrchestrationMixin._process_files_parallel()
            → batch_workers.py:284  _submit_instrument_file_tasks()    (ThreadPoolExecutor, max_workers=N)
              → batch_workers.py:305  executor.submit(self._process_instrument_file, ...)
                → live_workers.py:224  LiveOrchestrationMixin._process_instrument_file()
                  → live_workers.py:449  _read_tick_data()
                    → storage_client.download_bytes() + pl.read_parquet()
```

The `BatchOrchestrationMixin: memory backpressure engaged at 75.2%` log line is at
[`batch_workers.py:236`](../../../../market-data-processing-service/market_data_processing_service/app/core/batch_workers.py#L236)
inside `BatchOrchestrationMixin._on_memory_warning()`. The mixin only gates _new submissions_ — in-flight downloads
continue to completion, which is why memory keeps climbing for ~2 minutes after the backpressure log fires before the
OOM-killer would fire.

## 2 — Filter args lifecycle (read-time vs write-time)

| Arg              | File:line                                | Classification                                         | Note                                                                                 |
| ---------------- | ---------------------------------------- | ------------------------------------------------------ | ------------------------------------------------------------------------------------ |
| `instrument_ids` | `cli/handlers/process_handler.py:404`    | wiring (CLI → orchestrator)                            | `args.instrument_ids` cast and forwarded                                             |
| `instrument_ids` | `orchestration_service.py:238, 585, 635` | wiring (forwarded to scanner)                          | No filtering done at these hops                                                      |
| `instrument_ids` | `orchestration_scanner.py:376`           | **read-time-gate (intended)**                          | Passed to `_collect_matching_parquet_blobs`                                          |
| `instrument_ids` | `orchestration_scanner.py:448`           | **read-time-gate — BUG: only fires on venue-mismatch** | See §3                                                                               |
| `instrument_ids` | `orchestration_scanner.py:385`           | **read-time-gate — same bug in fallback branch**       | Identical pattern, same problem                                                      |
| `instrument_ids` | `orchestration_scheduling.py:243`        | **read-time-gate (correct)**                           | `filter_blob_by_criteria` called unconditionally. Comment cites 2026-05-05 incident. |
| `instrument_ids` | `data_source.py:131-132, 223-224`        | read-time-gate (correct, separate code path)           | `MockDataSource` / non-prod path; not used by `process` subcommand                   |
| `instrument_ids` | `orchestration_writer.py:268, 314`       | **write-time-gate** (VIX-specific)                     | Per-row check inside writer for a single special-case data_type                      |
| `venues`         | `orchestration_scanner.py:441-447`       | read-time-gate (correct path, but see §3)              | Prefix match works as intended                                                       |
| `venues`         | `orchestration_scheduling.py:243`        | read-time-gate (correct)                               | Same `filter_blob_by_criteria` call as above                                         |
| `data_types`     | `orchestration_service.py:231-247`       | read-time-gate (loop-level)                            | Orchestrator iterates only requested data_types; never invokes scanner for others    |
| `data_types`     | `orchestration_scanner.py:439`           | read-time-gate (per-blob partition match)              | `_blob_matches_data_type_partition()` — correct                                      |

Hypothesis predicted "~0 read-time hits and several write-time hits for the three filters." Reality is more nuanced: the
_intent_ is read-time gating, the _plumbing_ is in place, but the gating logic for `instrument_ids` is functionally a
no-op on the production path.

## 3 — The bloat owner: scanner logic-bug in `_collect_matching_parquet_blobs`

[`orchestration_scanner.py:441-450`](../../../../market-data-processing-service/market_data_processing_service/app/core/orchestration_scanner.py#L441-L450):

```python
if venues:
    blob_has_venue = any(f"venue={v}" in blob_name for v in venues)
    if not blob_has_venue:
        blob_has_venue = _blob_matches_chain_split_venue(blob_name, venues)
    if not blob_has_venue and not filter_blob_by_criteria(blob_name, venues, instrument_ids):
        continue
files.append(blob_name)
```

Logical truth table for the `continue` gate:

| `venues` set | `blob_has_venue` | `instrument_ids` checked?           | Blob included?                               |
| ------------ | ---------------- | ----------------------------------- | -------------------------------------------- |
| No           | n/a              | **No**                              | **Yes (all blobs)**                          |
| Yes          | Yes              | **No**                              | **Yes (all instruments in matching venues)** |
| Yes          | No               | Yes (via `filter_blob_by_criteria`) | Only if it matches                           |

So `instrument_ids` is **never consulted on the primary path**. It only acts as a rescue filter for blobs whose path
doesn't carry a `venue=` segment.

`filter_blob_by_criteria` itself is correct
([`path_parsing.py:118-146`](../../../../market-data-processing-service/market_data_processing_service/app/utils/path_parsing.py#L118-L146)):
it checks BOTH venues AND instrument_ids when each is provided. The bug is purely in _when_ the scanner calls it.

The 2026-05-28 smoke ran with `--venues BINANCE-FUTURES BYBIT --instrument-ids <4 symbols>`. Every BINANCE-FUTURES or
BYBIT trades parquet for the day matched the venue prefix, so `blob_has_venue=True` and the four-symbol filter was
silently ignored. With ~100+ perpetuals per venue, the scanner returned ~200+ blobs instead of 4. Workers downloaded
them. Memory climbed past 70 GB.

The 2026-05-28 full-scope CeFi VM ran without `--venues`. With `venues=None`, the entire `if venues:` block is skipped
and **every** parquet for the day is queued. Same root cause, larger blast radius.

### Sibling proof: the correct shape exists elsewhere

[`orchestration_scheduling.py:217-246`](../../../../market-data-processing-service/market_data_processing_service/app/core/orchestration_scheduling.py#L217-L246)
has the exact-same listing shape but written correctly:

```python
if not filter_blob_by_criteria(blob.name, venues, instrument_ids):
    continue
files.append(blob.name)
```

…with an in-line comment citing the 2026-05-05 incident (a related bug where data_type filtering was missed). The fix is
to bring `orchestration_scanner.py` to parity with this shape.

### What is _not_ the cause

- **Not** per-instrument DataFrame retention. The polars frame is `del`'d at `live_workers.py:470` after the polars→
  pandas conversion. The pandas frame is held only for the duration of `_process_all_timeframes()` — a per-instrument
  window, not a cumulative one.
- **Not** an unbounded ManifestWriter / accumulator. Manifest writes are streamed; no per-instrument residue.
- **Not** `pl.concat` / `pd.concat` of all-instrument data. The two `concat` calls in `live_workers.py:958, 1018`
  concatenate timeframe-slices _within_ one instrument, not across.

The bloat owner is upstream of the worker entirely: the scanner returns the wrong file list, so the workers faithfully
process hundreds of instruments the operator never asked for.

## 4 — Hypothesis verdict

**CONFIRMED.** The plan's hypothesis (filter-pushdown) is correct in shape — the read-time scope filter is the missing
piece. The implementation detail that diverges from the plan's prose is that the _plumbing_ for read-time filtering is
already there; the bug is that the _gate_ short-circuits past it. So the fix is even smaller than the plan anticipated.

This makes Phase 1.4 (the canary VM with `tracemalloc`) unnecessary. The cause is statically provable: the scanner
returns the wrong file list, and the worker downloads what the scanner returned. A canary would just confirm
`len(files_to_process)` is much larger than the operator-requested scope — which we already know by reading the code.

## 5 — Minimum-viable fix

**File:** `market-data-processing-service/market_data_processing_service/app/core/orchestration_scanner.py`

**Lines 441-449 (inside `_collect_matching_parquet_blobs`):**

Before:

```python
if venues:
    blob_has_venue = any(f"venue={v}" in blob_name for v in venues)
    if not blob_has_venue:
        blob_has_venue = _blob_matches_chain_split_venue(blob_name, venues)
    if not blob_has_venue and not filter_blob_by_criteria(blob_name, venues, instrument_ids):
        continue
files.append(blob_name)
```

After:

```python
if not filter_blob_by_criteria(blob_name, venues, instrument_ids):
    continue
files.append(blob_name)
```

**And the parallel fallback at lines 380-396 (`_list_instrument_files`):**

Before:

```python
if venues:
    blob_has_venue = any(f"venue={v}" in blob_name for v in venues)
    if not blob_has_venue and not filter_blob_by_criteria(blob_name, venues, instrument_ids):
        continue
files.append(blob_name)
```

After (same shape):

```python
if not filter_blob_by_criteria(blob_name, venues, instrument_ids):
    continue
files.append(blob_name)
```

`filter_blob_by_criteria` already handles `None` correctly (returns True), so this is safe when neither filter is
provided. The venue-prefix optimisation we lose is negligible — `filter_blob_by_criteria` is a substring check on a
small list; the cost is in the network listing call, which is unchanged.

No new module, no new abstraction, no orchestrator refactor. Phase 2.2 (per-iteration `del`) and Phase 2.3 (streaming
restructure) from the parent plan are **not needed** — the bug is upstream of the worker.

## 6 — Recommendation: skip Phase 1.4, proceed straight to Phase 2 + Phase 3

The plan's Phase 1.4 canary VM was a hedge against the hypothesis being wrong. The static trace is unambiguous (every
code path enumerated, the bug is two-line, the sibling-correct path exists at `orchestration_scheduling.py:243` as proof
of intent). A canary would burn ~1 hour of VM time + operator attention to confirm what the code already shows.

Proposed sequence:

1. **Phase 2.1**: ship the 3-line fix above. Add a unit test in
   `market-data-processing-service/tests/unit/test_orchestration_scanner.py` that exercises
   `_collect_matching_parquet_blobs` with `(venues=["V1"], instrument_ids=["I_specific"])` and asserts only the
   `I_specific` blob is returned, not the full V1 universe.
2. **Phase 3.1**: launch the canary VM (`e2-standard-4`, 16 GB) directly against the fix, with the same 4-instrument
   smoke scope. Pass criterion is in the parent plan: RSS < 2 GB throughout.
3. **Phase 3.3**: 16-day narrow-scope backfill on `e2-standard-4`. Unblocks the 4h/24h features-side work.
4. **Phase 4** (P2): codex SSOT update + revert the sharded-launcher mitigations.

Phase 2.2 (per-iteration `del`) and Phase 2.3 (streaming orchestrator) should NOT ship — they are P2/P3 against a
non-existent leak. If Phase 3.1 unexpectedly fails the RSS cap _with_ the scanner fix in place, then revisit.

## Side findings (do not chase from this audit)

- **`_collect_matching_parquet_blobs` returns `(files, all_parquet)`** but `all_parquet` is only used in the fallback
  branch (when `_data_type_requires_partition(data_type)` is False, line 380). Once the scanner fix lands, that fallback
  may be reachable for fewer cases — worth a tiny follow-up to confirm sports/prediction data still lists correctly. Not
  blocking.
- **`_blob_matches_chain_split_venue`** handles the DeFi `venue=BASE/chain=CHAIN/` partition shape. Make sure the new
  `filter_blob_by_criteria`-only path doesn't regress that — `filter_blob_by_criteria` uses `_resolve_venue_from_blob`
  (`path_parsing.py:50-115`) which should already cover it. A targeted unit test for
  `(venues=["UNISWAP-V3-ETHEREUM"], blob containing "venue=UNISWAP-V3/chain=ETHEREUM/")` would lock it in.
- **Backpressure mixin is well-engineered** (`_on_memory_warning` + `_unpause_if_safe`). Once the scanner fix lands and
  the queue is correctly scoped, backpressure should rarely engage. If it does on small scopes after the fix, the
  Explore agent's secondary suspect (pandas frame retention in `_process_all_timeframes`) becomes worth investigating.
  Not now.
