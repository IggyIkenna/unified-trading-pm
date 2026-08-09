---
doc_type: plan
title: Sports taxonomy P3 — move the consumers onto the canonical model (panel, ML, arb, catalogue, Betfair scaffold)
summary: >-
  Phase 3 of the sports canonicalisation chain — everything that READS the sports estate, moved onto the P1 contracts.
  Fixes the distinct-values panel so it badges drift instead of hiding it (the mechanism that let "0 non-canonical"
  coexist with 21 hidden venues); relocates `arbitrage_opportunity` out of the data layer into signals/features with a
  real multi-venue key; wires the ml-service `--family` flag to actually scope SPORTS training; adds T-2h and T-6h as
  MODEL horizons; switches `verify_ml_readiness.py` to the precedented aggregate >=95% bar; points ML labels at the IS
  fixtures-outcomes lineage now that markets/outcomes/settlements are retired; builds the Betfair Exchange adapter
  scaffold as BLOCKED-CREDENTIALS so the one genuinely-traded sports dataset has a proven shape; and closes out the
  fixture-grain catalogue dispatch, the fixtures-browser freshness posture and the sports_dependency mapping-scope
  question. Gated on P1's contracts; deliberately NOT gated on P2's data migration where a consumer can be moved
  contract-first.
status: active
nature: process
asset_group: [sports]
stage: [features]
repos:
  [
    deployment-api,
    strategy-service,
    features-service,
    ml-service,
    market-tick-data-service,
    instruments-service,
    unified-api-contracts,
  ]
scope: [engineer]
tags: [sports, consumers, distinct-values, ml, clv, arbitrage, betfair, catalogue, horizon]
related:
  [
    /plans/active/sports_taxonomy_p1_capture_and_contracts_2026_08_08.md,
    /plans/active/sports_taxonomy_p2_migration_2026_08_08.md,
    /plans/archive/2026_08/sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md,
    /plans/active/sports_group_c_execution_backtest_harness_2026_07_21.md,
    /plans/active/sports_catalog_league_grain_only_scope_2026_07_08.md,
    /plans/active/sports_fixtures_browser_single_catalogue_source_2026_07_24.md,
  ]
created: 2026-08-08
last_updated: 2026-08-08
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 9
estimate_calibrated_ai_days: 7.2
assigned_role: backend_engineer
effort: medium
supersedes:
superseded_by:
resolved_by:
drift_direction: advance-code
depends_on: [sports_taxonomy_p1_capture_and_contracts_2026_08_08]
gate_on_depends: true
context_scope:
  [
    deployment-api/deployment_api/routes/data_status/_distinct_values.py,
    strategy-service/strategy_service/adapters/sports/arbitrage_detector.py,
    features-service/features_service/sports/service.py,
    ml-service/ml_service/training/app/core/sports_feature_loader.py,
    ml-service/ml_service/training/app/core/sports_target_generator.py,
    /codex/02-data/honest-coverage-model.md,
  ]
source: ["sports venue/data-type audit, 2026-08-08 interactive session — 27 operator rulings"]
locked_by:
locked_since:
---

# Sports taxonomy P3 — the consumers

> Gated on P1 contracts. Where a consumer can be moved contract-first it is NOT additionally gated on P2's data
> migration — but any todo that needs migrated DATA to verify must say so and cite P2.

## The panel bug this phase exists to fix

`deployment-api::_distinct_values.py::enumerate_distinct_values` drops blank sentinels and every `_ACCEPTED_EXCEPTIONS`
member **before** enumerating. Result: the sports panel rendered 10 venues / 7 data types and "0 non-canonical" while
the manifest carried 31 venues / 10 data types — 21 fan-out bookmakers (~340k shards), `KALSHI`, a blank venue (2,490
shards) and the uppercase `ODDS` (6,306 CAPTURED shards) all invisible. The panel's own docstring promises "every raw
spelling variant survives, which is the entire point of the panel". It does not.

---

## Todos

### The panel

- [ ] [CODE] P0. **Make the panel BADGE excepted values instead of dropping them.** Every raw distinct value from the
      rollup must appear, each carrying `is_canonical` plus a new `exception_reason` (or equivalent) when it is an
      accepted exception — so a reader sees "known and accepted" rather than "not present". `non_canonical_count` may
      keep excluding accepted exceptions (that is its job as a drift headline), but the VALUE LIST must not. Blank
      sentinels must render as an explicit `<blank>` row, not vanish — a 2,490-shard blank venue is a finding.
- [ ] [TEST] P0. **Regression test from the real failure**: a coverage payload containing an accepted-exception venue, a
      blank venue and a non-canonical value must produce a value list containing ALL THREE. A test asserting only
      `non_canonical_count == 0` would have passed against the broken behaviour — which is why it shipped.
