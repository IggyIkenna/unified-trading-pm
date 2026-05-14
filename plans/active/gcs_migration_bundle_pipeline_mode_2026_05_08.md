---
name: gcs-migration-bundle-pipeline-mode-2026-05-08
overview:
  Bundled overnight GCS migration that walks every parquet ONCE and applies the full set of pending hive-vocab +
  partition-column changes in a single pass, so the canonical manifest is rewritten once instead of N times. Three
  changes ride together: (1) NEW `pipeline_mode={batch_databento, batch_tardis, batch_ccxt, batch_databento_replay,
  live_websocket, ...}` hive partition column added to every existing parquet path (millions of parquets across cefi /
  defi / tradfi / sports / prediction asset_groups), with the existing batch parquets receiving `pipeline_mode=batch_*`
  per their source priority entry; (2) finish the dual-vocab `category=` → `asset_group=` rekey that CLAUDE.md preserves
  as a transitional state — every legacy `category=` directory becomes canonical `asset_group=` on disk, the legacy
  reader fallback in `reader.py` is deleted, manifest's regex `(?:category|asset_group)=` collapses to the canonical
  form; (3) sweep up the 5 drift axes from the 2026-05-04 phantom-audit incident (legacy `path-prefix=day=*/` vs
  canonical `raw_tick_data/by_date/day=*/`, instrument_type casing PERPETUAL vs perpetual, schema-4 empty
  instrument_type, chain-bundle equivalence option↔options_chain) so the residual 354 phantom rows + any drift-class
  duplicates clear in the same pass. The manifest_migration_master_2026_05_07 stages (sports rename, writegate Phase
  2.A residuals, etc.) are coordinated with — Stage 1+2+3 of that plan complete BEFORE this bundle starts, and any
  Stage 4 migrations they own that share the parquet walk land here too. Reader fallback paths are kept for ≤30 days
  post-migration then deleted (workspace "no double SSOT" rule). Pre-requisite for live-pipeline activation
  (`live_pipeline_mtds_mdps_features_2026_05_08`) — the live-mode write path needs the `pipeline_mode` column live in
  the manifest schema before MTDS / MDPS / features-service can route writes correctly.
type: infra
epic: epic-infra
status: active

asset_group: cross-cutting
priority: P0
deadline: 2026-05-15
parent: master_to_live_defi_2026_05_23
locked_by: live-defi-rollout
locked_since: 2026-05-08
last_updated: 2026-05-08

completion_gates:
  code: C5
  deployment: D3
  business: none

repo_gates:
  - repo: unified-api-contracts
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-library
    code: C0
    deployment: none
    business: none
  - repo: market-tick-data-service
    code: C0
    deployment: none
    business: none
  - repo: market-data-processing-service
    code: C0
    deployment: none
    business: none
  - repo: instruments-service
    code: C0
    deployment: none
    business: none
  - repo: deployment-api
    code: C0
    deployment: none
    business: none
  - repo: deployment-ui
    code: C0
    deployment: none
    business: none
  - repo: deployment-service
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-pm
    code: C0
    deployment: none
    business: none

depends_on:
  - manifest-migration-master-2026-05-07
  - writegate-honest-coverage-endtoend-2026-05-06

