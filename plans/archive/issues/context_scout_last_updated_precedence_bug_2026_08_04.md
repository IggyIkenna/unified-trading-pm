---
doc_type: issue
title:
  "`generate_context_scope_inventory.py`'s `_last_touched()` trusted a manually-maintained `last_updated` frontmatter
  field outright over the real git commit date -- a genuinely different, unshipped bug from the
  reference-only-commit-walkback fix that closed the archived parent issue"
summary:
  "Follow-up to `/plans/archive/issues/context_scout_source_hunting_gap_2026_08_03.md` (archived 2026-08-03, commit
  59e83e2b7): that issue's todo 4 asked whether `_last_touched()`'s STALE/ UP_TO_DATE fallback could produce a false
  UP_TO_DATE. Two concurrent sessions investigated it and both confirmed real bugs, but they are DIFFERENT bugs and only
  one shipped. The shipped fix (`_commit_touches_only_ref_fields`, adversarially verified 0/1007 mismatches) addresses
  the git-fallback path used only when `last_updated` is ABSENT. It does not touch the separate, higher-impact bug this
  doc is about: when `last_updated` IS present, `_last_touched()` returned it immediately and never even looked at the
  git date. Nothing in this workspace auto-bumps `last_updated` on edit, so it silently goes stale -- measured
  2026-08-03: 390/435 corpus docs carrying the field were behind their real last commit, and for 200 of those the stale
  value alone produced a false UP_TO_DATE, hiding real post-scout edits from the incremental sweep (concrete example:
  `vol_dvol_backtestable_engines_2026_07_13.md` got genuine todo-flip commits after its scout marker, but its unbumped
  `last_updated: 2026-07-28` still read UP_TO_DATE). The parent issue archived with this specific finding never landed
  on `origin` -- confirmed by diffing `scripts/plan-hygiene/generate_context_scope_inventory.py`'s current
  `_last_touched()` against origin before filing this doc: it still returns `last_updated` outright, no `max()` with any
  git signal anywhere in the function."
status: resolved
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [context-scope, context-scout, plan-hygiene, tooling, staleness-heuristic, last_updated]
related:
  [/plans/archive/issues/context_scout_source_hunting_gap_2026_08_03.md, cursor-configs/skills/context-scout/SKILL.md]
created: 2026-08-04
parent_epic: agent_operating_framework_master
source:
  "Surfaced while shipping the parent issue's todo 4 fix under /autonomous: hit repeated concurrent- edit conflicts with
  two other AO-dispatched sessions working the same parent doc overnight, which archived it with todo 4 marked done.
  Diffing the actually-shipped code against my own local fix showed only the OTHER session's (also-real, also-confirmed)
  reference-only-commit-walkback bug landed -- this session's last_updated-precedence finding never made it to origin.
  Filed fresh rather than reopening the archived parent, per this workspace's archival discipline."
locked_by:
resolved_by:
execution_scope: local-only
assigned_role: docs_reconciler
model_tier: sonnet-doable
drift_direction: advance-code
assigned_vm: NA
depends_on: []
context_scope:
  [
    /plans/archive/issues/context_scout_source_hunting_gap_2026_08_03.md,
    cursor-configs/skills/context-scout/SKILL.md,
    scripts/plan-hygiene/generate_context_scope_inventory.py,
  ]
priority: P2
---

## What I found

`_last_touched()`'s current (pre-fix) shape:

```python
def _last_touched(fm: dict, path: Path, marker: str | None) -> str | None:
    last_updated = fm.get("last_updated")
    if isinstance(last_updated, (dt.date, dt.datetime)):
        return last_updated.isoformat()[:10]
    if isinstance(last_updated, str) and last_updated.strip():
        return last_updated.strip()[:10]
    # ... git fallback only reached when last_updated is absent ...
```

The `return` on a present `last_updated` is unconditional -- the git commit date (cheap OR the now-fixed accurate
walk-back) is never consulted when the field exists, no matter how stale it is. This is a distinct failure mode from
what the parent issue's shipped fix addresses: that fix improved the ACCURACY of the git-fallback path itself (only
reached when `last_updated` is missing); it does nothing when `last_updated` is present but wrong.

## Why it matters

Confirmed corpus-wide on 2026-08-03: of 435 docs carrying `last_updated`, 390 (90%) had it behind their real last git
commit -- unsurprising, since nothing in this workspace's tooling bumps the field on edit (it's manually set at
doc-creation time and then typically forgotten). For 200 of those, the stale value alone was enough to produce a false
UP_TO_DATE verdict against the doc's most recent `context-scout` marker, meaning the daily/hourly incremental sweep
silently skips re-scouting a doc that has genuinely new content since it was last scouted. Re-measured just now against
the current (post-overnight-re-scout) corpus: 3 more docs flip from UP_TO_DATE to STALE with this fix applied (640→637
UP_TO_DATE / 5→8 STALE) -- a smaller absolute number than the original 199-doc measurement only because most of the
corpus has since been freshly re-scouted, not because the underlying bug shrank; any doc that gets a `last_updated`
value going forward and then sees a real edit without that field being bumped is exposed to this exact bug again.

## Fix

`max(last_updated, git_signal)` instead of returning `last_updated` outright -- a legitimately-set `last_updated` (e.g.
an edit not yet committed) still counts, but can never mask a later git-tracked edit the field was never updated to
reflect. Composes cleanly with the already-shipped reference-only-commit-walkback fix: the git signal itself still
prefers the cheap single-commit date, only paying for the accurate walk-back when the cheap date wouldn't already
satisfy UP_TO_DATE against the marker.

## Todos

- [x] ✅ [SCRIPT] P2. Fix `_last_touched()` in `scripts/plan-hygiene/generate_context_scope_inventory.py` to take
      `max(last_updated, git_signal)` instead of returning `last_updated` outright. Add regression tests covering both
      precedence directions + the short-circuit interaction with the existing accurate-walk-back logic. Verify against
      the live corpus (before/after STALE/UP_TO_DATE counts) and cite the numbers here. — unified-trading-pm (this
      commit). 7 new/updated tests in `tests/unit/test_generate_context_scope_inventory.py` (12 total, all passing),
      ruff + basedpyright clean. Corpus impact measured against current HEAD (post-overnight-re-scout, so most of the
      false-UP_TO_DATE backlog this bug originally caused is already gone via fresh scouting, not this fix): 640→637
      UP_TO_DATE, 5→8 STALE (3 docs correctly reclassified). Module docstring updated to describe the
      MAX-of-both-signals behavior.

## Progress Log

- **2026-08-04**: filed + resolved in the same session. Only todo shipped and verified; archiving immediately per this
  workspace's completion discipline (a plan with every todo done + unlocked must be archived, not left sitting active).
