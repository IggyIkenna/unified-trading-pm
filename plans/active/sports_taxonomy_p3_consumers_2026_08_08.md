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

- [x] ✅ [CODE] P0. **Make the panel BADGE excepted values instead of dropping them.** Every raw distinct value from the
      rollup must appear, each carrying `is_canonical` plus a new `exception_reason` (or equivalent) when it is an
      accepted exception — so a reader sees "known and accepted" rather than "not present". `non_canonical_count` may
      keep excluding accepted exceptions (that is its job as a drift headline), but the VALUE LIST must not. Blank
      sentinels must render as an explicit `<blank>` row, not vanish — a 2,490-shard blank venue is a finding. —
      deployment-api@1b8d20b06334daeb6e3d8ad776e4f68707068f2e: `enumerate_distinct_values()` no longer drops blank
      sentinels or accepted-exception values before enumeration; blanks collapse into one `<blank>` row per axis and
      accepted-exception entries carry a new `exception_reason` field (via `_ACCEPTED_EXCEPTION_REASONS`), both still
      counted out of `non_canonical_count` only. Existing unit tests updated to assert presence + `exception_reason`
      instead of absence; full quality-gates.sh green (5265 passed).
- [x] ✅ [TEST] P0. **Regression test from the real failure**: a coverage payload containing an accepted-exception
      venue, a blank venue and a non-canonical value must produce a value list containing ALL THREE. A test asserting
      only `non_canonical_count == 0` would have passed against the broken behaviour — which is why it shipped. —
      deployment-api@625ca75: added `TestPanelMaskingRegressionFromRealFailure` — a single payload with an
      accepted-exception bookmaker, a blank venue and a synthetic genuine-drift venue, asserting all three survive in
      the value list with correct `is_canonical`/`exception_reason` badging; also asserts `non_canonical_count` alone
      (2, excluding the bookmaker) would not have distinguished the fixed behaviour from a masked one. Full
      quality-gates.sh green (5266 passed).
