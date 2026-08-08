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
    /plans/archive/issues/fleet_promoter_glue_runner_stall_2026_08_06.md,
    /codex/15-runbooks/safe-service-restart-procedures.md,
  ]
created: 2026-08-08
last_updated: "2026-08-08"
author: ikennaigboaka [interactive session, slot 1]
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
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

- [x] ✅ [BACKEND] P2. `infra_capture_and_devops_leftovers_finalize-001` (`done_sha=268f7147a`) — **verified 2026-08-08
      (slot 22): row no longer exists in `state.db`** — `GET /api/backlog` has zero rows matching this id, this title,
      or `done_sha=268f7147a` (2,369 total rows checked); the only row still tied to this doc family is
      `infra_capture_and_devops_leftovers-001` (parent plan, `status: queued`). Read the cited plan
      (`plans/active/infra_capture_and_devops_leftovers_finalize_2026_07_25.md`) and confirmed `268f7147a` is a real
      commit
      (`docs(plans): reconcile infra_capture_and_devops_leftovers parent — MANTLE + Live-ODDS quota blockers     cleared`,
      2026-08-02) that did genuine partial-reconciliation work, but the plan's own todo 2 checkbox is correctly still
      `- [ ]` — it is an intentionally-recurring re-check pointer ("re-run again once…") and 3 of 4 gated `BLOCKED-*`
      items remain open per that todo's own 2026-08-02 Progress Log entry, so the checkbox is NOT mis-stated. **No
      REOPEN or FLIP action was needed or possible**: the backlog row this audit item names has already vanished from
      state.db (consistent with `regen_positional_task_ids_not_content_stable_2026_07_17.md` — positional ids reshuffle
      across regen ticks) between the 2026-08-08 03:15 UTC audit snapshot and this check, and the plan doc it pointed at
      is already in its correct, honest state. Nothing further to do on this item.
