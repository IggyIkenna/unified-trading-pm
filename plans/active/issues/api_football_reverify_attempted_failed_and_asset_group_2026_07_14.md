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
