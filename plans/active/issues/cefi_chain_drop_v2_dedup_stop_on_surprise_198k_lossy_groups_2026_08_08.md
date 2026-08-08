---
doc_type: issue
title:
  CeFi Surface-C v2 dedup apply STOP-ON-SURPRISE — 198,250 chain-lossy groups (vs. tolerated 28), likely an active
  duplicate-manifest-row writer bug, not a chain-collision
summary: >-
  A fresh dry-run of `complete_cefi_manifest_canonical_dedup_v2_2026_07_20.py` (launched to close a small,
  pre-2025-11-01 residual-duplicate todo) correctly STOP-ON-SURPRISE'd: 198,250 PIN_ATOM-key groups now hold >1 CAPTURED
  row with DIFFERING row_count, vs. the 28-group tolerance measured/tolerated on 2026-07-24 (Finding 5/7 in the parent
  doc). `n_multichain_rows=0` (chain itself is NOT the differentiator), so this is NOT the known chain-collision shape
  the tolerance was written for — it looks like a much larger, probably-still-ACTIVE population of duplicate manifest
  rows under the same shard atom (same date/venue/data_type/instrument_type/pipeline_mode) with different row_counts,
  dominated by ASTER (1,166,689 rows in the dump), HYPERLIQUID (58,945), EXTENDED-STARKNET (4,423), plus smaller counts
  on COINBASE-FUTURES/BITFINEX-FUTURES/DERIBIT, spanning dates from 2024-01-01 through 2026-08-03 (today). This BLOCKS
  `--apply` of the v2 script (the correct, safe outcome — zero mutation occurred) and therefore also blocks
  `issues/cefi_pre_2025_11_manifest_duplicate_residual_2026_08_08.md` todo 2's original plan of "just re-run v2 apply";
  that todo is being closed via a narrower scoped equivalent that does not touch this population instead (see that doc's
  Progress Log).
