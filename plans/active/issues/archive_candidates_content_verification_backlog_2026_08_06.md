---
doc_type: issue
title:
  check_archive_candidates.sh (0-open-todos, unlocked -> archive; baseline 0, hard-fails quality-gates-v2) has ~116 live
  candidates needing real per-doc content verification, not a mechanical batch-archive
summary: >-
  While resolving a `ldr_main_qg_failure`-shaped promote-PR wall on `unified-trading-pm` (escalation agt-4dd4f4,
  2026-08-06), 5 of 6 failing plan-hygiene hard ratchets (terminal-status-archived, ag-closeout-linkage, reference-paths
  format+existence, effort-signal) were resolved with genuine fixes (see `unified-trading-pm@b30fb5267` for the exact
  diffs). The 6th, `check_archive_candidates.sh`, started at 148 candidates (baseline 0, refuses any baseline raise by
  construction — `min(n, existing)` in its own write path) and was reduced to ~116 by archiving 6 fully-done
  `_finalize_*.md` gated-closeout plans (a genuinely mechanical, no-judgment-call category per the 2026-07-30
  finalize-plan ruling) plus the incidental overlap with the terminal-status-archived fix. The remaining ~116 (110 issue
  docs with `status: open` but 0 remaining unchecked `- [ ]` todos, 6 active plans) are a DIFFERENT shape: `status` was
  never flipped to a terminal value at all, which means (unlike the terminal-status-archived batch, where `status:
  resolved` was already a human/agent judgment call already made) each one requires actually READING the doc's own
  prose/Progress Log to confirm the checkbox count reflects genuine completion before flipping `status` and archiving —
  a doc can have every listed `- [ ]` checked while its own summary/Progress Log still describes an open question, a
  deferred follow-up not yet turned into its own todo, or an `archive_exempt`-shaped standing-reference role. Blindly
  batch-flipping `status` on all 116 without that per-doc read would risk silently mis-marking still-open work as
  resolved — worse than staying blocked. Out of scope for a bounded CI-fix pass (see
  `unified-trading-pm/agents/cicd.md`'s own carve-out: "the full daily plan/codex/cross-plan reconciliation... is the
  plan_reconciler worker's job... NOT this gate-failure handler").
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, archive-candidates, ratchet, ci-cd, quality-gates-v2, ldr-main-promote]
related:
  [
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/08-workflows/ci-cd-flow.md,
    /plans/active/issues/reference_path_convention_2026_07_23.md,
  ]
