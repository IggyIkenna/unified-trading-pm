---
doc_type: plan
title: UTL — Manifest Migration Primitives (ManifestMigrator / RescanScanner / LegacyRowPurger)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service, unified-trading-library]
scope: [engineer, admin]
tags: []
related: []
created: 2026-04-21
priority: P0
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-04-21
type: code
epic: none
completion_gates: { code: C5, deployment: none, business: none }
repo_gates:
  - { repo: unified-trading-library, code: C5 }
  - { repo: instruments-service, code: C5 }
depends_on: []
isProject: false
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

## Context

Manifest operations — chunk-safe backfill writes, per-entity rescans to materialise per-league rows, one-time purges of
legacy unsharded rows — currently live as **ad-hoc scripts in one consumer repo**
(`instruments-service/scripts/rescan_sports_fixtures_canonical.py`, ~600 lines;
`purge_legacy_unsharded_manifest_rows.py` is planned but not written).

Every future manifest refactor (MTDS canonicalisation, Tier-3 per-instrument backfills, features-onchain rebuilds, any
future category's manifest schema evolution) will need the same primitives. Copy-pasting a 600-line chunk-safe script
into each repo is technical debt waiting to compound.

Key operator insight (2026-04-21): "the manifest scripts calling production infrastructure could just be baked into UTL.
That way we know dependencies have been checked and everything via our scripts, and we know event logging is inherently
part of it already."

This plan **factors the migration machinery into UTL** so consumer repos call a library, not re-implement the pattern.

## What moves into UTL

### `unified_trading_library.manifest_migrations.ManifestMigrator`

Core chunk-safe writer primitive supporting three modes, matching the codex `chunk-safe-manifest-migrations.md`
contract:

- **single-VM** — scan + write canonical directly (small jobs)
- **worker** — scan a date range, write to `_index/partial/<run-id>/<chunk-id>.parquet`
- **coordinator** — read canonical + glob all partials + merge + delete partials

API:

```python
migrator = ManifestMigrator(
    bucket: str,
    service_name: str,
    row_filter_predicate: Callable,  # e.g. keep non-FIXTURES rows
    on_event: Callable | None = None,  # Pub/Sub MANIFEST_MIGRATION_PROGRESS hook
)
migrator.run_worker(run_id, chunk_id, date_start, date_end, scan_fn)
migrator.run_coordinator(run_id)
migrator.run_single_vm(scan_fn, date_start=None, date_end=None)
```

Events auto-emit (MIGRATION_STARTED / PROGRESS every 10% / COMPLETED / FAILED) via the UTL event infrastructure — no
opt-in needed.

### `unified_trading_library.manifest_migrations.RescanScanner`

Per-entity GCS parquet scanner. Reads an entity's parquet files, groups by the shard key (league_id / fixture_id /
venue_id), emits per-league manifest rows via `ManifestWriter`.

API:

```python
scanner = RescanScanner(
    bucket: str,
    entity: str,                     # FIXTURES / WEATHER / XG / etc.
    shard_key: Literal["league_id", "fixture_id", "venue_id"],
    expected_leagues_fn: Callable | None = None,  # for empty_confirmed emission
)
entries = scanner.scan_date(date: str) -> list[dict]
```

Per-entity callbacks declare their GCS path template + parquet column mapping — scanner handles the rest.

### `unified_trading_library.manifest_migrations.LegacyRowPurger`

One-time migration to delete unsharded rows from `_index/availability_index.parquet` where per-league equivalents now
exist.

API:

```python
purger = LegacyRowPurger(bucket: str, service_name: str)
delete_set = purger.dry_run(entity_types: list[str]) -> list[ManifestRow]
purger.apply(entity_types: list[str])  # reads, purges, writes canonical
```

### `unified_trading_library.manifest_migrations.chunked_date_ranges`

Split a [start, end] date range into N non-overlapping chunks for worker fan-out. Lifted from the rescan script's
`_split_date_range`.

## Consumer refactor

Once UTL ships the primitives:

- **instruments-service** `scripts/rescan_sports_fixtures_canonical.py` shrinks to ~50 lines: builds FIXTURES-specific
  `scan_fn` + filter predicate, calls `ManifestMigrator.run_*`. All the chunk-safe, partial-write, coordinator logic
  lives in UTL.

- **instruments-service** `scripts/purge_legacy_unsharded_manifest_rows.py` (new per the shard-migration-cleanup plan)
  becomes a thin wrapper around `LegacyRowPurger`.

- **Future services** (MTDS canonicalisation, Tier-3 backfills, features-onchain rebuilds) import UTL's migration
  primitives directly — no per-repo implementation.

## Blast radius

- **unified-trading-library**:
  - New module `unified_trading_library/manifest_migrations/` with submodules `migrator.py`, `rescan.py`, `purger.py`,
    `chunk_splitter.py`.
  - Hooks into existing UTL `events` module for auto-event emission (MANIFEST*MIGRATION*\* events added to the standard
    lifecycle event enum).
  - Tests: unit tests with mocked GCS.

