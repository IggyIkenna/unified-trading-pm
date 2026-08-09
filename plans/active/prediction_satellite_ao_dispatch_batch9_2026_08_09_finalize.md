---
doc_type: plan
title: Prediction satellite AO batch 9 — finalize (reconcile source doc + archive)
summary: >-
  Gated closeout for prediction_satellite_ao_dispatch_batch9_2026_08_09.md — machine-held via depends_on +
  gate_on_depends: true until both of that plan's todos are done. Reconciles
  prediction_cross_venue_arb_and_coverage_2026_07_24.md's own checkboxes for the 2 items batch9 closes, re-checks the 3
  not-extracted items for whether any blocking condition has since cleared, then archives batch9 via the standard 6-step
  ritual.
status: active
nature: process
asset_group: [prediction]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [prediction, ao-dispatch, close-out, batch-9, satellite-docs, archival]
related:
  [
    /plans/active/prediction_satellite_ao_dispatch_batch9_2026_08_09.md,
    /plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: predictions_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.32
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/prediction_satellite_ao_dispatch_batch9_2026_08_09.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md,
  ]
depends_on: [prediction_satellite_ao_dispatch_batch9_2026_08_09]
gate_on_depends: true
source: >-
  Targeted satellite-batch extraction (2026-08-09), per task_template.md §4's finalize-plan-coverage rule.
assigned_role: data_engineering
effort: high
sequential: true
drift_direction: advance-code
---

# Prediction satellite AO batch 9 — finalize

**status: active — gated on batch9's 2 todos via `depends_on` + `gate_on_depends: true`.**

## Todos

- [x] ✅ [REVIEW] P1. **Source-doc reconciliation**: confirm `prediction_cross_venue_arb_and_coverage_2026_07_24.md`
      shows both extracted items closed — the series-scoped Kalshi historical-backfill todo and the cqg batch
      re-classification `--apply` todo — either flipped `[x]` with the batch9 commit citation, or annotated with a
      pointer to it. Repo: unified-trading-pm. Done when: both items are closed-by-citation with no orphaned "still
      looks open" gap; also re-verify the doc's own line count is still under `check_line_caps.sh`'s hard cap after the
      edit (the source doc was measured at 999-1000 lines as of 2026-08-08 per a sibling batch's own line-cap extraction
      todo). **DONE 2026-08-09.** Both extracted items already live only in
      `plans/archive/2026_08/prediction_cross_venue_arb_and_coverage_history_2026_08.md` (not in the active doc — the
      active doc carries zero orphaned open references to either) as `EXTRACTED 2026-08-09 → batch9.md` stubs; the stubs
      described the work as still-remaining, which was stale now that batch9 finished both. Appended a
      `**Reconciled 2026-08-09 (finalize P1)**` closure note to each stub (mirrors this doc's own established
      reconciliation pattern at its line 305): the Kalshi historical-backfill item cites
      `instruments-service@3f2ddca0`/`e2e-testing@5e2f90e` (build) +
      `instruments-service@d65dc051`/`e2e-testing@244e2cc` (honest-absence fix) + VM
      `mtds-prediction-kalshihistgap-20260809-195223` (2658/2658 markets manifest-verified); the cqg BATCH
      re-classification item cites VM `mtds-prediction-kalshi-cqg-rewalk-20260809-101228` (63/63 chunks,
      `failed_unclassified: 0`) + the beta-preview dry-run confirming non-OTHER. Active source doc unchanged at 381
      lines (well under the 1000-line hard cap); `check_line_caps.sh` run clean.
