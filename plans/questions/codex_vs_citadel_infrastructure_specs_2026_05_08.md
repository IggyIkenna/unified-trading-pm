---
name: codex-vs-citadel-infrastructure-specs
overview:
  Fresh-eyes audit — what would an alpha-and-error-free-optimised non-HFT combination trading system look like, and
  where does the current codex / repo / runtime architecture diverge from that ideal?
type: question
status: plan-spawned
created: 2026-05-08
plan_spawned: 2026-05-10
operator: ikenna
locked_by: live-defi-rollout
locked_since: 2026-05-08
spawned_plan: plans/active/codex_vs_citadel_infrastructure_audit_2026_05_10.md
related_codex:
  - codex/00-SSOT-INDEX.md
  - codex/04-architecture/separation-of-concerns.md
  - codex/04-architecture/tier-and-import-architecture.md
  - codex/04-architecture/batch-live-architecture.md
  - codex/04-architecture/runtime-deployment-topology.md
  - codex/02-data/availability-manifest-and-data-status.md
  - codex/02-data/honest-absence-downstream-handling.md
  - codex/05-infrastructure/live-pipeline-architecture.md
  - codex/09-strategy/architecture-v2/README.md
related_plans:
  - plans/active/master_to_live_defi_2026_05_23.md
  - plans/epics/live_defi_rollout.epic.md
  - plans/questions/batch_live_design_symmetry_2026_05_08.md
  - plans/questions/topology_features_strategy_ml_execution_2026_05_08.md
  - plans/questions/paper_vs_live_workflow_maturity_2026_05_08.md
---

# Codex vs Citadel infrastructure specs — fresh-eyes audit

## Intent

The system has accumulated ~150 codex SSOT docs across 9 sub-trees, **35 git repos in the workspace today** (the codex
SSOT-INDEX + CLAUDE.md still cite "65 repos" / "60+ repos" / "all 65 repos" from pre-merger plans — URDI / UTEI / others
were merged; the **codex misstates its own repo count by ~2x**, which is itself the cleanest data point for the broader
codex-staleness critique in Block A2 below), ~1500 lines of `CLAUDE.md` workspace rules, and a multi-month backlog of
"Citadel-grade" plans (CI/CD hardening, manifest v5 honest-coverage, writegate, shard-granularity SSOT propagation,
cloud-agnostic migration, alerting taxonomy, etc.). Each rule + SSOT is individually defensible — every one of them was
codified in response to a real incident. But the cumulative architecture is now an elaborate scaffold around two
archetypes (`carry_staked_basis` + `leveraged_funding_arb`) that have not yet generated a single dollar of live PnL.

The operator's question is the **opportunity-cost** question: if we were building the **best non-HFT combination trading
system in the world** from a clean slate today — optimised for **alpha velocity + error-free correctness** (in that
order), with the same 2026-05-23 live-DeFi cutover and the same 2-3-person team — what would be different about the
codex architecture, the repo split, the data model, the research workflow, the operational mechanics, and the governance
overhead? Which parts of the current system would survive on merit, which are accumulated cruft from "institutional
vocabulary" that don't earn their cost, and which are missing entirely (alpha-attribution discipline, researcher
leverage, capacity-aware portfolio construction, regime adaptation)?

This doc is NOT a "rip and replace" proposal — the system as built is impressive and most of it earns its keep. The goal
is to surface, audit, and decide-per-area which parts to **keep / lift / consolidate / delete / add**, against an
explicit "ideal Citadel-grade non-HFT combination system" benchmark that we agree on first.

A real Citadel-grade non-HFT trading shop is characterized by ~6 things — and we should write them down explicitly so
the audit has a target: **(a)** ruthless researcher leverage (idea → backtest → walk-forward → paper → live in days, not
weeks, with zero leakage and reproducible results); **(b)** institutional risk + portfolio construction (Kelly /
fractional Kelly per signal, correlation-aware capacity curves, regime-adaptive sizing, capital-efficient hedging);
**(c)** alpha attribution at every layer (per-signal / per-feature / per-regime / per-venue PnL decomposition, not just
"strategy hit a number"); **(d)** error-free pipeline correctness via type-system enforcement + executable specs + small
surface area, not via prose SSOTs + reconcilers; **(e)** operational excellence as a property of the framework, not a
discipline imposed on operators (event emission as a side-effect of the runtime, not an opt-in convention); **(f)**
focus — one strategy archetype shipped end-to-end before adding the second, one cloud before two, one asset_group at a
time. Most institutional shops fail at (a) and (c); they over-invest in (e) the way we have. The audit needs to test
each area against this benchmark.

## Question

### Operator directives (received during this question doc's drafting — pinned)

- **2026-05-09 ikenna**: _"agent paralel flow is the ssot we will do this for forseeable future needs to ebe tight"_ —
  multi-parallel-agent flow IS the workspace SSOT. Do NOT propose removing it. **Do** propose tightening its foot-guns.
  This re-shapes Block A3 (the audit re-frames around tightening, not replacing) and **PROMOTES D3 (per-agent
  worktrees)** as the structural fix that makes the SSOT tight.
- **2026-05-09 ikenna**: _"UTS needs to be a commoon soot codbebas with hooks to do eevrythihg with mim duploiacte
  thread but full flexibility"_ — the target architecture IS a **single common-SSOT codebase with hooks for
  extensibility**, minimum duplicate code paths, full flexibility via plugin / extension points. This is a DIRECTLY
  DECIDED answer to Block A1 (the recommendation is now "monorepo + plugin hooks", not "audit whether to consolidate").
  The plan-extraction work for A1 becomes "design + execute the consolidation + hook architecture" not "decide whether
  to consolidate."
- **2026-05-09 ikenna**: _"the rest of your question you can answer with the code understanding... plug and gaps with
  active plan updates"_ — fill the audit findings myself based on code understanding (don't gate on operator answers for
  the remaining blocks); when gaps surface, raise them as updates against active plans rather than as new question doc
  cycles.

### Block A — Repo + codebase shape

A1. **Repo split at 35 — earning its cost?** 35 git repos in the workspace today (27 active + 8 archived after the
features-\* consolidation 2026-05-08; ground truth = `workspace-manifest.json` `repositories` keys). The split was
justified historically by parallel-CI throughput + per-domain ownership boundaries, but with current team size the
symptoms remain visible: dirty-deps quickmerge bans, force-sync danger, version-skew risk, per-repo workflow template
rollouts, "where does X live?" cognitive load, QG bypass loopholes per repo, dual SSOTs from canonical/external-source
splits, multi-agent shared-tree foot-guns (the 4 documented in CLAUDE.md). Are 27 active repos earning their cost today?
Concretely: which 5-10 logical packages would survive in a clean rewrite, and what's the migration cost vs benefit?

