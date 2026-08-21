---
doc_type: issue
title: "Operator ruling record — /plan-reconcile full-corpus session, 2026-08-15 (items 1-7)"
summary: >-
  Durable, citable home for the seven operator rulings issued interactively during the 2026-08-15 full-corpus
  /plan-reconcile session (a laptop-driven review + apply pass over the plan_reconciler's residual findings docs from
  2026-08-08 through 2026-08-12). Applied across many plan/issue/codex docs this session that would otherwise only cite
  the session itself — a source nothing in the corpus could resolve — this doc gives those citations the traceable home
  check_plan_operator_ruling_evidence.py requires, per the precedent set by
  /plans/active/issues/operator_ruling_record_ao_round5_apply_session_2026_08_08.md.
status: open
nature: issue
asset_group: [meta] # corrected 2026-08-19 (ag-closeout-audit cross-cutting, Phase 1 Workflow) -- was [cross-cutting]; a standing operator-ruling citation register (parent_epic: plan_hygiene_master), zero data-pipeline content
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [admin]
tags: [operator-ruling, evidence, plan-hygiene, quality-gates, plan-reconcile, findings]
related:
  [
    /plans/active/issues/operator_ruling_record_ao_round5_apply_session_2026_08_08.md,
    /codex/04-architecture/agent-orchestrator-scheduled-jobs.md,
    /plans/active/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md,
  ]
created: 2026-08-15
parent_epic: plan_hygiene_master
assigned_vm: NA
execution_scope: local-only
priority: P2
assigned_role: admin
drift_direction: advance-docs
resolved_by:
locked_by:
source:
  "Interactive laptop session, 2026-08-15 — operator answered a batched Q&A while reviewing the plan_reconciler's
  residual findings across 10 tranches"
depends_on: []
context_scope:
  [
    /cursor-configs/skills/plan-reconcile/SKILL.md,
    /codex/12-agent-workflow/operator-gated-blocked-row-lifecycle.md,
    /plans/active/issues/operator_ruling_record_ao_round5_apply_session_2026_08_08.md,
  ]
---

# Operator ruling record — /plan-reconcile session, 2026-08-15

## Provenance

Each ruling below was issued directly in this session in response to a structured question (options + a marked
recommendation), following the same pattern as
`/plans/active/issues/operator_ruling_record_ao_round5_apply_session_2026_08_08.md`. This doc exists so downstream
checkbox-flip citations resolve to a real path instead of an unsourced "operator ruling" phrase.

## The rulings, as issued

- **Item 1 — 6 dead plan_reconciler tranche locks (ao/ci/cross_cutting/infra/prediction/sports, dead since 2026-08-10)**
  — _"Clear now, auto-clear policy going forward."_ Ruling: clear all 6 confirmed-dead locks immediately, and going
  forward the reconciler auto-clears a PM-repo doc's `locked_by: plan_reconciler` lock once AO confirms the
  corresponding dispatch id is `reaped-stale` (Option A of the 3 presented in
  `/plans/archive/issues/plan_reconciler_dead_run_no_lock_ttl_2026_08_12.md` todo 1). Applied: all 6 tranche findings
  docs had their stale lock cleared this session; the actual Option-A auto-clear mechanism was tracked as a follow-up
  todo in that doc (not implemented in this doc-hygiene pass) — since shipped, `agent-orchestrator@bfe8fb28a0`
  (`PlanReconcilerDeadLockSweep`), durable contract now at
  `/codex/04-architecture/agent-orchestrator-scheduled-jobs.md` § "PM-repo dead-lock correlation…".
- **Item 2 — corpus-wide `locked_by: live-defi-rollout` placeholder bug** — _"One-time corpus-wide clear
  (Recommended)."_ Ruling: Option B — treat the literal string `live-defi-rollout` as never a real lock and clear it
  from every doc in `plans/active/` carrying it in one pass, per
  `/plans/active/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md`. Applied via
  `scripts/plans/clear_locked_by_placeholder_2026_08_12.py --apply`; measured live count was only 2 remaining docs in
  the active corpus (earlier batches had already cleared the rest), not the ~96 originally estimated.
