---
doc_type: issue
title: plan_reconciler findings — prediction tranche — 2026-08-10
summary: >-
  Daily deep plan-reconciliation run-findings doc for the prediction topic tranche, dispatch agt-12ce9c (slot 17).
  Records hunter-detected candidates, adversarial-verification outcomes, applied fixes, routed operator questions, and
  coverage for this run. Also the progress journal for the run itself.
status: open
nature: issue
asset_group: [prediction]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [role, plan_reconciler, reconciliation, plan-hygiene, prediction, sharded-run]
related:
  [
<<<<<<< HEAD
    /plans/archive/2026_08/issues/ag_closeout_audit_prediction_parked_2026_08_10_r2.md,
=======
    /plans/archive/2026_08/issues/ag_closeout_audit_prediction_parked_2026_08_10_run2.md,
>>>>>>> 86f944c931 (docs(plans): reconcile last 3 ALLOWED_DUPLICATE_STEMS pairs — cefi/prediction/tradfi ag_closeout_audit slug collisions)
    /plans/active/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md,
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-08-10"
author: plan_reconciler
source: agt-12ce9c
parent_epic: predictions_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline: 0.1
calibrated_ai_days: 0.1
assigned_role: backend_engineer
drift_direction: fix
resolved_by:
locked_by: plan_reconciler (agt-12ce9c) since 2026-08-10T18:20:00Z
depends_on: []
---

# plan_reconciler findings — prediction tranche — 2026-08-10

Dispatch `agt-12ce9c`, slot 17, tranche `prediction`. PM head at run start: `ec7e68edbda6`.

## Scope

Prediction-primary docs in `plans/active/` (incl. `issues/`): ~31 docs carry `asset_group` containing `prediction`. Per
the Orthogonality HARD CHECK, `[prediction, sports]` dual-tags are the historically-confirmed same-work pairing (not
cross-tranche mistags); multi-AG docs are cross-AG coordination docs (context only). **~21 of 31 are inside the 12-hour
grace window** (heavy concurrent fleet activity — several batch/finalize pairs + same-day issue docs) and are READ-ONLY
context this run. **~10 are writable** (outside grace) — see Coverage. `predictions_master` epic (17h, writable) also
reconciled. No plan was archived this run (the only fully-done candidate, `predictions_other_bucket_and_ui_drilldown`,
is `locked_by:`-blocked and routed; `kalshi_live_capture...` became 0-open mid-run and is deferred-archive via
`archive_exempt` because 5 active referrers are inside grace).

## Flips verified

1. **`kalshi_live_capture_regression_and_drift_2026_07_13.md` sole open todo (:251)** — HARD evidence: the owning
   deliverable (`prediction_satellite_ao_dispatch_batch6_2026_07_29.md` todo 5) shipped 2026-08-09 —
   `execution-service@577b9a884`, verified ANCESTOR of `origin/live-defi-rollout` (non-live mocked verification per the
   operator's 2026-08-06 ruling). The kalshi doc's own 2026-08-09 markers still claimed "genuinely hasn't happened"
   (stale, written before/ignoring the same-day slot-19 execution). **FIXED**: flipped `- [x]` + added reconciler
   Progress Log entry.

**Phase-4 verification note**: hunter 3's phase_ab A1 missed-flip candidate (`prediction_phase_ab_residuals...:121` gate
met — batch10 + finalize both `status: complete`, capture_incident Phase-6 backfill DONE 2026-08-10) is CONFIRMED but
NOT applied — `prediction_phase_ab_residuals_2026_07_24.md` is inside the 12h grace window (4h). Filed for next-run
application (see Filed).

## Contradictions

1. **`prediction_satellite_ao_dispatch_batch4_2026_07_26.md` frontmatter↔body (P1)** — frontmatter `status: active`
   (`:19`) vs body banner "**Status: draft — NOT dispatched.**" (`:77`) vs summary "`status: draft`" (`:16-18`). The doc
   was operator-dispatched (Progress Log tasks `batch4-013/-017/-020/-023/-024`). **FIXED**: banner corrected to
   "Status: active — operator-dispatched (2026-07-28+)".
2. **`prediction_satellite_ao_dispatch_batch6_2026_07_29_finalize.md` self-contradiction (P3)** — summary said
   "`status: draft` until batch6 itself is approved and dispatched" (`:8`) while frontmatter is `status: active` (`:9`).
   Also the header gate-threshold "all 13 of that plan's todos" (`:6`, `:55`) is stale — the parent now has 21 top-level
   todos (19 `[x]` + 2 `[ ]`), and the doc's own Progress Log proves the `gate_on_depends` hold never wired ("ready (no
   blockers)", `:112-115`). **FIXED**: summary aligned to active-per-2026-07-30-ruling + wiring-gap caveat; "13" → "all
   of that plan's todos".
