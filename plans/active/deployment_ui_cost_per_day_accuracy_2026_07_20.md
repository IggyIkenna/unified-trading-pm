---
doc_type: plan
title: deployment-ui — Cost/day column accuracy (WS-1, split from the observability tracker)
summary: >-
  The Deployments table Cost/day column already reads real GCP BigQuery / AWS Athena billing data — no rate card, no
  fabrication — but three aggregation bugs make it misleading. Fix the 7-day average to divide by days-actually-billed
  instead of a fixed window, redefine the 24h projection as the most-recent-complete-day (partial-day-normalised
  fallback) instead of the peak observed day, map AWS ARN/instance-id billing rows to friendly VM names via the AWS
  census, and colour-code (not text-label) the actual-cost figure when it falls back to a partial day.
status: draft
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

> **🟡 Kept `draft` deliberately (operator 2026-07-20)** — the operator is mid-change on AO right now; this plan is
> written now (decisions are final) but not flipped `active`/dispatched until AO work settles. Flip `status: active`
> when ready to dispatch — no further authoring needed at that point.

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

- [ ] [REVIEW] P0. Reproduce + record the defect on live data — query `per_resource_daily(days=7)` for the VM showing
      `$4.4 / 7d $0.63 / 24h $4.4`; confirm it has exactly one billing day in the window; capture the `day_net` dict in
      the Progress Log as ground truth. No code change.
- [ ] [BACKEND] P0. **Fix the 7-day-average divisor** (decision 1). In `per_resource_daily`
      ([`service.py:319-327`](../../deployment-api/deployment_api/services/cost_observability/service.py)), divide by
      `len(day_net)` instead of the fixed window length. Sync field docs (`models.py:73-83`,
      [`deployments_inventory.py:425`](../../deployment-api/deployment_api/routes/deployments_inventory.py)). Empty case
      → `None` (honest absence).
- [ ] [BACKEND] P0. **Fix the 24h projection** (decision 2). Replace `max(daily)` (service.py:326) with: most recent
      COMPLETE billing day; fall back to partial-day normalisation (`day_cost / hours_billed × 24`) only when no
      complete day exists. Document the definition on the field. A legitimate `actual == projected` (a VM that ran
      exactly one complete day) is correct and expected.
- [ ] [DATA] P0. **Fix AWS attribution** (decision 3). Build the instance-id/ARN → friendly-name mapping from the AWS
      census (instance-id ↔ Name tag) already loaded by the inventory; apply it in the billing join so AWS VMs get real
      Cost/day. No mapping found → stay `None`, never fabricate `$0`.
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

## Codex SSOTs

- `codex/05-infrastructure/deployment-observability.md` — deployment inventory + (to add) the cost-attribution contract
  (three definitions, active-days average, 24h basis, GCP-name/AWS-ARN join, `cost_basis` colour convention).
- `codex/06-coding-standards/ui-testing-layers.md` — the UI gate (pw:L2 + cited spec) for the `CostCell` change.
