---
doc_type: codex-ssot
title: Async-wait & poll discipline — how an agent waits for things to complete _well_
summary:
  SSOT for how an agent waits on async work it cannot finish synchronously — watch a climbing PROGRESS metric not just
  the terminal condition, short-interval-first then expand, treat a stall as STOP-and-diagnose, prefer harness
  completion over polling; codifies watcher-coverage (terminal verdict on every exit path, measured-not-assumed, kill -0
  liveness) and the no-over-watch / no-sawtooth rule.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: [orchestrator, monitoring, self-healing, observability, runbook, verification]
related:
  [
    /codex/05-infrastructure/vm-tarball-deployment.md,
    /codex/12-agent-workflow/canonical-plan-flow.md,
    /codex/08-workflows/ci-cd-flow.md,
  ]
created: 2026-06-03
authoritative_for: [agent async-wait and poll cadence discipline, background-task watcher coverage]
referenced_by:
  [/codex/04-architecture/cross-venue-prediction-arb-detection.md, /codex/06-coding-standards/sub-agent-workflow.md]
owner:
last_reviewed: 2026-08-12
code_refs:
---

# Async-wait & poll discipline — how an agent waits for things to complete _well_

> **owner**: cross-cutting (agent-behaviour) · **cadence**: every long async wait · **verifier**:
> `cursor-configs/CLAUDE.md` § "Background-task honesty" + this doc · **last_executed**: 2026-06-03
>
> SSOT for HOW an agent should wait on async work it cannot finish synchronously — CI runs, the LDR→staging→SIT→main
> promotion cascade, VM jobs, deploys, backfills, a peer agent's PR. Composes with (does not replace) the
> **Background-task honesty** rule (never report "done" before seeing the real exit/output) and the **No fire-and-forget
> VM launch** rule. Codified 2026-06-03 after a frozen `ci_status` cascade was caught in ~6 min by short-interval
> polling that a 16-min "watch for done" monitor would have wasted.

## The failure mode this prevents

An agent kicks off async work (or waits on the fleet), then either (a) **passively waits** on a single long monitor that
only watches a _terminal_ condition (`state == done`), or (b) **reports progress optimistically** before the signal is
real. Both burn the wall-clock window and hide stalls: a monitor that only knows "done vs not-done" cannot tell
**slowly-progressing** from **dead-stuck**, so a silent jam (a broken writer, a missing dep, a credit outage) eats the
whole window before anyone looks.

## The discipline (HARD RULES)

1. **Watch a PROGRESS metric, not just the terminal condition.** Pick a number that climbs as the work advances (repos
   `≥STAGING_GREEN`, PRs merged, rows backfilled, files migrated) and log it each tick. A **flat** metric across several
   ticks = a **STALL**, which is an action signal, not a longer wait. "Done" alone is blind to stalls.

   **1a. VALIDATE THE METRIC BEFORE YOU TRUST A ZERO OR A FLAT READING (HARD RULE).** Rule 1 is necessary but not
   sufficient: it assumes the metric _can_ move for the operation you are actually running. Prove that first — otherwise
   a broken monitor is **indistinguishable from a broken job**, and rule 1 fires on the monitor's own defect and argues
   for killing healthy work. Two measured failures, same root cause, different mechanisms (2026-07-19, sports features
   re-run):

   | metric                                          | why it could NEVER signal progress                                   |
   | ----------------------------------------------- | -------------------------------------------------------------------- |
   | object count on a bucket from a launcher's hint | the bucket **404s**; `gcloud storage ls … \| wc -l` yields 0 forever |
   | count of `day=` partitions                      | the run **overwrites in place**, so the partition count cannot grow  |

   The first read `0` for 20 minutes on a VM that was writing fine; the second read a flat `3462` across three ticks
   while 288 objects/window were landing. Both looked exactly like a stall.

   Before arming, answer: **"what reading would this show if the job were healthy, and is that different from what it
   shows if the job is dead?"** If the answer is the same, the metric is useless. Concretely: resolve buckets via
   `resolve_bucket_name` (never string-interpolate an env-split name, and never trust a launcher's printed hint — verify
   the path returns objects at all); prefer **creation-time counts in the run window** over inventory counts, because
   inventory is blind to overwrite; and take a baseline reading at arm time so "flat" is measured against a number you
   know was live.

   **1b. A CRASH-RESTART LOOP CAN LOOK LIKE PROGRESS IN A SHORT WINDOW — check that the metric's VALUES advance across
   restarts, not just that log lines keep appearing (2026-08-07, `mtds-backfill-odds-1`).** The mirror image of 1a: not
   a metric that can't move, but one that moves for a genuinely wrong reason. A wrapping chunk-loop that respawns a
   fresh subprocess per unit of work (per-league, per-chunk) can crash that subprocess (OOM, unhandled exception) and
   restart it from the same durable checkpoint every time — each restart does REAL work before dying again (skip-fasts
   through already-covered dates, writes a genuine row or two), so a narrow-window check sees moving log lines, a
   plausible resource sample, and a real write, and concludes "healthy." Only a WIDER-window re-check (here, ~28 min
   later) revealed the exact same date/chunk being reprocessed identically — the underlying process had OOM-killed and
   restarted ~10 times, zero net progress. **Rule:** when the checkpoint mechanism itself is unproven (no
   `PROGRESS.json` / no monotonic counter visible yet — see the self-deleting-VM rule below), don't conclude health from
   log activity alone; diff the actual date/chunk/id VALUES between two checks spaced by the process's own expected
   unit-of-work duration, not just confirm lines are still being written. Full incident:
   `plans/active/issues/mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md`.

