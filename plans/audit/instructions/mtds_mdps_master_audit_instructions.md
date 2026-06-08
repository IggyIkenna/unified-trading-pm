---
name: mtds_mdps_master_audit_instructions
type: audit-instructions
epic: mtds_mdps_master
assigned_vm: vm-ml
tier: L1
last_updated: 2026-06-03
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

> **🔄 ALIGNED 2026-06-08 — pre-apply readiness audit + source-aware/Era-B model (SSOT wins where this differs).** The
> MTDS migrators/rebuilds/readers and MDPS scanner are now source-aware — `pipeline_mode={mode}_{source}[_{transport}]`
> in BOTH the path key and the column (not coarse `batch`), with populated `source` and `transport` columns, Era-B
> (`options_chain`/`futures_chain` as instrument*type plus `data_type=trades`), and readers that prefix-match the
> `pipeline_mode=batch*\*`partition. SSOT =`canonical_form_cross_service_audit_checklist.md`(**CF-1…CF-14**) and the **①–⑫ pre-apply readiness audit** in`plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md`(esp. ① migrator source-aware + Era-B, ⑤ reader prefix-match, ⑨ source-aware, ⑩ Era-B on-disk, ⑪ batch=live). Any text below assuming coarse`pipeline_mode=batch`, `data_type=options_chain`,
> or exact-coarse reader probes is STALE — audit against the SSOT.

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

- [ ] (k) **Per-venue acquisition-METHOD registry + verification (codified 2026-06-03)**: items (a)–(j) prove a cell is
      _recorded_ honestly; this item proves the _fetch itself_ is the right + complete method for every live venue ×
      data_type — the "which API / method per venue" dimension. Expected-method SSOT =
      `codex/02-data/mtds-data-source-coverage-matrix.md` (the `adapter (live / batch)` column) +
      `codex/02-data/mtds-download-api.md` + `codex/02-data/defi-venue-protocol-catalogue.md`. For **every** venue in
      the coverage matrix, read the adapter/handler and verify, **per data_type** (classify each mismatch
      `aligned`/`codex-stale`/`code-bug` per the drift-register method): (1) **endpoint match** — the actual REST
      endpoint / RPC method / subgraph query / WebSocket channel called matches the documented source (Tardis bulk CSV,
      CCXT public path, venue WS, The Graph gateway + `subgraph_id`, Solana RPC / Helius, Drift Velocity Data API, S3
      archive, …). (2) **completeness mechanics** — pagination / full-history reachability is implemented (The Graph
      1000-row page + `skip`/timestamp cursor; Tardis per-day coverage; Velocity API paging; WS gap-backfill on
      reconnect) so a backfill cannot silently truncate; rate-limit + retry/backoff present; concurrency caps wired
      (`MAX_WORKERS`). (3) **auth provenance** — every credentialled venue reads its key via Secret Manager /
      `ApiKeyReloader`, never `os.getenv()`; public venues declare no key. (4) **no stub-emit** — a data_type the matrix
      says the venue produces is actually fetched, not a scaffold returning `[]` / empty (composes with item (i) swallow
      audit + `defi_master` item (n) venue/capability consistency). **Deliverable**: a per-venue table
      `venue | data_type | documented source | code endpoint/method | pagination? | rate-limit/retry? | auth source | emits-real-data? | verdict`.
      GREEN = every live venue × data_type matches the matrix with pagination + rate-limit + SM-auth verified and zero
      stub-emit. Cross-ref: `defi_master` (Solana basis MVP source-of-truth note — Drift Velocity API), `cefi_master`
      (Tardis-vs-venue-WS).

### Batch vs Live Parity

- (batch-live) **Batch adapter output**: confirm each adapter in scope produces manifest rows with
  `capture_status=captured` for a known date range using the batch invocation path (`--mode batch`). Run against mock
  data if real upstream is unavailable (`CLOUD_MOCK_MODE=true`).
- (live-adapter) **Live adapter parity**: for each batch adapter, confirm the live adapter exists, accepts the same
  schema, and emits `available_at` at write-time (not read-time). Confirm no `DIVERGENT_EMPTY` rows for live mode.
- (mock-upstream) **Mock upstream pattern**: audits for this data layer MUST be runnable without hitting real APIs.
  Document fixture paths and `CLOUD_MOCK_MODE=true` invocations so downstream services can be audited independently.

## Canonical-form cross-service audit coverage (CF-1…CF-12)

SSOT: `plans/audit/instructions/canonical_form_cross_service_audit_checklist.md` — the everlasting enumeration of the
twelve canonical data+manifest invariants the 2026-06-01 canonicalisation programme enforces. **MTDS + MDPS own the raw
**tick** surface and the **processed_candles** surface** of that matrix (the `MTDS (raw tick)` + `MDPS (candles)` rows).
Re-running this Mode-1 audit must collectively prove every CF item below is GREEN **read from actual prod data-state,
not a code constant** (the manifest-v8 lesson: a constant said v8 while 0% of 7.4M rows were v8).

