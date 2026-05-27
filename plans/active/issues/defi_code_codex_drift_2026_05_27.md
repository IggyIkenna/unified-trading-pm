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
the codex SSOTs. Full register: [`codex/02-data/defi-data-pipeline.md`](../../../codex/02-data/defi-data-pipeline.md)
§1. Five drift points; two are actionable now (codex-doc), one is a real latent code bug (deferred), one is data cleanup
(deferred), one already self-bannered.

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

- [ ] [DOC] P2. D1 — update `defi-data-types-catalog.md` to canonical data_type names
      (`dex_swaps`/`dex_pool_state`/`lending_indices`/`perp_funding`); reconcile instrument-type map.
- [ ] [CODE] P2. **DEFERRED-UNTIL-PIPELINE-DONE** D3 — set `needs_candle_processing("lending_indices")=False` (UAC) +
      delete dead `DefiLendingIndicesAdapter` + fix `app/adapters/__init__.py` comment; QG green.
- [ ] [INFRA] P3. **DEFERRED-UNTIL-PIPELINE-DONE** D2 — delete legacy `lst_rates/`/`lending_indices/`/`dex_pools/`
      prefixes in `market-data-tick-defi-prd` (via `gcs_delete_object`) after dedicated buckets confirmed authoritative.
