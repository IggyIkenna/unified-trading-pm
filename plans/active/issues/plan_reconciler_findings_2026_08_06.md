---
doc_type: issue
title: Prediction-tranche /plan-reconcile run (2026-08-06, agt-65e60a) — findings + fixes
summary: >-
  Sharded plan_reconciler daily deep-reconciliation pass scoped to the `prediction` topic tranche (52-doc corpus: 17
  primary prediction plans, 27 issue docs, 8 cross-tagged with sports/cefi/defi/tradfi). Multi-agent fan-out DETECT
  (epic/topic/mechanical/missed-flip/AO-dispatch-readiness/zero-checkbox hunters) followed by adversarial VERIFY
  (independent refuter + confirmer per candidate) before any fix applied. This doc is both the run's progress journal
  and its human-readable report — updated incrementally as checkpoints land.
status: open
nature: issue
asset_group: [prediction]
stage: [meta]
scope: [engineer, admin]
repos: [unified-trading-pm]
tags: [prediction, plan-reconcile, plan_reconciler, contradiction, codex-alignment, audit, sharded]
related: [plans/active/prediction_consolidated_closeout_2026_07_18.md, cursor-configs/skills/plan-reconcile/SKILL.md]
created: 2026-08-06
parent_epic: predictions_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
source:
  'scheduled dispatch — POST /api/plan-health/dispatch {"mode": "reconcile", "tranche": "prediction"},
  dispatch_id=agt-65e60a'
locked_by:
drift_direction: advance-code
depends_on: []
resolved_by:
---

# Prediction-tranche plan_reconciler run — 2026-08-06 (agt-65e60a)

Scope: `asset_group` frontmatter containing `prediction` across `plans/active/*.md` + `plans/active/issues/*.md` (52
docs). Normative refs (`PLAN_FORMAT.md`/`task_template.md`/`INDEX.md`/`ACTIVE_INDEX.md`) and codex stay in scope per the
sharded-run contract. 17/52 docs are in the 12h GRACE WINDOW (read-only context this run, listed below) — newest git
change <12h old at run start (2026-08-06 20:33 UTC).

**Grace set (read-only this run):** ag_closeout_audit_rollout_2026_07_25.md,
issues/ag_closeout_audit_prediction_parked_2026_07_31.md,
issues/coverage_floor_registries_no_cross_propagation_2026_07_17.md,
issues/features_delta_one_dependency_checker_prediction_bucket_token_wrong_2026_07_27.md,
issues/instrument_availability_hive_migration_unrecognized_shapes_and_content_mismatch_2026_08_03.md,
issues/instrument_availability_league_and_question_group_partition_shapes_2026_08_03.md,
issues/instruments_docs_audit_outstanding_items_2026_07_08.md, issues/instruments_remaining_work_audit_2026_07_10.md,
issues/kalshi_execution_credential_secret_name_mismatch_2026_07_26.md,
issues/mtds_qg_red_uac_capability_declaration_drift_2026_08_05.md,
issues/prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md, prediction_consolidated_closeout_2026_07_18.md,
prediction_satellite_ao_dispatch_batch4_2026_07_26.md, prediction_satellite_ao_dispatch_batch6_2026_07_29.md,
prediction_satellite_ao_dispatch_batch7_2026_08_04.md, prediction_satellite_ao_dispatch_batch7_2026_08_04_finalize.md,
sports_predictions_live_mode_activation_readiness_2026_07_21.md.

