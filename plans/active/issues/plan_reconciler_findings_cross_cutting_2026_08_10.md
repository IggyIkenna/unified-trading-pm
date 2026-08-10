---
doc_type: issue
title: plan_reconciler findings — cross-cutting tranche — 2026-08-10
summary: >-
  Daily deep plan-reconciliation run-findings doc for the cross-cutting topic tranche, dispatch agt-33a6ec (slot 28).
  Records hunter-detected candidates, adversarial-verification outcomes, applied fixes, routed operator questions, and
  coverage for this run. Also the progress journal for the run itself.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [role, plan_reconciler, reconciliation, plan-hygiene, cross-cutting, sharded-run]
related: [/plans/active/cross_cutting_consolidated_closeout_2026_07_25.md]
created: "2026-08-10"
author: plan_reconciler
source: agt-33a6ec
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline: 0.1
calibrated_ai_days: 0.1
assigned_role: backend_engineer
drift_direction: fix
resolved_by:
locked_by: plan_reconciler (agt-33a6ec) since 2026-08-10T00:20:00Z
depends_on: []
---

# plan_reconciler findings — cross-cutting tranche — 2026-08-10

Dispatch `agt-33a6ec`, slot 28, tranche `cross-cutting`. PM head at run start: `f8f07e7459`.

## Scope

147 docs carry `asset_group: cross-cutting` in `plans/active/` (incl. `issues/`). **58 of 147 are inside the 12-hour
grace window** (heavy concurrent fleet activity on this tranche — several sibling batch/finalize plan pairs and issue
docs created within the last few hours) — read-only context this run, not written. **89 are workable.**

Note: yesterday's cross-cutting run (`plans/active/issues/plan_reconciler_findings_cross_cutting_2026_08_09.md`,
`agt-627fc7`) shows all sections still `(none yet)`/`(in progress)` — it appears to have died mid-flight before its
first STEP-5 checkpoint. That doc is itself inside today's grace window (locked since 2026-08-09T16:00:00Z, <12h old at
this run's start) so it is read-only context only; not touched, not diagnosed further here (a dead one-shot dispatch
with zero committed content is not, by itself, an actionable finding for this run).

## Flips verified

1. `bucket_iam_write_protection_per_tier_2026_06_09.md` P1.3 — closed MOOT (superseded by P2.3's already-passing
   real-tier-pair test; P1.3 as worded tests the permanently-retired dev/stg pair). Doc now 100% done, locked
   (`live-defi-rollout`) — archive-ready-once-unlocked, see Archive candidates below. `unified-trading-pm@388f07d0d0`.
2. `data_completion_to_100_all_ag_2026_06_21.md` — 2 todos flipped: (a) VM-launch canonicalisation-gate check, verified
   via the archived `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`'s cited `deployment-service@c97fefc9`;
   (b) Step-4 credential-gated venues, verified via the same archive's re-verification (Tardis/Helius/Databento-core/
   Odds-API already live, Glassnode+Kaiko/Sportradar/Databento-ICE-OPRA correctly filed as their own issue docs).
   `unified-trading-pm@29d8e89f42`.
3. `manifest_v6_batch3_residual_orphaned_work_2026_07_21.md` — both main checkboxes (deployment-api quote_asset/
   margin_type API, deployment-ui heatmap filter) confirmed genuinely shipped (`deployment-api@c250348`,
   `deployment-ui@e2d109a`, both verified live-on-origin 2026-08-05) despite the doc's own pre-existing stale prose
   saying otherwise. Doc reached 0 open todos — archived, see Archive candidates. `unified-trading-pm@83a81279dc`.
4. `carry_staked_basis_funding_scan_experiment_2026_06_16.md` — 2 todos flipped (`--live` 11-venue snapshot mode; dYdX
   v4 + Vertex wiring), both verified shipped via `e2e-testing@6e2ffb8` (live-code-grepped in the current file, not
   sha-ancestry — this repo's history predates a documented 2026-08-05 rewrite that broke ancestor-checking for older
   commits). A 3rd (Drift creds/RPC) NOT flipped — genuinely ambiguous whether it duplicates a sibling MTDS todo, routed
   instead of guessed. `unified-trading-pm@<pending final push>`.

## Contradictions

