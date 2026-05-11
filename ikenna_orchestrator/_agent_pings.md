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

[2026-05-11 ~now UTC] [main → slot 2] — **RE-TASK to manifest_schema_final_gate Phase 2 (UTL v8 ManifestWriter) — CRITICAL PATH** for 2026-05-15 freeze gate. Your writegate slice (b) primary scope ✅ DONE per PM@`2b207442`+`b0b01d9c`+`152db218`+`40aca8b4`+`2b7e4932`. Operator picked Option 2 from your 4-option re-task menu. Full brief: [`plans/active/work_split_2026_05_11_ikenna.md`](../plans/active/work_split_2026_05_11_ikenna.md) § "Slot 2 — RE-TASK BRIEF #2".

**Step 1 (~10 min)** — Adjacent quick win: clear slot 8's Q2 Bug 1 in `unified-api-contracts/unified_api_contracts/canonical/crosscutting/service_emission_policy.py:163-168` (6 keys + docstring at `:216`: `"market-data-pipeline-service"` → `"market-data-processing-service"`; actual service is MDPS). Update matching test at `market-data-processing-service/tests/unit/test_canonical_writer_ohlcv_1h_policy.py:199` if it references the old name. **Q2 Bug 2 (book_snapshot_5 key-shape) was already RESOLVED** by operator at PM@`fa806abe` — UAC code matches the decision (source-conceptual data_type tokens); just CLAUDE.md ratification. Ack to slot 8 via plan-of-record (`writegate_honest_coverage_endtoend_2026_05_06.md` Phase 6.2 + `plans/active/issues/writegate_uac_emission_policy_seed_dict_keys_mismatch_2026_05_11.md` flip to ✅ RESOLVED). Slot 8 unblocks → resumes Phase 6.2 in parallel with your Phase 2 work.

**Step 2 (~10-12 hrs)** — Phase 2 A/B/C/D per `manifest_schema_final_gate_2026_05_09.md:266-285`: (2.A) extend UTL `manifest_writer.py` 5 `record_*` functions with 3 new v8 kwargs (`service_emission_state` / `last_emission_decision_at` / `expected_window_completeness_fraction`, all defaulting to `None`); (2.B) `emission_publisher.publish_with_policy` integrates Phase 1.B `next_state(...)` resolver (slot 6 shipped at `UAC@174f401`) + passes to ManifestWriter; (2.C) `manifest_reader_fallback.py` v7-tolerance for ≤30d + `READER_BACKFILLED_V8_COLUMNS_AS_NULL` event; (2.D) NEW `manifest_migrations/v7_to_v8.py` per-VM-shard migration helper.

**Done-definition**: `unified-trading-library@<sha>` shipped + 11+ unit tests + back-compat with v7 rows. Slot 6's Phase 1 v8 column declarations are prereq (✅ shipped). No collision with slot 8 (separate Phase 6.2 scope). Phase 2 currently UNOWNED per post-pull state.

Per-shippable-unit commits + bundled push (slot branch + LDR FF) per CLAUDE.md "Commit + Push + Flip Plan Checkboxes" Half 4. Plan-flip in `manifest_schema_final_gate_2026_05_09.md` per shippable unit. EOD-audit per CLAUDE.md "End-of-cycle audit clause" before final DONE block.

_(swept clean 2026-05-11 by slot 1 main agent — all 8 pings handled: slots 2/3/4/6/7 ✅ DONE primary + re-task scope; slot 8 ✅ DONE all 5 in-scope P0-2 MDPS surgery steps incl. final EXPECTED_KNOWN_SOURCE_GAP reason upgrade at MDPS@`01f08b6` + CandleProcessingService dead-branch removal at MDPS@`a964b96` (coverage 73.18% → 74.63%); Step 5 (output_schemas.py OHLCV nullability) remains DEFERRED-AFTER `hard_schema_enforcement_2026_05_08.md` per task brief; 3 historical pings from 2026-05-08/09/10 (wave-8 / instruments-preflight / agent-arb-fundrate) had been ✅ acked long ago. Full DONE evidence + audit-findings + slot 8 finalization details preserved in plan bodies (`writegate_honest_coverage_endtoend_2026_05_06.md § DONE-2026-05-11 — slot 8 P0-2 surgery`) + commit messages + LEDGER's slot 8 entry. Slot 8's coordination note re VIX-gap consumer (MDPS@`2f163c1`+`01f08b6` — conservative non-NaN-bar refactor + EXPECTED_KNOWN_SOURCE_GAP reason upgrade; Harsh slot 5 rebases on top if catalog-aware version in flight) preserved in writegate plan body.)_

[2026-05-11 ~now UTC] ikenna-phase-1d-tab — ROUND 2 STARTED. Phase 1.D continuation: Risk Phase 2 (per-axis registry + family aggregator) + Phase 3 (UTL pre-flight evaluator) + Phase 7 (codex SSOTs) + Alerting P1 tick-staleness migration. 6 sub-agents fanned out in parallel: (D) risk archetype registry, (E) risk venue/account/client/asset_group/global registries, (F) risk family rules + UTL aggregator, (G) risk UTL rule_evaluator + preflight + ≥40 tests, (H) risk codex 2 NEW + 2 UPDATE, (I) alerting tick-staleness UAC+router+codex. Plans: risk_simulations_limits_alerting_2026_05_10.md + alerting_service_live_rules_2026_05_07.md.

