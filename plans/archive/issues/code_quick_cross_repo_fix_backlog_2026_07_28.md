---
doc_type: issue
title: Cross-repo CODE_QUICK fix backlog — all 55 items shipped across 11 repos, fully complete
summary: >-
  Follow-up to the checkbox-honesty pass (prose-trap fix batch + 22-doc archival). Of 420 docs with 1-2 open todos, a
  keyword pre-filter narrowed to 281 "plausibly quick" candidates, which a 9-way parallel read-only classification pass
  split into 22 DOC_ONLY_QUICK (done, landed inline), 55 CODE_QUICK (touch real service code, need per-repo
  quality-gates.sh + commit — this doc), and 204 NOT_QUICK (correctly left untouched). Operator explicitly chose
  "implement them all now" over drafting an AO plan (2026-07-28), then "do all /autonomous" to drive the remainder to
  completion. Round 1 shipped unified-api-contracts's 2 items (2026-07-28); Round 2 (9 parallel sub-agents, one per
  repo) shipped 51 non-MTDS items (2026-07-28); Round 3 (single agent, dispatched only once MTDS's live concurrent WIP
  finally cleared on a 3rd liveness recheck) shipped the final market-tick-data-service batch + the 3-repo cqg-wiring
  item (2026-07-29). All 55 items done.
status: resolved
nature: issue
asset_group: [meta]
stage: [meta]
repos:
  [
    market-tick-data-service,
    unified-api-contracts,
    unified-trading-pm,
    unified-trading-library,
    features-service,
    agent-orchestrator,
    instruments-service,
    deployment-service,
    deployment-api,
    unified-trading-system-ui,
    market-data-processing-service,
    ml-service,
    trading-agent-service,
  ]
scope: [engineer]
tags: [cross-repo, code-fix, backlog, plan-hygiene, checkbox-honesty]
related: []
created: "2026-07-28"
parent_epic: infrastructure_master
source: "main session, 2026-07-28, following the checkbox-honesty pass on the 1-2-open-todo bucket"
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
drift_direction: advance-code
depends_on: []
resolved_by:
  "All 55 items shipped across 11 repos over 2026-07-28/29 (see per-repo Status section + Progress Log for full sha
  evidence). market-tick-data-service (~15 items) + the cqg-wiring item were the last to land, on 2026-07-29 once that
  repo's live concurrent WIP cleared."
locked_by:
locked_since:
---

> **🟢 ARCHIVED 2026-07-29** — status=resolved, all 55 items shipped, 0 open todos, moved to
> `/plans/archive/issues/code_quick_cross_repo_fix_backlog_2026_07_28.md`. Archived per
> `/codex/11-project-management/issue-doc-lifecycle.md`'s archive-on-resolve rule.

# Cross-repo CODE_QUICK fix backlog — all 55 items shipped, complete

## Status per repo

- [x] **unified-api-contracts (2 items) — SHIPPED**: `unified-api-contracts@cb9e97dfd`. Dead
      `service_emission_policy.py` deleted; 7 lending protocols' `instrument_types` retrofitted to
      `[A_TOKEN, DEBT_TOKEN]`. Both source docs archived.

