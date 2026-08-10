---
doc_type: plan
title: AO satellite AO batch 2 — finalize
summary: >-
  Gated closeout for ao_satellite_ao_dispatch_batch2_2026_07_30.md — machine-held via depends_on + gate_on_depends until
  every todo in that batch is done. Reconciles each completed todo's evidence back into its TRUE source issue doc (the
  batch was an extraction, so the source docs' own checkboxes are the ones that go stale), re-checks whether any
  Deferred item's gate has since cleared (the time-gated item in particular — its 2026-08-02 date will likely have
  passed by the time this finalize runs), archives the source docs that reach zero open todos, and runs the standard
  6-step archival ritual on the batch plan itself.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-2, finalize]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch2_2026_07_30.md,
    /plans/archive/2026_07/ao_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/archive/2026_07/ao_satellite_ao_dispatch_batch1_finalize_2026_07_26.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-30"
last_updated: "2026-07-30"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: review
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [ao_satellite_ao_dispatch_batch2_2026_07_30]
gate_on_depends: true
sequential: true
source: >-
  Operator ruling 2026-07-24 (task_template.md §4) — every AO-dispatched plan needs a gated finalize plan. Authored in
  the same turn as its batch by the /ag-closeout-audit ao skill run of 2026-07-30.
context_scope:
  [
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /plans/active/ao_satellite_ao_dispatch_batch2_2026_07_30.md,
  ]
---

# AO satellite AO batch 2 — finalize

> **Machine-gated on `/plans/active/ao_satellite_ao_dispatch_batch2_2026_07_30.md`** (`depends_on` +
> `gate_on_depends: true`) — will not dispatch until every todo in that batch is `done`.
>
> **`status: active`** — machine-gated (not draft-gated): `depends_on` + `gate_on_depends: true` already holds every
> task of this finalize doc until batch2 finishes, so no separate draft flip is needed. **The gate is CURRENTLY CLOSED**
> — `ao_satellite_ao_dispatch_batch2_2026_07_30.md` still has open todos — this doc will not dispatch until batch2
> reaches 0 open todos.

## Todos