2. **Short-interval first, then EXPAND.** When the cadence is unknown, start at **~30–45 s** ticks to (a) confirm the
   mechanism actually moves and (b) catch a stall fast. Once you have ≥2 ticks of real progress, **lengthen** the
   interval (cache-window aware: stay <5 min to keep the prompt cache warm while actively polling; go to 20–30 min only
   for genuinely-idle long waits). Do **not** open with a 15–20 min monitor on unproven work — a stall then costs the
   whole interval.

3. **A stall → STOP and DIAGNOSE the blocker; never wait it out.** A stuck pipeline does not un-stick itself. On a flat
   metric, read the failing run's log (`gh run view --log-failed`), find the broken link (a failing writer, a
   `[skip ci]`/bot-token-no-trigger PR head, a dep not yet green, an out-of-credits gate), fix it, then resume. Most
   "the cascade is slow" is actually "the cascade is jammed."

4. **Prefer the harness completion signal over polling for harness-tracked work.** `run_in_background` Bash / sub-agents
   / workflows auto-re-invoke you on exit — rely on that, don't burn calls polling them. **Poll only genuinely
   external/untracked state** (GitHub Actions runs, remote VM jobs, deploys, another repo's PR) — and there, apply rules
   1–3.

   **4a. The harness's reported exit code is the LAST pipeline stage's, not necessarily your command of interest's
   (2026-07-27 K1/K2 migration).** A backgrounded command piped through `grep`/`tail`, or wrapped in a compound block
   ending in an always-succeeding step (`... ; echo done`), reports the exit status of that final stage — a real command
   failure upstream can still surface as "exit code 0." Several completion notifications this session read `exit code 0`
   on runs whose actual work had failed partway. For any consequential verdict (a migration/delete run's real success,
   not a routine check), verify the ACTUAL terminal marker directly from the durable log/output file content
   (`grep -c 'DONE\|rc=0'`, the script's own printed summary) — never trust the harness's exit-code summary alone when
   the backgrounded command was piped or compound.

5. **Monitors watch the RIGHT signal with a generous fallback timeout** — the correct log path / API field + an explicit
   done/terminated condition, plus a max-iteration cap so the monitor never exits inconclusively and forces a
   re-investigation. Exit the loop EARLY on the key transition (so you act promptly) rather than always running the full
   duration.

6. **Stay productive across the wait; never idle-burn the window.** While async work runs, do independent,
   non-conflicting work (read-only analysis, other repos, doc/plan flips) — but never work that destabilises the thing
   you are waiting on (e.g. re-pushing a branch whose PR's CI must settle to merge).

## Canonical poll loop (bash, external state)

```bash
# Watch a PROGRESS metric; short ticks; exit early on the key transition; capped + timed out.
for i in $(seq 1 12); do
  prog=$(<query the progress counter>)          # e.g. repos ≥ STAGING_GREEN
  key=$(<query the key terminal/transition>)     # e.g. PR state == MERGED
  echo "[$i $(date +%H:%M:%S)] progress=$prog key=$key"
  [ "$key" = "DONE" ] && { echo ">>> transition reached"; break; }
  sleep 40                                        # short first; widen once progress is confirmed
done
# If progress was FLAT across ticks → do NOT relaunch a longer monitor → diagnose the blocker now.
```

## Wake sources — `ScheduleWakeup` and `run_in_background` DO NOT COMPOSE (HARD RULE, codified 2026-06-16)

There are two ways the harness re-invokes a dormant agent, and **they are mutually exclusive in practice — pick exactly
ONE per wait. Never set a `ScheduleWakeup` as a "fallback" alongside an active `run_in_background`/tracked task.**

- **`run_in_background` task completion = RELIABLE.** A `run_in_background` Bash, sub-agent, or workflow re-invokes you
  **when it exits** — this is the dependable wake signal. The robust pattern for a long unattended wait is a **single
  background _orchestrator_** that does the waiting **and** the work and exits only when fully done:
  `( while ps -p $A >/dev/null; do sleep 60; done; launch B; while ps -p $B; do sleep 60; done; echo DONE ) &` via
  `run_in_background`. The harness fires the moment it exits — no timer needed.
- **`ScheduleWakeup` = BEST-EFFORT, in-session, NOT a guaranteed OS alarm.** It is the `/loop` self-pacing timer.
  **Empirically (2026-06-16): a `ScheduleWakeup` set as a safety-net while a `run_in_background` task was active NEVER
  FIRED — 34 min past its scheduled time the agent was still dormant** (only the operator's message woke it). The
  tracked background task was correctly progressing and would have re-invoked on completion, but the timer was
  **shadowed by it** — a pending tracked task is the harness's active wake source, and the standalone timer is not
  independently honoured while it is pending (and won't fire at all if the session is idle/asleep, since it is
  in-session not OS-level).
- **THE RULE.** (a) If a tracked background task is driving the wait → **rely on its completion; do NOT also schedule a
  wakeup** (it gives false "I'm covered" confidence and silently never fires). (b) Use `ScheduleWakeup` ONLY when **no
  tracked task** is in flight — i.e. self-pacing your own `/loop` ticks or polling genuinely **external/untracked**
  state (a remote CI run / VM job the harness can't see). (c) If something **MUST** resume regardless of session state,
  make it a tracked background task that exits on the condition — never trust the timer alone. (d) Need a periodic
  checkpoint during long tracked work? Build it **into** the orchestrator (exit at the checkpoint, or write a progress
  marker), not as a separate `ScheduleWakeup`.

Symptom that you hit this: you scheduled a wakeup "as a fallback," ended the turn, and the wakeup time passed with no
re-invocation. Root cause is almost always a concurrent `run_in_background` task shadowing the timer. Fix: drop the
redundant wakeup; let the task's completion drive you (or restructure as a single orchestrator task).

## Composes with

- **Background-task honesty** (`CLAUDE.md` § Agent behavior) — the truthfulness half; this doc is the cadence half.
- **No fire-and-forget VM launches** (`/codex/05-infrastructure/vm-tarball-deployment.md`) — T+10min verify is a poll.
- **CI verification after every push** (`CLAUDE.md`) — `gh run list` + `gh run view --log-failed` are the poll tools.
- **Plans run to actual completion** — "operationally shipped" is verified by polling the real signal to completion, not
  assumed from a green smoke test.

## Watcher coverage — never infinitely wait (HARD RULE, codified 2026-06-10)

Incident (2026-06-10, slot-3): a `run_in_background` until-loop watched for three repos' content to appear on `main`. It
died at its Bash timeout with **zero output** — no verdict, no notification semantics — and the session read the silence
as "still waiting". Worse, the awaited mechanism **could never fire**: the staging→main drain iterates
`staging_commits`, which only sit-gate's lock step writes, so non-breaking staging merges were invisible to it (bug #11,
`cicd_contract_hardening_2026_06_01.md`). Any watcher duration would have failed. Two distinct sins:

1. **Coverage sin** — the watcher only matched the success condition. Rules:
   - Watch the TERMINAL set, not the happy path: `state != OPEN` (merged/closed/failed all land), `status == completed`
     (then read the conclusion), never `until <success-marker>` alone.
   - PRINT an explicit verdict line on every exit path (`SUCCESS: …` / `FAILED: …` / `DEADLINE: …`) — an empty output
     file must be impossible. The verdict line is what the resuming agent reads; silence is indistinguishable from
     "still running".
   - Size the loop's own deadline INSIDE the harness timeout (e.g. a counter that prints `DEADLINE` and exits 0 before
     the kill), so expiry is a reported outcome, not a silent kill.

2. **Phantom-mechanism sin** — waiting on an automated hop nobody fires. Rules:
   - Before arming any wait >5 min on a pipeline hop, **name the mover**: `rg` the trigger chain (which workflow /
     `repository_dispatch` / cron advances this state?). "The automation handles it" without a named workflow + trigger
     is a diagnosis task, not a wait.
   - One deadline = ONE expected-cadence interval of the named mover (a `*/15` cron gets ≤2 ticks ≈ 30 min; a
     dispatch-driven hop gets one dispatch-plus-runtime). On expiry: STOP, diagnose the mover (`gh run list` — did it
     even fire?), never re-arm the same watcher.
   - When the mover turns out not to exist, that is a FINDING (file it per Findings Triage) — the wait converts into a
     fix or a sanctioned manual fallback, as bug #11 did (per-repo staging→main PRs).

3. **False-conclusion sin — a verdict the watcher never MEASURED (codified 2026-06-17).** Incident: a watcher's terminal
   line was `case "$pr81" in MERGED*) echo "RESULT: PR#81 MERGED — lock released";;`. `PR#81 MERGED` was a
   genuinely-true measurement, but `— lock released` was a **hardcoded string stapled onto the success echo** — the
   watcher never read the lock. It conflated "the proxy I watched reached its state" with "the whole chain completed".
   They were different events: the PR merged into **staging**, while the breaking-cascade `staging_status.locked` flag
   was a SEPARATE state still `True` ("SIT running"), gated on a downstream SIT the PR-merge said nothing about. The
   session reported "lock released"; the lock was still held. Rules:
   - **The verdict line must be DERIVED from measuring the real terminal state, never a pre-decided interpretation of a
     proxy signal.** If the goal is "lock released", the terminal check reads the lock flag (`grep -q 'locked=False'`),
     not a different signal you _believe_ implies it. If the goal is "fix on main", grep the fix on `main` — don't infer
     it from a staging-PR merge.
   - **Name the end-state, then measure THAT.** "PR merged", "staging green", "SIT passed", "lock released", "content on
     `main`" are distinct checkpoints in one pipeline — a watcher proves only the checkpoint it literally queries. Echo
     only what you measured: `RESULT: PR#81=MERGED (lock + main NOT yet verified)`, not `RESULT: … — lock released`.
   - **No editorial adjectives in the echo.** Every clause after the colon must correspond to a variable the loop
     actually read this iteration. If you didn't query it, you may not assert it — downstream (and the operator) read
     the verdict line as ground truth.

4. **Self-matching liveness sin — the death check matches the watcher's OWN process (codified 2026-06-19).** Incident
   (slot-1): a `run_in_background` until-loop waited for a detached `nohup python3 _ens_persist.py &` model-training to
   finish, with the failure branch `if ! pgrep -f _ens_persist.py >/dev/null; then echo DIED; break; fi`. But the
   watcher's own bash argv literally contains `_ens_persist.py` (in that very `pgrep` line), so
   `pgrep -f _ens_persist.py` returned the **watcher's own PID** → the check was always "alive" → the death branch could
   NEVER fire. A real OOM crash of the training would have been invisible; the watcher would have hung until its
   timeout, only ever exiting via the success marker (`meta.json`). The bug surfaced because a manual `ps` of the
   matched PID showed **0% CPU + 1.2 MB RSS** — impossible for a pandas/lightgbm worker, the tell that the match was a
   wrapper bash, not the worker. Rules:
   - **The liveness/death check must not be able to match the watcher itself.** `pgrep -f <pat>` / `ps aux | grep <pat>`
     match against full command lines, including the watcher's own (and any sibling shell whose argv contains `<pat>`).
   - **Prefer EXACT-pid liveness: `kill -0 <PID>`** (no string matching at all). Capture the real worker PID once —
     `PID=$(ps aux | grep "[p]ython3 _ens_persist.py" | awk '{print $2}')`, the `[p]` bracket-trick excluding the grep
     line itself — and **sanity-check it's the worker** (a real ML worker is >100 MB RSS and >100% CPU; a 0%/tiny-RSS
     match is the `nohup`/wrapper bash, the wrong PID). Alternatives: `pgrep -f pat | grep -v $$`, or match a marker the
     target emits that the watcher never names.
   - **Race-guard the death verdict:** after `kill -0` fails, `sleep` a few seconds and **re-check the success marker**
     before declaring failure — the worker may exit and write its marker in the same tick
     (`if ! kill -0 $PID; then sleep 4; [ -f meta.json ] && continue; echo FAILED; break; fi`).
   - **A `nohup … &` detached process is NOT a harness-tracked task** — nothing auto-wakes you on its exit; it needs a
     separate `run_in_background` pid-liveness watcher. Better: launch the long worker ITSELF with `run_in_background`
     (not `nohup &`) so its own exit is the tracked wake, and the watcher is only for a worker you cannot relaunch.

5. **`run_in_background` alone does not make a long job immune to a session kill (codified 2026-07-28,
   `plans/active/issues/nohup_detached_background_process_killed_by_orphan_reap_2026_07_27.md`).** A worker background-
   monitored a multi-hour GCS enrichment backfill via harness-native `run_in_background` (the correct fix for the
   `nohup`-detachment/`orphan_reap` trap above) but went **>25 minutes without a `/progress` heartbeat** while doing
   local-only bash progress checks. The orchestrator's `WorkerLivenessWatchdog` read the slot as stale and triggered
   `kill_session` — which (correctly, by design — see `_reap_pane_tree`/`tmux_spawn.py`) SIGTERMs the whole pane's
   descendant process tree BEFORE the actual `tmux kill-session`, killing the in-flight backfill as collateral even
   though it was properly parented and would have been immune to `orphan_reap`. Confirmed via
   `journalctl | grep 'kill_session(orch-slot-<N>)'` at the death timestamp — a DIFFERENT log signature from
   `orphan_reap sweep: ... KILLED`, so don't assume the earlier fix's root cause repeats; check which mechanism fired.
   **Rule: heartbeat cadence (`/progress` every ≤8-10 min, per worker.md's Heartbeat HARD RULE) is the BINDING
   constraint for ANY active long-running background task, independent of how well-parented the process itself is** —
   `run_in_background` fixes the orphan-reap failure mode, it does NOT exempt you from the heartbeat rule while you
   monitor it. If the work will run longer than one heartbeat window, plan the check-in cadence around the heartbeat
   requirement, not around how often the underlying job's own progress changes.

6. **Self-restarting supervisor + harness `run_in_background` is the standard pattern for a multi-hour LOCAL (non-VM)
   resumable background migration/backfill on a shared slot host (codified 2026-07-31,
   `plans/active/issues/footystats_migration_bg_workers_killed_externally_2026_07_28.md`).** Two DISTINCT kill
   mechanisms were confirmed on this workspace's shared hosts, hitting different weight classes — don't assume a single
   fix covers both:
   - **`nohup ... & disown` (or `setsid`-detached) dies in a fixed ~1-3 minutes, independent of host load.** Confirmed
     across repeated attempts at wildly different load levels (load 22 through load 49, one even at LOW load
     `1.39 2.05 3.09`) — this fits a fixed-duration, session/cgroup-boundary reap of nohup-detached processes, not a
     load-triggered OOM kill. Relaunching the identical work directly under the harness's own tracked
     `run_in_background` (no `nohup`/`disown` at all) survived well past the same ~1-3 minute window and ran healthily
     for 90+ minutes before eventually succumbing to a genuine, severe resource-exhaustion event — roughly **10x more
     durable, not immune**.
   - **A genuinely heavy job (e.g. a full `quality-gates.sh` run, or the same lightweight script under sustained
     100%-swap host pressure) CAN still be killed under `run_in_background`** — confirmed at host loads of 62-325 (on a
     16-core host) and swap 87-100% used, `status: "failed"`/`"killed"`/`"stopped"`, exit code 144, zero traceback. This
     is a DIFFERENT failure mode from item 5 above (that one is the `WorkerLivenessWatchdog` reaping a heartbeat-stale
     PANE); this one is genuine host-level resource exhaustion (OOM-killer-class) that item 5's heartbeat fix does not
     touch.
   - **Rule for any multi-hour LOCAL background migration/backfill**: (a) never `nohup ... & disown` — launch the work
     directly under the harness's `run_in_background` instead, which moves the typical failure window from minutes to an
     hour-plus; (b) wrap it in a self-restarting supervisor loop (`while ! success; do relaunch; done`, capped retries)
     keyed off a resumable checkpoint/`--resume-log`, itself run under `run_in_background`, so a kill from EITHER
     mechanism above is auto-recovered without a fresh agent turn having to notice and manually relaunch — this requires
     the underlying work to be CAS-idempotent/resumable, not a prerequisite this pattern can create on its own; (c) the
     checkpoint/resume-log file MUST live on the repo worktree's real disk, never `/tmp` — this workspace's shared hosts
     often mount a small (~2GB) `tmpfs` at `/tmp` that another slot's own temp usage can fill, corrupting a mid-write
     checkpoint with an `OSError: No space left on device` that looks like this same incident class at a glance but is a
     distinct, already-understood failure mode (disk-full, not a clean kill — it leaves a real traceback); (d) on a
     confirmed severe-contention host state (load 100+, swap >80% used), back off and wait for real recovery before
     retrying rather than blindly retrying into the same wall — swap-used% recovers faster and more directly than the
     5/15-min load average, which lags by design and can still read "elevated" well after swap has actually cleared.

Composes with: Poll cadence + stall-intervention (above) — a flat metric and a silent watcher are the same smell;
Background-task honesty (`CLAUDE.md`) — "no output yet" ≠ "finished" ≠ "still running", and "proxy reached its state" ≠
"chain completed", until a verdict line says which from a real measurement.

## Don't over-watch + no-sawtooth (codified 2026-06-21)

**Root cause of the recurring "operator finds me asleep" — it is NOT a wake-mechanism failure.** A tracked
`run_in_background` task's completion reliably auto-re-invokes the agent (verified 2026-06-21: the completion
notification fired on time; the operator had simply pinged 1 min before a 12-min watcher finished). The real defect is
the agent **manufacturing dormancy windows**, two banned patterns:

1. **Over-watching.** Arming a long (10-min+) watcher to "prove" a metric that is ALREADY visibly moving. Incident
   2026-06-21: a 12-min enrichment watcher was armed to confirm a fetch count that had already climbed 274→2760 by the
   2nd (~90s) check. The climb was obvious in two ticks; the remaining ~10 min were pure needless dormancy. **Rule:**
   confirm a climbing metric in **≤2 quick (~90s) checks**, conclude, and move on — never arm a long watcher to re-prove
   something already visible.

2. **Sawtooth.** Chaining many SHORT watchers (arm 5-min → wake → check → arm another 5-min → …). Each short watcher
   leaves a fresh dormancy gap the operator pings into, and if any re-arm is skipped or a watcher exits inconclusively,
   the loop dies silently → permanent dormancy until a human ping. **Rule:** for a genuinely long unattended wait
   (multi-day backfill, operator-gated credit/quota top-up) where there is **no autonomous code work left**, arm **ONE
   long event-driven monitor** in a single tracked task that: (a) polls at an interval matched to how slowly the watched
   state changes (hours for a multi-day backfill, not 5 min); (b) watches **ALL** actionable conditions in one place
   (stall / OOM / crash / the external unblock returning / completion); (c) exits — waking the agent — ONLY on an
   actionable event or completion. The agent then wakes on SIGNAL, not on a timer it must keep re-arming.

3. **Manage the expectation.** When the remaining work is genuinely just "wait on operator action + slow external rate,"
   SAY SO explicitly — name exactly what wakes the agent and what is the operator's action — instead of implying
   continuous active work. Don't fake liveness; an honest "nothing more to do autonomously, monitoring, here's the one
   signal I'm waiting on" beats a sawtooth of short watchers that reads as flaky.

Composes with the Watcher-coverage rule above (terminal verdict on every path; verify the awaited mechanism exists).

## Self-deleting VM/job — monitor must read exit_code, not just RUNNING-count (HARD RULE, codified 2026-06-22)

Backfill and batch VMs launched with `VM_SHUTDOWN_ON_COMPLETION=true` **self-delete on exit whether they SUCCEEDED
(exit 0) or CRASHED (exit 137=OOM / any other non-zero)**. A monitor that only watches the RUNNING set and treats a VM
leaving as "completed/drained" is **BLIND to mass failures**.

**Incident (2026-06-22):** 3 sports backfills OOM-died with exit 137, self-deleted, and the drain-only monitor read 14→1
as healthy completion — no wake fired. Coverage was actually 0% with 75k+ `attempted_failed` rows.

**RULE:** a backfill monitor MUST, per VM:

1. Read the **persisted GCS `run.log`** for the terminal `exit_code=<n>` line — this file **survives self-delete** (it
   is written to GCS before the VM destroys itself). Wake on any `137` / non-zero exit code.
2. Cross-check the manifest `attempted_failed` / `captured` counts — never infer success from "the VM is gone."
3. **Wake condition = `exit_code != 0 OR captured did not climb`**, not merely `RUN == 0`.

## HUNG process — monitor MUST watch LOG-MTIME ADVANCEMENT (codified 2026-06-22)

A backfill VM can sit `RUNNING` with no exit yet make zero progress for hours — the exit_code and RUNNING checks both
show "healthy" while the work is entirely stuck.

**Incident (2026-06-22):** Transfermarkt + FootyStats VMs hung 6.5h on an unbounded HTTP call — alive, exit_code absent,
RUNNING. An exit-code + RUNNING monitor never woke; only a human spot-check caught it.

**RULE:** the monitor's progress signal MUST include **log mtime advancement**. A frozen mtime past a generous threshold
(≥45 min) = HANG → WAKE.

- The GCS-tee'd `run.log` **LAGS** the on-VM log by minutes; for the authoritative mtime, SSH-read `/tmp/vm-exec-*.log`
  directly on the VM.
- The underlying bug behind such hangs is almost always an outbound HTTP/scrape call with **no `timeout=`** and no
  per-shard cancellation wrapper. Fix: `asyncio.wait_for(coro, timeout=N)` at the per-shard level so the stall is
  cancelled → caught → the loop continues. Never let an unbounded outbound call become a VM-wide hang.

Both rules above compose with § "Watcher coverage" (terminal verdict on every exit path, verified mechanism before
arming).

## Dispatched sub-agent is NOT a reliable wake — arm your OWN heartbeat watchdog (HARD RULE, codified 2026-06-24)

When you delegate critical UNATTENDED work to a background sub-agent and go quiet, the sub-agent's completion is your
wake **ONLY IF it completes**. A sub-agent that **dies silently** (rate-limit at startup / crash / API error) or
**hangs** sends NO completion notification. The sub-agent's internal monitor wakes the sub-agent, not you. You get
**ZERO wake** and go dormant indefinitely until the operator pings.

**Incident (2026-06-24):** a post-quota-reset ramp driver was dispatched at 00:00 UTC and died silently before launching
anything. The main loop went dormant 4.5h, wasting the day's fresh API-Football quota. The operator found it inactive
mid-morning — same class as every "operator finds me asleep" incident.

**RULE:** in the SAME turn as any sub-agent dispatch, ALSO arm YOUR OWN independent `run_in_background` **heartbeat
watchdog** that:

1. Polls the **real ground-truth signal** (VMs RUNNING / quota being consumed / the metric climbing) — NOT the
   sub-agent's liveness.
2. Reaches a **TERMINAL verdict + EXITS** (waking you) on done/problem **OR after a hard ≤30-min heartbeat REGARDLESS**
   — so you wake on signal OR on a guaranteed cadence, whichever comes first.
3. Prints an **explicit verdict line** on every exit path (done/problem/heartbeat) — silent expiry is banned.
4. Is **re-armed on each wake** until the work is verifiably complete, then stood down.

**Banned:** "quiet until it lands" with a dispatched sub-agent as the sole wake source.

The ≤30-min re-invoke cost is trivial compared to a multi-hour dormancy + wasted quota. This is the redundant backstop
that a single "dispatch and rely on sub-agent completion" pattern is missing.

**SCOPE of the ≤30-min figure (codified 2026-08-12, see incident below) — it is for UNBOUNDED/unknown-duration work, NOT
a KNOWN multi-hour job.** This rule was codified against the 2026-06-24 quota-ramp incident, where the sub-agent's own
expected runtime was unknown/short and a silent early death was the risk. It does NOT mean "re-invoke a fresh sub-agent
turn every ≤30 min for the life of the job" — for a job with a DOCUMENTED expected duration (e.g. any
`vm-launcher-runbook.md` category, which states per-launcher durations from ~15 min to 1-6+ hours), a chain of ≤30-min
sub-agent re-arms is the wrong pattern: each re-arm is a full sub-agent turn round-trip, and each one is a fresh
opportunity for the "resumed sub-agent ends its turn, reads as finished to the parent" failure below to silently stall
the chain — exactly what a multi-hour job maximizes the odds of hitting repeatedly. **For a job with a known/ documented
expected duration, use § "Don't over-watch + no-sawtooth"'s "ONE long event-driven monitor" pattern instead**, sized to
that duration (poll interval ≈ 10-20% of expected duration, floor ~5 min, no fixed 30-min re-arm-forever ceiling) — a
single tracked `run_in_background` loop that reads GROUND TRUTH directly (VM RUNNING state

- `run.log` progress/mtime + exit_code, not the sub-agent's self-report) and exits only on a real terminal state. This
  converts N required round-trips (one per ≤30-min tick, compounding failure risk each time) into ONE.

**Incident, 2026-08-12 (this exact conflict, live):** a sub-agent dispatched to launch + monitor a
`canonical-migration-tradfi-*` VM (documented 1-6h duration class) followed the ≤30-min-heartbeat rule literally — armed
a series of short (10-30 min) watchdogs, each correctly self-reporting and re-arming for several rounds, but each also
requiring the parent to notice its "completed" notification and manually resend a continuation. On one round the chain
went quiet with no further notification until the OPERATOR had to prompt ("surely run by now") — the exact "operator
finds me asleep" class this whole doc exists to prevent, hit specifically because a multi-hour-class job was being
watched with a short-cycle-reset pattern designed for a short/unknown-duration one.

Composes with § "Watcher coverage" (terminal verdict every path) + § "Don't over-watch + no-sawtooth" (one bounded
heartbeat that does REAL verification each tick, not many 5-min arm-check-arm cycles — THIS is the correct pattern for a
known-duration VM-scale job, not the ≤30-min sub-agent-heartbeat pattern above) + § "Wake sources" (`run_in_background`
completion is reliable; a dispatched sub-agent's completion is NOT if it dies silently).

**On Agent-Orchestrator (tmux) workers specifically**: this laptop-side failure mode does not apply the same way —
`agents/worker.md`'s `/progress` heartbeat (every ~5 min, server flags stale at 25 min) is already duration-independent
(a heartbeat ping is cheap and does not require the underlying job to finish, unlike a sub-agent re-arm which requires
ending and restarting a full reasoning turn) — see `worker.md`'s own composability note ("plan the check-in cadence
around the heartbeat requirement, not around how often the underlying job's own progress changes", § "run_in_background
alone does not make a long job immune to a session kill" above). An AO worker launching a VM-scale job should keep
sending its normal ~5-min `/progress` heartbeat throughout — including while long-idle waiting on VM progress — rather
than adopt the laptop-side ≤30-min-sub-agent-heartbeat pattern at all.

## A background `Workflow()` run can be silently stopped mid-run with no completion record — verify by direct measurement, never trust self-report (codified 2026-07-24)

`Workflow()` is documented as running in the background and delivering a `<task-notification>` on completion — but a run
can be reported "stopped" with **no completion record and no indication of how much it actually finished**. This is not
a one-off: `plan_line_cap_remediation_2026_07_23.md` hit it **twice independently** (`wf_22001490-e9b`, then a second
run `wf_87a8f203-aa1` re-dispatched against the same remaining tail) — both times with real, uncommitted, unverified
partial progress already sitting in the working tree, discovered only because the working tree was inspected directly,
not because the tool reported it.

**RULE:** when a `Workflow()` run comes back "stopped"/inconclusive (or you cannot otherwise confirm it ran to its
declared completion), do NOT assume zero progress and do NOT assume the reported summary (if any) is complete or
accurate. Recover by **direct measurement** of the actual target artifacts, e.g. for a file-editing workflow:

1. `wc -l` every target file vs `git show HEAD:<path> | wc -l` (or the equivalent artifact-count/state check for a
   non-file target) to find what actually changed on disk.
2. For a conservation-sensitive edit (e.g. content moved, not deleted), confirm every removed unit landed somewhere real
   — `grep -cE '^- \[[ xX]\]'` a before/after todo count, `grep -F` a snippet of removed content against every claimed
   destination file — before trusting the change is safe to keep.
3. Only THEN decide what to commit — partial-but-verified progress is real and should be kept; do not discard it because
   the run "failed", and do not re-dispatch the same workflow assuming last time's failure was a fluke — budget for
   having to run this same recovery drill again.

This is the `Workflow()`-specific instance of the same principle as § "Dispatched sub-agent is NOT a reliable wake"
above — a background task's own self-report (including "no report at all") is never sufficient evidence of what it did;
only a fresh measurement of the target state is.

## A resumed sub-agent that arms its OWN background watchdog and ends its turn reads as "finished" to the parent — every time (codified 2026-07-28)

A sub-agent correctly following § "Direct-check beats polling" below for a long-running check (a `quality-gates.sh` run,
a Docker build, a manifest CAS-write retry) will often reach for `run_in_background` + end its turn, expecting to be
"woken" when that background process completes — the pattern that works fine for a top-level agent talking directly to
the operator. **It does not work the same way one level down.** From the PARENT orchestrator's perspective, a dispatched
sub-agent that ends its turn with no live `Agent`-tool child of its own is **indistinguishable from having finished** —
the parent's harness fires a real completion notification regardless of what background shell processes the sub-agent
itself left running. The sub-agent's own watchdog then fires into a turn nobody is listening to; the parent must notice,
manually resume the sub-agent, and only then does real progress continue.

**Incident (2026-07-28, `june_2026_vintage_audit_findings_2026_07_27.md` autonomous-completion wave):** 7 of 9 resumed
sub-agents hit this at least once — some 2-3 times in a row — each ending its turn on a message equivalent to "I'll wait
for the background watchdog/monitor to notify me," each triggering a real `<task-notification status="completed">` that
the parent then had to resolve by resending the SAME task with an explicit "check synchronously now, do not re-arm
another wait" instruction. Each round-trip cost a full sub-agent turn for zero net task progress.

**RULE for anyone authoring a sub-agent prompt that includes a genuinely long-running step:** tell the sub-agent
explicitly, in the dispatch prompt, to **wait synchronously within its own turn** (a bounded `wait`/sleep/poll-loop
inside one Bash call, not a `run_in_background` job it then stops watching) for anything it needs the result of before
it can call itself done — arming a background watchdog and ending the turn is the anti-pattern here, not the fix,
precisely because "ending the turn" is the signal that reads as completion one level up. If the wait is genuinely too
long for one turn (e.g. a multi-hour backfill), that is a sign the sub-agent's OWN task is not actually "wait for X" but
"kick off X and report back now" — split it into two dispatches (kick off, then a second dispatch/resume once the
parent's own watchdog confirms X is done) rather than asking the sub-agent to straddle both.

## Direct-check beats polling (operator 2026-06-23)

A build / Cloud Run execution / PR / job status is a **single on-demand query** (`gcloud builds describe`,
`gh run view`, `gcloud run jobs executions describe`) — describe it and act. By the time you look it is **often already
done**. Arming a 30s-tick poller or "waiter" loop around a queryable status is **wasted motion that manufactures a
dormancy gap** (the operator then finds you "waiting" on something already finished).

The only **irreducible** wait is the underlying operation itself — a Docker image build is ~8–12 min and cannot be
forced faster. For that floor, use **one** tracked `run_in_background` task that exits on completion (it auto-wakes
you); do not wrap a one-call status check in a polling loop, and do not chain short waiters (sawtooth). Direct-check →
conclude → move on. Composes with § "Watcher coverage" + the "Don't over-watch + no-sawtooth" rule in CLAUDE.md.

## Backfill progress = the TARGET ARTIFACT, entity-scoped — never activity (HARD RULE, codified 2026-07-18)

A backfill/migration monitor MUST key on **objects of the requested type appearing in the window**, not on any activity
signal. Activity signals — log-line growth, log mtime, heartbeat blobs, process liveness, "N calls queued", `RUNNING`
status — all report **healthy while zero target output is produced**.

Measured failure (sports round-FIXTURES, 2026-07-18): a backfill VM launched `--entity FIXTURES` ran **3.5 hours** with
log lines climbing 81k → 103k, `PIPELINE_HEARTBEAT` firing, per-date "Shard completeness OK" messages, and
`status=RUNNING` throughout. It wrote **ZERO** `entity=fixtures` objects. Root cause: the write gate was existence-only
and ignored `redo_all`, so every already-captured date was skipped. A second launch WITH `--force` also wrote zero. The
failure was invisible to every activity-based signal for hours; one query — _"how many `entity=fixtures` parquets were
created today?"_ — settled it in seconds.

**The entity-scoping refinement (this is the subtle part).** "Some artifact was written" is NOT sufficient. That same VM
was writing per-VM manifest shards briskly the whole time — for `fixture_lineups` / `fixture_stats` / `fixture_events` /
`player_stats`. Those entities honour `redo_all`; the FIXTURES gate did not. So a shard-progress check that is
**entity-agnostic** sees healthy progress and passes the VM. `deployment-service/scripts/vm/ vm_zombie_watchdog.py`
already checks per-VM manifest-shard write progress explicitly to catch "alive + heartbeating but no useful work
happening" — but it is entity-agnostic, so it would have passed this VM.

**Rules:**

1. The monitor's progress metric is a **count of target artifacts created in the run window** (GCS object `time_created`
   on the expected prefix/entity, or manifest rows for that `data_type`) — never log/heartbeat activity.
2. When the job declares a TARGET (`--entity X`, a data_type, an asset_group), the metric MUST be **scoped to that
   target**. A job asked for X that produces only Y is FAILING, however busy it looks.
3. Sample dates/keys the job reaches EARLY, and alert on **still-zero after a bounded window** (a first-launch monitor
   keyed on dates the job had not yet reached produced a false alert on the same incident — the sample must be inside
   the processed range).
4. `time_created` / generation, never `updated` — a storage-class lifecycle transition bumps `updated` without any write
   (measured on the same corpus).
5. Activity signals remain valid ONLY for the orthogonal question "is the process hung?" (log-mtime advancement,
   heartbeat) — they can never establish that useful work happened.

Applies to backfills, migrations, re-derives and consolidator runs alike. SSOT for the incident:
`plans/active/issues/sports_features_layer_findings_sweep_2026_07_18.md` § G.

### Refinement (same day, 2026-07-18) — an artifact check is only as good as the ENTITY NAME

An artifact-keyed monitor fails EXACTLY like an activity-keyed one when it queries a **stale entity name**. Measured
hours after codifying the rule above: the sports fixtures entity had been SPLIT into `entity=fixtures_schedule` +
`entity=fixtures_outcomes`, but the monitor still counted the legacy `entity=fixtures`. It reported **zero writes on a
WORKING fix** and was ~7 minutes from raising a false "the fix did not take effect" alert. The real state was
`fixtures_schedule` with `round` populated 1/1 and 2/2.

So, before trusting a zero from an artifact check:

1. **Enumerate what the run ACTUALLY created** (`by entity` histogram over the day prefix, unfiltered) before concluding
   "nothing was written". One unfiltered listing distinguishes "wrote nothing" from "wrote somewhere else" in a single
   query — and is the ONLY cheap way to catch a rename/split.
2. A zero from a name-filtered query is **two hypotheses, not one**: nothing written, OR written under a different name.
   Never collapse them.
3. Entity names split/rename over a corpus's life; the June-era objects still sit under the OLD name, so "the old name
   exists in GCS" does NOT prove it is still the write target.

## A liveness check is only valid at the instant you act on it — re-check immediately before touching, never from an earlier read (codified 2026-07-29)

Hit during a multi-hour autonomous session: an mtime-based liveness check on a foreign dirty file read as "64 minutes
stale" (safely dead, eligible to inherit per the standard liveness gate). By the time the next tool call actually went
to touch it moments later, an immediate re-check showed mtime=13 seconds (genuinely live — another agent had just
resumed work on it). The first reading was not wrong when taken; it was simply **stale by the time it was acted on**,
because real time passed between the check and the action (other tool calls, reasoning, dispatch overhead).

**The rule**: liveness is a point-in-time fact, not a durable one. A "dead, safe to inherit" verdict from an earlier
check in the same turn or session is not sufficient grounds to act — **re-run the liveness check immediately before the
touch**, not before the intervening work. This is cheap (one `stat`/`git status` call) and is the only way to close the
race between "I checked" and "I act." Treat any liveness check as expired the moment something else happens in between —
a tool call, a wait, a dispatch — even if that gap is only seconds.

This is the same class of bug as trusting a cached "task done" status instead of re-verifying at the moment you rely on
it (see the resumed-sub-agent section above) — the fix is identical: re-verify at the point of action, not at the point
of the earlier observation.

## A local script's log timestamp is LOCAL TIME, not UTC — compare cloud-resource elapsed time in UTC, never against a `%(asctime)s` line (codified 2026-08-03)

Hit while diagnosing a manifest-consolidator lock during
`mtds_prediction_rebuild_instrument_type_mismatch_2026_08_01.md`'s apply chain: a lock blob showed "fresh lock present"
across 12+ consecutive polls spanning what LOOKED like 8+ minutes of local script log timestamps (`2026-08-03 15:13:...`
through `15:21:...`) — well past the consolidator's 300s default staleness TTL, reading as a genuine stall. The initial
(wrong) diagnosis was "the local machine's clock is drifting ~37-40 minutes ahead of UTC." The actual, verified cause
was much simpler and had nothing to do with clock drift: the machine's system clock was completely accurate (`date -u`
matched Google's own HTTP `Date:` response header exactly) — the local **timezone is BST (UTC+1)**, and Python's
`logging.basicConfig(format="%(asctime)s ...")` defaults to `time.localtime()`, so every script log line was silently 1
hour ahead of the true UTC timestamp the lock blob itself carried (`{"started_at": "...+00:00"}`, GCS `updated` field,
etc.). Comparing a local-time log line against a UTC-stamped cloud object's age is comparing two different clocks
without knowing it — the discrepancy scales with whatever the local TZ offset happens to be (1 hour here; it will differ
across machines/sessions and is NOT always a round number for every zone).

**The rule**: when judging whether a lock/heartbeat/cloud-timestamped resource is stale, fresh, or stalled, never
eyeball a script's own printed `%(asctime)s`-style log timestamp against your sense of elapsed time. Instead:

1. Read the resource's OWN timestamp directly (the GCS object's `updated`/`timeCreated` field, a lock blob's embedded
   `started_at`, a Cloud Scheduler/Run API response) — these are authoritative UTC.
2. Compute elapsed time against a real current-UTC reference (`datetime.now(timezone.utc)` in Python, or `date -u` / an
   HTTP response `Date:` header from any cloud endpoint as an independent cross-check) — never against a local process's
   own local-time log output.
3. If a script's logs must be read for elapsed-time reasoning, first check whether its logger is UTC-configured
   (`logging.Formatter.converter = time.gmtime`) or left at the local-time default — most ad-hoc scripts in this
   workspace use the unconfigured default, which is local time.

A relative interval measured entirely within the SAME script run (e.g. `sleep 30` between polls, or two `time.time()`
calls) is unaffected by this — TZ offset only corrupts ABSOLUTE timestamp comparisons across a local-vs-UTC boundary,
never relative durations measured by the same clock. The failure mode this prevents is treating a perfectly healthy,
recently-acquired lock as a stalled one purely from a timezone-display artifact — and either escalating a non-incident
or (worse) forcibly reclaiming a lock a live process still legitimately holds.