**Corpus-wide mechanical hygiene checks (ref-paths/ag-closeout-linkage/terminal-status-archived/archive-candidates) were
run and checked for prediction-tranche hits: ZERO** — the 4 corpus-wide hard failures on today's sweep all land in other
tranches (verified by grep against each check's itemized output). This tranche's own hygiene contribution is clean;
findings below come from the contradiction/false-unchecked/zero-checkbox sweep phases instead.

## Flips verified

1. `issues/mdps_features_deadcode_consolidation_2026_07_20.md` todo 3 (S1-c, `mdps-sports-` registry gap) — HARD
   evidence: `deployment-service@c79f984` (dated 2026-07-20, same day as filing) registers `mdps-sports-` in both
   `vm_prefix_registry.py:364` and `launcher_registry.py:153`, exactly matching the fix spec. Verified live.

## Contradictions

1. **[ROUTED — BLK-c1db1b8d, FYI not a new question]**
   `issues/kalshi_execution_credential_secret_name_mismatch_2026_07_26.md` todo 2 mixes the 2026-08-06 operator ruling
   ("NO — do not touch the live exchange") with an older, superseded instruction to place a real order — genuinely
   confusing, same checkbox. Two sibling docs (`prediction_satellite_ao_dispatch_batch6_2026_07_29.md`,
   `prediction_consolidated_closeout_2026_07_18.md`) still describe this as an open A/B/C question. All 3 docs are GRACE
   (edited <12h ago) — could not fix this run. Independently confirmed by 2 hunters (contradiction-hunter +
   topic-hunter) before I re-verified via direct read.
2. **[FIXED]** `prediction_satellite_ao_dispatch_batch4_2026_07_26_finalize.md` — stale "draft — NOT dispatched" banner
   contradicted `status: active` frontmatter (predated the 2026-07-30 no-double-gate convention).
3. **[FIXED]** `data_pipeline_check_mdps_features_2026_07_20_finalize_2026_07_27.md` — same class of stale banner.
4. **[FIXED]** `issues/autonomous_session_operator_decisions_2026_07_25.md` entry #12 — resolution text was a copy-paste
   duplicate of entry #11's unrelated content (real-world fold outcome was already correct; only the audit-trail text
   was wrong).
5. **[REPORTED, no fix — policy question]** `predictions_other_bucket_and_ui_drilldown_2026_06_20.md` — 3 `[UI] P0`
   todos ticked `[x]` while each carries `[BLOCKED-PLAYWRIGHT]`, contradicting the doc's own stated playwright-gate
   rule. Mitigated by a 4th open todo tracking pw:L2 separately — looks like a deliberate "tick-on-ship,
   verify-separately" practice, not an oversight. Worth a policy clarification, not urgent.
6. **[REPORTED, GRACE, no fix]** `sports_predictions_live_mode_activation_readiness_2026_07_21.md:177-179` claims a
   "currently-open bug" (`sports_arb_dutching_engine_not_wired_to_factory_2026_07_21.md`) that is actually resolved and
   archived with hard sha evidence — the doc's own 2026-07-29 correction pass fixed 3 adjacent stale claims in the same
   section but missed this one.

## Doc-drift (codex)

All 3 routed via BLK-c1db1b8d (codex edits are never autonomous, per HARD GATE) — direction is codex-stale in all 3:

1. `/codex/02-data/prediction-data-types-catalog.md` + `/codex/02-data/mtds-data-source-coverage-matrix.md` say
   prediction has 3 data types / book-depth capture retired-no-replacement; contradicted by shipped `book_snapshot_5`
   (UAC@53bf01d6, live WS connectors both venues, 399,713+ rows).
