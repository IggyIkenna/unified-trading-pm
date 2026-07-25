---
doc_type: issue
title:
  Sports legacy↔canonical row gap (F-2 / OR-1) — NOT a lossy migration and NOT a path artifact; canonical objects are
  independent LATER re-fetches, ~59% of the 305k "missing" rows are junk/snapshot-skew, ~37% (player_stats) is genuine
  complementary coverage
summary:
  'Read-only investigation of the cutover runbook''s F-2 finding — "13,222 legacy objects have a canonical counterpart
  holding STRICTLY FEWER ROWS (~305,000+ rows only in legacy)" — commissioned by operator ruling 2026-07-16
  ("investigate the row gap first"), the blocking gate on OR-1. **The finding is REAL — it is not a path/shape artifact
  (hypothesis d is DISPROVEN): canonical mirrors legacy''s per-league split exactly and every deficit reproduces at the
  exact pipeline_mode-normalised key.** But its CAUSE is not what F-2 assumed. **No migration ever transformed legacy
  rows into canonical rows**: the designated vehicle `migrate_sports_canonical_v9.py` is a byte-identical server-side
  `gcs_copy_object` (no row transform); the 2026-04-28 v1→v9 plan is `phase: pending_approval` (never executed, and
  scoped only `entity=fixtures`); and canonical `fixture_events` carries columns (`player_id`, `team_id`,
  `time_elapsed`) that DO NOT EXIST in legacy — no transform can invent them. Measured: **62/62 sampled canonical twins
  are WRITTEN LATER than their legacy twin** (legacy 2026-05-01…05-23; canonical 2026-07-06…07-15). The two buckets are
  two INDEPENDENT capture generations, and canonical is the fresher, richer one: over 3,051 paired objects canonical
  holds **+27,764 NET MORE rows** (gains 29,650 / "loses" 1,886 — 15:1). Per-class the ~305k splits: **standings 91,380
  + teams 16,502 + player_values 16,233 (~124k, 41%) = NO missing entities — snapshot skew of a mutable upstream and one
  cartesian-junk write**; **fixture_events 69,444 (23%) = a degenerate 5-column legacy schema whose rows are
  unattributable (50 rows collapse to 7 unique)**; **player_stats 111,827 (37%) = GENUINE complementary coverage — real
  38-col rows for fixtures canonical lacks (verified absent ±2 days)**. Recommendation for OR-1: **PARTIAL (option D) —
  reject the blanket row-union (A), and reject overwrite (B) as CATASTROPHIC; run a targeted, schema-aware, per-entity
  union restricted to player_stats (+ a fixture-coverage review of fixture_events), explicitly excluding the
  junk/snapshot-skew classes.** Class B is NOT a delete-blocker at the ~59% junk level, but it is NOT a false alarm
  either — the cutover is NOT unblocked as-is.'
status: resolved
nature: issue
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm, market-tick-data-service, instruments-service, unified-api-contracts]
scope: [engineer, admin]
tags: [sports, migration, bucket-canonicalisation, row-gap, data-correctness, gcs, manifest, investigation, read-only]
related:
  [
    ../sports_legacy_bucket_cutover_2026_07_16.md,
    ../sports_data_sources_canonical_completion_2026_07_13.md,
    ../../archive/2026_07/sports_manifest_canonicalisation_2026_06_01.md,
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
  sports_legacy_bucket_cutover_2026_07_16.md T2.4 (player_stats union, 388,825 rows / 4,015 cells, DONE 2026-07-16)
source: [operator ruling 2026-07-16 "investigate the row gap first", cutover runbook F-2 / OR-1]
---

> **✅ ARCHIVED 2026-07-25** — `status: resolved`, the 2026-07-23 RE-TRIAGE verdict is RESOLVED BY LATER WORK, 0 open
> todos, unlocked. Moved to `plans/archive/issues/` per the issue-doc-lifecycle archival ritual.

# Sports legacy↔canonical row gap — why canonical holds fewer rows (F-2 / OR-1)

> **READ-ONLY investigation. Zero mutations** — no writes, no copies, no manifest changes, no bucket changes. Every
> number below is measured live against the two buckets on 2026-07-16, not inherited from an audit leg.

| Bucket    | Name                                                  |
| --------- | ----------------------------------------------------- |
| Legacy    | `instruments-store-sports-central-element-323112`     |
| Canonical | `instruments-store-sports-prd-central-element-323112` |

## THE HEADLINE — three sentences

1. **The F-2 finding is REAL, not a false alarm.** Hypothesis (d) (path/shape artifact — legacy day-level object vs
   canonical per-league split) is **DISPROVEN**: canonical mirrors legacy's layout _exactly_ (same bare + per-league
   objects), and every deficit reproduces at the exact `pipeline_mode`-normalised key.