- [x] ✅ [DOC] P2. **Re-check the 3 not-extracted items** (tarball-overwrite race, fixture-pairing team-name
      canonicaliser, and `prediction_consolidated_closeout_2026_07_18.md`'s own 0-todo status) for whether anything has
      changed — in particular whether `prediction_satellite_ao_dispatch_batch6_2026_07_29.md`'s team-name-alias work has
      landed, which would let the fixture-pairing residual's citation be closed at the source. Repo: unified-trading-pm.
      Done when: an explicit still-held / cleared verdict is recorded for each. **DONE 2026-08-09.** Verdicts: (1)
      tarball-overwrite race — **STILL HELD**, unchanged since the 2026-08-08/09 na-eligibility-audits (genuine
      open-ended infra design question, two named options, no directive). (2) fixture-pairing team-name canonicaliser —
      **CLEARED**: batch6's `[DATA] P2` "team-name alias tables" todo is DONE 2026-08-05
      (`unified-api-contracts@41c13454` verified reachable on origin, `strategy-service@217e5b0e`;
      `unified_api_contracts/external/sports/team_mappings.py` confirmed present) — closed the citation at the source
      via a closure note appended to `prediction_cross_venue_arb_and_coverage_2026_07_24.md`'s "Still open" sub-note
      (the parent fixture-pairing-residual checkbox stays unchecked — a separate, unrelated open provenance question the
      source doc's own 2026-08-09 na-eligibility-audit flags as "Finding 5" is not resolved by this closure). (3)
      `prediction_consolidated_closeout_2026_07_18.md`'s 0-todo status — **STILL HELD / VALID**: re-verified live, 0
      open native todos (`grep -c '^- \[ \]'` = 0), `archive_exempt: true` coordination hub, all 4 child Phase A-E plans
      (`prediction_phase_ab_residuals_2026_07_24.md`, `prediction_phase_c_data_status_ui_2026_07_24.md`,
      `prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md`,
      `prediction_phase_e_football_arb_live_2026_07_24.md`) confirmed still `status: active` with open todos (7+2+5+3=17
      total).
- [ ] [DOC] P1. **Archive `prediction_satellite_ao_dispatch_batch9_2026_08_09.md`** via the standard 6-step ritual (per
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`): confirm todo 2's verdict is recorded, add
      the archived-banner cross-reference, run the post-phase codex audit, confirm no new CLAUDE.md contract is owed,
      update every corpus referrer, `git mv` to `plans/archive/2026_08/`. Repo: unified-trading-pm. Done when: batch9 is
      at its archived path with every referrer updated and this finalize plan's own todos all `[x]`.

## Progress Log

- 2026-08-09 (targeted satellite-batch extraction, RECLASSIFY-sweep follow-up): drafted alongside batch9,
  `status: active`, gated via `depends_on` + `gate_on_depends: true`. No work started — waiting on batch9's dispatch
  - completion.
- 2026-08-09 (todo 1 DONE, slot 24): batch9's own 4 todos confirmed all `[x]` (gate satisfied). Source-doc
  reconciliation done: both extracted items (series-scoped Kalshi historical-backfill, cqg BATCH re-classification
  `--apply`) live only as archived `EXTRACTED → batch9.md` stubs in
  `plans/archive/2026_08/prediction_cross_venue_arb_and_coverage_history_2026_08.md` (the active source doc carries no
  orphaned open reference to either) — appended a `Reconciled 2026-08-09 (finalize P1)` closure note to each stub citing
  batch9's shipped SHAs/VMs, mirroring the doc's own existing reconciliation-note convention. Active source doc line
  count re-verified: 381 lines, well under the 1000-line hard cap; `check_line_caps.sh` clean.
- 2026-08-09 (todo 2 DONE, slot 11): re-checked all 3 not-extracted items. Tarball-overwrite race — STILL HELD
  (unchanged design question). Fixture-pairing team-name canonicaliser — CLEARED: confirmed batch6's `[DATA] P2`
  team-name-alias-tables todo shipped 2026-08-05 (`unified-api-contracts@41c13454` reachable on origin,
  `team_mappings.py` present on disk); appended a closure note to
  `prediction_cross_venue_arb_and_coverage_2026_07_24.md` closing that specific citation at the source (left the parent
  fixture-pairing-residual checkbox unchecked — a separate open provenance question ("Finding 5") in that doc's own
  2026-08-09 na-eligibility-audit note is untouched by this closure, out of this todo's scope).
  `prediction_consolidated_closeout_2026_07_18.md`'s 0-todo status — STILL HELD/VALID: re-verified 0 open native todos,
  `archive_exempt: true`, all 4 child Phase A-E plans confirmed active with 17 open todos combined. Doc line count
  unaffected (source doc stayed well under cap).
