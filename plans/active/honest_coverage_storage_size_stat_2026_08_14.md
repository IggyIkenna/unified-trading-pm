---
doc_type: plan
title: Honest Coverage rollup — add per-asset-group GCS storage-size summary stat
summary: >-
  Add a new "storage size (TB)" summary stat to the Honest Coverage v2 rollup, sourced from GCS bucket size via Cloud
  Monitoring's `storage.googleapis.com/storage/total_bytes` metric (per-asset-group buckets, per
  bucket-isolation-model.md — no prefix filtering needed). Requires a new UTL/UAC-mediated Cloud Monitoring client (none
  exists in the codebase today — unified-api-contracts only has unused pydantic schemas), a compute-side field in
  instruments-service's coverage harness, a deployment-api passthrough, and a deployment-ui render. Triggered by an
  operator ad-hoc request to see sports' measured 0.43 TB (IS 0.061 TB + MTDS 0.369 TB, measured 2026-08-14) surfaced
  inside the existing per-AG summary tiles instead of a one-off manual query.
status: active
nature: design
asset_group: [meta]
stage: [data]
repos: [instruments-service, deployment-api, deployment-ui, unified-trading-library, unified-api-contracts]
scope: [engineer]
tags: [honest-coverage, storage, cloud-monitoring, gcs, summary-stats, data-status]
related:
  [
    /codex/02-data/honest-coverage-model.md,
    /codex/05-infrastructure/bucket-isolation-model.md,
    /codex/05-infrastructure/gcs-object-operations.md,
  ]
created: "2026-08-14"
last_updated: "2026-08-14"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: design
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.8
locked_by:
locked_since:
context_scope:
  [
    /codex/02-data/honest-coverage-model.md,
    /codex/05-infrastructure/bucket-isolation-model.md,
    instruments-service/scripts/measure_honest_coverage.py,
    deployment-api/deployment_api/services/data_status/coverage_metrics.py,
    deployment-ui/src/components/HonestCoverageCard.tsx,
    unified-api-contracts/unified_api_contracts/external/gcp/cloud_monitoring.py,
  ]
supersedes:
superseded_by:
depends_on:
source:
assigned_role: infra
effort: medium
drift_direction: advance-code
---

# Honest Coverage rollup — add per-asset-group GCS storage-size summary stat

> **Status: active** — operator resolved both open design questions 2026-08-14 (full build; storage lives in the
> existing per-AG `by_asset_group[ag]` coverage.json cell). LOCAL/human plan (`assigned_vm: NA`), never ingested by
> regen regardless of status — this flip just reflects the scope is settled, not that it's auto-dispatched.

## Why

Operator asked "how much sports data do we have across IS and MTDS in GCS, in TB" (2026-08-14). Answered via a one-off
Cloud Monitoring REST measurement (below), then asked to make this a standing stat on the Honest Coverage rollup rather
than a manual query each time.

**Measured baseline** (2026-08-14T09:55:00Z, `storage.googleapis.com/storage/total_bytes`, summed REGIONAL + COLDLINE
storage classes, prod tier only):

| Bucket                                                      | Bytes           | TB (1e12)  |
| ----------------------------------------------------------- | --------------- | ---------- |
| `instruments-store-sports-prd-central-element-323112` (IS)  | 60,944,478,854  | 0.0609     |
| `market-data-tick-sports-prd-central-element-323112` (MTDS) | 369,404,383,491 | 0.3694     |
| **Total**                                                   | 430,348,862,345 | **0.4303** |

## Current state (confirmed via code read, 2026-08-14)

- Honest Coverage v2 compute: `instruments-service/scripts/measure_honest_coverage.py`, `_compute_coverage()`
  (`by_asset_group[ag]` cell assembly). Every field is row/shard-count based (`captured`/`empty_confirmed`/
  `attempted_failed`/`expected_unattempted`/`total`/`coverage_pct`/`all_shards_coverage_pct` + v2 gate fields). No
  storage-size field exists.
