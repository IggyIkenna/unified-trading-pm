---
title: Ikenna's daily work-split — 2026-05-15 (Day-4, ~150 cal AI-days, post-freeze-gate cycle)
type: coordination-doc
status: active
created: 2026-05-15
deadline: 2026-05-23 (live DeFi cutover)
horizon: ~8 calendar days (15 May → 23 May); ~150 cal AI-days across 8 implementer slots
companion_to: plans/active/work_split_2026_05_14_ikenna.md
locked_by: live-defi-rollout
locked_since: 2026-05-15
---

# Ikenna's daily work-split — 2026-05-15

> **Cycle context**: Day-4 of the density push. Phase 1 freeze gate fired 2026-05-15. This split **continues from
> 14 May** — absorbs every unfinished 14 May item across slots 2/4/5/6/7/8 + folded-in slot 9/10/11 carry-overs +
> 3 new top-priority items surfaced today. ~150 cal AI-days across 8 implementer slots (avg ~19 cal/slot).
>
> **Stream C P1 archetype docs** (7 docs) — operator direction 2026-05-15: pull back from post-cutover deferral
> ("its just docs, why not"). Routed slot 2 below.

---

## Hard rules baked into this split (carry-over from 14 May)

1. **External Data Is Always Available — Never Silently Defer Adapters (HARD RULE codified 2026-05-14)**: if any
   adapter hits "no data" wall, file `CREDENTIAL APPROVAL REQUEST` in slot pings; status `BLOCKED-CREDENTIALS`;
   adapter scaffold + unit tests still ship. NEVER move to post-cutover plan without operator [ack].
2. **GCS backfill approval gate**: ≥1 week backfill = operator approval ping first. <1 week = pre-authorized.
3. **Singleton-locked + watchdog-registered launchers only** — no fire-and-forget VMs. STARTED within 60s +
   ≥1 progress event/hour + STOPPED at exit.
4. **Half-1 + Half-2 plan-flip discipline (HARD RULE strengthened 2026-05-15)**: every shippable unit =
   (a) commit + push code, then (b) flip `- [ ]` → `- [x] ✅ ... — <repo>@<sha>` in the SAME AGENT TURN with
   `docs(plans):` prefix. Two consecutive code commits without a sibling docs(plans) flip = rule violation.
   Reference incident: slots 5+7 each shipped 15+ items unflipped on 14 May → dashboard reported 14.5% when
   real was ~70%. See CLAUDE.md § "Commit + Push + Flip Plan Checkboxes".
5. **DeFi recursive borrow Phases 4-11 IN-SCOPE** (operator direction 2026-05-14, DESCOPE REVERSED).
6. **Wallet/Treasury Phase 2** (Copper / CEFFU): CLIENT-SIDE — not our blocker.

---

## Slot stack — ~150 cal AI-days across 8 implementer slots

| Slot | Theme | Cal AI-days |
| --- | --- | --- |
| 1 | Main orchestrator (continuous, uncounted) | — |
| 2 | DeFi catalogue closure + Helius wire-in + Stream C P1 archetype docs + Polymarket | ~20 |
| 3 | Perp venue gaps + Solana adapter expansion + Kraken live + arbitrage_price_dispersion finalisation | ~18 |
| 4 | Sports classifier + propagation + 6-bucket provisioning + expected_universe_v2 | ~19 |
| 5 | TradFi backfills + master refresh + Phase 5 QG ratchet + strategy LTV thresholds | ~20 |
| 6 | **manifest v8 Phase 6+7 (May-13-15 op-gated)** + phase_3c lending model + alerting | ~22 |
| 7 | **SIT critical-path scenarios (May-23 BLOCKER)** + basefc paradigm + audit_records + writegate finalize | ~28 |
| 8 | B-015 smoke re-launch + solana_defi venue naming + audit close + governance | ~18 |
| **Total** | (8 implementer slots) | **~145** |
| **+ buffer** | (in-stack reserve per slot for surfacing issues) | **+5** |
| **Grand total** | | **~150** |

---

### Slot 1 main — orchestration (continuous, uncounted)

