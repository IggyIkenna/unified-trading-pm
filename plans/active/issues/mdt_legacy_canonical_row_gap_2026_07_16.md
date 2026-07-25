---
doc_type: issue
title:
  MDT legacy↔canonical row gap (OR-5b) — the deficit is REAL and GENUINE (the OR-1 trap does NOT reproduce); three
  strictly-nested capture generations G3 ⊂ G2 ⊂ G1 mean the 3,816 "non-derivable" objects are the master superset and
  recovering them alone recovers 99.98% of the 6.37M-row pre-match gap
summary:
  'Read-only investigation of OR-5b on `market-data-tick-sports`, commissioned by operator ruling 2026-07-16 ("OR-5b(b):
  investigate first, like OR-1" + "OR-5b(a): derive from content, else park"). **The OR-1 precedent does NOT reproduce —
  the naive read is RIGHT this time.** NET row balance over all 108,966 crc-differing pairs: legacy 23,677,195 vs
  canonical 16,955,323 = **canonical is NET POORER by 6,721,872 rows**, losing 20 rows for every 1 it gains (OR-1 was
  +27,764 NET, gaining 15:1). Exact pass over all 45,701 unique pairs (91,402 full reads, 0 errors) decomposes the
  7,079,850: **6,372,806 (89.5%) are GENUINE pre-match bookmaker quotes canonical never captured** — distinct `(event,
  market, outcome, bm_time, price)` ticks, **0 price disagreements on 15,456 shared updates**, canonical ⊆ legacy in
  44,670/45,701 pairs (97.7%); **746,928 (10.5%) are post-kickoff/in-play rows** canonical largely excludes (needs a
  policy ruling, mechanism unproven). The genuine gap is confined to a contiguous **2022-03-07…2023-04-30** window
  (99.98%) where canonical holds just **7.8%** of legacy''s rows. **The structural finding**: legacy holds THREE capture
  generations — G1 (April 2026, the 3,816 old-shape objects), G2 (May 2026, 276,425 objects), G3 (canonical, June 2026)
  — and they are **strictly nested G3 ⊂ G2 ⊂ G1**, proven in both directions (G2-beyond-G1 = 0 over 973 cells; from the
  (b) side 38,197/38,197 = 100.000%, 150/150 objects). **OR-5b(a): ALL 3,816 are FULLY DERIVABLE from content, ZERO
  park-only** — `league_id := instrument_id.split('':'')[3]` agrees **100.0000%** with both the path''s `league=`
  segment and the `league_id` column (499,742 rows); `venue := instrument_id[1].upper() == venue.upper()` **100.0000%**
  (1,065,227 rows); `source == ODDS_API` on 3,816/3,816. Recommendation: **OR-5b(b) = D (PARTIAL / RECOVER-AS-P0) — the
  MDT delete is NOT unblocked**, but recover the **3,816** (a) objects (0.23 GB, 19.9M rows) via one schema-aware
  read-split-merge, NOT the 45,701: that single operation recovers 99.98% of the pre-match gap, after which the 45,701
  (b) objects are provably redundant (G2 ⊂ G1) → no action. Cross-check: T2.10''s 47,253 phantoms are **largely
  DISJOINT** (only 3,354 atoms overlap, 7.1%) — no double-counting.'
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm, market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags:
  [sports, migration, bucket-canonicalisation, row-gap, data-correctness, gcs, manifest, investigation, read-only, odds]
related:
  [
    ../sports_legacy_bucket_cutover_2026_07_16.md,
    ./sports_legacy_canonical_row_gap_2026_07_16.md,
    ../sports_data_sources_canonical_completion_2026_07_13.md,
    ../../epics/sports_master.md,
  ]
created: 2026-07-16
last_updated: 2026-07-16
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: research
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1.2
assigned_role: data
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source:
  [
    "operator ruling 2026-07-16 OR-5b(b) — investigate first, like OR-1",
    "operator ruling 2026-07-16 OR-5b(a) — derive from content, else park",
    "cutover runbook T2.6 / OR-5b",
  ]
---

# MDT legacy↔canonical row gap — why canonical holds 6.7M fewer rows (OR-5b)

> # 🔴 STEP 1-6 (the "MDT RECOVERY EXECUTION PLAN" below) ARE PERMANENTLY BLOCKED — DO NOT DISPATCH 2026-07-25
>
> The legacy bucket (`market-data-tick-sports-central-element-323112`) was **manually deleted by the operator on
> 2026-07-17T17:05:17Z**, BEFORE STEP 1 of this plan ever ran — confirmed **deliberate** (operator ruling, 2026-07-25:
> "abandon recovery"). The bucket is past its 7-day GCS soft-delete window and is **not recoverable**. Full incident
> writeup: `mdt_legacy_bucket_deleted_before_recovery_2026_07_25.md`. **There is nothing left to read — STEP 1-6 as
> written cannot be executed by any future worker, ever.** Do not re-dispatch against this plan's execution steps; every
> attempt will just re-discover the same 404. This doc's INVESTIGATION findings above (the row-gap analysis, the
> G1/G2/G3 nesting proof, the derivation map) remain historically correct and are preserved as read-only record — only
> the EXECUTION plan is dead. **T2.10 (STEP 4, seed purge) is a separate exception — it operates on the still-live
> manifest INDEX, not the deleted bucket's objects, and may be independently actionable; see that issue doc's follow-up
> todo.**

> # 🟢 CONFIRMED + EXPLAINED 2026-07-16 by [`sports_canonical_migrated_odds_mistamped_footystats_2026_07_16.md`](./sports_canonical_migrated_odds_mistamped_footystats_2026_07_16.md) — the G1 leg re-ran the merge decision independently and **refused it a second time.**
>
> The banner below is **upheld on new, independent evidence**, and the mechanism behind it is now identified:
>
> - **Why canonical holds every legacy key**: **16,969** canonical `_migrated_` objects (2026-05-05 refactor, 1,815
>   days) **are** the G1 content — **30/30** sampled G1 objects are row-identical and tick-key-identical to their
>   canonical twin (0 legacy-only, 0 canon-only). Canonical migrated ⊇ legacy G1 (1,815 days vs 386). **"Recovering G1"
>   copies data canonical already has.**
> - **Why the 32-day residue is real**: **213/3,816** G1 objects have **no** canonical migrated twin, on **23** days —
>   **22 of them are exactly this banner's gap days**. Two independent methods, one answer. The 550,062-key / 32-day
>   residue stands.
> - **Why `G3 ⊂ G2 ⊂ G1` looked true at the row layer**: canonical holds **two** populations per day — the June
>   `batch_odds_api` capture (de-duplicated, ~1 quote per tick, mostly the T-24h wave) and the `batch_footystats`
>   `_migrated_` copy (the full fetch-wave grid). Per-pair row comparisons saw only the first.
>
> **The one thing the banner missed**: the recompute leg's starvation is real. MDPS reads only the `batch_odds_api`
> prefix and excludes `_migrated_`, so it cannot see the richer half — "nothing to recover" is right about the
> **bucket** and wrong about the **consumer**. See the new doc.

