---
doc_type: issue
title:
  Funding + staking downstream readers are canonical on the production path — 4 stale old-form readers + 1 latent
  PATH_REGISTRY trap to clean
summary:
  A 2026-07-21 trace confirms every PRODUCTION consumer of funding (perp_funding + derivative_ticker funding columns)
  and staking (lst_rates) reads the canonical env-tiered market-data-tick-{ag}-prd bucket via resolve_bucket_name — zero
  live old-form readers on the engine data path. The known PATH_REGISTRY/build_bucket 404 defect is a LATENT trap
  (reached only by UTL's own thin domain clients, which have zero non-test runtime callers), not a live bug. Remaining
  cleanup of 4 non-runtime diagnostic/campaign scripts (worst = trace_carry_staked_basis.py, silent-empty staking) + 1
  CLI env-fallback still reference deleted buckets, and the UTL PATH_REGISTRY market-data-tick rows are still un-tiered.
status: open
nature: issue
asset_group: [defi, cefi]
stage: [data]
repos: [unified-trading-library, strategy-service, execution-service, features-service]
scope: [engineer, admin]
tags: [funding, staking, lst-rates, perp-funding, canonical-reader, path-registry, silent-empty, bucket-resolution]
related:
  [
    silent_wrong_answer_bucket_resolution_class_2026_07_20.md,
    ../../codex/05-infrastructure/bucket-isolation-model.md,
    ../../codex/06-coding-standards/canonical-write-guard-contract.md,
  ]
created: 2026-07-21
last_updated: 2026-07-21
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source:
  operator question 2026-07-21 — "all downstream code using canonical buckets? funding + staking from canonical data?"
depends_on: []
---

# Funding + staking downstream readers — canonical on the production path (audit + cleanup)

> **Verdict (2026-07-21): YES.** Every production/runtime consumer of funding and staking rates reads the canonical
> env-tiered `market-data-tick-{ag}-prd-{pid}` bucket via `resolve_bucket_name(kind="tick-data"|"market-data", …)`.
> **Live old-form readers on the engine data path: ZERO.** The known PATH_REGISTRY 404 defect is a LATENT trap, not
> reached by any funding/staking reader. What remains is cleanup of stale diagnostic scripts + the un-tiered UTL
> registry rows.

## Canonical production consumers (verified by source read, file:line)

- **Funding** — strategy `CanonicalPerpFundingProvider` (`engine/core/canonical_perp_funding_provider.py:134`,
  `kind="tick-data"/defi`); features delta-one loader + cefi funding corpus (`delta_one/app/core/data_loader.py:52,55`;
  `cefi/calculators/perp_funding_corpus.py:254-255`); execution `data/defi_lateral_loader.py:52-54`
  (`perp_funding`→`_SHARED_LATERAL_BUCKET`, canonical); ml via the folded `*_features` bucket. Execution
  funding-tracker/accrual/matching consume funding as passed-in feature VALUES (no bucket read).
- **Staking (LST)** — features `OnChainDataLoader` (`onchain/app/core/data_loader.py:488→197`,
  `get_bucket_name("market_data","defi")` → env-tiered); execution `data/defi_lateral_loader.py:60,238,280`
  (`lst_rates`, canonical prefix); features `dependency_checker.py:151` (repointed off the deleted `lst-rates-{pid}`
  2026-07-14). Staking reaches strategy as a COMPUTED feature (`gcs_feature_provider.py:96`, `kind="features"`).

## Cleanup todos (non-runtime today, but latent traps)

- [ ] 1. [CODE] P2. **`strategy-service/scripts/trace_carry_staked_basis.py` — SILENT-EMPTY staking reader (highest
      signal).** `_LST_RATES_BUCKET_TEMPLATE="lst-rates-{project_id}"` (`:81,:198`) + legacy `lst_rates/date=` prefix
      (`:204`) → lists the DELETED `lst-rates-{pid}` bucket → returns None → every slot logs "no on-chain lst_rates" and
      skips (realised staking carry collapses to zero). It is a `# Lifecycle: campaign` script (NOT the production
      engine, superseded by `trace_all_carry_archetypes.py`), but repoint `_load_lst_rate_series` to
      `resolve_bucket_name(kind="tick-data", asset_group="defi")` + `data_type=lst_rates` (mirror
      `execution defi_lateral_loader.py`) or delete as superseded.
- [ ] 2. [CODE] P2. **3 funding diagnostic scripts on the deleted `perp-funding-{pid}` bucket** —
      `strategy-service/scripts/trace_carry_staked_basis.py`, `trace_arbitrage_price_dispersion.py`,
      `probe_funding_rate_dispersion_coverage.py` (`_PERP_FUNDING_BUCKET_TEMPLATE="perp-funding-{project_id}"`, deleted
      2026-07-10) → read empty / list-fail. Repoint to `resolve_bucket_name(kind="tick-data", asset_group="defi")` or
      delete.
- [ ] 3. [CODE] P2. **`execution-service/.../cli/defi_arbitrage_dispersion_decision_trace.py:381`** — env-fallback
      `cfg.market_data_source_bucket_cefi or f"market-data-tick-cefi-{pid}"` (old flat un-tiered form). Reached only if
      the env var is unset (canonical-injected in prod). Drop the flat fallback → raise or resolve canonically.
- [ ] 4. [CODE] P1. **UTL `PATH_REGISTRY` market-data-tick rows are still un-tiered (the latent 404 trap).**
      `unified-trading-library/.../config_interface/paths/registry.py` rows for `raw_tick_data` / `processed_candles` /
      `l2_book_checkpoints` / `liquidation_clusters` / `liquidity_features_1m` resolve to un-tiered
      `market-data-tick-{category}-{pid}` (no `-prd-`, the deleted form). ONLY runtime callers are UTL's own
      `MarketTickDomainClient.get_tick_data`/`get_available_dates` + `MarketCandleDomainClient.get_candles`
      (`domain_client/clients/market_data.py:56`, `build_bucket("raw_tick_data", …)`) — verified ZERO non-test
      downstream callers. Repoint these rows to the env-tiered yaml name (as the Group-B rows already were), or delete
      the thin clients, so a future consumer wiring them cannot silently 404. See the bucket-name resolution authority
      section of `codex/05-infrastructure/bucket-isolation-model.md`.
- [ ] 5. [DATA] P2. **`features-service/.../onchain/calculators/perp_funding_rates_defi.py:58`** — reads the CANONICAL
      bucket but a path template `perp_funding/{venue}/date=` that never existed → returns empty. Pre-existing bug,
      superseded by `CanonicalPerpFundingProvider`; delete the dead MVP reader or fix its path to the v9 layout.

## Not a bug

The verdict is YES. This issue tracks the removal of latent traps, not a live data-correctness failure — no production
funding/staking reader is on an old form today. Same CLASS as
`silent_wrong_answer_bucket_resolution_class_2026_07_20.md` (which caught the runtime `eigen_rewards_calculator`
fragment-name 404 — already fixed); this doc is the funding/staking-scoped complement.
