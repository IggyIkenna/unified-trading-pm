---
doc_type: plan
title: COINBASE bare-name → COINBASE-SPOT migration (unblock Phase-3.5 gap-002 CODE task)
summary: |
  Prerequisite migration plan for `wsfeedconnector_phase35_gap_2026_07_06` § "COINBASE bare-name UAC removal +
  downstream migration". Removes bare `COINBASE` from CeFi-venue slots in UAC (`VENUES_BY_ASSET_GROUP["cefi"]`,
  `INSTRUMENT_TYPES_BY_VENUE`), re-keys the D2a Layer-1 `_CEFI_VENUE_FOLD` so `COINBASE-SPOT` stays canonical, and
  migrates ~30 downstream callers across MTDS + IS + execution-service + strategy-service + features-service +
  UTL + e2e-testing + system-integration-tests. Bare `COINBASE` is KEPT where it names the Coinbase-issued LST
  protocol (cbETH — DeFi namespace) or is metadata (`cex_listings`, `spot_mvp_filtered_venues` for coinbase-premium).
status: active
nature: refactor
asset_group: [cefi]
stage: [data]
repos:
  [
    unified-api-contracts,
    market-tick-data-service,
    instruments-service,
    execution-service,
    strategy-service,
    features-service,
    unified-trading-library,
    e2e-testing,
    system-integration-tests,
  ]
scope: [engineer]
tags: [naming-reconciliation, d2a, phase-3-5, coinbase, cefi-venue-canonicalisation, foundation-completion-gate]
related:
  [
    issues/wsfeedconnector_phase35_gap_2026_07_06.md,
    layer1_remeasure_and_certify_2026_07_06.md,
    foundation_gates_and_capture_to_100_2026_07_06.md,
    ../../codex/02-data/availability-manifest-and-data-status.md,
    ../../codex/02-data/honest-coverage-model.md,
    ../../codex/04-architecture/instruments-service-as-ssot-for-mtds.md,
  ]
created: 2026-07-06
last_updated: 2026-07-06
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 2
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
source:
  [
    issues/wsfeedconnector_phase35_gap_2026_07_06.md#L139-L164,
    unified-api-contracts/registry/venue_constants.py#L369-L377,
    instruments-service/scripts/check_enumeration_completeness.py#L158-L168,
  ]
---

# COINBASE bare-name → COINBASE-SPOT migration

