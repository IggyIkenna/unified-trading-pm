---
doc_type: issue
title:
  InstrumentsHandler "boolean value of NA is ambiguous" blocks HYPERLIQUID captures + classification of 12 non-ASTER
  cefi MVP attempted_failed cells (B0 residual)
summary: |
  Surfaced 2026-07-06 while classifying the residual MVP-scoped attempted_failed cells for B0 in
  `is_catalogue_completion_2d_2026_07_06.md`. The 12 non-ASTER cefi MVP AF cells split into two classes on inspection.
  (1) FOUR HYPERLIQUID truly-missing days (2024-09-12/28, 2024-12-31, 2026-03-18) all fail the same way — a DEBUG-log
  retry (2026-07-06 15:05Z) reproduced `Handler InstrumentsHandler failed on payload 1: boolean value of NA is
  ambiguous` and "Batch complete: 0 results collected" with NO manifest write. Root class = pandas NA-in-boolean bug in
  the InstrumentsHandler process path (or a downstream pandas op the handler drives) that hits specifically on
  HYPERLIQUID payload shapes; every HL retry crashes at the same step, so this is a repeatable adapter/handler bug not
  a transient. (2) FOUR 2026-06-23 cells (BINANCE-SPOT / BITFINEX-SPOT / BITGET-SPOT / BITGET-FUTURES all
  attempted_at=2026-06-23T13:14:05.978Z — same millisecond, so a single upstream batch fault) are stale-AF rows —
  their same-cell captured rows already exist (written 2026-06-26/27); classification =
  RESOLVED_STALE_AF_KNOWN_MANIFEST_DEDUP-P2. The remaining FOUR non-truly-missing HYPERLIQUID cells (2023-12-01/13,
  2025-01-18, 2026-06-06) are also stale-AF (co-existing captured rows found) — same root class as (2). Tradfi CME
  residual = 1 AF (2026-06-20) + 6 EU sparse dates (2024-07-08, 2024-11-26, 2024-12-04, 2025-08-07, 2025-08-18,
  2026-06-24); pattern (mostly single sparse days) is consistent with market-calendar/upstream Databento gaps, needs
  per-date confirmation.
status: open
nature: notes
asset_group: [cefi, tradfi]
stage: [data]
repos: [instruments-service, unified-trading-library]
scope: [engineer]
tags: [instruments, adapter-bug, honest-coverage, mvp, af-classification, b0-residual, pd-na]
related:
  [
    ../is_catalogue_completion_2d_2026_07_06.md,
    ../instruments_completion_tracker_2026_07_06.md,
    ../instruments_mtds_subset_consistency_remediation_2026_06_17.md,
    ../pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md,
  ]
created: 2026-07-06
assigned_vm: planning
source:
  [
    is_catalogue_completion_2d_2026_07_06.md B0 gate — classification residual per main-agent BLK-749ae284 answer,
    live DEBUG retry of HYPERLIQUID 2024-09-12 (2026-07-06 15:05Z),
    live retry of BITFINEX-SPOT 2023-12-16 + KRAKEN-FUTURES 2023-12-16..19 (2026-07-06 15:00/15:01Z),
  ]
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
locked_by: live-defi-rollout
locked_since: 2026-05-21
parent_epic: instruments_master
resolved_by:
---

## What I found

### 1. InstrumentsHandler pd.NA bug — HYPERLIQUID payload shape breaks the write pipeline

Live retry of `HYPERLIQUID 2024-09-12` (`instruments-service --operation instruments --mode batch --asset-group cefi
--venues HYPERLIQUID --start-date 2024-09-12 --end-date 2024-09-12 --force --log-level DEBUG`) reproduced the failure
cleanly:

- URDI[HYPERLIQUID]: fetched 176 instruments (11 subventures 429-rate-limited on the `earliest-funding` probe —
  fallback to launch date, non-fatal).
- Date filter 2024-09-12: 109 instruments active.
- ManifestWriter GET `_index/availability_index.parquet` succeeded (existing index read OK).
- `_index/per_vm/local-*.parquet` 404 (expected — no prior shard on this host).
- `WARNING Handler InstrumentsHandler failed on payload 1: boolean value of NA is ambiguous`.
- `INFO Batch complete: 0 results collected` → no captured row written.

Repro rate = 100% on retry; every truly-missing HYPERLIQUID day has the same fingerprint. The other three (2024-09-28,
2024-12-31, 2026-03-18) share the same one-shot attempt-then-crash pattern
(`attempted_at == written_at ± 6ms`, `row_count=0`, `error_reason=UNCLASSIFIED_ADAPTER_ERROR`) so they are the same
bug — the classifier didn't recognise the pd.NA ValueError.

The BITFINEX-SPOT smoke retry hit a DIFFERENT pandas warning (`Cannot convert ['2839'…] to numeric`) which is a
non-fatal payload-1 warning and did NOT block the write ("`5 new` entries in the availability index"). So the pd.NA
ambiguity is HYPERLIQUID-shape-specific, not a global handler bug.

### 2. Four 2026-06-23 cefi cells are STALE-AF (not truly missing)

