---
doc_type: issue
title:
  "check_archive_candidates --only pre-commit hook conflicts with the never-combine-flip-and-archival-mv SSOT (both
  shipped 2026-08-09)"
summary:
  "The new check_archive_candidates --only precommit gate (landed 2026-08-09) hard-blocks a checkbox-flip-only commit
  that leaves its doc 0-open/done/unlocked, but plan-completion-and-archival-discipline.md's 'never combine the checkbox
  flip with the git mv archival in ONE commit' rule (also migrated 2026-08-09) forbids shipping the flip and the
  archival move together. Any self-archiving single-todo plan (the <X>_finalize_<date>.md pattern is the common shape)
  hits both rules simultaneously with no compliant single-commit path."
status: open
resolved_by:
nature: issue
asset_group: [ci, meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, archival, pre-commit, ssot-conflict, check_archive_candidates]
related:
  [
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch9_finalize_2026_08_09.md,
    /agents/RULES.md,
  ]
context_scope:
  [
    scripts/plan-hygiene/check_archive_candidates.sh,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: 2026-08-09
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
source:
  "Discovered live while executing ci_satellite_ao_dispatch_batch9_finalize_2026_08_09.md's sole [REVIEW] todo (slot 16,
  2026-08-09)."
archive_exempt: true
locked_by:
drift_direction: none
depends_on: []
---

# check_archive_candidates hook vs. never-combine-flip-and-mv SSOT — same-day conflict

## What I found

Two governance mechanisms both landed on **2026-08-09** and directly contradict each other for any plan whose own
last-remaining todo's completion ALSO makes the doc archival-eligible (0 open todos, some done, unlocked, not
`archive_exempt`):