- **Item 3 — GCS-delete autonomy contradiction** (`deployment_registry_firestore_migration_2026_07_14.md` "fully
  autonomous" vs. `deployment_registry_firestore_p3_cutover_2026_07_14.md`'s "🔴 BLOCKED — GCS DELETE HELD UNTIL
  OPERATOR CONFIRMS" banner) — _"Fully autonomous, as originally designed."_ Ruling: the migration doc's original
  framing governs; the cutover doc's BLOCKED banner was the stale side. Applied: banner replaced with a non-blocking
  framing, the real unmet GO/NO-GO data preconditions preserved (documentation-only edit, no delete triggered).
- **Item 4 — `ag_closeout_audit_rollout_2026_07_25.md` line-cap split (1010L, over the 1000L hard cap)** — _"Yes,
  approve the extraction (Recommended)."_ Ruling: approved, same mechanical history-extraction pattern as the 2 existing
  precedents in this corpus (`data_completion_sports_history`, `prediction_cross_venue_arb_and_coverage` 1013→376L).
  Applied: Rounds 1-8 history (~850 lines) extracted to a new dated history doc under `plans/archive/2026_08/`
  (`ag_closeout_audit_rollout_history_2026_08.md`); doc now 170 lines.
- **Item 5 — codex path drift across 3 docs** (`/codex/06-coding-standards/ui-testing-layers.md` +
  `/codex/14-customer-journeys/testing/README.md` + `/codex/14-customer-journeys/testing/test-matrix.md` citing
  `tests/playbooks/`, `lib/registry/route-manifest.ts`, `tests/smoke/routes.spec.ts` — none of which exist in
  `unified-trading-system-ui`; real current paths are `tests/e2e/playbooks/` and `*.smoke.spec.ts` naming) — _"Yes,
  correct all 3 to verified-current paths (Recommended)."_ Ruling: approved, since the correct values were confirmed by
  a fresh `ls`/`find` against the live repo before writing them in (not fabricated). Applied this session.
- **Item 6 — `plans/epics/manifest_master.md` 6 hand-authored checkboxes invisible to corpus-wide tooling** — _"Yes,
  extract to a new active-plan doc (Recommended)."_ Ruling: approved. Applied: moved to a new local plan doc,
  `manifest_v9_residual_2026_08_15.md`, under `plans/active/` (`assigned_vm: NA`, `parent_epic: manifest_master`), epic
  body replaced with pointer lines.
- **Item 7 — batch of lower-stakes items already carrying a single clear worker recommendation** (vm-launcher-runbook.md
  Known-Issue note on the freshness-gap race; ao_boot_stub per-todo NA-vs-planning risk re-scoping annotation; 3 ui
  orphaned-successor items flagged as needing a future scoping pass; ci_late_findings xdist-leak title accepted as
  already-adequately-hedged, no edit; cross-cutting Item E —
  `carry_staked_basis_funding_scan_experiment_2026_06_16.md`'s possible-duplicate STRATEGY/MTDS drift-funding todos,
  recommendation was NOT a duplicate, keep both open with an explicit dependency note instead of merging) — _"Yes, apply
  all recommended actions (Recommended)."_ Ruling: approved, apply directly without individual review. Applied this
  session per each item's own worker recommendation.

## What this doc does and does not settle

Same distinction as its 2026-08-08 precedent: this settles _traceability_ (every citing todo now resolves to a real
doc), not independent _authenticity_ verification beyond the operator having answered these exact questions in this live
session — there is no separate confirmation todo needed here since the ruling and its application happened in one
continuous interactive session, not a later worker citing a claimed-but-unverifiable past ruling.

## Progress Log

- **2026-08-15 (interactive /plan-reconcile session)**: created to give this session's 7 batched rulings a traceable
  home; rulings applied across ~9 commits the same session (ao/ci/cross_cutting/infra/prediction/sports/ui tranches, the
  2026-08-08 findings-doc archival, the meta/incident docs, and the locked_by placeholder sweep).
- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries)
- **na-eligibility-audit 2026-08-17** [body-hash:b2d279e3ff692b16]: KEEP-NA, valid -- Zero open todos by design -- this is a pure evidentiary/citation record giving 7 operator rulings issued in one 2026-08-15 interactive session a traceable path so downstream checkbox-flip citations resolve to a real doc (required by check_plan_operator_ruling_evidence.py). Its own 'What this doc does and does not settle' section explicitly states no follow-up confirmation todo is needed since the ruling and its application happened in one continuous session. This is not resolved-and-archivable work; it is a standing reference target that other docs' evidence citations may still point at, matching the pattern of its own precedent doc (operator_ruling_record_ao_round5_apply_session_2026_08_08.md), which the corpus also keeps in plans/active/issues/ rather than archiving. No archive_exempt flag or archival-pending comment is present, unlike doc #11 in this same batch, reinforcing that this doc is not slated for archival.
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
