---
scope: [engineer, admin]
---

<!-- POST_PLAN_BANNER_2026_05_06 -->

> **POST-PLAN REALITY (2026-05-06)** — read [`../POST_PLAN_REALITY_2026_05_06.md`](../POST_PLAN_REALITY_2026_05_06.md)
> BEFORE making code or doc changes informed by this doc. This doc is partially stale: may describe service
> architecture, shard granularity, or failure isolation that's evolving with writegate Phase 2 + predictions Phase 2
> (per-fixture sports sharding, lifecycle timing for predictions, MDPS empty-output A/B/C decision tree, cluster
> validation as 4th write-gate pillar). The post-plan-reality doc lists the 10 cross-cutting principles codified in
> workspace `CLAUDE.md` (live=batch, no double SSOT, three-category empty-output decision A/B/C, cluster validation
> mandatory at record_captured, per-row write-time `available_at`, prediction lifecycle timing, temporary state must
> have named successor, per-VM shard isolation, etc.) plus the active plans where the canonical post-plan reality is
> being implemented. If this doc and the active plans disagree, the plans win. If you find a contradiction the plans
> don't address, flag to user — don't decide unilaterally.

# Shard-Level Failure Isolation (SSOT)

## Rule

**A failed shard MUST NOT kill other shards in the same batch.**

Shards are the isolation boundary. When processing fails for one shard, the service:

1. Logs the error with full details (venue, error message, shard ID, correlation ID) to the event stream
2. Emits a `VENUE_PROCESSING_FAILED` or `DATE_PROCESSING_FAILED` event with error details
3. Continues processing remaining shards
4. Reports partial success at the end (not total failure)

A **partially complete shard** should be killed — do not store partial data for a shard that errored mid-processing.

## Sharding Dimensions

For the complete per-service shard dimension matrix (all 8 pipeline layers, all categories), see
**`codex/02-data/availability-manifest-and-data-status.md`** — the SSOT for availability manifest schema, shard
dimensions, data status page hierarchy, and availability % calculation.

Quick reference (not exhaustive — see SSOT for full matrix):

| Service                        | Shard Dimensions                                                | Example                                          |
| ------------------------------ | --------------------------------------------------------------- | ------------------------------------------------ |
| instruments-service            | category x venue x [chain] x date                               | DEFI x AAVE_V3 x ETHEREUM x 2026-01-05           |
| market-tick-data-service       | category x venue x [chain] x instrument_type x data_type x date | CEFI x BINANCE-SPOT x spot x trades x 2026-01-05 |
| market-data-processing-service | category x venue x [chain] x instrument_type x date x timeframe | CEFI x BINANCE-SPOT x spot x 2026-01-05 x 1m     |
| feature services               | feature_group x [timeframe] x [chain] x [league_id] x date      | momentum x 1h x 2026-01-05                       |
| ML services                    | model_family x [training_period] x date                         | pregame_xg x 2024 x 2026-01-05                   |
| strategy/execution/PnL         | strategy_id x [venue] x [instruction_type] x date               | strat_001 x BETFAIR x TRADE x 2026-01-05         |
| risk-and-exposure              | client_id x date                                                | client_A x 2026-01-05                            |

## Error Handling Pattern

```python
for venue in venues_to_process:
    try:
        result = await process_venue(venue, date)
        all_results[venue] = result
    except (ValueError, KeyError, TypeError, RuntimeError) as e:
        # Per-shard error isolation: log and continue
        logger.error("Shard %s/%s failed: %s — continuing", venue, date, e)
        log_event("VENUE_PROCESSING_FAILED", details={
            "venue": venue,
            "date": date.isoformat(),
            "error": str(e),
            "error_type": type(e).__name__,
            "correlation_id": correlation_id,
        })
        # Do NOT raise — continue with remaining shards
```

## Anti-Patterns (DO NOT)

- `raise RuntimeError(...)` inside a per-venue loop — kills all remaining venues
- Swallowing errors silently (`except: pass`) — errors must be logged and evented
- Storing partial shard data — if a shard fails mid-processing, discard its partial output

## Event Stream Requirements

Failed shard events MUST include:

- `venue`: Which venue/shard failed
- `error`: Human-readable error message
- `error_type`: Exception class name
- `correlation_id`: For tracing
- `category`: Market category (cefi, tradfi, defi, sports)

This enables diagnosis from the event stream (GCS in batch, PubSub in live) without re-running the service.
