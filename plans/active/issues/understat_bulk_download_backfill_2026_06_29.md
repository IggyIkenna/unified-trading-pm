---
doc_type: issue
title:
  Understat bulk-download backfill — replace the slow date-by-date VM crawl with league×season batch pulls
  (instruments-service, 2026-06-29)
summary: "The understat xG backfill ran date-by-date on a multi-day SPOT VM and (separately) captured ZERO shot-level
  data because the adapter hit a dead endpoint. The shot-endpoint bug is fixed and shipped; this issue captures the
  design for a BULK downloader: understat serves a whole league-season in one getLeagueData call, so we iterate
  league×season (5 leagues × ~12 seasons) for match-level XG and pull per-match shots from getMatchData — minutes, not
  days. Data + manifest must be written in the IDENTICAL shape to the sequential backfill (same GCS path, same
  record_captured row atom). Nothing is written to GCS until the operator confirms the save path.

  "
status: open
nature: design
asset_group:
  [sports] # corrected 2026-07-25 (ag-closeout-audit orthogonality fix) -- was [cross-cutting], a genuine mistag: this
  # is an Understat (football/soccer xG data provider)-specific backfill for 5 sports leagues, not a generic
  # reusable cross-AG backfill pattern -- every endpoint/registry/data type here is sports-specific

stage: [data, meta]
repos: [instruments-service, unified-api-contracts, unified-trading-library, deployment-api]
scope: [engineer]
tags: [sports, understat, xg, backfill, manifest]
related:
  [
    sports_p2_history_reference_and_odds_2015_to_present_2026_06_27,
    sports_p1_golden_window_reference_sources_2026_06_27,
  ]
created: 2026-06-29
parent_epic: infrastructure_master
priority: P1
source:
  [
    "2026-06-29 operator-directed investigation (interactive session, slot-16 claimed): understat-vm-xg-complete gate
    stuck; XG_SHOTS captured=0 across all history",
    instruments-service@527b9d9 — get_match_shots endpoint fix (/getMatch → /getMatchData),
  ]
assigned_vm:
resolved_by:
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_since: 2026-05-21
---

# Understat bulk-download backfill

> **Working agreement (operator, 2026-06-29):** write this doc first; then verify the download + save path locally in
> slot-16; **do NOT write any data to GCS / touch the manifest until the operator confirms.** The running date-by-date
> VM (`us-backfill-20260628-070120`) was deleted on 2026-06-29; do not relaunch it.

## 1. Background / why this exists

- The date-by-date understat backfill VM crawled one calendar date at a time (2014→present), ETA ~3 days.
- Independently, **shot-level data (`XG_SHOTS`) was never captured for any date** (`captured=0`): the adapter called
  `GET /getMatch/{id}`, which upstream removed (now 404s for every id). The 404 was silently absorbed as honest-absence
  → hollow data that would have let the `understat-vm-xg-complete` gate flip on empty shots.
- **Fixed + shipped** (`instruments-service@527b9d9`): `get_match_shots` now reads `GET /getMatchData/{id}` (`shots`
  key); `_parse_shot_from_raw` maps `shotType` (was the always-`None` `type` key). Verified live: real shots returned
  for matches across 2014–2024.
- **This issue** is the faster replacement for the crawl: understat serves a whole league-season in one call.

## 2. What we must capture — registry SSOT (do NOT miss any)

SSOT: `unified-api-contracts/unified_api_contracts/canonical/domain/sports/league_data.py`.

| Item                      | Value                                                       | SSOT line                                 |
| ------------------------- | ----------------------------------------------------------- | ----------------------------------------- |
| Data types from understat | **`XG`, `XG_SHOTS`** (only these two)                       | `SPORTS_DATA_TYPE_TO_SOURCE` :174–175     |
| Leagues (native)          | **EPL, LA_LIGA, BUNDESLIGA, SERIE_A, LIGUE_1** (big-5 only) | `SPORTS_SOURCE_LEAGUE_ALLOWLIST` :240–242 |
| Coverage start            | **2014-01-01** (source-wide, no per-data_type override)     | :71–87                                    |

> **SCOPE CONFIRMED (operator, 2026-06-29): XG + XG_SHOTS ONLY.** `getLeagueData` also returns `players` (570/season)
> and `teams` (20/season) aggregates, and an OLD rich 13-table CSV dump exists in
> `football-raw-data-all-sources/understat/` (2026-02-05) — but **that bucket is DEPRECATED / no longer used**, and the
> live system tracks only XG + XG_SHOTS. So bulk scope = exactly the two live, manifest-tracked types.

## 3. The bulk endpoints (verified live 2026-06-29)

