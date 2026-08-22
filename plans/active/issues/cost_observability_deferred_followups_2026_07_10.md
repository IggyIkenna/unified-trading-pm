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
asset_group:
  [ui] # corrected 2026-07-30 (ui-tranche launch) -- was [meta]; the /costs page's own deferred
  # backlog (repos: deployment-api, deployment-ui)
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
author: unknown
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
context_scope:
  [
    /codex/05-infrastructure/billing-cost-observability.md,
    deployment-api/deployment_api/routes/costs.py,
    deployment-ui/src/pages/CostObservability.tsx,
    /plans/archive/2026_07/cost_observability_ui_2026_07_08.md,
    deployment-api/deployment_api/services/cost_observability,
  ]
---

# Cost Observability — deferred follow-up enhancements

> Migrated verbatim (2026-07-10) from the archived `cost_observability_ui_2026_07_08.md` so the deferred backlog stays
> tracked after archival. All seven were `- [ ]` in that plan's _Deferred / fast-follow_ and _Data-fidelity audit_
> sections. Not dispatched — `assigned_vm: NA`. Two are **operator-gated** (marked below).

## Ruled 2026-08-07 (operator, via consolidated NA-blocker-digest audit)

- [ ] [BACKEND] P2. **RULED — YES, do the business-context enrichment follow-on work.** Stamp `asset_group` on every
      launcher + run a backfill; AWS also needs cost-allocation tags activated. Was gated on the operator evaluating the
      By-label view first (2026-07-10) — ruling: proceed. Original context: today's `asset_group` coverage is ~0.16%
      ($34), so the axis reads mostly "(unlabeled)"; this closes that gap and restores/generalises what the retired
      narrow spend-by-strategy page showed.
- [x] ✅ **RULED — CLOSED as July-2026-onward, final.** AWS CUR historical backfill was originally framed as "just more
      data + one Glue crawler re-run" — **that premise is wrong, corrected 2026-08-07**: the deployed report
      (`aws cur describe-report-definitions` → `uts-cost-usage`) is the LEGACY CUR API, which cannot backfill at all;
      historical data (up to 36mo) is a CUR 2.0 / Data Exports feature requiring (a) creating a brand-new export (zero
      exist today — confirmed via `aws bcm-data-exports list-exports`), (b) filing an AWS Support case naming
      account/export/months, real turnaround time, not self-service, and (c) reconciling CUR 2.0's different,
      incompatible schema (nested columns, 2 new fields) against the existing Athena/Glue setup — genuine engineering
      work, not a toggle. Operator's own fallback ruling applies given the true cost exceeds what made this worth Ikenna
      trying quickly: **`/ops/costs`'s AWS tab is documented as July-2026-onward, accepted as final.** Revisitable later
      with these corrected facts if priorities change — not re-opened by default.

## Unscheduled P3 enhancements

- [x] ✅ [BACKEND] P3. **Deployed AWS-credential cutover to keyless WIF.** Wire the Athena reader to the keyless WIF
      role (`_code_builds_aws.py` precedent) so the Cloud Run deployment reaches Athena without a static key. Local dev
      uses the ambient profile; only needed at deploy time. **Shipped** `deployment-api@d8add54` (`aws_wif.py`;
      corrected 2026-07-15, plan-reconcile: already resolved per
      plans/active/deployment_api_cache_oom_and_ui_latency_remediation_2026_07_13.md, not still-open).
- [x] ✅ [BACKEND] P3. **DONE 2026-08-10 (slot-32, `ui_satellite_ao_dispatch_batch2-001`)** — **Provisional flag: make
      the AWS cutoff month-aware.** AWS provisional cutoff is now the FIRST of the current month (AWS re-trues the whole
      current month on the 6th–7th), threaded as a per-cloud `(gcp_cutoff, aws_cutoff)` pair through every row builder's
      provisional fold + the summary provisional-day count; GCP keeps trailing-2-days untouched. **Shipped**
      `deployment-api@6a536a82d` (QG green; tests: `test_aws_provisional_cutoff_is_first_of_current_month` +
      `test_summary_provisional_days_are_cloud_aware`).
- [x] ✅ [UI] [BACKEND] P3. **DONE 2026-08-10 (slot-32, `ui_satellite_ao_dispatch_batch2-001`)** — **Credits/discounts
      as a first-class view.** `CloudSummary`/`SummaryResponse` carry `discount_rate_pct` (|credit|/gross); the UI's
      gross → credits → net derivation now renders an "≈ X% off" chip (total + per-cloud cards). **Shipped**
      `deployment-api@6a536a82d` + `deployment-ui@b7beaf33b` (pw:L2 ✓ — spec
      `shows the effective discount rate chip next to the gross − credits derivation`).
- [x] ✅ [BACKEND] P3. **DONE 2026-08-10 (slot-32, `ui_satellite_ao_dispatch_batch2-001`)** — **Usage quantity + unit →
      unit economics.** `BreakdownRow` gains `usage_amount`/`usage_unit`/`cost_per_unit`, populated on sku-dimension
      rows ($/GB-month, $/vCPU-hour — net / summed usage where the group bills in ONE unit); the UI renders sortable
      Usage +
      $/unit columns under "By SKU". (GB-stored vs GB-egress for buckets was already covered by
      `storage_gb`/`cost_per_gb` + `cost_by_component`.) **Shipped** `deployment-api@6a536a82d` +
      `deployment-ui@b7beaf33b` (pw:L2 ✓ — spec `surfaces usage quantity + $/unit
      under the sku dimension`).
