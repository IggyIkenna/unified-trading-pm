---
doc_type: plan
title: Prediction satellite AO batch 5 — finalize (reconcile source docs + re-check the parked conflicts + archive)
summary: >-
  Finalize/gate plan for `prediction_satellite_ao_dispatch_batch5_2026_07_26.md`. Runs ONLY after batch5's three
  dispatched todos land (`gate_on_depends: true`): flips the corresponding items in the 2 source docs
  (`prediction_cqg_residual_2026_07_24.md`, `issues/kalshi_live_capture_regression_and_drift_2026_07_13.md`), re-checks
  whether either parked operator conflict has been ruled since, and archives cqg_residual if todo 1's re-based census
  plus todo 2's wiring genuinely close it. `status: draft` until batch5 itself is operator-approved and dispatched.
status: draft
nature: process
asset_group: [prediction]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [prediction, ao-dispatch, close-out, batch-5, satellite-docs, archival]
related:
  [
    /plans/active/prediction_satellite_ao_dispatch_batch5_2026_07_26.md,
    /plans/active/prediction_cqg_residual_2026_07_24.md,
    /plans/active/issues/kalshi_live_capture_regression_and_drift_2026_07_13.md,
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: predictions_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [prediction_satellite_ao_dispatch_batch5_2026_07_26]
gate_on_depends: true
source: >-
  Paired finalize for prediction_satellite_ao_dispatch_batch5_2026_07_26 per task_template.md §4's
  finalize-plan-coverage rule; drafted by the second /ag-closeout-audit prediction run 2026-07-26 (autonomous).
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# Prediction satellite AO batch 5 — finalize

> **Status: draft — NOT dispatched.** Gated (`gate_on_depends: true`) behind
> `prediction_satellite_ao_dispatch_batch5_2026_07_26.md`. It will not dispatch until batch5 is flipped `active` by the
> operator AND every batch5 todo is done. Do NOT flip this to `active` independently of batch5. `sequential: true`
> because todo 2 needs todo 1's reconciliation done first and todo 3 (archival) must run last.

## Todos

- [ ] [REVIEW] P1. **Reconcile both source docs' items to batch5's outcomes.** For each batch5 todo that shipped, flip
      the corresponding item in its `Source:` doc with a resolving `<repo>@<sha>` + evidence in the same commit: batch5
      todo 1's re-based census → annotate/flip `prediction_cqg_residual_2026_07_24.md` todo 1's stale "94.5% /
      2026-06-11" premise (todo 1 does NOT close that todo — it re-bases it; only the operator's extend-vs- ratify
      ruling closes it, so leave the checkbox open with the measured numbers recorded unless that ruling has landed);
      batch5 todo 2's loader wiring → flip that doc's todo 2 `[x]` with the test evidence, noting the prod promotion
      rides `prediction_phase_ab_residuals_2026_07_24.md`'s gated regen; batch5 todo 3's verdict → strike through item 1
      of `issues/kalshi_live_capture_regression_and_drift_2026_07_13.md`'s "Suggested next step" list with the verdict
      cited, matching how item 3 was closed 2026-07-26. Repo: unified-trading-pm. **Done when**: every shipped batch5
      todo has its source-doc item updated with a resolving reference in the same commit; any NOT-shipped todo is left
      `- [ ]` with a dated note on why.

- [ ] [REVIEW] P2. **Re-check the 2 parked operator conflicts and the non-batchable Deferred set for anything that has
      since cleared.** (a) Has the out-of-lifecycle-cell question (`empty_confirmed[EXPECTED_*]` out-of-window vs
      `expected_unattempted`, plus whether batch4 todo 1 leg 3's `EMPTY_CONFIRMED_REASONS` removal should proceed) been
      ruled? If yes, record the ruling and — only if it authorises it — note which side of
      `prediction_phase_ab_residuals_2026_07_24.md`:124 vs `prediction_satellite_ao_dispatch_batch4_2026_07_26.md` todo
      1 needs correcting, WITHOUT editing the other plan speculatively. (b) Same for the unmatched-market question
      (`OTHER` vs `attempted_failed[ClassifierConfidenceLow]`); if ruled, the three disagreeing surfaces named in
      batch5's Deferred (the `classifiers.py` module docstring, `classify_polymarket_to_canonical_group`, and MTDS
      `rebuild_prediction_manifest.py`:612) need reconciling to one contract — file that as its own scoped todo, do not
      fold a three-repo contract change into this finalize. (c) Re-check the operator-gated / upstream-blocked /
      time-gated Deferred items for any whose named blocker has demonstrably moved; if one has, note it as a batch6
      candidate. **Done when**: each of (a), (b) and (c) has either a recorded ruling + its consequence, or an explicit
      re-verified "gate still open" line with the date — and no already-asked operator question is re-asked a second
      time. Repo: unified-trading-pm.

- [ ] [DOC] P3. **Archive the fully-closed source doc(s) + update the closeout digest.** If
      `prediction_cqg_residual_2026_07_24.md` reaches 0 genuinely-open items (todo 2 shipped AND todo 1 either ruled or
      demonstrably moot on the re-based numbers), run the 6-step archival ritual and move it to `plans/archive/2026_07/`
      — including step 5, updating every corpus referrer's path (at minimum
      `prediction_consolidated_closeout_2026_07_18.md`'s "Aggregated source docs" entries at lines 302-306 and 349-355,
      plus batch5 and this plan's `related:`). If it does not reach 0, leave it active with a one-line dated residual
      note. Then archive batch5 + this finalize together in the same commit, per the batch1/2/3/4 precedent. Repo:
      unified-trading-pm. **Done when**: cqg_residual is either archived with every referrer resolving to the new path,
      or has a dated residual note explaining why it stays active; batch5 and this doc are archived alongside; and the
      closeout digest reflects the outcome. Codex-alignment check: batch5 creates no new durable contract, so nothing to
      update — confirm and record that explicitly rather than skipping the step.

## Progress Log

- 2026-07-26 (autonomous, second `/ag-closeout-audit prediction` run): drafted as the paired finalize for
  `prediction_satellite_ao_dispatch_batch5_2026_07_26.md`. Inert (`status: draft`, gated on batch5) until the operator
  approves + dispatches batch5.
