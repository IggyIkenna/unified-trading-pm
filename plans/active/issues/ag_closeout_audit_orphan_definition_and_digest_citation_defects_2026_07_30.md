---
doc_type: issue
title: >-
  /ag-closeout-audit's orphan count is not reproducible — the shipped Phase-0 pre-filter counts the explicitly
  NON-covering `_aggregated_sources_` digest as a covering doc, and SKILL.md contradicts the tooling on whether an
  `assigned_vm: NA` doc can be orphaned at all
summary: >-
  Found running `/ag-closeout-audit cefi` (autonomous, 2026-07-30, benchmark stand-in for the scheduled
  `ag_closeout_auditor` per-tranche dispatch). Two independent defects make the skill's headline number ("how many docs
  are orphaned") non-reproducible, and they push in OPPOSITE directions, so they do not cancel. (1)
  `scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py::_closeout_paths()` globs
  `plans/active/{prefix}_consolidated_closeout_*.md`, which MATCHES `<ag>_consolidated_closeout_aggregated_sources_*.md`
  — the discoverability digest SKILL.md Phase 0.1 explicitly declares NON-covering ("treat as NON-covering: being listed
  there is not dispatch"), and which the SAME function's second loop is careful to skip. So a doc mentioned ONLY in the
  digest reads as `cited_somewhere` and is dropped from the candidate list — the audit UNDER-reports orphans. Measured
  on cefi: 3 of 10 fresh orphan candidates were masked this way. Because every AG has such a digest, this affects all 9
  tranches. (2) SKILL.md's "Also NOT /na-eligibility-audit" paragraph states "An `assigned_vm: NA`, `status: active`/
  `open` doc is by definition NOT orphaned (it has an owner: itself)", but the shipped pre-filter only short-circuits
  `self_dispatched = assigned_vm == "planning" and status in ("active","open")` — NA docs stay orphan candidates. On
  cefi the two readings give 0 orphans vs 19 orphans from the identical corpus. Nothing in the skill, PLAN_FORMAT.md, or
  the script's docstring resolves which is intended, and the sports precedent the skill generalizes from reported real
  NA orphans, so the tooling reading is probably right — but that is an inference, not a ruling.
status: open
nature: issue
asset_group: [cefi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ag-closeout-audit, plan-hygiene, script-bug, orphan-definition, measurement-correctness, cross-tranche]
related:
  [
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/cefi_consolidated_closeout_aggregated_sources_2026_07_24.md,
    /plans/archive/issues/ag_closeout_audit_scope_widening_triage_2026_07_26.md,
    /plans/archive/issues/generate_ag_closeout_audit_candidates_ao_ci_infra_membership_stale_after_closeout_archival_2026_07_29.md,
  ]
created: "2026-07-30"
last_updated: "2026-07-30"
parent_epic: agent_operating_framework_master
priority: P1
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: none
assigned_role: cicd
estimate_class: refactor
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.16
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
source: >-
  `/ag-closeout-audit cefi` run 2026-07-30 (autonomous benchmark stand-in for the `ag_closeout_auditor` scheduled
  per-tranche dispatch, tranche=cefi) — Phase 0.2/0.3 covering-set discovery + Phase 1 classification.
context_scope:
  [
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py,
    /plans/archive/issues/ag_closeout_audit_scope_widening_triage_2026_07_26.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
---

# `/ag-closeout-audit` orphan count is not reproducible — two coverage-definition defects

## Finding 1 — the pre-filter counts the NON-covering digest as a covering doc (under-reports orphans, all 9 tranches)

`scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py`:

```python
def _closeout_paths(tranche: str) -> list[Path]:
    prefix = "cross_cutting" if tranche == "cross-cutting" else tranche
    return sorted(PM.glob(f"plans/active/{prefix}_consolidated_closeout_*.md"))

def _covering_paths(tranche: str, include_closeout: bool = True) -> list[Path]:
    paths = list(_closeout_paths(tranche)) if include_closeout else []
    for p in PM.glob(f"plans/active/{prefix}_*.md"):
        name = p.name
        if "aggregated_sources" in name or "_history_" in name:
            continue        # <-- the digest IS excluded here ...
```

The `aggregated_sources` guard exists in the second loop but NOT in `_closeout_paths()`, whose glob
`{prefix}_consolidated_closeout_*.md` matches `cefi_consolidated_closeout_aggregated_sources_2026_07_24.md` on the
`_aggregated_sources_...` suffix. So the digest is re-admitted through the front door and its citations count as
coverage — the exact opposite of SKILL.md Phase 0.1's rule.

This matters because the digest's whole job is to name EVERY doc in the AG. A doc whose only mention anywhere is in that
list is the textbook orphan this skill exists to find, and it is precisely the doc the bug hides.

**Measured on cefi (2026-07-30):** re-running the same computation with the digest removed from the citation base
surfaced 3 additional orphan candidates that the shipped script reports as covered —
`prediction_capture_incident_remediation_2026_07_06.md`, `prediction_live_clob_depth_capture_2026_07_24.md`,
`mdps_candle_path_instrument_type_segment_nondeterministic_2026_07_27.md`. (All 3 turned out to be genuinely covered
elsewhere on a per-doc read — by the `prediction` tranche and by `data_pipeline_check_mdps_features_2026_07_20.md`'s
work-queue respectively — so cefi's true count is unchanged. That is luck, not correctness: the mechanism that hid them
is real and every tranche runs it.)

**Secondary, same function:** `_covering_paths()`'s filename regex is `(dispatch_batch|satellite|_finalize)`, which is
SKILL.md Phase 0.2 path (a) only. Path (b) — the line-cap forks named after their Track/phase — is never followed, so
for cefi the real covering plans `cefi_misc_audits_and_hygiene_2026_07_25.md`,
`cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`, `cefi_track7_candle_namespace_residual_2026_07_25.md` and
`cefi_consolidated_native_ao_extract_2026_07_25.md` are all missing from the covering set (only their `_finalize`
siblings match). This pushes the count the OTHER way (over-reports orphans), which is why the two defects do not cancel
into a safe answer.

## Finding 2 — SKILL.md and the tooling disagree on whether an `assigned_vm: NA` doc can be orphaned

SKILL.md, "Also NOT `/na-eligibility-audit`":

> An `assigned_vm: NA`, `status: active`/`open` doc is by definition NOT orphaned (it has an owner: itself) — this skill
> correctly never touches it.

`generate_ag_closeout_audit_candidates.py::main()`:

```python
self_dispatched = assigned_vm == "planning" and status in ("active", "open")
```

Only `planning` short-circuits. Under the SKILL.md sentence, cefi's orphan count is **0** (every one of its 19 orphans
is `assigned_vm: NA`). Under the tooling, it is **19**. Same corpus, same run, same day.

The tooling reading is very likely the intended one — the skill's stated question is "what does nothing currently
active/dispatched cover", an NA doc is by definition not dispatched, Phase 0.3's inventory step deliberately includes NA
docs, Phase 0.2 explicitly warns NOT to filter discovery on `assigned_vm`, and the sports precedent this skill
generalizes from reported real NA orphans. But that is an inference chain, not a ruling, and it moves the headline
number by 19 on one tranche alone. **This run adopted the tooling reading and labelled it explicitly rather than
guessing silently.**

## Escalation — operator decision needed on Finding 2

Which definition is authoritative for the reported orphan count?

```
A: The TOOLING reading — `assigned_vm: NA` + active/open docs ARE orphan candidates; only `assigned_vm: planning`
   self-covers. Fix SKILL.md's "/na-eligibility-audit" paragraph to say the NA doc's *self-classification* is out of
   scope, not the doc itself.  [WORKER REC — matches the script, Phase 0.2/0.3, and the sports precedent]
B: The SKILL.md reading — NA + active/open is never an orphan. Then patch the script to short-circuit NA too, and
   accept that most tranches report ~0 and the skill measures only `planning`-gap coverage.
C: Neither as written — report BOTH numbers side by side every run (a "dispatched-gap" count and a
   "nothing-owns-this-at-all" count), since they answer different questions.
Other: operator can type a custom answer
```

## Findings 3-4 — two mechanical cefi-corpus items this run surfaced but did not fix (out of its authorized scope)

- `plans/active/issues/instruments_service_cefi_qg_red_on_ldr_head_2026_07_08.md` is `status: open` with **all 3 todos
  `[x]`**, each carrying commit evidence, and no dated section reopening anything. `resolved_by:` is blank. It is
  `archivable_now`.
- `plans/active/issues/cefi_book_snapshot5_schema_contract_ts_event_levels_mismatch_2026_07_28.md`'s open P3 todo
  ("if/when `derivative_ticker` is routed through `finalise_rows_and_path` with `validate=True` it will need the same
  `ts_event`-derivation treatment") is **provably already shipped** —
  `plans/archive/issues/lighter_zksync_derivative_ticker_tardis_numeric_market_id_leaks_into_symbol_schema_2026_07_29.md`
  records `market-tick-data-service@6bf568ee` adding `"derivative_ticker": {}` to `_WIRE_COLUMN_RENAMES` for exactly
  this reason. False-unchecked.

## Todos

- [x] ✅ [SCRIPT] P1. Exclude `*_aggregated_sources_*` from `_closeout_paths()` in
      `scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py` (move the existing `aggregated_sources` guard up,
      or filter in `_closeout_paths()` directly), and add a unit test asserting a doc cited ONLY in the digest is
      reported as `never_cited`. **Done when**: `--tranche cefi --json` no longer lists
      `cefi_consolidated_closeout_aggregated_sources_2026_07_24.md` in `covering_paths`, and the new test fails against
      the current code. Repo: unified-trading-pm. — unified-trading-pm@369df5695. `_closeout_paths()` now filters
      `"aggregated_sources" not in p.name`; `test_aggregated_sources_digest_is_not_a_covering_doc` added and passing.
- [x] ✅ [SCRIPT] P2. Extend `_covering_paths()` to implement SKILL.md Phase 0.2 path (b) — resolve the consolidated
      closeout's frontmatter `depends_on:`/`related:` (and its `_native_ao_extract_*` siblings') to real files and union
      them into the covering set, instead of matching filenames against `(dispatch_batch|satellite|_finalize)` only.
      **Done when**: `--tranche cefi --json`'s `covering_paths` includes the four 2026-07-25 line-cap forks
      (`cefi_misc_audits_and_hygiene`, `cefi_track2_coverage_backfill_checkpoints`,
      `cefi_track7_candle_namespace_residual`, `cefi_consolidated_native_ao_extract`). Repo: unified-trading-pm. —
      unified-trading-pm@369df5695. Implemented via each discovered `_finalize` doc's `depends_on:` resolved to its
      paired main-plan file path (more general than parsing the closeout's own `depends_on:`/`related:`, which are empty
      for cefi — the finalize→main link is the actual mechanical relationship every line-cap fork uses corpus-wide, also
      fixes the same gap independently found by the sports sibling run,
      `ag_closeout_audit_sports_prefilter_covering_gap_and_false_unchecked_p0_2026_07_30.md`). Verified:
      `--tranche cefi --json`'s `covering_paths` now includes all four named forks (16 covering docs, up from 12; 97
      members, down from 102 with the 5 newly-covering main docs excluded).
      `test_finalize_doc_depends_on_pulls_in_its_line_cap_fork_as_covering` added and passing.
