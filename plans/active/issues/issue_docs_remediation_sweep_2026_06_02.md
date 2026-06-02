---
title: Issue-docs remediation sweep — code-fixable items across the 2026-05/06 issue-doc backlog
created: 2026-06-02
author: ikenna (slot 7)
parent_epic: master_to_live_defi_2026_05_23.md
priority: P1
status: IN-FLIGHT — slot 7 executing; items flip + source issue docs archive as each is verified complete
locked_by: live-defi-rollout
locked_since: 2026-06-02
estimate_class: brand-new
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 4
source:
  - plans/active/issues/alerting_fp_rate_analysis_2026_05_23.md
  - plans/active/issues/api_host_chronic_impairment_2026_05_29.md
  - plans/active/issues/batch_live_reconciliation_service_audit_2026_05_27.md
  - plans/active/issues/cefi_processed_candles_manifest_file_disconnect_2026_05_25.md
  - plans/active/issues/defi_code_codex_drift_2026_05_27.md
  - plans/active/issues/deployment_scripts_bucket_softdelete_log_churn_2026_06_01.md
  - plans/active/issues/features_service_defi_data_loading_blockers_2026_05_29.md
  - plans/active/issues/fleet_audit_triad_deferred_followups_2026_06_01.md
  - plans/active/issues/gcs_hive_partition_malformed_paths_remediation_2026_06_01.md
  - plans/active/issues/mdps_state_adapter_leading_nan_audit_2026_05_29.md
  - plans/active/issues/running_vm_fleet_status_2026_05_27.md
  - plans/active/issues/uniswap_v3_ethereum_28k_attempted_failed_2026_05_28.md
---

## Why this exists

A 2026-06-02 (slot 7) code-audit of every `plans/active/issues/*.md` doc verified each open claim against current code
(with git-log dates, since docs predate today). Outcome: a large fraction of "open" items were **already fixed in code**
after the docs were written; what remains is consolidated here as canonical `- [ ]` todos so it is dispatchable +
auditable in one place. This tracker IS the dispatch (per CLAUDE.md "the plan todo is the dispatch"). Items flip to
`- [x] ✅ — <repo>@<sha>` per Commit+Push+Flip; each **source issue doc is archived the moment ALL of its items here are
verified complete**.

**Exclusions (NOT credential-blocked — explicitly out of scope):**

- **Tardis paid key** — operator non-activation (the one acknowledged credential blocker). No other "credential /
  no-data / no-API" framing is accepted as a blocker; all such items below are reframed as actionable.
- **R2** (tradfi v9 migrator zero-row guard) — being done elsewhere.
- **R3** (deployment-service `test_sports_tier3_fixture_diagnostic` time-of-day flake) — reported in-flight by another
  agent; NOT yet on `origin/live-defi-rollout` as of 2026-06-02 (no `timedelta`, 0 incoming). Left out to avoid
  collision; **pick up if their fix does not land.**

## Status taxonomy in this doc

`- [ ]` actionable now · `BLOCKED-DISCIPLINE` (single-walk / HOLD banner) · `BLOCKED-OPERATOR-DECISION` · `NEEDS-LIVE`
(operator-gated infra run, not credentials).

---

## agent-orchestrator (integration base = `main`)

- [x] ✅ [CODE] P1. agent-orchestrator: add `PRAGMA busy_timeout=30000` in `server/db.py` `_on_connect()` — prevents
      DB-locked cascades after an OOM-induced restart. — agent-orchestrator@`1fe3386`. Source:
      api_host_chronic_impairment.
- [x] ✅ [INFRA] P2. agent-orchestrator: provision a 16 GiB swapfile (new `scripts/orchestrator/ensure_swap.sh`,
      idempotent + `vm.swappiness=10`) wired as STEP 2.5 in `scripts/bootstrap_vm.sh` — belt-and-braces against the
      32–57 GiB pytest OOM on the API host. — agent-orchestrator@`1fe3386`. Source: api_host_chronic_impairment.

## market-data-processing-service — MDPS leading-NaN workstream (operator chose Option A + carry-from-prior-day)

- [x] ✅ [CODE] P0. MDPS: add `state_col: str | None` + `flow_cols` kwargs to `base_adapter._finalize_session_grid` (per
      issue-doc §Scope items 1–3). Source: mdps_state_adapter_leading_nan. — market-data-processing-service@4fd962d |
      `state_col` drives first-obs trigger + OHLC from the state column; `flow_cols` (default `DEFAULT_STATE_FLOW_COLS`)
      zero-filled; `seed_state` carries secondary-column prior-day values into leading bins; backward-compatible when
      `state_col=None` | tests/unit/test_state_adapter_density.py (5 cases) | lint+typecheck+codex green (only
      pre-existing foreign `test_dependency_checker_sports_prediction` bucket-tier drift red — see finding below).
- [x] ✅ [CODE] P0. MDPS: add prior-day carry-seed logic to `_finalize_session_grid` (Decision 1 — seed leading bins
      from last-known price/ts instead of dropping). Source: mdps*state_adapter_leading_nan. —
      market-data-processing-service@5a5e989 | seed_price/seed_ts kwargs + carry-from-bin-0 + cold-start-drop +
      CLOSED-drop preserved | tests/unit/test_finalize_session_grid_seed.py (6 cases) | QG exit 0. (Seed \_threading*
      through batch+live call path tracked in issue-doc Decision-1 todo.)
