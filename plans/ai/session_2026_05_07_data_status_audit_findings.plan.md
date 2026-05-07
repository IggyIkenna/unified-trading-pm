---
name: session_2026_05_07_data_status_audit_findings
overview:
  Thin wrapper-tracker for the 2026-05-07 deployment-ui data-status audit. Closes when all referenced line-items in the
  asset_group / manifest_migration master plans complete. Does NOT define new work — every finding folds into an
  existing master plan; this file just gives the operator a single deployment-UI surface to check progress against.
type: wrapper
epic: epic-code-completion
completion_gates:
  code: C5
  deployment: D3
  business: none
repo_gates:
  - repo: unified-trading-pm
    code: C2
    deployment: none
    business: none
depends_on:
  - sports_master_2026_05_07
  - predictions_master_2026_05_07
  - defi_master_2026_05_07
  - manifest_migration_master_2026_05_07
  - infrastructure_master_2026_05_07
todos: []
isProject: false
related:
  - data_status_drilldown_shard_atom_alignment_2026_05_07.plan.md
  - api_football_minimal_flattening_removal_2026_05_07.plan.md
---

# Session 2026-05-07 — Deployment-UI close-out tracker

Single-pane-of-glass for the data-status panel issues surfaced during the 2026-05-07 walkthrough. Each row references
the master plan that owns the actual fix; this tracker closes when every referenced master-plan todo is done. **No new
plan work belongs here** — folded into existing masters per user direction.

## A. Shipped this session (closed)

| #   | Issue                                                                                                                                         | Commit                                                                                                                           |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| A.1 | Slicer-induced 30-day default-window regression. Default startDate now `2018-01-01` (rollup origin).                                          | deployment-ui@`ebfbc5d`                                                                                                          |
| A.2 | Schema modal `"AUTO"` literal broke `instrument_catalogue` synthesis (instruments venue-level views).                                         | deployment-ui@`537d468`                                                                                                          |
| A.3 | Schema modal duplicated 'No schema yet' message (hardcoded UI block + backend message overlapped).                                            | deployment-ui@`537d468`                                                                                                          |
| A.4 | Coverage Summary header mislabeled `25,663 unique venues (latest day)` — actually `latest_day_instruments` sum.                               | deployment-ui@`537d468`                                                                                                          |
| A.5 | Honest-absence response too generic — added `probed_paths` field naming each candidate parquet URI.                                           | deployment-api@`4ca4bb7`                                                                                                         |
| A.6 | DeFi pool drilldown probed wrong hive key (`category=defi` only) + wrong venue partition (combined only). Now probes 4 candidates per alias.  | deployment-api@`0384eab`                                                                                                         |
| A.7 | DEFI canonicalisation closeout (8-commit thread from 2026-05-06) — manifest fully canonical, fallback removed, per-chain pre-launch clipping. | UTL@`248058bb`+`25ded4f3`, UAC@`405cbf5`+`f22f4b1`, MTDS@`8c3c2c7`, deployment-api@`64d2be9`+`14bbff9`, PM@`56850b0c`+`2bfe7f0f` |

## B. Open — owner plans already define the fix

Each row below references the master plan + the specific section/todo line(s) where the work lives. Tracker closes once
each owner plan checks those line-items off. **If a row's "owner" column is blank, the next maintenance pass on this
tracker should add the line-item to the named master plan** (do not invent a new plan).

