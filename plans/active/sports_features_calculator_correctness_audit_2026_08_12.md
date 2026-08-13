---
doc_type: plan
title: Sports features-service calculator correctness audit — every calculator, canonical data, honest NaN, no leakage
summary: >-
  The 2026-07-18 findings sweep (sports_features_layer_findings_sweep_2026_07_18 parts 1-3) audited sports DATA
  AVAILABILITY — capture gaps, a normalizer that silently zeroed real rows, odds leakage, honest-coverage tooling grain.
  This plan audits the layer above it: does each of the ~33 sports feature CALCULATORS actually consume its inputs
  correctly and produce a value a prediction model can trust? Seeded with 3 confirmed bugs found in a live session
  2026-08-12 auditing the Transfermarkt-dependent calculators (squad_value_calculator's net_transfer_spend silently
  defaults to 0.0 instead of NaN when transfer_records is absent — which is always, since transfer_records has zero
  fetch implementation; transfer_window_calculator's ~14-column "shock" feature family is permanently, silently all-zero
  for the same reason; player_lineup_calculator/replacement_model_calculator's market_value join was never wired to any
  real Transfermarkt data at all, despite a declared UpstreamReq). Extends `/data-pipeline-check-features` (currently
  proves force/skip-compute + canonical paths + throughput — never checks correctness of VALUES) into the standing
  regression surface for this class of bug, so it does not recur silently a fourth time.
status: draft
nature: process
asset_group: [sports]
stage: [features]
repos: [features-service, unified-api-contracts, unified-trading-pm]
scope: [engineer]
tags: [sports, features, calculators, data-crime, nan-handling, point-in-time, leakage, audit, canonical]
related:
  [
    /plans/active/issues/sports_features_layer_findings_sweep_2026_07_18.md,
    /plans/active/issues/sports_features_layer_findings_sweep_2026_07_18_part2_2026_07_26.md,
    /plans/active/issues/sports_features_layer_findings_sweep_2026_07_18_part3_2026_07_26.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/archive/2026_08/issues/transfermarkt_player_values_data_discarded_2026_08_07.md,
    /codex/06-coding-standards/validation-and-errors.md,
    /codex/04-architecture/features-service-architecture.md,
  ]
created: 2026-08-12
priority: P1
estimate_class: research
estimate_baseline_ai_days: 6.0
estimate_calibrated_ai_days: 7.2
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
assigned_role: data_engineering
effort: high
drift_direction: advance-code
depends_on: []
last_updated: 2026-08-12
locked_by:
locked_since:
supersedes:
superseded_by:
source:
context_scope:
  [
    features-service/features_service/sports/calculators/,
    features-service/features_service/sports/data/gcs_normalizers.py,
    features-service/features_service/sports/exporters/derived_features_exporter.py,
    features-service/features_service/sports/tracking/feature_builder_registry.py,
    unified-api-contracts/unified_api_contracts/canonical/domain/sports/feature_upstream.py,
    unified-api-contracts/unified_api_contracts/canonical/domain/features/required_inputs.py,
    cursor-configs/skills/data-pipeline-check-features/SKILL.md,
  ]
---

# Sports features-service calculator correctness audit (2026-08-12)

## Why this plan, and why it's not a duplicate of the 2026-07-18 sweep

`sports_features_layer_findings_sweep_2026_07_18` (parts 1-3, ~2000 lines total) is a genuinely thorough,
still-partially-open audit — but it is scoped to **data availability**: is the raw data captured, does the normalizer
preserve it, is the manifest grain honest, does the odds pipeline leak post-kickoff data. Its own §A found and fixed
exactly one calculator-input bug (`_normalize_fixture_lineups` zeroing real rows) via a shape mismatch, not a calculator
logic bug.

This plan is scoped one layer up: **given a calculator receives correct, present input data, does its own logic use that
data correctly, distinguish "missing" from "genuinely zero" everywhere, avoid lookahead bias, and actually produce
values worth training a model on?** These are different failure classes:

