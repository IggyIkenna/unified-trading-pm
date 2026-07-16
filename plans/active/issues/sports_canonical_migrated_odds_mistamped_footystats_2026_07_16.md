---
doc_type: issue
title:
  The sports odds raw the recompute needs is ALREADY IN canonical — 16,969 ODDS_API objects mis-stamped
  `pipeline_mode=batch_footystats` and skipped by `reprocess_sports_odds.py` on a documented-but-false "redundant"
  assumption; canonical raw is NOT truncated and the legacy G1 merge is a DUPLICATION, not a recovery
summary:
  'Measured 2026-07-16 by the OR-5b G1 recovery leg, which was dispatched to execute the legacy→canonical G1
  read-split-merge and **refused it on measurement** (2nd independent refusal). **The dispatch premise — "the legacy MDT
  bucket is the ONLY COMPLETE RAW LAYER for 2022-03..2023-04" — is FALSE.** Canonical holds **16,969** `_migrated_`
  objects (2026-05-05 refactor) spanning **1,815 days**, and they are the G1 content: **30/30** sampled legacy G1
  objects are **row-identical and tick-key-identical** to their canonical migrated twin (0 legacy-only, 0 canon-only
  keys; `source` column == `ODDS_API` on both sides). Canonical migrated (1,815 days) is a **superset** of legacy G1
  (3,816 objects / 386 days). **Every one of the 16,969 is mis-stamped**: `pipeline_mode=batch_footystats` on
  16,969/16,969 while carrying `venue=ODDS_API` + `data_type=odds` + a `source` column of `ODDS_API` — **zero are
  footystats data**. Per `codex/02-data/pipeline-mode-partition.md` (`{mode}_{source}`, source=VENDOR) the correct stamp
  is `batch_odds_api`. **Why the recompute starves**: `reprocess_sports_odds.py` lists ONLY
  `pipeline_mode={batch_odds_api,live_odds_api}` prefixes and its `_is_consumable_trades_blob` is
  `name.endswith("ticks.parquet") and "_migrated_" not in name` — the migrated files are `ticks_migrated_*.parquet`
  under `batch_footystats/`, so they fail **both** filters. The skip is deliberate and documented
  (`scripts/reprocess_sports_odds.py:117-120`: _"deliberately skipped (redundant with the per-bookmaker shape above,
  which co-exists for the same historical dates)"_) — **and that redundancy claim is measurably false for the
  under-captured window**. day=2022-04-16: the consumable `batch_odds_api` population holds **5,626 rows / 5,226 tick
  keys / 81% at T-24h**; the migrated population holds **79,773 rows / 74,153 keys / the full 8-point horizon grid**
  (111 distinct `fetch_utc`). The migrated schema is **identical to the consumable schema** (22 of 23 columns; only
  `data_source` differs) and carries every adapter-required column (`bm_time`, `bm_minutes_to_kickoff`) plus real
  per-bookmaker `venue` values. **⇒ The features recompute is unblocked by a CODE fix in MDPS, not by a legacy recovery
  or a GCS migration.** The genuine legacy-only residue is unchanged and small: **550,062 keys on 32 days** (dominated
  by a canonical capture OUTAGE 2022-09-07…2022-10-01), corroborated independently here — **213/3,816** G1 objects have
  no canonical migrated twin, on **23** days, **22** of which are exactly the gate''s gap days. **MDT is NOT
  delete-eligible** until those 32 days are recovered. Zero mutations performed.'
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-data-processing-service, market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    sports,
    odds,
    data-correctness,
    pipeline-mode,
    bucket-canonicalisation,
    migration,
    re-derive,
    raw-truncation,
    cutover,
    investigation,
    read-only,
  ]
related:
  [
    ./sports_canonical_raw_truncated_rederive_destroys_corpus_2026_07_16.md,
    ./mdt_legacy_canonical_row_gap_2026_07_16.md,
    ./mdt_t2_6_league_case_duplicate_population_2026_07_16.md,
    ./sports_halftime_odds_sfi_vs_inplay_2026_07_16.md,
    ../sports_legacy_bucket_cutover_2026_07_16.md,
    ../../epics/sports_master.md,
  ]
