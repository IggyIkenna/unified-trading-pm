---
name: session_2026_05_07_data_status_audit_findings
overview:
  Catalog of every audit finding from the 2026-05-07 deployment-ui data-status walkthrough. Mixes shipped fixes, open
  bugs, suspect data_types, and cross-source flattening gaps. Single inventory so one executing agent can pick up every
  open thread without re-deriving the audit. Per-finding columns: status (shipped/open/suspect), repo, scope, owner
  follow-up plan if it has one.
type: code
epic: epic-code-completion
completion_gates:
  code: C5
  deployment: D3
  business: none
repo_gates:
  - repo: deployment-api
    code: C2
    deployment: none
    business: none
  - repo: deployment-ui
    code: C2
    deployment: none
    business: none
  - repo: unified-api-contracts
    code: C2
    deployment: none
    business: none
  - repo: instruments-service
    code: C2
    deployment: none
    business: none
  - repo: unified-trading-pm
    code: C2
    deployment: none
    business: none
depends_on: []
todos: []
isProject: false
related:
  - data_status_drilldown_shard_atom_alignment_2026_05_07.plan.md
  - api_football_minimal_flattening_removal_2026_05_07.plan.md
  - data_status_multi_axis_shard_propagation_2026_05_06.plan.md (parent)
---

# Session 2026-05-07 — Data-status audit findings

## Why

User walked through the deployment-ui data-status panel and surfaced ~12 distinct issues spanning rendering bugs, schema
gaps, data-content gaps, and architectural confusions. Some shipped same-session; others need separate plans /
sub-plans. This file is the catalog so nothing falls between the cracks.

## Catalog

### A. Shipped this session (closed)

| #   | Issue                                                                                                                                                                                                                                                                                  | Commit(s)                                                                                                                        | Notes                                                                                                                                                                                                                                                                                                                   |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A.1 | Slicer-induced 30-day default-window regression. UI defaulted `startDate = today - 30d`; pre-slicer this was harmless (rollup-served paths ignored the window), post-slicer (deployment-api@`ad1e80b`) it correctly clipped → panel collapsed to 28 days/venue.                        | deployment-ui@`ebfbc5d`                                                                                                          | Default startDate now `2018-01-01` (workspace rollup origin). Codified in `feedback_rollup_slicer_default_window_must_match_rollup_origin.md`.                                                                                                                                                                          |
| A.2 | Schema modal `"AUTO"` literal broke `instrument_catalogue` synthesis. `firstDt ?? "AUTO"` fell through every backend lookup; venue-level click on instruments-service always returned 'no schema yet'.                                                                                 | deployment-ui@`537d468`                                                                                                          | Empty string instead of `"AUTO"` triggers the synthesis branch. Verified live: returns `TRADFI_INSTRUMENT_CATALOGUE` from CONTRACT_REGISTRY.                                                                                                                                                                            |
| A.3 | Schema modal duplicated 'No schema yet' message (hardcoded UI block + backend `schema.message` carried near-identical content).                                                                                                                                                        | deployment-ui@`537d468`                                                                                                          | UI now renders backend message only (with `whitespace-pre-wrap`).                                                                                                                                                                                                                                                       |
| A.4 | Coverage Summary header mislabeled `25,663 unique venues (latest day)` — actually `latest_day_instruments` sum. Real venue count ~67.                                                                                                                                                  | deployment-ui@`537d468`                                                                                                          | Relabeled to 'instruments (latest day, sum across asset groups)'.                                                                                                                                                                                                                                                       |
| A.5 | Honest-absence response too generic — operator can't tell path-drift from genuine absence.                                                                                                                                                                                             | deployment-api@`4ca4bb7`                                                                                                         | New `probed_paths` field + multi-line message naming the contract-registry key + each candidate parquet URI. SchemaModal renders monospace.                                                                                                                                                                             |
| A.6 | DeFi pool drilldown probed wrong hive key (`category=defi` only) + wrong venue partition shape (combined `venue={proto}-{chain}` only). Multi-chain protocols (AAVE_V3, UNISWAP_V3 on non-Ethereum chains) returned 'no pool data' even when parquets existed at the canonical layout. | deployment-api@`0384eab`                                                                                                         | Now probes 4 candidates per alias: 2 hive keys × 2 venue partitions. First-hit wins.                                                                                                                                                                                                                                    |
| A.7 | DEFI canonicalisation closeout (8 commits, parent thread from 2026-05-06).                                                                                                                                                                                                             | UTL@`248058bb`+`25ded4f3`, UAC@`405cbf5`+`f22f4b1`, MTDS@`8c3c2c7`, deployment-api@`64d2be9`+`14bbff9`, PM@`56850b0c`+`2bfe7f0f` | Manifest fully canonical (0 residual legacy underscore DeFi-venue rows); read-time fallback removed; `CHAIN_GENESIS_DATES` SSOT wired for per-chain pre-launch clipping. Captured in [project_data_status_multi_axis_phase_0_2_3_shipped_2026_05_06](project_data_status_multi_axis_phase_0_2_3_shipped_2026_05_06.md). |

