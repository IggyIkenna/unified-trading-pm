---
doc_type: issue
title:
  AO-tranche full-content scope audit (2026-07-31) — the 26 excluded false-positives, the retag decision, and 2 smaller
  findings surfaced while updating the tracker
summary: >-
  Durable home for findings from the 2026-07-31 full-content re-audit of
  `ao_open_issues_consolidated_close_out_2026_07_17.md` (the "ao" tranche's open-issues tracker). That session pass read
  all 88 repos/parent_epic-matched issue-doc candidates individually (not just the repos-breadth heuristic) and landed 3
  durable outcomes in the tracker itself — 62 confirmed genuine AO issues (36 already correctly `asset_group:
  [ao]`-tagged, 26 genuinely AO content sitting under a mistagged `asset_group`), all now referenced in the tracker's
  classification table. This doc captures the 4 things that did NOT fit in the tracker (already at its 1000-line hard
  cap with zero headroom) or that are genuinely operator-gated rather than auto-resolvable: the full 26-doc exclusion
  list with per-doc reasoning (§1), the retag decision for the 23 mistagged docs (§2), the duplicate-issue-doc merge
  (§3), and a stale internal count in the tracker (§4).
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ao, tranche-audit, asset-group, mistag, duplicate, tracker]
related:
  [
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /plans/archive/2026_08/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: 2026-07-31
last_updated: 2026-08-21
author: unknown
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
context_scope: [/plans/archive/2026_08/ao_open_issues_consolidated_close_out_2026_07_17.md, /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md, /cursor-configs/skills/ag-closeout-audit/SKILL.md, /plans/archive/issues/ao_dashboard_backlog_detail_queue_lag_e2e_flaky_2026_07_26.md, /plans/archive/issues/backlog_detail_spec_queue_lag_sort_order_flake_2026_07_30.md]
source:
  [
    "operator session 2026-07-31 — 'check and see which are tracked and which are not tracked and update the tracker doc
    properly'",
  ]
---

# AO-tranche full-content scope audit — findings that didn't fit in the tracker

## §1 — The 26 excluded false-positives, with reasoning

Started from the union of `repos:` contains `agent-orchestrator` OR `parent_epic` in
`{orchestrator_master, agent_operating_framework_master}` across `plans/active/issues/*.md` (89 candidates, 88 after
excluding 1 already-`resolved` doc). Read every title/summary/`asset_group`/repos-breadth individually rather than
trusting the filter. 62 survived as genuinely AO-subject (now in the tracker); these 26 did not — grouped by why:

**Broad multi-repo audits where agent-orchestrator is one of several repos, not the subject** (4):
`ao_scheduled_skills_benchmark_and_ruled_decisions_session_2026_07_30` (a 40-decision mega-session log,
`asset_group: [cross-cutting]`, 5 repos), `autonomous_session_operator_decisions_2026_07_25`
(`asset_group: [cefi, defi, tradfi, prediction, sports, cross-cutting]`),
`capability_wizard_analysis_findings_2026_06_11` (`asset_group: [cross-cutting]`, 6 repos,
`parent_epic: strategy_master`), `catalogue_census_equivalents_inventory_2026_07_24` (data-catalogue census question, 5
repos).

**PM/audit-tooling bugs (the bug lives in the audit skill or the plan-hygiene machinery, not in agent-orchestrator's own
runtime)** (9): `ag_closeout_audit_orphan_definition_and_digest_citation_defects_2026_07_30`,
`ag_closeout_audit_scope_widening_triage_2026_07_26`, `docs_reconcile_autonomous_sweep_2026_07_30`,
`na_and_ag_closeout_audit_population_overlap_2026_07_31`,
`na_audit_multi_tranche_shared_doc_ownership_and_draft_p0_park_2026_07_30`,
`na_doc_tranche_inventory_stale_citation_membership_cross_contamination_2026_07_29`,
`plan_quality_four_line_defense_architecture_2026_07_23`,
`quickmerge_sentinel_race_retry_storm_under_pm_doc_push_contention_2026_07_21`, `reference_path_convention_2026_07_23`.

**Genuinely unrelated content, matched the filter incidentally** (7):
`deployment_api_artifact_pipeline_health_test_date_drift_flake_2026_07_29` (deployment-api test flake),
`deployment_api_sigabrt_crash_loop_unresolvable_sha_citation_2026_07_31` (deployment-api bug; an agent-orchestrator SHA
is just cited as evidence), `e2e_login_persona_handoff_helper_stale_2026_07_22` (generic UI E2E helper),
`mtds_gas_fees_migration_script_unbounded_memory_2026_07_30` (`asset_group: [defi]`, unrelated),
`production_readiness_checklist_file_missing_2026_07_24` (missing deployment-service config file),
`unified_trading_system_ui_codex_violations_far_exceed_estimate_2026_07_21`,
`wizard_smoke_suite_pre_existing_failures_2026_07_28`.

**Shared-host/CI-tranche infra affecting every repo, not an AO dispatch/watchdog bug specifically** (5):
`fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29`, `orchestrator_gcloud_active_account_wif_poisoning_2026_07_25`
(correctly `asset_group: [ci]`), `s5_7_required_docs_gaps_2026_07_29` (`parent_epic: plan_hygiene_master`),
`shared_host_home_filesystem_full_2026_07_26`, `sit_validated_tree_treadmill_blocks_breaking_promotes_2026_07_20`
(correctly `asset_group: [ci]`), `vm_billing_waste_first_audit_and_preflight_gate_design_2026_07_24`.

**These are exclusions from the "ao" tranche's own tracker, not a claim the underlying work doesn't matter** — several
(`plan_quality_four_line_defense_architecture`, `shared_host_home_filesystem_full`) were already flipped
`assigned_vm: NA`/`execution_scope: local-only` earlier the same session as part of a broader 25-doc AO-plan
reclassification; that flip isn't wrong even though the topical "ao tranche" label is — moving PM-process/shared-infra
work out of the AO dispatch queue to be done locally is a defensible outcome regardless of which tranche technically
owns it. **Operator ask**: confirm this exclusion list is right, or name which of the 26 should actually be pulled into
the ao tranche's tracker.

## §2 — Operator decision needed: retag the 23 mistagged docs?

23 issue docs are genuinely about agent-orchestrator internals (dispatch, worker lifecycle, backlog regen, escalation,
orchestrator VM health) but carry `asset_group: meta`/`cross-cutting`/`infrastructure` instead of `[ao]`. Full list is
in the tracker's own new classification-table row (`ao_open_issues_consolidated_close_out_2026_07_17.md`, bucket
"genuine AO content but asset_group MISTAGGED"). Per `cursor-configs/skills/ag-closeout-audit/SKILL.md`'s own stated
rule, `asset_group` (not `parent_epic`) is the PRIMARY membership signal for the `ao`/`ci`/`infrastructure` tranches —
so as long as these stay mistagged, they are invisible not just to this tracker but to `/ag-closeout-audit ao` itself.

