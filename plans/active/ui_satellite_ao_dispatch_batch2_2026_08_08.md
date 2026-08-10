---
doc_type: plan
title:
  UI satellite docs — AO dispatch batch 2 (1 conflict-cleared todo unlocked by a 2026-08-07 operator ruling; the ui
  tranche's second batch)
summary: >-
  Third `/ag-closeout-audit ui` run (2026-08-08, Autonomous/AO-dispatched, dispatch agt-a0f1b7). Phase 0 found batch 1
  (`ui_satellite_ao_dispatch_batch1_2026_08_06.md`) still `status: draft`, unapproved, 3 days after drafting — this
  batch is independent, additive work, NOT a substitute for approving batch 1. Phase 1 (13-agent Workflow, candidate set
  grew 12→13 since 2026-08-07 — the new member is `ag_closeout_audit_ui_parked_2026_08_07.md`, itself covered)
  re-classified all 13 tranche-primary docs; orphan count held at 9 (composition reconciled — see this doc's own
  Progress Log for the methodology-consistency note). The delta since 2026-08-07 that actually matters: a 2026-08-07
  operator ruling (via the consolidated NA-blocker-digest audit) converted
  `cost_observability_deferred_followups_2026_07_10.md`'s two operator-gated items from blocked to RULED — one CLOSED
  outright (AWS CUR backfill, no action needed), one RULED TO PROCEED (business-context/asset_group enrichment). Per
  this skill's own non-batchable taxonomy, a ruled operator-gated item "becomes a normal batch candidate" — but
  investigating the enrichment item's actual implementation scope (see `## Deferred`) found it is NOT safely bounded
  (176 VM launcher scripts, 143 bypassing the one shared label-injection point, plus a directly-analogous 2026-08-06
  operator ruling on a sibling issue explicitly declining to treat this file-count as one todo) — so it stays deferred,
  evidenced, not drafted. The ONE item that IS conflict-clear and cleanly bounded is the source doc's other content: 4
  previously-"unscheduled" P3 cost-observability UI/backend enhancements, which both this run's Phase 1 agent and the
  sibling `na-eligibility-audit` skill's own 2026-08-07 pass independently flagged as "bounded/deterministic, no
  remaining judgment call." Combined into ONE sequential todo (same two files: `deployment-api`'s costs route +
  `deployment-ui`'s `CostObservability.tsx`) per CLAUDE.md's same-file concurrency rule — a deliberately small second
  batch, not an exhaustive one.
status: active
nature: process
asset_group: [ui]
stage: [meta]
repos: [deployment-api, deployment-ui]
scope: [engineer, admin]
tags: [ui, ao-dispatch, satellite-docs, batch-2, plan-hygiene, close-out, cost-observability]
related:
  [
    /plans/active/ui_consolidated_closeout_2026_07_30.md,
    /plans/active/ui_satellite_ao_dispatch_batch1_2026_08_06.md,
    /plans/active/ui_satellite_ao_dispatch_batch1_finalize_2026_08_06.md,
    /plans/active/ui_satellite_ao_dispatch_batch2_finalize_2026_08_08.md,
    /plans/active/issues/cost_observability_deferred_followups_2026_07_10.md,
    /plans/active/issues/vm_launcher_setup_script_freshness_gap_2026_07_31.md,
    /plans/archive/2026_08/issues/ag_closeout_audit_ui_parked_2026_08_08.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
parent_epic: deployment_and_user_management_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1.4
estimate_calibrated_ai_days: 1.1
assigned_role: ui_developer
effort: max
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    /plans/active/ui_consolidated_closeout_2026_07_30.md,
    /plans/active/ui_satellite_ao_dispatch_batch2_finalize_2026_08_08.md,
    /plans/active/issues/cost_observability_deferred_followups_2026_07_10.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/05-infrastructure/billing-cost-observability.md,
  ]
supersedes:
superseded_by:
depends_on: []
source: >-
  `/ag-closeout-audit ui` run 2026-08-08 (Autonomous/AO-dispatched mode, dispatch agt-a0f1b7, tranche-sharded per the
  ag_closeout_auditor role). Phase 0 re-discovered the ui covering set (closeout + batch1 + batch1_finalize, batch1
  still draft/unapproved); Phase 1 (13-agent Workflow) re-classified all 13 tranche-primary docs; Phase 3 applied the
  mandatory conflict-check to the one item a 2026-08-07 operator ruling newly unlocked, then investigated its actual
  bounded-ness before drafting (see Deferred item 1) rather than assuming "ruled" means "batchable."
---

# UI satellite docs — AO dispatch batch 2

> **`status: active` — operator-approved 2026-08-08, ingested/dispatched.** Drafted autonomously 2026-08-08 by the
> scheduled `ag_closeout_auditor` role; a fresh conflict-check re-verified the original Phase 3 clearance still held
> before dispatch — see `## Operator approval gate` at the bottom for what approving this batch meant, and the Progress
> Log for the re-check. **Independent of batch 1** (`ui_satellite_ao_dispatch_batch1_2026_08_06.md`, flipped `active` in
> the same operator-approval pass) — the two batches' todos touch disjoint files, no collision.

## Why this plan exists (the coverage gap, measured)

The 2026-08-07 `/ag-closeout-audit ui` run (see `issues/ag_closeout_audit_ui_parked_2026_08_07.md` Finding 3)
deliberately did NOT draft a batch 2: "nothing conflict-clear has newly emerged... drafting a competing batch2 against
the same 12 docs before batch1 even ships would be redundant." That changed between 2026-08-07 and 2026-08-08: a
2026-08-07 09:49 UTC+1 operator-rulings commit (`unified-trading-pm@f9672e180`, "record 2026-08-07 operator rulings from
consolidated NA-blocker-digest audit") ruled on BOTH of `cost_observability_deferred_followups_2026_07_10.md`'s
previously operator-gated items — this is new information a same-day-only re-check would not have caught, but a
day-later run does.

Per this skill's own non-batchable taxonomy: "Operator-gated... Once ruled, it becomes a normal batch candidate."
Applied literally, that would mean both ruled items are now batchable. Phase 3's investigation (below, `## Deferred`
item 1) found this is only TRUE for one of the two — the other needs its own scoping pass before it's safely
worker-determinable, despite being "ruled" in the yes/no sense. This is a real distinction: an operator ruling can clear
the _decision_ gate while the _implementation_ gate (bounded, worker-determinable outcome) stays open — this plan treats
those as two separate tests, not one.

## Rules this plan follows

- Every todo ends with `Source: \`<doc>.md\`` naming the satellite doc it was extracted from, plus a **Done when**
  clause.
- The 4 source sub-items are internally independent in principle but share 2 target files
  (`deployment-api/deployment_api/routes/costs.py`, `deployment-ui/src/pages/CostObservability.tsx`) — combined into ONE
  sequential todo per CLAUDE.md's same-file concurrency rule (batch 1's own Deferred item 11 flagged this exact
  collision risk and recommended exactly this combine-or-confirm-independence resolution).
