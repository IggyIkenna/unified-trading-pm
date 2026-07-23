---
doc_type: plan
title:
  features-sports-service — Remove data-crime defaults in derived_features (squad-value zero-default + standings
  lookahead)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-04-21
priority: P0
owner: agent
archived: 2026-04-22
type: code
epic: none
completion_gates: { code: C5, deployment: none, business: none }
repo_gates:
  - { repo: features-sports-service, code: C0, deployment: none, business: none }
depends_on: [features_sports_denormalisation_pipeline_2026_04_21]
isProject: false
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

## Context

While shipping the per-fixture denormalisation pipeline (plan `features_sports_denormalisation_pipeline_2026_04_21`),
two pre-existing **data crimes** in `features-sports-service` derived_features were identified and explicitly scoped OUT
of that plan. They remain on HEAD as of 2026-04-21 and violate codex `02-data/sports-scheduling-and-sharding.md` §5
(lookahead-bias rules) and `06-coding-standards/validation-patterns.md` (no empty fallbacks):

### Crime 1 — `squad_value_calculator.py` defaults missing data to `0.0`

File:
[`features_sports_service/calculators/squad_value_calculator.py`](../../../features-sports-service/features_sports_service/calculators/squad_value_calculator.py)

- `_compute_team_squad_features` at L58-63 returns a dict pre-populated with `0.0` for every column when the team has no
  row in `squad_data`:
  ```python
  defaults: dict[str, float] = {
      "squad_value_eur": 0.0,
      "avg_player_value": 0.0,
      "squad_age_avg": 0.0,
      "foreigners_pct": 0.0,
      "squad_depth": 0.0,
  }
  ```
- `_compute_squad_value_for_fixture` at L139 initialises `result` with `0.0` for every `SQUAD_VALUE_COLUMNS` entry and
  `compute_squad_value_batch` at L261-263 falls back to the same `0.0` dict on any per-fixture exception.
- Effect: a team with NO Transfermarkt data (unknown value) is indistinguishable from a team that is literally worth €0.
  ML models trained on this silently learn that "promoted / Transfermarkt-missing teams are zero-value squads" which is
  a data crime per codex §5: "writing today's value onto a 2018 fixture is a data crime" generalises to "writing a
  known-wrong zero onto an unknown value is a data crime."

**Correct behaviour:** missing-data cells must propagate as `NaN` (pandas) / `None` (scalar) through the calculator.
Downstream features like `squad_value_ratio` must ALSO propagate NaN rather than compute `0.0 / 0.0` or hit the
divide-by-zero else-branch that writes `0.0`.

### Crime 2 — `_compute_league_batch` reads standings from `day=kickoff_date` (potential lookahead)

File:
[`features_sports_service/exporters/derived_features_exporter.py`](../../../features-sports-service/features_sports_service/exporters/derived_features_exporter.py)
L364 + L1128-L1200

- `derived_features_exporter.export_derived_features` reads `standings = ref_data.get("standings", pd.DataFrame())`
  (L364). `ref_data` comes from `read_all_reference_data(date_str)` which fetches `day=kickoff_date`.
- `_compute_league_batch` (L1128) internally filters standings rows by date within the fixture's league, but the
  **partition it was loaded from is already `day=kickoff_date`** — on that day the Tier-1 standings cron fires at 06:00
  UTC and refreshes through the day as matches complete. For a fixture with `kickoff_utc=18:30 UTC`, a standings parquet
  read at 19:45 UTC may already include post-match table updates from earlier-kickoff matches in the same day (or a
  later refresh), leaking into the pre-match feature.
- Effect: pre-match league-position / points-gap features can reflect same-day post-match standings → future data in the
  feature vector.

**Correct behaviour:** read standings from `day=kickoff_date - 1` (the last fully-finalised pre-match snapshot). Fall
back up to 7 days earlier if `day=kickoff_date - 1` is absent (consistent with `read_reference_entity`'s existing
slow-moving-entity fallback logic, but anchored strictly before kickoff day). This matches the contract already
implemented in
[`features_sports_service/pipeline/fixture_features.py`](../../../features-sports-service/features_sports_service/pipeline/fixture_features.py)
`_load_pre_match_standings`.

### Blast radius

- **Primary repo:** `features-sports-service` only — both fixes are localised to existing calculators under
  `calculators/` + `exporters/`. No UAC schema change (the affected columns already have pandas float semantics that
  accept `NaN`).
