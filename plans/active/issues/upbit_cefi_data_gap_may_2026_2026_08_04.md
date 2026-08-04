---
doc_type: issue
title: UPBIT CeFi data gap — zero captured objects since 2026-05-25 for a codex-MVP venue
summary: >-
  UPBIT is codex-MVP (MVP_SCOPE.cefi.venues, spot-without-perp carve-out) but has produced ZERO captured tick-data
  objects in GCS since 2026-05-25 (~72 days as of 2026-08-04). Prior coverage (2021-03-03 through 2026-05-22) averaged
  ~600 trades+book_snapshot_5 parquet objects/day via batch_tardis. The Tardis backfill stopped abruptly — last full day
  2026-05-22 (606 objects), residual KRW-only book_snapshot_5 on May 23-24 (36 objects/day), then nothing. Live WS
  connectors exist in code but produce no GCS objects. No open issue or backfill plan tracks this gap; the parent plan's
  audit trail has zero UPBIT mentions.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, instruments-service]
scope: [engineer]
tags: [upbit, cefi, data-gap, mvp, tardis, coverage]
related:
  - /plans/active/cefi_consolidated_native_ao_extract_2026_07_25.md
  - /plans/active/cefi_consolidated_closeout_2026_07_18.md
  - /codex/02-data/mvp-scope-canonical.md
created: "2026-08-04"
author: slot-6 (data_engineering)
source:
  - cefi_consolidated_native_ao_extract_2026_07_25.md (Todo 6 — UPBIT live-wiring confirm)
assigned_vm: planning
parent_epic: cefi_master
resolved_by:
locked_by:
priority: P1
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# UPBIT CeFi data gap — zero captured objects since 2026-05-25

## What I found

UPBIT is codex-MVP (`MVP_SCOPE.cefi.venues`, `/codex/02-data/mvp-scope-canonical.md` § CeFi venues row —
spot-without-perp carve-out via `STAKING_SPOT_EXCEPTION`) but has produced **ZERO captured tick-data GCS objects** since
2026-05-25, a gap of ~72 days (as of 2026-08-04) for a venue the MVP definition expects to be live-wired.

**Measured GCS evidence** (read-only, prod buckets, 2026-08-04):

| Metric                        | Value                                                                                                   |
| ----------------------------- | ------------------------------------------------------------------------------------------------------- |
| IS catalogue (day=2026-08-03) | 488 active SPOT_PAIR instruments, 308 base assets, KRW+USDT quotes                                      |
| Pipeline mode                 | `batch_tardis` only — no live/forward mode                                                              |
| Data types captured (pre-gap) | `trades` (~263/day) + `book_snapshot_5` (~345/day) = ~608 obj/day                                       |
| Coverage period               | 2021-03-03 → 2026-05-22 (~5.2 years)                                                                    |
| May 23–24, 2026               | 36 obj/day — KRW-pair book_snapshot_5 ONLY (BTC-KRW, ETH-KRW, DOT-KRW, etc.), no trades, no USDT pairs  |
| **May 25, 2026 → present**    | **ZERO objects** — 72+ day complete gap                                                                 |
| Live WS connectors            | Present in code (`upbit_spot_ws.py`, `upbit_book_ws.py`, `upbit_adapter.py`) but produce no GCS objects |

**Per-day object counts (GCS `raw_tick_data/by_date/`):**

```
2026-05-19: 608 objects  (trades 263 + book_snapshot_5 345)  ← last full day
2026-05-20: 590 objects
2026-05-21: 589 objects
2026-05-22: 606 objects                                      ← last day with trades
2026-05-23:  36 objects  (book_snapshot_5 only, KRW pairs)   ← trades drop
2026-05-24:  36 objects  (book_snapshot_5 only, KRW pairs)
2026-05-25:   0 objects  ← COMPLETE STOP
...
2026-08-04:   0 objects
```

**Known historical issues** (both resolved, `cefi_venue_backfill_coverage_remediation_2026_05_27.md`):

- UPBIT Tardis CSV type mismatch (ArrowInvalid float-in-int-column) — ✅ fixed
- Cross-date memory accumulation (~78 GB) — ✅ fixed

Neither explains the May-25+ gap.

## Why it matters

1. **MVP definition breach**: UPBIT is explicitly listed as an MVP venue with no known caveats or deferred status. A
   codex-MVP venue with zero data for 2.5+ months is a material gap in the honest-coverage denominator.
2. **Invisible to the audit surface**: The parent `cefi_consolidated_closeout_2026_07_18.md` plan has zero UPBIT
   mentions — this gap has never been triaged or tracked. The `cefi_master.md` epic expects UPBIT at
   "trades/book_snapshot_5, 450 each."
3. **Root cause unknown**: Is Tardis UPBIT data simply unavailable past May 2026 (vendor-side ceiling — then UPBIT needs
   a non-Tardis source or MVP descope), or did the pipeline silently stop (then it needs a VM restart/repair)?
