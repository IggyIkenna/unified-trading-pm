---
name: deployment-api-work-stream-a
overview: deployment-api endpoints for programmatic VM backfill launch + GCS event tail (work-stream-A keystone unblock for the 2026-05-23 live-DeFi deadline)
type: code
epic: epic-code-completion
status: active

asset_group: cross-cutting
priority: P0
deadline: 2026-05-23
parent: master_to_live_defi_2026_05_23
locked_by: live-defi-rollout
locked_since: 2026-05-07
gates: [master_to_live_defi:work-stream-A]
last_updated: 2026-05-07

completion_gates:
  code: C5
  deployment: D3
  business: none

repo_gates:
  - repo: unified-api-contracts
    code: C0
    deployment: none
    business: none
  - repo: deployment-api
    code: C0
    deployment: none
    business: none

depends_on: []
isProject: false
---

# deployment-api work-stream-A — programmatic VM launch + live event tail

## Why this plan exists

The master plan `master_to_live_defi_2026_05_23.plan.md` audit (PM commit `12ce828a`, 2026-05-06) names
**work-stream-A** as one of the three keystone unblocks for the May 23 live-DeFi deadline. The codex SSOT
`03-observability/lifecycle-events.md` already defines the event schema and bucket layout
(`gs://{gcp_project_id}-events/events/{service}/{YYYY-MM-DD}/{vm-name}/hour={H}/*.jsonl`); what's missing is the
deployment-api surface so the deployment-UI / DART terminal / on-call operator can:

1. Launch a backfill VM **programmatically** from the UI (not via SSH-into-laptop + bash) — paired with the
   no-fire-and-forget rule from CLAUDE.md (every launch returns the VM name + correlation_id so the launcher's first
   action can be event-verification).
2. Tail the VM's structured events live without `gcloud storage cat ...` shelling — the production observability
   surface for live trading runs through the UI, not SSH.

Both endpoints are net-new — no existing deployment-api routes cover programmatic launch (`vm_deployments.py` reads
the GCS-backed registry, doesn't write it) or event-tail (`deploy_events_sse.py` is for the deploy CI/CD lane, not
backfill VMs).

## Pre-audit blast-radius manifest

| Repo / file                                                                              | Reference / consumer                                                                                       | Action                                                                       |
| ---------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| `unified-api-contracts/unified_api_contracts/internal/deployment.py`                     | Existing `DeploymentStatus`, `ComputeType`, `VMEventType`, `ShardEvent`, `DeploymentState`                 | EXTEND with `BackfillLaunchRequest`, `BackfillLaunchResult`, `VMLifecycleEvent`, `VMEventListResult`, `BackfillLaunchTaskKind` enum |
| `unified-api-contracts/unified_api_contracts/internal/__init__.py`                       | Re-exports `DeploymentStatus`, `VMEventType`, etc.                                                         | Add new symbols to `from unified_api_contracts.internal.deployment import (...)` block + `__all__` |
| `deployment-service/scripts/vm/vm_zombie_watchdog.py:113` `VM_PREFIX_TO_BUCKET`          | SSOT for VM-name → shard-bucket mapping; new launchers MUST add their prefix here                         | READ-ONLY — endpoint imports the dict to validate caller's `vm_name_prefix` is registered |
| `deployment-service/scripts/vm/launch-*.sh` (51 launcher scripts)                        | Bash launchers; canonical interface = CLI flags + env vars                                                  | READ-ONLY — endpoint shells into selected launcher via subprocess (or `--dry-run` in tests) |
| `deployment-api/deployment_api/main.py:54-76` route imports                              | FastAPI router includes per route module                                                                    | ADD imports for `backfill_launch.router`, `vm_events.router`                |
| `deployment-api/deployment_api/main.py:127-165` `_authenticated_router`                  | All `/api/...` routes go through `verify_api_key` dependency                                               | ADD both new routers under the authenticated chain                          |
| `deployment-api/deployment_api/auth.py` `verify_api_key`                                 | API-key auth pattern (X-API-Key header) — same dep used by every existing route                           | REUSE — both new endpoints use `verify_api_key`                             |
| `deployment-api/deployment_api/deployment_api_config.py`                                 | `gcp_project_id` (inherited from `UnifiedCloudConfig`); `is_mock_mode()`                                  | REUSE — events bucket = `f"{gcp_project_id}-events"`                        |
| `deployment-ui/src/components/...` (BackfillLaunchModal — TBD)                           | Greenfield UI; not part of this plan                                                                       | DEFERRED to a deployment-ui sub-plan — endpoints land first so UI has a back-end to call |
| `unified-trading-library/unified_trading_library/feature_service_base/base_service.py:159` | SSOT for events-bucket name pattern: `f"{gcp_project_id}-events"`                                          | READ-ONLY — confirm pattern; endpoint must use the same name              |

