---
doc_type: issue
title:
  DeFi v2 expected-universe enumerator OOMs every daily run since 2026-07-14 — zero per-instrument expected_unattempted
  coverage for ALL DeFi data_types
summary: >-
  instruments-service's `enumerate_expected_universe.py --asset-group defi --enumerator-version v2 --apply-write` Cloud
  Run Job (scheduled daily 01:30 UTC) has failed with "The configured memory limit was reached" (8Gi ceiling) on every
  execution from 2026-07-14 through today 2026-08-01 (19 consecutive days) — DeFi is the ONLY asset_group failing;
  cefi/tradfi/sports/prediction all complete green on the same schedule. Root cause: `main()`'s v2 apply-write path
  (`scripts/enumerate_expected_universe.py:4309-4334`) materialises the ENTIRE per-instrument enumeration result into
  one in-memory `list[ExpectedRow]` before writing anything — fine for the other 4 asset_groups but DeFi's catalogue
  (dex_pool_state alone already carries 18.9M captured manifest rows) blows the list past 8Gi before a single row is
  written. Net effect, confirmed via a live manifest census: the entire DeFi per-instrument `expected_unattempted`
  denominator is silently empty — 0 rows for risk_params/ liquidation_events/dex_pool_state/dex_pool_swaps/oracle_prices
  (and every other DeFi data_type), fleet-wide, for 19+ days.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [instruments-service, deployment-service]
scope: [engineer]
tags:
  [honest-coverage, expected-unattempted, defi, oom, memory-bounding, instruments-service, enumerate-expected-universe]
related:
  [
    /plans/archive/2026_08/defi_expected_unattempted_seeder_design_2026_07_26.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/defi-data-types-catalog.md,
  ]
created: 2026-08-01
last_updated: 2026-08-01
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: refactor
assigned_role: data_engineering
drift_direction: advance-code
resolved_by:
locked_by:
context_scope:
  [
    /plans/archive/2026_08/defi_expected_unattempted_seeder_design_2026_07_26.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    instruments-service/scripts/enumerate_expected_universe.py,
    deployment-service/terraform/gcp/defi_collection_scheduler.tf,
  ]
source: >-
  Discovered 2026-08-01 (slot-16, data_engineering craft) while investigating
  /plans/archive/2026_08/defi_expected_unattempted_seeder_design_2026_07_26.md's Todo 6 ("investigate whether the v2
  expected-universe enumerator actually covers risk_params/liquidation_events/dex_pool_state/dex_pool_swaps/
  oracle_prices"). Code-level answer is YES (UAC `PROTOCOL_CAPABILITIES` declares all 5 via `_LENDING_DATA`/
  `_DEX_DATA`/`_YIELD_DATA` + explicit per-protocol `liquidation_events` entries), but a live `gcloud run jobs
  executions list` + a bounded column-pruned manifest census (`read_availability_index(bucket,
  columns=["data_type","capture_status"])`, no whole-corpus walk) proved the mechanism has been non-functional in prod
  for 19 days.
depends_on: []
supersedes:
superseded_by:
---

# DeFi v2 expected-universe enumerator OOMs daily — zero per-instrument `expected_unattempted` coverage

## What I found

**1. The mechanism is code-complete.** `instruments-service/scripts/enumerate_expected_universe.py`'s v2 per-instrument
enumerator (`_enumerate_v2_defi`) already covers `risk_params` / `liquidation_events` / `dex_pool_state` /
`dex_pool_swaps` / `oracle_prices` — the 5 data_types
`/plans/archive/2026_08/defi_expected_unattempted_seeder_design_2026_07_26.md`'s P2 implementation deliberately left
unwired (correctly — they are per-instrument grain, wiring this plan's venue/chain-grain seeder into them would write
incorrect coarse rows). Validity comes from UAC's `PROTOCOL_CAPABILITIES`
(`unified_api_contracts/registry/capability_declarations/_defi.py`):
`_LENDING_DATA = ["lending_indices", "liquidations", "risk_params"]` (lines 363, 484-510 etc.),
`_DEX_DATA = ["dex_pool_state", "dex_pool_swaps"]` (line 364, wired on every `_POOL`-instrument_type protocol),
`_YIELD_DATA`/`_STAKING_DATA = ["lst_rates", "oracle_prices"]` (lines 365-366), plus explicit `"liquidation_events"`
entries on `aave_v3` (line 379) and `morpho` (line 431). This confirms the plan's own design-correction note (§7):
"Per-instrument honest-coverage for these 5 data_types is a separate, larger task" is TRUE in the sense that the
mechanism is separate — but it already EXISTS, it just isn't running.