1. Daily inventory regenerator + master plan refresh (morning + EOD).
2. Cross-side `_agent_pings.md` triage every ~5 min while operator active.
3. **Phase 7.G operator sign-off coordination** — when slot 6 hits QA gate green per asset_group, page operator for
   sign-off (5 asset_groups: cefi / defi / tradfi / sports / prediction).
4. Codex doc currency monitoring — flag drift between codex SSOTs and shipped contracts.
5. Continuous-verification column updates in master plan per HARD RULE.
6. Stream-C / paradigm-migration / SIT-scenarios coordination across slots 2+7.

---

### Slot 2 — DeFi catalogue + Helius + Stream C archetype docs + Polymarket — ~20 cal AI-days

Plan fan-out: `defi_catalogue_chain_primitives_2026_05_10` (74% done, 18 open todos) +
`wave2_polymarket_record_captured_from_counts_2026_05_09` + Stream C P1 archetype docs (pulled from
post-cutover per 2026-05-15 operator) + Helius `mev_apy` integration (credentials just landed) +
`cme_polymarket_arb_2026_05_08` (carry from slot 9 reassignment) + `cross_asset_group_catalogue_audit` Phase 6A
DeFi remainder.

1. **Helius `native_staking` mev_apy integration** — credentials vaulted at `helius-api-key` (operator provisioned
   2026-05-15); MTDS service account granted access. Flip integration tests from `@pytest.mark.requires_credentials`
   skip to live; endpoint `https://mainnet.helius-rpc.com/?api-key=<vaulted>`. Unblocks `carry_staked_basis` Solana
   leg `total_apy` (base_apy + mev_apy). (infra 0.8×, ~3 = 2.4 cal)
2. **Stream C P1 — 7 remaining archetype docs** (operator direction 2026-05-15: pulled from post-cutover; pure docs).
   Each archetype gets a `codex/09-strategy/architecture-v2/archetypes/<archetype>.md` per the canonical 9-strategy
   docs pattern. Targets: 7 archetypes that don't yet have docs. (refactor 0.4×, ~5 = 2.0 cal)
3. **`defi_catalogue_chain_primitives_2026_05_10` close-out** — 18 remaining open todos (chain-primitive UAC schema
   additions + downstream MTDS/features wiring). (design 0.6×, ~8 = 4.8 cal)
4. **`wave2_polymarket_record_captured_from_counts` Polymarket subset** (carry from 14 May) — wire counts →
   `record_captured()` for Polymarket market-state shards. (research 1.2×, ~3 = 3.6 cal)
5. **`cme_polymarket_arb_2026_05_08` close-out** (carry from slot 9 reassignment 14 May) — DeFi/Polymarket overlap.
   (design 0.6×, ~3 = 1.8 cal)
6. **`cross_asset_group_catalogue_audit` Phase 6A DeFi half remainder** — DeFi-specific catalogue parity audit.
   (research 1.2×, ~2 = 2.4 cal)
7. **`cross_asset_instruments_service_scope` triage** (carry from slot 9 reassignment) — instruments-service scope
   decision for cross_asset symbols. (research 1.2×, ~2 = 2.4 cal)
8. **Reserve**: in-stack pickup for new DeFi classification surfacings.

---

### Slot 3 — Perp venues + Solana expansion + Kraken live + APD finalisation — ~18 cal AI-days

Plan fan-out: `emerging_perp_venue_adapters_broken` remainder + Solana DEX adapter expansion (Phoenix / Orca /
Raydium / Drift) + Kraken live REST+WS integration (credentials in vault) +
`arbitrage_price_dispersion_finalisation_2026_05_09` (carry from slot 9 reassignment).

1. **Kraken CeFi live REST + WS integration** — credentials vaulted (`bybit_api_key`/`bybit_api_secret` v2
   authenticated 2026-05-15 with Spot + Derivatives perms; also Kraken testnet API onboarded). Wire
   `KrakenCeFiAdapter` scaffold from `execution-service@4d4d8e12d` to live data flow. (infra 0.8×, ~3 = 2.4 cal)
2. **Solana DEX adapter expansion — Phoenix / Orca / Raydium / Drift** — extend MTDS DeFi handlers per
   `defi_master_2026_05_07` venue matrix. (design 0.6×, ~5 = 3.0 cal)
