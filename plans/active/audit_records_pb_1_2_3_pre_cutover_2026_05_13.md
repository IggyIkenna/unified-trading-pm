---
title: Audit Records PB-1/2/3 Pre-Cutover (append-only + retention-lock + path fix)
type: active-plan
status: active
created: 2026-05-13
deadline: 2026-05-23
locked_by: live-defi-rollout
locked_since: 2026-05-13
estimate_class: brand-new
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.5
effective_concurrent_slots: 1
---

# Audit Records PB-1/2/3 Pre-Cutover

> **Source**: `plans/active/work_split_2026_05_13_harsh.md` § Slot 5. Operator confirmed all 3 items pre-cutover.
> Reference issue: `plans/active/issues/codex_audit_position_balance_2026_05_12.md` (file not yet created — see scope below).

## Pre-audit manifest

| Symbol / pattern | Current state | Action |
|---|---|---|
| `persist_audit_log` | `execution_service/utils/audit_log.py:37` | Fix path + add `client_order_id` param + use `resolve_bucket_name` |
| `audit/{client_id}/{YYYY/MM/DD}/{ts_iso}-{event_type}.json` | Wrong: `%Y/%m/%d` date, wrong path structure, `.json` ext | Fix to `audit/{client_id}/{YYYY-MM-DD}/{event_type}/{client_order_id}_{ts_iso}.jsonl` |
| `order_adapter.py:141,165,175,195` | Passes `client_order_id` as `client_id` param | Fix: pass "system" as client_id + `client_order_id=<order_id>` |
| `oms.py:115` | Passes `operation_id` as `client_id` | Fix: pass "system" as client_id + `client_order_id=operation_id` |
| `manual_instruction_api.py:360,644` | Passes `request.client_id` correctly | Add `client_order_id=instruction_id` for traceability |
| `cloud-providers.yaml` | No `audit-records` bucket kind | Add GCP + AWS `audit-records` bucket entries |
| `test_gcs_audit_log.py` | Tests mock `_get_cloud_config` for bucket name | Update to mock `resolve_bucket_name` + verify new path shape |

## Phase 1 — Scope (SERIAL)

- [x] [SCRIPT] P0. Read `audit_log.py`, `order_adapter.py`, `oms.py`, `manual_instruction_api.py`, `cloud-providers.yaml` — understand current state. (done at boot — see pre-audit manifest above)

## Phase 2 — PB-1 + PB-3: Fix audit_log.py + callers (SERIAL — code changes)

- [x] [SCRIPT] P0. Fix `execution_service/utils/audit_log.py`:
  - Add `client_order_id: str | None = None` parameter after `account_id`
  - Change path to `audit/{client_id}/{YYYY-MM-DD}/{event_type}/{order_id}_{ts_iso}.jsonl`
    where `order_id = client_order_id or "no-order"`
  - Change extension to `.jsonl` (content_type `application/jsonl`)
  - Date format: `%Y-%m-%d` (not `%Y/%m/%d`)
  - Use `resolve_bucket_name(cloud=_cloud_from_config(), kind="audit-records")` instead of `getattr(config, "audit_log_bucket", None) or "trading-audit-logs"`
  - Keep `_get_cloud_config()` for `cloud_provider` only; use `resolve_bucket_name` for bucket name
  (execution-service@51f1f879)
- [x] [SCRIPT] P0. Fix callers in `order_adapter.py`:
  - Line 141: `persist_audit_log("ORDER_CREATED", payload, "system", client_order_id=client_order_id or "unknown")`
  - Line 165: `persist_audit_log("ORDER_FILLED", payload, "system", client_order_id=_result_client_id)`
  - Line 175: `persist_audit_log("ORDER_REJECTED", payload, "system", client_order_id=_result_client_id)`
  - Line 195: `persist_audit_log("ORDER_CANCELLED", payload, "system", client_order_id=order_id)`
  (execution-service@51f1f879)
