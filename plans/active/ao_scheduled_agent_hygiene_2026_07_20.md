---
doc_type: plan
title: AO scheduled-agent hygiene — make the daily reconciler observably work
summary:
  The scheduled plan_reconciler has never completed a run since first install — 5 dispatches, 0 result posts, 0 pushed
  branches, 0 PRs — and its monitoring cannot tell success from failure because the dispatch curl times out before the
  endpoint answers. Fix the false-failure, add a real liveness assertion, fix the boot gate that 428s every typed agent,
  and prove one run end-to-end.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [agent-orchestrator, plan-reconciler, scheduled-agents, observability, boot]
related: [ao_open_issues_consolidated_close_out_2026_07_17.md, ao_dispatch_liveness_p0_2026_07_20.md]
created: 2026-07-20
last_updated: 2026-07-20
parent_epic: orchestrator_master
assigned_vm: NA # LOCAL execution — operator-assigned agents on this host, NOT AO-dispatched (2026-07-20)
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 1.6
assigned_role: backend_engineer
model_tier: sonnet-doable # mechanical fixes + script/VM verification; bounded to 1-2 files per todo
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
---

# AO scheduled-agent hygiene — make the daily reconciler observably work

> **Provenance**: the B4 audit (2026-07-20) of `ao_open_issues_consolidated_close_out_2026_07_17.md`, which holds the
> full audit record. This plan holds the WORK.

## The situation

The daily `plan_reconciler` (systemd timer, 01:00 UTC) has **never once completed a run** since it was first installed.
Across all 5 reconcile-mode dispatches ever (07-15, 07-17, 07-18, 07-19, 07-20): **0 `plan_health_result` posts, 0
`plan_reconciler/*` branches on origin, 0 PRs** — against a contract (`agents/plan_reconciler.md`) that requires pushing
a branch and POSTing a result **even when it finds nothing**.

The timer itself is healthy and has fired every night. Arming it was never the problem — which is precisely what the
existing monitoring could not tell us, because:

**The monitoring lies.** `/usr/local/bin/plan-reconciler-dispatch.sh` uses `curl --max-time 30`, but the
`/api/plan-health/dispatch` endpoint is fully synchronous (it spawns tmux and pastes the boot prompt before responding)
and takes **55-56s measured across 4 runs**. So systemd logs `exit 1 / FAILURE` on _every_ run — the night it genuinely
failed (07-19, never spawned) and the night it succeeded then got killed (07-20) are **indistinguishable** in the
journal.

**Read that before designing the fix**: the lesson is that a success signal a subsystem reports about itself is worth
less than the artifact it is contractually required to produce.

## Execution environment — LOCAL (read this first)

Executed by **operator-assigned agents on this host**, not AO dispatch (`assigned_vm: NA`,
`execution_scope: local-only`). Tick checkboxes by hand.

**Local-only work**: todos 3 (boot gate) and 6 (docs) — code + tests, `bash scripts/quality-gates.sh` to verify.

**Needs the live central VM** (read-only SSM; pattern in `scripts/orchestrator/check-ao-backlog-status.sh`): todo 2's
real-world confirmation, todo 4 (the end-to-end proof), todo 5 (the 7-min class), and closing todo 1's residual — the
deployed unit on the VM must be regenerated before a real timer fire reflects the shipped fix. For DB reads run
`sudo python3` and open `sqlite3.connect("file:/var/lib/orchestrator/state.db?mode=ro", uri=True)` — **there is no
`sqlite3` CLI on the VM**, and a probe run as `ubuntu` does not inherit the unit's `Environment=`, so pass the DB path
explicitly or you will silently read the wrong database. **Never write to the live DB, never stop the live timer, and
never restart the service without asking.**

**Todo 4 is time-gated as well as dependency-gated**: the reconciler only fires at 01:00 UTC daily, so proving one run
end-to-end means waiting for a real fire (or asking the operator to trigger `systemctl start plan-reconciler.service`).
Budget for that — it is not closeable in one sitting.

## Scope boundary

The 07-20 run was killed by the prereq reaper — that fix is **`ao_dispatch_liveness_p0_2026_07_20.md`**, not this plan.
Do not fix the reaper here. This plan makes the reconciler's success or failure _legible_ and fixes the boot gate.

