---
doc_type: codex-ssot
title: Instruments preflight chain (live = batch)
summary:
  UAC instruments_preflight_dag SSOT — per-(asset_group, downstream-entity) required upstream entity-types +
  max-staleness, enforced identically in batch and live via validate_preflight_for_trigger before any source fetch.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: [instruments, sports, cefi, pipeline-mode, data-correctness]
related:
  [
    /codex/04-architecture/instruments-live-architecture.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    /codex/04-architecture/alerting-batch-live.md,
  ]
created: 2026-05-08
authoritative_for: [instruments preflight-DAG chain (live=batch)]
referenced_by:
  [
    /codex/03-observability/lifecycle-events.md,
    /codex/04-architecture/batch-live-architecture.md,
    /codex/04-architecture/instruments-live-architecture.md,
    /codex/15-runbooks/instruments-live/t1-audit-discrepancy.md,
  ]
owner:
last_reviewed: 2026-08-20
code_refs:
---

# Instruments preflight chain (live = batch)

## Why

Every downstream service in the data pipeline (MTDS / MDPS / features-\* / strategy / execution / position-balance /
risk) depends on a chain of upstream entities being current. Batch enforces this implicitly via per-service
`_check_dependencies` / `check_shard_freshness` (CLAUDE.md "Honest absence vs fake placeholders" § 2). Live must enforce
the same rules with the same code path; otherwise live silently produces zero or stale rows when an upstream trigger
missed-fire or a source went degraded.

## SSOT — UAC `instruments_preflight_dag`

The dependency graph lives in `unified_api_contracts/canonical/crosscutting/instruments_preflight_dag.py`.
Per-(asset_group, downstream-entity-type), it declares the required upstream entity-types + max-staleness-tolerance.

| asset_group | downstream entity                                                                                             | required upstream                                    | max staleness                                                                                                            |
| ----------- | ------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| cefi        | 15-min OHLCV                                                                                                  | instrument-catalog                                   | 24 h                                                                                                                     |
| tradfi      | 15-min OHLCV                                                                                                  | instrument-catalog                                   | 24 h                                                                                                                     |
| prediction  | market-discovery                                                                                              | canonical_question_group SSOT (UAC-static)           | n/a (static)                                                                                                             |
| sports      | lineups                                                                                                       | fixtures-for-the-fixture-day                         | `kickoff − 24 h`                                                                                                         |
| sports      | weather cascade                                                                                               | fixtures-for-the-fixture-day                         | `kickoff − 24 h`                                                                                                         |
| sports      | injuries (event-time)                                                                                         | teams (current-season) AND fixtures (rolling window) | teams: season; fixtures: 24 h                                                                                            |
| sports      | post-match (any)                                                                                              | fixtures + lineups (for the fixture)                 | per-fixture                                                                                                              |
| sports      | mappings (sfi/tm)                                                                                             | teams (current-season)                               | season                                                                                                                   |
| defi        | DeFi collect handlers (pools/markets/LST/lending/liquidations/bridges/transfers/aggregator/flash-loan/solana) | instrument-catalog (IS DeFi catalogue)               | mode-aware: live 24h (manifest-row age via `DEFI_COLLECT_DAILY`), batch = per-`on_date` coverage snapshot (no age check) |

DeFi's gate is `assert_defi_catalog_fresh` (`market_tick_data_service/cli/handlers/_defi_catalog_freshness.py`), a
mode-aware wrapper around the same `run_preflight`/`instruments_preflight` mechanism — **not** a distinct DAG. `live`
mode reuses the standard manifest-row-within-24h check (`run_preflight(DEFI_COLLECT_DAILY)`); `batch` mode instead
asserts the IS catalogue has a per-date availability snapshot covering the historical `on_date` (the 24h-age check is
structurally wrong for a backfill of a past date — see the function's own docstring for the 2026-06-24 fix history).
Wired at the `process()`/per-shard chokepoint in every DeFi collect handler (all handlers importing it, including the 8
named in this doc's own dispatch batch — `lending_indices_handler`, `liquidations_handler`,
`liquidation_events_handler`, `bridge_events_handler`, `token_transfers_handler`, `aggregator_route_handler`,
`flash_loan_events_handler`, `solana_defi_handler` — were already wired as of 2026-06-05/06-21, predating this row's
addition); every FAILED check routes honest absence (`record_failed`/`record_empty`) rather than raising inside a
per-shard loop.

## Helpers

```python
get_preflight_requirements(asset_group, downstream_entity) -> list[PreflightRequirement]
validate_preflight_for_trigger(trigger_name, on_date, manifest_reader) -> PreflightResult
```

`PreflightResult` is `OK` or `FAILED(missing: list[MissingDependency])`. Every live trigger calls
`validate_preflight_for_trigger` before fetching from any source. On `FAILED`, the trigger:

1. Emits `INSTRUMENTS_LIVE_PREFLIGHT_FAILED` with `{asset_group, trigger_name, missing_dependencies, correlation_id}`.
2. Skips the fetch (no parquet write, no `record_captured`).
3. Lets the next scheduled fire retry — by then either the upstream caught up (preflight passes; trigger fires normally)
   or the alerting rule has paged on-call to fix the upstream.

The independent upstream-staleness monitor (`INSTRUMENTS_LIVE_UPSTREAM_STALE`) emits early-warning alerts when an
upstream is older than threshold even before any downstream trigger has fired.

## Live = batch invariant

The same `validate_preflight_for_trigger` helper is called by both modes. Batch passes the historical date; live passes
"now". Same code path, same failure modes, same manifest writes.

## Failure modes

`PreflightResult.FAILED` always includes per-missing-dependency
`{entity_type, expected_max_age, actual_age, last_seen_at}` so the alert surfaces the specific upstream blocking the
trigger.

## Cross-references

- Architecture entry-point:
  [`instruments-live-architecture.md`](/codex/04-architecture/instruments-live-architecture.md)
- Honest-absence rules:
  [`/codex/02-data/honest-absence-downstream-handling.md`](/codex/02-data/honest-absence-downstream-handling.md)
- Alerting taxonomy: [`alerting-batch-live.md`](/codex/04-architecture/alerting-batch-live.md) § "Instruments-live
  failure rules"
- Lifecycle events: `unified_api_contracts/internal/events.py` (`INSTRUMENTS_LIVE_PREFLIGHT_FAILED` /
  `INSTRUMENTS_LIVE_UPSTREAM_STALE`)