> **Purpose**: unblock the P2 CODE task at `issues/wsfeedconnector_phase35_gap_2026_07_06.md:139` ("COINBASE bare-name
> UAC removal + downstream migration"), which currently carries **BLOCKED-BY-D2a** because the shipped D2a naming
> reconciliation (`uac@e76d874a`, 2026-07-06 18:26) REQUIRES bare `COINBASE` to REMAIN in `VENUES_BY_ASSET_GROUP`
> **so long as the Layer-1 `_CEFI_VENUE_FOLD` folds `COINBASE-SPOT → COINBASE`**. Flipping the fold direction and
> migrating the CeFi-venue callers to `COINBASE-SPOT` removes that constraint.

## Codex SSOTs (READ before executing any phase)

- `codex/02-data/availability-manifest-and-data-status.md` — 4-state `capture_status`, shard-atom identity across
  writer/manifest/status/gate/UI.
- `codex/02-data/honest-coverage-model.md` — two-layer coverage model; UAC EXPECTED grain vs writer-emitted grain vs
  Layer-1 fold reconciliation.
- `codex/04-architecture/instruments-service-as-ssot-for-mtds.md` — IS resolver contract for cefi venues.

## Context (why bare `COINBASE` is a legacy artefact)

- UAC declares three CeFi venue keys for the exchange: bare `COINBASE`, `COINBASE-SPOT`, `COINBASE-FUTURES`. Only
  `COINBASE-SPOT` and `COINBASE-FUTURES` are in the MVP `venues` frozenset (`unified_api_contracts/canonical/
  crosscutting/mvp_scope.py:396-397`); bare `COINBASE` is a pre-2026-06-23 shape retained ONLY because the Layer-1
  checker's `_CEFI_VENUE_FOLD` folds `COINBASE-SPOT → COINBASE` and the EXPECTED-side itype-gate is keyed at the
  post-fold grain.
- The Layer-1 fold direction is the mechanism the D2a fix (`venue_constants.py:369-377`) explicitly documents:
  bare `COINBASE` MUST have its own `INSTRUMENT_TYPES_BY_VENUE` key "or the itype-gate authority switch silently
  zeroes COINBASE's entire EXPECTED set". This plan flips the pattern so `COINBASE-SPOT` is the canonical grain on
  both sides, matching the current shape for `BINANCE-SPOT`, `KRAKEN-SPOT`, `BITFINEX-SPOT`, `BITGET-SPOT` (each
  keyed only by the suffixed form; not folded).

## Migration principle (KEEP vs MIGRATE decision rules)

Bare `COINBASE` has THREE distinct semantic namespaces in the codebase. The plan MIGRATES only namespace **(A)**.

| # | Semantic namespace | Rule | Rationale |
|---|-------------------|------|-----------|
| A | **CeFi trading venue** (routing/execution/data ingestion for the Coinbase exchange spot market) | **MIGRATE → `COINBASE-SPOT`** | Align with post-2026-06-23 perp-gate pair shape (`COINBASE-SPOT ↔ COINBASE-FUTURES`). |
| B | **DeFi LST protocol** (Coinbase-issued cbETH liquid-staking token, chain=ETHEREUM) | **KEEP BARE** | Different namespace; the LST protocol is not the exchange. Registered under `LST` instrument-type, chain-suffixed venue `COINBASE-ETHEREUM` in the writer path. |
| C | **Display/metadata identifier** (which centralised exchanges list a given DeFi reward token) | **KEEP BARE** | Metadata for token listings; not a routing key. |

## Caller inventory (48 files touched; grouped by rule + repo)

### Group A1 — UAC registry (must land FIRST; 8 sites in 4 files)

| Site | Current | New | Notes |
|------|---------|-----|-------|
| `unified-api-contracts/unified_api_contracts/registry/venue_constants.py:377` | `"COINBASE": {"SPOT_PAIR"}` | **DELETE** entry | D2a critical — deletion is safe ONLY AFTER the fold flip below |
| `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:242` | `"COINBASE",` in `VENUES_BY_ASSET_GROUP["cefi"]` | **DELETE** | Legacy pre-2026-06-23 shape |
| `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:1113` | `"COINBASE": { "trades": ..., "book_snapshot_5": ... }` (venue → data-type start dates) | **DELETE**; keep only `COINBASE-SPOT` entry at L1117 | The two blocks are duplicates today |
| `unified-api-contracts/unified_api_contracts/registry/venue_mapping.py:154` | `"COINBASE": "coinbase"` in `venue_to_ccxt` | Rename key → `"COINBASE-SPOT": "coinbase"` | CCXT class routing |
| `unified-api-contracts/unified_api_contracts/registry/venue_mapping.py:181` | `"coinbase": "COINBASE-SPOT"` (tardis-endpoint reverse map) | **KEEP** — already canonical | No change |
| `unified-api-contracts/unified_api_contracts/registry/venue_mapping.py:818` | `("COINBASE", "SPOT_PAIR"): "coinbase"` in instrument_type_to_tardis | **DELETE** — L819 `("COINBASE-SPOT", "SPOT_PAIR"): "coinbase"` already handles the canonical case |
| `unified-api-contracts/unified_api_contracts/registry/venue_mapping.py:868` | `"COINBASE"` in `spot_mvp_filtered_venues` (coinbase-premium filter) | **Rename** → `"COINBASE-SPOT"` | Filter runs on canonical venue keys |
| `unified-api-contracts/unified_api_contracts/registry/venue_launch_dates.py:64` | `"COINBASE": "2014-12-08"` (GDAX/Coinbase Pro trading launch) | **Rename key** → `"COINBASE-SPOT"` | L236 `"COINBASE": "2022-08-24"` (cbETH LST launch) STAYS BARE (rule B) |

### Group A2 — D2a Layer-1 fold fix (must land WITH A1 in the same UAC PR)

**File**: `instruments-service/scripts/check_enumeration_completeness.py:163`

```python
# BEFORE (current — folds writer-side to bare)
_CEFI_VENUE_FOLD: dict[str, str] = {
    "OKX-SPOT": "OKX",
    "OKX-SWAP": "OKX",
    "OKX-FUTURES": "OKX",
    "COINBASE-SPOT": "COINBASE",   # ← DELETE this entry
    "BYBIT-FUTURES": "BYBIT",
    ...
}

# AFTER (COINBASE-SPOT is now canonical on BOTH sides — no fold needed)
_CEFI_VENUE_FOLD: dict[str, str] = {
    "OKX-SPOT": "OKX",
    "OKX-SWAP": "OKX",
    "OKX-FUTURES": "OKX",
    # COINBASE-SPOT stays canonical (post-migration) — no fold entry
    "BYBIT-FUTURES": "BYBIT",
    ...
}
```

**Gate**: after the fold fix, running Layer-1 enumeration against the current mtds writer output for COINBASE must
report the same EXPECTED cell count as the pre-migration run — verify with `bash scripts/quality-gates.sh` under IS
(the Layer-1 QG contract) + a spot-check on `COINBASE-SPOT` rows in a recent day's manifest.

### Group A3 — MTDS registry + config (5 sites)

| Site | Change |
|------|--------|
| `market-tick-data-service/market_tick_data_service/live/connectors/__init__.py:1` | Update comment header + confirm no bare `COINBASE` registration (registration is under `COINBASE-SPOT`) |
| `market-tick-data-service/configs/venue_data_types.yaml:112` | Rename YAML key `COINBASE:` → `COINBASE-SPOT:` |
| `market-tick-data-service/configs/expected_start_dates.yaml:55/127/248/258` | Rename each `COINBASE:` → `COINBASE-SPOT:` (4 sites in the same file — all reference the exchange, not LST) |
| `market-tick-data-service/market_tick_data_service/engine/orchestrator/venue_fetch.py` | Migrate bare-COINBASE branch → `COINBASE-SPOT` (2 sites) |
| `market-tick-data-service/market_tick_data_service/engine/orchestrator/symbol_rules.py` | Rename map key |
| `market-tick-data-service/market_tick_data_service/engine/orchestrator/preflight.py` | Migrate (2 sites) |
| `market-tick-data-service/market_tick_data_service/engine/shard_memory_profile.py` | Migrate (4 sites) |
| `market-tick-data-service/market_tick_data_service/cli/handlers/book_microstructure_handler.py` | Migrate |
| `market-tick-data-service/scripts/smoke_matrix.py:77` | `"COINBASE": "BTC-USD"` → `"COINBASE-SPOT": "BTC-USD"` |

Migration scripts + docstring references (do NOT touch — historical):

- `market-tick-data-service/market_tick_data_service/scripts/migrate_cefi_flat_to_v9_canonical.py` (docstring names
  bare `COINBASE` as the pre-canonical drift; keep for provenance)
- `market-tick-data-service/scripts/migrate_cefi_instrument_types.py` (one-off script; retain reference)

Tardis integration files that key by lowercase `"coinbase"` (canonical Tardis exchange id — NOT the venue key):

- `market-tick-data-service/market_tick_data_service/market_interface/adapters/cefi/tardis_shared.py` (4 sites)
- `market-tick-data-service/market_tick_data_service/market_interface/adapters/tradfi/tardis_adapter.py`
- `market-tick-data-service/market_tick_data_service/market_interface/adapters/tradfi/tardis_symbol_resolution.py`
- `market-tick-data-service/market_tick_data_service/live/connectors/tardis_machine_ws.py` (3 sites)

For these, **preserve** the lowercase `coinbase` Tardis id and the uppercase venue-key routing. Where these files
key by uppercase bare `COINBASE` in an ingestion path, migrate to `COINBASE-SPOT`; where they resolve `"coinbase"`
tardis-side, no change.

### Group A4 — instruments-service (2 sites, IS resolver)

| Site | Change |
|------|--------|
| `instruments-service/instruments_service/engine/orchestrator/venue_core.py:145` | **DELETE** `elif venue == "COINBASE": result.append("COINBASE-SPOT")` branch |
| `instruments-service/instruments_service/engine/orchestrator/venue_core.py:97-127, 317` | Update docstrings — remove "UAC keeps the bare `COINBASE` as an execution-context alias" language |
| `instruments-service/instruments_service/reference_data/factory.py` | Migrate the bare-COINBASE registration; ensure adapter registers under `COINBASE-SPOT` |
| `instruments-service/instruments_service/reference_data/adapters/cefi/ccxt_adapter.py` | Migrate |

### Group A5 — execution-service (12+ sites; the largest per-repo footprint)

**Compat-alias policy**: execution-service historically resolves both `COINBASE` and `COINBASE-SPOT` for user-facing
routes. Post-migration, the resolver-alias tables get **inverted** — canonical is `COINBASE-SPOT`; bare
`COINBASE` is retained ONLY as a backward-compat alias with a 1-plan deprecation window (this plan flips it; a
follow-on issue doc can retire it after downstream orchestrators/UIs are audited).

| Site | Change |
|------|--------|
| `execution-service/execution_service/instruments/registry.py:39` | `"COINBASE-SPOT": {"gcs_prefix": "COINBASE", ...}` — verify writer path still stamps `COINBASE-SPOT` post-A3; if so, change `gcs_prefix` → `"COINBASE-SPOT"` |
| `execution-service/execution_service/instruments/registry.py:178` | Keep `elif venue_code == "COINBASE": resolved_venue = "COINBASE-SPOT"` for **compat alias** |
| `execution-service/execution_service/instruments/registry.py:208` | `"COINBASE": ("COINBASE-SPOT", False)` — **KEEP as compat alias** |
| `execution-service/execution_service/instruments/registry.py:310` | `"COINBASE-SPOT": "COINBASE"` reverse map — flip to `"COINBASE-SPOT": "COINBASE-SPOT"` (identity) or remove |
| `execution-service/execution_service/instruments/utils.py:28` | `"COINBASE": "COINBASE-SPOT"` — **KEEP as compat alias** |
| `execution-service/execution_service/instruments/utils.py:238` | `elif venue_upper in ("COINBASE", "COINBASE-SPOT"): return "COINBASE"` — flip return to `"COINBASE-SPOT"` |
| `execution-service/execution_service/algo_library/algorithms/sor.py:27/29/34/153/169` | Docstring + demo data — update to `COINBASE-SPOT` (5 sites) |
| `execution-service/execution_service/custody/pre_trade_pinger.py:15` | Docstring — update to `COINBASE-SPOT` |
| `execution-service/execution_service/utils/nautilus_compatibility.py:17` | Nautilus Venue enum — leave the string `"COINBASE"` (nautilus schema constraint); document why |
| `execution-service/execution_service/services/execution_cost_estimator.py:32` | `"COINBASE": (Decimal("4"), Decimal("6"))` — rename to `"COINBASE-SPOT"` |
| `execution-service/execution_service/engine/backtest/preflight.py:90` | Update hint text |
| `execution-service/execution_service/trade_execution/factory.py:104` | `"coinbase": Venue.COINBASE` — leave (nautilus schema — see nautilus_compatibility.py note) |
| `execution-service/execution_service/trade_execution/venue_mapping.py` | 2 sites — migrate to `COINBASE-SPOT` (if venue-routing key) |
| `execution-service/execution_service/trade_execution/adapters/coinbase_ccxt.py` | Adapter file — verify registration key is `COINBASE-SPOT` |
| `execution-service/execution_service/results/serializer.py` | Migrate if venue-routing key |
| `execution-service/configs/expected_start_dates.yaml:55/126/233/243` | Rename YAML keys `COINBASE:` → `COINBASE-SPOT:` (4 sites; matches MTDS config change) |

### Group A6 — strategy-service (3 sites, mock data)

| Site | Change |
|------|--------|
| `strategy-service/scripts/risk/seed_mock_data.py:52` | Rename `"COINBASE"` → `"COINBASE-SPOT"` |
| `strategy-service/scripts/position/seed_mock_data.py:58` | Rename dict key |
| `strategy-service/scripts/position/seed_mock_data.py:190` | Rename venue string |

### Group A7 — features-service (1 site, mock data)

| Site | Change |
|------|--------|
| `features-service/scripts/delta_one/seed_mock_data.py:76` | Rename `"COINBASE"` → `"COINBASE-SPOT"` |

### Group A8 — UTL (2 sites, one config + one test scaffold)

| Site | Change |
|------|--------|
| `unified-trading-library/unified_trading_library/domain/data_source_mapping.py` | If it keys by venue for routing, migrate; if it's a display map, leave |
| `unified-trading-library/unified_trading_library/config_interface/instrument.py` | Check + migrate if venue-keyed |
| `unified-trading-library/unified_trading_library/post_trade/settler.py` | Check + migrate |

### Group A9 — e2e-testing + system-integration-tests (7+ sites)

| Site | Change |
|------|--------|
| `e2e-testing/scripts/build_smoke/run_live_verify_cefi.py:6` | Docstring — update `"COINBASE-*"` |
| `e2e-testing/scripts/cefi/run-batch-pipeline.sh:45/53` | Update venue-lists in comments + bash arrays |
| `e2e-testing/scripts/cefi/run-full-pipeline.sh:67` | Same |
| `e2e-testing/scripts/validation/validate_batch_live_smoke_matrix.py:580` | `"COINBASE": ["BTC-USD"]` → `"COINBASE-SPOT": ["BTC-USD"]` |
| `system-integration-tests/tests/unit/test_registry_alignment.py:125` | Rename in expected-set fixture |
| `system-integration-tests/tests/integration/test_instrument_alignment.py:198/202/204/248/423` | 5 sites — rename venue string in assertions |

### Group A10 — Tests (production migration triggers test fixture updates)

All `tests/**/test_*.py` files that grep for bare `COINBASE` as a venue-routing string get updated **in the same
PR as the corresponding production change**. Estimated ~30 test files across execution-service (~15),
market-tick-data-service (~5), unified-api-contracts (~5), instruments-service (~3), unified-trading-library (~2).
These are mechanical rename edits validated by `bash scripts/quality-gates.sh` in each affected repo.

### KEEP-BARE inventory (do NOT migrate — rule B or C)

| Site | Semantic | Reason |
|------|----------|--------|
| `unified-api-contracts/registry/expected_coverage.py:281` | `"COINBASE": list(_DEFI_LST_PAIRS)  # cbETH` | Rule B — DeFi LST namespace |
| `unified-api-contracts/registry/venue_launch_dates.py:236` | `"COINBASE": "2022-08-24"  # cbETH launch` | Rule B — LST launch date |
| `unified-api-contracts/internal/architecture_v2/restaking_rewards.py:657/663/676/718` | `cex_listings=[..., "COINBASE", ...]` | Rule C — display metadata |
| `market-tick-data-service/market_interface/adapters/defi/lst_coinbase_adapter.py` | DeFi LST adapter for cbETH | Rule B — writer stamps `COINBASE-ETHEREUM` (chain-suffixed); the internal string `"COINBASE"` is the protocol id |
| `execution-service/execution_service/utils/nautilus_compatibility.py:17` | Nautilus `Venue.COINBASE` enum | Third-party constraint — nautilus_trader schema |
| `execution-service/execution_service/trade_execution/factory.py:104` | `"coinbase": Venue.COINBASE` | Third-party constraint — nautilus_trader routing key |
| Tardis-integration adapters (lowercase `"coinbase"`) | Tardis exchange id | Tardis SSOT — not the venue key |

## Phase sequencing (repo-landing order + gates)

Each phase = one `quality-gates.sh`-green quickmerge per repo it touches. Phases MUST land in order: UAC first
(consumers depend on it), then IS + MTDS + execution + strategy + features + UTL + e2e in parallel-safe waves.

**Phase 1 — UAC + IS Layer-1 fold fix (single coordinated wave, LAND FIRST)**
- Todo A1: land UAC changes (8 sites in 4 files) — `unified-api-contracts` PR.
- Todo A2: land IS `_CEFI_VENUE_FOLD` fix (1 site in `check_enumeration_completeness.py`) — `instruments-service` PR.
- **Landing order within the wave**: A1 first (drops bare `COINBASE` from UAC registry), then A2 (removes the fold
  that would leave EXPECTED-side unattached). A worker running QG between the two would see a Layer-1 regression;
  land them in the same session.
- **Gate**: after both PRs land, run the smoke matrix against a recent day — `blocked-not-registered` cell count
  for `COINBASE` = 0; Layer-1 EXPECTED for CeFi COINBASE-SPOT = pre-migration EXPECTED count (regression: same
  number of instruments, keyed under `COINBASE-SPOT` now).

**Phase 2 — MTDS + IS resolver (parallel-safe with each other)**
- Todo A3: MTDS registry + config (9 sites in ~8 files) — `market-tick-data-service` PR.
- Todo A4: IS resolver (2 sites in 4 files) — `instruments-service` PR (separate from A2's fold fix).
- **Gate**: MTDS+IS QG green; a scheduled `register_all()` run continues to register `COINBASE-SPOT` (no bare
  regression). Manifest writer emits `COINBASE-SPOT` (already true today; verify via a spot-check on the newest
  manifest day).

**Phase 3 — execution-service (largest per-repo footprint; single PR)**
- Todo A5: execution-service registry + adapters + configs (16+ sites) — one PR to keep compat-alias
  edits atomic. Compat aliases (`COINBASE → COINBASE-SPOT`) retained; nautilus schema strings left alone.
- **Gate**: execution-service QG green; a paper-broker smoke run against `COINBASE-SPOT:SPOT:BTC-USD` and
  `COINBASE:SPOT:BTC-USD` (via alias) both succeed with the same resolved venue.

**Phase 4 — downstream tail (parallel-safe)**
- Todo A6: strategy-service seed mocks (3 sites).
- Todo A7: features-service seed mock (1 site).
- Todo A8: UTL check + migrate (3 sites — depending on greps).
- Todo A9: e2e-testing + SIT (7+ sites).
- **Gate**: each repo QG green; SIT smoke matrix reports the same total cell count with the venue-key labelled
  `COINBASE-SPOT` (was `COINBASE`).

**Phase 5 — cleanup + verification (optional, post-migration)**
- Todo A10: retire the execution-service compat alias (`COINBASE → COINBASE-SPOT`) after a 1-plan window — file
  as a follow-on issue doc if downstream orchestrators/UIs still reference bare `COINBASE`.

## Todos (executable — orchestrator will dispatch each `- [ ]` on a `data_engineering` role slot)

- [ ] [CODE] P1. **Phase 1 UAC changes (A1) — drop bare `COINBASE` from CeFi registry.** Edit
      `unified-api-contracts/unified_api_contracts/registry/venue_constants.py:377` (delete
      `"COINBASE": {"SPOT_PAIR"}` entry + its D2a rationale comment block L369-376),
      `market_data_categories.py:242` (delete bare `"COINBASE",` from `VENUES_BY_ASSET_GROUP["cefi"]`),
      `market_data_categories.py:1113` (delete the bare `"COINBASE": {...}` block; keep `"COINBASE-SPOT"` at
      L1117), `venue_mapping.py:154/818/868` (per the A1 table), `venue_launch_dates.py:64` (rename to
      `COINBASE-SPOT`; leave L236 cbETH bare). Ship via `quickmerge --agent --files` in unified-api-contracts.
      Gate: `bash scripts/quality-gates.sh` green in unified-api-contracts (repo:
      unified-api-contracts).
- [ ] [CODE] P1. **Phase 1 IS Layer-1 fold fix (A2) — drop `COINBASE-SPOT → COINBASE` fold entry.** Edit
      `instruments-service/scripts/check_enumeration_completeness.py:163` — delete the
      `"COINBASE-SPOT": "COINBASE",` line from `_CEFI_VENUE_FOLD`. Ship in the SAME session as A1 to keep Layer-1
      green (a run between A1 and A2 would show a false COINBASE hole). Gate: `bash scripts/quality-gates.sh`
      green in instruments-service (repo: instruments-service).
- [ ] [CODE] P1. **Phase 2 MTDS registry + configs (A3) — migrate ~9 sites to `COINBASE-SPOT`.** Files listed
      in the A3 table (venue_fetch.py, symbol_rules.py, preflight.py, shard_memory_profile.py, smoke_matrix.py,
      book_microstructure_handler.py, connectors/__init__.py comment + configs/venue_data_types.yaml +
      configs/expected_start_dates.yaml at 4 sites). Preserve lowercase `"coinbase"` Tardis-id strings.
      Gate: MTDS QG green; `register_all()` emits `COINBASE-SPOT` and no bare `COINBASE` key; smoke-matrix
      resolver returns `COINBASE-SPOT` for the coinbase spot cell (repo: market-tick-data-service).
- [ ] [CODE] P1. **Phase 2 IS resolver removal (A4) — drop bare-COINBASE branch in `venue_core.py`.** Delete the
      `elif venue == "COINBASE": result.append("COINBASE-SPOT")` branch in
      `instruments-service/instruments_service/engine/orchestrator/venue_core.py:145`; update the docstring at
      L97-127 + L317 to remove the "bare COINBASE as execution-context alias" language. Verify
      `reference_data/factory.py` + `adapters/cefi/ccxt_adapter.py` register under `COINBASE-SPOT`. Gate: IS QG
      green; IS integration test that fetches for `COINBASE-SPOT` returns the same instrument set as it did
      pre-migration for bare `COINBASE` (repo: instruments-service).
- [ ] [CODE] P1. **Phase 3 execution-service migration (A5) — largest per-repo change; single PR.** Edits per
      the A5 table (16+ sites across registry.py, utils.py, sor.py, pre_trade_pinger.py,
      execution_cost_estimator.py, trade_execution/venue_mapping.py, backtest/preflight.py,
      trade_execution/adapters/coinbase_ccxt.py, results/serializer.py, configs/expected_start_dates.yaml).
      Retain compat aliases (`COINBASE → COINBASE-SPOT`) in registry.py L178/L208 + utils.py L28; leave nautilus
      Venue.COINBASE + factory.py L104 lowercase `"coinbase"` alone (third-party schema). Update all
      `tests/trade_execution/unit/test_*.py` fixtures that key on `COINBASE:SPOT:...` to `COINBASE-SPOT:SPOT:...`
      in the same PR. Gate: execution-service QG green; a paper-broker smoke round-trip using
      `COINBASE-SPOT:SPOT:BTC-USD` resolves + a legacy `COINBASE:SPOT:BTC-USD` also resolves via alias (repo:
      execution-service).
- [ ] [CODE] P2. **Phase 4 strategy-service seed mocks (A6).** Rename `"COINBASE"` → `"COINBASE-SPOT"` at
      `scripts/risk/seed_mock_data.py:52`, `scripts/position/seed_mock_data.py:58`, and
      `scripts/position/seed_mock_data.py:190`. Gate: strategy-service QG green (repo: strategy-service).
- [ ] [CODE] P2. **Phase 4 features-service seed mock (A7).** Rename at
      `scripts/delta_one/seed_mock_data.py:76`. Gate: features-service QG green (repo: features-service).
- [ ] [CODE] P2. **Phase 4 UTL audit + migrate (A8).** Grep
      `unified_trading_library/{domain/data_source_mapping.py,config_interface/instrument.py,post_trade/settler.py}`
      for bare `COINBASE`; migrate each site where the string is a venue-routing key; leave display strings.
      Gate: UTL QG green; UTL public API for venue routing accepts `COINBASE-SPOT` (repo: unified-trading-library).
- [ ] [CODE] P2. **Phase 4 e2e-testing + SIT (A9).** Update per the A9 table
      (validate_batch_live_smoke_matrix.py:580, run_live_verify_cefi.py:6, run-batch-pipeline.sh + run-full-
      pipeline.sh venue-lists, test_registry_alignment.py:125, test_instrument_alignment.py 5 sites). Gate: SIT
      + e2e QG green (repo: e2e-testing, system-integration-tests).
- [ ] [PLAN] P3. **Phase 5 cleanup follow-on (A10).** After all above land + one full smoke-matrix run confirms
      the `blocked-not-registered` count for bare `COINBASE` is 0, file a follow-on issue doc
      (`plans/active/issues/coinbase_compat_alias_retirement_<date>.md`) proposing to retire the
      execution-service `COINBASE → COINBASE-SPOT` alias after auditing that no external caller (deployment-UI,
      client dashboards, external partners) still references bare `COINBASE`. Gate: issue doc filed with a
      concrete audit checklist (repo: unified-trading-pm plan doc).

## Acceptance gates (whole-plan verification)

1. **UAC**: `grep -rn '\bCOINBASE\b' unified-api-contracts/unified_api_contracts/registry/` returns hits ONLY at
   the DeFi LST callsites (`expected_coverage.py:281`, `venue_launch_dates.py:236`) + the `_DEFI_LST_PAIRS` /
   `restaking_rewards.py` metadata + the venue_mapping.py:181 tardis reverse map. Zero hits in `venue_constants.py`.
2. **Smoke matrix**: `bash scripts/validate_batch_live_smoke_matrix.sh` (or equivalent) run against a recent day
   shows `blocked-not-registered` count for `COINBASE` = 0; total cefi `blocked-not-registered` drops by ~13
   cells (per the parent issue doc's projection L588-591).
3. **Layer-1 QG**: `bash scripts/quality-gates.sh` green in instruments-service; the `check_enumeration_completeness`
   run does NOT flag a missing COINBASE EXPECTED set.
4. **Execution smoke**: an execution smoke test on `COINBASE-SPOT:SPOT:BTC-USD` succeeds; a compat-alias smoke on
   `COINBASE:SPOT:BTC-USD` also succeeds (until Phase 5 retirement).
5. **All 9 repos QG green** — Phase 1-4 shipped, each repo's tree at a green `.qg_last_passed_sha` sentinel.

## Progress Log

<!-- Append newest entries at the top: `- **YYYY-MM-DD** — <what landed> (<repo>@<sha> / evidence).` -->

- **2026-07-06** — **Plan drafted** by slot-4 (data_engineering). Enumerated 48 bare-`COINBASE` callsites across
  9 repos via `rg -n '\bCOINBASE\b' | rg -v 'COINBASE-(SPOT|FUTURES|BASE|USD)'` (excluding third-party
  substrings). Categorised into 3 semantic namespaces: (A) CeFi venue → MIGRATE to `COINBASE-SPOT`;
  (B) DeFi LST protocol (cbETH) → KEEP; (C) display/metadata (cex_listings, spot_mvp_filtered_venues) →
  KEEP. Proposed D2a Layer-1 fold fix: delete `_CEFI_VENUE_FOLD["COINBASE-SPOT"] = "COINBASE"` — this
  aligns COINBASE with the shape of BINANCE-SPOT / KRAKEN-SPOT / BITFINEX-SPOT (each keyed only by the
  suffixed form). Sequenced into 5 phases (UAC+IS-fold first as coordinated wave, then MTDS+IS-resolver in
  parallel, then execution-service alone, then downstream tail in parallel, then optional compat-alias
  retirement). This plan unblocks the P2 CODE task at
  `issues/wsfeedconnector_phase35_gap_2026_07_06.md:139` (COINBASE bare-name UAC removal).
