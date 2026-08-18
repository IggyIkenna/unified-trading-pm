---
doc_type: issue
title: plan_reconciler findings — cross-cutting tranche — 2026-08-16
summary: >-
  Daily deep plan-reconciliation run-findings doc for the cross-cutting topic tranche, dispatch agt-3cc834 (slot 11).
  Records hunter-detected candidates, adversarial-verification outcomes, applied fixes, routed operator questions, and
  coverage for this run. Also the progress journal for the run itself.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [role, plan_reconciler, reconciliation, plan-hygiene, cross-cutting, sharded-run]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/archive/issues/plan_reconciler_findings_cross_cutting_2026_08_10.md,
    /plans/active/issues/plan_reconciler_blocked_answer_and_result_post_gaps_2026_08_16.md,
    /plans/active/issues/plan_reconciler_dead_run_no_lock_ttl_2026_08_12.md,
  ]
created: "2026-08-16"
author: plan_reconciler
source: agt-3cc834
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline: 0.1
calibrated_ai_days: 0.1
assigned_role: backend_engineer
drift_direction: fix
resolved_by:
locked_by:
locked_since:
depends_on: []
context_scope:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/issues/plan_reconciler_blocked_answer_and_result_post_gaps_2026_08_16.md,
    /plans/active/issues/plan_reconciler_dead_run_no_lock_ttl_2026_08_12.md,
    /codex/02-data/external-data-always-available-rule.md,
    /plans/archive/issues/plan_reconciler_findings_cross_cutting_2026_08_10.md,
  ]
---

# plan_reconciler findings — cross-cutting tranche — 2026-08-16

Dispatch `agt-3cc834`, slot 11, tranche `cross-cutting`. PM head at run start: `effde0f7d5`.

## Scope

150 docs carry `asset_group: cross-cutting` in `plans/active/` (incl. `issues/`). **36 of 150 are inside the 12-hour
grace window** — read-only context this run, not written. **114 are workable** (~3.39MB), partitioned into 10
size-balanced batches (~285-415KB / 11-12 docs each) for full-coverage hunter reading, 2 waves of ≤5 parallel (see
Phase -1 note on the stale "≤10 parallel" figure below).

## Phase -1 (prior findings reconciliation)

- `plan_reconciler_findings_cross_cutting_2026_08_10.md` — extensively closed out by a 2026-08-15 follow-up session,
  but its own 2026-08-15 Progress Log claim **"Every open todo in this doc is now closed; 0 remaining" is FALSE**:
  `Item C` (`- [ ] [DOC] P2. Item C — rewrite /codex/02-data/external-data-always-available-rule.md`) is still
  visibly unchecked in the doc's own Todos section. A false-closure contradiction — exactly the class this skill
  exists to catch, just aimed at its own prior output. Not archived (still has 1 genuinely open item). Item C itself
  is a codex-SSOT multi-part rewrite (explicitly "not a single substitution" per its own text) — does not qualify for
  the STEP-5.f2 mechanical carve-out, so it stays operator-gated regardless of trust mode. Routing via `/blocked` this
  run with a drafted recommendation (see Filed). **UPDATE 2026-08-16 (separate /plan-reconcile Phase -1 pass)**: Item
  C resolved (`unified-trading-pm@de9fa73ef8`, see Filed #1 below), the doc reached 0 open todos, and has since been
  ARCHIVED to `/plans/archive/issues/plan_reconciler_findings_cross_cutting_2026_08_10.md` — see Archive candidates
  #1 below for the executed ritual.
- `plan_reconciler_blocked_answer_and_result_post_gaps_2026_08_16.md` (same-day, `ao` tranche, agt-3eb42b/slot 28) —
  documents 2 live infra gaps this run must work around: (1) `/api/plan-health/result` may reject an empty/omitted
  `X-Orchestrator-Secret` despite documented loopback-trust; (2) a `/blocked` answer may not reliably surface via
  `GET /api/slots/<N>/messages`. This run will not treat either as blocking — STEP 7's result POST failure (if
  reproduced) will not gate `/done`, and STEP 8 will re-check target docs directly rather than relying solely on
  `/messages` polling.
