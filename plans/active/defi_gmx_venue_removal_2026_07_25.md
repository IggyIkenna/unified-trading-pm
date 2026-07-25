---
doc_type: plan
title: Remove GMX venue support (unreliable historical funding data + narrow usage)
summary:
  Operator decision 2026-07-25 -- GMX perp_funding's entire captured history (2022-2023) turned out to be a synthetic
  OI-imbalance proxy, not real funding-rate observations (the native subgraph query never worked for this window; every
  sample fell back to a derived market="all" heuristic). GMX is referenced in strategy-service's carry/ staked-basis
  catalog but flagged there as unverified ("GMX-V2 rows pending verification"), and is not foundational -- a bounded,
  real removal across UAC/MTDS/IS/execution-service/strategy-service/UTL plus a prod-bucket GCS+manifest purge and doc
  updates.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos:
  [
    unified-api-contracts,
    market-tick-data-service,
    instruments-service,
    execution-service,
    strategy-service,
    unified-trading-library,
    unified-trading-pm,
  ]
scope: [engineer]
tags: [defi, gmx, venue-removal, data-quality, cleanup]
related: [defi_consolidated_closeout_2026_07_18, defi_migrated_marker_flagged_root_cause_clusters_2026_07_25]
created: 2026-07-25
last_updated: 2026-07-25
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 2
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
source:
  [
    "operator decision 2026-07-25, made during a /autonomous session investigating FLAGGED delete_migrated_defi_markers
    dry-run results -- GMX perp_funding turned out to be entirely synthetic-proxy historical data (verified via direct
    parquet inspection across the full 2022-2023 range: funding_rate_long == -funding_rate_short on every sample, the
    signature of the Messari-fallback OI-imbalance formula, market='all' every time -- the native per-market subgraph
    query apparently never succeeded for this whole window). Cross-repo footprint (94 files matching /gmx/i across 6
    repos) checked via grep before scoping this plan; strategy-service usage confirmed real but explicitly flagged
    unverified in-code (staked_basis.py: 'GMX-V2 rows pending verification in UAC VENUE_COLLATERAL_MATRIX')",
  ]
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
---

# Remove GMX venue support

## Context (read before dispatching any todo)

Full root-cause analysis: `issues/defi_migrated_marker_flagged_root_cause_clusters_2026_07_25.md` (GMX section) and the
2026-07-25 chat/plan discussion in `defi_consolidated_closeout_2026_07_18.md`'s progress log. Short version: GMX's
`perp_funding` capture (`market-tick-data-service/market_tick_data_service/cli/handlers/_perp_funding_gmx.py`) has a
native path (`fundingRateChangedEvents`, real per-market data) and a Messari fallback (`financialsDailySnapshots`, no
per-market field, derives a synthetic `imbalance = (long_oi - short_oi) / total_oi` proxy written as `market="all"`).
Every sampled historical row (2022-2023, both chains) is the fallback shape -- the native query never worked for this
venue's whole captured history. Combined with GMX's own `GMX-V2 rows pending verification` caveat already in
`strategy-service/strategy_service/engine/strategies/v2/ carry_and_yield/staked_basis.py`, the operator decided to
remove GMX rather than invest in fixing/backfilling it.

**Each todo below is independently dispatchable and safe to run CONCURRENTLY** -- every todo targets a different repo,
so there is no same-file collision risk. `depends_on`/`gate_on_depends` is deliberately NOT set for the GCS-purge todo
(no per-todo prereq syntax exists) -- it is `[OPERATOR]`-tagged so it is never auto-dispatched anyway; the human running
it should simply wait until the code-removal todos below have landed first (nothing enforces this mechanically, it is
operator judgment on timing).

**Definition-of-done convention for every removal todo below**:
`grep -rli "\bgmx\b" <repo> --include="*.py" | grep -v test` returns zero hits, OR only hits inside a dated
changelog/docstring comment describing the historical removal itself (never inside live logic, registries, or enums).

## Todos

- [x] ✅ [DATA] P2. **Remove GMX from `unified-api-contracts`** -- unified-api-contracts@18d53d63. Actual footprint was
      wider than the ~30-file pre-scoping (word-boundary grep missed `gmx_v2`/`gmxv2` forms): 44 files across
      `registry/` (venue/adapter-key registries, `VENUE_COLLATERAL_MATRIX`, capability declarations, launch
      dates/cadence), `internal/architecture_v2/` (collateral/jurisdiction/order-semantics/simulation-assumptions/
      liquidation-bonus registries + the `_STAKED_HEDGE_VENUES`/`gmx_v2` eligible-venue-id entries in
      `archetype_leg_spec_seeds.py`), `internal/reference/`, `internal/schemas/`, `scripts/`, and test fixtures (incl.
      hardcoded registry-count assertions that dropped by 1 after the removal). Confirmed each hit per the todo's
      caveat: left GMX-the-CeFi-token-symbol in `cefi_instrument_universe.py` and GMX-the-Morpho-collateral- asset in
      `defi_reserve_params.py` untouched (different namespace, not the DeFi venue); left the
      `test_ws_cassette_coexistence.py` `gmx_arbitrum_ws` mapping in place pending the sibling market-tick-data-service
      todo's connector deletion (that test reads the READ-ONLY root MTDS clone, which still has the connector file --
      removing the mapping now would fail for an unrelated reason). Definition-of-done grep
      (`grep -rli '\bgmx\b' . --include="*.py"`) returns zero hits outside dated `2026-07-25` removal comments + the 2
      out-of-scope token entries + the 1 documented pending-sibling-todo mapping. `bash scripts/quality-gates.sh` green
      (11925 passed, 0 failed, exit 0).
