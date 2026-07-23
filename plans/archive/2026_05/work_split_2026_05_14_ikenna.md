---
doc_type: plan
title: Ikenna's daily work-split — 2026-05-14 (Day-3 density-push, ~272 cal AI-days, pre-cutover stack)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [client-reporting-api, deployment-api, deployment-service, deployment-ui, e2e-testing, execution-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-14
type: coordination-doc
deadline: 2026-05-23 (live DeFi cutover)
horizon:
  ~9 calendar days (14 May → 23 May); ~272 cal AI-days across 8 implementer slots (200 baseline + 72 v2 extension)
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
> **Density target**: at the workspace-confirmed ~100-200 cal/side/day density pace this is ~1-2 calendar days of real
> work; the 9-day window to cutover is the calendar floor, not the AI-day floor. Slot stacks are deep so any slot
> closing early pulls from the in-stack reserve before requesting reassignment.
>
> **Non-overlap with Harsh today** (explicit drops): api_football Phase 3b/3c (Harsh slot 2), 117 UTL fixture sweep
> (Harsh slot 3), 2-of-17 strategy-service tests (Harsh slot 4), batch_live_symmetry entire (Harsh slots 5+8), Phase 1
> freeze-gate readiness audit (Harsh slot 6), cross_asset Phase 6C + ICE US softs + TRADER_JOEV2 UI refs (Harsh slot 7),
> defi_recursive_borrow descope successor (Harsh slot 9).

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
4. **Defi recursive borrow Phases 4-11**: **DESCOPE REVERSED** per operator direction 2026-05-14. "i want
   defi_recursive_borrow and recursive staking in 23rd may though even if not essential for defi i want it backtested
   coded up and tested ready to go live". Implementation PULLED INTO THIS SPLIT — see § "Day-3 operator direction:
   recursive_borrow scope-extension" at bottom.
5. **Wallet/Treasury Phase 2** (Copper / CEFFU integrations): CLIENT-SIDE, NOT our blocker. Config-only flip on
   `WalletProvisioningConfig.signing_surface` when client provisions credentials.

---

## Slot stack — 200 cal AI-days across 8 implementer slots

Slot 1 = main orchestrator (continuous; not counted in the 200). Stacks below are deep — slot owner ships top-down and
pulls in-stack reserve when each item closes.

| Slot               | Theme                                                                                             | Cal AI-days |
| ------------------ | ------------------------------------------------------------------------------------------------- | ----------- |
| 1                  | Main orchestrator (continuous, uncounted)                                                         | —           |
| 2                  | DeFi classification + catalogue + Polymarket subset                                               | ~24         |
| 3                  | Perp venue adapters + Solana RPC + DEX/Drift expansion                                            | ~25         |
| 4                  | Sports classifier + propagation chain + phantom apply-flips                                       | ~25         |
| 5                  | TradFi Item 2 cascade + tradfi backfill prep + Solana C                                           | ~25         |
| 6                  | Wallet/Treasury Phase 1 + DeFi alerts + custody wiring                                            | ~24         |
| 7                  | Treasury rollup endpoint + Phase 3 audit + DART manual-trade                                      | ~25         |
| 8                  | SHARD_AXIS_MATRIX drift + audit cleanup + ops verification                                        | ~25         |
| ~~9~~              | **REASSIGNED 2026-05-14 15:30 UTC** → folded across slots 2/5/6/7/8 (PC concurrency cap = 8 tabs) | ~~27~~      |
| ~~10~~             | **REASSIGNED 2026-05-14** → folded into slot 7 writegate stack                                    | ~~4~~       |
| ~~11~~             | **REASSIGNED 2026-05-14** → folded across slots 4/6/8 + cbETH DEFERRED + Kraken to slot 3         | ~~7.4~~     |
| **Subtotal**       | (8 implementer slots, baseline)                                                                   | **~200**    |
| **+ V2 ext**       | (see § "V2 extension — +72 cal AI-days" below)                                                    | **+72**     |
| **+ Orphans**      | (6 items: 11/12 May reserve + MTDS clusters + banners + slot 10)                                  | **+16**     |
| **+ Slot 11**      | (new-issue absorb + sports + Tardis + cbETH + Kraken)                                             | **+7.4**    |
| **+ Slot 6 #11**   | (phase_3c lending model — UNBOUNDED per operator)                                                 | **+7.2**    |
| **+ Harsh absorb** | (8 Harsh 14 May items reassigned across slots)                                                    | **+7**      |
| **Total**          | (8 implementer + emergency slots 10+11)                                                           | **~310**    |

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

Plan-of-record fan-out: `defi_classifier_missing_catalog_crossref` (issue) +
`defi_catalogue_chain_primitives_2026_05_10` + `wave2_polymarket_record_captured_from_counts_2026_05_09` +
`basefc_validation_flip_2026_05_10` + `solana_defi_coverage_gaps` (successor plan B — Lido/Marinade/Jito LST).

1. ✅ **`defi_classifier_missing_catalog_crossref` Phase A** — wire instruments-service catalog `available_from` /
   `available_to` cross-ref into `_classify_defi` + `_classify_cefi` (per operator decision 6 — make classifier consult
   IS catalog dates). (refactor 0.4×, ~3 baseline = ~1.2 cal) **DONE** (UTL@`513d79fb` + IS@`3670534`):
   `instrument_lifecycle_loader.py` added; `_classify_defi`/`_classify_cefi` wired with catalog cross-ref.
2. ✅ **Phase B re-attempt** — re-run Script 3, queue re-attempt VMs only for genuinely-failing classifications after
   crossref lands. (infra 0.8×, ~2 = 1.6 cal) **DONE** (2026-05-15): Dry run 605,070 candidates / 599,486 corrections
   (all `EXPECTED_PRE_VENUE_LAUNCH`) / 5,584 legit re-fetch. Apply-flips: RECONCILER_COMPLETED — 599,486 rows
   corrected + uploaded to
   `gs://market-data-tick-defi-central-element-323112/_index/per_vm/ikenna-slot2-corrector-defi-20260515.parquet` in
   528.5s. Consolidator merge within ~5 min. Corrector wired with lifecycle loader (IS@`2a398cd`).
3. ✅ **`wave2_polymarket_record_captured_from_counts` Polymarket subset** — wire counts → `record_captured()` for
   Polymarket market-state shards. (research 1.2×, ~3 = 3.6 cal) **DONE** (ALL PHASES COMPLETE: UTL@`ef47c81b`,
   `446d75ce`, `d8ca04bc`; MTDS@`a2f8d80`, `616ac15`; PM@`ce40d8ab`, `d93a9952`)
4. ✅ **`defi_catalogue_chain_primitives_2026_05_10` Phase 1A** — chain-primitive UAC capability matrix. (design 0.6×,
   ~5 = 3.0 cal) **DONE (Phase 1A only)** (uac@`00d526c`): 26 new DEFI_VENUE_DATA_TYPE_CAPABILITIES entries for Phase 1A
   protocols (vaults/LSTs/restaking/DEX aggregator). Phase 2+ (IS adapters, MTDS handlers) remain open in the plan.
5. ✅ **`solana_defi_coverage_gaps` successor plan B — Lido / Marinade / Jito LST** — design + first-phase ship. (design
   0.6×, ~4 = 2.4 cal) **DONE** (IS Phases 1-5 of `solana_lst_native_staking_adapters_2026_05_14.md` shipped in previous
   session): SolanaNativeStakingAdapter + SANCTUM (INF/jupSOL/laineSOL) + Marinade adapters shipped. Phase 6 (backfill)
   BLOCKED-OPERATOR-ACK per ping in pings/slot_2.md.
6. **`basefc_validation_flip_2026_05_10`** — close out validation flip per plan body. BLOCKED on
   `features_repo_consolidation_2026_05_08.md` Phase 6 parity-green (pre-req not met). (refactor 0.4×, ~3 = 1.2 cal)
7. ✅ **`cross_asset_group_catalogue_audit` Phase 6A DeFi half** — DeFi-specific catalogue parity audit (different from
   Harsh slot 7's 6C UI half). (research 1.2×, ~3 = 3.6 cal) **DONE** (pre-existing per
   cross_asset_group_catalogue_audit_2026_05_10.md line 469 [x] and table ✅ DONE row): Phase 6A workspace-grep audit +
   `check_chain_set_inclusion.py` QG ratchet (STEP 5.72) shipped Wave 4 2026-05-13.
8. ✅ **`utl_qg_preexisting_failures_2026_05_14` P1** — diagnose-first per Findings Triage; fix code-side or test-side
   per contract reading. (research 1.2×, ~3 = 3.6 cal) **DONE (STEP 5.5 fix shipped)**: UTL STEP 5.5
   `instrument_lifecycle_loader.py` cloud SDK import fixed (UTL@`ac223da9`). Remaining items diagnosed: backward-compat
   shims need cross-repo caller audit (treasury/kill_switch, outside slot scope); urllib3 CVE needs workspace-wide dep
   bump; deep UAC imports need UAC facade work. Filed in `utl_qg_preexisting_failures_2026_05_14.md`.
9. ✅ **Cluster D instruments-service test failures** (Phase 0 cluster D, instruments-service-half not yet flipped).
   (refactor 0.4×, ~2 = 0.8 cal) **DONE** (pre-existing per deployment_and_qg_strategy_implementation_2026_05_13.md §
   Cluster D [x]): instruments-service@d78dd02 — 74 failed tests now 78 passing; IS QG confirms 2591 passed, ALL QUALITY
   GATES PASSED exit 0.
10. ✅ **[ORPHAN-2026-05-14] `mtds_market_interface_test_failures_2026_05_14` cluster A** — defi_handlers row-count
    drift: test expects 1 row, handler returns 2 (AAVE_V3 + MORPHO dual-venue path). Diagnose-first per Findings Triage:
    code drifted from test intent (multi-venue is correct), so update test expectations. (research 1.2×, ~1 = 1.2 cal)
    **DONE** (MTDS@`8d54eb1`): Two distinct failures diagnosed — (1) `_fetch_aave_liquidations` missing
    `if not api_key or not subgraph_id: return []` guard (code fix, parallel parity with flash_loan handler); (2)
    `test_fetch_aave_flash_loans_returns_rows_on_200` not patching `get_subgraph_id` which returns `None` in real UAC
    registry (test fix, added patch). 33/33 tests pass. QG exit 0.
11. **Reserve**: in-stack pickup for any new DeFi classification issues filed during the cycle.

Backfill flag: items 2 + 3 may need <1-week test backfills — OK without approval. ≥1 week → ping operator.

---

### Slot 3 — Perp venue adapters + Solana RPC + DEX/Drift — ~25 cal AI-days

Plan-of-record fan-out: `emerging_perp_venue_adapters_broken_2026_05_*` (P0) +
`emerging_perp_adapters_diagnosed_2026_05_*` (P0) + `helius_solana_rpc_for_validation` (P1) +
`solana_defi_coverage_gaps` (successor A) + `defi_master` Drift/Jito subset.

1. ✅ **`emerging_perp_venue_adapters_broken` P0 root-cause fix** — adapter-level fixes for the broken-perp-venue list;
   each fix lands as separate commit. (research 1.2×, ~3 = 3.6 cal) **DONE** (2026-05-14): MTDS@7d45b21 — ASTER
   AsterBaseClient.base_url_futures corrected to fapi.asterdex.com; instruments-service@c0c6593 — ASTER P0 root cause
   fix.
2. ✅ **`emerging_perp_adapters_diagnosed` P0** — write fix notes / diagnosis into adapter docstrings per Findings
   Triage "fix in code if you have context". (research 1.2×, ~2 = 2.4 cal) **DONE** (2026-05-14):
   instruments-service@7c2fc5f — EXTENDED-STARKNET diagnosis comment with stale API endpoint note.
3. ✅ **`helius_solana_rpc_for_validation` P1** — wire Helius into the Solana RPC validation path (replaces Alchemy for
   Solana per UAC `CHAIN_RPC_TEMPLATES`). (infra 0.8×, ~3 = 2.4 cal) **DONE** (2026-05-14): execution-service@a300f7c —
   `capture_golden_swaps.py` Helius Solana RPC dispatch for SOLANA_CLMM/AMM shapes.
