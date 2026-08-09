---
doc_type: plan
title: Canonicalize sports odds-feature naming on UAC's SportsFeatureVector
summary: >-
  Operator-ruled 2026-07-21 (BLK-a1ce4719) resolution of sports_odds_feature_naming_four_way_mismatch_2026_07_21.md —
  direction is UAC-as-SSOT (Option A), executed as a scoped migration, not a blind rename. Picks deliberate field names
  for UAC's SportsFeatureVector/OddsFeaturesMixin, migrates the three real consumers (features-service producer,
  ml-service loader, strategy-service v2 + legacy subscriber), and closes the ml-service loader's silent-agnostic gap
  with loud schema validation.
status: active
nature: design
asset_group: [sports, prediction]
stage: [data, strategy]
repos: [unified-api-contracts, features-service, ml-service, strategy-service]
scope: [engineer, admin]
tags: [sports, odds-features, schema-parity, naming-migration, uac-ssot]
related:
  [
    plans/active/issues/sports_odds_feature_naming_four_way_mismatch_2026_07_21.md,
    plans/active/issues/sports_predictions_live_mode_and_backtest_execution_orphaned_2026_07_21.md,
    plans/active/sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md,
    plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
created: "2026-07-21"
last_updated: "2026-07-21"
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: design
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.8
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
source: [sports_odds_feature_naming_four_way_mismatch-001]
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/issues/sports_odds_feature_naming_four_way_mismatch_2026_07_21.md,
    unified-api-contracts/unified_api_contracts/internal/domain/features_sports/_features_venue_referee_player_odds.py,
    features-service/features_service/sports/exporters/odds_features_exporter.py,
    ml-service/ml_service/training/app/core/sports_feature_loader.py,
    strategy-service/strategy_service/adapters/sports_feature_subscriber.py,
  ]
---

> **🟡 Scope overlap with `sports_consolidated_closeout_2026_07_19.md` (flagged 2026-07-23, orphan-plan reconciliation
> audit).** That closeout's own sports issue-doc index still lists
> `plans/active/issues/sports_odds_feature_naming_four_way_mismatch_2026_07_21.md` as merely open/P2 and does not yet
> reflect that THIS plan already has a DECIDED naming scheme (see this plan's 2026-07-23 Progress Log entry below) plus
> a scoped, tracked 3-repo migration underway to execute it. Do not resolve this staleness gap unilaterally from either
> doc — check the closeout's current Track C/H sections (and its own Progress Log) for the latest state before acting on
> either doc; the closeout is getting its own reconciliation todo about this specific conflict as a separate step.
>
> **Dispatch model formalized, 2026-07-29 (operator ruling)**: `assigned_vm: NA` stays as declared, but remaining
> bounded todos on this plan are sanctioned to land via the satellite AO-dispatch-batch pattern already in practice
> (e.g. `sports_satellite_ao_dispatch_batch5_2026_07_26.md` / its `_finalize` sibling), rather than requiring a fresh
> personal review before every landing — this codifies what was already happening piecemeal, per
> `sports_odds_naming_migration_uncommitted_wip_and_checkbox_drift_2026_07_25.md`'s reconciliation todo.

# Canonicalize sports odds-feature naming on UAC's SportsFeatureVector

## Operator ruling (BLK-a1ce4719, 2026-07-21)

> A — canonicalize on UAC (SportsFeatureVector/OddsFeaturesMixin) as the SSOT — but execute it as a scoped migration
> plan, not a blind rename now.
>
> DIRECTION is doc-settled, not a unilateral architecture pick: the workspace UAC-SSOT-types HARD RULE makes Option B
> structurally non-compliant by its own description (it leaves UAC orphaned/non-compliant). Pure-C (indefinite defer) is
> also wrong: ml-service's schema-agnostic loader silently yielding `None`/`KeyError` on a naming mismatch is exactly
> the latent data-correctness landmine the data-pipeline-correctness HARD RULE says not to leave sitting. So the
> canonical home MUST be UAC.
>
> BUT the issue author's caution (real 3-repo migration cost; UAC's own current field names may not be the right names
> either) is valid and is handled by HOW, not by picking B/C:
>
> 1. Do NOT hand-rename fields unilaterally in one session — author this scoped migration plan (LOCAL/human track) for
>    operator review before any 3-repo dispatch. Mirrors how BLK-b567ce7d was resolved.
> 2. The plan must: (a) choose the clearest field names deliberately and land them IN UAC's SportsFeatureVector/
>    OddsFeaturesMixin as SSOT (renaming UAC's own fields if the current ones are poor — being SSOT does not make UAC's
>    current names sacrosanct); (b) migrate the three consumers to match; (c) CRITICALLY, add loud schema validation at
>    the ml-service loader boundary so a future naming mismatch fails LOUD, not silently `None`/`KeyError` — the
>    silent-agnostic loader is itself the bug-enabler and must be closed as part of this.
> 3. Sequencing: since sports is backtest-only with no imminent live wiring, the migration can be scheduled alongside
>    the wire-sports-end-to-end work rather than as an emergency — but it must be a TRACKED plan now, not an indefinite
>    defer.

