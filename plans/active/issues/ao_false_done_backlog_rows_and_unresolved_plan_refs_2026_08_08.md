---
doc_type: issue
title: >-
  audit-false-done.service has been exiting 1 on every run — 14 backlog rows are `done` in state.db while their plan
  checkbox is still `- [ ]`, plus 1,013 rows whose plan_ref no longer resolves and 12 that are structurally unauditable
summary: >-
  Found while diagnosing a reported "AO is overloaded / crashing" (2026-08-08 interactive session, slot 1) — the VM was
  neither, but `audit-false-done.service` was one of 13 failed systemd units on the orchestrator VM. It is a one-shot
  timer-driven audit that exits `1/FAILURE` whenever it finds breaches, so a permanently-red unit is the audit correctly
  reporting a standing breach, not a broken audit. Live run 2026-08-08 03:1x UTC against `data/state/state.db` @
  `origin/live-defi-rollout`: **false_done 14 · honest 645 · UNAUDITABLE 12 (brief_hash NULL) · unresolved 1,013
  (plan_ref did not resolve at the ref)**. The 14 false-done rows are the Commit+Push+Flip Half-2 violation CLAUDE.md
  calls the "#1 source of false-progress" — a worker marked the backlog row `done` (most carry a real `done_sha`) but
  never flipped the plan checkbox, so the plan corpus under-reports completion while the backlog over-reports it.
  Several are visibly gate-shaped ("Once the relaunched VM genuinely completes…", "Once fixed, backfill…"), i.e. work
  that was deferred rather than finished, which makes REOPEN the likely correct verdict for those rather than a checkbox
  flip. **Deliberately NOT auto-reopened in the discovering session**: the same session established that the fleet is
  account-capacity-starved (only 2 of 6 Anthropic accounts usable, 282 tasks already queued against 1 dispatched), so
  reopening 14 tasks would have deepened the starvation rather than relieved it. The 1,013 unresolved plan_refs are a
  much larger and separate signal — most are expected (rows pointing at since-archived plans) but the count has never
  been characterised, so it is carried here as its own audit todo rather than assumed benign.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [agent-orchestrator, backlog, false-done, audit, commit-push-flip, plan-hygiene, state-db, systemd, dispatch]
related:
  [
    /codex/12-agent-workflow/commit-push-flip-rule.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/issues/regen_positional_task_ids_not_content_stable_2026_07_17.md,
    /plans/active/issues/fleet_promoter_glue_runner_stall_2026_08_06.md,
    /codex/15-runbooks/safe-service-restart-procedures.md,
  ]
created: 2026-08-08
last_updated: "2026-08-08"
author: ikennaigboaka [interactive session, slot 1]
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
assigned_role: backend_engineer
drift_direction: advance-process
resolved_by:
locked_by:
depends_on: []
source: >-
  Operator-dispatched diagnosis of "whats overloading AO its crashing" (2026-08-08). The overload premise did not hold
  (load 0.69/8 cores, 25.8 GB of 31 GB free, zero OOM kills, NRestarts=0); this audit unit was one of the real defects
  the diagnosis surfaced underneath it.
context_scope:
  [
    /codex/12-agent-workflow/commit-push-flip-rule.md,
    agent-orchestrator/scripts/orchestrator/audit_false_done.py,
    agent-orchestrator/scripts/orchestrator/audit_cron_notify.py,
    agent-orchestrator/server/routes/backlog.py,
  ]
---

# `audit-false-done` standing breach — 14 false-done rows + 1,013 unresolved plan_refs

## What the audit actually reports

`audit_false_done.py` classifies every `done` backlog row by re-reading its plan checkbox at `origin/live-defi-rollout`.
Live run, 2026-08-08 ~03:15 UTC:

| bucket        | count | meaning                                                            |
| ------------- | ----: | ------------------------------------------------------------------ |
| `false_done`  |    14 | row is `done`, plan checkbox is still `- [ ]`                      |
| `honest`      |   645 | row is `done` and the checkbox agrees                              |
| `UNAUDITABLE` |    12 | `brief_hash IS NULL` — cannot be checked either way, **not clean** |
| `unresolved`  | 1,013 | `plan_ref` did not resolve at the ref                              |

The unit is `Type=oneshot` and returns non-zero on breach, so `systemctl --failed` listing it is the audit _working_. Do
**not** "fix" it by adding `SuccessExitStatus=1` — that would silence the only standing signal for this class.

## The 14 false-done rows

Each needs one verdict: **REOPEN** (`POST /api/backlog/{id}/reopen`, work genuinely not finished) or **FLIP** (work is
done; flip the plan checkbox with evidence per the Commit+Push+Flip rule). Verdict must come from reading the cited
plan + verifying the `done_sha`, never from the row's status alone.

