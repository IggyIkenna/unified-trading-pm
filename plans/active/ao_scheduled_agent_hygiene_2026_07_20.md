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
      artifacts.
- [ ] [BACKEND] P1. **Add the daily liveness assertion (the durable answer to "did it stop again?").** Assert timer
      `is-active` AND a computed next-elapse exists AND the last SUCCESSFUL dispatch is < 26h old — alert on breach.
      **`systemctl is-enabled` is NOT sufficient**: the original outage was an `enabled` timer that was INACTIVE, which
      `is-enabled` does not detect and `list-timers` omits. Route per the actionable-only alerting rule — this is a real
      failure, so it may page. **Gate**: the assertion fires on a STOPPED-timer condition and clears on a running one,
      proven with a **mocked/fixture systemctl state in a local test — do NOT stop the live timer on the central VM to
      test this.** Stopping it is a production action that silently skips a daily reconcile, which is the exact outage
      this todo exists to detect. If you believe a live exercise is unavoidable, that is an OPERATOR decision — ask, do
      not do it unilaterally.
- [ ] [BACKEND] P2. **Fix the /boot read-confirmation gate for typed agents.** `server/routes/slots_worker.py` calls
      `prompts.expected_read_files("worker", req.slot_role)` with the base role hardcoded to `"worker"`, so expected =
      `[RULES.md, worker.md, <craft>]`. A plan_health/plan_reconciler worker is pointed at `RULES.md` +
      `plan_reconciler.md` and never at `worker.md`, so its first `/boot` is rejected 428 and logs
      `boot_read_unconfirmed` — **176 events since 07-18**. It self-heals via retry (~10s + a re-read), so this is
      wasted tokens plus a permanently noisy signal rather than an outage — but it is a latent hard-fail for any agent
      that does not retry, and it makes `boot_read_unconfirmed` useless as an alert. Pass the ACTUAL agent kind (the
      spawn side already composes the right role). **Gate**: a plan_reconciler boot confirms on the FIRST POST; a test
      covers each typed role; `boot_read_unconfirmed` trends to ~0 over 24h.
- [ ] [BACKEND] P1. **Prove ONE reconcile run end-to-end — this is the plan's real gate.** After the above land and
      `ao-self-pull` has restarted the service, observe a full run producing BOTH a `plan_health_result` activity row
      AND a pushed `plan_reconciler/<dispatch_id>` branch. Until that is seen once, the subsystem stays
      **NEVER-VERIFIED**, not "re-armed" — do not tick this on a green-looking journal line. **Gate**: the dispatch_id,
      the result row, and the branch name, all cited.
- [ ] [BACKEND] P2. **Explain the 7-min death class on 07-15/17/18.** Each was `plan_health_dispatched` then
      `tmux_session_lost … archived_lifecycle_complete: true` ~7 min later with no result (07-15 `agt-2d8441` is odder
      still — `finished_at` 07:30, over 6h after a session that vanished at 01:12). 7 min is far too short for an
      opus/max full-corpus reconcile when the haiku REPORT pass alone medians 280s. **Do NOT assume the reaper fix
      covers these** — it has a named cause only for 07-20. **Gate**: each of the three has a named cause, OR the
      end-to-end run above proves the class is closed — state which.
- [ ] [DOC] P3. **Record that the tasks table is a projection, not a completion ledger.** In the regen docs
      (`server/regen_backlog_from_plan.py` module docstring + wherever regen behaviour is documented for operators),
      state explicitly: the tasks table holds currently-OPEN DISPATCHABLE todos plus dispatched history. `BLOCKED-*`
      todos are deliberately never ingested, and a todo checked off outside the dispatch loop has its still-queued row
      garbage-collected. **A missing row is therefore never by itself evidence of a lost task.** Provenance: the B1
      audit, where this item decayed twice because each re-measurement read normal projection churn as instability.
      **Gate**: the docs say it; a future reader cannot repeat the B1 mistake.

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
