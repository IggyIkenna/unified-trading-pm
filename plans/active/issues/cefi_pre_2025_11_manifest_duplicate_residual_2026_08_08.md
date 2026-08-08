---
doc_type: issue
title:
  CeFi pre-2025-11-01-era manifest duplicate residual — Surface B/C FAIL on the final 4-surface re-proof (2026-08-08)
summary: >-
  Running `verify_cefi_canonical_4surface_2026_07_20.py` as the final done-state re-proof for
  `cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md`'s resume sequence produced OVERALL: FAIL [A=PASS
  B=FAIL C=FAIL D=PASS]. Both failures are duplicate manifest rows on 2025-06-15 — a date BEFORE the `cefi-late-renames`
  migration's 2025-11-01 scope start, meaning this is a distinct, older population the current safe-residual work never
  touched, not a regression from anything done this session.
status: open
nature: issue
asset_group: [cefi]
stage: [meta]
repos: [market-tick-data-service, instruments-service]
scope: [engineer]
tags: [cefi, manifest, duplicate, 4surface, data-correctness]
related:
  [
    /plans/active/issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md,
    /plans/active/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_finalize_2026_08_08.md,
    /plans/active/issues/cefi_lighter_zksync_systemic_collision_2026_08_08.md,
  ]
created: 2026-08-08
author: unknown
parent_epic: cefi_master
priority: P2
source: >-
  Discovered running the final 4-surface re-proof for cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md's
  resume sequence, slot 18, 2026-08-08.
resolved_by:
locked_by:
assigned_vm: planning
assigned_role: data_engineering
code_refs:
  [
    market-tick-data-service/scripts/verify_cefi_canonical_4surface_2026_07_20.py,
    market-tick-data-service/scripts/complete_cefi_manifest_canonical_dedup_v2_2026_07_20.py,
  ]
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
context_scope:
  [
    market-tick-data-service/scripts/verify_cefi_canonical_4surface_2026_07_20.py,
    /plans/active/issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md,
  ]
---

# CeFi pre-2025-11-01-era manifest duplicate residual

## What I found

Ran `python scripts/verify_cefi_canonical_4surface_2026_07_20.py` (read-only, sampled, no `--apply`) as the last step of
`cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md`'s resume sequence. Result:
`OVERALL: FAIL    [A=PASS  B=FAIL  C=FAIL  D=PASS]`.

- **Surface A (GCS filename)**: PASS on both probes, all 7 sampled days.
- **Surface B (parquet `instrument_id` column)**: FAIL on the DERIBIT AVAX-USDC probe, 2025-06-15 —
  `stem='DERIBIT:PERPETUAL:AVAX-USDC@LIN' column=['DERIBIT:PERPETUAL:AVAX_USDC-PERPETUAL']` (the on-disk object's column
  still carries the old wire-form id even though the filename is canonical). The same probe PASSES on 2026-05-01.
- **Surface C (manifest)**: FAIL on both probes — `BITFINEX-FUTURES:PERPETUAL:ADA-USDT@LIN` has a duplicate manifest
  form `ADAF0:USTF0` (20 rows) alongside 7,261 canonical rows; `DERIBIT:PERPETUAL:AVAX-USDC@LIN` has a duplicate form
  `AVAX_USDC-PERPETUAL` (3 rows) alongside 1,076 canonical rows.
- **Surface D (reader resolution)**: PASS on both probes.
- **Corpus-level canonical fractions** (informational, not pass/fail): FILENAME 95.36% (24,593/25,789 across 7 sampled
  days, low point 2025-12-15 at 72.30%), COLUMN 92.50% (37/40 sampled objects), MANIFEST 98.64% (10,076,885/10,215,872
  rows).

**Both concrete failures are on 2025-06-15** — a date well BEFORE the `cefi-late-renames` migration's declared scope
start (2025-11-01, per that script's own usage examples and the parent doc's Finding 4/8). Per the verification script's
own docstring, days before ~2025-11-01 were expected to ALREADY be canonical from an earlier program; this shows that
expectation doesn't fully hold — there's a residual duplicate population from that earlier era that neither this
session's work nor the in-scope `cefi-late-renames` migration ever touched (it's a filename-rename tool; the duplicates
here are manifest-row-level, from the earlier `complete_cefi_manifest_ canonical_dedup` v1/v2 program's own coverage,
not from anything in the 2025-11-01+ LATE window).

## Why it matters