- [x] ✅ [UI] P3. **DONE 2026-08-10 (slot-32, `ui_satellite_ao_dispatch_batch2-001`)** — **"Other resources" leaf
      table.** Third leaf panel pinned to `resource_kind=other` (Cloud Run Jobs, build workers, …) alongside the
      vm/bucket leaves. **Shipped** `deployment-ui@b7beaf33b` (pw:L2 ✓ — spec
      `renders the Other resources leaf table with non-vm/non-bucket resources`).

## Codex SSOTs

- `/codex/05-infrastructure/billing-cost-observability.md` — the API row contract + provider behaviour these extend.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (infra tranche, dispatch agt-30721a) — Mix of 2 explicitly
  operator-gated items (awaiting operator's own evaluation / awaiting Ikenna) plus 4 unscheduled P3 items the doc itself
  frames as a deliberately-parked backlog, not a defaulted bucket — stays NA as a whole; the 4 P3 items are individually
  plausible future RECLASSIFY candidates for a dedicated split, not actioned this run.
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-03**: reviewed, still accurate — refreshed marker (5 entries).
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **na-eligibility-audit 2026-08-06 (ui tranche, dispatch agt-a6d668)**: KEEP-NA, valid — same as 2026-07-30; 2 items
  explicitly operator-gated (awaiting operator/Ikenna), 4 unscheduled P3 items in a deliberately-parked backlog, not a
  defaulted bucket.
- **context-scout 2026-08-07**: re-scouted; context_scope re-verified (5 entries), unchanged — all 5 still resolve and
  span both the operator-gated items (billing-cost-observability.md, the cost_observability service dir) and the
  unscheduled UI/backend P3 enhancements (costs.py, CostObservability.tsx).
- **Operator ruling 2026-08-07 (interactive session, via consolidated NA-blocker-digest audit)**: both previously
  operator-gated items are now RULED — see the "Ruled 2026-08-07" section above (replaces the old "Operator-gated"
  section). (1) Business-context enrichment: proceed. (2) AWS CUR historical backfill: CLOSED as July-2026-onward final,
  after live verification found the doc's "cheap toggle" premise was wrong (legacy CUR can't backfill; CUR 2.0 needs a
  new export + AWS Support case + schema reconciliation) — the true cost no longer matches what made this worth a quick
  try, per the operator's own cost-conditioned fallback.
- **na-eligibility-audit 2026-08-07 (ui tranche)**: KEEP-NA, valid — both prior operator-gated items are correctly
  retagged to their resolved state (ruled-proceed / ruled-closed) in the same edit, no stale gate tags remain. The
  business-context-enrichment item (now ruled+scoped) plus the 4 unscheduled P3 items are a plausible batched RECLASSIFY
  candidate (bounded/deterministic, no remaining judgment call) — flagged for the orchestrator's conflict-check, not
  actioned here per this audit's own verdict-4 protocol.
- **na-eligibility-audit 2026-08-08 (ui tranche)**: KEEP-NA, valid — closing the loop on 2026-08-07's flagged RECLASSIFY
  candidate. A dedicated scoping check (`ag_closeout_auditor`, same-day 2026-08-08 run) found the
  business-context-enrichment item does NOT clear the bounded-outcome bar after all: 176 VM launcher scripts exist, only
  ~9 route through the one shared label-injection choke point, and a directly-analogous 2026-08-06 operator ruling on a
  sibling infra-tranche issue already declined to treat a near-identical file count as one todo — so the "batched, no
  remaining judgment call" premise from yesterday's marker was wrong on the enrichment half. The 4 unscheduled P3 items
  ARE still cleanly bounded and are now covered by
  `/plans/archive/2026_08/ui_satellite_ao_dispatch_batch2_2026_08_08.md` (drafted today via the satellite-batch pathway,
  `status: draft`, pending operator approval) — the intended mechanism for extracting just the actionable slice, per
  this skill's own "not the corpus's main unblock pathway" guidance, so a whole-doc RECLASSIFY here would only dispatch
  a duplicate of what batch2 already covers once approved. Doc stays NA as a whole. No citation fix yet (batch2 hasn't
  shipped/been approved) — revisit once it has to close the 4 P3 checkboxes with a citation instead of leaving them
  open.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (5 entries), still accurate.
- **round-9 combined RECLASSIFY + satellite-extraction sweep (2026-08-09)**: re-read this doc end to end (5 open items).
  Stale-note correction: `/plans/archive/2026_08/ui_satellite_ao_dispatch_batch2_2026_08_08.md` (which carries the 4
  unscheduled P3 items as its 1 combined todo) is no longer "pending operator approval" — its own Progress Log shows it
  was approved and flipped `status: active` the same day it was drafted (2026-08-08). These 4 items are KEEP-NA-STALE
  (already-duplicated in an active AO plan, not yet shipped) — batch2's own finalize plan
  (`/plans/archive/2026_08/ui_satellite_ao_dispatch_batch2_finalize_2026_08_08.md` todo 1) already owns flipping these 4
  checkboxes with a shipped-sha citation once batch2's todo lands; not pre-flipped here without that evidence. The
  business-context enrichment item (item 1) remains correctly NOT-BOUNDED per the 2026-08-08 scoping finding (176
  launcher scripts, ~9 through the shared choke point) — no change. Doc stays NA as a whole.
- **na-eligibility-audit 2026-08-17 (ui tranche)** [body-hash:91f5e87355264d04]: KEEP-NA, valid — the sole open item
  (business-context/asset_group enrichment, operator-RULED-to-proceed 2026-08-07) still fails the bounded-outcome bar:
  only 45/149 raw-create VM launchers are directly migratable today per
  `infra_satellite_ao_dispatch_batch17_2026_08_16.md` (dated one day before this audit), the other 104 split across 3
  tiers still gated on unresolved operator design decisions. Corroborates, does not contradict, the 2026-08-08/09
  findings already in this doc.
- **context-scout 2026-08-17**: re-scouted; context_scope unchanged (5 entries), still accurate.
