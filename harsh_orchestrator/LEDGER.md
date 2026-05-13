---
title: Main Agent Ledger — Harsh side
type: orchestration-ledger
status: active
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# Main Agent Ledger (Harsh side)

> Tracks today's slot assignments and live state. Universal mechanics and reading order → [`AGENT_ONBOARDING.md`](AGENT_ONBOARDING.md). Full task briefs → today's work-split. History → `git log`.

---

## Current shift: 2026-05-13 (Day-4, Harsh-side ONLY)

**Work-split**: [`plans/active/work_split_2026_05_13_harsh.md`](../plans/active/work_split_2026_05_13_harsh.md)
**Model**: Sonnet 4.6 / thinking: high (all slots except where noted). Slot 1 + slot 2 → Opus 4.7.

| Slot | Theme | State | Plan-of-record | Branch |
|------|-------|-------|----------------|--------|
| 1 | Main orchestrator + on-call + LEDGER + ping triage | 🟢 ONLINE | (this LEDGER + work-split) | `tab/hk/1` |
| 2 | 🔴 Propagation chain Phase 3.1-3.N + 4 + 2.A (CRITICAL PATH → Gate 1) | ✅ DONE 2026-05-13 — Gate 1 fired (PM@163d0773); slot freed | `expected_unattempted_propagation_chain_2026_05_12.md` | `tab/hk/2` |
| 3 | Bucket SSOT residuals: provision 6 buckets + Q5 features rename + PART B apply-flips (gated on Gate 1) | ✅ DONE 2026-05-13 — GCP 3/3 buckets shipped; AWS 3/3 deferred Phase 2.6; Q5 already done; PART B reassignable | `bucket_name_ssot_canonicalisation_2026_05_10.md` | `tab/hk/3` |
| 4 | defi_simulation_realism Phases 4-6 (Ikenna slot 6 leftover) + Harsh 5B/5C/6B/6C carry-forward | ✅ DONE 2026-05-13 — Phase 8A-D rescued via cherry-pick (execution-service@38b3e8a5, foot-gun #5 intercept); 5B/5C/6B/6C reassignable | `defi_simulation_realism_2026_05_10.md` | `tab/hk/4` |
| 5 | Audit-records PB-1/2/3 (overwrite→append, retention-lock, customer-ID path) | 🟡 SPAWN PENDING | `codex_vs_citadel_infrastructure_audit_2026_05_10.md` (issue docs PB-1/2/3) | `tab/hk/5` |
| 6 | TradFi phantom-audit Databento-aware + 15 dry-runs + apply-flips + Gate 3 GCE phantom audit | 🟡 SPAWN PENDING | `manifest_cross_asset_rescan_design_2026_05_08.md` | `tab/hk/6` |
| 7 | 12 AlertCodes + 4 Breakers PRE-cutover + Telegram channel split + mock_data Phase 3.C/3.D tail | 🟡 SPAWN PENDING | `alerting_service_live_rules_2026_05_07.md` + `disaster_recovery_circuit_breakers_2026_05_10.md` + `mock_data_pipeline_benchmarking_2026_05_10.md` | `tab/hk/7` |
| 8 | 🆕 GMX/DRIFT venue capability refactor — REVERT DEFI_VENUE_AXIS_OVERRIDES (UAC@7c8482e); 3-sub-agent fan-out | 🟡 SPAWN PENDING | `cross_asset_group_catalogue_audit_2026_05_10.md` Phase 1C | `tab/hk/8` |
| 9 | Sports+Prediction reconciler classifier extension + 6 LookaheadBias strict-mode wire-ins + strategy-paper VM verify | 🟡 SPAWN PENDING | UTL `legacy_reason_classifier.py` + freeze-gate item 5 + `promote_workflow_may23_cli_path_2026_05_10.md` | `tab/hk/9` |
| 10 | MDPS 19 test fixes + Phase 4.FEATURES sweep (freeze-gate item 3 → 9/9) + dex_perp Phase 2 + EigenLayer Phase 3 | `dex_perp_and_venue_data_expansion_2026_05_12.md` | `tab/hk/10` | 🟡 SPAWN PENDING |

**Critical-path sequencing (slot 1 monitors)**:
1. Slot 2 Gate 1 fires → immediately ping slot 3 + slot 6 to start PART B / apply-flips
2. Slot 10 closes Phase 4.FEATURES → freeze-gate item 3 hits 9/9
3. Slot 8 UAC revert lands → ping operator; flag downstream strategy-service archetype consumers
4. Slots 4/5/6/7/9 fully independent — run in parallel from boot

**Operator-pending**: None. Q7(b) resolved (deployment-service@acf00a7, buckets provisioned). Slot 3 PART B waits on Gate 1 (slot 2) only.

---

## Spawned tab — boot

You are slot N. Do this in order, nothing else until done:

1. Read [`AGENT_ONBOARDING.md`](AGENT_ONBOARDING.md) — role, git discipline, communication bus, pre-commit check, sub-agent rules.
2. Find your **Slot N row** in the table above → note plan-of-record path + worktree branch.
3. Read today's **work-split § "Slot N"** for full task brief, done-definition, and repos owned.
4. Read your **plan-of-record** — scan open `- [ ]` todos for your phase.
5. Append boot ack to [`pings/slot_N.md`](pings/) using `date -u` for timestamp, then start work.

**COMPACT-CYCLE GUARD**: Do NOT read repo-level `.claude/CLAUDE.md` files from repos you're working in — the workspace CLAUDE.md (auto-loaded in system context) covers all critical cross-cutting rules. Only read a repo's CLAUDE.md if it's explicitly named in your task brief.

---

## Main orchestrator — fresh boot (slot 1)

Fresh main-agent chat (context window died, new session):

1. `git -C /home/hk/unified-trading-system-repos/unified-trading-pm fetch origin --quiet && git -C /home/hk/unified-trading-system-repos/unified-trading-pm log --oneline -5 origin/live-defi-rollout` — see recent origin activity.
2. `cat harsh_orchestrator/pings/slot_{2..10}.md 2>/dev/null` — intra-side pings.
3. `cat plans/active/_agent_pings.md` — cross-side pings.
4. Read this LEDGER § "Current shift" table — note each slot's state; update any SPAWN PENDING → IN FLIGHT based on ping acks.
5. Ack to operator: "Main online. Slots in flight: N. Pings: M intra / K cross. Standing by."