**2. The Cloud Run Job has been silently OOMing every day for 19 days.**
`gcloud run jobs executions list --project=central-element-323112 --region=asia-northeast1 --job=expected-universe-v2-defi`
shows every execution from `2026-07-14` through `2026-08-01` (today) failed with `Completed status: False`;
`gcloud run jobs executions describe` on the latest (`expected-universe-v2-defi-w5jxk`, 2026-08-01) gives the exact
condition:

```
message: 'Task expected-universe-v2-defi-w5jxk-task0 failed with exit code: 0 and message:
  The configured memory limit was reached.'
status: 'False'
type: Completed
```

The job runs 2026-06-23 through 2026-07-13 all succeeded (`status: True`) — this is a **regression**, not a day-one bug,
coinciding with the DeFi pool-catalogue growth this session's other active work already documents (the
`expand_defi_pool_catalogue_from_manifest.py` incident, 2026-07-31, 43.6GB RSS — same underlying "DeFi catalogue got a
lot bigger" shape). **DeFi is the only asset_group affected** — `cefi`/`tradfi`/`sports`/ `prediction`'s identical
`expected-universe-v2-<ag>` Cloud Run Jobs all complete green in 1.5-4 minutes on the same 01:30 UTC schedule, confirmed
via the same `executions list` command for each.

**3. Root cause, read directly in the code.** `main()`'s v2 apply-write path
(`scripts/enumerate_expected_universe.py:4309-4334`) does:

```python
v2_absent: list[ExpectedRow] = []
for expected_row in enumerate_v2(..., present_set=v2_present_set, ..., captured_set=v2_captured_set):
    v2_absent.append(expected_row)
    if len(v2_absent) > max_writes_per_run:
        ...  # halt-safety fires AFTER appending, not before
```

`enumerate_v2`/`_enumerate_v2_defi` themselves are generators (correctly lazy), but the caller drains the WHOLE
generator into one Python list — every `(instrument, date, data_type)` triple across the full catalog × date window ×
per-instrument-validity-filtered data_types — before `_write_absent_rows` is ever called (line 4389). For
cefi/tradfi/sports/prediction this fits in 8Gi; for DeFi it does not — `dex_pool_state` alone already carries 18.9M
**captured** manifest rows in the live index (confirmed via the census below), so the per-instrument catalog this
cross-product walks is proportionally enormous. This directly violates this craft's own EFFICIENCY north-star ("STREAM
instead of materialising the corpus in memory" — `unified-trading-pm/agents/data_engineering.md`) and is exactly the
memory-bounding guardrail class that file's STEP 0.56 warns about (2 prior same-shape DeFi-scale incidents in the same
week: `expand_defi_pool_catalogue_from_manifest_2026_07_31.py` 43.6GB, `features_service.cross_instrument` 38.8GB — both
caused a full agent-orchestrator outage on this shared host).

**4. Live manifest evidence (bounded, column-pruned read — no whole-corpus walk, single-walk discipline respected).**
`read_availability_index(bucket, columns=["data_type","capture_status"])` against the live
`market-data-tick-defi-prd-central-element-323112` consolidated index (29,956,737 rows total):

| capture_status           | count      |
| ------------------------ | ---------- |
| captured                 | 26,238,857 |
| empty_confirmed          | 3,716,101  |
| attempted_failed         | 1,765      |
| **expected_unattempted** | **14**     |

