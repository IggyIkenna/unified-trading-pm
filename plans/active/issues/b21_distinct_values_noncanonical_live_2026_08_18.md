---
doc_type: issue
title: B21 verification — live Distinct Values panel shows 113 non-canonical entries across 4 of 5 asset groups
summary: >-
  Live query of the deployment-api Distinct Values enumeration (all 5 asset groups) against the newest honest-coverage
  rollup finds B21 currently FAILS with 113 non-canonical entries (defi 38, sports 71, cefi 1, prediction 1, tradfi 2),
  most unaccounted for by the existing accepted-exceptions registry; 8 follow-up todos filed to classify and remediate.
created: 2026-08-18
author: data_engineering (slot 4, cross_cutting_satellite_ao_dispatch_batch15 item 1)
assigned_vm: planning
status: open
nature: issue
asset_group: [cross-cutting, defi, sports, cefi, tradfi, prediction]
stage: [data]
repos: [deployment-api, unified-api-contracts, market-tick-data-service, market-data-processing-service]
scope: [engineer]
parent_epic: security_and_cross_cutting_master
priority: P1
tags: [b21, distinct-values, canonical-drift, data-pipeline-completion]
related:
  [
    /plans/active/cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md,
    /plans/active/data_pipeline_completion_2026_08_21.md,
  ]
locked_by:
resolved_by:
source: >-
  cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md item 1 — "Verify B21: Distinct Values in the deployment
  UI shows zero non-canonical values, per asset group."
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# B21 verification — live result

## What I found

Ran the live `deployment_api.routes.data_status._distinct_values` enumeration (the exact code path backing
`GET /distinct-values/{asset_group}`) against the newest nightly honest-coverage rollup
(`source_date=2026-08-18`, `generated_at=2026-08-18T00:49:39Z`) for all 5 registered asset groups
(`VENUES_BY_ASSET_GROUP` keys: cefi, defi, prediction, sports, tradfi). Single bounded read — no whole-corpus GCS
walk (B13 discipline).

**B21 FAILS.** 113 non-canonical entries total, none of them already covered by the module's existing
`_ACCEPTED_EXCEPTIONS` registry (those are excluded from these counts already):

| Asset group | venues | instrument_types | data_types | chains | total |
| --- | --- | --- | --- | --- | --- |
| cefi | 0 | 0 | 0 | 1 (`<blank>`) | 1 |
| defi | 34 | 1 (`<blank>`) | 2 | 1 (`HYPERLIQUID`) | 38 |
| prediction | 0 | 0 | 0 | 1 (`<blank>`) | 1 |
| sports | 17 | 46 | 7 | 1 (`<blank>`) | 71 |
| tradfi | 0 | 1 (`<blank>`) | 0 | 1 (`<blank>`) | 2 |

Full per-axis, per-value lists (excerpted, non-blank only):

- **defi venues (34)**: `AAVEV3`, `AERODROME_V3-BASE`, `ASTER`, `BALANCER-{ARBITRUM,AVALANCHE,BASE,ETHEREUM,OPTIMISM,POLYGON}`,
  `BLAZESTAKE`, `CAMELOT_V3-ARBITRUM`, `CURVE-{AVALANCHE,ETHEREUM}`, `EXTENDED`, `GMX`, `HYPERLIQUID`,
  `KAMINO-SOLANA`, `KAMINO_LENDING`, `LIGHTER`, `MARGINFI-SOLANA`, `PANCAKESWAP_V3-{BASE,BSC,ETHEREUM}`,
  `SOLBLAZE-SOLANA`, `SOLEND-SOLANA`, `SUSHISWAP-ARBITRUM`, `SUSHISWAP_V3-{AVALANCHE,BASE,ETHEREUM}`,
  `UNISWAP_V3-{ARBITRUM,BASE,ETHEREUM,OPTIMISM,POLYGON}` — these read as chain-qualified venues not present in
  `ALL_DEFI_VENUES` (the vocabulary `_comparison_set` already widens to for defi) — either genuinely new/unregistered
  venue+chain combos, or a chain-suffix stripping edge case in `_defi_bare_venue_bases` for names that already
  contain a chain-like segment mid-string (e.g. `KAMINO-SOLANA` vs `KAMINO_LENDING`). Not yet root-caused here.
- **defi data_types (2)**: `dex_pools`, `dex_swaps` — not in `DATA_TYPES_BY_ASSET_GROUP['defi']`.
- **defi chains (1)**: `HYPERLIQUID` — a venue name leaking into the chains axis, or a genuinely new chain not in
  `MAINNET_CHAIN_IDS`.
