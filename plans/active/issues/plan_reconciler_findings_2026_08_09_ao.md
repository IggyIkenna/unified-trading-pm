---
doc_type: issue
title: "plan_reconciler daily deep reconciliation run — ao tranche, 2026-08-09"
summary: >-
  Run-findings doc for plan_reconciler dispatch agt-fe4564 (slot 21, 2026-08-09), TRANCHE=ao. Corpus: 87 active/issue
  docs tagged asset_group: ao; 54 are in the 12h grace window (heavy concurrent AO-tranche activity from sibling slots
  at run time) and read-only this run, leaving 33 non-grace docs (~796KB) as the actionable set. Normative refs
  (PLAN_FORMAT.md/task_template.md/INDEX.md/ACTIVE_INDEX.md) + codex stay in scope per the sharded-run contract.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, reconciliation, plan-hygiene, findings, scheduled, ao]
related: []
created: "2026-08-09"
parent_epic: plan_hygiene_master
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: review
assigned_vm: planning
execution_scope: orchestrator-agent
locked_by: plan_reconciler
locked_since: "2026-08-09"
supersedes:
superseded_by:
resolved_by:
source: "slot 21, plan_reconciler agt-fe4564, 2026-08-09"
context_scope:
  [
    unified-trading-pm/scripts/plan-hygiene/run_hygiene_sweep.sh,
    unified-trading-pm/agents/plan_reconciler.md,
    unified-trading-pm/cursor-configs/skills/plan-reconcile/SKILL.md,
  ]
drift_direction: advance-code
depends_on: []
---

# plan_reconciler run — 2026-08-09 (agt-fe4564, TRANCHE=ao)

## Scope + method

- `TRANCHE=ao` supplied → sharded topic-scoped run per `cursor-configs/skills/plan-reconcile/SKILL.md` § "Topic-scoped
  (sharded) runs". Population = every doc under `plans/active/` (incl. `issues/`) with `asset_group:` containing `ao`
  (87 docs) — `ao` is a real dedicated `asset_group` enum value since 2026-07-27, so no `parent_epic` fallback needed
  (the prior epic hub `ao_consolidated_closeout_2026_07_25.md` is itself archived — the tag is authoritative).
- Grace set (newest commit <12h old at run start, 2026-08-09T02:58Z): 54 of 87 docs (62%) — unusually high; concurrent
  sibling slots are actively working this exact tranche right now (satellite dispatch batch 8-11 authoring, false-done
  audits, operator ruling records). Read-only context this run.
- Non-grace actionable set: 33 docs (~796KB / ~8776 lines).
- All repos FF-pulled clean at run start (PM was 85 commits behind — the previously-reported FF-PULL-STARVATION dirty
  file had already been resolved by the time this run started; siblings were already current).

## Todos

- [ ] [DOCS] P3. **Repoint `ao_satellite_ao_dispatch_batch5_2026_08_03.md`'s reference to
      `ao_satellite_ao_dispatch_batch4_finalize_2026_08_01.md`** from the old active path to
      `/plans/archive/2026_08/ao_satellite_ao_dispatch_batch4_finalize_2026_08_01.md` (now archived, this run). Blocked
      this run by the 12h grace window (`batch5` was 5h old at report time) — pick up once it ages out, or whenever a
      future `ao`-tranche pass touches it anyway. Single-line fix, closes the `Reference path convention` ratchet
      regression noted below (86→87). **Done when**: the reference resolves + the existence-check count returns to ≤86.

## Flips verified

1. **`ao_satellite_ao_dispatch_batch4_finalize_2026_08_01.md`** sole open todo (archive the batch4 plan) — already done.
   Filesystem-verified: batch4 plan is archived at
   `/plans/archive/2026_08/ao_satellite_ao_dispatch_batch4_2026_08_01.md` with a banner naming this doc as owing the
   flip; both stated done-when conditions independently re-verified (`check_finalize_plan_coverage.py` 0 violations; no
   orphan-inventory regression). unified-trading-pm@d8fe8072a.

## Archived (verified-done, unlocked, non-grace)

