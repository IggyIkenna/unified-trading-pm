---
doc_type: issue
title: >-
  oracle_prices capture (CHAINLINK/PYTH/AAVE, all 3 venues) has produced zero new manifest rows since 2026-07-22 despite
  an actively-updating DeFi manifest elsewhere — the high-freq forward-poll cadence appears stalled
summary: >-
  Discovered while closing out lst_exchange_rate_data_availability_2026_07_21.md's Aave-oracle-adapter todo: the
  manifest confirms AaveOracle.getAssetPrice() DOES produce real captured rows (5,568 rows, 2023-01-27→2026-07-22,
  written via 3 backfill waves 07-23/07-27/07-28), so that todo is genuinely resolved. But ALL THREE oracle_prices
  venues (CHAINLINK, PYTH, AAVE) top out at the exact same max date 2026-07-22 — an 8-day silence — while the rest of
  the DeFi manifest keeps writing daily (max written_at across the whole index is 2026-07-30T10:44). This is a
  fleet-wide stall of one data_type across every venue, not an AAVE-specific gap, and needs investigation into whether
  the `collect-oracle-prices` forward-poll VM is actually running.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [defi, oracle-prices, capture-gap, forward-poll, manifest, data-availability, aave, chainlink, pyth]
related:
  [
    /plans/archive/issues/lst_exchange_rate_data_availability_2026_07_21.md,
    /plans/active/lst_rate_honest_coverage_2026_07_21.md,
    /codex/02-data/lst-exchange-rate-surfaces.md,
  ]
created: 2026-07-30
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
source:
  [
    "manifest-verification sub-agent run while closing out lst_exchange_rate_data_availability_2026_07_21.md's
    Aave-oracle todo, slot-11, 2026-07-30",
  ]
resolved_by:
locked_by:
locked_since:
---

# oracle_prices capture stalled since 2026-07-22 (all 3 venues)

## What I found

Read from the sanctioned single `_index/availability_index.parquet` DeFi manifest index
(`gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet`) via DuckDB — no new
whole-corpus GCS walk, per single-walk discipline:

- **AAVE (getAssetPrice) is genuinely captured, not fake**: venue=AAVE, data_type=oracle_prices, source=aave shows 5,568
  rows with `capture_status='captured'` (4,856 with `instrument_count=1`, 712 with `instrument_count=0`, spanning
  2023-01-27→2026-07-22. `written_at` clusters into three backfill waves: 2026-07-23 (covers 2023-01-27→2023-09-30),
  2026-07-27 (2023-10-01→2026-06-05), 2026-07-28 (2026-06-06→2026-07-22).
- **No row exists for ANY of venue=CHAINLINK, PYTH, or AAVE, data_type=oracle_prices, for any date 2026-07-23 through
  2026-07-30 (today)** — an 8-day silence across the entire data_type, not just the newly-wired AAVE branch.
- The manifest itself is NOT stale — the max `written_at` across the whole DeFi index is 2026-07-30T10:44Z, so other
  shards/data_types are actively writing today. This rules out "the index snapshot is old" as the explanation.
- `deployment-service/scripts/vm/launch-defi-forward-poll.sh` documents `collect-oracle-prices` as a "PRICE-SENSITIVE,
  high-freq" operation meant for a recurring/frequent cadence (line ~21, ~75-116) — it's an on-demand VM launcher, one
  of 4 whitelisted live operations. No CI workflow, cron, or scheduler reference to this launcher was found anywhere in
  the workspace (`grep -rl "launch-defi-forward-poll" --include="*.yml" --include="*.yaml" .` returned zero hits) —
  suggesting `collect-oracle-prices` only runs when someone manually launches (or relaunches) the forward-poll VM, and
  nobody has done so since the 07-27/07-28 backfill waves completed.
- The MTDS AAVE collection branch (`collect_aave_branch` in `_aave_oracle_collection.py`) cleanly self-skips on
  `run_tag=="live"` (AAVE is batch-only — no `live_aave` `PipelineMode` member per `SOURCE_MODE_CAPABILITY["aave"]`), so
  even if the forward-poll VM IS running live, the AAVE branch specifically would never produce new rows via that path
  regardless — it needs a batch/backfill re-run, not a live-mode fix. But CHAINLINK/PYTH have no such live-mode
  restriction and are ALSO silent since 07-22, which points to the forward-poll VM itself not running (or running and
  failing) rather than a per-venue code issue.

## Why it matters

- `oracle_prices` is the on-chain price the AAVE lending market marks LST collateral at (drives LTV/liquidation —
  Surface #3 in `/codex/02-data/lst-exchange-rate-surfaces.md`). An 8-day-and-growing staleness means any
  recursive-staking-collateral valuation built on this feed is working off week-old prices, silently, unless the reader
  itself surfaces staleness.
- This affects Chainlink and Pyth too, not just the newly-wired AAVE branch — so this is NOT resolved by, or a
  consequence of, the Aave-oracle-adapter wiring work; it is a pre-existing (or newly-introduced) operational gap in how
  `collect-oracle-prices` is scheduled/kept running.

## Recommended decision

Investigate whether a `collect-oracle-prices` forward-poll VM is currently running (heartbeat blob age, `run.log` tail)
for any cloud/zone in the fleet. If none is running, relaunch it
(`launch-defi-forward-poll.sh --operation collect-oracle-prices`) and consider whether this operation needs a standing
cron/scheduler (unlike a one-off backfill, a "high-freq PRICE-SENSITIVE" op reads as something that should self-sustain,
not depend on a human remembering to relaunch it after every VM cycle). If a VM IS running but not producing manifest
rows, that's a separate write-path bug to diagnose via its logs.

## Todos

- [ ] [DATA] P1. **Determine why `collect-oracle-prices` (CHAINLINK/PYTH/AAVE) has produced zero manifest rows since
      2026-07-22** — check whether a `launch-defi-forward-poll.sh --operation collect-oracle-prices` VM is currently
      running (heartbeat blob + `run.log` tail per the VM-delete guardrail's staleness checklist); if none is running,
      relaunch it; if one is running but silent, diagnose the write path. (repo: deployment-service,
      market-tick-data-service)
- [ ] [INFRA] P2. **Decide whether `collect-oracle-prices` needs a standing cron/scheduler** instead of relying on a
      manually-relaunched VM — no CI/cron reference to `launch-defi-forward-poll.sh` exists anywhere in the workspace
      today, so a "high-freq PRICE-SENSITIVE" op currently has no self-sustaining trigger. (repo: deployment-service)
- [ ] [DOCS] P3. **Fix the stale referrer in `plans/active/lst_rate_honest_coverage_2026_07_21.md`** — it still points
      at `/plans/active/issues/lst_exchange_rate_data_availability_2026_07_21.md` (now archived to
      `/plans/archive/issues/...`), but that file is already at 1001 lines (over the 1000-line hard cap with no baseline
      exemption for a touched file — `check_line_caps.sh`), so the referrer fix could not be committed alongside the
      archival. Trim the plan below the cap first, then fix the two stale path references (frontmatter `related:` + the
      body "Audit:" line). (repo: unified-trading-pm)

## Progress Log

- **slot-11 2026-07-30**: Filed while closing `lst_exchange_rate_data_availability_2026_07_21.md`'s Aave-oracle-wiring
  todo. Confirmed via manifest read (not a new GCS walk) that the AAVE branch itself works (5,568 real captured rows),
  but the whole `oracle_prices` data_type across all 3 venues has been silent for 8 days.
