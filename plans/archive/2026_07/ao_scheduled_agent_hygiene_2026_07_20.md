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
related:
  [
    /plans/archive/2026_08/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /plans/archive/2026_07/ao_dispatch_liveness_p0_2026_07_20.md,
  ]
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
      up the retry. **⚠️ RETRACTED 2026-07-20 — a conclusion posted here earlier was WRONG and is withdrawn in full.**
      It claimed `agt-751738` was reaped by `WorkerLivenessWatchdog._reclaim_idle_lingering_sessions` because a one-off
      "never calls `/boot`, so its SlotRow stays `idle`". **Every load-bearing part of that is false** — see the
      DISPROVEN list in the new P0 investigation todo below. It was built by matching an arithmetic coincidence
      (`boot_grace` 300s + 2 ticks x 60s = 420s vs a measured 7m40s) and reasoning backwards to a mechanism that fit the
      number, without checking the slot's actual status, without looking for a reclaim event, and without checking
      whether `tmux_session_lost` is an action or an observation. It is the grep-then-conclude failure this workspace
      warns about. **The 7-min death class is NOT explained. Treat it as OPEN** — the new P0 below carries the real
      handoff. (`agent-orchestrator@f641968` was shipped on that wrong premise: it is defensively harmless and its
      regression test is real, but it did NOT fix this and its commit message's stated motivation is wrong.)
- [x] ✅ [BACKEND] P0. **ROOT-CAUSE why every plan_reconciler run dies 6-8 minutes in — SELF-CONTAINED HANDOFF, read
      this whole todo before touching anything.** You are on the central planning VM (`i-0c9b283b31d6b5ca7`), so
      everything below is LOCAL — no SSM needed.

      **SYMPTOM.** Five reconcile-mode dispatches exist for all time (07-15 `agt-2d8441`, 07-17 `agt-55b581`, 07-18
                                                                                                                                          `agt-c02414`, 07-19 `agt-722a19`, 07-20 `agt-751738`). **Zero have ever produced a `plan_health_result` row, a
                                                                                                                                          pushed `plan_reconciler/*` branch, or a PR** — against a contract (`unified-trading-pm/agents/plan_reconciler.md`
                                                                                                                                          §258/§334) that requires pushing a branch and POSTing a result even when it finds nothing. 07-19 never spawned (a
                                                                                                                                          slot race, since fixed). The other four all died 6-8 min after boot.

                                                                                                                                          **BEST-DOCUMENTED INSTANCE — `agt-751738`, 2026-07-20, slot 5.** Timeline, all from `activity_log` (payload column
                                                                                                                                          is `details_json`, NOT `detail`/`payload`):
                                                                                                                                          `07:24:53 plan_health_dispatch_initiated` → `07:25:50 plan_health_dispatched` → `07:27:03 slot_boot` (opus,
                                                                                                                                          account `sub-a-ikenna`) → `07:28:18 slot_progress` ("plan_reconciler boot: read RULES + role + sub-agent rules;
                                                                                                                                          investigating slot git state before STEP 1 FF", phase=working) → `07:33:30 tmux_session_lost`. Its JSONL
                                                                                                                                          transcript (`/home/ubuntu/.claude-configs/orch-slot-5/projects/-home-ubuntu-unified-trading-system-repos--tabs-5/b1a0f68f-a649-415f-9b46-13903afd9228.jsonl`,
                                                                                                                                          83 entries, 436 KB) has its LAST entry at **07:32:29Z** — reading its plan-hygiene sweep output, mid-task, no
                                                                                                                                          error, no exit message.

                                                                                                                                          **PROVEN.** (a) It boots normally. (b) It heartbeats at least once. (c) It was doing real work at 07:32:29. (d)
                                                                                                                                          Its session was gone by 07:33:30. (e) It produced no work product.

                                                                                                                                          **DISPROVEN — do NOT re-walk these, each was checked and killed:**
                                                                                                                                          1. *"It never calls `/boot`"* — false, `slot_boot` at 07:27:03.
                                                                                                                                          2. *"It never heartbeats"* — false, `slot_progress` at 07:28:18.
                                                                                                                                          3. *"`_reclaim_idle_lingering_sessions` reaped it"* — no reclaim event exists for slot 5 in the window, and the
                                                                                                                                             reclaimer needs 2 consecutive idle/stale ticks it never had. The `boot_grace 300s + 2x60s = 420s` vs 7m40s
                                                                                                                                             match is an **arithmetic coincidence** — it is what produced the earlier wrong conclusion. Do not reuse it.
                                                                                                                                          4. *"`tmux_session_lost` = the orchestrator killed it"* — false. It is emitted by the TmuxPruner
                                                                                                                                             (`server/tmux_pruner.py:266`) when it DETECTS a session already gone. Observation, not action.
                                                                                                                                          5. *"An `orchestrator.service` restart killed it"* — false. `KillMode=process` (verify: `systemctl show
                                                                                                                                             orchestrator -p KillMode`), so systemd kills only the main process, never the workers — that is exactly what
                                                                                                                                             *"Unit process (claude) remains running after unit stopped"* means. Also: zero restarts within 30 min of the
                                                                                                                                             07-18 death.
                                                                                                                                          6. *"OOM"* — false, `journalctl -k` clean across the window; the box has ~23 GB available.

                                                                                                                                          **CONCLUSION SO FAR: the claude process exited on its own and nothing in the orchestrator killed it. The cause is
                                                                                                                                          genuinely UNKNOWN.**

                                                                                                                                          **WHERE TO LOOK NEXT (unchecked leads, cheapest first).**
                                                                                                                                          1. **The transcript tail past 07:32:29** — read the raw last lines of that JSONL (not just `type`/`text`; dump
                                                                                                                                             whole objects, including any `isApiErrorMessage`, `stop_reason`, `error`, or `result` records). A usage-limit
                                                                                                                                             or API error would appear here.
                                                                                                                                          2. **Account `sub-a-ikenna` usage at 07:32-07:33.** The reconciler is the ONLY spawn in the fleet using
                                                                                                                                             opus + `--effort max` + thinking-on, and both of today's runs used this account, which was simultaneously
                                                                                                                                             running ~5 plan_health workers and 3 cicd agents. Check the usage-poller data / `server/usage_tracker.py`
                                                                                                                                             records and any rotation/limit events around that timestamp.
                                                                                                                                          3. **Reproduce it directly** — spawn a reconciler manually and WATCH the pane live
                                                                                                                                             (`tmux attach -t orch-slot-N`, or `tmux capture-pane -p -S -200` on a loop) through the 6-8 min mark. This is
                                                                                                                                             the highest-information move and the cheapest way to see an error the logs never captured.
                                                                                                                                          4. **tmux server view** — `tmux show-messages`, and whether the tmux server itself restarted.

                                                                                                                                          **RULES.** Read-only until you have a cause. Never write to the live DB, never stop the timer, never restart the
                                                                                                                                          orchestrator without asking. **State plainly if you cannot establish the cause** — an honest "unknown, here is
                                                                                                                                          what I eliminated" is the required answer, and is worth more than a mechanism that merely fits the timing. Two
                                                                                                                                          confident wrong conclusions have already been posted on this exact question; both came from pattern-matching a
                                                                                                                                          number instead of verifying state.

                                                                                                                                          **Gate**: a named cause supported by evidence that survives the DISPROVEN list above, OR an explicit
                                                                                                                                          "cause not established" with the new leads eliminated and the next step named. Then update this plan AND
                                                                                                                                          `ao_uniform_agent_liveness_contract_2026_07_20.md`, whose premise depends on the answer.

                                                                                                                                      **✅ ROOT CAUSE ESTABLISHED 2026-07-20 (slot-16 interactive) — an UNGUARDED idle-lingering reclaimer reaped
                                                                                                                                      the live reconciler (fatal-blow ~90%, see the caveat in point 1), and DISPROVEN #3 above is itself WRONG.**
                                                                                                                                      Evidence is primary (journalctl + code + git), not a pattern-match on a number:

                                                                                                                                      1. **The reaper fired an unguarded `kill_session` on a live, working reconciler — this part is airtight.**
                                                                                                                                         `journalctl -u orchestrator` at **07:32:30.768** logs
                                                                                                                                         `WorkerLivenessWatchdog slot 5: reclaiming idle lingering session orch-slot-5 (finished/wedged worker did not exit, ticks=2) -> freeing slot`
                                                                                                                                         — **one second after** the transcript's last write (07:32:29). That line is emitted by
                                                                                                                                         `_reclaim_idle_lingering_sessions` (`server/worker_liveness_watchdog.py`), and the statement immediately after
                                                                                                                                         it is `kill_session(sess)` (worker_liveness_watchdog.py:1212). The DEFECT is proven independently of the exact
                                                                                                                                         kill-instant: the watchdog runs every 60s (started 07:30:25), so tick-1 landed ~07:31:25 — and the transcript
                                                                                                                                         kept writing entries through **07:32:29**, a full minute later — so the reaper was demonstrably accumulating
                                                                                                                                         ticks against a **live, actively-working** reconciler whose slot the DB had mislabeled `idle`, with no
                                                                                                                                         typed-agent exemption (precondition B). A reaper counting down to kill a live typed agent is the confirmed bug.

                                                                                                                                         **⚠️ CONFIDENCE CAVEAT (corrects an earlier over-claim in this entry).** Whether the 07:32:30 `kill_session`
                                                                                                                                         delivered the FATAL blow, vs. reaped a corpse that self-exited ~1s earlier, is **~90%, not proven**. `has_session`
                                                                                                                                         cannot decide it: worker sessions run `remain-on-exit on` (tmux_spawn.py:837), so a dead claude leaves a
                                                                                                                                         preserved zombie session that `has_session` still reports True — the reclaim's `has_session` gate (line 1182)
                                                                                                                                         therefore does NOT prove liveness at the kill. What tilts it to ~90% live-kill: the only plausible self-exit
                                                                                                                                         cause (account usage) is ruled out — sub-a-ikenna was at **5h=5%** at 07:31:09 (~80s prior) with zero
                                                                                                                                         rate-limit/429/overage/auth events in the window; OOM ruled out (journalctl -k clean); no self-exit/pane-capture
                                                                                                                                         event fired for slot 5 (only teardown events are the reclaim@07:32:30 + pruner@07:33:30); and a silent
                                                                                                                                         mid-inference stop with **no `isApiErrorMessage` in the transcript** is the signature of an external SIGHUP
                                                                                                                                         (`tmux kill-session`), not a graceful usage-limit (which writes an error turn and waits). The residual (an
                                                                                                                                         unexplained crash coinciding to the second with the reaper) has no positive evidence. Closed definitively only
                                                                                                                                         by observing the next run (R2). The `tmux_session_lost` at 07:33:30 (DISPROVEN #4) is the TmuxPruner observing
                                                                                                                                         the by-then-gone session ~60s later either way — downstream, not the cause.

                                                                                                                                      2. **DISPROVEN #3 is refuted on both clauses.** It claimed "no reclaim event exists for slot 5 in the window" and
                                                                                                                                         "the reclaimer needs 2 consecutive idle/stale ticks it never had." The journal shows the reclaim WITH
                                                                                                                                         `ticks=2`. The prior author missed it because **watchdog reclaims are logged to journalctl only — they are NOT
                                                                                                                                         written to `activity_log`**, so `/api/activity?slot=5` (the source both prior wrong conclusions leaned on)
                                                                                                                                         returns nothing for it. This reclaim is also routine: on 2026-07-19 alone it reaped slot 5 ≥8× and slot 4 many
                                                                                                                                         times **with no restart involved** — the everyday mechanism, so the 07:30 restart (DISPROVEN #5) is not required
                                                                                                                                         for it to fire.

                                                                                                                                      3. **Why it was reapable — precondition A (status).** `_reclaim_idle_lingering_sessions` only scans slots with
                                                                                                                                         `status in {idle, stale}` (worker_liveness_watchdog.py:1140). The reclaim log embeds the status as its `%s`:
                                                                                                                                         "reclaiming **idle** lingering session" → slot 5's status column was **`idle`** at 07:32:30. But
                                                                                                                                         `plan_health.py:283` sets `status="working"` at spawn (07:25:50), and neither `claim_slot_for_typed_agent`
                                                                                                                                         (state_store/slots.py) nor `seed_worker_slots_from_tabs` (autospawn.py:739-740 — only revives killed/stale→idle,
                                                                                                                                         "leaves a working row untouched") flips working→idle. So something flipped it between spawn and the kill;
                                                                                                                                         `idle_blocker_inferred` fired for slot 5 at **07:30:34** (the fleet idle sweep right after the 07:30:25 restart),
                                                                                                                                         so it read idle immediately post-restart. **The exact working→idle transition line is NOT yet pinned** (checked
                                                                                                                                         & excluded: seed-from-tabs, claim_slot, the dispatch-ack requeue at worker_liveness_watchdog.py:1011, the health
                                                                                                                                         stale-timeout at health.py:186/255 — 25-min threshold, only ~6min had elapsed). Flagged honestly rather than
                                                                                                                                         inventing a mechanism (the trap that produced the two prior wrong answers) — see residual (R1).

                                                                                                                                      4. **Why it was reapable — precondition B (no guard yet), the decisive fact.** The typed-agent exemption meant to
                                                                                                                                         protect the reconciler — the `typed_agent_sessions` guard in `_reclaim_idle_lingering_sessions` (`f641968`) —
                                                                                                                                         **did not exist in the running code at kill time.** `git show -s f641968` = committed **2026-07-20 14:40:19
                                                                                                                                         +0530 = 09:10 UTC**, ~1h38m **AFTER** the 07:32:30 kill. `git show 1e7fec0:` (06:26 UTC — the newest watchdog
                                                                                                                                         commit that could have been deployed at the kill) shows the function with `kill_session` and **no
                                                                                                                                         `typed_agent_sessions` guard at all**. So the reconciler — a typed one-off whose slot read idle — was reaped by
                                                                                                                                         an UNGUARDED idle-lingering reaper after 2 ticks. Timeline fits: boot 07:27:03 + boot-grace 300s + 2×60s
                                                                                                                                         watchdog ticks ≈ 07:32:30.

                                                                                                                                      **CONSEQUENCE FOR THE FIX (feeds `ao_uniform_agent_liveness_contract`, updated in the same session).** The claim in
                                                                                                                                      both this plan and the uniform-liveness plan that **"`f641968` did NOT fix this" is unsound** — it was inferred
                                                                                                                                      from `agt-751738`'s death, which PREDATES `f641968` by 1h38m; you cannot disprove a fix with an event older than
                                                                                                                                      the fix. On inspection `f641968`'s guard exempts any slot whose session matches a live (non-archived)
                                                                                                                                      `AgentRow.tmux_session`; `plan_health.py:296` sets that field at reconciler spawn and the AgentRow persists across
                                                                                                                                      restart in SQLite, so it **plausibly DOES fix it — but it is UNTESTED**: there has been no reconciler run since it
                                                                                                                                      deployed. The next run is the real test (todo 4).

                                                                                                                                      **RESIDUALS (named, with next step — not hand-waved):**
                                                                                                                                      - **(R1)** Pin the exact code path that flips a typed agent's slot `working`→`idle` (empirically happened at/around
                                                                                                                                        the 07:30 restart). Matters because IF the historical 07-15/17/18 deaths truly had no restart (unverifiable now —
                                                                                                                                        journalctl retention starts 2026-07-18 12:45, all three predate it), then either that flip happens WITHOUT a
                                                                                                                                        restart (unifying all four deaths under this one mechanism) or those three had a different trigger. Do not assume.
                                                                                                                                      - **(R2)** Verify `f641968` exempts live: on todo 4's next reconcile run, confirm the watchdog logs an EXEMPTION
                                                                                                                                        for orch-slot-5 (tick popped via the `typed_agent_sessions` continue at worker_liveness_watchdog.py:1172) instead
                                                                                                                                        of a kill, AND capture the slot's status column during the run. If it still reaps, the AgentRow guard is being
                                                                                                                                        defeated (investigate whether the restart archives/clears the AgentRow or its tmux_session).

                                                                                                                                      **Method note for the next reader:** both prior wrong conclusions leaned on `/api/activity` (`activity_log`), which
                                                                                                                                      does NOT record watchdog reclaims. For "what killed a worker", `journalctl -u orchestrator` is authoritative, not
                                                                                                                                      the activity feed. (`agent-orchestrator@f641968` was shipped on the retracted premise; it is defensively harmless,
                                                                                                                                      its regression test is real, and per the above it is likely the correct fix — just never confirmed live.)

- [x] ✅ [DOC] P3. **Record that the tasks table is a projection, not a completion ledger.** In the regen docs
      (`server/regen_backlog_from_plan.py` module docstring + wherever regen behaviour is documented for operators),
      state explicitly: the tasks table holds currently-OPEN DISPATCHABLE todos plus dispatched history. `BLOCKED-*`
      todos are deliberately never ingested, and a todo checked off outside the dispatch loop has its still-queued row
      garbage-collected. **A missing row is therefore never by itself evidence of a lost task.** Provenance: the B1
      audit, where this item decayed twice because each re-measurement read normal projection churn as instability.
      **Gate**: the docs say it; a future reader cannot repeat the B1 mistake. — **agent-orchestrator@fd09764** (module
      docstring) + **unified-trading-pm@b5e18435**
      (`/codex/04-architecture/agent-orchestrator-backlog-state-alignment.md`, new "The `tasks` table is a projection,
      not a completion ledger" section + an `Anti-patterns` cross-reference line — the operator-facing SSOT this todo
      also asked for).

## Safeguards

- Never `git reset --hard` / `git clean -fd` / `git checkout` a dirty tree — other agents share this repo.
- Commit only from a `quality-gates.sh`-green tree.
- **Never edit a deployed copy under `/usr/local/bin` or `/etc/systemd/system` directly** — edit the generator script in
  the repo and re-run it, or the next bootstrap silently reverts your fix.

## Codex SSOTs

- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — scheduled-agent dispatch model.
- `/codex/04-architecture/agent-orchestrator-alerting.md` — actionable-only alerting; what may page.
- `/codex/12-agent-workflow/async-wait-and-poll-discipline.md` — measured terminal verdicts, not activity signals.

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
- **2026-07-20 — todo 4/5's "watchdog-restart idle-reclaim race" hedge is now RESOLVED; the new P0 is closed (slot-16
  interactive, read-only investigation).** An UNGUARDED `WorkerLivenessWatchdog._reclaim_idle_lingering_sessions` reaped
  `agt-751738` — journalctl shows it at 07:32:30 (`ticks=2 -> freeing slot`), and that function calls `kill_session`
  (worker_liveness_watchdog.py:1212), 1s after the transcript's last write; the reaper was demonstrably ticking against
  a LIVE working reconciler (tick-1 ~07:31:25, a full minute before the last transcript write). **Fatal-blow-vs-corpse
  is ~90%, NOT proven** — `remain-on-exit on` (tmux_spawn.py:837) defeats the `has_session` liveness signal, but the
  self-exit alternative has no surviving cause (usage was 5h=5% 80s prior; no rate-limit/OOM/error; silent stop = the
  signature of an external SIGHUP, not a graceful usage-limit). Closed definitively only by observing the next run (R2).
  This **overturns the P0 todo's own DISPROVEN #3**: the reclaim event is real; it was invisible to the prior author
  only because watchdog reclaims log to journalctl, NOT to `activity_log`. The decisive fact is timing: the `f641968`
  typed-agent guard that would exempt the reconciler was committed at 09:10 UTC — **1h38m after** the 07:32:30 kill — so
  at kill time the idle-reclaimer had NO typed-agent exemption (`git show 1e7fec0:` confirms). Two named residuals
  carried in the P0 todo: (R1) pin the exact `working`→`idle` slot-status flip (empirically at the 07:30 restart; not
  yet located in code); (R2) verify `f641968` actually exempts a live reconciler on todo 4's next run — it is plausibly
  the correct fix but is UNTESTED (no reconcile run since it deployed). The uniform-liveness plan's "premise not
  diagnosed" banner is updated in the same session: the bug IS now diagnosed. **Method lesson for the corpus: for "what
  killed a worker", journalctl is authoritative — `/api/activity` does not record reclaims, and two confident wrong
  conclusions here came from trusting it.**