todos:
  - id: phase-0-pre-audit-gcs-state
    content: |
      - [x] [AGENT] P0. Phase 0 — Pre-audit GCS state across every bucket the workspace writes to.
        SOLO; blocks all later phases. (unified-trading-pm@0cc633c8 — pre-audit doc shipped at
        plans/archive/issues/gcs_migration_bundle_preaudit_2026_05_08.md; counts +
        per-bucket runs deferred to operator on a same-region asia-northeast1-c GCE VM
        per CLAUDE.md phantom-audit recipe — append `## Run results — YYYY-MM-DD` section
        at the bottom of the issue doc per pass.)

        Output: `unified-trading-pm/plans/archive/issues/gcs_migration_bundle_preaudit_2026_05_08.md` enumerating:
        (a) every workspace GCS bucket (`gs://{pid}-raw-tick`, `gs://{pid}-features`, `gs://{pid}-instrument-data`,
            `gs://{pid}-sports-reference`, `gs://{pid}-events`, etc.) — pull from
            `unified-cloud-interface` bucket registry + `deployment-service/configs/clusters/*.yaml`;
        (b) per bucket, parquet-count estimate (`gcloud storage du --readable-sizes` rolls up bytes; a parallel
            `gcloud storage ls --recursive` count gives the file count per asset_group prefix). Need a count to
            estimate migration wall-clock + cost;
        (c) per bucket, existing hive-key audit:
            - count of `category=` directories vs `asset_group=` directories per asset_group;
            - count of paths under legacy `day=*/...` prefix vs canonical `raw_tick_data/by_date/day=*/...`;
            - count of instrument_type casing variants (PERPETUAL vs perpetual; SPOT vs spot; OPTIONS_CHAIN vs
              options_chain vs option vs options);
            - count of schema-4 rows with empty `instrument_type` field;
            - count of chain-bundle equivalence drift (option vs options_chain, future vs futures_chain);
        (d) manifest current shape — read `_index/availability_index.parquet` per bucket;
            count rows by `(pipeline_mode IS NULL, capture_status, asset_group, venue, data_type)` — every NULL
            pipeline_mode row is a migration target;
        (e) 354 residual phantom rows from 2026-05-04 audit — re-run
            `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --dry-run` per asset_group and
            record the current count + drift-axis classification for each;
        (f) coordination check with `manifest_migration_master_2026_05_07` — verify which of its Stage 1/2/3
            migrations have shipped + which are still pending; pending Stage 4 items become candidates for
            bundling here;
        (g) cost estimate — per-bucket migration cost (Class A operations × file count + egress within-region);
            total estimated wall-clock at the `2*workers` HTTP pool sizing per CLAUDE.md phantom-audit recipe;
        (h) per-bucket safety snapshot — gcloud storage versioning enabled? if not, the migration MUST take a
            soft-snapshot first (per-prefix `gcloud storage cp -r ... gs://{pid}-pre-migration-snapshot/...` for
            the highest-value `_index/` paths and a sample of leaf parquets).

        The pre-audit IS the work for Phase 0. Subsequent phases MUST reference this artifact for counts,
        cost estimates, and per-asset-group readiness.

        **Critical**: run from a same-region GCE VM per CLAUDE.md "phantom audit re-runnable recipe" rule —
        cross-region listing is 18× slower (~12 prefixes/sec from laptop vs 222/sec on `asia-northeast1-c`).
    status: todo
    note: ""

  - id: phase-1a-uac-pipeline-mode-enum
    content: |
      - [x] [AGENT] P0. Phase 1A — UAC `PipelineMode` StrEnum + manifest schema column. PARALLEL with 1B/1C. (unified-api-contracts@8bc3f2a — PipelineMode SSOT + closed-set round-trip with SOURCE_PRIORITY)

        Site: `unified-api-contracts/unified_api_contracts/canonical/crosscutting/pipeline_mode.py` (NEW).

        ```python
        class PipelineMode(StrEnum):
            # Batch sources — one entry per existing batch source priority entry (cross-reference UAC SOURCE_PRIORITY)
            BATCH_DATABENTO = "batch_databento"
            BATCH_TARDIS = "batch_tardis"
            BATCH_CCXT = "batch_ccxt"
            BATCH_BARCHART = "batch_barchart"            # VIX 15m historical preload per CLAUDE.md
            BATCH_YAHOO = "batch_yahoo"                  # VIX 15m rolling Yahoo + tradfi ETFs
            BATCH_API_FOOTBALL = "batch_api_football"
            BATCH_FOOTYSTATS = "batch_footystats"
            BATCH_UNDERSTAT = "batch_understat"
            BATCH_TRANSFERMARKT = "batch_transfermarkt"
            BATCH_SOCCER_FOOTBALL_INFO = "batch_soccer_football_info"
            BATCH_OPEN_METEO = "batch_open_meteo"
            BATCH_ODDS_API = "batch_odds_api"
            BATCH_POLYMARKET_HISTORICAL = "batch_polymarket_historical"
            BATCH_KALSHI_HISTORICAL = "batch_kalshi_historical"
            BATCH_LIGHTER_CANDLES = "batch_lighter_candles"      # per dex_perp_onboarding 2026-05-07
            BATCH_PACIFICA_KLINE = "batch_pacifica_kline"
            BATCH_DATABENTO_REPLAY = "batch_databento_replay"    # for replay-cascade subsystem in live-pipeline plan
            # Live source — single entry; per-venue WS-vs-poll-fallback is an operational concern, not a manifest dim
            LIVE_WEBSOCKET = "live_websocket"
        ```

        Source-of-truth rule: **every UAC `SOURCE_PRIORITY` entry MUST have a corresponding `PipelineMode` value**;
        Phase 1A includes a unit test that asserts this round-trip.

        Manifest schema extension: `pipeline_mode: str | None` column in v5 manifest schema (sibling of
        `pipeline_mode` becomes the row primary-key extension — `(pipeline_mode, asset_group, venue, chain,
        data_type, instrument_type, instrument_id, league_id, timeframe, feature_group, model_family,
        training_period, strategy_id, client_id, instruction_type)`). Existing rows have `pipeline_mode=None` until
        Phase 4 backfills them.

        Tests `unified-api-contracts/tests/unit/test_pipeline_mode.py`:
        (1) closed-set: every PipelineMode value matches a SOURCE_PRIORITY entry exactly (no orphan modes; no
            orphan sources);
        (2) StrEnum round-trip via JSON serialization;
        (3) manifest row schema extension is back-compat with None default.

        QG: UAC quality-gates.sh clean.
    status: todo
    note: ""

  - id: phase-1b-utl-manifestwriter-pipeline-mode-param
    content: |
      - [x] [AGENT] P0. Phase 1B — UTL `ManifestWriter` accepts `pipeline_mode` kwarg + writes the column.
        PARALLEL with 1A/1C. (unified-trading-library@87134364 — pipeline_mode kwarg on all 5 record_* methods + AvailabilityRecord column + 11 unit tests; default `None` (back-compat) instead of BATCH_DATABENTO since no single batch source dominates workspace-wide; path-template extension deferred to Phase 2 migration script + Phase 4 consumer sweep since ManifestWriter does not compute parquet write paths)

        Site: `unified-trading-library/unified_trading_library/manifest_writer.py`.

        Add `pipeline_mode: PipelineMode` param to `record_captured` / `record_empty` / `record_failed` /
        `record_expected_empty`. Default value: `PipelineMode.BATCH_DATABENTO` (or similar batch default — pick
        the most-common batch source workspace-wide; agents pass explicit `pipeline_mode` for non-default cases).
        Phase 5 below sweeps every consumer to pass explicit `pipeline_mode` instead of relying on the default;
        once Phase 5 lands, the default value is REMOVED (no silent default — explicit is mandatory).

        Path template: extend the canonical write path with the `pipeline_mode=` segment:
        `{bucket}/raw_tick_data/by_date/day={day}/pipeline_mode={mode}/asset_group={ag}/venue={venue}/...`
        Hive-segment ordering matters for partition-pruning efficiency — `pipeline_mode` LEFT of `asset_group`
        because batch-vs-live reconciliation queries pivot on pipeline_mode first.

        Tests `unified-trading-library/tests/unit/test_manifest_writer_pipeline_mode.py`:
        (1) record_captured with pipeline_mode="live_websocket" writes path with the partition segment;
        (2) record_captured with pipeline_mode=BATCH_DATABENTO writes existing-shape paths PLUS the new column
            (back-compat during transition);
        (3) reader gates: `read_manifest(pipeline_mode="live_websocket")` returns only live rows;
            `read_manifest(pipeline_mode=None)` returns all (default = no filter);
        (4) post-Phase-5: removing the default raises if pipeline_mode is omitted (explicit-or-fail).

        QG: UTL quality-gates.sh clean.
    status: todo
    note: ""

  - id: phase-1c-uac-source-priority-pipeline-mode-mapping
    content: |
      - [x] [AGENT] P0. Phase 1C — UAC `SOURCE_PRIORITY` extension: every entry gets a `pipeline_mode` field. **SHIPPED 2026-05-08 (unified-api-contracts@6a8529f).** Option B chosen: rather than restructuring `SOURCE_PRIORITY`'s value type from `list[str]` to `list[SourcePriorityEntry]`, we keep the existing shape and add a thin `read_with_source_priority(asset_group, data_type) → (str, PipelineMode)` reader that delegates to the existing `pipeline_mode_for_source` helper. The closed-set round-trip is already enforced in `tests/unit/test_pipeline_mode.py`, so the reader's pipeline_mode lookup cannot break silently. Helper exposed via `from unified_api_contracts.canonical.crosscutting import read_with_source_priority`. New `tests/unit/test_source_priority_pipeline_mode.py` (12 tests) covers: every entry has ≥1 source; every source round-trips to a `PipelineMode`; reader returns `(source, mode)` tuple; reader is consistent with `get_primary_source` for every registered pair; reader always returns a batch mode (live is a write-time concern); KeyError on unregistered pair; synthetic live-priority-over-batch row selection; facade export.
        PARALLEL with 1A/1B.

        Site: `unified-api-contracts/unified_api_contracts/canonical/crosscutting/source_priority.py`.

        Each entry currently has shape `{source: str, priority: int, ...}`. Add `pipeline_mode: PipelineMode`. The
        live-vs-batch fan-in at read-time uses this — readers stratify by pipeline_mode + apply priority within
        each stratum (so live always wins for dates where live exists; batch wins where it doesn't).

        Reader behaviour change: `read_with_source_priority(...)` now returns a column `pipeline_mode` per row so
        downstream consumers can detect which source served each row. Useful for the batch-vs-live reconciliation
        gate in `live_pipeline_mtds_mdps_features_2026_05_08` Phase 12.

        Tests update existing `test_source_priority.py`:
        (1) every entry has a `pipeline_mode` populated;
        (2) reader returns the column;
        (3) live-priority-over-batch behaviour: synthetic row at same `(asset_group, venue, day)` with
            pipeline_mode=live_websocket is preferred over pipeline_mode=batch_databento.

        QG: UAC quality-gates.sh clean.
    status: done
    note: "Shipped 2026-05-08 unified-api-contracts@6a8529f — Option B reader pattern."

  - id: phase-2-migration-script-canonical
    content: |
      - [x] [AGENT] P0. Phase 2 — Canonical migration script.
        SEQUENTIAL after Phase 1.
        (unified-trading-pm@5a3c360a — `scripts/migration/gcs_migration_bundle_2026_05_08.py`
        + `tests/test_gcs_migration_bundle.py` shipped with 23 unit tests; dry-run by
        default; `assert_per_vm_shard_isolation` startup guard fires when `--apply` is
        invoked without `MANIFEST_PER_VM_SHARDS=true` + `VM_NAME=<unique-tag>`; HTTP
        pool sized to `2*workers`; leverages UAC `pipeline_mode_for_source` + UTL
        `manifest_migrations` per CLAUDE.md "no double SSOT" rule. Per-drift-class
        coverage in tests: pipeline_mode insertion (LEFT of asset_group=),
        category= → asset_group= rewrite, day=*/ → raw_tick_data/by_date/day=*/
        prefix normalisation, PERPETUAL → perpetual casing, option → options_chain
        chain-bundle equivalence; NOOP detection on canonical paths; idempotent;
        crc32c mismatch triggers rollback (delete dest, keep source) → FAILED;
        dry-run mode produces zero gcloud calls. Phase 3 VM fleet launch unblocked.)

        Site: `unified-trading-pm/scripts/migration/gcs_migration_bundle_2026_05_08.py` (NEW).

        Single Python script orchestrating the bundle. Per CLAUDE.md "Manifest concurrency principle" — read-once
        + per-shard freshness check + write-time CAS pattern; per-VM shard isolation
        (`MANIFEST_PER_VM_SHARDS=true` + `VM_NAME=<unique-tag>`) MANDATORY because Phase 3 launches multi-VM
        execution.

        Logical structure:

        ```python
        def migrate_one_parquet(source_uri: str) -> MigrationResult:
            """
            For each parquet:
            1. Parse the existing path to extract (day, legacy hive-vocab, asset_group, venue, data_type, ...).
            2. Determine target path applying the bundle:
               (a) Add pipeline_mode= segment using the writer's source priority entry (lookup by writer_service
                   metadata in the parquet footer or by source-attribution-via-bucket-prefix mapping).
               (b) Rewrite category= → asset_group= if legacy.
               (c) Normalize path prefix from `day=*/...` to `raw_tick_data/by_date/day=*/...` if legacy.
               (d) Normalize instrument_type casing (PERPETUAL → perpetual; chain-bundle: option → options_chain
                   for bundled data_types).
               (e) Re-derive schema-4 empty instrument_type by inspecting the parquet's row schema.
            3. If target == source (no migration needed), record `migration_status=NOOP` and skip.
            4. If target ≠ source:
               a. `gcloud storage cp source_uri target_uri` (server-side copy — no egress, fast).
               b. Verify destination size + crc32c match source.
               c. `gcloud storage rm source_uri`.
               d. Update the manifest row IN-PLACE: rewrite the row_key columns (pipeline_mode, asset_group,
                  data_type, instrument_type) + path column + write to the per-VM shard at
                  `_index/per_vm/{VM_NAME}.parquet`.
            5. Emit MIGRATION_PARQUET_PROCESSED event with before/after path + diff status.
            6. Return MigrationResult with timing + bytes-moved + drift-class observations.

        def main():
            # Iterate all parquets across configured buckets via gcloud storage ls --recursive piped through xargs.
            # Worker pool sized to 2*N_VMS, each worker handling a deterministic prefix slice (per-VM-shard
            # isolation pattern — workers can't collide on the same parquet).
            # Aggregate metrics: total moved, total bytes, drift-class histogram, error histogram.
        ```

        **Critical safety**: the script is dry-run by default (`--dry-run` flag, defaults to `True`). Operator
        explicitly passes `--apply` to enable destructive operations. Dry-run mode logs the planned migrations
        without executing — supports the per-bucket sample audit before full apply.

        Tests `unified-trading-pm/scripts/migration/tests/test_gcs_migration_bundle.py`:
        (1) per-drift-class fixture (synthetic parquet with `category=`, with legacy day-prefix, with PERPETUAL
            casing, with empty instrument_type) — each migrates to canonical shape;
        (2) NOOP detection — already-canonical parquet → migration_status=NOOP, no GCS operations;
        (3) crc32c verification — corrupted destination triggers rollback (delete dest, keep source);
        (4) dry-run mode — no GCS writes; planned migration captured in output JSON;
        (5) idempotent — running the script twice on the same input set is safe (second run = all NOOPs);
        (6) per-VM-shard isolation — two parallel runs with different VM_NAME values produce two distinct shard
            files at `_index/per_vm/{VM_NAME}.parquet` with no clobbering.

        QG: PM quality-gates.sh clean.
    status: done
    note: "Shipped 2026-05-08 — see commit cited inline above."

  - id: phase-3-execution-plan-and-vm-launch
    content: |
      - [ ] [HUMAN+AGENT] P0. Phase 3 — Execute the migration. Operator-gated; agent prepares + verifies, operator
        triggers the run. SEQUENTIAL after Phase 2.

        Steps:
        1. Final pre-flight verification: Phase 0 artifact still current; Phase 1 schema additions deployed
           (UAC + UTL pinned in workspace-manifest); Phase 2 script smoke-tested via `--dry-run` against a
           sample bucket prefix.
        2. Snapshot critical state: `gcloud storage cp -r gs://{pid}-raw-tick/_index/ gs://{pid}-pre-migration-snapshot/raw-tick-2026-05-XX/_index/`
           per bucket. The snapshot covers the canonical manifest before migration; if any drift class breaks
           the manifest in-flight, snapshot lets operator restore.
        3. Launch a fleet of migration VMs per CLAUDE.md "phantom audit re-runnable recipe" rule:
           - Per-bucket parallelism: 4-8 VMs per bucket depending on prefix count (Phase 0 § (b) gives the
             estimate);
           - Each VM gets a deterministic `--prefix-slice <slice>` arg — script's worker pool reads only its
             assigned slice. No two VMs ever touch the same parquet.
           - Same-region (`asia-northeast1-c`) per CLAUDE.md.
           - HTTP pool sized to `2*workers` (default 10 silently truncates list_blobs() under high concurrency).
           - `MANIFEST_PER_VM_SHARDS=true` + `VM_NAME=migration-${asset_group}-${slice}-${RUN_TS}` per workspace
             concurrency rule.
        4. Watch event stream for MIGRATION_VM_STARTED → MIGRATION_PARQUET_PROCESSED progress events → STOPPED.
           Per-VM completion should emit aggregate metrics (parquets-migrated, drift-class histogram,
           bytes-moved). No fire-and-forget per CLAUDE.md "no fire-and-forget VM launches".
        5. Manifest consolidator runs continuously during the migration — per-VM shards under
           `_index/per_vm/{VM_NAME}.parquet` get merged into canonical `_index/availability_index.parquet`
           via the existing `manifest_consolidator` daemon (runs at every cluster boot per workspace cron +
           a one-shot bounce post-migration to drain pending shards).
        6. Pre-VM-decommission per-asset-group QA gate: re-run
           `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group <ag>` per
           asset_group; phantom count must be 0 (was 354 residual pre-migration; the bundle fixes the 5 drift
           axes that were the source of those 354 phantoms).
        7. Per-asset-group migration sign-off: operator marks each asset_group complete inline as a checkbox in
           this plan's Phase 3 done-definition (NOT a separate issue doc) once Phase 3.6 phantom gate is green.
           Down-stream services bounced (MTDS/MDPS/features VMs) only after sign-off so they pick up the new
           manifest schema. Composes with `manifest_schema_final_gate_2026_05_09` Phase 7.G inline operator sign-off.

        Estimated wall-clock (back-of-envelope, refined by Phase 0 § (g)): cefi 8h, defi 4h, tradfi 6h,
        sports 12h (largest by file count), prediction 2h. Run sports overnight starting 2026-05-13 evening
        UTC; cefi+defi+tradfi+prediction in parallel one zone over starting same evening; full bundle done by
        2026-05-15 morning UTC.

        Coordination: VMs running ANY pipeline (MTDS backfill, MDPS reprocess, features compute, instruments
        backfill) MUST be drained or paused during their asset_group's migration window — per Cross-Plan-
        Coordination-Banners rule, banner ALL active plans with `🟡 IN-FLIGHT REFACTOR — gcs migration
        bundle 2026-05-13/14/15` so agents pause new VM launches.
    status: todo
    note: ""

  - id: phase-4-consumer-sweep-explicit-pipeline-mode
    content: |
      - [ ] [AGENT] P0. Phase 4 — Sweep every `record_captured` / `record_empty` / `record_failed` / `record_expected_empty`
        callsite to pass explicit `pipeline_mode`. PARALLEL with Phase 3 (sweeps land in source repos; migration
        runs against parquets on disk, not against running services).

        Site: workspace-wide. Phase 0 § (e) of `live_pipeline_mtds_mdps_features_2026_05_08` cross-references
        every consumer of ServiceEmissionPolicy + ManifestWriter; that audit covers the same callsites this
        phase sweeps.

        Per-service edits:
        - **MTDS**: every adapter passes `pipeline_mode=PipelineMode.BATCH_<source>` from the source-priority
          mapping (Phase 1C provides the lookup). Live-mode writes (added in `live_pipeline` Phase 3) pass
          `pipeline_mode=PipelineMode.LIVE_WEBSOCKET`.
        - **MDPS**: candle writer passes `pipeline_mode` propagated from the input parquet's column (so a
          batch-input → batch-output, live-input → live-output).
        - **features-service**: similar to MDPS — propagate from input.
        - **instruments-service**: catalog refresh writes pass `pipeline_mode=PipelineMode.<mode>` per source;
          mostly batch_* sources.
        - **e2e-testing harnesses**: any synthetic-fixture writer passes the synthetic source's pipeline_mode.

        Removal of the default in Phase 1B once this sweep is workspace-clean — the explicit-or-fail rule
        catches any future regression.

        Tests: per-service quality-gates.sh covers the wired callsites (existing test patterns). NEW workspace-
        wide grep verification: `grep -rln "record_captured\|record_empty\|record_failed\|record_expected_empty"
        --include="*.py" | xargs grep -L "pipeline_mode="` returns zero hits across all 12 affected repos.

        QG: every affected repo quality-gates.sh clean.
    status: todo
    note: ""

  - id: phase-5-reader-fallback-paths
    content: |
      - [ ] [AGENT] P0. Phase 5 — Reader fallback paths during the migration window. PARALLEL with Phase 3.

        **5.1 SHIPPED 2026-05-08 (unified-trading-library@52f123d6); 5.2 + 5.3 deferred to follow-up sub-agents.**
        UTL `read_manifest_with_source_priority(...)` reader landed in
        `unified_trading_library/manifest_reader_fallback.py` (NEW module, 356 lines) + 11 unit tests in
        `tests/unit/test_reader_fallback_chain.py` (469 lines). Public API: `read_manifest_with_source_priority`,
        `build_candidate_uris`, `ReaderMetadata` (frozen dataclass), `FALLBACK_LEVEL_NAMES` (canonical level
        names tuple). All four plan contracts (lines 403-409) test-covered: canonical-hit-no-events,
        miss-then-strip-emits-one-event, full-chain-five-levels-with-distinct-events, metadata-records-resolved-level.
        Plus edge cases: pipeline_mode=None back-compat skips canonical level; all-miss returns empty pa.Table +
        hit_level=None; ReaderMetadata is immutable.

        Three readers need fallback paths during migration:

        5.1 — UTL `read_manifest_with_source_priority(...)` reader: try canonical path
             `{bucket}/raw_tick_data/by_date/day={day}/pipeline_mode={mode}/asset_group={ag}/...` first; on
             miss, fall back to legacy paths in this order:
             (a) without pipeline_mode segment: `{bucket}/raw_tick_data/by_date/day={day}/asset_group={ag}/...`
             (b) with legacy hive vocab: `{bucket}/raw_tick_data/by_date/day={day}/category={ag}/...`
             (c) with legacy path prefix: `{bucket}/day={day}/asset_group={ag}/...`
             (d) combination: `{bucket}/day={day}/category={ag}/...`

             Each fallback emits a `READER_FELL_BACK_TO_LEGACY_PATH` event per row read so we can monitor
             migration progress + know when ALL readers have stopped hitting legacy paths.

        5.2 — MTDS / MDPS path probers (they look up specific (venue, instrument, day) parquets to read prior
             ticks for windowing): same fallback chain as 5.1.

        5.3 — Sports + DeFi GCS path SSOT (per CLAUDE.md "Sports GCS path SSOT" rule, the
             `candidate_parquet_paths` helper already implements a fallback chain): extend the helper's chain
             to include the new pipeline_mode-aware canonical path as the first probe.

        Reader fallback contract: **fallback is allowed for ≤30 days post-Phase-3**. After 30 days, fallback
        paths are deleted (workspace "no double SSOT" rule). The 30-day window covers any stragglers + lets
        the `READER_FELL_BACK_TO_LEGACY_PATH` event count drop to zero before code removal.

        Tests `unified-trading-library/tests/unit/test_reader_fallback_chain.py`:
        (1) canonical path hit returns immediately, no fallback events;
        (2) miss-then-pipeline_mode-stripped fallback returns successfully + emits one event;
        (3) full chain (canonical → strip pipeline_mode → category=legacy → day-prefix-legacy) — every step
            triggers a distinct event;
        (4) reader returns the path it actually read from in metadata so consumers can log the fallback
            level.

        QG: UTL quality-gates.sh clean.
    status: todo
    note: ""

  - id: phase-6-residual-phantom-cleanup
    content: |
      - [ ] [AGENT] P0. Phase 6 — Residual phantom cleanup. SEQUENTIAL after Phase 3.6.

        Pre-migration baseline (per Phase 0 § (e)) recorded the 354 residual phantom rows from the 2026-05-04
        audit. The bundle's drift-axis sweep should clear most/all of them; this phase verifies + cleans the
        residual.

        Run per asset_group:
        ```bash
        cd instruments-service && python scripts/reconcile_phantom_manifest_rows_all.py \
          --asset-group {ag} --apply
        ```
        With `MANIFEST_PER_VM_SHARDS=true` + a unique `VM_NAME` per asset_group sweep.

        Pass criterion: post-migration phantom count is **0 across all 5 asset_groups**. If not zero, root-cause
        each remaining phantom (likely a 6th drift axis the migration didn't anticipate) + add a one-shot
        targeted fix.

        Coordination: `manifest_migration_master_2026_05_07` Stage 4 has overlapping cleanup items; coordinate
        ownership — that plan's agents run their stages first, this phase's agent picks up the residual.

        QG: instruments-service quality-gates.sh clean (the script lives there per workspace history). Phantom
        count = 0 reported per asset_group + recorded inline in this plan's Phase 6 done-definition (NOT a separate
        issue doc). Composes with `manifest_schema_final_gate_2026_05_09` Phase 7.F phantom gate.
    status: todo
    note: ""

  - id: phase-7-codex-ssot-updates
    content: |
      - [x] [AGENT] P0. Phase 7 — Codex SSOT updates. PARALLEL with Phase 6. **PARTIAL SHIPPED 2026-05-08.** 7.1+7.2 at `unified-trading-pm@e8530de8` (pipeline-mode-partition.md status table + commit shas; availability-manifest-and-data-status.md v8 pipeline_mode column). 7.3+7.4 at `@7ac15cf4` (data-status-drilldown-hierarchy.md outermost-partition note; 00-SSOT-INDEX.md pipeline-mode-partition register). Items requiring post-Phase-3 migration data (drift-class histogram, observed wall-clock per asset_group, pre/post phantom counts) deferred until Phase 3 runs. Asset-group-vocabulary doc-touch deferred — no dedicated codex doc exists; vocabulary lives in CLAUDE.md "Asset-group vocabulary" section + availability-manifest-and-data-status.md (already updated). CLAUDE.md "Asset-group vocabulary" section flip ("category= legacy preserved" → "RESOLVED") deferred until Phase 3 actually runs.

        Per the workspace "Post-Plan-Phase Codex Audit" rule (CLAUDE.md, codified 2026-05-08), this phase
        enhances the plan-driven stub created at plan-draft time + updates 5 existing docs.

        New + updated docs:
        1. **ENHANCE** existing stub at `codex/02-data/pipeline-mode-partition.md` (created at plan-draft
           time 2026-05-08) — describes the `pipeline_mode` hive partition, the migration history, the
           source-priority fan-in semantics, the reader fallback contract + 30-day window. Add: actual
           pre/post migration phantom counts, observed wall-clock per asset_group, drift-class histogram
           from the migration run.
        2. **UPDATE** `codex/02-data/availability-manifest-and-data-status.md` — extend v5 manifest column
           list with `pipeline_mode`; remove the legacy `category=` description (or move it to a "historical
           note" sidebar with a reference to this migration).
        3. **UPDATE** `codex/02-data/asset_group-vocabulary.md` (or wherever the `category=`/`asset_group=`
           dual-vocab is documented) — flip the legacy mention to "RESOLVED 2026-05-15 per
           `gcs_migration_bundle_pipeline_mode_2026_05_08.md`"; reader fallback removal scheduled
           T+30 days.
        4. **UPDATE** `codex/02-data/data-status-drilldown.md` § "Per-asset_group depth table" — add
           `pipeline_mode` as the outermost partition column in the drilldown (above asset_group).
        5. **UPDATE** `codex/00-SSOT-INDEX.md` — register the new pipeline-mode-partition doc.
        6. **UPDATE** CLAUDE.md "Asset-group vocabulary" section — remove the "category= legacy preserved"
           statement; replace with "category= migrated to asset_group= 2026-05-15 per
           `gcs_migration_bundle_pipeline_mode_2026_05_08`; reader fallback removal scheduled
           2026-06-15".

        QG: PM quality-gates.sh clean. Plan-health agent picks up the SSOT additions on the next run.
    status: todo
    note: ""

  - id: phase-8-fallback-removal-followup
    content: |
      - [ ] [AGENT] P2. Phase 8 — Reader fallback removal (T+30 days post-migration).
        DEFERRED-PER-DESIGN to 2026-06-15.

        After 30 days of zero `READER_FELL_BACK_TO_LEGACY_PATH` events workspace-wide, delete the legacy
        fallback paths from:
        - UTL `read_manifest_with_source_priority`
        - MTDS / MDPS path probers
        - Sports `candidate_parquet_paths` helper

        Workspace "no double SSOT" rule applies — once migration is verified-clean for 30d, fallbacks have
        served their purpose. Delete in one commit per repo with a `[migration-cleanup]` tag.

        QG: per-repo quality-gates.sh clean post-deletion. Manual verification: `grep -rln "category=\|day=[^/]*$"`
        across workspace returns zero hits in production code paths.

        Banner removal: this plan unlocks at Phase 8 completion. Operator approves unlock per workspace
        unlock-protocol.
    status: todo
    note: ""

  - id: phase-9-workspace-wide-qg-sweep
    content: |
      - [ ] [AGENT] P0. Phase 9 — Final workspace-wide QG sweep.
        SEQUENTIAL after Phase 6.

        Run `quality-gates.sh` Pass 1 across all 9 affected repos per `repo_gates`. Every repo green
        simultaneously. Operator runs; agent prepares the sweep command + documents per-repo results.

        Final gate: master plan `master_to_live_defi_2026_05_23` Group F item dependency on this migration
        is satisfied; `live_pipeline_mtds_mdps_features_2026_05_08` unblocks at this gate.
    status: todo
    note: ""

isProject: false
estimate_class: infra
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 4.8
estimate_calibration_note: |
  No explicit AI-day estimates found in plan body during 2026-05-11 sweep; class inferred from filename (infra, multiplier 0.8×).
  Owner agent: fill baseline + multiply × 0.8 per codex/08-workflows/estimation-calibration.md. Refine class if dominant work-class differs.
---

> **🟡 IN-FLIGHT REFACTOR — batch_live_symmetry 2026-05-14** (BE-AWARE)
> `BatchExecutionMode` enum + `RECON_GREEN_THRESHOLDS` shipped at UAC@01c1b59.
> Re-verify any archetype-keyed batch/live routing code before touching pipeline_mode / reconciler
> threshold / mode-routing logic.

> **🟡 FOLDED INTO UMBRELLA — `manifest_evolution_master_2026_05_08`** (codified 2026-05-08)
>
> This plan's manifest-touching scope MUST execute as part of the umbrella's gate sequence — NOT in isolation. Operator
> direction: "manifest, code, and data migrate in the same group plan to avoid collision risk; force batch execution;
> don't allow execution in isolation." Three-axis invariant: schema (UAC) + writer code (UTL + adapter callsites) + GCS
> data layout co-evolve.
>
> Child of: [`plans/epics/manifest_evolution_master_2026_05_08.md`](../epics/manifest_evolution_master_2026_05_08.md)
>
> This plan's phases land in gate(s): **G6** (pipeline_mode= hive partition + writer kwarg adoption) + **G7** (workspace
> audit)