> **DECIDED 2026-05-09 (operator directive)**: target shape is **single common-SSOT codebase + hooks for extensibility,
> minimum duplicate threads, full flexibility**. The audit work for A1 is no longer "should we consolidate?" — it's
> **"design + execute the monorepo + hook architecture"**. Concrete shape (to be refined in the spawned plan):
>
> - **One `unified-trading-system` repo** (or 2-3 max) with internal sub-packages along the existing T0/T1/T2/T3 tier
>   model (`core/contracts/`, `core/library/`, `interfaces/market/`, `interfaces/execution/`, `services/strategy/`,
>   `services/features/`, `services/execution/`, etc.). Same dependency-DAG, vastly less coordination overhead.
> - **Hooks pattern** for per-domain / per-archetype / per-venue extensibility — adapter registries (already exist in
>   UAC `external/<source>/`), strategy-archetype registries (already exist in UAC `registry/`), feature-family
>   registries (already exist in features-service after consolidation), execution-mode registries (already exist in
>   `ManualExecutionMode`/`ServiceEmissionPolicy`). Lift these into a uniform "extension point" pattern so adding a new
>   venue / archetype / feature is a single registry entry + a single adapter file, not a new repo.
> - **Migration sequence** (to be detailed in spawned plan): (1) UAC + UTL + UCI + UEI collapse into
>   `unified-trading-core/` sub-package, (2) all `interfaces/*` (market, execution, sports, prediction adapters)
>   collapse into `unified-trading-interfaces/` sub-package, (3) all `*_service` repos collapse into
>   `unified-trading-services/` with sub-packages per service, (4) UI repos consolidate via the same pattern. End-state:
>   ~3-5 logical packages instead of 27 active repos.
> - **Coordination win**: removes dirty-deps quickmerge bans, force-sync danger, version-skew risk, per-repo workflow
>   template rollouts, the per-repo cursor-rules / CLAUDE.md symlinks, the per-repo QG-bypass-audit YAMLs.
> - **Open audit questions for plan extraction**: timing vs May-23 cutover (consolidation IS the cutover-gating work if
>   done pre-May-23, OR a post-cutover refactor); incremental vs big-bang migration; CI/CD shape under monorepo (single
>   QG pipeline vs per-package); hooks-pattern formalization (which existing registries are the canonical extension
>   surface vs which need lifting).

A2. **Codex inflation + codex staleness** — ~150 docs across 9 sub-trees + ~1500 lines of `CLAUDE.md` rules + per-repo
`CLAUDE.md` symlinks + `SUB_AGENT_MANDATORY_RULES.md` aliasing the full content. Each new agent (sub-agent or fresh
Claude Code session) burns ~30k tokens reading rules before doing anything substantive. **And the codex itself drifts**
— the SSOT-INDEX still cites "65 repos" / "60+ repos" in 4+ places against a real count of 35; CLAUDE.md says "60+
repos"; "all 65 repos" appears in archived-plan one-liners that survive in the index. If the codex can't keep its own
repo count current despite being the SSOT for repo state, what other facts in it are stale? Which docs are read
repeatedly + earn their cost (probably 00-SSOT-INDEX, batch-live-architecture, separation-of-concerns, master plan,
asset-group-bucket-layouts, honest-absence-downstream-handling) vs which are written-once / read-rarely artefacts that
exist for governance theatre? Is a "tiered codex" the right shape — a 200-line core SSOT every agent reads + a deeper
detailed reference accessed on-demand, vs the current "everything is mandatory" flat surface? **Is there a process for
codex re-derivation from authoritative state** (workspace-manifest.json owns repo count → codex auto-pulls from it
instead of hard-coding)?

A3. **CLAUDE.md as procedural rule book under the parallel-agent SSOT — what tightens further?** The file has more lines
about HOW to commit (pre-commit check, foot-guns #1-#4, prek auto-revert race, conditional push, plan-flip-as-you-ship,
pathspec commit form) than about WHAT to build. **Operator directive 2026-05-09**: parallel-agent flow IS the workspace
SSOT for the foreseeable future + needs to be tight. So the audit re-frames around tightening, not removing. Open
questions: which procedural rules earn their cost (the pre-commit-check + pathspec-commit-form + EOD-scoreboard
discipline catch real foot-gun fires daily — KEEP); which rules are workarounds for the underlying shared-tree race that
**D3 below would eliminate structurally** (foot-gun #1 / #2 / #3 / #4 all stem from the same shared-`.git/` +
shared-working-tree shape); which rules drift between text + behaviour as agents accumulate; which rules a fresh agent
ACTUALLY reads vs which exist as documentation-only governance theatre? If a fresh operator sat down today, which
CLAUDE.md sections would they need to follow, and which would be artefacts of accumulated parallelism? **The sibling
question doc `paper_vs_live_workflow_maturity_2026_05_08.md` overlaps here** — that doc focuses on the operational
paper/live workflow; this question is the upstream "is the agent-coordination shape itself earning its cost?"

A4. **Repo organisation by "tier + interface + service" vs "by domain bounded context"** — current shape is library-
centric (T0 contracts → T1 utility → T2 interfaces → T3 services), which is a clean dependency-DAG but cuts across
domain boundaries (a sports feature lives across UAC + URDI + UTL + features-sports-service + ... in 5 repos). Domain-
driven shape would group by (asset_group, capability) — `crypto-spot/`, `crypto-perp/`, `defi-onchain/`, `sports/`,
`prediction/` each containing all their adapters + features + strategies + tests in one tree. Which split serves alpha
velocity better given the team size + the actual coupling pattern (every cross-cutting refactor today touches 5-10
repos)?

### Block B — Data + correctness model

B1. **Honest-coverage taxonomy as runtime convention vs as type system** — the 4-state capture taxonomy (`captured` /
`empty_confirmed` / `attempted_failed` / `expected_unattempted`) + writegate + cluster validation + LookaheadBiasError

- NaN-ratio gate + reconcilers + phantom-audits + per-VM shard isolation + concurrency CAS is a giant correctness
  scaffold enforced at runtime via a UTL helper + downstream reconcilers + workspace-wide rules. A type-safe shape would
  model adapter output as a discriminated union ADT
  (`AdapterResult = Captured | EmptyConfirmed | Failed | ExpectedUnattempted`); the manifest writer's signature would
  force exhaustive case handling; you literally couldn't record `captured` for an empty parquet because the constructor
  wouldn't accept it. Today the whole class of bugs (1440 NaN OHLC bars, partial-bundle, blank-reason silent fallback,
  etc.) is enforced by reading + writing rules; with an ADT they'd be unrepresentable. Is the data integrity stack the
  right _shape_, or is it doing N reconcilers' worth of work that a type-discriminated-union would do for free?

B2. **`per-source colocation` vs `per-(asset_group, data_type) colocation`** — UAC currently has one flat `external/`
directory per source (~80 dirs), each with `schemas.py` + `normalize.py`. The cross-cutting question "what data_types
does Bybit emit for perp?" is answered by reading `external/bybit/`; the sibling cross-cutting question "for the
`OHLCV_15M` data_type, which sources cover which (venue, instrument_type, day) combinations?" is answered by reading the
`MTDS_DATA_SOURCE_COVERAGE_MATRIX` doc + chasing per-source colocation. The matrix is the SSOT; per-source colocation is
the implementation detail. Would a `per-data_type` shape (one dir per data_type, with sources as sub-modules) make the
cross-cutting question first-class + reduce the matrix-doc + reduce the every-data-type phantom-audit drift surface?

B3. **Manifest as side-effect-of-write vs manifest as pre-flight planner + post-flight verifier** — today the manifest
is written by adapters (record_captured / empty / failed / expected_unattempted) as a side-effect of the actual data
write, then audited by reconcilers + phantom-audits. A cleaner shape: pre-flight enumerator says "for date D, here are
the (shard_key, source) tuples expected" → adapter consumes the plan, writes data + reports per-shard status →
post-flight verifier compares plan vs actual, surfaces drift. Today ~70% of the writegate plan is reconciling these two
roles. Is "manifest = write-time side-effect" the wrong shape; should it be "manifest = pre-flight plan + post-flight
verification"? **Composes with sibling question `backfill_manifest_schema_freeze_gate_2026_05_08.md`** — that doc is
about freezing the current schema; this question is about whether the underlying SSOT model is shaped right.

