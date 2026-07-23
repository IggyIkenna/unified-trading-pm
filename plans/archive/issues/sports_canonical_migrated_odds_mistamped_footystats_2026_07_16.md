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
  footystats data**. Per `/codex/02-data/pipeline-mode-partition.md` (`{mode}_{source}`, source=VENDOR) the correct
  stamp is `batch_odds_api`. **Why the recompute starves**: `reprocess_sports_odds.py` lists ONLY
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
last_updated: 2026-07-17
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
    "/codex/02-data/pipeline-mode-partition.md",
  ]
---

# The odds raw is already in canonical — under the wrong `pipeline_mode`, behind a false "redundant" skip

> # 🟢 RESOLVED IN PART 2026-07-17 — the read-split-merge is EXECUTED and the FEATURES RECOMPUTE IS UNBLOCKED.
>
> `market-tick-data-service@75f226e8` merged the migrated population into the canonical `batch_odds_api` cells on the
> **199 days** where it changes anything (exhaustively scoped: 1,336/1,815 days were pure duplicates). **6,304,585 rows
> added, 0 lost, 0 errors.** Acceptance PASSES through the **UNCHANGED** MDPS reader + adapter (`day=2022-04-16`: raw
> 5,626→83,916; T-12h=896 · T-6h=898 · T-4h=896 · T-2h=884 · T-1h=270 · T-10m=870 all EXACT; T-24h=894 richer). Manifest
> rows for those days are correct + absorbed (41,753 rows, 100.00% present in the live index).
>
> **Still open**: the **purge** of the 42,476 mis-stamped manifest rows + 16,969 now-provably-redundant objects. The
> doc's "move the manifest rows, 0 collisions ⇒ a clean move" is **FALSIFIED** (it compared `venue=ODDS_API` vs
> `venue=BOOKMAKER`, which cannot collide; after the derivation 56.40% of cells already exist ⇒ a move would DUPLICATE).
> See § Progress Log 2026-07-17 (final).
>
> _(Superseded banners retained below for provenance.)_
>
> **🔴 the "~4 lines in MDPS" framing below is SUPERSEDED by an operator ruling.** Operator, 2026-07-16/17 (verbatim):
> _"i think footystats is IS odds api is mtds both iodds different places"_ ⇒ **fix (a) is REJECTED** (teaching MDPS to
> read `batch_footystats` would hard-code the SSOT violation into the consumer); **fix (c) — correct the objects — is
> THE ruling.** The 2026-07-17 leg then measured that fix (c) is **not a "re-stamp" at all but a read-split-merge**
> (different venue semantics / league key / instrument_type / data_type / filename), so a size-or-crc-verified copy is
> impossible by construction. Blast radius is **green** (no consumer reads `batch_footystats` on the MTDS raw-tick
> surface) and the union arithmetic is **proven** (strict superset of both; an overwrite destroys 184 canonical-only
> keys/day). See § Progress Log 2026-07-17 for the corrected execution spec.
>
> _(Original 2026-07-16 banner, retained for provenance:)_ **NOTIFY-OPERATOR (data-correctness · cross-repo · SSOT
> contradiction · redirects a multi-leg effort).** **Zero mutations were performed by this leg.** No GCS object created,
> modified or deleted; no manifest shard written; no index touched. This doc exists because the mandated operation would
> have been a **mass duplication**, and because the real fix is ~4 lines in MDPS rather than a 16,969-object migration
> or a legacy-bucket recovery.

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

`/codex/02-data/pipeline-mode-partition.md` defines `pipeline_mode = {mode}_{source}` where **`source` is the VENDOR**.
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
- [x] [DATA] P0. ✅ **Quantify the consumable-vs-migrated split across all 1,815 migrated days** — DONE 2026-07-17,
      exhaustive (all 1,815 days, real reads + real adapter, **0 errors**), reusing the cached `~/tmp-or5b/` inventory
      (no new whole-corpus walk). **Result: 1,336 days (73.6%) migrated is FULLY redundant (`mig_keys == can_keys`
      exactly) · 280 (15.4%) add raw keys but ZERO derive rows · 199 (11.0%) a REAL derive gain (742,504 rows) · 0 days
      lose anything.** Gain window 2020-06-14…2024-08-03, concentrated in 2022 (112 days) / 2023 (48) / 2024 (34). Also
      found: 3 mixed-schema-family days, 1 day with no canonical objects. This is what collapsed the merge scope by
      85.6% (2,731+33,920 objects vs 254,871). Evidence: `market-tick-data-service@75f226e8`.
