---
doc_type: issue
title: >-
  a plan_reconciler tranche run that dies mid-flight (before its own STEP 7 unlock) leaves `locked_by: plan_reconciler
  (agt-xxxxxx) since <ts>` permanently stuck — no TTL, heartbeat, or dead-session correlation exists anywhere to detect
  or clear it
summary: >-
  4 of the 10 `plan-reconciler.timer` tranche dispatches on 2026-08-09 (defi, cefi, ci, cross_cutting) died mid-run with
  zero forward progress after their first checkpoint commit, each leaving `locked_by: plan_reconciler (agt-xxxxxx) since
  <ts>` permanently set on its own `plan_reconciler_findings_<tranche>_2026_08_09.md` progress-journal doc — the skill's
  own "never auto-unlock" HARD-STOP means nothing has cleared these since (confirmed dead via git log: no commits after
  the initial checkpoint, no live process). This is NOT a one-off: the exact same pattern (a stale `locked_by:
  plan_reconciler (agt-XXXXXX) since <ts>` with only the initial 1-2 commits, never auto-released) is independently
  documented in at least 3 OTHER dated findings docs from 2026-08-06 through 2026-08-10
  (`plan_reconciler_findings_ci_2026_08_10.md`, `ag_closeout_audit_tradfi_parked_2026_08_10.md`,
  `safe_doc_push_isolation_drops_rename_deletions_2026_08_10.md`), each time surfaced only as an incidental "FYI" note
  by the NEXT day's audit rather than an actionable alert. Root cause investigated below: (1) the systemd
  `TimeoutStartSec=6000` on the timer's own dispatch service does NOT explain the deaths — it bounds only the CURL call
  waiting for `/api/plan-health/dispatch`'s HTTP response, and that response returns once the tmux session boots + the
  boot prompt is pasted (`autospawn._do_spawn`'s own docstring: "the SlotRow is NOT updated here — the spawned worker's
  first /heartbeat or /boot will update it"; no completion-polling code exists in `plan_health.dispatch()`) — a "spawn
  receipt," not the worker's full run, per the scheduled-jobs codex SSOT itself ("a row labelled `dispatched` is a SPAWN
  RECEIPT, not a completion"). The actual proximate death cause (OOM / context exhaustion / crash / quota) could not be
  independently confirmed from a laptop checkout for these 3-day-old dispatches (no live VM/DB access in this
  investigation) but is a known, already-cited failure class — `plan_health.py`'s own `dispatch()` docstring notes the
  pre-sharding unsharded design measured "7 of 8 daily attempts reaped-stale" and sharding was adopted specifically to
  shrink the blast radius, not eliminate the underlying death mode. (2) The actual SYSTEMIC bug, confirmed by code
  reading: `agent-orchestrator`'s dead-session reaper (`tmux_pruner.py`, `exit_reason="reaped-stale"`) operates entirely
  on AO's own DB tables (`AgentRow`/`SlotRow`) and has zero knowledge of, or interaction with, the PM repo's markdown
  frontmatter — so even a confirmed, correctly-detected dead session never triggers any release of the `locked_by:`
  field the worker itself stamped on its PM-repo findings doc. No TTL, heartbeat, or dead-session correlation of any
  kind exists for this specific lock type anywhere in either repo. Combined with the skill's deliberate "never
  auto-unlock" policy (`locked_by:` is designed to mean "a person must say `[unlock-plan]`"), a dead run's lock is now
  provably permanent until a human notices and intervenes — today that only happens when a LATER audit run happens to
  read the doc and files an incidental FYI, sometimes days later.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [agent-orchestrator, plan_reconciler, scheduled-jobs, locked_by, stale-lock, self-healing, dead-session, ttl]
related:
  [
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /plans/active/issues/plan_reconciler_findings_ci_2026_08_10.md,
    /plans/active/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md,
    /plans/active/issues/ag_closeout_audit_tradfi_parked_2026_08_10.md,
    /plans/active/issues/safe_doc_push_isolation_drops_rename_deletions_2026_08_10.md,
    /plans/archive/issues/one_shot_worker_completes_but_no_clean_exit_signal_watchdog_rekicks_2026_07_25.md,
    /codex/04-architecture/agent-orchestrator-scheduled-jobs.md,
  ]
created: "2026-08-12"
author: unknown
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: design
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.6
assigned_role: backend_engineer
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
source:
  "Operator-dispatched investigation, 2026-08-12: why did the 4 `plan-reconciler.timer` 2026-08-09 tranche dispatches
  (defi/cefi/ci/cross_cutting) die mid-flight with zero forward progress, leaving their findings docs locked_by:
  plan_reconciler with no self-healing since? Someone else is handling the doc-level unlock+archive of the 4 dead-run
  docs themselves (operator-approved) — this doc is the root-cause + systemic-fix write-up only."
context_scope:
  [
    agent-orchestrator/server/plan_health.py,
    agent-orchestrator/server/autospawn.py,
    agent-orchestrator/server/tmux_pruner.py,
    agent-orchestrator/scripts/install-plan-reconciler-timer.sh,
    /codex/04-architecture/agent-orchestrator-scheduled-jobs.md,
    unified-trading-pm/cursor-configs/skills/plan-reconcile/SKILL.md,
  ]
depends_on: []
---

# plan_reconciler dead-run lock has no TTL / self-healing — 4 of 10 tranches stuck on 2026-08-09, recurring pattern

## Evidence

1. **The 4 dead 2026-08-09 runs** (out of scope to touch directly, per operator instruction — someone else owns their
   unlock/archive): `plan_reconciler_findings_defi_2026_08_09.md` (`locked_by: plan_reconciler`, no dispatch-id/ts
   recorded — itself a hygiene gap, see finding 5), `plan_reconciler_findings_cefi_2026_08_09.md` (same, no
   dispatch-id/ts), `plan_reconciler_findings_ci_2026_08_09.md`
   (`locked_by: plan_reconciler (agt-04cb0e) since 2026-08-09T16:22:00Z`),
   `plan_reconciler_findings_cross_cutting_2026_08_09.md`
   (`locked_by: plan_reconciler (agt-627fc7) since 2026-08-09T16:00:00Z`). All 4 show zero commits/forward-progress
   since their initial creation, confirmed dead (no live process, no git activity).
2. **Not a one-off — the identical pattern recurs in the corpus's own subsequent audit passes**, each time noted only as
   an incidental "FYI," never escalated or fixed:
   - `plan_reconciler_findings_ci_2026_08_10.md` (the very next day's ci-tranche run) explicitly flags its own
     predecessor (`…_ci_2026_08_09.md`) as dead: "only 2 commits ever landed against it (start + one checkpoint) and
     several sections left `(pending)` — it appears to have died mid-flight before reaching STEP 7 (the '7 of 8 daily
     attempts reaped-stale' failure mode the sharded-dispatch design itself cites)," and separately notes an unrelated
     "Blocked-question answer retrieval may have a real gap" finding that raises "worth checking whether OTHER
     plan_reconciler/na-eligibility-audit runs' blocked-questions have silently never received their answers either."
   - `ag_closeout_audit_tradfi_parked_2026_08_10.md` independently found `plan_reconciler_findings_tradfi_2026_08_09.md`
     dead-locked (`agt-642862`) the same day as the 4 docs this investigation covers — a 5th tranche hit on the SAME
     2026-08-09 fire, just not in the operator's named list of 4 (possibly already resolved by the time this
     investigation ran — see `safe_doc_push_isolation_drops_rename_deletions_2026_08_10.md` below).
   - `safe_doc_push_isolation_drops_rename_deletions_2026_08_10.md` records that BOTH `…_2026_08_06.md` and
     `…_tradfi_2026_08_09.md` "each still carried their lock" at investigation time, and were eventually resolved only
     via an explicit operator `[unlock-plan]` grant — i.e. the ONLY resolution path that exists today is a human
     manually noticing and approving an unlock, per doc.
3. **`TimeoutStartSec=6000` on `plan-reconciler.service` does not explain the deaths** — traced the full call chain: the
   timer's dispatch script `curl`s `/api/plan-health/dispatch` (`--max-time 5950` per tranche, batches of 4 concurrent);
   `plan_health.dispatch()` (`server/plan_health.py`) calls `autospawn.do_spawn()` and returns immediately once it
   succeeds — no polling loop for worker completion exists in `dispatch()`. `_do_spawn`'s own docstring
   (`server/autospawn.py:1896`): "On success, the tmux session exists and the boot prompt has been pasted. The SlotRow
   is NOT updated here — the spawned worker's first /heartbeat or /boot will update it" — i.e. the HTTP response (and
   therefore the curl call, and therefore the systemd service) returns once the worker's tmux session boots (bounded by
   "the ~120s boot-readiness ceiling" per a nearby comment), not once the tranche's reconciliation actually finishes.
   This is corroborated by the codex SSOT itself (`agent-orchestrator-scheduled-jobs.md`): "A row labelled `dispatched`
   is a SPAWN RECEIPT, not a completion." **This directly contradicts `install-plan-reconciler-timer.sh`'s own header
   comment**, which asserts "each POST to `/api/plan-health/dispatch` blocks synchronously for that tranche's FULL
   worker run (confirmed 2026-07-24 against plan-reconciler/docs-reconciler: the handler blocks on autospawn.do_spawn(),
   not just a boot-confirmation)." That claim could not be corroborated against the current code and appears stale —
   filed as finding 4 below rather than silently left, per the misleading-doc HARD RULE. Practical upshot: the spawned
   tmux worker runs fully independently of the timer's oneshot systemd service once spawned — killing/timing-out the
   dispatch service (if it ever did) would NOT kill the worker, and conversely the worker dying does not get reported
   back through the dispatch script at all (it already returned minutes earlier). **Per-tranche timeout sharing the
   whole-corpus 6000s budget (investigation lead 1) is therefore RULED OUT as the root cause.**
