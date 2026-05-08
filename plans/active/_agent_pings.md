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

_(empty — Tab 10 ✅ DONE; Tab 9 Q1 + Q2 ✅ RESOLVED (Q2 operator-deferred rebase 07:18 UTC); Bugs 1+3 ✅ validated end-to-end via UAC@6a64a56 + MTDS@c6bdf96 + IS@6ae50de (already pushed). Tab 9 continuing VM validation at T+75min. Tabs 2, 9, 11 IN FLIGHT. Tabs 12/13/14 QUEUED. PM rebase pending — 4 local-ahead commits will rebase on 150c1d5 later.)_