- [x] ✅ [REVIEW] P1. **Re-check the sibling asset_groups for the same masking.** The same drop-before-enumerate applies
      to cefi/defi/tradfi/prediction exception sets. Report per-AG how many values the panel currently hides; file
      `- [ ]` follow-ups per AG where it is material, rather than fixing them silently here. — Reviewed
      deployment-api@1b8d20b06334daeb6e3d8ad776e4f68707068f2e: the drop-before-enumerate masking was NEVER an
      asset_group-conditional code path — it lived in the single shared `enumerate_distinct_values()` function that
      every asset_group's `GET /distinct-values/{asset_group}` call passes through (no `if asset_group == "sports"`
      branch anywhere in `_is_blank`/`_is_accepted_exception`/`_accepted_exception_reason`/the enumeration loop). The P0
      fix therefore already landed for cefi/defi/tradfi/prediction/sports SIMULTANEOUSLY in that one commit, not
      sports-only. Verified three ways: (1) commit diff shows the change is entirely inside the shared function/dict
      definitions, zero per-AG conditionals; (2) the commit's OWN shipped unit tests
      (`test_route_data_status_distinct_values.py`) already exercise cefi/defi/tradfi through this exact function —
      `test_defi_bare_pipeline_phase_venue_is_canonical_not_drift`,
      `test_cefi_and_tradfi_instrument_types_are_not_case_folded`,
      `test_tradfi_and_cefi_chain_bundle_instrument_types_are_badged_not_dropped` — with badge-not-drop +
      `exception_reason` assertions, and QG was green (5265 passed, per item 1's own evidence line) covering these exact
      tests; (3) `prediction` (and cefi/defi/tradfi) are all fully registered in
      `VENUES_BY_ASSET_GROUP`/`DATA_TYPES_BY_ASSET_GROUP` (unified-api-contracts `market_data_categories.py`), so the
      endpoint is completely wired for every sibling AG, not just sports. **Per-AG count of values currently hidden by
      drop-before-enumerate: 0 for cefi, 0 for defi, 0 for tradfi, 0 for prediction** (same as sports post-fix) — not
      material, no follow-up issue docs filed. (defi's separate bare-vs-composite-venue and case-insensitive
      instrument_type handling in `_comparison_set()` is a DIFFERENT, already-fixed false-drift mechanism — unrelated to
      this masking bug — see the module docstring's "Grain-aware exceptions" section.)

### Arbitrage

- [ ] [CODE] P0. **Relocate `arbitrage_opportunity` from market-data to the signals/features layer** with a real
      multi-venue key (leg list / venue set), replacing the single-venue stamp that cannot be correct for a cross-venue
      construct. Preserve the existing 13 days (2026-07-25 → 08-06) rather than discarding — it is the only
      arb-frequency history and the arb-decay analysis needs a series.
  - **Partial progress (2026-08-09)** — the new home's DETECTION + PERSISTENCE primitives are built, tested, and
    shipped; the live wiring (todo below) and the history migration + old-adapter deletion (todo below) remain. Checkbox
    stays open — "relocate + preserve history" is one unit and neither half of the remaining work is done.
- [x] ✅ [CODE] P0. **Wire the new detector into a live/batch producer** reading real `odds`/`trades` snapshots (the
      same per-bookmaker tick data `market-data-processing-service`'s `SportsArbitrageAdapter` reads today) and calling
      `features_service.sports.arb.detect_sports_arbitrage_opportunity` + `write_arb_opportunities` per fixture/interval
      — mirroring `features_service.cross_instrument.app.cross_venue_arb_runner`'s tick-loop shape. Without this the new
      module is a second "reference-only" library with no real caller (the same dead-code pattern found in
      `unified_api_contracts.canonical.domain.sports.arbitrage.ArbitrageOpportunity`, see below).
  - **Shipped (2026-08-09)** — `features-service@67de878df`: new `features_service/sports/arb/runner.py`
    (`run_arb_detection_once` + `run_live_loop`, reads MDPS's bucketed `odds_horizon_bucket` output via
    `read_bucketed_odds`, groups per-`(fixture_id, horizon_name)` snapshot, calls the detector, writes via
    `write_arb_opportunities`) + `--operation arb-detect` CLI handler + `_OPERATIONS` registration + unit tests
    (`tests/sports/unit/arb/test_runner.py`). QG green. Scope excludes the P1 history-migration and old-adapter-deletion
    todos below (unstarted, separate).
- [ ] [CODE] P1. **Migrate the historical 13 days (2026-07-25 → 08-06) by reprocessing the underlying raw odds/trades
      ticks** through the new detector (the old MDPS candle output only ever kept the aggregated `arb_margin`, never
      which bookmaker contributed each leg — so a leg-level series must be RECOMPUTED from the raw ticks, not migrated
      from the old rows). Once the live producer above exists and the history is backfilled, delete
      `market-data-processing-service/market_data_processing_service/app/adapters/sports/arbitrage_adapter.py`
      (`SportsArbitrageAdapter`) and its ~23 test references (`test_sports_adapters.py`, `test_schema_robustness.py`,
      `test_adapter_registry_coverage.py`).
- [ ] [CODE] P1. **Make the relocated series consume the CORRECTED operator-group guard** shipped in
      `unified-api-contracts@e080ef74` (re-keyed VENUE_OPERATOR_GROUPS, case-insensitive `.upper()` normalisation) +
      `unified-api-contracts@b9a0be80` (OPERATOR_GROUP_VENUES hierarchy — BETFAIR_EX_UK/EU/SB_UK → BETFAIR). Any arb
      whose legs are all one operator must never enter the series. If the historical 13 days contain such rows,
      recompute or flag them — do not carry a known-wrong population forward as a baseline.
  - **Done (2026-08-09) for the new detector** — `features_service/sports/arb/detector.py`'s
    `detect_sports_arbitrage_opportunity` calls `arb_legs_are_independent` and returns `None` (excludes) when legs
    collapse to one operator group; covered by
    `tests/sports/unit/arb/test_detector.py::test_same_operator_group_legs_never_enter_the_series`. Checkbox stays open
    — "the relocated series" isn't live yet (depends on the live-wiring todo above), and the historical-13-day
    population hasn't been checked/recomputed against this guard yet.
- [x] ✅ [REVIEW] P1. **Recompute the arb-decay/alpha-gate baseline on the corrected population** if the bugfix plan's
      blast-radius count comes back non-zero (that plan files this as a follow-up; this todo is its landing site).
      Operator ratified the decay spec as-written on 2026-08-08 — per-leg decay against a shared t=0, gate on p25, edge
      in both absolute bps and as a fraction of signal-time edge, window capped at `hedge_deadline_ms`. — **No recompute
      needed; condition (non-zero blast radius) was never met.** The bugfix plan
      (`/plans/archive/2026_08/sports_arb_operator_group_and_commission_bugfix_2026_08_08.md`, todo 8) and its finalize
      twin (`_finalize.md`, todo 3) both measured the blast radius at **zero**: same-operator-group arbs = 0, SMARKETS
      arbs = 0, over the full paper-trade/backtest record. Two structural reasons, re-verified live in this session (not
      just re-read from the archived doc): (1) `strategy-service`'s dutching backtest
      (`engine/strategies/v2/arbitrage_structural/sports_arb_dutching.py`) never calls
      `arb_legs_are_independent()`/`_expected_commission_pct()` at all — confirmed via grep, those symbols appear only
      in `adapters/sports/arbitrage_detector.py`; (2) the paper-trade path
      (`adapters/sports_feature_subscriber.py::_build_market_from_feature_vector`) still builds every market from a
      single FSS feature vector's one `bookmaker_key` (line 123), so all legs share one bookmaker and
      `arb_legs_are_independent` returns `False` unconditionally — no arb signal is ever emitted through the buggy path.
      All 6 fix commits (`e080ef74`, `b9a0be80`, `0fd51983`, `1a96c482`, `968237b8`, `446c2cb3`) confirmed present on
      `origin/live-defi-rollout` via `git log`. Since the historical arb-decay/alpha-gate baseline was never built from
      any operator-group-violating or SMARKETS-commission-blind rows, it needs no recomputation. This todo and the
      finalize doc's todo 3 are the same landing site — recorded here so the P3 plan carries its own closure evidence
      rather than only a cross-reference.

### ML

- [x] ✅ [CODE] P0. **Wire ml-service `--family` to actually scope SPORTS training** (operator ruling 2026-08-08, see
      `/plans/active/issues/ml_service_sports_clv_training_pipeline_never_functional_2026_07_26.md`). Today it is
      REQUIRED and validated for `--asset-group SPORTS` but `grep '\.family'` returns zero hits outside argparse — all 5
      documented family values produce identical behaviour. Each family must scope leagues and target-types (e.g.
      `pregame_clv_family` → CLV targets over the pre-match horizon set). Resolves
      `/plans/active/issues/ml_service_sports_clv_training_pipeline_never_functional_2026_07_26.md`'s sole open todo. —
      **DONE 2026-08-09** (slot-22, `backend_engineer`): `ml-service@bfdcff2`. Added
      `SPORTS_FAMILY_LEGACY_TARGET_TYPES` + `legacy_target_types_for_families()` in `family_router.py`, mapping each of
      the 5 `SportsMLPresets` families to the legacy `target_type` key(s) it owns (`pregame_xg_family`→xg,
      `pregame_clv_family`→clv, `ht_xg_family`→ht_delta; `ht_clv_family`/`meta_family` raise — no legacy single-output
      builder exists for halftime-market-CLV or OOF meta yet, so they fail loud instead of silently mis-mapping to
      `ht_delta`). `train_handler.py::_generate_sports_variants` now scopes `target_types` to `--family` by default and
      intersects with an explicit `--target-types` filter (verified the already-working
      `--family pregame_clv_family --target-types clv` retrain invocation from the resolved issue doc keeps working
      unchanged). `pipeline_handler.py::_build_pipeline_config` validates the single `--target-type` against the family
      scope for parity. 9 new unit tests (family-scoping + error cases) in `test_family_router.py` +
      `test_cli_handlers_coverage.py`; `quality-gates.sh` green (2177 passed, 4 skipped, sentinel-verified on
      `bfdcff2`).
- [ ] [CODE] P0. **Add BOTH T-2h and T-6h as MODEL horizons** (operator ruling 2026-08-08). Current set is
      `['T-10m','T-1h','T-24h']`; both new horizons already have data (T-2h 14,209 shards, T-6h 14,217) and ~2.7x the
      fixture coverage of T-24h, both safely pre-match. Retrain the sports models against the changed feature set and
      report the coverage and performance delta — do not assume it is an improvement, measure it. Resolves the open todo
      in `/plans/active/issues/sports_features_layer_findings_sweep_2026_07_18.md`. **Partial progress 2026-08-09
      (slot-11)**: horizon-declaration half SHIPPED — `SPORTS_MODEL_CONFIGS` (`model_2d`/`model_3d` @ T-6h,
      `model_2e`/`model_3e` @ T-2h) + matching grid configs — `ml-service@8af9324`; `FEATURE_HORIZONS`/`MODEL_HORIZONS`
      now emit T-6h/T-2h feature rows — `features-service@3394de8`. Retrain + measured delta remains OPEN — blocked on
      the sports ensemble trainer being hardcoded to `model_2a` only (no models have ever trained end-to-end at
      T-1h/T-10m either); see
      `/plans/active/issues/sports_t2h_t6h_horizon_retrain_blocked_on_generic_trainer_2026_08_09.md` for the
      generalize-then-retrain follow-up todos. Checkbox stays unflipped until the retrain half lands.
- [ ] [CODE] P1. **Switch `verify_ml_readiness.py` to the precedented aggregate >=95% pass bar** (operator ruling
      2026-08-08), replacing the strict per-day gate that fails near-empty FIFA-international-break days on an exact
      68.6% floor which is honest absence, not a defect. Prerequisite: the P1/P2 zombie-tick fixes in
      `/plans/active/issues/sports_odds_stale_fixture_reinjection_2026_07_14.md` must land first — re-run and confirm
      the floor is gone before switching, so the bar change is not masking a real regression.
- [x] ✅ [CODE] P1. **Point the ML label lineage at IS `fixtures_outcomes` / `matches`** now that
      `markets`/`outcomes`/`settlements` are retired as phantom declarations (P1). Document the lineage explicitly in
      codex so the next reader does not re-open "why is there no settlements data_type". — features-service@fa67da20:
      traced the full lineage end-to-end against live code (IS `sports_fixtures.py` Q6 write → UTL
      `read_fixtures_joined` → features-service `gcs_normalizers.py`/`_FIXTURE_COL_MAP` → exporters → ml-service
      `sports_feature_loader.py`/`sports_target_generator.py`) and found + fixed a REAL bug on that path:
      `_FIXTURE_COL_MAP` only knew the pre-2026-07-14-cutover legacy `home_score`/`away_score` column names, not the
      current Q6 `home_score_regulation`/`away_score_regulation` names UTL's reader actually returns for every
      post-cutover date (its own comment says the legacy names are "retired and no longer written") —
      `home_goals`/`away_goals` (and every derived XG/win-draw-loss/meta ML label) were silently ALL-NaN for current
      fixtures. Added the Q6 names to `_FIXTURE_COL_MAP` (existing `_rename_coalescing_collisions` already merges both
      eras across a straddling lookback window) + a regression test. Full lineage documented in
      `/codex/02-data/sports-data-types-catalog.md` § "ML label lineage". Halftime score labels
      (`ht_home_goals`/`ht_away_goals`) are NOT covered by Q6 at all (no halftime columns in `_Q6_OUTCOME_COLUMNS`) —
      whether they have an equivalent post-cutover gap is unverified, flagged in the codex section as a follow-up rather
      than silently expanding this todo's scope.
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
- [x] ✅ [UI] P1. **Fixtures-browser: accept and LABEL the staleness** (operator ruling 2026-08-08, see
      `/plans/active/sports_fixtures_browser_single_catalogue_source_2026_07_24.md`'s dated ruling banner). Confirm the
      catalogue-rollup regen cadence and surface it honestly ("as of <timestamp>"), consistent with how the rest of the
      estate labels rollup freshness. No live-day overlay. Needs `[UI]` + `pw:L2 ✓` + a cited regression spec per the
      playwright gate. Resolves `/plans/active/sports_fixtures_browser_single_catalogue_source_2026_07_24.md`. — **DONE
      2026-08-09** (slot-20, `ui_developer`): confirmed the regen cadence at the SSOT
      (`deployment-service/terraform/gcp/lifecycle_catalogue_scheduler.tf`) — sports catalogue rollup fires `0 1 * * *`
      (01:00 UTC daily incremental) + `0 7 * * 6` (Sat 07:00 UTC full rebuild). `deployment-api@a050b88`: new
      `fixtures_browser.catalogue_as_of()` reads `prod/catalog.parquet`'s blob `last_modified` (TTL-cached metadata
      HEAD, same cache window as the frame reader; `None` on any read failure, never fabricated) and
      `GET /fixtures/browse` now returns it as `as_of`; 4 new unit tests (success/failure/missing-blob/TTL-cache).
      `deployment-ui@2259df1`: `FixturesBrowser.tsx` renders "Catalogue as of &lt;timestamp&gt; — regenerated daily...
      live status may lag" or an explicit "freshness unavailable" fallback on a null `as_of` — no live-day overlay, per
      the ruling cited above. 2 new Vitest cases (both states) + `pw:L2 ✓`
      `deployment-ui/tests/e2e/data-status-fixtures-browser-as-of-freshness.spec.ts`. Both repos' `quality-gates.sh`
      green, both SHAs verified ancestors of `origin/live-defi-rollout`.
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

- **2026-08-09 (slot 14, review)** — Closed the "sibling asset_groups" masking re-check todo. Finding: NOT MATERIAL, 0
  hidden values per AG. The drop-before-enumerate bug fixed in `deployment-api@1b8d20b06334daeb6e3d8ad776e4f68707068f2e`
  lived in the single shared `enumerate_distinct_values()` function that EVERY asset_group's
  `GET /distinct-values/{asset_group}` call passes through — there was never a sports-only code path, so the fix already
  covers cefi/defi/tradfi/prediction as of the same commit. Verified via commit-diff read (no per-AG conditionals), the
  commit's own already-QG-green unit tests exercising cefi/defi/tradfi through the identical function, and confirming
  all four sibling AGs are fully registered in UAC's `VENUES_BY_ASSET_GROUP`/ `DATA_TYPES_BY_ASSET_GROUP`. No follow-up
  issue docs filed (nothing material to track).

- **2026-08-09 (slot 15)** — Dispatched the Arbitrage section's second todo ("Make the relocated series consume the
  CORRECTED operator-group guard"), but its prerequisite — the FIRST todo in the same section ("Relocate
  `arbitrage_opportunity` from market-data to the signals/features layer with a real multi-venue key") — is still
  unchecked and genuinely not done:
  `market-data-processing-service/market_data_processing_service/app/adapters/sports/ arbitrage_adapter.py::SportsArbitrageAdapter`
  still writes the `arbitrage_opportunity` MDPS candle with a single-venue stamp
  (`venue_arr = info.get("venue", "UNKNOWN")`) and picks best-odds-per-outcome across ALL bookmakers with **no**
  operator-group filtering at all — the "relocated series" this second todo needs to modify does not exist yet. (Two
  pre-existing, unrelated arb code paths were checked and ruled out as candidates: (1)
  `strategy-service/strategy_service/adapters/sports/arbitrage_detector.py` is a live signals-layer 3-way detector that
  already imports `arb_legs_are_independent` from the CURRENT `unified-api-contracts` `arb_config.py` (which already
  carries both e080ef74 and b9a0be80, plus a later prune commit `1a96c482`) — it is correctly guarded today, but it is
  not the 13-day `arbitrage_opportunity` history series this plan's first todo is about relocating; (2)
  `features-service/features_service/sports/arb/{arb_calculator.py,vig.py}` computes unrelated per-fixture ML features
  (`arb_percent`/`eligible_pair_count`/`arb_duration_seconds`) with zero operator-group awareness — also not the
  relocated series.) This plan has no `sequential: true` and no per-todo prereq syntax (CLAUDE.md: prereqs come only
  from `sequential`/`gate_on_depends`), so the two todos dispatch independently even though the second is a hard
  content-dependency on the first's output — an authoring gap in this specific arb sub-chain, not a data problem.
  Skipping this todo back to the queue (`reason_code: GATED`) rather than absorbing the much larger P0 relocation scope
  into a 1h P1 task. Whoever picks up the first todo should apply the operator-group guard (`arb_config.py`'s
  `arb_legs_are_independent`, already correct) to the new series AS PART of building it, which would satisfy both todos
  in one pass — or a future dispatch of this second todo should re-check whether the first has landed since this note.

- **2026-08-09 (slot 17, review)** — Closed the Arbitrage section's third todo ("Recompute the arb-decay/alpha-gate
  baseline on the corrected population"). This todo was conditional on the bugfix plan's blast-radius count coming back
  non-zero; it never did. Both `sports_arb_operator_group_and_commission_bugfix_2026_08_08.md` (todo 8) and its finalize
  twin (todo 3) measured the blast radius at zero (same-operator-group arbs = 0, SMARKETS arbs = 0) and archived that
  finding 2026-08-08. Re-verified live rather than trusting the archived doc alone: grepped `strategy-service` and
  confirmed the dutching backtest (`sports_arb_dutching.py`) still never calls
  `arb_legs_are_independent()`/`_expected_commission_pct()`, and the paper-trade path
  (`sports_feature_subscriber.py::_build_market_from_feature_vector`) still builds every market from one FSS vector's
  single `bookmaker_key`, so `arb_legs_are_independent` is structurally unreachable/always-False on that path — same
  structural reasons the archived finding cites, unchanged since 2026-08-08. All 6 fix commits confirmed present on
  `origin/live-defi-rollout` via `git log`. No recompute possible or needed since the historical baseline never
  contained the bug's population. No code shipped — this is a pure documentation closure, mirroring the finalize doc's
  own precedent that "a measured zero is a result, not a skip."

- **2026-08-09 (slot 22, backend_engineer)** — Dispatched the ML section's "Move the sports feature loader off its
  PATH-PREFIX read of bucketed odds" todo, but it is genuinely premature — the same authoring-gap pattern slot 15
  already flagged for the Arbitrage sub-chain (no `sequential`/`gate_on_depends` between a P3 consumer todo and its hard
  P2 content-dependency). Verified live, not just re-read from this doc: P2
  (`/plans/active/sports_taxonomy_p2_migration_2026_08_08.md`) todo "Move `odds_horizon_bucket` (135,980 shards) onto
  the `odds` + `horizon` model" is still unchecked, and its own gating "Consumer enumeration" todo (which explicitly
  names `sports_feature_loader._ODDS_BUCKETED_PREFIXES` as a todo target) is also still unchecked. Confirmed the
  physical write side has not moved either:
  `market-data-processing-service/app/adapters/sports/ bucket_assignment_adapter.py:696` still hard-codes
  `data_type = "odds_horizon_bucket"` for the registered candle adapter (grepped the whole repo for a `horizon=` GCS
  path segment or any new physical shape — none exists anywhere in MDPS, features-service, or UAC). UAC's P1-landed
  `SPORTS_HORIZONS`/`is_valid_horizon()` (`market_data_categories.py`) is a VALUE-vocabulary SSOT only — no
  path-template constant for the new horizon-axis physical shape exists in any repo. There is therefore no new canonical
  prefix in existence anywhere for the loader to "move onto" — the P3 todo's own text ("must move in the same change as
  the rename") makes the move a joint change with P2's physical re-stamp, which has not landed. Skipping back to the
  queue (`reason_code: GATED`) rather than fabricating a speculative path shape nothing writes yet or silently no-op-ing
  the todo. Recommend whoever picks up P2's `odds_horizon_bucket` re-stamp todo apply this loader migration as part of
  that same change (per the todo's own instruction), or the operator add `depends_on`/`gate_on_depends` wiring from this
  specific P3 todo onto P2's re-stamp todo to stop repeat premature dispatch.

- **2026-08-09 (slot 16) — Arbitrage relocation, Session 1 of 2 (detection + persistence primitives)**. Shipped
  `features-service@5f10127d` (quickmerge, QG green): new `features_service/sports/arb/detector.py`
  (`detect_sports_arbitrage_opportunity` — real multi-venue leg-list key, honest `None` on <2 books / no-arb / same-
  operator-group legs via UAC `arb_legs_are_independent`) and `features_service/sports/arb/store.py`
  (`write_arb_opportunities` — append-only, tick-timestamped
  `sports_arb/by_date/day=.../tick=.../opportunities.parquet`, honest-absence on empty list, mirrors
  `cross_venue_arb_runner.write_arb_store`), plus `tests/sports/unit/arb/test_detector.py` and `test_store.py`. This
  directly answers slot-15's note above (dispatch the first todo with the operator-group guard applied AS PART of
  building it) — the new detector's guard covers the new series from day one. Adopted 2-session scoping (this plan's arb
  todo is one unit spanning relocate+preserve- history — checkbox intentionally stays open): **Session 1 (done, this
  entry)** = detection+persistence only, no MDPS deletion, no historical migration. **Session 2** = the two new todos
  above (live producer wiring, P0; historical 13-day reprocessing from raw ticks + old-adapter deletion, P1). No Session
  3 needed — slot-17's entry above already closed the arb-decay/alpha-gate recompute todo at a measured zero
  blast-radius, so the corrected-population check this todo's evidence mentions is that already-closed finding, not new
  work. `market-data-processing-service`'s `SportsArbitrageAdapter` is UNTOUCHED and still the only live producer —
  nothing downstream reads the new module yet, so this is additive/inert until Session 2's live-wiring todo lands.
