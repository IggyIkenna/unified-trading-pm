---
doc_type: plan
title:
  COINBASE bare-name migration to COINBASE-SPOT — unblock the wsfeedconnector_phase35_gap-015 UAC drop of bare COINBASE
summary: |
  Draft-of-record for migrating ~30 source callers of the bare `COINBASE` venue key to `COINBASE-SPOT` so
  `wsfeedconnector_phase35_gap-015` can safely remove bare `COINBASE` from `VENUES_BY_ASSET_GROUP["cefi"]` +
  `INSTRUMENT_TYPES_BY_VENUE` (D2a critical) without data-correctness regression. The migration is two-sided: (1)
  CeFi-VENUE callers (spot exchange context — 25+ source files across 10 repos) migrate to `COINBASE-SPOT`; (2) DeFi
  LST-ISSUER callers (cbETH context in `_defi_lst.py`, `defi/lst.py`, `venue_launch_dates.py` DeFi section) KEEP bare
  `COINBASE` since that key is a protocol/issuer name in DeFi world, not a venue reference. Also fixes the Layer-1
  `_CEFI_VENUE_FOLD["COINBASE-SPOT"] → "COINBASE"` entry in `check_enumeration_completeness.py` so it becomes a no-op
  (fold target = self) once bare `COINBASE` is no longer the EXPECTED-side canonical form. UAC drop is the LAST landing
  (all dependent services accept `COINBASE-SPOT` first).
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos:
  [
    unified-api-contracts,
    market-tick-data-service,
    market-data-processing-service,
    instruments-service,
    execution-service,
    strategy-service,
    features-service,
    deployment-service,
    unified-trading-api,
    unified-trading-library,
  ]
scope: [engineer]
tags:
  [
    coinbase,
    venue-canonicalisation,
    d2a-naming-reconciliation,
    perp-gate-pair,
    cefi-spot,
    multi-repo-migration,
    prerequisite-blocker,
  ]
related:
  [
    issues/wsfeedconnector_phase35_gap_2026_07_06.md,
    foundation_gates_and_capture_to_100_2026_07_06.md,
    instruments_completion_tracker_2026_07_06.md,
    ../../codex/02-data/availability-manifest-and-data-status.md,
    ../../codex/02-data/honest-coverage-model.md,
    ../../codex/02-data/honest-absence-downstream-handling.md,
  ]
created: 2026-07-06
last_updated: 2026-07-06
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 1.6
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  [
    issues/wsfeedconnector_phase35_gap_2026_07_06.md#L155,
    unified-api-contracts/unified_api_contracts/registry/venue_constants.py#L365-L379,
    instruments-service/scripts/check_enumeration_completeness.py#L158-L173,
  ]
---

# COINBASE bare-name migration to COINBASE-SPOT

> **🎯 SINGLE-JOB PLAN.** Unblock `wsfeedconnector_phase35_gap-015` (the "drop bare COINBASE from UAC" CODE task) by
> migrating every downstream caller from bare `COINBASE` → `COINBASE-SPOT` for the **CeFi-venue** semantic, while
> preserving bare `COINBASE` for the **DeFi LST-issuer** semantic (cbETH). Prerequisite for gap-015 landing.
>
> **Codex SSOTs (read first, then implement — plan↔codex drift is review-blocking)**:
>
> - `codex/02-data/availability-manifest-and-data-status.md` — the 4-state `capture_status`; the writer stamps
>   `COINBASE-SPOT`, the manifest key is `COINBASE-SPOT`; the shard atom is IDENTICAL across
>   writer/manifest/status/gate/UI. This plan is exactly the "atom-identity" repair — bare `COINBASE` in
>   `VENUES_BY_ASSET_GROUP["cefi"]` is the ONE remaining spot where the atom name diverges (writer says
>   `COINBASE-SPOT`, EXPECTED-side says `COINBASE`) and the Layer-1 `_CEFI_VENUE_FOLD` folds them back together.
> - `codex/02-data/honest-coverage-model.md` — the two-layer / two-view model. Layer-1 EXPECTED-vs-ENUMERATED
>   comparison lives in `check_enumeration_completeness.py`. Any change that touches the D2a itype-gate authority
>   switch MUST run the Layer-1 checker end-to-end and show COINBASE-SPOT's EXPECTED set is preserved.
> - `codex/02-data/honest-absence-downstream-handling.md` — no silent placeholders; the bare-COINBASE removal must
>   NOT cause a silent EXPECTED-side zero. The Layer-1 pre-flight in Task 001 is the guard.

