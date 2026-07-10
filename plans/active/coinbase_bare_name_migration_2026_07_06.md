---
doc_type: plan
title: COINBASE bare-name UAC removal + downstream caller migration
summary: 'Migration plan for removing bare `COINBASE` from UAC''s cefi venue registries

  (`VENUES_BY_ASSET_GROUP["cefi"]`, `INSTRUMENT_TYPES_BY_VENUE`, etc.) and

  re-keying its 44 UAC + ~9 downstream cefi callers to `COINBASE-SPOT`

  (or KEEP-BARE where the reference is DeFi-LST context, i.e. bare `COINBASE`

  as the cbETH-issuer key). Prerequisite for

  `wsfeedconnector_phase35_gap_2026_07_06.md` gap-015 (the actual UAC removal

  step, blocked-by-D2a). Must NOT regress the D2a Layer-1 itype-gate authority

  switch — includes an explicit `_CEFI_VENUE_FOLD` re-anchor step.

  '
status: active
nature: design
asset_group: [cefi, cross-cutting]
stage: [data]
repos:
  [
    unified-api-contracts,
    instruments-service,
    market-tick-data-service,
    unified-trading-library,
    features-service,
    market-data-processing-service,
    deployment-api,
    deployment-service,
    execution-service,
  ]
scope: [engineer]
tags: [venue-canonicalisation, cefi, d2a-naming-reconciliation, layer1-checker, migration, phase-3-5, wsfeedconnector]
related:
  [
    issues/wsfeedconnector_phase35_gap_2026_07_06.md,
    ../../codex/02-data/availability-manifest-and-data-status.md,
    ../../codex/02-data/honest-coverage-model.md,
    ../../codex/02-data/defi-canonical-naming-ssot.md,
  ]
created: 2026-07-06
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.2
last_updated: 2026-06-27
locked_by: live-defi-rollout
locked_since: 2026-05-21
supersedes:
superseded_by:
depends_on: [wsfeedconnector_phase35_gap_2026_07_06]
source:
  [
    plans/active/issues/wsfeedconnector_phase35_gap_2026_07_06.md#L155-L164,
    unified-api-contracts/unified_api_contracts/registry/venue_constants.py#L365-L414,
    unified-api-contracts/unified_api_contracts/registry/market_data_categories.py#L232-L247,
    instruments-service/scripts/check_enumeration_completeness.py#L149-L199,
  ]
assigned_role: data_engineering
drift_direction: advance-code
sequential: true
---

# COINBASE bare-name UAC removal + downstream caller migration

> **STATUS: active.** Drafted per the operator-answered BLK-22e5f8a5 (2026-07-06). Dispatched for execution 2026-07-10
> per operator decision #3 in `plans/active/issues/instruments_remaining_work_audit_2026_07_10.md` ("flip
> `coinbase_bare_name_migration_2026_07_06.md` from `draft` to `active`, dispatch its full 7-step (S0-S7) plan now"):
> `assigned_vm: planning`, `status: active`. Executing S0-S7 in order below.

> **DOMAIN NOTE — bare `"COINBASE"` has TWO meanings in this workspace:**
>
> 1. **CeFi exchange** (Coinbase spot exchange) — the pre-D2a canonical cefi venue key. This is what gap-015 wants to
>    remove: it's LEGACY because `COINBASE-SPOT` is the canonical cefi spot venue now (post-2026-06-23 perp-gate pair
>    introduction; `COINBASE-SPOT` ↔ `COINBASE-FUTURES`).
> 2. **DeFi LST issuer** — Coinbase as the issuer of `cbETH` (the wrapped staked ETH token). This appears in the DeFi
>    capability declarations (`_defi_lst.py` `LST_VENUE_TO_TOKENS`, `internal/domain/defi/lst.py`
>    `LST_TOKEN_TO_PROTOCOL_ASSET`) and the MTDS LST adapter (`lst_coinbase_adapter.py`). This is NOT the same key; the
>    DeFi LST layer uses bare `COINBASE` as the PROTOCOL name (like `LIDO`, `ROCKETPOOL`).
>
> These callers MUST be handled differently: CeFi bare-COINBASE migrates to `COINBASE-SPOT`; DeFi bare-COINBASE (LST
> issuer) STAYS as bare `COINBASE`.

## 1. Context and prerequisite chain

- **Parent issue**: `plans/active/issues/wsfeedconnector_phase35_gap_2026_07_06.md` gap-015 (the actual UAC removal) is
  `BLOCKED-BY-D2a` (BLK-9d69f223 resolved by main 2026-07-06). Main's directive was: "Re-scope gap-015 to EXCLUDE the
  bare COINBASE removal entirely. Only proceed with parts of gap-015 that do not touch the bare COINBASE key. File a
  follow-on task for the bare COINBASE removal after the 25-caller migration plan is drafted and lands."
- **This plan is that migration plan.** It enumerates every downstream caller, proposes a target per caller, plans the
  `_CEFI_VENUE_FOLD` re-anchor so the D2a Layer-1 itype-gate authority switch does not silently zero `COINBASE`'s
  EXPECTED set, and sequences the multi-repo landings so no intermediate state is data-incorrect.
- **The D2a constraint (verbatim from `venue_constants.py:369-376`)**: bare `"COINBASE"` currently exists in
  `VENUES_BY_ASSET_GROUP["cefi"]` as the D2a-canonical EXPECTED lookup key. Removing it without inverting the
  `_CEFI_VENUE_FOLD` anchor to `COINBASE-SPOT` "silently zeroes COINBASE's entire EXPECTED set" — a data-correctness
  regression against every itype-gate Layer-1 audit that depends on the folded comparison.

## 2. Pre-audit — enumeration of every bare-COINBASE reference

**Total call sites (workspace-wide, excluding `.venv`, `.git`, `build`, archives, htmlcov)**: **~52 non-test/non-doc
source files** containing bare `COINBASE` (excluding the qualified `-SPOT` / `-FUTURES` suffixed forms). Break-down of
the actionable subset (44 UAC + 5 IS + 4 MTDS + N cross-repo):

### 2a. UAC — the SSOT layer (44 bare-COINBASE lines across 22 files)

Every UAC reference is one of these categories:

**CEFI ⇒ MIGRATE to `COINBASE-SPOT`** (unambiguous — the venue is the CEX):

