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
---

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

- [ ] [OPERATOR] P1. Pick the final canonical field names for `OddsFeaturesMixin`/`SportsFeatureVector` — this is the
      genuine architect call the parent issue flagged (not a mechanical rename): decide whether to keep UAC's current
      `market_*` prefix convention, adopt features-service's existing `*_implied_prob` style (least migration friction
      for the actual data producer), or a new deliberate naming. Cover ALL outcome shapes currently in use across the 3
      real consumers: per-outcome implied/fair probability (home/draw/away for 3-way sports markets), per-venue decimal
      odds (`SportsArbDutchingEngine`'s `<outcome_id>_<venue>` need), vig/overround, and the sharp/soft + book-range
      spread fields `features-service` already computes. Record the decision + rationale directly in this plan's
      Progress Log before todo 2 starts (unblocks every downstream todo).
- [ ] [DATA] P1. Update `unified_api_contracts`'s `OddsFeaturesMixin`/`SportsFeatureVector` fields to the names chosen
      in todo 1 (rename in place — UAC being SSOT doesn't make its current names sacrosanct). Add/update the UAC unit
      tests covering the schema's field set. (repo: unified-api-contracts)
- [ ] [DATA] P2. Migrate `features_service/sports/calculators/odds_columns.py`'s `ODDS_COLUMNS` + the odds-features
      exporter to emit the UAC-chosen field names instead of the current `home_implied_prob`-style convention; update
      the exporter's own tests + any downstream fixture files that assert the old column names. (repo: features-service)
- [ ] [BACKEND] P2. Close the silent-agnostic gap in `SportsFeatureLoaderMixin`
      (`ml_service/training/app/core/sports_feature_loader.py`): add real schema validation against
      `OddsFeaturesMixin`'s field set at the point the odds `feature_group` parquet is read, so a producer/consumer
      naming mismatch fails LOUD (raises) instead of silently defaulting via `.get()` — this closes the honest-absence /
      no-silent-placeholders gap the parent issue identified as the actual bug-enabler, independent of which naming
      wins. (repo: ml-service)
- [ ] [BACKEND] P2. Migrate `SportsValueBettingEngine` + `SportsArbDutchingEngine` (`on_tick`'s
      `features: dict[str, float]` reads) to the UAC-chosen field names — update the archetype engines' unit tests and
      any recorded fixture feature dicts. (repo: strategy-service)
- [ ] [BACKEND] P2. Migrate the legacy `strategy_service/adapters/sports_feature_subscriber.py` (currently
      `ht_odds_home_implied` etc.) to the same UAC-chosen names — this is a third, separate convention from the v2
      engines and must not be left behind as a 5th orphaned dialect. (repo: strategy-service)
- [ ] [REVIEW] P3. Once todos 2–6 land, write the FSS-output ↔ ml-service-input ↔ strategy-service-input parity test
      originally requested by `sports_predictions_live_mode_and_backtest_execution_orphaned_2026_07_21.md` — against the
      now-real UAC contract. This is the deliverable the parent issue's own todo 2 asked for; it was blocked until this
      plan's naming decision landed. (repo: features-service, ml-service, strategy-service)
- [ ] [REVIEW] P3. Cross-reference this migration against whichever plan ends up doing the "wire sports end-to-end" work
      (`sports_predictions_live_mode_and_backtest_execution_orphaned_2026_07_21.md`'s remaining todos) — per the
      operator's sequencing note, this migration should land BEFORE or ALONGSIDE that wiring, never after (a live
      pipeline hitting the old 4-way mismatch is the exact landmine this plan exists to defuse).

## Codex SSOTs

No existing codex SSOT names sports odds-feature naming; once todo 1's decision lands, add a short SSOT note under
`codex/09-strategy/architecture-v2/archetypes/` naming the canonical `OddsFeaturesMixin` field set so future archetype
work doesn't reintroduce a 5th convention.

## Progress Log

- 2026-07-21 (slot 7): Plan authored per operator ruling BLK-a1ce4719 on
  `sports_odds_feature_naming_four_way_mismatch_2026_07_21.md`. LOCAL/human track (`assigned_vm: NA`) — the operator
  explicitly asked for a scoped plan for review before any 3-repo dispatch, not immediate AO execution.
