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
    ao_consolidated_closeout_2026_07_25,
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

- **`process-category-sampler` failed EVERY run** — `TasksMax=50` with `TasksCurrent=40` (1420 `can't start new thread`
  in 6h, first seen 2026-08-07T16:48Z). NOT host exhaustion: 668 system threads against a threads-max of 231854. The
  unit enumerates every process on the box and publishes each as its own Pub/Sub call, so its thread demand grows with
  the fleet while the cap did not — guaranteed to fail harder as slots are added. Raised to 256
  (**agent-orchestrator@36067b6ac**); that exposed a second cap underneath — `MemoryMax=256M` with a measured
  `256.0M peak, 174.4M swap peak`, i.e. pinned and SWAPPING — raised to 1G. Both deployed + live-fired:
  `Result=success`.

## Outcome measured at session end (2026-08-08 ~12:10 UTC)

| signal                     | before           | after                             |
| -------------------------- | ---------------- | --------------------------------- |
| live worker tmux sessions  | 8                | **12 / cap 13**                   |
| effective backlog cap      | 8                | **13**                            |
| slots pinned >=80% context | 5 (all at 100%)  | **0**                             |
| watchdog kills today       | 3, flapping=true | **0, flapping=false**             |
| failed systemd units       | 2                | 1 (`audit-false-done`, by design) |

## Todos

- [x] ✅ [BACKEND] P2. **`ao-self-pull.sh` silently stops auto-deploying when an UNTRACKED file appears** — FIXED
      agent-orchestrator@2c08afd85. Gate now uses `--porcelain -uno` (TRACKED changes only). An untracked file cannot be
      blown away by a fast-forward merge, so there is no uncommitted WORK to protect — this gate's entire stated purpose
      — and the one genuinely-conflicting case (incoming commit creates that exact path) is already handled safely by
      `merge --ff-only`, which refuses and falls through to the same skip+alert. This fixes the CLASS: the 2026-07-29
      fix patched the INSTANCE by gitignoring two specific filenames via `accounts.json.bak-pre-sub-*`, and a
      differently-named backup slipped past it on 2026-08-08 and wedged the same gate again. Verified against the REAL
      wedged state on the VM: old predicate blocks, new one clears with that exact file still present. Untracked files
      are now logged so litter stays visible; `.gitignore` broadened to `accounts.json.bak*` as hygiene, not as the fix.
      ORIGINAL FINDING: Measured 2026-08-08: the central VM's AO checkout carried one untracked file
      (`data/config/accounts.json.bak-2026-08-08-tier`, someone's manual accounts backup) and self-pull logged
      `is dirty (non-churn) — skip (manual review)` and did nothing. An untracked `.bak-` file cannot conflict with a
      fast-forward pull, so this is a false block on the fleet's ONLY auto-deploy path — and it fails SILENTLY (a log
      line, no page), so the VM can sit un-deployed indefinitely. Recovered by hand this session via
      `git pull --ff-only` (untracked files do not block it) + `systemctl restart orchestrator`. **Done when**: the
      dirty-check distinguishes untracked-and-non-conflicting from a genuinely dirty TRACKED file, and a skip that
      persists past N ticks pages rather than only logging. (repo: agent-orchestrator)
- [x] ✅ [BACKEND] P2. **False-done rows: 26 -> 1, and the 1 is not a false-done.** Re-ran the audit 2026-08-08 ~12:50Z:
      **TOTAL FINDINGS: 1**. The other ~25 were same-day in-flight `_finalize-*` flips their own workers reconciled —
      exactly what this todo predicted ("re-run the audit before triaging so the genuinely-stale subset is isolated").
      The survivor, `cefi_content_migration_corpus_still_incomplete_relaunch_round3_needed-025`, was read in full: that
      plan carries FOUR near-identical "Round-8 ACTUAL LAUNCH" todos (3 checked, 1 open) because each time-gated
      deferral appended a fresh copy. The DB row is legitimately `done` — that dispatch DID complete, the worker
      verified the UTC gate was unmet, launched nothing, and spawned the follow-up — and the open `- [ ]` is
      legitimately open, because the launch still has not happened. **Neither side is wrong; it is the positional-
      task-ID mapping artifact** (`regen_positional_task_ids_not_content_stable_2026_07_17`). Flipping the checkbox
      would falsely claim 8 SPOT VMs were launched; reopening the row would falsely reopen completed work — so
      deliberately did NEITHER. Root fix is ALREADY IN FLIGHT by another agent: `_make_content_task_id` exists in
      `regen_backlog_from_plan.py` behind a `reportUnusedFunction` suppression (agent-orchestrator@ac36202 + @e0f107a),
      built but not yet wired. Not colliding with it.
- [ ] [BACKEND] P2. **Stash piles are ~15x bigger than first reported, and need a CONTENT VERIFIER before any discard.**
      The original report was "slot 11 has 8 stashes in `market-tick-data-service`". A full fleet sweep on 2026-08-08
      found **hundreds across 20 slots** — in `unified-trading-pm` alone: slot 10 = 31, slot 12 = 24, slot 11 = 23, slot
      13 = 23; plus slot 12 `market-tick-data-service` = 11, slot 11 `market-tick-data-service` = 8, and long tails on
      features-service / unified-api-contracts / instruments-service. The oldest reach back to 2026-06-23. Priority
      raised P3 -> P2 on that measured scale. **Deliberately NOT bulk-discarded this session.** Discarding foreign WIP
      is a workspace HARD RULE (and is hook-blocked for autonomous workers); at this scale a wrong call destroys real
      work fleet-wide — the single worst outcome available in this doc. Two findings make it tractable rather than
      open-ended: (a) the large majority are `autostash`, which git pops AUTOMATICALLY on a successful rebase — so a
      LEFTOVER autostash specifically means the pop FAILED (conflict), i.e. genuinely un-restored working state rather
      than noise; (b) the safe test is content-identity, the exact question
      `worktree_clean_check.verify_all_wip_preserve_refs` already answers for orphaned commits (is this content already
      in origin? SUPERSEDED / GONE / STILL-ORPHANED). **Done when**: a stash verifier reusing that verdict vocabulary
      exists, and every stash is either landed, preserved to a `wip-preserve/` ref, or written off with its verdict
      recorded. Note the detection half already exists (`stash_audit_watchdog.py` emits `stash_pile_stale`, 50 events in
      a 1000-row window) — what is missing is the verifier, not the alarm. (repo: all slot clones, agent-orchestrator)
- [x] ✅ [OPERATOR] P3. **Glue-runner litter removed — 51 orphaned unit files retired 2026-08-08T13:05Z.** Verified
      immediately before acting, and re-asserted inside the same script as a refuse-guard: **0 of 51 active, 0 enabled,
      no `/opt/github-glue*` directory anywhere, and no `Runner.Listener` process** (an earlier `pgrep -fc` reading of 1
      was the grep matching itself). So nothing was serving CI from them. Moved — not deleted — to
      `/etc/systemd/system/.retired-glue-units-20260808T130521Z/`, fully reversible, and regenerable from
      `setup-glue-runners.sh` whenever the two-pool deployment actually happens. `systemctl --failed` is now 1
      (`audit-false-done`, by design) instead of carrying permanent litter that already cost one false "12 failing
      units" diagnosis this session. The runbook's `last_executed: NEVER` was already accurate and stands. ORIGINAL
      FINDING: `scripts/self-hosted-runners/README.md` still reads
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
