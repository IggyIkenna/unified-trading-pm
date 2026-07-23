---
doc_type: plan
title: Ikenna's daily work-split — 2026-05-12 (DENSITY PUSH — 3.5-4 AI-days/slot/day)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, features-service, instruments-service, market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-12
type: coordination-doc
deadline: 2026-05-15
horizon: 4-day cycle (2026-05-12 → 2026-05-15)
companion_to: plans/active/work_split_2026_05_12_harsh.md
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

# Ikenna's daily work-split — 2026-05-12 (density push)

> **Companion (Harsh side):** [`work_split_2026_05_12_harsh.md`](work_split_2026_05_12_harsh.md). Cross-side handshakes
> are mirrored in both files; edit one, mirror the other.
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

**This split is sized at ~25-30 cal AI-days/side/day** (~100-120 per side per 4-day cycle, ~200-240 workspace) — that's
roughly the 7-day measured average (~100/day workspace = ~50/side), slightly above to push toward the demonstrated
~65/side rate, well below the theoretical 80-100/side ceiling. **Maintaining today's measured pace finishes ALL May-23
epics with margin.** No need to chase the ceiling unless a specific blocker forces it.

If end-of-cycle 2026-05-15 shows actual delivery <80 cal AI-days/side (i.e. <20/side/day sustained), pace is slipping;
investigate root cause (foot-gun storm? Q&A bus stalled? cross-slot collisions?). If ≥120/side landed, we're tracking
the throughput ceiling + on path to deliver everything with slack.

**Rolled forward from 2026-05-11 split** — Phase 1 freeze-gate items not yet closed:

- writegate slice (b) Phase 5.X (slot 2 carry-forward)
- live-pipeline Phase 4-5 design-ahead (slot 4 carry-forward)
- bucket_name_ssot Phase 0f-0i tail (slot 8 carry-forward — most Phase 0 items shipped per 2026-05-11 commit log)
- manifest_schema_final_gate Phase 2-3 (slot 6 carry-forward — Phase 1 frozen 2026-05-09; Phase 2 in flight slot 2
  2026-05-11)

## Working model

**Model A — 8 thematic slots** (no held-in-reserve this cycle; we need every slot loaded). Slot 1 = main orchestrator +
on-call governance (continuous, no AI-day budget). Slots 2-8 = thematic implementers at ~14-16 calibrated AI-days each.

**Sizing rationale**: 7 implementer slots × 14-16 calibrated AI-days × 4-day cycle = **~110 cal AI-days side scope**.
That's roughly the measured ~65/side/day rate × 4 days × 0.4 (only ~40% of delivered cal AI-days are pre-scheduled into
the work-split; the remaining ~60% is coordination + plan flips + sub-agent fan-out delivery beyond budget). The
pre-scheduled 110 × 1/0.4 ≈ ~275 cal AI-days side delivery expected over the cycle — close to the measured rate.
Sub-agent fan-out target 4-6 per task to keep delivery at or above today's throughput.

**Tabs run to done-definitions, NOT to 2026-05-15.** Whoever closes scope picks up carryover from the same-side reserve
list at the bottom of this file, OR cross-side helps with explicit handshake. NO idle slots — silence on a slot's ping
channel >2h gets re-tasked from reserve.

## Today's slot assignments

> **Per-tab worktree model** — each slot is a permanent worktree at `${WORKSPACE_ROOT}/.tabs/<N>/` on branch
> `tab/ikennaigboaka/<N>`. Reset slot theme if changing from yesterday:
> `bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --reset-slot <N>`.

