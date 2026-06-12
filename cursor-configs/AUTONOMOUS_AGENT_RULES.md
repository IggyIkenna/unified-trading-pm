# AUTONOMOUS AGENT RULES — finishing a lifecycle to DONE (no re-dispatch loops)

> **Purpose.** This file exists because long-running infra lifecycles (CI/CD repair, fleet promotion, manifest
> migrations) have repeatedly been left **half-done** — partially shipped, with TODOs, deferrals, and "operator-gated"
> items that the next agent re-discovers, re-plans, and re-defers. That restarts the same lifecycle five times and never
> converges. When an operator dispatches a "finish this completely while I'm away" task, these are the standing rules.
> Paste this file (alongside `SUB_AGENT_MANDATORY_RULES.md`) at the top of any such dispatch, and reference it from the
> plan-of-record.
>
> **This is the COMPLETION contract.** `SUB_AGENT_MANDATORY_RULES.md` is the _floor_ (how to act safely in this
> workspace); this file is the _finish-line_ (how to drive a lifecycle to a genuinely-done state without coming back).

## When these rules apply

The operator has said some version of: _"finish this completely, I'm away for N hours, don't ask me questions you could
answer yourself or with common sense, I want to come back to a working <thing>, I don't care how long / how many agents
/ how much context it takes, just keep the plan updated and keep going."_ That dispatch grants the authority below.

**The `/autonomous` skill is the explicit trigger.** Ending a prompt with `/autonomous` (or typing `/autonomous`) means
exactly the dispatch above: _apply these rules + `SUB_AGENT_MANDATORY_RULES.md`, and drive the task to completion on a
loop_ (rule 12). The skill (`cursor-configs/skills/autonomous/SKILL.md`, symlinked into `.claude/skills/`) is the
canonical entry point — it reads this file, arms the loop, and runs to a verified done-state.

## The rules

1. **Finish completely — no partial states.** Banned end-states: `DEFERRED` without doing it, `BLOCKED-OPERATOR`,
   `BLOCKED-CREDENTIALS` (you were given the creds), "leave for another agent", "hand to Harsh", "post-cutover", "most
   of it done, rest later", a half-finished wave. The lifecycle is done when its success criteria are _all_ met. The
   **only** acceptable non-completion is a genuine physical impossibility (e.g. two dependencies that cannot coexist —
   the canonical example is the aiohttp `<3.14` pin vs a CVE that only a `>=3.14` release fixes, where one constraint
   _must_ lose). When you hit one: take the least-bad path, **document the decision in the plan**, and keep going — do
   not stop and do not ask.

2. **Do not ask the operator questions.** They are away. Any decision the operator could make, you make — using common
   sense plus the **documented record of intent**: the plan-of-record, its source plans, the `issues/` docs, and the
   codex SSOTs explain _why_ every prior commit/PR exists, so you can decide what to keep, how to merge, and what to
   close. Ask all genuinely-unanswerable questions _before_ the operator leaves; after that, decide and document.

3. **You have full authority for the chicken-and-egg.** A pipeline that needs its own corrected code on `main`/`staging`
   to start working is unblockable through the normal gated path. You are authorized to **force-push `main`/`staging`**,
   create branches, create rulesets, restart services you own, and run the infra ops the plan labels "operator". These
   are not operator decisions when an operator has dispatched you to finish autonomously and given you the auth. (Still
   genuinely hard-stop: live wallet keys, `1.0.0` version graduation — those stay human unless explicitly named.)

4. **Reconcile everything down here, now.** Conflicting/dirty/blocked PRs, diverged branches, red quality gates — these
   are _yours_ to fix in this slot in this session. Never "give it back" to the agent who made it or to a teammate;
   assume **no one else is working** (one operator, one laptop, one slot). Resolve a conflict by keeping the **merged
   combination** of both sides' genuine work (never blind "take mine"/"take theirs"); where two agents independently
   wrote the same rule/fix, merge into the single best version; then **verify content survival** (grep both your
   additions and the incoming ones) before pushing.

5. **Parallelize with sub-agents to protect your context.** Fan out isolated, well-scoped work — greening one repo's
   quality gates, reconciling one repo's PR, enumerating one plan's open todos — to sub-agents (inject
   `SUB_AGENT_MANDATORY_RULES.md`). Keep the conclusions, not the file dumps. Max ~10 concurrent; never two agents on
   the same repo/file; shared-host cap ≤2 full `quality-gates.sh` at once.

6. **Keep the plan continuously updated — it is your memory across context compression.** Maintain an append-only
   **Progress Log** in the plan-of-record. Every shipped unit, every decision, every blocker-and-its-resolution goes in
   _as it happens_. Assume your context **will** be auto-compressed mid-task; a compressed-context future-you must be
   able to re-read the plan's index + brief + Progress Log and resume losslessly. Do not announce "I'm running out of
   context" and stop — write state to the plan and continue.

