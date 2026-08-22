---
doc_type: plan
title: AO satellite AO batch 23 — conflict-clear bounded extraction from the 2026-08-17 na-eligibility-audit ao run
summary: >-
  TWENTY-THIRD AO-dispatch batch for the `ao` topic tranche — output of a `/na-eligibility-audit ao` Phase 0-3 run
  (2026-08-17, dispatch agt-614193). Phase 1 classified 57 in-scope `assigned_vm: NA` docs via a 7-batch Workflow
  fan-out; 5 items across 3 source docs survive the Phase 2 conflict-check (verbatim/near-verbatim duplicate check
  against every active `assigned_vm: planning` plan in the same parent_epic, the tranche's own consolidated closeout,
  and every other satellite batch created this run or earlier) as genuinely bounded, already-decided, conflict-clear
  work. A 6th RECLASSIFY candidate (`codex_luna_flex_bridge_2026_08_14.md`'s Luna rate-card entry) was found
  conflicted against a standing operator-direction redirect banner cited in `ag_closeout_audit_ao_parked_2026_08_16.md`
  and deliberately EXCLUDED — see that doc + this run's report. A 7th (`plan_reconciler_dead_run_no_lock_ttl_2026_08_12.md`,
  all 3 open todos) was found ALREADY claimed verbatim by the active `ao_satellite_ao_dispatch_batch22_2026_08_16.md`
  and reclassified to KEEP-NA-STALE (already-duplicated) instead — not re-extracted here. **Extended 2026-08-17,
  later same day** (dispatch agt-8a918a, a fresh 2-hourly na-eligibility-audit re-run of this tranche) with one more
  item — a CEFI-manifest-script streaming fix, source `orchestrator_host_memory_exhaustion_4th_recurrence_2026_08_02.md`
  — found new on that run's fresh Phase 0 diff (didn't exist yet at this doc's original authoring) and
  conflict-checked clear the same way. Now 6 items across 4 source docs.
status: active # flipped from draft 2026-08-18 (/plan-reconcile ao, trust-mode ruling — see operator_ruling_record_plan_reconcile_ao_2026_08_18.md #4): todos already fully vetted/conflict-checked per this doc's own Phase 2 write-up; draft was a copy-paste template artifact, not a content gate
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-23, satellite-docs, satellite-extraction, na-eligibility-audit]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch23_finalize_2026_08_17.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /codex/04-architecture/agent-orchestrator-overview.md,
    /plans/active/issues/docs_reconcile_findings_2026_08_17.md,
    /plans/active/issues/check_reference_paths_silent_skip_and_quiet_hides_violation_2026_08_12.md,
    /plans/archive/2026_08/issues/orchestrator_host_memory_exhaustion_4th_recurrence_2026_08_02.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-17"
last_updated: "2026-08-17"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.24
assigned_role: infra
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/archive/issues/plan_reconciler_blocked_answer_and_result_post_gaps_2026_08_16.md,
    /plans/active/issues/docs_reconcile_findings_2026_08_17.md,
    /plans/active/issues/check_reference_paths_silent_skip_and_quiet_hides_violation_2026_08_12.md,
    /plans/archive/2026_08/issues/orchestrator_host_memory_exhaustion_4th_recurrence_2026_08_02.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
