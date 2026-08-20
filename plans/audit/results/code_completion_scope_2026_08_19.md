---
doc_type: audit-result
title: Code-completion scope — instruments-service, unified-api-contracts, unified-trading-library, MDPS, features-service, strategy-service, execution-service — 2026-08-19
summary: >-
  Per-repo inventory of everything NOT code-complete across the seven services, filtered against
  system_readiness_master.md's five-item allowlist (backfills, venue connectivity, market-data-live, testnets,
  archetype real-data testing). Everything else not code-complete is remaining work. Sources the known-P0 corpus
  plus ~65 sampled plans/issues and two direct code spot-checks; explicitly discloses what was read in full vs
  sampled vs not assessed.
status: partial
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    instruments-service,
    unified-api-contracts,
    unified-trading-library,
    market-data-processing-service,
    features-service,
    strategy-service,
    execution-service,
  ]
scope: [engineer, admin]
tags:
  [
    code-completeness,
    readiness,
    dispatch-scope,
    strategy-archetype,
    registry-hardening,
    execution-service,
  ]
related:
  [
    /plans/epics/system_readiness_master.md,
    /plans/active/issues/uac_get_venue_asset_group_silently_returns_cefi_for_all_venues_2026_08_19.md,
    /plans/active/issues/three_chain_registries_disagree_none_authoritative_2026_08_19.md,
    /plans/active/issues/execution_delta_proxy_repricer_generalization_2026_08_18.md,
    /plans/audit/results/registry_ground_truth_2026_08_19.md,
  ]
