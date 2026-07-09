---
doc_type: plan
title: AO task lifecycle — done-gate, dead-worker resume, preserve-on-handoff + fleet-wide slot commit identity
summary:
  Redesign the AO worker task lifecycle around dirty WIP — a done-API gate that rejects "done" while slot repos are
  dirty (push via QG+quickmerge, or stash + Slack alert); dead-worker respawn that RESUMES the same task in the same
  slot via --resume (no dirty resolution — the WIP is the context); orphan-WIP preserve-commit restricted to the
  done→new-work handoff and fixed to carry the slot·host identity (today it is rejected by the fix-commit-identity hook
  → permanent quarantine → dispatch starvation). Plus fleet-wide slot commit-identity correctness — the hook derives
  slot-N from the RETIRED tab/<op>/<N> branch scheme so every Path-B slot resolves to "main"; fix the derivation, add a
  per-host checker script, and harden the slot-creation paths.
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags:
  [agent-orchestrator, task-lifecycle, dirty-wip, resume, watchdog, autospawn, commit-identity, worktrees, quarantine]
related: [../epics/orchestrator_master.md, ao_dispatch_correctness_regen_reconcile_2026_07_07.md]
created: 2026-07-09
last_updated: 2026-07-09
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 2
locked_by:
locked_since:
depends_on:
supersedes:
superseded_by:
source:
  [operator request 2026-07-09 — AO dispatch-starvation investigation (7 slots dirty-quarantined, queue not draining)]
assigned_role: backend-engineer
drift_direction: advance-code
---

# AO task lifecycle — done-gate, dead-worker resume, preserve-on-handoff + slot commit identity