- [x] [SCRIPT] P0. Fix caller in `oms.py` line 115:
  - `persist_audit_log("ORDER_UPDATED", payload, "system", client_order_id=operation_id)`
  (execution-service@51f1f879)
- [x] [SCRIPT] P0. Update `manual_instruction_api.py` (lines 352, 637) to add `client_order_id=instruction_id`
  (execution-service@51f1f879)

## Phase 3 — PB-2: Bucket SSOT + provisioning (PARALLEL with Phase 2)

- [x] [SCRIPT] P0. Add `audit-records` bucket kind to `deployment-service/configs/cloud-providers.yaml`:
  - GCP: `audit-records: "trading-audit-records-${DEPLOYMENT_ENV_SHORT}-${GCP_PROJECT_ID}"`
  - AWS: `audit-records: "unified-trading-audit-records-${DEPLOYMENT_ENV_SHORT}-${AWS_ACCOUNT_ID}"`
  (deployment-service@c3ac1c5 — conflict-merged with upstream archetype-state/client-reports/manual-audit additions)
- [x] [SCRIPT] P0. Add `deployment-service/scripts/provision_audit_records_retention_lock.sh` with:
  - GCP Object Retention Lock: `gcloud storage buckets update gs://{bucket} --retention-period=220752000s`
  - AWS S3 Object Lock: `aws s3api put-object-lock-configuration ...` (COMPLIANCE mode, 7 years)
  - README: requires bucket to exist first (run setup-buckets.py first)
  (deployment-service@c3ac1c5)
- [ ] [INFRA] P0. Run provisioning to create + lock the `audit-records` bucket in prod GCP + AWS.

## Phase 4 — Tests + QG (SERIAL — after Phase 2)

- [x] [SCRIPT] P0. Update `tests/unit/test_gcs_audit_log.py`:
  - Remove mocking of `_get_cloud_config` for bucket name (still mock for cloud_provider)
  - Mock `resolve_bucket_name` to return a test bucket name
  - Updated `test_persist_uploads_jsonl_to_gcs`: verify JSONL content, new path shape, `.jsonl` extension
  - Updated `test_persist_blob_path_layout`: verify `audit/{client_id}/{YYYY-MM-DD}/{event_type}/...` shape
  - Added `test_append_only_distinct_paths_for_same_event_type`: 2 calls → 2 distinct paths
  - Added `test_persist_no_order_fallback_when_client_order_id_absent`: "no-order" sentinel
  - Added `test_persist_uses_resolve_bucket_name_with_audit_records_kind`: kind="audit-records"
  - 9 tests, all PASSED (execution-service@51f1f879)
- [ ] [SCRIPT] P0. Run `cd execution-service && bash scripts/quality-gates.sh`
  **BLOCKED**: pre-existing C901 complexity error in `rpc_fallback.py:69` (not my file) blocks QG step 2.
  My 5 files pass ruff + basedpyright scoped check. Tests 9/9 pass. **DEFERRED**: foreign file fix owned by teammate.
- [ ] [SCRIPT] P0. Run `cd deployment-service && bash scripts/quality-gates.sh`
  **BLOCKED**: pre-existing `pytest-timeout` missing from .venv (environment setup issue, not my change).
  My 2 files (yaml + bash script) have no Python tests. Lint step passed clean. **DEFERRED**: env setup owned by teammate.

## Done-definition

- [x] Append-only writes verified: `test_append_only_distinct_paths_for_same_event_type` PASSED (9/9 tests)
- [x] Path shape verified: `test_persist_blob_path_layout` PASSED — `audit/{client_id}/{YYYY-MM-DD}/{event_type}/{client_order_id}_{ts}.jsonl`
- [x] `audit-records` bucket kind in `cloud-providers.yaml` (GCP + AWS) — deployment-service@c3ac1c5
- [x] Provisioning script written + documented — `scripts/provision_audit_records_retention_lock.sh` — deployment-service@c3ac1c5
- [ ] QG passes for execution-service + deployment-service **BLOCKED** by pre-existing issues (see Phase 4 notes)

## Open questions

_(none yet)_