## What this plan is (and is not)

**Is**: an ORDERED per-repo migration of the CeFi-venue meaning of bare `COINBASE` to `COINBASE-SPOT`, culminating in
the UAC drop of bare `COINBASE` from `VENUES_BY_ASSET_GROUP["cefi"]` + `INSTRUMENT_TYPES_BY_VENUE["COINBASE"]`. Also
patches the Layer-1 `_CEFI_VENUE_FOLD` entry that WOULD go stale once bare `COINBASE` is no longer the EXPECTED-side
canonical form.

**Is not**: a rename of the DeFi LST-issuer `COINBASE` key (that key names Coinbase-the-corporation as the ISSUER of
cbETH liquid staking token — like `LIDO` → stETH, `ROCKET_POOL` → rETH — and it's a different semantic role from the
CeFi spot exchange). DeFi LST callers KEEP bare `COINBASE`. If the collision proves confusing later, a rename to
`COINBASE-CBETH` or `COINBASE-ISSUER` can be a separate follow-on; not in scope here.

## Semantic split — the migration policy

For every source reference to bare `COINBASE`, classify the semantic role:

| Semantic role                                                     | Decision              | Rationale                                                                                                                                                                                                     |
| ----------------------------------------------------------------- | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CeFi-VENUE (Coinbase spot exchange — Tardis, coinbase-premium)    | migrate → `COINBASE-SPOT` | The perp-gate pair (`COINBASE-SPOT`↔`COINBASE-FUTURES`) is the canonical shape per `cefi_universe_capture_rule_2026_06_23`; bare `COINBASE` is a pre-2026-06-23 legacy tag.                                    |
| DeFi LST-ISSUER (Coinbase-corporate issuing cbETH)                | keep bare `COINBASE`  | This is a DeFi PROTOCOL name (issuer identity), not a venue key. Aligns with `LIDO` / `ROCKET_POOL` / `SWELL` shape (LST issuer names have no chain suffix).                                                   |
| Test callers                                                      | mirror the source they test | Migrate CeFi-venue tests to `COINBASE-SPOT`; DeFi LST tests keep bare `COINBASE`.                                                                                                                             |

## Enumerated call sites (source only — tests handled per-repo)

### CeFi-VENUE callers → migrate to `COINBASE-SPOT`

**UAC (unified-api-contracts)** — LAST to migrate (all dependents must accept `COINBASE-SPOT` first):

- `unified_api_contracts/registry/venue_constants.py:377` **[D2a CRITICAL]** —
  `"COINBASE": {"SPOT_PAIR"}` → DROP (already have `COINBASE_SPOT: {"SPOT_PAIR"}` at line 366). Must land IN THE SAME
  COMMIT as the `_CEFI_VENUE_FOLD` update.
- `unified_api_contracts/registry/market_data_categories.py:242` —
  `"COINBASE",` in `VENUES_BY_ASSET_GROUP["cefi"]` → DROP (already have `"COINBASE-SPOT"` at line 246).
- `unified_api_contracts/registry/market_data_categories.py:1113` —
  `"COINBASE": { … }` capability entry → DROP (already have `"COINBASE-SPOT"` block at 1117).
