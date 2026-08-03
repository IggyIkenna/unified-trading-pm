---
doc_type: issue
title:
  "market-tick-data-service QG STEP 5.95 (inline # type: ignore freeze-and-shrink ratchet) is RED on a clean LDR HEAD
  tree — frozen baseline (658) is stale"
summary: >-
  Working tradfi_combo_casing_direction_ssot_contradiction-003 (unrelated, 2 files touched), a full quality-gates.sh run
  failed at STEP 5.95 with the live repo-wide `# type: ignore` count at 659 against a frozen baseline of 658. Verified
  pre-existing: stashing my entire diff and re-running the same grep on a clean tree at origin/live-defi-rollout HEAD
  still returns 659. My own changed files contain zero `# type: ignore` occurrences. This blocks EVERY worker's
  `--apply`/quickmerge Pass-1 QG in this repo, not just mine.
status: resolved
nature: issue
asset_group: [meta]
stage: [meta]
repos: [market-tick-data-service]
scope: [engineer]
tags: [quality-gates, ratchet, ldr_qg_failure, repo-blocker, market-tick-data-service]
related: [/plans/active/issues/tradfi_combo_casing_direction_ssot_contradiction_2026_08_03.md]
created: 2026-08-03
priority: P1
parent_epic: mtds_mdps_master
assigned_vm: planning
source: [tradfi_combo_casing_direction_ssot_contradiction_2026_08_03.md]
resolved_by: market-tick-data-service@840c816d
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
assigned_role: backend_engineer
---

## What I found

Running `bash scripts/quality-gates.sh` (Pass 1, full run, no skip flags) in `market-tick-data-service` for unrelated
work (2 files touched, neither containing `# type: ignore`), STEP `[5.95/6]` failed:

```
❌ 5.95: inline '# type: ignore' comment count rose to 659 (frozen baseline: 658). A broad ignore (no rule
   code) is BANNED — use an exact-rule '# type: ignore[code]  # <dep> reason' instead, or fix the underlying
   type error:
```

The checker (`scripts/quality-gates.sh` STEP 5.95, `_MTDS_TYPE_IGNORE_BASELINE=658` set in commit `d072b035` "add
freeze-and-shrink ratchet for blanket pyright headers + inline type:ignore") does a repo-wide
`grep -rn "# type: ignore" --include="*.py" .` (excluding `.venv`/`__pycache__`) and fails if the count rose above the
frozen baseline. Verified pre-existing (not caused by my diff):

```
git stash push --include-untracked -m check -- <my 2 files>
grep -rn "# type: ignore" --include="*.py" . | grep -v .venv | grep -v __pycache__ | wc -l
# -> 659, on a tree matching origin/live-defi-rollout HEAD exactly (git status clean)
git stash pop
```

The follow-up "no-rule-code broad ignore" grep (`grep -v -F "# type: ignore["`) returns EMPTY — the extra occurrence is
a well-formed `# type: ignore[code]  # reason` line, not a banned broad ignore. I did not bisect the exact commit that
tipped the count from 658→659 (dozens of commits landed in this repo since the baseline was set at `d072b035` on
2026-07-31 — full bisection was out of scope for my actual task).

## Why it matters

STEP 5.95 is unconditional (no skip flag, no warn-only mode) — this is a hard QG failure that blocks Pass-1 for EVERY
worker touching this repo, not just mine, until either the baseline is bumped (with the actual `# type: ignore[code]`
addition audited/justified) or the extra occurrence is removed. Declaring a repo-blocker (`RB-` id) rather than silently
retrying, per `unified-trading-pm/agents/RULES.md` § 4b.

## Recommended decision

1. Find the commit(s) that pushed the count from 658 → 659 since `d072b035` (2026-07-31) — likely narrowable via
   `git log -p --since=2026-07-31 -- '*.py' | grep -B5 '# type: ignore'` or a bisect on the grep count.
2. If the new `# type: ignore[code]` is a legitimate, narrow, justified suppression (not a broad ignore — already
   confirmed it isn't broad), bump `_MTDS_TYPE_IGNORE_BASELINE` to 659 in `scripts/quality-gates.sh` in the SAME commit
   that added it (the gap here is procedural: the adding commit didn't also ratchet the baseline).
3. If it's NOT justified, fix the underlying type error and keep the baseline at 658 (ratchet shrinks, never grows
   without cause).

- [x] ✅ [BACKEND] P1. Root-cause the commit that added the 659th `# type: ignore[code]` in market-tick-data-service
      since `d072b035` (2026-07-31) and either (a) fix the underlying type error and keep the baseline at 658, or (b)
      bump `_MTDS_TYPE_IGNORE_BASELINE` to 659 in `scripts/quality-gates.sh` with the specific line cited as
      justification. Unblocks STEP 5.95 for every worker in this repo. (repo: market-tick-data-service) —
      market-tick-data-service@840c816d

## Progress Log

- 2026-08-03 (slot-8): filed after `tradfi_combo_casing_direction_ssot_contradiction-003`'s prep-work Pass-1 QG hit this
  red on an otherwise-unrelated 2-file diff; verified pre-existing via stash+clean-tree re-check. Declared repo-blocker
  `RB-9732d071` for market-tick-data-service. No code changed this entry — doc only.
- 2026-08-03 (slot-13): root-caused — not one single commit but a genuine cumulative drift across 9 commits since
  `d072b035` that touched `# type: ignore[code]` lines with mixed net effects (749ca622 net 0, a1198300 +4, 5d856acb -4,
  13f14b78 +3, 69c7ba7c -3, dc037373 +1, ce275975 +2, d3260d2f -2, 06cd3ca5 +1), netting to +1 overall (658→659).
  Slot-10 had already shipped the fix at `840c816d` (bumped `_MTDS_TYPE_IGNORE_BASELINE` 658→659, citing the
  zero-broad-ignore audit) but never flipped this checkbox. Independently re-verified on a clean
  `origin/live-defi-rollout` HEAD tree: live repo-wide count == baseline == 659, and `grep -v -F "# type: ignore["`
  (broad/bare ignore detector) returns 0 — confirms option (b) was applied correctly and STEP 5.95 now passes. Closing
  as resolved; no further code change needed.
