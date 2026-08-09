---
doc_type: plan
title:
  MVP scope tagging — a rules-derived MVP subset of the could-exist universe (instruments + features + strategies +
  models), toggled in data-status so missing-data only counts what's in-scope
summary:
  Build a rules-derived MVP subset of the instrument catalogue (instruments + features + strategies + models) and wire a
  toggle into data-status so missing-data counts only MVP in-scope cells.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-ui, instruments-service, unified-api-contracts]
scope: [engineer, admin]
tags: [mvp, catalogue, tagging, instruments, data-status, scope-filter, denominator]
related: []
created: 2026-06-08
parent_epic: instruments_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P1
estimate_class: design
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 3.6
last_updated: 2026-07-27
locked_by: live-defi-rollout
locked_since: 2026-06-08
supersedes:
superseded_by:
depends_on: []
source:
  [
    'operator 2026-06-08 ("we need a pre-migration MVP tag — tag the instrument catalogue with what''s MVP (data_types +
    base ccys per venue, instrument types, fixtures, leagues, sources); rules not hardcode; UAC/IS process rules into
    MVP; deployment UI/API toggle MVP in data-status, on-the-fly not manifest-baked; same for strategy/features/models
    catalogues so missing-data only looks at what can exist")',
    composes with CF-14 (IS-catalogue could-exist root) + proper_instrument_catalogue_lifecycle_rollup_2026_06_04.md,
  ]
drift_direction: advance-code
context_scope:
  [
    /codex/02-data/mvp-scope-canonical.md,
    /plans/epics/instruments_master.md,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/mvp_scope.py,
    deployment-api/deployment_api/routes/data_status/_coverage_scope.py,
    ml-service/ml_service/training/ml/config_schema.py,
  ]
---

# MVP scope tagging — the third denominator (all ⊇ could-exist ⊇ MVP)

> **The problem**: data-status today shows "missing" for any catalogued instrument with no data — including far-dated
> futures, non-MVP venues, and instrument types we've enumerated but don't yet intend to capture. That floods the
> denominator with things we don't EXPECT data for yet, so coverage reads falsely RED.
>
> **The fix**: a third denominator tier. **ALL catalogued ⊇ could-exist (genesis/launch/coverage, CF-14) ⊇ MVP
> (rules-filtered).** MVP is a **rules-derived SUBSET** of the could-exist universe — not a hardcoded list (we don't
> know future expiries) and not a manifest column we re-bake (the MVP definition is essentially a **global UAC config**
> that changes often). Data-status gets an **MVP toggle**: on → denominator = MVP cells only; off → the full could-exist
> universe. Same idea extends to the **features / strategy / model** registries, so every "what's missing" surface only
> counts what's in MVP scope.

## Core design

### 1. MVP is a predicate over the catalogue, computed on-the-fly (NOT a manifest column)

- **Rules live in UAC** (a global `mvp_scope` config) — the SSOT for "what is MVP". They are applied to the **instrument
  catalogue** (which holds the actual enumerated instruments + expiries, from
  `proper_instrument_catalogue_lifecycle_rollup_2026_06_04.md`) to produce the MVP subset at read time.