created: 2026-07-16
last_updated: 2026-07-16
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
assigned_role: data
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source:
  [
    "OR-5b(a) G1 recovery leg dispatch 2026-07-16 — premise re-measured and refused",
    "./sports_canonical_raw_truncated_rederive_destroys_corpus_2026_07_16.md",
    "codex/02-data/pipeline-mode-partition.md",
  ]
---

# The odds raw is already in canonical — under the wrong `pipeline_mode`, behind a false "redundant" skip

> **NOTIFY-OPERATOR (data-correctness · cross-repo · SSOT contradiction · redirects a multi-leg effort).** **Zero
> mutations were performed by this leg.** No GCS object created, modified or deleted; no manifest shard written; no
> index touched. This doc exists because the mandated operation would have been a **mass duplication**, and because the
> real fix is ~4 lines in MDPS rather than a 16,969-object migration or a legacy-bucket recovery.

## The finding in one line

**Canonical is not missing the rich odds raw — it is holding it under `pipeline_mode=batch_footystats` with a
`ticks_migrated_*.parquet` filename, which is exactly the pair of things `reprocess_sports_odds.py` filters out.**

## Why this leg was dispatched, and why it refused

The dispatch (2026-07-16) carried this premise, inherited from the recompute leg:

> _"Each sports layer is RICHER THAN ITS OWN UPSTREAM … **The legacy MDT bucket is not a redundant copy. It is the ONLY
> COMPLETE RAW LAYER for that ~14-month window.** … Recovering G1 is therefore a PREREQUISITE for the blocked features
> recompute and any MDT delete."_

The dispatch also carried the standing instruction that saved this session four times: **"verify, do not inherit — 4
audits this session were wrong by inheriting."** Verified. The premise is false. **This is the second independent
refusal of the same merge** (the first, by the prior recovery leg, was right for a subtly different reason — see
"Reconciling the three legs").

## Evidence — measured live 2026-07-16, zero inherited numbers

### 1. The canonical `_migrated_` population IS the G1 content

| Measure                                               | Value                                                      |
| ----------------------------------------------------- | ---------------------------------------------------------- |
| canonical `_migrated_` raw objects                    | **16,969**                                                 |
| — carrying `pipeline_mode=batch_footystats`           | **16,969 / 16,969 (100%)**                                 |
| — carrying `venue=ODDS_API`                           | **16,969 / 16,969 (100%)**                                 |
| — carrying `data_type=odds`                           | **16,969 / 16,969 (100%)**                                 |
| — carrying `instrument_type=` (empty)                 | 16,967 (2 are `=odds`)                                     |
| canonical `batch_footystats` objects NOT `_migrated_` | **1**                                                      |
| days covered                                          | **1,815** (2020-06-06 … 2026-04-14)                        |
| legacy G1 old-shape objects                           | **3,816** on **386** days                                  |
| **G1 objects with a canonical migrated twin**         | **3,603 / 3,816 (94.42%)**                                 |
| **G1 objects WITHOUT a twin**                         | **213** on **23** days — all in the outage window          |
| **sampled G1 ↔ twin: tick-key-identical**             | **30 / 30** — 0 legacy-only keys, 0 canon-only keys        |
| **sampled G1 ↔ twin: row-count-identical**            | **30 / 30** (e.g. 98,298→98,298 · 83,971→83,971 · 315→315) |
| `source` column, both sides                           | **`ODDS_API` on 30/30** — **zero footystats data**         |

⇒ **Canonical's migrated population is a superset of legacy G1** (1,815 days vs 386). The legacy bucket carries nothing
unique on those days.

### 2. The mis-stamp is an SSOT violation, not a cosmetic one

`codex/02-data/pipeline-mode-partition.md` defines `pipeline_mode = {mode}_{source}` where **`source` is the VENDOR**.
These rows' own `source` column is `ODDS_API` on every sampled row ⇒ the correct stamp is **`batch_odds_api`**. They are
stamped **`batch_footystats`**. 16,969 objects assert a vendor they did not come from — a live data-correctness defect
independent of the recompute, and the direct cause of the prefix miss.

### 3. Why the recompute starves — read, not grepped

`market-data-processing-service/scripts/reprocess_sports_odds.py`:

```python
_CANONICAL_ODDS_PREFIX_TEMPLATES = [
    "raw_tick_data/by_date/day={date}/pipeline_mode=batch_odds_api/asset_group=sports/",
    "raw_tick_data/by_date/day={date}/pipeline_mode=live_odds_api/asset_group=sports/",
]                                    # <- batch_footystats is NOT listed

def _is_consumable_trades_blob(name: str) -> bool:
    return name.endswith("ticks.parquet") and "_migrated_" not in name   # <- excluded twice over
```

The migrated objects are `.../pipeline_mode=batch_footystats/.../ticks_migrated_20260505T160406Z.parquet` — they fail
the prefix list **and** both clauses of the filename predicate. They are invisible, not rejected.

**The skip is deliberate and its stated reason is false** (`reprocess_sports_odds.py:117-120`):

> _"Legacy migration artifacts (2026-05-05 per-shard refactor): filename `*_migrated_*.parquet` under
> `venue=ODDS_API/.../data_type=odds/` — **deliberately skipped (redundant with the per-bookmaker shape above, which
> co-exists for the same historical dates)**; NOT treated as 'unrecognized'."_

The per-bookmaker shape does co-exist — but for the under-captured window it is a **de-duplicated remnant**, not an
equivalent.

### 4. The two populations on the disputed day (`day=2022-04-16`)

| Population                                       | Objects | Rows       | Tick keys  | distinct `fetch_utc` | Horizon coverage                       |
| ------------------------------------------------ | ------- | ---------- | ---------- | -------------------- | -------------------------------------- |
| canonical `batch_odds_api` (**what MDPS reads**) | 207     | **5,626**  | **5,226**  | 88                   | **81% sits at T-24h**; 26–99 elsewhere |
| canonical `batch_footystats` `_migrated_`        | 17      | **79,773** | **74,153** | 111                  | **full 8-point grid**                  |

`minutes_to_kickoff` histogram (pre-match rows, minutes):

| bucket     | 0–10  | 10–60 | 60–120 | 120–240 | 240–360 | 360–720 | 720–1440 | 1440+     |
| ---------- | ----- | ----- | ------ | ------- | ------- | ------- | -------- | --------- |
| migrated   | 4,299 | 5,455 | 6,658  | 11,727  | 11,100  | 17,315  | 13,705   | 9,362     |
| consumable | 26    | 78    | 66     | 48      | 68      | 84      | 99       | **4,544** |

This is an **exact match** for the recompute leg's measured re-derive (T-24h reproduces at 317 rows;
T-12h/6h/4h/2h/1h/10m all yield **0**). The consumable population retains ~one quote per tick and almost only the T-24h
wave; the horizon grid lives **only** in the migrated population.

### 5. The migrated population is fully consumable — the schema already fits

| Check                                                | Result                                                                                                             |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| adapter-required `bm_time` / `bm_minutes_to_kickoff` | **present** in migrated                                                                                            |
| columns in consumable but NOT migrated               | **`data_source` only** (1 of 23)                                                                                   |
| columns in migrated but NOT consumable               | **none**                                                                                                           |
| `venue` column values                                | real bookmakers (`betonlineag`, `betrivers`, `draftkings`, `fanduel`…)                                             |
| `instrument_id` format                               | UAC `build_instrument_id` — `FOOTBALL:LIVESCOREBET:OVER_UNDER_2_5:PREMIER_LEAGUE:2022-23:TOTTENHAM-BRIGHTON::OVER` |

It is **not** the coarse `ODDS_API:SPORT:*` meta shape the module comment describes as unconsumable. It is the same
schema, denser.

## Reconciling the three legs — all three measured correctly; two mis-diagnosed

| Leg                 | Claim                                                             | Verdict                                                                                        |
| ------------------- | ----------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| OR-5b investigation | "6.37M genuine pre-match rows missing from canonical"             | **artifact** — ROWS not KEYS, PER-PAIR not WHOLE-DAY (as its own banner says)                  |
| OR-5b recovery leg  | "canonical holds 98.77% of every legacy key ⇒ nothing to recover" | **right, and its refusal was correct** — but it concluded the recompute had no problem         |
| recompute leg       | "canonical raw is truncated 14.2× ⇒ recover from legacy"          | **right that MDPS starves; wrong about why** — the rows are in canonical, under another prefix |