1. `manifest_v6_batch3_residual_orphaned_work_2026_07_21.md` — checkbox-vs-prose contradiction (both checkboxes
   correctly `[x]`, the doc's OWN 08-03 prose was stale by the time a later 08-06 audit read it) — bridging notes added,
   2 malformed/duplicate Follow-up todos closed as moot rather than deleted. Resolved + archived (see Flips).
2. 3 docs citing `cross_cutting_consolidated_closeout_2026_07_25.md` as "over the 1000-line hard cap" — live-verified
   720 lines (already split via a prior commit). **Not yet fixed in the 3 citing docs** — routed, see Plans not reached,
   Item N (low priority, individually stale but harmless; a future pass can batch-fix).
3. `is_catalogue_g1_root_audit_log_2026_07_24.md` self-contradicts on G1.run-full-history ownership (one line says
   EXTRACTED elsewhere, another says still-owned-here) — **not yet resolved**, see Plans not reached.
4. `master_data_canonicalisation_migration_catalogue_2026_06_07.md`'s "Deferred work — migrated to:" section is
   orphaned/stale (dead line-number refs, one successor citation points at an archived doc) — **not yet resolved**, see
   Plans not reached.
5. `live_pipeline_persistence_hot_path_decoupling_2026_06_24.md` (`status: blocked`) — the blocking condition (a dead
   compactor job) is very likely resolved per a cross-repo grep, but needs a live `gcloud run jobs executions list`
   re-verify before flipping — **not yet resolved**, see Plans not reached.

## Codex corrections applied (mechanical, evidence-cited — STEP 5.f2 carve-out)

1. `/codex/05-infrastructure/manifest-consolidator-ssot.md` — ml-store consolidator fold ratio corrected "5 → 1" to "2 →
   1", matching `bucket_fold_ml_2026_07_17.md`'s own twice-stated ground truth (only 1 of 5 ml kinds ever had a
   consolidator). Single-row substitution, no governance area touched, no new measurement.
   `unified-trading-pm@<pending>`.
2. `/codex/02-data/carry-venue-live-integration-reference.md` §8 items 1 and 6 — added a "DONE for the e2e read" marker
   matching item 7's existing pattern, both verified shipped in the same `e2e-testing@6e2ffb8` change (live-code
   confirmed, see Flips #4). `unified-trading-pm@<pending>`.

**Self-correction (important — logged for the record):** an EARLIER fix this run (part of `29d8e89f42`) corrected 3
epics' stale-looking `assigned_vm: vm-cross-cutting`/`vm-operator-ops`/`vm-ml` to `NA`, reasoning from the precedent of
3 sibling epics already fixed from `assigned_vm: planning`. That precedent does NOT actually apply — `planning` on an
epic is a live, misleading claim (D2 explicitly dropped epic-level dispatch); a legacy `vm-<id>` is EXPLICITLY
sanctioned as historical archaeology per an on-the-record 2026-07-12 ruling (finding 123/262, §A2 B-queue, cited
verbatim in `instruments_master.md`/`sports_master.md`: "RETAINED WORKSPACE-WIDE... migration OUT OF SCOPE"). Self-
caught while reviewing my own diff; reverted in `unified-trading-pm@27781e212d` before it could compound into a fresh
contradiction for a future audit to untangle. Logged here per the "report what did NOT land cleanly" honesty rule — this
was a genuine near-miss, not something to bury.

## Hygiene fixes

1. `instruments_mtds_consistency_remediation_residuals_2026_07_24.md` — repaired 9 instances of mojibake corruption
   (double-encoded 🔴/🟢 emoji + `×` multiplication sign, likely from the 2026-07-24 verbatim split from an archived
   parent). Content-only, isolated to this file (corpus-checked). `unified-trading-pm@42b68c8ba8`.
2. **Epic-roster regeneration** (`scripts/plans/populate_epic_bodies_2026_05_21.py --apply`) — ALL 22 epics were stale
   (derived "Assigned active plans" roster + `related_plans:` frontmatter drifted from live corpus state); ran
   corpus-wide since the tool is a pure DERIVED-projection regenerator (Phase-4's "regenerate via tooling, never
   hand-sync" pattern) with no narrative-content risk (spot-checked diffs on `mtds_mdps_master`/`defi_master`/
   `infrastructure_master` — only the roster section + `related_plans:` changed). `mtds_mdps_master` alone was 4 real
   docs behind (4→8); `instruments_master` undercounted 16→23. `unified-trading-pm@29d8e89f42`.
