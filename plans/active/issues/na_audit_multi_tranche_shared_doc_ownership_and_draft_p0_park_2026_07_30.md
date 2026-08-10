---
doc_type: issue
title: >-
  Concurrent per-tranche NA/closeout audits have no primary-owner rule for legitimately multi-tranche docs (47% of the
  prediction population), a P0 live data-correctness fix is parked behind an un-flipped `status: draft` AO batch, and
  the incremental-skip verdict marker has two incompatible date formats in the live corpus
summary: >-
  Filed by the scheduled `/na-eligibility-audit prediction` run 2026-07-30 (autonomous, no operator reachable). Three
  process findings, none covered by an existing doc. (1) OPERATOR-DECISION — `generate_na_doc_tranche_inventory.py`
  assigns tranche membership by pure `asset_group` set-intersection with no notion of a PRIMARY owner, so a doc tagged
  `[cefi, defi, tradfi, sports, prediction]` is legitimately a member of 5 tranches and is read, verdicted and edited by
  5 of the 9 concurrent workers the timer fires. 16 of this run's 34 in-scope docs (47%) are in this class. This is
  distinct from the already-fixed citation cross-contamination bug
  (`na_doc_tranche_inventory_stale_citation_membership_cross_contamination_2026_07_29.md`) — that was wrong membership;
  this is CORRECT membership with no ownership arbitration. (2) BLOCKED-OPERATOR-DECISION —
  `prediction_satellite_ao_dispatch_batch6_2026_07_29.md` is still `status: draft` (so not ingested, not dispatched) and
  its headline todo 1 is a live P0 data-correctness fix: 79% of daily Kalshi volume has silently mis-bucketed to
  `canonical_question_group=OTHER` every day since at least 2026-07-12 (18+ days), root-caused to a one-line bug at
  `instruments-service/.../prediction.py:95`. Because batch6 now CLAIMS that fix, the source doc's own Phase-6 item is
  simultaneously conflict-blocked from reclassification — the fix is reachable from neither side without an operator
  flip. (3) The Phase-0 incremental-skip marker exists in two incompatible shapes in the live corpus
  (`**na-eligibility-audit 2026-07-30**:` vs `**2026-07-27 (na-eligibility-audit)**`); a single-format grep silently
  mis-skips.
status: open
nature: issue
asset_group:
  [ao] # corrected 2026-08-04 (ag-closeout-audit ao tranche run) -- was [cross-cutting]. Agent-operating-framework
  # process tooling (na-eligibility-audit/ag-closeout-audit skill concurrency + draft-gate mechanics), not cross-AG.
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [na-eligibility-audit, ag-closeout-audit, plan-hygiene, tranche-membership, concurrency, ao-dispatch, draft-gate]
related:
  [
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /plans/active/issues/na_doc_tranche_inventory_stale_citation_membership_cross_contamination_2026_07_29.md,
    /plans/archive/issues/prediction_closeout_tag_and_batch_claim_findings_2026_07_30.md,
    /plans/active/prediction_satellite_ao_dispatch_batch6_2026_07_29.md,
    /plans/active/prediction_capture_incident_remediation_2026_07_06.md,
  ]
created: 2026-07-30
author: unknown
parent_epic: agent_operating_framework_master
assigned_vm: planning # reclassified NA -> planning 2026-08-03 (na-eligibility-audit, cross-cutting tranche) — conflict-check CLEAR
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: infra
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
context_scope:
  [
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    scripts/plan-hygiene/generate_na_doc_tranche_inventory.py,
    scripts/plan-hygiene/check_line_caps.sh,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /plans/active/issues/na_doc_tranche_inventory_stale_citation_membership_cross_contamination_2026_07_29.md,
    /plans/active/task_template.md,
  ]
depends_on: []
source:
  [
    "Scheduled /na-eligibility-audit prediction run 2026-07-30 (na_eligibility_auditor, autonomous, one of 9 concurrent
    per-tranche dispatches). No operator was reachable during the run, so every judgment call below is PARKED with
    options + a marked recommendation rather than applied.",
  ]
