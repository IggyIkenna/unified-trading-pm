---
doc_type: plan
title: Per-Venue VENUE_HEARTBEAT_INTERVAL Empirical Calibration
summary:
status: complete
nature: record
asset_group: [cefi]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
created: "2026-05-19"
archived: 2026-05-23
estimate_class: research
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.8
migrated_from: mdps_streaming_and_backpressure_2026_05_07.md § item 547
parent_epic: cefi_master
assigned_vm: vm-cefi
priority: P2
---

# Per-Venue VENUE_HEARTBEAT_INTERVAL Empirical Calibration

**MIGRATED FROM:** `mdps_streaming_and_backpressure_2026_05_07.md` § item 547 (per-venue heartbeat interval
calibration). Deferred from May-23 cutover because calibration requires 7-day live telemetry from MTDS running in
production — not implementable without real data.

**Pre-condition**: MTDS must be running live for ≥7 days with the `LiveConnectivityWatchdog` wired to adapters and
emitting `CONNECTIVITY_GAP_DETECTED` events.

## Objective

Populate `VENUE_HEARTBEAT_THRESHOLDS` in UAC `venue_thresholds.py` with empirically-derived per-(venue, data_type)
`timedelta` thresholds. Each threshold = 99th-percentile inter-message gap observed over 7 days of live WS streaming per
venue.

Current state: all values are empty (`{}`). `DEFAULT_HEARTBEAT_THRESHOLD_BY_CLASS` provides fallback defaults
(cefi_ws=5s, defi_ws=10s, tradfi_replay=30s) until this plan ships.

## Tasks

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **Collect inter-message gap telemetry**. Run MTDS live for ≥7 days with
      heartbeat logging enabled. Emit a `log_event("MTDS_HEARTBEAT_INTERVAL", details={venue, data_type, gap_seconds})`
      per received WS tick in the adapters (or derive from watchdog `last_heartbeat_ts` diffs). Collect into BigQuery or
      GCS log aggregates.

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **Compute 99th-percentile gap per (venue, data_type)**. Read the
      telemetry; compute P99 inter-message delta per (venue, data_type) over the 7-day window. Account for market-closed
      periods (daily schedule per venue) — use only market-hours windows.

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **Update UAC `venue_thresholds.py`**. Write the calibrated `timedelta`
      values into `VENUE_HEARTBEAT_THRESHOLDS: dict[tuple[str, str], timedelta]`. Each key is `(venue_key, data_type)`
      matching UAC canonical venue names.

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P1. **Smoke test**: deploy to staging MTDS; observe
      `CONNECTIVITY_GAP_DETECTED` events do not fire spuriously during normal market hours; confirm thresholds are not
      too tight.

- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P1. **Codex update**: extend
      `/codex/04-architecture/live-pipeline-architecture.md` with a "Heartbeat threshold calibration" subsection
      documenting the P99 methodology + the `VENUE_HEARTBEAT_THRESHOLDS` constant.

## Target venues (initial set — expand as adapters roll out)

| Venue             | Data type   | Initial class default | Target P99 threshold |
| ----------------- | ----------- | --------------------- | -------------------- |
| `BINANCE-FUTURES` | `trades`    | cefi_ws (5s)          | TBD                  |
| `BINANCE-FUTURES` | `ohlcv_1m`  | cefi_ws (5s)          | TBD                  |
| `BYBIT`           | `trades`    | cefi_ws (5s)          | TBD                  |
| `OKX`             | `trades`    | cefi_ws (5s)          | TBD                  |
| `UNISWAP_V3`      | `dex_swaps` | defi_ws (10s)         | TBD                  |

## Full Execution Criterion

Plan is operationally complete when:

1. `VENUE_HEARTBEAT_THRESHOLDS` in UAC has non-empty entries for all 7+ production venues.
2. A 7-day staging run shows <5 spurious `CONNECTIVITY_GAP_DETECTED` events per venue per day during market hours.
3. Codex updated.

## Temporary states + their canonical follow-up plans

None — this plan IS the canonical follow-up.

## Deferred work — migrated to:

All 5 items are **DEFERRED-OPERATOR-DECISION** pending ≥7 days of MTDS live telemetry. Migrated to `cefi_master` §
post-cutover calibration backlog:

- **Collect inter-message gap telemetry (P0, DEFERRED-OPERATOR-DECISION)**: Migrated to: cefi_master § post-cutover
  backlog. Gate: MTDS running live ≥7 days with `LiveConnectivityWatchdog` emitting events.
- **Compute 99th-percentile gap per (venue, data_type) (P0, DEFERRED-OPERATOR-DECISION)**: Migrated to: cefi_master §
  post-cutover backlog. Gate: telemetry collection above.
- **Update UAC `venue_thresholds.py` with calibrated timedeltas (P0, DEFERRED-OPERATOR-DECISION)**: Migrated to:
  cefi_master § post-cutover backlog. Gate: P99 computation above.
- **Staging smoke test — no spurious `CONNECTIVITY_GAP_DETECTED` (P1, DEFERRED-OPERATOR-DECISION)**: Migrated to:
  cefi_master § post-cutover backlog.
- **Codex update — `live-pipeline-architecture.md` heartbeat calibration subsection (P1, DEFERRED-OPERATOR-DECISION)**:
  Migrated to: cefi_master § post-cutover backlog.