created: 2026-08-19
last_updated: "2026-08-19"
date: 2026-08-19
severity: P0
audited_scope: >-
  plans/active/*.md and plans/active/issues/*.md filtered to the seven named repos, scoped to code/data/
  connectivity/security only — CI/CD, agent-orchestrator, cost-saving and cloud-migration explicitly excluded.
  Deployment counted only where it changes backfill throughput or alters manifest/shard definitions.
auditor: >-
  Interactive session slot 6, read-only scoping pass. Cross-referenced against plans/epics/system_readiness_master.md
  (W1-W22), sampled ~45 issue docs and ~20 plan docs in the seven-repo candidate set (199 candidate plans / 228
  candidate issues total matched on repo name), and ran two direct code spot-checks against strategy-service.
resulting_plan:
lib_version:
doc_versions_checked:
parent_epic: system_readiness_master
assigned_vm: NA
execution_scope: local-only
priority: P0
locked_by:
locked_since:
resolved_by:
source: >-
  plans/epics/system_readiness_master.md § "Definition of done" (operator ruling 2026-08-19), cross-referenced
  against the candidate plan/issue set produced by grepping plans/active/*.md and plans/active/issues/*.md for the
  seven repo names in their first 40 lines.
---

# Code-completion scope — seven services, 2026-08-19

## The goalpost, restated

Per `plans/epics/system_readiness_master.md` § "Definition of done" (operator ruling 2026-08-19): when this is done,
everything is complete **in code**. The only things that may still be pending are (1) backfills still running,
(2) venue connectivity — private/public feed, orders and trades, (3) market data live, (4) testnets where they
exist, (5) strategy archetypes code-ready for batch/paper/live pending real-data testing. Anything else not
code-complete is remaining work. That is the filter applied below — not "does the doc match reality," but "is this
in code yet, and if not, is it on the five-item list."

**Scope filter applied**: code / data / connectivity / security only. CI/CD, agent-orchestrator, cost-saving and
cloud-migration items were excluded even where a plan/issue touched one of the seven repos (e.g. `breaking_change_
differ_blind_to_registry_data_dicts`, `mdps_qg_tests_slice_oserror_cannot_send_recurrence2`, `defi_compute_gcp_
migration`). Deployment-layer items were kept only where they gate backfill throughput or manifest/shard shape
(e.g. `manifest_writer_per_vm_shard_flush_scales_with_shard_size`). `market-tick-data-service` (MTDS) is **not** one
of the seven named repos even though the epic's own pipeline table treats it as a distinct stage between
instruments-service and MDPS — MTDS-primary items are out of this report by the letter of the ask; flagged once
under "Scope note" below rather than silently absorbed.

## Known P0s (already filed — cited, not re-derived)

- **`/plans/active/issues/uac_get_venue_asset_group_silently_returns_cefi_for_all_venues_2026_08_19.md`** —
  `unified_api_contracts.execution.get_venue_asset_group()` does `_VENUE_ASSET_GROUP.get(venue.lower(), "cefi")` —
  every unresolved venue (AAVE_V3-ARBITRUM, LIDO-ETHEREUM, JUPITER-SOLANA, MORPHO-BASE all tested) silently returns
  `"cefi"`. No exception, no `None` — a caller cannot tell a real hit from a miss. Any per-asset-group split routed
  through this function is wrong.
- **`/plans/active/issues/three_chain_registries_disagree_none_authoritative_2026_08_19.md`** — `ChainKind` (23,
  missing `plasma`, which has live venues) / `KNOWN_CHAINS` (10, missing `scroll` and `starknet`, both live) /
  `VENUE_CHAIN_MAP` (4, covering 15 of 192 declared venues) give three different chain counts, none complete.
- **`/plans/active/issues/execution_delta_proxy_repricer_generalization_2026_08_18.md`** — the strategy→execution
  reference triple (price / position / credit) is designed, not built. `execution_service/engine/delta_proxy_
  repricer.py` implements the price leg only (`DeltaProxyRepricer` + `QuoteMaintainer`, real dataclasses + unit
  tests); `reference_position` and `credit` do not exist on `StrategyInstructionEnvelope`. Blocked on UAC's
  `QuoteInstruction` carrying no `delta`/`gamma`/`underlying_instrument_id`, and on the strategy-side receipt point
  (`QuoteHandler`) having been deleted 2026-08-15 as dead code with no replacement.
- **Archetype code-completeness** (`cursor-configs/skills/archetype-code-completeness/`, run live 2026-08-19 against
  60 `StrategyArchetype` members × 3 modes): rollup ~6 ready / ~47 not_ready / ~7 unverified per mode. Only
  **32/60 archetypes have a v2 engine registered at all** (`ARCHETYPE_ENGINE_REGISTRY`) — **spot-checked directly
  against `strategy-service/strategy_service/engine/strategies/v2/factory.py` in this session: exactly 32 entries,
  and neither `MARKET_MAKING_PASSIVE_SPREAD` nor `VOL_STRADDLE` nor any `CARRY_AND_YIELD` member appears**, matching
  the plan-of-record's own claim that those engines are shipped-as-code but deliberately withheld from registration.
  `VOL_TRADING` 18/19 and `PORTFOLIO` 4/4 have no registered engine; `CARRY_AND_YIELD` is 0/11.

## How to read the tables

**Size**: S = under a day, M = 1-3 days, L = 3-7 days, XL = needs its own phased plan. Rough, not measured against
a real estimate. **Blocked-external**: Y = genuinely gated on something outside engineering control (an operator
judgment call, a vendor credential, a cross-repo dependency that must land first) — these are NOT dispatchable as-is;
an AO worker given one will either stall or invent an answer. N = the worker can execute today given the cited
evidence.

---

## instruments-service

| Item | What's missing | Evidence | Size | Blocks | Ext. blocked |
| --- | --- | --- | --- | --- | --- |
| `InstrumentRecord` schema completeness + `extra='forbid'` | ADD/REMOVE field reconciliation against adapter kwargs not done; `extra='forbid'` not flipped — adapter kwargs are still silently dropped on mismatch | `/plans/active/instrument_record_schema_completeness_extra_forbid_2026_07_18.md` (4 open todos, lines 115-130) | M | W14 (exchange contract fidelity), silent data loss on any adapter kwarg drift | N |
| Instruments schema not locked/versioned (B23) | No `INSTRUMENTS_SCHEMA_VERSION` constant, no `schema_version` field on `SchemaContract`, per-AG contracts synthesized but never consulted by any writer/reader, no golden/hash test to catch a silent column change | `/plans/active/issues/instruments_schema_not_locked_versioned_2026_08_18.md` (4-part fix, all open, lines 78-95) | M | Any future schema change ships undetected | N |
| Instruments catalogue — definitions aggregation + field-change history | Design not yet ratified; monthly-grain definitions aggregation, mutable-field declaration, field-change log, point-in-time-equivalence proof all unbuilt | `/plans/active/instruments_catalogue_definitions_and_field_history_2026_08_17.md` (9 open todos, lines 196-253) | L | Downstream consumers still derive/hardcode instrument attributes instead of querying the catalogue | **Y** — P0 OPERATOR todo ("ratify or replace this design") gates everything else in this plan |
| Golden/red DeFi capability drift | `test_expected_matches_golden[defi]` failing fleet-wide, same failure class as an already-archived 2026-08-05 incident; root UAC commit identified but current red/green state not re-verified in this pass | `/plans/active/issues/instruments_service_defi_golden_red_capability_drift_2026_08_14.md` (0 open todos tracked — diagnosis only, no fix committed to a checkbox) | S | Fleet-wide CI-adjacent gate on instruments-service | **unverified** — flagged, not independently re-confirmed this session |
| AAVEV3 bare-alias enumerator bug | Root cause fixed (`chain_env.py` duplicate dict key + missing alias canonicalisation) — code portion is DONE; 46,300 bad `empty_confirmed` manifest rows still need an operator-gated `--apply` delete | `/plans/active/issues/defi_aavev3_bare_alias_enumerator_bug_2026_08_08.md` | S (data only) | — | **Y** (operator delete sign-off) — code itself is complete |
| Foundation / completion-tracker / G1-G5 gate / MTDS-consistency / CF-canonicalization plans | Sampled by title only, not read in depth this pass — `instruments_foundation_completeness_2026_06_24`, `instruments_completion_tracker_2026_07_06`, `instruments_foundation_phase0_cross_cutting_2026_07_24`, `instruments_mtds_consistency_remediation_residuals_2026_07_24`, `instruments_store_cf_canonicalization_single_walk_2026_07_24`, `instruments_cefi_g1_g5_gate_execution_2026_07_24`, `instruments_tradfi_g1_g5_gate_execution_2026_07_24`, `is_catalogue_g1_root_audit_log_2026_07_24` | titles + open/done counts only | unknown | likely mostly data/manifest canonicalisation (allowlist-adjacent) | **not assessed** |

## unified-api-contracts

| Item | What's missing | Evidence | Size | Blocks | Ext. blocked |
| --- | --- | --- | --- | --- | --- |
| `get_venue_asset_group()` silent CeFi fallback | See Known P0 above | issue cited | S-M | Any per-asset-group split computed through this function | N |
| Three chain registries disagree | See Known P0 above | issue cited | M | Any chain-scoped coverage/readiness figure | N |
| Registry SSOT hardening — venue→chain overlap + `VenueFeature`/`VenueCapability` vocabulary overlap | A "sixth concern" venue→chain SSOT overlap (P1) directly adjacent to the chain-registry P0 above, plus an unresolved enum-vocabulary overlap (P2) | `/plans/active/registry_ssot_hardening_2026_08_16.md` (2 open todos, lines 145-158) | M | Same blast radius as the chain-registry P0 — should land in the same change | N |
| `canonical_path_violations()` blind to filename stem | The oracle drops the last path segment before validating; raw venue wire stems and double-wrapped catalogue-miss ids return 0 violations == CANONICAL when they are not | `/plans/active/issues/canonical_path_oracle_blind_to_filename_stem_2026_07_20.md` (open todos still at lines 440-452) | M | Every canonical/non-canonical claim made via the oracle for non-tradfi shapes | N |
| Data-type-validity combinator fragmented per asset group | No asset group has a genuine `(venue, instrument_type) -> data_types` combinator; CEFI/DeFi/TradFi/Sports/Prediction each patch it differently, TradFi produces a provably-wrong cell (CME==ICE despite ICE having no Databento coverage) | `/plans/active/issues/uac_data_type_validity_combinator_fragmentation_2026_07_07.md` — remaining open todos are now data-backfill-flavored (lines 975+), suggesting the code-level fragmentation fix has landed but was not independently re-verified this session | unknown | Correctness of every valid-data-types check | **unverified** |
| Coverage-floor registries don't cross-propagate | Three parallel coverage-floor registries; sports registries 1 and 3 are structurally one SSOT, but cross-asset-group propagation gap remains open | `/plans/active/issues/coverage_floor_registries_no_cross_propagation_2026_07_17.md` | M | Coverage-start dates used inconsistently across MTDS pre-skip / ManifestWriter pre-launch guard | N |
| `OrderState` (23-doc SSOT) vs shipped `OrderStatus` (UAC) | Doc claims a 9-state `OrderState`; UAC ships a 7-member `OrderStatus`. Ruled 2026-08-06 (Option A: advance the contract), confirmed 2026-08-12 — CODE todo and TEST todo both still open | `/plans/active/issues/order_state_machine_ssot_vs_uac_orderstatus_2026_07_31.md` (lines 102, 112) | M | W11 order-lifecycle state fidelity in execution-service | N — ruling already made, just needs building |
| W5 — collateral/margin schema populated | `VenueCapabilityV2.collateral_rules`/`MarginSpec` schema exists and is already consumed by strategy-service risk-v2, but **zero venues have it populated** | epic W5, `/plans/audit/results/venue_transfer_custody_collateral_research_2026_08_18.md` | L | Every risk-v2 read degrades silently to "no data" | N — population work, not design |
| W5 — transfer-capability eligibility flags | No field on `VenueCapabilityV2` (or elsewhere) declares Copper/Ceffu/manual-transfer/prime-broker eligibility per venue — needs new fields, not just population | epic W5 | M | Transfer routing / W22 external instruction API | N |
| W8 — weightings SSOT | "Define which dimension each weighting applies to, in the contracts registry as SSOT" — P0, open in the epic, **no dedicated owning plan found in this pass** | epic W8 | M | Portfolio/coin/venue weighting correctness | **corpus gap — needs a plan authored** |
| `uac_per_venue_seed_fallback_removal_deferred` | Operator ruled 2026-07-26 to KEEP the fallback (not remove) — this is a closed decision, no residual action | `/plans/active/issues/uac_per_venue_seed_fallback_removal_deferred_2026_07_26.md` (0 open todos) | — | — | **CODE-COMPLETE / closed-by-ruling** |
| Master data canonicalisation migration catalogue | Large coordinator doc (26 done / 2 open) — sampled only, not read in depth | `/plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md` | unknown | likely mostly done | **not assessed in depth** |

## unified-trading-library

| Item | What's missing | Evidence | Size | Blocks | Ext. blocked |
| --- | --- | --- | --- | --- | --- |
| `PATH_REGISTRY` silently drops the `mode=` kwarg | `execution_fills`/`positions`/`strategy_instructions`/`pnl_attribution` path templates have no `{mode}` placeholder; `build_path()`'s bare `str.format` silently discards the unconsumed `mode=` kwarg real callers already pass — **batch/paper/live rows for the same (date, id) write to the IDENTICAL GCS path today, overwriting each other** | `/plans/archive/2026_08/issues/path_registry_dead_mode_kwarg_execution_fills_positions_strategy_instructions_pnl_attribution_2026_08_15.md` | M | Data integrity across every mode for 4 core artefact types — directly threatens the paper(W)==batch-rerun(W) determinism spine | **Y** — OPERATOR must decide the migration/backward-compat strategy (line 114) before the code change ships |
| 55 failing tests in `config_interface`/`cloud_interface` | **RESOLVED 2026-08-20** — symptom gone on direct re-run (1355 passed, 0 failed), stale-venv hypothesis ruled out by measurement. See `/plans/archive/2026_08/issues/unified_trading_library_config_interface_mass_test_failure_2026_08_15.md`. | `/plans/archive/2026_08/issues/unified_trading_library_config_interface_mass_test_failure_2026_08_15.md` | S-M | ~~Currently-red test suite~~ (resolved) | N |
| Manifest-writer per-VM shard flush scales with shard size | Full read-merge-reserialize-upload on every debounced flush; once a shard passes ~1M rows the flush takes longer than the debounce interval and the VM stalls near-zero-progress while looking healthy | `/plans/active/issues/manifest_writer_per_vm_shard_flush_scales_with_shard_size_2026_07_28.md` | M | Backfill throughput directly (in-scope per the deployment carve-out) | N |
| GCS client silent write failure | Wrong method names swallowed by a broad exception handler — cited in the epic as **already CLOSED/fixed** | epic W2 issue list | — | — | **CODE-COMPLETE** |
| Blocking GCS writes on the event loop, cross-asset-group | Sampled title only, not read | `/plans/active/issues/blocking_gcs_writes_on_event_loop_cross_asset_group_2026_07_18.md` (5 open) | unknown | likely a live-path latency/correctness bug | **not assessed** |

## market-data-processing-service

| Item | What's missing | Evidence | Size | Blocks | Ext. blocked |
| --- | --- | --- | --- | --- | --- |
| Multi-instrument candle bundle write race | When 2+ underlyings must land in the same shared `ticks.parquet` bundle for one day/timeframe/data_type cell, each is written via an independent overwrite with no download-existing/merge/re-upload step — concurrent per-instrument writes can silently drop rows. Hypothesis-stage: verification todo (does BYBIT 15s/1m still show only 1 `instrument_id`) still open | `/plans/active/issues/mdps_multi_instrument_bundle_write_race_hypothesis_2026_08_09.md` | M | Data completeness for every multi-underlying bundle | N |
| `--force` silently dropped on per-date subprocesses | **Already fixed** (`market-data-processing-service@e9f9819`) — remaining open todo is a data relaunch, not code | `/plans/active/issues/mdps_force_flag_dropped_subprocess_per_date_2026_08_08.md` | — | — | **CODE-COMPLETE** (residual is a backfill relaunch — allowlist item 1) |
| Adapter-protocol/polars-seam migration | Atomic single-PR migration across 18 adapter files sharing an ABC/Protocol boundary — correctly re-scoped from a small AO-eligible item to a dedicated implementation plan (not yet authored) | `/plans/active/issues/mdps_adapter_protocol_polars_seam_mis_scoped_ao_dispatch_2026_08_15.md` | L | Tech-debt / maintainability, not a correctness blocker | N — but needs a scoped plan before dispatch |
| W2 — manifest canonicalisation + skip logic, consolidator-freshness gating, orphan-shard consumption check | All three P0 items in the epic remain open with no single owning plan found in this pass (the gate register `data_pipeline_completion_2026_08_21.md` tracks the DATA side; the code-level "gate on index freshness and fail loudly" mechanism itself was not independently confirmed as shipped) | epic W2 | M-L | Backfill correctness fleet-wide | **unverified** |
| W3 — reconcile the shipped 3,960-shard denominator against the operator's deepest-grain ruling; readiness dump lacks `instrument_type`/`data_type` columns; `grain` field mislabelled | Three open P0/P1 items in the epic, not yet closed | epic W3 | M | Every coverage percentage; readiness-dump granularity | N |

## features-service

| Item | What's missing | Evidence | Size | Blocks | Ext. blocked |
| --- | --- | --- | --- | --- | --- |
| `corporate_actions` sourced from banned vendor Polygon.io | Live, dispatched calculator reads exclusively from `polygon_corporate_actions_adapter.py` — Massive-fka-Polygon.io is a fleet-wide banned vendor | `/plans/active/issues/features_service_corporate_actions_polygon_io_banned_vendor_2026_08_18.md` | M | W17 (fees/gas-adjacent post-MVP path), any artefact claiming corporate-actions coverage | **Y** — OPERATOR must decide the re-sourcing path (yfinance vs alternative) before the calculator can be rebuilt |
| Calendar domain invisible to honest-coverage manifest | `economic_events`/`forexfactory`/`corporate_actions`/`earnings_results` never call `record_captured` — zero manifest visibility into whether this data is captured, how completely, or when it last ran | `/plans/active/issues/features_service_calendar_domain_manifest_tracking_gap_2026_08_18.md` | S-M | Honest-coverage completeness claims for the calendar family | **Y** — needs a REVIEW decision first (does calendar belong in the Layer-1 expected universe at all) |
| 5 of 7 on-chain feature groups write byte-identical, zero-feature-column parquets stamped `captured=True`; 6 more false-`captured` rows with zero GCS objects; 4-repo vocabulary split for `feature_group` | P0. Partially closed (batch-6 todo 18 fixed one onchain path); root cause and remaining fix status for the rest not independently re-verified | `/plans/active/issues/features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md` | L | Data-correctness heartbeat (fabricated "captured" rows), plus 4-repo naming drift | **unverified** — needs a fresh read to confirm current state |
| `delta_one` dependency checker resolves the wrong PREDICTION bucket token | `_format_template_vars` does a naive `asset_group.lower()` with no abbreviation map; PREDICTION's real bucket uses `pred`, not the spelled-out name | `/plans/active/issues/features_delta_one_dependency_checker_prediction_bucket_token_wrong_2026_07_27.md` | S | `/data-pipeline-check-features` benchmark leg for PREDICTION | N |
| 3 code-shipped MEV engines (BACKRUN, JIT_LIQUIDITY, LIQUIDATION_BUNDLE) have no opportunity-detection feature producer | `features.get(key, 0.0)` silently defaults — engines are registered and "shipped" but cannot fire in a real paper/live run | `/plans/active/issues/mev_engines_opportunity_detection_signals_unproduced_2026_08_18.md` (cross-repo with strategy-service) | L | Live-readiness for 3 archetypes that otherwise read as done | N |
| MVP universe filter / VM tarball staleness | Sampled title only — "dropped every CeFi perpetual" claim not independently verified this session | `/plans/active/issues/features_universe_filter_settlement_suffix_and_vm_tarball_staleness_2026_07_27.md` (status=open, but 0 open/5 done todos shown — possibly already resolved and status stale) | unknown | unknown | **not assessed — status/checkbox mismatch flagged, needs a fresh look** |

## strategy-service

The largest body of open, genuinely code-level work of the seven repos.

| Item | What's missing | Evidence | Size | Blocks | Ext. blocked |
| --- | --- | --- | --- | --- | --- |
| Archetype engine registration (VOL_\*, MARKET_MAKING_\*) | See Known P0 — engines for most VOL_\* and MARKET_MAKING_\* variants are shipped as code + unit tests but deliberately **not registered** pending a passing backtest (registering without one "would make the matrix lie," per the plan's own words) | `/plans/active/v2_engine_venue_buildout_2026_06_15.md` (23 open todos) | XL in aggregate, but each variant is small once its data/model blocker clears | Archetype readiness matrix for ~20 archetypes | **Y for most** — genuinely gated on (a) an OPERATOR decision to authorize a Tardis backfill (currently "no backfill authorised"), which is item-5-adjacent ("pending testing with real data") but the AUTHORIZATION itself is an open judgment call, not a running backfill; (b) an unbuilt ML model variant for the `*_PREDICTION`/`*_ML_LEAN` engines (ml-service, outside this scope) |
| Strategy wizard / expansion overlays / config surface | Rank-buffer hysteresis, no-trade band, beta-hedge overlay, vol-target-at-book-layer all unimplemented; `CARRY_FUNDING_DISPERSION` missing from `PARAM_SCHEMA_REGISTRY`; 28/60 archetypes cannot be instantiated via the wizard; `risk_limits` untyped | `/plans/active/strategy_service_expansion_overlays_config_and_wizard_2026_08_12.md` (draft, 24 open todos) | XL | Epic W6 in full — "every archetype fully configurable... derivable from the wizard" | Mostly N; a few items need an OPERATOR decision (per-client config-surface key, funding-route capability-graph widening) |
| Strategy-service centralization fixes | 69 module-level reference-shaped constants need migrating to one of the 4 centralisation destinations; position-risk asset-group-agnostic core partially wired (DeFi health-factor gates now fail-closed per the 2026-08-18 ruling, but CeFi/TradFi leverage archetypes not yet inventoried against the same test); venue-eligibility generalization and mode-aware dispatch both await an operator design decision | `/plans/active/strategy_service_centralization_fixes_2026_08_16.md` (15 open) + `_finalize` (4 open) | L | W7 in full (anti-drift / centralisation) | Two OPERATOR-gated design decisions (lines 311, 315); rest is N |
| Two parallel position-risk mechanisms unreconciled | `DeFiHealthAggregator` (DeFi-only, not live-fed) vs the already-live, cross-service `margin_event_emitter.py`/`MarginEvent` — epic explicitly says converge on one **before any new archetype wires onto either** | `/plans/active/issues/defi_leverage_archetypes_health_factor_wrong_source_2026_08_16.md`, epic W7 | M | Gates further leverage-archetype work fleet-wide | N — but must land FIRST, see dispatch order |
| Live path has no stale-producer detection | If strategy-service goes down or stops publishing, execution-service does not detect it — the kill switch has 5 armed conditions, none is "an internal service went silent"; the dependency-health policy has 27 entries, zero are our own services, and it only alerts (zero actuator consumers) | `/plans/active/issues/live_path_has_no_stale_producer_revocation_2026_08_14.md` (P0) + `/plans/active/producer_silence_flatten_protocol_2026_08_14.md` (23 open / **0 done** — entirely unstarted) | L | Live-trading safety broadly — silent strategy-service outage currently triggers nothing | N — but see the one OPERATOR sub-item on the lightweight-launcher admission gate |
| Lazy/scoped loading refactor (UAC `__init__` restructure) | Layer 2 (UAC) is "the dominant blocker" — DeFi content interleaved with shared content in `__init__`; end state needs a scoped-build test | `/plans/active/lazy_scoped_loading_refactor_2026_08_16.md` (3 open) | L | Elysium carve-out (explicitly named as a hard blocker in that plan), general import-time cost | **Y** — P0 OPERATOR ruling on restructure scope gates the rest of the plan |
| Elysium carve-out — stubbed strategy-service | Per-interface resolution table, `UniverseService`/`ConfigVersionService`/`TreasuryService`/`ReconciliationService` stub specs, uniform stub shape, E2E connector completeness for the two real archetypes — none built yet | `/plans/active/elysium_carveout_stubbed_strategy_service_2026_08_12.md` (draft, 17 open) | XL | Elysium client artefact readiness | **Y** — two P0 OPERATOR gates (full E2E connector completeness; land lazy-loading refactor first) |
| Service config ownership + instruction contract | Mostly done (33/46 todos closed). Remaining: typed `client_configs` schema, schema-mechanism decision, gate-assertion decision, service-boundary contract writeup, a corrected false "done" claim in the archive | `/plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md` (draft, 13 open) | M | W6/W9 config surface | **Y** on 3 of the 13 — schema mechanism, gate-assertion shape, transfers-do-not-execute-in-prod path (explicit HIGH-severity funds decision) |
| PnL: 3 competing surfaces, 2 dead | `compute_pnl` (dead, right formula wrong keying/schema/sink), execution-alpha compute_handler (dead, zero readers), the real wired `paper_run_passive.py`/`paper_run_attribution.py`. Operator ruled Option B 2026-07-29; code todo still open | `/plans/active/issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md` | M | W13 PnL attribution correctness | N — ruling already made |
| Venue-eligibility gate is single-purpose | `venue_capabilities.py` only resolves venues for `carry_and_yield`'s perp-hedge leg; the other 8 in-scope families get `frozenset()` | `/plans/active/issues/venue_eligibility_hardcoded_outside_carry_and_yield_2026_08_16.md` | M | Every non-carry archetype's venue eligibility | **Y** — OPERATOR must decide the generalization shape |
| Position adapters lag execution connectors 8:~16 | strategy-service ships 8 DeFi position adapters against execution-service's ~16 live protocol connectors | `/plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md` (P0) | L | W1's strategy leg is an AND of position-adapter + archetype registration — this asymmetry caps the AND fleet-wide | N |
| Instrument-universe hot-swap position-state safety contradicted across docs | Codex says restart required; shipped code hot-swaps live with no restart/error | `/plans/active/issues/instrument_universe_hotswap_position_state_safety_unruled_2026_08_14.md` | S (once ruled) | Live position-state integrity during a universe change | **Y** — OPERATOR ruling required |
| Orphan-coverage design gaps: `strategy_orders`/`strategy_positions`/`strategy_pnl` have NO live writer at all | Dead code, zero production callers for one of three investigated surfaces; `backtest_results` genuinely untracked (no manifest of any kind); ml artefacts have a live writer with zero manifest coverage | `/plans/active/issues/strategy_ml_orphan_coverage_design_gaps_2026_08_03.md` | M | W18 canonical output paths | N |
| DeFi catalog/engine config-key contract drift | 14 archetypes were functionally dead (crashing/silent config-key mismatch, stubbed dependency); 9 DeFi ones mostly fixed, 5 more (sports/ML-directional/market-making/vol-options) correctly held xfail. One P2 design item ruled 2026-08-09, implementation status not re-confirmed | `/plans/active/issues/defi_catalog_engine_config_key_contract_drift_2026_07_23.md` | S (residual) | — | mostly **CODE-COMPLETE**, one residual item **unverified** |
| No venue/currency curtailment mechanism | `allowed_venues` config field is dead code; catalog and `archetype_leg_spec_seeds` describe the same domain with no cross-check | `/plans/active/issues/defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md` | M | Operator-level venue/currency risk controls | N |
| W8/W9/W10/W13/W16 (broad)/W18 — weightings, account-balance I/O, risk/exposure, PnL attribution across every dimension, universal fail-closed startup-readiness check, canonical output paths | All P0, all open in the epic; **no dedicated owning plan found for W8, W9, W10, the FULL W13, or W18** beyond the narrow PnL-engine fix above and scattered issue docs | epic W8-W10, W13, W16, W18 | XL each | The epic's own Definition-of-done items #1 (derived state) and #4 (fully scaffolded strategy-service) | **corpus gap — these need plans authored**, not currently dispatchable as-is |

## execution-service

| Item | What's missing | Evidence | Size | Blocks | Ext. blocked |
| --- | --- | --- | --- | --- | --- |
| Delta-proxy repricer generalization | See Known P0 | issue cited | L | W16 triggers/latency; MEV/market-making/arb-leg repricing generalization | **Y** — needs UAC's `QuoteInstruction` extended first (cross-repo), plus 2 judgment calls the epic's own W7 P1 finding says must be re-tagged `[OPERATOR]` before AO can touch them |
| CEFI live venue-string dispatch broken for 9/12 major venues | strategy-service's position-adapter factory and execution-service's order-adapter factory each hand-roll a legacy bare-token venue table never extended to canonical dash-suffixed IDs — 9 of 12 major CEFI venues raise an unhandled `ValueError` on live position-read AND order-placement under their real canonical name | `/plans/active/issues/cefi_live_venue_string_dispatch_broken_2026_08_16.md` (P0) | M | Live readiness for nearly all of CeFi — this is the single highest-leverage fix in the corpus for the readiness matrix | N |
| CCXT `withdraw()` stub always returns CONFIRMED | Real exchange call is commented out; every CEX_WITHDRAW-routed venue (18 of 22) would report a successful withdrawal that never happened. Confirmed **dead-code-today** (HandlerRegistry defaults to `MockTransferAdapter`, no CEX_WITHDRAW handler registered) | `/plans/active/issues/cefi_ccxt_withdraw_stub_returns_false_confirmed_2026_08_16.md` (P0) | M | Real-money withdrawal correctness once reachability is wired | N to build; **Y** (credentials) to exercise end-to-end |
| CloudKmsCustodyProvider silently defaults an unmapped chain to `chain_id=1` (Ethereum) | Custody surface for HOT_TRADING/GAS_RESERVE wallets; UAC's own `resolve_chain_id()` raises on the same case. Confirmed reachable-but-gated, not dead — `LINEA` is one of the unmapped chains and already live for data capture elsewhere | `/plans/active/issues/defi_cloud_kms_silent_wrong_chain_id_fallback_2026_08_16.md` (P0) | S-M | Custody/security correctness — wrong-chain fund movement risk | **Y** — OPERATOR must check live `wallet_provisioning.json` for an affected wallet first |
| Emergency close-all path broken; several execution-service connector modules unreachable | strategy POSTs to `/api/orders`; execution-service exposes no such route. Marinade/Kamino/Jupiter connectors have zero production callers. 6/32 DeFi connector modules (19%) genuinely reachable-and-live | `/plans/active/issues/e2e_wiring_reachability_audit_2026_08_15.md` (P0) | L | The disaster path this whole readiness effort exists to protect | **Y** — OPERATOR ruling needed on the close-all contract shape before building |
| Reconciliation: pause-before-manual-entry, virtual/persistent-delta exclusion, soft-delete audit trail | All three explicitly unbuilt, tracked as open todos in the same reachability-audit doc | same doc, lines 549-553 | M | W12 reconciliation in full | N |
| `OrderTracker` has no CANCELLED/AMENDED status | `GET /instructions/{id}` reports a genuinely-cancelled order as SUBMITTED forever; `is_instruction_complete()` never flips true for a cancel-only instruction | `/plans/active/issues/execution_order_tracker_missing_cancelled_amended_status_2026_08_17.md` (P2) | S | W11 "every incremental step... including cancels" | N |
| Production live orchestrator may not satisfy the `LiveOrchestrator` protocol it's cast to | Untested end-to-end; relayed from a sub-agent's investigation, spot-checked location only, not independently re-verified line-by-line this pass | `/plans/archive/2026_08/execution_service_live_orchestrator_protocol_mismatch_untested_2026_08_16.md` (P1) | M | Live-execution correctness broadly | **unverified — needs a fresh read** |
| Pendle connector built but never wired into dispatch | Working simulation-only connector exists; never instantiated in `DeFiAdapter`, absent from `DEFI_VENUE_TO_CONNECTOR_CLASS`/`DEFI_VENUE_TO_GATE_MARKER` | `/plans/active/issues/pendle_venue_onboarding_2026_08_16.md` (P2) | S | One additional DeFi venue's reachability | N |
| Execution policy + fill-model gaps | Two independent benchmark implementations need collapsing into one sent value; lending path must not be no-op'd; algo vocabulary duplicated across two modules; execution-policy evaluator unwired; sub-candle rung fallback design (already decided 2026-08-12) not yet built; PB.8 volume-overcounting correction not yet carried into the cap definition | `/plans/active/execution_service_policy_and_fill_model_gaps_2026_08_19.md` (13 open, all AGENT-tagged) | L | Fill-model realism for every backtest/paper comparison | N |
| Tenderly-fork integration test credential-blocked | Real test exists, `@pytest.mark.skip`ped pending a Tenderly fork RPC endpoint/API key | `/plans/active/issues/exec_tenderly_2026_08_15.md` (P3) | S | One test's coverage of the recursive-loop DeFi orchestrator | **Y** (credentials) |
| W14 exchange contract fidelity — venue error codes, pinned exchange version + cassette re-run on drift | Both P0, open in the epic; no dedicated plan found | epic W14 | L | Silent venue-version drift going undetected | **Y** — W14's own OPERATOR todo: test accounts with credentials per venue, a prerequisite |
| W15 security audit of every venue adaptor, "especially DeFi" | P0, open in the epic; **no plan doing this systematically was found in this pass** | epic W15 | XL | Security review coverage of every on-chain write path | **corpus gap — needs a plan authored** |
| W17 fees/gas breakdown (clearing/broker/exchange/gas/other) in both strategy- and execution-service | P0, open in the epic; partially overlaps `defi_gas_net_cost_partial_wiring_gap_2026_08_17` (P1 — gas cost silently defaults to 0 in 4 live strategy paths, real strategy engines already reading a never-produced feature/config value) but the full breakdown structure is broader than that one fix | epic W17, `/plans/active/issues/defi_gas_net_cost_partial_wiring_gap_2026_08_17.md` | M-L | Alpha PnL accuracy net of costs | N |
| W22 — strategy→execution messaging + external instruction API | Confirmed **unbuilt end-to-end** by a 2026-08-19 workspace-wide search — the only live instruction path today is manual (`ManualOperationHandler → LiveOrchestrator.execute_instruction()`). Needs: Pub/Sub instruction delivery, features→execution subscription, per-instruction GCS audit sink, 3 deployment topologies (internal/external-automated/manual) on one schema, external hosting both ways, the other 10 action types past TRADE (currently HTTP 501), kill-switch/flatten as callable instructions | epic W22 (10 open P0/P1 todos) | XL | The entire "external client" commercial surface this epic's presentation artefacts describe | Mostly N to start (it's a real build), but genuinely **needs a phased plan authored** before dispatch — this is epic-sized, not plan-sized |

---

## Corpus gaps — workstreams with no owning plan found

These are epic-level P0 items where the walk of `plans/active/` did not surface a plan or issue doc actually doing
the work, only the epic's own todo naming the requirement. Listed once here rather than repeated per repo:

- **W8 — weightings SSOT** (unified-api-contracts).
- **W9 — account balances as the single strategy I/O** (strategy-service).
- **W10 — risk and exposure, full dimension set** (strategy-service).
- **W13 — PnL attribution across every risk/exposure dimension** (strategy-service) — narrower than the PnL-engine
  fix tracked above, which fixes which formula/surface is authoritative, not the full attribution-dimension build.
- **W18 — canonical output paths for everything strategy-service emits** (strategy-service).
- **W15 — security audit of every venue adaptor** (execution-service, cross-repo).
- **W22 — strategy→execution messaging + external instruction API** (execution-service) — has 10 todos in the epic
  itself but no phased implementation plan; this one is large enough that authoring the plan is itself a step.

Before dispatching against any of these, the missing piece is a plan, not a worker — an AO todo needs a bounded,
worker-determinable outcome, and none of the seven exist as bounded units today.

## OPERATOR RULINGS — 2026-08-19, four of Wave 0 resolved

These four are DECIDED. The remaining Wave-0 items stay blocked.

| # | Ruling | Decision |
| - | ------ | -------- |
| 3 | `PATH_REGISTRY` `{mode}` | **Add `{mode}` to all four templates AND migrate existing data.** |
| 10 | Tardis backfill, VOL_\*/MARKET_MAKING_\* | **Authorised now.** |
| 7 | Close-all endpoint contract | **Define a dedicated close-all contract** — not a reuse of `/api/orders`. |
| 5 | Transfers in production | **WIRE IT — it should be running.** |

