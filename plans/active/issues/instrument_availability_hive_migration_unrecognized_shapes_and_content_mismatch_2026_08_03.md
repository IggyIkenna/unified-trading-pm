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
    /plans/archive/issues/instrument_availability_hive_canonicalisation_2026_07_21.md,
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
    /plans/archive/issues/instrument_availability_hive_canonicalisation_2026_07_21.md,
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

### 4. Prediction: a third, even older non-canonical shape (`market=`, ~12,463 objects)

Investigating todo 3 (the `canonical_question_group=`-before-`day=` shape) confirmed via a live GCS sample that it — and
a second, previously-undocumented shape, `market_lifecycle`'s `day={D}/group={G}/venue={V}/...` (venue THIRD, not
immediately after `day=`, so it never matched `_FLAT_RE` either) — both stopped being written at
**2026-07-22T00:37:29Z**, the last batch run before the `a9be6ce9` writer-fix deploy (03:20:56Z same day). Neither is
still being written post-2026-07-21. Both are now recognized + migratable (`instruments-service@aaa0866c`); a live
dry-run for `asset_group=prediction` confirms `unrecognized` drops from 25,745 to **12,463**.

The residual 12,463 is a **third**, even older flat shape found while classifying the leftover unrecognized objects:
`instrument_availability/by_date/day={D}/market={M}/venue={V}/...` (e.g. `market=BTC`/`market=ETH`/`market=OTHER`),
sampled from as far back as 2025-03. Unlike the `league=`/`group=` cases above, this is **not a safe mechanical path
rename**:

- A content sample (`day=2025-03-15/market=BTC/venue=POLYMARKET/instruments.parquet`, downloaded + parsed) has **no
  `canonical_question_group` column at all** — this shape predates the canonical-group bundling scheme entirely.
- `market=BTC` is a coarser bucket than any single `canonical_question_group` — the sampled file's `raw_symbol`s (e.g.
  `bitcoin-up-or-down-on-march-15-noon`) correspond to what is now `BTC_UP_DOWN_DAILY`, but the SAME `market=BTC` file
  could plausibly also hold rows belonging to `BTC_UP_DOWN_HOURLY` / `BTC_PRICE_RANGE_DAILY` / etc. — there's no per-row
  column to split on today, so a correct migration would need to re-derive `canonical_question_group` per row via
  `_extract_prediction_canonical_group` (or an equivalent), not just rewrite the path.

This needs the same kind of operator/architecture ruling todo 1 required for sports `league=` — see todo 8 below.

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

- [x] ✅ 1. [OPERATOR] P1. **RULED 2026-08-03 — option (a): `league=` is a legitimate trailing key.** Operator ruling:
      "League= yes" — add `league=` to sports's `instrument_availability` canonical key set as an additional trailing
      key (appended after `venue=`, before the leaf file), keeping the writer's existing per-league split rather than
      rolling it up to a per-venue grain. `cross-asset-canonical-target-ssot.md` §8 amended (sports-exception banner) +
      §11c decision log entry added (repo: unified-trading-pm). `migration_pending` — unblocks todo 2 below.