- [x] **market-tick-data-service (~15 items) — DONE 2026-07-29** once the repo's live concurrent WIP finally cleared
      (dispatched on the 3rd liveness recheck; the agent hit the session's API session-limit 3 times mid-task and was
      resumed each time from its transcript, not restarted). Real fixes shipped: `df3d55dd` (base_defi_adapter
      success-key), `f2f89fad` (`_solana_pda.py` address-primitives extraction), `cc4c92a6` (CAS DNS-resolver swap,
      stricter than the doc's literal ask), `45924760` (Tardis epoch-unit fix), `d797df2e` (do_merge dtype-coercion
      narrowing), `5bf8a3c7` (batched: kalshi/rebuild_prediction_manifest dead-code, data_manifest_handler dead-code,
      lst_rates_handler empty-marker fix, pool chain-collision MTDS half, VM-name-collision regression test), `a6e0a788`
      (unrelated dep re-pin needed to unblock QG), `dc82b08d` (the 12th/final repo for
      `qg_workspace_root_template_drift_12_repos_2026_07_24`, now separately archived). 3 items STALE-SKIPPED after
      verification (progress-checkpoint and VM-name-collision fixes already shipped by a predecessor slot;
      sports-timeout flaky-test fix superseded by a concurrent session's better version, conflict resolved in their
      favor). 2 items genuinely out-of-scope (autouse-fixture pattern + wallclock field-derivation both trace to source
      docs whose target files are outside the confirmed 26-file disambiguation list — untouched, not silently dropped,
      their own source docs remain open). **File-size/function-size QG violations resolved via real extraction,
      verified**: `rebuild_prediction_manifest.py` 909L→708L (extracted `_rebuild_prediction_emit.py`),
      `orchestrator/__init__.py` 912L→813L (moved a function into `preflight.py`), `_download_all_instruments()`
      56L→48L. Full quality-gates.sh green at final HEAD, confirmed via 2 independent fresh runs. One operator-worth
      flag surfaced (not auto-fixed): `lst_rates_handler.py`'s source doc carries an invalid
      `locked_by: live-defi-rollout` / `locked_since: 2026-05-21` artifact (impossible date, non-agent locker) — left
      as-is for operator attention, not auto-unlocked.

- [x] **unified-api-contracts + instruments-service cqg-wiring half of
      prediction_satellite_ao_dispatch_batch5_2026_07_26 — DONE 2026-07-29.** `unified-api-contracts@283d7449` (additive
      `InstrumentRecord.canonical_question_group` field + schema entry), `instruments-service@38e393de`
      (Polymarket/Kalshi adapters write `group.value` back; catalogue builder reads it per-row instead of the
      always-empty path-level value), market-tick-data-service dead-code half already covered by `5bf8a3c7` above. The
      batch5 plan + its finalize plan both fully executed and archived to `plans/archive/2026_07/`.

- [x] **unified-trading-pm scripts (13 items) — DONE.** 10 shipped fresh, 3 verified already-fixed by concurrent
      sessions (not assumed — re-verified live). Shas: `b4f418bb4` (RLIMIT_AS hardening), `91324d0b1` (frozen tmp_path,
      archived), `4c8dbb8bc` (citation ratchet fix, archived), `75adf01c4` (BLK_ID_RE + tests), `5acc25839` (quickmerge
      deletion fix, archived), `6e791d478`+11 fleet repos (WORKSPACE_ROOT= drift — MTDS's copy staged but blocked by its
      live conflict, documented not force-resolved), `2db15bb21` (Slack env fallback), `78fadefd7` (new
      `check_priority_tier_policy.py` hygiene script), `8a5693a4e`+`fd06d1dee` (SIGTERM trap + worker.md, archived).
      Stale-skipped (verified, not assumed): plan_discipline_unquoted_deferred_by_design, qg_5_83 timeout,
      quickmerge_silent_push_failure — all archived with evidence. UI-coverage generator-script half done jointly with
      the UI agent (`unified-trading-system-ui@7900f560`). Surfaced a real infra finding:
      `plans/active/issues/shared_clone_concurrent_commit_message_swap_2026_07_28.md` (P1) — this shared clone showed
      git-plumbing-level contamination under 9-agent concurrent load (index races, foreign-file sweep-ins, one hard
      conflict); every agent this round adopted a "verify content after every commit, never trust exit code alone"
      recovery pattern.

- [x] **unified-trading-library (4 items) — DONE.** `unified-trading-library@0db19a72` (all 3 real fixes: capped
      `_CANONICAL_CACHE` eviction in `_state.py`, narrowed the broad `except` in both `_read_availability_index_slim`
      and `read_availability_index`, regression tests for both). `bucket_fold_features_2026_07_17`'s UTL half was
      already done (`055948e3`, 2026-07-19) — verified grep-clean, stale-skipped correctly. All 3 real-fix docs
      archived.

