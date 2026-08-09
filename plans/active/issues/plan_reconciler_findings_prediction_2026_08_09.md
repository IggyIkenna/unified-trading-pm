---
doc_type: issue
title: "plan_reconciler daily deep reconciliation run — prediction tranche, 2026-08-09"
summary: >-
  Run-findings doc for plan_reconciler dispatch agt-c3a27f (slot 13, 2026-08-09), sharded to the `prediction`
  asset_group tranche per the 2026-08-06 sharded-dispatch ruling. Corpus: 30 active plans (~11.3K lines) + 24 issue docs
  (~8.8K lines) tagged asset_group containing `prediction` (~1.84MB), plus the `predictions_master` epic hub (1071
  lines) and the normative refs. 9 of 54 docs are in the 12h grace window and read-only this run. Filename carries the
  tranche (deviating from the role file's bare `<TODAY>` pattern) because 4+ sibling slots were observed running
  concurrent tranche shards at run start, making a same-day bare-date filename a live collision risk.
status: open
nature: issue
asset_group: [prediction]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, reconciliation, plan-hygiene, findings, scheduled, prediction]
related: []
created: "2026-08-09"
parent_epic: predictions_master
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
source: "slot 13, plan_reconciler agt-c3a27f, 2026-08-09"
context_scope:
  [
    unified-trading-pm/scripts/plan-hygiene/run_hygiene_sweep.sh,
    unified-trading-pm/agents/plan_reconciler.md,
    unified-trading-pm/cursor-configs/skills/plan-reconcile/SKILL.md,
    unified-trading-pm/plans/epics/predictions_master.md,
  ]
drift_direction: advance-code
depends_on: []
---

# plan_reconciler run — 2026-08-09 (agt-c3a27f, tranche=prediction)

## Scope + method

- `TRANCHE=prediction` supplied → sharded run per the 2026-08-06 ruling (SKILL.md § "Topic-scoped (sharded) runs").
  Filter: `asset_group:` frontmatter containing `prediction` across `plans/active/*.md` + `plans/active/issues/*.md`,
  plus the `predictions_master` epic hub. Normative refs (`PLAN_FORMAT.md`/`task_template.md`/`INDEX.md`/
  `ACTIVE_INDEX.md`) + codex stay in scope per the skill's corpus-wide-policy carve-out.
- Corpus: 30 active plans + 24 issue docs = 54 docs (~1.84MB) + 1 epic hub (97KB). Several docs are dual-tagged
  `[sports, prediction]` (shared with `sports_master`) — read in full but archival on those needs the cross-tranche
  check (SKILL.md § "Archival caution in a topic-scoped run"). `ag_closeout_audit_rollout_2026_07_25.md` is tagged 6
  asset groups (genuinely cross-cutting rollout doc) — read as CONTEXT only, not primary-owned by this shard.
- Grace set (newest commit <12h old at run start, 2026-08-09 02:38 UTC): 9 of 54 docs (17%). Read-only context this run:
  `sports_odds_feature_naming_canonicalization_2026_07_21.md`,
  `issues/backfill_smoke_write_path_canonical_audit_2026_07_20.md`,
  `predictions_other_bucket_and_ui_drilldown_2026_06_20.md`,
  `backfill_smoke_write_path_canonical_audit_finalize_2026_08_08.md`,
  `issues/mtds_pipeline_check_process_killed_during_skip_leg_poll_2026_08_06.md`,
  `mtds_pipeline_check_process_killed_during_skip_leg_poll_2026_08_06_finalize_2026_08_08.md`,
  `prediction_satellite_ao_dispatch_batch9_2026_08_09.md`, `prediction_cross_venue_arb_and_coverage_2026_07_24.md`,
  `prediction_satellite_ao_dispatch_batch9_2026_08_09_finalize.md`.
