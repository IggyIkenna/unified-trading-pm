---
doc_type: issue
title: CeFi E6 CF-7 relabel candidates + attempted_failed re-measure — the 50%/1.33M figure is STALE
summary: >-
  Live read of the cefi availability_index (9,138,791 rows, 2026-07-26) re-measures the historically-cited "~50%
  attempted_failed (1.33M)" figure as STALE: current measurement is 11.61% (1,060,613 rows) — the denominator has grown
  ~3.5x (2.64M -> 9.14M) since that figure was recorded while the numerator dropped modestly. Root-cause breakdown of
  the CURRENT 1,060,613 attempted_failed rows shows they are >90% already attributed to the open, P0-tracked Tardis
  concurrent-IP-lock 403 storm and its DERIBIT options_chain/ futures_chain backlog (no new mechanism found). COINBASE
  bare-venue relabel candidates = 0 (already fully canonical). One genuinely new, small, untracked finding: 9,750
  `captured` rows with a blank `data_type` string, all `market-tick-data-service`, spanning 2019-2026. Diagnose-only —
  no relabel/reclassify --apply executed.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer]
tags: [cefi, attempted-failed, data-correctness, relabel, tardis, deribit, diagnostic]
related:
  [
    /plans/active/issues/cefi_high_attempted_failed_batch_cluster_2026_07_23.md,
    /plans/archive/issues/tardis_concurrent_ip_lockout_2026_07_12.md,
    /plans/active/issues/deribit_options_chain_af_g4_blocker_2026_07_03.md,
    /plans/archive/2026_07/cefi_satellite_ao_dispatch_batch2_2026_07_26.md,
    /plans/active/data_completion_cefi_2026_07_15.md,
  ]
created: 2026-07-26
parent_epic: cefi_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: research
drift_direction: advance-code
depends_on: []
source:
  [
    "cefi_satellite_ao_dispatch_batch2_2026_07_26.md E6 CF-7 diagnostic todo, sourced from
    data_completion_cefi_2026_07_15.md's bare 'E6 CF-7 relabel... 50% attempted_failed (1.33M)' line item.",
  ]
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
---

# CeFi E6 CF-7 relabel candidates + attempted_failed re-measure

## What I found

**Method**: `gcloud storage cp gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`
to local scratch (9,138,791 rows), then `pandas` analysis. One read of the already-materialised index — no new GCS
corpus walk, no write, no relabel/reclassify `--apply`.

### (1) The "~50% attempted_failed (1.33M)" figure — RETIRE AS STALE

|                         |                                                   historically cited | measured 2026-07-26 |
| ----------------------- | -------------------------------------------------------------------: | ------------------: |
| total rows              | ~2,640,864 (cited elsewhere in `data_completion_cefi_2026_07_15.md`) |           9,138,791 |
| `attempted_failed` rows |                                                           ~1,330,000 |           1,060,613 |
| `attempted_failed` %    |                                                                 ~50% |          **11.61%** |

The denominator has grown ~3.5x (more `captured`/`empty_confirmed`/`expected_unattempted` rows landed) while the
numerator dropped modestly — the "~50%" framing is stale and should not be repeated; use 11.61% / 1,060,613 going
forward.

### (2) Root cause of the CURRENT 1,060,613 `attempted_failed` rows — already attributed, not a new mechanism

`error_reason` breakdown: `UNCLASSIFIED:Tardis HTTP 403` (562,997) + `Tardis HTTP 403` (224,508) +
`code=274 concurrent-IP-lock` (10,222) = **797,727 (75.2%)** — the Tardis-403 family. `VENUE_FETCH_FAILED` (normalized
leaked-text label) = 219,071 (20.7%). Remainder (~4%) is small tails (400/500/503, CSV-decode, timeouts, `expiry_date`
writer-validation).

By venue: **DERIBIT = 580,174 (54.7% of ALL cefi attempted_failed)**, spread near-evenly across
book_snapshot_5/trades/derivative_ticker/options_chain/futures_chain (~112-124K each) — i.e. a systemic per-day DERIBIT
gap, not one data_type. `options_chain`/`futures_chain` DERIBIT counts (113,615 / 112,728 today) match
`cefi_high_attempted_failed_batch_cluster_2026_07_23.md`'s numbers almost exactly (that doc's 2026-07-23 read: 113,593 /
112,600-113,587-ish) — **same population, already root-caused there and in
`tardis_concurrent_ip_lockout_2026_07_12.md`** (shared academic Tardis key, 1-concurrent-IP cap; historical poisoned
rows from before the cap-1 fix never retried). By year, roughly evenly spread 2020-2026 (93K-186K/year) — a
long-accumulated backlog, not a recent regression. **No new root cause found here — this confirms, does not extend, the
already-open P0 tracking.**

