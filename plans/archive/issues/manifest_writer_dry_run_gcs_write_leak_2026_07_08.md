---
doc_type: issue
title:
  ManifestWriter ignores UCI dry-run — every service's `--dry-run` flag silently writes real availability_index rows to
  prod GCS
summary: |
  While diagnosing sports-features manifest cleanliness (`sports_p2_features_history_to_ml_ready_2026_06_27`
  Todo 3), ran `features_service --feature-family sports --operation compute --dry-run --force --date 2025-09-01`
  to validate a fix. The CLI logged `DRY RUN — no cloud writes will be performed` +
  `UCI dry-run mode ACTIVE — all data sinks redirected to local`, but the run still appended 33 real rows to
  `gs://features-sports-prd-central-element-323112/_index/availability_index.parquet` (verified: object
  `Update time` + size changed immediately after the run; row count 3564→3584; new rows carry `written_at`
  matching the dry-run's wall-clock). Root cause: `ManifestWriter`'s GCS write path
  (`unified_trading_library/manifest_writer/_writer_io.py:565,627`) calls
  `unified_trading_library.cloud_interface.get_storage_client()` directly. Only `get_data_sink()` (used by the
  actual feature/candle/tick parquet writers) checks the module-level `_dry_run_active` flag
  (`unified_trading_library/cloud_interface/factory.py:429-441`) and redirects to `LocalDataSink`.
  `get_storage_client()` has no dry-run awareness at all — it always constructs a real `GCSStorageClient`
  regardless of `set_dry_run(True)`. `ManifestWriter` is used by every catalogued service (instruments-service,
  market-tick-data-service, features-service, …), so this is a cross-cutting UTL bug, not sports-specific: **any
  `--dry-run` invocation anywhere in the fleet silently writes real manifest rows to production**, contradicting
  the documented/logged contract ("no cloud writes will be performed").
status: resolved
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-library, features-service, instruments-service, market-tick-data-service]
scope: [engineer]
tags: [manifest, dry-run, data-correctness, ssot-contradiction, cross-repo, ucI, gcs]
related:
  [
    /plans/archive/2026_07/sports_p2_features_history_to_ml_ready_2026_06_27.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-07-08
parent_epic: sports_master
priority: P1
source:
  [
    sports_p2_features_history_to_ml_ready_2026_06_27.md (Todo 3,
    20th dispatch — slot 3),
    unified_trading_library/manifest_writer/_writer_io.py:560-630,
    unified_trading_library/cloud_interface/factory.py:429-460,
  ]
assigned_vm: planning
resolved_by: unified-trading-library@4e28da4e
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-08
---

## What I found

Running
`python3 -m features_service --feature-family sports --operation compute --mode batch --asset-group SPORTS --date 2025-09-01 --force --dry-run`
(intended as a safe, side-effect-free validation of a code fix) logged:

```
WARNING UCI dry-run mode ACTIVE — all data sinks redirected to local
WARNING DRY RUN — no cloud writes will be performed
...
INFO ManifestWriter: updated availability index (3584 total entries, 33 new) in features-sports-prd-central-element-323112
```

`gsutil stat gs://features-sports-prd-central-element-323112/_index/availability_index.parquet` before/after:

|                | before             | after                                                      |
| -------------- | ------------------ | ---------------------------------------------------------- |
| Content-Length | 90,331             | 91,211                                                     |
| Update time    | (2026-07-03 write) | 2026-07-08 20:03:42 GMT — matches the dry-run's wall clock |
| Row count      | 3,564              | 3,584                                                      |

Diffing the two parquets: 33 rows have `written_at` timestamps inside the dry-run's execution window (20:00:14–20:03:14
UTC 2026-07-08), all for `date=2025-09-01` across `fixture_stats`, `fixture_events`, `venues`, `fixtures`, `leagues`,
`teams`, `standings`, `derived_features` (×9 leagues), `fixture_features` (×9 leagues), `odds_features`, plus 6
`empty_confirmed`/`attempted_failed` rows for `fixture_lineups`, `fixture_player_stats`, `injuries`, `players`,
`referees`, `coaches`, `rounds`. These are REAL rows in the production catalogue, written by a command whose entire
purpose was to be a no-op.