- **Grain = everything-or-nothing per `(asset_group, venue, instrument_type, data_type[, base_ccy])`** (+ sports
  `league`, prediction market-group, the `source`). **NOT** per-strike / per-expiry / per-turn — if a
  `(venue, instrument_type)` is MVP, ALL its catalogued expiries/strikes are in-scope (we don't filter the leaves, we
  don't know future expiries; the catalogue enumerates them, MVP includes the whole family).
- **On-the-fly, not baked**: `is_mvp(cell)` is evaluated against the UAC rule + the catalogue when data-status renders.
  Changing the MVP definition is a UAC config edit, not a manifest re-walk (avoids re-marking millions of rows for what
  is a config). Optional: a cached materialised `mvp_view` (catalogue × rules) refreshed with the catalogue scheduler,
  for performance — but the manifest itself stays MVP-agnostic.

### 2. The UAC `mvp_scope` rule shape (illustrative — finalise in Phase 1)

> **⚠️ [v12 NOTE 2026-06-30] — THIS BLOCK IS STALE/ILLUSTRATIVE ONLY; the LIVE authority is `mvp_scope.py`
> `MVP_SCOPE_CONFIG_VERSION == 12` (`mvp_scope.py:761`), NOT this YAML.** Do NOT execute against this block. Known drift
> vs the v10/v12 canonical scope: (a) tradfi lists `trades` — v10/v12 tradfi is **`ohlcv_1m`-ONLY** (no trades/tbbo;
> `TRADFI_TICK_DATA_WINDOWS=[]` suppresses tradfi tick); (b) instrument types are UPPERCASE here — the canonical
> manifest/UAC grain is **lowercase** (`perpetual`/`spot_pair`); (c) prediction omits **KALSHI** — v12 prediction =
> `{POLYMARKET, KALSHI}` (and the cefi perps `KALSHI-PERP`/`POLYMARKET-PERP` are a DISTINCT cefi surface). The Phase-1
> ✅ items below shipped the REAL typed config in UAC (`@d6e0775f`); this YAML is the original sketch.

```
mvp_scope:
  cefi:    { venues: [binance, bybit, okx, deribit, hyperliquid], instrument_types: [PERPETUAL, SPOT], data_types: [trades, book_snapshot_5, funding_rate], base_ccys: [BTC, ETH, SOL, USDT], sources: [tardis, <venue>] }
  defi:    { venues: [uniswap_v3, curve, ...], instrument_types: [DEX_PAIR, LST, LENDING], data_types: [dex_swaps, lst_rates, ...] }
  tradfi:  { venues: [CME], instrument_types: [FUTURE, OPTIONS_CHAIN], data_types: [trades, ohlcv_1m], underliers: [ES, NQ, VX] }
  sports:  { leagues: [NFL, NBA, EPL, ...], data_types: [odds, results] }
  prediction: { venues: [POLYMARKET], market_groups: [...], data_types: [prediction_cqg, ohlcv_*] }
```

A cell is MVP iff it matches its asset_group's rule on every declared axis. A `(venue, instrument_type)` not in the rule
→ catalogued + could-exist but **NOT MVP** → excluded from the MVP denominator (no false "missing").

### 3. Producer: UAC or IS resolves rules → MVP predicate/view

- `unified_api_contracts` owns the `mvp_scope` config + `is_mvp(asset_group, venue, instrument_type, data_type, **axes)`
  predicate (pure, rule-only).
- instruments-service applies the predicate over the catalogue → an **MVP-tagged catalogue view** (`mvp: bool` column in
  the served catalogue, or a `catalogue.filter(is_mvp)` endpoint). This is the only place the catalogue (real expiries)
  meets the rules (scope) — keeps the manifest clean.

### 4. Consumer: deployment-api/UI MVP toggle in data-status

- deployment-api computes coverage over the 4-state UNION (CF-14) but with a `scope=mvp|could_exist|all` param: MVP →
  denominator = `is_mvp` cells only. UI adds an **MVP toggle button** in data-status (default ON pre-launch, so the
  board reflects MVP readiness, not the full enumerated universe).
- Reuses the existing could-exist denominator machinery (the G3 union view) — MVP is just an extra predicate on the
  denominator, not a new data path.

### 5. The parallel MVP catalogues (same pattern, other registries)

| Registry               | SSOT today                                        | MVP tag                                                                                                                          |
| ---------------------- | ------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| **Instruments / data** | IS catalogue (CF-14)                              | `mvp_scope` rules above → data-status MVP toggle                                                                                 |
| **Features**           | delta_one `registry.py` (1,382 specs / 34 groups) | `mvp_features` — the subset of feature groups in MVP scope; features data-status only counts MVP feature × MVP instrument cells  |
| **Strategy**           | the archetype registry                            | `mvp_strategies` — the MVP archetypes (carry_staked_basis, arbitrage_price_dispersion); strategy-output coverage scoped to these |
| **Models (ML)**        | the model registry                                | `mvp_models` — the MVP model set; ml-output coverage scoped to these                                                             |

All four resolve from a UAC `mvp_scope` config (one SSOT, per-registry sections) and feed the same `scope=mvp` toggle in
deployment-api/UI so EVERY "what's missing" surface (data, features, strategies, models) only counts in-scope cells.

## Phases

- [x] ✅ [DESIGN] P1. **`mvp_scope` rule schema FINALISED in UAC** — **unified-api-contracts@d6e0775f**: typed frozen
      dataclasses per AG (CeFi/DeFi/TradFi/Sports/Prediction) + everything-or-nothing grain + `FeaturesModelsMvpStub`
      for the per-registry sections. Concrete MVP membership has conservative defaults +
      `# TODO(mvp-scope): operator sign-off` markers (config edit, no data touch — not a blocker).
- [x] ✅ [CODE] P1. **UAC `is_mvp(...)` predicate + `mvp_scope` config + tests** — **unified-api-contracts@d6e0775f**:
      `is_mvp(asset_group, venue, instrument_type, data_type, *, base_ccy, league, market_group, source)` pure
      rule-only; exported `from unified_api_contracts import is_mvp, MVP_SCOPE`; 56 tests (non-MVP venue excluded, all
      expiries of an MVP future via grain, absent/impossible→False, config-edit-changes-membership). QG exit 0.
- [x] ✅ [CODE] P1. **IS MVP-tagged catalogue view** — **instruments-service@b475ae8**: added `mvp` to
      `CATALOG_COLUMNS` + an `_add_mvp_column(df, asset_group)` helper applying UAC `is_mvp(...)` per catalogue row
      (venue / instrument_type / data_type / league + `underlying`→`base_ccy`), wired into `run_rollup` for all asset
      groups before promote (so `catalog.parquet` serves `mvp: bool`). Guard:
      `tests/unit/scripts/test_build_instrument_catalogue.py` (MVP cell→True, non-MVP→False, empty-frame bool schema).
- [x] ✅ [CODE] P1. **deployment-api `scope=mvp|could_exist|all`** on the data-status coverage endpoint —
      **deployment-api@3390c98**: new `scope` query param on `GET /api/data-status/venue-year-coverage` (default
      `could_exist`; `all` = full universe; `mvp` = `is_mvp(asset_group, venue, instrument_type, data_type)` filter over
      the SAME cell iteration — reuses the existing union machinery, no rebuild). Helpers extracted to
      `routes/data_status/_coverage_scope.py` (host module crossed the 900-line cap). Parity test
      `tests/unit/test_route_venue_year_coverage_scope.py` asserts denominator monotonicity `mvp ≤ could_exist ≤ all`.
- [x] ✅ [UI] P2. **deployment-ui MVP toggle** in data-status (default ON pre-launch) — `[UI]` + `pw:L2 ✓` + regression
      spec per the playwright gate. **DONE (2026-06-17 /autonomous) — deployment-ui@2279e57 | pw:L2 ✓ (217/217 smoke
      green, Node 22) | regression: tests/smoke/venue_year_coverage.spec.ts**: `VenueCoverageTable` gains a
      `mvp|could_exist|all` scope pill toggle (default **MVP**, accent-green active) wired to
      `getVenueYearCoverage(ags, scope)` → `?scope=` on the venue-year-coverage endpoint (re-fetches on toggle via
      the `load()` dep). Regression spec adds: scope pills render + MVP active by default; clicking a pill moves the
      active state (drives the re-fetch). tsc + eslint + full `tests/smoke/` chromium = green.
- [ ] [CODE] P2. **Features/strategy/model MVP sections** — extend `mvp_scope` + apply the same predicate to the feature
      registry / archetype registry / model registry; scope their data-status the same way. **PHASE-2+ (2026-06-17
      /autonomous assessment) — NOT shipped, prerequisite genuinely absent (not a deadline defer):** (1) the
      `mvp_scope.py` `features`/`strategy`/`models` entries are `FeaturesModelsMvpStub` placeholders **by design**
      ("Phase 2+; consumers MUST NOT read these stubs"); (2) **no consumer exists** — there is no
      features/strategy/model data-status coverage endpoint to filter (the `scope=mvp` filter is instruments-only), so
      populating typed rules now = dead config the Phase-2 consumer must reconcile; (3) **features membership is an
      operator policy call** (which feature_groups go live). **(4) CORRECTED (2026-07-27, operator ruling —
      `june_2026_vintage_audit_findings_2026_07_27.md` §5-RESOLVED item 29): the "models has no stable `model_id` MVP
      taxonomy → BLOCKED-OPERATOR-DECISION" framing is STALE.** A stable, already-versioned `model_id` scheme ALREADY
      EXISTS — `generate_model_id`/`parse_model_id` in `ml-service/ml_service/training/ml/config_schema.py`:
      `{ASSET_GROUP}_{ASSET}_{TARGET_TYPE}_{MODEL_TYPE}_{TIMEFRAME}_V{N}` (verified live in the repo 2026-07-27),
      genuinely unique/stable over time by construction. The identity-axes question is RESOLVED — this is now an
      implementation task, not an open operator decision. Split for the Phase-2 owner: P2a
      `FeaturesMvpRule`+`StrategiesMvpRule` (`features_service` registry / 2 archetypes) land WITH their data-status
      consumer — dispatched verbatim into `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md` (draft); P2b
      `ModelsMvpRule` is now a scoped implementation task tracked in the new todo immediately below, not operator-gated.
- [x] ✅ [IMPLEMENT] P2. **P2b — wire `ModelsMvpRule` against the existing `generate_model_id`/`parse_model_id`
      scheme.** — **DONE 2026-07-28 — unified-api-contracts@0fb9821b**: `ModelsMvpRule` added (its own leaf module
      `_mvp_scope_models.py` — keeps `_mvp_scope_rules.py` under the 900-line QG file-size cap), replacing the `models`
      `FeaturesModelsMvpStub` placeholder in `MVP_SCOPE`. Derives MVP membership from the
      `{ASSET_GROUP}_{ASSET}_{TARGET_TYPE}_{MODEL_TYPE}_{TIMEFRAME}_V{N}` identity axes already produced by
      `generate_model_id`/`parse_model_id` (`ml-service/ml_service/training/ml/config_schema.py`) — new `is_model_mvp()`
      predicate matches on those same decomposed identity components (asset_group, asset, target_type, model_type,
      timeframe). **Correction to this todo's original text**: `FeaturesMvpRule`/`StrategiesMvpRule` (P2a,
      `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md`) had NOT actually landed yet when this todo was picked
      up (`mvp_scope.py` still only had `FeaturesModelsMvpStub` for both `features`/`strategy`) — so `ModelsMvpRule` was
      built mirroring the pattern of the EXISTING per-asset_group rules (`CeFiMvpRule`/ `TradFiMvpRule`/…) instead, plus
      UAC's own "T4 service depends on UAC, never the reverse" tier rule (UAC cannot import `parse_model_id` from
      ml-service — callers parse a raw `model_id` locally and pass the decomposed components in, mirroring how
      `is_mvp()` takes plain args rather than an `InstrumentCatalogEntry`). Ships with a **conservative EMPTY default**
      (every axis frozenset empty — `is_model_mvp` returns `False` for every model_id today): there is no existing
      ml-service model-OUTPUT tracking/manifest surface to derive an objective default from (unlike DeFi's v13
      "everything we currently produce" derivation), and concrete membership is a genuine Phase-3 operator-policy call,
      not part of this identity-axis wiring. 19 new/updated unit tests: conservative- default proof, per-axis
      positive/negative matching (asset_group/target_type/model_type/assets/timeframes incl. the unbound-timeframe
      convention), a `generate_model_id`/`parse_model_id`-shaped round-trip, and a rule-mechanism
      `mvp ≤ could_exist ≤ all` monotonicity proof (rule-narrowing can only shrink the MVP subset of a fixed candidate
      universe, never grow it — mirrors `deployment-api@3390c98`'s `test_route_venue_year_coverage_scope.py` pattern).
      `MVP_SCOPE_CONFIG_VERSION` 20→21. **The data-status coverage CONSUMER is NOT part of this todo** — split into the
      new P2b-2 todo below (genuine design gap, not guessed at under time pressure).
- **[IMPLEMENT] P2. EXTRACTED 2026-08-09 → `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md`.** P2b-2 — models
  data-status coverage consumer — the design gap this item was previously blocked on (what "could exist" means for
  models; where trained-model identities get recorded) is resolved per the round5-cross-cutting-audit 2026-08-08 note
  above (`TrainingGridConfig` = could-exist bound; `ModelRegistry.list_models()` = live write path — narrows to ordinary
  wiring). See the batch doc for the full scoped todo; do not duplicate-dispatch from here.
- **[DATA] P2. EXTRACTED 2026-08-09 → `cross_cutting_satellite_ao_dispatch_batch8_2026_08_09.md`.** **Verify**: with
  MVP ON, data-status shows ~100% for captured MVP cells and does NOT count non-MVP catalogued instruments as
  missing; with MVP OFF, the full could-exist universe is shown (the gap is honest, not hidden) — re-confirm
  consolidator freshness first, then run the real-DATA verify. See the batch doc for the full scoped todo; do not
  duplicate-dispatch from here.

## Config versioning (config_version) — per-config, metadata-not-path-axis

> **MIGRATED FROM:** `migration_verification_orphan_safety_2026_06_10.md` § B (config_version design todo, audit §B3) —
> folded here because this is the first config-as-data surface (`MVP_SCOPE` + the parallel leagues / prediction-markets
> configs).

**The gap (audit §B3)**: there is no concept of config versioning distinct from code/semver today. Features have
`formula_version` (a _formula_ version, baked into the GCS partition key), but **pure config** — which families are MVP,
which leagues, which market-groups — has no independent version.

- **Config change ≠ code change.** Changing `MVP_SCOPE` (e.g. adding a venue to MVP) is **data, not logic** — it must
  **NOT** force a repo semver bump.
- **But it must be TRACKED** so coverage history is interpretable: "coverage dropped because we ADDED scope, not because
  data regressed." Without a version stamp, a scope expansion is indistinguishable from a data regression in the
  coverage timeline.
- **Mechanism**: a monotonic `config_version` integer **+** a `config_content_hash` string stamped on the `MVP_SCOPE`
  config (and on the sports-leagues + prediction-markets configs), surfaced in the manifest / data-status response so a
  coverage delta attributes to a **scope change vs a data change**.
- **NO GCS partition key** — unlike `formula_version` (which IS a path axis), `config_version` is **metadata only**
  (manifest/response field), never a hive path segment. Changing the config does not re-bake a single object path.
- **DECISION (operator recommend, audit §B3 + Open-decision 3): PER-CONFIG**, not a single global int — one
  `config_version` each for `MVP_SCOPE`, leagues, and prediction-markets, because they change **independently** (a
  leagues edit must not bump the MVP_SCOPE version and falsely flag an MVP coverage delta).

- [x] ✅ [CODE] P1. **Add `config_version: int` + `config_content_hash: str` to each config module** — per-config
      monotonic `config_version` (int) + a stable `config_content_hash` (content-addressed) on the `MVP_SCOPE` config
      AND the sports-leagues + prediction-markets configs (per-config, NOT a single global int). Metadata only — no GCS
      partition key. **MVP_SCOPE — uac@47ed81a**: `MVP_SCOPE_CONFIG_VERSION` + `MVP_SCOPE_CONFIG_HASH` (deterministic,
      PYTHONHASHSEED-independent) + `ConfigDescriptor` + `mvp_scope_config_descriptor()`. **Leagues + prediction —
      uac@176f227**: extracted the generic primitives into `canonical/crosscutting/config_versioning.py`
      (`ConfigDescriptor` + `canonical_config_repr` (handles dataclasses/Pydantic/sets/dicts, sorted) +
      `compute_config_content_hash`; MVP_SCOPE refactored onto it, hash unchanged).
      `SPORTS_LEAGUES_CONFIG_VERSION/_HASH` + `sports_leagues_config_descriptor()` (hashes `LEAGUE_REGISTRY`) in
      `league_data.py`; `PREDICTION_MARKETS_CONFIG_VERSION/_HASH` + `prediction_markets_config_descriptor()` (hashes
      `PredictionMarketCategory` + `_DEFAULT_RULES`) in `prediction_mapping.py`. All exported at the package root; the 3
      hashes are independently distinct.
- [x] ✅ [CODE] P1. **Surface `config_version` + `config_content_hash` in the deployment-api data-status response** —
      **deployment-api@3390c98**: the venue-year-coverage response now carries a `config_versions` object
      `{mvp_scope, sports_leagues, prediction_markets}` each `{version, content_hash}`, sourced from the UAC
      `mvp_scope_config_descriptor()` / `sports_leagues_config_descriptor()` / `prediction_markets_config_descriptor()`
      SSOTs (uac@176f227) — so a coverage delta attributes to a scope-change (version/hash moved) vs a data-change
      (stable). Parity test asserts the surfaced triples match the UAC descriptors.
- [x] ✅ [CODE] P1. **Unit test: config_version is monotonic + the hash changes when the config changes** — version is a
      positive int + descriptor matches; `config_content_hash` changes iff the config content changes (and is stable
      across re-computation / set-reordering) — one test per config (MVP_SCOPE / leagues / prediction-markets).
      **MVP_SCOPE — uac@47ed81a**: `tests/unit/test_mvp_scope.py` (3 tests). **Leagues + prediction — uac@176f227**:
      `tests/unit/test_config_versioning.py` (shared-primitive determinism/order-independence + per-config public
      surface + hash-deterministic + hash-changes-iff-content + the 3-hashes-independent invariant; 12 tests). Full UAC
      QG green (217s); 155 config/schema unit tests pass.

## Open questions (operator)

1. **Rule home — UAC vs IS?** UAC (global config, IS applies it) keeps the rule SSOT with the contracts; IS owns the
   catalogue it's applied to. Recommend UAC-config + IS-applies. Confirm.
2. **On-the-fly vs cached `mvp_view`?** On-the-fly is simplest + always-fresh; a cached view helps if data-status
   renders over millions of cells. Recommend on-the-fly first, cache only if slow.
3. **Default toggle state** in data-status — ON (MVP-readiness view) pre-launch? Recommend ON.

## Composes with

CF-14 (could-exist root — MVP is its subset) · `proper_instrument_catalogue_lifecycle_rollup_2026_06_04.md` (the
catalogue MVP is filtered from) · `macro_micro_econ_data_capture_audit_2026_06_05.md` (capability vs backfill — MVP is
the "what we intend to capture for launch" cut) · the G3 deployment union view (the denominator machinery MVP refines) ·
`mtds_data_status_page_parity_2026_07_21.md` (2026-07-21 — extends this plan's `is_mvp`/`CoverageScope` toggle to MTDS,
which has no MVP wiring today, and precomputes the sports/prediction catalogue `mvp` column this plan left as a live
`df.apply` fallback — annotated here rather than duplicated as a new MVP-scope plan).

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — `locked_by: live-defi-rollout`; features MVP membership is an
  explicit operator policy call and the P2b-2 todo self-documents its own AO-ineligibility ('an open design call is not
  an AO-dispatchable todo').
- **context-scout 2026-08-01**: populated/refreshed context_scope (2 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) -- added the MVP-scope codex SSOT + the UAC/
  deployment-api/ml-service source paths behind the two still-open P2b-2/verify todos.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — re-confirms 2026-07-30. Of the 3 open todos: the parent
  "Features/strategy/model MVP sections" item and P2b-2 both resolve to the same explicit open design call (models
  could-exist scope + where trained-model identities get recorded — self-documented as needing a LOCAL/interactive
  design session first, not an AO todo). The real-DATA "Verify" todo (line ~215) looks closer to a bounded check
  (re-confirm consolidator freshness, run the parity verify) than a design call — flagged here as a possible
  MISCLASSIFIED_LIKELY_AO_ELIGIBLE candidate for a future pass, not reclassified this run since it shares the doc with
  genuinely operator-gated scope.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid -- flagged-but-deferred, not
  reclassified. Today's round5-cross-cutting-audit entry resolved the P2b-2 open design call ("both sub-questions have
  live precedent already... narrows to ordinary wiring, no design session needed first"), which on its face clears 2 of
  the 3 remaining open todos' judgment-call blockers. Held rather than flipped: `locked_by: live-defi-rollout` (set
  since creation, 2026-06-08) on a heavily-designed strategy/data-status architecture doc carries real risk if
  misjudged, and the doc's own multi-week history shows partial-unblocks handled by forking a slice out (P2a already
  dispatched separately via `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md`) rather than a whole-doc flip.
  Flagging as a promising candidate for a dedicated follow-up pass, not forcing it here.
- **context-scout 2026-08-09**: populated/refreshed context_scope (5 entries).
- **round9-cross-cutting-sweep 2026-08-09**: satellite-extracted the "Verify" `[DATA] P2` todo into
  `cross_cutting_satellite_ao_dispatch_batch8_2026_08_09.md` — the item flagged `MISCLASSIFIED_LIKELY_AO_ELIGIBLE` by
  the 2026-08-07/08-08 na-eligibility-audit passes but never previously extracted. Whole-doc RECLASSIFY not applied —
  `locked_by: live-defi-rollout` remains set (unrelated to this extraction; content edits/extractions are unaffected
  by the archival lock).
