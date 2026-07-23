---
doc_type: codex-ssot
title: Chunk-Safe Manifest Migrations
summary:
  Chunked-shard + coordinator pattern (UTL ManifestMigrator / RescanScanner / chunked_date_ranges) for running long
  manifest migrations across N VMs without racing the single _index parquet — workers write disjoint
  _index/partial/<run-id>/<chunk>.parquet and one singleton-locked coordinator merges then deletes them.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-service, instruments-service, unified-trading-library]
scope: [engineer, admin]
tags: [manifest, migration, backfill, single-walk, spot-vm, infrastructure]
related:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/cross-asset-rescan-protocol.md,
    /codex/05-infrastructure/vm-tarball-deployment.md,
  ]
created: 2026-04-21
authoritative_for: [chunk-safe parallel manifest migration pattern (worker/coordinator/partial-shard)]
referenced_by: [/codex/02-data/cross-asset-rescan-protocol.md, /codex/02-data/sports-scheduling-and-sharding.md]
owner:
last_reviewed: 2026-05-17
code_refs:
last_updated: 2026-04-21
---

# Chunk-Safe Manifest Migrations

**Canonical implementation:** `unified-trading-library` → `unified_trading_library.manifest_migrations`
(`ManifestMigrator`, `RescanScanner`, `LegacyRowPurger`, `chunked_date_ranges`). Consumer repos (e.g.
`instruments-service`) keep thin CLI entry points; do not fork the chunk-safe machinery into a second copy.

Pattern for running long migrations / backfills / rescans in parallel across N VMs without racing on the availability
manifest index.

## When to use

Use this pattern when all three are true:

1. The migration emits rows into `_index/availability_index.parquet` (or any other per-bucket singleton parquet).
2. The work window is long enough that one VM takes > ~30 minutes.
3. The date dimension (or another disjoint partition key) lets you split the work into N non-overlapping slices.

If any of those is false, use the single-VM shape — it's simpler and the last-writer-wins pattern is fine for small jobs
(rescan finishes in one write).

## The problem

The honest-coverage manifest at `gs://<bucket>/_index/availability_index.parquet` is a single parquet file. Every writer
does a read-modify-write cycle:

```
read canonical → filter rows we're replacing → append new rows → write canonical
```

Ten VMs running that loop concurrently will race. Whichever finishes last wins; rows from the others are silently
overwritten. Optimistic concurrency (`if_generation_match=...` with retry on 412) would work for ~2-3 writers but
collapses into livelock at 10+.

## The pattern — chunked shards + coordinator

Three execution modes, all in one script:

```
         ┌─────────────┐   ┌─────────────┐        ┌─────────────┐
         │  worker-1   │   │  worker-2   │  ...   │  worker-N   │
         │  date-range │   │  date-range │        │  date-range │
         │   A..B      │   │   C..D      │        │   Y..Z      │
         └──────┬──────┘   └──────┬──────┘        └──────┬──────┘
                │                 │                      │
                ▼                 ▼                      ▼
         _index/partial/<run-id>/1.parquet
         _index/partial/<run-id>/2.parquet
         ...
         _index/partial/<run-id>/N.parquet
                            │
                            ▼
                  ┌──────────────────┐
                  │   coordinator    │
                  │ reads canonical  │
                  │ + all partials   │
                  │ merges, writes,  │
                  │ deletes partials │
                  └────────┬─────────┘
                           ▼
                _index/availability_index.parquet
```

**Invariants:**

- Workers NEVER read or write the canonical index. Each writes exactly one partial file under
  `_index/partial/<run-id>/<chunk-id>.parquet`.
- `run-id` is a single timestamp shared across all workers in the same job, generated once by the launcher.
- `chunk-id` is unique within a run (e.g. `3-of-10`).
- Coordinator runs exactly once, after all workers finish. It does one read-modify-write of the canonical index plus a
  cleanup of the partials.
- Only one coordinator can run at a time (singleton-locked).
- Workers for the same run-id are allowed to coexist in the singleton check; workers from a different run-id (or the
  coordinator) are blocked.

## CLI shape

Migration script exposes three modes via one entry point. Example from
[`instruments-service/scripts/rescan_sports_fixtures_canonical.py`](../../instruments-service/scripts/rescan_sports_fixtures_canonical.py):