All 14 `expected_unattempted` rows are `lending_indices` (11) / `lst_rates` (3) — i.e. they come from **this plan's own
P2 MTDS-side venue/chain-grain seeder** (`DefiManifestRecorder.emit_expected_unattempted_for_remaining`, shipped
`market-tick-data-service@a5a93dc0`), matching slot-11's Todo-4 Progress Log entry exactly. **Zero**
`expected_unattempted` rows exist anywhere in the live index for `risk_params` / `dex_pool_state` / `dex_pool_swaps` /
`oracle_prices` — confirming the OOM'd job has never successfully written a single per-instrument `expected_unattempted`
row for DeFi. Per-data_type breakdown (no date filter — full history):

- `risk_params`: 29,024 rows (28,992 captured, 32 attempted_failed) — near-saturated already, but from an ad-hoc/manual
  capture, not this scheduler.
- `liquidation_events`: **0 rows of ANY capture_status** — never captured at all. Cross-checked
  `deployment-service/terraform/gcp/defi_collection_scheduler.tf`'s `defi_collect_operations` map: it wires
  `oracle-prices`/`dex-pools`/`dex-swaps`/`lending-indices`/`lst-rates`/`liquidations`/etc. but has **no**
  `liquidation-events` or `risk-params` entry, despite both having real handler code (`liquidation_events_handler.py`,
  `risk_params_handler.py`) and UAC capability declarations. These two data_types have no recurring collector at all — a
  separate, adjacent gap (see Todo 3 below).
- `dex_pool_state`: 18,930,756 rows (16,890,559 captured, 2,040,164 empty_confirmed, 33 attempted_failed).
- `dex_pool_swaps`: 6,205,363 rows (4,529,879 captured, 1,674,072 empty_confirmed, 1,412 attempted_failed).
- `oracle_prices`: 131,808 rows (131,178 captured, 630 empty_confirmed).

## Why it matters

The scheduler's own terraform comment documents the ORIGINAL bug this job was built to close (2026-06-19 audit): "0
`expected_unattempted` rows materialised in EVERY IS + MTDS `_index` fleet-wide" because the apply-write hop was never
cron-wired. That bug is now back, DeFi-only, for 19 days — the per-instrument honest-coverage denominator for the ENTIRE
DeFi asset_group (not just the 5 data_types
`/plans/archive/2026_08/defi_expected_unattempted_seeder_design_2026_07_26.md`'s Todo 6 asked about) has silently
regressed to under-counting: any downstream consumer of the DeFi coverage % (data-status UI, `_axis_census`,
honest-coverage reports) currently sees `captured / (captured + empty_confirmed + attempted_failed)` with the
`expected_unattempted` term always ~0 for per-instrument DeFi cells — overstating coverage completeness for any
not-yet-attempted instrument the catalogue already knows about. Per
`/codex/02-data/data-pipeline-correctness-hard-rule.md`, this is a correctness-heartbeat issue, not a
deadline-deferrable one.

## Recommended decision

Fix the OOM (Todo 1) rather than build a new parallel per-instrument seeder — the existing mechanism is already
correctly scoped and already covers these 5 data_types in code; it just needs to actually run to completion.

## Todos

- [x] ✅ [DATA] P0. Fix `instruments-service/scripts/enumerate_expected_universe.py`'s v2 `--apply-write` path
      (`main()`, ~lines 4309-4334) to stream/batch-write `ExpectedRow`s instead of draining the full generator into one
      `v2_absent: list[ExpectedRow]` before any write happens — e.g. flush to `_write_absent_rows` in bounded chunks
      (mirrors the existing `max_writes_per_run` halt-safety, but checked/flushed incrementally instead of only after
      full accumulation). Verify DeFi's `expected-universe-v2-defi` Cloud Run Job (8Gi) can then complete within its
      memory budget on a real run — or bump memory as a documented stopgap ONLY if streaming alone doesn't close the
      gap, per this craft's EFFICIENCY north-star (stream first, scale hardware second). (repo: instruments-service) —
      instruments-service@37f7e36e
- [x] ✅ [DATA] P1. **Sequentially gated on Todo 1.** Once the OOM is fixed, manually trigger
      `expected-universe-v2-defi` (or wait for the next 01:30 UTC scheduled run) and re-run this issue's manifest census
      (`read_availability_index(bucket, columns=["data_type","capture_status"])`) to confirm real `expected_unattempted`
      rows now materialise for `risk_params`/`dex_pool_state`/`dex_pool_swaps`/ `oracle_prices` (and any other
      previously-empty DeFi data_type). Record before/after counts in this doc's Progress Log. (repo:
      instruments-service) — instruments-service@66adbc1d, deployment-service@46e0eda
