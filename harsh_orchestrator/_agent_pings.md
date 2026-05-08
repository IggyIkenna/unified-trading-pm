<!--
Lightweight ping ledger — the doorbell.

Sub-agents append a one-liner here when they need attention from the main agent.
The main agent polls this file every ~10 min via /loop, reads the referenced plan
doc, answers in the plan doc's `## Open questions` section, then removes the line
from this file.

Format (one line per active ping):
  [YYYY-MM-DD HH:MM UTC] <agent-tag> — <one-liner with plan-doc pointer>

Examples:
  [2026-05-08 09:14 UTC] phase2-routes-tab — Q on subprocess.run timeout default; see deployment_api_work_stream_a_2026_05_07.md
  [2026-05-08 09:32 UTC] dart-playwright-tab — done with personas 1-3, blocked on persona 4 fixture; see strategy_and_dart_master_2026_05_07.md
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

[2026-05-08 11:13 UTC] features-consolidation-tab — STARTED Tab 2 (plans/active/features_repo_consolidation_2026_05_08.plan.md + plans/epics/ml_and_features_master_2026_05_07.plan.md Phase 2A/2B+3); kicking off Phase 0 pre-audit fan-out
[2026-05-08 11:14 UTC] instruments-live-tab — STARTED Tab 1 (plans/epics/instruments_live_master_2026_05_08.md + plans/epics/predictions_master_2026_05_07.md Phase 2+3 + archived instruments_and_market_tick_data_completion_2026_05_01 catalog-aware writer-guard); starting with Predictions Phase 2 adapter lifecycle gating (instruments-service Phase 1 already shipped 98bb167 + b904785) — fanning out 3 sub-agents (Polymarket adapter, Kalshi adapter, UMI tick provider rename + writer migration)
[2026-05-08 11:14 UTC] mechanical-refactor-tab — STARTED Tab 5 (7 plans: launcher_consolidation + data_status_tests + mtds_databento + mtds_per_instrument + hard_schema + api_football + cme_polymarket); reading plans-of-record before fan-out. Local PM is 6 commits behind origin with foreign dirty files (cefi_master/LEDGER/ONBOARDING/manifest) — NOT mine, leaving alone
[2026-05-08 11:42 UTC] vm-ops-tab — Tab 4 RE-STARTED after Tab 5's pull --rebase silently dropped my uncommitted work + the prior cefi-babysit-tab carryover (sweeps #16-#36). Original boot 11:15 UTC. **Big finding** filed as plans/active/issues/mdps_tradfi_silent_partial_drain_2026_05_08.md (4 mdps-tradfi VMs silent-exited 2026-05-07 14:00 UTC, no STOPPED events, partial-window). Re-applying carryover sweeps + sweep #37/#38/#39 + tradfi_master annotation now, will commit + push surgically (only my files).