**Mapping — CF items already covered by the existing Mode-1 checklist (do NOT re-run; cross-reference only):**

| CF item | Canonical target (short)                                     | Owned by existing item   |
| ------- | ------------------------------------------------------------ | ------------------------ |
| CF-1    | `schema_version = v9` read from actual rows                  | item (g)                 |
| CF-4    | `source` COLUMN stamped on every external ingest cell        | item (j)                 |
| CF-5    | Typed `EmptyConfirmedReason` on every empty cell             | item (f)                 |
| CF-9    | env-split bucket via `resolve_bucket_name()`                 | item (d)                 |
| CF-11   | fetch-failure → `attempted_failed`, never `empty_confirmed`  | item (i)                 |
| CF-12   | batch = live symmetry (schema / data_types / `available_at`) | "Batch vs Live Parity" § |

> Note: item (g) checks "≥ 95% at current version (v8 as of 2026-05-20)" — CF-1's canonical target is now **v9**
> (`MANIFEST_SCHEMA_VERSION` bumped 8→9, TradFi `source` column landed). When re-running (g) for CF-1, read the actual
> `schema_version` distribution and assert v9, not v8.

**Gap CF items — added below because the existing checklist does not cover them** (each reads prod data-state + greens):

- [ ] (CF-2) **`asset_group=` not `category=` on BOTH object paths AND manifest rows**: the CODE side already emits
      `asset_group=` (archived `venue_axis_asset_group_vocabulary`), but the DATA may still carry legacy `category=`.
      Check both surfaces in the `market-data-tick-{cefi|tradfi|defi|sports|prediction}-*` buckets AND the
      processed_candles buckets. Object paths: `gsutil ls -r gs://<bucket>/** | rg "category="` (or the UTL GCS
      object-list path) — expect 0 hits. Manifest rows: read a sample of `_index/availability_index.parquet` rows and
      assert no `category` field / no `category=` value in any partition column. **GREEN** = zero `category=` on paths
      AND zero `category` field/value in `_index` rows for both MTDS-tick and MDPS-candle buckets.

- [ ] (CF-3) **`pipeline_mode=` present as a HIVE PARTITION SEGMENT on object paths (not just the column)**: the column
      already shipped (gcs_migration_bundle_pipeline_mode); CF-3 is the distinct check that the object PATH carries a
      `pipeline_mode=batch…` / `pipeline_mode=live…` directory segment. List a sample of objects per bucket and confirm
      the path contains a literal `pipeline_mode=` segment (NOT merely a `pipeline_mode` parquet column):
      `<UTL gcs object-list> gs://<mtds-tick-bucket>/** | rg "pipeline_mode=(batch|live)"` and the same for the
      MDPS-candle bucket. **GREEN** = every sampled tick + candle object path contains a `pipeline_mode=` partition
      segment; zero objects with the column-but-no-path-segment shape.

- [ ] (CF-7) **Canonical names — underscore data_type · flat `venue` · populated `chain` · `{VENUE}_V{N}` underscore
      form; no legacy drift**: read the actual venue / data_type / source strings from a sample of prod manifest rows
      AND grep handler `data_type=` / `_DATA_TYPE` literals. Confirm: data_type uses underscores (no hyphen, e.g.
      `lst_rates` not `lst-rates`); `venue` is flat with `chain` populated as its own field (no glued `VENUE-CHAIN`);
      any `{VENUE}_V{N}` token is underscore-canonical (e.g. `UNISWAP_V3`, never `UNISWAPV3` / `UNISWAP-V3`). Greps:
      `rg "data_type=\"[^\"]*-" market-tick-data-service/ market-data-processing-service/ --include="*.py"` (expect 0);
      `rg -o "[A-Z]+V[0-9]" market-tick-data-service/ --include="*.py"` (glued — expect 0). Then read corpus rows to
      confirm no legacy hyphenated/glued strings already persisted. **GREEN** = handler literals + actual corpus
      venue/data_type strings are all canonical; zero hyphen-data_type, zero `VENUE-CHAIN`, zero glued `_V{N}`.

- [ ] (CF-8) **`available_at` per-row honest — never read-time / migration-time / lookahead derivation**: read the
      actual `available_at` column from a sample of prod tick + candle rows and assert it sits at-or-after the row's
      data day boundary (never before, never a migration-run timestamp, never a read-time `now()`). Distinct from
      CF-12's batch=live derivation parity — CF-8 is the per-row honesty of the stamped value itself. Confirm the MDPS
      candle `available_at` is derived from the candle close time / upstream tick availability at write time, not
      synthesized at read. **GREEN** = every sampled row's `available_at` is ≥ its data-day boundary and ≤ a plausible
      write time; zero rows with a uniform migration-batch timestamp or a read-time-derived value.