3. **batch4 rollup "4b open" stale marker (P2)** — `:193` said "into 4a DONE + 4b open"; all 4 split children
   (4a/4b-i/4b-ii/4c) are `[x]`. **FIXED**: rollup updated to reflect 4b-i/4b-ii COMPLETE + 4b-iii open.
4. **`prediction_consolidated_closeout_2026_07_18.md` internal inconsistency (P2, GRACE — not fixed)** — `:359-361`
   cites batch6 "todo 6's second leg, BLOCKED-OPERATOR-DECISION" vs `:362-365` "covered by batch6 todo 5
   (`...577b9a884`; shipped)"; also its per-child open-todo snapshot is stale (13/4/6/3 vs actual 7/2/5/3) and its
   ground-truth table claims "Football fixture ↔ Kalshi — NONE" (`:186`) and "Instrument-id 4/8" (`:183`) while the
   phase children are DONE. Routed (grace, 11h).
5. **`data_completion_prediction_2026_07_15.md` within-doc (P1, GRACE — not fixed)** — `:104` "prediction is
   single-venue today" vs `:171/:179-181` live Kalshi captured rows. Routed.
6. **`sports_predictions_live_mode_activation_readiness_2026_07_21.md` (P1, GRACE — not fixed)** — 🟡 banner `:87-103`
   calls the cross-AG bleed a "hard BLOCKER" but the bleed issue is archived `status: resolved` (0 prediction-bleed rows
   re-verified 2026-08-07). Routed.

## Doc-drift

- **batch6 parent SHA evidence chain (P2, GRACE — not fixed)**: `prediction_satellite_ao_dispatch_batch6_2026_07_29.md`
  cites `instruments-service@e0f7aaad`/`@62a8b1d8`/`@8f16345b`/`@81744f8a`, `execution-service@15ed3104`,
  `e2e-testing@8d31206` as "landed on live-defi-rollout" — **none are ancestors** (they live on
  `origin/wip-preserve/slot-5-instruments-service-diverged-...`); the work DID ship under rebased shas (landed
  equivalents `94f3ee11`/`15ed3104`/`76ee728` verified ancestors). Same pattern for pre-rebase citations
  (`e2e-testing@371ac1b`→`92d9a5d`, `is@afdb1ad6`→`fb474360`, `is@1fa9177f`→`511c4f0a`) across grace docs. Routed — the
  batch6_finalize's own reconcile todo 1 is the designated fixer; not false-progress (content IS shipped).
- **`/plans/archive/2026_08/issues/ag_closeout_audit_prediction_parked_2026_08_10_run2.md` (P3, GRACE — not fixed;
  renamed off its original slug-collision path 2026-08-11, line numbers below updated to match)** — `:75` says batch10
  archived complete, `:172` calls batch10 "the live dispatch surface" (stale). Routed.
- **`predictions_ml_walk_forward_and_arb_2026_06_20.md` (P3, GRACE — not fixed)** — `:150` cites
  `/codex/02-data/availability-manifest-and-data-status.md` line 1054 for the coverage formula; it is now at line 1136
  (text byte-identical). P3e line-anchor drift. Routed.
- **`prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md` (P2, GRACE — not fixed)** — P0 formal-green runs still
  `[ ]` but the operator-ruled `--day 2026-08-05` (ruling 2026-08-07) has passed (3 days); doc frames it as settled.
  Routed.

## Codex corrections applied (mechanical, evidence-cited)

All three go through the 2026-08-09 mechanical codex-staleness carve-out (HARD evidence, single unambiguous
substitution, no new measurement, not a HARD-STOP area) and full STEP-4 verify (hunter 4/5 + my own live read of
`batch4:804-816`):

1. **`/codex/02-data/canonical-cutover-register.md` §6e** — shapes #3/#3b migration was recorded as "in
   progress/299/348/NOT migrated"; it is COMPLETE 2026-08-06 (3,574 legacy `prediction_trades` objects enriched +
   deleted across 2025-03-14→2026-04-14, 0 remain — verified by batch4's final verification re-run). Corrected the
   summary line, the §6e bullet, and the historical-backfill table cell. Only shape #4 (4b-iii) remains pending.
2. **`/codex/02-data/non-canonical-path-inventory.md` row 22** — same stale "4b-i enrichment in progress" fact;
   corrected to "4b-i migration COMPLETE 2026-08-06 — 3,574 deleted, 0 remain; 4b-iii for shape #4 now pending".