- `unified_api_contracts/registry/venue_mapping.py:154` — `"COINBASE": "coinbase"` (Tardis exchange-id) → rename to `"COINBASE-SPOT": "coinbase"`.
- `unified_api_contracts/registry/venue_mapping.py:818` — `("COINBASE", "SPOT_PAIR"): "coinbase"` → DROP (already have `("COINBASE-SPOT", "SPOT_PAIR"): "coinbase"` at 819).
- `unified_api_contracts/registry/venue_mapping.py:868` — `spot_mvp_filtered_venues` list `"COINBASE"` → rename to `"COINBASE-SPOT"`.
- `unified_api_contracts/registry/venue_launch_dates.py:64` — `"COINBASE": "2014-12-08"` (GDAX launch, CeFi) → rename to `"COINBASE-SPOT": "2014-12-08"`. **NB**: the file also declares `"COINBASE": "2022-08-24"` at line 236 in the DeFi LST section — that entry is a duplicate-key BUG masked by the CeFi entry being overwritten at import; migration exposes it. The line 236 entry KEEPS bare `COINBASE` (DeFi LST role); the CeFi entry moves to `COINBASE-SPOT`, eliminating the collision.
- `unified_api_contracts/registry/venue_instrument_config.py:38` — `"COINBASE": ["SPOT_PAIR"]` → rename to `"COINBASE-SPOT": ["SPOT_PAIR"]`.
- `unified_api_contracts/registry/venue_instrument_config.py:70` — `valid_quote_currencies` `"COINBASE": ["USD"]` → rename to `"COINBASE-SPOT": ["USD"]`.
- `unified_api_contracts/registry/venue_adapter_keys.py:104` — `"COINBASE": NO_ADAPTER_YET` (currently kept as execution-context alias) → rename to `"COINBASE-SPOT": NO_ADAPTER_YET`. UAC docstring update accompanies.
- `unified_api_contracts/registry/session_times.py:108` — `"COINBASE": _CRYPTO_SESSION` → rename to `"COINBASE-SPOT": _CRYPTO_SESSION`.
- `unified_api_contracts/canonical/coverage_starts.py:44` — `"COINBASE": date(2014, 12, 8)` (CeFi row alongside BINANCE/DERIBIT) → rename to `"COINBASE-SPOT": date(2014, 12, 8)`.
- `unified_api_contracts/registry/data_availability.py:349` — bare `"COINBASE"` in CeFi list → rename to `"COINBASE-SPOT"`.
- `unified_api_contracts/registry/representative_sample.py:53` — `"venue": "COINBASE"` → rename to `"venue": "COINBASE-SPOT"`.
- `unified_api_contracts/internal/architecture_v2/restaking_rewards.py:657,663,676,718` — `cex_listings=[…, "COINBASE", …]` (CeFi listing venues) → rename each to `"COINBASE-SPOT"`.
- `unified_api_contracts/internal/architecture_v2/backtest_scenarios.py:337` — `id="SCN-B4-CBETH-PEG-COINBASE"` → rename ID token to `SCN-B4-CBETH-PEG-COINBASE-SPOT`.
- `unified_api_contracts/canonical/crosscutting/execution_fidelity.py:37,76,108,234` — docstring/comment "COINBASE" references + the per-venue override key (per-venue-override table). The **override lookup key** must migrate to `COINBASE-SPOT`; docstring text can update to "COINBASE-SPOT" for consistency. VERIFY the trades-only override still fires for the perp-gate spot venue.
- `unified_api_contracts/canonical/crosscutting/mvp_scope.py:100,185,480,922,1062` — docstring references + the per-venue `venue_data_types` override entry (operator 2026-06-28 decision A — COINBASE = trades only). The **override lookup key** must migrate to `COINBASE-SPOT`; verify `is_mvp("cefi", "COINBASE-SPOT", "SPOT_PAIR", "trades", …)` still returns True.
- `unified_api_contracts/internal/reference/instrument_key.py:30` — `"COINBASE": "coinbase"` (venue → Tardis exchange-id mapping used by `InstrumentKey.parse_for_tardis`) → rename to `"COINBASE-SPOT": "coinbase"`. Verify `test_coverage_gaps_domain.py:562` still parses `COINBASE:SPOT:BTC-USD` correctly (or migrates to `COINBASE-SPOT:SPOT:BTC-USD`).
- `unified_api_contracts/external/nautilus/data_schemas.py:283` — `"coinbase": "COINBASE"` (Nautilus reverse map) → rename value to `"COINBASE-SPOT"`. Update `test_nautilus_data_schemas.py:143` and downstream callers.

**instruments-service** — resolver:

- `instruments_service/engine/orchestrator/venue_core.py:145` — the `elif venue == "COINBASE": result.append("COINBASE-SPOT")` branch. After migration, the caller no longer supplies bare `COINBASE` for CeFi → this branch becomes dead. Options: (a) DELETE the branch; (b) keep as backwards-compat safety, adding a deprecation comment. **Recommend (a) DELETE** once callers migrated + smoke-matrix green; the fold in the Layer-1 checker also becomes a no-op.
- `instruments_service/scripts/check_enumeration_completeness.py:163` **[D2a fold]** —
  `"COINBASE-SPOT": "COINBASE"` → DROP the entry (fold target = self after UAC drop; leaving it would fold
  `COINBASE-SPOT` to a key that no longer exists).