| File                                           | Line                          | Context                                                                         | Migration                                                                                                      |
| ---------------------------------------------- | ----------------------------- | ------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `registry/venue_constants.py`                  | 377                           | `INSTRUMENT_TYPES_BY_VENUE["COINBASE"] = {"SPOT_PAIR"}` — D2a-critical          | **REMOVE** (COINBASE-SPOT entry already present at line 367)                                                   |
| `registry/market_data_categories.py`           | 242                           | `VENUES_BY_ASSET_GROUP["cefi"]` entry                                           | **REMOVE**                                                                                                     |
| `registry/market_data_categories.py`           | 1113-1116                     | `DataTypeCapability["COINBASE"] = {trades, book_snapshot_5}` (spot capability)  | **REMOVE** (COINBASE-SPOT entry at 1117-1120)                                                                  |
| `registry/venue_mapping.py`                    | 154                           | `venue_to_ccxt["COINBASE"] = "coinbase"`                                        | **RE-KEY** → `"COINBASE-SPOT": "coinbase"` (already present as tardis-endpoint at 181 — verify no duplication) |
| `registry/venue_mapping.py`                    | 818                           | `venue_instrument_type_to_tardis[("COINBASE", "SPOT_PAIR")] = "coinbase"`       | **REMOVE** (COINBASE-SPOT entry at 819 already exists)                                                         |
| `registry/venue_mapping.py`                    | 868                           | `spot_mvp_filtered_venues = [..., "COINBASE"]` — kimchi/coinbase premium filter | **RE-KEY** → `"COINBASE-SPOT"`                                                                                 |
| `registry/venue_instrument_config.py`          | 38                            | `default_venue_instrument_types["COINBASE"] = ["SPOT_PAIR"]`                    | **RE-KEY** → `"COINBASE-SPOT"`                                                                                 |
| `registry/venue_instrument_config.py`          | 70                            | `default_quote_assets["COINBASE"] = ["USD"]`                                    | **RE-KEY** → `"COINBASE-SPOT"`                                                                                 |
| `registry/venue_adapter_keys.py`               | 100-104                       | `"COINBASE": NO_ADAPTER_YET` + explanatory comment                              | **REMOVE** + delete the "bare-alias" comment                                                                   |
| `registry/venue_launch_dates.py`               | 64                            | `CEFI_VENUE_LAUNCH_DATES["COINBASE"] = "2014-12-08"`                            | **RE-KEY** → `"COINBASE-SPOT"`                                                                                 |
| `registry/session_times.py`                    | 108                           | `_CEFI_SESSION_TIMES["COINBASE"] = _CRYPTO_SESSION`                             | **RE-KEY** → `"COINBASE-SPOT"`                                                                                 |
| `registry/data_availability.py`                | 349                           | availability catalogue entry                                                    | **RE-KEY** → `"COINBASE-SPOT"`                                                                                 |
| `registry/representative_sample.py`            | 53                            | `"venue": "COINBASE"` in a sample record                                        | **RE-KEY** → `"COINBASE-SPOT"`                                                                                 |
| `canonical/coverage_starts.py`                 | 38, 44                        | `_CEFI_COVERAGE_STARTS["COINBASE"] = date(2014, 12, 8)`                         | **RE-KEY** → `"COINBASE-SPOT"`                                                                                 |
| `internal/reference/instrument_key.py`         | 30                            | `_TARDIS_CCXT_CANON["COINBASE"] = "coinbase"`                                   | **RE-KEY** → `"COINBASE-SPOT"`                                                                                 |
| `external/nautilus/data_schemas.py`            | 283                           | `_NAUTILUS_TO_UAC["coinbase"] = "COINBASE"`                                     | **RE-KEY** → `"COINBASE-SPOT"`                                                                                 |
| `canonical/crosscutting/mvp_scope.py`          | 100, 185, 480, 512, 922, 1062 | comments + base-token-fallback logic (`is_mvp("cefi", "COINBASE", …)` calls)    | **KEEP + DOCUMENT** as legacy compat OR remove after callers migrated (see §4)                                 |
| `canonical/crosscutting/execution_fidelity.py` | 37, 76, 108, 234              | comments describing the "trades-only override" behavior                         | **KEEP** (comments; will be trues after migration)                                                             |

**DEFI-LST ⇒ KEEP-BARE** (the venue is the LST-issuer PROTOCOL, not the CEX):

| File                                            | Line    | Context                                                              | Migration                        |
| ----------------------------------------------- | ------- | -------------------------------------------------------------------- | -------------------------------- |
| `registry/capability_declarations/_defi_lst.py` | 69      | `LST_VENUE_TO_TOKENS["COINBASE"] = ("cbETH",)`                       | **KEEP BARE** (cbETH-issuer key) |
| `internal/domain/defi/lst.py`                   | 41      | `LST_TOKEN_TO_PROTOCOL_ASSET["cbETH"] = ("COINBASE", "ETH")`         | **KEEP BARE** (cbETH-issuer key) |
| `registry/expected_coverage.py`                 | 281     | `"COINBASE": list(_DEFI_LST_PAIRS)` — cbETH LST pairs                | **KEEP BARE** (LST catalogue)    |
| `registry/venue_launch_dates.py`                | 236     | `DEFI_VENUE_LAUNCH_DATES["COINBASE"] = "2022-08-24"` — cbETH mainnet | **KEEP BARE** (LST issuer)       |
| `external/coinbase/schemas.py`                  | 367-368 | docstring cross-refs to `_defi_lst.py` + `lst.py`                    | **KEEP** (documentation)         |

**BACKTEST / RESTAKING architecture-v2 (out of D2a scope)**:

