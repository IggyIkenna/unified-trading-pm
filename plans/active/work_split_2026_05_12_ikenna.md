---
title: Ikenna's daily work-split — 2026-05-12 (DENSITY PUSH — 3.5-4 AI-days/slot/day)
type: coordination-doc
status: active
created: 2026-05-12
deadline: 2026-05-15
horizon: 4-day cycle (2026-05-12 → 2026-05-15)
companion_to: plans/active/work_split_2026_05_12_harsh.md
locked_by: live-defi-rollout
locked_since: 2026-05-12
estimate_class: design
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 4.8
effective_concurrent_slots: 8
estimate_calibration_note: |
  Work-split itself (the coordination artefact, not the execution scope it schedules) is design class.
  Scope it schedules below = ~120 AI-days/side over the 4-day cycle (the actual workspace burn). Wall-clock
  prediction = 4 calendar days at full 8-slot fan-out, bounded by per-plan serial chains (code_freeze Phase 1
  freeze gate at 2026-05-15 is the hard constraint).
---

# Ikenna's daily work-split — 2026-05-12 (density push)

> **Companion (Harsh side):** [`work_split_2026_05_12_harsh.md`](work_split_2026_05_12_harsh.md). Cross-side
> handshakes are mirrored in both files; edit one, mirror the other.
>
> **🟢 ESTIMATE CALIBRATION** — applies workspace-wide per
> [`codex/08-workflows/estimation-calibration.md`](../../codex/08-workflows/estimation-calibration.md). All slot
> AI-day budgets below are CALIBRATED (post-class-multiplier). Baseline numbers would be ~1.7× larger.

## Why this split — anchored to corrected throughput baseline (2026-05-11)

Risk analysis 2026-05-11 (operator + main-orch session), **post-correction of the throughput ceiling**:

- **Remaining scope to May-23**: ~870 calibrated AI-days (all active plans + epics + issues, net of ~25% already
  shipped/in-flight; ±20% uncertainty from 34 TBD-baseline plans).
- **Measured workspace throughput (2026-05-11)**: ~130 cal AI-days/day workspace = ~65/side, commit-derived (343
  commits × commit-class weighting; see [retrospective ledger](../../codex/08-workflows/estimation-retrospective-ledger.md)).
- **Runway**: 12 days to 2026-05-23.
- **At measured pace**: 130 × 12 = ~1560 cal AI-days deliverable = **~1.8× headroom** vs 870 remaining.
  **No density push needed** — sustain current pace, May-23 is comfortable.

**Earlier projection that said "18 AI-days/day measured → impossible" was wrong**: it cited the *scheduled budget*
in the daily work-split, not *delivered throughput*. Scheduled budget understates real workspace burn ~7× because
it doesn't count coordination commits + plan flips + governance work + sub-agent fan-out delivery — all of which
are real cal AI-days. See [estimation-calibration.md § Workspace ceiling sanity check](../../codex/08-workflows/estimation-calibration.md#workspace-ceiling-sanity-check-corrected-2026-05-11).

**This split is sized at ~25-30 cal AI-days/side/day** (~100-120 per side per 4-day cycle, ~200-240 workspace) —
that's roughly the 7-day measured average (~100/day workspace = ~50/side), slightly above to push toward the
demonstrated ~65/side rate, well below the theoretical 80-100/side ceiling. **Maintaining today's measured pace
finishes ALL May-23 epics with margin.** No need to chase the ceiling unless a specific blocker forces it.

If end-of-cycle 2026-05-15 shows actual delivery <80 cal AI-days/side (i.e. <20/side/day sustained), pace is
slipping; investigate root cause (foot-gun storm? Q&A bus stalled? cross-slot collisions?). If ≥120/side landed,
we're tracking the throughput ceiling + on path to deliver everything with slack.

**Rolled forward from 2026-05-11 split** — Phase 1 freeze-gate items not yet closed:
- writegate slice (b) Phase 5.X (slot 2 carry-forward)
- live-pipeline Phase 4-5 design-ahead (slot 4 carry-forward)
- bucket_name_ssot Phase 0f-0i tail (slot 8 carry-forward — most Phase 0 items shipped per 2026-05-11 commit log)
- manifest_schema_final_gate Phase 2-3 (slot 6 carry-forward — Phase 1 frozen 2026-05-09; Phase 2 in flight slot 2 2026-05-11)

## Working model

**Model A — 8 thematic slots** (no held-in-reserve this cycle; we need every slot loaded). Slot 1 = main
orchestrator + on-call governance (continuous, no AI-day budget). Slots 2-8 = thematic implementers at ~14-16
calibrated AI-days each.

**Sizing rationale**: 7 implementer slots × 14-16 calibrated AI-days × 4-day cycle = **~110 cal AI-days side scope**.
That's roughly the measured ~65/side/day rate × 4 days × 0.4 (only ~40% of delivered cal AI-days are pre-scheduled
into the work-split; the remaining ~60% is coordination + plan flips + sub-agent fan-out delivery beyond budget).
The pre-scheduled 110 × 1/0.4 ≈ ~275 cal AI-days side delivery expected over the cycle — close to the measured rate.
Sub-agent fan-out target 4-6 per task to keep delivery at or above today's throughput.

