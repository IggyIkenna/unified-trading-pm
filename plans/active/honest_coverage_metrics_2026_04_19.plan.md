---
name: honest-coverage-metrics
overview: Attempt-vs-capture manifest semantics — stop conflating "never attempted" with "attempted, confirmed empty".
type: mixed
epic: epic-code-completion
status: active

locked_by: live-defi-rollout
locked_since: 2026-04-19

completion_gates:
  code: C5
  deployment: D2
  business: none

repo_gates:
  - repo: unified-trading-library
    code: C5
    deployment: none
    business: none
  - repo: instruments-service
    code: C0
    deployment: none
    business: none
  - repo: market-tick-data-service
    code: C0
    deployment: none
    business: none
  - repo: features-sports-service
    code: C0
    deployment: none
    business: none
  - repo: deployment-api
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-system-ui
    code: C0
    deployment: none
    business: none

depends_on: []

todos:
  # ─── Phase A — UTL schema (this session) ──────────────────────────────
  - id: phase-a-schema
    content: |
      - [x] [AGENT] P0. UTL ManifestWriter schema — add capture_status, error_reason,
        attempted_at columns to AvailabilityRecord. Default capture_status="captured",
        error_reason=None, attempted_at=now(UTC) on ManifestWriter.add. Backfill path
        coerces legacy rows (NULL capture_status) to "captured" + attempted_at=None.
        Bump MANIFEST_SCHEMA_VERSION 4 → 5.
    status: done
    note: "Real code landed on live-defi-rollout."

  - id: phase-a-methods
    content: |
      - [x] [AGENT] P0. UTL ManifestWriter.record_empty(row_key, attempted_at) and
        record_failed(row_key, error, attempted_at). Write one AvailabilityRecord per
        call with row_count=0, capture_status="empty_confirmed" / "attempted_failed".
        Also add lookup(row_key) returning ManifestRow | None — Phase B adapters use it
        for skip-if-attempted decisions.
    status: done

  - id: phase-a-reexport
    content: |
      - [x] [AGENT] P0. Re-export record_empty, record_failed, lookup, ManifestRow, and
        CaptureStatus from unified_trading_library.__init__ so downstream repos can
        import them without reaching into manifest_writer.
    status: done

  - id: phase-a-tests
    content: |
      - [x] [AGENT] P0. Unit tests in tests/unit/test_manifest_writer_capture_status.py
        covering: (1) round-trip for each of the 3 statuses, (2) legacy parquet (no
        capture_status column) reads with defaults, (3) record_empty / record_failed
        idempotent per row_key, (4) lookup returns None on unknown and correct row on
        known, (5) backward-compat merge — legacy rows preserved with status="captured".
    status: done

  - id: phase-a-qg
    content: |
      - [x] [AGENT] P0. UTL quality-gates.sh Pass 1 green; quickmerge --agent to push
        to live-defi-rollout. Re-run deployment-service/scripts/vm/create-code-tarballs.sh
        so future VMs inherit the schema (no current VMs need rebuild — backward-compat
        read preserves them).
    status: done

  - id: phase-a-plan-doc
    content: |
      - [x] [AGENT] P0. Plan doc with pre-audit table + phased DAG + semantic decisions.
    status: done

  # ─── Phase B — adapter integration (next session) ─────────────────────
  - id: phase-b-polymarket
    content: |
      - [ ] [AGENT] P0. Polymarket adapter (instruments-service/scripts/full_polymarket_dump.py +
        instruments_service/engine/orchestrator.py PREDICTION paths) — call record_empty on
        0-row group, record_failed on gamma API exception. Pre-flight lookup(row_key) skips
        already-attempted shards unless --force.
    status: todo

  - id: phase-b-tardis
    content: |
      - [ ] [AGENT] P0. Tardis / MTDS tick adapters (market-tick-data-service) — same
        pattern for CeFi venues. Applies where ingester is purely tick-driven and zero
        rows on a day is a real signal (e.g. Tardis free tier on a non-trading day).
    status: todo

  - id: phase-b-kalshi
    content: |
      - [ ] [AGENT] P0. Kalshi adapter (instruments-service sports/prediction paths) —
        event-driven markets, sparse days. record_empty on confirmed 0-event day,
        record_failed on API exception.
    status: todo

  - id: phase-b-sfi
    content: |
      - [ ] [AGENT] P0. SFI fixture-stats / odds / lineups (instruments-service sports
        paths + features-sports-service batch_handler) — no fixtures on a given day is
        the common case, not an error. record_empty on confirmed empty, record_failed
        on exception.
    status: todo

  - id: phase-b-qg
    content: |
      - [ ] [AGENT] P0. QG green on all 4 downstream repos; re-run one backfill cycle
        per category and verify the manifest now has empty_confirmed rows where
        previously there was silence.
    status: todo

  # ─── Phase C — deployment-api + UI ────────────────────────────────────
  - id: phase-c-api
    content: |
      - [x] [AGENT] P1. deployment-api exposes attempt_coverage_pct, capture_coverage_pct,
        empty_rate, failure_rate per shard dimension. Derives from manifest capture_status
        counts; preserves existing availability_pct for backward compat. Shipped in
        deployment-api@6d6515e. Per-venue capture_status_counts + top-level
        failure_rate_by_dimension added; /instruments-for-shard surfaces
        capture_status/error_reason/attempted_at per row with legacy-fallback coerce.
    status: done

  - id: phase-c-ui
    content: |
      - [x] [AGENT] P1. deployment-ui data-status page renders 4-state heatmap
        (captured / empty_confirmed / attempted_failed / missing) with distinct colour
        + hatch. "Show only failures" filter toggle persisted in localStorage.
        Drill-down per-row CaptureStatusBadge + RetryShardButton wired to
        /deployments/deploy-missing with force=true. Shipped in deployment-ui@c3b57d3.
    status: done

  - id: phase-c-qg
    content: |
      - [x] [AGENT] P1. API + UI QG Pass 1 green on changed modules (deployment-api
        codex at tolerance; deployment-ui has 18 pre-existing hooks errors unrelated
        to this plan — confirmed against stash baseline). 17 new pytest + 5 new vitest
        tests covering capture_status counts, drill-down surfacing, 4-state heatmap,
        aria-label error bleed-through.
    status: done