2. `/codex/04-architecture/cross-venue-prediction-arb-detection.md` "Identity" section claims `af_fixture_id` already
   flows into the arb matcher; `prediction_phase_e_football_arb_live_2026_07_24.md`'s own still-open E3 todo is scoped
   to build exactly that (codex `last_reviewed` predates the plan's gap-finding trace by 1 day).
3. `/codex/09-strategy/operational/prediction-markets-codification-gaps.md` gaps G5/G7 look closed given production
   evidence — lower confidence, recommended a direct code-verification pass before any edit.

## Hygiene fixes

1. `prediction_phase_e_football_arb_live_2026_07_24.md:126` — extra unmatched closing paren.
2. `prediction_live_clob_depth_capture_2026_07_24.md` — `repos:` frontmatter: added market-tick-data-service (57
   mentions)/unified-api-contracts (9)/instruments-service (19), dropped fund-administration-service (0 body mentions,
   frontmatter-only — copy-paste artifact).
3. `issues/candle_feature_canonical_path_divergence_2026_07_20.md:311` — dangling ref repointed to archived path; also
   fixed stale "pending P7" prose (P6-P8 confirmed CLOSED 2026-07-23).
4. `issues/mtds_is_full_adapter_smoketest_findings_2026_07_07.md:409` — non-standard `[~]` marker → `[ ]` with PARTIAL
   prefix preserved.
5. `issues/mtds_pipeline_check_process_killed_during_skip_leg_poll_2026_08_06.md` — zero-checkbox doc, added 3 tracked
   todos for the genuine open P1 infra defect (host process-kill investigation).
6. 3× stale `related:` path repointed to the archived orphaned-issue doc
   (`sports_arb_decay_window_and_alpha_gate_design`, `sports_group_c_execution_backtest_harness`,
   `sports_odds_feature_naming_canonicalization`).
7. `prediction_phase_ab_residuals_2026_07_24.md` §A3 — fixed ~250-space indentation defect (was rendering as an
   unintended markdown code block); a sibling instance in a different file had already been fixed by a prior pass.
8. `issues/mdps_features_deadcode_consolidation_2026_07_20.md` todo 2 — reframed stale "pending operator A/B/C" to point
   at the 2 real still-open follow-up docs (option B was already chosen + substantially executed).
9. `issues/sports_odds_feature_naming_four_way_mismatch_2026_07_21.md` todo 3 — re-scoped: sibling migration is ~80%
   landed (8/9 done across 3 repos, independently re-verified), not "unstarted" as 4 prior audit passes concluded (their
   `SportsFeatureVector` class-name grep false-negatived — migration used field names, not a class import). Genuine
   residual found: `strategy-service/.../event_settled.py` still uses old `decimal_odds_` naming.
10. `issues/mtds_available_at_cross_asset_backfill_line_cap_remediation_2026_07_31.md` todo 2 — flagged very-likely MOOT
    (target plan archived+complete 16/16 since 2026-08-05, without the sequencing this todo asked for).
11. `prediction_cross_venue_arb_and_coverage_2026_07_24.md:606-616` — split the bundled lowercase-kalshi + blank/UNKNOWN
    todo: lowercase-kalshi portion already purged 2026-07-11 (13 days before this doc existed, carried forward verbatim
    from the pre-split parent); blank/UNKNOWN stays open, downgraded P2→P3.
12. `data_completion_prediction_2026_07_15.md` — 4 stale P0/P1 checkboxes (C0 bundled walk + 2 riders + post-walk)
    annotated SUPERSEDED by the doc's own later "Plan A object-layer migration" section (which explicitly says it
    supersedes them, confirms legacy buckets 404/gone); also corrected that section's Codex SSOTs citation (was pointing
    at a stale table row + a nonexistent section title).

## Filed

1. `issues/sports_odds_ready_dead_pubsub_trigger_2026_08_06.md` (NEW, P0) — extracted from a GRACE doc's finding D7
   (`instruments_docs_audit_outstanding_items_2026_07_08.md`), which had it as untracked prose invisible to 4 prior
   na-eligibility-audit passes over its lone meta-checkbox. Live sports odds capture unblocked 2026-07-29
   (`odds-api-key` rotated) — this dead Pub/Sub trigger means live sports feature computation will silently never fire
   once capture starts, no crash/alert.