4. **Secondary finding — likely-stale doc comment** (fix-in-same-turn candidate, but deferred to the O tag below since
   it's inside a shipped, symlinked installer script rather than a passive doc): `install-plan-reconciler-timer.sh`'s
   claim that the dispatch POST "blocks synchronously for that tranche's FULL worker run" is not supported by the
   current `dispatch()`/`_do_spawn()` code path (see finding 3). Either the code changed since the 2026-07-24
   confirmation cited, or the original confirmation was itself measuring something else (e.g. wall-clock including the
   ~120s boot wait, mistaken for full-run blocking). Flagged, not fixed directly — the install script is a live,
   symlinked-across-repos systemd unit generator; a comment-only correction there is safe and small but is bundled into
   the todo below rather than edited out-of-band by an investigation task with no code-change mandate.
5. **The actual systemic root cause, confirmed by code reading (investigation lead 3)**: `agent-orchestrator`'s
   dead-session reaper — `server/tmux_pruner.py`, which sets `AgentRow.exit_reason = "reaped-stale"` on a confirmed-dead
   tmux session — operates **entirely within `agent-orchestrator`'s own SQLite state** (`AgentRow`, `SlotRow`). It has
   no code path that reads or writes `unified-trading-pm` repo files at all. The PM-repo
   `locked_by: plan_reconciler (agt-xxxxxx) since <ts>` frontmatter field is set and cleared **exclusively by the
   worker's own prose-instruction skill steps** (`cursor-configs/skills/plan-reconcile/SKILL.md`) — there is no wrapping
   process, signal handler, or `finally`-equivalent, because the "worker" is an LLM agent following markdown
   instructions inside a tmux pane, not a supervised OS process with structured exit hooks. When the agent's session
   dies mid-run (crash, OOM, context exhaustion, quota cutoff, or anything else) BEFORE it reaches its own documented
   STEP 7 unlock+commit, nothing else in either repo ever performs that step on its behalf. Compounding this: the
   skill's own design is explicit that `locked_by:` must **never** be auto-cleared by any worker ("`locked_by:` is a
   person saying 'not yours' — `[unlock-plan]` is theirs to give") — so even a hypothetical future worker that could
   positively confirm a predecessor's session is dead is still barred from clearing the lock itself under the current
   policy. **The absence of ANY correlation between AO's own accurate reaped-stale detection and the PM-repo lock — even
   just for ALERTING, let alone auto-clearing — is the systemic bug**, not the specific trigger that killed these 4
   sessions.
6. **Data-quality gap found in passing**: 2 of the 4 dead docs (`…_defi_2026_08_09.md`, `…_cefi_2026_08_09.md`) carry
   only the bare literal `locked_by: plan_reconciler` with no `(agt-xxxxxx) since <ts>` suffix — unlike the other 2 and
   every other genuine lock cited above. This makes even a manual dead-session correlation impossible for those 2 docs
   (no dispatch id to look up, no timestamp to judge staleness against). Whatever fix is chosen below should also ensure
   the worker's own lock-stamping step always includes the dispatch id + timestamp (the skill likely already intends
   this — worth a quick skill-doc check for why 2 of 4 runs skipped it).

