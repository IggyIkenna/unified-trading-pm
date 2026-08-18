---
doc_type: issue
title: plans/active/INDEX.md auto-generated block duplicated 5-6x — regenerator has no concurrency guard
summary: >-
  Found 2026-08-16 in this shared slot's working tree: plans/active/INDEX.md's `<!-- AUTO-INDEX-START -->` block
  (written by scripts/plans/regenerate_active_plan_index.py) contains SIX stacked copies of its own header line
  (`_Auto-generated ... 350 plans_` / `352` / `303` / `314` / `284` / `285` / `290`) and correspondingly duplicated
  `### <domain> (N)` sections and plan-entry bullets beneath each. The file was still uncommitted at discovery time
  (working tree only), not on origin/live-defi-rollout, but the pattern — six DIFFERENT plan-count snapshots stacked
  in one file — means at least six regenerator runs landed on top of each other without the file ever being cleared
  first, most plausibly several concurrent sessions/agents on this shared multi-slot checkout each running the
  regenerator (or the full quality-gates.sh sweep, which invokes it) against the same working tree without any lock
  or atomic-replace on the output file.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, regenerator, concurrency, corruption, multi-agent, index]
related:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    /codex/12-agent-workflow/measurement-claims-discipline.md,
    /plans/active/manifest_consolidator_and_lifecycle_cost_optimization_2026_08_16.md,
  ]
created: 2026-08-16
author: claude-code (interactive session, discovered while diagnosing an unrelated plan-hygiene precommit failure)
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: infra
priority: P2
effort: low
source:
  [
    "Interactive session, 2026-08-16: discovered while diagnosing why plans/active/compute_flexible_cud_sizing_analysis_2026_08_16.md
    failed plan-hygiene precommit — grep on plans/active/INDEX.md's own diff surfaced the duplication as an unrelated
    finding, not the actual cause of that failure (which was a missing effort: field, unrelated).",
  ]
resolved_by:
locked_by:
locked_since:
context_scope:
  [scripts/plans/regenerate_active_plan_index.py, /codex/05-infrastructure/per-tab-worktrees.md]
drift_direction: advance-code
depends_on: []
---

# plans/active/INDEX.md auto-generated block duplicated 5-6x

## What was found

`git diff -- plans/active/INDEX.md` in this session's working tree (`.tabs/4/unified-trading-pm`, a shared slot — the
SessionStart hook flagged 2 other live `claude` processes with a cwd inside this exact slot at session start) showed
the `<!-- AUTO-INDEX-START -->` block containing, back to back, with no other content between them:

```
_Auto-generated via `scripts/plans/regenerate_active_plan_index.py`. 350 plans across 10 domains. ...
_Auto-generated via `scripts/plans/regenerate_active_plan_index.py`. 352 plans across 10 domains. ...
_Auto-generated via `scripts/plans/regenerate_active_plan_index.py`. 303 plans across 10 domains. ...
_Auto-generated via `scripts/plans/regenerate_active_plan_index.py`. 314 plans across 10 domains. ...
_Auto-generated via `scripts/plans/regenerate_active_plan_index.py`. 284 plans across 10 domains. ...
_Auto-generated via `scripts/plans/regenerate_active_plan_index.py`. 285 plans across 10 domains. ...
```

(a 7th, `290 plans`, appears further down attached to a `### cefi (N)` duplicate cluster). Each header is followed by
its own set of `### <domain> (N)` section headers and plan-entry bullet lists — i.e. this is not one clean regen with a
stray extra header line, it is (at least) 5-6 FULL regenerator outputs concatenated, each reflecting the corpus size at
a different point in time (350 → 352 → 303 → 314 → 284 → 285 → 290 — non-monotonic, consistent with different
concurrent sessions each adding/archiving plans between their own runs).

**This was NOT the cause of the plan-hygiene failure being diagnosed at the time** (that was an unrelated missing
`effort:` frontmatter field on a different, new plan doc, tracked/fixed in
`manifest_consolidator_and_lifecycle_cost_optimization_2026_08_16.md`). This file was left untouched — not staged, not
committed, not hand-edited — per the multi-agent safety rule against editing files you don't own mid-collision; it is
filed here as a standalone finding for whoever owns `scripts/plans/regenerate_active_plan_index.py` next.