| Endpoint                               | Returns                                                           | Covers                           | Throughput (measured)                              |
| -------------------------------------- | ----------------------------------------------------------------- | -------------------------------- | -------------------------------------------------- |
| `GET /getLeagueData/{league}/{season}` | `{teams, players, dates}` — `dates` = all matches' match-level xG | one whole league-season → **XG** | 0.70 s/call → 5 leagues × ~12 seasons ≈ **<1 min** |
| `GET /getMatchData/{match_id}`         | `{rosters, shots, tmpl}` — `shots = {h:[...], a:[...]}`           | one match → **XG_SHOTS**         | 0.29 s/call; match ids come free from `dates`      |

- Headers: browser UA + `X-Requested-With: XMLHttpRequest`; warm a cookie on `/` first. No API key.
- `getLeagueData` gzip; use a client that auto-decodes (httpx does).
- Total matches ≈ 19k (5 leagues × ~12 seasons). Serial shots ≈ 90 min; **~5–10 min at modest concurrency.**
- So: **iterate league × season for XG (≈55 calls); drive XG_SHOTS off each season's match ids.** This matches the
  operator's recollection — one league-season call yields all match-level data.

## 4. Save path + manifest contract — bulk MUST equal sequential

Both data types are written + recorded by `instruments-service/.../engine/orchestrator/understat.py`
(`_fetch_understat_xg` → XG; `_run_understat_shots_date` → XG_SHOTS). **Reuse these helpers — do not hand-roll paths.**
Verified the actual on-disk layout: the `"league"` partition key is a column/manifest key, **NOT a path segment** (real
path is `entity=understat_xg/understat_xg.parquet`, no `league=` subdir).

| Field                         | XG                                                                                                                         | XG_SHOTS                                                    |
| ----------------------------- | -------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| capture fn                    | `_fetch_understat_xg`                                                                                                      | `_run_understat_shots_date`                                 |
| sink                          | `_sports_ref_sink_for(bucket, date, "understat_xg")`                                                                       | `_sports_ref_sink_for(bucket, date, "understat_xg_shots")`  |
| entity                        | `understat_xg`                                                                                                             | `understat_xg_shots`                                        |
| GCS path (verified)           | `gs://{bucket}/sports_reference/by_date/day={date}/pipeline_mode=batch_understat/entity=understat_xg/understat_xg.parquet` | `…/entity=understat_xg_shots/understat_xg_shots.parquet`    |
| `record_captured` row_key     | `{"date": date, "data_type": "XG", "league_id": lid}`                                                                      | `{"date": date, "data_type": "XG_SHOTS", "league_id": lid}` |
| asset_group / instrument_type | `sports` / `""`                                                                                                            | `sports` / `"shot"`                                         |
| pipeline_mode                 | `BATCH_UNDERSTAT` (`"batch_understat"`)                                                                                    | same                                                        |
| source                        | `_sports_ref_source("understat_xg")` → `"understat"`                                                                       | `_sports_ref_source("understat_xg_shots")` → `"understat"`  |
| **manifest atom**             | **per `(date, league_id, data_type)`**                                                                                     | **per `(date, league_id, data_type)`**                      |
| honest-absence                | `record_empty(EXPECTED_NO_FIXTURE)` / `record_expected_empty(EXPECTED_PRE_SOURCE_COVERAGE_START                            | EXPECTED_PAUSED_LEAGUE)`                                    | same |
| failure                       | `record_failed(error=<classified>)`                                                                                        | same                                                        |