2. **But the assumed CAUSE is wrong.** There was **no lossy migration** — hypothesis (b) is **DISPROVEN**. Nothing ever
   transformed legacy rows into canonical rows. The two buckets are **two independent capture generations**, and
   canonical is the **later, net-richer** one.
3. **The ~305,000 "rows only in legacy" are not 305,000 lost observations.** ~59% are junk, snapshot skew, or
   unattributable degenerate-schema rows. **~37% (player_stats, ~111,827) is genuine complementary coverage** and is the
   only part that warrants recovery.

## Method

- Sampled **3,946 legacy objects across 10 days** spanning the full verified corpus (2018-09-22 … 2026-04-14).
- Cell key = strip the canonical-only `/pipeline_mode=<x>/` segment (per
  `unified_api_contracts/canonical/domain/sports/gcs_paths.py::candidate_parquet_paths`, the SSOT).
- Exact row counts via parquet-footer reads (never byte-size proxy — the runbook's R-20 trap).
- For every candidate deficit: read BOTH objects in full, compare **schemas, duplicate structure, and identity-key
  containment** (`team_id` / `player_id` / `fixture_id`), then scan the **whole entity tree ±2-3 days** in canonical to
  test whether the "missing" rows merely moved.

Reproduction fidelity: the sample yields **62 class-B pairs / 3,051 paired objects = 2.0%**, which scales to ~13,000
against the corpus — matching the audit's **13,222**. The `standings` deficit scales to **30 rows/day × 3,046 days =
91,380 — an exact match to the audit's 91,380**, confirming the sample is representative.

---

## Hypothesis (d) — PATH/SHAPE ARTIFACT: **DISPROVEN**

The prompt flagged this as the most likely false alarm. It is not one.

- Legacy and canonical carry the **identical layout** — both have a bare day-level object _and_ per-league splits:
  - legacy `…/day=2019-08-12/entity=fixture_events/fixture_events.parquet` +
    `…/entity=fixture_events/league=ALLSVENSKAN/…`
  - canonical `…/day=2019-08-12/pipeline_mode=batch_api_football/entity=fixture_events/fixture_events.parquet` +
    `…/league=ALLSVENSKAN/…`
- The only structural difference is the inserted `pipeline_mode=` segment. After normalising it, the mapping is **1:1**
  (legacy `entity=fixture_events/` had 15 objects on the sampled day; canonical had the same 15).
- The `_write_per_league` split named in the prompt lives in **features-service**
  (`features_service/sports/cli/handlers/batch_handler.py`) and governs the **features** bucket — it does **not** apply
  to the `sports_reference/` tree in instruments-store, which is per-league in _both_ buckets.
- Direct test: the legacy-only `fixture_id`s were scanned across the **entire canonical entity tree over a ±3-day
  window** (173 objects) — **NOT FOUND anywhere**. The rows did not move; they are absent.

> **Verdict (d): NOT an artifact. The 13,222 class is not a false alarm. The cutover is NOT unblocked on these
> grounds.**

## Hypothesis (b) — LOSSY MIGRATION: **DISPROVEN** (four independent proofs)

1. **The vehicle cannot transform rows.** `migrate_sports_canonical_v9.py` copies via server-side `gcs_copy_object` —
   _"`gcs_copy_object` server-side (~250x) for path-only moves"_ (`:44`), _"copies legacy-only → prd via server-side
   gcs_copy_object"_ (`:51`, `:498`). Byte-identical. A copy cannot change a row count.
2. **The v1→v9 plan never ran.** `plans/ai/sports_fixtures_legacy_schema_migration_2026_04_28.plan.md` is
   `phase: pending_approval`, and its scope line reads _"Only `entity=fixtures` is in scope for this plan"_ — it does
   not touch player_stats / standings / fixture_events at all.
3. **Canonical has columns legacy never had — no transform could invent them.** For
   `day=2021-05-08/entity=fixture_events/league=LA_LIGA/`:
   - legacy columns (5): `type`, `detail`, `comments`, `fixture_id`, `available_at`
   - canonical columns (13): `event_type`, `event_detail`, **`player_id`, `player_name`, `team_id`, `team_name`,
     `time_elapsed`, `time_extra`, `assist_id`, `assist_name`**, `comments`, `fixture_id`, `available_at` Canonical was
     **fetched fresh from the upstream**, not derived from legacy.
4. **Canonical is uniformly NEWER.** Of the 62 sampled class-B pairs: **canonical LATER 62/62; SAME 0; EARLIER 0.**
   Legacy writes cluster 2026-05-01…2026-05-23; canonical twins 2026-07-06…2026-07-15 — 6-10 weeks later. The 2026-07-13
   completion plan corroborates this with named **re-fetch/backfill campaigns into canonical**
   (`backfill-teams-61-leagues` 165,148 TEAMS rows, `fill-missing-player-stats`, the "v9-rebuild").

> **Verdict (b): there is NO data-loss event. No past migration dropped these rows. This is NOT a P0 data-loss finding
> beyond the cutover.** The rows were never in canonical to begin with — legacy and canonical are parallel capture
> generations that were populated by different fetch campaigns with different coverage.

## The direction nobody measured: **canonical is NET RICHER**

Over the **3,051 paired objects** in the sample:

| Relation                 | Objects       | Rows        |
| ------------------------ | ------------- | ----------- |
| canonical **MORE** rows  | 427 (14.0%)   | **+29,650** |
| canonical SAME rows      | 2,562 (84.0%) | 0           |
| canonical **FEWER** rows | 62 (2.0%)     | −1,886      |
| **NET**                  |               | **+27,764** |

Total rows over paired objects: legacy **236,212** vs canonical **263,976**. **Canonical gains ~15 rows for every 1 it
"loses".** F-2 measured only the losing 2% and reported it as if canonical were strictly poorer. It is not.

**This single fact kills OR-1 option B.** Overwriting canonical with legacy would destroy the +29,650-row majority.

---

## PER-CLASS VERDICT

### 1. `standings` — 91,380 rows — verdict **(c) SEMANTIC / snapshot skew. NO missing entities. No action.**

`day=*/entity=standings/league=ARGENTINA_PRIMERA/` is **90 → 60 on 10 of 10 sampled days** — one signature replicated
across ~3,046 day partitions (30 × 3,046 = **91,380**, the audit's exact number).

Measured on `day=2019-08-12`:

|                     | legacy                                                                                       | canonical                                                                                                      |
| ------------------- | -------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| rows                | 90                                                                                           | 60                                                                                                             |
| distinct `team_id`  | **30**                                                                                       | **30**                                                                                                         |
| in legacy NOT canon | **0**                                                                                        |                                                                                                                |
| in canon NOT legacy |                                                                                              | **0**                                                                                                          |
| groups              | `Anual 2026` (30), `Apertura, Group A` (15), `Apertura, Group B` (15), `Promedios 2026` (30) | `Apertura - Group A` (15), `Apertura - Group B` (15), **`Clausura - Group A` (15), `Clausura - Group B` (15)** |
| upstream `update`   | 2026-04-29                                                                                   | 2026-06-12                                                                                                     |

**Zero teams are missing from canonical.** The row delta is that the two snapshots captured **different derived tables**
of the same live standings endpoint at different times: legacy's snapshot (April) carried the `Anual`/`Promedios`
aggregate views; canonical's (June) carried the `Clausura` groups the April snapshot could not have known about.
Canonical holds data legacy lacks and vice versa — **neither is a superset**, and both are season-**2026** tables
mis-stamped under a `day=2019-08-12` partition (a pre-existing partitioning defect, out of scope here).

Legacy's "extra" rows are **derived aggregate views, not per-team observations**. Nothing to recover.

### 2. `teams` — 16,502 rows — verdict **(c) snapshot skew of a mutable upstream. No action.**

`entity=teams/league=EREDIVISIE/` is **22→18 / 24→18 on 10 of 10 days** — again one signature × ~3,050 days. Legacy's 4
extra teams (`RODA`, `WAALWIJK`, `ALMERE_CITY_FC`, `DEN_BOSCH`) are distinct real teams (legacy has **zero** duplicate
rows), so this is not dedup — but it is one upstream `/teams` response difference between the May and July fetches,
replicated, not 16,502 distinct facts. Canonical carries `available_at` (v9) that legacy lacks.

### 3. `player_values` — 16,233 rows — verdict **(a)-adjacent: legacy's extra is CARTESIAN JUNK. Never merge. No action.**

This is the runbook's headline example (_"`day=2019-08-12 season=2019`: legacy 640 vs canonical 38"_). It is real and
path-identical — but **inverted from the assumption**:

| Object                                                    | rows    | cols | distinct `team_id` | leagues                        | mtime      |
| --------------------------------------------------------- | ------- | ---- | ------------------ | ------------------------------ | ---------- |
| legacy `pipeline_mode=batch_transfermarkt/…/season=2019/` | **640** | 8    | **20**             | **32**                         | 2026-06-22 |
| canonical same path                                       | **38**  | 11   | **38**             | 2 (`MLS` 26 + `K_LEAGUE_1` 12) | 2026-06-24 |
| legacy **bare** `entity=player_values/season=2019/`       | 38      | 11   | 38                 | 2                              | 2026-05-01 |

The 640-row legacy object is a **cartesian-product artifact**: the same **20** `team_id`s stamped against **32** leagues
(20 × 32 = 640), with **3 columns missing** and **zero `team_id` overlap** with the real data. Canonical's 38 rows are
**correct** (MLS had 26 teams and K League 1 had 12 in 2019). Note the legacy bucket _also_ holds the correct 38-row
object at the bare path — canonical matches **that** one exactly.

> **Merging this "602-row deficit" into canonical would inject corruption into the bucket the operator wants clean.**

### 4. `fixture_events` — 69,444 rows — verdict **(c) DEGENERATE legacy schema; rows unattributable. No merge.**

Legacy's rows carry **no player, no team, no minute** — only `type`/`detail`/`comments`/`fixture_id`. On
`day=2021-05-08 league=LA_LIGA` legacy's **50 rows collapse to 7 distinct rows** (mass duplication once the
discriminating columns are absent); canonical's 26 rows carry the full 13-column attribution.

Day-level, canonical is far richer: **100 distinct `fixture_id` vs legacy's 46**. Legacy does retain **13** fixture_ids
canonical lacks (verified NOT FOUND across ±3 days), but their rows are unattributable ("a goal happened in fixture
605406", with no scorer, team, or minute). Recovering them buys ~7 usable facts per object at the cost of unioning a
5-column schema into a 13-column one.

### 5. `player_stats` — 111,827 rows — verdict **GENUINE COMPLEMENTARY COVERAGE. This is the only real residue.**

Same **38-column schema in both** — so this class is directly comparable and legacy's rows are **fully-formed real
observations**.

`day=2021-05-08 league=LIGUE_2`: legacy **216 rows / 216 unique / 6 fixtures / 12 teams**; canonical **72 rows / only 36
unique / 1 fixture / 2 teams** — and canonical's single fixture is **not one of legacy's 6** (zero `team_id` overlap).

Day-level containment on `day=2021-05-08`: legacy **60** distinct fixtures, canonical **53** — **29 only in legacy, 22
only in canonical**. The 29 legacy-only fixtures were scanned across canonical ±2 days (83 objects): **NOT FOUND**.

Two sub-findings:

- **Real legacy-only data exists here** — full player rows for fixtures canonical never captured. Deleting legacy
  without recovering them is a real (if bounded) loss.
- **NEW FINDING — canonical `player_stats` has an exact-duplicate defect**: 72 rows for 36 unique rows (2× duplication).
  This is independent of the cutover and should be triaged separately.

---

## Summary table — where the ~305,000 rows actually go

| Class            | Rows         | %    | Verdict                                                           | Recover?  |
| ---------------- | ------------ | ---- | ----------------------------------------------------------------- | --------- |
| `player_stats`   | 111,827      | 37%  | **GENUINE complementary coverage** (real 38-col rows)             | **YES**   |
| `standings`      | 91,380       | 30%  | (c) snapshot skew — **0 teams missing**; derived aggregate views  | no        |
| `fixture_events` | 69,444       | 23%  | (c) degenerate 5-col schema — rows unattributable (7:1 collapse)  | no¹       |
| `teams`          | 16,502       | 5%   | (c) snapshot skew — one upstream diff × ~3,050 days               | no        |
| `player_values`  | 16,233       | 5%   | **(a) cartesian junk** — 20 teams × 32 leagues; canonical correct | **NEVER** |
| **Total**        | **~305,386** | 100% | ~59% junk/skew · 23% unattributable · **37% genuine**             |           |

¹ a fixture-coverage review is warranted (13 legacy-only fixtures on the sampled day) even though the rows themselves
carry no attribution.

---

## RECOMMENDATION FOR OR-1

**Option D (PARTIAL) — new option; supersedes the runbook's A/B/C.**

- **REJECT B (overwrite canonical where legacy ⊇ canonical) — CATASTROPHIC.** Canonical is net-richer by **+27,764
  rows** over the sample; containment does **not** hold (neither bucket is a superset in any sampled class). Overwrite
  would replace canonical's 13-column `fixture_events` with legacy's 5-column stub and its correct 38-row
  `player_values` with the 640-row cartesian junk.
- **REJECT A (blanket row-union of all 13,222) — wrong instrument.** It would union incompatible schemas (5-col ∪ 13-col
  `fixture_events`), re-import the `player_values` corruption, and duplicate the `standings` aggregate-view rows into a
  bucket that deliberately no longer carries them. It also costs 13,222 read-merge-writes to recover data that is ~59%
  junk.
- **REJECT C (skip class B entirely) — loses the player_stats residue.** ~111,827 real 38-column rows for fixtures
  canonical demonstrably lacks. That is a data-pipeline-correctness violation, not an acceptable descope.
- **ADOPT D — targeted, schema-aware, per-entity union:**
  1. **`player_stats` only** — union legacy ∪ canonical per cell on the shared 38-col schema, keyed on
     `(fixture_id, player_id)`. Same schema both sides, so the union is well-defined and lossless. **De-duplicate on
     write** (canonical's 2× duplication defect would otherwise be inherited).
  2. **`fixture_events`** — do **not** union rows. Run a **fixture-coverage review** instead: enumerate the legacy-only
     `fixture_id`s and decide whether to **re-fetch them from api-football into the canonical 13-column schema** (the
     correct remedy — the data is upstream-available, per the external-data-always-available rule) rather than importing
     an unattributable stub.
  3. **`standings` / `teams` / `player_values`** — **NO ACTION.** Written disposition: snapshot skew with zero missing
     entities (standings/teams) and cartesian corruption (player_values). Document, do not merge.
- **Net effect on the cutover**: class B shrinks from **13,222 objects / 305k rows** to a **`player_stats`-scoped union
  plus a `fixture_events` re-fetch list** — a materially smaller, safer, and schema-correct Phase 2c.

### Consequences for the runbook

- **F-2 stands as a finding but its framing must be corrected**: "canonical is NOT a row-superset of legacy" is true,
  but so is the converse — _legacy is not a superset of canonical either_, and canonical is net-richer. The runbook's
  implied reading ("taking the phrase literally deletes 305,000+ rows") overstates by ~2.7×: the recoverable figure is
  ~111,827.
- **T2.4's ABORT clause is the operative one**, and it fires: _"any cell where legacy ⊄ canonical AND canonical ⊄ legacy
  (genuine divergence, not a subset) → STOP and escalate."_ Every sampled class is genuine divergence. A blind
  containment-based move was never viable.
- **OR-5 / `market-data-tick-sports` is untouched by this investigation** — its exact pass (T2.6) remains a hard gate.

## Loose ends / follow-ups (not fixed here — read-only investigation)

| #   | Finding                                                                                                                                                                                                               | Triage                                           |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| 1   | **Canonical `player_stats` holds exact-duplicate rows** (72 rows / 36 unique, `day=2021-05-08 league=LIGUE_2`). Independent of the cutover.                                                                           | New issue doc — data-correctness                 |
| 2   | **`standings` / `teams` write season-2026 live tables under historical `day=` partitions** (`day=2019-08-12` holds `season=2026` `update=2026-06-12` rows) across ~3,050 days. A partitioning defect in both buckets. | New issue doc — the canonical bucket inherits it |
| 3   | **A cartesian-junk `player_values` writer** produced a 640-row 20×32 object on 2026-06-22 at the canonical-shaped legacy path. Writer unidentified — possibly related to F-5's unidentified legacy writer.            | Feeds T0.1 / OR-2                                |

## Progress Log

**2026-07-16** — Investigation executed read-only per operator ruling. 3,946 legacy objects sampled across 10 days
(2018-09-22 … 2026-04-14); 3,051 paired; 62 class-B pairs reproduced (2.0%, scaling to ~13,000 vs the audited 13,222;
the `standings` signature reproduces the audited 91,380 exactly). Hypotheses (d) and (b) both DISPROVEN by direct
measurement; (a) and (c) carry ~59%; a genuine ~37% `player_stats` residue survives. Recommendation: **OR-1 option D
(partial, targeted, schema-aware)**. Zero mutations; scratch data deleted.

## RE-TRIAGE (2026-07-23)

**Verdict: RESOLVED BY LATER WORK.** This doc's own OR-1 option D recommendation was executed the SAME DAY it was
written, as **T2.4** of `plans/active/sports_legacy_bucket_cutover_2026_07_16.md`:

- **`player_stats` union — DONE**: T2.4 recovered **388,825** genuine legacy-only `(fixture_id, player_id)` rows across
  **4,015 cells, 0 FAIL**, dedupe-on-write, upsert-safe (re-read rows == union rows == unique keys, all 4,015 cells
  gated). T2.4's own progress log flags that this doc's 111,827 figure was a 10-day-sample extrapolation that
  under-counted the true population by ~3.5× — the full global-containment pass found more recoverable data than
  estimated here, not less.
- **`fixture_events` re-fetch review — DONE (produced a re-fetch list, not a blind row-union)**: T2.4 confirms "zero
  5-col degenerate stubs imported" and lists 40 cells / 1,542 fixtures for schema-upgrade re-fetch
  (`t2_4_refetch_fixture_events.json`) — exactly this doc's recommended remedy ("re-fetch from api-football into the
  canonical 13-column schema" rather than importing the unattributable stub).
- **`standings` / `teams` / `player_values` — NO ACTION**, per this doc's own ruling. Matches exactly.
- **Loose end #1 (canonical `player_stats` 2× duplicate defect) — FILED**:
  `issues/canonical_player_stats_fixture_events_quality_2026_07_16.md` (also measures the full-corpus scale: 740,725
  duplicate rows / 26%, T2.4's dedupe fixed only the 4,015 cells it touched, ~13,964 untouched cells still carry it).
  **Loose ends #2 (standings/teams 2026-live-under-historical-`day=` partitioning) and #3 (640-row cartesian
  `player_values` writer) — still genuinely unfiled**, confirmed by grep (no issue doc references either signature).

**Genuinely new finding, flagged per the findings-triage HARD RULE — CONFLICTS WITH ANOTHER DOC.**
`plans/active/sports_consolidated_closeout_2026_07_19.md`'s 2026-07-23 sweep section states (item **O**):
_"`sports_legacy_canonical_row_gap` OR-1 Option D (player_stats-only union + fixture_events re-fetch) **never
executed**"_ — this is **factually wrong**. T2.4 completed 2026-07-16, a full week before that sweep entry was written,
and is recorded in-body in `sports_legacy_bucket_cutover_2026_07_16.md` with a full evidence trail (per-cell gates,
evidence files, GCS backup paths). The sweep author appears not to have cross-checked the cutover plan's own T2.4 status
before writing item O. This doc's status is flipped to `resolved` on that basis; the closeout plan's item O should be
corrected in its own next pass (not done here — out of this task's scope, flagging only).
