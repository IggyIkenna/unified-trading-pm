---
doc_type: issue
title:
  §Z fabricated derived_features is corpus-wide (35,045 parquet objects, 100% of pre-fix) — re-run scope missed
  2017/2018 and cannot self-heal
summary: >-
  A creation-time census of all 124,554 derived_features objects plus a 250-object stratified content sample shows the
  §Z season_context fabrication affects 100% of every derived_features parquet written before the c6eb1f38 fix — 35,045
  files across 2017-2026. Two structural gaps: (a) the re-run scope was 2019→present, so 2017+2018 (26,089 files, incl.
  the single largest year) were never in scope; (b) `--force` only overwrites days the re-run PRODUCES output for, so
  stale fabricated objects survive on days that yield nothing. Supersedes the earlier "2021-2026 CLEAN" verdict, which
  sampled only rewritten days.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [features-service, unified-trading-pm]
scope: [engineer]
tags: [sports, data-correctness, features, season-context, fabrication, ml-readiness, backfill]
related: [../sports_consolidated_closeout_2026_07_19.md, ../sports_consolidated_audit_2026_07_19.md]
created: "2026-07-20"
source: sports_consolidated_closeout_2026_07_19.md Track F corpus census (2026-07-20)
resolved_by:
locked_by:
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P0
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
---

# §Z fabricated `derived_features` is corpus-wide, and the re-run cannot self-heal it

## What was measured (2026-07-20)

**Census** — one walk of `gs://features-sports-prd-central-element-323112/sports_features/by_date/**`, bucketing every
`feature_group=derived_features` object by GCS creation time against the §Z fix (`features-service@c6eb1f38`,
2026-07-19):

| data year | POST-FIX objects | PRE-FIX objects (suspect) |
| --------- | ---------------: | ------------------------: |
| 2017      |                0 |                     8,024 |
| 2018      |                0 |                    44,154 |
| 2019      |              362 |                     7,930 |
| 2020      |            1,482 |                     4,340 |
| 2021      |            8,926 |                     1,496 |
| 2022      |            7,406 |                       398 |
| 2023      |            6,214 |                       402 |
| 2024      |           10,112 |                       338 |
| 2025      |            7,626 |                       240 |
| 2026      |           12,336 |                     2,768 |
| **total** |       **54,464** |                **70,090** |

**Content sample** — 25 randomly-sampled `.parquet` objects per year from the pre-fix set (deterministic seed; 250
objects; fabrication signature = `competition_phase` single-valued across the sample AND `matchday` all-null):

| year | sampled | fabricated | clean | rate     | pre-fix parquet population |
| ---- | ------: | ---------: | ----: | -------- | -------------------------: |
| 2017 |      25 |         25 |     0 | **100%** |                      4,012 |
| 2018 |      25 |         25 |     0 | **100%** |                     22,077 |
| 2019 |      25 |         24 |     1 | 96%      |                      3,965 |
| 2020 |      25 |         25 |     0 | **100%** |                      2,170 |
| 2021 |      25 |         25 |     0 | **100%** |                        748 |
| 2022 |      25 |         25 |     0 | **100%** |                        199 |
| 2023 |      25 |         25 |     0 | **100%** |                        201 |
| 2024 |      25 |         25 |     0 | **100%** |                        169 |
| 2025 |      25 |         25 |     0 | **100%** |                        120 |
| 2026 |      25 |         25 |     0 | **100%** |                      1,384 |

**Overall fabrication rate among decidable pre-fix samples: 100%** (249/250). "Pre-fix" is therefore not merely
_suspect_ — it is _fabricated_, and the affected population is **35,045 parquet objects**.

## The two structural gaps

**Gap 1 — the re-run scope never included 2017/2018.** Track F specifies "2019→present". The corpus actually starts
`day=2017-02-02`. So 26,089 fabricated parquet files (2017: 4,012 + 2018: 22,077) — **2018 is the single largest year in
the corpus** — were never in scope for remediation and remain fabricated.

**Gap 2 — `--force` cannot heal a day that yields no output.** `--force` overwrites what the run _produces_; where the
run produces nothing for a day, the pre-existing fabricated object survives untouched. Directly observed: the 2019 VM
passed `day=2019-04-20` at ~12:42Z (it was at 2019-04-28 by then) and that day's 11 `derived_features` objects remain
100% `'late'` with `matchday` all-null, still carrying their original pre-fix creation timestamp. This is the same
overwrite-blind class already recorded as § AA.

This is why the 2019 VM had written only 3 days' output (01-04, 01-09, 03-02) after six hours while 2020 had written
~105 contiguous days — **not** a stall, and **not** skip-if-fresh (both VMs carry identical `--force` parameters,
verified from instance metadata). 2019 simply has far fewer days that produce output.

## Correction to the record

The closeout plan's Track F states **"VERIFIED 2026-07-19/20 (corpus-wide, not just pilot): 2021-2026 CLEAN"**. That
verdict is **overstated**. It was reached by sampling days, and the sampled days were ones the re-run had rewritten. The
census shows 2021-2026 still holds **2,821 fabricated pre-fix parquet objects** (748+199+201+169+120+1,384). The years
are _mostly_ clean, not clean.

## Required remediation (none of it optional — this is training data)

1. **Extend the re-run to 2017+2018** — the largest fabricated block, never in scope.
2. **Purge, don't just overwrite.** After the re-runs, every `derived_features` parquet still carrying a pre-fix
   creation timestamp is fabricated by measurement and must be DELETED. Honest absence beats a fabricated
   `competition_phase` (`/codex/02-data/honest-absence-downstream-handling.md`) — a day that legitimately produces no
   output should have no object, not a stale invented one.
   - The bucket has GCS soft-delete enabled (7-day window), so the purge is recoverable; snapshot the delete list
     regardless.
3. **Re-verify by census, not by sampling** — the re-check is "zero pre-fix-dated `derived_features` objects remain",
   which is decidable from object metadata alone and cannot be fooled by which days happened to be sampled.

## Why this is ML-blocking

`competition_phase` and `matchday` feed season-context features. A constant `'late'` across an entire season is not a
weak feature, it is an actively wrong one, and it is currently present in 100% of pre-fix rows — including the whole of
2017 and 2018. Per `/codex/02-data/data-pipeline-correctness-hard-rule.md` this freezes downstream ML work on sports
until the corpus is clean.

Evidence: `scratchpad/corpus_walk.sh`, `scratchpad/fab_rate.py`, `scratchpad/check_2019_fab.py` (2026-07-20).