- `instruments-service/scripts/reconcile_cefi_tardis_thirdkey_drift_2026_05_07.py:20,94` — comments only; docstring update to `COINBASE-SPOT` (already-shipped script; low-risk doc-only edit).
- `instruments-service/scripts/reconcile_corrupt_kebab_rows_lst_rates_oracle_prices_2026_05_16.py:45` — comment only; docstring update.

**execution-service**:

- `execution_service/instruments/registry.py:178` — `elif venue_code == "COINBASE": resolved_venue = "COINBASE-SPOT"` (currently converts). Options: (a) delete this branch (no bare COINBASE reaches this point after migration); (b) keep as backwards-compat guard. **Recommend (a) after downstream is clean**.
- `execution_service/instruments/utils.py:28` — `"COINBASE": "COINBASE-SPOT"` in the pre-canonicalisation lookup dict — delete or leave as no-op guard.
- `execution_service/instruments/utils.py:239` — `return "COINBASE"` (Nautilus-compat name). This one is FINE as-is (Nautilus uses one venue name for both spot + futures per `nautilus_compatibility.py:17`) — **KEEP** but rename local matching condition to `("COINBASE", "COINBASE-SPOT")` and drop bare.
- `execution_service/trade_execution/factory.py:104` — `"coinbase": Venue.COINBASE` (Nautilus `Venue` enum key). NautilusTrader's own `Venue.COINBASE` enum stays as-is (external library); this line stays too. **KEEP AS-IS**.
- `execution_service/algo_library/algorithms/sor.py:27,29,34,153,169` — docstring/example venue strings. Docstring update to `COINBASE-SPOT`; dictionary keys in the doctest example update to `COINBASE-SPOT`.
- `execution_service/custody/pre_trade_pinger.py:15` — comment listing CeFi venues → rename `COINBASE` to `COINBASE-SPOT`.
- `execution_service/engine/backtest/preflight.py:90` — `"Nautilus backtest only supports: BINANCE, BYBIT, COINBASE, DERIBIT, OKX"` message string. This is the NautilusTrader external-venue name (per factory.py) — **KEEP AS-IS** but flag with a comment noting it's the Nautilus enum name, not our canonical UAC key.
- `execution_service/utils/nautilus_compatibility.py:17` — `"COINBASE"` in `nautilus_venue_map` (both COINBASE + COINBASE-SPOT map to Nautilus "COINBASE"). **KEEP AS-IS** (Nautilus external-lib compat).
- `execution_service/services/execution_cost_estimator.py:32` — `"COINBASE": (Decimal("4"), Decimal("6"))` fee tuple → rename to `"COINBASE-SPOT"`.
- `execution-service/docs/ROUTING_MATRIX.md:18` — doc string → rename `COINBASE` to `COINBASE-SPOT`.

**strategy-service**:

- `scripts/risk/seed_mock_data.py:52` — `"COINBASE"` in mock venue list → rename to `"COINBASE-SPOT"`.
- `scripts/position/seed_mock_data.py:58` — `"COINBASE": ["BTC-USD", "ETH-USD"]` → rename key to `"COINBASE-SPOT"`.
- `scripts/position/seed_mock_data.py:190` — `"COINBASE"` in venue list → rename to `"COINBASE-SPOT"`.

**features-service**:

- `scripts/delta_one/seed_mock_data.py:76` — `"COINBASE"` → rename to `"COINBASE-SPOT"`.

**market-tick-data-service**:

- `scripts/smoke_matrix.py:77` — `"COINBASE": "BTC-USD"` (sample-instrument map) → rename to `"COINBASE-SPOT": "BTC-USD"`.
- `market_tick_data_service/scripts/migrate_cefi_flat_to_v9_canonical.py:38,75` — comment + docstring only; update to reflect `COINBASE-SPOT` as canonical.
- `configs/venue_data_types.yaml:112` — `COINBASE:` YAML key → rename to `COINBASE-SPOT:`.
- `configs/expected_start_dates.yaml:55` — `COINBASE: "2019-03-30"` → rename to `COINBASE-SPOT: "2019-03-30"`.
- `docs/*` — deployment guides + audit doc; rename venue examples where the example refers to a spot-context capture (KEEP examples that show the perp-gate pair intact).