> **🟡 IN-FLIGHT REFACTOR — code-freeze sequencing 2026-05-10** (BE-AWARE)
>
> [`plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md`](code_freeze_migrate_backfill_sequencing_2026_05_10.md)
> Phase 2.X folds the **OHLCV legacy filename → per-instrument file rename** (extract `instrument_id` from row data, NOT
> path heuristic per 2026-05-05 silent-placeholder incident) into this plan's single-walk discipline. Also: confirm
> Phase 2 schema column set enumerates ALL Phase 1 columns from `writegate_honest_coverage_endtoend_2026_05_06` slice
> (b) Phase 5.1 (`service_emission_state` + `pipeline_mode` + `feature_family`) before this plan's walk starts.
> Single-walk discipline is the constraint — reviewers reject any post-Phase-2 plan that proposes another whole-corpus
> walk.

# GCS migration bundle — pipeline_mode partition + category→asset_group rekey + drift cleanup (2026-05-08)

## Why this plan exists

Live-pipeline activation (`live_pipeline_mtds_mdps_features_2026_05_08`) needs a `pipeline_mode=` hive partition column
across every parquet on disk so live-mode writes can land alongside batch-mode writes in the same bucket without
conflict. Without the column, MTDS / MDPS / features-service in live mode would write to paths that downstream readers
can't reconcile against batch.

