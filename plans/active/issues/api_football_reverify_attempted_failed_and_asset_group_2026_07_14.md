---
doc_type: issue
title:
  "api_football final re-verify (task -004): 4,268 attempted_failed (~3,116 undocumented, INJURIES-dominant) + 22,668
  blank-asset_group sports rows + 1 defi/UNISWAP_V3-BASE row mis-filed in the sports manifest under source=api_football"
summary:
  "data_engineering VERIFY (slot-5, 2026-07-14) for task sports_data_sources_canonical_completion-004 (api_football
  final re-verify) measured against the live sports canonical (instruments-store-sports, 5.76M rows). PASS: 0
  duplicate-dedup-key groups; service_name is the 3 sanctioned values (instruments-service / backfill-teams-61-leagues /
  fill-missing-player-stats). RED: (A) 4,268 api_football attempted_failed vs the todo's 0-or-documented target — ~1,152
  are the already-tracked CF11 FIXTURE_STATS/EVENTS/LINEUPS P2 class, but ~3,116 are UNDOCUMENTED (INJURIES 1,946,
  FIXTURES 612, blank-data_type 461, PLAYER_STATS 73, TEAMS 24; 2014-01-01..2026-07-06, 75 leagues, 2,141 match-days).
  (B) 22,668 api_football rows carry a BLANK asset_group (should be sports) — the consolidator's per-AG asset_group heal
  only fires for market-data-tick-{ag} buckets, never the instruments-store-sports bucket, so blank/pre-v9 rows there
  never get stamped. (C) exactly 1 row is a genuine cross-asset_group contamination: date=2026-06-26
  venue=UNISWAP_V3-BASE asset_group=defi service_name=instruments-service capture_status=attempted_failed but
  source=api_football, sitting in the SPORTS manifest — a DeFi object mislabeled as an api_football sports capture."
status: open
priority: P1
nature: notes
asset_group: [sports, defi, meta]
stage: [meta]
repos: [instruments-service, market-tick-data-service, unified-trading-library]
scope: [engineer, admin]
tags: [api_football, attempted_failed, asset_group, sports, data-correctness, reverify, manifest]
related: [../sports_data_sources_canonical_completion_2026_07_13.md]
created: 2026-07-14
parent_epic: infrastructure_master
source:
  "data_engineering VERIFY worker (slot-5, planning VM), 2026-07-14, executing AO task
  sports_data_sources_canonical_completion-004. Measured against the live sports canonical
  (instruments-store-sports-prd-central-element-323112 _index/availability_index.parquet, 5,759,085 rows) via DuckDB
  over ADC; repro scripts scratchpad/apifootball_reverify.py + apifootball_findings_char.py."
locked_by:
resolved_by:
execution_scope: local-only
model_tier: sonnet-doable
drift_direction: advance-code
assigned_vm: planning
depends_on: []
---

## What I found

Task -004 ("api_football: final re-verify — 0 attempted_failed (or a documented operator-equivalent acceptable
residual), 0 dedup-key dup groups, correct service_name/asset_group") measured against the live sports canonical
(`instruments-store-sports-prd-central-element-323112`, `_index/availability_index.parquet`, 5,759,085 rows). Repro:
`scratchpad/apifootball_reverify.py` + `apifootball_findings_char.py`.

**PASS:**

- **0 duplicate-dedup-key groups** for api_football on the true dedup key (base + present optional dims).
- **service_name** = only the 3 sanctioned values (`instruments-service` 2,497,195 / `backfill-teams-61-leagues` 165,148
  / `fill-missing-player-stats` 8,678), all documented honest-provenance one-offs in the parent plan.

**RED (3 findings):**

### A) 4,268 attempted_failed — ~3,116 undocumented

| data_type       | attempted_failed | status                                          |
| --------------- | ---------------- | ----------------------------------------------- |
| INJURIES        | 1,946            | UNDOCUMENTED                                    |
| FIXTURES        | 612              | UNDOCUMENTED                                    |
| (blank)         | 461              | UNDOCUMENTED (blank data_type — itself suspect) |
| FIXTURE_STATS   | 408              | tracked (CF11 P2 backfill class)                |
| FIXTURE_LINEUPS | 384              | tracked (CF11 P2 backfill class)                |
| FIXTURE_EVENTS  | 360              | tracked (CF11 P2 backfill class)                |
| PLAYER_STATS    | 73               | UNDOCUMENTED                                    |
| TEAMS           | 24               | UNDOCUMENTED                                    |

~1,152 (FIXTURE_STATS/LINEUPS/EVENTS) are the already-filed CF11 `CF11_MATCH_DAY_EMPTY_GUARANTEED_TYPE` P2 backfill
(parent plan). The other **~3,116 (INJURIES-dominant) are not covered by any existing todo** and span 2014-01-01..
2026-07-06, 75 leagues, 2,141 match-days.

### B) 22,668 blank-asset_group api_football rows (should be `sports`)

Every one is an api_football sports data_type (INJURIES 8,042 / FIXTURE_EVENTS 6,791 / STANDINGS 3,360 / FIXTURES 2,311
/ TEAMS 770 / … both `empty_confirmed` and `captured`) whose `asset_group` column is BLANK. Root cause: the
consolidator's asset_group self-heal (`manifest_consolidator._asset_group_for_market_data_bucket` → REPLACE-coalesce
blank→bucket AG) only recognises `market-data-tick-{ag}` / prediction buckets; it returns `None` for the
`instruments-store-sports` bucket, so blank/pre-v9 rows in the sports manifest are never stamped `sports`. This
undercounts sports in any `GROUP BY asset_group` coverage rollup.