2. `BLK-c1db1b8d` — operator alert (see Doc-drift + Contradictions #1 above); `can_continue: true`, rest of run
   proceeded.

**GRACE-blocked findings, filed here for the next non-grace pass** (cannot fix this run, doc edited <12h ago):

- `issues/instrument_availability_league_and_question_group_partition_shapes_2026_08_03.md` todo 5 — HARD-evidenced
  missed-flip (the doc's OWN todo 1 already declares todo 5 moot) — flip `[x]` next pass, would make the doc a genuine
  archive candidate.
- `issues/mtds_qg_red_uac_capability_declaration_drift_2026_08_05.md:138` — zero-checkbox mis-escape (a real todo is
  wrapped inside a backtick code-span, breaking `- [ ]` line-start matching — confirmed isolated to this one doc, not a
  corpus-wide pattern). Genuine remaining work verified live still needed (AAVE `rewards` seed/capability cleanup, 8
  chain entries). Canonical todo text drafted by hunter, ready to paste in.
- `prediction_satellite_ao_dispatch_batch4_2026_07_26.md:690` — a fully-scoped, gated todo ("4b-iii") sits as prose
  inside `## Progress Log`, never promoted to a real checkbox — structurally invisible to backlog derivation.
- `prediction_satellite_ao_dispatch_batch6_2026_07_29.md:103-106` — banner factually wrong about sibling
  `batch6_finalize`'s status (says draft, sibling is actually active).
- `prediction_consolidated_closeout_2026_07_18.md` — stale child open-counts (phase_ab cited as "13 open," live is 7;
  capture_incident_remediation cited as "9 open," live is 8) + a "Deferred work" section with ~6 prose bullets, no
  checkboxes (needs verification each is tracked elsewhere — the "E2 alias additions" bullet's relationship to batch6's
  alias-table todo isn't explicitly cross-cited).
- `issues/prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md` — trailing note contradicts the todo
  immediately above it in the same doc; sole open todo lacks an explicit done-when criterion.
- `issues/instruments_remaining_work_audit_2026_07_10.md` — 4 confirmed prettier-mangling instances
  (underscore→asterisk, the documented bare-`npx prettier`<3.9.5 failure mode) at lines 675/676/707/807.
- **Informational only, no fix needed**: `gate_on_depends` reliability risk affects prediction's batch4/6/7 finalize
  docs too, but the root-cause bug is already tracked cross-tranche in
  `gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25.md` (status: open) — not re-filed.

## Archive candidates (operator review)

None this run — every near-zero-open-todo doc found was either GRACE-blocked (see Filed) or, on verification, still had
genuine open work.

## Refuted (dropped by verify)

1. **"Checkbox-under-`## Follow-ups`-not-`## Todos` = invisible to AO dispatch"** (hunter concern re:
   `coverage_floor_registries_no_cross_propagation_2026_07_17.md` +
   `features_delta_one_dependency_checker_prediction_bucket_token_wrong_2026_07_27.md`) — REFUTED by direct read of
   `agent-orchestrator/server/regen_backlog_from_plan.py::_parse_open_todos`: it scans every non-frontmatter,
   non-code-block line of the WHOLE document for the unchecked-checkbox pattern, with no heading-based section scoping.
   Both docs' checkboxes ARE visible to the dispatcher.
2. **`prediction_phase_e_football_arb_live_2026_07_24.md` E1 "Kalshi has none today" possible-stale-premise** —
   low-confidence hunter flag, not independently confirmed either way; left as reported-only, no action.
3. **`sports_predictions_live_mode_activation_readiness_2026_07_21.md:266-272` vs `prediction_phase_e...` "3-venue PAPER
   arb shipped" claim** — plausibly different things (component-level proof vs. formal strategy-tier promotion); not
   confirmed as a real contradiction.

## Coverage (hunters / batches / docs)

- **9 hunters** dispatched in parallel (≤10 cap): 7 epic-cluster/content hunters (partitioned to cover all 52 corpus
  docs, verified exact non-overlapping union match against the corpus list before dispatch) + 1 codex-alignment hunter
  (9 plans checked against their cited codex docs) + 1 cross-cutting topic hunter (6 themes swept across the full 52-doc
  list).
- **52/52 docs read in full** by exactly one epic-cluster hunter each (17 grace read-only, 35 non-grace).
- **Verified confirmed**: 19 (11 mechanical fixes applied directly by the orchestrator after independent
  re-verification, not just trusting hunter prose — every fix above was re-derived via direct `grep`/`Read`/git-log
  before editing) + 3 codex-drift findings routed + 1 new issue doc filed + several GRACE-blocked findings filed for
  next pass.
- **Verified refuted**: 3 (see above).

## Plans not reached

None — full 52-doc coverage achieved this run.
