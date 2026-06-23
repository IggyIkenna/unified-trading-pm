---
scope: [engineer, admin]
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
- **No fire-and-forget VM launches** (`codex/05-infrastructure/vm-tarball-deployment.md`) — T+10min verify is a poll.
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

## Direct-check beats polling (operator 2026-06-23)

A build / Cloud Run execution / PR / job status is a **single on-demand query** (`gcloud builds describe`, `gh run view`,
`gcloud run jobs executions describe`) — describe it and act. By the time you look it is **often already done**. Arming a
30s-tick poller or "waiter" loop around a queryable status is **wasted motion that manufactures a dormancy gap** (the
operator then finds you "waiting" on something already finished).

The only **irreducible** wait is the underlying operation itself — a Docker image build is ~8–12 min and cannot be forced
faster. For that floor, use **one** tracked `run_in_background` task that exits on completion (it auto-wakes you); do not
wrap a one-call status check in a polling loop, and do not chain short waiters (sawtooth). Direct-check → conclude → move
on. Composes with § "Watcher coverage" + the "Don't over-watch + no-sawtooth" rule in CLAUDE.md.