created: "2026-08-06"
author: cicd escalation agt-4dd4f4
last_updated: "2026-08-06"
parent_epic: plan_hygiene_master
assigned_vm: NA
execution_scope: local-only
assigned_role: cicd
priority: P1
estimate_class: research
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.8
source: >-
  Discovered live while resolving promote-PR #2367/#2371 wall (escalation agt-4dd4f4) — `bash
  scripts/plan-hygiene/check_archive_candidates.sh` run against live-defi-rollout HEAD b30fb5267, 2026-08-06.
drift_direction: worsening-slowly
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
context_scope:
  [
    /scripts/plan-hygiene/check_archive_candidates.sh,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/task_template.md,
  ]
---

# check_archive_candidates.sh has a real, unbatchable backlog — needs per-doc content review

## What I found

`bash scripts/plan-hygiene/check_archive_candidates.sh` is a hard, baseline-0, never-raisable ratchet in
`run_hygiene_sweep.sh --ci --no-regen` (folded into `quality-gates-v2` for this repo). As of `b30fb5267` on 2026-08-06
it reports ~116 candidates: docs with 0 remaining `- [ ]` todos, unlocked, `status` still `active`/`open` (never flipped
to a terminal value), still sitting in `plans/active/`. Split:

- **110 issue docs** (`plans/active/issues/*.md`, `status: open`, all listed checkboxes done)
- **6 active plans** (`plans/active/*.md`, `status: active`, all listed checkboxes done) —
  `ao_done_categorization_ display_and_quickmerge_gate_2026_08_06.md`,
  `canonical_id_builder_retrofit_checklist_2026_07_08.md`, `data_status_page_ux_and_canonicalisation_2026_07_16.md`,
  `defi_strategy_pnl_axis_index_2026_07_24.md`, `mtds_retry_safe_default_audit_2026_07_14.md`,
  `tradfi_consolidated_closeout_2026_07_18.md`

Live count drifts up and down slightly run-to-run as ~15+ concurrent AO slots land work on `live-defi-rollout`
continuously — treat any specific number here as a snapshot, not a fixed target; re-run the check for the current live
count before starting remediation.

## Why this needs a real per-doc read (not a batch script)

A checkbox-complete doc is NOT automatically content-complete: the check's own header comment documents 3 legitimate
NON-archive outcomes (`locked_by`, a `gate_on_depends` finalize-plan companion, `archive_exempt: true` for a
standing-reference hub) already excluded from this count — so everything remaining genuinely LOOKS archivable by the
checkbox signal alone, but confirming it actually IS requires reading:

1. The doc's own summary / Progress Log for any prose-only "still need to..." that never became a tracked `- [ ]` (the
   exact anti-pattern `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` § 2 names).
2. Whether the doc is itself a live-reference hub that should get `archive_exempt: true` instead of archival (the same
   doc's § "a doc explicitly routed for archival THROUGH another plan's own dispatched reconciliation todo" escape
   hatch, when applicable).
3. `tradfi_consolidated_closeout_2026_07_18.md` in particular reads like a coordination/umbrella doc by name — likely an
   `archive_exempt: true` candidate rather than a real archival, but confirm by reading it, don't assume.

## Todos

- [x] ✅ [DOC] P1. **Archive the 2 docs that flipped `check_terminal_status_archived` from GREEN to RED on 2026-08-06**
      (DONE 2026-08-06, cicd escalation agt-ca03f6 slot-9: archived
      `vm_zombie_watchdog_prefix_coverage_gap_2026_08_06.md` +
      `canonical_id_builder_retrofit_checklist_missing_finalize_2026_08_06.md` → `plans/archive/issues/`; also archived
      the 2 additional terminal-status violations that surfaced since this doc was filed —
      `live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31_finalize_2026_07_31.md` (superseded, work ported
      to survivor) → `plans/archive/2026_08/`, and re-opened
      `deployment_api_events_global_state_leak_flaky_metadata_probe_2026_08_06.md` from `resolved` → `open` because it
      carries an open P3 follow-up todo (archiving would silently drop it). `check_terminal_status_archived.py` now
      reports 0 violations) — a DIFFERENT, narrower check than this doc's main backlog: these already carry a terminal
      `status: resolved` (the human/agent judgment call is already made), they are simply still sitting in
      `plans/active/issues/`, so they need only the mechanical `git mv` + banner + referrer sweep, not the per-doc
      content read the ~114 candidates require. The 2 docs: `vm_zombie_watchdog_prefix_coverage_gap_2026_08_06.md`
      (filed+resolved same day by `slot-2·laptop`, `e724407f0`) and
      `canonical_id_builder_retrofit_checklist_missing_finalize_2026_08_06.md` (resolved by `slot-9·planning`,
      `4d77219cf`). Both 0 open todos, `locked_by:` empty. **Provenance**: measured by `/plan-reconcile ao` 2026-08-06 —
      the check PASSED at that run's entry and FAILED at its exit, and `git log -S` attributes both to other slots
      landing mid-run, not to the reconcile pass. Left unarchived deliberately because their owning slots created them
      minutes earlier and may be mid-ritual; archiving under a concurrent session is exactly how the active/archive
      duplicate-path divergence found the same day (`a62bdd8ea`) happens. **Done when**:
      `python3 scripts/plan-hygiene/check_terminal_status_archived.py` reports 0 violations again.
- [ ] [DOC] P1. Re-run `bash scripts/plan-hygiene/check_archive_candidates.sh` for the current live candidate list (it
      drifts with ongoing AO churn — do not reuse this doc's snapshot list without refreshing it first).
- [ ] [DOC] P1. For each of the 6 active-plan candidates: read the full doc, confirm genuine completion (not just
      checkbox count), then EITHER archive it via the standard 6-step ritual
      (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) — `git mv` to `plans/archive/<YYYY_MM>/`,
      flip `status` to a terminal value, fix every corpus referrer — OR set `archive_exempt: true` with a one-line
      Progress Log justification if it's a genuine standing-reference hub.
- [ ] [DOC] P1. For the ~110 issue-doc candidates: batch them into reviewable chunks (e.g. by `asset_group`, mirroring
      `/ag-closeout-audit`'s tranche split) and, per doc, confirm genuine completion then archive (flip `status` to
      `resolved`/`false-positive`/`superseded` + `git mv` to `plans/archive/issues/` + fix referrers) or apply
      `archive_exempt: true` with justification. Re-run the check after each chunk to confirm the live count is trending
      down, not just churning.
- [ ] [SCRIPT] P2. Once the backlog is cleared (or the residual is small + all `archive_exempt`-justified), consider
      whether this check's remediation should get its own dedicated skill (mirroring `/na-eligibility-audit`'s tranche +
      incremental-mode pattern) so future backlog growth from routine AO churn doesn't require another one-off
      CI-firefighting session to clear — a standing skill can also make the `archive_exempt: true` escape hatch a
      first-class reviewed decision instead of an ad-hoc one.

## Progress Log

- **2026-08-06 (cicd escalation agt-4dd4f4)**: found while resolving the LDR->main promote-PR quality-gates-v2 wall.
  Fixed the other 5/6 failing ratchets for real (see `unified-trading-pm@b30fb5267`); archived 6 of the ~148 original
  archive-candidates that were unambiguously mechanical (done `_finalize_*.md` plans, no independent judgment call per
  the 2026-07-30 finalize-plan ruling). Left the remaining ~116 for this tracked follow-up rather than mass-flip
  `status` without reading each doc — scope explicitly excluded from a bounded CI-fix pass per
  `unified-trading-pm/agents/cicd.md`'s own carve-out (deep reconciliation is `plan_reconciler`'s job).
- **2026-08-06 (cicd escalation agt-ca03f6, slot 9)**: completed Todo 1 (see the flip above) —
  `check_terminal_status_archived` is now 0 violations. The remaining ~113 archive candidates + AG-closeout linkage +
  NA-corpus ratchets stay tracked here and in `ag_closeout_linkage_baseline_regression_87_vs_69_2026_08_06.md` for
  `plan_reconciler`'s daily pass / `/na-eligibility-audit`; out of scope for this bounded CI-fix per the same carve-out.
  This doc's own Todos 2-5 remain open.

## Operational lessons (cicd, from resolving a PM ldr_qg_failure wall)

Two measurement traps worth carrying for the next cicd worker on a PM `ldr_qg_failure` wall (recorded here as the
closest active tracking doc for this wall family):

1. **A qg_red blocker's DECLARED cause is usually only ONE of several ratchets red.** RB-fbeef249 declared
   `finalize-plan-coverage` (already green on origin via the archival commit by dispatch time), but the full
   `run_hygiene_sweep.sh --ci --no-regen` reproduced 4 additional hard failures (terminal-status-archived, AG-closeout
   linkage, NA-corpus, archive-candidates). Diagnose with the full sweep, never just the named check.
2. **`check_plan_commit_sha_evidence.py` false-reports unresolvable `<repo>@<sha>` citations against STALE sibling
   clones** — it flags any cited SHA that `git cat-file -t` can't resolve, and a sibling checkout that hasn't fetched
   today's commits reads every recent citation as fabricated. Before treating its quickmerge re-gate failure as real,
   `git -C <sibling> fetch origin` each cited repo and re-run; only the citations that STILL don't resolve are genuine
   (and they're ratchet-baselined — a count at/below baseline passes). This cost a wasted re-gate cycle this session.
