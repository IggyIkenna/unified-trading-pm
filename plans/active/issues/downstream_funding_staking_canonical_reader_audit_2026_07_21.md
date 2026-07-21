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

- [x] 1. [CODE] P2. **`strategy-service/scripts/trace_carry_staked_basis.py` — SILENT-EMPTY staking reader (highest
      signal).** `_LST_RATES_BUCKET_TEMPLATE="lst-rates-{project_id}"` (`:81,:198`) + legacy `lst_rates/date=` prefix
      (`:204`) → lists the DELETED `lst-rates-{pid}` bucket → returns None → every slot logs "no on-chain lst_rates" and
      skips (realised staking carry collapses to zero). It is a `# Lifecycle: campaign` script (NOT the production
      engine, superseded by `trace_all_carry_archetypes.py`), but repoint `_load_lst_rate_series` to
      `resolve_bucket_name(kind="tick-data", asset_group="defi")` + `data_type=lst_rates` (mirror
      `execution defi_lateral_loader.py`) or delete as superseded. **Done — DELETED (not repointed).**
      `trace_all_carry_archetypes.py` already fully supersedes it: verified it reads staking (`lst_yields` via
      `resolve_bucket_name(kind="features", asset_group="defi")`) and funding (`funding_oi` via the delta-one features
      bucket) canonically, has real coverage, and zero other files reference `trace_carry_staked_basis`. It had zero
      test coverage and zero non-self consumers. Repointing would have meant re-implementing what the superseding script
      already does correctly — deletion is the correct simplification.
      strategy-service@c09785a8a9e7e742761e47686e4be304adb086c9 (QG: 5261 passed, 0 failed, full gate green).