> # 🔴 SUPERSEDED IN PART 2026-07-16 by the OR-5b(a) RECOVERY LEG — **THE HEADLINE OF THIS DOC IS AN ARTIFACT. DO NOT ACT ON IT.**
>
> **The recovery leg re-measured before writing, per the standing "never inherit a classification, re-measure at the
> key/object layer" rule — and the premise collapsed.** Everything below the fold about the _method_ and the _derivation
> map_ stands (both re-verified exhaustively). **The 6.37M "genuine pre-match density gap" does not exist.**
>
> **The one measurement no prior MDT audit ran: WHOLE-DAY, KEY-LEVEL containment over EVERY legacy tick-day.**
> Exhaustive — all **1,837** legacy tick-days, ~900k object reads, **0 errors** (`~/tmp-or5b/or5b_delete_gate.py` →
> `or5b_delete_gate.jsonl`):
>
> | Measure                                         | Value                                |
> | ----------------------------------------------- | ------------------------------------ |
> | legacy PRE-MATCH tick keys (all days)           | **42,108,211**                       |
> | legacy IN-PLAY tick keys (all days)             | **2,542,764**                        |
> | canonical tick keys                             | **44,091,464**                       |
> | legacy PRE-MATCH keys **absent** from canonical | **524,486 (1.2456%)**                |
> | legacy IN-PLAY keys **absent** from canonical   | **25,576 (1.0058%)**                 |
> | **TOTAL genuine legacy-only keys**              | **550,062 (1.23%)**                  |
> | **Days with ANY legacy-only key**               | **32 of 1,837 (1.74%)** — 1,805 at 0 |
>
> **Why this doc's 6.37M is wrong — two compounding measurement errors:**
>
> 1. **ROWS, not KEYS.** Legacy re-writes the same bookmaker quote at every fetch snapshot; canonical de-duplicated it.
>    Measured on 2022-03-15: G1 holds **28,944 pre-match ROWS carrying only 14,104 distinct tick KEYS**, and canonical
>    holds **14,904 keys — MORE**. This doc's artifact-check (iii) claimed to have cleared exactly this ("only 0.5% are
>    redundant re-polls") — it did not.
> 2. **PER-PAIR, not WHOLE-DAY.** Canonical spreads one legacy object's rows across many objects (2022-04-02: **313**
>    canonical objects for the day), so a row living in a SIBLING canonical object was scored "legacy-only". Check (ii)
>    declared this "CLEARED for (b) — one canonical object per cell"; it does not hold at the row layer.
>
> Over the exact 40 days in the claimed-worst window (2022-03-07…2022-04-21, where this doc says canonical holds
> **7.8%** of legacy's rows): G1 pre-match keys **979,578**, absent from canonical **54 (0.0055%)**. Canonical holds
> **more** distinct keys than legacy on nearly every one of those days.
>
> **The gap that IS real: 32 days, 550,062 keys — dominated by a contiguous canonical capture OUTAGE 2022-09-07 …
> 2022-10-01** (21 days; e.g. 2022-10-01 legacy **104,868** keys vs canonical **8,849**). By year: 2022 = **549,330** ·
> 2023 = **377** · 2025 = **355**.
>
> **⇒ Every OR-5b(a)/(b)/(c) recommendation below is void:**
>
> - **"Recover the 3,816 G1 objects" → REFUSED, and it was executed no further than a dry-run.** **3,472/3,816
>   (90.985%)** of G1 sits on a day where canonical already holds every legacy tick key — there is nothing to recover.
>   The dry-run measured the merge would have **ADDED ~15.7M rows that canonical already holds** — a mass duplication,
>   not a recovery. **No merge was applied. Zero data objects were mutated.**
> - **"G1 recovers 99.98% of the gap" → FALSE.** G1 does not even cover **3 of the 32** gap days (2023-07-29,
>   2025-02-23, 2025-03-02). Only **344/3,816** G1 objects sit on a gap day at all.
> - **"G3 ⊂ G2 ⊂ G1" → FALSE at the key layer.** Canonical (G3) holds **98.77%** of every legacy key and is a near
>   strict SUPERSET, not the poorest generation.
> - **The 45,701 class-B objects close ANYWAY — but by direct proof, not by the nesting claim: 43,964/45,701 (96.199%)**
>   sit on a zero-gap day ⇒ provably redundant. The remaining **1,737** sit on the 32 gap days and are the only class-B
>   objects carrying real data.
>
> **MDT delete-eligibility: 🔴 STILL NOT DELETE-ELIGIBLE** — but the residue is **~2,081 objects on 32 days** (1,737
> class-B + 344 G1), not 49,517, and the payload is **550,062 keys**, not 7,079,850 rows. The correct remedy is a
> **day-scoped recovery of 32 days**, NOT a G1 generation recovery. See the runbook's OR-5b block.
>
> ---
>
> **READ-ONLY investigation. Zero mutations** — no writes, no copies, no manifest changes, no bucket changes. Every
> number below is measured live against the two buckets on 2026-07-16.

| Bucket    | Name                                                 |
| --------- | ---------------------------------------------------- |
| Legacy    | `market-data-tick-sports-central-element-323112`     |
| Canonical | `market-data-tick-sports-prd-central-element-323112` |

## THE HEADLINE — four sentences

1. **The OR-1 trap does NOT reproduce. The naive read is RIGHT this time.** OR-1's audit had measured only the losing 2%
   while canonical was net-richer 15:1. Here the NET balance was computed over **every** paired object and it points the
   other way: **canonical is NET POORER by 6,721,872 rows**, losing **20 rows for every 1 it gains**.
2. **The 7,079,850 is ~89.5% genuine.** 6,372,806 rows are real, distinct pre-match bookmaker quotes canonical never
   captured — **0 price disagreements** where the two generations overlap, and canonical ⊆ legacy in 97.7% of pairs.
   Only the 746,928 in-play rows (10.5%) are policy-ambiguous. Nothing is junk; nothing is fabricated.
3. **But the remedy is ~12× smaller than the runbook assumes.** Legacy holds **three strictly-nested generations** (**G3
   ⊂ G2 ⊂ G1**). The 3,816 objects OR-5b(a) calls "non-derivable" are in fact the **oldest and RICHEST** generation — a
   strict superset of both the 45,701 (b) objects and canonical. Recovering **3,816 objects (0.23 GB)** recovers
   **99.98%** of the pre-match gap; the 45,701 then need no action at all.
4. **OR-5b(a) has no park-only residue.** All **3,816/3,816** are fully derivable from content — the missing fields are
   recoverable from `instrument_id`, which is UAC's own `build_instrument_id` key. **Nothing needs fabricating.**

## Method

- Reused T2.6's exact evidence (`~/tmp-cutover/t2_6_rowcounts.jsonl`, 108,966 crc-differing pairs with measured
  `lr`/`cr`) — spot-verified, not trusted blind.