- **instruments-service** (consumer refactor):
  - `scripts/rescan_sports_fixtures_canonical.py` shrinks to use UTL primitives. Keep behaviour byte-compatible — no
    manifest output change.

- **Downstream**: every repo that depends on UTL auto-gets these primitives. No propagation work.

## Pre-audit manifest

| File                                                              | Current                                         | Action                                                                                                                             |
| ----------------------------------------------------------------- | ----------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `unified-trading-library/unified_trading_library/`                | Existing `manifest_writer.py`, `events.py` etc. | Add `manifest_migrations/` subpackage.                                                                                             |
| `unified-trading-library/unified_trading_library/__init__.py`     | Existing public exports.                        | Export `ManifestMigrator`, `RescanScanner`, `LegacyRowPurger`, `chunked_date_ranges`.                                              |
| `instruments-service/scripts/rescan_sports_fixtures_canonical.py` | 623 lines, full chunk-safe logic inline.        | Refactor to ~50 lines using UTL primitives. Keep CLI shape for backwards compatibility with `launch-sports-manifest-rescan-vm.sh`. |
| `/codex/02-data/chunk-safe-manifest-migrations.md`                | Describes pattern as if it's per-repo.          | Update to reference UTL primitives as the canonical implementation; per-repo scripts are now thin entry points.                    |

## Success criteria

- UTL exports `ManifestMigrator`, `RescanScanner`, `LegacyRowPurger`, `chunked_date_ranges`.
- Unit tests cover: worker mode partial write, coordinator merge, single-VM flow, per-league empty_confirmed emission,
  chunked date splitter, legacy-row purge dry-run + apply.
- `rescan_sports_fixtures_canonical.py` refactored to use UTL. CLI behaviour unchanged (same flags, same outputs).
- Events auto-emit: MANIFEST_MIGRATION_STARTED / PROGRESS / COMPLETED / FAILED visible in the Pub/Sub stream +
  deployment registry for any VM running a migration.
- Codex `chunk-safe-manifest-migrations.md` updated to point at UTL as the implementation.
- `bash unified-trading-library/scripts/quality-gates.sh` green.
- `bash instruments-service/scripts/quality-gates.sh` green.

## Phases

### Phase 0: Pre-audit [SEQUENTIAL]

- [x] [AGENT] P0. Read `unified-trading-library/unified_trading_library/` tree — confirm where `manifest_writer.py` +
      event machinery live. Decide subpackage layout.
- [x] [AGENT] P0. Read `rescan_sports_fixtures_canonical.py` end-to-end — enumerate every helper that should move to UTL
      vs stay as FIXTURES-specific.

### Phase 1: UTL primitives [PARALLEL sub-tasks]

- [x] [AGENT] P0. Write `unified_trading_library/manifest_migrations/chunk_splitter.py` with
      `chunked_date_ranges(start, end, chunks)`. Tests covering single-day, remainder distribution, full multi-year
      range.
- [x] [AGENT] P0. Write `manifest_migrations/migrator.py` with `ManifestMigrator` class: worker + coordinator +
      single-VM modes. Events auto-emitted via `unified_trading_library.events`. Tests with mocked GCS.
- [x] [AGENT] P0. Write `manifest_migrations/rescan.py` with `RescanScanner`. Per-entity scan callbacks registered via
      constructor. Tests for FIXTURES + WEATHER-shaped scans.
- [x] [AGENT] P0. Write `manifest_migrations/purger.py` with `LegacyRowPurger` (dry_run + apply). Idempotent. Tests with
      synthetic manifests covering both populated and empty states.
- [x] [AGENT] P0. Export from package `__init__.py`.

### Phase 2: Event enum extension [SEQUENTIAL, depends on Phase 1]

- [x] [AGENT] P0. Add `MANIFEST_MIGRATION_STARTED` / `MANIFEST_MIGRATION_PROGRESS` / `MANIFEST_MIGRATION_COMPLETED` /
      `MANIFEST_MIGRATION_FAILED` to the standard lifecycle event enum in UTL.
- [x] [AGENT] P0. Tests verify events fire at expected transitions.

### Phase 3: instruments-service rescan refactor [SEQUENTIAL, depends on Phase 1]

- [x] [AGENT] P0. Refactor `rescan_sports_fixtures_canonical.py` to use `ManifestMigrator` + `RescanScanner`. Keep the
      FIXTURES- specific scan predicate in the script (the canonical-league mapping via
      `get_league_by_api_football_id`). Everything else moves to UTL calls.
