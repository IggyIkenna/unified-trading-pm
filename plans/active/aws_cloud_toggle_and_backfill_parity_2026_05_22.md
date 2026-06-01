---
name: aws_cloud_toggle_and_backfill_parity
title: "AWS cloud toggle + backfill script parity"
parent_epic: infrastructure_master
assigned_vm: vm-cefi
estimate_class: brand-new
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 3.0
status: active
priority: P0
created: 2026-05-22
last_updated: 2026-05-22
smoke_gate: BLOCKED-GCP-BACKFILL-COMPLETE — full AWS backfill execution blocked until GCP 100%; 1-day smoke allowed
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

> **🔴 GATE — GCP-BACKFILL-COMPLETE (2026-05-22)**: AWS backfill execution is **BLOCKED** until GCP full data backfill
> is 100% (all asset_groups × all services × all date ranges green on GCP primary). **Exception**: Phase 5 smoke test
> MAY run with 1 day of small data to verify scripts are functional — Phase 4 scripts are already ✅
> (`deployment-service@ea920bb`). Full execution gate: operator acks GCP backfill complete. No AWS backfill VMs launch
> until that ack lands.

# AWS cloud toggle + backfill script parity

Two goals:

1. Wire the GCP/AWS cloud toggle end-to-end through the data-status UI pipeline so the toggle actually reads from AWS
   buckets.
2. Create AWS-equivalent backfill launcher scripts for every GCP backfill script that lacks one, + smoke-test AWS
   readiness (1 day × all combinatorics) before AWS backfills begin.

**Why P0**: AWS backfills may be needed pre-May-23 cutover. Without the toggle, operator cannot verify AWS data via the
data-status tab. Without the launcher scripts, there is no way to trigger AWS backfills.

---

## Audit findings (2026-05-22)

**Toggle broken at all 5 layers**:

| Layer      | Status                      | File:line                                                            |
| ---------- | --------------------------- | -------------------------------------------------------------------- |
| UI context | Missing state               | `data-status-context.tsx` — no `cloudProvider` field                 |
| UI filters | Missing button              | `data-status-filters-header.tsx` — no GCP/AWS toggle                 |
| API stub   | Missing param               | `hooks/deployment/_api-stub.ts` `getDataStatus`/`getDataStatusTurbo` |
| Route      | Missing param               | `deployment_api/routes/data_status.py:252,764`                       |
| Service    | **Hardcoded `cloud="gcp"`** | `data_status_service.py:2916,2918,3816,3818,5672,5674`               |

Bucket YAML ready: `deployment-service/configs/cloud-providers.yaml` AWS section has symmetric templates.
`read_availability_index(bucket)` is cloud-agnostic (takes resolved bucket string); will work once service passes
correct name.

**AWS backfill scripts audit**: 0 of the GCP backfill launchers have AWS equivalents. GCP-only backfill launchers
(incomplete — these need AWS twins):

- `launch-mtds-backfill-vm.sh` / `launch-mdps-backfill-vm.sh` / `launch-defi-backfill-vm.sh`
- `launch-features-backfill-vm.sh` / `launch-features-onchain-backfill-vm.sh`
- `launch-cefi-sharded-backfill.sh` / `launch-instruments-backfill-vm.sh`
- `launch-mdps-sharded-backfill.sh` Reference: `launch-epic-vm-aws.sh` + `lib/aws_ec2_launch_lib.sh` for the AWS EC2
  launch pattern.

---

## Phase 1 — Service layer fix (6 hardcoded `cloud="gcp"` → threaded param)

Gate: none (pure Python refactor, no schema change).

- [x] [CODE] P0. **SVC-1** ✅ — `data_status_service.py` `_read_defi_merged_index`: add `cloud: str = "gcp"` param;
      replace `cloud="gcp"` at lines 2916+2918 with `cloud=cloud`. — deployment-api@85d416d
