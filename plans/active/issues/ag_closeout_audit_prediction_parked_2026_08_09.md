---
doc_type: issue
title: >-
  Prediction tranche closeout-audit findings (2026-08-09) — full 37-doc Phase-1 re-sweep, 8 orphans found, 4 extracted
  to batch10, 4 correctly non-batchable; 1 fresh checkbox-provenance finding on the fixture-pairing residual
summary: >-
  Filed by the scheduled `/ag-closeout-audit prediction` run 2026-08-09 (Phases 0-3, dispatch agt-465129). Unlike the
  last several daily runs (08-04/06/07/08, each a light re-verify of an unchanged corpus fingerprint), today's corpus
  had genuinely moved — `generate_ag_closeout_audit_candidates.py --tranche prediction` returned `total_members=37`
  (down from 38 on 08-08) and a fully different `never_cited` composition (10 docs, only 5 of 10 basenames overlapping
  the 08-08 carryover set) — so this run executed a full Phase-1 Workflow fan-out over all 37 AG-primary candidates (not
  just the never-cited delta), 0 errors. Verdicts: 22 `exclude_cross_cutting`, 6 `archivable_after_planned_work`, 1
  `archivable_now`, 4 `orphaned_partial_coverage`, 4 `orphaned_never_touched` — 8 genuine orphans. Phase 3
  conflict-check (re-verified via fresh grep across all 15 covering docs immediately before drafting, not assumed from
  the Phase-1 agents' own grep alone) found 4 of the 8 were conflict-clear and newly AO-eligible (2 operator-ruled
  2026-08-07 dead-code deletions, 1 batch4-Deferred item whose gate cleared 2026-07-28, 1
  declassified-from-operator-call data backfill) — extracted into
  `prediction_satellite_ao_dispatch_batch10_2026_08_09.md` (`status: draft`) + a gated `_finalize` twin. The other 4
  orphans are correctly non-batchable per the skill's own taxonomy (1 too-large-for-a-batch-todo, 1 operator-gated, 1
  time-gated on an external cross-tranche dependency, 1 belongs to the `infra`/`ci` tranche) — parked below, none newly
  actionable from this tranche. One fresh finding, below, on a likely checkbox-citation over-claim in a prior batch.
status: open
nature: issue
asset_group: [prediction]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [prediction, ag-closeout-audit, orphan-audit, plan-hygiene]
related:
  [
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_08/prediction_satellite_ao_dispatch_batch10_2026_08_09.md,
    /plans/archive/2026_08/prediction_satellite_ao_dispatch_batch10_2026_08_09_finalize.md,
    /plans/archive/issues/ag_closeout_audit_prediction_parked_2026_08_08.md,
    /plans/archive/2026_08/issues/ag_closeout_audit_prediction_parked_2026_07_31.md,
    /plans/active/data_completion_prediction_2026_07_15.md,
    /plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md,
    /plans/active/prediction_satellite_ao_dispatch_batch6_2026_07_29.md,
    /plans/active/predictions_ml_walk_forward_and_arb_2026_06_20.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: 2026-08-09
author: unknown
parent_epic: predictions_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: data_engineering
drift_direction: none
depends_on: []
source:
  [
    "Scheduled /ag-closeout-audit prediction run 2026-08-09 (ag_closeout_auditor, slot 14, dispatch agt-465129).
    Operator was not interactively present during the run, so all judgment-relevant items below are parked rather than
    guessed.",
  ]
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py,
  ]
---

# Prediction closeout-audit findings, 2026-08-09

> **Context.** Full Phase 0-3 results of today's `/ag-closeout-audit prediction` pass. 37 AG-primary candidates audited
> (via a 37-agent Workflow fan-out, 0 errors); 8 genuine orphans found; 4 extracted to
> `prediction_satellite_ao_dispatch_batch10_2026_08_09.md`; 4 remain correctly parked (below). One fresh
> checkbox-provenance finding, also below.