**market-data-processing-service**:

- `market_data_processing_service/engine/mock_data_provider.py:51` — `"COINBASE"` → rename to `"COINBASE-SPOT"`.
- `scripts/seed_mock_data.py:84` — `"COINBASE"` → rename to `"COINBASE-SPOT"`.
- `docs/DEPLOYMENT_GUIDE_FEMI.md:111` + `README.md:55` — doc examples → rename to `COINBASE-SPOT` (or add a footnote noting COINBASE = shorthand for COINBASE-SPOT).

**deployment-service** (docstrings only — no runtime dispatch key):

- `deployment_service/deployment/worker_manager.py:58` — docstring example `"COINBASE needs 256GB RAM"` → update to `COINBASE-SPOT`.
- `deployment_service/deployment/orchestrator.py:158` — docstring example → update to `COINBASE-SPOT`.
- `deployment_service/calculators/shard_distribution.py` + tests + `tools/check_ml_dependencies_by_mode.py` — verify each site is a CeFi-context reference; migrate accordingly.

**unified-trading-api**:

- `unified_trading_api/services/batch_candles.py:67` — `"COINBASE"` in venue list (CeFi context) → rename to `"COINBASE-SPOT"`.

**unified-trading-library**:

- `unified_trading_library/post_trade/settler.py:52` — `"COINBASE": Decimal("0.006")` (0.60% CeFi spot fee schedule) → rename to `"COINBASE-SPOT": Decimal("0.006")`.
- `unified_trading_library/config_interface/instrument.py` — verify + migrate CeFi context references.

### DeFi LST-ISSUER callers → KEEP bare `COINBASE` (do NOT migrate)

- `unified_api_contracts/registry/capability_declarations/_defi_lst.py:69` — `"COINBASE": ("cbETH",)`. **KEEP** — this is the LST-issuer role.
- `unified_api_contracts/registry/expected_coverage.py:281` — `"COINBASE": list(_DEFI_LST_PAIRS)  # cbETH`. **KEEP**.
- `unified_api_contracts/registry/venue_launch_dates.py:236` — `"COINBASE": "2022-08-24"  # Coinbase cbETH wrapped staked ETH launch` in the DeFi LST section. **KEEP**. (Once the CeFi entry at line 64 migrates to `COINBASE-SPOT`, the duplicate-key collision resolves and this entry stops being overwritten.)
- `unified_api_contracts/internal/domain/defi/lst.py:41` — `"cbETH": ("COINBASE", "ETH")`. **KEEP** — protocol-issuer tuple.
- `unified_api_contracts/external/coinbase/schemas.py:367-368` — docstring references DeFi LST role. **KEEP**.
- `market-tick-data-service/market_tick_data_service/market_interface/adapters/defi/lst_coinbase_adapter.py:33-34` — adapter docstring for the LST role. **KEEP**.

### Test callers (~70 files)

Test callers migrate to match the SOURCE they test. Since each repo's tests ship in the same PR as the source change,
they belong to the same per-repo todo below.

## Migration sequencing — CRITICAL ORDERING

The UAC drop of bare `COINBASE` is the LAST step. Every dependent must accept `COINBASE-SPOT` FIRST (so a transient
state where UAC is missing bare `COINBASE` but a service still looks it up cannot occur).

Order:

1. **P0** — Preflight: capture the Layer-1 EXPECTED baseline (before the migration): the exact set of
   `(venue, instrument_type, data_type, instrument, date)` cells the Layer-1 checker emits for
   `COINBASE`+`COINBASE-SPOT` today. This baseline is the ground truth to diff against post-migration.
2. **P1** — Dependent services migrate CeFi-venue callers to `COINBASE-SPOT` (accepting BOTH names in transition — no
   break):
   - execution-service (registry.py, utils.py, cost estimator, algorithms, docs)
   - instruments-service (venue_core.py — delete or keep as no-op)
   - strategy-service (seeds)
   - features-service (seed)
   - market-tick-data-service (smoke_matrix.py, configs YAML, scripts, docs)
   - market-data-processing-service (mock_data_provider, seed, docs)
   - deployment-service (docstrings + shard calc)
   - unified-trading-api (batch_candles.py)
   - unified-trading-library (settler.py + instrument.py)