But the workspace also has standing GCS migration debt:

- The `category=` → `asset_group=` rename was started but never finished — CLAUDE.md "Asset-group vocabulary" preserves
  `category=` legacy paths "without re-keying" and readers carry a fallback. This is workspace-wide technical debt that
  has lingered for ≥6 weeks.
- The 2026-05-04 phantom-audit incident identified 5 drift axes (path-prefix, hive-vocab, instrument_type casing, empty
  schema-4 instrument_type, chain-bundle equivalence) producing 130k+ false-positive phantom rows; reconciler fixes most
  but a 354-row residual remains (per CLAUDE.md "Manifest phantom audit" section).
- `manifest_migration_master_2026_05_07` Stage 4 has multiple residual sweeps that share the GCS-walk concern.

Running 4 separate overnight migrations is wasteful — each walks every parquet (millions across asset_groups) +
re-writes the manifest. The user's directive (2026-05-08) is **bundle**: one walk, one manifest re-index, all migrations
applied atomically per parquet. This plan IS that bundle.

Per CLAUDE.md "Manifest concurrency principle": read-once + per-shard freshness check + write-time CAS. Migration VMs
launch with `MANIFEST_PER_VM_SHARDS=true` + unique `VM_NAME` per slice; manifest consolidator merges per-VM shards into
canonical via last-writer-wins. No race between migration VMs.