This blocks the parent todo's final step (archive `cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md` + its
parent `cefi_consolidated_closeout_2026_07_18.md`), which is explicitly gated on this re-proof PASSING. It also means
the corpus-level "done" claim for the broader CeFi canonical program isn't accurate yet — genuine duplicate manifest
rows and stale parquet columns remain from an era predating this session's scope.

## Recommended decision

1. Determine whether this is a small, bounded residual (a handful of specific instrument/day combinations, similar in
   shape to the Surface-C dedup program's own tolerated residuals — Finding 5's BITFINEX-SPOT/BYBIT-SPOT population) or
   a broader gap in pre-2025-11-01 coverage.
2. Re-run (or extend) `complete_cefi_manifest_canonical_dedup_v2_2026_07_20.py` (the Surface-C dedup apply script,
   already proven safe on `e2-standard-16` per the parent doc's Finding 7) scoped to the pre-2025-11-01 date range, OR
   determine the specific root cause if these 2 probes are representative of a wider pattern.
3. Once resolved, re-run `verify_cefi_canonical_4surface_2026_07_20.py` to confirm PASS before any archival proceeds.

## Todos

- [ ] [DATA] P2. **Characterize the pre-2025-11-01 manifest duplicate population** — sample additional instrument/day
      pairs before 2025-11-01 (beyond the 2 probes here) to determine if this is bounded/small or a broader gap; report
      counts by venue similar to the parent doc's own collision breakdowns. Read-only, do NOT apply/delete/merge
      anything. (repo: market-tick-data-service)
- [ ] [DATA] P2. **Re-run the Surface-C dedup apply (or a scoped equivalent) for the pre-2025-11-01 range** once
      characterized, then re-run `verify_cefi_canonical_4surface_2026_07_20.py` to confirm PASS. (repo:
      market-tick-data-service, deployment-service)

## Progress Log

- **2026-08-08** — Filed during the `cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md` resume, slot 18. The
  safe-residual applies, cron cycle, and loop-until-dry verifier all completed; this final re-proof step surfaced a
  genuinely separate, pre-existing gap. Archival deferred pending resolution.
- **2026-08-08 (slot 9, characterization todo 1 in progress)**: ran a bounded, single-read, memory-capped scan of the
  cefi manifest (`_index/availability_index.parquet`, one GET, row-group-filtered in Arrow to `asset_group='cefi' AND
  date < '2025-11-01'` before any Python materialization — same single-walk pattern as
  `verify_cefi_canonical_4surface_2026_07_20.py`'s own `load_manifest_cefi`; script kept at
  `scratchpad/characterize_pre_2025_11_residual.py`, not yet promoted since it's a read-only investigation aid, not a
  reusable tool an open todo will re-run repeatedly).
  **STEP 1 result (complete, full pre-2025-11-01 slice, not a sample)**: 5,130,946 pre-2025-11-01 cefi manifest rows
  total; 5,059,930 after excluding chain-bundle itypes (same exclusion `verify_cefi_canonical_4surface` uses for its
  corpus fractions); **5,031,110 canonical-form (99.43%), 28,820 non-canonical-form (0.57%)** — i.e. this residual is
  bounded, not a broad gap (in the same shape/order-of-magnitude as Finding 5's tolerated Surface-C residuals in the
  parent doc, though a larger absolute count). Non-canonical rows by venue: BYBIT 7,857, DERIBIT 7,026, OKX-SWAP 4,176,
  KRAKEN-SPOT 2,316, OKX-FUTURES 2,086, BINANCE-FUTURES 2,010, KRAKEN-FUTURES 1,489, OKX-SPOT 890, BITFINEX-SPOT 656,
  BITFINEX-FUTURES 156 (consistent with the 2 probes' own duplicate counts: 20+3 rows across the 2 specific probe
  instruments), LIGHTER-ZKSYNC 114, BINANCE-SPOT 37, ASTER 7.
  STEP 2 (resolve each non-canonical row via the production resolver, check whether a canonical-form sibling for the
  same resolved id already exists in this slice — i.e. distinguish a genuine "duplicate form alongside canonical" from
  an orphan pre-migration id with no canonical counterpart here) crashed on a data anomaly the first pass didn't guard
  for: some pre-2025-11-01 rows carry a NULL `instrument_type` (the resolver's `_resolve_itype` assumes non-null) —
  fixed the script to skip+count those rows rather than crash, re-running now. Todo 1 stays open pending STEP 2's
  venue-level genuine-duplicate breakdown (the number that actually determines todo 2's fix scope).
