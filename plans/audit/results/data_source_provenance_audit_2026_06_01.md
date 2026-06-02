---
type: audit-result
epic:
  crosscutting (tradfi_master, cefi_master, defi_master, sports_master, predictions_master, mtds_mdps_master,
  manifest_master)
instructions_ref:
  plans/audit/instructions/{tradfi,cefi,sports,predictions,defi}_master_audit_instructions.md § "Dual-source
  provenance"; mtds_mdps_master item (j); manifest_master item (i)
auditor: slot-1 (ikenna, interactive)
date: 2026-06-01
status: complete
parent_plan: plans/active/data_source_provenance_all_asset_groups_2026_06_01.md
---

# Data-source provenance audit — all asset groups (2026-06-01)

## Scope + method

Audits the **data-source provenance** capability across all five asset groups: can a shard (`data_type × venue × time`)
carry more than one source over time via a row-level `source` column + per-source manifest row, resolved downstream by
UAC `SOURCE_PRIORITY`.

This is a **code write-path audit** — valid regardless of backfill state (per `manifest_master` § "Per-Service
capture*status Write-Path Calibration": a writer that never passes `source` \_necessarily* produces a blank column, so a
code RED is a data RED; the prod-row read only confirms it). Verified against current `live-defi-rollout` code:
`unified-api-contracts/.../canonical/crosscutting/source_priority.py`, `unified-trading-library/.../manifest_writer.py`,
`market-tick-data-service/.../cli/handlers/_defi_manifest.py`. Data-state reads (actual prod manifest `source`
distribution) are deferred to plan **Phase 7** — they confirm, they don't change, the verdicts below.

## Rule (corrected by operator 2026-06-01): provenance is UNIVERSAL

**Every captured cell stamps its `source` now — all asset groups, even single-source.** A source can be swapped or
supplemented later (e.g. a Tardis replacement); if stamping only begins when a 2nd source appears, the existing
single-source corpus is unlabelled and unresolvable after the swap. So a single-source cell with a blank `source` is
**RED**, not exempt. Cardinality (>1 source) governs only _resolution_ (which wins), not _whether_ to stamp.

The table below shows which cells are ALSO multi-source (they additionally need resolution) — but **all** cells need
`source` stamped.

## Multi-source cells declared in `SOURCE_PRIORITY` today (the subset that additionally needs resolution)

| asset_group    | multi-source cells (>1 source)                                                                                         | single-source (still must stamp source)       | evidence                   |
| -------------- | ---------------------------------------------------------------------------------------------------------------------- | --------------------------------------------- | -------------------------- |
| **tradfi**     | 6: `trades`/`tbbo`/`ohlcv_1m`/`ohlcv_15m`(+`yahoo`+`barchart`)/`options_chain`/`futures_chain` = `databento`+`massive` | —                                             | source_priority.py:250-259 |
| **defi**       | 2: `native_staking_rates`=`solana_rpc`+`helius_rpc`; `oracle_prices`=`pyth_hermes`+`chainlink`                         | ~20 others (`onchain_subgraph`/`onchain_rpc`) | source_priority.py:201,205 |
| **sports**     | 1: `FIXTURES`=`api_football`+`footystats` (footystats = deferred Phase 1B merge)                                       | ~25 others                                    | source_priority.py:116-119 |
| **cefi**       | **0**                                                                                                                  | all 9 = `["tardis"]`                          | source_priority.py:152-160 |
| **prediction** | **0**                                                                                                                  | all = single venue source                     | source_priority.py:269-278 |

## Per-asset-group verdicts

### tradfi — 🟡 AMBER (code GREEN; backfill now RUNNABLE)

- Gate enforced: `manifest_writer.py:2430` — `if category == "tradfi" and not source: raise MissingSourceError`. ✅
- 6 multi-source cells declared; writers pass `source` (dual-source plan Phase 3 shipped). ✅
- **Backfill UNBLOCKED** (correction 2026-06-01): `MASSIVE_API_KEY` was provided by the operator — Phase 5 is no longer
  blocked. Prod tradfi rows are still `source`-blank pending the run; the path is **MASSIVE S3 flat-files for bulk
  history** (flat-files are independent of the REST tier — the bulk backfill route; REST for incremental) + stamp
  `source=databento` on legacy rows. Run per `tradfi_massive_dual_source_2026_05_28.md` Phase 5.
- Covered by `tradfi_master` items (h)–(o).

### defi — 🔴 RED (the only LIVE silent-collapse; highest priority)

- 2 multi-source cells (`oracle_prices`, `native_staking_rates`) but the gate is **tradfi-only** → not enforced for
  defi.
- `DefiManifestRecorder.record_captured()` routes through `self._writer.add(...)` (`_defi_manifest.py:174`); the code's
  **own docstring (L144)** reads _"Until UTL `ManifestWriter.add()` is extended to persist [source]…"_ → **`source` is
  not persisted, defaults to `""`. CONFIRMED.**
