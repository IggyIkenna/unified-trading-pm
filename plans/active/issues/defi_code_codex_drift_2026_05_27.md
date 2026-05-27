---
title: "DeFi pipeline — code↔codex drift (audit 2026-05-27)"
created: 2026-05-27
author: harsh
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
| D3  | `DefiLendingIndicesAdapter` exists + decorator-registered + UAC `needs_candle_processing("lending_indices")=True`, but it's **not imported** in top-level `app/adapters/__init__.py` → silently never runs. Intent is bypass (features read lending raw). | code bug     | **DEFERRED-UNTIL-PIPELINE-DONE** |
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
- [ ] [DOC] P2. D6/D12 — full `defi-data-types-catalog.md` reconciliation: add the ~8–13 missing data_types
      (`lst_rates`, `vault_share_price`, `liquidations`, `risk_params`, `rewards`, `eigenlayer_rewards`,
      `native_staking_rates`, `aggregator_route`, `restaking_rewards`, `governance_proposals`, …) + fix `oracle_prices`
      (add Pyth) / `lending_indices` (add Spark + Compound V3) sources.
- [ ] [DOC] P2. D9/D11 — update `defi-venue-protocol-catalogue.md`: add EULER_V2 / BENQI / VENUS / MARGINFI / SOLEND /
      SOLAYER / PICASSO / CAMBRIAN; flag TRADER_JOE / VELODROME / GMX-AVALANCHE as empty/deprecated.

Code (DEFERRED-UNTIL-PIPELINE-DONE; other agents are correcting code — re-verify current state first):

- [ ] [CODE] P2. D3 — set `needs_candle_processing("lending_indices")=False` (UAC) + delete dead
      `DefiLendingIndicesAdapter` + fix `app/adapters/__init__.py` comment; QG green.
- [ ] [CODE] P2. D10 — RADIANT: add `PROTOCOL_CAPABILITIES`+`SUBGRAPH_IDS` OR downgrade from `DEFI_VENUE_PHASE=live` (a
      live venue with no capability/subgraph backing cannot fetch). Confirm intent with operator/Ikenna.
- [ ] [CODE] P3. **FOR-DECISION** D7 — `bloxroute` relay URLs in `mev_events_handler.py:42-43`: operator call on whether
      the removed-providers rule covers MEV-Boost relays; delete stale `mev_events_handler.py.bak` regardless.
- [ ] [CODE] P3. **FOR-DECISION** D8 — Starknet `infura_compatible` template (`_defi_chain_data.py:734`): keep+rename or
      remove; drop the `gas_fee_handler.py:78` infura comment.
- [ ] [CODE] P3. **FOR-DECISION** D13 — consolidate `governance_events` vs `governance_proposals` handlers to one path.
- [ ] [INFRA] P3. D2 — delete legacy `lst_rates/`/`lending_indices/`/`dex_pools/` prefixes in
      `market-data-tick-defi-prd` (via `gcs_delete_object`) after dedicated buckets confirmed authoritative.
