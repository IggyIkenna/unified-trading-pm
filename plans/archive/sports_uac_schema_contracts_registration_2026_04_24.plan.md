---
doc_type: plan
title: SPORTS UAC SchemaContract registration — close the SSOT gap for all 19 sports data_types
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    deployment-api,
    deployment-ui,
    instruments-service,
    strategy-service,
    unified-api-contracts,
    unified-trading-system-ui,
  ]
scope: [engineer, admin]
tags: []
related: []
created: 2026-04-24
overview:
  Declare UAC SchemaContracts for every SPORTS data_type currently written to GCS without a contract (19 of 20 live
  types). Today only `(sports, odds, trades)` is registered; FIXTURES, INJURIES, XG, WEATHER, etc. all fall back to raw
  parquet projection in the drilldown schema modal, and downstream consumers (FSS, strategy-service, deployment-api)
  have no SSOT to validate against. Also drop the SFI_STANDINGS phantom (schema bug — endpoint doesn't exist).
priority: P2
owner: agent
completed: 2026-04-25
type: code
epic: none
completion_gates: { code: C5, deployment: none, business: none }
repo_gates:
  - { repo: unified-api-contracts, code: C5, deployment: none, business: none }
  - { repo: deployment-api, code: C5, deployment: none, business: none }
  - { repo: instruments-service, code: na, deployment: none, business: none }
  - { repo: features-sports-service, code: na, deployment: none, business: none }
  - { repo: deployment-ui, code: na, deployment: none, business: none }
  - { repo: unified-trading-pm, code: C5, deployment: none, business: none }
depends_on: []
isProject: false
reconciliation_status: shipped_substantive
reconciliation_date: 2026-04-25
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

> **Reconciliation note (2026-04-25):** Substantively shipped — recommended for archive. 20/20 checkboxes done;
> frontmatter has `completed: 2026-04-25`. UAC 4810ced, cbd8047, a7eb167, cf79d54. Ready for archive. See
> `_reconciliation_evidence_map_2026_04_25.md` for evidence anchors.

## Context

While auditing the deployment-ui (localhost:5183) sports manifest on 2026-04-24, the user clicked "View schema" on
FIXTURES and received:

> **Schema: / FIXTURES · Source: none · No contract registered — the UI will project raw parquet columns.**

Investigation traced this to the UAC contract registry:

```python
# unified-api-contracts/.../internal/schemas/_sports_prediction_contracts.py:190
CONTRACT_REGISTRY[("sports", "odds", "trades")] = SPORTS_ODDS_TRADES
```

**Exactly one SPORTS SchemaContract is registered across the entire UAC registry.** Every other sports data_type (19 of
20 live) writes parquet to GCS every day with no column-level SSOT in UAC. The pipeline has been running this way since
sports went live (~18 months). The manifest-v5 honest-coverage `ManifestWriter` work tracks shard coverage, not column
schemas — it is orthogonal to this gap.

Secondary bug found during the same session (in scope because it's a sports schema lie): **SFI_STANDINGS** is declared
in `deployment-api/deployment_api/services/data_status_service.py` SPORTS_DATA_TYPE_META but the orchestrator at
`instruments-service/.../engine/orchestrator.py:4965` hard-codes `_want_sfi_standings = False` because the SFI API has
no standings endpoint. It will never populate. The manifest row is a zero-forever lie. Remove from metadata so the UI
stops showing an aspirational `0/8195` that has no recoverable state.

### Why this matters (beyond the "View schema" modal)

1. **Drilldown UI falls back to raw parquet projection** — confusing column names (`af_fixture_id`, `status_short`,
   `periods_first`) leak to end-users who should see human descriptions.
2. **Downstream consumers have no validation surface** — FSS reads these parquets (FIXTURE_FEATURES derivation, WEATHER
   join), strategy-service reads MATCHES/ODDS, but nothing in the chain validates that upstream columns didn't silently
   rename or change type. The drill-down `fixture_id → af_fixture_id` rename that broke the FIXTURES breakdown endpoint
   on 2026-04-24 would have been caught at contract-declaration time.
3. **CSV downloads (`buildFixturesCsvDownloadUrl`) have no canonical column ordering or naming** — they dump raw
   parquet. Professional clients receiving these will see internal-provider names.
4. **QG enforcement of "schema provenance"** (CLAUDE.md Service Infrastructure Requirements STEP 5.x) requires every
   domain type to come from UAC. Sports is the last major category-family still self-declaring.

---

## Pre-Audit Manifest

### Scope: 19 new contracts + 1 phantom removal

| #   | data_type                 | Source provider                       | GCS path (example day=YYYY-MM-DD)                | Row cardinality (per day)        | Contract-key tuple                                 |
| --- | ------------------------- | ------------------------------------- | ------------------------------------------------ | -------------------------------- | -------------------------------------------------- |
| 1   | **FIXTURES**              | API-Football                          | `entity=fixtures/fixtures.parquet`               | per-league per-fixture           | `("sports", "match", "fixtures")`                  |
| 2   | **FIXTURE_EVENTS**        | API-Football                          | `entity=fixture_events/fixture_events.parquet`   | per-fixture-event                | `("sports", "match", "fixture_events")`            |
| 3   | **FIXTURE_STATS**         | API-Football                          | `entity=fixture_stats/fixture_stats.parquet`     | per-fixture team-stat            | `("sports", "match", "fixture_stats")`             |
| 4   | **FIXTURE_LINEUPS**       | API-Football                          | `entity=fixture_lineups/fixture_lineups.parquet` | per-fixture player-lineup        | `("sports", "match", "fixture_lineups")`           |
| 5   | **PLAYER_STATS**          | API-Football                          | `entity=player_stats/player_stats.parquet`       | per-fixture per-player           | `("sports", "match", "player_stats")`              |
| 6   | **INJURIES**              | API-Football                          | `entity=injuries/injuries.parquet`               | per-player daily                 | `("sports", "match", "injuries")`                  |
| 7   | **XG**                    | Understat                             | `entity=understat_xg/understat_xg.parquet`       | per-fixture xG snapshot          | `("sports", "match", "xg")`                        |
| 8   | **WEATHER**               | OpenMeteo                             | `entity=weather/weather.parquet`                 | per-fixture / per-venue          | `("sports", "match", "weather")`                   |
| 9   | **FIXTURE_FEATURES**      | features-sports-service (derived)     | `fixture_features/*.parquet`                     | per-fixture feature row          | `("sports", "feature", "fixture_features")`        |
| 10  | **MATCHES**               | FootyStats                            | `footystats_matches/*.parquet`                   | per-league per-match             | `("sports", "match", "matches")`                   |
| 11  | **PREDICTIONS**           | FootyStats                            | `footystats_predictions/*.parquet`               | per-league per-fixture           | `("sports", "match", "predictions")`               |
| 12  | **STANDINGS**             | API-Football                          | `standings/*.parquet`                            | per-league per-team per-snapshot | `("sports", "league", "standings")`                |
| 13  | **LEAGUES**               | API-Football                          | `leagues/*.parquet`                              | per-league daily snapshot        | `("sports", "reference", "leagues")`               |
| 14  | **TEAMS**                 | API-Football                          | `teams/*.parquet`                                | per-team daily snapshot          | `("sports", "reference", "teams")`                 |
| 15  | **VENUES**                | API-Football                          | `venues/*.parquet`                               | per-venue static                 | `("sports", "reference", "venues")`                |
| 16  | **PLAYER_VALUES**         | Transfermarkt                         | `player_values/*.parquet`                        | per-player weekly                | `("sports", "player", "values")`                   |
| 17  | **TRANSFERMARKT_LEAGUES** | Transfermarkt                         | `transfermarkt_leagues/*.parquet`                | per-league reference             | `("sports", "reference", "transfermarkt_leagues")` |
| 18  | **SFI_LEAGUES**           | SFI                                   | `sfi_leagues/*.parquet`                          | per-league reference             | `("sports", "reference", "sfi_leagues")`           |
| 19  | **SFI_PROGRESSIVE_STATS** | SFI                                   | `sfi_progressive_stats/*.parquet`                | per-fixture per-team progressive | `("sports", "match", "sfi_progressive_stats")`     |
| —   | **SFI_STANDINGS**         | _(DELETE from SPORTS_DATA_TYPE_META)_ | n/a — endpoint does not exist                    | n/a                              | n/a                                                |
| —   | **ODDS**                  | _(already registered — skip)_         | —                                                | —                                | `("sports", "odds", "trades")` ✅                  |

Total: 19 new `SchemaContract` declarations + 1 metadata row deletion.

### Column-list discovery strategy

We do NOT hardcode column lists in the plan — they are the deliverable, not the input. A discovery script reads the
most-recently-written parquet for each data_type from GCS and emits a draft `ColumnSpec` list per contract. Human review
then adds:

- `description=` per column (domain meaning, not just the type)
- `nullable=` (inferred from `.isna().any()` over a sample window, reviewer confirms)
- `symbol_column=` (the canonical row identifier — e.g. `af_fixture_id` for FIXTURES, `af_player_id` for PLAYER_STATS,
  `af_league_id` for LEAGUES)
- `required_row_count_min=` (conservative floor; e.g. `1` for reference types, `0` for derivative types that can be
  legitimately empty)

### Known column renames / drift to capture in descriptions

From live errors + orchestrator comments (single pass, already learned this session):

- `fixture_id` → `af_fixture_id` (API-Football per-fixture + master FIXTURES). Orchestrator
  [orchestrator.py:3220-3221](instruments-service/instruments_service/engine/orchestrator.py#L3220-L3221) comments the
  prefer-af pattern; drilldown was blind to it (fixed 2026-04-24 in deployment-api; memory
  `project_ui_manifest_v5_plus_fixture_breakdown_fix_2026_04_24.md`).
- Status is split three ways on FIXTURES: `status_long` (human), `status_short` (code), `status_elapsed_time` (minute).
- Scores are per-phase: `home_score`, `home_score_halftime`, `home_score_fulltime`, `home_score_extratime`,
  `home_score_penalty` (and mirror `away_score_*`). Symmetric for away.
- Home/away team names use the `af_` prefix: `af_home_name`, `af_away_name`, `af_home_id`, `af_away_id`, `af_winner_id`.

### Downstream consumers affected (contract-only registration; no renames)

Phase 1-3 register contracts; consumers do NOT change. Validation is passive (FSS, strategy-service, drilldown can
opt-in to `validate_against_contract()` in a follow-up plan).

| Consumer                              | File(s)                                                | Touch needed in THIS plan?                                                                                 |
| ------------------------------------- | ------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------- |
| deployment-api drilldown schema modal | `deployment_api/services/data_status_drilldown.py`     | ❌ No — it already calls `lookup_contract()` and will light up automatically once registered.              |
| deployment-ui `SchemaModal`           | `deployment-ui/src/components/DataStatusDrilldown.tsx` | ❌ No — renders whatever contract returns. Will switch from "no contract registered" to full column table. |
| FSS reader                            | `features-sports-service/.../data/gcs_reader.py`       | ❌ No — reads columns imperatively today. Follow-up plan can add contract-validation.                      |
| instruments-service writers           | `orchestrator.py`                                      | ❌ No — writers already emit these columns; UAC is declaring reality, not changing it.                     |
| strategy-service sports signals       | `strategy-service/.../sports/*`                        | ❌ No — reads FIXTURES / ODDS / MATCHES today by column name. Follow-up plan.                              |

---

## Phased Execution DAG

```
Phase 0: Discovery (SEQUENTIAL)
    [SCRIPT] Extract real parquet schema for each of the 19 data_types from GCS.
    Output: JSON draft per data_type, checked into UAC under
            `unified-api-contracts/.claude/sports-contracts-draft-2026-04-24.json`
            (gitignored working file; converted to ColumnSpec in Phase 1).

    ┌──────────────────────────────────────────────┐
    ▼
Phase 1: Register contracts (PARALLEL × 5 provider families)
    Family A — API-Football reference   : LEAGUES, TEAMS, VENUES  [3 contracts]
    Family B — API-Football fact        : FIXTURES, FIXTURE_EVENTS, FIXTURE_STATS,
                                          FIXTURE_LINEUPS, PLAYER_STATS, INJURIES,
                                          STANDINGS  [7 contracts]
    Family C — Transfermarkt            : PLAYER_VALUES, TRANSFERMARKT_LEAGUES  [2 contracts]
    Family D — SFI                      : SFI_LEAGUES, SFI_PROGRESSIVE_STATS  [2 contracts]
    Family E — FootyStats + Understat   : MATCHES, PREDICTIONS, XG, WEATHER (OpenMeteo),
                                          FIXTURE_FEATURES (FSS derivative)  [5 contracts]
    Total: 19 new contracts, one new UAC file per family (or consolidated).

    All 5 families can land in parallel as separate sub-agent PRs since the
    contract keys are disjoint tuples.

    ▼
Phase 2: Registry wiring + tests (SEQUENTIAL, after all of Phase 1)
    Hook each new `SportsContract` into `CONTRACT_REGISTRY` in UAC.
    Add `tests/test_sports_contracts.py` that asserts every contract is
    round-trippable: `lookup_contract(*key)` returns the declared contract,
    `ColumnSpec` validators pass, `symbol_column` appears in `columns`.

    ▼
Phase 3: Phantom cleanup (SEQUENTIAL, independent but small)
    Delete SFI_STANDINGS row from deployment-api SPORTS_DATA_TYPE_META.
    Verify deployment-ui manifest no longer renders the 0/8195 forever-zero row.

    ▼
Phase 4: QG gate across all affected repos
    `quality-gates.sh` Pass 1 on UAC + deployment-api.
    Downstream repos unchanged — no need to re-gate.

    ▼
Phase 5: Verification (visual, in deployment-ui)
    Click "View schema" on every SPORTS row in the manifest. Confirm the modal
    renders populated column tables for all 19 data_types (plus existing ODDS).
    Confirm SFI_STANDINGS row is gone.
```

Phase 1 families A-E are **PARALLEL**. Phase 2 is **sequential** (one UAC PR that wires all 19 registrations) to avoid
registry-init race in tests. Phase 3 is **independent** of Phases 0-2 — can be done in any order.

---

## Todos

### Phase 0 — Discovery

- [x] [SCRIPT] P0. Write a throwaway discovery script `unified-api-contracts/scripts/extract-sports-parquet-schemas.py`
      that reads the most recently-written parquet for each of the 19 data_types from GCS (use the paths from the
      pre-audit manifest; default `day=` = yesterday, fall back to most recent `<= 30 days ago`). For each file emit a
      JSON record `{data_type, columns: [{name, pyarrow_type, nullable_sample}]}`. Write to
      `.claude/sports-contracts-draft-2026-04-24.json` (gitignored). Script is disposable — deleted at the end of
      Phase 1.
- [x] [AGENT] P0. Review the JSON draft. For every column add a 1-line `description` explaining the domain meaning (not
      the type — the type is already known). Mark the canonical row identifier per data_type (the `symbol_column`). This
      is the domain-knowledge delta that cannot be auto-generated.

### Phase 1 — Contract declarations (PARALLEL × 5 families)

- [x] [AGENT] P0. Family A (API-Football reference). Create
      `unified-api-contracts/unified_api_contracts/internal/schemas/_sports_reference_contracts.py` with
      `SPORTS_LEAGUES`, `SPORTS_TEAMS`, `SPORTS_VENUES`. Each is a full `SchemaContract` with ColumnSpecs +
      symbol_column + `required_row_count_min`. Register in `CONTRACT_REGISTRY` under keys from the manifest above.
      Expose via `__all__` and module re-export in `internal/schemas/__init__.py`.
- [x] [AGENT] P0. Family B (API-Football fact). Create
      `unified-api-contracts/unified_api_contracts/internal/schemas/_sports_match_contracts.py` with `SPORTS_FIXTURES`,
      `SPORTS_FIXTURE_EVENTS`, `SPORTS_FIXTURE_STATS`, `SPORTS_FIXTURE_LINEUPS`, `SPORTS_PLAYER_STATS`,
      `SPORTS_INJURIES`, `SPORTS_STANDINGS`. Register all 7 under match/reference keys. Include prominent description
      notes for the `af_` prefix convention and the three `status_*` columns.
- [x] [AGENT] P0. Family C (Transfermarkt). Add `SPORTS_PLAYER_VALUES`, `SPORTS_TRANSFERMARKT_LEAGUES` to
      `_sports_reference_contracts.py` (or a dedicated `_sports_transfermarkt_contracts.py` if Family A file exceeds
      ~300 lines). `symbol_column="tm_player_id"` for PLAYER_VALUES (canonical identifier Transfermarkt exposes).
- [x] [AGENT] P0. Family D (SFI). Add `SPORTS_SFI_LEAGUES`, `SPORTS_SFI_PROGRESSIVE_STATS` to
      `_sports_reference_contracts.py` (or a dedicated `_sports_sfi_contracts.py`). Make sure to NOT declare
      `SPORTS_SFI_STANDINGS` — see Phase 3.
- [x] [AGENT] P0. Family E (FootyStats + Understat + OpenMeteo + FSS derivative). Create `_sports_derived_contracts.py`
      with `SPORTS_MATCHES` (FootyStats), `SPORTS_PREDICTIONS` (FootyStats), `SPORTS_XG` (Understat), `SPORTS_WEATHER`
      (OpenMeteo). Create `_sports_features_contracts.py` with `SPORTS_FIXTURE_FEATURES` (the FSS derivative output;
      contract keyed at `("sports", "feature", "fixture_features")`). Register all 5.

### Phase 2 — Registry wiring + tests

- [x] [AGENT] P0. Extend `unified_api_contracts/internal/schemas/__init__.py` to import the new modules so
      `CONTRACT_REGISTRY` side-effects run on `import unified_api_contracts`. Verify all 19 new keys are present via
      `python -c "from unified_api_contracts.internal.schemas.contracts import CONTRACT_REGISTRY; print(len(CONTRACT_REGISTRY))"`
      before vs after (expect +19).
- [x] [AGENT] P0. Add `unified-api-contracts/tests/test_sports_contracts.py` with: (a) every new contract round-trips
      via `lookup_contract(*key)`, (b) `symbol_column` appears in `columns`, (c) `required_row_count_min` is set, (d)
      `ColumnSpec` validators pass for each `SchemaContract.columns[i]`. Minimum 19 parametrised test cases.
- [x] [AGENT] P0. Run `cd unified-api-contracts && bash scripts/quality-gates.sh` — must pass fully (no reduced
      coverage, no new basedpyright errors, cassette-parity test still green).

### Phase 3 — SFI_STANDINGS phantom removal

- [x] [AGENT] P1. Open `deployment-api/deployment_api/services/data_status_service.py`. Locate `SPORTS_DATA_TYPE_META`
      entry for `SFI_STANDINGS` (around lines 226-231 — confirm by grep). Delete the entry. Delete any related rows in
      `_sports_expected_dates_for_league` and the unit-meta constants if specific to SFI_STANDINGS. Do NOT delete
      `_want_sfi_standings = False` in the orchestrator — that is the correct defensive check; leaving it makes the
      absence intentional.
- [x] [AGENT] P1. Add a short comment at the orchestrator site noting why SFI_STANDINGS is intentionally absent from the
      manifest: "SFI has no standings endpoint (provider gap); removed from metadata 2026-04-24 after confirming with
      upstream docs."
- [x] [AGENT] P1. Grep for any `SFI_STANDINGS` string literals across the workspace. Expected to find zero after
      cleanup; any remaining hit is a stale reference that must be fixed or documented.

### Phase 4 — QG gate

- [x] [AGENT] P0. Run `cd unified-api-contracts && bash scripts/quality-gates.sh` (full Pass 1, all tests).
- [x] [AGENT] P0. Run `cd deployment-api && bash scripts/quality-gates.sh` (full Pass 1, all tests). Expected: same or
      slightly lower test count (Phase 3 removes SFI_STANDINGS rows from any existing tests that asserted on it).

### Phase 5 — Verification (visual)

- [x] [AGENT] P1. Start deployment-ui tier 1 (`bash unified-trading-system-ui/scripts/dev-tiers.sh --tier 1`). Navigate
      to data-status tab. Click "View schema" on each of the 19 SPORTS data_type rows in the manifest. For each, confirm
      the modal renders: `Source: CONTRACT_REGISTRY`, a non-empty columns table, and `required_row_count_min` in the
      header. Screenshot each result as evidence in the completion commit message.
- [x] [AGENT] P1. Confirm SFI_STANDINGS row is no longer present in the SPORTS manifest panel.

### Phase 6 — Quickmerge

- [x] [AGENT] P0.
      `cd unified-api-contracts && bash scripts/quickmerge.sh "feat: register 19 SPORTS SchemaContracts (close UAC SSOT gap; drop SFI_STANDINGS phantom)" --agent`.
- [x] [AGENT] P0.
      `cd deployment-api && bash scripts/quickmerge.sh "fix(sports): remove SFI_STANDINGS phantom from SPORTS_DATA_TYPE_META (endpoint does not exist)" --agent`.

### Phase 7 — Plan completion

- [x] [AGENT] P0. Ask user to unlock this plan (remove `locked_by` from frontmatter + commit with `[unlock-plan]` tag).
      Agents MUST NOT unlock autonomously per CLAUDE.md plan-locking protocol.

---

## Success Criteria

### Code gates (all repos in `repo_gates`)

- **C1**: All 19 `SchemaContract` declarations compile and instantiate without error.
- **C2**: `unified-api-contracts/tests/test_sports_contracts.py` passes with 19+ parametrised cases. Existing UAC tests
  continue to pass (cassette-parity, contract-registry integrity). deployment-api tests unchanged except for
  SFI_STANDINGS references removed.
- **C3**: `ruff`, `basedpyright`, and Codex gates clean on modified files in both UAC and deployment-api.
- **C4**: `quality-gates.sh` Pass 1 clean on UAC and deployment-api.
- **C5**: Quickmerge PRs merged to `live-defi-rollout` (both repos).

### Visual acceptance (Phase 5)

- "View schema" on any of the 19 SPORTS data_type rows in deployment-ui returns a populated column table with
  `Source: CONTRACT_REGISTRY` (not `none`).
- SFI_STANDINGS row is gone from the SPORTS manifest panel.

### Deployment / Business

- `deployment: none` — contracts are type-declarations, no infra impact.
- `business: none` — internal SSOT housekeeping, no KPI.

---

## Out of Scope

- **Contract-validation wiring on downstream consumers** (FSS, strategy-service, drilldown).
  `validate_against_contract()` call sites are a follow-up plan. This plan only declares. Validation is opt-in so the
  registration can land without cascading failures on legitimate column drift that post-dates the snapshot.
- **Renaming any parquet columns.** Contracts declare reality (including `af_` prefixes and split `status_*` columns).
  Cleaning up API-Football internal prefixes is a separate normalisation plan.
- **Cross-category contracts** (PREDICTION, CEFI, TRADFI, DEFI). Those registries have their own gaps (or completeness)
  tracked elsewhere.
- **Schema evolution migration.** When a provider adds a column (API-Football adds a new stat), this plan does not
  specify the update cadence. Follow-up plan should declare a cassette-schema-parity drift test for sports.

---

## Related Sessions / Prior Work

- 2026-04-24 session: UI manifest-v5 migration + fixture breakdown `af_fixture_id` fix in deployment-api (memory
  `project_ui_manifest_v5_plus_fixture_breakdown_fix_2026_04_24.md`). The drilldown fix unblocks the FIXTURES
  per-fixture breakdown click; this plan closes the upstream SSOT gap that surfaced during the same session when the
  user clicked "View schema".
- Availability-manifest v5 honest-coverage plan: `/codex/02-data/availability-manifest-and-data-status.md`. That work is
  about **shard coverage** (did we capture?). This plan is about **column schemas** (what did we capture?). The two are
  orthogonal.
- Sports roadmap master execution: `plans/active/sports_roadmap_master_execution_2026_04_21.md` — this plan is a
  follow-up to the visibility/data-status strand of that roadmap.