| #    | Finding                                                                                                                                                                                                                                                                | Owner master plan                                                                                                                 | Owner section / line-item to verify                                                                                                                                                                                                                                                                                                             |
| ---- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| B.1  | api_football minimal-flattening (FIXTURE_STATS / EVENTS / LINEUPS / INJURIES drop nested arrays at write-time). Plan exists in `plans/ai/`; user direction 2026-05-07 = flatten + isolated re-fetch (separate `/fixtures/statistics` API call, no impact on FIXTURES). | `sports_master_2026_05_07`                                                                                                        | Add explicit todo group "API-Football payload flattening" referencing `plans/ai/api_football_minimal_flattening_removal_2026_05_07.plan.md` Phases 1–3. Migration shape: flip manifest → `attempted_failed reason=INCOMPLETE_PAYLOAD_PRE_FLATTENING` + delete thin parquets + re-fetch via dedicated VM.                                        |
| B.2  | UI drill-down hierarchy doesn't match codex shard-key matrix (CME options collapses across cluster membership; DeFi can't drill chain → protocol → data_type).                                                                                                         | `infrastructure_master_2026_05_07` (deployment-ui surface lives here) OR new feature in `consolidated_strategy_and_ui_2026_04_15` | Add reference to `plans/ai/data_status_drilldown_shard_atom_alignment_2026_05_07.plan.md` 5-phase plan.                                                                                                                                                                                                                                         |
| C.1  | LEAGUES daily-dump duplicates UAC `LeagueDefinition` refdata (3046 daily shards = pure waste; UAC has everything except `logo_url`).                                                                                                                                   | `manifest_migration_master_2026_05_07`                                                                                            | Add to refdata cadence migration: kill LEAGUES data_type, lift `logo_url` into UAC, flip manifest → `record_empty(reason=EXPECTED_DEPRECATED_DATA_TYPE)` + delete parquets.                                                                                                                                                                     |
| C.2  | ODDS in instruments-service — provenance suspect. Three candidates: odds_api (which belongs in MTDS not instruments-service), footystats_odds (separate folder per SSOT), api_football `/odds`. UAC has no contract for `(sports, ∅, odds)`.                           | `sports_master_2026_05_07`                                                                                                        | Add audit todo: trace the writer for `data_type=odds` in instruments-service, identify source, decide canonical home (MTDS for market-typed odds, instruments-service only if pre-game refdata), document in `codex/02-data/sports-data-source-coverage-matrix.md`.                                                                             |
| C.3  | PREDICTIONS vs ODDS overlap clarity. footystats publishes both `/odds` (market odds) and `/predictions` (model output odds-like probabilities).                                                                                                                        | `sports_master_2026_05_07`                                                                                                        | Add codex doc-only todo: clarify schema descriptions to call out provenance + computed-vs-market distinction.                                                                                                                                                                                                                                   |
| C.4  | PLAYER_VALUES schema only carries team-level aggregates (`squad_size`, `player_count`); per-player `market_value_eur` from Transfermarkt is dropped. Same minimal-flattening pattern as api_football.                                                                  | `sports_master_2026_05_07`                                                                                                        | Add Transfermarkt normalizer flatten todo: per-(team, player, season, fetch_day) row with `player_id`, `player_name`, `position`, `age`, **`market_value_eur`**, `contract_until`, `current_club_id`, `nationality_iso`. Existing team-aggregate parquet becomes a derived view OR dropped if features-sports rolls per-player at compute time. |
| C.5  | PLAYER_STATS — confirmed correct (api_football fully flattened, ~38 cols per player per fixture).                                                                                                                                                                      | n/a — no work needed                                                                                                              | Documented as the known-good reference shape for what the OTHER api_football data_types should look like post-flatten.                                                                                                                                                                                                                          |
| C.6  | SFI_PROGRESSIVE_STATS has rich content (~60 cols incl xG, dominance, AH/OU odds) but no `match_end_timer` / `ft_timer` column. Snapshots stop at the freeze point but we never persist that derivation.                                                                | `sports_master_2026_05_07` (groups with C.10)                                                                                     | Add freeze-detection writer + `match_end_time` column.                                                                                                                                                                                                                                                                                          |
| C.7  | Sanity sweep STANDINGS / WEATHER / XG / MATCHES schema-modal. XG (per-shot events) likely needs flatten audit; STANDINGS and MATCHES probably OK.                                                                                                                      | `sports_master_2026_05_07`                                                                                                        | Add audit todo: open schema modal per data_type, confirm column count vs source-payload signal density.                                                                                                                                                                                                                                         |
| C.8  | Cross-source dropped-data audit. api_football is one source where minimal-flattening landed; audit footystats / understat / DeFi adapter normalizers for the same stub-normalizer pattern.                                                                             | `manifest_migration_master_2026_05_07`                                                                                            | Add cross-source flatten audit todo.                                                                                                                                                                                                                                                                                                            |
| C.9  | AAVE_V3-ARBITRUM phantom rows — manifest claims 1781/1785 captured but on-disk listing returns 0 across all 4 layout candidates probed by the post-fix drilldown.                                                                                                      | `defi_master_2026_05_07`                                                                                                          | Run `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group defi --dry-run` → fix detected drift.                                                                                                                                                                                                                     |
| C.10 | `match_end_time` cascade is codified in CLAUDE.md (api_football native → SFI freeze → footystats/understat → kickoff+120min) but no writer implements. Load-bearing for odds-settlement timing.                                                                        | `sports_master_2026_05_07`                                                                                                        | Add 3-step todo: (1) FIXTURES write-time computation when `status_short ∈ {FT,AET,PEN}`; (2) SFI freeze-point detection; (3) UTL `resolve_match_end_time(fixture_id)` cascade resolver.                                                                                                                                                         |
| C.11 | TEAMS daily-shard refdata anti-pattern (3046 daily shards; should be per-(team, season)). VENUES (1/1 singleton) is correct. TEAMS already carries 7 venue\_\* cols; VENUES only adds OpenMeteo geo overlay. Codify refdata cadence SSOT.                              | `manifest_migration_master_2026_05_07`                                                                                            | Add refdata cadence migration (groups with C.1). UAC contract gains `cadence: "singleton"                                                                                                                                                                                                                                                       | "per_season" | "per_day"` field; data-status panel renders cadence-aware denominators. Decide VENUES dedup (fold into TEAMS or keep as geo-enrichment overlay). |
| C.12 | POLYMARKET "out of scope" badge in UI is technically correct: UAC declares `data_type=prediction_canonical_question_group` for POLYMARKET, MTDS still writes legacy per-base-asset (`BTC`/`ETH`/`SPX`/etc.). Badge resolves once predictions_master Phase 1 ships.     | `predictions_master_2026_05_07`                                                                                                   | Already covered: lifecycle ingestion + classifier + adapter migration (14/37 done). User direction 2026-05-07: NOT out of scope per intent — small Polymarket dataset means migration is feasible in one VM run. Confirm Phase 1 timeline against 2026-05-23 master deadline.                                                                   |