status: open
nature: issue
asset_group: [cefi]
stage: [meta]
repos: [market-tick-data-service, instruments-service]
scope: [engineer]
tags: [cefi, manifest, duplicate, dedup, chain-drop, data-correctness, stop-on-surprise, big-finding]
related:
  [
    /plans/active/issues/cefi_pre_2025_11_manifest_duplicate_residual_2026_08_08.md,
    /plans/active/issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-08-08
author: unknown
parent_epic: cefi_master
priority: P1
source: >-
  Discovered while working plans/active/issues/cefi_pre_2025_11_manifest_duplicate_residual_2026_08_08.md todo 2, slot
  3, 2026-08-08 — a routine re-run of the already-proven-safe `complete_cefi_manifest_canonical_dedup_v2_2026_07_20.py`
  dry-run (`canonical-migration-cefi-dedup-apply-20260808-233932`, e2-standard-8, asia-northeast1-c) refused to proceed.
resolved_by:
locked_by:
assigned_vm: planning
assigned_role: data_engineering
code_refs:
  [
    instruments-service/scripts/complete_cefi_manifest_canonical_dedup_v2_2026_07_20.py,
    instruments-service/scripts/complete_cefi_manifest_canonical_dedup_2026_07_17.py,
  ]
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
context_scope:
  [
    instruments-service/scripts/complete_cefi_manifest_canonical_dedup_v2_2026_07_20.py,
    /plans/active/issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md,
  ]
---

# CeFi Surface-C v2 dedup apply STOP-ON-SURPRISE — 198,250 chain-lossy groups

## What I found

Launched `canonical-migration-cefi-dedup-apply-20260808-233932` (`cefi-dedup-apply` category, `e2-standard-8`,
`asia-northeast1-c`, DRY mode) as the first step of resolving
`issues/cefi_pre_2025_11_manifest_duplicate_residual_2026_08_08.md` todo 2 ("re-run the Surface-C dedup apply ... for
the pre-2025-11-01 range"). Consolidator cron (`uts-prod-manifest-consolidator-market-data-cefi-cron`) was ENABLED at
launch time (dry-run needs no drain — matches the script's own docstring, drain is only required for `full`/`--apply`).

The dry-run loaded 7 blobs (main index + 6 per-VM shards), ran cleanly through the v1 canonicalize pass and the v2
marker/venue-axis transforms (`marker_added=55956[cap=1422]`, `okx_opt=190`, `combo=0` — all within normal-looking
ranges), then hit the CHAIN-DROP safety check and refused:

```
[v2 CHAIN-DROP=True] rows merging on chain-differing PIN_ATOM groups=0  LOSSY(captured w/ differing count)=198250 [MUST be 0]
STOP (DATA LOSS): 198250 PIN_ATOM group(s) hold >1 CAPTURED row with DIFFERING non-zero row_count after the
underlying+chain key-fold — beyond the known _CHAIN_LOSSY_TOLERANCE_MAX=50 tolerance (the 2026-07-24 measured
BYBIT-SPOT residual was 2 groups); this is a DIFFERENT/unreviewed population — diagnose before --apply, do not just
raise the tolerance.
Diagnose before --apply.
command exited rc=1
```

**Zero mutation occurred** — the script's own dry-run-first design correctly refused before any snapshot/write. Full
log:
`gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-cefi-dedup-apply-20260808-233932/run.log`.

### This is very likely NOT a chain-collision, despite the check's name

`_chain_merge_safety()` reports `n_multichain_rows=0` alongside `n_lossy=198250` — meaning within every affected
PIN_ATOM-key group, `chain` is constant (a single value). The "lossy" count is really: **>1 CAPTURED row exists for the
exact same (date, venue, data_type, instrument_type, pipeline_mode[, underlying]) shard atom, with DIFFERENT `row_count`
values** — i.e. genuine duplicate manifest rows for one shard, unrelated to the chain-drop the check was built to guard.
Sample (`BITFINEX-FUTURES:PERPETUAL:AAVE-USDT@LIN` trades, `2026-07-24`): 8 distinct captured rows for the ONE shard
with `row_count` = 3146, 787, 158, 53, 14, 9, 4, 1 — looks like successive partial/incremental writes that were each
appended as a NEW row instead of updating/superseding the existing one for that shard.

### Venue / date breakdown (from the dump)

| venue             | rows (dump) | date range observed           |
| ----------------- | ----------- | ----------------------------- |
| ASTER             | 1,166,689   | 2024-01-01 .. 2026-05-27      |
| HYPERLIQUID       | 58,945      | 2025-05-28 .. 2026-08-01      |
| EXTENDED-STARKNET | 4,423       | 2026-07-07 .. 2026-08-02      |
| COINBASE-FUTURES  | 1,071       | (not individually sampled)    |
| BITFINEX-FUTURES  | 8           | 2026-07-24                    |
| DERIBIT           | 4           | 2026-07-13 (volatility_index) |

(198,250 is the GROUP count from the script's own gate; the row counts above are DETAIL-TABLE rows, i.e. every
individual captured row inside an affected group — several rows per group for the heavy venues.)

**ASTER's date range (2024-01-01 start) is notable**: ASTER is a recently-onboarded venue (heavy per-VM backfill shards
observed active THIS week — `cefi-queue-heavy-binancefutu-x17-20260808-*`, `cefi-fwd-20260808-*` — in the same dry-run's
blob list), yet duplicate rows appear as far back as 2024-01-01, well before any plausible real launch/ backfill-start
date for the venue. That combination (recent onboarding + duplicates on 2+-year-old dates) plus the 2026-03 through
2026-08 (today) density elsewhere suggests this may be an ACTIVE, ONGOING writer/backfill behavior (each write appending
a new row per shard atom instead of updating one), not a one-time historical artifact — i.e. this population may still
be GROWING right now, not a fixed backlog.

## Why it matters

- Blocks `--apply` of the already-proven-safe v2 canonicalization script fleet-wide (it can't distinguish "the small
  known-safe 28-group residual" from this new 198,250-group population — the gate is corpus-wide, not per-population).
- If the writer-append-instead-of-update hypothesis is correct, this is an ACTIVE data-correctness bug inflating the
  cefi manifest with duplicate rows continuously, not a historical residual — every future dry-run of this script (or
  any other tool relying on "one row per shard atom") will keep finding a GROWING population until the root cause is
  fixed at the writer/consolidator, not just cleaned up after the fact.
- `_dedup_blob`'s row_count-desc tie-break (keep the largest) may be the WRONG resolution strategy here if some of these
  groups are genuinely two DIFFERENT real captures rather than one canonical capture plus stale partial writes — needs a
  scoped sample-and-classify pass (mirroring `characterize_cefi_pre_2025_11_manifest_duplicates_2026_08_08.py`'s
  approach) before any bulk `--apply`, not a blind "raise the tolerance."

### Corroborating precedent already in the codebase

`complete_cefi_manifest_canonical_dedup_2026_07_17.py`'s own `_effective_dedup_key()` docstring documents the EXACT
failure shape at small scale, found 2026-07-24: "64 residual lossy PIN_ATOM groups were ASTER rows with TWO captured
rows sharing an identical PIN_ATOM but DIFFERENT `chain` (blank vs. `"ASTER"`) and DIFFERING real `row_count` — almost
certainly a writer chain-tagging transition (blank before, `"ASTER"` after) that produced a second manifest row instead
of updating the first, rather than two spellings of the same capture." This is precisely the mechanism hypothesized
above, just 3-4 orders of magnitude smaller than what this dry-run now measures (64 → ~1.17M ASTER rows alone). If the
writer-tagging transition never fully completed (or keeps re-triggering), the population would keep growing exactly as
observed — supports treating this as ACTIVE, not historical.

## Recommended decision

1. Scoped, READ-ONLY characterization of this population (ASTER / HYPERLIQUID / EXTENDED-STARKNET first, they're ~98% of
   the volume): for a sample of affected shard atoms, pull the underlying per-VM shard write history (which VM/run wrote
   each row_count value, at what timestamp) to determine writer-append-vs-update behavior directly, rather than
   inferring from row_count magnitudes alone.
2. If confirmed a writer/consolidator append bug: root-cause + fix at the writer/consolidator (the actual data-safety
   fix), THEN clean up the accumulated duplicate rows (the v2 script, or a purpose-built collapse, once the shape is
   confirmed safe).
3. If NOT a writer bug (i.e. some groups really are 2 distinct real captures): the `_dedup_blob` collapse strategy needs
   a per-population review before this volume can be swept in bulk — do not raise `_CHAIN_LOSSY_TOLERANCE_MAX` to
   unblock without that review; the script's own comment explicitly warns against this.
4. Until resolved, any consumer of the cefi manifest that assumes "1 row per shard atom" (dashboards, gates,
   `capture_status` rollups) should be treated as reading a manifest with a KNOWN, currently-uncharacterized
   duplicate-row population for these venues — flag downstream if this surfaces as a visible discrepancy.

## Todos

- [ ] [DATA] P1. **Root-cause whether ASTER/HYPERLIQUID/EXTENDED-STARKNET manifest writes are appending a NEW row per
      write instead of updating the existing shard-atom row** — pull per-VM shard write history for a sample of the
      affected shard atoms (start with the `BITFINEX-FUTURES:PERPETUAL:AAVE-USDT@LIN` / `2026-07-24` sample above, 8
      rows for one shard) and confirm/refute against the writer code path (`record_captured` / `ManifestWriter` in
      market-tick-data-service). (repo: market-tick-data-service)
- [ ] [DATA] P1. **Once root-caused, fix the writer/consolidator if confirmed appending, THEN re-run the v2 dry-run** to
      confirm the chain-lossy count drops back toward the historical ~28-group baseline before any `--apply` is
      attempted again. (repo: instruments-service, market-tick-data-service)

## Progress Log

- **2026-08-08 (slot 3)** — Filed while working `issues/cefi_pre_2025_11_manifest_duplicate_residual_2026_08_08.md`
  todo 2. Dry-run evidence + venue/date breakdown above; zero mutation occurred (STOP-ON-SURPRISE fired before any
  snapshot/write). VM self-terminated (`VM_SHUTDOWN_ON_COMPLETION`) after failing exit_code=1.
