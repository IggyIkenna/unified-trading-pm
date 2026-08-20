---
doc_type: issue
title: "2026-08-18 plan_reconciler — epic-scoped run over plan_hygiene_master"
summary: >-
  First epic-scoped `/plan-reconcile plan_hygiene_master` run (the new 2026-08-18 epic-scoped mode, as opposed to a
  tranche/`all` sweep). Scope: the epic file itself plus all 22 docs where `parent_epic: plan_hygiene_master` matches
  exactly. Phase -1 reconciled all 6 prior standing findings/ruling docs against fresh state first. Given this epic
  IS the plan-reconciler's own dogfood output, the corpus was already extremely well-maintained by repeated
  self-auditing (na-eligibility-audit + context-scout + prior plan_reconciler passes) — this run found 2 genuine
  actionable items (both applied, working-tree only, uncommitted per this session's explicit instruction) and 1
  genuine open question routed without a forced answer.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, reconciliation, plan-hygiene, epic-scoped, findings]
related:
  [
    /cursor-configs/skills/plan-reconcile/SKILL.md,
    /plans/epics/plan_hygiene_master.md,
    /plans/active/issues/plan_reconciler_findings_all_2026_08_15.md,
    /plans/active/issues/plan_reconciler_findings_all_2026_08_12.md,
  ]
created: "2026-08-18"
parent_epic: plan_hygiene_master
assigned_vm: NA
execution_scope: local-only
priority: P3
assigned_role: review
drift_direction: none
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source: "Epic-scoped /plan-reconcile plan_hygiene_master run, laptop-driven sub-agent session, 2026-08-18. DO-NOT-SHIP
  constraint in force (shared checkout under contention) — every edit below is applied to the WORKING TREE only,
  uncommitted; lead session ships."
depends_on: []
context_scope:
  [
    /cursor-configs/skills/plan-reconcile/SKILL.md,
    /plans/epics/plan_hygiene_master.md,
    scripts/plan-hygiene/epic_report_data.py,
  ]
---

# plan_reconciler — epic-scoped run over `plan_hygiene_master`, 2026-08-18

