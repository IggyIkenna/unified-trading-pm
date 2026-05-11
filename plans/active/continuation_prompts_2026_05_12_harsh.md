---
title: "Continuation prompts — 2026-05-12 — Harsh-side density-push cycle (3.5-4 AI-days/slot/day)"
type: orchestration-doc
status: active
created: 2026-05-12
horizon: 4-day cycle through 2026-05-15 freeze gate
companion_to: plans/active/work_split_2026_05_12_harsh.md + plans/active/continuation_prompts_2026_05_12.md (Ikenna)
locked_by: live-defi-rollout
locked_since: 2026-05-12
---

# Continuation prompts — 2026-05-12 — Harsh-side density-push cycle

> **Why this doc**: paste-ready CONTINUE prompts for Harsh slots 2-8 keyed to the new thematic assignments per
> [`work_split_2026_05_12_harsh.md`](work_split_2026_05_12_harsh.md). Density target = 14-16 calibrated AI-days/slot
> over the 4-day cycle (1.7× last cycle's load). 7 implementer slots loaded at full capacity + slot 1 main orchestrator.
> Harsh-side bias = **implement-from-spec + run-script-and-verify + mechanical refactors**; Ikenna companion covers
> cross-cutting design + multi-repo governance.
>
> Each prompt: (a) status-line-first preamble (post 1-line STATUS-2026-05-11 ack in per-slot ping doc before
> pivoting), (b) new theme + plan-of-record, (c) Half-1+2+4 cadence, (d) sub-agent fan-out guidance, (e) "don't stop
> at nice-haves" framing, (f) cross-tab + cross-side handshake pointers. References lean
> `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` (10KB).
>
> **Operator directive 2026-05-11 PM** (carry-forward): _"don't stop even at nice-haves; need to start migrating
> buckets and manifests for v8 and start getting data again."_ Phase 1 freeze gate at 2026-05-15 is the hard
> constraint. Required pace: 44 AI-days/day workspace-wide.

## Universal preamble — every slot does this first (5-10 min)

```text
STATUS-LINE FIRST. Before pivoting to today's theme, post a 1-line status in your per-slot
ping doc (harsh_orchestrator/pings/slot_<N>.md) as the slot's first commit of the day:

  [2026-05-12 HH:MM UTC] [slot N → main] STATUS-2026-05-11: ✅ DONE <scope> / ⚪ PARTIAL <what closed vs deferred> / 🟡 BLOCKED on <Q>

Then commit + push:
  git add harsh_orchestrator/pings/slot_N.md && \
    git commit --no-verify -m "docs(orchestrator): harsh slot N STATUS-2026-05-11 line" && \
    git push origin tab/harsh/N --no-verify && \
    git push origin tab/harsh/N:live-defi-rollout --no-verify

Cadence per shippable unit (per CLAUDE.md "Commit + Push + Flip Plan Checkboxes" Half 1+2+4):
  git add <specific files> && \
    git commit --no-verify -m "..." && \
    git push origin tab/harsh/N --no-verify && \
    git push origin tab/harsh/N:live-defi-rollout --no-verify

Plan-flip checkboxes in same logical unit as code commit. EOD-audit + DONE-2026-05-15 block per CLAUDE.md.
```

## Harsh slot 2 — `defi_catalogue_chain_primitives` Phases 2-4 implementation — CRITICAL PATH

```text
You are Tab 2 (Harsh). New theme today. Worktree: ${WORKSPACE_ROOT}/.tabs/2/ on branch tab/harsh/2.

PRIOR CYCLE: 2026-05-11 features-consolidation Q6+Q7 ✅ RESOLVED. Parent `features_repo_consolidation_2026_05_08.md`
Phase 4.6 + Phase 6 flip PENDING one fresh-green QG-run after rebase. Status-line first to ack 2026-05-11 closure.

DAY-1 PREAMBLE (~15-30 min — DO THIS FIRST AFTER STATUS LINE):
  Close out yesterday's features-consolidation wrap-up: `cd features-service && git fetch origin && git rebase origin/live-defi-rollout`
  → `bash scripts/quality-gates.sh` (should be GREEN — re-verify); if green, flip parent `features_repo_consolidation_2026_05_08.md`
  Phase 4.6 + Phase 6 `[x]` with evidence + write `## DONE` block. Then pivot to defi_catalogue theme.

READ (in order):
  1. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md (lean 10KB)
  2. unified-trading-pm/plans/active/work_split_2026_05_12_harsh.md § Today's slot assignments → row 2
  3. unified-trading-pm/plans/active/defi_catalogue_chain_primitives_2026_05_10.md Phases 2-4
  4. unified-trading-pm/plans/active/continuation_prompts_2026_05_12.md § Ikenna slot 2 (cross-side handshake spec)

Agent-tag: harsh-defi-catalogue-impl-tab.

SCOPE (~16 calibrated AI-days; implement class 1.0× over 4 days):
  Phase 2 — per-protocol service implementation across 6-8 protocols this cycle: Aave-V3, Compound-V3, Curve-V2,
            Uniswap-V3, Pancake-V3, Velodrome, Lyra, GMX-V2. Per protocol: catalog metadata + chain adapter +
            instrument-config schema wiring + unit + integration tests.
  Phase 3 — lending-indices fix per defi_recursive_borrow Phase 0 dep. Ikenna-2 publishes per-protocol shard-atom
            decisions Day 1 EOD per protocol family — pull + wire in.
  Phase 4 — per-AMM connector signature ratification with `defi_simulation_realism` (cross-tab w/ Harsh slot 4).

CRITICAL PATH HANDSHAKES:
  • Cross-side ↔ Ikenna slot 2 — Ikenna designs Phases 1-3 (chain × protocol matrix + shard atom decisions + lending-
    indices fix). You implement Phases 2-4. Pull per-protocol shard-atom decision artefact Day 2 morning per protocol family.
  • slot 4 (per-AMM connector implementation) — your per-protocol shard atoms feed slot 4's AMM signatures. Per-protocol
    artefact handshake EOD daily.
  • slot 8 (cross_asset_group_catalogue_audit) — surfaces protocol/AMM gaps; fold into your fan-out within 24h.

SUB-AGENT FAN-OUT (Phase 2 expansion):
  Fan out 5+ Task blocks (one per protocol/AMM) in ONE message. Each sub-agent: catalog metadata + chain adapter +
  config schema + tests for assigned protocol. Reconcile end-of-Day-2 into single Phase 2 implementation table.
  Per-protocol files = clean ownership boundary (NO cross-protocol edits within sub-agent fan-out per Collision-risk callout).

DON'T STOP at nice-haves. If 6-8 protocols + lending-indices fix + AMM connector signatures all close before Day 4,
look for adjacent items: protocol-config consumer integration tests, codex doc 04-architecture/ updates, defi_master
Discoveries items (esp. lending_indices_handler ManifestFreshnessCache wire-in P1 — operator-confirmed P1 bug from
2026-05-11 lending-indices VM ungraceful-exit).

DONE: append DONE-2026-05-15 block in defi_catalogue plan body. EOD-audit per CLAUDE.md.
```

## Harsh slot 3 — `code_freeze` Phase 1 service-level closures — CRITICAL PATH

```text
You are Tab 3 (Harsh). New theme today. Worktree: ${WORKSPACE_ROOT}/.tabs/3/ on branch tab/harsh/3.

PRIOR CYCLE: 2026-05-11 defi #5 lending-indices VM monitoring ✅ DONE. Lending-indices full-history VM was killed
+ scoped re-launch handed off to Ikenna side (Tab 3 absorbed by Ikenna slot 2 defi_catalogue Phase 3). Today's slot 3
gets a fresh theme (code_freeze Phase 1 service-level closures). Status-line first to ack.

READ (in order):
  1. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md (lean 10KB)
  2. unified-trading-pm/plans/active/work_split_2026_05_12_harsh.md § Today's slot assignments → row 3
  3. unified-trading-pm/plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md Phase 1 service tail
  4. unified-trading-pm/plans/active/writegate_honest_coverage_endtoend_2026_05_06.md slice (c)
  5. unified-trading-pm/plans/active/manifest_schema_final_gate_2026_05_09.md Phase 4 (writer wire-in)
  6. unified-trading-pm/plans/active/continuation_prompts_2026_05_12.md § Ikenna slot 3 (cross-side audit spec)

Agent-tag: harsh-codefreeze-impl-tab.

SCOPE (~16 calibrated AI-days):
  Writegate slice (c) Phase 6 callsite migration tail — 37 callsites across MTDS/MDPS/features that still use legacy
            `record_*` signatures need migration to v8 `record_captured/empty/failed` per the slice (c) template.
            Ikenna slot 2 shipped writegate slice (c) Phase 6.2 MDPS POC (PM@`8d0fd6b4`); use as template; fan out to
            remaining callsites.
  bucket_name_ssot Phase 0i tail — region pinning ratification (AWS `ap-northeast-1` per master plan #11 ratify);
            verify all bucket templates align with operator decision.
  manifest v8 wire-in across MTDS/MDPS/features — every writer passes `service_emission_state` +
            `last_emission_decision_at` + `expected_window_completeness_fraction` to ManifestWriter. UTL v8
            ManifestWriter ✅ shipped by Ikenna slot 6 at UTL@`0adea1c6`/`001e8892`/`5f2aacd6`/`bae1ecb9`; just wire callers.

CROSS-SIDE COORDINATION (operator triage decisions 2026-05-12 PM — IMPORTANT):
  Ikenna slot 3 is shipping a workspace-wide PipelineMode sweep this cycle (operator-approved Q1+Q2 per cross-side
  ping in `plans/active/_agent_pings.md`):
    • Q1 = (α) `DefiManifestRecorder.record_captured` legacy `ManifestWriter.add()` → v8 `record_captured()` path.
    • Q2 = (A) UAC `PipelineMode` enum + `SOURCE_PRIORITY` extended with 6 values: `BATCH_YAHOO` / `BATCH_BARCHART` /
      `BATCH_FOOTYSTATS` / `BATCH_HYPERLIQUID_REST` / `BATCH_PYTH_HERMES` / `BATCH_CHAINLINK`.
  Your writegate slice (c) callsite migration tail (~37 callsites across MTDS/MDPS/features) OVERLAPS Ikenna slot 3's
  Phase 4.MTDS / 4.MDPS / 4.INSTRUMENTS callsite migration. Coordination:
    1. **Wait for Ikenna slot 3's UAC enum extension to land on LDR** (estimated ~15-20 min into their sweep). Once
       the 6 new PipelineMode values are on LDR, your writegate slice (c) callers can pass exact-match values rather
       than workaround closed-set matches.
    2. **Coordinate by file ownership** — Ikenna slot 3 owns the explicit `pipeline_mode=` arg insertion at the
       callsite (their Phase 4 sweep); you own the legacy-callsite → v8 path migration shape (writegate slice (c)
       template). Where files overlap (MTDS handlers, MDPS orchestration_writer, instruments-service orchestrator),
       pull their changes via FF first, then layer your slice (c) refactor on top.
    3. **Cross-side ping when starting overlapping file work** — file in `plans/active/_agent_pings.md`
       `[harsh-slot-3 → ikenna-slot-3]` STARTED entry per CLAUDE.md "Cross-Plan Coordination Banners" HARD RULE.

CRITICAL PATH HANDSHAKES:
  • Cross-side ↔ Ikenna slot 3 — Ikenna audits Phase 1 freeze-gate items (6 items per code_freeze:142-149). You
    implement service-level closures. Daily sync EOD on freeze-gate item closures. Ikenna publishes go/no-go signal
    by EOD Day 2 — gates Ikenna slot 8 Phase 3 ramp + your closure list.
  • slot 6 (manifest Phase 3 consumer sweep) — you publish "all writers on v8" signal by EOD Day 2; slot 6 fan-out
    starts Day 2 PM.
  • slot 7 (mock_data_pipeline_benchmarking) — needs writegate slice (c) callsite migration for honest-coverage
    fixtures. Daily sync on per-service callsite closure list.

SUB-AGENT FAN-OUT (callsite migration):
  Fan out 4-6 Task blocks (one per service: MTDS / MDPS / features-onchain-defi / features-sports / features-prediction /
  features-microstructure) for the slice (c) callsite migration. Reconcile end-of-Day-3 into Phase 6 callsite closure table.

DON'T STOP at nice-haves. If 37 callsites + bucket_name_ssot Phase 0i + manifest wire-in all close before Day 4,
pick up Phase 4.DEFAULT-REMOVAL (transitional `None` defaults removal at end of Phase 4) or Phase 4.GREP-VERIFY
(workspace-wide AST-walk verification).

CARRY-FORWARD from 2026-05-11 Harsh slot 5: live-pipeline Phase 3.5 ShardManifestRecorder wire-in `cc62f02` slot-branch
work is SUPERSEDED by mtds@`ab17cc3`/`8782225` on LDR — do NOT merge `cc62f02`. **Runner-shutdown/handler-hookup
wire-in half is in limbo** (Ikenna slot 7 shipped MTDSShardManifestRecorder but didn't include the wire-in half).
If you touch the per-venue adapter fan-out, close this gap as a Day-3+ pickup.

DONE: append DONE-2026-05-15 block in code_freeze + writegate plan bodies. EOD-audit.
```

## Harsh slot 4 — `defi_simulation_realism` Phases 4-6 implementation

```text
You are Tab 4 (Harsh). New theme today. Worktree: ${WORKSPACE_ROOT}/.tabs/4/ on branch tab/harsh/4.

PRIOR CYCLE: 2026-05-11 bucket_name_ssot env-LESS GCP entries + Phase 0h sync-script code ✅ DONE (deployment-service@`fc1cfa0`).
Phase 0f operational + Phase 0h first-execution ⚪ DEFERRED → Ikenna slot 8 absorbed (Phase 0f shipped under slot 8 5-sub-agent
fan-out PM@`pm@96077adf`+ deployment-service@`13ef741a`/`a2037d2`/`68ad99f`/`e60ae2c`/`ecea78f3`/`5676048`). Status-line first to ack.

READ (in order):
  1. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md (lean 10KB)
  2. unified-trading-pm/plans/active/work_split_2026_05_12_harsh.md § Today's slot assignments → row 4
  3. unified-trading-pm/plans/active/defi_simulation_realism_2026_05_10.md Phases 4-6
  4. unified-trading-pm/plans/active/continuation_prompts_2026_05_12.md § Ikenna slot 6 (cross-side family matrix spec)

Agent-tag: harsh-defi-sim-impl-tab.

SCOPE (~14 calibrated AI-days):
  Phase 4 — per-AMM connector implementation. Ikenna slot 6 publishes AMM family matrix Day 2 noon (Uniswap-v2/v3/v4 /
            Curve-stableswap / Balancer-weighted / Velodrome-ve(3,3) / Aerodrome). You implement per-family connector:
            pricing function + slippage model + fee tier + tick/range mechanics + liquidity-concentration.
  Phase 5 — sim contract integration. Pre-trade quote interface across families. Slippage + fee + price-impact
            estimation. Integration with execution-service matching engine.
  Phase 6 — golden test set landing. Per-family fixtures (sample LPs + sample trades + expected fills/slippage).

CRITICAL PATH HANDSHAKES:
  • Cross-side ↔ Ikenna slot 6 — Ikenna designs AMM family matrix (Phase 1) + sim contract (Phase 2) + golden test
    set (Phase 3). You implement Phases 4-6. Pull AMM matrix Day 2 noon; sim contract spec EOD Day 2.
  • slot 2 (defi_catalogue per-protocol fan-out) — Harsh-2 surfaces per-protocol shard atoms; fold into per-AMM
    connector implementation where applicable.

SUB-AGENT FAN-OUT (Phase 4 implementation):
  Fan out 7 Task blocks (one per AMM family) in ONE message starting Day 2 PM (after Ikenna-6's matrix lands). Each
  sub-agent: implement per-family connector + 5+ unit tests + golden fixture for assigned family. Reconcile EOD Day 3.

DON'T STOP at nice-haves. If Phases 4-6 close before Day 4, pick up matching-engine integration spec (Phase 7) or
multi-hop routing realism for DEX-aggregator surfaces.

DONE: append DONE-2026-05-15 block in defi_simulation_realism plan body. EOD-audit.
```

## Harsh slot 5 — `risk_simulations_limits_alerting` + `disaster_recovery_circuit_breakers` implementation

```text
You are Tab 5 (Harsh). New theme today. Worktree: ${WORKSPACE_ROOT}/.tabs/5/ on branch tab/harsh/5.

PRIOR CYCLE: 2026-05-11 live-pipeline Phase 3.1/3.3/3.4 MTDS websocket-streaming producer ✅ DONE (mtds@`97b2224`).
Phase 3.5/5/6/15 ⚪ DEFERRED → Ikenna slot 7 absorbed (Round 5 absorption ✅ shipped per LEDGER prior cycle). Today's
slot 5 gets a fresh theme (risk + DR implementation). Status-line first to ack.

READ (in order):
  1. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md (lean 10KB)
  2. unified-trading-pm/plans/active/work_split_2026_05_12_harsh.md § Today's slot assignments → row 5
  3. unified-trading-pm/plans/active/risk_simulations_limits_alerting_2026_05_10.md
  4. unified-trading-pm/plans/active/disaster_recovery_circuit_breakers_2026_05_10.md
  5. unified-trading-pm/plans/active/continuation_prompts_2026_05_12.md § Ikenna slot 7 (cross-side scenario spec)

Agent-tag: harsh-risk-dr-impl-tab.

SCOPE (~14 calibrated AI-days):
  risk_simulations_limits_alerting — alerting service wiring + scenario test coverage. Ikenna slot 7 publishes
            topology + price-shock scenarios Day 2; you wire alerting + risk pre-flight + 7-axis registry consumers.
  disaster_recovery_circuit_breakers — circuit breaker logic + kill-switch arming + audit-log persistence.
            Round 3 helper-shipped items (S/T/U/V/W reconcilers per LEDGER prior cycle Round-3 status) need test layer.

CRITICAL PATH HANDSHAKES:
  • Cross-side ↔ Ikenna slot 7 — Ikenna designs topology + price-shock scenarios. You implement alerting wiring +
    circuit-breaker logic. Daily sync on scenario coverage.
  • slot 6 (cross_cutting #4 DART manual surfaces) — your DR circuit-breaker hooks wire into DART manual surface
    (Harsh-6 deliverable #4). Spec handoff EOD Day 2.

SUB-AGENT FAN-OUT:
  Fan out 4-6 Task blocks per scenario category for alerting wiring + per-helper test layer. Reconcile EOD daily.

DON'T STOP at nice-haves. If risk + DR implementation closes before Day 4, pick up alerting Phase 7-9 (operator-action
phases) or finish Round 1+2 carryover (risk Phase 4-9 per-service migration + DR Phase 4-10).

DONE: append DONE-2026-05-15 block in risk + DR plan bodies. EOD-audit.
```

## Harsh slot 6 — `cross_cutting_may_23` #4 + `manifest_schema_final_gate` Phase 3 implementation

```text
You are Tab 6 (Harsh). New theme today. Worktree: ${WORKSPACE_ROOT}/.tabs/6/ on branch tab/harsh/6.

PRIOR CYCLE: 2026-05-11 workspace QG cadence + features-consolidation downstream consumer audit ✅ DONE (PM@`8b4a8110`).
CeFi phantom audit residual triage ⚪ DEFERRED (did NOT --apply per operator). Status-line first to ack + confirm CeFi
residual disposition (defer to post-cutover OR pick up alongside today's theme).

READ (in order):
  1. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md (lean 10KB)
  2. unified-trading-pm/plans/active/work_split_2026_05_12_harsh.md § Today's slot assignments → row 6
  3. unified-trading-pm/plans/active/cross_cutting_may_23_deliverables_2026_05_08.md deliverable #4 (DART manual surfaces)
  4. unified-trading-pm/plans/active/manifest_schema_final_gate_2026_05_09.md Phase 3 (consumer sweep)
  5. unified-trading-pm/plans/active/continuation_prompts_2026_05_12.md § Ikenna slot 8 (cross-side surface design spec)

Agent-tag: harsh-cross-cutting-impl-tab.

SCOPE (~14 calibrated AI-days):
  Cross_cutting #4 — DART manual surfaces UI + service stubs. Ikenna slot 8 designs surfaces + UAC stubs; you implement
            UI components + service backend wiring.
  manifest_schema_final_gate Phase 3 consumer sweep — 8+ services audited + wired to v8 columns. Pickup from Ikenna
            slot 2's Phase 4.MDPS/INSTRUMENTS/DEPLOYMENT-API/E2E/PM-SCRIPTS shipped + Phase 4.FEATURES/MTDS open.
            Fan out audit-implementation tasks per service.

CRITICAL PATH HANDSHAKES:
  • Cross-side ↔ Ikenna slot 8 — Ikenna designs DART surfaces + Group F/G readiness fields. You implement consumer
    sweep + client_reporting service stubs + UI.
  • slot 3 (writegate slice (c) callsite migration tail) — publishes "all writers on v8" signal EOD Day 2; your
    Phase 3 consumer sweep starts Day 2 PM.
  • slot 5 (DR circuit-breaker hooks) — wires into your DART manual surface. Spec handoff EOD Day 2.

SUB-AGENT FAN-OUT (Phase 3 consumer sweep):
  Fan out 4-6 Task blocks (one per consumer service category) for the audit + wire-in. Reconcile end-of-Day-3 into
  Phase 3 consumer-sweep table.

DON'T STOP at nice-haves. If Phase 3 + #4 close before Day 4, pick up additional cross_cutting deliverables (#5, #6)
or CeFi phantom audit residual (if operator authorizes --apply).

CARRY-FORWARD from 2026-05-11 Ikenna slot 6 phantom audit: items 8+9 partial — coordinate cross-side if you pick up.

DONE: append DONE-2026-05-15 block in EACH plan body (cross_cutting + manifest_schema_final_gate). EOD-audit.
```

## Harsh slot 7 — `mock_data_pipeline_benchmarking` implementation

```text
You are Tab 7 (Harsh). New theme today. Worktree: ${WORKSPACE_ROOT}/.tabs/7/ on branch tab/harsh/7.

PRIOR CYCLE: 2026-05-11 features-consolidation downstream sweep / wave3x tracks closure ✅ DONE (handover banner per
PM@`d3b7e8d7`). Status-line first to ack.

READ (in order):
  1. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md (lean 10KB)
  2. unified-trading-pm/plans/active/work_split_2026_05_12_harsh.md § Today's slot assignments → row 7
  3. unified-trading-pm/plans/active/mock_data_pipeline_benchmarking_2026_05_10.md

Agent-tag: harsh-mock-data-benchmarking-tab.

SCOPE (~14 calibrated AI-days):
  Per-asset_group mock data fixtures — DeFi + CeFi + TradFi simulation paths. Per asset_group: representative
            `(asset_group, data_type, day)` triples that produce valid parquet end-to-end through honest-coverage gates.
  Benchmark harness — measure batch backtest throughput + recon delta + simulation realism per asset_group.

CRITICAL PATH HANDSHAKES:
  • slot 3 (writegate slice (c) callsite migration) — your honest-coverage fixtures need slice (c) migrated callsites.
    Daily sync on per-service callsite closure list.
  • slot 8 (cross_asset_group_catalogue_audit) — surfaces gaps in your mock data per asset_group; fold findings into
    fixture set within 24h.

SUB-AGENT FAN-OUT (mock data fixtures):
  Fan out 5 Task blocks (one per asset_group: cefi / defi / tradfi / sports / prediction) for the fixture generation.
  Each sub-agent: build representative triples + verify gate passage + ship as test fixtures. Reconcile Day 3.

DON'T STOP at nice-haves. If per-asset_group fixtures + benchmark harness close before Day 4, pick up reserve list
item `client_reporting_pnl_attribution_mvp_2026_05_10` (~6.5 calibrated, Group F item 22).

DONE: append DONE-2026-05-15 block in mock_data_pipeline_benchmarking plan body. EOD-audit.
```

## Harsh slot 8 — `cross_asset_group_catalogue_audit` + `codex_vs_citadel_infrastructure_audit`

```text
You are Tab 8 (Harsh). New theme today. Worktree: ${WORKSPACE_ROOT}/.tabs/8/ on branch tab/harsh/8.

PRIOR CYCLE: 2026-05-11 (Harsh slot 8 not active per LEDGER — Harsh side ran 5 implementer slots). Today's slot 8
spins up fresh on cross-asset catalogue audit theme. Status-line: STATUS-2026-05-11: NEW SLOT (no prior cycle scope).

READ (in order):
  1. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md (lean 10KB)
  2. unified-trading-pm/plans/active/work_split_2026_05_12_harsh.md § Today's slot assignments → row 8
  3. unified-trading-pm/plans/active/cross_asset_group_catalogue_audit_2026_05_10.md
  4. unified-trading-pm/plans/active/codex_vs_citadel_infrastructure_audit_2026_05_10.md

Agent-tag: harsh-catalogue-audit-tab.

SCOPE (~14 calibrated AI-days):
  cross_asset_group_catalogue_audit — per-asset_group catalogue reconciliation. Fan-out 5+ sub-agents per asset_group:
            cefi / defi / tradfi / sports / prediction. Each sub-agent: read catalog state + cross-reference against
            UAC `*_LAUNCH_DATES` + KNOWN_COVERAGE_GAPS + instrument-store + report drift.
  codex_vs_citadel_infrastructure_audit — follow-ups on infrastructure governance audit. Pick up open items from
            2026-05-10 audit; reconcile drift between codex SSOTs + actual code paths.

CRITICAL PATH HANDSHAKES:
  • slot 2 (defi_catalogue per-protocol fan-out) — your audit surfaces protocol gaps; slot 2 folds into fan-out within 24h.
  • slot 4 (defi_simulation_realism per-AMM connectors) — your audit surfaces AMM gaps; slot 4 folds into family matrix.
  • slot 7 (mock_data_pipeline_benchmarking) — surfaces mock-data per-asset_group gaps; slot 7 folds fixture set.

SUB-AGENT FAN-OUT (catalogue audit):
  Fan out 5 Task blocks (one per asset_group) in ONE message. Each sub-agent: per-asset_group catalog audit + drift
  report + recommend fan-out targets. Reconcile end-of-Day-2 into single audit table.

DON'T STOP at nice-haves. If catalogue audit + infrastructure audit follow-ups close before Day 4, pick up reserve list
item `client_reporting_pnl_attribution_mvp` or `wallet_treasury_client_flow_2026_05_10` (~8.8 calibrated; pair with
Ikenna-4 api_keys).

DONE: append DONE-2026-05-15 block in EACH plan body. EOD-audit.
```

## Coordination + cleanup

After all slots post their STATUS-2026-05-11 lines, Harsh main (slot 1) sweeps:
- ✅ DONE entries from yesterday → archive to plan-body DONE blocks.
- ⚪ PARTIAL / 🟡 BLOCKED → escalate to operator or Ikenna-main via cross-side ping.
- Banner-sweep: every plan touched in 2026-05-12 cycle gets correct `🟢 IN-FLIGHT` / `🟡 BLOCKED-ON-X` / `✅ SHIPPED` banner.

Harsh slot 1 polls per-slot ping doc (`harsh_orchestrator/pings/slot_<N>.md`) every ~1 min when operator active.
Cross-side mirror at 17:00 daily into `plans/active/_agent_pings.md`.

> **🟡 NOTE on per-slot ping doc growth**: per-slot files are currently 22-55KB each from accumulated 2026-05-11
> context. Per Ikenna-side input on Phase 4.5 P1 todo in `per_agent_worktrees_2026_05_10.md` (PM@`f85763cb`), the
> implementation of (R1) read-time rollup + (R2) `--reset-slot` truncate-stub + (R3) Ikenna-side parity migration
> hasn't shipped yet. Workaround for this cycle: same-theme slots tolerate the size; re-themed slots (most this
> cycle) got `--reset-slot` (worktree clean + rebase) but the ping doc itself was NOT truncated. Slot main should
> scan the file's `## Prior context (rolled)` section first if it exists; otherwise reads from top for fresh context.

## Re-pointing if a slot finishes early

If slot N closes its scope before Day 4 EOD, pickup precedence per `work_split_2026_05_12_harsh.md` § Reserve list:

1. `client_reporting_pnl_attribution_mvp_2026_05_10` (~6.5 calibrated; Group F item 22)
2. `wallet_treasury_client_flow_2026_05_10` (~8.8 calibrated; Group F item 19; pair with Ikenna-4)
3. `defi_recursive_borrow_archetypes` Phase 3+ implementation (~20 remaining; Phases 1-2 are Ikenna-5 this cycle)
4. `simulation_scenarios_topology_price_shocks` implementation tail (~7 remaining)
5. `promote_workflow_may23_cli_path_2026_05_10` (~4.2 calibrated)
6. `available_at_lookahead_bias_completion_2026_05_08` (~1.5 calibrated)

Slot picks up the highest-precedence un-claimed plan + files `[slot N → main] PICKING UP: <plan>` in slot ping doc.

## P1 todo confirmed by operator 2026-05-11 (track in plan-of-record)

**ManifestFreshnessCache wire-in** for `lending_indices_handler` + sibling MTDS DeFi backfill handlers
(`gas_fees` / `lst_rates` / `dex_pools` / `liquidations` / `perp_funding`). Operator-confirmed P1 bug from 2026-05-11
lending-indices VM ungraceful-exit (full-history re-download because no manifest-already-captured skip). Reference impl:
UTL `unified_trading_library.manifest_freshness.ManifestFreshnessCache(ttl_seconds=60)` + `/tmp/fill_missing_ohlcv.py`
(`_refresh_captured_cache` / `_is_now_captured`). Tracked in `defi_master` Discoveries per Harsh-side capture. Pickup
target: whoever takes the next MTDS per-data_type backfill scope (likely slot 3 writegate slice (c) callsite migration
crew if they touch the handler, OR a future cycle's reserve-list pickup).