1. **`ao_satellite_ao_dispatch_batch4_finalize_2026_08_01.md`** — all 5 todos `[x]` after the flip above, `locked_by:`
   blank. Ran the 6-step ritual: banner added, `status: active`→`complete`, `git mv` to `plans/archive/2026_08/`, fixed
   2 non-grace corpus referrers (`ao_satellite_ao_dispatch_batch5_finalize_2026_08_03.md`'s `related:`,
   `plans/epics/orchestrator_master.md`'s `related_plans:`). A 3rd referrer
   (`ao_satellite_ao_dispatch_batch5_2026_08_03.md`, the non-finalize batch5 plan) is in the 12h grace window this run —
   left dangling for a future pass to fix. unified-trading-pm@d8fe8072a.

## Hygiene fixes

1. **3 dangling `related:` refs repointed to their actual archive paths** (mechanical-adjudicator-confirmed, each target
   path verified to exist before repointing): `killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21.md`
   (→ `/plans/archive/2026_07/ao_uniform_agent_liveness_contract_2026_07_20.md`, + added leading-slash convention to a
   2nd already-correct entry), `long_lived_vm_logs_not_backed_up_2026_07_02.md` (bare-slug → full path for
   `/plans/archive/vm_launcher_durable_log_observability_2026_06_19.md`), `orchestrator_vm_e2e_hardening_2026_07_24.md`
   (→ `/plans/archive/issues/plan_line_cap_remediation_2026_07_23.md`). unified-trading-pm@845c3a900.
2. **`orchestrator_vm_e2e_hardening_2026_07_24.md`'s `last_updated` frontmatter inversion fixed** — was `2026-06-27`, 4
   weeks BEFORE the doc's own `created: "2026-07-24"` (a copy-paste artifact from the parent plan it was split out of);
   set to `2026-08-07`, the doc's actual latest Progress Log entry date. unified-trading-pm@845c3a900.
3. **2 pre-existing `check_plan_operator_ruling_evidence.py` gate violations fixed** (found only because the precommit
   `--only` mode now scans the WHOLE staged file, not just my diff, when I touched these 2 docs for unrelated reasons):
   `deepseek_flash_ab_routing_test_2026_08_05.md` and `ao_scheduled_job_reserve_and_staggering_2026_08_04.md` each had a
   2nd "operator ruling" claim in the same todo block whose citation was outside the checker's 300-char window. No new
   source was invented — each fix restates the SAME citation the block already gave once, closer to the 2nd mention.
   unified-trading-pm@93952a342.

## Contradictions

1. **`ao_residuals_after_dispatch_hardening_2026_07_17.md`** Deferred-table cell said the escalation epic was
   `status: paused`; live `plans/epics/escalation_and_disaster_recovery_master.md` frontmatter confirms `active` since
   2026-07-28 (the doc's own todo section already said this — only the table cell was stale). Fixed.
   unified-trading-pm@dbdc1b370.
2. **`ao_orphan_audit_followup_triage_2026_07_30.md`** pre-screen table row for the prediction-trades-migration doc
   (below) was a pre-session snapshot ("active, 3 open `[BACKEND] P2`"); actual current state is `assigned_vm: planning`
   (flipped 2026-08-06), 1 open `[OPERATOR] P2` (2 of 3 todos shipped). Fixed. unified-trading-pm@dbdc1b370.
3. **`prediction_trades_migration_concurrent_dispatch_2026_07_28.md`** cited `_NON_DISPATCHABLE_RE` as the mechanism
   excluding `[OPERATOR]`-tagged todos from dispatch — verified live against
   `agent-orchestrator/server/regen_backlog_from_plan.py`: no such named regex excludes on `[OPERATOR]`; the real
   mechanism is `_OPERATOR_TAG_PREFIX_RE`/`operator_gated`. The practical outcome the doc describes (todo 3 stays gated)
   was already correct — only the cited code path was wrong. Added a correction note, left the history intact.
   unified-trading-pm@dbdc1b370.
4. **`ao_scheduled_job_reserve_and_staggering_2026_08_04.md`**'s still-open timer-reinstall todo instructed
   `sudo bash scripts/install-<job>-timer.sh` — verified live against `user-timer-env.sh` (hard-ERRORs under sudo) and
   `codex/04-architecture/agent-orchestrator-scheduled-jobs.md`'s current "NO sudo" section that the very commit 2 lines
   above this todo made that instruction actively wrong: executing it as literally written would fail. Corrected the
   command. unified-trading-pm@93952a342.
5. **`blocked_prerequisites_marker_not_in_non_dispatchable_regex_2026_07_28.md`**'s "15 files" blast-radius claim (a
   manual grep from 2026-07-28) is now superseded by a purpose-built automated gate
   (`ao_dispatch_visibility_gate_accidental_exclusions_2026_08_08.md`'s `max_ineffective_declarations` baseline,
   currently 4) that tracks this precisely — a fresh grep today shows 18 raw hits, i.e. the manual count was already
   stale before this correction. Added a pointer to the automated gate + the 2 newer docs to `related:`.
   unified-trading-pm@dbdc1b370.
6. **`backlog_park_lost_across_sibling_todo_insertion_2026_07_30.md`**'s title and summary assert a root-cause mechanism
   ("a park does not carry forward across a sibling-todo edit") that the SAME doc's own 2026-07-30T14:20Z Progress Log
   entry directly disproves — a regression test reproducing the described shape **passes on current code**, and a
   hand-verified 3rd variant also survives; verdict recorded there is "content-hash-only already, NOT positional." Added
   a correction banner rather than rewriting the title (preserves history, fixes what a skimming reader sees first).
   unified-trading-pm@dbdc1b370.

## Missed-flip found but NOT flipped (evidence gap)

1. **`ao_non_dispatchable_regex_swallows_resolved_retags_2026_07_29.md` todo 1** — the doc's own Progress Log names this
   todo "already-executed" via `unified-trading-pm@6edd4486a`, and todo 4 (done) spot-checked 23 of "the 24 mentions
   rephrased" by that commit. But todo 1's own stated target scope is 27 mentions across 21 files — 3 mentions/6 files
   more than what `6edd4486a` actually touched (24/15), never reconciled anywhere in this doc. Annotated with the exact
   gap and the specific re-check needed (re-run the corpus-wide `_parse_open_todos` replication in the doc's own
   Evidence section) rather than flipping on the smaller, undercounting figure. unified-trading-pm@dbdc1b370.

## Doc-drift (flagged, not auto-fixable — see Filed below)

1. **CLAUDE.md** (both `unified-trading-pm/CLAUDE.md` and the `cursor-configs/CLAUDE.md` it symlinks from) still
   instructs `git pull` does NOT reinstall a timer — re-run `sudo bash scripts/install-<job>-timer.sh` under "AO
   scheduled jobs" — but `ao_scheduled_job_reserve_and_staggering_2026_08_04.md`'s own `[x]` todo (shipped
   agent-orchestrator@c3a85c3b4, 2026-08-08) converted all 8 installers to `systemd --user`, which now hard-ERRORs under
   `sudo`. CLAUDE.md is out of this skill's edit authority (not under `plans/**`) — filed for operator/follow-up.
