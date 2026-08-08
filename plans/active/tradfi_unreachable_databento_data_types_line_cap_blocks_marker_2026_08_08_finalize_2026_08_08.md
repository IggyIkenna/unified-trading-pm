---
doc_type: plan
title: tradfi line-cap-blocks-marker — finalize (verify extraction + archive)
summary: >-
  Gated closeout for the retroactive reclassification of
  issues/tradfi_unreachable_databento_data_types_line_cap_blocks_marker_2026_08_08.md (NA → planning, 2026-08-08
  na-eligibility-audit round7 RECLASSIFY sweep). Machine-held via depends_on + gate_on_depends: true until that doc's
  own todo (extract the target doc's oldest closed Progress Log sections to a dated history archive, add the missed
  cross-reference, record the conflict finding) is done. Verifies the extraction landed cleanly (target doc back under
  the soft cap, check_line_caps.sh still green, the open todo's own text unchanged) and archives the source issue doc
  once genuinely resolved.
status: active
nature: process
asset_group: [tradfi, cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [plan-hygiene, line-caps, ao-dispatch, close-out, reclassification, na-audit]
related:
  [
    /plans/active/issues/tradfi_unreachable_databento_data_types_line_cap_blocks_marker_2026_08_08.md,
    /plans/active/issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md,
    /plans/active/issues/mdps_tradfi_ohlcv_15m_24h_conversion_still_zero_2026_07_27.md,
    /plans/active/task_template.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.08
assigned_role: docs_reconciler
sequential: true
drift_direction: advance-code
depends_on: [tradfi_unreachable_databento_data_types_line_cap_blocks_marker_2026_08_08]
gate_on_depends: true
source: >-
  Authored alongside the 2026-08-08 na-eligibility-audit round7 RECLASSIFY sweep's flip of
  issues/tradfi_unreachable_databento_data_types_line_cap_blocks_marker_2026_08_08.md (NA → planning), per
  plans/active/task_template.md §4's finalize-plan-coverage rule and the retroactive-reclassification naming
  convention in /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md §1(b). Placed directly
  under plans/active/ (not plans/active/issues/) because doc_type: plan must match its path-derived type.
context_scope:
  [
    /plans/active/issues/tradfi_unreachable_databento_data_types_line_cap_blocks_marker_2026_08_08.md,
    /plans/active/issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md,
    scripts/plan-hygiene/check_line_caps.sh,
  ]
locked_by:
locked_since:
supersedes:
superseded_by:
---

# tradfi line-cap-blocks-marker — finalize

> **🔒 GATED, not draft.**
> `depends_on: [tradfi_unreachable_databento_data_types_line_cap_blocks_marker_2026_08_08]` + `gate_on_depends: true`
> holds every todo below until that doc's own extraction todo is `done`. Authored `status: active` (not `draft`) per the
> established no-double-gate precedent used by every other batch/finalize pair in this tranche.

## Todos

- [ ] [REVIEW] P2. **Verify the extraction landed correctly, then reconcile.** Confirm: (a)
      `plans/active/issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md` is back
      under the 500-line soft cap (`wc -l`); (b) `bash scripts/plan-hygiene/check_line_caps.sh` (or its scoped-mode
      invocation) passes clean on the target doc; (c) the extracted archive doc
      (`plans/archive/2026_08/tradfi_unreachable_databento_data_types_history_2026_08.md` or whatever path the worker
      used) carries the extracted sections verbatim, `status: complete`, `nature: record`, 0 open todos; (d) the
      target doc's own open `[DESIGN] P2` todo (line ~247 pre-extraction, "RULED 2026-08-07 — YES, build it,
      MDPS-owned") is textually unchanged by the extraction; (e) the `mdps_tradfi_ohlcv_15m_24h_conversion_still_zero_
      2026_07_27.md` cross-reference was added to the target doc's `related:` list; (f) the cross-doc conflict finding
      from the source issue doc's "What I found" section (the `mdps_tradfi_ohlcv_15m_24h_conversion_still_zero_2026_
      07_27.md` overlap — ~90% duplicate-work risk, the `futures_chain`-grain CBOE/vix_features question) is recorded
      as a dated Progress Log entry on the now-under-cap target doc, not just in the source issue doc. **Done when**:
      all six checks above pass, cited with evidence (line counts, gate output, exact archive path).
- [ ] [DOC] P3. **Archive the source issue doc** (`tradfi_unreachable_databento_data_types_line_cap_blocks_marker_2026_
      08_08.md`) via the standard 6-step ritual once todo 1 confirms the extraction is genuinely complete: add the
      archive banner → grep the corpus for every referrer and repoint each to the archived path → clear `locked_by`
      (already empty) → move to `plans/archive/2026_08/issues/`. **Done when**: the doc is archived, every corpus
      referrer resolves, and `check_reference_paths.py` has not regressed.

## Codex SSOTs

- `/plans/active/task_template.md` finding J — extract completed Progress Log sections as you go
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` — retroactive-reclassification naming
  shape (b) this finalize doc follows

## Progress Log

- **2026-08-08** — Drafted alongside the na-eligibility-audit round7 RECLASSIFY flip of
  `issues/tradfi_unreachable_databento_data_types_line_cap_blocks_marker_2026_08_08.md`. Authored `status: active` per
  the established no-double-gate precedent; `gate_on_depends: true` already machine-holds every task here until the
  source doc's own extraction todo is done.
