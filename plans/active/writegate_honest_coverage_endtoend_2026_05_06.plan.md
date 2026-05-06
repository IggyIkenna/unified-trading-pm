---
type: plan
locked_by: live-defi-rollout
locked_since: 2026-05-06
created: 2026-05-06
companion_handover: shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md
parent_plan: shard_granularity_ssot_propagation_2026_05_06.plan.md
supersedes_phases:
  - shard_granularity_ssot_propagation_2026_05_06.plan.md § Phase 1 Tier 1 #1 (MDPS 1440-NaN, paused — now scoped here)
  - shard_granularity_ssot_propagation_2026_05_06.plan.md § Phase 1 Tier 2 raw-tables (sports available_at, paused — now
    scoped here)
status: drafted
---

# Write-Gate + Honest-Coverage End-to-End — Plan

**Branch:** `live-defi-rollout` **Goal:** Collapse two double-SSOT bugs (MDPS empty-handling, sports `available_at`
stamping) and the partial-bundle silent-acceptance class into one cohesive contract change at
`ManifestWriter.record_captured`. Forward + retrospective + UI + QG enforcement so post-merge backfill % across every
service means **real** % (no fake captured rows, no NaN placeholders, no partial bundles passing as complete).

This plan resolves the 3 CRITICAL questions in the parent HANDOVER (MDPS contract shape / sports raw-tables migration /
cluster-validation sequencing) into a single shippable work-package per the user's framework: production-grade, no
double-SSOT, schema/manifest/GCS migrations sanctioned where needed, no compat shims.

---

## Cross-cutting principles (confirmed 2026-05-06)

These bind every todo in this plan. Workspace CLAUDE.md additions in Phase 1C codify them:

1. **Production-grade `>99%` means real `>99%`** — denominator clipped to legitimately-coverable shards (per existing
   `SOURCE_COVERAGE_START` / `KNOWN_COVERAGE_GAPS` / `venue_trading_calendar`); numerator counts only honest captures
   (real rows passing the 4-pillar write-gate). NaN placeholders + partial bundles + silent per-schema drops do not
   count.

2. **Single SSOT only — no double-SSOT in the data-saving methodology.** Where two paths exist for the same outcome, one
   is deleted. No `_create_empty_output()` AND `_handle_empty_tick_data()`; no `_ensure_timestamp` shim AND per-source
   `stamp_available_at_*` helpers; no parallel v3-shape `_write_manifest_records` AND v6 canonical writer; no inline
   NaN-ratio gate AND UTL helper.

3. **Schema, manifest, GCS, code rewrites are sanctioned wherever the SSOT requires them.** No backwards-compatibility
   shims, no fallback readers for legacy shapes (one documented exception: hive-vocab `category=` vs `asset_group=` per
   existing CLAUDE.md asset-group section). Migration scripts replace fallback readers; fallback readers get deleted.

4. **Live = batch = same data, same fields, same timing semantics.** Live just gets the data through different
   sources/endpoints because some live sources are faster than the canonical historical one. Historical writes are
   timestamped as if collected by the live pipeline (the source the live pipeline would actually use). Live and batch
   produce identical schemas; they do NOT differ in data_types or fields available.

5. **`available_at` is per-row, stamped at write-time, equal to when our live pipeline would have actually got that
   row's information.** Never derived at read-time. For multi-source data_types, the source priority registry (Phase 1B)
   determines which source's timestamp is used.

6. **Cluster validation is mandatory at `record_captured` for bundled shards.** No opt-out, no helper-call-pattern, no
   "will wire it later." Runtime enforcement (UTL guard) + static enforcement (QG STEP 5.64). If the data_type is in
   `BUNDLED_DATA_TYPES`, `expected_root_clusters` must be passed or the call raises.

7. **Three-category empty-output decision tree.** Every condition that could produce an empty result resolves to ONE of:
   - **A. Source returned 0 ticks for the requested window** → `record_empty(row_key, attempted_at)`. Honest absence.
   - **B. Source returned ticks; ALL fall outside the requested day after `interval_idx` filter** →
     `record_failed(UpstreamTimestampBiasError(observed_dates, expected_day, n_ticks))`. **Upstream bug — partition
     mislabeled at MTDS write-time, OR source replay covered wrong window, OR clock-skew. NOT honest empty.** Paired
     upstream fix in MTDS (Phase 2.B).
   - **C. Rows in window but downstream calc dropped all rows due to NaN/malformed source fields** →
     `record_failed(MalformedTickFieldError(field, n_dropped, sample_values))`. Data-quality issue worth diagnosing.
   - No fourth category. No silent NaN placeholder rows. The `_create_empty_output()` method is deleted from
     `base_adapter`.

---

## Temporary states + their canonical follow-up plans

**Principle**: nothing in this plan accepts a temporary state as final. Every partial implementation lists its named
successor plan that ships the proper fix. No "we'll fix it later" without a doc.

| Temporary state shipped here                                                                                     | What it means                                                                                                                                                                                                                                                                                                                                                             | Successor plan / phase                                                                                                  |
| ---------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `BUNDLED_DATA_TYPES` includes `prediction_canonical_question_group` with `PREDICTION_GROUPS = {}` empty registry | The slot is reserved + cluster guard is wired. No caller currently uses this data_type (Polymarket shards per-`base_asset` per current audit). When canonical_question_group SSOT lands, registry gets populated AND Polymarket migrates AND cluster guard fires meaningfully. Until then: any caller using this data_type fails loud → forces them to wait for the SSOT. | `prediction_canonical_question_group_uac_ssot_2026_<TBD>.plan.md` (greenfield UAC build; see Tracked Open Questions §1) |
| (no temporary state on `match_end_time`)                                                                         | `match_end_time` is detected from real source signals, not a constant. Detection cascade in Phase 2.D below: api_football native field → SFI progressive-stats freeze → footystats / understat fallbacks → last-resort `kickoff + 120min` only when all else missing (and that case marks the row with a low-confidence flag).                                            | (in-scope)                                                                                                              |
| MTDS v6 columns owner sign-off                                                                                   | Wired per the explicit decision rule (see Phase 2.A). UAC owner verifies completeness post-merge in case any data_type's row carries v6-relevant fields we missed.                                                                                                                                                                                                        | In-plan Phase 5 verification todo.                                                                                      |
| `SOURCE_PRIORITY` registry top-entry-only                                                                        | Phase 1B seeds the priority-1 source per `(asset_group, data_type)`. Multi-source merge (timestamp-availability > coverage > info-richness > merge-different-fields per user 2026-05-06) is its own design pass.                                                                                                                                                          | `multi_source_priority_merge_2026_<TBD>.plan.md` (Tracked Open Questions §7)                                            |
| MDPS / features-\* `feature_group → required_inputs[]` DAG inlined per-service                                   | Three services keep their local DAGs (features-onchain, features-sports, features-delta-one). Lookahead-bias enforcement still runs but reads from per-service DAG.                                                                                                                                                                                                       | `feature_dag_uac_ssot_2026_<TBD>.plan.md` (Tracked Open Questions §2)                                                   |

Anything not listed here is intended as the final shape post-merge. If a reviewer finds a hidden temporary state, file
it as a plan-amendment todo before merging.

---

## Pre-audit blast radius

### MDPS (market-data-processing-service)

Confirmed 53 `_create_empty_output` callsites across `app/adapters/{cefi,defi,tradfi,sports,prediction}/`. Sample paths
showing the bug class:

| Adapter                                                                                             | Sites                  | Notes                                                               |
| --------------------------------------------------------------------------------------------------- | ---------------------- | ------------------------------------------------------------------- |
| `defi/swap_adapter.py`                                                                              | 106                    | Confirmed path B (1440 NaN bars when ticks present but outside day) |
| `cefi/trades_adapter.py`                                                                            | 69, 74, 83             | Multiple path types; needs A/B/C decision per site                  |
| `cefi/derivative_adapter.py`                                                                        | 69, 99                 |                                                                     |
| `cefi/book_snapshot_adapter.py`                                                                     | 87, 117                |                                                                     |
| `cefi/futures_chain_adapter.py`                                                                     | 75, 105                | Bundle data_type — also Phase 2.B cluster-validation site           |
| `cefi/liquidations_adapter.py`                                                                      | 143, 173               | Liquidations are legitimately sparse — most sites probably path A   |
| `cefi/options_chain_adapter.py`                                                                     | 164, 194               | Bundle — cluster validation site                                    |
| `tradfi/trades_adapter.py`, `tradfi/tbbo_adapter.py`                                                | (multiple)             |                                                                     |
| `sports/odds_snapshot_adapter.py`, `sports/odds_movement_adapter.py`, `sports/arbitrage_adapter.py` | (multiple)             |                                                                     |
| `prediction/*_adapter.py`                                                                           | (count TBD in Phase 0) |                                                                     |