**Not done here**: retagging is 23 separate one-line frontmatter edits (`asset_group: [meta]` → `[ao]` etc.) — small and
mechanical individually, but a distinct scope from "update the tracker doc," and worth a single batched pass rather than
doing it piecemeal while also working the issues themselves.

## §3 — Duplicate issue docs need merging

`ao_dashboard_backlog_detail_queue_lag_e2e_flaky_2026_07_26.md` and
`backlog_detail_spec_queue_lag_sort_order_flake_2026_07_30.md` both describe the exact same symptom —
`backlog-detail.spec.ts`'s Queue-lag/timestamp-sort Playwright tests failing reproducibly on a clean tree — filed 4 days
apart by different sessions, neither referencing the other. Needs a human read of both (they may differ in root-cause
theory even if the symptom matches) before deciding which one is the survivor and which gets `superseded_by`/archived.

## §4 — Stale count in the tracker doc (found while trimming for line-cap room, not fixed)

`ao_open_issues_consolidated_close_out_2026_07_17.md`'s "Split-out child plans" section still says **"14 `- [ ]` MOVED
items stay open... (`ao_scheduled_agent_hygiene` ×3, `ao_fleet_infra_hardening` ×5, `ao_fleet_observability_kpis` ×6)"**
— but that same section's own table now shows `ao_fleet_observability_kpis_2026_07_20.md` as **✅ ARCHIVED 2026-07-31,
9/9, no residual**. Its 6 MOVED items should have moved into the "15 MOVED items whose child is archived, flipped `[x]`"
bucket (making it 21) but weren't. Fixing this correctly means finding each of the 6 individual MOVED todos in the
tracker's Phase sections and flipping them `[x]` with a `DONE via ao_fleet_observability_kpis_2026_07_20.md` pointer
(the established pattern already used for the other archived children) — not just editing the summary count.