B4. **`live = batch` principle is correct, implementation is brittle** — the principle is repeated across multiple codex
docs because consumers keep reintroducing bespoke shapes (live-only data*types, separate field sets, distinct
`available_at` derivation). Type-level enforcement: a single `Pipeline[ModeT]` runtime where `ModeT in {Batch, Live}` is
a generic parameter; the only mode-conditional code is a 4-seam `Source[ModeT]` / `Output[ModeT]` injector; every other
line is mode-agnostic by construction (impossible to write `if mode == "live": ...`). Today the principle is prose;
better would be a base class that \_can't* be written wrong. What's the cost of refactoring strategy-service /
features-service / execution-service to that shape, and what's the saved governance + reconciler-writing time over 6-12
months? **Composes with sibling question `batch_live_design_symmetry_2026_05_08.md`** — that doc audits the existing
wire-up surface; this question asks whether the principle should be language-enforced rather than prose-asserted.

B5. **`available_at` as write-time stamp vs as schema-level invariant** — every parquet has an `available_at` column
that must be present + correctly stamped per source-specific rules; missing or wrong stamp triggers `LookaheadBiasError`
at compute. Better: the schema TYPE for any tick-level source is parameterised by `available_at_rule: AvailabilityRule`;
the row constructor takes `available_at` as a required field; the rule itself lives in UAC as a typed primitive (e.g.
`AvailabilityRule.fixture_event_time(60_min_before_kickoff)` returns a callable the writer calls). Today the rules live
in prose docs + per-source helpers + a runtime check; tomorrow they could be type-level + impossible to forget.

### Block C — Researcher experience + alpha workflow

C1. **No first-class "research → paper → live" flow for the alpha researcher** — DART exists but appears to be a UI
wrapper. The end-to-end "I have an idea, here's a notebook, hit deploy" path doesn't exist as a single workflow. The
researcher today must understand: ServiceEmissionPolicy, manifest writers, write-gates, shard-granularity SSOT, hive
partitions, batch=live seams, UAC schema placement, instrument lifecycle hot-reload, the 5 axes of operational mode
(env*canon.py), the ML experiment lifecycle, the strategy registry-v2 axes, restriction-policy, archetype declaration in
UAC, etc. — before they can backtest a new signal. Citadel-grade non-HFT shops invest heavily in **researcher leverage**
(one researcher should ship 5-10 ideas/month; today the friction predicts <1/month). What's the researcher-experience
equivalent of `dev-tiers.sh --tier 0`? What's the "I'm a researcher with a hypothesis, here's the golden path" doc that
\_doesn't exist today*?

C2. **No alpha attribution stack at the architecture level** — `pnl-attribution` is in scope of the client-reporting
question doc as a P&L _reporting_ concern. The deeper alpha-attribution question is missing entirely:

- per-signal PnL decomposition (which feature drove which trade?)
- counterfactual PnL ("what if we hadn't traded this hour?")
- regime-aware Sharpe (per-market-state performance, with regime detection as a first-class output)
- capacity curves (how does PnL scale with NAV — does the strategy decay above $X NAV?)
- factor exposures (is the carry archetype just a beta to ETH-staking-yield, or is there idiosyncratic alpha?)

These aren't in the codex. They're the alpha-research primitives that turn "the strategy made $X" into "feature F at
regime R drove $Y at NAV up to $Z capacity." Without them, scaling an archetype + adding new ones + retiring decayed
ones is guesswork. Where would these primitives live (UAC schemas + features-service module + strategy-service consumer

- research notebook surface), and what's the dependency on shipping them before May-23?

C3. **Portfolio construction + correlation-aware sizing** — the system as architected treats archetypes as independent
silos; each strategy gets a capital allocation + risk limits, no first-class concept of correlation matrix across
archetypes / regime-conditional sizing / fractional Kelly under uncertainty. For a non-HFT _combination_ system, the
alpha is in the COMBINATION — uncorrelated archetypes pooled with right sizing have higher Sharpe than any one archetype
solo. `portfolio-allocator.md` exists in `03-services/` but appears thin. What would a first-class portfolio
construction layer look like (cross-archetype correlation estimator → fractional Kelly per signal → regime-conditional
allocator → capital flow to strategy-service)?

C4. **ML lifecycle is documented but not integrated into a single research loop** — `ml-experiment-lifecycle.md` +
`features-service-architecture.md` + `ml/` sub-package in UTL exist independently. The walk-forward backtest + train-
predict-evaluate cycle + online retraining + model promotion gate + drift monitoring + retirement isn't a single
end-to-end workflow the researcher can run. What's the "MLOps for alpha" workflow, and how much of it is missing vs
already-built-but-undiscoverable?

C5. **No regime-adaptation primitive at the framework level** — every Citadel-grade non-HFT system has some notion of
"market regime" (vol regime, correlation regime, liquidity regime, macro regime) and conditions strategy behavior on it.
Today the system has features per-asset_group but no first-class regime-detection layer. Should there be a
`features-regime-service` + a `Regime` type in UAC + per-strategy regime-conditional allocations?

### Block D — Operational + governance overhead

D1. **"No fire-and-forget VM launches" is treating the symptom** — the rule + protocol catches stalled-VM bugs by
requiring event-stream verification, which is a discipline imposed on every launcher author. The cause is using stateful
VMs as if they were stateless workers. A queue + workers framework (Cloud Run jobs / AWS Batch / ECS Fargate Spot /
Modal / Beam / Ray Tasks) emits per-task lifecycle events as a property of the framework — no opt-in needed, no silent
failure mode possible. The cost of porting backfills from `gcloud compute instances create` launchers to a job runtime
is days; the saved discipline + saved silent-failure incidents is permanent. Should backfills move to a job-runtime, and
which one?

D2. **"Per-VM shard isolation + concurrency CAS + manifest consolidator" is a homemade distributed-write protocol** —
every multi-worker backfill needs `MANIFEST_PER_VM_SHARDS=true` + unique `VM_NAME` + the consolidator daemon merging
per-VM shards into the canonical manifest. This is a hand-rolled distributed write coordinator. Off-the-shelf options:
Iceberg / Delta Lake / Hudi (multi-writer ACID on object storage); a real database (Postgres / DuckDB-as-coordinator)
for the manifest with regular ACID semantics; a workflow engine (Temporal / Airflow / Prefect) that owns the per-task
coordination. Which is the right shape, and what's the cost-benefit vs the current homemade scheme?

D3. **Plan-flip-as-you-ship + shared-tree foot-guns + pre-commit checks + auto-revert race** — the entire
`Commit + Push + Flip Plan Checkboxes` HARD RULE plus 4 documented foot-guns (#1 foreign work bundled in, #2 path-arg
masking, #3 concurrent-agent reset, #4 prek auto-restore race) exists because multiple agents share `.git/` + working
tree on one operator's machine. Per-agent worktrees (`git worktree add`) would isolate the index entirely; each agent
commits to their own worktree, no shared-staging collision possible. Cost: ~20 lines of bootstrap; benefit: removes 4
foot-guns

- ~150 lines of pre-commit-discipline rules. Why hasn't this happened? **(Live evidence: the very session that drafted
  this question doc lost an earlier version of this file when a parallel agent overwrote `plans/questions/` with their
  own untracked WIP — the 4 foot-guns continue to fire in real-time.)**

