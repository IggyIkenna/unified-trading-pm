---
doc_type: issue
title: UTL GCS client silent write failure — wrong method names swallowed by a defensive guard, cross-repo
summary: >-
  deployment_service/deployment/state.py called upload_from_string()/download_as_string() on UTL's GCS handle --
  methods that do not exist on the current get_storage_client() factory's GCSBlobHandle. A defensive
  getattr/callable() guard swallowed the AttributeError silently: save_state() logged "Created deployment" and
  returned success while writing NOTHING to GCS. Fixed in state.py (2026-08-18) via the proven upload_bytes/
  download_bytes pattern already correct in wave_launcher.py. The same anti-pattern was confirmed and fixed
  (2026-08-18) in monitor.py/orchestrator.py/vm_monitoring.py (deployment-service@a773a597bb), each verified via a
  real live write+read-back against its actual bucket. A full fleet-wide triage (36 files outside
  deployment-service) found 16 genuine Category-1 files (22 call sites, all in instruments-service +
  strategy-service, NOT yet fixed -- follow-up plan pending), 13 Category-2 raw-SDK-import violations (working but
  non-compliant), and 7 Category-3 false positives (incl. UTL's own manifest pipeline, which already has a correct
  workaround). Two NEW, separate findings surfaced during the fix: (1) T1Orchestrator's log_event() calls
  throughout orchestrator.py pass kwargs the real log_event() signature rejects -- crashes in real (non-test-mocked)
  execution, masked entirely by every test patching log_event out; (2) the deployment-metadata-{project}/
  deployment-status-{project} buckets DeploymentMonitor/VersionRegistry target do not exist in the production GCP
  project -- that subsystem has likely never persisted data, independent of the method-name bug.
status: open
nature: design
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service, unified-trading-library]
scope: [engineer]
tags: [gcs, data-correctness, silent-failure, cross-repo, utl]
related:
  [
    /plans/active/deployment_service_api_integration_cleanup_2026_08_18.md,
    /codex/05-infrastructure/gcs-object-operations.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-18
last_updated: "2026-08-20"
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class:
estimate_baseline_ai_days:
estimate_calibrated_ai_days:
assigned_role: infra
effort: medium
resolved_by:
drift_direction: advance-code
depends_on:
context_scope:
  [
    /plans/active/deployment_service_api_integration_cleanup_2026_08_18.md,
    /codex/05-infrastructure/gcs-object-operations.md,
    deployment-service/deployment_service/deployment/state.py,
    deployment-service/scripts/wave_launcher.py,
    deployment-service/deployment_service/monitor.py,
  ]
supersedes:
superseded_by:
source:
  [
    "Surfaced 2026-08-18 fixing deployment_service_api_integration_cleanup_2026_08_18.md todo 2 (Deploy Console
    live-broken bug) -- the fix's own end-to-end verification caught save_state() returning false-success while
    writing nothing to GCS. Root cause: StateManager.save_state/load_state/list_deployments called
    client.bucket().blob().upload_from_string()/.download_as_string() -- methods absent from UTL's current
    GCSBlobHandle/GCSBucketHandle (read-only handle, confirmed by introspection) -- guarded by a getattr/callable()
    check that degraded silently instead of failing loud.",
  ]
locked_by:
locked_since:
---

# UTL GCS client silent write failure — wrong method names, cross-repo

## What happened (confirmed, not hypothesized)

Fixing the Deploy Console live-broken-deploy bug (`deployment_service_api_integration_cleanup_2026_08_18.md` todo 2)
required exercising `StateManager.save_state()`/`load_state()`/`list_deployments()` in
`deployment_service/deployment/state.py` end-to-end against the real `unified-deployment-state-central-element-323112`
bucket. First pass: the function returned a clean success JSON — but the object was never actually written to GCS,
caught only by directly checking `blob.exists()` after the call, not by trusting the return value.

**Root cause**: these three methods called `client.bucket().blob().upload_from_string()` /
`.download_as_string()` — methods that do not exist on UTL's `get_storage_client()` factory's returned
`GCSBlobHandle`/`GCSBucketHandle` (confirmed via introspection: the handle is read-only w.r.t. those method names,
no `upload_from_string` at all). A defensive `getattr(...)`/`callable()` guard around the call swallowed the
resulting failure silently instead of raising — `save_state()` logged "Created deployment" and returned a
success-shaped result on every call, while persisting nothing.

**This exact failure mode was already hit and fixed once in this same repo**:
`deployment_service/scripts/wave_launcher.py` uses the correct pattern (`client.upload_bytes(...)` /
`download_as_bytes(...)`) — `state.py` simply never received the same fix when the bug was first found elsewhere.

## Fixed

**`state.py` (2026-08-18, as part of the Deploy Console fix)**: all three methods switched to
`upload_bytes`/`download_as_bytes`, matching `wave_launcher.py`'s proven pattern. ~15 test-mock call sites in
`test_deployment_state.py` and `test_deployment_orchestrator.py` updated to match. Shipped:
`deployment-service@c16b1f1407`. Re-verified live: write succeeds, an independent read-back returns the correct
persisted state, no more false-success.

**`monitor.py` / `orchestrator.py` / `vm_monitoring.py` (2026-08-18, this session)**: shipped
`deployment-service@a773a597bb`. Triage + fix + live verification per file/method below — the bug's manifestation
varies by call site depending on whether a defensive `getattr`/`callable()` guard was present (silent no-op,
`state.py`'s exact shape) or absent (uncaught `AttributeError` crash):

- **`orchestrator.py`'s `T1Orchestrator`** — triage question resolved: it sources its GCS client via the identical
  `get_storage_client()` factory as `state.py` (see the `gcs_client` property), not a separately-instantiated
  client, so it shares the exact bug. `save_plan()` (`bucket.blob().upload_from_string()`, guarded, silent no-op)
  and `load_plan()` (`blob.download_as_text()`, unguarded, crash) both fixed to `upload_bytes`/`download_as_bytes`.
  **Verified live**: wrote + read back a scratch `OrchestrationPlan` against the real
  `deployment-orchestration-central-element-323112` bucket (the bucket this code actually targets), confirmed
  correct content, `delete_blob()` cleanup confirmed via `blob.exists() == False` after.
- **`vm_monitoring.py`'s `VMMonitoringManager.check_gcs_status()`** — `blob.download_as_string()` (unguarded,
  crash) fixed to `download_as_bytes()`. This was a live-breaking bug: it crashed every time a VM's completion
  status marker was actually found (`blob.exists() == True`) — the common case this method exists to detect.
  `_get_status_from_gcs()`'s own `download_as_string()` call was confirmed NOT broken (see below) and left
  unchanged. **Verified live**: wrote a real status marker + read it back via `VMMonitoringManager` against the
  real `deployment-orchestration-central-element-323112` bucket (confirmed as the actual production
  `status_bucket` — it resolves via `DeploymentConfig.effective_state_bucket`, not a hardcoded literal), cleaned up.
