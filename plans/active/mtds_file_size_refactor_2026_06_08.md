---
doc_type: plan
title: MTDS/MDPS tech-debt & coverage — file-size splits + polars seam + coverage/QG residuals (survivor M-2)
summary:
  MTDS/MDPS tech-debt plan — split 15 pre-existing >900-line source files, apply pandas-to-polars adapter seam, and
  clear QG residuals after per-AG data migrations complete. Resumed 2026-07-27 (operator directive, interactive
  operator-gate session).
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    instruments-service,
    market-data-processing-service,
    market-tick-data-service,
    unified-api-contracts,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags: [tech-debt, refactor, file-size, mtds, mdps, polars, quality-gates, deferred]
related: []
created: 2026-06-08
parent_epic: mtds_mdps_master
assigned_vm: NA
execution_scope: local-only # was: orchestrator-agent — corrected 2026-08-19 (plan_reconciler, cross-cutting) — only valid NA-paired value
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 2
last_updated: 2026-07-12
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source:
  [
    "master_data_canonicalisation_migration_catalogue_2026_06_07.md (MTDS-QG P2 — Option A, operator 2026-06-08)",
    "market-tick-data-service quality-gates.sh file-size gate (MAX_FILE_LINES=900, hard-fail, no baseline)",
  ]
drift_direction: advance-code
context_scope:
  [
    /plans/epics/mtds_mdps_master.md,
    /codex/06-coding-standards/quality-gates.md,
    market-tick-data-service/market_tick_data_service/cli/handlers,
    market-data-processing-service/market_data_processing_service/app/adapters,
    /plans/active/mdps_adapter_protocol_polars_migration_2026_08_22.md,
  ]
---

# MTDS file-size refactor — split the 15 pre-existing >900-line source files

> **🟢 RESUMED 2026-07-27 (operator, interactive operator-gate session)** — was ⏸️ DEFERRED 2026-06-26, non-essential,
> parked. This is pure tech-debt (file-size splits + the pandas→polars adapter seam + coverage/QG residuals) and is
> already self-gated behind the per-AG data migration (now complete for all 5 AGs). **NOTE the live blocker is elsewhere
> (was: "stays a live blocker" — corrected 2026-07-12, finding 186, §A2 B-queue ruling):** the issue
> `issues/fleet_mtds_qg_red_hardcoded_url_record_empty_ratchet_2026_06_22.md` (which blocked ALL MTDS ships) was a
> SEPARATE doc and was NOT deferred by this — but that blocker is now RESOLVED (2026-06-30, QG green + Cloud Build
> SUCCESS, archived at `../archive/issues/fleet_mtds_qg_red_hardcoded_url_record_empty_ratchet_2026_06_22.md`),
> confirmed by a subsequent green-QG MTDS ship landing 2026-07-06 (`market-tick-data-service@f4dab8f9`, full
> `quality-gates.sh` exit 0). No live MTDS-ship blocker remains from that issue as of this correction.

> **🟢 ENGINE-INTERNAL POLARS LAZY CHAIN SHIPPED 2026-06-29** — the engine portion of the parked "pandas→polars adapter
> seam" (the Polars→Pandas→Polars internal aggregation chain in `_aggregate_from_15s_polars`) has been un-deferred and
> shipped via [`mdps_polars_engine_cost_sharpening_2026_06_28.md`](./mdps_polars_engine_cost_sharpening_2026_06_28.md):
> pure-Polars lazy (`scan_parquet` + projection pushdown), subprocess-per-date default, manifest column-prune,
> canonical-ID CLI matcher (full-month Binance benchmark landed 10.35× wall / 6.11× peak RSS / 8.88× retention vs the
> audited 3× / 5× / 7.8× targets). The **adapter-protocol** portion of the seam — the 18 MDPS adapters'
> `process_to_candles(df, …)` signature still taking pandas, P3 line below — stays parked here.

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

