---
doc_type: issue
title:
  repo-blocker resolution signal (watcher_green / reporter) fired twice while the underlying QG condition still failed
summary:
  Declared `RB-166e706f` for a genuine `market-tick-data-service` QG red (STEP 5.101 empty-string-fallback baseline
  breach — chronic, separately tracked in `mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md`).
  Received TWO consecutive "resolved" notifications (`resolve_source=watcher_green`, then `resolve_source=reporter` on
  the re-declared `RB-eb458809`) roughly 70 and 15 minutes apart respectively — both times a fresh, direct
  `check_no_empty_string_fallback.py --scope market-tick-data-service` re-run (repo confirmed at unchanged HEAD, zero
  new commits) reproduced the IDENTICAL failure both times. The condition never actually changed across all 3
  measurements; only the resolution signal did.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [repo-blocker, multi-agent-safety, false-positive, reliability, quality-gates]
related:
  [
    /plans/archive/issues/mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md,
    /plans/active/sports_track_h_denominator_prereqs_2026_07_28.md,
  ]
created: 2026-07-28
priority: P2
parent_epic: agent_operating_framework_master
source: "Self-observed by slot-14 during sports_track_h_denominator_prereqs-002, 2026-07-28"
resolved_by:
locked_by:
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-28
---

# repo-blocker resolution signal false-positive — 2026-07-28

## What I found

Timeline (all times UTC 2026-07-28):

1. **~13:45** — declared `RB-166e706f` after `quality-gates.sh --no-fix` genuinely failed STEP 5.101 (91
   empty-string-fallback sites > baseline 89, `scripts/verify_lst_collateral_support.py:89,167`).
2. **~14:56** — received
   `[orchestrator repo-health] market-tick-data-service is GREEN again (blocker RB-166e706f resolved via watcher_green)`.
   Fresh-pulled both `market-tick-data-service` and `unified-trading-pm` to `origin/live-defi-rollout` HEAD (zero
   pending commits either side), re-ran the FULL `quality-gates.sh --no-fix` — **identical failure**, same file, same
   line numbers, same counts (91 > 89).
3. **~15:14** — re-declared as `RB-eb458809` with this evidence.
4. **~15:34** — received
   `[orchestrator repo-health] market-tick-data-service is GREEN again (blocker RB-eb458809 resolved via reporter)`.
   Fresh-pulled `market-tick-data-service` again — `git rev-parse HEAD` unchanged (`873c6c73`, no new commits at all
   since step 2). Ran the TARGETED checker directly
   (`check_no_empty_string_fallback.py --scope market-tick-data-service`, faster than the full suite) — **identical
   failure again**, same 91 > 89, same 2 lines.
5. **~15:32** — re-declared a 3rd time as `RB-b6432008`.

**The underlying repo state genuinely never changed** across all 3 measurements (same HEAD SHA both times I checked it,
same live violation count both times I ran the checker). Only the orchestrator's own resolution signal fired twice,
incorrectly, from two DIFFERENT `resolve_source` values (`watcher_green` then `reporter`) — ruling out a single buggy
code path being the sole cause; this looks like two independent ways to reach an incorrect "resolved" state.

## Why it matters

The repo-blocker mechanism exists specifically so a worker doesn't have to self-poll a red repo (`worker.md` § 4b: "the
backend's RepoHealthWatcher then polls the repo's CI state ITSELF and, the moment it reads green, sends you an outbox
message"). If that signal is unreliable, EVERY waiter on a blocker is at risk of either (a) wasting time re-verifying a
false "resolved" signal (this session's cost: ~2 extra full/targeted QG runs, ~20 min), or worse, (b) a worker with LESS
verification discipline than this session applied trusting the signal and attempting to ship/quickmerge against a
still-red tree — which `quickmerge.sh`'s own Pass-1 QG gate would still catch (so no actual bad code reaches
`live-defi-rollout`), but would produce a confusing quickmerge failure disconnected from the worker's own (correctly
blocked) mental model.

## Recommended decision

1. **Did NOT attempt to root-cause the resolution-signal bug itself** — out of scope for this session (I don't have
   `agent-orchestrator`'s `RepoHealthWatcher`/reporter code open, and my actual task is unrelated data-pipeline work);
   flagging for whoever owns that subsystem.
2. **Established a local mitigation this session**: never trust a `resolved via <source>` notification at face value for
   a repo-blocker — always fresh-pull + re-run the SPECIFIC failing check (or full QG) before proceeding to ship. Worth
   promoting into `worker.md` § 4b's own text (currently reads "the green signal arrives as a message... act on it
   immediately" — this instance shows that's not always safe without a fresh local re-verify first).

- [ ] [SCRIPT] P2. Whoever owns `agent-orchestrator`'s `RepoHealthWatcher` (the `watcher_green` source) and the
      `reporter`-triggered resolution path should investigate why BOTH independently declared this specific
      `market-tick-data-service` blocker resolved while a direct re-run of the exact same check it should be keying off
      (`check_no_empty_string_fallback.py --scope market-tick-data-service` / the STEP 5.101 gate inside
      `quality-gates.sh`) still failed identically both times. Candidate angles: is the watcher checking a CACHED CI
      result rather than a live re-run; is it checking the WRONG check (e.g. overall `quality-gates-v2` status on a
      DIFFERENT commit than the one that actually failed STEP 5.101 locally); is `reporter`-source resolution keyed off
      a different waiter's self-report that itself was wrong. (repo: agent-orchestrator)
- [ ] [DOC] P3. Once root-caused, add a one-line caution to `worker.md` § 4b ("declare a repo-blocker") noting that a
      `resolved via <source>` notification should still be locally re-verified (fresh-pull + targeted re-check) before
      shipping, until this specific reliability gap is closed — cheap insurance, not a distrust of the mechanism in
      general. (repo: unified-trading-pm)
