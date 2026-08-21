---
doc_type: plan
title: api_football_minimal_flattening_removal_2026_05_07
summary: Stop dropping nested API-Football payloads at write time. Today FIXTURE_STATS / FIXTURE_EVENTS / FIXTURE_LINEUPS
  / INJURIES persist only `fixture_id + data_available_at` over what FIXTURES already has — every per-team / per-event /
  per-player field in the payload is dropped during ingest. Flatten at the UAC normalizer level so the parquets carry the
  actual signal (xG, shots, possession, cards, formations, lineup grids, injury reasons).
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-ui, features-service, instruments-service, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: []
related:
  [
    sports_uac_schema_contracts_registration_2026_04_24.plan.md (archived),
    /plans/archive/data_status_drilldown_shard_atom_alignment_2026_05_07.md,
  ]
created: "2026-05-07"
type: code
epic: epic-code-completion
completion_gates: { code: C5, deployment: D3, business: none }
repo_gates:
  - { repo: unified-api-contracts, code: C2, deployment: none, business: none }
  - { repo: instruments-service, code: C2, deployment: none, business: none }
  - { repo: features-service (sports family), code: C2, deployment: none, business: none }
  - { repo: unified-trading-pm, code: C2, deployment: none, business: none }
depends_on: []
todos: []
isProject: false
estimate_class: refactor
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 3.2
estimate_calibration_note: "Backfilled 2026-05-13: 16 todos, 13 done (near complete; 3 left). Reclassified
  design→refactor — mechanical UAC normalizer flatten + adapter writer updates + downstream feature consumers;
  per-payload-key column additions, not closed-set design calls. Baseline 8 (16 todos × ~0.5 mech), × 0.4 = 3.2. #
  operator-confirm class — borderline refactor/design.

  "
---

> **ARCHIVED 2026-05-20** — 100% complete (all 16 items shipped + DEFERRED resolved 2026-05-20 slot-8); preserved for
> archaeology. No deferred work outstanding.

> **🟡 STAMPING SCOPE FOLDED INTO UMBRELLA — `available_at_lookahead_bias_completion_2026_05_08`** (codified 2026-05-08)
>
> Per operator direction this session — `available_at` stamping wiring (Phase 3 scope: fixture_stats → match_end_time /
> fixture_events → event_time / lineups → kickoff−60min / injuries → report_time) executes as part of the umbrella's
> per-asset_group cascade — NOT in isolation. Source-specific stamping rule (UAC SSOT) + per-adapter `available_at`
> column write + UTL `record_captured` enforcement co-evolve.
>
> Stamping owner:
> [`plans/active/available_at_lookahead_bias_completion_2026_05_08.md`](available_at_lookahead_bias_completion_2026_05_08.md)

# api_football minimal-flattening removal

## Why

The deployment-ui Schema modal for `(sports, match, fixture_stats)` shows the contract has only two columns:
`fixture_id` (string) and `data_available_at` (datetime). FIXTURES already provides 30+ rich columns including all of
`af_fixture_id`, scores, status, league, season, both team IDs+names, kickoff timestamp, half periods, etc. So
FIXTURE_STATS today contributes **zero signal** over FIXTURES — it's a value-destroying duplicate.

The `_sports_match_contracts.py` module docstring openly admits it: _"the instruments-service adapter currently performs
**minimal flattening** at write-time: only the top-level identifier columns + `data_available_at` make it onto disk for
`fixture_events`, `fixture_stats`, and `fixture_lineups`. The nested arrays of stat-name/stat-value tuples
(FIXTURE_STATS), event-time/player tuples (FIXTURE_EVENTS), and player-grid coordinates (FIXTURE_LINEUPS) are dropped
today; this is a known limitation, not a contract gap."_

Confirmed by audit:

- `unified_api_contracts/external/api_football/normalize.py:377-381` —
  `normalize_api_football_fixture_stats(raw, fixture_id)` literally returns `dict(raw)` with `fixture_id` stamped on. No
  unpacking of the `statistics: [{type: ..., value: ...}, ...]` array.
- Same shape at lines 384-388 (`fixture_event` — `events: [{time, team, player, type, detail}]` lost) and 391-395
  (`lineup` — `startXI: [{player, pos, grid}]` + `substitutes: [...]` lost).
- For INJURIES, `normalize_api_football_injury` at line 372-374 likewise returns the raw dict as-is; pyarrow keeps the
  four nested struct columns (`player`, `team`, `fixture`, `league`) but each is opaque to downstream readers and
  there's no row-per-(player, team, fixture) explosion.