**Ruling 3 — migrate, do not quarantine.** The migration touches stored paths, so it is governed by
[entity-rename-and-split-consumer-migration-rule](/codex/02-data/entity-rename-and-split-consumer-migration-rule.md):
every consumer enumerated and migrated in the SAME change, because a token grep misses path-prefix, filename and
registry-membership binders. Writer-only fixes are explicitly NOT what was chosen.

**Ruling 10 — authorised, but Tardis is capped at 1 concurrent VM across both clouds.** This queues, it does not
parallelise; count the fleet before launching. It reclassifies ~20 archetypes from "not code-complete" to allowlist
item 5 (code-ready, pending real-data testing) — so the archetype-completeness gap shrinks by decision, not by
dispatch, and every readiness figure quoting the old split needs re-deriving afterwards.

**Ruling 7 — a disaster path gets its own contract.** Reusing `/api/orders` would give the emergency flatten the
same failure modes as ordinary order flow. Needs its own idempotency semantics and its own tests. Unblocks the
reconciliation-pause / virtual-entry / soft-delete trio that was waiting on this shape.

**Ruling 5 — transfers are to be WIRED, not left deliberately inert.** This is the highest-consequence ruling of
the four and it changes what the client artefacts may say: §11 "Automated movement" content currently framed as
target-state moves toward real capability as the wiring lands, and must be re-graded then — not before.
Two hard constraints on whoever implements it:
- **Thresholds and policy resolve SLOW-PATH**, per `system_readiness_master.md` § W7. Gas floors, reserve
  thresholds and rebalance bands are strategy/config decisions published into the cache; execution's handlers
  execute a pre-computed decision. Putting reserve-threshold logic inside `TransferCoordinator` would give
  execution a policy decision, force per-chain tables into execution-service (breaking venue-agnosticism), and put
  it on the fast path — three violations from one plausible-looking commit.
