---
doc_type: issue
title: HYPERLIQUID/trades live writer produces a blank-pipeline_mode row (not just blank source) — reproduced twice
summary: >-
  Surfaced while closing out source_column_blank_on_external_cells_2026_08_15.md's cefi backfill (8,840 rows fixed,
  applied to prod). A post-apply strict re-audit found 1 residual RED row in cefi/HYPERLIQUID/trades — reproduced
  identically on a SECOND independent strict-audit run minutes later (same row: date=2026-06-29,
  instrument_id=HYPERLIQUID:PERPETUAL:IP-USD@LIN, capture_status=empty_confirmed). Confirmed via direct row lookup: this
  row's pipeline_mode is ALSO blank/None, not just source — so the backfill script correctly skips it (nothing to derive
  from), and this is the pre-existing "CF-3 population" class the DeFi/TradFi precedent scripts already document as
  unfixable by a source backfill. This is a genuine, real write-path gap, out of scope for the source backfill task that
  found it.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [write-path, pipeline-mode, source-provenance, hyperliquid, data-correctness]
related:
  [
    /plans/active/issues/source_column_blank_on_external_cells_2026_08_15.md,
    /plans/active/data_source_provenance_enforcement_2026_07_24.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-08-15
author: slot-8 data_engineering
last_updated: 2026-08-15
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
context_scope:
  [
    /plans/active/issues/source_column_blank_on_external_cells_2026_08_15.md,
    market_tick_data_service/market_interface/adapters/onchain_perps/hyperliquid_adapter.py,
  ]
supersedes:
superseded_by:
resolved_by:
source: >-
  Found while running source_column_blank_on_external_cells_2026_08_15.md's [SCRIPT] P2 re-audit todo (re-run
  scripts/quality_gates/audit_source_column_distribution.py --strict after the cefi+tradfi backfills landed).
---

# HYPERLIQUID/trades live writer produces a blank-pipeline_mode row

## What I found

Two independent strict re-audits of the prod cefi manifest (`market-data-tick-cefi-prd-central-element-323112`), run
minutes apart at 2026-08-15T12:39Z and 2026-08-15T12:45Z, both found the SAME 1 RED row:
`cefi/HYPERLIQUID/trades rows=343026 {<blank>=1, hyperliquid=290369, tardis=52656}`.

Direct row lookup (streamed, `venue=='HYPERLIQUID' & data_type=='trades' & source blank`) identified the exact row:

```
date=2026-06-29  instrument_id=HYPERLIQUID:PERPETUAL:IP-USD@LIN
source=None  pipeline_mode=None  capture_status=empty_confirmed
```

**This row's `pipeline_mode` is ALSO blank**, not just `source`. `backfill_cefi_source_column.py` (this same session's
fix for the 14-cell residual) explicitly and correctly SKIPS rows with a blank `pipeline_mode` — there is nothing to
derive `source` from. This is exactly the "CF-3 population" class the DeFi (`backfill_defi_source_column.py`) and TradFi
(`restamp_tradfi_source_2026_07_07.py`) precedent scripts' own docstrings already document as a SEPARATE,
unfixable-by-backfill defect: rows written before the write path stamped `pipeline_mode` at all. A source-derivation
backfill cannot repair this class by construction — the fix has to be upstream, in whatever wrote this `empty_confirmed`
row for `HYPERLIQUID:PERPETUAL:IP-USD@LIN` on 2026-06-29 without ever setting `pipeline_mode`.

**Since the row is byte-identical across two audits 6 minutes apart** (same date, same instrument_id, same blank
values), this is NOT a moving target / new live write racing my read — it is one single static historical row that
predates whatever wired up `pipeline_mode` stamping for this venue's `empty_confirmed`/honest-absence path. The reason
it looked alarming mid-session (initially read as "a live writer keeps reintroducing a blank row") was a false lead —
the same row was simply re-observed twice, not regenerated.

## Why it matters

Not currently blocking anything — it is 1 row out of 29,481,508 (cefi) and does not affect the
`source_column_blank_on_external_cells_2026_08_15.md` backfill's own done-criteria (that task's scope was the 14 named
cells with a valid-`pipeline_mode`-but-blank-`source` shape; this row has neither). But it IS a genuine, un-derivable
provenance gap the `data_source_provenance_enforcement_2026_07_24.md` plan's still-open P0 "Write-path" todo should
eventually sweep up — and it's evidence that HYPERLIQUID's `empty_confirmed` write path has (or had) a code path that
skips `pipeline_mode` stamping entirely, worth checking whether it's still reachable today or purely historical.

## Recommended decision

Low priority (P2, 1 row) — either (a) determine whether this is a live-reachable code path in
`market_tick_data_service/market_interface/adapters/onchain_perps/hyperliquid_adapter.py`'s `empty_confirmed` write for
`trades` (if so, fix the write path so it can't happen again — this IS in scope for the still-open
`data_source_provenance_enforcement_2026_07_24.md` P0), or (b) if purely historical (the code path no longer exists), a
one-row manual manifest patch is not worth a dedicated script — fold the fix into whenever
`data_source_provenance_enforcement_2026_07_24.md`'s Write-path P0 todo is next worked, citing this doc.

## Todos

- [ ] [SCRIPT] P2. Determine whether
      `market_tick_data_service/market_interface/adapters/onchain_perps/hyperliquid_adapter.py` (or its shared
      `empty_confirmed`/honest-absence write path) has a live code path that can still stamp
      `capture_status=empty_confirmed` with a blank `pipeline_mode` for `trades`. If live: fix it (stamp `pipeline_mode`
      unconditionally on every manifest write, matching the universal-provenance wire-up other venues already got). If
      purely historical: note so here and fold the 1-row manual fix into
      `data_source_provenance_enforcement_2026_07_24.md`'s Write-path P0 todo rather than a standalone script. Repo:
      market-tick-data-service.

## Progress Log

- **2026-08-15 (slot-8·data_engineering)**: filed after two independent strict-audit re-checks (12:39Z, 12:45Z) found
  the identical single row, ruling out the initial "live writer keeps reintroducing it" hypothesis (see "What I found").
  No code changed — root-cause narrowed to blank `pipeline_mode`, not blank `source`; out of scope for the
  source-backfill task that surfaced it.