- A **data-crime** bug: a calculator returns a hardcoded default (usually `0.0`) when its input is absent,
  indistinguishable from a genuine zero value. Confirmed today in
  `squad_value_calculator._compute_team_net_transfer_spend` — every call in production returns `0.0` (never NaN) because
  `transfer_records` is never fetched, silently contradicting this same file's own documented "missing-data cells
  default to NaN, NEVER 0.0" rule for its sibling features in the identical function.
- A **dead feature** bug: a calculator produces a column that is always the same constant value across the entire corpus
  because its real input is never wired, silently carrying zero information into any model trained on it. Confirmed
  today: `transfer_window_calculator`'s ~14 "shock" columns (`*_minutes_lost_pct_last_window`,
  `*_value_lost_pct_last_window`, `*_new_signing_*`, `*_post_window_lineup_stability_*`) are always exactly `0.0` for
  every fixture, forever, because they depend on `transfer_records` which has no writer.
- A **disconnected-join** bug: a calculator's declared upstream (`UpstreamReq`/`InputReq`) is never actually joined into
  the DataFrame it receives at the real production call site, so the declaration is aspirational, not real. Confirmed
  today: `player_lineup_calculator` and `replacement_model_calculator` both expect a per-player `market_value` column;
  the actual production caller (`derived_features_exporter.py` / `feature_builder_registry.py`) passes
  `lineups = ref_data.get("fixture_lineups", ...)` (api_football) with **no join against Transfermarkt `player_values`
  anywhere** — confirmed by tracing both `derived_features_exporter.py:313-318` and the `feature_builder_registry.py`
  `required_inputs` list for `player_lineup` (`["target_fixtures", "lineups", "player_stats"]` — `player_values` is not
  in it despite the calculator's own declared optional UpstreamReq).
- A **lookahead-bias / leakage** bug: a calculator reads a value that would not actually have been known at the
  fixture's `available_at` timestamp — the class the 2026-07-18 sweep's §B already found once in the odds pipeline. Not
  yet checked for the calculator layer itself (as opposed to the upstream data layer) — this plan's job.

**None of the 3 confirmed bugs above are about missing DATA — the underlying inputs load fine (or would, once
Transfermarkt is backfilled per `transfermarkt_player_values_data_discarded_2026_08_07.md`). They are about what each
calculator DOES with its inputs.** This is exactly why `/data-pipeline-check-features` — which proves the compute path
runs and writes canonical paths — did not catch any of them: it never inspects the VALUES a calculator produces.

## Audit method (apply this checklist to every calculator below)

For each calculator in scope:

1. **Trace it to its real production caller** — do not trust its own docstring/`UpstreamReq` declaration. Find the
   actual call site (`derived_features_exporter.py`, `feature_builder_registry.py`, or wherever else it's invoked in
   production) and confirm every DataFrame it receives is actually populated with the data its docstring claims, not an
   empty/default DataFrame nobody ever fills.
2. **NaN-vs-zero**: for every feature column, when its underlying input is absent, does it return NaN (honest unknown)
   or a hardcoded default (0.0, 0.5, etc.)? A hardcoded default is only correct when the underlying real-world quantity
   is unambiguously that value when the input condition holds (e.g. `is_summer_window_open=0.0` when no window is open
   IS a correct real zero) — never as a stand-in for "we don't have this data."
3. **Dead-feature check**: sample the calculator's output over a real multi-month window (use
   `/data-pipeline-check-features` or a direct GCS read) and confirm every declared column has genuine variance. A
   column that is 100% one value across the whole sample is either a real universal constant (rare, name it explicitly)
   or a wiring bug.