[2026-05-11 ~16:00 UTC] ikenna-slot8-phase6-2-mdps-wiring — 🟡 BLOCKED on Q2 in writegate plan: UAC `SERVICE_OUTPUT_POLICIES` MDPS rows have service-name typo (`pipeline` vs `processing`) + `book_snapshot_5` key-shape ambiguity — silently breaks slice (b) POC + blocks Phase 6.2 wiring. Issue doc: plans/active/issues/writegate_uac_emission_policy_seed_dict_keys_mismatch_2026_05_11.md. Recommended fix (option a + α) in Q. Slot 8 wiring paused; read-only audit continues.

[2026-05-11 ~PM UTC] ikenna-slot8-q2-fix-phase6-2 — 🟢 PARTIAL DONE. Operator approved option (a + α). Q2 RESOLVED on `origin/live-defi-rollout`: UAC rename `pipeline`→`processing` (UAC@`7be6bd5`), UTL docstrings (UTL@`4d8de4ce`), CLAUDE.md option-α (PM@`fa806abe`), MDPS regression test asserting real UAC lookup (MDPS@`daf9988`), Q2 plan + issue doc flipped ✅ (PM@`a948857f`). **Task 6 Phase 6.2 wiring PARTIAL**: 152 LOC scaffolding (`_resolve_policy_output_data_type` + `_publish_emission_check` for ohlcv_1m/24h/book_snapshot_5) on `tab/ikennaigboaka/8` ONLY (MDPS@`ae0cada`); NOT FF'd to `live-defi-rollout` (dead helpers). Sub-agent rate-limited by Anthropic mid-Task-6; consumer wiring + per-data_type unit tests remain. Plan body line 3119-3126 annotated PARTIAL with commit pointer. Next slot 8 cycle picks up from `mdps@ae0cada` — head-start, not blank state. Slot 8 going quiet.

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

[2026-05-11 09:55 UTC] ikenna-live-pipeline-tab — ✅ DONE slot 4 design-ahead. Phase 4/5/6/11/14 design-only stubs
shipped: UAC@e55651b (FeaturesComputedEvent) + UTL@58bfbbeb (MDPSStreamingAggregator + Asset/CrossCutting features
runners + 11 contract tests) + deployment-api@7d95dc9 (/api/data-status/live + LiveStatusRow + 4 tests) +
deployment-ui@f3204ce (LiveDataStatusTab scaffold + 5 vitest tests) + PM@789201d0 (codex extension + plan flips +
scoreboard). All implementation gated on features_repo_consolidation Phase 7 (Harsh slot 2). See
plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md § DONE-2026-05-11.
[2026-05-11 10:35 UTC] ikenna-live-pipeline-tab — ✅ RE-TASK DONE slot 4 promote-to-implementation. After your re-task
ping (features_repo_consolidation Phase 7 cleared 2026-05-08; gate was stale), promoted Phase 4/5/6 UTL stubs to real
implementation: UTL@ee64481a (MDPSStreamingAggregator full async run loop + 4-category decision tree + cascade-partial)
+ UTL@35425c70 (AssetScopedFeaturesRunner + CrossCuttingFeaturesRunner real impls + Phase 6.2 worst-of propagation) +
PM@<this commit> (plan flips Phase 4/5/6 → [x], new scoreboard, cross-side ping to Harsh slot 5 unblocking per-service
consumer wiring). 27 unit tests pass across the 3 UTL primitives. DEFERRED in plan body (not blocking): cascade per-
shard buffer + cross-cutting watermark-buffered scheduler + deployment-api endpoint real-wiring (needs live producers
running). See plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md § DONE-2026-05-11 — Ikenna slot 4 RE-TASK.

[2026-05-11 10:55 UTC] ikenna-live-pipeline-tab — ✅ ADDITIONAL Phase 11.1 endpoint real wiring shipped after operator
pushback. deployment-api@9b0e81d promotes the /api/data-status/live endpoint from design-only stub to REAL manifest-
read wiring: reads v8 availability manifest per asset_group, filters pipeline_mode=live_websocket, builds LiveStatusRow
per shard with manifest-derived staleness from attempted_at, capture_status from 4-state taxonomy, resilient pre-v8 +
OSError handling. 10 unit tests (up from 4). The deployment-ui scaffold already calls fetch() against this endpoint —
real rows render the moment Harsh slot 5's per-service wiring lands. Health-API HTTP join for precise per-shard
last_event_age_seconds / degraded_ratio_60s / cluster_pct_skipped_60s DEFERRED on per-service URL registry in
DeploymentApiConfig — documented inline + in scoreboard. Phase 11.1 endpoint half now [x] done in plan.
[2026-05-11 ~now UTC] ikenna-phase-1d-tab — ROUND 3 STARTED. Slot 7 continues with 14 sub-agents in parallel covering DR Phase 2 + 3 (8 reconcilers) + 7 + 8 codex + Risk Phase 6 (deployment-api + UI). Plans: disaster_recovery_circuit_breakers_2026_05_10.md + risk_simulations_limits_alerting_2026_05_10.md.