- `plan_reconciler_dead_run_no_lock_ttl_2026_08_12.md` — dead-lock auto-clear was RULED (Option A, 2026-08-15) but
  the backend wiring is still an open `[BACKEND] P1` todo (not yet implemented). If this run hits a locked doc, will
  verify liveness manually (no live tmux session / no recent commits / AO-confirmed reaped-stale) before treating a
  lock as dead, per the same precedent prior sessions used.
- **Doc-drift noted, not self-fixed**: `agents/plan_reconciler.md` STEP 0/3 and
  `cursor-configs/skills/plan-reconcile/SKILL.md` Phase 1 both still say "≤10 parallel" for hunter/verifier fan-out.
  `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` § "When YOU spawn sub-agents" caps it at **5**, citing an explicit
  2026-08-10 operator ruling on host oversubscription (shared ~10-core box, ~4 concurrent slots). This run follows
  the more recent, more specific, safety-motivated cap (5) and flags the stale "10" in the two former docs as a
  finding rather than self-editing them (outside `plans/**`, barred by this skill's own STEP-0 rule).

## Flips verified

(in progress — see Progress Log)

## Contradictions

1. **P0** `master_data_canonicalisation_migration_catalogue_2026_06_07.md:198` (Gate-State Board, defi row, G4
   column, `🟢 (applied 2026-06-29)`) vs `:291-296` (WAVE checklist, slot-2 DeFi G4 todo, still `- [ ]` open):
   "**CORRECTED 2026-08-12 (/plan-reconcile)**: the 'IS v9 migration done' claim above was WRONG... GATE C... still
   0% v9 on disk... Reopened... NOT ✅ COMPLETE." The board's own header claims "refresh at each gate promotion" but
   was last refreshed 2026-07-12 — a month BEFORE the 2026-08-12 correction, so it never picked it up. Directly
   verified both sides myself (read both cited line ranges in full) — genuine, currently-live contradiction (not
   scope/time-difference: same gate, same AG, the correction explicitly says the earlier claim was wrong). **FIXED**:
   board cell corrected `🟢 (applied 2026-06-29)` → `🟡 (REOPENED 2026-08-12 -- GATE C still 0% v9 on disk, see
   slot-2 WAVE item below)`, matching the doc's own 🟡="gated" vocabulary used elsewhere in the same table.
   `unified-trading-pm@de9fa73ef8`.
2. **P1** `plan_reconciler_findings_all_2026_08_15.md` (whole-corpus prior run, batch 4) — frontmatter summary + a
   closing-section bullet both flatly claimed "None of the above have been applied yet," but the body carries 30+
   dated DONE/APPLIED/RESOLVED entries with real shipped-commit citations from subsequent sessions (grep-measured by
   the batch-4 hunter, spot-confirmed by me). Same false-progress class as item 1 above, in a DIFFERENT prior
   reconciler doc. **FIXED**: both claims corrected to point readers at each item's own body entry instead of
   trusting the stale summary. Also flipped 2 genuinely-resolved-but-unchecked todos inside the same doc (a
   conflict-marker non-issue already resolved in its own text; a 4-doc archive_exempt-BRIDGE item already
   filesystem-confirmed archived). `unified-trading-pm@f2c07765e6`.
3. **P1** `instruments_mtds_consistency_remediation_residuals_2026_07_24.md:9-10` (batch 4) — frontmatter claimed
   "Mostly DONE (29/43 todos); 14 residuals remain open," but a fresh grep (batch-4 hunter, spot-confirmed by me)
   measured 0 open `- [ ]` / 41 closed `- [x]` / 5 no-checkbox EXTRACTED-pointer bullets across the full 1001-line
   doc. `assigned_vm: planning`, unlocked, `status: active` — genuinely 100% done and mis-described. **FIXED**:
   summary corrected to "DONE — 0 open todos," flagged ARCHIVE-READY (see Archive candidates). Did not personally
   re-verify HARD evidence on each of the 41 individual `[x]` items (out of proportion for this pass) — the fix here
   is the mechanically-measured checkbox-count claim, not a re-audit of the doc's substance.
   `unified-trading-pm@f2c07765e6`.

## Doc-drift

(in progress)

## Codex corrections applied (mechanical, evidence-cited)

(none yet)

## Hygiene fixes

(in progress)

## Filed

1. **Item C from `plan_reconciler_findings_cross_cutting_2026_08_10.md`** —
   `/codex/02-data/external-data-always-available-rule.md` step 2 (lines 64-72) still prescribes filing a
   `pings/slot_<N>.md` operator-credential request. **Confirmed stale**: `unified-trading-pm/agents/RULES.md` § 6
   ("Orchestrator HTTP surface — what you do NOT do anymore") explicitly states file-based orchestration
   (`pings/slot_<N>.md`) was REPLACED by the HTTP surface — `POST /api/slots/<N>/blocked` is the current mechanism
   (used live by this very run). **[WORKER REC] concrete replacement for step 2**:

   ```
   2. **File a credential request via `POST /api/slots/<N>/blocked`** (the ping-file mechanism -- `pings/slot_<N>.md`
      -- was RETIRED; file-based orchestration was replaced by the agent-orchestrator HTTP surface, see
      `unified-trading-pm/agents/RULES.md` § 6). Use the standard escalation shape (options + a marked
      recommendation, per `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` § "When escalating a question to the
      operator"):
      ```
      {
        "task_id": "<dispatch_id>",
        "question": "CREDENTIAL APPROVAL REQUEST -- <adapter_name>. Vendor: <name + tier + cost estimate>. What I
          need: <API key | OAuth flow | account email + signup | hardware-2FA setup>. Account to use: <existing
          operator email | new account needed>. Unblocks: <asset_group x archetype combos + which gate>. Without
          it: integration tests skip; unit + scaffold ship + adapter is dormant.",
        "options": ["A: approve -- <shortest safe path> [WORKER REC]", "B: use an alternative vendor: <name>"],
        "recommendation": "A",
        "can_continue": true,
        "continue_on": "<what proceeds while waiting>"
      }
      ```
   ```

   **NOT independently confirmed this run**: Item C's second claim (a "stale cross-link to an archived doc") — the
   only cross-link in the current doc body is `master_to_live_defi_2026_05_23.md` (line 75), which this run's own
   STEP 1 observed as still `plans/active/` (a grace-window plan, not archived). Not proposing a fix for this half
   without independent confirmation — routing as-is via `/blocked` for the operator to confirm/correct.
   Multi-part (mechanism rewrite + an unconfirmed second claim) — does not qualify for the STEP-5.f2 mechanical
   carve-out, routed via `/blocked` per Modes § Calibration ("blast radius" gate on any codex/CLAUDE.md edit, applies
   regardless of trust mode). **RESOLVED 2026-08-16T18:04Z**: operator answered `BLK-a8e6b715` = **A** (via
   `/api/activity`, not `/messages` — reproduces the known Gap 2 retrieval issue live, see Phase -1 note above).
   Applied: rewrote `/codex/02-data/external-data-always-available-rule.md` step 2 per the drafted text above;
   flipped Item C `[x]` in the 2026-08-10 doc with citation. Left the master_to_live_defi cross-link untouched per
   the ruling. Landed `unified-trading-pm@de9fa73ef8` via `safe-doc-push.sh` (host under heavy churn: 24
   autostash/safety-snapshot entries, 17s push-slot queue wait — a systemic condition tracked in
   `multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md` /
   `pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md`, not specific to this run). This run's own
   content verified landed correctly. The foreign-WIP frontmatter edit restored earlier this run (see prior Progress
   Log entry) was re-stashed by this push's own quarantine cycle — script explicitly flagged it as "recoverable, not
   destroyed" but warned a blind re-restore now risks reverting a NEWER concurrent edit to the same 2 files (the
   collision it names). Left stashed rather than risk mis-restoring content outside this run's scope/ownership; not
   this tranche's work to chase further.

