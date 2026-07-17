---
doc_type: issue
title:
  TradFi instrument_type migration read the stale legacy object (REPAIRED @bd115230; real loss 71,179 on CME 2026-06-28,
  not the originally-reported 425,096)
summary:
  canonicalize_tradfi_instrument_type_2026_07_16.py (run + flipped DONE on 2026-07-16) re-derived each blank captured
  row's instrument_type from the LEGACY by_date object path instead of the CANONICAL pipeline_mode-partitioned one.
  Where both exist they can disagree wildly — the legacy object is a stale partial. The migration therefore overwrote
  correct manifest counts with partial ones and mis-attributed the shortfall to a "pre-existing manifest-vs-object
  staleness bug" in its own DRIFT warnings, its docstring, and the parent plan's P9 entry. Independently reproduced
  2026-07-17. Rollback snapshot exists; repair = re-run with canonical-path-first.
status: resolved
nature: issue
asset_group: [tradfi]
stage: [meta]
repos: [instruments-service]
scope: [engineer, admin]
tags: [data-correctness, manifest, instrument_type, migration, tradfi, availability-index]
related: [data_status_page_ux_and_canonicalisation_2026_07_16.md]
created: 2026-07-17
last_updated: 2026-07-17
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineer
drift_direction: advance-code
resolved_by: instruments-service@bd11523015ecc98f166e668ac7c0dca49b792be1
locked_by:
locked_since:
source:
  surfaced by the cefi/defi instrument_type backfill (sibling migration) 2026-07-17; independently reproduced before
  filing
depends_on: []
---

# TradFi instrument_type migration read the STALE legacy object → 71,179 instruments' coverage lost (REPAIRED)