- `sequential:` deliberately UNSET at the plan level — there is only one todo, so plan-level sequencing is moot; the
  todo's own text sequences its 4 internal sub-parts.
- The business-context-enrichment item is in `## Deferred`, not dispatched speculatively, with the scoping evidence that
  justifies holding it back.

## Todos

- [x] ✅ [BACKEND] [UI] P3. **DONE 2026-08-10 (slot-32)** — **Ship the 4 combined cost-observability P3 enhancements as
      one sequential change.** (1) Make the AWS provisional-flag cutoff month-aware — AWS re-trues the whole current
      month on the 6th-7th, so early- current-month AWS days currently render as final though they are not; GCP's
      trailing-2-days provisional logic is correct as-is and untouched. (2) Add a credits/discounts view — GCP credits
      are already fetched; surface gross → credits → net + the effective discount rate (how much promo/CUD/SUD is
      saving). (3) Add usage-quantity → unit-economics — GCP `usage.amount`/`unit` and AWS
      `line_item_usage_amount`/`pricing_unit` → $/GB-month,
      $/vCPU-hour, and GB-stored vs GB-egress for buckets.
      (4) Add an "Other resources" leaf table — Cloud Run Jobs is ~$2.9k/30d (CPU $2,047 + Mem
      $882), bigger than any single VM, but today only vm+bucket leaf
      tables exist; it only surfaces inside the "By resource" rollup. Implement in the order listed (1 is an independent
      bugfix; 2-4 are additive view/table features that can share scaffolding) — do not skip re-reading
      `/codex/05-infrastructure/billing-cost-observability.md` first, it is the API row contract all 4 extend. **Done
      when**: all 4 corresponding checkboxes in the source doc's "Unscheduled P3 enhancements" section are flipped `[x]`
      citing this todo's shipped sha(s), and a fresh `npx playwright test` run on `CostObservability.tsx`'s existing
      spec(s) is green (`pw:L2 ✓`) with the new surfaces exercised. Repo: deployment-api, deployment-ui. Source:
      `cost_observability_deferred_followups_2026_07_10.md` (the 4 items under "## Unscheduled P3 enhancements").
      **DONE**: (1) AWS provisional cutoff first-of-current-month + cloud-aware provisional fold/`provisional_days`
      (`deployment-api@6a536a82d`); (2) `discount_rate_pct` on summary/clouds + UI "≈ X% off" chip
      (`deployment-api@6a536a82d`, `deployment-ui@b7beaf33b`); (3) `usage_amount`/`usage_unit`/`cost_per_unit` on
      sku-dimension rows + sortable Usage/$/unit
      columns (`deployment-api@6a536a82d`, `deployment-ui@b7beaf33b`); (4) "Other resources" leaf table for
      `resource_kind=other` (`deployment-ui@b7beaf33b`). Both repos QG green (api: full suite incl. 2 new tests; ui:
      tsc/eslint/vitest 25/25 — pw:L2 ✓, 3 new specs exercising the new surfaces). All 4 source-doc checkboxes flipped
      citing these shas. Both commits verified ancestors of `origin/live-defi-rollout`.