## Phase 2 — orphan report

**8 orphaned docs** (excludes the 22 `exclude_cross_cutting` docs, which are genuinely multi-AG/other-AG content —
re-verified this run via the Orthogonality HARD CHECK, see below):

`orphaned_partial_coverage` (4 — some remaining work covered, some not):

1. [`data_completion_prediction_2026_07_15.md`](/plans/active/data_completion_prediction_2026_07_15.md) — 19 open items;
   the headline Phase-B OBJECT-layer CQG-bundle migration (5 items) is confirmed uncovered by 6 independent audit passes
   now (see Finding 1 below); a smaller manifest-VALUE-relabeling slice IS covered (applied 2026-07-19).
2. [`prediction_capture_incident_remediation_2026_07_06.md`](/plans/active/prediction_capture_incident_remediation_2026_07_06.md)
   — 7 of 8 open items correctly parked under the 2026-07-14 perps-not-MVP ruling; the 8th (Phase 6's historical Kalshi
   `OTHER`-bucket reclassify) was declassified from an operator call 2026-08-08 and had real narrative acknowledgment
   but zero execution claim anywhere — **extracted to batch10 todo 2**.
3. [`prediction_cross_venue_arb_and_coverage_2026_07_24.md`](/plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md)
   — 4 remaining items; 2 already fully covered by today's earlier `batch9` (dispatched), 1 (fixture-pairing checkbox)
   likely stale-but-covered by `batch6` (see Finding 5 below), 1 (tarball-overwrite race) belongs to `infra`/`ci`.
4. [`prediction_live_clob_depth_capture_2026_07_24.md`](/plans/active/prediction_live_clob_depth_capture_2026_07_24.md)
   — 34/35 checkboxes done; the sole remainder (`book_snapshot_5` batch row-proof) was gate-cleared 2026-07-28 and named
   "ready" by its own 2026-08-07 finalize entry, but never dispatched anywhere — **extracted to batch10 todo 1**.

`orphaned_never_touched` (4 — nothing covers the remaining work at all):

5. [`issues/ag_closeout_audit_prediction_parked_2026_07_31.md`](/plans/archive/2026_08/issues/ag_closeout_audit_prediction_parked_2026_07_31.md)
   Finding 1 — an (A) delete vs (B) keep-and-document judgment call on 2 _other_ adapter dead-code docs (distinct from
   the 2 extracted below), still explicitly unadjudicated. Correctly non-batchable (operator-gated).
6. [`issues/is_polymarket_dead_fixture_cross_reference_2026_07_31.md`](/plans/archive/2026_08/issues/is_polymarket_dead_fixture_cross_reference_2026_07_31.md)
   — the judgment call that blocked this WAS resolved (operator RULED 2026-08-07, option A: DELETE), but the deletion
   itself was never executed — **extracted to batch10 todo 3**.
7. [`issues/mtds_prediction_adapters_dead_rest_polling_interface_2026_07_31.md`](/plans/active/issues/mtds_prediction_adapters_dead_rest_polling_interface_2026_07_31.md)
   — same shape, same 2026-08-07 operator ruling (option A: DELETE), never executed — **extracted to batch10 todo 4**.
