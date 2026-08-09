---
doc_type: codex-ssot
title: Entity rename/split must migrate every consumer in the same change
summary:
  HARD RULE — renaming or splitting a data entity (data_type, instrument_type, venue token, axis name, GCS path segment)
  MUST enumerate every consumer and migrate them in the SAME change. A grep of the renamed token is NOT a sufficient
  enumeration, because real consumers bind by GCS path prefix, by filename, by registry membership and by frontmatter,
  none of which a token grep finds. Written 2026-08-08 from a measured near-miss in the sports estate.
status: current
nature: ssot
asset_group: [meta]
stage: [data]
repos:
  [
    unified-api-contracts,
    market-tick-data-service,
    market-data-processing-service,
    instruments-service,
    features-service,
    ml-service,
    deployment-api,
  ]
scope: [engineer, admin]
tags: [rename, migration, consumers, canonicalisation, process-rule, hard-rule]
related:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/four-surface-reconciliation-procedure.md,
    /codex/02-data/sports-data-types-catalog.md,
    /plans/archive/2026_08/sports_taxonomy_p1_capture_and_contracts_2026_08_08.md,
  ]
created: 2026-08-08
authoritative_for:
  [entity rename/split consumer-migration rule, what counts as a complete consumer enumeration before a rename]
referenced_by:
owner:
last_reviewed: 2026-08-08
code_refs:
---

# Entity rename/split must migrate every consumer in the same change

> **HARD RULE (operator ruling 2026-08-08).** Renaming or splitting a data entity — a `data_type`, an `instrument_type`,
> a venue token, an axis name, or a GCS path segment — MUST enumerate every consumer and migrate them in the **same
> change**. A rename that lands without its consumer migration is review-blocking.

## Why this exists

The rule was proposed in `sports_features_layer_findings_sweep_2026_07_18_part3_2026_07_26.md` after an
`entity=fixtures` → `fixtures_schedule`/`fixtures_outcomes` split left consumers behind. It was ratified 2026-08-08 and
immediately governs the sports taxonomy chain, which performs the operation twice at scale: `trades` → `odds` across
375,257 shards and six years, and the whole 19-token uppercase→lowercase instruments-service vocabulary.

## The enumeration is NOT a grep

This is the load-bearing part of the rule. **A grep of the renamed token systematically misses real consumers**, because
consumers bind to an entity in at least five different ways:

| binding                  | example (measured, sports estate 2026-08-08)                                                                                                             | found by a token grep? |
| ------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------- |
| **GCS path prefix**      | `features-service` `sports_feature_loader._ODDS_BUCKETED_PREFIXES` matches `.../pipeline_mode=batch_mdps_odds_horizon_bucket/`                           | **NO**                 |
| **filename**             | `reprocess_sports_odds.py::_is_consumable_trades_blob` matches on the FILENAME `inplay_ticks.parquet` alone                                              | **NO**                 |
| **registry membership**  | a venue's presence in `SPORTS_EXCHANGE_VENUES` drives fee model, alpha profile and instrument types — none of which name the venue                       | partially              |
| **frontmatter / config** | `SPORTS_DATA_TYPE_TO_SOURCE` keys drive the expected-universe enumerator; a missing key mints `expected_unattempted` rows across every instrument × date | partially              |
| **the data_type column** | the obvious case                                                                                                                                         | yes                    |

Corollary of the workspace's standing grep rule: **0 hits ≠ no consumers.** Grep-then-READ, never grep-then-conclude.

## Required before any rename/split lands

1. **Produce a written consumer inventory**, checked in, covering at minimum: every writer, every reader, the
   expected-universe enumerator, path-prefix and filename matchers, the manifest/shard-atom definition, the
   honest-coverage measurer, and any UI/API surface that renders the axis.
2. **Migrate every listed consumer in the same change** as the rename. If a consumer genuinely cannot move in the same
   change, the rename does not land — split the work so the consumer moves first.
3. **Keep the shard atom identical across writer / manifest / status / gate / UI** (see
   `/codex/02-data/availability-manifest-and-data-status.md`). A rename that changes the atom on one surface only is the
   four-surface drift `/codex/02-data/four-surface-reconciliation-procedure.md` exists to catch.
4. **State explicitly what was NOT checked.** An enumeration with a stated blind spot is honest; one that implies
   completeness it does not have is the failure mode.

## Anti-pattern: the accepted-exception escape hatch

When a rename leaves stranded values behind, the tempting fix is to add them to an accepted-exception registry so the
drift panel goes quiet. **That is not canonicalisation — it is suppression**, and it is how the sports estate reached a
state where the panel reported "0 non-canonical" while hiding 21 venues (~340k shards), a blank venue, and 6,306
captured shards of an uppercase data_type that a UAC comment wrongly described as "4 stale empty rows".

Accepted-exception sets are legitimate only for values that are **real, understood, and permanently intended** — never
as a landing zone for a migration that was not finished. **The success criterion for a rename is the exception set
shrinking, never growing.**