## Codex SSOTs

Read these BEFORE making code changes — drift = review-blocking failure per `doc → plan → code`:

- [`codex/02-data/availability-manifest-and-data-status.md`](../../codex/02-data/availability-manifest-and-data-status.md)
  — manifest schema + 4-state taxonomy. Phase 1 extends with `pipeline_mode` column.
- CLAUDE.md "Asset-group vocabulary" section — current dual-vocab `category=`/`asset_group=` state (this plan resolves
  it).
- CLAUDE.md "Manifest phantom audit" section — 5 drift axes the audit handles. This plan's Phase 2 migration applies the
  same 5 fixes during the parquet walk so post-migration the audit reports zero phantoms.
- CLAUDE.md "Manifest migration, NOT fallback" rule — fallback paths in readers are short-lived (≤30d per Phase 5
  contract); not a long-term coexistence pattern.
- [`codex/02-data/data-status-drilldown.md`](../../codex/02-data/data-status-drilldown.md) § "Per-asset_group depth
  table" — drilldown order; Phase 7 adds pipeline_mode as outermost.
- [`codex/04-architecture/runtime-deployment-topology.md`](../../codex/04-architecture/runtime-deployment-topology.md) —
  how migration VMs fit into the deployment topology.

## Pre-audit manifest

Phase 0 produces `unified-trading-pm/plans/archive/issues/gcs_migration_bundle_preaudit_2026_05_08.md`. Subsequent
phases reference it for: (a) bucket inventory; (b) per-bucket parquet count + cost estimate; (c) per-bucket drift-class
histogram; (d) manifest current shape; (e) phantom-row baseline; (f) coordination with `manifest_migration_master` Stage
4; (g) total cost + wall-clock; (h) snapshot strategy.