- [x] ✅ [BACKEND] P2. **Remove GMX capture from `market-tick-data-service`** -- market-tick-data-service@68407ae5.
      Deleted `_perp_funding_gmx.py` + `gmx_arbitrum_ws.py`; stripped gmx dispatch from `perp_funding_handler.py`
      (DEFAULT_PROTOCOLS, GMX subgraph queries, `_run_process` branch, class stage-bindings, `preflight()`'s graph-key
      loading), `dex_pools_handler.py`'s protocol table, `_dex_pools_subgraph.py`'s query-selection map,
      `liquidations_handler.py` + `_liquidations_queries.py` (GMX liquidation capture -- found beyond the todo's
      explicit scope via the repo-wide grep, in-scope under "remove GMX capture"), `_instruments_metadata.py`'s
      chain/address map, the connectors registry, `subgraph_health_probe.py`, `data_manifest_handler.py` + `cli/main.py`
      doc/help strings. Removed/updated GMX-specific test coverage (`test_perp_funding_handler_coverage.py` +
      `test_perp_funding_normalization.py` deleted -- fully GMX-scoped; `test_perp_funding_handler.py`,
      `test_liquidations_handler_coverage.py`, `test_cf11_swallow_remediation.py`,
      `test_defi_lst_perp_specialty_ws_scaffolds.py` trimmed). Verified via the definition-of-done grep convention (zero
      hits outside dated `2026-07-25` changelog comments in non-test `.py`; dated one-off migration scripts under
      `scripts/one_offs/` and `market_tick_data_service/scripts/` left untouched as historical artifacts, out of
      "capture" scope). Evidence: `bash scripts/quality-gates.sh` exit 0 (6905 passed, 0 failed).
- [x] ✅ [DATA] P2. **Remove GMX from `instruments-service` reference data / MVP instrument universe** --
      `engine/orchestrator/defi.py`, `scripts/enumerate_expected_universe.py`,
      `scripts/dex_pool_glued_pair_id_canonicalize_2026_07_09.py`. Done-when: the definition-of-done convention above,
      zero hits. (repo: instruments-service) -- instruments-service@0214bb3c (+ reference_data/factory.py, not in the
      original pre-scoped list but matched the repo-wide grep). Cross-repo drift-guard note: also fast-forwarded onto
      unified-api-contracts@18d53d63 (todo -001, since instruments-service's
      `test_defi_set_equals_uac_denominator_drift_guard` set-equality invariant required it) and reconciled with a
      concurrent fix (8df301f4, golden fixture + rule11 dedup count already regenerated upstream). Evidence:
      `bash scripts/quality-gates.sh` exit 0 (4888 passed, 0 failed, coverage 88.59%). **Third concurrent-dispatch
      cleanup** -- instruments-service@2de3418e (slot-3, discovered 0214bb3c/8df301f4 already landed mid-session;
      reconciled via 3-way conflict resolution rather than blind-overwrite, keeping the peers' dated-changelog-comment
      style). Residual GMX references beyond the peers' scope: `docs/DEFI_INSTRUMENTS.md` (multiple current-tense "GMX
      is a supported DEX-pool protocol" passages -- adapter architecture counts 13->12/8->7, protocol x chain coverage
      table row, known-gaps `GMX-AVALANCHE` entry, `DEX_VENUE_KEYWORDS` list, Graph-sourcing table row; historical dated
      2026-07-09 migration-results table left untouched as a genuine historical record),
      `tests/unit/test_orchestrator_coverage.py` (`GMX-ARBITRUM` used only as an arbitrary example venue in
      `test_cefi_tradfi_below_half_ratio_is_flagged`, renamed to `RADIANT-ARBITRUM` -- no GMX-specific behavior was
      under test), `tests/unit/scripts/test_enumerate_expected_universe_v2.py` (docstring rationale claiming
      `perp_funding` legitimately appears in the POOL union "because GMX" -- now false since GMX was the only POOL
      protocol declaring `perp_funding`, updated to a dated-removal note), and
      `scripts/dex_pool_glued_pair_id_canonicalize_2026_07_09.py`'s "8 protocols that share
      UniswapV3ReferenceDataAdapter" comment (peers' commit updated the docstring/set counts to 12/7 but missed this one
      inline comment, left at stale "8"). Verification: `grep -rli "\bgmx\b" . --include="*.py" | grep -v test` zero
      hits; full-repo (incl. tests) grep shows only dated 2026-07-25 changelog comments. Evidence:
      `bash scripts/quality-gates.sh --no-fix` exit 0 (4888 passed, 7 skipped, 0 failed, sentinel matches HEAD).