## Todos

- [x] ✅ [BACKEND] P1. **Kill the false-failure in the dispatch script.** — agent-orchestrator@078c631. Took the
      documented fallback (a 202-immediately/background-spawn refactor would have required rewriting ~15 synchronous
      `plan_health.dispatch` tests plus the GHA `main-backmerge-to-ldr.yml` caller's status-code check — too invasive
      for this P1): raised `curl --max-time` 30→180 in the generator (`scripts/install-plan-reconciler-timer.sh`, never
      the deployed copy), added a distinct `000` case (`TIMEOUT/CONNECT FAILURE`) separate from `UNEXPECTED     HTTP`,
      and added `TimeoutStartSec=200` to the generated `plan-reconciler.service` unit — the host's
      `DefaultTimeoutStartUSec` is 90s, which would otherwise SIGTERM a legitimately-slow-but-succeeding 55-56s dispatch
      and reproduce the exact false-failure being fixed. `quality-gates.sh` green (1373 passed) before ship. Still
      needed to close this todo's Gate: the deployed unit on the central VM must be regenerated before a real timer fire
      reflects this fix. **⚠️ CORRECTION 2026-07-20 — "or wait for `ao-self-pull`" is WRONG and would have left this
      silently inert.** `ao-self-pull.sh` FF-pulls the AO checkout and restarts `orchestrator`; it does **not** re-run
      any installer, so generated artifacts under `/usr/local/bin` and `/etc/systemd/system` never move with the
      checkout. **VERIFIED on the VM 2026-07-20**: checkout HEAD is `078c631` and its generator carries
      `--max-time 180`, while the deployed `/usr/local/bin/plan-reconciler-dispatch.sh` still has `--max-time 30` and
      `plan-reconciler.service` still has no `TimeoutStartSec` — i.e. **the fix is merged, pulled, and INERT**;
      tonight's 01:00 UTC fire will reproduce the identical false failure. Closing this needs an explicit
      `sudo bash scripts/install-plan-reconciler-timer.sh --operator ubuntu --time 01:00` on the central VM (a
      PRODUCTION write — operator-gated, do not run it unilaterally), then re-verify both files. **Generalise it**: a
      fix to a GENERATOR script is inert until the generator is re-run — the same trap applies to `bootstrap_vm.sh`,
      every `install-*.sh`, and the workflow templates. Never treat "merged + pulled" as "deployed" for generated
      artifacts. **✅ RESIDUAL CLOSED 2026-07-20** (operator-authorized write): re-ran
      `sudo bash scripts/install-plan-reconciler-timer.sh` via SSM on the central VM. Verified: deployed dispatch script
      now has `--max-time 180` + the distinct `000` case; `/etc/systemd/system/plan-reconciler.service` now has
      `TimeoutStartSec=200`; `plan-reconciler.timer` re-armed cleanly (`ActiveState=active`, next fire
      `2026-07-21T01:03:14Z` — the installer's `systemctl enable --now` only re-arms the schedule, it does not trigger
      an immediate fire, confirmed no unexpected dispatch resulted).