- [ ] [BACKEND] P2. `infra_capture_and_devops_leftovers_finalize-001` (`done_sha=268f7147a`)
- [ ] [BACKEND] P2. `defi_dex_pool_swaps_733_row_indexer_health_findings-001` (`done_sha=69d41b26f`)
- [ ] [BACKEND] P2. `cefi_track2_backfill_vm_preempted_no_recovery-003` (**`done_sha` EMPTY** — the strongest reopen
      candidate: a `done` row with no shipping evidence at all; todo is gate-shaped, "Once the relaunched VM genuinely
      completes (measured exit, not a wall-clock guess)…")
- [ ] [BACKEND] P2. `deployment_api_sigabrt_crash_loop-017` (`done_sha=467b28964`)
- [ ] [BACKEND] P2. `sports_fast_t1_recon_oom_live_capture_outage-003` (`done_sha=80265d6`) — gate-shaped ("Once fixed,
      backfill/re-fetch the resulting gap (2026-07-27, 2026-07-28…)")
- [ ] [BACKEND] P2. `infra_capture_and_devops_leftovers-001` (`done_sha=c3c65402e`)
- [ ] [BACKEND] P2. `sports_closeout_track_x_hygiene-006` (`done_sha=976786c5`) — 9,733-object
      `instruments-store-sports-prd` migration; verify against the real object count, not the plan's prose
- [ ] [BACKEND] P2. `defi_cefi_venue_chain_axis_contamination-011` (`done_sha=45b5112e7`)
- [ ] [BACKEND] P2. `defi_cefi_venue_chain_axis_contamination-014` (`done_sha=b78ec6e7c`)
- [ ] [BACKEND] P2. `mtds_migrate_executor_progress_checkpoint_gap-008` (`done_sha=c98e0abb`)
- [ ] [BACKEND] P2. `mtds_migrate_executor_progress_checkpoint_gap-009` (`done_sha=6ddb0374`)
- [ ] [BACKEND] P2. `mtds_migrate_executor_progress_checkpoint_gap-010` (`done_sha=6ddb0374` — **same sha as -009**;
      check whether one commit legitimately closed both or whether a shared sha was copied across rows)
- [ ] [BACKEND] P2. `deployment_scripts_bucket_soft_delete_retention_drift-002` (`done_sha=97d37ce57`) — explicitly
      dated "Final drain confirmation on/after 2026-08-09", i.e. **not due yet**; likely REOPEN, not FLIP
- [ ] [BACKEND] P2. `cefi_content_migration_corpus_still_incomplete_relaunch_round3_needed-025` (`done_sha=0e9185d2c`) —
      round-8 launch across 8 shards; verify launch evidence before flipping

## Follow-ups

- [ ] [BACKEND] P2. **Characterise the 1,013 `unresolved` rows.** Confirm the expected explanation (rows whose plan was
      archived, so `plan_ref` no longer resolves at `origin/live-defi-rollout`) actually accounts for the bulk, and
      report the residue that does NOT. A row that is `done` and unresolvable is invisible to this audit forever, so a
      large unexplained residue is a silent-blindspot, not bookkeeping noise. Report the split; do not bulk-mutate.
- [ ] [BACKEND] P3. **Bound the 12 `UNAUDITABLE` (`brief_hash IS NULL`) rows.**
      `regen_positional_task_ids_not_content_stable_2026_07_17.md` already shipped `agent-orchestrator@aaa2db8` to bound
      this tail and the count still moves — re-measure, and confirm every remaining unhashed row is a `done` row (which
      is what bounds the exposure).
- [ ] [BACKEND] P3. **Decide whether a standing false-done breach should page.** It currently only transitions Slack
      state via `audit_cron_notify.apply_transition` (breach→breach stays silent, by design), so a breach that never
      clears is silent after its first notify while the systemd unit stays red indefinitely. Confirm that matches the
      actionable-only alerting contract in `/codex/04-architecture/agent-orchestrator-alerting.md`.

## Codex SSOTs

- `/codex/12-agent-workflow/commit-push-flip-rule.md` — the Half-2 rule these 14 rows violate
- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — evidence format for a legitimate flip
- `/codex/15-runbooks/safe-service-restart-procedures.md` — account-capacity check that gates re-dispatch

## Progress Log

- **2026-08-08 ~03:15 UTC (interactive session, slot 1)**: Filed. Ran `audit_false_done.py` live against the
  orchestrator VM (`i-0c9b283b31d6b5ca7`) via SSM and captured all 14 ids + `done_sha`s above. **No row was reopened and
  no checkbox was flipped in this session** — deliberately: the same diagnosis established the fleet is
  account-capacity-starved (sub-a 98% weekly, sub-b 100% and rate-limited to 2026-08-09T19:00Z, sub-e/sub-f `disabled`
  with `overage_disabled_reason=org_level_disabled`, leaving only sub-c/sub-d usable), with 282 tasks already queued
  against 1 dispatched. Reopening 14 tasks into that queue would have deepened the starvation while producing no
  throughput. Sequencing is therefore: resolve account capacity first, then work these 14.