3. **P1** — **Same commit** as UAC drop (below): patch `check_enumeration_completeness.py` `_CEFI_VENUE_FOLD` to drop
   the `"COINBASE-SPOT": "COINBASE"` entry (single, atomic; the fold and the UAC drop cannot land in different
   commits — a transient state where UAC drops the bare key but the fold still folds `COINBASE-SPOT` → `COINBASE`
   would zero the EXPECTED set for one CI run). Ship as one commit in unified-trading-pm (fold live in IS scripts
   dir — that PR is the same repo as UAC only if we co-land; since IS lives in a service repo, the ACTUAL atom is
   IS + UAC same-hour, guarded by the Layer-1 post-flight in step 5.
4. **P0** — UAC drop bare `COINBASE`: `venue_constants.py:377`, `market_data_categories.py:242` +
   `1113`, `venue_mapping.py:154+818`, `venue_launch_dates.py:64` (CeFi entry — leave line 236 DeFi entry intact),
   `venue_instrument_config.py:38+70`, `venue_adapter_keys.py:104`, `session_times.py:108`, `coverage_starts.py:44`,
   `data_availability.py:349`, `representative_sample.py:53`, `restaking_rewards.py:657+663+676+718`,
   `backtest_scenarios.py:337`, `execution_fidelity.py` override key, `mvp_scope.py` override key,
   `instrument_key.py:30`, `data_schemas.py:283`.
5. **P0** — Layer-1 post-flight: re-run
   `.venv/bin/python instruments-service/scripts/check_enumeration_completeness.py` (or the QG-invoked equivalent) and
   compare against the P0 baseline; EXPECTED set for the perp-gate pair (`COINBASE-SPOT` + `COINBASE-FUTURES`) must
   be IDENTICAL to pre-migration `COINBASE` + `COINBASE-FUTURES` EXPECTED sets. Any drift is a stop-ship (roll back
   UAC drop until root-caused). This is the D2a-authority-switch regression guard.
6. **P2** — Smoke-matrix re-measure: `blocked-not-registered` cells attributed to bare `COINBASE` (25 cells) drop to
   0. `COINBASE-SPOT` cells stay HONEST-BLOCKED-CREDENTIALS (bare Coinbase spot WSFeedConnector not yet built —
   tracked separately as gap-013 CODE task).
7. **P3** — gap-015 CODE task ships (drops bare COINBASE from UAC — see the follow-on issue-doc todo).

## Actionable todos (per-repo, ordered for orchestrator dispatch)

- [ ] [PRE-FLIGHT] P0. **Capture Layer-1 EXPECTED baseline for `COINBASE` + `COINBASE-SPOT` + `COINBASE-FUTURES`**
      before any migration commit. Run
      `.venv/bin/python instruments-service/scripts/check_enumeration_completeness.py --asset-group cefi > /tmp/coinbase_layer1_baseline.txt`
      (or the QG-invoked equivalent), then extract the specific
      `(venue, instrument_type, data_type, instrument, date)` rows for each of the 3 venue keys. Persist the diff to
      the plan's Progress Log so downstream can verify post-migration parity (repo: instruments-service,
      unified-trading-pm — evidence-log commit only). **Gate**: baseline captured + committed to plan Progress Log.
- [ ] [CODE] P1. **execution-service: migrate CeFi-venue call sites to `COINBASE-SPOT`** — per-file plan above (repo:
      execution-service). Include tests (`test_coinbase_adapter*`, `test_factory*`, `test_sor*`, etc.). Keep
      `Venue.COINBASE` Nautilus enum + `nautilus_compatibility.py` Nautilus name AS-IS. Add a
      `test_coinbase_spot_migration_backwards_compat.py` regression asserting `resolve_venue(bare "COINBASE")` STILL
      resolves via the utils.py fallback (defence-in-depth). **Gate**: `bash scripts/quality-gates.sh` green;
      per-service pytest for `tests/trade_execution/unit/` + `tests/unit/` passes; regression test added.
