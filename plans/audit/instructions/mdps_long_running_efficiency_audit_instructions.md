---
name: mdps_long_running_efficiency_audit_instructions
type: audit-instructions
epic: mtds_mdps_master
assigned_vm: vm-ml
tier: L1
last_updated: 2026-05-28
related_audit_instructions:
  - mtds_mdps_master_audit_instructions.md   # parent audit; this is a focused efficiency sub-audit
related_plans:
  - active/mdps_filter_pushdown_memory_audit_and_fix_2026_05_28.md       # tactical fixes already shipped
  - active/mdps_long_running_multi_shard_architecture_audit_2026_05_28.md # the multi-week refactor plan this audit informs
codex_ssots_to_check_drift_against:
  - codex/06-coding-standards/service-orchestration-patterns.md         # § 15 (codified 2026-05-28)
  - codex/06-coding-standards/cli-convention.md                          # § "Instrument Identity and CLI Granularity" (codified 2026-05-28)
  - codex/05-infrastructure/vm-tarball-deployment.md                     # invariant #10 (codified 2026-05-28)
  - codex/06-coding-standards/data-engine-selection.md                   # NEW (codified 2026-05-28)
  - codex/06-coding-standards/read-time-filter-pushdown.md               # NEW (codified 2026-05-28)
---

# MDPS Long-Running Efficiency — Audit Instructions

## Scope

Focused efficiency audit for the **market-data-processing-service** in the long-running multi-shard VM execution
shape. Built from operator-stated concerns 2026-05-28 EOD after the Phase 3.2 7-day backfill canary surfaced a 25 GB
per-day RSS floor that the tactical Phase 2.2 fix couldn't reach.

**This is NOT the broader MDPS audit** — that lives in
[`mtds_mdps_master_audit_instructions.md`](mtds_mdps_master_audit_instructions.md) and covers adapter parity, manifest
schema_version compliance, ADAPTER_FETCH_FAILED emissions, etc. This audit is specifically about MDPS performance,
memory, and architecture under the deployment shape we actually run: **one e2-standard-8 (32 GB) VM iterating many
(date × asset_group × data_type × venue × instrument) shards in one Python process**.

Findings land in `plans/audit/results/mdps_long_running_efficiency_audit_*_2026_05_28.md` — one finding per file when
they're substantive, or grouped by axis (state-inventory / engine-mixing / manifest-IO / concurrency / etc).

## Operator-stated concerns (the seed)

These are the four points the operator raised 2026-05-28 EOD. Each one is BOTH a finding to verify AND a starting
point for digging deeper. The audit must check whether each concern is real, document the surface area, and propose
the corresponding architectural change.

### Concern A — `_cleanup_after_day` MUST fire on every per-shard exit path, no exceptions

> "The cleanup should happen even if we are processing a single day for a single data type and single instrument."

Phase 3 of the sibling tactical plan landed the immediate fix (try/finally in `process_category` at
`orchestration_service.py:132+`, MDPS@dcd7416). The audit obligation is broader:

- **Inventory every code path that mutates per-shard state.** Not just the orchestrator — any module that allocates
  on a per-shard basis (data sinks, sample storage, candle service caches, the canonical_writer's manifest
  accumulator, the ResourceProfiler if it samples per-shard). Each of these needs to be in the `_cleanup_after_day`
  hook's reach OR documented as "lifetime = process" with rationale.
- **Verify the cleanup hook is exercised by EVERY CLI invocation shape**: single-day single-instrument, single-day
  single-data_type, multi-day full-asset-group, etc. The cleanup path being silently dead in the most-restricted
  invocation is exactly how the 2026-05-28 incident landed. Test in QG, not just empirically.
- **Map the gap between what `_cleanup_after_day` currently clears and the empirical 25 GB per-day floor.** The
  current hook clears `candle_processing_service.cache` + `sampling_service.cache` + runs `gc.collect()`. Empirical
  measurement post-MDPS@dcd7416 will tell us how much of the 25 GB those two caches actually own. Whatever the hook
  doesn't reach is a separate finding (likely the Polars/PyArrow arena retention from Concern D).

