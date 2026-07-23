---
doc_type: issue
title:
  Canonical sports player_stats within-object duplicate defect (~740k rows / ~26%) + fixture_events schema heterogeneity
  (~30% degenerate 5-col) — pre-existing, surfaced during the legacy-bucket cutover T2.4
summary:
  'Two pre-existing data-correctness defects in the CANONICAL instruments-store-sports-prd bucket, measured in full
  during the sports legacy bucket cutover T2.4 (OR-1 player_stats union). NOT introduced by the cutover and NOT blocking
  it. (1) canonical player_stats carries 740,725 within-object exact-duplicate rows on (fixture_id, player_id) — ~26% of
  its 2,882,420 rows — far larger than the row-gap doc''s cited "72 rows / 36 unique" single-cell example; the T2.4
  union DE-DUPES the 4,015 cells it touched (partial fix) but the ~13,964 untouched cells still carry the defect. (2)
  canonical fixture_events has 4 concurrent schema variants (13-col canonical, 5-col degenerate stub ~30% of a
  120-object sample, 9-col named, 10-col af_-prefixed) — the same 5-col degenerate stub the operator ruling warned
  against importing already pervades canonical independent of legacy. Both warrant a de-dup + schema-normalisation pass
  over canonical player_stats/fixture_events, ideally folded into the fixture_events re-fetch campaign the OR-1 ruling
  calls for.'
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm, instruments-service, unified-api-contracts]
scope: [engineer, admin]
tags: [sports, data-correctness, player-stats, fixture-events, duplicates, schema-drift, canonical, cutover-surfaced]
related:
  [
    ../sports_legacy_bucket_cutover_2026_07_16.md,
    /plans/active/issues/sports_legacy_canonical_row_gap_2026_07_16.md,
    ../../epics/sports_master.md,
  ]
created: 2026-07-16
last_updated: 2026-07-16
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P1
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
source: [sports cutover T2.4 measurement 2026-07-16]
---

# Canonical sports player_stats / fixture_events data-quality defects (cutover-surfaced)

> Measured live 2026-07-16 during the legacy-bucket cutover T2.4. **Pre-existing in canonical; not introduced by and not
> blocking the cutover.** Filed per the findings-triage HARD RULE (data-correctness → issue doc + notify operator).

## Finding 1 — canonical player_stats within-object duplicate defect: 740,725 rows (~26%)

Building the global canonical player_stats (fixture_id, player_id) key set over all 27,296 canonical
`entity=player_stats/*/player_stats.parquet` objects measured:

| metric                                    | value         |
| ----------------------------------------- | ------------- |
| total rows                                | **2,882,420** |
| per-object unique (fixture_id, player_id) | 2,141,695     |
| **within-object duplicate rows (defect)** | **740,725**   |
| global distinct keys                      | 2,139,386     |
| cross-object same-key overlap             | 2,309 (small) |

So ~25.7% of canonical player_stats rows are exact `(fixture_id, player_id)` duplicates **within a single object** — the
row-gap investigation saw only one instance ("72 rows / 36 unique", `day=2021-05-08 LIGUE_2`) and flagged it as a triage
item; the full measurement shows it is systemic. The writer appends without de-duping on `(fixture_id, player_id)`.

**Partial remediation already shipped by the cutover**: T2.4's union DE-DUPES on write, so the **4,015 cells it touched
are now dup-free**. The remaining **~13,964 canonical player_stats cells the union skipped (SKIP_NO_NEW) still carry the
defect**. A full fix is a de-dup rewrite over the untouched cells (idempotent, keyed on `(fixture_id, player_id)`).

## Finding 2 — canonical fixture_events schema heterogeneity (~30% degenerate 5-col)

A 120-object random sample of canonical `entity=fixture_events/*/fixture_events.parquet` found **four concurrent
schemas**:

