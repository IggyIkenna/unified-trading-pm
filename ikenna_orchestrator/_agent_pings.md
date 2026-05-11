<!--
Lightweight ping ledger — the intra-side doorbell (Ikenna's main ↔ Ikenna's spawned tabs).

For Ikenna ↔ Harsh CROSS-SIDE comms use plans/active/_agent_pings.md instead — keep the
two ledgers separate so the cross-side surface stays uncluttered with intra-Ikenna
STARTED/DONE acks.

Sub-agents append a one-liner here when they need attention from the main agent.
The main agent polls this file every ~1 min while operator is active (stretches to
~5 min when ledger empty for 30+ min), reads the referenced plan doc, answers in
the plan doc's `## Open questions` section, then removes the line from this file.

Format (one line per active ping):
  [YYYY-MM-DD HH:MM UTC] <agent-tag> — <one-liner with plan-doc pointer>

Examples:
  [2026-05-08 09:14 UTC] defi-launch-tab — STARTED Tab 2 (plans/active/defi_master_2026_05_07.md)
  [2026-05-08 09:32 UTC] live-pipeline-tab — Q on Phase 4 MDPS reader template; see plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md
  [2026-05-08 10:01 UTC] alerting-tab — DONE Tab 6 Phase 2 KillSwitchBus rule wiring; see plans/active/alerting_service_live_rules_2026_05_07.md

This file is EPHEMERAL — entries are removed when handled. Full Q&A history lives
in the referenced plan doc's `## Open questions` section (status badges 🟡 BLOCKED
→ ✅ RESOLVED).

When this ledger consistently has 15-20+ active pings, signal Ikenna to spawn a
SECOND main agent in another tab; two main agents can divide the ledger using a
[CLAIMED-BY: main-1] / [CLAIMED-BY: main-2] marker on each ping.

Full lifecycle + format spec: cursor-configs/CLAUDE.md § "Daily Work-Split Process" — Plan-of-record + Q&A bus / Ping ledger / Polling cadence subsections.
-->

# Active pings

[2026-05-11 ~now UTC] [main → slot 3] — RE-TASK after ✅ DONE original scope. **DECONFLICTED 2026-05-11 PM**: original re-task had 3 items; item (a) UAC `EXPECTED_KNOWN_SOURCE_GAP` enum addition is now owned by **slot 6** (its spawn prompt per PM@`2e7cfeea` assigns it explicitly). Slot 3 picks up 2 items: (a) flip sports `available_at` Phase 1 todo in `available_at_lookahead_bias_completion_2026_05_08.md` per Harsh slot 4's `MTDS@c186ecb` ship; (b) answer 4 design Qs Q-A/B/C/D in `plans/active/issues/mtds_sports_available_at_wiring_2026_05_11.md` § "Open design questions". Full brief: `plans/active/work_split_2026_05_11_ikenna.md` § "Slot 3 — RE-TASK BRIEF". **Do NOT touch MDPS VIX-gap consumer** (`_maybe_write_vix_gap_placeholder`) — that's Harsh slot 5's territory per the P0-2 routing. ~1-2 hrs.

[2026-05-11 ~now UTC] [main → slot 4] — RE-TASK: your spawn prompt's "BLOCKED on features_repo_consolidation_2026_05_08
Phase 7 (Harsh slot 2)" gate is **STALE**. Verified 2026-05-11: `features_repo_consolidation_2026_05_08.md:678` Phase 7
`[x]` flipped; `workspace-manifest.json` shows 8 features-\*-service repos
`archived_into=features-service archive_date=2026-05-08`; 8 source repos archived on GitHub. Phase 7 cleared 3 days ago.
Promote your 5 design stubs to actual implementation: (1) `MDPSStreamingAggregator` UTL stub → real impl per
`codex/05-infrastructure/live-pipeline-architecture.md` Phase 4 design; (2) `AssetScopedFeaturesRunner` UTL stub → real
impl; (3) `CrossCuttingFeaturesRunner` UTL stub → real impl; (4) `deployment-api /api/data-status/live` endpoint stub →
wire to real `data_freshness` callback; (5) `<LiveDataStatusTab/>` deployment-ui scaffold → wire to live API; (6)
plan-flip Phase 4/5/6 implementation halves `design-shipped` → `[x]` with `<repo>@<sha>` evidence. Full brief:
`plans/active/work_split_2026_05_11_ikenna.md` § "Slot 4 — RE-TASK BRIEF". Coordinate via cross-side ping with Harsh
slot 5 (per-service consumers were waiting on your design promotion). ~6-10 hrs.

