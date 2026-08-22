---
doc_type: issue
title: Finalize — locked_by live-defi-rollout placeholder-source bug hunt (2026-08-19)
summary: >-
  Gated finalize for `locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md`'s RECLASSIFY whole-doc flip
  (na-eligibility-audit, cross-cutting tranche, 2026-08-19), scoped ONLY to the remaining item (find + patch the
  doc-creation source still stamping the placeholder on new docs). Does not touch the doc's separate, already-closed
  corpus-wide UNLOCK action (operator-gated, HARD-STOP, resolved 2026-08-12/18).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ao-dispatch, close-out, finalize, na-eligibility-audit, locked_by]
related:
  [
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-19"
last_updated: "2026-08-19"
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.25
assigned_role: review
effort: low
resolved_by:
drift_direction: none
depends_on: [locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10]
gate_on_depends: true
sequential: true
context_scope:
  [
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /plans/archive/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md,
  ]
supersedes:
superseded_by:
locked_by:
locked_since:
source: >-
  Paired finalize for locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md's na-eligibility-audit
  RECLASSIFY whole-doc flip (dispatch agt-dc3dbe, slot 30, 2026-08-19).
---

# Finalize — locked_by live-defi-rollout placeholder-source bug hunt

- [x] ✅ [REVIEW] P3. `scripts/cicd/parity_watchdog.py`'s fix (commit `de854a729f`, 2026-08-20T17:47:10Z) verified
      reachable on `origin/live-defi-rollout` (`git merge-base --is-ancestor de854a729f origin/live-defi-rollout`)
      and confirmed live at `parity_watchdog.py:111` (emits an empty `locked_by:` field). **However the "zero NEW
      hits" re-verification did NOT pass** — see the new todo below.
- [ ] [SCRIPT] P2. **Recurrence found 2026-08-22**: `plans/active/issues/dp_live_004_bybit_futures_book_snapshot_unproductive_2026_08_21.md`
      (`author: data-pipeline-failure`, created 2026-08-21T04:03:11Z — AFTER the parity_watchdog fix landed) still
      carries `locked_by: live-defi-rollout`. `parity_watchdog.py` was only ONE of at least two doc-creation
      writers stamping this placeholder — this doc's author tag (`data-pipeline-failure`) does not match any
      script found in this repo (`grep -rl "author: data-pipeline-failure"` over every `.py` in every cloned repo
      in this slot returns zero hits), so the writer is either cross-repo (a data-pipeline-alerts monitor not
      cloned in this workspace) or template-copied from `plans/PLAN_FORMAT.md`'s own literal example frontmatter
      (lines 131/211/771 all show `locked_by: live-defi-rollout` as example text, itself a candidate root cause —
      any doc-creation code/agent that copies that example verbatim reproduces the bug). Find the actual writer
      (grep the data-pipeline-alerts/monitor codebase and/or the escalation-doc-creation path for
      `data-pipeline-failure`) and patch it to emit an empty `locked_by:`; consider also fixing PLAN_FORMAT.md's
      example values to a non-literal placeholder (e.g. `<actor> since <ts>`) so future copy-paste can't reproduce
      this. (2 already-existing docs — `dp_fetch_009_cefi_liquidations_batch_aster_2026_08_20.md` and
      `manifest_hygiene_red_changed_all_2026_08_20.md` — also carry the placeholder but predate the fix commit
      [2026-08-20T08:03-08:24Z, fix landed 17:47Z same day], so they are NOT new evidence of recurrence; leave them
      for the ordinary corpus sweep.)
- [ ] [REVIEW] P3. Once the todo above lands (verified via a fresh-doc creation + repeat grep showing zero NEW
      hits), THEN re-verify the source doc `locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md`'s
      own `locked_by:`/`locked_since:` are clear before any further archival action (it is itself part of the
      corpus this bug touches). Note: that source doc was already archived 2026-08-21 on the strength of the
      parity_watchdog fix alone — this re-check is now about whether that archival needs revisiting given the
      recurrence found here, not about archiving it again.

## Progress Log

- **2026-08-19**: drafted alongside the na-eligibility-audit whole-doc RECLASSIFY flip (dispatch agt-dc3dbe, slot
  30, cross-cutting tranche).
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
- **2026-08-22** (slot 3, review): verified the parity_watchdog.py citation (commit `de854a729f`, reachable).
  Ran the doc's own re-verification bar ("fresh-doc creation + repeat grep showing zero NEW hits") and it FAILED —
  found `dp_live_004_bybit_futures_book_snapshot_unproductive_2026_08_21.md`, created ~10.5h after the fix landed,
  still carrying the placeholder from a different, unidentified doc-creation writer. Split the original single
  todo into three: the parity_watchdog verification (done), a new todo to hunt the second writer, and a
  re-sequenced final re-check of the source doc's own lock state. Did not touch the already-archived source doc's
  archival status — that determination stands unless the new writer-hunt todo surfaces reason to revisit it.
