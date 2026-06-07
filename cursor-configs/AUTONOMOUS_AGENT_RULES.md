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