Existing honest path: `app/core/{batch,live}_workers.py:189` `_handle_empty_tick_data` (called from line 269 of
live_workers — so the routing infra exists; adapters bypass it).

### MTDS (market-tick-data-service)

| File                                        | Line     | Concern                                                                                               |
| ------------------------------------------- | -------- | ----------------------------------------------------------------------------------------------------- |
| `market_tick_data_service/raw_tick_hive.py` | (writer) | Phase 2.B: write-time `tick.timestamp.date()` vs `day=` partition validation; reject + log mismatches |
| `adapters/databento_adapter.py`             | 30–48    | `_PerSchemaFailure` already shipped (parent plan Phase 1) — verify                                    |
| `adapters/tardis/options_chain.py`          | 596–702  | Bundle write — Phase 2.B cluster validation site                                                      |
| `adapters/tardis/futures_chain.py`          | similar  |                                                                                                       |
| `adapters/databento/options_chain.py`       | 869–985  | Bundle write — Phase 2.B cluster validation site                                                      |
| `umi_tick_provider.py`                      | 225      | `category=` → `asset_group=` vocab cleanup                                                            |

### features-sports-service

| File                                                        | Line               | Concern                                                                        |
| ----------------------------------------------------------- | ------------------ | ------------------------------------------------------------------------------ |
| `cli/handlers/batch_handler.py`                             | 76–91              | `TABLE_TO_EXPORT` 14 entries — drives Phase 2.C per-table available_at logic   |
| `cli/handlers/batch_handler.py`                             | 146                | `_ensure_timestamp` shim (DELETE in Phase 2.C)                                 |
| `cli/handlers/batch_handler.py`                             | 383, 465, 528, 597 | `_ensure_timestamp` callsites — replace with per-source `stamp_available_at_*` |
| `cli/batch_write.py`                                        | 38, 88             | Sibling `_ensure_timestamp` (DELETE)                                           |
| `exporters/exports.py`                                      | (each export\_\*)  | Per-table `available_at` stamping logic                                        |
| `exporters/_fetch_runner.py` (or wherever the runner lives) | —                  | Add `_FETCH_COMPLETED_AT: dict[table, datetime]` for the 8 reference tables    |

### instruments-service (sports schemas)

Schema additions (in `unified_reference_data_interface` / sports schemas):

| Schema                                                  | Add column                                                                                                    | Reason                                                                                                          |
| ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `FIXTURES_COLUMNS`                                      | `announced_at` (timestamp UTC)                                                                                | Fixtures are scheduled days/weeks pre-kickoff; this is the row's true `available_at`                            |
| `FIXTURE_EVENTS_COLUMNS`                                | `event_time` (timestamp UTC)                                                                                  | Per-event truth — already per-row in semantics; verify column exists or add                                     |
| `INJURIES_COLUMNS`                                      | `report_time` / `occurrence_time` (timestamp UTC)                                                             | Per-injury truth — when the injury was reported / when it happened (occurrence wins for events during fixtures) |
| `FIXTURE_STATS_COLUMNS`, `FIXTURE_PLAYER_STATS_COLUMNS` | `match_end_time` (timestamp UTC)                                                                              | Post-match aggregates — earliest moment we'd have the full row                                                  |
| `FIXTURE_LINEUPS_COLUMNS`                               | `available_at` derived as `kickoff_utc − 60min` (constant); no schema column needed if we stamp at write-time | Conservative — lineups are always at LEAST 60min before, often 1–2h                                             |

Blast radius for schema bumps: **0 references to these schemas outside features-sports-service** (verified:
`FIXTURE_STATS_COLUMNS|FIXTURE_EVENTS_COLUMNS|FIXTURE_LINEUPS_COLUMNS|FIXTURE_PLAYER_STATS_COLUMNS|INJURIES_COLUMNS` —
47 hits all inside features-sports-service, 0 in MDPS / strategy-service / features-onchain). Schema bumps are free.

### UTL (unified-trading-library)

| File                       | Line                        | Change                                                                                                                                                 |
| -------------------------- | --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------- |
| `manifest_writer.py`       | 97                          | `ClusterCoverageError` ✓ exists                                                                                                                        |
| `manifest_writer.py`       | 1098                        | `check_cluster_coverage` — make private (`_check_cluster_coverage`); no longer public API                                                              |
| `manifest_writer.py`       | 1163                        | `record_captured` — add `expected_root_clusters: Mapping[str, int] \| None` + `cluster_extractor: Callable                                             | None`kwargs; raise`MissingClusterValidationError`when`data_type ∈ BUNDLED_DATA_TYPES` and kwargs not passed |
| `errors.py`                | new                         | `UpstreamTimestampBiasError`, `MalformedTickFieldError`, `MissingClusterValidationError`                                                               |
| `availability_stamping.py` | (already exists per LIFT-3) | Add `stamp_available_at_post_match`, `stamp_available_at_announcement`, `stamp_available_at_explicit`, `stamp_available_at_kickoff_offset(minutes=60)` |

### UAC (unified-api-contracts)

New SSOT registries (each under `unified_api_contracts.canonical.crosscutting.honest_coverage` or similar):

| Registry                        | Type                                                   | Content                                                                                                                                                         |
| ------------------------------- | ------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `BUNDLED_DATA_TYPES`            | `frozenset[str]`                                       | `{"options_chain", "futures_chain", "prediction_canonical_question_group", "sports_fixture_bundle"}`                                                            |
| `DATA_TYPE_TO_CLUSTER_REGISTRY` | `dict[str, str]`                                       | `data_type` → registry-symbol-name (e.g. `"options_chain"` → `"OPTIONS_CLUSTERS"`)                                                                              |
| `OPTIONS_CLUSTERS`              | `dict[root, dict[cluster, min_rows]]`                  | ES.OPT seed already exists in instruments-service per HANDOVER; lift to UAC                                                                                     |
| `FUTURES_CLUSTERS`              | (analogous)                                            | Combo/spread cluster taxonomies; greenfield-light                                                                                                               |
| `SPORTS_FIXTURE_CLUSTERS`       | (TBD)                                                  | Greenfield — per-fixture aggregate cluster (bookmakers per fixture, etc.)                                                                                       |
| `SOURCE_PRIORITY`               | `dict[(asset_group, data_type), list[str]]`            | Source rank by tie-breakers (timestamp-availability > coverage > info-richness) — Phase 1B writes top entry only; multi-source merge logic deferred             |
| `AVAILABILITY_AT_SEMANTICS`     | `dict[(asset_group, data_type), AvailabilitySemantic]` | Per-data_type stamping rule (`fetch_completed_at`, `kickoff_minus_60min`, `match_end_time`, `event_time`, `report_time`, `announced_at`, `forecast_issue_time`) |

Existing UAC artifacts to preserve: `SOURCE_COVERAGE_START`, `DATA_TYPE_COVERAGE_START`, `KNOWN_COVERAGE_GAPS`,
`venue_trading_calendar`, `RAW_TICK_ASSET_GROUP_HIVE_KEY` / `_LEGACY`.

### deployment-ui / deployment-api

| Surface                  | Change                                                                                                                                                                                            |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Data-status panel        | Render `attempted_failed` reasons distinctly per typed error (color + drill-down): `EmptyPlaceholderBugBackfill`, `ClusterCoverageError`, `UpstreamTimestampBiasError`, `MalformedTickFieldError` |
| Schema-view per-leaf     | Show `available_at` min/max/null-count alongside row-count + per-column NaN ratio                                                                                                                 |
| Per-pillar breakdown     | New columns: `failed_row_count` / `failed_nan_ratio` / `failed_schema` / `failed_cluster` per shard                                                                                               |
| Live-vs-historical alert | Surface when historical-mode produces the same `data_type` for a date that is in the live window (would imply double-write)                                                                       |

---

## Phase DAG

```
Phase 0 (audit, mostly done)
  → Phase 1A (UTL contract)  ──┐
  → Phase 1B (UAC SSOTs)    ──┤── Phase 2 (parallel: 2A MDPS, 2B MTDS, 2C features-sports, 2D instruments-service)
  → Phase 1C (CLAUDE.md)    ──┘     │
                                    ▼
                              Phase 3 (Retrospective: 3A reconcilers, 3B GCS stamping, 3C pre-v6 cleanup)
                                    │
                                    ▼
                              Phase 4 (UI + alerts) ── runs partly in parallel with Phase 2
                                    │
                                    ▼
                              Phase 5 (Validation + honest-coverage baseline)
```

QG gates between every phase. No Phase N+1 todo starts until every Phase N todo is checked + workspace QG passes on
every repo touched in Phase N.

---

## Concurrent in-flight stream — sports phantom FIXTURES recovery (2026-05-06)