## Closure criteria

This wrapper closes (and gets archived) when:

1. Every B.1 / B.2 / C.1–C.12 row's referenced owner plan has the corresponding todo(s) added explicitly.
2. Each referenced todo gets ticked off in its owner plan.
3. The deployment-UI surface (visited by re-running the audit) no longer shows the issue (panel tells the truth: no
   suspicious counts, no `out of scope` for migrated venues, schema modals show full flattened shape, no missing
   drill-down depth).

Before archive: a follow-up agent walks the deployment-ui data-status panel and confirms each row above renders
correctly. If anything regressed (or new findings surface), they extend this tracker rather than discarding it.

## What this tracker is NOT

- **Not a plan.** It defines no work directly. Every fix lives in an owner master plan.
- **Not a duplicate.** When you find yourself describing a fix here in detail, that's the signal to add it to the owner
  master plan instead and link it from the relevant row.
- **Not infrastructure-aware.** This focuses on the data-status panel surface. UI / UX work that doesn't touch the audit
  findings goes in the relevant master.

## References

- `plans/active/sports_master_2026_05_07.plan.md` — owner of B.1 + C.2/C.3/C.4/C.6/C.7/C.10
- `plans/active/predictions_master_2026_05_07.plan.md` — owner of C.12 (POLYMARKET migration)
- `plans/active/defi_master_2026_05_07.plan.md` — owner of C.9 (AAVE_V3 phantom rows)
- `plans/active/manifest_migration_master_2026_05_07.plan.md` — owner of C.1 + C.8 + C.11 (refdata cadence +
  cross-source flatten)
- `plans/active/infrastructure_master_2026_05_07.plan.md` — owner of B.2 (deployment-ui drill-down)
- `plans/ai/data_status_drilldown_shard_atom_alignment_2026_05_07.plan.md` — folded into B.2 owner
- `plans/ai/api_football_minimal_flattening_removal_2026_05_07.plan.md` — folded into B.1 owner
- Live deployment-ui screenshots inspected this session (FIXTURE_STATS, FIXTURE_LINEUPS, ODDS, LEAGUES, PLAYER_VALUES,
  PLAYER_STATS, PLAYER_VALUES, TEAMS, VENUES, SFI_PROGRESSIVE_STATS, POLYMARKET prediction panel).
