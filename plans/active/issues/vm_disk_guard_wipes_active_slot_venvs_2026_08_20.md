---
doc_type: issue
title: vm-disk-guard reclaims the venv of ACTIVE slots — its idle test never matches, so every slot's venv is swept
summary: >-
  `vm-disk-guard.sh` deletes `.tabs/<N>/*/.venv` for every slot it judges idle, and its idle test is "a live
  `orch-slot-<N>` tmux session exists". On the current orchestrator VM no `orch-slot-*` tmux session exists at all, so
  EVERY slot reads as idle and EVERY slot's venv is swept — including a slot with a `quality-gates.sh` run in flight.
  Disk sits at 79-81% against the guard's 80% threshold, so this trips on most 2-hourly passes. Measured live on slot 7
  on 2026-08-20; the failure surfaces as a confusing QG red (missing sqlalchemy dialect + a bogus coverage failure)
  that looks like a code regression and is not one.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [agent-orchestrator, disk-guard, venv, quality-gates, slot-worktrees, false-red, tmux-liveness]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch24_2026_08_18.md,
    /plans/archive/issues/slot_venv_duplication_disk_pressure_2026_06_29.md,
    /plans/archive/2026_08/issues/fleet_venv_drift_after_pull_no_resync_2026_08_11.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /codex/06-coding-standards/quality-gates.md,
  ]
created: 2026-08-20
author: worker slot 7 (data_engineering, ao_satellite_ao_dispatch_batch24 item 4)
assigned_vm: planning
execution_scope: orchestrator-agent
parent_epic: orchestrator_master
priority: P1
assigned_role: infra
resolved_by:
locked_by:
source:
  [
    agent-orchestrator/scripts/vm-disk-guard.sh,
    /var/log/vm-disk-guard.log,
    /plans/active/ao_satellite_ao_dispatch_batch24_2026_08_18.md,
  ]
context_scope:
  [
    agent-orchestrator/scripts/vm-disk-guard.sh,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /codex/06-coding-standards/quality-gates.md,
    /plans/active/ao_satellite_ao_dispatch_batch24_2026_08_18.md,
  ]
---

# vm-disk-guard reclaims the venv of ACTIVE slots

## What I found

`agent-orchestrator/scripts/vm-disk-guard.sh` (threshold-gated, `THRESHOLD=80`) reclaims regenerable data when `/` is
at or above 80%. One of the things it reclaims is idle-slot worktree venvs, added for the 2026-06-28 disk-exhaustion
incident. Its own comment states the intent precisely — it is meant to skip "a slot whose venv a QG may be mid-use".

The idle test it actually uses is tmux-session presence:

```bash
active="$(runuser -u "${owner}" -- tmux list-sessions -F '#S' 2>/dev/null \
  | grep -E '^orch-slot-[0-9]+$' || true)"
for slotdir in "${tabs}"/*/; do
  n="$(basename "${slotdir}")"
  grep -qx "orch-slot-${n}" <<<"${active}" && continue   # running — leave it
  find "${slotdir}" -maxdepth 2 -type d \( -name '.venv' -o -name '.venv-workspace' \) -prune -exec rm -rf {} +
done
```

**On this VM no `orch-slot-*` tmux session exists at all.** `tmux ls` returns only an unrelated
`kimi_precompact_test` session, while a genuinely working slot-7 session reports `AO_SESSION_NAME=orch-slot-7` with
`TMUX` unset (it is not tmux-hosted). The guard's `active` list is therefore empty, `grep -qx` never matches for any
`N`, and the loop deletes the venvs of all 16 slots unconditionally. The script's own fallback comment ("if the query
can't be made ... the slot is treated as idle — acceptable ... since a venv only re-builds") is load-bearing here in a
way it was not designed for: it is not a rare degraded case, it is the steady state.

Measured on 2026-08-20 (slot 7):

- **Every** repo in `.tabs/7/` (25 of them) had no `.venv`; slots 5, 6, 8 and 9 likewise. The **root clone**
  `unified-trading-system-repos/agent-orchestrator/.venv` was intact — consistent with a sweep scoped to `.tabs/`.