## Scope (the 4 conventions this plan reconciles)

Per `sports_odds_feature_naming_four_way_mismatch_2026_07_21.md`'s finding — read that doc first for the full grep
evidence. Summary of what each site currently uses:

1. **features-service OUTPUT** (`features_service/sports/exporters/odds_features_exporter.py` +
   `features_service/sports/calculators/odds_columns.py`'s `ODDS_COLUMNS`) — `home_implied_prob`, `draw_implied_prob`,
   `away_implied_prob`, `market_vig`, `vig_pct`, `sharp_soft_gap_home/draw/away`, `book_range_prob_home/draw/away`,
   `fair_prob_home/draw/away`, etc. Plain `pd.DataFrame`, no schema class.
2. **ml-service INPUT** (`ml_service/training/app/core/sports_feature_loader.py`'s `SportsFeatureLoaderMixin`) —
   schema-agnostic; validates only `fixture_id` + the `event_id`→`fixture_id` crosswalk. Zero field-name enforcement.
3. **strategy-service INPUT** — v2 archetype engines' `on_tick(..., features: dict[str, float], ...)`:
   `SportsValueBettingEngine` reads `decimal_odds_<outcome_id>`/`fair_prob_<outcome_id>`; `SportsArbDutchingEngine`
   reads `decimal_odds_<outcome_id>_<venue>`. A separate legacy consumer,
   `strategy_service/adapters/sports_feature_subscriber.py`, reads a THIRD convention:
   `ht_odds_home_implied`/`ht_odds_draw_implied`/`ht_odds_away_implied`.
4. **UAC's OWN schema** —
   `unified_api_contracts/internal/domain/features_sports/_features_venue_referee_player_odds.py`'s `OddsFeaturesMixin`
   (part of `SportsFeatureVector`) — `market_home_implied_prob`, `market_vig_pct`, `market_overround`. Currently
   imported by NONE of the three real consumers.

## Todos

- [x] [DATA] P1. ✅ **RETAGGED 2026-07-28 (stale-tag audit — already decided, `[OPERATOR]` never removed). DECIDED
      2026-07-23 — new deliberate naming, not adopted from any single existing convention.** Operator ruling
      (BLK-a1ce4719, see this doc's own "## Operator ruling" section above and
      `/plans/active/issues/sports_odds_feature_naming_four_way_mismatch_2026_07_21.md`): design fresh, and migrate the
      underlying data + manifest (not just rename call sites) so every one of the 3 real consumers' actual needs is
      satisfied, including the per-venue decimal-odds shape `SportsArbDutchingEngine` needs that **features-service does
      not currently compute at all** (FSS's `ODDS_COLUMNS` — read in full, 180 fields,
      `features_service/sports/calculators/odds_columns.py:11-190` — has only cross-book aggregates like
      `best_odds_home/draw/away`, never a per-bookmaker raw decimal-odds column; this is NEW feature-engineering work,
      not a rename). Full scheme + representative before/after mapping + the new- computation gap are recorded in the
      Progress Log below. The exhaustive field-by-field mapping for all 180 existing FSS columns is generated by
      applying the scheme below — that mechanical pass is todo 2's job, not re-litigated here.
- [x] ✅ [DATA] P1. **SHIPPED — `features-service@b03a6de4`** (checkbox-drift fix, 2026-07-26 slot 6; work landed
      2026-07-25 but this plan's own checkbox was never flipped). Added per-bookmaker raw decimal-odds retention:
      `_pivot_bucketed_to_fixture()` in `features_service/sports/exporters/odds_features_exporter.py` now computes a
      dynamic-width `odds_decimal_<outcome>_<venue>` column per bookmaker actually quoting the fixture at that horizon
      (line ~574), and `export_odds_features()`'s merge-back carries these new columns through since they aren't in the
      fixed `ODDS_COLUMNS` list (comment at line ~395). **Re-verified live repo state before flipping** (no further
      drift since the 2026-07-25T14:20Z checkpoint this todo's source doc flagged): `b03a6de4` confirmed an ancestor of
      current HEAD via `git merge-base --is-ancestor`, and the exact `odds_decimal_{outcome}_{venue}` f-string is
      present in the current file. (repo: features-service)
- [x] ✅ [DATA] P1. Update `unified_api_contracts`'s `OddsFeaturesMixin`/`SportsFeatureVector` fields to the names
      chosen in todo 1 (rename in place — UAC being SSOT doesn't make its current names sacrosanct). Add/update the UAC
      unit tests covering the schema's field set. (repo: unified-api-contracts) **DONE (na-eligibility-audit
      2026-08-03)** — `sports_satellite_ao_dispatch_batch2_2026_07_24.md:416`: `unified-api-contracts@689efa54` +
      `ml-service@91f031a`, all 49 fields renamed to the decided scheme, grounded in features-service's actual
      calculator output (not a blind find-replace — same-named-but-unrelated columns in other layers correctly left
      untouched). New UAC test file asserts the exact field set. Known transitional gap noted there: some FSS-side
      renames still pending (this doc's own todo above, already tracked, separately closed).
- [x] ✅ [DATA] P2. Migrate `features_service/sports/calculators/odds_columns.py`'s `ODDS_COLUMNS` + the odds-features
      exporter to emit the UAC-chosen field names instead of the current `home_implied_prob`-style convention; update
      the exporter's own tests + any downstream fixture files that assert the old column names. (repo: features-service)
      — **SHIPPED features-service@0ded2449 (slot 11, data_engineering, 2026-07-25T14:20Z)**: all 139 `ODDS_COLUMNS`
      entries + the exporter + PIT horizon-gating overrides + `feature_definitions.yaml` renamed per the decided scheme,
      matching UAC's already-renamed `OddsFeaturesMixin` exactly where they overlap and extending the scheme by symmetry
      for the BookmakerTier/probability-space fields UAC's shipped subset didn't cover. Also fixed an unrelated
      pre-existing path bug in `regenerate_feature_definitions.py`. `quality-gates.sh` full run (sentinel bypassed):
      17823 passed, 0 failed. **Concurrent-duplicate note (slot 4)**: slot 4 independently built the same 139-entry
      migration in parallel, unaware of slot 11's in-flight ship — caught the collision on push (branch drift showed
      slot 11's commit already on origin), verified it was complete and correct before discarding its own duplicate diff
      (never shipped). A repo-wide old-name grep against the newly-landed tree found 2 files slot 11's commit missed —
      `features_service/sports/engine/sports_validity_engine.py` (`bookmaker_count_total`) and
      `scripts/sports/seed_mock_data.py` (`market_vig`/`home_edge`/`odds_draw`) — fixed to the same scheme by slot 4,
      quality-gates.sh fresh full run green (17823 passed, sentinel forced not cached): features-service@e240eca2. Full
      `tests/sports/` suite (incl. integration, which the standard `RUN_INTEGRATION=false` gate skips) also verified
      green except one confirmed byte-identical PRE-EXISTING failure (`test_table_schemas_dict_has_all_sport_tables`,
      unrelated "players" table gap — verified on a clean tree, filed separately:
      `issues/sports_table_schemas_missing_players_table_2026_07_25.md`). **Follow-up finding (P2, filed as a new todo
      below, NOT fixed here — different repo, out of scope for this `(repo: features-service)`-scoped todo)**: a
      repo-wide grep of ml-service turned up FOUR more files still using the pre-migration names —
      `ml_service/training/engine/mock_data_provider.py`, `ml_service/training/app/core/sports_target_generator.py`,
      `tests/training/unit/test_sports_feature_loader.py`, `tests/training/unit/test_horizon_gate_shield.py` — none of
      these were touched by the earlier ml-service migration commits
      (`unified-api-contracts@689efa54`/`ml-service@91f031a` covered the schema/loader only, not mock-data generation or
      target generation).
- [x] [BACKEND] P2. Close the silent-agnostic gap in `SportsFeatureLoaderMixin`
      (`ml_service/training/app/core/sports_feature_loader.py`): add real schema validation against
      `OddsFeaturesMixin`'s field set at the point the odds `feature_group` parquet is read, so a producer/consumer
      naming mismatch fails LOUD (raises) instead of silently defaulting via `.get()` — this closes the honest-absence /
      no-silent-placeholders gap the parent issue identified as the actual bug-enabler, independent of which naming
      wins. (repo: ml-service) — CLOSED (na-eligibility-audit 2026-08-03): done via
      `sports_satellite_ao_dispatch_batch2_2026_07_24.md:448` (`ml-service@07976ae`, `_validate_odds_schema`).
- [x] [BACKEND] P2. Migrate `SportsValueBettingEngine` + `SportsArbDutchingEngine` (`on_tick`'s
      `features: dict[str, float]` reads) to the UAC-chosen field names — update the archetype engines' unit tests and
      any recorded fixture feature dicts. (repo: strategy-service) — CLOSED (na-eligibility-audit 2026-08-03): done via
      `sports_satellite_ao_dispatch_batch2_2026_07_24.md:454` (`strategy-service@4c55438c`).
- [x] [BACKEND] P2. Migrate the legacy `strategy_service/adapters/sports_feature_subscriber.py` (currently
      `ht_odds_home_implied` etc.) to the same UAC-chosen names — this is a third, separate convention from the v2
      engines and must not be left behind as a 5th orphaned dialect. (repo: strategy-service) — CLOSED
      (na-eligibility-audit 2026-08-03): done via `sports_satellite_ao_dispatch_batch2_2026_07_24.md:454` (same commit,
      combined).
- [x] ✅ [DATA] P2. **SHIPPED — `ml-service@10e219f`** (2026-07-26, slot-10, `data_engineering`, via
      `sports_satellite_ao_dispatch_batch5_2026_07_26.md`'s AO-dispatched copy of this todo; checkbox-drift fix
      2026-07-28). Migrated 4 ml-service files still using the pre-migration odds-feature names, missed by the earlier
      ml-service migration commits (`unified-api-contracts@689efa54`/`ml-service@91f031a` covered only the
      schema/loader, not these) — `ml_service/training/engine/mock_data_provider.py` (6 genuine hits, re-derived
      positionally from the shipped `features-service@0ded2449` migration diff), `test_horizon_gate_shield.py` (1
      genuine hit, 3 sites), `test_sports_feature_loader.py` (8 sites, `TestOddsJoinKeyCrosswalk` incidental
      join-key-crosswalk names). `ml_service/training/app/core/sports_target_generator.py` needed NO change — an earlier
      unrelated fix (`ml-service@a14985b`) had already replaced its bare CLV/velocity names. Deliberately left
      `test_naming_mismatch_raises_loudly`'s intentional old-name fixture unchanged (would defeat the test's own
      purpose). Post-fix repo-wide grep of all 125 old names across the 4 files: zero functional hits.
      `quality-gates.sh` full run green. Re-verified `10e219f` is a real, current commit in `ml-service` before this
      flip (`git show --no-patch` confirms).
- **[REVIEW] P3. Extracted to `/plans/active/sports_satellite_ao_dispatch_batch11_2026_08_09.md` todo 2 (2026-08-09,
  satellite-batch-extraction pass) — todos 1-6 above are all `[x]` shipped, so the FSS-output ↔ ml-service-input ↔
  strategy-service-input naming-parity test originally requested by
  `sports_predictions_live_mode_and_backtest_execution_orphaned_2026_07_21.md` is now unblocked. Tracked there
  (`assigned_vm: planning`), not duplicated here; that batch's finalize sibling reconciles this checkbox once it lands.
  `sports_satellite_ao_dispatch_batch10_2026_08_06.md`'s Conflict-gated section had held this exact item back citing
  "the still-unshipped migration" — that premise is now stale (see this doc's own 2026-08-08 Progress Log entry below,
  which independently flagged the same staleness).**
- [x] ✅ [REVIEW] P3. Cross-reference this migration against whichever plan ends up doing the "wire sports end-to-end"
      work (`sports_predictions_live_mode_and_backtest_execution_orphaned_2026_07_21.md`'s remaining todos) — per the
      operator's sequencing note, this migration should land BEFORE or ALONGSIDE that wiring, never after (a live
      pipeline hitting the old 4-way mismatch is the exact landmine this plan exists to defuse). — **RESOLVED BY
      CITATION (round-9 sweep, 2026-08-09)**:
      `sports_predictions_live_mode_and_backtest_execution_orphaned_2026_07_21.md` is `status: resolved`, archived
      2026-07-25 (`resolved_by: strategy-service@9a7de7f8,     unified-trading-system-ui@35137c88`) — there is no longer
      an active plan doing the "wire sports end-to-end" work to cross-reference against. The sequencing concern is
      satisfied in substance: this doc's own consumer-migration commits (ml-service/strategy-service via
      `sports_satellite_ao_dispatch_batch2_2026_07_24.md`, 2026-07-23..07-24) landed at or before the wiring doc's
      2026-07-25 resolution, and the final residual (`ml-service@10e219f`, 2026-07-26) closed a narrow 4-file gap the
      orphaned doc's own resolved commits never touched (mock-data/target-generator/test fixtures, not the live consumer
      path). No live pipeline is known to have hit the old 4-way mismatch. Nothing left to cross-reference.
- [ ] [REVIEW] P3. Archive this doc once `/plans/active/sports_satellite_ao_dispatch_batch11_2026_08_09.md` todo 2 (the
      extracted FSS↔ml-service↔strategy-service naming-parity test) lands — full 6-step archival ritual (status flip,
      banner, `git mv`, referrer sweep), not before (per the 2026-08-09 round-9 sweep's own note: the extraction is
      still in flight, archiving now would be premature).

## Codex SSOTs

No existing codex SSOT names sports odds-feature naming; once todo 1's decision lands, add a short SSOT note under
`codex/09-strategy/architecture-v2/archetypes/` naming the canonical `OddsFeaturesMixin` field set so future archetype
work doesn't reintroduce a 5th convention.

## Progress Log

- 2026-07-21 (slot 7): Plan authored per operator ruling BLK-a1ce4719 on
  `sports_odds_feature_naming_four_way_mismatch_2026_07_21.md`. LOCAL/human track (`assigned_vm: NA`) — the operator
  explicitly asked for a scoped plan for review before any 3-repo dispatch, not immediate AO execution.
- 2026-07-23: **Naming scheme DECIDED (todo 1).** Operator chose new deliberate naming over adopting any single existing
  convention, with full data+manifest migration so all 3 consumers' actual needs are met — read
  `features_service/sports/calculators/odds_columns.py` in full (180 existing fields) to ground the scheme in what FSS
  actually computes today, not just the four-way-mismatch doc's illustrative excerpt.

  **Scheme — `<category>_<metric>[_<outcome>][_<venue>]`, outcome ∈ {home, draw, away} lowercase (matches the
  per-outcome dict-key shape every consumer already expects), venue only present for per-venue fields:**

  | Category prefix                                                 | Meaning                                                                                                                                                                                                                                                                                                | Example old (FSS) → new                                                                                                                                                                                                                                                        |
  | --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
  | `prob_implied_`                                                 | raw implied probability from vig-laden odds                                                                                                                                                                                                                                                            | `home_implied_prob` → `prob_implied_home`                                                                                                                                                                                                                                      |
  | `prob_fair_`                                                    | vig-removed fair probability                                                                                                                                                                                                                                                                           | `fair_prob_home` → `prob_fair_home`                                                                                                                                                                                                                                            |
  | `prob_sharp_` / `prob_soft_`                                    | tier-consensus probability                                                                                                                                                                                                                                                                             | `sharp_prob_mean_home` → `prob_sharp_mean_home`; `soft_consensus_home` → `prob_soft_consensus_home`                                                                                                                                                                            |
  | `odds_market_`                                                  | market-structure scalars (not outcome-indexed)                                                                                                                                                                                                                                                         | `market_vig` → `odds_market_vig`; `overround` → `odds_market_overround`; `vig_pct` → `odds_market_vig_pct`; `market_efficiency_score` → `odds_market_efficiency`; `market_complexity_score` → `odds_market_complexity`; `market_spread_current` → `odds_market_spread_current` |
  | `odds_decimal_`                                                 | consensus/best decimal odds per outcome (satisfies `SportsValueBettingEngine`'s `decimal_odds_<outcome_id>`)                                                                                                                                                                                           | `best_odds_home` → `odds_decimal_home`                                                                                                                                                                                                                                         |
  | `odds_decimal_<outcome>_<venue>`                                | **NEW** per-bookmaker raw decimal odds (satisfies `SportsArbDutchingEngine`'s `<outcome_id>_<venue>` need) — venue is the UAC-canonical venue token, e.g. `odds_decimal_home_pinnacle`. Does not exist in FSS today; see the new-compute todo above.                                                   |
  | `odds_disagreement_` / `odds_variance_` / `odds_fragmentation_` | cross-bookmaker dispersion                                                                                                                                                                                                                                                                             | `bookmaker_disagreement_home` → `odds_disagreement_home`; `book_fragmentation_home` → `odds_fragmentation_home`; `book_std_prob_home` → `prob_disagreement_std_home`                                                                                                           |
  | `odds_movement_`                                                | closing-minus-opening / directional                                                                                                                                                                                                                                                                    | `odds_movement_home` → kept as-is (already scheme-compliant); `pinnacle_vs_market_diff_home` → `odds_movement_pinnacle_diff_home`                                                                                                                                              |
  | `odds_velocity_` / `odds_acceleration_`                         | rate/rate-of-rate of change                                                                                                                                                                                                                                                                            | `velocity_home_24h_to_6h` → `odds_velocity_home_24h_to_6h`; `acceleration_home` → `odds_acceleration_home`; `velocity_prob_home` → `prob_velocity_home`                                                                                                                        |
  | `odds_clv_`                                                     | closing-line-value family                                                                                                                                                                                                                                                                              | `clv_home` → `odds_clv_home`; `sharp_clv_home` → `odds_clv_sharp_home`; `clv_direction_home` → `odds_clv_direction_home`                                                                                                                                                       |
  | `odds_steam_`                                                   | steam-move detection                                                                                                                                                                                                                                                                                   | `steam_detected_home` → `odds_steam_detected_home`; `steam_magnitude_home` → `odds_steam_magnitude_home`                                                                                                                                                                       |
  | `odds_book_count_`                                              | bookmaker-tier population counts                                                                                                                                                                                                                                                                       | `bookmaker_count_sharp` → `odds_book_count_sharp`                                                                                                                                                                                                                              |
  | `odds_<market>_`                                                | alternate-market blocks keep their existing market prefix, just move under the `odds_` namespace                                                                                                                                                                                                       | `asian_handicap_line` → `odds_asian_handicap_line`; `odds_btts_yes` → unchanged (already compliant); `implied_prob_over` → `prob_implied_over`                                                                                                                                 |
  | `ht_` prefix retired                                            | legacy `strategy_service/adapters/sports_feature_subscriber.py`'s `ht_odds_home_implied` folds into the same `prob_implied_home` (half-time context becomes a `period` dimension on the row, not a name-baked prefix) — eliminates the 5th orphaned dialect the parent issue flagged, not just the 4th |

  This is a **generative rule**, not an exhaustive list — todo 2 (UAC) and todo 3 (FSS) apply it mechanically to all 180
  existing `ODDS_COLUMNS` entries plus the new per-venue fields; the table above covers every category present in the
  corpus so the mechanical pass has no ambiguous case left to invent a name for. `outcome`/`venue` tokens are always
  lower-case to match the casing decision made elsewhere in this session (sports data_type reverting to lower-case) —
  this keeps ONE casing convention across the sports vocabulary rather than introducing a second UPPER-token exception
  inside feature names.

- 2026-07-25 (slot 4) **lesson for the next migration of this shape**: a quoted-string-literal search/replace for a
  column rename is NOT sufficient on its own — several producer files build the same column names dynamically via
  f-strings (`f"clv_{outcome}"`, `f"velocity_{side}_{suffix}"`, etc.), which a literal-string regex silently skips,
  leaving the WRITER still emitting the old name while `ODDS_COLUMNS`/tests expect the new one (surfaced as `KeyError`
  test failures, not a quiet no-op). Also confirm with a digit-aware f-string pattern (`{side}_24h_to_6h` has digits in
  the static part, which an `[a-z_]*`-only regex misses) and check for DOUBLE-substitution f-strings
  (`f"velocity_{side}_{suffix}"`) separately from single-substitution ones. Separately: this exact 139-column migration
  landed via two independent concurrent builds (slot 11 shipped first, slot 4 built the same thing unaware) — worth a
  fast pre-flight `git log --oneline -3 -- <target file>` / branch-drift check before starting a large mechanical rename
  that's plausible for another slot to also be doing, to catch the collision before doing the full work rather than
  after.

- 2026-07-25 (slot 4) **review-fix on the gap-fix, features-service@0ab873b3**: a review of `e240eca2` caught that the
  `scripts/sports/seed_mock_data.py` gap-fix over-renamed `df["odds_draw"]` → `df["odds_moneyline_draw"]` inside
  `_compute_vig_column`/`_compute_edge_column`. That `df` comes straight from UAC
  `SyntheticDataGenerator. generate_match_odds()` (`unified_api_contracts/internal/testing/synthetic.py`), which
  hardcodes the RAW columns `odds_home`/`odds_draw`/`odds_away` — a completely different, unrelated schema from the
  `ODDS_COLUMNS` feature-naming scheme this whole migration targets. `odds_home`/`odds_away` were correctly left alone
  in the same two functions; only `odds_draw` got swept up by mistake (a same-name-different-schema false positive my
  earlier repo-wide grep couldn't distinguish, since it only matches on the STRING, not on which schema a given `df`
  actually came from). This would have `KeyError`'d the next time the script actually ran — quality-gates.sh stayed
  green only because the script has zero test coverage (`grep tests/` for it returns nothing), so nothing exercised the
  bug. Reverted both lines back to `df["odds_draw"]`, smoke-tested `_compute_vig_column`/`_compute_edge_column` directly
  against a synthetic `odds_home`/`odds_draw`/`odds_away` frame (correct non-NaN vig/edge values), quality-gates.sh
  fresh full run green (17823 passed). **Lesson**: a column-rename grep must verify which SCHEMA a `df` actually carries
  before renaming a read of it, not just match the string — a scheme-compliant name colliding with an unrelated raw-data
  column of the same old name is a real trap, not a hypothetical one.
- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (sports tranche) — carries a dated operator ruling that keeps it
  NA by name — '**Dispatch model formalized, 2026-07-29 (operator ruling)**: `assigned_vm: NA` stays as declared, but
  remaining bounded todos on this plan are sanctioned to land via the satellite AO-dispatch-batch pattern'. The
  mechanism for landing its work is already chosen and is NOT a flip of this doc; re-litigating it would contradict a
  ruling 1 day old
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — added the UAC schema file this migration targets
  - the 3 real consumer source files (producer/loader/subscriber) the remaining parity-test todo spans.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid — no new 2026-08-08 operator ruling
  touches this doc; the 2026-07-29 ruling that keeps it NA-by-name while sanctioning its bounded todos to land via the
  satellite AO-dispatch-batch pattern is unchanged and not re-litigated. Cross-checked
  `/plans/active/sports_satellite_ao_dispatch_batch10_2026_08_06.md` (2026-08-06, most recent batch): its own
  "Conflict-gated" section lists this doc's `[REVIEW] P3` FSS↔ml-service↔strategy-service naming-parity todo as
  explicitly sequenced after the (per that batch's text) "still-unshipped 3-repo four-way naming migration" — but this
  doc's own Todos show that migration (todos 1-6) is now fully `[x]` shipped, so batch10's premise for holding it back
  is stale and the parity test may be ripe for extraction into the next sports satellite batch. Flagging for the next
  `/ag-closeout-audit sports` or batch-drafting pass rather than reclassifying here — this skill's scope is in-place
  verdicts on existing docs, not drafting new satellite-batch content. Doc stays NA, unchanged this pass.
- **satellite-batch-extraction 2026-08-09 (sports tranche)**: this is exactly that flagged next pass — extracted todo 9
  (`[REVIEW] P3`, FSS↔ml-service↔strategy-service naming-parity test) into
  `/plans/active/sports_satellite_ao_dispatch_batch11_2026_08_09.md` todo 2 (`assigned_vm: planning`), conflict-checked
  against `sports_satellite_ao_dispatch_batch10_2026_08_06.md`'s Conflict-gated entry for this same item (its holding
  premise — "the still-unshipped migration" — confirmed stale: todos 1-6 above are all `[x]`). Todo 10 (`[REVIEW] P3`,
  cross-reference against the wire-sports-end-to-end plan) stays open here, untouched. Doc stays `assigned_vm: NA`.
- **round-9 RECLASSIFY+satellite sweep 2026-08-09**: todo 10 (the last remaining open checkbox) resolved by citation —
  its cross-reference target, `sports_predictions_live_mode_and_backtest_execution_orphaned_2026_07_21.md`, is
  `status: resolved`/archived (2026-07-25), so there is nothing active left to cross-reference; the sequencing concern
  it guarded against is satisfied in substance (this doc's consumer-migration commits landed at/before that resolution).
  **This doc now has ZERO open `- [ ]` checkboxes** — the one remaining tracked item (naming-parity test) is prose-cited
  to `sports_satellite_ao_dispatch_batch11_2026_08_09.md` todo 2, not a checkbox here. Flagging for a future
  `/archive-candidates-audit` pass rather than archiving in this sweep (archival's referrer-sweep ritual is out of scope
  for a citation-fix pass, and batch11's extracted todo hasn't landed yet — premature to archive while the extraction is
  still in flight).