The API-Football payloads that get dropped today are **the high-signal columns sports prediction features need**:

| Endpoint               | Today's stored columns            | Dropped (per the API payload + UAC docstring)                                                                                                                                                                                                                                                       |
| ---------------------- | --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/fixtures/statistics` | `fixture_id`, `data_available_at` | `team_id`, `shots_total`, `shots_on_target`, `shots_off_target`, `shots_inside_box`, `shots_outside_box`, `corners`, `offsides`, `ball_possession`, `yellow_cards`, `red_cards`, `goalkeeper_saves`, `passes_total`, `passes_accurate`, `passes_pct`, `expected_goals`, `goals_prevented` × 2 teams |
| `/fixtures/events`     | `fixture_id`, `data_available_at` | `time_elapsed`, `time_extra`, `team_id`, `player_id`, `player_name`, `assist_id`, `assist_name`, `event_type` (Goal/Card/Subst/Var), `event_detail` (Normal Goal / Yellow Card / etc), `comments` (per event row)                                                                                   |
| `/fixtures/lineups`    | `fixture_id`, `formation`         | `coach_id`, `coach_name`, `team_id`, `player_id`, `player_name`, `player_number`, `player_pos` (G/D/M/F), `player_grid` ("4:1" coords), `is_starter`/`is_sub` (per player row)                                                                                                                      |
| `/injuries`            | (4 opaque struct columns)         | Need flat: `player_id`, `player_name`, `player_photo`, `team_id`, `team_name`, `fixture_id`, `league_id`, `season`, `injury_reason`, `injury_type`                                                                                                                                                  |

Without this flattening, every features-sports calculator that wants "shots-on-target advantage", "xG delta",
"possession differential", "first-15-min momentum", "lineup-strength delta" runs on empty / NaN. The features pipeline
can never compute the high-Sharpe signals the strategy layer was designed for.

## Scope (the gap to close)

Three layers of work, sequenced by dependency:

1. **UAC normalize*api_football*\*** — flatten the nested arrays into a list[dict] of per-(team, event, player, …) rows.
   This is where the actual unpacking happens. Pure function on the raw payload; no I/O.
2. **UAC contracts** — declare the expanded SchemaContract for each data_type, listing every flat column with dtype +
   nullable + description. Today's two-column contract becomes ~20-row per fixture for fixture_stats, ~30-row per
   fixture for fixture_events, ~22-row per (fixture, team) for fixture_lineups, ~10-row per (fixture, player) for
   injuries.
3. **instruments-service api_football handler** — the adapter at
   `reference_data/adapters/sports/adapters/api_football.py` already calls the normalizer; once the normalizer returns
   multiple rows, the handler downstream of `get_fixture_statistics` / `get_fixture_events` / `get_fixture_lineups` /
   `get_injuries` writes them all. `to_parquet` already handles list-of-dict; the column shape just needs to match the
   new contract.

Optional (Phase 4): one-shot reprocessor that re-fetches fixtures with the captured `af_fixture_id` set and rewrites the
parquets in place. Or skip — the daily forward-poll picks up new fixtures with the new shape and the historical "thin"
rows survive until features-sports needs them. Decide post-Phase-3.

## What this changes vs current state

**Today (verified 2026-05-07):**

- `(sports, match, fixture_stats)` parquet: 1 row per fixture, 2 columns (`fixture_id`, `data_available_at`).
- Schema modal shows: `Schema: FIXTURE_STATS · Source: CONTRACT_REGISTRY · symbol_column: fixture_id` with 2 columns.
- Coverage panel: `FIXTURE_STATS 121,987 / 165,517 shards (74%)` — but every "captured" shard is functionally empty for
  downstream features.
- Features-sports calculators that try to compute `xg_advantage_home_minus_away`, `shots_on_target_diff`,
  `possession_pct_home_minus_away`, etc. on these parquets read NaN every time. The features-sports honest-coverage
  panel hides this because the features-sports writer emits its OWN row even when the upstream is empty (no cross-source
  NaN-rate gate yet — separate writegate concern).

**After this plan ships:**

- `(sports, match, fixture_stats)` parquet: 2 rows per fixture (one per team), ~18 columns including `team_id`,
  `is_home`, `shots_total/on/off`, `corners`, `expected_goals`, `ball_possession_pct`, `passes_pct`, etc.
- Same shape change for fixture_events (per-event row), fixture_lineups (per-player row), injuries (per-player row).
- Features-sports calculators for "shots-on-target advantage", "xG delta", "lineup-strength delta", etc. become
  computable from real data. Existing NaN-rate write-gate (in features-sports calculators) starts rejecting legitimately
  empty fixtures (paused leagues, delayed reports) instead of silently writing zeros.
- Coverage % stays similar at the manifest level; the **content quality** shifts from 0% → ~95% useful.

## Pre-audit blast radius

**unified-api-contracts**:

- `unified_api_contracts/external/api_football/normalize.py` — 4 functions to rewrite (lines 372, 377, 384, 391). Each
  returns `list[dict]` instead of `dict` so the caller's existing `[normalize(row) for row in raw_rows]` comprehension
  naturally explodes the nested array.
- `unified_api_contracts/internal/schemas/_sports_match_contracts.py` — 4 `SchemaContract` definitions to extend (lines
  318 SPORTS_FIXTURE_STATS, 348 SPORTS_FIXTURE_LINEUPS, plus the EVENTS + INJURIES contracts in adjacent files). Add
  explicit `ColumnSpec` per dropped field. Keep `symbol_column="fixture_id"` (or `"player_id"` for injuries) and
  `required_row_count_min=0` (legitimately-empty fixtures still allowed).
- Tests: `tests/unit/test_normalize_api_football.py` (or sister) needs new fixture-payloads + assertions on the flat
  shape. ~150 LOC of test data + assertions.

**instruments-service**:

- `instruments_service/reference_data/adapters/sports/adapters/api_football.py` — the handlers at lines 422
  (`get_fixture_statistics`), 442 (`get_fixture_events`), and the lineup / injury equivalents already iterate raw*rows
  and call `normalize*\*`. Once normalize returns `list[dict]`per row, the handler needs to`chain.from_iterable` to
  flatten to a single per-fixture list. ~30 LOC delta.
- `to_parquet` writer: already accepts `list[dict]` and writes flat columns; no change.
- Manifest writer: already records 1 row per (fixture_id, day). Stays per-fixture even though parquet has 2 rows per
  fixture (sports shard atom is `(league_id, day)`, not `(fixture_id, team_id, day)`).

**features-service (sports family)**:

- Calculators that today read `fixture_stats.parquet` and find no useful columns: this is where the win lands. Extend
  the relevant calculators to consume the new columns (xg_advantage, shots_on_target_diff, etc.). Out-of-scope for this
  plan; tracked separately under the features-sports honest-coverage / dependency plan.

**unified-trading-pm**:

- This plan in `plans/ai/` until user-approved → `plans/active/`.
- Codex doc `/codex/02-data/sports-data-source-coverage-matrix.md` — note the per-data_type column-count expectation so
  future audits catch a regression.

## Phased execution DAG

```
Phase 1 (UAC normalizer)   →   Phase 2 (UAC contracts)   →   Phase 3 (adapter handler)
─────────────────────────       ─────────────────────────       ───────────────────────────
Rewrite 4 normalize fns     Extend 4 SchemaContracts        Adapter `chain.from_iterable`
+ new unit tests            with full ColumnSpec lists      + smoke against API-Football
                                                            + one fresh ingest day
                                                                    ↓
                                                    Phase 4 (optional reprocessor)
                                                    ──────────────────────────────
                                                    Backfill historical parquets
                                                    OR skip + let forward-poll handle
                                                            ↓
                                                    Phase 5 (codex doc + plan close)
