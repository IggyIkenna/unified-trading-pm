---
title: "CeFi Tardis backfill — writegate Phase 2 findings (bundle shard shape + missing rows_captured)"
created: 2026-05-07
author: harsh
source:
  - plans/active/cefi_master_2026_05_07.plan.md (in-flight section + 3-findings annotation, PM@9b1f1d5)
  - plans/active/writegate_honest_coverage_endtoend_2026_05_06.plan.md (Phase 2.A residual + Phase 2.E progress events)
  - cursor-configs/CLAUDE.md § "Shard-granularity SSOT" + § "No fire-and-forget VM launches"
  - gs://market-data-tick-cefi-central-element-323112/_index/per_vm/cefi-bitfinex-spot-2020-heavy-20260507-150340.parquet
  - gs://market-data-tick-cefi-central-element-323112/_index/per_vm/cefi-kraken-spot-2020-heavy-20260507-151100.parquet
  - gs://central-element-323112-events/events/market-tick-data-service/2026-05-07/cefi-bitfinex-spot-2020-heavy-20260507-150340/hour=14/*.jsonl
locked_by: live-defi-rollout
locked_since: 2026-05-07
---

# CeFi Tardis backfill — writegate Phase 2 findings

> **Severity**: P0 — both findings contradict workspace SSOTs in CLAUDE.md and were observed in an in-flight 37-VM
> production run.
> **Blast radius**: cefi asset_group (37 VMs in flight today; ~252 venue-year-instrument-type shards across
> bitfinex/bitget/kraken futures+spot 2020-2026); writegate Phase 2.A residual + Phase 2.E surface; data-status
> drilldown UI.
> **Suggested owner**: Ikenna (writegate Phase 2.A + 2.E per work-split D2 P0).

## Context

37 cefi VMs were launched 2026-05-07 ~14:00 UTC in `asia-northeast1-c` covering bitfinex/bitget/kraken × futures+spot
× 2020-2026 (`e2-highmem-2`). Sample event verification at T+30min on 3 VMs found data IS being written
(`instrument_count=8,310,353` ticks per bundle row), but two writegate-rule violations surfaced.

## Finding 1 — Asymmetric manifest shard shape (captured = bundle-level, empty_confirmed = per-instrument)

### What I found

Per-VM manifest shard inspection on 2 VMs (200 + 250 rows) shows:

| capture_status   | rows | instrument_id populated | instrument_count    |
| ---------------- | ---- | ----------------------- | ------------------- |
| `captured`       | 8 / 10 | **0% (empty string)** | 8,310,353 (bundle)  |
| `empty_confirmed`| 192 / 240 | **100%** (BTCUSD, ETHUSD, ...) | 0     |

Sample `captured` row from `cefi-bitfinex-spot-2020-heavy-20260507-150340` per-VM shard (date 2020-01-01,
data_type book_snapshot_5):

```python
{'date': '2020-01-01', 'venue': 'BITFINEX-SPOT', 'data_type': 'book_snapshot_5',
 'instrument_type': 'SPOT_PAIR',
 'instrument_id': '',                          # ← empty
 'instrument_count': 8310353,                  # ← bundle-level rollup
 'capture_status': 'captured',
 'error_reason': '', 'expected': True, 'available': True,
 'written_at': '2026-05-07T14:10:28.941163+00:00',
 'schema_version': 7}
```

Sample `empty_confirmed` row from the same shard (same date, same data_type):

```python
{'date': '2020-01-01', 'venue': 'BITFINEX-SPOT', 'data_type': 'book_snapshot_5',
 'instrument_type': '',                        # ← empty
 'instrument_id': 'BTCUSD',                    # ← per-instrument
 'instrument_count': 0,
 'capture_status': 'empty_confirmed',
 'error_reason': '',
 'written_at': '2026-05-07T14:10:28.941287+00:00'}
```

Pattern repeats identically on `cefi-kraken-spot-2020-heavy-20260507-151100` (10 captured / 240 empty_confirmed).

### Why it matters

This contradicts the per-asset-group shard-key matrix codified in CLAUDE.md § "Shard-granularity SSOT":

> CeFi spot/perp: (asset_group, venue, data_type, instrument_type, instrument_id, day) — per-instrument (35GB roots,
> source atom is per-instrument-per-day).

A captured row with empty `instrument_id` + populated `instrument_count=8.3M` is bundle-level rollup, not the
per-instrument shard the SSOT requires. Concrete consequences:

1. **Data-status drilldown can't show per-instrument coverage** for cefi spot — the captured rows don't carry the
   `instrument_id` axis the deployment-UI drilldown panel pivots on. Operators see "BITFINEX-SPOT book_snapshot_5
   2020-01-01 = captured" but can't drill to "which 24 of 25 instruments did we actually capture?"
2. **Phantom-audit cannot reconcile per-instrument** — `reconcile_phantom_manifest_rows_all.py` works at row-key
   granularity. Bundle-level captured rows pass without per-instrument verification.
3. **Cluster-coverage gate is bypassed** — workspace rule "Validation gates per `record_captured` — 4 pillars" pillar
   #4 (cluster coverage ≥ expected) cannot fire on a bundle-shaped row because there's no `instrument_id` axis to
   count clusters against.
