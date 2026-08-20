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
last_updated: "2026-08-20"
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
    /plans/active/issues/plan_reconciler_findings_sports_2026_08_19.md,
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

- [x] ✅ [REVIEW] P1. **DONE 2026-08-19 (plan_reconciler, agt-07473e) — `unified-trading-pm@e6e455f6c2`.** The
      extract's citation line numbers had drifted (closeout doc restructured/trimmed multiple times since); matched
      by CONTENT/topic instead. Of the closeout's 17 open checkboxes at run start, 5 were confirmed DONE-but-unflipped
      and flipped (Finding C correction, `sports_reference_v2` post-floor cull, catalogue re-roll, catalogue
      player-grain upgrade, launcher-used determination — each with verified evidence, 2 shas content-verified
      instead after hitting the corpus's known squash-merge SHA-orphaning trap). Also caught + struck 1
      duplicate-dispatch (`sports_satellite_ao_dispatch_batch16_2026_08_17.md` re-drafted the already-shipped
      `sports_reference_v2` cull as unclaimed work). The remaining ~11 open items were confirmed either genuinely
      separate scope, already extracted to an owning satellite/gated plan, or (1 item, the line-532 venue-vocabulary
      cleanup) too entangled with a live separately-tracked contradiction (`STALE 2026-08-14` footystats-mislabel
      pointer) to safely touch this pass — left open, recommendation recorded in
      `plan_reconciler_findings_sports_2026_08_19.md`. Line-cap discipline: the parent was at exactly 1000/1000
      before this edit; flipping + trimming verbose trailers kept it at 998L after. Full detail:
      `plans/active/issues/plan_reconciler_findings_sports_2026_08_19.md`.
- [x] ✅ [DOC] P1. **DONE 2026-08-19 (plan_reconciler, agt-07473e) — confirmed (a): no doc reached a terminal status
      via todo 1's reconciliation.** None of the 5 flips completed `sports_consolidated_closeout_2026_07_19.md` (still
      12 open todos after) or any other doc to 0-open-todos; the 1 cited-as-resolved doc
      (`sports_canonical_raw_truncated_rederive_destroys_corpus_2026_07_16.md`) was already `status: resolved` before
      this pass, not a new transition. No archival triggered by this todo.
- [x] ✅ [REVIEW] P1. **DONE 2026-08-19 (plan_reconciler, agt-07473e) — all 4 items resolved.** (1) KALSHI/POLYMARKET
      cross-AG bleed: `sports_satellite_ao_dispatch_batch3_2026_07_25.md`'s disposition candidate shipped DONE
      2026-07-31 (now archived at `plans/archive/2026_07/`) — gate cleared; the closeout's line-532 venue-vocabulary
      checkbox could now partially advance, but is left open per todo 1's note above (too entangled with a separate
      live contradiction to safely edit this pass — recorded as a recommendation, not silently dropped). (2) T-18h
      horizon/cap-widening design choice: no operator ruling found (`grep -rl "T-18h" plans/active/issues/` — 0
      hits) — gate still closed, no new todo needed. (3) Sports P2a sub-items (a)/(b): BOTH already resolved AND
      already tracked+done in `sports_closeout_track_s2_foldin_2026_07_25.md` (line 172: sub-item (a) G1 noise-wipe
      DONE; line 216: sub-item (b) G2 2015-2017 diagnosis DONE 2026-07-27) — no new todo needed, follow-through
      already complete. (4) K1/K2 DELETE-gated `DP_RUN_MOSTLY_EMPTY` re-check: the Track V K1/K2 delete executed
      2026-07-28 (`market-tick-data-service@26201c44`, verified in the closeout doc); the gated re-check was ALREADY
      extracted AND already completed in `sports_closeout_track_s2_foldin_2026_07_25.md` (line 437-445, DONE
      2026-08-05 — spike resolved as predicted, no code change needed) — no new todo needed.
- [ ] [DOC] P1. **Archive `sports_consolidated_native_ao_extract_2026_07_25.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): confirm todo 3 above resolved every excluded/scoped-down item (migrate any
      still-open follow-up to a tracked todo elsewhere) → add the archive banner → run the codex-alignment check (no new
      codex doc was created by this extraction, so this step is a no-op confirmation, not skip-without-checking) → grep
      the corpus for every referrer of `sports_consolidated_native_ao_extract_2026_07_25` (including this finalize doc's
      own filename) and fix each path to point at the archived location → clear `locked_by` (already empty here,
      confirm). **Done when**: the plan is moved to `plans/archive/2026_07/`, every corpus referrer resolves to the new
      path, and this finalize doc itself gets archived alongside it in the same commit. **PRE-CONDITIONS NOW MET
      (2026-08-19, plan_reconciler agt-07473e) — todos 1-3 above are all DONE, the extract plan is 33/33 verified
      done, no excluded item remains open.** NOT executed this pass: `grep -rl` found **21 corpus referrers**
      (excluding this doc and the extract itself) — several require live-vs-historical judgment (dated
      `plan_reconciler_findings_*` reports should likely stay pointing at the pre-archive path as accurate history;
      `sports_consolidated_closeout_2026_07_19.md` alone cites the extract plan well over a dozen times, including 5
      just added this pass, and is already at 998/1000 lines — a bulk repoint there risks the line cap again;
      `plans/epics/sports_master.md` + `plans/epics/html/sports_master.html` are the epic hub + its generated report).
      A genuinely separate, bounded pass — full referrer list not re-derived here, re-run
      `grep -rl "sports_consolidated_native_ao_extract_2026_07_25" plans/active/ plans/epics/` for the current set.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — added `check_line_caps.sh`, the script todo 1
  directs the worker to actually run against the parent doc.
- **context-scout 2026-08-17**: re-verified; context_scope unchanged (5 entries, all resolve).
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