- [ ] (CF-10) **No phantom / date-impossible `captured` — every captured cell is object-backed**: walk
      captured-vs-objects per `(chain/venue, date)` for both the MTDS-tick and MDPS-candle buckets. Assert no
      `capture_status=captured` row exists for a date before the chain genesis / venue launch with no backing object,
      and that every post-launch `captured` row has a real object behind it. Reuse the
      `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group X --dry-run` pattern adapted to
      the MTDS/MDPS buckets (do NOT write empty parquets to mask phantoms — relabel honestly via `record_empty` /
      `record_failed`). **GREEN** = zero object-less `captured` rows; zero pre-genesis/pre-launch `captured` rows; every
      sampled captured cell resolves to an existing GCS object.

- [ ] (CF-4-prop / MDPS) **Processed candle propagates the upstream raw cell's `source` (distinct from item (j))**: item
      (j) covers the MTDS ingest write-time `source` stamp on raw tick cells. This item is the MDPS-side PROPAGATION
      check: a processed candle MUST carry the `source` of the raw tick cell(s) it was built from, so a `tardis`-derived
      candle is distinguishable from a `venue`-derived candle (and from a future Tardis-alternative source). Read a
      sample of processed-candle manifest rows and confirm `source` is non-blank and matches the upstream raw cell's
      `source` for the same `(asset_group, venue, instrument, data_type, day)`. Multi-source upstream → candle carries
      the resolved primary source per `select_primary_available_source()`. **GREEN** = zero blank `source` on candle
      rows; candle `source` traces to the upstream tick `source` for every sampled cell. SSOT:
      `plans/active/data_source_provenance_all_asset_groups_2026_06_01.md`.

## Success Criteria

- All correctness checklist items (a)–(k) GREEN
- Multi-source cells stamp `source` at write time (item j) — zero blank `source` on any `(asset_group, data_type)` with
  a multi-entry `SOURCE_PRIORITY`, read from actual prod rows
- `a6_batch_live_adapter_parity.py` shows 100% parity (batch count == live count per venue per asset_group)
- A3 manifest divergence: zero `MISSING_EXPECTED` and zero `DIVERGENT_EMPTY`
- QG exits 0 for market-tick-data-service

## Output Format (Correctness)

Result file at `plans/audit/results/mtds_mdps_master_audit_YYYY_MM_DD.md`. Same structure as per `../README.md`.

---

## Source-aware pipeline_mode + Era-B — recurring regression checks (added 2026-06-08; the migration extras)

> Guard the post-migration form against silent regression. Run weekly and after ANY migrator/reader/writer change. These
> supersede item (g)'s stale "v8" target — the canonical schema version is now **v9**.

- [ ] (src-1) **Migrators stamp SOURCE-AWARE pipeline_mode, never coarse.** `migrate_*_v9_canonical` and
      `rebuild_*_manifest` stamp `pipeline_mode=batch_<source>` in BOTH the path key and the column via UTL
      `derive_pipeline_mode_for_row` — no coarse `batch` default. Grep `market-tick-data-service/` (excluding tests) for
      a literal `DEFAULT_PIPELINE_MODE = "batch"` or `pipeline_mode = "batch"` assignment → must be 0 (DeFi was the last
      coarse writer; it must STAY 0).
- [ ] (src-2) **Readers prefix-match `batch_<source>`, no exact-coarse probe.** features `mtds_canonical_reader`, mdps
      `orchestration_scanner`, and every reader match the `pipeline_mode=batch_` prefix (plus `live_`/`replay_`), not an
      exact `pipeline_mode=batch/` path. Grep MTDS + MDPS + features for an exact-coarse `pipeline_mode=batch/` or
      `pipeline_mode=live/` probe → 0 hits (the C-PATH READ fix; must not regress).
- [ ] (src-3) **`transport` column populated** on every captured cell (rest/websocket/flat_file via M2
      `default_transport_for_source`) — 0 blank on external cells.
- [ ] (src-4) **C-#6 cross-check holds:** `source_string_for(pipeline_mode) == source` for batch rows; UTL raises
      `PipelineModeSourceMismatchError` on a mismatch. Verify the guard fires in tests.
- [ ] (erab) **Era-B on disk:** `options_chain`/`futures_chain` appear ONLY as `instrument_type`, with
      `data_type=trades`. Byte-probe a recent cefi+tradfi chain shard and count objects whose path has
      `data_type=options_chain` or `data_type=futures_chain` → must be 0. The live writer (`tardis_shared.py`
      `_LEGAL_DATA_TYPES`) raises on `data_type=options_chain`.
- [ ] (v9) **schema_version = v9 (supersedes item (g)'s v8):** read the actual `_index` `schema_version` distribution
      per `market-data-tick-<ag>` bucket; assert ≥95% v9 on real data-state.

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