## Phased execution DAG

```
Phase 0 (Pre-audit GCS state — SOLO; blocks everything)
   │
   ├─> Phase 1A (UAC PipelineMode enum + manifest column) ─┐
   ├─> Phase 1B (UTL ManifestWriter pipeline_mode kwarg)   ─┤  PARALLEL within Phase 1
   └─> Phase 1C (UAC SOURCE_PRIORITY pipeline_mode field)  ─┘
        │
        └─> Phase 2 (Canonical migration script + tests)
             │
             ├─> Phase 3 (Operator-gated migration VM fleet) ──┐
             ├─> Phase 4 (Consumer sweep — explicit pipeline_mode) ──┤  PARALLEL Phases 3-5
             └─> Phase 5 (Reader fallback paths)               ──────┘
                  │
                  ├─> Phase 6 (Residual phantom cleanup) ─┐
                  └─> Phase 7 (Codex SSOT updates)        ─┤  PARALLEL Phase 6+7
                       │                                    │
                       └─> Phase 9 (Workspace-wide QG sweep — final)
                            │
                            └─> Phase 8 (Reader fallback removal — DEFERRED to T+30d)
```

## Success criteria

Per phase — see each todo. Plan-level final gate:

- All 9 `repo_gates` reach C5; deployment gate D3 once Phase 9 sweep is green.
- Manifest's regex `(?:category|asset_group)=` collapses to canonical `asset_group=` only.
- Phantom row count = 0 across all 5 asset_groups (354 → 0).
- Every parquet on disk has `pipeline_mode=` segment in path.
- Reader fallback events workspace-wide drop to zero within 7d post-migration (Phase 8 then deletes).
- `live_pipeline_mtds_mdps_features_2026_05_08` Phase 3 (MTDS streaming rollout) unblocked.