isProject: true
---

## Context + Motivation

`ManifestWriter` today only writes a row when `row_count > 0`. The absence of a row is ambiguous: it can mean "we never
tried" **or** "we tried and there was legitimately nothing to capture". For CeFi/DeFi/TradFi reference data this
ambiguity is mostly benign (those categories ingest densely, so missing rows really are missing work). For
**event-driven** categories it is actively misleading:

- Polymarket PREDICTION shows 23 % capture today. The actual attempt rate is ~99 % — we queried gamma for nearly every
  (day × conditionId) pair but most pairs traded zero times that day, so nothing was written.
- SFI fixture feeds have dozens of league×day cells per season that genuinely have no fixtures. The manifest cannot
  distinguish those from cells we forgot to ingest.
- Kalshi, weather, odds-API feeds all share this shape.

The platform already has the plumbing to report "honest coverage" (two bars: attempted and captured) — the missing piece
is the manifest row that records the attempt even when it produced zero data. This plan lands that plumbing in three
phases:

| Phase | Scope                                                            | Session          |
| ----- | ---------------------------------------------------------------- | ---------------- |
| A     | UTL schema + `record_empty` / `record_failed` / `lookup` methods | **This session** |
| B     | Adapter integration (Tardis, Polymarket, Kalshi, SFI)            | Next 1-2         |
| C     | deployment-api exposes the split; UI renders two-bar row         | Session after    |

## Phased DAG

