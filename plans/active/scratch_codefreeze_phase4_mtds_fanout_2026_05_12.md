---
title: Phase 4.MTDS + writegate-slice-(c) callsite-migration fan-out plan (Harsh slot 3, 2026-05-12)
type: scratch
status: prep — execution gated on Ikenna slot 3 UAC PipelineMode enum + MTDS sweep landing on live-defi-rollout
created: 2026-05-12
companion_to: plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md (freeze-gate item 3, line ~153) + plans/active/writegate_honest_coverage_endtoend_2026_05_06.md (slice (c) Phase 6) + plans/active/manifest_schema_final_gate_2026_05_09.md (Phase 4)
locked_by: live-defi-rollout
locked_since: 2026-05-12
---

# Phase 4.MTDS + writegate slice (c) callsite-migration — fan-out prep (Harsh slot 3)

> **🟡 GATED — DO NOT EXECUTE YET.** Spawn the fan-out only after **both** land on `live-defi-rollout`:
> (1) UAC `PipelineMode` enum + `SOURCE_PRIORITY` extension with 6 `BATCH_*` values
>     (`BATCH_YAHOO` / `BATCH_BARCHART` / `BATCH_FOOTYSTATS` / `BATCH_HYPERLIQUID_REST` / `BATCH_PYTH_HERMES` / `BATCH_CHAINLINK`);
> (2) Ikenna slot 3's Phase 4.MTDS `pipeline_mode=` arg-insertion sweep on `market-tick-data-service`.
> Slot 1 main has the LDR poll-watch and will post `[main → slot 3] — cleared @<sha>` in `harsh_orchestrator/pings/slot_3.md`.
> File overlap: MTDS handlers + `engine/orchestrator.py` + `live/*.py` — **pull-FF then layer** per CLAUDE.md
> "Two teammates × multiple parallel agents" + "Cross-Plan Coordination Banners" HARD RULES.

## Inventory (source: `unified-trading-pm/scripts/quality_gates/pipeline_mode_explicit_baseline.yaml`, slot-8 bootstrap 2026-05-12)

114 baselined `record_*` callsites without explicit `pipeline_mode=`:

| Repo | Count | Owner | Status |
|---|---|---|---|
| `market-tick-data-service` | 97 | **Harsh slot 3 (this plan)** — but Ikenna slot 3's Phase 4.MTDS `pipeline_mode=` sweep lands first; see "Ownership boundary" below | gated |
| `features-service` | 6 | **NOT mine** — Phase 4.FEATURES, gated on features-consolidation merge ~2026-05-16 (calendar_orchestrator.py ×2 + sports/cli/handlers/batch_handler.py ×4) | not mine |
| `unified-trading-library` | 11 | **NOT mine (yet)** — Phase 4.DEFAULT-REMOVAL successor (UTL test/internal callsites) | not mine |

Already shipped (NOT in scope, for reference): Phase 4.MDPS @MDPS@`a3c7198` (22 callsites; `resolve_pipeline_mode_from_source` helper) · Phase 4.INSTRUMENTS @instruments-service@`e530906` (~50 callsites; `_SPORTS_DATA_TYPE_TO_PIPELINE_MODE` SSOT) · Phase 4.GREP-VERIFY @PM@`4159b7ae` (`check_pipeline_mode_explicit_at_record_calls.py` + STEP 5.70).

## MTDS 97-callsite breakdown (file → count → methods → lines)

DeFi CLI handlers (`market_tick_data_service/cli/handlers/`):