- **Only `SUBACCOUNT_MOVE` has a registered handler today.** `CEX_WITHDRAW` is commented "NOT WIRED", `REBALANCE`
  is enum-only, and gas top-up/floor has no handler and no reserve-threshold logic anywhere. Wiring means building
  those, not just instantiating the coordinator.


### Four more Wave-0 rulings — 2026-08-19

| # | Ruling | Decision |
| - | ------ | -------- |
| 6 | Corporate-actions re-sourcing | **Yahoo Finance.** |
| — | market-tick-data-service scope | **INCLUDE it** — the omission from the seven-repo list was accidental. |
| — | `_SCE_1H` strategy_id | **Migrate properly**, not document-and-leave. |
| — | Seven unowned epic P0s | **Author all seven plans now, in parallel.** |

**Ruling 6 — Yahoo Finance.** Not on the fleet-wide banned-vendor list (Elysium · Arkham · Bloxroute · Infura ·
Kaiko · Massive-fka-Polygon.io), so it is a permitted source. Build the adapter scaffold regardless of credential
state per the external-data-always-available rule; if access is missing, ship the scaffold and mark
`BLOCKED-CREDENTIALS` rather than descoping. **Also required in the same change**: correct
[tradfi-databento-sourcing-ssot](/codex/02-data/tradfi-databento-sourcing-ssot.md), whose 2026-08-03 banner still claims the Polygon.io removal is
"COMPLETE ACROSS ALL REPOS" — features-service is the third confirmed still-live usage found after that date.