- `/var/log/vm-disk-guard.log` shows it firing on most recent passes, because usage hovers right at the threshold:
  ```
  2026-08-20T00:00:01Z vm-disk-guard: / at 81% (>= 80%) — vacuuming regenerable caches
  2026-08-20T08:00:01Z vm-disk-guard: / at 80% (>= 80%) — vacuuming regenerable caches
  2026-08-20T12:00:01Z vm-disk-guard: / at 80% (>= 80%) — vacuuming regenerable caches
  ```
- The venv also disappeared **a second time**, outside a logged guard window, while a QG run was in flight. I did not
  establish what removed it that time and am deliberately not attributing it to the guard without evidence — see the
  open todo below.

**How it presents to a worker** (this is the expensive part — the symptom does not look like the cause):

1. First `quality-gates.sh` run aborts cleanly: `❌ quality gate ABORTED — no usable .venv/bin/python`. Recoverable and
   reasonably self-describing.
2. If the sweep lands *during* a run, site-packages is deleted underneath the running interpreter and pytest instead
   dies with `sqlalchemy.exc.NoSuchModuleError: Can't load plugin: sqlalchemy.dialects:sqlite` at fixture setup for
   every DB-touching test, **plus** `ERROR: Coverage failure: total of 65 is less than fail-under=72` — because
   hundreds of tests erroring at setup execute no lines. Both read as a code regression in the worker's own diff. They
   are not.

After `uv sync`, the identical unchanged commit passed the full gate: 5272 passed / 2 skipped backend + 469 dashboard.

## Prior art — checked, and this is NOT a duplicate of either

Two resolved venv issues sit nearby; neither covers this mechanism, and the distinction is the whole point:

- `/plans/archive/issues/slot_venv_duplication_disk_pressure_2026_06_29.md` (resolved) is the ANCESTOR of this bug, not
  a duplicate: it is the disk-pressure incident whose fix ADDED the idle-slot venv reclamation to `vm-disk-guard.sh` in
  the first place. This issue is a new failure mode OF that fix — the reclamation is correct in intent, its idle
  predicate is what does not hold.
- `/plans/archive/2026_08/issues/fleet_venv_drift_after_pull_no_resync_2026_08_11.md` (resolved) is about venv DRIFT —
  a venv that EXISTS but holds versions behind `uv.lock` after a pull, with no re-sync counterpart to the 5-min ff-pull
  cron. Confirmed distinct: that doc never mentions `vm-disk-guard` (zero matches), and drift is not deletion.
  **It matters anyway, because it is the wrong diagnosis this bug invites**: both present as "the python suite broke,
  `uv sync` fixed it", so a worker who has seen the drift issue will reasonably conclude drift and move on. That is
  most likely what happened on items 2 and 3 of
  `/plans/active/ao_satellite_ao_dispatch_batch24_2026_08_18.md`, each of which recorded a stale-venv `uv sync` detour.
  A drift check cannot catch this one: at the moment of failure there is no venv to compare against the lock.

## Why it matters

- **It silently blocks the shipping pipeline for every slot worker.** A green `quality-gates.sh` tree is the commit
  contract, and quickmerge `--agent` refuses without a sentinel matching HEAD. A worker whose venv is swept cannot ship
  at all until it re-syncs.
- **It burns worker turns on a false red.** The presenting failure is a plausible-looking test/coverage regression, so
  the honest response is to investigate one's own diff first. `ao_satellite_ao_dispatch_batch24_2026_08_18` items 2 and
  3 each recorded a "stale `.venv`, fixed via `uv sync`" detour and diagnosed it as staleness; item 4 hit it again.
  That is plausibly three recurrences on a single plan, re-diagnosed from scratch each time.
- **The guard's stated safety property does not hold.** It explicitly intends not to touch a slot whose venv a QG may
  be mid-use, and today it cannot honour that for any slot.
- It is self-perpetuating at the margin: every swept venv is rebuilt by the next worker via `uv sync`, pushing usage
  back toward the threshold for the next pass.

## Recommended decision

