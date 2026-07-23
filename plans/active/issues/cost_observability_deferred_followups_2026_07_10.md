---
doc_type: issue
title: Cost Observability — deferred follow-up enhancements (migrated at plan archival)
summary:
  The seven open follow-ups from the now-archived cost-observability plans, kept together as a tracked backlog. Two are
  operator-gated decisions (asset_group business-context enrichment; AWS CUR historical backfill); the other five are
  unscheduled P3 enhancements to the /ops/costs page. Migrated here 2026-07-10 when cost_observability_ui_2026_07_08.md
  and its two successors were archived complete, so none of the deferred work is lost. Nothing here is dispatched — pick
  up individually when prioritised.
status: open
nature: process
asset_group: [meta]
stage: [meta]
repos: [deployment-api, deployment-ui]
scope: [engineer]
tags: [billing, cost, observability, deferred, followup, deployment-api, deployment-ui]
related:
  [
    /plans/archive/2026_07/cost_obs_ui_unified_breakdown_2026_07_08.md,
    /plans/archive/2026_07/cost_obs_backend_sku_usage_enrichment_2026_07_08.md,
    /plans/archive/2026_07/cost_observability_ui_2026_07_08.md,
  ]
created: "2026-07-10"
last_updated: "2026-07-10"
parent_epic: deployment_and_user_management_master
priority: P2
source:
  migrated from cost_observability_ui_2026_07_08.md (Deferred / fast-follow + audit findings) at archival — operator
  2026-07-10
assigned_vm: NA
execution_scope: local-only
model_tier: sonnet
thinking_tier: medium
estimate_class: design
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.2
assigned_role: ui_developer
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
---

# Cost Observability — deferred follow-up enhancements

> Migrated verbatim (2026-07-10) from the archived `cost_observability_ui_2026_07_08.md` so the deferred backlog stays
> tracked after archival. All seven were `- [ ]` in that plan's _Deferred / fast-follow_ and _Data-fidelity audit_
> sections. Not dispatched — `assigned_vm: NA`. Two are **operator-gated** (marked below).

## Operator-gated (waiting on a decision)

- [ ] [BACKEND] P3. **Business-context enrichment — asset_group / archetype view.** Derive `asset_group` / archetype
      from GCP `labels`/`system_labels` + AWS resource tags → a spend-by-strategy view (restores + generalises what the
      retired narrow page showed). **Gated:** operator is evaluating the By-label view first (2026-07-10); if it adds
      value, enrich by stamping `asset_group` on every launcher + a backfill (AWS also needs cost-allocation tags
      activated). Today's `asset_group` coverage is ~0.16% ($34), so the axis reads mostly "(unlabeled)".
- [ ] [BACKEND] [INFRA] P2. **AWS CUR historical backfill — Athena holds July-2026 only.**
      `aws_billing.cur_uts_cost_usage` contains ONLY `2026-07` (the CUR delivery started in July), so `/ops/costs`
      structurally cannot show pre-July AWS spend; the operator's Cost-Explorer CSV (Jan–Jun, ~$8.6k gross) has zero
      overlap with the CUR. **Gated:** waiting on Ikenna. With the CUR "include historical data" method it is
      essentially just more data + one Glue crawler re-run (~12 months, still tiny — ~150k rows / a few MB — no code
      change if the same table/schema). Else document the AWS tab as **July-2026-onward** (operator: acceptable). Not a
      code bug — a data-source coverage gap.

## Unscheduled P3 enhancements

- [x] ✅ [BACKEND] P3. **Deployed AWS-credential cutover to keyless WIF.** Wire the Athena reader to the keyless WIF
      role (`_code_builds_aws.py` precedent) so the Cloud Run deployment reaches Athena without a static key. Local dev
      uses the ambient profile; only needed at deploy time. **Shipped** `deployment-api@d8add54` (`aws_wif.py`;
      corrected 2026-07-15, plan-reconcile: already resolved per
      plans/active/deployment_api_cache_oom_and_ui_latency_remediation_2026_07_13.md, not still-open).
- [ ] [BACKEND] P3. **Provisional flag: make the AWS cutoff month-aware.** The provisional flag is trailing-2-days for
      BOTH clouds, but AWS re-trues the whole current month (6th–7th). Early-current-month AWS days render as final
      though they are not — make the AWS cutoff month-aware.
- [ ] [UI] [BACKEND] P3. **Credits/discounts as a first-class view.** We already fetch GCP credits; surface gross →
      credits → net + the effective discount rate (how much promo/CUD/SUD is saving).
- [ ] [BACKEND] P3. **Usage quantity + unit → unit economics.** GCP `usage.amount/unit`; AWS
      `line_item_usage_amount/pricing_unit` → $/GB-month, $/vCPU-hour, and GB-stored vs GB-egress for buckets.
- [ ] [UI] P3. **"Other resources" leaf table.** Cloud Run Jobs is ~$2.9k/30d (CPU $2,047 + Mem $882), bigger than any
      single VM, but only vm+bucket leaf tables exist; it surfaces only in the "By resource" breakdown. Add an "other
      resources" leaf.

## Codex SSOTs

- `/codex/05-infrastructure/billing-cost-observability.md` — the API row contract + provider behaviour these extend.