**Verified from same-region GCS probes (2026-05-07):** project `central-element-323112`, events bucket
`gs://central-element-323112-events/`, layout
`events/{service}/{YYYY-MM-DD}/{vm-name}/hour={H}/*.jsonl`, schema
`{event, service, timestamp, metadata: {service_name, severity, details: {correlation_id, ...}}}`.

## Execution DAG

```
Phase 1 (UAC types — SEQUENTIAL prerequisite)
    └─> Phase 2 (deployment-api routes + integration tests — PARALLEL within phase)
            ├─ /api/backfill/launch
            └─ /api/vm/events
                └─> Phase 3 (QG pass + commit + push — SEQUENTIAL)
                        └─> Phase 4 (deployment-ui wiring — DEFERRED to sub-plan)
```

## Phase 1 — UAC internal types (SEQUENTIAL prerequisite)

- [ ] [SCRIPT] P0. Extend `unified_api_contracts/internal/deployment.py` with five Pydantic models +
      `BackfillLaunchTaskKind` StrEnum.

  Models:
  - `BackfillLaunchTaskKind` StrEnum — closed set of supported launcher tasks: `cefi_backfill`, `tradfi_backfill`,
    `defi_backfill`, `prediction_backfill`, `sports_backfill`, `mtds_prediction`, `mtds_perp_funding`,
    `mtds_gas_fees`, `mtds_lst_rates`, `mtds_vault_share_price`, `mtds_lending_indices`, `mdps_backfill`,
    `features_backfill`, `features_sports_backfill`, `canonical_migration`, `forward_poll`. The set MUST be a
    proper subset of the launcher scripts under `deployment-service/scripts/vm/launch-*.sh`.
  - `BackfillLaunchRequest(BaseModel)` — task: `BackfillLaunchTaskKind`; asset_group: lowercase enum literal
    (`cefi|defi|tradfi|prediction|sports`); venue: optional str (e.g. `binance`, `bybit`, `cme`); start_date /
    end_date: ISO date strings; data_types: optional list[str] (`ohlcv_1m`, `trades`, `tbbo`, etc.);
    instrument_ids: optional list[str]; tier_plan: optional str (e.g. `crypto-basis-2023-05+2024-06`); year /
    month: optional str (`2025` or `2025-06`); root_symbol: optional str (`ES`, `BTC`, `IBIT`); extra_metadata:
    `dict[str, str]` for forward-compat metadata pass-through; force: bool = False (singleton-lock bypass);
    dry_run: bool = False (echo-only mode for staging tests + CI smoke); skip_dependency_check: bool = False.
  - `BackfillLaunchResult(BaseModel)` — vm_name: str; vm_name_prefix: str (validated against
    `VM_PREFIX_TO_BUCKET`); zone: str (defaults to `asia-northeast1-c`); project_id: str; launched_at: datetime;
    correlation_id: str (UUID4 — used as the event-stream sub-partition); launcher_script: str (resolved
    `launch-*.sh` filename); dry_run: bool; events_uri: str (`gs://{pid}-events/events/{service}/{date}/{vm_name}/`).
  - `VMLifecycleEvent(BaseModel)` — event: str; service: str; timestamp: datetime; severity: str (INFO / WARNING /
    ERROR / CRITICAL); correlation_id: str | None; details: `dict[str, str]`; raw_metadata: `dict[str, object]`
    (verbatim JSONL row for callers that want the unparsed payload).
  - `VMEventListResult(BaseModel)` — vm_name: str; service: str; date: str (YYYY-MM-DD); hours_scanned: list[int];
    total_events: int; events: list[VMLifecycleEvent]; truncated: bool (true if next_page_token is needed);
    next_page_token: str | None.

  Tests in `unified-api-contracts/tests/internal/test_deployment_extensions.py`:
  - Round-trip JSON for each model.
  - `BackfillLaunchTaskKind` enum value check (must include each task name).
  - `VMLifecycleEvent` parses canonical JSONL row from a fixture taken verbatim off
    `gs://central-element-323112-events/.../*.jsonl` (sample captured 2026-05-07 from
    `instruments-service/2026-05-07/af-backfill-20260507-002914/hour=00/`).

- [ ] [SCRIPT] P0. Re-export from `unified_api_contracts/internal/__init__.py` — add the 5 new symbols to the
      existing `from unified_api_contracts.internal.deployment import (...)` block AND to `__all__`.