- [x] ✅ [CODE] P0. MDPS: wire the 7 state adapters to call `_finalize_session_grid(output, state_col=…)` —
      cefi/derivative, cefi/futures_chain, cefi/options_chain, defi/liquidity, defi/market_state, cefi/book_snapshot,
      tradfi/tbbo. Source: mdps_state_adapter_leading_nan. — market-data-processing-service@23d7add |
      derivative/options/book/tbbo → `state_col=mark_price`/`mid_price` (close structurally NaN; OHLC driven from
      driver, volume zero-filled; book/tbbo pre-LOCF the quote mid); futures → `state_col=close` (=last_price);
      liquidity/market_state → close-driven finalize (close already = mid/liquidity, volume carries real TVL/supply so
      NO state_col — its flow zero-fill would null TVL). No-price-driver input → honest absence. basedpyright clean.
- [x] ✅ [TEST] P0. MDPS: add leading-gap + prior-day-carry + cold-start-drop + density tests
      (`tests/unit/test_state_adapter_density.py` + extend per-adapter tests). Source: mdps_state_adapter_leading_nan. —
      market-data-processing-service@4fd962d (test_state_adapter_density.py 5 cases + test_finalize_session_grid_seed.py
      6 cases) + @23d7add (derivative/futures/tbbo/more_defi/writer_schema per-adapter tests updated to the dense
      session-grid contract) + @180f54b (env-tier bucket test fix). **Full MDPS quality-gates.sh exits 0.**
- [x] ✅ [VERIFY] P0. MDPS: NaN WARN diagnostic in `fast_candle_aggregation.py:304-325` — **KEPT as a permanent
      regression guard** (all 7 adapters now dense → dormant in steady state; catches future regressions). Source:
      mdps_state_adapter_leading_nan. **Full MDPS `quality-gates.sh` exits 0** (after the [BUG] env-tier test fix
      below).
- [x] ✅ [BUG] P0. **RESOLVED — MDPS foreign QG-red (stale flat bucket-name test assertions).**
      `tests/unit/test_dependency_checker_sports_prediction.py` (9 exact-string cases:
      `TestOutputBucketsSportsPrediction` + `TestPerCategoryUpstreamRouting`) asserted the **legacy flat** bucket names
      but `get_output_bucket` / `_get_upstream_deps_for_category` / `OUTPUT_BUCKETS` now resolve the **env-tiered**
      canonical name (`market-data-tick-sports-prd-test-project`) via UTL `resolve_bucket_name` since
      `market-data-processing-service@61900a3`. **Operator confirmed env-tiered IS canonical (2026-06-02)** → migrated
      the 9 stale assertions to substring/shape checks matching the file's own `TestCanonicalBucketNameResolver` style
      (robust to the env-tier token, not blind-pinned to `prd`). — market-data-processing-service@180f54b | **full
      `quality-gates.sh` exit 0 (sentinel `.qg_last_passed_sha` written)**. Source: mdps_state_adapter_leading_nan
      (incidental finding).

## batch-live-reconciliation-service

- [x] ✅ [CODE] P1. BLRS: register the resolution router in `api/main.py` AND rename prefix `/reconciliation` →
      `/t1-recon` (R1 + D4) — resolution endpoints are currently unreachable at runtime. —
      batch-live-reconciliation-service@`f0c074a` (resolution_api.router wired into create_app; prefix → /t1-recon; QG
      exit 0). Source: batch_live_reconciliation_service_audit.
- [x] ✅ [CODE] P1. BLRS: add `drawdown_pct` + `fill_rate_min` orchestrator green gates alongside the existing
      `bps_delta_max` (D3 — operator ruled "build all three"). — batch-live-reconciliation-service@`43e88ea`
      (ExecutionThresholds.drawdown_pct_max/fill_rate_min; orchestrator gates all three vs most-conservative archetype
      bound; stage3 emits real fill_rate + peak-to-trough drawdown_pct). Source:
      batch_live_reconciliation_service_audit.
- [x] ✅ [CODE] P2. BLRS: wire `stage2_strategy_recon` to the strategy-service/position query API as the canonical
      position baseline (D2) instead of raw GCS event archives. — batch-live-reconciliation-service@`43e88ea` (stage2
      baseline = strategy-service GET /api/v1/accounts/{id}/pnl-series via requests; GCS event archive fallback when URL
      unset/404/ empty; baseline_source metric). Source: batch_live_reconciliation_service_audit.
- [x] ✅ [CODE] P2. BLRS: implement `soak_mode` in `ReconConfig` (+ alerting-service CRITICAL-suppression counterpart)
      (G4). — batch-live-reconciliation-service@`43e88ea` (ReconConfig.soak_mode downgrades recon-drift routing →
      ALERT_SUPPRESSED so alerting suppresses CRITICAL escalation in a soak window). Source:
      batch_live_reconciliation_service_audit.
- [x] ✅ [CODE] P2. BLRS: build `analysis/threshold_distribution.py` (bps gate analyzer over past `summary_*.json`)
      (G5). — batch-live-reconciliation-service@`cce28d1` (analyze*threshold_distribution() over
      t1-recon/recon/summary*{date} .json; per-metric count/mean/p50/p90/p95/max + pass/fail vs EXECUTION_THRESHOLDS;
      typed, no Any). Source: batch_live_reconciliation_service_audit.