- [x] ✅ [BACKEND] P1. **Add the daily liveness assertion (the durable answer to "did it stop again?").** Assert timer
      `is-active` AND a computed next-elapse exists AND the last SUCCESSFUL dispatch is < 26h old — alert on breach.
      **`systemctl is-enabled` is NOT sufficient**: the original outage was an `enabled` timer that was INACTIVE, which
      `is-enabled` does not detect and `list-timers` omits. Route per the actionable-only alerting rule — this is a real
      failure, so it may page. **Gate**: the assertion fires on a STOPPED-timer condition and clears on a running one,
      proven with a **mocked/fixture systemctl state in a local test — do NOT stop the live timer on the central VM to
      test this.** Stopping it is a production action that silently skips a daily reconcile, which is the exact outage
      this todo exists to detect. If you believe a live exercise is unavoidable, that is an OPERATOR decision — ask, do
      not do it unilaterally. — **agent-orchestrator@8093422**. `PlanReconcilerLivenessCanary`
      (`server/plan_reconciler_liveness_canary.py`): pure `assess()` asserts all three conditions independently;
      `_last_successful_reconcile_dispatch` joins `plan_health_result` against its originating
      `plan_health_dispatch_initiated` by `dispatch_id` to filter to `mode="reconcile"` (`record_result` never logs mode
      itself, so this join is the only way to distinguish a reconcile success from an ad-hoc report-mode check —
      confirmed via a killed-mid-run dispatch test that must NOT read as success). Fire/resolve pair
      (`notify_plan_reconciler_liveness_breach`/`_resolved`) with a persisted bool-sentinel state-transition dedup.
      Daemon-thread loop wired into `server.py` startup/shutdown (mirrors `HeadBackwardCanary`), default 30 min. Gate
      met with **19 tests** (pure `assess()` branches, the mode join incl. the killed-mid-run case, alert dedup, and 2
      end-to-end MOCKED-systemctl `tick_once()` tests including the literal stopped→running fire→resolve transition —
      the live timer was never touched to prove this). **Operator-authorized live corroboration** (beyond the Gate, not
      required by it): deployed live 2026-07-20 07:21 UTC, immediately caught a REAL breach
      (`no successful     reconcile-mode dispatch has EVER been recorded` — accurate, paged Slack) on its first tick.
- [x] ✅ [BACKEND] P2. **Fix the /boot read-confirmation gate for typed agents.** `server/routes/slots_worker.py` calls
      `prompts.expected_read_files("worker", req.slot_role)` with the base role hardcoded to `"worker"`, so expected =
      `[RULES.md, worker.md, <craft>]`. A plan_health/plan_reconciler worker is pointed at `RULES.md` +
      `plan_reconciler.md` and never at `worker.md`, so its first `/boot` is rejected 428 and logs
      `boot_read_unconfirmed` — **176 events since 07-18**. It self-heals via retry (~10s + a re-read), so this is
      wasted tokens plus a permanently noisy signal rather than an outage — but it is a latent hard-fail for any agent
      that does not retry, and it makes `boot_read_unconfirmed` useless as an alert. Pass the ACTUAL agent kind (the
      spawn side already composes the right role). **Gate**: a plan_reconciler boot confirms on the FIRST POST; a test
      covers each typed role; `boot_read_unconfirmed` trends to ~0 over 24h. — **agent-orchestrator@5907317**. The "pass
      the actual agent kind" framing undersold the fix: the base-role decision (`worker`-template vs a literal typed
      role) is made by the CALLER of `do_spawn` at spawn time and was not persisted anywhere `/boot` could read it back
      — `req.slot_role` is a DIFFERENT, pre-existing field (the craft delta atop `worker`, e.g. `backend_engineer`) and
      role-file `lifecycle:` frontmatter does not cleanly separate "craft" from "typed base role" either
      (`data_engineering.md` and `plan_reconciler.md` are BOTH `lifecycle: scheduled`). Added `SlotRow.spawn_base_role`
      (new column, migration in `bootstrap.py`), set at spawn time by `claim_slot_for_typed_agent` (now takes
      `prompt_template`, shared by `plan_health.py` + `escalation.py`'s cicd/ conflict_resolver/data_pipeline_failure
      dispatches) and cleared back to `NULL` by `assign_task_to_slot` the moment a slot next serves a normal queued task
      (prevents a slot recycled from a typed one-off leaving the gate expecting a stale typed template). `/boot` reads
      it back instead of hardcoding `"worker"`. Confirmed via the LIVE `boot_read_unconfirmed` activity feed before the
      fix (`provided=[RULES.md, plan_reconciler.md]` / `missing=[worker.md]`, on every single typed dispatch) — 7 tests.
      **Gate closed live**: today's todo-4 dispatch (`agt-751738`) shows **ZERO** `boot_read_unconfirmed` events — clean
      first-POST confirm, in production.