2. **`codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md`** documents
   `POST /api/slots/{id}/rotate-account` as a live mechanism; `deepseek_claude_blended_provider_routing_2026_07_28.md`
   confirmed live 2026-07-28 (grepped `routes/slots_ops.py`/`server.py`) that no such route exists — the real mechanism
   is `reassign`+`spawn`. Codex edit needs an operator ruling before any agent touches it (HARD GATE, this skill never
   rewrites codex autonomously) — filed.
3. **`codex/05-infrastructure/per-tab-worktrees.md`** doesn't document the `cascade_dep_branch()` TOCTOU race that
   `utl_shared_clone_commits_repeatedly_reset_2026_07_22.md` root-caused (3 recurring incidents, partial fix shipped, 3
   stronger fixes operator-AUTHORIZED 2026-08-08 but not yet implemented) — this doc's own banner cites
   `per-tab-worktrees.md` as governing SSOT for exactly this mechanism, but the codex doc has zero mention of it. Filed.
4. **`codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`** cites
   `plans/active/issues/ao_operator_delete_gating_aws_iam_and_corpus_sweep_2026_07_27.md` as "will archive; this doc is
   the durable SSOT going forward" — that doc IS now archived (at
   `plans/archive/issues/ao_operator_delete_gating_aws_iam_and_corpus_sweep_2026_07_27.md`), so the codex doc's own
   reference is dangling. A path-only fix, but codex is out of `plans/**` — filed.