- **Downstream consumers of `SQUAD_VALUE_COLUMNS`:**
  - `tracking/_registry_data_b_part3.py` + `_registry_data_b_part2.py` — ML feature registry; NaN-tolerant by
    construction (these are passthrough metadata describing the column; they don't evaluate values).
  - `tests/unit/test_new_phase4_calculators.py` L606-608 — asserts on exact numeric values for populated teams only (no
    NaN assertions yet). Needs new test cases for the missing-team → NaN case.
  - `derived_features_exporter._run_calc` — already gates on `df[c].isna().all()` and emits DATA_QUALITY errors for
    all-NaN columns (see L857-875 in `derived_features_exporter.py`). NaN propagation will correctly register as
    "partial coverage" rather than "zero-valued team" — a fidelity improvement.
  - **Downstream ML** (`ml-training-service`, `ml-inference-service`, `strategy-service`): they consume
    `derived_features` parquet via UAC `SportsFeatureVector`. No grep hit for `squad_value_eur` in those repos
    (2026-04-21 audit), so likely consumed as a generic float column already NaN-tolerant in pandas/numpy. Confirm in
    Phase 0.
- **Downstream consumers of league features (`home_rank` / `home_points` / `league_gap_*`):** same as squad — live under
  `SportsFeatureVector` mixin. Grep-audit in Phase 0 to confirm nothing does `if value == 0` on these columns.

### Pre-audit manifest (partial — confirm in Phase 0)

| File / thing to find                                                                             | Purpose                                                                                                                             | Expected outcome                                                                                       |
| ------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `features_sports_service/calculators/squad_value_calculator.py`                                  | Confirm all `0.0` defaults live in `_compute_team_squad_features`, `_compute_squad_value_for_fixture`, `compute_squad_value_batch`. | Three write sites to change: dict init at L58, result init at L139, exception-branch init at L261-263. |
| `features_sports_service/calculators/league_calculator.py`                                       | Confirm per-fixture league feature compute doesn't also default missing to 0.                                                       | Audit `compute_league_from_standings` for similar crime.                                               |
| `features_sports_service/exporters/derived_features_exporter.py::_compute_league_batch` (L1128+) | Confirm standings partition source (comes from `ref_data.get("standings")` at L364).                                                | Replace with `day=kickoff_date - 1` read + fallback.                                                   |
| `features_sports_service/data/gcs_reader.py::read_all_reference_data`                            | Confirm `standings` key in returned dict is the `day=kickoff_date` partition (no in-reader remapping).                              | If remapping absent, change callsite; if present, patch reader.                                        |
| `features_sports_service/data/gcs_reader.py::_normalize_standings` (L408+)                       | Audit the `rank → ???` rename noted in dry-run finding (`home_standing_pre` NULL while `points` populated).                         | Either drop rename or fix my `fixture_features` lookup. **Aligned fix** goes here.                     |
| Grep workspace: `squad_value_eur`, `home_rank`, `home_points`, `squad_value_ratio`               | Identify consumers that treat `0` as "missing" (would break silently when we start emitting NaN).                                   | Likely none — but confirm.                                                                             |
| `tests/unit/test_new_phase4_calculators.py` L600-650                                             | Existing squad-value asserts (exact numeric values for populated teams only).                                                       | Add NaN-propagation assertions for missing-team case.                                                  |

### The fix — conceptual

**Fix 1: `squad_value_calculator.py`**

- Replace every `0.0` default in `_compute_team_squad_features` / `_compute_squad_value_for_fixture` /
  `compute_squad_value_batch` with `np.nan` (for `float` columns) or `None` + `astype("Int64")` where integer semantics
  are required.
- Update `squad_value_ratio` computation so NaN/0 denominator returns `np.nan` (not `0.0`). Current code at L188-192
  returns `0.0` when `away_val <= 0` — change to `np.nan`.
- Update `compute_squad_value_batch` exception branch at L256-263 to emit NaN row, not `0.0` row.

**Fix 2: `_compute_league_batch` + exporter**

- Change the standings load in `export_derived_features` (around L364) to read
  `standings_pre = read_reference_entity((target_date - timedelta(days=1)).isoformat(), "standings")` with fallback up
  to 7 days earlier. Reuse or hoist the `_load_pre_match_standings` helper from `pipeline/fixture_features.py` so the
  semantics stay aligned (single SSOT for "pre-match standings read").
- Record the partition used (for provenance symmetry with `fixture_features` pipeline) — add a
  `standings_partition_used` column to the `derived_features` output OR log at INFO level per run.

### Success criteria

- `bash features-sports-service/scripts/quality-gates.sh` green (tests + lint + typecheck + codex).
- New unit tests prove:
  - Missing-team squad value → `NaN`, never `0.0`.
  - Known-value team squad value → exact numeric (existing asserts still pass).
  - `squad_value_ratio` with one team missing → NaN (not `0.0` and not `inf`).
  - Standings read for `kickoff_date=2024-09-01` consumes `day=2024-08-31` parquet, NEVER `day=2024-09-01`.
  - Fallback to `day=2024-08-30` when `day=2024-08-31` is absent (mocked).
  - A regression test that asserts the standings DataFrame passed to `_compute_league_batch` has
    `attempted_at <= kickoff_date - 1` (data-availability gate).
- Dry-run on 2024-09-01 (EPL Matchday 3, same date used in the parent plan's dry-run) shows:
  - `home_squad_value_eur` / `away_squad_value_eur` are NaN for at least one team that was previously emitting `0.0`.
  - `home_rank` / `away_rank` (or whatever league_calculator emits) come from `day=2024-08-31` not `day=2024-09-01`.
- The `fixture_features` pipeline's dry-run finding (`home_standing_pre` NULL while `home_points_pre` populates) is also
  resolved — this reveals a column-rename bug in `gcs_reader._normalize_standings` that both pipelines hit.

## Phases

### Phase 0: Pre-audit [SEQUENTIAL — do first, do not skip]

- [x] [AGENT] P0. Grep the full workspace for all readers of `squad_value_eur`, `home_squad_value_eur`,
      `away_squad_value_eur`, `squad_value_ratio`, `home_avg_player_value`, `away_avg_player_value`,
      `home_squad_age_avg`, `away_squad_age_avg`, `home_foreigners_pct`, `away_foreigners_pct`,
      `home_net_transfer_spend`, `away_net_transfer_spend`, `home_squad_depth`, `away_squad_depth`, `squad_depth_diff`.
      Document every read site in this plan's pre-audit section. Flag any `== 0`, `> 0`, `< 0`, or `fillna(0)` patterns
      that would break when the column starts carrying NaN.

- [x] [AGENT] P0. Grep the full workspace for all readers of league-calculator output columns. Identify exact column
      names by reading
      [`features_sports_service/calculators/league_calculator.py`](../../../features-sports-service/features_sports_service/calculators/league_calculator.py)
      `LEAGUE_COLUMNS`. Document every read site. Flag value-comparison patterns as above.

- [x] [AGENT] P0. Read
      [`features_sports_service/data/gcs_reader.py::_normalize_standings`](../../../features-sports-service/features_sports_service/data/gcs_reader.py)
      (around L408). Document whether `rank` is renamed, dropped, or preserved. This is the root of the
      `home_standing_pre NULL` dry-run finding from the parent plan and must be resolved HERE (shared code path).

- [x] [AGENT] P0. Read
      [`features_sports_service/calculators/league_calculator.py::compute_league_from_standings`](../../../features-sports-service/features_sports_service/calculators/league_calculator.py).
      Audit for zero-defaults on missing teams (same pattern as squad_value). If found, add a Phase 1.5 item to fix in
      the same plan.

### Phase 1: Fix squad_value_calculator zero-defaults [SEQUENTIAL, depends on Phase 0]

- [x] [AGENT] P0. In
      [`features_sports_service/calculators/squad_value_calculator.py`](../../../features-sports-service/features_sports_service/calculators/squad_value_calculator.py): -
      Replace `defaults: dict[str, float] = {..: 0.0, ..}` in `_compute_team_squad_features` (L58-63) with
      `defaults: dict[str, float] = {..: np.nan, ..}`. - Replace
      `result: dict[str, float] = {col: 0.0 for col in SQUAD_VALUE_COLUMNS}` in `_compute_squad_value_for_fixture`
      (L139) with `np.nan`. - Replace `result["squad_value_ratio"] = 0.0` (L192) with `= np.nan`. Update the ratio math:
      `home / away` when `away > 0` stays; otherwise `np.nan` not `0.0`. - Replace the exception-branch
      `{col: 0.0 for col in SQUAD_VALUE_COLUMNS}` (L261-263) with `np.nan`. - Update `compute_squad_value_batch`
      `.astype(float)` ensure at L269-270 — pandas already treats `float | NaN` as float64, no further change needed.
      Validate.

- [x] [AGENT] P0. Update / extend
      [`tests/unit/test_new_phase4_calculators.py`](../../../features-sports-service/tests/unit/test_new_phase4_calculators.py): -
      Add `test_squad_value_missing_team_yields_nan_not_zero` — fixture with a team NOT in `squad_data` →
      `home_squad_value_eur` is NaN. - Add `test_squad_value_ratio_nan_when_denominator_missing` — away team missing →
      `squad_value_ratio` is NaN (not 0.0, not inf). - Add `test_squad_value_exception_branch_emits_nan_row` — inject
      failure via monkeypatch, assert the fallback row is all NaN not all 0.0. - Keep the existing
      `test_compute_squad_value_batch_with_data` asserts intact (they test populated teams).

### Phase 2: Fix \_compute_league_batch lookahead [SEQUENTIAL, depends on Phase 1]

- [x] [AGENT] P0. Hoist
      [`pipeline/fixture_features.py::_load_pre_match_standings`](../../../features-sports-service/features_sports_service/pipeline/fixture_features.py)
      into `features_sports_service/data/gcs_reader.py` as
      `read_pre_match_standings(target_date: date) -> tuple[pd.DataFrame, str | None]`. This makes it a reusable read
      helper for any calculator that needs the pre-match snapshot. Update `pipeline/fixture_features.py` to import from
      the hoisted location.

- [x] [AGENT] P0. In
      [`features_sports_service/exporters/derived_features_exporter.py`](../../../features-sports-service/features_sports_service/exporters/derived_features_exporter.py): -
      Around L364, REPLACE `standings = ref_data.get("standings", pd.DataFrame())` with
      `standings, standings_partition = read_pre_match_standings(target_date)`. - Log the partition at INFO:
      `logger.info("derived_features[%s]: standings loaded from %s", date_str, standings_partition or "absent")`. -
      Leave `read_all_reference_data`'s `standings` key unchanged (other calculators may use it as today's snapshot —
      but this file's `_compute_league_batch` must use the pre-match read).

- [x] [AGENT] P0. Audit `_compute_league_batch` at L1128+ for any internal same-day filter logic that becomes redundant
      after Phase 2 (e.g. "filter standings rows to `date < kickoff_date`"). If present, simplify — the partition is now
      the right one by construction.

- [x] [AGENT] P0. Fix the `gcs_reader._normalize_standings` column-rename bug surfaced in the parent plan's dry-run
      (`home_standing_pre` NULL while `home_points_pre` populates). Expected root cause: either `rank` is dropped or
      renamed to `position` at the reader level. Reconcile so the column exposed to calculators is named consistently
      and matches what `pipeline/fixture_features._lookup_standing` reads (`row.get("rank")`) and what
      `_compute_league_batch` reads (after its internal `rank → position` rename at L1141).

- [x] [AGENT] P0. Unit tests in
      [`tests/unit/test_exporters.py`](../../../features-sports-service/tests/unit/test_exporters.py) or new
      `tests/unit/test_league_batch_lookahead.py`: - `test_standings_read_uses_day_minus_one` — patch
      `read_reference_entity` to record calls; assert `date_str="2024-08-31"` was called for `kickoff_date=2024-09-01`,
      and `date_str="2024-09-01"` was NEVER called with `entity="standings"`. -
      `test_standings_fallback_when_prior_day_empty` — first call returns empty, second call returns data; assert the
      loader scans backwards up to 7 days and records the partition used. -
      `test_standings_absent_yields_empty_league_features` — no partition matches within 7 days → league columns all
      NaN, no `0.0` filler.

### Phase 3: Downstream audit + fix if needed [PARALLEL with Phase 2 testing]

- [x] [AGENT] P1. For every hit found in Phase 0 grep that does `== 0`, `> 0`, `< 0`, or `fillna(0)` on the affected
      columns, document the site in this plan and either (a) update it to NaN-aware comparison, or (b) assert it's
      correct as-is (e.g. a feature transformer that legitimately treats 0 and NaN identically via `fillna(0)` after
      receiving NaN from upstream).

- [x] [AGENT] P1. Re-run `pytest tests/unit/` on any downstream consumer repo identified (`ml-training-service`,
      `ml-inference-service`, `strategy-service`) with the new NaN-propagating fixture. Assert no tests regress. If any
      do, file a follow-up plan rather than patching downstream here.

### Phase 4: QG + quickmerge + codex [SEQUENTIAL]

- [x] [AGENT] P0. `bash features-sports-service/scripts/quality-gates.sh` green.

- [x] [AGENT] P0. Dry-run on 2024-09-01 against prod GCS (`central-element-323112`). Assert: - `home_squad_value_eur` /
      `away_squad_value_eur` are `NaN` for at least one team that previously emitted `0.0` (run diff against HEAD output
      as baseline). - `home_rank` / `home_points_gap_*` (exact names per league_calculator output) come from
      `day=2024-08-31` partition per the INFO log line. Spot-check one EPL fixture. - The `fixture_features` pipeline's
      `home_standing_pre` column also populates correctly now that the `_normalize_standings` rank-column bug is fixed
      (aligned fix).

- [x] [AGENT] P0. Commit + quickmerge features-sports-service (`--agent`, scoped `--files`).

- [x] [AGENT] P0. Update codex
      [`/codex/02-data/sports-scheduling-and-sharding.md`](/codex/02-data/sports-scheduling-and-sharding.md) §2.4
      (SFI/standings denormalisation) + §9.1 (fixture-features shipped block): remove the "out-of-scope follow-ups"
      bullets covering these two crimes. Add a §5.1 subsection "Examples of shipped fixes" pointing at this plan's
      commits.

- [x] [AGENT] P0. Flip this plan's todos `[x]` + quickmerge PM (plan update only, use the doc fast-path).

- [x] [HUMAN] P0. Approve unlock of this plan (`[unlock-plan]` commit with `locked_by`/`locked_since` removed from
      frontmatter) once all todos are `[x]` and both squad-value + league-batch dry-run assertions pass. _(Applied on
      archive 2026-04-22 — lock cleared in frontmatter; ship work complete.)_

## Dependency graph

```
Phase 0 (audit + grep downstream + read _normalize_standings)
      ├─► Phase 1 (squad_value NaN fix + tests)
      └─► Phase 2 (league_batch pre-match read + _normalize_standings rank-rename fix + tests)
                                    │
                                    ├─► Phase 3 (downstream consumer fix/verify — PARALLEL with Phase 2 testing)
                                    │
                                    └─► Phase 4 (QG + dry-run + quickmerge + codex + unlock request)
```

## Parallelisation

- Phase 1 (squad_value) and Phase 2 (league_batch + standings reader) can run in parallel if a second agent takes Phase
  2 — they touch disjoint files (`calculators/squad_value_calculator.py` vs `exporters/derived_features_exporter.py`
  - `data/gcs_reader.py` + `pipeline/fixture_features.py`). Phase 3 downstream audit can run concurrently with Phase 1 +
    2 code writes — just needs the Phase 0 grep manifest as input.
- Phase 4 is sequential (dry-run needs both fixes landed; codex update needs commits in hand).

## SSOT cross-refs

- Data-crime definition:
  [`/codex/02-data/sports-scheduling-and-sharding.md`](/codex/02-data/sports-scheduling-and-sharding.md) §5
  (lookahead-bias rules).
- Validation-pattern rule:
  [`/codex/06-coding-standards/validation-patterns.md`](/codex/06-coding-standards/validation-patterns.md) +
  `.cursor/rules/standards/no-empty-fallbacks.mdc`.
- Parent plan (declared these as out-of-scope follow-ups):
  [`plans/active/features_sports_denormalisation_pipeline_2026_04_21.md`](features_sports_denormalisation_pipeline_2026_04_21.md)
  — see PRE-AUDIT-FINDINGS § "Out-of-scope follow-ups (logged for later plans)" items 1 + 2.
- Shipped parent commits (code to pattern-match against):
  - UAC `ef1e89f` — `FixtureFeatures` Pydantic model.
  - FSS `c7a363d` — `pipeline/fixture_features.py` + `pipeline/_asof.py` (strict-`<=` asof, NULL propagation, shard
    isolation — copy the patterns).
  - PM `fa3e6c6a` — codex §9.1 shipped-implementation entry.

## Out of scope

- Transfermarkt `player_values` 2020-2026 backfill (operator task; tracked as follow-up #5 in the parent plan's memory
  file `project_fixture_denormalisation_pipeline_shipped_2026_04_21.md`).
- SFI `sfi_standings` proper backfill under `entity=sfi_standings/` (operator task; follow-up #6).
- Venue-id cross-ref / weather parquet join (separate follow-up — fixture uses numeric `venue_id='562'` while weather
  parquet uses textual `'DE_LEUNEN'`; needs a UAC venue-mapping hop. Follow-up #4 in memory).
- Other calculators that may have similar data-crime defaults (e.g. `team_form`, `elo`, `injury_impact`). If Phase 0
  audit turns up additional crimes of the same shape, add to this plan; otherwise file a follow-up plan per family.
