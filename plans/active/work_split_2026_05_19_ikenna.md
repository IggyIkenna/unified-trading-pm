---
title: Ikenna's daily work-split — 2026-05-19 (Cycle 2 Day-4; full backlog sweep — all May-23 + no-deadline)
type: coordination-doc
status: active
created: 2026-05-19
deadline: 2026-05-23
horizon: 4 calendar days (19 May → 23 May); Cycle 2 close + Cycle 3 paper-smoke
companion_to: plans/active/work_split_2026_05_19_harsh.md
locked_by: live-defi-rollout
locked_since: 2026-05-19
estimate_class: infra
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 4.8
effective_concurrent_slots: 8
estimate_calibration_note: |
  Full-sweep day. All May-23-deadline + no-deadline backlog allocated across 8 implementer
  slots. Ikenna owns ~231 cal AI-days (2× Harsh's 116). Carries every deferred item from
  May-15 / May-16 / May-18 splits. Critical blocker: operator must trigger write-pause
  window FIRST (L3 + L5 flips gate on it). Inventory as of 2026-05-19 08:26 UTC:
  462 total / 236 May-23 critical-path / 97 no-deadline = 333 spreadable.
---

# Ikenna's daily work-split — 2026-05-19 (full backlog sweep)

> **Today = Cycle 2 Day-4 (last day).** Must close Cycle 2 by EOD: write-pause window + L3/L5 delegate-flip + archive
> old flat buckets + manifest re-sync + write-resume. Cycle 3 (paper-smoke) starts 2026-05-20.
>
> **P0 operator action required before slot 2 can proceed**: trigger MTDS + instruments-service write-pause (~30 min
> window). All delegate-flip pre-checks were green as of 2026-05-18 10:40 UTC.
>
> **Carries forward**: all open items from May-18 Ikenna split (slots 4/6/7/8 = 34 items), plus any May-15/16 deferrals
> still showing open in inventory (confirmed via inventory regeneration 2026-05-19).

---

## Hard rules

1. **Write-pause = operator-triggered.** Do NOT pause services autonomously. Slot 2 waits on operator go-ahead before
   executing L3/L5 flips.
2. **Half-1 + Half-2 discipline**: every shippable unit = (a) commit + push, then (b) flip checkbox with `docs(plans):`
   prefix commit, IN SAME AGENT TURN.
3. **Slot 1 precedence**: only slot 1 main edits `master_to_live_defi_2026_05_23.md`.
4. **Conflict check**: `git fetch` before every execution-service / deployment-api / UTL commit.
5. **pvl-p18a monitor**: Harsh dedicated slot is polling; Ikenna main does NOT poll.
6. **GCS backfill ≥1 week**: requires operator approval. <1 week = pre-authorized.

---

## Slot stack — ~231 cal AI-days across 8 implementer slots

| Slot      | Theme                                                                                             | Cal AI-days | Plans owned                                                            |
| --------- | ------------------------------------------------------------------------------------------------- | ----------- | ---------------------------------------------------------------------- |
| 1         | Main orchestrator (continuous, uncounted)                                                         | —           | This LEDGER                                                            |
| 2         | code_freeze Phase 2.6 close (write-pause + L3/L5 + archive)                                       | ~35         | code_freeze §2.6                                                       |
| 3         | code_freeze Phase 2.0–2.5 gaps + batch_live_symmetry Tabs 1–3                                     | ~35         | code_freeze §2.0–2.5, batch_live_symmetry                              |
| 4         | api_keys Phase 3–4 + defi_recursive_borrow Phase 3–4                                              | ~34         | api_keys, defi_recursive_borrow                                        |
| 5         | writegate Phase 6.6/6.7 + live_pipeline Phase 3–5                                                 | ~30         | writegate, live_pipeline                                               |
| 6         | deployment_ui_lifecycle_tabs (full 6-tab restructure)                                             | ~30         | deployment_ui_lifecycle_tabs                                           |
| 7         | cross_cutting_deliverables (12.4) + simulation_scenarios_topology (7.6) + defi_master Phase 2–3   | ~27         | cross_cutting_deliverables, simulation_scenarios_topology, defi_master |
| 8         | defi_catalogue close (27.2 remaining, 87%) + defi_simulation_realism final (0.7) + dex_perp close | ~29         | defi_catalogue, defi_simulation_realism, dex_perp_and_venue_data       |
| 9         | batch_live_symmetry Tabs 4–7 + cme_polymarket_arb Phase 1 + promote_workflow_may23 residuals      | ~31         | batch_live_symmetry, cme_polymarket_arb, promote_workflow_may23        |
| **Total** |                                                                                                   | **~251**    |                                                                        |

---

### Slot 1 — Main orchestrator (continuous)

1. **Write-pause coordination** — once operator signals ready: (a) confirm all delegate-flip code on LDR, (b) cross-ping
   Harsh-main to suspend any conflicting commits, (c) ack slot 2 to proceed.
2. **Cross-side ping triage** — respond to any outstanding pings in `_agent_pings.md` +
   `ikenna_orchestrator/_agent_pings.md`. May-18 12:17 UTC ping to Harsh (features_tick_observation_audit
   - StrategyDecisionContext correlation_id) needs Harsh-side ack — check and follow up.
3. **EOD inventory regenerator** — re-run after all slots report DONE.
4. **Master plan continuous-verification matrix** — flip `Last verified` per item shipped today.
5. **Harsh-side S3-S20 SUSTAIN sweep coordination** — ensure no surface conflicts.

---

### Slot 2 — code_freeze Phase 2.6 close (write-pause window) — ~35 cal AI-days

**BLOCKER**: wait for operator write-pause signal before executing L3/L5 flips.

**Plan**: `code_freeze_migrate_backfill_sequencing_2026_05_10.md` § Phase 2.6.

```bash
# Pre-write-pause (can do now while waiting):
cd .tabs/2/unified-trading-library
rg "get_bucket_name" --type py --glob '!.venv*' --glob '!tests'
# Identify the 36+ L3 consumers in cloud_constants.py et al.
```

1. - [ ] **L3 flip — UTL `get_bucket_name` → `resolve_bucket_name`** (36+ consumers in
         `unified_trading_library/cloud_interface/cloud_constants.py` + wrappers). Run QG. Push. (refactor 0.4×, ~8 =
         3.2 cal)
2. - [ ] **L5 flip — deployment-api `_BUCKET_TEMPLATES`** → `resolve_bucket_name()`. Run QG. Push. (refactor 0.4×, ~3 =
         1.2 cal)
3. - [ ] **Write-resume verification** — after operator redeploys: confirm manifest rows landing in env-tiered paths via
         `gcloud storage ls gs://{env-tiered-bucket}/` spot-check. (infra 0.8×, ~2 = 1.6 cal)
4. - [ ] **Archive old flat buckets** — run
         `bash deployment-service/scripts/archive-flat-buckets.sh    --env prod --cloud both` (30-day hold, not delete).
         (infra 0.8×, ~2 = 1.6 cal)
5. - [x] **GAP-2.0.B** — Confirm Stage 0 drain covers BOTH GCP + AWS VM fleets. Doc update. ✅ pm@`2af45259`
6. - [x] **GAP-2.0.C** — Update CLAUDE.md "No fire-and-forget" HARD RULE with pre-migration drain addendum. ✅
         pm@`2af45259`
7. - [x] ✅ **Reconcile phantoms** — run
         `python scripts/reconcile_phantom_manifest_rows_all.py    --asset-group cefi --dry-run` + repeat per
         asset_group. (infra 0.8×, ~2 = 1.6 cal) All 5 asset_groups show **0 phantoms** as of 2026-05-19:
         cefi=0/1290706 (128k prefixes, 34min), defi=0/311602 (89k prefixes, 23min), tradfi=0/245907,
         sports=0/559961, prediction=0/14403. Axes 7-9 fixes shipped 2026-05-13 (IS@1a62547) eliminated all
         false-positives from previous 2026-05-11 run. Manifest is clean across all 5 groups.
8. - [ ] **Phase 2 freeze gate** — flip all remaining `- [ ]` gate items in code_freeze §2. Push `docs(plans):` flip
         commit. (design 0.6×, ~1 = 0.6 cal)

---

### Slot 3 — code_freeze Phase 2.0–2.5 gaps + batch_live_symmetry Tabs 1–3 — ~35 cal AI-days

**Part A — code_freeze remaining Phase 2 gaps** (open `[GAP]` items not covered by slot 2):

1. - [x] ✅ **GAP-2.2.B** — Update CLAUDE.md "Honest absence" HARD RULE with Phase 2.2 GCS migration reference. (design
         0.6×, ~1 = 0.6 cal) — PM@`22d632c4`
2. - [x] ✅ **GAP-2.3.A** — Append Phase 2.X OHLCV legacy filename rename sub-section to code_freeze plan. (design 0.6×,
         ~2 = 1.2 cal) — PM@`1467b823`
3. - [x] ✅ **GAP-2.3.B** — Audit features-service readers for `ticks.parquet` literal path references. (research 1.2×,
         ~2 = 2.4 cal) — PM@`1467b823` (no breaking changes; 3 bundled-type paths safe)
4. - [ ] [BLOCKED-OPERATOR-APPROVAL] **Phase 2.5** — Run `manifest_cross_asset_rescan_design_2026_05_08.md` cross-asset
         `--apply-flips` sequence per the plan. (infra 0.8×, ~3 = 2.4 cal) cefi/defi/tradfi already done 2026-05-13.
         Sports (99,620 phantoms) + prediction (50) require operator approval per ≥1 week backfill rule. Launcher
         `launch-cross-asset-rescan-vm.sh` **now complete** with `--pass 1|2|3|4` sequential enforcement (deployment-service@880bc3a
         + instruments-service@5a0b115, 2026-05-19). Secondary blocker RESOLVED. Unblocks when operator approves
         sports/prediction apply-flips (operator [ack] required — use `bash launch-cross-asset-rescan-vm.sh --apply cefi`).
5. - [x] ✅ **gcs_migration_bundle Phase 4** — Consumer sweep audit complete. All production callsites already pass
         `pipeline_mode=` (MTDS DefiManifestRecorder, MDPS record_empty_for_shard, instruments-service orchestrator,
         features-service compute). PM@`22e23663` Phase 4 flipped DONE in plan. Phase 3 (VM fleet migration) =
         [BLOCKED-OPERATOR] — requires operator to trigger + cost-audit first. Phases 6/9 unblock after Phase 3.

**Part B — batch_live_symmetry Tabs 1–3** (plan at 34%, 19.7 cal left):

Read `batch_live_symmetry_2026_05_10.md` for open Tab 1/2/3 items. Tab 1 = codex SSOT batch, Tab 2 = UAC + UTL J1
helper + L7 sweep, Tab 3 = QG STEPs L2/L3/L7.

6. - [x] ✅ **Tab 1 — codex SSOT batch** (cefi-batch-live.md + mode-axis-discipline.md). ~200 lines each. (design 0.6×,
         ~5 = 3.0 cal) — batch_live_symmetry §Tab 1 all ✅; PM@`6153d9ea` (cefi-batch-live + mode-axis-discipline
         shipped) + PM@`9df278ef` (batch-live-architecture updated); full-exec verified: both files present + STEP
         5.75/5.76/5.77/5.78 in base-service.sh
7. - [x] ✅ **Tab 2 — UAC J1 helper + L7 sweep** per batch_live_symmetry plan §Tab 2. (brand-new 1.0×, ~5 = 5.0 cal) —
         batch_live_symmetry §Tab 2 all ✅; UAC@`01c1b59` (BatchExecutionMode + RECON_GREEN_THRESHOLDS + J1 stub) +
         exec@`b30167e2` (node_builder migrated); L7 fix-list documented for Tab 5/MDPS owner
8. - [x] ✅ **Tab 3 — QG STEPs L2/L3/L7 AST sweeps** per batch_live_symmetry plan §Tab 3. (refactor 0.4×, ~4 = 1.6 cal)
         — batch_live_symmetry §Tab 3 all ✅; PM@`5772f57b` (STEP 5.75+5.76) + PM@`fac14af3` (STEP 5.77 L2) +
         PM@`882faaa0` (STEP 5.78 L3); 0 workspace violations pre-flight; L7 sweep complete
9. - [x] ✅ **Plan checkboxes flip** for all items shipped. (0.5 cal) — PM@`450967d4` all slot-3 checkboxes flipped;
         gcs_migration Phase 4 + batch_live_symmetry Tabs 1-3 verified DONE

---

### Slot 4 — api_keys Phase 3–4 + defi_recursive_borrow Phase 3–4 — ~34 cal AI-days

**Part A — api_keys_wallets_accounts_readiness Phase 3 (Copper) + Phase 4 (DeFi mainnet)** (plan at 63%, 23.7 cal left):

1. - [ ] **Phase 3.A — Copper real-fund-movement test** — Execute small-amount transfer to confirm Copper API is live.
         Verify idempotency + response schema. (infra 0.8×, ~2 = 1.6 cal)
2. - [x] ✅ **Phase 3.B — CEFFU integration** — Start CEFFU KYB / API key sub-deliverables. Read api_keys §Phase 3.B for
         the sub-task list. (brand-new 1.0×, ~4 = 4.0 cal) — 3.B.3 stub shipped execution-service@027a8153b (OES +
         direct-custody shape-compatible; factory-registered; raises NotImplementedError until POD delivers spec
         June-1); 3.B.1/3.B.2 HUMAN; 3.B.4/3.B.5 blocked on human steps; (backfilled 2026-05-19)
3. - [x] ✅ **Phase 4.A — UAC DeFi wallet schema** — `WalletConfig` + `ChainWallet` + per-chain RPC wiring. (brand-new
         1.0×, ~3 = 3.0 cal) — uac@d721b6a (2026-05-12; WalletProvisioningConfig + SigningSurface + SpendingCaps + 27
         tests; backfilled 2026-05-19)
4. - [x] ✅ **Phase 4.B — PBM position-health endpoint** — per api_keys §4.C.B. (brand-new 1.0×, ~2 = 2.0 cal) —
         uac@1fababa + pbm@e93e3e5 (2026-05-15; GET /positions/health + PositionHealthSnapshot + 5s cache + 11 tests;
         backfilled 2026-05-19)
5. - [x] ✅ **Phase 4.C — UTL shared pre-flight helper** — per api_keys §4.C.C. (brand-new 1.0×, ~2 = 2.0 cal) —
         utl@b1b05343 (2026-05-15; run_wallet_preflight_checks 5-layer short-circuit + audit-log row; 21 tests QG green;
         backfilled 2026-05-19)
6. - [x] ✅ **Phase 4.D + 4.E — execution-service + DART wire-in** — per api_keys §4.C.D + 4.C.E. (brand-new 1.0×, ~1.5
         = 1.5 cal) — execution-service@754b22bf9 (2026-05-15; \_enforce_wallet_preflight + WalletPreflightRegistry +
         /instruction/precheck; 17 tests; backfilled 2026-05-19)

**Part B — defi_recursive_borrow Phase 3–4** (plan at 75%, 10.5 cal left):

7. - [x] ✅ **Phase 3 — Sim contract integration** — wire Aave/Compound flash-loan receiver into sim engine. Read plan
         for open items. (design 0.6×, ~4 = 2.4 cal) — strategy-service@44a8afc (2026-05-17;
         CARRY_RECURSIVE_BORROW_LENDING_ONLY + PERP_HEDGED builders in BUILDERS_BY_ARCHETYPE; tracer math
         net_apr_recursive + net_apr_with_perp_funding; QG green; backfilled 2026-05-19)
8. - [x] ✅ **Phase 4 — Per-family backtest scenarios** — carry + recursive-borrow scenario sets. (design 0.6×, ~6 = 3.6
         cal) — deployment-service@6dfac41 (2026-05-17; RecursiveLeverageReceiver.sol Option A + 11 foundry tests;
         security review passed; mainnet deploy BLOCKED-OPERATOR-DECISION wallet key human-only; backfilled 2026-05-19)
9. - [x] ✅ **Plan flips** for all shipped items. (0.5 cal) — backfill commit this turn
10. - [x] ✅ **Phase 4.C — CCTP bridge adapter** — api_keys §4.C (discovered open during boot, implemented this
          session). uac@a0238d3 + execution-service@05bdad628 (2026-05-19; CCTPBridgeConnector full: burn-and-mint USDC
          bridge, 10 EVM chains, 5 CCTP error codes, testnet_contracts.yaml addresses, 25 unit tests green)
11. - [x] ✅ **Batch-32 method-size refactor — instruments/factory_cefi_defi.py** — all 3 violations (235L, 249L, 95L)
          extracted to private helpers; all public methods now ≤50L; removed from FUNCTION_SIZE_EXTRA_EXCLUDES
          allowlist. execution-service@ca97b10db (2026-05-19; allowlist 12→11, slot-4 cumulative 98 files cleared)
12. - [x] ✅ **Batch-32 method-size refactor — config/grid_v2_registry.py** — all 3 violations (130L, 163L, 205L)
          extracted to private helpers; all public methods now ≤50L; removed from FUNCTION_SIZE_EXTRA_EXCLUDES
          allowlist. execution-service@911b4ffde (2026-05-19; allowlist 11→10, slot-4 cumulative 99 files cleared)
13. - [x] ✅ **Batch-32 method-size refactor — config/grid_generator_v2.py** — all 3 violations (157L, 199L, 215L)
          extracted to 7 additional private helpers (_build_venue_section, _build_grid_metadata,
          _load_strategy_components, _update_stats, _accumulate_strategy_configs, _finalize_gen_output,
          _setup_gen_context); all public methods now ≤50L; removed from FUNCTION_SIZE_EXTRA_EXCLUDES
          allowlist. execution-service@f27e5fc13 (2026-05-19; allowlist 10→9, slot-4 cumulative 100 files cleared)

---

### Slot 5 — writegate Phase 6.6/6.7 + live_pipeline Phase 3–5 — ~30 cal AI-days

**Part A — writegate Phase 6.6/6.7** (plan at 52%, 11.5 cal left):

1. - [x] ✅ **Phase 6.6 — ml-training-service emission wiring** — `_check_emission_policy()` + BLOCK_CRITICAL gate in
         `store_model()`; `training_completeness_fraction` param; 5 tests. — ml-training-service@ff20617 (pre-shipped
         2026-05-13)
2. - [x] ✅ **Phase 6.6 — ml-inference-service emission wiring** — `_check_emission_policy()` +
         `_filter_by_emission_policy()`
   - `_upload_one_mode()` in `prediction_publisher.py`; 4 STRICT_FAIL tests. — ml-inference-service@9fb5d50 (pre-shipped
     2026-05-13)
3. - [x] ✅ **Phase 6.7 — strategy-service emission wiring** — `_check_emission_policy` + gate in
         `SignalPublisher.publish()`; 4 tests. — strategy-service@88eb085 (pre-shipped 2026-05-13)
4. - [x] ✅ **Phase 6.7 — risk-and-exposure-service emission wiring** — `_check_emission_policy` + gate in
         `RiskSnapshotSink.write()`; 4 tests. — risk-and-exposure-service@df4849f (pre-shipped 2026-05-13)

**Part B — live_pipeline_mtds_mdps_features Phase 3–5** (15.0 cal budget):

Read `live_pipeline_mtds_mdps_features_2026_05_08.md` for remaining open items. Focus on:

5. - [x] ✅ **Phase 3 MTDS real-time adapter** — all WSFeedConnectors shipped across defi/cefi/tradfi/sports/prediction;
         Phase 3.5 COMPLETE. — MTDS@99fc7b3 (pre-shipped 2026-05-17)
6. - [x] ✅ **Phase 4 MDPS live consumer** — LiveStreamAggregator + 7 Protocol adapters + consumer wiring shipped. —
         mdps@0068b2f (pre-shipped 2026-05-11)
7. - [ ] **Plan flips** for all shipped items + downstream AUDIT P0 items (ml-training NaN-fill + ml-inference
         gap-blocking). (0.5 cal)

---

### Slot 6 — deployment_ui_lifecycle_tabs (full 6-tab restructure) — ~30 cal AI-days

**Plan**: `deployment_ui_lifecycle_tabs_2026_05_08.md` (30.0 cal, no progress yet — TBD baseline).

This is the cross-cutting 6-tab restructure of the deployment UI. Read the full plan before starting. Key tabs: Deploy,
Status, Logs, Strategy, Kill-switch, Config.

1. - [ ] **Pre-audit** — read plan + identify current UI tab structure vs target. Grep for existing tab components in
         `unified-trading-system-ui/`. (research 1.2×, ~1 = 1.2 cal)
2. - [ ] **Tab 1 — Deploy lifecycle** — wiring VM launch events to UI deploy tab. (brand-new 1.0×, ~5 = 5.0 cal)
3. - [ ] **Tab 2 — Status / data-freshness** — per-service health + manifest freshness feed. (brand-new 1.0×, ~5 = 5.0
         cal)
4. - [ ] **Tab 3 — Logs / event-stream** — WebSocket log tail per VM / service (Harsh slot-7 shipped WebSocket VM
         streaming May-18; wire it into this tab). (brand-new 1.0×, ~5 = 5.0 cal)
5. - [ ] **Tab 4 — Strategy panel** — promote / demote / paper → live controls. (brand-new 1.0×, ~5 = 5.0 cal)
6. - [ ] **Tab 5 — Kill-switch** — manual emergency halt per strategy / per service. (brand-new 1.0×, ~4 = 4.0 cal)
7. - [ ] **Plan flips** for each tab shipped. (0.5 cal)

---

### Slot 7 — cross_cutting_deliverables + simulation_scenarios_topology + defi_master — ~27 cal AI-days

**Part A — cross_cutting_may23_deliverables** (plan at 60%, 12.4 cal left):

Read `cross_cutting_may23_deliverables_2026_05_08.md` for open `- [ ]` items. Focus on:

1. - [x] ✅ **Strategy catalogue** — archetype × venue matrix in UAC; STRATEGY_REGISTRY + ArchetypeConfig SSOT. —
         uac@18bdc6e + uac@3cae1c2 (backfilled 2026-05-19)
2. - [x] ✅ **Strategy IDs** — stable ID schema + `parse_strategy_id` / `format_strategy_id` canonical helpers. —
         uac@5083d65 (backfilled 2026-05-19)
3. - [x] ✅ **Client model + accounts** — `CapitalAllocation` frozen dataclass + `CAPITAL_ALLOCATION_SEED` +
         `ClientDefinition` / `ClientRegistry` SSOT; 28 tests. — uac@3591037 + uac@3cae1c2 (backfilled 2026-05-19)

**Part B — simulation_scenarios_topology** (plan at 62%, 7.6 cal left):

4. - [x] ✅ **Phase 3 — scenario-runner integration** — 3.E `AdversarialMatchingEngine`
         (RejectFills/LatencyInject/BookSpoof at fill boundary) + 3.F alerting `synthetic=True` suppression +
         risk/alerting consumers. — execution-service@d0ec76f1 + alerting@3c0d675 (Harsh slot 5, 2026-05-12; backfilled
         2026-05-19)
5. - [x] ✅ **Phase 4 — per-scenario fixture sets** — 10 `ScenarioOverlay` registry instances (2 CeFi + 6 DeFi + 2
         cross_asset); SCENARIO_REGISTRY populated. — uac@33630a6 (slot 7 Day-2 2026-05-12; backfilled 2026-05-19)

**Part C — defi_master Phase 2–3** (plan at 33%, 9.4 cal left):

6. - [x] ✅ **Phase 2 — MTDS wiring for chain primitives** — UAC export surface (HYPERLIQUID/STARKNET RPC templates + ChainKind) shipped UAC@fa7e868+36eae39; MTDS `_ChainAnnotatingWriter` + `ONCHAIN_PERP_VENUE_CHAIN` dict + per-venue chain annotation wired for LIGHTER/PACIFICA/EXTENDED/HYPERLIQUID. — mtds@705a635 + uac@36eae39
7. - [x] ✅ **Phase 3 — instruments-service CLOB adapters** — Audit 2026-05-19: lighter.py + pacifica.py +
         extended.py all exist in instruments-service; factory.py + orchestrator wired; defi_master Phase 2
         checkbox flipped. — PM@d40d0f0d6
8. - [x] ✅ **Plan flips** for all shipped items. — PM@d40d0f0d6 + mtds@705a635

---

### Slot 8 — defi_catalogue close + defi_simulation_realism + dex_perp — ~29 cal AI-days

**Part A — defi_catalogue_chain_primitives** (plan at 87%, 27.2 cal left):

Read plan for the 9 remaining open items. Most are Phase 6 backfills + Phase 7 instrument wiring.

1. - [ ] **Phase 6 — per-chain backfill scripts** (items 6J, 7E unblocked — upstream shipped). Run backfill for each
         chain primitive. (infra 0.8×, ~6 = 4.8 cal)
2. - [x] ✅ **Phase 7.I — defi_catalogue instruments cross-ref** — already `[x] ✅` in plan body (slot 1 shipped PM@75560065 2026-05-18; Group F items 17-20 refreshed). No further action.
3. - [ ] **Remaining open items** — read plan body and ship all remaining `- [ ]` items in order. (mixed, ~10 = 8.0 cal)
4. - [ ] **Close defi_catalogue** — flip all remaining checkboxes; mark plan `status: complete` if all done. Push. (0.5
         cal)

**Part B — defi_simulation_realism** (plan at 98%, 0.7 cal left — 1 item):

5. - [x] ✅ **Final item** — `defi_simulation_realism_2026_05_10.md` ARCHIVED in `plans/archive/` with 0 open items. All items `[x]`. No remaining work.

**Part C — dex_perp_and_venue_data** (plan at 94%, 0.5 cal left):

6. - [ ] **Final 2 items** — (1) VM launcher for Extended OHLCV backfill: `BLOCKED-OPERATOR-DECISION` (ping in plan body §2F); (2) Uniswap V3 subgraph research: `DEFERRED NICE-TO-HAVE P3` per plan body §4C. Both items unshippable without operator unblock. dex_perp at 94% done.

**Part D — hard_schema_enforcement** (no-deadline, 4.8 cal):

7. - [ ] **Open items** — read `hard_schema_enforcement_2026_05_08.md` and ship remaining items. (design 0.6×, ~8 = 4.8
         cal)

---

### Slot 9 — batch_live_symmetry Tabs 4–7 + cme_polymarket_arb + promote_workflow_may23 — ~31 cal AI-days

**Part A — batch_live_symmetry Tabs 4–7** (continuation from slot 3's Tabs 1–3):

1. - [ ] **Tab 4 — features-service ModeHandler lift (4 families)** — commodity / cross_instrument / multi_timeframe /
         calendar. Per plan §Tab 4. (brand-new 1.0×, ~6 = 6.0 cal)
2. - [ ] **Tab 5 — feature emission wiring** — per plan §Tab 5. (brand-new 1.0×, ~5 = 5.0 cal)
3. - [ ] **Tabs 6–7** — remaining plan tabs. Read plan for items. (brand-new 1.0×, ~4 = 4.0 cal)

**Part B — cme_polymarket_arb Phase 1** (no-deadline, 15.0 cal):

4. - [ ] **Phase 1 — InstrumentType.EVENT_CONTRACT + UAC schema** — per `cme_polymarket_arb_2026_05_08.md`. (brand-new
         1.0×, ~5 = 5.0 cal)
5. - [ ] **Phase 2 — MTDS Polymarket + CME adapter scaffolds** — per plan Phase 2. (brand-new 1.0×, ~5 = 5.0 cal)

**Part C — promote_workflow_may23 residuals** (plan at 62%, 1.6 cal left):

6. - [ ] **Remaining open items** — read `promote_workflow_may23_cli_path_2026_05_10.md` and ship all remaining `- [ ]`
         items. (design 0.6×, ~3 = 1.6 cal)
7. - [ ] **Plan flips** for all shipped. (0.5 cal)

---

## Operator-action items pending (from prior cycles)

| #   | Item                                                                       | Status                 | Ping filed    |
| --- | -------------------------------------------------------------------------- | ---------------------- | ------------- |
| 1   | **Write-pause** — trigger MTDS + instruments-service pause for L3/L5 flips | 🔴 BLOCKING slot 2     | May-18 slot 1 |
| 2   | **tradfi-fwd cron deployment** — tradfi_forward_cron_missing_2026_05_17.md | 🟡 BLOCKED-OPERATOR    | May-17        |
| 3   | **Phase 7.G manifest v8 sign-off** — 5 asset_groups                        | 🟡 BLOCKED-OPERATOR    | May-15        |
| 4   | **Phase 3c lending VM re-run** — USDT/USDC IRM re-run                      | 🟡 BLOCKED-OPERATOR    | May-15        |
| 5   | **Kalshi credential** (5.B.2)                                              | 🟡 BLOCKED-CREDENTIALS | May-18 slot 8 |
| 6   | **CoinGecko credential** (5.C)                                             | 🟡 BLOCKED-CREDENTIALS | May-18 slot 8 |

---

## Done-definition (2026-05-19 EOD)

- Slot 2: L3 + L5 flips on LDR + archive script run + write-resume verified + phantoms clean.
- Slot 3: code_freeze Phase 2.0–2.5 gaps closed + batch_live_symmetry Tabs 1–3 on LDR.
- Slot 4: api_keys Phase 3.A + 4.A–4.E + defi_recursive_borrow Phase 3–4 all on LDR.
- Slot 5: writegate Phase 6.6 (ml-training + ml-inference) + Phase 6.7 (strategy + risk) on LDR.
- Slot 6: deployment_ui_lifecycle_tabs ≥ 3 tabs shipped, plan ≥50% checked off.
- Slot 7: cross_cutting strategy catalogue + strategy IDs + simulation Phase 3 on LDR.
- Slot 8: defi_catalogue ≥95% done + defi_simulation_realism 100% + hard_schema shipped.
- Slot 9: batch_live_symmetry Tabs 4–7 + cme_polymarket_arb Phase 1 on LDR.

---

## Spawn prompt — paste into each tab (slot N)

```text
You are slot N (Ikenna side). Today is 2026-05-19 (Cycle 2 Day-4 — full backlog sweep).

Boot:
1. SYNC TO LDR — from .tabs/<N>/:
     for d in */; do
       (cd "$d" && [ -d .git -o -f .git ] && \
        git fetch origin live-defi-rollout --quiet && \
        git merge --ff-only origin/live-defi-rollout 2>/dev/null) ;
     done

2. Read unified-trading-pm/ikenna_orchestrator/AGENT_ONBOARDING.md

3. Read unified-trading-pm/plans/active/work_split_2026_05_19_ikenna.md § "Slot <N>"

4. Read your top plan-of-record (listed in the slot section above).

5. Boot ack at unified-trading-pm/ikenna_orchestrator/pings/slot_<N>.md using `date -u`.

CRITICAL RULES:
* Plan-flip discipline: every shippable unit = (Half 1) commit + push code, then
  (Half 2) flip checkbox with docs(plans): prefix commit IN SAME AGENT TURN.
* git fetch before every commit on shared repos (execution-service, UTL, UAC,
  deployment-api, deployment-service).
* QG before push: bash scripts/quality-gates.sh (Pass 1). Then quickmerge or direct push.
* Slot 2 ONLY: do NOT flip L3/L5 until operator signals write-pause is active.
* Slot 6: check for Harsh slot-7 deployment-ui commits before pushing.

Now begin.
```
