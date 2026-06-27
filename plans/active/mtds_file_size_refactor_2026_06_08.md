---
doc_type: plan
title: MTDS/MDPS tech-debt & coverage — file-size splits + polars seam + coverage/QG residuals (survivor M-2)
summary:
status: deferred
nature: process
stage: [meta]
repos: [instruments-service, market-data-processing-service, market-tick-data-service, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: 2026-06-08
parent_epic: mtds_mdps_master
assigned_vm: vm-cross-cutting
execution_scope:
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 2
last_updated: 2026-06-26
locked_by: live-defi-rollout
locked_since: 2026-06-08
supersedes:
superseded_by:
depends_on:
source: ['master_data_canonicalisation_migration_catalogue_2026_06_07.md (MTDS-QG P2 — Option A, operator 2026-06-08)', 'market-tick-data-service quality-gates.sh file-size gate (MAX_FILE_LINES=900, hard-fail, no baseline)']
---

# MTDS file-size refactor — split the 15 pre-existing >900-line source files

> **⏸️ DEFERRED 2026-06-26 (operator) — non-essential, parked.** This is pure tech-debt (file-size splits + the
> pandas→polars adapter seam + coverage/QG residuals) and is already self-gated behind the per-AG data migration. The
> operator deprioritised it — it does NOT block instruments/MTDS data correctness or the backfill-to-100% path. The
> folded residuals stay captured here so nothing is lost; pick it up when the MTDS commit-quality-boundary
> (`.qg_last_passed_sha`) actually needs restoring. **NOTE the live blocker is elsewhere:** the issue
> `issues/fleet_mtds_qg_red_hardcoded_url_record_empty_ratchet_2026_06_22.md` (which blocks ALL MTDS ships) is a
> SEPARATE doc and is NOT deferred by this — it stays a live blocker.

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
- [ ] [REFACTOR] P2. Split **MTDS** `engine/orchestrator.py` (4,219L, `market-tick-data-service`) LAST — extract
      pre-flight / classify / dispatch / manifest-emit modules; only after all per-AG `--apply` complete. Full unit
      suite + a migration smoke before/after. **NB: distinct from the `instruments-service` `engine/orchestrator.py`
      (8,192L) split tracked in I-2 — same filename, different repo; do not conflate.**
- [ ] [VERIFY] P2. `quality-gates.sh --no-fix` exit 0 (file-size gate GREEN) → `.qg_last_passed_sha` writes → MTDS
      commit-quality-boundary restored (no more basedpyright-on-touched-only workaround).

## Success criterion

`find market_tick_data_service -name '*.py' ! -path '*/scripts/*' | xargs wc -l | awk '$1>900'` returns **0** rows; MTDS
`quality-gates.sh --no-fix` exits 0; the full unit suite green; zero behaviour change (the data pipeline produces
byte-identical output before/after).

## Folded-in (M-2 consolidation 2026-06-26)

> This plan is the **M-2 survivor** of the instruments/MTDS consolidation
> (`instruments_mtds_plan_consolidation_2026_06_26.md`) — broadened from "file-size refactor" to the MTDS/MDPS tech-debt
> & coverage bucket. Open todos migrated here from 3 archived plans; full detail lives in the archived sources under
> `archive/2026_06/`.

### From `mtds_coverage_75_and_codex_zero_2026_06_11` (archived — 5/8 done; coverage→82% + codex→0 SHIPPED)

- [ ] [REFACTOR] P1. **Split the remaining MTDS >900L files + extract oversized fns/methods** — the 8 >900L excluded
      files + 2 `market_interface` >900 (databento_adapter 1,361, polymarket_adapter 1,022); extract 6 fns >200L + ~150
      methods >50L (75 violations); delete ALL exclude entries; REUSE UTL for cross-cutting pure calcs (search UTL
      first, flag promotion candidates). **Overlaps the file-size table above — execute as one programme.** Repo:
      market-tick-data-service. (MIGRATED FROM: `mtds_coverage_75_and_codex_zero_2026_06_11`.)
- [ ] [TEST] P3. **Re-add 17 connector reconnect tests** that were deleted (mock-flawed: never-closing mocked websockets
      spun the reconnect loop) using terminating mocks (the `ws.closed` flip pattern in
      `test_deribit_book_ticker_ws_coverage.py`). Repo: market-tick-data-service. (MIGRATED FROM: same.)
- [ ] [CODE] P3. **UAC generated-artifact churn** — UAC QG regenerates `openapi/ui-reference-data.json` in a new format
      (18k-line churn) + emits untracked `openapi/capability-manifest.json` + `capability-orphan-report.txt`; per the
      generated-artifacts HARD RULE, gitignore + `git rm --cached` (or re-commit the tracked copy from the current
      generator). Repo: unified-api-contracts. (MIGRATED FROM: same.)

### From `mdps_adapter_protocol_pandas_to_polars_2026_06_21` (archived — not started; operator-directed LATER migration)

- [ ] [REFACTOR] P3. **All 18 MDPS adapters' `process_to_candles(df, …)` → Polars** — the compute engine is pure-Polars
      but the ~18 source adapters still emit/accept pandas at the seam, forcing a per-shard conversion; thread the
      polars frame through the adapter protocol to drop it. Repo: market-data-processing-service. (MIGRATED FROM:
      `mdps_adapter_protocol_pandas_to_polars_2026_06_21`.)
- [ ] [DESIGN] P3. **Phase-6 `_publish_emission_check` scalability — operator option-pick** — the per-shard
      emission-policy check materialises the availability index per call. Surface the option set (in-process TTL cache
      vs batched pre-flight vs incremental index), get the operator pick, then implement. Repo:
      market-data-processing-service. (MIGRATED FROM: same.)

### From `mdps_coverage_85pct_2026_06_10` (archived — 9/10 done; MDPS coverage→86.71% SHIPPED)

- [ ] [QG] P2. **Run PM `bash scripts/quality-gates.sh`** to confirm the plan + codex update pass
      (`unified-trading-pm`). (MIGRATED FROM: `mdps_coverage_85pct_2026_06_10`.)

### Live issue docs this survivor tracks (referenced, NOT folded — they are active blockers with their own lifecycle)

- `issues/fleet_mtds_qg_red_hardcoded_url_record_empty_ratchet_2026_06_22.md` — pre-existing hardcoded-URL +
  `record_empty`-string debt elevated to ERROR by the qg-base ratchet; **blocks ALL MTDS LDR→staging ships** until
  baselined or remediated. The file-size/coverage work here lands behind this gate.
- `issues/mtds_cefi_mvp_gate_and_thegraph_shard_test_fleet_red_2026_06_23.md` — cefi MVP-gate + thegraph 9-key shard
  test reds on LDR (mostly resolved; 1 residual aster perp-funding red on the cefi owner's track).
