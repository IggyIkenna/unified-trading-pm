---
doc_type: plan
title: Operator ruling record — ci-tranche line-cap splits applied under Trust Mode (2026-08-16)
summary: >-
  Traceability record for two plan-splitting decisions the 2026-08-16 ci-tranche plan_reconciler run (dispatch
  agt-4f7ad9) applied directly instead of parking, per the 2026-08-15 /plan-reconcile Trust Mode ruling ("every item
  the Calibration section would otherwise route to STILL ASK/PARK — because it's a preference/authority call, not a
  provable fact — gets the [WORKER REC] applied directly... logged with full reasoning in a dated
  operator_ruling_record_<slug>_<date>.md doc"). Both splits are `[WORKER REC]`: reproduce the SAME extraction pattern
  (`_progress_log_history_<date>.md`, verbatim relocation of closed historical narrative, zero content lost, a
  one-paragraph pointer left behind) an earlier session already applied successfully to a sibling doc in this exact
  tranche (`plans/archive/2026_08/github_actions_operator_gated_followups_progress_log_history_2026_08_03.md`,
  2026-08-03) and that the 2026-08-10 predecessor plan_reconciler run explicitly named as its own
  "Recommended NEXT item" — the highest-leverage unblock available, sitting parked for 6 days with no operator answer
  ever having disagreed with the same recommendation across this doc-chain's history.
status: complete
nature: record
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-reconciler, ci, trust-mode, line-cap-remediation, operator-ruling-record]
related:
  [
    /plans/active/github_actions_operator_gated_followups_2026_07_17.md,
    /plans/active/issues/pytest_timeout_60s_flaky_under_contention_continued2_2026_08_03.md,
    /plans/archive/2026_08/github_actions_operator_gated_followups_hard_won_context_and_cost_ruling_history_2026_08_16.md,
    /plans/archive/2026_08/pytest_timeout_60s_flaky_under_contention_continued2_progress_log_history_2026_08_16.md,
    /plans/archive/2026_08/github_actions_operator_gated_followups_progress_log_history_2026_08_03.md,
    /plans/active/issues/plan_reconciler_findings_ci_2026_08_10.md,
  ]
created: 2026-08-16
last_updated: 2026-08-16
parent_epic: plan_hygiene_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.08
assigned_role: script
drift_direction: none
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source:
  - "plan_reconciler ci-tranche run agt-4f7ad9, 2026-08-16"
---

# Operator ruling record — ci-tranche line-cap splits (2026-08-16)

## Context

`cursor-configs/skills/plan-reconcile/SKILL.md` §"Trust mode (2026-08-15 operator ruling)" authorizes this run to apply
a `[WORKER REC]` directly — instead of asking/parking — for any item its own Calibration section would otherwise
classify as "STILL ASK / PARK" (a preference/authority call, not a provable fact), with the one carve-out being any
edit to `codex/**` or `CLAUDE.md`. The Calibration section explicitly names "how to split a plan" as exactly this
class of preference call. Neither split below touches codex or CLAUDE.md.

Both target docs were independently confirmed, this run, to still be over the 1000-line hard cap
(`scripts/plan-hygiene/check_line_caps.sh` / `check_line_caps.sh` HARD gate):

- `plans/active/github_actions_operator_gated_followups_2026_07_17.md` — 1006-1007L (grew back over cap since its
  2026-08-03 split).
- `plans/active/issues/pytest_timeout_60s_flaky_under_contention_continued2_2026_08_03.md` — 1013L, first flagged
  2026-08-10 (`plan_reconciler_findings_ci_2026_08_10.md`), reconfirmed unresolved 2026-08-15, and again unchanged at
  the start of this run.

## Decision — `[WORKER REC]` applied

**Ruling**: extract each doc's closed historical narrative (Progress-Log-shaped content with zero open todos
depending on it) verbatim into a dated `<slug>_..._history_2026_08_16.md` sibling under `plans/archive/2026_08/`,
leaving a one-paragraph pointer in its place. This is the SAME mechanical pattern already proven on
`github_actions_operator_gated_followups_2026_07_17.md` itself on 2026-08-03 (that split brought it from over-cap down
to a healthy margin; unrelated new content regrew it past 1000L over the following two weeks — a normal, expected
lifecycle for an actively-worked operator-decision ledger, not a sign the pattern failed).

