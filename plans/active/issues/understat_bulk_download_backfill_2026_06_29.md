---
doc_type: issue
title: Understat bulk-download backfill — replace the slow date-by-date VM crawl with league×season batch pulls (instruments-service, 2026-06-29)
summary: 'The understat xG backfill ran date-by-date on a multi-day SPOT VM and (separately) captured ZERO shot-level data because the adapter hit a dead endpoint. The shot-endpoint bug is fixed and shipped; this issue captures the design for a BULK downloader: understat serves a whole league-season in one getLeagueData call, so we iterate league×season (5 leagues × ~12 seasons) for match-level XG and pull per-match shots from getMatchData — minutes, not days. Data + manifest must be written in the IDENTICAL shape to the sequential backfill (same GCS path, same record_captured row atom). Nothing is written to GCS until the operator confirms the save path.

  '
status: open
nature: design
asset_group: [cross-cutting]
stage: [data, meta]
repos: [instruments-service, unified-api-contracts, unified-trading-library, deployment-api]
scope: [engineer]
tags: [sports, understat, xg, backfill, manifest]
related: [sports_p2_history_reference_and_odds_2015_to_present_2026_06_27, sports_p1_golden_window_reference_sources_2026_06_27]
created: 2026-06-29
parent_epic: infrastructure_master
priority: P1
source: ['2026-06-29 operator-directed investigation (interactive session, slot-16 claimed): understat-vm-xg-complete gate stuck; XG_SHOTS captured=0 across all history', instruments-service@527b9d9 — get_match_shots endpoint fix (/getMatch → /getMatchData)]
assigned_vm:
resolved_by:
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_since: 2026-05-21
---

# Understat bulk-download backfill

> **Working agreement (operator, 2026-06-29):** write this doc first; then verify the download + save path
> locally in slot-16; **do NOT write any data to GCS / touch the manifest until the operator confirms.**
> The running date-by-date VM (`us-backfill-20260628-070120`) was deleted on 2026-06-29; do not relaunch it.

## 1. Background / why this exists

- The date-by-date understat backfill VM crawled one calendar date at a time (2014→present), ETA ~3 days.
- Independently, **shot-level data (`XG_SHOTS`) was never captured for any date** (`captured=0`): the adapter
  called `GET /getMatch/{id}`, which upstream removed (now 404s for every id). The 404 was silently absorbed
  as honest-absence → hollow data that would have let the `understat-vm-xg-complete` gate flip on empty shots.
- **Fixed + shipped** (`instruments-service@527b9d9`): `get_match_shots` now reads `GET /getMatchData/{id}`
  (`shots` key); `_parse_shot_from_raw` maps `shotType` (was the always-`None` `type` key). Verified live:
  real shots returned for matches across 2014–2024.
- **This issue** is the faster replacement for the crawl: understat serves a whole league-season in one call.

## 2. What we must capture — registry SSOT (do NOT miss any)

SSOT: `unified-api-contracts/unified_api_contracts/canonical/domain/sports/league_data.py`.

| Item | Value | SSOT line |
| --- | --- | --- |
| Data types from understat | **`XG`, `XG_SHOTS`** (only these two) | `SPORTS_DATA_TYPE_TO_SOURCE` :174–175 |
| Leagues (native) | **EPL, LA_LIGA, BUNDESLIGA, SERIE_A, LIGUE_1** (big-5 only) | `SPORTS_SOURCE_LEAGUE_ALLOWLIST` :240–242 |
| Coverage start | **2014-01-01** (source-wide, no per-data_type override) | :71–87 |

> **SCOPE CONFIRMED (operator, 2026-06-29): XG + XG_SHOTS ONLY.** `getLeagueData` also returns `players`
> (570/season) and `teams` (20/season) aggregates, and an OLD rich 13-table CSV dump exists in
> `football-raw-data-all-sources/understat/` (2026-02-05) — but **that bucket is DEPRECATED / no longer used**,
> and the live system tracks only XG + XG_SHOTS. So bulk scope = exactly the two live, manifest-tracked types.

## 3. The bulk endpoints (verified live 2026-06-29)

| Endpoint | Returns | Covers | Throughput (measured) |
| --- | --- | --- | --- |
| `GET /getLeagueData/{league}/{season}` | `{teams, players, dates}` — `dates` = all matches' match-level xG | one whole league-season → **XG** | 0.70 s/call → 5 leagues × ~12 seasons ≈ **<1 min** |
| `GET /getMatchData/{match_id}` | `{rosters, shots, tmpl}` — `shots = {h:[...], a:[...]}` | one match → **XG_SHOTS** | 0.29 s/call; match ids come free from `dates` |

