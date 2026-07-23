---
doc_type: plan
title: Cost Observability — SKU/usage data foundation + breakdown enrichment (backend)
summary:
  Backend half of the cost-breakdown enrichment — pull the SKU and usage fields the query currently drops (all BigQuery
  and Athena-native, verified via a live bq probe) and derive the operator-requested detail on top. Adds gross/credit
  bifurcation per breakdown row, an SKU dimension, bucket storage volume plus class split, idle static-IP and
  orphaned-disk cost-waste, spot-vs-on-demand, VM machine specs from system_labels, and AWS invoice reconciliation.
  Feeds the UI half (cost_obs_ui_unified_breakdown_2026_07_08), which stays draft until this plan's last task releases
  it.
status: complete
nature: process
asset_group: [meta]
stage: [meta]
repos: [deployment-api]
scope: [engineer]
tags: [billing, cost, observability, bigquery, athena, sku, breakdown, deployment-api]
related:
  [/plans/archive/2026_07/cost_observability_ui_2026_07_08.md, /codex/05-infrastructure/billing-cost-observability.md]
created: "2026-07-08"
last_updated: "2026-07-08"
parent_epic: deployment_and_user_management_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: design
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 2.4
assigned_role: backend-engineer
drift_direction: advance-code
depends_on: []
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: cost_observability_ui_2026_07_08.md
---

# Cost Observability — SKU/usage data foundation + breakdown enrichment (backend)

> **✅ ARCHIVED 2026-07-10 — COMPLETE.** Every todo shipped (see the Progress Log below). Codex aligned
> (`/codex/05-infrastructure/billing-cost-observability.md`: label dimension + real GitHub provider). Moved to
> `plans/archive/2026_07/`.

> **AO-DISPATCHED backend plan.** The backend half of the operator-requested cost-breakdown enrichment. Full design
> context, the live `bq` evidence, and the data-fidelity audit that motivated all of this live in the LOCAL parent plan
> **`cost_observability_ui_2026_07_08.md`** (read its "Resource-detail enrichment + unified breakdown" and
> "Data-fidelity audit findings" sections first). The UI half is **`cost_obs_ui_unified_breakdown_2026_07_08.md`** — it
> stays `draft` until this plan's LAST task flips it `active`, so the UI agent never builds against fields that don't
> exist yet.
>
> **Core principle (operator-decided, probe-verified):** every field here is **BigQuery/Athena-native** — pull
> `sku.description` + `usage.amount_in_pricing_units` (GCP) / `line_item_usage_type` + `usage_amount` (AWS CUR), the
> SKU + usage fields the current query drops, and derive everything from them keyed by `resource.name`. **NO Cloud
> Monitoring / CloudWatch** (extra API cost + an IAM grant we don't have). Anything not in the export is dropped, not
> sourced elsewhere.

## Codex SSOTs (read before touching)

- `/codex/05-infrastructure/billing-cost-observability.md` — the two exports + the net/gross/credit contract; **update
  it in task 10** with the new SKU/usage/waste/volume fields.
- `codex/06-coding-standards/` — no raw `boto3` / `google.cloud` (UTL wrappers), no `os.getenv`, UTC datetimes; run
  `bash scripts/quality-gates.sh` before every commit; ship via quickmerge.

## Tasks

- [x] ✅ [BACKEND] P0. **SKU + usage foundation** (unlocks tasks 3-8) — deployment-api@1a6e8a8. In
      `services/cost_observability/queries.py` `gcp_facts_sql`, add `sku.description AS sku`,
      `usage.amount_in_pricing_units AS usage_amount`, `usage.pricing_unit AS usage_unit` (extend the GROUP BY); in
      `aws_facts_sql` add `line_item_usage_type AS     usage_type` + `SUM(line_item_usage_amount) AS usage_amount`. Add
      `sku` / `usage_amount` / `usage_unit` to `CostRecord` + the GCP/AWS adapters in `providers.py`. pytest for the new
      columns.
- [x] ✅ [BACKEND] P1. **Bifurcate gross/credit/net per breakdown row** — deployment-api@a6bd1f8. Added `gross` +
      `credit` to `BreakdownRow` (currently net-only); populate net (primary), gross = Σcost, credit = Σcredit in
      `_grouped` / `_by_resource` / `_by_day` (and `_by_sku`, added by a concurrent task, for consistency). pytest
      asserting the per-row split and that it reconciles to the summary net/gross/credit across every dimension.
- [x] ✅ [BACKEND] P2. **SKU breakdown dimension** — deployment-api@9b4e59d. Add `sku` to the route `Dimension`
      literal + a `_by_sku` grouping (by `(cloud, service, sku)`), wired into `breakdown()`. This surfaces the hidden #1
      cost driver (Coldline Class A Operations). pytest.
- [x] ✅ [BACKEND] P2. **Bucket storage volume + class split** — deployment-api@171a61c. `dimension=bucket` rows now
      carry `storage_gb` (avg GB over the window), `storage_class_gb` (Standard/Nearline/Coldline/Archive split), and
      `cost_per_gb`, derived from the storage-volume SKUs' `usage_amount` (GCP `gibibyte month`, filtered via
      `usage_unit` to exclude operations/retrieval SKUs; AWS `TimedStorage-*` usage-types) grouped by `resource.name`.
      Rescaled GiB/GB-month → avg GB via `_AVG_DAYS_PER_MONTH` (365.25/12). Show GB, not raw bytes; no object count, no
      soft-delete split (dropped, not billable). pytest with GCP + AWS storage-SKU fixtures. Rebased 3x onto concurrent
      SKU-dimension/gross-credit/idle-waste tasks landing on the same file; full backend QG green on each merge.
