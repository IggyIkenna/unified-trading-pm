---
doc_type: plan
title: Sports satellite AO batch 6 — finalize (reconcile source docs + resolve deferrals + archive both)
summary: >-
  Gated closeout for sports_satellite_ao_dispatch_batch6_2026_07_26.md — machine-held via depends_on + gate_on_depends:
  true until all 9 of that plan's todos are done. Mirrors the batch3/batch4/batch5-finalize pattern (reconcile each
  distinct source doc's checkboxes once its batch-6 todo lands, then re-check the Deferred conflict-gated +
  operator-gated items for any that have since cleared), and then carries the 4th step batch2-5's finalize plans are all
  missing and which batch6 todo 7 adds to them: archive every source doc this batch drove to terminal status, in the
  same commit as the status flip, so `check_terminal_status_archived.py` never sees a terminal doc in `plans/active/`.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-6, satellite-docs, archival]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch6_2026_07_26.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26_finalize.md,
    /plans/archive/issues/sports_plan_reconcile_operator_decisions_2026_07_26.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-30"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.3
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [sports_satellite_ao_dispatch_batch6_2026_07_26]
gate_on_depends: true
source: >-
  /ag-closeout-audit skill run 2026-07-26 (second run of the day, autonomous mode), per task_template.md §4's
  finalize-plan-coverage rule — every assigned_vm: planning plan needs a companion gated finalize plan, mirroring the
  batch2/batch3/batch4/batch5 precedent.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/sports_satellite_ao_dispatch_batch6_2026_07_26.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26_finalize.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
---

# Sports satellite AO batch 6 — finalize

> **⚠️ `status: draft` — NOT dispatched.** Flips to `active` only when its parent batch does, on explicit operator
> approval. Drafted in the same turn as the parent per `task_template.md` § 4's finalize-plan-coverage rule.

> **Machine-gated on `sports_satellite_ao_dispatch_batch6_2026_07_26.md`** (`depends_on` + `gate_on_depends: true`) —
> the dispatcher will not queue any todo below until all 9 tasks in that plan are `done`. `sequential: true` because
> todo 2 needs todo 1's reconciliation done first, todo 3 needs todo 2's verdicts, and todo 4 (archival) must run last.

## Todos

- [x] ✅ [REVIEW] P1. **Reconcile all 9 source docs' checkboxes.** — unified-trading-pm (this commit). All 9 source docs
      reconciled. Three special cases confirmed: (a) part2 (7 open) + part3 (3 open) — all checkboxes in sanctioned
      states (flipped/owned/open-with-reason); (b) part3 §Y: deployment-service@5c9d673 confirmed in §Y only, todo 2 did
      NOT double-flip; (c) todos 4+8: all prose items properly converted, none dropped. SHA verification: 11/12 cited
      SHAs on origin; instruments-service@696921d3 was stale pre-rebase SHA → corrected to b03b7994 in batch6 plan. 1
      source doc flipped to status: resolved (multisource_xg — [OPERATOR/DESIGN] checkbox flipped citing batch6 todo 11
      ruling + features-service@961c4ad9). 3 source docs already archived+resolved. 4 source docs stay open with
      documented remaining work (part2 7 open, part3 3 open, odds_api_outage 1 open — backfill not yet launched,
      odds_api_raw_ingestion already resolved).

- [x] ✅ [REVIEW] P1. **Re-check the 8 Deferred items from batch6's own doc** — unified-trading-pm (this commit).
      **COUNT CORRECTION: 5 items, not 8** (the finalize plan's "8" was stale — it drifted during authoring). 2
      conflict-gated + 3 operator-gated (1 doc-level + 2 meta-parks). **Conflict-gated (both still unresolved):** (1)
      part3 §Z matchday-recovery vs Track F — Track F re-scoped to post-floor only but not yet executed; ordering
      conflict persists, neither superseded nor sanctioned-interim decision made by the closeout. (2) Reconcile-in-place
      vs archive-as-history — measured 10 surviving open items (part2: 7, part3: 3), well above the ~4-item threshold
      for cheap archive-as-history, so in-place remains the working assumption. **Operator-gated:** (3)
      ml_service_sports_clv `[CODE] P3` — still genuinely unresolved, pure design decision (wire `--family` vs drop
      validation), no operator ruling found. (4) Generalise todo 7's finalize-plan fix workspace-wide (meta-park) —
      still parked, awaiting operator approval, no ruling found. (5) Tranche ownership for
      `sports_prediction_mvp_writetime_precompute` (meta-park) — **RESOLVED by CORRECTION 2026-08-05**: cross-cutting
      batch2 finalize confirmed the doc IS already cross-cutting-owned via Track 23 in
      `cross_cutting_consolidated_closeout_2026_07_25.md`; original "invisible to every tranche" premise was measurably
      wrong. No batch7 extraction needed — ownership is already correct. **No operator questions re-asked** — all items
      either still-deferred with re-verified confirmation or resolved by subsequent correction.

- [ ] [REVIEW] P1. **Verify batch6 todo 7's fix actually closed the loop it was written to close, and re-run the gate
      that caught it.** Todo 7 adds a source-doc-archival todo to 5 sports `*_finalize` plans. Confirm (a) all 5 carry
      it, (b) `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` reports 0 hard failures, and (c)
      `.venv/bin/python scripts/plan-hygiene/check_terminal_status_archived.py` reports 0 violations against its
      baseline — including after THIS plan's own todo 1 flipped source docs to `resolved`, which is the exact transition
      that generated today's 10-violation hard failure. If todo 1 flipped any doc to `resolved` without archiving it in
      the same commit, that is the bug todo 7 was meant to prevent reproducing itself inside this very plan — fix it
      here and record that it happened. **Done when**: all three checks pass and the interaction between todo 1 and todo
      7 is explicitly confirmed clean.

- [ ] [DOC] P1. **Archive `sports_satellite_ao_dispatch_batch6_2026_07_26.md` AND every source doc it drove to terminal
      status** via the standard 6-step ritual (per CLAUDE.md's plan-archival rule): migrate any remaining Deferred items
      to a tracked todo elsewhere (todo 2 above should have resolved or re-confirmed all 6 — verify none silently
      vanish) → add the archive banner → run the codex-alignment check (batch6 establishes no new durable contract;
      confirm still true, and note that the finalize-plan-pattern generalisation was deliberately parked, so
      `task_template.md` § 4 is expected to be UNCHANGED) → grep the corpus for every referrer of
      `sports_satellite_ao_dispatch_batch6_2026_07_26` and fix each path to point at the archived location → clear
      `locked_by` (already empty; confirm). **This is the step batch2-5's finalize plans omit**: any source doc todo 1
      flipped to `status: resolved`/`complete` moves to `plans/archive/issues/` (or `plans/archive/2026_07/` for a
      non-issue plan) in the SAME commit as the flip, each with a genuine resolution banner and verified 0 open todos —
      never left terminal-but-active for a CI gate to sweep up. **Done when**: batch6 is in `plans/archive/2026_07/`,
      every corpus referrer resolves to the new path, every terminal source doc is archived alongside, this finalize doc
      itself is archived in the same commit, and `run_hygiene_sweep.sh --ci` is still 0-hard-failures afterwards.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: refreshed context_scope (6 entries) -- dropped the batch-naming/conflict-check codex doc
  (batch-creation concern, not finalize-reconcile); this is a pure archival gate, no source-code target.