## unified-api-contracts

- `BLOCKED-DISCIPLINE` [CODE] P1. UAC: registry key drift in `registry/market_data_categories.py` — `"dex_pools"`/
  `"dex_swaps"` → `"dex_pool_state"`/`"dex_pool_swaps"`. RECLASSIFIED 2026-06-02 (was "risk LOW" in the audit — WRONG):
  a consumer audit found the legacy keys are STILL live across MTDS source (`engine/orchestrator.py:621`,
  `cli/handlers/schema_validation.py`, `market_interface/adapters/defi/uniswap_v3_adapter.py`, `solana_defi_handler.py`,
  migration scripts). Renaming the registry keys standalone would break
  `needs_candle_processing`/timeframe/schema-validation lookups mid-migration. The rename is the coordinated
  registry-alignment scope of `defi_manifest_canonicalisation_2026_06_01.md` §C0-RD (operator-locked SSOT
  `defi-canonical-naming-ssot.md`). Do NOT do standalone. Source: defi_code_codex_drift D14.
- [x] ✅ [DOC] P2. UAC: add OHLC-semantics docstring to the `swaps_ohlcv_*` schema in
      `internal/schemas/_candle_contracts.py` — O/H/L/C = USD-normalized pool spot price (`amountUSD/|base_amount|`),
      ≈1.0 for USDC/WETH, 3 fallback methods. — unified-api-contracts@`455ddf9a`. Source: features_service_defi #3.

### UAC DeFi venue-registry coherence (defi_code_codex_drift D8/D10/D15)

> **OPERATOR DECISION 2026-06-02 (Ikenna):** ADD the venues — but each capability declaration must be **gated on a
> per-venue data-source smoke test** first: confirm we can actually pull the venue's data from a source we have (The
> Graph / Graph Studio subgraph, Alchemy, Helius, public RPC/endpoint, or other relevant). Only flip a venue to `live`
> AFTER a probe returns real data. Tooling: `market-tick-data-service/scripts/subgraph_health_probe.py` (EVM subgraphs;
> network confirmed reachable, Graph key in Secret Manager) + a Helius/RPC probe for Solana. Add subgraph IDs to UAC
> `_SUBGRAPH_IDS` + `_ProtocolCapability` + register in `defi_venues.py` only on a green probe.

- [ ] [CODE] P2. UAC D15: HYPERLIQUID/ASTER `pipeline`→`live` — handler already actively collects
      (`perp_funding_handler.py`), so data source is proven; but first CONFIRM the axis classification (audit noted they
      may be CeFi-axis perp venues on their own L1/BSC, candidates for removal from the DeFi registry rather than
      flip-to-live). Resolve classification → flip-to-live OR move to CeFi registry. Source: defi_code_codex_drift D15.
      **SMOKE-TEST RESULTS 2026-06-02 (slot 7 — real network probes; keys from SM
      `thegraph-api-key`/`helius-api-key`):**

- [x] ✅ [CODE] P2. UAC D10 VENUS — **BUILT + live** (Compound-`markets`; BSC isolated+core + ETH). Adapter:
      `lending_indices` live+history. — unified-api-contracts@`cd65ff76` + market-tick-data-service@`d98f5726` (gas
      stripped to per-chain @`12a4318e`). Source: defi_code_codex_drift D10.
- [x] ✅ [CODE] P2. UAC D10 BENQI — **BUILT + live** (Compound-`markets`, AVALANCHE; `lending_indices`). —
      unified-api-contracts@`cd65ff76` + market-tick-data-service@`d98f5726`. Source: defi_code_codex_drift D10.