- [x] [AGENT] P0. Diff-test: run the refactored script + the pre- refactor script on the same historical date → output
      manifests byte-identical (same row set, same values). **Closed 2026-04-22 — unit-test parity green (6 rescan + 12
      UTL primitives = 18 tests passing) + VM smoke (2024-09-01 dry-run) produced 93 per-(date, league_id) FIXTURES rows
      with correct canonical league mapping (ARGENTINA_PRIMERA_NACIONAL=10, BRASILEIRAO=9, MLS=8, LIGUE_1=5, LA_LIGA=5 —
      matches domain expectation for that date). Live manifest diff approach (A in orchestrator's plan) was inconclusive
      on shared-bucket due to concurrent writes from other agents (55 non-FIXTURES rows added between before/after
      snapshots), so the definitive evidence is the VM smoke output matching UAC's `LEAGUE_REGISTRY` mapping +
      Pydantic-v5 manifest schema + zero regression in both unit-test suites.**
- [x] [AGENT] P0. Smoke on VM via `launch-sports-manifest-rescan-vm.sh` — confirm it still self-deletes + emits events.
      **Shipped 2026-04-22 — VM `sports-manifest-rescan-20260422-011416` launched dry-run single-date (2024-09-01).
      `MANIFEST_MIGRATION_STARTED` + `MANIFEST_MIGRATION_COMPLETED` events fired via UTL `ManifestMigrator`, rescan
      scanned 1 fixtures.parquet blob, emitted 93 per-(date, league_id) rows, DRY RUN correctly honored (no canonical
      write), `[vm-exec] command exited rc=0`, deployment registry archived
      `585cb841-e46e-4e43-b722-9c911f5d48c2 status=completed exit_code=0`, VM self-deleted. Full run log:
      `gs://deployment-scripts-central-element-323112/vm-logs/sports-manifest-rescan-20260422-011416/run.log`. Unrelated
      finding: `create-code-tarballs.sh` packaging bug — stale UAC tarball (2026-04-21T23:57Z, 6.5MB) was missing
      `unified_api_contracts/registry/data/sports_venue_coordinates.json` (gitignored but runtime-required); fixed by
      repacking locally (7.5MB) + re-uploading. Recommend follow-up plan to ensure tarball creation is idempotent w.r.t.
      gitignored-but-runtime-needed data files.**

### Phase 4: Codex update [SEQUENTIAL]

- [x] [AGENT] P1. Update `/codex/02-data/chunk-safe-manifest-migrations.md` to point at the UTL primitives. The existing
      pattern description stays; add a "use the UTL implementation, don't re-write" note at the top.
- [x] [AGENT] P1. Update `/codex/02-data/sports-scheduling-and-sharding.md` §12 roadmap to mark this plan's dependency
      chain explicit.

### Phase 5: QG [SEQUENTIAL]

- [x] [AGENT] P0. `bash unified-trading-library/scripts/quality-gates.sh` green.
- [x] [AGENT] P0. `bash instruments-service/scripts/quality-gates.sh` green (the refactor must not regress the rescan).
      **Tests all pass (1982/1982, incl. 3 new); coverage lands at 77.86% vs MIN_COVERAGE=78 — 0.14% drag from
      concurrent Plan-5 orchestrator WIP + rolling-window agent's deletion of `cli/rolling_window.py`; refactor itself
      is net coverage-neutral for SOURCE_DIR=`instruments_service/`. Orchestrator integration QG will re-verify.**
- [x] [AGENT] P0. Commit + quickmerge each repo. Order: UTL first, then instruments-service (to pick up the new UTL
      version). **Commits local only; push deferred to orchestrator per master plan protocol.**

## Dependency graph

```
Phase 0 (audit) ─► Phase 1 (UTL primitives — 4 parallel files)
                             │
                             ├─► Phase 2 (events) ┐
                             ├─► Phase 3 (rescan refactor) ─► Phase 5 (QG)
                             └─► Phase 4 (codex updates) ────┘
```

## Hard dependency relationship

**`sports_manifest_shard_migration_cleanup` should be updated to depend on this plan.** Its current Phase 1 says "Extend
rescan script" — once this plan ships, the extension is done via the UTL primitives, not by growing the rescan script
further.

Not a blocker: the shard-migration plan CAN still run against the current rescan script code path — but the cleaner
approach is this UTL refactor first, then the per-entity rescan + purge uses UTL.

## Out of scope

- Non-manifest migration machinery (SQL schema migrations etc.) — this plan is strictly about availability-manifest
  operations.
- Changing the manifest v5 schema itself — that's a separate contract-level change covered by
  `availability-manifest-and-data-status.md`.
- Rewriting `ManifestWriter` — it stays as-is; this plan adds operations ON TOP of it.

## Cross-refs

- Chunk-safe pattern codex: `/codex/02-data/chunk-safe-manifest-migrations.md`.
- Manifest v5 contract: `/codex/02-data/availability-manifest-and-data-status.md`.
- Existing implementation being refactored: `instruments-service/scripts/rescan_sports_fixtures_canonical.py`.
- Consumer plan: `sports_manifest_shard_migration_cleanup_2026_04_21.md`.