- [ ] [DATA] P2. Investigate whether `liquidation_events`/`risk_params` having no recurring collector in
      `deployment-service/terraform/gcp/defi_collection_scheduler.tf`'s `defi_collect_operations` map is intentional
      (one-off backfill only, by design) or a genuine scheduling gap — if a gap, wire a scheduler entry mirroring the
      sibling `oracle-prices`/`dex-pools` pattern. (repo: deployment-service)

## Progress Log

- 2026-08-01 (slot-16, data_engineering): Issue filed during investigation of
  `/plans/archive/2026_08/defi_expected_unattempted_seeder_design_2026_07_26.md`'s Todo 6. Full evidence above (Cloud
  Run execution history, `gcloud run jobs executions describe` OOM message, live manifest census, code-read root cause).
  No fix attempted in this session — scoped as its own follow-up per that plan's own Todo 6 framing ("a distinct, larger
  task").
- 2026-08-01 (slot-11, data_engineering): Todo 1 shipped — `instruments-service@37f7e36e`. Replaced `main()`'s v2
  apply-write path's drain-whole-generator-into-one-list pattern with `_stream_write_v2_absent_rows()` +
  `_write_v2_per_vm_shard_chunk()`: the bounded-window (non-`--full-history`) path now streams `enumerate_v2()`'s
  candidates through bounded 250k-row chunks, flushing the CSV report + a per-VM shard PART file
  (`_index/per_vm/{VM_NAME}-part{N:05d}.parquet`) every chunk instead of materialising the full candidate set first;
  `max_writes_per_run` halt-safety is now checked incrementally instead of only after a full drain. Confirmed safe
  against the manifest consolidator's shard discovery (globs every `_index/per_vm/*.parquet`, not one file per `VM_NAME`
  — `unified_trading_library.manifest_consolidator._list_per_vm_shards_with_mtime`). `full_history` mode
  (range-encoding, not used by the daily cron) is untouched — it still needs the full per-day set materialised for
  contiguous-span compaction. Added 7 new unit tests
  (`tests/unit/scripts/test_enumerate_v2_stream_write_oom_fix_2026_08_01.py`) covering multi-chunk streaming, mid-stream
  halt-safety (documents the trade-off: chunks already flushed before the cap trips stay written), apply_write shard
  PART-file writes (mocked GCS, no network), missing-env-guard fast-fail, and the zero-candidates path. Full
  `quality-gates.sh` green (321 pre-existing + 7 new tests pass, no regressions); shipped via quickmerge. Todo 2 (verify
  a real `expected-universe-v2-defi` Cloud Run run completes + re-run the manifest census) is sequentially gated on this
  and NOT attempted in this session — it requires triggering/waiting on the live 01:30 UTC Cloud Run Job (or a manual
  trigger) and is scoped as its own follow-up.