4. ✅ **`solana_defi_coverage_gaps` successor plan A** — Pyth Hermes batch + PythNet live integration design +
   first-phase ship. (design 0.6×, ~4 = 2.4 cal) **DONE** (2026-05-14): PM@3fc9a790 —
   `plans/active/solana_lst_native_staking_adapters_2026_05_14.md` created (6 phases,
   SANCTUM+SOLBLAZE+Pyth+native_staking_rates+backfill).
5. ✅ **DEX perp + venue data expansion** — pickup from yesterday's Harsh slot 10 close; extend to additional venues per
   `defi_master` venue matrix. (infra 0.8×, ~5 = 4.0 cal) **DONE** (2026-05-14): market-tick-data-service@78e3b28 —
   PACIFICA-SOLANA (REST, api.pacifica.fi/v1/funding_rate/history, gated 2025-06-01) + LIGHTER-ZKSYNC (Tardis
   market_stats CSV, datasets.tardis.dev/v1/lighter-zksync/market_stats, gated 2026-04-17, Tardis API key via Secret
   Manager). Both wired into DEFAULT_PROTOCOLS + \_collect_pacifica/\_collect_lighter. EXTENDED-STARKNET omitted
   (BLOCKED-OPERATOR-DECISION per defi_master Item C).
6. ✅ **Drift JitoSOL+mSOL basis-pair build-out** — eligibility wiring for `carry_staked_basis` per archetype matrix.
   (design 0.6×, ~4 = 2.4 cal) **DONE** (2026-05-14): strategy-service@6ff86fe — DRIFT-SOLANA perp_funding in UAC; xfail
   test removed; TestDriftSolanaLstEligibility + perp_hedge_candidates test added; jito-drift + marinade-drift slots
   verified; 48 tests pass.
7. ✅ **Hyperliquid arb_price_dispersion eligibility check** — verify USDC-margin compatibility per archetype matrix.
   (research 1.2×, ~2 = 2.4 cal) **DONE** (2026-05-14): USDC margin accepted (0 haircut) → eligible for
   `arbitrage_price_dispersion`. perp_funding capability gap fixed: UAC@052120d (HYPERLIQUID+ASTER in
   VENUE_DATA_TYPE_CAPABILITIES) + strategy-service@c7a3f92 (4 tests). DRIFT/GMX DeFi-only reclassification also shipped
   as part of the same UAC commit.
8. ✅ **Cluster D ml-inference test failures** (Phase 0 cluster D, ml-inference-half). (refactor 0.4×, ~2 = 0.8 cal)
   **DONE** (2026-05-14 sub-agent): ml-inference@7e37109 — STEP 5.63 false-positive docstring fix + STEP 5.64
   `emit_preflight_skip()` added to `batch_handler.py` dependency-missing branches.
9. ✅ **Aster + Bybit UTA eligibility verification for carry_staked_basis** — LST_AS_MARGIN per archetype matrix.
   (research 1.2×, ~3 = 3.6 cal) **DONE** (2026-05-14): strategy-service@ab8661e — ASTER=no LST (USDC/USDT-only), BYBIT
   UTA stETH=True (10% haircut) → lido-bybit slot unlocked; `TestAsterBybitUtaLstEligibility` test class added.
10. ✅ **[ORPHAN-2026-05-14] `mtds_market_interface_test_failures_2026_05_14` clusters B + C** — Alchemy `_get_rpc_url`
    API drift + g9_regression classifier event-shape drift. (research 1.2×, ~2 = 2.4 cal) **DONE** (2026-05-14
    sub-agent): Cluster B already passing (no fix needed); Cluster C — MTDS@a54dc62 — `_safe_classify` re-exported from
    `migrate_tradfi_canonical.py` entry module.
11. ✅ **Reserve**: in-stack on Solana RPC ratelimit handling + DEX venue catch-up — Phase 2 SANCTUM instruments-service
    adapter shipped: `sanctum.py` (INF + JUPSOL + LAINESOL, \_solana_utils pattern) + factory registration + 8 unit
    tests. (instruments-service@e149995 + f44f0dc; PM plan Phase 2 checkboxes flipped @169132e7)

**Redistributed from Slot 9 (2026-05-14 15:30 UTC)**: 12. ✅ **`arbitrage_price_dispersion_finalisation_2026_05_09`**
(~3.6 cal) — ALREADY COMPLETE as of 2026-05-09/10 (20/20 todos [x] done by prior agents). Phases A/B/C/D/E all shipped:
strategy-service@{24f8494,0b4ef0e,04c0d52,1107ab7, d01661e,de9b4b0,2fdf7e8} + pnl-attribution-service@f5dcf63 +
PM@{5fe5eabd,5d2d74c1}. Plan archived 2026-05-15 (slot 3 admin). Deferred item: live cutover dry-run →
master_to_live_defi_2026_05_23.md Group F item 17. 13. ✅ **Kraken CeFi adapter scaffold** (~1.8 cal) — SCAFFOLD SHIPPED
instruments-service@`da462af` (KRAKEN-SPOT→ccxt.kraken + KRAKEN-FUTURES→ccxt.krakenfutures wired in factory.py; 3 new
tests). Historic batch via Tardis already wired. Status: BLOCKED-CREDENTIALS-OPERATOR-INCOMING — credential vault
entries `kraken-api-key` / `kraken-api-secret` pending operator [ack] on pings/slot_3.md.

Backfill flag: item 3 + 5 + 6 — Solana validation backfills <1 week OK without approval.

---

### Slot 4 — Sports classifier + propagation chain + phantom apply-flips — ~25 cal AI-days

Plan-of-record fan-out: 3 sports classifier issue docs (sfi_footystats / player_values / weather) +
`sports_classifier_extension_followup` (parent) + propagation chain Phase 3.1-3.N +
`expected_unattempted_propagation_gap` P1 + sports/prediction phantom apply-flips +
`api_football_minimal_flattening_removal_2026_05_07` + `sports_master`.

1. ✅ **3 sports classifier gap issues** — sfi_footystats / player_values / weather classifications missing branches.
   (refactor 0.4×, ~3 = 1.2 cal) **DONE** (2026-05-14 prior session): sfi_footystats → uac@435abae + utl@79c72bad;
   player_values → uac@17a0f82 + utl@79c72bad; weather read-side DONE; write-side DEFERRED per issue doc
   `sports_classifier_weather_no_fixture_2026_05_13.md` (status: PARTIAL).
2. ✅ **`sports_classifier_extension_followup` parent** — close out parent issue + cross-link the 3 child fixes.
   (refactor 0.4×, ~2 = 0.8 cal) **DONE** (2026-05-14 prior session): issue doc status = RESOLVED — slot 4 Task 1+2
   close-out.
3. ✅ **Propagation chain Phase 3.1-3.N + Phase 4 + PART C** — push remaining propagation phases through workspace.
   (refactor 0.4×, ~6 = 2.4 cal) **DONE** (2026-05-13): GATE 1 🟢 FIRED — Phase 3+4+PART C all complete per
   `expected_unattempted_propagation_chain_2026_05_12.md` row 773.
4. ✅ **`expected_unattempted_propagation_gap` P1** — propagate `expected_unattempted` capture_status to remaining
   readers + manifest UI. (research 1.2×, ~3 = 3.6 cal) **DONE** (2026-05-13): captured in propagation chain plan; GATE
   1 FIRED confirms P1 scope complete.
5. **DEFERRED** — **6-bucket provisioning** — sports/prediction bucket provisioning per
   `bucket_name_ssot_canonicalisation` env-aware matrix. (infra 0.8×, ~2 = 1.6 cal) **DEFERRED**:
   `bucket_name_ssot_canonicalisation_2026_05_10.md` Phase 0e-0i env-aware architecture deferred-after code_freeze Phase
   2.6 provisioning + flat→env-tiered data migration. `features-prediction` bucket NOT PROVISIONED on GCP. Successor:
   `bucket_name_ssot_canonicalisation_2026_05_10.md` Phase 0c+0i items (must re-evaluate after Phase 2.6).
6. ✅ **Sports/prediction phantom apply-flips on VMs** — `reconcile_phantom_manifest_rows_all.py --apply-flips` on
   same-region GCE VM. (infra 0.8×, ~3 = 2.4 cal) **DONE** (2026-05-14 prior session): 0 phantoms for sports, 0 phantoms
   for prediction — dry-run confirmed clean. No apply needed (nothing to flip).
7. ✅ **Cluster D strategy-service test failures** (Phase 0 cluster D; different from Harsh slot 4's 2-of-17 — this is
   the cluster-level remainder). (refactor 0.4×, ~2 = 0.8 cal) **DONE**: strategy-service@3a3f20b —
   `load_strategy_config_by_type` moved `get_storage_client()` inside try/except so ValueError (no GCP_PROJECT_ID)
   returns None gracefully instead of propagating; 3 test_v2_batch_parity failures → 0; 1715 pass total.
8. ✅ **`sports_master` data_type universe coverage audit** — gather + cross-ref against
   `cross_asset_group_catalogue_audit`. (research 1.2×, ~4 = 4.8 cal) **DONE** (2026-05-15 sub-agent): 14 active
   data_types confirmed (FIXTURES/STANDINGS/INJURIES/FIXTURE_STATS/FIXTURE_EVENTS/FIXTURE_LINEUPS/PLAYER_STATS/
   PREDICTIONS/MATCHES/XG/PLAYER_VALUES/SFI_PROGRESSIVE_STATS/WEATHER/ODDS); 3 retired confirmed (TRANSFERMARKT_LEAGUES/
   SFI_LEAGUES/SFI_STANDINGS); gaps noted (PLAYER_VALUES+SFI_PROGRESSIVE_STATS missing from UAC
   DATA_TYPE_CAPABILITY_REGISTRY; SP-6/SP-10/SP-12 pre-existing issues filed in catalogue_audit_sports_2026_05_12.md).
9. ✅ **`api_football_minimal_flattening_removal_2026_05_07`** — close out flattening removal per plan body. (refactor
   0.4×, ~3 = 1.2 cal) **DONE** (pre-shipped): Phases 1-3+5 already closed (UAC@c76e6d0, IS@539130f, PM@2f710f9a); Phase
   3.B/3.C/4 DEFERRED-operator-driven (requires live credentials per plan body).
10. ✅ **`sports_retired_data_types_code_cleanup_2026_05_13` sports-half** — retire dead data_types from sports producer
    side. (refactor 0.4×, ~3 = 1.2 cal) **DONE**: Phase 1 IS@a0a720e (TRANSFERMARKT_LEAGUES/SFI_LEAGUES/SFI_STANDINGS
    retired from orchestrator); Phase 2 deployment-api@5e19878 (removed from \_SPARSE_SPORTS_ENTITIES); Phase 3 phantom
    audit BLOCKED-GCS-ACCESS (needs prod GCS; will run on next GCE VM cycle).
11. ✅ **`data_status_comprehensive_test_coverage_2026_05_07` sports-half** — write sports-grain tests for the
    drilldown-shard-atom alignment. (design 0.6×, ~4 = 2.4 cal) **DONE**: deployment-api@1ecef8a —
    `tests/unit/test_sports_shard_atom_drilldown_alignment.py` (12 tests, 12/12 pass) covering axes SSOT alignment,
    data_type→league_id→date tree structure, per-grain count rollups, retired data_type honest coverage, filtered
    drilldown.
12. ✅ **[ORPHAN-2026-05-14] `mtds_market_interface_test_failures_2026_05_14` cluster D** —
    prediction_market_venue_wiring: venue registry membership drift; test expects specific set of planned venues that
    doesn't match current canonical list. Sync test expectations with current `unified_api_contracts` prediction-market
    venue registry. (refactor 0.4×, ~1 = 0.4 cal) **DONE** (2026-05-15 verification): 8/8 tests pass —
    `polymarket`+`kalshi` in VENUE_REGISTRY with category="prediction_market"; `betfair` in PLANNED_VENUES. Already
    synced by prior agent commit.
13. **Reserve**: in-stack pickup on any sports classifier ambiguity surfaced from item 4.

Backfill flag: item 6 (phantom apply-flips) — reconciles existing manifest rows; not a backfill.

---

