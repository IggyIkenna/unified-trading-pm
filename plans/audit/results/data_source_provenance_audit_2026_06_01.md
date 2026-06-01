---
type: audit-result
epic: crosscutting (tradfi_master, cefi_master, defi_master, sports_master, predictions_master, mtds_mdps_master, manifest_master)
instructions_ref: plans/audit/instructions/{tradfi,cefi,sports,predictions,defi}_master_audit_instructions.md § "Dual-source provenance"; mtds_mdps_master item (j); manifest_master item (i)
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
capture_status Write-Path Calibration": a writer that never passes `source` *necessarily* produces a blank column, so a
code RED is a data RED; the prod-row read only confirms it). Verified against current `live-defi-rollout` code:
`unified-api-contracts/.../canonical/crosscutting/source_priority.py`,
`unified-trading-library/.../manifest_writer.py`,
`market-tick-data-service/.../cli/handlers/_defi_manifest.py`. Data-state reads (actual prod manifest `source`
distribution) are deferred to plan **Phase 7** — they confirm, they don't change, the verdicts below.

## The enforcement universe — multi-source cells declared in `SOURCE_PRIORITY` today

| asset_group | multi-source cells (>1 source) | single-source-only | evidence |
| ----------- | ------------------------------- | ------------------ | -------- |
| **tradfi**  | 6: `trades`/`tbbo`/`ohlcv_1m`/`ohlcv_15m`(+`yahoo`+`barchart`)/`options_chain`/`futures_chain` = `databento`+`massive` | — | source_priority.py:250-259 |
| **defi**    | 2: `native_staking_rates`=`solana_rpc`+`helius_rpc`; `oracle_prices`=`pyth_hermes`+`chainlink` | ~20 others (`onchain_subgraph`/`onchain_rpc`) | source_priority.py:201,205 |
| **sports**  | 1: `FIXTURES`=`api_football`+`footystats` (footystats = deferred Phase 1B merge) | ~25 others | source_priority.py:116-119 |
| **cefi**    | **0** | all 9 = `["tardis"]` | source_priority.py:152-160 |
| **prediction** | **0** | all = single venue source | source_priority.py:269-278 |

## Per-asset-group verdicts

### tradfi — 🟡 AMBER (code GREEN, data-state owed)

- Gate enforced: `manifest_writer.py:2430` — `if category == "tradfi" and not source: raise MissingSourceError`. ✅
- 6 multi-source cells declared; writers pass `source` (dual-source plan Phase 3 shipped). ✅
- **Data-state RED/PENDING**: Phase 5 backfill blocked on `MASSIVE_API_KEY` → prod tradfi rows are likely still
  `source`-blank despite the v9 column. Confirm via prod read (plan Phase 7).
- Covered by `tradfi_master` items (h)–(o).

### defi — 🔴 RED (the only LIVE silent-collapse; highest priority)

- 2 multi-source cells (`oracle_prices`, `native_staking_rates`) but the gate is **tradfi-only** → not enforced for defi.
- `DefiManifestRecorder.record_captured()` routes through `self._writer.add(...)` (`_defi_manifest.py:174`); the code's
  **own docstring (L144)** reads *"Until UTL `ManifestWriter.add()` is extended to persist [source]…"* → **`source` is
  not persisted, defaults to `""`. CONFIRMED.**
- **Consequence (live today)**: Pyth vs Chainlink (`oracle_prices`) and solana_rpc vs helius_rpc (`native_staking_rates`)
  for the same cell **collapse last-write-wins**, divergence silently dropped — corrupts on-chain price/staking features.
- Covered by `defi_master` items (n1)–(n4); remediated by plan **Phase 2 (P0)**.

### sports — 🔴 RED

- `FIXTURES` is multi-source `[api_football, footystats]`; gate not enforced.
- Source lives in the **GCS path** today (`data_source=ODDS_API/`, `pipeline_mode=batch_api_football/`), NOT a column —
  contradicts the operator-confirmed column model (path→column migration needed).
- Covered by `sports_master` items (h)–(j); remediated by plan **Phase 4 (P1)**.

### cefi — 🟢 GREEN today / LATENT (downgraded from the earlier "RED" framing)

- **ZERO multi-source cells declared** (all `["tardis"]`). The registry-driven gate correctly requires nothing today →
  **no current violation**.
- Latent: when a live per-venue source is added alongside the Tardis archive for the same `(data_type, venue)`,
  `SOURCE_PRIORITY` must be expanded **and** `source` stamped *first*. Until a 2nd source actually lands, cefi has no gap.
- Covered by `cefi_master` items (i)–(l), reframed as **preparatory**; plan **Phase 3 (P2, downgraded from P1)**.

### prediction — 🟢 GREEN / N/A by design

- Single source per venue; Polymarket/Kalshi are **venues**, not sources; dispersion is cross-venue at the feature layer.
- No action. `predictions_master` items (h)–(j) are invariant-confirmation only (regression guard).

## Registry-driven gate — immediate enforcement scope (plan Phase 1)

Generalising the gate to *"raise `MissingSourceError` when `SOURCE_PRIORITY[(asset_group, data_type)]` has >1 entry and
`source` is blank"* **today** catches: tradfi (6, already gated), **defi (`oracle_prices` + `native_staking_rates`)**,
sports (`FIXTURES`). Auto-exempts cefi (0 multi) + prediction (0 multi) until their registries grow. This is the correct
immediate scope — no hardcoded asset_group list.

## Gap items — all canonical, already in the active plan

Every gap is a canonical `- [ ] [TYPE] P#.` todo in
[`plans/active/data_source_provenance_all_asset_groups_2026_06_01.md`](../../active/data_source_provenance_all_asset_groups_2026_06_01.md)
(`parent_epic: mtds_mdps_master`, `assigned_vm: vm-ml`). Priority refinement from this audit:

| Phase | work | priority (post-audit) | why |
| ----- | ---- | --------------------- | --- |
| 1 | UAC/UTL registry-driven source gate | **P0** | foundation; catches defi+sports+tradfi today |
| 2 | DeFi writer rewiring (`add()` → `record_captured(source=)`) | **P0** | the only LIVE silent-collapse (oracle/staking) |
| 4 | Sports source path→column + FIXTURES merge | P1 | path-vs-column divergence |
| 3 | CeFi `SOURCE_PRIORITY` expansion + source stamping | **P2 (was P1)** | latent — only when a 2nd cefi source lands |
| 5 | Downstream reconciliation wired (all multi-source ag) | P0 | correctness — no double-count |
| 6 | QG generalisation + codex | P1 | enforce + document |
| 7 | Prod data-state verification | P1 | confirm code findings in prod rows |
| — | prediction | none | N/A by design |

## Active plan absorbing gaps

| gap set | active plan | status |
| ------- | ----------- | ------ |
| all provenance gaps (Phases 1–7) | `plans/active/data_source_provenance_all_asset_groups_2026_06_01.md` | active — todos open, dispatchable |

## Archive condition

Archives when all Phase 1–7 todos in the parent plan are `- [x]`.
