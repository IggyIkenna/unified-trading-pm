---
name: features_and_ml_master
title: "ML + Features Master (umbrella)"
type: epic
tier: L1
status: active
priority: P1
assigned_vm: vm-ml
parent: master_to_live_defi_2026_05_23
created: 2026-05-07
last_updated: 2026-05-21
locked_by: live-defi-rollout
locked_since: 2026-05-07
related_plans:
  - ../archive/features_repo_consolidation_2026_05_08.plan.md
  - ../active/features_service_qg_cleanup_2026_05_11.md
  - ../active/ml_repo_consolidation_2026_05_19.md
  - ../archive/2026_05/phase5_features_streaming_carry_staked_basis_mvp_2026_05_19.md
  - ../active/regime_clustering_structure_allocator_2026_05_29.md
---

# ML + Features Master (umbrella)

> **🟡 IN-FLIGHT REFACTOR — features-\* repo consolidation + live-pipeline activation 2026-05-08**
>
> [`features_repo_consolidation_2026_05_08`](../active/features_repo_consolidation_2026_05_08.md) merges the 8 separate
> features-\*-service repos into a single `features-service` repo with sub-packages per family. Phase 5 of that plan
> lifts 4 cross-family helpers (watermark+grace fan-in, available_at stamping, LookaheadBiasError gate, NaN write-gate)
> into UTL — overlaps with this plan's Phase 2.UTL-LIFT (FeatureBatchHandler lift). Coordinate ownership: this plan owns
> FeatureBatchHandler; consolidation plan owns the 4 helpers; banner mutually to avoid double-lift.
>
> [`live_pipeline_mtds_mdps_features_2026_05_08`](../active/live_pipeline_mtds_mdps_features_2026_05_08.md) builds on
> the consolidated repo for live-mode features compute. This plan's batch features compute work continues in parallel.
> Naming disambiguation: "features consolidation" in THIS plan = feature-DATA consolidation (pre-joined wide parquet for
> ml-training reads); features_repo_consolidation = REPO consolidation. Different scopes; both ship pre-May-23.

> **🟡 IN-FLIGHT REFACTOR — `available_at` adapter stamping** (coordinated by
> `available_at_lookahead_bias_completion_2026_05_08` Phase 1). Re-verify per-adapter `available_at` stamping wiring
> before adding new adapters to this plan.

> **Consolidation 2026-05-07**: this umbrella folds 4 previously-standalone plans
> (`feature_dag_uac_ssot_and_features_coverage` / `features_consolidation_and_drilldown` /
> `ml_training_feature_read_perf` / `consolidated_ml_advanced_pipeline`) into one SSOT covering the full **UAC
> feature-DAG → features-\* writers → ml-training reader → ml-inference → strategy consumption** chain. Source plans
> archived alongside this file with an `ARCHIVED` banner pointing back here; all open todos preserved verbatim in Phase
> 1-4 below.

## Scope

This is the SSOT for everything that lives between the raw-data writers (owned by the writegate honest-coverage plan)
and the live-trading strategy service. The chain has four logical tiers, each owned by one of the folded source plans:

1. **UAC feature-DAG SSOT** — the `feature_group → required_inputs[]` registry, plus
   `EXPECTED_FEATURE_GROUPS_BY_SERVICE` + `FEATURE_COVERAGE_START` denominators, plus the UTL `ManifestFreshnessCache`
   lifted out of `/tmp/fill_missing_ohlcv.py`. Without this, the `LookaheadBiasError` strict-mode check in writegate
   runs against per-service inlined DAGs (3 of them, drift-prone) and the data-status feature-coverage rollup
   denominator is inferred from manifest contents (circular: shows 100% even when nothing's been written).
2. **features-\* writer + reader pre-join** — UTL `FeatureBatchHandler` base lifting the
   `(DataLoader, Calculator, FeatureWriter, ManifestWriter, ManifestFreshnessCache, write-gate)` glue duplicated across
   Delta-One / Onchain / Sports / Volatility services (~200 LOC each). Plus the feature-store consolidation sidecar that
   pre-joins all feature_groups into a single wide parquet per `(asset_group, day, instrument, timeframe)` so
   ml-training does one GCS GET per day instead of N. Plus the deployment-ui feature-group drill-down route.
3. **ml-training feature-read perf** — surgical wins inside `gcs_feature_reader.py` / `feature_data_adapter.py`: parquet
   row-group pruning + column push-down + DuckDB lazy joins replacing pandas outer-merge. Target ≥2× faster read step +
   ≥30% lower peak RSS during merge. Self-contained 1-3 day item; baseline that the consolidation work needs to beat by
   5-10×.
4. **ML model lifecycle** — calibration / Bayesian tuning / incremental + transfer + multi-task training / hierarchical
   inference / strategy calibrated-signal consumption / cost-aware strategy filtering. About 70% of the original
   `consolidated_ml_advanced_pipeline` items are PARTIALLY_DONE (skeletons exist, spec items missing); net-new items
   (multi-task, hierarchical, calibrated signal consumption, cost-aware strategy) are May-23-or-later live trading
   prereqs.

The 4 source plans shared owner repos (UAC + UTL + features-\* + ml-training + ml-inference + strategy +
deployment-api/ui) and the same downstream consumer chain. Splitting them across 4 plans made it ambiguous which plan
owned `LookaheadBiasError` strict-mode wiring, the `ManifestFreshnessCache` adoption, or the `FeatureBatchHandler` lift;
the umbrella collapses that ambiguity by sequencing the work as a single critical path.

**MVP backtest scope** (per
[`codex/09-strategy/mvp-universe-per-asset-group.md`](../../codex/09-strategy/mvp-universe-per-asset-group.md)): ML
training data volume bounded by Tier A archetype universe: ~6M training rows total across all archetypes (TradFi S&P
~365K, DeFi carry ~1.3M, CeFi perp arb ~2.6M, Sports ~800K, Prediction ~900K). ml-continuous (CeFi + ES)

- ml-settled (Sports) are the two ML archetype families May-23 must complete; broader ML framework supports the rest
  code-ready.

## Codex SSOTs

Read these BEFORE making code changes; drift between code and these docs is a review-blocking failure per
`doc → plan → code`:

- [`codex/02-data/data-lineage-MTDS-features-ml.md`](../../codex/02-data/data-lineage-MTDS-features-ml.md) — MTDS →
  features-\* → ml-training/ml-inference lineage; calibration / Bayesian tuning / hierarchical inference / consolidation
  sidecar all sit on this chain.
- [`codex/02-data/honest-absence-downstream-handling.md`](../../codex/02-data/honest-absence-downstream-handling.md) —
  NaN handling per consumer class (rolling-window denominator adjustment, propagated NaN through cross-instrument
  calcs); the consolidation join boundary + DuckDB lazy-join must preserve these semantics.
- [`codex/02-data/data-status-drilldown-hierarchy.md`](../../codex/02-data/data-status-drilldown-hierarchy.md) —
  drill-down hierarchy SSOT for the deployment-ui feature-group route + per-feature-group parquet download endpoint.
- [`codex/04-architecture/batch-live-architecture.md`](../../codex/04-architecture/batch-live-architecture.md) —
  batch=live symmetry; ml-training (batch) + ml-inference (live) MUST share the same feature-read path + same
  calibration.
- [`codex/04-architecture/batch-live-architecture.md`](../../codex/04-architecture/batch-live-architecture.md) —
  code-path symmetry contract; strategy signal consumption + decision policy engine cannot diverge between modes.
- [`codex/06-coding-standards/feature-service-pattern.md`](../../codex/06-coding-standards/feature-service-pattern.md) —
  features-\* service pattern; the UTL `FeatureBatchHandler` base lifts the boilerplate the doc describes.
- [`codex/06-coding-standards/quality-gates.md`](../../codex/06-coding-standards/quality-gates.md) — QG discipline for
  the perf changes (basedpyright, ruff, coverage floor on the rewritten reader path).
- [`codex/06-coding-standards/performance-targets.md`](../../codex/06-coding-standards/performance-targets.md) —
  service-level perf targets (the 2-4× / 5-10× targets live here).

## Phased execution DAG

```
Phase 1 (UAC + UTL foundations)
    1A — UAC feature-DAG SSOT + denominator registries (PARALLEL with 1B)
    1B — UTL ManifestFreshnessCache + assert_no_lookahead_for_feature_group helper
                |
                v  (QG gate)
Phase 2 (features-* writers + reader pre-join)
    2A — Replace per-service DAGs with UAC import + wire UTL lookahead helper
    2B — Adopt ManifestFreshnessCache in features-sports + features-volatility BatchHandlers
    2C — deployment-api denominator clip via UAC FEATURE_COVERAGE_START
    2D — UTL FeatureBatchHandler base + 4-service refactor
    2E — Feature-store consolidation sidecar (write-time pre-join)
    2F — deployment-ui feature-group drill-down route + download endpoint
                |
                v  (QG gate)
Phase 3 (ml-training read perf)
    3A — Row-group pruning + column push-down (PARALLEL with 3B)
    3B — DuckDB lazy joins
    3C — Concurrency tuning (features-volatility, features-delta-one max_workers)
    3D — End-to-end benchmark + B3 sign-off
                |
                v  (QG gate)
Phase 4 (ML model lifecycle)
    4A — Calibration + P&L objectives + Bayesian tuning + feature-importance polish
    4B — ml-training: multi-task joint training; SHAP GCS history persistence
    4C — ml-inference: hierarchical model loading Level 0-2
    4D — strategy-service: calibrated-signal consumption + cost-aware filtering
                |
                v  (QG gate)
Phase 5 (phantom audit + sanity replay)
    5A — Extend reconcile_phantom_manifest_rows_all.py to features manifest
    5B — Sanity replay on 3 representative shards
```

## Critical-path priority for May-23

**Upstream sibling-blocker.** Phase 2A consumer migration depends on adapter-side `available_at` write-time stamping
landing across the per-source MDPS / MTDS / features-input adapter surface. That stamping work is owned by
[`writegate_honest_coverage_endtoend_2026_05_06`](../active/writegate_honest_coverage_endtoend_2026_05_06.md) Phase 2.D
(per-source `stamp_available_at_*` helpers). Coordinate cadence with Agent 2 (writegate tab) — partial coverage exists
today; the Phase 2A `assert_no_lookahead_for_feature_group` helper silently no-ops on adapters that haven't been
migrated yet, so Phase 2A correctness is contingent on writegate Phase 2.D progressing.

- **Phase 1A** (UAC `FEATURE_REQUIRED_INPUTS` SSOT): 1-day pure-win, gates writegate's `LookaheadBiasError`
  strict-mode + Phase 2's whole consumer migration. Already substantially shipped (UAC@4a25b07 + UAC@2f40c9d +
  UAC@7a3299a + UTL@d7902f6 + UTL@4354276c) — closes the remaining sports vocabulary alignment + the 8-service consumer
  wires.