- Non-grace actionable set: 45 active+issue docs + 1 epic hub.
- Concurrency note: at run start, 4+ sibling slots (8, 9, 14, 26) were observed running hygiene sweeps concurrently —
  consistent with the weekly per-tranche sharded cadence (other tranches dispatched the same day). This run touches ONLY
  `prediction`-tagged docs; no overlap expected, but the findings-doc filename was disambiguated with the tranche name
  to avoid a same-day collision (see summary).

## Flips verified

1. **`sports_odds_feature_naming_four_way_mismatch_2026_07_21.md` todo 3** — "the four-way naming migration has not
   started" was stale since 2026-07-23 and survived 5 audit re-triage passes (07-23/25, 07-30, 08-01, 08-06) without any
   of them re-checking the target doc. Actual state: 8/9 done across 4 repos (real, live-verified shipped commits).
   Adversarially verified (refuter + confirmer, both COULD NOT REFUTE, independently re-verified 7-9 SHAs each).
   `unified-trading-pm@508466382`'s ancestor commit chain, see `56af1cf65`.
2. **`honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md`** — phantom `OPTION` removal from bare
   `OKX`/`OKX_FUTURES`, shipped `unified-api-contracts@d67a226fc` 2026-08-04, verified live in `venue_constants.py`
   (self-verified via git + direct code read, HARD evidence). Survived a 2026-08-07 audit pass 3 days after shipping.
   `unified-trading-pm@a1b2f4523`.

## Contradictions

1. **[FIXED] `prediction_consolidated_closeout_2026_07_18.md` Ground-truth verdict table, 3 rows + Conclusion.**
   Instrument-id canonical shape ("partial 4/8" → actually 8/8 done), Kalshi fixture-linking ("NONE" → ~100% on 92
   fixtures), Polymarket fixture-linking ("string bridge only" → real numeric `af_fixture_id`) — all stale against
   later-shipped Phase A-B/E work, none carried the table's own "A0 live read" correction marker. Adversarially verified
   (refuter + confirmer, both COULD NOT REFUTE all 3 rows). `56af1cf65`.
2. **[FIXED] `prediction_phase_e_football_arb_live_2026_07_24.md` E1 vs E2 same-document self-contradiction.** E1 (open)
   said Kalshi resolution "has none today" while E2 (done, directly below) shipped it. Narrowed E1 to its
   genuinely-remaining scope (a live 3-way cross-venue consistency MEASUREMENT, not yet run anywhere) rather than
   closing it — confirmed by both refuter and confirmer as a real, distinct residual. `56af1cf65`.
3. **[FIXED, P0 safety-relevant] `prediction_satellite_ao_dispatch_batch6_2026_07_29.md` todo 5.** Still posed "place a
   real order on the live Kalshi exchange" as an open operator-answerable question, 3 days after
   `kalshi_execution_credential_secret_name_mismatch_2026_07_26.md` recorded an explicit "NO — do not touch the live
   exchange" ruling (2026-08-06). Double-confirmed by 2 independent hunters (batch4 + batch6) AND a dedicated
   refuter+confirmer pair — all 4 independently found the same gap via git archaeology (a prior plan_reconciler
   review-branch attempt never landed on `live-defi-rollout`). `56af1cf65`.
4. **[FIXED] `sports_group_c_execution_backtest_harness_2026_07_21.md` Todo 5 (+ finalize Todo 2).** `docs/BACKTESTS.md`
   claimed dead in execution-service; actually lives in strategy-service, current, already covers sports, and documents
   a different backtest surface (Group-B) than this todo's actual target (Group-C). Root cause: an archived
   investigation conflated two separate facts. Adversarially verified (refuter + confirmer, both COULD NOT REFUTE).
   `2232c994a`.
5. **[FIXED] `prediction_satellite_ao_dispatch_batch4_2026_07_26.md` (+finalize) banner staleness.** Both docs' body
   banners said "Status: draft — NOT dispatched" contradicting `status: active` frontmatter and extensive shipped
   history. Self-verified mechanically (frontmatter grep). `2232c994a`.
