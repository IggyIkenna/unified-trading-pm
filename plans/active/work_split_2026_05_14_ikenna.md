---
title: Ikenna's daily work-split — 2026-05-14 (Day-3 density-push, ~272 cal AI-days, pre-cutover stack)
type: coordination-doc
status: active
created: 2026-05-14
deadline: 2026-05-23 (live DeFi cutover)
horizon: ~9 calendar days (14 May → 23 May); ~272 cal AI-days across 8 implementer slots (200 baseline + 72 v2 extension)
companion_to: plans/active/work_split_2026_05_14_harsh.md
locked_by: live-defi-rollout
locked_since: 2026-05-14
---

# Ikenna's daily work-split — 2026-05-14

> **Cycle context**: Day-3 of the 2026-05-12 density-push cycle. Phase 1 freeze gate fires **tomorrow (2026-05-15)** —
> Harsh-side owns the freeze-gate close-out audit (their slot 6). Ikenna scope here is the **~50% of remaining May-23
> work that Harsh is NOT touching in his 14 May split** (~200 calibrated AI-days, 8 implementer slots × ~22-25 cal
> each). Slot 1 main is orchestration only, not counted in the 200.
>
> **Density target**: at the workspace-confirmed ~100-200 cal/side/day density pace this is ~1-2 calendar days of
> real work; the 9-day window to cutover is the calendar floor, not the AI-day floor. Slot stacks are deep so any
> slot closing early pulls from the in-stack reserve before requesting reassignment.
>
> **Non-overlap with Harsh today** (explicit drops): api_football Phase 3b/3c (Harsh slot 2), 117 UTL fixture sweep
> (Harsh slot 3), 2-of-17 strategy-service tests (Harsh slot 4), batch_live_symmetry entire (Harsh slots 5+8),
> Phase 1 freeze-gate readiness audit (Harsh slot 6), cross_asset Phase 6C + ICE US softs + TRADER_JOEV2 UI refs
> (Harsh slot 7), defi_recursive_borrow descope successor (Harsh slot 9).

---

## Hard rules baked into this split

1. **GCS backfill approval gate (codified here)**: any backfill that pulls **≥1 week of data** requires operator
   approval BEFORE the VM launch. Backfills of **<1 week** for testing / validation / smoke may run without approval.
   Slot owner posts a `pings/slot_N.md` entry _"BACKFILL APPROVAL REQUEST: <plan>, <date range>, <est rows>"_ and waits
   for operator `[ack]` before `gcloud compute instances create`. Applies to every asset_group.
2. **Singleton-locked + watchdog-registered launchers only** — every backfill VM uses a launcher under
   `deployment-service/scripts/vm/` with `VM_PREFIX_TO_BUCKET` entry. No fire-and-forget.
3. **Active event-stream verification** — STARTED within 60s + ≥1 progress event/hour + STOPPED at exit; SSH-tail is
   dev-only.
4. **Defi recursive borrow Phases 4-11**: **DESCOPE REVERSED** per operator direction 2026-05-14. "i want defi_recursive_borrow and recursive staking in 23rd may though even if not essential for defi i want it backtested coded up and tested ready to go live". Implementation PULLED INTO THIS SPLIT — see § "Day-3 operator direction: recursive_borrow scope-extension" at bottom.
5. **Wallet/Treasury Phase 2** (Copper / CEFFU integrations): CLIENT-SIDE, NOT our blocker. Config-only flip on
   `WalletProvisioningConfig.signing_surface` when client provisions credentials.

---

## Slot stack — 200 cal AI-days across 8 implementer slots

Slot 1 = main orchestrator (continuous; not counted in the 200). Stacks below are deep — slot owner ships top-down and
pulls in-stack reserve when each item closes.

| Slot | Theme                                                            | Cal AI-days |
| ---- | ---------------------------------------------------------------- | ----------- |
| 1    | Main orchestrator (continuous, uncounted)                        | —           |
| 2    | DeFi classification + catalogue + Polymarket subset              | ~24         |
| 3    | Perp venue adapters + Solana RPC + DEX/Drift expansion           | ~25         |
| 4    | Sports classifier + propagation chain + phantom apply-flips      | ~25         |
| 5    | TradFi Item 2 cascade + tradfi backfill prep + Solana C          | ~25         |
| 6    | Wallet/Treasury Phase 1 + DeFi alerts + custody wiring           | ~24         |
| 7    | Treasury rollup endpoint + Phase 3 audit + DART manual-trade     | ~25         |
| 8    | SHARD_AXIS_MATRIX drift + audit cleanup + ops verification       | ~25         |
| 9    | Mechanical (Cluster A sed) + governance + cron/ratchet sweep     | ~27         |
| **Subtotal** | (8 implementer slots, baseline)                          | **~200**    |
| **+ V2 ext** | (see § "V2 extension — +72 cal AI-days" below)          | **+72**     |
| **Total**    | (8 implementer slots, baseline + v2)                     | **~272**    |

---

### Slot 1 main — orchestration (continuous, uncounted)

