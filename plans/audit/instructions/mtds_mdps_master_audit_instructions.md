---
name: mtds_mdps_master_audit_instructions
type: audit-instructions
epic: mtds_mdps_master
assigned_vm: vm-ml
tier: L1
last_updated: 2026-06-01
related_plans:
  - active/mdps_filter_pushdown_memory_audit_and_fix_2026_05_28.md # tactical fixes shipped 2026-05-28
  - active/mdps_long_running_multi_shard_architecture_audit_2026_05_28.md # architectural refactor track
codex_ssots_to_check_drift_against:
  # Long-standing correctness contracts:
  - codex/04-architecture/instruments-service-as-ssot-for-mtds.md
  - codex/02-data/availability-manifest-and-data-status.md
  - codex/05-infrastructure/gcs-object-operations.md
  # Efficiency contracts codified 2026-05-28:
  - codex/06-coding-standards/service-orchestration-patterns.md # § 15 batch-service lifecycle
  - codex/06-coding-standards/cli-convention.md # § Instrument Identity + CLI Granularity
  - codex/05-infrastructure/vm-tarball-deployment.md # invariant #10 per-shard cleanup
  - codex/06-coding-standards/data-engine-selection.md # NEW
  - codex/06-coding-standards/read-time-filter-pushdown.md # NEW
---

# MTDS / MDPS Master — Audit Instructions

The single canonical audit doc for everything in the MTDS + MDPS surface. Two audit modes share this doc:

| Mode                                                            | What it checks                                                                   | When to run                                                                                          |
| --------------------------------------------------------------- | -------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| **[Correctness](#mode-1--correctness-audit)**                   | Adapter parity, manifest schema, honest absence, batch=live invariants           | Weekly + per-adapter ship + after writegate phase changes + on manifest divergence alerts            |
| **[Efficiency](#mode-2--efficiency-audit-codified-2026-05-28)** | Memory pathology, engine choice, CLI granularity, per-shard state, observability | After any OOM/hang incident; before any execution-model decision; when the per-day RSS floor changes |

Both modes write findings to `plans/audit/results/` under the prescribed filenames. New findings are appended to the
relevant mode's checklist as they surface (see [§ Extending this doc](#extending-this-doc)).

## Epic Scope

Market Tick Data Service (MTDS) all adapters (23 batch + 18 live as of 2026-05-20) and MDPS candle processing + the
shared writegate + raw market data pipeline. Spans `market-tick-data-service/`, `market-data-processing-service/`, the
two services' tarballs in `deployment-service/scripts/vm/`, and the shared `_index/availability_index.parquet` write
path in both `market-data-tick-{cefi|tradfi|defi|sports|prediction}-*` buckets.

Key invariants: QG STEPS 5.64 (cluster validation), 5.66 (per-VM shard isolation), 5.69 (bucket name SSOT), honest
absence taxonomy, batch=live adapter parity, single-engine discipline, per-shard cleanup.

---

# Mode 1 — Correctness Audit

## Triggers

- Weekly (minimum cadence)
- After each new MTDS adapter ships
- After any writegate phase change
- When A3 manifest divergence scan shows `DIVERGENT_EMPTY` or `MISSING_EXPECTED`
- After VM tarball deployment to update batch adapter coverage

## Checklist

- [ ] (a) **ADAPTER_FETCH_FAILED emitted**: every adapter emits `ADAPTER_FETCH_FAILED` event on all error paths. Grep:
      `rg "ADAPTER_FETCH_FAILED" market-tick-data-service/ --include="*.py"` — count vs adapter file count; every
      handler file should have at least one hit

- [ ] (b) **Cluster validation at record_captured() — QG STEP 5.64**: mandatory `cluster_*` kwargs present at every
      `record_captured()` call for bundled data_types. Run: `bash scripts/quality-gates/cluster_validation.sh` (or
      equivalent QG step)

- [ ] (c) **Per-VM shard isolation — QG STEP 5.66**: `VM_NAME` + `MANIFEST_PER_VM_SHARDS=true` wired. Run: relevant QG
      step; grep for `MANIFEST_PER_VM_SHARDS` in VM launch scripts

- [ ] (d) **Bucket lookup via resolve_bucket_name() — QG STEP 5.69**: no inline `gs://` f-strings. Run:
      `bash scripts/quality-gates/no_inline_bucket_fstrings.sh` (or equivalent). Grep:
      `rg "gs://" market-tick-data-service/ --include="*.py"` — should be 0 hits in business logic

- [ ] (e) **Batch adapter count == live adapter count**: parity across all asset_groups. Run:
      `python3 plans/audit/results/a6_batch_live_adapter_parity.py` — report any gaps

- [ ] (f) **EmptyConfirmedReason for empty returns**: all adapters that can return empty data use a typed reason from
      `UAC EMPTY_CONFIRMED_REASONS`; no blank strings. Grep:
      `rg 'record_empty\(reason=""' market-tick-data-service/ --include="*.py"` — should be 0 hits

- [ ] (g) **Manifest schema_version in actual data**: read actual `schema_version` column from a sample of prod manifest
      rows (not the code constant). Must be ≥ 95% at current version (v8 as of 2026-05-20). Run:
      `python3 plans/audit/results/a4_manifest_v8_compliance.py` — check actual distribution

- [ ] (h) **No subprocess gsutil/gcloud for per-object ops**: all per-object GCS operations use UTL library. Grep:
      `rg "subprocess.*gsutil|subprocess.*gcloud" market-tick-data-service/ --include="*.py"` — should be 0 hits

- [ ] (i) **Fetch-failure → `attempted_failed`, never `empty_confirmed` — PER-ADAPTER swallow audit (codified
      2026-06-01)**: every MTDS adapter/handler doing external I/O (RPC/REST/subgraph/SDK) must route a fetch error to
      `record_failed` (`attempted_failed`), NOT swallow it (`except: … return []/None`) into a `record_empty`
      (`empty_confirmed`) — a swallowed timeout/DNS/RPC error mislabeled as honest-empty corrupts the manifest + every
      downstream consumer. Grep:
      `rg -U "except\b[^\n]*:\s*\n(\s*[^\n]*\n)?\s*return (\[\]|None|\{\}|pd\.DataFrame\(\))" market-tick-data-service/ --include="*.py" -g '!*test*'`
      then read each adapter's outer fetch try/except. **Closed per-adapter checklist — check EVERY adapter.** Fix =
      re-raise / typed failure sentinel so the caller's `record_failed` fires. 2026-06-01: fixed `lst_rates_handler`
      L697 + `oracle_prices_handler` L820/L948; OPEN `lending_indices_handler` L989. Full spec:
      `defi_master_audit_instructions.md` item (aa).

- [ ] (j) **Source provenance stamped at write time — UNIVERSAL (codified 2026-06-01, operator)**: **every** MTDS
      adapter/handler MUST pass a non-blank `source=` (a closed-set string from `SOURCE_PRIORITY`) to `record_captured`
      — on every cell, all asset groups, **even single-source ones** (operator: "I may find an alternative for Tardis,
      so it's the same issue" — stamp now so a future source swap is distinguishable). NOT gated on cardinality. Today
      only `category=="tradfi"` is gated; cefi (`tardis`)/defi/sports/prediction write `source=""`, and DeFi handlers
      route via `DefiManifestRecorder` → legacy `ManifestWriter.add()` which drops `source` entirely (defi multi-source
      cells additionally collapse last-write-wins). Verify by reading ACTUAL prod rows — **RED on any blank `source`**.
      Grep callsites: `rg "record_captured\(" market-tick-data-service/ --include="*.py" -A8 | rg "source="`. SSOT:
      `plans/active/data_source_provenance_all_asset_groups_2026_06_01.md`; manifest-schema home: `manifest_master` item
      (i).

### Batch vs Live Parity

- (batch-live) **Batch adapter output**: confirm each adapter in scope produces manifest rows with
  `capture_status=captured` for a known date range using the batch invocation path (`--mode batch`). Run against mock
  data if real upstream is unavailable (`CLOUD_MOCK_MODE=true`).
- (live-adapter) **Live adapter parity**: for each batch adapter, confirm the live adapter exists, accepts the same
  schema, and emits `available_at` at write-time (not read-time). Confirm no `DIVERGENT_EMPTY` rows for live mode.
- (mock-upstream) **Mock upstream pattern**: audits for this data layer MUST be runnable without hitting real APIs.
  Document fixture paths and `CLOUD_MOCK_MODE=true` invocations so downstream services can be audited independently.

## Success Criteria

- All correctness checklist items (a)–(j) GREEN
- Multi-source cells stamp `source` at write time (item j) — zero blank `source` on any `(asset_group, data_type)` with
  a multi-entry `SOURCE_PRIORITY`, read from actual prod rows
- `a6_batch_live_adapter_parity.py` shows 100% parity (batch count == live count per venue per asset_group)
- A3 manifest divergence: zero `MISSING_EXPECTED` and zero `DIVERGENT_EMPTY`
- QG exits 0 for market-tick-data-service

## Output Format (Correctness)

Result file at `plans/audit/results/mtds_mdps_master_audit_YYYY_MM_DD.md`. Same structure as per `../README.md`.

---

# Mode 2 — Efficiency Audit (codified 2026-05-28)

## Scope

Focused efficiency audit for **market-data-processing-service** in the long-running multi-shard VM execution shape.
Built from operator-stated concerns 2026-05-28 EOD after the Phase 3.2 7-day backfill canary surfaced a 25 GB per-day
RSS floor that the tactical cleanup-wiring fix at MDPS@dcd7416 only reduced to 15.7 GB.

The deployment shape this audit interrogates: **one e2-standard-8 (32 GB) VM iterating many
`(date × asset_group × data_type × venue × instrument)` shards in one Python process**. The orchestrator was originally
written under the one-VM-per-shard fan-out assumption; the actual deployment moved to long-running multi-shard but the
orchestrator state model didn't follow, hence the per-day floor.

## Triggers

- Any MDPS OOM, deadlock, or per-day RSS floor > 16 GB on a 32 GB box
- Before any execution-model decision in the architectural plan
- After the architectural plan's Phase 1 lands a decision (re-run the state inventory to confirm match)
- Any time the deployment shape changes (e.g. moving from one e2-standard-8 to a process-pool model)
- Workspace-wide engine-discipline drift (a service starts mixing Polars + Pandas mid-pipeline)

## Operator-stated concerns (the seed)

These are the four points the operator raised 2026-05-28 EOD. Each one is BOTH a finding to verify AND a starting point
for digging deeper.

### Concern A — `_cleanup_after_day` MUST fire on every per-shard exit path, no exceptions

> "The cleanup should happen even if we are processing a single day for a single data type and single instrument."

Tactical fix shipped (try/finally in `process_category` at `orchestration_service.py:132+`, MDPS@dcd7416). Audit
obligations:

- **Inventory every code path that mutates per-shard state.** Not just the orchestrator — any module that allocates on a
  per-shard basis (data sinks, sample storage, candle service caches, the canonical_writer's manifest accumulator, the
  ResourceProfiler if it samples per-shard). Each of these needs to be in the `_cleanup_after_day` hook's reach OR
  documented as "lifetime = process" with rationale.
- **Verify the cleanup hook is exercised by EVERY CLI invocation shape**: single-day single-instrument, single-day
  single-data_type, multi-day full-asset-group, etc. The cleanup path being silently dead in the most-restricted
  invocation is exactly how the 2026-05-28 incident landed. Test in QG, not just empirically.
- **Map the gap between what `_cleanup_after_day` currently clears and the empirical per-day floor.** The current hook
  clears `candle_processing_service.cache` + `sampling_service.cache` + runs `gc.collect()`. Empirical measurement:
  post-MDPS@dcd7416 the residue is still 15.7 GB. Whatever the hook doesn't reach is a separate finding (likely the
  Polars/PyArrow arena retention from Concern D).

Codex: composes with `codex/06-coding-standards/service-orchestration-patterns.md` § 15 (HARD RULE codified 2026-05-28).

### Concern B — CLI granularity: a single canonical instrument_id should be sufficient to scope one cell

> "An instrument_id is the last thing and it covers everything — which venue this instrument belongs to, which
> asset_group, and which data_type as well. By default the mode, start_date and end_date and asset group are needed, but
> we should be able to drill down into the finest shard which is the instrument_id."

The codex now defines this (`cli-convention.md` § "Instrument Identity and CLI Granularity"): canonical form
`VENUE:INSTRUMENT_TYPE:SYMBOL`; venue + instrument_type + asset_group are derivable; data_type is independent. The MDPS
implementation doesn't match — the scanner does substring matching that fails on the canonical form silently.

Audit obligations:

- **Inventory every parameter the MDPS CLI accepts** (top-level args, env-var bridges in `_build_legacy_argv`, legacy
  `process` subparser flags). For each, classify as `derivable-from-instrument-id`, `independent`, or `redundant`.
- **Audit the filter parser** in `_collect_matching_parquet_blobs` against the codex contract. Does it parse
  `VENUE:INSTRUMENT_TYPE:SYMBOL`?
- **Verify single-cell drilldown semantics end-to-end.** A run with just
  `--instrument-ids BINANCE-FUTURES:PERPETUAL:BTCUSDT --data-types trades --start-date X --end-date X` should process
  EXACTLY one shard and exit.
- **Cross-service impact**: instruments-service, MTDS, features-\* services use similar `--instrument-ids` patterns.
  Surface workspace-wide drift.

### Concern C — The orchestrator design was built for one-VM-per-shard fan-out (legacy assumption)

> "The original idea was to spin up multiple VMs (in the range of thousands and even tens of thousands) to process one
> single day for one venue or per asset_group — but that is not a viable option as it costs more than a long running VM.
> So the flows you see are coming from that older design. I want you to audit those things."

The codex now documents the per-shard cleanup contract for multi-shard VMs (`vm-tarball-deployment.md` invariant #10).
Audit obligations:

- **State-inventory audit.** For every attribute on the orchestrator (`CandleOrchestrationService` + its mixins) and
  every module-level singleton it references, tabulate
  `(qualified_attr, type, lifetime_intent, lifetime_actual, reset_cost, who_owns_cleanup)`. Any row where intent ≠
  actual is a finding.
- **Repeated work across shards.** Does MDPS re-read the 526 MB `availability_index.parquet` per-date? Per-data_type?
  Per-instrument? Each re-read is 2-5 GB decompressed.
- **Per-instance state that should be per-shard (or vice versa).** Examples: per-asset_group `_data_sinks` dict belongs
  to the VM lifetime; per-date pandas frames belong to the shard lifetime.
- **The freshness check + manifest write loop.** Every per-shard write goes through `canonical_writer` which appends to
  the manifest. For 16 days × 4 instruments × 7 timeframes = 448 manifest scans + 448 writes per VM.
- **Decision evidence for execution model.** Provide the cost-model evidence for the architectural plan's Phase 1.1
  decision (subprocess-per-date / subprocess-per-shard / in-process / process-pool). Don't pick — just evidence.

### Concern D — Polars/Pandas conversion churn

> "What is the role of polars here? If it's just reading the dataframe and then converting into pandas dataframe and
> then all the processing is happening inside pandas, that is not the right design. Polars is capable of doing all the
> things that pandas does. We can switch to pyarrow engine that pandas supports."

The codex now has `data-engine-selection.md` (codified 2026-05-28). Rule: pick one engine end-to-end;
Polars→Pandas→Polars is a banned anti-pattern.

Audit obligations:

- **Engine inventory.** Tabulate every `pl.read_parquet`, `pd.read_parquet`, `.to_pandas()`, `pl.from_pandas()`,
  `pa.Table.*`, `parquet.write_*`, `.to_parquet()` callsite. Per row:
  `(file:line, engine_in, engine_out, why_chosen, conversion_cost)`.
- **Why each conversion exists.** For each `.to_pandas()` / `pl.from_pandas()`, find the immediate consumer. If a
  downstream library only accepts one type, the FIX is at the consumer.
- **What does the chosen end-to-end engine measurably save?** Run one instrument-day through pure-Polars end-to-end as a
  feasibility prototype. Measure peak RSS vs the current mixed-engine path.
- **Cross-service impact.** Same engine question for instruments-service, features-\* services, batch-live-
  reconciliation-service.

## Additional axes (E – H, found while shipping the 2026-05-28 tactical fixes)

### Axis E — pre-count vs processing scanner divergence

`process_handler.py:383` calls `orchestrator.list_instrument_files(...)` for the progress tracker. It passes `venues=`
but not `instrument_ids=`. The processing scanner inside `process_category` passes both. So the log reports "Listed 18
files" while only 4 are processed. Misleading for narrow-scope runs.

### Axis F — observability of memory state across shards

Existing memory signals are partial: `📉 date-boundary GC` log (MDPS@0254531),
`BatchOrchestrationMixin: memory backpressure engaged at X%` (reactive at 85%), `💾 Memory after cleanup: N MB` from
`_cleanup_after_day`. A long- running VM should emit structured events at every shard boundary so the per-shard cost
model is measured in production, not just in canaries.

### Axis G — the chain-bundle fan-out path (`_iter_chain_symbol_dfs`)

For `options_chain` / `futures_chain`, one parquet contains many instruments. `live_workers.py:483-570` implements a
per-symbol streaming pattern. This is the architecturally correct shape and is in tension with the per-instrument- file
pattern used elsewhere. Audit documents this as an existing reference for "the right shape".

### Axis H — adapter-registry-driven dispatch

`CandleAdapterRegistry` (`process_handler.py:317`) routes each `(asset_group, data_type)` to a candle adapter. Audit:
which adapters exist, which are unregistered (treated as bypass), which load reference data, which hold state across
calls. Adapter-side caches were the suspicion before the 2026-05-28 audit; finding H confirmed all 21 stateless.

## Efficiency Checklist

This is the running list. Tick items as the corresponding finding ships a fix. **Add new items at the bottom as new
findings surface.**

- [x] ✅ (E1) **Pre-count scanner passes `instrument_ids`**: at `process_handler.py:383-388`, the
      `list_instrument_files` pre-count call should accept `instrument_ids=` so the log line and tracker total reflect
      the actual scope. Findings doc: `mdps_long_running_axes_e_g_h_2026_05_28.md` § Axis E. — MDPS@a5e1dac 2026-05-28

- [x] ✅ (E2) **Manifest reuse across the per-timeframe re-check**: at `orchestration_service.py:166-211`, the second
      `check_shard_freshness` call re-reads the 526 MB manifest. Either pass the already-loaded DataFrame or skip the
      re-read entirely. Findings doc: `mdps_long_running_manifest_io_2026_05_28.md` § "The double freshness check". —
      MDPS@569040a 2026-05-28 (option B3: single merged-axis check, missing/stale partitioned locally for log parity;
      tests in `tests/unit/test_process_category_single_freshness_check.py` pin call_count==1 across fresh/stale/missing
      paths)

- [x] ✅ (E3) **Canonical instrument_id parser**: replace the substring matcher in
      `orchestration_scanner.py:_collect_matching_parquet_blobs` with the structured parser specified in
      `codex/06-coding-standards/cli-convention.md` § "Instrument Identity and CLI Granularity". Add regression tests
      that pin canonical-form behaviour. Findings doc: `mdps_long_running_cli_granularity_2026_05_28.md`. — MDPS@9ea08c8
      2026-05-28 — added `parse_canonical_instrument_id()` + `blob_matches_canonical_instrument_id()` +
      `blob_matches_any_instrument_id()` in `path_parsing.py`; wired into `_collect_matching_parquet_blobs` (formerly
      substring-only). 4 new regression tests + 38/38 scanner+scheduling unit tests green.

- [ ] (E4) **Extend `_cleanup_after_day` to clear all state-inventory attrs** flagged in the audit (per-asset_group
      `_data_sinks`, instruments DataFrame, manifest read buffer if cached). Call
      `pyarrow.default_memory_pool().release_unused()` at the end so the PyArrow arena hand-off happens. Findings doc:
      `mdps_long_running_state_inventory_2026_05_28.md` § "Recommended next step".

- [~] (E5) **Pure-Polars `_read_tick_data` → `_process_all_timeframes` → writer chain**: **Stages 1 + 2 + 3 + 3.5
  shipped ✅** — Stage 4 + 5 outstanding (3.6 + 3.8 self-block on Stage 4). - Stage 1 — MDPS@591120b 2026-05-28:
  `_read_tick_data` returns `pl.DataFrame`; data_type filter polars-native via `.filter(pl.col(...).is_in(...))`;
  boundary conversion to pandas at `_eager_preprocess_and_recover_metadata` entry. - Stage 1.3 — MDPS@ceb7a12
  2026-05-28: `_iter_chain_symbol_dfs` yields `pl.DataFrame` (dropped `.collect().to_pandas()`); `.to_pandas()` now in
  `_process_chain_bundle_streaming` at adapter boundary. Test assertions updated (n_unique/[0] polars equivalents). -
  Stage 1.4 — MDPS@c24b17c 2026-05-28: `GCSDataSource.read_tick_data` + `LiveDataSource.read_tick_data` + abstract base
  `DataSource.read_tick_data` return `pl.DataFrame`. Pandas fallback via `pl.from_pandas(pd.read_parquet(...))` keeps
  polars contract. test_data_source.py updated. - Stage 2a — MDPS@f364539 2026-05-28:
  `cefi/trades_adapter._compute_grouped_stats_polars` no longer does `core.to_pandas().set_index(...)` table-level
  roundtrip; per-column polars→numpy→pd.Series construction with shared `pd.Index`. - Stage 2b — MDPS@3dcc062
  2026-05-28: `prediction/trades_adapter.py:184` switched from `pd.read_parquet` to `pl.read_parquet` for lifecycle data
  load. - Stage 2 audit: only 2 of 18 adapters touched (cefi/trades + prediction/trades — both done); other 16 adapters
  use pure pandas internally with no polars round trips, so they're untouched in this stage. - Stage 3a —
  unified-api-contracts@3814249 2026-05-28: `CandleOutput.to_polars()` added in UAC (mirrors `to_dataframe()`); polars
  dep added; unit tests for empty + populated cases. - Stage 3b — MDPS@6e61cfe 2026-05-28: all 5 `to_dataframe()` sites
  in live_workers + 2 in candle_generator switched to `to_polars()`; `_inject_passthrough_columns` polarised
  (`with_columns(pl.lit(...).alias(col))`); `_emit_instrument_processed_event` polarised
  (`get_column().is_not_null().sum()`); `pd.concat`→`pl.concat`, `sort_values`→`sort`, `.empty`→`.is_empty()`. The
  polars→pandas boundary now sits at a single seam in `candle_write_mixin._write_candles` (and at 4 streaming-write call
  sites for the chain-bundle path) — canonical_writer.write_candle_parquet keeps pandas (plan's lower-risk hedge). 10
  unit tests updated to polars fixtures; 0 basedpyright regressions; 0 new test failures. - Stage 3.5 — MDPS@5e50b7d
  2026-05-28: `StorageDispatchWorker.write` signature flipped to `pl.DataFrame` + `df.write_parquet` (polars native);
  `ParquetSchemaWorker.validate` accepts polars OR pandas (collapses internally for UTL `ParquetSchemaEnforcer`);
  `OrchestrationCoordinator.process_batch` boundary conversion removed since downstream workers now accept polars
  natively. 3.4 audit confirmed `orchestration_writer.py` helpers all sit downstream of the `_write_candles` seam — no
  code change. - Stage 3.5 cleanup — MDPS@febcb3b 2026-05-28: per workspace rule "Delete deprecated code. No parallel
  code paths" (universal.md), removed the abandoned (B) thin-coordinator scaffold: `OrchestrationCoordinator` +
  `CandleGeneratorWorker` + `ParquetSchemaWorker` + `StorageDispatchWorker` plus their four unit-test files. None were
  reachable from any production entry point. The (B) scaffold deliberately omitted every workspace HARD RULE the
  production write chain enforces (manifest emission, honest absence, UAC SchemaContract, emission policy, cluster
  validation, chain-bundle streaming, Category D, VIX gap, etc.). 1269 lines removed, 20 added.
  `OrchestrationWorkersMixin` (production composition shim used by `CandleOrchestrationWriter`) trimmed + kept.

      Stage 4 + 5 per [`plans/active/mdps_pure_polars_migration_2026_05_28.md`](../../active/mdps_pure_polars_migration_2026_05_28.md)
      finish the chain (Stage 4: aggregation calculators — `fast_candle_aggregation.py` 36 pandas-ops +
      `timeframe_candles.py` 48 pandas-ops; Stage 5: long-tail + hidden-pandas-fallback cleanup). Items 3.6
      (remove the Stage-1 boundary `.to_pandas()`) + 3.8 (benchmark re-run) self-block on Stage 4 landing.
      Findings doc: `mdps_long_running_engine_mixing_2026_05_28.md` § "Feasibility prototype recommendation".

- [ ] (E6) **Structured memory events**: add `SHARD_STARTED`, `SHARD_COMPLETED`, `MANIFEST_LOAD_BYTES`,
      `INSTRUMENTS_LOAD_ROWS`, promote `📉 date-boundary GC` to a structured `DATE_BOUNDARY_GC` event, add
      `BACKPRESSURE_DEADLOCK_RISK` proactive signal. Findings doc: `mdps_long_running_observability_2026_05_28.md` §
      "Recommended structured events".

- [ ] (E7) **Execution-model decision evidence**: the cost-model table in `mdps_long_running_concurrency_2026_05_28.md`
      is the evidence base for the architectural plan's Phase 1.1 decision. Re-confirm the table's numbers after E1-E5
      land.

- [ ] (E8) **Chain-bundle streaming as the architectural reference pattern**: any future MDPS refactor of the per-
      instrument-file path should follow the shape of `_iter_chain_symbol_dfs` (`live_workers.py:483-570`). Findings
      doc: `mdps_long_running_axes_e_g_h_2026_05_28.md` § Axis G.

- [ ] (E9) **Per-shard memory regression test in QG**: a canary VM in CI that runs a small narrow-scope backfill and
      asserts peak RSS < threshold (threshold = whatever the post-E5 measurement establishes). Findings doc:
      `mdps_long_running_observability_2026_05_28.md` § "QG / regression-test recommendation".

## Audit Deliverables (Mode 2)

One markdown findings doc per axis, all in `plans/audit/results/`. The 2026-05-28 run produced:

| #   | Findings doc                                         | Covers                                               |
| --- | ---------------------------------------------------- | ---------------------------------------------------- |
| 1   | `mdps_long_running_state_inventory_2026_05_28.md`    | Concerns A + C — central state-inventory table       |
| 2   | `mdps_long_running_engine_mixing_2026_05_28.md`      | Concern D — engine inventory + feasibility prototype |
| 3   | `mdps_long_running_cli_granularity_2026_05_28.md`    | Concern B — CLI parameter inventory + parser audit   |
| 4   | `mdps_long_running_manifest_io_2026_05_28.md`        | Concern C deep-dive — manifest read/write patterns   |
| 5   | `mdps_long_running_concurrency_2026_05_28.md`        | Execution-unit cost model                            |
| 6   | `mdps_long_running_observability_2026_05_28.md`      | Axis F — memory telemetry                            |
| 7   | `mdps_long_running_axes_e_g_h_2026_05_28.md`         | Axes E + G + H — small adjacent findings             |
| ★   | `mdps_long_running_efficiency_SUMMARY_2026_05_28.md` | Operator-readable rollup                             |

Each findings doc opens with `## What I read` (file:line + codex refs the audit grounded on) and closes with
`## Recommended next step` (concrete enough that an implementer can scope a PR from it).

## Anti-patterns to flag in efficiency audit results

- Findings doc that says "consider X" without naming the file:line where X lives in the current code.
- Recommendation that contradicts a codex doc landed 2026-05-28 (codex audit confirmed 0/4 contradictions; new drift
  would be a regression).
- "We should refactor everything" — the architectural plan is for that. Findings docs are evidence + bounded
  recommendations.
- Sub-agent fabrication: any file:line ref that doesn't exist on the current `live-defi-rollout` tip is review-
  blocking.

---

# Extending this doc

This doc is the single canonical MDPS / MTDS audit reference. When new findings surface (in any future incident, canary,
or operator concern), add them here rather than spinning up new audit-instructions files.

How to add:

- **New Correctness item**: append to the Mode 1 Checklist as `(i)`, `(j)`, etc. Provide the grep / script command that
  proves the item passes.
- **New Efficiency item**: append to the Mode 2 Efficiency Checklist as `(E10)`, `(E11)`, etc. Cite the findings doc in
  `plans/audit/results/` that motivates it.
- **New Concern (operator-stated)**: add a `### Concern <Letter>` subsection in Mode 2 under "Operator-stated concerns"
  with the operator quote + audit obligations bullets. Use the next letter (E ran out — extend the alphabet or use
  `Concern I`, `Concern J`).
- **New Axis (internally-surfaced)**: add a `### Axis <Letter>` subsection in Mode 2 under "Additional axes" with a
  short description + the findings-doc filename it produces.
- **New Codex SSOT**: add the path to the frontmatter `codex_ssots_to_check_drift_against` list. Future audits will
  cross-reference automatically.
- **New trigger condition**: add to the relevant mode's "Triggers" list.

Avoid:

- Creating a parallel `_v2` or `_long_running_*` instructions doc — that recreates the fragmentation we just merged
  away. There is ONE master audit-instructions per epic; the table at the top distinguishes audit modes within it.
- Letting a findings doc drift from its referenced checklist item. The checklist item is the contract; the findings doc
  is the evidence.

## Linked Results

| Date       | Result file                                                          | Status                                                                      |
| ---------- | -------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| 2026-05-28 | `mdps_long_running_efficiency_SUMMARY_2026_05_28.md` (+ 7 axis docs) | Mode 2 first run; checklist items E1–E9 unticked, waiting on implementation |
