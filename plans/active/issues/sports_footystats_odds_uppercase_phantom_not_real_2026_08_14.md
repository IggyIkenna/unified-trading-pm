---
doc_type: issue
title:
  footystats uppercase `ODDS` (MTDS) is phantom, not "6,306 real shards" — P2 fold-todo premise contradicted by live GCS
  check
summary: >-
  Live GCS-existence check contradicts the P2 migration plan's "expect 6,306 real shards" premise for footystats
  uppercase ODDS — 0/20 sampled rows have backing content, while their lowercase odds twin does (20/20); the UAC comment
  that reclassified this population as "real, live instruments-service data" is also wrong about which system owns it.
  Blocks the P2 "fold footystats ODDS+odds" todo pending operator disposition.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts]
scope: [engineer]
tags: [sports, data-correctness, manifest, phantom-rows, blocked]
related:
  [
    /plans/active/sports_taxonomy_p2_migration_2026_08_08.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/archive/2026_08/sports_taxonomy_p1_capture_and_contracts_2026_08_08.md,
    /plans/archive/issues/sports_shard_enumeration_cartesian_blowup_2026_07_20.md,
  ]
created: 2026-08-14
author: slot-18 (data_engineering)
assigned_vm: planning
parent_epic: sports_master
priority: P0
resolved_by:
locked_by:
source:
  [
    "sports_taxonomy_p2_migration_2026_08_08.md todo 'Fold footystats ODDS (6,306 captured) + odds (16,207 captured)
    into a single odds'",
  ]
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# footystats uppercase `ODDS` is phantom, not real — contradicts the P2 todo's own premise

## What I found

The P2 plan's todo (`/plans/active/sports_taxonomy_p2_migration_2026_08_08.md`, "Fold footystats `ODDS` (6,306
captured) + `odds` (16,207 captured) into a single `odds`") states: "the UAC comment calling the uppercase set '4 stale
empty rows' is FALSE — expect 6,306 real shards." That premise itself traces to a 2026-08-08 "correction" in
`unified_api_contracts/registry/market_data_categories.py` (`SPORTS_DATA_TYPE_ACCEPTED_STALE_UPPERCASE_RESIDUE` comment,
`unified-api-contracts@54e7e64d`) which asserts the 6,306 `ODDS` (uppercase, venue=FOOTYSTATS, source=footystats) rows
are "**a live instruments-service reference-data population**... 6,306 real captured shards", not MDPS writer residue.

Both the count (6,306 captured / 136 empty_confirmed, venue=FOOTYSTATS) and the corresponding lowercase `odds` count
(16,207 captured / 313 empty_confirmed, venue=FOOTYSTATS) are confirmed live in the MTDS raw-tick manifest
(`market-data-tick-sports-prd-central-element-323112`, `read_availability_index`, bounded column-pruned read) — so the
counts themselves are right. But two things the 2026-08-08 correction asserted are demonstrably wrong, checked live this
session (2026-08-14):

1. **"That is a live instruments-service reference-data population" is FALSE.** I read the actual instruments-service
   manifest (`instruments-store-sports-prd-central-element-323112`) directly: it carries **0 uppercase `ODDS` rows**
   (fully lowercased by the P2 19-token migration, `instruments-service@3637252f81`/ `@f2586ada09`) and its lowercase
   `odds`/footystats population is **30,498 captured** — a completely different count from 6,306/16,207. The 6,306-row
   population the comment describes is physically in the **MTDS** raw-tick manifest, not instruments-service. The
   comment's own "the census conflated two different systems that happen to share a token" self-diagnosis is,
   ironically, itself conflating the two systems.

2. **"6,306 real captured shards" is FALSE — they are phantom (no backing GCS content).** I ran a live GCS existence
   check (same two-shape probe `drop_sports_odds_phantom_uppercase_2026_07_26.py` already built for the ODDS_API-venue
   slice of this same population) against a random sample of 20 of the 6,306 venue=FOOTYSTATS uppercase-`ODDS`
   `captured` rows: **0/20 (0%) have a backing parquet object** under either known GCS shape. For the SAME 20 (date,
   league) combinations, the lowercase `odds` twin **does** have a backing object, 20/20 (100%). This exactly reproduces
   the finding `plans/archive/issues/sports_shard_enumeration_cartesian_blowup_2026_07_20.md`'s dry-run tool already
   made for the ODDS_API-venue slice (22,145 rows sampled, predicted-phantom) — the 2026-08-08 correction re-classified
   this population as "real" based on `capture_status == 'captured'` alone, without a live GCS existence check, and
   appears to have gotten it backwards.

