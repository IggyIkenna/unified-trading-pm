---
doc_type: issue
title: >-
  HeadBackwardCanary false-CRITICAL-paged 2 genuinely-safe branch-quarantine-heal discards — preserve-ref naming
  mismatch between the canary's detector and heal_dead_slot_branch_quarantine's producer
summary: >-
  2026-08-17 01:31 UTC and 03:16 UTC, HeadBackwardCanary paged CRITICAL "1 commit silently discarded by backward-HEAD
  reset" for slot-8 agent-orchestrator@66ec1a4d and slot-11 strategy-service@bf56f53b. Both discards were produced by
  WorkerLivenessWatchdog's periodic watchdog_unpushed_sweep tick calling heal_dead_slot_branch_quarantine() on a
  genuinely-dead slot (liveness=dead/absent, commit age >>900s guard) — working exactly as designed: it preserved each
  commit to a wip-preserve ref BEFORE realigning. But head_backward_canary.py's _find_preserve_ref() only ever queried
  the `wip-preserve/orchestrator-slot-<N>-<sha>` naming convention (_orphan.py's shape) — never
  heal_dead_slot_branch_quarantine's own DIFFERENT shape (`wip-preserve/slot-<N>-<repo>-<status>-<timestamp>`, no
  `orchestrator-` prefix, sha not in the ref name at all), introduced by that function 2026-06-21, over a month before
  the canary's ref-check was added 2026-07-27. Every branch-quarantine-heal-sourced discard was therefore
  STRUCTURALLY GUARANTEED to page CRITICAL regardless of whether the preserve succeeded — a distinct, previously
  undocumented failure mode, not a regression of either prior fix. Fixed in agent-orchestrator@70bc2b30d6 (queries both
  naming conventions in one ls-remote call) with a regression test. Both underlying commits were confirmed SAFE before
  the fix shipped: slot-11's content was already independently re-cherry-picked under a new sha (f89c6d82) by the
  slot's own next worker at 04:01 UTC (self-resolved); slot-8's fix was superseded by a more complete independent fix
  (agent-orchestrator@bc9835a3, landed 02:39:46 UTC, same root incident) — neither needed a forced cherry-pick.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, strategy-service]
scope: [engineer, admin]
tags:
  [
    git-safety,
    data-loss,
    false-positive,
    alerting,
    head-backward-canary,
    worktree-clean-check,
    branch-quarantine,
    worker-liveness,
    slot-8,
    slot-11,
  ]
