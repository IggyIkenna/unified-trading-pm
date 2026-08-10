---
doc_type: issue
title:
  "/na-eligibility-audit's body_content_hash strips its own verdict-marker lines but not context-scout's Progress Log
  line — a context-scout-only touch still flips incremental_skip to false, forcing a needless re-verify"
summary: >-
  `generate_na_doc_tranche_inventory.py`'s `body_content_hash()` (the shipped fix for
  `na_eligibility_incremental_diff_false_positive_on_frontmatter_only_backfills_2026_08_03.md`) correctly strips
  frontmatter and its own `**na-eligibility-audit YYYY-MM-DD**` marker lines before hashing, but `/context-scout` writes
  a BODY-level Progress Log line (`- **context-scout YYYY-MM-DD**: populated/refreshed context_scope (N entries).`),
  which is not frontmatter and is not an na-eligibility-audit marker — so it survives into the hashed body and any
  context-scout touch flips `incremental_skip` to `false` even though nothing classification-relevant changed. Measured
  live on the 2026-08-09 tradfi-tranche run (dispatch agt-3df41f): 11 of 25 candidate docs (44%) were flagged "changed
  since verdict" by the script; manual `git diff <marker-sha>..HEAD` on each confirmed the ONLY difference was a
  context-scout Progress Log line addition (2 of the 11 also had an unrelated `effort: xhigh` frontmatter bump, which
  `strip_frontmatter()` already correctly excludes from the hash — that part of the prior fix works as intended). This
  is the same false-positive family the 2026-08-03 issue fixed for frontmatter-only context-scout backfills, but that
  fix predates context-scout also writing a body-level bookkeeping line, which falls through the same gap in a different
  place. Since context-scout runs corpus-wide on its own schedule independent of na-eligibility-audit's
  2-hour/10-tranche cadence, this false-positive recurs on EVERY future run for every doc context-scout has touched
  since that doc's last verdict marker — the exact compounding failure mode the 2026-08-03 issue already described, just
  via a body line instead of a frontmatter field.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    plan-hygiene,
    na-eligibility-audit,
    context-scout,
    incremental-diff,
    false-positive,
    measurement-correctness,
    body-content-hash,
  ]
related:
  [
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /plans/archive/issues/na_eligibility_incremental_diff_false_positive_on_frontmatter_only_backfills_2026_08_03.md,
  ]
created: "2026-08-09"
author: unknown
last_updated: "2026-08-09"
parent_epic: plan_hygiene_master
priority: P3
source:
  "/na-eligibility-audit tranche=tradfi, autonomous scheduled run 2026-08-09 (dispatch agt-3df41f) — found while
  manually `git diff`-verifying every Phase-0 doc flagged 'changed since verdict' before trusting the flag, per the
  SKILL.md Phase-0 'Interim mitigation for date-fallback false-positives' instruction"
assigned_vm: NA
resolved_by:
execution_scope: local-only
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.08
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
archive_exempt: true # 2026-08-10: 0 open todos, full archival deferred (grace-locked referrers) -- see Progress Log
context_scope:
  [/cursor-configs/skills/na-eligibility-audit/SKILL.md, scripts/plan-hygiene/generate_na_doc_tranche_inventory.py]
---

# na-eligibility-audit's body_content_hash is blind to context-scout's own Progress Log marker line

## What I found

`generate_na_doc_tranche_inventory.py` computes `body_content_hash()` as: strip frontmatter, strip any line matching
`_VERDICT_MARKER_LINE_RE` (`**na-eligibility-audit YYYY-MM-DD**...`), then SHA-256 the remainder. This correctly makes
the hash stable across (a) frontmatter-only edits and (b) this skill's own marker additions/updates — both were the
explicit design goals of the fix shipped for
`/plans/archive/issues/na_eligibility_incremental_diff_false_positive_on_frontmatter_only_backfills_2026_08_03.md`.

What it does NOT cover: `/context-scout` writes its own dated marker line directly into the same Progress Log section,
e.g.:

```
- **context-scout 2026-08-09**: populated/refreshed context_scope (6 entries).
```

This line is body content (not frontmatter) and is not an na-eligibility-audit marker, so `_VERDICT_MARKER_LINE_RE` does
not strip it. Its addition changes `body_content_hash()`'s output, so `incremental_skip` computes `false` even when it
is the ONLY change since the doc's last na-eligibility-audit verdict marker.

## Evidence — 11 confirmed false positives, one tranche, one run

Tradfi-tranche Phase 0 (2026-08-09, dispatch agt-3df41f) flagged 21 of 25 candidate docs as "in scope" (not
`incremental_skip`). Manually running `git diff <marker-commit>..HEAD -- <doc>` on each (per SKILL.md's own prescribed
interim-mitigation check) found 11 where the ENTIRE diff was a context-scout line addition (2 of the 11 additionally had
a `+effort: xhigh` frontmatter line, already correctly excluded by `strip_frontmatter()`):

- `plans/active/canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md`
- `plans/active/tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md`
- `plans/active/issues/instruments_docs_audit_outstanding_items_2026_07_08.md` (cefi-owned, read in this run only)
- `plans/active/issues/mtds_is_full_adapter_smoketest_findings_2026_07_07.md` (cefi-owned, read in this run only)
- `plans/active/issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md` (cefi-owned, read in this
  run only)