## Why this is a design decision, not a mechanical fix

A "SMALL SAFE mechanical fix" was considered and rejected: any fix that actually closes the gap requires deciding
**whether a provably-dead worker's own self-lock may ever be auto-cleared**, which is exactly the same category of
question already sitting open, unresolved, and explicitly operator-gated in the sibling doc
`locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md` (Option A/B/C, todo 1: "[OPERATOR] P1. Rule which
option … applies"). That doc's own precedent is that even a clearly-nonsensical `locked_by` value (a branch name,
`locked_since` predating the doc's own `created` date) was NOT auto-cleared by the worker that found it — the operator
was asked directly, every time. Building a new automatic-unlock mechanism for THIS lock type without that same ruling
would be inconsistent with an already-established, deliberately conservative corpus norm. A narrower, non-unlock
alerting-only mechanism is possible without a policy change (see Option B below) but still requires design choices (what
staleness threshold, what correlation signal, which repo owns the sweep) that are better made explicitly than guessed
into a "small" patch.

## Recommendation

**Option A (broader)**: build a periodic sweep (either AO-side, since it has the live dead-session truth, or a PM-side
hygiene script that calls a new read-only AO endpoint) that cross-references every
`locked_by: plan_reconciler (agt-xxxxxx) since <ts>` in `plans/active/issues/` against AO's `AgentRow.exit_reason`. When
the dispatch id resolves to `exit_reason="reaped-stale"` (or the agent is simply gone with no live tmux session) AND
`locked_since` is older than some generous multiple of the tranche's expected runtime (the sharded design targets well
under 2h per the timer's own `TimeoutStartSec` margin — a threshold like 6-12h would clear same-day dead locks without
racing a still-legitimately- running worker), **auto-clear the lock**. Argument for treating this as safe despite the
"never auto-unlock" norm: a worker's OWN self-stamped progress-lock, positively correlated to a dispatch id AO's own
state confirms is dead, is a categorically different claim than an ambiguous/human-intended `locked_by:` — this is the
same distinction the sibling placeholder-lock doc's Option A argues for a different (but structurally similar) case.
Still needs an explicit operator ruling before implementation, per that same precedent.