3. **`emerging_perp_venue_adapters_broken` remainder** — close remaining broken-venue items per Day-3 status.
   (research 1.2×, ~2 = 2.4 cal)
4. **`arbitrage_price_dispersion_finalisation_2026_05_09`** (carry from slot 9 reassignment) — push remaining
   finalisation items. (design 0.6×, ~4 = 2.4 cal)
5. **Hyperliquid arb_price_dispersion eligibility close** — verify USDC-margin + 7-venue dispersion universe.
   (research 1.2×, ~2 = 2.4 cal)
6. **`helius_solana_rpc_for_validation` final close** (credentials now in vault — last wire-up). (infra 0.8×,
   ~2 = 1.6 cal)
7. **Aster + Bybit UTA `carry_staked_basis` LST_AS_MARGIN final** — eligibility-matrix close. (research 1.2×,
   ~2 = 2.4 cal)
8. **Reserve**: in-stack pickup for any Solana RPC ratelimit handling.

---

### Slot 4 — Sports classifier + propagation + 6-bucket + universe — ~19 cal AI-days

Plan fan-out: 3 sports classifier issues final close-out + propagation chain Phase 3.1-3.N + 6-bucket provisioning
(re-activate from DEFERRED) + `expected_universe_v2_design` (carry from slot 9 reassignment) + sports/prediction
phantom apply-flips remainder + `api_football_minimal_flattening_removal_2026_05_07`.