```
Phase A (UTL schema)
       │
       │  quality-gates.sh pass + UTL re-tarballed
       ▼
Phase B (adapter integration — PARALLEL per repo)
  ├── instruments-service (Polymarket, Kalshi, SFI)
  ├── market-tick-data-service (Tardis)
  └── features-sports-service (fixture-dependent feeds)
       │
       │  QG per repo + one real backfill cycle per category
       ▼
Phase C (deployment-api + UI — SEQUENTIAL)
  ├── deployment-api surface
  └── deployment-ui two-bar row
       │
       │  Mock-mode smoke + visual parity
       ▼
      Done
```

Parallelization: Phase B repos are independent — one sub-agent per repo. Phase C is sequential because the UI reads the
API schema.

## Pre-Audit — Blast-Radius Manifest (ManifestWriter consumers)

Generated via
`grep -rn "ManifestWriter\|manifest_writer\|write_with_zero_fill\|record_empty\|record_failed" --include="*.py" --exclude-dir=".venv*" --exclude-dir="__pycache__"`
across the full workspace on 2026-04-19. Tests and the owning file
(`unified-trading-library/unified_trading_library/manifest_writer.py`) are excluded from the "callers" table below; they
appear in the "Tests" section.

| #   | Repo                              | File                                                             | Line                                                                                                                        | Pattern               | Phase-B action                                                                                                                                    |
| --- | --------------------------------- | ---------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | alerting-service                  | alerting_service/persistence/storage_store.py                    | 98                                                                                                                          | `ManifestWriter(...)` | Safe to defer — dense writes                                                                                                                      |
| 2   | deployment-service                | deployment_service/cli/utils/manifest_reader.py                  | —                                                                                                                           | reader only           | Reads new columns (Phase C consumer)                                                                                                              |
| 3   | deployment-service                | scripts/rebuild_sports_manifest.py                               | 202                                                                                                                         | `ManifestWriter(...)` | Safe to defer — rebuild tool                                                                                                                      |
| 4   | e2e-testing                       | scripts/defi/data_layer_runner.py                                | —                                                                                                                           | direct use            | Safe to defer — test harness                                                                                                                      |
| 5   | execution-service                 | execution_service/engine/modes/live/data_sink.py                 | 109                                                                                                                         | `ManifestWriter(...)` | Safe to defer — live writes dense                                                                                                                 |
| 6   | execution-service                 | execution_service/results/save_operations.py                     | 784                                                                                                                         | `ManifestWriter(...)` | Safe to defer — per-run artefacts                                                                                                                 |
| 7   | features-calendar-service         | features_calendar_service/engine/calendar_orchestrator.py        | 252                                                                                                                         | `ManifestWriter(...)` | **Phase B candidate** (calendar-driven)                                                                                                           |
| 8   | features-commodity-service        | features_commodity_service/cli/handlers/batch_handler.py         | 212                                                                                                                         | `ManifestWriter(...)` | Safe to defer — dense                                                                                                                             |
| 9   | features-cross-instrument-service | features_cross_instrument_service/cli/handlers/batch_handler.py  | 327                                                                                                                         | `ManifestWriter(...)` | Safe to defer — dense                                                                                                                             |
| 10  | features-delta-one-service        | features_delta_one_service/engine/orchestrator.py                | 238                                                                                                                         | `ManifestWriter(...)` | Safe to defer — dense                                                                                                                             |
| 11  | features-multi-timeframe-service  | features_multi_timeframe_service/engine/orchestrator.py          | 242                                                                                                                         | `ManifestWriter(...)` | Safe to defer — dense                                                                                                                             |
| 12  | features-onchain-service          | features_onchain_service/engine/orchestrator.py                  | 148                                                                                                                         | `ManifestWriter(...)` | Safe to defer — dense                                                                                                                             |
| 13  | features-sports-service           | features_sports_service/cli/handlers/batch_handler.py            | 326                                                                                                                         | `ManifestWriter(...)` | **Phase B: needs record_empty**                                                                                                                   |
| 14  | features-volatility-service       | features_volatility_service/engine/orchestrator.py               | 192, 264, 647                                                                                                               | `ManifestWriter(...)` | Safe to defer — dense                                                                                                                             |
| 15  | instruments-service               | instruments_service/cli/instruments_handler.py                   | 166                                                                                                                         | `ManifestWriter(...)` | Safe to defer — runs everything                                                                                                                   |
| 16  | instruments-service               | instruments_service/engine/orchestrator.py                       | 982, 1168, 1255, 1287, 1342, 1469, 1569, 1683, 2054, 3173, 3383, 3436, 3520, 3588, 3661, 3711, 3839, 4009, 4235, 4308, 4454 | `ManifestWriter(...)` | **Phase B:** sports_manifest / pred_manifest / odds_manifest / xg_manifest / \_ft_manifest need record_empty. CeFi/DeFi paths stay as-is (dense). |
| 17  | instruments-service               | scripts/full_polymarket_dump.py                                  | 175                                                                                                                         | `ManifestWriter(...)` | **Phase B: needs record_empty**                                                                                                                   |
| 18  | instruments-service               | scripts/patch_prediction_shards.py                               | 72                                                                                                                          | `ManifestWriter(...)` | **Phase B: needs record_empty**                                                                                                                   |
| 19  | instruments-service               | scripts/rescan_prediction_v4.py                                  | 112                                                                                                                         | `ManifestWriter(...)` | **Phase B: needs record_empty**                                                                                                                   |
| 20  | instruments-service               | scripts/rescan_sports_manifest.py                                | —                                                                                                                           | direct path use       | Safe to defer — rebuild tool                                                                                                                      |
| 21  | instruments-service               | scripts/fix_manifest_venue_casing.py                             | 69                                                                                                                          | parquet-rewrite       | Safe to defer — cleanup tool                                                                                                                      |
| 22  | market-data-processing-service    | market_data_processing_service/app/core/canonical_writer.py      | 309                                                                                                                         | `ManifestWriter(...)` | Safe to defer — dense                                                                                                                             |
| 23  | market-data-processing-service    | market_data_processing_service/app/core/orchestration_service.py | 325                                                                                                                         | `ManifestWriter(...)` | Safe to defer — dense                                                                                                                             |
| 24  | market-data-processing-service    | market_data_processing_service/app/core/candle_write_mixin.py    | —                                                                                                                           | reader                | —                                                                                                                                                 |
| 25  | market-data-processing-service    | market_data_processing_service/io/writer.py                      | —                                                                                                                           | reader                | —                                                                                                                                                 |
| 26  | market-data-processing-service    | scripts/reprocess_sports_odds.py                                 | 239                                                                                                                         | `ManifestWriter(...)` | **Phase B: needs record_empty**                                                                                                                   |
| 27  | market-tick-data-service          | market_tick_data_service/engine/orchestrator.py                  | 1083                                                                                                                        | `ManifestWriter(...)` | **Phase B: needs record_empty** (Tardis + prediction paths)                                                                                       |
| 28  | market-tick-data-service          | market_tick_data_service/cli/handlers/data_manifest_handler.py   | —                                                                                                                           | reader                | Phase C consumer                                                                                                                                  |
| 29  | market-tick-data-service          | market_tick_data_service/scripts/rebuild_prediction_manifest.py  | 268                                                                                                                         | `ManifestWriter(...)` | **Phase B: needs record_empty**                                                                                                                   |
| 30  | market-tick-data-service          | scripts/rebuild_mtds_manifest.py                                 | 162                                                                                                                         | `ManifestWriter(...)` | Safe to defer — rebuild tool                                                                                                                      |
| 31  | market-tick-data-service          | scripts/migrate_tradfi_to_hive.py                                | —                                                                                                                           | direct use            | Safe to defer — migration                                                                                                                         |
| 32  | ml-inference-service              | ml_inference_service/app/core/prediction_publisher.py            | 115, 211                                                                                                                    | `ManifestWriter(...)` | Safe to defer — dense                                                                                                                             |
| 33  | ml-training-service               | ml_training_service/ml/model_registry.py                         | 293                                                                                                                         | `ManifestWriter(...)` | Safe to defer — dense                                                                                                                             |
| 34  | pnl-attribution-service           | pnl_attribution_service/cli/handlers/compute_handler.py          | 237                                                                                                                         | `ManifestWriter(...)` | Safe to defer — dense                                                                                                                             |
| 35  | risk-and-exposure-service         | risk_and_exposure_service/core/risk_snapshot_sink.py             | 116                                                                                                                         | `ManifestWriter(...)` | Safe to defer — dense                                                                                                                             |
| 36  | strategy-service                  | strategy_service/engine/core/cloud_strategy_storage.py           | 186, 264, 342                                                                                                               | `ManifestWriter(...)` | Safe to defer — dense                                                                                                                             |
| 37  | unified-trading-library           | unified_trading_library/**init**.py                              | 704-717                                                                                                                     | re-export block       | **Phase A: add new symbols**                                                                                                                      |
| 38  | unified-trading-library           | unified_trading_library/dependency_check.py                      | —                                                                                                                           | symbol check          | Safe — no schema touch                                                                                                                            |

### Tests (legacy — must keep passing, backward-compat verified)

| Repo                     | Test file                                                                            |
| ------------------------ | ------------------------------------------------------------------------------------ |
| unified-trading-library  | tests/unit/test_manifest_v4_migration.py                                             |
| unified-trading-library  | tests/unit/test_manifest_writer_league.py                                            |
| unified-trading-library  | tests/unit/test_manifest_writer_zero_fill.py                                         |
| unified-trading-library  | tests/unit/test_g9_regression_canonicalisation.py                                    |
| instruments-service      | tests/integration/test_library_deps_integration.py                                   |
| instruments-service      | tests/unit/{test_handler_and_reloaders, test_league_partitioning, ...}.py            |
| market-tick-data-service | tests/integration/test_library_contracts.py + tests/unit/test_league_partitioning.py |
| features-onchain-service | tests/unit/test_onchain_calculators.py                                               |
| ml-training-service      | tests/smoke/test_strict_writer_enforcement.py                                        |

"Safe to defer" means the producer writes dense rows on every run (CeFi tick data, feature computations, live execution
artefacts, per-run risk snapshots), so absence of a manifest row really does mean the producer never ran. `record_empty`
is not needed — the existing SHARD_INCOMPLETE event already covers ingestion failure for those paths. Phase B can still
retrofit them later once honest-coverage is universal, but attempt-vs-capture metrics give no new signal for them.

## Semantic Decisions

1. **No retroactive sentinel fill.** An earlier draft of this plan suggested back-writing `empty_confirmed` rows for
   existing Polymarket (day × conditionId) pairs that the migration never actually queried. This was **wrong** — it
   would fabricate attempt history. The only legitimate way to populate `empty_confirmed` for the existing Polymarket
   migration output is to **re-run the migration after Phase B lands**. That rerun will naturally write sentinels for
   every pair it queries. The same rule applies to Tardis / Kalshi / SFI: no back-fill, only forward-fill from the next
   real run.

2. **Coverage definition (two metrics, not one).**
   - `attempt_coverage_pct = rows_where_capture_status_in_{captured,empty_confirmed,attempted_failed} / total_expected_cells`
   - `capture_coverage_pct = rows_where_capture_status == "captured" / total_expected_cells`
   - Derived: `empty_rate = empty_confirmed / attempted_total`, `failure_rate = attempted_failed / attempted_total`.
   - Existing `availability_pct` (bare presence of a row) remains for backward compat — it will equal
     `attempt_coverage_pct` once Phase B is universal.

3. **Backward-compat read path.** Legacy parquet rows (no `capture_status` column) are coerced to
   `capture_status="captured"`, `error_reason=None`, `attempted_at=None` during read. This means live VMs on old library
   versions keep working; any new row they write has the default `"captured"` status. `MANIFEST_SCHEMA_VERSION` bumps 4
   → 5 so downstream freshness checks can see the schema change.

4. **`--force` interaction with capture_status.** `lookup(row_key)` returns the row with capture_status. Adapter
   pre-flight:
   - `captured` → skip unless `--force` (existing behaviour, preserved).
   - `empty_confirmed` → skip unless `--force` (new behaviour — we trust the prior empty confirmation).
   - `attempted_failed` → **retry by default** (error_reason tells us why it failed last time; operator can inspect and
     decide if `--skip-failed` is appropriate, but default is to retry).
   - no row → attempt.

5. **`attempted_at` vs `written_at`.** `written_at` stays as the wall-clock stamp of when the manifest row was written.
   `attempted_at` is the wall-clock stamp of when the adapter _started_ the attempt. For `captured` rows they are nearly
   equal; for `empty_confirmed` / `attempted_failed` rows they can differ by seconds (the time it took to confirm the
   empty / fail) but the distinction matters in adversarial post-mortem — e.g. "the attempt was at T0 but the manifest
   only recorded it at T0+45min, so we lost the attempt-history guarantee during the outage".

6. **Idempotency per row_key.** `record_empty(row_key=X)` called twice with the same `row_key` writes two parquet rows;
   the `_merge_dataframes` dedup by the existing key columns collapses them to last-write-wins. This matches the
   existing `.add()` idempotency semantics.

## Success Criteria

### Phase A (this session)

- [x] UTL quality-gates.sh Pass 1 green (ruff, basedpyright, tests).
- [x] New unit tests pass in isolation (`pytest tests/unit/test_manifest_writer_capture_status.py`).
- [x] Existing manifest tests still pass (no regression on `test_manifest_v4_migration.py`,
      `test_manifest_writer_league.py`, `test_manifest_writer_zero_fill.py`).
- [x] Legacy parquet (written by pre-Phase-A library) reads cleanly via `read_availability_index` and returns
      `capture_status="captured"` for every row.
- [x] Re-tar UTL so future VMs inherit the schema.

### Phase B (next 1-2 sessions)

- [ ] Each repo quality-gates.sh Pass 1 green.
- [ ] One real backfill cycle per event-driven category written, and subsequent `read_availability_index` shows
      `empty_confirmed` rows for confirmed-empty cells.
- [ ] PREDICTION attempt_coverage_pct rises from today's 23 % to ~99 % after Polymarket re-runs; SFI / Kalshi / weather
      paths show analogous lifts.

### Phase C (final session)

- [ ] deployment-api exposes the new fields in the `/data-status` response.
- [ ] deployment-ui data-status page renders two-bar rows per shard.
- [ ] Mock-mode smoke shows both bars for PREDICTION + SPORTS; visual parity check signed off.

## Non-Goals

- **No retroactive back-fill of `empty_confirmed` sentinels.** We explicitly refuse to write attempt history that did
  not happen.
- **No coverage-model change for CeFi / DeFi / TradFi tick data.** Those categories capture densely — a missing row
  really is a missing-work signal, and `SHARD_INCOMPLETE` already reports it. Phase B only touches event-driven adapters
  where absence-vs-empty is ambiguous.
- **No schema migration of legacy parquet files on GCS.** The backward-compat read path handles them forever. We never
  rewrite old data unless a live backfill naturally touches it.
- **No UI changes in Phase A or B.** The two-bar row is strictly Phase C.

## SSOT References

- UTL ManifestWriter: `unified-trading-library/unified_trading_library/manifest_writer.py`
- Availability manifest v4 codex: `unified-trading-pm/codex/02-data/availability-manifest-and-data-status.md`
- Coverage ratchet policy: `unified-trading-pm/plans/active/coverage_ratchet_policy_2026_04_19.plan.md`
- Shard-level failure isolation: `unified-trading-pm/codex/04-architecture/shard-level-failure-isolation.md`
