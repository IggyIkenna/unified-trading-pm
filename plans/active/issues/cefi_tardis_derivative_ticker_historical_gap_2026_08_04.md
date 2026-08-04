---
doc_type: issue
title: CEX-Tardis derivative_ticker historical gap (2026-05-22→2026-08-02) left by the forward-capture outage fix
summary: >-
  Split off perp_funding_data_semantics_and_cadence_2026_06_16.md's 2026-08-04 forward-capture-outage fix, which only
  resumes NEW captures — the ~2-month historical hole the outage itself created is a separate, larger backfill.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [derivative_ticker, perp-funding, backfill, cron, data-correctness, tardis]
related:
  [
    /plans/active/issues/perp_funding_data_semantics_and_cadence_2026_06_16.md,
    /plans/active/issues/cefi_onchain_perp_forward_capture_outage_2026_08_03.md,
  ]
created: 2026-08-04
priority: P1
parent_epic: mtds_mdps_master
assigned_vm: planning
execution_scope: orchestrator-agent
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: ["perp_funding_data_semantics_and_cadence-014, slot 6, 2026-08-04"]
drift_direction: advance-code
context_scope:
  [
    /plans/active/issues/perp_funding_data_semantics_and_cadence_2026_06_16.md,
    deployment-service/scripts/vm/launch-cefi-forward-poll.sh,
    unified-api-contracts/unified_api_contracts/registry/perp_funding_cadence.py,
  ]
---

# CEX-Tardis derivative_ticker historical gap (2026-08-04)

## What I found

Fixing `perp_funding_data_semantics_and_cadence_2026_06_16.md`'s CEX-Tardis forward-capture-outage todo (a singleton-
filter collision that made the `cefi-fwd-daily-cron-` host refuse every one of its own daily fires — see that doc's
2026-08-04 resolution note) only resumes captures going forward from 2026-08-03. It does NOT backfill the gap the outage
itself left: `derivative_ticker` has been dark since 2026-05-22 (`BINANCE-FUTURES`/`OKX-SWAP`/`KRAKEN-FUTURES`/
`BITGET-FUTURES`) or 2026-05-01 (`BYBIT`/`DERIBIT`) — roughly 70-90 days per venue, ~2 months minimum. This directly
underlies `carry_staked_basis` funding-carry ranking (P0 input) for the affected window.

## Why it matters

Same P0 input as the parent doc: a multi-month hole in `derivative_ticker` for 6 of the doc's 8 census venues means any
funding-carry analysis or backtest touching 2026-05-22→2026-08-02 is working off honest-absence gaps, not real data.

## Recommended decision / Todos

- [ ] [DATA] P1. Backfill `derivative_ticker` (+ whatever other data_types share the same forward-poll pass) for
      `BINANCE-FUTURES`/`BYBIT`/`OKX-SWAP`/`OKX-FUTURES`/`KRAKEN-FUTURES`/`BITGET-FUTURES`/`BITFINEX-FUTURES`/ `DERIBIT`
      across each venue's own gap-start (2026-05-22 or 2026-05-01, per the parent doc's census) through 2026-08-02
      (2026-08-03 onward is already covered by the resumed cron). Use the already-fixed, already-verified
      `launch-cefi-forward-poll.sh <start> <end>` date-range invocation (single VM, sequential per-day pass — the same
      launcher + fix verified live in the parent doc, not a new script). Respect the Tardis 1-concurrent-VM-both-clouds
      hard cap (`tardis-concurrency-guard.sh`) — this will queue behind/ahead of the daily cron fire, size the launch
      window accordingly. Verify via manifest row counts pre/post, not just VM exit code. **Repo:
      market-tick-data-service** (verification) **+ deployment-service** (launch).

## Progress Log

- **slot-9 2026-08-04**: `launch-cefi-forward-poll.sh 2026-05-01 2026-08-02` already launched
  (`cefi-fwd-20260804-021235`, e2-standard-8, `asia-northeast1-c`, started ~2026-08-04T02:12:40Z) — covers both
  per-venue gap-starts (2026-05-01 and 2026-05-22) through 2026-08-02 in one sequential single-VM pass, respecting the
  Tardis 1-concurrent-VM cap. Confirmed via `run.log` actively writing real `derivative_ticker` shards (e.g.
  `COINBASE-FUTURES:PERPETUAL:QQQ-USD@LIN.parquet`, 225340 rows) and a per-minute `PIPELINE_HEARTBEAT`/`RESOURCE_SAMPLE`
  cadence — healthy, not stalled. `vm-logs/<vm>/PROGRESS.json` write is monotonic-gated per-VM; day markers in `run.log`
  are the more reliable in-flight progress signal (sequential per-day pass starting at `VM_START_DATE`). This is a long
  single-VM sequential backfill (~94 days × 8+ venues) — monitoring via bounded background watchdogs (~10 min cadence,
  reading `run.log` day markers + VM status) rather than continuous polling, per the async-wait-discipline HARD RULE.
  Will verify via manifest row counts once the VM shuts down (`VM_SHUTDOWN_ON_COMPLETION=true`), then flip the todo.
