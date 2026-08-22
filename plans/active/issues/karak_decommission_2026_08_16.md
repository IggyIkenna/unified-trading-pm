---
doc_type: issue
title: Decommission Karak entirely from the codebase
summary: >-
  Operator decision 2026-08-16: Karak's real integration is not the simple ERC4626 vault the current
  execution-service code assumes — live on-chain verification found the hardcoded vault address
  (`KarakConnector.WSTETH_VAULT`/`CORE_ADDRESS`) resolves to ZERO deployed bytecode, and Karak's actual wstETH
  restaking product ("King Karak" / weETHk) runs on a Veda/BoringVault architecture (Accountant/Teller/Lens/
  DelayedWithdraw contracts), a materially different and larger rebuild than any other DeFi connector in this
  repo. Given Symbiotic covers the same restaking-yield archetype role at ~20x Karak's real deposited size in the
  one comparable pool measured (16,349 wstETH vs 703.9 shares), the operator chose to decommission Karak entirely
  rather than rebuild it. This issue enumerates every reference across 8 repos (~50 files) found by a full-workspace
  grep, so removal is complete rather than partial (a half-removed venue is worse than the status quo — it reads as
  supported while quietly broken).
status: open
nature: issue
asset_group: [defi] # corrected 2026-08-19 (ag-closeout-audit cross-cutting, Phase 1 Workflow) -- was [cross-cutting, defi]; Karak is a single DeFi restaking venue decommission, not multi-AG
stage: [data, features, strategy, execution]
repos:
  [
    execution-service,
    unified-api-contracts,
    strategy-service,
    instruments-service,
    market-tick-data-service,
    features-service,
    unified-trading-pm,
  ]
scope: [engineer]
assigned_vm: NA
execution_scope: local-only
tags: [defi, karak, decommission, restaking, venue-removal]
priority: P1
source: operator-request-2026-08-16
parent_epic: defi_master
related:
  [
    /plans/active/issues/e2e_wiring_reachability_audit_2026_08_15.md,
    /plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md,
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
    /plans/archive/issues/symbiotic_venue_onboarding_2026_08_16.md,
  ]
created: 2026-08-16
resolved_by:
locked_by:
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/active/issues/e2e_wiring_reachability_audit_2026_08_15.md,
    execution-service/execution_service/defi_execution/protocols/karak.py,
    /codex/02-data/entity-rename-and-split-consumer-migration-rule.md,
  ]
---

# Decommission Karak entirely from the codebase

## Why (evidence, measured 2026-08-16, this session)

- **The address is wrong, not just low-confidence.** `execution_service/defi_execution/protocols/karak.py`'s own
  docstring already flagged `WSTETH_VAULT`/`CORE_ADDRESS` (`0x399f22ae52a18382a67542b3De9BeD52b7B9A4ad`) as "LOW
  confidence — may be a placeholder." Live on-chain verification (real Ethereum mainnet RPC, block 25,765,709)
  confirmed it: **zero deployed bytecode at that address.** A live `deposit()` against it would either revert or,
  worse, silently misdirect funds depending on tx type.
- **The real product is architecturally different.** Karak's actual wstETH restaking exposure is "King Karak"
  (weETHk, `0x7223442cad8e9cA474fC40109ab981608F8c4273`, verified real contract, `totalSupply` = 703.9 shares) — a
  Veda/BoringVault wrapper (separate `Accountant`/`Teller`/`Lens`/`DelayedWithdraw` contracts). `karak.py`'s
  `deposit()`/`withdraw()` assume a single ERC4626 `vault.deposit()` call; the real flow goes through the Teller
  contract instead. Fixing the address alone would not make the connector correct — the write path needs rebuilding.
- **Scale comparison.** Symbiotic's comparable DefaultCollateral wstETH vault (a REAL, verified contract,
  `0xC329400492C6ff2438472D4651Ad17389fCb843a`) holds 16,349 wstETH — roughly 20x Karak's King Karak deposits in the
  one pool measured. Both cover the same `CARRY_AVS_CONTINUOUS`/restaking-yield archetype role
  (`restaking-reward-economics.md`); Symbiotic is the larger, structurally-simpler, address-correct venue to build
  out instead. See `/plans/archive/issues/symbiotic_venue_onboarding_2026_08_16.md`.
