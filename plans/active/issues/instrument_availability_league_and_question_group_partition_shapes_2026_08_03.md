---
doc_type: issue
title:
  instrument_availability carries TWO more non-compliant partition shapes never examined by the 2026-07-21
  hive-canonicalisation finding — sports `league=` (STILL ACTIVELY WRITTEN) + prediction `canonical_question_group=`
  (2026-08-03)
summary: >-
  While executing todo 7c of instrument_availability_hive_canonicalisation_2026_07_21.md (the day=/venue= flat ->
  full-hive copy migration), discovered the corpus also contains TWO further partition shapes that neither that doc's
  2026-07-21 grounding, the writer fix (instruments-service@a9be6ce9), nor the 7c migration script ever examined: sports
  writes `instrument_availability/by_date/day={D}/league={L}/venue={V}/instruments.parquet` (league= INSERTED between
  day= and venue=) and prediction writes
  `instrument_availability/by_date/canonical_question_group={G}/day={D}/venue={V}/instruments.parquet`
  (canonical_question_group= OUTERMOST, day= nested inside it). Both are the SAME class of operator HARD RULE violation
  (missing pipeline_mode=/asset_group=, non-canonical order) as the parent doc, at large scale: ~172,592 sports objects
  (confirmed present on 2026-08-10, the most recent captured day — an ONGOING, live writer defect, not just historical
  backlog) and ~25,745 prediction objects (sampled canonical_question_group= prefixes all stop ~2026-07-17..22, i.e.
  appears HISTORICAL-ONLY, superseded around the same time as the 2026-07-21 writer fix — needs confirmation, not
  assumed).
status: open
nature: issue
asset_group: [sports, prediction]
stage: [data]
repos: [instruments-service, unified-trading-library]
scope: [engineer, admin]
tags:
  [
    canonicalisation,
    instrument-availability,
    hive,
    sports,
    prediction,
    league,
    canonical-question-group,
    operator-ruling-needed,
  ]
related:
  [
    /plans/archive/issues/instrument_availability_hive_canonicalisation_2026_07_21.md,
    /codex/02-data/cross-asset-canonical-target-ssot.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-08-03
author: unknown
last_updated: 2026-08-03
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.72
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
context_scope:
  [
    /plans/active/issues/instrument_availability_hive_migration_unrecognized_shapes_and_content_mismatch_2026_08_03.md,
    /plans/archive/issues/instrument_availability_hive_canonicalisation_2026_07_21.md,
    /codex/02-data/cross-asset-canonical-target-ssot.md,
    instruments-service/scripts/migrate_instrument_availability_hive_2026_08_03.py,
    instruments-service/instruments_service/engine/orchestrator/writers.py,
    instruments-service/instruments_service/engine/orchestrator/sports.py,
  ]
locked_since:
supersedes:
superseded_by:
resolved_by:
source:
  discovered mid-execution of instrument_availability_hive_canonicalisation_2026_07_21.md todo 7c (2026-08-03, slot-9) —
  the migration script's own dry-run "unrecognized shapes" counter flagged these as anomalously large (172,592 / 25,745)
  versus cefi/defi/tradfi's noise-scale counts (234/207/54), triggering this investigation.
depends_on: []
sequential: true
---

# instrument_availability carries two more non-compliant partition shapes (2026-08-03)

## What I found

Executing todo 7c of `/plans/archive/issues/instrument_availability_hive_canonicalisation_2026_07_21.md` (the flat
`day=/venue=` -> full-hive copy migration), I ran
`instruments-service/scripts/migrate_instrument_availability_hive_2026_08_03.py --asset-group <ag>` in dry-run mode
(VM-side, bounded prefix listing — not a new corpus walk) against all 5 `instruments-store-{ag}-prd` buckets. Results:

| asset_group | flat (day=/venue=) | already full-hive | **unrecognized** |
| ----------- | -----------------: | ----------------: | ---------------: |
| cefi        |              7,650 |            45,673 |              234 |
| defi        |             73,679 |           105,757 |              207 |
| tradfi      |             25,402 |            25,288 |               54 |
| sports      |              6,330 |             9,721 |      **172,592** |
| prediction  |              4,105 |             6,772 |       **25,745** |

cefi/defi/tradfi's unrecognized counts are noise-scale (<0.5% of each bucket's total) — confirmed via a bounded,
single-level `gsutil ls` at `instrument_availability/by_date/` for all three: **zero** non-`day=` top-level prefixes
exist in any of them. Sports and prediction are qualitatively different — confirmed via the same bounded check:

- **Sports**: `instrument_availability/by_date/` has **0** non-`day=` top-level prefixes (day= IS first), but under
  `day={D}/` the writer inserts `league={L}/` BEFORE `venue=`:
  `instrument_availability/by_date/day=2026-07-26/league=HUNGARY_NB_I/venue=API_FOOTBALL/instruments.parquet`. Confirmed
  present on **day=2026-08-10** (the most recent captured day at investigation time) — this is an **ONGOING, live writer
  defect**, not solely historical backlog. The 2026-07-21 writer fix (`_instrument_availability_sink_for` in
  `instruments-service/instruments_service/engine/orchestrator/writers.py`) only touches `_write_venue`'s codepath
  (venue-keyed sports-reference writes, e.g. API_FOOTBALL fixtures/injuries/etc. under `venue={venue_str}` directly) —
  this `league=`-keyed shape is written by a **different, not-yet-located** writer codepath (likely a per-league
  team/fixture/standings catalog write in `sports.py`/`footystats.py`/`process_enrichment.py` — NOT examined by this
  investigation, left for the fix todo below).
- **Prediction**: `instrument_availability/by_date/` has **78** top-level `canonical_question_group=` prefixes (NOT
  `day=` — question-group is outermost, `day=` is nested one level inside it):
  `instrument_availability/by_date/canonical_question_group=BTC_PRICE_RANGE_DAILY/day=2026-07-22/venue=POLYMARKET/instruments.parquet`.
  Sampled 3 different `canonical_question_group=` prefixes (`AVAX_PRICE_RANGE_DAILY`, `BOX_OFFICE_OPENING_WEEKEND`,
  `BTC_PRICE_RANGE_DAILY`) — all three's most recent `day=` sub-prefix falls in the **2026-07-17 to 2026-07-22** range,
  i.e. clustered right around the 2026-07-21 writer-fix date. This is consistent with (but not yet PROVEN as) a
  **historical-only, superseded** shape — a worker picking up the fix todo below MUST re-confirm this (sample more than
  3 of the 78 prefixes, check for any `day=` beyond 2026-07-22) before treating it as non-live, since a false
  "historical-only" assumption would mean silently missing an ongoing violation exactly like the sports case.

Both shapes are the SAME class of violation the parent doc addresses (operator HARD RULE 2026-07-21: every data-at-rest
tree uses the full canonical hive grammar, `pipeline_mode=`/`asset_group=` included, in canonical order) — just with an
extra, non-canonical key (`league=` / `canonical_question_group=`) that the parent doc's grounding never encountered
because it only examined `_write_venue`'s single codepath.

## Why it matters