```bash
# Single-VM (default, historical behaviour — fine for small jobs)
python scripts/rescan_sports_fixtures_canonical.py --workers 16

# Worker (scans a date range, writes a partial, exits)
python scripts/rescan_sports_fixtures_canonical.py \
  --chunk-id 3-of-10 --run-id 20260421-120000 \
  --date-start 2024-01-01 --date-end 2024-04-15 --workers 16

# Coordinator (merges all partials into canonical, deletes partials)
python scripts/rescan_sports_fixtures_canonical.py \
  --coordinate --run-id 20260421-120000
```

Mode selection:

| Flag combination                          | Mode        |
| ----------------------------------------- | ----------- |
| (neither `--chunk-id` nor `--coordinate`) | single-VM   |
| `--chunk-id X --run-id Y`                 | worker      |
| `--coordinate --run-id Y`                 | coordinator |

Validation: `--chunk-id` and `--coordinate` are mutually exclusive; both require `--run-id`.

## Launcher shape

The launcher generates `RUN_ID` once and fans out N workers + (after workers finish) one coordinator. Example from
[`deployment-service/scripts/vm/launch-sports-manifest-rescan-vm.sh`](../../deployment-service/scripts/vm/launch-sports-manifest-rescan-vm.sh):

```bash
# Fan out 10 workers across the full history
bash launch-sports-manifest-rescan-vm.sh \
  --chunks 10 --date-start 2018-01-01 --date-end 2026-04-20

# Poll for completion
gcloud compute instances list \
  --filter='labels.run-id=<stamp> AND status=RUNNING' --zones=asia-northeast1-c

# Merge the partials into canonical
bash launch-sports-manifest-rescan-vm.sh --coordinate --run-id <stamp>
```

Launcher responsibilities:

1. **Generate `RUN_ID` once** before any gcloud call.
2. **Split the date range** into N non-overlapping chunks. Delegate to the script's `_split_date_range()` helper so
   Python and bash agree on slicing.
3. **Label every VM** with `run-id=<stamp>,chunk=<i-of-N>` so polling / log correlation works.
4. **Singleton-lock smart-mode:** allow sibling workers of the same `run-id` to coexist; block everything else.
5. **Coordinator launch** must reject overlap with any running rescan (workers or other coordinators), because the
   canonical read-modify-write can't tolerate peers.

## Write semantics the pattern preserves

The coordinator's merge must match the single-VM merge exactly:

1. Read canonical.
2. Drop the rows this migration is replacing (filter predicate is migration-specific — for FIXTURES it's
   `data_type == "FIXTURES" AND service_name == "instruments-service" AND league_id != ""`).
3. Append all worker partial rows.
4. Write canonical.
5. Delete `_index/partial/<run-id>/*.parquet` (best-effort).

Any rows the workers happen to emit twice (e.g. overlapping ranges) will both land in the final manifest. That's usually
wrong for per-(date, league_id) shards — **workers must scan disjoint date ranges**. The launcher's date-range splitter
enforces this.

## What this pattern does NOT solve

- **Schema migrations across the whole manifest** — use a one-off single-VM migration; the coordinator is not a
  distributed transaction.
- **Row-level dedup** — the coordinator blindly unions worker partials. If two workers emit the same row key, both land
  in the manifest. The launcher must split work by a genuinely disjoint key.
- **Cross-bucket migrations** — each bucket has its own canonical index and needs its own coordinator. If a migration
  spans buckets, chain one coordinator per bucket.

## Future reuse

Candidates that should adopt this pattern on their next long migration:

- MTDS per-venue tick-data canonicalisation (when it runs over 2+ years of history).
- Instruments-service per-instrument sentinel backfill (Tier-3 shards over many chains × instrument_types).
- Features-onchain feature-group rebuild.

Use **UTL** (`ManifestMigrator` + `chunked_date_ranges` + optional `RescanScanner` / `LegacyRowPurger`) for every new
migration — wire a migration-specific `drop_canonical_row` predicate and Parquet scan callbacks; do not duplicate
coordinator/worker/partial-path logic in service repos.

## SSOT cross-refs

- [`/codex/02-data/availability-manifest-and-data-status.md`](availability-manifest-and-data-status.md) — manifest v5
  shard columns + `capture_status`.
- [`/codex/02-data/sports-data-source-coverage-matrix.md`](sports-data-source-coverage-matrix.md) — Phase 5 FIXTURES
  per-league rescan motivation.
- [`/codex/05-infrastructure/vm-tarball-deployment.md`](/codex/05-infrastructure/vm-tarball-deployment.md) — how any VM
  boots the migration script via `setup-data-pipeline-vm.sh`.
- Singleton-lock reference incident — 2026-04-19 SFI thundering herd (10 VMs / 6 hours / ~4 useful writes).