**MTDS is IN SCOPE.** It owns market-data-live, which is allowlist item 3 of the goalpost, and the epic's own
pipeline table treats it as a distinct stage. The scoping pass excluded it on a literal reading of the repo list;
that exclusion is now reversed and MTDS needs the same per-repo remaining-work treatment as the other seven.

**`_SCE_1H` — migrate, do not document-and-leave.** The harder, correct option. Governed by
[entity-rename-and-split-consumer-migration-rule](/codex/02-data/entity-rename-and-split-consumer-migration-rule.md):
enumerate and migrate EVERY consumer in the same change — stored GCS rows, manifest entries, ledger records,
backtest artefacts, registry memberships, and the two legacy-mapping scripts. No shim (the workspace bans
deprecated shims). A token grep will miss path-prefix, filename and registry-membership binders, so the enumeration
must be done properly before anything changes.

**Author all seven unowned P0 plans in parallel.** UAC weightings SSOT; strategy-service account-balance I/O,
risk/exposure, PnL-attribution-in-full, canonical output paths; execution-service security audit; W22
messaging/external-instruction-API. Plan authoring is file-disjoint across the seven so it parallelises, and does
not need to wait on Waves 1-3. Caveat worth carrying: W22 and the security audit both lean on accurate per-venue
and per-chain declarations, so their authors should expect Wave-1's UAC registry fixes to change their inputs.