- [ ] [REVIEW] P1. **Re-check the sibling asset_groups for the same masking.** The same drop-before-enumerate applies to
      cefi/defi/tradfi/prediction exception sets. Report per-AG how many values the panel currently hides; file `- [ ]`
      follow-ups per AG where it is material, rather than fixing them silently here.

### Arbitrage

- [ ] [CODE] P0. **Relocate `arbitrage_opportunity` from market-data to the signals/features layer** with a real
      multi-venue key (leg list / venue set), replacing the single-venue stamp that cannot be correct for a cross-venue
      construct. Preserve the existing 13 days (2026-07-25 → 08-06) rather than discarding — it is the only
      arb-frequency history and the arb-decay analysis needs a series.
- [ ] [CODE] P1. **Make the relocated series consume the CORRECTED operator-group guard** shipped in
      `unified-api-contracts@e080ef74` (re-keyed VENUE_OPERATOR_GROUPS, case-insensitive `.upper()` normalisation) +
      `unified-api-contracts@b9a0be80` (OPERATOR_GROUP_VENUES hierarchy — BETFAIR_EX_UK/EU/SB_UK → BETFAIR). Any arb
      whose legs are all one operator must never enter the series. If the historical 13 days contain such rows,
      recompute or flag them — do not carry a known-wrong population forward as a baseline.
- [ ] [REVIEW] P1. **Recompute the arb-decay/alpha-gate baseline on the corrected population** if the bugfix plan's
      blast-radius count comes back non-zero (that plan files this as a follow-up; this todo is its landing site).
      Operator ratified the decay spec as-written on 2026-08-08 — per-leg decay against a shared t=0, gate on p25, edge
      in both absolute bps and as a fraction of signal-time edge, window capped at `hedge_deadline_ms`.

### ML

- [ ] [CODE] P0. **Wire ml-service `--family` to actually scope SPORTS training** (operator ruling 2026-08-08). Today it
      is REQUIRED and validated for `--asset-group SPORTS` but `grep '\.family'` returns zero hits outside argparse —
      all 5 documented family values produce identical behaviour. Each family must scope leagues and target-types (e.g.
      `pregame_clv_family` → CLV targets over the pre-match horizon set). Resolves
      `/plans/active/issues/ml_service_sports_clv_training_pipeline_never_functional_2026_07_26.md`'s sole open todo.
- [ ] [CODE] P0. **Add BOTH T-2h and T-6h as MODEL horizons** (operator ruling 2026-08-08). Current set is
      `['T-10m','T-1h','T-24h']`; both new horizons already have data (T-2h 14,209 shards, T-6h 14,217) and ~2.7x the
      fixture coverage of T-24h, both safely pre-match. Retrain the sports models against the changed feature set and
      report the coverage and performance delta — do not assume it is an improvement, measure it. Resolves the open todo
      in `/plans/active/issues/sports_features_layer_findings_sweep_2026_07_18.md`.
- [ ] [CODE] P1. **Switch `verify_ml_readiness.py` to the precedented aggregate >=95% pass bar** (operator ruling
      2026-08-08), replacing the strict per-day gate that fails near-empty FIFA-international-break days on an exact
      68.6% floor which is honest absence, not a defect. Prerequisite: the P1/P2 zombie-tick fixes in
      `/plans/active/issues/sports_odds_stale_fixture_reinjection_2026_07_14.md` must land first — re-run and confirm
      the floor is gone before switching, so the bar change is not masking a real regression.
- [ ] [CODE] P1. **Point the ML label lineage at IS `fixtures_outcomes` / `matches`** now that
      `markets`/`outcomes`/`settlements` are retired as phantom declarations (P1). Document the lineage explicitly in
      codex so the next reader does not re-open "why is there no settlements data_type".
- [ ] [CODE] P1. **Move the sports feature loader off its PATH-PREFIX read of bucketed odds.**
      `sports_feature_loader._ODDS_BUCKETED_PREFIXES` matches
      `processed/by_date/day={date}/pipeline_mode=batch_mdps_odds_horizon_bucket/` and
      `.../data_type=odds_horizon_bucket/` by string prefix — both disappear under the P1 `horizon`-axis model. This is
      the consumer a `data_type` grep does not find; it must move in the same change as the rename per the codex rename
      rule.

### Betfair Exchange

- [ ] [CODE] P1. **Build the Betfair Exchange adapter scaffold + UAC contract** (operator ruling 2026-08-08: scaffold
      only). This is the ONE genuinely-traded sports dataset available to us — matched-bet volume — and we capture none
      of it; every current row is an odds_api quote. **Fully AO-completable with no operator step**: the scaffold,
      contract, venue capability wiring and unit tests are all buildable credential-free per the
      External-Data-Always-Available rule, and the todo is DONE when they exist and pass QG. It must write
      `data_type=trades` (the name P1 reserved for real matched volume), NOT `odds`. This todo must NOT carry a
      blocked-on-credentials marker: the credential ask is a separate, already-tracked item and must not gate the
      scaffold. **Do not restate the literal marker token here either** — a live `BLOCKED-<TOKEN>` string anywhere in a
      todo block makes that todo permanently non-dispatchable (`_has_live_blocked_token`,
      `agent-orchestrator/server/regen_backlog_from_plan.py`), which is exactly how this todo sat silently absent from
      the live backlog from authoring until 2026-08-08 — the sentence forbidding the marker contained the marker.

