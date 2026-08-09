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
status: complete
nature: process
asset_group: [tradfi, cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [plan-hygiene, line-caps, ao-dispatch, close-out, reclassification, na-audit]
related:
  [
    /plans/archive/2026_08/issues/tradfi_unreachable_databento_data_types_line_cap_blocks_marker_2026_08_08.md,
    /plans/archive/2026_08/issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md,
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
effort: max
sequential: true
drift_direction: advance-code
depends_on: [tradfi_unreachable_databento_data_types_line_cap_blocks_marker_2026_08_08]
gate_on_depends: true
source: >-
  Authored alongside the 2026-08-08 na-eligibility-audit round7 RECLASSIFY sweep's flip of
  issues/tradfi_unreachable_databento_data_types_line_cap_blocks_marker_2026_08_08.md (NA → planning), per
  plans/active/task_template.md §4's finalize-plan-coverage rule and the retroactive-reclassification naming convention
  in /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md §1(b). Placed directly under
  plans/active/ (not plans/active/issues/) because doc_type: plan must match its path-derived type.
context_scope:
  [
    /plans/archive/2026_08/issues/tradfi_unreachable_databento_data_types_line_cap_blocks_marker_2026_08_08.md,
    /plans/archive/2026_08/issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md,
    scripts/plan-hygiene/check_line_caps.sh,
  ]
locked_by:
locked_since:
supersedes:
superseded_by:
---

# tradfi line-cap-blocks-marker — finalize

> **ARCHIVED 2026-08-09** — both todos done (extraction premise superseded by wholesale archival of the target doc;
> source issue doc archived). See Progress Log.

> **🔒 GATED, not draft.** `depends_on: [tradfi_unreachable_databento_data_types_line_cap_blocks_marker_2026_08_08]` +
> `gate_on_depends: true` holds every todo below until that doc's own extraction todo is `done`. Authored
> `status: active` (not `draft`) per the established no-double-gate precedent used by every other batch/finalize pair in
> this tranche.

## Todos

- [x] ✅ [REVIEW] P2. **Extraction premise superseded — verified the actual outcome instead.** The target doc's sole
      open `[DESIGN] P2` todo was extracted to `tradfi_satellite_ao_dispatch_batch9_2026_08_09.md` the same day
      (2026-08-09, unrelated batch-dispatch work), leaving it 0-open-todos — archived WHOLESALE rather than trimmed in
      place, so the line-cap-relief extraction this todo specified no longer has a target (an archived doc isn't re-read
      by the active-corpus na-eligibility-audit sweep this issue was filed to unblock). Confirmed: (a) the target doc is
      at
      `/plans/archive/2026_08/issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md`
      with an ARCHIVED banner + `status: resolved`; (b) the cross-doc conflict finding (vs.
      `mdps_tradfi_ohlcv_15m_24h_conversion_still_zero_2026_07_27.md`) is preserved verbatim in both the source issue
      doc's "What I found" and a new dated Progress Log entry on the now-archived target doc — not lost. Repo:
      unified-trading-pm. cicd escalation agt-558c62.
- [x] ✅ [DOC] P3. **Archived the source issue doc** — `git mv` to
      `plans/archive/2026_08/issues/tradfi_unreachable_databento_data_types_line_cap_blocks_marker_2026_08_08.md`,
      archive banner added, `status: resolved`, its own todo flipped obsolete-by-archival. Corpus referrers (7
      active-corpus files with the leading-slash `/plans/active/issues/...` form) repointed to the archived path;
      `check_reference_paths.py`'s existence-check ratchet does not scan `plans/archive/` sources, so no further
      referrer sweep is needed. Repo: unified-trading-pm. cicd escalation agt-558c62.

## Codex SSOTs

- `/plans/active/task_template.md` finding J — extract completed Progress Log sections as you go
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` — retroactive-reclassification naming
  shape (b) this finalize doc follows

## Progress Log

- **2026-08-08** — Drafted alongside the na-eligibility-audit round7 RECLASSIFY flip of
  `issues/tradfi_unreachable_databento_data_types_line_cap_blocks_marker_2026_08_08.md`. Authored `status: active` per
  the established no-double-gate precedent; `gate_on_depends: true` already machine-holds every task here until the
  source doc's own extraction todo is done.
- **context-scout 2026-08-09**: populated/refreshed context_scope (3 entries).
- **2026-08-09 (cicd escalation agt-558c62, ldr_qg_failure gate fix)**: gate cleared by the source doc's todo flipping
  obsolete-by-archival (see that doc). Both todos here done — extraction premise verified superseded, source issue doc
  archived. Archiving this finalize plan now (both todos `[x]`, unlocked).