### (3) COINBASE relabel candidates — ZERO, already fully canonical

`venue == "COINBASE"` (bare): **0 rows**. `venue == "COINBASE-SPOT"`: 112,758 rows (correct canonical form).
`COINBASE-FUTURES` (124,941) and `COINBASE-CDE` (11,845) also already canonical. The original E6 CF-7 todo's
"COINBASE↔COINBASE-SPOT mismatch" premise does not currently exist in the live index — no relabel needed.

### (4) Blank-venue rows — 6, negligible

`venue` blank/NA: 6 rows total, all `capture_status=captured`, one row each across 6 different data_types. Not worth a
dedicated relabel pass at this volume.

### (5) Blank-`data_type` rows — 9,750, a genuinely NEW, untracked finding

`data_type == ""`: 9,750 rows. ALL `capture_status=captured` (real data, not a failure state), ALL
`service_name=market-tick-data-service`, spread across 2019-2026 (not a single incident window — 38 in 2019 up to 3,178
in 2024). Venue breakdown: BYBIT 1,772 / BINANCE-FUTURES 1,763 / OKX-SWAP 1,740 / UPBIT 1,352 / HYPERLIQUID 687 /
DERIBIT 669 / BINANCE-SPOT 627 / COINBASE-SPOT 381 / OKX-SPOT 378 / OKX-FUTURES 374 / OKX 7. No existing open issue doc
found tracking this specific population (grepped `plans/active/` for "blank data_type" and the exact row count — no
hit). Root cause not investigated in this pass (out of scope for a diagnose-only todo) — plausibly a writer path that
stamps `capture_status` before `data_type` resolution, or a schema/consolidation artifact for rows written before a
data_type column was populated consistently.

## Why it matters

The stale 50%/1.33M figure, if left uncorrected, would keep getting cited as evidence of a large ongoing correctness
problem when the real current number (11.61%) is both smaller and already ~95% attributed to already-open,
already-P0-tracked work (Tardis 403 + DERIBIT backlog). The one genuinely new item (9,750 blank `data_type` captured
rows) is real but small and not urgent.

## Recommended decision

- [x] [DOCS] P3. **[already covered by plans/active/cefi_satellite_ao_dispatch_batch3_2026_07_26.md, see that doc for
      execution]** Update `data_completion_cefi_2026_07_15.md`'s bare E6 CF-7 line item to strike the stale "~50%
      (1.33M)" figure and point at this doc for the current 11.61%/1,060,613 measurement + attribution.