- [x] 2. [CODE] P2. **3 funding diagnostic scripts on the deleted `perp-funding-{pid}` bucket** —
      `strategy-service/scripts/trace_carry_staked_basis.py`, `trace_arbitrage_price_dispersion.py`,
      `probe_funding_rate_dispersion_coverage.py` (`_PERP_FUNDING_BUCKET_TEMPLATE="perp-funding-{project_id}"`, deleted
      2026-07-10) → read empty / list-fail. Repoint to `resolve_bucket_name(kind="tick-data", asset_group="defi")` or
      delete. **Done.** `trace_carry_staked_basis.py` deleted (see todo 1). `trace_arbitrage_price_dispersion.py` +
      `probe_funding_rate_dispersion_coverage.py` repointed to
      `resolve_bucket_name(kind="tick-data",     asset_group="cefi"|"defi")`. Adjacent fix in the SAME files (found
      while editing): both scripts' Tardis/perp_funding list prefixes were a STRICT full prefix
      (`.../asset_group=cefi/venue=.../data_type=.../`) that silently returns zero rows whenever the canonical v9
      `pipeline_mode={M}/` segment is present (confirmed via
      `market-tick-data-service/scripts/migrate_cefi_flat_to_v9_canonical.py` + UAC `canonical_path_violations` tests
      that `pipeline_mode` is a real, present-in-prod optional segment) — broadened to a day-level prefix +
      needle-filter (mirrors `execution-service/.../data/defi_lateral_loader.py`'s `build_partition_needles`), so the
      bucket-name fix isn't undermined by a still-too-strict prefix.
      strategy-service@c09785a8a9e7e742761e47686e4be304adb086c9 (same commit as todo 1; QG: 5261 passed, 0 failed).
- [x] 3. [CODE] P2. **`execution-service/.../cli/defi_arbitrage_dispersion_decision_trace.py:381`** — env-fallback
      `cfg.market_data_source_bucket_cefi or f"market-data-tick-cefi-{pid}"` (old flat un-tiered form). Reached only if
      the env var is unset (canonical-injected in prod). Drop the flat fallback → raise or resolve canonically.
      **Done.** Repointed to `resolve_bucket_name(cloud=get_cloud_provider(), kind="tick-data", asset_group="cefi")`.
      Found + fixed the IDENTICAL duplicated pattern in the sibling file
      `defi_target_universe_rebalance_recommender.py:241` in the same commit (same bug, same fix). NOT fixed (separate,
      larger, out-of-scope finding — flagged, not touched): both files'
      `_list_cefi_perp_symbols`/`_cefi_funding_per_coin` helpers list via a legacy `day={date}/category=cefi/venue=…`
      prefix (`category=`, not the v9 `asset_group=` key) — a distinct latent bug from the one this todo targets; needs
      its own audit given the wider blast radius (touches the CLI's whole cross-venue-funding read path, not just one
      bucket-name literal). execution-service@25739c4af6324278448f60dfe2f224ec90111e67 (QG: 7876 passed, 0 failed, full
      gate green).
- [ ] 4. [CODE] P1. **UTL `PATH_REGISTRY` market-data-tick rows are still un-tiered (the latent 404 trap).**
      `unified-trading-library/.../config_interface/paths/registry.py` rows for `raw_tick_data` / `processed_candles` /
      `l2_book_checkpoints` / `liquidation_clusters` / `liquidity_features_1m` resolve to un-tiered
      `market-data-tick-{category}-{pid}` (no `-prd-`, the deleted form). ONLY runtime callers are UTL's own
      `MarketTickDomainClient.get_tick_data`/`get_available_dates` + `MarketCandleDomainClient.get_candles`
      (`domain_client/clients/market_data.py:56`, `build_bucket("raw_tick_data", …)`) — verified ZERO non-test
      downstream callers. Repoint these rows to the env-tiered yaml name (as the Group-B rows already were), or delete
      the thin clients, so a future consumer wiring them cannot silently 404. See the bucket-name resolution authority
      section of `codex/05-infrastructure/bucket-isolation-model.md`. **NOT SHIPPED — code written + verified, blocked
      from committing by 2 independent external conditions (both confirmed 2026-07-21, neither caused by this fix):**
      (a) Also found + fixed a 3rd caller beyond the two named above:
      `unified_trading_library/domain_client/clients/liquidity.py`'s `LiquidityDomainClient` hits
      `l2_book_checkpoints`/`liquidation_clusters`/`liquidity_features_1m` via `build_bucket(...)` — also zero non-test
      callers workspace-wide, same latent-trap class. (b) Chose REPOINT over delete. For 4 of 5 rows (`raw_tick_data`,
      `processed_candles`, `l2_book_checkpoints`, `liquidation_clusters`) added the `-prd-` tier:
      `bucket_template="market-data-tick-{category}-prd-{project_id}"`. Verified via `gcloud storage buckets describe`
      that `market-data-tick-{cefi,defi}-prd-{pid}` return 403 (permission-denied — bucket EXISTS) not 404, confirming
      `-prd-` is correct. For `liquidity_features_1m`, `gcloud storage buckets describe` on
      `market-data-features-{cefi}-{prd-,}{pid}` returned a clean 404 in BOTH forms — that bucket-KIND never existed at
      all (not just missing a tier); repointed instead to the REAL, already-tiered shared features bucket
      `features-{category}-prd-{project_id}` (same literal the Group-B rows already use), since a same-family tier-only
      fix would still 404. **Exact fix (apply verbatim once unblocked — 5 one-line `bucket_template=` replacements in
      `unified_trading_library/unified_trading_library/config_interface/paths/registry.py`):** `raw_tick_data` +
      `processed_candles` + `l2_book_checkpoints` + `liquidation_clusters`: `"market-data-tick-{category}-{project_id}"`
      → `"market-data-tick-{category}-prd-{project_id}"`. `liquidity_features_1m`:
      `"market-data-features-{category}-{project_id}"` → `"features-{category}-prd-{project_id}"`. **Blocker 1
      (repo-wide, pre-existing, already tracked)**: `unified-trading-library`'s `quality-gates.sh` fails `pip-audit` on
      `pyasn1==0.6.3` (CVE-2026-59885/59886, transitive dep pinned in the committed `uv.lock`) —
      `Codex compliance FAILED: 1 violations (max allowed: 0)`, blocking quickmerge's Pass-1 sentinel for EVERY commit
      to this repo today, unrelated to any diff. Independently re-confirmed via the same `git stash`-isolation technique
      (my 5-row fix stashed away → identical failure persists) as
      `plans/active/issues/utl_pyasn1_cve_pip_audit_blocks_quickmerge_2026_07_21.md` (filed earlier today by another
      agent hitting the same wall on an unrelated diff) — see that doc for the fix todo (bump/patch `pyasn1`, out of
      scope for an inline bucket-tiering fix). **Blocker 2 (session-specific)**: a second concurrent agent had a live,
      uncommitted, actively-progressing edit on this SAME file (`registry.py`'s `"instruments"` `DataSetSpec` row —
      non-overlapping with the 5 rows this todo targets, confirmed via diff) for the ~70+ minutes this session ran;
      editing + shipping alongside their WIP was judged unsafe (their in-progress multi-file refactor spans
      `pipeline_mode_resolver.py` / `cloud_data_provider.py` / `manifest_writer/` / `instrument_lifecycle_loader.py` /
      `options_cluster_lookup.py` too) so the fix was applied, verified isolated via `git stash` (lint clean, typecheck
      clean, full test suite green EXCLUDING the pip-audit line), then fully reverted from the working tree (via the
      Edit tool, not shell `cp` — the harness re-syncs shell-level file changes against its own tracked Edit-tool state,
      so a raw `cp`-based revert does not actually take effect) to avoid colliding with their live WIP or leaving stale
      uncommitted state in a shared clone. **Round 2 action**: once
      `utl_pyasn1_cve_pip_audit_blocks_quickmerge_2026_07_21.md` is resolved AND the concurrent registry.py session has
      committed, apply the 5-line fix above (+ the `liquidity.py` finding from (a)) and ship via the normal quickmerge
      path — no re-investigation needed.
- [x] 5. [DATA] P2. **`features-service/.../onchain/calculators/perp_funding_rates_defi.py:58`** — reads the CANONICAL
      bucket but a path template `perp_funding/{venue}/date=` that never existed → returns empty. Pre-existing bug,
      superseded by `CanonicalPerpFundingProvider`; delete the dead MVP reader or fix its path to the v9 layout. **Done
      — FIXED (not deleted), because real production callers exist.** Contrary to this todo's "superseded / dead reader"
      framing, `compute_defi_funding_rates` has TWO live callers: `features_service/onchain/engine/orchestrator.py:774`
      (`_process_perp_funding_rates`, the live "perp_funding_rates" onchain feature group — runs the full per-day loop
      in live mode) and `features_service/onchain/live/perp_funding_compute_runner.py:59`. Deleting would have broken
      both. Fixed the path to the v9 canonical layout: added `_load_raw_frame()` (list day partition + needle-filter on
      `asset_group=defi/venue=HYPERLIQUID/data_type=perp_funding/`, mirroring the same optional-`pipeline_mode`-segment
      pattern as todo 2) replacing the broken `pl.read_parquet(gcs_glob)` on the nonexistent
      `perp_funding/{venue}/date=` layout. Added 2 new unit tests exercising `_load_raw_frame`'s needle-filter directly
      (with + without a `pipeline_mode=` segment present) plus updated the 6 existing tests to patch the new seam.
      features-service@31252ff748ac3edc014e364aa7be448b158f53eb (QG: 17778 passed, 0 failed, full gate green).

## Round 2 — deferred work after 2026-07-21

| Item                                                                                         | Status                                           | Blocker                                                                                                                             | Next step                                                                                                                                                                                                  |
| -------------------------------------------------------------------------------------------- | ------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Todo 4 (UTL PATH_REGISTRY bucket-tiering, 5 rows + `liquidity.py`'s `LiquidityDomainClient`) | Code written + isolation-verified, NOT committed | `utl_pyasn1_cve_pip_audit_blocks_quickmerge_2026_07_21.md` (repo-wide pip-audit CVE gate) + a concurrent live edit on the same file | Apply the verbatim fix documented under todo 4 above once both clear                                                                                                                                       |
| execution-service `category=cefi` legacy prefix (found under todo 3, NOT fixed)              | Flagged, not fixed                               | Out of scope — separate, wider-blast-radius audit                                                                                   | New issue doc if not already tracked; touches `_list_cefi_perp_symbols`/`_cefi_funding_per_coin` in both `defi_arbitrage_dispersion_decision_trace.py` and `defi_target_universe_rebalance_recommender.py` |

## Not a bug

The verdict is YES. This issue tracks the removal of latent traps, not a live data-correctness failure — no production
funding/staking reader is on an old form today. Same CLASS as
`silent_wrong_answer_bucket_resolution_class_2026_07_20.md` (which caught the runtime `eigen_rewards_calculator`
fragment-name 404 — already fixed); this doc is the funding/staking-scoped complement.