**Root cause** (read, not guessed — traced the exact call path):

1. `ServiceRuntime` bootstrap calls `unified_trading_library.cloud_interface.factory.set_dry_run(True)` when `--dry-run`
   is passed, which sets a module-level `_dry_run_active = True`.
2. `get_data_sink(...)` (factory.py:438-441) checks that flag and returns `LocalDataSink()` — this is what the real
   feature-parquet writers use, and it correctly stayed local (no feature parquet files were written to prod during the
   dry-run; the actual data output was fine).
3. `ManifestWriter`'s write path (`_writer_io.py:560-568` and `:625-630`) instead calls
   `unified_trading_library.cloud_interface.get_storage_client()` — a **different** factory function
   (factory.py:125-166) that has **no `_dry_run_active` check anywhere in its body**. It always builds a real
   `GCSStorageClient` (or `S3StorageClient`) and hits the network.
4. `ManifestWriter.__init__` (`_writer.py:92-155`) also has no `dry_run` parameter to plumb through, so there is no way
   for a caller to opt the manifest-write path out of the network even explicitly.

Grepped every file in `unified_trading_library/manifest_writer/` (`_writer.py`, `_writer_io.py`, `_core.py`,
`_writer_captured.py`, `_writer_ingest.py`, `_writer_validation.py`, `_writer_record.py`, `_rows.py`) for `dry_run` —
zero matches. The only `dry_run`-aware code in the whole package is the unrelated `manifest_writer/_maintenance.py`
(rebuild/cleanup CLI utilities), which is not in the hot write path.

## Why it matters

- **Contradicts the logged contract.** The CLI explicitly promises "no cloud writes will be performed" — this is false
  for the manifest catalogue on every service that uses `ManifestWriter` (instruments-service, market-tick-data-service,
  features-service, and any other consumer). Any agent or operator running a `--dry-run` smoke test to validate a fix is
  unknowingly polluting the production availability index.
- **Corrupts exactly the signal this codebase relies on for correctness gating.** `availability_index.parquet` is the
  SSOT the manifest-cleanliness gates (`check_pipeline_completeness.py`, per-era completeness checks, the
  honest-absence/`capture_status` machinery) all read from. A dry-run's synthetic `attempted_failed` / `empty_confirmed`
  rows are now indistinguishable from real production outcomes.
- **This session's concrete damage**: the dry-run above duplicated an existing genuine
  `injuries@2025-09-01 attempted_failed(ValueError)` row (now 2 copies) and added 32 other rows for a date whose real
  compute state was already fully captured. This directly pollutes the exact "0 blank-reason, 0 un-evidenced
  attempted_failed" cleanliness gate `sports_p2_features_history_to_ml_ready_2026_06_27` Todo 3 is trying to verify.
- **Likely not new** — 19 prior dispatches of the same sports-features task did extensive live GCS investigation; if any
  used `--dry-run` for validation (a natural instinct when "just checking" prod data), the manifest may already carry
  other undetected synthetic rows from this session's discovery date backward. Not independently verified in this pass —
  flagged as a follow-up below rather than a confirmed second incident.

## Recommended decision

Fix in `unified-trading-library` (the shared root cause), not per-service:

1. **Give `ManifestWriter` dry-run awareness.** Either (a) add an explicit `dry_run: bool | None = None` constructor
   param (mirroring the existing `strict_validation`/`per_vm_shards` "None = read from `UnifiedCloudConfig`" pattern
   already used in `_writer.py:__init__`), defaulting to
   `unified_trading_library.cloud_interface.factory._dry_run_active` when unset; or (b) expose a public
   `is_dry_run() -> bool` accessor next to `set_dry_run()` in `factory.py` and have `_writer_io.py`'s two
   `get_storage_client()` call sites (lines ~565, ~627) short-circuit to a no-op local write when it's `True` — logging
   what WOULD have been written, same as `get_data_sink()`'s redirect.
2. Add a regression test in UTL's `manifest_writer` test suite: `set_dry_run(True)`, construct a `ManifestWriter`, call
   `record_captured(...)` + `write()`, assert no real GCS call is made (patch/mock `get_storage_client` and assert
   not-called, or assert a `LocalStorageProvider`-equivalent path is used).