BINANCE-SPOT / BITFINEX-SPOT / BITGET-SPOT / BITGET-FUTURES all show `attempted_at = 2026-06-23T13:14:05.978Z` — the
same millisecond across four venues, so a single upstream batch fault (network / auth / Tardis-side). All four cells
now have same-day captured rows written 2026-06-26/27 → the AF rows are STALE, the data is present. Same dedup
class as the `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05` finding: when the (venue,date)
gets a retry into `captured` the writer emits a new row with populated `instrument_type/pipeline_mode/source`, and
the manifest dedup key mismatch keeps the blank-shard-atom failed row alongside.

### 3. Four "stale-AF" HYPERLIQUID cells co-exist with captured data

HYPERLIQUID 2023-12-01, 2023-12-13, 2025-01-18, 2026-06-06 all show co-existing captured rows in the same
(venue,date) — classification = same stale-AF class as (2). Only the four (2024-09-12/28, 2024-12-31, 2026-03-18)
are TRULY missing (no matching captured row), and all four hit the pd.NA handler bug on retry.

### 4. Tradfi CME residual — market-calendar / Databento sparse gaps

`CME 2026-06-20` AF (1 cell) + `CME` EU on 2024-07-08 / 2024-11-26 / 2024-12-04 / 2025-08-07 / 2025-08-18 /
2026-06-24 (6 cells). Pattern is single-day sparse gaps — 2024-11-26 sits adjacent to US Thanksgiving 2024
(Thanksgiving = Nov 28), 2024-07-08 immediately post-July-4-observed. Consistent with market-calendar edges or
Databento missing-day gaps. Not the same class as the HL adapter bug; needs per-date confirmation against the
Databento CME calendar / TradFi v9 apply completion (in-flight via `tradfi_v9_stage1_finish_2026_07_06.md`).

## Why it matters

- The pd.NA handler bug is the ROOT class of 4 truly-missing MVP HYPERLIQUID cells — every retry crashes at the same
  point, so this is on the honest-coverage critical path (cefi Layer-1 for HYPERLIQUID cannot go 100% until the
  handler write step accepts the payload shape).
- The classification unblocks B0's "0 missing MVP" gate per the main-agent BLK-749ae284 answer: 40 ASTER = Stage-2c
  in-flight (accepted); 24 cefi EU 2023-12-16..19 = historical service outage floor (accepted, document); 12 cefi
  AF now classified into the two named classes above (accept 8 as RESOLVED_STALE_AF, accept 4 as
  KNOWN_HANDLER_BUG_PD_NA with a fix TODO); 7 tradfi CME residual = market-calendar/Databento gap (accept, verify
  post-tradfi-v9-apply).
- Follow-on: TRUE 0-missing requires (a) the pd.NA fix so HL truly-missing days clear on retry, (b) the manifest
  dedup fix (already tracked P2 in `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05`) so stale-AF
  rows collapse, and (c) the tradfi v9 apply chain completing (already tracked in `tradfi_v9_stage1_finish`). None
  of these are in scope for B0's flip — they're separate tracked items.

## Recommended decision

Accept the classification and flip B0. Track the pd.NA fix + tradfi CME verify as the P1/P2 todos below.

- [ ] [CODE] P1. Reproduce + fix the InstrumentsHandler "boolean value of NA is ambiguous" on HYPERLIQUID payloads;
      first reproduce with `.venv/bin/python -m instruments_service --operation instruments --mode batch --asset-group
      cefi --venues HYPERLIQUID --start-date 2024-09-12 --end-date 2024-09-12 --force --log-level DEBUG`, capture the
      full traceback (raise `logger` in `cli/instruments_handler.py` to log the exception's traceback not just the
      "failed on payload" one-liner), narrow to the pandas op that receives a pd.NA in a boolean context, guard with
      `pd.isna(…)` or `.fillna(False)`. Verify by re-running the 4 truly-missing HYPERLIQUID days
      (2024-09-12/28, 2024-12-31, 2026-03-18) and confirming `capture_status=captured` in the manifest.
      (repo: instruments-service)
- [ ] [VERIFY] P2. Per-date confirm the 7 tradfi CME residual cells (2024-07-08 / 2024-11-26 / 2024-12-04 /
      2025-08-07 / 2025-08-18 / 2026-06-20 AF / 2026-06-24 EU) against the Databento CME trading-calendar. Cross-check
      whether each is a real market-closure day (holiday / session-end / no ohlcv-1m tick coverage) vs a fetch gap
      that needs a re-fetch. Post-`tradfi_v9_stage1_finish` completes, re-measure. (repo: instruments-service)
- [ ] [DATA] P2. When the manifest dedup fix (`pipeline_mode_source_batch_live_replay_standardisation_2026_06_05`)
      lands, run the targeted reconcile that collapses the 8 stale-AF cefi rows (4 HL 2023-12-01/13, 2025-01-18,
      2026-06-06 + 4 2026-06-23 batch venues) so the coverage rollup stops double-counting them. Do NOT hand-edit the
      dedup machine (per `instruments_mtds_subset` P2 finding). (repo: unified-trading-library)

## Progress log

- **2026-07-06** — Issue filed. Root-caused HL InstrumentsHandler failure to a repeatable pd.NA-in-boolean bug via a
  DEBUG-log retry of 2024-09-12 (`is@LDR`). Classified the 12 non-ASTER cefi MVP AF cells into
  KNOWN_HANDLER_BUG_PD_NA (4) + RESOLVED_STALE_AF (8), plus the tradfi CME 7 as
  MARKET_CALENDAR_OR_DATABENTO_GAP-pending-verify. Unblocks `is_catalogue_completion_2d` B0 gate flip.