4. **Point-in-time correctness**: does every input value used actually carry a timestamp <= the target fixture's
   `available_at_rule` cutoff (per `required_inputs.py`'s declared rule for that data_type)? Check for any read that
   doesn't filter/partition by an as-of date, or that reads a "current" snapshot rather than the historically-correct
   one.
5. **Canonical GCS/manifest alignment**: does the calculator's actual read path match the canonical `gcs_paths.py` path
   template and the manifest `data_type` the writer uses — not a legacy/stale path a previous refactor left behind?

## Todos

- [ ] [CODE] P0. Fix `squad_value_calculator._compute_team_net_transfer_spend` to return `np.nan` (not `0.0`) when
      `transfer_data` is empty/absent — matching this same file's own stated rule for every sibling feature in
      `_compute_team_squad_features`. Add a regression test asserting `net_transfer_spend` is NaN (not 0.0) for a team
      with no transfer_records rows, distinct from a team with real rows summing to a genuine net-zero. Repo:
      features-service. Done when: the test exists, passes, and QG is green.
- [ ] [DIAG] P1. Confirm live whether `transfer_window_calculator`'s ~14 shock columns are indeed 100% constant `0.0`
      across a real multi-month production sample (not just reasoned from the missing-input trace) — pull a real window
      via `/data-pipeline-check-features` or a direct GCS read of `derived_features`/`transfer_window` shards and check
      column variance directly. If confirmed, this todo's done-when is met; if NOT (some non-transfer_records path
      already populates them another way this session missed), correct the finding in this doc's Progress Log before the
      next todo proceeds.
- [ ] [CODE] P1. **UNBLOCKED 2026-08-13**: `transfer_records` now has a real writer, backfilled and verified 32/32
      mappable Prediction-tier leagues (164,924 rows) — see
      `plans/archive/2026_08/issues/transfermarkt_player_values_data_discarded_2026_08_07.md` (RESOLVED). Re-verify
      `transfer_window_calculator`'s shock columns show genuine variance against this real backfilled data.
- [ ] [CODE] P1. Wire a real per-player `market_value` join into `player_lineup_calculator`'s production input — trace
      `derived_features_exporter.py`'s `lineups` DataFrame construction, add the missing join against Transfermarkt
      `player_values` (unpacking the per-player JSON `players` column — see the next todo), and update
      `feature_builder_registry.py`'s `player_lineup` `required_inputs` to actually include `player_values`. Repo:
      features-service. Done when: `top1_player_value_share_xi`/`top3_player_value_share_xi` show real variance on a
      sample day with known Transfermarkt coverage (e.g. EPL, per the live verification in
      `transfermarkt_player_values_data_discarded_2026_08_07.md`).
- [ ] [CODE] P1. Fix `gcs_normalizers._normalize_player_values` to unpack the per-player JSON `players` column into flat
      per-player rows (team_id, player_id, market_value_eur, position, age — whatever the JSON payload carries) in
      addition to its current flat team-aggregate handling. This is the prerequisite for the previous todo. Repo:
      features-service. Done when: a real captured PLAYER_VALUES snapshot round-trips through this normalizer into a
      per-player DataFrame with non-null `market_value_eur`.
- [ ] [CODE] P2. Re-verify `replacement_model_calculator`'s actual production wiring — confirm whether
      `feature_builder_registry.py`'s Phase 1 registration is genuinely live in production (vs.
      `derived_features_exporter.py` being the only real path, in which case `replacement_model` may not run in
      production at all). If it is live, apply the same market_value join fix as `player_lineup_calculator` (it inherits
      the same gap). Repo: features-service. Done when: the answer is stated with evidence (a real call-graph trace or a
      live production log showing the group executing), not inferred.