## Suggested dispatch order

Reasoning follows the dependency chain the epic itself describes (instruments-service → UAC underlies almost
everything; strategy/execution sit downstream of both) plus the explicit "land X before Y" statements found in the
plans themselves.

**Wave 0 — operator rulings needed before ANY dependent code work starts.** These are judgment calls; dispatching
the code work ahead of the ruling produces either a stall or an invented answer:
1. Instruments catalogue design ratification (`instruments_catalogue_definitions_and_field_history`).
2. UAC `__init__` restructure scope for the lazy-loading refactor (blocks strategy-service Elysium carve-out too).
3. PATH_REGISTRY `{mode}` migration/backward-compat strategy (UTL) — data is actively colliding across modes until
   this lands, so this ruling is high-urgency despite being "just" a decision.
4. Venue-eligibility generalization shape + mode-aware dispatch design (strategy-service centralization fixes).
5. Transfers-do-not-execute-in-production path decision (strategy-service, funds-adjacent — HIGH severity).
6. Corporate-actions re-sourcing path off the banned vendor (features-service).
7. Close-all-endpoint contract shape (execution-service reachability audit) — disaster-path priority.
8. CloudKmsCustodyProvider — check live `wallet_provisioning.json` for an affected wallet before the code fix ships.
9. Instrument-universe hot-swap position-state safety ruling.
10. Tardis-backfill authorization for the VOL_\*/MARKET_MAKING_\* backtest-and-register family — note this ruling
    converts ~20 archetypes from "not code-complete" to "allowlist item 5, pending real-data testing," which is a
    large chunk of the archetype-completeness gap resolved by a single decision rather than by dispatch.

