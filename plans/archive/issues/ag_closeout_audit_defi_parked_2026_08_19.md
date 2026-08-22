---
doc_type: issue
title: ag-closeout-audit defi parked findings — 2026-08-19
summary: >-
  Parked findings from the scheduled ag_closeout_auditor run (2026-08-19, tranche=defi, slot 28, dispatch agt-fa5ded).
  Phase 0: 134 AG-primary corpus members, 30 covering docs (17 batch generations), 99 real candidates after excluding
  self-dispatched covering docs. Phase 1 (Workflow, 99 agents, one per doc): 59 orphaned_never_touched + 6
  orphaned_partial_coverage (65 orphaned total) + 19 exclude_cross_cutting (all verified legitimate multi-AG spans,
  zero new mistags found) + 9 archivable_now + 6 archivable_after_planned_work. Phase 3: 9 conflict-cleared items
  drafted into `defi_satellite_ao_dispatch_batch18_2026_08_19.md` (status: draft). Of the remaining 56 orphaned docs:
  23 are already self-dispatching (assigned_vm: planning, feeding the AO backlog directly — no batch item needed), 5
  were already extracted into the still-draft `defi_satellite_ao_dispatch_batch14_2026_08_16.md`, and the rest carry
  only operator/design/human/time-gated remaining work, the large majority independently reconfirmed correctly-NA by
  3-8+ prior na-eligibility-audit rounds each. 10 findings total.
status: superseded
superseded_by: ag_closeout_audit_defi_parked_2026_08_21
nature: issue
asset_group: [defi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ag-closeout-audit, parked, defi, orphan]
related:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/defi_satellite_ao_dispatch_batch18_2026_08_19.md,
    /plans/active/defi_satellite_ao_dispatch_batch18_2026_08_19_finalize.md,
    /plans/active/defi_satellite_ao_dispatch_batch14_2026_08_16.md,
    /plans/active/defi_live_poller_phased_build_2026_08_15.md,
    /plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md,
    /plans/active/elysium_carveout_stubbed_strategy_service_2026_08_12.md,
    /plans/active/defi_cf2_cf3_legacy_canonical_backfill_2026_08_08.md,
    /plans/active/defi_migration_audit_log_2026_07_24.md,
    /plans/archive/2026_08/issues/ag_closeout_audit_defi_parked_2026_08_10.md,
  ]
created: 2026-08-19
parent_epic: defi_master
assigned_vm: NA
priority: P3
last_updated: "2026-08-19"
source: >-
  ag_closeout_auditor scheduled run 2026-08-19 (tranche=defi, slot 28, DISPATCH_ID=agt-fa5ded)
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/archive/2026_08/issues/ag_closeout_audit_defi_parked_2026_08_10.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /plans/active/defi_satellite_ao_dispatch_batch18_2026_08_19.md,
    /plans/active/defi_satellite_ao_dispatch_batch14_2026_08_16.md,
  ]
---

> **📦 ARCHIVED 2026-08-22 (archival pass 2) — SUPERSEDED** by the 2026-08-21 re-run of the same audit
> (`ag_closeout_audit_defi_parked_2026_08_21.md`, active). 0 open todos, no lock. Kept as a historical
> audit-run record.
# ag-closeout-audit defi parked findings — 2026-08-19

Prior parked docs for this tranche (2026-08-06, 08-07, 08-08, 08-10) were checked first — none are in
`plans/active/issues/` any more, all 4 already archived (resolved via the normal archival ritual), so nothing to
reconcile/append before this fresh run per the "reconcile prior dated parked docs first" rule.

## Findings

**Finding 1 — Phase 1 classification summary.** 99 real candidates (134 corpus members minus 35 self-dispatched
covering docs) classified via a Workflow, one agent per doc (effort:medium), against the 30-doc active covering-plan
set. Verdicts: `orphaned_never_touched` 59, `exclude_cross_cutting` 19, `archivable_now` 9, `archivable_after_planned_work`
6, `orphaned_partial_coverage` 6. 2 of 99 agents hit a transient rate-limit error on the first pass; resumed via
`Workflow({resumeFromRunId})` — the other 97 replayed from cache instantly, both retried agents completed clean on
the second pass (99/99 final). No action needed — informational.