- [x] ✅ 2. [DATA] P1. Fix the sports `instrument_availability` writer to emit the ruled shape from todo 1 (trailing
      `league=`, plus the still-missing `pipeline_mode=`/`asset_group=` keys), then extend
      `migrate_instrument_availability_hive_2026_08_03.py` to recognize + migrate the sports `league=` shape (~172,595
      objects) (repo: instruments-service). Todo 1's ruling is now resolved — no longer gated. —
      instruments-service@ba87cc32: `_write_sports_fixture_venue` now writes via `_instrument_availability_sink_for`
      (full-hive prefix) with `league=` as a trailing partition key after `venue=`; migration tool's `hive_target_for`
      extended with `_SPORTS_LEAGUE_FLAT_RE` to recognize + map the legacy `day=/league=/venue=` flat shape to its hive
      target. 125 targeted unit tests green (incl. new regression coverage for both the writer's sink call args and the
      migration tool's sports-league mapping); full QG green. **Caveat found 2026-08-03 while working todo 5 below: the
      code is shipped to `live-defi-rollout` but NOT YET confirmed live in production** — a live GCS check 23 min after
      the merge still showed the old flat shape (`ba87cc32` had not yet reached `main`, and the
      `uts-prod-instruments-service-sports-fixtures` Cloud Run Job pins an image built from `main`) — see todo 9.
- [x] ✅ 3. [DATA] P2. **Investigated 2026-08-03 — NOT still being written; extended + shipped.** Live GCS confirms the
      `canonical_question_group=`-before-`day=` shape's last write was 2026-07-22T00:37:29Z, the batch run immediately
      before the `a9be6ce9` writer-fix deploy (03:20:56Z same day) — it stopped exactly at cutover, same as sports's
      shape. Extended `migrate_instrument_availability_hive_2026_08_03.py`'s `hive_target_for()` with
      `_PREDICTION_GROUP_FIRST_FLAT_RE` to recognize + migrate it, PLUS an adjacent second legacy shape found during the
      same investigation (`market_lifecycle`'s `day=/group=/venue=` — venue third, never matched `_FLAT_RE` either, same
      2026-07-22T00:37:29Z cutover) via `_PREDICTION_LIFECYCLE_DAY_GROUP_VENUE_FLAT_RE`. 8 new targeted unit tests
      (hive_target_for + scan, both shapes × both venues + cross-asset-group non-recognition guards); full QG green.
      Live dry-run: prediction `unrecognized` 25,745 → 12,463 (residual is a third, older `market=` shape — see the new
      §4 finding above and todo 8 below, NOT part of this todo's scope). — instruments-service@aaa0866c.
- [x] ✅ 4. [OPERATOR] P1. **RULED 2026-08-03 — per-pair "superset wins", NOT a blanket flat-always/hive-always rule.**
      Sampled real parquet CONTENT (downloaded + parsed via pandas/pyarrow, not just crc32c/size metadata) for 10 pairs
      spread across all 3 affected asset_groups and the full 2019–2026 date range (tradfi ×3, cefi ×3, defi ×4; PROD
      buckets, read-only). Live evidence + methodology in
      `instruments-service/scripts/{sample_content_mismatch,sample_content_mismatch_offsets,compare_content_v2}.py`
      (scratchpad copies retained by the sampling worker; not committed — reproducible from the tool sequence described
      below).

      **Methodology gotcha caught mid-sample (material to the ruling): `instrument_key` is NOT a stable identity
                      column across writer generations** — e.g. `DERIBIT:FUTURE:BTC-27SEP19` (flat, older key format) vs
                      `DERIBIT:FUTURE:BTC@INV-20190927` (hive, newer key format) are the SAME instrument (`raw_symbol=BTC-27SEP19`
                      both sides). Comparing on `instrument_key` alone falsely reads as 100% disjoint; `raw_symbol` (+
                      `contract_symbol` for tradfi futures) is the stable cross-generation identity key and is what the table below
                      uses.

                      | asset_group | venue | day | flat rows | hive rows | relationship (by `raw_symbol`) |
                      |---|---|---|---:|---:|---|
                      | tradfi | CME | 2020-01-02 | 154 | 154 | tied (full overlap) |
                      | tradfi | CME | 2026-06-28 | 32 | 216 | **hive is a strict superset** — flat missing 184 real contracts |
                      | tradfi | NYSE | 2026-07-22 | 535 | 535 | tied (full overlap) |
                      | cefi | DERIBIT | 2019-03-31 | 6 | 312 | **hive is a strict superset** — flat missing 306 real DERIBIT options |
                      | cefi | BITFINEX-SPOT | 2023-12-16 | 284 | 284 | tied (full overlap) |
                      | cefi | DERIBIT-COMBO | 2026-06-04 | 568 | 31 | **flat is a strict superset** — hive missing 537 instruments |
                      | defi | UNISWAP_V2-ETHEREUM | 2020-05-20 | 11 | 9 | **flat is a strict superset** — hive missing 2 (root-cause sample from "What I found" §3 above) |
                      | defi | AAVE_V3-AVALANCHE | 2022-06-01 | 8 | 8 | tied (full overlap) |
                      | defi | AERODROME_V3-BASE | 2024-06-01 | 12 | 12 | tied (full overlap) |
                      | defi | AAVE_V3-ETHEREUM | 2026-06-27 | 36 | 36 | tied (full overlap) |

                      **Finding: in all 10/10 sampled pairs, the smaller side's instrument set is a clean SUBSET of the larger
                      side's — zero genuinely-irreconcilable (mutually-exclusive) divergence once compared on the stable identity
                      key.** 6/10 tied, 2/10 hive strictly more complete, 2/10 flat strictly more complete. This rules out BOTH
                      blanket options (a) and (b) from the original menu — either would silently discard real, verified-present
                      instrument rows in ~40% of sampled cases, which is exactly the risk the original finding warned about
                      ("force-overwriting either direction... risks silently discarding real data"). It also rules out a *naive*
                      "newest GCS write wins" reading of option (c): the tradfi CME 2026-06-28 pair shows flat's GCS write is ~1 day
                      NEWER than hive's yet flat has 184 FEWER contracts — a newer write was measurably worse there, so recency
                      alone is not a safe completeness proxy.

                      **RULED POLICY (refined option (c))**: per-object, resolve content_mismatch by **completeness** (superset by
                      `raw_symbol`/`contract_symbol` identity), not by side-label or timestamp:
                      - One side's instrument set ⊇ the other's → the superset side's content is authoritative; the migration
                        target ends up holding the superset side's bytes (whichever original path had them).
                      - Sets are equal-membership but bytes still differ (schema_version / column-order / float-precision drift,
                        the tied rows above) → no data-loss risk either way; default to the flat side's bytes for the hive target
                        (keeps single-writer provenance, matches the tool's existing copy direction, avoids a special case).
                      - (Not observed in this sample, but keep as a backstop) neither side is a superset of the other (genuinely
                        disjoint, non-overlapping instruments on both sides) → do NOT auto-resolve; flag for manual per-object
                        review/union. 0/10 sampled pairs hit this case, so it is expected to be rare, not the common path.

                      **Separate finding surfaced by this same sampling, NOT a migration-policy question — flagged as todo 7
                      below**: the cefi DERIBIT 2019-03-31 pair shows the CURRENT flat writer's own most recent rewrite of that
                      historical day (GCS write 2026-07-13) is missing all 306 options a same-day-but-earlier hive copy has — i.e.
                      the live backfill/reconciliation path that re-generates historical `instrument_availability` snapshots may
                      have a real option-coverage regression, independent of which side wins this migration's copy-up.

- [x] ✅ 5. [REVIEW] P2. **Corrected 2026-08-03.** `cross-asset-canonical-target-ssot.md` §8's sports-exception banner
      updated to record `ba87cc32`'s writer fix + tool extension as shipped, WITH the deploy-lag caveat found while
      doing this correction (code shipped to LDR, not yet confirmed live — see todo 9); added a parallel banner for
      prediction's two additional shapes (`aaa0866c`, todo 3) noting the residual `market=` shape is pending todo 8's
      ruling. `canonical-cutover-register.md` §6b's "live writer" row + "Residual" paragraph updated in lockstep (same
      overclaim risk, cross-linked doc) — repo: unified-trading-pm.
- [ ] 9. [DATA] P1. Verify `instruments-service@ba87cc32` has reached `main`
      (`git merge-base --is-ancestor ba87cc32     origin/main`) and the `uts-prod-instruments-service-sports-fixtures`
      Cloud Run Job is running an image built after it
      (`gcloud run jobs executions describe <latest> --format='value(...containers[0].image)'` vs
      `gcloud     artifacts docker images list ... --sort-by=~UPDATE_TIME`); if confirmed live, run a fresh dry-run +
      apply the sports historical-backlog migration (~172,595 objects, `--asset-group sports`) and update
      `canonical-cutover-register.md` §6b's "live writer" + "Residual" rows to reflect the confirmed-live + migrated
      state. If `main` is still behind, do NOT force-promote — this repo's LDR→main pipeline is normally automatic
      (`*/15` fleet promote); if still stalled past a reasonable window, this is the documented "v2-never-reported
      deadlock" class (`/codex/08-workflows/ci-cd-flow.md`) which auto-recovers via
      `ci-failure-watcher     --auto-recover` — do not manually escalate for that specific pattern (repo:
      instruments-service + unified-trading-pm). **Attempt 2026-08-03T10:20Z — still NOT confirmed live, correctly held
      (no force-promote, no escalation).** `git merge-base --is-ancestor ba87cc32 origin/main` fails: `main` is 767
      commits behind `live-defi-rollout` (LDR HEAD `f1403733`, `ba87cc32` landed on LDR at 08:48:16Z). Root cause traced
      via the PM fleet promote workflow's own log (`ldr-to-main-promote-fleet.yml` run 30803757306, 10:00Z tick):
      `GATE BLOCK     instruments-service: ci_status=FAILING (cached='SIT_VALIDATED', live='FAILING')` — the
      dep-order/LDR-green gate refuses to open a new promote PR while `live-defi-rollout`'s own `quality-gates-v2` isn't
      reporting green. The last _completed_ v2 run on LDR failed at 00:33:18Z (SHA `e793331`, `qg_red_reason: pytest`) —
      22 commits (incl. `ba87cc32` and several later `fix(...)` commits) have landed since, but every intervening v2 run
      was `cancelled` (superseded by the next push, ordinary concurrency-group behavior) before it could re-confirm
      green, so whether LDR is genuinely still red or just never got a chance to re-verify is unknown. The current run
      (workflow_dispatch `30800087100`, started 09:07:46Z) is not superseded and is still progressing, but its two
      `self-hosted, glue`-labelled QG-slice jobs have sat `queued` for 1h10m+ — the repo (`gh api .../actions/runners`)
      has exactly ONE registered `glue` runner, currently `busy`, i.e. a single shared runner is serializing QG-slice
      jobs across the whole multi-repo fleet, not an instruments-service- specific problem. This matches the documented
      "v2-never-reported"/stuck-promote class this todo already calls out as self-recovering — did NOT force-promote,
      did NOT open a manual escalation, did NOT run the sports migration (writer fix not yet confirmed live in prod, so
      applying now would only need a repeat pass once it is). Todo left **unchecked** for re-verification on a future
      dispatch once LDR's v2 actually completes and the fleet promote picks `ba87cc32` up.
- [ ] 6. [DATA] P2. Implement todo 4's ruled per-object "superset wins" resolver and run it across the ~32,846
      content_mismatch objects (defi 31,315 / cefi 1,494 / tradfi 37): for each pair, download + parse both parquets,
      compare by `raw_symbol` (+ `contract_symbol` for tradfi futures/futures_contracts) identity set, write the
      superset side's bytes to the hive target (flat's bytes on a tie), and log any pair where neither side is a
      superset of the other to a follow-up review list instead of auto-resolving it. Re-run the migration tool's dry-run
      afterward to confirm `content_mismatch` drops to (ideally) 0, or to the size of that review list (repo:
      instruments-service). Depends on todo 4.
- [ ] 7. [DATA] P2. Investigate the cefi DERIBIT options-coverage gap surfaced by todo 4's sampling: the flat
      `instrument_availability` object for day=2019-03-31/venue=DERIBIT was rewritten 2026-07-13 and contains 0 OPTION
      rows, while a hive-shape copy from the same day has 306 — determine whether this is isolated to that one (day,
      venue) or a systemic gap in the historical-backfill/reconciliation path for DERIBIT options, and fix the
      writer/backfill if systemic (repo: instruments-service).
- [ ] 8. [OPERATOR] P2. Rule on prediction's third legacy shape surfaced by todo 3's investigation:
      `instrument_availability/by_date/day={D}/market={M}/venue={V}/...` (`market=BTC`/`ETH`/`OTHER`, ~12,463 objects,
      sampled from 2025-03 — see §4 in "What I found" above). This shape predates the `canonical_question_group`
      bundling scheme (confirmed via content sample: no `canonical_question_group` column) and is a COARSER bucket that
      can span multiple canonical groups per file — unlike sports `league=`, this is not a safe structural rename.
      Options: (a) content-level reclassify each row into today's `canonical_question_group` grain (mirrors
      `_extract_prediction_canonical_group`) before migrating, (b) preserve `market=` as its own distinct trailing key
      (parallel taxonomy to `canonical_question_group=`, alongside it — may confuse downstream readers expecting one
      canonical grain), or (c) treat this ~2025-03-era snapshot as superseded by later, correctly-bundled data and
      exclude it from the 7c migration (verify no downstream reader still depends on it first). Blocks extending the
      migration tool for this residual shape (repo: instruments-service).