- **Operator ruling, 2026-08-16**: decommission Karak entirely rather than rebuild — do not leave a half-correct,
  wrong-address connector in the tree (same "complete-looking uncalled/broken component" defect class this
  workspace has already spent several sessions closing, per `e2e_wiring_reachability_audit_2026_08_15.md`).
- **Cross-doc conflict, resolved 2026-08-16 (this note)**:
  `/plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md` (authored 2026-08-14, two
  days before this decision) lists Karak among the 20 protocol connectors it says need wiring into real dispatch
  (its "never instantiated anywhere" list). That direction is SUPERSEDED by this doc for Karak specifically — do
  not wire Karak per that doc's framing; delete it per this doc instead. That doc now carries a pointer back here so
  a reader hitting Karak in its list does not wire up a connector this doc says to remove.

## Scope — every reference found (full-workspace grep, 2026-08-16)

Per `/codex/02-data/entity-rename-and-split-consumer-migration-rule.md`: enumerate every consumer in the SAME
change — a token grep alone misses path-prefix/filename/registry-membership binders, so each file below needs a
**read**, not a blind delete, to catch the non-token forms (a `karak.py` filename, a dict key, a docstring citation).

### execution-service — delete the connector + its wiring

- [ ] [AGENT] P1. **Delete `execution_service/defi_execution/protocols/karak.py`** (the connector itself — confirmed
      wrong address, unreachable per this session's own audit table).
- [ ] [AGENT] P1. **Remove Karak from `execution_service/defi_execution/protocols/__init__.py`** (import + `__all__`
      re-export).
- [ ] [AGENT] P1. **Remove Karak references from `execution_service/defi_execution/protocols/base.py`** (check for a
      docstring/comment mention, not necessarily code).
- [ ] [AGENT] P1. **Remove Karak from the yield-stream modules**: `matching_engine/yield_streams/restaking_avs.py`,
      `matching_engine/yield_streams/seasonal_points.py`, `matching_engine/yield_streams/__init__.py` — these model
      `CARRY_AVS_CONTINUOUS`/`CARRY_ISSUER_SEASONAL` reward sources; Karak is likely one enum/dict entry among several
      (EigenLayer, Ether.fi, Puffer, etc.) — remove the Karak entry only, do not touch siblings.
- [ ] [AGENT] P1. **Check `execution_service/custody/pre_trade_pinger.py`** and
      `execution_service/cli/defi_carry_recursive_staked_decision_trace.py` for Karak references (likely a venue-name
      literal in an archetype trace or custody allowlist) and remove.
- [ ] [AGENT] P1. **Delete `tests/unit/test_karak_connector.py`**; remove Karak-specific cases from
      `tests/unit/test_defi_base_connector.py` and `tests/unit/defi_execution/test_connector_live_capability.py`
      (these are likely parametrized-by-venue tests — remove the Karak parameter, keep the test structure).

### strategy-service — position read side

- [ ] [AGENT] P1. **Delete `strategy_service/position/position_interface/adapters/karak.py`** and remove its
      registration from `position_interface/factory.py` + `position_interface/__init__.py` +
      `position_interface/capabilities.py`.
- [ ] [AGENT] P1. **Remove Karak from strategy archetypes**: `engine/strategies/v2/base.py`,
      `engine/strategies/v2/carry_and_yield/staked_basis.py`, `engine/strategies/v2/carry_and_yield/recursive_staked.py`
      — read each carefully; Karak may appear in a `venue_universe` list alongside Symbiotic/EigenLayer/etc., remove
      only the Karak entries.
- [ ] [AGENT] P1. **Remove Karak from `pnl/engine/reward_attribution.py`** (reward-source attribution, mirrors the
      execution-service yield_streams change above).
- [ ] [AGENT] P1. **Update/remove Karak cases in** `tests/position/position_interface/unit/test_defi_adapters.py` and
      `tests/position/position_interface/unit/test_bespoke_defi_readers.py`.

### instruments-service — reference data

- [ ] [AGENT] P1. **Delete `instruments_service/reference_data/adapters/defi/karak.py`**; remove its registration
      from `reference_data/factory.py` and `engine/orchestrator/defi.py`.
- [ ] [AGENT] P1. **Delete `tests/unit/reference_data/adapters/defi/test_karak_metadata.py`**; update
      `tests/unit/scripts/goldens/expected_universe/defi.json` (a golden fixture — Karak's expected-universe entries
      must be removed, not just the adapter, or this golden test will fail on the removal) and
      `tests/unit/reference_data/adapters/defi/test_instrument_type_filter_regression_2026_07_08.py` if it
      parametrizes over Karak.
- [ ] [AGENT] P2. **Update `docs/DEFI_INSTRUMENTS.md` and `docs/ADAPTER_ARCHITECTURE.md`** to drop Karak from the
      documented adapter list; update `scripts/enumerate_expected_universe.py` if it hardcodes a Karak entry.

### market-tick-data-service — batch capture

- [ ] [AGENT] P1. **Delete `market_interface/adapters/defi/restaking_karak_adapter.py`**; remove its registration
      from `market_interface/factory.py` and `market_interface/adapters/defi/__init__.py`.
- [ ] [AGENT] P1. **Remove Karak from** `cli/handlers/staking_yields_handler.py` and
      `cli/handlers/_lst_extended_rates.py` (yield/rate handlers likely iterate a venue list including Karak).
- [ ] [AGENT] P1. **Delete `tests/unit/market_interface/adapters/defi/test_restaking_karak_adapter.py`**; update
      `tests/unit/test_staking_yields_handler.py` and `tests/unit/test_lst_rates_handler.py` to drop Karak cases.

### features-service

- [ ] [AGENT] P1. **Remove Karak from `features_service/onchain/app/core/lst_seasonal_rewards_collector.py`**
      (likely a venue-keyed collector entry, same pattern as the execution-service/strategy-service reward-source
      removals above).

### unified-api-contracts — the SSOT registrations (do this FIRST, or the other repos' removals will hit dangling references)

- [ ] [AGENT] P0. **Remove Karak from every registry file that declares it as a real venue**:
      `registry/defi_venues.py`, `registry/venue_constants.py` (the `KARAK` constant + any `AVS`/restaking groupings
      it belongs to), `registry/venue_adapter_keys.py`, `registry/capability_declarations/_defi.py`
      (`VENUE_DATA_TYPE_CAPABILITIES` entries), `registry/defi_venue_capabilities.py`, `registry/expected_coverage.py`,
      `registry/chain_env.py` (if it carries Karak-specific chain/launch-date data).
- [ ] [AGENT] P0. **`registry/lst_token_addresses.py`** — Karak's wstETH vault address was never migrated here (it's
      wrong/unreachable at the execution-service level), but check no entry was added at any point; if one exists,
      remove it.