- **Exact pass, not a sample, for the headline decomposition**: read **both** sides of **all 45,701** unique pairs —
  **91,402 full parquet reads, 0 errors** (OR-1's precedent explicitly condemned extrapolation; T2.6's whole point was
  exact-not-extrapolated).
- Cell key = strip **both** `/pipeline_mode=<x>/` **and** `/data_source=<x>/` (the MDT trap, per T2.6). Verified 1:1
  against the object inventory — no split, no many-to-one.
- Containment measured at three keys to defeat the circularity that inflates "unique" counts: the **poll** key (incl.
  `fetch_utc`), the **tick-identity** key `(event_id, market_key, outcome_name, bm_time, price)`, and the
  **bookmaker-update** key `(event_id, market_key, outcome_name, bm_time)`.

## Artifact checks — all three CLEARED before any verdict

| #   | Classic artifact                             | Test                                                                                                  | Result                                                                                                                                           |
| --- | -------------------------------------------- | ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| i   | **Wrong key mapping**                        | 1:1 against the object inventory; enumerated every canonical object for sampled `(day, league)` cells | **CLEARED** — exactly one canonical counterpart per legacy object; T2.6's dual strip is correct                                                  |
| ii  | **1:N split** (rows present but spread)      | Enumerated the **full** canonical counterpart set per cell and summed across it, never 1:1            | **CLEARED** for (b) — one canonical object per cell. **CONFIRMED for (a)** — the old-shape objects ARE 1:N (mean 26.1 cells each); handled below |
| iii | **Snapshot/dedup skew** (redundant re-polls) | Re-ran containment on the tick-identity key with `fetch_utc` REMOVED                                  | **CLEARED** — only **0.5%** of the gap is redundant re-polls; **99.5%** are distinct bookmaker quotes                                            |

> Artifact (iii) is the one that would have made this a false alarm — "canonical polled less often" would be a
> non-finding. It is not what happened: legacy's extra rows carry **`bm_time` values canonical has no row for at all**,
> i.e. **bookmaker updates canonical never observed**, not re-observations of ticks it already holds.

---

## NET ROW BALANCE — the number OR-1's audit never computed

Over **all 108,966** crc-differing pairs (the 287,634 crc-identical pairs are byte-identical ⇒ contribute exactly 0):

| Relation                 | Objects        | Rows           |
| ------------------------ | -------------- | -------------- |
| canonical **MORE** rows  | 13,227 (12.1%) | **+357,978**   |
| canonical SAME rows      | 50,038 (45.9%) | 0              |
| canonical **FEWER** rows | 45,701 (41.9%) | **−7,079,850** |
| **NET**                  |                | **−6,721,872** |

Total rows over paired objects: legacy **23,677,195** vs canonical **16,955,323**. **Canonical gains 0.05 rows for every
1 it loses — a 20:1 deficit.**

> **This is the exact inverse of OR-1**, where canonical was +27,764 NET and gained 15:1. The instruments precedent does
> **not** transfer. On this bucket, canonical is genuinely the poorer generation.

## EXACT DECOMPOSITION of the 7,079,850 — all 45,701 pairs, 0 errors

| Measure                                          | Value                           |
| ------------------------------------------------ | ------------------------------- |
| T2.6 raw row gap (`lr − cr`)                     | **7,079,850**                   |
| Legacy-only ROWS at tick identity                | **7,119,734**                   |
| Canonical-only ROWS at tick identity             | 8,929                           |
| — of the legacy-only: **PRE-MATCH** (`mtk >= 0`) | **6,372,806** (89.5%)           |
| — of the legacy-only: **POST-KICKOFF / in-play** | **746,928** (10.5%)             |
| Distinct bookmaker updates — legacy              | 13,000,712                      |
| Distinct bookmaker updates — canonical           | 5,926,464                       |
| **Bookmaker updates canonical NEVER captured**   | **7,083,177** (54.5% of legacy) |
| Bookmaker updates only canonical has             | 8,929                           |
| Pairs where canonical ⊆ legacy (tick level)      | **44,670 / 45,701 (97.7%)**     |
| Pairs where canonical holds every legacy tick    | **1 / 45,701**                  |

**Price integrity (the fabrication test):** across 15,456 **shared** bookmaker updates the two generations agree on
price **100.00% — zero disagreements**. Legacy is not fabricated (OR-1's `player_values` cartesian-junk class has no
analogue here), and canonical is not corrupt. They simply captured **different amounts of the same true market**.

### The gap is one contiguous 14-month window

| Year  | Objects | Legacy rows | Canon rows | **Pre-match gap** | In-play gap | Canon-only |
| ----- | ------- | ----------- | ---------- | ----------------- | ----------- | ---------- |
| 2020  | 1,896   | 534,122     | 496,965    | **0**             | 37,143      | 0          |
| 2021  | 1,573   | 587,411     | 543,950    | **0**             | 43,533      | 72         |
| 2022  | 23,318  | 6,261,306   | 1,160,364  | **4,865,391**     | 269,471     | 8,280      |
| 2023  | 10,297  | 2,692,781   | 1,032,553  | **1,506,097**     | 159,503     | 0          |
| 2024  | 3,492   | 1,235,143   | 1,134,857  | **0**             | 100,267     | 0          |
| 2025  | 1,354   | 470,027     | 433,823    | 1,318             | 34,927      | 41         |
| 2026  | 3,771   | 1,273,004   | 1,171,432  | **0**             | 102,084     | 536        |
| **Σ** | 45,701  | 13,053,794  | 5,973,944  | **6,372,806**     | **746,928** | 8,929      |

**99.98%** of the pre-match gap (6,371,448 of 6,372,806 rows) falls inside **2022-03-07 … 2023-04-30**. Outside that
window the pre-match gap is **exactly zero** — canonical is at full parity. Within it, canonical holds only **7.8%** of
legacy's rows (564,335 of 7,196,584). This is a **bounded, dated under-capture by the June canonical campaign**, not a
systemic defect.

The in-play deficit, by contrast, is **uniform across all seven years** — a different mechanism (see class 2).

---

## THE STRUCTURAL FINDING — three strictly-nested generations

Provenance is measured from object metadata, and it **corrects the audit**:

| Generation                              | Objects | Created                | Rows            |
| --------------------------------------- | ------- | ---------------------- | --------------- |
| **G1** — legacy old-shape (sub-class a) | 3,816   | **2026-04-05 … 04-13** | 19,944,880      |
| **G2** — legacy `batch_api_football`    | 276,425 | **2026-05-19 / 05-22** | ~23.7M (paired) |
| **G3** — canonical `batch_odds_api`     | 252,171 | **2026-06-18 … 06-28** | ~17.0M (paired) |

> **Audit correction (R-20 class).** The runbook records _"all 406,581 were created 2026-06-27 in ONE bulk op"_. That is
> **false** — `2026-06-27` is the **COLDLINE storage-class lifecycle transition** (`updated` + `sc_upd`), not a write.
> Every legacy trades object's `created` is **2026-05-19 (231,532)** or **2026-05-22 (44,893)**. Reading `updated` as a
> write time would have mis-dated the entire corpus.

**The three generations are strictly nested — proven in BOTH directions:**

| Direction | Test                                                           | Result                                                                                |
| --------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| From (a)  | `G2 − G1` over 973 cells from 70 old-shape objects             | **0 quotes** — May adds nothing over April                                            |
| From (a)  | `G3 − (G1 ∪ G2)` over the same 973 cells                       | **0 quotes** — canonical adds nothing over legacy                                     |
| From (b)  | 150 randomly-sampled **pre-match-gap** objects → is `G2 ⊆ G1`? | **38,197 / 38,197 = 100.000%**, **150/150 objects**, 0 with a missing (a) counterpart |

⇒ **G3 ⊂ G2 ⊂ G1.** Each successive re-fetch captured strictly less. **The April old-shape objects are the master
copy.** And **99.8%** of the 28,804 pre-match-gap objects (carrying **99.98%** of the gap rows) sit on a day that has an
(a) object.

> **Therefore: recovering the 3,816 (a) objects recovers 99.98% of the 6.37M pre-match gap.** The 45,701 (b) objects
> hold **nothing** the (a) objects do not already hold. This collapses the remedy from 45,701 read-merge-writes to
> **3,816 reads (0.23 GB)**.

---

## PER-CLASS VERDICT

### 1. PRE-MATCH DENSITY GAP — 6,372,806 rows (89.5%) — verdict **GENUINE. Recover (via G1).**

Real, distinct bookmaker quotes canonical never captured. Every falsification test failed to break it:

- **Not re-polls**: 99.5% carry `bm_time` values canonical has no row for → genuine missed bookmaker updates.
- **Not fabricated**: 100.00% price agreement on 15,456 shared updates.
- **Not a coverage illusion**: **0/200** sampled pairs have canonical missing an `event_id` or a `market_key` —
  canonical covers the same fixtures and the same markets. The deficit is purely **temporal density**: canonical holds
  ~33–49% of legacy's quotes at **every** pre-match horizon (T-24h … T-0), uniformly.
- **Not spread elsewhere**: canonical's counterpart set is exactly one object per cell (verified against the inventory).

Legacy captures the full 8-point horizon grid (T-24h, T-12h, T-6h, T-4h, T-2h, T-1h, T-10m, T-0); canonical's June
re-fetch frequently captured only one or two points of it. **Odds trajectory across the pre-match window is precisely
the signal a sports strategy consumes** — this is not incidental density.

Bounded to **2022-03-07 … 2023-04-30**, 23 venues, 26 leagues.

### 2. POST-KICKOFF / IN-PLAY — 746,928 rows (10.5%) — verdict **REAL but POLICY-AMBIGUOUS. Operator ruling needed.**

> **🔬 SUPERSEDED IN PART 2026-07-16 by
> [`sports_halftime_odds_sfi_vs_inplay_2026_07_16.md`](./sports_halftime_odds_sfi_vs_inplay_2026_07_16.md)** (operator
> question: _"we want half time odds — is there knowledge of this from SFI derived half time?"_). **The mechanism below
> is no longer unproven, and this section's WORKER REC (option A) is superseded by B-REFINED.**
>
> - **The exclusion is NOT a deliberate pre-match-only policy** — it is a June-campaign snapshot-grid artifact. The
>   "lookahead-bias guarantee that may rest on it" **does not exist**: MDPS force-feeds every post-kickoff row into
>   **T-0** (`nearest_idx[vals<0]=N_BUCKETS-1`, applied AFTER the staleness rejection), and **184/282 (65%) of sampled
>   canonical T-0 rows are already post-kickoff**, to −71.1 min. There is no pre-match purity to protect.
> - **SFI already holds half-time ODDS, denser** — the captured `sfi_progressive_stats` contract carries 12 price
>   columns, **100% non-null inside the HT break**, 31/31 fixtures 2021→2026, 30s granularity, over a superset of these
>   leagues. The half-time market LEVEL does not depend on these rows.
> - **Only ~3.1% (~23,000 rows) is unique+usable** — per-bookmaker quotes in the PIT-valid HT-break window (+45..55);
>   63.2% is what the HT odds PIT gate actively rejects as 2nd-half leakage, 17.0% is post-match. **No HT-specific
>   market exists in these rows at all** (`h2h`/`totals`/`spreads`/`h2h_lay` only).
> - **Revised disposition → B-REFINED**: carry the in-play rows through the option-D G1 read-split-merge (they are in
>   the same 3,816 objects — marginal cost ≈ 0) into a **DISTINCT population quarantined from the pre-match bucketing
>   path**. Merging them into `data_type=odds` would sweep them into T-0 and deepen the 65% contamination.

Uniform across all seven years, unlike class 1. These are rows with `minutes_to_kickoff < 0` — odds snapshots taken
**after** the fixture kicked off. Canonical holds **1.07%** in-play vs legacy's **5.59%**; **92/112** sampled canonical
objects hold **zero** in-play rows.

The exclusion is **strong but not absolute**, and **no filter exists in the current adapter** — `odds_api_adapter.py`
computes `minutes_to_kickoff` but never filters on it. So the mechanism is **unproven**: it may be a deliberate
pre-match-only capture policy (consistent with the workspace's pinned _"footystats PREDICTIVE pre-match ODDS"_ ruling
and the `assert_available_at_present` / `LookaheadBiasError` guard), or simply an artifact of the June campaign's
snapshot grid stopping at kickoff.

**Do not silently discard 746,928 real observations on an unproven mechanism, and do not blindly merge them into a
bucket whose pre-match-only property may be load-bearing for lookahead-bias guarantees.** This needs a written
disposition — see OR-5b(c) below.

### 3. Residual pre-match outside the window — 1,358 rows — verdict **negligible; recover opportunistically or document.**

1,358 rows on days with no (a) object (chiefly 2025-03-02). Below any materiality threshold; record the disposition.

---

## Summary table — where the 7,079,850 rows actually go