### B. Open — needs planning + execution

#### B.1 — api_football minimal flattening (FIXTURE_STATS / EVENTS / LINEUPS / INJURIES)

`normalize_api_football_*`
([normalize.py:372-395](unified-api-contracts/unified_api_contracts/external/api_football/normalize.py#L372-L395)) are
3-line pass-through stubs. Each just stamps `fixture_id` on the raw dict; the nested `statistics: [...]`,
`events: [...]`, `startXI: [...]`, and 4 nested injury structs are never unpacked. Pyarrow drops the unflattenable
nested objects at parquet-write time, so on disk we keep only top-level scalars (`fixture_id`, `data_available_at`,
`formation` for lineups).

Per-data_type column count today vs intended:

| Endpoint               | Today                                      | Intended (after flatten)                                                                                                                                                                                                                                    |
| ---------------------- | ------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/fixtures/statistics` | 2 cols (`fixture_id`, `data_available_at`) | ~18 per (fixture, team): `team_id`, `is_home`, `shots_total/on/off/inside_box/outside_box`, `corners`, `offsides`, `ball_possession_pct`, `yellow_cards`, `red_cards`, `goalkeeper_saves`, `passes_total/accurate/pct`, `expected_goals`, `goals_prevented` |
| `/fixtures/events`     | 2 cols                                     | ~10 per event: `time_elapsed/extra`, `team_id/name`, `player_id/name`, `assist_id/name`, `event_type`, `event_detail`, `comments`                                                                                                                           |
| `/fixtures/lineups`    | 3 cols                                     | ~12 per (fixture, team, player): `team_id/name`, `formation`, `coach_id/name`, `player_id/name/number/pos/grid`, `is_starter`                                                                                                                               |
| `/injuries`            | 4 opaque struct cols                       | ~10 flat: `player_id/name/photo/type/reason`, `team_id/name`, `fixture_id`, `league_id/season`                                                                                                                                                              |

**Decision (user direction 2026-05-07)**: flatten, don't kill. The dropped data IS exactly what features-sports
calculators need (xG, possession, shots-on-target, lineup-strength). Each endpoint is an isolated API call distinct from
`/fixtures` proper, so re-fetch is independent.

**Migration mechanics for historical re-fetch**:

1. Flip every existing `(fixture_stats|fixture_events|fixture_lineups|injuries)` manifest row to `attempted_failed` with
   `error_reason="INCOMPLETE_PAYLOAD_PRE_FLATTENING"` (extend `EMPTY_CONFIRMED_REASONS` / equivalent failure-reason
   taxonomy in UAC if not already covered — currently covered by free-form `error_reason` strings; consider promoting to
   closed enum).
2. Delete the existing thin parquets at the canonical sports paths
   (`gs://sports-reference-{pid}/sports_reference/by_date/day=*/entity=fixture_stats/...`, etc.).
3. Forward-poll naturally re-fetches days the manifest now shows as `attempted_failed`. Spin a dedicated VM for
   historical (post-2020-06-06 per `DATA_TYPE_COVERAGE_START`) backfill.
4. UI shows 'missing' for these data_types until re-fetch completes — that's the honest state.

Plan:
[`api_football_minimal_flattening_removal_2026_05_07.plan.md`](api_football_minimal_flattening_removal_2026_05_07.plan.md)
(in `plans/ai/`). Update needed: change "kill fixture_stats" framing → "flatten + migrate" per user direction; add the
migration mechanics above.

#### B.2 — Drill-down hierarchy doesn't match codex shard-key matrix

UI today drills only `venue → instrument_type → days`. Codex says MTDS CeFi spot/perp =
`(venue, data_type, instrument_type, instrument_id, day)`; CeFi options/futures = bundled per-root; DeFi =
`(chain, venue/protocol, data_type, instrument_or_protocol_id, day)`. Operator can't navigate to "which (chain,
protocol, data_type) is dragging the denominator" or "which ES.OPT cluster is missing for 2024-01-15".

Plan:
[`data_status_drilldown_shard_atom_alignment_2026_05_07.plan.md`](data_status_drilldown_shard_atom_alignment_2026_05_07.plan.md)
(in `plans/ai/`). 5 phases: audit → deployment-api hierarchical endpoint → deployment-ui HierarchicalShardDrilldown →
per-shard download + missing surfacing → MTDS CLI shard-targeting (`--shard-key`, `--instrument-type`, `--root`, `--day`
flags).

### C. Suspect data_types — need investigation before action

Each row below is a question the audit raised but didn't resolve. The right move per row is "audit, then write a plan
slice OR confirm it's fine." Don't rip-out without confirming the consumer doesn't depend on it.

#### C.1 — `LEAGUES` (sports) — daily dump duplicates UAC reference data

3046/3049 daily LEAGUES shards. Schema: `league_id`, `name`, `country`, `league_type`, `logo_url`. UAC already has all
of these as static reference data:

- `LeagueDefinition`
  ([league_registry.py:28](unified-api-contracts/unified_api_contracts/canonical/domain/sports/league_registry.py#L28))
  carries `league_id`, `name`, `country`, `league_type`.
- `get_provider_league_id(canonical_league_id, provider)`
  ([provider_league_ids.py:689](unified-api-contracts/unified_api_contracts/canonical/domain/sports/provider_league_ids.py#L689))
  handles per-season footystats ID mapping (which DOES change yearly — captured in `FOOTYSTATS_SEASON_IDS` +
  `FOOTYSTATS_HISTORICAL_SEASON_IDS`).
- Only `logo_url` isn't in UAC — and even that is static per league.

**Action**: kill the LEAGUES daily-dump data_type. Lift `logo_url` into UAC `LeagueDefinition` if any consumer needs it.
Migration: flip manifest rows to `record_empty(reason=EXPECTED_DEPRECATED_DATA_TYPE)` (extend reason taxonomy if
needed) + delete parquets + remove the orchestrator scheduler entry + remove the UAC contract. Consumers (deployment-ui
league-name lookups, features-sports league-grouping) read directly from `LeagueDefinition` per the existing
`get_provider_league_id` import path.

#### C.2 — `ODDS` (sports, instruments-service) — what is it?

Schema modal shows `Source: none` (no UAC contract registered for `(sports, ∅, odds)`) AND no parquet found at the
probed paths. The data_type appears in the panel (93657/101572 shards) but the schema is unknown.

**Audit question**: which provider actually writes this folder? Three candidates:

- **odds_api** (canonical market-odds source). Per workspace architecture, odds_api odds belong in MTDS
  (market-tick-data-service) not instruments-service. If instruments-service writes odds_api odds too, that's a
  duplicate write path — pick one and remove the other.
- **footystats_odds**. Per the SPORTS path SSOT (the 2026-04-29 phantom-row audit fix), footystats odds live under
  `entity=footystats_odds/` — different folder from `entity=odds/`. If `entity=odds/` is footystats_odds written under
  the wrong folder name, it's a path-drift bug.
- **api_football_odds**. API-Football has a `/odds` endpoint too. If we're calling that AND it overlaps with
  footystats_odds AND odds_api, that's three sources for the same content.

Action: trace the writer for `data_type=odds` in instruments-service, identify the source, decide the right home (MTDS
for market-data-typed odds, refdata stays in instruments-service if it's pre-game opener-snapshot). If it duplicates
MTDS odds_api, kill the instruments-service path. Document the canonical home in
`codex/02-data/sports-data-source-coverage-matrix.md`.

#### C.3 — `PREDICTIONS` (sports) vs `ODDS` — overlap?

`PREDICTIONS` data_type is 93826/101572 shards. Footystats publishes both `/odds` (market odds) AND `/predictions`
(their model output — which is also expressed as odds-like probabilities). User correctly noted these can be confused.

Audit question: does our `PREDICTIONS` data_type carry footystats' MODEL output (predicted odds)? Or is it something
else (e.g. `predictions` table name lifted from API but actually fetched market odds)? Verify the schema modal columns
match the source endpoint payload. Document the distinction in codex.

#### C.4 — `PLAYER_VALUES` (sports, transfermarkt) — only team-level aggregates

User screenshot shows schema: `team_id`, `name`, `squad_size`, `player_count`, `league_id`, `canonical_league`,
`season`. **Missing the actual per-player euro-denominated market values** — Mbappe €180m, Haaland €200m, etc. — which
is the high-signal data Transfermarkt is famous for.

This is the same minimal-flattening pattern as api_football: the adapter reads Transfermarkt's per-team squad-page
response, computes summary aggregates (squad_size = how many players, player_count = how many have valuations), and
drops the per-player array.

Audit + plan needed: extend the Transfermarkt normalizer to flatten the per-player array. New shape: one row per (team,
player, season, fetch_day) with columns `player_id`, `player_name`, `position`, `age`, `market_value_eur` (the actual
€value), `contract_until`, `current_club_id`, `nationality_iso`, etc. Existing team-aggregate parquet stays as a derived
view (or features-sports rolls it from the per-player parquet at compute time).

#### C.5 — `PLAYER_STATS` (sports) — source confirmed api_football

Per schema modal columns (`fixture_id`, `team_id`, `player_id`, `rating` described as "API-Football player rating",
`minutes_played`, shot/pass/tackle/save/duel breakdown), confirmed source = api_football `/fixtures/players` endpoint.
Unlike fixture_stats / fixture_events / fixture_lineups, PLAYER_STATS IS fully flattened today (~38 columns per player
per fixture). Module docstring at
[`_sports_match_contracts.py:26-27`](unified-api-contracts/unified_api_contracts/internal/schemas/_sports_match_contracts.py#L26-L27)
calls this out: "PLAYER_STATS is the exception — it ships fully flattened with all ~38 player-level metrics."

**Action**: nothing — already correct. Document in plan as the known-good reference for what the OTHER api_football
data_types should look like after flattening.

#### C.6 — `SFI_PROGRESSIVE_STATS` (sports, soccer_football_info) — rich content, but NO match-end-time column

60494/62766 shards. Schema IS fully flattened (~60 columns: `dominance_pct`, `xg_home/away`,
`dominance_index_home/away`, `dominance_avg_home/away`, `attacks/dangerous/normal × home/away`,
`shots_total/on_target/off_target`, `corners`, `fouls`, `cards`, `substitutions`, `odds_1x2_home/draw/away`,
`odds_ou_over/under/line`, `odds_ah_home/away/line`, `odds_asian_corner_*`, `ht_start_timer`, `ht_end_timer`,
`data_available_at`).

**Audit gap (2026-05-07 user observation)**: schema has `ht_start_timer` + `ht_end_timer` (halftime break boundaries)
but NO `match_end_timer` / `ft_timer` / `final_whistle_time` column. SFI publishes a progressive `timer_seconds` that
increments through the match; the FREEZE point of that timer (when consecutive snapshots stop advancing) IS the
match-end signal. We're capturing every snapshot but not deriving / persisting the freeze point. See C.10 below — this
is the load-bearing gap.

#### C.10 — `match_end_time` derivation cascade is codified but writer-side implementation may be incomplete

CLAUDE.md workspace rule names the cascade:

> fixture_stats / fixture_player_stats → `match_end_time` (detected via cascade: api_football native → SFI progressive
> freeze → footystats / understat → low-confidence `kickoff + 120min` fallback)

But:

- **api_football native**: FIXTURES schema has `periods_first` (1H start epoch), `periods_second` (2H start epoch),
  `status_short` ('FT'/'AET'/'PEN'/'CANC'/...), `status_elapsed_time` (minutes elapsed). No explicit `match_end_time`
  column. Could derive: for `status_short=FT`, end ≈ `periods_second + 45min + injury_time`; for `AET`, `+ 30min` (15 ET
  each half); for penalty shootout, `+5min`. Computed at write-time would be fine; today not done.
- **SFI progressive freeze** (C.6 above): SFI publishes `timer_seconds` per snapshot. The last snapshot before the timer
  stops advancing is the match-end signal. Today we capture every snapshot but don't derive the freeze point — the
  contract has `ht_start_timer`/`ht_end_timer` for halftime but no `ft_timer`/`match_end_time` for full-time.
- **footystats / understat**: post-match endpoints return after the game; the `available_at` of those rows is
  post-match, but that's reception time not match-end time per se.
- **Fallback**: `kickoff + 120min` (low-confidence — assumes the game went to AET).

**Why this matters**: `match_end_time` is the load-bearing field for **odds-market settlement timing**. A settlement
feature wants to know "the moment after the final whistle when the bookmaker will resolve the market." Without an
authoritative `match_end_time` column on fixtures, we either:

- Use `data_available_at` of post-match data (reception, not settlement) — biases the settlement feature.
- Use `kickoff + 120min` fallback — wrong by 30+ minutes for non-AET games.
- Use `status_elapsed_time` from the last in-play FIXTURES snapshot — only works if FIXTURES is also written
  progressively (today it's mostly the post-match status).

**Action**: 3-step plan

1. **api_football side**: extend the FIXTURES writer to compute `match_end_time` at write-time when
   `status_short ∈ {FT, AET, PEN}` using `periods_second` + reg-time + ET + injury-time. Add to UAC contract.
2. **SFI progressive freeze side**: extend SFI_PROGRESSIVE_STATS adapter to detect freeze (last snapshot before timer
   stops advancing) and stamp `match_end_time` on the final-snapshot row. Or persist a derived
   `(fixture_id, match_end_time)` table somewhere (small, 1 row/fixture).
3. **Cascade resolver**: features-sports calculator-side helper `resolve_match_end_time(fixture_id)` that walks the
   cascade in priority order (api_football FIXTURES → SFI freeze → fallback). Lift to UTL or
   `unified-trading-library/availability_stamping.py` if multiple consumers need it.

This SHOULD have been part of either the api_football flattening plan (B.1) or the predictions canonical-question
lifecycle plan, but isn't currently named. Add as its own slice or fold into B.1 under "FIXTURES enrichment".

#### C.7 — Other sports data_types — quick sanity sweep

Per the screenshot: STANDINGS (33515/33527), TEAMS (3046/3049), VENUES (1/1), WEATHER (70899/70998), XG (12785/12805),
MATCHES (101524/101572). Audit each schema modal for column count + signal density. Some should be small (TEAMS, VENUES
= static refdata). Others (XG = per-match per-shot xG events) need real content to be useful — verify they're not
minimal-flattened.

#### C.8 — Cross-source dropped-data audit (footystats / understat / DeFi)

api_football is one source where minimal-flattening landed. Audit the other source-side normalizers for the same
pattern:

- `unified_api_contracts/external/footystats/normalize.py` — already flattening per row?
- `unified_api_contracts/external/understat/normalize.py` — xG events, definitely should be per-event flat
- `unified_api_contracts/external/transfermarkt/normalize.py` — covered by C.4 above
- `unified_api_contracts/external/soccer_football_info/normalize.py` — covered by C.6 above
- DeFi adapters in MTDS: `dex_pools_handler` / `dex_swaps_handler` / `lending_indices_handler` etc. — verify per-pool /
  per-position normalization isn't dropping fields (DEX swaps in particular have rich `swap_amount0` / `swap_amount1` /
  `tick` / `liquidity` payloads).

#### C.9 — AAVE_V3-ARBITRUM phantom-rows scenario

Manifest shows AAVE_V3-ARBITRUM = 1781/1785 shards captured (99.8%) but on-disk listing returns 0 across all 4 layout
candidates probed by the post-fix `_list_defi_objects_with_aliases`. This matches the 'phantom rows' incident class —
manifest claims captured, parquets aren't where probes look.

Audit step 1: list the actual writer's GCS path for AAVE_V3-ARBITRUM lending_indices on a recent day. Compare against
the 4 candidates the drilldown probes. If it's at a 5th layout, extend the prober. If the parquets genuinely don't
exist, run the phantom-rows reconciler
(`instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group defi --dry-run`).

### D. Migration / decision matrix per finding

| #    | Action                                  | Migration shape                                                                                                                     | Owner plan                                      |
| ---- | --------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| B.1  | Flatten api_football                    | flip manifest → `attempted_failed reason=INCOMPLETE_PAYLOAD_PRE_FLATTENING` + delete parquets + re-fetch                            | api_football plan                               |
| B.2  | Hierarchical drill-down                 | additive — no migration                                                                                                             | drill-down plan                                 |
| C.1  | Kill LEAGUES daily dump                 | `record_empty reason=EXPECTED_DEPRECATED_DATA_TYPE` + delete parquets + remove orchestrator + UAC contract + lift `logo_url` to UAC | TBD                                             |
| C.2  | Resolve ODDS provenance                 | depends on outcome — may be a kill (duplicate of MTDS) OR a path-drift fix                                                          | TBD                                             |
| C.3  | Document PREDICTIONS vs ODDS            | doc-only (codex); maybe rename data_type if confusing                                                                               | TBD                                             |
| C.4  | Flatten PLAYER_VALUES                   | same shape as B.1 — flip + delete + re-fetch with per-player flatten                                                                | TBD                                             |
| C.5  | (None — already correct)                | n/a                                                                                                                                 | n/a                                             |
| C.6  | Audit SFI_PROGRESSIVE_STATS             | TBD pending audit                                                                                                                   | TBD                                             |
| C.7  | Sanity sweep other sports data_types    | TBD per-data_type                                                                                                                   | TBD                                             |
| C.8  | Cross-source normalizer audit           | TBD per-source                                                                                                                      | TBD                                             |
| C.9  | AAVE_V3 phantom-rows                    | run reconcile_phantom_manifest_rows_all.py --asset-group defi                                                                       | TBD                                             |
| C.10 | `match_end_time` cascade implementation | additive write-time column on FIXTURES + SFI freeze detection + UTL resolver helper                                                 | TBD (load-bearing for odds-settlement features) |

## What this plan does

Acts as the **single inventory** of session findings so a follow-up agent doesn't have to re-derive the audit. Each
`B.*` and `C.*` item is independently scoped — pick whichever matters most given remaining time-to-launch.

**Suggested execution order** (assuming live-DeFi 2026-05-23 deadline + value-density per item):

1. **C.9 phantom-rows reconcile** — fast, exposes data-quality reality. (1 day)
2. **C.1 LEAGUES kill** — clean, removes daily noise. Releases API quota + storage. (1 day)
3. **C.2 ODDS provenance** — must resolve before we trust the sports panel. (1 day audit + decision)
4. **B.1 api_football flatten** — biggest features-sports value unlock. (3-5 days incl. backfill VM)
5. **C.4 PLAYER_VALUES flatten** — same pattern as B.1, reuse migration shape. (2 days)
6. **B.2 drill-down hierarchy** — pure UX improvement, lower urgency than data-content unlocks. (3-5 days)
7. **C.3 / C.6 / C.7 / C.8** — incremental audits. Defer if 2026-05-23 budget binds.

## What this plan does NOT do

- **Doesn't ship code itself.** This is the catalog. Each `B.*`/`C.*` row gets its own plan slice when an executing
  agent picks it up.
- **Doesn't gate the parent multi-axis plan close.** That plan
  ([`data_status_multi_axis_shard_propagation_2026_05_06.plan.md`](data_status_multi_axis_shard_propagation_2026_05_06.plan.md))
  Phase 3 is shipped; the residual cell-grid wiring (B.2 above) is its natural follow-up but lives in the drill-down
  plan now.
- **Doesn't commit to a specific kill-or-flatten decision per row.** C.1/C.2/C.3/C.4 each need a per-row audit + user
  decision before the migration runs. The catalog frames the decision; it doesn't pre-commit it.

## References

- Live deployment-ui screenshots inspected this session — 6 schema modal views (FIXTURE_STATS, FIXTURE_LINEUPS, ODDS,
  LEAGUES, PLAYER_VALUES, PLAYER_STATS) plus DEFI panel + DEFI pool drilldown.
- Sister plans: api_football flatten (`plans/ai/api_football_minimal_flattening_removal_2026_05_07.plan.md`), drill-down
  (`plans/ai/data_status_drilldown_shard_atom_alignment_2026_05_07.plan.md`).
- Workspace rules invoked: shard-granularity SSOT, manifest-migration-not-fallback, per-asset-group shard-key matrix,
  sports GCS path SSOT, asset_group hive-key canonical/legacy probing.