1. **6-bucket provisioning re-activate** (carry from 14 May DEFERRED item #5) — sports/prediction bucket provisioning
   per `bucket_name_ssot_canonicalisation` env-aware matrix. Re-evaluate deferral reason; if blocker resolved, ship.
   (infra 0.8×, ~3 = 2.4 cal)
2. **`expected_unattempted_propagation_gap` P1** — close remaining propagation cascade. (research 1.2×, ~3 = 3.6 cal)
3. **Sports/prediction phantom apply-flips remainder** (sports/pred 16.8% + 0.49% phantoms per 2026-05-12 audit) —
   reconcile + apply-flips on same-region GCE VM. (infra 0.8×, ~2 = 1.6 cal)
4. **propagation chain Phase 3.1-3.N + Phase 4 + PART C remainder**. (refactor 0.4×, ~4 = 1.6 cal)
5. **`api_football_minimal_flattening_removal_2026_05_07` close** (carry from 14 May). (refactor 0.4×, ~3 = 1.2 cal)
6. **`expected_universe_v2_design_2026_05_08`** (carry from slot 9 V2) — sports/prediction universe enumerator
   design. (design 0.6×, ~3 = 1.8 cal)
7. **`sports_master_2026_05_07` data_type universe coverage audit** — cross-ref vs `cross_asset_group_catalogue_audit`.
   (research 1.2×, ~3 = 3.6 cal)
8. **`data_status_comprehensive_test_coverage_2026_05_07` sports-half close** — drilldown-shard-atom alignment tests.
   (design 0.6×, ~3 = 1.8 cal)
9. **3 sports classifier issues final verification** — confirm sfi_footystats / player_values / weather close. (refactor
   0.4×, ~2 = 0.8 cal)
10. **Reserve**: in-stack pickup for any sports classifier ambiguity.

---

### Slot 5 — TradFi backfills + master refresh + Phase 5 QG + LTV thresholds — ~20 cal AI-days

Plan fan-out: TradFi Item 2 Phase 5 QG ratchet (carry from 14 May #3) + tradfi backfills (Databento + CME/EUREX 1-week
each, operator-approval pending) + `tradfi_master_2026_05_07` master refresh + `strategy_service_qg_ltv_threshold_violations_2026_05_15` +
`mtf_intraday_micro_regime_policy` (carry from slot 9) + `sports_retired_data_types_code_cleanup` non-sports half.

1. **TradFi 1-week test backfill execution** (carry from 14 May #4; <7 days AUTHORIZED no operator approval needed) —
   run on same-region GCE VM, verify sample parquets OHLC-populated + manifest captured rows match planned scope.
   (infra 0.8×, ~3 = 2.4 cal)
2. **Databento session-stamp backfill — operator approval pending** (≥1-week — slot 5 filed CREDENTIAL APPROVAL
   REQUEST 2026-05-15). Script: `market-tick-data-service/scripts/migrate_tradfi_ohlcv_session_stamps.py`. **OPERATOR
   ACTION REQUIRED**: ack the request in `pings/slot_5.md` to unblock VM launch. (infra 0.8×, ~3 = 2.4 cal)
3. **TradFi Item 2 Phase 5 QG ratchet** (carry from 14 May #3) — QG STEP enforcement banning legacy futures-contract
   shape (operator GREENLIT). (design 0.6×, ~3 = 1.8 cal)
4. **`tradfi_master_2026_05_07` master plan refresh** (carry from 14 May #5) — push remaining open todos
   workspace-wide. (research 1.2×, ~4 = 4.8 cal)
5. **`tradfi_master_2026_05_07` venue + symbology coverage audit** (carry from 14 May #8). (research 1.2×, ~3 = 3.6 cal)
6. **CME/EUREX 1-week test backfill** (carry from 14 May #10; AUTHORIZED). (infra 0.8×, ~2 = 1.6 cal)
7. **`strategy_service_qg_ltv_threshold_violations_2026_05_15` close** (carry from 14 May #11) — migrate to UAC
   `LIQUIDATION_PARAMS_REGISTRY`. (refactor 0.4×, ~1 = 0.4 cal)
8. **`mtf_intraday_micro_regime_policy` 2 dict entries** (carry from slot 9 #4 reassignment). (design 0.6×,
   ~1 = 0.6 cal)
9. **`sports_retired_data_types_code_cleanup` non-sports half** (carry from 14 May #7) — retire dead data_types from
   cross-cutting / UAC side. (refactor 0.4×, ~3 = 1.2 cal)
10. **TradFi venue calendar SSOT `MarketSession` final close** — operator answered Yes 2026-05-13; backfill VM ask
    pending. (design 0.6×, ~2 = 1.2 cal)
11. **Reserve**: in-stack pickup for any tradfi QG enforcement gaps.

Backfill flag: items 1 + 6 <1 week — pre-authorized; item 2 ≥1 week — **OPERATOR ACK REQUIRED**.

---

### Slot 6 — manifest v8 Phase 6+7 + phase_3c lending + alerting close — ~22 cal AI-days

Plan fan-out: `manifest_schema_final_gate_2026_05_09.md` Phase 6+7 (TOP PRIORITY — May-13-15 operator-gated window IS
NOW) + `phase_3c_lending_rate_model` continuation (UNBOUNDED per operator) + alerting close-out + audit_records Phase 1
+ `available_at_lookahead_bias_completion_2026_05_08` close + alerting_runbook operator-UX remainder.

1. **🔴 [TOP PRIORITY] `manifest_schema_final_gate_2026_05_09.md` Phase 6 + Phase 7 — v8 GCS bundled walk
   (May-13-15 operator-gated window IS NOW; we're in day 3 of 3)** — slot 6 is the plan owner. **Phase 6**:
   bounce-sweep stale VMs (`gcloud compute instances list --project=central-element-323112 --filter="status=RUNNING"`
   → confirm STOPPED or graceful shutdown). **Phase 7.A pre-flight** (Phase 1-5 ✅ + Phase 6 drain confirmed).
   **Phase 7.B snapshot** per-bucket `_index/` to `gs://{pid}-pre-migration-snapshot/`. **Phase 7.C launch fleet**:
   per-bucket 4-8 migration VMs in asia-northeast1-c with `MANIFEST_PER_VM_SHARDS=true` + unique `VM_NAME`.
   **Phase 7.D-E** event stream watch + manifest consolidator. **Phase 7.F** per-asset-group QA gate (phantom
   count MUST be 0). **Phase 7.G** cross-ping slot 1 main per asset_group when QA green for **operator sign-off**
   (5 sub-checkboxes: cefi/defi/tradfi/sports/prediction). (infra 0.8×, ~6 = 4.8 cal)
2. **🔴 `phase_3c_lending_rate_model` continuation** — 5th bug fix shipped 2026-05-14
   (`execution-service@70825a432`); UAC IRM defaults updated (`unified-api-contracts@215ed3e`). **Awaiting operator
   VM re-run** to confirm USDT 55%→90%+, USDC 85%→90%+, DAI TBD. (a) coordinate VM run via operator ping;
   (b) if DAI still fails, find DAI IRM source. (research 1.2×, ~4 = 4.8 cal — unbounded per operator)
3. **`audit_records_pb_1_2_3_pre_cutover_2026_05_13` Phase 1 close** — pre-cutover audit-records gate. (research
   1.2×, ~3 = 3.6 cal)
4. **`available_at_lookahead_bias_completion_2026_05_08` sweep close** — remaining stamping helper consumers.
   (refactor 0.4×, ~3 = 1.2 cal)
5. **`alerting_runbook_and_operator_ux_post_cutover_2026_05_12` operator-UX remainder**. (design 0.6×, ~3 = 1.8 cal)
6. **Custody Cloud-KMS smoke + 4 DeFi alert-codes alerting wiring final**. (design 0.6×, ~3 = 1.8 cal)
7. **DeFi handler hardening verification across all 4 handlers** (post-`market-tick-data-service@c1e6963` + `@f657431`)
   — confirm record_captured INSIDE try/finally per eigenlayer pattern; spot-check next smoke re-launch. (research
   1.2×, ~2 = 2.4 cal)
8. **`strategy_paper_vm_nautilus_trader_missing_dep` re-verify** (carry from slot 9 #5). (refactor 0.4×,
   ~0.5 = 0.2 cal)
9. **Reserve**: in-stack pickup for any wallet/custody issues.

---

### Slot 7 — SIT critical-path BLOCKER + basefc paradigm + audit + writegate finalize — ~28 cal AI-days

Plan fan-out: **`sit_may23_critical_path_coverage_gaps_2026_05_15` (MAY-23 BLOCKER)** +
`basefc_validation_flip_2026_05_10` items 1-5 + `audit_records_pb_1_2_3` Phase 2-3 + writegate Phase 6.6/6.7/6.9
α-vs-β audit (carry from slot 10 reassignment) + `client_reporting_pnl_attribution_mvp` + `compute_optimization_mock_data`
Ikenna-half + `mock_data_pipeline_benchmarking` Phase 8.A + `context_fill_optimization`.

1. **🔴 [MAY-23 BLOCKER] `sit_may23_critical_path_coverage_gaps_2026_05_15`** — 3 SIT scenario playbooks:
   (a) `defi_carry_staked_basis_paper` — LST rates → strategy → execution → PBM manifest;
   (b) `defi_apd_paper` — DEX/CEX dispersion → strategy → execution;
   (c) `defi_paper_to_live_early_gate` — MinimalCandidateManifest → promote → VM event + DART gate.
   Add to `system-integration-tests/tests/scenarios/defi_scenarios.py` + wire into
   `tests/overnight/test_archetype_cascade.py` parametrization. Last automated CI gate before paper→live_early
   manual promotion. (brand-new 1.0×, ~4.5 = 4.5 cal)
2. **`basefc_validation_flip_2026_05_10` items 1-5** — calculator paradigm migration (decide flip strategy →
   migrate concrete calculators → flip UTL canonical validate_class_attributes → plan-flip cite). Item 6 auto-closes.
   (refactor 0.4×, ~6 = 2.4 cal)
3. **writegate Phase 6.6 + 6.7 + 6.9 α-vs-β audit** (carry from slot 10 reassignment) — 9 services audit; β verdict
   closes Gate 4. (research 1.2×, ~4 = 4.8 cal)
4. **`audit_records_pb_1_2_3_pre_cutover_2026_05_13` Phase 2-3** — close pre-cutover audit gate items. (research
   1.2×, ~4 = 4.8 cal)
5. **`client_reporting_pnl_attribution_mvp_2026_05_10` push** — open todos workspace-wide. (design 0.6×,
   ~4 = 2.4 cal)
6. **`compute_optimization_mock_data_2026_05_13` Ikenna-half** — mock-data compute cost reduction for CI.
   (design 0.6×, ~3 = 1.8 cal)
7. **`mock_data_pipeline_benchmarking_2026_05_10` Phase 8.A** (orphan from slot 7 14 May) — master plan Group F
   item 18 row budget assertion. (infra 0.8×, ~3 = 2.4 cal)
8. **`data_status_drilldown_shard_atom_alignment_2026_05_07` finalize**. (research 1.2×, ~3 = 3.6 cal)
9. **`context_fill_optimization_2026_05_14` Phase 1**. (research 1.2×, ~2 = 2.4 cal)
10. **Reserve**: in-stack pickup for SIT scenario surfacings.

---

### Slot 8 — B-015 smoke re-launch + solana_defi venue naming + audit close + governance — ~18 cal AI-days

Plan fan-out: B-015 smoke re-launch coordination (apply-flips audit complete; manifest CLEAN) +
`solana_defi_coverage_gaps` successor D venue naming + `AUDIT_pre_may_8_cleanup_2026_05_13` close +
`bucket_name_ssot_canonicalisation_2026_05_10` workspace flip (carry from slot 9) +
`code_freeze_migrate_backfill_sequencing_2026_05_10` cross-cutting audit (carry from slot 9) +
`governance_qg_automation_gaps_post_cutover_2026_05_12` codification + `deploy_missing_auto_launch_2026_05_07` close
(V2) + Cluster B pnl-attribution lint.

1. **B-015 smoke re-launch coordination** — phantom audit returned CLEAN per
   `plans/active/issues/b_015_smoke_vms_phantom_manifest_silent_skip_2026_05_15.md` resolution update
   (2026-05-15 11:22-11:23 UTC); root cause was STALE IN-FLIGHT LOCK not phantoms. Coordinate with Harsh slot 9 to
   re-launch MTDS lst_rates smoke with UNIQUE `VM_NAME=mtds-lst-rates-smoke-v2-20260515` + features-onchain smoke
   investigation (no event stream on first launch — get serial-console output). Apply-flips NOT needed. (infra
   0.8×, ~2 = 1.6 cal)
2. **`solana_defi_coverage_gaps` successor D venue naming reconciliation** (carry from 14 May #2). (design 0.6×,
   ~3 = 1.8 cal)
3. **`AUDIT_pre_may_8_cleanup_2026_05_13` close** (carry from 14 May #3). (refactor 0.4×, ~3 = 1.2 cal)
4. **`bucket_name_ssot_canonicalisation_2026_05_10` workspace flip** (carry from slot 9 #7) — remaining
   call-site sweep + QG ratchet enforcement. (refactor 0.4×, ~4 = 1.6 cal)
5. **`code_freeze_migrate_backfill_sequencing_2026_05_10` cross-cutting audit** (carry from slot 9 #10) —
   sequencing items + TradFi cross-asset items. (research 1.2×, ~3 = 3.6 cal)
6. **`governance_qg_automation_gaps_post_cutover_2026_05_12` codification** (carry from slot 9 #12) — Runbook
   Execution-Owner SSOT gaps. (design 0.6×, ~3 = 1.8 cal)
7. **`deploy_missing_auto_launch_2026_05_07` close** (V2 carry from slot 9) — cross-cutting auto-launch cleanup.
   (infra 0.8×, ~3 = 2.4 cal)
8. **Cluster B pnl-attribution-service lint sweep**. (refactor 0.4×, ~2 = 0.8 cal)
9. **`honest_coverage_cron_vm_scheduling`** (carry from slot 9 #3) — verify scheduler-fire post operator-ran
   setup script + per-day output. (infra 0.8×, ~2 = 1.6 cal)
10. **Reserve**: in-stack pickup for any UAC drift surfacings.

---

## Top-priority items for 2026-05-15 (cross-slot)

| Priority | Item | Owner | Why |
| --- | --- | --- | --- |
| **P0** | manifest v8 Phase 6+7 | Slot 6 #1 | Operator-gated window IS NOW (day 3 of 3); operator sign-off per asset_group needed |
| **P0** | SIT critical-path scenarios | Slot 7 #1 | Last automated CI gate before paper→live_early manual promotion |
| **P0** | B-015 smoke re-launch | Slot 8 #1 + Harsh slot 9 | `carry_staked_basis` paper-trade gate; manifest clean, just needs new VM_NAME |
| **P1** | phase_3c lending model VM re-run | Slot 6 #2 + operator | Awaiting operator VM run to confirm USDT 90%+ + USDC 90%+ |
| **P1** | Databento session-stamp backfill | Slot 5 #2 + operator | ≥1-week backfill ack pending |

## Operator-action items pending

1. **Phase 7.G v8 sign-off** — 5 asset_groups; slot 6 will cross-ping per asset_group when QA green.
2. **phase_3c lending VM re-run** — operator approves slot 6 #2 VM launch for re-run.
3. **Databento session-stamp backfill ≥1 week** — operator approves slot 5 #2 per CREDENTIAL APPROVAL REQUEST shape.

---

## Spawn prompt — paste into each tab (slot N)

```text
You are slot N (Ikenna side). Boot in order:

1. SYNC TO LDR — pull latest in every owned repo. From .tabs/<N>/:
     for d in */; do
       (cd "$d" && [ -d .git -o -f .git ] && git fetch origin live-defi-rollout --quiet && \
        git merge --ff-only origin/live-defi-rollout 2>/dev/null) ;
     done

2. Read unified-trading-pm/ikenna_orchestrator/AGENT_ONBOARDING.md (LDR-alignment HARD RULE,
   plan-flip Half-1+Half-2 discipline, GCS backfill rule, External-Data HARD RULE).

3. Read unified-trading-pm/plans/active/work_split_2026_05_15_ikenna.md § "Slot <N>".
   Look for items annotated **[CARRY FROM 14 MAY]** — these continue work-in-flight from yesterday.

4. Read your top plan-of-record.

5. Boot ack at unified-trading-pm/ikenna_orchestrator/pings/slot_<N>.md using `date -u`,
   one line. Then start work.

CRITICAL RULES:
* Plan-flip discipline: every shippable unit = (Half 1) commit + push code, then (Half 2) flip
  `- [ ]` → `- [x] ✅ ... — <repo>@<sha>` in SAME AGENT TURN. NEVER batch flips. CLAUDE.md
  reinforced 2026-05-15 after slots 5+7 shipped 30+ items unflipped on 14 May → dashboard showed
  14.5% when real was 70%.
* External data wall: NEVER silently defer. File CREDENTIAL APPROVAL REQUEST in pings/slot_N.md;
  status BLOCKED-CREDENTIALS; scaffold + tests still ship.
* GCS backfill ≥1 week: operator approval ping + HOLD until [ack]. <1 week: pre-authorized.
* Conflict resolution: `bash unified-trading-pm/scripts/dev/slot-master-rebase.sh` from conflicted
  repo for auto-shape classification. paragraph-rewrite/code → STOP + 🟡 BLOCKED Q to slot 1.

Cron FF-pull every 15 min keeps your tree fresh while you work. GHA tab-mirror-to-ldr auto-mirrors
your tab pushes to LDR.

Now begin.
```

---

## Done-definition (2026-05-15 EOD)

- Slot 1: master plan refresh + inventory regen done; Phase 7.G sign-off coordination ledger updated.
- Slot 2: Helius live + Stream C 7 archetype docs landed + defi_catalogue ≥85% done.
- Slot 3: Kraken live wired + Solana DEX adapters expanded.
- Slot 4: 6-bucket re-evaluated + propagation chain Phase 3 close + sports universe audit.
- Slot 5: Phase 5 QG ratchet shipped + tradfi master refresh + Databento backfill operator-approved or queued.
- Slot 6: **manifest v8 Phase 7.G hits operator-sign-off queue for ≥3 of 5 asset_groups**; phase_3c VM re-run
  results landed.
- Slot 7: **SIT 3 scenarios shipped** + basefc items 1-5 closed + writegate α-vs-β verdict filed.
- Slot 8: B-015 smoke re-launched (or new diagnostic if features-onchain still failing).

**Daily inventory regenerator** (slot 1 main, EOD) should show **workspace cal-days remaining ≤ 370** (down from 518
this morning).