| # | File | record_* | lines |
|---|---|---|---|
| 3 | `_defi_manifest.py` | empty×2, failed×1 | 152, 214, 290 |
| 3 | `bridge_events_handler.py` | captured×1, empty×1, failed×1 | 142, 151, 160 |
| 3 | `dex_pools_handler.py` | captured×1, empty×1, failed×1 | 374, 383, 398 |
| 3 | `dex_swaps_handler.py` | captured×1, empty×1, failed×1 | 377, 386, 396 |
| 3 | `eigenlayer_rewards_handler.py` | captured×1, empty×1, failed×1 | 181, 190, 200 |
| 3 | `evm_defi_handler.py` | captured×1, empty×1, failed×1 | 390, 399, 409 |
| 3 | `flash_loan_events_handler.py` | captured×1, empty×1, failed×1 | 141, 150, 159 |
| 9 | `gas_fee_handler.py` | captured×3, empty×3, failed×3 | 219, 227, 236, 252, 260, 269, 285, 293, 302 |
| 3 | `governance_events_handler.py` | captured×1, empty×1, failed×1 | 124, 133, 142 |
| 4 | `lending_indices_handler.py` | captured×1, empty×2, failed×1 | 324, 350, 359, 369 |
| 3 | `liquidation_events_handler.py` | captured×1, empty×1, failed×1 | 153, 162, 171 |
| 3 | `liquidations_handler.py` | captured×1, empty×1, failed×1 | 297, 306, 316 |
| 5 | `lst_rates_handler.py` | captured×1, empty×2, failed×2 | 408, 417, 425, 433, 480 |
| 3 | `mev_events_handler.py` | captured×1, empty×1, failed×1 | 124, 133, 142 |
| 6 | `oracle_prices_handler.py` | captured×2, empty×2, failed×2 | 642, 650, 659, 669, 677, 686 |
| 3 | `perp_funding_handler.py` | captured×1, empty×1, failed×1 | 245, 254, 263 |
| 6 | `position_data_handler.py` | captured×2, empty×2, failed×2 | 124, 133, 142, 171, 180, 189 |
| 3 | `solana_defi_handler.py` | captured×1, empty×1, failed×1 | 225, 233, 244 |
| 9 | `staking_yields_handler.py` | captured×3, empty×3, failed×3 | 115, 124, 133, 160, 169, 178, 205, 214, 223 |
| 3 | `token_transfers_handler.py` | captured×1, empty×1, failed×1 | 187, 196, 205 |
| 5 | `vault_share_price_handler.py` | captured×1, empty×2, failed×2 | 287, 295, 481, 497, 505 |

Engine + live:

| # | File | record_* | lines |
|---|---|---|---|
| 8 | `engine/orchestrator.py` | failed×5, empty×3 | 2482, 2596, 2762, 2769, 2901, 2910, 2949, 2954 |
| 1 | `live/manifest_recorder.py` | empty×1 | 182 |
| 2 | `live/websocket_runner.py` | captured×1, empty×1 | 647, 665 |

## Ownership boundary — Ikenna slot 3 vs Harsh slot 3 (OPEN — confirm with slot 1 / Ikenna slot 3 when dep lands)

Per Harsh-slot-3 CONTINUE prompt coordination note #2:
- **Ikenna slot 3** owns the explicit `pipeline_mode=PipelineMode.BATCH_<source>` kwarg insertion at each MTDS `record_*` callsite (their Phase 4.MTDS mechanical sweep — clears the GREP-VERIFY baseline).
- **Harsh slot 3 (me)** owns the **manifest v8 wire-in** = every `record_captured(...)` callsite additionally passes the 3 v8 columns:
  `service_emission_state` (UAC `ServiceEmissionStateEnum` via UTL `next_state(...)`), `last_emission_decision_at` (ISO-8601 ms UTC),
  `expected_window_completeness_fraction` (float 0..1) — per `manifest_schema_final_gate_2026_05_09.md` Phase 4 line 257-285 + UTL@`0adea1c6`.
  Plus the writegate slice (c) emission-policy gate (`publish_with_policy` / `publish_with_manifest_lookup`) **only where MTDS emits a derived/policy output** — Phase 6.1 says MTDS raw capture is "n/a per policy table — `record_captured` covers it", so the slice (c) publish-gate scope on MTDS is narrow (verify against `SERVICE_OUTPUT_POLICIES` for any MTDS rows); the bulk of my MTDS work is the v8-column threading on `record_captured`.