- [x] **features-service (6 items) — DONE.** `87e73cee` (4 MTDS chain-scoping flags + a real bug fix found while
      auditing: `--asset-group CEFI` was silently writing DeFi Hyperliquid data under the CEFI shard), `c5e0f336`
      (end_date fallback), `d06919bf` (User-Agent header, doc stays active — 1 operator-gated todo left), `bfac5033`
      (`_scan_input_coverage` filter fix), `ab53855b` (silent_wrong_answer_audit — 1 fix already shipped by a peer, 1
      genuinely missing and fixed fresh; 2 untracked prose findings converted to real todos in
      `silent_wrong_answer_audit_untracked_followups_2026_07_28.md`). candle_canonical_path_migration_execution's 18th
      item verified already shipped (`d16ed8aa`, 2026-07-27) — stale-skipped correctly, no PM edit needed. All resolved
      docs archived, referrers fixed.

- [x] **agent-orchestrator (5 items) — DONE.** `587c8db` (Mode-2 archive-fallback + same-commit-rename detection, 2
      fixes in one commit), `c72197d` (spawn_base_role liveness fix), `78d4b59` (WALL_TYPES fold — fleet grep found a
      3rd gap, `sit-gate.yml`'s `harness_lint`, folded too), `9a68cd2` (baseline-ratchet regression fix + fleet-wide
      `--update-baseline` stamping missing commit anchors on 18/25 repos, bonus). All 5 flipped + archived. Added a
      missing STEP 5.101 codex catalogue entry (was undocumented fleet-wide since 2026-07-08).

- [x] **instruments-service (4 items + baseline-ratchet) — DONE.** `3c424e61` verified already covering
      sports_t0_t1_dependency_gate (stale-skipped correctly, fixed a stale duplicate todo elsewhere too), `696921d3`
      (empty-write guard in `recover_fixtures_from_truthset.py`), `f7e64c54` (`--run-tag` wiring + 7 tests), `bd1fdc87`
      (incidental: unblocked the entire test suite from a pre-existing unrelated DeFi golden-fixture drift).
      Baseline-ratchet 366→362. All archived.

- [x] **deployment-service (3 items) — DONE.** `841f464` (scheduler_env_prefix fix, live-verified via a real
      pause/suppress/resume cycle against a real Cloud Scheduler job), `76a2459` (terraform IAM Group-B join half),
      baseline-ratchet (anchor-stamped, no ratchet room left — live count already at ceiling). Archived.

- [x] **deployment-api (2 items) — DONE.** `1562558` (sports:1800 staleness budget mirrored into health_consolidator.py,
      doc stays active — 1 unrelated todo left), `ea8b9b7` (Cloud Build timeout 600s→900s, archived). Surfaced the
      shared_clone_concurrent_commit_message_swap finding (see above).

- [x] **unified-trading-system-ui (2 items) — DONE.** `7900f560` (VenueAssetGroupV2→VenueCategoryV2 rename +
      CROSS_CATEGORY member across 21 files, tsc/eslint/tests clean; residual regen-drift split into its own tracked
      todo, `ui_coverage_ts_regen_content_drift_after_venue_category_v2_rename_2026_07_28.md`), `145bf5dd` (Batch 5
      Playwright spec — 4/6 tests genuinely green with pw:L2 evidence, 2 hit a pre-existing unrelated host-contention
      auth-redirect race, honestly reported and filed separately as
      `ui_playwright_admin_gated_route_login_redirect_race_under_host_contention_2026_07_28.md` rather than claimed
      passing). Both archived.

- [x] **Mechanical baseline-ratchet re-run across 5 repos — DONE.** `unified-trading-pm@637055f9a` +
      `unified-trading-pm@a2225fb38`. Correction to the original scope note: the baseline is ONE shared PM-repo file
      (`scripts/quality_gates/no_empty_string_fallback_baseline.yaml`), not 5 independent per-repo files — all 5
      dispatched agents were writing the same file; the dead-WIP liveness protocol correctly prevented duplicate work
      and folded every repo's numbers into one commit (ml-service 8→6, trading-agent-service 2→1, instruments-service
      366→362, deployment-service anchor-stamped at ceiling, mtds already done earlier). Flipped in
      `mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md`.

## Full classification data — now mostly historical