- `plans/active/issues/tradfi_autonomous_session_operator_decisions_2026_07_25.md`
- `plans/active/issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md`
- `plans/active/issues/tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md`
- `plans/active/issues/tradfi_within_bounds_source_zero_shard_atom_mismatch_2026_07_28.md`
- `plans/active/tradfi_backfill_throughput_followups_2026_07_24.md` (also had `+effort: xhigh`)
- `plans/active/tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md` (also had `+effort: xhigh`)

That's 44% of this one tranche's candidate population re-flagged for full Phase-1 re-classification on zero real content
change. Since context-scout sweeps the whole active corpus independent of this skill's own cadence, the same class
recurs continuously and compounds across all 10 tranches, not just tradfi.

## Recommended fix

Generalize `_VERDICT_MARKER_LINE_RE`'s treatment beyond na-eligibility-audit's own marker: add a sibling regex (or
broaden the existing one) matching `**context-scout YYYY-MM-DD**...` lines and strip them the same way before hashing.
While in the file, grep the active corpus for OTHER dated bookkeeping-marker conventions already in informal use
(`\*\*[a-z][a-z_-]* \d{4}-\d{2}-\d{2}\*\*:` beyond `na-eligibility-audit` and `context-scout` — e.g. `docs-reconciler`,
`plan-reconciler`, `ag-closeout-audit` may write similar dated lines) so the fix is a general "strip any known
sibling-skill dated marker line" rule rather than a second one-off special case that a THIRD skill's marker convention
will just re-trigger again later. Add a regression fixture: a doc whose only post-marker diff is a context-scout (or
other sibling-marker) line must compute `incremental_skip: true`.

## Todos

- [x] ✅ [SCRIPT] P2. In `scripts/plan-hygiene/generate_na_doc_tranche_inventory.py`, extend `body_content_hash()`'s
      marker-line stripping to also exclude `**context-scout YYYY-MM-DD**...` body lines (and any other confirmed
      sibling-skill dated marker convention found via the corpus grep above), so a context-scout-only touch no longer
      changes the hash. Add a unit fixture proving a context-scout-only diff yields `incremental_skip: true`. —
      `unified-trading-pm@a1f72c11c8`: `_BOOKKEEPING_MARKER_SKILL_NAMES = ("na-eligibility-audit", "context-scout")`
      shipped, regression test `test_body_content_hash_stable_across_context_scout_marker_line` added. Verified by
      plan_reconciler infra shard (agt-716973, 2026-08-10): both the code and the test exist live at HEAD.
- [x] ✅ [DOCS] P3. Add a one-line cross-reference in `cursor-configs/skills/na-eligibility-audit/SKILL.md`'s Phase 0
      "Interim mitigation for date-fallback false-positives" section naming this context-scout-specific sub-case
      explicitly, so the next tranche run that hits it can cite this issue instead of independently re-deriving the same
      by-hand verification this run just performed across 11 docs. — shipped alongside the script fix: SKILL.md's Phase
      0 now reads "**`/context-scout`-only sub-case**: a body-level `/context-scout` Progress Log line... fixed by
      generalizing `body_content_hash()`'s marker-stripping to a sibling-marker family; see
      `issues/na_eligibility_hash_blind_to_context_scout_progress_log_line_2026_08_09.md`." Verified live at HEAD by
      plan_reconciler infra shard (agt-716973, 2026-08-10).

## Progress Log

- **2026-08-09** — Filed by `/na-eligibility-audit` (tranche `tradfi`, autonomous scheduled run, dispatch agt-3df41f).
  Found while manually `git diff`-verifying every Phase-0 "in scope" doc before trusting the flag, per SKILL.md's own
  "grep-then-READ, not grep-then-conclude" / interim-mitigation discipline. Filed `assigned_vm: NA` per the
  ask-before-creating default (autonomous run, no operator present) and mirroring the identical two-step precedent this
  doc's own `related:` predecessor used — both todos are bounded/worker-determinable, but deliberately not
  self-reclassified in the same breath as filing; left for an independent future pass (or operator) to conflict-check
  and flip. Checked for an existing conflicting claim before filing (grep for `_VERDICT_MARKER_LINE_RE` and
  `context-scout.*hash` across `plans/active/` — none found).
- **2026-08-10 (plan_reconciler infra shard, agt-716973)** — both todos verified HARD-shipped (code + test + SKILL.md
  cross-reference all confirmed live at HEAD, independently corroborated by
  `infra_satellite_ao_dispatch_batch11_2026_08_09.md:115-145` showing the same items `[x]` with matching evidence) and
  flipped. Doc is now fully done, unlocked — normally archive-ready, but **archival DEFERRED this run**: 5 leading-slash
  referrers to this doc live in 3 docs (`infra_satellite_ao_dispatch_batch11_2026_08_09.md` + its `_finalize` twin +
  `ag_closeout_audit_infra_parked_2026_08_09.md`) that are all inside today's 12h grace window (actively being worked,
  read-only this run) — archiving now would leave those referrers dangling. Leave this doc active; a future run (once
  those 3 docs clear grace) should complete the 6-step ritual.