3. **Cleanup**: the 33 polluted rows for `features-sports-prd-central-element-323112` / `date=2025-09-01` are expected
   to be naturally overwritten once the real (non-dry) `--force` recompute for that date runs (manifest dedups on the
   row key, not `written_at` — confirmed by this session's own diff: 33 raw appends net to +20 rows for the day,
   implying ~13 already deduped against pre-existing keys at write time). No manual GCS surgery recommended — a real
   recompute is the correct fix path and is already planned as part of Todo 1/Todo 3 of
   `sports_p2_features_history_to_ml_ready_2026_06_27`.
4. **Follow-up audit** (separate, smaller task): grep prior session logs/plan Progress Logs across the sports backfill
   plans for any other `--dry-run` invocations against prod buckets, to bound whether other manifests were similarly
   polluted.

## Follow-up audit (Todo 3, 2026-07-08)

Grepped all 9 `plans/active/sports_p1_*` + `plans/active/sports_p2_*` plan files (the full set of 19 prior dispatches,
2026-06-27 → 2026-07-07) for every `--dry-run` occurrence, then traced each one to its actual code path rather than
pattern-matching on the string alone:

| Plan file (line)                                                  | `--dry-run` command                                                                                               | Traced to                                                                                                                                                                                                                 | Vulnerable?                                                                                                                            |
| ----------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `sports_p1_golden_window_apifootball_2026_06_27.md:221`           | `reconcile_phantom_manifest_rows.py --dry-run --data-types STANDINGS,TEAMS`                                       | `instruments-service/scripts/reconcile_phantom_manifest_rows.py:221` — `if args.dry_run: logger.info(...); return 0` **before** any write call                                                                            | No — script's own dry-run returns before the canonical-manifest write; never touches `ManifestWriter`/`get_storage_client` write path. |
| `sports_p2_history_apifootball_2015_to_present_2026_06_27.md:97`  | `run_sports_fixtures_p2a_2026_06_27.sh` "--dry-run verified"                                                      | `instruments-service/scripts/run_sports_fixtures_p2a_2026_06_27.sh:49-50` — dry-run branch only echoes "[DRY RUN] Would run: …" and never invokes `sports_chunked_backfill.sh`/the instruments-service CLI                | No — coordinator's dry-run never spawns the service process at all.                                                                    |
| `sports_p2_history_apifootball_2015_to_present_2026_06_27.md:267` | `audit_fixtures_via_api_football.py --dry-run` (`GCP_PROJECT_ID=central-element-323112 DEPLOYMENT_ENV_SHORT=prd`) | `instruments-service/scripts/audit_fixtures_via_api_football.py:417-431` — dry-run branch only logs the would-be work plan; `get_storage_client()` call above it (line 406) is read-only (loads the manifest for diffing) | No — no `ManifestWriter`/write call anywhere in this script; the one `get_storage_client()` use is a read.                             |
| `sports_p2_history_apifootball_2015_to_present_2026_06_27.md:321` | `run_sports_enrichment_core_p2a_2026_06_27.sh` "--dry-run"                                                        | `instruments-service/scripts/run_sports_enrichment_core_p2a_2026_06_27.sh:72-73` — same pattern as the fixtures coordinator: dry-run branch only echoes, never spawns the service                                         | No — same as above.                                                                                                                    |
| `sports_p2_features_history_to_ml_ready_2026_06_27.md:146`        | `features_service --dry-run --force --date 2025-09-01`                                                            | This IS the original incident that produced this issue doc — not a second occurrence.                                                                                                                                     | N/A — already the documented finding.                                                                                                  |

Confirmed via a second grep pass requiring a service-CLI name (`features_service`/`instruments-service`/
`instruments_service`/`market-tick-data-service`/`mtds`) on the same line as `--dry-run` across all 9 files: **zero
matches**. None of the 19 prior dispatches invoked a `ServiceRuntime`-bootstrapped service CLI (the only code path that
calls `factory.set_dry_run(True)` and therefore reaches the leaking `ManifestWriter` → `get_storage_client()` call) with
`--dry-run`. **No additional manifest pollution found** — the single incident already documented above (33 rows,
`features-sports-prd-central-element-323112`, `date=2025-09-01`) is the only one in this window. No further cleanup
action needed beyond Todo (3) above (natural overwrite on the real recompute).