3. `strategy_master.md` epic hub — dropped a hardcoded "53 archetypes" from its own Codex-SSOTs pointer line, which
   contradicted the SAME doc's body 2 paragraphs above (which already explains the count is a live code figure, not a
   constant, and specifically warns against this exact restatement pattern).
4. `capability_wizard_analysis_findings_2026_06_11.md` — F5's "Status: OPEN" corrected to RESOLVED (verified fixed
   2026-07-27 via `unified-trading-pm@ce6eb1775` in the sibling gap-discovery doc, never reflected back); F12/F14's
   hedge-pointer ("decision deferred to the UI-phase owner") resolved to a confirmed real successor doc.
5. `carry_staked_basis_funding_scan_experiment_2026_06_16.md` — annotated a duplicate Aave-Ethereum backfill todo as
   superseded-in-place by its own doc's more refined follow-up todo (same gap, tracked twice).

## Filed

1. **`plans/active/issues/deployment_api_prod_disable_auth_true_2026_08_06.md`** — live unauthenticated prod Cloud Run
   endpoint (`uts-shared-deployment-api`), open 4+ days with 2 prior re-flags (na-eligibility-audit 2026-08-07,
   ag-closeout-audit 2026-08-08 ×2), still unresolved. Escalated immediately rather than batching at end-of-pass given
   severity: `BLK-46b42d75` (options A/B/C, recommendation A, evidence-backed via a fresh consumer-count grep). Progress
   Log entry appended to the target doc itself (already carries the tracked `- [ ]` todos — no new todo needed, this is
   a re-verify + escalate, not a new finding). Not counted as a hunter candidate (found via direct read while
   cross-referencing grace-window `ag_closeout_audit_cross_cutting_parked_*` docs for the Phase-0 pileup check).
2. **`plans/active/issues/recon_bucket_missing_nightly_recon_failing_2026_07_13.md`** — P0, data-pipeline-correctness-
   tagged; 3 separate na-eligibility-audit passes (07-30/08-03/08-06) all independently recommended promoting the
   bundled ~5-deliverable todo into its own wrapper plan/epic, unactioned for 3+ weeks. Escalated: `BLK-8bb28da4`
   (options A-D, recommendation A — promote now, `assigned_vm: planning`). Progress Log entry appended to the target
   doc; did not author the wrapper plan myself (that is exactly the ask-before-creating call the prior audits already
   deferred to the operator).
3. **`plans/active/issues/features_service_clean_check_dangling_fleet_ci_dedup_revert_2026_08_07.md`** — zero-checkbox
   HARD RULE violation (`assigned_vm: planning` but structurally undispatchable). Converted the prose "Resolution path"
   into a real `- [ ]` [INFRA] P2 todo directly (mechanical fix, applied — see Hygiene fixes).

## Archive candidates (operator review)

1. `bucket_iam_write_protection_per_tier_2026_06_09.md` — 100% done (last todo closed this run),
   `locked_by: live-defi-rollout` — needs `[unlock-plan]` before the standard archival ritual can run. Its gated
   finalize plan (`bucket_iam_write_protection_per_tier_2026_06_09_finalize_2026_07_27.md`) can dispatch once the parent
   flips `active`.

## Refuted (dropped by verify)

1. INFRA_A's C4 (`bucket_iam_write_protection_per_tier_2026_06_09.md`'s "no remaining project-wide objectAdmin"
   success-criteria bullet vs. the doc's own later note that broader `roles/storage.admin` is still present) — verified
   this is NOT a hidden gap: the residual drift is already tracked in its own dedicated issue doc
   (`unified_trading_sa_live_iam_drift_vs_terraform_2026_07_31.md`), cited by name in the same paragraph the hunter
   flagged. No action needed.
2. INFRA_A's C5 (the 3 non-grace `ag_closeout_audit_cross_cutting_parked_2026_08_02/06/07.md` docs, suspected possible
   duplicates per a prior session's flagged concern) — read all 3 in full (plus the 2 grace-window siblings,
   08-01/08-08, as context): genuinely distinct content per run, each explicitly avoiding re-duplicating prior runs'
   still-open findings. Confirms a real corpus-growth pattern (new dated doc per run vs. one rolling register) but NOT a
   contradiction or duplication bug — refuted as a finding requiring a fix.
