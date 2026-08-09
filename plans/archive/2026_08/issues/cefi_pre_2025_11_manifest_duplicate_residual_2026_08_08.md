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
status: resolved
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
resolved_by: >-
  instruments-service@e7d070c3 (scoped pre-2025-11-01 dedup apply, POST-APPLY GATE GREEN). Own scope fully closed; the
  corpus-wide verify-PASS remainder is a separate, already-tracked population — see
  /plans/active/issues/cefi_chain_drop_v2_dedup_stop_on_surprise_198k_lossy_groups_2026_08_08.md.
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

- [x] [DATA] P2. ✅ **Characterize the pre-2025-11-01 manifest duplicate population** —
      market-tick-data-service@813de7f1. **Bounded and small**: 6,575 duplicate groups out of 4,850,391 effective-key
      groups (0.14%) across the whole pre-2025-11-01 cefi manifest slice (5,128,927 rows, 98.92% already-canonical).
      Overwhelmingly a stale `attempted_failed` wire-form placeholder coexisting with a `captured` canonical-form row
      for the same shard (not two competing real captures — see Progress Log for the full venue breakdown + sample
      evidence). See Progress Log entry below for evidence + method.
- [x] [DATA] P2. ✅ **Re-run the Surface-C dedup apply (or a scoped equivalent) for the pre-2025-11-01 range** —
      instruments-service@e7d070c3, deployment-service@149aca1a. **Pre-2025-11-01 population fully collapsed, verified
      two ways**: (1) the apply's own post-write gate re-scanned all 6 blobs and reported
      `POST-APPLY GATE     GREEN: 0 pre-cutoff duplicate groups remain`; (2) a direct manifest query post-apply for the
      exact two wire-forms `verify_cefi_canonical_4surface_2026_07_20.py` originally flagged (`ADAF0:USTF0`,
      `AVAX_USDC-PERPETUAL`) confirms every SURVIVING occurrence of either form is dated 2026-05-23 through 2026-07-26 —
      100% post-cutoff, zero pre-cutoff residual. Re-running the verify script still returns `OVERALL:     FAIL`
      (Surface B/C), but for a DIFFERENT reason than todo 2 targeted: a separate, already-tracked, out-of-scope
      post-cutoff population (dated well after 2025-11-01) accounts for 100% of the remaining duplicates on these two
      probes — see `/plans/active/issues/cefi_chain_drop_v2_dedup_stop_on_surprise_198k_lossy_groups_2026_08_08.md`
      (which this same session expanded to cover it). This todo's own scope (the pre-2025-11-01 range) is fully closed;
      a corpus-wide verify PASS depends on that separate issue's resolution, not on anything further here. See Progress
      Log for full evidence.

## Progress Log

- **2026-08-08** — Filed during the `cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md` resume, slot 18. The
  safe-residual applies, cron cycle, and loop-until-dry verifier all completed; this final re-proof step surfaced a
  genuinely separate, pre-existing gap. Archival deferred pending resolution.