- **Consequence (live today)**: Pyth vs Chainlink (`oracle_prices`) and solana_rpc vs helius_rpc
  (`native_staking_rates`) for the same cell **collapse last-write-wins**, divergence silently dropped — corrupts
  on-chain price/staking features.
- Under the universal rule, **all ~22 defi cells** must stamp source (e.g. `onchain_subgraph`), not just the 2
  multi-source ones — same `add()`-doesn't-persist root cause.
- Covered by `defi_master` items (n1)–(n4); remediated by plan **Phase 2 (P0)**.

### sports — 🔴 RED

- `FIXTURES` is multi-source `[api_football, footystats]`; gate not enforced.
- Source lives in the **GCS path** today (`data_source=ODDS_API/`, `pipeline_mode=batch_api_football/`), NOT a column —
  contradicts the operator-confirmed column model (path→column migration needed).
- Covered by `sports_master` items (h)–(j); remediated by plan **Phase 4 (P1)**.

### cefi — 🔴 RED (operator correction: stamp `source=tardis` NOW)

- Single source today (all `["tardis"]`) but `source` is **not stamped** (`""`). Under the universal rule this is RED:
  operator 2026-06-01 "I may find an alternative for Tardis, so it's the same issue." Stamp `source=tardis` on every
  cefi cell now so that when Tardis is replaced/supplemented, the existing corpus is already labelled and
  distinguishable.
- No `SOURCE_PRIORITY` change needed yet (`tardis` already declared) — just stamp it. Expand the list only when the
  alternative lands.
- Covered by `cefi_master` items (i)–(l) (reframe to "stamp now"); plan **Phase 3 (P1, restored from P2)**.

### prediction — 🔴 RED (stamp source now; venue ≠ source still holds)

- Single source per venue (`polymarket_clob` etc.) but `source` is **not stamped** (`""`) → RED for the same
  swap-resilience reason (a future Polymarket data-provider change). Stamp it now.
- **The venue ≠ source distinction is unchanged**: Polymarket/Kalshi remain separate **venues**; cross-venue dispersion
  stays a feature-layer concern; when Kalshi lands it is a venue addition. Stamping each venue-cell's own `source` is a
  _separate_ requirement that also applies here.
- Covered by `predictions_master` items (h)–(j) (reframe from "N/A" to "stamp source + keep venue≠source"); plan Phase 7
  prediction todo.

## The gate — universal (plan Phase 1)

The gate raises `MissingSourceError` when `source` is **blank OR not a member of
`SOURCE_PRIORITY[(asset_group, data_type)]`**, for **every** captured cell, all asset groups — NOT gated on cardinality.
`SOURCE_PRIORITY` validates the allowed source string (closed set) and drives resolution when >1; it does not decide
whether to stamp. So enforcement covers tradfi, defi, cefi (`tardis`), sports, prediction (`polymarket_clob`) alike. A
cell with no `SOURCE_PRIORITY` entry at all is a registry gap to fix, not a pass.

## Gap items — all canonical, already in the active plan

Every gap is a canonical `- [ ] [TYPE] P#.` todo in
[`plans/active/data_source_provenance_all_asset_groups_2026_06_01.md`](../../active/data_source_provenance_all_asset_groups_2026_06_01.md)
(`parent_epic: mtds_mdps_master`, `assigned_vm: vm-ml`). Priority refinement from this audit:

| Phase | work                                                                                                              | priority (post-audit) | why                                               |
| ----- | ----------------------------------------------------------------------------------------------------------------- | --------------------- | ------------------------------------------------- |
| 1     | UAC/UTL **universal** source gate (blank OR not-in-list → raise, all asset groups)                                | **P0**                | foundation; every cell stamps source              |
| 2     | DeFi writer rewiring (`add()` → `record_captured(source=)`, all defi cells)                                       | **P0**                | only LIVE multi-source collapse + universal stamp |
| 3     | CeFi stamp `source=tardis` NOW                                                                                    | **P1**                | swap-resilience — operator may replace Tardis     |
| 4     | Sports source path→column + stamp every cell                                                                      | P1                    | path-vs-column divergence                         |
| 5     | Downstream reconciliation wired (multi-source cells)                                                              | P0                    | correctness — no double-count                     |
| 6     | QG generalisation + codex + reword instruction gate descriptions                                                  | P1                    | enforce + document universal rule                 |
| 7     | Prod data-state verification (zero blank source, every cell) + TradFi backfill (MASSIVE flat-files, key provided) | P1                    | confirm + tradfi unblocked                        |
| 7p    | Prediction stamp `source` (venue≠source still holds)                                                              | P1                    | swap-resilience                                   |

## Active plan absorbing gaps

| gap set                          | active plan                                                          | status                            |
| -------------------------------- | -------------------------------------------------------------------- | --------------------------------- |
| all provenance gaps (Phases 1–7) | `plans/active/data_source_provenance_all_asset_groups_2026_06_01.md` | active — todos open, dispatchable |

## Archive condition

Archives when all Phase 1–7 todos in the parent plan are `- [x]`.