## Anti-patterns to avoid

- **Do NOT split this into 4 separate migrations.** The user's explicit directive (2026-05-08) is bundle. One walk, one
  manifest re-index, multi-migration apply per parquet.
- **Do NOT keep the `category=` reader fallback long-term.** Phase 5 contract is ≤30d. Phase 8 deletes it. CLAUDE.md
  "Manifest migration, NOT fallback" rule.
- **Do NOT run migration VMs cross-region.** Same-region only (asia-northeast1-c per CLAUDE.md phantom-audit rule);
  cross-region is 18× slower.
- **Do NOT skip the snapshot step (Phase 3.2).** GCS doesn't have point-in-time recovery for non-versioned buckets. If
  migration corrupts the manifest, snapshot is the only rollback.
- **Do NOT launch new MTDS/MDPS/features VMs during the migration window** for the asset_group being migrated. They will
  write to manifest paths that the migration is concurrently rewriting; race-conditions will produce phantom rows. Per
  workspace Cross-Plan-Coordination-Banners rule + Phase 3 banner.
- **Do NOT remove the explicit-or-fail rule (Phase 4) before the workspace sweep is grep-clean.** Silent default hiding
  a missed callsite is exactly the bug class the rule prevents.
- **Do NOT bundle in migrations the operator hasn't approved.** Phase 0 § (f) coordination check explicitly verifies
  which `manifest_migration_master` Stage 4 items are in scope; out-of-scope items stay separate.

## Cross-plan coordination

- **`live_pipeline_mtds_mdps_features_2026_05_08`** — STRICT BLOCKER: Phase 9 of this plan must complete before
  live_pipeline Phase 3 (MTDS streaming rollout). Banner that plan with
  `🟢 BLOCKER FOR live_pipeline Phase 3 — gcs migration bundle Phase 9 must land first`.
- **`features_repo_consolidation_2026_05_08`** — independent; no overlap. Features manifest writes pass through the same
  `ManifestWriter` so they pick up the new `pipeline_mode` kwarg from Phase 1B; Phase 4 sweep covers features-service's
  call sites.
- **`manifest_migration_master_2026_05_07`** — coordinated parent. That plan's Stage 1+2+3 should land BEFORE Phase 3 of
  this plan starts so we don't bundle work that's still in flight elsewhere. Phase 0 § (f) verifies. Stage 4 residual
  sweeps coordinate with this plan's Phase 6.
- **`writegate_honest_coverage_endtoend_2026_05_06`** — Phase 2.A residual sweeps (placeholder method deletion + v6
  column wiring) are coordinated; either land in writegate plan + this plan's Phase 0 § (f) confirms the source state,
  or fold any unfinished items into this bundle's Phase 4 sweep.
- **`master_to_live_defi_2026_05_23`** — parent. Add a Group F sub-bullet pointing here: "GCS migration bundle
  (pipeline_mode + category→asset_group + drift cleanup) per `gcs_migration_bundle_pipeline_mode_2026_05_08.md` —
  pre-req for live-pipeline activation."
- **`infrastructure_master_2026_05_07`** — umbrella; Phase 7 codex SSOT updates may overlap with infrastructure master
  codex sweeps. Coordinate via banner.
- **`sports_master_2026_05_07`** — sports-specific GCS structure overlaps; banner that plan during the sports
  asset_group migration window.
- **`predictions_master_2026_05_07`** + **`defi_master_2026_05_07`** + **`tradfi_master_2026_05_07`** +
  **`cefi_master_2026_05_07`** — banner each during their asset_group's migration window (per Phase 3 estimated
  wall-clock).

## Temporary states + their canonical follow-up plans

- **Reader fallback paths** in Phase 5 are temporary by design — Phase 8 (T+30d, deferred to ~2026-06-15) deletes them.
  Successor plan: this plan's Phase 8 itself.
- **`pipeline_mode` default in `ManifestWriter`** (Phase 1B) is temporary — Phase 4 sweep removes it once the
  workspace-wide grep is clean. No separate successor needed; tracked inside this plan.

## Risk register