| Class                      | Rows          | %     | Verdict                                                                       | Recover?         |
| -------------------------- | ------------- | ----- | ----------------------------------------------------------------------------- | ---------------- |
| **Pre-match density gap**  | **6,372,806** | 89.5% | **GENUINE** — real distinct quotes, 0 price disagreements, canonical ⊆ legacy | **YES** (via G1) |
| **Post-kickoff / in-play** | 746,928       | 10.5% | REAL but policy-ambiguous — mechanism unproven                                | **RULING**       |
| Residual (outside window)  | 1,358         | 0.02% | negligible                                                                    | opportunistic    |
| **Total**                  | **7,119,734** | 100%  | **~89.5% genuine · 0% junk · 0% fabricated**                                  |                  |

> Contrast with OR-1 (instruments): ~59% junk/skew, ~37% genuine. **MDT is ~89.5% genuine and 0% junk.** The two buckets
> must not be reasoned about by analogy.

---

## OR-5b(a) — THE DERIVATION MAP (all 3,816, measured exhaustively)

**Verdict: 3,816 DERIVABLE / 0 PARK-ONLY.** The operator's "else park" branch is **empty**. Nothing is fabricated —
every field comes from the rows.

The four old shapes hold **19,944,880 rows / 0.23 GB**:

| Shape                                                         | Objects | Created       |
| ------------------------------------------------------------- | ------- | ------------- |
| `raw_tick_data/by_date/day=*/source=*/league=*/ticks.parquet` | 2,881   | 2026-04-12    |
| `raw_tick_data/by_date/day=*/venue=*/league=*/ticks.parquet`  | 549     | 2026-04-13    |
| `raw_tick_data/by_date/day=*/source=*/ticks.parquet`          | 364     | 2026-04-05/06 |
| `raw_tick_data/by_date/day=*/venue=*/ticks.parquet`           | 22      | 2026-04-12    |

**The key insight the runbook missed**: the path's `source=ODDS_API` / `venue=ODDS_API` segment is the **VENDOR**, not
the bookmaker venue. The real venue is a **column in the rows** (`betonlineag`, `pinnacle`, …). That is why no canonical
path looked derivable — the derivation was being attempted from the path instead of from the content. And
`instrument_id` is **UAC's own `build_instrument_id` key**
(`unified_api_contracts/canonical/domain/sports/canonical_ids.py`), format
`SPORT:VENUE:MARKET_TYPE:LEAGUE:SEASON:HOME-AWAY::SELECTION` — it **encodes both missing dimensions**.

### The rules — each MEASURED against ground truth, none assumed

| Field             | Rule                                  | Evidence                                                                                                                                    |
| ----------------- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `asset_group`     | `sports`                              | bucket constant — `market-data-tick-sports-*` is sports-only; 100% of canonical objects carry it                                            |
| `pipeline_mode`   | `batch_odds_api`                      | `source` column == `ODDS_API` on **3,816/3,816 objects, every row**. Identical rule T2.6 already verified + crc-proved for the 6,110        |
| `venue`           | `instrument_id.split(':')[1].upper()` | **100.0000%** agreement with the row's own `venue` column uppercased — **1,065,227 rows / 200 objects**; total-rule-true on **3,816/3,816** |
| `league_id`       | `instrument_id.split(':')[3]`         | **100.0000%** agreement with **BOTH** the path's `league=` segment **AND** the `league_id` column — **499,742 rows / 150 objects**          |
| `instrument_type` | `odds`                                | canonical convention: **252,155 / 252,171** raw trades objects (16 `=sport` outliers)                                                       |
| `data_type`       | `trades`                              | canonical convention: **252,163 / 252,171** at `pipeline_mode=batch_odds_api` (8 `live_odds_api`)                                           |
| malformed ids     | —                                     | **0** malformed `instrument_id`s across all 3,816                                                                                           |

**Why `league_id` is proven and not a heuristic**: the rule is validated on the **3,430 objects where the answer is
already known** (the path carries `league=`), where it agrees **100.0000%**, and only then applied to the **386** that
lack it. This is derivation from evidence, not inference.

### The fan-out — this is a SPLIT, not a copy

| Measure                                             | Value      |
| --------------------------------------------------- | ---------- |
| canonical target cells `(day, venue, league_id)`    | **99,414** |
| — cells that **already exist** in canonical (merge) | 87,194     |
| — cells that **do not exist** (new object)          | 12,220     |
| mean cells per old-shape object                     | **26.1**   |

**⚠️ `gcs_copy_object` cannot execute this** — it is a read → split-by-`(venue, league_id)` → **merge** → write. The
T2.6 vehicle is the wrong instrument for sub-class (a).

---

## RECOMMENDATION

### OR-5b(b) → **D (PARTIAL / RECOVER-AS-P0) — a new option; supersedes A/B/C**

> **The `market-data-tick-sports` delete is NOT unblocked.** Deleting the legacy bucket today destroys **6,372,806
> genuine, verified, non-reproducible pre-match bookmaker quotes**. That is a `data-pipeline-correctness-hard-rule`
> violation, not an acceptable descope.