- **2026-08-08 (slot 3)** — Characterized the pre-2025-11-01 duplicate population per todo 1. New READ-ONLY script
  `market-tick-data-service/scripts/characterize_cefi_pre_2025_11_manifest_duplicates_2026_08_08.py`
  (`market-tick-data-service@813de7f1`): single-walk load of the cefi manifest slice (`date < 2025-11-01`, one atomic
  GET, row-group filtered in Arrow), vectorized canonical/wire split, resolver run ONLY over the 375 UNIQUE
  non-canonical `(venue, itype, id, data_type, underlying)` tuples (not per-row), grouped on the SAME
  `_effective_dedup_key` shape as `complete_cefi_manifest_canonical_dedup_2026_07_17.py` (PIN_ATOM + bundle-underlying
  - chain) but keyed on the RESOLVED canonical id so a canonical spelling and a wire spelling of the same real shard
    collapse onto one key.

  **Result — bounded, small, mostly benign**: 5,128,927 pre-cutoff cefi manifest rows, 98.92% already-canonical.
  4,850,391 distinct effective-dedup-key groups; **6,575 (0.14%) are duplicates** (>1 distinct `instrument_id` form
  under one shard atom), touching 13,150 rows total. Breakdown by venue (groups / rows / captured-rows):

  | venue            | groups | rows  | captured_rows |
  | ---------------- | ------ | ----- | ------------- |
  | KRAKEN-SPOT      | 2,316  | 4,632 | 2,302         |
  | OKX-SWAP         | 1,651  | 3,302 | 1,599         |
  | BINANCE-FUTURES  | 942    | 1,884 | 864           |
  | OKX-SPOT         | 758    | 1,516 | 740           |
  | BITFINEX-SPOT    | 656    | 1,312 | 653           |
  | BITFINEX-FUTURES | 152    | 304   | 151           |
  | KRAKEN-FUTURES   | 55     | 110   | 5             |
  | BINANCE-SPOT     | 37     | 74    | 0             |
  | DERIBIT          | 8      | 16    | 0             |

  **Root-cause reading of the sample** (30 sampled groups, all 2020-01-02 KRAKEN-SPOT/OKX-SWAP): every sample is exactly
  2 rows — one `capture_status=captured` under the CANONICAL spelling (e.g. `KRAKEN-SPOT:SPOT_PAIR:ADA-USD`) and one
  `capture_status=attempted_failed` under the OLD WIRE spelling (e.g. `ADA/USD`, `BCH-USD-SWAP`) — a stale
  failed-attempt placeholder left under the pre-migration wire id that was never cleaned up once the canonical spelling
  successfully captured. This is corroborated by the per-venue `captured_rows`≈`groups` pattern for
  KRAKEN-SPOT/OKX-SWAP/BINANCE-FUTURES/OKX-SPOT/BITFINEX-SPOT/BITFINEX-FUTURES (≈1 captured row per 2-row group, not 2),
  and BINANCE-SPOT/DERIBIT/most of KRAKEN-FUTURES have **zero** captured rows in ANY of their duplicate groups (both
  forms are non-captured placeholders — no real data involved at all). **This is structurally DIFFERENT from Finding
  5/8's genuine two-real-captures collisions** in the parent doc — no sample here shows two `captured` rows with
  differing `row_count` (the actual data-loss-risk shape); cleanup of an `attempted_failed` row never discards real data
  by definition. Full per-tuple/per-group detail is in the script's own stdout (not persisted — re-run to regenerate;
  the script is READ-ONLY and cheap, ~35s wall-clock on this host).

  **Answers "bounded/small or a broader gap"**: bounded and small (0.14% of groups), and the dominant shape is safe to
  clean up. Feeds directly into todo 2 (scoped Surface-C dedup apply for this range) — that todo should confirm this
  characterization holds at `--apply` time and can likely treat the `captured`+`attempted_failed` pairs as the standard
  best-status-wins collapse `_dedup_blob` already implements, rather than needing new merge logic.