5. **`nohup_detached_background_process_killed_by_orphan_reap_2026_07_27.md`** cited "the `worker.md` Heartbeat HARD
   RULE's ≤10-min cadence" — `agents/worker.md` was tightened to ~5 min on 2026-08-05 (commit `b8eb68e`), after this doc
   was last touched by 2 audit passes that didn't catch the number drift. Low-severity (historical-incident doc, the
   number was accurate when written) — filed as a minor correction.
6. **`nohup_detached_background_process_killed_by_orphan_reap_2026_07_27.md`** vs
   `codex/12-agent-workflow/async-wait-and-poll-discipline.md` item 6 (a different, now-archived source doc): this doc's
   own measured kill latency is ~305-355s; the codex item 6 states "~1-3 minutes" (60-180s) for what reads as the same
   nohup-detached-process-reaped-by-host phenomenon, with no cross-reference between the two. Could be two genuinely
   distinct mechanisms — ambiguous, filed for someone to adjudicate directly (not resolvable from the documented record
   alone).

## Big findings (notify operator — cross-cutting, outside this shard's fix mandate)

1. **`locked_by: live-defi-rollout` / `locked_since: 2026-05-21` — a bogus-lock pattern, confirmed on 18+ docs
   corpus-wide.** Found on 2 of my own non-grace docs (`deepseek_claude_blended_provider_routing_2026_07_28.md`,
   `long_lived_vm_logs_not_backed_up_2026_07_02.md`) with `locked_since` dates that PREDATE the doc's own `created:`
   date by weeks — impossible for a genuine per-doc lock event. **Two hunter sub-agents estimated the corpus-wide count
   at "97"; I could not reproduce that number and instead directly measured it myself**
   (`grep -rlE '^locked_by:\s*live-defi-rollout\s*$' plans/active/` → 62 total, of which 18 have the exact same
   impossible-predating `locked_since: 2026-05-21`, 19 are blank, 25 have a plausible-but-unconfirmed date) — see the
   filed issue doc for the full breakdown and methodology note on the discrepancy. This is almost certainly a
   tooling/template bug (a branch name stamped as the locker identity, same date on every predating case) rather than
   independent genuine human locks, and since `locked_by:` is a HARD archival blocker no autonomous agent may clear,
   this could be silently blocking archival across a meaningful slice of the corpus. **Not fixed or cleared here** —
   `locked_by:` is an explicit-human-signal field this skill (and every agent) is required to treat as authoritative
   regardless of how confident the evidence looks (SKILL.md § "STILL ASK/PARK"). Routed via `/blocked`
   (`BLK-a30d3bc0`) + filed below for an operator ruling on the correct remediation.
2. **plan_reconciler's own review-PR output is piling up unmerged — 19 open PRs, oldest 7 days.** Independently measured
   twice this session (once directly by me, once by the topic hunter):
   `gh pr list --search "plan_reconciler" --state open --limit 50` returns 19 open PRs as of 2026-08-09, oldest
   (`#1998`) created 2026-08-02T12:53:13Z, none merged. This run's own PR (below) will be #20. A corpus-wide grep of all
   33 non-grace `ao`-tranche docs found zero tracking of this as a known concern, despite the AO scheduled-job doc
   (`ao_scheduled_job_reserve_and_staggering_2026_08_04.md`) extensively tracking plan_reconciler's
   dispatch/sharding/timer reliability in detail. If the "PROVING PHASE" review-gate (`plan_reconciler.md` STEP 7) is
   still the intended steady state, the daily reconciliation work has had ZERO effect on the live corpus for a week —
   findings pile up in unreviewed branches instead of landing. Routed via `/blocked` (`BLK-a8e76fb3`) + filed below.

## Filed

- Big finding 1 (locked_by bogus-lock, 97 docs) — filed as
  `plans/active/issues/ao_locked_by_live_defi_rollout_bogus_lock_corpus_wide_2026_08_09.md` (new doc, this run).
- Big finding 2 (plan_reconciler PR pileup) — filed as
  `plans/active/issues/plan_reconciler_review_pr_pileup_never_merged_2026_08_09.md` (new doc, this run).
