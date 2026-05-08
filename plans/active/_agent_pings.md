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

Full lifecycle + format spec: cursor-configs/CLAUDE.md § "Daily Work-Split Process" — Plan-of-record + Q&A bus / Ping ledger / Polling cadence subsections.
-->

# Active pings

_(empty — Tab 12 Q1 ✅ RESOLVED ~10:30 UTC; operator picked (b) Defer per features_repo_consolidation_2026_05_08
absorption. All 12 spawned tabs ✅ DONE today (3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14). Only Tab 2 (cefi-babysit) still
IN FLIGHT. Beef-up sub-agent BLOCKED ping resolved via fast-forward rebase + push of sports_master beef-up.)_

[2026-05-08 14:00 UTC] alerting-phase2-publisher-hook — UAC rules.py parallel-edit collision blocking kill_switch_scope
field; see alerting_service_live_rules_2026_05_07.md [2026-05-08 12:43 UTC] deploy-missing-phase0-facilitation — 3
IAM/audit/rate-limit decisions ready for operator review; see deploy_missing_auto_launch_2026_05_07.md § "Operator
decision summary".

[2026-05-08 ~now UTC] uac-strategy-catalogue-ids-tab6a — cross_cutting #1+#2 already shipped under UAC architecture_v2,
plan-body design would create parallel SSOTs + collide with live `strategy.py` facade — operator triage needed; see
issues/cross_cutting_strategy_catalogue_already_shipped_2026_05_08.md + cross_cutting_may_23_deliverables_2026_05_08.md.