- [ ] [OPERATOR] P1. **BLOCKED-OPERATOR-DECISION.** Rule on the Finding-2 escalation above (A/B/C), then reconcile
      whichever of SKILL.md / `generate_ag_closeout_audit_candidates.py` is wrong so the two agree. **Done when**: the
      skill text and the script's `self_dispatched` predicate encode the same definition, and this doc cites the ruling.
      Repo: unified-trading-pm.
- [x] ✅ [PM] P3. Archive `plans/active/issues/instruments_service_cefi_qg_red_on_ldr_head_2026_07_08.md` (Finding 3 —
      all todos done with commit evidence, nothing reopened) per the archival ritual, filling `resolved_by:` first.
      Repo: unified-trading-pm. — unified-trading-pm@a101de9f0. Moved to `/plans/archive/issues/`, `status: resolved`,
      `resolved_by:` filled, banner added, 5 active corpus referrers fixed (2 also carried a stale "still open"
      DESIGN-decision claim, corrected in the same edit); `locked_by: live-defi-rollout` was the known stale branch-name
      artifact, cleared per the established same-pattern precedent
      (`/plans/archive/issues/tradfi_eu_not_draining_source_axis_drift_2026_06_24.md`).
- [x] ✅ [PM] P3. Flip the false-unchecked `derivative_ticker` `ts_event` todo in
      `plans/active/issues/cefi_book_snapshot5_schema_contract_ts_event_levels_mismatch_2026_07_28.md` (Finding 4),
      citing `market-tick-data-service@6bf568ee`. Repo: unified-trading-pm. — unified-trading-pm@(this commit).
      Independently re-verified live in `tardis_shared.py` (`"derivative_ticker": {}` present in `_WIRE_COLUMN_RENAMES`)
      before flipping, not just trusting the citation.