- [ ] [DATA] P3. **RULED 2026-07-28 (operator gate-cleanup pass) — retagged from the "either/or" open framing, no longer
      a cross-tranche operator-decision-gated conflict with
      `instruments_mtds_consistency_remediation_residuals_2026_07_24.md:449`.** The apparent conflict dissolves once the
      two populations are read precisely: this doc's 9,750-row venue breakdown is overwhelmingly (9,743 rows) ALREADY
      market-type-suffixed venues (BYBIT/BINANCE-FUTURES/OKX-SWAP/UPBIT/HYPERLIQUID/DERIBIT/BINANCE-SPOT/
      COINBASE-SPOT/OKX-SPOT/OKX-FUTURES) — only `data_type` is blank, `venue` is unambiguous. The remaining **7 rows
      (bare `OKX`×7)** are the population needing reclassification. **CORRECTION (2026-07-30, spot-check per
      `ao_non_dispatchable_regex_swallows_resolved_retags_2026_07_29.md`'s audit todo)**: the original 2026-07-28 note
      claimed a "14-row (bare `OKX`×7 + bare `COINBASE`×7)" population, treating it as "the SAME 14-row population" as
      the cross-cutting doc's `_index` COINBASE(7)+OKX(7) line — this is factually wrong. Section (3) of THIS doc's own
      measurement (above) found `venue == "COINBASE"` (bare) = **0 rows** across the full live index, and the venue
      breakdown in section (5) confirms no bare-COINBASE rows exist within the 9,750-row population either (it sums to
      9,750 using only `COINBASE-SPOT` (suffixed, 381 rows) + bare `OKX` (7 rows) — no bare-COINBASE line item). The
      cross-cutting doc's COINBASE(7)+OKX(7) figure is a DIFFERENT, older measurement
      (`audit_index_vs_gcs_spellings.py`, 2026-06-18 spelling-mismatch pass over captured-cell spellings, not this doc's
      2026-07-26 blank-`data_type` scan) and should NOT be assumed to describe the same rows without a fresh join —
      re-verify before treating that doc's figure as satisfied by this one. Applying the operator's general theme (full
      completions/backfills where determinable, no shortcuts; never fabricate a value when honest-absence/reclassify is
      the correct disposition) split the disposition instead of picking one: **(a) 9,743 rows — BACKFILL** the
      `data_type` per row: root-cause the writer path that stamps `capture_status=captured` before `data_type`
      resolution, join each row back to its actual captured GCS object's `data_type=` path segment, and correct the
      manifest field — this is mechanically determinable (venue is unambiguous) and gets a full backfill, not a
      diagnose-only close, per the "no partial completion" mandate; cost is not a blocker (a manifest-field correction,
      no new paid infra). **(b) 7 rows (bare `OKX`) — RECLASSIFY**: do NOT fabricate a guessed venue-suffix/`data_type`
      for these — the real per-market data is already correctly captured under the suffixed venues elsewhere, so the
      bare-venue row is a malformed/duplicate manifest artifact, not a genuine gap; guessing here would violate the
      workspace's honest-absence/no-fabricated- placeholder rule. Whoever executes (b) should separately confirm whether
      `instruments_mtds_consistency_remediation_residuals_2026_07_24.md:449`'s COINBASE(7)+OKX(7) figure is satisfied by
      this OKX×7 reclassify or needs its own independent handling — do not assume it is closed by this todo alone.
      **Done when**: the 9,743-row backfill lands with a re-measured manifest showing blank-`data_type` `captured` rows
      for those resolved-venue populations at 0, the 7-row bare-`OKX` subset is reclassified (marked
      malformed/superseded, not backfilled), the cross-cutting doc's own COINBASE(7)/OKX(7) figure is independently
      re-verified (not assumed satisfied), and both source docs' checkboxes are flipped with the commit(s) cited.

## Progress Log

- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): RECLASSIFY candidate PARKED on conflict-check:
  `cefi_instruments_store_blank_data_type_residual_2026_07_29.md` (active, planning) claims the adjacent
  blank-`data_type` remediation and `manifest_reprocessing_generic_utility_2026_07_07.md` already registers a
  blank-data_type backfill script. Needs an operator call on which doc owns which bucket's population before dispatch.
  Filed as BLOCKED-OPERATOR-DECISION in this run's Deferred list; `assigned_vm` unchanged.
- **✅ OWNERSHIP RESOLVED 2026-07-31** (corpus-wide ownership-conflict sweep; the operator call the entry above was
  waiting on). All three docs read; the split is by **BUCKET**, and it is clean — the two active docs were never
  measuring the same rows:

  | Doc                                                                                  | Bucket / population it OWNS                                                                                                                                                                                                            |
  | ------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
  | **THIS doc**                                                                         | `market-data-tick-cefi-prd-central-element-323112` (MTDS tick manifest) — the **9,750**-row blank-`data_type` population: 9,743 BACKFILL + 7 bare-`OKX` RECLASSIFY                                                                     |
  | `/plans/active/issues/cefi_instruments_store_blank_data_type_residual_2026_07_29.md` | `instruments-store-cefi-prd-central-element-323112` (IS instruments manifest) — the **1** `captured`+blank row (BITFINEX-SPOT, 2023-12-16); its 5,806 non-captured blanks are already closed by evidence as correct universal behavior |
  | `/plans/archive/issues/manifest_reprocessing_generic_utility_2026_07_07.md`          | **Not an owner — shared TOOLING**, and already resolved/archived (4/4 done). It shipped the instruments-service `--operation reprocess-shards` CLI; reuse it, do not re-register a competing one-off script.                           |

  Neither active doc's population overlaps the other's, so both stay open and independently dispatchable — the only
  thing that was ever wrong here was the missing cross-reference, now added in both directions. The genuinely-unresolved
  cross-doc question is unchanged and stays in this doc's todo: the cross-cutting doc's older COINBASE(7)+OKX(7) figure
  is a **different 2026-06-18 measurement** and must be independently re-verified, not assumed satisfied by this one.