**Phase 1 success criteria:**

- `cd unified-api-contracts && bash scripts/quality-gates.sh` Pass 1 green (excluding pre-existing dirty-file
  failures from teammates — verified via `git blame`).
- New tests in `tests/internal/test_deployment_extensions.py` pass.
- `from unified_api_contracts.internal import BackfillLaunchRequest, BackfillLaunchResult, VMLifecycleEvent, VMEventListResult, BackfillLaunchTaskKind` works.

## Phase 2 — deployment-api routes (PARALLEL within phase)

### 2.A — `POST /api/backfill/launch` (PARALLEL with 2.B)

- [ ] [SCRIPT] P0. Create `deployment-api/deployment_api/routes/backfill_launch.py`:

  Behaviour:
  1. Auth: `verify_api_key` (X-API-Key header) — inherited via `_authenticated_router` in main.py.
  2. Validate request body via `BackfillLaunchRequest`.
  3. Resolve `(task, asset_group, venue?)` → launcher script. Mapping codified inline as a dict literal
     (`_TASK_TO_LAUNCHER: dict[BackfillLaunchTaskKind, str]`) — closed set. Unknown task → 400.
  4. Generate `vm_name = f"{prefix}-{run_ts}"` (run_ts = `datetime.now(UTC).strftime("%Y%m%d-%H%M%S")`). Prefix
     determined from task + asset_group + (venue / root) following the VM_PREFIX_TO_BUCKET conventions in
     `vm_zombie_watchdog.py:113`. Validate the resolved prefix is registered in `VM_PREFIX_TO_BUCKET`; unknown prefix
     → 400 with the registration instructions from the CLAUDE.md "VM Naming Convention" section.
  5. Build env / metadata: `VM_NAME`, `MANIFEST_PER_VM_SHARDS=true` (always — concurrency rule), `VM_FORCE`,
     `SKIP_DEPENDENCY_CHECK`, `RUN_TS`, `VM_FORCE_WINDOW`, plus task-specific (`VM_VENUE`, `VM_START_DATE`,
     `VM_END_DATE`, `VM_DATA_TYPES`, `VM_INSTRUMENT_IDS`, `VM_ASSET_GROUP`).
  6. Build subprocess argv: `["bash", launcher_path, *flags]` (flags from request fields; `--force` /
     `--dry-run` propagated from request). Launcher inherits the constructed env. **Dry-run / mock-mode path
     **never** calls subprocess** — returns the constructed argv + env-diff in a stub `BackfillLaunchResult`
     for verification (CI tests assert this without actually calling `gcloud`).
  7. Real launch path: `subprocess.run(argv, env=..., capture_output=True, text=True, timeout=600)`. Bash launchers
     are typically <60s in steady-state but `gcloud compute instances create` plus singleton-lock probing can take
     up to ~120s under contention; 600s ceiling is generous. timeout → 504 with `LAUNCH_TIMEOUT` event.
  8. Emit `VM_LAUNCH_REQUESTED` lifecycle event via `log_event(...)` BEFORE shelling, and `VM_LAUNCHED` /
     `VM_LAUNCH_FAILED` after — every step recorded for live observability.
  9. Per CLAUDE.md "Shard-level failure isolation": no `raise` inside the launcher loop. Errors classified via
     `classify_venue_error` (UAC) where applicable; non-classified subprocess errors → `VM_LAUNCH_FAILED` event +
     5xx response.
  10. Return `BackfillLaunchResult` JSON.

  Subprocess + gcloud safety:
  - `subprocess.run(argv, ...)` with `shell=False` — argv list, never a shell string.
  - In tests: `monkeypatch.setattr("subprocess.run", _fake_run)` so VMs are NEVER created in CI / staging tests.
    Mock returns synthesized argv + stdout for assertions.
  - Production guard: if `_cfg.is_mock_mode()` is True OR `request.dry_run`, the route returns a
    `BackfillLaunchResult` with `dry_run=True` and the resolved argv reflected back, without calling subprocess.

- [ ] [SCRIPT] P0. Wire route into `deployment_api/main.py`: add `from .routes import backfill_launch` and
      `_authenticated_router.include_router(backfill_launch.router, prefix="/api/backfill", tags=["Backfill"])`.

