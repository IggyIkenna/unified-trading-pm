---
doc_type: issue
title:
  sports derived_features re-run STOPPED WRITING mid-year (2018/2019/2020 ~95% still fabricated) — VM logged year-end
  frontier while writing nothing; purge BLOCKED
summary: >-
  The 2017-2020 derived_features re-run (Track F, features-service@c6eb1f38 fix) only actually rewrote 2017 in full.
  2018 wrote ~791 of ~22,077 cells (Jan-Mar sparse, Apr-Nov ZERO), 2019 wrote 181, 2020 wrote 741 — while each VM logged
  "Target fixtures on YYYY-12-31" and self-deleted as if complete. Measured by creation-time census of the features
  corpus (78,344 derived_features objects). 27,421 pre-fix (fabricated) cells remain in 2017-2020 (21,286 in 2018
  alone), plus 2,821 in 2021-2026. These are NOT honest-absence and must be REGENERATED, not purged — the Track F
  fabricated-object purge is BLOCKED until the re-run actually works.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [features-service, deployment-service, unified-trading-pm]
scope: [engineer]
tags: [sports, data-correctness, features, season-context, fabrication, ml-readiness, async-discipline]
related: [sports_derived_features_fabricated_corpus_scope_2026_07_20.md, ../sports_consolidated_closeout_2026_07_19.md]
created: "2026-07-21"
source: Track F pre-purge safety census (2026-07-21)
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

# sports derived_features re-run stopped writing mid-year — corpus still mostly fabricated

## Measured (creation-time census of the features corpus, 2026-07-21)

One features.parquet per (day, league) cell; a cell is pre-fix (fabricated, created < 2026-07-19) OR post-fix (rewritten
by the §Z-fixed re-run). Result:

| year      | post-fix cells (rewritten) | pre-fix cells (still fabricated) |
| --------- | -------------------------: | -------------------------------: |
| 2017      |                     20,079 |                                0 |
| 2018      |                        791 |                       **21,286** |
| 2019      |                        181 |                            3,965 |
| 2020      |                        741 |                            2,170 |
| 2021      |                      4,463 |                              748 |
| 2022-2026 |              (mostly post) |            199/201/169/120/1,384 |

**2018 month-by-month** proves the write-stop: Jan 510 post / Feb 30 / Mar 244 / **Apr-Nov ZERO post** / Dec 7 — the VM
wrote sparsely for three months, then logged its way to `Target fixtures on 2018-12-31` and self-deleted while writing
NOTHING for eight months.

## The async-discipline trap (again)

The four re-run VMs each reached a year-end frontier in `run.log` and self-deleted — reading as clean completion. But
the **frontier log line is activity, not an artifact**. Counting the TARGET artifacts (derived_features objects by
`time_created`) shows only 2017 actually rewrote. This is precisely the failure class CLAUDE.md warns about:
"backfill/migration progress = count of TARGET artifacts created, NEVER activity."

## Consequences

1. **The fabricated-object purge is BLOCKED.** 27,421 pre-fix cells in 2017-2020 are NOT legitimate honest-absence —
   they are fabricated objects the re-run failed to replace. Deleting them would destroy data that must be regenerated.
2. **Track F is NOT done.** The sports features corpus is still ~95% fabricated for 2018-2020. Not ML-ready.
3. **Root cause UNKNOWN** — why did 2017 (VM 131907) rewrite in full while 2018 (131925) / 2019 (063306) / 2020
   (063322), launched identically with `FORCE=1`, stop writing after ~March? Candidates: the features re-run silently
   stops writing derived_features after N days / an un-propagated `--force` for the derived_features export (cf. the §G
   finding where redo_all was plumbed to enrichment entities but not the fixtures writer) / a swallowed mid-year error /
   skip-if-fresh treating the fabricated object as fresh. Investigate the 2018 VM `run.log` around the Mar→Apr
   write-stop BEFORE relaunching — a naive relaunch will fail the same way.

## Tooling bugs also caught (both would have corrupted the purge)

- `blob.time_created` is **None** via the UTL `get_storage_client()` list_blobs path — any purge tool keying on it sees
  ZERO pre-fix objects. Creation time must come from `gcloud storage ls -l`. `purge_fabricated.py` must be fixed before
  use.
- an awk `/league=[^/]+/` regex is broken (the `/` in the class terminates the awk regex literal) — parse the listing in
  Python, not awk.

Evidence: `scratchpad/df_listing.txt` (the census listing), `scratchpad/purge_census*.{py,sh}` (2026-07-21).

## ROOT CAUSE (2026-07-21) — not a stalled VM; the features CANNOT be computed for 2018-2020

Read the 2018 VM `run.log` directly. Every day fails to write for a real, measured reason — the re-run is honest, the
INPUTS are absent:

- `calculator_season_context` produces **18 all-NaN columns** (matchday, competition_phase, games_remaining, …). This is
  the §Z fix WORKING — honest `None`, not fabricated `'late'`. But it means season-context is genuinely empty.
- `calculator_league` (24 all-NaN: positions, points, strengths), `calculator_multisource_xg` (21 all-NaN),
  `calculator_squad_value` (5-6 all-NaN), `calculator_halftime` (15 all-NaN) — the **upstream fixture data (results,
  standings, xG, squad values) is MISSING for 2018**, so every derived feature is NaN.
- `batch_feature_quality_gate`: "Feature output for 2018-01-0N has 83-84 all-NaN columns (recovery=skip)".
- **`AvailableAtStampingError: available_at stamping (post_match) produced all-NaT result; every row's source timestamp is missing or unparseable. Stamping midnight UTC would mask this; raising instead.`**
  — RAISES (Traceback), aborting the day's write. This is why most 2018 days never wrote and the fabricated pre-fix
  object survived.

**Reframing:** the fabricated `derived_features` for 2018-2020 were FAKE values hiding a genuine upstream-data absence.
The remediation is NOT "relaunch the re-run" — a relaunch fails identically. It is a foundation-gate problem:

1. **Establish whether the 2018-2020 upstream fixture data (results / standings / xG / event timestamps) SHOULD exist**
   (i.e. api-football / footystats / understat coverage for those seasons) and, if so, backfill it FIRST. If it
   genuinely does not exist, then 2018-2020 derived_features are **honest-absent** and the fabricated objects should be
   DELETED (the purge becomes correct) — but only after that is confirmed per-league, not assumed.
2. **Fix the write-abort behavior**: `AvailableAtStampingError` raising on all-NaT means a day with no parseable source
   timestamp produces NO output at all (not even an honest-absence marker). Decide the honest contract —
   skip-with-record vs raise — so the pipeline distinguishes "computed empty" from "crashed".
3. Why did 2017 write in full while 2018-2020 did not? Almost certainly 2017 upstream coverage is more complete — verify
   by checking upstream fixture-results availability per year.

This is a **foundation-completion-gate** issue (derived_features depend on fixture results/standings/xG); it freezes the
Track F purge AND the "ML-ready" claim for sports 2018-2020 until the upstream layer is confirmed/backfilled.
