---
doc_type: issue
title:
  Two archive-candidate docs are genuine "prose-only remaining work" traps (100% checkboxes checked, real open work
  described only in prose/tables) AND already exceed the 1000-line hard cap, so neither can be safely edited to fix
  either problem without a split first
summary: >-
  While resolving cicd escalation agt-c3b939 (plan_health archive-candidates gate), 14 checkbox-complete docs were
  deep-read individually (not trusted by checkbox count — this corpus has confirmed prose-only-remaining-work traps). 12
  were genuine traps; 10 were safely fixed (a real `- [ ]` todo added, all under the 1000-line hard cap). The other 2
  are ALSO traps (real remaining work exists only in a "Deferred work" table row / prose, invisible to
  `check_archive_candidates.sh`'s checkbox count) but are already over the `check_line_caps.sh` 1000-line hard cap
  (1011L / 1509L) — the prek `--precommit` rule is absolute for a file a commit touches ("a file THIS commit touches
  must not be over its tier's cap, full stop", no ratchet exemption), so adding the missing todo would itself become
  uncommittable. Left untouched this pass; the archive-candidates gate stays green regardless (2 candidates vs baseline
  11), but the underlying prose-trap defect in both docs is real and not yet fixed.
status: open
nature: issue
asset_group: [tradfi, defi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, line-caps, archive-candidates, prose-trap, split-needed]
related:
  [
    /plans/active/issues/tradfi_mdps_build_continuous_mismatches_2_and_4_still_open_2026_07_26.md,
    /plans/active/issues/mtds_backfill_vm_startup_oom_rc137_2026_07_14.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: 2026-07-29
parent_epic: plan_hygiene_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
source: [cicd escalation agt-c3b939 (plan_health gate), archive-candidates deep-read, 2026-07-29]
drift_direction: worsening-slowly
depends_on: []
locked_by:
resolved_by:
---

# Two archive-candidate docs need a split before their prose-trap can be fixed

## What I found

Resolving the `check_archive_candidates.sh` hard gate (14 candidates vs baseline 11), I deep-read all 14 flagged docs
instead of trusting the 0-open-checkbox heuristic. 12 turned out to be genuine traps — checkbox-complete but with real
remaining work described only in prose, a "Deferred work" table row, or a banner. 10 of those were fixed cleanly (a real
`- [ ]` todo added, converting the invisible prose gap into tracked work). These 2 could not be:

1. **`tradfi_mdps_build_continuous_mismatches_2_and_4_still_open_2026_07_26.md`** (1011 lines, over the 1000L hard cap).
   Every checkbox is `[x]`, but the "## Deferred work after 2026-07-26" table's last row reads: _"New P2 todo — re-run
   the ES/MES backfill a THIRD time now that the empty-day-listing retry mitigation is live | Not done (slot 4,
   2026-07-26)... | Nobody — launch one more `launch-mdps-backfill-vm.sh` pass + re-measure the `1d` hit rate"_ — real,
   named, unowned remaining work with no corresponding open checkbox anywhere in the doc.
2. **`mtds_backfill_vm_startup_oom_rc137_2026_07_14.md`** (1509 lines, over the 1000L hard cap). Every checkbox is
   `[x]`, but the doc's own closing sections leave two threads explicitly open: the
   `uts-prod-manifest-consolidator-market-data-defi` DuckDB consolidator crash / cron scheduler stays **PAUSED**
   ("resuming it... remains operator+backend-owned and will be decided on its own evidence, not unblocked by this
   verdict alone"), and the Morpho `lending_indices` backfill live-verify section ends "Not yet a full close for this
   handler — the backfill was still running at the time this entry was written."

Both are ALSO over `check_line_caps.sh`'s 1000-line hard cap. That check has NO ratchet exemption for a file the current
commit touches ("a file THIS commit touches must not be over its tier's cap, full stop" —
`scripts/plan-hygiene/check_line_caps.sh`'s own doc comment) — so adding even one line (the missing todo) to either doc
would make it uncommittable via the normal path. Fixing the prose-trap here requires a real split (same pattern the
operator already ratified for `sports_consolidated_closeout_2026_07_19.md` in
`autonomous_session_operator_decisions_2026_07_25.md` entry #9: a trimmed coordination-index parent + N child plans
under cap, wired via `depends_on`/`gate_on_depends`), not a mechanical one-line add — genuinely open-ended judgment
about what goes where, not something to guess at here.

## Why it matters

The `check_archive_candidates.sh` gate stays green regardless (2 candidates vs baseline 11, well under) — this is NOT
currently blocking anything. But both docs' real remaining work stays invisible to every mechanical hygiene check
(checkbox count AND the archive-candidates heuristic) until split, which means it will keep silently NOT happening
unless someone reads the full doc by hand again.

## Recommended next step (not done here — needs real design judgment, not a mechanical fix)

For each doc: split into a trimmed index/summary doc (kept under the 1000L cap, the historical investigation + Progress
Log content) + extract the ONE real open item into a small, clean, dispatchable child doc/todo. Suggested child-doc
content:

- tradfi_mdps doc → extract: "launch one more `launch-mdps-backfill-vm.sh` ES/MES pass, re-measure the `1d` hit rate
  against the 454/2398 baseline, and pursue the `_list_instrument_files` listing-consistency lead if the hit rate is
  still flat" as a standalone `- [ ]` todo in a new, small, under-cap doc.
- mtds_backfill doc → extract: "confirm the DuckDB consolidator crash root cause is fully resolved, decide whether
  `uts-prod-manifest-consolidator-market-data-defi-cron` can be un-paused, and confirm the Morpho `lending_indices`
  backfill's live-verify actually completed with no rc=137 recurrence" as a standalone `- [ ]` todo.

## Todos

- [ ] [DOC] P2. Split `tradfi_mdps_build_continuous_mismatches_2_and_4_still_open_2026_07_26.md` (1011L, over cap) into
      an under-cap index/history doc + a small child doc carrying the one real open item (the P2 "re-run backfill a
      third time" action from the Deferred-work table), per the recommended-next-step above.
- [ ] [DOC] P2. Split `mtds_backfill_vm_startup_oom_rc137_2026_07_14.md` (1509L, over cap) into an under-cap
      index/history doc + a small child doc carrying the two real open items (consolidator cron un-pause decision,
      Morpho `lending_indices` live-verify completion confirmation), per the recommended-next-step above.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid - doc's own text declares the index/history split an open-ended
  judgment call about what goes where