**Resolution needed before fan-out spawn**: (a) does Ikenna slot 3's sweep land first and I layer the v8 columns on top of their commits (assume yes per coordination note), or (b) is the MTDS `pipeline_mode=` + v8-column work a single combined sweep one of us does (and the other reviews)? If (a): my fan-out below targets the same 97 callsites but adds ONLY the v8 kwargs (`service_emission_state` etc.) on `record_captured` + leaves `pipeline_mode=` to their commit. If the dep lands as a combined sweep already including v8 columns, my scope collapses to a verification pass + the slice (c) `publish_with_policy` audit.

## Per-source `pipeline_mode=` value mapping (MTDS DeFi handlers)

Exact values pending the extended UAC `SOURCE_PRIORITY`; structure (per `manifest_schema_final_gate` Phase 4.INSTRUMENTS table + the 3 finding docs):

| MTDS handler / source | `PipelineMode` value |
|---|---|
| on-chain subgraph (Messari / The Graph) — lending_indices, dex_swaps, dex_pools, evm_defi, staking_yields, vault_share_price, lst_rates, eigenlayer_rewards, governance_events, etc. | `BATCH_ONCHAIN_SUBGRAPH` |
| on-chain RPC (direct node) — token_transfers, bridge_events, flash_loan_events, liquidation_events, mev_events, gas_fee (eth_gasPrice), position_data | `BATCH_ONCHAIN_RPC` |
| Hyperliquid REST — perp_funding (HL leg), solana_defi where HL-sourced | `BATCH_HYPERLIQUID_REST` (NEW — pending enum) |
| Pyth Hermes — oracle_prices (Solana feeds) | `BATCH_PYTH_HERMES` (NEW — pending enum) |
| Chainlink — oracle_prices (EVM feeds) | `BATCH_CHAINLINK` (NEW — pending enum) |
| Yahoo — (MTDS VIX 15m fallback; mostly MDPS-side, but check `umi_tick_provider`) | `BATCH_YAHOO` (NEW — pending enum) |
| Barchart — VIX 15m preload | `BATCH_BARCHART` (NEW — pending enum) |

**Action when dep lands**: read the actual extended `unified_api_contracts/canonical/crosscutting/source_priority.py` + `pipeline_mode.py` and lock the per-handler mapping table from the SOURCE_PRIORITY top-entry per `(asset_group, data_type)`; some handlers dispatch multi-source (e.g. `oracle_prices_handler` does Pyth-then-Chainlink) — the `pipeline_mode=` value must be resolved per-row from which source actually served, not per-handler. This is the Q3 "orchestrator dispatch strategy" item — likely a small `_resolve_pipeline_mode_for_defi_source(source_name)` helper mirroring MDPS's `resolve_pipeline_mode_from_source(blob_path)`.

## Proposed sub-agent fan-out (5 sub-agents — spawn in ONE message; paste SUB_AGENT_MANDATORY_RULES.md at top of each)

Each sub-agent owns disjoint files (zero `.git/index` collision within-slot is FALSE — they share the slot worktree → strict named-file staging + per-agent commit discipline; the orchestrator (me) reconciles).