1. Master plan refresh + `regenerate_active_plan_inventory.py` daily sweep (morning + EOD).
2. `_agent_pings.md` cross-side triage every ~5 min while operator active; per-slot pings polled.
3. `strategy_service_qg_step6_production_readiness_newly_exposed` triage (operator decision 3 — slot 1 owner).
4. **Phase 6.9 workspace QG flip-sweep** monitoring — Gate 4 fires once 6.6/6.7/6.8 land workspace-wide.
5. `governance_qg_automation_gaps_post_cutover` — codify the runbook execution-owner SSOT gaps surfaced this cycle.
6. Freeze-gate close monitoring + relay Harsh slot 6 findings to relevant Ikenna slot if mismatch surfaces.

---

### Slot 2 — DeFi classification + catalogue + Polymarket — ~24 cal AI-days

Plan-of-record fan-out: `defi_classifier_missing_catalog_crossref` (issue) + `defi_catalogue_chain_primitives_2026_05_10` + `wave2_polymarket_record_captured_from_counts_2026_05_09` + `basefc_validation_flip_2026_05_10` + `solana_defi_coverage_gaps` (successor plan B — Lido/Marinade/Jito LST).

1. **`defi_classifier_missing_catalog_crossref` Phase A** — wire instruments-service catalog `available_from` /
   `available_to` cross-ref into `_classify_defi` + `_classify_cefi` (per operator decision 6 — make classifier consult
   IS catalog dates). (refactor 0.4×, ~3 baseline = ~1.2 cal)
2. **Phase B re-attempt** — re-run Script 3, queue re-attempt VMs only for genuinely-failing classifications after
   crossref lands. (infra 0.8×, ~2 = 1.6 cal)
3. **`wave2_polymarket_record_captured_from_counts` Polymarket subset** — wire counts → `record_captured()` for
   Polymarket market-state shards. (research 1.2×, ~3 = 3.6 cal)
4. **`defi_catalogue_chain_primitives_2026_05_10`** — close out open todos: chain-primitive UAC schema additions +
   downstream MTDS/features wiring. (design 0.6×, ~5 = 3.0 cal)
5. **`solana_defi_coverage_gaps` successor plan B — Lido / Marinade / Jito LST** — design + first-phase ship. (design
   0.6×, ~4 = 2.4 cal)