- [x] ✅ [REVIEW] P0. **Re-verify every batch-2 done-claim against reality, not against its checkbox** — for each of the
      8 todos in `/plans/active/ao_satellite_ao_dispatch_batch2_2026_07_30.md`, re-run `git show --stat <sha>` for every
      cited commit and re-run the specific named test(s) directly rather than trusting the claim, and re-run each todo's
      own stated done-when check where it is a command (the na-eligibility-timer fire-completion read, the orch_token
      reporter-staleness read, the JWT-secret token-survives-restart + healthz check, the 4 orphan-commit dispositions,
      the wip-preserve ref disposition). **NOTE (plan_reconciler agt-c7578b, 2026-08-10)**: the na-eligibility-timer
      item and the wip-preserve-ref item were EXTRACTED 2026-08-09 to `ao_satellite_ao_dispatch_batch10_2026_08_09.md`
      (todos 1/2) and never completed inside batch2 itself — do NOT expect a done-when check to succeed against batch2
      for those 2 specifically; check batch10's own evidence for them instead. **Done when**: all 8 verified, and any
      claim whose evidence does not hold up is re-opened as a new tracked todo in this doc's Progress Log with the
      discrepancy stated.

      **VERIFIED 2026-08-10 (slot 30, review) — all 8 done-claims hold against reality, no discrepancies.** Re-ran
                  `git show --stat` + `git merge-base --is-ancestor` + content-diffs and re-ran the named tests directly:
                  (1) `ao_done_gate_no_carveout...` — `agent-orchestrator@22a14b1`/`@e1b30f5`/`@587c8db` all ancestors of
                  `origin/live-defi-rollout`; all 3 sub-item code paths live on HEAD (`_diff_blocks_checkbox`+`_ADDED_BLOCKED_LINE_RE`
                  +`todo_blocked_pending_other_owner`, `_marker_disposition_in_text`+`_mode1_fallback_disposition`+
                  `_mode2_no_recent_commit_disposition`, rename-following `_same_commit_added_path_matching_basename` +
                  `_flips_at_path_or_rename`/`_cancels_at_path_or_rename`/`_defers_at_path_or_rename`); re-ran
                  `tests/test_done_gate_plan_flip_hard_reject.py` = **42 passed** (all 8 named regression tests present, pass).
                  (2) `branch_reset_to_origin...` — all 4 orphan commits confirmed NOT on origin (`features-service@207afd62`,
                  `@d1c1ad8a`, `unified-api-contracts@724bd9be`, `agent-orchestrator@559452e`), all 4 replacements ON origin
                  (`a90256f5`, `a9429cba`, `698b5b6f`, `09cda29`), `git diff 724bd9be 698b5b6f --stat` EMPTY (byte-identical), route +
                  test file for `09cda29` live. (3) `mtds_backfill_sequential_true...` — `agent-orchestrator@77769ab` on origin,
                  `current_task_ids_by_plan`+`_wire_sequential_prereqs` code live; re-ran `tests/test_regen_reconcile.py` = **19
                  passed** (regression test `test_sequential_reword_mid_flight_does_not_corrupt_chain` present at :324). (4)
                  na-timer (EXTRACTED → batch10 todo 1) — batch10's own evidence re-checked: `agent-orchestrator@17939c3`
                  (TimeoutStartSec 2450→21600) on origin; live `state.db` shows `agent_kind=na_eligibility_auditor`
                  `exit_reason=lifecycle-complete` rows incl. the exact cited `agt-b831d5` + fresh `agt-ffd0db`/`agt-a70469`
                  (3 lifecycle-complete current; `reaped-stale` is a separately-tracked mode, out of this todo's scope). (5)
                  orch_token — source doc's own `[x]` MOOT verdict (2026-08-06 loopback-preference) present; live `/api/fleet/git-health`
                  confirms `ip-172-31-5-118` 34/34 slots `reporter_stale=false`. (6) JWT-secret — `/etc/systemd/system/
                  orchestrator.service.d/jwt-secret-gcs.conf` present (systemd env carries `ORCHESTRATOR_JWT_SECRET_GCS`), unit active.
                  (7) `dispatch_sequential_gate...` — `unified-trading-pm@41a51d9ff` on origin; both codex docs state the
                  gate-on-`sequential:true` behavior + cite `agent-orchestrator@867b1731e`. (8) wip-preserve (EXTRACTED → batch10
                  todo 2) — `git ls-remote origin 'refs/wip-preserve/*'` empty; `staging-lock-check.yml` byte-identical between
                  `a77eb6d1` and `strategy-service@400d3773` (ON origin); current HEAD file is the thin-caller stub. No claim failed
                  verification; no new todo required.

- [x] ✅ [REVIEW] P0. **Reconcile each todo's evidence into its TRUE source doc (8 docs, listed below)** — batch 2 was
      an extraction, so the 8 source-doc items it covers are the ones that go stale, not the batch's. Flip the specific
      todo in each of: `ao_done_gate_no_carveout_for_red_gate_evidence_only_closure_2026_07_28.md` (3 of its 4 todos),
      `branch_reset_to_origin_orphans_unpushed_worker_commits_2026_07_27.md` (both `[WORKER] P1` checkboxes, with
      per-item MOOT-SUPERSEDED-or-recovered dispositions),
      `mtds_backfill_sequential_true_dispatch_order_violated_2026_07_29.md` (both todos),
      `na_eligibility_auditor_timer_not_yet_installed_2026_07_27.md` (its SCRIPT P3 item only),
      `git_status_reporter_stale_public_url_token_expiry_2026_07_24.md` (its INFRA P3 item),
      `orchestrator_jwt_secret_not_pinned_causes_fleet_git_status_outage_2026_07_24.md` (its DEVOPS P1 item),
      `dispatch_sequential_gate_fix_2026_07_24.md` (its DOCS P1 item — confirm operator sign-off was actually obtained
      before this flip, per that todo's `[OPERATOR]` tag), and `wip_preserve_refs_silently_unrecovered_2026_07_29.md`
      (its `[DATA] P2` item only). **DONE 2026-08-10 (slot 28, review)** — all 8 source docs already have their target
      checkboxes flipped with the correct evidence SHAs (verified via per-doc read, 0→4 open→checked across the set). No
      new flips needed; the evidence was reconciled organically by the workers who shipped each fix. Summary per doc:
      (1) `ao_done_gate`: all 4 [x] ✅ with agent-orchestrator@22a14b1/@e1b30f5/@587c8db/@3839380, all ancestors of
      origin; (2) `branch_reset`: both WORKER P1 items [x] ✅ SUPERSEDED with per-orphan dispositions, verified
      byte-identical on origin; (3) `mtds_backfill`: both [x] ✅ with agent-orchestrator@77769ab/@3474b95, tests re-ran
      green; (4) `na_eligibility`: SCRIPT P3 [x] ✅ with agent-orchestrator@17939c3 + live state.db lifecycle-complete
      rows; (5) `git_status`: INFRA P3 [x] ✅ MOOT — loopback fix removed token dependency, reporter_stale=0 live; (6)
      `jwt_secret`: DEVOPS P1 [x] ✅ — .env.local literal + systemd drop-in, token-survives-restart proven; (7)
      `dispatch_sequential`: DOCS P1 [x] ✅ — operator sign-off obtained 2026-08-06 + 2026-08-08, both codex docs cite
      sequential gate; (8) `wip_preserve`: DATA P2 [x] ✅ SUPERSEDED — byte-identical content on origin, ref deleted.
      **Done when**: satisfied — all 8 source docs' target checkboxes were already committed with real SHAs/evidence; no
      additional commits needed.
- [x] ✅ [INFRA] P0. **Re-check every Deferred item's gate and spin the cleared ones into batch 3** — walk both Deferred
      sections of the batch plan and, for each entry, state whether its named gate has cleared: the 7 design/judgment
      forks (re-check whether any has since been operator-ruled or the source doc itself narrowed to one direction), the
      cross-tranche-claimed item (re-check whether `na_docs_validity_and_ao_eligibility_audit_2026_07_26.md`'s
      conflict-check todo has landed — if so, this item's status changes from "claimed elsewhere" to "archivable" or
      "genuinely orphaned again" depending on what that check found), and the time-gated item
      (`ao_done_require_origin_not_enforced_2026_07_29.md` — by the time this finalize runs, **2026-08-02 will very
      likely have passed**; re-measure the `on_origin=False` rate over the now-available fuller-volume window and either
      spin it into batch 3 or record why it's still not ready). **Done when**: each entry is marked cleared-and-moved
      (naming the new batch-3 plan and todo) or still-gated with the current reason — no entry left unstated.

      **DONE 2026-08-10 (slot 17, infra) — walked all 11 entries across the batch plan's THREE Deferred sections (the
          9 design/judgment forks in section A, the 1 cross-tranche item in section B, the 1 time-gated item in section C);
          every gate re-checked against its current source doc. Result: 9/11 gates CLEARED and the items fully resolved in
          their own source docs — NONE retain dispatchable work, so NO new todo is added to `ao_satellite_ao_dispatch_batch3`
          (batch 3 = `plans/active/ao_satellite_ao_dispatch_batch3_2026_07_31.md`, already active with its own todo set); the
          2 remaining are genuinely still-gated (operator-held, corroborated by batch12's own 2026-08-09 "Declined, zero
          extraction" verdict). Per-entry disposition:**

          **Section A — design/judgment forks (9):**
          (1) `ao_context_pct_0_for_monitor_heavy_workers_2026_07_29.md` — **STILL GATED**. Doc `status: open`, 3 open todos.
          The named gate (DATA P3's "prefer (b) if it proves reliable enough" two-direction call) has NOT been operator-ruled
          and the doc has not committed to one path; UI P2 depends on it and BACKEND P3 is upstream-CLI-gated. batch12
          (2026-08-09) independently lists it operator-gated (22). (2) `ao_self_pull_stalled_by_untracked_backup_files` —
          **CLEARED/MOOT** — resolved + archived 2026-07-30 (`agent-orchestrator@61b7a4f` time-gated `_track_dirty_tick`
          alert, verified; `@b5fb9fc`), 0 open. (3) `external_promote_gated_task_redispatch_churn_no_durable_park` —
          **CLEARED** — fork operator-ruled (Option A) 2026-07-31, resolved + archived 2026-08-06, 0 open. (4)
          `mdps_odds_horizon_bucket_launch_prep_stale_todo_duplicate_dispatch` — **CLEARED** — sole open todo closed by
          operator ruling 2026-08-06, archived 2026-08-07, 0 open. (5) `two_agents_slot3_collision_and_yahoo_finance_red_tree`
          — **CLEARED** — fork operator-ruled (ao round-5 item 15, collision-warning mechanism + hunk-scope staging)
          2026-08-08, archived, 0 open. (6) `unified_trading_pm_stash_pile_accumulation` — **STILL GATED**. Doc `status:
          open`, 2 open `[OPERATOR] P3` mechanical-drop todos — the judgment-call review IS done (all 188 entries audited
          2026-08-08/09), but `git stash drop`/`clear` is categorically agent-blocked by `block_destructive_commands.py`, so
          the drop loops must be run by the operator directly; batch12 (2026-08-09) concurs. (7)
          `prediction_trades_migration_concurrent_dispatch` — **CLEARED** — fork resolved: convention written + dispatcher
          `in_flight_elsewhere` check shipped `agent-orchestrator@9e28a36` (2026-08-06), operator ruling recorded 2026-08-09,
          archived, 0 open. (8) `na_eligibility_auditor_timer` P2 timeout-retune — **CLEARED** — "bump vs diagnose" fork
          resolved via bump: `agent-orchestrator@17939c3` (2026-08-04) raised `--max-time` 2400→7200s + `TimeoutStartSec`
          2450→21600s (also applied to sibling `ag-closeout-auditor` timer); doc archived 2026-08-06, 0 open. (9)
          `wip_preserve_refs_silently_unrecovered` two SCRIPT P3 items — **CLEARED** — both forks operator-ruled 2026-08-06 and
          shipped as P1: daily fleet-wide sweep (`agent-orchestrator@d36219c` `WipPreserveSweepWatchdog`), local-only-tier
          rescue (`unified-trading-pm@f60d3caa9`), quickmerge post-push verification FAIL-not-warn
          (`unified-trading-pm@98b99afa2`); doc archived, 0 open.

          **Section B — cross-tranche-claimed (1):** (10) `blank_assigned_vm_dispatch_classification_gap` — **CLEARED** —
          the conflict-check todo batch2 flagged as claimed by `na_docs_validity_and_ao_eligibility_audit_2026_07_26.md` HAS
          LANDED: the source doc's own `[REVIEW] P2` (DONE 2026-07-30 slot-15, zero conflict-check hits over the 30 flipped
          docs) AND `na_docs_validity`'s folded-in copy (line 178 `[x]`) are both done. Per this todo's own framing the item
          resolves to **archivable** — the check found no genuine conflicts, and the doc is itself `status: resolved` +
          archived 2026-07-30 (57-file classification + `docspec.py` `Req.R` gate fix `unified-trading-pm@e88c41727`).

          **Section C — time-gated (1):** (11) `ao_done_require_origin_not_enforced` — **CLEARED** — the `on_origin=False`
          rate WAS re-measured over the now-fuller window: 0/151, 0/52, 0/222 (all 0.0%) after the `_sha_on_origin`
          fallback-fetch fix (`25d497f`); operator explicitly ruled 2 days sufficient and flipped `done_require_origin=true`
          default (`agent-orchestrator@cf7cd35`, re-verified an ancestor of `origin/live-defi-rollout` today); doc resolved +
          archived, 0 open.

          **Net: 9/11 cleared (all resolved/archived in-source, nothing left to dispatch — no batch-3 todo added);
          2/11 still-gated (`ao_context_pct_0`, `stash_pile`), both operator-held; every entry stated.**

- [ ] [REVIEW] P0. **Archive every source doc that has reached zero open todos, and repoint any referrer.** At minimum
      re-check `ao_done_gate_no_carveout_for_red_gate_evidence_only_closure_2026_07_28.md` (its 4th, DOCS todo may still
      be open if the codex sign-off didn't land in time),
      `branch_reset_to_origin_orphans_unpushed_worker_commits_2026_07_27.md`,
      `mtds_backfill_sequential_true_dispatch_order_violated_2026_07_29.md`,
      `na_eligibility_auditor_timer_not_yet_installed_2026_07_27.md` (its P2 timeout-retune item likely still open — do
      not archive if so), `git_status_reporter_stale_public_url_token_expiry_2026_07_24.md`,
      `orchestrator_jwt_secret_not_pinned_causes_fleet_git_status_outage_2026_07_24.md`,
      `dispatch_sequential_gate_fix_2026_07_24.md`, and `wip_preserve_refs_silently_unrecovered_2026_07_29.md` (its 2
      SCRIPT items likely still open — do not archive if so). Run the standard 6-step archival ritual (migrate any
      DEFERRED item → banner → codex-alignment check → update CLAUDE.md/codex if a contract changed → fix every
      referrer's path corpus-wide → clear the lock) on any doc that IS fully done. **Done when**:
      `grep -rl <slug> plans/ codex/` returns only the archived copy's own path for each archived doc, and
      `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` reports zero hard failures.
- [ ] [INFRA] P0. **Run the 6-step archival ritual on the batch plan itself, then regenerate the inventory** — banner
      `/plans/active/ao_satellite_ao_dispatch_batch2_2026_07_30.md`, migrate any still-Deferred item into batch 3 (never
      leave a deferral that is not already a `- [ ]` todo somewhere), move the file to `plans/archive/2026_07/`, fix
      every corpus-wide referrer including this finalize plan's own `related:`/`depends_on:`, then run
      `.venv/bin/python scripts/plan-hygiene/regenerate_active_plan_inventory.py`. **Done when**: the batch plan is
      archived with a banner, the inventory regenerates with an orphan count of 0, and `check_finalize_plan_coverage.py`
      no longer names this pair.

## Codex SSOTs

`/codex/11-project-management/` (findings triage + the archival ritual),
`/codex/11-project-management/cross-reference-path-convention.md` (the corpus-wide referrer fixup),
`/codex/12-agent-workflow/commit-push-flip-rule.md` (evidence-backed flips),
`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility".

## Progress Log

- **2026-07-30** — Authored in the same turn as its batch by `/ag-closeout-audit ao` (autonomous mode).
  `sequential: true` is deliberate here: the five todos are a genuine chain (verify → reconcile → re-check gates →
  archive sources → archive self) and several touch the same files. Left `status: draft`.
- **2026-08-06 (/plan-reconcile ao)**: corrected the stale body banner — frontmatter is `status: active` (machine-gated
  via `depends_on`+`gate_on_depends: true`, not draft-gated; the 2026-07-30 entry above records the authoring-time state
  only). Banner text fixed; no dispatch-readiness change — the gate itself is still closed (batch2 has open todos).
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: re-verified context_scope (5 entries) — all paths resolve, still the correct archival
  SSOT + batch-sibling set; no change needed. Gated finalize doc, no source path.
- **context-scout 2026-08-07**: re-scouted; context_scope unchanged (5 entries), still accurate — genuine `*_finalize`
  gate, every todo points at other docs, no source path applies.
- **2026-08-10 (slot 30, review)**: todo 1 done — re-verified all 8 batch-2 done-claims against reality (SHAs
  ancestor-checked against `origin/live-defi-rollout`, content-diffs, live host/DB reads, and direct re-runs of the
  named test files `tests/test_done_gate_plan_flip_hard_reject.py` = 42 passed + `tests/test_regen_reconcile.py` = 19
  passed). Every claim holds; no discrepancy to re-open. The 2 EXTRACTED items (na-timer, wip-preserve) were checked
  against batch10's own evidence per the plan_reconciler NOTE. Full per-claim evidence in the flipped todo.
- **2026-08-10 (slot 17, infra)**: todo 3 done — walked all 11 Deferred entries across the batch plan's three Deferred
  sections and re-checked every gate against its live source doc. 9/11 cleared and fully resolved in-source (all three
  batch2 Deferred sections), 2/11 still gated (both operator-held; batch12's 2026-08-09 zero-extraction verdict
  independently corroborates). Because every cleared item's work already shipped through its own source doc or a later
  batch, NO new todo was added to `ao_satellite_ao_dispatch_batch3_2026_07_31.md` — the "spin into batch 3" branch of
  the todo's done-when is met by recording the actual absorbing location for each cleared entry. Full per-entry
  disposition in the flipped todo.