| Slot | Theme                                                                                                                                                                                                                                                                                                                                                                                                                                                               | Plan-of-record                                                                                                                                                                                                                                                                                                                                                           | Cycle budget (calibrated AI-days)     |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------- |
| 1    | Main orchestrator + governance + master plan refresh + cross-plan banner audit                                                                                                                                                                                                                                                                                                                                                                                      | [`master_to_live_defi_2026_05_23.md`](master_to_live_defi_2026_05_23.md) + [LEDGER](../../ikenna_orchestrator/LEDGER.md)                                                                                                                                                                                                                                                 | continuous (no AI-day budget)         |
| 2    | **CRITICAL PATH** — `defi_catalogue_chain_primitives` Phases 1-3 design lead (chain × protocol matrix; per-protocol shard atom decisions; lending-indices fix per defi_recursive_borrow Phase 0 dep)                                                                                                                                                                                                                                                                | [`defi_catalogue_chain_primitives_2026_05_10.md`](defi_catalogue_chain_primitives_2026_05_10.md) Phases 1-3                                                                                                                                                                                                                                                              | ~16                                   |
| 3    | **CRITICAL PATH** — `code_freeze_migrate_backfill` Phase 1 freeze-gate completion audit + Phase 2 sequencing dry-run + cross-plan banner sweep                                                                                                                                                                                                                                                                                                                      | [`code_freeze_migrate_backfill_sequencing_2026_05_10.md`](code_freeze_migrate_backfill_sequencing_2026_05_10.md) Phase 1.E + Phase 2 dry-run                                                                                                                                                                                                                             | ~14                                   |
| 4    | `api_keys_wallets_accounts_readiness` — **SCOPE CONTRACTED 2026-05-12 PM** (operator: own-money May-23, no Copper/Fireblocks/CEFFU/Firebase). Now: wire 4 CeFi venue accounts (Bybit/Deribit/Binance/OKX) × 2 envs (testnet + live) = 8 credential bundles + secrets + smoke; Hyperliquid/Aster connector audit; Phase 3.D Treasury rollup `/api/treasury/rollup` endpoint; Phase 6.A Telegram per-env + 6.C GHA WIF (deferred Firebase 6.B); pre-cutover gate prep | [`api_keys_wallets_accounts_readiness_2026_05_10.md`](api_keys_wallets_accounts_readiness_2026_05_10.md) Phase 2.A (testnet+live) + 3.D + 6.A/C + 8.D prep                                                                                                                                                                                                               | **~6-10** (was ~16; post-contraction) |
| 5    | `defi_recursive_borrow_archetypes` Phase 1-2 design (Family 1 + Family 2 archetype topology; depends on defi_catalogue Phase 3 lending-indices fix → slot 2 handshake)                                                                                                                                                                                                                                                                                              | [`defi_recursive_borrow_archetypes_2026_05_10.md`](defi_recursive_borrow_archetypes_2026_05_10.md) Phases 1-2                                                                                                                                                                                                                                                            | ~14                                   |
| 6    | `defi_simulation_realism` Phases 1-3 design (AMM family matrix + simulation contract + golden test set)                                                                                                                                                                                                                                                                                                                                                             | [`defi_simulation_realism_2026_05_10.md`](../archive/defi_simulation_realism_2026_05_10.md) Phases 1-3                                                                                                                                                                                                                                                                   | ~14                                   |
| 7    | `simulation_scenarios_topology_price_shocks` Phases 1-2 design + handshake to risk_simulations / DR plans                                                                                                                                                                                                                                                                                                                                                           | [`simulation_scenarios_topology_price_shocks_2026_05_09.md`](simulation_scenarios_topology_price_shocks_2026_05_09.md) + handshakes to [`risk_simulations_limits_alerting_2026_05_10.md`](../archive/risk_simulations_limits_alerting_2026_05_10.md) + [`disaster_recovery_circuit_breakers_2026_05_10.md`](../archive/disaster_recovery_circuit_breakers_2026_05_10.md) | ~14                                   |
| 8    | `cross_cutting_may_23_deliverables` deliverable #4 (DART manual surfaces) + manifest_schema_final_gate Phase 3 (consumer sweep) + master plan Group F/G refresh                                                                                                                                                                                                                                                                                                     | [`cross_cutting_may_23_deliverables_2026_05_08.md`](cross_cutting_may_23_deliverables_2026_05_08.md) #4 + [`manifest_schema_final_gate_2026_05_09.md`](manifest_schema_final_gate_2026_05_09.md) Phase 3                                                                                                                                                                 | ~14                                   |

**Total pre-scheduled scope: ~102 calibrated AI-days across 7 implementer slots over 4-day cycle.** Companion (Harsh)
loads similarly. Pre-scheduled workspace ~204 AI-days; **expected delivery ~520 cal AI-days workspace** (at measured
130/day × 4 days, with ~60% as coordination + fan-out delivery beyond pre-schedule). Per CLAUDE.md "Sized ~100-150 cal
AI-days per side per 4-day cycle" sizing convention (2026-05-11 corrected).

## Cross-tab handshakes (intra-Ikenna)

- **Slot 2 → Slot 5**: `defi_catalogue` Phase 3 lending-indices fix is the dependency for `defi_recursive_borrow` Family
  1 implementation. Slot 2 publishes Phase 3 spec artefact by EOD Day 2 (2026-05-13); slot 5 starts Family 1 design Day
  1 in parallel (independent of fix), pulls fix Day 3.
- **Slot 3 → Slot 8**: `code_freeze` Phase 1 freeze-gate audit (slot 3) must close before manifest Phase 2/3 work ramps
  on slot 8. Slot 3 publishes go/no-go signal by EOD Day 2.
- **Slot 6 → Slot 7**: `defi_simulation_realism` AMM family matrix (slot 6 Phase 1) feeds simulation_scenarios topology
  shock scenarios (slot 7). Slot 6 publishes matrix by Day 2 noon; slot 7 starts AMM-flavoured topology shocks Day 2
  afternoon.
- **Slot 4 → Slot 5 + Slot 8**: `api_keys_wallets` schema decisions cascade. Slot 4 publishes wallet schema by Day 1
  EOD; slot 5 uses it for archetype config; slot 8 uses it for client surface design.

## Cross-side handshakes (Ikenna ↔ Harsh, mirrored in companion split)

- **Ikenna-2 ↔ Harsh-2 (defi_catalogue)**: Ikenna designs (Phases 1-3), Harsh implements (Phases 2-6 across protocols).
  Ikenna publishes per-protocol shard-atom decision by Day 1 EOD per protocol family; Harsh starts implementation Day 2
  morning.
- **Ikenna-3 ↔ Harsh-3 (code_freeze)**: Ikenna audits Phase 1 freeze gate readiness; Harsh implements Phase 1
  service-level work (writegate slice (c) callsites, bucket_name_ssot Phase 0 tail, manifest v8 wire-in). Daily sync at
  EOD on freeze-gate item closures.
- **Ikenna-6 ↔ Harsh-4 (defi_simulation_realism)**: Ikenna designs AMM family matrix + sim contract; Harsh implements
  per-AMM family connectors. Spec handoff EOD Day 2.
- **Ikenna-7 ↔ Harsh-5 (risk + DR + simulation)**: Ikenna designs scenarios + risk-limit-axis matrix; Harsh implements
  alerting wiring + circuit breaker logic. Daily sync on scenario coverage.