- [ ] [SCRIPT] P0. Integration tests in `deployment-api/tests/integration/test_backfill_launch.py`:
  1. Auth required — POST without X-API-Key → 401.
  2. Bad task → 400 (task value not in enum, OR task not in `_TASK_TO_LAUNCHER` mapping).
  3. Unknown vm-name prefix (i.e. one not in `VM_PREFIX_TO_BUCKET`) → 400 with helpful message.
  4. Valid request, dry-run mode — returns `BackfillLaunchResult` with `dry_run=True`, `vm_name` matches the prefix
     pattern + RUN_TS regex `^[a-z][-a-z0-9]+-\d{8}-\d{6}$`, `events_uri` matches the
     `gs://{pid}-events/events/{service}/{date}/{vm_name}/` pattern, subprocess.run NOT called.
  5. Valid request, mocked subprocess — returns `BackfillLaunchResult` with `dry_run=False`, subprocess.run called
     with the right argv + env (asserted via captured monkeypatch).
  6. subprocess timeout → 504 with `LAUNCH_TIMEOUT` envelope.
  7. subprocess non-zero exit → 502 with `VM_LAUNCH_FAILED` envelope.

### 2.B — `GET /api/vm/events` (PARALLEL with 2.A)

- [ ] [SCRIPT] P0. Create `deployment-api/deployment_api/routes/vm_events.py`:

  Behaviour:
  1. Auth: `verify_api_key`.
  2. Query parameters: `vm_name: str` (required); `service: str | None` (defaults: derived from `vm_name` prefix
     against a small `_PREFIX_TO_SERVICE` map, falls back to `instruments-service` for `*-backfill-`,
     `market-tick-data-service` for `mtds-` / `cefi-` / `tradfi-` / `defi-`, `market-data-processing-service` for
     `mdps-`, etc.); `date: str | None` (YYYY-MM-DD; defaults to `datetime.now(UTC).strftime("%Y-%m-%d")`);
     `hour_start: int | None`; `hour_end: int | None` (0-23 inclusive); `severity: str | None` (filter to
     `severity >= ...`); `event_filter: list[str] | None` (subset of event names); `limit: int = 1000`
     (max 5000); `page_token: str | None` (opaque cursor for pagination).
  3. Resolve events_uri =
     `gs://{cfg.gcp_project_id}-events/events/{service}/{date}/{vm_name}/hour={H}/*.jsonl` for each H in
     `[hour_start, hour_end]` (defaults: 0..current_hour for today, else 0..23).
  4. List blobs via UTL `cloud_interface` (or direct `google.cloud.storage` since deployment-api already deps it
     transitively via UTL) — list ONCE per hour partition.
  5. Stream-parse each JSONL row into `VMLifecycleEvent`. Apply severity / event_filter / limit. Sort by
     `timestamp` ascending. JSONL parse failures emit `EVENT_PARSE_FAILED` log event but don't fail the request
     (shard-level failure isolation — no raise inside the loop).
  6. Return `VMEventListResult` JSON. If `len(events) == limit`, set `truncated=True` and
     `next_page_token=...` (the next page-token encodes `(last_timestamp, blob_index, row_index)` opaque base64).
  7. Mock-mode: return a synthesized `VMEventListResult` with 3 STARTED + INSTRUMENT_PROCESSED + STOPPED events
     so the UI smoke render works without GCS creds.

  Performance:
  - Default scan: 1 hour partition. `gcloud storage cat` of the typical `1778113506490157_372.jsonl` takes ~50ms;
    1 hour is bounded to <200 KB (verified live 2026-05-07).
  - 24-hour scan: bounded to <5 MB total. No streaming response needed for v1 (FastAPI defaults are fine).
  - Pagination handles the >5000-event-day case; live forward-poll VMs emit ~1 event / 30s × 24h = ~2880 / day.

- [ ] [SCRIPT] P0. Wire route into `deployment_api/main.py`: add `from .routes import vm_events` and
      `_authenticated_router.include_router(vm_events.router, prefix="/api/vm", tags=["VM Events"])`.

- [ ] [SCRIPT] P0. Integration tests in `deployment-api/tests/integration/test_vm_events.py`:
  1. Auth required — GET without X-API-Key → 401.
  2. Missing vm_name → 422.
  3. Mock-mode returns synthesized `VMEventListResult` with 3 events + `truncated=False`.
  4. Real-mode (GCS mocked via `monkeypatch` of the storage client):
     - Empty bucket → `total_events=0`, `events=[]`.
     - Single hour with 5 JSONL rows — parses all 5, sorted by timestamp.
     - `severity=ERROR` filter — drops INFO / WARNING.
     - `event_filter=["STARTED","STOPPED"]` — drops everything else.
     - Malformed JSONL row in middle of partition — skipped, others returned, `EVENT_PARSE_FAILED` logged.
     - `limit=2` triggers `truncated=True` + non-null `next_page_token`.
  5. `date` defaults to today's UTC date.