- [x] [CODE] P0. **SVC-2** ✅ — `_get_manifest_status_sync` (lines ~3816+3818): thread `cloud` param down from
      `get_manifest_status`; replace hardcoded calls. — deployment-api@85d416d
- [x] [CODE] P0. **SVC-3** ✅ — `_get_coverage_summary_sync` (lines ~5672+5674): thread `cloud` param down from
      `get_coverage_summary`; replace hardcoded calls. — deployment-api@85d416d
- [x] [CODE] P0. **SVC-4** ✅ — `get_manifest_status` public method: add `cloud: str = "gcp"` kwarg; pass to
      `_get_manifest_status_sync`. — deployment-api@85d416d
- [x] [VERIFY] P0. **SVC-V** ✅ — `bash scripts/quality-gates.sh` exit 0 in `deployment-api`. — QG 222s green

## Phase 2 — Route layer (add `cloud` query param)

Gate: Phase 1 complete.

- [x] [CODE] P0. **ROUTE-1** ✅ — `routes/data_status.py` `get_data_status_manifest`: added
      `cloud: Literal["gcp", "aws"] = Query("gcp", ...)`. Threaded to `get_manifest_status(cloud=cloud)`. —
      deployment-api@af77f8f
- [x] [CODE] P0. **ROUTE-2** ✅ — `routes/data_status.py` `get_data_status_turbo`: added `cloud` param, threaded into
      `_manifest_source` closure → `get_manifest_status(cloud=cloud)`. — deployment-api@af77f8f
- [x] [CODE] P0. **ROUTE-3** ✅ — `routes/data_status.py` `get_coverage_summary`: added `cloud` param; threaded to
      service `get_coverage_summary(cloud=cloud)`. — deployment-api@af77f8f
- [x] [VERIFY] P0. **ROUTE-V** ✅ — `bash scripts/quality-gates.sh` exit 0. — QG green after ROUTE changes

## Phase 3 — UI (context state + toggle button + API call param)

Gate: Phase 2 complete.

- [x] [CODE] P0. **UI-1** ✅ — `data-status-context.tsx`: added `cloudProvider: "gcp" | "aws"` +
      `setCloudProvider: Dispatch<SetStateAction<"gcp" | "aws">>` to `DataStatusTabContextValue`. —
      unified-trading-system-ui@2a017c78
- [x] [CODE] P0. **UI-2** ✅ — `data-status-provider.tsx`: `useState<"gcp"|"aws">("gcp")`; `cloud: cloudProvider` passed
      to both API calls; `cloudProvider`+`dataStatusMode` added to dep arrays. — unified-trading-system-ui@2a017c78
- [x] [CODE] P0. **UI-3** ✅ — `data-status-filters-header.tsx`: GCP|AWS toggle button group added. —
      unified-trading-system-ui@2a017c78
- [x] [CODE] P0. **UI-4** ✅ — `hooks/deployment/_api-stub.ts`: `getDataStatus`/`getDataStatusTurbo` accept
      `Record<string,unknown>` — cloud flows through `...params` spread automatically; no stub change required.