D4. **"Plans Run To Actual Completion" + EOD-audit + scoreboard + continuous-verification-column** is governance
catching code-shipped-but-not-operationally-shipped drift — a class of bug that could be eliminated structurally by
defining "done" as "the operation ran + an automated check confirmed the expected on-disk / on-cloud state." Could plans
be machine-checkable? A `done.yaml` per plan section listing concrete probes (gcloud / aws / parquet / event- stream
queries) that pass = green checkbox. The plan ITSELF becomes the verifier instead of relying on agents to run manual
probes per the EOD-audit recipe.

D5. **Sub-agent rule injection** — `SUB_AGENT_MANDATORY_RULES.md` is a symlink to CLAUDE.md (codified 2026-05-08) so
sub-agents inherit the full rule surface. Every Task spawn pastes the full rules into the prompt — every spawn pays the
30k-token rule tax. Is a smaller "core protocol" + on-demand rule fetch (sub-agent reads only the rule section relevant
to its task) the right shape, or does the full-paste approach earn its token cost?

D6. **Workspace-wide QG sweeps as bulk jobs vs as continuous integration** — the QG sweep Ikenna is currently running to
clean up `ruff N811` / `basedpyright reportUnknown` etc. across 35 repos is a manual periodic effort. A
continuously-clean codebase (workspace-root pre-commit + zero baseline + fail-loud on first error) doesn't accumulate
the bulk-cleanup debt. What changed in the workspace's QG hygiene over time that allowed the multi-repo cleanup backlog
to form, and what process change prevents the next cycle?

### Block E — What's missing entirely (alpha-multiplying)

E1. **First-class capacity / Kelly / portfolio construction layer** (sibling to C3 but distinct: this is about whether
the _primitives_ exist, not whether the workflow uses them).

E2. **Regime detection as a service** (sibling to C5).

E3. **Alpha attribution stack** (sibling to C2).

E4. **Researcher-grade backtesting environment** that's literally indistinguishable from production (per the batch=live
principle taken to its logical end — researcher writes a strategy in a notebook, hits "deploy", same code runs paper →
live).

E5. **Counterfactual / shadow-trading mode** — runs the strategy alongside live but doesn't actually execute, logs
"would-have-fired" signals + "would-have-PnL" → enables A/B testing of strategy variants in production without capital
risk. Sibling to the batch=live + paper-trade smoke surfaces but operationally distinct.

E6. **Experimentation / feature-importance discipline** — for each archetype, what's the documented set of features
tested, accepted, rejected, with what rationale + statistical evidence? Today this is implicit-knowledge-only. A
research-grade archive (notebooks + decision-doc per feature) would compound institutional knowledge.

E7. **Capacity-aware capital allocator** — given current NAV + per-archetype capacity curves + correlation matrix, what
allocation maximizes risk-adjusted return? Today capital flows are operator-driven; the system has no
"recommend-allocation" output.

### Block F — What probably stays (the non-negotiable alpha + correctness primitives)

F1. **`live = batch` principle** — the right idea. Implementation needs hardening (B4), but the principle is
non-negotiable for backtesting fidelity.

F2. **Honest-absence semantics** — every Citadel-grade system distinguishes "we tried + got nothing" from "we didn't
try" from "we're not allowed to have anything here." The 4-state taxonomy is correct; only the enforcement mechanism (B1
ADT vs runtime convention) is up for redesign.

F3. **Asset-group-axis vocabulary + 5-asset-group future scope** — the _vocabulary_ survives even if the _scope_
contracts (E.g. defer sports + prediction; build crypto + DeFi end-to-end first; fold them in later when proven). The
asset_group axis is a clean dimension for sharding + isolation.

F4. **Shard-level failure isolation** — non-negotiable for multi-source backfills.

F5. **UAC as the canonical schema SSOT** — non-negotiable; the alternative is per-service drift.

F6. **Event stream + lifecycle event taxonomy** — non-negotiable for observability.

F7. **The `unified-events-interface` UI surface for production observability** — non-negotiable; SSH-tailing logs is a
dev crutch, the event stream is the production answer.

## What "answered" looks like

- A canonical plan exists (probably `plans/active/codex_consolidation_<date>.md` or folded into the May-23 cutover
  master) that enumerates per-area decisions: KEEP / LIFT / CONSOLIDATE / DELETE / ADD against each block above, with a
  prioritisation against the May-23 cutover (in-scope for cutover vs explicit post-cutover deferral with named successor
  plan per the `Temporary state must have a named successor plan` HARD RULE).
- Codex SSOT(s) describe: the **target Citadel-grade non-HFT combination architecture** (a single doc that's the
  benchmark we're auditing against), the **researcher-experience golden path** (notebook → paper → live with no
  leakage), the **alpha attribution primitives** (per-signal / per-feature / per-regime PnL decomposition), the
  **portfolio construction layer** (Kelly / capacity / correlation), the **regime detection layer**.
- A real-data run has shipped: at least ONE archetype (`carry_staked_basis`) has the alpha-attribution stack wired
  end-to-end; researcher can answer "which feature drove the PnL last week?" from a single dashboard.
- The repo split question (A1) has a decided answer: either an explicit "35 repos earn their cost — here's the
  measurement" OR a consolidation plan (number of repos + migration order + cost / benefit estimate).
- **Codex re-derivation gate (A2)**: workspace-manifest.json is the SSOT for repo count + identity; the codex
  SSOT-INDEX + CLAUDE.md re-derive their counts from that file (no hard-coded "65 repos" / "60+ repos" strings allowed
  to survive). A QG step asserts no stale-count strings remain.
- The "fire-and-forget VM launches" governance rule is either (a) replaced by a job-runtime that makes the rule
  unnecessary OR (b) explicitly retained with documented cost-benefit vs the alternative.
- Per-agent worktrees decision shipped (D3) — either rolled out as the workspace default OR explicitly rejected with
  documented reason.
- Service-readiness checklist: the audit results in concrete checklist additions (or modifications) to the master plan's
  Group A-G items, OR explicit "this is post-cutover" deferrals with named successor plans.

## Audit findings (to be filled by audit pass)

The audit fills one sub-question at a time. Each entry follows this shape:

- **Code state**: <what exists in repos today, file:line citations across UAC + UTL + UCI + UEI + service repos>.
- **Codex state**: <which codex docs cover the area today, drift vs current code, gaps, governance overhead measure
  (lines of doc + cross-references + rule rollout cost)>.
- **Operational state**: <how often does the area surface as a foot-gun / incident / blocker; has the rule earned its
  cost in caught bugs vs imposed overhead>.
- **Alpha-relevance**: <does this area have ANY direct path to alpha generation (yes / indirect / no), and if no, what
  fraction of total team hours has it consumed in the last 90 days>.
- **Citadel-benchmark gap**: <what's the gap between current shape + the benchmark "ideal Citadel-grade non-HFT
  combination system" shape>.
- **KEEP / LIFT / CONSOLIDATE / DELETE / ADD** recommendation with rationale.

The audit MUST resist the temptation to KEEP everything by default. Every SSOT + every rule + every repo should be asked
"if you didn't exist, what specifically would break, and is that breakage worse than the cost you impose?"

### A2 — Codex inflation + codex staleness (seeded 2026-05-08)