- Combined ~198,337 objects (and growing daily for sports) — comparable in scale to the ENTIRE cefi+tradfi flat
  population this doc's own todo 7c just migrated (~33,052). This was silently absent from the parent doc's todo 7b
  sizing table (its "sports 148,691 / prediction 22,637" row-totals actually already included these objects, just
  uncounted-as-a-distinct-shape — 7b's methodology sized total-objects-under-root, not shape-classified).
- Sports' `league=` shape is a **live, ongoing** writer defect — every new day captured makes the gap bigger, same
  urgency class as any other "writer still emits non-canonical paths" finding.
- The correct hive position for `league=`/`canonical_question_group=` is NOT yet defined anywhere —
  `cross-asset-canonical-target-ssot.md` §8's documented key set
  (`day/pipeline_mode/asset_group/venue/ instrument_type`) has no slot for a league or question-group axis. This is a
  genuine **design decision** (does the key survive at all in the target shape, and if so where in the canonical order —
  before or after `venue=`?), not a mechanical apply-the-existing-pattern fix — same class of decision the parent doc's
  todo 1 resolved via an explicit operator ruling into the same SSOT.

## Recommended decision

Propose (for operator confirmation, not unilaterally applied): extend `cross-asset-canonical-target-ssot.md` §8 with
`league=`/`canonical_question_group=` as an OPTIONAL trailing key, positioned AFTER `venue=` (mirrors how
`instrument_type=` was explicitly ruled OUT for the plain instrument_availability listing in the parent doc's todo 1,
but sports/prediction's own further sub-partitioning is closer to a `market=`/`canonical_question_group=` trailing tail
already accepted elsewhere in this same corpus — e.g. the prediction flat shape already nests `market=OTHER/` after
`venue=` without issue). Target: `day={D}/pipeline_mode={pm}/asset_group={ag}/venue={V}/league={L}/...` (sports) and
`day={D}/pipeline_mode={pm}/asset_group=prediction/venue={V}/canonical_question_group={G}/...` (prediction) — i.e. the
SAME canonical `day/pipeline_mode/asset_group/venue` prefix this doc's todos 2-8 already established, with the extra key
demoted to a trailing sub-partition rather than kept ahead of `day=`/between `day=` and `venue=`. This is a proposal,
not a ruling — needs explicit operator sign-off before any writer/migration code is built against it.

## Todos

- [x] ✅ 1. [OPERATOR] P1. **Prediction half RESOLVED 2026-08-06 (independently, via completed migration work — no
      operator ruling paragraph needed).**
      `instrument_availability_hive_migration_unrecognized_shapes_and_content_mismatch_2026_08_03.md` todo 3
      (`instruments-service@eca688ac6`) investigated the identical `canonical_question_group={G}/day={D}/venue={V}/...`
      shape, confirmed historical-only (last write 2026-07-22, same `a9be6ce9` writer-fix cutover as sports), and
      migrated it directly into the already-ruled base `instrument_availability` template (no
      `canonical_question_group=` trailing key) rather than adding one — now reflected in
      `/codex/02-data/cross-asset-canonical-target-ssot.md` §8's prediction banner. This answers the "rule on the
      canonical position" question in the negative (it collapses into the base shape) via completed migration rather
      than a separate ruling. **Todos 2/5's prediction-half scope is now moot for the same reason — not independently
      re-verified/flipped here (out of this bonus finding's scope), flagged for a future pass.** Original text preserved
      below for record. **Sports half RESOLVED 2026-08-03 — narrowed to prediction only.** This todo duplicated
      `/plans/active/issues/instrument_availability_hive_migration_unrecognized_shapes_and_content_mismatch_2026_08_03.md`
      todo 1 (same underlying decision, filed independently same day by a different slot): the operator ruled on that
      doc's todo 1 — option (a), `league=` is a legitimate sports trailing key
      (`day={D}/pipeline_mode={pm}/asset_group=sports/venue={V}/league={L}/instruments.parquet`,
      `cross-asset-canonical-target-ssot.md` §8 "sports exception" banner + §11c decision log). **That ruling covers
      ONLY sports's `league=` position — it does not mention `canonical_question_group=` (prediction) at all**, so this
      todo's remaining open scope is narrowed to: rule on the canonical target position for prediction's
      `canonical_question_group=` key alone (confirm or revise the "Recommended decision" above for prediction), write
      that ruling into `cross-asset-canonical-target-ssot.md` §8. Still blocks todos 3-5 below for the prediction half;
      todo 3's sports half can now proceed against the already-ruled shape without waiting further.
- [x] ✅ 2. [DATA] P1. Re-verify prediction's `canonical_question_group=` shape is genuinely historical-only (sample all
      78 top-level prefixes, not just 3 — bounded per-prefix listing, not a corpus walk; confirm zero objects on any day
      after ~2026-07-22) — **CONFIRMED HISTORICAL-ONLY 2026-08-06**: all 78 `canonical_question_group=` prefixes sampled
      via bounded GCS per-prefix listing (16-thread parallel, `instruments-store-pred-prd-central-element-323112`);
      latest day=2026-07-22 across all groups (the `a9be6ce9` writer-fix cutover), 0 still-live writes, 0 exceptions. No
      escalation needed. — unified-trading-pm@b53a0a1e6 (investigation only, no code change). Does not depend on todo 1.
- [x] ✅ 3. [DATA] P1. Locate the sports writer codepath that emits `day=/league=/venue=/instruments.parquet` (distinct
      from `_write_venue`/`_instrument_availability_sink_for` — likely in `sports.py`, `footystats.py`, or a per-league
      team/fixture/standings catalog writer in `process_enrichment.py`) and fix it to the ruled canonical shape from
      todo 1, following the SAME sink-PREFIX-not-partition-dict pattern as `_instrument_availability_sink_for`
      (alphabetical-sort trap). — **ALREADY DONE 2026-08-03 by sibling doc**
      (`instrument_availability_hive_migration_unrecognized_shapes_and_content_mismatch_2026_08_03.md` todo 2): codepath
      located in `_write_sports_fixture_venue` (`process_write.py:247`, NOT in
      `sports.py`/`footystats.py`/`process_enrichment.py` as originally speculated). Fixed to use
      `_instrument_availability_sink_for(bucket, ...)` with `league=` trailing after `venue=` (original
      `instruments-service@ba87cc32`, current LDR equivalent `4e25aae1`). Migration tool extended with
      `_SPORTS_LEAGUE_FLAT_RE` to recognize + migrate the legacy shape. Writer fix surviving on LDR confirmed 2026-08-06
      via code inspection (slot 8). Depends on todo 1.
- [x] ✅ 4. [DATA] P1. **EXECUTED 2026-08-06 (slot 6, data_engineering craft).** Historical migration of sports
      `league=` objects via
      `migrate_instrument_availability_hive_2026_08_03.py --asset-group sports --apply-prod     --confirm-prod-write`
      (PROD, `instruments-store-sports-prd-central-element-323112`). Results: **172,348 copied**, **247
      content_mismatch** (all `day=2026-08-02`, writer-fix cutover day — resolved via `--resolve-content-mismatch`: 8
      flat_wins, 7 hive_wins, 230 tie_flat_bytes, **2 disjoint** flagged for manual review), **0 failed**.
      Post-migration dry-run confirms **188,680 total hive objects** (reconciles: 16,332 pre-existing + 172,348 copied =
      188,680 ✓). Flat sources preserved (copy-only, never deletes). 2 disjoint pairs carried forward:
      `KUWAIT_DIVISION_1/day=2026-08-02` (flat=4 hive=4, neither superset) and `ROMANIA_LIGA_I/day=2026-08-09` (flat=2
      hive=2, neither superset) — same instrument-churn class as the sibling doc's 14 disjoint pairs, not
      migration-blocking. — instruments-service (migration execution, no code change — script already shipped by todo
      3/sibling doc todo 2).
- [ ] 5. [DATA] P2. IF todo 2 finds prediction's `canonical_question_group=` shape still live: fix that writer too (same
      pattern as todo 3) and migrate its historical objects (same pattern as todo 4). IF todo 2 confirms
      historical-only: just run the historical migration (no writer fix needed). Depends on todo 1 + todo 2.

## Progress Log

- **context-scout 2026-08-03**: populated/refreshed context_scope (6 entries).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged. Note: the sibling doc
  `instrument_availability_hive_migration_unrecognized_shapes_and_content_mismatch_2026_08_03.md` already reports the
  sports `league=` writer fix shipped (`instruments-service@ba87cc32`) — this doc's todos 1/3/4 (sports half) may be
  stale/duplicative; not verified further, flagged for the next content pass, not resolved here (out of this skill's
  scope).