7. **Ship discipline stays canonical** (this is _how_, the above is _whether_): commit only from a `quality-gates.sh`-
   green tree (QG-sweep — run the gate once per batch); ship via `quickmerge --agent --files '<paths>'`;
   **Commit+Push+Flip** the source-plan checkbox in the same turn; conditional-push (fetch first, never stomp incoming);
   honor each repo's promotion model (PM → `main` directly, Option B; services via `tab→LDR→staging→SIT→main`). Capture
   any new discovery as a `- [ ]` in the right source plan the moment it surfaces.

8. **Respect dependency order.** Drive the base tiers green first (T0 = `unified-trading-library` /
   `unified-api-contracts`), then dependents, then leaves; only do the irreversible cut (fleet promote) once the whole
   set is green at the prior stage. A wave is not "started" until the previous wave is green.

9. **End with a complete report.** When the success criteria are met, write a final report in the plan: every
   forced-tradeoff decision made under rule 1, every genuine impossibility, and the verified end-state. There should be
   nothing for the operator to "pick up" — that is the whole point.

10. **Use the full observability + control surface proactively — you drive the machinery, you don't just watch it.** You
    are authorized and expected to: **manually trigger workflows** (`gh workflow run <wf>.yml --ref <branch>`,
    `repository_dispatch` events, re-dispatch a stale required check, kick the promoter / SIT / staging-to-main) to
    unstick a stalled stage or to verify a fix — do not wait passively for a cron when a manual dispatch confirms it
    now; **emit and read Slack alerts** (the `#ci-failures` webhook `SLACK_CI_WEBHOOK_URL` + the every-alert →
    orchestrator path) so progress and failures are visible, and use them to monitor the cascade end-to-end; **watch the
    right progress metric** (repos reaching `STAGING_GREEN`/`main`, PRs merged, runs going green) with short ticks first
    then widen, and on a flat metric STOP-and-diagnose (`gh run view --log-failed`) rather than wait it out. Reach for
    every tool that gives you signal or control — manual triggers, Slack, `gh run`/`gh pr` polling, monitors — instead
    of blocking on the operator or on a schedule.

11. **Verify the BLAST RADIUS before tightening a gate or rolling fleet-wide — local-green ≠ fleet-green. (Added
    2026-06-07 after a real regression: re-enabling the `[5.5]` actionlint gate + a shellcheck-default-severity made
    EVERY repo's QG fail on rolled-out templates that were never checked; and pushing canonical workflow files to LDR
    only left every repo's `staging` behind → a `semver-agent.yml` conflict class that blocked another agent's PR. Both
    were "shipped, looked done locally, broke the fleet.")** Two hard sub-rules:
    - **(a) A gate you make stricter must be one the WHOLE FLEET already passes — prove it first, in the same change.**
      Before enabling / broadening / re-enabling a check or lowering a ratchet, run that exact check against EVERY repo
      (and every branch) it will gate — not just PM / your repo. If any repo fails, either fix it in the SAME change, or
      scope the gate so it can't fail them (e.g. severity floor), or don't ship it. Never enable a gate and "see what
      goes red" — that IS the regression. A check that runs from an SSOT (`base-service.sh`, a reusable workflow, a
      rolled-out template) gates the fleet the instant it merges to the ref CI reads.
    - **(b) A fleet rollout / shared-artifact change is not done until ALL branches + consumers are reconciled.** In the
      `tab → LDR → staging → main` model, pushing a file to LDR only leaves `staging` (and `main`) behind on that file →
      a conflict for every staging-based PR until it's promoted. When you roll a workflow/template/base-script to LDR
      fleet-wide, in the same pass either (i) drive the LDR→staging drain so staging catches up, or (ii) explicitly note
      - own the resulting conflict class — do NOT walk away and let another agent hit it.
    - **The closing self-check (every gate/rollout change): re-run the affected gate on ≥1 representative CONSUMER repo
      (not the SSOT repo) and confirm green, and check the other promotion branches you didn't touch.** If you didn't
      verify it on a consumer + across branches, you didn't finish it — you just moved the failure to whoever pulls
      next.

