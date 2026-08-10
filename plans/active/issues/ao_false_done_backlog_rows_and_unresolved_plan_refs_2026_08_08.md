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
- [x] ✅ [BACKEND] P2. `sports_fast_t1_recon_oom_live_capture_outage-003` (`done_sha=80265d6`) — gate-shaped ("Once
      fixed, backfill/re-fetch the resulting gap (2026-07-27, 2026-07-28…)") — **verified 2026-08-08 (slot 32): no
      REOPEN or FLIP action needed or possible — the row this audit item names has already self-corrected**, same
      positional-id-reshuffle pattern as the 4 items above
      (`regen_positional_task_ids_not_content_stable_2026_07_17.md`). `GET /api/backlog` shows zero rows with
      `done_sha=80265d6` anywhere in the current 2,430-row set, and no row currently holds the id
      `sports_fast_t1_recon_oom_live_capture_outage-003` at all. `80265d67` is a real, on-origin commit
      (`deployment-service`, slot-12, 2026-08-06T00:36:24Z —
      `fix(vm): odds-api guard counts gcloud     stderr WARNING as a VM, blocking every backfill launch`) that genuinely
      shipped, but it fixed a launcher pre-flight guard, not the gap-backfill todo itself. Read the cited plan
      (`plans/active/issues/sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md` line 497): the P1 "Once fixed,
      backfill/re-fetch the resulting gap…" todo is correctly still `- [ ]` — its own Progress Log records that a
      slot-12 session on 2026-08-06 prematurely flipped it to done citing `80265d6`'s backfill VM launch, and a same-day
      interactive session caught that "gate cleared" was premature (final manifest-full-coverage verification was never
      run) and **reverted the checkbox to open**, then ran the todo's own literal done-when (manifest-only read,
      `instruments-store-sports-prd`) and found coverage genuinely NOT full on any of the 5 gap days (25–57% reachable
      coverage, real `attempted_failed` residue). The live backlog now reflects this honestly: the current
      `sports_fast_t1_recon_oom_live_capture_outage-015` row (same "Once fixed, backfill/re-fetch…" title) is
      `status: queued`, `done_sha: null`, blocked on an unmet auto-unpark prerequisite — not `done`. So the false-done
      state the 03:15 UTC audit snapshot captured has already been corrected upstream (both the backlog row and the plan
      checkbox), by a different session, before this task was ever picked up. No REOPEN (would re-open work that's
      already honestly open) or FLIP (would falsely mark unmet work done) was warranted or performed; this item only
      needed its tracker checkbox resolved with the verification trail above.
- [x] ✅ [BACKEND] P2. `infra_capture_and_devops_leftovers-001` (`done_sha=c3c65402e`) — **verified 2026-08-08 (slot
      18): no REOPEN or FLIP action needed or possible — already self-corrected by a different session before this task
      was picked up.** `GET /api/backlog` for this exact id now shows an orphaned row with a DIFFERENT
      `done_sha=f79fbded3` (not the audit-captured `c3c65402e`), same
      `regen_positional_task_ids_not_content_stable_2026_07_17.md` reshuffle pattern as the 5 items above. `f79fbded3`
      (slot-10, 2026-08-08T17:26:13Z,
      `docs(plans): close infra_capture_and_devops_leftovers-001 — api_football struck (BLK-b969f5f0), live odds VM     re-verified healthy`)
      is a real, on-origin commit that genuinely closed the plan's Live-ODDS P2 todo: (1) api_football second-source
      wiring correctly STRUCK per operator decision B on `/blocked` `BLK-b969f5f0` (data-correctness risk — no
      sanctioned business writing sports odds via api_football post-wipe), citing a prior 2026-08-08 false-done-audit
      pass that had restated this as open doc-drift, not a live gap; (2) the live `odds_api` VM
      (`mtds-live-sports-odds-api-trades-20260804-131449`) freshly confirmed RUNNING with a clean GCS run.log through
      2026-08-08T17:23Z, zero errors, manifest shards writing every ~60s. Read the cited plan
      (`plans/active/infra_capture_and_devops_leftovers_2026_07_06.md` line 292): the checkbox is correctly `[x]` ✅ and
      matches `f79fbded3` exactly. No REOPEN (would re-open genuinely, freshly-verified-done work) or FLIP (already
      flipped, honestly) was warranted or performed; this item only needed its tracker checkbox resolved with the
      verification trail above.