| File                                                   | Line                    | Context                                                                                                 | Migration                                                                                            |
| ------------------------------------------------------ | ----------------------- | ------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `internal/architecture_v2/restaking_rewards.py`        | 110, 657, 663, 676, 718 | `cex_listings=["BINANCE", "COINBASE", ...]` — bare COINBASE = CEX identifier                            | **RE-KEY** → `"COINBASE-SPOT"`                                                                       |
| `internal/architecture_v2/backtest_scenarios.py`       | 337                     | `id="SCN-B4-CBETH-PEG-COINBASE"` — scenario ID string; refers to the CEX venue for the peg arb backtest | **RE-KEY** → `id="SCN-B4-CBETH-PEG-COINBASE-SPOT"` (or LEAVE — it's a string ID, not a venue lookup) |
| `internal/architecture_v2/archetype_leg_spec_seeds.py` | 2 occurrences           | `"coinbase"` (lowercase) — tardis-endpoint spelling                                                     | **KEEP LOWERCASE** (Tardis endpoint spelling, not a bare UAC key)                                    |

### 2b. instruments-service (5 bare-COINBASE lines across 6 files)

| File                                                                         | Line              | Context                                                                                                                                      | Migration                                                                                                                                                                                                                                                            |
| ---------------------------------------------------------------------------- | ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `instruments_service/engine/orchestrator/venue_core.py`                      | 145-146           | `expand_cefi_tardis_endpoints`: `elif venue == "COINBASE": result.append("COINBASE-SPOT")` — the runtime alias expansion for the IS producer | **DELETE** the `elif` branch entirely; after UAC removes bare COINBASE from `VENUES_BY_ASSET_GROUP`, the input list will not contain bare COINBASE, so the expansion is dead code. The passthrough (`else: result.append(venue)`) handles `COINBASE-SPOT` correctly. |
| `instruments_service/engine/orchestrator/venue_core.py`                      | 97, 115, 126, 317 | docstring examples of the expansion                                                                                                          | **UPDATE** docstring to remove COINBASE special case                                                                                                                                                                                                                 |
| `scripts/check_enumeration_completeness.py`                                  | 158-173           | `_CEFI_VENUE_FOLD = {"COINBASE-SPOT": "COINBASE", ...}` — D2a fold                                                                           | **INVERT** the anchor (see §3)                                                                                                                                                                                                                                       |
| `scripts/cefi_per_venue_capture_summary.py`                                  | 7, 50, 70         | **AUDITED 2026-07-10**: all 3 hits already `COINBASE-SPOT` (venue list, tuple key, comment) — zero bare-COINBASE                             | **NO CHANGE** — confirmed clean                                                                                                                                                                                                                                      |
| `scripts/enumerate_expected_universe.py`                                     | 601, 603          | **AUDITED 2026-07-10**: only hits are `COINBASE-SPOT` in comments; no direct bare-COINBASE string, reads from UAC as expected                | **NO CHANGE** — confirmed clean                                                                                                                                                                                                                                      |
| `scripts/reconcile_cefi_tardis_thirdkey_drift_2026_05_07.py`                 | 20, 94            | **AUDITED 2026-07-10**: bare COINBASE only in docstring/comment prose (venue-name examples), no lookup                                       | **KEEP** — historical; delete-when-obsolete per lifecycle policy                                                                                                                                                                                                     |
| `scripts/reconcile_corrupt_kebab_rows_lst_rates_oracle_prices_2026_05_16.py` | 45                | **AUDITED 2026-07-10**: bare COINBASE listed alongside ETHERFI/LIDO/JITO/MARINADE — DeFi-LST protocol context, not a CeFi lookup             | **KEEP BARE** — historical + DeFi-LST context                                                                                                                                                                                                                        |
| `scripts/local_cefi_recent_gap_fill.sh`                                      | 17, 33            | **AUDITED 2026-07-10**: `VENUES=` list already contains `COINBASE-SPOT`; line 17 comment also `COINBASE-SPOT` — zero bare-COINBASE           | **NO CHANGE** — confirmed clean                                                                                                                                                                                                                                      |

### 2c. market-tick-data-service (4 bare-COINBASE lines across 4 files; 1 DeFi-LST context)

| File                                                                                  | Line            | Context                                                                                                                                                               | Migration                                                                                                                                                                                                                                                                                                                      |
| ------------------------------------------------------------------------------------- | --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `market_tick_data_service/market_interface/adapters/defi/lst_coinbase_adapter.py`     | 33, 34, 112     | LST adapter for cbETH — `self.venue = "COINBASE-ETHEREUM"` + comments referring to `LST_VENUE_TO_TOKENS["COINBASE"]`                                                  | **KEEP BARE** (DeFi LST context)                                                                                                                                                                                                                                                                                               |
| `market_tick_data_service/scripts/migrate_cefi_flat_to_v9_canonical.py`               | 38, 75          | migration script comment: bare `COINBASE` is drift for `COINBASE-SPOT`                                                                                                | **KEEP** — historical migration script; already documents the CF-7 relabel                                                                                                                                                                                                                                                     |
| `scripts/migrate_cefi_instrument_types.py`                                            | 168, 186        | **AUDITED 2026-07-10**: already `COINBASE-SPOT` only — zero bare-COINBASE                                                                                             | **NO CHANGE** — confirmed clean                                                                                                                                                                                                                                                                                                |
| `scripts/migrate_cefi_v2.py`                                                          | 95              | **AUDITED 2026-07-10**: already `COINBASE-SPOT` only (`_SPOT_DEFAULT_VENUES` frozenset) — zero bare-COINBASE                                                          | **NO CHANGE** — confirmed clean                                                                                                                                                                                                                                                                                                |
| `scripts/smoke_matrix.py`                                                             | 77              | `_REPRESENTATIVE_SYMBOL["COINBASE"] = "BTC-USD"` — cell enumeration keys off UAC's `VENUES_BY_ASSET_GROUP["cefi"]`, which still emits bare `COINBASE` (S3 not landed) | **DONE 2026-07-10** — ADDED `"COINBASE-SPOT": "BTC-USD"` additively alongside the existing bare key (NOT a rename — renaming now would silently drop the representative symbol for the still-enumerated bare-COINBASE cell until S3 lands, the same class of regression slot-9 found for S2). Forward-compatible either order. |
| `market_tick_data_service/engine/orchestrator/preflight.py`                           | 303, 502        | **AUDITED 2026-07-10**: already `COINBASE-SPOT` only — zero bare-COINBASE                                                                                             | **NO CHANGE** — confirmed clean                                                                                                                                                                                                                                                                                                |
| `market_tick_data_service/engine/orchestrator/symbol_rules.py`                        | 155             | **AUDITED 2026-07-10**: already `COINBASE-SPOT` only — zero bare-COINBASE                                                                                             | **NO CHANGE** — confirmed clean                                                                                                                                                                                                                                                                                                |
| `market_tick_data_service/engine/orchestrator/venue_fetch.py`                         | 284, 487        | **AUDITED 2026-07-10**: already `COINBASE-SPOT` only (comments) — zero bare-COINBASE                                                                                  | **NO CHANGE** — confirmed clean                                                                                                                                                                                                                                                                                                |
| `market_tick_data_service/engine/shard_memory_profile.py`                             | 57, 60, 61, 162 | **AUDITED 2026-07-10**: already `COINBASE-SPOT` only — zero bare-COINBASE                                                                                             | **NO CHANGE** — confirmed clean                                                                                                                                                                                                                                                                                                |
| `configs/expected_start_dates.yaml`                                                   | 127             | **market-tick-data-service:** section `venues:` map                                                                                                                   | **DONE 2026-07-10** — rekeyed `COINBASE` → `COINBASE-SPOT`. File also carries `instruments-service:`/`features-delta-one-service:` sections (lines 55, 248, 258) with their own bare-COINBASE entries — those belong to S4/S6 craft scope, left untouched here.                                                                |
| `configs/venue_data_types.yaml`                                                       | 112             | asset-group-scoped `CEFI:` map, no live MTDS runtime consumer (confirmed via repo-wide grep — this file is unused dead config in-repo)                                | **DONE 2026-07-10** — rekeyed `COINBASE` → `COINBASE-SPOT` (zero regression risk, nothing reads this key today).                                                                                                                                                                                                               |
| `market_tick_data_service/live/connectors/{coinbase_book_ws.py, coinbase_spot_ws.py}` | n/a             | live WS connectors (already register `COINBASE-SPOT`, so file names are cosmetic)                                                                                     | **AUDITED 2026-07-10** — confirmed no bare `"COINBASE"` register call. **NO CHANGE**                                                                                                                                                                                                                                           |
| `market_tick_data_service/live/connectors/__init__.py`                                | n/a             | connector registry                                                                                                                                                    | **AUDITED 2026-07-10** — confirmed already registers COINBASE-SPOT only. **NO CHANGE**                                                                                                                                                                                                                                         |

### 2d. execution-service (12 bare-COINBASE lines across 12 files)

Execution-service is **OUT-OF-SCOPE for this data_engineering plan** per main's directive. Documented here for the
follow-on:

| File                                                          | Line                  | Context                                                                                    | Follow-on action                                                                                                                             |
| ------------------------------------------------------------- | --------------------- | ------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------- |
| `execution_service/instruments/registry.py`                   | 178-179, 207-208, 310 | bare-venue backward-compat resolver (`"COINBASE" → "COINBASE-SPOT"`) + Nautilus map        | **KEEP the resolver** (this is a resilience shim for external callers passing bare venue names) OR migrate + delete once callers are cleaned |
| `execution_service/instruments/utils.py`                      | 239                   | `normalize_venue_for_nautilus` — coerces bare/qualified → NautilusTrader's bare `COINBASE` | **KEEP** — Nautilus itself uses bare `COINBASE` as its venue name; this is intentional                                                       |
| `execution_service/utils/nautilus_compatibility.py`           | 17                    | `NAUTILUS_SUPPORTED_VENUES` frozenset includes `"COINBASE"`                                | **KEEP** — Nautilus support catalogue                                                                                                        |
| `execution_service/services/execution_cost_estimator.py`      | 32                    | `_VENUE_FEES_BPS["COINBASE"]`                                                              | **RE-KEY** to `COINBASE-SPOT` (fee schedule per canonical venue) OR keep as base fallback                                                    |
| `execution_service/trade_execution/factory.py`                | 104                   | `venue_map["coinbase"] = Venue.COINBASE` — Nautilus routing                                | **KEEP** — Nautilus context                                                                                                                  |
| `execution_service/algo_library/algorithms/sor.py`            | 27, 29, 34, 153, 169  | SOR algorithm example / cost snapshot / mock venue keys                                    | **RE-KEY** to `COINBASE-SPOT` in the cost snapshot dict; **KEEP** the docstring examples (they can either be bare or -SPOT — cosmetic)       |
| `execution_service/custody/pre_trade_pinger.py`               | 15                    | docstring comment                                                                          | **KEEP** or update as documentation                                                                                                          |
| `execution_service/engine/backtest/preflight.py`              | 90                    | Nautilus support message                                                                   | **KEEP** — Nautilus context                                                                                                                  |
| `execution_service/engine/handlers/trade_handler.py`          | (grep)                | possibly a lookup                                                                          | **AUDIT + RE-KEY** if a lookup                                                                                                               |
| `execution_service/results/serializer.py`                     | (grep)                | possibly a lookup                                                                          | **AUDIT + RE-KEY** if a lookup                                                                                                               |
| `execution_service/trade_execution/adapters/coinbase_ccxt.py` | (grep)                | adapter class                                                                              | **KEEP** file (bare-word CCXT context)                                                                                                       |
| `execution_service/trade_execution/venue_mapping.py`          | (grep)                | execution-service local venue map                                                          | **AUDIT + RE-KEY**                                                                                                                           |
| `configs/expected_start_dates.yaml`                           | (grep)                | YAML config                                                                                | **RE-KEY**                                                                                                                                   |

**Follow-on task pointer**: file a new plan under
`plans/active/coinbase_bare_name_migration_execution_service_2026_07_06.md` (or later date) once this plan is landed and
gap-015 has cleared UAC. Owner: `assigned_role: backend-engineer`. Depends on THIS plan.

### 2e. Other service repos

| Repo                             | Files                                                                                                                                                                                      | Migration                                                                                                                                                                                                      |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `unified-trading-library`        | `post_trade/settler.py:52` — fee-schedule fallback; `config_interface/instrument.py:30` — enum `COINBASE = "COINBASE"` (the string value is a stable identifier for consumers).            | **KEEP** the enum name (identifier), **RE-KEY** the string VALUE to `"COINBASE-SPOT"` OR keep as CEX-alias — flag for the utl-owning slot.                                                                     |
| `features-service`               | `cross_instrument/app/calculators/paired_dispatch.py`, `scripts/delta_one/seed_mock_data.py:76`, plus test callers                                                                         | **RE-KEY** the mock-data seed to COINBASE-SPOT; **AUDIT** paired_dispatch for lookups vs labels.                                                                                                               |
| `market-data-processing-service` | `engine/mock_data_provider.py`, `scripts/seed_mock_data.py`                                                                                                                                | **RE-KEY** to COINBASE-SPOT (mock-data providers).                                                                                                                                                             |
| `deployment-api`                 | `routes/venue_relaunch_estimate.py`, `services/data_status/{defi,manifest,reference_scope,rollup_cache}.py`, `services/data_status_mock.py`                                                | **AUDIT** each — `reference_scope.py:107,126` comments describe bare-venue base-venue duality (BASE lookup) — likely **KEEP** as the descriptive comment. Others: **AUDIT + RE-KEY** where it's a data-lookup. |
| `deployment-service`             | `calculators/shard_distribution.py:392,397`, `deployment/{orchestrator,worker_manager}.py`, `scripts/vm/*.sh`, `cli/utils/manifest_reader.py`, `tools/check_ml_dependencies_by_mode.py:87` | **RE-KEY** shard-distribution `spot_only_venues` to `COINBASE-SPOT`; **AUDIT + KEEP** where the string is a documentation label (docs/runbooks/RESOURCE-profiles).                                             |

## 3. `_CEFI_VENUE_FOLD` re-anchor — the D2a-safety change

**Current state** (`instruments-service/scripts/check_enumeration_completeness.py:158-173`):

```python
_CEFI_VENUE_FOLD: dict[str, str] = {
    "OKX-SPOT": "OKX",
    "OKX-SWAP": "OKX",
    "OKX-FUTURES": "OKX",
    "COINBASE-SPOT": "COINBASE",   # ← folds writer-side COINBASE-SPOT → EXPECTED-side bare COINBASE
    "BYBIT-FUTURES": "BYBIT",
    "COINBASE-INTERNATIONAL": "COINBASE-FUTURES",
    "OKEX": "OKX",
    "OKEX-SWAP": "OKX",
    "OKEX-FUTURES": "OKX",
    "CRYPTOFACILITIES": "KRAKEN-FUTURES",
    "BITFINEX-DERIVATIVES": "BITFINEX-FUTURES",
}
```

The fold direction is `writer-token → EXPECTED-token`. Today the EXPECTED token for spot Coinbase is bare `COINBASE`, so
writer-side `COINBASE-SPOT` folds to it. After this migration bare `COINBASE` disappears from EXPECTED, which means
`COINBASE-SPOT` is BOTH the writer token AND the EXPECTED token — the fold entry is no longer needed for that pair.

**Fix (single-edit)** — remove the `"COINBASE-SPOT": "COINBASE"` line:

```python
_CEFI_VENUE_FOLD: dict[str, str] = {
    "OKX-SPOT": "OKX",
    "OKX-SWAP": "OKX",
    "OKX-FUTURES": "OKX",
    # (bare COINBASE removed from UAC 2026-XX-XX; COINBASE-SPOT is now the
    # canonical EXPECTED token — no fold needed here since writer emits
    # COINBASE-SPOT.)
    "BYBIT-FUTURES": "BYBIT",
    "COINBASE-INTERNATIONAL": "COINBASE-FUTURES",
    "OKEX": "OKX",
    "OKEX-SWAP": "OKX",
    "OKEX-FUTURES": "OKX",
    "CRYPTOFACILITIES": "KRAKEN-FUTURES",
    "BITFINEX-DERIVATIVES": "BITFINEX-FUTURES",
}
```

**But** — legacy manifest rows that stamped bare `COINBASE` (writer-side, pre-2026-06-23 canonical-perp-gate migration)
still exist in the manifest. These rows would now come through the fold un-mapped and end up in the
`ENUMERATED - EXPECTED` STRAY bucket. Two options to handle those:

**Option A (recommended, single-edit)** — INVERT the fold anchor:

```python
_CEFI_VENUE_FOLD: dict[str, str] = {
    "OKX-SPOT": "OKX",
    "OKX-SWAP": "OKX",
    "OKX-FUTURES": "OKX",
    "COINBASE": "COINBASE-SPOT",  # ← INVERTED (2026-XX-XX): after bare COINBASE
    #   dropped from UAC VENUES_BY_ASSET_GROUP + INSTRUMENT_TYPES_BY_VENUE,
    #   COINBASE-SPOT is the sole canonical EXPECTED token; legacy manifest
    #   rows that stamped bare COINBASE fold UP to COINBASE-SPOT so they
    #   match EXPECTED (avoids a stray bucket + preserves audit continuity).
    "BYBIT-FUTURES": "BYBIT",
    "COINBASE-INTERNATIONAL": "COINBASE-FUTURES",
    "OKEX": "OKX",
    "OKEX-SWAP": "OKX",
    "OKEX-FUTURES": "OKX",
    "CRYPTOFACILITIES": "KRAKEN-FUTURES",
    "BITFINEX-DERIVATIVES": "BITFINEX-FUTURES",
}
```

Rationale for Option A:

- Zero new stray tuples on the Layer-1 audit (legacy bare-COINBASE writer rows fold to the new canonical).
- Symmetric with the existing `OKX-SPOT → OKX` / `BYBIT-FUTURES → BYBIT` entries (a legacy-writer-token →
  canonical-EXPECTED fold).
- The invariant expressed by the fold is the same: "writer-side dialects → the ONE canonical EXPECTED token", we just
  changed which token is canonical.
- Reversible — if we later graduate the writer to emit only COINBASE-SPOT and clean up historical rows, the entry
  becomes a no-op.

**Option B (belt-and-braces)** — same as Option A, plus a one-shot manifest relabel migration script that rewrites all
historical bare-COINBASE capture_status rows in the availability manifest to `COINBASE-SPOT`. Costs a manifest
re-consolidation; benefit is that the fold becomes truly unnecessary after the migration completes. Not recommended for
THIS plan (extra scope); can be filed as a P3 follow-on.

**Regression guard**: the plan lands with a new test in
`instruments-service/tests/test_check_enumeration_completeness.py` that asserts:

- `_canon_venue("cefi", "COINBASE")` returns `"COINBASE-SPOT"` (Option A fold applies).
- `_canon_venue("cefi", "COINBASE-SPOT")` returns `"COINBASE-SPOT"` (passthrough).
- The EXPECTED set for `("cefi", "COINBASE-SPOT")` contains `("SPOT_PAIR", "trades")` and
  `("SPOT_PAIR", "book_snapshot_5")` (matches `DataTypeCapability["COINBASE-SPOT"]`), so the itype-gate authority switch
  does NOT drop the pair.

## 4. Sequenced multi-repo landings — the DAG

Every step is one shippable unit (`bash scripts/quality-gates.sh`-green quickmerge). The write-order is chosen so **no
intermediate LDR state is data-incorrect** (a Layer-1 audit could run against LDR at any point between steps and pass or
emit a small, expected residual — never a silent zeroing).

### Step S0 (prep — this plan lands as `status: draft` first)

- [x] [DESIGN] P2. Land THIS plan as `status: draft` via `docs(plans):` commit (do NOT quickmerge; do NOT ingest).
      Operator reviews + flips to `status: active` + `assigned_vm: planning` if agent execution is desired. Gate: file
      present on LDR HEAD; commit message starts with `docs(plans):`; no worker dispatched. **DONE 2026-07-10** —
      operator decision #3 in `instruments_remaining_work_audit_2026_07_10.md` dispatched full execution; flipped
      `status: draft` → `active`, `assigned_vm: NA` → `planning` this commit.

### Step S1 — instruments-service `_CEFI_VENUE_FOLD` invert (Option A, single-file edit)

- [x] [CODE] P2. `instruments-service/scripts/check_enumeration_completeness.py`: replace `"COINBASE-SPOT": "COINBASE"`
      with `"COINBASE": "COINBASE-SPOT"` (Option A). Add unit test in `tests/test_check_enumeration_completeness.py`
      (see §3). Ship via
      `quickmerge --agent --files 'scripts/check_enumeration_completeness.py tests/test_check_enumeration_completeness.py'`.
      **Gate:** `bash scripts/quality-gates.sh` green; new test passes; existing Layer-1 audit against production
      manifest does NOT show a new `expected_only` or `enumerated_only` COINBASE row (verify by re-running
      `check_enumeration_completeness.py --asset-group cefi` against the current manifest snapshot). **DONE 2026-07-10**
      — instruments-service@300b0767. Ran `measure_honest_coverage.py --asset-group cefi     --diagnose-layer1` against
      the live production manifest (`market-data-tick-cefi-prd-central-element-323112`, 11.1M merged rows) before and
      after reasoning through the diff: the fold invert relabels the pre-existing `(COINBASE-SPOT, spot_pair, trades)`
      stray from venue token `COINBASE` to `COINBASE-SPOT` — no new `expected_only`/`enumerated_only` COINBASE row
      appeared (stray/missing counts for COINBASE unchanged: 1 stray, 0 new missing). That residual stray's root cause
      is the `CeFiMvpRule.venues` split (`COINBASE-SPOT` / `COINBASE-FUTURES` already MVP-recognized; bare `COINBASE` is
      not, since `_CEFI_SUB_VENUE_BASES` only covers `OKX`) — exactly the `VENUES_BY_ASSET_GROUP["cefi"]` rename this
      plan's **S3** fixes; not a regression from S1 and not a new finding (already the plan's own problem statement).