Codex: composes with [`service-orchestration-patterns.md`](../../codex/06-coding-standards/service-orchestration-patterns.md)
§ 15 (HARD RULE codified 2026-05-28); per-shard cleanup is now mandatory at code-review time.

### Concern B — CLI granularity: a single canonical instrument_id should be sufficient to scope one cell

> "An instrument_id is the last thing and it covers everything — which venue this instrument belongs to, which
> asset_group, and which data_type as well. By default the mode, start_date and end_date and asset group are needed,
> but we should be able to drill down into the finest shard which is the instrument_id."

The codex now defines this (cli-convention.md § "Instrument Identity and CLI Granularity"): the canonical form is
`VENUE:INSTRUMENT_TYPE:SYMBOL`; venue, instrument_type, and asset_group ARE derivable; data_type is independent and
still requires `--data-types`. The MDPS implementation doesn't match the codex yet — the scanner currently does
substring matching that doesn't even match the canonical form against blob paths.

Audit obligations:
- **Inventory every parameter the MDPS CLI accepts** (top-level args, env-var bridges in `_build_legacy_argv`,
  legacy `process` subparser flags). For each, classify it as `derivable-from-instrument-id` (should be optional when
  instrument-id is canonical), `independent` (always required), or `redundant` (should warn or error on conflicts).
- **Audit the filter parser** in `_collect_matching_parquet_blobs` against the codex contract. Does it parse
  `VENUE:INSTRUMENT_TYPE:SYMBOL`? Or only substring-match? Compare against the codex's reference parser implementation.
- **Verify single-cell drilldown semantics end-to-end.** A run with just
  `--instrument-ids BINANCE-FUTURES:PERPETUAL:BTCUSDT --data-types trades --start-date X --end-date X` should process
  EXACTLY one shard and exit. Today the CLI doesn't even accept this without redundant `--venues` because the parser
  is substring-based. Document the gap.
- **Cross-service impact**: instruments-service, MTDS, features-* services use similar `--instrument-ids` patterns.
  Do they have the same gap? If so, surface a workspace-wide finding pointing at the new codex rule.

### Concern C — The orchestrator design was built for one-VM-per-shard fan-out (legacy assumption)

> "The original idea was to spin up multiple VMs (in the range of thousands and even tens of thousands) to process one
> single day for one venue or per asset_group — but that is not a viable option as it costs more than a long running
> VM. So the flows you see are coming from that older design. I want you to audit those things."