| Risk                                                                     | Likelihood                     | Impact                            | Mitigation                                                                                                  |
| ------------------------------------------------------------------------ | ------------------------------ | --------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Migration VM crashes mid-walk; partial state                             | Medium                         | Manifest temporarily inconsistent | Per-VM shard isolation + manifest consolidator handles partial completes; restart from last-completed slice |
| crc32c mismatch on copy                                                  | Low                            | Silent corruption                 | Phase 2 script verifies post-copy; mismatch triggers rollback (delete dest, keep source)                    |
| Concurrent live VM writes during migration produce phantom rows          | High if not banner-coordinated | Manifest pollution                | Phase 3 banner discipline + per-asset-group window scheduling                                               |
| Migration estimate (Phase 0 § (g)) under-estimates by >2×                | Medium                         | Cutover slip                      | Phase 0 includes empirical measurement on a sample slice before launching full fleet                        |
| Reader fallback events don't drop to zero within 30d                     | Low                            | Phase 8 delayed                   | Acceptable; fallback removal isn't on May-23 critical path                                                  |
| 6th drift axis discovered post-migration                                 | Low                            | Phantom count > 0 after Phase 6   | Phase 6 includes per-asset-group root-cause; one-shot targeted fixes acceptable                             |
| `manifest_migration_master` Stage 4 items collide with this plan's scope | Medium                         | Double-work or work-stealing      | Phase 0 § (f) coordination check is explicit; banner discipline                                             |
| Snapshot bucket cost spikes                                              | Low                            | Per-VM-budget overrun             | Snapshot only `_index/` + sample leaf parquets, not the full bucket                                         |

## DONE-2026-05-08 — Tab 3 (gcs-migration-manifest-tab) shipped

Tab 3 of [`work_split_2026_05_08_ikenna.md`](work_split_2026_05_08_ikenna.md) ran 5 sub-agents during this session.
Phases shipped on `live-defi-rollout`:

| Phase / Item                                                 | Commit(s)                                                                       | Notes                                                                                              |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| Phase 0 — Pre-audit doc                                      | `unified-trading-pm@0cc633c8` (doc) + `@12483f5b` (flip)                        | 521-line operator-runnable doc + 8 sections (a)–(h) tagged WORKSPACE-LOCAL vs REQUIRES VM RUN.     |
| Phase 1A — UAC `PipelineMode` SSOT                           | `unified-api-contracts@8bc3f2a`                                                 | Closed-set StrEnum + helpers + `pipeline_mode_for_source` round-trip tests.                        |
| Phase 1B — UTL `ManifestWriter` `pipeline_mode` kwarg        | `unified-trading-library@87134364`                                              | New kwarg on all 5 record\_\* methods + `_ROW_KEY_COLUMNS` extension + 11 unit tests.              |
| Phase 1C — UAC `SOURCE_PRIORITY` `pipeline_mode` field       | `unified-api-contracts@6a8529f` + `unified-trading-pm@53c498c5` (flip)          | Option B (thin reader helper, no value-type change). 12 unit tests.                                |
| Phase 2 — Canonical migration script                         | `unified-trading-pm@5a3c360a` (script + tests + conftest) + `@cc6fe4ce` (flip)  | 694-line script + 23 unit tests, dry-run by default, leverages UTL `manifest_migrations`.          |
| Phase 5.1 — UTL `read_manifest_with_source_priority` reader  | `unified-trading-library@52f123d6` + `unified-trading-pm@2a0d105d` (annotation) | NEW `manifest_reader_fallback.py` 356 lines + 469-line tests. 5-level fallback chain.              |
| Phase 7.1 + 7.2 — Codex (pipeline-mode-partition + manifest) | `unified-trading-pm@e8530de8`                                                   | Status table with all 6 shipped phases + commit shas; v8 pipeline_mode column in v5+ schema.       |
| Phase 7.3 + 7.4 — Codex (drilldown + SSOT-INDEX)             | `unified-trading-pm@7ac15cf4`                                                   | pipeline_mode as outermost partition note; SSOT-INDEX register entry.                              |
| Foot-gun #3 issue doc (workspace governance)                 | (content via `@351e0a2e` Tab 5 hijack but durable on origin)                    | Documents 4 foot-gun #3 incidents in this session + recommends `git commit -o <files>` mitigation. |
| Manifest v7→v8 schema migration design (Tab 3 sep item 3)    | `unified-trading-pm@10ac1f5f`                                                   | DRAFT pending Tab 2 Phase 11 slice b spec for `ServiceEmissionStateEnum` closed-set values.        |
| Expected_universe v2 design (Tab 3 sep item 4)               | `unified-trading-pm@6320a8b5`                                                   | Catalog-aware cross-bucket join, ~190M rows estimate.                                              |
| Cross-asset rescan design (Tab 3 sep item 5)                 | `unified-trading-pm@cc67e904`                                                   | Class A/B/C flip schema; launcher script DEFERRED (sub-agent rate-limited).                        |

**Pending (operator-gated or follow-up sub-agents):**

- Phase 3 — Operator-gated VM execution (operator runs after Phase 0 audit results in §§(b)(c)(d)(e)(h)).
- Phase 4 — Workspace-wide consumer sweep (parallel with Phase 3 per plan DAG).
- Phase 5.2 — MTDS / MDPS path probers fallback (separate sub-agent).
- Phase 5.3 — Sports + DeFi `candidate_parquet_paths` extension (separate sub-agent).
- Phase 6 — Residual phantom cleanup (sequential after Phase 3.6).
- Phase 8 — Reader fallback removal (T+30d, ~2026-06-15).
- Phase 9 — Final workspace-wide QG sweep (sequential after Phase 6).
- Cross-asset rescan launcher script + watchdog dict update (sub-agent rate-limited; design doc shipped at `cc67e904`).

**Foot-gun #3 incidents this session (4 total — see
[`../archive/issues/foot_gun_3_double_strike_2026_05_08.md`](../archive/issues/foot_gun_3_double_strike_2026_05_08.md)):**

1. PM@`784f2bfe` — sub-agent's commit message says "Phase 0 pre-audit doc" but actual diff is +58 lines to Tab 1's
   defi_master_2026_05_07.md (foreign content under sub-agent's message).
2. PM@`12483f5b` — sub-agent's plan-flip commit (correct +/-8) but ALSO bundled Tab 4's
   `live_pipeline_preaudit_2026_05_08.md` (+408 lines).
3. PM@`351e0a2e` — Tab 5's deploy_missing commit hijacked Tab 3's foot_gun issue doc into ITS commit.
4. Multiple commit attempts during Phase 7 + design-doc shipping where prek auto-stash + parallel-agent staging raced;
   mitigated by `git commit -o <specific-files>` (Option C from the issue doc) which scoped commits regardless of
   foreign staged work.

**Sub-agents F + G** (Manifest v7 design + cross-asset rescan launcher) hit Anthropic API rate limit mid-session
(`You've hit your limit · resets May 10 at 8pm`). Re-done in foreground (this main agent); launcher script for
cross-asset rescan deferred.