## Deferred — real remaining work held back, with the reason (per the non-batchable taxonomy)

**TOO-LARGE-OR-RISKY-FOR-A-BATCH-TODO** (needs its own dedicated look, not a first-pass batch slot — despite being
operator-_ruled_, it is not yet operator-_scoped_):

1. **`cost_observability_deferred_followups_2026_07_10.md`'s business-context/asset_group enrichment item** (ruled
   2026-08-07: "YES, do the... work. Stamp `asset_group` on every launcher + run a backfill; AWS also needs
   cost-allocation tags activated.") reads like a single bounded todo in the source doc's own text, but a dedicated
   scoping pass this run found it is not: **176 distinct VM launcher scripts** exist
   (`deployment-service/deployment_service/vm_prefix_registry.py`, 237 registered prefixes), of which **143 call
   `gcloud compute instances create` directly** — only ~9 currently route through the one shared choke point
   (`lc_gcloud_create` in `scripts/vm/lib/launcher_common.sh`) that already threads a `labels_str` param and could
   cheaply grow an `asset_group=` key. Of the 142 launchers that already pass SOME `--labels=`, a sample found live
   key-name drift (`asset_group=` vs `asset-group=` — the hyphenated form is silently NOT captured by the reader's
   `BUSINESS_LABEL_KEYS`), so this is not a mechanical find-and-replace either. The read side has a second, independent
   gap: `cost_observability/models.py` states AWS carries no cost-allocation tags at all today (GCP-only), and no
   `strategy` key exists anywhere in `BUSINESS_LABEL_KEYS` despite the source doc's summary invoking
   "spend-by-strategy." **Direct, on-point precedent**: `issues/vm_launcher_setup_script_freshness_gap_2026_07_31.md`
   (infra tranche — cited, not touched, per the multi-tranche primary-owner rule) surfaced the IDENTICAL
   143-launchers-bypass-the-shared-helper shape for a different concern (freshness-guard propagation) and was explicitly
   operator-ruled 2026-08-06 to NOT treat it as one bounded todo: "This is bigger than a single bounded todo — it is a
   fleet-wide audit + remediation across up to 139 files... Filing as a scoped audit + a design question, not attempting
   the 139-file sweep here." That ruling picked option (a) — migrate high-value raw-create launchers onto
   `lc_gcloud_create` — and a first batch (3 launchers) has already shipped (`deployment-service@6998cc228`), with a
   standing infra-tranche follow-up todo for the remaining ~136. **This enrichment item should piggyback on that
   migration, not fork a parallel effort**: every launcher that migrates to `lc_gcloud_create` for the freshness-guard
   reason gets the `asset_group` label threading essentially for free at the same choke point. Recommend: (a) do not
   draft this as a ui-tranche batch todo at all — the mechanical work is infra-tranche's own migration surface; (b)
   once/if a critical mass of launchers has migrated, a follow-on ui-tranche todo can add the read-side AWS support +
   the `strategy` dimension + a backfill script for already-labeled resources' key-name drift, which IS a bounded,
   ui/cost-observability-scoped task distinct from the launcher migration itself. Not filing a fresh cross-tranche issue
   doc for this cross-reference — the connection is fully documented here and in this plan's own `related:` list; a
   future ui-tranche audit re-checking this item should re-measure the infra migration's progress
   (`vm_launcher_setup_script_freshness_gap_2026_07_31.md`'s own follow-up todo) before re-assessing bounded-ness.

## Operator approval gate

Approving this plan means: flip `status: draft` → `active` here (the finalize plan ships `active` from the start — see
`task_template.md` §4's no-double-gate rule). Until then nothing here is ingested or dispatched (`plans/PLAN_FORMAT.md`
— `status: draft` is not ingested). Before flipping, note:

1. **This is a 1-todo batch, deliberately** — not a sign of a shallow audit. The tranche's real remaining orphan
   population (9 of 13 docs) is still dominated by the same operator-gated/time-gated/too-large categories batch 1's
   Deferred section already documented; today's audit found exactly one item that newly cleared to genuinely-bounded,
   and drafted exactly that.
2. **Batch 1 (`ui_satellite_ao_dispatch_batch1_2026_08_06.md`) was approved + dispatched in the same 2026-08-08 pass** —
   approving this batch did not require approving that one (independent decisions), but the operator reviewed both
   together given they were both pending ui-tranche satellite work.
3. **The deferred business-context-enrichment item is NOT waiting on this plan** — it needs a scoping decision on the
   infra-tranche launcher-migration side first (see `## Deferred` item 1). No action needed here beyond awareness.

## Codex SSOTs (read before touching the todo)

`/codex/05-infrastructure/billing-cost-observability.md` · `/codex/05-infrastructure/vm-launcher-runbook.md` (context
for why Deferred item 1 was NOT drafted) · `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`
· `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`

## Progress Log

- **2026-08-08 (ag_closeout_auditor, dispatch agt-a0f1b7, slot 11)** — Drafted following the third
  `/ag-closeout-audit ui` run. Phase 1 (13-agent Workflow) re-classified all 13 tranche-primary docs (candidate set grew
  12→13, new member `ag_closeout_audit_ui_parked_2026_08_07.md` self-classified `archivable_after_planned_work` — its
  own recommendations already fully folded into `ui_consolidated_closeout`'s P2 todo #5 and batch1's standing approval
  gate, no new action needed on it). **Methodology-consistency note**: today's 13 independent Phase-1 agents split on
  whether a Deferred-section-only mention (no actual dispatched Todo) counts as `orphaned_partial_coverage` or
  `orphaned_never_touched` — 2 agents (`consolidator_throughput_backlog_monitor`,
  `cost_observability_deferred_followups`) used a more generous bar than the other 11 and than the 2026-08-06/08-07
  runs' established convention (only a doc's actual dispatchable `## Todos` — not `## Deferred` prose — counts as
  coverage). Reconciled to the established stricter bar for this doc's own headline figure: **orphan count 9 of 13** (2
  `orphaned_partial_coverage`: `data_status_cell_grid_rearchitecture_2026_07_18.md`,
  `artifact_pipeline_observability_2026_07_17.md` — both correctly partial because batch1's actual Todos 1/3 cite them;
  7 `orphaned_never_touched`). This is flat against 2026-08-07's 9 of 12 in raw count (the +1 denominator is the new,
  non-orphaned 13th doc) — full detail in `issues/ag_closeout_audit_ui_parked_2026_08_08.md`. Also found this run:
  `artifact_pipeline_observability_2026_07_17.md` carries an 11th genuinely-open item with zero checkbox representation
  (a "Still open" sentence trailing an `[x]`- checked parent bullet, line 683) that both prior audit passes and the
  doc's own na-eligibility-audit pass missed — not fixed here (outside this skill's write-scope for a non-covering
  candidate doc), flagged in the parked-findings doc for na-eligibility-audit's next pass. Also: Phase 7 of that same
  doc (the P0 CPU-throttling investigation) is now fully resolved (2026-08-07 operator ruling, confirmed live) —
  batch1's own Deferred item 8 wording is now slightly stale on this point (still describes it as open); no action
  needed since it resolved independently of any covering doc. Conflict-check run before drafting (grepped `infra`/`ao`
  tranche batches + the full corpus for `CostObservability.tsx`/`costs.py`/business-context-enrichment mentions) — zero
  collisions found; the 2 incidental `costs.py` hits (`ci_pipeline_speed_and_cost_redesign_2026_08_05.md`, read-only
  reference; `infra_satellite_ao_dispatch_batch1_2026_07_26.md`, an already-shipped historical `[x]` item) are both
  benign, confirmed by direct read.
- **2026-08-08 (operator approval)**: flipped `status: draft` → `active` after a fresh conflict-check re-verified this
  batch's own Phase 3 clearance still held: (a) no `deployment_and_user_management_master` sibling batch drafted after
  this one exists; (b) re-grepped `CostObservability.tsx`/`costs.py` across the full active corpus — same 2 benign
  incidental hits as at drafting time, no new claim; (c) `ui_consolidated_closeout_2026_07_30.md` unchanged since this
  batch's drafting. `locked_by` unset. Batch 1 (`ui_satellite_ao_dispatch_batch1_2026_08_06.md`) approved in the same
  pass — confirmed disjoint target files, no collision. Dispatching.
- **context-scout 2026-08-09**: populated/refreshed context_scope (6 entries).
