---
title:
  "MVP scope tagging — a rules-derived MVP subset of the could-exist universe (instruments + features + strategies +
  models), toggled in data-status so missing-data only counts what's in-scope"
created: 2026-06-08
parent_epic: instruments_master
assigned_vm: vm-cross-cutting
status: active
priority: P1
estimate_class: design
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 3.6
locked_by: live-defi-rollout
locked_since: 2026-06-08
source:
  - operator 2026-06-08 ("we need a pre-migration MVP tag — tag the instrument catalogue with what's MVP (data_types +
    base ccys per venue, instrument types, fixtures, leagues, sources); rules not hardcode; UAC/IS process rules into
    MVP; deployment UI/API toggle MVP in data-status, on-the-fly not manifest-baked; same for strategy/features/models
    catalogues so missing-data only looks at what can exist")
  - composes with CF-14 (IS-catalogue could-exist root) + proper_instrument_catalogue_lifecycle_rollup_2026_06_04.md
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
      `# TODO(mvp-scope): operator     sign-off` markers (config edit, no data touch — not a blocker).
- [x] ✅ [CODE] P1. **UAC `is_mvp(...)` predicate + `mvp_scope` config + tests** — **unified-api-contracts@d6e0775f**:
      `is_mvp(asset_group, venue, instrument_type, data_type, *, base_ccy, league, market_group, source)` pure
      rule-only; exported `from unified_api_contracts import is_mvp, MVP_SCOPE`; 56 tests (non-MVP venue excluded, all
      expiries of an MVP future via grain, absent/impossible→False, config-edit-changes-membership). QG exit 0.
- [ ] [CODE] P1. **IS MVP-tagged catalogue view** — apply `is_mvp` over the rolled-up catalogue; serve `mvp: bool` (or a
      filtered endpoint). On-the-fly; optional cached `mvp_view` refreshed with the catalogue scheduler.
- [ ] [CODE] P1. **deployment-api `scope=mvp|could_exist|all`** on the data-status coverage endpoint (denominator =
      `is_mvp` cells when mvp) — reuse the G3 union machinery.
- [ ] [UI] P2. **deployment-ui MVP toggle** in data-status (default ON pre-launch) — `[UI]` + `pw:L2 ✓` + regression
      spec per the playwright gate.
- [ ] [CODE] P2. **Features/strategy/model MVP sections** — extend `mvp_scope` + apply the same predicate to the feature
      registry / archetype registry / model registry; scope their data-status the same way.
- [ ] [DATA] P2. **Verify**: with MVP ON, data-status shows ~100% for captured MVP cells and does NOT count non-MVP
      catalogued instruments as missing; with MVP OFF, the full could-exist universe is shown (the gap is honest, not
      hidden).

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

- [~] [CODE] P1. **Add `config_version: int` + `config_content_hash: str` to each config module** — per-config monotonic
      `config_version` (int, bumped on every content change) + a stable `config_content_hash` (content-addressed) on the
      `MVP_SCOPE` config and on the sports-leagues + prediction-markets configs (per-config, NOT a single global int).
      Metadata only — no GCS partition key. **MVP_SCOPE DONE — uac@47ed81a**: `MVP_SCOPE_CONFIG_VERSION` +
      `MVP_SCOPE_CONFIG_HASH` (deterministic — sorted-frozenset serializer, PYTHONHASHSEED-independent) +
      `ConfigDescriptor` + `mvp_scope_config_descriptor()`, exported at the package root. **Pending: leagues +
      prediction-markets configs** (reuse the same `ConfigDescriptor` pattern — smaller follow-ons).
- [ ] [CODE] P1. **Surface `config_version` + `config_content_hash` in the deployment-api data-status response** — so a
      coverage delta attributes to a scope-change (config_version bumped) vs a data-change (config_version stable).
      Carry the per-config triple (config name, version, hash) alongside the `scope=mvp|could_exist|all` coverage
      payload.
- [~] [CODE] P1. **Unit test: config_version is monotonic + the hash changes when the config changes** — assert
      `config_version` only ever increases (never decreases/reused) and that `config_content_hash` changes iff the
      config content changes (and is stable across unrelated edits) — one such test per config (MVP_SCOPE / leagues /
      prediction-markets). **MVP_SCOPE DONE — uac@47ed81a**: `tests/unit/test_mvp_scope.py` (public surface + determinism
      + hash-changes-iff-content-changes, 3 tests). Leagues/prediction tests ride their config additions.

## Open questions (operator)

1. **Rule home — UAC vs IS?** UAC (global config, IS applies it) keeps the rule SSOT with the contracts; IS owns the
   catalogue it's applied to. Recommend UAC-config + IS-applies. Confirm.
2. **On-the-fly vs cached `mvp_view`?** On-the-fly is simplest + always-fresh; a cached view helps if data-status
   renders over millions of cells. Recommend on-the-fly first, cache only if slow.
3. **Default toggle state** in data-status — ON (MVP-readiness view) pre-launch? Recommend ON.

## Composes with

CF-14 (could-exist root — MVP is its subset) · `proper_instrument_catalogue_lifecycle_rollup_2026_06_04.md` (the
catalogue MVP is filtered from) · `macro_micro_econ_data_capture_audit_2026_06_05.md` (capability vs backfill — MVP is
the "what we intend to capture for launch" cut) · the G3 deployment union view (the denominator machinery MVP refines).