- [ ] [DATA] P0. **Recover the 32 gap days from legacy** (fix (d)) — the only genuine legacy→canonical recovery; the MDT
      delete gate. Day-scoped, key-level verified, MERGE-never-overwrite.
- [x] [DATA] P1. ✅ **Re-stamp the 16,969 mis-stamped objects to `batch_odds_api`** (fix (c)) — SUPERSEDED-AND-DONE in
      the form that matters: it was never a re-stamp but a **read-split-merge**, executed pilot-first on the 199 days
      where it changes anything (`market-tick-data-service@75f226e8`). The other 1,616 days hold content canonical
      already has under the correct stamp, so re-homing them moves nothing — what remains for them is the **purge** todo
      above, not a re-stamp.
- [ ] [CODE] P2. **Reconsider the `_migrated_` exclusion in `reprocess_sports_odds.py` once the purge lands.** It is
      currently unreachable for these objects anyway (they live under `batch_footystats`, a prefix the reader never
      lists), so it is dead code w.r.t. them — but it stays until the purge removes the population, as defence in depth.
      Removing it earlier would re-open option (a), which the operator rejected.
- [ ] [DOCS] P1. **Correct the cutover runbook's OR-5b block** — the residue is a 32-day recovery; the G1 generation
      recovery is refused twice and must not be re-proposed.

## Progress Log

**2026-07-17 (final) — ✅ EXECUTED. 199 days merged, 6,304,585 rows added, 0 lost, acceptance PASSES on the REAL
reader+adapter. The features recompute is UNBLOCKED.**

Tool: `market-tick-data-service@75f226e8` → `scripts/merge_migrated_odds_into_canonical_2026_07_17.py`.

| stage                          | result                                                                                                                  |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------------- |
| scope (exhaustive, 1,815 days) | **199** gain days (11.0%) · 1,336 (73.6%) pure duplicates · 280 add raw keys but 0 derive rows · **0 errors**           |
| pilot `day=2022-04-16`         | dry-run `rows_added=78,290` == the independently-measured migrated-only key count **exactly**; 207 cells, 0 created     |
| **apply (199 days)**           | **26,264 cells written · 7,911 created · 15,282 skipped (no new keys) · 6,304,585 rows added · 0 errors · 0 rows lost** |
| manifest                       | **41,753** rows, all `batch_odds_api`/`odds_api`/`trades`/`captured`, 199/199 days, 0 dup cells                         |
| manifest absorbed              | consolidator folded the shard in <30s; **41,753/41,753 (100.00%)** of my cells present in the live index, 0 missing     |
| **ACCEPTANCE (real derive)**   | ✅ **PASS** — see below                                                                                                 |

**The acceptance test, run through the REAL `reprocess_sports_odds._read_raw_odds` + the REAL adapter** (not a
simulation) on `day=2022-04-16`: raw **5,626 → 83,916** rows.

| horizon | corpus | derived now | verdict                     |
| ------- | ------ | ----------- | --------------------------- |
| T-12h   | 896    | **896**     | ✅ EXACT                    |
| T-6h    | 898    | **898**     | ✅ EXACT                    |
| T-4h    | 896    | **896**     | ✅ EXACT                    |
| T-2h    | 884    | **884**     | ✅ EXACT                    |
| T-1h    | 270    | **270**     | ✅ EXACT                    |
| T-10m   | 870    | **870**     | ✅ EXACT                    |
| T-24h   | 317    | **894**     | ✅ RICHER (+577)            |
| T-0     | 27 val | **27**      | ✅ = the leak-filtered rows |

