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

[2026-05-08 11:13 UTC] features-consolidation-tab — STARTED Tab 2
(plans/active/features_repo_consolidation_2026_05_08.plan.md + plans/epics/ml_and_features_master_2026_05_07.plan.md
Phase 2A/2B+3); kicking off Phase 0 pre-audit fan-out [2026-05-08 11:14 UTC] instruments-live-tab — STARTED Tab 1
(plans/epics/instruments_live_master_2026_05_08.md + plans/epics/predictions_master_2026_05_07.md Phase 2+3 + archived
instruments_and_market_tick_data_completion_2026_05_01 catalog-aware writer-guard); starting with Predictions Phase 2
adapter lifecycle gating (instruments-service Phase 1 already shipped 98bb167 + b904785) — fanning out 3 sub-agents
(Polymarket adapter, Kalshi adapter, UMI tick provider rename + writer migration) [2026-05-08 ~17:30 UTC]
mechanical-refactor-tab — **DONE Tab 5 cycle (going quiet)**. 7 plans: 5 ✅ shipped (launcher_consolidation_followup
[ds@4a2cd7e+da@14b9ddd], data_status_tests Wave 1+2 [da@6cfed38+da@6ab227b 119 tests pushed; mtds@317d57e 19 tests LOCAL
ONLY awaiting rebase past ac307bb], mtds_per_instrument chain axis [mtds@b674243], api_football flattening
[uac@c76e6d0+is@539130f+pm@36c40a10+pm@1966b572], cme_polymarket Phase 1 [uac@b95d146+pm@2d7fb6bf]); 2 🟡 documented
blocked (mtds_databento P2-gated/Tab-4-ops-territory, hard_schema_enforcement blocked-on-tradfi_master). **Pending
main-agent action**: (a) push mtds@317d57e after rebasing past 1 incoming workflow-CI commit; (b) rebase PM + commit
working-tree plan flips for Plans 1/2/4 (Plans 6/7 already on origin). Wave 2 carryover (15 of 30 Plan 2 todos remain) —
mostly UAC/UTL/deployment-ui contention or Cat E/F gated-on-other-plans; safe Tab 5 contributions exhausted this cycle.
[2026-05-08 11:42 UTC] vm-ops-tab — Tab 4 RE-STARTED after Tab 5's pull --rebase silently dropped my uncommitted work +
the prior cefi-babysit-tab carryover (sweeps #16-#36). Original boot 11:15 UTC. **Big finding** filed as
plans/active/issues/mdps_tradfi_silent_partial_drain_2026_05_08.md (4 mdps-tradfi VMs silent-exited 2026-05-07 14:00
UTC, no STOPPED events, partial-window). Re-applying carryover sweeps + sweep #37/#38/#39 + tradfi_master annotation
now, will commit + push surgically (only my files). [2026-05-08 13:55 UTC] deployment-ui-tab — DONE Tab 3 Phase A
foundation (4 of 5): UAC@ba94d05 (LifecycleClass+CloudTarget+EnvironmentTier+helpers, 8 files/817 inserts/43 tests) +
PM@ebe5cc09 (codex deployment-ui-architecture.md NEW, 318 lines) + PM@eb8a96ca (codex batch-live-symmetry UX section,
+42 lines) + PM@4d6f2731 (plan-flip + Open Q1). A.2 deferred per operator priority. **Open Q1 ⚠️ case-5 BIG**: STEP
5.11+5.12 QG template lists CloudTarget as banned but Phase A.5 makes it UAC SSOT — see plan-of-record Open questions
for routing options. [2026-05-08 19:30 UTC] deployment-ui-tab — **CORRECTION + DONE Tab 3 Phase A foundation (5 of 5
✅)**. Prior 13:55 UTC ping was "4 of 5 + A.2 deferred"; A.2 now ALSO done in this session:
deployment-service/scripts/vm/vm_zombie_watchdog.py (+198/-99 — VmPrefixSpec migration + 4 lifecycle helpers + 96 dict
entries + 9 reserved live/exp prefixes; basedpyright/ruff clean; smoke-imports OK) + cursor-configs/CLAUDE.md "VM Naming
Convention" (+28/-4 — lifecycle_class tagging rule + live/exp patterns) +
codex/05-infrastructure/launcher-script-ssot.md (Post-Plan-Phase Codex Audit pass per HARD RULE — describes new
VmPrefixSpec shape + helper convention) + plan-of-record (A.2 checkbox flipped + Status 5/5 + DONE block extended +
repo_gates deployment-service C0→C2). All A.2 edits UNCOMMITTED — main agent commits centrally per operator direction.
**Open Q1 ⚠️ case-5 BIG still open** (STEP 5.11+5.12 QG amendment for CloudTarget UAC SSOT). **Operator action
carryover**: relaunch watchdog VM after A.2 commits land so running watchdog picks up new VmPrefixSpec shape.