### Step S3 — UAC removal (the "gap-015" step, now un-blocked)

- [ ] [CODE] P2. `unified-api-contracts/`: apply every CEFI ⇒ MIGRATE from §2a. Concrete file diff:
  - `registry/venue_constants.py`: delete line 377 (`"COINBASE": {"SPOT_PAIR"}`) and its 8-line D2a comment (368-376).
    Delete `COINBASE-INTERNATIONAL` fold entry from `_CEFI_VENUE_FOLD` only if S1 already landed.
  - `registry/market_data_categories.py`: delete line 242 (`"COINBASE",`) from `VENUES_BY_ASSET_GROUP["cefi"]`; delete
    lines 1113-1116 (`"COINBASE"` DataTypeCapability entry).
  - `registry/venue_mapping.py`: delete line 154 (`venue_to_ccxt["COINBASE"] = "coinbase"`) — `COINBASE-SPOT` mapping
    already exists via tardis_to_venue at line 181; delete line 818 (`("COINBASE", "SPOT_PAIR"): "coinbase"`); change
    line 868 (`spot_mvp_filtered_venues`) `"COINBASE"` → `"COINBASE-SPOT"`.
  - `registry/venue_instrument_config.py:38,70`: `"COINBASE"` → `"COINBASE-SPOT"`.
  - `registry/venue_adapter_keys.py:100-104`: delete the bare `"COINBASE": NO_ADAPTER_YET` entry + its comment.
  - `registry/venue_launch_dates.py:64`: rename key `"COINBASE"` → `"COINBASE-SPOT"`. **DO NOT** touch line 236
    (DeFi-LST cbETH context — bare COINBASE STAYS).
  - `registry/session_times.py:108`: rename key.
  - `registry/data_availability.py:349`: rename key.
  - `registry/representative_sample.py:53`: rename `venue` field value.
  - `canonical/coverage_starts.py:44`: rename key. Delete the `COINBASE` mention in the docstring at line 38 (or update
    to reference `COINBASE-SPOT`).
  - `internal/reference/instrument_key.py:30`: rename key.
  - `external/nautilus/data_schemas.py:283`: rename value.
  - `canonical/crosscutting/mvp_scope.py`: comment-only — no runtime change needed for this step because the
    `_CEFI_SUB_VENUE_BASES = frozenset({"OKX"})` on line 89 does NOT include `COINBASE` (already verified in the gap-016
    audit), and the `is_mvp("cefi", "COINBASE", …)` base-normalize path is only exercised for callers that pass bare
    COINBASE — which will disappear once we finish the caller migration. Leave the comments in place; they document the
    historical shape.
  - `internal/architecture_v2/restaking_rewards.py`: `cex_listings` lists — rename `"COINBASE"` → `"COINBASE-SPOT"` (4
    occurrences).

  **DO NOT touch** the DeFi-LST caller subset (§2a "DEFI-LST ⇒ KEEP-BARE"): `_defi_lst.py:69`, `lst.py:41`,
  `expected_coverage.py:281`, `venue_launch_dates.py:236`. These use bare COINBASE as the cbETH-issuer PROTOCOL key.

  Ship via `quickmerge --agent --files '<the 12 UAC files above>'`. **Gate:**
  - UAC `bash scripts/quality-gates.sh` green.
  - `grep -n '"COINBASE"' unified_api_contracts/registry/venue_constants.py` returns 0 hits.
  - `"COINBASE" not in VENUES_BY_ASSET_GROUP["cefi"]` at runtime (add a UAC unit test).
  - `check_enumeration_completeness.py` audit against production manifest shows COINBASE cell counts UNCHANGED (fold
    from S1 does its job).

