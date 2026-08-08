---
doc_type: issue
title:
  AO dispatch-visibility gate regressed (26 > baseline 24) — sports_all_vendor_honest_coverage_convergence's combined
  [SCRIPT][BLOCKED-UPSTREAM-OUTAGE] tag reads as an undeclared exclusion
summary: >-
  While shipping an unrelated docs-only fix, `check_ao_dispatch_visibility_gate.py`'s zero_dispatchable_docs axis failed
  (26 > baseline 24) due to concurrent, unrelated sports-capture-session commits that landed via a routine fresh-pull
  mid-task. Root-caused one concrete new regression: `sports_all_vendor_honest_coverage_convergence_2026_08_07.md`'s
  todo tags `[SCRIPT][BLOCKED-UPSTREAM-OUTAGE]` back-to-back with no separating space, and the parser's marker-detection
  apparently expects the BLOCKED-token to open its own bracket in isolation (or at least be independently matched),
  reading the combined form as an undeclared/accidental exclusion. Re-baselined to the measured 26 to unblock unrelated
  shipping per this gate's own documented remedy ("only --update-baseline after fixing or filing the newly-found
  accidental exclusions") — did not attempt the parser fix itself (agent-orchestrator code change, outside this
  session's docs-only task scope).
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [ao, dispatch-visibility, ratchet, sports, false-positive]
related:
  [
    /plans/archive/issues/ao_silently_non_dispatchable_todos_have_no_visibility_gate_2026_08_08.md,
    /plans/active/issues/sports_all_vendor_honest_coverage_convergence_2026_08_07.md,
  ]
created: 2026-08-08
author: unknown
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: refactor
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
context_scope:
  [
    agent-orchestrator/server/regen_backlog_from_plan.py,
    scripts/quality_gates/check_ao_dispatch_visibility_gate.py,
    scripts/quality_gates/ao_dispatch_visibility_baseline.yaml,
    /plans/active/issues/sports_all_vendor_honest_coverage_convergence_2026_08_07.md,
  ]
source: >-
  Surfaced 2026-08-08 while shipping ao_satellite_ao_dispatch_batch5-003 (unrelated docs-only §3/§4 closure) — the QG's
  post-gate check failed on unrelated corpus drift that landed via a routine mid-task fresh-pull.
---

# AO dispatch-visibility gate regressed on an unrelated, concurrent sports-capture commit

## What I found

`bash scripts/quality-gates.sh` failed its `ao-dispatch-visibility` post-gate check
(`check_ao_dispatch_visibility_gate.py`) with `zero_dispatchable_docs=26 > baseline 24`. My own staged diff (5 docs-only
files, none of them AO-dispatch-related) did not touch any of the 26 flagged docs — confirmed via
`git diff --cached --stat` before running QG. Root-caused at least one of the +2 new regressions:
`plans/active/issues/sports_all_vendor_honest_coverage_convergence_2026_08_07.md` line 175 —

```
- [ ] [SCRIPT][BLOCKED-UPSTREAM-OUTAGE] P2. **Retry Transfermarkt's 8 attempted_failed PLAYER_VALUES rows** ...
```

— landed by `085fabcac` (2026-08-08 22:23Z, a live sports-capture session ticking through unrelated smallchunk progress,
pulled into my worktree by an ordinary `git pull --rebase --autostash` mid-task). The
`[SCRIPT][BLOCKED-UPSTREAM-OUTAGE]` combined bracket (no separating space between the two tags) reads to
`_parse_open_todos` (agent-orchestrator's `server/regen_backlog_from_plan.py`) as an undeclared/accidental exclusion —
`excluded: [{"declared": false}]` in the gate's own `--json` output — even though the BLOCKED marker visually looks like
it opens its own bracket. Not independently traced into the actual `_STALE_MARKER_*_RE` regex (that's a real
agent-orchestrator code investigation, out of scope for the docs-only task this was found under).

## Why it matters

This is the exact bug class `ao_silently_non_dispatchable_todos_have_no_visibility_gate_2026_08_08.md` (now archived)
was built to catch: a plan renders a live `- [ ]`, the operator sees tracked work, and AO silently never dispatches it.
If the `[TAG][BLOCKED-<token>]` no-space-combined form is systematically mis-parsed, every existing todo using that
exact authoring style (not just this one sports doc) is silently non-dispatchable — worth a grep across the corpus once
root-caused, not assumed to be a single-doc fluke.

## Recommended decision

Re-baselined `max_zero_dispatchable_docs: 24` → `26` in the same commit as the unrelated fix that surfaced this, per the
gate script's own documented remedy (file + re-baseline, don't hand-raise silently). This is NOT a fix — it just stops
an unrelated, pre-existing regression from blocking every other agent's shipping. A real fix needs: (a) confirm the
exact regex in `regen_backlog_from_plan.py` that decides "declared" vs "accidental" for a `[TAG][MARKER]`-combined
bracket (vs. `[TAG] [MARKER]` with a space, or `[MARKER]` alone) — likely a missing alternative in `_STALE_MARKER_*_RE`;
(b) grep the corpus for other `]\[BLOCKED-`/`]\[DEFERRED-BY-DESIGN`/`]\[stretch` no-space combos to size the blast
radius before fixing; (c) fix the regex + add a regression test; (d) re-run this gate and lower
`max_zero_dispatchable_docs` back down once confirmed clean.

## Todos

- [ ] [BACKEND] P3. **Root-cause + fix the `[TAG][BLOCKED-<token>]` no-space-combined-bracket parse gap in
      `agent-orchestrator/server/regen_backlog_from_plan.py`'s `_parse_open_todos`/`_STALE_MARKER_*_RE`.** Confirm via a
      unit test reproducing `sports_all_vendor_honest_coverage_convergence_2026_08_07.md:175`'s exact tag ordering.
      Repo: agent-orchestrator.
- [ ] [SCRIPT] P3. **Grep the corpus for other `]\[BLOCKED-`/`]\[DEFERRED-BY-DESIGN`/`]\[stretch` no-space combos** once
      the regex root cause is confirmed, to size how many other docs share this same silent-exclusion bug. Repo:
      unified-trading-pm.
- [ ] [SCRIPT] P3. **Once fixed, re-run `check_ao_dispatch_visibility_gate.py --update-baseline` to ratchet
      `max_zero_dispatchable_docs` back down** from 26 to the newly-clean measured count. Repo: unified-trading-pm.

## Progress Log

- **2026-08-08**: filed during `ao_satellite_ao_dispatch_batch5-003` (unrelated docs-only §3/§4 closure task) — the
  regression blocked shipping via the standard Pass-1 QG flow; re-baselined in the same commit per this doc's own
  Recommended decision.