[2026-05-11 ~13:45 UTC] ikenna-writegate-slice-b-tab (slot 2) — ✅ Q1 RESOLVED by operator PM@`39ab61e5` (option b: manifest_schema_final_gate canonical v8 owner; slot 2 scope re-threaded to UTL helper + MDPS POC + deployment-api/ui + codex/CLAUDE.md + ship-gate). Resuming Phase 5.1 (UTL `manifest_completeness` helper) first.

[2026-05-08 21:21 UTC] wave-8-basefc-validationflip — DONE audit; 74 calcs (not 12), paradigm split, 3-step migration;
NO code shipped (foreign WIP on UTL registry.py + scope multi-day); successor plan needed post-Phase-6; see
plans/active/issues/basefc_validation_flip_audit_2026_05_08.md (PM@142f7289) [2026-05-09 00:18 UTC]
instruments-preflight-gate-tab F0 — DONE A.9 + A.10 SHIPPED (UAC@a07711d facade + UAC@8f89ec4 module + UTL@db0f4364
helper); F2 cefi-available-at-stamping-tab UNBLOCKED —
`from unified_trading_library.instruments_preflight import run_preflight, PreflightFailedError, UTLManifestReader`; see
plans/epics/instruments_live_master_2026_05_08.md § A.9 + A.10 [2026-05-10 06:00 UTC] agent-arb-fundrate-c3 — ✅ DONE
Phase A Commit 3 + A.7; Q11 RESOLVED. Engine 8-step loop at strategy-service@04c0d52; allocator multi-pair branch (b) at
strategy-service@de9b4b0; PM plan flips at PM@4184c112 + this commit. Phase A complete; Phase B unblocked next. See
plans/active/arbitrage_price_dispersion_finalisation_2026_05_09.md.

[2026-05-11 ~now UTC] ikenna-phase-1d-tab — STARTED slot 7 (Phase 1.D: alerting + risk + DR). Fanning out 3 sub-agents
in ONE message: (A) alerting Phase 2.X pattern→event_pattern rename + ML codex; (B) risk Phase 0+1.A-E (RiskRule +
StrategyFamily + AlertCode 39→45); (C) DR Phase 0+1.A-F (circuit_breaker + kill_switch UAC). Master coordination: I
commit 6 LIVE_ALERT_RULES entries after Sub-A rename + Sub-B codes land. Plans:
alerting_service_live_rules_2026_05_07.md / risk_simulations_limits_alerting_2026_05_10.md /
disaster_recovery_circuit_breakers_2026_05_10.md.

[2026-05-11 ~now UTC] ikenna-slot7-risk-uac (Sub-B) — DONE risk Phase 0+1.A-E + 1.F cross-ref + 2.G. Shipped
UAC@945ad5d (risk_rule.py + strategy_family.py + risk.py facade + 6 AlertCodes 39→45 + 55 unit tests all green) +
UAC@dc4c9f0 (ruff fixes). PM@0044e370 (plan flips + banners on 3 cross-plan files + audit findings). FOOT-GUN #1
INCIDENT in UAC@dc4c9f0 — bundled Sub-C pre-staged test_circuit_breaker_taxonomy.py + test_kill_switch.py + __init__.py
reorder under Sub-B commit message (no data loss, wrong attribution). Mitigation noted in risk plan § Audit findings
0.D. Coordinator/Sub-C decide revert-vs-leave. Plan-of-record: risk_simulations_limits_alerting_2026_05_10.md.