- 2026-08-01 (slot-15, data_engineering): Started Todo 2. Confirmed `instruments-service@37f7e36e` (Todo 1) reached
  `:latest` (image built 11:33:56Z, content-verified to carry `_stream_write_v2_absent_rows`) and manually triggered
  `expected-universe-v2-defi` via `gcloud run jobs execute --wait`. **It OOM'd again** — execution
  `expected-universe-v2-defi-6s6sx`, same `The configured memory limit was reached.` condition, but this time the crash
  (signal 9) happened DURING `_download_manifest`'s `Loading manifest from gs://.../_index/availability_index.parquet`
  step — BEFORE a single candidate row is even generated, let alone written. Todo 1's write-path fix was real and
  necessary but not sufficient: it never got a chance to run. **Second, distinct root cause**: `_download_manifest`
  already column-projects the read (the 2026-07-14 sports-OOM fix, `_needed_manifest_columns` /
  `_read_manifest_parquet_projected`), but that only bounds the on-disk/decompressed bytes — it still materialises the
  FULL 29.9M-row DeFi consolidated index as ONE pandas DataFrame with 7-8 present-set string columns
  (`_DEFAULT_PRESENT_COLS` + `capture_status`). Sports' fix worked because sports is 5.75M rows (~0.5GB projected); DeFi
  at 29.9M rows blows past 8Gi purely on pandas' per-cell Python-object overhead for string columns, independent of the
  compressed file size (1.07GiB on GCS). Fixed via `instruments-service@66adbc1d`: replaced `_download_manifest`
  (bulk-load into one DataFrame) with `_download_manifest_sets()` + `_stream_present_and_captured_sets_from_parquet()` —
  streams the manifest (main index + per-VM shards) through
  `pyarrow.parquet.ParquetFile.iter_batches(columns=..., batch_size=1_000_000)`, calling the existing, unmodified,
  tested `_build_present_set`/`_build_captured_set` PER BATCH and unioning the results (mathematically identical to
  building from one combined DataFrame — the only per-batch cross-row step, the bundle-grain rollup, is a pure
  per-asset_group lookup with no cross-batch dependency). Peak memory now O(1 batch) instead of O(full manifest); each
  local temp file (main index + every per-VM shard) is deleted immediately after it's streamed instead of held for the
  whole run. Removed the now-dead `_read_manifest_parquet_projected` (no remaining callers) and its 2 direct tests,
  replacing them with equivalent streaming-builder tests plus a new multi-batch-vs-whole-DataFrame equivalence test
  (`test_stream_present_and_captured_sets_multi_batch_equals_whole_dataframe`, batch_size=1 forcing 8 batches over the
  fixture) — the actual regression pin for this fix. Full `quality-gates.sh` green (56/56 in
  `test_enumerate_manifest_memory_frugal.py`, no regressions). Shipped + verified on origin:
  `instruments-service@66adbc1d`. **Re-verification against a live re-run (post image-rebuild) is in progress** — see
  the next entry for the outcome + before/after census counts.