- **2026-08-08 (slot 3, continued)** — Started todo 2 by launching a fresh dry-run of the FULL
  `complete_cefi_manifest_canonical_dedup_v2_2026_07_20.py` (`canonical-migration-cefi-dedup-apply-20260808-233932`,
  drain not needed for dry mode). It correctly STOP-ON-SURPRISE'd on an UNRELATED, much larger population: 198,250
  chain-lossy groups (vs. the 28-group tolerance from 2026-07-24), dominated by ASTER/HYPERLIQUID/EXTENDED-STARKNET, ALL
  post-2025-11-01 — **zero mutation occurred**. Filed as its own big finding:
  `/plans/active/issues/cefi_chain_drop_v2_dedup_stop_on_surprise_198k_lossy_groups_2026_08_08.md`
  (`unified-trading-pm@61327a2d6`) — that population needs independent root-cause investigation and is explicitly OUT OF
  SCOPE for this todo. **Pivoted todo 2 to the "scoped equivalent" the todo text already allows**: wrote
  `instruments-service/scripts/apply_cefi_pre_2025_11_manifest_duplicate_residual_2026_08_08.py`, which reuses v1's
  resolver + `_dedup_blob`/`_snapshot`/`_load`/`_write` verbatim (same pattern as v2) but restricts the collapse to
  `date < 2025-11-01` rows only — the on/after-cutoff rows (including the entire ASTER/HYPERLIQUID/EXTENDED-STARKNET
  blocked population) are never loaded into the collapse pass at all, so this apply cannot touch that population.
  STOP-ON-SURPRISE bands sized to the todo-1 characterization (groups_duplicate ∈ [1000, 20000];
  multi_captured_lossy_groups MUST be 0 — todo-1's sample found zero of the shape that blew up post-cutoff). Next: run
  the scoped script's dry-run on a `cefi-dedup-apply`-category VM, verify bands hold, then a drained `--apply`, then
  re-run `verify_cefi_canonical_4surface_2026_07_20.py`.

- **2026-08-09 (slot 3)** — Shipped the scoped script (`instruments-service@87a5d72a`) + a new `cefi-dedup-apply-scoped`
  VM launcher category (`deployment-service@149aca1a`). Its own dry-run
  (`canonical-migration-cefi-dedup-apply-scoped-20260809-001849`) correctly STOP-ON-SURPRISE'd: `groups_duplicate`
  matched the characterization exactly (6,575, confirming the grouping logic reproduces todo 1), BUT the added safety
  check found the collapse pass was ALSO touching a second, much larger, unreviewed population — 98,188 groups with >=2
  CAPTURED rows sharing the IDENTICAL spelling but DIFFERING row_count (not a spelling variant at all — literal
  duplicate rows). This is the SAME shape as the post-cutoff ASTER/HYPERLIQUID/EXTENDED-STARKNET population, now
  confirmed pre-cutoff too — filed as a todo on
  `/plans/active/issues/cefi_chain_drop_v2_dedup_stop_on_surprise_198k_lossy_groups_2026_08_08.md`
  (`unified-trading-pm@<next-sha>`), out of scope for THIS todo. **Zero mutation occurred** (dry-run + the gate would
  have refused `--apply` too). Root cause of the scope leak: `_collapse_pre_cutoff` ran `v1._dedup_blob` over the WHOLE
  pre-cutoff dataframe rather than restricting it to the todo-1-characterized 6,575 spelling-variant groups
  specifically. Fixing now: scope the collapse to touch ONLY rows belonging to those 6,575 groups, leaving every other
  pre-cutoff row (including the newly-found 98,188-group population) completely untouched.

- **2026-08-09 (slot 3, closing)** — Shipped the fix (`instruments-service@e7d070c3`, updated
  `unified-trading-pm@088e59ce0` merges slot 14's concurrent Finding 11 root-cause into the sibling doc). Re-ran the
  scoped dry-run (`canonical-migration-cefi-dedup-apply-scoped-20260809-003610`): clean —
  `groups_duplicate=6575 rows_collapsed=6575 multi_captured_lossy_groups=0 drop_set_captured=0`, exit 0. Paused
  `uts-prod-manifest-consolidator-market-data-cefi-cron`, verified `PAUSED` via direct `gcloud scheduler jobs describe`,
  THEN launched the drained `--apply` on `e2-standard-16`
  (`canonical-migration-cefi-dedup-apply-scoped-20260809-004017`, matching Finding 7's precedent for the
  `--apply`-loads-full-schema OOM risk). Result: snapshotted all 6 blobs first
  (`_index/snapshots/pre_d4_20260809T004232Z/`), wrote all 6,
  `POST-APPLY GATE GREEN: 0 pre-cutoff duplicate groups remain`, exit 0, VM self-deleted. Resumed the cron, verified
  `ENABLED` via direct `gcloud scheduler jobs describe`. Re-ran `verify_cefi_canonical_4surface_2026_07_20.py`: still
  `OVERALL: FAIL` (Surface B/C) on the SAME two probes — investigated directly via a manifest query for the exact
  wire-forms (`ADAF0:USTF0`, `AVAX_USDC-PERPETUAL`): all 23 surviving rows are dated 2026-05-23 through 2026-07-26, 100%
  post-cutoff. This confirms the pre-2025-11-01 apply worked completely (nothing pre-cutoff survives for either
  instrument) and the verify script's continued FAIL is driven entirely by the separate, already-tracked post-cutoff
  population — not a gap in this todo's own work. Both todos done; this doc's remaining open item (a corpus-wide verify
  PASS) depends on `cefi_chain_drop_v2_dedup_stop_on_surprise_198k_lossy_groups_2026_08_08.md`'s resolution, tracked
  there.