- **REJECT C (skip / accept the loss)** — the loss is real, genuine, and 89.5% of the gap. The OR-1 escape hatch ("it
  was mostly junk") is **not available here**: 0% is junk, 0% is fabricated.
- **REJECT B (blanket union of the 45,701)** — **wrong instrument, ~12× the work, and lossy at the edges.** The 45,701
  (b) objects are provably **redundant**: `G2 ⊂ G1` at 100.000%. Unioning them recovers nothing the 3,816 don't already
  carry, at 45,701 read-merge-writes instead of 3,816 reads.
- **ADOPT D — recover **sub-class (a)**, then close (b) as redundant:**
  1. **Recover the 3,816 G1 objects** (0.23 GB, 19.9M rows) via **one schema-aware read-split-merge** into the 99,414
     canonical cells. This recovers **99.98% of the 6.37M pre-match gap** plus G1's own superset content, in a single
     bounded operation. Derivation map above — the executor must **not re-derive it**.
  2. **The 45,701 (b) objects → NO ACTION** once (1) lands. `G2 ⊂ G1` is proven in both directions; they are
     information-free relative to G1. This is the single biggest scope reduction available.
  3. **MERGE, never overwrite.** Canonical holds **8,929** tick-quotes legacy lacks and **extra columns** legacy lacks
     (`bookmaker_key`, `fixture_id`, `available_at`). An overwrite destroys them. The write must union rows on
     `(event_id, market_key, outcome_name, bm_time, price)` and preserve canonical's column set.
  4. **`available_at` must be stamped, never invented** — use the sanctioned
     `unified_trading_library.availability_stamping.stamp_available_at_odds_snapshot(df, source="odds_api")`, which T2.7
     already verified empirically against native canonical objects (`available_at − bm_time == 5.0s uniformly`).
  5. **Delete-gate**: `market-data-tick-sports` becomes delete-eligible only after the recovered cells are
     crc/row-verified in canonical — the gate is the OBJECT layer (T4.1), never the manifest.
- **Net effect**: OR-5b(b) shrinks from _"45,701 objects / 7.08M rows, undecidable"_ to **"3,816 objects / one
  schema-aware split-merge, fully specified"** — with the 45,701 closed by proof rather than by policy.

### OR-5b(a) → **B (infer from content) — and the inference IS provably total**

The runbook's premise (_"no canonical path is derivable without inventing those fields (fabrication)"_) is **FALSE**,
and its recommended fallbacks are therefore moot:

- **REJECT A (row-count then abandon)** — their rows are **not** contained in canonical (52.9% of a 110-object sample is
  legacy-only); abandoning them discards the master generation.
- **REJECT C (park under `_audits/`)** — parking is the correct answer only for a genuinely non-derivable object, and
  **there are none**: 3,816/3,816 derive from content at 100.0000%. Parking the richest generation as an opaque archive
  would be a data-correctness regression dressed as caution.
- **ADOPT B** — every field derives from the rows via UAC's own `build_instrument_id` key. **The operator's
  never-fabricate constraint is fully honoured: nothing is invented, every value is read from the data and
  cross-validated against ground truth where ground truth exists.**

### OR-5b(c) → **NEW — the in-play question needs a ruling (746,928 rows)**

Not covered by the operator's 2026-07-16 rulings, and it must not be settled silently by either recovery or deletion.

> **🔬 INVESTIGATED + RE-RECOMMENDED 2026-07-16 →
> [`sports_halftime_odds_sfi_vs_inplay_2026_07_16.md`](./sports_halftime_odds_sfi_vs_inplay_2026_07_16.md). The WORKER
> REC below moves from A to B-REFINED; C is spent (mechanism proven).**

- ~~**A: recover pre-match only; document the 746,928 in-play rows as a deliberate, written exclusion [WORKER REC]**~~ —
  **REJECTED**: its premise is measurably false. Canonical has no pre-match-only property to preserve (T-0 is **65%**
  post-kickoff) and no lookahead guarantee rests on it (MDPS force-feeds post-kickoff rows into T-0). Discards ~23,000
  non-reproducible per-bookmaker HT-break quotes for no gain.
- **B: recover in-play too, into a distinct population** (e.g. its own `instrument_type` / `data_type`), so pre-match
  consumers are unaffected but the observations survive. → **ADOPT as B-REFINED [WORKER REC 2026-07-16]**: the rows ride
  along on the option-D G1 read-split-merge (same 3,816 objects — marginal cost ≈ 0), landing in a distinct population
  **quarantined from the pre-match bucketing path** (merging into `data_type=odds` would sweep them into T-0 and deepen
  the existing 65% contamination).
- ~~**C: prove the mechanism first**~~ — **SPENT**: mechanism proven. The exclusion is a **June-campaign snapshot-grid
  artifact, not a deliberate policy** — no adapter filter exists AND the processed layer actively force-feeds
  post-kickoff rows into T-0.
- Other.

**Half-time-odds context (the operator's actual question):** the delete does **not** cost us half-time market knowledge
— SFI's captured `sfi_progressive_stats` carries 12 populated price columns at 30s granularity, **100% non-null through
the HT break**, 31/31 fixtures 2021→2026, over a superset of these leagues. What dies is the **per-bookmaker** HT
dispersion (~3.1% ≈ 23k rows, 23 books). The **HT-RESULT market (first-half 1X2) is in NEITHER source** — SFI's API
serves `h1_*` but `_extract_odds()` never reads it → a re-fetchable capture gap, not a deletion loss.

## Cross-checks

- **T2.10 (47,253 phantom `api_football × trades` index rows) — LARGELY DISJOINT. No double-counting.** Measured against
  the live canonical index: 47,253 `captured` rows, all with nonzero `instrument_count`, spanning 2020/2022/2023/2025.
  Their distinct `(date, venue, league_id)` atoms vs the OR-5b(b) objects' 42,336 atoms → **overlap = 3,354 (7.1%)**;
  43,899 phantom atoms have no OR-5b(b) object and 38,982 OR-5b(b) atoms have no phantom row. The two defects are
  independent: T2.10 is an INDEX-layer mis-stamp, OR-5b(b) is an OBJECT-layer capture gap. **T2.10's purge predicate
  remains correct and must still carry its mandatory `source` filter.**
- **OR-1 / the instruments bucket is untouched by this investigation** and its option-D disposition stands. The two
  buckets have **opposite** verdicts — do not generalise either.

## Loose ends / follow-ups (not fixed here — read-only investigation)

| #   | Finding                                                                                                                                                                                                                                                                                                                  | Triage                                     |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------ |
| 1   | **The June canonical odds campaign under-captured 2022-03-07…2023-04-30 by ~92%** (canonical holds 7.8% of legacy's rows in-window). Whatever ran it either lost or never requested the horizon grid for that window. **Root cause unidentified — and if the same campaign is still live, it is still under-capturing.** | **BIG FINDING → operator + own issue doc** |
| 2   | **Three overlapping capture generations coexist in one legacy bucket** (April old-shape / May `batch_api_football` / June canonical), each a strict subset of its predecessor. No generation marker, no supersession record.                                                                                             | Feeds T0.1 / OR-2 (unidentified writers)   |
| 3   | **The runbook's "all 406,581 created 2026-06-27 in ONE bulk op" is a COLDLINE lifecycle artifact** (`updated`, not `created`). Any other inference resting on that date should be re-checked.                                                                                                                            | Correct the runbook (done — see T2.6 note) |
| 4   | **Canonical's `data_type` COLUMN says `odds` while its PATH says `data_type=trades`** (legacy's column says `trades`). Column/path disagreement on a live surface; corroborates T2.9's contract drift.                                                                                                                   | Feeds T2.9                                 |
| 5   | **30/200 sampled canonical objects carry duplicate rows on the poll key** `(event, market, outcome, bm_time, price, fetch_utc)`. Independent of the cutover; a merge must de-duplicate on write or inherit it.                                                                                                           | New issue doc — data-correctness           |

## Progress Log

**2026-07-16 (later) — OR-5b(a) RECOVERY LEG: the merge was REFUSED on measurement. Zero data objects mutated.** The leg
was dispatched to execute the option-D G1 read-split-merge (3,816 objects → 6.37M pre-match rows + the in-play subset).
Per the standing re-measure rule, every inherited claim was re-tested at the key/object layer BEFORE any write. Sequence
and evidence (`~/tmp-or5b/`):

1. **Live re-inventory of both MDT buckets** (`or5b_inventory.py`) — legacy **406,583** (the +2 vs the 07:44 baseline
   are this morning's own T0.6 snapshot backups; legacy is dormant, 0 removals), canonical **497,692**. G1 re-listed
   live: **3,816** objects / 227,673,166 B / created 2026-04-05…04-13 — matches this doc exactly.
2. **Derivation map RE-VALIDATED exhaustively** (`or5b_g1_measure.py`, all 3,816 objects / **19,944,880 rows**, 0
   errors): `source == ODDS_API` **100.0000%** · `venue := instrument_id[1].upper()` **100.0000%** ·
   `league_id := instrument_id[3]` vs BOTH the path `league=` and the `league_id` column **100.0000%** · `date` column
   == path `day=` **100.0000%** · **0 malformed instrument_ids**. **This doc's map is CORRECT and is confirmed** — the
   "fabrication-required" premise is indeed disproven.
3. **A rule this doc's map is MISSING — `.upper()`.** Canonical's `league_id` vocabulary carries BOTH `SOCCER_EPL` and
   `soccer_epl`. With `.upper()`, **all 49,707** derived target cells already exist in canonical ⇒ **0 new objects**.
   (This doc reports 99,414 cells / 87,194 existing / 12,220 new — exactly **2×** the measured 49,707, i.e. the fan-out
   census double-counted every cell.)
4. **🔴 BIG FINDING — T2.6's 6,110-object move is a pure DUPLICATE population** (`or5b_t26_dup_proof.py`, EXACT over all
   6,110 pairs / 12,220 full reads / 0 errors): the 6,110 lowercase-`league_id` canonical objects are **exactly** T2.6's
   dst set, and each is content-identical to canonical's pre-existing native UPPERCASE-`league_id` twin on the same
   (day, venue, LEAGUE) — **6,110/6,110 = 100.0000% identical tick-key sets, 0 legacy-only ticks, 0 canonical-only
   ticks**. T2.6's strip key was case-blind, so it classified already-present objects as "class A / no canonical
   counterpart". T2.6 recovered **0 rows** and added 6,110 duplicate objects; T2.7's MDT shard describes them. Own issue
   doc filed. **No deletion performed — this leg authorises none.**
5. **Canonical target-cell schema census** (`or5b_schema_census.py`, all 49,707 cells, footer reads, 0 errors): **4**
   schema families, all 23-col. The `bookmaker_key`/`fixture_id`/`available_at` trio this doc calls "3 columns legacy
   lacks" exists in only **6,641/49,707 (13.4%)** — and those cells LACK `venue`/`instrument_type`/`data_source`, which
   the other 43,066 HAVE. Two families, not a superset.
6. **Column conventions measured, never invented** (`or5b_colvalues.py`): `bookmaker_key.upper() == path venue` and
   `== instrument_id[1].upper()` on **10,744/10,744**; canonical's own `fixture_id` is **`''` on 100%** (0 nulls, 0 ==
   event_id); `available_at − bm_time == 5.0s` on **10,744/10,744** (re-confirms T2.7). Family A `data_type` column =
   `trades`; family B = `odds` (T2.9 drift, and it splits BY FAMILY).
7. **THE DECISIVE CHECK — whole-day key containment** (`or5b_wholeday_check.py` → `or5b_delete_gate.py`). The per-cell
   dry-run claimed ~1.65M rows to add over 40 days; against the **whole-day** canonical keyset those same G1 pre-match
   keys were **99.9945% already present (54 absent of 979,578)**. Escalated to an exhaustive pass over **all 1,837
   legacy tick-days**: **550,062 legacy-only keys (1.23%) on 32 days; 1,805 days at exactly ZERO.** See the banner.
8. **Merge REFUSED.** Applying it would have written ~15.7M rows canonical already holds. `or5b_merge.py` exists and is
   dry-run-clean (0 parked / 0 aborted / merge-not-overwrite proof per object) but was **never run with `--apply`**. The
   in-play quarantine was never written.

**Only GCS write performed by this leg** (additive, non-destructive, mandated): the canonical MDT index snapshot →
`gs://market-data-tick-sports-prd-central-element-323112/_index/or5b_backups/20260716-164545/availability_index.20260716-164545.or5b_g1.bak.parquet`,
crc32c `2KzY/w==` **verified == source** (47,184,905 B, src gen 1784189886055849). Placed under `_index/or5b_backups/` —
never `_index/per_vm/` (R-11). **No per-VM manifest shard was written** (`or5b-g1-20260716` does not exist): a shard
must describe real recovered cells, and there are none. **No data object was created, modified, or deleted.**

**A mechanism correction for whoever executes the 32-day recovery — the in-play quarantine design in OR-5b(c) does NOT
work as specified.** Measured, not assumed: `reprocess_sports_odds.py::_is_consumable_trades_blob` is
`name.endswith("ticks.parquet") and "_migrated_" not in name` — it lists at
`day={D}/pipeline_mode=batch_odds_api/asset_group=sports/` and **never inspects the `instrument_type=`/`data_type=`
segments**. So a distinct `instrument_type`/`data_type` alone (the ruling's stated mechanism) would still be swept in
and force-fed to T-0. A working quarantine needs BOTH axes: a **filename that is not `ticks.parquet`** (defeats the
sports reprocessor) AND a **distinct `data_type=`** (defeats `orchestration_scanner._matches_data_type`, which is a
`f"data_type={dt}/" in name` substring test). `pipeline_mode` must stay the true `batch_odds_api` — it is a closed UAC
enum (`{mode}_{source}`, test-enforced); `batch_odds_api_inplay` would be fabricating a field. Residual hazard measured:
a day holding a quarantine blob but no consumable blob would raise `RawOddsShapeUnrecognizedError` (a false
`attempted_failed`) — over all 301 in-play days, **0 such days**. Note also that the sibling leg's fix has ALREADY
landed in `bucket_assignment_adapter.py` (`n[vals < 0] = -1`, post-kickoff REJECTED, replacing the T-0 force-feed), so
the code layer no longer force-feeds; the quarantine is defence-in-depth, not the sole guard.

**2026-07-16** — Investigation executed read-only per operator rulings OR-5b(a)+(b). **Exact pass over all 45,701 unique
pairs (91,402 full parquet reads, 0 errors)** — not a sample, per the OR-1 precedent's own critique of extrapolation.
All three classic artifacts (key mapping / 1:N split / snapshot-dedup skew) tested and **cleared**; the OR-1 trap does
**not** reproduce. NET balance over every paired object: **canonical −6,721,872 rows, losing 20:1** (OR-1 was +27,764,
gaining 15:1). The 7,079,850 is **89.5% genuine pre-match bookmaker quotes / 10.5% policy-ambiguous in-play / 0% junk /
0% fabricated** — 100.00% price agreement on 15,456 shared updates, canonical ⊆ legacy in 97.7% of pairs. Structural
finding: **G3 ⊂ G2 ⊂ G1** proven in both directions (150/150 objects, 38,197/38,197 quotes) ⇒ the 3,816 "non-derivable"
objects are the master superset and their recovery covers **99.98%** of the gap, closing the 45,701 by proof. OR-5b(a):
**3,816 derivable / 0 park-only** — `league_id := instrument_id[3]` at **100.0000%** against known ground truth,
`venue := instrument_id[1].upper()` at **100.0000%** over 1,065,227 rows; the runbook's "fabrication-required" premise
is disproven (the path's `source=` is the vendor; the venue is in the rows). Zero mutations; scratch data deleted.

**2026-07-17 — OR-5b(c) RULED by operator (via `[slot-3·laptop]` takeover): RECOVER IN-PLAY INTO A DISTINCT POPULATION
(B-REFINED).** Operator ruling 2026-07-17: the 25,576 in-play keys are recovered (not excluded) into a population
quarantined from the pre-match T-0 path. **Quarantine mechanism (as the runbook's own correction mandates —
`_is_consumable_trades_blob` matches on filename `ticks.parquet` only): a non-`ticks.parquet` filename AND a distinct
`data_type=`, with `pipeline_mode` staying `batch_odds_api` (closed UAC enum).** The pre-match 524,486 keys recover into
the canonical odds path. Delete gate remains the day-scoped 32-day recovery + T4.1 object-layer unique==0. **Execution
owner: `[slot-3·laptop]` (reassigned by operator 2026-07-17; `[main·laptop]` idle 5h, confirmed off).** No tooling was
inherited (the `~/tmp-or5b/` scripts live on another host) → recovery is being rebuilt from spec, re-measuring the 32
gap days independently before any write (standing "never inherit a classification" rule).

**2026-07-25 — 🔴 BLOCKED (slot 2). Legacy bucket manually deleted 2026-07-17T17:05:17Z, confirmed by the operator as a
DELIBERATE abandonment of this recovery (2026-07-25 ruling, via `AskUserQuestion`). STEP 1-6 below can never execute —
their read target no longer exists and is past GCS's 7-day soft-delete window. Full incident:
`mdt_legacy_bucket_deleted_before_recovery_2026_07_25.md`. Do not dispatch against STEP 1-6 again.**

**2026-07-17 — MDT RECOVERY EXECUTION PLAN (slot-3, IN PROGRESS — nothing mutated yet; 🔴 SUPERSEDED 2026-07-25, see
banner above — the legacy bucket this plan reads from was deleted before any step ran). Ground truth re-established this
session:**

- **Layout confirmed by direct sampling.** Both buckets: `raw_tick_data/by_date/day=YYYY-MM-DD/…`. LEGACY gap-day
  objects are **OLD-shape** — `day=2022-10-01/source=ODDS_API/ticks.parquet` and
  `…/source=ODDS_API/league=<L>/ticks.parquet` (no `asset_group`/`instrument_type`/`data_type` segments). CANONICAL is
  new-shape (`pipeline_mode=/asset_group=sports/instrument_type=/data_type=/…`). The recovery must derive the canonical
  path segments from the rows (`build_instrument_id`, the (a) derivation map — re-validated 100.0000%) — NOT copy paths.
- **Delete gate = the day-scoped 32-day recovery + T4.1 unique==0 + T2.10 seed purge.** (Everything else — the migrated
  mis-stamp, the T2.6 duplicate population — is a SEPARATE features-recompute issue, ~4-line MDPS fix, NOT the delete
  gate.)
- **STEP 1 (read-only) — re-derive the 32 gap days.** Candidate window from the banner (2022-09-07…2022-10-01 dominant +
  a handful of 2023/2025 days); do NOT inherit the day-list — confirm by whole-day KEY-LEVEL containment (legacy tick
  keys − canonical tick keys) over the candidate window + probe the rest via the availability index's per-day counts.
  Expect ~32 days / **550,062** legacy-only keys (524,486 pre-match + 25,576 in-play) / ~2,081 objects.
- **STEP 2 (build) — day-scoped read-split-merge.** Per gap day: read legacy old-shape objects → extract keys absent
  from canonical → derive canonical segments via `build_instrument_id` → split pre-match vs in-play by kickoff time.
  **MERGE, never overwrite** (canonical holds columns legacy lacks: `bookmaker_key`,`fixture_id`,`available_at`); de-dup
  on the poll key `(event,market,outcome,bm_time,price)` (30/200 canonical objects have poll-key dups — de-dup on
  write); stamp `available_at` via
  `unified_trading_library.availability_stamping.stamp_available_at_odds_snapshot(df, source="odds_api")`.
- **STEP 2b — in-play quarantine (per OR-5b(c) ruling).** In-play rows land in a DISTINCT population:
  **non-`ticks.parquet` filename AND a distinct `data_type=`** (else `_is_consumable_trades_blob` filename-match sweeps
  them into T-0); `pipeline_mode` STAYS `batch_odds_api` (closed UAC enum).
- **STEP 3 — verify by CONTENT** (fresh re-read in a separate process, never the writer's return): recovered keys
  present in canonical, crc/row-verified; collateral-damage census (group-by (data_type,source) before/after) shows only
  the intended cells changed.
- **STEP 4 — T2.10 seed purge**: strip 37,114 phantom `api_football × trades` (captured, nonzero IC) from
  `_index/per_vm/_legacy_seed.parquet` with the NULL-safe COALESCE source filter (211,313 real `odds_api × trades`
  survive), back up first, let the consolidator re-merge; verify by content.
- **STEP 5 — T4.1 MDT object-layer proof** (unique==0 for the legacy bucket) → **STEP 6 — delete the legacy bucket**
  (backed up first). **⚠️ CHECKPOINT WITH OPERATOR BEFORE STEP 6 (irreversible).**
- Build as a one-off `market-tick-data-service/scripts/` migration with lifecycle markers. Tooling from `~/tmp-or5b/` is
  NOT on this host → rebuilt from this spec.

> **🟥 BLOCKED-OPERATOR-DECISION, 2026-07-25 (slot 7, data_engineering) — this plan is now MOOT, do not dispatch STEP
> 1-6 against it.** Live-verified before attempting STEP 1: the legacy bucket
> (`market-data-tick-sports-central-element-323112`) was manually deleted by the operator on 2026-07-17T17:05:17Z
> (`gcloud storage rm`, confirmed via Cloud Audit Logs) — BEFORE this recovery plan's own STEP 1 ever executed — and is
> confirmed past GCS's 7-day soft-delete window (absent from the project's 39 currently soft-deleted buckets). The
> ~550,062 legacy-only keys this plan was designed to recover are permanently lost; there is nothing left to read. Full
> writeup + recommended next steps (confirm operator intent, re-assess whether STEP 4's T2.10 seed purge is
> independently actionable since it operates on the still-live index, not the deleted bucket):
> `issues/mdt_legacy_bucket_deleted_before_recovery_2026_07_25.md`.
