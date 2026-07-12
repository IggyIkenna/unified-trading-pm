---
doc_type: issue
title:
  OnchainPerpBatchHandler hardcodes HYPERLIQUID/ASTER only — LIGHTER/PACIFICA/EXTENDED backfill silently captures 0 rows
summary: >
  While re-verifying the cefi G4 gate (mvp_backfill_cefi_tick_v10_2026_06_27.md), extended
  launch-cefi-hl-aster-historical-backfill.sh to also target LIGHTER-ZKSYNC/PACIFICA-SOLANA/ EXTENDED-STARKNET
  (deployment-service@dfe2784) since these venues sit at 0 captured Layer-1 tuples and umi_tick_provider.py appeared to
  route them generically. Launched 8 SPOT VMs; all produced exactly 0 rows every single day with NO error, because
  market-tick-data-service's OnchainPerpBatchHandler (collect-onchain-perp-batch operation) hardcodes its venue-source
  map to HYPERLIQUID and ASTER only and silently filters any other requested venue out, so the day-loop "succeeds" doing
  nothing for the VM's entire lifetime. VMs were terminated once found. The real fetch code for these 3 venues already
  exists (the _umi_lighter / _umi_pacifica / _umi_extended adapter modules, ~500-650 lines each) but is currently wired
  only into perp_funding_handler.py's separate code path, not into OnchainPerpBatchHandler.
status: open
nature: notes
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [data-correctness, silent-failure, venue-allowlist, cefi, honest-coverage, layer-1]
related:
  [
    plans/active/mvp_backfill_cefi_tick_v10_2026_06_27.md,
    plans/active/issues/cefi_layer1_denominator_gaps_2026_07_03.md,
  ]
created: 2026-07-12
parent_epic: cefi_master
priority: P1
source: [plans/active/mvp_backfill_cefi_tick_v10_2026_06_27.md G4 re-verification, slot-2 2026-07-12]
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-12
locked_by:
resolved_by:
---

> **NOTIFY-OPERATOR class finding (data-correctness, silent failure).** No VM launch will EVER close the LIGHTER-ZKSYNC
> / PACIFICA-SOLANA / EXTENDED-STARKNET Layer-1 denominator gaps in `mvp_backfill_cefi_tick_v10_2026_06_27.md` until
> this code fix lands — the day-loop reports "success" (exit 0, `PROGRESS: chunk=N/365 ...`) on every single date while
> writing zero rows, so nothing in the launcher/orchestrator surfaces this as an error.

## What I found

During cefi G4 re-verification (2026-07-12), `measure_honest_coverage.py` Layer-1 showed 3 whole venues at
`present_tuples=0` despite being declared in the cefi universe with UAC `VENUE_DATA_TYPE_CAPABILITIES` start dates
already set (D2b, 2026-07-06):

| venue             | expected tuples               | present |
| ----------------- | ----------------------------- | ------- |
| LIGHTER-ZKSYNC    | 3 (book5/deriv_ticker/trades) | 0       |
| PACIFICA-SOLANA   | 3                             | 0       |
| EXTENDED-STARKNET | 3                             | 0       |

`grep -rli "lighter\|pacifica\|extended.starknet" market_tick_data_service/` showed live-only WS connectors
(`live/connectors/{lighter_zksync,pacifica_solana,extended_starknet}_perp_ws.py`) AND REST adapter modules
(`adapters/_umi_{lighter,pacifica,extended}.py`, ~500-650 lines each, exposing `fetch_lighter_rest` / equivalent with
real trades+book fetch functions), plus generic venue routing for these 3 venues inside `adapters/umi_tick_provider.py`
(chain-kind mapping, `_fetch_lighter_rest` dispatch by `venue_upper == "LIGHTER-ZKSYNC"` etc.). This looked like
ready-made infrastructure, so I extended `deployment-service/scripts/vm/launch-cefi-hl-aster-historical-backfill.sh`
(which drives `--operation collect-onchain-perp-batch`) to add these 3 venues alongside HYPERLIQUID/ASTER — shipped as
`deployment-service@dfe2784` — and launched 8 SPOT VMs (year-sharded, 2024/2025/2026 per venue per their UAC
start_date).

**All 8 VMs produced zero rows.** Checked the run.log for `cefi-lighter-zksync-2025-...`
(`gs://deployment-scripts-central-element-323112/vm-logs/cefi-lighter-zksync-2025-20260712-033210/run.log`): every
single day's chunk logged
`OnchainPerpBatch complete for <date>: 0 rows across venues=[] data_types=['trades', 'book_snapshot_5', 'derivative_ticker']`
— **`venues=[]`, not `['LIGHTER-ZKSYNC']`** — meaning the requested venue was silently dropped before any fetch was
attempted. No exception, no warning, `PROGRESS:` line still printed as if the chunk succeeded.

Root cause in `market_tick_data_service/cli/handlers/onchain_perp_batch_handler.py`:

```python
_VENUE_SOURCE: dict[str, str] = {"HYPERLIQUID": "hyperliquid", "ASTER": "aster"}
...
venues = _resolve_csv_arg(self, "venues", ("HYPERLIQUID", "ASTER"))
venues = [v for v in venues if v in _VENUE_SOURCE]   # <- silently drops anything else
```

`_VENUE_SOURCE` / `_VENUE_PIPELINE_MODE` / `_VENUE_CHAIN` / `_VENUE_LAUNCH` are ALL hardcoded to exactly
`{"HYPERLIQUID", "ASTER"}` (lines ~153-166). `OnchainPerpBatchHandler` is genuinely HL/ASTER-only at the code level —
the umi_tick_provider.py routing I found earlier is a **separate code path** consumed by `perp_funding_handler.py` (a
different `--operation`), not by `collect-onchain-perp-batch`.

**VMs terminated** (`gcloud compute instances delete` on all 3 still-RUNNING 2025-shard VMs at 2026-07-12T04:1x Z) once
the zero-rows pattern was confirmed, to stop burning SPOT spend on a guaranteed-empty 365+540-day day-loop per venue.

## Why it matters

1. **The G4 gate for cefi cannot close** until LIGHTER-ZKSYNC/PACIFICA-SOLANA/EXTENDED-STARKNET have real captured rows
   — no amount of VM re-launching fixes this without the code change.
2. **Silent-failure risk beyond this incident**: `venues = [v for v in venues if v in _VENUE_SOURCE]` with no logged
   warning for a dropped venue means ANY future worker who requests a venue outside `{HYPERLIQUID, ASTER}` via this
   handler will get a "successful" multi-hour VM run that writes nothing, with no signal to notice except manually
   reading run.log for `venues=[]`. This is worth hardening independently of the 3-venue feature gap.

## Recommended fix

1. `[CODE]` P1. Add `LIGHTER-ZKSYNC` / `PACIFICA-SOLANA` / `EXTENDED-STARKNET` to `_VENUE_SOURCE` /
   `_VENUE_PIPELINE_MODE` / `_VENUE_CHAIN` / `_VENUE_LAUNCH` in `onchain_perp_batch_handler.py`, and add a
   `_process_venue` fetch branch for each that calls the existing REST adapters
   (`adapters/_umi_lighter.fetch_lighter_rest`, `_umi_pacifica.<equivalent>`, `_umi_extended.<equivalent>`) the same way
   `_fetch_hyperliquid_s3` / `_fetch_aster_rest` are dispatched today. Use the UAC `VENUE_DATA_TYPE_CAPABILITIES` start
   dates already declared (LIGHTER 2024-08-01, PACIFICA 2025-06-01, EXTENDED 2024-10-01) for `_VENUE_LAUNCH`. Add
   regression tests mirroring the existing HL/ASTER coverage (per-venue dispatch, honest-absence pre-launch
   classification).
2. `[CODE]` P2. Make the `venues = [v for v in venues if v in _VENUE_SOURCE]` filter loud — log a `WARNING` (or raise)
   naming any `--venues` entry that was silently dropped, so a future mis-targeted launch fails fast instead of running
   a multi-hour no-op.
3. `[VERIFY]` P1. Once (1) ships, re-launch LIGHTER-ZKSYNC/PACIFICA-SOLANA/EXTENDED-STARKNET via the already-extended
   `launch-cefi-hl-aster-historical-backfill.sh` (deployment-service@dfe2784 — no further launcher change needed) and
   verify real rows land (check run.log for `venues=['LIGHTER-ZKSYNC']` and `rows_written > 0`, not just VM RUNNING
   status).

## Open actions

- [ ] [CODE] P1. Wire LIGHTER-ZKSYNC/PACIFICA-SOLANA/EXTENDED-STARKNET into `OnchainPerpBatchHandler` (see
      recommendation 1). (repo: market-tick-data-service)
- [x] ✅ [CODE] P2. Log/raise on silently-dropped `--venues` entries in `OnchainPerpBatchHandler` (see recommendation
      2). (repo: market-tick-data-service) — `market-tick-data-service@4f62bd7e`. Extracted `_resolve_venues()`: any
      `--venues` token not in `_VENUE_SOURCE` is now logged as a `WARNING` naming the dropped venue(s) before the
      supported subset is returned, so a mis-targeted launch (e.g. `LIGHTER-ZKSYNC`) surfaces immediately instead of
      only being discoverable by grepping run.log for `venues=[]`. 2 new unit tests
      (`test_resolve_venues_drops_unsupported_and_warns`, `test_resolve_venues_all_supported_no_warning`).
      quality-gates.sh green (899/900 lines, under the file-size cap after a ruff reformat).
- [ ] [VERIFY] P1. Re-launch the 3-venue backfill after the code fix lands and confirm real rows write (see
      recommendation 3). (repo: deployment-service)