## Archive candidates (operator review)

1. `plan_reconciler_findings_cross_cutting_2026_08_10.md` — Item C (its last open todo) flipped this run (see Filed
   #1 / Progress Log below); doc now has 0 open todos, unlocked. **ARCHIVED 2026-08-16** (separate `/plan-reconcile`
   Phase -1 pass): moved to `/plans/archive/issues/plan_reconciler_findings_cross_cutting_2026_08_10.md`
   (`status: resolved`, banner added); the 5 leading-slash-path referrers found (of 10 total mentions — 5 were bare
   filename mentions, out of `check_reference_paths.py`'s scope) repointed:
   `citadel_paper_batch_live_reconciliation_2026_06_19.md`, `manifest_v9_residual_2026_08_15.md` (x2),
   `cross_cutting_satellite_ao_dispatch_batch13b_2026_08_13.md`, `bucket_iam_write_protection_per_tier_2026_06_09.md`,
   and this doc's own `related:` entry (line 18).
2. `plans/active/issues/committed_conflict_marker_plan_doc_2026_08_10.md` — all 3 todos `[x]`, unlocked,
   `archive_exempt: true` but the exemption is explicitly time-boxed ("keep active through the next plan-reconcile
   cycle so the operator can review... before archival", filed 2026-08-10) — 6 days and multiple reconcile cycles
   have since passed (confirmed via Phase -1's own doc listing). **ARCHIVED 2026-08-16** (same pass): moved to
   `/plans/archive/issues/committed_conflict_marker_plan_doc_2026_08_10.md`, `archive_exempt` dropped. Re-measured
   referrer count at archival time: 5 (not the 4 originally estimated), all bare filename mentions inside already-
   archived docs — none needed a leading-slash repoint.
3. `plans/active/instruments_mtds_consistency_remediation_residuals_2026_07_24.md` — 0 open todos (see Contradictions
   #3), unlocked, `status: active`. Still ARCHIVE-READY, NOT executed this pass either — 27 referrers is out of
   proportion for a Phase -1 reconciliation of 3 named findings docs; left for a dedicated `/archive-candidates-audit`
   pass (this doc's own status note is accurate as written, no change needed).
4. `plans/archive/issues/orchestrator_vm_disk_io_contention_runner_burst_2026_07_28.md` — independently confirmed
   (0 open todos, `archive_exempt: true` BRIDGE-marker citing the exact same deferred-follow-on pattern, 4+ days
   overdue). Still ARCHIVE-READY, NOT executed this pass — 16 referrers, same proportionality call as #3.

**DECISION (2026-08-16, original run)**: archival execution deferred for all 4 in the original run, given the
reference-path-convention ratchet was already failing and a rushed 4-doc sweep risked new dangling refs.
**UPDATE (2026-08-16, separate /plan-reconcile Phase -1 pass)**: #1 and #2 executed above — both were directly in
scope (findings-doc self-reconciliation / a small, already-measured 4-5-referrer case) and completed cleanly with no
new dangling refs introduced (verified via fresh `grep` before and after). #3 and #4 remain deferred — their
27-and-16-referrer scope is better suited to a dedicated `/archive-candidates-audit` pass than folded into this
3-doc-scoped session.

## Hygiene fixes

1. `plans/active/issues/ag_closeout_audit_cross_cutting_parked_2026_08_08.md` — "Carried forward" list (11 items):
   refreshed against live corpus state — 5 of 11 have since archived (annotated, no longer need retagging), 6 remain
   active. Also corrected a self-contradiction: the `strategy_config_hot_reload_doc_vs_shipped_2026_07_31.md` bullet
   claimed "operator ruling still outstanding" while this SAME doc's own Todos section already showed it RULED
   2026-08-06 and flipped `[x]` 2026-08-09 — never back-ported to the summary bullet. `unified-trading-pm@ca11808d7e`.
2. `plans/active/bucket_fold_features_2026_07_17.md` — stale "🟡 MIGRATION IN FLIGHT" banner (since 2026-07-17)
   corrected to reflect the doc's own 2026-07-26 Progress Log ("Fold A is now 100% closed except..."); only the P3
   Alias-sunset todo remains open. `related:` frontmatter: fixed 2 non-leading-slash paths + repointed 2 entries that
   had moved to `plans/archive/2026_07/` (dangling refs). `unified-trading-pm@ca11808d7e`.
3. Reference-path-convention fixes (bare slug / `../`-relative / stale-archived-path, batch 3 findings, spot-verified
   by me before fixing): `capability_wizard_analysis_findings_2026_06_11.md` F42 inline status corrected to FIXED
   (matches its own roll-up table + tracked todo, both already showed `unified-api-contracts@f3440731` DONE);
   `mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md` + `cross_venue_funding_reversion_research_2026_07_24.md`
   `related:` lists repointed to leading-slash paths (1 target had itself moved to `plans/archive/2026_08/` since);
   `colocated_feature_pipeline_in_memory_handoff_2026_06_21.md` body citation repointed to the now-archived target.
   `unified-trading-pm@f2c07765e6`.

## Refuted (dropped by verify)

(none yet)

## Coverage (hunters / batches / docs)

10 batches prepared (114 non-grace docs, ~3.39MB), 2 waves of ≤5 parallel hunters planned. Wave status tracked in
Progress Log as it proceeds.

## Plans not reached

**Coverage decision**: hunted 5 of 10 batches this run (batches 0-4, ~57 of 114 non-grace docs, ~57% by doc count)
rather than all 10 — see Progress Log for the rationale (value density from the first 5 batches was very high;
pushing to full coverage in one run risks the same "runs too long, dies mid-flight" failure mode sharding was
introduced to prevent). Batches 5-9 (the remaining ~57 workable docs, file lists preserved in this run's scratchpad
bin-packing output) were NOT hunted this run — genuinely unreached, not refuted or filed as resolved. A future
cross-cutting run should prioritize these.

**Confirmed findings this run did NOT apply** (verified/read but not personally resolved, given time budget):

- Batch 0 — `pipeline_mode_partition_migration_2026_06_01.md` todos (M1: cefi/tradfi/sports/prediction rider may
  already be satisfied per the master doc's C-PATH inventory, unresolved across 3 prior audit passes; M2: the
  "instruments bucket — no canonicalisation plan exists yet" claim may be false, a live plan is registered) — both
  need a live grep-confirm I didn't run this pass.
- Batch 0 — `daily_trading_analyst_llm_job_design_2026_07_29.md` §5: self-identified stale codex citation
  (`agent-orchestrator-single-vm-architecture.md` says "01:00 UTC daily/opus", live reality is hourly/sonnet-forced)
  has its own open follow-up todo, still `[ ]`.
- Batch 1 — `venue_year_coverage_cefi_oom_deployment_api_2026_08_09.md`: P0 priority, `assigned_vm: planning`, 5 days
  stalled with no Progress Log movement despite closely-related sibling work happening nearby in the same window —
  looks like a dispatch-gap, not a genuine blocker. Worth a live AO-backlog check.
- Batch 3 — `deployment_service_basedpyright_ratchet_broken_by_dep_backmerge_2026_08_15.md`: frontmatter states a
  root cause as settled fact; the doc's OWN bisection body falsifies it, and a later cross-slot measurement only
  "partially rehabilitates" it with an explicit caveat ("could not pin the specific commit"). Genuinely nuanced/still
  evolving — did not attempt a fix, needs a closer read than this pass's budget allowed.
- Batch 3 — `strategy_archetype_latency_deployment_profile_execution_2026_08_10.md`: sole open todo already burned 4
  dispatch cycles (2026-08-12→08-14) before a guard fix shipped (`agent-orchestrator@5c3dfb58c8`); no confirmation
  since 08-14 that the guard is actually holding. `assigned_vm: planning` — worth a live AO-backlog check before
  assuming this is settled.
- Batch 3 — `infra_ops_residual_migration_verification_2026_07_24.md`: a P0 "confirm what's actually shipped" item
  open 23+ days, re-classified as "stays NA, judgment work" by 4+ separate na-eligibility-audit passes without the
  actual audit ever being run. Pattern worth surfacing on its own — repeated re-classification isn't the same as
  doing the work.
- Batch 3 — `colocated_feature_pipeline_in_memory_handoff_2026_06_21.md`: Progress Log repeatedly (3 separate audit
  passes) asserts `locked_by: live-defi-rollout` while the actual frontmatter field is blank — a stale-prose
  instance of the corpus-wide branch-name-as-lock pattern already tracked in
  `locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md`. Not independently fixed here (prose-only,
  no functional lock exists) — noted for that doc's own sweep.

## Progress Log

- **2026-08-16T17:36Z (run start)**: dispatch `agt-3cc834`, slot 11. RULES.md + plan_reconciler.md read. STEP 1
  hygiene inputs gathered: corpus-wide hygiene sweep shows 2 hard ratchet failures (reference-path-convention,
  assigned_vm:NA corpus size) + 1 soft warning (delete/VM-launch tagging) — all 3 are standing, previously-tracked
  ratchets/ candidate-signals, not new regressions introduced by this run (confirmed via digest re-run). INDEX.md ↔
  active-plans drift (17 docs) noted from the digest but none of the 17 filenames match this tranche's inventory —
  not chased. Phase -1 prior-findings check complete (see section above): 1 false-closure contradiction found in the
  cross-cutting 2026-08-10 doc, 2 live infra gaps + 1 stale-lock-mechanism note absorbed as run-conduct context, 1
  parallel-cap doc-drift flagged. Tranche inventory: 150 docs, 36 grace, 114 workable. Bin-packed into 10 batches.
  About to launch Wave 1 (5 batch hunters).
- **2026-08-16T17:46Z (lock commit landed + near-miss recovered)**: `unified-trading-pm@08a5cfe934` (this doc) landed
  via `scripts/dev/safe-doc-push.sh` under heavy fleet churn (branch moved twice in ~90s; the script's own
  contention-hardening handled it after 2 plain-git attempts failed on branch-drift). The push run reported exit 9
  (orphaned prek patch, a documented near-miss class per
  `safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md`): a patch containing a DIFFERENT slot's
  small in-progress edit (`drift_direction`/`depends_on` frontmatter additions to
  `plan_reconciler_findings_prediction_2026_08_16.md` and `prosewrap_padding_baseline_climbing_recheck_2026_08_16.md`
  — neither owned by this run) had not been restored to the working tree after this run's own prek hook cycle.
  Verified `git status --porcelain` was otherwise clean (this run's own content intact), then `git apply --check` +
  `git apply` restored the foreign patch to the working tree only (left uncommitted, unstaged — not this run's work
  to commit), then removed the now-applied patch file. No content lost; flagging as a live recurrence of the known
  class for whoever next reads that tracked issue doc.
- **2026-08-16T21:42Z (separate /plan-reconcile Phase -1 reconciliation pass, this doc's own dead lock cleared)**:
  this doc's `locked_by: plan_reconciler (agt-3cc834) since 2026-08-16T17:36:33Z` was confirmed DEAD before touching
  it: `check-ao-backlog-status.sh` filtered on `agt-3cc834` against the live AO backlog returned 0 matching tasks
  (queued/dispatched/blocked), and no commit landed against this doc for ~3h05m before this pass started (last
  activity `dc95c63538` at 18:27:12Z, itself already framed as a deliberate stopping point — "batch 5-9 not hunted...
  a future cross-cutting run should prioritize these" — not a mid-sentence crash). Same 3-part liveness bar the
  2026-08-15 precedent used for the sibling 08-10 doc's lock (no live tmux session / no recent commits /
  AO-confirmed not-in-backlog). Lock cleared. **Backfilled 5 `<pending>` sha placeholders** with their real,
  HEAD-reachable commits (`git log --stat` per candidate commit, matched by touched-file set, not guessed):
  Contradictions #2/#3 and Hygiene #3 → `f2c07765e6`; Hygiene #1/#2 → `ca11808d7e`. **Executed 2 of the 4 deferred
  archivals** (see Archive candidates, updated above) — `plan_reconciler_findings_cross_cutting_2026_08_10.md` (my
  direct Phase -1 scope) and `committed_conflict_marker_plan_doc_2026_08_10.md` (small, already-measured referrer
  count) — both via the standard 6-step ritual, flat `plans/archive/issues/` destination per
  `archive_path_convention_dated_subfolder_vs_flat_issues_contradiction_2026_08_16.md`'s same-day ruling. Left
  batches 5-9 and the "confirmed findings not applied" list untouched — genuine remaining ordinary work, not a
  doc-hygiene gap this Phase -1 pass exists to close.
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries)
- **na-eligibility-audit 2026-08-17** [body-hash:2cdf81414edf3464]: KEEP-NA, valid -- Prose-only remaining work (the exact trap this rubric warns about): 0 checkboxes, but the doc's own "Plans not reached" section states batches 5-9/10 of the sibling plan-reconcile sweep (~43% of docs by count) were never hunted this run, plus 6 named unapplied findings. Genuinely mid-flight plan_reconciler output, not done. Cross-cutting tranche audit.