## Progress Log

- **2026-07-30 (autonomous `/ag-closeout-audit cefi`, benchmark stand-in for the `ag_closeout_auditor` per-tranche
  dispatch):** Ran Phases 0-2 read-only over cefi's 58 AG-primary docs. Both defects found while reconciling the shipped
  pre-filter's covering set against SKILL.md Phase 0.1/0.2 by hand. Filed rather than fixed: the run's authorized fix
  class was the Phase-0.3 orthogonality mistag only, and Finding 2 needs an operator ruling nobody was available to
  give. Phase 3 (drafting `cefi_satellite_ao_dispatch_batch4`) deliberately NOT run — SKILL.md requires explicit
  operator approval before shipping a drafted batch pair.
- **2026-07-30 (slot-12, `ag_closeout_auditor` scheduled dispatch, tranche=cefi):** Fixed both script bugs (todos 1-2),
  archived the Finding-3 doc and flipped the Finding-4 false-unchecked todo (todos 4-5). Todo 3 (Finding 2's
  NA-orphan-definition ruling) stays open — genuinely operator-gated, not guessed. Adopted the same interim "tooling
  reading" (A) as this doc's prior run for this session's own Phase 1 classification, labelled explicitly, not silently.
  Proceeding to a fresh Phase 0-3 pass over the corrected candidate set (see
  `/plans/active/cefi_satellite_ao_dispatch_batch4_2026_07_30.md` if drafted).
- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): RECLASSIFY -> `assigned_vm: planning` (in place, name
  unchanged). 2 SCRIPT todos are bounded script fixes with explicit done-whens; the one genuine judgment call is
  correctly `[OPERATOR]`-tagged (stays non-dispatchable). Conflict-check clear
  (`ag_closeout_audit_scope_widening_triage` cites a different, already-archived defect). Shared conflict-check
  protocol: `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` sect.3 - CLEARED.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