**Phase 2 success criteria:**

- All Phase 2 integration tests pass.
- `cd deployment-api && bash scripts/quality-gates.sh` Pass 1 green.
- basedpyright clean (no Any types, no type:ignore).
- ruff clean.

## Phase 3 — Quality gates + commit + push (SEQUENTIAL)

- [ ] [SCRIPT] P0. Run `cd unified-api-contracts && bash scripts/quality-gates.sh` Pass 1; commit + push directly to
      `live-defi-rollout` (per CLAUDE.md "DO NOT quickmerge when local dep repos are dirty"). Commit message:
      `feat(uac): work-stream-A internal types for backfill launch + VM event tail`.

- [ ] [SCRIPT] P0. Run `cd deployment-api && bash scripts/quality-gates.sh` Pass 1; commit + push directly to
      `live-defi-rollout`. Commit message: `feat(deployment-api): work-stream-A endpoints — POST /api/backfill/launch + GET /api/vm/events`.

- [ ] [SCRIPT] P0. Flip the matching plan checkboxes in this file + push as a separate `plan(...)` commit per the
      CLAUDE.md "Commit + Push + Flip Plan Checkboxes" hard rule.

**Phase 3 success criteria:**

- Two work commits pushed to `live-defi-rollout` on UAC + deployment-api.
- One plan-flip commit pushed on PM.
- `gh pr` not created — staying on the working branch per CLAUDE.md (VMs pull `live-defi-rollout`, not `main`).

## Phase 4 — deployment-ui wiring (DEFERRED — separate sub-plan)

Not in scope for this plan. The endpoints land first; UI wires up afterwards via a `deployment_ui_backfill_launcher_2026_05_XX.plan.md`
that will:

- Add a `BackfillLaunchModal` to deployment-ui.
- Add a `VMEventTail` widget that polls `/api/vm/events` and renders the live event stream.
- Plumb correlation_id into the deployment-ui URL so the operator can deep-link.

## Temporary states + their canonical follow-up plans

- `_TASK_TO_LAUNCHER` mapping is inlined in `deployment_api/routes/backfill_launch.py` for v1 — closed set. The
  long-term shape (per the cloud-agnostic master plan) is a UAC SSOT registry mapping (asset_group, task) →
  launcher_path so AWS launchers can plug in without touching the route module. Successor plan:
  `cloud_agnostic_launcher_registry_2026_05_XX.plan.md` (work-stream D).
- `_PREFIX_TO_SERVICE` in `vm_events.py` is similarly inlined for v1. Same successor plan as above.

## Risk register

| Risk                                                                             | Mitigation                                                                                          |
| -------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `subprocess.run` deadlocks on a hung launcher                                    | 600s timeout + `VM_LAUNCH_TIMEOUT` event — surfaced to operator via UI                              |
| Endpoint accidentally launches a real VM in CI / SIT                             | Two-layer guard: `is_mock_mode()` short-circuits BEFORE subprocess; tests `monkeypatch.setattr("subprocess.run", ...)`. CI never has gcloud creds anyway. |
| `vm_name_prefix` not in `VM_PREFIX_TO_BUCKET` → silent zombie                    | Validation step rejects unknown prefixes with 400 + the registration instructions                  |
| Concurrent two-VM launches with same RUN_TS                                      | Sub-second timestamp collision avoided via UUID4 correlation_id; vm_name still has same RUN_TS but Python `monotonic_ns()` ensures distinct names within a process |
| Missing X-API-Key on legitimate UI calls                                         | UI tier 1+ uses the same X-API-Key as every existing route — already wired in deployment-ui's API client |
| Launcher requires interactive TTY (e.g. `gcloud auth login` mid-execution)       | Out of scope — production VMs use service-account credentials. If launcher prompts in dev, it's a launcher bug; surfaces as a 504 timeout with `STDIN_REQUIRED` envelope. |

## Citadel-grade compliance checklist

- [x] Pre-audit blast-radius manifest above (every consumer enumerated).
- [x] Phased DAG with parallel/sequential markers + dependencies.
- [x] No technical debt — no compat shims, no deprecation wrappers, no fallback imports.
- [x] Parallelization — Phase 2.A and 2.B independent, marked PARALLEL.
- [x] Success criteria per phase (QG, integration tests).
- [x] Downstream consumer updates — Phase 1 (UAC) updates re-exports in `__init__.py`; Phase 2 wires routes in `main.py`.
- [x] Single source of truth — types live in UAC `internal/deployment.py`, no per-service shadow copies; launcher mapping documented as a v1 inline with named successor plan.