The codex now documents the per-shard cleanup contract for multi-shard VMs ([`vm-tarball-deployment.md`](../../codex/05-infrastructure/vm-tarball-deployment.md)
invariant #10). The audit obligation is to surface every architectural decision that bakes in the old assumption:

- **State-inventory audit (THE central deliverable of this audit doc).** For every attribute on the orchestrator
  (`CandleOrchestrationService` + its mixins: `CandleOrchestrationScanner`, `OrchestrationSchedulingMixin`,
  `OrchestrationWorkersMixin`, `OrchestrationStateMixin`, `LiveOrchestrationMixin`, `BatchOrchestrationMixin`,
  `CandleOrchestrationBase`) and every module-level singleton it references, tabulate:
  ```
  (qualified_attr, type, lifetime_intent, lifetime_actual, reset_cost_to_recreate, who_owns_cleanup)
  ```
  `lifetime_intent` = the answer the original code assumed (likely "process exit" for most things).
  `lifetime_actual` = what we measured in the canary (the 25 GB-vs-87 MB reclaim gap is the empirical signal).
  Any row where intent ≠ actual is a finding.
- **Repeated work across shards.** Specifically: does MDPS re-read the 526 MB `availability_index.parquet` per-date?
  Per-data_type? Per-instrument? Each re-read is potentially 2-5 GB decompressed. If the manifest can be loaded once
  per VM lifecycle and reused across shards (with a per-shard-write invalidation), document it. If it can be replaced
  by a streaming / partial-index pattern, document THAT.
- **Per-instance state that should be per-shard (or vice versa).** Examples: per-asset_group `_data_sinks` dict
  belongs to the VM lifetime; per-date pandas frames belong to the shard lifetime. Are any of these mis-scoped?
- **The freshness check + manifest write loop.** Every per-shard write goes through `canonical_writer` which appends
  to the manifest. Every per-shard read calls `check_shard_freshness` which scans the manifest. For 16 days × 4
  instruments × 7 timeframes = 448 manifest scans + 448 manifest writes inside one VM. What's the cost? Is it
  amortising correctly?
- **Decision: subprocess-per-shard vs single-process vs process-pool.** The architectural audit plan
  [`mdps_long_running_multi_shard_architecture_audit_2026_05_28.md`](../active/mdps_long_running_multi_shard_architecture_audit_2026_05_28.md)
  Phase 1.1 enumerates the closed set. This efficiency audit's job is to provide the **evidence base** for picking
  one — the state inventory + the cost model. Don't pick the option in this audit doc; just produce the evidence.

### Concern D — Polars/Pandas conversion churn

> "What is the role of polars here? If it's just reading the dataframe and then converting into pandas dataframe and
> then all the processing is happening inside pandas, that is not the right design. Polars is capable of doing all the
> things that pandas does. If the role of polars is to just read the file then why is it like that? Are there any
> advantages of using it over pandas for file read? We can switch to pyarrow engine that pandas supports."

The codex now has [`data-engine-selection.md`](../../codex/06-coding-standards/data-engine-selection.md) (NEW,
codified 2026-05-28). The rule: pick one engine end-to-end; Polars→Pandas→Polars is a banned anti-pattern.

Audit obligations:
- **Engine inventory.** Tabulate every `pl.read_parquet`, `pd.read_parquet`, `.to_pandas()`, `pl.from_pandas()`,
  `pa.Table.*`, `parquet.write_*`, `.to_parquet()` callsite in MDPS source. Per row:
  ```
  (file:line, engine_in, engine_out, why_chosen, conversion_cost)
  ```
  Currently known: `_read_tick_data` (live_workers.py:449-479) goes `pl.read_parquet → .to_pandas() → return
  pandas`, then `_process_all_timeframes` re-enters polars for aggregation. There may be more.
- **Why each conversion exists.** For each `.to_pandas()` / `pl.from_pandas()` call, find the immediate consumer. Is
  there a polars-native (or pandas-native) replacement? Sometimes the conversion exists because a downstream library
  (UTL writer, candle_processing_service, sampling_service) only accepts one type — in which case the FIX is at the
  consumer, not at the converter.
- **What does the chosen end-to-end engine measurably save?** Run one instrument-day through pure-Polars (or
  pure-Pandas+PyArrow) end-to-end as a feasibility prototype. Measure peak RSS vs the current mixed-engine path. The
  number is the input to the architectural audit's Phase 2 decision.
- **Cross-service impact.** Same engine question for instruments-service, features-* services, batch-live-
  reconciliation-service. The codex rule applies workspace-wide; the migration order can be staged.

## Additional axes that came up while shipping the tactical fixes

The above four are the operator-seeded concerns. While shipping the tactical fixes 2026-05-28, the following adjacent
issues surfaced. The audit should also touch them so they don't slip:

### Axis E — pre-count vs processing scanner divergence

`process_handler.py:383` calls `orchestrator.list_instrument_files(...)` to compute `total_instruments` for the
progress tracker. This call passes `venues=` but NOT `instrument_ids=`. The processing scanner (called inside
`process_category`) passes both. So the operator sees "Listed 18 files" in the log even though only 4 will actually be
processed — misleading and slows operator debugging. Either pass `instrument_ids` to the pre-count, or change the
log to clarify "pre-count (venue-only scope): 18; will process after instrument_ids filter: 4". Trivial fix; not
shipped yet.

### Axis F — observability of memory state across shards

The current operator-visible signal for memory state is: (a) the `📉 date-boundary GC` log I added in Phase 2.2
(MDPS@0254531), (b) `BatchOrchestrationMixin: memory backpressure engaged at X%` when backpressure fires, (c) `💾
Memory after cleanup: N MB` from `_cleanup_after_day`. These are partial. A long-running VM should emit a structured
event (`SHARD_MEMORY_HIGH_WATER_MARK` or similar) at every shard boundary so the per-shard cost model can be measured
in production, not just in one-off canaries.

### Axis G — the chain-bundle fan-out path (`_iter_chain_symbol_dfs`)

For data_types like `options_chain` and `futures_chain`, one parquet contains many instruments. `live_workers.py:483-
570` (per the earlier audit's side findings) implements a per-symbol streaming pattern. This is the architecturally
correct shape and is in tension with the per-instrument-file pattern used elsewhere. The audit should document this
as an existing working reference for "the right shape", and flag that the rest of MDPS doesn't follow it.

### Axis H — adapter-registry-driven dispatch

`CandleAdapterRegistry` (referenced in `process_handler.py:317`) routes each (asset_group, data_type) to a candle
adapter. Auditing: which adapters exist, which are missing (treated as bypass), which load reference data, which hold
state across calls. Adapter-side caches may contribute to the 25 GB floor.

## Audit deliverables

One markdown findings doc per axis, all in `plans/audit/results/`, all dated `2026_05_28`:

- `mdps_long_running_state_inventory_2026_05_28.md` (Concerns A + C) — the canonical state-inventory table + the
  intent-vs-actual gap.
- `mdps_long_running_engine_mixing_2026_05_28.md` (Concern D) — engine inventory + the feasibility-prototype RSS
  measurement.
- `mdps_long_running_cli_granularity_2026_05_28.md` (Concern B) — CLI parameter inventory + parser audit + the
  cross-service impact.
- `mdps_long_running_manifest_io_2026_05_28.md` (Concern C deep-dive) — manifest read/write patterns + per-shard
  cost.
- `mdps_long_running_concurrency_2026_05_28.md` (orchestration cost model) — ThreadPoolExecutor + backpressure
  behavior + the case for/against subprocess-per-shard.
- `mdps_long_running_observability_2026_05_28.md` (Axis F) — what memory telemetry exists + what should exist.
- `mdps_long_running_axes_e_g_h_2026_05_28.md` (Axes E + G + H) — the smaller adjacent findings, single doc.

Each findings doc opens with `## What I read` (the file:line + codex refs the audit grounded on) and closes with
`## Recommended next step` (concrete enough that an implementer can scope a PR from it). Findings docs are
**read-only artefacts** — do not patch MDPS from them in this pass. Patches belong in the architectural audit plan
(`mdps_long_running_multi_shard_architecture_audit_2026_05_28.md`) which schedules them across Phases 1-4.

## Triggers

- 2026-05-28 EOD: initial run (this audit's creation moment).
- After the architectural audit plan's Phase 1 lands a decision: re-run the state inventory to confirm the decision
  matches the empirical evidence.
- Any time the deployment shape changes (e.g. moving from one e2-standard-8 to a process-pool model, or back to
  one-VM-per-shard fan-out).

## Anti-patterns to flag in audit results

- Findings doc that says "consider X" without naming the file:line where X lives in the current code.
- Recommendation that contradicts a codex doc landed 2026-05-28 (the codex audit confirmed 0/4 contradictions; new
  drift would be a regression).
- "We should refactor everything" — the architectural plan is for that. Findings docs are for evidence + bounded
  recommendations.
- Sub-agent fabrication: any file:line ref that doesn't exist on the current `live-defi-rollout` tip is review-
  blocking.