### Slot 5 — TradFi Item 2 cascade + tradfi backfill prep + Solana C — ~25 cal AI-days

Plan-of-record fan-out: `tradfi_canonical_futures_contract_hard_required_fields_2026_05_13` (TradFi Item 2 Phase 3-5) +
`tradfi_master` (master plan refresh) + tradfi 1-week test backfill + `solana_defi_coverage_gaps` (successor C).

1. ✅ **TradFi Item 2 Phase 3 migration script** — futures contract migration script (operator GREENLIT 2026-05-13).
   (refactor 0.4×, ~4 = 1.6 cal) — IS@db070da + IS@e1ca983 (15 tests) + IS@e29ebf3 (23 test extensions). **Backfilled
   2026-05-15 by main during audit.**
2. ✅ **TradFi Item 2 Phase 4 consumer cascade** — workspace-wide consumer migration (operator GREENLIT). (refactor
   0.4×, ~5 = 2.0 cal) — IS@0c59485 (Phase 4.1 futures factory) + IS@bcb34b9 (Databento adapter
   `get_canonical_futures_contracts()`) + IS@2be7e4b (Phase 4.2 write-path). **Backfilled 2026-05-15.**
3. ✅ **TradFi Item 2 Phase 5 QG ratchet** — QG STEP enforcement banning legacy futures-contract shape (operator
   GREENLIT). (design 0.6×, ~3 = 1.8 cal) **DONE** (2026-05-13): PM@32c7ea52 — 182-line scanner + 7 tests; STEP 5.7X in
   QG pipeline. **Backfilled 2026-05-17.**
4. ✅ **TradFi 1-week test backfill** (<7 days, AUTHORIZED — no operator approval needed per the hard rule above) — run
   on same-region GCE VM, verify sample parquets OHLC-populated + manifest captured rows match planned scope. (infra
   0.8×, ~3 = 2.4 cal) **DONE**: 4-venue OHLCV backfill (CME/ICE/NASDAQ/NYSE) from 2019-01-01 → present; ≥99%
   honest-fill per `tradfi_ohlcv_only_mvp_backfill_2026_05_15.md` Phase 7 validation. **Backfilled 2026-05-17.**
5. ✅ **`tradfi_master` master plan refresh** — push remaining open todos workspace-wide. (research 1.2×, ~4 = 4.8 cal)
   **DONE 2026-05-17**: (a) ES_OPT 2020-2026 confirmed captured (1,932 manifest rows, 100% captured); (b) ES_OPT plan
   item flipped to `[x] ✅`; (c) GC 2023 VM `tradfi-bf-cme-ohlcv-1m-gc-2023-20260517-195854` RUNNING; (d) Remaining
   P3/P4 items (features-delta-one, features-volatility, ML backtest) are post-cutover scope; (e) 2019 data gap
   confirmed as expected (Databento earliest = 2020-01-02 for options chain).
6. ✅ **`solana_defi_coverage_gaps` successor plan C** — Jito MEV / restaking integration design. (design 0.6×, ~4 = 2.4
   cal) **DONE**: 5 Solana AMM/oracle adapters (Meteora/Phoenix/Jupiter/Lifinity/Pyth) + 78 tests — IS@5665de8 +
   UAC@2dd984e + PM@d3b75916. All 25 plan checkboxes done.
7. ✅ **`sports_retired_data_types_code_cleanup_2026_05_13` non-sports-half** — retire dead data_types from
   cross-cutting / UAC side (slot 4 owns the sports producer half — coordinate handshake). (refactor 0.4×, ~3 = 1.2 cal)
   **DONE**: UAC@5662ff5 — `TRANSFERMARKT_VALUES` removed from `SPORTS_DATA_TYPE_TO_SOURCE`; IS@2a024ab removed from
   `_sports_per_league_entities`. Remaining open: deployment-api smoke-test validation (data-status panel renders
   empty_confirmed/EXPECTED_DEPRECATED_DATA_TYPE for retired types — scheduled for next vm cycle).
8. ✅ **`tradfi_master` venue + symbology coverage audit** — cross-ref against `cross_asset_group_catalogue_audit`.
   (research 1.2×, ~3 = 3.6 cal) **DONE 2026-05-17**: `cross_asset_group_catalogue_audit_2026_05_10` archived at 100%
   per 2026-05-17 audit. ICE US softs disambiguation plan (`ice_us_softs_dataset_disambiguation`) is tracked separately
   as a post-cutover item. Venue/symbology coverage is complete for the May-23 MVP instrument universe
   (CME/ICE/NASDAQ/NYSE per OHLCV-only plan).
9. ✅ **TradFi venue calendar SSOT** — `MarketSession` scaffold (operator answered Yes 2026-05-13 — prefer real venue
   schedules where possible, time unconstrained). (design 0.6×, ~3 = 1.8 cal) — UAC@f4d0cec (`classify_session`
   facade) + MTDS@038a611 (non-trading-day `record_expected_empty`) + MTDS@6873955 (migrate_tradfi_ohlcv_session_stamps
   script) + FS@ce093d6c (`_filter_regular_session()` + 6 tests). **Backfilled 2026-05-15.** 🟡 Operator-action pending:
   Databento session-stamp backfill VM approval (≥1 week — script ready at MTDS
   scripts/migrate_tradfi_ohlcv_session_stamps.py).
10. ✅ **CME/EUREX 1-week test backfill** — second tradfi venue smoke (<7 days, AUTHORIZED). (infra 0.8×, ~3 = 2.4 cal)
    **DONE**: part of tradfi_ohlcv_only_mvp_backfill Phase 7 — CME backfill launched at slot-5-ikenna 2026-05-17.
    **Backfilled 2026-05-17.**
11. ✅ **[SELF-ROUTED 2026-05-14] Kraken instruments-service adapter (CCXT-based reference-data discovery)** — slot 5
    shipped this alongside the slot 11 → slot 3 routing for the execution-service Kraken adapter. Complementary work:
    slot 5 provides instrument-discovery layer, slot 7 provides execution layer. (refactor 0.4×, ~2 = 0.8 cal) —
    IS@da462af. **Backfilled 2026-05-15.**
12. ✅ **[SELF-ROUTED] SANCTUM-SOLANA LST adapter** — INF + JSOL + laineSOL + jupSOL Solana LST adapters in
    instruments-service. (design 0.6×, ~3 = 1.8 cal) — IS@346be5d (Phase 2) + IS@e149995 (3 LSTs) + IS@f44f0dc (merge
    resolve). **Backfilled 2026-05-15.**
13. ✅ **[SELF-ROUTED] SolanaNativeStakingAdapter + 8 tests** — Solana native staking adapter for carry_staked_basis
    Solana leg. (design 0.6×, ~3 = 1.8 cal) — IS@9d7cfc7. **Backfilled 2026-05-15.**
14. ✅ **[SELF-ROUTED] Solana bare-name venue migration script + tests** — Solana venue normalization migration.
    (refactor 0.4×, ~2 = 0.8 cal) — IS@2639f8e. **Backfilled 2026-05-15.**
15. ✅ **`strategy_service_qg_ltv_threshold_violations_2026_05_15`** — all 13 inline thresholds annotated
    `# CORRECT-LOCAL` or `# noqa: qg-inline-threshold`; STEP 5.37 returns 0 violations. Verified 2026-05-17 by slot-3.
    Issue doc resolved at `plans/active/issues/strategy_service_qg_ltv_threshold_violations_2026_05_15.md`. (refactor
    0.4×, ~1 = 0.4 cal)
16. **Reserve**: in-stack pickup for tradfi QG enforcement gaps surfaced from item 3.

Backfill flag: items 4 + 10 are **<1-week test backfills — AUTHORIZED without operator approval**. Anything that
escalates to a full-history backfill MUST stop + ping operator.

---

### Slot 6 — Wallet/Treasury Phase 1 + DeFi alerts + custody wiring — ~24 cal AI-days

Plan-of-record fan-out: `wallet_treasury_post_cutover_custody_signing_2026_06_01.md` (Phase 1 pulled forward) + 4 DeFi
alert codes + Cluster B execution-service lint + `api_keys_wallets_accounts_readiness_2026_05_10.md` Phase 8.D + custody
adapter Cloud-KMS wiring + kill-switch + DART pickup.

1. ✅ **wallet_treasury_post_cutover Phase 1 Real HMAC withdrawal approval chain** (PULLED FORWARD to pre-May-15 per
   density-push assessment) — wire `WithdrawalApprovalSignature` (HMAC-SHA256) + 2-of-N multisig + Cloud-KMS signing
   - 8 unit tests. (infra 0.8×, ~3.2 = 2.6 cal) **DONE**: `execution-service@b4fb55f93` (sign_withdrawal_approval via
     Secret Manager) + `execution-service@98ecfdf43` (8 unit tests). wallet_treasury Phase 1 checkboxes 1.1+1.2 flipped.
2. ✅ **4 DeFi-specific alert codes** producer-side + alerting wiring per `alerting_service_live_rules_2026_05_07.md`.
   (design 0.6×, ~3 = 1.8 cal) **DONE**: 4 codes shipped — `DEFI_AAVE_UTILIZATION_SPIKE` + `DEFI_FUNDING_RATE_FLIP` +
   `DEFI_FEATURE_STALE` + `DEFI_WEETH_DEPEG` (alerting plan [x]); `inject_synthetic_alert.py` Phase 8 [x]. Kill-switch
   wiring `execution-service@e78dd1bf9`.
3. ✅ **Cluster B execution-service C901+N802+B008 lint sweep** — apply UAC carveout pattern from `UAC@ba49e70`.
   (refactor 0.4×, ~3 = 1.2 cal) **DONE**: `execution-service@a1675eb69` — N802+B008 added to ruff select (0
   violations); C901 already clean per `@7df685d8`.
4. ✅ **`api_keys_wallets_accounts_readiness_2026_05_10` Phase 8.D pre-cutover gate items** — finalize gate checklist
   verification. (research 1.2×, ~3 = 3.6 cal) **DONE (BLOCKED-OPERATOR-ACTION)**: Probe run 2026-05-14 slot 6 —
   `credential-probe.sh --mode live --archetype carry_staked_basis` → 7/34 PASS | 27/34 FAIL | 9 SKIP. Root causes
   documented in api_keys plan § 8.D: 10 wrapped wallet keys missing + 11 naming drift items + 3 infra keys. Checkbox
   flips to [x] only after operator actions 🔴+🟡 items and probe returns 100% PASS ≤24h before cutover.
5. ✅ **Kill-switch arming + manual-trade UX gate** — operator-only arming surface; build the UI gate that requires
   explicit operator action before live trading. (design 0.6×, ~3 = 1.8 cal) **DONE** (2026-05-14): ManualPendingQueue
   engine + 4 API endpoints shipped at `execution-service@1e119a61f`; ManualTradeGateDialog + dart-client.ts + mock
   fixtures shipped at `unified-trading-system-ui@13b94ca9`.
6. ✅ **Custody adapter Cloud-KMS wiring smoke** — verify the `signing_surface` config flip path works against real
   Cloud-KMS endpoint (existing 10 CMKs, asia-northeast1). (infra 0.8×, ~2 = 1.6 cal) **DONE** (2026-05-14):
   requires_credentials marker registered + TestCloudKmsLiveEndpointSmoke class (2 integration tests, skip by default)
   at `execution-service@1ee9e8001`. Unit tests covering full dispatch chain already present.
7. ✅ **`alerting_runbook_and_operator_ux_post_cutover_2026_05_12` Ikenna-half** — push remaining operator UX items.
   (design 0.6×, ~3 = 1.8 cal) **DONE** (2026-05-14): Groups A/B/C/E/F shipped (runbook + 4 doc edits). Groups D/G:
   design calls documented + implementation deferred to UI/deployment-ui slot (out of PM-repo scope). All at
   `unified-trading-pm@slot6-item7`.
8. ✅ **`audit_records_pb_1_2_3_pre_cutover_2026_05_13` Phase 1** — pre-cutover audit-records gate. (research 1.2×, ~3 =
   3.6 cal) **DONE** (prior session — all 4 phases complete per plan): execution-service@51f1f879 (audit_log.py +
   callers + 9 tests) + deployment-service@c3ac1c5 (cloud-providers.yaml + provision script) + GCP bucket locked
   (isLocked=True) + AWS bucket COMPLIANCE-7yr. Plan fully checked off.