3. **`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §1(a)** — stated finalize twins ship
   `status: draft` until the source plan's todos are done; the shipped fleet implements the 2026-07-30 no-double-gate
   ruling (`status: active` from the start, `gate_on_depends` machine-holds each task). Corrected the stated convention
   (this also makes the batch6/7/8 finalizes' citations to this doc's no-double-gate finding resolve — the companion
   ruling-text addition is noted as follow-up, see Filed).

## Hygiene fixes

1. `batch4` `related:` — verified the "perks→perps" typo hunter flagged is ALREADY CORRECT in the live file (`:39` reads
   `perps`); **refuted, no edit**.
2. `batch4` prose 4b-iii → **tracked `- [ ] [DATA] P2.` todo** (was a `- **` prose bullet, invisible to
   `regen_backlog_from_plan.py`; HARD RULE follow-up-as-todo violation). Added delete-safety justification mirroring
   4b-i (fresh `gcs_bucket_soft_delete_retention_seconds()` ≥604800s check → reversibility-qualified, no `[OPERATOR]`).
3. `kalshi_live_capture...` `related:` — 3 refs missing the leading-slash convention (`../../epics/...`,
   `../../archive/2026_05/...`, `../../archive/2026_07/...`); converted to `/plans/...` form (targets verified to
   exist).
4. `prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md` — 2 `related:` entries bare `plans/archive/...` (no
   leading slash) → `/plans/archive/...`; stale 2026-08-06 archive-candidate note ("follow-up not turned into its own
   todo") corrected — the follow-up IS tracked as the `- [ ] [DATA] P3` todo at :343.
5. `features_delta_one_dependency_checker_prediction_bucket_token_wrong_2026_07_27.md` — false-checked benchmark `[x]`
   (`:210-214`: "Full benchmark measurement needs a longer-running VM" — the throughput measurement never completed)
   retitled to reflect the completed sub-goal + **DEFERRED** annotation pointing to the already-tracked Follow-up at
   `:272`.
6. `prediction_satellite_ao_dispatch_batch8_2026_08_08.md` + `_finalize.md` — 5 bare
   `issues/prediction_cross_venue_ arb_line_cap_blocks_marker_2026_08_07.md` prose/todo refs re-pointed to
   `/plans/archive/2026_08/issues/...` (the `related:`/`context_scope:` refs were already corrected by the finalize's
   own git mv).
7. `predictions_master` epic — removed archived `batch10`/`batch10_finalize` from related_plans + the "Assigned active
   plans" section; fixed count 19 → 17; `last_updated` 2026-07-12 → 2026-08-10.

Corpus-wide `run_hygiene_sweep.sh --ci` hard failures at run start (2): `check_create_only_archive_commits` (1 pair —
`deployed_versions_retirement_cross_repo_followups`, a concurrent sibling fixed the active twin during this run) and
`check_na_corpus_ratchet` (3 new NA docs — owned by `/na-eligibility-audit`, out of tranche).
`ag_closeout_audit_rollout` at 1003L (over the 1000 hard cap) is in-tranche (contains `prediction`) — routed as a split
finding (operator-gated).

## Filed

Routed to the operator via `POST /api/slots/17/blocked` (options + `[WORKER REC]` marked, `can_continue: true`). Every
item is durably tracked here too (Phase-5.9(a) routed==parked). **routed=3, parked=3**:

- [ ] [DOC] P1. **`ag_closeout_audit_rollout_2026_07_25.md` is 1003L — OVER the 1000L hard cap.** Coordination hub; ~880
      lines are fully-closed dated Progress-Log narrative (Finding-J extractable to a `_history_2026_08.md` record, the
      same remedy batch8 applied to `prediction_cross_venue_arb_and_coverage`, 1013→376L). Splitting a plan is an
      operator-gated decision. [WORKER REC: approve the mechanical Finding-J history extraction]
- [ ] [DOC] P2. **`predictions_other_bucket_and_ui_drilldown_2026_06_20.md` is 0-open (11/11 done), archive-candidate
      ×2, blocked only by `locked_by: live-defi-rollout` (`locked_since: 2026-06-20`)** — the corpus-wide
      placeholder-lock defect (see
      `/plans/active/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md`). Never auto-unlocked per
      HARD LIMITS. [WORKER REC: rule the placeholder lock void → unlock → archive]
- [ ] [DOC] P2. **Grace-window findings to apply on the next post-grace run** (batch6 parent SHA evidence chain;
      closeout internal contradictions; phase_ab A1 missed-flip; data_completion single-venue; sports_predictions stale
      blocker banner; phase_d P0 runs; ml_walk_forward line-anchor; parked-issue batch10 self-contradiction). None were
      writable this run (all <12h old). Tracked here so no finding is lost.

Standing follow-ups (not operator-gated, noted): the batch6/7/8 finalizes cite this codex doc's no-double-gate finding —
the S3 substitution resolves the citation, but a fuller "2026-07-30 no-double-gate ruling" section in
`ao-dispatch-batch-naming-and-conflict-check.md` is still owed (new content, not a substitution — route to a doc-author
or a future run).

## Archive candidates (operator review)

- **`predictions_other_bucket_and_ui_drilldown_2026_06_20.md`** — 11/11 done (verified), flagged ARCHIVE CANDIDATE ×2
  (2026-08-09), blocked by `locked_by: live-defi-rollout`. **Parked, not archived** — per HARD LIMITS `locked_by:` is
  never auto-unlocked regardless of evidence. Corroborates the corpus-wide placeholder-lock issue doc.
- **`kalshi_live_capture_regression_and_drift_2026_07_13.md`** — became 0-open this run (flip above);
  `archive_exempt: true` set with Progress Log justification because 5 active referrers are inside grace and cannot be
  re-pointed to `plans/archive/` yet. Deferred to a future `all` pass.
- No other archival candidates in the writable set (batch8 is done but its archive is in-flight via batch8_finalize todo
  2; batch4 has a new open todo after the 4b-iii conversion).

## Refuted (dropped by verify)

- **batch4 `related:` "perks" typo** (hunter 1 P3d) — live file already reads `prediction_perps_...` (correct); the
  cited typo does not exist.
- **batch8_finalize Done-when "3-in/3-out" vs actual 2-in/2-out** (hunter 1 K5, P3) — real but trivial staleness in a
  `[x]`-done todo's Done-when text; not worth editing a closed-todo's retrospective wording. Noted only.
- **batch4 Deferred items "lost"** (hunter 1 A3) — deferral (b) is promoted in archived-complete batch10, deferral (a)
  is a documented permanent `[OPERATOR]` hard-stop in batch4_finalize; nothing lost, prose-format only.
- **`parent_epic` keyword-heuristic WARNs** for `prediction_phase_c_data_status_ui`,
  `prediction_satellite_ao_dispatch_ batch8`, `predictions_ml_walk_forward_and_arb` (hunter 5) — all three
  correctly-declared (`predictions_master` is justified by explicit dated provenance in each body; heuristic false
  positives).
- **batch4 4b-ii Tier-2-VM-mechanism observation** (hunter 5 P3f) — executed as an in-session read-only GCS listing,
  arguably Tier-1-eligible; not clearly a violation, not actioned.

## Coverage (hunters / batches / docs)

Writable set (prediction-primary, outside 12h grace):

- plans/active/ag_closeout_audit_rollout_2026_07_25.md (multi-AG; line-cap finding)
- plans/active/issues/features_delta_one_dependency_checker_prediction_bucket_token_wrong_2026_07_27.md
- plans/active/issues/kalshi_live_capture_regression_and_drift_2026_07_13.md
- plans/active/issues/prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md
- plans/active/prediction_satellite_ao_dispatch_batch4_2026_07_26.md
- plans/active/prediction_satellite_ao_dispatch_batch6_2026_07_29_finalize.md
- plans/active/prediction_satellite_ao_dispatch_batch7_2026_08_04_finalize.md (read in full; no actionable findings)
- plans/active/prediction_satellite_ao_dispatch_batch8_2026_08_08.md
- plans/active/prediction_satellite_ao_dispatch_batch8_2026_08_08_finalize.md
- plans/active/predictions_other_bucket_and_ui_drilldown_2026_06_20.md
- plans/active/sports_group_c_execution_backtest_harness_2026_07_21_finalize_2026_08_08.md (sports-prediction; read in
  full, findings reported under the sports parent)
- plans/epics/predictions_master.md

**5 parallel read-only hunter sub-agents** (sonnet, `SUB_AGENT_MANDATORY_RULES.md` pasted at each spawn top):

1. Batch-dispatch docs (batch4/batch8/batch8_finalize + predictions_master epic) — status contradiction, prose-only
   4b-iii, epic batch10 dangling refs, batch8 bare-ref hygiene.
2. Finalize docs (batch6/7/sports-group-c finalizes + parents) — gate-threshold staleness, broken batch6 SHA evidence
   chain, unshipped SportsMatchingEngine deletion, no flips.
3. Prediction issue docs (kalshi/phantom/features_delta_one/other_bucket) — kalshi missed-flip (HARD evidence), features
   false-checked benchmark, other_bucket archive-candidate, leading-slash ref violations.
4. Topic hunter (prediction data-completion/adapters/milestones, cross-doc) — confirmed the SHA-cluster + bleed-issue
   resolution, surfaced closeout/data_completion/phase_ab/phase_d/sports_predictions grace findings, confirmed no
   false-GREEN on the honest-coverage chain.
5. Codex-alignment + mechanical (batch4/6/7/8 finalizes' Codex SSOTs sections; ag_closeout_rollout line-cap; parent_epic
   adjudications) — 3 mechanical-eligible codex corrections, ag_closeout_rollout split characterization, all parent_epic
   flags correct-as-declared.

**~12 doc-groups covered; ~700KB hunter tokens; ~46 min total wall-clock** (parallel). Every applied fix was
independently re-verified by me (live file reads, `git merge-base --is-ancestor` on the cited shas, `wc -l` on line
caps, count greps) before landing — none taken on a hunter's word alone. Cross-tranche archival caution applied before
the one deferred-archive decision (kalshi).

## Plans not reached

None among the writable set. ~21 grace-window docs were read only as cross-reference context per the grace-window
contract (never written): batch6, batch7, batch4_finalize, closeout, phase_ab/c/d/e, data_completion, capture_incident,
ml_walk_forward, sports_group_c, sports_odds, sports_predictions, prediction_betfair, mtds_prediction_*,
ag_closeout_audit_prediction_parked, sports_odds_four_way_mismatch.

## Deferred work after 2026-08-10

| Item                                                                                                                                                | State                | Blocked on                                                    |
| --------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------- | ------------------------------------------------------------- |
| `ag_closeout_audit_rollout` line-cap split (1003L)                                                                                                  | **Operator-owned**   | split/extraction ruling (Finding-J history extraction)        |
| `predictions_other_bucket_and_ui_drilldown` archive                                                                                                 | **Operator-owned**   | unlock authority (placeholder `locked_by: live-defi-rollout`) |
| Grace-window reconcile fixes (batch6 SHA chain, closeout, phase_ab A1, data_completion, sports_predictions, phase_d, ml_walk_forward, parked-issue) | **Not done (grace)** | 12h grace expiry — apply on a future run                      |
| kalshi deferred archive                                                                                                                             | **Not done**         | post-grace referrer sweep (a future `all` pass)               |
| Add no-double-gate ruling section to `ao-dispatch-batch-naming-and-conflict-check.md`                                                               | **Not done**         | new-content authoring (doc-owner or future run)               |

**Recommended NEXT item**: the `ag_closeout_audit_rollout` line-cap split (1003L, already breached its cap once) is the
highest-leverage — the Finding-J extraction is mechanical and unblocks a hard-cap breach. The batch6 parent SHA evidence
chain is the most important to apply next run (its finalize's reconcile todo 1 is the designated owner).

## Progress Log

- **2026-08-10 ~18:05 UTC** — Run started. FF'd PM + all 25 sibling repos (clean). `run_hygiene_sweep.sh --ci` (exit 1:
  2 corpus-wide hard failures — create-only-archive pair + NA-ratchet; 1 in-tranche line-cap:
  `ag_closeout_audit_rollout` 1003L). Digest (306 active top-level) + skeleton built. Computed prediction population +
  grace set (~21 grace / ~10 writable).
- **2026-08-10 ~18:20 UTC** — Findings doc created + committed (`8d43f72a07`).
- **2026-08-10 ~18:25-19:15 UTC** — Dispatched 5 parallel read-only hunters. All returned (batches 1-4 in ~5 min, topic
  hunter ~7 min). Independently re-verified the load-bearing claims inline (batch6 SHA chain via
  `merge-base --is-ancestor`, kalshi flip via `577b9a884`, 4b-i completion via batch4:804-816, batch6_finalize status
  contradiction).
- **2026-08-10 ~19:15-20:00 UTC** — Applied + pushed in 5 safe-doc-push checkpoints: codex corrections (`86a6fd6e69`),
  issue docs (`4417a9e1da`), batch docs (`42a39ef94a`), epic (`3115acda96`). Two pushes needed the safe-doc-push
  auto-reconcile path (high branch churn). kalshi flip triggered the archive-candidates gate → resolved with
  `archive_exempt: true` + justification.
- **2026-08-10 ~20:00 UTC** — Filing the 3 operator-gated findings + updating this doc. Then STEP 7 result POST + STEP 8
  `/done`.
