---
doc_type: plan
title: Sports consolidated native AO extract — finalize (reconcile parent checkboxes + archive)
summary: >-
  Gated closeout for sports_consolidated_native_ao_extract_2026_07_25.md — machine-held via depends_on +
  gate_on_depends: true until all 26 of that plan's todos are done. Reconciles each completed todo's evidence back into
  sports_consolidated_closeout_2026_07_19.md's own corresponding checkbox (this extraction's source doc is the master
  plan itself, unlike a satellite batch drawing from many small docs), re-checks the excluded/scoped-down sub-items for
  whether their gate has since cleared, then runs the standard archival ritual on the extract plan. Mirrors
  sports_satellite_ao_dispatch_batch3_finalize_2026_07_25.md's pattern.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, native-extract, finalize, archival]
related:
  [
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/archive/2026_07/sports_satellite_ao_dispatch_batch3_finalize_2026_07_25.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-30"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.48
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [sports_consolidated_native_ao_extract_2026_07_25]
gate_on_depends: true
source: >-
  task_template.md §4's finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated finalize plan,
  mirroring the sports_satellite_ao_dispatch_batch2/3-finalize precedent.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    scripts/plan-hygiene/check_line_caps.sh,
  ]
---

# Sports consolidated native AO extract — finalize