Re-verified on the largest gain days too (2023-04-01: 149,782 raw → 14,962 bucketed, every horizon ~2,100; 2022-04-02:
110,637 raw → 8,298 bucketed). **The MDPS reader is UNCHANGED** — it sees the rich population because the objects are
now in the right place. That is exactly the operator's ruling: fix the DATA, not the reader.

**A bug I introduced and repaired (recorded so it is not repeated).** The first revision accumulated manifest rows in
memory and uploaded the shard once at the end of `main()`; every `timeout`-killed chunk therefore lost its rows, leaving
**96 of 153** merged days with objects but no manifest row — an index/data desync, and the 7,911 newly-created cells
would have been phantom. Repaired by a `--manifest-only` pass that recomputes every row from the CURRENT live object
(independent of which chunk wrote what) and flushes per-day to a local jsonl. Verified 100.00% present. The tool now
flushes per-day by construction and the docstring forbids re-introducing an end-of-run-only upload.

### ⚠️ NOT done — and why (the manifest re-stamp is MIS-SPECIFIED, a 4th falsification)

The doc's todo _"Move the manifest rows WITH the objects — 42,476 rows / 2,128 days; **0 cell-key collisions ⇒ a clean
move**"_ **cannot be executed as written.** The "0 collisions" was measured between `venue=ODDS_API` rows and
`venue=BOOKMAKER` rows — those can **never** collide, the venue differs by construction. Measured on the live index
after applying the derivation (`venue := bookmaker`):

| measure                                                            | value                                                                                                                                                                   |
| ------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `batch_footystats` rows                                            | 42,476 — but only **22,145** distinct case-normalised cell keys ⇒ the manifest is **itself ~2× duplicated** (`ODDS` 22,145 / `odds` 20,331), mirroring the object layer |
| footystats `(date, league)` that ALREADY exist in `batch_odds_api` | **12,490 / 22,145 (56.40%)** — a 1:1 move would create **duplicate** manifest rows                                                                                      |
| footystats-only `(date, league)`                                   | 9,655 (9,605 case-normalised) — implies manifest INCOMPLETENESS vs objects, a separate defect                                                                           |

⇒ The correct operation is a **de-cased purge of the 42,476 mis-stamped rows once their objects are gone**, not a move.
It is now safe to specify, because the merge has made the `batch_footystats` population **provably redundant by
construction** on the 199 days that mattered (and it was already redundant on the other 1,616). Sequenced as a todo
below rather than forced on a spec measured to be wrong.

**2026-07-17 (earlier) — EXECUTION leg: the merge is PROVEN CORRECT IN SIMULATION, and the SCOPE COLLAPSES ~88%. Three
inherited claims falsified. Zero mutations so far.**

Every number below is measured live this session; nothing inherited. Scratch: `~/tmp-splitmerge/`.

### 1. ✅ The prior leg's pilot arithmetic REPRODUCES exactly

Independent re-read of both populations on `day=2022-04-16`: migrated 17 objects / **167,464** rows · canonical 207
objects / **5,626** rows · derivation `venue := instrument_id[1].upper()` **100.0000% (167,464/167,464)** · union
**83,916** · canonical-only **184** · migrated-only **78,290** · schema diff = `data_source` only. **Confirmed.**
Additionally: the union is **invariant** under poll-key vs tick-identity-key and under venue case ⇒ those numbers are
robust, not artifacts.

### 2. 🔴 THE ACCEPTANCE TEST IS ALREADY ANSWERED — no GCS mutation needed to evaluate it (the doc said it required one)

The doc states the grid "cannot be checked by row arithmetic … requires **running the MDPS derive** over the merged
cells, which cannot precede the merge." **That is false.** `reprocess_date` calls
`adapter.process_to_bucketed_df(raw_df)` — a **pure function of the raw DataFrame**. So the derive can be run locally on
a merged DataFrame with **zero writes** (`~/tmp-splitmerge/simulate_derive.py`).