- [ ] [DIAG] P1. Audit the Phase-0 calculator group (`squad_value`, `transfer_window`, `player_lineup`, `manager`,
      `injury_impact`, `formation`, `european_fatigue`, `travel_calculator`, `venue_context`, `weather_calculator`,
      `season_context`, `team_form`, `team_goals`, `team_xg`, `advanced_stats_calculator`, `h2h_calculator`,
      `elo_calculator`, `steam_detector`, `odds_calculator`, `halftime_calculator`, `ht_features`, `goal_timing`,
      `league_calculator`, `promoted_team_features_calculator`, `promoted_team_handler`) against the 5-point checklist
      above. Group by shared input source where possible to avoid re-tracing the same DataFrame construction repeatedly.
      Repo: features-service. Done when: every calculator in this group has a stated verdict (clean / data-crime /
      dead-feature / disconnected-join / leakage, with evidence) recorded in this doc's Progress Log.
- [ ] [DIAG] P1. Audit the Phase-1 calculator group (`relative_context_calculator`, `bench_sub_calculator`,
      `replacement_model_calculator`, `xg_decomposition_calculator`, `multisource_xg_calculator`,
      `poisson_xg_calculator`, `meta_features_calculator`, `bucketed_features_calculator`, `ml_predictions`,
      `team_derived`, `referee_features`) against the same checklist — these additionally depend on Phase-0 outputs, so
      also confirm each one's `depends_on` declaration in `feature_builder_registry.py` matches what it actually reads.
      Repo: features-service. Done when: every calculator in this group has a stated verdict recorded in this doc's
      Progress Log.
- [ ] [DIAG] P2. For every calculator marked "clean" in the two audits above, spot-check point-in-time correctness
      specifically: pick 2 real historical fixtures at least a season apart, compute features for each using data "as
      of" its own kickoff date, and confirm the computed value does not change if data captured AFTER that fixture's
      kickoff is later added to the corpus (i.e. re-running the SAME historical fixture after new data has landed
      reproduces the SAME feature values — no forward leakage). Repo: features-service.
- [ ] [CODE] P2. Extend `/data-pipeline-check-features` (`cursor-configs/skills/data-pipeline-check-features/SKILL.md` +
      its driver) with a new correctness leg that would have caught all 3 bugs seeded in this doc automatically: (a) a
      dead-feature detector — flag any declared feature column that is 100% one value across the sampled window; (b) a
      data-crime detector — for calculators with a documented "NaN not 0.0" contract in their own docstring, sample rows
      with a known-absent upstream input and assert the output is NaN, not the documented-banned default. This makes the
      skill catch this bug CLASS going forward, not just report today's 3 instances once. Repo: unified-trading-pm
      (skill) + features-service (driver hooks, if the skill needs new assertions the current driver doesn't expose).
      Done when: running the extended skill against `squad_value`/`transfer_window` in their CURRENT (unfixed, at
      authoring time) state reproduces both confirmed bugs as automatic findings, proving the check is real and not just
      narrated.
- [ ] [DOC] P2. Once the two Phase-0/Phase-1 audits above are complete, write the consolidated verdict table (one row
      per calculator: clean / bug class / evidence / fix status) into this doc, and file any newly-found bug as its own
      `- [ ]` todo here rather than leaving it as prose. Cross-reference `sports_consolidated_closeout_2026_07_19.md` if
      this plan's findings affect that closeout's own open scope.

## Progress Log

- **2026-08-12 (interactive session)**: filed after an operator-directed downstream check of the Transfermarkt
  `PLAYER_VALUES`/`TRANSFER_RECORDS` consumers (`squad_value_calculator`, `transfer_window_calculator`,
  `player_lineup_calculator`, `replacement_model_calculator`) surfaced 3 confirmed bugs (data-crime, dead-feature,
  disconnected-join — see the "Why this plan" section above for full evidence) that are outside
  `transfermarkt_player_values_data_discarded_2026_08_07.md`'s own scope (that doc owns the WRITER-side data; this plan
  owns the CALCULATOR-side correctness) and outside the 2026-07-18 sweep's scope (data availability, not calculator
  logic). Operator ruled this should be a human/local plan (`assigned_vm: NA`), to be driven by a separate interactive
  session/agent, not AO-dispatched. `status: draft` until that session is ready to pick it up — flip to `active` then.