related:
  [
    /plans/archive/issues/slot11_silent_branch_reset_data_loss_2026_07_13.md,
    /plans/archive/issues/slot_double_reset_dataloss_race_2026_07_25.md,
    /codex/04-architecture/agent-orchestrator-alerting.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
created: "2026-08-17"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by: >-
  agent-orchestrator@70bc2b30d6 — "fix(head-backward-canary): recognize branch-heal wip-preserve ref naming
  (head_backward_canary_preserve_ref_naming_mismatch_2026_08_17)"; regression test
  test_preserved_ref_populated_for_branch_heal_naming_convention added to tests/test_head_backward_canary.py; full
  quality-gates.sh green (4013 passed).
source: >-
  Operator-approved live production data-recovery task, 2026-08-17 ("check if self resolved else recover and gimme
  detailed on what you are recovering and why they were discarded"). Investigated read-only via AWS SSM against the
  orchestrator VM (i-0c9b283b31d6b5ca7, ap-northeast-1) — /api/state, /api/activity, and direct git (fetch/reflog/
  ls-remote) against .tabs/8/agent-orchestrator and .tabs/11/strategy-service, run as the `ubuntu` user for correct
  SSH/git-identity.
depends_on: []
---

> **🟢 RESOLVED 2026-08-17 — fix shipped (agent-orchestrator@70bc2b30d6) with a regression test; both underlying
> "discarded" commits confirmed already safe (one self-resolved under a new sha, one superseded by a more complete
> independent fix) — neither needed a forced cherry-pick.**

# HeadBackwardCanary false-paged 2 genuinely-safe branch-quarantine-heal discards (2026-08-17)

## What happened (the two pages)

`HeadBackwardCanary` (`agent-orchestrator/server/head_backward_canary.py`) paged `#agent-orchestrator-alerts` twice:

1. **01:31 UTC** — slot-8, `agent-orchestrator`, commit `66ec1a4d` "fix(bootstrap): re-upsert ORCHESTRATOR_VM_ID
   immediately after .env.local overwrite", reset detected at 01:21:00 UTC.
2. **03:16 UTC** — slot-11, `strategy-service`, commit `bf56f53b` "docs(strategy): confirm CEFI exclusion intentional
   for LIQUIDATION_CAPTURE slot", reset detected at 03:10:42 UTC.

Both alerts read "silently discarded ... recoverable only via reflog — cherry-pick NOW before it ages out" — the
CRITICAL, page-worthy classification the canary reserves for a discard with `preserved_ref=None` (no matching
wip-preserve ref found).

## Root cause: preserve-ref naming mismatch, not a data-loss bug

Traced both events to their exact activity-log record via `GET /api/activity`:

- Slot-8: `2026-08-17T01:22:10Z`, `event_type=slot_branch_quarantine_auto_heal`, `trigger=watchdog_unpushed_sweep`,
  `liveness=dead`, `preserved_refs=["agent-orchestrator:wip-preserve/slot-8-agent-orchestrator-diverged-20260817T012055Z", ...]`,
  `realigned_repos=["agent-orchestrator", ...]`.
- Slot-11: `2026-08-17T03:11:48Z`, same `event_type`, `trigger=watchdog_unpushed_sweep`, `liveness=absent`,
  `preserved_refs=["strategy-service:wip-preserve/slot-11-strategy-service-diverged-20260817T031037Z", ...]`,
  `realigned_repos=["strategy-service", ...]`.

Both fired from `WorkerLivenessWatchdog`'s periodic `watchdog_unpushed_sweep` tick (`worker_liveness_watchdog.py`
~line 1953) calling `heal_dead_slot_branch_quarantine()` (`worktree_clean_check/_branch_state.py`) with the STANDARD
900s `min_ahead_age_seconds` guard (not the narrower 300s scheduled-job override in `plan_health.py` — that path was
investigated and ruled out; both discarded commits were 50+ minutes old, far past even the general 900s floor, so the
age guard is not implicated at all). `classify_maker_liveness` correctly read `dead`/`absent` (each slot's prior tmux
session had genuinely ended). The heal did EXACTLY what it is designed to do: pushed the ahead commit to a
`wip-preserve/...` ref, verified the push, and only then realigned via `checkout -B <base> origin/<base>` — the
documented, safe, by-design preserve-then-realign sequence from `slot11_silent_branch_reset_data_loss_2026_07_13.md`
and `slot_double_reset_dataloss_race_2026_07_25.md`. **Confirmed live** via SSM `git ls-remote` (run as `ubuntu` for
working SSH auth — an earlier attempt as `root` failed with "dubious ownership"/"Permission denied" and produced a
false "0 refs" reading, corrected before drawing any conclusion): both preserve refs exist on origin RIGHT NOW and
resolve to the exact discarded SHAs —
`refs/heads/wip-preserve/slot-8-agent-orchestrator-diverged-20260817T012055Z` → `66ec1a4d927b...`,
`refs/heads/wip-preserve/slot-11-strategy-service-diverged-20260817T031037Z` → `bf56f53ba7c1...`.

**The bug is entirely in the canary's detector**, `_find_preserve_ref()`. It queried only
`refs/heads/wip-preserve/orchestrator-slot-<N>-*` — the naming convention `_orphan.py`'s
`commit_and_push_dirty_repos` (the dirty-state-inherit flow) uses. `heal_dead_slot_branch_quarantine`
(`_branch_state.py`) has ALWAYS used a different shape — `wip-preserve/slot-<N>-<repo>-<status>-<timestamp>`, no
`orchestrator-` prefix, sha never in the ref name — introduced in `8d728a8` (2026-06-21, the original self-healing
hardening commit). The canary's `_find_preserve_ref` was added over a month later, `fe961502` (2026-07-27), and its
single glob pattern only ever matched the first shape. **This makes every branch-quarantine-heal-sourced discard
structurally unrecoverable-by-detection** — the canary reports `preserved_ref=None` (real, page-worthy loss)
100% of the time for this path, independent of whether the preserve genuinely succeeded (which, per the code's own
design, it almost always does — the function refuses the whole realign on a preserve-push failure, per
`_branch_state.py:498-506`). This is a **new, distinct failure mode** — not a regression of either the 900s age-guard
fix (`slot11_silent_branch_reset_data_loss_2026_07_13.md`) or the realign-cooldown/age-guard-hoisting fix
(`slot_double_reset_dataloss_race_2026_07_25.md`); both of those are working correctly here, confirmed by reading the
live code paths and activity-log evidence above.

## Fix shipped — agent-orchestrator@70bc2b30d6

`_find_preserve_ref()` now queries BOTH naming conventions in one `git ls-remote` call (still a single read-only
remote query):

```python
ls = _git(
    repo_path, "ls-remote", "origin",
    f"refs/heads/wip-preserve/orchestrator-slot-{slot}-*",
    f"refs/heads/wip-preserve/slot-{slot}-*",
)
```

Regression test `test_preserved_ref_populated_for_branch_heal_naming_convention` added to
`tests/test_head_backward_canary.py`, reproducing the exact `_branch_state.py` ref shape. Full `quality-gates.sh`
green (4013 passed, 7 skipped). Shipped via quickmerge, landed on `live-defi-rollout`.

## Both "discarded" commits — confirmed safe, neither cherry-picked

Per this workspace's own established precedent (`slot11_silent_branch_reset_data_loss_2026_07_13.md` UPDATE 5/6 —
check for independent re-implementation before blindly cherry-picking a flagged sha), both were verified rather than
mechanically recovered:

- **Slot-11 `bf56f53b` — SELF-RESOLVED under a new sha.** `git log --oneline -- strategy_service/engine/strategies/v2/archetype_slots_defi.py`
  on the live slot-11 clone shows `f89c6d82 docs(strategy): confirm CEFI exclusion intentional for LIQUIDATION_CAPTURE slot`
  — same message, already reachable from current `live-defi-rollout` HEAD. The slot's own reflog confirms the
  timeline: `bf56f53b` committed 02:39:14 → reset 03:10:42 → **the SAME slot's next worker cherry-picked it back
  itself at 04:01:07** (`f89c6d82`), 51 minutes after the reset and well before this investigation began. A literal
  `merge-base --is-ancestor bf56f53b HEAD` correctly reads false (new sha, same content) — content-diff confirmed the
  exact added comment block is present at the live HEAD. **No action taken** — attempting the original sha's
  cherry-pick reproduces this exactly ("previous cherry-pick is now empty, possibly due to conflict resolution"),
  confirming the content match; committing an empty cherry-pick was correctly refused.
- **Slot-8 `66ec1a4d` — SUPERSEDED by a more complete independent fix, not merely duplicated.** Cherry-picking onto
  current HEAD produces a genuine conflict in `scripts/bootstrap_vm.sh`: current HEAD (`bc9835a3`, landed **02:39:46
  UTC — 43 minutes after the 01:21:00 discard**, i.e. very likely the very first action of slot-8's own respawned
  worker, one second before its `last_spawned_at`) independently root-caused the SAME incident
  (`ao_satellite_ao_dispatch_batch21`, "planning"'s `.env.local.bak.1786877088` forensic evidence — identical citation
  to `66ec1a4d`'s own commit body) and shipped a STRICTLY STRONGER fix: skip the destructive `.env.local` overwrite
  entirely for an already-provisioned host (upsert blob keys in place instead), rather than `66ec1a4d`'s narrower
  mitigation of moving the `ORCHESTRATOR_VM_ID` re-upsert earlier to shrink the interruption window. Since the
  destructive overwrite branch is now unreachable at all for an already-provisioned host, there is no window left to
  shrink — `66ec1a4d`'s specific patch is fully subsumed. Forcing the old, narrower fix on top would reintroduce
  now-unnecessary code movement and confuse which guard is authoritative. **No action taken** — verified functionally
  equivalent-or-better, matching the "re-implemented more completely" pattern from `slot11_silent_branch_reset_data_loss_2026_07_13.md`
  UPDATE 5/6.

## Todos

- [x] [BACKEND] P2. Fix `_find_preserve_ref()` to recognize both wip-preserve ref naming conventions. —
      agent-orchestrator@70bc2b30d6, regression test added, quality-gates.sh green.
- [x] [VERIFY] P2. Confirm slot-8 `66ec1a4d` and slot-11 `bf56f53b` are each genuinely safe before any forced
      cherry-pick. — done above; both confirmed safe by independent means (self-resolved-under-new-sha /
      superseded-by-more-complete-fix), no cherry-pick performed for either.
