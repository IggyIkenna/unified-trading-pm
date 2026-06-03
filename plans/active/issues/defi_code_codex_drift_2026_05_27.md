---
title: "DeFi pipeline — code↔codex drift (audit 2026-05-27)"
created: 2026-05-27
source:
  - codex/02-data/defi-data-pipeline.md
  - codex/02-data/data-lineage-MTDS-features-ml.md
  - codex/02-data/defi-data-types-catalog.md
locked_by: live-defi-rollout
status: active
priority: P2
---

# DeFi pipeline — code ↔ codex drift (audit 2026-05-27)

## What I found

Re-read the actual Python (MTDS / MDPS / UAC / features-service) on 2026-05-27 and cross-checked GCS, comparing against
the codex SSOTs. **Comprehensive audit record (13 findings D1–D13, audit-result format):**
[`plans/audit/results/defi_pipeline_code_codex_drift_2026_05_27.md`](../../audit/results/defi_pipeline_code_codex_drift_2026_05_27.md).
In-codex summary: [`codex/02-data/defi-data-pipeline.md`](../../../codex/02-data/defi-data-pipeline.md) §1. This issue
doc is the **actionable tracker** — todos below. The first pass surfaced 5 architectural drifts (D1–D5); a broadening
pass added D6–D13 (catalog completeness, venue drift, banned `bloxroute` relay, RADIANT unbacked, infura, governance
dup).

| #   | Drift                                                                                                                                                                                                                                                     | Side         | Status                           |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------ | -------------------------------- |
| D1  | `defi-data-types-catalog.md` uses stale names `swap_events`/`pool_state`/`lending_metrics`/`funding_rates`; code writes `dex_swaps`/`dex_pool_state`/`lending_indices`/`perp_funding`                                                                     | codex-doc    | **actionable now**               |
| D2  | Legacy stale prefixes `lst_rates/`,`lending_indices/`,`dex_pools/` inside `market-data-tick-defi-prd` (stop 2026-04-14); canonical data is in dedicated buckets `lst-rates-*`/`lending-indices-*`/`dex-pools-*`                                           | data cleanup | **DEFERRED-UNTIL-PIPELINE-DONE** |
| D3  | `DefiLendingIndicesAdapter` exists + decorator-registered + UAC `needs_candle_processing("lending_indices")=True`, but it's **not imported** in top-level `app/adapters/__init__.py` → silently never runs. Intent is bypass (features read lending raw). | code bug     | **✅ RESOLVED 2026-05-27**       |
| D4  | features-onchain reads bypass types raw from MTDS                                                                                                                                                                                                         | —            | aligned (no action)              |
| D5  | `data-lineage` per-layer paths use legacy `{category}` bucket patterns                                                                                                                                                                                    | codex-doc    | tracked ML-14 (rewrite)          |

## Why it matters

- **D3 is the substantive one.** A lending-candle adapter is wired in two of three places (UAC gate + decorator) but
  disabled by a missing import. Today this is benign (it matches the intended bypass behaviour by accident, and features
  read `lending_indices` raw), but it is a tripwire: anyone who "fixes" the missing import would silently start
  producing unused `lending_ohlcv` candles and flip the gate's behaviour. The three sources (UAC gate, MDPS adapter
  registry, features bypass contract) must agree on ONE answer: lending_indices is bypass ⇒ gate should be `False` and
  the adapter deleted.
- **D1/D5** are documentation drift that misleads downstream consumers reading the catalog/lineage for canonical names
  and bucket patterns.
- **D2** is dead data occupying the canonical bucket; harmless but should be cleaned to avoid confusion during the
  bucket-SSOT consolidation.

## Recommended decision

- **Now (codex-doc, safe):** update [`defi-data-types-catalog.md`](../../../codex/02-data/defi-data-types-catalog.md)
  headings + instrument-type map to canonical `data_type=` names (D1). (D5 rewrite stays under the existing ML-14 item.)
- **After the running backfill completes (code):** for D3, set `needs_candle_processing("lending_indices") = False` in
  UAC `registry/market_data_categories.py`, delete the dead `DefiLendingIndicesAdapter`
  (`market-data-processing-service/.../app/adapters/defi/lending_indices_adapter.py`), and fix the misleading comment in
  `app/adapters/__init__.py`. Single code path, no shim. Re-run QG.
- **After the run (data):** for D2, delete the legacy `lst_rates/`,`lending_indices/`,`dex_pools/` prefixes under
  `market-data-tick-defi-prd` via `gcs_delete_object` once the dedicated buckets are confirmed authoritative.

## Todos

Codex-doc (safe now):

- [x] [DOC] P2. D1 — `defi-data-types-catalog.md` renamed to canonical data_type names
      (`dex_swaps`/`dex_pool_state`/`lending_indices`/`perp_funding`) + instrument-type map + staleness banner. ✅ this
      session.
- [x] [DOC] P2. D6/D12 — `defi-data-types-catalog.md` reconciled: § "Additional data types" added (~12 types:
      `lst_rates`, `vault_share_price`, `liquidations`, `risk_params`, `utilization`, `rewards`, `eigenlayer_rewards`,
      `native_staking_rates`, `aggregator_route`, `protocol_outages`, `governance_proposals`, `dex_pool_swaps`,
      `restaking_*`) + `oracle_prices` (+Pyth) / `lending_indices` (+Spark/Compound V3) / `perp_funding` sources fixed +
      dedicated-bucket note + banner resolved. ✅ this session.
