---
title: TradFi expected_unattempted not draining — source-axis EU drift from the un-re-enumerated databento-first flip
created: 2026-06-24
source:
  - live manifest gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet (read 2026-06-24 19:49Z)
  - instruments-service/scripts/enumerate_expected_universe.py (_seed_pipeline_source_transport, L300-330)
  - deployment-service/scripts/wave_launcher.py (NEEDS_WORK, L106)
  - live VM run.log gs://deployment-scripts-central-element-323112/vm-logs/tradfi-bf-cme-ohlcv-1m-gc-2025-20260624-114619/run.log
locked_by: live-defi-rollout
parent_epic: tradfi_master
priority: P2
status: active
---

# TradFi EU not draining — source-axis seed/capture drift (PROVEN)

## What I found (root cause — PROVEN with cell-level evidence)

The tradfi `expected_unattempted` (EU) is dead-flat at **1,084,542** while a multi-VM CME/NYSE/NASDAQ databento
backfill campaign burns compute. **Root cause = the EU seeds were materialised under the OLD `SOURCE_PRIORITY[0] =
massive`, and the 2026-06-24 databento-first flip was never followed by a re-enumeration — so the seeds' `source`/
`pipeline_mode` key no longer matches the `source=databento` rows the campaign actually captures. The two are disjoint
manifest row-keys, so databento captures can never reconcile (drain) the massive seeds.**

This is precisely the failure the enumerator's own docstring warns against
(`enumerate_expected_universe.py::_seed_pipeline_source_transport`, L304-309):
> "the seeds the enumerator materialises MUST carry the same pipeline_mode + source (+ transport) as the real rows they
> will be reconciled against — else the denominator-seed rows diverge from real rows … source = the top external source
> for (asset_group, data_type)." — i.e. `SOURCE_PRIORITY[0]` **at enumeration time**.

### The evidence

**1. EU is keyed on a source the campaign no longer fetches.** From the live `_index` (manifest row key includes
`source` + `pipeline_mode`):

| capture_status | source | pipeline_mode | rows |
|---|---|---|---|
| expected_unattempted | massive | batch_massive | **748,481** (69% of EU) |
| expected_unattempted | databento | batch_databento | 336,061 |
| captured | databento | batch_databento | **654,602** |
| captured | massive | batch_massive | 70,665 |

**2. CME ohlcv_1m (source × status)** — the captures and the EU are disjoint sets:
- `databento`: 147,159 captured / **0 EU**
- `massive`: 49,298 captured / **173,190 EU** / 586,085 empty_confirmed

**3. Timing proves it's a stale pre-flip seed, not a live mis-seed.** All EU rows carry
`enumerator_run_id = enum-universe-tradfi-20260622-*`, `written_at` max **2026-06-22T15:45Z** — i.e. seeded
2026-06-22, when `SOURCE_PRIORITY[0]` for (tradfi, ohlcv_1m/ohlcv_15m/trades/tbbo) was still `massive`. The
databento-first flip is **2026-06-24** (CLAUDE.md + UAC `_source_priority_data`). Current live
`SOURCE_PRIORITY[('tradfi','ohlcv_1m')] = ['databento','massive','yahoo']`.

**4. The campaign IS capturing databento (it's not the bug) — it just can't drain the massive seeds.** Live GC-2025
VM run.log (19:47-19:50Z): `Pre-flight: venue=CME date=2025-09-24 ohlcv_1m — 2 of 2 expected atoms still missing
(GC.FUT, GC.OPT)` → fetches → `Manifest updated … complete=True … 53987 records` → `captured=2`. So the databento
capture rows grow; the `source=massive` EU rows are untouched → EU dead-flat.

**5. The wave-launcher perpetuates the waste.** `wave_launcher.py::NEEDS_WORK = {expected_unattempted,
attempted_failed}` counts a cell as "needs work" if its **per-source row** is EU. So it keeps seeing the 748k orphaned
massive-EU cells, dispatches (venue,root,year) VMs for them; the VM pre-flight then fetches databento (already covered
or newly captured under a different key) and the massive EU row is never reconciled → next tick re-dispatches the same
shards. Compute burned, EU never moves.

## Why it matters

- **Data-pipeline correctness (the heartbeat).** The raw EU metric (1.08M) is the monitoring signal for "remaining
  tradfi work"; 748k of it is undrainable noise, masking the true databento gap and reading as a stalled campaign.
- **Wasted compute + metered-billing risk.** The wave-launcher re-dispatches done shards every 2-3h forever; each VM
  re-hits databento (mostly L0/free here, but the pattern is wrong and at scale risks metered L1/L2 re-fetches).
- **Blocks the tradfi-universe OPS pass (KRX/equities/options).** Adding the planned MTDS OHLCV wave on top of this
  would add more VMs that re-dispatch orphaned-source EU rather than drain real gaps (operator's explicit warning).

## Scope

TradFi-only for the **data** (the databento-first flip was tradfi-scoped, 2026-06-24; cefi/defi/sports source maps
unchanged). The wave-launcher `NEEDS_WORK` source-blindness is **cross-cutting** machinery but only bites where a
SOURCE_PRIORITY flip left orphaned seeds — today that's tradfi.

## Recommended decision (the fix)

A re-run alone is **not** sufficient — there is no automatic stale-source-seed retirement in the enumerator/consolidator
(seeds are keyed by `source`; a databento re-run writes NEW rows and leaves the 748k massive rows as orphans the
wave-launcher still picks up). The complete fix is a coordinated, single-walk manifest operation:

1. **Retire the orphaned massive EU seeds** for the data_types where massive is no longer `SOURCE_PRIORITY[0]`
   (tradfi ohlcv_1m/ohlcv_15m/trades/tbbo: `source=massive` + `capture_status=expected_unattempted`). These are
   meaningless under databento-first (massive is now FALLBACK[1], not backfilled). Reclassify/drop — NOT re-fetch.
2. **Re-run `enumerate_expected_universe.py` for tradfi** with the live databento-first priority → re-seeds EU under
   `source=databento`. Cells databento already captured drop out of EU; genuinely-missing cells become drainable
   databento gaps. (Verify the run SUPERSEDES prior seeds by latest `enumerator_run_id`, or pair with step 1.)
3. **Make the wave-launcher gap source-resolved (defensive, prevents recurrence).** A cell is a gap only if NO source
   in `SOURCE_PRIORITY` has it `captured` — i.e. collapse on `(venue,date,data_type,instrument_id)` via
   `select_primary_available_source()` before applying `NEEDS_WORK`. Then a future SOURCE_PRIORITY flip can't strand
   the launcher on orphaned-source EU.
4. **Re-consolidate + snapshot** the tradfi `_index` and confirm EU drains on the next wave tick (EU(massive) → 0 for
   the flipped data_types; captured climbs only for genuine databento gaps).

Filed (not auto-fixed) because steps 1-2 reclassify ~748k live manifest rows (single-walk discipline + data-correctness
across the tradfi manifest), and step 3 changes shared wave-launcher gap semantics — both exceed "small + clearly safe +
one-repo" and need operator awareness before execution. The OPS-pass STEP 4 (MTDS KRX/equities/options OHLCV wave) is
**HELD** until this drains.

## Progress / status
- 2026-06-24 — Filed. Root cause PROVEN (source-axis seed/capture drift from un-re-enumerated 2026-06-24 databento
  flip). Awaiting operator decision on executing the 4-step fix (esp. the 748k massive-seed retirement, which is the
  destructive-ish single-walk step). Coordinator NOTIFIED in chat.