**The simulation is VALIDATED against ground truth**: canonical-alone reproduces the known measured baseline **T-24h=317
and 0 on every other horizon** — exactly what the truncation doc measured from a live `--force` run. A simulation that
reproduces the real derive's known output is faithful.

| horizon | acceptance (corpus) | merged derive | verdict                          |
| ------- | ------------------- | ------------- | -------------------------------- |
| T-12h   | 896                 | **896**       | ✅ exact                         |
| T-6h    | 898                 | **898**       | ✅ exact                         |
| T-4h    | 896                 | **896**       | ✅ exact                         |
| T-2h    | 884                 | **884**       | ✅ exact                         |
| T-1h    | 270                 | **270**       | ✅ exact                         |
| T-10m   | 870                 | **870**       | ✅ exact                         |
| T-24h   | 317                 | **894**       | ✅ strictly RICHER (+577)        |
| T-0     | 338 (27 valid)      | **27**        | ✅ = the 27 valid (MDPS@3bf56ff) |

**⇒ The merge reproduces 6/7 horizons exactly, is strictly richer on the 7th, and loses nothing.** The gate is met
**before** any mutation.

### 3. 🔴 FALSIFIED — the migrated population is internally **2× DUPLICATED** (not reported by any prior leg)

167,464 rows carry only **83,732** distinct keys — exactly 2×. Mechanism: the 17th object (the bare
`data_type=odds/ticks_migrated_*.parquet`, **no `league=` segment**) holds the **same 83,732 ticks** as the 16 league
objects, with `league_id` **NULL**. Same migration timestamp. The 2× ratio holds in **every** horizon bucket
(10,214→5,107 · 11,082→5,541 · 18,948→9,474 · 24,594→12,297 · 28,572→14,286 · 11,512→5,756 · 11,126→5,563). The doc's
"167,464 rows" headline overstates the real payload by 2×; the true payload is **83,732 ticks**. **De-dup on write is
mandatory** (the adapter's own dedup masks this at the derive layer, so it was invisible to every prior leg).

### 4. 🔴 FALSIFIED — canonical has **≥2 SCHEMA FAMILIES**, and one has NO `venue` column

The doc's "the migrated schema is identical to the consumable schema (22 of 23 columns; only `data_source` differs)" is
true **only on family-A days**. Measured: `day=2023-01-15` — **all 165** canonical consumable objects carry
`available_at`/`bookmaker_key`/`fixture_id` and **NO** `venue`/`instrument_type`/`data_source` (family B), at the _same_
path shape. **8 of 42** sampled days (19%) hit this. This corroborates [[mdt_legacy_canonical_row_gap_2026_07_16]] §
schema census (4 families; the trio in only 13.4% of cells) — but that was never carried into the merge spec. **A
`venue`-bearing merge key is broken by construction on family-B days.**

**Fix (measured, not assumed)**: `venue == instrument_id[1].lower()` at **100.0000%** in BOTH populations ⇒ `venue` is
redundant in the key. The family-agnostic key `(instrument_id, fetch_utc, price, bm_time)` reproduces the pilot day's
arithmetic **EXACTLY** (83,732/5,626/83,916/184/78,290). That is the key the execution must use.

### 5. 🔴 THE SCOPE COLLAPSES ~88% — most days do NOT need the merge

Cached-inventory scoping (no new whole-corpus walk) reproduces the doc exactly: **16,969** migrated objects / **1,815**
object-days / **1** non-migrated `batch_footystats` object. But a 42-day stratified probe (real reads + real derive,
read-only) finds:

| result                               | days                                                        |
| ------------------------------------ | ----------------------------------------------------------- |
| migrated adds **0** raw keys         | **30 / 34** clean days — `mig_keys == can_keys` **EXACTLY** |
| migrated **adds** keys ⇒ needs merge | **4 / 34** — 2022-04-16, 2022-10-07, 2023-03-05, 2024-04-24 |
| merge **loses** derive rows          | **0 / 34**                                                  |

On the redundant days the migrated keyset **equals** canonical's (6,899==6,899 · 45,768==45,768 · 148,087==148,087 …) —
i.e. canonical already holds that content under the CORRECT stamp, and the `batch_footystats` copy is a pure duplicate.
**Merging those days is ~238k object rewrites for ZERO gain** — churn on a live bucket, not a fix. The doc's P0 todo
"quantify the consumable-vs-migrated split across all 1,815 migrated days" is therefore **load-bearing and must complete
before the merge** — it is now in flight (full 1,815-day probe, read-only, resumable).

**Consequence for the manifest**: the 42,476 mis-stamped rows are wrong on EVERY day, but the correct remedy is **not
uniform** — a day whose migrated objects are pure duplicates wants those objects (and their rows) REMOVED, not moved. A
blanket "move the manifest rows with the objects" would re-home 16,969 objects of which ~88% are duplicates.

**2026-07-17 — RE-STAMP leg (operator ruling = option B, fix the STAMP not the reader). Blast radius COMPLETE. The
"re-stamp" is MIS-SPECIFIED: it is a read-split-merge. Zero mutations to GCS/manifest.**

The operator's architecture ruling is CONFIRMED and independently corroborated in code — but the operation it implies is
**not a re-stamp**, and the dispatch's own acceptance criteria are unachievable as written. Measured, nothing inherited.

### 1. Blast radius — NO consumer depends on the wrong stamp (the re-stamp is reader-safe)

| consumer                                                            | verdict                                                                                                                                                            |
| ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `reprocess_sports_odds.py` (MDPS)                                   | cannot see them (prefix + `_migrated_` filter) — the thing being fixed                                                                                             |
| `reconcile_phantom_manifest_rows_all.py` `ticks_migrated_` wildcard | **DeFi-ONLY** (`if asset_group == "defi" and venue and chain`) — sports unaffected                                                                                 |
| `reconcile_phantom_manifest_rows_all.py` `prefix_tpls`              | SSOT-derived post-Axis-10 (probes ALL `batch_*` modes) — moves WITH the rows, no `--apply` hazard                                                                  |
| `features-service` `_FEATURE_GROUP_TO_PIPELINE_MODE`                | `odds_features → BATCH_ODDS_API`; only `derived_features → BATCH_FOOTYSTATS` (FEATURES tree, not raw) — **independently corroborates the operator's architecture** |
| `instruments-service` `engine/orchestrator/footystats.py`           | writes `BATCH_FOOTYSTATS` on the INSTRUMENTS (reference) surface — the operator's IS home, untouched                                                               |
| `wipe_footystats_odds_2026_06_25.py`                                | one-off; explicitly **KEEPs** rows where `source != footystats` — would not have touched these                                                                     |

**⇒ Nothing reads `batch_footystats` on the MTDS raw-tick sports surface. The re-stamp breaks no consumer.**

### 2. Manifest layer — measured on the live index (generation `1784189886055849`, frozen 08:18:06Z)

| measure                                                       | value                                                                                                                                                                                       |
| ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| MTDS sports index total rows                                  | 1,958,498                                                                                                                                                                                   |
| `batch_footystats` rows                                       | **42,476** — 100% `venue=ODDS_API`, 100% `source=footystats`                                                                                                                                |
| — capture_status                                              | 42,027 `captured` / 449 `empty_confirmed`                                                                                                                                                   |
| — date span                                                   | **2020-06-01 … 2026-04-14 — 2,128 distinct days** (not 1,815: that was the OBJECT-day count)                                                                                                |
| `batch_odds_api` rows (merge target)                          | 362,766                                                                                                                                                                                     |
| **cell-key collisions `batch_footystats` ∩ `batch_odds_api`** | **0** (and still 0 case-normalised) — the manifest move is a CLEAN move                                                                                                                     |
| 🔴 `data_type` CASE SPLIT within `batch_footystats`           | `ODDS` 22,145 vs `odds` 20,331 → 42,476 keys collapse to **22,145** case-normalised ⇒ a near-total case-DUPLICATE population (cf. [[mdt_t2_6_league_case_duplicate_population_2026_07_16]]) |

The manifest carries the mis-stamp too: `source=footystats` on `venue=ODDS_API` rows. So the fix must move
`pipeline_mode` **and** `source` together — the path stamp and the manifest agree with each other and disagree with the
DATA (whose own `source` column is `ODDS_API`).

### 3. 🔴 THE BLOCKER — this is a read-split-merge, not a re-stamp; a size/crc-verified copy is IMPOSSIBLE

The two populations do not differ by a `pipeline_mode` value. They are **different path shapes with different
semantics**:

| axis               | migrated (`batch_footystats`)             | canonical (`batch_odds_api`)               |
| ------------------ | ----------------------------------------- | ------------------------------------------ |
| `venue=`           | `ODDS_API` — the **VENDOR**               | `BETONLINEAG` — the **BOOKMAKER**          |
| league key         | `league=2._BUNDESLIGA` (raw, uncanonical) | `league_id=ALLSVENSKAN` (canonical)        |
| `instrument_type=` | `` (empty)                                | `odds`                                     |
| `data_type=`       | `odds`                                    | **`trades`**                               |
| filename           | `ticks_migrated_20260505T160406Z.parquet` | `ticks.parquet`                            |
| cardinality        | 17 objects/day (all bookmakers bundled)   | 207 objects/day (one per bookmaker×league) |

**⇒ The dispatch's "copy to the correct canonical path, content-verified (size/crc)" cannot be done**: one migrated
object must be SPLIT into ~N bookmaker objects and MERGED into cells that already hold data, so the bytes necessarily
change and size/crc equality can never hold. This is precisely the **OR-5b(a) read-split-merge** that fix (c) below
describes — the dispatch under-specified it as a stamp fix.

### 4. DRY-RUN pilot on `day=2022-04-16` — the arithmetic is PROVEN (read-only, zero writes)

Full read of both populations (`~/tmp-stamp/idx/pilot_dryrun.py`):

| measure                                                | value                                                                                                            |
| ------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------- |
| migrated objects / rows                                | 17 / **167,464**                                                                                                 |
| canonical objects / rows                               | 207 / **5,626**                                                                                                  |
| **derivation map `venue := instrument_id[1].upper()`** | **100.0000% — 167,464/167,464** rows carry 8-segment ids; yields exactly the **16** venues canonical already has |
| schema diff                                            | `data_source` is the ONLY column canonical has and migrated lacks (22/23) — confirms the prior leg               |
| migrated distinct tick keys                            | 83,732                                                                                                           |
| canonical distinct tick keys                           | 5,626                                                                                                            |
| **UNION**                                              | **83,916 — a STRICT SUPERSET of BOTH** ✅                                                                        |
| **migrated-ONLY keys (ADDED by the merge)**            | **78,290** ⇒ the merge is genuinely ADDITIVE — this is NOT the duplication that was twice-refused                |
| 🔴 **canonical-ONLY keys (DESTROYED by an overwrite)** | **184** ⇒ MERGE-never-overwrite is now empirically re-proven on this day                                         |

**Acceptance test is NOT arithmetic-checkable.** The sibling's grid (T-12h=896 · T-6h=898 · T-4h=896 · T-2h=884 ·
T-1h=270 · T-10m=870 · T-24h=317) are **post-derive READER outputs**, not raw rows — the raw migrated rows in those
windows are 11,082 / 18,948 / 24,594 / 28,572 / 11,512 / 11,126 / 10,214. Verifying it therefore requires **running the
MDPS derive** over the merged cells, which cannot precede the merge. The pilot gate must be re-specified as: merge → run
derive → compare grid.