3. INSTRUMENTS' hedge-pointer check (3 "uncaptured, flagged for follow-up" fragments in
   `instruments_remaining_work_audit_2026_07_10.md`) — fresh-grepped by the hunter; all 3 already resolve to a real,
   correctly-tracking owner doc. No rewrite needed (the hedge language is arguably now stale-but-harmless, since the
   owners are confirmed correct — below the bar for a dedicated fix at P3).

## Coverage (hunters / batches / docs)

**9 hunters** (7 epic-cluster + 2 topic), all completed, all reports processed: INFRA_A (18 docs), INFRA_B (18 docs),
MTDS_MDPS (6 docs), INSTRUMENTS (11 docs), STRATEGY (6 docs), MANIFEST_BLS (12 docs), AOF_HYGIENE_SMALL (18 docs),
topic-CI/CD (grep sweep across 89-doc working set + `issues/`), topic-AO-lifecycle (grep sweep, same scope). **89 of 89
non-grace docs read in full by exactly one epic-cluster hunter** (7 batches partition the full 89-doc workable set with
no gaps or overlaps — verified against the Phase-0 inventory at dispatch time). 58 grace-window docs read as context
only where a hunter's batch or a topic hunter's cross-reference touched them.

**Candidates generated**: ~50 distinct findings across all 9 reports (contradictions, missed-flips, codex-drift,
AO-readiness, hedge-pointers, structural/prose, zero-checkbox). **Verified + applied this run**: 19 (see Flips verified
/ Codex corrections / Hygiene fixes above, plus the epic-roster regeneration touching 22 files and a
self-caught-and-reverted mistake). **Escalated**: 2 (`BLK-46b42d75`, `BLK-8bb28da4`). **Routed below (confirmed
findings, not auto-fixable this run)**: 14, enumerated in Plans not reached. **Refuted / no-action-needed**: 3
(INFRA_A's C4 already tracked in a separate known issue doc; C5's 3 `ag_closeout_audit_cross_cutting_parked_*` docs
confirmed genuinely distinct, not duplicates; INSTRUMENTS' hedge-pointer fragments confirmed already correctly owned).
**Ledger check**: 19 applied + 2 escalated + 14 routed + 3 refuted = 38 dispositioned findings out of ~50 generated; the
remaining ~12 were P3-cosmetic (whitespace/backtick-parity nits) explicitly not worth individual fixes at corpus scale —
noted by the hunters, not silently dropped, but not itemized below either (see note at end of Plans not reached).

## Plans not reached

Confirmed findings this run did NOT apply, with reasons — each is either genuinely operator/judgment-gated, needs a live
re-verify I didn't have time for, or is a script/codex-level fix outside a single reconciliation pass's mandate. None of
these are silently dropped; each names its target doc so a future pass (or the operator) can pick it up directly instead
of re-discovering it.

Grace-window, could not touch (<12h old at check time):

- Item A. `ag_closeout_audit_cross_cutting_parked_2026_08_06.md` todo #1 (retag the now-archived+resolved
  `deployment_api_quickmerge_blocked_pre_existing_test_failures_2026_08_04.md` — should get the same MOOT treatment its
  own sibling doc's precedent already established). Touched by another agent 38 min before I checked; deferred.

Operator/judgment-gated, not mine to decide:

- Item B. `/codex/05-infrastructure/bucket-isolation-model.md` §8/§8.5 — god-SA-removal status still says "Pending"
  though P2.1b shipped 2026-08-08. Not a single substitution (needs the whole §8 framing reworded plus the residual
  `storage.admin` drift reflected) — doesn't qualify for the f2 mechanical carve-out.
- Item C. `/codex/02-data/external-data-always-available-rule.md` — prescribes a RETIRED ping-file mechanism plus a
  stale cross-link to an archived doc. Multi-part rewrite, not a single substitution.
- Item D. `plans/active/issues/ao_scheduled_job_reserve_and_staggering_2026_08_04.md` — open `[OPERATOR]` re-install
  todo whose literal instructions now hard-fail (the script it names moved to `systemd --user`, refuses `sudo`), and
  whose "not-live" premises are contradicted by dated evidence elsewhere in the corpus, including this run. Needs a
  careful rewrite, not a quick substitution.
- Item E. `plans/active/carry_staked_basis_funding_scan_experiment_2026_06_16.md` — the Drift creds/RPC todo (annotated,
  not flipped, this run). Genuinely unclear whether it duplicates the sibling MTDS-production todo.
- Item F. `plans/epics/manifest_master.md` — carries live `[AGENT]`/`[OPERATOR]` open checkboxes directly in the epic
  body, invisible to every plan-corpus tool (all scan `plans/active/*.md`, never `plans/epics/*.md`). A distinct orphan
  class. Moving them to a real plan is a structural decision outside this run's mandate.

Needs a live re-verify I didn't run, time-bounded this session:

- Item G. `plans/active/issues/batch_live_reconciliation_service_audit_2026_05_27.md` — G3/G10 marked "still genuinely
  open as of 2026-07-27" but the successor plan shows both DONE. `status: open` never revisited.
- Item H. `plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md` P9.2 — cites UAC version drift dated
  2026-06-20; the same doc's own later entries show UAC had already moved far past those versions two days later. High
  likelihood self-resolved, not independently re-checked against current UAC.
- Item I. `plans/active/issues/perp_funding_data_semantics_and_cadence_2026_06_16.md` — frontmatter `status: open`,
  `locked_by: live-defi-rollout`, but body is 100% done (20/20 checkboxes). Strong archive candidate once unlocked. Not
  actioned this run (locked; prioritized the already-verified `bucket_iam` case instead).

Script/tooling-level, backend_engineer scope, not a plan-doc fix:

- Item J. `check_na_corpus_ratchet.py`'s new `--diff-base` mode inherits an already-documented fenced-code-block
  checkbox-overcounting bug (open, unfixed since 2026-08-02). Code-verified live today: `_CHECKBOX_RE` has no
  fence-awareness.
- Item K. `plans/active/issues/plan_hygiene_ratchet_regressions_outpace_serial_ci_fix_velocity_2026_08_09.md` — 4
  Progress Log entries claim a "P3 backlog todo" exists for prosewrap `--diff-base` conversion; no such checkbox exists
  anywhere in the doc. Real still-needed work has no tracked home. This doc was grace-protected when checked (touched by
  a same-tranche dispatch <12h earlier), so I could not add the missing todo myself.
- Item L. `plans/active/issues/over_cap_live_plan_is_permanently_unverdictable_2026_08_02.md` line 138 — a checked `[x]`
  todo cites a literal unfilled template placeholder as its evidence sha. Underlying work is genuinely done
  (independently verified against a different doc); just needs the real sha backfilled.

Duplicate open-todo pair, both stale identically, routed as one item:

- Item M. `context_scope_marker_claims_exceed_frontmatter_count_2026_08_06.md` and
  `governance_sweep_deferred_followups_2026_08_06.md` both independently track the same "restore 2 dropped context_scope
  entries" action on the same target doc, created the same day. Neither reflects that 1 of the 2 entries was already
  restored by an unrelated edit — both still say 2.

Low-priority stale citations, harmless, batchable later:

- Item N. 3 docs (`promote_ref_orphaned_on_manual_pr_close_2026_08_06.md`,
  `provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md`,
  `unified_trading_system_ui_block_list_parity_test_failing_2026_08_04.md`) cite the cross-cutting closeout hub doc as
  "already over the 1000-line hard cap" — live-verified 720 lines (split via an earlier, untraced commit). Confirmed 2
  of the 3 exact citations by direct grep; the 3rd references the same underlying line-cap-deadlock chain indirectly and
  wasn't fully traced to a single fixable line this run. All 3 claims are stale but harmless.

**~12 P3-cosmetic findings not itemized** (whitespace/backtick-parity artifacts, minor verb-tense nits, off-by-one
counts in Progress Log prose) across INFRA_A (S2-S5), MTDS_MDPS (#7-#8), AOF_HYGIENE (S1-S2, minor AO-readiness verb
nits), topic-AO (#2/HEDGE-1) — each individually named in the hunter scratch reports this run's coverage section
references; not worth a dedicated fix pass at corpus scale, flagged here so the count is honest rather than silently
absorbed.