- Headers: browser UA + `X-Requested-With: XMLHttpRequest`; warm a cookie on `/` first. No API key.
- `getLeagueData` gzip; use a client that auto-decodes (httpx does).
- Total matches ≈ 19k (5 leagues × ~12 seasons). Serial shots ≈ 90 min; **~5–10 min at modest concurrency.**
- So: **iterate league × season for XG (≈55 calls); drive XG_SHOTS off each season's match ids.** This matches
  the operator's recollection — one league-season call yields all match-level data.

## 4. Save path + manifest contract — bulk MUST equal sequential

Both data types are written + recorded by `instruments-service/.../engine/orchestrator/understat.py`
(`_fetch_understat_xg` → XG; `_run_understat_shots_date` → XG_SHOTS). **Reuse these helpers — do not hand-roll
paths.** Verified the actual on-disk layout: the `"league"` partition key is a column/manifest key, **NOT a
path segment** (real path is `entity=understat_xg/understat_xg.parquet`, no `league=` subdir).

| Field | XG | XG_SHOTS |
| --- | --- | --- |
| capture fn | `_fetch_understat_xg` | `_run_understat_shots_date` |
| sink | `_sports_ref_sink_for(bucket, date, "understat_xg")` | `_sports_ref_sink_for(bucket, date, "understat_xg_shots")` |
| entity | `understat_xg` | `understat_xg_shots` |
| GCS path (verified) | `gs://{bucket}/sports_reference/by_date/day={date}/pipeline_mode=batch_understat/entity=understat_xg/understat_xg.parquet` | `…/entity=understat_xg_shots/understat_xg_shots.parquet` |
| `record_captured` row_key | `{"date": date, "data_type": "XG", "league_id": lid}` | `{"date": date, "data_type": "XG_SHOTS", "league_id": lid}` |
| asset_group / instrument_type | `sports` / `""` | `sports` / `"shot"` |
| pipeline_mode | `BATCH_UNDERSTAT` (`"batch_understat"`) | same |
| source | `_sports_ref_source("understat_xg")` → `"understat"` | `_sports_ref_source("understat_xg_shots")` → `"understat"` |
| **manifest atom** | **per `(date, league_id, data_type)`** | **per `(date, league_id, data_type)`** |
| honest-absence | `record_empty(EXPECTED_NO_FIXTURE)` / `record_expected_empty(EXPECTED_PRE_SOURCE_COVERAGE_START | EXPECTED_PAUSED_LEAGUE)` | same |
| failure | `record_failed(error=<classified>)` | same |

