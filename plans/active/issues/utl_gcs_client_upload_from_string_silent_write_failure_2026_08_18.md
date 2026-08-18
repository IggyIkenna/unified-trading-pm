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
last_updated: 2026-08-18
parent_epic: infrastructure_master
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
    deployment_service/deployment/state.py,
    deployment_service/scripts/wave_launcher.py,
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

## Follow-up (not yet scoped as dispatchable todos — this is the open question, not a decided plan)

1. Scope a remediation plan for the 16 confirmed Category-1 files outside deployment-service (instruments-service
   15 files / 20 call sites + strategy-service 1 file / 2 call sites) — apply the `upload_bytes`/`download_as_bytes`
   fix pattern per file, verify each against its real target bucket. Needs an AO-vs-human dispatch-scope decision
   from the operator before authoring (per this doc's own coordinating-session note) — these are one-off/historical
   scripts in an unfamiliar repo per-file context, not a blind batch-replace.
2. For the instruments-service dated one-off scripts specifically: check whether their backup-snapshot/
   canonical-index writes already silently failed when originally run in production, and whether that leaves any
   manifest/GCS state inconsistent — a data-correctness check, separate from (and prerequisite to) just fixing the
   method names going forward.
3. ✅ **DONE (2026-08-18)** — Triage + fix `orchestrator.py`'s `log_event()` kwargs-signature mismatch. See "Two
   findings from the 2026-08-18 follow-up session — both resolved" below.
4. ✅ **DONE (2026-08-18)** — Decide + execute on the missing `deployment-metadata-{project}`/
   `deployment-status-{project}` buckets. See "Two findings from the 2026-08-18 follow-up session — both resolved"
   below — retargeted at the already-existing `deployment-orchestration-{project}` bucket, no new bucket
   provisioned.
5. Consider routing the 13 Category-2 raw-SDK-import files through `get_storage_client()` for coding-standard
   compliance — lower urgency (not silently broken today), batch with other coding-standard cleanup rather than a
   dedicated pass.

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