- **Code state**: workspace has **35 git repos** (counted via `for d in */; do [ -d "$d/.git" ] && echo "$d"; done`).
  `unified-trading-pm/workspace-manifest.json` is the SSOT for the canonical repo registry; that file IS internally
  consistent. The drift is purely in human-readable codex / CLAUDE.md prose.

- **Codex state**: **stale repo-count strings appear in 12+ canonical-doc lines** across the codex + CLAUDE.md, all
  citing "60+" / "62" / "65" / "69" repos against a real count of 35. Concrete inventory:
  - `codex/00-SSOT-INDEX.md` lines 84, 108, 110, 112, 124 — "65 repos" / "60+ repos" / "62 repos" / "69 repos" each
    referencing archived plans (the plans themselves are frozen, but the SSOT-INDEX entries citing them are read every
    session).
  - `codex/06-coding-standards/quality-gates.md` lines 198, 257 — "~62 repos" / "62 repos".
  - `codex/08-workflows/version-cascade-flow.md` lines 18, 41 — "62 repos" twice.
  - `codex/10-audit/CONTRACTS_SEPARATION_AUDIT.md` line 10 — "across 62 repos".
  - `codex/09-strategy/architecture-v2/legacy-family-migration.md` line 68 — "60+ repos".
  - `cursor-configs/CLAUDE.md` line 1772 — "When all 60+ repos are available (full workspace)".

  **Merged-repo references** (URDI / UTEI / UDEI / USEI / UML / UFCL / UPI all merged into instruments-service /
  execution-service per CLAUDE.md): 34 codex files mention them. Most are properly tagged "formerly URDI" / "merged into
  execution-service" — legitimate historical provenance. But:
  - `codex/10-audit/REPO_READINESS_CHECKLIST.yaml` lines 27-28 still treat URDI / UTEI / UDEI / UML / UFCL / UPI / USEI
    as live tier-1/tier-2 libraries in the canonical readiness checklist taxonomy.
  - `codex/04-architecture/asset-class-ownership.md` line 124 uses present tense: _"`--SPORTS` flag — CURRENTLY BROKEN:
    uses local parser, not USRI/URDI"_ — recommending repos that no longer exist as the canonical shape.

  **Deleted-provider references** (Elysium / Bloxroute / Arkham / Infura per CLAUDE.md "do NOT reference"): 10 codex
  files. **Most are correctly tagged as RETIRED / REMOVED** with provenance — that's good defensive discipline, not
  staleness. But the cumulative volume (~10 docs of "do-not-do-this" prose) is governance overhead every agent reads
  every session.

- **Operational state**: the staleness fires in real time — **this very session, the operator caught the agent quoting
  "67 repos" from the codex, and the codex itself misstates by ~2x**. Every fresh agent / sub-agent that reads the codex
  inherits the same stale framing. Cost is paid per-session in token-budget + reasoning-correctness. 60-second fix per
  stale string × ~12-50 strings = ~30 min of operator-or-agent time to remediate; cost-of-not-fixing is permanent
  ongoing token-tax + ongoing stale-fact propagation in agent reasoning.

- **Alpha-relevance**: indirect. Stale codex doesn't directly affect PnL, but it affects every agent's reasoning about
  scope ("we need to roll this out to 60+ repos" vs "...to 35 repos") which inflates planning estimates + induces
  unnecessary work.

- **Citadel-benchmark gap**: a Citadel-grade system would treat the codex as **derived from authoritative state**, not
  as a hand-edited prose surface. The repo count comes from `workspace-manifest.json` at render time. The "live repo
  list" in any codex doc is generated, not typed. A QG step asserts no hard-coded count strings survive in canonical
  prose. Today: hand-typed, hand-maintained, drift is the default state.

- **Recommendation**: **CONSOLIDATE + ADD-GATE**.
  1. **CONSOLIDATE**: one-pass sweep of stale `60+` / `6[0-9] repo` strings across `codex/` + `cursor-configs/CLAUDE.md`
     — replace with the dynamic shape `<N> repos (current count derivable from workspace-manifest.json)` or strike the
     count entirely where it's incidental. ~30 min of edits.
  2. **ADD-GATE**: PM `scripts/quality-gates.sh` adds STEP that greps for `\b(60\+|[5-9][0-9]) repo` in canonical doc
     dirs + fails CI if any survive. Sentinel: the count check is a special case of "any time the codex hard-codes a
     fact that lives elsewhere as SSOT, fail loud."
  3. **CONSOLIDATE**: `codex/10-audit/REPO_READINESS_CHECKLIST.yaml` updated to remove URDI / UTEI / UDEI / USEI / UML /
     UFCL / UPI from the live tier-1/tier-2 taxonomy (they're merged; the checklist should reflect the post-merger
     reality). `codex/04-architecture/asset-class-ownership.md` line 124 + adjacent — rewrite present-tense "CURRENTLY
     BROKEN" claims that name retired repos as the right shape.
  4. **KEEP**: deleted-provider "do-not-reintroduce" warnings in `mev-protection.md` / `legacy-family-migration.md` /
     `strategy-summary.md` — those are genuine defensive discipline (every agent reading those docs should know not to
     re-add Elysium / Bloxroute). Different from the stale-repo-count case.

  The work is **<1 day of one agent's time**, ships as a single PM commit + a CI step, and pays back permanently.

  **Update 2026-05-09**: parts (1) + (3) shipped (PM@b9c93a38 + PM@96fbd444 — codex stale-string sweep; manifest +
  `.code-workspace` cleanup of archived features-* leakage; 27-active-repo count now consistent across all three
  surfaces). Part (2) — the QG ADD-GATE step — still pending; track in active plan during plan extraction.

### B1 — Honest-coverage taxonomy as runtime convention vs as type system (filled 2026-05-10)

- **Code state**: `unified-trading-library/unified_trading_library/manifest_writer.py` is **4360 lines** in a single
  module. The 4-state honest-coverage taxonomy is enforced by **4 separate methods** on the `ManifestWriter` class
  (line 1053):
  - `record_captured(...)` — line 1968 — write a parquet + index a `captured` row.
  - `record_empty(row_key=..., reason=...)` — line 1397 — index an `empty_confirmed` row; reason MUST be from the
    closed-set `EMPTY_CONFIRMED_REASONS` frozenset (UAC) or raises `LegacyBlankErrorReasonError` (line 1463) or
    `UnknownEmptyConfirmedReasonError` (line 1467).
  - `record_failed(row_key=..., error=..., attempted_at=...)` — line 1595.
  - `record_expected_unattempted(row_key=..., attempted_at=...)` — line 1542.
  - Plus `record_captured_from_counts(...)` variant — line 2222.

  The 4-state outcome is exposed as a `CaptureStatus` `str`-enum (line 134) with 4 members (`CAPTURED` /
  `EMPTY_CONFIRMED` / `ATTEMPTED_FAILED` / `EXPECTED_UNATTEMPTED`). The enforcement is **runtime**, not type-level —
  there are 6 distinct exception classes (`MissingClusterValidationError` line 173, `MissingFeatureFamilyError` line
  204, `UpstreamTimestampBiasError` line 259, `MalformedTickFieldError` line 308, `UnknownEmptyConfirmedReasonError`
  line 349, `ClusterCoverageError` line 379) plus `LookaheadBiasError` from the `point_in_time` module — each fires
  when the adapter calls the wrong method shape or passes invalid arguments. None of these would compile-fail; they
  all raise at runtime, after the bad call has been written.

  The 4 separate methods means an adapter author can call `record_captured(...)` on a parquet that's actually empty,
  and the only thing that catches it is one of the runtime `*Error` classes if the validation gates trigger — which
  they don't always (the 2026-05-05 MDPS 1440-NaN-OHLC-bars-per-day-for-years incident is the canonical case where
  `record_captured` accepted thousands of empty rows because the writer's row-count gate didn't fire on
  `O=H=L=C=None`).