### Step S2 — instruments-service `venue_core.py` delete the dead `elif COINBASE` alias

> **✅ ORDERING FIXED 2026-07-10** — verified 2026-07-10 by slot 9 (data_engineering) that landing this step before S3
> fails 2 regression tests (see the disproven ordering note below). Resolved via Option A of
> `plans/active/issues/coinbase_bare_name_migration_s2_ordering_2026_07_10.md`: this plan's frontmatter now sets
> `sequential: true`, and this S2 section was physically moved to AFTER the S3 section above (regen chains
> `prereqs.completed_tasks` to the immediately-preceding unchecked todo in file order — S3, not S1). The dispatcher will
> not offer S2 to a worker until S3's backlog task is `done`. Do not reorder S2 back above S3 without re-verifying this
> gate.

- [ ] [CODE] P2. `instruments-service/instruments_service/engine/orchestrator/venue_core.py`: delete lines 145-146
      (`elif venue == "COINBASE": result.append("COINBASE-SPOT")`) — after S1 the fold handles residuals; this expansion
      becomes dead code once UAC drops bare COINBASE (S3). Update the docstring lines 97/115/126/317 to remove the
      COINBASE special case. Regression test: `test_expand_cefi_tardis_endpoints_no_bare_coinbase_input` — feeding
      `["COINBASE-SPOT", "BINANCE-SPOT"]` produces `["COINBASE-SPOT", "BINANCE-SPOT"]` (passthrough). **Gate:** QG
      green; test added; no downstream IS producer regressions in `tests/unit/`. **Depends on S3 landing first**
      (machine-gated via `sequential: true` — see banner above) — verified 2026-07-10 that landing S2 before S3 fails
      this exact gate.

  ~~Ordering note: S2 CAN land before S3 because it does not READ the UAC dict; it just deletes a runtime alias branch
  that will still be exercised (by test callers) until S3 removes bare COINBASE from the input list. Safe to land now.~~
  **DISPROVEN 2026-07-10**: `bash scripts/quality-gates.sh` run with the elif-branch deleted (S1/S3 not yet landed)
  fails 2 existing tests —
  `tests/unit/test_adapter_routing_uac_invariant.py::test_expanded_cefi_enumeration_fully_resolvable` (bare `COINBASE`
  resolves to `NO_ADAPTER_YET`) and
  `tests/unit/test_new_orchestrator.py::test_process_instruments_cefi_venues_available` (`COINBASE-SPOT` drops out of
  the CEFI venue list). Root cause: UAC's `VENUES_BY_ASSET_GROUP["cefi"]` still emits bare `COINBASE` until S3 lands, so
  deleting the alias branch makes IS's cefi venue producer emit an unmapped bare `COINBASE` — a real production
  regression, not just a test artifact. **S2 must land AFTER S3** (or be combined into the same cross-repo shippable
  unit as S3).