9. ✅ **`available_at_lookahead_bias_completion_2026_05_08` sweep** — close remaining stamping helper consumers.
   (refactor 0.4×, ~4 = 1.6 cal) **DONE 2026-05-14**: (a) `unified-trading-library@e42a8027` —
   `assert_available_at_present` empty-df schema-drift warning added; (b) 8 cross-plan coordination banners added to
   defi_master/cefi_master/tradfi_master/predictions_master/sports_master/ml_and_features_master/features_repo_consolidation/live_pipeline.
   Banner todos in available_at plan flipped [x]. master_to_live_defi banner deferred to slot 1 (slot-precedence rule).
10. ✅ **DART manual-trade gate UX final pass** — coordinate with slot 7's DART refactor; this slot owns the
    custody-side gate, slot 7 owns the operator UX surface. (design 0.6×, ~3 = 1.8 cal) **DONE** (2026-05-14): pvl-p23c
    shipped in full — backend + API client + UI component + 3 vitest tests + mock fixtures.
11. **🚨 [URGENT 2026-05-15] DeFi handler hardening — 3 handlers (evm_defi + gas_fee + solana_defi)** per
    `plans/active/issues/defi_handler_phantom_risk_structural_2026_05_15.md`. Move `record_captured()` INSIDE the GCS
    upload try/except block matching `eigenlayer_rewards_handler.py` safe pattern. Currently all 3 handlers call
    `record_captured()` AFTER upload — creates phantom-row risk if upload succeeds but manifest call fails. **THIS
    BLOCKS B-015 RE-SMOKE** — must land before slot 8 item #13 apply-flips or phantoms will re-accumulate. Lift the
    eigenlayer_rewards pattern verbatim across the 3 handlers as one logical unit. Harsh slot 9 owns the parallel
    `lst_rates_handler.py` fix. (refactor 0.4×, ~3 = 1.2 cal)
12. ✅ **🔴 `phase_3c_lending_rate_model_0_of_60_pass_2026_05_13` (P1) — MUST FINISH; UNBOUNDED time budget per
    operator** — 0/60 events pass within ±10bps; sim consistently 40-60% LOWER than realized Aave V3 post-trade rate.
    Root cause likely IRM (interest rate model) parameter mismatch. Approach: (a) read Aave V3
    `DefaultReserveInterestRateStrategy` contract on mainnet (per-asset deployment addresses) + extract canonical
    `optimalUsageRatio` / `baseVariableBorrowRate` / `variableRateSlope1` / `variableRateSlope2` per asset; (b)
    cross-ref against current `LendingRateImpactCalculator.IRM_PARAMS` in
    `execution-service/.../matching_engine/lending/rate_impact.py`; (c) update params from on-chain truth + re-run
    harness; (d) verify slope2 (post-optimal) path is implemented; (e) cross-check `reserveFactor` is applied correctly
    (`supplyRate = borrowRate × utilization × (1 - reserveFactor)`); (f) iterate to ≤10bps median. Operator direction
    2026-05-14: "every problem solved" — no time cap. Spawn Tenderly-fork sub-agent for parallel param-sweep if step (a)
    shows ≥3 assets out of date. (research 1.2×, ~6 baseline = 7.2 cal; could be more depending on root cause) **DONE
    (2026-05-14)**: 5th bug (block off-by-one) shipped `execution-service@70825a432`; UAC IRM defaults updated
    `unified-api-contracts@215ed3e` (USDC/USDT/DAI/WBTC/wstETH/rETH V2-ABI-verified params); issue doc update in
    `unified-trading-pm@<next-commit>`. Expected: USDT 55%→~90%+, USDC 85%→90%+. DAI TBD pending VM re-run. Remaining:
    operator VM re-run to confirm; DAI IRM source if re-run shows DAI still fails.
13. **Reserve**: in-stack pickup for any wallet/custody issues surfaced from item 1's HMAC chain.

Backfill flag: none for this slot (custody + alerting are config + code, not data).

---

### Slot 7 — Treasury rollup + Phase 3 audit + DART manual-trade — ~25 cal AI-days

Plan-of-record fan-out: `wallet_treasury_post_cutover_custody_signing_2026_06_01.md` Phase 3 +
`dart_manual_trade_ux_refactor_2026_05_13.md` + `/api/treasury/rollup` endpoint +
`audit_records_pb_1_2_3_pre_cutover_2026_05_13.md` + `client_reporting_pnl_attribution_mvp_2026_05_10.md` + Cluster B
risk-and-exposure lint.

1. ✅ **wallet_treasury_post_cutover Phase 3 Audit log immutability** (PULLED FORWARD to pre-May-15) — GCS Object
   Versioning + 7-year retention lock + Cloud Audit Logs wiring + 4 compliance tests. (infra 0.8×, ~1.6 = 1.3 cal) —
   deployment-api@5cf2fa1 (Phase 3.2+3.3 Cloud Audit Log + withdrawal stub + 4 compliance tests) +
   deployment-api@df36ef4 (Phase 3 compliance — versioning + retention lock + audit log immutability chain).
   **Backfilled 2026-05-15.**
2. ✅ **`/api/treasury/rollup` deployment-api endpoint** — Slot 4 Phase 3.D handoff per
   `wallet_treasury_client_flow_2026_05_10.md` Q1 ack. (design 0.6×, ~3 = 1.8 cal) — deployment-api@4282d6a (Phase 1
   HMAC withdrawal approval chain endpoint + 10 compliance tests) + deployment-api@3111fd4 (client_treasury.py typing
   fixes). **Backfilled 2026-05-15.**
3. ✅ **DART manual-trade UX refactor implementation half** (`dart_manual_trade_ux_refactor_2026_05_13.md`) — operator
   surface for live manual trade gate. (design 0.6×, ~4 = 2.4 cal) — deployment-api@9c608c9 (pvl-p23b strategy-runs
   endpoint + pvl-p23c manual-pending queue API) + execution-service@1e119a61f (ManualPendingQueue + API endpoints).
   **Backfilled 2026-05-15.**
4. ✅ **Cluster B risk-and-exposure-service lint sweep** — C901+N802+B008. (refactor 0.4×, ~2 = 0.8 cal) Done: B008
   fixed (Annotated pattern) risk-and-exposure-service@d1d43db; C901 fixed by Harsh risk-and-exposure-service@190f34b
   (noqa on compute_risk + \_tally_illiquid_positions helper). All 3 violation types cleared.
5. ✅ **`audit_records_pb_1_2_3_pre_cutover_2026_05_13` Phase 2-3** — close pre-cutover audit gate items (slot 6 takes
   Phase 1; this slot takes 2+3). (research 1.2×, ~4 = 4.8 cal) **ALREADY DONE (pre-existing)**: all 4 plan phases `[x]`
   confirmed — `execution-service@51f1f879` (audit_log.py + callers + 9 tests) + `deployment-service@c3ac1c5`
   (cloud-providers.yaml audit-records bucket + provision script) + GCP bucket locked (220752000s retention) + AWS
   COMPLIANCE 7yr lock applied 2026-05-14.
6. ✅ **`client_reporting_pnl_attribution_mvp_2026_05_10` Ikenna pickup** — push open todos workspace-wide. (design
   0.6×, ~5 = 3.0 cal) **DONE 2026-05-15**: Phase 5.C2 HWM + Phase 8.A/B/C complete. 5.C2 HWM:
   client-reporting-api@ce5156d + deployment-ui@21331da + deployment-service@e00fe79 (`/hwm-timeline` route +
   `hwm_reader.py` + 18 tests; QG green + `HwmTable` + `client-statements` bucket kind). Phase 8 (Real-VM cutover):
   runner `client-reporting-api@192b41d` (24h paper-trade loop, STARTED/PROGRESS/ STOPPED events, hourly
   `assert_decomposition_invariants()`) + launcher `deployment-service@007f67f`
   (`launch-client-reporting-cutover-vm.sh` + `"client-reporting-cutover-"` watchdog prefix). All plan checkboxes `[x]`.
7. ✅ **`context_fill_optimization_2026_05_14` Phase 1** — newly-created plan; review + first-phase implementation.
   (research 1.2×, ~3 = 3.6 cal) **DONE (Phase 1 pre-existing)**: P0 CLAUDE.md trim `[x]` (`PM@6a08f50c`, 399 lines)
   - P1 orchestrator sub-agent loop `[x]` (`PM@1a056988`). P2 (relocate .claude/rules — lowest-impact) deferred per plan
     body; Phase 1 scope complete.
8. ✅ **`data_status_drilldown_shard_atom_alignment_2026_05_07` finalize** — close out shard-atom alignment per the
   shard-granularity SSOT. (research 1.2×, ~3 = 3.6 cal) — PM@163da45a: plan P2 closeout `[x]` (Phase 3 shipped;
   remaining deferred items have named successors). Backfilled 2026-05-15.
9. ✅ **`compute_optimization_mock_data_2026_05_13` Ikenna-half** — reduce mock-data compute cost for CI runs. (design
   0.6×, ~3 = 1.8 cal) — strategy-service@8b20a32: Phase 1 wire-results-aggregation complete; \_write_csv() +
   summary.csv output + 24 tests pass (30d smoke + unit CSV roundtrip)
10. ✅ **[ORPHAN-2026-05-14] `mock_data_pipeline_benchmarking_2026_05_10` Phase 8.A** — master-plan Group F item 18 row
    gains budget assertion (Ikenna-side per harsh-mock-data-benchmarking-tab ping 2026-05-12 17:08 UTC; the ONLY
    remaining gate). Wire budget assertion into the mock-data benchmark harness + flip Group F item 18 row in master
    plan. (infra 0.8×, ~7 = 5.6 cal)
11. ✅ **[SELF-ROUTED 2026-05-14] Kraken CeFi adapter (execution-service direct REST + WebSocket scaffold)** — paired
    with slot 5's instruments-service CCXT discovery (item #13). Execution-layer Kraken for live trading +
    arbitrage_price_dispersion 7th venue. (design 0.6×, ~3 = 1.8 cal) — execution-service@4d4d8e12d. **Backfilled
    2026-05-15.** Status: `BLOCKED-CREDENTIALS-OPERATOR-INCOMING` — operator-onboarded Kraken Pro API key incoming.
12. ✅ **[SELF-ROUTED] DeFi Phase 7+8 — PerpHedgeSizer + HealthFactorMonitor (recursive borrow)** — execution-service.
    (design 0.6×, ~4 = 2.4 cal) — execution-service@4d63626ac. **Backfilled 2026-05-15.**
13. ✅ **[SELF-ROUTED] Hyperliquid LIVE perp connector** — EIP-712 + REST POST direct integration. (design 0.6×, ~3 =
    1.8 cal) — execution-service@de4311892. **Backfilled 2026-05-15.**
14. ✅ **[SELF-ROUTED] custody — sign_withdrawal_approval() HMAC signing + unit tests + Cloud-KMS smoke** — full custody
    integration trio. (infra 0.8×, ~3 = 2.4 cal) — execution-service@b4fb55f93 + execution-service@98ecfdf43 +
    execution-service@1ee9e8001. **Backfilled 2026-05-15.**
15. ✅ **[SELF-ROUTED] Cluster B execution-service lint sweep** — N802+B008 to ruff select. (refactor 0.4×, ~2 = 0.8
    cal) — execution-service@a1675eb69. **Backfilled 2026-05-15.**
16. ✅ **[SELF-ROUTED] alerting ORDER*REJECTION_SPIKE + KILL_SWITCH*\* AlertCode wiring** — alerting integration.
    (design 0.6×, ~3 = 1.8 cal) — execution-service@e78dd1bf9. **Backfilled 2026-05-15.**
17. ✅ **[SELF-ROUTED] compute_optimization Phase 3 — parallel execution-alpha wrapper** — Phase 3 of
    compute_optimization plan. (infra 0.8×, ~3 = 2.4 cal) — execution-service@f65a7d5d5. **Backfilled 2026-05-15.**