- [ ] [AGENT] P1. **Remove Karak from non-registry UAC modules**: `canonical/crosscutting/mvp_scope.py`,
      `internal/architecture_v2/restaking_rewards.py`, `internal/domain/strategy_service/pnl.py`,
      `internal/domain/defi/sim_schemas.py`, `internal/domain/defi/lst.py`, `internal/reference/instrument_validation.py`,
      `testing/vcr_endpoints.py`.
- [ ] [AGENT] P2. **Update `ui-reference-data.json`** (a generated/static UI reference file — check whether it's
      regenerated by a script or hand-maintained before editing) and
      `external/defillama/mocks/protocols.yaml` (a test-fixture mock, drop the Karak entry).

### unified-trading-pm — documentation

- [ ] [AGENT] P2. **Update codex docs** that list Karak as an active/planned venue: `/codex/09-strategy/architecture-v2/
      cross-cutting/pnl-attribution.md`, `/codex/09-strategy/architecture-v2/cross-cutting/restaking-reward-economics.md`,
      `/codex/09-strategy/architecture-v2/archetypes/carry-recursive-staked.md`,
      `/codex/09-strategy/architecture-v2/archetypes/yield-staking-simple.md`, `/codex/04-architecture/
      transfer-coordinator.md`, `/codex/04-architecture/interface-credential-convention.md`,
      `/codex/04-architecture/amm-slippage-simulation.md`, `/codex/04-architecture/defi-execution-overview.md`,
      `/codex/02-data/defi-venue-protocol-catalogue.md`, `/codex/02-data/defi-data-type-taxonomy.md`,
      `/codex/02-data/availability-manifest-and-data-status.md`, `/codex/02-data/instrument-pipeline-defi.md` — remove
      Karak from venue lists/tables; where a whole section is Karak-specific, delete the section (don't leave a
      stub referencing removed code).