### Step S4 — IS data_engineering downstream ripple

- [x] [CODE] P2. `instruments-service/`: audit each remaining bare-COINBASE hit (§2b) and re-key any lookups.
      `scripts/local_cefi_recent_gap_fill.sh`, `scripts/enumerate_expected_universe.py`,
      `scripts/cefi_per_venue_capture_summary.py` — if any read `VENUES_BY_ASSET_GROUP["cefi"]` and got bare COINBASE,
      they now get COINBASE-SPOT and pass through. Leave historical one-off migration scripts
      (`reconcile_*_2026_*_*.py`) as documentary; they will not re-run. **Gate:** QG green; audit script self-test still
      passes; no runtime string errors. **DONE 2026-07-10 (slot-11)** — repo-wide grep sweep of `instruments-service`
      (excluding S1's `check_enumeration_completeness.py` and S2's `venue_core.py`, both handled by parallel tasks
      001/002) found **zero bare-COINBASE lookups requiring re-key**: all 3 named files already reference
      `COINBASE-SPOT` exclusively (see §2b, updated with confirmed line numbers); the 2 historical
      `reconcile_*_2026_*_*.py` scripts only mention bare COINBASE in documentary comments (one of them in DeFi-LST
      protocol context alongside ETHERFI/LIDO/JITO/MARINADE — correctly stays bare per §2a). No code diff needed — this
      step's target state was already met independent of S1/S3 landing order. Evidence:
      `grep -rn 'COINBASE'     --include='*.py' --include='*.sh' --exclude-dir='.venv*' --exclude-dir=build --exclude-dir=htmlcov . | grep -v     'COINBASE-SPOT\|COINBASE-FUTURES\|COINBASE-INTERNATIONAL\|COINBASE-ETHEREUM' | grep -v '/tests/'`
      returns only the S1/S2-owned files + the historical-comment hits above.