The recovery leg's delete gate read **all** canonical objects for a day (including the migrated ones) and correctly
found `pre_only=0`. MDPS reads **only** the `batch_odds_api` prefix and correctly found itself starving. Both are true.
The missing link is that **the two populations are not the same population** — which is exactly what the `_migrated_`
skip assumes away.

The gate's own arithmetic corroborates it on `day=2022-04-16`: `canon_keys` **77,769** == `legacy_pre_keys` **74,001** +
`legacy_inplay_keys` **3,768**, exactly. Canonical's keyset for that day _equals_ legacy's — because 17 of its 224
objects **are** legacy's objects.

## The genuine legacy-only residue — independently corroborated

The recovery leg's exhaustive gate (all 1,837 legacy tick-days, ~900k reads, 0 errors) stands **unchallenged**:

| Measure                            | Value                                                                                                       |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| legacy-only PRE-MATCH keys         | **524,486** (1.2456%)                                                                                       |
| legacy-only IN-PLAY keys           | **25,576** (1.0058%)                                                                                        |
| **total genuine legacy-only keys** | **550,062 (1.23%)**                                                                                         |
| days with ANY legacy-only key      | **32 of 1,837** — 1,805 at exactly 0                                                                        |
| dominant cause                     | canonical capture **OUTAGE 2022-09-07…2022-10-01** (21 days; 2022-10-01: legacy 104,868 vs canonical 8,849) |

**This leg corroborates it from a completely independent direction**: the **213** G1 objects with no canonical migrated
twin sit on **23** days, and **22 of those 23 are exactly the gate's gap days** (the exception, 2022-09-08, has
`pre_only=0` — canonical got that day from the other population). The 10 remaining gap days carry only a small tail
(54–516 keys each, ~2,004 total). Two independent methods, one answer.

## What must NOT happen

- **Do NOT execute the OR-5b(b) option-D G1 legacy→canonical read-split-merge.** It would copy content canonical already
  holds (94.42% of G1 has an identical twin), writing ~15.7M duplicate rows. Refused twice now, on independent evidence.
- **Do NOT delete `market-data-tick-sports`.** 550,062 keys on 32 days exist only there.
- **Do NOT run `reprocess_sports_odds.py --force` over historical dates** until the loss guard lands — the hazard the
  recompute leg documented is real and unchanged; only its cause is restated.

## Fix direction (not implemented here — MDPS is owned by the recompute leg; annotated, not edited)

- **(a) [MDPS, P0] Make the migrated population consumable — this alone unblocks the features recompute.** Add
  `raw_tick_data/by_date/day={date}/pipeline_mode=batch_footystats/asset_group=sports/` to the prefix list and treat
  `ticks_migrated_*.parquet` under `venue=ODDS_API/.../data_type=odds/` as **consumable**, unioning it with the
  per-bookmaker shape (de-dup on the tick key; the migrated set is a superset on the affected dates). Delete the false
  "redundant" comment at `:117-120` with it. **No GCS migration required.**