- **Codex state**: ~6 codex docs cover this surface:
  - `codex/02-data/availability-manifest-and-data-status.md` — manifest schema + 4-state taxonomy SSOT.
  - `codex/02-data/honest-absence-downstream-handling.md` — downstream NaN-handling per category + reason taxonomy
    (codified 2026-05-07).
  - `codex/02-data/expected-absence-backfill-runbook.md` — per-source absence-classification rules.
  - `codex/02-data/hive-schema-compatibility.md` — manifest hive partition shape.
  - `codex/02-data/manifest-migration-coordination.md` — multi-writer coordination protocol.
  - `cursor-configs/CLAUDE.md` (~6 separate sections) — 4-category empty-output decision rule, write-gate validation,
    cluster validation, available_at semantics, etc. Many of these rules grew incrementally — each in response to a
    specific incident (TradFi MVP partial-bundle, MDPS 1440-NaN, RED ALERT silent-fallback). Volume: roughly **400
    lines of CLAUDE.md alone** are dedicated to honest-coverage discipline + its enforcement protocol.

  **Cross-reference cost**: the 4-state taxonomy is referenced by name in ~30 codex docs and ~50 plan files
  (frequency-of-use). Every agent reading any one of those reads the closed-set vocabulary; every adapter author has
  to know which of 4 record methods + ~10 typed reasons is correct for their case.

- **Operational state**: this is the area with the highest fire-rate of the entire system. Documented incidents
  caught by the runtime-convention layer (only after the fact):
  - 2026-05-05 MDPS 1440-NaN-OHLC-bars-per-day-for-years (silent-success-with-empty-output for years before
    hand-inspection caught it).
  - 2026-05-06 TradFi MVP ES.OPT 18-dates-with-single-parent-fills (partial-bundle marked `captured`).
  - 2026-05-07 RED ALERT: 5 CeFi VMs writing 96-100% empty rows with all blank reasons
    (bitfinex/bitget/kraken — silent fallback to legacy blank-reason path before `LegacyBlankErrorReasonError`
    landed via UTL@68b3804a).
  - 2026-04-29 phantom audit: 167k fake PLAYER_VALUES denorm rows + 15k legacy phantoms.
  - 2026-05-04 phantom audit: 130,897 false-positive phantoms across CeFi (path-prefix + chain-bundle drift; real
    residual = 354 after 5-axis reconciler).
  - 2026-05-07 MTDS partial-bundle Databento: bundled `ohlcv_1m;trades` lost ohlcv on 429 marked complete.

  These are 6 documented *significant* incidents over 30 days, each requiring a multi-day fire-fight + a new codex
  rule + a new reconciler script. The runtime-convention layer **caught them late, but did catch them** — that's the
  pattern. Net team-hour cost over the last 90 days: easily **>2 weeks** of senior-agent time on writegate /
  reconciler / phantom-audit work.

- **Alpha-relevance**: **indirect but high-leverage**. Bad data → bad features → bad strategies → bad PnL. The 4-state
  taxonomy is on the alpha critical path: every honest-coverage incident has either (a) directly corrupted backtest
  history (lookahead bias from missing `available_at`) or (b) wasted weeks of researcher / engineer time on
  fire-fighting instead of alpha work. The discipline is necessary; the *shape* of the discipline is the audit
  question.

- **Citadel-benchmark gap**: a Citadel-grade system would model the 4 outcomes as a **discriminated union ADT** —
  `AdapterResult` is one of `Captured(parquet_path: Path, row_count: int, available_at_envelope: tuple[datetime,
  datetime], cluster_coverage: ClusterCoverage)` | `EmptyConfirmed(reason: EmptyConfirmedReason, attempted_at:
  datetime)` | `Failed(error: VenueError, attempted_at: datetime)` | `ExpectedUnattempted(attempted_at: datetime)`.
  The adapter's `fetch_and_write` method returns this ADT; the manifest writer takes one as input; you can't write
  `captured` for an empty result because you can't construct `Captured(row_count=0)` — the dataclass `__post_init__`
  raises (or even better, `row_count: PositiveInt` from pydantic). Per-case validation is per-variant: `Captured`
  validates row count + NaN ratio + cluster coverage + schema match; `EmptyConfirmed` validates reason in closed set;
  etc. The 6 runtime exception classes collapse into ~3 type-level invariants enforced by construction.

  Composes naturally with operator's directive **"common SSOT codebase + hooks + min duplicate thread + full
  flexibility"**: the ADT is the single SSOT for "outcome shape"; per-data-type / per-source customisation happens via
  the `cluster_coverage: ClusterCoverage` and `reason: EmptyConfirmedReason` extension points — same hook pattern as
  UAC adapter registries.

- **Recommendation**: **LIFT (high-priority, post-cutover)**.
  1. **NEW**: UAC `unified_api_contracts.canonical.crosscutting.honest_coverage` — define `AdapterResult` as a sealed
     discriminated-union dataclass (Python `match` statement support; pydantic validators per-variant). 4 dataclasses,
     ~150 LoC total.
  2. **NEW**: UTL `manifest_writer.write_result(result: AdapterResult, row_key: dict[str, str]) -> None` — single
     entry point that pattern-matches on the variant and dispatches to the existing internal write paths. Old 4
     `record_*` methods kept as deprecated shims for one release cycle, then deleted.
  3. **MIGRATE**: every adapter (~30 across MTDS / instruments-service / features-service / sports adapters / DeFi
     adapters) updated to return `AdapterResult` instead of calling `record_*` directly. The `unified-trading-system`
     monorepo (Block A1 DECIDED-YES) makes this a single PR instead of 30.
  4. **DELETE**: 4 of the 6 runtime exception classes (`MissingClusterValidationError`, `MalformedTickFieldError`,
     `UnknownEmptyConfirmedReasonError`, `ClusterCoverageError`) become unconstructible — the variants enforce them
     by-shape. `LookaheadBiasError` + `UpstreamTimestampBiasError` survive (genuine cross-cutting timing concerns).
  5. **REDUCE**: ~400 lines of CLAUDE.md honest-coverage discipline collapses to **~50 lines**: the ADT shape +
     "always return AdapterResult, never call record_* directly" + 1 link to the codex doc. The remaining 350 lines of
     incident-driven rules become unnecessary because the types prevent the bug class.
  6. **GATE**: workspace-wide grep step in QG fails CI if `record_captured(`, `record_empty(`, `record_failed(`,
     `record_expected_unattempted(` appear in any adapter source after the migration deadline.

  **Cost**: ~3-5 AI-days for the UAC + UTL + 1-2 reference adapter + tests; +1-2 AI-days per adapter family for the
  migration sweep (parallelisable). **Saved cost**: every future honest-coverage incident class is type-level
  unrepresentable; ~2 weeks/quarter of fire-fighting recovered; ~350 lines of CLAUDE.md governance overhead deleted.
  **Timing**: post-May-23 cutover (the existing runtime convention works for the cutover; the lift is the
  permanence-improvement); ride with the Block A1 monorepo migration so it lands as one architectural slice.

  **Active plan update**: file new plan
  `plans/active/honest_coverage_adt_lift_<date>.md` (post-cutover work) OR fold into the spawned monorepo
  consolidation plan as a Phase under `unified-trading-core/contracts/` redesign.