- **`monitor.py`'s `DeploymentMonitor.get_service_version()` / `.record_event()` / `._parse_events_blob()` and
  `VersionRegistry.register_version()`** — all four fixed (guarded no-ops → `upload_bytes`/`download_as_bytes`
  calls that actually execute; unguarded `download_as_text()` crash → `download_as_bytes()`). `record_event()` is
  live-called from `live_deployment.py` for every VM/deploy lifecycle event and its output (`get_vm_events()`) is
  served by `deployment-api`'s `_lifecycle.py` route to the Deploy Console — this was silently dropping the entire
  VM-event timeline. `register_version()` is also live-called from `live_deployment.py` (explicitly
  best-effort/non-blocking by that call site's own comment — a write failure here was never going to crash a
  deploy, but the version-history data was silently never persisted either way).
  **`DeploymentMonitor.get_deployment_status()` and `VersionRegistry.get_version_history()` were confirmed NOT
  broken and left unchanged** — both read blobs via `bucket.list_blobs()`, which (confirmed by reading
  `unified_trading_library/cloud_interface/providers/gcp.py`'s `GCSBucketHandle.list_blobs()`) returns the
  **native, unwrapped `google.cloud.storage.Blob` iterator**, not the read-limited `GCSBlobHandle` that
  `bucket.blob(path)` returns — so `.download_as_text()` genuinely exists and works on those objects. This
  `.blob()` (wrapped, broken) vs `.list_blobs()` (native, works) distinction is the key mechanism throughout this
  bug class and is called out inline in the fixed source.
  **Live write+read-back verification against monitor.py's OWN target buckets was not possible** — see the new
  "missing buckets" finding below. Verified instead: (a) the `upload_bytes()`/`download_as_bytes()` call surface
  (identical code path to the fix) round-trips correctly against a real, existing bucket; (b) `record_event()` now
  reaches an actual GCS network call and fails with a genuine `google.api_core.exceptions.NotFound` (404, bucket
  does not exist) instead of silently swallowing an `AttributeError` before ever touching the network — proving the
  method-name bug is fixed and isolating the separate, pre-existing bucket-provisioning gap.
- Added new unit test coverage for `record_event()`/`get_events()` in `test_monitor.py` — **neither had ANY test
  coverage before this fix**, which is exactly how the always-`False` `getattr(blob, "upload_from_string", None)`
  guard shipped and stayed silent for however long it's been live.
- All existing test mocks asserting the old method names (`upload_from_string`/`download_as_text`/
  `download_as_string` on `.blob()`-sourced mocks) updated across `test_monitor.py`,
  `test_top_level_orchestrator.py`, `test_backends_vm_services.py` — mocks on `.list_blobs()`-sourced blobs
  (confirmed-correct call sites) were deliberately left unchanged.

## Two NEW findings surfaced while fixing the three files above (NOT fixed — flagging for the operator / a
## dedicated follow-up, both out of scope for a "fix the wrong method name" task)

1. **`orchestrator.py`'s `log_event()` calls pass kwargs the real function doesn't accept.** UTL's actual
   `log_event(event_name, severity="INFO", details=None, client_id=None, correlation_id=None)` (both the
   `events_interface` and `events` module copies — confirmed identical signature) does **not** take arbitrary
   kwargs, but essentially every `log_event(...)` call site in `orchestrator.py` passes free-form ones (`date=`,
   `asset_group=`, `service=`, `error_type=`, `total_jobs=`, `execution_tiers=`, etc.) — confirmed live: exercising
   `save_plan()`'s own success-path `log_event("orchestrator.md.saved", date=plan.date, ...)` call raises
   `TypeError: log_event() got an unexpected keyword argument 'date'` immediately after a successful GCS write.
   **Every single deployment-service test touching `T1Orchestrator` masks this** by wrapping the call in
   `with patch("deployment_service.orchestrator.log_event"):` (see `test_top_level_orchestrator.py`, every test) —
   so the real function has apparently never actually run against this file's call sites in CI. This means
   `create_daily_plan()`, `propagate_failure()`, `save_plan()`, `load_plan()`, and the `gcs_client` property's error
   handlers are all likely to crash with `TypeError` on their first `log_event()` call in real (non-test-mocked)
   production execution — independent of, and probably more severe than, the GCS silent-write bug this doc is
   about. Not fixed here (different bug class, would need an audit of every `log_event()` call site in the file,
   not a 3-file targeted fix) — needs its own triage/fix pass.
2. **`deployment-metadata-{project}` and `deployment-status-{project}` GCS buckets do not exist** in the production
   project (`central-element-323112`) — confirmed via `bucket.exists() == False` for both, vs.
   `deployment-orchestration-{project}` and `unified-deployment-state-{project}` which both confirmed `True`. These
   are the two hardcoded bucket names `DeploymentMonitor`/`VersionRegistry` target (not resolved via
   `resolve_bucket_name()` — itself a separate, pre-existing "no inline bucket name" coding-standard gap). No
   Terraform/infra-as-code declaration for either bucket was found anywhere in the workspace. Net effect: the
   VM-event-timeline (`record_event`/`get_events`, Deploy Console) and service-version-registry
   (`register_version`/`get_version_history`) features have likely **never** persisted or read real data in
   production, independent of (and previously masked by) the method-name bug fixed above — fixing the method names
   alone does not restore this functionality; the buckets need to be provisioned (or the code retargeted at
   existing buckets) first. Not created in this session — bucket creation is a real infra decision (naming
   convention, IAM, whether to route through `resolve_bucket_name()` instead of perpetuating the hardcoded literal)
   that belongs in a scoped follow-up, not a silent side-effect of a bug-fix task.

## Fleet-wide triage (Part 2, 2026-08-18) — definitive category table, audit only, no fixes applied outside
## deployment-service

Re-ran the workspace-wide grep for `\.(upload_from_string|download_as_string)\(` fresh (don't trust the prior "60+"
count): **39 unique non-test production files + several test-only hits + one stray duplicate** (a leftover agent
worktree copy of `vm_monitoring.py` at
`deployment-service/.claude/worktrees/agent-aa4b436033ef73e2f/deployment_service/backends/services/vm_monitoring.py`
— not real source, a hygiene artifact, not triaged as a real file). The "60+" figure was almost certainly inflated
by test-file/worktree-duplicate noise in the original untriaged grep.

**Category definitions**: **1** = traces to `get_storage_client()` AND the call is on a `.blob(path)`-sourced
object (the wrapped `GCSBlobHandle`, which lacks these methods) → genuine silent-write-failure/crash bug. **2** =
calls the real raw `google.cloud.storage` SDK's `Blob.upload_from_string()`/`download_as_string()` directly (the
calling code itself imports `google.cloud.storage`) → works fine functionally, but a "no direct google.cloud"
coding-standard violation. **3** = false positive (not a real GCS blob call, a test double, or — the key
non-obvious subcase found repeatedly below — a `get_storage_client()`-sourced call where the blob was NOT sourced
via `.blob()` (works fine, no bug): either `bucket.list_blobs()` returning native unwrapped blobs, or code
deliberately reaching into `GCSStorageClient`'s private `._client` attribute to grab the raw native SDK client,
bypassing the wrapper entirely).