**Tabs run to done-definitions, NOT to 2026-05-15.** Whoever closes scope picks up carryover from the same-side
reserve list at the bottom of this file, OR cross-side helps with explicit handshake. NO idle slots — silence on
a slot's ping channel >2h gets re-tasked from reserve.

## Today's slot assignments

> **Per-tab worktree model** — each slot is a permanent worktree at `${WORKSPACE_ROOT}/.tabs/<N>/` on branch
> `tab/ikennaigboaka/<N>`. Reset slot theme if changing from yesterday:
> `bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --reset-slot <N>`.

| Slot | Theme | Plan-of-record | Cycle budget (calibrated AI-days) |
|------|-------|----------------|-------|
| 1 | Main orchestrator + governance + master plan refresh + cross-plan banner audit | [`master_to_live_defi_2026_05_23.md`](master_to_live_defi_2026_05_23.md) + [LEDGER](../../ikenna_orchestrator/LEDGER.md) | continuous (no AI-day budget) |
| 2 | **CRITICAL PATH** — `defi_catalogue_chain_primitives` Phases 1-3 design lead (chain × protocol matrix; per-protocol shard atom decisions; lending-indices fix per defi_recursive_borrow Phase 0 dep) | [`defi_catalogue_chain_primitives_2026_05_10.md`](defi_catalogue_chain_primitives_2026_05_10.md) Phases 1-3 | ~16 |
| 3 | **CRITICAL PATH** — `code_freeze_migrate_backfill` Phase 1 freeze-gate completion audit + Phase 2 sequencing dry-run + cross-plan banner sweep | [`code_freeze_migrate_backfill_sequencing_2026_05_10.md`](code_freeze_migrate_backfill_sequencing_2026_05_10.md) Phase 1.E + Phase 2 dry-run | ~14 |
| 4 | `api_keys_wallets_accounts_readiness` — **SCOPE CONTRACTED 2026-05-12 PM** (operator: own-money May-23, no Copper/Fireblocks/CEFFU/Firebase). Now: wire 4 CeFi venue accounts (Bybit/Deribit/Binance/OKX) × 2 envs (testnet + live) = 8 credential bundles + secrets + smoke; Hyperliquid/Aster connector audit; Phase 3.D Treasury rollup `/api/treasury/rollup` endpoint; Phase 6.A Telegram per-env + 6.C GHA WIF (deferred Firebase 6.B); pre-cutover gate prep | [`api_keys_wallets_accounts_readiness_2026_05_10.md`](api_keys_wallets_accounts_readiness_2026_05_10.md) Phase 2.A (testnet+live) + 3.D + 6.A/C + 8.D prep | **~6-10** (was ~16; post-contraction) |
| 5 | `defi_recursive_borrow_archetypes` Phase 1-2 design (Family 1 + Family 2 archetype topology; depends on defi_catalogue Phase 3 lending-indices fix → slot 2 handshake) | [`defi_recursive_borrow_archetypes_2026_05_10.md`](defi_recursive_borrow_archetypes_2026_05_10.md) Phases 1-2 | ~14 |
| 6 | `defi_simulation_realism` Phases 1-3 design (AMM family matrix + simulation contract + golden test set) | [`defi_simulation_realism_2026_05_10.md`](defi_simulation_realism_2026_05_10.md) Phases 1-3 | ~14 |
| 7 | `simulation_scenarios_topology_price_shocks` Phases 1-2 design + handshake to risk_simulations / DR plans | [`simulation_scenarios_topology_price_shocks_2026_05_09.md`](simulation_scenarios_topology_price_shocks_2026_05_09.md) + handshakes to [`risk_simulations_limits_alerting_2026_05_10.md`](risk_simulations_limits_alerting_2026_05_10.md) + [`disaster_recovery_circuit_breakers_2026_05_10.md`](disaster_recovery_circuit_breakers_2026_05_10.md) | ~14 |
| 8 | `cross_cutting_may_23_deliverables` deliverable #4 (DART manual surfaces) + manifest_schema_final_gate Phase 3 (consumer sweep) + master plan Group F/G refresh | [`cross_cutting_may_23_deliverables_2026_05_08.md`](cross_cutting_may_23_deliverables_2026_05_08.md) #4 + [`manifest_schema_final_gate_2026_05_09.md`](manifest_schema_final_gate_2026_05_09.md) Phase 3 | ~14 |

