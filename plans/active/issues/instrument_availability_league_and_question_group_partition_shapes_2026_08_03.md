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
context_scope: [/plans/active/issues/instrument_availability_hive_canonicalisation_2026_07_21.md, /codex/02-data/cross-asset-canonical-target-ssot.md, instruments-service/scripts/migrate_instrument_availability_hive_2026_08_03.py]
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

- [ ] 1. [OPERATOR] P1. **Sports half RESOLVED 2026-08-03 — narrowed to prediction only.** This todo duplicated
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
- [ ] 2. [DATA] P1. Re-verify prediction's `canonical_question_group=` shape is genuinely historical-only (sample all 78
      top-level prefixes, not just 3 — bounded per-prefix listing, not a corpus walk; confirm zero objects on any day
      after ~2026-07-22) OR find it is still being written and escalate to the SAME urgency as sports below if so. Does
      not depend on todo 1.
- [ ] 3. [DATA] P1. Locate the sports writer codepath that emits `day=/league=/venue=/instruments.parquet` (distinct
      from `_write_venue`/`_instrument_availability_sink_for` — likely in `sports.py`, `footystats.py`, or a per-league
      team/fixture/standings catalog writer in `process_enrichment.py`) and fix it to the ruled canonical shape from
      todo 1, following the SAME sink-PREFIX-not-partition-dict pattern as `_instrument_availability_sink_for`
      (alphabetical-sort trap). Depends on todo 1.
- [ ] 4. [DATA] P1. Historical migration: copy the ~172,592 (at investigation time, growing) sports `league=` objects to
      the ruled full-hive target — mirrors this doc's own `migrate_instrument_availability_hive_2026_08_03.py` pattern
      (copy-if-missing + metadata-verify, VM-scoped, never deletes the source). Depends on todo 1 + todo 3 (writer fixed
      first, so no new non-compliant objects land during/after the historical copy).
- [ ] 5. [DATA] P2. IF todo 2 finds prediction's `canonical_question_group=` shape still live: fix that writer too (same
      pattern as todo 3) and migrate its historical objects (same pattern as todo 4). IF todo 2 confirms
      historical-only: just run the historical migration (no writer fix needed). Depends on todo 1 + todo 2.

## Progress Log

- **context-scout 2026-08-03**: populated/refreshed context_scope (3 entries).