- **Ikenna-8 ↔ Harsh-6 (cross_cutting + manifest)**: Ikenna designs DART manual surfaces + Group F/G readiness fields;
  Harsh implements consumer sweep for manifest v8 + client_reporting service stubs.

## Collision-risk callouts

- **`defi_catalogue_chain_primitives`** — slots Ikenna-2 + Harsh-2 both edit. Surgical `git add -p` on shared files (the
  plan body itself, UAC schema additions). Ikenna does plan body + UAC; Harsh does service code.
- **`code_freeze_migrate_backfill`** — slots Ikenna-1 (banner sweep) + Ikenna-3 (audit) + Harsh-3 (implementation
  closures) all edit the plan. Slot 3 owns the plan body during cycle; slot 1 reads-only for banner audit.
- **Master plan** — slot 1 owns. Other slots feed status via ping ledger, don't edit directly.
- **CLAUDE.md / codex** — no slot touches unless explicit (kill orphan edits at PR time).

## Daily sync points

- **09:00 each day** — main-orch (slot 1) reads ledger sweep, surfaces blocked Qs to operator.
- **13:00 each day** — Ikenna slots ping daily-progress in `ikenna_orchestrator/pings/slot_<N>.md` with 1-line status
  (in-flight / done / blocked).
- **17:00 each day** — cross-side mirror: Ikenna-Harsh main-orchs sync handshake status via shared `_agent_pings.md`.
- **EOD each day** — main-orch flips closed-this-cycle checkboxes in plans of record + updates master plan Group D/F/G
  readiness columns.

## Reserve list (pick up if a slot closes early)

Order of pickup precedence:

1. `client_reporting_pnl_attribution_mvp_2026_05_10` — ~6.5 calibrated AI-days. Group F item 22.
2. `wallet_treasury_client_flow_2026_05_10` — ~8.8 calibrated. Group F item 19.
3. `mock_data_pipeline_benchmarking_2026_05_10` — ~7.0 calibrated. Backtest data prereq.
4. `bucket_name_ssot_canonicalisation_2026_05_10` Phase 0i tail — ~2 calibrated remaining (most Phase 0 shipped).
5. `cross_asset_group_catalogue_audit_2026_05_10` — ~31.2 calibrated; can fan out to multiple sub-agents.
6. `codex_vs_citadel_infrastructure_audit_2026_05_10` — ~15.6 calibrated; hygiene.
7. **VIX 15m pipeline_mode finding** (PM@`a5e5aa4d`) — Yahoo / Barchart route lacks BATCH_YAHOO / BATCH_BARCHART
   PipelineMode values. ~0.5 calibrated. Post-cutover acceptable.
8. **footystats pipeline_mode gap** (PM@`6ede1e01`; issue doc
   `plans/archive/issues/footystats_pipeline_mode_gap_2026_05_12.md`) — ~0.5 calibrated. Post-cutover acceptable.
9. **expected_universe_v2 enumerator implementation** — plan promoted 2026-05-11 (status: active); impl scope ~2-3
   calibrated. Day-4 if Family-1/2 slots run dry.
10. **Stream C C-enum.3+4** (slot 5 Tier 2 item 6 deferred-to-backport) — finish if defi_recursive_borrow slot closes
    early. ~0.5 calibrated.

**2026-05-11 spillover migration ledger** (per `work_split_2026_05_11_ikenna.md` § Deferred work after 2026-05-11
session): items already routed to slot prompts above:

- Writegate slice (b) Phase 5.X remainder → slot 8 (manifest Phase 3 owner + cross_cutting #4 carry-forward)
- 4 lending-indices residuals → slot 2 (defi_catalogue Phase 3)
- live-pipeline Phase 4-5 design-ahead → slot 7 (Harsh slot 5 absorption carry-forward)
- live-pipeline Phase 13/14/15 DEFERRED-AFTER-PHASE-3-5 → slot 7 (if Phase 3-5 closes early)
- live-pipeline Phase 6 (cross-cutting features) → slot 7 (unblocks once Harsh slot 2 closes features-consolidation
  Q6+Q7)
- Phase 4.MTDS Q1-Q5 → slot 3 (code_freeze Phase 1.E audit triage)
- Slot 5 Tier 1 items 1+2 status-uncertain → slot 5 STATUS-2026-05-11 ack resolves; if open, slot 5 carry-forward
- Slot 5 Tier 2 item 4 (available_at DeFi/TradFi/Pred stamping) → slot 5 carry-forward + per-asset-group master plans
- Slot 6 phantom audit items 8+9 → slot 6 carry-forward (defi_simulation_realism theme)
- TradFi 4.3% P0-triage from phantom audit → slot 3 Phase 1.E audit
- Slot 8 writegate Phase 6.2 PARTIAL scaffolding (mdps@`ae0cada` on slot branch only) → slot 8 (natural extension)

## Pace experiment — what we're measuring

- **Workspace cal AI-days delivered by EOD Day 4 (2026-05-15)** via commit-class weighting (see retrospective ledger
  SSOT for formula). Target: **≥400 cal AI-days workspace** (~100/day sustained, slightly below 2026-05-11 observed
  130/day). Floor: ≥320 (signals "scope-vs-runway tight but achievable"); <320 signals "investigate bottleneck — Q&A
  bus? foot-gun storm? cross-slot collisions?"
- **Foot-gun incident count per slot per cycle**. Target: ≤1 per slot. Each #4 firing costs ~0.5-1.5 cal AI-days in
  recovery; per-slot PREK isolation should hold rate at ~0 in steady state.
- **Q&A bus turnaround** — operator response to 🟡 BLOCKED in <30 min target. Cycle floor: <90 min p50.
- **Cross-slot collision rate** — number of git index conflicts requiring rebase --theirs / restore --staged. Target:
  ≤2/side/cycle. Per-tab worktrees should hold this near 0.

Post-cycle review 2026-05-15 EOD: append the cycle's workspace cal AI-days delivery to the retrospective ledger §
Workspace-wide throughput observations. If all 4 metrics within target, pace holds; if any breach, cycle 2 plan
recalibrates.

## Addendum — manifest + writegate + propagation + migration + backfill (COMPREHENSIVE, 2026-05-12 PM)

**Operator direction 2026-05-12 PM**: all manifest cleanup + `expected_unattempted` propagation + bucket SSOT migration

- writegate coding + emission policy rollout spread across ALL Ikenna slots. Execution order locked: **1. Coding → 2.
  Reconciliation dry-runs → 3. Apply-flips → 4. Env-split migration (production first) → 5. Backfills**.

---

### Master dependency DAG

```
══════════════════ IMMEDIATE PARALLEL (no inter-dependencies) ═══════════════════════════
  Slot 3-A:  GCE VM dry-run baseline — all 5 AGs × 3 scripts [starts now]
  Slot 3-B:  GCS production bucket provisioning (Storage Transfer Service) [starts now]
  Slot 4:    Propagation chain Phase 0A (UAC) → 0B (UTL) → then 1→2→3-fanout→4
  Slot 4:    Script-1 SOURCE_RETURNED_ZERO root-cause + fix [starts now, no blocker]
  Slot 5:    Phase 2.D match_end_time SFI freeze-detect [starts now]
  Slot 6:    Phase 2.B MTDS cluster Option α [starts now]
  Slot 6:    Emission Phase 6.3 features-volatility BUILD FROM SCRATCH [starts now]
  Slot 7:    Emission Phase 6.4 features-cross STRICT_FAIL [starts now]
  Slot 8:    Phase 6.8 instruments-service 41 .add()→record_captured() [starts now]

═══════════════════ GATE 0A: UAC Phase 0A + UTL Phase 0B pushed ═════════════════════════
  Slot 4:    Phase 1 MTDS pre-flight → Phase 2 MDPS DependencyChecker
             Phase 3 features 6-module fan-out (PARALLEL) + Phase 2.A MDPS 4-state (PARALLEL)
             Phase 4 ML

═══════════════════ GATE 1: Phases 1–4 + 2.A all pushed to origin ═══════════════════════
  Slot 3:    Apply-flips in dependency order:
               Pass 1: instruments data_types, all 5 AGs
               Pass 2: MTDS data_types, all 5 AGs
               Pass 3: MDPS data_types
               Pass 4: features + ML data_types

═══════════════════ GATE 2: bucket physical migration (prod) done + parity ══════════════
  Slot 8:    Code migration — resolve_bucket_name() all scripts + VM launchers

═══════════════════ GATE 3: phantom = 0 + manifest accurate ══════════════════════════════
  ALL slots: BACKFILLS CLEARED — instruments-service → MTDS → MDPS → features order
```

**Phase 2.B does NOT block Phase 2.A or 2.C** — different repos (MTDS vs MDPS/features). Run in parallel. **Phase 2.D
(match_end_time) does NOT block any reconciler** — instruments-service field addition only.

---

### Slot assignments (manifest/writegate work, all 8 slots)

| Slot  | Work                                                                                                                                              | Gates                                      | Cal AI-days |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------ | ----------- |
| **1** | Gate status tracking + blocker triage + ping triage + master plan refresh                                                                         | continuous                                 | —           |
| **3** | ① Dry-run baseline GCE VM (5 AGs) [NOW] ② Bucket provisioning prod (STS) [NOW] ③ Apply-flips Passes 1-4 [GATE 1] ④ Bucket code migration [GATE 2] | starts NOW; ③ waits GATE 1; ④ waits GATE 2 | ~7          |
| **4** | Script-1 root-cause + Phase 0A→0B→1→1.5→2→3-fanout→4 + Phase 2.A MDPS 4-state+v6                                                                  | GATE 0A serial unlock                      | ~9          |
| **5** | Phase 2.D match_end_time SFI [NOW] + Phase 2.C features-sports stubs [after defi_recursive phases]                                                | independent                                | ~3          |
| **6** | Phase 2.B MTDS cluster Option α [NOW] + Emission 6.3 features-vol BUILD FROM SCRATCH [NOW]                                                        | independent                                | ~7          |
| **7** | Emission 6.4 features-cross STRICT_FAIL [NOW] + Emission 6.5 features-\* wiring [NOW]                                                             | independent                                | ~4          |
| **8** | Phase 6.8 instruments-service 41 callsites [NOW] + Phase 6.9 QG sweep [after 6.3-6.8] + bucket code migration [GATE 2]                            | 6.9 waits 6.3-6.8; migration waits GATE 2  | ~8          |

**Total additional cal AI-days across all slots: ~38** (covers all open writegate coding + propagation chain +
reconcilers + bucket migration).

---

### Spawn prompts

**Slot 3 — Dry-run baseline + bucket provisioning + apply-flips**:

```
MODEL TIER: Sonnet 4.6 / THINKING: high
WORKSPACE_ROOT: /Users/ikennaigboaka/Code/unified-trading-system-repos

PART A — NOW: GCS production bucket provisioning per bucket_name_ssot_canonicalisation_2026_05_10.md.
  Production buckets only — staging/dev deferred (we need production data for DeFi cutover).
  Use Storage Transfer Service to copy flat→env-tiered. Verify object-count parity before any code switch.
  Record parity counts in bucket_name_ssot plan. When done: ping Slot 1 → GATE 2 condition met.

PART B — AFTER GATE 1 (propagation chain Phases 1–4 + 2.A pushed to origin):
  ⚠️ DO NOT run reconcile_expected_absence_reasons --apply-flips or reconcile_legacy_blank_to_typed_reason --apply-flips
  BEFORE Gate 1. Reason: MTDS currently writes attempted_failed for instruments instruments-service says don't exist
  (the propagation gap — see expected_unattempted_propagation_gap_2026_05_12.md). Classifiers would assign typed
  reasons to rows that should become expected_unattempted — corruption, not cleanup.
  First: run INFORMATIONAL dry-run (--dry-run, no writes) to record current phantom baseline counts.
  Then Phase 1-4 + 2.A ship (Gate 1 fires). Then run the actionable dry-run + apply-flips below.
  Apply-flips in strict dependency order:
  Pass 1: instruments,venue_trading_calendar all 5 AGs (--apply-flips)
  Pass 2: MTDS data_types all 5 AGs
  Pass 3: MDPS data_types
  Pass 4: features + ML data_types
  Also run: reconcile_expected_absence_reasons.py --apply-flips all 5 AGs
  Also run: reconcile_legacy_blank_to_typed_reason.py --apply-flips all 5 AGs
  Verify phantom count = 0 (or <10 class-C). Record. Ping Slot 1 → GATE 3 condition.

PART C — AFTER GATE 2: Code migration — replace hardcoded gs:// f-strings with resolve_bucket_name().
  Scope: instruments-service scripts + deployment-service VM launchers (~60 files).
  QG STEP 5.69 ratchet must return zero violations. Push.
```

**Slot 4 — Propagation chain Phases 0–4 + MDPS 4-state contract + Script-1 root-cause**:

```
MODEL TIER: Sonnet 4.6 / THINKING: high
PLAN: unified-trading-pm/plans/active/expected_unattempted_propagation_chain_2026_05_12.md
WORKSPACE_ROOT: /Users/ikennaigboaka/Code/unified-trading-system-repos

PART A — NOW: Root-cause Script-1 zero-upgrade for defi + sports:
  Read instruments-service/scripts/reconcile_legacy_blank_to_typed_reason.py lines 410-470.
  Check: capture_status = 'empty_confirmed' eligible vs 'attempted_failed' excluded.
  Check: cefi instrument-day grain special handling at line 445.
  Fix filter if wrong. Run --apply-flips for affected asset_groups.

PART B — SEQUENTIAL foundation, then fan-out:
  Phase 0A: Add EXPECTED_OUTSIDE_PROCESSING_SCOPE + EXPECTED_UPSTREAM_EMPTY to UAC EmptyConfirmedReason
            + EMPTY_CONFIRMED_REASONS dict. QG + push. (GATE 0A prerequisite — ship this first)
  Phase 0B: Verify ManifestReader bucket param OR add read_upstream_manifest() helper in UTL.
            3 mock-GCS unit tests. QG + push. (GATE 0A complete after 0A+0B both pushed)
  Phase 1:  MTDS batch orchestrator — read instruments-service manifest pre-flight.
            5 asset_groups. Verify instruments bucket names in cloud-providers.yaml.
            3 unit tests. QG + push.
  Phase 1.5:Sports classifier fixture-existence fix (legacy_reason_classifier.py).
            Add fixture_manifest param to _classify_sports(). 3 unit tests. QG + push.
  Phase 2:  MDPS DependencyChecker.record_expected_unattempted on skip.
            Wire 4-state consumption contract:
              empty_confirmed → forward-fill zero-volume bars (price continuity preserved)
              attempted_failed → NaN (do NOT forward-fill — data may exist but fetch failed)
              expected_unattempted → propagate skip
            4 unit tests. QG + push.
  Phase 3:  Spawn 6 sub-agents SIMULTANEOUSLY (delta_one, calendar, onchain, volatility, sports, commodity).
            Each wires EXPECTED_OUTSIDE_PROCESSING_SCOPE for non-MVP instruments in batch handler.
            Add UAC FEATURES_MVP_INSTRUMENTS frozenset first (Phase 3.0 pre-step).
            QG per module + push.
  Phase 4:  ml-training + ml-inference expected_unattempted (ML_SCOPE_INSTRUMENTS constant in UAC).
            QG per repo + push.

PART C — PARALLEL with Phase 3 fan-out (same MDPS repo as Phase 2):
  Writegate Phase 2.A — MDPS 4-state output routing:
    Delete _create_empty_output from canonical_writer.
    Wire 4-state routing (empty_confirmed→forward-fill, attempted_failed→NaN, expected_unattempted→propagate).
    Add v6 column wiring: quote_asset + margin_type into canonical_writer.add().
    Per-adapter integration tests. QG green + push.
  When Phases 1–4 + 2.A all pushed: ping Slot 1 → GATE 1 fired.
```

**Slot 4 session close status (2026-05-12):**

- PART A (Script-1 root-cause) ✅ DONE — prior session
- Phase 0A (UAC EmptyConfirmedReason) ✅ DONE — `uac@0457b0e`
- Phase 0B (UTL helper) ✅ DONE — pre-existed; no new helper needed
- Gate 0A ✅ FIRED
- Phase 1 (MTDS pre-flight) ✅ DONE — wired, QG green
- Phase 1.5 (sports classifier) ✅ DONE — `pm@ff2b46fb`
- Phase 2 (MDPS dep-skip record_expected_unattempted) ✅ DONE — `mdps@3f70cf6`; 4 unit tests pass
- Phase 3.0 design direction ✅ RESOLVED — **Option A confirmed** by operator 2026-05-12. subscription_list is runtime
  (DomainConfigReloader). No UAC frozenset. Runtime comparison at `_get_instruments()`.
- Phase 3.1–3.N 🟡 TODO — spawn 6 feature sub-agents (delta_one, calendar, onchain, volatility, sports, commodity)
- Phase 4 (ML services) 🟡 TODO — after Phase 3
- PART C (writegate 2.A MDPS 4-state routing) 🟡 TODO
- 19 pre-existing MDPS test failures 🟡 FLAGGED (EmissionDecision schema drift, sports config, env validation) — not
  this slot's work; logged to ping
- Gate 1: 🔴 OPEN — need Phases 3, 4, and 2.A first

**Slot 5 — Phase 2.D match_end_time + Phase 2.C features-sports**:

```
MODEL TIER: Sonnet 4.6 / THINKING: medium
WORKSPACE_ROOT: /Users/ikennaigboaka/Code/unified-trading-system-repos

PART A — NOW: Phase 2.D ALL fields (full scope — all ship now):
  Decision (locked 2026-05-12): full Phase 2.D ships. All fields are retroactively available.
  Pre-audit:
    # CRITICAL FIRST: does instruments-service poll for FUTURE (upcoming) fixtures from API Football?
    grep -rn "future\|upcoming\|scheduled\|date_from\|date_gte\|next.*fixture\|fixture.*future" \
      instruments-service/instruments_service/ --include="*.py" | grep -v .venv | head -20
    # If NO future-fixture poll exists: add it. We need upcoming fixtures so:
    #   (a) downstream can calibrate API_FOOTBALL_RESULT_LAG_P95_SECONDS as fixtures complete live
    #   (b) MTDS/features know what to attempt + when for each fixture
    #   (c) announced_at is captured at fixture creation, not just at backfill time
    # Future-fixtures poll: query API Football /fixtures?status=NS&next=50 (or date_from=today)
    # Write each fixture to instruments manifest as expected_unattempted until SFI confirms it started.
    grep -rn "match_end_time\|announced_at\|report_time\|freeze_detect\|progressive_stats\|POSTPONED\|CANCELLED" \
      instruments-service/ --include="*.py" | grep -v .venv | head -30
    grep -n "announced_at\|created_at\|fixture.*date\|timestamp" \
      instruments-service/instruments_service/adapters/api_football*.py | head -20
  Steps:
    1. UAC instruments schema: add match_end_time: datetime | None + announced_at: datetime | None + report_time: datetime | None
    2. UAC constants: SFI_DATA_LAG_P95_SECONDS (measure once: sample 1000 fixtures, compute
       (SFI-progressive-stats-freeze-timestamp − scheduled_kickoff − nominal_duration).quantile(0.95). Start with 300s as prior).
    3. SFI adapter: freeze-detection → match_end_time field (30 progressive stats stop → match end)
    4. API Football adapter: read announced_at from fixture object (fixture.created / fixture.timestamp field — check API Football response shape first)
    5. Derive: report_time = match_end_time + timedelta(seconds=SFI_DATA_LAG_P95_SECONDS) where match_end_time is known
    6. UAC: add EXPECTED_FIXTURE_POSTPONED + EXPECTED_FIXTURE_CANCELLED to EmptyConfirmedReason
    7. instruments-service: for fixtures with status POSTPONED or CANCELLED → record_empty(reason=EXPECTED_FIXTURE_POSTPONED/CANCELLED)
       BOTH historical AND live: instruments-service forward-polls API Football for fixture status updates.
       On POSTPONED/CANCELLED: overwrite manifest with record_empty (manifest history records the overwrite —
       downstream can query status history). No state-machine needed — just overwrite + the manifest audit trail
       shows the transition. Wire in the existing API Football polling loop, not a new path.
    8. assert_available_at_present wiring
    9. UAC: source latency constants for ALL sports sources (calibrate once from historical data):
         SFI_DATA_LAG_P95_SECONDS — already above
         UNDERSTAT_DATA_LAG_P95_SECONDS — sample 500 fixtures: (understat data timestamp − match_end_time).quantile(0.95). Prior: 7200s (2hr)
         FOOTYSTATS_DATA_LAG_P95_SECONDS — same method. Prior: 3600s (1hr)
         API_FOOTBALL_RESULT_LAG_P95_SECONDS — time from FT whistle to API Football showing final score. Prior: 1800s (30min)
         OPEN_METEO_HISTORICAL_LAG_SECONDS — weather actuals lag; minimal (~1hr). Prior: 3600s. Pre-match forecasts: available_at = scrape_time (no lookahead)
       These feed into available_at stamping for features — report_time = match_end_time + SOURCE_LAG_P95_SECONDS per source.
       Pre-match sources (API Football fixtures, Open-Meteo forecasts): available_at = scrape_time, not match_end_time.
       Add all constants to UAC unified_api_contracts/registry/source_data_latency.py (new file).
    5 unit tests (freeze detected, no freeze yet, announced_at from API Football, postponed, cancelled). QG + push.

PART B — AFTER defi_recursive Phase 2 design: Phase 2.C features-sports stubs:
  Fix fixture_lineups + fixture_player_stats stubs (data read at _fetch_runner.py:171/173 but discarded).
  4-step fix per stub:
    1. Read from _fetch_runner output instead of discarding
    2. Stamp available_at per row
    3. Write to GCS via canonical_writer
    4. record_captured() with assert_available_at_present
  Delete _ensure_timestamp (5 callsites).
  Wire per-table available_at for 14 TABLE_TO_EXPORT entries.
  Per-table unit tests + integration test. QG + push.
```

**Slot 6 — Phase 2.B MTDS cluster Option α + Emission Phase 6.3 features-volatility**:

```
MODEL TIER: Sonnet 4.6 / THINKING: high
WORKSPACE_ROOT: /Users/ikennaigboaka/Code/unified-trading-system-repos

PART A — NOW: Phase 2.B MTDS cluster wiring Option α (decision locked 2026-05-12):
  Generalise the manual ES.OPT cluster check at engine/orchestrator.py:2186-2218 to cover ALL BUNDLED_DATA_TYPES.
  Pre-audit:
    grep -n "BUNDLED_DATA_TYPES\|root_cluster\|cluster_extractor\|expected_root_clusters\|ES\.OPT\|options_chain" \
      market-tick-data-service/ --include="*.py" | grep -v .venv | head -40
  Steps:
    1. UAC: add DatabentoClassification.root_cluster field to classification schema
    2. UAC: add futures_expiry_bucket() helper (TradFi futures chain cluster grouping)
    3. MTDS engine/orchestrator.py: generalise ES.OPT check → BUNDLED_DATA_TYPES dispatch
    4. Wire record_captured(expected_root_clusters=, cluster_extractor=) for all bundled adapters
    5. Unit tests per bundled data_type (options_chain, futures_chain, sports per-fixture bundles). QG + push.

PART B — NOW PARALLEL: Emission Phase 6.3 features-volatility BUILD FROM SCRATCH:
  No prior template — this is the first features-service service to get publish_with_policy.
  Pre-audit:
    grep -rn "record_captured\|manifest_writer\|canonical_writer" \
      features-service/features_service/volatility/ --include="*.py" | grep -v .venv | head -20
  Steps:
    1. Add features-volatility entry to UAC SERVICE_EMISSION_POLICY_SEED_DICT
    2. Wire _resolve_policy_output_data_type in volatility batch handler
    3. Wire _publish_emission_check (routes to STRICT_FAIL / PARTIAL_OK / NAN_FILL / BLOCK_CRITICAL)
    4. 4 unit tests (one per emission mode). QG + push.
```

**Slot 7 — Emission Phase 6.4 features-cross STRICT_FAIL + Phase 6.5 features-\* seeds**:

```
MODEL TIER: Sonnet 4.6 / THINKING: high
WORKSPACE_ROOT: /Users/ikennaigboaka/Code/unified-trading-system-repos

PART A — NOW: Emission Phase 6.4 features-cross-instrument (STRICT_FAIL — trading-risk):
  Cross-asset signals propagate into strategy. Bad emission = trading risk event. STRICT_FAIL mode
  prevents silent bad data from reaching strategy without an explicit error.
  Pre-audit:
    grep -rn "record_captured\|manifest_writer\|publish" \
      features-service/features_service/cross_instrument/ --include="*.py" | grep -v .venv | head -20
  Steps:
    1. Add STRICT_FAIL seed for features-cross-instrument in UAC SERVICE_EMISSION_POLICY_SEED_DICT
    2. Wire _publish_emission_check in cross_instrument batch handler
    3. 4 unit tests (mode routing). QG + push.

PART B — PARALLEL: Emission Phase 6.5 features-* seeds (UAC@b570d49 already seeded; wire emit paths):
  Wire _publish_emission_check for: delta_one, calendar, onchain, commodity modules.
  Spawn sub-agents per module (PARALLEL — 4 sub-agents in one Agent tool call).
  Each sub-agent: audit → wire → 4 unit tests → QG → push.
```

**Slot 8 — Phase 6.8 instruments-service + Phase 6.9 QG sweep + bucket code migration**:

```
MODEL TIER: Sonnet 4.6 / THINKING: high
WORKSPACE_ROOT: /Users/ikennaigboaka/Code/unified-trading-system-repos

PART A — NOW: Phase 6.8 instruments-service 41 .add() callsites (decision: Option (a) locked):
  Pre-audit:
    grep -n "\.add(\|manifest_writer\.add\|ManifestWriter.*\.add" \
      instruments-service/instruments_service/ --include="*.py" | grep -v .venv
  Migrate all callsites from .add() → record_captured(). Per callsite:
    - service_emission_state kwarg (add to UAC SERVICE_EMISSION_POLICY_SEED_DICT if entry missing)
    - pipeline_mode kwarg (from instruments-service source type)
    - available_at per-row (assert_available_at_present)
  Wire publish_with_policy() from UTL@1a7e1d4b for instruments-service output data_types.
  QG STEP 5.64 (callsite AST walk) + STEP 5.69 (bucket f-strings) must pass. Push.

PART B — AFTER 6.3-6.8 all pushed: Emission Phase 6.9 QG workspace flip-sweep:
  Run QG STEP 5.64 across ALL services — expect zero .add() violations.
  Run QG STEP 5.66 — expect zero MultiWorkerWithoutShardIsolationError.
  Run QG STEP 5.69 — expect zero inline bucket f-strings.
  Fix any violations. Push. Ping Slot 1 → GATE 4 condition met.

PART C — AFTER GATE 2: Bucket code migration:
  Replace all hardcoded gs:// f-strings with resolve_bucket_name(cloud=..., kind=..., asset_group=..., env=...).
  QG STEP 5.69 returns zero hits. Push.
```

**Slot 8 session close status (2026-05-12):**

- PART A ✅ DONE — `instruments-service@27fbc90`
- PART B 🔴 BLOCKED — gate: Slots 6+7 confirm Phases 6.3+6.4+6.5 pushed → Slot 1 pings slot 8
- PART C 🔴 BLOCKED — gate: Gate 2 (bucket parity confirmed by Slot 3) → Slot 1 pings slot 8
- Reserve pulled: bucket_name_ssot Phase 0i tail ✅ DONE (`deployment-service@00a1288` + `utl@aeff9c19`)
- Slot 4 pinged with manual-audit provisioning handoff (6 buckets × 3 envs × 2 clouds)
- Next: watch `ikenna_orchestrator/pings/slot_8.md` for gate signals from Slot 1

---

### check_shard_freshness retry — CONFIRMED WORKING (correction 2026-05-12)

UTL ships `retry_failed: bool = True` as DEFAULT. Both MTDS (`tick_data_handler.py:190`) and MDPS
(`orchestration_service.py:158`) call without overriding — so `attempted_failed` rows ARE treated as not-fresh and
retried on next backfill. Memory note from 2026-05-06 ("retry doesn't work") pre-dates UTL@ba83a6f1 (shipped
2026-05-07). No additional orchestrator wiring needed.

---

### Serial gate status tracking

| Gate    | Condition                                                                | Status                                                                               | Unblocks                                                         |
| ------- | ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------ | ---------------------------------------------------------------- |
| Gate 0A | UAC Phase 0A + UTL Phase 0B pushed to origin                             | 🟢 FIRED (uac@0457b0e; UTL: helper pre-existed; PM@fc429e43 per Slot 4 ping)         | Slot 4 Phases 1–4 ✅ proceeding (Phase 1.5 QG green PM@ff2b46fb) |
| Gate 1  | Propagation chain Phases 1–4 + Phase 2.A all pushed to origin            | 🔴 OPEN                                                                              | Slot 3 apply-flips                                               |
| Gate 2  | Physical bucket migration (prod) complete + object-count parity verified | 🟢 FIRED (Slot 3 @ ~19:00 UTC — 16 STS jobs SUCCESS, parity verified; PM@`c52ddffb`) | Slot 3 PART C (resolve_bucket_name migration) + Slot 8 PART C    |
| Gate 3  | Phantom count = 0 (or <10 class-C) + manifest data-status panel accurate | 🔴 OPEN                                                                              | Backfill clearance                                               |
| Gate 4  | All writegate coding (2.A-2.D + 6.3-6.9 + Phase 6.8) pushed to origin    | 🔴 OPEN                                                                              | Full manifest audit                                              |

Slot 1 main owns the gate status column. Update when condition met; ping all affected slots.

---

### Writegate phase-to-slot assignments (no orphans)

| Writegate phase                                                                | Slot                      | Priority               | Est. cal AI-days |
| ------------------------------------------------------------------------------ | ------------------------- | ---------------------- | ---------------- |
| Phase 2.A — MDPS 4-state contract + `_create_empty_output` delete + v6 columns | **4**                     | P0 NOW                 | ~4               |
| Phase 2.B — MTDS cluster Option α (orchestrator boundary)                      | **6**                     | P0 NOW                 | ~4               |
| Phase 2.C — features-sports stubs + per-table available_at                     | **5**                     | P1 (after defi design) | ~2               |
| Phase 2.D — `match_end_time` from SFI freeze-detect (CORRECTED)                | **5**                     | P0 NOW                 | ~1               |
| Phase 2.E.3 — downstream consumer audit (7 services)                           | **8** (part of 6.9 sweep) | P1                     | ~1               |
| Phase 3.A — reconcilers dry-run + apply-flips                                  | **3**                     | P0 (GATE 1 gated)      | ~2               |
| Emission Phase 6.3 — features-volatility BUILD FROM SCRATCH                    | **6**                     | P0 NOW                 | ~4               |
| Emission Phase 6.4 — features-cross STRICT_FAIL                                | **7**                     | P0 NOW                 | ~3               |
| Emission Phase 6.5 — features-\* seeds wiring (4 modules)                      | **7**                     | P1                     | ~3               |
| Emission Phase 6.8 — instruments-service 41 `.add()` callsites                 | **8**                     | P0 NOW                 | ~3               |
| Emission Phase 6.9 — QG workspace flip-sweep                                   | **8**                     | P1 (after 6.3-6.8)     | ~1               |
| Phase 5 — coverage baseline ratchet CI gate                                    | **8** (tail)              | P2                     | ~1               |

---

## Defer post-deadline (NOT in this cycle)

- `wave2_polymarket_record_captured_from_counts` — deadline 2026-06-15.
- `simulation_scenarios_post_cutover` — deadline 2026-07-15.
- Emission Phase 6.6 + 6.7 (ml-training + strategy + execution + risk) — ~10-15 cal AI-days;
  post-Phase-4.DEFAULT-REMOVAL migration required first. File as separate Cycle 2 plan.
- Phase 3.D.5 v2 catalog-driven enumeration — multi-week scope; Cycle 3+.
- Wave 3.S/3.M/3.X (sports/prediction per-source rules + zero-activity bars + dimensions audit) — Cycle 2.
- CeFi Tardis re-shape Option A (252-shard re-rescan) — separate VM run; Cycle 2.
- Any plan with frontmatter `deadline:` ≥ 2026-05-24.
