---
doc_type: issue
title:
  T2.6's 6,110-object MDT "class-A move" is a pure DUPLICATE population — the strip key was case-blind, so 6,110 objects
  already present in canonical under the UPPERCASE league_id representation were re-copied under the lowercase one;
  proven content-identical 6,110/6,110 (12,220 full reads, 0 errors); 0 rows recovered
summary:
  'Cutover-INTRODUCED defect found by the OR-5b(a) recovery leg 2026-07-16 while re-validating the G1 derivation map.
  T2.6 classified 6,110 legacy MDT objects as "class A — no canonical counterpart" using the strip key
  `re.sub(/pipeline_mode=[^/]+/) + re.sub(/data_source=[^/]+/)`, which is **case-sensitive on the `league_id=`
  segment**. Canonical''s native `league_id` vocabulary is UPPERCASE (252,164 objects); the legacy objects carry the raw
  lowercase `soccer_*` form. So every legacy `league_id=soccer_epl` object failed to pair with canonical''s
  `league_id=SOCCER_EPL` object, was called class A, and was copied into canonical — creating a second, lowercase
  representation of data canonical already held. **EXACT proof over all 6,110 pairs (12,220 full parquet reads, 0
  errors): 6,110/6,110 = 100.0000% identical tick-key sets on (event_id, market_key, outcome_name, bm_time, price); 0
  lowercase-only ticks; 0 uppercase-only ticks; identical row counts.** The 6,110 lowercase-league canonical objects are
  EXACTLY T2.6''s dst set (set equality verified both directions). Consequences: (1) canonical MDT carries 6,110
  duplicate objects on 22 days (2025-07-31…2025-12-31); (2) T2.7''s MDT per-VM shard (6,110 rows,
  `VM_NAME=cutover-move-20260716`) describes them and will land them in the index at T6.1; (3) T2.6''s headline "6,110
  moved, 305,000+ rows recovered" is **0 rows recovered**. Related: the same case-blindness is why the OR-5b
  investigation''s cell census double-counted (99,414 vs the measured 49,707). NOT fixed here — this leg authorises no
  deletions.'
status: resolved
nature: issue
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm, market-tick-data-service]
scope: [engineer, admin]
tags: [sports, migration, bucket-canonicalisation, data-correctness, gcs, manifest, duplicates, odds, investigation]
related:
  [
    ../sports_legacy_bucket_cutover_2026_07_16.md,
    ./mdt_legacy_canonical_row_gap_2026_07_16.md,
    ../../epics/sports_master.md,
  ]
created: 2026-07-16
last_updated: 2026-07-16
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
assigned_role: data
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
  "Option A executed — plans/archive/2026_07/sports_master_closeout_2026_07_21.md:694-697 (6,110 lowercase-twin
  duplicate GCS objects deleted, crc-verified) +
  plans/archive/2026_07/sports_master_closeout_progress_log_2026_07_24.md:399-429 (phantom soccer_* manifest-row prune,
  6,110/6,110 verified stale_remaining=0)"
source: ["OR-5b(a) recovery leg 2026-07-16 — re-validation of the G1 derivation map"]
---

# T2.6's 6,110 "class-A moves" are duplicates — a case-blind strip key

> **READ-ONLY finding. Zero mutations** — nothing was deleted or rewritten. The 6,110 duplicate objects and their 6,110
> staged manifest rows are still in place, awaiting a ruling.

| Bucket    | Name                                                 |
| --------- | ---------------------------------------------------- |
| Legacy    | `market-data-tick-sports-central-element-323112`     |
| Canonical | `market-data-tick-sports-prd-central-element-323112` |

## The defect

T2.6 paired legacy↔canonical MDT objects on

```python
key = re.sub("/pipeline_mode=[^/]+/", "/", re.sub("/data_source=[^/]+/", "/", name))
```

This key is **case-sensitive on every surviving segment**, including `league_id=`. But the two buckets do not agree on
that segment's representation:

| Representation                     | Canonical objects | Provenance                            |
| ---------------------------------- | ----------------- | ------------------------------------- |
| `league_id=SOCCER_EPL` (UPPERCASE) | **252,164**       | native — canonical's real convention  |
| `league_id=soccer_epl` (lowercase) | **6,110**         | **created by T2.6's own move, today** |