A separate stream is running in parallel to this plan, owned by the
`sports_phantom_fixtures_recovery_2026_05_06.plan.md` plan. Be aware while
executing this plan because the recovery touches the same `ManifestWriter` /
orchestrator surfaces this plan modifies — the two streams must not step on
each other.

### What's running

**Live VM (as of 2026-05-06 13:54 UTC)**: `af-backfill-20260506-135454` on
asia-northeast1-c, e2-standard-4, running api_football FIXTURES backfill
2020-06-06 → 2026-05-04. Estimated ~10h wall-clock (most dates are
no-fixture days = fast paths; match days ~80s each for the api_football
fetch + per-league manifest write). After this VM auto-shuts, a sequential
chain runner (`deployment-service/scripts/vm/run-sports-phantom-downstream-chain.sh`,
commit `5be53a7`) launches 5 follow-on VMs (PLAYER_STATS / FIXTURE_STATS /
FIXTURE_EVENTS / FIXTURE_LINEUPS / INJURIES) — singleton-locked on
`af-backfill-` prefix; ~3-5h sequential.

### Why it's running

The orchestrator's FIXTURES adapter pre-2026-05-06 was emitting
`manifest.add(row_count=0)` for every Prediction-tier league × date (zero-fixture
days), creating ~100k phantom `captured` rows that violate CLAUDE.md "4 pillars"
rule #1. Root-cause writer fix shipped in instruments-service `f36651c`. The
recovery sequence:

1. `flip_phantom_fixtures_zero_rows.py` (instruments-service `962982e`) flipped
   100k phantoms `captured`+`instrument_count=0` → `empty_confirmed`. **Wrong**: orchestrator
   skips both `captured` and `empty_confirmed`.
2. `flip_phantom_to_attempted_failed.py` (`2821111`) re-flipped to
   `attempted_failed` + extended to 75k cap-zero rows on per-fixture downstreams
   (PLAYER_STATS / FIXTURE_STATS / FIXTURE_EVENTS / FIXTURE_LINEUPS / INJURIES).
   **Insufficient**: discovered `check_shard_freshness` ignores
   `capture_status` — attempted_failed treated as "fresh" by orchestrator
   pre-flight (see `feedback_check_shard_freshness_ignores_capture_status.md`).
3. `write_phantom_reflip_per_vm_shard.py` (`2d18d0d`) mirrored corrective rows
   to a fresh per-VM shard so reader's fall-back merge sees them past the 120s
   canonical mtime threshold (see `feedback_manifest_reader_staleness_per_vm_fallback.md`).
4. `delete_phantom_rows_from_shards.py` (`73be000`) **DELETED** the 176k
   phantom rows (canonical + 10 per-VM shards with backups). Goal: orchestrator
   sees them as MISSING and re-fetches.
5. **Discovered**: orchestrator pre-flight is at (date, data_type) granularity,
   not per-league — once any league has FIXTURES for date X, the date is "fresh"
   and the WHOLE date is skipped. See
   `feedback_orchestrator_freshness_per_league_granularity.md`.
6. **Orchestrator patched** (instruments-service `d73565a`) to defer pre-flight
   to per-entity handlers when `expected[]` contains any of 17 sports
   per-league entities. Per-entity handlers' existing `_should_skip_date_for_per_league`
   pattern (orchestrator.py:490) handles per-(date, data_type, league_id)
   correctly. **THIS is the architectural fix this plan should be aware of.**

The currently-running VM v6 was launched after the patch + confirmed working in
production: log shows `"date=2020-06-07: deferring pre-flight to per-league
entity handlers"` + `"SPORTS: No fixtures for date=2020-06-07 — wrote
empty_confirmed markers for 33 leagues"`. Patch is live + correct behavior.

### Potential effects on this plan

**Surfaces touched that overlap with this plan's scope:**

1. **`ManifestWriter` per-VM shard merge** (`unified-trading-library/.../manifest_writer.py:2222`):
   the recovery stream's `delete_phantom_rows_from_shards.py` mutated the
   `_index/per_vm/*.parquet` set in the sports bucket. If this plan's Phase 1A
   `record_captured` contract change introduces new shard-key columns or
   migrates existing ones, the recovery's deleted-then-rewritten rows must
   migrate cleanly. The DELETE script's signature filter
   (`(capture_status='attempted_failed' AND error_reason marker) OR
   (capture_status='captured' AND instrument_count==0)`) leaves all columns
   otherwise unchanged, so a v6→v7 schema upgrade should be transparent.

2. **`check_shard_freshness` (UTL)**: this plan's Phase 1A may add per-row
   capture_status filtering to the freshness check (closing the
   "attempted_failed treated as fresh" hole architecturally rather than via
   per-service defer-to-handler workaround). When that lands, the
   per-service patch in instruments-service `d73565a` becomes redundant but
   harmless — it just makes is_fresh=False unconditionally for sports
   per-league entities, which is what the new UTL behavior would do anyway.
   Recommend keeping the instruments-service patch in place until UTL fix
   ships + verifying the new path doesn't regress (test: launch a
   `--sports-entity FIXTURES` VM, confirm it doesn't skip-cycle).

3. **Manifest backups in canonical bucket**: recovery wrote 4 backup blobs
   in `gs://instruments-store-sports-central-element-323112/_index/`:
   - `availability_index.20260506-111222.bak.parquet` (pre-flip-1)
   - `availability_index.20260506-112347.bak.parquet` (pre-flip-2)
   - 10 per-VM shard `.20260506-120021.bak.parquet` siblings (pre-DELETE)
   These are reversibility safety nets. **Do not delete** them while the
   recovery VMs are still running. After verify (~2026-05-07) they can be
   purged.

4. **`af-backfill-` VM concurrency**: the recovery stream's chain runner
   uses the singleton-locked launcher (`launch-api-football-backfill-vm.sh`).
   This plan's Phase 2.D instruments-service work (writer-side changes to
   `_create_empty_output` callsite categorisation) does not launch
   `af-backfill-` VMs, so no direct lock conflict — but if a Phase 2.D
   smoke test wants to launch one, sequence after the chain runner has
   finished its 5 entities or use `--force`.

5. **Orchestrator `defer pre-flight` log line**: the new log signature is
   `"date={D}: deferring pre-flight to per-league entity handlers (sports
   per-league mode; expected={...})"`. If this plan adds telemetry/structured
   events around pre-flight, this is a new log shape to be aware of.

### Memory entries to read for context

- `project_sports_phantom_fixtures_recovery_2026_05_06.md` — full session log
- `feedback_orchestrator_freshness_per_league_granularity.md` — the
  architectural finding that drives the orchestrator patch
- `feedback_check_shard_freshness_ignores_capture_status.md` — the related
  UTL-level finding
