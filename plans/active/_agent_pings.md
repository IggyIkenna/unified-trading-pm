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

[2026-05-08 07:50 UTC] ml-features-phase2a-tab — Q1 🟡 BLOCKED [ESCALATED-TO-OPERATOR 07:55 UTC] scope ambiguity strategic — Tab 12 continuing with inventory map meanwhile; see ml_and_features_master_2026_05_07.plan.md ## Open questions Q1
[2026-05-08 08:20 UTC] lending-indices-relaunch-tab — ✅ DONE Tab 9 — VALIDATION block appended to issues/lending_indices_handler_bugs_2026_05_07.md. AAVE V3 ETH captured rows start exactly 2023-01-27 (53 captured @ T+123min, matching probe). Bug 1 RESOLVED end-to-end (UAC SSOT misdiagnosis). Bugs 1+3 fix shipped: UAC@6a64a56 + MTDS@c6bdf96 + IS@6ae50de all on origin. PM commits 69ebe5b + new VALIDATION commit LOCAL only — Q2 push deferred per operator 07:18 UTC. Going quiet.