- **sports venues (17, non-blank)**: `BETANO_UK`, `BETFRED_UK`, `BETUS`, `BOYLESPORTS`, `FANATICS`, `FOOTBALL`,
  `GROSVENOR`, `KALSHI`, `LADBROKES_UK`, `LEOVEGAS`, `LOWVIG`, `MYBOOKIEAG`, `ODDS_API`, `SPORT888`, `UNKNOWN`,
  `WILLIAMHILL_US` — mostly ODDS_API bookmaker fan-out spellings NOT already in
  `SPORTS_ODDS_API_ACCEPTED_NONCANONICAL_BOOKMAKERS` (that registry has 20 specific bookmaker names; these are
  different/newer spellings), plus `FOOTBALL`/`ODDS_API`/`UNKNOWN` which look like source/category labels leaking
  into the venue axis rather than real venues.
- **sports instrument_types (46, non-blank)**: 18 `ASIAN_HANDICAP_*` and 15 `OVER_UNDER_*` line-value variants not
  in `SPORTS_MARKET_TOKEN_ACCEPTED_NONCANONICAL_INSTRUMENT_TYPES`, plus `ODDS` and 12 lowercase bookmaker-named
  instrument_type stamps (`betmgm`, `betway`, `bovada`, `coral`, `fanduel`, `ladbrokes_uk`, `paddypower`, `pinnacle`,
  `skybet`, `unibet_uk`, `williamhill`) — a venue name appearing as an instrument_type value looks like a
  writer-side column-swap bug, not naming drift.
- **sports data_types (7)**: `ARBITRAGE_OPPORTUNITY`, `odds_horizon_bucket_{15m,1d,1h,4h}`, `odds_movement`,
  `odds_snapshot` — not in `DATA_TYPES_BY_ASSET_GROUP['sports']` and not in
  `SPORTS_DATA_TYPE_ACCEPTED_STALE_UPPERCASE_RESIDUE`.
- **cefi/prediction/tradfi**: only the `<blank>` sentinel row on the `chains` axis (expected — those asset groups
  are not chain-bearing) plus tradfi's `<blank>` on `instrument_types`. No REAL non-blank drift found for these 3
  asset groups in this run.

## Why it matters

B21 (`data_pipeline_completion_2026_08_21.md`) is an operator-set Friday 2026-08-21 gate: "zero non-canonical
entries in Distinct Values in the deployment UI, per asset group... that surface is the acceptance check." This
run shows it is not close to green for defi and sports specifically — 38 and 71 entries respectively. Two
sub-classes of finding here are qualitatively different and should be triaged separately, not lumped:

1. **Extend `_ACCEPTED_EXCEPTIONS`** — known, already-understood spellings (e.g. more ODDS_API bookmaker fan-out,
   more sports line-value granularity) that are real but permanently accepted, same shape as the existing 9
   registry entries.
2. **Genuine drift needing a code/registry fix** — the defi venue-vocabulary gap (34 entries, largest single
   cluster), the sports venue-axis category leakage (`FOOTBALL`/`ODDS_API`/`UNKNOWN`), and the sports
   instrument_type column-swap-looking lowercase bookmaker names, which read as a writer bug rather than naming
   drift and deserve investigation before being waved through as "accepted".

## Recommended decision

Root-cause and remediate per asset group; do not bulk-accept without investigation given the column-swap-shaped
sports instrument_type finding above.