### B2 — Per-source colocation vs per-(asset_group, data_type) colocation (filled 2026-05-10)

- **Code state**: UAC `unified_api_contracts/external/` has **73 source sub-directories**. Each follows a flat
  per-source layout: `__init__.py` + `examples/` + `mocks/` + `normalize.py` + `schemas.py`. The 73 are NOT 1:1 with
  the ~53 venues — extra ~20 are data-providers (databento, tardis, alchemy, defillama, cryptoquant, barchart,
  coinglass, etc.) + macro-data feeds + auxiliary services. Cross-cutting "per-data_type" view today comes from prose
  matrices (`mtds-data-source-coverage-matrix.md` + sports sibling) cross-linked to UAC registry helpers
  (`VenueMapping.all_*_venues`, `get_expected_data_types_for_venue`, `get_venue_data_type_start_date`).

- **Codex state**: 2 prose matrix docs (~500 lines each) hand-typed; cross-link to registry helpers but ARE prose.
  Drift risk: 2026-04-20 phantom-audit incident (false 26% sports ODDS phantom) was matrix-doc / registry-code drift.

- **Operational state**: per-source colocation works for "add a source" (1 PR / 1 dir / 1 registry entry). Strains on
  cross-cutting audits — every reconciler has to enumerate sources + read schemas + normalize into per-data_type
  view. ~5 documented incidents involved cross-cutting drift not catchable from any single source's view.

- **Alpha-relevance**: indirect (bad coverage denominators → bad expectations).

- **Citadel-benchmark gap**: keep per-source colocation (natural physical shape); generate per-data_type view from a
  **typed registry** rather than prose matrix. Each source declares emitted data_types as
  `SOURCE_EMITS: dict[DataType, EmissionSpec]` next to its `schemas.py`; UAC exposes
  `data_type_coverage(dt)` derived helper; matrix doc becomes generated artefact. Composes with operator's "common
  SSOT codebase + hooks + min duplicate" — `EmissionSpec` is the extension hook, per-source files are hook impls,
  cross-cutting view is derived not duplicated.

- **Recommendation**: **KEEP per-source colocation; LIFT cross-cutting view to typed-registry-derived**.
  1. **NEW**: UAC `data_type_registry.py` — typed cross-cutting registry; per-source `external/{source}/registry.py`
     declares emissions.
  2. **NEW**: `data_type_coverage(data_type)` + `sources_for(venue, data_type)` derived helpers replace the prose
     matrix as SSOT.
  3. **NEW**: `scripts/render-coverage-matrix.py` generates the matrix doc from registry at PM QG time; commits the
     rendered .md; QG asserts no manual edits to the rendered file.
  4. **MIGRATE**: 73 source dirs each get a `registry.py` (current implicit knowledge in adapter code becomes
     typed-explicit).
  5. **DELETE**: prose matrix doc once rendered version is canonical.

  **Cost**: ~2-3 AI-days for registry + 1-2 reference migrations + render script; +1 AI-day per source family for
  migration sweep. **Saved cost**: drift-induced phantom incidents go away by construction. **Timing**: post-cutover;
  ride with monorepo migration.

  **Active plan update**: extend `manifest_evolution_master_2026_05_08` with a Wave for the cross-cutting registry
  lift, OR file as Phase under the spawned monorepo plan
  (`plans/active/codex_vs_citadel_infrastructure_audit_2026_05_10.md`).

### B3 — Manifest as side-effect-of-write vs as pre-flight planner + post-flight verifier (filled 2026-05-10)

- **Code state**: today's manifest is written as side-effect by adapters via the 4 `record_*` methods (B1 above).
  `record_expected_unattempted` (line 1542) is the **early form of the planner-side** — pre-flight enumerator
  pre-populates expected rows; adapters supersede them with `record_captured` / `record_empty` / `record_failed` as
  they run.

  **Operator has already started this transition.**
  `plans/active/expected_universe_v2_design_2026_05_08.md` (status: draft, folded into
  `manifest_evolution_master_2026_05_08` umbrella) is the canonical "manifest = pre-flight plan + post-flight
  verification" plan. Per the plan frontmatter: *"manifest, code, and data migrate in the same group plan to avoid
  collision risk; force batch execution; don't allow execution in isolation."*

- **Codex state**: covered by `availability-manifest-and-data-status.md` § "Two SSOTs for the manifest's expected
  universe" + `pipeline-coverage-matrix.md`. The "expected universe = catalog × dates × data_types" model is already
  documented; gap is in implementation.

- **Operational state**: 4 documented phantom-audit incidents in 30 days are the manifestation of "writer-as-SSOT
  means audit-after-the-fact."

- **Alpha-relevance**: indirect (bad coverage denominators → bad expectations).

- **Citadel-benchmark gap**: NONE conceptually — operator's existing plan sketches the right shape. Gap is execution.

- **Recommendation**: **ALIGN — follow operator's existing plan**. No new audit recommendation; track v2 enumerator
  landing + audit whether it actually replaces writer-as-SSOT vs sits alongside. **Zero new active plan updates
  needed for B3** — operator's already on it.

### B4 — `live = batch` principle: prose vs type-level enforcement (filled 2026-05-10)

- **Code state**: grep for `mode == "live"` / `mode == "batch"` / `pipeline_mode == ...` across strategy-service +
  features-service + market-tick-data-service: **only 11 occurrences**. Lower than expected given the volume of doc
  + plan content asserting the principle. Suggests principle is mostly enforced; the 11 are likely legitimate seam
  dispatchers (data source / output sink / live-trigger vs batch-trigger).

- **Codex state**: `codex/04-architecture/batch-live-architecture.md` (436 lines) is the SSOT — folded from 2 prior
  separate docs per `codex_refactor_2026_05_08`. Volume substantial (~500 lines) but earned.

- **Operational state**: low fire-rate in past 90 days. Principle is mostly self-enforcing.

- **Alpha-relevance**: **direct** — bad batch=live correspondence = backtest results don't predict live PnL = wasted
  research cycles.

- **Citadel-benchmark gap**: small. Principle mostly enforced; type-level enforcement (B4 original critique) is
  overkill for 11 remaining mode-branches. Bigger win is **structural**: per Block A1 consolidation, the `Pipeline`
  base class lives in `unified-trading-core/runtime/` as a shared primitive every service inherits, not 5+
  copy-paste implementations across service repos.

- **Recommendation**: **KEEP — light touch**.
  1. **NEW**: spot-check the 11 mode-conditional branches; classify legitimate-seam vs mode-leakage; fix in place if
     leakage (single PR).
  2. **NEW**: in spawned monorepo plan, `Pipeline` base class lives in `core/runtime/` as shared primitive — use
     consolidation as opportunity to enforce seam shape via subclassing / dependency injection rather than generic
     type parameter.
  3. **GATE**: optional QG step that greps `if.*mode\s*==\s*` patterns in service source + WARNs (not fails).

  **Cost**: ~1 AI-day for audit + spot-fix sweep. **Saved cost**: small but non-zero. **Timing**: post-cutover;
  rides with monorepo consolidation.

  **Active plan update**: NONE NEEDED — track as informal item in the monorepo plan when spawned.

