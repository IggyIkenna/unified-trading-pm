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

## Current shift: 2026-05-13 Wave 2 (Day-4 PM, Harsh-side ONLY)

**Work-split**: [`plans/active/work_split_2026_05_13_harsh.md`](../plans/active/work_split_2026_05_13_harsh.md) § "Wave 2"
**Model**: Sonnet 4.6 / thinking: high (all slots). Wave 1 closed; lunch break; 6 implementor slots for Wave 2.

| Slot | Theme | State | Plan-of-record | Branch |
|------|-------|-------|----------------|--------|
| 1 | Main orchestrator + on-call + LEDGER + ping triage | 🟢 ONLINE | (this LEDGER + work-split) | `tab/hk/1` |
| 2 | risk_simulations finalisation (82% → 100%; P0 items + P1 stablecoin) | 🟡 READY-TO-SPAWN | `risk_simulations_limits_alerting_2026_05_10.md` | `tab/hk/2` |
| 3 | DR Phase 6+9+10 finalisation (AGENT items + SCRIPT prep only; NO VM launch) | 🟡 READY-TO-SPAWN | `disaster_recovery_circuit_breakers_2026_05_10.md` | `tab/hk/3` |
| 4 | 🐛 Script 3 classifier P1 fix (instruments-service ↔ UTL signature) + arbitrage_price_dispersion final 2 items | 🟡 READY-TO-SPAWN | `issues/classify_blank_reason_fixture_manifest_kwarg_2026_05_13.md` + `arbitrage_price_dispersion_finalisation_2026_05_09.md` | `tab/hk/4` |
| 5 | mock_data Phase 3.D per-reader threading (MTDS Tardis/Databento + ml-inference + strategy) | 🟡 READY-TO-SPAWN | `mock_data_pipeline_benchmarking_2026_05_10.md` | `tab/hk/5` |
| 6 | wave3x_residual_ssots finalisation (73% → 100%) | 🟡 READY-TO-SPAWN | `wave3x_residual_ssots_2026_05_08.md` | `tab/hk/6` |
| 7 | cross_asset Phase 5A/5B/5C TradFi ETF + futures-roots consolidation | 🟡 READY-TO-SPAWN | `cross_asset_group_catalogue_audit_2026_05_10.md` Phase 5 | `tab/hk/7` |
| 8 | (reserve — spillover absorption from slots 2-7) | 🟪 RESERVE | — | `tab/hk/8` |
| 9 | (reserve — spillover absorption from slots 2-7) | 🟪 RESERVE | — | `tab/hk/9` |
| 10 | dex_perp Phase 2B/2C + EigenLayer Phase 3 (carry from Wave 1) | 🟢 IN FLIGHT | `dex_perp_and_venue_data_expansion_2026_05_12.md` | `tab/hk/10` |

**Wave 1 closeout** (commits on LDR for the record):
- Slot 2 ✅ DONE (PM@3b317e65) — propagation chain Gate 1 fired
- Slot 3 ✅ DONE (PM@3a16656d) — GCP 3 buckets shipped, AWS deferred Phase 2.6
- Slot 4 ✅ DONE (PM@42755747) — Phase 8A-D rescued via cherry-pick (execution-service@38b3e8a5, foot-gun #5 intercept)
- Slots 5-9 ✅ DONE (PM@3d3d5c14) — batch closure; full per-slot detail in pings/slot_N.md
- Slot 10 🟢 still working

**Critical-path sequencing (slot 1 monitors during Wave 2)**:
1. Slot 4 ships Script 3 classifier fix → unblocks defi/sports/prediction legacy-blank reclassification (deferred apply-flips still pending operator post-cutover)
2. Slot 10 finishes dex_perp Phase 2 + EigenLayer → freeze-gate item 3 fully verified
3. Slots 2/3/5/6/7 fully independent — run in parallel
4. New HARD RULE: LDR-alignment cadence (codified 2026-05-13 PM@f49d5f7d). Slots that boot must rebase ALL owned repos; FF-push per shippable unit, not end-of-session

**Pre-lunch spawn picks** (safest for unattended start): **slot 4** (smallest scope, ~30-90 min) and **slot 2** (well-defined P0 items, FF-pushes steadily). Spawn prompts in work-split § "Spawn prompts (Wave 2)".

**Operator-pending**: None blocking Wave 2. Carry-forward (post-lunch operator decisions): slot 8's A/B/C UAC architecture triage (deferred; lives in cross-side `_agent_pings.md`); Telegram OPS chat_id (operator action); AWS bucket creation (Phase 2.6 window, needs GCE VM with aws CLI).

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