---

# NA/closeout audit sharding: no owner for shared docs, plus a P0 parked behind a draft gate

## Finding 1 — legitimately multi-tranche docs have no PRIMARY owner (BLOCKED-OPERATOR-DECISION)

**What was measured.** `scripts/plan-hygiene/generate_na_doc_tranche_inventory.py` computes membership as a set
intersection over `asset_group` (per-AG loop, then the `ao`/`ci`/`infra` and `meta`/`cross-cutting` branches). It emits
a `tranches: [...]` LIST per doc and has no concept of a primary/owning tranche. The `--tranche <t>` filter is then a
simple `t in r["tranches"]`.

For the `prediction` tranche on 2026-07-30 that yields 36 docs, of which **16 (47% of the 34 in-scope after the
incremental filter) carry 4-6 tranche memberships**:

| Tranches | Docs                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 5-6      | `issues/adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md`, `issues/backfill_smoke_write_path_canonical_audit_2026_07_20.md`, `issues/candle_feature_canonical_path_divergence_2026_07_20.md`, `issues/estate_orphan_assessment_2026_07_21.md`, `issues/instruments_docs_audit_outstanding_items_2026_07_08.md`, `issues/instruments_remaining_work_audit_2026_07_10.md`, `issues/mdps_features_deadcode_consolidation_2026_07_20.md`, `issues/mtds_is_full_adapter_smoketest_findings_2026_07_07.md`, `issues/ui_coverage_ts_regen_content_drift_after_venue_category_v2_rename_2026_07_28.md` |
| 4        | `issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md`, `issues/uac_per_venue_seed_fallback_removal_deferred_2026_07_26.md`                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| 2        | the 5 `[sports, prediction]` docs (`sports_arb_decay_window_and_alpha_gate_design`, `sports_group_c_execution_backtest_harness`, `sports_odds_feature_naming_canonicalization`, `sports_predictions_live_mode_activation_readiness`, `issues/sports_odds_feature_naming_four_way_mismatch`)                                                                                                                                                                                                                                                                                                                                 |