### B5 — `available_at` as write-time stamp vs schema-level invariant (filled 2026-05-10)

- **Code state**: `unified_trading_library/availability_stamping.py` is **330 lines** — substantial helper module
  with per-source stamping rules (sports `kickoff − 60min`, fixture_events `event_time`, post-match
  `match_end_time`, pre-match odds publication time, weather forecast-issue-time, tick-level
  `tick.timestamp + scrape_latency`). `manifest_writer.assert_available_at_present` (line 72) is the runtime gate;
  missing/null `available_at` raises `LookaheadBiasError`.

  Two enforcement layers exist: (1) stamping helpers — opt-in by adapter author; (2) runtime gate — catches
  missing-stamp at write time, not earlier. Gap: gate is at write time, not at row-construction time. An adapter
  that constructs rows in memory without stamping doesn't fail until the writer tries to record them. Worse: an
  adapter that stamps with the WRONG rule (e.g. `event_time` for a post-match stat that should use
  `match_end_time`) never fails — silent lookahead bias.

- **Codex state**: `codex/04-architecture/instrument-lifecycle-cache-delta-hot-reload.md` + sports-specific stamping
  rules in CLAUDE.md "Shard-granularity SSOT" section + ~5 plans + the `available_at_lookahead_bias_completion_*`
  active plan. Substantial cross-referencing across multiple files. Drift risk: per-source stamping rules codified
  across multiple files; adding a new source means updating helper + doc + remembering the rule.

- **Operational state**: lookahead-bias incidents have surfaced in 3+ documented cases (carry-tracer, sports lineup
  leakage, sports fixture stats). Runtime gate catches missing-stamp; doesn't catch wrong-rule.

- **Alpha-relevance**: **direct + critical**. Lookahead bias = invalid backtest = invalid alpha. Every minute of
  lookahead in features = potentially $X of phantom alpha that won't materialise live. **The single highest-priority
  Block-B item.**

- **Citadel-benchmark gap**: a Citadel-grade system would model `available_at` as a **type-level required field on
  every row** with a per-source `AvailabilityRule` Protocol that the row constructor invokes — adapter literally
  cannot construct a row without computing the stamp. Today it's a runtime gate.

  Concretely: row base class in UAC requires `available_at: datetime` field; pydantic validator on every row class
  invokes the row's source's `AvailabilityRule.stamp(row)` automatically. `AvailabilityRule` becomes a typed
  primitive in UAC: `class AvailabilityRule(Protocol): def stamp(self, row: dict) -> datetime: ...` with per-source
  implementations. Adding a new source = adding one `AvailabilityRule` impl; the row constructor calls
  `rule.stamp(row)` automatically.

- **Recommendation**: **LIFT (post-cutover, high-leverage)**.
  1. **NEW**: UAC `availability_rule.py` — `AvailabilityRule` Protocol + per-source implementations (lift from
     `availability_stamping.py`).
  2. **NEW**: row base class in UAC requires `available_at: datetime` via pydantic validator that calls the row's
     source's `AvailabilityRule.stamp(row)` automatically.
  3. **MIGRATE**: per-source row classes inherit from the base; `stamp_available_at_*` opt-in helpers become
     unnecessary (auto-applied via validator).
  4. **DELETE**: 330 lines of `availability_stamping.py` collapse to ~50 lines (per-source rule impls only).
  5. **REDUCE**: cross-referenced CLAUDE.md + codex doc surface for `available_at` rules collapses to one canonical
     UAC reference.

  **Cost**: ~2-3 AI-days. **Saved cost**: lookahead-bias incident class becomes type-level unrepresentable; ~1 week
  of fire-fight per surfaced incident saved. **Timing**: post-cutover; ride with monorepo + B1 ADT lift (composes —
  the `Captured(...)` ADT variant takes a row collection that's already stamped).

  **Active plan update**: extend the active `available_at_lookahead_bias_completion_2026_05_08.md` plan with a
  post-cutover Phase for the type-level lift.

## Operator notes / answers

- **2026-05-08 ikenna correction**: the codex's "67 repos / 65 repos / 60+ repos" framing is wrong; actual count is
  **35** as of today. URDI / UTEI / and others were merged. This factual correction is preserved in Block A1 + A2 and is
  itself the cleanest data point seeding the codex-staleness audit (A2 — codex misstates its own repo count by ~2x).

## Iteration log

| Date       | Author              | Change                                                                                                                            |
| ---------- | ------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| 2026-05-08 | ikenna + main agent | Initial draft created with fresh-eyes critique seeded into Block A-F sub-questions                                                |
| 2026-05-08 | ikenna + main agent | Repo count corrected 67 → 35 across doc (operator caught stale codex inheritance); meta-finding promoted into A2 + Operator notes |

## Plan-shape decisions (filled before plan extraction)

- **Plan name + path**: TBD — likely `plans/active/codex_consolidation_<date>.md` for the consolidation slice + a
  separate `plans/active/researcher_experience_and_alpha_attribution_<date>.md` for the alpha-multiplying additions.
  Each large enough to be its own master.
- **Plan type**: mixed — code (B1 ADT refactor, B4 type-level batch=live, D1 job-runtime port) + infra (A1 repo
  consolidation, D3 per-agent worktrees, D6 continuous QG hygiene) + docs (A2 tiered codex, A2 codex-re-derivation gate,
  A3 CLAUDE.md trim) + business (E1-E7 alpha-multiplying primitives).
- **Owner side**: ikenna for the cross-cutting design + benchmark codification + repo consolidation calls; harsh for
  per-area implementation slices once decided.
- **Codex SSOTs touched** (TBD pending audit): likely NEW: `04-architecture/citadel-grade-target-architecture.md` (the
  benchmark doc), `09-strategy/researcher-experience-golden-path.md`, `09-strategy/alpha-attribution-primitives.md`,
  `04-architecture/portfolio-construction-layer.md`, `04-architecture/regime-detection-layer.md`.
- **Cross-plan dependencies**:
  - composes with `risk_simulations_limits_alerting_2026_05_08.md` (sibling question) — risk + portfolio construction
    overlap (note: that doc was previously in `plans/questions/` but was overwritten in the directory churn this session
    — verify with operator whether it still exists elsewhere).
  - composes with `client_reporting_pnl_attribution_2026_05_08.md` (sibling question) — PnL attribution overlap (same
    note as above re: directory churn).
  - composes with `batch_live_design_symmetry_2026_05_08.md` (sibling question, currently in `plans/questions/`) — B4
    overlap.
  - composes with `topology_features_strategy_ml_execution_2026_05_08.md` (sibling question, currently in
    `plans/questions/`) — Block C overlap (researcher experience touches the same surface).
  - composes with `paper_vs_live_workflow_maturity_2026_05_08.md` (sibling question, currently in `plans/questions/`) —
    A3 overlap (operational mechanics).
  - composes with `master_to_live_defi_2026_05_23.md` Group A-G items — many of the audit's recommendations either
    fold-in to existing master items or stand alone post-cutover.
- **Estimated scope**: TBD pending audit — anywhere from 5 AI-days (codex consolidation only, defer everything else
  post-cutover) to 30+ AI-days (full re-shape including B1 ADT + D1 job runtime + E1-E7 alpha primitives).

## Plan extraction record

(Empty — fills when the plan ships.)