### Catalogue, browser, dependency

- [ ] [SCRIPT] P1. **Dispatch the fixture-grain catalogue build, gated on P1 contracts** (operator ruling 2026-08-08).
      The fixture-grain-vs-league-grain decision was already ruled 2026-07-14 ("FIXTURE-GRAIN WANTED"); only dispatch
      routing was unrouted. Build once against the FINAL venue/data_type/horizon axes rather than rebuilding after.
      Resolves the 4 open todos in `/plans/active/sports_catalog_league_grain_only_scope_2026_07_08.md`.
- [ ] [UI] P1. **Fixtures-browser: accept and LABEL the staleness** (operator ruling 2026-08-08). Confirm the
      catalogue-rollup regen cadence and surface it honestly ("as of <timestamp>"), consistent with how the rest of the
      estate labels rollup freshness. No live-day overlay. Needs `[UI]` + `pw:L2 ✓` + a cited regression spec per the
      playwright gate. Resolves `/plans/active/sports_fixtures_browser_single_catalogue_source_2026_07_24.md`.
- [ ] [REVIEW] P1. **`sports_dependency.py::_build_fixture_league_map_from_gcs` — enumerate callers and use cases FIRST,
      then decide** (operator ruling 2026-08-08). Named use cases to check: the fixtures catalogue as a sports auxiliary
      to the instruments catalogue, and dependency checks from downstream services (which already have the manifest, so
      the need may be redundant). **If zero real use cases → DELETE the path** (no shims). If use cases extend beyond
      MVP to all API-Football leagues, note that UAC already holds most of the mapping fixtures for prediction, features
      and the outside-MVP set — reuse it rather than rebuilding. Resolves
      `/plans/active/issues/sports_dependency_check_manifest_vs_gcs_path_2026_07_08.md`.

## Codex SSOTs

- `/codex/02-data/honest-coverage-model.md` — two-layer/two-view model the panel must render honestly.
- `/codex/06-coding-standards/ui-testing-layers.md` — the `[UI]` + `pw:L2` gate for the fixtures-browser todo.
- `/codex/02-data/external-data-always-available-rule.md` — why the Betfair scaffold is built despite no credential.

## Progress Log

- **2026-08-08** — Authored from the interactive sports audit. Panel-masking mechanism measured directly against
  `_distinct_values.py` and the 2026-08-05 rollup. Craft-role note: the Group-C "backend_engineer vs quant_dev" split
  was investigated and is a NON-question — `agent-orchestrator/server/state_store/slots.py:616-624` shows every craft
  role plus plain `worker` collapses to the same `planning` dispatch group and worker pool; `assigned_role` only selects
  the role-prompt file.

- **2026-08-08 (slot 3, interactive — dispatch verification of the whole P1..P4 chain)** — Verified all 8 chain docs are
  `status: active` + `assigned_vm: planning` + `execution_scope: orchestrator-agent`, zero `[OPERATOR]` tags, and
  present on `origin/main`. Live AO backlog (read-only via SSM) holds tasks for every one, one already dispatched to a
  worker. The gates release WITHOUT a human: `gate_on_depends` is machine-managed by `_wire_gate_on_depends_prereqs`,
  which also covers a zero-backlog-task upstream via a derived `gate-upstream-open:<stem>` condition — and P2's second
  gate, `/plans/active/issues/sports_af_full_entity_completion_2026_08_03.md`, is itself `assigned_vm: planning` with 3
  open `[SCRIPT]` todos, so nothing in the chain waits on an operator to release it. **One real gap found and fixed**:
  this plan's Betfair scaffold todo had NEVER been ingested. Its own closing sentence ("Do NOT mark this
  `BLOCKED-CREDENTIALS`") tripped `_has_live_blocked_token`, so regen classified the todo non-dispatchable — while the
  same todo's text asserted it was "Fully AO-completable with no operator step". Rewritten in
  `unified-trading-pm@a134a45948`; re-verified with regen's REAL parser, not a re-implementation: P3 14/15 -> 15/15, and
  all 8 docs now parse 75/75. Corpus-wide the same silent drop hits 47 todos across 37 AO docs (14 of them parse to ZERO
  dispatchable todos) — filed as
  `/plans/archive/issues/ao_silently_non_dispatchable_todos_have_no_visibility_gate_2026_08_08.md`, NOT hand-triaged,
  because three prior regex-widening fixes all regressed. Ingestion of the fixed todo lands on the next plan-regen tick
  (~30 min default); no operator action.