- 2026-08-01 (slot-15, data_engineering): Re-verified `instruments-service@66adbc1d` after the LDR→main promotion +
  image rebuild (`:latest` digest `sha256:b218d358...`, built from commit `15d3e82b`, confirmed content-carries the
  streaming fix) and re-triggered `expected-universe-v2-defi` (`expected-universe-v2-defi-k8w8g`). **It OOM'd a THIRD
  time** — same `The configured memory limit was reached.` condition, but this time it got PAST the "Loading manifest"
  step (ran ~2 min vs. the prior ~29s) and died mid-stream. **Third, distinct root cause**: streaming the READ bounds
  the transient per-batch pandas DataFrame, but the ACCUMULATED OUTPUT — `present_set`/`captured_set`, plain Python
  `set[tuple[str, ...]]` — is NOT bounded by batching: DeFi's manifest is ~29.96M "present" rows (captured +
  empty_confirmed + attempted_failed) at a 7-8-column present-set grain, and ~30M Python tuple-of-strings set entries
  carry the same order-of-magnitude per-cell object overhead as the pandas DataFrame Todo 1/this-Todo's read-fix already
  eliminated — streaming the read alone cannot bound the final accumulated set size. Per this issue's own Todo 1
  acceptance criteria ("bump memory as a documented stopgap ONLY if streaming alone doesn't close the gap"), applied the
  stopgap: `deployment-service@46e0eda` makes `expected_universe_v2_scheduler.tf`'s `cpu`/`memory` per-asset_group
  overridable (module default stays the working 2 vCPU / 8Gi for cefi/tradfi/sports/prediction) and bumps DeFi
  specifically to `cpu=8`/`memory=32Gi` — a scoped, DeFi-only change, not a blanket fleet bump. Applied via the
  sanctioned `terraform/gcp/tofu.sh ENV=prod` wrapper (`tofu plan -target='module.expected_universe_v2_job["defi"]'` →
  reviewed the plan, exactly `0 add / 1 change / 0 destroy`, cpu `2→8` + memory `8Gi→32Gi`, nothing else touched →
  `tofu apply` the saved plan) before committing the terraform source, confirmed live via `gcloud run jobs describe`.
  Re-triggered (`expected-universe-v2-defi-hcs9g`, async): **SUCCEEDED** —
  `Execution completed successfully in 13m46.61s`, the first successful `expected-universe-v2-defi` run since 2026-07-13
  (20 consecutive prior days OOM'd). **Before/after manifest census** (same
  `read_availability_index(bucket, columns=["data_type","capture_status"])` query the issue's own evidence used — note:
  this bounded/column-pruned read helper ITSELF then OOM'd when re-run directly on this shared host post-fix, spiking to
  15.5GB RSS in ~5s despite only projecting 2 columns; an RSS-monitored kill switch caught it safely before host impact
  — logged as a follow-up finding below, NOT re-opening this issue's scope). Switched to a DuckDB (`duckdb==1.5.3`,
  already vendored) streaming aggregate against a local copy of the manifest parquet instead (per
  `run-bounded-analysis.sh`'s own documented DuckDB-over-pandas precedent) — computes the same GROUP BY in DuckDB's
  native columnar engine without ever materialising a 30M-row Python/pandas object, memory_limit=2GB, peak well within
  bounds:

  | capture_status           | before (2026-08-01, this issue's opening evidence)                       | after (this run) |
  | ------------------------ | ------------------------------------------------------------------------ | ---------------- |
  | captured                 | 26,238,857                                                               | 26,241,053       |
  | empty_confirmed          | 3,716,101                                                                | 6,556,301        |
  | attempted_failed         | 1,765                                                                    | 1,773            |
  | **expected_unattempted** | **14** (all `lending_indices`/`lst_rates`, from the P2 MTDS seeder only) | **607,685**      |

  Per-data_type `expected_unattempted` breakdown now (previously 0 for every one of these): `dex_pool_state`=96,992,
  `governance_events`=87,694, `lending_indices`=84,886, `liquidations`=82,315, `risk_params`=81,441,
  `dex_pool_swaps`=63,398, `position_data`=61,893, `oracle_prices`=15,485, `perp_funding`=6,846, `staking_yields`=5,053,
  `lst_rates`=2,448, `rewards`=2,119, plus 15 more data_types (incl. `liquidation_events`) each at ~1,141 — confirming
  the enumerator correctly seeds the denominator for `liquidation_events`/`risk_params` even with no recurring collector
  wired yet (Todo 3's open question), because "could exist" is independent of "has a collector". Todo 2's acceptance
  criteria (`risk_params`/`dex_pool_state`/`dex_pool_swaps`/`oracle_prices` all now materialise real
  `expected_unattempted` rows) is fully met. **Follow-up finding (not re-opening this issue, informs the craft's own
  tooling)**: `unified_trading_library.manifest_writer._read_index.read_availability_index(bucket, columns=[...])` — the
  SAME helper this issue's own opening evidence used successfully — does NOT actually bound memory at DeFi's current
  ~33.4M-row scale despite column projection; it OOM'd directly on this host on a 2-column request. Worth a dedicated
  issue doc for UTL if this helper is relied on elsewhere at DeFi scale; out of scope here.

- **context-scout 2026-08-01**: populated context_scope (4 entries).