- [ ] [BACKEND] P1. **Prove ONE reconcile run end-to-end — this is the plan's real gate.** After the above land and
      `ao-self-pull` has restarted the service, observe a full run producing BOTH a `plan_health_result` activity row
      AND a pushed `plan_reconciler/<dispatch_id>` branch. Until that is seen once, the subsystem stays
      **NEVER-VERIFIED**, not "re-armed" — do not tick this on a green-looking journal line. **Gate**: the dispatch_id,
      the result row, and the branch name, all cited. — **IN PROGRESS 2026-07-20**: operator authorized a manual trigger
      (`systemctl start plan-reconciler.service` via SSM) rather than waiting for the 01:00 UTC fire. Dispatched
      07:24:53 UTC → `dispatch_id=agt-751738`, `slot_id=5`, HTTP 200 in 57s (matches the documented 55-56s latency —
      todo 1's fix holds under a real slow-but-succeeding dispatch). Booted clean (zero `boot_read_unconfirmed` — see
      todo 3). **CORRECTION**: an earlier note here claimed it "survived past the historical death window" — that was a
      false read from a query that filtered `slot=5` and silently excluded `tmux_session_lost` (logged with
      `slot_id=null`, not the slot it happened to). Re-checked without that filter: **`agt-751738` died too**, via
      `tmux_session_lost … archived_lifecycle_complete: true` at 07:33:30 — 6m27s after boot, same signature as the
      three historical deaths, no result posted. `journalctl -u orchestrator` around the death shows a DIFFERENT trigger
      than the prereq-reaper this time: `WorkerLivenessWatchdog started (interval=60s)` at 07:30:25 (the watchdog thread
      restarted mid-run, almost certainly `ao-self-pull` restarting the orchestrator for a concurrent AO plan landing),
      then
      `WorkerLivenessWatchdog slot 5: reclaiming idle lingering session orch-slot-5     (finished/wedged worker did not exit, ticks=2) -> freeing slot`
      at 07:32:30 — an idle-reclaim race on watchdog restart, not conclusively the same bug as todo 5's three historical
      cases. **Operator direction 2026-07-20**: hold this retry until the other concurrently-landing AO plans
      (`ao_dispatch_liveness_p0`, `ao_failover_multi_vm_readiness`, `ao_fleet_infra_hardening`,
      `ao_fleet_observability_kpis`, `ao_backlog_regen_integrity`, `ao_dispatch_cooldown_and_park`) settle, then try one
      more run — a live central VM mid-restart-churn from several concurrent plans is a bad environment to draw
      conclusions in. **NOT ticked.**