- **(b) [MDPS, P0] The per-date loss guard still lands** (already this issue's sibling todo) — defence in depth. With
  (a) the derive stops starving; the guard stops the _next_ unknown starvation from deleting a corpus.
- **(c) [MDT, P1] Correct the mis-stamp at the source.** 16,969 objects assert `pipeline_mode=batch_footystats` for
  ODDS_API data, violating `{mode}_{source}`. A re-stamp to `batch_odds_api` (read-split-merge into the canonical cells
  using the OR-5b(a) derivation map — `venue := instrument_id[1].upper()`, `league_id := instrument_id[3]`, both
  re-validated at 100.0000% by the prior leg) makes (a) unnecessary and the corpus honest. **This is the durable fix but
  it is a large mutation** — do it deliberately, pilot-first, MERGE-not-overwrite, not as a side effect of unblocking a
  recompute. Sequence it AFTER (a) has unblocked the recompute.
- **(d) [MDT, P0] The 32-day recovery is the real delete gate.** Day-scoped, ~213 twin-less G1 objects + ~1,737 class-B
  objects on 32 days / 550,062 keys. This is the only legacy→canonical recovery that recovers anything.

## Todos

- [ ] [CODE] P0. **[MDPS] Consume the `batch_footystats` `_migrated_` population** (fix (a)) — add the prefix, flip the
      `_migrated_` skip to a union with tick-key de-dup, delete the false "redundant" comment at
      `reprocess_sports_odds.py:117-120`. Verify on `day=2022-04-16`: the derive must reproduce all 8 horizons
      (T-12h=896, T-6h=898, T-4h=896, T-2h=884, T-1h=270, T-10m=870, T-24h=317) instead of T-24h only.
- [ ] [DATA] P0. **Quantify the consumable-vs-migrated split across all 1,815 migrated days** — establish exactly which
      dates depend on the migrated population (single walk; both inventories are already cached in `~/tmp-or5b/`).
      Supersedes the truncation doc's "quantify the raw truncation" todo, which is framed on the wrong axis
      (canonical-vs-legacy rather than consumable-vs-migrated **within** canonical).
- [ ] [DATA] P0. **Recover the 32 gap days from legacy** (fix (d)) — the only genuine legacy→canonical recovery; the MDT
      delete gate. Day-scoped, key-level verified, MERGE-never-overwrite.
- [ ] [DATA] P1. **Re-stamp the 16,969 mis-stamped objects to `batch_odds_api`** (fix (c)) — pilot-first, after (a).
- [ ] [DOCS] P1. **Correct the cutover runbook's OR-5b block** — the residue is a 32-day recovery; the G1 generation
      recovery is refused twice and must not be re-proposed.

## Progress Log

**2026-07-16 — G1 recovery leg: merge REFUSED on measurement (2nd independent refusal). Zero mutations.** Dispatched to
execute the legacy→canonical G1 read-split-merge on the premise that the legacy bucket is the only complete raw layer.
Re-measured before writing, per the standing never-inherit rule. Sequence (`~/tmp-or5bg1/`):

1. **Read the dispatch's own primary source** — `mdt_legacy_canonical_row_gap_2026_07_16.md` already carried a
   `SUPERSEDED IN PART` banner voiding the 6.37M headline the dispatch was built on. The dispatch inherited the
   pre-banner numbers.
2. **`day_anatomy.py` on `day=2022-04-16`** (the day the dispatch cites): reproduced the recompute leg's 5,626 vs 79,773
   exactly — then found the 79,773 also present **inside canonical**, at `pipeline_mode=batch_footystats` with a
   `_migrated_` filename (17 objects, sizes matching the legacy originals).
3. **`mistamp_proof.py`** (30 sampled G1 objects, full reads both sides): **30/30 row-identical and tick-key-identical**
   to their canonical migrated twin; 0 legacy-only, 0 canon-only keys; `source == ODDS_API` on both sides of all 30.
   **213/3,816** G1 objects have no twin, on 23 days — 22 of which are exactly the gate's 32 gap days.
4. **Inventory census**: 16,969 canonical `_migrated_` objects, **100%** `batch_footystats` + `venue=ODDS_API` +
   `data_type=odds`; **zero** footystats data; 1,815 days.
5. **Read the consumer** (grep-then-READ): `_CANONICAL_ODDS_PREFIX_TEMPLATES` omits `batch_footystats`;
   `_is_consumable_trades_blob` excludes `_migrated_`. Doubly invisible. The skip's stated reason ("redundant") is false
   for the under-captured window.
6. **Schema check**: migrated carries every adapter-required column; 22/23 columns identical to the consumable shape
   (only `data_source` differs); real per-bookmaker `venue` values; UAC-format `instrument_id`. Fully consumable.
7. **Merge REFUSED** — it would duplicate ~15.7M rows canonical already holds. No object created, modified or deleted;
   no manifest shard written (`or5b-g1-20260716` does not exist — a shard must describe real recovered cells, and there
   are none); no index snapshot needed (nothing was to be written).

**Net effect**: the blocked features recompute needs a ~4-line MDPS change, not a bucket recovery. MDT stays
NOT-delete-eligible on a 32-day / 550,062-key residue — unchanged, and now corroborated twice.
