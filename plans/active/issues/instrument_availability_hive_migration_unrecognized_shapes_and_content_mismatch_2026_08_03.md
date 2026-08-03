---
doc_type: issue
title:
  instrument_availability hive migration (7c) — sports/prediction unrecognized flat shapes + cross-AG content_mismatch
  residuals (2026-08-03)
summary: >-
  Executing todo 7c of instrument_availability_hive_canonicalisation_2026_07_21.md (the copy-and-verify migration)
  surfaced three correctness gaps the parent plan's todos 1-7b did not anticipate: (1) sports's instrument_availability
  writer STILL emits a completely different flat shape (day=/league=/venue=/...) as of TODAY (2026-08-02 writes
  confirmed) — the 2026-07-21 writer fix (instruments-service@a9be6ce9) evidently did not cover the sports code path,
  and this shape is invisible to the 7c migration tool's regex (~172K objects silently "unrecognized (ignored)"); (2)
  prediction has a SECOND non-canonical shape rooted at canonical_question_group=/day=/venue=/... (group BEFORE day,
  inverse of the recognized day=/venue=/canonical_question_group= ordering) contributing to ~25K unrecognized objects;
  (3) across cefi/defi/tradfi, a total of ~32,846 flat source objects have an ALREADY-EXISTING hive-path target with
  DIFFERENT (crc32c, size) content — the tool safely refuses to overwrite (by design) but these need a human
  authoritative-source decision before they can be resolved.
status: open
nature: issue
asset_group: [sports, prediction, cefi, defi, tradfi]
stage: [data]
repos: [instruments-service, unified-trading-library]
scope: [engineer, admin]
tags:
  [canonicalisation, instrument-availability, hive, sports, prediction, content-mismatch, data-correctness, migration]
related:
  [
    /plans/active/issues/instrument_availability_hive_canonicalisation_2026_07_21.md,
    /codex/02-data/cross-asset-canonical-target-ssot.md,
  ]
created: 2026-08-03
last_updated: 2026-08-03
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1.2
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
context_scope:
  [
    /codex/02-data/cross-asset-canonical-target-ssot.md,
    /plans/active/issues/instrument_availability_hive_canonicalisation_2026_07_21.md,
    instruments-service/scripts/migrate_instrument_availability_hive_2026_08_03.py,
    instruments-service/instruments_service/engine/orchestrator/process_write.py,
  ]
locked_since:
supersedes:
superseded_by:
resolved_by:
source: slot-8 worker, discovered while executing todo 7c (2026-08-03)
depends_on: []
sequential: false
---

# instrument_availability hive migration (7c) — unrecognized shapes + content_mismatch residuals (2026-08-03)

## What I found

Executing todo 7c (the flat→full-hive copy-and-verify migration,
`instruments-service/scripts/migrate_instrument_availability_hive_2026_08_03.py`) on real PROD infra for all 5 asset
groups surfaced three gaps the parent doc's todos 1-7b did not classify or anticipate (7b's sizing was a raw
prefix-object COUNT, not a shape classification):

### 1. Sports: the writer was NEVER actually fixed — a third, unrecognized flat shape

`gs://instruments-store-sports-prd-.../instrument_availability/by_date/day=2026-08-02/league=ARGENTINA_PRIMERA_NACIONAL/venue=API_FOOTBALL/...`
— confirmed via a direct listing of **today's** (2026-08-02) writes. The shape is
`day={D}/league={L}/venue={V}/instruments.parquet` — a per-(day, league, venue) grain with NO `pipeline_mode=` /
`asset_group=` at all. This means:

- The 2026-07-21 writer fix (`instruments-service@a9be6ce9`, cited in the parent doc's todo 3 as covering "the writer")
  did **not** cover sports's write path — sports is still writing non-canonical, un-hived data 13 days after the ruling,
  and continues to do so as of today.
- The 7c migration tool's `_FLAT_RE` regex (`day=([^/]+)/venue=([^/]+)/(.+)`) expects `venue=` immediately after `day=`
  — it does not match `league=` in between, so every sports object in this shape is silently bucketed into
  `unrecognized shapes (ignored)` by the dry-run scan, NOT counted as a migration candidate.
- Measured impact (fresh dry-run, 2026-08-03 06:33 UTC): sports scan = 6,330 recognized flat candidates + 16,051
  already-hive + **172,595 unrecognized**. The 172,595 figure is the sports writer's entire non-canonical backlog,
  invisible to both 7c's candidate count and (per §8 of the canonical-target-ssot) the RULED target shape.

**Open design question (needs an operator/architecture ruling, not a worker judgment call):** does `league=` belong in
sports's full-hive key set as an additional trailing key (the parent issue doc's own text left "the exact trailing
keys... a design decision for the executing effort" open), or must the sports writer be changed to the ruled per-(day,
pipeline_mode, asset_group, venue) grain (rolling multiple leagues into one venue-level listing — a behavior change, not
just a path rename)? `cross-asset-canonical-target-ssot.md` §8 does not currently allow `league=` anywhere in the ruled
`instrument_availability` template.