**Finding 2 — exclude_cross_cutting verification, zero new mistags.** All 19 `exclude_cross_cutting` docs were read
in full by their Phase-1 agent and independently spot-checked here. Every one carries a genuine multi-AG `asset_group`
tag (3+ real tranches, or the legitimate "spans all 5 AGs + cross-cutting" coordination pattern) — none match the
Orthogonality HARD CHECK's dangerous "exactly one specific tranche + cross-cutting" dual-tag mistag shape. No retag
needed on any of the 19. No action needed — informational.

**Finding 3 — batch18 drafted, 9 items.** `defi_satellite_ao_dispatch_batch18_2026_08_19.md` (+ finalize) drafted
with 9 conflict-cleared bounded items from 8 source docs (full per-item Source: citations in the batch doc itself):
verify the blazestake `lending_indices` OOM fix, build 5 MTDS on-chain feature collectors, wire a Pendle-mirroring
Cloud Scheduler entry, build the operator-ruled Option B staking-return metric, migrate `dex_swaps`→`dex_pool_swaps`,
verify+delete 4 empty test buckets, re-verify the Era-B cefi+tradfi G4 coupling, author 2 missing finalize plans, and
pull a TVL snapshot for the live-poller Tranche 3/4 ordering. `status: draft` — flipping to `active` needs operator
approval (not made here). No action needed here beyond the standing follow-up already tracked as a `- [ ]` on this
same audit's own next-run checklist: **operator, please review and flip batch18 to `active` if approved.**

**Finding 4 — 5 shortlisted candidates already covered by draft batch14.** During shortlisting, 5 of an initial
14-candidate pool (`defi_legacy_fold_relaunch_vm_infra_flakiness_and_oom_2026_08_15`,
`instruments_service_defi_golden_red_capability_drift_2026_08_14`,
`dp_vm_001_mdps_defi_2026_lock_ttl_staleness_budget_mismatch_2026_08_15`,
`mtds_qg_red_morpho_url_and_sports_contract_regression_2026_08_15`, and the wiring items from
`pendle_venue_onboarding_2026_08_16`) turned out to already be extracted verbatim into
`defi_satellite_ao_dispatch_batch14_2026_08_16.md` (still `status: draft`, authored 2026-08-16, not yet
operator-approved). Excluded from batch18 to avoid duplication. No new action — **the standing recommendation is
the same as Finding 3: batch14 has been sitting in draft for 3 days, operator review would unblock both it and these
5 items.**

**Finding 5 — 23 orphaned docs are already self-dispatching, need no batch item.** 23 of the 65 orphaned docs carry
`assigned_vm: planning` + `status: active`/`open` themselves — they already feed the AO backlog directly off their
own `- [ ]` checkboxes (`regen_backlog_from_plan.py`); the "orphaned" verdict here only means no *other* covering doc
cites them, which is expected and correct for a plan that dispatches itself. Examples: `data_pipeline_check_mdps_features_2026_07_20.md`,
`b21_defi_venue_5_unregistered_perp_dex_2026_08_19.md`, `defi_pool_uppercase_recurrence_after_fold_2026_08_11.md`.
No action needed — informational, confirms the audit's own coverage-bar methodology is working as designed rather
than indicating a real gap.

