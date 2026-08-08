---
doc_type: issue
title: >-
  AO observability + deploy-hygiene gaps found while diagnosing a 2026-08-08 fleet stall — activity-log flood fixed,
  four residual gaps tracked here
summary: >-
  A session that set out to answer "does an AO worker retain its backlog when its account runs out of usage" surfaced a
  cluster of unrelated observability and deploy-hygiene defects on the central VM. Two are fixed and deployed:
  OrphanRefVerifyWatchdog wrote one activity row per wip-preserve ref per tick (measured 882 of 1000 rows in a SIX
  MINUTE window, 76% of the feed) making /api/activity near-useless for diagnosing anything else, now transition-deduped
  (agent-orchestrator@b19140b23); and the context-saturation retry loop burned 15 minutes per wedge on a /compact that
  cannot succeed (agent-orchestrator@b52dd1910, tracked on its own issue doc). Four residual gaps are tracked here and
  are NOT fixed - the ao-self-pull auto-deploy silently skipping on an untracked backup file, ~26 genuine false-done
  backlog rows the audit cron keeps re-finding, a 50-event stash_pile_stale backlog, and the glue-runner fleet whose own
  runbook still reads last_executed NEVER while 51 orphaned unit files sit disabled on the VM pointing at directories
  that do not exist.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [agent-orchestrator, observability, activity-log, deploy, self-pull, false-done, glue-runners, stashes]
related:
  [
    /plans/active/issues/slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md,
    /plans/active/issues/ao_scheduled_job_reserve_and_staggering_2026_08_04.md,
    /codex/04-architecture/agent-orchestrator-alerting.md,
    /codex/04-architecture/agent-orchestrator-scheduled-jobs.md,
  ]
created: 2026-08-08
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.4
assigned_role: backend_engineer
drift_direction: none
last_updated: 2026-08-08
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: ['interactive session 2026-08-08 — operator: "did you fix all these so no issues left whatsoever? else do it"']
---

# AO observability + deploy-hygiene gaps (2026-08-08)

## Fixed + deployed in the originating session

- **Activity-log flood** — `OrphanRefVerifyWatchdog` logged one `orphan_ref_verified` row per ref per tick,
  unconditionally. Measured live: `orphan_ref_verified` + `orphan_ref_self_closed` were **882 of the last 1000
  `/api/activity` rows inside a six-minute window** (and 456/600 in an earlier sample), crowding every other event out
  of the feed while that feed was actively being used to diagnose a fleet stall. It also contradicted this workspace's
  own standing rule that a standing condition dedups by state-transition and never fires every tick. Now logs only on a
  verdict CHANGE, with a `dedup_state`-persisted latch pruned wholesale each tick. **agent-orchestrator@b19140b23**,
  deployed to the central VM and restarted 11:39 UTC.
- **Context-saturation retry burn** — tracked on
  `/plans/active/issues/slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md`, not duplicated here.
  **agent-orchestrator@b52dd1910**.

## Todos

- [ ] [BACKEND] P2. **`ao-self-pull.sh` silently stops auto-deploying when an UNTRACKED file appears.** Measured
      2026-08-08: the central VM's AO checkout carried one untracked file
      (`data/config/accounts.json.bak-2026-08-08-tier`, someone's manual accounts backup) and self-pull logged
      `is dirty (non-churn) — skip (manual review)` and did nothing. An untracked `.bak-` file cannot conflict with a
      fast-forward pull, so this is a false block on the fleet's ONLY auto-deploy path — and it fails SILENTLY (a log
      line, no page), so the VM can sit un-deployed indefinitely. Recovered by hand this session via
      `git pull --ff-only` (untracked files do not block it) + `systemctl restart orchestrator`. **Done when**: the
      dirty-check distinguishes untracked-and-non-conflicting from a genuinely dirty TRACKED file, and a skip that
      persists past N ticks pages rather than only logging. (repo: agent-orchestrator)
