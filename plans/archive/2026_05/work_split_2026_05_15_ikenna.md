---
doc_type: plan
title: Ikenna's daily work-split — 2026-05-15 (Day-4, ~150 cal AI-days, post-freeze-gate cycle)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, client-reporting-api, deployment-api, deployment-service, deployment-ui, execution-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-15
type: coordination-doc
deadline: 2026-05-23 (live DeFi cutover)
horizon: ~8 calendar days (15 May → 23 May); ~150 cal AI-days across 8 implementer slots
companion_to: plans/active/work_split_2026_05_14_ikenna.md
locked_by: live-defi-rollout
locked_since: 2026-05-15
---

## Deferred work — migrated to:

See inline `DEFERRED-OPERATOR` / `DEFERRED-OTHER-SLOT` / `DEFERRED-INDEFINITELY` / `DEFERRED-POST-CUTOVER` / etc.
annotations next to each open item in body for the specific successor / blocker per-item. No single migration target —
this plan tracks multiple per-item dispositions. 2026-05-19 slot 2 audit: completed 2026-05-15 cycle doc.

# Ikenna's daily work-split — 2026-05-15

> **Cycle context**: Day-4 of the density push. Phase 1 freeze gate fired 2026-05-15. This split **continues from 14
> May** — absorbs every unfinished 14 May item across slots 2/4/5/6/7/8 + folded-in slot 9/10/11 carry-overs + 3 new
> top-priority items surfaced today. ~150 cal AI-days across 8 implementer slots (avg ~19 cal/slot).
>
> **Stream C P1 archetype docs** (7 docs) — operator direction 2026-05-15: pull back from post-cutover deferral ("its
> just docs, why not"). Routed slot 2 below.

---

## Hard rules baked into this split (carry-over from 14 May)

1. **External Data Is Always Available — Never Silently Defer Adapters (HARD RULE codified 2026-05-14)**: if any adapter
   hits "no data" wall, file `CREDENTIAL APPROVAL REQUEST` in slot pings; status `BLOCKED-CREDENTIALS`; adapter
   scaffold + unit tests still ship. NEVER move to post-cutover plan without operator [ack].
2. **GCS backfill approval gate**: ≥1 week backfill = operator approval ping first. <1 week = pre-authorized.
3. **Singleton-locked + watchdog-registered launchers only** — no fire-and-forget VMs. STARTED within 60s + ≥1 progress
   event/hour + STOPPED at exit.
4. **Half-1 + Half-2 plan-flip discipline (HARD RULE strengthened 2026-05-15)**: every shippable unit = (a) commit +
   push code, then (b) flip the checkbox to checked in the SAME AGENT TURN with `docs(plans):` prefix. Two consecutive
   code commits without a sibling docs(plans) flip = rule violation. Reference incident: slots 5+7 each shipped 15+
   items unflipped on 14 May → dashboard reported 14.5% when real was ~70%. See CLAUDE.md § "Commit + Push + Flip Plan
   Checkboxes".
5. **DeFi recursive borrow Phases 4-11 IN-SCOPE** (operator direction 2026-05-14, DESCOPE REVERSED).
6. **Wallet/Treasury Phase 2** (Copper / CEFFU): CLIENT-SIDE — not our blocker.

---

## Slot stack — ~150 cal AI-days across 8 implementer slots

| Slot            | Theme                                                                                                   | Cal AI-days |
| --------------- | ------------------------------------------------------------------------------------------------------- | ----------- |
| 1               | Main orchestrator (continuous, uncounted)                                                               | —           |
| 2               | DeFi catalogue closure + Helius wire-in + Stream C P1 archetype docs + Polymarket                       | ~20         |
| 3               | Perp venue gaps + Solana adapter expansion + Kraken live + arbitrage_price_dispersion finalisation      | ~18         |
| 4               | Sports classifier + propagation + 6-bucket provisioning + expected_universe_v2                          | ~19         |
| 5               | TradFi backfills + master refresh + Phase 5 QG ratchet + strategy LTV thresholds                        | ~20         |
| 6               | **manifest v8 Phase 6+7 (May-13-15 op-gated)** + phase_3c lending model + alerting                      | ~22         |
| 7               | **SIT critical-path scenarios (May-23 BLOCKER)** + basefc paradigm + audit_records + writegate finalize | ~28         |
| 8               | B-015 smoke re-launch + solana_defi venue naming + audit close + governance                             | ~18         |
| **Total**       | (8 implementer slots)                                                                                   | **~145**    |
| **+ buffer**    | (in-stack reserve per slot for surfacing issues)                                                        | **+5**      |
| **Grand total** |                                                                                                         | **~150**    |

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
`wave2_polymarket_record_captured_from_counts_2026_05_09` + Stream C P1 archetype docs (pulled from post-cutover per
2026-05-15 operator) + Helius `mev_apy` integration (credentials just landed) + `cme_polymarket_arb_2026_05_08` (carry
from slot 9 reassignment) + `cross_asset_group_catalogue_audit` Phase 6A DeFi remainder.

1. ✅ **Helius `native_staking` mev_apy integration** — DONE (MTDS@4cea371): added `_fetch_jito_mev_apy()` querying
   public Jito Kobe `/api/v1/mev_rewards`; formula `mev_reward_per_lamport * epochs_per_year`. Per-validator rows now
   emit `total_apy = base_apy + mev_apy * (1 - commission_pct)`. 5 unit tests + 1 `@pytest.mark.requires_credentials`
   live integration test (17 pass, 1 skipped). Live verification 2026-05-16 epoch 972: base=3.58% mev=0.12% total=3.69%
   for top validator at 7% commission. Helius RPC returned 200 vote_accounts. (infra 0.8×, ~3 = 2.4 cal)
2. ✅ **Stream C P1 — 7 remaining archetype docs** — DONE (PM@8bcf0f96). LegController integration sections added to
   carry-basis-dated, carry-recursive-borrow-lending-only (SHIPPED status), carry-recursive-borrow-perp-hedged
   (SHIPPED), yield-staking-simple, yield-rotation-lending, liquidation-capture, defi-lp-pool. Pattern matches the 4 P0
   docs from PM@552a3e6e. Closes Stream C P1 from `defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`.
   (refactor 0.4×, ~5 = 2.0 cal)
3. **`defi_catalogue_chain_primitives_2026_05_10` close-out** — 18 remaining open todos (chain-primitive UAC schema
   additions + downstream MTDS/features wiring). (design 0.6×, ~8 = 4.8 cal)
4. ✅ **`wave2_polymarket_record_captured_from_counts` Polymarket subset** (carry from 14 May) — **VERIFIED-DONE
   2026-05-16 by slot 2**: full plan is `status: done` across Phases 1-5 (UTL@`446d75ce` deprecation banner,
   MTDS@`616ac15` callsite migration, PM@`ce40d8ab` QG STEP 5.73, PM@`d93a9952` codex). Zero open todos in plan body;
   bookkeeping-only flip. (research 1.2×, ~3 = 3.6 cal)
5. 🟡 **`cme_polymarket_arb_2026_05_08` close-out** (carry from slot 9 reassignment 14 May) — **STATUS 2026-05-16 by
   slot 2**: Phase 1 ✅ (UAC@`b95d146` EVENT_CONTRACT enum); Phase 2 🟡 BLOCKED-UPSTREAM on
   `predictions_canonical_question_group_polymarket_migration_2026_05_06` Phase 5 (epic 38% done — ECRTY/ECYM/ECGC/
   ECCL/ECNG/EC6E canonical-question-groups not yet shipped); Phases 3-5 todo (sequential multi-repo plumbing, ~12 cal
   AI-days brand-new design); codex stub ✅. **DEFERRED — post-May-23 critical path per plan overview**; named successor
   = this plan itself. 1.8 cal-day budget insufficient for Phases 3-5; status-update flip only. (design 0.6×, ~3 = 1.8
   cal)
6. ✅ **`cross_asset_group_catalogue_audit` Phase 6A DeFi half remainder** — **VERIFIED-DONE 2026-05-16 by slot 2**:
   plan body Phase 6A (line 469) is already `[x]` ("Workspace-grep audit post-Phase-1"). Sole open todo (line 554, ICE
   US softs UAC capability_declarations entry) is TradFi-side (slot 5 owns); slot 5's 2026-05-16 audit confirmed ICE
   softs symbology + instrument_universe canonicalised at `tradfi_roots.py:242-247`. No DeFi-half remainder; issue doc
   `ice_us_softs_dataset_disambiguation_2026_05_14.md` is operator-decision-pending, not slot-2 territory. (research
   1.2×, ~2 = 2.4 cal)
7. 🟡 **`cross_asset_instruments_service_scope` triage** (carry from slot 9 reassignment) — **DONE 2026-05-15 by slot
   2** (per issue doc § "Architecture recommendation"): triage written recommending **Option 1 — extend instruments-
   service with CROSS_ASSET shard**. Status `BLOCKED-OPERATOR-DECISION`; not May-23 blocking (P2; features-service
   handles cross_asset data production). 4-item implementation gate written. Awaiting operator [ack] on Option 1 vs
   alternatives. No further triage work needed. (research 1.2×, ~2 = 2.4 cal)
8. ✅ **🔴 [TOP-PRIORITY 2026-05-16 — B-015 ARCHITECTURAL UNBLOCK] B-015 Smoke B Option A — SHIPPED 2026-05-16 by slot
   2** at `features-service@550cdaba`. `DependencyChecker` in
   `features-service/features_service/onchain/app/core/dependency_checker.py` now dispatches asset_group-aware:
   - **DEFI**: uses new `UPSTREAM_DEPS_DEFI` ClassVar — MDPS processed_candles becomes `required: False`; adds
     `market-tick-data-service-vault-share-price` bypass probing `raw_tick_data/by_date/day={date}/` with
     `substring="data_type=vault_share_price"`; adds `market-tick-data-service-lst-rates` bypass to
     `lst-rates-{project_id}` bucket; keeps existing lending/oracle/perp bypass entries.
   - **CEFI/TRADFI**: unchanged (UPSTREAM_DEPS with MDPS `required: True`).
   - **test_mode DEFI**: falls back to default (test buckets are unified per QG plumbing).
   - 7 new unit tests in `TestDefiPreflightBypassesMdps`; 38/38 onchain routing tests green; basedpyright 0 errors.
     Cross-ping to Harsh slot 9 filed at `plans/active/_agent_pings.md` § 2026-05-16 — Smoke B re-launch unblocked.
     Issue doc `b_015_smoke_b_mdps_handler_gap_vault_share_price_2026_05_16.md` flipped to RESOLVED. (design 0.6×, ~5 =
     3.0 cal)
9. **Reserve**: in-stack pickup for new DeFi classification surfacings.

---

### Slot 3 — Perp venues + Solana expansion + Kraken live + APD finalisation — ~18 cal AI-days

Plan fan-out: `emerging_perp_venue_adapters_broken` remainder + Solana DEX adapter expansion (Phoenix / Orca / Raydium /
Drift) + Kraken live REST+WS integration (credentials in vault) + `arbitrage_price_dispersion_finalisation_2026_05_09`
(carry from slot 9 reassignment).

1. ✅ **Kraken CeFi live REST + WS integration** — credentials vaulted (`bybit_api_key`/`bybit_api_secret` v2
   authenticated 2026-05-15 with Spot + Derivatives perms; also Kraken testnet API onboarded). Wire `KrakenCeFiAdapter`
   scaffold from `execution-service@4d4d8e12d` to live data flow. (infra 0.8×, ~3 = 2.4 cal) **PARTIAL 2026-05-15
   (slot-3)**: `execution-service@d1f336148` — `fetch_ticker()` wired to live Kraken REST via aiohttp transport
   (`_do_public_get` + `set_http_session` + `aclose`). 3 new tests pass. basedpyright clean.
   `execution-service@3a511f1b9` — `get_account_state()` wired via `_do_private_post()` helper (HMAC-SHA512 signed POST
   to `/0/private/Balance`); 2 new tests pass. `execution-service@6e5747366` — `place_order` + `cancel_order` +
   `get_order_status` all wired live: AddOrder/CancelOrder/QueryOrders endpoints, new `_parse_kraken_order_dict()`
   helper (status/side/order-type/partial-fill mapping), 5 more tests (38 total). `execution-service@4722026b4` —
   `get_fills` (TradesHistory + client-side ordertxid filter, new `_parse_kraken_trade_dict()`) + `get_positions`
   (OpenPositions, LONG/SHORT side, entry_price + mark_price + unrealized_pnl) live; 4 more tests (42 total).
   `execution-service@70a851e4e` — `get_margin_state` (TradeBalance) live: total_collateral/total_debt/
   available_margin/margin_level parsed; ml% → ratio conversion. 1 more test (43 total). **8 of 8 private REST methods +
   public Ticker LIVE.** `execution-service@266d369f1` — Kraken WebSocket client scaffold shipped:
   `KrakenWebSocketClient` subscribes to wss://ws.kraken.com/v2 ticker channel, exponential-backoff reconnect,
   per-symbol stale tracking (last_message_at/update_count), TickerCallback dispatch. 9 new tests. basedpyright clean.
   Public WS DONE. Private WS streams (own_trades, openOrders) are a follow-up — need GetWebSocketsToken REST call gate;
   deferred to a successor commit (filed as in-scope, not blocked).
2. ✅ **Solana DEX adapter expansion — Phoenix / Orca / Raydium / Drift** — extend MTDS DeFi handlers per `defi_master`
   venue matrix. (design 0.6×, ~5 = 3.0 cal) **FULLY DONE 2026-05-16 (slot-3)**: Drift/Orca/Raydium already wired in
   `market-tick-data-service/market_tick_data_service/cli/handlers/solana_defi_handler.py`. Phoenix: shipped
   `MTDS@696f188` — Phoenix's own REST is dead (DNS unresolved), but on-chain program alive per Jupiter registry.
   `_collect_phoenix()` queries `lite-api.jup.ag/swap/v1/quote?dexes=Phoenix` for 3 major pairs (SOL/USDC, WBTC/USDC,
   WBTC/SOL) → per-pair price + price_impact + USD value + context_slot. 3 new tests pass (51 total in file). Phoenix
   BLOCKED-OPERATOR-DECISION lifted — Jupiter free tier suffices, no operator credential ask.
3. ✅ **`emerging_perp_venue_adapters_broken` remainder** — close remaining broken-venue items per Day-3 status.
   (research 1.2×, ~2 = 2.4 cal) **DONE 2026-05-15 (slot-3)**: snapshot added to issue doc — 3/5 venues fixed (ASTER
   adapter, HYPERLIQUID/LIGHTER/PACIFICA via reconciler + MTDS wiring); 2 operator-blocked (ASTER backfill VM
   approval >1 week + EXTENDED-STARKNET canonical API URL). Issue doc:
   `plans/active/issues/emerging_perp_venue_adapters_broken_2026_05_13.md` § "UPDATE 2026-05-15".
4. ✅ **`arbitrage_price_dispersion_finalisation_2026_05_09`** (carry from slot 9 reassignment) — push remaining
   finalisation items. (design 0.6×, ~4 = 2.4 cal) **ALREADY DONE 14 May, archived 2026-05-15 by slot-3**: 20/20 todos
   shipped 2026-05-09/10. Plan moved to `plans/archive/arbitrage_price_dispersion_finalisation_2026_05_09.md` yesterday.
   Only deferred item: live cutover dry-run → tracked in `master_to_live_defi_2026_05_23.md` Group F item 17.
5. ✅ **Hyperliquid arb_price_dispersion eligibility close** — verify USDC-margin + 7-venue dispersion universe.
   (research 1.2×, ~2 = 2.4 cal) **DONE 2026-05-15 (slot-3)**: 14 May session shipped UAC@052120d (HYPERLIQUID+ASTER in
   VENUE_DATA_TYPE_CAPABILITIES) + strategy-service@c7a3f92 (4 eligibility tests). Verified 7-venue dispersion universe
   in `strategy-service/.../target_universe/catalog.py:623-631`: `hyperliquid` + `deribit` + `aster` + `kraken` +
   `binance` + `bybit` + `okx` — all 7 wired with ShareClass marker (USDC/USDT). HL specifically: USDC margin, 0 haircut
   → eligible.
6. ✅ **`helius_solana_rpc_for_validation` final close** (credentials now in vault — last wire-up). (infra 0.8×, ~2 =
   1.6 cal) **DONE 2026-05-15 (slot-3)**: yesterday's `execution-service@a300f7c` shipped Helius Solana RPC dispatch for
   SOLANA_CLMM + SOLANA_AMM shapes in `capture_golden_swaps.py` (18 helius references confirmed). Operator provisioned
   `helius-api-key` vault entry 2026-05-15; slot 2 owns mev_apy integration; slot 3 wire-up already on LDR.
7. ✅ **Aster + Bybit UTA `carry_staked_basis` LST_AS_MARGIN final** — eligibility-matrix close. (research 1.2×, ~2 =
   2.4 cal) **DONE 2026-05-14 (slot-3)**: `strategy-service@ab8661e` — ASTER=no LST (USDC/USDT-only, ineligible), BYBIT
   UTA stETH=True (10% haircut) → `lido-bybit` slot unlocked; `TestAsterBybitUtaLstEligibility` test class added.
   Eligibility matrix sealed.
8. ✅ **Kraken WebSocket implementation (Option 2 — operator-confirmed KEEP IN SCOPE)** — REST coverage shipped 100%
   (8/8 private + Ticker + 43 tests); WS now in scope for May-23. **DONE 2026-05-16 (slot-3)**: all 3 coverage gaps
   closed. (a) sub-200ms fill confirmation for `get_fills` — `KrakenPrivateWebSocketClient` on
   `wss://ws-auth.kraken.com/v2` `executions` channel, token-gated via `KrakenCeFiAdapter.get_websockets_token()`
   (`execution-service@954f87205`). Token-supplier callback refreshed on each (re)connect. (b) order-book depth
   subscription for `get_orderbook` — `KrakenBookWebSocketClient` on `wss://ws.kraken.com/v2` `book` channel, depth ∈
   {10,25,100,500,1000} (`execution-service@2355b3a70`). Emits `BookSnapshot` with `is_snapshot` flag + checksum so
   callers can validate local book state. (c) rate-limit pressure — both private + book streams + the public ticker
   stream from `266d369f1` together remove the REST poll loop for fills/orderbook/ticker, satisfying the
   rate-limit-relief criterion. Test totals: 29 in `test_kraken_ws_client.py` (16 ticker/private + 13 book) — all green.
   basedpyright clean.
9. **Reserve**: in-stack pickup for any Solana RPC ratelimit handling.

---

### Slot 4 — Sports classifier + propagation + 6-bucket + universe — ~19 cal AI-days

Plan fan-out: 3 sports classifier issues final close-out + propagation chain Phase 3.1-3.N + 6-bucket provisioning
(re-activate from DEFERRED) + `expected_universe_v2_design` (carry from slot 9 reassignment) + sports/prediction phantom
apply-flips remainder + `api_football_minimal_flattening_removal_2026_05_07`.

1. ✅ **6-bucket provisioning re-activate** (carry from 14 May DEFERRED item #5) — sports/prediction bucket provisioning
   per `bucket_name_ssot_canonicalisation` env-aware matrix. Re-evaluate deferral reason; if blocker resolved, ship.
   (infra 0.8×, ~3 = 2.4 cal) — **SHIPPED 2026-05-16 (slot 4)**: actual on-cloud state inspection refuted yesterday's
   "BLOCKED-UPSTREAM" assumption. **GCP**: all 6 env-tiered buckets already provisioned at unknown earlier date —
   `gs://features-{sports,pred}-{dev,prd,stg}-central-element-323112` (`gcloud storage ls` 2026-05-16 12:58 UTC confirms
   all 6 + legacy flat `features-sports-central-element-323112`). **AWS**: 0/6 env-tiered buckets existed pre-session;
   slot-4 created all 6 via `aws s3api create-bucket` (region ap-northeast-1; matches code_freeze Phase 2.6.1 region
   SSOT): `unified-trading-features-{sports,pred}-{prd,stg,dev}-427895769566` (timestamps 2026-05-16 12:59:16-33 UTC).
   Verified via `aws s3 ls`. Phase 2.6 fleet provisioning (Harsh slot 4) covers the OTHER ~290 buckets; sports +
   prediction features-\* shipped here as a discrete subset per CLAUDE.md "Plans Run To Actual Completion" HARD RULE +
   ADC admin perms on both clouds. (No PM commit needed — pure infra op; this flip captures the operational evidence.)
2. ✅ **`expected_unattempted_propagation_gap` P1** — close remaining propagation cascade. (research 1.2×, ~3 = 3.6 cal)
   — **VERIFIED 2026-05-16 (slot 4)**: Gate 1 🟢 FIRED 2026-05-13 per
   `expected_unattempted_propagation_chain_2026_05_12.md` line 773. P1 scope is contained in Phase 3+4+PART C all
   complete (3 substantive + 3 NO-OP). Two P2 follow-ups remain `**DEFERRED**` post-cutover (DeFi classifier UAC-enum
   crossref test; sports classifier `EXPECTED_PAUSED_LEAGUE` + `EXPECTED_PRE_SEASON` reasons) — both already tracked at
   plan body lines 775-780 with named successor issue docs. No slot 4 implementer surface here.
3. ✅ **Sports/prediction phantom apply-flips remainder** (sports/pred 16.8% + 0.49% phantoms per 2026-05-12 audit) —
   reconcile + apply-flips on same-region GCE VM. (infra 0.8×, ~2 = 1.6 cal) — **VERIFIED 2026-05-16 (slot 4)**:
   propagation-chain plan § "Reconciliation baseline" line 706-707 shows **sports phantom count = 0** + **prediction
   phantom count = 0** (post-retired-type-cleanup, dry-run 2026-05-14). Sports retired-data-type migration shipped
   2026-05-13 via VM `migrate-sports-retired-20260513-160205` flipping 88,779 rows. No apply-flips remainder — nothing
   to flip. (sports-retired plan line 250 — Phase 1 IS@a0a720e; Phase 2 deployment-api@5e19878.)
4. ✅ **propagation chain Phase 3.1-3.N + Phase 4 + PART C remainder**. (refactor 0.4×, ~4 = 1.6 cal) — **VERIFIED
   2026-05-16 (slot 4)**: per `expected_unattempted_propagation_chain_2026_05_12.md` lines 765-773 deferred-work table —
   Phase 3.1 (delta_one) ✅ features-service@4a26ae04; Phase 3.2 (calendar) ✅ NO-OP; Phase 3.3 (onchain) ✅ NO-OP;
   Phase 3.4 (volatility) ✅ features-service@4a26ae04; Phase 3.5 (sports) 🟡 DEFERRED with named successor (operator
   triage + Phase 3.5 design call); Phase 3.6 (commodity) ✅ NO-OP; Phase 4 (ml-training + ml-inference) ✅ NO-OP
   (externally-injected instrument lists); PART C ✅ SUBSTANTIALLY-DONE (mdps@3f70cf6, slot 4 2026-05-12; mdps@f50db4e
   docstring cleanup, Harsh slot 2 2026-05-13). Gate 1 🟢 FIRED 2026-05-13. Residual Phase 5 Pass 3+4 (MDPS/features
   apply-flips) + Phase 6 validation gate items both `BLOCKED-UPSTREAM` on slot-6 G4 v8 cutover.
5. ✅ **`api_football_minimal_flattening_removal_2026_05_07` close** (carry from 14 May). (refactor 0.4×, ~3 = 1.2 cal)
   — **VERIFIED 2026-05-16 (slot 4)**: plan body line 320-321 confirms Phase 5 closeout already landed `PM@36c40a10`
   (Slot 6 Wave 3 2026-05-13). Phases 1-3.A ✅ shipped (UAC@c76e6d0 + IS@539130f + IS@e1ca983). Phase 3.B/3.C (live-API
   smoke + EPL forward-poll) + Phase 4 (optional reprocessor) remain `**DEFERRED**` per plan body line 269 —
   operator-executable post-cutover when API quota allows. Plan body line 267 P2 closeout already `[x]`. No slot 4 work
   remaining.
6. ✅ **`expected_universe_v2_design_2026_05_08`** (carry from slot 9 V2) — sports/prediction universe enumerator
   design. (design 0.6×, ~3 = 1.8 cal) — **VERIFIED DESIGN-COMPLETE 2026-05-16 (slot 4)**: all design phases shipped
   pre-today: Phase 1 enumerator code + `InstrumentCatalogEntry` + 65 unit tests (`instruments-service@5c5b1f8`); Phase
   2 launcher `launch-expected-universe-v2-vm.sh` + watchdog prefix `expected-universe-v2-`
   (`deployment-service@7313a39`); Phase 3 Q1 cefi venue-sharding decision (~7 VMs, one per venue) documented; Phase 5
   codex updates landed (3 SSOTs, 2026-05-15). Sports + prediction enumerators ARE part of the 5-per-asset-group v2
   dispatch table (sports: per-fixture lifecycle for per-fixture data_types; prediction: per-`canonical_question_group`
   market lifecycle bundle). Open items are **Phase 4 production launch** (10 VMs × ~3-4h parallel — `BLOCKED-UPSTREAM`
   on slot-6's Phase 7 G4 v8 schema cutover, per plan body line 26-30 banner + Prerequisites line 318) + 1 Phase 1
   integration test (DEFERRED, same blocker) + 1 Phase 2 singleton-lock shell-test (DEFERRED, gcloud mock harness). Slot
   4 has no further implementer surface here until G4 v8 lands; checkbox ✅ on the design half. (Slot-4 evidence note:
   `unified-trading-pm@<TBD>` after this flip lands.)
7. ✅ **`sports_master` data_type universe coverage audit** — cross-ref vs `cross_asset_group_catalogue_audit`.
   (research 1.2×, ~3 = 3.6 cal) — **VERIFIED 2026-05-16 (slot 4)**: 14 May sub-agent audit already shipped per
   `work_split_2026_05_14_ikenna.md` line 238-243 — 14 active data_types confirmed (FIXTURES/STANDINGS/INJURIES/
   FIXTURE_STATS/FIXTURE_EVENTS/FIXTURE_LINEUPS/PLAYER_STATS/PREDICTIONS/MATCHES/XG/PLAYER_VALUES/SFI_PROGRESSIVE_STATS/
   WEATHER/ODDS); 3 retired confirmed (TRANSFERMARKT_LEAGUES/SFI_LEAGUES/SFI_STANDINGS); gaps PLAYER_VALUES +
   SFI_PROGRESSIVE_STATS missing from UAC DATA_TYPE_CAPABILITY_REGISTRY documented in
   `catalogue_audit_sports_2026_05_12.md` SP-6/SP-10/SP-12 with named successor in
   `cross_asset_group_catalogue_audit_2026_05_10.md`. No slot 4 work remaining.
8. ✅ **`data_status_comprehensive_test_coverage_2026_05_07` sports-half close** — drilldown-shard-atom alignment tests.
   (design 0.6×, ~3 = 1.8 cal) — **VERIFIED 2026-05-16 (slot 4)**: 14 May session shipped deployment-api@1ecef8a —
   `tests/unit/test_sports_shard_atom_drilldown_alignment.py` (12 tests, 12/12 pass) covering axes SSOT alignment,
   data_type→league_id→date tree, per-grain count rollups, retired data_type honest coverage, filtered drilldown. Plus
   the cross-repo regression-test net (Vitest + Playwright e2e) per
   `data_status_comprehensive_test_coverage_2026_05_07.md` lines 108-191 — categories A (shard SSOT) + B (UAC parity) +
   C (start-date clipping) + D (deploy-missing end-to-end) all `[x]`
   deployment-api@6cfed38/40f7769/6ab227b/3040a1b/8012a12. No slot 4 work remaining.
9. ✅ **3 sports classifier issues final verification** — confirm sfi_footystats / player_values / weather close.
   (refactor 0.4×, ~2 = 0.8 cal) — **SHIPPED 2026-05-16 (slot 4)**: sfi_footystats → uac@435abae + utl@79c72bad;
   player_values → uac@17a0f82 + utl@79c72bad; weather read-side ✅ (utl@79c72bad). **Weather write-side closed today**:
   `instruments-service@f799109` — `_record_weather_empty(reason=...)` helper accepts typed `EmptyConfirmedReason`; the
   no-fixtures branch (orchestrator.py:6489) now emits `reason="EXPECTED_NO_FIXTURE"` directly so the
   `legacy_reason_classifier` round-trip no longer needs to second-guess. Closes
   `sports_classifier_weather_no_fixture_2026_05_13.md` (status flipped to RESOLVED in same logical unit). Parent issue
   `sports_classifier_extension_followup` ✅ RESOLVED (pm@48db1ae0) cross-linking all 3 child fixes.
10. **Reserve**: in-stack pickup for any sports classifier ambiguity. — **NOT TRIGGERED 2026-05-16 (slot 4)**: no
    ambiguity surfaced during item 1-9 carry-status verifications.

---

### Slot 5 — TradFi backfills + master refresh + Phase 5 QG + LTV thresholds — ~20 cal AI-days

Plan fan-out: TradFi Item 2 Phase 5 QG ratchet (carry from 14 May #3) + tradfi backfills (Databento + CME/EUREX 1-week
each, operator-approval pending) + `tradfi_master` master refresh +
`strategy_service_qg_ltv_threshold_violations_2026_05_15` + `mtf_intraday_micro_regime_policy` (carry from slot 9) +
`sports_retired_data_types_code_cleanup` non-sports half.

1. ✅ **TradFi 1-week test backfill execution** (carry from 14 May #4) — (infra 0.8×, ~3 = 2.4 cal). **OPERATIONALLY
   SHIPPED 2026-05-16**: operator unblocked Databento (`databento-api-key` v6); slot 5 fixed two MTDS bugs in sequence
   (MTDS@`741eb5d` temp-file placeholder collision + MTDS@`f19ff5f` SDK chunk-iteration `int(Timestamp)` bypass via
   `pretty_ts=False`); VM `tradfi-bf-es-adhoc-adhoc-20260516-132055` captured **2,263,630 rows across 5 trading days**:
   2026-05-01=382,926 / 2026-05-04=495,632 / 2026-05-05=348,307 / 2026-05-06=479,893 / 2026-05-07=556,872. Weekends
   2026-05-02/03 pre-skipped (EXPECTED_WEEKEND). Sample parquet
   `day=2026-05-01/.../futures_chain/ohlcv_1m/ES/ticks.parquet` (1,528 rows): canonical schema present
   (instrument_id=`CME:FUTURE:ES-20260619`, lifecycle_phase=active, session=regular, phase=continuous, available_at
   stamped); OHLC range 7240.75–7411.5; 0 nulls across OHLCV+volume. exit_code=0 + self-shutdown. The two MTDS fixes
   simultaneously unblock items 6 + 10 + the 5 paused `mdps-tradfi-*` VMs.
2. ✅ **Databento session-stamp backfill** (infra 0.8×, ~3 = 2.4 cal) — **OPERATIONALLY SHIPPED 2026-05-16 14:29 UTC**:
   VM `canonical-migration-tradfi-sessionstamp-20260516-135034` completed migration: **24,944 parquets back-stamped**,
   **12,184 skipped** (already had columns OR no timestamp surface like VIX index), **0 errors**, elapsed 5,771s (~96
   min), date range 2024-01-01 → 2026-05-05. Spot-check 2025-06-13 CME combo parquet schema includes `session`
   - `phase` (session=regular×850 / phase=continuous×850). Slot 5 ping 14:29 UTC confirms operationally closed. Bonus
     durability fixes shipped same agent turn: UTL@`bc87bc89` (accept VM-extracted `deployment/` dir as workspace marker
     — covers the foot-gun) + deployment-service@`9ed84f8` (launcher sets `UNIFIED_TRADING_CLOUD_PROVIDERS_YAML`
     belt-and-braces).
3. ✅ **TradFi Item 2 Phase 5 QG ratchet** (carry from 14 May #3) — QG STEP enforcement banning legacy futures-contract
   shape (operator GREENLIT). (design 0.6×, ~3 = 1.8 cal) — **VERIFIED PRE-EXISTING DONE 2026-05-15**: PM@`32c7ea52`
   already shipped Phase 5 QG ratchet on 2026-05-13 (182-line scanner, AST-walks every `CanonicalFuturesContract(...)`,
   7 unit tests green). Confirmed at
   `plans/active/tradfi_canonical_futures_contract_hard_required_fields_2026_05_13.md:183-201` — "✅ COMPLETE
   2026-05-13". Carry-flag was bookkeeping only.
4. ✅ **`tradfi_master` master plan refresh** (carry from 14 May #5) — push remaining open todos workspace-wide.
   (research 1.2×, ~4 = 4.8 cal) — **DONE 2026-05-16 (slot 5 ikenna)**: shipped 3 epic-level open todos (1) expiry guard
   `instruments-service@c3782ba` (P1) + 4 tests; (2) VIX-specific feature calculator `features-service@b3814675` (P3) —
   `compute_vix_features()` + 10 tests; (3) TradFi feature_groups → UAC `FEATURE_REQUIRED_INPUTS`
   `unified-api-contracts@99a7614` (P1) — 8 feature_groups (options_iv + 6 vol kin + `vix_features`). Remaining open
   items in tradfi_master are pipeline-VM runs (P3/P4 features-delta-one / features-volatility / ml-training smoke),
   BLOCKED-CREDENTIALS (ES_OPT 2020-2022), TRACKED-ELSEWHERE pointers (hard_schema_enforcement,
   available_at_lookahead_bias), VERIFY P0 spot-check (no `futures_contracts.parquet` files written in prod yet —
   confirmed via `gsutil ls` against 2024-2026 dates × all venues; write path `_write_futures_contracts` exists in
   IS@2be7e4b but recent backfills haven't exercised it; surfacing as discovery for Phase 4.2 follow-up), and end-state
   May-23 success criteria gated on full pipeline run.
5. ✅ **`tradfi_master` venue + symbology coverage audit** (carry from 14 May #8). (research 1.2×, ~3 = 3.6 cal) —
   **AUDIT 2026-05-16**: cross-referenced against `cross_asset_group_catalogue_audit_2026_05_10.md` § ICE US softs
   action item (Phase 5B pending). Found ICE US softs (CT/CC/KC/SB/OJ/DX) **already canonicalised** in UAC:
   `canonical/domain/derivatives/tradfi_roots.py:242-247` registers all 6 as `CATEGORY_ICE_FUTURES` with
   `DATASET_ICE_US`
   - exchange="ICE"; `registry/tradfi_instrument_universe.py:233-239` `_ICE_US_FUTURES` list has all 6 as
     `DatabentoInstrumentDef(..."ICE", "FUTURE", "IFUS.IMPACT", "parent", ...)`;
     `registry/tradfi_symbology.py:104-105, 319, 408` references `CT.FUT → IFUS.IMPACT`. Zero drift: no `CT.FUT.*CME`
     references workspace-wide. Other carry-over TF-6/TF-7 items (no `futures_chain` data_type / `options_chain` only at
     CME / VIX-15m constants location) remain open per the catalogue audit and are tracked in that plan, NOT a slot-5
     deliverable.
6. ✅ **CME (MES) 1-week test backfill** (carry from 14 May #10) — (infra 0.8×, ~2 = 1.6 cal). **OPERATIONALLY SHIPPED
   2026-05-16**: VM `tradfi-bf-mes-adhoc-adhoc-20260516-132914` ran with the same 2 MTDS fixes that unblocked item 1.
   Captured **1,854,206 rows across 5 trading days** (2026-05-01=327,750 / 05-04=419,950 / 05-05=285,879 / 05-06=365,861
   / 05-07=454,718). MES.FUT canonical futures_chain + combo partitions written, weekends pre-skipped, exit_code=0.
   **EUREX descoped**: not in current TradFi adapter universe (`EUREX` exists in
   `unified_api_contracts/registry/venue_session_hours.py` + `half_day_sessions.py` for calendar logic only; no entries
   in `tradfi_roots.py` / `tradfi_instrument_universe.py` / `launch-tradfi-backfill-vm.sh`). EUREX coverage is a
   separate adapter-buildout task, NOT a backfill smoke. Moved to `tradfi_master.md` § "Eurex venue expansion" follow-up
   todo (P2, post-cutover).
7. ✅ **`strategy_service_qg_ltv_threshold_violations_2026_05_15` close** (carry from 14 May #11) — migrate to UAC
   `LIQUIDATION_PARAMS_REGISTRY`. (refactor 0.4×, ~1 = 0.4 cal) — **VERIFIED ALREADY CLEAN 2026-05-15**: ran exact STEP
   5.37 regex on `strategy_service/engine/` — every match is annotated `# CORRECT-LOCAL` (gas uplift, runtime config,
   func defaults) or `# noqa: qg-inline-threshold`. Live `bash scripts/quality-gates.sh` reports
   `✅ STEP 5.37: No inline HF/LTV/margin thresholds (UAC LIQUIDATION_PARAMS_REGISTRY)`. Triage exemptions already
   correctly applied; issue doc at `plans/active/issues/strategy_service_qg_ltv_threshold_violations_2026_05_15.md` was
   self-resolving (filed today + cleaned later same day by earlier slot-5 commits).
8. ✅ **`mtf_intraday_micro_regime_policy` 2 dict entries** (carry from slot 9 #4 reassignment). (design 0.6×, ~1 = 0.6
   cal) — **VERIFIED SHIPPED 2026-05-15**: Option A (NAN_FILL) operator-acked. UAC@`1f8bcbc` (`SERVICE_OUTPUT_POLICIES`
   seeds for `intraday_regime` + `micro_regime` + 2 tests) + FS@`140b6fe5` (`_SEEDED_FEATURE_GROUPS` in
   `batch_handler.py` + `TestSingleTfGroupsNanFill` class). Issue doc
   `plans/active/issues/mtf_intraday_micro_regime_policy_2026_05_14.md` already shows ✅ RESOLVED. No further action.
9. ✅ **`sports_retired_data_types_code_cleanup` non-sports half** (carry from 14 May #7) — retire dead data_types from
   cross-cutting / UAC side. (refactor 0.4×, ~3 = 1.2 cal) — **VERIFIED 2026-05-16**: workspace grep across all
   non-IS/non-deployment-api repos (UTL, FS, MTDS, MDPS, strategy, execution, ML, MLI, deployment-service) for
   `TRANSFERMARKT_LEAGUES|SFI_LEAGUES|SFI_STANDINGS` returned 0 active references — only historical
   `# retired 2026-05-05` comments. UAC itself (`canonical/domain/sports/`, `internal/schemas/_sports_contracts.py`,
   `registry/data_type_capability.py`) already has only historical comments (no enum / registry entries). **One stale
   snapshot fixed**:
   `unified-trading-system-ui/context/api-contracts/canonical-schemas/domain/sports/provider_league_ids.py` had stale
   `"TRANSFERMARKT_LEAGUES": None / "2019-01-01"` + `"SFI_LEAGUES" / "SFI_STANDINGS"` dict entries (UI-side docs
   snapshot, not runtime). Synced to live UAC: UI@`f010d14f` (also picks up `UNDERSTAT_COVERED_LEAGUES` helper +
   `does_understat_cover()` added in UAC 2026-05-08).
10. ✅ **TradFi venue calendar SSOT `MarketSession` final close** — operator answered Yes 2026-05-13; backfill VM ask
    pending. (design 0.6×, ~2 = 1.2 cal) — **OPERATIONALLY SHIPPED 2026-05-16 slot 5**: all three code legs already
    shipped earlier (UAC@`f4d0cec` `classify_session` facade + MTDS@`038a611` non-trading-day `record_expected_empty` +
    FS@`ce093d6c` `_filter_regular_session()` + 6 tests). Backfill VM leg now LIVE: VM
    `canonical-migration-tradfi-sessionstamp-20260516-135034` running
    `migrate_tradfi_ohlcv_session_stamps.py --start-date 2024-01-01 --end-date 2026-05-14 --no-dry-run` post the
    GCS-prefix-walking-bug fix (MTDS@`fdb92ca`). Migration walks forward correctly; ~2500 files stamped in ~10 minutes
    at start; expected to walk ~30k historical TradFi OHLCV parquets and back-fill session/phase columns via UAC
    `classify_session(venue, ts)`. Item closes operationally on VM exit_code=0; the code legs are already in production
    write-time stamping per MTDS@`038a611`.
11. **Reserve**: in-stack pickup for any tradfi QG enforcement gaps.

Backfill flag: items 1 + 6 <1 week — pre-authorized; item 2 ≥1 week — **OPERATOR ACK REQUIRED**.

---

### Slot 6 — manifest v8 Phase 6+7 + phase_3c lending + alerting close — ~22 cal AI-days

Plan fan-out: `manifest_schema_final_gate_2026_05_09.md` Phase 6+7 (TOP PRIORITY — May-13-15 operator-gated window IS
NOW) + `phase_3c_lending_rate_model` continuation (UNBOUNDED per operator) + alerting close-out + audit_records Phase 1

- `available_at_lookahead_bias_completion_2026_05_08` close + alerting_runbook operator-UX remainder.

1. **🔴 [TOP PRIORITY] `manifest_schema_final_gate_2026_05_09.md` Phase 6 + Phase 7 — v8 GCS bundled walk (May-13-15
   operator-gated window IS NOW; we're in day 3 of 3)** — slot 6 is the plan owner. **Phase 6**: bounce-sweep stale VMs
   (`gcloud compute instances list --project=central-element-323112 --filter="status=RUNNING"` → confirm STOPPED or
   graceful shutdown). **Phase 7.A pre-flight** (Phase 1-5 ✅ + Phase 6 drain confirmed). **Phase 7.B snapshot**
   per-bucket `_index/` to `gs://{pid}-pre-migration-snapshot/`. **Phase 7.C launch fleet**: per-bucket 4-8 migration
   VMs in asia-northeast1-c with `MANIFEST_PER_VM_SHARDS=true` + unique `VM_NAME`. **Phase 7.D-E** event stream watch +
   manifest consolidator. **Phase 7.F** per-asset-group QA gate (phantom count MUST be 0). **Phase 7.G** cross-ping slot
   1 main per asset_group when QA green for **operator sign-off** (5 sub-checkboxes:
   cefi/defi/tradfi/sports/prediction). (infra 0.8×, ~6 = 4.8 cal)
2. **🔴 `phase_3c_lending_rate_model` continuation** — 5th bug fix shipped 2026-05-14 (`execution-service@70825a432`);
   UAC IRM defaults updated (`unified-api-contracts@215ed3e`). **Awaiting operator VM re-run** to confirm USDT 55%→90%+,
   USDC 85%→90%+, DAI TBD. (a) coordinate VM run via operator ping; (b) if DAI still fails, find DAI IRM source.
   (research 1.2×, ~4 = 4.8 cal — unbounded per operator)
3. ✅ **`audit_records_pb_1_2_3_pre_cutover_2026_05_13` Phase 1 close** — plan archived as 100% complete 2026-05-16
   (slot-8 SWEEP-16 mechanical archive sweep). All Phases 1-4 verified done. Archived at
   `plans/archive/audit_records_pb_1_2_3_pre_cutover_2026_05_13.md`. (research 1.2×, ~3 = 3.6 cal)
4. ✅ **`available_at_lookahead_bias_completion_2026_05_08` sweep close** — stamping helper consumers shipped:
   UTL@`8b0fb816` (`stamp_available_at_onchain_tick` added); MTDS@`bbdbf55` (all 4 onchain DeFi handlers stamped:
   evm_defi, gas_fee, solana_defi, lst_rates — all write paths); features-service@`7b1ede28`
   (`contextlib.suppress(LookaheadBiasError)` removed + `contextlib` + `LookaheadBiasError` import cleanup). Chain link
   1 complete. (refactor 0.4×, ~3 = 1.2 cal)
5. ✅ **`alerting_runbook_and_operator_ux_post_cutover_2026_05_12` operator-UX remainder** — DESIGN-SHIPPED 2026-05-17:
   Groups A/B/C/E/F all `[x]` in plan; Group D (ST-11 block-list TS parity) design call done → CI parity test, DEFERRED
   to Harsh UI slot; Group G (STALE_OPEN_ALERT dashboard) design call done → deployment-ui tile, DEFERRED to Harsh
   deployment-ui slot. Named successors in plan body. Plan's done-definition satisfied (all groups either shipped or
   explicitly migrated). (design 0.6×, ~3 = 1.8 cal)
6. ✅ **Custody Cloud-KMS smoke + 4 DeFi alert-codes alerting wiring final** — Cloud-KMS smoke END-TO-END verified
   2026-05-12 (master plan entry + work_split_2026_05_14 item 14 ✅); 4 DeFi alert-codes (`DEFI_AAVE_UTILIZATION_SPIKE`,
   `DEFI_FUNDING_RATE_FLIP`, `DEFI_FEATURE_STALE`, `DEFI_WEETH_DEPEG`) all `[x]` in alerting_service_live_rules plan
   (alerting-service@12411e0 + features-service@2ecb1378). (design 0.6×, ~3 = 1.8 cal)
7. ✅ **DeFi handler hardening verification across all 4 handlers** (post-`market-tick-data-service@c1e6963` +
   `@f657431`) — verified shard-level failure isolation (record_captured INSIDE try, recorder.close() in finally) across
   evm_defi_handler, gas_fee_handler, solana_defi_handler, lst_rates_handler. All 4 handlers follow eigenlayer pattern.
   (research 1.2×, ~2 = 2.4 cal)
8. ✅ **`strategy_paper_vm_nautilus_trader_missing_dep` re-verify** (carry from slot 9 #5) — verified nautilus_trader
   dependency correctly declared in strategy-service pyproject.toml; no missing dep issue confirmed. (refactor 0.4×,
   ~0.5 = 0.2 cal)
9. **Reserve**: in-stack pickup for any wallet/custody issues.

---

### Slot 7 — SIT critical-path BLOCKER + basefc paradigm + audit + writegate finalize — ~28 cal AI-days

Plan fan-out: **`sit_may23_critical_path_coverage_gaps_2026_05_15` (MAY-23 BLOCKER)** +
`basefc_validation_flip_2026_05_10` items 1-5 + `audit_records_pb_1_2_3` Phase 2-3 + writegate Phase 6.6/6.7/6.9 α-vs-β
audit (carry from slot 10 reassignment) + `client_reporting_pnl_attribution_mvp` + `compute_optimization_mock_data`
Ikenna-half + `mock_data_pipeline_benchmarking` Phase 8.A + `context_fill_optimization`.

1. ✅ **🔴 [MAY-23 BLOCKER] `sit_may23_critical_path_coverage_gaps_2026_05_15`** — 3 SIT scenario playbooks shipped in
   `system-integration-tests@3872ce2`: (a) `defi_carry_staked_basis_paper` + (b) `defi_apd_paper` (with explicit
   not-silently-skipped routing assertion) + (c) `defi_paper_to_live_early_gate` (promote → VM STARTED + DART day-1
   blocking gate). Added to `defi_scenarios.py::get_scenarios` (5 → 8) + dedicated
   `tests/scenarios/test_may23_critical_paths.py` makes the May-23 gate dependency explicit (presence + per-gate
   semantics + suite aggregate). All 28 framework + may23 tests pass; basedpyright clean. (brand-new 1.0×, ~4.5 = 4.5
   cal)
2. ✅ **`basefc_validation_flip_2026_05_10` items 1-5** — calculator paradigm migration FULLY DONE 2026-05-16 (incl.
   extended-scope multi_timeframe family pickup): (1) strategy decision Option-a `PM@082444d7`; (2a) cross_instrument 20
   calcs `features-service@71643dec`; (2b) onchain 19 calcs `features-service@151dffab`; (2c) multi_timeframe 9 calcs +
   ABC promoted to UTL canonical `features-service@87ba9cf6`; (3) UTL mandatory `__init_subclass__` flip
   `unified-trading-library@ccc9b7bf` (eager MRO walk because ABCMeta sets `__abstractmethods__` after
   `__init_subclass__`); (4) plan-flip cite. **48 concrete calcs migrated** across cross_instrument + onchain +
   multi_timeframe polars families; `validate_class_attributes()` OK on all; basedpyright clean; UTL test stub updated
   to assert raises. (refactor 0.4×, ~6 = 2.4 cal)
3. ✅ **writegate Phase 6.6 + 6.7 + 6.9 α-vs-β audit** — β verdict confirmed across 9 services (`PM@3a4afdc5`);
   per-service emission boundary is canonical (vs centralised α). Audit table added at
   `writegate_honest_coverage_endtoend_2026_05_06.md` § 3.5 with per-service file + boundary mapping. **Gate 4 CLOSED**:
   every Phase 6.6/6.7/6.8 service has `[x]` checkbox + sha evidence + QG STEP 5.71 paired-callsite check passes
   workspace-wide. (research 1.2×, ~4 = 4.8 cal)
4. ✅ **`audit_records_pb_1_2_3_pre_cutover_2026_05_13` Phase 2-3** — verified all plan body checkboxes `[x]` +
   Done-definition fully checked: `execution-service@51f1f879` (audit_log.py path fix + client_order_id param +
   resolve_bucket_name + 9 unit tests), `deployment-service@c3ac1c5` (cloud-providers.yaml audit-records kind +
   retention-lock provision script), GCP `gs://trading-audit-records-prd-central-element-323112` locked 2026-05-13
   (`retentionPeriod=220752000 isLocked=True`), AWS `unified-trading-audit-records-prd-427895769566` COMPLIANCE 7yr lock
   2026-05-14. No additional work this session; verification-only flip. (research 1.2×, ~4 = 4.8 cal)
5. ✅ **`client_reporting_pnl_attribution_mvp_2026_05_10` push** — verified all 36 top-level plan checkboxes `[x]`, zero
   open. Phase 5.C2 HWM + Phase 8.A/B/C confirmed complete in 14 May session (per work_split_2026_05_14 item 6 evidence:
   `client-reporting-api@ce5156d` + `deployment-ui@21331da` + `deployment-service@e00fe79` for HWM route;
   `client-reporting-api@192b41d` + `deployment-service@007f67f` for Phase 8 real-VM cutover runner + launcher). No
   additional work this session. (design 0.6×, ~4 = 2.4 cal)
6. ✅ **`compute_optimization_mock_data_2026_05_13` Ikenna-half** — all Ikenna-half items shipped: Phase 0 ✅
   (stage-bottleneck classification `PM@c36a5bfb`); Phase 1 ✅ (aggregation wire + `--max-parallel` flag
   `strategy-service@8b20a32`; verify-extend item is DEFERRED with named follow-up — per-archetype design call needed);
   Phase 2 partial ✅ (sports `--worker-count` `features-service@722697d3`; onchain/volatility families already had it);
   Phase 3 ✅ (execution-alpha scaffold `execution-service@fa18c3a1b`
   - parallel wrapper `execution-service@f65a7d5d5` + VM launcher `deployment-service@1510310` + smoke
     `strategy-service@fc634e3`). Remaining open: Phase 4 ml-training (Harsh-half), Phase 5 SKU matrix (joint), Phase 2
     profiling item (joint). (design 0.6×, ~3 = 1.8 cal)
7. ✅ **`mock_data_pipeline_benchmarking_2026_05_10` Phase 8.A** — verified Phase 8.A code SHIPPED: `UTL@f942dc54`
   (`check_budget()` + `BudgetExceededError`); benchmark report parquet+md landed at
   `gs://central-element-323112-benchmark-reports/benchmark_report/`; 8-VM matrix complete + per-stage P50/P95/P99 in
   `benchmark_report.md`. **Master plan Group F row 18 update is slot 1 main's territory** per CLAUDE.md "slot
   precedence" rule (slot 7 does NOT edit `master_to_live_defi_2026_05_23.md` directly). Open downstream: actual 2yr
   batch VM run is owner Agent 4 (AUTHOR-MISSING note in master plan row) — not slot 7 work. (infra 0.8×, ~3 = 2.4 cal)
8. ✅ **`data_status_drilldown_shard_atom_alignment_2026_05_07` finalize** — already finalised yesterday (`PM@163da45a`
   per work_split_2026_05_14 item 8 "Phase 3 shipped; remaining deferred items have named successors"). Audit
   reconfirms: 34/41 checkboxes `[x]`; remaining 7 open items all explicitly DEFERRED with named successors per
   "Deferred work after 2026-05-13" table (download-csv → Phase 3 SmartDownloadButton; Playwright → operator-doable;
   canonical_question_group → predictions Plan A; cross-registry test → predictions Plan A; rollup metric →
   infrastructure_master). No additional work this session. (research 1.2×, ~3 = 3.6 cal)
9. ✅ **`context_fill_optimization_2026_05_14` Phase 1** — already finalised yesterday per work_split_2026_05_14 item 7:
   P0 CLAUDE.md trim `[x]` (`PM@6a08f50c`, 399 lines / 25.3KB) + P1 orchestrator sub-agent poll loop `[x]`
   (`PM@1a056988`). Plan body P2 (relocate `.claude/rules/` per-repo) is lowest-impact, deferred per body — outside
   Phase 1 scope. No additional work this session. (research 1.2×, ~2 = 2.4 cal)
10. **Reserve**: in-stack pickup for SIT scenario surfacings.

---

### Slot 8 — B-015 smoke re-launch + solana_defi venue naming + audit close + governance — ~18 cal AI-days

Plan fan-out: B-015 smoke re-launch coordination (apply-flips audit complete; manifest CLEAN) +
`solana_defi_coverage_gaps` successor D venue naming + `AUDIT_pre_may_8_cleanup_2026_05_13` close +
`bucket_name_ssot_canonicalisation_2026_05_10` workspace flip (carry from slot 9) +
`code_freeze_migrate_backfill_sequencing_2026_05_10` cross-cutting audit (carry from slot 9) +
`governance_qg_automation_gaps_post_cutover_2026_05_12` codification + `deploy_missing_auto_launch_2026_05_07` close
(V2) + Cluster B pnl-attribution lint.

1. ✅ **B-015 smoke re-launch coordination** — phantom audit returned CLEAN per
   `plans/active/issues/b_015_smoke_vms_phantom_manifest_silent_skip_2026_05_15.md` (root cause: stale in-flight lock
   not phantoms; apply-flips not needed). Harsh slot-9 re-launched 2026-05-15:
   - **Smoke A ✅ CLEAN** — `mtds-lst-rates-20260515-201226` exit_code=0; 12+ LST venues × 5 days (2026-04-15..19)
     written to `gs://lst-rates-central-element-323112/`; no phantoms (handlers hardened pre-launch:
     `mtds@c1e6963/f657431` + 3bca360).
   - **Smoke B 🟡 BLOCKED-UPSTREAM** — features-onchain dependency-check failed: MDPS `processed_candles` missing for
     `2026-04-15..19/DEFI`. Upstream MDPS DEFI batch must run for those dates before features-onchain can produce data.
     Operator decision pending: (a) declare B-015 verified on Smoke A alone + ship MDPS DEFI batch as separate task, OR
     (b) run MDPS first then re-run features-onchain. Coordination DONE on slot-8 side. (infra 0.8×, ~2 = 1.6 cal)
2. ✅ **`solana_defi_coverage_gaps` successor D venue naming reconciliation** (carry from 14 May #2). All phases landed
   by slot-3 2026-05-15: Phase 1 `instruments-service@2639f8e` (migration + 7 unit tests), Phase 2 dry-run (169 Cat A
   phantom + 59 Cat B), Phase 3 migration ran locally with ADC admin perms (`rows_phantom_marked=228`, backup at
   `availability_index.20260515-135146.bak.parquet`), Phase 4 codex update `unified-trading-pm@02efcea5`. Verified
   bare-name venues `captured=0`, PROTOCOL-SOLANA rows `empty_confirmed`. Plan flipped at `unified-trading-pm@d526b8cb`.
   (design 0.6×, ~3 = 1.8 cal)
3. ✅ **`AUDIT_pre_may_8_cleanup_2026_05_13` close** (carry from 14 May #3). All 3 flagged items already resolved by
   other agents during the 14 May audit pass: (a) wave3x Track D EXPECTED_KNOWN_SOURCE_GAP shipped `UAC@174f401` (status
   table already `done`); (b) launcher_scripts Phases 2/3 annotated DEFERRED-PER-AUDIT at `PM@724a2029`; (c)
   deployment_ui_lifecycle_tabs A.2 false positive corrected. (refactor 0.4×, ~3 = 1.2 cal)
4. 🟡 **`bucket_name_ssot_canonicalisation_2026_05_10` workspace flip** — `BLOCKED-UPSTREAM` on
   `code_freeze_migrate_backfill_sequencing_2026_05_10` Phase 2.6 (window 2026-05-15→05-19): call-site sweep + L3 legacy
   delegate + dependency_checker migration all gated on Phase 2.6 physical flat→env-tiered migration. **What IS
   shipped** (verified 2026-05-15 18:59 UTC): QG STEP 5.69 ratchet operational
   (`scripts/quality-gates-base/base-service.sh:1578-1623`); 2 repos at 0 (instruments-service @5210149,
   deployment-service @0b802ec); 8 baselined repos await Phase 2.6 ratchet-down (deployment-api 27, execution 33, UTL
   23, batch-live-recon 7, UAC 5, UI 4, features-service 2, strategy-service 2); L1↔L4 parity zero-drift verified; L2
   features-\* templates migrated to `resolve_bucket`. Workspace-flip Done-def #6 (full grep-audit table) deferred-after
   Phase 2.6 with named successor. (refactor 0.4×, ~4 = 1.6 cal — bulk deferred-after Phase 2.6)
5. 🔄 **`code_freeze_migrate_backfill_sequencing_2026_05_10` cross-cutting audit** (carry from slot 9 #10) — Slot-8
   audit 2026-05-15 19:05 UTC. Plan has 122 items; cross-cutting subset surfaces 5 actionable items (Phase 2 freeze gate
   × 6 unchecked, blocked-on-physical-migration), of which slot-8 closeable:
   - ✅ **Stamp-lag fix for `defi-data-type-taxonomy.md`** — already naturally absorbed; doc shows
     `last_reviewed: 2026-05-15` with prior 2026-05-12 stamp acknowledged in body. Flipped in plan body.
   - 🟡 **5 NEW gap-2.6.A through gap-2.6.E (Phase 2.6 detailed playbook)** — slot 8 / slot 3 carry; deployment-service
     surface. Owners TBD; remains open as physical-migration work for the 2026-05-15→05-19 window. Routed to slot 3
     (already shipping Phase 2.6 playbook per `slot_3.md`).
   - 🟡 **Codex audit for 11 Phase 1.A/1.B/1.C plans (P2)** — depth-audit follow-up beyond slot-6 day-1 breadth; not
     blocking; carry into post-cutover sweep.
   - 🟡 **TradFi 4.3% phantom audit triage (P2)** — no named owner; routed to `tradfi_master.md` § "Port phantom-audit"
     P0 todo; POST-CUTOVER scope per plan body.
   - 🟡 **Phase 2 freeze gate × 6 items** — blocked on physical migration (Phase 2.0-2.6 window 05-15→05-19).
     Audit-summary flip; substantive items routed/blocked. (research 1.2×, ~3 = 3.6 cal)
6. ✅ **`governance_qg_automation_gaps_post_cutover_2026_05_12` codification** (carry from slot 9 #12) — Runbook
   Execution-Owner SSOT gap codified at `unified-trading-pm@7ef2ecdb`. Ships
   `scripts/quality_gates/check_runbook_execution_owner.py` + baseline (9 violations) + PM `quality-gates.sh` wiring
   (ratchet mode — fails on regression). Verified: basedpyright clean, ruff clean, smoke exit 0. Future PRs ratchet down
   by adding the 4-field `execution:` block to the 9 baselined runbooks. Group A.1 todo flipped in the governance plan
   body. (design 0.6×, ~3 = 1.8 cal)
7. 🔄 **`deploy_missing_auto_launch_2026_05_07` close** (V2 carry from slot 9). **Slot-8 partial 2026-05-15**: Phase 4
   item 1 (codex docs) ✅ SHIPPED at `unified-trading-pm@52cf9627` — `/codex/02-data/data-status-drilldown.md` §5
   documents preview + auto-launch modes with full IAM / rate-limit / audit-log / idempotency / correlation-id /
   tarball-refresh contract. **7 items still open**: Phase 2 (4 P0 deployment-api endpoint + idempotency + event
   correlation + rate-limiter) `BLOCKED-UPSTREAM` on Firestore rate-limit state infra + BigQuery audit-log infra (Phase
   0 Decision 2+3 ratified 2026-05-08 but supporting infra still in design); Phase 3 (2 P0 UI) gated on Phase 2
   endpoint; Phase 4 item 2 (P2 final closeout) gated on Phase 0-3 + 7-day soak. (infra 0.8×, ~3 = 2.4 cal — partial:
   doc shipped, endpoint deferred)
8. ✅ **Cluster B pnl-attribution-service lint sweep** — C901+N802+B008 already fixed in 14 May session at
   `pnl-attribution-service@9f3379f`; invalid `noqa` directives cleaned at `pnl-attribution-service@44ac3fd`. Verified
   15 May 18:58 UTC: `ruff check pnl_attribution_service/` → `All checks passed!`. (refactor 0.4×, ~2 = 0.8 cal)
9. ✅ **`honest_coverage_cron_vm_scheduling`** (carry from slot 9 #3) — Cron-VM half closed: slot-2 shipped canonical
   `deployment-service@19454f1` Cloud Scheduler + Cloud Run Job at 00:30 UTC. Slot-8 collision: independently built
   Python launcher (`deployment-api@d6e72c6`); reverted at `deployment-api@3afc016`. Issue doc flipped at
   `unified-trading-pm@ae61ca1b`. **Operator verification still needed**: confirm first scheduler fire on 2026-05-16
   00:30 UTC produces `gs://central-element-323112-honest-coverage/2026-05-16/coverage.json`. Backfill of pre-cron dates
   remains a one-shot operator concern (ping in slot_8.md 19:36 UTC). (infra 0.8×, ~2 = 1.6 cal)
10. **Reserve**: in-stack pickup for any UAC drift surfacings.

---

## Top-priority items for 2026-05-15 (cross-slot)

| Priority | Item                             | Owner                    | Why                                                                                 |
| -------- | -------------------------------- | ------------------------ | ----------------------------------------------------------------------------------- |
| **P0**   | manifest v8 Phase 6+7            | Slot 6 #1                | Operator-gated window IS NOW (day 3 of 3); operator sign-off per asset_group needed |
| **P0**   | SIT critical-path scenarios      | Slot 7 #1                | Last automated CI gate before paper→live_early manual promotion                     |
| **P0**   | B-015 smoke re-launch            | Slot 8 #1 + Harsh slot 9 | `carry_staked_basis` paper-trade gate; manifest clean, just needs new VM_NAME       |
| **P1**   | phase_3c lending model VM re-run | Slot 6 #2 + operator     | Awaiting operator VM run to confirm USDT 90%+ + USDC 90%+                           |
| **P1**   | Databento session-stamp backfill | Slot 5 #2 + operator     | ≥1-week backfill ack pending                                                        |

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
  checkbox → checked in SAME AGENT TURN. NEVER batch flips. CLAUDE.md
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
- Slot 6: **manifest v8 Phase 7.G hits operator-sign-off queue for ≥3 of 5 asset_groups**; phase_3c VM re-run results
  landed.
- Slot 7: **SIT 3 scenarios shipped** + basefc items 1-5 closed + writegate α-vs-β verdict filed.
- Slot 8: B-015 smoke re-launched (or new diagnostic if features-onchain still failing).

**Daily inventory regenerator** (slot 1 main, EOD) should show **workspace cal-days remaining ≤ 370** (down from 518
this morning).

## Pre-cutover sweep — all remaining May-23 cal-days routed (2026-05-16 race-to-finish)

**Source**: operator direction 2026-05-16 — race ahead; allocate ALL remaining May-23 cutover work across the 8 Ikenna
slots; no operator action needed (all credentials vaulted). Inventory dashboard 2026-05-16: 78 plans, 55% done, **~290
cal AI-days remaining on May-23-deadline plans**.

Items annotated **[SWEEP-16]** are NEW additions to each slot's existing stack — additive, take after current
top-of-stack lands. Slot 1 main continues orchestration + drives the DAI VM relaunch + owns the workspace-qg.yml
redesign accepted today.

**Source**: operator direction 2026-05-16 — race ahead; allocate ALL remaining May-23 cutover work across the 8 Ikenna
slots; no operator action needed (all credentials vaulted). Inventory dashboard 2026-05-16: 78 plans, 55% done, **~290
cal AI-days remaining on May-23-deadline plans**.

Items annotated **[SWEEP-16]** are NEW additions to each slot's existing stack — additive, take after current
top-of-stack lands. Slot 1 main continues orchestration + drives the DAI VM relaunch + owns the workspace-qg.yml
redesign accepted today.

### Per-slot SWEEP-16 allocation

#### Slot 2 — **[SWEEP-16]** items (+5 cal absorbed from MTDS-pipeline overflow)

- **`mdps_streaming_and_backpressure_2026_05_07`** (3.0 cal, 0/7) — MTDS streaming + backpressure design + close. Slot 2
  has MTDS context from Helius integration. (design 0.6×, ~5 = 3.0 cal)

- 🟡 **`mdps_streaming_and_backpressure_2026_05_07`** (3.0 cal, 0/7) — MTDS streaming + backpressure design + close.
  Slot 2 has MTDS context from Helius integration. (design 0.6×, ~5 = 3.0 cal) — **CARRY TO NEXT SLOT-2 SESSION
  2026-05-16 by slot 2**: substantial 6-item multi-repo P1 design (LiveConnectivityWatchdog + CONNECTIVITY events +
  auto-backfill + circuit-breaker + per-venue heartbeat calibration + codex update). Spans MTDS + MDPS +
  execution-service. Exceeded slot-2 remaining wall-clock today; deferred to next session.
- ✅ **`solana_lst_native_staking_adapters_2026_05_14` close** (0.2 cal, 21/22) — **VERIFIED 2026-05-16 by slot 2**:
  sole open item (line 181) is `[BLOCKED-CREDENTIALS — pinging operator]` VM launcher (Phase E). Status correctly set;
  no further slot-2 action needed; awaiting operator [ack] on credential ask. (refactor 0.4× ~0.2)
- ✅ **`solana_restaking_rewards_coverage_2026_05_13` close** (0.2 cal, 16/18) — **VERIFIED 2026-05-16 by slot 2**: 2
  open items (lines 137, 140) both annotated `[DEFERRED] **NICE-TO-HAVE**` (MTDS wiring for Solayer/Picasso/ Cambrian +
  Picasso/Cambrian program ID verification). Correctly statused as nice-to-haves; not May-23 blocking. (refactor 0.4×
  ~0.2)
- ✅ **`solana_amm_coverage_expansion_2026_05_13` flip-verify** — **VERIFIED 2026-05-16 by slot 2**: plan ARCHIVED at
  `plans/archive/solana_amm_coverage_expansion_2026_05_13.md`. (~0.1 cal)
- ✅ **`solana_venue_naming_reconciliation_2026_05_14` flip-verify** — **VERIFIED 2026-05-16 by slot 2**: plan ARCHIVED
  at `plans/archive/solana_venue_naming_reconciliation_2026_05_14.md`. (~0.1 cal)
- ✅ **`solana_perp_dex_adapters_2026_05_13` flip-verify** — **VERIFIED 2026-05-16 by slot 2**: plan ARCHIVED at
  `plans/archive/solana_perp_dex_adapters_2026_05_13.md`. (~0.1 cal)

#### Slot 3 — **[SWEEP-16]** items (+18 cal — MTDS/DEX/perp expansion theme)

- **`live_pipeline_mtds_mdps_features_2026_05_08` Ikenna portion** (15.0 cal) — DeFi instrument live-pipeline
  activation; slot 3 owns perp/venue/DEX theme already. (design 0.6×, ~15 = 9.0 cal) — **PARTIAL 2026-05-17 (slot-3)**:
  Phases 0-14 all done (PM@58b07da0 Phase 3 flip). Phase 15 (QG sweep + 7-day live smoke): **15.1 COMPLETE** — MTDS QG
  3751 pass / 0 failures (all 5 pre-existing Tardis+smarkets failures fixed: MTDS@936f0c4 + MTDS@1180dfe + UAC@0710ba8;
  issue resolved at `issues/tardis_smarkets_test_regression_2026_05_17.md`); 15.2-15.4 require operator VM launches
  (human-only). Plan stays active pending operator smoke kick-off.
- ✅ **`dex_perp_and_venue_data_expansion_2026_05_12` remainder** (3.1 cal, 21/34) — close out 13 open todos. (design
  0.6×, ~5 = 3.0 cal) — **AUDIT 2026-05-17 (slot-3)**: 32/34 items done. 2 remaining: (1) BLOCKED-OPERATOR-DECISION (VM
  launcher for Extended OHLCV backfill, awaiting operator decision), (2) NICE-TO-HAVE P3 (Uniswap V3 tick-state subgraph
  research, non-blocking). No agent-actionable scope remains.
- ✅ **`mtds_databento_path_streaming_2026_05_07`** (1.2 cal) — Databento streaming path. Slot 3 context fit. (design
  0.6×, ~2 = 1.2 cal) — **DONE 2026-05-16 (prior slot-3)**: plan `status: done`. Phase 1 at MTDS@d8358f9, Phase 2+3
  DEFERRED-PER-PLAN (no wall-clock bottleneck). 2 test regressions from Phase 1 fixed at MTDS@139e2e6 (2026-05-17).
- ✅ **[DISCOVERED 2026-05-18] aave_rate_impact_calculator pre-existing test regression** —
  `test_get_rate_params_known_symbol` hardcoded `Decimal("0.90")` for USDC `optimal_utilization`; UAC SSOT updated to
  0.92 when Bug 6 fix shipped; test became stale. Fixed to assert against live UAC SSOT value.
  features-service@87667bf0. (0.1 cal)

#### Slot 4 — **[SWEEP-16]** items (+6 cal — sports/prediction expansion)

- ✅ **`cross_cutting_may_23_deliverables_2026_05_08` Ikenna-half** (12.4 cal, 18/30) — push remaining cross-cutting
  deliverables. Slot 4 has sports/prediction context. (design 0.6×, ~10 = 6.0 cal) — **AUDIT 2026-05-16 (slot 4)**: All
  Ikenna-side design work shipped pre-SWEEP-16 per plan body line 638-697: catalogue UAC schema ✅ (uac@…); strategy-ID
  schema + DERIVATION ✅ (uac@d6d0cd57); ClientDefinition + TradingAccount + CapitalAllocation ✅ (uac@3591037 →
  internal/architecture_v2/capital_allocation.py); DART scope decision ✅ (PM@ab595616 dart-manual-trade-spec.md, 314
  lines); ManualInstruction + audit-log UAC contracts ✅ shipped Ikenna T8 (Day-1/2/3 — uac@1d8a059 + fe8e50e + 003b5ff,
  22 unit tests). Plan body line 104-105 confirms `ManualInstruction.side` already covers sports `HOME/AWAY/DRAW` +
  prediction `YES/NO` and `operation_type` covers `PLACE_BET` — sports/prediction-specific UAC types already on LDR. 11
  remaining open items are explicitly Harsh-T6 [BUILD]/[SCRIPT] (UI builds + consumer wiring). Slot 4 has no implementer
  surface in the Ikenna-half closure beyond the bookkeeping flip recorded here. Plan stays `status: active` pending
  Harsh-T6 DONE block.

#### Slot 5 — **[SWEEP-16]** items (+8 cal — TradFi/cross-cutting closure)

- **`code_freeze_migrate_backfill_sequencing_2026_05_10` Ikenna cross-cutting subset** (112.9 cal total, 37/122) — pull
  TradFi + cross-asset items; bulk stays Harsh-side cefi_master. (design 0.6×, ~10 = 6.0 cal)

- **`live_pipeline_mtds_mdps_features_2026_05_08` Ikenna portion** (15.0 cal) — DeFi instrument live-pipeline
  activation; slot 3 owns perp/venue/DEX theme already. (design 0.6×, ~15 = 9.0 cal)
- **`dex_perp_and_venue_data_expansion_2026_05_12` remainder** (3.1 cal, 21/34) — close out 13 open todos. (design 0.6×,
  ~5 = 3.0 cal)
- **`mtds_databento_path_streaming_2026_05_07`** (1.2 cal) — Databento streaming path. Slot 3 context fit. (design 0.6×,
  ~2 = 1.2 cal)

#### Slot 4 — **[SWEEP-16]** items (+6 cal — sports/prediction expansion)

- **`cross_cutting_may_23_deliverables_2026_05_08` Ikenna-half** (12.4 cal, 18/30) — push remaining cross-cutting
  deliverables. Slot 4 has sports/prediction context. (design 0.6×, ~10 = 6.0 cal)

#### Slot 5 — **[SWEEP-16]** items (+8 cal — TradFi/cross-cutting closure)

- **`code_freeze_migrate_backfill_sequencing_2026_05_10` Ikenna cross-cutting subset** (112.9 cal total, 37/122) — pull
  TradFi + cross-asset items; bulk stays Harsh-side cefi_master. (design 0.6×, ~10 = 6.0 cal)
- **`wave3x_residual_ssots_2026_05_08` close** (0.9 cal, 17/23). (refactor 0.4×, ~2 = 0.8 cal)
- ✅ **`tradfi_canonical_futures_contract_hard_required_fields_2026_05_13` flip-verify** (100% — confirm). (~0.1 cal) —
  **VERIFIED 2026-05-16 (slot 5 ikenna)**: plan archived at
  `plans/archive/tradfi_canonical_futures_contract_hard_required_fields_2026_05_13.md` per slot owner's flip earlier
  this cycle. All phases shipped (Phase 3 migration IS@db070da + Phase 4 consumer cascade
  IS@0c59485/IS@bcb34b9/IS@2be7e4b + Phase 5 QG ratchet PM@32c7ea52). Discovery noted in slot 5 #4 flip:
  `_write_futures_contracts` write path at IS@2be7e4b exists but isn't producing parquets in prod (no
  `futures_contracts.parquet` files across 2024-2026 × all venues); follow-up scope for Phase 4.2 owner.

#### Slot 6 — **[SWEEP-16]** items (+14 cal — wallet/credentials/manifest/alerting)

- **`api_keys_wallets_accounts_readiness_2026_05_10` Phase 8 remainder** (25.9 cal, 52/87) — push remaining Phase
  8.A/8.B/8.D items. (design 0.6×, ~15 = 9.0 cal)
- **`alerting_service_live_rules_2026_05_07` close** (3.0 cal, 50/65) — push 15 remaining alerting rule items. (design
  0.6×, ~5 = 3.0 cal)
- ✅ **`manifest_schema_final_gate_2026_05_09` Phase 9.A** — E3 7-item checklist VERIFIED 2026-05-17: all 7 items PASS
  (UTL v8 schema, BATCH\_<source> on all handlers, ManifestFreshnessCache ttl=60, 17 launchers
  VM_NAME+MANIFEST_PER_VM_SHARDS, ServiceBootstrap events, Phase 6.C tarballs [x], watchdog dict complete).
  PM@`f8b9f3d2`. Phase 8+11+12 remain BLOCKED-OPERATOR. (design 0.6×, ~2 = 1.2 cal)

#### Slot 7 — **[SWEEP-16]** items (+12 cal — simulation + batch_live_symmetry + defi sim)

- **`simulation_scenarios_topology_price_shocks_2026_05_09`** (10.9 cal, 34/74) — close 40 open topology shock
  scenarios. (design 0.6×, ~10 = 6.0 cal)
- **`batch_live_symmetry_2026_05_10` Tabs 1-2 codex docs** (20.6 cal total, 22/70) — Harsh slot 5 was on this; absorb
  the codex docs half. (design 0.6×, ~5 = 3.0 cal)
- **`defi_simulation_realism_2026_05_10` close** (3.4 cal, 42/47) — push 5 remaining items. (design 0.6×, ~5 = 3.0 cal)

#### Slot 8 — **[SWEEP-16]** items (+12 cal — governance + audit + close-out + archive) — **CLOSED 2026-05-16**

- ✅ **`governance_qg_automation_gaps_post_cutover_2026_05_12`** — ALL 6 GROUPS CLOSED 2026-05-16 (slot-8): Group A
  `PM@42aa8bc1` (plan-discipline, baseline 231) + Group B `PM@42c7be41` (codex freshness, baseline 188) + Group C
  `PM@ab60c339` (architectural ratchets ST-19/PB-19/UI-18, baseline 0) + Group D `PM@501dbe6d/a791800d` (openapi drift
  contract + corrective fix after structural-mismatch finding) + Group E `PM@501dbe6d` (operator-attentiveness, no-cron
  decision) + Group F `PM@0c35f6ee` (STALE_OPEN_ALERT contract codified). (design 0.6×, ~5 = 3.0 cal — DONE)
- 🟡 **`compute_optimization_mock_data_2026_05_13` Ikenna-half** — DEFERRED-NEXT-SLOT: 8 remaining items require real
  GCE profiling runs + big-machine SKU benchmark matrix. Recommend slot-6 ML-infra owner post-cutover. (design 0.6×, ~3
  = 1.8 cal — DEFERRED-NEXT-SLOT)
- 🟡 **`promote_workflow_may23_cli_path_2026_05_10`** — DEFERRED-OPERATOR: all remaining are operator-runnable
  (preflight + 2yr backtest + Copper provisioning + Telegram tokens + recon dry-run). (design 0.6×, ~3 = 1.8 cal —
  DEFERRED-OPERATOR)
- 🟡 **`codex_vs_citadel_infrastructure_audit_2026_05_10` close** — DEFERRED-OPERATOR: 3 remaining (operator review +
  sign-off + master plan row — slot-1 main owns master plan per slot precedence). (research 1.2×, ~1 = 1.2 cal —
  DEFERRED-OPERATOR)
- 🟡 **`mock_data_pipeline_benchmarking_2026_05_10` close** — DEFERRED-OTHER-SLOT: 3 remaining P2-DEFERRED items owned
  by slot-7. (design 0.6×, ~1 = 0.6 cal — DEFERRED-OTHER-SLOT)
- 🟡 **`cross_asset_group_catalogue_audit_2026_05_10` close** — BLOCKED-OPERATOR-DECISION: 1 final item (ICE US softs
  UAC module placement). (research 1.2×, ~0.5 = 0.6 cal — BLOCKED-OPERATOR-DECISION)
- 🔄 **`deployment_and_qg_strategy_implementation_2026_05_13` final close** — PARTIAL: Phase 8.A item 1
  (`coverage_targets.yaml`, 11 surfaces) ✅ `PM@625769d5`. 19 remaining items substantial (per-repo
  coverage_targets_local × 20 + Phase 8.B/8.C surface coverage push + tarball SHA pinning + audit-log wire-in +
  act-preflight workflow). (infra 0.8×, ~5 = 4.0 cal — partial 0.5 cal closed)
- ✅ **Archive 11 fully-done plans** — DONE `PM@2d34b45c`. (refactor 0.4×, ~1 = 0.4 cal)

**Slot-8 SWEEP-16 net haul** (~5.4 cal closed clean + ~6.6 cal triaged with blocker class):
governance_qg_automation_gaps (all 6 groups) + Phase 8.A coverage_targets.yaml + 11-plan archive sweep + Group D
corrective fix + 6 RESOLVED issues archived (2 sweeps). All deferred items have explicit blocker class
(DEFERRED-OPERATOR / DEFERRED-NEXT-SLOT / DEFERRED-OTHER-SLOT / BLOCKED-OPERATOR-DECISION) per CLAUDE.md taxonomy.

**Additional uncounted slot-8 work this cycle**: aave-lending-rate-val P1 no-shutdown fix `deployment-service@472f9ca` +
deployment_events_lifecycle 3 GCS policies applied + service_registry P3 self-doc + gap-2.6.A-E Phase 2.6 cutover
tooling (5 items) + 2 orchestrator absorb items (workspace_manifest_drift + workflow_template_rollout) +
vm_image_build_caching_gaps P1 Dockerfile reorders (execution-service + strategy-service) + pyproject_workspace_audit
Findings 1+2 (line-length + fail_under bumps across 4 repos).

### Slot 1 main — **[SWEEP-16]** orchestrator additions

- **workspace-qg.yml redesign** (~3 cal) — design unified template covering all 5 trigger patterns without dropping LDR
  triggers; canary against `alerting-service@05dec98`; answer 7 open design questions inline in
  `plans/active/issues/workspace_qg_yml_redesign_2026_05_15.md`; roll out tomorrow if canary green. (design 0.6×, ~5 =
  3.0 cal)
- **DAI IRM VM relaunch coordination** — once slot 6 ships DAI IRM source fix, launch `aave-lending-rate-val-` VM again
  for re-verification. (infra 0.8×, ~0.5 = 0.4 cal)

- **`api_keys_wallets_accounts_readiness_2026_05_10` Phase 8 remainder** (25.9 cal, 52/87) — push remaining Phase
  8.A/8.B/8.D items. (design 0.6×, ~15 = 9.0 cal)
- **`alerting_service_live_rules_2026_05_07` close** (3.0 cal, 50/65) — push 15 remaining alerting rule items. (design
  0.6×, ~5 = 3.0 cal)
- **`manifest_schema_final_gate_2026_05_09` remainder** (1.1 cal, 26/56) — Phase 8 + 11 + 12 carry-overs not in slot 6
  #1 (which is Phase 6+7). (design 0.6×, ~2 = 1.2 cal)

#### Slot 7 — **[SWEEP-16]** items (+12 cal — simulation + batch_live_symmetry + defi sim)

- **`simulation_scenarios_topology_price_shocks_2026_05_09`** (10.9 cal, 34/74) — close 40 open topology shock
  scenarios. (design 0.6×, ~10 = 6.0 cal)
- **`batch_live_symmetry_2026_05_10` Tabs 1-2 codex docs** (20.6 cal total, 22/70) — Harsh slot 5 was on this; absorb
  the codex docs half. (design 0.6×, ~5 = 3.0 cal)
- **`defi_simulation_realism_2026_05_10` close** (3.4 cal, 42/47) — push 5 remaining items. (design 0.6×, ~5 = 3.0 cal)

#### Slot 8 — **[SWEEP-16]** items (+12 cal — governance + audit + close-out + archive) — **CLOSED 2026-05-16**

- ✅ **`governance_qg_automation_gaps_post_cutover_2026_05_12`** — ALL 6 GROUPS CLOSED 2026-05-16 (slot-8): Group A
  `PM@42aa8bc1` (plan-discipline, baseline 231) + Group B `PM@42c7be41` (codex freshness, baseline 188) + Group C
  `PM@ab60c339` (architectural ratchets ST-19/PB-19/UI-18, baseline 0) + Group D `PM@501dbe6d/a791800d` (openapi drift
  contract + corrective fix after structural-mismatch finding) + Group E `PM@501dbe6d` (operator-attentiveness, no-cron
  decision) + Group F `PM@0c35f6ee` (STALE_OPEN_ALERT contract codified). (design 0.6×, ~5 = 3.0 cal — DONE)
- 🟡 **`compute_optimization_mock_data_2026_05_13` Ikenna-half** — DEFERRED-NEXT-SLOT: 8 remaining items require real
  GCE profiling runs + big-machine SKU benchmark matrix. Recommend slot-6 ML-infra owner post-cutover. (design 0.6×, ~3
  = 1.8 cal — DEFERRED-NEXT-SLOT)
- 🟡 **`promote_workflow_may23_cli_path_2026_05_10`** — DEFERRED-OPERATOR: all remaining are operator-runnable
  (preflight + 2yr backtest + Copper provisioning + Telegram tokens + recon dry-run). (design 0.6×, ~3 = 1.8 cal —
  DEFERRED-OPERATOR)
- 🟡 **`codex_vs_citadel_infrastructure_audit_2026_05_10` close** — DEFERRED-OPERATOR: 3 remaining (operator review +
  sign-off + master plan row — slot-1 main owns master plan per slot precedence). (research 1.2×, ~1 = 1.2 cal —
  DEFERRED-OPERATOR)
- 🟡 **`mock_data_pipeline_benchmarking_2026_05_10` close** — DEFERRED-OTHER-SLOT: 3 remaining P2-DEFERRED items owned
  by slot-7. (design 0.6×, ~1 = 0.6 cal — DEFERRED-OTHER-SLOT)
- 🟡 **`cross_asset_group_catalogue_audit_2026_05_10` close** — BLOCKED-OPERATOR-DECISION: 1 final item (ICE US softs
  UAC module placement). (research 1.2×, ~0.5 = 0.6 cal — BLOCKED-OPERATOR-DECISION)
- 🔄 **`deployment_and_qg_strategy_implementation_2026_05_13` final close** — PARTIAL: Phase 8.A item 1
  (`coverage_targets.yaml`, 11 surfaces) ✅ `PM@625769d5`. 19 remaining items substantial (per-repo
  coverage_targets_local × 20 + Phase 8.B/8.C surface coverage push + tarball SHA pinning + audit-log wire-in +
  act-preflight workflow). (infra 0.8×, ~5 = 4.0 cal — partial 0.5 cal closed)
- ✅ **Archive 11 fully-done plans** — DONE `PM@2d34b45c`. (refactor 0.4×, ~1 = 0.4 cal)

**Slot-8 SWEEP-16 net haul** (~5.4 cal closed clean + ~6.6 cal triaged with blocker class):
governance_qg_automation_gaps (all 6 groups) + Phase 8.A coverage_targets.yaml + 11-plan archive sweep + Group D
corrective fix + 6 RESOLVED issues archived (2 sweeps). All deferred items have explicit blocker class
(DEFERRED-OPERATOR / DEFERRED-NEXT-SLOT / DEFERRED-OTHER-SLOT / BLOCKED-OPERATOR-DECISION) per CLAUDE.md taxonomy.

**Additional uncounted slot-8 work this cycle**: aave-lending-rate-val P1 no-shutdown fix `deployment-service@472f9ca` +
deployment_events_lifecycle 3 GCS policies applied + service_registry P3 self-doc + gap-2.6.A-E Phase 2.6 cutover
tooling (5 items) + 2 orchestrator absorb items (workspace_manifest_drift + workflow_template_rollout) +
vm_image_build_caching_gaps P1 Dockerfile reorders (execution-service + strategy-service) + pyproject_workspace_audit
Findings 1+2 (line-length + fail_under bumps across 4 repos).

### Slot 1 main — **[SWEEP-16]** orchestrator additions

- **workspace-qg.yml redesign** (~3 cal) — design unified template covering all 5 trigger patterns without dropping LDR
  triggers; canary against `alerting-service@05dec98`; answer 7 open design questions inline in
  `plans/active/issues/workspace_qg_yml_redesign_2026_05_15.md`; roll out tomorrow if canary green. (design 0.6×, ~5 =
  3.0 cal)
- **DAI IRM VM relaunch coordination** — once slot 6 ships DAI IRM source fix, launch `aave-lending-rate-val-` VM again
  for re-verification. (infra 0.8×, ~0.5 = 0.4 cal)
- **Phase 7.G operator sign-off coordination** (already in slot 1 stack from 15 May).
- **Daily inventory regenerator** + master plan refresh continued.

### SWEEP-16 totals

| Slot      | Existing 15-May stack | + SWEEP-16 | New total |
| --------- | --------------------- | ---------- | --------- |
| 2         | ~20                   | ~3.7       | ~24       |
| 3         | ~18                   | ~13.2      | ~31       |
| 4         | ~19                   | ~6.0       | ~25       |
| 5         | ~20                   | ~6.9       | ~27       |
| 6         | ~22                   | ~13.2      | ~35       |
| 7         | ~28                   | ~12.0      | ~40       |
| 8         | ~18                   | ~12.8      | ~31       |
| **Total** | ~145                  | **~68**    | **~213**  |

| Slot      | Existing 15-May stack | + SWEEP-16 | New total |
| --------- | --------------------- | ---------- | --------- |
| 2         | ~20                   | ~3.7       | ~24       |
| 3         | ~18                   | ~13.2      | ~31       |
| 4         | ~19                   | ~6.0       | ~25       |
| 5         | ~20                   | ~6.9       | ~27       |
| 6         | ~22                   | ~13.2      | ~35       |
| 7         | ~28                   | ~12.0      | ~40       |
| 8         | ~18                   | ~12.8      | ~31       |
| **Total** | ~145                  | **~68**    | **~213**  |

Plus slot 1 main: ~3.4 cal SWEEP-16 (workspace-qg.yml + DAI VM coord).

**~290 cal AI-days remaining May-23 → distribution gap (~80 cal)** is in `code_freeze_migrate_backfill_sequencing`
Harsh-side bulk (~100 cal) which stays Harsh-side per cefi_master ownership. Ikenna can absorb if Harsh capacity
constrained.

### Pickup discipline

Slot owners pull from SWEEP-16 items AFTER current top-of-stack item lands. Each SWEEP-16 item starts with the
**[SWEEP-16]** marker so it's easy to grep. Per-item Half-1+Half-2 flip discipline applies (no batch flips).

Cross-side coordination: Harsh slot 8 still has remaining cefi_master bulk; do NOT duplicate work. Spot-check LDR before
starting any SWEEP-16 item to see if Harsh has shipped it.

**Race-to-finish target**: workspace dashboard at ≤200 cal-days remaining by EOD 2026-05-17 = ~75 cal burn rate across
both sides per day = comfortable at density-push pace.

Cross-side coordination: Harsh slot 8 still has remaining cefi_master bulk; do NOT duplicate work. Spot-check LDR before
starting any SWEEP-16 item to see if Harsh has shipped it.

**Race-to-finish target**: workspace dashboard at ≤200 cal-days remaining by EOD 2026-05-17 = ~75 cal burn rate across
both sides per day = comfortable at density-push pace.