**Finding 6 — `defi_live_poller_phased_build_2026_08_15.md` needs its own dedicated batch2 plan (recommendation).**
Tranches 1-4 (~37 DeFi venue live-connector builds, using the now-proven config-driven base classes from Tranche 0)
remain entirely un-dispatched — genuinely substantial, multi-week scope, deliberately NOT folded into batch18 (see
batch18's own Deferred section). **Recommendation**: author `defi_live_poller_ao_dispatch_batch2_<date>.md` scoped
per-venue or in small venue groups, mirroring how Tranche 0 became the now-archived
`defi_live_poller_ao_dispatch_batch1_2026_08_16.md`. Not drafted here — needs per-venue scoping this audit pass
didn't do. Flagged for a future `/ag-closeout-audit defi` run or direct operator/plan-brainstorm session.

**Finding 7 — Elysium client-delivery docs carry ~88+ open items, all correctly NA (high-visibility standing debt).**
`elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md` (~88 open todos: capital-budget enforcement,
transfer-handler stub replacement, custody-routing/mirroring build, disclosure-review items) and
`elysium_carveout_stubbed_strategy_service_2026_08_12.md` (substantial spec/stub work, status: draft) are both
repeatedly reconfirmed correctly `assigned_vm: NA` by 3+ independent na-eligibility-audit passes each
(client-artefact-sensitive, custody/capital judgment calls). Not re-triaged here — this finding exists purely to give
the operator visibility into the standing size of this backlog, since neither doc's own recent Progress Log entries
surface the aggregate count anywhere else. No action requested unless the operator wants to re-scope any sub-piece
as bounded.

**Finding 8 — `defi_cf2_cf3_legacy_canonical_backfill_2026_08_08.md` scoping pass declined twice now.**
`defi_satellite_ao_dispatch_batch11_2026_08_09.md` (2026-08-09) already assessed and declined this doc's 5-item
scoping pass ("none is a bounded fact yet, per the doc's own dispatch-scope-eligibility self-assessment"); today's
run reached the identical conclusion independently, 10 days later, with zero progress on the doc itself in between.
Non-batchable-taxonomy: needs-its-own-scoping-pass, not conflict-gated (nothing to re-triage against). Flagging
because 2 independent audits agreeing this doc is stuck, unchanged, for 10+ days is itself worth operator attention —
either someone scopes it directly, or it stays parked indefinitely.

**Finding 9 — `defi_migration_audit_log_2026_07_24.md` items 3-4 need a doc-correction pass before they're
extractable.** `defi_satellite_ao_dispatch_batch16_2026_08_17.md` (2026-08-17) already flagged both the FOLD-3
orphan-data_types item and the DeFi collection-gaps retag item as having a stale/inverted premise that needs
rewording before either can be cleanly extracted as a batch todo. Unchanged today (2 days later). Non-batchable-
taxonomy: needs-doc-correction-first. **Recommendation**: a worker (or this same doc's own next editor) should
correct the premise wording directly in the source doc first — that unblocks both items for the next batch's
shortlist without needing another full audit pass.

**Finding 10 — remaining ~40 orphaned docs are settled, correctly-NA standing work (no new information).** The rest
of the 65 orphaned docs beyond Findings 3-9's coverage (roughly 40 docs) carry only operator-gated decisions
(`[OPERATOR]`-tagged human sign-offs, credential asks like the Tenderly fork provisioning in `exec_tenderly_2026_08_15.md`),
design/judgment calls with no bounded done-when (`[DESIGN]`-tagged), or dependency chains gated on other NA work
(e.g. `defi_track5_coverage_mvp_backfill_2026_07_24.md`'s machine `depends_on` gate on the consolidated closeout).
Each is already independently reconfirmed correctly-NA by 3-8+ prior na-eligibility-audit rounds in its own Progress
Log — nothing new to report per-doc, and per the "informational finding is not a todo" rule this is summarized here
rather than individually re-listed. Full per-doc verdict + reasoning for all 99 candidates is preserved in this run's
Workflow journal (`wf_e9c0acb4-3e8`, `agent-orchestrator` transcript store) if a future audit needs to cross-check
without re-triaging from scratch.

## Reconciliation

10 findings identified, 10 findings written above. `parked_findings == entries_written`: confirmed.

## Progress Log

- **2026-08-19 (ag_closeout_auditor, defi tranche, dispatch agt-fa5ded, slot 28)**: authored alongside
  `defi_satellite_ao_dispatch_batch18_2026_08_19.md` (+ finalize) from the day's `/ag-closeout-audit defi` run.
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)