Raw per-doc classification data for the original 281-candidate triage is saved in the session scratchpad (NOT durable,
will vanish with the session):
`/private/tmp/claude-501/-Users-ikennaigboaka-Code-unified-trading-system-repos--tabs-4/60ea16ec-43a4-4dcc-a3f2-7baea3767b5e/scratchpad/{quick_candidates.tsv,not_quick_mechanical.tsv,one_to_two_todo_files.tsv,qc_batch_*}`.
Low value now that 53/55 items are shipped with evidence above — only worth pulling if this doc itself is ever lost.

## Progress log

**2026-07-28, Round 1** — Initial fan-out: 9 parallel read-only agents classified 281 docs. 2 repo-fix agents dispatched
(market-tick-data-service, unified-api-contracts). unified-api-contracts shipped (`cb9e97dfd`). market-tick-data-service
hit 2 real quality-gates.sh violations and was left uncommitted pending a proper trim. Session moved to `/pre-compact`
before Rounds 2-6 — this doc was created to survive compaction.

**2026-07-28, Round 2 (`/autonomous` resume)** — Checked market-tick-data-service first: found live concurrent WIP
(unresolved conflict, 88s-old mtime, live PID) and deliberately skipped it rather than collide. Dispatched 9 parallel
sub-agents (one per remaining repo), each pasted the full `SUB_AGENT_MANDATORY_RULES.md` + `AUTONOMOUS_AGENT_RULES.md`
contract. **Recurring operational pattern across ~6 of the 9 agents**: they backgrounded their `quality-gates.sh`/
`quickmerge` runs and ended their turn expecting an auto-wake that doesn't reach sub-agents — each was caught via its
task-notification and resumed with an explicit "run it as a blocking foreground call" instruction; all recovered and
finished. All 9 agents completed successfully — 51 items shipped/verified across unified-trading-pm, features-service,
agent-orchestrator, unified-trading-library, instruments-service, deployment-service, deployment-api,
unified-trading-system-ui, and the ml-service+trading-agent-service baseline-ratchet pair. Rechecked
market-tick-data-service again afterward: still live (6-second-old mtime on the same file set) — deferred a second time
rather than collide; likely another concurrent session already working this exact backlog. Separately found and fixed an
incomplete archival left over from the unified-trading-library agent's work: 3 issue docs had an archive copy created on
origin but the stale `plans/active/issues/` duplicate was never removed (a shared-clone commit race dropped the
delete-half of the move) — completed via `unified-trading-pm@e2f568370`. **Remaining**: market-tick-data-service (~15
items) + its coordinated cqg-wiring item, both blocked purely on that repo's live concurrent activity, not on any
decision or credential. Recheck liveness before dispatching; if another session already finished it, verify via
`git log` rather than redoing the work.

**2026-07-29, Round 3 (closeout)** — Rechecked market-tick-data-service a 3rd time: mtime finally 5+ minutes stale, no
unmerged conflicts — dispatched a single agent for the full remaining scope (~15 MTDS items + the 3-repo cqg-wiring
item). The agent's own session hit the API's session-limit 3 separate times mid-task (a hard external resource
constraint, not a bug); each time it was resumed from its transcript via `SendMessage` rather than restarted, and it
picked back up correctly each time with no lost work. Finished cleanly: real fixes for all live items, 3 correctly
identified as already-shipped by a predecessor slot (stale-skipped, verified via git log rather than assumed), 2
correctly left out-of-scope (target files outside the confirmed file list), the 2 file-size + 1 function-size QG
violations resolved via genuine code extraction (not reformatting), full quality-gates.sh green. Separately completed
`qg_workspace_root_template_drift_12_repos_2026_07_24`'s last remaining repo (MTDS was the 12th/final, blocked earlier
by the same live-WIP conflict) — archived that doc too (`unified-trading-pm@8f5460af4`). **All 55 CODE_QUICK items are
now shipped; this tracking doc is archived alongside them.** Verified via the repo's own hygiene scripts, not just
self-reports: `check_archive_candidates.sh` → "No archive candidates found", `check_terminal_status_archived.py` → 0
violations — every doc that reached 0 open todos this session was actually archived, not just checkbox-flipped.