- Serve: deployment-api passes the coverage JSON through at `/api/data-status/honest-coverage` verbatim.
- Render: `deployment-ui/src/components/HonestCoverageCard.tsx`, `deriveCoverage()` + the
  `AG_ORDER.filter(...).map(...)` per-AG tile block. No storage-size tile today.
- **No live Cloud Monitoring integration exists anywhere in the codebase.**
  `unified-api-contracts/unified_api_contracts/external/gcp/cloud_monitoring.py` defines pydantic request/response
  schemas mirroring `google.cloud.monitoring_v3`, but has zero callers. Per this workspace's HARD RULE, GCS-adjacent
  cloud calls must go through a UTL-mediated client (no subprocess `gcloud`/`gsutil`), so this needs a real
  `MetricServiceClient`-backed helper, not a CLI wrapper.

## Design questions — RESOLVED (operator, 2026-08-14)

- **Build scope: full build** (not a lighter ad-hoc query skill). 4-repo touch + IAM grant confirmed worth it.
- **Field placement: per-AG `by_asset_group[ag]` coverage.json cell** (additive schema bump, not a separate endpoint).
- **Soft-delete exclusion: already satisfied by the metric itself — no extra filtering needed.** Confirmed live via
  `GET /v3/projects/central-element-323112/metricDescriptors/storage.googleapis.com%2Fstorage%2Ftotal_bytes`
  (2026-08-14): the metric's own description reads _"Soft-deleted objects are not included in the total; use the updated
  v2 metric for a breakdown of total usage including soft-deleted objects."_ So
  `storage.googleapis.com/storage/total_bytes` (metricKind GAUGE, valueType DOUBLE, unit `By`, single label
  `storage_class`) — the exact metric already used for this doc's measured baseline below — is the correct metric to
  call; do NOT switch to `storage/v2/total_bytes` (that one adds an `object_type` label with `live`/`noncurrent`/
  `soft-deleted` breakdown specifically because it INCLUDES soft-deleted bytes by default, which is not what we want
  here).
- **IAM: DONE.** `roles/monitoring.viewer` granted directly to
  `unified-trading-sa@central-element-323112.iam.gserviceaccount.com` on project `central-element-323112` (2026-08-14,
  self-service per finding W in `task_template.md` — this is the orchestrator's own ambient GCP identity, not a foreign
  credential). Verified live via
  `gcloud projects get-iam-policy central-element-323112 --flatten="bindings[].members" --filter="bindings.members:unified-trading-sa@central-element-323112.iam.gserviceaccount.com AND bindings.role:roles/monitoring.viewer"`
  → returned `roles/monitoring.viewer`.

## Todos (LOCAL — executed directly in this interactive session, not AO-dispatched)

- [x] 2. ✅ [INFRA] P3. Built
      `get_bucket_total_bytes(bucket_name: str, project_id: str, lookback_days: int = 3) -> float` in
      `unified-trading-library/unified_trading_library/cloud_interface/cloud_monitoring_ops.py`, re-exported from
      `unified_trading_library/cloud_interface/__init__.py` AND the top-level `unified_trading_library/__init__.py` (the
      latter was a gap this change surfaced — `check-import-patterns.py` in instruments-service's QG caught the missing
      top-level export, fixed same-session). Lazy-imports `google.cloud.monitoring_v3` inside the function. Deliberately
      does NOT reuse `unified_api_contracts.external.gcp.cloud_monitoring`'s pydantic schemas — those mirror the raw
      REST/JSON shape for callers without the native SDK; this codebase's own convention (every other UTL GCP client)
      extracts typed fields off the real `MetricServiceClient` SDK response via `getattr`/`cast` instead, and converting
      the SDK's already-structured response into a UAC dict-shaped model only to immediately re-extract it would be a
      pure downgrade with no real process boundary crossed. Added `google-cloud-monitoring>=2.21.0,<3.0.0` to
      `unified-trading-library/pyproject.toml` (`uv lock` resolved to 2.31.0). — unified-trading-library@5d619a6894.
      Evidence: `basedpyright` clean (0 errors, 0 warnings); `QG_SLICE=tests` (full unit suite incl. the 3 new tests in
      `tests/cloud_interface/unit/test_cloud_monitoring_ops.py` — latest-per-storage-class summing,
      empty-bucket-returns-zero, filter/request-shape) → `✅ Tests PASSED`; `ruff check` on touched files → all passed.
      Both gate slices took 900s/2288s to START (host-wide `WAIT_RAM_LIVE` contention from other concurrent sessions on
      this shared host), ran clean once admitted — no code-level residual issues. Reinforced by the live functional
      proof below.