6. **[FIXED] `prediction_satellite_ao_dispatch_batch4_2026_07_26_finalize.md` todo 3 stale count.** "3 A3-relocated
   sibling docs" — 1 (`prediction_perps_kalshi_polymarket_parked`) was already archived at this doc's own 2026-07-26
   drafting. Corrected to 2 genuinely-active docs. `2232c994a`.
7. **[FIXED] `mtds_is_full_adapter_smoketest_findings_2026_07_07.md` MARGINFI/SOLEND self-contradiction.** Open Question
   §4 said "no reference-data adapter of any kind"; the doc's own later 2026-07-12 finding confirms adapters work (root
   cause was an unmaintained venue-prefix registry, fixed `unified-api-contracts@0250892d`). `a1b2f4523`.
8. **[FIXED] `ag_closeout_audit_prediction_parked_2026_07_31.md` Finding 1 stale status.** Both named dead-code docs got
   a 2026-08-07 operator delete ruling, but self-verified live that NEITHER deletion has executed yet — updated the
   framing to reflect ruled-but-not-executed rather than still-awaiting-a-ruling. `508466382`.
9. **[CORRECTED-FALSE-POSITIVE] `autonomous_session_operator_decisions_2026_07_25.md` entry 24.** A hunter flagged this
   as a stale prose deferral needing conversion to a tracked todo (trigger date passed 13 days ago). Independent
   re-verification found the target plan (`ao_fleet_observability_kpis_2026_07_20.md`) is actually `status: complete`
   and archived — the work shipped, just never linked back. Closed the loop instead of creating an unnecessary todo.
   `508466382`.
10. **[FLAGGED, routed to operator — BLK-8f289fba]** Instrument-ID convention drift ACROSS 2 codex docs themselves
    (`prediction-markets.md`'s self-flagged-unresolved `{VENUE}:{MARKET_TYPE}:{EVENT_SLUG}@{OUTCOME}` vs
    `prediction-schema-paths.md`'s `POLYMARKET::UP_DOWN::{ASSET}::{TF}::{WINDOW_END_TS}`), neither matching live
    `canonical_instrument_id` samples. Never edited codex without a ruling.
11. **[FLAGGED, routed to operator — BLK-8f289fba]** Both prediction codex docs' Kalshi "BLOCKED-CREDENTIALS" framing
    (`last_reviewed: 2026-05-22`) reads stale — live capture has run through `day=2026-07-27`; the real residual gate is
    the live-order-verification ruling (contradiction #3 above), not a credentials absence.
12. **[FLAGGED, not fixed — informational]** `/codex/04-architecture/cross-venue-prediction-arb-detection.md`'s
    "Standing caveats" item 5 (producer trades-mislabel, framed as still-open) was fixed 7 weeks ago
    (`market-tick-data-service@ef01a055`, 2026-06-24) per `prediction_cross_venue_arb_and_coverage_2026_07_24.md`'s own
    todo. Lower-priority than #10/#11 (a single stale caveat, not a 3-way format conflict) — noted here for a future
    codex-alignment pass rather than a separate blocked-question.

## Doc-drift

See Contradictions #10-#12 above (all codex-related). No codex edits were made this run (never autonomous per the role's
HARD RULE) — both routed via BLK-8f289fba.

## Hygiene fixes

1. `prediction_satellite_ao_dispatch_batch4_2026_07_26.md` — converted a bare Progress Log bullet (4b-iii, real
   gate-cleared work) into a proper `- [ ]` checkbox; was invisible to `regen_backlog_from_plan.py`. `2232c994a`.
2. `prediction_satellite_ao_dispatch_batch6_2026_07_29.md` — added the missing `sequential: false` frontmatter field
   (only batch generation lacking it among 5); corrected todo 1's evidence SHA (cited sha only on an abandoned branch,
   live equivalent is a different-hash rehash of the same content). `3c54c9d2c`.
3. `mtds_qg_red_uac_capability_declaration_drift_2026_08_05.md` — reformatted a todo that was wrapped entirely in one
   backtick code span (`` - `- [ ] ...` ``), invisible to any checkbox scanner; fixed 2 bare-slug `related:` refs + a
   stray-space-broken codex path. `a1b2f4523`.