- [ ] [CODE] P1. **instruments-service: migrate `venue_core.py` resolver + Layer-1 checker + reconcile scripts to
      `COINBASE-SPOT`** (repo: instruments-service). The `elif venue == "COINBASE":` branch in `venue_core.py:145` is
      the RESOLVER that produces `COINBASE-SPOT` from bare `COINBASE` today; DELETE it (no upstream call sites
      remain after execution-service + strategy-service migrations). Also patch the reconcile scripts' docstrings
      (comment-only). Do NOT change `_CEFI_VENUE_FOLD` yet — that lands in the same commit as the UAC drop. **Gate**:
      QG green; regression test asserts `expand_cefi_tardis_endpoints(["COINBASE-SPOT"])` returns
      `["COINBASE-SPOT"]` and no bare `COINBASE` re-enters the pipeline.
- [ ] [CODE] P1. **strategy-service: migrate seed mock data** (repo: strategy-service). Files:
      `scripts/risk/seed_mock_data.py:52`, `scripts/position/seed_mock_data.py:58,190`, plus config-reloader tests
      (`tests/**/test_config_reloaders.py`) that key off the seed. **Gate**: QG green; unit tests for the mock
      seeders pass.
- [ ] [CODE] P1. **features-service: migrate seed mock data + cross-instrument tests** (repo: features-service).
      Files: `scripts/delta_one/seed_mock_data.py:76`, `tests/cross_instrument/**` (conftest + tests).
      **Gate**: QG green; cross-instrument test suite passes.
- [ ] [CODE] P1. **market-tick-data-service: migrate smoke_matrix, YAML configs, scripts, and docstrings** (repo:
      market-tick-data-service). Files: `scripts/smoke_matrix.py:77`, `configs/venue_data_types.yaml:112`,
      `configs/expected_start_dates.yaml:55`, `market_tick_data_service/scripts/migrate_cefi_flat_to_v9_canonical.py`
      (comment-only), `tests/unit/scripts/test_migrate_cefi_v2.py`,
      `tests/unit/scripts/test_validate_manifest_coverage.py`,
      `tests/unit/test_orchestrator_failure_classification.py`,
      `tests/unit/engine/test_sentinels_coverage.py`. Do NOT touch the `market_interface/adapters/defi/lst_coinbase_adapter.py`
      (DeFi LST-issuer role — KEEP bare `COINBASE`). **Gate**: QG green;
      `.venv/bin/python scripts/smoke_matrix.py` still emits the correct
      `(venue=COINBASE-SPOT, instrument=BTC-USD)` sample row.
- [ ] [CODE] P1. **market-data-processing-service: migrate mock data provider + seed + docs** (repo:
      market-data-processing-service). Files: `market_data_processing_service/engine/mock_data_provider.py:51`,
      `scripts/seed_mock_data.py:84`, `tests/unit/test_data_source.py`, `test_dependency_checker.py`,
      `test_fx_rate_adapter.py`, `test_orchestration_scanner.py`, `test_orchestration_scheduling.py`,
      `test_orchestration_workers.py`. **Gate**: QG green; mock-data orchestration tests pass.
- [ ] [CODE] P2. **deployment-service: migrate docstring examples + shard calc + budget tests** (repo:
      deployment-service). Files: `deployment_service/deployment/worker_manager.py:58` (docstring),
      `orchestrator.py:158` (docstring), `calculators/shard_distribution.py`,
      `tools/check_ml_dependencies_by_mode.py`, `tests/**` (budget + worker manager + data fixtures).
      **Gate**: QG green; shard-distribution + worker-manager tests pass.
- [ ] [CODE] P2. **unified-trading-api: migrate `batch_candles.py`** (repo: unified-trading-api). File:
      `unified_trading_api/services/batch_candles.py:67`. **Gate**: QG green.
- [ ] [CODE] P2. **unified-trading-library: migrate settler fee schedule + config_interface** (repo:
      unified-trading-library). Files: `unified_trading_library/post_trade/settler.py:52`,
      `unified_trading_library/config_interface/instrument.py`, plus tests
      (`tests/unit/test_api_key_reloader.py`, `test_domain_clients.py`, `test_emission_publisher.py`,
      `test_manifest_consolidator.py`). **Gate**: QG green; UTL post-trade tests pass.