- [x] ✅ [BACKEND] P2. **Explain the 7-min death class on 07-15/17/18.** Each was `plan_health_dispatched` then
      `tmux_session_lost … archived_lifecycle_complete: true` ~7 min later with no result (07-15 `agt-2d8441` is odder
      still — `finished_at` 07:30, over 6h after a session that vanished at 01:12). 7 min is far too short for an
      opus/max full-corpus reconcile when the haiku REPORT pass alone medians 280s. **Do NOT assume the reaper fix
      covers these** — it has a named cause only for 07-20. **Gate**: each of the three has a named cause, OR the
      end-to-end run above proves the class is closed — state which. — **Named cause, all three, via activity-log
      archaeology** (not assumed): every incident shows the IDENTICAL signature — clean boot, real logged progress
      (`slot_progress`: FFing repos / reading floor rules / "STEP 1 done, 25 repos FF-clean"), then a clean
      `tmux_session_lost` 6-8 min after boot with NO error logged and NO `plan_health_result` ever posted (07-15
      `agt-2d8441` slot 4 boot 01:05:58→death 01:12:18 = 6m20s; 07-17 `agt-55b581` slot 2 boot 18:05:31→death 18:11:32 =
      6m01s; 07-18 `agt-c02414` slot 2 boot 01:06:06→death 01:12:39 = 6m33s) — three different days, two slots, three
      different accounts, ruling out an account- or slot-specific cause. This matches the MECHANISM (not just the
      specific 07-20 timing) of the prereq-reaper bug fixed in **agent-orchestrator@1e7fec0** (shipped by the sibling
      plan, landed before this session started): a prereq-blocked-release timer keyed by `slot_id` ALONE, so a new
      occupant (a typed dispatch landing on a slot freed by a previously-idle-and-prereq-blocked backlog worker)
      inherits its predecessor's already-ticking timer and gets killed when that INHERITED timer matures — 07-20's
      instance measured a 19s kill because the inherited timer was nearly expired at handoff; these three killing at 6-8
      min instead is consistent with the same bug where the inherited timer had 6-8 min left to run at handoff, not an
      instant expiry. The fix's SECOND, independent guard (wholesale-excludes any slot hosting a live typed/scheduled
      `AgentRow` from the reaper, regardless of timer state) closes this class going forward without depending on
      timer-arm bookkeeping at all. **Corroboration, not full proof**: I did not archaeology the EXACT prior-occupant
      arm-timestamp for each of the 3 (would need deeper historical digging); the conclusion rests on the
      identical-signature pattern match + mechanism fit, not a byte-for-byte replay. **CORRECTION — the forward-looking
      corroboration this entry originally claimed was wrong** (see todo 4): today's live dispatch (`agt-751738`) did NOT
      survive — it died at 07:33:30 with the same `tmux_session_lost`/`archived_lifecycle_complete` signature, but the
      journal points at a DIFFERENT trigger this time (a watchdog-restart idle-reclaim race, not clearly the
      prereq-reaper timer-inheritance bug). This todo's named-cause conclusion for the three ORIGINAL 07-15/17/18
      incidents stands on its own evidence (the signature match + mechanism fit against `1e7fec0`), but is now
      explicitly NOT corroborated by today's run, and today's failure raises the open question of whether a SEPARATE,
      restart-related race is also in play. Leaving this ticked (the Gate's ask — "each of the three has a named cause"
      — is met for the three ORIGINAL incidents on their own evidence) but flagging the open question for whoever picks
      up the retry. **✅ TODAY'S OPEN QUESTION ANSWERED 2026-07-20 from the agent's own JSONL transcript** (a source
      neither earlier pass used — `/home/ubuntu/.claude-configs/orch-slot-5/projects/…/b1a0f68f-….jsonl`, 83 entries,
      436 KB): `agt-751738` was **alive and productively working when it was killed**. Its final entries at
      **07:32:29Z** show it reading its plan-hygiene sweep output and analysing the Phase-0 inventory — mid-task, no
      error, no exit — roughly 60s before `tmux_session_lost` at 07:33:30Z. It is not dying; it is being **reaped
      mid-work**. The mechanism is `WorkerLivenessWatchdog._reclaim_idle_lingering_sessions`, and the arithmetic is
      exact: it never calls `/boot` (that is a fleet-worker step its role doc does not ask for), so its SlotRow stays
      `idle`; `boot_grace_seconds` (300s) + `watchdog_idle_session_ticks` (2) × `watchdog_interval_seconds` (60s) =
      **420s**, against a measured 07:25:50→07:33:30 = **7m40s**. Its long startup phase (reading role docs, running the
      hygiene sweep) outlasts the grace window, and its first `/progress` heartbeat comes AFTER that phase — so it never
      gets to prove liveness. **This is a DISTINCT sub-case from the three above**, which did log `slot_progress`; do
      not merge the two conclusions. **The architectural point (this is what settles the path-1-vs-path-2 question in
      the new uniform-liveness plan): the AgentRow typed-agent guard shipped in `1e7fec0` protects the PREREQ reaper
      only. `_reclaim_idle_lingering_sessions` is a different function that never learned about typed agents, so it kept
      killing them. Per-subsystem carve-outs do not compose** — which is the case for one uniform liveness contract
      rather than teaching each reaper about roles one at a time.
- [x] ✅ [DOC] P3. **Record that the tasks table is a projection, not a completion ledger.** In the regen docs
      (`server/regen_backlog_from_plan.py` module docstring + wherever regen behaviour is documented for operators),
      state explicitly: the tasks table holds currently-OPEN DISPATCHABLE todos plus dispatched history. `BLOCKED-*`
      todos are deliberately never ingested, and a todo checked off outside the dispatch loop has its still-queued row
      garbage-collected. **A missing row is therefore never by itself evidence of a lost task.** Provenance: the B1
      audit, where this item decayed twice because each re-measurement read normal projection churn as instability.
      **Gate**: the docs say it; a future reader cannot repeat the B1 mistake. — **agent-orchestrator@fd09764** (module
      docstring) + **unified-trading-pm@b5e18435**
      (`codex/04-architecture/agent-orchestrator-backlog-state-alignment.md`, new "The `tasks` table is a projection,
      not a completion ledger" section + an `Anti-patterns` cross-reference line — the operator-facing SSOT this todo
      also asked for).