- [ ] [AGENT] P3. **Do NOT edit `plans/archive/**`** — archived plans are historical record, not live documentation;
      Karak mentions there describe what was true at the time and should not be retroactively edited. Leave them.
- [ ] [AGENT] P2. **Update `scripts/quality_gates/reachability_gate_baseline.json`** if it carries a Karak entry
      (check first — it may already correctly show Karak as unreachable, in which case removing the venue makes the
      baseline row moot and it should be dropped, not left as a phantom entry for a venue that no longer exists).

## Verification (do not skip)

- [ ] [AGENT] P1. **Re-run the full-workspace grep from this doc's own discovery step** (`grep -rli "karak"` across
      all 8 repos) after the removal pass — it must return zero hits outside `plans/archive/` and this issue doc
      itself. A partial removal that still compiles/passes tests is not done; it just means nothing caught the
      residue.
- [ ] [AGENT] P1. **Each repo's own `quality-gates.sh` must be green** after its Karak removal, before shipping —
      this includes any golden-fixture tests (`expected_universe/defi.json` etc.) that will need their Karak rows
      dropped, not just the adapter code.
- [ ] [AGENT] P2. **Check for a Karak-specific ratchet-baseline entry** in any of the venue-coverage cascade
      baselines (`tests/data/execution_service_venue_reachability_baseline.json` and siblings) — Karak was never
      reachable, so it may or may not already appear there; if it does, remove the row (the venue no longer exists,
      so "unreachable" is moot, not resolved).

## Progress Log

- **/plan-reconcile ao 2026-08-22**: stripped the inline `# corrected 2026-08-21 ...` comment from the
  `parent_epic:` frontmatter line (rationale preserved: it was `security_and_cross_cutting_master`, corrected to
  `defi_master` by ag-closeout-audit's defi Phase 2 sweep, matching this doc's own `asset_group: [defi]`
  correction). `regen_backlog_from_plan.py`'s `parse_frontmatter_parent_epic` does not strip inline `#` comments
  (verified by reading it — no `.split("#")`, unlike the `status`/`execution_scope`/`sequential`/`effort`
  parsers), so the value was being read as the whole comment-laden string rather than `defi_master`. Same defect
  class as the `assigned_vm` instance fixed this pass in the two `dp_fetch_009_cefi_liquidations_*` docs.

- **2026-08-16**: issue authored. Full-workspace `grep -rli "karak"` across execution-service, unified-api-contracts,
  strategy-service, instruments-service, market-tick-data-service, market-data-processing-service, features-service,
  unified-trading-pm — confirmed 8 code/doc repos, ~50 files (listed above by repo). Not yet executed — scoped only,
  per operator's "Human" plan-destination ruling (assigned_vm: NA). MDPS had zero hits (Karak, like most DeFi LST/
  restaking venues, produces no candle-derivable market data MDPS processes — consistent with the Symbiotic
  onboarding doc's finding that MDPS is not a relevant layer for this venue shape).
- **na-eligibility-audit 2026-08-16** [body-hash:5eaa96c384a0defb]: KEEP-NA, valid — Brand-new issue doc (created 2026-08-16, today), read end to end: a full-workspace Karak-decommission sweep across 8 repos (~50 files), 27 open [AGENT]-tagged todos (P0-P3), every one a mechanically bounded delete-this-file / remove-this-entry / update-this-golden-fixture instruction with the design decision (decommission entirely, not rebuild) already made and justified (zero deployed bytecode at the hardcoded vault address, verified real-mainnet;.
- **context-scout 2026-08-17**: populated context_scope (3 entries).
- **context-scout 2026-08-20**: refreshed context_scope (3 entries).