So a legacy object at `league_id=soccer_epl` never matched canonical's `league_id=SOCCER_EPL` object holding the same
rows. It was classified **class A ("no canonical counterpart → derivable → MOVE")** and copied in.

## The proof — exact, not sampled

`~/tmp-or5b/or5b_t26_dup_proof.py`, evidence `~/tmp-or5b/or5b_t26_dup_evidence.jsonl`.

1. **The lowercase population IS T2.6's output.** Set equality against `t2_6_move_evidence.jsonl` (status=COPIED):
   `lowercase_set == t2_6_dst_set` → **True**; `lowercase − t2_6_dst = 0`; `t2_6_dst − lowercase = 0`.
2. **Every one has a native uppercase twin.** Grouping canonical on `(day, venue, league_id.upper())` yields **6,110**
   cells holding BOTH a lowercase and an uppercase object.
3. **Every twin is content-identical.** EXACT pass over all 6,110 pairs — **12,220 full parquet reads, 0 errors** — on
   the tick-identity key `(event_id, market_key, outcome_name, bm_time, price)`:

| Measure                            | Value                         |
| ---------------------------------- | ----------------------------- |
| pairs with IDENTICAL tick-key sets | **6,110 / 6,110 = 100.0000%** |
| total lowercase-only ticks         | **0**                         |
| total uppercase-only ticks         | **0**                         |

Sampled row counts agree exactly too (e.g. 2025-09-04 BOVADA SOCCER_DENMARK_SUPERLIGA: 42 vs 42, shared 42). Both sides'
`league_id` **column** carries the raw lowercase form regardless — only the PATH segment differs, which is precisely why
this is a representation artifact and not a data difference.

## Consequences

1. **Canonical MDT holds 6,110 duplicate objects** across 22 days (2025-07-31 … 2025-12-31).
2. **T2.7's MDT shard (6,110 rows, `_index/per_vm/cutover-move-20260716.parquet`) describes the duplicates.** At T6.1 it
   will merge them into the index. The runbook's expected MDT delta (`+526 new / 5,584 corrected`) is therefore a
   projection about **duplicate** cells. The shard is deliberately unmerged today — **this must be settled before
   T6.1**, which is the last safe moment.
3. **T2.6's recovery claim is void**: the move recovered **0 rows**. Its gate ("total rows recovered ≥ 305,000") was
   never a data-recovery measure — it counted rows in objects canonical already had.
4. **The same case-blindness propagated into the OR-5b investigation**, whose target-cell census reports 99,414 cells
   (exactly 2× the measured 49,707) — one phantom cell per real cell.

## This is the OR-1 / OR-9 pattern, a third time

OR-9 exists because "option D enumerated only the 5 largest entities and the rest silently inherited superseded". Here a
**path-string** key stood in for a **content** comparison, and 6,110 objects silently inherited "unique". The workspace
rule this violates is already written down: _re-measure at the key/object layer; never inherit a classification from a
path-shaped proxy._

## Disposition — needs a ruling (BLOCKS T6.1 for the MDT shard)

- **A: delete the 6,110 duplicate lowercase objects and drop the 6,110 rows from T2.7's MDT shard before T6.1 [WORKER
  REC]** — restores canonical to its native single representation; provably lossless (0 lowercase-only ticks). Requires
  a deletion mandate, which the discovering leg did not have.
- **B: keep the objects, but drop/repoint the 6,110 shard rows** — leaves 6,110 duplicate objects on disk but keeps the
  index honest (one cell, one representation).
- **C: keep both and register the lowercase representation as legitimate** — contradicts canonical's 252,164-object
  native convention and permanently doubles those cells.
- Other.

> Whichever is chosen, **the legacy source objects are unaffected** — this is purely about the 6,110 copies T2.6 wrote
> into canonical today and the 6,110 manifest rows staged to describe them.

## Progress Log

**2026-07-16** — Found by the OR-5b(a) recovery leg while re-validating the G1 derivation map against canonical's real
`league_id` vocabulary (the leg needed to know which representation to write into, and discovered canonical had two).
Proven exactly over all 6,110 pairs (12,220 reads, 0 errors), both directions of set equality plus content identity.
Zero mutations performed. Filed for a ruling; blocks the MDT half of T6.1.