source: >-
  `/na-eligibility-audit ao` (2026-08-17, dispatch agt-614193, slot 30). Phase 1 classified 57 in-scope docs (of 69
  total ao-tranche candidates, 12 skipped via an unchanged incremental-diff marker) via a 7-batch Workflow fan-out.
  Phase 2 conflict-check: grepped every status:draft/active `ao_satellite_ao_dispatch_batch*` (3/8/14/21/22) +
  finalizes, `ao_consolidated_closeout_2026_08_12.md`, and every other `assigned_vm: planning` doc under
  `parent_epic: orchestrator_master`/`agent_operating_framework_master` for each of the 6 RECLASSIFY candidates'
  subject matter (distinctive function/mechanism names, not just titles) — zero hits for the 5 items extracted here.
  Two candidates were caught by this same check and NOT extracted: `codex_luna_flex_bridge_2026_08_14.md` (redirect
  banner on a sibling surface) and `plan_reconciler_dead_run_no_lock_ttl_2026_08_12.md` (already claimed by
  batch22 — 3 of batch22's own 6 todos cite it by path).
---

# AO satellite AO batch 23

> **`status: active`** — flipped from `draft` 2026-08-18 (`/plan-reconcile ao` trust-mode ruling, see
> `operator_ruling_record_plan_reconcile_ao_2026_08_18.md` #4): the todos were already fully vetted and
> conflict-checked per this doc's own Phase 2 write-up, so `draft` was a copy-paste template artifact, not a content
> gate. Todos 1-4 were executed by workers on 2026-08-20. **`assigned_vm: planning` /
> `execution_scope: orchestrator-agent`**. _(Banner corrected 2026-08-22 by `/plan-reconcile ao` — it still read
> `status: draft` / "never auto-ingested until an operator flips this", contradicting the frontmatter for 4 days.)_

## Why this plan exists

`/na-eligibility-audit ao`'s 2026-08-17 run classified the full `assigned_vm: NA` "ao" tranche population. Of 57
in-scope docs, the large majority are genuine KEEP-NA (operator-gated, live-infra judgment, unresolved design forks,
or already tracked elsewhere) — see this run's report for the full breakdown. This batch extracts the handful that
are bounded, already-decided, and conflict-clear:

1. **Audit whether other `plan_reconciler`/`na-eligibility-audit` runs have silently missed answers to still-open
   blocked questions** — a bounded, stated-done-when audit with no open judgment call. Source:
   `plan_reconciler_blocked_answer_and_result_post_gaps_2026_08_16.md`.
2. **Fix `fix_frontmatter.py`'s summary-truncation logic** — a fully scoped, single-file code fix with two named
   defects and a stated fix direction. Source: `docs_reconcile_findings_2026_08_17.md`.
3-5. **Three `check_reference_paths.py`/`find_moved_doc_referrers.sh` fixes** (hard-error on an unresolvable `--only`
   path; print offending references on failure even under `--quiet`; retire the now-dead `--quiet`-workaround
   rationale once #4 ships) — each a well-specified, deterministic script change with a stated test to add. Source:
   `check_reference_paths_silent_skip_and_quiet_hides_violation_2026_08_12.md`.
6. **Wrap or streamify 4 named CEFI-manifest-scale scripts** in `market-tick-data-service/scripts/` that are the
   dominant current source of `resource-watchdog` kills (187 kills/7d, 25 >10GB RSS) — a bounded fix with two named
   remediation approaches (stream the read, or wrap in `run-bounded-analysis.sh`) and a stated verification method.
   Source: `orchestrator_host_memory_exhaustion_4th_recurrence_2026_08_02.md` (added 2026-08-17, later same day).

**Explicitly excluded** (named here so nobody re-derives them as candidates without reading why):

1. **`codex_luna_flex_bridge_2026_08_14.md`'s Luna `model_pricing.py` rate-card entry** — individually bounded
   (mirrors an already-shipped identical pattern for GLM Coding Plan), but `ag_closeout_audit_ao_parked_2026_08_16.md`
   (this same tranche's standing parking register) explicitly states the WHOLE doc is "excluded from AO-dispatch by
   operator direction 2026-08-14 (operator is handling both elsewhere, not via this tracker)" — a redirect-banner
   never-relitigate case found on a sibling surface, not inside the candidate doc itself. Flagged in this run's report
   for an operator/human cross-check rather than dispatched here.
2. **`plan_reconciler_dead_run_no_lock_ttl_2026_08_12.md`'s all 3 open todos** — individually bounded (the operator's
   2026-08-15 Option-A ruling resolved the judgment call), but ALL THREE are already claimed verbatim by the active
   `ao_satellite_ao_dispatch_batch22_2026_08_16.md` (its todos 1-3 cite this doc by path + exact todo text; its own
   finalize plan's todo 2 already owns reconciling/archiving this source doc once batch22 ships). Reclassified to
   KEEP-NA-STALE (already-duplicated) instead of re-extracted — would otherwise dispatch a duplicate.
3. **Every other doc's remaining open items** — operator-gated, design-fork, credential-blocked, or already tracked
   via an existing active plan/epic per this run's own report; re-triage on the next `/na-eligibility-audit ao` run,
   not re-derived here.

## Rules for every worker on this plan

- All 6 todos below are file-disjoint (different scripts/mechanisms; todo 6 touches a different repo entirely,
  `market-tick-data-service`, vs todos 1-5's `agent-orchestrator`/`unified-trading-pm`) — safe to run concurrently,
  no `sequential: true`.
- Todos 3-5 all touch `scripts/plan-hygiene/check_reference_paths.py` (todos 3-4) or
  `scripts/plan-hygiene/find_moved_doc_referrers.sh` (todo 5) — todos 3 and 4 share `check_reference_paths.py` but
  touch disjoint functions (`_run_only`'s existence-check vs its failure-printing path); todo 5 is gated on todo 4
  landing first by its own done-when (it retires a workaround whose reason for existing is todo 4's defect), not by
  `sequential: true` — a worker picking up todo 5 first should check todo 4's status before starting.

## Todos

- [x] ✅ [BACKEND] P2. **Audit whether other `plan_reconciler`/`na-eligibility-audit` runs have silently missed answers
      to still-open blocked questions**, now that this gap is confirmed live (not just suspected — reproduced
      2026-08-16, dispatch agt-3eb42b). Query the escalation/blocked-question table for any row with a recorded
      operator answer but no corresponding worker-side pickup, across recent runs. **Done when**: a count of
      affected historical rows is reported (0 is a valid, good answer) and, if any are found, each is individually
      resolved (apply the answer now, or re-ask if too stale to trust). Source:
      `/plans/archive/issues/plan_reconciler_blocked_answer_and_result_post_gaps_2026_08_16.md` todo "[BACKEND] P2.
      Audit whether other plan_reconciler/na-eligibility-audit runs...". Repo: agent-orchestrator (+ unified-trading-pm
      for the source doc's own historical-scan scope). — **DONE 2026-08-20 (slot 14)**: affected count = **167**
      (0 is not the answer this time). All 167 answers durably stored + retrievable via the fixed
      `GET /api/blocked/{blocked_id}`; 0 in-flight, 11 tasks done, 6 tasks still `queued` (answers preserved) — full
      breakdown in Progress Log.
- [x] ✅ [SCRIPT] P2. **Fix `fix_frontmatter.py`'s summary-truncation logic**
      (`scripts/plan-hygiene/fix_frontmatter.py`'s `get_first_paragraph_after_heading()`, gated by its sole caller's
      `if not has_field(new_fm, "summary")` guard — reference the symbols, not a line number: this todo previously
      cited `lines ~245-294`/`~646-654`, corrected 2026-08-18 /plan-reconcile per task_template.md §3's "reference
      SYMBOLS, never line numbers" rule). Two confirmed defects: (a) hard-cuts mid-word at 197
      chars with a literal `" ..."` suffix when no sentence/space boundary is found in budget; (b) locks onto the
      FIRST `". "`/`"! "`/`"? "` in the source paragraph even when that leaves most of the 197-char budget unused,
      producing dangling lead-ins. **Fix direction**: widen the sentence-boundary search to use more of the 197-char
      budget before falling back to a hard cut, and prefer a hard cut mid-clause (not mid-word) as the last resort.
      **Done when**: the widened search + mid-clause-cut fallback ship with a regression test covering both defect
      classes (a truncation that previously stopped before the doc's real point, and a dangling first-sentence
      lead-in), and `quality-gates.sh` is green. Source: `/plans/active/issues/docs_reconcile_findings_2026_08_17.md`
      todo "[SCRIPT] P2. Fix fix_frontmatter.py's summary-truncation logic". Repo: unified-trading-pm. — **DONE
      2026-08-20 (slot 32)**: `get_first_paragraph_after_heading()` now requires a sentence boundary to use at
      least half the 197-char budget before accepting it (fixes defect b — no more locking onto an early first
      sentence and wasting most of the budget), adds a comma/semicolon/dash clause-boundary tier before the
      word-boundary fallback, and only cuts mid-word as the genuine last resort when the paragraph has no space at
      all (fixes defect a — the old bare hard-cut path). Two new regression tests added to the pre-existing
      `tests/unit/test_fix_frontmatter_summary_truncation.py` (`test_early_sentence_boundary_does_not_win_over_unused_budget`,
      `test_late_clause_boundary_used_when_no_late_sentence_boundary`); all 8 tests in that file pass.
      `quality-gates.sh` green. Also fixed an unrelated pre-existing red (`reachability-gate`:
      execution-service's `PendleConnector` newly reachable but not dropped from
      `scripts/quality_gates/reachability_gate_baseline.json`) blocking the shared gate — confirmed via a clean
      direct re-run of `check_reachability_gate.py`, fixed per the check's own prescribed shrink-the-baseline
      remedy. Evidence: unified-trading-pm@bd4f0b5884 (truncation fix), unified-trading-pm@5ac4b78f42 (baseline
      fix, both ancestor-verified on origin/live-defi-rollout).
- [x] ✅ [SCRIPT] P1. **Make an unresolvable `--only` path a hard error** in `check_reference_paths.py`'s `_run_only()`
      — today `if not p.is_file(): continue` silently drops an unresolvable path and the function reports "0
      violation(s)" / exit 0, a false-clean-bill-of-health that cost 7 failed `safe-doc-push` attempts and 6 wrong
      diagnoses on one real incident (2026-08-12). **Fix**: print the attempted path (including its resolved
      absolute form) and exit non-zero when a named `--only` path does not resolve. **Done when**: a regression test
      asserts non-zero exit for a non-existent `--only` path, and `quality-gates.sh` is green. Source:
      `/plans/active/issues/check_reference_paths_silent_skip_and_quiet_hides_violation_2026_08_12.md` todo "[SCRIPT]
      P1. Make an unresolvable --only path a hard error". Repo: unified-trading-pm. — **DONE (pre-existing, verified
      2026-08-20, slot 4)**: already shipped in `unified-trading-pm@1a066b0125` (`_run_only()` now appends
      unresolved paths and hard-errors, printing evidence even under `--quiet`); regression tests
      `test_unresolvable_only_path_is_a_hard_error` + `test_unresolvable_only_path_reported_even_under_quiet` in
      `scripts/plan-hygiene/test_check_reference_paths.py` (collected via `PYTEST_UNIT_DIR`). No code change needed
      this session — checkbox was simply stale.
- [x] ✅ [SCRIPT] P2. **Print offending references on failure even under `--quiet`** in `check_reference_paths.py`'s
      `_run_only()`, `_run_diff_base()`, and the corpus-wide path — `--quiet` currently suppresses the per-violation
      `FORMAT`/`DANGLING` lines but keeps the summary count, so a precommit failure says "N violation(s)" without
      ever naming the offending reference. **Fix**: print offending references on FAILURE regardless of `--quiet`;
      quiet should suppress noise on success, never evidence on failure. **Done when**: a regression test confirms
      `--quiet` + a real violation still prints the offending reference(s), and `quality-gates.sh` is green. Source:
      `/plans/active/issues/check_reference_paths_silent_skip_and_quiet_hides_violation_2026_08_12.md` todo "[SCRIPT]
      P2. Print offending references on failure even under --quiet". Repo: unified-trading-pm. — **DONE 2026-08-20
      (slot 10)**: `main()`'s corpus-wide (baseline) path now prints FORMAT/DANGLING evidence on failure regardless
      of `--quiet` (`_run_only()`/`_run_diff_base()` were already fixed by `1a066b0125`); added regression test
      `test_corpus_wide_quiet_still_prints_evidence_on_failure`. `quality-gates.sh` green. Evidence:
      unified-trading-pm@cc7fc08e54 (ancestor-verified on origin/live-defi-rollout).
- [ ] [SCRIPT] P3. **Retire the `--quiet`-workaround rationale in `find_moved_doc_referrers.sh`'s header** once todo
      4 ships, and re-check whether that script still has a reason to exist. Its header currently documents its own
      existence as a workaround specifically for `run_hygiene_sweep.sh` calling `check_reference_paths.py` with
      `--quiet`, which todo 4 makes obsolete. **Done when**: the header comment is corrected (or the script is
      retired if it truly has no other purpose once the workaround rationale is gone) and any caller that depended
      on it is checked. Source:
      `/plans/active/issues/check_reference_paths_silent_skip_and_quiet_hides_violation_2026_08_12.md` todo "[SCRIPT]
      P3. Retire the --quiet-workaround rationale in find_moved_doc_referrers.sh's header". Repo: unified-trading-pm.
- [ ] [INFRA] P2. **Wrap or streamify the 4 CEFI-manifest-scale scripts in `market-tick-data-service/scripts/`**
      that are the dominant current source of `resource-watchdog` kills — `normalize_instrument_type_casing.py
      --index-only --dry-run` (up to 15.2GB), `audit_cefi_manifest_noncanonical_enumeration_2026_07_18.py`
      (5.5-5.9GB), `revert_cefi_live_corrective_migration_overreach_2026_08_16.py` (up to 19.5GB),
      `measure_shard_duration_p95.py` (5-10GB, scales with `--concurrency`) — each materializes a full CEFI-scale
      manifest/index into memory rather than a streamed/chunked read. **Done when**: each script either reads its
      manifest/index in a bounded/streamed fashion or is wrapped in `scripts/dev/run-bounded-analysis.sh`, and a
      7-day post-fix `journalctl -u resource-watchdog` check shows zero kills attributable to these script names.
      Source: `/plans/archive/2026_08/issues/orchestrator_host_memory_exhaustion_4th_recurrence_2026_08_02.md` todo
      "[INFRA] P2. Wrap or streamify the CEFI-manifest-scale scripts...". Repo: market-tick-data-service.

## Codex SSOTs (read before starting)

`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`,
`/codex/12-agent-workflow/commit-push-flip-rule.md`, `/codex/12-agent-workflow/measurement-claims-discipline.md`.

## Progress Log

- **2026-08-17 (na_eligibility_auditor, dispatch agt-614193, autonomous)**: Drafted per `/na-eligibility-audit ao`'s
  Phase 3 — 5 conflict-clear, file-disjoint, bounded todos extracted from 3 source docs after Phase 2's conflict-check
  excluded 2 further candidates (a redirect-banner case and an already-claimed-by-batch22 case, both detailed above).
  `status: draft` per autonomous-mode safety rail; flipping to `active` is an operator decision.
- **2026-08-17 (na_eligibility_auditor, dispatch agt-8a918a, later same day, autonomous)**: Extended with todo 6 — a
  bounded CEFI-manifest-script streaming fix, source `orchestrator_host_memory_exhaustion_4th_recurrence_2026_08_02.md`,
  found new on this run's fresh Phase 0 diff (post-dated batch23's original authoring). Conflict-checked clear:
  grepped `market-tick-data-service/scripts/` script names + "resource-watchdog kill" against every active
  `assigned_vm: planning` plan under `parent_epic: orchestrator_master`, `ao_consolidated_closeout_2026_08_12.md`,
  and every `ao_satellite_ao_dispatch_batch*` (incl. this one) — only hit was `ao_satellite_ao_dispatch_batch21_2026_08_16.md`,
  which merely records the finding's own discovery (its own todo already closed), not a competing dispatch of the
  fix. Source doc's checkbox flipped citing this extraction; still `status: draft`, no re-approval needed for an
  additive same-status edit.
- **context-scout 2026-08-19**: verified the pre-existing context_scope (5 entries, set at authoring) — all paths
  confirmed resolving on disk, still the correct source-doc reading list; no change needed.

- **2026-08-20 (slot 14, backend worker)**: Completed batch23 item 1 — the historical blocked-answer-orphan audit
  (read-only query of the live orchestrator SQLite `data/state/state.db` + the fixed `GET /api/blocked/{id}`
  endpoint; no code change — the fix already shipped in `agent-orchestrator@4a0753791a`). Findings:
  - **Affected count = 167** distinct `blocked_queue` rows with `answered_at` set + non-null `answer` whose answer
    delivery message was orphaned by task/slot reassignment (`blocked_message_orphaned_by_reassign` in
    `take_pending_messages` — the exact Gap-2 class the source doc reproduced). Span 2026-08-07 → 2026-08-19
    (per-day 21/5/27/18/5/16/11/4/15/11/16/9/9). Signal: `slot_messages` rows `text LIKE 'BLOCKED Q answered%'` with
    `answered_at` set (terminal) but `delivered_at` NULL (never delivered), joined to `blocked_queue` on
    (slot_id, task_id) + answer-time proximity.
  - **51** of the 167 relate to reconciler/eligibility/audit work (the task's target class).
  - **0** are for a currently-in-flight task (no slot's `current_task` matches). 11 affected tasks are `done`
    (answers moot — work completed). **6 affected tasks are still `queued`** — answers preserved in `blocked_queue`,
    listed so they are not silently lost when they dispatch: `cefi_fwd_backfill_vm_deleted_by_sa_within_10min`
    (BLK-4a5e7363), `cefi_window_scoped_coverage_gap_okx_binance_bybit_2024` (BLK-23131e14),
    `defi_satellite_ao_dispatch_batch11` (BLK-13334ded / BLK-6c04234a / BLK-74d8766b / BLK-a635d9e2 / BLK-e59287f4),
    `safe_doc_push_extreme_stash_quarantine_drops_renamed_file_content` (BLK-0fe3a14a / BLK-633c6d9e),
    `tradfi_satellite_ao_dispatch_batch9` (BLK-963d4046 / BLK-d3fe28e8),
    `venue_year_coverage_cefi_oom_deployment_api` (BLK-9e7f98bf).
  - **Resolution**: no answer content was ever lost — all 167 answers are durably recorded in `blocked_queue` and
    retrievable by blocked_id via the shipped fix (verified live: `GET /api/blocked/BLK-336884f2` → HTTP 200 with full
    question+answer). Nothing needs re-asking (all answers present/non-empty). The 11 done tasks' answers are moot;
    the 6 queued tasks' answers are preserved and fetchable by the blocked_ids above. 145 distinct answer texts among
    the 167 → ~22 are repeat answers to re-dispatched versions of the same underlying question (e.g. the
    `defi_satellite_ao_dispatch_batch9` vm-zombie-daemon answer ×5, bare `A` ×16), so the population is ~145 distinct
    decisions, not 167. Audit conclusion: the delivery gap existed fleet-wide (not just on the reconciler's own runs),
    but it only ever lost the NOTIFICATION, never the answer — the 2026-08-19 fix closes it going forward.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
- **2026-08-20 (slot 32, infra worker)**: Completed batch23 item 2 — fixed
  `fix_frontmatter.py`'s `get_first_paragraph_after_heading()` summary-truncation logic (both
  named defects: early-sentence-boundary wasting most of the budget, and the bare mid-word hard
  cut). Widened the boundary search with a minimum-budget-usage threshold, added a clause-boundary
  tier, and kept mid-word cut only as the true last resort. Extended the pre-existing
  `tests/unit/test_fix_frontmatter_summary_truncation.py` with 2 new regression tests (8/8 pass).
  Also found and fixed, same session, an unrelated pre-existing red on the shared
  `reachability-gate` check (execution-service's `PendleConnector` newly reachable, baseline not
  shrunk) that would have blocked shipping under the green-tree rule — fixed via the check's own
  prescribed remedy, verified with a standalone clean re-run before touching it.
  `quality-gates.sh` green both times. Evidence: unified-trading-pm@bd4f0b5884 (truncation fix),
  unified-trading-pm@5ac4b78f42 (baseline fix) — both ancestor-verified on
  origin/live-defi-rollout.