Scratch investigation scripts (not committed — safe to lose, kept local for reproduction): bounded
`read_availability_index` queries + a per-row two-shape GCS-existence probe mirroring
`drop_sports_odds_phantom_uppercase_2026_07_26.py`'s own candidate-prefix logic, run via
`scripts/dev/run-bounded-analysis.sh` (memory-capped, per RULES.md § 1).

## Why it matters

This P0 todo sits inside `sports_taxonomy_p2_migration_2026_08_08.md`, a `sequential: true`, prod-manifest-mutating
migration plan with an explicit §3a delete-safety posture. "Fold" (as literally worded) implies a content-merge of two
real populations — the same four-surface operation already executed for `trades`→`odds` (a VM-scale GCS
read/rewrite/write, `market-tick-data-service@071a5466`). If the uppercase rows are genuinely phantom duplicates of
already-captured lowercase data (as this session's live check indicates), running a content-merge fold would be pure
wasted GCS I/O against non-existent source objects — the real fix is a much cheaper **manifest-only relabel (or purge,
if genuinely orphaned) of the 6,306+136 uppercase rows**, since there is nothing on disk to move or merge. Executing the
wrong operation either wastes VM/GCS cost for no data-correctness gain, or — worse — if my 20-row sample is somehow
unrepresentative of the full 6,306, a manifest-only purge could silently discard real data that a full-population check
would have caught. This is exactly the class of finding CLAUDE.md's "big finding (data-correctness / SSOT contradiction)
→ NOTIFY OPERATOR" rule exists for: the premise has now flipped twice ("4 stale" → "6,306 real" → this session's
"phantom, 0/20 sampled"), and a third silent flip without operator visibility risks the same mistake recurring a third
time.

## Recommended decision

- [ ] [OPERATOR] P0. **Confirm the disposition of the 6,306 captured + 136 empty_confirmed uppercase `ODDS`
      (venue=FOOTYSTATS, MTDS bucket `market-data-tick-sports-prd-central-element-323112`) manifest rows** before any P2
      fold/drop code ships. Two live-measured facts to reconcile: (a) 0/20 sampled rows have backing GCS content under
      either known raw_tick_data path shape; (b) the same (date, league) combination's lowercase `odds` row does have
      backing content, 20/20. Recommendation: run the FULL population (not just a 20-row sample) through the same
      live-existence check `drop_sports_odds_phantom_uppercase_2026_07_26.py` already built (or a
      footystats-venue-scoped variant of it), then — if the full check confirms phantom — replace the P2 todo's "fold"
      framing with a manifest-only relabel/purge (no GCS object move needed, since there is nothing on disk under the
      uppercase token) rather than a four-surface content-merge. If the full check finds a meaningful non-phantom
      minority, that minority is the actual "real shards" population and needs the four-surface fold; the rest does not.
      (repo: market-tick-data-service, unified-api-contracts for the corrected comment)
- [ ] [DATA] P1. **Correct `unified_api_contracts/registry/market_data_categories.py`'s
      `SPORTS_DATA_TYPE_ACCEPTED_STALE_UPPERCASE_RESIDUE` comment** once the operator's disposition above is settled —
      it currently claims the 6,306-row population is "a live instruments-service reference-data population", which this
      session's direct read of the instruments-service manifest disproves (0 uppercase `ODDS` rows there, 30,498
      captured lowercase `odds`/footystats — an unrelated count). (repo: unified-api-contracts)

## Progress Log

- **2026-08-14 (slot-18)** — Filed. Dispatched task `sports_taxonomy_p2_migration-005` (the "fold footystats ODDS +
  odds" todo); before implementing, live-verified the todo's own "expect 6,306 real shards" premise against the actual
  GCS estate and found it contradicted (0/20 phantom, matching the twin lowercase). Filed this issue + posted `/blocked`
  on the task rather than execute a fold against non-existent source content or unilaterally reclassify a
  twice-already-revised population without operator visibility.