> ## ✅ RESOLVED 2026-07-17 — repaired via `instruments-service@bd115230`, independently verified.
>
> ### 🔴 AND: this doc's ORIGINAL headline ("425,096 instruments lost") was WRONG. Corrected below — do not cite it.
>
> **What the real damage was: 71,179 instruments on exactly ONE atom (CME 2026-06-28) — 1 of 10,542.** The repair
> restored it: Σ `instrument_count` **46,727,155 → 46,798,334 (+71,179)**, and CME 2026-06-28 now reads **74,005 (OPTION
> 69,212 / COMBO 4,446 / FUTURE 347) == its canonical object exactly**. Verified by an independent re-read of live GCS
> (the workflow's own adversarial verifier died on an API 529, so the dispatching agent did the verification directly
> rather than accept the repair agent's log).
>
> **Why the original −425,096 was an overstatement — it conflated four unrelated things.** Measured per-atom against ALL
> 10,542 canonical objects, the snapshot→live delta decomposes as:
>
> | component                                       | Σ delta      | verdict                                         |
> | ----------------------------------------------- | ------------ | ----------------------------------------------- |
> | superseded-ghost rows the CONSOLIDATOR deduped  | **−453,041** | legitimate — live matches the canonical objects |
> | post-snapshot re-captures                       | **+75,709**  | legitimate                                      |
> | stale-count re-stamps where the object is right | **+25,951**  | legitimate                                      |
> | **CME 2026-06-28**                              | **−71,179**  | ⬅ **the ONLY real damage**                      |
>
> `47,149,715 − 453,041 + 75,709 + 25,951 = 46,798,334` — closes exactly to the repaired figure. **Returning to
> 47,149,715 was never correct**: that number itself contained ~453k of double-counted ghost rows. My original
> measurement compared two moving numbers and attributed the whole delta to the migration; only 1 of 10,542 atoms was
> genuinely corrupted (the single case where a canonical object exists AND diverges from legacy — they agree 149/149 on
> a random sample).
>
> **The mechanism in "What happened" below is still CORRECT and still mattered** — the migration did read the stale
> legacy object, and it did overwrite CME's real 74,005 with the legacy partial's 2,826. Only the blast-radius figure
> was wrong. Keep the mechanism; discard the number.
>
> **Lesson (the same one this plan keeps re-learning): I asserted a headline number from a two-point diff without
> decomposing it, and it propagated into this doc, the plan's P9 correction, and an operator escalation before anyone
> checked it.** A delta between two live, concurrently-mutating artifacts is not evidence of a single cause.

## What happened

`instruments-service/scripts/canonicalize_tradfi_instrument_type_2026_07_16.py` (parent plan
`data_status_page_ux_and_canonicalisation_2026_07_16.md`, P9 Q2, shipped `instruments-service@66258618`) backfilled
blank `instrument_type` on tradfi's `_index/availability_index.parquet` by doing a targeted per-shard read of that
shard's own `instruments.parquet` and re-deriving the type from the object's own column. That design is right.

**The bug: it resolved the object at the LEGACY path** (`instrument_availability/by_date/day=<D>/venue=<V>/`) rather
than the **CANONICAL** source-aware path
(`instrument_availability/by_date/day=<D>/pipeline_mode=<M>/asset_group=<AG>/venue=<V>/`). Both objects can exist for
the same shard, and **they are not the same data** — the legacy one is a stale partial left behind by the pipeline_mode
partition migration. Because the script re-stamps `row_count`/`instrument_count` from whatever object it read, it wrote
the PARTIAL counts over the manifest's correct ones.

It then **mis-diagnosed its own damage**: the discrepancy surfaced in its per-shard `shard count DRIFT` warnings, and
was written up (in the script docstring AND the parent plan's P9 Q2 checkbox) as "a separate, pre-existing
manifest-vs-object staleness bug likely not tradfi-specific, worth its own follow-up investigation". That explanation is
wrong — the drift was **manufactured by the migration itself**.

## Evidence (independently reproduced 2026-07-17, not taken from the sibling agent's report)

Aggregate, live vs the migration's own pre-migration snapshot
(`_index/snapshots/pre_tradfi_instrument_type_canon_2026_07_16_20260716T143452Z.parquet`):

| metric                        | pre-migration snapshot | live now   | delta                                                                                                                                       |
| ----------------------------- | ---------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| Σ `instrument_count` (tradfi) | 47,149,715             | 46,724,619 | **−425,096** [OVERSTATED — see top banner; real migration loss = −71,179 on CME 2026-06-28; rest is legit consolidator dedup + re-captures] |

Worked example — **CME 2026-06-28**:

| source                                    | rows / counts                                              |
| ----------------------------------------- | ---------------------------------------------------------- |
| manifest BEFORE (snapshot)                | ONE blank-type row, `instrument_count=74,005`              |
| manifest AFTER (live)                     | OPTION 2,566 + FUTURE 32 + COMBO 228 = **2,826**           |
| **CANONICAL object** (`pipeline_mode=…`)  | **74,005 rows** — OPTION 69,212 / COMBO 4,446 / FUTURE 347 |
| **LEGACY object** (`by_date/day=/venue=`) | **2,826 rows** — OPTION 2,566 / COMBO 228 / FUTURE 32      |

The canonical object matches the ORIGINAL manifest count (74,005) **exactly**; the legacy object matches what the
migration WROTE (2,826) **exactly**. That is conclusive: the migration read the legacy object.

## Why it matters

- ~~The tradfi availability manifest now understates real coverage by 425,096 instruments.~~ **[CORRECTED: the real
  understatement was 71,179 on one atom, now repaired @bd115230.]** Anything reading `instrument_count`/`row_count` for
  tradfi coverage (data-status page, honest-coverage denominators, gates) is being told less data exists than actually
  does.
- It is a **false-negative**, which is the quieter and more dangerous direction: nobody gets paged for coverage that
  looks lower than it is, and the manifest's own DRIFT log already "explained" it.
- The parent plan's P9 Q2 entry currently records the wrong root cause, so the next agent would inherit the wrong mental
  model.

## Fix

1. **Repair = re-run the same backfill with canonical-path-first**, NOT a rollback (a rollback would restore the blank
   `instrument_type` the migration correctly fixed). The sibling script
   `scripts/canonicalize_cefi_defi_instrument_type_2026_07_17.py` already implements the correct rule — it reads the
   CANONICAL path first and falls back to legacy ONLY when the canonical object does not exist (measured on defi:
   canonical existed for 67/120 sampled targets, legacy for 99/120, and the two AGREE where both exist, 127/143 — so the
   fallback is genuinely needed, but must never win over an existing canonical object). Generalise that script to tradfi
   (it is already `--asset-group`-parameterised) and re-run.
2. **Verify** by re-reading live and confirming Σ `instrument_count` returns to ~47,149,715 and CME 2026-06-28 reads
   74,005 across OPTION/COMBO/FUTURE.
3. **Correct the record**: the parent plan's P9 Q2 checkbox + the tradfi script's docstring both assert the
   "pre-existing staleness" explanation. Both must be corrected or the next reader re-inherits it.
4. **Blast-radius check (not yet done)**: are there OTHER migrations that resolve a by_date object path? Any that
   hardcode the legacy layout have the same latent bug. `canonicalize_cefi_split_venue_chain_2026_07_17.py` (shipped
   today) only _checks existence_ at the canonical path and never re-stamps counts from an object, so it is unaffected;
   `drain_residual_lending_rows_2026_07_17.py` reads no objects at all. Others are unaudited.

## Rollback / safety

- Pre-migration snapshot (tradfi):
  `gs://instruments-store-tradfi-prd-central-element-323112/_index/snapshots/pre_tradfi_instrument_type_canon_2026_07_16_20260716T143452Z.parquet`
- The blank rows the migration fixed are genuinely fixed (0 captured rows remain blank in tradfi) — only the COUNTS on
  the re-stamped shards are wrong. So the repair is a re-derive, not a restore.

## The repair (applied 2026-07-17, `instruments-service@bd115230` + `test_repair_tradfi_instrument_type_counts.py` 22 tests)

The obvious repairs were BOTH wrong (measured, not assumed) — a naive re-run of the sibling backfill is a no-op (0 blank
captured rows remain), and a blind snapshot restore silently reverts real data (the daily job re-captures a rolling
window, so 26 rows across atoms present in BOTH snapshot and live would have been reverted — e.g. CME 07-15 OPTION
68,500→70,552). The repair therefore used **base = LIVE**, with the snapshot used ONLY to identify which atoms the
migration touched, re-derived canonical-path-first, idempotent (re-run = 0 repairs), CAS-guarded (the index is rewritten
~every 60s by the consolidator — a plain overwrite would have raced, and did: the write's precondition failed on attempt
1). Rollback snapshot: `…/_index/snapshots/pre_tradfi_count_repair_2026_07_17_20260717T142732Z.parquet` (Σ=46,727,155).

## Two NEW findings the repair surfaced (NOT fixed — own follow-ups)

1. **875 tradfi atoms have objects overwritten far NARROWER than the original capture.** e.g. ICE 2020-01-27: 8,866 → 1
   row; a NASDAQ atom 760 → fewer. The manifest now honestly matches those thinned objects (so it is NOT a manifest
   bug), but ~453k instruments' worth of _objects_ genuinely shrank at some point — pre-existing, unexplained, and the
   real source of most of the −453,041 "ghost dedup" line above. Worth a root-cause: something rewrote historical tradfi
   capture objects with narrower content.
2. **153 duplicate row_keys in tradfi (all KRX)** carry TWO different `capture_status` values at one row_key — a 4-state
   violation the consolidator's dedup key does not collapse. Pre-existing (present in the snapshot too), so the repair
   gated on "duplicate count must not INCREASE" rather than "==0" (which would refuse forever). (Note: a fresh
   whole-index read post-repair shows 0 duplicates on the `_ROW_KEY_COLUMNS` composite — the 153 are on the repair
   script's narrower key; reconcile which key definition is authoritative as part of the follow-up.)