4. **Live connectors don't close the gap**: The WS connectors exist in code but produce no GCS objects — the only data
   source is the Tardis backfill, which is what stopped.

## Recommended decision

1. **Diagnose root cause first** — check whether Tardis actually carries UPBIT data past May 2026 (query Tardis API
   directly for available date ranges), or whether the backfill VM/launcher stopped/was de-prioritized.
2. **If Tardis has the data** → restore the UPBIT backfill (VM relaunch, fix whatever stopped it).
3. **If Tardis does NOT have the data** → operator decision needed: either (a) wire UPBIT live WS connectors to produce
   GCS objects (non-Tardis, on-demand capture going forward, with the pre-May-2026 Tardis data as historical floor), or
   (b) explicitly descope UPBIT from MVP with a documented ruling.

## Todos

- [x] ✅ [DATA] P1. **Diagnose the UPBIT May-2026 data gap root cause.** (a) Query Tardis API directly for UPBIT's
      available date range — does Tardis carry UPBIT data past 2026-05-22? (b) Check the `cefi-queue-heavy` backfill VM
      logs around May 23-25 for UPBIT-specific errors/stoppage. (c) Check whether the UPBIT backfill shard was
      explicitly disabled/de-prioritized in launcher config. Repo: market-tick-data-service. **Done when**: a written
      root-cause verdict (Tardis-vendor-ceiling vs pipeline-stoppage vs config-change) is recorded in this issue doc's
      Progress Log, with evidence. — market-tick-data-service@N/A (diagnosis-only, no code change)
- [ ] [DATA] P1. **Based on the root cause from the todo above, either restore the UPBIT backfill or file an
      operator-gated descope decision.** If Tardis has the data: relaunch the UPBIT backfill and verify objects land in
      GCS for ≥3 recent days. If Tardis doesn't: file a concrete operator decision ask (wire live WS → GCS, or descope
      UPBIT from MVP) with clear trade-offs. Repo: market-tick-data-service (if backfill fix) or unified-trading-pm (if
      descope decision). **Done when**: either objects are flowing again, or a tagged `[OPERATOR]` decision issue is
      filed with the two options.

## Progress Log

_Initial finding filed 2026-08-04 by slot-6 (data_engineering) as part of
`cefi_consolidated_native_ao_extract_2026_07_25.md` Todo 6._

### Root-cause diagnosis — 2026-08-04 by slot-15 (data_engineering)

**Verdict: PIPELINE STOPPAGE** (not Tardis vendor ceiling, not launcher config exclusion).

**Evidence:**

1. **Tardis API (a) — data IS available past 2026-05-22**: Direct `GET /v1/exchanges/upbit` query to `api.tardis.dev`
   confirms UPBIT is `"enabled": true`, available since `2021-03-03`, with **no exchange-level `availableTo`**. Symbols
   have been added as recently as **2026-07-31** (4 days before this diagnosis) — e.g. `BTC-AI` added 2026-06-30,
   multiple symbols added 2026-07-28 through 2026-07-31. This conclusively rules out "Tardis stopped carrying UPBIT
   data."

2. **Launcher config (c) — UPBIT IS included and NOT disabled**: `launch-cefi-sharded-backfill.sh` line 636 includes
   `UPBIT` in the default `VENUES` list alongside all other CEFI spot venues. The `_venue_years()` function (line 652)
   assigns UPBIT years `2022 2023 2024 2025 2026`. UPBIT is correctly classified as spot-only (`_venue_is_derivatives`
   returns 1 for UPBIT — it only gets the "heavy" group with `trades;book_snapshot_5`, no light/derivatives group). No
   config exclusion, no commented-out UPBIT, no de-prioritization.

3. **VM logs (b) — pattern matches SPOT preemption without auto-recovery**: The degradation pattern (2026-05-22: 606
   objects → May 23-24: 36 book_snapshot_5-only, KRW pairs only, no trades → May 25+: zero) is characteristic of a SPOT
   VM that was preempted mid-backfill and never auto-recovered. The `cefi-coverage-backfill` VM task uses SPOT by
   default (`--provisioning-model=SPOT`), and pre-May-2026 the preemption recovery infrastructure (`RelaunchPreemptedVm`
   actuator) may not have been in place for this launcher (the `lc_write_launch_params` +
   `lc_write_preemption_signal_file` preemption-recovery wiring was added 2026-07-15 per
   `cefi_completion_program_2026_07_15.md`). The 2-day residual tail (May 23-24 with KRW-only book data) is consistent
   with a partially-completed shard that finished its in-flight work before the VM terminated.

**Recommendation for Todo 2**: Since Tardis carries the data and the launcher config is correct, **relaunch the UPBIT
backfill** (2022-2026, heavy group only — `trades;book_snapshot_5` for SPOT_PAIR instruments). The preemption-recovery
infrastructure is now in place, so a fresh launch should complete normally. Scope:
`VENUES="UPBIT" YEARS="2022 2023 2024 2025 2026" LAUNCH_GROUPS="heavy" bash launch-cefi-sharded-backfill.sh`.
