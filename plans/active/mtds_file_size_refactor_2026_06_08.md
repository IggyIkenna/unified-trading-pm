---
title: "MTDS file-size refactor — split the 15 pre-existing >900-line source files (post-migration)"
created: 2026-06-08
parent_epic: mtds_mdps_master
assigned_vm: vm-cross-cutting
status: active
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 2
locked_by: live-defi-rollout
locked_since: 2026-06-08
source:
  - master_data_canonicalisation_migration_catalogue_2026_06_07.md (MTDS-QG P2 — Option A, operator 2026-06-08)
  - market-tick-data-service quality-gates.sh file-size gate (MAX_FILE_LINES=900, hard-fail, no baseline)
---

# MTDS file-size refactor — split the 15 pre-existing >900-line source files

> **Why this exists (operator decision A, 2026-06-08)**: MTDS `quality-gates.sh` hard-fails the file-size gate
> (`MAX_FILE_LINES=900`, no baseline) on **15 pre-existing** source files → the `.qg_last_passed_sha` sentinel can't go
> green. These files are **NOT introduced by the data-migration work** (the file-size loop EXCLUDES `./scripts/*`, so
> the migration scripts are clean) and splitting them — especially the 4,219-line `engine/orchestrator.py` the migration
> USES for Era-B classification — right before the `--apply` is a high-risk refactor for ZERO migration benefit. So it
> is **DEFERRED to AFTER the data migration** (the named successor for the MTDS-QG P2 deferral). Until then, MTDS
> migration code ships verified via **basedpyright-on-touched-files** (the established MTDS path), and the `--apply`
> runs from VM/tarball, not the quickmerge sentinel.
>
> **GATED: do NOT start until the per-AG data migrations (`--apply`) are complete.** Touching `orchestrator.py` /
> `tardis_adapter.py` / the handlers while the migration depends on them is the exact regression risk this defers.

## The 15 files (real-prod measured 2026-06-08; `wc -l`, `scripts/` excluded)

| File                                                         | Lines | Split approach (sketch)                                                                               |
| ------------------------------------------------------------ | ----- | ----------------------------------------------------------------------------------------------------- |
| `engine/orchestrator.py`                                     | 4219  | the worst — extract per-concern modules (pre-flight, classify, dispatch, manifest-emit); biggest care |
| `market_interface/adapters/tradfi/tardis_adapter.py`         | 2880  | split per data_type / per response-shape parser                                                       |
| `cli/handlers/solana_defi_handler.py`                        | 2134  | extract per-protocol handler helpers                                                                  |
| `adapters/umi_tick_provider.py`                              | 2057  | split provider vs parser vs cache                                                                     |
| `cli/handlers/evm_defi_handler.py`                           | 1440  | per-protocol helpers                                                                                  |
| `cli/handlers/lending_indices_handler.py`                    | 1373  | per-protocol                                                                                          |
| `cli/handlers/perp_funding_handler.py`                       | 1287  | per-venue                                                                                             |
| `market_interface/adapters/tradfi/databento_adapter.py`      | 1263  | per data_type parser                                                                                  |
| `cli/handlers/dex_pools_handler.py`                          | 1106  | per-venue / per-chain                                                                                 |
| `cli/handlers/oracle_prices_handler.py`                      | 1080  | Pyth vs Chainlink split                                                                               |
| `cli/handlers/dex_swaps_handler.py`                          | 988   | per-venue                                                                                             |
| `cli/handlers/solana_lst_archival.py`                        | 988   | per-LST                                                                                               |
| `cli/handlers/gas_fee_handler.py`                            | 971   | per-chain                                                                                             |
| `market_interface/adapters/prediction/polymarket_adapter.py` | 929   | CLOB vs Gamma split                                                                                   |
| `live/websocket_runner.py`                                   | 912   | per-transport / per-venue runner                                                                      |

## Approach (HARD — no behaviour change)

- **Pure mechanical extraction, behaviour-preserving** — move cohesive blocks into sibling modules + re-import; NO logic
  change, NO API change. The QG `engine/` ⊥ `adapters/` import rule + the singleton-adapter pattern must survive.
- **One file per commit**, each `quality-gates.sh --no-fix` exit 0 (the gate goes green incrementally as each file drops
  ≤900) + the existing unit suite green (no test deletion — `delete deprecated code`, no shims).
- Start with the LOW-risk handlers (per-venue/per-chain splits are clean); do `orchestrator.py` LAST + with the most
  care (it's the migration's classifier — only touch it once every AG's `--apply` is done).

## Phased execution

- [ ] [REFACTOR] P2. Split the 11 cli/handlers + adapters files (912–2,880L) — per-venue/per-chain/per-protocol
      extraction, one commit each, QG-green incrementally. Repo: market-tick-data-service.
- [ ] [REFACTOR] P2. Split `engine/orchestrator.py` (4,219L) LAST — extract pre-flight / classify / dispatch /
      manifest-emit modules; only after all per-AG `--apply` complete. Full unit suite + a migration smoke before/after.
- [ ] [VERIFY] P2. `quality-gates.sh --no-fix` exit 0 (file-size gate GREEN) → `.qg_last_passed_sha` writes → MTDS
      commit-quality-boundary restored (no more basedpyright-on-touched-only workaround).

## Success criterion

`find market_tick_data_service -name '*.py' ! -path '*/scripts/*' | xargs wc -l | awk '$1>900'` returns **0** rows; MTDS
`quality-gates.sh --no-fix` exits 0; the full unit suite green; zero behaviour change (the data pipeline produces
byte-identical output before/after).