**Implication for the bulk writer:** the bucket = `instruments-store-sports-{project}`. The atom is per
`(date, league, data_type)`, but the bulk fetch is per `(league, season)`. So the writer must **group the season payload
by calendar date**, and for each `(date, league)` emit one XG row and one XG_SHOTS row (shots aggregated from all of
that date's matches in that league) — exactly as the sequential path does per date.

## 5. Manifest correctness — the falsely-empty XG_SHOTS rows

- Live manifest (verified 2026-06-30 via `read_availability_index`): `XG_SHOTS` = 288,284 `empty_confirmed` + 13,781
  `expected_unattempted` + 392 `attempted_failed` + **9 `captured`** (the 9 are the 2024-12-14/21 validation writes; the
  doc previously said `captured=0`). Almost all the `empty_confirmed` is FALSE — shots exist upstream.
- **PROOF the emptiness is false (understat, per `(league, date)`):** 4,436 league-dates have real XG captured but only
  **9** have XG_SHOTS captured; on **≥1,675** of the _exact same_ XG-captured dates XG_SHOTS is recorded
  `empty_confirmed` — impossible, since every match's xG total is built from shot events. The dead `/getMatch`
  endpoint's `[]` was absorbed as honest-absence. A naive idempotent re-run **skips** these (log: "skipping date — all 5
  expected leagues per-league captured"), so it would NOT backfill.
- **Coverage-tab blind spot (new finding, 2026-06-30):** the deployment-ui Data Status tab NEVER shows XG_SHOTS — it is
  absent from `SPORTS_DATA_TYPE_META` (`deployment-api/.../data_status/sports_helpers.py`), so the build loop filters it
  out. And for SPORTS the tab's headline is _attempt_ coverage (`(captured+empty+failed)/expected`), which counts the
  false-empties as successful attempts → the broken type reads green via its healthy sibling (XG at 99% is genuine)
  while being invisible. So the tab did not — and structurally cannot — surface this gap. Register XG_SHOTS in
  `SPORTS_DATA_TYPE_META` so coverage tracking sees it.
- The bulk writer must therefore **force-overwrite** those rows to `captured` (last-write-wins) — i.e. write with the
  force/overwrite path, not the skip-if-present path.
- **OPEN Q2:** confirm the consolidator's last-write-wins dedup will promote `empty_confirmed → captured` on a re-write
  of the same row_key (expected yes), and whether any `expected_unattempted` rows need an explicit reseed first. Verify
  on a single (date, league) before any bulk run.

## 6. Proposed approach (design — not yet built)

1. **Fetcher** (new, fast, concurrent): for each `league ∈ 5`, `season ∈ 2014…current`: `getLeagueData` → group `dates`
   by calendar date → per-match `getMatchData` for shots (bounded concurrency).
2. **Writer**: feed the grouped per-`(date, league)` data into the **existing** `_sports_ref_sink_for` +
   `record_captured` path (reuse, don't reimplement) so GCS + manifest shape is byte-identical to sequential.
   Honest-absence/off-season/coverage guards stay (reuse the same `record_empty`/`record_expected_empty`).
3. **Run locus:** slot-16 (claimed/paused) for the prototype + a dry-run that writes NOTHING; a real run target (local
   vs a short-lived VM) is an operator decision — **NOT the old date-by-date VM.**
4. **Verify:** after a single-(date,league) write, confirm GCS path + parquet rows + manifest row promoted to
   `captured`; then scale.

## 7. Decisions + open questions

- **Q1 — RESOLVED (operator 2026-06-29):** scope = **XG + XG_SHOTS only**. The rich 13-table dump lives in the
  **deprecated** `football-raw-data-all-sources/understat/` bucket (no longer used); do not reproduce it.
- **Q3 — RESOLVED:** work + validate in **slot-16** (claimed/paused). Real-run locus decided later (not the crawler VM).
- **Q4 — DEFERRED by sequence (operator 2026-06-29):** validate the bulk approach FIRST (save to GCS + manifest), THEN
  decide whether the existing capture fns can adopt it without large changes — else keep a **standalone script**.
- **Q2 — I will verify:** confirm last-write-wins promotes `empty_confirmed → captured` on re-write of the same row_key;
  reseed `expected_unattempted` if needed. Verify on a single (date, league) before any bulk run.

## 8. Todos

- [x] [DATA] P1. Confirm download path — read-only prototype validated `getLeagueData` (match-XG, 0.7s/call) +
      `getMatchData` (shots, 0.29s/call); EPL/2023 = 380 matches/120 dates. Also confirmed bulk == stored: XG download
      byte-exact to GCS for 2023-03-11 (24/24) + 2024-12-14 (20/20), 0 xG mismatches → idempotent. §3.
- [x] [DATA] P0. Save path confirmed with operator — paths/manifest atom resolved via existing helpers; operator
      approved a small validation write. §4.
- [x] [DATA] P1. Validation write + consolidator test (2024-12-14, then 2024-12-21) — **surfaced 3 layered manifest
      bugs, see §9.** The consolidator does NOT promote captured over seed cleanly.
- [x] [CODE] P0. instruments-service `understat.py` — XG_SHOTS `record_captured` `instrument_type="shot" → ""` to match
      the existing rows + XG + sports convention. §9.1. **SHIPPED `instruments-service@4281a01db`** (LDR); QG green
      (108s); no test pinned `"shot"`.
- [x] [CODE] P0. **UTL manifest NULL-vs-`''` dedup bug (§9.2) — fix BOTH layers.** `record_captured` now serializes
      unset optional dedup dims as `NULL` (`_records_to_dataframe`, forward-fix) AND `manifest_consolidator` treats
      `NULL == ''` at EVERY dedup site — the anti-join keys AND the window `PARTITION BY` (which used raw values; the
      miss the doc's first cut would have left) — via a new `_dedup_key_sql(coalesce(nullif(cast(x),''),sentinel))`.
      Resolves the pre-existing `''` rows system-wide with NO historical migration. **SHIPPED
      `unified-trading-library@f5ec2291f`** (LDR); 5 new regression tests (proven to fail without the fix) + 728
      manifest tests green; validated on the LIVE manifest — collapses **2,290** real duplicate rows (2,230 XG_SHOTS +
      60 XG).
- [x] [CODE] P0. **lookup_contract data_type-case + blank-instrument_type sports aliases (UAC).** After §9.1 the
      write-time schema lookup is `("sports","","XG_SHOTS")`; the contract was keyed `("sports","shot","xg_shots")`, so
      it missed on BOTH instrument_type AND data_type case → `MANIFEST_WRITE_SCHEMA_MISSING` (validation silently
      skipped). Fix: `lookup_contract` case-normalizes data_type (mirrors the instrument_type fallback) AND
      `SPORTS_XG`/`SPORTS_XG_SHOTS` are registered under blank-instrument_type aliases. **SHIPPED
      `unified-api-contracts@b5a4adce1`** (LDR); +2 regression tests. (Not in the original §9 plan — discovered as a
      consequence of §9.1; restores schema validation for the backfill.)
- [x] [CODE] P1. **asset_group blank on captured (§9.3) — CORRECTED APPROACH.** The doc proposed `venue="understat"`;
      that is WRONG — `venue` is a BASE dedup key and sports rows carry `venue=""`, so it would re-split captured from
      the `venue=""` seeds and RE-BREAK §9.2. Verified on the live manifest: XG captured = `sports` (pre-Rule-1 writes),
      XG_SHOTS captured (my 9 validation rows, current code) = `''`. Root cause: `_resolve_asset_group` Rule 1 blanks
      ALL no-venue rows. Fix: Rule 1 now HONORS an explicit closed-set `asset_group` on a no-venue reference row (stamps
      `sports`), never touches `venue`. **SHIPPED with §9.2 in `unified-trading-library@f5ec2291f`**; +1 regression
      test.
- [ ] [DATA] P1. One-off manifest normalization — clean the pre-existing dup pollution (incl. seed-vs-seed
      `empty_confirmed`+`expected_unattempted` dups) + the 5 stale `instrument_type=shot` test rows on 2024-12-14.
      **Sequenced AFTER the §9.2 consolidator fix DEPLOYS to the Cloud Run jobs** — normalizing before the deployed
      consolidator has the fix would just re-duplicate against the still-buggy comparison. §9.
- [ ] [SCRIPT] P1. Build the bulk writer reusing `get_fixtures(league,season)` (bulk XG) + `get_match_shots` +
      `_gated_sink_write` + `record_captured` (no path/manifest reshape); season getLeagueData cache + concurrent shots;
      group season → per (date, league). §4/§6. (Unblocked — §9.2 shipped.)
- [ ] [DATA] P0. Full backfill run (operator-gated locus; NOT a VM — bulk local) → all 5 leagues 2014→present, XG +
      XG_SHOTS captured; manifest `pending_fetch=0`, `attempted_failed=0`, `captured>0` for native leagues. §6.
      (Unblocked — §9.2 shipped. **`dont save before confirming` — operator gate before any GCS write.**)
- [ ] [CODE] P1. **DEFERRED — Register `XG_SHOTS` in `SPORTS_DATA_TYPE_META`** (deployment-api) so the Data Status tab
      renders an XG_SHOTS coverage row (currently filtered out → the broken type is invisible). §5. Change is READY
      (patch saved: `scratchpad/deployment_api_xg_shots_meta.patch`) but **BLOCKED**: deployment-api LDR HEAD
      (`12e5603`) has 4 PRE-EXISTING unrelated test failures (`test_route_fleet` ×3 from the recent fleet feature
      `e04668d`, `test_empty_reason_breakdown` taxonomy) → tree not QG-green → quickmerge blocked. Re-apply once LDR
      deployment-api is green. Operator notified.
- [ ] [VERIFY] P1. Verify the §9.2 consolidator fix reaches the DEPLOYED Cloud Run jobs (image rebuild on UTL promote);
      the manifest self-heals once live. Then run the one-off normalization.
- [ ] [VERIFY] P1. After backfill: re-evaluate the `understat-vm-xg-complete` gate against the manifest; flip only on
      real captured shots (not hollow). Then the 6 parked sports tasks unblock.

## 9. Validation findings (2026-06-30) — consolidator does NOT promote captured cleanly

A small real write (XG_SHOTS for 2024-12-14, then 2024-12-21 via the production `_run_understat_shots_date`, force=True)

- a consolidator run uncovered **three layered bugs**. The write itself works (473 + ~447 real shots → GCS parquet), but
  the manifest ends up with DUPLICATE rows per (date, league) instead of promoting `expected_unattempted → captured`, so
  the gate's `pending_fetch` never clears.

**9.1 instrument_type mismatch (FIXED in slot-16, not shipped).** `record_captured` stamped `instrument_type="shot"` but
every existing XG_SHOTS row (297,818) + every XG row + all sports types use `""`; `instrument_type` is a dedup key →
split. Fix: `"shot" → ""` (shot-level stays encoded by `data_type=XG_SHOTS` + the `SPORTS_XG_SHOTS` contract + parquet
columns). Operator-confirmed: match the manifest convention (`""`), no migration.

**9.2 NULL-vs-`''` optional-dim dedup (THE blocker — UTL-layer, system-wide, PRE-EXISTING).** Even after 9.1, captured
rows still duplicated. Root cause: `record_captured` (real pipeline) serializes optional dedup-dim columns as `''`,
while seed rows (`record_expected_empty`/`record_empty`) leave them `NULL`. The consolidator substitutes NULL→sentinel
(so NULL==NULL) but keeps `''` distinct → `NULL ≠ ''` → a captured row in a different shard than its seed never
supersedes it. Confirmed on the live manifest: **XG = 610 dup (date,league) groups, XG_SHOTS = 2,235** (incl.
seed-vs-seed `empty_confirmed`+`expected_unattempted` dups). NOT understat-specific — affects every data_type.

**DECIDED (operator, 2026-07-06): fix BOTH layers, not one or the other.** (1) `manifest_writer`'s `record_captured`
must emit `NULL` (not `''`) for unset optional dedup dims going forward — root-cause correctness, matches seed
semantics. (2) `manifest_consolidator` must ALSO treat `NULL == ''` in the dedup key — not redundant
belt-and-suspenders, it's load-bearing: it's what correctly resolves the millions of pre-existing `''` rows already
written across every asset_group (system-wide, all data_types) without a live migration of historical manifest data. (3)
THEN — and only after both land — run the one-off normalization pass (§8) to clean up the duplicate rows the bug already
created (610 XG / 2,235 XG_SHOTS dup groups + the 5 stale test rows); normalizing before the consolidator fix ships
would just re-duplicate against the still-buggy comparison.

**9.3 asset_group blank on captured — SHIPPED (`unified-trading-library@f5ec2291f`), CORRECTED from the doc's proposed
fix.** `_resolve_asset_group` (`_writer_ingest.py`) Rule 1 treats a no-venue row as non-market-data and drops the
provided `asset_group="sports"` → `''`. **The doc originally proposed `venue="understat"` — that is a BUG:** `venue` is
a BASE dedup key and every sports row carries `venue=""`, so stamping `venue="understat"` on captured rows would
re-split them from the `venue=""` seeds and RE-BREAK §9.2. Live-manifest check confirmed the asymmetry: XG captured =
`sports` (written pre-Rule-1) but XG_SHOTS captured (the 9 validation rows, current code) = `''` — Rule 1 blanks ALL
no-venue rows regardless of the provided kwarg. **Correct fix (shipped):** Rule 1 now HONORS an explicit _closed-set_
`asset_group` on a no-venue reference row (stamps `sports`) — a non-closed-set label (ML `quant`) still drops to `''`.
Never touches `venue`, so §9.2 is preserved. asset_group is NOT a dedup key (cosmetic for the per-asset_group coverage
rollup), so it never caused the duplicate — but a blank one would drop XG_SHOTS from the SPORTS rollup.

**Convention reference (operator-directed "use what other data types use"):** data_type = `XG_SHOTS` (UPPERCASE — all
sports reference types + downstream `feature_upstream`); the contract-registry key `"xg_shots"` is lowercase only as a
lookup key and `lookup_contract` normalizes instrument_type case but NOT data_type → the `MANIFEST_WRITE_SCHEMA_MISSING`
warning (fix `lookup_contract` to normalize data_type case too — fixes XG as well). asset_group = `sports`.
instrument_type = `""` (blank) per §9.1.

## Progress Log

- **2026-07-07 (slot-7 opus/max, task `understat_local_backfill_completion-002` — Manifest verification):** Ran the gate
  re-verify against the LIVE consolidated manifest
  (`gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`, 4,897,283 total rows,
  607,540 understat). The full-history backfill driver has made **substantial progress since the 2026-07-06 baseline**
  but the DoD is **still NOT MET**. Big-5 counts (EPL/LA_LIGA/BUNDESLIGA/SERIE_A/LIGUE_1) compared to the 2026-07-06
  slot-12 baseline:

  | metric                        | baseline (2026-07-06 slot-12) | now (2026-07-07 slot-7) | delta      |
  | ----------------------------- | ----------------------------- | ----------------------- | ---------- |
  | XG captured                   | 4,432                         | **6,676**               | +2,244     |
  | XG_SHOTS captured             | 1,961 (44% of XG)             | **6,671 (99.9% of XG)** | +4,710     |
  | XG_SHOTS attempted_failed     | 384                           | **20**                  | −364       |
  | XG_SHOTS expected_unattempted | 13,811                        | **6,093**               | −7,718     |
  | XG expected_unattempted       | 315                           | **245**                 | −70        |
  | XG latest captured date       | 2023-03-11                    | **2026-05-24**          | +3.2 years |
  | XG_SHOTS latest captured date | 2024-12-21                    | **2026-05-24**          | +17 months |

  The captured-shots ratio (XG_SHOTS / XG) is now **99.9%** (was 44%) — the driver drove XG_SHOTS to near-parity with
  XG. Latest captured for both is 2026-05-24 (rolling window frontier).

  **DoD violations that block a green flip on task `-005`**:
  - **20 XG_SHOTS `attempted_failed`** remain (all `HTTP_NOT_FOUND`, 4 per big-5 league, attempted_at 2026-06-23) — the
    plan's DoD requires 0.
  - **6,093 XG_SHOTS + 245 XG `expected_unattempted`** remain (evenly split 1,218-1,219 per big-5 league for XG_SHOTS,
    49 per league for XG) — the plan's DoD requires 0.
  - **16,352 stale `empty_confirmed`** rows with `attempted_at < 2026-07-06` (breakdown by month: 208 in 2026-04, 5,360
    in 2026-05, 10,784 in 2026-06) — the plan's DoD requires 0.

  **Assessment**: the resume-aware driver from task -001 pushed the frontier forward by ~3 years (XG) / ~17 months
  (XG_SHOTS) and closed 95% of the shots-captured gap, but the tail (attempted_failed + EU + stale empty) has not
  cleared. This is the same class of tail as the ~2016 hand-off note in the plan preface — historical dates the driver
  still needs to re-attempt. Task `-005` (gate flip) stays RED until task `-001` drives to `0 attempted_failed`. Task
  `-003` (§9.2b consolidator confirmation) and task `-004` (one-off normalization) are also unchanged from their
  BLOCKED-PREREQUISITES status. No code shipped this session.

- 2026-06-29: shot-endpoint root-cause fixed + shipped (`instruments-service@527b9d9`); date-by-date VM
  `us-backfill-20260628-070120` deleted; bulk endpoints + throughput + save/manifest contract verified live; this issue
  written. Scope confirmed XG + XG_SHOTS only (raw bucket deprecated). Moved into slot-16 worktree.
- 2026-06-30: bulk download validated == stored GCS XG (idempotent, 0 mismatches). Operator-approved a small validation
  write → ran XG_SHOTS for 2024-12-14 + 2024-12-21 + consolidator. **Uncovered 3 layered manifest bugs (§9):**
  instrument_type `shot`→`""` (fixed in slot-16, unshipped); the UTL NULL-vs-`''` optional-dim dedup blocker
  (system-wide: XG 610 / XG_SHOTS 2,235 dup groups); asset_group blank-on-captured (venue Rule 1). Consolidator does NOT
  promote captured over seed → gate won't clear until §9.2 is fixed. **Operator decision pending: fix manifest writer vs
  consolidator for the NULL-vs-`''` dedup.** Left 5 stale `instrument_type=shot` test rows on 2024-12-14 + fresh
  captured rows on 2024-12-21 (need cleanup). No code shipped; root working tree restored clean.
- 2026-07-06: **§9.2 DECIDED — fix BOTH layers.** Operator ruled against picking just one side: `manifest_writer`'s
  `record_captured` will emit `NULL` (not `''`) for unset optional dedup dims going forward (root-cause correctness,
  matches seed semantics), AND `manifest_consolidator` will also treat `NULL == ''` in the dedup key — the consolidator
  side is load-bearing, not redundant, since it's what resolves the millions of pre-existing `''` rows already written
  system-wide (every asset_group, not just understat) without needing a live migration of historical manifest data. Ship
  both as one change. The one-off normalization pass (§8) is sequenced strictly AFTER both land — normalizing against
  the still-buggy comparison would just recreate the duplicates. Unblocks the bulk writer build + full backfill run once
  shipped.
- 2026-06-30 (manifest-grounded verification): pulled the live sports manifest (`read_availability_index`) to reconcile
  the deployment-ui Data Status tab (operator saw "XG 99%", "SPORTS 85.5% captured / 100% attempted / 77% empty").
  Findings: (a) the tab is faithful but for SPORTS scores _attempt_ coverage — empty_confirmed counts as a successful
  attempt, so false-empties read as coverage; (b) XG (99%) is genuinely captured (validated byte-exact earlier) — its
  empties are legit non-match days; (c) XG_SHOTS is the broken case AND is invisible in the tab (absent from
  `SPORTS_DATA_TYPE_META`). Hard proof of false-emptiness: 4,436 XG-captured league-dates vs only 9 XG_SHOTS captured;
  ≥1,675 of the identical XG-captured dates record XG_SHOTS `empty_confirmed`. Updated §5 with live counts + the proof,
  added a todo to register XG_SHOTS in `SPORTS_DATA_TYPE_META`, and corrected the `repos:` frontmatter (added
  `unified-trading-library` for §9.2 + `deployment-api` for the visibility fix; dropped the untouched
  `deployment-service`). No code shipped.
- 2026-07-06 (implementation + ship): built and SHIPPED all four code fixes to LDR after the operator's "start working
  on the fix" go-ahead. **`unified-api-contracts@b5a4adce1`** (lookup_contract data_type-case + blank-instrument_type
  sports aliases — discovered as a §9.1 consequence, restores schema validation),
  **`unified-trading-library@f5ec2291f`** (§9.2 both layers: writer emits NULL for unset optional dims + consolidator
  `_dedup_key_sql` treats `NULL == ''` at the anti-join keys AND the window `PARTITION BY`; §9.3 asset_group Rule 1
  honors closed-set label on no-venue reference rows — CORRECTED from the doc's `venue="understat"`, which would have
  re-broken §9.2), **`instruments-service@4281a01db`** (§9.1 instrument_type=""). Each landed via quickmerge with its
  full QG green (UAC 234s / UTL 140s / IS 108s) + strict-quickmerge clean. 8 new regression tests total, all proven to
  fail without the fix; 728 UTL manifest tests + 92 UAC contract tests green. Validated on the LIVE manifest: the fixed
  consolidator dedup collapses **2,290** real duplicate rows (2,230 XG_SHOTS + 60 XG). **deployment-api XG_SHOTS-meta
  DEFERRED** — LDR deployment-api HEAD carries 4 pre-existing unrelated failures (fleet routes + empty-reason taxonomy)
  so its tree isn't QG-green; patch saved, will re-apply when green. **Deployment note:** the §9.2 consolidator fix
  reaches the ~20 Cloud Run consolidator jobs on the next image rebuild after UTL promotes; the live manifest self-heals
  (dups collapse) once that lands — verify then run the one-off normalization. NEXT: build the bulk writer,
  operator-gate the backfill run (`dont save before confirming`), re-evaluate the `understat-vm-xg-complete` gate.
- 2026-07-06 (slot-12, `data_engineering` — gate re-evaluation, task `understat_local_backfill_completion-005`): the
  shipped verify (`/tmp/verify_understat_gate.py`) against the LIVE consolidated manifest
  (`gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`, 5.28M rows, 611,728
  understat) shows the full-history backfill has NOT reached completion in this era. Big-5 XG captured=4,432 /
  empty=19,764 / **`expected_unattempted`=315** / attempted_failed=0; big-5 XG_SHOTS captured=**1,961** (44% of XG) /
  empty=7,580 / **`attempted_failed`=384** (all `HTTP_NOT_FOUND`, attempted_at 2026-06-23 → 2026-06-29) /
  **`expected_unattempted`=13,811**. Hollow-shots ratio 67-73% per league (EPL 69.8%, LA_LIGA 73.0%, BUNDESLIGA 67.5%,
  SERIE_A 69.6%, LIGUE_1 71.2%); latest captured dates: XG 2023-03-11, XG_SHOTS 2024-12-21. No active backfill process,
  no `/tmp/understat_backfill.log`. Gate cannot be flipped — DoD
  (`0 attempted_failed / 0 expected_unattempted / XG_SHOTS ≈ XG`) is NOT met. Task 005 marked BLOCKED-PREREQUISITES in
  `plans/archive/2026_07/understat_local_backfill_completion_2026_07_06.md`; the ~2.4 h ETA run below appears to have
  been interrupted (matches the plan preface's "~700+ dates 2014→2016" hand-off note). NEXT (operator): confirm + remove
  any circular-prereq on `understat-vm-xg-complete` from tasks 001-004 in `backlog.yaml`, `POST /api/backlog/regen`,
  then task 001 re-runs the resume-aware driver to completion.
- 2026-07-06 (bulk writer + backfill run — operator go "build the writer and save the data" + "also fix XG capture
  now"): A small validation write (2023-03-11) — made possible ONLY because the lookup_contract fix made schema
  validation actually RUN — surfaced **three more pre-existing bugs** (all previously masked by the skipped validation),
  fixed + regression-tested + **SHIPPED `instruments-service@9dfea859d`**: **(A) shots schema** —
  `_run_understat_shots_date`'s df never matched `SPORTS_XG_SHOTS`: no `xa` column (understat has no per-shot xA →
  nullable-null), `home_goals`/`away_goals`/`period` as `object` not `int64` (→ nullable `Int64`), `available_at` `us`
  not `ns`. Conformed in the write path (fixes GCS parquet + validation). **(B) XG capture recorded EMPTY despite
  fixtures — two coupled bugs:** (1) the fixture `league` field is a nested `CanonicalLeague` dict, so the flatten
  exploded it into `league_*` columns leaving NO flat `league` key → the whole per-league capture block was skipped; (2)
  `_captured_leagues` tracked the RAW league name while the honest-absence loop subtracts the CANONICAL, so every
  non-already-uppercase league (all but EPL) got `empty` written OVER its capture. A **2026-05-07 bulk run** had
  recorded empty for ~all XG match-days while the xG parquets sit in GCS — manifest under-reported XG as **4,444
  captured / 301,667 empty** (the "99%" in the tab is ATTEMPT coverage). NOT operator-me: confirmed via untouched dates
  (2023-03-18 / 2024-01-13 show the same GCS-data-but-`empty` pattern, timestamped 2026-05-07). Regression test
  reproduces the nested-dict + non-canonical shapes (the prior happy-path used a string league + identity canonical, so
  it caught neither). **(C) adapter getLeagueData match cache** — memoise the lightweight per-(league, season) match
  list so the full-history bulk backfill fetches each season ONCE, not per date (~30k → ~72 fetches); autouse
  cache-clear fixture prevents test pollution. **Bulk driver** (`scratchpad/bulk_backfill.py`) enumerates fixture-dates
  per league-season (pre-populating the cache) then drives the EXISTING per-date functions with bounded concurrency —
  full reuse of the shipped write + honest -absence path. Validated on 8 dates (98 XG + 2,100 shots, 0 errors, correct
  manifest shape: captured / sports / instrument_type NULL / schema-valid). **FULL RUN LAUNCHED** (5 big-5 leagues
  2014→present, XG + XG_SHOTS, force=True, concurrency 6, per-VM shard `understat-bulk-backfill-slot16`): ~17 dates/min,
  ETA ~2.4h, 0 errors — repairs the ~300k mis-recorded XG rows AND captures the previously-broken XG_SHOTS in one pass.
  Consolidator (with §9.2b) collapses the captured-vs-seed dups once its image rebuilds on the UTL promote. NEXT: verify
  totals on completion, then re-evaluate the gate. **UPDATE §4 table cell: XG_SHOTS instrument_type is `""` (not
  `"shot"`) per §9.1; GCS path DOES carry a `league={lid}` segment (the doc's §4 "no league subdir" note was for XG only
  — XG_SHOTS partitions by league).**
- 2026-07-13 (slot-3, interactive session): operator asked whether this line of work is done at literal 100%; it is not.
  This doc's own §8 open todos ("verify §9.2 consolidator fix reaches deployed jobs", "one-off manifest normalization")
  are exactly the still-open gap: a fresh 2026-07-13 manifest re-verify found the sibling doc
  `sports_xg_shots_instrument_type_dedup_key_instability_2026_07_09.md`'s fix has RECURRED (2024-12-14 big-5 duplicates
  back, plus a new instance on XG). Also found the `expected_unattempted` residual (30, down from 6,093) is closing via
  a typing script that was never actually scheduled anywhere — closing that lag requires wiring
  `type_understat_eu_no_provider_coverage.py` into a Cloud Scheduler job, not further ad-hoc runs. Full detail +
  concrete next steps filed in `plans/archive/2026_07/understat_local_backfill_completion_2026_07_06.md` (2026-07-13
  entry + 4 new todos) and in the sibling dedup docs' own Progress Logs. Not duplicating the fix plan here — this doc's
  §8 todos remain the durable tracking for the consolidator-reaches-deployed-jobs question; treat them as still open,
  not superseded.
