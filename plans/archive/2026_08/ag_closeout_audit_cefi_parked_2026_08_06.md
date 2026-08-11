---
doc_type: issue
title:
  "Parked findings + full report from the 2026-08-06 /ag-closeout-audit cefi run (19 docs classified across 2 candidate
  sets; batch8 drafted with 3 conflict-clear todos; 3 drafted batches — 4/6/7 — now await operator review, oldest 6
  days; 2 long-carried conflict-gated items re-verified still open; a corpus-wide linkage-gate ratchet regression found
  and filed separately)"
summary: >-
  First `ag_closeout_audit_cefi_parked_*` doc for this tranche. Phase 0 re-derived the covering-plan set via
  `generate_ag_closeout_audit_candidates.py --tranche cefi` (93 members, 14 real active covering docs including batch4,
  batch6 and batch7 — all 3 still `status: draft`, none operator-reviewed since batch7 was drafted 2026-08-03 — 12
  never-cited via the citation heuristic) UNIONED with 7 additional docs `check_ag_closeout_linkage.py` independently
  flagged as cefi-tagged orphans (only 1 of the 7 overlapped the citation heuristic's 12). 19 docs deep-audited via 2
  parallel `Workflow` dispatches. Verdicts: 5 exclude_cross_cutting, 3 archivable_now, 1 self_dispatched_covered, 5
  orphaned_partial_coverage, 5 orphaned_never_touched. 3 of the 10 genuine orphans carried real, conflict-clear
  AO-eligible work, extracted into `cefi_satellite_ao_dispatch_batch8_2026_08_06.md` (+ finalize, both `status: draft`).
  The 2 conflict-gated items carried through batch4→batch6→batch7's Deferred/re-check chain (Schema v10
  `instrument_id_form` backfill; `estate_orphan_assessment` todo 6 cross-tranche boundedness) were independently
  re-verified live — both still open, unchanged. Incidentally found and filed separately (not cefi-scoped, affects 9 of
  10 tranches): `check_ag_closeout_linkage.py`'s live orphan count (87) now exceeds its baseline (69) by 18.