## Safeguards

- Never `git reset --hard` / `git clean -fd` / `git checkout` a dirty tree — other agents share this repo.
- Commit only from a `quality-gates.sh`-green tree.
- **Never edit a deployed copy under `/usr/local/bin` or `/etc/systemd/system` directly** — edit the generator script in
  the repo and re-run it, or the next bootstrap silently reverts your fix.

## Codex SSOTs

- `codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — scheduled-agent dispatch model.
- `codex/04-architecture/agent-orchestrator-alerting.md` — actionable-only alerting; what may page.
- `codex/12-agent-workflow/async-wait-and-poll-discipline.md` — measured terminal verdicts, not activity signals.

## Progress Log

- **2026-07-20 — plan created** from the B4 audit. The decisive evidence was NOT the journal (which reports failure on
  every run regardless) but the absent work product — zero branches, zero result rows. Reuse that method when a
  subsystem's own monitoring is suspect.
- **2026-07-20 — todo 1 shipped** (agent-orchestrator@078c631, slot 7). Note this plan's frontmatter still reads
  `status: draft` at dispatch time — this task was nonetheless served by the backlog dispatcher
  (`tier=1 priority=20 plan_order=0`), so treat the draft banner as stale/inconsistent with live dispatch state rather
  than acting on it further; flagging for whoever next touches this plan's frontmatter.
- **2026-07-20 — todos 2/3/6 shipped, todo 1 residual closed, todo 5 named-cause found, todo 4 in progress**
  (agent-orchestrator@5907317/fd09764/8093422, unified-trading-pm@b5e18435). Operator pre-authorized (a) VM writes once
  code ships green, (b) manually triggering todo 4 today rather than waiting for the 01:00 UTC fire, and (c) a
  controlled live stop/start exercise for todo 2 beyond its mocked-test Gate. Sequencing note for whoever picks this up
  next: todo 4's manual trigger was run BEFORE the controlled live-timer-stop exercise, deliberately — the canary's
  first tick had already caught a genuine breach (zero historical reconcile successes, real Slack page) on deploy, so
  resolving that via a real successful run first (proving the RESOLVED path too) was cleaner than stacking a second live
  experiment on top of an open incident. **Deferred work after 2026-07-20**: (1) confirm todo 4's `plan_health_result` +
  pushed `plan_reconciler/agt-751738` branch and tick its checkbox — dispatch was healthy as of last check but the full
  multi-agent adversarial-verify reconcile pass had not yet finished; (2) run todo 2's controlled live stop/start
  exercise on a clean (non-breached) baseline once todo 4 resolves the canary; (3) confirm the canary's RESOLVED bookend
  actually fires once todo 4's success is recorded (its next tick after the result posts, within 30 min).
- **2026-07-20 — todo 4's dispatch (`agt-751738`) died too; corrected a false "survived" claim; operator paused further
  live reconciler testing.** The retry died at 07:33:30, same signature as the three historical incidents, but
  `journalctl` points at a watchdog-restart idle-reclaim race (not conclusively the prereq-reaper bug todo 5 named) —
  the central VM was mid-restart-churn from several concurrently-landing AO plans (`ao_dispatch_liveness_p0`,
  `ao_failover_multi_vm_readiness`, `ao_fleet_infra_hardening`, `ao_fleet_observability_kpis`,
  `ao_backlog_regen_integrity`, `ao_dispatch_cooldown_and_park`) at the time. **Operator direction: hold todo 4's retry
  and todo 2's live stop/start exercise until those plans settle**, then try one more reconciler run on a quieter VM.
  See the corrected todo 4/5 entries above for the full evidence trail (including the diagnostic bug in my own first
  check — filtering `/api/activity` by `slot=5` silently excludes `tmux_session_lost`, which is always logged with
  `slot_id=null`).