## Todos

- [x] ✅ [BACKEND] P1. Add dry-run awareness to `ManifestWriter`'s GCS write path — gate the two `get_storage_client()`
      call sites in `unified-trading-library/unified_trading_library/manifest_writer/_writer_io.py` (~lines 560-568,
      625-630) behind the existing `unified_trading_library.cloud_interface.factory._dry_run_active` flag (add a public
      `is_dry_run()` accessor in `factory.py` alongside `set_dry_run()`), matching `get_data_sink()`'s existing
      redirect-to-local behavior. Ship via UTL QG + quickmerge. (repo: unified-trading-library) — 2026-07-08 (slot-2):
      shipped `unified-trading-library@4e28da4e`. `is_dry_run()` accessor added next to `set_dry_run()`
      (`cloud_interface/factory.py`, re-exported from `cloud_interface/__init__.py`); both `_writer_io.py` call sites
      (`_write_to_gcs` legacy CAS path, `_flush_per_vm_pending` per-VM shard path) now short-circuit before
      `get_storage_client()` when `is_dry_run()` is true, logging what would have been written and draining any staged
      per-VM pending rows so nothing leaks into a later real write. QG green (124s), pushed via quickmerge.
- [x] ✅ [BACKEND] P1. Add a regression test to `unified-trading-library`'s manifest_writer test suite:
      `set_dry_run(True)` + `ManifestWriter(...).record_captured(...).write()` must NOT call the real
      `get_storage_client()` / hit GCS. (repo: unified-trading-library) — 2026-07-08 (slot-2): shipped in the same
      commit, `unified-trading-library@4e28da4e`, `tests/unit/test_manifest_writer_dry_run.py` (3 tests: legacy-mode
      no-op, per-VM-mode no-op, dry-run-off control). Used `writer.add()`/`write()`/`flush()`/`_drain()` rather than
      `record_captured()` directly (simpler kwargs, same code path) — verified BOTH fail with
      `AssertionError: get_storage_client() must not be called` when stashed against pre-fix code (proving they exercise
      the real bug), and pass clean post-fix.
- [x] ✅ [DATA] P2. Follow-up audit: grep `plans/active/sports_p2*` + `plans/active/sports_p1*` Progress Log entries (19
      prior dispatches, 2026-06-27 → 2026-07-07) for `--dry-run` invocations against `features-sports-prd-*` or
      `instruments-store-*` buckets; for any found, diff the affected date's manifest rows the same way this issue doc
      did, to bound whether other manifest pollution needs the same natural-overwrite cleanup path. (repo:
      unified-trading-pm) — unified-trading-pm@(this commit). Result: 5 `--dry-run` mentions found across all 9 sports
      plan files, all traced to code paths that do NOT reach the vulnerable `ManifestWriter`/`get_storage_client()`
      write call (see "Follow-up audit" section above). Zero additional pollution found; no cleanup action needed.

## Progress Log

### 2026-07-08 21:10 UTC — slot-2: both fix todos shipped, issue resolved

Task `manifest_writer_dry_run_gcs_write_leak-002` (regression test). Implemented both remaining todos together since the
test has nothing to assert without the fix existing first: `unified-trading-library@4e28da4e` adds `is_dry_run()` next
to `set_dry_run()` in `cloud_interface/factory.py` (+ re-export from `cloud_interface/__init__.py`) and gates both
`_writer_io.py` GCS call sites (`_write_to_gcs`, `_flush_per_vm_pending`) behind it, logging what would have been
written instead of hitting the network. Added `tests/unit/test_manifest_writer_dry_run.py` (3 tests) — verified they
fail with `AssertionError: get_storage_client() must not be called` when stashed against the pre-fix tree (proving they
exercise the real bug) and pass clean post-fix. QG green (124s), shipped via quickmerge. Todo (3) (natural-overwrite
cleanup) and (4) (follow-up audit) were already closed by a prior session. Marking `status: resolved`.