12. **Drive to completion on a loop — the loop is the _mechanism_ for "keep going", not a new authority.** Every rule
    above answers _"finish without coming back"_; a **loop** is the timer that makes you come back to **your own**
    unfinished work — tick after tick — instead of stopping at _"done, what's next?"_. This is what lets one dispatch
    run for many hours / dozens of iterations and actually converge. Use the `/loop` skill mechanics (a background
    sentinel + `notify_on_output`, or `ScheduleWakeup`) to re-feed yourself the task on each tick.
    - **(a) `/autonomous` means run to the end — the loop is the default driver, not a conditional.** The dispatch is
      "drive to completion"; arm a loop and keep going until the success criteria are met, never stopping at the first
      natural break. The only judgment is _cadence_, not _whether_ — a queue of plans / a multi-hour migration /
      iterate-until-converged work (backtest-tuning, market-watch) obviously loops; a genuinely short single-unit job
      may finish in one pass before the first tick fires (fine — don't manufacture iterations), but the posture is
      always "keep going to done," never "did one thing, stopped."
    - **(b) Self-pace by default; fixed-interval only for a steady external cadence.** Prefer a **dynamic** loop: after
      each iteration choose the next wake by _what you're actually waiting on_ — an **event** (a CI run / backtest / PR
      reaching a terminal state → arm a watcher that wakes you when it fires) or a **time** (lean long for idle ticks to
      avoid pure overhead). Use a **fixed interval** (e.g. `15m`) only when you're polling a steady external cadence.
      Honor the poll-discipline already in `CLAUDE.md` (short ~30–45 s ticks first to confirm the mechanism moves, then
      widen).
    - **(c) The canonical multi-plan loop** (the "execute this list of plans to DONE" pattern), bound to workspace
      ship-discipline: each tick → pick the next open plan item → implement → `quality-gates.sh`-green →
      `quickmerge --agent --files` → **flip the checkbox in the same turn** (Commit+Push+Flip, rule 7); when a whole
      plan's items are done → run a **thorough audit/analysis of what actually shipped** (rule 9 + Post-Plan-Phase Codex
      Audit) before moving to the next plan.
    - **(d) The loop's "handoff document" IS the plan's Progress Log (rule 6) — never a new
      `*_HANDOFF.md`/`*_SUMMARY.md` / status file** (no-summary-docs rule). Journal progress into the plan-of-record
      every tick (or the slot ping file for cross-plan multi-plan dispatches); assume context is auto-compressed
      _between_ ticks, so a compressed future-you must resume losslessly from that log. Update it periodically, not just
      at the end.
    - **(e) Every loop MUST have a termination condition — finish, don't spin forever.** The loop ends when the success
      criteria are met → kill the loop/sleeper PID, write the rule-9 final report. And **stall-safety**: a progress
      metric must _climb_ across ticks (items flipped, plans done, rows backfilled, runs green); a **flat** metric =
      **STOP and diagnose** the blocker (`gh run view --log-failed`) — never burn ticks blindly repeating a failing
      action.
    - **(f) Spec-change mid-loop — the loop does NOT license silently redefining the goal.** A small clarification
      _within_ the documented intent (plan / source plans / `issues/` / codex) → make it, log it (rules 1–2), keep
      going. A genuine **scope/spec change that contradicts the documented record of intent** is the rare case: take the
      least-bad path and **document the decision** — or, if it's the kind of thing you could only have asked _before_
      the operator left, that's exactly the question to have surfaced then; on a tick, decide-and-document, never
      quietly pivot the whole dispatch.
    - **(g) A loop inherits every rule here — it is throttle, not bypass.** Hard-stops still hard-stop (live wallet
      keys, `1.0.0` graduation); kill-switch autonomy stays protective-only; ship discipline stays canonical. On
      operator "stop", kill the loop/sleeper PID **immediately** and don't re-arm (continuous runtimes can be sticky —
      honor stop the first time, not the fifth).

## The anti-pattern this prevents

> Agent does 60% of a lifecycle, ships it, marks the rest `DEFERRED` / `BLOCKED-OPERATOR`, writes a summary. Next agent
> reads the summary, re-audits, re-plans, ships another 60% of the _remainder_, defers again. Five sessions later the
> pipeline still is not self-sustaining and the operator has answered the same question five times. **Converge instead:
> one agent, full authority, runs it to actually-done, parallelizing as needed, journaling to the plan throughout.**
>
> **Second anti-pattern (rule 11) — the silent fleet regression:** an agent ships a gate-tightening or an SSOT/fleet
> rollout, sees it green LOCALLY (PM / its own repo), declares done — but the change gates or skews the other ~24 repos
> it never checked, so the next agent's PR breaks on infra the first agent introduced. "Green where I looked" is not
> "green where it runs." Tightening a gate or rolling fleet-wide is only done once proven across the fleet + all
> promotion branches.
>
> **Third anti-pattern (rule 12) — the agent that stops at the first natural break:** dispatched to "execute these N
> plans to done," it implements one, ships it, writes "ready for next agent," and stops — because nothing _re-asked_ it
> to continue. The fix is a **loop**: re-feed yourself the task on a self-paced tick so you pick up the next item
> yourself, journal each tick to the plan's Progress Log, and only stop the loop when the success criteria are met. The
> loop's failure mode is the opposite — **spinning forever / repeating a failing action**: guard it with a termination
> condition and a climbing progress metric (flat metric → STOP and diagnose). Persistence is the point; mindless
> repetition is the regression.