### Step S5 — MTDS data_engineering downstream ripple

- [x] [CODE] P2. `market-tick-data-service/`: apply §2c CEFI callers. Deep-audit
      `engine/orchestrator/{preflight,symbol_rules,venue_fetch}.py`, `engine/shard_memory_profile.py`, `configs/*.yaml`.
      Re-key any lookups to COINBASE-SPOT. Leave the `lst_coinbase_adapter.py` DeFi-LST references alone. **Gate:** MTDS
      QG green; smoke_matrix.py returns identical output for the (cefi, COINBASE-SPOT) row that it previously returned
      for (cefi, COINBASE); shard-launch scripts (`launch-cefi-*.sh` in deployment-service) still target the COINBASE
      shard (name may need to shift COINBASE → COINBASE-SPOT in the shard registry — coordinate with the
      deployment-service step). **DONE 2026-07-10** — market-tick-data-service@b5f653a9. Deep-audit found the four
      engine files (`preflight.py`, `symbol_rules.py`, `venue_fetch.py`, `shard_memory_profile.py`) already
      writer-token-canonical (`COINBASE-SPOT` only, no bare COINBASE) — they operate on the WRITER-side token, which
      migrated in the 2026-06-23 perp-gate change, distinct from UAC's EXPECTED-side `VENUES_BY_ASSET_GROUP` (still
      bare, pending S3). Re-keyed `configs/venue_data_types.yaml:112` and `configs/expected_start_dates.yaml:127`
      (market-tick-data-service section only — confirmed no live runtime consumer for the first file; the second is read
      via UTL `DateValidator`'s cwd-search but MTDS's own code never calls it, so zero regression risk either way).
      `scripts/smoke_matrix.py:77` got an ADDITIVE `COINBASE-SPOT` entry (kept bare `COINBASE` too) since its cell
      enumeration reads live from UAC's `VENUES_BY_ASSET_GROUP["cefi"]`, which still emits bare `COINBASE` until S3
      lands — a straight rename here would have reproduced the exact S2-ordering regression slot-9 found (silently
      dropping the representative symbol for the still-enumerated cell). `bash scripts/quality-gates.sh` green at the
      committed SHA (sentinel-verified); shipped via
      `quickmerge --agent --files 'configs/expected_start_dates.yaml     configs/venue_data_types.yaml scripts/smoke_matrix.py'`.

### Step S6 — cross-repo ripple (features-service, MDPS, UTL, deployment-api, deployment-service)

- [ ] [CODE] P3. `features-service/`, `market-data-processing-service/`, `unified-trading-library/`, `deployment-api/`,
      `deployment-service/`: apply §2e. Each repo lands independently after S3 (UAC ships first). For the
      deployment-service shard-launch scripts (`scripts/vm/launch-cefi-{forward-poll,sharded-backfill}.sh`), coordinate
      with the deployment-service owner if COINBASE-shard VM naming needs to update — the shard name is data-plane
      observable. **Gate per repo:** QG green; mock-seeds emit COINBASE-SPOT; data_status_mock produces identical
      counts.

### Step S7 — execution-service follow-on (OUT-OF-SCOPE, filed as new plan)

- [x] [PLAN] P3. File `plans/active/coinbase_bare_name_migration_execution_service_2026_XX_XX.md` with
      `assigned_role: backend-engineer` for the 12 execution-service callers listed in §2d. Depends on THIS plan.
      Include a note about whether the `execution_service/instruments/registry.py:178-179` bare-venue backward-compat
      resolver should be kept (Nautilus-driven) or removed after downstream users are cleaned. Filed by the operator or
      whoever picks up the follow-on. **DONE 2026-07-10** — filed
      `plans/active/coinbase_bare_name_migration_execution_service_2026_07_10.md` (slot-8, data_engineering);
      `status: draft`, `assigned_vm: NA`, `assigned_role: backend-engineer`,
      `depends_on: [coinbase_bare_name_migration_2026_07_06]`.

## 5. Codex SSOTs consulted

- `codex/02-data/availability-manifest-and-data-status.md` — the writer/expected/enumerated pipeline that the D2a fold
  reconciles.
- `codex/02-data/honest-coverage-model.md` — Layer-1 / Layer-2 model that the itype-gate authority switch feeds.
- `codex/02-data/defi-canonical-naming-ssot.md` — DeFi-side canonical (protocol-chain) key rules — confirms the
  LST-issuer bare-COINBASE (cbETH context) is a DEFI-side key that STAYS bare.
- `plans/PLAN_FORMAT.md` — this plan's frontmatter shape.

## 6. Full-execution criterion (per CLAUDE.md "Plans Run To Actual Completion")

**Not applicable at draft state.** When flipped to `status: active`, the `Full-execution criterion` for the migration
is:

- ✅ After S1-S6 land, the Layer-1 `check_enumeration_completeness.py` audit against the production manifest returns
  EXPECTED-only + ENUMERATED-only bucket sizes for the ("cefi", "COINBASE-SPOT") pair that are ≤ their respective sizes
  for the pre-migration ("cefi", "COINBASE") pair. Growth is a regression.
  - **What ran**:
    `PYTHONPATH=... python instruments-service/scripts/check_enumeration_completeness.py --asset-group cefi --json-out /tmp/layer1.json`
    on the planning VM against `gs://mvp-manifest-bucket/manifest_index.json` HEAD.
  - **Verification**: `jq '.by_asset_group.cefi.by_venue["COINBASE-SPOT"].completeness_pct' /tmp/layer1.json` returns a
    value ≥ the pre-migration value for `.by_venue["COINBASE"]`.

