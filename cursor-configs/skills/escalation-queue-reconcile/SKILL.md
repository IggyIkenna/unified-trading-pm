---
name: escalation-queue-reconcile
description: >-
  Reconcile the AO escalation-queue MECHANISM itself to healthy — not an individual CI wall (that's `/ci-reconcile`'s
  job once the queue is healthy), but the watchdog/reconcile-pass subsystem that dispatches, retries, pages on, and
  eventually gives up on a red CI wall. Built from the 2026-08-07 incident where two `unified-trading-pm` rows sat
  `unresolved — still_red_past_deadline` for 15-17h because `verify_dispatched_escalations` only ever re-polled
  `status=="dispatched"` rows — once a row went terminal `unresolved` nothing ever looked at it again — plus the
  regression caught in the SAME session where the fix's own reconcile pass (`reconcile_stale_unresolved_escalations`)
  sorted `resolved_at` ASCENDING with a small limit, so 238 historical rows starved out the 2 recent ones the feature
  was built for. Cheap-first by design (2026-08-07 operator direction, "keep the polling interval wide so genuinely-no-
  issue doesn't waste tool calls"): Step 1 is always ONE curl call against `GET /api/escalations/active`; a healthy
  queue (empty, or only fresh in-flight rows well inside the retuned 45-min deadline) exits immediately with a one-line
  report — no deep diagnosis, no issue-doc churn, minimal tokens. Only a genuine anomaly (a `status=unresolved` row, a
  `dispatched`/`queued` row past its deadline, or the retuned constants having drifted back toward the old single-shot
  behavior) triggers the expensive path: diagnose at the root via the same read-only SSM approach used to catch the
  original bug, auto-fix anything small/clear/obviously-correct the same way this workspace's background agents already
  do (quickmerge the fix), and for a genuine judgment call raise a live `/blocked` question to `main` first (bounded
  2-minute wait, mirroring `cicd.md`'s pattern) before falling back to filing/updating a `plans/active/issues/` doc for
  the operator — mirroring `/ci-reconcile`'s "always auto-fixes, never silently logs" contract, scoped down to this one
  subsystem, plus the ask-main-then-operator escalation ladder `plan_reconciler`/`cicd` already use. Designed to be
  dispatched on a 3-hour systemd timer via `agent-orchestrator/scripts/ install-escalation-queue-reconciler-timer.sh`
  (`mode=escalation_reconcile`, `agents/escalation_queue_reconciler.md`) — a ONE-SHOT check per invocation, not a
  self-looping watch; AO's own timer supplies the cadence. Trigger on `/escalation-queue-reconcile`, "check the
  escalation queue is healthy", "did the escalation watchdog regress", "audit the AO escalation queue", "is a CI wall
  stuck unresolved".
---

# /escalation-queue-reconcile — escalation-queue mechanism health check

Answers one question, cheaply when the answer is "yes": **is the escalation-queue MECHANISM itself healthy right now —
not an individual red wall, but the watchdog that dispatches/retries/pages/reconciles it?** A queue with active
`queued`/`dispatched` rows is normal fleet churn, not a finding — the finding is a row that got PERMANENTLY stuck, or
the reconcile pass that's supposed to catch that silently not working.

**Not `/ci-reconcile`.** That skill fixes an individual CI wall once the queue notices it's red. This skill checks
whether the queue's own dispatch/retry/give-up/reconcile machinery is still doing its job — a narrower, cheaper,
higher-frequency check than a fleet-wide CI sweep.

## Step 0 — are you ON the orchestrator VM, or checking it remotely?

The scheduled `escalation_queue_reconciler` worker (the common case — this is what runs every 3 hours) IS DISPATCHED ON
the orchestrator instance itself (`i-0c9b283b31d6b5ca7`) — it can reach `localhost:8765` directly, no AWS anything
needed. **Try the direct path first, always:**

```bash
curl -s -m 5 localhost:8765/api/mode
```

Succeeds → you're on the VM. Use PLAIN `curl localhost:8765/...` for every check below, no `aws ssm` wrapper — a worker
session's AWS identity (`ikenna-worker`) does NOT have `ssm:SendCommand` and cannot self-grant it (confirmed live
2026-08-08, `plans/archive/issues/escalation_queue_reconciler_ssm_permission_gap_2026_08_08.md`); routing through SSM to
reach the machine you're already running on is both unnecessary and a hard permission wall. Only fails (no response /
connection refused, and it's not a benign restart per Step 1 below) if you're checking this INTERACTIVELY from somewhere
else (your own laptop session, not the dispatched worker) — that's the one case the SSM wrapper below is for:

```bash
CMD_ID=$(aws ssm send-command \
  --instance-ids i-0c9b283b31d6b5ca7 --region ap-northeast-1 \
  --document-name "AWS-RunShellScript" \
  --parameters 'commands=["curl -s -m 10 localhost:8765/api/mode"]' \
  --query "Command.CommandId" --output text)
sleep 4
aws ssm get-command-invocation --command-id "$CMD_ID" --instance-id i-0c9b283b31d6b5ca7 \
  --region ap-northeast-1 --query "{Status:Status,Out:StandardOutputContent,Err:StandardErrorContent}" --output json
```

Every command in Step 1-2 below is written as a plain `curl`/shell command — wrap it in the SSM pattern above ONLY when
Step 0 confirmed you're remote. Don't reach for SSM by default; it's the exception, not the rule.

## Step 1 — the cheap check (always do this first, and ONLY this, on a healthy queue)

```bash
curl -s -m 10 localhost:8765/api/escalations/active
```

This is the SAME view the AO dashboard's escalations widget renders (default `active_within_hours` window) — never act
on a different endpoint or a cached/stale read. Evaluate the result:

- **`[]`, or every row is healthy on its own clock**: a `queued` row's `created_at`, OR a `dispatched` row's
  `dispatched_at`, well inside the retuned 45-minute deadline (`RESOLUTION_DEADLINE_MINUTES` in
  `agent-orchestrator/server/escalation.py`) → **healthy. Report one terse line (row count + oldest age) and STOP.** Do
  not run Step 2. Do not file anything. This is the expected, common-case outcome and must stay cheap — one SSM
  round-trip, nothing else.
- **Any row has `status=unresolved`**, or a `queued` row's `created_at` is past ~45 min, or a `dispatched` row's
  `dispatched_at` is past ~45 min, or the curl itself failed → proceed to Step 2.

  **Judge a `dispatched` row by `dispatched_at`, never `created_at`.** `verify_dispatched_escalations` anchors its
  deadline check on `dispatched_at` (falling back to `created_at` only when `dispatched_at` is null) — a re-escalated
  row's `dispatched_at` resets on every fresh redispatch while `created_at` stays pinned at the original enqueue time. A
  `dispatched` row with an old `created_at` but a recent `dispatched_at` (the API response's `attempts` > 1 confirms
  it's been redispatched) is mid-cycle in the designed re-escalation loop, not stuck — scoring it on `created_at` alone
  manufactures a false anomaly on every busy-queue run and defeats this step's "stay cheap" goal (confirmed live
  2026-08-08: a `dispatched` row, `attempts=2`, `created_at` ~96min old but `dispatched_at` ~43min old, was healthy and
  mid re-escalation, not stuck).

  **The same reasoning extends to a `queued` row reached via re-escalation, not just fresh enqueues.**
  `_mark_unresolved_and_maybe_reescalate` flips a still-red `dispatched` row to `status=queued` with
  `resolution="still_red_reescalated"`, `dispatched_at` cleared to null, and `resolved_at` stamped to the flip time —
  `retry_queued_escalations` then picks it up oldest-first on a later tick. A `queued` row with an old `created_at` but
  `resolution=still_red_reescalated` and a recent `resolved_at` (the actual last-touched timestamp) is the SAME
  mid-cycle pattern as above, not stuck — judge it by `resolved_at`, not `created_at` (confirmed live 2026-08-10: a
  `queued` row, `created_at` ~2h9min old, `resolved_at` ~4min old, `reescalations=1`, was healthy and awaiting its next
  dispatch tick).

**Connection failure ≠ regression by itself.** If the curl fails (`exit status 7` / connection refused), first rule out
a benign service restart before calling it a finding — this has happened twice in one 6-hour observation window and both
times was ordinary maintenance, not a bug:

```bash
systemctl is-active orchestrator; journalctl -u orchestrator --since "-10 min" | tail -20
```

`deactivating`/`Stopping orchestrator.service` in the log around the failure time → benign restart, retry the Step 1
curl after ~20-40s and treat the retry's result as the real answer. Only escalate to Step 2 if the retry ALSO fails with
the service showing `active`, or the restart pattern itself is recurring across multiple runs (a NEW finding in its own
right — file it, don't just keep silently retrying).

## Step 2 — root-cause diagnosis (only reached on a genuine anomaly)

1. **Confirm the retuned constants haven't drifted back** — read `agent-orchestrator/server/escalation.py`'s
   `RESOLUTION_DEADLINE_MINUTES` (expect 45), `MAX_REESCALATIONS` (expect 10), `PAGE_AFTER_REESCALATIONS` (expect 2),
   `RECONCILE_UNRESOLVED_WINDOW_HOURS` (expect 24). Any of these reverted toward the old single-shot values
   (90/1/page-on-first-miss) is itself the finding — someone shipped a revert, intentionally or not.
2. **Confirm the reconcile pass is actually running and ordered correctly** — the ordering-bug class (ascending instead
   of descending `resolved_at`, or a `LIMIT` too small for the backlog) is exactly the kind of regression that looks
   correct in a code review and only shows up live. Pull a few `unresolved` rows via the same approach as Step 1
   (`GET /api/escalations/active?include_resolved_within_hours=<N>`, widen `N` until the stuck row appears) and check:
   is `reconcile_stale_unresolved_escalations()` (`agent-orchestrator/server/autospawn.py`'s `_drain_escalations()`
   calls it) even being invoked on a live tick — check recent `journalctl`/activity-log output for its log lines, not
   just that the function exists in the source.
3. **For a genuinely stuck row**: diagnose why it never resolved and never got reconciled — read the row's `wall_type`
   - `repo` + `pr_number`, cross-check the real CI state (`gh run list`/`gh pr view`) the same way `/ci-reconcile` does,
     and determine whether the underlying wall is ACTUALLY still red (a real ongoing problem, hand off to
     `/ci-reconcile` or the `cicd` worker) or already cleared (a reconcile-pass bug that should have caught it, file it
     here).

## Step 3 — genuinely uncertain? Ask main first, bounded wait, operator as last resort

Not every Step-2 finding is a slam-dunk fix or a slam-dunk file-it. A judgment call — "is this fix actually safe to
auto-apply", "which of two plausible root causes is it", "does this pattern match an accepted precedent or is it new" —
gets a LIVE attempt at main before falling back to a durable issue doc, the same pattern `cicd`/`plan_reconciler`
already use (`unified-trading-pm/agents/cicd.md` § "NEEDS-A-HUMAN-DECISION"):

```bash
curl -sS -X POST $SERVER_URL/api/slots/$SLOT_ID/blocked \
  -H 'Content-Type: application/json' \
  -d '{"task_id": "'"$DISPATCH_ID"'", "question": "<the finding + why it is genuinely ambiguous>",
       "options": ["A: ...", "B: ..."], "recommendation": "A", "can_continue": false, "authority": "main_agent"}'
```

This fires a dashboard alert and sets your slot `status=blocked`. Poll `GET $SERVER_URL/api/slots/$SLOT_ID/messages`
(heartbeating each tick) for **up to 2 MINUTES**:

- **main answers** → apply the decision, fold it into Step 4 (fix or file, now disambiguated by the answer), and cite
  the answer in your Step 5 report — this is the "answers structure things" payoff: a resolved judgment call becomes a
  documented precedent (in the issue doc or the fix's commit message) instead of a re-diagnosed-from-scratch guess next
  time the same shape recurs.
- **main replies it can't resolve, or 2 minutes elapse with no answer** → STOP waiting, don't hold the slot (shared
  capacity). File the finding as `plans/active/issues/<slug>_<date>.md` per Step 4 as normal, but note explicitly that a
  live main-agent attempt was made and timed out/deferred — this is the "operator as last resort" path: the row persists
  in `/api/blocked` for a human to answer at their own pace (`authority: main_agent`'s 10-min system timeout would
  otherwise kill+requeue your slot — stopping yourself at 2 min avoids that and hands off cleanly instead), and the
  issue doc means the operator doesn't have to re-derive context main already saw.

Reserve `authority: "operator"` on the initial call (skip asking main at all) only for the kind of hard-stop this
workspace treats as human-only regardless of context (e.g. a fix that would need touching wallet keys or force-pushing
main — extremely unlikely for this skill's scope, but the same bar as everywhere else in this workspace).

## Step 4 — fix or file, never silently log

Same findings-triage HARD RULE this whole workspace uses: a small, clear, obviously-correct code fix (a reverted
constant, an ordering bug, a missing log line) → fix it directly and ship via `bash scripts/quality-gates.sh --no-fix` +
`quickmerge.sh --agent --files '<paths>'`, add a regression test if the bug class is the kind unit tests can catch (the
ordering bug from 2026-08-07 needed a REAL in-memory SQLite test — a MagicMock-based test cannot catch an `ORDER BY`
regression, see `tests/test_escalation.py`'s `test_reconcile_prioritizes_recent_over_ancient_under_a_tight_limit`).
Anything ambiguous, cross-repo, or requiring a judgment call → Step 3 first (ask main, bounded wait), then
`plans/active/issues/<slug>_<date>.md` either way (answered-and-fixed still gets a brief record; unresolved gets the
full finding) citing the specific row(s)/evidence found. A genuinely stuck wall whose root cause is in the TARGET repo's
own code (not the escalation mechanism) is out of scope for THIS skill — hand it to `/ci-reconcile` rather than fixing
it here.

## Step 5 — report

**Cheap path (Step 1 only, the expected common case)**: one line — row count, oldest age, verdict. Nothing more.

**Deep path (Step 2+ reached)**: what was found, the root-cause diagnosis, whether Step 3's live ask was used and by
whom it was answered (main / timed-out-to-operator), what was fixed (repo@sha) or filed (issue doc path), and the Step-1
re-check confirming the queue is healthy again post-fix.

## Under `/autonomous`

One-shot per dispatch, matching AO's 3-hour scheduled-timer cadence (`install-escalation-queue-reconciler-timer.sh`) —
do not loop internally waiting for the next tick; the timer supplies that. Step 3's 2-minute bounded wait is the ONE
exception to "never pause" — it has its own hard ceiling precisely so it can't turn into an unbounded stall. If Step 2+
fixed something, do one confirming Step-1 re-check before finishing, then stop (mirrors `/ci-reconcile`'s own no-pause
contract).

## What this skill does NOT do

Does not fix an individual red CI wall's actual failing test/lint/build (that's `/ci-reconcile` or the `cicd` worker's
job) — only the queue mechanism that dispatches/retries/pages/reconciles it. Does not touch `escalation.py`'s tuning
constants without a clear, evidenced reason (a confirmed drift/revert, not a preference change). Does not force-push,
does not bypass the provenance gate. Codex/plan SSOTs: `agent-orchestrator/server/escalation.py` (the constants +
`reconcile_stale_unresolved_escalations` docstrings are the living SSOT for expected values),
`plans/archive/issues/escalation_watchdog_retune_and_reconcile_2026_08_07.md` (the incident this skill exists to keep
fixed).