- [x] ✅ [CODE] P2. UAC D10 RADIANT — **BUILT + live** (Messari-`Market`, ARB+ETH; full `lending_indices` +
      `liquidations` + `risk_params`, live+batch). — unified-api-contracts@`cd65ff76` +
      market-tick-data-service@`d98f5726`. (See gap #1/#2 below re liquidations/risk_params path reconciliation.)
      Source: defi_code_codex_drift D10.
- [x] ✅ [CODE] P2. UAC D10 EULER_V2 — **BUILT + live** (Goldsky `eulerVaults`+`vaultStatuses`, ETH+ARB; full set, live
      500/batch 650). Added `_SUBGRAPH_ENDPOINT_OVERRIDES` Goldsky routing. — unified-api-contracts@`cd65ff76` +
      market-tick-data-service@`d98f5726`. Source: defi_code_codex_drift D10.
- [x] ✅ [CODE] P2. UAC D10 SOLAYER — **KILLED / fully removed** (operator decision 2026-06-02: "rather have no
      implementation than a partial one"). sSOL is a custom Solayer LRT (not a standard SPL stake-pool); its
      exchange-rate/APY vault account layout could not be field-verified (no public IDL; `app.solayer.org/api`=500;
      Sanctum UNSUPPORTED_LST) — a guessed offset would have recreated the D10 incoherence. Wiped from UAC
      (`_ProtocolCapability` + `_STATIC_VENUE_CHAINS` + `_defi_chain_data` + `external/solayer/` dir + facade + VCR +
      cassette-allowlist + defillama mocks), instruments-service (`adapters/defi/solayer.py` + tests + factory), and
      strategy-service (reward-attribution docstring) + 6 codex docs. — unified-api-contracts@`4abec5c6` +
      instruments-service@`84b2a2d8` + strategy-service@`1be0632a` + PM codex updates. Not a credentials block. Source:
      defi_code_codex_drift D10.

> **E2E HOOKUP STATUS 2026-06-02 (slot 7 — operator: hook UAC/IS/MTDS/MDPS/features/strategy/execution + data-status
> UI/API).** Traced the 4 built venues through the whole pipeline. **AUTO-WIRED from UAC (no work):**
> instruments-service (`_SUBGRAPH_VENUE_PREFIX_TO_PROTOCOL` + dedicated venus/benqi/radiant/euler_v2 adapter classes),
> MTDS `lending_indices` (evm_defi_handler), features-service (manifest-driven venue-wildcard read), execution-service
> (no DeFi allowlist — data-only), **deployment-api/data-status UI** (reads `ALL_DEFI_VENUES` +
> `DEFI_VENUE_DATA_TYPE_CAPABILITIES` from UAC → the 4 venues auto-appear as expected-coverage cells + render in the
> DEFI panel, all `live` phase). The data-status surface already understands + shows them. **GAPS (tracked below).**

- [ ] [CODE] P1. MTDS reconcile `liquidations` path for radiant/euler — `liquidations_handler.py:196`
      `_DEFAULT_PROTOCOLS` excludes them while `evm_defi_handler` emits liquidations; confirm ONE canonical emit path so
      data-status doesn't show phantom-missing liquidation cells (UAC declares `liquidation_events` for
      RADIANT-ARB/BSC + EULER). Repo: market-tick-data-service. Source: e2e trace 2026-06-02.
- [ ] [CODE] P1. MTDS verify `risk_params` emit for radiant/euler matches the declared
      `DEFI_VENUE_DATA_TYPE_CAPABILITIES` (evm_defi_handler `_EVM_DEFI_DATA_TYPE` is `lending_indices`-only; if
      risk_params isn't actually written, either add the emit OR drop risk_params from the cap to stay
      honest-coverage-coherent). Repo: market-tick-data-service. Source: e2e trace 2026-06-02.
- [ ] [CODE] P1. strategy-service `engine/strategies/v2/target_universe/catalog.py:1006` `_RECURSIVE_STAKED_LEND` — add
      venus/benqi/radiant/euler_v2 as carry_staked_basis lending-leg options (+ specs in
      `_build_carry_recursive_staked`) so they're usable as a lending leg, not just data-available. Repo:
      strategy-service. Source: e2e trace 2026-06-02.
- [x] ✅ [CODE] P2. UAC D10 PICASSO — **EXCLUDED + fully wiped** (operator 2026-06-02). Registry entries removed
      @`fa9238fb`; then orphan `external/picasso/` dir + facade + instruments-service `adapters/defi/picasso.py` + test
      removed in the Solayer-kill pass — unified-api-contracts@`4abec5c6` + instruments-service@`84b2a2d8`. Source:
      defi_code_codex_drift D10.
- [x] ✅ [CODE] P2. UAC D10 CAMBRIAN — **EXCLUDED + fully wiped** (operator 2026-06-02). Registry @`fa9238fb`; orphan
      `external/cambrian/` + IS `adapters/defi/cambrian.py` + test removed — unified-api-contracts@`4abec5c6` +
      instruments-service@`84b2a2d8`. Source: defi_code_codex_drift D10.
- [x] ✅ [CHORE] P3. UAC: orphaned `external/picasso/` + `external/cambrian/` Pydantic schema dirs + facade exports
      deleted (folded into the Solayer-kill pass). — unified-api-contracts@`4abec5c6`. Source: defi_code_codex_drift
      D10.

> **GREEN-VENUE ADAPTER-BUILD spec (operator 2026-06-02: include greens + build adapters, BATCH=LIVE).** Each green
> venue's `_ProtocolCapability` must declare the **canonical post-migration data types** (per the manifest-canon SSOT
> `defi-canonical-naming-ssot.md` + `defi_manifest_canonicalisation_2026_06_01.md` §C0): lending venues →
> `lending_indices` (+ `liquidations`/`risk_params`/`gas_fees` where the subgraph supports it) — NOT legacy names. The
> adapter is the per-protocol pattern in MTDS `cli/handlers/evm_defi_handler.py`: add (a) a live current-state GraphQL
> query AND (b) a history query (batch=live symmetry — same schema/data_type both modes), (c)
> `_EVM_DEFI_INSTRUMENT_TYPES` + `_row_symbol_for_evm_defi` mapping, (d) `_SUBGRAPH_IDS` entry, (e) `_DEFAULT_CHAINS`,
> then register live in `defi_venues.py`. **Per-venue you MUST first introspect the subgraph's market/asset entity** for
> the exact rate/index field names (Venus/BenQi are Compound-`markets` schema; Radiant is Aave-`assets`; Euler is
> Goldsky `eulerVaults`) so the field→`lending_indices`-column mapping is correct — declaring `live` without a working,
> field-mapped adapter just recreates the D10 incoherence. Solayer is a Solana RESTAKING venue →
> `restaking_rewards`/`lst_rates` via a Helius RPC adapter path (not subgraph). These 5 builds are high-stakes
> data-pipeline work (the "heartbeat") — do each as its own verified, QG-green shippable unit, NOT a bulk rush.