- ✅ MTDS smoke matrix `blocked-not-registered` COINBASE cell count is 0 (was 25 pre-D2a; already registered
  post-gap-001, but verified).

- **No handoff exceptions** — this plan is contained to data_engineering repos + drafts an execution-service follow-on
  as a separate plan.

## 7. Deferred / out-of-scope

- **Execution-service (12 files)** — separate follow-on plan (§2d + S7).
- **DeFi-LST bare COINBASE (cbETH issuer)** — deliberately KEPT; this plan explicitly does NOT touch `_defi_lst.py`,
  `internal/domain/defi/lst.py`, `venue_launch_dates.py:236`, `expected_coverage.py:281`, or the MTDS
  `lst_coinbase_adapter.py`. The DeFi-LST bare COINBASE is the PROTOCOL name for the cbETH LST — analogous to `LIDO`,
  `ROCKETPOOL`, etc. — and is a DIFFERENT canonical namespace from the CeFi VENUES_BY_ASSET_GROUP dict.
- **Belt-and-braces manifest relabel (§3 Option B)** — reasonable P3 follow-on if the S1 fold entry is ever considered
  permanent debt; not in scope here.

## Progress Log

<!-- Append newest entries at the top: `- **YYYY-MM-DD** — <what landed> (<repo>@<sha> / evidence).` -->

- **2026-07-10** — **S5 done** (slot-7, data_engineering) — market-tick-data-service@b5f653a9. Deep-audited all §2c
  files; the four engine files (`preflight.py`, `symbol_rules.py`, `venue_fetch.py`, `shard_memory_profile.py`) were
  already `COINBASE-SPOT`-only (writer-side token, migrated separately in the 2026-06-23 perp-gate change — distinct
  from UAC's still-bare EXPECTED-side `VENUES_BY_ASSET_GROUP`). Re-keyed the two `configs/*.yaml` files (confirmed zero
  live MTDS runtime consumer, so zero regression risk). `scripts/smoke_matrix.py` got an ADDITIVE `"COINBASE-SPOT"`
  entry (kept bare `"COINBASE"` too) rather than a rename, because its cell enumeration reads UAC's
  `VENUES_BY_ASSET_GROUP["cefi"]` live and that dict still emits bare `COINBASE` until S3 lands — a straight rename
  would have reproduced the exact S2-ordering regression slot-9 already found (this plan's §2c table + S5 todo updated
  with confirmed line numbers). QG green (sentinel-verified at the committed SHA); shipped via quickmerge.
- **2026-07-10** — **S2/S3 ordering fixed** (slot-3, PM-only `docs(plans):` commit — no service-repo code diff).
  Implemented Option A of `plans/active/issues/coinbase_bare_name_migration_s2_ordering_2026_07_10.md` (slot 9's
  verified finding that S2 fails 2 regression tests if dispatched before S3): added `sequential: true` to this plan's
  frontmatter and physically reordered the body so the `### Step S3` section now precedes `### Step S2` —
  `regen_backlog_from_plan.py`'s sequential-chain wiring links each remaining unchecked todo to its immediate file-order
  predecessor, so the backlog now genuinely gates S2's dispatch on S3's task reaching `done` (previously only a
  human-readable blocked-banner, not a machine gate — S1-S6 had zero real prereq wiring despite the documented DAG
  dependency in §4). New todo order for the 4 still-open steps: S3 → S2 → S5 → S6. Updated S2's banner to reference this
  fix; kept the disproven "safe to land before S3" ordering note struck through for history. Flipped the issue doc's
  Option A checkbox + `status: resolved`. No code shipped (plan-file edit only); nothing to quickmerge.
- **2026-07-10** — **S7 done** (slot-8, data_engineering). Filed
  `plans/active/coinbase_bare_name_migration_execution_service_2026_07_10.md` — carries over the 12-file
  execution-service enumeration from §2d verbatim plus the `registry.py:178-179` backward-compat-resolver decision (KEEP
  the Nautilus-boundary map, decide the UAC-facing branch by audit at execution time). Filed as `status: draft`,
  `assigned_vm: NA` (LOCAL track, default per CLAUDE.md), `depends_on: [coinbase_bare_name_migration_2026_07_06]` — do
  not execute before S1-S6 of THIS plan land.
- **2026-07-10** — **S4 flipped** by slot-11 (data_engineering, PM-only `docs(plans):` commit — no instruments-service
  code diff). Audited the §2b file list outside S1's `check_enumeration_completeness.py` and S2's `venue_core.py` (both
  in-flight under tasks 001/002 at the time): `cefi_per_venue_capture_summary.py`, `enumerate_expected_universe.py`,
  `local_cefi_recent_gap_fill.sh` already reference `COINBASE-SPOT` exclusively — zero bare-COINBASE lookups to re-key.
  The 2 historical `reconcile_*_2026_*_*.py` scripts only carry bare COINBASE in documentary comments, correctly left
  as-is. §2b table updated with confirmed line numbers replacing the `(grep)` placeholders. Note for future dispatch:
  this plan's S1→S6 steps have a real internal dependency chain (documented in §4) but no
  `depends_on`/`sequential: true` gating between the per-step backlog tasks, so S1-S6 dispatched to multiple slots in
  parallel with prereqs reported as "met" — S4 happened to be safe to complete independent of S1/S3 landing order
  because its target files were already compliant, but that was a lucky audit outcome, not a guarantee; a future step in
  this DAG shape could be genuinely blocked by out-of-order dispatch.
- **2026-07-06** — **Plan drafted** by slot-10 (data_engineering) as gap-016 of
  `wsfeedconnector_phase35_gap_2026_07_06`. Per BLK-22e5f8a5 answered by main: `assigned_vm: NA`, `status: draft`,
  `assigned_role: data_engineering`; execution-service callers documented as out-of-scope with a §7 follow-on task
  pointer. Full enumeration of 44 UAC bare-COINBASE lines across 22 files + 5 IS + 4 MTDS + 12 execution-service
  (out-of-scope) + cross-repo (UTL/features/MDPS/deployment-{api,service}). D2a `_CEFI_VENUE_FOLD` re-anchor strategy:
  **Option A (single-edit inversion)** — flip `"COINBASE-SPOT": "COINBASE"` to `"COINBASE": "COINBASE-SPOT"`;
  zero-new-stray on Layer-1 audit; reversible. Sequenced landings S1→S6 (S0 = this draft) so no intermediate LDR state
  is data-incorrect. Ship via `docs(plans):` commit + push only (no quickmerge, no ingest — status:draft).