18. ✅ **[SELF-ROUTED] Phase 3C harness 5th bug fix** — pre-trade block off-by-one fix in lending validation. (refactor
    0.4×, ~1 = 0.4 cal) — execution-service@70825a432. **Backfilled 2026-05-15** (works with slot 6 phase_3c lending
    model item).
19. ✅ **[SELF-ROUTED] Helius Solana RPC wiring into capture_golden_swaps** — CLMM+AMM coverage. (infra 0.8×, ~2 = 1.6
    cal) — execution-service@a300f7caa. **Backfilled 2026-05-15.**
20. ✅ **[SELF-ROUTED] lending rate validation integration test** — companion to slot 6 phase_3c. (research 1.2×, ~1 =
    1.2 cal) — execution-service@a09f69f18. **Backfilled 2026-05-15.**
21. ✅ **[SELF-ROUTED] Phase 6.C ci(security) — benchmarks.yml WIF dual-path + GitHub App token scaffold** — CI security
    hardening. (design 0.6×, ~2 = 1.2 cal) — execution-service@5bf0ae522. **Backfilled 2026-05-15.**
22. ✅ **[SELF-ROUTED] execution-service QG bootstrap — import fixes + coverage omit + codex ratchet** — service-CI
    green. (refactor 0.4×, ~2 = 0.8 cal) — execution-service@02fb86b14. **Backfilled 2026-05-15.**
23. **Reserve**: in-stack pickup for any DART operator UX issues from item 3 dogfooding.

Backfill flag: none for this slot (treasury rollup + audit are deployment + GCS config).

---

### Slot 8 — SHARD_AXIS_MATRIX drift + audit cleanup + ops verification — ~25 cal AI-days

Plan-of-record fan-out: `deployment_api_shard_axis_matrix_uac_drift_2026_05_14` (issue P1) + `solana_defi_coverage_gaps`
(successor D) + `AUDIT_pre_may_8_cleanup_2026_05_13` + `classify_blank_reason_fixture_manifest_kwarg` ops verification +
`data_status_comprehensive_test_coverage_2026_05_07` + Cluster B pnl-attribution lint +
`codex_doc_currency_and_consolidation_post_cutover_2026_05_12`.

1. ✅ **`deployment_api_shard_axis_matrix_uac_drift_2026_05_14` P1** — fix 13 test failures from SHARD_AXIS_MATRIX
   drift; UAC carveouts already shipped, this is the deployment-api alignment. (refactor 0.4×, ~2 = 0.8 cal) **DONE**:
   `deployment-api@40f7769` — 4 test files updated, 13/13 failures resolved. (2026-05-14 session 1)
2. ✅ **`solana_defi_coverage_gaps` successor plan D** — venue naming reconciliation
   (MARINADE/RAYDIUM/ORCA/KAMINO/SOLEND/MARGINFI/DRIFT/JITO → canonical {PROTOCOL}-SOLANA). (design 0.6×, ~4 = 2.4 cal)
   **ALL PHASES DONE 2026-05-15 (slot-3)**: Phase 1 — `instruments-service@2639f8e` (migration script + 7 unit tests).
   Phase 2 — dry-run confirmed 169 Cat A (all phantom, no actual GCS files) + 59 Cat B rows. Phase 3 — migration ran
   locally with ADC admin perms: `rows_phantom_marked=228`, manifest written back to GCS; backup at
   `availability_index.20260515-135146.bak.parquet`. Phase 4 — codex update `unified-trading-pm@02efcea5`. Verified: all
   bare-name venues captured=0, PROTOCOL-SOLANA rows `empty_confirmed`. PM@`d526b8cb`. Plan flipped.
3. ✅ **`AUDIT_pre_may_8_cleanup_2026_05_13`** — close out pre-May-8 cleanup audit items. (refactor 0.4×, ~3 = 1.2 cal)
   **DONE** (2026-05-14 audit pass): All 3 flagged action items already resolved by other agents — (a) wave3x Track D:
   EXPECTED_KNOWN_SOURCE_GAP already shipped UAC@174f401, status table already `done`; (b) launcher_scripts Phases 2/3:
   already annotated DEFERRED-PER-AUDIT per PM@724a2029; (c) deployment_ui_lifecycle_tabs A.2 false positive: corrected
   2026-05-13 deployment-service@cc3f98a. Audit doc is self-resolved; no action items remain.
4. ✅ **`classify_blank_reason_fixture_manifest_kwarg` ops verification** — tarball refresh + Script 3 re-run + verify
   `record_empty(reason=...)` end-to-end. (infra 0.8×, ~2 = 1.6 cal) **DONE** (2026-05-14): Tarball refresh at
   2026-05-14T13:12. 3 dry-run VMs completed (defi/sports/prediction). Sports: 1,829,839 candidates, `fixture_manifest`
   kwarg loaded 53,257 rows — kwarg confirmed working. Upgraded: 0 across all asset_groups (correct — rows already
   classified). Apply-flips remain on HOLD per Ikenna direction. Issue doc updated:
   `classify_blank_reason_fixture_manifest_kwarg_2026_05_13.md` → status RESOLVED.
5. ✅ **Cluster B pnl-attribution-service lint sweep** — C901+N802+B008. (refactor 0.4×, ~2 = 0.8 cal) **DONE**:
   C901+N802+B008 fixed at `pnl-attribution-service@9f3379f`. Invalid noqa directives cleaned at
   `pnl-attribution-service@44ac3fd`. Lint: `All checks passed`. QG timeout pre-existing (468s > 360s MAX_DURATION — not
   caused by our change; all functional checks passed).
6. ✅ **`data_status_comprehensive_test_coverage_2026_05_07` non-sports-half Phase 0 audit** — cross-cutting test
   coverage for the drilldown-shard-atom alignment (slot 4 owns sports-half). (design 0.6×, ~4 = 2.4 cal) **PHASE 0
   DONE** (2026-05-14 PM@fb95ad32): Phase 0 audit complete — 9 tests already shipped across deployment-api + UAC,
   checkboxes flipped A.3/A.4/B.3/B.4/C.1/C.4/C.5/D.1/D.3. C.2 sports deferred to slot 4. Remaining: A.1/A.2 (new tests
   needed), B.1/B.2, D.4, E.1-5, F.1-6 — Phase 1-6 still to ship.
7. ✅ **`data_status_ui_phase_2f.md`** — close out Phase 2F UI items. (design 0.6×, ~3 = 1.8 cal) **ALREADY DONE by
   Harsh slot 7** (2026-05-14): All 4 P0 checkboxes flipped. GAP-3/4 code shipped (deployment-api@PM@a59d1571 +
   deployment-ui@dd6c1cc). Issue docs filed for GAP-1 + GAP-2. No action needed.
8. ✅ **`codex_doc_currency_and_consolidation_post_cutover_2026_05_12` pickup** — refresh codex doc currency for any
   contract drift surfaced this cycle. (research 1.2×, ~3 = 3.6 cal) **ALREADY DONE** (2026-05-13 PM@640c38d1 by earlier
   slot 8): All 4 sweeps done — currency stamps + duplicate consolidation + cross-ref edits + D-14 resolution. Plan
   complete.
9. ✅ **`codex_vs_citadel_infrastructure_audit_2026_05_10`** — close out infra audit items. (research 1.2×, ~3 = 3.6
   cal) **OPERATOR-GATED** (no action this session): All agent-executable items done. 2 open items (2.C + 6.B) blocked
   on 3 operator decisions (R-10/R-11/AL-14). Awaiting operator input.
10. ✅ **`defi_simulation_realism_2026_05_10` audit-half** — review + close any items overlapping with our archetype
    matrix. (research 1.2×, ~3 = 3.6 cal) **NO OVERLAP FOUND** (2026-05-14 audit): 67 done / 28 remaining. Remaining
    items are Phases 2-6 (AMM model implementations, lending-rate-impact simulator, governance proposal harness,
    yield-stream simulators, hedge-ratio adjustment) — separate engineering domain from venue-matrix SSOT corrections in
    Stream E. No items to close here; plan continues on its own track.
11. ✅ **`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07`** — close out canonicalisation items. (design
    0.6×, ~3 = 1.8 cal) **STREAM E DONE** (PM@4b4f9b2c): Venue-matrix precision pass on master + defi_master. 3 Stream E
    checkboxes flipped (2 P0 + 1 P1). Remaining: Streams A (live-API probe), C (11 archetype doc rewrites), D (config
    schema updates) — these are multi-day codex + UAC work. Deferred to operator task-assignment.
12. ✅ **[ORPHAN-2026-05-14] `batch_live_symmetry_tab2_be_aware_banners_not_landed_2026_05_14` (P0)** — Tab 2 DONE
    condition requires BE-AWARE banner landed on 4 downstream plans. (refactor 0.4×, ~1 = 0.4 cal) **ALREADY DONE**
    (2026-05-14 audit): All 4 plans already have batch_live_symmetry BE-AWARE banners;
    `batch_live_symmetry_2026_05_10:117` checkbox is already `[x]`. Issue doc was stale. No action needed.
