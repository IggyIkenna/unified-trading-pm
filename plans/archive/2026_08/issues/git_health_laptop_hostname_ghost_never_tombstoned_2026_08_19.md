---
doc_type: issue
title:
  "Fleet git-health: a laptop hostname rename creates a ghost host bucket that can never self-resolve — MacBook-Pro to
  Mac paged agent-orchestrator-alerts continuously for 3.5+ days"
summary: >-
  Operator's laptop's OS-reported `hostname -s` changed from `MacBook-Pro` to `Mac` (~2026-08-15/16, evidence: the
  `.stash-archive-{Mac,laptop}-slot2-*` directory-name split and Slack's first "silent for" reading). The reporter/
  ff-pull crons (`unified-trading-pm/scripts/dev/slot-git-status-report.sh:173`, `hostname -s`) now post under the new
  name; the OLD `MacBook-Pro` bucket in agent-orchestrator's `SlotGitStatusRow` table is frozen forever. Root cause:
  `agent-orchestrator/server/host_tombstone.py`'s `is_host_tombstoned` — the ONLY thing that stops
  `WorkerLivenessKicker._git_surfaces_pass` (`server/worker_liveness/__init__.py:676`, `if is_host_tombstoned(host):
  continue`, gating BOTH the Slack pager and the fleet-dashboard summary) from treating a dead host as an ongoing
  incident — is deliberately scoped to AWS EC2-shaped hostnames only (`_AWS_HOSTNAME_RE`, `^ip-\d+-\d+-\d+-\d+$`); its
  own comment states a laptop hostname "must never be tombstoned" via that path. A renamed laptop bucket therefore has
  NO path to ever self-resolve — confirmed live via `agent-orchestrator-alerts`: `MacBook-Pro` paged every ~15-90min,
  continuously, for 3.5+ days straight (`git reporter cron: silent for <N>m`, N climbing in lockstep with wall-clock
  time, never once recovering), exactly the never-resolving-condition anti-pattern
  `/codex/04-architecture/agent-orchestrator-alerting.md` rules against. Investigated whether a direct DB purge/rename
  of the stale rows was available instead: confirmed NO sanctioned delete/rename mechanism exists for
  `SlotGitStatusRow` (only an unrelated `delete_slot()` on a different table); the DB is a single centralized SQLite
  file on the `planning` VM (`server/db.py:108`), so a raw-SQL row rename would need VM/operator access and risks a
  `(host, slot_id)` primary-key collision if "Mac" already reports the same slot numbers — a code-level fix was both
  safer and immediately available.
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [git-health, monitoring, false-positive, tombstone, host-rename, agent-orchestrator, slack-alerting]
related:
  [
    /codex/04-architecture/agent-orchestrator-alerting.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    plans/archive/issues/git_health_phantom_dirty_flicker_ff_cron_race_2026_07_21.md,
  ]
created: 2026-08-19
last_updated: 2026-08-19
priority: P2
parent_epic: infrastructure_master
source: "operator (interactive session), 2026-08-19 — asked why the fleet dashboard showed two Mac-like hosts"
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
drift_direction: advance-code
resolved_by: "agent-orchestrator@fb615aba94 (host_tombstone.py _KNOWN_RENAMED_HOSTS floor)"
locked_by:
depends_on: []
---

> **🟢 ARCHIVED 2026-08-19** — status=resolved, 0 open todos. Archived per
> /codex/11-project-management/issue-doc-lifecycle.md's archive-on-resolve rule.

## What was found

The fleet git-health dashboard (`agent-orchestrator/dashboard/src/FleetGit.tsx`) showed two host panels for what is a
single physical laptop: `Mac · planning` (live, fresh snapshots) and `MacBook-Pro · planning` (every slot showing
`reporter dead` + `ff-pull dead`, `snap:3d ago`). Confirmed via `hostname`/`hostname -s`/`scutil --get ComputerName`
locally that this is one machine whose `hostname -s` value changed (router/DHCP rename), not two machines, and
unrelated to the separately-confirmed-terminated AWS `human-planning` VM (`i-0dd9812a96cdda5dc`, tag
`vm-id=human-planning`).

`slot-git-status-report.sh:173` (`HOSTNAME_SHORT="$(hostname -s ...)"`) stamps whatever `hostname -s` returns as the
fleet-health `host` key on every post. Both the reporter cron and the FF-pull cron were independently confirmed alive
and correctly running every 5 minutes under the new name (crontab entries + live `ps aux` + `/tmp/slot-cron-ff-
pull.501.log` + `/tmp/slot-git-status-report.501.log`, all `host=Mac`, `[ok]`). The separately-flagged `ff:conflict`
badge on every "Mac" slot was investigated and found to be an UNRELATED, correctly-working display artifact (worst-of-
precedence roll-up surfacing a handful of permanently-diverged `.stale-pre-history-rewrite-20260805T112453Z` branches
+ one `unified-trading-ci` upstream mispoint as `conflict`, already known to `verify-slot-host-symmetry.sh` as a
non-alerting soft nit) — not part of this issue, no code change made for it.

Pulling `agent-orchestrator-alerts` via `scripts/dev/slack-read-channel.py agent-orchestrator-alerts 96` confirmed the
operational impact: `MacBook-Pro` re-paged roughly every 15-90 minutes, continuously, from ~2026-08-15 evening through
the moment of this fix, always `git reporter cron: silent for <N>m` with N climbing in step with wall-clock time —
never a single `RECOVERED` bookend, because under the old name it structurally cannot recover.

## Root cause

`agent-orchestrator/server/host_tombstone.py`'s `is_host_tombstoned(host)` is the single gate
(`server/worker_liveness/__init__.py:676`, `if is_host_tombstoned(host): continue`, called from `_git_surfaces_pass`
before either `_maybe_alert_git_staleness` or `_maybe_alert_unpushed_plans`) that stops a dead host from paging
forever — and it also drives the dashboard's `is_tombstoned` skip in `summarise_git_health`
(`server/routes/git_health.py:465`). It offers two paths to `True`: (1) a manual `_KNOWN_TERMINATED_HOSTS` floor, and
(2) a live `aws ec2 describe-instances` lookup gated to `_AWS_HOSTNAME_RE`-shaped hostnames (`^ip-\d+-\d+-\d+-\d+$`).
Both paths are EC2-only by design — the module's own comment: "a laptop hostname ... is never an EC2 instance and
must never be tombstoned" via the AWS path. A laptop that changes its self-reported hostname is therefore permanently
outside both mechanisms: not AWS-shaped (no lookup possible) and not in the manual floor (nobody had a reason to add
it there before this).

## Fix

Generalized the existing manual fail-safe-floor pattern (already used for `_KNOWN_TERMINATED_HOSTS`) with a parallel
`_KNOWN_RENAMED_HOSTS: dict[str, str]` (old hostname → current hostname, for audit) in
`agent-orchestrator/server/host_tombstone.py`, checked in `is_host_tombstoned` alongside the terminated-hosts set —
same "never prune, tombstone-only" contract, no AWS round-trip, no DB write, no VM/operator access needed. Added
`"MacBook-Pro": "Mac"`. Added `test_known_renamed_laptop_host_is_always_tombstoned_without_an_aws_call` to
`tests/test_host_tombstone.py` (mirrors the existing terminated-host test; also asserts the CURRENT hostname `Mac` is
never affected by its own old-name entry). Takes effect fleet-wide within ~2 minutes of landing on
`live-defi-rollout` via the central orchestrator's `ao-self-pull.sh` cron (root cron, every 2min, restarts on HEAD
move) — no manual VM action required.

Considered and declined: pinning the reporter/FF-pull scripts' hostname source (e.g. to `scutil --get ComputerName`,
which is operator-set and stable across DHCP/router changes, instead of `hostname -s`) would prevent this class of
recurrence fleet-wide. Declined for THIS fix because it touches shared cron infrastructure that every laptop and VM
in the fleet runs (`slot-git-status-report.sh`, `slot-cron-ff-pull.sh`) and needs its own review (e.g. Linux VMs have
no `ComputerName` equivalent) rather than being folded into a same-session ghost-host cleanup. If a hostname rename
recurs, the same two-line `_KNOWN_RENAMED_HOSTS` entry resolves it immediately, same as this one.

## Open TODOs

- [x] [INFRA] P2. ✅ **DONE — agent-orchestrator@fb615aba94.** Add `_KNOWN_RENAMED_HOSTS` floor to
      `host_tombstone.py`, entry `"MacBook-Pro": "Mac"`, plus a unit test proving the old name tombstones without an
      AWS call and the current name is unaffected.
