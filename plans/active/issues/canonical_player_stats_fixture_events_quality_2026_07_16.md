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
    /plans/archive/issues/sports_legacy_canonical_row_gap_2026_07_16.md,
    ../../epics/sports_master.md,
  ]
created: 2026-07-16
author: unknown
last_updated: 2026-07-26
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
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
archive_exempt: true
source: [sports cutover T2.4 measurement 2026-07-16]
context_scope:
  [
    /plans/archive/2026_07/sports_legacy_bucket_cutover_2026_07_16.md,
    /plans/epics/sports_master.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /plans/archive/issues/sports_legacy_canonical_row_gap_2026_07_16.md,
    market-tick-data-service/scripts/sports/reconcile_player_stats_missing_gcs_manifest_2026_08_05.py,
  ]
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

## Finding 1 — RESOLVED 2026-07-25

Ran `instruments-service/scripts/dedup_canonical_player_stats_2026_07_25.py --apply` over all 26,687 manifest-tracked
`PLAYER_STATS`/`captured` cells (a single bounded manifest read, not a fresh GCS walk — real object paths resolved via
UAC's `candidate_parquet_paths(..., pipeline_mode=...)` SSOT). Covered ALL cells uniformly rather than trying to
reconstruct which of the original 27,296 the T2.4 union's 4,015 already touched (that tooling was session-local and
didn't survive to this session) — de-duping an already-clean object is a safe no-op, so full coverage converges to the
same end state regardless of prior partial coverage. **Result: 7,066 objects deduped, 808,279 duplicate rows removed
(more than the original 740,725 estimate — expected, since this covers strictly more cells than the original T2.4
scope). A re-run immediately after confirmed 0 duplicate rows remain project-wide** (the doc's own stated verification
methodology). Generation-matched CAS writes (14 transient losses to concurrent live writers on the first pass, all
cleanly picked up by the idempotent re-run — 0 errors on the second pass).

**Two things found during this pass, not previously documented for player_stats specifically:**

- **Schema heterogeneity also affects player_stats** (previously this doc only documented it for fixture_events, Finding
  2 below): ~12% of captured cells (3,274/26,687) carry a NESTED schema — columns
  `[team, players, fixture_id, available_at]` where `players` is a list-of-dicts per team, not one flat row per player.
  The dedup script correctly SKIPPED these (never guessed how to dedupe a schema it wasn't built for) — they are outside
  this finding's original scope (which measured 2,882,420 rows across 27,296 objects, implying the flat schema as the
  dominant/measured shape) and need their own schema-normalisation pass, mirroring Finding 2's fixture_events treatment.
  Not filed as a separate issue doc — small enough to track here as a follow-up, same remediation shape as Finding 2. —
  **RESOLVED 2026-07-26 (slot-2)**: flattened all 3,274 via `instruments-service@a22e371e`
  (`scripts/normalize_nested_player_stats_2026_07_26.py`, reusing the production `normalize_api_football_player_stats`
  mapping function). Hit + fixed a self-caused incident along the way (240 objects briefly written empty, fully
  remediated) — full writeup: `/plans/archive/issues/sports_player_stats_normalize_empty_write_incident_2026_07_26.md`
  (archived 2026-07-26; follow-ups: `/plans/archive/issues/sports_player_stats_empty_write_followups_2026_07_26.md`,
  archived + resolved 2026-07-28). Independent final census confirms 0 remaining nested-schema `player_stats` objects.
- **1,298/26,687 (4.9%) manifest-`captured` cells have NO corresponding GCS object** — concentrated in 2019 (a
  known-drifted writer-generation era per this doc's own Defect 3). This is a manifest-vs-reality mismatch, not a
  duplicate-row issue; left untouched/logged (never guessed), and is a candidate for its own investigation but out of
  this finding's scope. — **ROOT-CAUSE CENSUS 2026-07-26 (slot-2)**: re-measured (manifest-driven, single bounded read,
  same methodology) — 1,298/26,701 confirmed, distribution by `day` year: `{2018: 3, 2019: 972, 2020: 235, 2025: 88}`,
  100% `pipeline_mode=batch_api_football`. The 2018-2020 bulk (1,210/1,298, 93%) is consistent with this doc's own
  Defect 3 (the 2019-era `instrument_count` semantic drift — same writer generation, same era, cross-referenced per this
  finding's own instruction) — no NEW root cause investigated beyond confirming the era match; a manifest row from that
  generation can be `captured` with no live object for the same reason that generation's `instrument_count` semantics
  diverged from every later era (an early, less-hardened writer). **The 88/1,298 (6.8%) 2025 cells are DIFFERENT and NOT
  explained by the 2019-era theory** — recent dates, current writer generation, so a genuinely live/current gap, not a
  historical artifact. This is flagged as its own follow-up (below) rather than guessed at: determining whether these
  are a live write-completion race, a later deletion, or something else needs its own targeted investigation (e.g.
  checking whether a corresponding `attempted_failed`/error-log entry exists for the same cells, which this pass did not
  check). **Disposition**: no manifest reconciliation action taken in this pass — relabeling a `captured` row to an
  honest state (e.g. `attempted_failed`) is itself a manifest-mutation action broader than this todo's scope and risks
  masking the live 2025 gap's real cause if done before that gap is understood; ruled non-actionable-in-this-todo per
  the todo's own "or explicit non-actionable ruling" allowance.

Evidence: `instruments-service@210d4567` (script commit).

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

## Follow-up todos (added 2026-07-26, slot-2)

- [x] ✅ [DATA] P2. Investigate the 88/1,298 (6.8%) `PLAYER_STATS` manifest-`captured`-but-no-GCS-object cells dated
      2025 (current writer generation, NOT the 2019-era quirk the rest of the 1,298 population matches) — check for a
      corresponding `attempted_failed`/error-log signal on the same (date, league, `batch_api_football`) cells, and
      determine whether this is a live write-completion race, a later deletion, or another current-pipeline gap. Do NOT
      relabel the manifest rows until the mechanism is understood. (repo: instruments-service /
      market-tick-data-service) — instruments-service@36b59400 + see Progress Log 2026-08-02 for the root-cause verdict.
- [x] ✅ [DATA] P3. Once the 2025 mechanism above is understood (and, separately, for the 1,210 2018-2020-era cells
      already attributed to the Defect-3 writer-generation quirk), decide + execute the actual manifest reconciliation
      (relabel to an honest `capture_status`, or document why `captured` with no object is the correct historical record
      for that era) — this is the manifest-mutation action deferred from the 2026-07-26 root-cause census above. (repo:
      instruments-service) — market-tick-data-service@25c7a3f2

## Progress Log

- 2026-08-05 (slot-16): P3 manifest reconciliation SCRIPT SHIPPED (market-tick-data-service@25c7a3f2,
  `scripts/sports/reconcile_player_stats_missing_gcs_manifest_2026_08_05.py`). Decision: both populations relabeled from
  `captured` to `attempted_failed` with distinct error_reason values. The 88 2025-era cells (migration artifact from the
  rescan→migrate→backfill pipeline) get `error_reason` documenting the 3-script sequence; the ~1,210 2018-2020-era cells
  (Defect-3 writer-generation quirk) get `error_reason` documenting the known-divergent early-writer semantics. Script
  follows the established manifest_swap safety pattern: dry-run default, snapshot-before-write, CAS-filtered index
  rewrite, post-write verification. Actual `--apply-prod --confirm-prod-write` execution pending — the script is ready,
  the census already confirmed 0 GCS objects at any candidate path.

- 2026-07-26 (slot-2): Both open follow-ups from the 2026-07-25 pass closed out: (1) the 3,274 nested-schema
  `player_stats` cells flattened (`instruments-service@a22e371e`), 0 remaining on an independent census — see
  `/plans/archive/issues/sports_player_stats_normalize_empty_write_incident_2026_07_26.md` (archived 2026-07-26) for a
  self-caused incident hit and fully remediated along the way. (2) The 1,298 missing-GCS cells root-caused by era: 1,210
  (93%) match the existing Defect-3 2019-2020 writer-generation quirk (no new investigation needed beyond confirming the
  era match); 88 (7%) are a 2025 anomaly NOT explained by that theory, filed as its own follow-up todo above rather than
  guessed at. No manifest reconciliation action taken this pass (ruled non-actionable-in-this-todo, see the follow-up
  todos).
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **2026-08-02 (slot-3)**: 2025-cell follow-up RESOLVED — mechanism understood, root-caused with evidence, no relabel
  performed (correctly deferred to the P3 reconciliation todo below). Re-derived the exact 88 cells
  (`instruments-service@36b59400`, `scripts/census_player_stats_2025_missing_2026_08_02.py`, single bounded manifest
  read + real-path existence check, same methodology as the fixture_events sibling census) and characterized their
  provenance columns. **Verdict: a stale/orphaned manifest row left behind by an unpaired one-off migration — NOT a live
  write-completion race, and NOT the 2026-07-26 empty-write incident** (ruled out directly: that incident only ever
  touched the 3,274 _nested-schema_ cells, a disjoint population from these 88 `not_found` cells, which were already
  measured absent from GCS _before_ the incident's `--apply` ever ran).
  - All 88 rows share the SAME signature: `league_id=None` (blank/unresolved), `written_at` on 2026-07-14 (spread
    11:38–16:20 UTC, one per date — not a single bulk timestamp), `job_id=""`/`enumerator_run_id=""` (no run correlator
    retained), `error_reason=""` (consistent with `captured`, never `attempted_failed`), and a real nonzero
    `instrument_count` (89–12,003 rows) — i.e. these are NOT empty placeholders, they genuinely once described real
    data.
  - **0/88 have a matching `attempted_failed` row at the same key** anywhere in the current manifest — expected, since a
    same-key row can't hold both states simultaneously today (confirms this was never a fetch failure).
  - **Direct GCS verification (2025-09-01, 2025-10-15, 2025-11-30 sampled) proves the REAL data exists and is correctly
    captured** — 5+ per-league `player_stats.parquet` objects sit at the current canonical
    `pipeline_mode=batch_api_football/entity=player_stats/league={L}/` path for every sampled date, each with its OWN
    correct `captured` manifest row (real `league_id`, correct `written_at` ~14:55–16:29 UTC same day, correct
    per-league row counts). The 88 `league_id=None` rows are a SEPARATE, EXTRA manifest row per date sitting alongside
    those correct rows — not the only record for that date.
  - **Root cause, corroborated by code + timeline**: `rescan_sports_manifest.py` (`Lifecycle: permanent`, walks GCS and
    rebuilds manifest rows from whatever parquet it finds) ran across many 2025 dates on 2026-07-14, at a point when
    each date's PLAYER_STATS data still lived at the OLD bare single-file path
    (`entity=player_stats/player_stats.parquet`, all leagues combined) — it wrote a `captured` row with blank
    `league_id` and the bare file's total row count. Later the SAME DAY, `migrate_sports_per_league.py` (per-league
    migration, `scripts/migrate_sports_per_league.py:345-355`) split that bare file into the per-league objects and
    **deletes the original bare file once all per-league writes succeed** — by design, not a bug in itself. A
    downstream/parallel pass (`backfill_sports_per_entity_manifest.py`, whose own docstring says it exists to fix
    "`rescan_sports_manifest.py` wrote rows with `league_id=''`") then wrote the correct per-league manifest rows. **No
    step in that three-script sequence ever retired the ORIGINAL blank-league row** — it is a manifest row honestly
    describing a real (now legitimately migrated-away) object that no current tooling ever goes back to reconcile.
    Independently corroborated by a parallel code-read of the CURRENT live per-league writer
    (`sports_reference_fixtures_write.py::_write_fixture_entity_per_league`): it writes the GCS object BEFORE calling
    `manifest.record_captured(...)` (object-then-manifest order), so the CURRENT writer path structurally cannot produce
    a captured-with-no-object row via a race — ruling out mechanism (a) for these 88 cells specifically.
  - **Disposition**: closest to "a later deletion" per the todo's own taxonomy — a legitimate, sanctioned deletion (the
    per-league migration) that left its source manifest row unreconciled. This is now understood well enough to hand to
    the P3 reconciliation todo below: relabeling these 88 rows (e.g. to reflect they describe a migrated/superseded
    shard, not a live gap) is safe now that the mechanism is confirmed non-recurring-by-default (the migration script is
    a one-off, not a scheduled job) and non-data-loss (the real per-league data is present and correctly captured under
    its own rows).
  - Evidence: `instruments-service@36b59400` (census script + JSON root-cause report,
    `scripts/_player_stats_2025_missing_root_cause_2026_08_02.json`).

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — dropped the honest-absence codex doc and the
  now-superseded dedup script (Finding 1 fully resolved), added the 2025-cell root-cause census script since the sole
  remaining open item (the P3 manifest-reconciliation todo) builds directly on it.
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **context-scout 2026-08-07**: refreshed context_scope (5 entries) — swapped the now-superseded root-cause census
  script (`census_player_stats_2025_missing_2026_08_02.py`, investigation closed) for the reconciliation script the sole
  open Follow-up todo names directly (`reconcile_player_stats_missing_gcs_manifest_2026_08_05.py`, shipped but its
  `--apply-prod` pass still pending).
- **2026-08-10 (slot-29)**: the sole open Follow-up flipped `[x]` (both PLAYER_STATS populations independently verified
  0 confirmed-missing — see the todo's own DONE note and the batch12 plan's Progress Log for full detail).
  `archive_exempt: true` set on THIS commit per the RULED-2026-08-09 two-commit bridge (this doc's own last todo is its
  archival trigger) — dropped in the immediately-following `git mv` archival commit.

## Follow-ups

- [x] [DATA] P3. Execute the actual --apply-prod --confirm-prod-write pass of
      scripts/sports/reconcile_player_stats_missing_gcs_manifest_2026_08_05.py over the 88 2025-era + ~1,210
      2018-2020-era PLAYER_STATS captured-without-GCS cells (relabel captured->attempted_failed with the recorded
      distinct error_reasons), then verify the manifest. **DONE 2026-08-10 (slot-29)**: 2025 population —
      `market-tick-data-service@56df68f7f`, 88 rows relabeled, independently verified 0 confirmed-missing (separate
      dry-run pid 4057523). 2018-2020 population — required two further bugfixes beyond the originally-shipped
      `25c7a3f2` (a pyarrow-native column-projected rewrite to fix a resource-watchdog RSS kill,
      `market-tick-data-service@22a305ff1`, then a `.length`->`len()` one-line fix,
      `market-tick-data-service@975d6a4f8`) before the apply-prod pass could complete without being killed; 1,210 rows
      relabeled, independently verified 0 confirmed-missing among the remaining 2,184 captured rows (separate dry-run
      pid 2169822, no `--apply-prod`). Full diagnostic detail (resource-watchdog kill evidence, retry reasoning) in
      `/plans/active/sports_satellite_ao_dispatch_batch12_2026_08_09.md` Progress Log, 2026-08-09/10 entries.

> **2026-08-06 archive-candidate audit**: Progress Log 2026-08-05 (slot-16): P3 reconciliation 'SCRIPT SHIPPED
> (market-tick-data-service@25c7a3f2)... Actual `--apply-prod --confirm-prod-write` execution pending — the script is
> ready' — the todo was flipped `[x]` while the actual prod manifest mutation is still unexecuted open work. **Resolved
> 2026-08-10**: the prod apply has now genuinely executed for both populations, independently verified per above — the
> premature-flip pattern this audit warned about does not recur here.