- **Phase 1A.3 sports vocabulary decision** (operator ~30 min): the resolution-approach pick (mapping table /
  tuple-typed required_inputs / namespaced names) GATES Phase 2A consumer migration for features-sports-service. Until
  this decision lands, features-sports cannot be wired into the UAC DAG, and the `assert_no_lookahead_for_feature_group`
  helper degrades to a silent no-op on sports calculators. Hard floor for features-sports correctness — pull forward
  into Phase 1A finalization.
- **Phase 3A+3B quick-wins** (row-group pruning + column push-down + DuckDB lazy joins): pure Python, self-contained, no
  risk to live trading correctness. ~1-3 day spike unlocks the 5-10× consolidation-sidecar target downstream.
- **Phase 4D** (strategy-service calibrated-signal consumption + cost-aware filtering): live trading prereq for May-23
  Group F (Trading prerequisites). Hard floor. **Acceptance criterion** (was missing pre-deep-audit): a strategy-service
  `pytest` integration test with mock ml-inference calibrated output + cost-aware filtering enabled, asserting (a)
  signal pass-through respects calibrated confidence thresholds and (b) cost-aware filter drops signals where
  `expected_alpha < execution_cost_bps`. Sub-criterion: shadow-mode wiring on at least one archetype (e.g.
  `carry_staked_basis`) producing live-vs-mocked diff before automation flip.
- **Everything else** (consolidation sidecar, FeatureBatchHandler base, deployment-ui drill-down, multi-task training,
  hierarchical inference, phantom audit extension): post-May-23.

## Tier-violation cleanup (slot 7, 2026-06-01 — surfaced during dependency-alignment)

- [ ] [CODE] P1. **regime_clustering imports ml-service across a tier boundary (TIER_VIOLATION).**
      `features-service/features_service/cross_instrument/app/calculators/regime_clustering.py:178` does
      `from ml_service.training.backtest_v2.walk_forward import ...` (function-local,
      `# noqa: imports-inside-functions`). ml-service is a higher tier than features-service, so a feature calculator
      depending on ML _training/backtest_ code is backwards. `fix-internal-dependency-alignment.py` reports
      `TIER_VIOLATION` (can't add to pyproject). features pyproject already omits ml-service, so the (optional)
      `ml-service` entry was **removed from `workspace-manifest.json` features deps** (slot 7 2026-06-01) to align
      manifest↔pyproject + unblock the PM dependency-alignment gate — but the lazy import remains a latent runtime
      ImportError (if features runs without ml-service installed) + an architectural leak. Fix: move `walk_forward` (or
      the shared regime/backtest helper) to a lower tier (UTL/UAC), or remove the regime_clustering→ml dependency.
      Repos: features-service (+ ml-service).

## DeFi data-loading dispatch (slot 7, 2026-06-01 — from `features_service_defi_data_loading_blockers_2026_05_29.md`)

- [ ] [CODE] P1. **DeFi #1 — map `volume_analysis` / `vwap` / `microstructure` feature groups → `dex_pool_swaps`** via
      UAC `resolve_data_type_for_feature_group()` so DeFi features resolve to the canonical dex_swaps data_type. Repo:
      features-service (self-contained). Operator decision 2026-06-01. **Consumer-side mapping (NOT manifest work)** —
      depends on `defi_manifest_canonicalisation_2026_06_01.md` § C2 establishing the canonical `dex_swaps` data_type.
- [ ] [DATA] P2. **DeFi #2 — legacy bucket = read-only historical archive; NO manifest rebuild.** Operator decision
      2026-06-01: the legacy DeFi bucket is a read-only historical archive; do NOT rebuild its manifest (that would be
      manifest-canon work). Treat as read-only when loading historical DeFi features. Repo: features-service (policy).
- **DeFi #4 — drop duplicate columns `swap_count` / `volume_quote_usd` from `DEX_SWAPS_SCHEMA`** → **MOVED to
  `defi_manifest_canonicalisation_2026_06_01.md` § C0-RD6** (it's a `dex_swaps` superset-union refinement on existing
  parquet → must fold into the single-walk, not a separate schema change). Slot-7 DeFi #3 confirmed they are exact
  aliases (`swap_count == trade_count`, `volume_quote_usd == volume`). Tracked there to avoid dual-tracking.
- [ ] [DOCS] P1. **DeFi #3 — UAC contract-doc: document `dex_swaps` OHLC semantics.** Slot-7 investigation 2026-06-01:
      O/H/L/C are **USD-normalized pool spot prices** (price = `amountUSD / abs(base amount)`; for USDC/WETH this yields
      ~1.0 = USDC-per-WETH, which is correct, not a bug). The UAC contract is currently SILENT on this. Add a docstring
      to the `swaps_ohlcv_*` schema in
      `unified-api-contracts/unified_api_contracts/internal/schemas/_candle_contracts.py` clarifying the three
      aggregation methods (amountUSD/base, amount_in_usd/amount_in, token-ratio fallback). NO MDPS bug found
      (`market_data_processing_service/app/adapters/defi/swap_adapter.py:237-316` is correct). Repo:
      unified-api-contracts.

## Open questions

### Q1 — [ml-features-phase2a-tab, 2026-05-08 07:50 UTC] ✅ RESOLVED — operator picked (b) Defer per features-repo-consolidation absorption

**Main agent escalation note 2026-05-08 07:55 UTC**: This is a strategic-scope call (defer/ship/contract- change), not a
technical answer main can make autonomously. Surfaced to operator chat as case-5 BIG (work- split affecting + UTL
contract surface + cross-cutting 8 services). Operator is at lunch, ETA return ~10:00 UTC. Tab 12 — continue with the
per-service compute-boundary inventory doc as you proposed in the question body; that's productive regardless of which
path (a/b/c) operator picks. Don't ship wires until A1 lands. `git fetch && git pull` periodically (or just re-read this
section); A1 will appear here.

**Scope ambiguity for Tab 12 (Phase 2A wire-in) — spawn prompt vs plan body.**

The Tab 12 spawn prompt in
[archived `work_split_2026_05_07_harsh_5tab_layout`](../archive/work_split_2026_05_07_harsh_5tab_layout.md) §"Tab 12"
said: _"wire the 8 services that compute features into the UTL `assert_no_lookahead_for_feature_group` helper... so
every feature compute call validates inputs against the UAC `feature_group → required_inputs` DAG at runtime."_ —
implying ship the wires now.

The plan body (this doc) Phase 2A marks all three named consumers (`features-onchain-service`,
`features-sports-service`, `features-delta-one-service`) as **P1** with
**`[BLOCKED-ON adapter-side available_at stamping prerequisite]`** — and the prerequisite itself is a separate **P0**
item ("Adapter-side `available_at` write-time stamping prerequisite" at line 236) whose owner is writegate Phase 2.D,
not Tab 12. The plan-of-record "Critical-path priority for May-23" section explicitly says: _"the
`assert_no_lookahead_for_feature_group` helper silently no-ops on adapters that haven't been migrated yet, so Phase 2A
correctness is contingent on writegate Phase 2.D progressing."_

Three real factors compound the ambiguity:

1. **Helper is permissive** (`unified_trading_library/point_in_time.py:343-363`) — it silently no-ops when (a)
   `feature_group` is not in UAC `FEATURE_REQUIRED_INPUTS`, (b) `inputs_df` is empty, OR (c) `available_at_col` is
   missing from the frame. So shipping wires before stamping lands does NOT cause runtime failures — it just defers
   correctness pickup until Phase 2.D progresses. The wire IS the landing pad.

