---
scope: [engineer, admin]
---

# Instruments-live architecture (entry-point)

## What live-mode is for instruments

Live-mode for instruments-service refreshes **reference data** — catalog rows (root, instrument_id, expiry, league_id,
team_id, market_id, canonical_question_group) — not market ticks. The service emits the same shape as a batch run, just
with a "now" lookback instead of a historical date.

## Same path as batch (no separate live path)

Live-mode writes parquet to the **identical GCS path** as batch. There is no `pipeline_mode=live` partition for
instruments because instruments are catalog state, not time-series ticks. Downstream consumers (MTDS catalog load,
features-\* preflight, strategy preflight) always read from the same path regardless of whether the row was written by a
live trigger or a batch run.

## T+1 is audit, not backfill

The next morning a retrospective audit job re-runs each (asset_group, entity-type) for the prior day from the
historical-batch source and compares against what live wrote. Discrepancies above tolerance escalate via
`INSTRUMENTS_LIVE_T1_AUDIT_DISCREPANCY` and the
[`t1-audit-discrepancy.md`](../15-runbooks/instruments-live/t1-audit-discrepancy.md) playbook. T+1 is **not** a parallel
backfill — the live row stays in place; the audit job only writes a discrepancy report.

## Trigger-driven (sports), wall-clock-driven (cefi/tradfi/prediction)

Sports lifecycle is event-driven (kickoff windows, season rolls, transfer windows) so triggers fire on schedule keyed to
those events. Other asset_groups poll on a fixed cadence (15-min cefi/tradfi OHLCV, 15-min prediction market-discovery).
Cloud Scheduler is the trigger driver for both shapes. Per-trigger cadence + source + downstream owner doc is in the
routing table below.

## Per-(asset_group, entity-type) routing table

| asset_group | entity-type                                                     | Cadence / Trigger                      | Source adapter                        | Manifest shard                                                   | Detail doc                                                                                             |
| ----------- | --------------------------------------------------------------- | -------------------------------------- | ------------------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| cefi        | instrument-catalog                                              | 15-min wall-clock                      | CCXT (replaces Tardis T+1 historical) | `(asset_group=cefi, venue, instrument_type, day)`                | [`asset-class-ownership.md`](asset-class-ownership.md)                                                 |
| tradfi      | instrument-catalog                                              | 15-min wall-clock                      | Polygon / Yahoo (Databento alt)       | `(asset_group=tradfi, venue, instrument_type, root, day)`        | [`asset-class-ownership.md`](asset-class-ownership.md)                                                 |
| prediction  | market-discovery                                                | 15-min wall-clock                      | Polymarket / Kalshi REST              | `(asset_group=prediction, venue, canonical_question_group, day)` | [`../02-data/prediction-schema-paths.md`](../02-data/prediction-schema-paths.md)                       |
| sports      | fixtures                                                        | daily fixture re-poll                  | api_football                          | `(asset_group=sports, source=af, league_id, day)`                | [`../02-data/sports-fixtures-lifecycle.md`](../02-data/sports-fixtures-lifecycle.md)                   |
| sports      | teams + mappings                                                | per-league season-roll trigger         | api_football, sfi, transfermarkt      | `(asset_group=sports, source, league_id, season)`                | [`../02-data/sports-data-source-coverage-matrix.md`](../02-data/sports-data-source-coverage-matrix.md) |
| sports      | player-values                                                   | annual transfer-window trigger         | transfermarkt                         | `(asset_group=sports, source=tm, league_id, season)`             | [`../02-data/sports-data-source-coverage-matrix.md`](../02-data/sports-data-source-coverage-matrix.md) |
| sports      | injuries (event-time)                                           | rolling sub-hourly while season active | api_football                          | `(asset_group=sports, source=af, league_id, day)`                | [`../02-data/sports-fixtures-lifecycle.md`](../02-data/sports-fixtures-lifecycle.md)                   |
| sports      | weather cascade                                                 | trigger-driven leading up to kickoff   | open-meteo                            | `(asset_group=sports, source=openmeteo, league_id, fixture_id)`  | [`../02-data/sports-fixtures-lifecycle.md`](../02-data/sports-fixtures-lifecycle.md)                   |
| sports      | lineups                                                         | `kickoff − 60min` trigger              | api_football                          | `(asset_group=sports, source=af, league_id, fixture_id)`         | [`../02-data/sports-fixtures-lifecycle.md`](../02-data/sports-fixtures-lifecycle.md)                   |
| sports      | post-match (results, fixture_stats, sfi_progressive, understat) | `match_end_time` trigger               | api_football, sfi, understat          | `(asset_group=sports, source, league_id, fixture_id)`            | [`../02-data/sports-fixtures-lifecycle.md`](../02-data/sports-fixtures-lifecycle.md)                   |

## Cross-references

- Symmetry: [`batch-live-architecture.md`](batch-live-architecture.md) § 9 Instruments-live exception (single SSOT)
- Pre-flight chain (live=batch): [`instruments-preflight-chain.md`](instruments-preflight-chain.md)
- Cloud Scheduler topology + per-trigger cron expressions:
  [`../05-infrastructure/runtime-tiers-and-deployment.md`](../05-infrastructure/runtime-tiers-and-deployment.md) §
  "Instruments-live Cloud Scheduler topology"
- Cluster topology (where these run):
  [`../05-infrastructure/deployment-clusters-live-vs-batch.md`](../05-infrastructure/deployment-clusters-live-vs-batch.md)
- Live monitoring + event cadence:
  [`../05-infrastructure/live-deployment-monitoring.md`](../05-infrastructure/live-deployment-monitoring.md)
- Alerting taxonomy (typed failure modes): [`alerting-batch-live.md`](alerting-batch-live.md) § "Instruments-live
  failure rules"
- T+1 audit discrepancy runbook:
  [`../15-runbooks/instruments-live/t1-audit-discrepancy.md`](../15-runbooks/instruments-live/t1-audit-discrepancy.md)
- CLI surface: [`../06-coding-standards/cli-convention.md`](../06-coding-standards/cli-convention.md) (`--operation` /
  `--mode batch|live` / `--asset-group` / `--trigger <name>`)

## Code surface

- `instruments-service` CLI: `--mode live --trigger <name>` selects entity-type subset + source adapter; same
  `_check_dependencies` + `_should_skip_date` + `record_captured/record_empty/record_failed` semantics as batch.
- `unified_api_contracts/canonical/crosscutting/instruments_preflight_dag.py` — preflight DAG SSOT consumed by every
  trigger before fetching.
- `unified_api_contracts/internal/events.py` — `INSTRUMENTS_LIVE_*` lifecycle events.
- `unified_api_contracts.canonical.crosscutting.transfer_windows` + sports trigger calendar — UAC SSOT for sports
  triggers.
