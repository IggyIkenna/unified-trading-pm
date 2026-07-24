---
doc_type: plan
title: Harsh's daily work-split — 2026-05-12 (DENSITY PUSH — 3.5-4 AI-days/slot/day)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-12
type: coordination-doc
deadline: 2026-05-15
horizon: 4-day cycle (2026-05-12 → 2026-05-15)
companion_to: plans/active/work_split_2026_05_12_ikenna.md
locked_by: live-defi-rollout
locked_since: 2026-05-12
estimate_class: design
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 4.8
effective_concurrent_slots: 8
estimate_calibration_note: "Work-split itself (the coordination artefact, not the execution scope it schedules) is
  design class.

  Scope it schedules below = ~120 AI-days/side over the 4-day cycle (the actual workspace burn). Wall-clock

  prediction = 4 calendar days at full 8-slot fan-out, bounded by per-plan serial chains (code_freeze Phase 1

  freeze gate at 2026-05-15 is the hard constraint).

  "
---

# Harsh's daily work-split — 2026-05-12 (density push)

> **Companion (Ikenna side):** [`work_split_2026_05_12_ikenna.md`](work_split_2026_05_12_ikenna.md). Cross-side
> handshakes are mirrored in both files; edit one, mirror the other.
>
> **🟢 ESTIMATE CALIBRATION** — applies workspace-wide per
> [`/codex/08-workflows/estimation-calibration.md`](/codex/08-workflows/estimation-calibration.md). All slot AI-day
> budgets below are CALIBRATED (post-class-multiplier). Baseline numbers would be ~1.7× larger.

## Why this split — anchored to corrected throughput baseline (2026-05-11)

Risk analysis 2026-05-11 (operator + main-orch session), **post-correction of the throughput ceiling**:

- **Remaining scope to May-23**: ~870 calibrated AI-days (all active plans + epics + issues, net of ~25% already
  shipped/in-flight; ±20% uncertainty from 34 TBD-baseline plans).
- **Measured workspace throughput (2026-05-11)**: ~130 cal AI-days/day workspace = ~65/side, commit-derived (343 commits
  × commit-class weighting; see [retrospective ledger](/codex/08-workflows/estimation-retrospective-ledger.md)).
- **Runway**: 12 days to 2026-05-23.
- **At measured pace**: 130 × 12 = ~1560 cal AI-days deliverable = **~1.8× headroom** vs 870 remaining. **No density
  push needed** — sustain current pace, May-23 is comfortable.