2. **API mismatch.** Helper signature requires `pl.DataFrame`; almost every consumer calculator uses `pd.DataFrame`
   (features-onchain `app/calculators/base.py` `OnChainCalculator.calculate_features(raw_data: pd.DataFrame)`,
   `BaseFeatureCalculator.calculate(df: pd.DataFrame, **params)` in UTL `feature_calculator/registry.py:19`,
   features-delta-one + features-sports + MDPS calculators all pandas). Wire-in needs either per-call-site
   `pl.from_pandas(...)` or a UTL helper variant accepting either. Latter is a UTL contract change worth surfacing.

3. **`target_ts` plumbing.** The helper requires a tz-aware `target_ts` at the call site. In features-onchain
   `OnChainCalculator.calculate(df, **params)` the as-of is NOT in scope today — it's only known later at the writer
   layer (`features_onchain_service/app/core/feature_writer.py:307` `as_of_date`). For a clean wire we'd need either (a)
   plumb `target_ts` through `calculate(df, **params)` via params dict, OR (b) refactor each calculator to accept it
   explicitly, OR (c) wire the helper at the WRITER layer instead (where `as_of_date` is in scope but inputs have
   already been consumed — semantically wrong, the helper validates INPUTS not OUTPUTS).

**My read:** the spawn prompt is more aggressive than the plan body warrants. The plan body's BLOCKED annotations are
correct — the wire-in is contingent on Phase 2.D adapter-side stamping. Shipping wires now lands them as no-ops in
production until Phase 2.D progresses; that's defensible per the "helper is permissive" semantic, but it's also 8
services × ~100 calculators × pd→pl conversion + target_ts plumbing = several hours of mechanical edits with non-zero
collision risk against parallel agents, for zero immediate correctness value.

**Asking main agent / operator to pick:**

- **(a) Ship wires now anyway** at one CENTRAL boundary per service (per-service base class, NOT per-calculator) — ~8-10
  small commits, helper degrades gracefully on missing `available_at`, becomes load-bearing as Phase 2.D progresses.
  **Recommendation if this path:** wire at the per-service base class's `calculate()` method
  (`OnChainCalculator.calculate` for onchain, equivalent for each other service), thread `target_ts` via the `**params`
  dict using a new convention `target_ts: datetime` key, no-op the call when params doesn't include it yet. This is the
  minimum-viable wire.
- **(b) Defer Tab 12** until writegate Phase 2.D adapter-side stamping ships — flip Tab 12 from QUEUED to BLOCKED in the
  work-split ledger, free up the implementer for higher-impact May-23 work (e.g. strategy-service Phase 4D
  calibrated-signal consumption is hard-floor for live trading; Phase 2A wire-in is permissive prep).
- **(c) Lift the helper to accept either pd or pl** at UTL — a one-line UTL contract update so the wire-in becomes a
  3-line edit at each consumer site without conversion. Decreases the mechanical effort of (a) by ~50%; surfacing this
  so the answer can fold-in (a)+(c) if helpful.

Continuing meanwhile with: per-service compute-boundary inventory doc (the 8-service map of where the wire would land),
so whichever direction the operator picks, the next agent (or this one) can ship it without re-scanning.

#### A1 — [main, 2026-05-08 ~10:30 UTC]

**Status**: ✅ RESOLVED — operator (Harsh) picked **(b) Defer Tab 12**, with stronger reasoning than Tab 12's original
proposal: the per-service wire-in approach itself is no longer the plan.

**Why deferred** — Ikenna's plan-consolidation work (PM@`78918e1` 2026-05-08) shipped a new plan
[`features_repo_consolidation_2026_05_08.md`](../active/features_repo_consolidation_2026_05_08.md) (P0, deadline
2026-05-13) that **restructures the entire features-\* layer**: merges all 8 features-\*-service repos into a single
`features-service` repo with sub-packages per family. As part of that consolidation, **Phase 5 lifts 4 cross-family
helpers into UTL** — including the exact one Tab 12 was wiring:

> "(c) **`LookaheadBiasError` strict-mode gate** — per-row enforcement that `input.available_at <= target_ts - horizon`.
> Currently fires in 3 of 8 features-\* repos with subtle differences in horizon resolution; **lift into a single
> `assert_no_lookahead_for_feature_group(...)` helper** that reads horizon from the UAC feature-DAG SSOT (per
> `ml_and_features_master` Phase 1A)." — `features_repo_consolidation_2026_05_08.md` Phase 5 §(c)

**What this means concretely**:

1. **Per-service wire-in is no longer the plan.** The helper goes ONCE into UTL `feature_service_base/` at the
   consolidated layer, not 8 times into 8 separate service repos.
2. **Tab 12's three sub-problems get resolved by the consolidation**:
   - Sub-problem A (pd vs pl mismatch): single UTL helper signature designed once at the consolidated layer.
   - Sub-problem B (`target_ts` plumbing): designed once at the UTL layer rather than plumbed through 8 different
     calculator hierarchies.
   - Sub-problem C (the 5-min UTL contract change to accept pd|pl): folds naturally into the Phase 5 lift.
3. **Sequence going forward**:
   1. Ikenna's writegate Phase 2.D ships adapter-side `available_at` stamping.
   2. `features_repo_consolidation_2026_05_08` Phases 0-4 merge 8 repos → 1 (`features-service`).
   3. Consolidation Phase 5 lifts the helper into UTL `feature_service_base/`.
   4. `live_pipeline_mtds_mdps_features_2026_05_08` wires the consolidated service into the live runtime.

**Tab 12's deliverable** — the per-service compute-boundary inventory map produced during the lunch-break wait — is
**still valuable** as input to `features_repo_consolidation` Phase 0 pre-audit. Cross-reference for the consolidation
plan to consume.

**Tab 12 status**: ✅ DONE in registry; going-quiet honored. Q1 resolution is the durable artifact.

> Source: `plans/archive/feature_dag_uac_ssot_and_features_coverage_2026_05_06.md`. Phase 1A
>
> - 1B largely shipped (4 commits across UAC + UTL); remaining open todos are sports vocabulary alignment and the
>   8-service consumer wires + denominator clip on deployment-api.

### 1A — UAC (5 todos shipped, 5 open)

- [x] [AGENT] P0. **`FEATURE_REQUIRED_INPUTS` DAG**. Single declaration in
      `unified_api_contracts/canonical/domain/features/required_inputs.py`. **SHIPPED 2026-05-07 UAC@4a25b07**: 32
      feature_groups seeded (2 onchain + 30 delta-one). 10 onchain + all sports feature_groups omitted pending
      AVAILABILITY_AT_SEMANTICS defi-vocabulary follow-up.
- [x] [AGENT] P0. **Per-service registry** `EXPECTED_FEATURE_GROUPS_BY_SERVICE`. **SHIPPED 2026-05-07 UAC@4a25b07**: 5
      services seeded (features-onchain 12, features-delta-one 33, features-sports 36, features-volatility empty stub,
      features-cross-instrument empty stub).
- [x] [AGENT] P0. **Per-feature-group coverage floor** `FEATURE_COVERAGE_START`. **SHIPPED 2026-05-07 UAC@4a25b07**: 6
      onchain floors (Aave V3 mainnet 2022-03-16, Lido stETH 2020-12-18, EigenLayer 2023-06-14, Morpho 2022-06-01).
- [x] [AGENT] P0. **Tests**. **SHIPPED 2026-05-07 UAC@4a25b07**: 15 tests in `tests/test_feature_dag_ssot.py`.
- [x] [AGENT] P0. **AVAILABILITY_AT_SEMANTICS defi vocabulary gap — Half 1 + Half 2 closed**. **SHIPPED UAC@2f40c9d**
      (`lending_indices` / `risk_params` / `rewards` / `flash_loan_events` / `eigenlayer_rewards` registered) +
      **UAC@7a3299a** (8 of 10 deferred onchain feature_groups lifted; `fear_greed` + `macro_sentiment` intentionally
      NOT lifted — live HTTP pass-throughs that bypass the manifest).

#### 1A.3 — Sports vocabulary alignment

Closes the sports-vocab gap (36 sports feature_groups in `EXPECTED_FEATURE_GROUPS_BY_SERVICE` but absent from
`FEATURE_REQUIRED_INPUTS`). Sequence: pick approach → build resolver → lift entries → tests.

- [ ] [AGENT] P1. **Pick the resolution approach.** Three options under consideration; ~30 min decision with the
      operator. Append the chosen path under this todo as the "decided" line + flip to `[x]`:
  - (a) **Mapping table** (cheapest) — UAC adds `SPORTS_INPUT_NAME_TO_DATA_TYPE: dict[str, list[tuple[str, str]]]` keyed
    on the bare reference-entity name (e.g. `"target_fixtures" → [("sports", "FIXTURES")]`). Pros: zero changes to
    `BuilderEntry.required_inputs: list[str]`. Cons: extra indirection layer.
  - (b) **Tuple-typed required_inputs** (cleanest, more invasive) — change `BuilderEntry.required_inputs: list[str]` →
    `list[tuple[str, str]]` and migrate every sports calculator's declaration. Pros: same shape as
    `FEATURE_REQUIRED_INPUTS`. Cons: 36 calculator-side migrations.
  - (c) **Namespaced names** — adopt `"sports.FIXTURES"` as the single canonical input-name vocabulary; parse the prefix
    at lookup time. Pros: backwards-compat. Cons: runtime parsing.