6. **`basefc_validation_flip_2026_05_10`** — close out validation flip per plan body. (refactor 0.4×, ~3 = 1.2 cal)
7. **`cross_asset_group_catalogue_audit` Phase 6A DeFi half** — DeFi-specific catalogue parity audit (different from
   Harsh slot 7's 6C UI half). (research 1.2×, ~3 = 3.6 cal)
8. **`utl_qg_preexisting_failures_2026_05_14` P1** — diagnose-first per Findings Triage; fix code-side or test-side
   per contract reading. (research 1.2×, ~3 = 3.6 cal)
9. **Cluster D instruments-service test failures** (Phase 0 cluster D, instruments-service-half not yet flipped).
   (refactor 0.4×, ~2 = 0.8 cal)
10. **Reserve**: in-stack pickup for any new DeFi classification issues filed during the cycle.

Backfill flag: items 2 + 3 may need <1-week test backfills — OK without approval. ≥1 week → ping operator.

---

### Slot 3 — Perp venue adapters + Solana RPC + DEX/Drift — ~25 cal AI-days

Plan-of-record fan-out: `emerging_perp_venue_adapters_broken_2026_05_*` (P0) + `emerging_perp_adapters_diagnosed_2026_05_*` (P0) + `helius_solana_rpc_for_validation` (P1) + `solana_defi_coverage_gaps` (successor A) + `defi_master_2026_05_07` Drift/Jito subset.

1. **`emerging_perp_venue_adapters_broken` P0 root-cause fix** — adapter-level fixes for the broken-perp-venue list;
   each fix lands as separate commit. (research 1.2×, ~3 = 3.6 cal)
2. **`emerging_perp_adapters_diagnosed` P0** — write fix notes / diagnosis into adapter docstrings per Findings Triage
   "fix in code if you have context". (research 1.2×, ~2 = 2.4 cal)
3. **`helius_solana_rpc_for_validation` P1** — wire Helius into the Solana RPC validation path (replaces Infura/Alchemy
   for Solana per UAC `CHAIN_RPC_TEMPLATES`). (infra 0.8×, ~3 = 2.4 cal)
4. **`solana_defi_coverage_gaps` successor plan A** — Pyth Hermes batch + PythNet live integration design + first-phase
   ship. (design 0.6×, ~4 = 2.4 cal)
5. **DEX perp + venue data expansion** — pickup from yesterday's Harsh slot 10 close; extend to additional venues
   per `defi_master_2026_05_07` venue matrix. (infra 0.8×, ~5 = 4.0 cal)
6. **Drift JitoSOL+mSOL basis-pair build-out** — eligibility wiring for `carry_staked_basis` per archetype matrix.
   (design 0.6×, ~4 = 2.4 cal)
7. **Hyperliquid arb_price_dispersion eligibility check** — verify USDC-margin compatibility per archetype matrix.
   (research 1.2×, ~2 = 2.4 cal)
8. **Cluster D ml-inference test failures** (Phase 0 cluster D, ml-inference-half). (refactor 0.4×, ~2 = 0.8 cal)
9. **Aster + Bybit UTA eligibility verification for carry_staked_basis** — LST_AS_MARGIN per archetype matrix.
   (research 1.2×, ~3 = 3.6 cal)
10. **Reserve**: in-stack on Solana RPC ratelimit handling + DEX venue catch-up.

Backfill flag: item 3 + 5 + 6 — Solana validation backfills <1 week OK without approval.

---

### Slot 4 — Sports classifier + propagation chain + phantom apply-flips — ~25 cal AI-days

Plan-of-record fan-out: 3 sports classifier issue docs (sfi_footystats / player_values / weather) + `sports_classifier_extension_followup` (parent) + propagation chain Phase 3.1-3.N + `expected_unattempted_propagation_gap` P1 + sports/prediction phantom apply-flips + `api_football_minimal_flattening_removal_2026_05_07` + `sports_master_2026_05_07`.

1. **3 sports classifier gap issues** — sfi_footystats / player_values / weather classifications missing branches.
   (refactor 0.4×, ~3 = 1.2 cal)
2. **`sports_classifier_extension_followup` parent** — close out parent issue + cross-link the 3 child fixes.
   (refactor 0.4×, ~2 = 0.8 cal)
3. **Propagation chain Phase 3.1-3.N + Phase 4 + PART C** — push remaining propagation phases through workspace.
   (refactor 0.4×, ~6 = 2.4 cal)
4. **`expected_unattempted_propagation_gap` P1** — propagate `expected_unattempted` capture_status to remaining
   readers + manifest UI. (research 1.2×, ~3 = 3.6 cal)
5. **6-bucket provisioning** — sports/prediction bucket provisioning per `bucket_name_ssot_canonicalisation` env-aware
   matrix. Operator-approval needed only if backfill is part of this — provisioning alone = config + bucket-create
   only, no approval. (infra 0.8×, ~2 = 1.6 cal)
6. **Sports/prediction phantom apply-flips on VMs** — `reconcile_phantom_manifest_rows_all.py --apply-flips` on
   same-region GCE VM. (infra 0.8×, ~3 = 2.4 cal)
7. **Cluster D strategy-service test failures** (Phase 0 cluster D; different from Harsh slot 4's 2-of-17 — this is
   the cluster-level remainder). (refactor 0.4×, ~2 = 0.8 cal)
8. **`sports_master_2026_05_07` data_type universe coverage audit** — gather + cross-ref against
   `cross_asset_group_catalogue_audit`. (research 1.2×, ~4 = 4.8 cal)
9. **`api_football_minimal_flattening_removal_2026_05_07`** — close out flattening removal per plan body. (refactor
   0.4×, ~3 = 1.2 cal)
10. **`sports_retired_data_types_code_cleanup_2026_05_13` sports-half** — retire dead data_types from sports producer
    side. (refactor 0.4×, ~3 = 1.2 cal)
11. **`data_status_comprehensive_test_coverage_2026_05_07` sports-half** — write sports-grain tests for the
    drilldown-shard-atom alignment. (design 0.6×, ~4 = 2.4 cal)
12. **Reserve**: in-stack pickup on any sports classifier ambiguity surfaced from item 4.

Backfill flag: item 6 (phantom apply-flips) — reconciles existing manifest rows; not a backfill.

---

### Slot 5 — TradFi Item 2 cascade + tradfi backfill prep + Solana C — ~25 cal AI-days

Plan-of-record fan-out: `tradfi_canonical_futures_contract_hard_required_fields_2026_05_13` (TradFi Item 2 Phase 3-5) + `tradfi_master_2026_05_07` (master plan refresh) + tradfi 1-week test backfill + `solana_defi_coverage_gaps` (successor C).

1. **TradFi Item 2 Phase 3 migration script** — futures contract migration script (operator GREENLIT 2026-05-13).
   (refactor 0.4×, ~4 = 1.6 cal)
2. **TradFi Item 2 Phase 4 consumer cascade** — workspace-wide consumer migration (operator GREENLIT). (refactor
   0.4×, ~5 = 2.0 cal)
3. **TradFi Item 2 Phase 5 QG ratchet** — QG STEP enforcement banning legacy futures-contract shape (operator
   GREENLIT). (design 0.6×, ~3 = 1.8 cal)
4. **TradFi 1-week test backfill** (<7 days, AUTHORIZED — no operator approval needed per the hard rule above) — run
   on same-region GCE VM, verify sample parquets OHLC-populated + manifest captured rows match planned scope.
   (infra 0.8×, ~3 = 2.4 cal)
5. **`tradfi_master_2026_05_07` master plan refresh** — push remaining open todos workspace-wide. (research 1.2×,
   ~4 = 4.8 cal)
6. **`solana_defi_coverage_gaps` successor plan C** — Jito MEV / restaking integration design. (design 0.6×, ~4 =
   2.4 cal)
7. **`sports_retired_data_types_code_cleanup_2026_05_13` non-sports-half** — retire dead data_types from
   cross-cutting / UAC side (slot 4 owns the sports producer half — coordinate handshake). (refactor 0.4×, ~3 =
   1.2 cal)
8. **`tradfi_master_2026_05_07` venue + symbology coverage audit** — cross-ref against
   `cross_asset_group_catalogue_audit`. (research 1.2×, ~3 = 3.6 cal)
9. **TradFi venue calendar SSOT** — `MarketSession` scaffold (operator answered Yes 2026-05-13 — prefer real venue
   schedules where possible, time unconstrained). (design 0.6×, ~3 = 1.8 cal)
10. **CME/EUREX 1-week test backfill** — second tradfi venue smoke (<7 days, AUTHORIZED). (infra 0.8×, ~3 = 2.4 cal)
11. **Reserve**: in-stack pickup for tradfi QG enforcement gaps surfaced from item 3.

Backfill flag: items 4 + 10 are **<1-week test backfills — AUTHORIZED without operator approval**. Anything that
escalates to a full-history backfill MUST stop + ping operator.

---

### Slot 6 — Wallet/Treasury Phase 1 + DeFi alerts + custody wiring — ~24 cal AI-days

Plan-of-record fan-out: `wallet_treasury_post_cutover_custody_signing_2026_06_01.md` (Phase 1 pulled forward) + 4 DeFi alert codes + Cluster B execution-service lint + `api_keys_wallets_accounts_readiness_2026_05_10.md` Phase 8.D + custody adapter Cloud-KMS wiring + kill-switch + DART pickup.

1. **wallet_treasury_post_cutover Phase 1 Real HMAC withdrawal approval chain** (PULLED FORWARD to pre-May-15 per
   density-push assessment) — wire `WithdrawalApprovalSignature` (HMAC-SHA256) + 2-of-N multisig + Cloud-KMS signing
   + 8 unit tests. (infra 0.8×, ~3.2 = 2.6 cal)
2. **4 DeFi-specific alert codes** producer-side + alerting wiring per `alerting_service_live_rules_2026_05_07.md`.
   (design 0.6×, ~3 = 1.8 cal)
3. **Cluster B execution-service C901+N802+B008 lint sweep** — apply UAC carveout pattern from `UAC@ba49e70`.
   (refactor 0.4×, ~3 = 1.2 cal)
4. **`api_keys_wallets_accounts_readiness_2026_05_10` Phase 8.D pre-cutover gate items** — finalize gate checklist
   verification. (research 1.2×, ~3 = 3.6 cal)
5. **Kill-switch arming + manual-trade UX gate** — operator-only arming surface; build the UI gate that requires
   explicit operator action before live trading. (design 0.6×, ~3 = 1.8 cal)
6. **Custody adapter Cloud-KMS wiring smoke** — verify the `signing_surface` config flip path works against real
   Cloud-KMS endpoint (existing 10 CMKs, asia-northeast1). (infra 0.8×, ~2 = 1.6 cal)
7. **`alerting_runbook_and_operator_ux_post_cutover_2026_05_12` Ikenna-half** — push remaining operator UX items.
   (design 0.6×, ~3 = 1.8 cal)
8. **`audit_records_pb_1_2_3_pre_cutover_2026_05_13` Phase 1** — pre-cutover audit-records gate. (research 1.2×,
   ~3 = 3.6 cal)
9. **`available_at_lookahead_bias_completion_2026_05_08` sweep** — close remaining stamping helper consumers.
   (refactor 0.4×, ~4 = 1.6 cal)
10. **DART manual-trade gate UX final pass** — coordinate with slot 7's DART refactor; this slot owns the
    custody-side gate, slot 7 owns the operator UX surface. (design 0.6×, ~3 = 1.8 cal)
11. **Reserve**: in-stack pickup for any wallet/custody issues surfaced from item 1's HMAC chain.

Backfill flag: none for this slot (custody + alerting are config + code, not data).

---

### Slot 7 — Treasury rollup + Phase 3 audit + DART manual-trade — ~25 cal AI-days

Plan-of-record fan-out: `wallet_treasury_post_cutover_custody_signing_2026_06_01.md` Phase 3 + `dart_manual_trade_ux_refactor_2026_05_13.md` + `/api/treasury/rollup` endpoint + `audit_records_pb_1_2_3_pre_cutover_2026_05_13.md` + `client_reporting_pnl_attribution_mvp_2026_05_10.md` + Cluster B risk-and-exposure lint.

1. **wallet_treasury_post_cutover Phase 3 Audit log immutability** (PULLED FORWARD to pre-May-15) — GCS Object
   Versioning + 7-year retention lock + Cloud Audit Logs wiring + 4 compliance tests. (infra 0.8×, ~1.6 = 1.3 cal)
2. **`/api/treasury/rollup` deployment-api endpoint** — Slot 4 Phase 3.D handoff per
   `wallet_treasury_client_flow_2026_05_10.md` Q1 ack. (design 0.6×, ~3 = 1.8 cal)
3. **DART manual-trade UX refactor implementation half** (`dart_manual_trade_ux_refactor_2026_05_13.md`) —
   operator surface for live manual trade gate. (design 0.6×, ~4 = 2.4 cal)
4. **Cluster B risk-and-exposure-service lint sweep** — C901+N802+B008. (refactor 0.4×, ~2 = 0.8 cal)
5. **`audit_records_pb_1_2_3_pre_cutover_2026_05_13` Phase 2-3** — close pre-cutover audit gate items
   (slot 6 takes Phase 1; this slot takes 2+3). (research 1.2×, ~4 = 4.8 cal)
6. **`client_reporting_pnl_attribution_mvp_2026_05_10` Ikenna pickup** — push open todos workspace-wide. (design
   0.6×, ~5 = 3.0 cal)
7. **`context_fill_optimization_2026_05_14` Phase 1** — newly-created plan; review + first-phase implementation.
   (research 1.2×, ~3 = 3.6 cal)
8. **`data_status_drilldown_shard_atom_alignment_2026_05_07` finalize** — close out shard-atom alignment per the
   shard-granularity SSOT. (research 1.2×, ~3 = 3.6 cal)
9. **`compute_optimization_mock_data_2026_05_13` Ikenna-half** — reduce mock-data compute cost for CI runs. (design
   0.6×, ~3 = 1.8 cal)
10. **Reserve**: in-stack pickup for any DART operator UX issues from item 3 dogfooding.

Backfill flag: none for this slot (treasury rollup + audit are deployment + GCS config).

---

### Slot 8 — SHARD_AXIS_MATRIX drift + audit cleanup + ops verification — ~25 cal AI-days

Plan-of-record fan-out: `deployment_api_shard_axis_matrix_uac_drift_2026_05_14` (issue P1) + `solana_defi_coverage_gaps` (successor D) + `AUDIT_pre_may_8_cleanup_2026_05_13` + `classify_blank_reason_fixture_manifest_kwarg` ops verification + `data_status_comprehensive_test_coverage_2026_05_07` + Cluster B pnl-attribution lint + `codex_doc_currency_and_consolidation_post_cutover_2026_05_12`.

1. **`deployment_api_shard_axis_matrix_uac_drift_2026_05_14` P1** — fix 13 test failures from SHARD_AXIS_MATRIX
   drift; UAC carveouts already shipped, this is the deployment-api alignment. (refactor 0.4×, ~2 = 0.8 cal)
2. **`solana_defi_coverage_gaps` successor plan D** — Phoenix / Orca / Raydium DEX integration design + first-phase
   ship. (design 0.6×, ~4 = 2.4 cal)
3. **`AUDIT_pre_may_8_cleanup_2026_05_13`** — close out pre-May-8 cleanup audit items. (refactor 0.4×, ~3 = 1.2 cal)
4. **`classify_blank_reason_fixture_manifest_kwarg` ops verification** — tarball refresh + Script 3 re-run + verify
   `record_empty(reason=...)` end-to-end. (infra 0.8×, ~2 = 1.6 cal)
5. **Cluster B pnl-attribution-service lint sweep** — C901+N802+B008. (refactor 0.4×, ~2 = 0.8 cal)
6. **`data_status_comprehensive_test_coverage_2026_05_07` non-sports-half** — cross-cutting test coverage for the
   drilldown-shard-atom alignment (slot 4 owns sports-half). (design 0.6×, ~4 = 2.4 cal)
7. **`data_status_ui_phase_2f.md`** — close out Phase 2F UI items. (design 0.6×, ~3 = 1.8 cal)
8. **`codex_doc_currency_and_consolidation_post_cutover_2026_05_12` pickup** — refresh codex doc currency for any
   contract drift surfaced this cycle. (research 1.2×, ~3 = 3.6 cal)
9. **`codex_vs_citadel_infrastructure_audit_2026_05_10`** — close out infra audit items. (research 1.2×, ~3 =
   3.6 cal)
10. **`defi_simulation_realism_2026_05_10` audit-half** — review + close any items overlapping with our archetype
    matrix. (research 1.2×, ~3 = 3.6 cal)
11. **`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07`** — close out canonicalisation items.
    (design 0.6×, ~3 = 1.8 cal)
12. **Reserve**: in-stack pickup for any UAC drift surfaced from item 1's deployment-api alignment.

Backfill flag: item 4 (classify_blank_reason ops verification) — single-day re-run only, AUTHORIZED.

---

### Slot 9 — Mechanical (Cluster A sed) + governance + cron/ratchet sweep — ~27 cal AI-days

Plan-of-record fan-out: Phase 0 Cluster A `×→x sed + import-pattern fix` + `solana_defi_coverage_gaps` (successor E) + `honest_coverage_cron_vm_scheduling` + `mtf_intraday_micro_regime_policy` + `strategy_paper_vm_nautilus_trader_missing_dep` (resolved? re-verify) + `cross_asset_instruments_service_scope` triage + `bucket_name_ssot_canonicalisation_2026_05_10` + `cme_polymarket_arb_2026_05_08` + `arbitrage_price_dispersion_finalisation_2026_05_09` (this slot's biggest item).

1. **Cluster A ×→x sed + import-pattern fix** (mechanical, ~0.5d). (refactor 0.4×, ~0.5 = 0.2 cal)
2. **`solana_defi_coverage_gaps` successor plan E** — Kamino / Marinade Native integration design + first-phase ship.
   (design 0.6×, ~4 = 2.4 cal)
3. **`honest_coverage_cron_vm_scheduling`** — cron VM for cross-cutting honest-coverage rescan per Runbook Execution
   Owner SSOT. (infra 0.8×, ~3 = 2.4 cal)
4. **`mtf_intraday_micro_regime_policy`** — 2 dict entries (small). (design 0.6×, ~1 = 0.6 cal)
5. **`strategy_paper_vm_nautilus_trader_missing_dep`** — re-verify Harsh's resolved status `7beb103d`; if still
   missing, add pip dep + retest. (refactor 0.4×, ~0.5 = 0.2 cal)
6. **`cross_asset_instruments_service_scope` triage** — instruments-service scope decision for cross_asset symbols.
   (research 1.2×, ~3 = 3.6 cal)
7. **`bucket_name_ssot_canonicalisation_2026_05_10` workspace flip** — remaining call-site sweep + QG ratchet
   enforcement. (refactor 0.4×, ~4 = 1.6 cal)
8. **`cme_polymarket_arb_2026_05_08`** — close out plan body. (design 0.6×, ~4 = 2.4 cal)
9. **`arbitrage_price_dispersion_finalisation_2026_05_09`** — push remaining finalisation items. (design 0.6×,
   ~6 = 3.6 cal)
10. **`code_freeze_migrate_backfill_sequencing_2026_05_10` audit** — close out sequencing items. (research 1.2×,
    ~3 = 3.6 cal)
11. **Phase 6.9 workspace QG flip-sweep** — bulk flip across the remaining services post-6.6/6.7/6.8 land. (refactor
    0.4×, ~6 = 2.4 cal)
12. **`governance_qg_automation_gaps_post_cutover` codification** — pair with slot 1 main on the SSOT writeup.
    (design 0.6×, ~5 = 3.0 cal)
13. **Reserve**: in-stack pickup for any sed-fallout surfaced from item 1.

Backfill flag: item 3 (cron VM scheduling) — defines the cron, doesn't trigger a backfill on launch. Production cron
runs are themselves bounded jobs, not backfills.

---

## Cross-slot handshakes today

- **Slot 4 ↔ Slot 5** on `sports_retired_data_types_code_cleanup`: slot 4 owns producer-side, slot 5 owns
  cross-cutting/UAC side. Coordinate via `_agent_pings.md`.
- **Slot 6 ↔ Slot 7** on wallet/treasury: slot 6 = Phase 1 HMAC chain, slot 7 = Phase 3 audit immutability +
  treasury rollup; both touch deployment-api so push in serialised order (slot 6 first, slot 7 rebases).
- **Slot 6 ↔ Slot 7** on DART: slot 6 = custody-side gate, slot 7 = operator UX surface. Different files; parallel.
- **Slot 4 ↔ Slot 8** on `data_status_comprehensive_test_coverage`: slot 4 sports-half, slot 8 non-sports-half.
  Parallel; no overlap.
- **Slot 2 ↔ Slot 7** on `cross_asset_group_catalogue_audit`: slot 2 = Phase 6A DeFi half, **Harsh slot 7** = Phase 6C
  UI half. Both independent of each other.

## Cross-side handshakes (Ikenna ↔ Harsh)

- **Ikenna slot 2 Phase A/B** ↔ Harsh slot 6 freeze-gate audit: if Harsh slot 6 surfaces a freeze-gate item that
  depends on defi classifier crossref, slot 2 owner is paged via `_agent_pings.md`.
- **Ikenna slot 6+7 wallet_treasury Phase 1+3** (pulled forward to pre-May-15) is independent of Harsh today;
  ack-only.
- **batch_live_symmetry** entirely Harsh slots 5+8; Ikenna does NOT touch. If Harsh files an Ikenna-touching UAC
  ratchet, slot 8 owner picks up via _agent_pings.md.

---

## Spawn prompt (Model B — one spawn per slot)

```text
You are slot N (Ikenna side). Do this in order, nothing else until done:

1. Read unified-trading-pm/ikenna_orchestrator/AGENT_ONBOARDING.md (git discipline, LDR-alignment HARD RULE, fetch-first
   HARD RULE, pre-commit check, sub-agent rules, GCS backfill approval gate).
2. Read unified-trading-pm/plans/active/work_split_2026_05_14_ikenna.md § "Slot N" for your full task stack.
3. Read your plan-of-record (named in your slot section) — scan open `- [ ]` todos for your phase.
4. Append boot ack to unified-trading-pm/ikenna_orchestrator/pings/slot_N.md using `date -u` for timestamp, then start
   work.

GCS backfill rule: if any item triggers a backfill of ≥1 week of data, STOP and ping operator via slot_N.md before
launching the VM. Backfills of <1 week for testing / validation / smoke are pre-authorized — go ahead.

**Plan-flip cadence (HARD RULE — re-emphasized because this is the #1 source of wasted reallocation)**:
every time you ship a shippable unit you MUST do BOTH halves in the same logical unit, NOT batched at session end:

  - **Half 1**: commit + PUSH (`git push origin HEAD:live-defi-rollout`). Pushed = real. Local-only ≠ shipped.
  - **Half 2**: in the plan-of-record named for your item, flip the relevant `- [ ]` → `- [x] (commit-sha + brief
    evidence)`. Commit the flip with `docs(plans):` prefix. PUSH it. Only AFTER both halves land do you start the
    next item.

A flipped checkbox is the orchestrator's signal that the item is done — without the flip, the next reallocation
sweep may re-dispatch the same item to another slot. Every item in your stack above lives in a named plan-of-record;
find the `- [ ]` line in that plan that matches your item and flip it.

End-of-session: write **Half 3** — `## Deferred work after 2026-05-14 session` table in each touched plan listing
every item's status (todo / done / blocked / deferred) so the next agent doesn't scan 1000 lines to figure out where
you left off.

Ship top-down through the slot stack; when an item closes, pull from the in-stack reserve before requesting
reassignment.
```

---

## Done-definition (cycle end ≤ 2026-05-23)

Per slot: every top-level numbered item shipped as a `- [x]` checkbox in its plan-of-record with commit-sha
evidence, OR explicitly annotated `**DEFERRED**` with successor plan named per Capture Discoveries As Plan Todos
HARD RULE. Slots running ahead of pace pull from the in-stack reserve.

**Cycle gate**: all 200 cal AI-days shipped or annotated by 2026-05-23 cutover. Slots are NOT held in reserve for
density-push absorption — every slot has a deep stack.

---

## Deferred / not-in-scope this cycle

- AWS migration (`aws_migration_defi_first_2026_05_07.md`) — DEFERRED past 2026-05-23 per 2026-05-13 operator
  direction.
- Copper / CEFFU integrations — CLIENT-SIDE, NOT our blocker (config-only flip when client provisions).
- Fireblocks institutional custody — June-15+ scope, not this cycle.
- Any GCS backfill ≥1 week without explicit operator approval ping in slot_N.md.

---

## V2 extension — +72 cal AI-days (drives workspace remaining toward ~200)

Pulled from top remaining plans in the inventory dashboard (regenerated 2026-05-14 12:14 UTC, 580 cal total, 77
plans). Each slot picks up its v2 items AFTER its main stack lands; this is overflow, not replacement.

| Slot | V2 item                                                                                                   | Plan                                                                  | Cal |
| ---- | --------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- | --- |
| 2    | **`defi_catalogue_chain_primitives_2026_05_10` push** — remaining 21 open todos (currently 47/68, 63.5 cal left); split into 2-3 batches and ship | `defi_catalogue_chain_primitives_2026_05_10.md`                       | +9  |
| 3    | **`live_pipeline_mtds_mdps_features_2026_05_08` Ikenna-half** (15.0 cal total; instruments_live_master May-23 deadline) — DeFi instrument live-pipeline activation | `live_pipeline_mtds_mdps_features_2026_05_08.md`                      | +9  |
| 4    | **`topology_qgroup_gap_closure_2026_05_09` (9.6 cal, May-23)** + **`simulation_scenarios_topology_price_shocks_2026_05_09` sports-half subset** | `topology_qgroup_gap_closure_2026_05_09.md` + topology shocks         | +9  |
| 5    | **`code_freeze_migrate_backfill_sequencing_2026_05_10` cross-cutting subset** — pull TradFi + cross-asset-group sequencing items (plan is 123.5 cal total; Ikenna takes the cross-cutting cap of ~9, rest stays Harsh-side cefi_master) | `code_freeze_migrate_backfill_sequencing_2026_05_10.md`               | +9  |
| 6    | **`api_keys_wallets_accounts_readiness_2026_05_10` more Phase 8 items** (40.0 cal left, 33/87, May-23) + **`alerting_service_live_rules_2026_05_07` close** (4.5 cal, 43/65, May-23) | api_keys_wallets + alerting_service_live_rules                        | +9  |
| 7    | **`cross_cutting_may_23_deliverables_2026_05_08` Ikenna-half** (13.4 cal, 17/30) + **`mtds_per_instrument_download_api_2026_04_24`** (3.3 cal, 6/19) + **`mdps_streaming_and_backpressure_2026_05_07`** (3.0 cal, 0/7) | 3-plan parallel: cross_cutting deliverables + mtds per-instrument + mdps streaming | +9 |
| 8    | **`deployment_and_qg_strategy_implementation_2026_05_13`** (12.3 cal, 20/52) + **`hard_schema_enforcement_2026_05_08`** (4.8 cal) + **`gcs_migration_bundle_pipeline_mode_2026_05_08`** (4.8 cal, May-15 deadline) | deployment_and_qg + hard_schema_enforcement + gcs_migration_bundle    | +9  |
| 9    | **`writegate_honest_coverage_endtoend_2026_05_06` Phase 6.9 expanded scope** (12.6 cal, 117/246) + **`expected_universe_v2_design_2026_05_08`** (3.6 cal) + **`deploy_missing_auto_launch_2026_05_07` close** (4.1 cal, 6/14) | writegate Phase 6.9 + expected_universe_v2 + deploy_missing_auto_launch | +9  |
| **Total V2** |                                                                                                | (8 implementer slots × +9)                                            | **+72** |

**Note on `code_freeze_migrate_backfill_sequencing_2026_05_10` (slot 5 v2)**: this plan is 123.5 cal total
and owned by cefi_master (Harsh-side). Ikenna takes only the **cross-cutting subset** (~9 cal) — TradFi-side migration
sequencing items + cross-asset bucket-name SSOT items that overlap with Ikenna slot 5+9's existing themes. The bulk
(~115 cal) stays Harsh-side for 15-22 May absorption.

**Note on `aws_migration_defi_first_2026_05_07`** (28.4 cal in dashboard): DEFERRED past 2026-05-23 per operator
direction; NOT pulled into this v2 extension.

**Note on `defi_recursive_borrow_archetypes_2026_05_10`** (38.9 cal): **DESCOPE REVERSED 2026-05-14** — Phases 4-11 pulled into May-23 scope per operator. Assigned: Phases 4+5+12 → Slot 2; Phase 6 → Slot 3; Phases 7+8 → Slot 6. See § "Day-3 operator direction: recursive_borrow scope-extension" below. `defi_recursive_borrow_archetypes_post_cutover_2026_06_01` (24.0 cal): scope-narrowed to only genuine post-cutover items — Phases 4-13 are back in May-23 scope.

**Note on `batch_live_symmetry_2026_05_10`** (20.6 cal): Harsh-side today (slots 5+8); NOT pulled.

**Note on `simulation_scenarios_post_cutover_2026_06_01`** (15.2 cal): post-cutover target 2026-07-15; NOT pulled.

**Note on `promote_workflow_post_cutover_ui_pipeline_2026_05_10`** (20.0 cal): deadline 2026-07-04 post-cutover; NOT
pulled.

---

## Math — burn vs workspace remaining

| Source | Cal AI-days |
| --- | --- |
| Workspace-wide remaining (auto-inventory 2026-05-14 12:14 UTC, 77 plans) | **580** |
| Ikenna 14 May split baseline (200) + v2 extension (72) + recursive_borrow reversal (~22) | −294 |
| Harsh 14 May split (today closeout only — 8 days remain 15-23 May for him to absorb the rest) | −8 |
| **Remaining workspace cal AI-days after both 14 May splits land** | **~278** |

Note: Net burn against dashboard is closer to ~265 (some items are NEW work not yet checkboxed). Realistic remaining ≈ **~300 cal AI-days** for Harsh to absorb across 15-23 May (~37 cal/day × 8 days = comfortable at density-push pace).

---

## Day-3 operator direction: recursive_borrow scope-extension (2026-05-14)

**Operator direction 2026-05-14**: "i want defi_recursive_borrow and recursive staking in 23rd may though even if not essential for defi i want it backtested coded up and tested ready to go live". Descope reversed.

**Slot assignments** (Phases 4-11, code+test+backtest READY-TO-GO-LIVE, live toggle OFF at cutover):

| Phases | Slot | Rationale |
| --- | --- | --- |
| Phase 4 (Solidity `RecursiveLeverageReceiver.sol` extending `FlashLoanReceiver.sol`) + Phase 5 (`RecursiveLoopOrchestrator` in execution-service) + Phase 12 (backtest harness e2e — both archetypes on testnet) | **Slot 2** (DeFi classification + catalogue) | Core DeFi implementation slot |
| Phase 6 (Hyperliquid LIVE perp connector — EIP-712 signing + REST POST `/exchange` + WS `user_events`) | **Slot 3** (Perp venue adapters + DEX/Drift) | Phase 6 is a perp adapter — natural fit with Slot 3's theme |
| Phase 7 (`PerpHedgeSizer` — `_HYPERLIQUID_RULES` $500k cap pre-trade check) + Phase 8 (`HealthFactorMonitor` + `LiquidationProximityCircuit` alerts) | **Slot 6** (Wallet/Treasury + DeFi alerts + custody) | Health monitors + position alerts fit Slot 6's DeFi alert theme |

**Critical prerequisite in Slot 2's existing theme**: `CARRY_RECURSIVE_BORROW_LENDING_ONLY` + `CARRY_RECURSIVE_BORROW_PERP_HEDGED` enum values ALREADY in UAC `internal/architecture_v2/enums.py`. `ARCHETYPE_CONFIG_SEED` ALREADY has both keys. Missing: `_ARCHETYPE_ENGINE_MAP` in `strategy-service/engine/strategies/v2/factory.py:63` lacks both entries — Slot 2 adds these before Phase 12 backtest.

**Defi_catalogue dependency**: Phase 3 lending-indices fix (already in Slot 2's existing scope) is required for Family 2 backtest accuracy. Not a hard blocker for Phases 4-8 coding.

**Harsh slot 9**: lightweight ack + plan-body verification + cross-ping only (~0.5 cal research). All implementation Ikenna-side.

---

## Open questions

(None at draft time. Will populate as slot work progresses; route to `_agent_pings.md` if cross-side, or
slot_N.md if intra-side.)