- [x] [REFACTOR] P2. ✅ Split the 11 cli/handlers + adapters files (912–2,880L) — per-venue/per-chain/per-protocol
      extraction, one commit each, QG-green incrementally. Repo: market-tick-data-service. —
      market-tick-data-service@6f753c5cb: all 14 listed cli/handlers+adapters files confirmed ≤900 lines (`wc -l`).
- [x] [REFACTOR] P2. ✅ Split **MTDS** `engine/orchestrator.py` (4,219L, `market-tick-data-service`) LAST — extract
      pre-flight / classify / dispatch / manifest-emit modules; only after all per-AG `--apply` complete. Full unit
      suite + a migration smoke before/after. **NB: distinct from the `instruments-service` `engine/orchestrator.py`
      (8,192L) split tracked in I-2 — same filename, different repo; do not conflate.** —
      market-tick-data-service@6f753c5cb: monolithic engine/orchestrator.py (4230 lines) removed, replaced with
      engine/orchestrator/{**init**,_state,manifest_finalize,partitioned_writer,preflight,...}.
- [x] ✅ [VERIFY] P2. `quality-gates.sh --no-fix` exit 0 (file-size gate GREEN) → `.qg_last_passed_sha` writes → MTDS
      commit-quality-boundary restored (no more basedpyright-on-touched-only workaround). — CLOSED na-eligibility-audit
      2026-08-08: stale, already satisfied. Evidence: this doc's own top banner cites market-tick-data-service@f4dab8f9
      (2026-07-06, full `quality-gates.sh` exit 0); independently confirmed via `scripts/quality-gates.sh`'s dated
      2026-06-11 Wave-3 comment + commit `33a14c1f` (same date, "Wave-3 size-debt burn-down... all >900L files split...
      coverage floor pinned 79.7"); live-verified today that `databento_adapter.py` (352L) and `polymarket_adapter.py`
      (899L), both cited in this plan as >900L violations, are now under the 900-line cap.

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
- [x] ✅ [TEST] P3. **Re-add 17 connector reconnect tests** that were deleted (mock-flawed: never-closing mocked websockets
      spun the reconnect loop) using terminating mocks (the `ws.closed` flip pattern in
      `test_deribit_book_ticker_ws_coverage.py`). Repo: market-tick-data-service. (MIGRATED FROM: same.)
- [x] ✅ [CODE] P3. **UAC generated-artifact churn** — UAC QG regenerates `openapi/ui-reference-data.json` in a new format
      (18k-line churn) + emits untracked `openapi/capability-manifest.json` + `capability-orphan-report.txt`; per the
      generated-artifacts HARD RULE, gitignore + `git rm --cached` (or re-commit the tracked copy from the current
      generator). Repo: unified-api-contracts. (MIGRATED FROM: same.)

### From `mdps_adapter_protocol_pandas_to_polars_2026_06_21` (archived — not started; operator-directed LATER migration)

- [ ] [REFACTOR] P3. **All 18 MDPS adapters' `process_to_candles(df, …)` → Polars** — the compute engine is pure-Polars
      (engine-internal lazy chain shipped 2026-06-29 via
      [`mdps_polars_engine_cost_sharpening_2026_06_28.md`](./mdps_polars_engine_cost_sharpening_2026_06_28.md)) but the
      ~18 source adapters still emit/accept pandas at the seam, forcing a per-shard conversion; thread the polars frame
      through the adapter protocol to drop it. Repo: market-data-processing-service. (MIGRATED FROM:
      `mdps_adapter_protocol_pandas_to_polars_2026_06_21`.) **2026-08-15 scope survey (slot-31·infra, batch13 todo
      pickup) confirms this stays P3/parked, NOT a bounded single-task item**: atomic one-PR migration across all 18
      adapters (the ABC boundary can't be half-converted) with 5 files (cefi/trades_adapter.py,
      cefi/book_snapshot_adapter.py, cefi/liquidations_adapter.py, sports/bucket_assignment_adapter.py,
      tradfi/ohlcv_passthrough.py) needing genuine groupby-based feature-engineering rewrites, not type-hint swaps —
      full file-by-file survey in the (now-archived) `issues/mdps_adapter_protocol_polars_seam_mis_scoped_ao_dispatch_
      2026_08_15.md`; its `[DESIGN]` scoping todo is now satisfied by
      `/plans/active/mdps_adapter_protocol_polars_migration_2026_08_22.md` (human-driven, `status: draft` pending
      execution — the dedicated design/execution effort itself is NOT yet done, only its scope).
- [x] ✅ [DESIGN] P3. **Phase-6 `_publish_emission_check` scalability — RESOLVED, already shipped
      (round5-cross-cutting-audit 2026-08-08).** Both options already live+composed: in-process 60s-TTL cache
      (`read_availability_index`) + optional `manifest_index` pre-read passthrough (MDPS commit `ca69f512`, "F3 safe
      pass-through"). Closed 2026-07-29,
      `plans/archive/issues/manifest_completeness_full_corpus_map_build_2026_07_20.md`. No operator pick needed. The
      per-shard emission-policy check materialises the availability index per call. Surface the option set (in-process
      TTL cache vs batched pre-flight vs incremental index), get the operator pick, then implement. Repo:
      market-data-processing-service. (MIGRATED FROM: same.)

### From `mdps_coverage_85pct_2026_06_10` (archived — 9/10 done; MDPS coverage→86.71% SHIPPED)

- [x] ✅ [QG] P2. **Run PM `bash scripts/quality-gates.sh`** to confirm the plan + codex update pass
      (`unified-trading-pm`). (MIGRATED FROM: `mdps_coverage_85pct_2026_06_10`.)

### Live issue docs this survivor tracks (referenced, NOT folded — they are active blockers with their own lifecycle)

- `issues/fleet_mtds_qg_red_hardcoded_url_record_empty_ratchet_2026_06_22.md` — pre-existing hardcoded-URL +
  `record_empty`-string debt elevated to ERROR by the qg-base ratchet; **RESOLVED 2026-06-30 (was: "blocks ALL MTDS
  LDR→staging ships" — corrected 2026-07-12, finding 186, §A2 B-queue ruling)** — QG green + Cloud Build SUCCESS, now
  archived (`../archive/issues/fleet_mtds_qg_red_hardcoded_url_record_empty_ratchet_2026_06_22.md`); no longer gates the
  file-size/coverage work here.
- `issues/mtds_cefi_mvp_gate_and_thegraph_shard_test_fleet_red_2026_06_23.md` — cefi MVP-gate + thegraph 9-key shard
  test reds on LDR (mostly resolved; 1 residual aster perp-funding red on the cefi owner's track).

## Progress Log

- **2026-07-13** — Per the MTDS/MDPS 2-survivor consolidation (`mtds_consolidation_foldin_mapping_2026_07_12.md`,
  operator ruling 2026-07-13: "Approve all + unlock"), `mdps_polars_engine_cost_sharpening_2026_06_28.md`
  (`status: complete`, 0 open todos, all 6 items shipped) is archived to `plans/archive/2026_07/` and its completion
  CREDIT is folded into this M-2 Progress Log rather than migrating any open work (there was none). That plan
  un-deferred the Polars portion of this survivor's parked seam (see the "🟢 ENGINE-INTERNAL POLARS LAZY CHAIN SHIPPED
  2026-06-29" banner above): pure-Polars lazy candle aggregation, subprocess-per-date default, manifest double-read fix,
  canonical-ID CLI matcher — measured 10.35× wall / 6.11× peak RSS / 8.88× retention on a full-month Binance benchmark
  (all above the audited 3×/5×/7.8× targets). Shas: market-data-processing-service@c7e0437/85060ff/eee8433/2dd13db,
  unified-trading-pm@68bf2c85c/be1f7633c. The remaining M-2 scope (file-size splits, adapter-protocol pandas→polars,
  coverage/QG residuals) stays parked/⏸️ DEFERRED — unaffected by this fold.
- **context-scout 2026-08-01**: populated/refreshed context_scope (1 entries).
- **context-scout 2026-08-03**: refreshed context_scope (4 entries) -- was codex-epic-only; added the QG file-size
  codex + the two live source dirs the remaining open todos (fn/method splits, MDPS polars adapter seam) target.
- **2026-08-15 (slot-31·infra)**: picked up as `cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md`'s "All 18
  MDPS adapters → Polars" todo. Ran a concrete file-by-file scope survey before touching code (18 adapter files, their 4
  production callers, `base_adapter.py`'s shared pandas helpers) and confirmed batch13's "bounded/deterministic"
  classification does not hold: this is an atomic single-PR migration across all 18 adapters (the shared ABC can't be
  half-converted) with 5 files needing genuine groupby-based feature-engineering rewrites on live candle-production
  code, matching the same scope already operator-deferred twice under two archived predecessor plans (prior combined
  estimate 2.0 calibrated AI-days). Did not attempt the migration; this item stays P3/parked here pending a dedicated
  design/execution effort. Full survey + recommendation (now archived):
  `issues/mdps_adapter_protocol_polars_seam_mis_scoped_ao_dispatch_2026_08_15.md`.
- **2026-08-22 (T2)**: that issue doc's `[DESIGN]` scoping todo is now satisfied —
  `/plans/active/mdps_adapter_protocol_polars_migration_2026_08_22.md` authored (human-driven per operator ruling,
  `status: draft`), enumerating the exact 18+1+4 file surface, a dual-path sequencing so the 13 light adapters ship
  independently of the 5 heavy ones, and the numeric-parity verification bar. The MIGRATION ITSELF remains
  unexecuted — this closes only the scoping half. Source issue doc archived to
  `plans/archive/issues/mdps_adapter_protocol_polars_seam_mis_scoped_ao_dispatch_2026_08_15.md`.

- **na-eligibility-audit 2026-08-17** [body-hash:ed2216fabc187778]: KEEP-NA, stale-items corrected -- closed 3 of 5 open items (connector-reconnect-tests, UAC generated-artifact-churn, PM quality-gates.sh confirm): all already shipped, each citing this exact doc as Source, inside the active cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md (parent_epic infrastructure_master) -- market-tick-data-service@26eef1999f (2026-08-15), unified-api-contracts@f70f29c8 (2026-08-15), and PM's own quality-gates.sh confirmed green (sentinel .qg_last_passed_sha == HEAD 8b7e53a624). Doc stays assigned_vm: NA for its 2 remaining genuine items (MTDS file-split programme, Polars adapter migration -- both large, non-bounded). Cross-cutting tranche audit conflict-check finding.
## Deferred work — migrated to:

**Not yet identified** — this whole plan (`status: active` as of 2026-07-27, was `paused`/tagged `deferred`) IS the
designated survivor/receptacle for the MTDS/MDPS file-size-splits + pandas→polars adapter-seam + coverage/QG-residual
scope (was parked per the top-of-doc "⏸️ DEFERRED 2026-06-26 (operator) — non-essential, parked" banner — **operator
directive 2026-07-27: resume**). There is no external successor to point to because the work was never migrated
elsewhere — it stays captured here so nothing is lost. This plan itself remains the owner.

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — `locked_by: live-defi-rollout`; contains a [DESIGN] P3 that
  explicitly requires an operator option-pick (Phase-6 `_publish_emission_check` scalability) before implementation.
- **na-eligibility-audit 2026-08-08 (cross-cutting tranche)**: KEEP-NA, stale items — reaffirms 2026-07-30's standing
  ruling (item 6, [DESIGN] P3 operator option-pick, dispositive on its own). Additionally closed item 1 ([VERIFY] P2 QG
  exit 0) as stale/already-satisfied, evidence-backed (see its own checkbox note). Remaining 6 open items are genuine
  work; item 2's "75 violations / 8 files" framing is now materially smaller than described
  (`scripts/quality-gates.sh`'s `FUNCTION_SIZE_EXTRA_EXCLUDES` is down to 10 entries per live check) — flagged for a
  future non-read-only pass to refresh the description, not acted on here (read-only classification scope).
- **context-scout 2026-08-09**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-17**: re-scouted; context_scope re-verified (4 entries), unchanged.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
