---
doc_type: issue
title:
  Codex-vs-Citadel Blocks C/D/E/F audit findings — researcher experience, operational governance, alpha-multiplying
  primitives, non-negotiable primitives
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    deployment-service,
    execution-service,
    features-service,
    strategy-service,
    unified-trading-pm,
    unified-trading-system-ui,
  ]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-10
author: ikenna + main agent
source:
  [
    plans/active/issues/codex_vs_citadel_block_b_audit_findings_2026_05_10.md (sibling — Block A2 + B fills),
    plans/active/codex_vs_citadel_infrastructure_audit_2026_05_10.md (spawned audit plan; this issue doc closes the last
    4 audit blocks ahead of the 12-sub-agent fan-out so the question doc isn't needed for execution),
    PM@e381d016 (retired question doc — git-history recovery for original Block-A/B prose),
  ]
locked_by: live-defi-rollout
locked_since: 2026-05-10
---

# Codex-vs-Citadel Blocks C/D/E/F audit findings

> **Severity**: P1 — same shape as Block B sibling. Recommendations are mostly post-cutover but high-leverage; some are
> immediate (D3 per-agent worktrees, D5 sub-agent rule-injection trim) given the operator-decided parallel-agent SSOT
> direction. **Blast radius**: workspace-wide (architecture / governance / researcher workflow). **Suggested owner**:
> spawned audit plan + named active plans where dispositions point.

## Why this doc exists

Per operator directive 2026-05-09: _"the rest of your question you can answer with the code understanding... plug gaps
with active plan updates."_ + 2026-05-10: _"do it all till we don't need the question doc anymore to execute as we have
all the answers in plans."_ Block A and B were filled in PM@b9c93a38..PM@e381d016 + sibling issue doc; this doc finishes
blocks C/D/E/F so all audit answers live in active plans rather than the (now retired) question doc.

This doc is intentionally **denser** than the sibling — fewer benchmark sketches, more concrete evidence + crisp
KEEP/LIFT/CONSOLIDATE/DELETE/ADD recommendations + which active plan absorbs each.

## Block C — Researcher experience + alpha workflow

### C1 — No first-class "research → paper → live" flow for the alpha researcher

- **Code state**: DART surface exists in `unified-trading-system-ui/app/(platform)/services/research/` (allocate page,
  family-archetype-asset-group-browser, dashboard, onboarding/cockpit) — UI is rich. **No active researcher notebook
  surface in the workspace** (`find -path '*/notebooks/*' -name '*.ipynb'` returns only ARCHIVED ones in
  `archive/new-sports-batting-services/notebooks/`). The researcher's golden path is **implicit-knowledge-only**: they
  must understand ServiceEmissionPolicy, manifest writers, write-gates, shard-granularity SSOT, hive partitions,
  batch=live seams, UAC schema placement, instrument lifecycle hot-reload, the 5 axes of operational mode
  (env_canon.py), the ML experiment lifecycle, the strategy registry-v2 axes, restriction-policy, archetype declaration
  in UAC, etc. — before they can backtest a new signal.
- **Codex state**: `/codex/04-architecture/ml-experiment-lifecycle.md` covers ML lifecycle but not "researcher → paper →
  live as one workflow". `/codex/04-architecture/research-service-and-dart-integration.md` covers DART integration but
  not the researcher's golden path. **No `/codex/09-strategy/researcher-experience-golden-path.md` exists.**
- **Citadel-benchmark gap**: large. A Citadel-grade non-HFT shop ships 5-10 ideas/researcher/month; our friction
  predicts <1/month.
- **Recommendation**: **ADD (post-cutover, highest C-block leverage)**.
  1. **NEW codex doc**: `/codex/09-strategy/researcher-experience-golden-path.md` — single-page workflow from "I have a
     hypothesis" → backtest → walk-forward → paper → live, with every prereq linked.
  2. **NEW researcher entry-point**: `unified-trading-services/research/notebooks/golden_path.ipynb` (or equivalent
     under monorepo-consolidated shape) — bootstrap notebook that hides ServiceEmissionPolicy / manifest / hive / UAC
     ceremony behind 3-4 helper imports. Researcher writes signal → calls `evaluate(signal, archetype, period)` → gets
     backtest + walk-forward + capacity-curve + factor-decomp output.
  3. **GATE**: integration test that the golden-path notebook runs end-to-end under `dev-tiers.sh --tier 0` against mock
     data with no manual setup.
- **Cost**: ~3-4 AI-days (codex doc + notebook + helpers + integration test). **Saved cost**: directly compounds into
  alpha velocity — every reduced friction × every researcher × every idea.
- **Active plan to file/extend**: NEW `plans/active/researcher_experience_golden_path_<date>.md` post-cutover, OR fold
  into the spawned monorepo plan. Sibling question doc `topology_features_strategy_ml_execution_2026_05_08.md` overlaps
  — may be the natural home.

### C2 — No alpha attribution stack at the architecture level

- **Code state**: `pnl-attribution-service` EXISTS — has `engine/`, `analytics/`, `execution_alpha/` sub-modules. Real
  service, not a stub. But: surface is realised-PnL accounting (fee/funding/yield reconciliation per
  `Plan: Position Precision & P&L Hardening 2026-03-11`), NOT alpha-research decomposition. Missing primitives:
  - per-signal PnL decomposition ("which feature drove which trade?")
  - counterfactual PnL ("what if we hadn't traded this hour?")
  - regime-aware Sharpe (per-market-state performance)
  - capacity curves (PnL vs NAV — does the strategy decay above $X NAV?)
  - factor exposures (is the carry archetype just a beta to ETH-staking-yield?)
- **Codex state**: NONE of the above five primitives have a codex doc.
- **Operational state**: every archetype currently lives or dies on aggregate-PnL evidence — no factor-decomposition
  evidence to scale / retire decisions.
- **Citadel-benchmark gap**: large. Alpha-research-grade attribution is the foundation Citadel shops are built on.
- **Recommendation**: **ADD (post-cutover, highest E-block leverage; folds with C2 here since C is workflow-side and E3
  is primitive-side)**.
  1. **NEW UAC**: `unified_api_contracts.canonical.alpha_attribution` — typed schemas for `SignalPnL`,
     `CounterfactualPnL`, `RegimeConditionalSharpe`, `CapacityCurvePoint`, `FactorExposure`.
  2. **NEW pnl-attribution-service module**: `analytics/alpha_research/` — per-archetype implementations consuming
     existing realised-PnL + adding the 5 primitives.
  3. **NEW strategy-service consumer**: dashboard endpoint exposing per-archetype alpha decomposition for the
     researcher.
  4. **NEW researcher notebook surface**: integrates with C1's golden-path notebook.
- **Cost**: ~5-7 AI-days. **Saved cost**: every scale / retire / capital-allocation decision becomes evidence-based;
  recovers every wasted week of operating an archetype that's actually decayed beta.
- **Active plan to file/extend**: NEW `plans/active/alpha_attribution_stack_<date>.md` post-cutover. Sibling
  `client_reporting_pnl_attribution_2026_05_08.md` is REPORTING-side; this is RESEARCH-side; both can ship.

### C3 — Portfolio construction + correlation-aware sizing

- **Code state**: **EXISTS** — `strategy-service/strategy_service/portfolio_allocator/` has 8 archetype engines
  (`archetypes.py`), `cadence.py`, `emitter.py`, `guard_rails.py`, `service.py`, `share_class_fx.py`. Per-archetype
  dispatch via `AllocatorArchetype` UAC enum. Takes NAV / returns / volatility / sharpe / CVAR / regime signal → target
  weights. Sources from PBMS NAV series + strategy-service slot list. `risk-and-exposure-service` has
  `core/correlation_matrix.py` + `v2/correlation_cap.py`. **This is most of the C3 + E1 + E7 critique already built.**
- **Codex state**: `/codex/03-services/portfolio-allocator.md` exists but appears thin per the original audit.
- **Citadel-benchmark gap**: smaller than I originally thought — **the primitives exist**. The gap is: (a) Unified
  workflow exposing them to the researcher (C1 dependency). (b) Explicit Kelly / fractional-Kelly engine (the 8
  archetype engines may approximate but need named formalisation). (c) Capacity curves as a first-class output
  (per-strategy NAV → expected-PnL curves).
- **Recommendation**: **KEEP + LIFT to documentation parity**. The code is mostly built; the codex undersells it.
  1. **EXTEND codex**: `/codex/03-services/portfolio-allocator.md` documents the 8 archetypes + Kelly mapping (which
     archetype = which sizing rule).
  2. **NEW**: explicit `portfolio_allocator/kelly.py` + `portfolio_allocator/capacity.py` modules if not already covered
     by the 8 archetypes (audit during Phase 1).
- **Cost**: ~1-2 AI-days. **Active plan**: extend the spawned audit plan Phase 1 (per-area audit) for this row.

### C4 — ML lifecycle integrated into a single research loop

- **Code state**: `ml-training-service` exists; `unified-trading-pm/codex/04-architecture/ml-experiment-lifecycle.md`
  covers experiment lifecycle. `experiments/phase_5d_runlist_2026_04_18.yaml` shows real experiment runs. The pieces
  exist; the workflow integration is the gap (composes with C1).
- **Recommendation**: **ALIGN — fold into C1's golden-path notebook + codex doc**. Zero new code; integrate existing
  ml-training-service pieces into the researcher entry point.

### C5 — Regime-adaptation primitive at the framework level

- **Code state**: **PARTIALLY EXISTS** — `features-service/features_service/commodity/engine/regime/hmm_detector.py`
  - `cross_instrument/app/calculators/regime_calculator.py`. Per-asset-group, fragmented; no unified `Regime` UAC
    primitive that strategies can condition on uniformly.
- **Codex state**: no codex doc covers cross-asset-group regime as first-class.
- **Citadel-benchmark gap**: medium. Code exists per asset-group; needs unification.
- **Recommendation**: **LIFT (post-cutover)**. UAC `Regime` discriminated-union (vol_regime / correlation_regime /
  liquidity_regime / macro_regime) + cross-asset-group `regime_features` consumer in features-service. ~3-4 AI-days.
- **Active plan**: NEW `plans/active/regime_unified_primitive_<date>.md` post-cutover.

## Block D — Operational + governance overhead

### D1 — "No fire-and-forget VM launches" — symptom vs cause; should backfills move to a job runtime?

- **Code state**: 68 `launch-*.sh` scripts in `deployment-service/scripts/vm/` (heavy GCE-instance use). AWS Batch
  terraform EXISTS in `deployment-service/terraform/modules/container-job/aws/` — partial job-runtime infra is already
  built (just not used for backfills yet).
- **Codex state**: `/codex/05-infrastructure/vm-tarball-deployment.md` is the canonical SSOT;
  `codex/05-infrastructure /launcher-script-ssot.md` codifies the launcher convention. Both treat VM-launches as the
  dominant shape.
- **Citadel-benchmark gap**: large operationally. Job runtime makes lifecycle events a framework property, not an opt-in
  discipline. The "no fire-and-forget" rule + 200 lines of launcher discipline + the vm_zombie_watchdog.py + per-prefix
  VM_PREFIX_TO_BUCKET dict all collapse if backfills run on AWS Batch / Cloud Run jobs / Modal / Ray Tasks.
- **Recommendation**: **CONSOLIDATE (post-cutover, after May-23 stabilises)**.
  1. Pick ONE job runtime (operator decision; AWS Batch is half-built per terraform — natural choice).
  2. Port 1-2 backfill flavours as proof (e.g. MTDS Tardis backfill).
  3. Measure cost-per-task-event-emission + silent-failure rate vs current GCE shape.
  4. Migrate per-flavour over 1-2 quarters; deprecate `gcloud compute instances create` launchers.
- **Cost**: ~2 weeks for proof-of-concept; ~3-6 months full migration. **Saved cost**: removes "no fire-and-forget"
  discipline entirely; ~150 lines of CLAUDE.md collapse; ~1 week/quarter of VM-zombie-debugging recovered.
- **Active plan**: NEW `plans/active/job_runtime_migration_<date>.md` post-cutover. Composes with cloud-agnostic
  migration master since AWS Batch is the natural target.

### D2 — Homemade distributed-write protocol (per-VM shard isolation + concurrency CAS + manifest consolidator)

- **Code state**: `manifest_writer.py` (4360 lines) implements the per-VM shard isolation + CAS + consolidator daemon
  protocol. This is multi-writer ACID-on-object-storage hand-rolled.
- **Citadel-benchmark gap**: Iceberg / Delta Lake / Hudi solve this. Postgres-as-coordinator solves this.
  Temporal/Airflow/Prefect own the workflow coordination.
- **Recommendation**: **EVALUATE (post-cutover, P2)**. Cost-benefit: the homemade protocol works (per Block B B3
  evidence — operator's expected-universe-v2 plan already on the right shape). Off-the-shelf swap is multi-week
  re-architecture for marginal correctness improvement. **Likely outcome: KEEP for now; revisit when scale forces it
  (e.g. >100 concurrent backfill workers, or when team adds a data-engineering hire).**
- **Active plan**: NONE NEEDED — file an evaluation issue post-cutover IF operator wants formal cost-benefit.

### D3 — Plan-flip-as-you-ship + foot-guns + per-agent worktrees (operator-promoted)

- **Operator directive 2026-05-09 #1**: parallel-agent flow IS the SSOT; tighten it. **D3 is the structural fix.**
- **Code state**: shared `.git/` + working tree across N agents per operator. 4 documented foot-guns (#1 foreign work
  bundled in, #2 path-arg masking, #3 concurrent-agent reset, #4 prek auto-restore race) — all stem from shared-tree
  shape. `git worktree add` would isolate the index per agent.
- **Recommendation**: **ADD (immediate, pre-cutover even)**. Highest D-block leverage given operator-decided
  parallel-agent SSOT.
  1. Operator workspace bootstrap creates per-agent worktrees: `.cursor-worktrees/{agent-tag}/` pointing at the same
     `live-defi-rollout` branch with isolated indexes.
  2. Each Cursor / Claude Code session opens its own worktree; commits land on the same branch via per-worktree push.
  3. Foot-guns #1 / #2 / #3 / #4 become unrepresentable (separate `.git/index` per agent).
  4. CLAUDE.md "mandatory pre-commit check" + "pathspec commit form" rules collapse to ~30 lines (the foot-gun
     mitigations were band-aids on the cause).
- **Cost**: ~20-30 lines of bootstrap + 1 codex doc + 1 short CLAUDE.md update. **Saved cost**: ~150 lines of
  pre-commit-discipline rules deleted; ~daily foot-gun fires across agent fleet stop.
- **Active plan**: NEW `plans/active/per_agent_worktrees_2026_05_<date>.md` — pre-cutover-or-immediate (this is the
  agent-flow-tightening operator asked for).

### D4 — Plans-Run-To-Actual-Completion as machine-checkable

- **Code state**: HARD RULE codified in CLAUDE.md 2026-05-08. Operator currently runs the verification recipe manually
  (gcloud / aws / parquet / event-stream queries per Tab/agent).
- **Recommendation**: **ADD (P2, post-cutover)**. Each plan section ships a `done.yaml` listing concrete probes
  (commands + expected outputs); plan-validator script reads the yaml + runs probes + flips checkboxes if all green.
  Removes "operator manually verifies operational state" effort.
- **Cost**: ~3-4 AI-days. **Active plan**: NEW post-cutover.

### D5 — Sub-agent rule injection — full-paste vs on-demand

- **Code state**: `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` is a symlink to `cursor-configs/CLAUDE.md` (~1500
  lines). Every Task spawn pastes the full content as preamble — every spawn pays ~30k token cost.
- **Citadel-benchmark gap**: under operator-decided parallel-agent SSOT, sub-agent fan-out is the default workflow; the
  30k-token-per-spawn cost compounds heavily. A core 200-line "must-read" + on-demand-fetched detail surface would
  amortise.
- **Recommendation**: **LIFT (P2)**. NEW `cursor-configs/CLAUDE_CORE.md` (~200 lines: the absolute non-negotiables —
  pre-commit check, conditional push, plan-flip cadence, `docs(plans):` prefix, no-secrets, basedpyright-not-pyright,
  uv-pip-install). Sub-agent preamble pastes CORE; sub-agent fetches detail sections on-demand via Read tool when task
  touches a specific area (e.g. "honest-coverage" → Read CLAUDE.md § honest-coverage). Existing CLAUDE.md becomes the
  detail reference; SUB_AGENT_MANDATORY_RULES symlink swaps to CORE.
- **Cost**: ~1-2 AI-days. **Saved cost**: ~25k tokens/spawn × ~50 spawns/cycle = 1.25M tokens saved. **Active plan**:
  extend the spawned audit plan or NEW `plans/active/sub_agent_rule_injection_lift_<date>.md`.

### D6 — Workspace-wide QG sweeps as bulk vs continuous integration

- **Code state**: operator currently running ad-hoc QG sweeps to clean up `ruff N811` / `basedpyright reportUnknown`
  across the workspace.
- **Recommendation**: **ALIGN — workspace-root pre-commit + zero baseline + fail-loud ON FIRST ERROR is the existing
  SSOT** per CLAUDE.md "Plan: Zero Baseline Typecheck — 2026-03-10 (DONE)". The cleanup backlog forms because the
  per-repo baseline files allow regression. Tightening: workspace-root QG sweep that fails CI on first error per repo
  (already partly there). ~0 new code; tighten existing config.
- **Active plan**: track in spawned audit plan Phase 1 audit row.

## Block E — Missing alpha-multiplying primitives

(This block partially folds with C — keeping for completeness; cross-references E↔C.)

- **E1 (Kelly / capacity / portfolio construction)** — folds with C3. Code mostly EXISTS in
  `strategy_service/portfolio_allocator/`; gap is documentation parity + explicit Kelly + capacity curves.
- **E2 (Regime detection as a service)** — folds with C5. Partially exists per-asset-group; gap is unified
  cross-asset-group `Regime` primitive in UAC.
- **E3 (Alpha attribution stack)** — folds with C2. Service exists but realised-PnL only; gap is the 5 research-grade
  primitives (signal/counterfactual/regime-Sharpe/capacity/factor).
- **E4 (Researcher-grade backtest indistinguishable from production)** — folds with C1 + B4. Principle is sound ("live =
  batch"); needs golden-path notebook surface to expose.
- **E5 (Counterfactual / shadow-trading mode)** — partial via paper-trade smoke. Gap: per-strategy "shadow mode"
  declared in UAC + execution-service routes shadow signals to a logger, not a venue. **NEW primitive**.
- **E6 (Experimentation / feature-importance discipline)** — gap entirely. Per-archetype: documented set of features
  tested / accepted / rejected with rationale + statistical evidence. Today implicit-knowledge-only. NEW
  research-archive surface (notebook decision-doc per feature).
- **E7 (Capacity-aware capital allocator)** — folds with C3 + E1.

**Net E recommendations (not duplicated above)**:

- **E5 ADD (post-cutover)**: shadow-trading mode primitive — `ExecutionMode.SHADOW` + execution-service route. ~2-3
  AI-days.
- **E6 ADD (post-cutover)**: per-archetype feature-decision-archive — researcher notebook + `decisions.md` per feature.
  Mostly process + light tooling. ~2 AI-days for tooling.

## Block F — Non-negotiable primitives (KEEP)

These are KEEPS regardless of consolidation. The Block A1 monorepo move + Block B1/B5 type-level lifts make them
stronger, not weaker.

| F-item                                 | Why non-negotiable                                                                                    |
| -------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| F1 `live = batch` principle            | Backtesting fidelity; the seam is unavoidable but the 99% shared code is non-negotiable               |
| F2 Honest-absence semantics (4-state)  | Every Citadel-grade system needs this; only the ENFORCEMENT mechanism (B1 ADT) is up for redesign     |
| F3 Asset-group-axis vocabulary         | Clean dimension for sharding + isolation; survives even if scope contracts to crypto-only pre-cutover |
| F4 Shard-level failure isolation       | Non-negotiable for multi-source backfills (cefi/defi/sports especially)                               |
| F5 UAC as canonical schema SSOT        | Non-negotiable; alternative is per-service drift                                                      |
| F6 Event stream + lifecycle taxonomy   | Non-negotiable for observability                                                                      |
| F7 unified-events-interface UI surface | Non-negotiable for production observability; SSH-tailing logs is dev-only                             |

**No active plan updates needed for Block F** — all F items are KEEPS reinforced by other audit recommendations.

## Disposition table — what landed where

| Block | Sub-q | Recommendation                                        | Active plan / artefact                                                               | Timing              |
| ----- | ----- | ----------------------------------------------------- | ------------------------------------------------------------------------------------ | ------------------- |
| C     | C1    | ADD researcher golden-path doc + notebook             | NEW `researcher_experience_golden_path_<date>.md` OR fold into spawned monorepo plan | Post-cutover        |
| C     | C2    | ADD alpha-attribution stack (research-grade)          | NEW `alpha_attribution_stack_<date>.md`                                              | Post-cutover        |
| C     | C3    | KEEP + LIFT to doc parity (code exists)               | EXTEND `/codex/03-services/portfolio-allocator.md` + spawned audit plan Phase 1      | Pre-cutover (cheap) |
| C     | C4    | ALIGN — fold into C1 golden path                      | (same as C1)                                                                         | Post-cutover        |
| C     | C5    | LIFT regime to unified UAC primitive                  | NEW `regime_unified_primitive_<date>.md`                                             | Post-cutover        |
| D     | D1    | CONSOLIDATE — pick one job runtime (AWS Batch likely) | NEW `job_runtime_migration_<date>.md`                                                | Post-cutover        |
| D     | D2    | EVALUATE only — homemade protocol works               | NONE NEEDED                                                                          | Post-cutover P2     |
| D     | D3    | ADD per-agent worktrees                               | NEW `per_agent_worktrees_<date>.md`                                                  | **PRE-cutover**     |
| D     | D4    | ADD machine-checkable plans (`done.yaml` + validator) | NEW post-cutover                                                                     | Post-cutover P2     |
| D     | D5    | LIFT sub-agent rule injection to CORE + on-demand     | NEW `sub_agent_rule_injection_lift_<date>.md` OR spawned audit plan                  | Pre-cutover (cheap) |
| D     | D6    | ALIGN — tighten existing zero-baseline                | spawned audit plan Phase 1                                                           | Pre-cutover         |
| E     | E5    | ADD shadow-trading mode primitive                     | NEW post-cutover                                                                     | Post-cutover        |
| E     | E6    | ADD per-archetype feature-decision archive            | NEW post-cutover                                                                     | Post-cutover        |
| F     | all   | KEEP all 7 — reinforced by B1/B5 lifts                | NONE NEEDED                                                                          | n/a                 |

## Question doc closure criteria

Per the operator directive ("do it all till we don't need the question doc anymore"), the audit doc lifecycle Step 5
closes when:

1. ✅ All 6 audit blocks (A/B/C/D/E/F) have findings + recommendations + named active plans where applicable.
2. ✅ Recommendations are migrated to issue docs in `plans/active/issues/`:
   - `codex_vs_citadel_block_b_audit_findings_2026_05_10.md` — A2 + B1-B5
   - `codex_vs_citadel_blocks_cdef_audit_findings_2026_05_10.md` (this doc) — C1-C5 + D1-D6 + E1-E7 + F1-F7
3. ✅ Spawned audit plan `plans/active/codex_vs_citadel_infrastructure_audit_2026_05_10.md` consumes the issue docs in
   its Phase 1 (per-area audit) instead of running 12 sub-agents from scratch.
4. ⏳ Per-recommendation active plan updates land where dispositions point:
   - B5 → extend `available_at_lookahead_bias_completion_2026_05_08.md` with post-cutover Phase
   - B2 → extend `manifest_evolution_master_2026_05_08.md` with cross-cutting registry Wave
   - D3 → NEW `per_agent_worktrees_<date>.md` (pre-cutover)
   - C1/C2/C5/D1/D5 → NEW post-cutover plans as named in disposition

The retired question doc is now redundant — every answer lives in this issue doc + the sibling Block B issue doc + the
spawned audit plan + the named active plans in the disposition table.

## Composes with

- `codex_vs_citadel_block_b_audit_findings_2026_05_10.md` (sibling) — Block A2 + B fills.
- `codex_vs_citadel_infrastructure_audit_2026_05_10.md` (parent spawned plan) — execution surface for the pre-cutover +
  immediate items.
- `available_at_lookahead_bias_completion_2026_05_08.md` (B5 extension target).
- `manifest_evolution_master_2026_05_08.md` (B2 + B3 extension targets).
- `master_to_live_defi_2026_05_23.md` Group F/G items — many of these audit recs feed those service-readiness rows.
