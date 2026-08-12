---
doc_type: issue
title:
  MTDS QG red — lending_indices COMPOUND_V3 fallback path emits `batch_compound_v3`, test (and the onchain-subgraph
  convention) expects `batch_onchain_subgraph`
summary: >-
  Pre-existing `market-tick-data-service` quality-gates red blocking all shipping (slot 32's sports P2 `trades`→`odds`
  re-stamp included). `test_collect_protocol_chain_writes_canonical_partition_compound` fails deterministically: when
  the mocked instruments-store parquet for COMPOUND_V3 is absent, the handler's fallback write path emits
  `pipeline_mode=batch_compound_v3`, but the test asserts `pipeline_mode=batch_onchain_subgraph` (the primary path's
  value, via `pipeline_mode_for_source("onchain_subgraph", ...)` at
  `market_tick_data_service/cli/handlers/lending_indices_handler.py:348`). Confirmed pre-existing on clean LDR HEAD: CI
  `quality-gates-v2` failed with the SAME assertion in both runs today (31636664383 @ 20:14, 31632477709 @ 19:24),
  before slot 32's commit landed. AAVE_V3 asserts the same `batch_onchain_subgraph` convention at test line 106, so the
  fallback's venue-specific `batch_compound_v3` token is the drift, not the test.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [qg-red, repo-blocker, lending-indices, defi, pipeline-mode, path-shape]
related:
  [
    /codex/02-data/pipeline-mode-partition.md,
    /plans/active/sports_taxonomy_p2_migration_2026_08_08.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-08-12
author: [ikennaigboaka (slot-32, data_engineering)]
source: ["slot-32 quality-gates.sh Pass-1 run on 071a5466 + CI verification of 31636664383/31632477709"]
parent_epic: defi_master
resolved_by:
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
drift_direction: advance-code
archive_exempt: true
depends_on: []
locked_by:
locked_since:
---

# MTDS QG red — lending_indices COMPOUND_V3 pipeline_mode drift

## What I found

Running Pass-1 `quality-gates.sh` in `market-tick-data-service` at HEAD `071a5466` (slot-32 sports re-stamp commit,
which adds 3 NEW unreferenced files under `scripts/sports/`) fails exactly one test:

```
FAILED tests/unit/test_lending_indices_handler.py::test_collect_protocol_chain_writes_canonical_partition_compound
AssertionError: assert 'day=2026-04-17/pipeline_mode=batch_onchain_subgraph/asset_group=defi/venue=COMPOUND_V3/chain=ETHEREUM/'
in 'raw_tick_data/by_date/day=2026-04-17/pipeline_mode=batch_compound_v3/asset_group=defi/venue=COMPOUND_V3/...'
```

Mechanism (read from `lending_indices_handler.py`, not guessed): the primary `_collect_protocol_chain` path resolves
`pipeline_mode_for_source("onchain_subgraph", ...)` (line 348) → `batch_onchain_subgraph`. When the mocked
instruments-store parquet is absent (the test's environment), the handler logs "falling back to subgraph discovery" and
writes through a fallback path that emits the venue-specific `batch_compound_v3` token. The test asserts the primary
convention for BOTH AAVE_V3 (line 106) and COMPOUND_V3 (line 177), so the fallback's `batch_compound_v3` is the drift.

**Pre-existing, not caused by the sports re-stamp**: confirmed byte-identical on clean LDR (CI runs 31636664383 @ 20:14
and 31632477709 @ 19:24 today fail on the same assertion; both predate the slot-32 commit). Recent DeFi lending-indices
work (`bd153821` "canonical venue", `d36e2498` id-form fix) is the likely origin.

## Why it matters

The `market-tick-data-service` quality gate is RED on `live-defi-rollout`, which blocks EVERY worker's Pass-1 →
quickmerge ship for that repo (the commit is the per-repo quality boundary) — slot 32's sports P2 `trades`→`odds`
re-stamp tool is written, committed, and dry-run-validated, but cannot land until this is green. It also blocks the
standing LDR→main promotion for MTDS.

## Recommended decision

Fix the fallback path's emitted `pipeline_mode` to the SSOT value `batch_onchain_subgraph`
(`pipeline_mode_for_source("onchain_subgraph", ...)`, the same resolution the primary path uses), or — if
`batch_compound_v3` is genuinely the canonical venue-specific mode for the fallback — update the test's assertion and
re-verify the pipeline-mode-partition SSOT contract. The AAVE_V3 assertion (line 106, `batch_onchain_subgraph`) and the
handler's own primary-path resolution favor the former.

- [x] ✅ [DATA] P0. Fix `market-tick-data-service` QG red: align the lending_indices COMPOUND_V3 fallback write path's
      emitted pipeline_mode with `pipeline_mode_for_source("onchain_subgraph", ...)` (`batch_onchain_subgraph`), or
      update the test assertion if the venue-specific token is SSOT- correct — resolve against
      `/codex/02-data/pipeline-mode-partition.md` and clear the MTDS QG red. — market-tick-data-service@6a039e5242:
      threaded the SSOT pipeline_mode through `_collect_protocol_chain` → `_write_protocol_chain_rows` →
      `write_defi_rows` (resolver `_resolve_lending_pipeline_mode` in `lending_indices_write.py`); full
      `quality-gates.sh` green (exit 0); quickmerge landed on LDR + ancestry verified on origin.

- [x] ✅ [DATA] P1. Convert the COMPOUND_V3 venue-only `_VENUE_OVERRIDES` entry
      (`unified-trading-library/unified_trading_library/pipeline_mode_resolver.py:135`) to a per-data_type
      `_VENUE_DT_OVERRIDES` entry (`oracle_prices` → `batch_compound_v3`), following the POLYMARKET multi-source-venue
      precedent — the venue-only entry shadows the `lending_indices` SSOT source (onchain_subgraph) for ANY derive-path
      caller (backfill / manifest-rebuild / future COMPOUND_V3 data_type). — unified-trading-library@b3b2c440e4: moved
      COMPOUND_V3 AND SPARK to `_VENUE_DT_OVERRIDES[(*, "oracle_prices")]` (SPARK had the identical latent drift — its
      lending venue "SPARK" matched its override key, mis-stamping spark lending_indices as batch_spark); AAVE retained
      as venue-only (lending venue AAVE_V3 ≠ "AAVE", single-source). UTL + MTDS QG green (exit 0), quickmerge landed on
      LDR + ancestry verified.