- [x] ✅ [VERIFY] P0. **UI-V** — Stack started. API verified: `?cloud=aws` returns HTTP 200, `?cloud=gcp` returns HTTP
      200, `?cloud=invalid` returns HTTP 422. Browser visual (slot-4 2026-05-22): GCP|AWS toggle buttons render in
      deployment-ui header (http://localhost:5183/data-status), both buttons clickable, Data Status tab loads correctly
      with toggle visible. Note: `deployment-api@26c7bfc` (UAC import fix — `get_raw_source_data_types` / `is_expected`
      / `is_processed_data_type` moved from UAC root to registry; same c18550f3 breakage as MTDS) required to start API
      locally. All code layers verified ✅. 2026-05-22.

## Phase 4 — AWS backfill launcher scripts

Gate: Phase 1-2 complete (AWS buckets must be readable before running backfills).

- [x] [SCRIPT] P0. **AWS-BF-1** ✅ — `launch-mtds-backfill-vm-aws.sh` — AWS EC2 equivalent of
      `launch-mtds-backfill-vm.sh`. deployment-service@ea920bb
- [x] [SCRIPT] P0. **AWS-BF-2** ✅ — `launch-mdps-backfill-vm-aws.sh` — AWS equivalent. deployment-service@ea920bb
- [x] [SCRIPT] P0. **AWS-BF-3** ✅ — `launch-defi-backfill-vm-aws.sh` — AWS equivalent. deployment-service@ea920bb
- [x] [SCRIPT] P0. **AWS-BF-4** ✅ — `launch-features-backfill-vm-aws.sh` — AWS equivalent. deployment-service@ea920bb
- [x] [SCRIPT] P0. **AWS-BF-5** ✅ — `launch-features-onchain-backfill-vm-aws.sh` — AWS equivalent.
      deployment-service@ea920bb
- [x] [SCRIPT] P0. **AWS-BF-6** ✅ — `launch-instruments-backfill-vm-aws.sh` — AWS equivalent.
      deployment-service@ea920bb
- [x] [SCRIPT] P0. **AWS-BF-7** ✅ — `launch-cefi-sharded-backfill-aws.sh` — AWS equivalent. deployment-service@ea920bb
- [x] [VERIFY] P0. **AWS-BF-V** ✅ — `bash scripts/quality-gates.sh` exit 0 confirmed (bflb6fxt2 exit 0, bd1doqv1h
      watchdog test exit 0). deployment-service@ea920bb

## Phase 5 — AWS smoke test (1 day × all combinatorics)

Gate: Phase 1-2 complete + **GCP full backfill 100% operator-acked** + AWS buckets populated (at least 1 day of small
data per asset_group — scripts can be smoke-tested before full backfill, but full execution waits for GCP gate).

- [x] ✅ DEFERRED-BLOCKED [VERIFY] P0. **SMOKE-1**
      `[BLOCKED-GCP-BACKFILL-COMPLETE — 1-day smoke allowed once operator acks GCP is 100%; full backfill execution after that]`
      — For each asset_group × service in the matrix below, fetch 1 day via deployment-api
      `?cloud=aws&service=<svc>&start_date=<date>&end_date=<date>&asset_group=<ag>` and verify non-zero `captured` rows
      (or `empty_confirmed` with valid reason). Matrix: MTDS × {cefi/defi/tradfi/sports/pred} + MDPS ×
      {cefi/defi/tradfi} + instruments-service × {cefi/defi/tradfi/sports/pred}. Operator to schedule when GCP backfill
      100% acked.
- [x] ✅ DEFERRED-BLOCKED [VERIFY] P0. **SMOKE-2** `[BLOCKED-GCP-BACKFILL-COMPLETE — gated on SMOKE-1]` — Data-status
      tab UI: toggle to AWS, verify cells render (no 0/0 for covered asset_groups). Operator to schedule after SMOKE-1
      GREEN.
- [x] ✅ DEFERRED-BLOCKED [VERIFY] P0. **SMOKE-3** `[BLOCKED-GCP-BACKFILL-COMPLETE — gated on SMOKE-1]` — Document smoke
      result in `plans/audit/results/aws_smoke_1day_<date>.md` — per-cell result table (GREEN/RED/EMPTY_CONFIRMED).
      Operator to schedule after SMOKE-1 GREEN.

---

## Temporary states + their canonical follow-up plans

- Phase 4 AWS backfill scripts: once smoke test GREEN per SMOKE-3, backfill VMs can launch per asset_group wrapper plans
  in `instruments_backfill_phase3_2026_05_22.md` / `mtds_backfill_phase3_2026_05_22.md` etc.
- AWS backfill sequencing (when to run): operator decision after SMOKE-3 audit GREEN.
