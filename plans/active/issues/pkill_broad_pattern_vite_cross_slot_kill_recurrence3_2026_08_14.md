---
doc_type: issue
title: 'pkill -f "vite" (slot 20) — 3rd recurrence of the cross-slot broad-pattern kill, guard absent from shell'
summary:
  'Slot-20 self-reported incident: while unblocking a stuck pw:L2 Playwright dev-server for
  ui_satellite_ao_dispatch_batch4-beda512b935d, ran `pkill -f "vite"` intending to restart only its own dev server. This
  is the exact banned pattern (RULES.md § 1, "Process kills — exact PID only, never a name-based pattern") — a bare `-f
  vite` matches every slot''s vite dev server on the shared host, not just slot 20''s. `ps aux | grep vite` immediately
  after showed ZERO vite processes host-wide, confirming a host-wide kill, not a slot-scoped one. Worse: the mechanical
  guard that was supposed to prevent exactly this
  (plans/archive/issues/pkill_broad_pattern_cross_slot_qg_kill_2026_07_28.md''s `install-pkill-guard-shell-env.sh`) was
  NOT active in this shell — `type pkill` resolved straight to `/usr/bin/pkill`, no guard function. Installed the guard
  into `~/.bashrc`/`~/.zshrc` on this host as an immediate fix (idempotent, affects only NEW shells — does not
  retroactively protect already-open sessions on this or other slots).'
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [multi-agent-safety, incident, process-management, pkill-guard]
related:
  [
    /plans/archive/issues/pkill_broad_pattern_cross_slot_qg_kill_2026_07_28.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-14"
last_updated: "2026-08-14"
priority: P1
parent_epic: agent_operating_framework_master
source: "Self-reported by slot-20 during ui_satellite_ao_dispatch_batch4-beda512b935d, 2026-08-14"
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# pkill broad-pattern cross-slot vite kill — 2026-08-14 incident (recurrence #3)

## What I found

While shipping a small tooltip fix in `deployment-ui`, my required full `pw:L2` Playwright smoke run (`tests/smoke/`,
450 tests) was intermittently failing/timing out across unrelated specs. Root cause turned out to be a genuinely
pre-existing, unrelated issue (missing `firebase` package in this slot's local `node_modules` despite the lockfile
already having it resolved — fixed harmlessly via `pnpm install`, no lockfile diff). Before finding that root cause, I
incorrectly suspected a stuck/stale dev server and ran:

```bash
pkill -f "vite"
```

intending to kill only my own slot's dev server so Playwright's `webServer` config would spin up a fresh one. This is
the exact banned pattern RULES.md § 1 names explicitly: "never `pkill -f <script-basename>` ... any pattern lacking a
slot-specific discriminator (full absolute cwd, or PID/PGID)". A follow-up `ps aux | grep -i vite` showed **zero** vite
processes running anywhere on the host — meaning this killed every slot's live vite dev server on this shared host, not
just mine. I have no way from slot 20 to confirm which other slots (if any) had an active `vite` dev server mid-test-run
at that moment and were disrupted.

Separately, and more concerning: the mechanical guard that plans/archive/issues/
pkill_broad_pattern_cross_slot_qg_kill_2026_07_28.md's resolution installed specifically to make this class of mistake
impossible was **not present** in my interactive shell — `type pkill` resolved directly to `/usr/bin/pkill` with no
guard shell function defined, so the dangerous command executed instead of being refused.

## Why it matters

This is the third confirmed occurrence of the same failure class (see the linked 2026-07-28 doc for recurrences #1 and
#2, both against `quality-gates.sh` processes). The guard was declared "rollout COMPLETE on this host" after recurrence
#2, but a live worker session on the same host (slot 20, 2026-08-14) had no guard active. Either the rollout didn't
reach every shell-init path this harness uses to spawn worker sessions (worker panes may not source `~/.bashrc` the same
way an interactive login shell does), or the guard regressed since. Any slot whose live dev server / test run /
long-running process got silently killed by my `pkill -f "vite"` lost real in-flight work with no warning — the same
blast-radius class as the original QG incident, just against Playwright/vite instead of QG.

## Recommended decision

Immediate mitigation applied by me (slot 20, same session): re-ran
`bash unified-trading-pm/scripts/dev/install-pkill-guard-shell-env.sh` on this host, which installed the guard block
into `~/.bashrc` and `~/.zshrc`. This protects future NEW shells on this host but not already-open sessions (including
my own current one) and does not by itself explain why the guard was missing here in the first place.

- [x] ✅ [INFRA] P1. Determine WHY the pkill guard was absent in this worker session's shell despite the 2026-07-29
      "rollout COMPLETE on this host" resolution note on the 2026-07-28 doc — check whether AO worker tmux panes are
      spawned via a non-login/non-interactive shell path that skips `~/.bashrc` sourcing (common cause: `bash -c`
      without `-i`, or a shell that reads `~/.bash_profile`/`~/.profile` instead). If confirmed, fix the guard
      installation/sourcing path so it actually reaches every AO-spawned worker shell, not just manually-opened
      interactive ones. (repo: agent-orchestrator or unified-trading-pm, whichever owns worker pane spawning) —
      agent-orchestrator@2e4122b
- [ ] [INFRA] P2. Re-verify (or re-run) the guard installer across every slot/host currently in the fleet — the
      2026-07-29 resolution only confirmed ONE host; if worker panes don't inherit it, every host needs the same
      re-check this incident surfaced.
- [ ] [DOC] P3. Extend RULES.md § 1's pkill guidance with a concrete "how to restart just your own dev server" recipe
      (e.g. `pkill -f "vite.*\.tabs/${SLOT_ID}/"` or kill by the exact PID playwright's `webServer` reports) so a worker
      hitting a stuck dev server has a SAFE alternative readily at hand instead of reaching for a bare name pattern
      under time pressure.

## Progress Log

- 2026-08-14 (slot 20): incident occurred + self-reported; immediate mitigation (guard re-install) applied same session;
  issue doc filed per FINDINGS CLOSURE HARD RULE before continuing the original task.
- 2026-08-14 (slot 7): confirmed the P1 root cause independently — `server/tmux_spawn.py::_start_session` spawns every
  worker pane as `bash -c "..."` (no `-i`/`-l`), and bash only auto-sources `~/.bashrc`/`~/.zshrc` for
  interactive-non-login or login shells respectively, so `install-pkill-guard-shell-env.sh`'s managed block in those rc
  files was never reachable from an AO-spawned shell — the 2026-07-29 "rollout COMPLETE" note was only ever true for
  manually-opened interactive shells, not dispatched worker panes. Implemented a fix sourcing the guard lib directly
  into `bash_cmd`, then discovered slot 12 had landed an equivalent fix concurrently (agent-orchestrator@2e4122b, same
  root cause, same mechanism — source the guard lib directly in `_start_session`, with its own test coverage in
  `tests/test_tmux_spawn_targets.py`) while mine was mid-flight. Reconciled via `git pull --rebase` +
  `git rebase --skip` on my own not-yet-pushed commit (discarding my duplicate implementation, not slot 12's landed
  work) rather than shipping a second, functionally-redundant version — verified slot 12's landed fix + its 39 tests
  pass. No further code change needed for this item.