8. [`predictions_ml_walk_forward_and_arb_2026_06_20.md`](/plans/active/predictions_ml_walk_forward_and_arb_2026_06_20.md)
   — 4 P0/P1 items chained on the external `sports_master:Group E` gate (confirmed still unchecked live). Correctly
   non-batchable (time-gated on a cross-tranche dependency this tranche doesn't control).

**Ledger**: 8 orphans found, 4 extracted (batch10), 4 parked below as Findings 2-4 (Finding 1 covers doc #1's recurring
gap). `parked_findings` count for this doc: **5** (Findings 1-5 below) == 5 entries written. Balanced.

## Orthogonality HARD CHECK (re-run this cycle)

Grepped the corpus for `asset_group:.*cross-cutting` and checked every hit's array for a `prediction`-plus-exactly-one-
other-peer-marker mistag shape: **zero hits** — the 3 cross-cutting-tagged docs touching prediction content
(`ag_closeout_audit_rollout_2026_07_25.md`, `issues/autonomous_session_operator_decisions_2026_07_25.md`,
`issues/instruments_remaining_work_audit_2026_07_10.md`) all carry 5-6 real peer-AG markers (genuinely multi-AG, not a
dual-tag mistag). Also checked the "fork inherits parent's bare `[cross-cutting]` tag" pattern for any
`prediction_*`/`kalshi_*`/`polymarket_*`-named doc: the only filename-hint hit
(`sports_prediction_mvp_writetime_precompute_2026_07_24.md`) was read directly and confirmed genuinely cross-cutting (a
shared manifest-schema/deployment-infra change spanning sports+prediction+deployment-api,
`parent_epic: deployment_and_user_management_master`) — not a mistag. No retag needed this cycle.

## Finding 1 — `data_completion_prediction_2026_07_15.md`'s Phase-B migration: 6 audit passes deep with no dedicated

plan ever authored

The doc's headline P0 cluster (ship MTDS+UAC+MDPS live-writer bundle change, build a historical rollup migration script,
pre-migration drain, post-verify, delete superseded objects — 5 chained items) has now been independently re-triaged to
"0 AO-eligible as a batch todo, needs its own dedicated design/scoping plan" by **six** separate audit passes: batch1,
batch2 (as a Phase-B-naming-ambiguity operator-gated conflict), batch3, batch4, batch6, and now this run. Every pass
agrees on the verdict; none has actually authored the dedicated plan the verdict calls for.

