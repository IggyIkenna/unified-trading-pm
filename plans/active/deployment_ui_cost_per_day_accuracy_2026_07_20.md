---
doc_type: plan
title: deployment-ui — Cost/day column accuracy (WS-1, split from the observability tracker)
summary: >-
  The Deployments table Cost/day column already reads real GCP BigQuery / AWS Athena billing data — no rate card, no
  fabrication — but three aggregation bugs make it misleading. Fix the 7-day average to divide by days-actually-billed
  instead of a fixed window, redefine the 24h projection as the most-recent-complete-day (partial-day-normalised
  fallback) instead of the peak observed day, map AWS ARN/instance-id billing rows to friendly VM names via the AWS
  census, and colour-code (not text-label) the actual-cost figure when it falls back to a partial day.
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [deployment-api, deployment-ui]
scope: [engineer]
tags: [deployment-ui, cost, billing, observability]
related:
  - deployment_ui_observability_ux_tracker_2026_07_17.md
created: "2026-07-20"
last_updated: "2026-07-20"
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
assigned_role: backend_engineer
drift_direction: advance-code
sequential: true
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source: split from deployment_ui_observability_ux_tracker_2026_07_17.md WS-1, per operator 2026-07-20 decision session
---

# deployment-ui — Cost/day column accuracy

> **🟢 ACTIVE (operator 2026-07-21)** — flipped `active` as one of the first two plans dispatched to AO to test its
> reliability (the other is `deployment_ui_date_range_filter_and_search_2026_07_20.md`). Must-do review fixes applied
> before activation (AWS-census wiring named, `hours_billed` defined, repro todo de-hypothesized). Remaining
> observability plans stay `draft` until these two complete and AO looks stable.

## Context

Split out of
[`deployment_ui_observability_ux_tracker_2026_07_17.md`](deployment_ui_observability_ux_tracker_2026_07_17.md) WS-1 —
see that tracker for the full root-cause trace (code paths, line numbers, the exact `$4.4 / 7d $0.63 · 24h $4.4` symptom
explained). Summary: `per_resource_daily()` in
[`deployment-api/deployment_api/services/cost_observability/service.py`](../../deployment-api/deployment_api/services/cost_observability/service.py)
already sources real billing (GCP BigQuery resource-level export + AWS Athena CUR) — the three figures are correct in
principle, wrong in aggregation.

## Decisions (operator, 2026-07-20 — all four confirmed, no longer open)

1. **7-day average divisor** — divide by the count of days the resource actually has billing rows (`len(day_net)`), not
   the fixed window length 7.
2. **24h projection** — most recent COMPLETE billing day; if none exists yet, normalise the partial day
   (`day_cost / hours_billed × 24`) as fallback. (Machine-type rate card × 24 rejected — keeps the no-rate-card design.)
3. **AWS attribution** — join CUR `line_item_resource_id` (ARN/instance-id) against the AWS census the inventory already
   loads, keyed on the instance's Name tag.