### Why this leg did NOT execute the mutation

Per the dispatch's own step 1 — _"prove before you mutate … If ANY consumer depends on the current (wrong) stamp, report
before acting"_ — the proof returned something stronger than a consumer dependency: **the specified operation does not
match the data**. Executing a 2,128-day / 16,969-object read-split-merge that rewrites 207+ live canonical objects per
day, where an overwrite is measurably destructive (184 keys/day) and the pilot gate cannot be evaluated without a derive
run, is not a safe thing to start on a mis-specified mandate. The blast radius is green and the arithmetic is proven —
what is missing is a correctly-specified execution plan, which is now written below.

**Reader-side cleanup SHIPPED** — `market-data-processing-service@49dbce9`: the false skip comment
(`reprocess_sports_odds.py:117-120`, _"redundant with the per-bookmaker shape"_) is **retracted in place** with the
measured refutation (5,626 vs 167,464 rows; 78,290 migrated-only keys) so no future leg re-inherits the lie. The
`_migrated_` **exclusion itself REMAINS** — removing it is option (a), which the operator explicitly rejected (it would
hard-code the SSOT violation into the consumer). Behaviour unchanged; the lie is gone.

### Corrected todos for the execution leg (supersede fix (c)'s one-liner)

- [x] [DATA] P0. ✅ **Re-specify the pilot gate** — `market-tick-data-service@75f226e8`. **The gate did NOT need a
      mutation to evaluate**: `process_to_bucketed_df` is a pure function of the raw DataFrame, so the derive runs
      locally with zero writes. Simulation validated against ground truth (canonical-alone reproduces the known live
      baseline T-24h=317/rest-0), then confirmed on the REAL reader+adapter post-merge. **Evidence**: `day=2022-04-16`
      raw 5,626→83,916; T-12h=896 · T-6h=898 · T-4h=896 · T-2h=884 · T-1h=270 · T-10m=870 **all EXACT**, T-24h=894
      (richer than 317), T-0=27 (leak-filtered). ✅ PASS — no horizon lost.
