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

## Composes with

- **Background-task honesty** (`CLAUDE.md` § Agent behavior) — the truthfulness half; this doc is the cadence half.
- **No fire-and-forget VM launches** (`codex/05-infrastructure/vm-tarball-deployment.md`) — T+10min verify is a poll.
- **CI verification after every push** (`CLAUDE.md`) — `gh run list` + `gh run view --log-failed` are the poll tools.
- **Plans run to actual completion** — "operationally shipped" is verified by polling the real signal to completion, not
  assumed from a green smoke test.