## Why this matters

`INDEX.md` is meant to be a reliable, grep-first navigation aid ("Grep this block for a domain keyword before scanning
`plans/active/` by hand" — its own header text). A corrupted copy with 5-6x duplicated entries makes grep results
noisy (the same plan's one-line summary appears multiple times, with different summaries if the plan's own `summary:`
changed between regen runs) and the file's own plan COUNT is meaningless (which of 350/352/303/314/284/285/290 is
"current"?). Left as-is, whichever session's `safe-doc-push.sh`/quickmerge run happens to commit this file next ships
the corruption to `origin/live-defi-rollout` for every other slot to inherit.

## Root cause (inferred, not yet confirmed against the generator's source)

`regenerate_active_plan_index.py` most likely writes its output by APPENDING or by a non-atomic read-modify-write
against `plans/active/INDEX.md`'s content between its `<!-- AUTO-INDEX-START -->`/`<!-- AUTO-INDEX-END -->` markers,
rather than truncating and rewriting the block atomically. On a shared multi-slot checkout where several sessions can
independently run `bash scripts/quality-gates.sh` (which invokes the regenerator as part of its sweep) against the SAME
working tree with no lock, two runs racing produces exactly this shape: each run reads the file (possibly already
containing a prior run's output), doesn't fully clear the old block, and writes its own fresh block alongside/after it.

## What needs to happen

- [ ] [SCRIPT] P2. **Read `scripts/plans/regenerate_active_plan_index.py` and confirm whether its write is a full
      truncate-and-replace of the `<!-- AUTO-INDEX-START -->...<!-- AUTO-INDEX-END -->` span, or an append/partial
      update.** If it's not an atomic full-block replace, fix it to be one (write to a temp file, then rename over the
      target, so a concurrent reader/writer never observes a partial or doubled state). Done-when: the regenerator's
      own logic provably always fully replaces the marker span regardless of the block's prior content.
- [ ] [SCRIPT] P3. **Add a concurrency guard** (a lock file, or accept that `quality-gates.sh` on a shared slot host
      should serialize this specific step) so two simultaneous regenerator runs against the same working tree can't
      race even with the atomic-write fix above — the atomic write alone prevents a mid-write torn state but not a
      "run B's stale-corpus output silently clobbers run A's fresher one" last-write-wins loss. Done-when: either a
      documented lock mechanism exists, or a reasoned decision that last-write-wins is acceptable for this
      specific auto-generated, easily-regenerable file (re-running the regenerator fixes it, unlike real data loss).
- [ ] [SCRIPT] P2. **Clean up the currently-corrupted working-tree copy of `plans/active/INDEX.md` in
      `.tabs/4` and re-run the regenerator once cleanly** (only after the fix above, or the same corruption can
      reproduce). Coordinate with whichever live session currently owns uncommitted work in that slot before touching
      it — do not force through a collision. Done-when: `plans/active/INDEX.md` contains exactly one
      `<!-- AUTO-INDEX-START -->` block with one plan count, committed and pushed.

## Progress Log

- **2026-08-16 (interactive session)**: Filed from a working-tree observation during an unrelated plan-hygiene
  diagnosis. Root cause is inferred from the symptom shape, not yet confirmed by reading the generator's source —
  whoever picks this up should verify the truncate-vs-append hypothesis before assuming the fix.
- **na-eligibility-audit 2026-08-17** (infra tranche) [body-hash:a2e2e57f9a3e4ff3]: RECLASSIFY_WHOLE —
  `assigned_vm: NA` → `planning`. All 3 todos are bounded, deterministic engineering work with stated done-when
  criteria; no gate, banner, lock, or redirect found. Fresh 2026-08-16 filing with no prior audit history.
- **context-scout 2026-08-17**: refreshed context_scope (2 entries).