**Earlier projection that said "18 AI-days/day measured → impossible" was wrong**: it cited the _scheduled budget_ in
the daily work-split, not _delivered throughput_. Scheduled budget understates real workspace burn ~7× because it
doesn't count coordination commits + plan flips + governance work + sub-agent fan-out delivery — all of which are real
cal AI-days. See
[estimation-calibration.md § Workspace ceiling sanity check](/codex/08-workflows/estimation-calibration.md#workspace-ceiling-sanity-check-corrected-2026-05-11).

**This split is sized at ~25-30 cal AI-days/side/day pre-scheduled** (~100-120 per side per 4-day cycle) — that's
roughly the 7-day measured average. Harsh-side is implement-from-spec heavy, expects to deliver above pre-schedule when
service-side fan-out closes substantive commits (1.2 cal weight each) vs Ikenna-side coordination weight.

If end-of-cycle 2026-05-15 shows actual delivery <80 cal AI-days/side (i.e. <20/side/day sustained), pace is slipping;
investigate root cause. If ≥120/side landed, we're tracking the throughput ceiling.

Harsh side this cycle: **implement-from-spec + run-script-and-verify + mechanical refactors**. Ikenna companion covers
cross-cutting design, multi-repo governance, master plan + Q&A surfaces. CLAUDE.md split principle applies —
implement-side gets the bulk of LOC + commits; design-side gets the bulk of decisions.

**Rolled forward from 2026-05-11 split** — items not yet closed:

- writegate slice (c) Phase 6 (37-callsite migration; slot 8 carry-forward)
- bucket_name_ssot Phase 0f-0i implementation (72 launchers env-aware; slot 4 carry-forward)
- features-\* consolidation residual (slot 2 carry-forward)
- CeFi phantom audit residual triage (slot 6 carry-forward; did NOT --apply per 2026-05-11)

## Working model

**Model A — 8 thematic slots** (no held-in-reserve this cycle). Slot 1 = main orchestrator + on-call governance
(continuous, no AI-day budget). Slots 2-8 = thematic implementers at ~14-16 calibrated AI-days each.

**Density rationale + tabs-run-to-done-definitions** — see Ikenna companion section. Same protocol applies.

## Today's slot assignments

> **Per-tab worktree model** — each slot is a permanent worktree at `${WORKSPACE_ROOT}/.tabs/<N>/` on branch
> `tab/harsh/<N>`. Reset slot theme if changing from yesterday:
> `bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --reset-slot <N>`.

| Slot | Theme                                                                                                                                                                                                                                               | Plan-of-record                                                                                                                                                                                                                                           | Cycle budget (calibrated AI-days) |
| ---- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------- |
| 1    | Main orchestrator + on-call + harsh-side LEDGER + intra-side ping triage                                                                                                                                                                            | [LEDGER](../../harsh_orchestrator/LEDGER.md)                                                                                                                                                                                                             | continuous (no AI-day budget)     |
| 2    | **CRITICAL PATH** — `defi_catalogue_chain_primitives` Phases 2-4 implementation (per-protocol fan-out across 6-8 protocols this cycle: Aave-V3, Compound-V3, Curve-V2, Uniswap-V3, Pancake-V3, Velodrome, Lyra, GMX-V2) — sub-agent fan-out 5+ deep | [`defi_catalogue_chain_primitives_2026_05_10.md`](defi_catalogue_chain_primitives_2026_05_10.md) Phases 2-4                                                                                                                                              | ~16                               |
| 3    | **CRITICAL PATH** — `code_freeze_migrate_backfill` Phase 1 service-level closures (writegate slice (c) callsite migration tail + bucket_name_ssot Phase 0i tail + manifest v8 wire-in across MTDS/MDPS/features) — sub-agent fan-out 4+             | [`code_freeze_migrate_backfill_sequencing_2026_05_10.md`](code_freeze_migrate_backfill_sequencing_2026_05_10.md) Phase 1 service tail + [`writegate_honest_coverage_endtoend_2026_05_06.md`](writegate_honest_coverage_endtoend_2026_05_06.md) slice (c) | ~16                               |
| 4    | `defi_simulation_realism` Phases 4-6 implementation (per-AMM connector + golden test set landing) — depends on Ikenna-6 family matrix EOD Day 2                                                                                                     | [`defi_simulation_realism_2026_05_10.md`](../archive/defi_simulation_realism_2026_05_10.md) Phases 4-6                                                                                                                                                   | ~14                               |
| 5    | `risk_simulations_limits_alerting` + `disaster_recovery_circuit_breakers` implementation (alerting service wiring + circuit breaker logic + scenario test coverage) — depends on Ikenna-7 scenario specs Day 2                                      | [`risk_simulations_limits_alerting_2026_05_10.md`](../archive/risk_simulations_limits_alerting_2026_05_10.md) + [`disaster_recovery_circuit_breakers_2026_05_10.md`](../archive/disaster_recovery_circuit_breakers_2026_05_10.md)                        | ~14                               |
| 6    | `cross_cutting_may_23_deliverables` deliverable #4 implementation (DART manual surfaces UI + service stubs) + `manifest_schema_final_gate` Phase 3 consumer sweep across 8+ services                                                                | [`cross_cutting_may_23_deliverables_2026_05_08.md`](cross_cutting_may_23_deliverables_2026_05_08.md) #4 + [`manifest_schema_final_gate_2026_05_09.md`](manifest_schema_final_gate_2026_05_09.md) Phase 3                                                 | ~14                               |
| 7    | `mock_data_pipeline_benchmarking` implementation (per-asset_group mock data fixtures + benchmark harness across DeFi + CeFi + TradFi simulation paths)                                                                                              | [`mock_data_pipeline_benchmarking_2026_05_10.md`](mock_data_pipeline_benchmarking_2026_05_10.md)                                                                                                                                                         | ~14                               |
| 8    | `cross_asset_group_catalogue_audit` implementation (per-asset_group catalogue reconciliation; fan-out 5+ sub-agents per asset_group) + `codex_vs_citadel_infrastructure_audit` follow-ups                                                           | [`cross_asset_group_catalogue_audit_2026_05_10.md`](../archive/cross_asset_group_catalogue_audit_2026_05_10.md) + [`codex_vs_citadel_infrastructure_audit_2026_05_10.md`](codex_vs_citadel_infrastructure_audit_2026_05_10.md)                           | ~14                               |

**Total pre-scheduled scope: ~102 calibrated AI-days across 7 implementer slots over 4-day cycle.** Companion (Ikenna)
loads similarly. Pre-scheduled workspace ~204 AI-days; **expected delivery ~520 cal AI-days workspace** (at measured
130/day × 4 days, with ~60% as coordination + fan-out delivery beyond pre-schedule). Per CLAUDE.md "Sized ~100-150 cal
AI-days per side per 4-day cycle" sizing convention (2026-05-11 corrected).

## Cross-tab handshakes (intra-Harsh)

- **Slot 2 → Slot 4**: `defi_catalogue` per-protocol shard atoms (slot 2) feed `defi_simulation_realism` per-AMM
  connector signatures (slot 4). Per-protocol artefact handshake EOD daily.
- **Slot 3 → Slot 6**: `manifest_schema_final_gate` Phase 1 (slot 3 wire-in tail) → Phase 3 (slot 6 consumer sweep).
  Slot 3 publishes "all writers on v8" signal by EOD Day 2; slot 6 fan-out starts Day 2 PM.
- **Slot 3 → Slot 7**: `mock_data_pipeline_benchmarking` (slot 7) needs writegate slice (c) callsite migration (slot 3)
  for honest-coverage fixtures. Daily sync on per-service callsite closure list.
- **Slot 5 → Slot 6**: DR circuit-breaker hooks (slot 5) wire into DART manual surface (slot 6 deliverable #4). Spec
  handoff EOD Day 2.
- **Slot 8 → Slots 2 + 4**: catalogue audit (slot 8) surfaces protocol/AMM gaps; slot 2 + slot 4 fold findings into
  their per-protocol fan-out within 24h.

## Cross-side handshakes (Harsh ↔ Ikenna, mirrored in companion split)

- **Harsh-2 ↔ Ikenna-2 (defi_catalogue)**: see Ikenna companion. Ikenna does Phases 1-3 design + UAC schema; Harsh does
  Phases 2-4 service implementation across 6-8 protocols/AMMs.
- **Harsh-3 ↔ Ikenna-3 (code_freeze)**: Ikenna audits Phase 1 freeze gate; Harsh implements Phase 1 service tail
  closures. Daily sync on freeze-gate item closures EOD.
- **Harsh-4 ↔ Ikenna-6 (defi_simulation_realism)**: Ikenna designs AMM family matrix + sim contract; Harsh implements
  per-AMM connectors. Spec handoff EOD Day 2.
- **Harsh-5 ↔ Ikenna-7 (risk + DR + simulation)**: Ikenna designs scenarios; Harsh implements alerting wiring + circuit
  breakers. Daily sync EOD.
- **Harsh-6 ↔ Ikenna-8 (cross_cutting + manifest)**: Ikenna designs DART surfaces + Group F/G; Harsh implements UI +
  manifest v8 consumer sweep.

## Collision-risk callouts

- **Per-protocol files in defi_catalogue** — Harsh-2 sub-agents each own 1-2 protocols; do NOT cross protocol boundaries
  within sub-agent fan-out (collision = lost work).
- **Manifest writer / reader (UTL)** — Harsh-3 writes; do NOT also write from Harsh-6 consumer sweep. Slot 3 publishes
  signed-off helper signatures EOD Day 2; slot 6 imports + consumes only.
- **Service-level QG scripts** — every slot working on a service edits that service's `scripts/quality-gates.sh` when
  adding ratchets. Atomic edits + named-file stage discipline; foot-gun #1 mitigation applies workspace-wide.

## Daily sync points

- **09:00 each day** — main-orch (slot 1) reads ledger sweep, surfaces blocked Qs to operator.
- **13:00 each day** — Harsh slots ping daily-progress in `harsh_orchestrator/pings/slot_<N>.md` with 1-line status
  (in-flight / done / blocked).
- **17:00 each day** — cross-side mirror: Harsh-Ikenna main-orchs sync handshake status via shared `_agent_pings.md`.
- **EOD each day** — main-orch flips closed-this-cycle checkboxes in plans of record + signals to Ikenna main for master
  plan Group D/F/G readiness column updates.

## Reserve list (pick up if a slot closes early)

Order of pickup precedence:

1. `client_reporting_pnl_attribution_mvp_2026_05_10` — ~6.5 calibrated. Group F item 22.
2. `wallet_treasury_client_flow_2026_05_10` — ~8.8 calibrated. Group F item 19. (Pair w/ Ikenna-4 api_keys.)
3. `defi_recursive_borrow_archetypes` Phase 3+ implementation — ~20 calibrated remaining (Phases 1-2 owned by Ikenna-5
   this cycle). Family 3 implementation starts when Ikenna-5 publishes Family 3 spec.
4. `simulation_scenarios_topology_price_shocks` implementation tail — ~7 calibrated remaining if Ikenna-7 publishes
   scenarios early.
5. `promote_workflow_may23_cli_path_2026_05_10` — ~4.2 calibrated.
6. `available_at_lookahead_bias_completion_2026_05_08` — ~1.5 calibrated.

## Pace experiment — what we're measuring

Same 4 metrics as Ikenna companion:

- **Workspace cal AI-days delivered by EOD Day 4 (2026-05-15)** via commit-class weighting. Target ≥400 workspace
  (~100/day sustained). Floor ≥320.
- **Foot-gun incident count per slot per cycle**. Target: ≤1.
- **Q&A bus turnaround**. Target: p50 <90 min.
- **Cross-slot collision rate**. Target: ≤2/side/cycle.

Post-cycle review 2026-05-15 EOD jointly with Ikenna main. Append delivery to retrospective ledger.

## Defer post-deadline (NOT in this cycle)

- `wave2_polymarket_record_captured_from_counts` — deadline 2026-06-15.
- `simulation_scenarios_post_cutover` — deadline 2026-07-15.
- Any plan with frontmatter `deadline:` ≥ 2026-05-24.

## Spawn prompts (Model B reserve — if mid-cycle absorption needed)

For mid-cycle re-task absorption, spawn pattern:

```
You are slot <N> on Harsh's side, tab/harsh/<N> worktree at .tabs/<N>/. Today's cycle: 2026-05-12 → 2026-05-15
density push (3.5-4 calibrated AI-days/slot/day). Your absorbed scope: <plan-name> Phase <X>.

Read SUB_AGENT_MANDATORY_RULES.md first. Plan-of-record: <plan-path>. Done-definition: <criterion>.
Cross-tab handshake: <slot M> needs your <artefact> by <when>.

Sub-agent fan-out target: 4-6 sub-agents on independent files. Bundle commit + push at every shippable unit
per CLAUDE.md Commit+Push+Flip HARD RULE. Foot-gun #4 mitigation: --no-verify default for docs(plans): flips.
```
