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
last_reviewed: 2026-06-25
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

Composes with § "Watcher coverage" (terminal verdict every path) + § "Don't over-watch + no-sawtooth" (one bounded
heartbeat that does REAL verification each tick, not many 5-min arm-check-arm cycles) + § "Wake sources"
(`run_in_background` completion is reliable; a dispatched sub-agent's completion is NOT if it dies silently).

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