- `feedback_manifest_reader_staleness_per_vm_fallback.md` — the 120s mtime
  threshold gotcha (relevant to any one-shot manifest mutation script this
  plan's Phase 3 might write)

---

## Phase 0 — Pre-audit + remaining blast-radius gaps

- [x] [AUDIT] P0. instruments-service delta vs HANDOVER findings (done 2026-05-06; see HANDOVER §instruments-service
      post-audit).
- [ ] [AUDIT] P0. MDPS — categorise all 53 `_create_empty_output` callsites into A / B / C. Output: a per-callsite
      manifest table file:line → category. 1-2 days.
- [ ] [AUDIT] P0. MDPS prediction adapters — count `_create_empty_output` sites + classify (not yet listed in audit).
- [ ] [AUDIT] P0. MTDS — confirm bundle adapter list (options_chain, futures_chain, prediction, sports_fixture_bundle) +
      each adapter's row schema (so cluster_extractor can be written).
- [ ] [AUDIT] P0. features-sports — for each of the 14 `TABLE_TO_EXPORT` entries, document the actual source columns
      currently present. Confirm we have the columns required to stamp the new `available_at` semantics (e.g.
      `match_end_time` is present on `fixture_stats` rows; `event_time` on `fixture_events`; `report_time` on
      `injuries`).
- [ ] [AUDIT] P0. Multi-source coverage matrix per `(asset_group, data_type)` — list every source we currently use AND
      every alternative we could use. Drives the `SOURCE_PRIORITY` registry seeding in Phase 1B.
- [ ] [AUDIT] P0. instruments-service sports schemas — confirm the columns to add (`announced_at` on fixtures;
      `event_time` on fixture_events; `report_time` on injuries; `match_end_time` on fixture_stats /
      fixture_player_stats).

QG between Phase 0 and Phase 1A/1B/1C: audit manifest reviewed by user; per-callsite A/B/C decisions signed off;
SOURCE_PRIORITY tie-breaker rules confirmed for each (asset_group, data_type) where multi-source applies.

---

## Phase 1A — UTL contract changes (sequential, blocks all)

- [ ] [SCRIPT] P0. Add 3 new typed errors to `unified_trading_library/errors.py`: -
      `UpstreamTimestampBiasError(observed_date_range: tuple[date, date], expected_day: date, n_ticks_seen: int, instrument_id: str | None = None)`
      — path B -
      `MalformedTickFieldError(field: str, n_dropped: int, sample_values: list[Any] = None, instrument_id: str | None = None)`
      — path C - `MissingClusterValidationError(data_type: str, expected_registry_key: str)` — record_captured guard
- [ ] [SCRIPT] P0. `manifest_writer.py:1163` `record_captured` signature change: - Add
      `expected_root_clusters: Mapping[str, int] | None = None` - Add
      `cluster_extractor: Callable[[str], str] | None = None` - Add `symbol_column: str = "symbol"` (currently in
      helper) - Inside `record_captured`: if `data_type in BUNDLED_DATA_TYPES` (imported from UAC) and
      `expected_root_clusters is None` → raise
      `MissingClusterValidationError(data_type, DATA_TYPE_TO_CLUSTER_REGISTRY.get(data_type))`. - When kwargs present:
      call `_check_cluster_coverage` internally; on `ClusterCoverageError` return → call `record_failed(...)` instead of
      writing the parquet.
- [ ] [SCRIPT] P0. `manifest_writer.py:1098` rename `check_cluster_coverage` → `_check_cluster_coverage`. Remove from
      `__all__`. Internal-only.
- [ ] [SCRIPT] P0. `availability_stamping.py` extend with: -
      `stamp_available_at_kickoff_offset(df, kickoff_col="kickoff_utc", minutes=60)` — for lineups -
      `stamp_available_at_post_match(df, kickoff_col="kickoff_utc", duration_min=120, scrape_latency_min=15)` — for
      fixture_stats / fixture_player_stats - `stamp_available_at_event_time(df, event_time_col="event_time")` — per-row
      pass-through, used for fixture_events + injuries (when row has its own time) -
      `stamp_available_at_announcement(df, announced_col="announced_at")` — for fixtures -
      `stamp_available_at_explicit(df, fetch_completed_at: datetime)` — for 8 reference tables
- [ ] [SCRIPT] P0. New UTL helper `manifest_writer.assert_available_at_present(df: pd.DataFrame)` — raises
      `LookaheadBiasError` (existing) if `available_at` column missing or contains NaN. Called automatically from
      `record_captured` when not in cluster path.
- [ ] [TEST] P0. UTL unit tests: - `record_captured` raises `MissingClusterValidationError` for every entry in
      `BUNDLED_DATA_TYPES` when kwarg not passed. - `record_captured` succeeds + writes when kwargs passed and clusters
      complete. - `record_captured` calls `record_failed` (no parquet write) when clusters incomplete. -
      `record_captured` calls `assert_available_at_present` and raises `LookaheadBiasError` on missing/null
      `available_at`. - `record_empty` accepts `attempted_at` + writes manifest row only. - `record_failed` accepts each
      new typed error variant + writes appropriate `error_reason`.
- [ ] [QG] P0. Add UTL `quality-gates.sh` step that fails if `_create_empty_output`-style placeholder return patterns
      are reintroduced (grep-based static check; can be fooled but catches the obvious).
- [ ] [DEP] P0. Bump UTL version (semver-agent handles; do NOT bump manually) on merge.

QG between Phase 1A and Phase 2: UTL tests green; UTL pushed to live-defi-rollout; downstream consumers rebuild against
new UTL pinned in workspace-manifest.json.

---

## Phase 1B — UAC SSOTs (parallel with 1A)

- [ ] [SCRIPT] P0. New module `unified_api_contracts/canonical/crosscutting/honest_coverage.py`: -
      `BUNDLED_DATA_TYPES: frozenset[str]` initial seed: - `"options_chain"` — registry: `OPTIONS_CLUSTERS` (populated,
      lifted from instruments-service ES.OPT 11-cluster taxonomy; per-root entries) - `"futures_chain"` — registry:
      `FUTURES_CLUSTERS` (greenfield; ES + MES seeds; expand per-root in this plan) - `"ODDS_SNAPSHOT"`,
      `"ODDS_MOVEMENT"`, `"ARBITRAGE"` — registry: `SPORTS_FIXTURE_CLUSTERS` (greenfield; per-(league-tier → bookmaker
      set); seed tier-1 EU football here, expand per-tier in this plan + follow-up) -
      `"prediction_canonical_question_group"` — registry: `PREDICTION_GROUPS = {}` **EMPTY temporary state**. Slot
      reserved + cluster guard wired. NO caller currently uses this data*type (Polymarket shards per-`base_asset` per
      current audit). When canonical_question_group SSOT lands in
      `prediction_canonical_question_group_uac_ssot_2026*<TBD>.plan.md`, registry gets populated AND Polymarket migrates AND cluster guard fires meaningfully. Documented in §"Temporary states + their canonical follow-up plans".     - `DATA_TYPE_TO_CLUSTER_REGISTRY:
      dict[str,
      str]`(data_type → registry symbol name).     -`OPTIONS_CLUSTERS`lifted from instruments-service (ES.OPT 11-cluster taxonomy as seed; per-root entries).     -`FUTURES_CLUSTERS`(greenfield; ES + MES seeds; spreads + butterflies per root).     -`SPORTS_FIXTURE_CLUSTERS` (greenfield; per-`league_tier`→ expected bookmaker set; tier-1 EU football seed; tier-2 / tier-3 expansion in this plan or follow-up).     -`PREDICTION_GROUPS
      = {}` (empty placeholder; gets populated by canonical_question_group SSOT plan).
- [ ] [SCRIPT] P0. New module `unified_api_contracts/canonical/crosscutting/source_priority.py`: - `SourcePriority` enum
      or dataclass per `(asset_group, data_type)`. - `SOURCE_PRIORITY: dict[tuple[str, str], list[str]]` — ordered list
      of source keys, top entry is primary. - Tie-breaker rules documented in module docstring (timestamp-availability >
      coverage > info-richness > merge-different-fields). - Phase 1B seeds the dict for sports data_types (lineups,
      fixture_events, injuries) with single-source entries; multi-source merge logic deferred.
- [ ] [SCRIPT] P0. New module `unified_api_contracts/canonical/crosscutting/availability_semantics.py`: -
      `AvailabilitySemantic = Literal["fetch_completed_at", "kickoff_minus_60min", "match_end_time", "event_time", "report_time", "announced_at", "forecast_issue_time", "publication_time"]` -
      `AVAILABILITY_AT_SEMANTICS: dict[tuple[str, str], AvailabilitySemantic]` — per-(asset_group, data_type) stamping
      rule. - Sports seeds: `("sports", "FIXTURES")` → `announced_at`; `("sports", "FIXTURE_LINEUPS")` →
      `kickoff_minus_60min`; `("sports", "FIXTURE_EVENTS")` → `event_time`; `("sports", "INJURIES")` → `report_time`;
      `("sports", "FIXTURE_STATS"|"FIXTURE_PLAYER_STATS")` → `match_end_time`; reference tables →
      `fetch_completed_at`. - CeFi / DeFi / TradFi / prediction seeds: TBD per Phase 0 audit (most are fetch-time /
      event-time straightforward).
- [ ] [SCRIPT] P0. Lift instruments-service ES.OPT cluster lookup (`reference_data/options_cluster_lookup.py`) to UAC
      `OPTIONS_CLUSTERS` registry. Delete the instruments-service module; update consumers.
- [ ] [TEST] P0. UAC unit tests: - Every entry in `BUNDLED_DATA_TYPES` has a corresponding entry in
      `DATA_TYPE_TO_CLUSTER_REGISTRY`. - Every registry symbol referenced in `DATA_TYPE_TO_CLUSTER_REGISTRY` resolves to
      a non-empty dict. - Every `(asset_group, data_type)` shipped by any service has an entry in
      `AVAILABILITY_AT_SEMANTICS` (parametrise over service registries). - Every multi-source `(asset_group, data_type)`
      has an entry in `SOURCE_PRIORITY`.

QG between Phase 1B and Phase 2: UAC tests green; UAC pushed; consumer-pin propagates.

---

## Phase 1C — Workspace CLAUDE.md rule additions (parallel with 1A/1B)

- [ ] [DOCS] P0. Add to `unified-trading-pm/cursor-configs/CLAUDE.md` (between "No fire-and-forget VM launches" and
      "Sports GCS path SSOT", or wherever fits):

      **§ "Live = batch — same data, different sources"**
      Live and batch are operational modes of the SAME pipeline. They produce identical schemas + identical `data_types` + identical fields. They differ only in WHICH source serves a given `(asset_group, data_type)`, because some sources lag others on real-time emission. Historical writes MUST be timestamped with the `available_at` we'd actually have in live mode (the source priority registry's top entry's emission time, not the canonical historical source's slower archive time). Applies to every asset_group; canonical example: sports injuries — historical source may give report_time post-match, but live pipeline scrapes a faster source mid-match; historical writes stamp with the live-pipeline-equivalent time, NOT the historical-source post-match time.

      **§ "Three-category empty-output decision (MDPS + every per-shard adapter)"**
      Every condition producing an empty result resolves to ONE of: A (source returned 0 ticks → `record_empty`), B (ticks present, all outside requested day → `record_failed(UpstreamTimestampBiasError)` + paired upstream MTDS partitioner fix), C (ticks in window, downstream calc dropped due to malformed fields → `record_failed(MalformedTickFieldError)`). No fourth category. No silent NaN placeholder rows. `_create_empty_output()`-style methods are banned; `base_adapter` does not provide one.

      **§ "Cluster validation mandatory at record_captured"**
      For any `data_type ∈ UAC.BUNDLED_DATA_TYPES`, `record_captured` requires `expected_root_clusters` + `cluster_extractor` kwargs. UTL guard raises `MissingClusterValidationError` if absent. QG STEP 5.64 statically walks every `record_captured(` callsite + asserts the kwargs are passed when the literal data_type is bundled. Runtime + static enforcement; no opt-out.

      **§ "`available_at` is per-row, write-time, equal to live-pipeline-arrival"**
      Every shard's parquet contains an `available_at` column. Each row's value = when the live pipeline would have actually had that row's information (per `UAC.AVAILABILITY_AT_SEMANTICS`). For multi-source data_types, the `UAC.SOURCE_PRIORITY` top entry determines the source whose timing is used. NEVER derived at read-time. Stamping helpers: `unified_trading_library.availability_stamping.stamp_available_at_*`. UTL's `record_captured` calls `assert_available_at_present` internally.