- **A — lending / yield / restaking handlers (≈30 callsites):** `staking_yields_handler.py` (9) + `lst_rates_handler.py` (5) + `lending_indices_handler.py` (4) + `vault_share_price_handler.py` (5) + `eigenlayer_rewards_handler.py` (3) + `_defi_manifest.py` (3 — shared `DefiManifestRecorder` helper; **Q1 — this is the legacy `ManifestWriter.add()` path, operator picked (α) migrate to v8 `record_captured()` — sub-agent A owns the `DefiManifestRecorder` v8-migration as the FIRST step, since the handlers below call it**).
- **B — DEX / swaps / pools / perp / gas (≈21 callsites):** `dex_swaps_handler.py` (3) + `dex_pools_handler.py` (3) + `evm_defi_handler.py` (3) + `solana_defi_handler.py` (3) + `perp_funding_handler.py` (3) + `gas_fee_handler.py` (9) — wait, that's 24; rebalance: move `gas_fee_handler.py` to D. B = dex_swaps + dex_pools + evm_defi + solana_defi + perp_funding (15).
- **C — events handlers (≈21 callsites):** `bridge_events_handler.py` (3) + `flash_loan_events_handler.py` (3) + `liquidation_events_handler.py` (3) + `liquidations_handler.py` (3) + `governance_events_handler.py` (3) + `mev_events_handler.py` (3) + `token_transfers_handler.py` (3).
- **D — oracle + gas + position-data (≈21 callsites):** `oracle_prices_handler.py` (6 — multi-source Pyth/Chainlink, needs the per-row resolver) + `gas_fee_handler.py` (9) + `position_data_handler.py` (6).
- **E — orchestrator + live (≈11 callsites):** `engine/orchestrator.py` (8 — orchestrator-level `record_failed`/`record_empty`; `pipeline_mode` resolved from the dispatched source; these are the "shard-isolation no-raise" paths) + `live/websocket_runner.py` (2) + `live/manifest_recorder.py` (1 — `LIVE_WEBSOCKET` mode, mirrors MDPS `_MDPSManifestRecorder`).

Roughly: A 30 / B 15 / C 21 / D 21 / E 11 = 98 (≈97). If Ikenna slot 3's commit already added `pipeline_mode=` to all of them, each sub-agent's job collapses to: add `service_emission_state` / `last_emission_decision_at` / `expected_window_completeness_fraction` on every `record_captured` in its files + run `cd market-tick-data-service && bash scripts/quality-gates.sh` (must stay green) + delete its files' entries from `pipeline_mode_explicit_baseline.yaml` (if pipeline_mode arg removed the WARNING) — coordinate the baseline-yaml edit through the orchestrator to avoid 5-way collision on one file.

## Done-definition (when executed)

- All 97 MTDS `record_*` callsites carry explicit `pipeline_mode=` (Ikenna slot 3) + every `record_captured` carries the 3 v8 columns (me).
- `cd market-tick-data-service && bash scripts/quality-gates.sh` green; QG STEP 5.64 (writegate AST sweep) + STEP 5.70 (`check_pipeline_mode_explicit_at_record_calls.py`) green workspace-wide; the 97 MTDS entries removed from `pipeline_mode_explicit_baseline.yaml`.
- `code_freeze_migrate_backfill_sequencing_2026_05_10.md` freeze-gate item 3 (line ~153) flipped `[ ]→[x]` once all 4 sub-items (MTDS / FEATURES / GREP-VERIFY / DEFAULT-REMOVAL) green — note FEATURES + DEFAULT-REMOVAL are NOT mine, so I flip only the MTDS half + annotate.
- writegate slice (c) Phase 6.1 MTDS verify done; `manifest_schema_final_gate` Phase 4.MTDS `[x]`.
- Cross-side INFO ping to ikenna-main with final counts; flip slot_3.md + DONE block.

## Cross-tab handshakes

- **→ slot 6 (manifest Phase 3 consumer sweep)**: publish "all MTDS writers on v8" signal once this lands (work-split Slot 3 → Slot 6 handshake).
- **→ slot 7 (mock_data_pipeline_benchmarking)**: per-service callsite closure list daily sync.
- **CARRY-FORWARD (Day-3+ pickup if budget)**: runner-shutdown/handler-hookup wire-in for `MTDSShardManifestRecorder` (`mtds@ab17cc3`/`8782225` shipped the recorder; the `ShardManifestRecorder` Protocol `close()` + runner shutdown call + handler `manifest_recorder=` wire + runner-calls-close test was pre-positioned by `mtds@8782225` but not completed — Ikenna slot 7 superseded but didn't include the wire-in half). If I touch the per-venue adapter fan-out (sub-agent E territory), close this gap. Per Harsh-slot-3 CONTINUE prompt CARRY-FORWARD note + `_agent_pings.md` 2026-05-12 line 57.