| # | Repo | File | Category | Evidence |
|---|---|---|---|---|
| 1 | instruments-service | `scripts/dedupe_manifest_schema_drift.py` | **1** | `get_storage_client()` → `client.bucket(args.bucket).blob(args.blob).upload_from_string(...)` |
| 2 | instruments-service | `scripts/fix_prediction_manifest_and_gcs_2026_05_22.py` | **1** | `get_storage_client()` → `bucket.blob(snapshot_path).upload_from_string(...)` |
| 3 | instruments-service | `scripts/migrate_available_at_column.py` | **1** | `get_storage_client()` → `bucket.blob(blob_name)` → `.upload_from_string(...)` |
| 4 | instruments-service | `scripts/migrate_fixtures_split.py` | **1** | `get_storage_client()` → `bucket.blob(dest_name).upload_from_string(...)` |
| 5 | instruments-service | `scripts/migrate_local_sfi_to_canonical.py` | **1** | `get_storage_client()` → `bucket.blob(blob_path).upload_from_string(...)` |
| 6 | instruments-service | `scripts/migrate_sports_available_at_column.py` | **1** | `get_storage_client()` → `bucket.blob(blob_name).upload_from_string(...)` |
| 7 | instruments-service | `scripts/purge_bad_prediction_manifest_rows.py` | **1** | `get_storage_client()` → 2 call sites, both `bucket.blob(...).upload_from_string(...)` |
| 8 | instruments-service | `scripts/purge_bitget_phantom_null_rows.py` | **1** | `get_storage_client()` → `bucket.blob(backup_path).upload_from_string(data,...)` |
| 9 | instruments-service | `scripts/purge_deprecated_etf_manifest_rows_2026_05_16.py` | **1** | `get_storage_client()` → `bucket.blob(INDEX_PATH).upload_from_string(...)` |
| 10 | instruments-service | `scripts/purge_pre_launch_manifest_rows.py` | **1** | `get_storage_client()` → `bucket.blob(INDEX_PATH).upload_from_string(...)` |
| 11 | instruments-service | `scripts/purge_prediction_other_group_rows.py` | **1** | `get_storage_client()` → 2 call sites `bucket.blob(...).upload_from_string(...)`, **plus a third, DIFFERENT-yet-still-broken sourcing path**: `all_shards = list(client.list_blobs(BUCKET_NAME, prefix=...))` uses the TOP-LEVEL `GCSStorageClient.list_blobs()` (not `bucket.list_blobs()`), which yields bare `BlobMetadata` dataclasses with zero I/O methods at all — even more broken than the `.blob()` case, a third sourcing variant not anticipated by the 2-path taxonomy above |
| 12 | instruments-service | `scripts/purge_sports_unknown_venue_manifest_rows_2026_08_05.py` | **1** | `get_storage_client()` → `bucket.blob(backup_path).upload_from_string(data,...)` |
| 13 | instruments-service | `scripts/reclassify_kalshi_other_historical.py` | **1** | `get_storage_client()` → 3 call sites, all `bucket.blob(...).upload_from_string(...)` |
| 14 | instruments-service | `scripts/reconcile_attempted_failed_to_captured_2026_05_13.py` | **1** | `get_storage_client()` → `bucket.blob(per_vm_blob_path).upload_from_string(...)` |
| 15 | instruments-service | `scripts/reconcile_correct_legacy_blank_misflips_2026_05_13.py` | **1** | `get_storage_client()` → `bucket.blob(per_vm_blob_path).upload_from_string(...)` |
| 16 | strategy-service | `scripts/run_2yr_config_grid_backtest.py` | **1** | `get_storage_client()` → `bucket.blob(blob_path).upload_from_string(...)` at 2 call sites, no try/except around either — uncaught `AttributeError` crash |
| 17 | market-tick-data-service | `scripts/normalize_instrument_type_casing.py` | 2 | `from google.cloud import storage`; `storage.Client()` → `bucket.blob().upload_from_string(...)` — raw SDK throughout |
| 18 | market-tick-data-service | `scripts/migrate_sports_league_partition.py` | 2 | `from google.cloud import storage`; `storage.Client()` → `.upload_from_string(...)` — raw SDK |
| 19 | market-tick-data-service | `scripts/migrate_cefi_instrument_types.py` | 2 | File also uses `get_storage_client()` elsewhere, but the manifest-write helper locally imports `from google.cloud import storage` and calls `.upload_from_string()` on that raw client — 3 call sites, all raw-SDK |
| 20 | market-tick-data-service | `scripts/reset_source_returned_zero_manifest.py` | 2 | `from google.cloud import storage` with a self-acknowledged `# noqa: TID251` exemption comment; raw SDK, works, flagged violation |
| 21 | market-tick-data-service | `scripts/migrate_underlying_partition.py` | 2 | `from google.cloud import storage`; raw SDK `.upload_from_string(...)` |
| 22 | strategy-service | `scripts/trace_all_carry_archetypes.py` | 2 | Local `from google.cloud import storage as gcs`; `gcs.Client(...)` → `.upload_from_string(...)` (file also legitimately uses `get_storage_client()` elsewhere, not at this call site) |
| 23 | strategy-service | `scripts/position/capture_phase_9_evidence.py` | 2 | `from google.cloud import storage as gcs`; fully raw-SDK file, no UTL usage anywhere |
| 24 | execution-service | `scripts/run_execution_alpha_measurement.py` | 2 | `from google.cloud import storage as gcs`; raw SDK `.upload_from_string(...)` |
| 25 | e2e-testing | `scripts/paper_trading/paper_engine.py` | 2 | `from google.cloud import storage` with a self-documented `# noqa: TID251` POC exemption |
| 26 | e2e-testing | `scripts/defi/run_dr_drill_cutover.py` | 2 | Bare `from google.cloud import storage as gcs_storage`, no noqa/exemption — unflagged violation |
| 27 | client-reporting-api | `scripts/seed_demo_client.py` | 2 | `from google.cloud import storage` inline (docstring: "Uses google-cloud-storage directly"); no `get_storage_client()` anywhere in file |
| 28 | features-service | `features_service/sports/scripts/compute_sfi_progressive_only.py` | 2 | `from google.cloud import storage as gcs_storage` inside a try block, no noqa |
| 29 | unified-trading-pm | `scripts/catalogue/sync-to-mock.py` | 2 | Top-level `from google.cloud import storage` + `storage.retry.DEFAULT_RETRY`, `client: storage.Client` param, no noqa |
| 30 | market-tick-data-service | `scripts/tradfi_manifest_row_loss_restore_2026_07_12.py` | **3** | `get_storage_client()` → `native = getattr(storage, "_client", None)` reaches past the wrapper into the private raw native SDK client → `gcs.bucket(bucket).blob(INDEX_BLOB)` is a real native `Blob` → `.upload_from_string(...)` (needed for `if_generation_match=` CAS semantics the wrapper doesn't expose) works fine — the native-escape-hatch subcase |
| 31 | execution-service | `execution_service/backtest_v2/smart_fill_replay.py` | **3** | `_upload_string()` capability-dispatches: `getattr(client, "upload_bytes", None)` — the real `get_storage_client()` result always has `.upload_bytes` and takes that branch; the `.bucket().blob().upload_from_string()` fallback is reached only for a native/test-fake client that genuinely has the method (the file's own comments document the `GCSBlobHandle` gap and design around it) — no bug in the production path |
| 32 | deployment-api | `tests/unit/test_audit_log_compliance.py` | **3** | Pure `MagicMock()` test double (`_make_gcs_client()`, docstring: "Return a mocked google.cloud.storage.Client-like object") — not real GCS, not `get_storage_client()`-sourced |
| 33 | unified-trading-library | `unified_trading_library/manifest_consolidator.py` | **3** | 3 call sites, all via the native-escape-hatch: `native_client = getattr(client, "_client", None)` → `cast(_GCSClient, native_client).bucket(x).blob(y)` is a genuine native `Blob` — deliberately bypasses the wrapper to reach `if_generation_match` CAS semantics; no `google.cloud` import in this file (Protocol-typed) |
| 34 | unified-trading-library | `unified_trading_library/manifest_writer/_writer_io.py` | **3** | Same native-escape-hatch subcase as `manifest_consolidator.py` — `_write_with_generation_match` → `getattr(client, "_client", None)` → native `Blob.upload_from_string(...)` |
| 35 | unified-trading-library | `unified_trading_library/ledger/run_writer.py` | **3** | `_upload_string()` checks `callable(client.upload_bytes)` FIRST and takes it when present (all real production callers pass `get_storage_client()`, which has it); the `.bucket().blob().upload_from_string()` fallback is dead code in production, reachable only when a caller injects a native/test-fake client without `.upload_bytes` (tests only, per its own docstring) |
| 36 | unified-trading-library | `unified_trading_library/cloud_interface/providers/gcp.py` | **3** | This IS the UCI abstraction layer's own implementation of `upload_bytes()`/`conditional_upload_bytes()` (2 call sites) — the exempt case, not a violation |

**Totals**: **16 Category-1 files (22 call sites)** — all in instruments-service (15 files / 20 call sites) and
strategy-service (1 file / 2 call sites) — genuinely affected, NOT yet fixed, need a scoped follow-up remediation
plan. **13 Category-2 files** — raw `google.cloud.storage` imports, working but a coding-standard violation, lower
urgency, different fix (route through `get_storage_client()`). **7 Category-3 files** — false positives / already
correct (2 in market-tick-data-service + execution-service using deliberate escape-hatch/dispatch patterns, 1 test
double in deployment-api, 4 in UTL's own manifest-writing pipeline — UTL's own code was already aware of and
designed around the `GCSBlobHandle` gap before this incident surfaced it elsewhere).

**Notable finding within instruments-service's 15 files**: most are DATED one-off migration/purge/reconcile scripts
(`_2026_05_13`, `_2026_05_16`, `_2026_05_22`, `_2026_08_05` suffixes) — meaning they were likely already RUN in
production before this bug was ever noticed. If so, their safety-backup-snapshot and/or canonical-index-update
writes (the `.upload_from_string()` call sites found) may have silently no-op'd when those scripts actually ran,
independent of whether the scripts' core purge/migration logic (which may use a different, correct write path)
succeeded. This is a genuine data-correctness question or the underlying rows may need a separate integrity check
before this issue can be considered fully triaged — flagging for the operator, not resolved in this pass.

## Real per-script data-integrity audit (2026-08-18, follow-up session) — Follow-up item 2 RESOLVED

**Top-line verdict: NO CONFIRMED, UNRECOVERABLE DATA LOSS across any of the 15 instruments-service Category-1
files.** Re-verified each file still carries the broken call pattern (all 15 do — none have been fixed yet). Then,
per file, determined already-run vs not-yet-run via git blame + a corpus-wide grep of every plan/issue doc, and —
critically, per this doc's own prior caution that "a script that logged 'backup complete' is not evidence the
backup exists" — did **live, direct GCS reads** (`get_storage_client().list_blobs()`/`.download_as_bytes()`
against the real prod buckets, never trusting a log line) for every file where a plausible risk existed, rather
than inferring from Progress Log prose alone.

**The decisive structural fact**: the bug that makes `.upload_from_string()`/`.download_as_string()` broken on
`get_storage_client()`'s `.blob()`-sourced `GCSBlobHandle` was **introduced into all 15 of these files by a single
commit, `instruments-service@02cc9055` ("refactor(scripts): replace google.cloud/boto3 imports with
get_storage_client across scripts tier"), 2026-08-11 05:11 UTC** — before that commit every one of these 15 files
called the real, fully-functional `google.cloud.storage.Client()` directly (raw SDK — Category-2-shaped, not
buggy). Every one of the 15 files was **created** well before 2026-08-11 (oldest 2026-05-04, newest
`reclassify_kalshi_other_historical.py` at 2026-08-10 — one day before the refactor), and a corpus-wide search
found **zero evidence any of the 15 has been re-run since 2026-08-11**. One-off migration/purge scripts in this
codebase are near-universally run within days of being written (confirmed for every file below with execution
evidence) — so the population that actually executed did so exclusively against the OLD, correct code.

**A second structural fact bounds the worst case even for a hypothetical post-08-11 run**: `GCSBlobHandle` (the
`.blob(path)`-sourced wrapper) implements only `name`/`size`/`exists()`/`download_to_filename()`/
`download_as_bytes()` — it lacks `upload_from_string`, `upload_from_file`, `download_as_text`, `download_as_string`,
AND `.delete()`. In every one of these 15 files, the snapshot/backup write (or, for files with no backup step, the
single overwrite call) is textually and functionally the FIRST broken call the script would reach — it precedes
every delete/overwrite in the function body. None of the 15 files use the `getattr`/`callable()` silent-swallow
guard that caused the original deployment-service bug; they either call the broken method unguarded (crashes
immediately with `AttributeError`, before any destructive step ever executes) or — in
`migrate_available_at_column.py`/`migrate_fixtures_split.py`/`migrate_sports_available_at_column.py` only — wrap
the upload in a broad `except Exception` **per blob**, which soft-fails that one blob (visible in the run's failure
summary + non-zero exit code) without touching the pre-existing object (GCS only replaces an object on write
*success*). Net effect: this bug class, as it manifests in these 15 files, cannot silently destroy pre-existing
data — worst case is "the fix/migration never took effect," not "data vanished."

### Per-script classification

| # | File | Ran? | When / evidence | Pre- or post-08-11 | GCS verification (live, this session) | Verdict |
|---|---|---|---|---|---|---|
| 1 | `dedupe_manifest_schema_drift.py` | **NO** — write path (`--apply`, no `--dry-run`) never executed | 2026-05-06 HANDOVER: "exist but not in orchestrator path"; 2026-05-06 plan: purge marked `DEFERRED-OPERATOR-DECISION`; 2026-06-08 + 2026-07-24 audits: dup issue still OPEN; 2026-08-15 issue doc re-measures the dup rate and attributes the improvement to **writer-side** fixes (`canonicalize_manifest_instrument_type()` 07-27, consolidator TRY_CAST 07-20), not to this script | N/A | N/A (nothing to check — no write attempted) | **NOT YET RUN** — zero risk |
| 2 | `fix_prediction_manifest_and_gcs_2026_05_22.py` | YES | `data_status_coverage_gaps_and_prediction_manifest_fix_2026_05_22.md`: "3940 rows purged... 4931 legacy GCS parquets deleted... instruments-service@0ba4d139" | PRE (working raw-SDK code) | Live read of `instruments-store-pred-prd-…/_index/availability_index.parquet` (32,029 rows): only 30 blank-`data_type` residual rows remain (0.09%), everything else canonical (`prediction_canonical_question_group`/`prediction_market_lifecycle`/`instruments`) | **FALSE ALARM** — fix confirmed reflected in current prod data |
| 3 | `migrate_available_at_column.py` | Shipped/generalized (`8d89e6b`); its own plan states "operational runs deferred to respective asset_group masters" | `available_at_lookahead_bias_completion_2026_05_08.md` Phase 2 | Created pre-08-11; no re-run evidence found | Not conclusively isolated (sampled cefi/tradfi raw-tick parquets outside this script's specific `--data-type` scope, inconclusive either way) | **UNDETERMINED execution history** — but the structural argument above applies regardless: a per-blob `except Exception` catch means a broken run can only ever leave a blob un-migrated, never corrupted/deleted |
| 4 | `migrate_fixtures_split.py` | Shipped (`instruments-service@3f8b6a9`, 2026-06-17); the ONE-OFF historical-backlog split does **not** appear to have completed | `sports_p2_features_history_to_ml_ready_2026_06_27.md` (2026-06-24 evidence): "entity=fixtures_schedule + entity=fixtures_outcomes DO NOT EXIST... only entity=fixtures" | Unclear if ever completed; created pre-08-11 | Live read (2026-08-18) at 6 historical (pre-writer-cutover) dates (2023-06-15→2026-01-01): `entity=fixtures_schedule`/`entity=fixtures_outcomes` = 0 objects at every date; legacy `entity=fixtures` = 1 object at every date (fully intact) | **NOT YET RUN to completion** — source data 100% intact, split never materialized; zero risk |
| 5 | `migrate_local_sfi_to_canonical.py` | YES | `instruments_to_100pct_eod_2026_05_04.plan.md`: "SFI local-dump → canonical \| `bf429c0` \| 14,418 partitions, 36.5 min" | PRE | Not independently re-verified via a fresh GCS read this session (relied on the precise commit+partition-count Progress Log evidence) | **FALSE ALARM** — strong doc evidence, pre-bug |
| 6 | `migrate_sports_available_at_column.py` | YES | `sports_data_available_at_rename_2026_05_07.plan.md` Phase 1 (script) + Phase 2 (operator-run) | PRE | Live read of 5 real 2019 sports parquets (`sports_reference/by_date/day=2019-01-01/.../fixture_events.parquet`, 5 different leagues): **all 5** show `available_at=True`, `data_available_at=False` | **FALSE ALARM** — verified directly in prod data |
| 7 | `purge_bad_prediction_manifest_rows.py` | **NO** — zero execution trace anywhere in the ~600-doc plans/issues corpus outside the two meta-docs about this bug itself; the actual 2026-05-22 prediction purge ran via the sibling `fix_prediction_manifest_and_gcs_2026_05_22.py` instead | Corpus-wide `grep -rn "purge_bad_prediction"` returns only this issue doc + the canonicalization plan | N/A | N/A | **NOT YET RUN** — zero risk (superseded by a different script before ever being invoked) |
| 8 | `purge_bitget_phantom_null_rows.py` | YES | `data_status_coverage_gaps_and_prediction_manifest_fix_2026_05_22.md`: "11 phantom rows purged... instruments-service@0ba4d139... Also purged from prd bucket... backup at `_index/backups/availability_index_pre_bitget_phantom_purge_prd_20260522_125403.parquet`" | PRE | Live read: backup blob **confirmed present** (667,518 bytes) in `instruments-store-cefi-prd-…`; current manifest has **0** phantom (null-status) rows at all 11 target `(venue, date)` pairs | **FALSE ALARM** — doubly verified (backup exists + fix stuck). Side note: the script's own hardcoded `BUCKET_NAME` (no `-prd-` segment) resolves to a bucket that **doesn't exist today** — a separate, pre-existing stale-bucket-name bug (same class documented in `purge_pre_launch_manifest_rows.py`'s own docstring), unrelated to the upload_from_string bug; the real prod purge was done against the correct `-prd-` bucket |
| 9 | `purge_deprecated_etf_manifest_rows_2026_05_16.py` | YES | `plans/epics/tradfi_master.md`: "OPERATIONALLY SHIPPED 2026-05-16 slot 5 (instruments-service@f203ef3): ...deleted 121 rows... CAS via if_generation_match=1778936472461402" | PRE | No backup step in this script by design (direct CAS overwrite) — but ran successfully with working code, so nothing was at risk. Live read confirms the *original* 121-row purge target is gone; however **5,932** deprecated-ticker rows (exact `NYSE`/`BATS`-venue, exact-ticker-segment match) have since re-accumulated, dated through 2026-08-11 | **FALSE ALARM** for THIS script's 2026-05-16 run. **Separate side finding (not this bug)**: an ongoing/different capture path is still writing deprecated-ETF rows going forward — a forward-scope-drift issue, flagged below, out of THIS audit's scope |
| 10 | `purge_pre_launch_manifest_rows.py` | YES | Own docstring: "live-verified 2026-07-15: 612 api_football FIXTURES rows... confirmed via a direct live re-fetch"; precedent `0382454` (2026-05-04 era, `instruments_to_100pct_eod_2026_05_04.plan.md`) | PRE (both eras) | Live read: **0** api_football FIXTURES rows remain in the documented pre-launch window (2017-02-25..2017-09-09) out of 16.85M sports manifest rows | **FALSE ALARM** — verified directly in prod data |
| 11 | `purge_prediction_other_group_rows.py` | YES | `plans/epics/predictions_master.md`: "purged 435 OTHER rows... + 821 from 2 per-VM shards... instr-backfill-pred-20260523 — IS@d76b877f" | PRE | Live read: current pred-prd `underlying=OTHER` share on CQG rows is 6.4% (healthy noise floor, not the un-purged 100%-OTHER state) | **FALSE ALARM** — strong doc evidence + consistent current state |
| 12 | `purge_sports_unknown_venue_manifest_rows_2026_08_05.py` | YES (functionally-equivalent code ran the same day the file was authored, in an interactive session — see `manifest_purge_null_filter_near_miss_and_heavy_io_local_2026_08_05.md`) | Near-miss doc: "Re-ran with the corrected pattern (mask.fill_null(False)... explicit assert actual_delta == matching_count BEFORE the CAS write)... Both purges: delta assertion passed exactly (4 and 1,308 respectively)... 0 remaining matches" | PRE (6 days before the 08-11 refactor) | Live read: **3 backup snapshots** confirmed present in `instruments-store-sports-prd-…/_index/backups/` from 2026-08-05 (`...pre_instruments_store_sports_unknown_venue_purge_...` ×2, `...pre_unknown_purge_sports-venue_...` ×1); current manifest shows **0** matching `(venue=UNKNOWN, empty_confirmed, row_count=0)` rows out of 16.85M | **FALSE ALARM** — doubly verified. Note: the actual backup filenames don't match the *committed* script's hardcoded path pattern — production used an ad-hoc session variant, not this exact file; the committed file itself has never executed, and — because it's idempotent and the condition is already resolved — a future run would exit at "Nothing to purge" *before* ever reaching the broken upload call |
| 13 | `reclassify_kalshi_other_historical.py` | YES | `prediction_capture_incident_remediation_2026_07_06.md`: "DONE 2026-08-10 — instruments-service@d4e5c23d... 162,692 instruments... 69,292 reclassified... Backup: gs://.../  _index/backups/reclassify_kalshi_other/... Post-patch distribution verified on 3 sample dates" | PRE (1 day before the 08-11 refactor) | Live read: **2 backup snapshots** confirmed present (`manifest_pre_reclassify_20260810-090706.parquet`, `manifest_pre_update_20260810-091004.parquet`, 1,251,486 bytes each) | **FALSE ALARM** — doubly verified |
| 14 | `reconcile_attempted_failed_to_captured_2026_05_13.py` | Dry-run confirmed live on HYPERLIQUID 2026-05-13 (`emerging_perp_venue_adapters_broken_2026_05_13.md`); listed elsewhere as one of ~45 "already executed against production" one-offs | 2026-05-13 era | PRE | Purely **additive** — writes only a new per-VM shard parquet, never deletes/overwrites the canonical index or any source data | **FALSE ALARM / no-risk regardless** — even a fully-broken run here has nothing destructive to fail partway through |
| 15 | `reconcile_correct_legacy_blank_misflips_2026_05_13.py` | YES | `defi_legacy_blank_reclassification_2026_05_13.md`: "599,486 rows corrected... Elapsed: 14.1s" + 5/5 sample-verified (no parquet exists at the corrected dates, as expected for pre-launch rows) | PRE | Same additive-only shape as #14 — no delete/overwrite of source data | **FALSE ALARM** — verified via the doc's own 5/5 sample-check |

### Side finding (out of this audit's scope, flagged not fixed): forward-going deprecated-ETF scope drift

Row 9 above surfaced that `market-data-tick-tradfi-prd-…`'s manifest currently carries 5,932 rows matching the
exact deprecated-ETF ticker/venue pattern (`ETHE`/`GBTC`/`BITO`/`FBTC`/`ARKB`/`FETH` at `NYSE`/`NYSE_ARCA`/`BATS`/
`CBOE_BZX`), with dates extending to 2026-08-11 — well after the 2026-05-16 one-off purge's 121-row cleanup. This
means some capture path is still fetching/writing these MVP-excluded tickers going forward, independent of this
bug. Not investigated further here (out of scope for "did the upload_from_string bug lose data") — worth a
separate follow-up if the operator wants the MVP scope reduction actually enforced going forward, not just
purged retroactively once.

## Follow-up (not yet scoped as dispatchable todos — this is the open question, not a decided plan)

1. Scope a remediation plan for the 16 confirmed Category-1 files outside deployment-service (instruments-service
   15 files / 20 call sites + strategy-service 1 file / 2 call sites) — apply the `upload_bytes`/`download_as_bytes`
   fix pattern per file, verify each against its real target bucket. Needs an AO-vs-human dispatch-scope decision
   from the operator before authoring (per this doc's own coordinating-session note) — these are one-off/historical
   scripts in an unfamiliar repo per-file context, not a blind batch-replace.
2. ✅ **DONE (2026-08-18, follow-up session)** — For the instruments-service dated one-off scripts: checked whether
   their backup-snapshot/canonical-index writes already silently failed when originally run in production. See
   "Real per-script data-integrity audit" above — **no confirmed data loss**; 3 of 15 files never actually executed
   their write path (zero risk by construction), 1 more (`migrate_available_at_column.py`) has undetermined
   execution history but is structurally safe regardless, and the remaining 11 are verified (7 via live GCS reads
   this session, 4 via precise, commit-cited Progress Log evidence) to have run successfully with the pre-08-11
   working code.
3. ✅ **DONE (2026-08-18)** — Triage + fix `orchestrator.py`'s `log_event()` kwargs-signature mismatch. See "Two
   findings from the 2026-08-18 follow-up session — both resolved" below.
4. ✅ **DONE (2026-08-18)** — Decide + execute on the missing `deployment-metadata-{project}`/
   `deployment-status-{project}` buckets. See "Two findings from the 2026-08-18 follow-up session — both resolved"
   below — retargeted at the already-existing `deployment-orchestration-{project}` bucket, no new bucket
   provisioned.
5. ✅ **DONE for 6/13, fixed-but-ship-blocked for 5/13, deliberately skipped for 2/13 (2026-08-18, Category-2
   remediation session)** — routed the 13 Category-2 raw-SDK-import files through `get_storage_client()`. See
   "Category-2 remediation results" below for the full per-file breakdown + evidence.

## Two findings from the 2026-08-18 follow-up session — both resolved (2026-08-18, this session)

### Finding 1 — `orchestrator.py`'s `log_event()` kwargs-signature mismatch — FIXED

Confirmed UTL's real `log_event(event_name, severity="INFO", details=None, client_id=None, correlation_id=None)`
signature (`unified_trading_library/events/__init__.py` — the copy `unified_trading_library`'s top-level `__init__.py`
actually re-exports; `events_interface/__init__.py` carries an identical duplicate). All 19 `log_event(...)` call
sites in `orchestrator.py` (`gcs_client` property's 3 exception handlers, `create_daily_plan()`'s
started/completed/3-error-branch events, `propagate_failure()`'s started/completed events, `save_plan()`'s
success + 4 exception-handler events, `load_plan()`'s not_found + 4 exception-handler events) passed free-form
top-level kwargs (`date=`, `asset_group=`, `error_type=`, `stack_trace=`, `level=`, etc.) the real function rejects.
Fixed by moving all structured context into `details={...}`, mirroring the pattern already used correctly by
`deployment_service/data_pipeline_monitors/escalation.py` and `scripts/recovery/relaunch_consolidator.py`
(`log_event(name, severity=..., details={...})`) — no new pattern invented. Exception-handler call sites also now
pass `severity="ERROR"` (previously defaulted to `INFO` even for genuine errors — a valid, always-available
parameter, not new kwarg surface).

Added real (non-mocked) regression test coverage in `test_top_level_orchestrator.py` — a `real_log_event` fixture
configures the actual `unified_trading_library.events` sink in `mode="test"` (console-only, no PubSub/GCS needed)
so a future kwarg-mismatch regression raises a real `TypeError` in CI instead of being silently swallowed by
`patch("deployment_service.orchestrator.log_event")`, which is exactly how the original bug went undetected (every
prior test in the file patches it out). 5 new tests cover all 19 call sites.

**Live-verified outside pytest**: a standalone script called every fixed method (`gcs_client` property's 3 error
branches, `create_daily_plan()`, `propagate_failure()`, `save_plan()` success + 4 error paths, `load_plan()`
not_found + 4 error paths) against the real `unified_trading_library.events.log_event()` (mode="test" sink, not a
mock) — all 19 call sites completed with zero `TypeError`.

Shipped `deployment-service@888865419f`.

### Finding 2 — missing `deployment-metadata-{project}`/`deployment-status-{project}` buckets — RESOLVED BY REUSE

Operator question: don't we already have a bucket for this kind of deployment/logging metadata that these could
reuse instead of provisioning two new empty buckets? Investigated for real rather than guessing:

- Read `monitor.py`'s `DeploymentMonitor`/`VersionRegistry` methods to confirm the data shape: small per-service
  version JSON (`versions/{service}/current.json` + `versions/{service}/history/{timestamp}.json`) and per-shard
  VM-event JSONL logs (`{deployment_id}/shards/{shard_id}/events.jsonl`) — both small-object, path-prefix-keyed
  operational metadata, not high-throughput market data.
- Checked `terraform/modules/shared-infrastructure/gcp/main.tf`: `google_storage_bucket.deployment_orchestration`
  (`deployment-orchestration-{project}`) is the one Terraform-provisioned bucket in this repo's orbit, explicitly
  documented as "state isolated by path prefix, not env name" — i.e. designed from the start to hold multiple
  operational-metadata categories side by side under different key prefixes. `unified-deployment-state-{project}`
  (state.py's code-fallback default) predates Terraform and was never adopted into it
  (`terraform/gcp/bucket_iam_per_tier_sa.tf` line ~520).
- Confirmed `deployment-orchestration-{project}` is not just Terraform-declared but genuinely already live and
  in active use: it's the bucket `orchestrator.py`'s `save_plan()`/`load_plan()` already write to (fixed +
  live-verified in the prior follow-up session), the deployed `deployment-dashboard` Cloud Run service's
  `cloudbuild.yaml` explicitly sets `STATE_BUCKET=deployment-orchestration-{project}` and FUSE-mounts it with the
  comment "API only needs to read/write deployment state", and a **live top-level-prefix listing of the real
  bucket** (delimiter-based, no full walk) showed `cache/`, `deployments/`, `deployments.development/`,
  `deployments.production/`, `locks/` already present — i.e. `vm_monitoring.py`'s `VMMonitoringManager` (via
  `effective_state_bucket`) and `state.py`'s `StateManager` (in at least some invocation contexts) are *already*
  writing real production data into this exact bucket today.
- Collision check against that live listing: `versions/` (new prefix, absent) is safe for `VersionRegistry`/
  `get_service_version()` as-is. The event-log write path originally targeted `deployments/{deployment_id}/shards/
  {shard_id}/events.jsonl` — reusing the bare `deployments/` prefix directly would risk a real (if unlikely) key
  collision with `vm_monitoring.py`'s `deployments/{deployment_id}/{shard_id}/status` already living there (a
  shard_id of literally `"shards"` would collide), so renamed to a new, distinct `deployment-events/` prefix
  instead — confirmed absent from the live bucket, zero collision risk. Fixing this also caught and fixed a latent
  write/read prefix mismatch in `get_events()`'s all-shards path (it still queried the old `deployments/` prefix
  after `_events_blob_path()` moved to `deployment-events/`, which would have silently returned `[]` for that read
  path even though `record_event()` was writing real data).
- IAM/identity: no per-bucket IAM binding exists for `deployment_orchestration` in Terraform (project-level IAM
  governs it); `monitor.py` uses the identical `get_storage_client()` factory as `orchestrator.py`, called from the
  same `deployment_service` package/process context (`live_deployment.py`) — no new IAM grant needed.

**Verdict: reuse, not provision.** Repointed `DeploymentMonitor.get_service_version()`/`_events_bucket_name()` and
`VersionRegistry.bucket_name` at `deployment-orchestration-{project}`. Added unit tests asserting the bucket name
and the `deployment-events/` (not `deployments/`) prefix, plus a regression test guarding that `get_events()`'s
all-shards `list_blobs()` prefix stays in sync with `_events_blob_path()`'s write path. **Live-verified outside
pytest** against the real bucket: pre-check confirmed zero pre-existing objects at the target keys, then
`record_event()`/`get_events()` (both single-shard and all-shards paths)/`get_vm_events()` and
`register_version()`/`get_service_version()`/`get_version_history()` all round-tripped real data correctly, a
post-write prefix listing confirmed every pre-existing prefix (`cache/`, `deployments/`, `deployments.development/`,
`deployments.production/`, `locks/`) was untouched and only the two new `versions/`/`deployment-events/` prefixes
were added, then everything written was deleted and cleanup was confirmed via `blob.exists() == False`.

Shipped `deployment-service@8647635a67`.

## Category-2 remediation results (2026-08-18, dedicated Category-2 session)

Re-verified all 13 Category-2 rows still applied (all did — none had been touched since the fleet-wide triage).
Converted each to `get_storage_client()` + `upload_bytes`/`download_bytes`/`.bucket().blob().download_as_bytes()`
(mirroring `wave_launcher.py`'s proven pattern; SSOT `/codex/05-infrastructure/gcs-object-operations.md`). Verified
the exact call shapes used (top-level `upload_bytes`/`download_bytes`, `.bucket().blob().download_as_bytes()`/
`.exists()`, `.bucket().list_blobs(prefix=)`, top-level `delete_blob()`, `gcs_copy_object()`) with a live
write+read+list+delete+copy round-trip against a disposable scratch prefix in
`config-store-test-central-element-323112` (all 6 patterns PASS) before touching any file, then did per-file
targeted live exercises of the actual converted functions (not just the shape) for `capture_phase_9_evidence.py`'s
4 helpers and `normalize_instrument_type_casing.py`'s hand-merged `_boost_connection_pool()` — both fully green.

**6/13 fixed + shipped**, ruff+basedpyright clean, pre-existing test-suite failures in each repo confirmed
unrelated via `git stash`-and-rerun before shipping:

- `market-tick-data-service/scripts/{normalize_instrument_type_casing,migrate_sports_league_partition,
  reset_source_returned_zero_manifest,migrate_underlying_partition}.py` — **market-tick-data-service@0fcd2389d3**.
  `normalize_instrument_type_casing.py` had drifted substantially upstream (78 commits behind; the file grew a
  backup-before-overwrite step, dedup/collision handling, and a `_boost_connection_pool()` HTTP-pool-size patch
  since this session started editing it) — quickmerge's autostash-pull hit a genuine 3-way conflict, resolved by
  hand: kept upstream's new functionality, converted BOTH the pre-existing violation AND the new backup-write call
  the upstream rewrite had added (`bucket.blob(backup_path).upload_from_string(...)` — same bug class, would have
  crashed under the wrapped client), and fixed `_boost_connection_pool()` to reach the native HTTP session through
  the wrapper's `._client` (mirroring `migrate_prediction_instrument_id_wrap_2026_07_09.py`'s established pattern)
  instead of failing closed with a silent "could not access" warning. Live-verified outside pytest: the pool-boost
  now measurably resizes the real adapter (`pool_maxsize` 64→128) instead of no-op'ing.
  `migrate_sports_league_partition.py`/`migrate_underlying_partition.py` kept their discovery/read/delete calls on
  the native `storage.Client()` deliberately — their `discover_files()` yields real native `Blob` objects via
  `client.list_blobs()`, which the wrapper's top-level `list_blobs()` does NOT (bare `BlobMetadata`, zero I/O
  methods — the exact Category-1 finding #11 shape) — only the flagged write call was converted.
- `e2e-testing/scripts/defi/run_dr_drill_cutover.py` — **e2e-testing@f605c5ce0a**.
- `features-service/features_service/sports/scripts/compute_sfi_progressive_only.py` — **features-service@bac12944a7**.

**5/13 fixed, verified, but SHIP-BLOCKED** by pre-existing, unrelated, repo-wide failures each confirmed via
`git stash` to already fail on HEAD before this session touched anything (code fix itself is done + ruff/
basedpyright clean; left as uncommitted working-tree edits, not lost):

- `strategy-service/scripts/trace_all_carry_archetypes.py` + `scripts/position/capture_phase_9_evidence.py` —
  blocked by `StrategyDomainConfig(extra="forbid")` rejecting real env keys, breaking all 4
  `TestStrategySafeFieldAllowList` tests — already a tracked `- [ ] [AGENT] P3` todo in
  `/plans/active/cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md`; **2026-08-18 tracking pass** confirmed
  the fix is still sitting uncommitted + correct, and annotated that todo with the specific 2 files riding on top
  of it so they aren't lost when the config bug is eventually fixed.
- `execution-service/scripts/run_execution_alpha_measurement.py` — blocked by the same
  `extra_forbidden`/pydantic-settings config-validation failure class (different fields —
  `market_data_gcs_bucket`/`instruments_store_gcs_bucket`/`unified_cloud_services_gcs_bucket` — but identical root
  cause shape to strategy-service's), breaking `test_handler_registry.py`/`test_policy_resolver.py` (11 tests) +
  `test_gcs_live_data_sink.py`/`test_defi_data_loader_coverage.py` (2 more). **2026-08-18: now tracked** —
  `/plans/archive/issues/execution_service_pydantic_extra_forbidden_blocks_gcs_fix_2026_08_18.md`, cross-linked to
  the strategy-service todo above (same failure class, second independent repo, worth a human noticing the
  pattern even though the fix will likely stay per-repo).
- `client-reporting-api/scripts/seed_demo_client.py` — blocked by 4 pre-existing failures in
  `test_invoice_viewing_transitions_analytics.py` (expects HTTP 404, gets a different status) — unrelated to GCS.
  **2026-08-18: now tracked** —
  `/plans/archive/issues/client_reporting_api_invoice_test_failures_block_gcs_fix_2026_08_18.md`, cross-linked to
  the pre-existing (but non-overlapping) `repo_scripts_governance_audit_2026_06_18.md` cloud-discipline todo.
- `unified-trading-pm/scripts/catalogue/sync-to-mock.py` — blocked by the `archive-safety-ratchet` post-gate check:
  10 pre-existing `related:` frontmatter entries across 6 unrelated active plan/issue docs (re-measured
  2026-08-18, was estimated at "8 docs" — actual is 6) cite archived `/plans/archive/...` paths directly instead
  of a codex doc (per the archival ritual step 5). **2026-08-18: assessed, NOT fixed, remains ship-blocked** — see
  "PM-repo blocker: assessed as NOT a simple repoint" below for why this turned out to be more involved than
  originally scoped; **already tracked** at
  `/plans/active/issues/archival_referrer_codex_redirect_bulk_cleanup_2026_08_17.md` +
  `/plans/active/infra_satellite_ao_dispatch_batch19_2026_08_18.md` (the existing 925-citation corpus-wide
  cleanup dispatch) — annotated with the exact 6 docs blocking this specific fix so they get priority.

### PM-repo blocker: assessed as NOT a simple repoint (2026-08-18)

Re-ran the actual gate (`quality-gates.sh --no-fix`, not a hand-picked file list) to get the true current blocking
set: **10 violations across 6 docs**, not the "8 docs" estimated by the prior session (the set of dirty docs in
this shared checkout shifts as other sessions work — re-measure before trusting an old count). Read the checker
source (`scripts/plan-hygiene/check_active_refs_archived_plans.py`): it rejects **any** `/plans/archive/...`
citation, full stop — there is no "point at the archived plan's new/current path" remedy, because every resolving
path under `plans/archive/` fails the same regex. The only valid fix is migrating each archived plan's still-load-
bearing durable fact into a codex SSOT and repointing there (or dropping the citation if nothing is genuinely
load-bearing) — a real per-citation research task, not a mechanical string-swap, and genuinely different across
the 6 docs' 10 citations (6 unrelated topics: a WSFeedConnector rollout-gap audit, a SIT-treadmill incident, 2
CVE remediations, 3 tradfi-databento satellite batches, an adapter-contract-regression ratchet + a lint-sweep
regression, and an MTDS pyright-suppressions contradiction). Separately, all 6 target docs were simultaneously
dirty in the shared checkout with **other sessions' own unrelated uncommitted WIP** at the time (confirmed via
`git status`) — editing and staging them risked entangling this task's fix with work this session doesn't own.
Both factors together (genuine research complexity + live entanglement) meant this did not qualify as the "cheap
and safe" case worth forcing — tracked instead, per the existing corpus-wide cleanup dispatch (already active,
already prioritized toward these 6 docs now).

**2/13 deliberately NOT fixed** — forcing either would have been riskier than leaving the working code alone:

- `market-tick-data-service/scripts/migrate_cefi_instrument_types.py` — `flush_manifest()`'s raw-SDK write uses
  `if_generation_match=` CAS semantics with a re-read-and-retry-unconditional fallback on failure. UTL's
  `conditional_upload_bytes()` exists and could express the happy path, but replicating the exact retry-on-
  precondition-failure-vs-retry-on-any-exception distinction the current code has, with zero existing test
  coverage and this being a `Lifecycle: oneoff` migration script, was judged not worth the correctness risk for a
  "working but non-compliant" fix. Left as-is; noted here as the one Category-2 file still open.
- `e2e-testing/scripts/paper_trading/paper_engine.py` — carries an explicit, deliberate
  `# noqa: TID251 — POC engine uses google-cloud-storage directly (minimal Cloud Run image, no UTL cloud_interface)`
  on both call sites. Converting would pull the full UTL dependency into a Cloud Run image the file's own docstring
  says is deliberately kept minimal (`pandas/numpy/urllib only — no research-code imports`) — against the file's
  stated design intent, not a mechanical swap. Left as-is.

## Tracked follow-ups (added 2026-08-19, `/plan-reconcile security_and_cross_cutting_master` Phase 2.4 zero-checkbox
## sweep — converted from prose so these 2 genuinely-open items are visible to checkbox-based tooling; neither is
## answered by this conversion)

- [ ] [OPERATOR] P1. Decide AO-vs-human dispatch scope for the 16 confirmed Category-1 remediation files
      (instruments-service 15 files/20 call sites + strategy-service 1 file/2 call sites — see the classification
      table above) before authoring a remediation plan. Options: **A) AO-dispatched batch** — bounded, mechanical
      per-file `upload_bytes`/`download_bytes` conversion with a live-verify step per file, same shape as this
      doc's own Category-2 remediation which shipped cleanly across 6 repos **[WORKER REC — this doc's own Category-2
      precedent already proved the mechanical-fix-plus-live-verify pattern works fleet-wide]**. **B) human-authored
      plan** — the original coordinating session's own note flagged these as "one-off/historical scripts in an
      unfamiliar repo per-file context, not a blind batch-replace," which leans toward closer human review per file.