[2026-05-11 ~now UTC] ikenna-slot8-p0-2-surgery — DONE P0-2 MDPS dead write-gate surgery (4 of 6 steps shipped per
slot 8 task brief). Step 1: legacy `_write_candles` MRO override deleted (mdps@d717c59) — CandleOrchestrationService
now resolves to canonical writer + 4-pillar gate via MRO. Step 2: TradFi ohlcv_passthrough 1440-NaN-bar shape deleted
(mdps@93883b7). Step 3: duplicated `_create_closed_market_candle` (both copies) + `_write_closed_market_candles` +
TRADFI special-case branch deleted; `_handle_empty_tick_data` now routes every asset_group through
`record_empty_for_shard` (mdps@2f163c1). Step 4: interim shipped via Step 3 (VIX gap → record_empty
SOURCE_RETURNED_ZERO); reason-kwarg upgrade to EXPECTED_KNOWN_SOURCE_GAP blocked on slot 3/slot 6 UAC enum ship per
manifest_schema_final_gate_2026_05_09 Phase 1. Step 5 OUT-OF-SCOPE per task brief. Step 6: triple-SSOT audit COMPLETE
— `MarketDataProcessingService(CandleProcessingService)` is NOT on production CLI path; 100+ LOC test-removal
deferred for operator triage. **COORDINATION NOTE for Harsh slot 5 + main**: line 34 ping mentions VIX-gap consumer
is Harsh slot 5's territory, but slot 8 task brief explicitly owned `_maybe_write_vix_gap_placeholder` as part of P0-2
step 3/4. The refactor I did (delete the `_write_closed_market_candles` call + add `record_empty_for_shard` interim)
is the conservative non-NaN-bar version; if Harsh slot 5 has a different (e.g. catalog-aware) version in flight,
they should rebase against mdps@2f163c1 + extend rather than revert. Full DONE block at writegate plan body just
above § Phase 0 audit findings — MTDS bundle adapter inventory. Plan-flip commits:
PM@52a3fbc0/46cd5ab3/d05143e6/30796569/9bd8d44a (Step-by-step) + this commit. Plan-of-record:
writegate_honest_coverage_endtoend_2026_05_06.md § Phase 2.A.

[2026-05-11 13:00 UTC] ikenna-slot8-p0-2-finalize — P0-2 surgery FINALIZATION SHIPPED + merged to origin/live-defi-rollout.
  Step 4 closed (VIX gap → record_empty(EXPECTED_KNOWN_SOURCE_GAP); mdps@01f08b6 — record_empty_for_shard +
  _emit_status_for_shard accept reason kwarg defaulting to SOURCE_RETURNED_ZERO for backward compat on cefi/defi/tradfi
  callers). Step 6 closed (CandleProcessingService dead-branch deleted + 4 source files + 5 test files / ~2090L removed;
  mdps@a964b96; coverage rose 73.18% → 74.63%). MDPS commits a964b96 + 01f08b6 + 6677728 + 849d039 + fe7deb5 NOW LIVE
  on origin/live-defi-rollout — VMs pulling from live-defi-rollout get the canonical_writer + 4-pillar gate live path.
  PM plan-flips: bf18c6db (Step 6 done) + 0736e4b2 (Step 4 done) + 5b3ea34d (DONE block) + earlier step 1-3 flips. All
  Steps 1/2/3/4/6 = ✅ done. Step 5 (output_schemas.py OHLCV nullability) remains DEFERRED-AFTER hard_schema_enforcement
  plan per task brief. Plan-of-record: writegate_honest_coverage_endtoend_2026_05_06.md §
  DONE-2026-05-11 — slot 8 P0-2 surgery (Finalization 2026-05-11 — slot 8 P0-2 finalize sub-agent subsection appended).