4. **Partial-day `cost_actual_usd`** — keep showing it (don't hold `None`), but distinguish it from a complete-day
   figure by **colour, not a text label** — the backend must expose a basis flag so the UI can key its styling off it.

## Todos

- [x] ✅ [REVIEW] P0. Reproduce + record the defect on live data — run `per_resource_daily(days=7)` and find ANY
      resource with billing rows for exactly ONE day in the window (it will exhibit `avg == actual/7` and
      `projected == actual`, the reported symptom; `$4.4 / 7d $0.63 / 24h $4.4` was an illustrative example, not a
      specific named VM to search for). Capture that resource's `day_net` dict in the Progress Log as ground truth. No
      code change. — reproduced 2026-07-21, see Progress Log.
- [x] ✅ [BACKEND] P0. **Fix the 7-day-average divisor** (decision 1). In `per_resource_daily`
      ([`service.py:319-327`](../../deployment-api/deployment_api/services/cost_observability/service.py)), divide by
      `len(day_net)` instead of the fixed window length. Sync field docs (`models.py:73-83`,
      [`deployments_inventory.py:425`](../../deployment-api/deployment_api/routes/deployments_inventory.py)). Empty case
      → `None` (honest absence). — deployment-api@b6bebdf: `avg_7d_usd=round(sum(daily) / len(daily), 2)`
      (`daily = list(day_net.values())`, so `len(daily) == len(day_net)`); docs synced in `models.py` +
      `deployments_inventory.py`; existing regression test `test_per_resource_daily_three_values` updated (was asserting
      the buggy `/7` divisor, now asserts `/3` = days actually billed).
- [x] ✅ [BACKEND] P0. **Fix the 24h projection** (decision 2). Replace `max(daily)` (service.py:326) with: most recent
      COMPLETE billing day; fall back to partial-day normalisation (`day_cost / hours_billed × 24`) only when no
      complete day exists — where `hours_billed` = wall-clock hours elapsed since UTC midnight for that partial day
      (`datetime.now(timezone.utc)`), NOT a new hourly billing query (the billing snapshot is daily-grained). Document
      the definition on the field. A legitimate `actual == projected` (a VM that ran exactly one complete day) is
      correct and expected. — deployment-api@3359d4b:
      `projected_24h = day_net[max(complete_days)] if complete_days     else day_net[latest] / hours_billed * 24`;
      `hours_billed` floored at 1h to avoid a runaway multiplier in the first minutes of a new UTC day. Regression tests
      added: peak-vs-most-recent-complete-day distinction (`test_per_resource_daily_three_values`, now uses a
      $30-peak/$20-recent dataset) + partial-day normalisation (`test_per_resource_daily_24h_partial_day_normalized`).
      Docs synced in `models.py` + `deployments_inventory.py`.
- [ ] [DATA] P0. **Fix AWS attribution** (decision 3). Concrete wiring: the census carrying both `instance_id` and
      `name` (Name tag) is `deployment-service` `backends/aws_census.py` (`AwsInstanceCensus` via `list_ec2_census()`),
      consumed in `deployment-api` `routes/_aws_deployments.py::_ec2_item` — but the item currently drops `instance_id`
      before the billing join in `deployments_inventory.py:1678 _attach_costs` (which matches only on `item.name`).
      Build `{inst.instance_id: inst.name}` from the census and thread it into `_attach_costs` (new optional param) so
      an AWS CUR row's `line_item_resource_id` (ARN → parse trailing `instance/i-…`) resolves to the friendly name
      before the join. No mapping found → stay `None`, never fabricate `$0`.
- [ ] [BACKEND] P1. **Partial-day basis flag** (decision 4). When `cost_actual_usd` falls back to the latest PARTIAL day
      (no complete day exists — service.py:321-322), emit a `cost_basis: "partial" | "complete"` field alongside it (or
      equivalent) so the frontend can style it — no text label, colour only. Field doc updated.
- [ ] [UI] P1. `CostCell` colour treatment — when `cost_basis == "partial"`, render the actual-cost figure in a visually
      distinct colour from the normal complete-day colour (no added text/tooltip — colour is the only signal per
      operator decision). `pw:L2 ✓` + a cited regression spec covering both partial and complete states.
- [ ] [REVIEW] P1. Unit tests — (a) 1-day-in-window → avg == actual (regression for the reported symptom); (b) N active
      days → avg == sum/N; (c) 24h basis is complete-day/normalised, not `max`; (d) AWS ARN→name mapping attributes a
      known CUR row; (e) unmapped AWS row stays `None`; (f) `cost_basis` is `"partial"` iff no complete day exists.
      `bash scripts/quality-gates.sh` green in deployment-api.
- [ ] [INFRA] P1. Ship (`quickmerge.sh "msg" --agent --files '<paths>'`) + flip todos same turn (`docs(plans):`).
- [ ] [REVIEW] P2. Post-phase codex audit — document the Cost/day attribution contract (three definitions, active-days
      average, 24h basis, GCP-name/AWS-ARN join, `cost_basis` colour convention) in
      `codex/05-infrastructure/deployment-observability.md`.

## Success criteria

- `cost_avg_7d_usd` averages over days the resource actually had billing rows — a 1-day-old VM reads `$4.4 · 7d ~$4.4`,
  not `$4.4 · 7d $0.63`.
- `cost_projected_24h_usd` is a defined full-day estimate (complete-day or partial-day-normalised), not "most expensive
  day we happened to see".
- AWS VMs get real Cost/day via ARN→name mapping, or an honest `—` — never a fabricated `$0`.
- A partial-day `cost_actual_usd` is visually distinguishable by colour alone, no text label.
- Source unchanged — still the real BigQuery/Athena billing snapshot; no rate card introduced anywhere.

## Progress Log

- **2026-07-20** — Split from `deployment_ui_observability_ux_tracker_2026_07_17.md` WS-1. Operator confirmed all four
  open decisions in an interactive session (avg divisor = days-actually-billed; 24h basis = complete-day +
  partial-day-normalised fallback; AWS mapping = census instance-id↔Name tag; partial-day `cost_actual_usd` = shown,
  distinguished by colour only, not a text label — this refines the tracker's original "tooltip" suggestion). Plan
  written now with decisions final but kept `status: draft` — operator is mid-change on AO and wants dispatch held until
  that settles.
- **2026-07-21** — Reproduced the defect on LIVE billing data (GCP BigQuery + AWS Athena,
  `GCP_PROJECT_ID=central-element-323112`, window 2026-07-15..2026-07-22 exclusive, `today=2026-07-21`) by calling
  `CostObservabilityService().per_resource_daily(days=7)` (and its internal `_window`/`_window_table`/`_agg` to recover
  the raw `day_net` per resource) from a standalone script — no code change. Of 1,676 resources with billing rows in the
  window, **1,039 (62%) have exactly ONE billing day** — the bug is the common case, not an edge case. Ground truth
  (near-exact match to the plan's illustrative `$4.4 / 7d $0.63 / 24h $4.4` figures):
  - `resource_id: features-sports-sports-20260719-113257`
  - `day_net: {"2026-07-19": 4.432787}`
  - current (buggy) output: `actual_usd=4.43`, `avg_7d_usd=0.63` (= `4.43/7`, decision-1 bug — divides by fixed window
    length 7 instead of `len(day_net)==1`), `projected_24h_usd=4.43` (= `max(daily)`, which happens to already equal
    `actual` for a true 1-day resource — decision-2 doesn't change this case, only the multi-day/partial-day cases).
  - Also captured for cross-check: `resource_id: cefi-queue-heavy-20260714-123340`,
    `day_net: {"2026-07-15": 5.7624200000000005}` → `actual_usd=5.76`, `avg_7d_usd=0.82`, `projected_24h_usd=5.76`.
  - Confirms the exact symptom named in the todo: `avg == actual/7` and `projected == actual`. After the decision-1 fix
    (divide by `len(day_net)`), `avg_7d_usd` for both examples above should read equal to `actual_usd` (`4.43` and
    `5.76` respectively), not `0.63`/`0.82`.

## Codex SSOTs

- `codex/05-infrastructure/deployment-observability.md` — deployment inventory + (to add) the cost-attribution contract
  (three definitions, active-days average, 24h basis, GCP-name/AWS-ARN join, `cost_basis` colour convention).
- `codex/06-coding-standards/ui-testing-layers.md` — the UI gate (pw:L2 + cited spec) for the `CostCell` change.