4. `sports_odds_feature_naming_four_way_mismatch_2026_07_21.md` — set `archive_exempt: true` with justification after
   the todo-3 flip left it at 0 open todos; NOT archived because it's a cross-tranche shared `[sports, prediction]` doc
   referenced by sports-tranche docs (`sports_satellite_ao_dispatch_batch10_2026_08_06.md`,
   `sports_consolidated_native_ao_extract_2026_07_25.md`) — a single-tranche shard must not archive it unilaterally per
   SKILL.md's archival-caution rule and the standing
   `na_audit_multi_tranche_shared_doc_ownership_and_draft_p0_park_2026_07_30.md` finding naming this exact doc.
   `56af1cf65`.
5. Whitespace-corruption cleanup (cosmetic, bundled with content fixes, not separately committed): `~300`
   stray-leading-space continuation lines in `prediction_satellite_ao_dispatch_batch6_2026_07_29.md` todo 5.

## Filed

- **BLK-0d9d2799** — where should 2 fully-shipped, gate-cleared prediction data items (combined `_index` manifest
  canonicalisation walk; POLYMARKET re-enum + `book_snapshot_5` backfill) land? Both promoted ready 2026-08-07,
  unclaimed by any batch 6-9. Recommendation: A (fold into a future batch10).
- **BLK-8f289fba** — 2 codex-alignment findings needing an operator ruling before any SSOT edit (see Contradictions
  #10-#11). Recommendation: B (park for a dedicated codex-alignment pass).

## Archive candidates (operator review)

- **`sports_odds_feature_naming_four_way_mismatch_2026_07_21.md`** — reached 0 open todos this run (flip #1 above) but
  is cross-tranche shared; marked `archive_exempt: true` rather than archived. `locked: false`. Genuine archive
  candidate for a future `all` pass or joint sports+prediction coordination once referrers are swept on both sides.

## Refuted (dropped by verify)

None. All 8 adversarial verification sub-agents (4 refuter+confirmer pairs, covering the Kalshi stale-text finding, the
closeout-table + phase_e self-contradiction pair, the sports-odds-naming MAJOR finding, and the BACKTESTS.md wrong-repo
claim) returned COULD-NOT-REFUTE / CONFIRMED on every topic — nothing surfaced by the hunters was knocked down by
adversarial review this run.

## Coverage (hunters / batches / docs)

- **Corpus**: 58 prediction-tranche docs (1 epic hub + 26 active plans + 31 issue docs, `asset_group` containing
  `prediction`) — corrected up from an initial naive-grep count of 55 after discovering multi-line `asset_group:` YAML
  arrays aren't caught by a single-line grep (a Python frontmatter parser found 3 more docs, incl.
  `sports_manifest_consolidator_zero_growth_stall_2026_07_29.md`).
- **STEP 3 (DETECT)**: 9 read-only hunter sub-agents, 1 per batch, every doc read in full by exactly one hunter (9
  grace-protected docs read as context only, no fixes proposed against them). Full multi-checklist duty per hunter:
  contradictions, missed-flips, AO-dispatch-readiness, hedge-pointers, zero-checkbox sweep, prose/structural integrity,
  codex-alignment.
- **STEP 4 (VERIFY)**: 8 adversarial sub-agents (4 refuter+confirmer pairs) for the highest-stakes P0/P1/MAJOR findings;
  4 additional findings self-verified via direct git/grep (mechanical, provable-from-filesystem facts per the skill's
  own calibration guidance — auto-resolve, don't escalate to a full adversarial pair).
- **Total findings surfaced**: ~75-85 across all categories (see hunter reports in this run's transcript); triaged into
  ~10 Tier-A (P0/P1/MAJOR) + ~49 Tier-B (P2 mechanical/contradiction) + an unquantified Tier-C (P3 cosmetic: typos,
  whitespace, minor citation drift).
- **Applied this run**: 9 flips/contradiction-fixes + 5 hygiene fixes = 14 edits across 10 files, 5 commits (+1 doc-open
  commit), all pushed to `plan_reconciler/agt-c3a27f`.
- **Routed**: 2 blocked-questions (BLK-0d9d2799, BLK-8f289fba) covering 3 distinct findings needing operator authority.
- **verified_confirmed**: 8 (Kalshi, closeout-table×3-rows+conclusion treated as 1 verified cluster, phase_e
  self-contradiction, sports-odds-naming, BACKTESTS.md — 4 topics × refuter+confirmer = 8 agent verdicts, all
  confirming). **verified_refuted**: 0.

## Plans not reached

Given the corpus scale (58 docs, ~80 findings), this run prioritized the P0/P1/MAJOR findings + a representative slice
of P2 mechanical fixes over exhaustively applying every Tier-B/C item. **Not applied this run** (tracked here, not
silently dropped):

- **Grace-protected findings** (cannot edit until the 12h window expires on each doc; re-check in the next non-grace
  pass): line-cap breach on `prediction_cross_venue_arb_and_coverage_2026_07_24.md` (1009/1000 lines, batch8's own
  fix-todo still open); a likely-ready missed-flip at that same doc's line 380 (fixture-pairing residual — its stated
  blocker, batch6's team-name-alias todo, shipped 2026-08-05); a missing-checkbox-marker defect in that same doc (2
  EXTRACTED bullets, lines ~702/764); a missing-checkbox-marker defect in
  `sports_odds_feature_naming_canonicalization_2026_07_21.md` (todo 9, line ~197); that same doc's un-fulfilled promised
  codex SSOT note; batch9's conflict-check miscategorization (should cite category-4 stale-checkbox, not category-3
  conflict) in `prediction_satellite_ao_dispatch_batch9_2026_08_09.md`.
- **Remaining Tier-B mechanical findings** (~35 items, mostly stale `related:`/`context_scope` path pointers to archived
  docs, minor line-citation drift, `../`-relative-path format violations in pre-migration docs, last_updated staleness)
  across: `prediction_capture_incident_remediation_2026_07_06.md`, `predictions_ml_walk_forward_and_arb`,
  `sports_predictions_live_mode_activation_readiness`, `sports_group_c_execution_backtest_harness` (3 more stale
  `related:` pointers beyond the BACKTESTS.md fix), `data_pipeline_check_mdps_features_2026_07_20` (3 `../`-relative
  refs), `instruments_docs_audit_outstanding_items_2026_07_08` (4 genuinely-stale archived-target paths of 15 checked),
  `mdps_features_deadcode_consolidation_2026_07_20` (declassification-vs-todo-text self-contradiction),
  `ml_training_and_prediction_pipeline_launchers_stale_post_consolidation_2026_08_04` (stale cross-ref), and several
  na-eligibility-audit miscounts (`coverage_floor_registries_no_cross_propagation_2026_07_17`).
- **Recurring corpus-hygiene patterns observed but not corpus-wide-swept** (documented for a future dedicated pass, not
  this shard's remit): (a) missing-checkbox-marker on "EXTRACTED"/Progress-Log bullets — 5 confirmed instances in this
  tranche alone (2 fixed: batch4's 4b-iii, mtds_qg_red_uac's backtick-wrapped todo; 3 grace-blocked); (b)
  non-leading-slash `related:` refs silently escaping the archival-repoint automation (batch8's systemic root-cause
  finding — explains many of the stale-path items above at once); (c) audit passes (na-eligibility-audit, context-scout,
  RE-TRIAGE) repeatedly re-stamping "unchanged" without re-checking the referenced target doc — root cause of the
  sports-odds-naming 5-cycle-survival finding and a contributing factor elsewhere.

Every item above is either grace-protected (will surface again on the next prediction-tranche run once the window
expires) or was surfaced by a hunter this run and is recoverable from the hunter transcripts in this dispatch's history
— nothing is silently lost.
