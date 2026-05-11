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

_(swept clean 2026-05-11 by slot 1 main agent — all 8 pings handled: slots 2/3/4/6/7 ✅ DONE primary + re-task scope; slot 8 ✅ DONE all 5 in-scope P0-2 MDPS surgery steps incl. final EXPECTED_KNOWN_SOURCE_GAP reason upgrade at MDPS@`01f08b6` + CandleProcessingService dead-branch removal at MDPS@`a964b96` (coverage 73.18% → 74.63%); Step 5 (output_schemas.py OHLCV nullability) remains DEFERRED-AFTER `hard_schema_enforcement_2026_05_08.md` per task brief; 3 historical pings from 2026-05-08/09/10 (wave-8 / instruments-preflight / agent-arb-fundrate) had been ✅ acked long ago. Full DONE evidence + audit-findings + slot 8 finalization details preserved in plan bodies (`writegate_honest_coverage_endtoend_2026_05_06.md § DONE-2026-05-11 — slot 8 P0-2 surgery`) + commit messages + LEDGER's slot 8 entry. Slot 8's coordination note re VIX-gap consumer (MDPS@`2f163c1`+`01f08b6` — conservative non-NaN-bar refactor + EXPECTED_KNOWN_SOURCE_GAP reason upgrade; Harsh slot 5 rebases on top if catalog-aware version in flight) preserved in writegate plan body.)_

[2026-05-11 ~now UTC] ikenna-phase-1d-tab — ROUND 2 STARTED. Phase 1.D continuation: Risk Phase 2 (per-axis registry + family aggregator) + Phase 3 (UTL pre-flight evaluator) + Phase 7 (codex SSOTs) + Alerting P1 tick-staleness migration. 6 sub-agents fanned out in parallel: (D) risk archetype registry, (E) risk venue/account/client/asset_group/global registries, (F) risk family rules + UTL aggregator, (G) risk UTL rule_evaluator + preflight + ≥40 tests, (H) risk codex 2 NEW + 2 UPDATE, (I) alerting tick-staleness UAC+router+codex. Plans: risk_simulations_limits_alerting_2026_05_10.md + alerting_service_live_rules_2026_05_07.md.