- [x] [DOC] P2. D9/D11 — `defi-venue-protocol-catalogue.md` gained "Registry inconsistencies + pending venues" section
      (EULER_V2/VENUS/BENQI/RADIANT/MARGINFI/SOLEND live-without-capability; SOLAYER/PICASSO/CAMBRIAN
      capability-without-venue; HYPERLIQUID/ASTER phase mismatch). Catalogue was ~90% complete; the gaps are
      code-registry states, documented + cross-linked. ✅ this session.

Code (DEFERRED-UNTIL-PIPELINE-DONE; other agents are correcting code — re-verify current state first):

- [x] ✅ [CODE] P2. D3 — `needs_candle_processing("lending_indices")=False` (UAC@96db70a6, reverts drift 4c98a635) +
      dead `DefiLendingIndicesAdapter` deleted + `app/adapters/__init__.py` comment fixed + bypass test moved to
      `BYPASS_TYPES` (MDPS@5c2b612) + epic DeFi-V note corrected (PM@e5742c656). All three sources now agree:
      lending_indices is bypass. QG green (ruff + basedpyright + `test_defi_bypass_routing` 41/41). — 2026-05-27.
- [ ] [CODE] P2. D10 (generalized) — 6 venues `DEFI_VENUE_PHASE=live` with no `PROTOCOL_CAPABILITIES`/`SUBGRAPH_IDS`
      (EULER_V2, VENUS, BENQI, RADIANT-ETH, MARGINFI, SOLEND): add backing OR downgrade/register. Confirm intent with
      operator/Ikenna. **The 3 inverse venues (SOLAYER/PICASSO/CAMBRIAN: capability-without-venue) are RESOLVED — fully
      removed 2026-06-02 (operator decision, no usable/decodable data source); UAC capabilities + IS adapters wiped.
      SSOT: `plans/active/issues/issue_docs_remediation_sweep_2026_06_02.md`.**
- [ ] [CODE] P3. D14 — `dex_pools_handler.py`: manifest records canonical `data_type="dex_pools"` (L62) but parquet
      writes `data_type="dex_pool_state"` (L569) → manifest≠data divergence. Canonical is `dex_pools`. The write-flip
      CANNOT be done standalone — it would split forward-writes (`dex_pools/`) from historical (`dex_pool_state/`),
      violating single-walk discipline. **Bundled into the deferred GCS rename**: `plans/epics/mtds_mdps_master.md`
      Phase 9 (`dex_pool_state`→`dex_pools`), which now lists the `write_defi_rows(data_type=...)` handler flip
      alongside the on-disk hive rename so they land together. (diagnosed 2026-05-27)
- [ ] [CODE] P3. D15 — HYPERLIQUID + ASTER are `DEFI_VENUE_PHASE=pipeline` but `perp_funding_handler` actively collects
      them; reconcile the phase label (→ live, or confirm cefi-axis classification).
- [ ] [CODE] P3. **DECIDED 2026-05-27 → REMOVE (deferred)** D7 — usage audit found **nil active downstream consumption**
      of bloxroute/`mev_events` relay data: bloxroute already removed as the mempool feed (`sandwich_theoretical.py` is
      a theoretical-only tracer, not a live engine). Remove the 2 bloxroute URLs from `mev_events_handler.py:42-43`
      `MEV_BOOST_RELAYS` (keep Flashbots/agnostic/ultra_sound) + delete `mev_events_handler.py.bak`. No Ikenna; codex
      docs already mark Bloxroute "removed".
- [ ] [CODE] P3. **DECIDED 2026-05-27 → REMOVE (deferred)** D8 — **infura already decommissioned workspace-wide
      2026-05-22** (execution `chain_config.yaml:14`); remaining refs are stale. Remove the Starknet `infura_compatible`
      template (`_defi_chain_data.py:734`) + the `gas_fee_handler.py:78` comment. No Ikenna; codex docs already mark
      Infura "removed/banned".
- [x] [CODE] P3. **DECIDED 2026-05-27 → KEEP** D13 — `governance_proposals` is an intentional unregistered scaffold for
      the Phase-4B simulation harness (not wired in `cli/main.py`), so it is NOT an active parallel path vs
      `governance_events`. No change; documented in the catalog § "Additional data types".
- [~] [INFRA] P3. D2 — delete legacy `lst_rates/`/`lending_indices/`/`dex_pools/` prefixes in
  `market-data-tick-defi-prd` (via `gcs_delete_object`) after dedicated buckets confirmed authoritative. `lst_rates/`
  **DONE 2026-05-28**: 1,200 date-prefix parquets deleted; 64,373 stale manifest rows pruned. `lending_indices/` +
  `dex_pools/`: deferred until Gate 2 Solana migration completes (canonical buckets must be confirmed superset first).
  Solana instrument_types added to codex — PM@(Gate 6 commit). Cited: UAC@7e9f4ad9 + UAC@90b2bb9d + MTDS@c38d1ca3 +
  MTDS@896d5c9 (Gate 5).