- [x] ✅ [BACKEND] P2. `defi_dex_pool_swaps_733_row_indexer_health_findings-001` (`done_sha=69d41b26f`) — **FLIP,
      verified 2026-08-08 (slot 8)**: `69d41b26f` is a real commit
      (`docs(plans): resolve UNISWAP_V3/OPTIMISM+     PANCAKESWAP_V3/BSC bad-indexers investigation…`, author
      `ikennaigboaka [slot-8·planning]`, 2026-08-02T21:11:29Z, confirmed ancestor of `origin/live-defi-rollout`) that
      genuinely resolved the cited plan's "bad indexers transient vs. permanent" investigation todo —
      UNISWAP_V3/OPTIMISM confirmed PERMANENT/structural, PANCAKESWAP_V3/BSC confirmed transient-and-resolved with a new
      stalled-indexer-head finding filed separately (full evidence: that plan's Progress Log entry "2026-08-02T~21:10Z
      (slot 8, data_engineering, task `defi_dex_pool_swaps_733_row_indexer_health_findings-001`)"). The false-done flag
      was a plan-doc bookkeeping artifact, not undone work: a later worker appended a near-duplicate `[x]` checkbox
      elsewhere in the same doc instead of editing the original todo, leaving the original orphaned as `- [ ]` — the doc
      itself now documents this root cause in full (see its "✅ CLOSED 2026-08-08 (false-done audit reconciliation)"
      annotation), and that orphaned duplicate was already reconciled by a separate slot-1 session
      (`unified-trading-pm@b55c96fb0`, confirmed via `git     blame`). No further action needed on the underlying plan;
      this item only needed its tracker checkbox flipped here.
- [x] ✅ [BACKEND] P2. `cefi_track2_backfill_vm_preempted_no_recovery-003` (**`done_sha` EMPTY** — the strongest reopen
      candidate: a `done` row with no shipping evidence at all; todo is gate-shaped, "Once the relaunched VM genuinely
      completes (measured exit, not a wall-clock guess)…") — **verified 2026-08-08 (slot 19): no REOPEN action needed or
      possible — the row is no longer false-done.** `GET /api/backlog` for this exact id returns `status: "queued"`,
      `done_sha: null`, `dispatched_to: null` (not `done`) — the false-done state the 03:15 UTC audit snapshot captured
      has already self-corrected. Cross-checked against the cited plan
      (`plans/active/issues/cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md`): the todo's own checkbox is
      still honestly `- [ ]` (the gate — "the relanched VM genuinely completes, measured exit" — remains unmet as of
      today; the 6th VM died via `WORKER_STALLED` on 2026-08-06, a 7th relaunch is queued but not yet dispatched, and 5
      separate review-craft dispatches today alone independently re-verified the gate is still unmet and declined via
      `reason_code: "GATED"`). Read `server/routes/backlog.py`'s `reopen_backlog_task` to confirm it is a no-op here
      regardless (resets an already-`queued`/`done_sha: null` row to the same state) — not calling it, since there is
      nothing to correct. No REOPEN or FLIP was warranted or performed; this item only needed its tracker checkbox
      resolved with the verification trail above.
- [x] ✅ [BACKEND] P2. `deployment_api_sigabrt_crash_loop-017` (`done_sha=467b28964`) — **verified 2026-08-08 (slot 18):
      no REOPEN or FLIP action needed or possible — the row this audit item names has already self-corrected.**
      `467b28964` (slot-6, 2026-07-31) is a `docs(plans):` commit against
      `plans/active/issues/deployment_api_sigabrt_crash_loop_2026_07_24.md` itself — the `[REVIEW] P1` MASTER/WORKER
      pid-role-correlation todo (now at line 224). At that time the commit's own content shows the todo's done-when
      genuinely wasn't met ("a SIGABRT occurred, but the correlation is UNRESOLVABLE… Leaving this checkbox unchecked")
      — i.e. the 03:15 UTC audit snapshot correctly caught a real false-done (backlog row `done`, checkbox honestly
      still `- [ ]`). Per `GET /api/backlog`, the positional id `deployment_api_sigabrt_crash_loop-017` now points at a
      DIFFERENT, orphaned row (`title: "(orphan — no longer in backlog.yaml)"`, `done_sha=ffd41f98e`,
      `dispatched_to=12`, `done_at=2026-08-08T11:12:59Z`) — confirming the
      `regen_positional_task_ids_not_content_stable_2026_07_17.md` reshuffle gotcha. `ffd41f98e` (slot-12,
      2026-08-08T11:12:22Z) IS the honest resolution of the same line-224 todo: gate genuinely met (a SIGABRT occurred
      post-`785405d`-deploy), all 7 correlated pids matched `gunicorn WORKER forked` entries, checkbox correctly flipped
      `[x]` with a `[BACKEND] P3` follow-up filed for why workers abort(). Current file state: line 224 is `[x]` ✅,
      matching `ffd41f98e` exactly. The false-done condition the audit captured has already been superseded by genuine,
      correctly-flipped follow-up work — nothing to REOPEN (would re-open already-honestly-done work) or FLIP (already
      flipped, by the row now holding the real work).
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

- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: RECLASSIFY → `assigned_vm: planning`. All 17 open items
  are bounded, worker-determinable audit work with a clear evidence requirement: the 14 named backlog rows each need
  "read the cited plan + verify the `done_sha`, verdict REOPEN or FLIP" — the exact same per-row evidence-based audit
  pattern this tranche's workers already run routinely elsewhere in this corpus (see e.g.
  `ao_open_issues_consolidated_close_out_2026_07_17.md`'s own false-done reconciliation work); the 3 follow-ups
  (characterise the 1,013 unresolved rows; bound the 12 UNAUDITABLE rows; decide whether a standing breach should page,
  checked against an existing codex contract) are similarly bounded fact-finding/verification tasks, none a fresh
  design/judgment call. The filing session's own capacity-starvation concern (deferring the 14 REOPEN-or-FLIP verdicts
  until account headroom recovers) is an operational sequencing note, not a design gate — a worker dispatched this doc
  naturally queues behind the fleet's existing capacity-aware dispatch throttling the same way every other backlog task
  does; it does not require a hard `assigned_vm: NA` block. Conflict-check clear: grepped `plans/active/*.md` for every
  one of the 14 named task ids plus "audit_false_done"/"false_done" — zero hits outside this doc (the
  `ao_observability_and_deploy_hygiene_gaps_2026_08_08.md` false-done item, filed earlier the same day from a shallower
  ~26-row snapshot, is independently confirmed already closed/superseded by this doc's own more precise 14-row audit —
  no overlap remains to conflict on). `execution_scope: local-only → orchestrator-agent`. Companion gated finalize:
  `ao_false_done_backlog_rows_and_unresolved_plan_refs_2026_08_08_finalize_2026_08_08.md`.

- **2026-08-08 (slot 22, backend_engineer)**: Verdict on `infra_capture_and_devops_leftovers_finalize-001`
  (`done_sha=268f7147a`): checked off, no action possible or needed — the named backlog row no longer exists in
  `state.db` (0 hits by id, title, or `done_sha` across all 2,369 rows), and the plan doc it pointed at
  (`infra_capture_and_devops_leftovers_finalize_2026_07_25.md`) already carries its own correct, honest state (todo 2
  intentionally `- [ ]` as a recurring re-check pointer, 3 of 4 gated `BLOCKED-*` parent items still open per its
  2026-08-02 Progress Log). See the checklist item above for the full verification trail.

- **2026-08-08 (slot 8, backend_engineer)**: Verdict on `defi_dex_pool_swaps_733_row_indexer_health_findings-001`
  (`done_sha=69d41b26f`): **FLIP** — verified `69d41b26f` is a real, on-origin commit (authored by this same slot on
  2026-08-02) that genuinely completed the cited plan's "bad indexers transient vs. permanent" investigation todo. The
  false-done flag traced to a plan-doc duplicate-checkbox bookkeeping bug, already root-caused and reconciled by a
  separate slot-1 session earlier the same day (`unified-trading-pm@b55c96fb0`) — confirmed via `git blame` on the
  reconciled checkbox. No REOPEN warranted; no code work needed. See the checklist item above for the full trail.

- **2026-08-08 (slot 19, backend_engineer)**: Verdict on `cefi_track2_backfill_vm_preempted_no_recovery-003` (`done_sha`
  EMPTY at audit time): **no action possible or needed** — `GET /api/backlog` shows this exact id is currently
  `status: "queued"`, `done_sha: null`, not `done`. The false-done state the 03:15 UTC audit snapshot captured has
  already self-corrected by the time of this check (consistent with this task id's own well-documented history of
  positional-ID/status churn — see the cited issue doc's Progress Log, which records 17+ review-craft dispatches to this
  same gate-shaped todo over 2026-07-30 through today, each independently re-verifying and declining via
  `/skip-current-task reason_code: "GATED"`). Cross-checked the underlying plan
  (`plans/active/issues/cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md`): its own todo checkbox is
  correctly still `- [ ]` — the gate ("relaunched VM genuinely completes, measured exit") remains genuinely unmet (6th
  VM died via `WORKER_STALLED` 2026-08-06; 7th relaunch queued, not yet dispatched; 5 independent dispatches today alone
  confirm no VM is currently running). Read `reopen_backlog_task` in `agent-orchestrator/server/routes/backlog.py` to
  confirm calling it now would be a pure no-op (already `queued`/`done_sha: null`) — declined to call it since there is
  nothing to correct. No REOPEN or FLIP warranted; no code work needed. See the checklist item above for the full trail.

- **2026-08-08 (slot 18, backend_engineer)**: Verdict on `deployment_api_sigabrt_crash_loop-017` (`done_sha=467b28964`
  at audit time): **no REOPEN or FLIP action needed or possible** — same self-correcting-positional-id pattern as the
  slot-19/slot-22 items above. `467b28964` (2026-07-31, slot-6) was a genuine false-done AT THE TIME: it's a
  `docs(plans):` commit whose own content leaves the `[REVIEW] P1` MASTER/WORKER pid-correlation todo (now line 224 of
  `deployment_api_sigabrt_crash_loop_2026_07_24.md`) explicitly unchecked ("Leaving this checkbox unchecked — done-when
  genuinely not met"). But `GET /api/backlog` shows the positional id `-017` now belongs to a DIFFERENT, orphaned row
  (`done_sha=ffd41f98e`, dispatched to slot 12, done `2026-08-08T11:12:59Z`) — the id was reused by a regen tick per
  `regen_positional_task_ids_not_content_stable_2026_07_17.md`. `ffd41f98e` is the honest, correctly-flipped resolution
  of that same line-224 todo (slot 12 today: gate met, 7/7 SIGABRT pids matched `gunicorn WORKER`, checkbox flipped
  `[x]` with a `[BACKEND] P3` follow-up filed). Current plan-doc state already matches `ffd41f98e` exactly — nothing to
  correct. See the checklist item above for the full trail.
