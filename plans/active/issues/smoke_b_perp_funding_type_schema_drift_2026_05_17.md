---
title: "Smoke B FAILED — perp_funding Int64→Datetime schema drift + utilization subprocess stall"
created: 2026-05-17
author: ikenna-slot1-main
source:
  - "features-onchain-defi-20260517-171908 DEPLOYMENT_FAILED (exit_code=124)"
  - "gs://deployment-scripts-central-element-323112/vm-logs/features-onchain-defi-20260517-171908/run.log"
locked_by: live-defi-rollout
---

# Smoke B FAILED — perp_funding schema drift + utilization stall

## What I found

VM `features-onchain-defi-20260517-171908` (DeFi features, 2026-04-08→2026-04-12) exited with `DEPLOYMENT_FAILED` at
17:23 UTC (stall watchdog killed after 3601s log silence, exit_code=124).

**Bug 1: perp_funding timestamp schema drift**

```
ERROR ❌ Error in load_derivative_ticker: type Int64 is incompatible with expected type Datetime('ns', 'UTC')
```

Occurs for `perp_funding` on dates 2026-04-10, 2026-04-11, 2026-04-12. The MTDS parquet files for those dates store the
timestamp column as `Int64` (epoch nanoseconds) rather than `Datetime('ns', 'UTC')`. The features-onchain reader
(`load_derivative_ticker`) expects `Datetime`. The per-shard error isolation catches it (logged as ERROR, no raise), so
those dates are silently skipped rather than blocking the run.

**Bug 2: utilization subprocess stall**

After:

```
INFO Resolved 50 MTDS parquet files for rate_indices ... day=2026-04-08 ...
INFO Loaded 134426 rate rows from MTDS
[vm-exec] STALL: log has not grown in 3601s (threshold=3600s) — killing CMD_PID=6771
```

The features-onchain subprocess for `utilization` on 2026-04-08 hung indefinitely after loading rate_indices data. Stack
trace showed `do_wait` in kernel — waiting for a child process that never exited. No OOM, no Python exception.

## Why it matters

- **DeFi features (onchain) are not computed** for the 2026-04-08→2026-04-12 window → paper backtest blocked
- The perp_funding type drift means `onchain_perps` feature group is silently empty for affected dates (no WARNING)
- The utilization stall is a complete blocker — any date where `utilization` hangs will stall the VM

## Recommended decision

**Bug 1 (perp_funding schema drift)** — fix in features-onchain `load_derivative_ticker`:

- Cast Int64 → Datetime when loading. `polars`: `.cast(pl.Datetime("ns", "UTC"))` after `.with_columns`.
- OR fix in MTDS writer to always emit `Datetime` (schema-breaking change, requires UTL/UAC coordination).
- **Immediate fix**: add cast in reader (non-breaking). Owner: slot-6 (features-onchain).

**Bug 2 (utilization stall)** — needs investigation:

- Likely: `utilization` feature computation calls a subprocess that hangs (GCP API call? rate_indices aggregation?).
- Short-term: add `timeout=3600` to the inner subprocess call so the stall-watchdog isn't the only kill mechanism.
- Investigation: check `features-onchain-service/features_onchain_service/` for `subprocess.run` / `Popen` calls in the
  utilization calculation path. Owner: slot-6 (features-onchain).

**Re-run Smoke B** after both fixes land (or with `--skip-feature perp_funding` if Bug 1 fix takes >1 day).

## Status

- [x] ✅ [AGENT] P0. Bug 1 fix — perp_funding timestamp cast in `load_derivative_ticker` — slot-6 owns
      (features-onchain) — features-service@30e449d7 (per-shard cast Int64→Datetime before append; also covered by
      post-concat cast at 64682456 from parallel agent)
- [x] ✅ [AGENT] P0. Bug 2 investigation — utilization subprocess stall root cause + timeout guard — slot-6 owns —
      features-service@30e449d7 (root cause: synchronous PubSub log_event per-row on 134k rows; fix: cap
      emit_aave_utilization_events at _MAX_UTILIZATION_EVENTS=500; GCS async write fix at 64682456 from parallel agent)
- [ ] [AGENT] P0. Smoke B re-run (2026-04-08→2026-04-12) after Bug 1+2 fix — slot-1 main launches VM
- [ ] [AGENT] P1. Harsh-side paper backtest launch blocked on Smoke B passing — pending Smoke B re-run
