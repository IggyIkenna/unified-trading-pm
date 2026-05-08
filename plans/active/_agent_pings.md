<!--
Lightweight ping ledger — the doorbell.

Sub-agents append a one-liner here when they need attention from the main agent.
The main agent polls this file every ~10 min via /loop, reads the referenced plan
doc, answers in the plan doc's `## Open questions` section, then removes the line
from this file.

Format (one line per active ping):
  [YYYY-MM-DD HH:MM UTC] <agent-tag> — <one-liner with plan-doc pointer>

Examples:
  [2026-05-08 09:14 UTC] phase2-routes-tab — Q on subprocess.run timeout default; see deployment_api_work_stream_a_2026_05_07.plan.md
  [2026-05-08 09:32 UTC] dart-playwright-tab — done with personas 1-3, blocked on persona 4 fixture; see strategy_and_dart_master_2026_05_07.plan.md
  [2026-05-08 10:01 UTC] manifest-rescan-tab — silent-zero finding for prediction asset_group; see issues/prediction_silent_zero_2026_05_08.md

This file is EPHEMERAL — entries are removed when handled. Full Q&A history lives
in the referenced plan doc's `## Open questions` section (status badges 🟡 BLOCKED
→ ✅ RESOLVED).

When this ledger consistently has 15-20+ active pings, signal Harsh to spawn a
SECOND main agent in another tab; two main agents can divide the ledger using a
[CLAIMED-BY: main-1] / [CLAIMED-BY: main-2] marker on each ping.

Full lifecycle + format spec: plans/active/work_split_2026_05_07_harsh_5tab_layout.md
-->

# Active pings

_(empty — STARTED pings ack'd 2026-05-08 06:18 UTC for Tabs 9 (06:12), 10 (06:13), 11 (06:15). All clean boots, no flags. 4 tabs IN FLIGHT (2/9/10/11). Tabs 12/13/14 still QUEUED pending operator review.)_

[2026-05-08 06:39 UTC] predictions-phase1-ingestion-tab — DONE Tab 10 — Phase 1 instruments-service half shipped (instruments-service@98bb167 + b904785, PM@7343b93 + 8526f99); Phase 2 MTDS half explicitly deferred per plan body's "Temporary states" section. See predictions_master_2026_05_07.plan.md ## DONE-2026-05-08.
[2026-05-08 06:43 UTC] lending-indices-relaunch-tab — 🟡 BLOCKED Tab 9 (Q1): Bug 1 still reproduces on AAVE V3 ETHEREUM; root-caused to UAC PROTOCOL_LAUNCH_DATES[("ETHEREUM","AAVEV3")]="2022-03-14" likely wrong (real launch 2023-01-27) AND Bug 3 routes pre-launch to SOURCE_RETURNED_ZERO instead of EXPECTED_PRE_GENESIS_CHAIN. Big finding (contradicts Tab 5 DONE-block + UAC SSOT). VM left running. Full Q1 + recommended decision in issues/lending_indices_handler_bugs_2026_05_07.md.