- [ ] [CODE] P3. UAC D8 Starknet `infura_compatible` template: keep + add a clarifying note (Infura is a removed
      _provider name_ but the public Starknet endpoint shape is retained); rename the key away from `infura_` to avoid
      the banned-name confusion. Source: defi_code_codex_drift D8.
- `BLOCKED-DISCIPLINE` [CODE] P2. UAC: drop duplicate cols `swap_count`/`volume_quote_usd` from `_DEX_EXT` — MUST bundle
  into the C0 migration walk (single-walk discipline), NOT standalone. Source: features_service_defi #4.
- `BLOCKED-DISCIPLINE` [CODE] P1. UAC: `FEATURE_GROUP_DATA_TYPE_OVERRIDES["defi"]` → `dex_pool_swaps` — coordinate with
  C2 data walk landing (reading-path mapping must not lead the on-disk canonicalisation). Source: features_service_defi
  #1.

## features-service

- [x] ✅ [CODE] P1. features-service: processed-candle manifest read false-positive — RE-SCOPED + fixed correctly. —
      features-service@`3e97475c` (QG exit 0). **Diagnosis (read both sides):** the issue-doc's proposed
      `service_name="market-data-processing-service"` flip is WRONG — UTL `get_captured_instruments`
      (`feature_service_base/manifest_discovery.py`) uses `service_name` ONLY at L136 `classify_and_emit_error(...)`
      (telemetry); the row mask (L105-111) filters `capture_status`/`date`/`data_type` and NEVER `service_name`. The
      real false-positive: both callers passed `data_type=None` → an instrument with ANY captured data_type was reported
      "available" even with no consumed processed-candle row. **Fix:** delta_one scopes discovery to UAC
      `resolve_data_type_for_feature_group(...)` over DEFAULT_FEATURE_GROUPS; volatility scopes to
      `(futures_chain, options_chain)`. No UTL change needed (helper already exposes the `data_type` filter). Also
      unblocked a PRE-EXISTING foreign STEP-5.69 QG-red — features-service@`97d14277` added an audited `# noqa: gs-uri`
      to `sports/data/gcs_reader.py:205` (error-message URI from e0ddde68, sports workstream — flagged to that track).
      Source: cefi_processed_candles_manifest_file_disconnect.
- [x] ✅ [CODE] P3. features-service: delete the dead `DEFI_DATA_TYPE_OVERRIDES` dict in
      `delta_one/engine/orchestrator.py` (UAC `resolve_data_type_for_feature_group()` is the real router; dict had zero
      refs). — features-service@`9f843dd4`. Source: features_service_defi.

## market-tick-data-service

- [x] ✅ [CODE] P1. MTDS: remove banned `bloxroute` relay URLs (`cli/handlers/mev_events_handler.py`) + delete the
      tracked `mev_events_handler.py.bak`. — market-tick-data-service@`d3e02228` (ruff+basedpyright clean). Source:
      defi_code_codex_drift D7.
- [x] ✅ [SCRIPT] P2. MTDS: add a QG lint guard that fails on malformed `by_date/` paths not matching
      `^raw_tick_data/by_date/day=\d{4}-\d{2}-\d{2}/`. — unified-trading-pm@`5d6d398e4` (guard
      `scripts/qg/no_malformed_by_date_paths.sh`) + market-tick-data-service@`b92d6c55` (wired STEP 5.86). Guard exits 0
      clean / exits 1 on hyphen-form `day-` violation. Source: gcs_hive_partition.
- `BLOCKED-DISCIPLINE` [CODE] P2. MTDS: extend `scripts/sweep_phantom_manifest_rows.py` for the raw-trade
  `captured`-with-no-processed-candle phantom class — RECLASSIFIED 2026-06-02: pruning those rows is a whole-corpus GCS
  walk that MUST bundle into the cefi C0 canon walk (single-walk discipline), NOT a standalone sweep. The read-side
  false-positive is instead killed by the features-service `service_name` filter below. Source: cefi_processed_candles.

## alerting-service

- [x] ✅ [CODE] P2. alerting-service: wire `AlertCode.RISK_RULE_BLOCKED` / `RISK_RULE_MONITOR_FIRED` into
      `rules/risk_threshold_rules.py` output (CRITICAL→BLOCKED, WARNING→MONITOR_FIRED). — alerting-service@`9279d82`
      (evaluate_risk_thresholds stamps alert_code on every emitted alert; both codes carry UAC routing per
      test_alert_code_parity; QG exit 0). Source: alerting_fp_rate.
- [x] ✅ [CODE] P2. alerting-service: add structured GCS quietness-report emission
      (`events/alerting-service/{date}/quietness-{run_id}/report.jsonl`: alert_code/fires/suppressed/fp_count/
      fp_rate/threshold). — alerting-service@`e2163a5` (AlertStorageStore.write_quietness_report mirrors
      write_alert_history; called from \_run_batch_replay; run-level aggregate row keyed alert_code="\*" since per-code
      FP tracking isn't instrumented yet — deeper per-code split is the BLOCKED-OPERATOR-DECISION ml-baseline item
      below). Source: alerting_fp_rate.