- [ ] [CODE] P0. **UAC bare-COINBASE drop (co-lands with `_CEFI_VENUE_FOLD` patch)** — the CULMINATION step (repo:
      unified-api-contracts + instruments-service, TWO PRs same-day). UAC PR: drop `"COINBASE"` from
      `venue_constants.py:377`, `market_data_categories.py:242+1113`, `venue_mapping.py:154+818`,
      `venue_launch_dates.py:64` (CeFi entry only — line 236 DeFi entry stays), `venue_instrument_config.py:38+70`,
      `venue_adapter_keys.py:104`, `session_times.py:108`, `coverage_starts.py:44`, `data_availability.py:349`,
      `representative_sample.py:53`, `restaking_rewards.py:657+663+676+718`, `backtest_scenarios.py:337`,
      `execution_fidelity.py` override-key, `mvp_scope.py` override-key, `instrument_key.py:30`,
      `data_schemas.py:283`. IS PR: drop `_CEFI_VENUE_FOLD["COINBASE-SPOT"]` entry in
      `check_enumeration_completeness.py:163`. PRs must land within a 30-min window (IS first, then UAC) —
      cross-repo bundle. **Gate**: UAC pytest green; IS pytest green;
      `.venv/bin/python instruments-service/scripts/check_enumeration_completeness.py --asset-group cefi` shows
      COINBASE-SPOT EXPECTED set === pre-migration COINBASE EXPECTED set (baseline diff = 0 for perp-gate spot rows).
- [ ] [POST-FLIGHT] P0. **Layer-1 parity assertion + smoke-matrix drop** — re-run the Layer-1 checker + smoke_matrix
      end-to-end after the UAC drop lands. Assert: (a) `_CEFI_VENUE_FOLD` no longer has a `COINBASE-SPOT` entry;
      (b) EXPECTED-side comparison for `COINBASE-SPOT` matches the pre-migration `COINBASE` set row-for-row
      (baseline captured in preflight todo); (c) smoke-matrix `blocked-not-registered` count for bare `COINBASE`
      drops to 0 (was 25 cells = 5 instruments × 5 data_types-per the smoke_matrix); (d) `COINBASE-SPOT`
      `blocked-not-registered` count is unchanged (stays HONEST-BLOCKED — the WSFeedConnector build is separate,
      tracked as the Coinbase-spot WSFeedConnector item in the parent issue doc). Any drift => file a fix issue-doc
      + notify main. **Gate**: parity report committed to plan Progress Log with concrete row counts + diff = 0
      evidence.
- [ ] [UNBLOCK] P0. **Notify wsfeedconnector_phase35_gap-015 to proceed** — this plan's completion is the
      prerequisite for gap-015 (COINBASE bare-name UAC removal + downstream migration). Ping main + edit the
      parent issue doc `plans/active/issues/wsfeedconnector_phase35_gap_2026_07_06.md` to remove the
      BLOCKED-BY-D2a marker on the gap-015 todo and add a "PREREQ-DONE: coinbase_bare_name_migration_2026_07_06"
      cross-reference (repo: unified-trading-pm plan doc). **Gate**: gap-015 checkbox unblocked; the parent
      issue doc references this plan's completion.

## Progress Log

<!-- Append newest entries at the top: `- **YYYY-MM-DD** — <what landed> (<repo>@<sha> / evidence).` -->

- **2026-07-06** — **Plan filed** (slot-9 planning) as the prerequisite for
  `wsfeedconnector_phase35_gap-015` (COINBASE bare-name UAC drop). Grep enumerated 256 bare-`COINBASE` refs across
  ~100 files (30-ish source + ~70 tests). Semantic split: CeFi-venue callers → `COINBASE-SPOT`; DeFi LST-issuer
  callers keep bare `COINBASE`. Ordered per-repo todos with the D2a fold patch co-landing with the UAC drop
  (single 30-min IS+UAC bundle). Discovered a duplicate-key BUG in `venue_launch_dates.py` where the DeFi cbETH
  entry at line 236 silently overwrites the CeFi GDAX entry at line 64 (Python dict overwrites on import) — the
  migration exposes and fixes it (line 64 → `COINBASE-SPOT`, line 236 stays bare). Baseline capture is the P0
  pre-flight; parity assertion is the P0 post-flight. Estimate: refactor class × 4 baseline = 1.6 calibrated days
  (mechanical rename + regression re-run; the risk is the Layer-1 EXPECTED-set parity which is guarded by the
  pre/post-flight baseline diff).