| variant                   | share (n=120) | columns                                                                                       |
| ------------------------- | ------------- | --------------------------------------------------------------------------------------------- |
| canonical 13-col          | 68 (57%)      | event_type, event_detail, player_id, player_name, team_id, team_name, time_elapsed, …         |
| **degenerate 5-col stub** | **36 (30%)**  | available_at, comments, detail, fixture_id, type (no attribution — the exact stub OR-1 warns) |
| 9-col named               | 9 (7%)        | assist, player, team, fixture_id, time, type, …                                               |
| 10-col af\_-prefixed      | 7 (6%)        | af_fixture_id, af_player_id, af_team_id, af_assist_id, …                                      |

The 5-col degenerate stub the operator ruling warns against importing **already pervades canonical (~30%)** independent
of the legacy bucket. The cutover imported **zero new 5-col stubs** (the 40 class-A fixture_events it moved are the
10/11-col attributed forms, which canonical already carries). This is a canonical data-quality issue, not a cutover
regression.

## Recommended remediation (P1, not cutover-gating)

1. **player_stats**: an idempotent de-dup rewrite over all canonical player_stats cells (keyed
   `(fixture_id, player_id)`), reusing the T2.4 union tooling's dedup path. ~13,964 cells remain.
2. **fixture_events**: fold into the OR-1 fixture_events re-fetch campaign — re-fetch the degenerate/heterogeneous cells
   from api-football into the canonical 13-col schema. Re-fetch lists for the cutover's own legacy-only fixtures are at
   `~/tmp-cutover/t2_4_refetch_{player_stats,fixture_events}.json` (archived to
   `gs://deployment-scripts-central-element-323112/sports_cutover_2026_07_16/phase2_evidence/`).
3. Add a writer-side de-dup + schema-conformance gate so neither defect re-accrues.

## Progress Log

**2026-07-16** — Both defects measured in full during cutover T2.4 (`~/tmp-cutover/t2_4_build_canon_keys.py` for the dup
census; the fixture_events sample via the cutover schema probe). T2.4 union partially remediated the player_stats dup
defect (4,015 cells). Filed for a dedicated follow-up; does not block the legacy-bucket delete.

---

## Defect (3) — the index's `instrument_count` semantic has DRIFTED across writer generations (added 2026-07-16, surfaced by OR-9)

**Pre-existing, NOT cutover-introduced, does NOT block the legacy-bucket delete** (the delete gate is the object layer).

The manifest writer defines `instrument_count` as the written **row count** — `_writer_captured.py:360`:
`effective_count = int(row_count) if row_count is not None else len(df)`. The live index does not honour that uniformly.
Measured on **untouched** canonical `instruments-store-sports-prd` cells (`~/tmp-or9/or9_instrument_count_semantic.py`,
`_era.py`; index generation `1784207377339311`):

| era  | cells sampled | `instrument_count == rows` | notes                                                               |
| ---- | ------------: | -------------------------: | ------------------------------------------------------------------- |
| 2019 |             6 |                    **0/6** | **6/6 carry `1`** — incl. one object with **24 rows / 12 fixtures** |
| 2020 |            12 |                       7/12 | mixed                                                               |
| 2025 |            15 |                      10/15 | row-count dominant                                                  |
| 2026 |            15 |                      11/15 | row-count dominant                                                  |

⇒ **2019-era rows carry `instrument_count=1` as a per-object marker, not a row count.** Consequences:

1. Any consumer reading `instrument_count` as "rows" **silently mis-reads the entire 2019 era** (and any completeness or
   row-count-based coverage check over it is wrong by construction, not by a little).
2. **T2.4's 4,015 unioned `player_stats` cells** carry the matching staleness for whichever are post-2019: a union
   changes the object's row count while the index row keeps the pre-union count.
3. It is why **OR-9 deliberately did NOT "correct" the 122 cells it unioned** — rewriting a 2019-era `1` to a row count
   would impose a semantic that generation never used and diverge those cells from every untouched sibling. Fixing
   OR-9's 122 while leaving T2.4's 4,015 would be arbitrary; this needs one systemic ruling.

**Proposed fix**: decide the ONE semantic (row count, per the writer), then backfill/normalise `instrument_count` across
eras in a single pass — or, if the 2019 `1` is intentional, document it and fix the _consumers_. Either way the decision
belongs with the same de-dup/schema-normalisation sweep as defects (1) and (2). **Do not** let a per-plan agent correct
its own touched subset piecemeal.