**Why it matters.** `na-eligibility-auditor.timer` fires **one dispatch per tranche, up to 9 concurrent**. Every one of
those 16 docs is therefore read end-to-end, verdicted, and (per the skill's Phase 3) has a dated Progress Log marker
written into it by between 2 and 6 workers simultaneously, against the same files. Two concrete costs:

- **Redundant classification at 2-6x on nearly half the population.** The most expensive docs in the corpus are in this
  class (`instruments_remaining_work_audit` 979 lines, `mtds_is_full_adapter_smoketest_findings` 646,
  `instruments_docs_audit_outstanding_items` 631, `candle_feature_canonical_path_divergence` 542,
  `estate_orphan_assessment` 517) — the sharding concentrates duplicate work on exactly the heaviest reads.
- **Write collisions.** Phase 3 mandates a marker on every KEEP-NA doc. N workers appending a marker at the same
  location in the same Progress Log is an N-way merge conflict when the per-tranche branches are integrated, and the
  RECLASSIFY path is worse — two workers can flip `assigned_vm` and fill DIFFERENT `assigned_role` values from their own
  tranche's perspective. This is not hypothetical: the infra tranche's 2026-07-30 run already recorded reclassifying 3
  docs that belonged to other tranches and deciding to leave the edits applied
  (`na_doc_tranche_inventory_stale_citation_membership_cross_contamination_2026_07_29.md` Progress Log).

**How THIS run handled it (so the corpus state is legible).** Deliberately conservative: all 34 in-scope docs were
classified, but the dated verdict marker was written **only to the 18 prediction-primary docs** (`asset_group` is
prediction-only, or the doc is prediction-named with `parent_epic: predictions_master`). The 16 shared docs above were
verdicted in the run report but NOT edited, to avoid a 6-way collision during a known-concurrent window. **Side effect
worth naming: those 16 now have no incremental-skip anchor from any tranche, so every future run of every tranche
re-reads them from scratch** — the incremental mode is effectively off for half this population until an ownership rule
exists.

**This is NOT the already-fixed citation bug.**
`na_doc_tranche_inventory_stale_citation_membership_cross_contamination_2026_07_29.md` (fixed
`unified-trading-pm@6228cff7e`) was about docs landing in the WRONG tranche via a stale citation-grep. Every doc in the
table above is in the RIGHT tranches — the gap is that "right for N tranches" has no arbitration for who acts.

**Options:**

- **A [WORKER REC]** — Add a `primary_tranche` to the inventory script's output, derived from `parent_epic` (the axis
  `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 2 already names as the clean,
  single-valued grouping axis: `predictions_master` -> `prediction`, `infrastructure_master` -> `infra`,
  `instruments_master` -> the AG named by the doc, etc.), and have both skills' Phase 3 **apply** steps act only on docs
  whose primary tranche matches the run, while still **classifying** the full membership set. Cheapest correct fix,
  reuses an axis the codex already blesses, and needs no corpus retagging.
- **B** — Keep the script as-is and add an ordering/lock convention to the skills: the alphabetically-first tranche in a
  doc's `tranches` list owns the write. Zero tooling change, but arbitrary and invisible from the doc itself.
- **C** — Serialise the 9 dispatches instead of running them concurrently. Removes the collision entirely but gives up
  the whole point of the sharding (the concurrent run is what makes a daily full sweep affordable).
- **D** — Accept the redundancy and make the markers merge-safe (one marker line per tranche, appended in a per-tranche
  subsection). Fixes conflicts, keeps the 2-6x duplicate reads.
- **Other:** operator may specify a different ownership rule.

## Finding 2 — a live P0 data-correctness fix is parked behind an un-flipped `status: draft` batch (BLOCKED-OPERATOR-DECISION)

`prediction_satellite_ao_dispatch_batch6_2026_07_29.md` was drafted by the `/ag-closeout-audit prediction` scheduled run
on 2026-07-29 and is still `status: draft` as of this run (re-verified live). Its **todo 1** is:

> Fix the write-time `canonical_question_group` mis-bucketing bug — 79% of daily Kalshi volume silently routes to
> `OTHER` ... every day since at least 2026-07-12 ... `instruments-service/.../prediction.py:95` passes the FULL
> `instrument_key` instead of the bare Kalshi ticker into the CQG classifier.

That is a live, ongoing data-correctness defect (18+ days as of today), root-caused with a one-line fix and a
machine-checkable done-when. Per CLAUDE.md, "Data pipeline correctness is the heartbeat."

**The deadlock this run hit.** `status: draft` means batch6 is not ingested by `regen_backlog_from_plan.py` and is never
dispatched. Meanwhile, because batch6 _claims_ the fix, this run's Phase-2 conflict-check correctly refuses to
RECLASSIFY the source doc (`prediction_capture_incident_remediation_2026_07_06.md`, whose Phase 6 carries the same item)
— flipping it would create a duplicate claim. So the P0 is reachable from neither side. Flipping a drafted AO batch to
`active` is explicitly an operator decision (CLAUDE.md "Plan destination — ASK BEFORE CREATING" HARD RULE), so this run
did not do it.

**Note before flipping:** `prediction_closeout_tag_and_batch_claim_findings_2026_07_30.md` Finding 2 (independently
re-confirmed by this run's own conflict-check) shows **batch4 todo 3 and batch6 todo 7 claim the identical cqg
recent-window re-enumeration item**. Flipping batch6 as-is dispatches that item to two workers — the exact
duplicate-dispatch class already filed as `prediction_trades_migration_concurrent_dispatch_2026_07_28.md`.

**Options:**

- **A [WORKER REC]** — Resolve the batch4/batch6 duplicate first (delete batch6 todo 7, cite batch4 todo 3 in its
  Deferred section, per the closeout-findings doc's own mechanical recommendation), then flip batch6 to
  `status: active`. Gets the P0 dispatched with no duplicate-dispatch hazard.
- **B** — Flip batch6 to `active` now and accept the one duplicated todo (the underlying re-enumeration is idempotent,
  so the cost is wasted compute, not corruption). Fastest to unblock the P0.
- **C** — Leave batch6 draft and instead reclassify only the source doc's Phase-6 item by splitting it out. Avoids the
  operator flip but creates a competing claim — the conflict-check protocol explicitly forbids resolving an overlap by
  preferring one side.
- **Other:** operator may dispatch the one-line fix directly outside the batch.

## Finding 3 — the incremental-skip verdict marker has two incompatible formats (mechanical)

The skill's Phase 0 says to grep each doc for "a dated `na-eligibility-audit YYYY-MM-DD` ... verdict marker". The live
corpus contains at least two shapes:

- `**na-eligibility-audit 2026-07-30**: KEEP-NA, valid — ...` (name-then-date) — e.g.
  `ag_closeout_audit_rollout_2026_07_25.md:963`, `issues/group_c_cloud_run_job_failures_triage_2026_07_16.md:373`.
- `**2026-07-27 (na-eligibility-audit)** — Full re-read of all 14 open items ...` (date-then-name) — e.g.
  `issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md:492`, written by the 2026-07-27 tradfi
  dry-run.

A grep written for only one shape mis-classifies the other. This run's first-pass regex matched name-then-date only and
therefore treated the tradfi-marked doc as unverdicted; harmless here (it had been edited since, so it was in scope
anyway), but the failure is silent and direction-dependent — a date-first-only grep would OVER-skip and silently drop
genuinely-changed docs from Phase 1.

## Finding 4 — the 1000-line hard cap makes the incremental marker PHYSICALLY unwritable in the biggest NA docs (BLOCKED-OPERATOR-DECISION)

_Added 2026-08-02 by the scheduled `/na-eligibility-audit cross-cutting` run (autonomous). Same mechanism family as
Finding 3: both defeat Phase 0's incremental skip, this one structurally rather than by regex._

`check_line_caps.sh` enforces a flat **1000L HARD cap** on `plans/active/*.md` (`>1000` fails), and in
scoped/`--precommit` mode ANY staged over-cap plan fails outright. Three of this tranche's docs are pinned at the
ceiling **right now**:

| doc                                                              | lines | open todos | headroom    |
| ---------------------------------------------------------------- | ----- | ---------- | ----------- |
| `data_completion_to_100_all_ag_2026_06_21.md`                    | 1000  | 16         | **0**       |
| `instruments_completion_tracker_2026_07_06.md`                   | 1000  | 15         | **0**       |
| `master_data_canonicalisation_migration_catalogue_2026_06_07.md` | 999   | 6          | 1 (needs 3) |

Writing the one-line Phase-3 verdict marker into any of them pushes the file over the cap and blocks the commit. So the
three **largest** NA docs in the tranche — 37 open todos between them, the most expensive to read — are the exact three
that can never carry a skip marker, and every scheduled run re-reads all three in full, forever. That is the single
biggest recurring cost in this tranche's runtime, and it grows as more docs get trimmed _to_ the cap rather than under
it. (`master_data_canonicalisation` additionally has no `## Progress Log` section at all, so it needs 3 lines, not 1.)

Note this is self-reinforcing with the line-cap remediation work: that effort's success condition is docs sitting _at_
1000L, which is precisely the state that breaks marker-writability.

- **A [WORKER REC]**: let the marker live in **frontmatter** instead of the body — one
  `na_audit_verdict: KEEP-NA <date>` scalar, which `docspec` already parses and which `check_line_caps.sh` counts but is
  1 line for a doc that has no Progress Log either. Still costs 1 line, so pair it with **A2**: exclude frontmatter
  lines from the line-cap count (they are schema, not content — arguably the cap was always meant to bound prose).
- **B**: keep an EXTERNAL marker sidecar — a single `scripts/plan-hygiene/na_audit_verdicts.yaml` keyed by doc path +
  verdict + date + the git SHA the verdict was made against. Zero lines in any plan, survives the cap entirely, and the
  SHA makes the staleness test exact instead of date-based. Costs one new tracked file and a small script change.
- **C**: split the three docs under the cap so a marker fits. Correct in principle but it is real content surgery on
  three live operator coordinators, and it buys ~a handful of lines before they refill.
- **D**: accept the permanent re-read cost and document it in SKILL.md so future runs stop rediscovering it.
- **Other**: operator text.

## Finding 5 (mechanical, folded into the Finding-3 todo) — `task_template.md` is in the NA inventory population

`plans/active/task_template.md` carries `assigned_vm: NA` + `status: active` so `generate_na_doc_tranche_inventory.py`
counts it as a cross-cutting NA doc — but it is the **authoring template every plan is copied from**, with 0 real todos
(its `- [ ]` examples are illustrative). `docspec.is_exempt` already exempts `INDEX.md` and `_`-prefixed docs, and
`zero_checkbox_sweep_all_tranches_2026_07_31.md` independently lists `task_template.md` as structurally exempt — the NA
inventory is the one population that still includes it. This run deliberately did **not** write a verdict marker into it
(a dated audit line inside the template would be copied into every new plan authored from it), which means it re-enters
scope on every run. Fix belongs with Finding 3's script todo.

## Todos

- [ ] [SCRIPT] P2. **DEFAULT-RULED 2026-08-06, option A+A2: frontmatter scalar (`na_audit_verdict: KEEP-NA <date>`),
      paired with excluding frontmatter lines from the line-cap count entirely.** `[SCRIPT]` tag (was `[OPERATOR]`) —
      lowest-friction, consistent with how markers already work elsewhere in this corpus; the line-cap exclusion avoids
      the marker itself contributing to over-cap pressure. Rule on Finding 4 (A / A2 / B / C / D) — where the
      incremental-skip verdict marker lives for a doc pinned at the 1000L hard cap. **Done when**: the ruling is
      recorded here and, for A/A2/B, the marker mechanism is implemented in
      `scripts/plan-hygiene/generate_na_doc_tranche_inventory.py` + named in
      `/cursor-configs/skills/na-eligibility-audit/SKILL.md` Phase 0, and the three docs in the table above carry a
      readable verdict. (repo: unified-trading-pm)
- [x] ✅ [OPERATOR] P1. Rule on Finding 1 (A / B / C / D) — how concurrent per-tranche audits arbitrate ownership of a
      legitimately multi-tranche doc. **Done when**: the ruling is recorded here and, if A, `primary_tranche` is emitted
      by `scripts/plan-hygiene/generate_na_doc_tranche_inventory.py` with a unit test, and both skills' Phase 3 sections
      cite it as the apply-scope gate. -- CLOSED (na-eligibility-audit 2026-08-03): Option A shipped in full. Directly
      confirmed live: `generate_na_doc_tranche_inventory.py --tranche cross-cutting --json` emits an `owning_tranche`
      field per doc, derived from `parent_epic` exactly as Option A specified;
      `tests/unit/test_generate_na_doc_tranche_inventory.py` covers it;
      `cursor-configs/skills/na-eligibility-audit/SKILL.md`'s own Phase 0 now states the primary-owner rule as HARD, and
      `cursor-configs/skills/ag-closeout-audit/SKILL.md` (lines ~508/513) cites the same rule rather than duplicating
      it. All "done when" criteria met. (repo: unified-trading-pm)
- [x] ✅ [OPERATOR] P0. Rule on Finding 2 (A / B / C) — how the parked `prediction.py:95` CQG P0 gets dispatched. **Done
      when**: batch6 is either `status: active` (with the batch4/batch6 duplicate resolved if option A) or the fix is
      dispatched by another named route, and this todo cites the resulting SHA. -- CLOSED (na-eligibility-audit
      2026-08-03): Option A executed. Directly confirmed live: `prediction_satellite_ao_dispatch_batch6_2026_07_29.md`
      is `status: active` + `assigned_vm: planning`; its todo 1 shows
      `[x] ✅ [CODE] P0. DONE 2026-07-30 —     instruments-service@94f3ee11` (repointed 2026-08-06 — original sha
      orphaned by the 2026-08-05 history rewrite; content verified identical) (the CQG mis-bucketing fix); the
      batch4/batch6 duplicate (todo 7) was resolved via that section's explicit 2026-07-30 operator ruling, recorded in
      `/plans/active/prediction_satellite_ao_dispatch_batch6_2026_07_29.md`'s own
      `## Deferred — duplicate extraction, sole owner is batch4 todo 3` section. (repo: unified-trading-pm,
      instruments-service)
- [ ] [SCRIPT] P2. Resolve Finding 3: pick ONE canonical verdict-marker format, state it explicitly in
      `/cursor-configs/skills/na-eligibility-audit/SKILL.md` Phase 0/3 (recommend the name-then-date form
      `**na-eligibility-audit YYYY-MM-DD (<tranche> tranche)**:`, which also carries the tranche needed by Finding 1's
      option D), and make the Phase-0 skip filter match both shapes so already-marked docs are not re-read while the
      corpus still carries the legacy form. **Done when**: the SKILL.md text names one format and the skip filter is
      documented as accepting both. (repo: unified-trading-pm) **Scope extended 2026-08-02 (cross-cutting run): (a) a
      THIRD live shape exists** —
      `### 2026-07-30 (`/na-eligibility-audit`, tranche=cross-cutting, autonomous) — KEEP-NA     verdict` as a heading,
      found in `issues/ag_closeout_linkage_gate_blind_to_four_tranches_2026_07_30.md` and normalized to the
      name-then-date form by that run; whatever filter lands must tolerate the heading shape too, or re-normalize the
      stragglers. **(b) also exclude `plans/active/task_template.md` from the NA inventory population** per Finding 5 —
      mirror `docspec.is_exempt`'s existing `INDEX.md`/`_`-prefix carve-outs in `generate_na_doc_tranche_inventory.py`,
      so the authoring template stops entering scope on every run.

## Codex SSOTs

- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 2 (`parent_epic` as the clean
  single-valued grouping axis — the basis of Finding 1's option A) and § 3 (the conflict-check protocol whose correct
  application produced Finding 2's deadlock).
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility" — the bar every
  verdict in this run's Phase 1 was measured against.
- `/codex/02-data/data-pipeline-correctness-hard-rule.md` — why Finding 2's parked item is P0 rather than routine.

## Progress Log

- **na-eligibility-audit 2026-08-03 (cross-cutting tranche)**: KEEP-NA-STALE items closed + RECLASSIFY. Findings 1 and
  2's `[OPERATOR]` todos both verified resolved with hard evidence (see checkboxes above) and closed. The remaining open
  todos — Finding 4 (`[OPERATOR]` P2, still genuinely open: re-verified live,
  `master_data_canonicalisation_migration_catalogue_2026_06_07.md` is at 999/1000 lines with no `## Progress Log`
  section, i.e. still physically unable to carry a marker, exactly as this finding predicted) and Finding 3 (`[SCRIPT]`
  P2, still open: SKILL.md's Phase 0 does not yet document multi-format marker tolerance, and `task_template.md` is
  still not excluded from the inventory population) — are bounded/mechanical (Finding 3) or correctly gated (Finding 4,
  stays non-dispatchable regardless of this flip). Conflict-check (§3): no active `assigned_vm: planning` doc under
  `parent_epic: agent_operating_framework_master` claims Finding 3's specific fix (marker-format consolidation +
  `task_template.md` exclusion) — CLEAR. Flipped `assigned_vm: NA -> planning`, `execution_scope` to
  `orchestrator-agent`. No finalize-plan companion needed (`doc_type: issue`, structurally exempt).
- **context-scout 2026-08-03**: refreshed context_scope (6 entries) — retargeted onto the doc's now-remaining open work
  (Finding 3's marker-format script + `task_template.md` exclusion, Finding 4's line-cap gate) since Findings 1 and 2
  are now closed; added the two concrete script targets (`generate_na_doc_tranche_inventory.py`, `check_line_caps.sh`)
  and `task_template.md` that were previously named in prose but not cited.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged.