**Why this qualifies for Trust Mode** (evidence bar, not vibes — per the Calibration section's own test, "can the
evidence make exactly one answer provably right?"):

1. **A proven precedent exists for the EXACT same doc** (not just the same doc class) — the 2026-08-03 split of this
   same `github_actions_operator_gated_followups` doc is itself the reference implementation.
2. **Zero prior operator disagreement** — every batched ruling this skill has asked for has been answered with the
   marked `[WORKER REC]` (9/9 on 2026-07-15, 7/7 on 2026-08-15, per the Calibration section's own citation); this
   specific recommendation (split these exact 2-3 over-cap ci-tranche docs) was independently surfaced as the
   "Recommended NEXT item" by the 2026-08-10 predecessor run and never contradicted.
3. **Zero content lost** — a verbatim relocation, not a summarization or deletion; verified line-for-line via `sed`
   line-range extraction (not manual retyping) plus a post-hoc grep confirming the extracted headings are fully absent
   from the live doc and the live doc's remaining todos/status are untouched.
4. **No open todo depends on the extracted content** — confirmed per-doc before extracting (see per-doc detail below).

## Applied

### 1. `github_actions_operator_gated_followups_2026_07_17.md` (1006-1007L → 736L)

Extracted: `### Hard-won context the next session should inherit rather than rediscover` (2026-07-17/22 post-migration
system-check narrative + operational lessons) + `## Cost ruling 2026-07-23` (semver-agent revert decision) — lines
286-563 of the pre-split doc. Both are closed historical record bookended by two LIVE decision-ledger sections
("Deferred work after 2026-07-17" before, "Deferred work after 2026-07-23" after) that were left untouched along with
every open todo (D1/D3 rows, Phase 7's org-migration REVIEW item, etc.).

- New doc:
  `/plans/archive/2026_08/github_actions_operator_gated_followups_hard_won_context_and_cost_ruling_history_2026_08_16.md`
  (336L).
- Live doc: frontmatter `related:`/`last_updated` updated to point at the new history doc + this ruling record.

### 2. `pytest_timeout_60s_flaky_under_contention_continued2_2026_08_03.md` (1013L → 143L)

Extracted: the bulk `## Progress Log` — ~20 individual `cicd`-escalation investigation entries from 2026-08-03 across
7+ repos, every one concluding "no code or workflow change made or needed" (pure fleet-wide single-self-hosted-runner
queue-depth contention, the exact bug class this doc-chain tracks). Lines 121-1001 of the pre-split doc.

**Kept in the live doc** (deliberately NOT extracted, despite being inside the same Progress Log section): the
2026-08-09 status-update entry and the "## na-eligibility-audit verdict" section — both directly inform the live
doc's own still-open todos 1 and 3 (both gated on the ledger-coordination fix "landing AND holding (sustained)"), so
moving them to a rarely-read history doc would have made the live doc's own gating condition harder to evaluate at a
glance. This is a deliberate deviation from the "extract everything, keep only a pointer" pattern used for doc 1 —
justified by the same evidence-based principle (don't move content a live decision depends on), not a different rule.

- New doc:
  `/plans/archive/2026_08/pytest_timeout_60s_flaky_under_contention_continued2_progress_log_history_2026_08_16.md`
  (961L).
- Live doc: frontmatter `related:`/`last_updated` updated to point at the new history doc + this ruling record.

## What this does NOT change

Neither split touches: any open todo's text, evidence, or checkbox state; either doc's `assigned_vm`/`priority`/
`parent_epic`; the operator-decision ledgers (D1-D4 tables, "Deferred work after..." tables) in doc 1; or the
gating logic for doc 2's todos 1/3. This is a pure line-cap remediation — content moved, nothing decided differently.

## Reversibility

A `git revert` of the commit(s) this ruling record ships with fully restores both docs to their pre-split content —
the extraction is a mechanical `sed` line-range move (verified byte-identical via boundary-grep sanity checks before
applying), not a hand-edited rewrite.

## Progress Log

- **2026-08-16 (plan_reconciler ci-tranche, agt-4f7ad9)**: both splits applied, verified clean (0 residual matches for
  extracted headings in either live doc; kept sections spot-checked intact), frontmatter updated on all 4 touched
  docs (2 live + 2 new archive docs), this ruling record created. Checkpoint commit follows in the same turn.