Fix the guard's liveness signal rather than raising the threshold — the threshold is doing its job, the idle test is
not. A slot's real liveness is already tracked in the orchestrator's own state (`SlotRow.status` / `last_ping`, which
the watchdog already uses), and a QG run in progress is directly observable (the QG ledger lock, or a live process
under the slot's absolute worktree path). Any of those is a sounder signal than the presence of a tmux session name
that nothing currently creates.

Explicitly **not** done here: creating an `orch-slot-<N>` tmux session to make the guard skip the slot. That would
suppress the symptom, but the AO backend keys worker liveness, one-shot `send-keys` nudges and TmuxPruner reaping off
exactly those session names, so fabricating one risks a non-existent pane being treated as a live worker. That is an
operator call, not a worker's.

## Todos

- [x] ✅ [INFRA] P1. Replace `vm-disk-guard.sh`'s tmux-only idle test with a signal that reflects real slot liveness —
      e.g. query the orchestrator's own `SlotRow.status`/`last_ping` (the watchdog's existing definition), and/or skip
      any slot with a live process under its absolute worktree path (`pgrep -f ".tabs/<N>/"`, the slot-scoped form
      `/codex/05-infrastructure/per-tab-worktrees.md` already sanctions). Must fail SAFE — an unanswerable liveness
      query should now mean "leave the venv alone", the opposite of today's fallback, since the measured cost of a
      wrong sweep is a fleet-wide QG outage. (repo: agent-orchestrator)
      **DONE `agent-orchestrator@616e15a4ca`** — a slot is now LIVE when (a) an `orch-slot-<N>` tmux session exists
      (kept for hosts that run tmux-hosted workers) OR (b) ANY live process has its CWD inside the slot's absolute
      worktree path, read via `/proc/<pid>/cwd` (`pgrep -f` cannot see a claude worker whose cmdline is just
      `claude --session-id <uuid>`). FAIL-SAFE inverted: an unreadable process table now means LEAVE every venv, not
      sweep. Verified: functional test against the live `/proc` (slots 1/7/14/21/29 all judged LIVE, a nonexistent
      slot judged IDLE) + `bash -n`; full QG green (5272 passed/2 skipped backend + 469 dashboard vitest, coverage
      86.13%), sentinel==HEAD `616e15a4`, landed + ancestry-verified on `origin/live-defi-rollout`.
- [x] ✅ [INFRA] P1. Make the guard refuse to sweep a venv that is in use REGARDLESS of the slot's idle verdict — a
      belt-to-the-suspenders check for the mid-run deletion that produced the `NoSuchModuleError` +
      false-coverage-failure signature above (e.g. honour the QG ledger lock `quality-gates.sh` already takes).
      (repo: agent-orchestrator)
      **DONE `agent-orchestrator@087f1723ca`** — added a `_slot_venv_in_use()` belt, a second independent check after
      `slot_has_live_process`: refuses to sweep a slot when any live process's COMMAND LINE references the slot's
      absolute worktree path (`pgrep -f "<slot>/"`), catching a venv still in use even when the CWD scan reads the slot
      idle — complements (does not duplicate) `616e15a4`'s CWD-based liveness signal. Verified: `bash -n` + functional
      test against live `/proc`; full QG green (5272 passed/2 skipped backend + 469 dashboard, coverage 86.13%),
      sentinel==HEAD `087f1723`, landed + ancestry-verified on `origin/live-defi-rollout`.
- [ ] [INFRA] P2. Make `quality-gates.sh` detect a venv that vanished or was truncated MID-RUN and abort with the same
      explicit message it already prints when the venv is missing UP FRONT, instead of surfacing it as
      `NoSuchModuleError` + a coverage-ratchet failure. A worker should never have to reverse-engineer a disk sweep
      from a sqlalchemy dialect error. (repo: agent-orchestrator)
- [ ] [INFRA] P2. Determine what removed slot 7's venv the SECOND time on 2026-08-20, outside any logged
      `vm-disk-guard` window (between a successful `uv sync` and the QG run that followed it). Either attribute it to a
      known mechanism or confirm the guard ran unlogged — do not assume it is the same cause. (repo: agent-orchestrator)