**Scope definition used**: `rg "^parent_epic: plan_hygiene_master$" plans/active/*.md plans/active/issues/*.md` — 22
child docs (confirmed against the docspec-aligned exact-match convention this skill's epic-scoped mode specifies, not
`regenerate_active_plan_inventory.py`'s broken filename-substring "orphan" check). Plus the epic file
(`plans/epics/plan_hygiene_master.md`, 249 lines) and the normative refs. Every one of the 22 child docs + the epic
file was read in FULL by this run (no sampling) — corpus small enough for direct single-session coverage, no
sub-agent hunter fan-out needed.

**⚠️ NOT SHIPPED — DO NOT SHIP constraint in force this session.** Every fix below is applied to the working tree
only (uncommitted). Lead session reviews `git status`/`git diff` and ships via the normal `docs(plans):` /
`safe-doc-push.sh` path.

## Phase -1 — prior findings/ruling docs reconciled first

6 standing docs checked against fresh state (none needed a fix from this pass — all already correctly maintained by
their own repeated na-eligibility-audit/context-scout self-audits):

- `plan_reconciler_findings_all_2026_08_12.md` — 24 open items, all independently re-confirmed genuinely open
  (cross-doc redirects / corpus-wide judgment calls / operator-gated) by a 2026-08-17 na-eligibility-audit pass that
  read the full 758-line doc. No action.
- `plan_reconciler_findings_all_2026_08_15.md` — 1 open item (systemic `last_updated` staleness, routed to a
  corpus-wide script-fix owner, correctly `assigned_vm: planning`). No action.
- `plan_reconciler_findings_prediction_2026_08_16/17/18.md` — each still carries genuinely-open 12h-grace-window
  mechanical re-checks and cross-tranche routing notes, all re-confirmed by same-day na-eligibility-audit passes as
  recently as today. No action (these belong to the `prediction` tranche's own daily cadence, not this epic-scoped
  pass to re-execute).
- `plan_reconciler_findings_sports_2026_08_18.md` — carries 2 explicit "action for the next sports pass" items
  (archive `sports_fixtures_schedule_wrong_schema_day_2026_04_14.md` + work
  `sports_consolidated_native_ao_extract_2026_07_25_finalize.md`'s todos 1-3) that were deferred because their
  referrer hub (`sports_consolidated_closeout_2026_07_19.md`) was inside its 12h grace window at write time. Those
  3 target docs are `parent_epic: sports_master`, not `plan_hygiene_master` — **out of this epic's scope to execute**
  (touching them belongs to a `sports`-tranche-scoped `/plan-reconcile` pass, which this run deliberately does not
  duplicate, per the sports tranche's own very active concurrent dispatch activity today). Noted for the next sports
  pass, not executed here.
- `operator_ruling_record_plan_reconcile_session_2026_08_15.md` — 0 open todos by design (standing evidentiary
  record for 7 operator rulings). No action.

## Phase 0/1/2 — the epic file + 22 child docs

Read in full. Findings:

### Applied (2, working-tree only)

1. **`plans/epics/plan_hygiene_master.md:174` — done-but-unchecked, HARD evidence.** The epic's own open
   `- [ ] [PLAN] P1` "Stale 2026-05-23 deadline framing" item named 3 targets
   (`master_to_live_defi_2026_05_23.md`, `aws_cloud_toggle_and_backfill_parity`, `human_work_backlog`) as still
   carrying future-tense pre-cutover framing in `plans/active/`. Verified fresh: all 3 are now archived —
   `master_to_live_defi_2026_05_23.md` at `plans/archive/2026_07/` (`status: complete`),
   `aws_cloud_toggle_and_backfill_parity_2026_05_22.md` + `human_work_backlog_2026_05_20.md` both at
   `plans/archive/2026_05/`. `plans/active/INDEX.md` no longer cites `master_to_live_defi` at all (0 hits, confirmed
   via `rg`). Flipped `[x]` citing this evidence.
2. **`plans/active/issues/plan_commit_sha_evidence_unresolvable_0f9b8a65ca_2026_08_10.md` — stale
   `archive_exempt: true` bridge, real archive candidate.** Both todos have been `[x]` since 2026-08-10; the doc's own
   Progress Log explicitly called `archive_exempt: true` "TEMPORARY... the archive will be a separate follow-up
   commit immediately after this one" — that follow-up commit never landed, and the doc sat 8 days past its own
   stated archival point. Re-ran `check_plan_commit_sha_evidence.py` fresh before archiving: `3127 citations, 0
   unresolvable` — still green, the fix has held. All 3 corpus referrers are themselves already under
   `plans/archive/2026_08/` (no active-corpus referrer needed a path fix). Ran the archival ritual: banner added,
   `archive_exempt` dropped, `status: open` → `resolved`, moved to `plans/archive/2026_08/issues/`.

### Routed — genuine open question, NOT applied (evidence doesn't clear the "provable" bar)

3. **4 findings docs' `parent_epic` value is a plausible-but-unconfirmed candidate for repoint** —
   `plan_reconciler_findings_prediction_2026_08_16.md`, `_17.md`, `_18.md`, and
   `plan_reconciler_findings_sports_2026_08_18.md` all carry `parent_epic: plan_hygiene_master`, while every OTHER
   tranche's per-tranche findings doc in this corpus (cefi→`cefi_master`, defi→`defi_master`, tradfi→`tradfi_master`,
   ci→`ci_master`, cross-cutting/infra→`security_and_cross_cutting_master`, ui→
   `deployment_and_user_management_master`) points at its own tranche's real content epic instead — a 7-vs-2
   asymmetry, and `predictions_master`/`sports_master` demonstrably exist as valid, populated epics. Initially
   suspected as drift and a repoint candidate. **Ran the actual mechanical check before concluding anything**
   (`check_parent_epic_alignment.py`, the same one Phase 0 uses) — it rates all 4 `OK`/plausible for
   `plan_hygiene_master` (scores 5-6, not a mismatch flag), which undercuts rather than confirms the repoint
   hypothesis: these ARE reconciler-mechanism run-journals (na-eligibility-audit/context-scout/plan_reconciler
   process vocabulary throughout), not pure prediction/sports-market content, so `plan_hygiene_master` is
   keyword-defensible too. Per this skill's own calibration bar ("provable" means a check run THIS turn that settles
   it, not a pattern-match inference) — this does NOT clear the bar. **Not auto-applied.** Recorded here as a genuine
   open preference question (both answers defensible; no forced `[WORKER REC]`) for the operator/lead session:
   **Option A** — repoint the 4 docs to `predictions_master`/`sports_master` to match the majority 7-tranche
   convention. **Option B** — leave as `plan_hygiene_master` (matches the checker's own plausibility verdict + the
   `all`-scoped findings docs' existing convention of staying under the meta epic). No action taken pending a ruling.

### Confirmed correct, no action (spot-checked, not exhaustively re-listed)

- `codex_vs_repo_docs_ssot_audit_2026_06_01.md`'s 2 remaining open P1 todos (MTDS `DEPLOYMENT_GUIDE_FEMI.md`/
  `SHAHRIYAR_DEPLOYMENT_INFRA_SPEC.md` finish; strategy-service (15) FIX-STALE/REDIRECT pass) are genuinely still
  undone — verified live: both flagged MTDS docs still exist on disk in `market-tick-data-service/docs/`, and
  `strategy-service/docs/` still carries the flagged `STRATEGY_MODES.md`/`CLI_REFERENCE.md`/`BACKTEST_ENGINE.md`
  files unchanged. Not done-but-unchecked — real remaining repo work.
- `codex_vs_repo_docs_ssot_audit_2026_06_01_finalize_2026_07_27.md`'s sole todo stays correctly machine-gated
  (`depends_on`+`gate_on_depends: true` on the parent plan's still-open todos above).
- `issue_docs_remediation_sweep_2026_06_02.md`, `governance_sweep_deferred_followups_2026_08_06.md`,
  `context_scope_marker_claims_exceed_frontmatter_count_2026_08_06.md`,
  `na_eligibility_body_hash_unstable_across_marker_appends_2026_08_17.md`,
  `na_inventory_counts_fenced_code_block_checkboxes_as_open_todos_2026_08_02.md`,
  `na_marker_helper_hardcoded_root_pm_path_2026_08_18.md`,
  `na_eligibility_audit_same_tranche_duplicate_concurrent_dispatch_2026_08_18.md`,
  `pm_archive_false_done_and_review_backlog_2026_08_15.md` — every remaining open item in these 8 docs is either an
  `[OPERATOR]` hard-stop (2 permanent: fork-PR-approval GitHub UI click, live-trading go-ahead; several time-gated or
  design-scoped), or a genuine `[SCRIPT]`/`[BACKEND]` code-fix todo correctly dispatched to AO
  (`assigned_vm: planning`) that this doc-reconciliation pass does not itself implement (out of `/plan-reconcile`'s
  "PM-repo doc edits only" mandate). All independently re-verified via each doc's own most recent (2026-08-17/18)
  na-eligibility-audit self-check entry plus a fresh read this pass — no stale citations, no false-unchecked
  checkboxes found.
- `s5_7_required_docs_gaps_2026_07_29.md` — `archive_exempt: true` correctly still bridging on
  `codex_vs_repo_docs_ssot_audit_2026_06_01.md` (its parent) not yet reaching terminal status; 0 open todos, not a
  fresh archive candidate (unlike finding 2 above, this bridge is still load-bearing).
- `epic_taxonomy_restructure_and_html_reconcile_2026_08_18.md` — per this run's own explicit brief, this plan's open
  todos (Phase 1 README refresh deferred to Phase 6; Phase 3's 3 new follow-up todos for the 2 excluded
  pre-existing-debt files; Phase 6's full-run + index todos) are genuine tracked follow-up work, not
  stale/false-unchecked — confirmed on a fresh read, left untouched.
- `ao_round5_apply_session_operator_qa_index_2026_08_08.md` — sole open todo (replace the grep-derived index with a
  primary transcript if one is ever exported) has no owner/trigger, correctly still open per its own 2026-08-18
  na-eligibility-audit entry.
- `june_2026_vintage_audit_findings_2026_07_27.md` (959 lines) — all 4 remaining open items are live cross-doc
  dependency checks (perp_funding migration awaiting a live SPOT VM + an unresolved merge conflict;
  mvp_scope_catalogue_tagging awaiting a draft batch; cryptovenue_equity_perps' target doc genuinely still has open
  Phase 3/4/1d-1f work; colocated_feature_pipeline's item 1.5b gated on a sibling plan reaching green) — reaffirmed
  KEEP-NA 4x by prior audits (2026-07-30/08-04/08-07/08-17), read in full this pass, no drift found.

## No-miss ledger (Phase 5.9)

- **(a) routed == parked**: `routed = 1` (the parent_epic repoint question); `parked_in_issue_doc = 1` (recorded in
  this doc's own "Routed" section above). Balanced.
- **(b) sub-agent skips**: none — no sub-agents were dispatched this run (corpus small enough for direct single-seat
  coverage of all 22 docs + epic file).
- **(c) verify-at-HEAD**: N/A — nothing was committed this run (DO-NOT-SHIP constraint); both applied fixes verified
  present in the WORKING TREE directly (`grep`/`cat` re-read after edit).
- **(d) conservation on move**: 1 file moved (`plan_commit_sha_evidence_unresolvable_0f9b8a65ca_2026_08_10.md`,
  `plans/active/issues/` → `plans/archive/2026_08/issues/`) — confirmed present at the new path, absent at the old
  path.
- **(e) every count re-derived this turn**: yes — the 22-doc scope count, the 3127-citation ratchet figure, and the
  hygiene-sweep's single hard failure were all measured this session, not carried from memory.

## Exit-gate observation (STEP 5, corpus-wide — NOT self-inflicted)

`run_hygiene_sweep.sh --ci --no-regen` (entry gate, read-only): 1 hard failure —
`check_na_corpus_ratchet (--diff-base origin/main)`: +1 new NA-population doc / +4 new open todos vs `origin/main`.
This is the same structurally-unavoidable class every plan_reconciler run in this corpus's history documents (a
findings doc is itself `assigned_vm: NA` per template, and `origin/main` lags the much-more-active
`live-defi-rollout` by design) — not attributable to this run specifically (this run had not yet written its own
findings doc at hygiene-sweep-entry time; the drift predates this session). Routed to `/na-eligibility-audit` per
established precedent, not this skill's remit.

## Progress Log

- **2026-08-18 (epic-scoped /plan-reconcile plan_hygiene_master, laptop sub-agent session)**: full read of the epic
  file + all 22 `parent_epic: plan_hygiene_master` child docs; Phase -1 reconciled 6 standing findings/ruling docs
  first (0 needed a fix). 2 fixes applied working-tree-only (epic done-but-unchecked flip; 1 archival). 1 genuine
  parent_epic-repoint question routed unresolved (checker evidence undercuts rather than confirms the repoint
  hypothesis — not force-applied). Everything else in scope re-verified correct, no drift found. DO-NOT-SHIP in
  force — lead session ships this doc + the 2 target-doc edits.
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
