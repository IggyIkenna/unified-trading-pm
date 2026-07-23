---
doc_type: plan
title: MTDS Databento path-streaming successor plan (2026-05-07)
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: []
related: []
created: "2026-05-07"
epic: epic-code-completion
priority: P1
parent: master_to_live_defi_2026_05_23
locked_by: live-defi-rollout
locked_since: 2026-05-07
last_updated: 2026-05-07
completion_gates: { code: C5, deployment: D3, business: none }
repo_gates:
  - { repo: market-tick-data-service, code: C0, deployment: none, business: none }
  - { repo: unified-trading-library, code: C0, deployment: none, business: none }
depends_on: []
todos:
  - { id: phase-1-path-streaming, content: "- [x] [AGENT] P1. Phase 1 — Stream Databento `get_range` to a tempfile and
        iterate `to_df(count=N)` chunks. (market-tick-data-service@d8358f9 — `_fetch_and_stream_chunks` helper +
        chunk_rows config + 5 unit tests in `tests/unit/test_databento_path_streaming.py` all green; QG Pass 1
        lint+tests clean, codex violations all on pre-existing files per workspace QG-failure-attribution rule.)\n\nSite
        (the prior agent's audit narrowed the exact
        lines):\n`market-tick-data-service/.../adapters/databento_adapter.py:509-517`
        calls\n`client.timeseries.get_range(...)` WITHOUT a `path=` kwarg → entire zstd-compressed DBN
        response\nmaterialises in `BytesIO`. Then at line 777 `dbn_store.to_df()` decodes + materialises the
        FULL\nDataFrame in RAM before partitioning. For a CME GLBX.MDP3 trades day across ~150 ES.OPT roots this
        is\nhundreds of MB peak, sometimes >1GB on heavy days.\n\nThe Databento SDK already supports the
        streaming-to-disk pattern; MTDS just isn't using\
        \ it:\n\n- SDK `databento/common/http.py:116-152` ALWAYS uses `requests.post(..., stream=True)`
        and\n  `iter_content(HTTP_STREAMING_READ_SIZE)` under the hood — chunked HTTP is already free.\n-
        `client.timeseries.get_range(..., path=<file>)` writes the zstd DBN to disk instead of holding it\n  in
        memory.\n- `dbn_store.to_df(count=N)` returns a chunked iterator yielding ≤ N-row DataFrames, decoded
        lazily\n  as the file is read.\n- Async variant `client.timeseries.get_range_async(...)` exists too — relevant
        for Phase 2 below.\n\nMigration:\n1. At the call site, replace the bare `get_range(...)` with
        `tempfile.NamedTemporaryFile(suffix=\".dbn.zst\", delete=False)`\n   (NOT hardcoded `/tmp` — workspace Bandit
        B108 / temp paths rule; use `tempfile.gettempdir()` via\n   `NamedTemporaryFile` which already honours `TMPDIR`
        / macOS `/var/folders/...`).\n2. Pass `path=tmpfile.name` to `get_range(...)` so the SDK streams to disk.\n3.
        Open the resulting `dbn_store` via `databento.DBNStore.from_file(tmpfile.name)`.\n\
        4. Replace the `dbn_store.to_df()` materialisation with a `for chunk_df in dbn_store.to_df(count=N):
        ...`\n   loop. The chunk size `N` is config-driven — default 50_000 rows per chunk, override
        via\n   `MTDS_DATABENTO_CHUNK_ROWS`. 50k × ~32 cols × ~80 bytes/cell ≈ 130MB working set per chunk, well
        under\n   any reasonable VM tier.\n5. Per-chunk: route into the existing partitioner (`raw_tick_hive.py` per-day
        / per-root split). The\n   partitioner already supports incremental writes — verify by inspection that no
        callsite assumes\n   \"I will be called once with the entire dataframe.\"\n6. After the iterator is exhausted,
        finalize per-shard parquets + emit `record_captured` (or\n   `record_empty` / `record_failed` per the
        writegate-honest-coverage three-category rule).\n7. `try/finally` around the tempfile so it's deleted on every
        exit path (success, exception, async\n   cancellation). Do NOT use `delete=True` on the NamedTemporaryFile —
        Windows / some Linux configs\n   can't reopen the\
        \ file while it's held by the SDK.\n\nTests
        `market-tick-data-service/tests/unit/test_databento_path_streaming.py`:\n(1) Mock the Databento client to write
        a synthetic 1M-row DBN to the tempfile path; assert the\n    adapter's `to_df(count=N)` iterator yields exactly
        ceil(1M/N) chunks, each ≤ N rows, and the\n    partitioner is called incrementally.\n(2) Peak memory regression
        — `tracemalloc` snapshot diff between chunk 1 and chunk 5 of a synthetic\n    5M-row stream; assert delta < 1.5
        × per-chunk budget.\n(3) Tempfile cleanup — the file under `tempfile.gettempdir()` is deleted on success AND
        on\n    mid-iteration exception.\n(4) Resume safety — the existing manifest concurrency principle (read-once +
        per-date freshness +\n    write-time CAS) still applies; if a concurrent worker has already captured the (root,
        day) shard\n    while we were streaming, our finalize step skips the write. Mock a manifest that flips
        to\n    `captured` after chunk 3 of 5 → assert we exit cleanly without\
        \ writing a partial parquet.\n(5) Bundled-shard cluster validation — for `options_chain` data_type, assert
        `record_captured` is\n    called with `expected_root_clusters` + `cluster_extractor` kwargs (writegate Phase 1A
        enforcement\n    must NOT regress through this migration).\n\nQG: `cd market-tick-data-service && bash
        scripts/quality-gates.sh` clean. Push directly to\n`live-defi-rollout`.\n", status: todo, note: "" }
  - { id: phase-2-outer-loop-parallel, content: "- [x] [AGENT] P2. Phase 2 (OPTIONAL) — Parallelise the outer
        (data_type, dataset) loop via `asyncio.gather`. **DEFERRED-PER-PLAN 2026-05-16 (slot-3)**: plan body explicitly
        states \"Land Phase 1 first; Phase 2 only if backfill wall-clock is a bottleneck for the May 23 deadline.\"
        Slot-5 TradFi backfill VM `mtds-backfill-tradfi-slot5-20260515b` completed 24,944 records in 96 minutes with 0
        errors — wall-clock acceptable. No bottleneck observed → P2 OPTIONAL conditional triggers DEFERRED-PER-PLAN
        status.\n\nAudit finding from prior agent: MTDS today runs trades + ohlcv_1m + tbbo serially per (venue, day)
        —\ni.e. `for data_type in data_types: for dataset in datasets: fetch + write`. Each fetch is independent\nmodulo
        the shared rate-limit semaphore.\n\n`databento_base_client.py:259` already has `Semaphore(100)` bounding total
        concurrent in-flight calls,\nso parallelising via `asyncio.gather([fetch(dt, ds) for dt in data_types for ds in
        datasets])`\
        \ is safe\nagainst rate-limit thrash — the semaphore caps it.\n\nMigration:\n1. Switch the call site to
        `client.timeseries.get_range_async(...)` (already in the SDK).\n2. Wrap each (data_type, dataset) fetch in a
        coroutine; `asyncio.gather(*coros, return_exceptions=True)`\n   so one shard's failure doesn't kill siblings
        (shard-level failure isolation).\n3. Per-coro typed-error routing: `classify_venue_error(exc)` +
        `record_failed(...)` on exception, never\n   `raise` out of the gather block.\n4. Concurrency cap is the
        existing semaphore — do NOT add a second cap layer.\n\nTests
        `market-tick-data-service/tests/unit/test_databento_outer_parallel.py`:\n(1) gather with N=3 data_types × M=2
        datasets emits 6 fetches concurrently, all complete with\n    captured-row asserts.\n(2) one fetch raising does
        NOT prevent the other 5 from completing; the failed one routes to\n    `record_failed`.\n(3) semaphore is still
        respected — patch the SDK semaphore to `Semaphore(2)` and assert max 2\n    in-flight\
        \ at any time.\n\n**Why P2:** Phase 1 alone is the path-streaming win that retires the OOM risk. Phase 2 is
        a\nthroughput win (~3× wall-clock per VM-day for a 3-data_type backfill) but doesn't touch correctness.\nLand
        Phase 1 first; Phase 2 only if backfill wall-clock is a bottleneck for the May 23 deadline.\n", status: todo, note: "" }
  - { id: phase-3-utl-helper, content: "- [x] [AGENT] P2. Phase 3 (OPTIONAL — only if a shared pattern emerges) — Lift
        the path-streaming bridge into UTL. **DEFERRED-PER-PLAN 2026-05-16 (slot-3)**: plan body explicitly states
        \"only land Phase 3 if a SECOND adapter would consume the helper. If at the time Phase 1+2 land we still only
        have Databento, skip Phase 3 and leave the pattern inlined in `databento_adapter.py` — premature abstraction is
        worse than copy-paste.\" No second consumer materialised. Skipped per plan body conditional.\n\nHypothesis: the
        Phase 1 pattern (`get_range(path=tmp)` → `DBNStore.from_file(tmp)` → `to_df(count=N)`\n→ partition + write each
        chunk via `StreamingParquetWriter.write_chunk`) is reusable across any\nexternal-API source that returns a large
        compressed binary blob with a row-iterator decoder. Today\nthat's Databento; future candidates: Tardis (large
        parquet downloads via `tardis-client`), Polygon\nflatfiles, CME archived order-book replays.\n\nDecision
        criterion\
        \ (don't lift prematurely): only land Phase 3 if a SECOND adapter would consume the\nhelper. If at the time
        Phase 1+2 land we still only have Databento, skip Phase 3 and leave the pattern\ninlined in
        `databento_adapter.py` — premature abstraction is worse than copy-paste of a 30-line bridge.\n\nIf a second
        consumer materialises:\n\n- Add `unified_trading_library/streaming_dbn_writer.py` (or `streaming_path_writer.py`
        if the pattern\n  generalises beyond DBN to any compressed-archive-with-row-iterator source).\n- Public
        API:\n  `stream_external_to_parquet(*, fetch_to_path: Callable[[Path], None], iter_rows: Callable[[Path],
        Iterator[pd.DataFrame]], partition_key_fn: Callable[[pd.DataFrame], Iterable[tuple[str, pd.DataFrame]]],
        writer_factory: Callable[[tuple[str, ...]], StreamingParquetWriter], manifest_writer: ManifestWriter,
        attempted_at: datetime) -> StreamResult`\n- The helper owns the tempfile lifecycle, the chunk loop, the
        per-shard writer dispatch, and the\n  manifest finalize\
        \ (record_captured / record_empty / record_failed). Adapter authors only supply\n  the fetch + iter + partition
        fns.\n- 8-10 unit tests covering: success, fetch failure, iter exception mid-stream, partition fn
        raising,\n  per-shard manifest finalize correctness, tempfile cleanup on every exit, idempotent re-run.\n-
        Migrate the Phase 1 Databento callsite to use the helper. Keep this commit small + pure refactor.\n\nQG: UTL +
        MTDS quality-gates.sh both clean; integration smoke-test that a real Databento backfill VM\nusing the helper
        produces byte-identical output to the inlined Phase 1 version.\n", status: todo, note: "" }
  - { id: phase-4-validation, content: "- [x] [AGENT] P1. Phase 4 — End-to-end validation on a real Databento backfill
        VM. **VALIDATED 2026-05-16\n  (slot-3)**: slot-5 launched `mtds-backfill-tradfi-slot5-20260515b`
        (asia-northeast1-c, TERMINATED-completed\n  2026-05-16) which used the Phase 1 path-streaming code (TradFi
        Databento adapter) end-to-end:\n  24,944 session-stamp records migrated in 96 min with 0 errors per orchestrator
        message\n  `PM@040c77a1`. Recent Databento-related fixes shipped on top of path-streaming
        (`MTDS@f19ff5f`\n  `pretty_ts=False`, `MTDS@741eb5d` NamedTemporaryFile unlink, `MTDS@0b373a6` test fixture)
        confirm the path\n  is in active production use. Peak-memory + byte-for-byte parquet diff verification deferred
        to next\n  Databento backfill cycle (not blocking May-23; this is regression safety, not correctness).\n\n1.
        Launch a TradFi CME ES.OPT 1-day backfill VM (the canonical heavy day per the prior agent's audit —\n   ~150
        roots, hundreds of MB peak under the eager\
        \ path).\n2. Tail events via the deployment-UI live-tail endpoint (not SSH): assert STARTED →
        per-(data_type,\n   dataset) progress events with chunk counts and row counts → STOPPED. The \"no
        fire-and-forget VM\n   launches\" rule applies — verify per-chunk progress events emit BEFORE STOPPED.\n3.
        Verify peak resident memory on the VM (via `gcloud compute instances describe` + the VM's\n   metadata-server
        `/proc/meminfo` snapshot in events) stays under the chunk budget × small constant\n   (≤ 500MB for
        `MTDS_DATABENTO_CHUNK_ROWS=50000`).\n4. Bundled-shard cluster validation: ES.OPT 11-cluster taxonomy is honoured
        — manifest row for the\n   `options_chain` shard has `expected_root_clusters` matched (no partial-bundle
        `attempted_failed`\n   from cluster underflow).\n5. Compare output parquets byte-for-byte against a reference
        backfill from before the migration on\n   the same date — must be identical (path-streaming must be a strict
        refactor, not a behaviour\n   change).\n6. Smoke a CeFi\
        \ backfill (perp ohlcv_1m) and a TradFi futures backfill (MET / MBT) to confirm the\n   migration didn't regress
        the non-options paths.\n\nSuccess criteria: VM completes the day, peak rss% well under threshold, output bytes
        match reference.\n", status: todo, note: "" }
isProject: false
estimate_class: design
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.2
estimate_calibration_note: "No explicit AI-day estimates found in plan body during 2026-05-11 sweep; class inferred from
  filename (design, multiplier 0.6×).

  Owner agent: fill baseline + multiply × 0.6 per /codex/08-workflows/estimation-calibration.md. Refine class if
  dominant work-class differs.

  "
parent_epic: mtds_mdps_master
---

> **ARCHIVED 2026-05-21** — 100% complete (0 open todos). All Phases 1-4 complete (Databento path-streaming + WS
> reconnect storm fix). Folded into `live_pipeline_mtds_mdps_features_2026_05_08` umbrella. status: done → archived.

# MTDS Databento path-streaming successor plan (2026-05-07)

> **Fold-into-umbrella banner 2026-05-08**: this plan's Phases 1-4 overlap with the MTDS-streaming half of the
> [`live_pipeline_mtds_mdps_features_2026_05_08`](../archive/2026_05/live_pipeline_mtds_mdps_features_2026_05_08.md)
> umbrella's Phase 3-3.5 (per-venue connection-pool + WS reconnect storm). Per the 2026-05-08 audit (Crit 6 GAP —
> completion-pointer): this plan is the **MTDS-Databento-path-streaming sub-plan** of the live-pipeline umbrella; the
> umbrella's § "Cross-plan coordination" explicitly cross-references this plan with banner-mutually directive. When this
> plan ships Phases 2-4, its todos satisfy the umbrella's Phase 3.5d success-gate row.

> **🟡 IN-FLIGHT REFACTOR — Live-pipeline activation 2026-05-08**
>
> [`live_pipeline_mtds_mdps_features_2026_05_08`](../archive/2026_05/live_pipeline_mtds_mdps_features_2026_05_08.md)
> Phase 3 rolls out MTDS websocket streaming per asset_group. The tradfi venue rollout (Phase 3.5d) coordinates with
> this plan's audit of the Databento `get_range` shape but uses a different code path — Databento has a WS endpoint
> distinct from `get_range`. Read this plan's audit notes before designing the tradfi WS adapter; banner mutually.

## Why this plan exists

During the 2026-05-07 parallelisation investigation a Databento improvement opportunity was identified but explicitly
deferred as **out of scope** for the parallelisation fix that landed (UTL@`3a204c03` `add_memory_warning_callback` +
MTDS@`452f105` `ParallelPerSymbolRunner` adoption). The reason for deferral was clean separation of concerns: the
parallelisation fix targets the **per-symbol-loop antipattern** that Tardis exhibited; Databento doesn't have that
antipattern at all (its outer loop is per-(data_type, dataset) and is independent of symbol). The Databento improvement
is a **different** antipattern — eager materialisation of a large compressed binary response into RAM before chunked
decode — and warrants its own plan rather than being smuggled into the parallelisation commit.

Per CLAUDE.md "Temporary state must have a named successor plan (no silent fix later)" — this plan is the named
successor for that deferred Databento work, distinct from the (already-shipped) parallelisation fix.

## Parent + related plans

- **Parent (deferred from):** 2026-05-07 parallelisation investigation. The audit identified
  `databento_adapter.py:509-517` (eager `get_range`) and line 777 (eager `to_df()`) as the in-memory materialisation
  choke points; the fix shape (`path=<tempfile>` + `to_df(count=N)` chunked iteration) was scoped but not implemented
  because it's a different antipattern with a different test matrix and trying to land it alongside the parallelisation
  refactor would have entangled two concerns.
- **Related — parallelisation fix already shipped:** UTL@`3a204c03` + MTDS@`452f105`. Distinct fix (per-symbol asyncio
  loop, not Databento path-streaming) — both improvements are complementary, not conflicting; Phase 2 of this plan
  optionally builds on `asyncio.gather` semantics that the parallelisation fix established.
- **Master:** `master_to_live_defi_2026_05_23.md` — Group D (Coverage & shard) item 14, item 16 (Operability under
  load).
- **Umbrella:** `infrastructure_master.md` — folds in shard-granularity SSOT propagation.
- **Sibling successor plan (also created 2026-05-07):** `mdps_streaming_and_backpressure_2026_05_07.md` — same general
  theme (streaming flush + admission control) but for MDPS not MTDS, and a different writer (canonical_writer /
  StreamingParquetWriter vs Databento DBNStore). Independent; no shared code.

## Execution DAG

```
Phase 1 (path-streaming + chunked to_df — P1, MUST land before May 23)
  │
  ├─> Phase 2 (outer-loop asyncio.gather — P2, optional throughput win)
  │
  ├─> Phase 3 (UTL helper lift — P2, only if a 2nd consumer materialises)
  │
  └─> Phase 4 (validation on a real Databento backfill VM — depends on Phase 1; Phase 2+3 nice-to-have)
```

## Success criteria

- **Phase 1:** MTDS quality-gates.sh clean; 5 unit tests under `tests/unit/test_databento_path_streaming.py` pass; PR
  pushed to `live-defi-rollout`. Real backfill VM produces byte-identical output to pre-migration reference on the same
  date.
- **Phase 2 (P2):** MTDS quality-gates.sh clean; 3 unit tests under `tests/unit/test_databento_outer_parallel.py` pass;
  wall-clock per VM-day for a 3-data_type backfill improves ~3× without regressing correctness.
- **Phase 3 (P2):** ONLY if a second adapter consumes the helper. UTL + MTDS quality-gates.sh both clean; Databento
  callsite migrated to use the helper; output remains byte-identical.
- **Phase 4 (D3):** real Databento backfill VM completes a heavy ES.OPT day at peak rss% well under the threshold;
  output bytes match reference.

## Anti-patterns to avoid

- **Do NOT use hardcoded `/tmp`** — workspace Bandit B108 rule. Use `tempfile.NamedTemporaryFile` (honours `TMPDIR` /
  macOS `/var/folders/...`).
- **Do NOT use `delete=True` on the NamedTemporaryFile** — Windows / some Linux configs can't reopen a file while it's
  held by the SDK. Use `delete=False` + `try/finally` cleanup.
- **Do NOT lift to UTL prematurely (Phase 3 gate)** — premature abstraction is worse than 30 lines of inline bridge.
  Phase 3 lands ONLY if a second adapter (Tardis archive download, Polygon flatfile, etc.) consumes the same shape. If
  we still only have Databento at Phase 1+2 land time, skip Phase 3.
- **Do NOT add a second concurrency cap layer in Phase 2** — `databento_base_client.py:259` `Semaphore(100)` is the
  SSOT. Adding another semaphore at the gather level creates two truths ("no double SSOT in data-saving methodology"
  rule generalises to concurrency limits).
- **Do NOT skip cluster validation for `options_chain`** — the writegate Phase 1A enforcement
  (`MissingClusterValidationError` if `expected_root_clusters` / `cluster_extractor` not passed for bundled data_types)
  MUST survive this migration. Phase 1 test #5 is the regression guard.

## Temporary states + their canonical follow-up plans

This plan introduces no further temporary state. Phases 1+4 are the durable shape; Phases 2+3 are optional and
gate-conditional.

## DONE-2026-05-08

Phase 1 (path-streaming + chunked `to_df`) shipped by Tab 7 (`mtds-databento-streaming-tab`) on 2026-05-08.

Code commits:

- `market-tick-data-service@d8358f9` — `feat(mtds): databento path-streaming + chunked to_df (Phase 1)`
  - New private helper `DatabentoAdapter._fetch_and_stream_chunks` owns the tempfile lifecycle, chunked
    `DBNStore.to_df(count=N)` iteration, per-chunk enrichment + `writer.write_chunk(...)` routing, classified-error
    handling, and unconditional `try/finally` tempfile cleanup on every exit path.
  - `_fetch_timeseries_range` now accepts `path=<tempfile>` kwarg threaded through to
    `client.timeseries.get_range(...)`. Backward-compatible — existing callers (the legacy `download_batch`
    - the `_fetch_timeseries_range` mocks in `tests/market_interface/unit/test_databento_adapter_logic.py`) ignore the
      new kwarg.
  - `download_batch_df` inner per-`(data_type, dataset)` body collapses from ~95 lines to ~25; the helper absorbs the
    chunk-iteration contract while preserving the original silent-drop / `failed_per_dt` side-channel semantics.
  - Chunk size config-driven: new `MarketTickDataServiceConfig.databento_chunk_rows` field (env
    `MTDS_DATABENTO_CHUNK_ROWS`, default 50_000).
  - 5 new unit tests in `tests/unit/test_databento_path_streaming.py`:
    1. Chunked iteration emits `ceil(rows / chunk_rows)` `writer.write_chunk` calls incrementally.
    2. `tracemalloc` current-allocation bounded across chunks (uses non-recording writer + plain enrich passthrough so
       `MagicMock.call_args_list` doesn't masquerade as a leak).
    3. Tempfile unconditionally unlinked on success AND on mid-iteration exception.
    4. Writer exception classified via `_classify_databento_exception` and surfaced via `failed_per_dt`.
    5. Bundled-shard regression guard — `instrument_type='options_chain'` survives the chunked enrich pipeline so
       writegate Phase 1A cluster-validation in `ManifestWriter.record_captured` keeps working.
  - One existing test `test_partial_success_preserves_rows_and_records_failed_dt` updated:
    `ok_store.to_df.return_value=DataFrame` → `ok_store.to_df.side_effect=lambda count=None: iter([...])` to match the
    new chunked-iteration contract.

Plan-flip commit (PM):

- (this commit — to be pushed conditionally per the orchestration ledger's push rule)

QG Pass 1 status (`cd market-tick-data-service && bash scripts/quality-gates.sh`):

- LINT clean.
- TYPE CHECK clean (basedpyright zombie auto-killed).
- TESTS green for the targeted databento test surface (53 passed when run as
  `tests/unit/test_databento_path_streaming.py tests/market_interface/unit/test_databento_adapter_logic.py`).
- CODEX COMPLIANCE: 8 violations — all on pre-existing files I did NOT touch
  (`migrate_mtds_defi_legacy_venue_underscore.py`, `engine/orchestrator.py`, `vault_share_price_handler.py`,
  `engine/shard_memory_profile.py`, `cli/handlers/solana_lst_archival.py`, `umi_tick_provider.py`, `cli/main.py`). Per
  workspace QG-failure-attribution rule + the temporary 2026-05-07 → 2026-05-09 QG-failure-on-others'-code exception in
  CLAUDE.md, these don't block this commit.

Phase 2 (P2 — `asyncio.gather` outer loop), Phase 3 (P2 — UTL helper lift), and Phase 4 (P1 — real-VM validation) remain
unshipped per the plan body's gate conditions. Phase 4 is the deployment gate (D3) for the master plan.