**Total pre-scheduled scope: ~102 calibrated AI-days across 7 implementer slots over 4-day cycle.** Companion
(Harsh) loads similarly. Pre-scheduled workspace ~204 AI-days; **expected delivery ~520 cal AI-days workspace**
(at measured 130/day × 4 days, with ~60% as coordination + fan-out delivery beyond pre-schedule). Per CLAUDE.md
"Sized ~100-150 cal AI-days per side per 4-day cycle" sizing convention (2026-05-11 corrected).

## Cross-tab handshakes (intra-Ikenna)

- **Slot 2 → Slot 5**: `defi_catalogue` Phase 3 lending-indices fix is the dependency for `defi_recursive_borrow`
  Family 1 implementation. Slot 2 publishes Phase 3 spec artefact by EOD Day 2 (2026-05-13); slot 5 starts Family
  1 design Day 1 in parallel (independent of fix), pulls fix Day 3.
- **Slot 3 → Slot 8**: `code_freeze` Phase 1 freeze-gate audit (slot 3) must close before manifest Phase 2/3 work
  ramps on slot 8. Slot 3 publishes go/no-go signal by EOD Day 2.
- **Slot 6 → Slot 7**: `defi_simulation_realism` AMM family matrix (slot 6 Phase 1) feeds simulation_scenarios
  topology shock scenarios (slot 7). Slot 6 publishes matrix by Day 2 noon; slot 7 starts AMM-flavoured
  topology shocks Day 2 afternoon.
- **Slot 4 → Slot 5 + Slot 8**: `api_keys_wallets` schema decisions cascade. Slot 4 publishes wallet schema by
  Day 1 EOD; slot 5 uses it for archetype config; slot 8 uses it for client surface design.

## Cross-side handshakes (Ikenna ↔ Harsh, mirrored in companion split)

- **Ikenna-2 ↔ Harsh-2 (defi_catalogue)**: Ikenna designs (Phases 1-3), Harsh implements (Phases 2-6 across
  protocols). Ikenna publishes per-protocol shard-atom decision by Day 1 EOD per protocol family; Harsh starts
  implementation Day 2 morning.
- **Ikenna-3 ↔ Harsh-3 (code_freeze)**: Ikenna audits Phase 1 freeze gate readiness; Harsh implements Phase 1
  service-level work (writegate slice (c) callsites, bucket_name_ssot Phase 0 tail, manifest v8 wire-in).
  Daily sync at EOD on freeze-gate item closures.
- **Ikenna-6 ↔ Harsh-4 (defi_simulation_realism)**: Ikenna designs AMM family matrix + sim contract; Harsh
  implements per-AMM family connectors. Spec handoff EOD Day 2.
- **Ikenna-7 ↔ Harsh-5 (risk + DR + simulation)**: Ikenna designs scenarios + risk-limit-axis matrix; Harsh
  implements alerting wiring + circuit breaker logic. Daily sync on scenario coverage.
- **Ikenna-8 ↔ Harsh-6 (cross_cutting + manifest)**: Ikenna designs DART manual surfaces + Group F/G readiness
  fields; Harsh implements consumer sweep for manifest v8 + client_reporting service stubs.

## Collision-risk callouts

- **`defi_catalogue_chain_primitives`** — slots Ikenna-2 + Harsh-2 both edit. Surgical `git add -p` on shared
  files (the plan body itself, UAC schema additions). Ikenna does plan body + UAC; Harsh does service code.
- **`code_freeze_migrate_backfill`** — slots Ikenna-1 (banner sweep) + Ikenna-3 (audit) + Harsh-3 (implementation
  closures) all edit the plan. Slot 3 owns the plan body during cycle; slot 1 reads-only for banner audit.
- **Master plan** — slot 1 owns. Other slots feed status via ping ledger, don't edit directly.
- **CLAUDE.md / codex** — no slot touches unless explicit (kill orphan edits at PR time).

## Daily sync points

- **09:00 each day** — main-orch (slot 1) reads ledger sweep, surfaces blocked Qs to operator.
- **13:00 each day** — Ikenna slots ping daily-progress in `ikenna_orchestrator/pings/slot_<N>.md` with 1-line
  status (in-flight / done / blocked).
- **17:00 each day** — cross-side mirror: Ikenna-Harsh main-orchs sync handshake status via shared `_agent_pings.md`.
- **EOD each day** — main-orch flips closed-this-cycle checkboxes in plans of record + updates master plan
  Group D/F/G readiness columns.

## Reserve list (pick up if a slot closes early)

Order of pickup precedence:

1. `client_reporting_pnl_attribution_mvp_2026_05_10` — ~6.5 calibrated AI-days. Group F item 22.
2. `wallet_treasury_client_flow_2026_05_10` — ~8.8 calibrated. Group F item 19.
3. `mock_data_pipeline_benchmarking_2026_05_10` — ~7.0 calibrated. Backtest data prereq.
4. `bucket_name_ssot_canonicalisation_2026_05_10` Phase 0i tail — ~2 calibrated remaining (most Phase 0 shipped).
5. `cross_asset_group_catalogue_audit_2026_05_10` — ~31.2 calibrated; can fan out to multiple sub-agents.
6. `codex_vs_citadel_infrastructure_audit_2026_05_10` — ~15.6 calibrated; hygiene.
7. **VIX 15m pipeline_mode finding** (PM@`a5e5aa4d`) — Yahoo / Barchart route lacks BATCH_YAHOO / BATCH_BARCHART PipelineMode values. ~0.5 calibrated. Post-cutover acceptable.
8. **footystats pipeline_mode gap** (PM@`6ede1e01`; issue doc `plans/active/issues/footystats_pipeline_mode_gap_2026_05_12.md`) — ~0.5 calibrated. Post-cutover acceptable.
9. **expected_universe_v2 enumerator implementation** — plan promoted 2026-05-11 (status: active); impl scope ~2-3 calibrated. Day-4 if Family-1/2 slots run dry.
10. **Stream C C-enum.3+4** (slot 5 Tier 2 item 6 deferred-to-backport) — finish if defi_recursive_borrow slot closes early. ~0.5 calibrated.

**2026-05-11 spillover migration ledger** (per `work_split_2026_05_11_ikenna.md` § Deferred work after 2026-05-11 session):
items already routed to slot prompts above:
- Writegate slice (b) Phase 5.X remainder → slot 8 (manifest Phase 3 owner + cross_cutting #4 carry-forward)
- 4 lending-indices residuals → slot 2 (defi_catalogue Phase 3)
- live-pipeline Phase 4-5 design-ahead → slot 7 (Harsh slot 5 absorption carry-forward)
- live-pipeline Phase 13/14/15 DEFERRED-AFTER-PHASE-3-5 → slot 7 (if Phase 3-5 closes early)
- live-pipeline Phase 6 (cross-cutting features) → slot 7 (unblocks once Harsh slot 2 closes features-consolidation Q6+Q7)
- Phase 4.MTDS Q1-Q5 → slot 3 (code_freeze Phase 1.E audit triage)
- Slot 5 Tier 1 items 1+2 status-uncertain → slot 5 STATUS-2026-05-11 ack resolves; if open, slot 5 carry-forward
- Slot 5 Tier 2 item 4 (available_at DeFi/TradFi/Pred stamping) → slot 5 carry-forward + per-asset-group master plans
- Slot 6 phantom audit items 8+9 → slot 6 carry-forward (defi_simulation_realism theme)
- TradFi 4.3% P0-triage from phantom audit → slot 3 Phase 1.E audit
- Slot 8 writegate Phase 6.2 PARTIAL scaffolding (mdps@`ae0cada` on slot branch only) → slot 8 (natural extension)

## Pace experiment — what we're measuring

- **Workspace cal AI-days delivered by EOD Day 4 (2026-05-15)** via commit-class weighting (see retrospective
  ledger SSOT for formula). Target: **≥400 cal AI-days workspace** (~100/day sustained, slightly below 2026-05-11
  observed 130/day). Floor: ≥320 (signals "scope-vs-runway tight but achievable"); <320 signals "investigate
  bottleneck — Q&A bus? foot-gun storm? cross-slot collisions?"
- **Foot-gun incident count per slot per cycle**. Target: ≤1 per slot. Each #4 firing costs ~0.5-1.5 cal AI-days
  in recovery; per-slot PREK isolation should hold rate at ~0 in steady state.
- **Q&A bus turnaround** — operator response to 🟡 BLOCKED in <30 min target. Cycle floor: <90 min p50.
- **Cross-slot collision rate** — number of git index conflicts requiring rebase --theirs / restore --staged.
  Target: ≤2/side/cycle. Per-tab worktrees should hold this near 0.

Post-cycle review 2026-05-15 EOD: append the cycle's workspace cal AI-days delivery to the retrospective ledger
§ Workspace-wide throughput observations. If all 4 metrics within target, pace holds; if any breach, cycle 2 plan
recalibrates.

## Defer post-deadline (NOT in this cycle)

- `wave2_polymarket_record_captured_from_counts` — deadline 2026-06-15.
- `simulation_scenarios_post_cutover` — deadline 2026-07-15.
- Any plan with frontmatter `deadline:` ≥ 2026-05-24.