## Todos

- [x] ✅ [OPERATOR] P2. **Rule on §1** — confirm the 26-doc exclusion list, or name which should be pulled back into the
      ao tranche. **RULED 2026-08-06 (operator, interactive), recorded here in
      `ao_tranche_full_content_audit_findings_2026_07_31.md`: BLANKET CONFIRMATION — all 26 exclusions stand, none
      pulled back.** The gate offered "an explicit yes/no per contested doc, or a blanket confirmation"; the operator
      chose blanket. Basis: the audit read all 88 candidates individually rather than trusting the filter, and each of
      the 26 carries a stated reason grouped into four coherent categories (4 broad multi-repo audits, 9 PM/audit-
      tooling bugs whose defect lives in the audit skill or plan-hygiene machinery rather than agent-orchestrator's
      runtime, 7 incidentally-matched unrelated docs, 5-6 shared-host/CI-tranche infra items). The distinction being
      drawn — is agent-orchestrator the SUBJECT of the doc, or merely one of several repos it touches? — is the right
      one. **This changes no work, only tracker ownership**: as §1 itself states, these are exclusions from the ao
      tranche's tracker, not a claim the underlying work does not matter.
- [x] ✅ [OPERATOR] P2. **Rule on §2** — approve (or defer) the 23-doc `asset_group` retagging pass. **RULED 2026-08-06
      (operator, interactive), recorded here in `ao_tranche_full_content_audit_findings_2026_07_31.md`: APPROVED, folded
      into normal issue-doc work — NOT a bulk pass.** Both halves of the gate are answered: go/no-go = GO; who does it =
      whichever agent next touches each doc for an unrelated reason. Rationale for opportunistic over bulk: the retag is
      genuinely worth doing (mistagging is what forced this audit in the first place, and every tranche-scoped audit
      keeps re-inheriting the noise), but a 23-file bulk edit landing against ~15 concurrent slots is a collision magnet
      for zero urgency. Opportunistic folding reaches the same end state with near-zero contention risk. Standing
      instruction captured as its own todo below so it survives as tracked work rather than as a decision buried in a
      Progress Log.
- [ ] [DOC] P3. **Standing (no deadline): when you touch any of §2's 23 mistagged docs for any other reason, correct its
      `asset_group` to include `ao` in the same commit.** The authoritative list is §2 of this doc — read it there, do
      not re-derive it. Do NOT open a doc solely to retag it, and do NOT batch these: the 2026-08-06 operator ruling
      chose opportunistic folding precisely to avoid a 23-file bulk edit under concurrent-slot contention. **Done
      when**: §2's list is exhausted, at which point this doc's remaining §3/§4 items decide its archival. Until then
      this todo is expected to sit open for a long time — that is the intended shape, not staleness.
- [x] [SCRIPT] P2. **§3 — DONE 2026-08-08.** Survivor: `ao_dashboard_backlog_detail_queue_lag_e2e_flaky_2026_07_26.md`
      (`status: resolved`, real fix `agent-orchestrator@e761cb1`). Added the missing
      `superseded_by: [ao_dashboard_backlog_detail_queue_lag_e2e_flaky_2026_07_26]` to the duplicate's frontmatter (it
      already had `status: resolved` + `resolved_by:` prose but no machine-readable pointer), and folded its two extra
      root-cause candidates into the survivor's body for the historical record. Both docs already archived — no move
      needed. Source: this doc §3. — unified-trading-pm (this commit)
- [x] [SCRIPT] P3. **§4 — DONE 2026-08-08, but not as originally scoped.** Live-checked all 3 named children
      (`ao_scheduled_agent_hygiene` ×3, `ao_fleet_infra_hardening` ×5-across-4-blocks, `ao_fleet_observability_kpis` ×6)
      — every one of the 14 MOVED-item checkboxes was **already** `- [x]` with a `DONE via <child>` pointer (verified by
      direct read, not just grep); the stale part was only the summary sentence claiming they "stay open because their
      child plan is still active" when the status table two paragraphs up already shows all 3 archived. So the original
      todo's "correct the 14 to 8" premise was itself stale (only `ao_fleet_observability_kpis` had been assumed
      unfixed) — corrected the sentence to state all 29 MOVED items in the tracker are closed, none open. Source: this
      doc §4. — unified-trading-pm (this commit)

## Progress Log