**Implication for the bulk writer:** the bucket = `instruments-store-sports-{project}`. The atom is per
`(date, league, data_type)`, but the bulk fetch is per `(league, season)`. So the writer must **group the
season payload by calendar date**, and for each `(date, league)` emit one XG row and one XG_SHOTS row (shots
aggregated from all of that date's matches in that league) — exactly as the sequential path does per date.

## 5. Manifest correctness — the falsely-empty XG_SHOTS rows

- Live manifest (verified 2026-06-30 via `read_availability_index`): `XG_SHOTS` = 288,284 `empty_confirmed` +
  13,781 `expected_unattempted` + 392 `attempted_failed` + **9 `captured`** (the 9 are the 2024-12-14/21 validation
  writes; the doc previously said `captured=0`). Almost all the `empty_confirmed` is FALSE — shots exist upstream.
- **PROOF the emptiness is false (understat, per `(league, date)`):** 4,436 league-dates have real XG captured but
  only **9** have XG_SHOTS captured; on **≥1,675** of the *exact same* XG-captured dates XG_SHOTS is recorded
  `empty_confirmed` — impossible, since every match's xG total is built from shot events. The dead `/getMatch`
  endpoint's `[]` was absorbed as honest-absence. A naive idempotent re-run **skips** these (log: "skipping date —
  all 5 expected leagues per-league captured"), so it would NOT backfill.
- **Coverage-tab blind spot (new finding, 2026-06-30):** the deployment-ui Data Status tab NEVER shows XG_SHOTS —
  it is absent from `SPORTS_DATA_TYPE_META` (`deployment-api/.../data_status/sports_helpers.py`), so the build loop
  filters it out. And for SPORTS the tab's headline is *attempt* coverage (`(captured+empty+failed)/expected`), which
  counts the false-empties as successful attempts → the broken type reads green via its healthy sibling (XG at 99% is
  genuine) while being invisible. So the tab did not — and structurally cannot — surface this gap. Register XG_SHOTS
  in `SPORTS_DATA_TYPE_META` so coverage tracking sees it.
- The bulk writer must therefore **force-overwrite** those rows to `captured` (last-write-wins) — i.e. write
  with the force/overwrite path, not the skip-if-present path.
- **OPEN Q2:** confirm the consolidator's last-write-wins dedup will promote `empty_confirmed → captured`
  on a re-write of the same row_key (expected yes), and whether any `expected_unattempted` rows need an
  explicit reseed first. Verify on a single (date, league) before any bulk run.

## 6. Proposed approach (design — not yet built)

1. **Fetcher** (new, fast, concurrent): for each `league ∈ 5`, `season ∈ 2014…current`:
   `getLeagueData` → group `dates` by calendar date → per-match `getMatchData` for shots (bounded concurrency).
2. **Writer**: feed the grouped per-`(date, league)` data into the **existing** `_sports_ref_sink_for` +
   `record_captured` path (reuse, don't reimplement) so GCS + manifest shape is byte-identical to sequential.
   Honest-absence/off-season/coverage guards stay (reuse the same `record_empty`/`record_expected_empty`).
3. **Run locus:** slot-16 (claimed/paused) for the prototype + a dry-run that writes NOTHING; a real run
   target (local vs a short-lived VM) is an operator decision — **NOT the old date-by-date VM.**
4. **Verify:** after a single-(date,league) write, confirm GCS path + parquet rows + manifest row promoted to
   `captured`; then scale.

## 7. Decisions + open questions

- **Q1 — RESOLVED (operator 2026-06-29):** scope = **XG + XG_SHOTS only**. The rich 13-table dump lives in the
  **deprecated** `football-raw-data-all-sources/understat/` bucket (no longer used); do not reproduce it.
- **Q3 — RESOLVED:** work + validate in **slot-16** (claimed/paused). Real-run locus decided later (not the crawler VM).
- **Q4 — DEFERRED by sequence (operator 2026-06-29):** validate the bulk approach FIRST (save to GCS + manifest),
  THEN decide whether the existing capture fns can adopt it without large changes — else keep a **standalone script**.
- **Q2 — I will verify:** confirm last-write-wins promotes `empty_confirmed → captured` on re-write of the same
  row_key; reseed `expected_unattempted` if needed. Verify on a single (date, league) before any bulk run.

## 8. Todos

- [x] [DATA] P1. Confirm download path — read-only prototype validated `getLeagueData` (match-XG, 0.7s/call) +
  `getMatchData` (shots, 0.29s/call); EPL/2023 = 380 matches/120 dates. Also confirmed bulk == stored: XG download
  byte-exact to GCS for 2023-03-11 (24/24) + 2024-12-14 (20/20), 0 xG mismatches → idempotent. §3.
- [x] [DATA] P0. Save path confirmed with operator — paths/manifest atom resolved via existing helpers; operator
  approved a small validation write. §4.
- [x] [DATA] P1. Validation write + consolidator test (2024-12-14, then 2024-12-21) — **surfaced 3 layered manifest
  bugs, see §9.** The consolidator does NOT promote captured over seed cleanly.
- [ ] [CODE] P0. instruments-service `understat.py` — XG_SHOTS `record_captured` `instrument_type="shot" → ""` to match
  the 297k existing rows + XG + sports convention. APPLIED in slot-16 (uncommitted); validated instrument_type now
  matches. §9.1. (Not shipped — held pending the deeper §9.2 fix.)
- [ ] [CODE] P0. **UTL manifest NULL-vs-`''` dedup bug (§9.2)** — captured rows write optional dedup-dims
  (`timeframe, feature_group, model_family, training_period, strategy_id, client_id, instruction_type`) as `''`; seeds
  use `NULL`; consolidator treats `NULL ≠ ''` → captured never supersedes seed across shards → duplicates. System-wide
  (XG 610 / XG_SHOTS 2,235 dup groups). **DECIDED (operator, 2026-07-06): fix BOTH** — `record_captured` write `NULL`
  for unset optional dims (root cause, forward-fix) AND `manifest_consolidator` treat `NULL == ''` in the dedup key
  (resolves the pre-existing `''` rows system-wide without a historical migration). Ship together, as one change.
- [ ] [CODE] P1. **asset_group blank on captured (§9.3)** — `record_captured` omits `venue` → `_resolve_asset_group`
  Rule 1 (no venue → non-market-data → drop label) blanks `asset_group`. Pass `venue="understat"` so the kwarg
  `"sports"` stamps. (Existing XG captured rows show `sports` — mechanism not fully reconciled; confirm before fixing.)
- [ ] [DATA] P1. One-off manifest normalization — clean the pre-existing dup pollution (incl. seed-vs-seed
  `empty_confirmed`+`expected_unattempted` dups) + the 5 stale `instrument_type=shot` test rows on 2024-12-14.
  **Sequenced AFTER the §9.2 writer+consolidator fix ships** — normalizing first would just re-duplicate against the
  still-buggy comparison. §9.
- [ ] [SCRIPT] P1. Build the bulk writer reusing `_sports_ref_sink_for` + `record_captured` (no path/manifest reshape);
  group season → per (date, league). §4/§6. (Blocked on §9.2 — fix now decided, unblocks once it ships.)
- [ ] [DATA] P0. Full backfill run (operator-gated locus) → all 5 leagues 2014→present, XG + XG_SHOTS captured;
  manifest `pending_fetch=0`, `attempted_failed=0`, `captured>0` for native leagues. §6. (Blocked on §9.2 — fix now
  decided, unblocks once it ships.)
- [ ] [CODE] P1. Register `XG_SHOTS` in `SPORTS_DATA_TYPE_META`
  (`deployment-api/deployment_api/services/data_status/sports_helpers.py`) so the Data Status tab renders an XG_SHOTS
  coverage row (currently filtered out → the broken type is invisible in coverage tracking). §5.
- [ ] [VERIFY] P1. After backfill: re-evaluate the `understat-vm-xg-complete` gate against the manifest; flip only on
  real captured shots (not hollow). Then the 6 parked sports tasks unblock.

## 9. Validation findings (2026-06-30) — consolidator does NOT promote captured cleanly

A small real write (XG_SHOTS for 2024-12-14, then 2024-12-21 via the production `_run_understat_shots_date`, force=True)
+ a consolidator run uncovered **three layered bugs**. The write itself works (473 + ~447 real shots → GCS parquet),
but the manifest ends up with DUPLICATE rows per (date, league) instead of promoting `expected_unattempted → captured`,
so the gate's `pending_fetch` never clears.

**9.1 instrument_type mismatch (FIXED in slot-16, not shipped).** `record_captured` stamped `instrument_type="shot"`
but every existing XG_SHOTS row (297,818) + every XG row + all sports types use `""`; `instrument_type` is a dedup key
→ split. Fix: `"shot" → ""` (shot-level stays encoded by `data_type=XG_SHOTS` + the `SPORTS_XG_SHOTS` contract +
parquet columns). Operator-confirmed: match the manifest convention (`""`), no migration.

**9.2 NULL-vs-`''` optional-dim dedup (THE blocker — UTL-layer, system-wide, PRE-EXISTING).** Even after 9.1, captured
rows still duplicated. Root cause: `record_captured` (real pipeline) serializes optional dedup-dim columns as `''`,
while seed rows (`record_expected_empty`/`record_empty`) leave them `NULL`. The consolidator substitutes NULL→sentinel
(so NULL==NULL) but keeps `''` distinct → `NULL ≠ ''` → a captured row in a different shard than its seed never
supersedes it. Confirmed on the live manifest: **XG = 610 dup (date,league) groups, XG_SHOTS = 2,235** (incl.
seed-vs-seed `empty_confirmed`+`expected_unattempted` dups). NOT understat-specific — affects every data_type.

**DECIDED (operator, 2026-07-06): fix BOTH layers, not one or the other.** (1) `manifest_writer`'s `record_captured`
must emit `NULL` (not `''`) for unset optional dedup dims going forward — root-cause correctness, matches seed
semantics. (2) `manifest_consolidator` must ALSO treat `NULL == ''` in the dedup key — not redundant belt-and-suspenders,
it's load-bearing: it's what correctly resolves the millions of pre-existing `''` rows already written across every
asset_group (system-wide, all data_types) without a live migration of historical manifest data. (3) THEN — and only
after both land — run the one-off normalization pass (§8) to clean up the duplicate rows the bug already created (610
XG / 2,235 XG_SHOTS dup groups + the 5 stale test rows); normalizing before the consolidator fix ships would just
re-duplicate against the still-buggy comparison.

**9.3 asset_group blank on captured.** `record_captured` does not pass `venue`; `_resolve_asset_group`
(`_writer_ingest.py`) Rule 1 treats a no-venue row as non-market-data and drops the provided `asset_group="sports"` →
`''`. Fix: pass `venue="understat"`. NOTE: existing XG captured rows have `asset_group="sports"` despite the same call
shape — mechanism not fully reconciled; verify before fixing. asset_group is NOT a dedup key (cosmetic for the
per-asset_group coverage rollup), so it does not cause the duplicate.

**Convention reference (operator-directed "use what other data types use"):** data_type = `XG_SHOTS` (UPPERCASE — all
sports reference types + downstream `feature_upstream`); the contract-registry key `"xg_shots"` is lowercase only as a
lookup key and `lookup_contract` normalizes instrument_type case but NOT data_type → the `MANIFEST_WRITE_SCHEMA_MISSING`
warning (fix `lookup_contract` to normalize data_type case too — fixes XG as well). asset_group = `sports`.
instrument_type = `""` (blank) per §9.1.

## Progress Log

- 2026-06-29: shot-endpoint root-cause fixed + shipped (`instruments-service@527b9d9`); date-by-date VM
  `us-backfill-20260628-070120` deleted; bulk endpoints + throughput + save/manifest contract verified live;
  this issue written. Scope confirmed XG + XG_SHOTS only (raw bucket deprecated). Moved into slot-16 worktree.
- 2026-06-30: bulk download validated == stored GCS XG (idempotent, 0 mismatches). Operator-approved a small
  validation write → ran XG_SHOTS for 2024-12-14 + 2024-12-21 + consolidator. **Uncovered 3 layered manifest bugs
  (§9):** instrument_type `shot`→`""` (fixed in slot-16, unshipped); the UTL NULL-vs-`''` optional-dim dedup blocker
  (system-wide: XG 610 / XG_SHOTS 2,235 dup groups); asset_group blank-on-captured (venue Rule 1). Consolidator does
  NOT promote captured over seed → gate won't clear until §9.2 is fixed. **Operator decision pending: fix manifest
  writer vs consolidator for the NULL-vs-`''` dedup.** Left 5 stale `instrument_type=shot` test rows on 2024-12-14 +
  fresh captured rows on 2024-12-21 (need cleanup). No code shipped; root working tree restored clean.
- 2026-07-06: **§9.2 DECIDED — fix BOTH layers.** Operator ruled against picking just one side: `manifest_writer`'s
  `record_captured` will emit `NULL` (not `''`) for unset optional dedup dims going forward (root-cause correctness,
  matches seed semantics), AND `manifest_consolidator` will also treat `NULL == ''` in the dedup key — the consolidator
  side is load-bearing, not redundant, since it's what resolves the millions of pre-existing `''` rows already written
  system-wide (every asset_group, not just understat) without needing a live migration of historical manifest data.
  Ship both as one change. The one-off normalization pass (§8) is sequenced strictly AFTER both land — normalizing
  against the still-buggy comparison would just recreate the duplicates. Unblocks the bulk writer build + full backfill
  run once shipped.
- 2026-06-30 (manifest-grounded verification): pulled the live sports manifest (`read_availability_index`) to
  reconcile the deployment-ui Data Status tab (operator saw "XG 99%", "SPORTS 85.5% captured / 100% attempted / 77%
  empty"). Findings: (a) the tab is faithful but for SPORTS scores *attempt* coverage — empty_confirmed counts as a
  successful attempt, so false-empties read as coverage; (b) XG (99%) is genuinely captured (validated byte-exact
  earlier) — its empties are legit non-match days; (c) XG_SHOTS is the broken case AND is invisible in the tab (absent
  from `SPORTS_DATA_TYPE_META`). Hard proof of false-emptiness: 4,436 XG-captured league-dates vs only 9 XG_SHOTS
  captured; ≥1,675 of the identical XG-captured dates record XG_SHOTS `empty_confirmed`. Updated §5 with live counts +
  the proof, added a todo to register XG_SHOTS in `SPORTS_DATA_TYPE_META`, and corrected the `repos:` frontmatter
  (added `unified-trading-library` for §9.2 + `deployment-api` for the visibility fix; dropped the untouched
  `deployment-service`). No code shipped.