1. **`scripts/plan-hygiene/check_archive_candidates.sh --only`** (wired into `safe-doc-push.sh`'s prek chain 2026-08-09,
   per that script's own header comment — "Root-caused 2026-08-09 after the corpus-wide count reached 9 ... entirely via
   commits that never ran this check"). It hard-fails (`exit 1`, blocking the commit) any staged `plans/active/*.md`
   file that is 0-open/some-done/unlocked/not-exempt, with the remedy: "archive it: flip status to a terminal value, add
   the archive banner, git mv to plans/archive/..., fix corpus referrers" — **in other words, do the archival in the
   SAME commit as the flip that closes the last todo, or the commit is rejected outright.**

2. **`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` § "Never combine the checkbox flip with the
   `git mv` archival in ONE commit"** — migrated into this codex doc as the self-declared SSOT on the SAME DAY
   (2026-08-09; the rule itself dates to a 2026-07-30 incident, previously living only in `agents/RULES.md`). It states
   plainly: "Fix: commit the flip FIRST as a plain edit at the still-active path, THEN `git mv` to the archive location
   as a separate follow-up commit" — because a combined commit's diff at the ORIGINAL path shows only a deletion, which
   can make `/done`'s M3 verification (`cross_repo_pm_flip_verified`) reject with
   `cross_repo_pm_file_touched_no_checkbox_flip`.

**Live case that hit this**: `ci_satellite_ao_dispatch_batch9_finalize_2026_08_09.md` is a single-todo `<X>_finalize`
plan (the standard finalize-plan-coverage pattern per `task_template.md` §4). Flipping its one `[REVIEW]` todo to `[x]`
makes it 0-open/done/unlocked in the same diff — `check_archive_candidates --only` rejected the flip-only commit,
demanding same-commit archival; the codex SSOT forbids exactly that combination.

**Worked around this instance via a documented one-commit `archive_exempt: true` bridge**: the flip commit carries a
temporary `archive_exempt: true` (with a Progress Log entry naming this exact conflict) to satisfy the hook without
combining flip+mv, and the immediately-following commit performs the real 6-step archival ritual and drops the now-moot
exemption key. This is a workaround for one doc, not a fix for the underlying rule conflict — it also required noticing
the escape hatch exists and reasoning about why it legitimately applies here, which a less context-rich worker session
could easily miss (defaulting instead to either violating the SSOT by combining, or getting stuck unable to ship at
all).

**Possibly-relevant mitigating detail found while investigating** (not verified as a full fix — flagging for whoever
picks this up): `agent-orchestrator/server/verify.py`'s `_mode1_disposition`/`_resolve_current_plan_text` docstrings
explicitly describe detecting "a bundled `git mv` + checkbox-flip commit ... even when it lands inside the worker's own
worktree," including a fallback (`checkbox_currently_checked_sha_mismatch`) that reads the CURRENT plan text at its
resolved archive location when the diff-based check at the old path comes up empty. This suggests the server-side gap
the 2026-07-30 incident described may have since been patched for at least the single-repo (mode 1) case — if confirmed,
the codex "never combine" rule may be safely relaxable (at least for mode 1), which would also retire this whole
conflict. This needs a deliberate verification pass (a scratch `/done` walked through both code paths), not a guess —
did not attempt it here to keep this task's blast radius to its own scope.

## Why it matters

Every `<X>_finalize_<date>.md` single-todo self-archiving plan (a common, deliberately-encouraged pattern per
`task_template.md` §4's finalize-plan-coverage rule — this fleet has produced at least 10 batch-N/finalize pairs in the
`ci` tranche alone) will hit this identical conflict the moment its last todo closes. Left unresolved, every future
occurrence either (a) burns a worker session rediscovering the same investigation this issue already did, or (b) gets
silently resolved by whichever of the two rules the worker happens to prioritize, with no consistency across sessions.

## Recommended decision

One of:

- **(a)** Verify whether `agent-orchestrator`'s current M3 fallback logic (see "possibly-relevant" note above) actually
  closes the 2026-07-30 gap for mode-1 (single-repo) cases, and if so, narrow the codex "never combine" rule to mode-2
  (cross-repo PM flip) only — which would make same-commit flip+archival safe (and hook-compliant) for the common
  single-repo finalize-plan case.
- **(b)** If the M3 gap is still real for mode 1 too, add an explicit, narrow carve-out to
  `check_archive_candidates.sh --only` for the specific shape "this commit's diff on this file is itself the checkbox
  flip that produces the 0-open state" (i.e., don't flag a file in the SAME commit that just closed its own last todo —
  let a FOLLOW-UP commit's hook run catch it if the archival never happens), removing the need for the `archive_exempt`
  bridge entirely.
- **(c)** At minimum, document the `archive_exempt: true` one-commit-bridge pattern used here as the sanctioned
  workaround in `plan-completion-and-archival-discipline.md` itself, so the next worker who hits this doesn't have to
  re-derive it.

## Todos

- [x] ✅ [DOC] P2. **Verified 2026-08-10 (slot 17): the M3 gap IS closed for mode 1.** A direct `verify.check_plan_flip`
      trial (scratch-repo simulation: same-commit flip+`git mv` confirmed `_archival_rename_disposition` returns True;
      the existing regression test `test_done_accepts_cross_repo_self_archived_with_annotated_checked_line` exercises
      the same `plan_ref_self_archived_with_marker` path and PASSES). The codex SSOT was narrowed to mode-2 only via
      `unified-trading-pm@79171795f2` + citation-fix follow-up; the `archive_exempt: true` bridge was independently
      documented and shipped (todo 2 below). **Path (a) taken** — the `check_archive_candidates.sh --only` hook and the
      codex rule now align: single-repo same-commit flip+archival is the sanctioned, hook-compliant shape; cross-repo
      still uses the two-commit flip-then-mv split with the `archive_exempt: true` bridge. (repo: agent-orchestrator +
      unified-trading-pm)
- [x] [DOC] P2. ✅ **DONE — already shipped via a different, independently-filed duplicate issue, discovered and
      confirmed by plan_reconciler (ci tranche) 2026-08-10.** This exact conflict was independently rediscovered the
      same day (2026-08-09) by a different worker (via `sports_taxonomy_p1_capture_and_contracts_2026_08_08_finalize`)
      and filed/resolved as
      `/plans/archive/2026_08/issues/check_archive_candidates_only_mode_no_flip_then_mv_exemption_2026_08_09.md`
      (`status: resolved`, archived same day) — satisfies option (c)'s "at minimum" bar in full. Independently
      re-verified live: `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`'s "`archive_exempt: true`
      is the sanctioned bridge... (RULED 2026-08-09)" section is present;
      `scripts/plan-hygiene/check_archive_candidates.sh` has the `archive_exempt: true` skip logic (4 call sites);
      `tests/test_check_archive_candidates_flip_then_mv.bats` exists on disk. Shipped `unified-trading-pm@a231c2a80`.
      Options (a)/(b) (narrowing the codex rule, or a same-commit auto-detect carve-out) remain unimplemented —
      genuinely deferred to todo 1's outcome, not silently dropped.

## Progress Log

- **2026-08-09** — Filed while executing `ci_satellite_ao_dispatch_batch9_finalize_2026_08_09.md`'s sole todo (slot 16).
  Worked around for that one doc via a documented one-commit `archive_exempt: true` bridge; this issue tracks the
  underlying conflict for a durable fix.
- **2026-08-10 (plan_reconciler, ci tranche)** — flipped todo 2 (already independently shipped by a duplicate issue
  filed/resolved the same day this doc was created — see todo 2 for the citation trail). Doc stays `status: open`: todo
  1 (does the M3 fallback actually close the mode-1 combined-commit gap, which would let options (a)/(b) narrow or
  remove the `archive_exempt` bridge entirely) is a genuine, still-open investigation, not addressed by the duplicate's
  fix.
- **2026-08-10 (slot 17, batch12 worker)** — flipped todo 1 (path (a) confirmed). Direct trial (scratch-repo simulation)
  verified `_archival_rename_disposition` returns True on a same-commit flip+`git mv` →
  `plan_ref_self_archived_with_marker`. Existing test
  `test_done_accepts_cross_repo_self_archived_with_annotated_checked_line` PASSES. Codex SSOT
  (`plan-completion-and-archival-discipline.md`) narrowed to mode-2 only at `unified-trading-pm@79171795f2`
  - citation-fix follow-up (corrects a stale test-name reference). Both source-doc todos now `[x]`; doc can be archived
    once the wrapping batch plan (`ci_satellite_ao_dispatch_batch12_2026_08_10.md`) and its sibling finalize plan are
    also resolved. `archive_exempt: true` set to satisfy `check_archive_candidates.sh --only` — per the codex-sanctioned
    bridge pattern; will be dropped in the actual archival commit.
- **context-scout 2026-08-14**: populated context_scope (2 entries).