- [ ] [REVIEW] P2. Scope a fix for the other 7 `DomainConfig`-family classes in
      `unified_trading_library/.../domain_configs.py` sharing the identical `extra="forbid"` + `.env`-auto-read
      latent-crash risk that `StrategyDomainConfig` had (`InstrumentDomainConfig`/`ClientDomainConfig`/
      `VenueDomainConfig`/`TickerUniverseConfig`/`RiskDomainConfig`/`AlertRuleDomainConfig`/`RateLimitDomainConfig`/
      `FeatureFlagDomainConfig`) — same `extra="ignore"` fix pattern already shipped for `StrategyDomainConfig`
      (`unified-trading-library@1da1a095d4`) is the likely fix, but each class needs its own confirm-then-fix pass,
      not a blind sweep.

## Progress Log

- **2026-08-18**: Filed while fixing `deployment_service_api_integration_cleanup_2026_08_18.md` todo 2. Root cause
  fixed in `state.py` (shipped `deployment-service@c16b1f1407`), confirmed by direct GCS write+read-back
  verification. Scope of the remaining 3 confirmed files + 60+ untriaged fleet-wide candidates recorded, not yet
  actioned — `assigned_vm: NA` pending operator triage-scope decision.
- **2026-08-18 (same day, follow-up session)**: Part 1 — fixed + live-verified `monitor.py`/`orchestrator.py`/
  `vm_monitoring.py` (shipped `deployment-service@a773a597bb`); confirmed `orchestrator.py`'s `T1Orchestrator`
  shares the exact bug (same `get_storage_client()` source as `state.py`); confirmed `get_deployment_status()` and
  `get_version_history()` were NOT broken (list_blobs-sourced native blobs) and left unchanged; added missing test
  coverage for `record_event()`/`get_events()` (previously zero). Surfaced two new, separate findings not fixed in
  this pass: `orchestrator.py`'s `log_event()` kwargs-signature mismatch (likely crashes in real, non-test-mocked
  execution), and the nonexistent `deployment-metadata-{project}`/`deployment-status-{project}` buckets
  `monitor.py` targets. Part 2 — ran the full fleet-wide triage (36 files outside deployment-service): 16
  Category-1 (genuine bug, NOT fixed — instruments-service 15 files + strategy-service 1 file), 13 Category-2
  (raw-SDK-import coding-standard violation, working), 7 Category-3 (false positive). Replaced the prior "60+
  untriaged" placeholder with this definitive table. `assigned_vm`/`status` left unchanged for the coordinating
  session to decide the AO-vs-human split for the remaining Category-1 remediation.