> **Status: ACTIVE — operator approved 2026-07-09; executing in SLOT 16 (interactive session, claimed + `paused` so
> AutoSpawn never spawns over it). `execution_scope: local-only` — the AO fleet does NOT execute this plan (it patches
> the AO's own spawn/watchdog path).**

## 1. Problem — evidence from the 2026-07-09 investigation

The AO had 7 queued dispatchable tasks, ~8 idle slots, and only 1 task progressing. Root-cause chain (all verified
against live state + the AO's own activity log on the planning VM):

1. **Dirty-quarantine deadlock (the binding constraint).** 7/17 slots (2, 5, 9, 10, 12, 13, 14) carried a dead worker's
   uncommitted WIP. AutoSpawn's pre-spawn resolver tried to preserve it via an auto-commit
   (`server/worktree_clean_check/_orphan.py` `commit_and_push_dirty_repos`, commit at ~line 148), but that commit runs
   **without `--no-verify`** with author `-c user.name="agent-orchestrator (orphan-wip)"` — which the fail-closed
   `unified-trading-pm/scripts/hooks/fix-commit-identity.sh` hook REJECTS (self-heal config + exit 1, expects re-run;
   there is no re-run). Activity log (`slot_dirty_state_resolved`) for every quarantined slot:
   `err='git commit failed: Enforce slot·host commit identity...Failed'`. All repos error → `resolve_dirty_state`
   returns `quarantined` (`_resolve.py:133-142`) → `_do_spawn` refuses to spawn ANY worker over the slot
   (`autospawn.py:1111-1112`) → the slot is dead capacity forever. The quarantine `detail` string falsely blames the
   "FM2 wiped-index/mass-delete guard" — the real error (hook rejection) is only in the per-repo
   `orphan_commits[].error`.
2. **No resume-on-death.** `--resume <claude_session_id>` machinery exists and the session id IS correctly generated at
   spawn (`tmux_spawn.py:927-938`, passed `--session-id` at `autospawn.py:1180`, persisted to
   `SlotRow.claude_session_id` at `autospawn.py:1553-1561`) — but it is only used by the watchdog for a silent-but-alive
   session (G2b, `worker_liveness_watchdog.py:297,397`) and account-failover. A DEAD session with an in-flight task is
   never resumed: AutoSpawn fresh-spawns (new session id), and `tmux_pruner.py:225-228` requeues the orphaned task
   (`status=queued, dispatched_to=None`) for ANY slot. The dead worker's WIP context is abandoned.
3. **Spawn "success" without submission.** `_boot_landed` (`tmux_spawn.py:763-776`) verifies the boot prompt was
   _delivered_ (marker or `[Pasted text +N lines]` placeholder visible), not _submitted_ — a `C-m` swallowed by the
   TUI's bracketed-paste leaves the prompt sitting unsubmitted; the spawn is declared OK; the worker never runs `/boot`,
   never claims, and churns through kicker/watchdog/respawn every ~5 min (observed on slots 4/7/8/11; the kick log's
   `snippet=` is the worker's own unsubmitted input-box text).
4. **Doomed slots eat the spawn budget.** The dirty/branch gate runs inside `_do_spawn` (slow section) AFTER the slot
   consumed a `spawn_budget` unit (`autospawn.py:1461,1493-1528`); `_should_spawn` (:1507) doesn't check dirt. With 7
   quarantined slots cycling 5-min cooldowns, clean idle slots get skipped as `queue_satisfied`.
5. **Slot identity is systematically wrong fleet-wide.** `setup-tab-worktrees.sh:298-300` correctly stamps
   `user.name = "<canon> [slot-<N>·<host>]"` per-worktree at creation. But the enforcement hook
   (`fix-commit-identity.sh:57-58`) derives the EXPECTED label from the branch name — `tab/<op>/<N>` → `slot-N`, else
   `main`. The tab-branch model is RETIRED (Path-B slots sit on `live-defi-rollout`), so the hook expects
   `[main·<host>]` in EVERY slot and actively REWRITES the correct slot identity away on the first commit. This is why
   slot numbers are missing across the planning VM and operator PCs, and why cross-slot commit attribution is broken.

Second sweep (same day, operator-reported `worker_kick_failed` + `autospawn_failed` UI noise) — activity histogram last
500 events (11:27→12:26Z): 62 `autospawn_failed` (61 = the §1.1 dirty-quarantine on slots 2/5/9/10/12/13/14 — same root
cause; 1 = a `tmux session orch-slot-4 already exists` spawn race), 60 `worker_kick_failed`
(`post_kick_classification=frozen` on every one), 45 `autospawn_succeeded`/hr + 44 `slot_boot`/hr = heavy
spawn→boot→vanish churn:

6. **Zombie dispatch — the lone "working" slot is not working.** Task
   `sports_xg_shots_instrument_type_dedup_key_instability-001` is `dispatched_to=3`, SlotRow `status=working`, fresh
   `last_ping` — but slot 3's live pane shows the worker idling ("Boot returned no eligible task … I'm holding idle")
   with `❯ check again` sitting UNSUBMITTED in its input box. The boot resume-branch exists (`slots_worker.py:110-122`
   returns the slot's own `current_task` with `dispatch_reason="resume"`), and heartbeat re-offers it too — but a
   dispatch handed out in a boot/heartbeat RESPONSE has **no ACK/progress deadline**: if the worker freezes without
   acting on the response (slot 3), the task stays `dispatched` forever and nothing reconciles pane-reality against
   DB-state.
7. **Kicks don't land, and nothing escalates.** `_kick_session` (`worker_liveness/__init__.py:220-232`) does raw
   `send-keys <text>` + 1s + `C-m` with NO submit verification (same delivered≠submitted family as `_boot_landed`); 37
   consecutive failed kicks on slot 3 in one hour with zero escalation. The kicker's auto-respawn (`_respawn.py`
   `maybe_auto_respawn_stuck_slot`) (a) SKIPS slots whose DB status is `working` — exactly the zombie state — and (b)
   when it does fire, kills + FRESH-spawns (context lost) instead of `--resume`. `classify_pane`'s spinner regex vs
   past-tense `✻ Worked for Xs` ambiguity is flagged in the code's own comments (`worker_liveness/__init__.py:418-420`).
8. **Liveness-signal integrity.** `last_ping` is written by non-worker paths — `assign_task_to_slot`
   (`state_store/slots.py` dispatch-time bump), the kicker's spinner-observation branch
   (`worker_liveness/__init__.py:437-440`), the respawn path (`_respawn.py:349`) — so a frozen worker can read as alive
   and the watchdog's heartbeat-silence never fires (slot 3: frozen pane, fresh ping).
9. **Unsubmitted-text depositors.** The frozen input boxes hold operator-style instructions (`check again`,
   `file the CLAUDE.md fix as a plan todo`, `check why those 7 tasks are blocked`) — something (main-agent / plan-health
   guidance path) types into worker panes WITHOUT a verified submit, manufacturing the frozen state the kicker then
   fails to clear. A pending-messages outbox already exists (`take_pending_messages`) and is the right channel.

Non-bugs confirmed while sweeping: `idle_blocker_inferred` (17/hr) = the `footystats-mp-complete` prerequisite
legitimately gating one queued task; `plan_health_dispatch_failed` 503s = no-free-slot symptom of the wedge above, not a
separate defect.

## 2. Target task lifecycle (the contract)

```
spawn(slot, --session-id SID, boot prompt)          # SID persisted on SlotRow at spawn
  → worker POST /boot → pick_next_task → task dispatched_to slot
  → worker works …
  ├─ PATH 1 — worker finishes:
  │    worker pushes EVERY touched repo (QG + quickmerge), then POST /done
  │    backend done-gate: check_slot_clean over ALL repos in the slot
  │      • generated-only dirt → auto-restore, proceed
  │      • clean → accept done (existing plan-flip checks unchanged) → slot idle → next dispatch
  │      • dirty → REJECT done (structured 409: repo → files + required action)
  │          worker: important WIP → QG + quickmerge push, re-POST /done
  │                  unimportant  → slot-tagged stash → backend Slack-alerts the stash
  │                                 (slot, task, repo, stash ref, files) → re-POST /done
  └─ PATH 2 — worker dies mid-task (session dead / pane dead / heartbeat-silent past kill):
       task NOT done + slot dirty
         → DO NOT run dirty resolution (no auto-commit, no stash — the WIP is the resumed agent's context)
         → DO NOT requeue the task away from the slot (tmux_pruner leaves dispatched_to intact)
         → respawn SAME slot with --resume SID (same cwd/CLAUDE_CONFIG_DIR) + nudge
           "finish your in-flight task; push via QG+quickmerge; then POST /done"
         → bounded: max 2 resume attempts per death episode → fall back to preserve+fresh (below)
       task NOT done + slot CLEAN → today's behavior (requeue + fresh spawn) is fine.

preserve-on-handoff (the ONLY auto-commit point):
  task is done (or slot has no task) AND leftover dirt exists at next spawn
    → orphan-WIP commit with the SLOT'S OWN [slot-N·host] identity (attribution = owning slot),
      --no-verify (a preservation commit to a wip-preserve/ ref is not a QG boundary; FM2
      wiped-index/mass-delete guard STAYS in code), push wip-preserve/orchestrator-slot-<N>-<sha>,
      realign to origin/<base>, spawn fresh.
```

## 3. Codex SSOTs this plan depends on (read before executing; update in the DOC todo)

- `codex/05-infrastructure/per-tab-worktrees.md` — Path-B slot clones, commit attribution `[slot-N·host]`,
  inherited-dirty-WIP liveness gate.
- `codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` +
  `codex/04-architecture/agent-orchestrator-overview.md` — slot/worker lifecycle, dispatch, watchdog.
- `codex/12-agent-workflow/async-wait-and-poll-discipline.md` — watchdog/monitor verdict discipline (dead vs working
  must be a measured verdict).
- `plans/PLAN_FORMAT.md` §8b — evidence-backed completion for the VERIFY todo.

## 4. Design decisions (locked unless operator objects at review)

- **Done-gate scans ALL repos in the slot dir** (not just task-declared repos) — leftover dirt anywhere blocks done.
  Generated-only artifacts (`restore_generated_artifacts` set) are auto-restored, never a rejection.
- **Resume is scoped to dead + dirty + task-not-done** (operator spec). Dead + clean → normal requeue/fresh path.
- **Resume implies NO dirty resolution on that spawn path** — quarantine/FM2 checks are bypassed for the resume spawn;
  the FM5/FM7 branch-state gate still runs read-only diagnostics but must not block resume (log-only).
- **The stash path is agent-initiated, backend-notified** — slot-tagged stash (`_stash.py` `slot_stash_tag`) so it is
  recoverable per-slot; the Slack alert exists to drive the count of stashes to ~0 over time (root-cause each one).
- **The identity hook stays fail-closed for interactive commits** (self-heal + re-run). Automation (orphan-WIP preserve)
  uses the correct identity + `--no-verify`. The hook's slot derivation moves branch → PATH.
- **`fable-required` / model-tier unchanged** — out of scope.

## 5. Todos

### Phase A — done-API dirty gate (PATH 1)

- [x] [CODE] P0. ✅ agent-orchestrator@5b07bd3 — **Done-gate in the done endpoint** — in
      `agent-orchestrator/server/routes/slots_worker.py` (done handler, ~line 800s): before marking the task done, run
      `worktree_clean_check.check_slot_clean` over every repo in the slot dir (after `restore_generated_artifacts`); if
      dirty → do NOT mark done; return a structured 409
      `{dirty: [{repo, staged, unstaged, untracked}], required_action: "quickmerge-or-stash"}`; task stays `dispatched`.
      Idempotent re-call after cleanup accepts.
- [x] [CODE] P0. ✅ agent-orchestrator@5b07bd3 — **Worker contract** — update `agent-orchestrator/agents/worker.md` (+
      `server/prompts.py` render vars if needed): done preconditions — push every touched repo via QG+quickmerge BEFORE
      `/done`; on 409 → important WIP → quickmerge it; unimportant → slot-tagged
      `git stash push --include-untracked -m slot-<N>-…`, report the stash in the retry payload; never delete/reset WIP.
- [x] [CODE] P0. ✅ agent-orchestrator@5b07bd3 — **Boot prompt bans ask-permission turns** — observed (slot 12, 07:50Z):
      a freshly-spawned worker finished its memory-housekeeping preamble and ENDED ITS TURN with _"should I proceed with
      STEP 0 … and then /boot?"_ — an interactive Claude that ends a turn is inert, so the spawn is wasted until a kick
      lands. Harden the worker boot prompt + `agents/worker.md`: NO human watches this pane — never end a turn with a
      question or permission-ask; STEP-0 reads and the CLAUDE.md memory-reset are silent preamble, not discussion; the
      FIRST turn must reach `/boot` (or arm the idle heartbeat loop when no task, as slot 4 correctly does) in the SAME
      turn. Evidence gate — sampled fresh spawns reach `/boot` on turn 1 with zero permission-ask turns.
- [x] [CODE] P1. ✅ agent-orchestrator@5b07bd3 — **Stash-notify** — done-retry payload carries
      `stashed: [{repo, stash_ref, files}]`; backend logs `slot_stash_on_done` activity + fires a Slack notification
      (`server/notifications/`) with slot, task id, repo, stash ref, file list — so every stash is visible and
      root-caused (target = zero stashes steady-state).

### Phase B — dead-worker resume (PATH 2)

- [x] [CODE] P0. ✅ agent-orchestrator@5b07bd3 — **Dead+dirty+not-done classifier → resume-pending** — in
      `server/worker_liveness_watchdog.py`: when a slot's session is dead (tmux gone / pane dead) with `current_task`
      not done AND the slot dir is dirty, mark the slot resume-pending (persisted on SlotRow) instead of the plain
      killed→fresh path. Measured verdict only (session liveness + task row), per async-wait discipline.
- [x] [CODE] P0. ✅ agent-orchestrator@5b07bd3 — **Resume-respawn path** — AutoSpawn (or the watchdog respawn) spawns
      the resume-pending slot with `resume_session_id = SlotRow.claude_session_id` (`tmux_spawn.spawn` already supports
      it — same cwd + CLAUDE_CONFIG_DIR keyed by session name); task stays `dispatched_to` the slot; `resume_nudge` =
      "you died mid-task <id>; your WIP is intact in the worktree — finish it, push via QG+quickmerge, then POST /done".
      **Skip `resolve_dirty_state` entirely on this path** (`autospawn.py:1091-1112` gate becomes lifecycle-aware).
- [x] [CODE] P1. ✅ agent-orchestrator@5b07bd3 — **Bound the resume loop** — max 2 resume attempts per death episode
      (counter on SlotRow, reset on task done); on exhaustion fall back to Phase-C preserve + fresh spawn + requeue
      (mirrors the watchdog G2b single-resume pattern, `worker_liveness_watchdog.py:297`).
- [x] [CODE] P1. ✅ agent-orchestrator@5b07bd3 — **tmux_pruner respects resume-pending** —
      `server/tmux_pruner.py:225-228` currently requeues a dead slot's task (`status=queued, dispatched_to=None`); it
      must leave a resume-pending slot's task dispatched (or requeue pinned `target_slot=<N>, affinity=high` until
      attempts exhaust).
- [x] [CODE] P1. ✅ agent-orchestrator@5b07bd3 — **Spawn success = SUBMITTED, not delivered** — `_boot_landed`
      (`server/tmux_spawn.py:763-776`) additionally verifies the prompt left the input box (spinner/first-output
      present, or the input line no longer holds the marker; optionally confirm the worker's `/boot` POST within T).
      Retry the submit (`C-m`) once before failing the spawn. Without this, died-vs-working classification (Phase B
      trigger) is untrustworthy.

### Phase B2 — wedged-ALIVE workers (the slot-3 zombie class; 2nd sweep findings §1.6-1.9)

- [x] [CODE] P0. ✅ agent-orchestrator@5b07bd3 — **Dispatch-ACK contract** — a task handed out in a boot/heartbeat
      response records `offered_at`; if the worker shows no ack/progress within T (progress event, spinner, or context
      growth), the dispatch is reconciled: task auto-returns to `queued` (pinned `target_slot` per Phase B) +
      `slot_dispatch_unacked` activity. Kills the zombie-dispatch class (slot 3: `dispatched` >1h, worker idle in-pane,
      zero progress events).
- [x] [CODE] P0. ✅ agent-orchestrator@5b07bd3 — **Kick-failure escalation → kill + resume** — after K consecutive
      `worker_kick_failed` on a live session (or dispatched-task-no-progress past T), stop kicking: kill the wedged
      session and respawn via the Phase-B `--resume` path (context preserved). Fix `maybe_auto_respawn_stuck_slot`
      (`_respawn.py:141-266`): (a) it currently SKIPS `status=working` slots — the exact zombie state; (b) when it fires
      it must `--resume` when a task is in flight, not fresh-spawn.
- [x] [CODE] P1. ✅ agent-orchestrator@5b07bd3 — **One verified-submit helper for every pane injection** — extract a
      shared `submit_to_pane(session, text)` (send-keys `-l`, verify the input box cleared / spinner appeared, single
      retry) and use it in `_kick_session` (`worker_liveness/__init__.py:220-232`), `tmux_spawn._submit`, and any
      messaging path; also disambiguate `classify_pane`'s spinner regex vs past-tense `✻ Worked for Xs` (its own comment
      flags it) so working/frozen/idle verdicts are truthful. Evidence gate — `worker_kick_failed` with
      `post_kick=frozen` drops to ~0 in the activity stream.
- [x] [CODE] P1. ✅ agent-orchestrator@5b07bd3 — **Liveness-signal integrity** — only worker-originated signals
      (`/boot`, `/heartbeat`, `/progress`, `/done`) plus a GENUINE active-spinner observation may refresh `last_ping`;
      audit + fix the non-worker writers (`assign_task_to_slot` dispatch bump, `_respawn.py:349`, spinner branch
      false-positives). Regression test — a frozen-pane slot with a stale worker trips heartbeat-silence within the
      watchdog window.
- [x] [CODE] P1. ✅ agent-orchestrator@5b07bd3 — **Worker messaging goes through the outbox, not raw tmux typing** —
      find the depositor(s) of the unsubmitted input-box instructions (`check again`, `stop the loop` on slot 1,
      `check on the poll loop status` on slot 4 — live 12:40Z survey; `file the CLAUDE.md fix as a plan todo`).
      Server-side audit (12:40Z) already clears the server: the ONLY free-text pane typer is `_kick_session` (fixed
      strings) — `/api/slots/{id}/message` correctly uses the outbox — so the depositors are OUTSIDE the server
      (main-agent Bash `tmux send-keys` / operator dashboard terminals). Route them through the pending-messages outbox
      (`take_pending_messages`, drained at boot/heartbeat) or the verified-submit helper; add the ban to
      `agents/main.md`; optionally add a pane-deposit detector (frozen-with-text that matches no kick text →
      `pane_text_deposited` activity) so future depositors self-identify. NOTE — an unsubmitted deposit is LOST OPERATOR
      INTENT (slot 1's `stop the loop` never executed), not just noise.
- [x] [CODE] P2. ✅ agent-orchestrator@5b07bd3 — **Spawn-vs-respawn TOCTOU** —
      `autospawn_failed: tmux session orch-slot-4 already exists` — re-check `has_session` inside the spawn (or
      serialize respawn ownership between kicker-respawn and AutoSpawn); treat an existing live session as a benign
      skip, not a failure.
- [ ] [CODE] P1. **Context lifecycle for long-running agents (main + review)** — operator 2026-07-09: these sessions
      ideally run for days, which the model isn't designed for; today the only control is honor-system self-compact
      guidance (`agents/main.md` "run /compact at >~70%") while the backend's pressure signal (`derive_context_pressure`
      low/medium/high/thrashing, `CompactionRow` detection — `state_store/slots.py:352`) is observed but never ACTED on.
      Build the backend-driven two-tier policy, **COOPERATIVE-FIRST** (operator 2026-07-09: never compact an agent
      mid-work; a single pane-snapshot "looks idle" is untrustworthy — §1.7's classifier ambiguity, background shells,
      check-then-send race). **Tier 1 — proactive guided compact** at `context_used_pct` ≥ ~45-50% (≈450-500k on [1m];
      pct-based so 200k workers get the same policy if ever enabled). Delivery — NO new per-tick flag check (operator: a
      1-min loop must not grow a compact banner): the keeper enqueues a normal OUTBOX message ("context at N% — run
      /compact at your next natural checkpoint, focus: keep operating loop / watchlist / unanswered messages / in-flight
      items; drop tick-by-tick history"), which the main/review loops ALREADY drain every cycle (main.md STEP 2A/2B;
      workers at boot/heartbeat) — zero added overhead. Execution — `/compact` is a CLIENT-side command, not a model
      tool, so the agent runs it by SELF-INJECTION: from a Bash call, `tmux send-keys` the /compact line into ITS OWN
      session (it knows `#S`), then END the turn — mid-turn typed input QUEUES and executes the moment the turn ends, so
      "runs when free" holds by construction; ack via `compact_done` next tick. Ship this as a sanctioned helper
      (`scripts/agent/self-compact.sh`, built on the verified-submit helper — the raw-send-keys ban exempts only this
      instrument). HARD GUARD (live-fired 2026-07-09): the helper MUST require `$TMUX`/`$TMUX_PANE` set and target its
      OWN pane id — `tmux display-message -p '#S'` on a NON-tmux shell silently returns the most-recently-active session
      (observed: an interactive VSCode session resolved to `orch-slot-1` = the REVIEW agent), so a blind fallback would
      compact a DIFFERENT agent; abort loudly when not inside tmux. FORCED fallback only past a deadline (unacked 2
      ticks / ~45 min) and only on a MEASURED multi-signal idle verdict: pane `idle` debounced across ≥3 observations
      over ~60s + NO child processes under the pane shell (`pgrep -P <pane_pid>` — catches "1 shell still running") +
      empty input box → inject via the verified-submit helper + confirm the compact ran; log `proactive_compact` vs
      `forced_compact`. (Race note: a `/compact` submitted during an active turn QUEUES and runs at the next turn
      boundary — worst case is deferral, not corruption.) Hard never-force: spinner, running shells, non-empty input
      box, or `thrashing` (escalate to recycle instead). Client-side auto-compact stays underneath as the final safety
      net. **Tier 2 — checkpoint-recycle** after 2 proactive compacts OR 24h (immediately on `thrashing`): cooperative
      too — agent writes its checkpoint (watchlist + open items → `main-agent-checkpoint.md` + `last_msg`) and **EXITS
      ITSELF** (no kill; dead session → keeper's normal respawn with the boot prompt referencing the checkpoint — same
      voluntary-exit pattern account rotation already uses, `slots_worker.py:153` "exiting, new session spawning").
      Fresh model state beats an N-times-compacted session for loop agents whose durable state is already external
      (state.db / activity / inbox scratch). Cost rationale — a 20-min-tick agent is past the 5-min prompt-cache TTL, so
      EVERY tick re-reads the whole conversation at full input price; lean context is directly cheaper + faster. Workers
      excluded (/boot-per-shippable-unit already bounds them; Phase B covers death).

### Phase C — preserve-on-handoff only + identity-correct orphan commit

- [x] [CODE] P0. ✅ agent-orchestrator@5b07bd3 — **Lifecycle-gate the pre-spawn dirty resolution** — `autospawn.py`
      `_do_spawn`: run `resolve_dirty_state` ONLY when the slot has no in-flight task (previous task done or none) —
      i.e. the done→new-work handoff; the resume path (Phase B) bypasses it.
- [x] [CODE] P0. ✅ agent-orchestrator@5b07bd3 — **Fix the orphan-WIP commit** —
      `server/worktree_clean_check/_orphan.py:97-163`: drop the `-c user.name="agent-orchestrator (orphan-wip)"`
      override; commit with the slot clone's OWN worktree identity (`<canon> [slot-N·host]` — stamped by setup; re-stamp
      defensively if absent) so attribution tracks the owning slot; keep predecessor agent id + slot in the body and add
      an `Orphan-WIP: slot-<N>` trailer; add `--no-verify` (preservation commit to `wip-preserve/` is not a QG boundary;
      FM2 wiped-index/mass-delete guard stays in code at `_wiped_index.py`).
- [x] [CODE] P2. ✅ agent-orchestrator@5b07bd3 — **Truthful quarantine detail** — `_resolve.py:133-142`: the blanket
      detail string `"all dirty repos refused (FM2 wiped-index/mass-delete guard)"` masked the hook failure for days;
      surface the first per-repo error line in the outcome `detail`, the `slot_dirty_state_resolved` activity, and the
      Slack quarantine alert.
- [x] [CODE] P2. ✅ agent-orchestrator@5b07bd3 — **Stop doomed slots eating spawn budget** — move a cheap dirty/branch
      pre-check into `_should_spawn` (`autospawn.py:1507`) or exclude failed spawns from the budget so quarantined slots
      no longer starve clean idle slots into `queue_satisfied` skips (`autospawn.py:1493-1528`).

### Phase D — slot commit identity, fleet-wide

- [ ] [SCRIPT] P0. **Fix the hook's slot derivation** — `unified-trading-pm/scripts/hooks/fix-commit-identity.sh:57-58`:
      derive `slot-<N>` from the worktree PATH (`…/.tabs/<N>/<repo>` → `slot-N`; main workspace → `main`), NOT from the
      retired `tab/<op>/<N>` branch scheme (Path-B slots sit on `live-defi-rollout`, so today every slot resolves to
      `main` and the hook REWRITES the correct stamped identity away). Host derivation
      (`ORCHESTRATOR_VM_ID`/`VM_NAME`/`laptop`) unchanged.
- [ ] [SCRIPT] P0. **Per-host identity checker** — new `unified-trading-pm/scripts/dev/check-slot-commit-identity.sh`
      (lifecycle marker; permanent): for the main workspace + every `.tabs/<N>/<repo>` on THIS host, verify
      `user.name`/`user.email` (worktree config aware) match the expected `<canon> [slot-N·host]` — sharing the SAME
      derivation as the hook (single SSOT — source a shared helper, don't duplicate the sed); `--fix` stamps
      (`extensions.worktreeConfig` + `git config --worktree`); exit non-zero on drift; runnable on the planning VM, the
      human-planning VM, and operator laptops.
- [ ] [SCRIPT] P1. **Harden slot creation** — `scripts/dev/setup-tab-worktrees.sh`: after clone/config (:291-325), run
      the checker in verify mode as the final step; ensure repos added later to an existing slot dir also get stamped
      (idempotent re-run covers a partial slot).
- [ ] [CODE] P1. **AO-side clone/repair paths stamp identity** — `agent-orchestrator/server/worktree_setup.py` (and any
      other AO code path that creates or repairs a slot clone) stamps the same worktree identity at creation so a
      backend-provisioned slot is never identity-less.

### Phase E — tests, runtime verification, docs

- [ ] [TEST] P1. **Unit tests** (AO `tests/unit/`): done-gate 409 payload + accept-after-clean; classifier matrix
      (dead×dirty×done → resume vs requeue vs preserve); resume spawn passes `--resume <sid>` + skips dirty resolution;
      bounded-resume fallback; pruner leaves resume-pending tasks; orphan commit uses slot identity + `--no-verify`
      (hook-rejection regression test); `_boot_landed` submission check.
- [ ] [VERIFY] P0. **Runtime verification on the planning VM** — (a) the 7 quarantined slots (2, 5, 9, 10, 12, 13, 14)
      clear through the fixed preserve path: WIP lands on `wip-preserve/orchestrator-slot-<N>-<sha>` refs with
      `[slot-N·host]` authorship, slots realign + spawn; (b) backlog drains (queued→dispatched→done transitions in
      `/api/state`); (c) one induced dead-worker (kill a test worker mid-task) → resume-respawn with the SAME session id
      finishes the task through the done-gate; (d) `check-slot-commit-identity.sh` green on the planning VM AND the
      operator PC; (e) the slot-3 zombie dispatch reconciles (task resumed or requeued + completed) and
      `worker_kick_failed(post_kick=frozen)` drops to ~0/hr in the activity stream. Evidence (activity-log excerpts,
      backlog counts, commit SHAs, script output) recorded in the Progress Log — run it, don't read it.
- [ ] [DOC] P1. **Post-phase codex audit** — update `codex/05-infrastructure/per-tab-worktrees.md` (commit attribution —
      PATH-based slot derivation; checker script; orphan-WIP identity),
      `codex/04-architecture/agent-orchestrator-overview.md` (task lifecycle states — done-gate, resume-on-death,
      preserve-on-handoff), and the CLAUDE.md one-liners if the shipped contract changed; SUPERSEDED-banner anything
      invalidated.

## 6. Out of scope (tracked elsewhere / follow-ups)

- Changing the identity hook's fail-closed semantics for interactive commits — intentionally unchanged.
- The `147 = 139 done + 8 open` backlog-summary presentation on the dashboard — cosmetic, not a defect.
- `idle_blocker_inferred` on `footystats-mp-complete` — a real prerequisite doing its job, not a defect.
- `plan_health_dispatch_failed` 503s — symptom of the frozen-session wedge; expected to clear with Phase B2 (verify in
  the VERIFY todo, don't fix separately).

## 7. Progress Log

- 2026-07-09 ~15:15Z — **Phases A + B + B2 (6/7) + C SHIPPED**: `agent-orchestrator@5b07bd3` (quickmerge → LDR; QG
  green, 1137 tests incl. 12 new lifecycle tests in `tests/test_task_lifecycle_done_gate_resume.py`). The commit itself
  carries the fixed attribution `ikennaigboaka [slot-16·planning]` — first production proof of the Phase-D identity
  chain. Notes: (a) B2 "pane-deposit detector" sub-item was optional — skipped (the main.md ban + the server-side audit
  shipped); (b) the B2 context-lifecycle todo is the remaining open Phase-B2 item; (c) Phase-D todo "AO-side
  clone/repair paths stamp identity" is satisfied BY DELEGATION — `server/worktree_setup.py` bootstrap/reset invoke
  `setup-tab-worktrees.sh`, whose provision path now ends with `check-slot-commit-identity.sh --fix --slot N`. Live
  findings folded in: the planning VM's GLOBAL `slotIdentity.name` was itself label-polluted ("ikennaigboaka
  [slot-0·human-planning]") — the concat source of every mangled name on this host; the shared lib now SANITIZES canon
  (strips " [label·host]") and adds `git config --global slotIdentity.host` as a host source for interactive shells (env
  still wins for fleet processes); this host repaired (`slotIdentity.name=ikennaigboaka`, `slotIdentity.host=planning`).
  Checker audit of this host: 419 repos, 117 identity-drifted (fix scheduled in VERIFY).
- 2026-07-09 — Plan drafted from the live investigation (quarantine deadlock chain, resume gap, identity-hook stale
  derivation confirmed with file:line + activity-log evidence). Awaiting operator review → flip `status: active`.
- 2026-07-09 13:46Z — Operator approved; `status: active`. Execution claimed SLOT 16: `POST /api/slots/16/pause`
  (status=paused — AutoSpawn/watchdog/escalation skip it) + `POST /api/slots/16/claim-interactive` (12h claim
  `slot16-interactive-20260709-134626-5f29`). Slot-16 clones stamped `ikennaigboaka [slot-16·planning]` (AO clone had
  EMPTY identity; PM clone had `[slot-0·human-planning] [main·planning]` in `.git/config.worktree` — live proof of the
  §1.5 hook-mangling this plan fixes; root PM clone is `[slot-0·human-planning] [main·laptop]`, same class). Code work
  happens in `.tabs/16/{agent-orchestrator,unified-trading-pm}`; plan-file flips from the root PM clone.