- [x] ✅ [BACKEND] P2. `sports_closeout_track_x_hygiene-006` (`done_sha=976786c5`) — 9,733-object
      `instruments-store-sports-prd` migration; verify against the real object count, not the plan's prose — **verified
      2026-08-08 (slot 12): no REOPEN or FLIP action needed or possible — the row this audit item names has already
      self-corrected.** `GET /api/backlog` for this exact id currently returns `status: "queued"`, `done_sha: null`,
      `dispatched_to: null` (NOT `done`), same self-correcting
      `regen_positional_task_ids_not_content_stable_2026_07_17.md` reshuffle pattern as the 6 items above; a full scan
      of the live 2,429-row backlog found zero rows anywhere still carrying `done_sha=976786c5`. `976786c5`
      (`market-tick-data-service`, slot-8, 2026-08-04) is a real, on-origin commit — confirmed via
      `unified-trading-pm@c85fb2eb1`'s same-turn plan-flip commit — but it only built + shipped the migration SCRIPT
      (`migrate_instruments_store_sports_league_vocabulary_2026_08_04.py`); the dry-run itself was explicitly never
      executed, and that same slot-8 commit deliberately left the plan-level P2 checkbox open ("Plan- level P2 checkbox
      stays open (gated on the full migration, not just the script)"). Verified against the REAL object count per this
      item's own instruction, not just the prose: read the cited plan
      (`plans/active/sports_closeout_track_x_hygiene_2026_07_25.md` line 138) — still honestly `- [ ]`, "Done when: a
      fresh census of `instruments-store-sports-prd` returns 0 objects carrying the contaminated vocabulary" — and the
      split sub-todos in `issues/sports_peripheral_bucket_league_vocabulary_contamination_2026_07_20.md`: todo 2
      (build+dry-run) is `[x]` but explicitly documents the dry-run was NOT run; todo 3 ("Apply the migration to prod,
      gated on todo 2's dry-run review") is still `- [ ]`. No object has actually moved — the 9,733-object count is
      unchanged from its 2026-07-20 census. So the false-done state the 03:15 UTC audit snapshot captured (backlog row
      `done` citing a script-build sha, plan checkbox honestly still open) has already self-corrected: the live backlog
      row for this exact id is back to `queued`/`done_sha: null`, matching the plan's own honest open state. No REOPEN
      (would re-open work that's already honestly open, not done) or FLIP (would falsely mark an un-executed migration
      done) was warranted or performed; this item only needed its tracker checkbox resolved with the verification trail
      above.
- [x] ✅ [BACKEND] P2. `defi_cefi_venue_chain_axis_contamination-011` (`done_sha=45b5112e7`) — **verified 2026-08-08
      (slot 15): no REOPEN or FLIP action needed or possible — the row this audit item names has already
      self-corrected**, same `regen_positional_task_ids_not_content_stable_2026_07_17.md` reshuffle pattern as the items
      above. `GET /api/backlog` for this exact id now returns `status: "done"`,
      `done_sha: "no-code:gate-still-unmet-verified"` (not `45b5112e7`), `dispatched_to: 9`,
      `done_at: 2026-08-08T15:05:57Z` — a different slot already re-ran this exact investigation after the 03:15 UTC
      audit snapshot and closed it honestly. The backlog title/brief ("**NEW 2026-08-04.** Once…") matches the P1 todo
      at line ~300 of the cited plan (`plans/active/issues/defi_cefi_venue_chain_axis_contamination_2026_07_28.md`):
      "Once `cefi_tardis_derivative_ticker_historical_gap_2026_08_04.md`'s backfill … completes and is
      manifest-verified: re-run `run_cefi_perp_funding_corpus.py` … then verify `funding_window()` returns non-empty
      observations." That todo's checkbox is correctly still `- [ ]` — cross-checked both halves of the gate: (1) the
      dependency doc IS archived (`plans/archive/issues/cefi_tardis_derivative_ticker_historical_gap_2026_08_04.md`, "🟢
      ARCHIVED 2026-08-07 — all 3 todos done"), so the RAW backfill landed, but (2) this todo's own SECOND half —
      re-running the funding corpus script + verifying `funding_window()` — has not happened yet; the plan's own
      "Deferred after 2026-08-08" section confirms the corpus recompute is still gated on VM `cefi-fwd-20260808-123230`
      (launched 12:32:30Z, ~18-24h remaining as of the last Progress Log entry) plus a GCS probe, neither done as of
      this check. So the false-done state the 03:15 UTC audit snapshot captured (backlog row `done` citing a stale sha,
      plan checkbox honestly open) was correctly re-verified and closed by slot 9 with no code needed — nothing further
      to do here.
- [x] ✅ [BACKEND] P2. `defi_cefi_venue_chain_axis_contamination-014` (`done_sha=b78ec6e7c`) — **verified 2026-08-08
      (slot 27): no REOPEN or FLIP action needed or possible — the row this audit item names has already
      self-corrected.** `GET /api/backlog` for this exact id currently returns `status: "dispatched"`,
      `dispatched_to: 17`, `done_sha: null` (NOT `done`), same self-correcting
      `regen_positional_task_ids_not_content_stable_2026_07_17.md` reshuffle pattern as every item above. `b78ec6e7c`
      (slot-9, 2026-08-04T12:52:21Z) IS a real, on-origin commit — confirmed ancestor of `origin/live-defi-rollout` —
      and its diff + Progress Log entry ("slot-9 2026-08-04 ~12:39Z … Step 2 DONE. Steps 1/3/4 still gated") show it
      genuinely completed only STEP 2 of the 4-step sequenced P1 cleanup at line 330 (the 42 corrupted
      `venue=<bare>`/`chain=FUTURES` manifest rows — 42 CAS-dropped, consolidator resumed) while explicitly leaving
      steps 1/3/4 gated; the commit never claimed the todo itself was done, so the 03:15 UTC audit's `false_done` flag
      (backlog row `done` citing this sha, checkbox honestly `- [ ]`) was a real Half-2 miss at the time. Cross-checked
      the cited plan (`plans/active/issues/defi_cefi_venue_chain_axis_contamination_2026_07_28.md` line 330): the todo
      is still correctly `- [ ]` — steps 1 (corpus re-run/schedule confirmed fresh) and 3/4 (physical GCS duplicate
      cleanup, HYPERLIQUID residual root-cause) remain open per the doc's own body. The live backlog id now points at a
      fresh dispatch (slot 17, `dispatched_at: 2026-08-08T10:55:22Z`) actively working the same title, not a stale
      `done` row — the false-done state has already been superseded by honest re-dispatch. No REOPEN (would collide with
      slot 17's in-flight work on an already-correctly-queued task) or FLIP (would falsely mark unmet steps 1/3/4 done)
      was warranted or performed; this item only needed its tracker checkbox resolved with the verification trail above.
- [x] ✅ [BACKEND] P2. `mtds_migrate_executor_progress_checkpoint_gap-008` (`done_sha=c98e0abb`) — **verified 2026-08-08
      (slot 30): no REOPEN or FLIP action needed on the backlog row — already self-corrected**, same
      `regen_positional_task_ids_not_content_stable_2026_07_17.md` reshuffle pattern as every item above.
      `GET     /api/backlog` for this exact id currently returns `status: "queued"`, `done_sha: null` (not `done`). But
      verifying the cited plan (`plans/archive/issues/mtds_migrate_executor_progress_checkpoint_gap_2026_08_04.md` line
      119-121, the `migrate_sports_casing_2026_07_22.py` checkpoint todo) surfaced a genuine **citation defect**: the
      checkbox was already correctly `[x]` and the checkpoint code genuinely exists (`record_vm_progress` import + call
      confirmed present in the script), but the cited sha `c98e0abb` is a real, on-origin commit that has NOTHING to do
      with this todo — it's an unrelated `market-tick-data-service` test fix
      (`fix(tests): update DEFI shard count 2828→2856…`, same slot-16, ~30 min later). The real checkpoint commit is
      `486c61b2` (`feat(sports): add record_vm_progress checkpoint to migrate_sports_casing_2026_07_22.py`, slot-16,
      2026-08-05T05:44:34Z — confirmed via `git log --follow` on the script + `git blame` on the added lines, both
      ancestors of `origin/live-defi-rollout`). Fixed the citation in the plan doc itself (same-file findings-triage
      fix). No REOPEN (would re-open genuinely-done work) or FLIP (already flipped, honestly, just mis-cited) was
      warranted; this item needed a citation fix, not a status change.
- [x] ✅ [BACKEND] P2. `mtds_migrate_executor_progress_checkpoint_gap-009` (`done_sha=6ddb0374`) — **verified 2026-08-08
      (slot 7): no REOPEN or FLIP action needed or possible — the row this audit item names has already
      self-corrected.** `GET /api/backlog` for this exact id currently returns `status: "queued"`, `done_sha: null` (not
      `done`), same self-correcting `regen_positional_task_ids_not_content_stable_2026_07_17.md` reshuffle pattern as
      every item above. `6ddb0374` is a real, on-origin commit
      (`feat(mtds): add record_vm_progress checkpoint to migrate_sports_casing_revert_2026_07_27.py`, slot-8,
      2026-08-05T04:45:50Z, confirmed ancestor of `origin/live-defi-rollout`) that genuinely added the checkpoint:
      `record_vm_progress` is imported and called (gated on the per-day `Counter` reaching zero) in
      `market-tick-data-service/scripts/sports/k1k2_casing_revert_2026_07_27/migrate_sports_casing_revert_2026_07_27.py`.
      Read the cited plan (`plans/archive/issues/mtds_migrate_executor_progress_checkpoint_gap_2026_08_04.md`, Category
      A): the corresponding todo is correctly `[x]` ✅ and already cites `6ddb0374` accurately — no citation defect here
      (unlike -008's `c98e0abb` mis-citation). So the false-done state the 03:15 UTC audit snapshot captured (backlog
      row `done`, checkbox possibly not yet flipped at that instant) has already been corrected — both the backlog row
      (back to `queued`/`done_sha: null`) and the plan checkbox (honestly `[x]` with an accurate citation) are
      consistent. No REOPEN (would re-open genuinely-done work) or FLIP (already flipped, honestly) was warranted or
      performed; this item only needed its tracker checkbox resolved with the verification trail above.
- [x] ✅ [BACKEND] P2. `mtds_migrate_executor_progress_checkpoint_gap-010` (`done_sha=6ddb0374` at audit time — **same
      sha as -009**) — **verified 2026-08-08 (slot 9): no REOPEN or FLIP action needed or possible — the row this audit
      item names has already self-corrected**, same self-correcting
      `regen_positional_task_ids_not_content_stable_2026_07_17.md` reshuffle pattern as every item above.
      `GET /api/backlog` for this exact id currently returns `status: "queued"`, `done_sha: null` (not `done`),
      `brief: "[DATA] P2. Add \`record_vm_progress\` checkpoint
      to"` — matching the     THIRD, still-open Category-A todo (`migrate_sports_league_id_casing_2026_07_21.py`), not the first     (`migrate_sports_casing_revert_2026_07_27.py`, already correctly claimed by -009's `6ddb0374`). Resolved slot 7's     scoping question: confirmed via `GET
      /api/backlog`that -010's own`done_sha=6ddb0374`citation from the 03:15 UTC     audit snapshot WAS a copied-sha defect (the row never legitimately closed on that sha) — but the backlog has     already self-corrected past it (back to`queued`/`done_sha:
      null`), so there is nothing left to fix on the row     itself. Verified the underlying checkpoint work genuinely is NOT done, confirming the plan checkbox's honesty:     `git
      log -1 origin/live-defi-rollout --
      scripts/sports/league_id_relocation/migrate_sports_league_id_casing_2026_07_21.py`     shows the file's last touch was an unrelated commit (`1970ef45`, defi gas-fees/casing script batch), and     `grep
      -n
      record_vm_progress`against that script at`origin/live-defi-rollout` returns zero hits — no checkpoint     exists. Cross-checked the cited plan (`plans/archive/issues/mtds_migrate_executor_progress_checkpoint_gap_2026_08_04.md`    line 124): the third todo is correctly still`-
      [
      ]`, consistent with both the live backlog (queued, real     unstarted work) and the script (no checkpoint present). No REOPEN (nothing `done`to reopen) or FLIP (work     genuinely isn't done) was warranted or performed; this item only needed its tracker checkbox resolved with the     verification trail above — the real checkpoint work stays live in the backlog as task    `mtds_migrate_executor_progress_checkpoint_gap-010`
      for a future data_engineering dispatch.
- [x] ✅ [BACKEND] P2. `deployment_scripts_bucket_soft_delete_retention_drift-002` (`done_sha=97d37ce57`) — **verified
      2026-08-08 (slot 7): no REOPEN or FLIP action needed or possible — the row this audit item names has already
      self-corrected**, same `regen_positional_task_ids_not_content_stable_2026_07_17.md` reshuffle pattern as every
      item above. `GET /api/backlog` (2,429 rows) has zero rows currently holding the id
      `deployment_scripts_bucket_soft_delete_retention_drift-002` (only the unrelated `-001` orphan,
      `done_sha=2e9c249d7`, survives under this doc family). `97d37ce57` is a real, on-origin commit
      (`docs(plans): exact - [x] brief match for 08-06 pre-gate verification flip…`, slot-6, 2026-08-06T14:33:53Z) that
      flipped the PRE-GATE checkpoint todo (line 104: "Final drain confirmation on/after 2026-08-09" — **VERIFIED
      2026-08-06 (slot-6, infra, PRE-GATE): NOT yet drained**, 98.6% bloat_pct vs done-when ≤9%, explicitly recorded as
      "records the 08-06 verification cycle, NOT the final drain"), not the real final-drain todo — a legitimate,
      honestly-documented interim checkpoint, not an over-claim. Read the cited plan
      (`plans/active/issues/deployment_scripts_bucket_soft_delete_retention_drift_2026_07_31.md`): line 104 is correctly
      `[x]` matching `97d37ce57` exactly, and the REAL final-drain todo (line 114, same title, separate checkbox) is
      correctly still `- [ ]` with a `DEFERRED-BY-DESIGN` marker gating it to on/after 2026-08-09 (today is 2026-08-08 —
      not due yet, confirming this audit item's own "likely REOPEN, not FLIP" hunch was half right: the gate is
      genuinely unmet, but there is no live `done` backlog row left to REOPEN either). No REOPEN (nothing currently
      `done` to reopen) or FLIP (already flipped, honestly, on the correct pre-gate todo) was warranted or performed;
      this item only needed its tracker checkbox resolved with the verification trail above.
- [x] ✅ [BACKEND] P2. `cefi_content_migration_corpus_still_incomplete_relaunch_round3_needed-025`
      (`done_sha=0e9185d2c`) — **verified 2026-08-08 (slot 20): no REOPEN or FLIP action needed — the plan checkbox
      already honestly matches the sha.** `0e9185d2c` (`unified-trading-pm`, slot-11, 2026-08-07T19:22:15Z, confirmed
      ancestor of `origin/live-defi-rollout`) is the **twelfth** dispatch of the time-gated "Round-8 ACTUAL LAUNCH" todo
      in `plans/active/issues/cefi_content_migration_corpus_still_incomplete_relaunch_round3_needed_2026_07_31.md`
      (line 868) — it did NOT launch any VMs (its own text: "UTC=2026-08-07T19:12Z (NOT ≥ 2026-08-08T00:00Z...) ... No
      VMs launched"), it correctly deferred (all 8 shards were AT/OVER the `≤2/(vm-prefix,day)` budget cap) and added a
      gated follow-up todo (line 888, `-026` in the backlog, still genuinely `- [ ]`/`queued`). The checkbox this sha
      touched is `[x]` — consistent with the doc's own established pattern (11 prior "Nth deferred" todos, lines
      688-841, all correctly checked done-as-correctly-deferred, not done-as-launched) — so this was never a false-done
      in truth: "done" here means "this dispatch cycle completed (by deferring honestly)", not "shards launched".
      **Adjacent finding while verifying**: the Cloud Scheduler job meant to auto-flip the `-026` gating prereq
      (`cefi-round8-midnight-prereq-flip`) fired at its scheduled 2026-08-08T00:01:00Z time but FAILED
      (`gcloud scheduler jobs describe cefi-round8-midnight-prereq-flip --location=asia-northeast1     --project=central-element-323112`
      → `status.code=2`, i.e. UNKNOWN/unreachable) — its `httpTarget.uri` is
      `http://13.113.200.22:8765/api/prerequisites/...`, the orchestrator VM's PUBLIC EIP on port 8765, which has NO
      inbound firewall rule (confirmed workspace-wide convention: `/check-agent-orchestrator` skill exists specifically
      because "VM:8765 has no inbound rule"). Its cron (`1 0 8 8 *`) next fires **2027-08-08** — this prereq is now
      stuck false indefinitely, permanently blocking `-026` unless someone manually flips it or fixes the job. Filed as
      a tracked todo in the cefi plan doc itself (see that doc's new Follow-ups todo) rather than fixed inline here —
      root-causing/redesigning the flip mechanism is out of scope for this verification-only item.

## Follow-ups

- [x] ✅ [BACKEND] P2. **Characterise the 1,013 `unresolved` rows.** Confirm the expected explanation (rows whose plan
      was archived, so `plan_ref` no longer resolves at `origin/live-defi-rollout`) actually accounts for the bulk, and
      report the residue that does NOT. A row that is `done` and unresolvable is invisible to this audit forever, so a
      large unexplained residue is a silent-blindspot, not bookkeeping noise. Report the split; do not bulk-mutate. —
      **verified 2026-08-08 (slot 22): expected explanation accounts for 100% of the bulk, zero unexplained residue.**
      Full trail in the Progress Log below.
- [ ] [BACKEND] P3. **Bound the 12 `UNAUDITABLE` (`brief_hash IS NULL`) rows.**
      `regen_positional_task_ids_not_content_stable_2026_07_17.md` already shipped `agent-orchestrator@aaa2db8` to bound
      this tail and the count still moves — re-measure, and confirm every remaining unhashed row is a `done` row (which
      is what bounds the exposure). **➡️ EXTRACTED 2026-08-09 to `ao_satellite_ao_dispatch_batch12_2026_08_09.md` todo 6
      — do NOT action here.**
- [ ] [BACKEND] P3. **Decide whether a standing false-done breach should page.** It currently only transitions Slack
      state via `audit_cron_notify.apply_transition` (breach→breach stays silent, by design), so a breach that never
      clears is silent after its first notify while the systemd unit stays red indefinitely. Confirm that matches the
      actionable-only alerting contract in `/codex/04-architecture/agent-orchestrator-alerting.md`. **➡️ EXTRACTED
      2026-08-09 to `ao_satellite_ao_dispatch_batch12_2026_08_09.md` todo 7 — do NOT action here.**

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

- **2026-08-08 (slot 32, backend_engineer)**: Verdict on `sports_fast_t1_recon_oom_live_capture_outage-003`
  (`done_sha=80265d6` at audit time): **no REOPEN or FLIP action needed or possible** — same self-correcting
  positional-id pattern as the 4 items above. `GET /api/backlog` (2,430 rows) has zero rows with `done_sha=80265d6` and
  no row currently holding this exact id. `80265d67` (deployment-service, slot-12, 2026-08-06) is a real commit that
  fixed a VM-launch guard, not the backfill todo itself. The cited plan
  (`plans/active/issues/sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md` line 497) shows its own Progress Log
  already caught + reverted a premature flip of this exact todo on 2026-08-06 (checkbox restored to `- [ ]` after a
  manifest-only re-check found only 25-57% reachable coverage across the 5 gap days, not full coverage) — the current
  live backlog row for this same todo (`-015`) is correctly `queued`/`done_sha: null`, not `done`. Both the backlog and
  the plan checkbox already reflect the honest state; nothing to correct. See the checklist item above for the full
  trail.

- **2026-08-08 (slot 12, backend_engineer)**: Verdict on `sports_closeout_track_x_hygiene-006` (`done_sha=976786c5` at
  audit time): **no REOPEN or FLIP action needed or possible** — same self-correcting positional-id pattern as the 6
  items above. `GET /api/backlog` (2,429 rows) has zero rows with `done_sha=976786c5` anywhere, and this exact id is now
  `status: "queued"`, `done_sha: null`. `976786c5` (market-tick-data-service, slot-8, 2026-08-04) only built + shipped
  the migration SCRIPT — the dry-run was never executed and that same commit's own plan-flip explicitly left the
  plan-level checkbox open. Verified against the real object count per this item's instruction, not just prose: the
  cited plan (`sports_closeout_track_x_hygiene_2026_07_25.md` line 138) is still honestly `- [ ]`, and the issue doc's
  own gated "Apply the migration to prod" sub-todo
  (`sports_peripheral_bucket_league_vocabulary_contamination_2026_07_20.md`) is still `- [ ]` — no object has actually
  moved, the 9,733-object count is unchanged. Both the backlog and the plan checkbox already reflect the honest open
  state; nothing to correct. See the checklist item above for the full trail.

- **2026-08-08 (slot 18, backend_engineer)**: Verdict on `infra_capture_and_devops_leftovers-001` (`done_sha=c3c65402e`
  at audit time): **no REOPEN or FLIP action needed or possible** — already self-corrected by a different session
  (slot-10) before this task was picked up, same self-correcting positional-id pattern as the 5 items above.
  `GET /api/backlog` shows this exact id now holds an orphaned row with `done_sha=f79fbded3` (not `c3c65402e`).
  `f79fbded3` (slot-10, 2026-08-08T17:26:13Z) is a real commit that genuinely closed the cited plan's Live-ODDS P2 todo:
  api_football second-source wiring correctly STRUCK per operator decision B on `BLK-b969f5f0`, and the live `odds_api`
  VM freshly re-verified RUNNING with a clean run.log. The plan checkbox at
  `infra_capture_and_devops_leftovers_2026_07_06.md` line 292 is correctly `[x]` ✅ and matches `f79fbded3` exactly.
  Nothing to correct. See the checklist item above for the full trail.

- **2026-08-08 (slot 27, backend_engineer)**: Verdict on `defi_cefi_venue_chain_axis_contamination-014`
  (`done_sha=b78ec6e7c` at audit time): **no REOPEN or FLIP action needed or possible** — same self-correcting
  positional-id pattern as the 7 items above. `GET /api/backlog` shows this exact id is currently
  `status: "dispatched"`, `dispatched_to: 17`, `done_sha: null` (not `done`). `b78ec6e7c` (slot-9, 2026-08-04) was a
  genuine false-done AT THE TIME: it only completed step 2 of the 4-step sequenced P1 cleanup at line 330 of
  `defi_cefi_venue_chain_axis_contamination_2026_07_28.md` (its own Progress Log entry says "Step 2 DONE. Steps 1/3/4
  still gated"), and the checkbox there is correctly still `- [ ]`. The live backlog row for this id is now a fresh
  in-flight dispatch to slot 17, not a stale `done` row — the false-done state has already self-corrected. See the
  checklist item above for the full trail.

- **2026-08-08 (slot 30, backend_engineer)**: Verdict on `mtds_migrate_executor_progress_checkpoint_gap-008`
  (`done_sha=c98e0abb` at audit time): **no REOPEN or FLIP action needed on the backlog row** — same self-correcting
  positional-id pattern as the 8 items above (`GET /api/backlog` shows `status: "queued"`, `done_sha: null`). Verifying
  the cited plan checkbox surfaced a real citation defect instead: `c98e0abb` is a genuine on-origin commit but an
  unrelated test fix, not the checkpoint work. The checkpoint itself is real and the checkbox was already honestly `[x]`
  — corrected the citation to the actual commit `486c61b2` in
  `mtds_migrate_executor_progress_checkpoint_gap_2026_08_04.md` (same-file findings-triage fix). See the checklist item
  above for the full trail.

- **2026-08-08 (slot 9, backend_engineer)**: Verdict on `mtds_migrate_executor_progress_checkpoint_gap-010`
  (`done_sha=6ddb0374` at audit time, same sha as -009): **no REOPEN or FLIP action needed or possible** — same
  self-correcting positional-id pattern as the 9 items above. Resolved slot 7's open scoping question:
  `GET /api/backlog` confirms -010's brief matches the THIRD Category-A todo
  (`migrate_sports_league_id_casing_2026_07_21.py`), so the audit-time `6ddb0374` citation (which actually belongs to
  -009's script) was genuinely a copied-sha defect — but the backlog row has already self-corrected to
  `status: "queued"`, `done_sha: null`, so there is no live false-done state left to fix. Confirmed the underlying work
  genuinely isn't done: zero `record_vm_progress` hits in `migrate_sports_league_id_casing_2026_07_21.py` at
  `origin/live-defi-rollout`, matching the plan's own still-open checkbox (line 124). No REOPEN or FLIP performed; the
  real checkpoint work remains correctly queued as its own backlog task. See the checklist item above for the full
  trail.

- **2026-08-08 (slot 7, backend_engineer)**: Verdict on `deployment_scripts_bucket_soft_delete_retention_drift-002`
  (`done_sha=97d37ce57` at audit time): **no REOPEN or FLIP action needed or possible** — same self-correcting
  positional-id pattern as the 10 items above. `GET /api/backlog` (2,429 rows) shows zero rows currently holding this
  exact id. `97d37ce57` (slot-6, 2026-08-06) is a real commit that flipped the PRE-GATE verification checkpoint (line
  104), a legitimate interim checkpoint distinct from the REAL final-drain todo (line 114, same title, separate
  checkbox) — both are correctly stated in the plan doc: line 104 `[x]` matches `97d37ce57` exactly, line 114 is
  correctly still `- [ ]` and `DEFERRED-BY-DESIGN`-gated to on/after 2026-08-09 (not due yet as of today, 2026-08-08).
  Nothing to correct on either the backlog row (already gone/self-corrected) or the plan checkbox (already honest). See
  the checklist item above for the full trail.

- **2026-08-08 (slot 22, backend_engineer)**: Follow-up — **Characterise the 1,013 `unresolved` rows.** Ran
  `audit_false_done.py --json` live against the actual production `state.db` (`agent-orchestrator/data/state/state.db`,
  224MB, on the orchestrator VM itself — this slot runs ON that VM, so no SSM hop was needed) with `--pm` pointed at a
  fresh `origin/live-defi-rollout` fetch (ref `0f6635534`). Live counts have moved since the 03:15 UTC snapshot
  (expected, ongoing churn): `false_done=3` (down from 14 — the other 11 already self-corrected per the checklist items
  above), `honest=745`, `UNAUDITABLE=11`, **`unresolved=1042`** (up from 1,013). **Characterisation**: for each of the
  1,042 unresolved `task_id`s, pulled its `plan_ref` from `state.db`, then checked whether that path's basename appears
  anywhere under `plans/archive/` at `origin/live-defi-rollout` (via `git ls-tree -r --name-only`, 2,768 archive files
  indexed) — i.e., whether the row's plan doc was genuinely archived (the audit script's own hypothesis) rather than
  broken/mis-cited. Result: **1,042 / 1,042 (100%) matched an archived file by basename — zero residue.** Spot-checked 3
  random samples with `git show origin/live-defi-rollout:<literal plan_ref>` (confirmed each fails to resolve, as the
  audit found) cross-referenced against the matching archive path (confirmed each exists, e.g.
  `plans/active/issues/blank_assigned_vm_dispatch_classification_gap_2026_07_26.md` →
  `plans/archive/issues/blank_assigned_vm_dispatch_classification_gap_2026_07_26.md`) — all 3 confirmed genuine
  archival, not coincidence. Caveat noted for rigor: 15 basenames are duplicated across the archive tree (e.g. two
  different `api_host_chronic_impairment_2026_05_29.md` docs in different month folders) — a basename-only match can't
  distinguish which specific archived copy a row's original doc became in that rare case, but it does not change the
  headline finding (still a real archived doc either way, not a broken/dangling `plan_ref`). **Verdict: the expected
  explanation fully accounts for the unresolved bucket — this is bookkeeping noise from normal plan-archival lifecycle,
  not a silent blindspot.** No bulk-mutation performed (per the todo's own instruction); this is a report-only finding,
  no code shipped, no backlog rows touched.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (4 entries), still accurate.

- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep)**: KEEP-NA-STALE, valid — `grep -cE
  '^[[:space:]]*[-*] \[ \]'` = **2**, both citation-pointers already correctly marked `➡️ EXTRACTED 2026-08-09 to
  ao_satellite_ao_dispatch_batch12_2026_08_09.md` (todos 6 and 7) — real remaining work on this doc is zero. Note: the
  round7 (2026-08-08) marker's claim to have flipped `assigned_vm: NA → planning` never actually landed in this doc's
  own frontmatter (still `NA` as of this read) — but this is now moot, since both real items are already covered
  elsewhere; re-flipping would be a pointless duplicate dispatch against work with nothing left to do. Not re-flipping.
