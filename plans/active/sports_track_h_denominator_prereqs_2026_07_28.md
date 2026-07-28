---
doc_type: plan
title: Sports Track H denominator prerequisites — MDPS odds_horizon_bucket reprocess + batch_footystats copy+swap
summary: >-
  The 2 real remaining blockers (of an original 3) on `sports_consolidated_native_ao_extract_2026_07_25.md`'s Track H
  "registry-aware honest-coverage denominator" todo — confirmed still unshipped across 4 consecutive same-day dispatches
  (slots 11, 7, 10, 15 on 2026-07-28), each independently re-checking shipped-status rather than re-deriving the
  finding. Extracted into its own dispatchable plan (rather than left as issue-doc prose) so
  `sports_track_h_denominator_gated_2026_07_28.md`'s `depends_on`+`gate_on_depends: true` machine-gate has real upstream
  tasks to hold on — the coverage-registry refresh (the 3rd original blocker) already shipped 2026-07-22/07-27 and is
  not repeated here.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [market-data-processing-service, market-tick-data-service]
scope: [engineer]
tags: [sports, league-id, migration, prereqs, ao-dispatch, plan-hygiene]
related:
  [
    /plans/active/issues/sports_league_id_namespace_migration_2026_07_20.md,
    /plans/active/sports_track_h_denominator_gated_2026_07_28.md,
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
  ]
created: "2026-07-28"
last_updated: "2026-07-28"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Operator-directed split (2026-07-28, answering blocked question BLK-2f9e7680): 4 consecutive same-day dispatches of
  the Track H denominator todo (slots 11/7/10/15) hit the identical STOP condition; a priority-999 park did not
  hard-block re-dispatch because no machine `depends_on` existed. This plan supplies the 2 real upstream todos so the
  companion gated plan can hold on them for real.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

# Sports Track H denominator prerequisites

> Both todos below are independent (different repos, different scripts) and can run concurrently. Neither is
> `[OPERATOR]`-gated: both are idempotent, copy-before-delete/reprocess-from-canonical-source operations already
> authorised in principle by `issues/sports_league_id_namespace_migration_2026_07_20.md`'s "READY TO EXECUTE 2026-07-21"
> section (operator-authorised migrate+delete, gated on dry-run success + VM drain — both already met for the raw
> `batch_odds_api` shape; these 2 todos extend the same authorised migration to its 2 still-outstanding shapes).

## Todos

- [ ] [CODE] P1. **Re-run the MDPS `odds_horizon_bucket` reprocess (Step 7 of the league_id namespace migration).**
      `market-data-processing-service/.../reprocess_sports_odds.py` must be re-run for the historical days so its
      `bucketed.parquet` output regenerates under the now-canonical `league_id=` partition (raw content is already
      canonical per the shipped `batch_odds_api` migration — this step regenerates the DERIVED `odds_horizon_bucket`
      surface from it, per `issues/sports_league_id_namespace_migration_2026_07_20.md` § "Ordered procedure" Step 7).
      **Mitigate the features double-count hazard** (that doc's STOP condition 7): do the reprocess + stale-object
      delete inside a drained per-day window, not as a slow background copy, so old-raw and new-canonical
      `bucketed.parquet` never coexist for a features read. Self-justified, not `[OPERATOR]`-gated: a re-derivation from
      already-canonical source content, not a destructive operation on source data. (repo:
      market-data-processing-service). **Done when**: a fresh live manifest census
      (`read_availability_index(bucket, columns=["league_id","pipeline_mode"])`) shows 0
      `batch_mdps_odds_horizon_bucket` rows carrying a non-registry `league_id`, and a features read for a migrated day
      returns a single non-doubled row set (no old+new `bucketed.parquet` double-count). Source:
      `issues/sports_league_id_namespace_migration_2026_07_20.md` STATUS 2026-07-25 + RE-DISPATCH CHECK 2026-07-28
      (slot-7/slot-10).

- [ ] [CODE] P1. **Build + execute the `batch_footystats` copy+swap pass** (footystats legacy-bundle shape, 16,970
      objects per the 2026-07-20 sizing) — canonicalise its `league_id`, mirroring the already-shipped, adversarially-
      verified raw `batch_odds_api` executor (`market-tick-data-service@b2a49317`,
      `scripts/sports/league_id_relocation/migrate_sports_league_id_casing_2026_07_21.py`): COPY (server-side, no
      egress) to the canonical target + rewrite the parquet's `league_id` CONTENT column, CRC/row-verify (source∩copy
      row-key intersection == 100%, never object-count-only), THEN atomic manifest swap reusing
      `deployment-service/scripts/rebuild_sports_manifest.py::_clean_stale_league_entries` (never an additive write —
      the consolidator dedup key includes `league_id`). Never delete-first; the old objects' deletion stays a separate,
      later, human-gated step per the delete-safety protocol (out of scope for this todo). Self-justified, not
      `[OPERATOR]`-gated: reversible copy/verify/swap only, same authorised pattern as the sibling raw-shape migration.
      (repo: market-tick-data-service). **Done when**: a fresh live manifest census shows 0 `batch_footystats` rows
      carrying a non-registry `league_id`. Source: `issues/sports_league_id_namespace_migration_2026_07_20.md` STATUS
      2026-07-25 + RE-DISPATCH CHECK 2026-07-28 (slot-7/slot-10);
      `issues/sports_batch_footystats_mistamped_odds_orphan_delete_staging_2026_07_25.md:191-196` (confirms this shape
      was never in the earlier swap's scope).

## Progress Log

### 2026-07-28 (slot-15) — plan created, split out of the Track H denominator bounce

Created per operator answer to `BLK-2f9e7680` (4th consecutive same-day re-dispatch of
`sports_consolidated_native_ao_extract_2026_07_25.md`'s Track H denominator todo, all 4 hitting the identical STOP
condition). A priority-999 backlog park does not hard-block re-dispatch without a machine `depends_on` — see
`sports_track_h_denominator_gated_2026_07_28.md` for the companion gated plan this unblocks.