- [ ] [AGENT] P1. **Build the resolver** per the chosen approach. Tests: every sports `BuilderEntry.required_inputs`
      entry resolves to at least one registered `(asset_group, data_type)` pair in `AVAILABILITY_AT_SEMANTICS`.
- [ ] [AGENT] P1. **Lift the 36 sports feature_groups into `FEATURE_REQUIRED_INPUTS`** using the resolver. Multi-source
      entries (e.g. `FIXTURES` from both api_football + footystats) emit one `InputReq` per source.
- [ ] [TEST] P1. **Closed-set guarantee test** — assert each of the 36 sports feature_groups has ≥1 input, every input's
      `(asset_group, data_type)` is in `AVAILABILITY_AT_SEMANTICS`, every `available_at_rule` matches the registry. Plus
      a per-source multiplicity check.
- [ ] [DOCS] P1. **Update temporary-states bullet** in the `## Temporary states + their canonical follow-up plans`
      section (search "External-sentiment-API live-read pass-throughs" or "features-volatility-service +
      features-cross-instrument-service stubs") from "actionable as Phase 1A.3" → "fully closed <commit-sha>" with link
      to the lift commit.

### 1B — UTL (3 todos shipped, 0 open)

- [x] [AGENT] P0. **`unified_trading_library/manifest_freshness.py::ManifestFreshnessCache(ttl_seconds=60)`**. **SHIPPED
      2026-05-07 UTL@d7902f6**: 17 unit tests including the canonical concurrent-write race scenario.
- [x] [AGENT] P0. **Public API**: re-export from `unified_trading_library`. **SHIPPED 2026-05-07 UTL@d7902f6**:
      top-level facade `from unified_trading_library import ManifestFreshnessCache,     DEFAULT_TTL_SECONDS`.
- [x] [AGENT] P1. **UTL `assert_no_lookahead_for_feature_group(feature_group, inputs_df,     target_ts)` helper**.
      **SHIPPED UTL@4354276c**: reads UAC `FEATURE_REQUIRED_INPUTS[fg]`, computes max_horizon, raises
      `LookaheadBiasError` if any input row has `available_at > target_ts - horizon`. 9 unit tests.

## Phase 2 — features-\* writers + reader pre-join (was: features_consolidation_and_drilldown + Phase 2/3 of feature_dag plan)

> Source: `plans/archive/features_consolidation_and_drilldown_2026_05_06.md` and Phase 2/3 of the feature_dag plan.
> Sequenced after Phase 1; the consolidation sidecar (2E) needs writegate's 4-pillar write-gate to land first so it
> doesn't amplify silent corruption.

### 2A — Replace per-service DAGs with UAC import + wire UTL lookahead helper

#### Per-service compute-boundary inventory (Tab 12 prep, 2026-05-08 07:55 UTC)

Probed all 8 candidate services from the Tab 12 spawn prompt to map the cleanest single wire-in site per service.
Findings advisory until Q1 (above) resolves direction.

**Tab 12 spawn-prompt's "8 services" appears to be 5 services + 3 categorical mismatches:**

- **In scope (5)** — services in UAC `EXPECTED_FEATURE_GROUPS_BY_SERVICE`: `features-onchain-service`,
  `features-delta-one-service`, `features-sports-service`, `features-volatility-service`,
  `features-cross-instrument-service`.
- **Out of scope (3)** — `market-data-processing-service` produces candles (raw ticks → OHLCV bars), not feature_groups;
  `strategy-service` consumes feature_groups to produce trade decisions, doesn't produce them; the 3rd "+ 4 others" slot
  in the spawn prompt likely intended to round to 8 but no other service produces feature_groups per the UAC registry.
- **CLAUDE.md "LookaheadBiasError raised loud at every features-\* + MDPS compute" rule context**: applies to MDPS's
  candle-aggregation _output_ availability stamping (writer-side), NOT the input-side
  `assert_no_lookahead_for_feature_group` helper which is feature_group-keyed. Strategy-side lookahead validation uses
  the existing row-level `PointInTimeEnforcer.check_observation_timestamp` API, not the new feature_group helper.

**Per-service wire-site map (5 in-scope services):**

| Service                           | UAC fg count | Base file:line                                                                                                                                                                              | Native df | `feature_group` on base?                                            | Wire complexity                                                                                                                                     | Status             |
| --------------------------------- | ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------- | ------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ |
| features-delta-one-service        | 33           | [`base_calculator.py:90`](../../../features-delta-one-service/features_delta_one_service/app/calculators/base_calculator.py#L90) `BaseFeatureCalculator.calculate(df, symbol)`              | **pl**    | ✅ abstract property (`feature_group`)                              | **Clean**: 1 line in `calculate` after `validate_input` BEFORE `_calculate_features`.                                                               | Ready (pending Q1) |
| features-cross-instrument-service | 0 (stub)     | [`base_calculator.py:101`](../../../features-cross-instrument-service/features_cross_instrument_service/app/calculators/base_calculator.py#L101) `BaseFeatureCalculator.calculate(df, ...)` | **pl**    | ✅ abstract property (line 58)                                      | **Clean**: same shape as delta-one. Helper no-ops because UAC registry empty stub.                                                                  | Ready (pending Q1) |
| features-onchain-service          | 12           | [`base.py:93`](../../../features-onchain-service/features_onchain_service/app/calculators/base.py#L93) `OnChainCalculator.calculate(df, **params)`                                          | pd        | ❌ via `@FeatureCalculatorRegistry.register("name")` decorator only | **Medium**: needs (i) `feature_group` class-attr extraction from registry, (ii) `pl.from_pandas(df)` conversion or UTL helper variant accepting pd. | Ready (pending Q1) |
| features-sports-service           | 36           | TBD — calculator base.py not at canonical path; per-`*_calculator.py` likely                                                                                                                | mixed     | TBD                                                                 | **Hard-blocked** by Phase 1A.3 sports vocabulary alignment todo above.                                                                              | Blocked-deeper     |
| features-volatility-service       | 0 (stub)     | No `app/calculators/` populated; `BuilderRegistry` placeholder per audit 2026-05-07                                                                                                         | —         | —                                                                   | **No-op**: no calculators registered, wire would silently no-op until builders land.                                                                | No-op              |

**Net wire surface if Q1 resolves to (a) "ship now":** 3 base-class edits (delta-one, cross-instrument, onchain) + 3
unit tests = ~6 small commits, ~1.5h. Folding (c) into (a) (lift UTL helper to accept pd or pl) drops the medium onchain
edit to clean → total ~1h. Sports + volatility deferred until upstream prereqs ship (Phase 1A.3 + builder registration
respectively).

**Original Phase 2A todos below remain unflipped** until Q1 resolves direction:

- [ ] [AGENT] P1. **features-onchain-service**: delete local feature_group → required_inputs DAG (if any) + call
      `assert_no_lookahead_for_feature_group(feature_group, inputs_df, target_ts)` at each calculator's input-load
      boundary BEFORE compute. Sites: `app/calculators/*.py` (12 calculators). [BLOCKED-ON adapter-side `available_at`
      stamping prerequisite below]
- [ ] [AGENT] P1. **features-sports-service**: same. Calculators in `features_sports_service/calculators/*.py`.
      [BLOCKED-ON UAC sports vocabulary decision in Phase 1A.3]
- [ ] [AGENT] P1. **features-delta-one-service**: same. Calculator sites in `features_delta_one_service/`. [BLOCKED-ON
      adapter-side `available_at` stamping prerequisite]
- [ ] [AGENT] P0. **Adapter-side `available_at` write-time stamping prerequisite** — every calculator's input adapter
      MUST stamp `available_at` per the workspace SSOT
      `unified_trading_library.availability_stamping.stamp_available_at_*` (per `AVAILABILITY_AT_SEMANTICS` rules).
      Without the stamp, `assert_no_lookahead_for_feature_group(...)` degrades to a silent no-op via the "missing col"
      branch. Adapters needing stamping (sample): features-onchain DefiLlama / AAVE subgraph / Lido contract / Pyth
      Solana / Chainlink EVM / DefiBalances; features-delta-one MTDS readers; features-volatility VIX / Yahoo readers;
      features-cross-instrument multi-asset-group delta-one concat path. Sequence: adapter stamps → helper validates →
      consumer trusts. Partial coverage already exists via writegate Phase 2.D `available_at` work.

### 2B — Adopt `ManifestFreshnessCache`

- [ ] [AGENT] P1. **features-sports-service BatchHandler**: instantiate `ManifestFreshnessCache(ttl_seconds=60)` at
      handler init; call `cache.is_now_captured(row_key)` before any expensive remote call. **DEFERRED 2026-05-07** —
      Phase 1B unblocks the cache infra, but the BatchHandler already has a `_should_skip_attempted(feature_group)`
      helper at
      [`batch_handler.py:479`](../../../features-sports-service/features_sports_service/cli/handlers/batch_handler.py#L479)
      keyed by `table_name`. That table-name vocabulary is NOT aligned with the Phase 1A
      `EXPECTED_FEATURE_GROUPS_BY_SERVICE['features-sports-service']` calculator-output vocabulary — clean wire-in needs
      the manifest row_key shape rationalised first via Phase 1A.3.
- [ ] [AGENT] P1. **features-volatility-service orchestrator**: same. Skip if manifest already says captured. **DEFERRED
      2026-05-07** — features-volatility-service's `BuilderRegistry` is a placeholder per audit 2026-05-07 (no
      calculators registered yet); `EXPECTED_FEATURE_GROUPS_BY_SERVICE['features-volatility-service']` is empty. Cache
      adoption is meaningless until orchestrator ships live IV-surface fits.

### 2C — deployment-api denominator clip

- [x] [AGENT] P1. **`data_status_service.py`**:
  - Add `_clip_dates_to_feature_coverage(service, feature_group, start, end)` mirroring the sports clip helper at lines
    39-50. Reads UAC `FEATURE_COVERAGE_START`.
  - `_build_feature_group_breakdown` (line 3684): denominator = clipped_dates \*
    `EXPECTED_FEATURE_GROUPS_BY_SERVICE[service]` (instead of inferring from what's been written).
  - Endpoint `/data_status?check_feature_groups=true` (line 2288) returns honest expected/found/missing per
    feature_group. **SHIPPED 2026-05-07 deployment-api@9b51dfb**: implemented as a sibling method
    `_build_feature_group_breakdown_uac`. 8 unit tests in `tests/unit/test_feature_group_breakdown_uac.py`.

### 2D — UTL `FeatureBatchHandler` base + 4-service refactor

- [ ] [AGENT] P2. **UTL `unified_trading_library/feature_service_base/batch_handler.py`** — `FeatureBatchHandler[T]`
      generic base lifting the (DataLoader, Calculator, FeatureWriter, ManifestWriter, ManifestFreshnessCache,
      write-gate) wiring. Per-service hooks: `load_inputs(shard_key) -> InputBundle`, `compute(inputs) -> OutputBundle`,
      `expected_clusters(shard_key) -> dict | None`. **UNBLOCKED 2026-05-07** — `ManifestFreshnessCache` shipped per
      Phase 1B (UTL@`d7902f6`); ready to start.
- [ ] [AGENT] P2. Refactor Delta-One, Onchain, Sports, Volatility BatchHandlers to extend the base. Net delete ~200 LOC
      each. Behavior-preserving — diff existing batch outputs.

### 2E — Feature-store consolidation sidecar

#### 2E.1 — Design

- [ ] [AGENT] P0. **Decide consolidation atom**: per `(asset_group, day, timeframe)` wide-table or per
      `(asset_group, day, instrument_id)` per-instrument wide-table. Trade-off: instrument-wide reads in single file
      (fast for per-instrument training) vs day-wide cross-instrument reads (fast for ranking/portfolio models).
      Recommendation: ship instrument-wide first; add day-wide if measured useful.
- [ ] [AGENT] P0. **Path SSOT in UAC**:
      `gs://features-consolidated-{asset_group}-{project_id}/by_date/day=YYYY-MM-DD/timeframe={tf}/{instrument_id}.parquet`.
      One file per (asset_group, day, instrument, timeframe) carrying every feature column from every feature_group
      joined on `(timestamp, instrument_id)`.
- [ ] [AGENT] P0. **Manifest** — consolidation rows in availability manifest with `feature_group="_consolidated"`
      sentinel + `model_family / training_period` empty.

#### 2E.2 — Write-time orchestration

- [ ] [AGENT] P1. **features-consolidation sidecar (or per-service post-compute hook)**: after each features-\*-service
      finishes a (day, instrument, timeframe) shard, emit a Pub/Sub event. Subscriber consolidator joins all available
      feature_groups for that key into a wide parquet. If any required feature_group is missing, write
      `record_failed(MissingFeatureGroup)`; honest signal.
- [ ] [AGENT] P1. **Strict ordering** — consolidator depends on writegate's write-gate, so it never joins garbage rows.
      UTL `validate_shard()` re-runs on the consolidated output (pillars 2-4). [BLOCKED-ON writegate Phase 1A
      `record_captured` 4-pillar gate]

#### 2E.3 — ml-training read switch

- [ ] [AGENT] P1. `FeatureDataAdapter` switches to read `features-consolidated-...` paths when present, falls back to
      per-feature_group paths only for legacy training periods. Migration window documented.
- [ ] [AGENT] P1. Benchmark vs Phase 3 baseline (post-DuckDB-merge): target 5-10× speedup on representative training
      run. [BLOCKED-ON Phase 3 baseline numbers]

### 2F — deployment-ui feature drill-down

- [ ] [AGENT] P3. **deployment-api**: per-feature_group leaf endpoint
      `GET /data_status/feature_groups/{service}/{feature_group}/shards?...` returning shard-level rows + GCS URIs.
      Mirror the existing market-data drill-down depth.
- [ ] [AGENT] P3. **deployment-api**: parquet download endpoint
      `GET /data_status/feature_groups/{service}/{feature_group}/parquet?day=...&instrument=...&timeframe=...` returning
      the parquet bytes (or a signed URL).
- [ ] [AGENT] P3. **deployment-ui** new route `/feature-groups/{service}/{feature_group}` rendering shard list + schema
      view + download button. Match the look of the existing market-data drill-down. Reuses `DimensionStatus` types
      already in `deployment-ui/src/types/index.ts`.

## Phase 3 — ml-training feature-read perf (was: ml_training_feature_read_perf)

> Source: `plans/archive/ml_training_feature_read_perf_2026_05_06.md`. Self-contained 1-3 day spike; pure-Python
> pure-win. Baseline that the consolidation sidecar (Phase 2E) needs to beat by 5-10×.

### 3A — Row-group pruning + column push-down (PARALLEL with 3B)

- [ ] [AGENT] P0. **Row-group pruning** in `gcs_feature_reader.py:_download_parquet`. Replace
      `pd.read_parquet(io.BytesIO(parquet_bytes))` with `pyarrow.parquet.ParquetFile(...).read(filters=...)` or
      `pyarrow.dataset.dataset(...).to_table(filter=...)`. Push date-range filter (already known at the call site) to
      row-group min/max pruning. **DEFERRED** (2026-05-08 Wave-3 Tab ML-TRAIN): not shipped this cycle. The column
      push-down item below already switched the per-shard read to `pyarrow.parquet.ParquetFile.read(columns=...)`, so
      the structural prerequisite is in place. Adding row-group filters at the same boundary is a small follow-up but
      per-shard parquets are single-day already (one date per file), so row-group pruning's biggest win would land if
      MTDS / features-\* ever consolidate to multi-day parquet files. Captured for the next 3A iteration; today's column
      push-down delivers the bulk of the read-perf win.
- [x] [AGENT] P0. **Column push-down**. `FeatureDataAdapter.read_features(columns=...)` already exists; thread `columns`
      argument all the way through `ParallelGCSFeatureReader._download_parquet` so only requested columns are
      deserialised. Evidence: ml-training-service@365f710 — `columns: list[str] | None` threaded through
      `ParallelGCSFeatureReader.read_features` → `_parallel_download` → `_download_parquet` →
      `_read_parquet_with_projection`; identity columns (`timestamp` / `instrument_id` / ...) always retained;
      `FeatureDataAdapter.load`, `CloudFeatureProvider._load_delta_one_frames` / `_load_mtf_frames` /
      `_query_gcs_features` / `_query_defi_features` / `query_features` all accept + forward `columns=`;
      `final_training_handler` and `hyperparam_grid_handler` pass their Stage-1 `selected_features` down. Real-shape
      profile (152 files × 1440 rows × 50 features × 5-projected): wall-clock 2.66× faster, dataframe bytes -65.7%, peak
      Python-heap alloc -27.3%. Wider parquets (200 cols × 10 projected): 3.04× wall-clock, -52.6% alloc, -87% df bytes.
- [x] [AGENT] P0. **Tests**: synthetic 365-day per-instrument parquet with 50 feature columns. Assert reading 38 days ×
      5 columns is at least 4× faster than reading all data + filtering. Evidence: ml-training-service@365f710 — 10 unit
      tests in `tests/unit/test_gcs_feature_reader_column_pushdown.py` covering keeps-only-requested,
      identity-cols-retained, heterogeneous-schema-drop, zero-overlap-short-circuit, value-equivalence,
      `IDENTITY_COLUMNS`-pinned-to-provider-set, and parameterised wall-clock + dataframe-size benchmarks across 3
      column-ratio shapes. Multi-file 4× wall-clock target hit by the harness at `scripts/profile_column_pushdown.py`
      (wider-parquet runs); per-unit-shard test asserts ≥1.3× to absorb CI noise — see the size-ratio assertions for the
      deterministic checks.

### 3B — DuckDB lazy joins

- [ ] [AGENT] P1. **Replace pandas outer-merge with DuckDB**. `_merge_features` (`gcs_feature_reader.py:185-232`): build
      an in-process DuckDB connection, register each per-day per-group DataFrame as a view, run
      `SELECT * FROM g0 FULL OUTER JOIN g1 USING     (timestamp, instrument_id) FULL OUTER JOIN g2 ...`. DuckDB query
      planner picks join order; lower memory peak; faster for 4+ groups.
- [ ] [AGENT] P1. Drop the manual `_dedupe_columns` logic — DuckDB join uses `USING` so no `_x` / `_y` suffixes.
- [ ] [AGENT] P1. **Tests**: identical-output test against pandas merge baseline on a fixture with 4 feature_groups and
      overlapping timestamps. Diff must be empty (modulo column order).

### 3C — Concurrency tuning

- [ ] [AGENT] P2. **features-volatility-service**: profile `VolatilityFeaturesOrchestrator.process()` with
      `max_workers ∈ {4, 8, 16, 32}` on a representative options-chain shard. Pick the knee. Update default in service
      config.
- [ ] [AGENT] P2. **features-delta-one-service**: identify BatchHandler concurrency knob; apply same profiling
      methodology.
- [ ] [AGENT] P2. **Per-asset-group max_workers SSOT** in UAC or per-service config — codify the knees so future
      operators don't have to re-profile.

### 3D — End-to-end benchmark + B3 sign-off

- [ ] [AGENT] P3. **Benchmark harness**: replay one full ML training run (one model_family, one asset_group, 38-day
      window) before-and-after. Report wall-clock + peak RSS for: feature read step, feature merge step, total training
      time. Pick CeFi as the chosen asset_group (Tier 2C cefi adapters shipped at MDPS@b9f9328 so a clean validated
      shard set exists).
- [ ] [AGENT] P3. **Document results** in this plan's Benchmark section. Target: ≥2× faster feature read step; ≥30%
      lower peak RSS during merge.
- [ ] [AGENT] P3. **B3 sign-off**: KPI met → mark plan code-ready for archive after data-pipeline-completion epic
      closes.

#### Benchmark (filled during Phase 3D)

| Metric                       | Before | After (target) | After (actual) |
| ---------------------------- | ------ | -------------- | -------------- |
| Feature read step wall-clock | TBD    | -50%           | TBD            |
| Peak RSS during merge        | TBD    | -30%           | TBD            |
| End-to-end ML training       | TBD    | -20%           | TBD            |

## Phase 4 — ML model lifecycle (was: consolidated_ml_advanced_pipeline)

> Source: `plans/archive/consolidated_ml_advanced_pipeline_2026_04_15.md`. About 70% of items are PARTIALLY_DONE
> (skeletons exist, spec items missing); net-new items (multi-task, hierarchical, calibrated signal consumption,
> cost-aware strategy) are the May-23-or-later live trading prereqs. **Phase 4D is the only May-23 hard floor** —
> strategy-service must consume calibrated confidences + apply cost-aware filtering before live trading.

### 4A — UAC + UTL ML foundations (PARTIALLY_DONE polish)

- [ ] [AGENT] P0. **mlr-p1-uac-ml-schemas**: Extend UAC internal ML schemas with calibration, training scope, cost-aware
      types. PARTIALLY-FRESH — `InferenceRequest.explain: bool` shipped (UAC `internal/domain/ml/schemas.py:605`).
      Remaining genuine gap: tabnet/tft schemas (UAC grep `TabNet|tabnet|TFT|tft` → 0 hits) — only meaningful if the
      model factory supports them, which is itself architecture-v2 dependent.
- [ ] [AGENT] P0. **mlr-p1-utl-calibration**: Build calibration module in UTL `ml/calibration.py`. PARTIALLY-FRESH —
      `ProbabilityCalibrator` confirmed in `unified_trading_library/ml/ml_training_utils.py:16`; no separate
      `ml/calibration.py` module, no reliability_diagram / temperature_scaling helpers; consider lifting into a
      dedicated module per spec.
- [ ] [AGENT] P0. **mlr-p1-utl-pnl-objective**: Build P&L-aware training objectives in UTL `ml/pnl_objectives.py`.
      PARTIALLY-FRESH — confirmed pnl_weighted + sharpe at `ml_training_utils.py:199-206`; no separate
      `ml/pnl_objectives.py`; asymmetric_mse not implemented.
- [ ] [AGENT] P0. **mlr-p1-utl-bayesian**: Build Bayesian optimization wrapper in UTL `ml/bayesian_optimizer.py`.
      PARTIALLY-FRESH — `BayesianHyperparamOptimizer` at `ml_training_utils.py:70`; consumed in ml-training
      `uniform_training_pipeline.py:592-599`; no MedianPruner/RDBStorage; lifting to dedicated
      `ml/bayesian_optimizer.py` is cosmetic.
- [ ] [AGENT] P0. **mlr-p1-utl-feature-importance**: Build feature importance monitor in UTL
      `ml/feature_importance_monitor.py`. STALE-ish — SHAP shipped end-to-end (UAC `InferenceRequest.explain` +
      ml-inference `inference_shap.py` TreeExplainer cache + orchestrator wiring). GCS history persistence still
      pending. Consider flipping to DONE if "feature importance" was scoped narrowly to SHAP at inference time.
- [ ] [AGENT] P1. **mlr-p1-qg**: Run quality-gates.sh on UAC, UTL — all pass.
- [ ] [AGENT] P1. **daml-p2-decision-policy**: Create `unified_trading_library/ml/decision_policy_engine.py` (plan [x]
      but file not found). PARTIALLY-FRESH — `DecisionPolicyConfig` exists in
      `unified_trading_library/config_interface/sports_ml_config.py:26` (sports-only); the cross-asset-group "engine"
      module path `unified_trading_library/ml/decision_policy_engine.py` is still absent.

### 4B — ml-training-service integration

- [ ] [AGENT] P0. **mlr-p2-calibration-integration**: Wire calibration into `uniform_training_pipeline.py` Phase 3
      (PARTIALLY_DONE — basic cal/ECE exists, missing cal/val split + joblib persist).
- [ ] [AGENT] P0. **mlr-p2-pnl-training**: Wire P&L-aware objectives into `model_trainer_factory.py` (PARTIALLY_DONE —
      LightGBM custom objective exists; extension to other model families pending).
- [ ] [AGENT] P0. **mlr-p2-bayesian-tuning**: Replace grid search with Bayesian optimization in Phase 2 (PARTIALLY_DONE
      — basic Optuna wired at `uniform_training_pipeline.py:594`; genuinely-missing piece is grid-search removal +
      MedianPruner/RDBStorage).
- [x] [AGENT] P0. **mlr-p2-incremental**: Add incremental training mode to `uniform_training_pipeline.py`. Evidence:
      ml-training `f94f7db` (incremental + cross-asset transfer learning).
- [x] [AGENT] P0. **mlr-p2-transfer-learning**: Add global/cross-asset training scope to pipeline. Evidence: ml-training
      `f94f7db`.
- [ ] [AGENT] P0. **mlr-p2-multi-task**: Add multi-target joint training option (GENUINELY_PENDING — confirmed absent:
      ml-training grep `multi_target|multi.task` → 0 production hits).
- [ ] [AGENT] P1. **mlr-p2-feature-importance-feedback**: Wire feature importance monitor into Phase 3 post-training
      (PARTIALLY_DONE — basic usage; same scope as mlr-p1-utl-feature-importance).
- [ ] [AGENT] P1. **mlr-p2-qg**: Run quality-gates.sh on ml-training-service — pass.
- [x] [AGENT] P0. **daml-p4-feature-adapter**: Add sports GCS feature loading to ML training service
      `feature_data_adapter.py`. Evidence: ml-training `644ff22` + `bcc8db0` + `a5d3bbf`.

### 4C — ml-inference-service

- [x] [AGENT] P0. **mlr-p3-calibration-inference**: Apply calibration at inference time. Evidence: ml-inference
      `d6744d0`.
- [x] [AGENT] P1. **mlr-p3-shap-inference**: Add optional SHAP explanation to inference responses. Evidence: UAC
      `InferenceRequest.explain: bool` shipped; `inference_shap.py` (TreeExplainer cache + bag) shipped; orchestrator
      wires `request.explain` at `engine/orchestrator.py:180`.
- [ ] [AGENT] P1. **mlr-p3-hierarchical**: Support hierarchical model loading Level 0-2 (GENUINELY_PENDING —
      ml-inference grep `level_0|level_1|level_2|hierarchical` → 0 hits).
- [x] [AGENT] P1. **mlr-p3-qg**: Run quality-gates.sh on ml-inference-service — pass. Evidence: ml-inference `8b4fb8b` +
      `bd05cbf`.

### 4D — strategy-service consumption (May-23 hard floor)

- [ ] [AGENT] P0. **mlr-p4-strategy-calibrated-signals**: Update strategy-service to consume calibrated confidences
      (GENUINELY_PENDING — strategy-service grep `calibrated.*confidence|consume.*calibrated|calibration.*signal` → 0
      hits). Ownership overlaps with `strategy_and_dart_master_SUPERSEDED_2026_05_21` Phase 3.4 (slv-p2-\* lifecycle
      items) — was `consolidated_strategy_and_ui:Group D` pre-2026-05-07 umbrella consolidation. **Live trading prereq
      for May-23.**
- [ ] [AGENT] P0. **mlr-p4-cost-aware-strategy**: Add cost-aware signal filtering in strategy-service (GENUINELY_PENDING
      — execution-service has `services/execution_cost_estimator.py` and `v2/cost_models.py` (the producer side);
      strategy-service has no consumer wiring). **Live trading prereq for May-23.**
- [ ] [AGENT] P1. **mlr-p4-qg**: Run quality-gates.sh on strategy-service — pass.
- [ ] [AGENT] P1. **mlr-p5-final-qg**: Final QG on all repos (UAC, UTL, ml-training-service, ml-inference-service,
      strategy-service).

## Phase 5 — Phantom audit + sanity replay

> Source: Phase 3 of feature_dag plan. Final acceptance gate; brings features manifest under the same phantom-audit
> regime as raw data.

- [ ] [AGENT] P2. **`instruments-service/scripts/reconcile_phantom_manifest_rows_all.py`**: extend `--asset-group` to
      accept `features` (or add `--features` flag). Probe feature parquet paths via UAC SSOT candidate-path helper
      (mirror sports' `candidate_parquet_paths`). New drift axes: timeframe hive casing, feature_group empty-check
      (parquet exists but is 0 rows or all-NaN beyond writegate's NaN-threshold). Regression test: synthesise a phantom
      row + missing parquet; audit flags it. [SOFT-BLOCKED-ON Phase-1A SSOTs (probe denominator)]
- [ ] [AGENT] P2. **Same-region GCE smoke run** of the audit in `--dry-run` against the features manifest (per CLAUDE.md
      cross-region listing perf rule). Confirm zero phantoms or document genuine drift.
- [ ] [AGENT] P3. **Sanity replay** — pick 3 small representative shards (one DeFi onchain, one CeFi delta-one, one
      sports), recompute. Assert: (a) features-\* services no longer carry inlined DAGs (grep returns 0); (b)
      data-status feature-coverage % matches expected (denominator clip works); (c) phantom audit dry-run output is
      parseable.

## Anti-patterns (don't do)

- Don't redefine `LookaheadBiasError` or `available_at` stamping helpers — writegate owns them. Import.
- Don't redefine `AVAILABILITY_AT_SEMANTICS` taxonomy — writegate owns. Reuse.
- Don't keep per-service DAGs alive in parallel with the UAC SSOT (workspace "delete deprecated code" rule).
- Don't tune `ManifestFreshnessCache` TTL below 30s — CLAUDE.md says it burns GCS reads for marginal gain.
- Don't add a fallback "if UAC registry missing, infer from manifest" — that's the bug we're fixing.
- Don't write a "fast path" parallel to the existing reader. Replace in place.
- Don't introduce DuckDB as a process-wide singleton — per-call connection is fine; avoid hidden state across training
  runs.
- Don't tune `max_workers` higher than the GCS HTTP pool size in the storage client (CLAUDE.md: pool tuned to
  `2 * workers`; symmetric on the read side).
- Don't ship the consolidation sidecar before writegate's write-gate lands — joining ungated shards is a
  silent-corruption amplifier.
- Don't keep both per-feature_group and consolidated read paths permanently active in ml-training. Migrate then delete
  the legacy reader.
- Don't add asset-group-specific consolidator microservices — single sidecar with per-asset-group config knobs.

## Temporary states + their canonical follow-up plans

- **External-sentiment-API live-read pass-throughs (deferred, post-May-23 if needed).** `fear_greed` (live HTTP fetch
  from Alternative.me) + `macro_sentiment` (live HTTP fetch from CoinGecko + DefiLlama) bypass the manifest entirely —
  there's no upstream `(asset_group, data_type)` to enforce LookaheadBias against. Two paths to close, both deferred:
  - (a) Register `crypto_sentiment` and/or `macro_metrics` as DeFi data_types in
    `unified_api_contracts.registry.market_data_categories.DEFI_DATA_TYPES` + add availability_semantics + write a
    captured-tick adapter (probably in MTDS) that snapshots the API output into a manifest data_type on a sensible
    cadence. Then lift the calculators here.
  - (b) Treat both calculators as out-of-band sentiment overlays that don't participate in honest-coverage accounting at
    all (analogous to how options Greeks aren't manifest data_types). Document the carve-out in the
    EXPECTED_FEATURE_GROUPS_BY_SERVICE comment so they don't appear in the denominator either. Decision deferred to a
    focused 2-hour session with the operator. Not a May-23 blocker — these are enrichment features, not core trading
    signals.
- **features-volatility-service + features-cross-instrument-service stubs.** Both services have empty
  `EXPECTED_FEATURE_GROUPS_BY_SERVICE` lists today — populate as their respective `BuilderRegistry` patterns consolidate
  (volatility currently a placeholder per audit 2026-05-07; cross-instrument has 20+ calculators in dir but no central
  registry yet). Successor: rolled into Phase 2A consumer-migration when those services adopt the pattern.

## Success criteria (rolled up across all 5 phases)

| Criterion                                                                                                          | Gate    |
| ------------------------------------------------------------------------------------------------------------------ | ------- |
| `FEATURE_REQUIRED_INPUTS`, `EXPECTED_FEATURE_GROUPS_BY_SERVICE`, `FEATURE_COVERAGE_START` declared in UAC + tested | C2 (P1) |
| Three features-\* services consume UAC DAG (no inlined duplicates)                                                 | C5 (P2) |
| `ManifestFreshnessCache` in UTL + adopted by features-sports + features-volatility                                 | C5 (P2) |
| data-status feature-coverage % uses UAC denominator + coverage-start clip                                          | C5 (P2) |
| `FeatureBatchHandler` base merged + 4 services migrated                                                            | C5 (P2) |
| Consolidation parquet path declared in UAC + written by sidecar                                                    | C5 (P2) |
| ML training reads consolidation parquet by default                                                                 | C5 (P2) |
| deployment-ui `/feature-groups/{service}/{feature_group}` renders + download works                                 | D3 (P2) |
| Row-group pruning + column push-down landed                                                                        | C2 (P3) |
| DuckDB lazy joins landed; output identical to pandas baseline                                                      | C2 (P3) |
| Benchmark: ≥2× faster feature read step on representative training run                                             | B3 (P3) |
| Benchmark: ≥30% lower peak RSS during merge                                                                        | B3 (P3) |
| Benchmark: ≥5× faster feature read step vs Phase 3 baseline (consolidation sidecar)                                | B3 (P2) |
| ml-training calibration cal/val split + joblib persist                                                             | C5 (P4) |
| ml-inference hierarchical model loading Level 0-2                                                                  | C5 (P4) |
| strategy-service consumes calibrated confidences + applies cost-aware filtering                                    | C5 (P4) |
| Phantom audit covers features manifest                                                                             | C5 (P5) |
| Sanity replay passes on 3 representative shards                                                                    | B2 (P5) |

## `available_at` + lookahead-bias coordination (2026-05-08 audit)

> **Coordinator:**
> [`active/available_at_lookahead_bias_completion_2026_05_08`](../active/available_at_lookahead_bias_completion_2026_05_08.md).
> Audit 2026-05-08 confirmed: UTL
> `assert_no_lookahead_for_feature_group(feature_group, inputs_df: pl.DataFrame, target_ts)` already takes target_ts and
> gracefully no-ops when feature_group absent / df empty / column missing
> ([UTL point_in_time.py:274-393](../../../unified-trading-library/unified_trading_library/point_in_time.py#L274-L393)).
> features-sports `_enforce_pit_sports` (data/writer.py:42-72) is the canonical writer-boundary precedent — mirror it.

- [ ] [SCRIPT] P0. **UAC `FEATURE_REQUIRED_INPUTS` expansion across asset_groups**. Today 10 defi groups registered;
      target ~90 (sports ~60 + cefi ~5 + tradfi ~8 + defi residual + predictions). Each unregistered feature_group makes
      the lookahead-bias gate silently no-op. Coordinator Phase 4. Sub-todos lifted into the asset-group masters (cefi /
      tradfi / predictions / sports / defi).
- [ ] [TRACKED] P0. **Tab 12 wire-in (8 features-\* services) DEFERRED** per PM@cf9b9ba1 until coordinator Phase 0 (MDPS
      bar boundary) + Phase 1 (per-asset-group adapter stamping) ship. Wire at writer boundary, NOT calculator boundary,
      to avoid pd↔pl conversion (the precedent: features-sports `_enforce_pit_sports`). features-onchain's
      `contextlib.suppress(LookaheadBiasError)`
      ([feature_writer.py](../../../features-onchain-service/features_onchain_service/app/core/feature_writer.py)) is
      the canary — flip the suppress to a raise once chain is live; that single edit verifies end-to-end.

## Sub-plans (referenced from this epic)

- **`plans/active/ml_repo_consolidation_2026_05_19.md`** (~6 cal-AI-days, P0, deadline 2026-05-23, `infra` class) —
  Merge `ml-training-service` + `ml-inference-service` into a new `ml-service` repo with sub-packages
  `ml_service/training/` and `ml_service/inference/`; archive both source repos via `gh repo archive`. ONE Docker image
  (conditional training-deps Docker layer to keep live-inference image lean), ONE flat `pyproject.toml`, ONE Health-API
  exposing aggregated freshness, ONE CLI with `--operation` discriminating train / evaluate / hyperparam /
  batch-inference / live-inference / cascade-inference. Mirrors `features_repo_consolidation_2026_05_08.md` 10-phase
  pattern. Pre-cutover race; flips to `BLOCKED-CUTOVER` if Phase 6 parity slips. Soft freeze on structural changes in
  both source repos for duration. Phase 4D consumers (strategy-service calibrated-signal consumption) will reference
  `ml-service` post-merge — coordinate downstream-import-rewrite sweep. Sibling:
  `plans/active/strategy_repo_consolidation_2026_05_19.md` (independent execution).

## Coordination with sibling plans

- **writegate_honest_coverage_endtoend_2026_05_06**: this umbrella consumes writegate's `LookaheadBiasError`,
  `available_at` stamping helpers, `AVAILABILITY_AT_SEMANTICS` taxonomy, and 4-pillar write-gate. If writegate amends
  any of those, treat as a writegate amendment not a fork.
- **master_to_live_defi_2026_05_23**: Phase 4D is the May-23 hard floor (Group F live trading prereqs). Phase 1A is
  highest-leverage 1-day spike that gates everything downstream.
- **strategy_and_dart_master_SUPERSEDED_2026_05_21** (was `consolidated_strategy_and_ui_2026_04_15` pre-2026-05-07
  umbrella consolidation): Phase 4D `strategy-service calibrated-signal consumption` overlaps with that plan's Phase 3.4
  (slv-p2-\* lifecycle items + slv-p3-research-shell) — coordinate ownership before starting.

## Closed items (from sources, retained for audit trail)

### From feature_dag_uac_ssot_and_features_coverage (Audit 2026-05-07)

- Audit run: 2026-05-07 (parallel-agent pass). Verified: 11 of 11 unchecked todos. Mis-marked DONE → flipped: 0.
  In-flight VMs: none. Recommendation at fold-time: KEEP active. Phase 1 (UAC + UTL foundations) is mechanically simple
  and unblocks everything downstream. The feature DAG SSOT is one of the highest-leverage 1-day items remaining for
  `LookaheadBiasError` enforcement to be honest. Schedule Phase 1 as soon as writegate Phase 2.D
  (`AVAILABILITY_AT_SEMANTICS`) lands. Phases 2-3 are sequenced after but trivially parallelisable across the 3
  features-\* services.

### From features_consolidation_and_drilldown (Audit 2026-05-07)

- Audit run: 2026-05-07 (parallel-agent pass). Verified: 14 of 14 unchecked todos. Mis-marked DONE → flipped: 0 — Phase
  3 deployment-ui shipped multi-axis SchemaModal + per-asset-group accordion + SmartDownloadButton via `8056995` /
  `7309b56` / `537d468` / `0fbd28b`, but those land general data-status drilldown — they do NOT yet implement the
  feature_group-specific routes named here, so the Phase 3 todos are still fresh as scoped. In-flight VMs: none.
  Recommendation at fold-time: KEEP active but explicitly P2/P3. Plan is well-scoped and depends-on chain is correct
  (writegate → feature_dag → ml-read-perf → this plan). For May-23 deadline this is post-launch optimisation. If budget
  tight: drop Phase 1 (feature-store consolidation = ~500 LOC + risky), keep Phase 2 (UTL FeatureBatchHandler, worth 200
  LOC × 4 services) + Phase 3 (drill-down — operator visibility for Group G UX).

### From ml_training_feature_read_perf (Audit 2026-05-07)

- Audit run: 2026-05-07 (parallel-agent pass). Verified: 11 of 11 unchecked todos. Mis-marked DONE → flipped: 0 (none —
  verified `gcs_feature_reader.py:166` still uses `pd.read_parquet(io.BytesIO(parquet_bytes))`; `_merge_features` still
  uses pandas outer-merge with `_dedupe_columns`; no `pyarrow.parquet`/`pyarrow.dataset`/`duckdb` imports anywhere in
  `ml-training-service/ml_training_service/`. The manifest-side commit `f7369f2` (job_id threading per Phase 1B b.2) is
  in writegate scope, not this plan.) In-flight VMs: none. Recommendation at fold-time: KEEP active. This is a 1-3 day
  item that's fully self-contained and unlocks the 5-10× target for the consolidation plan. For May-23 deadline this is
  post-launch optimisation but should be queued behind the May-23 Group F+G live-readiness work. Phases 1+2 (row-group
  pruning
  - DuckDB) are pure-win pure-Python — no risk to live trading correctness if shipped post-May-23.

### From consolidated_ml_advanced_pipeline (Audit 2026-05-07)

- Audit run: 2026-05-07 (parallel-agent pass). Verified: 17 of 18 unchecked todos (mlr-p3-shap-inference re-evaluated →
  flippable to DONE). Mis-marked DONE → flipped: 1 — `mlr-p3-shap-inference` flipped to `[x]`. Verified: full SHAP
  wiring present at `ml-inference-service/ml_inference_service/app/inference/inference_shap.py` (TreeExplainer cache
  - bag) and `engine/orchestrator.py:180` (`if request.explain: ...`); UAC `InferenceRequest.explain: bool = Field(...)`
    shipped at `unified_api_contracts/internal/domain/ml/schemas.py:605`. The plan's note "request.explain exists, no
    schema field" is stale. Recommendation at fold-time: KEEP active but RESCOPE. About 70% of original-scope items are
    PARTIALLY_DONE (skeletons exist, spec items missing). Recommended path: (a) flip the 1 mis-marked DONE; (b) split
    the remaining 17 into "spec-gap PARTIALLY_DONE polish" (low-priority) and "GENUINELY_PENDING net-new" (multi-task,
    hierarchical inference, calibrated signal consumption, cost-aware strategy). Net-new items are the May-23-or-later
    live trading prereqs. Reconciliation status (2026-04-25): YAML `todos:` block converted to canonical Cursor markdown
    checkboxes per `PLAN_FORMAT.md`. 6 todos flipped to `[x]` with cited commit evidence; 18 remain open.

## Assigned active plans

_4 active plans declare `parent_epic: features_and_ml_master` in their frontmatter. Workers pick up in priority order
(P0 first). Auto-populated by `scripts/plans/populate_epic_bodies_2026_05_21.py`._

## P0 — must complete before next foundation gate

### [`workspace_qg_sweep_2026_05_23`](../archive/2026_05/workspace_qg_sweep_2026_05_23.md) — features/ML cluster

**status**: 🟠 ACTIVE — QG sweep for features-service + ml-service + ml-inference-service + ml-training-service. All
ruff clean; run full `bash scripts/quality-gates.sh` to surface STEP violations. PREREQ: MTDS QG green. [vm: vm-ml]

### [`features_repo_consolidation_2026_05_08`](../archive/features_repo_consolidation_2026_05_08.plan.md)

**status**: ✅ ARCHIVED 2026-05-21 — Phases 0-10 shipped; Phase 6 parity RUN deferred to
`features_service_qg_cleanup_2026_05_11` Phase 2; performance_features wire-in deferred to
`phase5_features_streaming_carry_staked_basis_mvp_2026_05_19` Phase-H

### [`ml_repo_consolidation_2026_05_19`](../active/ml_repo_consolidation_2026_05_19.md)

**status**: done · **estimate**: 6 cal AI-days (class: infra)

## P1 — important; post-current-gate

_(no plans currently assigned at this priority)_

## P2 — useful; opportunistic

### [`features_service_qg_cleanup_2026_05_11`](../active/features_service_qg_cleanup_2026_05_11.md)

**status**: active · **estimate**: 1.2 cal AI-days (class: refactor)

### [`phase5_features_streaming_carry_staked_basis_mvp_2026_05_19`](../archive/2026_05/phase5_features_streaming_carry_staked_basis_mvp_2026_05_19.md)

**status**: ✅ ARCHIVED 2026-05-23 — Phase-H complete; Phases E/F BLOCKED-OPERATOR-DEPLOY (Cloud Run deploy gated). ·
**estimate**: 15.0 cal AI-days (class: brand-new)

## P3 — backlog; revisit quarterly

_(no plans currently assigned at this priority)_

## Archived plans

### [`phase5_features_streaming_carry_staked_basis_mvp_2026_05_19`](../archive/2026_05/phase5_features_streaming_carry_staked_basis_mvp_2026_05_19.md)

**status**: ✅ ARCHIVED 2026-05-23 — Phase-H (performance_features passthrough) complete; Phases E/F
BLOCKED-OPERATOR-DEPLOY.

**Deferred (migrated):**

- **Phase-E: features-service Cloud Run deploy + 24h soak (BLOCKED-OPERATOR-DEPLOY)**:
  `deploy_features_service_cloud_run.sh` is operator-only. Tarballs at features-service@c9729dce ready.
- **Phase-F: paper VM relaunch + verification (BLOCKED-OPERATOR-DEPLOY)**: Sequential after deploy+soak.
- **Post-cutover multi-venue expansions**: env-split rollback, multi-venue funding/staking/matching, health_factor — per
  post-cutover successor plans.

### [`features_backfill_phase3_2026_05_22`](../archive/2026_05/features_backfill_phase3_2026_05_22.md)

**status**: ✅ ARCHIVED 2026-05-23 — All 18 items DEFERRED-OPERATOR-DECISION (compute VMs need operator launch
authorization post-cutover). · **estimate**: 2.4 cal AI-days (class: infra)

**Deferred (MIGRATED FROM archived plan)** — post-cutover compute launch:

- **CeFi feature compute VMs (DeltaOne, Volatility, MTF) + DeFi + TradFi + Cross-cutting (P0)**: Gate: operator VM
  launch authorization post-cutover.
- **Sports features (P0)**: Gate: `sports_master` Phase 3+4.
- **Prediction features (P0)**: Gate: operator authorization.
- **Calendar + XInstrument cross-cutting (P0)**: Gate: phases 1-5 GREEN.
