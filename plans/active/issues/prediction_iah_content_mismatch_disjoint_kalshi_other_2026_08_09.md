---
doc_type: issue
title: prediction *-iah apply-prod — 2 genuinely-disjoint content_mismatch pairs (KALSHI/OTHER, day=2026-07-21)
summary: >-
  Applied the already-tool-extended (instruments-service@eca688ac) historical hive-copy migration for prediction's two
  confirmed-historical-only legacy shapes (canonical_question_group={G}/day={D}/venue={V} +
  market_lifecycle's day={D}/group={G}/venue={V}), via a fresh canonical-migration-prediction-iah VM
  (--apply-prod --confirm-prod-write). Result: 13,282 candidates, 13,280 copied/already-present-verified, 0 failed, 2
  content_mismatch. Both mismatch pairs (asset_group=prediction, canonical_question_group=OTHER, day=2026-07-21,
  venue=KALSHI — one instrument_availability, one its market_lifecycle sibling) resolve as `disjoint_needs_review`
  under the tool's ruled "superset wins" policy (todo 4 of the archived
  instrument_availability_hive_migration_unrecognized_shapes_and_content_mismatch_2026_08_03.md) — neither the flat nor
  the hive side is a superset of the other (flat=2185/hive=196 ids for instrument_availability; flat=9190/hive=2083 for
  market_lifecycle), so the tool correctly declined to auto-resolve. Manual inspection shows BOTH sides carry real,
  non-overlapping market data from the exact writer-cutover boundary day (old flat writer + the 2026-07-21 03:20:56Z
  hive-writer deploy both wrote to this same nominal day), so a straight "pick one side" copy (the precedent set by
  todo 13's 14-pair review) would silently drop real markets from whichever side loses — this needs an explicit
  operator ruling on union vs. pick, not a mechanical resolution.
status: open
nature: issue
asset_group: [prediction]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [data-correctness, content-mismatch, instrument-availability, hive-migration, kalshi, disjoint]
related:
  [
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_08/issues/instrument_availability_hive_migration_unrecognized_shapes_and_content_mismatch_2026_08_03.md,
    /plans/archive/issues/instrument_availability_hive_canonicalisation_2026_07_21.md,
    /codex/02-data/canonical-cutover-register.md,
    /plans/active/sports_satellite_ao_dispatch_batch9_2026_08_04.md,
  ]
created: 2026-08-09
parent_epic: infrastructure_master
assigned_vm: NA
priority: P2
last_updated: 2026-08-09
source: >-
  sports_satellite_ao_dispatch_batch9_2026_08_04.md todo -004 (slot 13, data_engineering) — apply-prod run of
  scripts/migrate_instrument_availability_hive_2026_08_03.py --asset-group prediction --apply-prod
  --confirm-prod-write, executed on canonical-migration-prediction-iah-20260809-144755.
resolved_by:
locked_by:
execution_scope: local-only
drift_direction: none
depends_on: []
supersedes:
---

# prediction *-iah apply-prod — 2 disjoint content_mismatch pairs

## What I found

Fresh apply-prod run (`canonical-migration-prediction-iah-20260809-144755`, 126.6s, 32 workers):

```
copied:                   0
already_present_verified: 13,280
source_vanished:          0
content_mismatch:         2
failed:                   0
```

(The `copied: 0` / `already_present_verified: 13,280` split confirms this population had already been substantially
migrated by an earlier attempt — the first launch of this todo, 2026-08-09 14:29Z, self-deleted mid-`uv pip install`
before ever reaching the Python script, per a stale `SETUPTOOLS_SCM_PRETEND_VERSION=0.99.0` baked into the tarball
snapshot used at that launch time — root-caused + since fixed upstream at `deployment-service@501eb48b`/`@49b50814`,
tarballs/startup-script republished 2026-08-09T14:47-48Z. Not re-filing as a separate issue: the fix already landed
and the standing floor check (`check_setuptools_scm_pretend_version_floor.py`) now guards regression. The
`already_present_verified` count implies most objects were copied on a PRIOR, unobserved successful run — plausible
given the tool's own idempotency design (copy-if-missing) and the 2026-08-03 dry-run's original 13,282-candidate
count for this same population, unchanged here.)

The 2 `content_mismatch` pairs, downloaded + compared by identity column (`raw_symbol` /
`market_id`) per the ruled todo-4 methodology:

| src (flat) | dst (hive) | flat ids | hive ids | common | only_flat | only_hive |
|---|---|---|---|---|---|---|
| `instrument_availability/by_date/canonical_question_group=OTHER/day=2026-07-21/venue=KALSHI/instruments.parquet` | `.../day=2026-07-21/pipeline_mode=batch_kalshi/asset_group=prediction/venue=KALSHI/canonical_question_group=OTHER/instruments.parquet` | 2,185 | 196 | 183 | 2,002 | 13 |
| `market_lifecycle/by_canonical_group/day=2026-07-21/group=OTHER/venue=KALSHI/market_lifecycle.parquet` | `.../day=2026-07-21/pipeline_mode=batch_instruments_service/asset_group=prediction/venue=KALSHI/group=OTHER/market_lifecycle.parquet` | 9,190 | 2,083 | 2,016 | 7,174 | 67 |

Neither side is a superset (`disjoint_needs_review` per `_resolve_one_mismatch`). Sampling `only_hive` on the
`instrument_availability` pair shows tickers dated `26JUL24` (e.g. `KXMLBGAME-26JUL241915SDATL`) even though this
object's own `day=` partition key is `2026-07-21` — consistent with the hive side being written by the NEW
(post-`a9be6ce9`) live writer starting from its 2026-07-21T03:20:56Z deploy moment (which legitimately captures
markets whose lifecycle metadata references nearby future dates), while the flat side holds the OLD writer's
earlier-that-day snapshot. Both are real production Kalshi market records, not corrupt/test data — this is exactly
the "genuinely disjoint, non-overlapping instruments on both sides" backstop case todo 4's ruling anticipated
(`instrument_availability_hive_migration_unrecognized_shapes_and_content_mismatch_2026_08_03.md` line ~278), not a
tool bug.

## Why it matters

A one-sided "pick the richer side" resolution (the precedent set by todo 13's 14-pair review, e.g. copying flat→hive
when flat was substantially richer) would be WRONG here — it would silently drop 13 (instrument_availability) / 67
(market_lifecycle) real hive-only Kalshi records that todo 13's simpler pairs didn't have to contend with (those were
either clean supersets or trivial 1-5-symbol churn). This is `canonical_question_group=OTHER` — the catch-all bucket,
so both sides plausibly hold real, distinct markets that never got reclassified into a named group. Getting this
wrong either direction is a real data-completeness gap for prediction's canonical `instrument_availability`/
`market_lifecycle` surfaces on the exact writer-cutover boundary day.

## Recommended decision

[OPERATOR] ruling needed on the resolution policy for these 2 pairs (and any future genuinely-disjoint pair this
population might still surface — todo 4's original ruling only covered superset/tie cases mechanically; disjoint was
always the explicit manual-review backstop, never auto-resolved):

- **(a) Union** (recommended): merge both sides on the identity column, write the union back to the hive target
  (keeping the flat original untouched, copy-only convention preserved). Correct outcome, but is NEW code — the
  existing tool only supports pick-one-side (`gcs_copy_object`), not a merge-and-write path.
  Follow-up: `- [ ] [DATA] P2. Add a --union-content-mismatch mode to
  instruments-service/scripts/migrate_instrument_availability_hive_2026_08_03.py that merges flat+hive rows by
  identity column (raw_symbol / market_id) and writes the merged parquet to the hive target only (never touches the
  flat source); apply to these 2 pairs. (repo: instruments-service)`
- **(b) Leave both sides as-is, flag as a permanent residual**: simplest, but the hive target remains missing 2,002 /
  7,174 real flat-only markets (and the flat original remains missing 13 / 67 hive-only ones) — a real, if small
  (population is 2 pairs out of 13,282), completeness gap on the canonical surface.

- [ ] [OPERATOR] P2. Rule union-vs-leave-as-is for the 2 disjoint prediction content_mismatch pairs above (KALSHI/
      OTHER/day=2026-07-21, both instrument_availability + market_lifecycle); if union, dispatch the follow-up
      `--union-content-mismatch` tool change to instruments-service per option (a) above.

## Progress Log

- **2026-08-09 (slot 13, data_engineering)**: filed after completing sports_satellite_ao_dispatch_batch9_2026_08_04.md
  todo -004's apply-prod run. 13,280/13,282 objects clean (0 failed); these 2 pairs are the only residual, both
  confirmed genuinely disjoint (not a tool defect) and out of todo -004's automated-resolution scope by design (mirrors
  the archived sibling doc's own todo-4/todo-13 precedent).