**Wave 1 — UAC foundation, file-disjoint from strategy/execution work, so runs in parallel with Wave-0 rulings
resolving elsewhere.** `get_venue_asset_group()` fix and the three-chain-registry consolidation both touch UAC's
core registry layer and were filed the same day — **verify they don't touch the same file before parallelizing them
against each other**; both can run alongside `registry_ssot_hardening`'s venue→chain overlap (same root cause,
arguably one change), `canonical_path_oracle_blind_to_filename_stem`, and `coverage_floor_registries_no_cross_
propagation` (different files, safe to parallelize). `order_state_machine` code+test todo can run in parallel too
(ruling already made).

**Wave 1 (parallel repos)** — instruments-service (`InstrumentRecord` extra=forbid, schema versioning), UTL (config
test-failure root-cause, manifest-writer flush perf), MDPS (multi-instrument write-race verification+fix),
features-service (delta_one bucket-token fix, calendar-manifest wiring once its REVIEW decision lands) are all
file-disjoint from UAC and from each other — dispatch concurrently.

**Wave 2 — strategy-service, sequenced internally.** Land the `DeFiHealthAggregator` vs `margin_event_emitter`
reconciliation FIRST (the epic explicitly says no new archetype wires onto either until this converges). Then:
position-adapter buildout (closing the 8-vs-16 asymmetry) and the live-path stale-producer/flatten-protocol work
(currently 0/23 done, safety-relevant) can run in parallel with each other and with the wizard/config-surface
expansion, since they touch different files. Archetype engine registration for the VOL_\*/MARKET_MAKING_\* family
waits on Wave-0 item 10.

