---
doc_type: issue
title: >-
  PM ldr-to-main-promote inflight_wait wedges on a run whose checks slice already failed — LDR sat 1627 commits ahead of
  main for 80+ min behind a doomed stale promote PR
summary: >-
  Found 2026-08-10 by the ci-reconciler hourly sweep. PM's LDR→main promotion was wedged: LDR 1627 commits ahead of main
  while the only open promote PR (#2713, frozen head promote/unified-trading-pm/12bb896a446c) carried a quality-gates-v2
  run whose CHECK slice had already concluded failure (the AG-closeout linkage ratchet) but whose TESTS leg was still
  running (90+ min in, up to the 135-min timeout). ldr-to-main-promote.yml's `inflight_wait` block counts ANY
  non-terminal QG run for the inflight head as "about to pass" (`status != completed`) and refuses to supersede the
  stale PR that tick — so it never opened a fresh promote PR on the fixed tip and the drain sat blocked. Nothing paged:
  the promote runs all concluded `success` (action=inflight_wait) and the doomed run's own CRITICAL Slack was about the
  AG-closeout content (already fixed on LDR), not the wedge itself. This is the exact class the ci-reconciler role
  exists to catch (a red promotion stall invisible to #ci-failures). FIX SHIPPED: ldr-to-main-promote.yml now queries
  the inflight head's check-runs; if any QG slice has concluded `failure`, it supersedes immediately instead of waiting
  the doomed run out (fail-open on query error → original inflight_wait). Shipped `unified-trading-pm@caf9921d12` (LDR,
  quickmerge). Manually cancelled the doomed run (`gh run cancel 31395941118`) as the immediate unblock — the next tick
  superseded #2713 and opened fresh PR #2714 on the fixed tip (carries the fix + the AG-closeout baseline fix, QG in
  progress).
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, promotion, ci_reconciler, ldr-to-main-promote, inflight-wait, wedge]
related:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /plans/active/issues/ldr_to_main_promote_fleet_queued_run_cancelled_livelock_2026_08_07.md,
  ]
created: 2026-08-10
source: ci-reconciler sweep
resolved_by:
locked_by:
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: small
drift_direction: fix_shipped
depends_on: []
context_scope:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /plans/active/issues/ldr_to_main_promote_fleet_queued_run_cancelled_livelock_2026_08_07.md,
    .github/workflows/ldr-to-main-promote.yml,
  ]
---

# PM ldr-to-main-promote inflight_wait wedges on a doomed run

## Symptom

- LDR 1627 commits ahead of `main` (compare `main...live-defi-rollout` → `ahead_by:1627, behind_by:1`), growing.
- Single open promote PR #2713 frozen at `12bb896a` (pre-fix head) for 80+ min.
- Its QG run `31395941118`: `QG slice (checks)` = **failure** (concluded 14:05Z), `QG slice (tests)` = **in_progress**
  (started 14:02Z). Run overall non-terminal → inflight_wait fires every tick.
- Promote ticks all concluded `success` with `action=inflight_wait` → nothing paged on the wedge itself.

## Root cause

`ldr-to-main-promote.yml` (PM-LOCAL, no template) inflight_wait block:

```bash
_V2_INFLIGHT=$(gh run list ... --json headSha,status --jq "[.[]|select(.headSha==\"$_INFLIGHT_SHA\" and .status!=\"completed\")]|length")
if [ "${_V2_INFLIGHT:-0}" != "0" ]; then
  echo "⏳ ... still running — not superseding this tick, letting it finish"
  ... exit 0
fi
```

Any non-completed run (regardless of a slice already failing) counts as "about to pass". A run whose checks slice failed
CANNOT pass — waiting only wedges the drain behind the slow tests leg (70-135 min). The 2026-07-27 inflight_wait
feature's intent (don't preempt a run that might pass) is preserved; the bug is it also waits on runs that provably
can't.

## Fix (shipped)

- `unified-trading-pm@caf9921d12` (LDR, quickmerge): before inflight_wait, query the inflight head's check-runs
  (`gh api .../commits/<sha>/check-runs`); if any check-run named `*QG slice*` has `conclusion == "failure"`, log
  `⏭ ... superseding this tick instead of waiting it out` and fall through to the supersede path. Fail-open: query error
  → `_V2_DOOMED=0` → original inflight_wait (never supersede on a broken check).
- Immediate unblock (this run): `gh run cancel 31395941118` terminated the doomed tests leg → next */15 tick superseded
  #2713 and opened fresh **PR #2714** on the current fixed tip (300 changed files, auto-merge armed).

## Verification

- 15:45Z promote tick: `closed superseded promote PR #2713`, `opened .../pull/2714`, `auto-merge armed`.
- PR #2714 head `111006224b` includes `caf9921d12` (ancestor-verified); QG run `31405420640` in_progress.
- Both the promote fix and the separate `workspace-quickmerge-validation` provisioning fix
  (`unified-trading-pm@53f632d92`) ride LDR→main via the normal promote path.

## Follow-ups

- [ ] [DEVOPS] P2. Confirm PR #2714 merges green (QG run `31405420640`) and LDR→main catches up; then close this issue.
- [ ] [DEVOPS] P3. Consider the same doomed-run guard in `ldr-to-main-promote-fleet.yml`'s per-repo supersede path if
      the fleet bot ever shows the same wait-on-doomed-run shape (no evidence of it today — fleet PRs are per-SHA
      fresh).

## Progress Log

**context-scout 2026-08-14**: populated context_scope (3 entries)