### 2. Prediction: a second non-canonical shape (group-before-day)

`gs://instruments-store-pred-prd-.../instrument_availability/by_date/canonical_question_group=AVAX_PRICE_RANGE_DAILY/day=2026-07-13/venue=POLYMARKET/...`
— a SECOND flat shape, `canonical_question_group={G}/day={D}/venue={V}/...`, inverse-ordered from the one the migration
tool's tests DO recognize (`day={D}/venue={V}/canonical_question_group={G}/...`, confirmed handled per
`test_migrate_instrument_availability_hive_2026_08_03.py::test_prediction_polymarket_instrument_availability_uses_clob`).
Sampled dates run through 2026-07-13 — 2026-07-17 (pre-cutover; not yet confirmed whether this shape is still being
written post-2026-07-21, unlike sports's confirmed-still-live case above).

Measured impact (fresh dry-run, 2026-08-03 06:33 UTC): prediction scan (instrument_availability + market_lifecycle
combined) = 4,105 recognized candidates + 10,877 already-hive + **25,745 unrecognized**.

### 3. Cross-AG content_mismatch — flat source and an existing hive target disagree on content

The tool is correctly conservative: when the hive target path already exists, it compares (crc32c, size) against the
flat source and, on a mismatch, does **NOT** overwrite — it flags `content_mismatch` for manual review. Measured across
today's full-mode APPLY runs (real PROD writes, all other outcomes are safe/idempotent copies or verified matches):

| asset_group |     copied | already_present_verified | content_mismatch | failed |
| ----------- | ---------: | -----------------------: | ---------------: | -----: |
| cefi        |      1,571 |                    6,156 |        **1,494** |      0 |
| defi        |      3,316 |                   42,364 |       **31,315** |      0 |
| tradfi      |      7,492 |                   25,365 |           **37** |      0 |
| prediction  |      4,105 |                        0 |                0 |      0 |
| sports      |          0 |                    6,330 |                0 |      0 |
| **TOTAL**   | **16,484** |               **80,215** |       **32,846** |      0 |

All 5 asset groups reconfirmed idempotent via a second fresh full-mode run (2026-08-03 07:08-07:24 UTC): re-running
APPLY on an already-migrated bucket now reports `copied: 0` and the SAME content_mismatch count, proving every
non-mismatched recognized-shape candidate is durably present at its hive target. Total recognized-shape candidates
across the 5 buckets: 117,166 (16,484 + 80,215 + 32,846) — the residual 32,846 content_mismatch objects are the only
unresolved recognized-shape work, blocked on todo 4's operator decision above. The unrecognized-shape populations
(sports ~172,595 / prediction ~25,745) are untouched by this migration entirely — see todos 1-3.

**Root-cause sample (defi, `day=2020-05-20/venue=UNISWAP_V2-ETHEREUM`)**: the flat source (created 2026-07-09, 31,322
bytes, crc32c=`4fZjbA==`) and the existing hive target (created 2026-07-29 04:25:45 — matching the exact timestamp of
the `restore_defi_hive_instrument_availability_2026_07_29.py` GCS Soft-Delete restore documented in the parent doc's "🔴
2026-07-29 near-miss" section — 31,246 bytes, crc32c=`HUkSmA==`) are near-identical in size but genuinely different
content. This strongly suggests the restored hive objects (from an earlier, since-deleted hive population effort)
captured a slightly different instrument snapshot for that historical day than the current flat original. **This needs a
human authoritative-source decision** (does the flat or the pre-existing hive copy reflect the more complete/correct
listing for that day?) — not a mechanical fix; force-overwriting either direction without that decision risks silently
discarding real data.

## Why it matters

- Sports's writer being un-fixed means the 2026-07-21 operator HARD RULE ("every data-at-rest tree uses the full
  canonical hive grammar") is currently violated by **every sports write since the ruling**, not just historical backlog
  — this is an ongoing correctness gap, not a one-time migration debt.
- The parent doc's todo 3 ("instruments-service writer fixed... instruments-service@a9be6ce9") and the
  canonical-target-ssot §8 note ("Shipped... writer sink-prefix + reader lockstep") both read as though the writer fix
  is universal across all 5 asset groups. It is not — this needs a correction banner or scope clarification on those
  docs once the sports fix ships, to avoid a future reader trusting the "shipped" claim at face value.
- Todo 7c's completion, if reported as "465,375 objects migrated, done," would silently overstate progress: the real
  recognized-and-actionable candidate population across the 5 buckets is far smaller (cefi 7,650 + defi 73,679 + tradfi
  25,402 + prediction 4,105 + sports 6,330 ≈ 117K, not 465K — the 7b sizing counted unrecognized-shape and already-hive
  objects too, since it was a raw prefix count, not a shape classification), and ~32.8K of the resolvable candidates are
  further blocked on the content_mismatch decision above.

## Recommended decision

1. **[OPERATOR]** Rule on sports's target hive shape: either (a) amend `cross-asset-canonical-target-ssot.md` §8 to add
   `league=` as a legitimate trailing key for sports's `instrument_availability` template (matching its current
   per-league writer grain), or (b) mandate a sports writer change to roll up to the per-(day, pipeline_mode,
   asset_group, venue) grain (dropping the league split — verify no downstream reader depends on per-league availability
   listings first). This blocks both a sports writer fix AND extending the 7c tool to cover sports.
2. **[DATA]** Once (1) rules, fix the sports write path (`process_write.py` or its sports-specific caller) to emit the
   ruled shape, then extend `migrate_instrument_availability_hive_2026_08_03.py`'s `_FLAT_RE` / `hive_target_for` to
   recognize and migrate the sports `league=` shape (172,595 objects).
3. **[DATA]** Investigate whether prediction's `canonical_question_group=`-before-`day=` shape is still being written
   post-2026-07-21 (if yes, same writer-gap problem as sports, scoped to prediction); either way, extend the tool to
   recognize this second shape and migrate it (25,745 objects).
4. **[OPERATOR]** Decide the authoritative-source resolution policy for the ~32,846 cross-AG content_mismatch objects
   (defi 31,315 / cefi 1,494 / tradfi 37) — sample a handful of parquet contents (not just metadata) to determine which
   side is more complete before ruling a blanket policy (e.g., "flat original always wins" vs "hive/restored copy always
   wins" vs "always keep both, manifest points at the newer one").
5. **[REVIEW]** Once 1-4 land, correct the "Shipped... writer sink-prefix + reader lockstep" line in
   `cross-asset-canonical-target-ssot.md` §8 to scope it accurately (it covered cefi/defi/tradfi/the day-before-group
   prediction shape; NOT sports, NOT the group-before-day prediction shape) or remove the banner once truly universal.

## Todos

- [ ] 1. [OPERATOR] P1. Rule on sports's target full-hive shape for `instrument_availability` (`league=` as a trailing
      key vs. a writer grain change) — `cross-asset-canonical-target-ssot.md` §8 amendment either way (repo:
      unified-trading-pm).
- [ ] 2. [DATA] P1. Fix the sports `instrument_availability` writer to emit the ruled shape from todo 1, then extend
      `migrate_instrument_availability_hive_2026_08_03.py` to recognize + migrate the sports `league=` shape (~172,595
      objects) (repo: instruments-service). Depends on todo 1's ruling.
- [ ] 3. [DATA] P2. Investigate whether prediction's `canonical_question_group=`-before-`day=` shape is still being
      written post-2026-07-21; extend the migration tool to recognize + migrate it (~25,745 objects) (repo:
      instruments-service).
- [ ] 4. [OPERATOR] P1. Decide the authoritative-source resolution policy for the ~32,846 cross-AG content_mismatch
      objects (sample real parquet content, not just metadata, before ruling) (repo: instruments-service /
      unified-trading-pm decision).
- [ ] 5. [REVIEW] P2. Once todos 1-4 land, correct the writer-fix scope claim in `cross-asset-canonical-target-ssot.md`
      §8 (repo: unified-trading-pm). Depends on todos 1-4.