- Doc-drift items 1-6 above — filed as `- [ ]` todos inside the 2 new issue docs above (CLAUDE.md/codex items under the
  pileup doc's "what this means for findings quality" section is wrong; corrected: filed under the bogus-lock doc's own
  "Related doc-drift noticed along the way" section) and cross-referenced from this findings doc.
- `ao_non_dispatchable_regex_swallows_resolved_retags_2026_07_29.md` todo 1's 27-vs-24 gap — filed in place (see
  Missed-flip section above), no separate issue doc needed (already has a durable home).
- `killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21.md`'s stale 2-way todo framing (superseded by a
  3rd direction per the doc's own 2026-08-03/04 Progress Log, never rewritten) — noted here, left for a future pass
  since resolving it needs picking the actual implementation direction (a design call, not evidence-resolvable).
- `ao_scheduled_job_reserve_and_staggering_2026_08_04.md` line ~380's 2-way DESIGN decision embedded in an
  `assigned_vm: planning` todo (keep vs. drop the `job_name`-less `ScheduledJobStatus` opt-out) — ao-readiness finding,
  needs an operator decision before dispatch; noted here.
- `reaper_kills_inflight_detached_quickmerge_false_done_2026_07_24.md`'s "very likely MOOT" slot-8/9 recovery claim —
  re-attempted the doc's own recommended "5-minute direct check" this session (grepped the 2 candidate archived plans
  for the task ids/shas) and found no direct match; the claim remains genuinely unverified even after a 2nd attempt.
  Noted here for whoever next touches that doc.
- `data_completion_cefi_2026_07_15.md:332`'s stale referrer to the now-archived
  `ao_done_gate_no_carveout_for_red_gate_evidence_only_closure_2026_07_28.md` (moved-doc-referrer hunter finding) — out
  of the `ao` tranche (that referrer doc is `cefi`-tagged), not fixed here; noted for the `cefi` shard.
- 4 grace-protected docs citing stale paths for docs that moved during this run's window
  (`ao_round5_apply_session_rulings_untraceable_blocks_quickmerge_2026_08_08.md`,
  `operator_ruling_record_ao_round5_apply_session_2026_08_08.md`,
  `operator_ruling_evidence_baseline_raised_58_to_76_2026_08_09.md`,
  `orchestrator_db_pool_exhaustion_state_poll_stall_2026_07_25.md`) each cite the pre-move path of
  `mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30.md` (now archived) or
  `ao_satellite_ao_dispatch_batch1_2026_07_26.md` (also archived) — all 4 referrers are inside the 12h grace window this
  run and unwritable; left for the next `ao`-tranche pass to fix once they age out of grace.

## Archive candidates (operator review — near-complete, not auto-folded)

14 docs in the non-grace set have ≤1 open todo (mechanical-adjudicator-confirmed) — a consolidation-candidate class, not
individually flagged per SKILL.md's fold-by-default carve-out (needs `[REVIEW]`/`[DOC]` tag + exactly 1 obvious active
sibling; none of these 14 were checked against that narrow bar this pass given the volume). Listed as ONE class-level
item per SKILL.md's batching guidance rather than 14 separate asks:

- `ao_satellite_ao_dispatch_batch3_2026_07_31.md`
- `ao_satellite_ao_dispatch_batch4_finalize_2026_08_01.md` (now archived, see above — no longer in this list)
- `context_scout_completion_and_plan_brainstorm_skill_2026_07_30.md`
- `ao_db_lock_storm_and_stuck_shutdown_outage_2026_07_26.md`
- `ao_deepseek_provider_model_telemetry_mislabeled_2026_08_06.md`
- `ao_self_pull_wedged_by_main_inbox_untracked_file_2026_07_30.md`
- `backlog_park_lost_across_sibling_todo_insertion_2026_07_30.md`
- `cicd_escalation_agentrow_archived_prematurely_mid_session_2026_07_29.md`
- `killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21.md`
- `long_lived_vm_logs_not_backed_up_2026_07_02.md` (also carries the bogus `locked_by:` — see Big finding 1)
- `one_shot_worker_completes_but_no_clean_exit_signal_watchdog_rekicks_2026_07_25.md`
- `prediction_trades_migration_concurrent_dispatch_2026_07_28.md`
- `ahead_push_sentinel_stale_after_amend_no_rejected_push_retry_2026_07_24.md` and
  `ao_recovery_audit_layer1_deleted_2026_07_15.md` (both genuinely 1-open-but-unstarted, not "almost done" — flagged by
  the mechanical hunter as a literal-rubric-match nuance, not real near-complete candidates)