status: resolved
nature: issue
asset_group: [cefi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [cefi, ag-closeout-audit, parked-findings, batch-approval-backlog, dispatch-gap]
related:
  [
    /plans/archive/2026_07/cefi_satellite_ao_dispatch_batch4_2026_07_31.md,
    /plans/archive/2026_08/cefi_satellite_ao_dispatch_batch6_2026_08_02.md,
    /plans/archive/2026_08/cefi_satellite_ao_dispatch_batch7_2026_08_03.md,
    /plans/archive/2026_08/cefi_satellite_ao_dispatch_batch8_2026_08_06.md,
    /plans/archive/2026_08/cefi_satellite_ao_dispatch_batch8_2026_08_06_finalize.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/ag_closeout_linkage_baseline_regression_87_vs_69_2026_08_06.md,
    /plans/active/issues/fail_hard_canonical_enforcement_design_2026_07_20.md,
    /plans/active/issues/estate_orphan_assessment_2026_07_21.md,
    /scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py,
    /scripts/plan-hygiene/check_ag_closeout_linkage.py,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-06"
author: unknown
last_updated: "2026-08-06"
parent_epic: cefi_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
assigned_role: data_engineering
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
context_scope:
  [
    /plans/archive/2026_08/cefi_satellite_ao_dispatch_batch8_2026_08_06.md,
    /plans/active/issues/ag_closeout_linkage_baseline_regression_87_vs_69_2026_08_06.md,
    /plans/archive/2026_08/cefi_satellite_ao_dispatch_batch7_2026_08_03.md,
    /plans/active/issues/fail_hard_canonical_enforcement_design_2026_07_20.md,
    /plans/active/issues/estate_orphan_assessment_2026_07_21.md,
  ]
source: >-
  `/ag-closeout-audit cefi` run 2026-08-06 (ag_closeout_auditor scheduled worker, slot 3, dispatch agt-02411c). Phase 0
  re-derived the covering set via `generate_ag_closeout_audit_candidates.py --tranche cefi` (93 members, 12 never-cited)
  UNIONED with a `check_ag_closeout_linkage.py` cross-check (+7 independently-flagged cefi orphans). Ran the skill's
  iterative-drain step 1 (re-checked the 2 carried-forward Deferred items live) before two parallel Phase-1 `Workflow`
  dispatches (12 + 7 agents) covering all 19 candidates.
---

# Parked findings + full report — 2026-08-06 `/ag-closeout-audit cefi` run

> **🟢 ARCHIVED 2026-08-07 (na-eligibility-audit, tranche=cefi).** Both todos done: todo 1 resolved 2026-08-06
> (governance sweep, `unified-trading-pm@de1d795de1`, all 4 backlogged batches reviewed/activated); todo 2 flipped MOOT
> 2026-08-07 (target doc archived in the 76-doc resolved-issues sweep). The 2 carried-forward
> `BLOCKED-OPERATOR-DECISION` items (`fail_hard_canonical_enforcement_design_2026_07_20.md`'s §5 design gaps;
> `estate_orphan_assessment_2026_07_21.md` todo 6) and the linkage-gate regression finding remain live in their OWN docs
> — not lost, just not owned here. Superseded by nothing — this doc's findings are now permanent record in their
> respective source docs; [`cefi_satellite_ao_dispatch_batch9_2026_08_07.md`](/plans/archive/2026_08/cefi_satellite_ao_dispatch_batch9_2026_08_07.md)'s successor findings live in that doc (or
> its own `ag_closeout_audit_cefi_parked_2026_08_07.md`, if one is later filed).

## New findings this run

### 1. [WORKER REC] 3 drafted AO-dispatch batches (batch4/6/7) now await operator review, oldest 6 days — plus this run's own batch8 makes 4

| batch  | created    | age (from 2026-08-06) | todos | status | done |
| ------ | ---------- | --------------------- | ----- | ------ | ---- |
| batch4 | 2026-07-31 | 6 days                | 7     | draft  | 0/7  |
| batch6 | 2026-08-02 | 4 days                | 6     | draft  | 0/6  |
| batch7 | 2026-08-03 | 3 days                | 3     | draft  | 0/3  |
| batch8 | 2026-08-06 | 0 days (this run)     | 3     | draft  | 0/3  |

Every one of the last 4 audit rounds (batch4 through this run's batch8) correctly found genuinely conflict-clear,
bounded, low-risk work and drafted it per the skill's own safety design (drafting is inert, safe to do autonomously) —
the audit-coverage side of this tranche's pipeline is working as intended, and batch7 itself already independently
re-verified batch4's and batch6's content was still valid (no superseding work landed). But **nothing has been flipped
to `active` in 6 days**: 19 total todos across 4 batches, zero dispatched. This mirrors an identical pattern
independently observed in the `infra` tranche's own 2026-08-04 parked-findings doc (4 drafted batches, oldest 4 days) —
this looks like a cross-tranche operator-review-throughput bottleneck, not a cefi-specific issue, but flagging
per-tranche since that is this doc's scope.

**Recommendation [WORKER REC]**: a single operator pass reviewing batches 4/6/7/8 together (19 todos total, mostly P2/P3
with one P1 in batch8 — the confirmed HYPERLIQUID OOM defect fix — none `[OPERATOR]`-tagged on their own merits, all
already conflict-checked against each other and the corpus) would likely clear most or all to `active` in one sitting.
Not escalating as blocking (no in-flight work depends on these landing urgently), but the accumulation itself is now a
4-batch, 6-day-and-growing queue.

### 2. [CROSS-TRANCHE, filed separately] `check_ag_closeout_linkage.py` ratchet regression — 87 live vs. 69 baseline

Found incidentally while cross-validating cefi's own Phase 0 candidate list against this stricter safety-net check. NOT
cefi-scoped (only 7 of the 87 orphans are cefi-tagged; cross-cutting carries 36, ao 14, defi 11, ci 10). Filed as its
own issue rather than duplicated here:
`/plans/active/issues/ag_closeout_linkage_baseline_regression_87_vs_69_2026_08_06.md`. Flagging its existence here only
so a reader of this doc doesn't miss it.

## Carried forward from the batch4→batch6→batch7 Deferred/re-check chain (re-verified live this run)

Both items remain **OPEN, unchanged** — third-or-later consecutive re-check to find them still blocked:

1. **`issues/fail_hard_canonical_enforcement_design_2026_07_20.md`'s `[DESIGN] P1`** "Close the three §5 gaps
   (derivative-bundle column gate; live-lane dual-resolver reconciliation; read...)" (line 156) — re-checked via direct
   grep: still `- [ ]` open. Transitive gate (Schema v10 `instrument_id_form` backfill Stage 2) NOT cleared.
2. **`issues/estate_orphan_assessment_2026_07_21.md` todo 6** — cross-tranche boundedness disagreement (cefi/sports
   KEEP-NA vs. defi RECLASSIFY). Re-checked via direct grep: the "Operator/next-toucher: rule on todo 6's boundedness"
   note is still present, unresolved.

Both are correctly NOT re-drafted as batch8 candidates (conflict-gated / operator-gated, not re-triageable by this
skill) — batch8's own finalize plan (todo 2) will re-check these again before batch9 is next drafted, and will flag
explicitly for the operator if still unresolved a fourth consecutive time.

## This run's Phase 1 classification — all 19 docs, full report

**Candidate set A (12 docs, citation-heuristic never-cited):**

| doc                                                                                           | verdict                   | ao_eligible      | one-line reasoning                                                                                                                                                               |
| --------------------------------------------------------------------------------------------- | ------------------------- | ---------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `aster_and_cefi_rolling_adv_feature_2026_07_21.md`                                            | orphaned_partial_coverage | No               | Only Phase 3 (strategy-side ADV consumption) remains; explicit undecided design call, independently reaffirmed NA by 2 prior batches + na-eligibility-audit.                     |
| `instruments_cefi_g1_g5_gate_execution_2026_07_24.md`                                         | orphaned_partial_coverage | **Yes → batch8** | 3 stale-open markers (G1.2, GATE G4 banner, MANIFEST_ALLOW_STALE_FALLBACK) all independently re-verified already-true, just never flipped; other 2 open items stay correctly NA. |
| `issues/cefi_backfill_per_day_catalogue_reload_2026_07_20.md`                                 | orphaned_partial_coverage | No               | Remaining `[BACKEND] P2` proper-fix item needs a real design choice (range-loop vs. cross-process cache), not yet scoped in detail.                                              |
| `issues/cefi_book_snapshot5_schema_contract_ts_event_levels_mismatch_2026_07_28.md`           | orphaned_never_touched    | No               | 2 open items, both explicit design/redesign decisions for features-service's loader.                                                                                             |
| `issues/cefi_liquidations_attempted_failed_lifetime_count_stale_2026_07_30.md`                | orphaned_never_touched    | No               | 2 open items, both blocked on an `[OPERATOR]` decision among 3 named options; no code-fix work remains.                                                                          |
| `issues/mdps_features_deadcode_consolidation_2026_07_20.md`                                   | exclude_cross_cutting     | —                | Genuinely multi-AG (`[cefi, defi, tradfi, sports, prediction]`); open items are PREDICTION-specific. Flag for prediction/infra's own audit.                                      |
| `issues/ml_training_and_prediction_pipeline_launchers_stale_post_consolidation_2026_08_04.md` | exclude_cross_cutting     | —                | Genuinely multi-AG (same 5-tag pattern); open items are ML-launcher-CLI-surface verification, not cefi-specific.                                                                 |
| `issues/mtds_live_mode_never_touches_authenticated_tardis_datasets_endpoint_2026_08_02.md`    | orphaned_never_touched    | No               | Sole remaining item is a standing observability tripwire (fires only IF a future connector change happens) — not actionable now.                                                 |
| `issues/per_venue_scope_key_provisioning_incomplete_2026_07_23.md`                            | orphaned_never_touched    | No               | 3 `[HUMAN]`-tagged items (GCP Secret Manager credential provisioning) — direction already ruled, only the operator's own exchange-login action remains.                          |
| `issues/phantom_audit_estate_coverage_gap_2026_07_10.md`                                      | exclude_cross_cutting     | —                | Genuinely multi-AG (`[cefi, defi, tradfi, sports]`); the phantom-audit bucket-list generalization item isn't cefi-specific.                                                      |
| `l2_book_microstructure_capture_2026_07_13.md`                                                | orphaned_never_touched    | No               | 2 open items, both explicitly `BLOCKED-DATA-CORRECTNESS`-prefixed — a real, already-flagged blocker, not fresh work.                                                             |
| `prediction_capture_incident_remediation_2026_07_06.md`                                       | exclude_cross_cutting     | —                | Genuinely multi-AG (`[prediction, cefi]`); 8 open items, none real dispatchable cefi work per na-eligibility-audit 2026-07-30.                                                   |

**Candidate set B (7 docs, `check_ag_closeout_linkage.py`-flagged, missed by the citation heuristic):**

| doc                                                                                                | verdict                   | ao_eligible                   | one-line reasoning                                                                                                                                                                                      |
| -------------------------------------------------------------------------------------------------- | ------------------------- | ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `issues/cefi_bare_okx_venue_removal_2026_08_04.md`                                                 | archivable_now            | housekeeping only             | Both todos done, both cited commits independently re-verified genuine via `git show`.                                                                                                                   |
| `issues/cross_instrument_delta_one_listing_recurring_hang_2026_08_03.md`                           | archivable_now            | housekeeping only             | All 4 todos done, all 4 cited commits independently re-verified genuine; `status:` frontmatter simply never flipped.                                                                                    |
| `issues/features_service_clean_check_dangling_revert_of_hyperliquid_cefi_bucket_fix_2026_08_03.md` | exclude_cross_cutting     | —                             | `asset_group: [defi]`, `parent_epic: defi_master` despite the "cefi_bucket" title — genuinely defi-primary; sole open item is `[OPERATOR]`-gated (drop a specific ruled-abandoned git stash).           |
| `issues/mdps_derivative_ticker_single_instrument_high_rss_2026_08_03.md`                           | orphaned_partial_coverage | **Yes → batch8**              | Confirmed P1 defect (18.5GB RSS OOM on a single-instrument HYPERLIQUID backfill), root cause pinpointed, fix is prose-only (never promoted to a checkbox) — a classic "prose-only remaining work" trap. |
| `issues/multi_timeframe_phantom_captured_manifest_rows_on_universal_write_failure_2026_08_03.md`   | self_dispatched_covered   | No (linkage fix only)         | `assigned_vm: planning`, genuinely self-dispatched; sole remaining item is `[OPERATOR]`-gated compute-cost tradeoff. Needs a `related:` link added to the closeout family, not a new todo.              |
| `issues/okx_futures_instid_marker_convention_mismatch_2026_07_30.md`                               | orphaned_partial_coverage | **Yes → batch8**              | Docstring-reconciliation sub-part is bounded/uncited anywhere; the A/B/C convention decision itself stays `[OPERATOR]`-gated; 2 other items already drafted (still-draft) in batch6.                    |
| `issues/okx_futures_trades_zero_capture_and_polymarket_perp_funding_failed_2026_08_05.md`          | archivable_now            | housekeeping + 1 citation fix | Both todos done, both fixes verified present; one cited commit hash is wrong (`@b2497b73` → should be `@b29285ae`) — fix during archival.                                                               |

## Ledger

19 docs classified this run. 3 extracted into `cefi_satellite_ao_dispatch_batch8_2026_08_06.md` (durable home: the batch
itself). 5 `exclude_cross_cutting` flagged above with one-line reasoning (durable home: this doc + batch8's own
"Cross-tranche notes" section). 3 `archivable_now` + 1 `self_dispatched_covered` flagged above (durable home: this doc

- batch8's own housekeeping sections). 2 carried-forward conflict-gated items re-verified (durable home: this doc +
  batch8-finalize's todo 2). 1 new `[WORKER REC]` finding (the batch-review backlog) + 1 cross-tranche finding (the
  linkage-gate regression, filed as its own doc) = **2 new parked findings this run, 2 entries written above —
  balanced**. Zero genuine `BLOCKED-OPERATOR-DECISION` conflicts found this run (all 3 AO-eligible candidates were
  conflict-clear).

## Todos

- [x] ✅ [OPERATOR] P2. **RESOLVED 2026-08-06 (governance sweep, commit `unified-trading-pm@de1d795de1`).** All 4
      batches reviewed and flipped `status: active` — batch4/6 activated as-drafted after verification; batch7's one
      stale todo (already-deleted stray file) marked done-elsewhere; batch8's stale docstring todo marked done-elsewhere
      and its history-rewrite-affected SHA citation corrected. Original text preserved below for record. **Review +
      approve/decline the 4 backlogged drafted cefi batches** (finding 1) —
      `cefi_satellite_ao_dispatch_batch4_2026_07_31.md` (7 todos), `batch6_2026_08_02.md` (6 todos),
      `batch7_2026_08_03.md` (3 todos), and this run's `batch8_2026_08_06.md` (3 todos, incl. 1 P1 confirmed-defect
      fix).
- [x] ✅ [DOCS] P3. **Add a `related:`/digest mention for
      `multi_timeframe_phantom_captured_manifest_rows_on_universal_write_failure_2026_08_03.md`** in the cefi closeout
      family (finding from Phase 1 candidate set B) — self-dispatched and already being worked, just missing from the
      graph `check_ag_closeout_linkage.py` checks. **MOOT — flipped 2026-08-07 (ag-closeout-audit cefi run, slot 4,
      dispatch agt-ed7b44)**: the doc was archived 2026-08-06 in the 76-doc resolved-issues archive sweep (work
      resolved), so the linkage mention is void; no digest addition needed.

## Progress Log

- **2026-08-06** — `/ag-closeout-audit cefi` run (autonomous mode, scheduled dispatch, slot 3, dispatch agt-02411c).
  Phase 0: 93 members, 14 active covering docs (batch4/6/7 all still draft, all still count as covering per the skill's
  widened rule), 12 never-cited via citation heuristic. Cross-validated with `check_ag_closeout_linkage.py` (+7
  independently-flagged orphans, only 1 overlap) — found and filed the corpus-wide linkage-gate ratchet regression as
  its own issue in the same pass. Re-checked both carried-forward conflict-gated Deferred items live (0 resolved, both
  still open). Ran 2 parallel Phase-1 `Workflow` dispatches (12 + 7 agents, 0 errors) covering all 19 candidates.
  Extracted 3 conflict-clear AO-eligible items into `cefi_satellite_ao_dispatch_batch8_2026_08_06.md` + finalize twin
  (both `status: draft`). **Ledger**: 2 new parked findings, 2 entries written above — balanced.
- **context-scout 2026-08-06**: populated/refreshed context_scope (5 entries) — added the sibling
  `ag_closeout_linkage_baseline_regression_87_vs_69_2026_08_06.md` issue this same run filed (New finding 2 above),
  previously only in `related:`.
- **na-eligibility-audit 2026-08-06** (tranche=cefi, autonomous): KEEP-NA, valid — freshly filed today by the sibling
  `/ag-closeout-audit` skill; todo 1 is an explicit `[OPERATOR]` approval gate for 4 drafted satellite batches, todo 2
  is minor docs-linkage hygiene incidental to the doc's core purpose. No trap triggered; both items correctly remain
  open.
- **STANDING OPERATOR FLAG — 2026-08-11 (slot 28, `cefi_satellite_ao_dispatch_batch9_2026_08_07_finalize-002`)** — FIFTH
  consecutive no-change re-check (batch4→5→6→7→8) of the two carried `BLOCKED-OPERATOR-DECISION` items in this doc's
  "Carried forward" section. **Both STILL unresolved — direct operator attention required, not more automated
  re-triage** (batch8-finalize's standing instruction: five no-change re-checks is the flag-explicitly threshold). (a)
  `fail_hard_canonical_enforcement_design_2026_07_20.md`'s `[DESIGN] P1` "close the three §5 gaps" (line 156) is still
  `- [ ]` open — Schema v10 `instrument_id_form` backfill Stage 2 (a future batch10 candidate) stays blocked on it +
  Stage 1 write-enforce. **Needs the operator to run the §5 design session.** (b)
  `estate_orphan_assessment_2026_07_21.md` todo 6 cross-tranche boundedness (cefi+sports KEEP-NA vs defi RECLASSIFY,
  reverted) — the "Operator/next-toucher: rule on todo 6's boundedness, then flip deliberately" note (line ~558) is
  still present, unresolved. **Needs the operator to rule on todo 6's boundedness.** Until either gate clears or the
  operator decides, these two items will keep re-appearing in every future cefi batch finalize re-check. (Appended to an
  archived doc per [`cefi_satellite_ao_dispatch_batch9_2026_08_07_finalize.md`](/plans/archive/2026_08/cefi_satellite_ao_dispatch_batch9_2026_08_07_finalize.md) todo 2's explicit standing-flag
  instruction — status/verdicts left untouched.)