- [ ] [BACKEND] P2. **Reconcile the ~26 genuine false-done backlog rows the `audit-false-done` cron keeps re-finding.**
      The unit exiting 1 is BY DESIGN (its own unit file documents "a nonzero exit means a false-done row was FOUND —
      real signal, not a bug"), and Slack alerting is already transition-deduped through `audit_cron_notify.py` — so the
      unit is not the defect and must NOT be "fixed" by changing its exit code. The defect is the finding: backlog rows
      with `status=done` whose plan checkbox is still `- [ ]`, i.e. the false-progress class CLAUDE.md names as its #1
      risk. IDs captured 2026-08-08 include `agent_orchestrator_ldr_terminal_promotion-001..004`,
      `cefi_live_event_cold_compactor_oom_*-004..005`, `sports_arb_operator_group_and_commission_bugfix-001..008` (+ its
      `_finalize-001..004`), `wip_preserve_refs_silently_unrecovered-002..003`,
      `sit_gate_fleet_green_auto_retrigger_stuck-005`, `infra_satellite_ao_dispatch_batch8-001`,
      `fleet_promoter_glue_runner_stall-004`. **NOT auto-resolvable**: each needs a per-item read of whether the work
      actually landed, then either flip the checkbox or reopen the task — guessing 26 verdicts is exactly the
      fabrication this audit exists to catch. Note several are same-day `_finalize-*` rows where the flip may simply
      still be in flight; re-run the audit before triaging so the genuinely-stale subset is isolated first. **Done
      when**: `systemctl start audit-false-done.service` exits 0. (repo: agent-orchestrator, unified-trading-pm)
- [ ] [BACKEND] P3. **Triage the `stash_pile_stale` backlog — 50 events in a 1000-row activity window (2026-08-08).**
      Operator-reported corroboration the same day: slot 11 carries 8 git stashes in `market-tick-data-service`, oldest
      23 days. A stash pile that old is either recoverable work nobody has claimed or litter that should be dropped;
      either way `git stash drop` on foreign WIP is banned, so this needs a per-stash liveness/ownership read. **Done
      when**: every stale stash is either landed, preserved to a `wip-preserve/` ref, or explicitly written off with the
      decision recorded. (repo: all slot clones)
- [ ] [OPERATOR] P3. **Decide the glue-runner fleet's fate — 51 orphaned systemd unit files on the central VM.**
      `scripts/self-hosted-runners/README.md` still reads
      `last_executed: NEVER (files created 2026-07-15, redesigned     two-pool 2026-07-16; not yet deployed)`, yet 51
      `github-glue-*` unit files exist (written 2026-07-27) whose `ExecStart` points at
      `/opt/github-glue-runners-<repo>/refresh-gh-token.sh` — and **no such directory exists anywhere on the box**. They
      are all `enabled=disabled, active=inactive`, last result 203/EXEC, so they are inert litter rather than a live
      failure (this is why only ONE unit shows in `systemctl --failed`). A prior report of "12 failing token-refresh
      units" describes the pre-disable state and is no longer accurate. Deliberately left in place this session —
      deleting them would destroy scaffolding the real deployment needs. **Done when**: either the two-pool deployment
      is completed per `/plans/archive/2026_07/github_actions_ci_cost_reduction_2026_07_15.md`, or the units are removed
      and the runbook's `last_executed` reflects the decision. `[OPERATOR]` because it is a cost/architecture call, not
      a bounded fix. (repo: unified-trading-pm)

## Progress Log

**2026-08-08 (interactive session, slot 4)** — Originated from an unrelated question about AO account-exhaustion
behaviour. Findings above were surfaced by reading `/api/activity` and the live systemd/journal state over SSM
(read-only except where noted). Two fixes shipped + deployed; the four todos above are deliberately NOT closed because
each needs either a per-item human read (false-done, stashes) or an architecture decision (glue runners), and the
self-pull fix touches the fleet's only auto-deploy path so it wants its own gated change rather than a same-session
drive-by. Corrected two earlier mis-reads during the session: the "12 failing glue units" are disabled-and-inert not
failing, and the "33 vs 27 repos" gap between old and new slots is leftover `*.stale-pre-history-rewrite-*` dirs, i.e.
the new slots are cleaner.