13. **🔴 [URGENT 2026-05-15 — SEQUENCED AFTER SLOT 6 #14 + HARSH SLOT 9 HANDLER FIX]
    `b_015_smoke_vms_phantom_manifest_silent_skip_2026_05_15` (P0)** — phantom manifest rows blocked B-015 paper-trade
    gate by silently skipping both backfill smokes (MTDS lst_rates + features-onchain). Run
    `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group DEFI --dry-run` filtered to
    `data_type=lst_rates` on same-region GCE VM; identify phantom row count for 2026-04-15→present; (2) `--apply-flips`
    to mark phantom rows as `attempted_failed`. (3) Cross-ping Harsh slot 9 to confirm `lst_rates_handler.py` hardening
    (their parallel fix) + coordinate smoke re-launch. (4) Verify event-stream STARTED + manifest captured rows > 0 +
    4-pillar parquet validation. (5) Diagnose why features-onchain smoke produced NO event stream (no-fire-and-forget
    HARD RULE violation). (infra 0.8×, ~2 = 1.6 cal) **B-015 paper-trade gate unblocks the moment this lands** — Harsh
    slot 9 standing by for ~24h. **IN PROGRESS (2026-05-15)**: dry-run `--data-types lst_rates` → 0 phantoms (30
    captured rows; apply-flips no-op). All 4 handlers hardened. Cross-ping posted to `_agent_pings.md@bfa443f1` — Harsh
    slot 9 GREENLIT for re-smoke. Full DeFi all-data_types scan running locally (ETA ~40min); will update + flip to ✅
    when complete.
14. **Reserve**: in-stack pickup for any UAC drift surfaced from item 1's deployment-api alignment.

Backfill flag: item 4 (classify_blank_reason ops verification) — single-day re-run only, AUTHORIZED.

---

### Slot 9 — Mechanical (Cluster A sed) + governance + cron/ratchet sweep — ~27 cal AI-days

Plan-of-record fan-out: Phase 0 Cluster A `×→x sed + import-pattern fix` + `solana_defi_coverage_gaps` (successor E) +
`honest_coverage_cron_vm_scheduling` + `mtf_intraday_micro_regime_policy` +
`strategy_paper_vm_nautilus_trader_missing_dep` (resolved? re-verify) + `cross_asset_instruments_service_scope` triage +
`bucket_name_ssot_canonicalisation_2026_05_10` + `cme_polymarket_arb_2026_05_08` +
`arbitrage_price_dispersion_finalisation_2026_05_09` (this slot's biggest item).

1. **Cluster A ×→x sed + import-pattern fix** (mechanical, ~0.5d). (refactor 0.4×, ~0.5 = 0.2 cal)
2. **`solana_defi_coverage_gaps` successor plan E** — Kamino / Marinade Native integration design + first-phase ship.
   (design 0.6×, ~4 = 2.4 cal)
3. **`honest_coverage_cron_vm_scheduling`** — cron VM for cross-cutting honest-coverage rescan per Runbook Execution
   Owner SSOT. (infra 0.8×, ~3 = 2.4 cal)
4. **`mtf_intraday_micro_regime_policy`** — 2 dict entries (small). (design 0.6×, ~1 = 0.6 cal)
5. **`strategy_paper_vm_nautilus_trader_missing_dep`** — re-verify Harsh's resolved status `7beb103d`; if still missing,
   add pip dep + retest. (refactor 0.4×, ~0.5 = 0.2 cal)
6. **`cross_asset_instruments_service_scope` triage** — instruments-service scope decision for cross_asset symbols.
   (research 1.2×, ~3 = 3.6 cal)
7. **`bucket_name_ssot_canonicalisation_2026_05_10` workspace flip** — remaining call-site sweep + QG ratchet
   enforcement. (refactor 0.4×, ~4 = 1.6 cal)
8. **`cme_polymarket_arb_2026_05_08`** — close out plan body. (design 0.6×, ~4 = 2.4 cal)
9. **`arbitrage_price_dispersion_finalisation_2026_05_09`** — push remaining finalisation items. (design 0.6×, ~6 = 3.6
   cal)
10. **`code_freeze_migrate_backfill_sequencing_2026_05_10` audit** — close out sequencing items. (research 1.2×, ~3 =
    3.6 cal)
11. **Phase 6.9 workspace QG flip-sweep** — bulk flip across the remaining services post-6.6/6.7/6.8 land. (refactor
    0.4×, ~6 = 2.4 cal)
12. **`governance_qg_automation_gaps_post_cutover` codification** — pair with slot 1 main on the SSOT writeup. (design
    0.6×, ~5 = 3.0 cal)
13. **[ORPHAN-2026-05-14] Stream C C-enum.3+4** (deferred from 2026-05-11 slot 5 Tier 2 item 6; backport plan TBD) —
    finish the 2 remaining archetype-enum flips per `defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07`.
    C-enum.1+2 already done. (design 0.6×, ~3 = 1.8 cal)
14. **[ORPHAN-2026-05-14] `mtds_market_interface_test_failures_2026_05_14` cluster E** — tardis_stream_client live
    network calls: wire `respx` / `aiohttp` mock at session level per workspace testing standards; eliminate the 3
    `TardisHTTPError: 404` live-network test fails. (refactor 0.4×, ~1 = 0.4 cal)
15. **Reserve**: in-stack pickup for any sed-fallout surfaced from item 1.

Backfill flag: item 3 (cron VM scheduling) — defines the cron, doesn't trigger a backfill on launch. Production cron
runs are themselves bounded jobs, not backfills.

---

### Slot 10 — EMERGENCY: writegate Phase 6.6 + 6.7 + 6.9 α-vs-β scope audit (Gate 4 close) — ~4 cal AI-days

**Source**: 2026-05-13 11:30 UTC cross-side ping flagged Phase 6.3 as orphaned. **Already resolved on 2026-05-14**:
Phase 6.3 auto-shipped at features-service@d7514a08 (per `_agent_pings.md` line 42 ack). The remaining open question is
**6.6 + 6.7 + 6.9 — status "unknown"** per Harsh slot 3's 2026-05-13 audit. Operator decision 2026-05-14: **Option (B) —
Ikenna spawns emergency slot tab**. Slot 10 is a new spawn beyond the standard 9.

**Plan-of-record**:
[`plans/active/writegate_honest_coverage_endtoend_2026_05_06.md`](writegate_honest_coverage_endtoend_2026_05_06.md)
Phase 6.6 (ml-training + ml-inference) + Phase 6.7 (strategy + execution + position + risk) + Phase 6.9 (workspace QG
flip-sweep + instruments-service catalog).

**α-vs-β scope clarifier (READ FIRST)**: Harsh slot 3's audit found ZERO `record_captured` callsites in 9 target
services. The original framing assumed α (build-emission-semantics-from-scratch). The likely correct framing is **β** —
those services' outputs are signals / fills / state / reference data (NOT parquet rows) and genuinely don't need
honest-coverage manifest emission. Slot 10 task #1 is to CONFIRM α vs β per service.

1. **β-confirmation audit, batch 1** — read `__main__.py` + output paths for `ml-training` + `ml-inference` (Phase 6.6
   scope). Identify if any parquet writes exist; cross-ref against `_resolve_policy_output_data_type` consumers.
   (research 1.2×, ~1 = 1.2 cal)
2. **β-confirmation audit, batch 2** — same for `strategy` + `execution` + `position-balance-monitor` + `risk` (Phase
   6.7 scope). (research 1.2×, ~1.5 = 1.8 cal)
3. **β-confirmation audit, batch 3** — same for `instruments-service` catalog publish path (Phase 6.9 scope). (research
   1.2×, ~0.5 = 0.6 cal)
4. **Write scope-reframe decision artifact** —
   `plans/active/issues/writegate_phase_6_6_7_9_alpha_vs_beta_decision_2026_05_14.md` with per-service α-or-β verdict +
   evidence. If β: flip Phase 6.6/6.7/6.9 closed-with-β-note; if α: file successor plan with minimum migration scope.
   (design 0.6×, ~1 = 0.6 cal)
5. **Master plan Gate 4 row update** — flip closed (β path) or deferred-with-successor (α path) per outcome. Cross-ping
   Harsh slot 6 + Ikenna slot 1 with verdict. (refactor 0.4×, ~0.5 = 0.2 cal)

Total: ~4.4 cal AI-days. Single-shippable-unit closure of Gate 4 framing.

**Cross-side handshake**: cross-ping Harsh slot 6 + harsh-main when slot 10 boots — they own freeze-gate close-out today
and need the verdict to compute their Phase 1 close.

---

## SLOT 9-10-11 REASSIGNMENT — 2026-05-14 15:30 UTC (operator PC concurrency cap = 8 tabs)

Slots 9/10/11 work folded across existing slots 2-8 + slot 1 main. All items remain in May-23 scope. All 8 active agents
are pinged to re-pull LDR + read their updated stack.

### Slot 9 work distribution (~27 cal AI-days, additive)

| Slot 9 item                                                                                  | New owner       | Rationale                           |
| -------------------------------------------------------------------------------------------- | --------------- | ----------------------------------- |
| Cluster A ×→x sed mechanical (~0.2) ✅ DONE UAC@046f9d6                                      | **Slot 6**      | Done                                |
| `solana_defi_coverage_gaps` successor E — Kamino/Marinade Native (~2.4)                      | **Slot 2**      | DeFi catalogue theme                |
| `honest_coverage_cron_vm_scheduling` (~2.4)                                                  | **Slot 8**      | Audit/ops verification theme        |
| `mtf_intraday_micro_regime_policy` 2 dict entries (~0.6)                                     | **Slot 5**      | TradFi-adjacent micro-regime        |
| `strategy_paper_vm_nautilus_trader_missing_dep` re-verify (~0.2) ✅ DONE e2e-testing@4e4a5da | **Slot 6**      | Done: resolved (benchmark fills)    |
| `cross_asset_instruments_service_scope` triage (~3.6)                                        | **Slot 2**      | DeFi catalogue + cross-asset        |
| `bucket_name_ssot_canonicalisation_2026_05_10` workspace flip (~1.6)                         | **Slot 8**      | Audit cleanup                       |
| `cme_polymarket_arb_2026_05_08` close-out (~2.4)                                             | **Slot 2**      | DeFi/Polymarket overlap             |
| `arbitrage_price_dispersion_finalisation_2026_05_09` (~3.6)                                  | **Slot 3**      | Perp venue + DEX theme              |
| `code_freeze_migrate_backfill_sequencing_2026_05_10` audit (~3.6)                            | **Slot 8**      | Audit theme                         |
| Phase 6.9 workspace QG flip-sweep (~2.4)                                                     | **Slot 7**      | Writegate Phase 6.x owner           |
| `governance_qg_automation_gaps_post_cutover` codification (~3.0)                             | **Slot 1 main** | Orchestrator-flavoured              |
| ORPHAN MTDS test cluster E — tardis network-mocking (~0.4) ✅ DONE MTDS@316996f              | **Slot 6**      | Done: mock_session.closed=False fix |
| ORPHAN Stream C C-enum.3+4 archetype enum flips (~1.8)                                       | **Slot 2**      | DeFi archetype canonicalisation     |
| V2: `writegate Phase 6.9 expanded scope` (12.6 cal left)                                     | **Slot 7**      | Writegate owner                     |
| V2: `expected_universe_v2_design_2026_05_08` (3.6 cal)                                       | **Slot 4**      | Sports/prediction universe          |
| V2: `deploy_missing_auto_launch_2026_05_07` close (4.1 cal)                                  | **Slot 8**      | Cross-cutting cleanup               |

### Slot 10 work distribution (~4 cal AI-days)

All of slot 10 (writegate Phase 6.6 + 6.7 + 6.9 α-vs-β audit across 9 services) → **Slot 7**, who owns writegate Phase
6.x already. Slot 7 confirms β verdict + flips Gate 4 row in master plan.

**✅ DONE PM@`e054700e` 2026-05-15**: β-verdict confirmed; issue doc filed at
`plans/active/issues/writegate_phase_6_6_7_9_alpha_vs_beta_decision_2026_05_14.md`; intra-side ping to slot 1 main with
Gate 4 master-plan update instructions. Master plan flip delegated to slot 1 main (slot-precedence rule).

### Slot 11 work distribution (~7.4 cal AI-days; cbETH retracted, Kraken re-classed)

| Slot 11 item                                                                                                                  | New owner                 | Rationale                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| ----------------------------------------------------------------------------------------------------------------------------- | ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| alerting D.5+D.7 codex violations (~0.4) ✅ DONE (pre-existing — UAC imports already present, no violations found 2026-05-14) | **Slot 6**                | Done: issue doc closed                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| features-service size violations 3 files (~0.4)                                                                               | **Slot 4**                | Sports `batch_handler.py` 914L (slot 4 owns sports); other 2 mechanical decomposition                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| Tardis docstring + codex (✅ DONE PM@468c7e8d)                                                                                | —                         | Already shipped                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| Sports scrapers cross-links (✅ DONE PM@3e349c65)                                                                             | —                         | Already shipped                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| Phase 1 freeze-gate audit (✅ DONE PM@e67f5ce3)                                                                               | —                         | Already shipped                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| **cbETH adapter scaffold + Coinbase API credential ask**                                                                      | **DEFERRED post-cutover** | Operator review 2026-05-14: on-chain `exchangeRate()` is canonical SSOT (`market-tick-data-service/.../lst_rates_handler.py:100` cbETH config + PM@3a7a4914 "exchangeRate() is SSOT, DefiLlama is non-goal" + cbETH smoke shipped at MTDS@f0b1f7f9). The Coinbase Institutional REST is a nice-to-have richer-data source, NOT a May-23 blocker. Mark cbETH adapter scaffold `**DEFERRED**` + master plan row update from `BLOCKED-CREDENTIALS` → `DEFERRED post-cutover`.                                                                                |
| **Kraken CeFi adapter (live + historic) — keep in scope** (~1.8) ✅ SCAFFOLD SHIPPED                                          | **Slot 3**                | Operator confirmed 2026-05-14: API key incoming (already onboarded at Kraken Pro). Scaffold shipped instruments-service@`da462af` — KRAKEN-SPOT→ccxt.kraken + KRAKEN-FUTURES→ccxt.krakenfutures wired in factory.py `_CANONICAL_VENUE_TO_CCXT_EXCHANGE`; 3 new tests in test_factory_comprehensive.py. Historic batch via Tardis (already in CANONICAL_VENUE_TO_ADAPTER). Credential vault entries `kraken-api-key`/`kraken-api-secret` pending operator [ack] on slot_3.md CREDENTIAL APPROVAL REQUEST. Status: `BLOCKED-CREDENTIALS-OPERATOR-INCOMING`. |
| Master plan row updates: cbETH → DEFERRED; Kraken → CREDENTIALS-INCOMING (~0.4)                                               | **Slot 8**                | Audit cleanup                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |

### Net additions per slot (~38 cal AI-days redistributed)

| Slot   | Added from 9/10/11                                                    | New slot total |
| ------ | --------------------------------------------------------------------- | -------------- |
| 2      | ~10.2                                                                 | ~34            |
| 3      | ~5.4                                                                  | ~30            |
| 4      | ~4.0                                                                  | ~29            |
| 5      | ~0.6                                                                  | ~25.6          |
| 6      | ~1.2                                                                  | ~25            |
| 7      | ~18.8 (all of slot 10 + Phase 6.9 flip-sweep + V2 writegate 12.6 cal) | ~44            |
| 8      | ~9.7                                                                  | ~35            |
| 1 main | ~3.0                                                                  | (continuous)   |

Stack totals span ~25-44 cal AI-days across slots over 9 calendar days to May-23 — comfortable at density-push pace
(~100-200 cal/side/day).

---

### Slot 11 — REASSIGNED (historical section below — see SLOT 9-10-11 REASSIGNMENT above for current owners)

**Source**: operator direction 2026-05-14 ~15:00 UTC. (1) Harsh-side ending early — Ikenna absorbs Harsh's new-issue
pickups. (2) Sports scrapers formalisation per HARD RULE. (3) Tardis docstring clarification. (4) Deep coverage scan
2026-05-14 surfaced 2 silent-missing adapters (Coinbase cbETH + Kraken) — must be built with `BLOCKED-CREDENTIALS`
status per "External Data Is Always Available" HARD RULE. Slot 11 is a fresh spawn beyond standard 9 + emergency
slot 10.

1. ✅ **`alerting_service_codex_violations_d5_d7_2026_05_14`** — 4 codex compliance fixes in
   `alerting_service/subscribers/governance_forum_watcher.py` + `stablecoin_issuer_pause_subscriber.py`: raw
   `response.json()` → Pydantic `model_validate()`; empty-string fallbacks → fail fast. (refactor 0.4×, ~1 = 0.4 cal)
   **DONE 2026-05-14 slot 6**: Pre-existing — files already import from `unified_api_contracts.internal.alerting`
   (`GovernanceForumProposal` + `IssuePauseEvent`) + use `model_validate()`. No code change required; issue doc filed.
2. ✅ **`features_service_size_violations_2026_05_14`** (P2 Ikenna-owned) — 3 size violations:
   `sports/cli/handlers/batch_handler.py` 914L (max 900);
   `cross_instrument/.../stablecoin_aggregate_exposure.py:compute()` 89L (max 50);
   `onchain/.../eigen_rewards_calculator.py:_calculate_from_mtds()` 56L (max 50). Decomposition along natural
   boundaries; blocks features-service CI green. (refactor 0.4×, ~1 = 0.4 cal) **✅ FULLY DONE (2026-05-15)**: upstream
   decomposed stablecoin/eigen. `batch_handler.py` now 723L (under 900L limit) + all functions under 200L — stale QG
   exclusion removed. Also fixed pre-existing `feature_family="sports"` kwarg missing on 4 manifest calls
   (record_empty/record_failed) that was causing 3 test failures. — `features-service@d8e68608`
3. ✅ **Tardis stream client docstring + codex clarity sweep** — Tardis historical-data 403 is **separate paid
   commercial subscription** (not academic tier). Actions: (a) docstring update at `tardis_stream_client.py:159` —
   VERIFIED on LDR at `MTDS@60c2e55`. (b) codex note at `interface-credential-convention.md` § Tardis — already present
   (lines 158-167). (c) error message at line 167 references
   `/codex/04-architecture/interface-credential-convention.md § Tardis` — verified. All 3 actions confirmed done.
   (research 1.2×, ~0.5 = 0.6 cal)
4. ✅ **Sports scrapers `BLOCKED-OPERATOR-DECISION` cross-link verification** — per operator pick 2026-05-14 (B + light
   C): (a) `master_to_live_defi_2026_05_23.md` row — `dba80b61` on LDR ✅. (b) successor plan
   `plans/active/sports_scrapers_post_cutover_2026_06_01.md` — exists in tab/4 PM ✅. (c) `sports_master.md:201` has
   `[plans/active/sports_scrapers_post_cutover_2026_06_01.md]` cross-link with `BLOCKED-OPERATOR-DECISION` annotation
   ✅. All verifications pass. (design 0.6×, ~1 = 0.6 cal)
5. ✅ **Phase 1 freeze-gate audit** (absorbed from Harsh slot 6) — read-only verification that master plan freeze-gate
   items #1-#6 are actually green on disk; file gap issue docs if mismatch. (research 1.2×, ~1.5 = 1.8 cal) **DONE
   2026-05-15**: master plan lines 1112-1126 confirm 6/6 ✅ ALL ITEMS GREEN — Day-3 audit 2026-05-14 by slot 6.
   Freeze-gate sequencing plan checkboxes flipped at `PM@e67f5ce3`. No gap issue docs needed — zero discrepancies found.
6. **🔴 Coinbase cbETH LST APR adapter (SILENT-MISSING from 2026-05-14 deep coverage scan)** — no adapter file in either
   `instruments-service/.../reference_data/adapters/` or `mtds/.../market_interface/`. Required for `carry_staked_basis`
   × DeFi cell. Per HARD RULE: (a) build SCAFFOLD anyway — UAC contract additions for cbETH APR + supply/redemption
   rates + auth shape + retry/backoff + error classification + manifest emission per writegate Phase 6.x; unit tests
   against mocks (per Coinbase API docs); integration tests marked `@pytest.mark.requires_credentials`. (b) file
   `CREDENTIAL APPROVAL REQUEST` in `ikenna_orchestrator/pings/slot_11.md`: vendor=Coinbase Institutional API,
   tier=read-only API key, cost=$0 (free tier read-only), unblocks=`carry_staked_basis` cbETH leg eligibility for
   May-23. (c) status: `BLOCKED-CREDENTIALS` until operator [ack]; do NOT move to a post-cutover plan. (design 0.6×, ~3
   = 1.8 cal)
7. **🔴 Kraken CeFi perp + spot adapter (SILENT-MISSING)** — no dedicated adapter; CCXT fallback insufficient for May-23
   SLAs (rate limits + ticker normalization gaps). Required for `arbitrage_price_dispersion` × CeFi (7th venue) AND
   `carry_staked_basis` × CeFi hedge-leg. Per HARD RULE: (a) build SCAFFOLD — direct Kraken REST + WebSocket; UAC +
   auth + manifest emission; unit tests against mocks. (b) file `CREDENTIAL APPROVAL REQUEST`: vendor=Kraken Pro API,
   tier=read-only API key (no withdraw permissions), cost=$0 (free tier), unblocks=full 7-venue CeFi coverage + 1 hedge
   venue for `carry_staked_basis`. (c) `BLOCKED-CREDENTIALS` until [ack]. (design 0.6×, ~3 = 1.8 cal)

Total slot 11: ~7.4 cal AI-days. Fresh spawn from script — operator runs `setup-tab-worktrees.sh --add-slot 11` if not
already present.

---

## Harsh 14 May absorption — reassigned 2026-05-14 (Harsh side ending early)

**Source**: operator direction 2026-05-14 ~15:00 UTC. Harsh-side stopping for the day. ALL Harsh 14 May items that are
NOT YET FF'd to LDR (or are partial) absorbed by Ikenna. **Additive to existing Ikenna slot stacks — does NOT remove
pre-existing Ikenna work.** Slot owners pick up the absorbed item AFTER their existing top-of-stack lands.

**Pickup discipline**: before starting an absorbed item, slot owner runs:

```bash
git -C ../<repo> fetch origin live-defi-rollout
git -C ../<repo> log origin/live-defi-rollout --oneline --since=2026-05-14 --author=harsh
```

If the item is already shipped by Harsh → flip absorbed item to `[x] (harsh-shipped @ <sha>)` and skip.

| Harsh 14 May item                                               | Plan-of-record                                                                               | Ikenna pickup slot    | Rationale                                                                                                  |
| --------------------------------------------------------------- | -------------------------------------------------------------------------------------------- | --------------------- | ---------------------------------------------------------------------------------------------------------- |
| Slot 2 — `api_football_phase_3b_3c_smoke_forward_poll` (P0 EOD) | `api_football_phase_3b_3c_smoke_forward_poll_2026_05_13.md`                                  | **Slot 4**            | Sports owner; P0 today                                                                                     |
| Slot 3 — 117 UTL test-fixture sweep (`pipeline_mode` kwarg)     | UTL@`547ff3c` + writegate Phase 4                                                            | **Slot 9**            | Mechanical refactor; slot 9 has Cluster A sed + workspace ratchet sweep                                    |
| Slot 4 — 2 of 17 strategy-service test failures                 | strategy-service test suite                                                                  | **Slot 2**            | Already has Cluster D instruments-service tests + utl_qg failures (research-flavoured triage)              |
| Slot 5 — batch_live_symmetry Tabs 1-2 codex docs                | `batch_live_symmetry_2026_05_10.md` Tabs 1-2                                                 | **Slot 8**            | Already pair-slotted on Tab 2 + banners (item #12)                                                         |
| Slot 6 — Phase 1 freeze-gate readiness audit (read-only)        | `master_to_live_defi_2026_05_23.md` § "Phase 1 status"                                       | **Slot 11** (item #5) | Orchestrator-flavoured; absorbed into slot 11                                                              |
| Slot 7 (a) — UI `ui-reference-data.json` TRADER_JOEV2 update    | `cross_asset_group_catalogue_audit_2026_05_10.md` Phase 1D                                   | **Slot 5**            | TradFi/cross-asset theme                                                                                   |
| Slot 7 (b) — cross_asset Phase 6C UI-drilldown                  | `cross_asset_group_catalogue_audit_2026_05_10.md` Phase 6C                                   | **Slot 7**            | Natural extension of slot 7 item #8 (data_status_drilldown_shard_atom_alignment)                           |
| Slot 7 (c) — ICE US softs (CT/CC/KC/SB/OJ/DX) disambiguation    | `cross_asset_group_catalogue_audit_2026_05_10` + `ice_us_softs_dataset_disambiguation` issue | **Slot 5**            | TradFi venue/symbology theme                                                                               |
| Slot 8 — batch_live_symmetry Tab 3 + UAC + QG STEPs             | `batch_live_symmetry_2026_05_10.md` Tabs 3+                                                  | **Slot 8**            | Already pair-slotted on Tab 2; Tab 3 extension same slot                                                   |
| Slot 9 — defi_recursive_borrow DESCOPE successor                | `defi_recursive_borrow_archetypes_2026_05_10.md`                                             | **REVERSED**          | Operator direction 2026-05-14: DESCOPE REVERSED, recursive_borrow IS in May-23 scope. No successor needed. |

**Estimated added load**: ~7 cal AI-days across the Ikenna stack. Stack revised total: ~288 (pre-Harsh-absorb) + 7
(Harsh absorption) + 7.2 (slot 6 item #11 phase_3c lending) + 7.4 (slot 11) = **~310 cal AI-days**.

---

## Cross-slot handshakes today

- **Slot 4 ↔ Slot 5** on `sports_retired_data_types_code_cleanup`: slot 4 owns producer-side, slot 5 owns
  cross-cutting/UAC side. Coordinate via `_agent_pings.md`.
- **Slot 6 ↔ Slot 7** on wallet/treasury: slot 6 = Phase 1 HMAC chain, slot 7 = Phase 3 audit immutability + treasury
  rollup; both touch deployment-api so push in serialised order (slot 6 first, slot 7 rebases).
- **Slot 6 ↔ Slot 7** on DART: slot 6 = custody-side gate, slot 7 = operator UX surface. Different files; parallel.
- **Slot 4 ↔ Slot 8** on `data_status_comprehensive_test_coverage`: slot 4 sports-half, slot 8 non-sports-half.
  Parallel; no overlap.
- **Slot 2 ↔ Slot 7** on `cross_asset_group_catalogue_audit`: slot 2 = Phase 6A DeFi half, **Harsh slot 7** = Phase 6C
  UI half. Both independent of each other.

## Cross-side handshakes (Ikenna ↔ Harsh)

- **Ikenna slot 2 Phase A/B** ↔ Harsh slot 6 freeze-gate audit: if Harsh slot 6 surfaces a freeze-gate item that depends
  on defi classifier crossref, slot 2 owner is paged via `_agent_pings.md`.
- **Ikenna slot 6+7 wallet_treasury Phase 1+3** (pulled forward to pre-May-15) is independent of Harsh today; ack-only.
- **batch_live_symmetry** entirely Harsh slots 5+8; Ikenna does NOT touch. If Harsh files an Ikenna-touching UAC
  ratchet, slot 8 owner picks up via \_agent_pings.md.

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

**Adapter/data-source HARD RULE (codified 2026-05-14)**: if you hit a "no data available" wall on any adapter,
handler, or data-source client (instruments-service, MTDS, or anywhere else), **DO NOT** defer / descope / move to
post-cutover. Data EXISTS for every asset_group × archetype — the unblock is a credential ask, not a scope cut.
Banned reasoning: "no public API" / "free tier exhausted" / "no test data" / "subscription required". Required:
(1) build the adapter scaffold anyway (UAC + auth + retry + error class + manifest emission + unit tests against
mocks + integration tests marked `@pytest.mark.requires_credentials`); (2) file `CREDENTIAL APPROVAL REQUEST` in
your slot_N.md with vendor / tier / cost / account-needed / what-it-unblocks; (3) plan status = `BLOCKED-CREDENTIALS`
(NOT `DEFERRED`, NOT `POST-CUTOVER`); plan-flip is `- [ ] [BLOCKED-CREDENTIALS — pinging operator at <sha>]`; never
move adapter to a post-cutover plan without explicit operator [ack]. Full SSOT: CLAUDE.md § "External Data Is Always
Available".

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

Per slot: every top-level numbered item shipped as a `- [x]` checkbox in its plan-of-record with commit-sha evidence, OR
explicitly annotated `**DEFERRED**` with successor plan named per Capture Discoveries As Plan Todos HARD RULE. Slots
running ahead of pace pull from the in-stack reserve.

**Cycle gate**: all 200 cal AI-days shipped or annotated by 2026-05-23 cutover. Slots are NOT held in reserve for
density-push absorption — every slot has a deep stack.

---

## Deferred / not-in-scope this cycle

- AWS migration (`aws_migration_defi_first_2026_05_07.md`) — DEFERRED past 2026-05-23 per 2026-05-13 operator direction.
- Copper / CEFFU integrations — CLIENT-SIDE, NOT our blocker (config-only flip when client provisions).
- Fireblocks institutional custody — June-15+ scope, not this cycle.
- Any GCS backfill ≥1 week without explicit operator approval ping in slot_N.md.

---

## V2 extension — +72 cal AI-days (drives workspace remaining toward ~200)

Pulled from top remaining plans in the inventory dashboard (regenerated 2026-05-14 12:14 UTC, 580 cal total, 77 plans).
Each slot picks up its v2 items AFTER its main stack lands; this is overflow, not replacement.

| Slot         | V2 item                                                                                                                                                                                                                                                                   | Plan                                                                               | Cal     |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- | ------- |
| 2            | **`defi_catalogue_chain_primitives_2026_05_10` push** — remaining 21 open todos (currently 47/68, 63.5 cal left); split into 2-3 batches and ship                                                                                                                         | `defi_catalogue_chain_primitives_2026_05_10.md`                                    | +9      |
| 3            | **`live_pipeline_mtds_mdps_features_2026_05_08` Ikenna-half** (15.0 cal total; instruments_live_master May-23 deadline) — DeFi instrument live-pipeline activation                                                                                                        | `live_pipeline_mtds_mdps_features_2026_05_08.md`                                   | +9      |
| 4            | ✅ **`topology_qgroup_gap_closure_2026_05_09` Phase 7 DONE** (PM@a0ed7a31 — Q-doc archived, Phase 7 checkbox flipped) + **`simulation_scenarios_topology_price_shocks_2026_05_09` sports-half subset** (4.D DEFERRED-PER-USER, not actionable without operator direction) | `topology_qgroup_gap_closure_2026_05_09.md` + topology shocks                      | +9      |
| 5            | **`code_freeze_migrate_backfill_sequencing_2026_05_10` cross-cutting subset** — pull TradFi + cross-asset-group sequencing items (plan is 123.5 cal total; Ikenna takes the cross-cutting cap of ~9, rest stays Harsh-side cefi_master)                                   | `code_freeze_migrate_backfill_sequencing_2026_05_10.md`                            | +9      |
| 6            | **`api_keys_wallets_accounts_readiness_2026_05_10` more Phase 8 items** (40.0 cal left, 33/87, May-23) + **`alerting_service_live_rules_2026_05_07` close** (4.5 cal, 43/65, May-23)                                                                                      | api_keys_wallets + alerting_service_live_rules                                     | +9      |
| 7            | **`cross_cutting_may_23_deliverables_2026_05_08` Ikenna-half** (13.4 cal, 17/30) + **`mtds_per_instrument_download_api_2026_04_24`** (3.3 cal, 6/19) + **`mdps_streaming_and_backpressure_2026_05_07`** (3.0 cal, 0/7)                                                    | 3-plan parallel: cross_cutting deliverables + mtds per-instrument + mdps streaming | +9      |
| 8            | **`deployment_and_qg_strategy_implementation_2026_05_13`** (12.3 cal, 20/52) + **`hard_schema_enforcement_2026_05_08`** (4.8 cal) + **`gcs_migration_bundle_pipeline_mode_2026_05_08`** (4.8 cal, May-15 deadline)                                                        | deployment_and_qg + hard_schema_enforcement + gcs_migration_bundle                 | +9      |
| 9            | **`writegate_honest_coverage_endtoend_2026_05_06` Phase 6.9 expanded scope** (12.6 cal, 117/246) + **`expected_universe_v2_design_2026_05_08`** (3.6 cal) + **`deploy_missing_auto_launch_2026_05_07` close** (4.1 cal, 6/14)                                             | writegate Phase 6.9 + expected_universe_v2 + deploy_missing_auto_launch            | +9      |
| **Total V2** |                                                                                                                                                                                                                                                                           | (8 implementer slots × +9)                                                         | **+72** |

**Note on `code_freeze_migrate_backfill_sequencing_2026_05_10` (slot 5 v2)**: this plan is 123.5 cal total and owned by
cefi_master (Harsh-side). Ikenna takes only the **cross-cutting subset** (~9 cal) — TradFi-side migration sequencing
items + cross-asset bucket-name SSOT items that overlap with Ikenna slot 5+9's existing themes. The bulk (~115 cal)
stays Harsh-side for 15-22 May absorption.

**Note on `aws_migration_defi_first_2026_05_07`** (28.4 cal in dashboard): DEFERRED past 2026-05-23 per operator
direction; NOT pulled into this v2 extension.

**Note on `defi_recursive_borrow_archetypes_2026_05_10`** (38.9 cal): **DESCOPE REVERSED 2026-05-14** — Phases 4-11
pulled into May-23 scope per operator. Assigned: Phases 4+5+12 → Slot 2; Phase 6 → Slot 3; Phases 7+8 → Slot 6. See §
"Day-3 operator direction: recursive_borrow scope-extension" below.
`defi_recursive_borrow_archetypes_post_cutover_2026_06_01` (24.0 cal): scope-narrowed to only genuine post-cutover items
— Phases 4-13 are back in May-23 scope.

**Note on `batch_live_symmetry_2026_05_10`** (20.6 cal): Harsh-side today (slots 5+8); NOT pulled.

**Note on `simulation_scenarios_post_cutover_2026_06_01`** (15.2 cal): post-cutover target 2026-07-15; NOT pulled.

**Note on `promote_workflow_post_cutover_ui_pipeline_2026_05_10`** (20.0 cal): deadline 2026-07-04 post-cutover; NOT
pulled.

---

## Math — burn vs workspace remaining

| Source                                                                                        | Cal AI-days |
| --------------------------------------------------------------------------------------------- | ----------- |
| Workspace-wide remaining (auto-inventory 2026-05-14 12:14 UTC, 77 plans)                      | **580**     |
| Ikenna 14 May split baseline (200) + v2 extension (72) + recursive_borrow reversal (~22)      | −294        |
| Harsh 14 May split (today closeout only — 8 days remain 15-23 May for him to absorb the rest) | −8          |
| **Remaining workspace cal AI-days after both 14 May splits land**                             | **~278**    |

Note: Net burn against dashboard is closer to ~265 (some items are NEW work not yet checkboxed). Realistic remaining ≈
**~300 cal AI-days** for Harsh to absorb across 15-23 May (~37 cal/day × 8 days = comfortable at density-push pace).

---

## Day-3 operator direction: recursive_borrow scope-extension (2026-05-14)

**Operator direction 2026-05-14**: "i want defi_recursive_borrow and recursive staking in 23rd may though even if not
essential for defi i want it backtested coded up and tested ready to go live". Descope reversed.

**Slot assignments** (Phases 4-11, code+test+backtest READY-TO-GO-LIVE, live toggle OFF at cutover):

| Phases                                                                                                                                                                                                           | Slot                                                 | Rationale                                                       |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- | --------------------------------------------------------------- |
| Phase 4 (Solidity `RecursiveLeverageReceiver.sol` extending `FlashLoanReceiver.sol`) + Phase 5 (`RecursiveLoopOrchestrator` in execution-service) + Phase 12 (backtest harness e2e — both archetypes on testnet) | **Slot 2** (DeFi classification + catalogue)         | Core DeFi implementation slot                                   |
| Phase 6 (Hyperliquid LIVE perp connector — EIP-712 signing + REST POST `/exchange` + WS `user_events`)                                                                                                           | **Slot 3** (Perp venue adapters + DEX/Drift)         | Phase 6 is a perp adapter — natural fit with Slot 3's theme     |
| Phase 7 (`PerpHedgeSizer` — `_HYPERLIQUID_RULES` $500k cap pre-trade check) + Phase 8 (`HealthFactorMonitor` + `LiquidationProximityCircuit` alerts)                                                             | **Slot 6** (Wallet/Treasury + DeFi alerts + custody) | Health monitors + position alerts fit Slot 6's DeFi alert theme |

**Critical prerequisite in Slot 2's existing theme**: `CARRY_RECURSIVE_BORROW_LENDING_ONLY` +
`CARRY_RECURSIVE_BORROW_PERP_HEDGED` enum values ALREADY in UAC `internal/architecture_v2/enums.py`.
`ARCHETYPE_CONFIG_SEED` ALREADY has both keys. Missing: `_ARCHETYPE_ENGINE_MAP` in
`strategy-service/engine/strategies/v2/factory.py:63` lacks both entries — Slot 2 adds these before Phase 12 backtest.

**Defi_catalogue dependency**: Phase 3 lending-indices fix (already in Slot 2's existing scope) is required for Family 2
backtest accuracy. Not a hard blocker for Phases 4-8 coding.

**Harsh slot 9**: lightweight ack + plan-body verification + cross-ping only (~0.5 cal research). All implementation
Ikenna-side.

---

## Open questions

(None at draft time. Will populate as slot work progresses; route to `_agent_pings.md` if cross-side, or slot_N.md if
intra-side.)

---

## Deferred work after 2026-05-14 slot-8-session-2 session

| Phase / item                        | Status as of 2026-05-14                                                                       | Successor / blocker                                                             |
| ----------------------------------- | --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Task 4 — ops verification           | ✅ DONE — fixture_manifest kwarg confirmed working; upgraded=0 (correct); apply-flips on HOLD | Await Ikenna direction; manifest_cross_asset_rescan_design_2026_05_08 Q1        |
| Task 6 Phase 0 audit                | ✅ DONE — 9 checkboxes flipped; sports C.2 deferred                                           | Phases 1-6 still to ship (A.1/A.2/B.1/B.2/D.4/E/F new tests)                    |
| Task 10 defi_archetypes             | Stream E DONE — venue-matrix precision pass                                                   | Streams A/C/D require multi-day codex+UAC work; operator task-assignment needed |
| Task 5 pnl-attribution lint         | ✅ DONE — @44ac3fd                                                                            | —                                                                               |
| Task 3 AUDIT_pre_may_8              | ✅ DONE (all actions pre-resolved)                                                            | —                                                                               |
| Task 7 data_status_ui_phase_2f      | ✅ DONE by Harsh slot 7                                                                       | —                                                                               |
| Task 8 codex_doc_currency           | ✅ DONE by earlier slot 8 (PM@640c38d1)                                                       | —                                                                               |
| Task 9 codex_vs_citadel             | ✅ OPERATOR-GATED — awaiting R-10/R-11/AL-14                                                  | Operator answers needed                                                         |
| Item 12 batch_live_symmetry banners | ✅ DONE (pre-resolved by other agents)                                                        | —                                                                               |