- [x] 1. ✅ [INFRA] P3. Grant `monitoring.viewer` to `unified-trading-sa` on `central-element-323112` —
      unified-trading-pm@(no code, IAM-only) + live-verified 2026-08-14 (see Design questions section above).
- [ ] [DATA] P3. BLOCKED-ON:sports_fixtures_weather_live_edit_2026_08_14 — Wired `_compute_coverage()` in
      `instruments-service/scripts/measure_honest_coverage.py` (docstring 21-32, import 125, new helpers
      `_instruments_store_kind()` 281-293 + `_measure_ag_storage_bytes_tb()` 296-326, call site 852-856) to set
      `ag_counts["storage_bytes_tb"] = round((is_bytes + mtds_bytes) / 1e12, 4)`. **Scope decision, evidence-based, not
      guessed**: the existing `by_asset_group[ag]` cell's row/shard counts are already sourced ENTIRELY from MTDS's
      bucket (`_MANIFEST_BUCKET_CANDIDATES`, confirmed by direct code read) — there is no separate IS-only or MTDS-only
      coverage.json, this is the one cross-AG harness and the cell already implicitly reaches across the IS/MTDS
      boundary. So `storage_bytes_tb` SUMS `resolve_bucket_name(kind=     "instruments-store", asset_group=ag)` (IS) +
      the MTDS prd-primary bucket, both pinned to `deployment_env=     "prod"` — matching this doc's own resolved
      baseline of 0.43 TB (IS+MTDS combined), which only equals 0.061+0.369 summed. Fails gracefully per-AG (broad
      catch, `logger.warning`, returns `None`, never aborts the run) since a storage-metric outage must not block
      data-correctness-critical coverage computation. Called once per AG (no per-shard loop). —
      instruments-service@(quickmerge BLOCKED, see below — content correct + live-proven, not yet landed). Evidence:
      `bash scripts/quality-gates.sh --no-fix` → `✅ ALL QUALITY GATES PASSED (99s)`, exit 0, fresh non-cached blocking
      foreground run. **Live sanity check (this session, after fixing the dependency gap below): `storage_bytes_tb` for
      sports = `0.4303`, exact match to this doc's manually-measured 0.061+0.369=0.430 baseline** — real end-to-end call
      through `measure_honest_coverage.py` → `get_bucket_total_bytes` → live Cloud Monitoring API, not a mock.
      **Shipping blocker (2026-08-14)**: quickmerge's `--agent` fast path fell back to a full un-baselined re-gate scan
      (tree drifted from the Pass-1 sentinel because a DIFFERENT live session sharing this checkout is actively editing
      `instruments_service/engine/orchestrator/sports_fixtures.py`/`weather.py`); that full scan surfaced 4 findings — 3
      confirmed PRE-EXISTING on `origin/live-defi-rollout` HEAD (verified via `git show`, none in files this todo
      touches: `sports_reference_core.py`'s backward-compat comment, a hardcoded-project-ID pattern in
      `test_reconcile_correct_legacy_blank_misflips_cefi_2026_05_13.py`, a real-cloud-API mock comment in
      `test_enumerate_v2_stream_write_oom_fix_2026_08_01.py`) + 1 genuinely new (`sports_fixtures.py` pushed to 908L, 8
      over the 900L cap, by that OTHER session's in-progress edit — 898L on HEAD). Reproduced identically on 2
      consecutive retries (not flaky). Per this workspace's multi-agent-safety rule, a live claim (file mtime <120s at
      time of check) is PROTECT-only — did not touch any of the 4 files. Also fixed 2 REAL, in-scope QG findings along
      the way (both in my own new files, already folded into this todo's evidence above): a hardcoded
      `central-element-323112` project ID in the new UTL test (→ `test-project`), and an empty-string-fallback on the
      `storage_class` label in `cloud_monitoring_ops.py` (→ raises `ValueError` instead of silently defaulting). **Next
      step**: retry
      `bash scripts/quickmerge.sh "feat: wire storage_bytes_tb into honest-coverage harness     (IS+MTDS bucket sum)" --agent --files 'scripts/measure_honest_coverage.py uv.lock     tests/unit/test_measure_honest_coverage.py'`
      once the other session's `sports_fixtures.py`/`weather.py` edits land or drop back under the line cap.
- [x] 4. ✅ [INFRA] P3 (found + fixed mid-session, not in original todo list). `instruments-service`'s own
      `pyproject.toml`/`uv.lock` did not carry `google-cloud-monitoring` as a dependency (a transitive gap from UTL —
      `uv sync --frozen` confirmed nothing new installed under the stale lock, and the live sanity check first failed
      with `ModuleNotFoundError: No module named 'google.cloud.monitoring_v3'`). Fixed via `uv lock` in
      instruments-service (219 packages resolved, `google-cloud-monitoring v2.31.0` added) + `uv sync --frozen`
      (confirmed `from unified_trading_library import get_bucket_total_bytes` now imports cleanly). This is what
      unblocked the live sanity check above. — instruments-service@(working tree, uncommitted; `uv.lock` diff only).
- [x] 5. ✅ [BACKEND] P3. Confirmed deployment-api's `/api/data-status/honest-coverage` — route handler is actually
      `deployment_api/routes/data_status/_live_coverage_honest.py::get_honest_coverage` (prefix `/api/data-status`, NOT
      `coverage_metrics.py` as originally guessed at recon time — that module is unrelated). Reads
      `gs://{project}-honest-coverage/{date}/coverage.json` raw, `json.loads` into a bare `dict[str, object]`, adds two
      provenance keys, returns via `Response(media_type="application/json")` — no `response_model=`, no Pydantic
      validation, no field whitelist anywhere in or reachable from this file. **No code change needed** — a new
      `storage_bytes_tb` key passes through completely untouched. — deployment-api@(no change).
- [x] 6. ✅ [UI] P3. Added a storage-size tile to `HonestCoverageCard.tsx`'s per-AG summary block. `src/api/client.ts`:
      added `storage_bytes_tb?: number` to the `by_asset_group[ag]` cell type. `HonestCoverageCard.tsx`: new
      `formatStorageTb()` (2-3 sig figs — `.toFixed(2)` <10 TB, `.toFixed(1)` <100 TB, `.toFixed(0)` ≥100 TB, e.g. "0.43
      TB" / "12.7 TB" / "156 TB"); `deriveCoverage()` returns `storageBytesTb: s.storage_bytes_tb ?? null` (same
      null-hiding pattern as `couldExistPct`); new conditional tile row (`data-testid="coverage-storage-tb"`, hides
      entirely — no "—" placeholder — when the field is absent, matching the file's existing hide-not-fake convention).
      Extended (not duplicated) the existing `tests/smoke/data_status_coverage_labels.spec.ts` with 2 new Playwright
      tests: sports `0.4303`→"0.43 TB" + tradfi `156.4`→"156 TB" render correctly with no `"undefined"` anywhere, AND
      the tile cleanly absents itself (zero DOM matches, no `"undefined"` text) against the real cron payload shape (no
      `storage_bytes_tb` field). This commit ALSO bundled 3 unrelated live bugs the operator surfaced mid-session (see
      Progress Log): the deployment-ui console 401 root-cause fix (`deploymentApi.ts` — 34 fetch call sites now attach
      `Authorization: Bearer <google_id_token>`, matching `client.ts`'s existing pattern), the "Check Status" dead-click
      fix in `ExecutionDataStatus.tsx` (a disabled button was preventing its own guard-clause error banner from ever
      firing), and the Pipeline Trace instrument type-ahead (`PipelineTraceCard.tsx`, reuses the existing
      `/api/data-status/instruments/search` endpoint + `DataStatusTab.tsx`'s search pattern). —
      deployment-ui@deb97bff9c. Evidence: consolidated `npx tsc --noEmit` clean across the full combined diff;
      `npx eslint` clean; combined Playwright run across all 3 touched specs → 25/25 passed (2.2m). Post-push ancestry
      verified; `authHeaders(` confirmed present in the pushed `deploymentApi.ts` (35 occurrences — 1 definition + 34
      call sites).
- [x] 7. ✅ [DOC] P3. Updated `/codex/02-data/honest-coverage-model.md` — `storage_bytes_tb` added to the example JSON +
      a new documentation paragraph covering metric source, TB/1e12 unit, soft-delete exclusion, the IS+MTDS dual-bucket
      scope decision + rationale, prod-tier pinning, and prediction's flat-kind resolution via
      `_instruments_store_kind()`. **Re-applied once** (2026-08-14): the first pass was silently overwritten by a
      concurrent commit from a different slot/host ("main·laptop") landing on this SAME shared working tree between when
      it was written and when this session checked back — a real instance of the "ahead=0 + clean tree ≠ landed" risk
      this workspace's rules warn about, here caused by uncommitted content (not even a push race) being clobbered by a
      peer session's own commit+pull cycle on the shared checkout. — unified-trading-pm@(shipping via safe-doc-push.sh,
      see below).

## Progress Log

- **2026-08-14 (interactive session, slot 3)**: Filed as `status: draft` per operator's mid-turn ask to surface the
  measured sports storage figure (IS 0.061 TB + MTDS 0.369 TB = 0.43 TB total) inside the Honest Coverage rollup's
  summary stats.
- **2026-08-14 (same session, follow-up)**: Operator resolved both design questions (full build; per-AG cell) and raised
  a third requirement (exclude soft-deleted bytes) — confirmed already satisfied by
  `storage.googleapis.com/storage/total_bytes`'s own metric definition (see Design questions section). Granted +
  live-verified `roles/monitoring.viewer` to `unified-trading-sa` directly (self-service, finding W). Flipped to
  `status: active`.
- **2026-08-14 (same session, build complete)**: All 7 todos landed via parallel per-repo agents + direct
  interactive-session work (dependency-lock fix, live sanity check). **End-to-end proof**: a real (non-mocked) call
  through the shipped code path returned `storage_bytes_tb = 0.4303` for sports, exactly matching this doc's
  manually-measured baseline. **Everything is WORKING-TREE ONLY across 4 repos — nothing committed, nothing pushed,
  nothing deployed.** It will not appear in any live UI until shipped. **All gates now confirmed green**: UTL's own
  `QG_SLICE=tests`/`typecheck` (both passed, delayed only by host RAM-governor admission, not code issues), ruff clean,
  instruments-service's full `quality-gates.sh` passed (99s), deployment-ui's Playwright spec 7/7 passed + tsc clean
  (pre-existing unrelated errors excluded via `git stash` diff). No residual verification debt remains. **Next step (not
  yet done, needs an explicit operator go-ahead per this workspace's commit-discipline norms)**: review the diffs, then
  commit + quickmerge each repo (unified-trading-library first — instruments-service depends on it) and flip these
  checkboxes' commit-sha references.