- [x] ✅ [BACKEND] P2. **Idle static-IP + orphaned-disk cost-waste** — deployment-api@8d8802f. New
      `services/cost_observability/waste.py`: `Static Ip Charge` SKU (GCP) and `...ElasticIP:IdleAddress` usage-type
      (AWS) are self-contained idle flags (no cross-ref needed — those SKUs only bill while unattached);
      `... PD     Capacity` SKUs (GCP disks) cross-ref the currently-RUNNING VM fleet via
      `vm_utils.list_running_vm_names` (degrades to "not flagged" — never a false-positive orphan — when the fleet
      lookup is unavailable). Wired into `_by_resource` as new `BreakdownRow.is_idle` / `waste_kind` fields,
      resource-dimension only. AWS unattached-EBS dropped (not billable-native — no distinct idle usage-type in the CUR,
      and no AWS volume-attachment API integration exists in this codebase to cross-ref against; same "if not in the
      export, don't fabricate it elsewhere" contract as the bucket-volume task's dropped soft-delete split). pytest: 11
      new tests covering the classifiers + service-level flagging (evidence resources: `harsh-static-ip`,
      `ikenna-windows-tokyo-restored`). Full backend QG green.
- [x] ✅ [BACKEND] P2. **Spot vs on-demand split** — deployment-api@947a48b. Added `purchase_option` (spot | on-demand |
      other) to `CostRecord` + `BreakdownRow`, derived via `providers._purchase_option`: GCP `sku.description` text
      match on "spot"/"preemptible" vs "instance core"/"instance ram" (else "other" — the axis only applies to
      compute-instance SKUs, not storage/network); AWS `usage_type` text match on "SpotUsage" vs
      "BoxUsage"/"HeavyUsage"/"DedicatedUsage" (else "other"). Exposed on resource + service breakdown rows via a
      rank-based fold (`_PURCHASE_RANK`: spot > on-demand > other) — a group shows "spot" if ANY of its underlying SKU
      lines is spot-priced, since the question is "did this resource/service have any spot cost", not an arbitrary
      last-seen value across its many SKU lines. 4 new pytest cases (classifier unit test, provider-mapping test,
      resource/service aggregation-fold test). Rebased 3x onto concurrent idle-waste/bucket-storage/AWS-reconciliation
      tasks landing on the same files (models.py, service.py); full backend QG green on each merge.
- [x] ✅ [BACKEND] P2. **VM machine specs** — deployment-api@c3f5c39. Verified `system_labels` schema live via a bq
      probe against the resource-level export (only the instance's Core/Ram SKU rows carry
      `compute.googleapis.com/machine_spec` / `cores` / `memory` — disk/IP SKU rows for the same VM don't; memory is
      MiB, e.g. `n2-highmem-16` → cores=16, memory=131072 → 128 GB). `gcp_facts_sql` pulls the three labels via an
      `ANY_VALUE(SELECT ... FROM UNNEST(system_labels) ...)` per-key helper (no Compute API); added
      `machine_type`/`vcpu`/`memory_gb` to `CostRecord` + `BreakdownRow`; `_by_resource` tracks the latest non-empty
      spec per resource across its SKU rows. pytest: parser-helper tests, a provider-mapping test (VM row carries the
      spec, sibling disk-SKU row doesn't), a service-aggregation test. Rebased 3x onto concurrent
      idle-waste/bucket-storage/spot-purchase-option tasks landing on the same files (models.py, providers.py,
      service.py); full backend QG green + 4335-test suite green on each merge.
- [x] ✅ [BACKEND] P2. **AWS net + invoice reconciliation** — deployment-api@301ccfc. `aws_facts_sql` switched
      `line_item_unblended_cost` → `line_item_net_unblended_cost` (net of RI/SP discounts) and relaxed the
      `Usage`/`DiscountedUsage`-only filter to `IN ('Usage', 'DiscountedUsage', 'Tax', 'Fee')`, so the AWS total now
      reconciles toward the invoice instead of reporting usage-only spend (Refund/Credit/RIFee/SavingsPlanRecurringFee
      rows stay excluded — a further refinement, not required to close the usage-only gap). Tax/Fee rows carry no
      `usage_type` and fall back to `'Unknown'` via the existing `COALESCE(NULLIF(...))`. Rebased 3x onto concurrent
      zone-dimension/gross-credit/bucket-volume/idle-waste tasks landing on the same file; full backend QG green on each
      merge. pytest: `test_aws_facts_sql_uses_net_cost_and_includes_tax_and_fee`.
- [x] ✅ [BACKEND] P3. **Zone dimension** — deployment-api@537af3d. Add `location.zone` (GCP) /
      `line_item_availability_zone` (AWS) to `CostRecord` + a finer zone cut of the region dimension. pytest.
- [x] ✅ [BACKEND] P3. **Codex contract update** — unified-trading-pm (this commit). The earlier partial pass
      (deployment-api@075bf2542, before tasks 2/4-9 shipped) left the doc's "in flight / still pending" note stale —
      replaced with the full `BreakdownRow` field set (gross/credit, waste flags,
      storage_gb/storage_class_gb/cost_per_gb, purchase_option, machine_type/vcpu/memory_gb), the AWS net+invoice
      reconciliation note, the `zone` dimension, and the extended `CostRecord` tuple, in
      `/codex/05-infrastructure/billing-cost-observability.md`.
- [x] ✅ [BACKEND] P3. **Release the UI plan (draft-gate)** — unified-trading-pm (this commit). All 10 prior backend
      tasks (incl. the codex contract update, completed adjacent to this task after discovering it was marked done but
      never actually finished) are shipped and checked off; flipped
      `plans/active/cost_obs_ui_unified_breakdown_2026_07_08.md` `status: draft`→`active` so the UI agent picks it up
      against the now-complete API contract.