- **2026-08-18 (same day, third session)**: resolved both findings surfaced in the second session (Follow-up items
  3 and 4) — see "Two findings from the 2026-08-18 follow-up session — both resolved" above for full detail.
  Finding 1 (`orchestrator.py`'s `log_event()` kwargs mismatch): fixed all 19 call sites (`details={...}`,
  mirroring `escalation.py`/`relaunch_consolidator.py`'s existing correct pattern), added real non-mocked
  regression tests, live-verified zero `TypeError` outside pytest. Shipped `deployment-service@888865419f`.
  Finding 2 (missing `deployment-metadata-{project}`/`deployment-status-{project}` buckets): investigated per the
  operator's reuse question — confirmed `deployment-orchestration-{project}` (Terraform-provisioned, already live,
  already holding `orchestrator.py`'s/`vm_monitoring.py`'s data per a live prefix listing) is a genuine semantic
  and IAM fit; repointed `DeploymentMonitor`/`VersionRegistry` at it under new `versions/`/`deployment-events/`
  prefixes (renamed off `deployments/` to avoid a real, if unlikely, collision with `vm_monitoring.py`'s existing
  keys there — also fixing a latent write/read prefix mismatch this uncovered in `get_events()`), live-verified
  write+read-back+zero-collision+cleanup against the real bucket. Shipped `deployment-service@8647635a67`. Neither
  fix required or performed any new bucket provisioning. Follow-up items 1, 2, 5 (fleet-wide Category-1 remediation,
  the pre-existing-data integrity check, Category-2 cleanup) remain open — `status` stays `open` pending those.
