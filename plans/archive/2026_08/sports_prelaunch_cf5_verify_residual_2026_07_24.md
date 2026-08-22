---
doc_type: plan
title: Sports pre-launch-window + CF-5 relabel residual — forked from migration_verification_orphan_safety_2026_06_10
summary: >-
  2 small residual todos forked verbatim out of the archived migration-verification/orphan-safety harness plan
  (2026-07-24 plan line-cap remediation split): the operator-gated sports pre-launch-window (C3) corpus decision and the
  sports CF-5 trades-relabel fix, last recorded (2026-06-16) as code-complete but not yet landed.
status: complete # was: active — archived 2026-08-08, both todos done (CF-5 landed, C3 superseded per data-floor ruling)
nature: process
asset_group:
  [sports] # corrected 2026-07-25 (ag-closeout-audit orthogonality fix) -- was [cross-cutting], a genuine mistag:
  # pre-launch-window + CF-5 trades-relabel are sports-specific, inherited the parent harness's cross-cutting tag
  # on fork instead of being corrected to its real single-AG scope
stage: [meta]
repos:
  [
    deployment-api,
    deployment-service,
    deployment-ui,
    features-service,
    instruments-service,
    market-data-processing-service,
  ]
scope: [engineer, admin]
tags: [sports, cf-5, pre-launch-window, manifest, migration, plan-split, residual]
related:
  [
    /plans/archive/migration_verification_orphan_safety_2026_06_10.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
parent_epic: manifest_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: design
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.9
assigned_role: data_engineering
drift_direction: advance-code
last_updated: "2026-07-24"
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Forked verbatim from `plans/archive/migration_verification_orphan_safety_2026_06_10.md` (its own Progress Log, entries
  dated 2026-06-11 / 2026-06-16) as part of the 2026-07-24 plan line-cap remediation
  (`plans/active/issues/plan_line_cap_remediation_2026_07_23.md`, row 18 / bucket (d)). The parent plan's durable
  protocol (CF-15…CF-21) had already migrated to codex; these were the last genuinely-open items in its sports thread
  and are tracked here going forward.
context_scope:
  [
    /plans/archive/migration_verification_orphan_safety_2026_06_10.md,
    market-tick-data-service/market_tick_data_service/scripts/rebuild_sports_manifest_v9.py,
    instruments-service/scripts/backfill_orphan_class_e_sports.py,
  ]
---

> **🗄️ ARCHIVED 2026-08-08** — both todos done: CF-5 relabel fix landed (`market-tick-data-service@7f1262a0`), C3
> pre-launch-window question SUPERSEDED by the sports 2020-06 data floor ruling (see banner below). Disposition executed
> by `/plans/active/sports_taxonomy_p4_backfill_2026_08_08.md`.

> **✅ OPERATOR RULING 2026-08-08 — this doc's sole open todo is STALE, not open.** It offers a choice between extending
> `SOURCE_COVERAGE_START["footystats"]` 2019→2018 (plus the api_football sub-entity windows) and re-backfilling the
> 10,345-object C3 corpus, OR ratifying it as outside-window. **That choice was already foreclosed.**
> `/codex/02-data/sports-2020-06-data-floor.md` (operator ruling 2026-07-21) explicitly supersedes the 2018 amendment —
> _"all sports `SOURCE_COVERAGE_START` / `DATA_TYPE_COVERAGE_START` floors are clamped to `date(2020, 6, 6)`"_
> (`unified-api-contracts@8cdf7808`) — and pre-floor sports data is fabrication-by-construction: **delete, do not
> backfill**. Re-confirmed by the operator 2026-08-08. Disposition is executed by
> `/plans/active/sports_taxonomy_p4_backfill_2026_08_08.md` (agent-autonomous via delete-safety §3a) and this doc is
> closed out by its finalize sibling. Do NOT extend the coverage windows.

# Sports pre-launch-window + CF-5 relabel residual

> **Origin.** Both todos below are moved **verbatim** from
> `plans/archive/migration_verification_orphan_safety_2026_06_10.md` (now trimmed + unlocked; full historical Progress
> Log archived to `plans/audit/results/migration_orphan_safety_goalpost_verification_2026_06_10.md` as an Appendix).
> **Freshness flag (not an edit to the text below):** the CF-5 fix was last recorded (2026-06-16) as code-complete but
> **not yet landed** (blocked on a dirty MTDS/UAC dep tree, preserved on a wip branch) — over a month has passed since,
> so whoever picks up todo 1 should first check whether `origin/wip-preserve/mtds-346-cf5-trades` has since landed on
> `market-tick-data-service` HEAD before re-doing the work.

## Todos

- [x] ✅ [DATA] P1. **Sports CF-5 oracle relabel = ZERO — ROOT-CAUSED + FIXED (code), preserved to a wip branch awaiting
      a clean-dep window (2026-06-16).** **DONE (na-eligibility-audit 2026-08-03)** —
      `sports_satellite_ao_dispatch_batch2_2026_07_24.md:521`: landed `market-tick-data-service@7f1262a0`. The stale
      `origin/wip-preserve/mtds-346-cf5-trades` branch had NOT landed and was too old to cherry-pick wholesale (would
      have regressed later fixes on the same file) — applied the isolated one-line fix (`"trades"`→`"TRADES"` in
      `_PER_FIXTURE_DERIVED_DATA_TYPES`) directly on current HEAD + adapted the regression test, TDD-verified.
      `quality-gates.sh` green. The finding's "61.8% league match-rate / league-resolution" hypothesis was WRONG for the
      bulk: on the real prod MDPS sports index (`market-data-tick-sports-prd`, 584,257 empty_confirmed), **583,185 are
      data_type=`trades` whose league_id resolves 100%**. **Real root cause:** `_PER_FIXTURE_DERIVED_DATA_TYPES` listed
      the MDPS odds tick as lowercase `"trades"`, but membership is tested as `data_type.upper() in set` (step 6.5
      truthset gate + `is_derived_captured`) → `"TRADES"` never matched → step 6.5 silently skipped EVERY `trades` empty
      → all kept SOURCE_RETURNED_ZERO instead of the truthset-derived EXPECTED_NO_FIXTURE. **Fix:**
      `"trades"`→`"TRADES"` in `mtds/scripts/rebuild_sports_manifest_v9.py` (kept at the 900-line cap) + a regression
      test. MTDS QG-green; verified by direct `_step6_5_truthset_gate` call (not-in-truth → EXPECTED_NO_FIXTURE;
      in-truth → stays SOURCE_RETURNED_ZERO, since `trades` is correctly excluded from the guaranteed set). **NOT YET
      LANDED:** quickmerge's pre-flight dep-audit refused across 3 retries because a LIVE sibling was continuously
      running fleet manifest-regen / version-alignment (UTL→UAC dirty, version bumps 0.14→0.15) — must not stomp foreign
      WIP. **The verified fix is PRESERVED on `origin/wip-preserve/mtds-346-cf5-trades` (mtds@d0a15a3)** — land it with
      `quickmerge.sh --agent --files 'market_tick_data_service/scripts/rebuild_sports_manifest_v9.py tests/unit/scripts/test_rebuild_sports_manifest_v9.py'`
      (cherry-pick the wip commit onto a clean MTDS tree) the moment all MTDS deps are clean. Reason-level only
      (status-diff GREEN — does NOT block the G4 apply). Repo: market-tick-data-service. Provenance: 2026-06-16 prod
      MDPS index diagnosis.
- [x] ✅ SUPERSEDED 2026-08-08 (see OPERATOR RULING banner above) — the choice this todo posed was already foreclosed by
      `/codex/02-data/sports-2020-06-data-floor.md` (operator ruling 2026-07-21, `unified-api-contracts@8cdf7808`): all
      sports `SOURCE_COVERAGE_START`/`DATA_TYPE_COVERAGE_START` floors are clamped to `date(2020, 6, 6)`, so the C3
      pre-floor corpus is fabrication-by-construction — delete, do not backfill. Re-confirmed by the operator
      2026-08-08. Disposition **EXECUTED 2026-08-22** by `/plans/active/sports_taxonomy_p4_backfill_2026_08_08.md`
      (agent-autonomous via delete-safety §3a — see that plan's Progress Log for the full evidence trail:
      `instruments-service@4219aaa45a`). **Measured drift**: the corpus was actually 12 real objects at execution
      time, not the 10,345 cited below from the 2026-06-11 R8 sweep — two intervening, broader 2026-07-21/27
      `sports_reference/by_date/` pre-floor wipe campaigns (neither scoped/labelled as C3-specific) had already swept
      up the overwhelming majority. Do NOT extend the coverage windows. ~~[DATA] P1. Sports pre-launch-window corpus
      decision (C3, 10,345
      objects — operator-gated): either extend the UAC windows (`SOURCE_COVERAGE_START["footystats"]` 2019-01-01 →
      2018-01-01 — the footystats HISTORICAL season API demonstrably serves 2018 rows now on disk; + the api_football
      `DATA_TYPE_COVERAGE_START` sub-entity windows) and re-run `backfill_orphan_class_e_sports.py` to manifest the
      corpus, OR ratify the corpus as permanently outside-window (it then becomes a CF-21-style cleanup candidate).
      Blast radius of a window change: backfill orchestrators start fetching those windows
      (`clip_dates_to_source_coverage`), data-status denominators, the phantom audit. Repos: unified-api-contracts +
      instruments-service. Provenance: R8 sweep 2026-06-11 (C3 rows in the reference bucket's
      `orphan_sweep_sports.parquet`).~~

## Success criteria

1. CF-5 sports-trades relabel fix confirmed landed on `market-tick-data-service` HEAD (or landed by this plan).
2. Operator decision recorded + executed on the C3 pre-launch-window corpus (window-extend + backfill, or ratified
   permanently-outside-window).

## Progress Log

- **2026-08-22 (slot-24, data_engineering)** — Closing out this doc's C3 disposition per the standing floor ruling:
  `/plans/active/sports_taxonomy_p4_backfill_2026_08_08.md`'s C3-disposal todo executed the delete
  (`instruments-service@4219aaa45a`), measuring the corpus at 12 real objects (not the 10,345 cited below) at
  execution time. See that plan's Progress Log for the full evidence trail (census/apply/post-delete verification).
- 2026-07-24 — plan forked from `migration_verification_orphan_safety_2026_06_10.md` (line-cap remediation split); no
  further work done yet beyond what the parent's archived Progress Log already recorded.
- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (sports tranche) — MIXED: todo 1 (land the preserved CF-5 relabel
  fix from `origin/wip-preserve/mtds-346-cf5-trades`) is genuinely AO-eligible, but todo 2 is explicitly labelled
  'operator-gated' (extend the UAC `SOURCE_COVERAGE_START` windows and re-backfill 10,345 objects, OR ratify the corpus
  permanently outside-window) — flipping the doc dispatches both, so it stays NA. Extraction of todo 1 into a batch doc
  is the right next move and is a plan-authoring call, parked
- **context-scout 2026-08-01**: populated/refreshed context_scope (2 entries).
- **resolve-round5-sports 2026-08-08**: RESOLVED — closed todo 2 as SUPERSEDED, citing the OPERATOR RULING banner (added
  earlier this session by a concurrent agent) and independently confirming `/codex/02-data/sports-2020-06-data-floor.md`
  already forecloses the extend-windows option. Verified `/plans/active/sports_taxonomy_p4_backfill_2026_08_08.md`
  exists and is `status: active`. Both todos in this doc are now closed — flagging for archival review (not archived
  here; leaving that to the taxonomy P4 finalize sibling per its own stated ownership). Closes round-5 sports item 4.
- **context-scout 2026-08-03**: refreshed context_scope (3 entries) — added the 2 source files the plan's 2 remaining
  todos target directly (`rebuild_sports_manifest_v9.py` for CF-5, `backfill_orphan_class_e_sports.py` for C3).