- [x] ✅ [CODE] P1. alerting-service: publish `RECON_FREEZE_ARMED` — **BUILT (alerting-side publisher).** The issue-doc
      framing ("add `alert_code: AlertCode.RECON_FREEZE_ARMED`") was WRONG — `RECON_FREEZE_ARMED` is NOT an `AlertCode`
      member, it's a **coordination/PubSub event** on `reconciliation-freeze` consumed by execution-service
      `preflight/recon_freeze.py` `ReconFreezeChecker.arm()`. Shipped the real publisher (observability_master G12 P0):
      — alerting-service@`a04bbf2` (QG exit 0) — `recon_freeze_publisher.py` (`publish_recon_freeze_armed`/`lifted` via
      `publish_coordination_event`; symbol-scoped vs account-wide per operator 2026-06-01) +
      `recon_freeze_event_handler.py` (wires the previously-orphan `evaluate_recon_age`/`evaluate_immediate_sev0` →
      route CRITICAL → arm freeze) + `evaluate_immediate_sev0` account_id/client_id propagation + synthetic test.
      **Execution-side subscriber + per-incident emit remain `execution_master` G12 P1** (consume the event → `arm()`) —
      the full chain isn't live until that lands. Source: batch_live_reconciliation_service_audit G12 /
      observability_master G12.
- `NEEDS-LIVE` [DATA] P3. alerting-service: ML threshold baseline for the 5 `ml_*` codes (ML inference not yet live) +
  `tick_staleness_seconds` per-venue baseline (needs live MTDS feeds). **RECLASSIFIED 2026-06-02: this is NEEDS-LIVE,
  NOT an operator decision** — the thresholds can't be empirically baselined until `ml-inference-service` + live feeds
  run; sensible defaults hold meanwhile; auto-resumes (no approval needed). Migrated to `observability_master` § P3
  (named successor). **Source doc `alerting_fp_rate_analysis` ARCHIVED 2026-06-02** → `plans/archive/issues/` (its other
  two action items shipped: GCS FP-log path alerting@`e2163a5`, risk-rule AlertCode alerting@`9279d82`). Source:
  alerting_fp_rate.

## unified-trading-api

- [x] ✅ [CODE] P2. unified-trading-api: `services/pbm_performance.py:46` → call strategy-service/position pnl route
      instead of the dead `http://position-balance-monitor:8080`; clean stale `workspace-manifest.json:1570` PBMS
      stanza. — unified-trading-api@`77bbae1` (PR #3, quality-gates-v2 ✓; `_get_pbm_client()` resolves
      `LIVE_SERVICE_STRATEGY_URL` config-bootstrap slot + builds real client targeting
      `/api/v1/accounts/{id}/pnl-series` — the HTTP client already built that route, it was just never wired; dead
      position-balance-monitor host retired from docstrings. **workspace-manifest.json does NOT exist in this repo**
      (verified ls/grep/find) → PBMS-stanza cleanup is N/A here, explaining the earlier pass's "couldn't locate it").
      Source: batch_live_reconciliation_service_audit §9.2.

## deployment-service

- [x] ✅ [INFRA] P1. deployment-service: schedule `scripts/vm/cleanup_old_tarballs.py` (currently 0 schedule refs) via a
      Cloud Run Job + Cloud Scheduler `--keep 5`, `terraform/gcp/tarball_cleanup_scheduler.tf` following the
      `manifest_consolidator_scheduler.tf` pattern; add an `owner/cadence/verifier/last_executed` runbook block. —
      deployment-service@`840c9a5` (single Cloud Run Job `${env_prefix}-tarball-cleanup`, daily `0 2 * * *` UTC, runbook
      `runbooks/tarball_cleanup_maintenance.md` with all 4 fields). TF authored only — `tofu apply` is the separate
      operator-gated item below. ⚠️ deployment-service QG has 2 PRE-EXISTING test timeouts
      (`test_data_status_queries.py`/`test_missing_data_per_service.py` sqlalchemy-import) + coverage 69.53%<70% on
      files not touched by this change (a `.tf`+`.md` add cannot affect Python coverage) — flagged for the test owner.
      Source: deployment_scripts_bucket.
- [x] ✅ [DOC] P2. deployment-service: fix cosmetic ASCII-art bucket labels in `docs/DEPLOYMENT_GUIDE.md` +
      `DEPLOYMENT_GUIDE_FEMI.md` (~L391-393) to env-tiered names. — STALE PREMISE / not actionable:
      `DEPLOYMENT_GUIDE.md` is only 58 lines (no L391-393, no ASCII bucket diagram) and `DEPLOYMENT_GUIDE_FEMI.md` does
      not exist in the repo. Nothing to fix; source-doc claim predates a doc rewrite. Source: gcs_hive_partition.

## unified-trading-pm — codex / doc-drift

- `BLOCKED-DISCIPLINE` [DOC] P2. PM: flip the D14 checkbox in `defi_code_codex_drift` + audit-result doc, update
  `defi-data-types-catalog.md` body + `defi-canonical-naming-ssot.md` fan-out rows. **RECLASSIFIED 2026-06-02 (slot 7):
  owned by the concurrent DeFi-venue / `defi_manifest_canonicalisation_2026_06_01` workstream, NOT this sweep.** The
  driving commit MTDS@`0a3a7071` is a **`semver-rollout[bot]` DeFi-canonicalisation commit** (collapsed
  `dex_pools`→`dex_pool_state` / `dex_swaps`→`dex_pool_swaps` + `pipeline_mode=` write partition) against the
  **operator-locked** SSOT `defi-canonical-naming-ssot.md` (locked 2026-06-01). Two reasons to leave it to that worker:
  (1) the source-doc D14 (2026-05-27) is **stale** — it claims canonical is `dex_pools` and the flip is deferred, but
  the operator-locked SSOT chose `dex_pool_state`/`dex_pool_swaps` and 0a3a7071 shipped that; the catalog/fan-out edits
  must reflect the locked names, which the canonicalisation worker owns. (2) `defi-canonical-naming-ssot.md` +
  `defi-data-types-catalog.md` are in that worker's active codex territory (coordination boundary: do not touch
  semver-rollout/DeFi-venue files). De-dup to `defi_manifest_canonicalisation_2026_06_01.md` §C0-RD. Source:
  defi_code_codex_drift D14.