- **2026-08-18 (fourth session, data-integrity audit — Follow-up item 2 resolved)**: Re-verified all 15
  instruments-service Category-1 files still carry the broken call pattern (unfixed), then determined per-file
  already-run vs not-yet-run via git blame on instruments-service + a corpus-wide grep of every plan/issue doc,
  and did live GCS reads (`get_storage_client().list_blobs()`/`.download_as_bytes()` against real prod buckets —
  never trusting a script's log output) for every file carrying plausible risk. **Verdict: NO CONFIRMED,
  UNRECOVERABLE DATA LOSS.** Key structural finding: the bug was introduced into all 15 files by ONE commit,
  `instruments-service@02cc9055` (2026-08-11 05:11 UTC) — every file used the working raw `google.cloud.storage`
  SDK before that, and every file was created (and, where run, executed) before that date; zero evidence any of
  the 15 has been re-run since. Per-file: 3 never actually executed their write path at all (`dedupe_manifest_
  schema_drift.py`, `purge_bad_prediction_manifest_rows.py`, and `migrate_fixtures_split.py`'s historical-backlog
  split specifically — source data 100% intact in all 3 cases, confirmed live for the fixtures case); 11 ran
  successfully with the pre-bug working code (7 independently re-verified via a fresh live GCS read this session —
  backups present and/or the fix reflected in current prod data — the other 4 via precise, commit+row-count-cited
  Progress Log evidence); 1 (`migrate_available_at_column.py`) has undetermined per-asset-group execution history
  but is structurally safe regardless (per-blob `except Exception` catch — a broken run can only leave a blob
  un-migrated, never corrupt/delete it). See "Real per-script data-integrity audit" section above for the full
  15-row classification table + evidence. Side finding (flagged, not fixed, out of scope): TradFi manifest
  currently carries 5,932 deprecated-ETF-shaped rows dated through 2026-08-11 — a forward-going capture-scope-drift
  issue unrelated to this bug, separate from the 2026-05-16 one-off purge (which is confirmed to have worked
  correctly at the time). No code changed this session — audit + doc update only. Follow-up items 1, 5 remain
  open.
- **2026-08-18 (fifth session — Category-2 remediation)** [dedup note: this entry replaces a verbatim-duplicated
  copy of the "third session" bullet that was found sitting here — same content already logged above, removed,
  nothing lost]: see "Category-2 remediation results" above for full detail. Fixed all 13 Category-2 files;
  live-verified the 6 shared call-shape patterns against a scratch bucket before touching any file, plus targeted
  live exercises of the two riskiest converted files. Shipped 6/13: `market-tick-data-service@0fcd2389d3` (4
  files — one, `normalize_instrument_type_casing.py`, required hand-resolving a genuine 3-way merge conflict
  against 78 commits of upstream drift, live-verified after), `e2e-testing@f605c5ce0a` (1 file),
  `features-service@bac12944a7` (1 file). Fixed-but-ship-blocked 5/13 on pre-existing, unrelated, repo-wide red
  (strategy-service ×2, execution-service ×1, client-reporting-api ×1, unified-trading-pm ×1) — each confirmed
  pre-existing via `git stash`+rerun, left as verified uncommitted working-tree edits. Deliberately skipped 2/13
  (`migrate_cefi_instrument_types.py`'s CAS-semantics write, `paper_engine.py`'s deliberate minimal-image noqa
  exemption) — forcing either was judged riskier than leaving the working, non-compliant code alone. Follow-up
  item 1 (fleet-wide Category-1 remediation) and the execution-service `extra_forbidden` config-validation
  regression (newly surfaced, not yet tracked anywhere) remain open — `status` stays `open`.
- **2026-08-18 (sixth session — tracking pass on the 5 fixed-but-ship-blocked files)**: re-verified all 5 fixes
  still sitting correctly uncommitted in their 4 repos (`git status`/`git diff` each — no content lost or drifted
  since the prior session). strategy-service's blocker was already tracked (batch15) but didn't mention the 2
  riding GCS fixes — added that note. execution-service's `extra_forbidden` failure and client-reporting-api's 4
  invoice-test failures were confirmed NOT tracked anywhere — filed
  `/plans/archive/issues/execution_service_pydantic_extra_forbidden_blocks_gcs_fix_2026_08_18.md` and
  `/plans/archive/issues/client_reporting_api_invoice_test_failures_block_gcs_fix_2026_08_18.md` respectively (both
  cross-linked back here and to each other where relevant). The PM-repo `sync-to-mock.py` blocker was assessed for
  a direct fix per this session's own instructions (attempt it if genuinely a simple repoint) — re-running the
  real gate found 10 violations across 6 docs (not the 8 estimated), read the checker source and confirmed the
  only valid remedy is per-citation codex-migration research (not a mechanical path-swap), and found all 6 target
  docs entangled with other sessions' live unrelated WIP — concluded this was NOT the simple case, and instead
  annotated the existing corpus-wide cleanup dispatch
  (`/plans/active/issues/archival_referrer_codex_redirect_bulk_cleanup_2026_08_17.md` +
  `/plans/active/infra_satellite_ao_dispatch_batch19_2026_08_18.md`) with the exact 6 blocking docs so that work
  gets prioritized there instead of being forced here. **No code shipped this session** — all 5 fixes remain
  uncommitted working-tree edits, now with every blocker either tracked-with-context or (strategy-service) already
  tracked-and-annotated. `status` stays `open`.
- **2026-08-18 (seventh session, resolution pass on the 5 fixed-but-ship-blocked files)**: **4 of 5 now resolved
  and shipped.** The prior sessions' uncommitted edits no longer existed in any of the 11 local slot checkouts
  (`git status`/`git diff`/`git stash list` all clean) — redone from scratch, same conversions as originally
  described. `client-reporting-api/scripts/seed_demo_client.py`: its blocker (4 invoice-viewing test failures)
  turned out to already be gone — `quality-gates.sh --test` came back fully green (667 passed, 0 failed), no commit
  history explains a fix, most likely upstream drift in this shared multi-session checkout; redone + shipped
  `client-reporting-api@0e54aab310`. `strategy-service`'s 2 files + `execution-service`'s 1 file: root cause
  diagnosed for real — see
  `/plans/active/cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md`'s StrategyDomainConfig todo and
  `/plans/archive/issues/execution_service_pydantic_extra_forbidden_blocks_gcs_fix_2026_08_18.md` for full detail —
  `BaseConfig` subclasses (`pydantic_settings.BaseSettings`) auto-read `.env` on every construction regardless of
  code-level kwargs; narrow domain-config schemas with inherited `extra="forbid"` reject any of `.env`'s many
  unrelated keys, confirmed via direct repro (`cp .env.example .env` + rerun: 32 distinct violations for
  execution-service's config, not just the 3 fields this doc's summary named). Fixed via `extra="ignore"`,
  mirroring existing precedent elsewhere in the codebase. Shipped `unified-trading-library@1da1a095d4` (the actual
  fix location — `StrategyDomainConfig` lives in UTL, not strategy-service), `strategy-service@20e9602e96` (the 2
  riding GCS files), `execution-service@3448247dba` (pydantic fix + riding GCS file together). **Only
  `unified-trading-pm/scripts/catalogue/sync-to-mock.py` remains ship-blocked** — unchanged, still routed through
  the existing corpus-wide cleanup dispatch per the sixth session's assessment. **New finding, not fixed**: the
  UTL fix resolves only 2 of 9 `DomainConfig`-family classes in `domain_configs.py` sharing the identical
  architectural shape (narrow schema + inherited `.env`-reading + `extra="forbid"`) — the other 7
  (`InstrumentDomainConfig`/`ClientDomainConfig`/`VenueDomainConfig`/`TickerUniverseConfig`/`RiskDomainConfig`/
  `AlertRuleDomainConfig`/`RateLimitDomainConfig`/`FeatureFlagDomainConfig`) carry the same latent
  crash-on-real-`.env` risk, unfixed — flagged for a follow-up decision, not scoped as a todo here.
- **context-scout 2026-08-20**: refreshed context_scope (5 entries)