- [x] ✅ [BACKEND] P2. **Remove GMX from `execution-service`** -- `service_config.py`, the 4
      `cli/defi_*_decision_trace.py` scripts (carry_staked_basis / carry_basis_perp / arbitrage_dispersion /
      liquidation_capture) that reference GMX, `custody/pre_trade_pinger.py`. Done-when: the definition-of-done
      convention above, zero hits. (repo: execution-service) -- execution-service@09a828ed. Also updated
      tests/e2e/test_defi_execution_e2e.py (stale GMX venue-coverage assertions).
      `grep -rli "\bgmx\b" . --include="*.py"` returns zero hits repo-wide (incl. tests).
- [x] ✅ [BACKEND] P2. **Remove GMX from `strategy-service`** -- the `("gmx", "GMX", ShareClass.USDC)` entry in
      `engine/strategies/v2/target_universe/catalog_carry.py`, GMX chain/config entries in
      `engine/strategies/v2/carry_and_yield/staked_basis.py` (including the "GMX-V2 rows pending verification" comment,
      which becomes moot once removed), any GMX rows in `catalog_directional.py`/`catalog_staked_basis.py`, the
      venue-name-casing comment mentioning GMX in `engine/core/canonical_perp_funding_provider.py` (cosmetic, update if
      it reads oddly without GMX), and the 3 trace/probe scripts
      (`trace_arbitrage_price_dispersion.py`/`probe_funding_rate_dispersion_coverage.py`/`trace_all_carry_archetypes.py`)
      if they hardcode GMX. Done-when: the definition-of-done convention above, zero hits. (repo: strategy-service) --
      strategy-service@ca818ff8. Also removed the now-dead `"gmx": "arbitrum"` staking_protocol alias and updated 4
      tests in `test_target_universe.py`/`test_canonical_perp_funding_provider.py` that asserted GMX-specific
      catalog/alias behavior (GMX never had LST collateral acceptance, so CARRY_STAKED_BASIS slot count is unaffected;
      CARRY_BASIS_PERP -13 slots, ML_DIRECTIONAL_CONTINUOUS DeFi perps -2 slots, both within the existing
      `_TARGET_MIN`/`_TARGET_MAX` band). `quality-gates.sh` green (108s, exit 0).
- [x] ✅ [BACKEND] P3. **Remove GMX from `unified-trading-library`** -- any shared constants/registries referencing GMX
      (3 files matched pre-scoping). Done-when: the definition-of-done convention above, zero hits. (repo:
      unified-trading-library) -- unified-trading-library@f22e516f. Removed the `GMX` venue override
      (`pipeline_mode_resolver.py`), the `gmx` APY seed (`core/mock_defi_dynamics.py`), and `GMX` from the DeFi venue
      frozenset (`ml/models.py`). `grep -rli "\bgmx\b" . --include="*.py"` returns zero hits repo-wide (incl. tests).
      `quality-gates.sh` green (146s, exit 0).
- [ ] [OPERATOR] P1. **Purge GMX GCS objects + manifest rows** -- delete every `raw_tick_data/**/venue=GMX/**` object
      (all chains, all data_types: `perp_funding`, `derivative_ticker`, any `dex_pool_state` entries from the `gmx`
      protocol table) in `market-data-tick-defi-prd-central-element-323112`, and the corresponding manifest rows.
      Prod-bucket delete, human-gated per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` -- no agent runs
      this. Do this AFTER the code-removal todos above have landed (so nothing still tries to read GMX data mid-purge)
      -- operator judgment on exact timing, not machine-gated. Done-when: zero `venue=GMX` objects remain in the bucket,
      manifest shows zero rows for venue=gmx. (repo: market-tick-data-service)
- [x] ✅ [DOC] P2. **Update documentation referencing GMX** -- any codex docs, this plan's parent
      (`defi_consolidated_closeout_2026_07_18.md`), and related issue docs that describe GMX as active/supported.
      Done-when: a grep across `codex/` + `plans/active/` for "GMX" shows only historical/changelog-style references
      (e.g. this plan itself, the root-cause issue doc), none describing it as a currently-supported venue. (repo:
      unified-trading-pm) -- unified-trading-pm@bfda5df5b. Fanned out to 6 sub-agents covering 26 codex docs + 15
      plans/active docs (40 files changed, 1 excluded: `instrument_id_format_canonicalization_2026_07_08.md` was already
      1309L, over the 1000L hard cap pre-existing this change -- deferred, not shipped). Each mention was judged
      CURRENTLY-ACTIVE (edited to a removal note) vs. HISTORICAL/dated (left unchanged to preserve the audit trail);
      `defi_consolidated_closeout_2026_07_18.md` and the root-cause issue doc
      (`issues/defi_migrated_marker_flagged_root_cause_clusters_2026_07_25.md`) both received targeted annotations.

## Codex SSOTs

- `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` -- governs the GCS-purge todo.
- `/codex/02-data/defi-canonical-naming-ssot.md` -- update if it lists GMX as a supported venue.
