---
doc_type: issue
title:
  "instruments_mtds_consistency_remediation_residuals_2026_07_24.md still cites the pre-archival path of
  corrector_scripts_dedup_tiebreak_timestamp_bug_2026_08_09.md — needs a prettier-clean pass before the link-repoint can
  land"
summary:
  "corrector_scripts_dedup_tiebreak_timestamp_bug_2026_08_09.md (all 4 todos done) was archived 2026-08-12 to
  /plans/archive/2026_08/issues/corrector_scripts_dedup_tiebreak_timestamp_bug_2026_08_09.md via its companion finalize
  plan. instruments_mtds_consistency_remediation_residuals_2026_07_24.md:809 still cites the old plans/active/issues/...
  path in a Progress Log prose citation. A direct edit was attempted and reverted: the doc is already AT the
  check_line_caps.sh hard cap (1000L), and prettier's mandatory --write auto-stage pass reflowed a large surrounding
  paragraph (26-space -> 30-space continuation indent) as a side effect of touching one nearby line, pushing the file to
  1001L and tripping check_line_caps.sh (a doc newly crossing the cap is NOT covered by the line-cap ritual's
  zero-open-todo or bounded-link-repoint carve-outs -- see
  /codex/12-agent-workflow/plan-completion-and-archival-discipline.md § 'The line-cap does NOT block a bounded same-line
  link-repoint' caution note). Per that doc's own guidance: 'the actual fix is to land a standalone formatting commit on
  the file first, bringing it to prettier-clean, before adding the marker.'"
status: open
nature: issue
asset_group: [cefi, defi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, referrer-fixup, line-cap, prosewrap-padding, archival]
related:
  [
    /plans/active/instruments_mtds_consistency_remediation_residuals_2026_07_24.md,
    /plans/archive/2026_08/issues/corrector_scripts_dedup_tiebreak_timestamp_bug_2026_08_09.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: 2026-08-12
last_updated: 2026-08-12
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.04
assigned_role: data_engineering
drift_direction: none
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: slot 11, 2026-08-12, corrector_scripts_dedup_tiebreak_timestamp_bug_2026_08_09_finalize archival session
context_scope:
  [
    /plans/active/instruments_mtds_consistency_remediation_residuals_2026_07_24.md,
    /plans/archive/2026_08/issues/corrector_scripts_dedup_tiebreak_timestamp_bug_2026_08_09.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    unified-trading-pm/scripts/plan-hygiene/check_line_caps.sh,
  ]
---

# Stale referrer to an archived doc's pre-archival path — blocked on the doc's own prettier/line-cap state

## What I found

`instruments_mtds_consistency_remediation_residuals_2026_07_24.md:809` (a Progress Log prose citation inside a completed
todo) still reads:

```
plans/active/issues/corrector_scripts_dedup_tiebreak_timestamp_bug_2026_08_09.md
```

That doc archived 2026-08-12 to
`/plans/archive/2026_08/issues/corrector_scripts_dedup_tiebreak_timestamp_bug_2026_08_09.md` (all 4 todos done,
`resolved_by:` cites the 4 landing commits). The citing doc itself sits exactly at `check_line_caps.sh`'s 1000-line hard
cap — any staged touch triggers `prettier-autostage`'s unconditional `--write` pass, which reflows the surrounding
paragraph's continuation-line indent (measured: 26-space → 30-space across ~40 lines in this case) as a side effect,
adding 1 net line and pushing the file to 1001L. That trips the hard cap even though the actual content change was a
single-line path swap — the bounded-link-repoint carve-out in `plan-completion-and-archival-discipline.md` does not
cover a file newly crossing the cap in the same commit.

## Why it matters

A future reader following that citation lands on a dead path. Low severity (the doc is small, single citation, easy to
find via grep) but real — leave it broken and it's one more stale pointer someone else pays to re-discover.

## Recommended decision

Two-step landing, per the codex doc's own prescribed fix:

1. Land a standalone prettier-formatting commit on `instruments_mtds_consistency_remediation_residuals_2026_07_24.md`
   first (no content change — just bring the file to prettier-clean so its continuation-line indent stops drifting on
   every future touch). Verify `check_line_caps.sh` afterward to confirm the reformat alone doesn't cross the cap (it
   may shrink OR grow the line count — check both directions).
2. Once prettier-clean, make the single-line path-repoint at line ~809 (`plans/active/issues/...` →
   `/plans/archive/2026_08/issues/corrector_scripts_dedup_tiebreak_timestamp_bug_2026_08_09.md`, plus a short "(RESOLVED
   2026-08-12)" note if it still fits the bounded-repoint carve-out's line-count rules) as its own commit.

## Todo

- [ ] [DOC] P3. Land a standalone prettier-formatting commit on
      `plans/active/instruments_mtds_consistency_remediation_residuals_2026_07_24.md` (no content change), verify
      `check_line_caps.sh` still passes post-reformat, then repoint line ~809's citation from
      `plans/active/issues/corrector_scripts_dedup_tiebreak_timestamp_bug_2026_08_09.md` to
      `/plans/archive/2026_08/issues/corrector_scripts_dedup_tiebreak_timestamp_bug_2026_08_09.md` in a separate
      follow-up commit. Repo: unified-trading-pm. Done-when: the citation resolves to the archived doc and
      `check_reference_paths.py` shows zero new broken referrers.

## Progress Log

- **2026-08-12 (slot 11)**: filed during the `corrector_scripts_dedup_tiebreak_timestamp_bug_2026_08_09_finalize`
  archival session — the direct fix was attempted, hit the prettier-reflow/line-cap interaction described above, and was
  reverted rather than forced through. Rest of the archival (source doc + finalize plan both archived, codex rule
  migrated, `infrastructure_master.md`'s own link fixed) landed clean; this is the one referrer left outstanding.

- **context-scout 2026-08-14**: populated context_scope (4 entries).