- [ ] [INFRA] P2. Drop the tmux-session-name liveness signal from `vm-disk-guard.sh` entirely, relying solely on the
      already-shipped `/proc/<pid>/cwd` + command-line liveness checks (`agent-orchestrator@616e15a4ca` /
      `@087f1723ca`). Per D139 ruling (2026-08-22): drop tmux — the shipped signal covers both worker types;
      fabricated sessions risk confusing send-keys nudges and TmuxPruner. (repo: agent-orchestrator)
- [ ] [INFRA] P3. Bring baseline `/` usage down far enough that the guard is genuinely exceptional rather than firing
      on most 2-hourly passes — it has run at 80-81% on 3 of the last 4 logged passes, so today the fleet is
      effectively running with venv reclamation always-on. (repo: agent-orchestrator)

## Progress Log

- **2026-08-21 (interactive session, slot 15) — recurred TWICE in one session, AFTER the
  2026-08-20 liveness fix (`agent-orchestrator@616e15a4ca`) shipped, and correlated with a
  separate near-data-loss.** `agent-orchestrator/.venv` in slot 15 vanished mid-session
  twice (~17:00 and ~18:50 UTC), each time surfacing as `quality-gates.sh` aborting with
  "no usable .venv/bin/python" rather than a false-red — the shipped fix's `abort, don't
  silently mis-green` behavior worked correctly; only the underlying sweep-an-active-slot
  root cause is not fully closed. Fixed live both times with `uv sync --frozen`, no code
  change. Adds a THIRD data point to the open "second-sweep, no logged pass" todo below,
  now from an INTERACTIVE session (not an AO-dispatched worker) — worth checking whether
  the shipped liveness signal (`/proc/<pid>/cwd` under the worktree) actually covers an
  interactive Claude Code session's process tree the same way it covers a spawned
  worker's, since this is a genuinely different process shape than the slot-7/slot-21
  cases the fix was built against.

  **Separately, and possibly connected**: between the two venv-vanish incidents, a
  `chore(orphan-wip)` auto-commit (AO's `DirtyStateResolution.COMMIT_AND_PUSH` pre-spawn
  dirty-state gate) fired on this same slot at 17:04:58Z, and the branch was then reset to
  `origin/live-defi-rollout` — orphaning that commit and 4 files of in-progress work
  (recovered from the reflog: `git checkout 530af5d3 -- <paths>`, no permanent loss, but a
  close call). Not confirmed causally linked to the venv sweep — noted here rather than
  filed separately since both point at the same underlying question this doc's `[OPERATOR]
  P2` todo below already asks: does an interactive slot correctly register as "live" to
  AO's own liveness/dirty-state machinery, or does it look indistinguishable from an idle
  worker slot to both the disk-guard AND the dirty-state gate?

- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)
- **2026-08-20 (infra, slot 21)**: Fixed the P1 liveness signal — `vm-disk-guard.sh` no longer sweeps a slot whose
  worktree hosts any live process (tmux-session check retained as a secondary signal + `/proc/<pid>/cwd` read as the
  primary, with the process table treated as authoritative), and fails safe (unreadable `/proc` ⇒ leave ALL venvs).
  Shipped `agent-orchestrator@616e15a4ca`. Env note: this slot's first QG run failed only on a stale
  `dashboard/node_modules` (missing declared `@vitest/coverage-v8`) — a pre-existing env staleness (a bash-script
  change cannot influence dashboard deps), fixed via `npm --prefix dashboard install`, then full QG green. Same
  env-fix class the sibling items in `/plans/active/ao_satellite_ao_dispatch_batch24_2026_08_18.md` recorded.
- **2026-08-22 — ruling D139 (Disk-guard liveness signal)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch authority,
  AUTONOMOUS_AGENT_RULES rule 2): Drop tmux — the shipped signal covers both worker types; fabricated sessions risk
  confusing send-keys nudges and TmuxPruner. Source: /plans/active/issues_corpus_completion_dispatch_2026_08_21.md
  ledger.