- [x] [DATA] P0. ✅ **Execute the read-split-merge** — `market-tick-data-service@75f226e8`,
      `scripts/merge_migrated_odds_into_canonical_2026_07_17.py`. **199 days · 26,264 cells · 7,911 created · 6,304,585
      rows added · 0 errors · 0 derive rows lost.** MERGE-never-overwrite enforced by a hard refusal when
      `merged < existing`. **Scoped by exhaustive measurement** (all 1,815 days probed, 0 errors): only 199 (11.0%)
      gain; 1,336 (73.6%) are pure duplicates ⇒ merging all would be ~238k rewrites for zero gain. Used the
      **family-agnostic** key `(instrument_id, fetch_utc, price, bm_time)` — `venue` is redundant
      (`venue == instrument_id[1]` @ 100.0000%) and breaks family-B days.
- [x] [DATA] P0. ✅ **Resolve the `data_type` case-duplicate population** — handled at the OBJECT layer by the merge's
      mandatory de-dup. **Root cause found and it is bigger than a case split**: the migrated population is internally
      **2× duplicated** (the bare no-`league=` object repeats the 16 league objects with `league_id` NULL; 167,464 rows
      → 83,732 keys, uniform across every horizon). The manifest mirrors it (42,476 rows → 22,145 case-normalised
      cells). No duplicate was carried into canonical.
- [ ] [DATA] P0. **PURGE (not "move") the 42,476 mis-stamped manifest rows + their 16,969 objects.** ⚠️ The doc's "0
      cell-key collisions ⇒ a clean move" is **FALSIFIED** — it compared `venue=ODDS_API` against `venue=BOOKMAKER`,
      which cannot collide by construction. After the derivation, **56.40%** of footystats `(date, league)` cells
      already exist in `batch_odds_api` ⇒ a 1:1 move creates DUPLICATE manifest rows. The correct op is a de-cased
      **purge**, now safe to specify because the merge made the `batch_footystats` population **provably redundant by
      construction**. Prereq: re-verify redundancy per object, then delete objects + rows together. (Manifest rows for
      the 199 merged days are already correct + absorbed: 41,753 rows, 100.00% present in the live index — per-VM shard
      `_index/per_vm/odds-restamp-20260717.parquet`, read-back verified.)

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
