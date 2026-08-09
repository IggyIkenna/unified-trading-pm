---
doc_type: issue
title:
  tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md sits at the exact 1000-line hard cap
  — a routine na-eligibility-audit Progress Log marker (and a genuine cross-doc conflict finding) could not be recorded
  there
summary: >-
  `plans/archive/2026_08/issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md` is
  exactly 1000 lines (`wc -l`). `check_line_caps.sh`'s `PLAN_HARD_CAP=1000` check uses `-gt` (strictly greater than), so
  the file itself is not currently failing the gate — but it cannot absorb even one more line without doing so at the
  next commit that touches it. Confirmed live during a 2026-08-08 na-eligibility-audit (tradfi tranche) Phase 3 apply
  pass: a 21-line edit (a `related:` cross-reference + a dated Progress Log marker) pushed the file to 1021 and was
  rejected by `check_line_caps.sh` in SCOPED mode as a NEW HARD violation; the small-marker-append exception
  (`check_line_caps.sh`'s own 2026-08-02 operator-ruling carve-out) does NOT cover this case because it only applies
  when the file is ALREADY over cap before the commit — a file sitting exactly AT the 1000-line boundary has zero
  headroom for even a 1-line addition, and the carve-out's own `PRE_COMMIT_LINES -gt PLAN_HARD_CAP` check can never be
  true for a doc starting at exactly 1000. This is the SAME failure class as
  `/plans/archive/2026_08/issues/prediction_cross_venue_arb_line_cap_blocks_marker_2026_08_07.md` (filed one day earlier
  for a different doc in a different tranche) — but that doc was ALSO at-cap; this is now the SECOND independent
  occurrence, suggesting a doc sitting exactly at the 1000-line boundary (not yet over) is not a rare edge case in this
  corpus.
status: resolved
nature: issue
asset_group: [tradfi, cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [plan-hygiene, line-caps, progress-log, na-eligibility-audit, doc-maintenance]
related:
  [
    /plans/archive/2026_08/issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md,
    /plans/active/issues/mdps_tradfi_ohlcv_15m_24h_conversion_still_zero_2026_07_27.md,
    /plans/archive/2026_08/issues/prediction_cross_venue_arb_line_cap_blocks_marker_2026_08_07.md,
    /plans/active/task_template.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: 2026-08-08
author: na_eligibility_auditor (agt-29c933, slot 4)
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: docs_reconciler
drift_direction: advance-code
depends_on: []
source:
  [
    "Found 2026-08-08 (na_eligibility_auditor, slot 4, dispatch agt-29c933) while running /na-eligibility-audit tradfi
    Phase 3 (apply KEEP-NA verdict markers) — the target doc was at the exact 1000-line hard cap, blocking both the
    marker write and a genuine cross-doc conflict finding surfaced by the same Phase-1 classification pass.",
  ]
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    /plans/archive/2026_08/issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md,
    /plans/active/task_template.md,
    scripts/plan-hygiene/check_line_caps.sh,
  ]
supersedes:
superseded_by:
---

# tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md is at the 1000-line hard cap

> **ARCHIVED 2026-08-09** — obsolete-by-archival: the target doc was archived wholesale rather than trimmed (its own
> sole open todo got extracted elsewhere the same day, leaving it 0-open-todos). See this doc's own Progress Log.

## What I found

`plans/archive/2026_08/issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md` is
exactly 1000 lines. Its sole open todo (line 247, `[DESIGN] P2`, "RULED 2026-08-07 — YES, build it, MDPS-owned") sits
well before its `## Progress Log` section (line 815-1000, ~185 lines, dated entries starting 2026-07-15) — unlike the
prediction-tranche precedent below, the open item here is cleanly separated from the historical narrative, which should
make a safe extraction considerably easier to verify.

**A genuine cross-doc conflict finding could not be recorded because of this cap.** The 2026-08-08 na-eligibility-audit
Phase-1 classification pass found that
`/plans/active/issues/mdps_tradfi_ohlcv_15m_24h_conversion_still_zero_2026_07_27.md` already BUILT and LIVE-VERIFIED the
exact "general-purpose ohlcv_1m→ohlcv_15m/24h MDPS aggregation" mechanism this doc's sole open todo calls for —shipped
`market-data-processing-service@0671953` + `unified-api-contracts@079d48ff` (2026-08-03, 4 days BEFORE this doc's
2026-08-07 "build it, general-purpose" ruling), live-proven with 99,711 real candles / 788 new `captured` manifest rows
for CME(non-combo)/NASDAQ/NYSE. That sibling doc also carries its own 2026-08-06 ruling that
`instrument_type=combo`/`futures_chain` grain is DELIBERATELY EXCLUDED from ohlcv_15m/24h ("no downstream consumer
expects combo-grain candles") — verified against features/strategy/ml-service generally, but NOT explicitly checked
against THIS doc's CBOE/`vix_features` need. Independently confirmed in UAC's `market_data_categories.py`: CBOE's
`VENUE_DATA_TYPE_CAPABILITIES` maps CBOE only to `{"index","futures_chain","options_chain"}` instrument_types (no bare
`future`) — i.e. CBOE's VX-futures may themselves fall under the SAME `futures_chain` grain the sibling doc already
excluded (not confirmed against the live catalogue this pass — flagging, not asserting). Net: this doc's "build it,
general-purpose" framing risks either (a) ~90% duplicate work (the mechanism mostly already exists, only needs CBOE
added to a working pipeline) or (b) re-opening a futures_chain-grain policy question already answered "no" elsewhere
without CBOE/vix_features in view when it was answered.

## Why this matters

`/na-eligibility-audit`'s Phase 0 incremental-diff mode skips re-reading a doc on future runs only when it carries a
dated `na-eligibility-audit YYYY-MM-DD` Progress Log marker that is not older than the doc's last edit. This doc cannot
receive that marker while at cap, so every future na-eligibility-audit run (this one runs on a 2-hour timer) will
re-read this ~1000-line doc in full, forever, until the cap is cleared. Worse than the prediction precedent: the
cross-doc conflict finding above is currently only recorded in this issue doc and this run's final chat report — it is
NOT visible to a future worker who opens the target doc directly without also finding this issue doc.

**A tooling gap worth naming**: `check_line_caps.sh`'s small-marker-append exception (2026-08-02 operator ruling)
requires the file to be ALREADY over cap before the commit (`PRE_COMMIT_LINES -gt PLAN_HARD_CAP`). A doc sitting exactly
AT 1000 lines — not yet over — can never satisfy that condition, so the exception silently doesn't help the most common
trigger case (a doc that just reached the boundary through ordinary edits). This is now 2 independent occurrences in 2
days (prediction 2026-08-07, tradfi 2026-08-08) of the same underlying pattern — worth the line-cap remediation owner
considering whether the exception's `PRE_COMMIT_LINES -gt PLAN_HARD_CAP` condition should instead be `-ge` (or the whole
doc should be flagged SOFT once it crosses 900-950L, giving workers a warning before they hit the wall) — flagging as an
observation, not prescribing the fix.

## Recommended fix

Per `task_template.md` finding J ("extract completed Progress Log sections AS YOU GO"): pick the oldest fully-closed
dated sub-section(s) in the 815-1000 range (all dated 2026-07-15 initially per a quick scan — good extraction candidates
since they predate the doc's later findings), confirm the candidate range doesn't cross-reference anything still
relevant to the line-247 open todo, then extract verbatim into
`plans/archive/2026_08/tradfi_unreachable_databento_data_types_history_2026_08.md` (`status: complete`,
`nature: record`, 0 open todos) and leave a one-line pointer in its place. Re-run `wc -l` + `check_line_caps.sh` after
to confirm the doc is back under the soft cap. Once extracted, add the
`mdps_tradfi_ohlcv_15m_24h_conversion_still_zero_2026_07_27.md` cross-reference to the doc's `related:` list and a
Progress Log entry recording the conflict finding above (both described in full here in the meantime).

- [x] ✅ [DOC] P2. **OBSOLETE-BY-ARCHIVAL 2026-08-09** — the target doc's own sole open todo (line-247 `[DESIGN] P2`)
      was extracted the same day to `/plans/active/tradfi_satellite_ao_dispatch_batch9_2026_08_09.md`, leaving 0 open
      todos; the target doc was archived wholesale to
      `/plans/archive/2026_08/issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md`
      (cicd escalation agt-558c62, `check_archive_candidates.sh` ratchet) rather than trimmed in place — the
      line-cap-relief extraction this todo called for no longer has a target (an archived doc isn't subject to the
      active-corpus na-eligibility-audit re-read cost this issue was filed to avoid). The cross-doc conflict finding
      above (against `mdps_tradfi_ohlcv_15m_24h_conversion_still_zero_2026_07_27.md`) is preserved verbatim in this
      still-open issue doc's own "What I found" section and in the target doc's now-archived Progress Log — not lost.
      Repo: unified-trading-pm.

## Progress Log

- **2026-08-08 (na_eligibility_auditor, slot 4, dispatch agt-29c933)**: Filed. Not fixed inline this run — mirrors the
  prediction-tranche precedent's own reasoning: the extraction is mechanical but wants a dedicated verification pass,
  not a rushed side-effect of an unrelated marker write. The source doc's na-eligibility-audit verdict this pass
  (KEEP-NA, valid, 1 open item) stands independently of this line-cap issue; only the Phase-0 incremental-skip
  optimization and the cross-doc conflict finding's visibility ON the source doc are lost until this is fixed.
- **context-scout 2026-08-09**: populated/refreshed context_scope (3 entries).
- **2026-08-09 (cicd escalation agt-558c62, ldr_qg_failure gate fix)**: target doc's sole remaining open todo got
  extracted to `tradfi_satellite_ao_dispatch_batch9_2026_08_09.md` (unrelated batch-dispatch work, same day), leaving it
  0-open-todos and archive-eligible — archived wholesale instead of trimmed. This issue's own todo is now moot; flipped
  obsolete-by-archival, status `resolved`. Gated finalize plan
  (`tradfi_unreachable_databento_data_types_line_cap_blocks_marker_2026_08_08_finalize_2026_08_08.md`) unblocked to
  archive this doc.

## na-eligibility-audit verdict

**na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: **RECLASSIFY `assigned_vm: NA → planning`.** This doc's
sole open todo is a fully bounded, mechanical doc-hygiene extraction with a precise, checkable `Done-when` (verbatim
Progress-Log-section extraction to a dated `_history_2026_08.md` archive, `related:` cross-reference add, conflict
finding recorded, `wc -l` back under 500, `check_line_caps.sh` still green) — no design or operator judgment involved,
and this exact procedure (extract oldest closed dated sections, leave a pointer, re-verify line caps) is already an
established, repeatedly-executed sibling precedent throughout this corpus (e.g. the "line-cap remediation" extractions
already performed on `github_actions_operator_gated_followups_2026_07_17.md` and
`fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md`, both cited by their own Progress Logs) — the same
"self-service default extends to a script/tooling gap with an exact existing sibling precedent" reasoning behind today's
operator-Q&A ruling 9, applied to a doc-hygiene procedure rather than a script flag. **Conflict-check**: (a) no active
`assigned_vm: planning` plan in `parent_epic: tradfi_master` claims this file or the target archive path; (b) no sibling
batch/finalize doc drafted this run touches it; (c) no `tradfi_consolidated_closeout` doc exists to check against; (d)
the sibling `prediction_cross_venue_arb_line_cap_blocks_marker_2026_08_07.md` (same issue shape, different tranche) is
independently still `assigned_vm: NA` — not a prior claim on THIS file, no cross-tranche conflict. Clear — flipped
directly (this issue doc's own single todo already is the properly-scoped work); paired finalize doc authored at
`plans/active/tradfi_unreachable_databento_data_types_line_cap_blocks_marker_2026_08_08_finalize_2026_08_08.md` (placed
directly under `plans/active/`, not `issues/`, since it is `doc_type: plan`).
