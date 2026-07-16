---
doc_type: issue
title:
  Drift backfill had NO per-date skip gate — every SPOT restart re-walked already-captured days (~1.2M Helius sigs/day)
summary:
  "`_backfill_drift_s3_date` (market-tick-data-service) had no per-date manifest-freshness skip check at all — unlike
  every sibling DeFi handler (dex_pools/gas_fee/perp_funding), which all wire ManifestFreshnessCache before expensive
  work. A SPOT-preempted restart therefore unconditionally re-walked its whole --start/--end range including
  already-captured days: confirmed live 2026-07-15, a VM recreated at 16:11Z began re-resolving 1,209,478 Helius
  signatures for 2025-01-09 — a day fully captured at 02:45Z the same morning (parquet verified present in GCS) —
  burning scarce Helius credits on data we already had. Compounding factor: ManifestFreshnessCache keeps its PREVIOUS
  membership set when the consolidated-manifest read fails (the known defi consolidator SIGKILL/staleness class), and
  that set is EMPTY on a just-launched VM, so even a gate would have failed OPEN. Operator ruling 2026-07-15: stop the
  VM, fix the gate to fail CLOSED to already-captured when the day's canonical parquet exists, then relaunch."
status: open
nature: record
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-trading-library]
scope: [engineer, admin]
tags: [defi, drift, backfill, manifest, freshness, skip-gate, spot-preemption, helius, credits, data-correctness]
related:
  [
    plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md,
    plans/active/issues/defi_consolidator_scheduler_sigkill_unresolved_2026_07_10.md,
    plans/active/issues/mtds_perp_funding_backfill_hang_2026_07_14.md,
  ]
created: 2026-07-15
assigned_vm: NA
source:
  ["operator observation 2026-07-15 (main-session status check)", "live VM log + GCS canonical-parquet verification"]
parent_epic: defi_master
priority: P1
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-16
---

# Drift backfill re-walked already-captured days on every restart (2026-07-15)

> Filed because the shipped code comments cite this doc as the record. Found during an operator status check, not by an
> alert — a silent-waste class: the VM looked perfectly healthy the whole time.

## What happened (verified, not inferred)

- `mtds-solana-drift-backfill` was SPOT-preempted and recreated **2026-07-15T16:11Z**; at 16:53Z it began
  `Drift Helius backfill: 1209478 sigs in window [2025-01-09, 2025-01-09] for SOL-PERP`.
- **2025-01-09 was already fully captured at 02:45Z the same morning**
  (`Solana DeFi collection for 2025-01-09: 1209478 total records`). Coordinator verified the canonical parquet exists
  for `day=2025-01-09`, `2025-01-10`, `2025-01-13` (1 DRIFT `perp_funding` object each, bounded GCS check).
- Cost: ~1.2M Helius signature resolutions **per already-captured day**, against a quota the operator had just topped up
  (2M + 10M at reset) precisely to finish the _remaining_ gap. Re-doing ≥6 captured days (2025-01-09→14) before reaching
  new work.
- Operator stopped it (protective, reversible) and ruled: fix the gate to fail CLOSED, then relaunch.

## Root cause (deeper than the initial hypothesis)

The initial coordinator hypothesis was "the gate fails open under consolidator staleness". **The truth is worse**:
`_backfill_drift_s3_date` had **no per-date skip check at all** — it is the only DeFi backfill handler missing one
(`dex_pools_handler.py`, `gas_fee_handler.py`, `perp_funding_handler.py` all wire `ManifestFreshnessCache` before doing
expensive work). So restarts re-walked everything unconditionally.

The staleness hypothesis is still a REAL compounding factor and is why a naive gate would not have been enough:
`ManifestFreshnessCache` keeps its **previous membership set** when the consolidated-manifest read fails (the
`defi_consolidator_scheduler_sigkill_unresolved_2026_07_10` class — that consolidator genuinely is intermittently
dead/stale, and `ManifestConsolidatorStaleError` fires on essentially every date per
`mtds_perp_funding_backfill_hang_2026_07_14`). On a just-launched VM that previous set is **empty** → every date looks
unattempted → fail OPEN → re-fetch. Hence the two-part fix.

## Fix

- **UTL** `unified-trading-library@dfcb1181` — `ManifestFreshnessCache` now surfaces `last_refresh_failed`, so callers
  can distinguish "manifest says not captured" (trustworthy) from "manifest read failed" (not trustworthy). (Adjacent,
  same class, landed same day: `@2d1f77a8` — per-asset_group consolidator in-flight horizon, defi 4200s, fixing the
  1800s boundary that missed defi's ~31-32min merges.)
- **MTDS** `market_tick_data_service/cli/handlers/solana_defi_drift.py` — adds the missing gate at the TOP of
  `_backfill_drift_s3_date` (ahead of the S3-vs-Helius dispatch, so both sub-paths share one decision): normal path =
  `ManifestFreshnessCache.is_now_skip_worthy`; when `last_refresh_failed`, fall back to a **bounded one-day**
  canonical-parquet existence probe → exists ⇒ **fail-closed SKIP** with a loud `MANIFEST_FRESHNESS_STALE_FALLBACK`
  warning (never silent). Probe failure ⇒ `False` ⇒ re-attempt (never silently assume capture). `attempted_failed` days
  remain never-skip-worthy (unchanged, correct).

## Todos

- [ ] [CODE] P1. Ship the MTDS half (gate + fail-closed fallback + regression tests). Repo: market-tick-data-service.
- [ ] [VERIFY] P1. Relaunch the Helius/S3 Drift backfill on the fixed code and prove via log that it SKIPS
      2025-01-09..2025-01-14 and starts at the first genuinely-uncaptured date (T+15min measured check, not liveness).
      NOTE 2026-07-16: an AO slot launched `backfill_drift_v2_historical` (17 markets, 2022-11-04→2026-07-16,
      funding+trades) which uses Drift's FREE public data API (`data.api.drift.trade`, zero Helius lines in log) — this
      may supersede the Helius sig-walk path entirely for historical funding. Decide which path owns history before
      relaunching the Helius one; do not run both over the same range.
- [ ] [SCRIPT] P2. **Class check — every backfill launcher is SPOT** (hard rule: backfills default to SPOT), so any
      handler lacking a skip gate re-does captured work on every preemption. Audit the other backfill entrypoints
      (`scripts/backfill_*`, the per-data_type handlers) for the same missing-gate pattern and for fail-open-on-stale;
      fix or file. Repo: market-tick-data-service.

## Progress log

- 2026-07-15/16: Found during an operator status check. VM stopped protectively; UTL half shipped (`dfcb1181`); MTDS
  half authored (gate + 245 lines of regression tests) but its shipping agent hit the weekly API limit mid-gate — picked
  up by the coordinator. Doc created retroactively because the shipped code comments already cite it.