- [ ] [DOCS] P0. Update existing CLAUDE.md "Honest absence vs fake placeholders" section with explicit cross-link to the
      three-category decision; rewrite the "Reader/schema-drift bug" sub-bullet to call out path B (timestamp bias) as a
      distinct sub-class.
- [ ] [DOCS] P0. Update `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` to inherit the new sections
      (it's a per-repo synced file).
- [ ] [SCRIPT] P0. Run `bash unified-trading-pm/scripts/propagation/sync-claude-md-to-all-repos.sh` (or the equivalent)
      so per-repo `CLAUDE.md` mirrors pick up the new sections.

QG between Phase 1C and Phase 2: every per-repo `.claude/CLAUDE.md` (or symlink) contains the new sections; validated by
grep.

---

## Phase 2 — Service forward fixes (parallel after 1A+1B+1C)

### Phase 2.A — MDPS forward fixes (delete `_create_empty_output`)

- [ ] [SCRIPT] P0. Delete `_create_empty_output` from `app/adapters/base_adapter.py`. Replace with a private helper
      `_classify_empty_path(tick_data, day_start, day_end) -> Literal["A", "B", "C"]` plus typed exceptions
      `EmptyAfterFilterError` (path A — adapter raises, orchestrator catches → `record_empty`),
      `UpstreamTimestampBiasError` (path B — propagates from UTL), `MalformedTickFieldError` (path C — propagates from
      UTL).
- [ ] [SCRIPT] P0. For each of the 53 callsites: convert `return self._create_empty_output(...)` to
      `raise <appropriate>` per the Phase 0 A/B/C manifest. Code owner sign-off per adapter file.
- [ ] [SCRIPT] P0. Update `_handle_empty_tick_data` in `batch_workers.py` + `live_workers.py` to catch all three
      exceptions + route to `record_empty` (path A) / `record_failed(UpstreamTimestampBiasError)` (path B) /
      `record_failed(MalformedTickFieldError)` (path C).
- [ ] [SCRIPT] P0. Delete `_write_manifest_records` v3-shape parallel write from `orchestration_service.py:329–388`.
      Single canonical v6 path via `canonical_writer` only. (Resolves parent HANDOVER §"❌ MDPS mismatches" item.)
- [ ] [SCRIPT] P0. Wire v6 columns (`quote_asset` / `margin_type` / `combo_type` / `leg_weights`) into
      `canonical_writer.add()` per the explicit decision rule below — no UAC-owner blocking dependency: **Wire (row
      carries v6-relevant info):** - CeFi: `derivative_adapter`, `futures_chain_adapter`, `options_chain_adapter` —
      populate `quote_asset` from instrument metadata (`USD` / `USDT` / `USDC` / `BTC` etc.) + `margin_type` (`linear` /
      `inverse` / `quanto`). DERIBIT inverse vs linear is the canonical disambiguation case — without these columns,
      manifest row-keys collide. - CeFi `book_snapshot_adapter`, `liquidations_adapter`, `trades_adapter` — populate
      `quote_asset` + `margin_type` (same source as above). - TradFi `futures_chain_adapter` — populate `combo_type`
      (`outright` / `spread` / `butterfly` / `condor`) + `leg_weights` (legs JSON list); ES.OPT spreads are the
      canonical case. - TradFi `options_chain_adapter` — populate `combo_type` (`single` / `vertical` / `straddle` /
      etc.) + `leg_weights`. **Skip (leave at default `""`):** - All DeFi adapters (`swap_adapter`, `liquidity_adapter`,
      `market_state_adapter`, etc.) — DEX spot has no margin_type; quote_asset is the second leg of the pool which is
      the data_type axis already. - All sports adapters — irrelevant. - All prediction adapters — irrelevant. Phase 5
      verification todo: UAC owner confirms the wired set matches the v6 schema spec; flag any data_type whose row
      carries v6-relevant info we missed.
- [ ] [SCRIPT] P0. Add missing data_types to `_CEFI_TRADFI_DEFI_DATA_TYPES` in `orchestration_scanner.py:46–72`
      (`dex_pool_swaps`, `evm_defi_lending`, `evm_defi_amm`, `staking_yields`).
- [ ] [SCRIPT] P0. Fix adapter registry imports — add `liquidity`, `market_state`, `fx_rates` to
      `app/adapters/__init__.py` so decorators fire.
- [ ] [SCRIPT] P0. Wire `expected_root_clusters` + `cluster_extractor` into MDPS chain-bundle write paths
      (futures_chain, options_chain). Use UAC `DATA_TYPE_TO_CLUSTER_REGISTRY` to look up the registry per data_type.
- [ ] [TEST] P0. Per-adapter integration test: simulate path A / path B / path C; assert correct manifest verb fires;
      assert NO 1440-row NaN parquet ever lands on disk.
- [ ] [TEST] P0. End-to-end smoke: pick 1 venue × 1 instrument × 1 day across each asset_group; run MDPS; assert
      manifest reflects honest verb; spot-check 1 parquet per data_type; assert OHLC populated where claimed `captured`.
- [ ] [QG] P0. MDPS quality-gates.sh green.

### Phase 2.B — MTDS partitioner validation + cluster wiring

- [ ] [SCRIPT] P0. Add write-time partition-key validation to `raw_tick_hive.py`: assert
      `tick.timestamp.date() == day_partition_key` before writing each tick. On mismatch: log + emit
      `RAW_TICK_PARTITION_MISMATCH` event + reject the tick (do NOT write to GCS). Per-instrument shard-level isolation;
      one instrument's mismatch doesn't kill the venue run.
- [ ] [SCRIPT] P0. Wire `expected_root_clusters` + `cluster_extractor` into every MTDS bundle adapter: -
      `adapters/tardis/options_chain.py` (lines ~596–702) - `adapters/tardis/futures_chain.py` -
      `adapters/databento/options_chain.py` (lines ~869–985) - `adapters/databento/futures_chain.py` -
      `polymarket_adapter.py` (uses `prediction_canonical_question_group` once that lands — for now, pass an empty
      registry → cluster gate is a no-op, deferred to follow-up plan)
- [ ] [SCRIPT] P0. `umi_tick_provider.py:225` — replace `category="prediction_market"` with `asset_group=...` per
      workspace vocabulary.
- [ ] [SCRIPT] P0. **Sports per-fixture_id shard granularity (in-scope, NOT deferred — confirmed 2026-05-06).**
      `orchestrator.py:1739` currently groups by `(bookmaker, league)` only; expand to full v5/v6 spec
      `(asset_group=sports, source, data_type, league_id, fixture_id|day-aggregate, day)`. Per-fixture data_types
      (`ODDS_SNAPSHOT`, `ODDS_MOVEMENT`, `ARBITRAGE`, `FIXTURE_STATS`, `FIXTURE_EVENTS`, `FIXTURE_LINEUPS`,
      `FIXTURE_PLAYER_STATS`, `INJURIES` when fixture-scoped) shard at fixture_id; aggregate data_types (`STANDINGS`,
      `LEAGUES`, `TEAMS`, etc.) shard at day-aggregate. Reasoning: the entire sports ML stack predicts at fixture-level
      — without per-fixture sharding, can't drill down on missing fixtures or fixture-specific stats. League stays as a
      higher-level rollup grouping for data-status panel filtering, NOT as the shard atom.

      **Break-fix scope (anything that breaks because of this change is fixed in this plan):**
      - **MTDS reader paths** — wherever a reader keys on `(venue, data_type, date)` for sports, expand the lookup to include `fixture_id` (where applicable). Audit + fix in Phase 0.
      - **MDPS sports adapter** — if it consumes MTDS sports parquets keyed by `(bookmaker, league)`, update to read per-fixture parquets and aggregate up if needed.
      - **features-sports input pipeline** — `mtds_canonical_reader` and similar must read per-fixture; verify per-(asset_group, data_type) reader granularity matches the new writer granularity.
      - **deployment-ui data-status panel** — sports panel surfaces league + proficiency rollups (drill-down view), but the underlying shard atom is now per-fixture. UI rolls up per-league for filter view + per-fixture for drill-down. Explicitly: `(league_id) → (fixture_id) → (data_type) → leaf_parquet` drill-down path. Phase 4.B picks this up.
      - **Manifest reconciliation** — existing manifest rows with `(bookmaker, league)` shard keys flip to a new shape; reconciler script in Phase 3.A handles the migration: read old parquet, split per-fixture, write new parquets, mark old `attempted_failed[reason=ShardSchemaMigrated]` for re-attempt under new contract.

- [ ] [SCRIPT] P0. **Sports `BUNDLED_DATA_TYPES` registry seeding** (couples to per-fixture sharding above). Per-fixture
      data_types that aggregate multiple bookmakers/sub-rows in one shard's parquet → `BUNDLED_DATA_TYPES`-eligible.
      Concrete entries: - `ODDS_SNAPSHOT` / `ODDS_MOVEMENT` / `ARBITRAGE` — cluster_extractor: `bookmaker`.
      `SPORTS_FIXTURE_CLUSTERS = {tier_1: {pinnacle, bet365, ...}, tier_2: {...}}` per league-tier (UAC seeds tier-1 EU
      football tier list; expand per follow-up). - `FIXTURE_STATS` / `FIXTURE_PLAYER_STATS` from a single source —
      typically NOT bundled (one row per fixture or per (fixture, player)) unless multi-source merge is enabled
      (deferred to multi-source merge plan). `sports_fixture_bundle` in `BUNDLED_DATA_TYPES` is a logical category; the
      actual `data_type` strings registered are the per-data_type entries above (`ODDS_SNAPSHOT`, etc.). Update Phase 1B
      `BUNDLED_DATA_TYPES` seed to include those concrete data_type names.
- [ ] [SCRIPT] P0. GMX multi-chain — `perp_funding_handler.py:225` currently writes `chain=""`; emit per-chain Tier-2
      fan-out per HANDOVER follow-up note.
- [ ] [SCRIPT] P0. Skip-if-exists granularity — `tick_data_handler.py:166` currently calls `check_shard_freshness` at
      `(venue, data_type, date)`; tighten to full v6 key including `quote_asset` + `margin_type` to avoid DERIBIT
      inverse/linear suppression bug.
- [ ] [SCRIPT] P0. DeFi venue-split rationalisation — `orchestrator.py:1880–1908` hardcoded 27-protocol tuple; replace
      with `_VENUE_MAPPING.all_defi_venues` lookup (single SSOT).
- [ ] [TEST] P0. MTDS unit test: feed a tick with `timestamp.date() != day_key` → assert rejection + event emission.
- [ ] [TEST] P0. MTDS bundle adapter test: feed a partial bundle (8 of 11 ES.OPT clusters) → assert
      `record_failed(ClusterCoverageError)` fires + no parquet written.
- [ ] [QG] P0. MTDS quality-gates.sh green.

### Phase 2.C — features-sports forward fixes

- [ ] [SCRIPT] P0. Delete `_ensure_timestamp` from `cli/handlers/batch_handler.py:146` AND `cli/batch_write.py:38`. No
      shim, no fallback.
- [ ] [SCRIPT] P0. Replace 4 `_ensure_timestamp` callsites in `batch_handler.py:383, 465, 528, 597` (and 1 in
      `batch_write.py:88`) with the appropriate `availability_stamping.stamp_available_at_*` call per
      `UAC.AVAILABILITY_AT_SEMANTICS`.
- [ ] [SCRIPT] P0. For each of the 14 `TABLE_TO_EXPORT` entries in `cli/handlers/batch_handler.py:76–91`, wire
      write-time `available_at` stamping per UAC semantic: - `fixtures` →
      `stamp_available_at_announcement(df, "announced_at")` (column added by Phase 2.D) - `fixture_stats`,
      `fixture_player_stats` → `stamp_available_at_post_match(df, "kickoff_utc", duration_min=120)` - `fixture_events` →
      `stamp_available_at_event_time(df, "event_time")` (column added by Phase 2.D) - `fixture_lineups` →
      `stamp_available_at_kickoff_offset(df, "kickoff_utc", minutes=60)` - `injuries` →
      `stamp_available_at_event_time(df, "report_time")` (column added by Phase 2.D) - 8 reference tables →
      `stamp_available_at_explicit(df, fetch_completed_at)` where `fetch_completed_at` comes from
      `_FETCH_COMPLETED_AT[table_name]` cache populated at fetch time
- [ ] [SCRIPT] P0. Add `_FETCH_COMPLETED_AT: dict[str, datetime]` module-level cache in the export runner (currently
      appears to live in `exports.py` — verify in Phase 0). Populate inside each `export_*` for the 8 reference tables.
      Accessor: `get_fetch_completed_at(table_name) -> datetime`.
- [ ] [TEST] P0. Per-table unit test: build a fixture row → call export → assert `available_at` column present + matches
      semantic + would pass `LookaheadBiasError` for a feature at `kickoff − 24h` window.
- [ ] [TEST] P0. Integration test: run batch over 1 day × 1 league × all 14 tables; assert manifest reflects honest
      verbs; assert `available_at` populated on every parquet; assert no row has `available_at > kickoff_utc + 4h`
      (sanity bound for post-match).
- [ ] [QG] P0. features-sports quality-gates.sh green.

### Phase 2.D — instruments-service sports schema bumps + write-time stamping

- [ ] [SCRIPT] P0. Add column to schemas (in unified_reference_data_interface or wherever the SoT is — verify in Phase
      0): - `FIXTURES_COLUMNS`: `announced_at: timestamp_utc not null` - `FIXTURE_EVENTS_COLUMNS`:
      `event_time: timestamp_utc not null` (verify it's not already there per-event) - `INJURIES_COLUMNS`:
      `report_time: timestamp_utc not null` + `occurrence_time: timestamp_utc nullable` (occurrence_time wins for events
      that happened during a fixture; report_time as fallback when occurrence not known) - `FIXTURE_STATS_COLUMNS`,
      `FIXTURE_PLAYER_STATS_COLUMNS`: `match_end_time: timestamp_utc not null`
- [ ] [SCRIPT] P0. Update each source ingester (api_football, footystats, understat, transfermarkt,
      soccer_football_info, etc.) to populate the new column from the source's native field: - `announced_at`:
      api_football `fixture.date.publish_at` (verify field name) OR fallback `kickoff_utc - 14d` if source doesn't
      expose it - `event_time`: per-event `time.elapsed` + `kickoff_utc` (already convertible) - `report_time`:
      api_football `injury.date` / understat report timestamp / footystats injury date - `occurrence_time`: from
      fixture_events for in-fixture injuries (cross-reference at write time) - `match_end_time`: **detected, not
      defaulted.** Cascade per-fixture (UAC `MATCH_END_TIME_DETECTORS` registry, source-priority ordered): 1.
      `api_football` — `fixture.fixture.timestamp` +
      `status_long ∈ {"Match Finished", "Finished after extra time", "Finished after penalties"}` resolves to actual end
      time. Use if status indicates finished AND timestamp present. 2. `soccer_football_info` (SFI) — re-use the
      halftime-freeze detector (same `≥4-of-6` freeze threshold across
      `shoots_total/shoots_on_target/shoots_off_target/attacks_dangerous_away/dominance_index_home/dominance_index_away`
      per existing `features-sports` halftime algorithm) but applied to the second-half tail to detect full-time.
      Output: timestamp of the longest stable freeze run after minute 80, with min 5-min duration. Treats this as a
      derived feature → also surfaces a `match_end_time_source = "sfi_progressive_freeze"` audit column. 3. `footystats`
      — match end timestamp if present in their match-detail endpoint (verify in Phase 0 audit). 4. `understat` — match
      end timestamp if present (verify in Phase 0 audit). 5. **Last-resort fallback only**: `kickoff_utc + 120min` with
      `match_end_time_confidence = "low_kickoff_plus_default"` audit column. Manifest row gets
      `attempted_failed[reason=MatchEndTimeUndetected]` if NO source provides it AND fallback is used — operator can
      choose to re-attempt later from a freshly-scraped source. - `match_end_time_source` (new audit column on
      FIXTURE_STATS / FIXTURE_PLAYER_STATS): which detector won (`"api_football_native"` / `"sfi_progressive_freeze"` /
      `"footystats_native"` / `"understat_native"` / `"low_kickoff_plus_default"`). Lets data-status panel surface
      low-confidence fixtures.
- [ ] [SCRIPT] P0. instruments-service stale comment fix: `engine/orchestrator.py:4980` "ManifestWriter v5" →
      "ManifestWriter v6".
- [ ] [SCRIPT] P0. Wire `assert_available_at_present` (UTL helper) into `InstrumentsWriteGate._gated_sink_write` so any
      ingester forgetting to stamp `available_at` fails loud.
- [ ] [TEST] P0. Per-source ingester test: feed a sample API response → assert `available_at` column populated correctly
      per UAC semantic.
- [ ] [QG] P0. instruments-service quality-gates.sh green.

QG between Phase 2 and Phase 3: every Phase 2 service has QG green; integration smoke run end-to-end produces honest
manifest verbs across all 4 services for a 1-day × 1-venue test run.

---

## Phase 3 — Retrospective migration (after Phase 2 lands)

The whole point of Phase 3 is: existing on-disk parquets + manifest rows that were written under the old (buggy)
contract get corrected, so the post-merge backfill % means real %. No silent "old data still lies, new data is honest"
split.

### Phase 3.A — Manifest reconciliation scripts

- [ ] [SCRIPT] P0. `mdps_reconcile_1440_nan_placeholders.py` — scan every MDPS-written parquet under
      `gs://{pid}-mdps-*/raw_candle_data/`; for each file, compute `nan_ratio_per_column` for OHLC columns; if all 4 of
      (open, high, low, close) are >95% NaN AND row_count == n_candles → flip manifest row from `captured` to
      `attempted_failed[reason=EmptyPlaceholderBugBackfill]`. Per-VM shard write (manifest concurrency rule).
      Idempotent + dry-run + scoped by `--asset-group` / `--data-type`. Re-attempt happens via existing MDPS backfill
      flow once Phase 2.A lands.
- [ ] [SCRIPT] P0. `mtds_reconcile_partial_bundles.py` — for every `data_type ∈ BUNDLED_DATA_TYPES` with on-disk
      parquets, count clusters per UAC registry; if observed clusters < expected → flip manifest from `captured` to
      `attempted_failed[reason=ClusterCoverageError(historical)]` with the missing cluster set in the error_reason
      payload. Handles options_chain (ES.OPT 11-cluster), futures_chain, sports_fixture_bundle. Per-VM shard write.
- [ ] [SCRIPT] P0. `mtds_reconcile_partition_mismatch.py` — scan a sample of raw_tick parquets; for each instrument's
      parquet under `day=YYYY-MM-DD`, check if any tick's `timestamp.date()` differs from the partition key. Stats-only
      first (count mismatches per venue / data_type / day); flag for human review before flipping any manifest rows
      (this is upstream-bug detection, not data-quality fix).
- [ ] [SCRIPT] P0. `features_sports_reconcile_available_at.py` — for every features-sports parquet on disk, check if
      `available_at` column present + populated correctly per the new UAC semantic. If missing or wrong → flip manifest
      from `captured` to `attempted_failed[reason=MissingAvailableAt]`. Re-attempt happens via Phase 2.C re-run.
- [ ] [SCRIPT] P0. Pre-v5 / pre-v6 manifest row purge — wire
      `instruments-service/scripts/dedupe_manifest_schema_drift.py` + `purge_legacy_unsharded_manifest_rows.py` into the
      orchestrator boot sequence (per parent HANDOVER §"Migration items"). Delete the fallback readers that previously
      handled legacy shapes.
- [ ] [SCRIPT] P0. `category=` → `asset_group=` GCS migration runbook — confirm migration scripts exist for every
      asset_group (cefi/defi/tradfi/sports/prediction); run sequentially per asset_group with a verification step
      (sample list_blobs after each, assert ≥99% canonical hive vocab). Do NOT delete the legacy fallback reader until
      100% migrated AND a hold-period confirms no readers fail.

### Phase 3.B — GCS available_at backfill (sports + others)

- [ ] [SCRIPT] P0. For every sports parquet on disk pre-Phase-2.C, add `available_at` column with the value derived from
      the new UAC semantic + the row's existing columns (kickoff_utc / event_time / report_time / match_end_time /
      fetch_completed_at). One-shot rewrite per file. Manifest update: `available_at_stamped_at = <run_time>` audit
      column.
- [ ] [SCRIPT] P0. Delete legacy `_ensure_timestamp`-stamped `timestamp` columns where they equalled the (now-incorrect)
      midnight UTC fallback. The new `available_at` column replaces them as the SSOT.
- [ ] [SCRIPT] P0. Per-(asset_group, data_type) backfill scope: - **sports** (above) - **CeFi**: confirm raw_tick
      partitions already have implicit per-tick `timestamp` column → derive
      `available_at = timestamp + scrape_latency_estimate` per source priority registry - **DeFi**: similar to CeFi but
      per-block + RPC-latency offset - **TradFi**: similar to CeFi - **Prediction**: deferred until
      canonical_question_group SSOT lands (follow-up plan)

### Phase 3.C — Reconciler observability + halt-on-error

- [ ] [SCRIPT] P0. Every reconciler script wraps work in `unified_trading_library.run_lifecycle.run_lifecycle(...)` (per
      existing run_lifecycle SSOT rollout). Emits `RECONCILER_STARTED` / `RECONCILER_PROGRESS` (per-asset-group with row
      counts) / `RECONCILER_COMPLETED` / `RECONCILER_FAILED`.
- [ ] [SCRIPT] P0. Each reconciler script supports `--max-flips-per-run` halt safety; default 100k. Operator confirms
      first 100k flips look right before lifting the cap.
- [ ] [SCRIPT] P0. Each reconciler emits a CSV/JSON audit report at `gs://{pid}-reconciler-audit/{run_id}/` listing
      every flipped (row_key, old_status, new_status, error_reason).

QG between Phase 3 and Phase 4: every reconciler has run end-to-end on a 1-week sample window; audit reports reviewed by
user; no anomalies.

---

## Phase 4 — Data-status UI + alerts (parallel with Phase 2 after Phase 1 lands)

### Phase 4.A — deployment-api

- [ ] [SCRIPT] P0. New per-pillar write-gate failure breakdown in `data_status_service.py`: - Aggregate
      `attempted_failed` rows by `error_reason` → return per-shard breakdown - New columns: `failed_row_count`,
      `failed_nan_ratio`, `failed_schema`, `failed_cluster`, `failed_timestamp_bias`, `failed_malformed`,
      `failed_empty_placeholder_backfill`
- [ ] [SCRIPT] P0. New endpoint `GET /data-status/{service}/leaf/{shard_key}/schema` — returns per-leaf-parquet schema
      view: columns, types, row_count, per-column non_null_count, per-column NaN ratio, `available_at`
      min/max/null_count.
- [ ] [SCRIPT] P0. Live-vs-historical envelope alert: when historical-mode produces a `data_type` for a date in the live
      window AND `live_pipeline_already_wrote = true` → emit `LIVE_HISTORICAL_DOUBLE_WRITE` warning event.

### Phase 4.B — deployment-ui (unified-trading-system-ui)

- [ ] [SCRIPT] P0. Render new `attempted_failed` reasons distinctly per typed error in the data-status panel: - Distinct
      color + icon per (`EmptyPlaceholderBugBackfill`, `ClusterCoverageError`, `UpstreamTimestampBiasError`,
      `MalformedTickFieldError`, `MissingAvailableAt`, `ClusterCoverageError(historical)`,
      `RAW_TICK_PARTITION_MISMATCH`) - Drill-down per reason → leaf parquet + audit report link
- [ ] [SCRIPT] P0. Surface per-pillar write-gate failure breakdown as a stacked-bar visualisation per shard.
- [ ] [SCRIPT] P0. Schema-view modal (per-leaf parquet) — call new `/leaf/.../schema` endpoint; render columns + types +
      row_count + NaN ratio + `available_at` envelope.
- [ ] [SCRIPT] P0. Live-vs-historical envelope alert badge in the asset-group panel header.

QG between Phase 4 and Phase 5: UI smoke-test (Tier 0 + Tier 1) — every new color/badge/drill-down renders correctly
against seeded fixtures.

---

## Phase 5 — Validation + honest-coverage baseline

- [ ] [SCRIPT] P0. Per-service end-to-end coverage measurement (post-reconcile): - Denominator =
      `expected_dates × expected_instruments × expected_data_types` clipped by `SOURCE_COVERAGE_START` /
      `KNOWN_COVERAGE_GAPS` / `venue_trading_calendar` - Numerator =
      `count(manifest_rows where capture_status == "captured")` - Honest empty =
      `count(capture_status == "empty_confirmed")` (NOT in numerator, but tracked as legitimate absence) - Failed =
      `count(capture_status == "attempted_failed")` per error_reason (NOT in numerator)
- [ ] [SCRIPT] P0. Document the post-merge baseline at
      `unified-trading-pm/codex/02-data/honest_coverage_baseline_2026_05.md`: - Per-(service, asset_group, data_type)
      baseline % - Per-error_reason failure breakdown - Set as the ratchet floor — future merges that drop coverage
      below this % fail QG (per parent plan §"coverage_ratchet_policy")
- [ ] [SCRIPT] P0. LookaheadBiasError end-to-end smoke test: pick 1 strategy / 1 model / 1 fixture; run feature compute
      at `kickoff − 24h`; assert no input row consumed has `available_at > kickoff − 24h`; CI-runnable.
- [ ] [SCRIPT] P0. Write-gate quartet integration test (per asset_group × per bundled data_type matrix): row=0 →
      `record_empty`; partial bundle → `record_failed(ClusterCoverageError)`; high NaN →
      `record_failed(NanRatioExceededError)` (deferred to follow-up plan once that pillar lands); schema mismatch →
      `record_failed(SchemaMismatchError)`. CI-runnable.
- [ ] [QG] P0. Workspace-wide QG on every repo touched (UTL, UAC, MDPS, MTDS, features-sports, instruments-service,
      deployment-api, deployment-ui, unified-trading-pm). Per-repo `quality-gates.sh` green.

QG end-of-plan: user signs off on baseline document; ratchet floor activated.

---

## Coordination with sibling plans

- **`shard_granularity_ssot_propagation_2026_05_06.plan.md` Phase 1 Tier 1 #1 (MDPS 1440-NaN, paused)** — superseded by
  this plan's Phase 2.A. Mark as superseded in companion plan; delete the "AWAITING USER DIRECTION" todo.
- **`shard_granularity_ssot_propagation_2026_05_06.plan.md` Phase 1 Tier 2 raw-tables (sports available_at, paused)** —
  superseded by this plan's Phase 2.C + Phase 2.D. Mark as superseded; delete the "Paused pending user direction on
  hybrid acceptance" todo.
- **HANDOVER §"Item 1 — Cluster-aware bundle validation"** — superseded by this plan's Phase 1A `record_captured`
  mandatory kwarg + Phase 1C CLAUDE.md rule. The "TradFi MVP follow-ups parallel stream" framing is no longer accurate;
  cluster validation is now the mainline contract change, not a parallel stream.
- **`market_tick_data_to_100pct_2026_05_05.plan.md`** — coordination: Phase 2.B partition-key validation + cluster
  wiring overlap with this plan's MTDS scope. Reconcile ownership in Phase 0 before Phase 2.B starts.
- **`data_status_ui_fixes_2026_05_06.plan.md`** + **`data_status_offline_rollup_2026_05_06.plan.md`** — coordination:
  Phase 4 UI work overlaps. Reconcile in Phase 0; either fold into this plan or split cleanly.
- **`manifest_schema_v6_quote_margin_combo_2026_04_23.plan.md`** — Phase 2.A v6 column wiring + Phase 2.B v6 column
  wiring align. Verify v6 schema state matches what this plan assumes.

---

## Tracked open questions (deferred to follow-up plans)

These remain open and will be resolved in subsequent plans the user drafts:

1. **UAC `canonical_question_group` SSOT** for Polymarket / Kalshi predictions — greenfield UAC build. Blocks prediction
   shard-key correctness in instruments-service + MTDS.
2. **`feature_group → required_inputs[]` DAG SSOT in UAC** — currently inlined 3 different ways across features-onchain,
   features-sports, features-delta-one. Drives `LookaheadBiasError` enforcement.
3. **v6 columns `quote_asset` / `margin_type` / `combo_type` / `leg_weights` ownership** — only MTDS writes them;
   instruments-service, MDPS leave at `""`. Confirm MTDS-only or roll out.
4. **NaN-ratio gate lift to UTL** — currently inlined in instruments-service `_validate_predictions_null_rates`
   (FootyStats-only). Lift to UTL `write_gate_helper` with per-feature-group thresholds in UAC.
5. **Phantom-audit drift-probe lift to UTL** — `reconcile_phantom_manifest_rows_all.py` 5-axis logic +
   `ASSET_GROUP_CONFIG` is script-local. Lift to UTL `manifest_audit` so MDPS / MTDS / features-\* can reuse.
6. **Per-VM shard isolation as workspace rule** — `MANIFEST_PER_VM_SHARDS=true` + unique `VM_NAME` pattern from
   `00f6352`/`619a32e` should become every-concurrent-backfill default. Add to base-service.sh QG check.
7. **Multi-source merge spec** — Phase 1B seeds `SOURCE_PRIORITY` top entry only. Full multi-source merge
   (timestamp-availability > coverage > info-richness > merge-different-fields) is a follow-up plan.
8. **Bulk pre-flight tightening in instruments-service** — UTL `check_shard_freshness` line 2259–2267 doesn't include
   `league_id` in match unless explicitly passed; orchestrator line 1224 calls without it. Harsh's commit `7bfa877`
   extended downstream per-league skip; tightening the bulk gate is deferred.
9. ~~**MTDS sports per-fixture_id shard-granularity**~~ — **MOVED IN-SCOPE 2026-05-06.** Now Phase 2.B in this plan.
   Reasoning: ML predictions are fixture-level; without per-fixture sharding, can't drill down on missing fixtures or
   fixture-specific stats. League stays as a higher-level rollup grouping. Anything that breaks (MTDS reader paths, MDPS
   sports adapter, features-sports input pipeline, deployment-ui sports panel) is fixed in this plan. Manifest
   reconciliation handles the shard-shape migration in Phase 3.A.
10. **Polymarket shard-key sequencing** — commits `b336834`/`d7bd17f` fixed crypto-keyword false-positives but the
    shard-key (`data_type=<base_asset>`) still deviates. Risk: re-classifying as classifier matures. Defer to
    canonical_question_group plan.

---

## Estimated timeline

- Phase 0: 2-3 days (audit completion)
- Phase 1A + 1B + 1C: 1 week parallel (UTL + UAC + CLAUDE.md)
- Phase 2: 2 weeks parallel across 4 services
- Phase 3: 1 week (reconcilers + GCS rewrites; compute-heavy)
- Phase 4: 1 week parallel with Phase 2 (UI + alerts)
- Phase 5: 2-3 days (baseline measurement + ratchet activation)

**Total: ~3.5 weeks of focused work + reconciler runtime.**

---

## Success criteria

- ✓ All 6 cross-cutting principles enforced at runtime (UTL guards) AND statically (QG steps).
- ✓ `_create_empty_output` deleted; `_ensure_timestamp` deleted; `_write_manifest_records` v3-shape deleted;
  `check_cluster_coverage` made internal. Single SSOT per concern, no shims.
- ✓ Every shard's parquet on disk has `available_at` column populated correctly per UAC semantic. No row has
  `available_at` derived at read-time.
- ✓ Every bundle data_type's `record_captured` is wired with `expected_root_clusters` + `cluster_extractor`. QG STEP
  5.64 enforces.
- ✓ Forward writes produce honest manifest verbs only (`captured`, `empty_confirmed`,
  `attempted_failed[<typed_reason>]`).
- ✓ Retrospective on-disk corrections: 1440-NaN historical shards flipped + queued for re-attempt; partial bundles
  flipped + queued; pre-v6 rows purged; legacy fallback readers deleted.
- ✓ Data-status UI surfaces per-typed-error breakdown + per-pillar write-gate failure stack + `available_at` envelope
  per leaf parquet.
- ✓ Honest coverage baseline measured per service; ratchet floor activated; future regressions detectable.
- ✓ Workspace-wide QG green on every repo touched.
- ✓ Live = batch verification: any new (asset_group, data_type) shipped after this plan must declare `SOURCE_PRIORITY` +
  `AVAILABILITY_AT_SEMANTICS` entries; QG enforces.