### C) 1 cross-asset_group contamination row

`date=2026-06-26 venue=UNISWAP_V3-BASE data_type='' asset_group=defi service_name=instruments-service capture_status=attempted_failed source=api_football`
— a DeFi (UNISWAP_V3-BASE) object sitting in the SPORTS manifest, mislabeled `source=api_football` with a blank
data_type. Wrong on venue/asset_group/source simultaneously; low volume (1 row) but a real mis-route.

## Why it matters

Data-pipeline correctness is the heartbeat. Finding A means real api_football INJURIES/FIXTURES/etc. failures are frozen
un-recovered; Finding B undercounts sports coverage on every asset_group rollup; Finding C is a cross-asset_group leak
that should never happen. None are blocked on credentials.

## Recommended decision + todos

- [ ] [DATA] P1. **Re-fetch backfill the ~3,116 UNDOCUMENTED api_football attempted_failed** (INJURIES 1,946, FIXTURES
      612, blank-data_type 461, PLAYER_STATS 73, TEAMS 24) via the existing per-fixture/per-entity recovery path
      (`instruments-service` `_fetch_sports_reference_data`, same pattern as
      `api_football_attempted_failed_residual_closer_2026_07_13.py`). Whatever genuinely re-fetches to 0 rows with a
      clean 2xx `FetchEvidence` → relabel `empty_confirmed(SOURCE_RETURNED_ZERO)`; the rest must capture. Investigate
      the 461 blank-data_type failures first (a blank data_type is itself suspect — likely a writer/enumerator bug).
      (repo: instruments-service)
- [ ] [DATA] P1. **Extend the consolidator asset_group heal to the instruments-store-sports bucket** so blank/pre-v9
      sports rows are stamped `asset_group=sports` at consolidation (mirror `_asset_group_for_market_data_bucket` for
      the `instruments-store-{ag}` bucket family, OR a one-off repair pass over the 22,668 blank rows). Fixes the sports
      coverage-rollup undercount. (repo: unified-trading-library)
- [ ] [DATA] P2. **Remove/relabel the 1 defi/UNISWAP_V3-BASE row mis-filed in the sports manifest under
      source=api_football** (date=2026-06-26). Trace the writer that emitted a UNISWAP_V3-BASE row with
      source=api_football into the sports bucket; delete the phantom row (CAS-safe) and fix the mis-route at source if
      reproducible. (repo: market-tick-data-service / instruments-service)

## Update 2026-07-15 — Finding A closed; Finding B grown (37x), Finding C unchanged, still root-caused

Live re-check against the current canonical (`instruments-store-sports-prd`, 5,432,276 rows) as part of this session's
final whole-plan re-verify:

- **Finding A (undocumented attempted_failed): CLOSED.** INJURIES and FIXTURES both now `0` (fixed
  `instruments-service@493393c8` + `21591e54` + `9b4f7655`, independently verified live). Total api_football
  `attempted_failed` is now **766** (was 4,268) — 305 is the already-tracked CF11 class (`PLAYER_STATS` 87,
  `FIXTURE_STATS` 80, `FIXTURE_EVENTS` 65, `FIXTURE_LINEUPS` 49, `TEAMS` 24), 461 is the blank-data_type residual
  (root-caused this session — see the sports plan's Progress Log 2026-07-15 entry — a genuinely separate class from
  finding A, not a re-fetch target). Both remaining classes are already tracked elsewhere; no action needed on this todo
  beyond what's already landed.
- **Finding B (blank asset_group): NOT closed, and much bigger than recorded here.** Re-measured 2026-07-15:
  api_football alone now has **844,209** blank-`asset_group` rows (was 22,668 on 2026-07-14 — a ~37x increase). This is
  the SAME root cause already documented above (the consolidator's asset_group heal never covers
  `instruments-store-sports`), not a new bug — the count grew because this session's own write volume was unusually
  large (a 328K-row pre-launch purge, multiple multi-hundred-thousand-row reconciliations/migrations, several
  residual-closer backfill rounds — none of these paths stamp `asset_group` explicitly, so they all landed as blank,
  same as every pre-v9 write always has). Also newly confirmed the SAME blank-asset_group pattern exists on every other
  sports source, not just api_football: footystats 99,048 / soccer_football_info 360 / transfermarkt 45 / open_meteo
  1,804 (`odds_api` and `mdps_odds_horizon_bucket` show **0** blank — those writers already stamp asset_group
  explicitly). The P1 todo above (extend the consolidator heal to `instruments-store-{ag}`) is the correct fix and
  should be scoped to ALL sports sources, not just api_football, given this — updating title/summary would be reasonable
  next time this doc is touched, but left as-is here to avoid rewriting another slot's filed finding without a fix in
  hand.
- **Finding C (defi/UNISWAP_V3-BASE contamination row): unchanged, still exactly 1 row, still open.**
- **Bonus, smaller finding**: a proper dedup-key check (including `instrument_id`, which the original PASS verdict's key
  did not — worth noting since it changes the "0 duplicate-dedup-key groups" PASS from 2026-07-14) finds exactly **2**
  duplicate groups, both `odds_api`/`trades`/`instrument_id∈{soccer_epl, soccer_italy_serie_a}` on `date=2026-06-21` —
  each is the same `instrument_id` captured twice with identical `row_count` at two different `written_at` timestamps (a
  benign double-write-event, not obviously corrupted underlying data) — small enough (2 groups, one date) not to warrant
  its own todo, noting here for completeness.