4. **Same class as TradFi MVP partial-bundle** (ES.OPT 18 single-parent fills) and **MDPS 1440-NaN-OHLC** — captured
   rows at the wrong granularity that pass the rollup check but mask per-instrument absence.

### Recommended decision

Owner: Ikenna writegate Phase 2.A residual (per work-split D2 P0). Two ways to land the fix:

- **Option A (per-instrument captured rows — workspace SSOT-conformant)**: cefi adapter writes one captured row per
  (venue, data_type, instrument_id, day) with the per-instrument tick count. Bundle stops existing in the manifest.
  Most disruptive but matches CLAUDE.md SSOT directly.
- **Option B (keep the bundle row, ALSO write per-instrument rows)**: bundle-level row continues for fast rollup;
  per-instrument captured rows added underneath for drilldown + cluster validation. Doubles row count per (venue,
  data_type, day) but preserves rollup performance.
- **Option C (pure re-shape)**: keep the row count, but populate `instrument_id` on the captured row by emitting
  one per-instrument captured per actual instrument that captured ≥1 tick, while the empty_confirmed rows continue
  for instruments that captured zero. This is the cleanest match to the SSOT.

C is most aligned with TradFi futures bundle handling. Operator + writegate-owner pick.

## Finding 2 — `PROCESSING_COMPLETED` events lack `rows_captured` field

### What I found

Sample event stream from `cefi-bitfinex-spot-2020-heavy-20260507-150340` hour=14 partition (57 events total in 30 min):

```text
COMPLETED  2026-05-07T14:10:29  date=2020-01-01  rows=?  shards=?  duration_s=?
COMPLETED  2026-05-07T14:14:28  date=2020-01-02  rows=?  shards=?  duration_s=?
COMPLETED  2026-05-07T14:18:40  date=2020-01-03  rows=?  shards=?  duration_s=?
COMPLETED  2026-05-07T14:22:22  date=2020-01-04  rows=?  shards=?  duration_s=?
```

Event details carry `date`, `asset_groups`, `venue_count` — **no `rows_captured`, `shards_captured`,
`instruments_processed`, or `duration_seconds` fields.** No `INSTRUMENT_PROCESSED` events in the stream at all.

### Why it matters

CLAUDE.md § "No fire-and-forget VM launches" requires:

> Adapters MUST emit per-instrument progress events with row counts so silent-success-with-zero-output is detectable
> from the event stream alone.

This is a hard rule because the 2026-05-05 MDPS 1440-NaN-OHLC reference incident specifically named "absence of
intermediate progress events with row counts" as the silent-success signal that wasn't there. The cefi adapter
hits the same gap: PROCESSING_COMPLETED fires per date but carries no row count, and there's no per-instrument
INSTRUMENT_PROCESSED event at all.

Concrete consequence: if the cefi Tardis adapter regressed to silent-zero for a chain/venue combination tomorrow,
the only way an operator would notice is by reading the per-VM manifest shard parquet directly — events alone
would say "STARTED + PROCESSING_STARTED + PROCESSING_COMPLETED + ..." with no signal that zero rows were captured.
This is exactly the failure mode the workspace rule was written to prevent.

### Recommended decision

Owner: Ikenna writegate Phase 2.E (per-source progress events) per work-split / writegate plan. Concrete asks:

- Add `rows_captured`, `shards_captured`, `duration_seconds` to `PROCESSING_COMPLETED` `details` payload.
- Add `INSTRUMENT_PROCESSED` event firing per-instrument with `instrument_id`, `rows_captured`, `data_type` so
  silent-success-with-zero-output is visible at instrument-granularity in the live event stream.
- Mirror the shape across cefi / tradfi / defi MTDS adapters so the rule applies workspace-wide, not per-asset_group.

## Cross-references

- `plans/active/cefi_master_2026_05_07.plan.md` § "Tardis-venues backfill IN-FLIGHT" (PM@9b1f1d5) — operational
  context + per-VM evidence.
- `plans/active/writegate_honest_coverage_endtoend_2026_05_06.plan.md` Phase 2.A + Phase 2.E — fix lands here.
- `cursor-configs/CLAUDE.md` § "Shard-granularity SSOT" — SSOT this contradicts (finding 1).
- `cursor-configs/CLAUDE.md` § "No fire-and-forget VM launches" — SSOT this contradicts (finding 2).
- `cursor-configs/CLAUDE.md` § "Findings Triage Discipline (HARD RULE)" — case-5 (big) escalation pathway.

## VM-blocker assessment

**NOT VM-blocking.** The 37-VM run is producing data (`instrument_count=8.3M` ticks per bundle row, 4 dates
processed in 30 min on the sample VM). Findings 1 + 2 are about manifest shape + observability, not data loss.
Operator decision: let the VMs run to completion (ETA ~05-08/09 per cefi_master), then either (a) re-rescan with
the per-instrument writegate fix applied retroactively, or (b) accept bundle-shaped manifest for this 37-VM batch
+ enforce per-instrument shape from the next backfill onward. C2 of recommendation #1 (pure re-shape) keeps
existing data on disk usable while migrating to canonical shape.