**Option B (narrower, no policy change)**: do NOT auto-clear anything. Add only a staleness-detection sweep (same
correlation as Option A) that fires a Slack alert / files a same-day flag when a `plan_reconciler` self-lock is
confirmed dead — closing the "only discovered incidentally by the next day's audit, sometimes days later" gap without
touching the never-auto-unlock policy at all. Strictly additive, lowest risk, but still requires deciding the alerting
channel/threshold and who builds the AO↔PM correlation, so it's an [OPERATOR]-scoped design choice, not a blind patch.

**Option C**: leave as-is; rely on incidental discovery by the next audit pass (today's actual behavior). Not
recommended — already measured to let locks sit for days (`…_ci_2026_08_09.md` was still locked as of the 2026-08-10
run, i.e. ≥18h, and per this investigation, ≥3 days by 2026-08-12).

## Todos

- [ ] [OPERATOR] P2. Rule which option (A/B/C) above applies for closing the plan_reconciler dead-run lock gap, or a
      different approach. If A or B: also rule on the staleness threshold and which repo/service owns the AO↔PM-repo
      correlation sweep.
- [ ] [INFRA] P3. Once ruled: fix the likely-stale "blocks synchronously for that tranche's FULL worker run" claim in
      `agent-orchestrator/scripts/install-plan-reconciler-timer.sh`'s header comment (finding 4) — either re-confirm it
      against a live measurement first, or correct it to describe the actual "spawn receipt, not completion" behavior
      the codex SSOT already documents, so a future reader doesn't inherit the same wrong mental model this
      investigation had to disprove from code.
- [ ] [INFRA] P3. Once ruled: audit why 2 of the 4 dead 2026-08-09 docs (`…_defi_…`, `…_cefi_…`) stamped a bare
      `locked_by: plan_reconciler` with no `(agt-xxxxxx) since <ts>` suffix (finding 6) — a genuine dead-session
      correlation needs the dispatch id + timestamp on every run's lock-stamping step, not just most of them.

## Progress Log

- **2026-08-12** — Filed per operator-dispatched investigation into why 4 `plan-reconciler.timer` 2026-08-09 tranche
  dispatches (defi/cefi/ci/cross_cutting) died mid-flight leaving permanent `locked_by: plan_reconciler` locks. Ruled
  out the systemd `TimeoutStartSec`/per-tranche-timeout-sharing hypothesis via code reading (finding 3) — dispatch is a
  spawn receipt, not a completion-blocking call, so the timer's own timeout cannot be what killed these sessions.
  Confirmed the actual systemic gap: AO's dead-session reaper has zero interaction with PM-repo file state, so even
  correct dead-session detection never propagates to a lock release, and the skill's own explicit never-auto-unlock
  policy means nothing else does either (finding 5) — corroborated by the same pattern recurring, undetected until
  incidental next-day audit FYIs, across at least 3 other dated findings docs (finding 2). Not implemented directly:
  closing the gap requires an operator ruling on whether a positively-dead worker's OWN self-lock may ever auto-clear,
  matching the precedent already set (and still open) in the sibling
  `locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md` doc. The 4 named 2026-08-09 docs themselves are
  explicitly out of scope for this doc (a separate session owns their unlock/archive per operator instruction).