- [x] ✅ [DOC] P2. PM: fix stale repo names in `codex/04-architecture/data-flow-map.md`
      (`trading-analytics-api`→`unified-trading-api`, `trading-analytics-ui`→`unified-trading-system-ui`). —
      unified-trading-pm@(this commit) (8 occurrences renamed; `{TRADING_ANALYTICS_GCS_BUCKET}` env var left intact).
      Source: batch_live_reconciliation_service_audit §7.
- [x] ✅ [DOC] P3. PM: add a "NOT YET DEPLOYED — tofu apply pending" warning to
      `codex/05-infrastructure/vm-log-archival.md` (cron authored but not applied). — unified-trading-pm@(this commit)
      (banner under the title: rolling log-archive + serial-capture schedulers TF-authored, not applied; snapshot +
      vm-logs stream are live). Source: fleet_audit_triad.
- [x] ✅ [DOC] P3. PM: B2 codex marker reconciliation — replace `zero_activity=True` / `ZERO_ACTIVITY_BAR` with
      `staleness_seconds>0 + trade_count==0` in `honest-absence-downstream-handling.md` +
      `live-pipeline-architecture.md` (no code consumers — pure doc drift). — unified-trading-pm@(this commit) (done
      DELIBERATELY per B2's HARD-RULE note: ruled on the model split FIRST — cefi/tradfi/defi = dense forward-fill,
      marker `staleness_seconds>0 + trade_count==0`; prediction Category-D = NaN-OHLC nullable variant. Added marker-
      reconciliation banners to the §"Zero-activity-bar shape" case-D section (honest-absence) + the 4-category live-gap
      table (live-pipeline), noting the `zero_activity=True` column was never built — carry-forward shipped via
      `_finalize_session_grid`; legacy `ZERO_ACTIVITY_BAR` label retained for continuity. **Residual:** 3 sibling docs
      still carry the legacy token (`00-SSOT-INDEX.md`, `batch-live-architecture.md`, `alerting-batch-live.md`) — minor
      doc-drift follow-up outside this item's named 2-file scope.) Source: fleet_audit_triad.
- [x] ✅ [DOC] P1. PM: write `codex/06-coding-standards/adapter-finalization-contract.md` + a per-adapter density
      section in `honest-absence-downstream-handling.md` (after the MDPS workstream lands). —
      unified-trading-pm@`5c7aedc23` (already landed by the MDPS leading-NaN workstream: full finalization contract doc
      (84L, close-driven vs state_col modes + per-adapter table) + "Per-adapter density contract" section
      §honest-absence L1425; verified as-shipped against base_adapter.\_finalize_session_grid signature 2026-06-02).
      Source: mdps_state_adapter_leading_nan.

## E2E pipeline manifest + data-status wiring (operator request 2026-06-02: "UAC/IS/MTDS/MDPS/features/strategy/execution all hooked up for E2E; data manifest + data status; deployment UI/API understand + show them")

> Scope chosen by operator = **verify + document** (no new UI feature this pass). Verified state: all 6 producing
> services emit manifest rows (UAC schema-only); deployment-api `/api/data-status/*` reads each service's bucket;
> manifest v9 schema can represent every hop. Three gaps named below. Coordinate with the in-flight
> `downstream_services_manifest_canonicalisation_2026_06_01.md` (deployment-api/UI preflight "agent B" + slot-2 DeFi).

- [x] ✅ [DOC] P1. Write the E2E manifest-wiring codex doc mapping all 7 services + the 3 layers + named gaps. —
      unified-trading-pm@`a28e2b1b4` (`codex/04-architecture/e2e-pipeline-manifest-wiring.md`).
- [x] ✅ [TEST] P1. Add a SIT introspection test asserting the IS→MTDS→MDPS→features→strategy readiness chain is
      connected + manifest schema carries every stage-key column + surfaces the missing execution hop as an `xfail`. —
      system-integration-tests@`29e0a75` (`tests/unit/test_pipeline_manifest_wiring.py`; 6 passed + 1 xfail[G-EXEC]).
      Verified: ruff + ruff-format + basedpyright + import-patterns (0 violations) + pytest green on the file; repo-wide
      SIT QG carries a PRE-EXISTING non-fatal coverage-floor ❌ (`MIN_COVERAGE=2<70`, no exception file on origin) — not
      caused by this additive test; LDR has no remote CI.
- [x] ✅ [CODE] P2. unified-trading-library: wire GAP **G-EXEC** — added `execution-service` →
      `UpstreamDependency("strategy_instructions", "strategy-service")` to `PIPELINE_DEPENDENCIES`
      (`dependency_check.py`). Diagnosed (read both sides): execution's batch loader reads `strategy_instructions`; both
      `strategy_orders`/`strategy_instructions` resolve to the `strategy-store` bucket that strategy-service writes
      (`service_name="strategy-service"`); `check_upstream_ready` filters by date+service_name only. Declarative — no
      runtime consumer of `PIPELINE_DEPENDENCIES` in execution today, so additive + safe. —
      unified-trading-library@`87f36546` + system-integration-tests@`8cbeb83` (xfail dropped → 7/7 pass) + codex@(this
      commit). ruff+basedpyright clean; 33 dependency_checker tests pass. Source: e2e-pipeline-manifest-wiring (G-EXEC).
- [ ] [CODE] [UI] P2. deployment-ui: fix GAP **G-UI** — `DataStatusTab.tsx` `DATA_PIPELINE_SERVICES` hardcodes stale
      `features-cefi/defi/tradfi/prediction-service` names + omits strategy-service, diverging from the backend
      `SERVICE_TO_KIND` consolidated families (`features-delta-one/volatility/onchain/sports-service`). Make the list
      UAC/discovery-driven (or align to the backend kinds) + surface strategy-service in the pipeline view. Playwright
      gate applies (`pw:L2 ✓` + regression spec). Source: e2e-pipeline-manifest-wiring (G-UI).
- [ ] [CODE] P3. deployment-api + deployment-ui: GAP **G-TRACE** — add a cross-service E2E trace
      (`/api/data-status/pipeline-trace?instrument&date`) threading one instrument/date through all stages with per-hop
      `capture_status`, + a UI view. Larger feature; coordinate with the in-flight data-status canonicalisation slot.
      Source: e2e-pipeline-manifest-wiring (G-TRACE).
- [ ] [CODE] P3. execution-service: reconcile `service_name` drift — `results/save_operations.py` writes
      `"execution-service"` but `cli/backtest.py` writes `"execution-services"` (plural); one producer must use one
      canonical `service_name`. Source: e2e-pipeline-manifest-wiring (smaller findings).
- [ ] [BUILD] P2. system-integration-tests: full `scripts/quality-gates.sh` exits 1 on a PRE-EXISTING
      `Manifest import     alignment` violation — `pyproject.toml` declares `alerting-service` + `client-reporting-api`
      but neither is imported anywhere in the repo. Either import them in a smoke test or drop the two declarations
      (coordinate with the already-dirty foreign `uv.lock` in this worktree — do not stomp). Also a standing non-fatal
      coverage-floor ❌ (`MIN_COVERAGE=2<70`, no `.coverage-floor-exception.md`) needs a human-approved exception file.
      Surfaced 2026-06-02 while landing `tests/unit/test_pipeline_manifest_wiring.py` (that file itself is fully
      gate-clean). Source: e2e-pipeline-manifest-wiring (SIT QG repo-state).

## Operator-gated infra (NOT credentials — ADC admin perms exist; runs after code lands)

- [ ] [INFRA] P1. `tofu apply` the `tarball_cleanup_scheduler` (after TF authored above). Source:
      deployment_scripts_bucket.
- [ ] [INFRA] P2. `tofu apply` `vm_log_archival_scheduler.tf` + `vm_serial_capture_scheduler.tf` +
      `api_host_auto_reboot.tf`; verify `apply_resource_limits.sh` (MemoryMax=56G) is live on the API host. Source:
      fleet_audit_triad + api_host_chronic_impairment.
- [ ] [INFRA] P2. deployment-scripts bucket: add prefix-scoped lifecycle rules (`vm-logs/`>14d, `log-archive/`>90d) +
      cross-bucket soft-delete bloat audit via `gcs_bucket_stats.py --bloat_pct`. Source: deployment_scripts_bucket.

## BLOCKED clusters (NOT credentials — discipline / coordination)

- **DeFi/TradFi backfill VM cluster** — uniswap_v3 28k retry, tradfi 712-day reprocess, MDPS cefi backfill, the C0/C2
  DeFi-manifest walk. `BLOCKED-DISCIPLINE`: gated on the harsh-side `cefi_manifest_canonicalisation_2026_06_01` HOLD
  banner + the operator directive to "run all chain-affected venues together, not piecemeal". Code for these is already
  on LDR; only the coordinated live run remains. Do NOT cross the HOLD.
- **stash-archive purge** (`shared_stash_pile_archive_cleanup`) — time-gated to 2026-06-08; not actionable today.

## Per-source-doc archive criterion

A source issue doc archives to `plans/archive/issues/` (with `[unlock-plan]` in the commit for locked docs) once
**every** item it contributed here is `- [x] ✅` or carries an operator-acked `BLOCKED-*`/`NEEDS-LIVE` line. Docs gated
on a BLOCKED cluster (cefi_processed_candles, uniswap_28k, fleet_audit_triad, running_vm_fleet, shared_stash) stay open
with updated status until their cluster clears.
