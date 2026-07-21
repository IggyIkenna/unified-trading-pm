---
doc_type: issue
title:
  "GIT STATUS RED auto-nudge repeats a stale dirty-file claim for deployment-ui (cost-observability-mockup.html) across
  15000+ minutes"
summary:
  Slot 4's heartbeat/boot responses repeatedly carry a GIT STATUS RED nudge claiming `deployment-ui` has 1 dirty file
  (`cost-observability-mockup.html`), with a monotonically climbing "dirty for Nm" counter (11615m → 15050m across one
  session). Directly verified twice ~90 min apart that `.tabs/4/deployment-ui` is genuinely clean (`git status` reports
  nothing to commit) and the named file does not exist anywhere in the worktree or its history. The server-side
  git-status watcher generating this nudge is reading stale/cached state that never got invalidated.
status: resolved
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [git-status-watcher, false-positive, stale-cache, monitoring, orchestrator]
related: []
created: 2026-07-21
priority: P3
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: infra
drift_direction: advance-code
source: "slot-4 heartbeat/boot responses, 2026-07-21"
resolved_by: "agent-orchestrator@5e0f67d, 2026-07-21"
locked_by:
depends_on: []
---

## What I found

Slot 4's `/boot`, `/heartbeat`, and `/progress` responses repeatedly carried this message, with a monotonically
increasing "dirty for Nm" counter (11615m at session start, 15050m ~90 min later in the same session):

```
🟥 GIT STATUS RED — auto-nudge per CLAUDE.md HARD RULE 'Commit + Push + Flip plan checkbox SAME agent turn'.
Your slot has 1 repo(s) past the yellow threshold:
  - deployment-ui: dirty 1 files for 15050m — COMMIT+PUSH [?? cost-observability-mockup.html]
```

Directly verified in `.tabs/4/deployment-ui` (twice, ~90 min apart):

```
$ git status
On branch live-defi-rollout
Your branch is up to date with 'origin/live-defi-rollout'.
nothing to commit, working tree clean
```

`cost-observability-mockup.html` does not exist anywhere under `.tabs/4/deployment-ui` (`find` returns nothing), and it
has no history in this worktree (`git log -- cost-observability-mockup.html` empty). The repo is genuinely clean; the
nudge is stale.

## Why it matters

The counter has been climbing for 15000+ minutes (~10+ days) across what look like multiple sessions on slot 4 — the
server-side git-status watcher that generates this nudge is reading a state that no longer matches the actual worktree
(most likely a cached scan result, or a scan of a different/stale path, that never got invalidated after the file was
committed/removed or the worktree was reset). Left unfixed, this will keep firing on every heartbeat/boot for slot 4
indefinitely, training operators/agents to ignore GIT STATUS RED nudges generally — which defeats the actual HARD RULE
this mechanism exists to enforce.

## Recommended decision

Someone with access to the orchestrator server's git-status-watcher code should: (1) confirm whether it caches
dirty-file state without a TTL/invalidation-on-clean-check, and (2) add a self-healing re-scan (or at minimum, a
one-shot re-verify against live `git status` before re-emitting the nudge) so a genuinely-cleaned repo stops alerting.
Not fixed inline this session — the watcher's implementation is outside `.tabs/4` (orchestrator-server-side), out of
scope for a data_engineering/cicd dispatch.

- [x] [INFRA] P3. ✅ Root-cause + fix the stale GIT STATUS RED nudge for slot 4 / deployment-ui (server-side git-status
      watcher reading stale/cached state instead of live `git status`) — see evidence above. —
      agent-orchestrator@5e0f67d

## Root cause + fix (2026-07-21)

`maybe_nudge_on_red_repos` (`server/worker_liveness/_git_alerts.py`) read `slot.git_status_json` — a snapshot POSTed
every 5 min by `slot-git-status-report.sh` — and computed `dirty for Nm` as `now - dirty_oldest_mtime` from that cached
snapshot, with **no check that the snapshot itself was still being refreshed**. If a slot's reporter cron dies (dead
host / cron disabled / VM decommissioned), `git_status_json` freezes at its last-posted instant forever; every
subsequent kicker tick still recomputes the age against the live `now`, so the counter climbs unbounded even after the
real repo is clean — exactly the 11615m → 15050m growth observed for slot 4 / deployment-ui.

Fix: before trusting the snapshot's embedded per-repo ages, check `slot.git_status_reported_at` freshness against
`REPORTER_STALE_S` (15 min) — the same constant `maybe_alert_git_staleness` already uses to detect a silent reporter
cron. If the snapshot itself is stale, skip the worker nudge rather than repeat an unconfirmable claim (the operator is
already separately paged for the dead-reporter condition via the existing Slack staleness alert). Added two regression
tests (`test_nudge_skipped_when_snapshot_itself_is_stale`, `test_nudge_still_fires_on_fresh_snapshot`) to
`tests/test_git_staleness_alerting.py`. Full QG green (1539 passed).

Scope note: `maybe_alert_git_staleness` (the Slack-paging path) already has its own reporter-silence handling and was
not touched — only the worker-facing nudge (`maybe_nudge_on_red_repos`) had this gap.