- **na-eligibility-audit 2026-08-01** (autonomous, tranche `ao`, dispatch agt-8e95ca, slot 2): KEEP-NA, valid — §1 and
  §2 are literally titled "Operator ask"/"Operator decision needed" (explicit go/no-go on an exclusion list and a
  retagging pass). §3 states in its own body it "needs a human read of both... before deciding which one is the
  survivor" despite the `[SCRIPT]` tag. Only §4 (flip 6 already-archived `MOVED` items + fix a stale count) is purely
  mechanical, but 3 of 4 todos are human-judgment-gated so the doc as a whole correctly stays NA.
- 2026-07-31: filed during `/pre-compact` — these 4 findings existed only in chat during the live audit session and
  would have been lost at compaction; the tracker doc itself has zero line-cap headroom to hold them (999/1000 lines).
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries). Skipped one candidate entry —
  `/plans/archive/2026_08/ao_open_issues_consolidated_close_out_2026_07_17.md` (already in `related:`) — per this run's
  explicit instruction not to read or touch that file (under active concurrent edit by a different session).
- **context-scout 2026-08-03**: re-verified context_scope (4 entries, unchanged) — all still resolve; this is a
  code-free tracker/audit-findings doc (no source-code target applies) so the codex+plan-doc list stands.
- **na-eligibility-audit 2026-08-04** (autonomous, tranche `ao`): KEEP-NA, valid — re-affirmed, no content change (still
  4 open todos: §1/§2 are explicit `[OPERATOR]` rulings, §3 self-states it needs a human read, §4 is the lone mechanical
  item but the doc stays whole-NA since `assigned_vm` is doc-granular). Cross-validated: the same-day sibling
  `/ag-closeout-audit ao` batch6 run also declined this doc as operator-gated.
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (4 entries), unchanged.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
- **context-scout 2026-08-07**: refreshed context_scope (5 entries) — added
  `/plans/archive/2026_08/ao_open_issues_consolidated_close_out_2026_07_17.md` (the tracker doc) as the first entry:
  §4's open todo directly edits it (flip 6 MOVED items + fix a stale count), and the 2026-08-01 marker's reason for
  skipping it (a since-passed instruction not to touch a file under concurrent edit) no longer applies.

- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — re-affirmed, no content change. §1/§2's operator rulings both
  now `[x]` (closed 2026-08-06); the standing §2 opportunistic-retag todo and §3's human-read-needed merge stay
  genuinely open. §4 (flip 6 MOVED items + fix a stale count) is the one purely mechanical item, flagged separately
  below as MISCLASSIFIED_LIKELY_AO_ELIGIBLE — consistent with this doc's own established reasoning that the whole doc
  still correctly stays NA since `assigned_vm` is doc-granular and the other open items are judgment-gated.
- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 1)**: KEEP-NA, valid — §3 and §4 are both now `[x]`
  (done 2026-08-08). The sole remaining open item is the standing §2 opportunistic-retag todo, which is explicitly NOT a
  standalone dispatchable task by its own text ("Do NOT open a doc solely to retag it, and do NOT batch these" — the
  2026-08-06 operator ruling specifically chose opportunistic-only over a bulk pass to avoid a 23-file collision
  magnet). A single-item doc whose only content is an anti-batch instruction cannot be satellite-extracted without
  violating the instruction itself.
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries)
- **na-eligibility-audit 2026-08-17 (ao tranche)** [body-hash:f91ba0117fea57b5]: KEEP-NA, valid — sole remaining todo is a standing opportunistic-retag instruction under an explicit 2026-08-06 operator ruling against batching it; never-relitigate case (a)/(c) applies directly.
- **na-eligibility-audit 2026-08-21 (ao tranche batch 2/3)**: KEEP-NA, valid — sole remaining item is the standing §2 opportunistic-retag instruction, explicitly barred from batching by the 2026-08-06 operator ruling; re-affirms 8 prior audit passes.
- **2026-08-21 — ruling D1 (Stale meta-doc disposition)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch authority,
  AUTONOMOUS_AGENT_RULES rule 2): Approve all — repeated audits agree these are churn, not live tasks; the two
  keep-open items and the one split are the only exceptions. Source:
  /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger. **No retag applied here** — this doc's
  sole open todo (the standing §2 opportunistic-retag instruction) is explicitly one of D1's own named "keep-open"
  exceptions: it is intentionally standing with no deadline ("this todo is expected to sit open for a long time —
  that is the intended shape, not staleness"), the opposite of the churn D1 rules on.