- [x] ✅ [DATA] P1. Root-cause the 34 defi non-canonical venue entries — determine whether each is a genuinely
      unregistered venue+chain combo (needs adding to `ALL_DEFI_VENUES` as `pipeline`-phase) or a
      `_defi_bare_venue_bases` chain-suffix-stripping edge case for names containing a chain-like infix (e.g.
      `KAMINO-SOLANA`). Repo: unified-api-contracts (registry) or deployment-api (`_distinct_values.py`).
      Done-when: each of the 34 values is classified and either registered or the comparison logic fixed.
      **DONE 2026-08-19 (slot-33).** Classified all 34 programmatically against the live UAC registry
      (`ALL_DEFI_VENUES`/`LEGACY_DEFI_VENUE_ALIASES`/`MAINNET_CHAIN_IDS`) — 3 classes:
      1. **26/34 — comparison-logic bug, FIXED**: the raw manifest value is a LITERAL exact member of
         `ALL_DEFI_VENUES` in its full composite `PROTOCOL-CHAIN` form (e.g. `BALANCER-ARBITRUM`,
         `UNISWAP_V3-ETHEREUM`, `KAMINO-SOLANA`, `SOLEND-SOLANA`), but `_comparison_set` only compared against
         the chain-suffix-STRIPPED bare-base set, discarding the valid literal-composite match. Fixed by
         comparing against the union of bare bases and the full `ALL_DEFI_VENUES` set —
         `deployment-api@03d56dab24`.
      2. **2/34 — known aliases, FIXED**: `AAVEV3` / `BLAZESTAKE` are `LEGACY_DEFI_VENUE_ALIASES` keys already
         folded by `normalize_defi_venue`, never consulted by this panel. Added
         `DEFI_VENUE_ACCEPTED_NONCANONICAL_ALIASES` (mirrors `CEFI_VENUE_ACCEPTED_NONCANONICAL_ALIASES`),
         wired into `_ACCEPTED_EXCEPTIONS[("venues", "defi")]` — `unified-api-contracts@1c14d7aafc`.
      3. **1/34 — dead residue, FIXED**: `GMX` was removed from `ALL_DEFI_VENUES` 2026-07-25 (operator ruling,
         `defi_gmx_venue_removal_2026_07_25.md`, unreliable data); repo-wide grep confirms zero live
         MTDS/instruments-service adapter code stamps it — pure historical residue. Added
         `DEFI_VENUE_ACCEPTED_DEAD_RESIDUE` (same UAC commit), wired into the same `_ACCEPTED_EXCEPTIONS` entry.
      4. **5/34 — genuinely unregistered, filed separately**: `ASTER`, `EXTENDED`, `HYPERLIQUID`,
         `KAMINO_LENDING`, `LIGHTER` are not in `ALL_DEFI_VENUES`/`LEGACY_DEFI_VENUE_ALIASES` in any form. These
         need real registry-phase (`live` vs `pipeline`) + writer-trace judgment calls a mechanical fix would
         risk getting wrong (per this same file's own D1b/CHAINLINK-* precedent) — filed as
         `plans/active/issues/b21_defi_venue_5_unregistered_perp_dex_2026_08_19.md` with full per-value
         evidence + 4 scoped follow-up todos, not folded into this item.
      Verified: re-classifying all 34 against the shipped fix + new accepted-exception registries confirms
      exactly the 5 above remain flagged — the other 29 now resolve correctly (26 canonical, 3
      accepted-exception).
- [ ] [DATA] P1. Root-cause the 2 defi non-canonical data_types (`dex_pools`, `dex_swaps`) — add to
      `DATA_TYPES_BY_ASSET_GROUP['defi']` if genuinely produced, else trace the writer emitting them. Repo:
      unified-api-contracts / market-tick-data-service. Done-when: a written determination + fix lands.
- [ ] [DATA] P1. Investigate the sports instrument_types axis carrying lowercase bookmaker names (`betmgm`,
      `betway`, `bovada`, `coral`, `fanduel`, `ladbrokes_uk`, `paddypower`, `pinnacle`, `skybet`, `unibet_uk`,
      `williamhill`) — this looks like a venue/instrument_type column swap in the writer, not naming drift.
      Repo: market-data-processing-service or sports data writer. Done-when: root cause identified; if a real
      writer bug, filed as its own P0 issue (data-correctness, per CLAUDE.md governance rule).
- [ ] [DATA] P2. Investigate sports venue-axis entries `FOOTBALL`, `ODDS_API`, `UNKNOWN` — these read as
      source/category labels leaking into the venue column rather than real bookmaker names. Repo: sports data
      writer. Done-when: root cause identified and either fixed at the writer or added as an accepted exception
      with a stated reason.
- [ ] [DATA] P2. Extend `SPORTS_ODDS_API_ACCEPTED_NONCANONICAL_BOOKMAKERS` / add a new registry export for the
      remaining sports venues (`BETANO_UK`, `BETFRED_UK`, `BETUS`, `BOYLESPORTS`, `FANATICS`, `GROSVENOR`,
      `LADBROKES_UK`, `LEOVEGAS`, `LOWVIG`, `MYBOOKIEAG`, `SPORT888`, `WILLIAMHILL_US`) once each is confirmed a
      genuine, permanently-accepted bookmaker fan-out spelling (not a writer bug). Repo: unified-api-contracts.
      Done-when: registry updated and this panel's sports venue count drops accordingly.
- [ ] [DATA] P2. Extend the sports instrument_types accepted-exception registry (or fix the writer per the P1 item
      above) for the 33 remaining `ASIAN_HANDICAP_*`/`OVER_UNDER_*`/`ODDS` line-value variants once classified.
      Repo: unified-api-contracts. Done-when: registry updated or writer fixed.
- [ ] [DATA] P2. Investigate the 7 sports non-canonical data_types (`ARBITRAGE_OPPORTUNITY`,
      `odds_horizon_bucket_*`, `odds_movement`, `odds_snapshot`) — add to `DATA_TYPES_BY_ASSET_GROUP['sports']` if
      genuinely produced and permanent, else trace the writer. Repo: unified-api-contracts. Done-when: a written
      determination + fix/registry update lands.
- [ ] [DATA] P3. Investigate the recurring `<blank>` chain/instrument_type sentinel rows across cefi, defi,
      prediction, tradfi (5 occurrences) — confirm these are honest-absence (no chain/instrument_type ever
      stamped for non-chain-bearing asset groups) rather than a writer omission. Done-when: each `<blank>` is
      confirmed expected or traced to a specific writer gap.