> **Machine-gated on `sports_consolidated_native_ao_extract_2026_07_25.md`** (`depends_on` + `gate_on_depends: true`) —
> the dispatcher will not queue any todo below until all 26 tasks in that plan are `done`. `sequential: true` because
> todo 2 (source-doc archival) needs todo 1's reconciliation done first (a doc can only be archived once its status is
> genuinely flipped to `resolved`), todo 3 (re-check excluded/scoped-down items) benefits from todo 1's reconciliation
> being done first too, and todo 4 (archival of this extract plan itself) must run last.
>
> **Reminder carried from the source plan**: `sports_consolidated_closeout_2026_07_19.md` was OVER the 1000-line hard
> cap as of 2026-07-25 (`issues/autonomous_session_operator_decisions_2026_07_25.md` entry #9) and may still be
> uncommittable via the normal path when this finalize plan runs — re-check `check_line_caps.sh` against it FIRST; if
> still blocked, do not attempt todo 1's edit until the split/promote/leave-as-is decision in that entry has been ruled,
> and note the block explicitly rather than silently skipping the reconciliation.

## Todos

- [ ] [REVIEW] P1. **Reconcile `sports_consolidated_native_ao_extract_2026_07_25.md`'s 26 now-done todos back into
      `sports_consolidated_closeout_2026_07_19.md`'s own corresponding checkboxes.** For each of the 26 todos: flip the
      identically-worded (or closely-paraphrased) checkbox at the cited
      `sports_consolidated_closeout_2026_07_19.md: <line>` location, citing the extract plan's shipped commit(s) —
      verify the actual shipped commit exists before citing it (`git log`, not the extract plan's own claim alone).
      **First check whether the parent file is still over the line-cap**
      (`bash scripts/plan-hygiene/check_line_caps.sh plans/active/sports_consolidated_closeout_2026_07_19.md`) — if
      still HARD-blocked, do NOT force the edit; record which checkboxes are ready to flip and note the commit is
      deferred until the cap decision lands (do not silently skip this reconciliation — file it as a tracked follow-up
      if blocked). For the 4 todos that were scoped DOWN from the source todo's literal text (venue vocabulary re-stamp
      excluding cross-AG bleed; the T-12h↔T-24h dead-zone scan excluding the T-18h-horizon design choice; the
      emitter-locate todo dropping the stale "before folding into K2" framing; Sports P2a sub-item (c) only, excluding
      sub-items (a)/(b)): flip only the portion actually completed, and leave a clear note in the parent checkbox's own
      text (or a cross-reference) that sub-items (a)/(b)/the excluded design choice remain open and are NOT covered by
      this flip. **Done when**: all 26 corresponding checkboxes in the parent doc are flipped (or the cap-block is
      explicitly recorded if still blocking), each citing a verified commit, with the 4 partial-scope todos' remaining
      sub-items left visibly open.
- [ ] [DOC] P1. **Archive every doc todo 1 drives to `status: resolved`/`complete` — in the same commit as the flip,
      never left sitting in `plans/active/`.** `check_terminal_status_archived.py` HARD-fails on any doc whose
      frontmatter reads a terminal status while it still lives under `plans/active/` (including `plans/active/issues/`)
      — the omission of this exact step across the sports finalize-plan family already forced one such HARD-fail: the
      `plan_health` gate's own remediation (`unified-trading-pm@57ed9271c`, escalation `agt-9a5061`, PR #1545)
      auto-archived 11 docs nobody's plan owned. **This plan's shape differs from the other 4 sports finalize plans**:
      todo 1 flips checkboxes back into ONE parent doc (`sports_consolidated_closeout_2026_07_19.md`), not into many
      separate small source docs — so the expected outcome here is usually a no-op, since the master closeout doc is
      very unlikely to reach 0 open todos from this one extract's reconciliation alone. Still: if todo 1's
      reconciliation (or a subsequent audit) ever DOES drive `sports_consolidated_closeout_2026_07_19.md`, or any other
      doc this extraction touches, to a genuine terminal status with 0 open todos, archive it to
      `plans/archive/2026_07/` IN THE SAME COMMIT as that status flip — fix every corpus referrer of the archived doc's
      pre-archive path. **Done when**: either (a) an explicit confirmation is recorded that no doc reached a terminal
      status via todo 1 (the expected case), or (b) every doc that did is archived in the same commit as its flip, and
      `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` reports 0 hard failures. Source:
      `archive/issues/sports_plan_reconcile_operator_decisions_2026_07_26.md` § 2.
- [ ] [REVIEW] P1. **Re-check whether any of the excluded/scoped-down sub-items' gates have since cleared.**
      Specifically: (1) the KALSHI/POLYMARKET cross-AG bleed exclusion (venue vocabulary todo) — check whether
      `sports_satellite_ao_dispatch_batch3_2026_07_25.md:132`'s disposition candidate has shipped; if so, the parent
      doc's venue-vocabulary checkbox can now flip fully, not partially. (2) The T-18h-horizon/cap-widening design
      choice (dead-zone scan todo) — check whether an operator ruling has since been made; if so, extract a new tracked
      todo for the implementation. (3) Sports P2a sub-items (a) G1 noise-wipe and (b) G2 2015-2017 diagnosis — check
      whether the ambiguity about sub-item (a)'s population overlap with the already-answered §U decision has been
      resolved (an operator confirmation or a fresh census); if resolved, extract as a new tracked todo. (4) The K1/K2
      DELETE-gated `DP_RUN_MOSTLY_EMPTY` re-check sub-part — check whether the K1/K2 legacy-object DELETE (Track V,
      `[OPERATOR]`-gated) has executed; if so, extract the re-check as a new tracked todo. For any of the 4 whose gate
      has cleared, create the follow-up todo (in this doc's own tracked continuation or a new dated batch) rather than
      silently leaving it dropped. **Done when**: each of the 4 items has either (a) a new tracked todo created because
      its gate cleared, or (b) an explicit re-verified confirmation the gate is still closed.
- [ ] [DOC] P1. **Archive `sports_consolidated_native_ao_extract_2026_07_25.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): confirm todo 3 above resolved every excluded/scoped-down item (migrate any
      still-open follow-up to a tracked todo elsewhere) → add the archive banner → run the codex-alignment check (no new
      codex doc was created by this extraction, so this step is a no-op confirmation, not skip-without-checking) → grep
      the corpus for every referrer of `sports_consolidated_native_ao_extract_2026_07_25` (including this finalize doc's
      own filename) and fix each path to point at the archived location → clear `locked_by` (already empty here,
      confirm). **Done when**: the plan is moved to `plans/archive/2026_07/`, every corpus referrer resolves to the new
      path, and this finalize doc itself gets archived alongside it in the same commit.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — added `check_line_caps.sh`, the script todo 1
  directs the worker to actually run against the parent doc.