```

Phase 1 + 2 can run partially in parallel (contract is the type, normalizer is the implementation; both must agree).
Phase 3 depends on both. Phase 4 is independent, can defer indefinitely.

## Phase-by-phase tasks

### Phase 1 — UAC normalizer flattening

- [x] [UAC] P0. `normalize_api_football_fixture_stats(raw, fixture_id) -> list[dict]`. Unpack the `team` +
      `statistics: [{type, value}, ...]` payload into 2 rows (one per team) with explicit columns: `team_id`,
      `team_name`, `is_home` (bool, derived from raw `team.id == fixture.teams.home.id`), then one column per stat-type
      from the closed enum (`shots_total`, `shots_on_target`, `shots_off_target`, `shots_inside_box`,
      `shots_outside_box`, `corners`, `offsides`, `ball_possession_pct`, `yellow_cards`, `red_cards`,
      `goalkeeper_saves`, `passes_total`, `passes_accurate`, `passes_pct`, `expected_goals`, `goals_prevented`). Use
      `_safe_int` for integer-typed stats and `_safe_pct`/`_safe_float` helper for percentage / float types.
      (UAC@c76e6d0 — closed-set `_FIXTURE_STAT_TYPE_MAP` drives the column population; `is_home` left None for the
      orchestrator to stamp via fixture cross-reference.)
- [x] [UAC] P0. `normalize_api_football_fixture_event(raw, fixture_id) -> list[dict]`. Unpack each event in the
      `events: [...]` array into one row with: `time_elapsed`, `time_extra` (nullable int), `team_id`, `team_name`,
      `player_id`, `player_name`, `assist_id`, `assist_name` (nullable), `event_type` (Goal/Card/subst/Var),
      `event_detail`, `comments` (nullable string). (UAC@c76e6d0)
- [x] [UAC] P0. `normalize_api_football_lineup(raw, fixture_id) -> list[dict]`. Today returns one row per team with
      `formation` only. Extend to: one row per (team, player) — flatten
      `startXI: [{player.id, .name, .number, .pos, .grid}]` AND `substitutes: [...]` AND coach. Columns: `team_id`,
      `team_name`, `formation`, `coach_id`, `coach_name`, `player_id`, `player_name`, `player_number`, `player_pos`
      (G/D/M/F), `player_grid` (e.g. "4:1"), `is_starter` (bool). (UAC@c76e6d0 — coach NOT emitted as own row; stamped
      on every (team, player) row to preserve grain.)
- [x] [UAC] P0. `normalize_api_football_injury(raw) -> dict`. Flatten the 4 nested struct columns (`player`, `team`,
      `fixture`, `league`) into top-level: `player_id`, `player_name`, `player_photo`, `player_type`, `player_reason`,
      `team_id`, `team_name`, `fixture_id`, `league_id`, `league_season`. Returns single dict (one injury report = one
      row), but with all useful fields surfaced. (UAC@c76e6d0)
- [x] [UAC] P0. Tests at `tests/unit/test_normalize_api_football.py` extend the existing fixture-statistics / events /
      lineups / injuries test cases with full payload fixtures + per-column assertions. Verify shape (list-of-dict
      count) + per-column dtype + null handling. (UAC@c76e6d0 — 13 new tests, all green.)

### Phase 2 — UAC contracts

- [x] [UAC] P0. `_sports_match_contracts.py` SPORTS_FIXTURE_STATS extension. Replace the current 2-column ColumnSpec
      list with the full ~18-column spec, each entry naming dtype, nullable, description. Remove the "Adapter currently
      writes only fixture_id + data_available_at" comment block. `symbol_column` stays `fixture_id`. Note:
      `required_row_count_min=0` stays — legitimately-empty fixtures (e.g. abandoned matches) still allowed.
      (UAC@c76e6d0 — 23 columns including `data_available_at`.)
- [x] [UAC] P0. SPORTS_FIXTURE_EVENTS analogous extension. ~10 columns. (UAC@c76e6d0 — 13 columns.)
- [x] [UAC] P0. SPORTS_FIXTURE_LINEUPS analogous extension. ~12 columns. (UAC@c76e6d0 — 13 columns.)
- [x] [UAC] P0. SPORTS_INJURIES analogous extension. ~10 columns. (UAC@c76e6d0 — 11 columns; `symbol_column` migrated
      from the legacy `player` struct to the flat `player_id` field.)
- [x] [UAC] P0. Update module docstring to remove the "minimal flattening is a known limitation" disclaimer and replace
      with a forward-looking note pointing at this plan's commits. (UAC@c76e6d0)

### Phase 3 — instruments-service adapter handler

- [x] [instruments-service] P0. `api_football.py` — handler list-comprehensions become
      `list(itertools.chain.from_iterable(normalize_*(row, fixture_id) for row in raw_rows))` for the 3 list-returning
      normalizers (stats, events, lineups). INJURIES stays single-dict per row. (instruments-service@539130f — also
      tightens return-type annotations from `list[CanonicalX]` to `list[dict[str, object]]` to match the actual runtime
      shape + base-class signature, drops unused Canonical\* imports.)
- [x] ✅ [instruments-service] P0. **SHIPPED 2026-05-16 (slot 4)** — live-API smoke against fixture_id=1208051
      (Liverpool vs Man Utd 2024-12-22) verified the chain.from_iterable + normalizer composition produces expected
      multi-row expansion end-to-end: - fixture_stats: **2 rows × 22 cols** per-team (expected ≥2 / ~18-22 cols ✅) -
      fixture_events: **25 rows × 12 cols** per-event (expected ≥1 ✅) - fixture_lineups: **40 rows × 12 cols**
      (expected ≥22 — 11 starters × 2 teams ✅) - injuries (date=2026-05-16): **540 rows × 10 cols** date-level fetch ✅
      Smoke script `instruments-service/scripts/smoke_api_football_flattening_2026_05_16.py` uses
      `get_secret('api-football-api-key')` from vaulted credential (operator provisioned pre-2026-05-16). Re-runnable.
- [x] ✅ [instruments-service] P0. EPL forward-poll verified end-to-end (2026-05-19): GCS parquet
      `sports_reference/by_date/day=2026-05-13/entity=fixture_stats/league=EPL/fixture_stats.parquet` has shape (2, 23)
      — 2 rows per fixture (one per team) × 23 columns including `team_id`, `team_name`, `is_home`, `shots_on_target`,
      `shots_off_target`, `shots_total`, `ball_possession_pct`, `expected_goals`, `goals_prevented`, `passes_pct`,
      `corners`, `offsides`, `yellow_cards`, `red_cards`, `goalkeeper_saves`, `passes_total/accurate`,
      `data_available_at`. Confirms flattening code (IS@539130f) is live in production. Old 2-column schema is gone.
      PM@2f710f9a (plan closeout flip).

### Phase 4 — Optional historical reprocessor

- [x] ✅ [CANCELLED — optional, default skip per plan] [instruments-service] P1. One-shot historical reprocessor — plan
      body explicitly recommends skipping: "quota cost > marginal value on stale fixtures." Forward-poll naturally fills
      new fixtures with new shape. Historical thin rows (pre-2026-05-08) handled by per-calculator NaN gate + UTL
      `assert_available_at_present`. Re-evaluate only if features-sports calculators become critically blocked on
      historical rows. pm@<flip-sha>.

### Phase 5 — Codex doc + plan close

- [x] ✅ [unified-trading-pm] P2. `/codex/02-data/sports-data-source-coverage-matrix.md` adds an explicit "expected
      column count per data_type" so a future audit catches a regression to the minimal-flattening shape. (PM@36c40a10 —
      shipped in the original DONE-2026-05-08 cycle; checkbox was inadvertently not flipped at that time. Flipped now.)
- [x] ✅ [unified-trading-pm] P2. Plan closes out: all phases shipped. 3.B live-API smoke ✅ (2026-05-16, slot 4); 3.C
      EPL forward-poll ✅ (2026-05-19); Phase 4 CANCELLED (optional skip); Phase 5.A/5.B closed. Full plan 100%.
      PM@2f710f9a (2026-05-13 closeout) + Phase 3.B/3.C completed post-2026-05-13.

## Success criteria

- **Code gates (per repo):** `bash scripts/quality-gates.sh` passes on UAC + instruments-service.
- **Test gates:** new normalizer unit tests pass; integration smoke (one EPL forward-poll day) lands parquets with the
  expected shape and column count.
- **Visual gate:** deployment-ui Schema modal for `(sports, match, fixture_stats)` shows ~18 columns instead of 2; same
  shape change visible for fixture_events / fixture_lineups / injuries. The 'No schema yet' message never appears for
  these.
- **Functional gate:** one features-sports calculator (e.g. `shots_on_target_advantage`) successfully reads the new
  columns from the new parquets — proves the full path works end-to-end.

## Temporary states + their canonical follow-up plans

- **Historical thin parquets** survive until Phase 4 reprocessor runs OR until forward-poll naturally overwrites.
  Successor: this plan's Phase 4 (optional). features-sports calculators that read these parquets must NaN-handle the
  missing per-team rows for now (existing UTL `assert_available_at_present` + features-sports per-calculator NaN gate
  already handles).
- **Backfill range gate** (`DATA_TYPE_COVERAGE_START` already pins these data_types to 2020-06-06 per the workspace rule
  on api_football historical coverage) — no change needed; pre-2020-06-06 dates stay pre-skipped.

## What this plan does NOT do (out of scope)

- features-sports calculator updates that consume the new columns. Tracked separately — those calculators exist today
  reading mostly empty parquets; they'll naturally start producing real signal once the new columns are populated, but
  extending their feature lists (e.g. adding `xg_advantage_home_minus_away` as a new feature) is its own plan.
- footystats / understat / SFI per-source flattening. Those are separate sources with separate normalizers; similar
  audit might be useful but is not in this plan's scope.
- A reprocessor that re-fetches API quota for years of historical fixtures. Phase 4 is optional and the default
  recommendation is to skip it — quota cost > marginal value on stale fixtures.

## References

- `unified-api-contracts/unified_api_contracts/external/api_football/normalize.py` lines 372-395 — the 4 pass-through
  normalizers to rewrite.
- `unified-api-contracts/unified_api_contracts/internal/schemas/_sports_match_contracts.py` lines 1-25 — module
  docstring acknowledging the minimal-flattening limitation; lines 318 + 348 — the contracts to extend.
- `instruments-service/instruments_service/reference_data/adapters/sports/adapters/api_football.py` lines 422-460 — the
  handlers that call the normalizers.
- API-Football docs: <https://www.api-football.com/documentation-v3#tag/Fixtures-statistics> (statistics endpoint),
  <https://www.api-football.com/documentation-v3#tag/Fixtures-events> (events),
  <https://www.api-football.com/documentation-v3#tag/Fixtures-lineups> (lineups),
  <https://www.api-football.com/documentation-v3#tag/Injuries> (injuries).
- Reference incident 2026-05-07: user inspected the FIXTURE_STATS schema modal in the deployment-ui data-status panel,
  observed only `fixture_id + data_available_at`, and asked whether this duplicated FIXTURES (yes, today it does —
  that's the bug).

## DONE-2026-05-13 — Slot 6 Wave 3 cycle (plan closeout)

Slot 6 Wave 3 closed out residual checkboxes: flipped Phase 5.A (codex doc shipped PM@36c40a10 but checkbox missed) and
Phase 5.B (plan closeout). Phase 3.B/3.C were deferred at this point but completed subsequently: Phase 3.B live-API
smoke ✅ 2026-05-16 (slot 4); Phase 3.C EPL forward-poll ✅ 2026-05-19. Plan is 100% complete.

- `unified-trading-pm@2f710f9a` — docs(plans): api_football — flip Phase 5.A/5.B + plan closeout + DONE-2026-05-13

## DONE-2026-05-08 — Tab 5 cycle (Phases 1-3 + 5)

Tab 5 (api-football-flattening-tab) shipped Phases 1-3 + 5 of this plan in one cycle. Phase 4 (optional historical
reprocessor) intentionally skipped per plan body's default recommendation — forward-poll naturally fills new fixtures
with the new shape; historical thin parquets survive harmlessly until the next league cycle re-fetches.

Code commits:

- `unified-api-contracts@c76e6d0` — feat(api_football): flatten fixture_stats / events / lineups / injuries. Adds
  `_FIXTURE_STAT_TYPE_MAP` closed-set + `_safe_pct` / `_safe_float` helpers; rewrites the 4 pass-through normalizers to
  per-row flat dicts; extends 4 SchemaContracts with full per-column ColumnSpec lists; rewrites the
  `_sports_match_contracts.py` module docstring; ships 13 new unit tests under
  `tests/unit/test_normalize_api_football.py`.
- `instruments-service@539130f` — feat(api_football): wire flattened normalizers via chain.from_iterable. Updates the 4
  fixture-handlers to compose chain.from_iterable across the per-row normalizer outputs; tightens return-type
  annotations from `list[CanonicalX]` to `list[dict[str, object]]` (matches base-class signature + actual runtime
  shape); drops the now-unused Canonical\* imports.
- `unified-trading-pm@36c40a10` — plan(api_football_minimal_flattening): flip Phase 1+2+3+5 + ship codex
  regression-guard. Adds "Expected column counts per API-Football data_type" sub-section under §2.1 of
  `/codex/02-data/sports-data-source-coverage-matrix.md` (5-row table + footnote + 2026-05-08 changelog entry); flips
  shipped checkboxes in this plan body with commit-sha + brief evidence; marks the 2 Phase 3 smoke-test items as
  `**DEFERRED**` with a hand-back note for operator-driven live-API + EPL forward-poll verification.

~~Open items (executable — credentials available via act-secrets):~~ **[RESOLVED 2026-05-20 slot-8]** — all items now
done:

- ~~Phase 3.B + 3.C~~ ✅ DONE: Phase 3.B live-API smoke shipped 2026-05-16 (slot 4); Phase 3.C EPL forward-poll verified
  end-to-end 2026-05-19. Plan body checkboxes updated.
- ~~Phase 4~~ ✅ CANCELLED: optional skip confirmed per plan recommendation. Checkbox flipped.
- ~~Phase 5.B~~ ✅ DONE: plan close flipped PM@2f710f9a (2026-05-13). Plan 100% complete.