Routed via `/blocked` (`BLK-26742a3d`) as a single batched class question rather than 14 individual asks. **ANSWERED
2026-08-09 (operator, final): option A** — leave as-is, resurface naturally on the next `ao`-tranche pass. Matches the
recommendation; no action needed.

## Refuted (dropped by verify)

- None of the 8 hunters' candidates were refuted outright — every candidate either (a) verified true and was fixed, (b)
  verified true but needs an operator/design decision (routed), or (c) turned out to already be resolved by earlier work
  and just needed a closing note (e.g. batch3's Deferred data-correctness note, already fixed upstream).

## Coverage (hunters / batches / docs)

- **8 hunters**: 5 doc-batch hunters (A-E, covering all 33 non-grace docs in full), 1 topic/cross-cutting hunter
  (AO-lifecycle themes + the PR-pileup measurement), 1 mechanical adjudicator (all 33 docs' Phase-0-style flags), 1
  moved-doc-referrer hunter (13 moved docs, ~30 referrer lines found across the whole corpus, not just `ao`).
- **Docs read in full**: 33/33 non-grace `ao`-tranche docs (100% of the actionable set). 54 grace docs read read-only as
  context by hunters where cited.
- **Candidates surfaced**: ~45 across all hunters (contradictions, missed-flips, doc-drift, hedge-pointers,
  prose-integrity, ao-readiness, mechanical flags, moved-doc referrers).
- **Verified + applied**: 1 flip, 1 archival, 3 dangling-ref repoints, 1 frontmatter-date fix, 2 pre-existing-gate
  fixes, 6 contradiction/stale-citation fixes = 14 applied changes across 6 commits.
- **Verified true but NOT auto-fixed** (routed): 1 missed-flip with an unreconciled scope gap, 6 doc-drift items (2
  needing a CLAUDE.md/codex edit outside this skill's authority), 2 big cross-cutting findings, 1 stale 2-way todo
  framing, 1 embedded design-decision-in-a-dispatched-todo, 1 still-unverifiable hedge claim, 1 out-of-tranche referrer,
  4 grace-blocked referrers, 14 near-complete consolidation candidates (batched).
- **Routed = parked check** (Phase 5.9(a)): 3 `/blocked` alerts posted this round (`BLK-a30d3bc0` locked_by bogus-lock,
  `BLK-a8e76fb3` PR pileup, `BLK-26742a3d` near-complete-docs class question); all 3 also filed durably above
  (`routed == parked`, both = 3).

## Exit-gate hygiene sweep (Phase 5 — `run_hygiene_sweep.sh --ci`, run at report time)

3 hard failures corpus-wide. **2 are pre-existing** — confirmed unchanged from this run's own STEP-1 entry sweep
(`Silent-default-effort plans`, `Archive candidates` — both already `❌ FAIL` at 2026-08-09T02:58Z, before any edit this
session; corpus-wide ratchets outside this shard's `ao`-tranche mandate, not investigated further here). **1 is a new,
understood, temporary regression I caused and cannot fix this run**: `Reference path convention (existence)` went from
baseline 86 to **87** dangling refs. Root cause: archiving `ao_satellite_ao_dispatch_batch4_finalize_2026_08_01.md`
(Archived section above) turned `ao_satellite_ao_dispatch_batch5_2026_08_03.md`'s existing reference to it into a
dangling one — but `batch5` itself is a 12h-grace-window doc this run (5h old at report time, still grace-protected), so
I cannot edit it to repoint the reference without violating the grace-window HARD LIMIT. This is the same gap already
noted under "Archived" and "Filed" above. **Self-resolves** the moment `batch5` ages out of grace (≈7h from report time)
and any future `ao`-tranche pass repoints the one reference — a single-line fix, not a design decision. Did not
re-baseline the ratchet to paper over this (the docstring's own guidance is to re-baseline only pre-existing drift, and
this is freshly self-caused) — reporting it honestly instead, per Phase 5.9(e).

## Plans not reached

None — full non-grace `ao`-tranche coverage achieved this run (33/33 docs read in full).