**Wave 3 — execution-service, sequenced internally.** CEFI live venue-string dispatch (highest-leverage single fix
in the corpus — unblocks 9/12 major CeFi venues at once) and OrderTracker CANCELLED/AMENDED status are file-disjoint
and safety-uncontroversial — dispatch immediately, do not wait on anything above. The close-all endpoint and
reconciliation-pause/virtual-entry/soft-delete trio wait on the Wave-0 contract-shape ruling. The delta-proxy
repricer generalization waits on UAC's `QuoteInstruction` extension (Wave 1 territory) landing first, plus the two
judgment calls being re-tagged `[OPERATOR]` before any AO dispatch. Execution-policy/fill-model gaps are file-
disjoint from all of the above and can run any time.

**Wave 4 — the two XL corpus gaps (W22 messaging/external API, W15 security audit).** Neither is dispatchable
until a phased plan exists. Authoring those plans is itself Wave-4 work and can start as soon as an author is
available — it does not need to wait on Waves 1-3, but the plans themselves will likely want Wave-1's UAC fixes
(especially the chain/asset-group registries) landed first since both W22 and W15 lean on accurate per-venue/
per-chain declarations.

---

## Coverage disclosure

**Read in full**: `plans/epics/system_readiness_master.md` (871 lines, all of W1-W22 + Definition of done); the
three known-P0 issue docs cited by name in the task; `plans/audit/results/registry_ground_truth_2026_08_19.md`
(frontmatter/format reference only).

**Sampled — frontmatter + full open-todo list, not full prose**: ~20 plans (`venue_readiness_and_registry_
hardening`, `registry_ssot_hardening`, `strategy_service_centralization_fixes` + finalize, `strategy_service_
expansion_overlays_config_and_wizard`, `v2_engine_venue_buildout` — this one's prose was read in depth for the
VOL_\*/MARKET_MAKING_\* section specifically — `execution_service_policy_and_fill_model_gaps`, `instrument_record_
schema_completeness_extra_forbid`, `instruments_catalogue_definitions_and_field_history`, `venue_capability_route_
axis_and_cross_ag_declarations`, `venue_e2e_wiring` + finalize, `venue_smoke_test_bar` + finalize, `service_config_
ownership_and_instruction_contract`, `lazy_scoped_loading_refactor`, `elysium_carveout_stubbed_strategy_service`,
`data_pipeline_completion_2026_08_21`, `citadel_satellite_ao_dispatch_batch2`, `cross_cutting_strategy_execution_
determinism`) and ~45 issue docs (summary + first few open todos each — see the per-repo tables above for the full
list; every issue cited in a table row above was read at least to this depth).

**Title/metadata only, not assessed for content**: the remaining ~180 candidate plans and ~180 candidate issues
that matched a seven-repo name in their frontmatter — dominated by per-asset-group data-completion/backfill/
satellite-dispatch plans (cefi/defi/tradfi/sports/prediction `*_consolidated_closeout`, `*_satellite_ao_dispatch_
batch*`, `data_completion_*`) which are presumptively allowlist-item-1 (backfills) territory and were not opened to
confirm that presumption for each one individually. A handful of these could contain genuine code gaps discovered
mid-backfill that this pass missed — the corpus is too large to read exhaustively in one sitting.

**Two direct code spot-checks performed**: (1) confirmed `checks.mtds_live_feed()` and `_mtds_live_feed_probe.py`
exist as claimed by the epic's W1 checkbox. (2) confirmed `strategy-service/strategy_service/engine/strategies/v2/
factory.py`'s `ARCHETYPE_ENGINE_REGISTRY` has exactly 32 entries and does not include `MARKET_MAKING_PASSIVE_SPREAD`,
`VOL_STRADDLE`, or any `CARRY_AND_YIELD` member — matching both the archetype-code-completeness skill's own count
and `v2_engine_venue_buildout`'s "NOT registered" claims. Neither spot-check found a flipped-but-not-landed claim;
both plans checked were accurate. This is not evidence the rest of the corpus is equally clean — it is evidence for
exactly the two claims checked.

**Not assessed at all**: `market-tick-data-service` (excluded per the explicit seven-repo scope, see "Scope note"
above), `deployment-api` (named in several P0-adjacent issues — e.g. unauthenticated-prod-P0 — but not one of the
seven repos), CI/CD and agent-orchestrator items even where they touched a named repo (explicitly out of scope per
the task).

## Progress Log

**2026-08-19 — scoped.** Read-only pass, no plans/artefacts/source touched. Produced this doc as the only new file.
