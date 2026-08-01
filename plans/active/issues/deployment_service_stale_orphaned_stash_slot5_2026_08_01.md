---
doc_type: issue
title:
  deployment-service slot-5 checkout has a 5-week-old orphaned git stash — real WIP invisible to any tracking, at risk
  of permanent loss
summary: >-
  `.tabs/5/deployment-service`'s local git stash carries a `stash@{1}` autostash dated 2026-06-22T19:17:17Z (5+ weeks
  old as of this writing, 2026-08-01) — a `data_pipeline_monitors/cli.py` + `escalation.py` refactor (swaps the existing
  `_ensure_live_events()` PubSub-wiring pattern for a `run_lifecycle()`/`setup_events()`-at-main() pattern) + a
  `launch-defi-backfill-vm.sh` tweak (bigger machine type, `--preemptible`, a manifest-staleness metadata fix) +
  matching test stubs. It was never mine — discovered as a pre-existing `git pull --rebase --autostash` artifact while
  working an unrelated task in this checkout. Stashes are 100% local (never pushed/backed up), so this is real,
  substantial work that vanishes permanently if this VM's disk is ever reset, with zero record anywhere else.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [git, stash, multi-agent-safety, per-tab-worktrees, data-pipeline-monitors, orphaned-wip]
related:
  [
    /plans/archive/issues/dp_event_pubsub_delivery_gap_2026_06_22.md,
    /plans/active/issues/multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md,
  ]
created: 2026-08-01
author: backend_engineer (slot-5)
assigned_vm: NA
parent_epic: agent_operating_framework_master
execution_scope: local-only
priority: P3
source: [git stash list / git stash show -p stash@{1} in .tabs/5/deployment-service, discovered incidentally 2026-08-01]
resolved_by:
locked_by:
---

# deployment-service slot-5 checkout has a 5-week-old orphaned git stash

## What I found

`.tabs/5/deployment-service` — `git stash list` shows two entries:

```
stash@{0}: autostash   (2026-08-01T10:30:38Z — mine, from this session, already superseded/redundant, left in place;
                         `git stash drop` is hard-blocked by the orchestrator guardrail for autonomous workers)
stash@{1}: autostash   (2026-06-22T19:17:17Z — NOT mine, pre-existing, 5+ weeks old)
```

`stash@{1}`'s content (`git stash show -p stash@{1}`):

- `deployment_service/data_pipeline_monitors/cli.py` (198 lines changed) — replaces the CURRENT LIVE
  `escalation.route_finding()`'s `_ensure_live_events()` PubSub-wiring call with a different pattern: `setup_events()`
  called once near the top of `main()` (best-effort, wrapped in `try/except`) + a
  `with run_lifecycle(service_name= "dp-fleet-monitor"):` context manager wrapping the whole dispatch body.
- `deployment_service/data_pipeline_monitors/escalation.py` (37 lines removed) — deletes `_ensure_live_events()`
  entirely (the function the LIVE file currently defines + calls).
- `scripts/vm/launch-defi-backfill-vm.sh` — `MACHINE_TYPE` default `e2-standard-4` → `e2-standard-8`, adds
  `--preemptible`, adds `MANIFEST_CONSOLIDATED_STALENESS_SEC=86400` metadata (comment: "Daily catalog → 120s
  consolidated-staleness default is too short").
- `tests/unit/test_data_pipeline_monitors_cli.py` (+15 lines) — adds `_stub_main_cloud()` monkeypatch helper stubbing
  `setup_events`/`run_lifecycle` so `cli.main()` tests stay credential-free under the new pattern.

**The timestamp (2026-06-22) exactly matches `/plans/archive/issues/dp_event_pubsub_delivery_gap_2026_06_22.md`** — the
issue this refactor appears to have been addressing. That issue is **already `status: resolved`**
(`resolved_by: 2026-07-28 (plan-vintage-audit archival, [unlock-plan] granted)`), resolved via the
`_ensure_live_events()` pattern the CURRENT live `escalation.py` already has — i.e. a DIFFERENT fix than this stash's
approach shipped and landed instead. This stash may therefore be a superseded alternate attempt (safe to discard) or may
carry a genuinely better pattern (`run_lifecycle()` context manager vs. the lazy-init `_ensure_live_events()` singleton)
that was simply never compared/merged — I did not have the context to judge which, and this is exactly the kind of
"worth a second pair of eyes before discarding real code" call the `git stash drop` guardrail exists to force.

## Why it matters

- Stashes are **local-only** — never pushed, never backed up, invisible to `git log`, GitHub, or any dashboard. If this
  VM's disk is ever reset/rebuilt (a real operational event for this workspace — VMs get replaced), this WIP is gone
  with no trace it ever existed, except this doc.
- It sat here through however many `/boot` cycles this slot has run since 2026-06-22 without being noticed — the
  fresh-pull discipline (`git pull --rebase --autostash`) only ever autostashes/pops the CURRENT invocation's own local
  diff; it doesn't surface or clean up an OLDER stash entry sitting underneath.
- `git stash drop`/`git stash clear` are hard-blocked for autonomous workers (orchestrator guardrail,
  `block_destructive_commands.py`) — correctly so, since distinguishing "safe to discard" from "someone's real
  in-progress work" from the stash content alone is a judgment call, not a mechanical check.

## Recommended decision

- [ ] [OPERATOR] P3. Review `deployment-service` slot-5's `stash@{1}` (`git stash show -p stash@{1}`, dated 2026-06-22)
      — decide whether the `run_lifecycle()`/`setup_events()`-at-`main()` pattern it introduces is worth merging over
      the currently-live `_ensure_live_events()` pattern (or the reverse — confirm the live pattern is strictly better
      and the stash is safe to drop), then either land it as a real commit or `git stash drop     stash@{1}` (human-only
      action — the orchestrator guardrail blocks this for agents) to stop it silently persisting. Also worth a broader
      question while here: should any slot's `/boot` fresh-pull step warn on a stash entry older than N days, so this
      class of silent-loss risk doesn't require a human stumbling onto it by accident (as happened here)? — a candidate
      follow-up, not this todo's scope.