**Why not resolved here.** Scoping a 3-repo coordinated migration (which combined-design approach, what the historical
rollup script's exact algorithm is, drain/verify sequencing) is a genuine design decision — exactly the
"too-large-or-risky-for-a-batch-todo" non-batchable category, not a fact this run can determine by reading code.

**Recommendation.** Six agreeing audit passes without action is a different situation from one or two — worth a direct
operator decision on whether to prioritize authoring that dedicated design/scoping plan (as a LOCAL, human-driven plan
per CLAUDE.md's "Plan destination" default), rather than a 7th automated pass re-confirming the same gap. Options: **(a)
[recommended]** operator (or a human session) authors the dedicated Phase-B migration design plan directly, closing this
recurring finding for good; (b) leave it parked and let it keep resurfacing on each daily audit (status quo, costs one
report line per day, zero forward progress); (c) explicitly deprioritize/shelve the Phase-B migration if it's no longer
worth doing, and close this thread by editing `data_completion_prediction_2026_07_15.md` to reflect that decision. No
action taken here beyond flagging — this is a design/priority call, not a worker- determinable fact.

## Finding 2 — `ag_closeout_audit_prediction_parked_2026_07_31.md` Finding 1: its own condition has now been satisfied

`ag_closeout_audit_prediction_parked_2026_07_31.md`'s Finding 1 links the SAME 2 adapter dead-code docs
`prediction_satellite_ao_dispatch_batch10_2026_08_09.md` todos 3/4 now extract
(`is_polymarket_dead_fixture_cross_reference_2026_07_31.md`,
`mtds_prediction_adapters_dead_rest_polling_interface_2026_07_31.md`). Its stated wait condition — "no action needed...
unless/until an operator or the next worker touching either adapter file picks (A) or (B)" — has already been satisfied:
both docs now carry explicit 2026-08-07 operator rulings (DELETE, option A), which is why this run classified
`orphaned_never_touched` (bounded, ruled, just never executed) rather than re-parking them as still-operator-gated (they
were, historically, per 4 prior re-confirmations: 07-31, 08-02, 08-04, 08-07 na-audits — but the gate cleared
2026-08-07). No fresh action needed on the 07-31 parked doc itself here (it is a historical record, not a live task);
its own `[DOC] P3` todo should be flipped `[x]` once batch10 todos 3/4 land — folded into `batch10_finalize`'s
reconciliation scope rather than a separate todo here, to avoid a duplicate-dispatch surface on the same 2 underlying
fixes.

## Finding 3 — `predictions_ml_walk_forward_and_arb_2026_06_20.md`: time-gate re-confirmed unchanged

`sports_master.md:629`'s Group E gate is still unchecked live as of this run. No action needed; re-check on the next
`/ag-closeout-audit prediction` cycle or whenever `sports_master` Group E is independently touched.

## Finding 4 — `prediction_cross_venue_arb_and_coverage_2026_07_24.md`'s tarball-overwrite race: belongs to `infra`/`ci`

Re-confirmed unchanged since batch4 first flagged it (2026-07-26): a concurrent fleet `create-code-tarballs` run can
clobber a freshly-rebuilt tarball/setup-script before a new VM's boot-fetch. Zero prediction-specific content; a generic
VM-fleet build-race. Flagging again for the `infra`/`ci` tranche's own `/ag-closeout-audit` sibling run to pick up — per
the primary-owner rule, this tranche does not draft a competing todo on infra-owned ground.

## Finding 5 — possible checkbox-citation over-claim: fixture-pairing residual may only be partially closed

`prediction_cross_venue_arb_and_coverage_2026_07_24.md`'s `[DESIGN] P1` fixture-pairing residual has 3 parts: (3a)
resolve each `SportsFixtureKey` to a canonical sport fixture via the sports-domain registry, (3b) populate
`CanonicalPredictionMarket.mapped_sport_event_id` + `PredictionMarketCrossVenueMapping`, (3c) team-name canonicaliser
for the arb-layer grouping. Both the Phase-1 classifying agent (this run) and `batch9`'s own drafting pass (also today)
independently treated this as fully claimed by `prediction_satellite_ao_dispatch_batch6_2026_07_29.md`'s `[DATA] P2`
"team-name alias tables" todo (`unified-api-contracts@41c13454`, `strategy-service@217e5b0e`, 2026-08-05). Reading that
todo's own shipped-evidence text closely, it explicitly describes building alias **resolution** (3c) — no mention of
3a's registry-resolution join or 3b's `mapped_sport_event_id`/ `PredictionMarketCrossVenueMapping` population. However,
batch6's own Progress Log ALSO references 3 SHAs including one on **instruments-service**
(`instruments-service@62a8b1d8`, mentioned in a 2026-07-31 re-dispatch entry) which this run did not cross-check against
3a/3b's specific done-when criteria — instruments-service is exactly the repo 3a/3b's "sports-event link on prediction
enum" work would land in. **Not re-litigated a 4th time by drafting a competing batch10 todo** (that would risk a real
duplicate-dispatch collision if 3a/3b genuinely did ship under that SHA) — flagging as a targeted verification gap for
whoever next closes batch6's own fixture-pairing todo or reconciles
`prediction_cross_venue_arb_and_coverage_2026_07_24.md`'s checkbox: confirm `instruments-service@62a8b1d8`'s actual diff
covers 3a+3b before treating the residual as fully closed.

## Todos

- [ ] [DOC] P3. No action needed on Finding 1 unless/until an operator rules on one of the 3 options (author the
      dedicated Phase-B design plan / leave parked / explicitly deprioritize). Informational only. (repo:
      unified-trading-pm)
- [ ] [DOC] P3. No action needed on Finding 2 directly — folded into
      `prediction_satellite_ao_dispatch_batch10_2026_08_09_finalize.md`'s reconciliation scope once batch10 todos 3/4
      land. (repo: unified-trading-pm)
- [ ] [DOC] P3. No action needed on Finding 3 — re-check when `sports_master` Group E next moves. (repo:
      unified-trading-pm)
- [ ] [DOC] P3. No action needed on Finding 4 here — flagged for the `infra`/`ci` tranche's own audit, not this
      tranche's file to fix. (repo: unified-trading-pm)
- [ ] [DOC] P3. Finding 5 — before any future pass treats `prediction_cross_venue_arb_and_coverage_2026_07_24.md`'s
      fixture-pairing checkbox as closable, verify `instruments-service@62a8b1d8`'s actual diff covers parts 3a
      (registry-resolution) and 3b (`mapped_sport_event_id`/`PredictionMarketCrossVenueMapping` population), not just 3c
      (team-name canonicalisation). **Done when**: an explicit verdict (covers / doesn't cover 3a+3b) is recorded on
      this doc or the checkbox's own citation. (repo: unified-trading-pm)

## Codex SSOTs

- `/cursor-configs/skills/ag-closeout-audit/SKILL.md` — Phase 0-3 procedure this run followed.
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility" — why Finding
  1's item stays non-batchable.
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 3 — the conflict-check protocol
  applied before drafting batch10.

## Progress Log

- **2026-08-09 (slot 14, ag_closeout_auditor, dispatch agt-465129):** Filed by the scheduled
  `/ag-closeout-audit prediction` run. Phase 0: discovered 15 covering plans (consolidated closeout + 4 Phase A-E
  children + satellite batches 4/6/7/8/9 + their finalizes), confirming the closeout-hub `depends_on:` resolution fix
  (shipped 2026-08-01) is still live (11 phase-child entries structurally resolved, not just via incidental citation).
  Phase 1: full 37-candidate Workflow fan-out (`wf_52c10a43-54a`, 0 errors, ~871s, ~3.39M subagent tokens) — 22
  `exclude_cross_cutting`, 6 `archivable_after_planned_work`, 1 `archivable_now`, 4 `orphaned_partial_coverage`, 4
  `orphaned_never_touched`. Phase 3: conflict-checked all 8 orphans against the full 15-doc covering set (re-verified
  via fresh grep immediately before drafting, not assumed from the Phase-1 agents' own grep alone) — 4 conflict-clear
  and extracted to `prediction_satellite_ao_dispatch_batch10_2026_08_09.md` (`status: draft`) + gated `_finalize`
  (`status: active`), both validated against `check_frontmatter_schema.py` + `check_todo_format.sh`. 4 correctly
  non-batchable, parked as Findings 1-4 above. 1 fresh checkbox-provenance concern (Finding 5) flagged, not acted on
  (would risk a duplicate-dispatch collision if wrong). parked_findings ledger: 5 findings this doc == 5 entries written
  above. Balanced.

- **na-eligibility-audit 2026-08-09 (prediction tranche)**: KEEP-NA, valid — first audit pass (doc created today). 5
  open `[DOC] P3` items: 3 are informational watch-items gated on external/operator decisions (Finding 1 = operator
  decision pending among 3 options; Finding 3 = re-check when `sports_master:Group E` clears; Finding 4 = `infra`/`ci`
  tranche scope, not this tranche's to fix), 1 is a closeable-once-dependent bookkeeping note (Finding 2, folds into
  `batch10_finalize`), 1 is a genuine bounded verification task (Finding 5: confirm `instruments-service@62a8b1d8`
  covers fixture-pairing parts 3a/3b). The mix of externally-gated items means the whole-doc RECLASSIFY bar is not
  cleared — one bounded item among several genuinely-gated ones does not flip a whole doc. Doc stays NA.
- **na-eligibility-audit 2026-08-10 (prediction tranche)**: KEEP-NA, valid — re-verified, 5 open, unchanged since the
  2026-08-09 marker (no new content). Same mix as before: 3 externally-gated watch-items, 1 closeable-once-dependent
  bookkeeping note (Finding 2, still folds into `batch10_finalize` — batch10 confirmed still active/in-flight, 1/5 todos
  done), 1 bounded verification task (Finding 5) not yet independently re-verified this pass. Whole-doc RECLASSIFY bar
  still not cleared. Doc stays NA.
