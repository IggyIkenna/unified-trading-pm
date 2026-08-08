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

- [x] [DATA] P2. ✅ **Characterize the pre-2025-11-01 manifest duplicate population** —
      market-tick-data-service@813de7f1. **Bounded and small**: 6,575 duplicate groups out of 4,850,391 effective-key
      groups (0.14%) across the whole pre-2025-11-01 cefi manifest slice (5,128,927 rows, 98.92% already-canonical).
      Overwhelmingly a stale `attempted_failed` wire-form placeholder coexisting with a `captured` canonical-form row
      for the same shard (not two competing real captures — see Progress Log for the full venue breakdown + sample
      evidence). See Progress Log entry below for evidence + method.
- [ ] [DATA] P2. **Re-run the Surface-C dedup apply (or a scoped equivalent) for the pre-2025-11-01 range** once
      characterized, then re-run `verify_cefi_canonical_4surface_2026_07_20.py` to confirm PASS. (repo:
      market-tick-data-service, deployment-service)

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
