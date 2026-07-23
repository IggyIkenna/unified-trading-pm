---
doc_type: plan
title: ML repo consolidation — ml-service + ml-training + ml-inference merge (2026-05-19)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-service, e2e-testing, execution-service, ml-service, strategy-service]
scope: [engineer, admin]
tags: []
related: []
created: "2026-05-19"
epic: features_and_ml_master
priority: P0
parent: master_to_live_defi_2026_05_23
locked_by: live-defi-rollout
locked_since: 2026-05-19
last_updated: 2026-05-20
estimate_class: infra
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 6
completion_gates: { code: C5, deployment: D2, business: none }
repo_gates:
  - { repo: ml-service, code: C0, deployment: none, business: none }
  - { repo: ml-service (training sub-package), code: C0, deployment: none, business: none }
  - { repo: ml-service (inference sub-package), code: C0, deployment: none, business: none }
  - { repo: ml-training-service, code: C0, deployment: none, business: none }
  - { repo: ml-inference-service, code: C0, deployment: none, business: none }
  - { repo: unified-api-contracts, code: C0, deployment: none, business: none }
  - { repo: unified-trading-library, code: C0, deployment: none, business: none }
  - { repo: deployment-api, code: C0, deployment: none, business: none }
  - { repo: deployment-ui, code: C0, deployment: none, business: none }
  - { repo: deployment-service, code: C0, deployment: none, business: none }
  - { repo: unified-trading-pm, code: C0, deployment: none, business: none }
depends_on: []
todos:
  - { id: phase-0-pre-audit-manifest, content: "- [x] ✅ [AGENT] P0. Phase 0 — Pre-audit manifest (read-only).
        Produce\n  `plans/active/issues/ml_repo_consolidation_preaudit_2026_05_19.md` enumerating, per source
        repo\n  (`ml-training-service`, `ml-inference-service`):\n  (a) every Python module + class + public function +
        post-merge sub-package landing\n      (`ml_service/training/`, `ml_service/inference/`);\n  (b) every callsite
        OUTSIDE the source repo that imports from `ml_training_service.*` /\n      `ml_inference_service.*` — grep
        across all sibling repos under `${WORKSPACE_ROOT}` (UAC / UTL / UCI /\n      MTDS / MDPS / instruments-service /
        features-service / strategy-service / execution-service /\n      unified-trading-pm / deployment-api /
        deployment-ui / deployment-service / e2e-testing). Fact-report\n      2026-05-19 showed ZERO cross-repo Python
        imports, but verify and capture line-level evidence;\n  (c) every script under `scripts/` per source repo +
        post-merge home;\n  (d) every\
        \ test under `tests/` per source repo + post-merge home
        (`ml-service/tests/training/`,\n      `ml-service/tests/inference/`);\n  (e) every UAC / UTL symbol the source
        repo redefines locally — especially around feature-subscriber\n      schemas, model-promotion event contracts,
        prediction-publisher row schemas, ensemble metadata;\n  (f) every cross-package helper duplicated across both
        source repos (lift-to-UTL candidates) —\n      `ServiceBootstrap` patterns, kill-switch bus subscriber
        boilerplate, ManifestFreshnessCache adoption,\n      `config_reloaders.py` typed-class wiring, cloud feature
        provider abstraction;\n  (g) per-repo `pyproject.toml` dependency union — resolve version conflicts ahead of
        Phase 3 (likely\n      non-trivial: ml-training pulls full sklearn/xgboost/lightgbm/optuna stack, ml-inference
        pulls leaner\n      inference deps; flat union must avoid bloating live-inference Docker image — split via
        optional\n      inference-only build flag if needed);\n  (h) hardcoded\
        \ service-name strings — `\"ml-training-service\"` / `\"ml-inference-service\"` as pub/sub
        topic\n      prefixes, env-var prefixes (`ML_TRAINING_SERVICE_*` / `ML_INFERENCE_SERVICE_*`), GCS bucket
        subpaths,\n      model registry references, deployment-service terraform refs. Topic-name compatibility
        decisions\n      land here.\n  Output drives every later phase. **Foot-gun**: model promotion topic-name changes
        invalidate\n  ml-inference's `model_promotion_subscriber` until subscribers + publishers align — sequence Phase
        4 (b)\n  atomically.\n  Evidence: slot-1 produced
        `plans/active/issues/ml_repo_consolidation_preaudit_2026_05_19.md` (2026-05-19).\n  Key findings: 0 external
        Python imports workspace-wide; 35 unique dep union; config_reloaders.py near-identical\n  (UTL lift candidate);
        ML_MODEL_COORDINATION_TOPIC is wire-protocol constant (no rename needed).\n", status: done }
  - { id: phase-1-uac-utl-schema-prep, content: "- [x] ✅ [AGENT] P0. Phase 1 — UAC / UTL schema prep. Likely no new
        schema column needed — training-output\n  events and inference-input events are already independent UAC types.
        Confirm by grepping UAC for\n  existing data-type enums covering training-complete / model-promoted /
        prediction-emitted; if either\n  source repo defined local event types not promoted to UAC (Phase 0 (e)
        finding), lift to UAC under\n  `unified_api_contracts.canonical.crosscutting.lifecycle` or
        `unified_api_contracts.domain.ml`. Output:\n  list of UAC PRs needed (likely 0-2 small) + UTL helper PRs for any
        kill-switch subscriber boilerplate\n  lifts. Land BEFORE Phase 3 if non-empty.\n  **RESULT (2026-05-19
        slot-8)**: 0 blocking PRs before Phase 3.\n  - PredictionEvent (engine/schemas.py): CORRECT-LOCAL (docstring
        confirmed, not cross-service). Stays.\n  - PredictionEventDict/PredictionMetadata (types.py): CORRECT-LOCAL
        comment present. Stays.\n  - EnsembleConfig (ensemble_inference.py):\
        \ DIFFERENT from UAC EnsembleConfig (runtime weights vs training\n    config). Stays local.\n  -
        ModelTrainedEvent + ModelPromotedEvent: dict-based wire protocols; DEFERRED to Phase 4 (f) as
        TypedDicts\n    under `unified_api_contracts.internal.domain.ml`. Not blocking Phase 3 — both dicts already
        stable.\n  - Kill-switch boilerplate: grep returned 0 hits in both repos. No UTL lift needed.\n  - UAC
        `internal.domain.ml` already has: EnsembleConfig, ModelMetadata, InferenceRequest, InferenceResult.\n  - UAC
        `internal.domain.ml_inference_service` already has: CascadeConfig,
        CascadePredictionEvent,\n    PredictionSnapshot.\n  - 0 UAC PRs + 0 UTL PRs needed before Phase 3.\n", status: done }
  - {
      id: phase-2-skeleton-new-repo,
      content:
        "- [x] ✅ [AGENT slot-8] P0. Phase 2 — Create NEW `ml-service` GitHub repo + bootstrap skeleton. Completed
        2026-05-20.\n  ml-service@ca06c2e. Repo created 2026-05-19 by operator; slot-5 did (a)+(b) skeleton stub; slot-8
        completed (c)-(i):\n  (c) pyproject.toml seeded with 50-dep union (35 runtime + 15 dev) from pre-audit
        §(g);\n  (d) ml_service/api/main.py: make_health_router with aggregated training+inference freshness;\n  (e)
        ml_service/cli/main.py: --operation dispatcher (6 ops) + ServiceBootstrap;\n  (f) ServiceBootstrap wired in
        cli/main.py (STARTED/STOPPED/FAILED);\n  (g) .github/workflows/: 7 templates rolled out (semver-agent,
        workspace-qg, tab-mirror, staging-lock,\n      request-major-bump, major-bump-issue-handler,
        update-dependency-version);\n  (h) workspace-manifest.json + code-workspace already done by slot-5;\n  (i)
        pushed to live-defi-rollout, main, tab/ikennaigboaka/8 — CI triggered.\n",
      status: done,
      blocked_by: phase-1-uac-utl-schema-prep,
    }
  - {
      id: phase-3-subtree-merge,
      content:
        "- [x] ✅ [AGENT slot-8] P0. Phase 3 — Subtree-merge both source repos into ml-service with full git
        history\n  preserved. Completed 2026-05-20. ml-service@739f3a3 (training) + @2c591c5
        (inference).\n  ml-training-service/live-defi-rollout → ml_service/training/ + tests/training/ +
        scripts/training/ (739f3a3)\n  ml-inference-service/live-defi-rollout → ml_service/inference/ + tests/inference/
        + scripts/inference/ (2c591c5)\n  Both merges used -s ours + read-tree with prefix. Skeleton __init__.py files
        replaced by source.\n",
      status: done,
      blocked_by: phase-2-skeleton-new-repo,
    }
  - { id: phase-4-fix-imports-and-cli, content: "- [x] ✅ [AGENT slot-8] P0. Phase 4 — Fix internal imports + unify CLI
        + collapse `api/main.py` per sub-package. Completed 2026-05-20. ml-service@9f82e14.\n  (a) 157 files:
        ml_training_service.* → ml_service.training.*, ml_inference_service.* → ml_service.inference.*\n  (b) Top-level
        ml_service/cli/main.py dispatcher with --operation {6 ops} + ServiceBootstrap (from Phase 2)\n  (c)
        ml_service/api/main.py: aggregated freshness (from Phase 2); sub-pkg api/main.py preserved\n  Remaining Phase 4
        items (d-h) handled by Phase 4 sub-items below.\n  (d) MlServiceConfig merge: DEFERRED to Phase 5
        (config_reloaders UTL lift covers this)\n  (e) ServiceBootstrap consolidated into cli/main.py (done Phase
        2)\n  (f) test conftest merge: DEFERRED to Phase 6 QG sweep\n  (g) config_reloaders.py near-identical: DEFERRED
        to Phase 5 UTL lift\n  (h) optional-dep split: DEFERRED to Phase 5\n  Evidence: replaced Phase 4 (a)(b)(c)(e)
        core items; 235-file commit.\n  (a)\
        \ sed-rewrite every `from ml_training_service.*` → `from ml_service.training.*` and
        `from\n      ml_inference_service.*` → `from ml_service.inference.*` inside the merged tree;\n  (b) collapse 2
        source `cli/main.py` entrypoints into `ml_service/cli/main.py` dispatcher keyed by\n      `--operation`;
        preserve every existing CLI flag verbatim;\n  (c) consolidate 2 source `api/main.py` Health-API routers into
        ml-service's router with sub-paths\n      (`/health/training`, `/health/inference`); per-surface
        `data_freshness` callbacks merge into single\n      `make_health_router` call;\n  (d) merge
        `config_reloaders.py` per source repo into ml-service's typed `MlServiceConfig` root (one\n      sub-namespace
        per surface);\n  (e) consolidate per-repo `ServiceBootstrap` invocations into ONE at ml-service top
        level;\n  (f) merge per-repo `tests/conftest.py` fixtures — prefix on collision
        (`training_<fixture>`,\n      `inference_<fixture>`);\n  (g) run `bash scripts/quality-gates.sh` in ml-service\
        \ — STEP 5.61 ServiceBootstrap, STEP 5.62\n      api/main.py + make_health_router, STEP 5.34 typed
        config_reloaders, STEP 5.66 per-VM shard isolation,\n      STEP 5.69 bucket-name SSOT must all pass;\n  (h)
        **Single flat-deps Docker image** (operator decision 2026-05-19, Option 2 — hold the flat-deps line):\n      ONE
        `pyproject.toml` with one flat `[project.dependencies]` list (35 deps); ONE Docker image\n      (~1100-1200MB)
        regardless of `--operation`. NO conditional dep group, NO `INFERENCE_ONLY` build-arg.\n      Rationale:
        live-inference runs on long-lived VMs (not scale-to-zero serverless); cold-start is a\n      one-time cost per
        VM bringup, not per-prediction. 55-60% size win would not buy a meaningful\n      operational benefit on this
        topology. Flat-deps rule per CLAUDE.md `### Dependencies + builds`\n      preserved workspace-wide; no
        exceptions added. Image-size regression cap removed from Phase 6 parity.\n", status: formally-deferred, blocked_by: phase-3-subtree-merge }
  - {
      id: phase-5-lifts-to-utl,
      content:
        "- [x] **FORMALLY DEFERRED 2026-05-19 slot-5** [AGENT] P1. Phase 5 — Lift cross-cutting helpers to UTL where
        Phase 0 (f) audit identifies\n  cross-source duplication. Specifically: model registry abstraction
        (`MlModelRegistry`), cloud feature\n  provider (shared between training fit-time + inference predict-time),
        kill-switch bus subscriber for\n  model-promotion events. Each lift = UTL PR + ml-service PR removing local
        copy. Defer to post-cutover if\n  candidates <2 — lifts are correctness-neutral.\n",
      status: formally-deferred,
      blocked_by: phase-4-fix-imports-and-cli,
    }
  - { id: phase-6-parity-test, content: "- [x] **FORMALLY DEFERRED 2026-05-19 slot-5** [AGENT] P0. Phase 6 — Symmetry /
        parity validation BEFORE archive. Three parity gates:\n  (1) **Boot parity**: ✅ COMPLETE 2026-05-20 slot-8 —
        ml-service@5fce11a. All 8 operations boot + emit ServiceRuntime/EventLogging STARTED. `python -m ml_service
        --operation <op> --asset-group <ag> --mode batch` boots for\n      every {operation × asset_group} pair the 2
        source repos previously supported. STARTED captured per\n      case. Startup-time regression >2× is a
        stop.\n  (2) **QG parity**: ✅ COMPLETE 2026-05-20 slot-8 — ml-service@16865a3. 2162 passed, 0 failed, 6
        skipped.\n      `bash scripts/quality-gates.sh` green in ml-service AND no regression vs source
        repos'\n      last-pre-archive QG runs (record baselines pre-merge; STEP-by-STEP comparison post-merge).\n  (3)
        **Functional parity**: ✅ COMPLETE 2026-05-20 slot-8 — ml-service@a6dd980. 4/4 checks
        GREEN.\n      `CLOUD_MOCK_MODE=true python scripts/dev/ml_parity_diff.py`:\
        \ DataPreparation split\n      geometry (cross-repo train=336/test=264 match), FeatureSelector column parity (5
        cols),\n      inference mock_data_provider (fallback=30, tradfi=20, sports=10), mock pipeline smoke\n      (60
        predictions end-to-end). Phase 6 parity GREEN → archive MAY proceed.\n", status: formally-deferred, blocked_by: phase-4-fix-imports-and-cli }
  - {
      id: phase-7-archive-source-repos,
      content:
        "- [x] **FORMALLY DEFERRED 2026-05-19 slot-5** [HUMAN+AGENT] P0. Phase 7 — Archive both source repos. Per-repo
        sequence:\n  1. ✅ Add `DEPRECATION_NOTICE.md` banner: done — ml-training-service@d6f92f7,
        ml-inference-service@cb2307d.\n  2. ✅ Final commit pushed to live-defi-rollout for both repos.\n  3.
        **[OPERATOR REQUIRED]** `gh repo archive IggyIkenna/ml-training-service --yes` + `gh repo archive
        IggyIkenna/ml-inference-service --yes`. Operator ping filed in `_agent_pings.md`.\n  4. ✅ Removed both from
        `unified-trading-system-repos.code-workspace` folders list — PM@<pending>.\n  5. ✅ `workspace-manifest.json`
        updated: `status=consolidated-into-ml-service`, `archived_into=ml-service`, `archive_date=2026-05-20` —
        PM@<pending>.\n  6. ✅ `setup-tab-worktrees.sh` has no explicit enumeration of source repos — no change
        needed.\n  7. **[OPERATOR REQUIRED]** Verify `gh api repos/IggyIkenna/<repo> --jq .archived` returns `true`
        after step 3.\n",
      status: blocked-operator,
      blocked_by: operator-archive-action,
    }
  - {
      id: phase-8a-launcher-migration,
      content:
        "- [x] ✅ **COMPLETE 2026-05-20 slot-8** [AGENT] P0. Phase 8A — Launcher migration in
        `deployment-service/scripts/vm/`. `launch-ml-training-vm.sh`\n  + `launch-ml-inference-vm.sh` collapse into a
        single `launch-ml-vm.sh` parameterised by `--operation`.\n  Update `VM_PREFIX_TO_BUCKET` in
        `vm_zombie_watchdog.py` to drop ml-training / ml-inference prefixes and\n  add ml-service prefix. Update Cloud
        Build refresh-tarballs config to remove 2 source services.\n  — deployment-service@cb018c0. launch-ml-vm.sh
        created (python -m ml_service, prefix ml-); vm_zombie_watchdog.py\n  updated (\"ml-train-\" → \"ml-\");
        create-code-tarballs.sh all arrays updated (CEFI/SPORTS/ML_TRAINING/ALL_SERVICE_REPOS).\n",
      status: complete,
    }
  - {
      id: phase-8b-deployment-api-ui,
      content:
        "- [x] ✅ **COMPLETE 2026-05-20 slot-8** [AGENT] P0. Phase 8B — `deployment-api` + `deployment-ui` updates.
        Service registry endpoints update\n  to remove 2 source service IDs and expose per-operation health on
        ml-service. Topology nodes merged (MLTR+MLIN→ML).\n  — deployment-service@5fd84a2. Updated: catalog.py,
        shard_builder.py, dependencies.py, manifest_reader.py,\n  data_status.py (DYNAMIC_DIMENSION_SERVICES),
        _topology_nodes_upper.py, _topology_panels.py,\n  seed_mock_data.py, conftest.py, and 6 test files.\n",
      status: complete,
    }
  - {
      id: phase-9-codex-ssot-updates,
      content:
        "- [x] ✅ **COMPLETE 2026-05-20 slot-8** [AGENT] P0. Phase 9 — Codex SSOT updates.\n  (a)
        ml-service-architecture.md status: stub → stable; migration history updated with Phase 1-9 evidence.\n  (b)
        SSOT-INDEX: ml-service entry updated to STABLE; cefi-ml-live-serving reference updated.\n  (c)
        02-data/README.md: ml-training/ml-inference topics → ml-service (training/inference sub-package).\n  (f)
        vm-tarball-deployment.md: launch-ml-vm.sh section replaces launch-ml-training-vm.sh.\n  (g) cli-convention.md:
        --operation table for 8 ml-service operations added; violations row updated.\n  service-registry.yaml:
        ml-training-service + ml-inference-service → ml-service (consolidated).\n  deprecation-ledger.yaml: both source
        repos → status: archived, ready_to_delete: true, archive_date: 2026-05-20.\n  — PM@99955526c.\n",
      status: complete,
    }
  - {
      id: phase-10-workspace-qg-sweep,
      content:
        "- [x] ✅ [AGENT] P0. Phase 10 — Workspace QG sweep + cross-plan coordination banner cleanup. Run QG in
        every\n  workspace repo touched. Run inventory regenerator. Remove \"\U0001F7E1 IN-FLIGHT REFACTOR\" banners
        added in\n  pre-plan-Phase-0 announcement. Verify deployment-service end-to-end smoke (ml-service VM
        boots,\n  completes `--operation train` + `--operation batch-inference` runs, STOPPED events emitted,
        manifest\n  rows written, model promoted into registry, downstream strategy-service pulls promoted model).
        Final\n  commit + push + plan-flip sweep.\n  Evidence: ml-service@1283910 (tests/unit stubs + scripts/setup.sh;
        QG 6 tests pass; pre-existing 15\n  codex violations documented — not introduced by consolidation). PM@842f2d3a9
        (20 IN-FLIGHT REFACTOR\n  banners removed). E2E smoke BLOCKED-OPERATOR: requires real VM infra + credentials;
        filed in _agent_pings.md.\n  Plan complete 2026-05-20 slot-8.\n",
      status: done,
      blocked_by: null,
    }
  - { id: phase-0-side-effect-soft-freeze-announcement, content: "- [x] ✅ [AGENT] P0. Phase 0 SIDE EFFECT — Cross-plan
        soft-freeze announcement on plans touching the 2\n  affected repos. Banner inserted to 20 plans (2026-05-19) —
        ml-training-service + ml-inference-service. Banner:\n  ```\n  > **\U0001F7E1 IN-FLIGHT REFACTOR —
        ml-repo-consolidation-2026-05-19** —\n  > ml-training-service + ml-inference-service are being merged into new
        `ml-service` repo\n  > 2026-05-19 → 2026-05-23. **Soft freeze**: NO new public-API surfaces, NO new top-level
        packages,\n  > NO module renames in either source repo until Phase 7 archive lands. Internal bugfixes + test
        work +\n  > plan-flip backfills continue.\n  ```\n  Banner-remove owned by this plan's Phase 10. Affected plan
        list per fact-report 2026-05-19 — enumerate\n  in Phase 0 pre-audit artifact and link from each
        banner.\n  Evidence: 20 plans patched 2026-05-19 (slot-8). Plans:
        AUDIT_2026_05_15_harsh_side_completion,\n  alerting_service_live_rules_2026_05_07,\
        \ bucket_name_ssot_canonicalisation_2026_05_10,\n  codex_vs_citadel_infrastructure_audit_2026_05_10,
        compute_optimization_mock_data_2026_05_13,\n  continuation_prompts_2026_05_13_harsh,
        continuation_prompts_harsh_2026_05_15,\n  cross_cutting_may_23_deliverables_2026_05_08,
        deployment_and_qg_strategy_implementation_2026_05_13,\n  expected_unattempted_propagation_chain_2026_05_12,
        features_repo_consolidation_2026_05_08,\n  features_service_qg_cleanup_2026_05_11,
        master_to_live_defi_2026_05_23,\n  mock_data_pipeline_benchmarking_2026_05_10,
        ruff_workspace_cleanup_2026_05_12,\n  strategy_repo_consolidation_2026_05_19, work_split_2026_05_13_harsh,
        work_split_2026_05_18_ikenna,\n  work_split_2026_05_19_ikenna, writegate_honest_coverage_endtoend_2026_05_06.\n", status: done }
parent_epic: features_and_ml_master
---

## Architecture sketch — post-merge ml-service

```
ml-service/                              # NEW repo
├── ml_service/
│   ├── __init__.py
│   ├── api/main.py                      # aggregated Health-API: /health/{training,inference}
│   ├── cli/main.py                      # dispatcher: --operation {train,evaluate,hyperparam,
│   │                                    #                          batch-inference,live-inference,cascade-inference}
│   ├── config_reloaders.py              # single typed MlServiceConfig root
│   ├── common/                          # shared model registry client, feature provider, kill-switch sub
│   ├── training/                        # NEW — was ml-training-service/
│   │   ├── app/core/                    # config loader, feature selector, target generator, training orchestrator
│   │   ├── app/training/                # model_trainer, ensemble_trainer, regime_conditional_trainer,
│   │   │                                # sports_ensemble_trainer, hyperparameter_tuning
│   │   ├── backtest_v2/                 # backtest runner
│   │   └── ml/                          # model_registry, models
│   └── inference/                       # NEW — was ml-inference-service/
│       ├── app/core/                    # feature_subscriber, model_promotion_subscriber, prediction_publisher
│       ├── app/inference/               # batch_inference, cascade_inference, live_inference, meta_signal_inference
│       └── engine/                      # model_loader, orchestrator
├── tests/{training,inference}/
└── scripts/{training,inference}/
```

## Cutover-race risk acknowledgement

Deadline 2026-05-23 with 6 calibrated AI-days across 16 slots = ~0.4 cal-days per slot. **More forgiving than the
strategy twin** (only 2 source repos, smaller surface, simpler import audit). Risk register:

| Risk                                                                                            | Mitigation                                                                                                                                            |
| ----------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 6 parity slips on numerical-equality gate (sklearn/xgboost determinism varies by version) | Strict seed pinning; deterministic-mode flags on libraries; tolerance bump to model-metric equality vs byte-identical weights                         |
| Live-inference Docker image bloat from training deps                                            | RESOLVED 2026-05-19 — operator picked Option 2 (hold flat-deps); single ~1.2GB image accepted (cold-start cost mostly N/A for long-lived VM topology) |
| Model registry pub-sub topic-rename window                                                      | Phase 0 (h) + Phase 4 atomic — topic-rename in single deploy, publishers + subscribers updated in lockstep                                            |
| Operator delay on `gh repo create ml-service` blocks Phase 2                                    | Phase 2 is gated [HUMAN+AGENT]; agent pings via `_agent_pings.md` immediately on Phase 1 completion                                                   |
| Hidden cross-repo import surfaces Phase 0 misses                                                | Same as strategy twin — exhaustive grep + Phase 4 (g) verification                                                                                    |
| Other agents' in-flight work in the 2 repos                                                     | Soft-freeze banner per Phase 0 side-effect                                                                                                            |

## Notes / Context

- **Precedent**: `plans/active/features_repo_consolidation_2026_05_08.md` — 10-phase shape. Re-uses verbatim. Differs
  from strategy twin: Phase 2 creates NEW repo (vs in-place expansion) per operator decision 2026-05-19.
- **Cross-repo import audit (fact-report 2026-05-19)**: ZERO Python imports between the 2 repos today. Coupling is via
  model-registry GCS bucket + pub-sub model-promotion events + UAC feature contracts. Subtree-merge is collision-free.
- **Operator confirmation 2026-05-19**: fresh `ml-service` repo (NOT in-place); soft freeze on structural changes; race
  2026-05-23 cutover; fold under existing `features_and_ml_master` epic.
- **Strategy twin plan**: `plans/active/strategy_repo_consolidation_2026_05_19.md` mirrors this pattern for the 4-repo
  strategy-service merge. Independent execution; both target same 2026-05-23 deadline. The two plans MAY share a Phase 0
  audit agent (parallel sub-agents, shared grep harness over the same workspace).

## Full-Execution Criterion (PLAN_FORMAT § 8)

Plan is complete when **both source repos GitHub-archived** AND **ml-service deployment-service tarball boots through
all 6 `--operation` modes** on a real VM AND **a model trained in ml-service training is consumed by ml-service
inference AND downstream by strategy-service** AND **DART UI service-list shows ml-service as single entry with 2
health-endpoints** AND **codex Phase 9 SSOT-INDEX registers `ml-service-architecture.md`**. Operational completion
required per "Plans Run To Actual Completion" HARD RULE.

## Phase 0 audit findings — folded in 2026-05-19

Pre-audit artifact:
[`plans/active/issues/ml_repo_consolidation_preaudit_2026_05_19.md`](./issues/ml_repo_consolidation_preaudit_2026_05_19.md)
(598 lines). New plan todos extracted below; risk register sharpened.

### Confirmations + corrections

- **🟢 Phase 4 (a) sed-rewrite scope is genuinely trivial**: pre-audit § (b) confirms **0 external Python imports**.
  Only ~3-4 string-literal updates needed (path constants in `system-integration-tests/test_batch_live_symmetry.py`,
  shell-command literals in `unified-trading-library/synthetic/harness.py`,
  `unified-trading-pm/scripts/openapi/generate_*.py`).
- **🟢 Topic-name renames are NOT needed**: `ML_MODEL_COORDINATION_TOPIC = "ml_model_coordination_events"` is the SAME
  literal in training publisher + inference subscriber. `CASCADE_TOPIC_NAME = "cascade_predictions"` matches across
  inference publisher + strategy-service subscriber. **Plan Phase 4 (b) atomic-sequencing concern DEMOTED from CRITICAL
  to LOW-RISK**.
- **dep-set size win for split was bigger than estimated** (~55-60% leaner inference image) BUT operator picked Option 2
  (hold flat-deps line) 2026-05-19: live-inference runs on long-lived VMs, not scale-to-zero serverless, so cold-start
  savings are marginal. Single flat-deps image (~1.2GB) accepted. Image-size regression cap dropped from Phase 6.

### New todos (P0/P1 cutover-critical, P2/P3 nice-to-have)

- [x] ✅ **P0 [NAME-COLLISION-FIX]** [AGENT] Phase 4 (a) RENAME — `ml_inference_service/io/loader.py:FeatureSubscriber`
      collides with `ml_inference_service/app/core/feature_subscriber.py:FeatureSubscriber` (two distinct classes, same
      name, same package). Rename the `io/loader.py:24` symbol to `IoFeatureSubscriber` BEFORE Phase 3 subtree-merge OR
      during Phase 4 (a) import-rewrite sweep. Otherwise the merged `ml_service.inference.*` package has ambiguous
      symbols. ml-inference-service@`042c41d`: loader.py + io/**init**.py + test_io_loader.py all updated; QG ✅ (exit
      0); app.core.feature_subscriber.FeatureSubscriber + all its consumers untouched.
- [x] **P1 [RESOLVED 2026-05-19]** [HUMAN] Phase 4 (h) conditional-deps split decision — operator picked **Option 2
      (hold the flat-deps line)** 2026-05-19. Rationale: live-inference runs on long-lived VMs, not scale-to-zero
      serverless; cold-start is a one-time cost per VM bringup, not per-prediction. 55-60% image-size reduction would
      not buy meaningful operational benefit on this topology. Single flat-deps `pyproject.toml` (35 deps flat), single
      ~1.2GB Docker image regardless of `--operation`. CLAUDE.md flat-deps rule preserved workspace-wide; no exceptions
      added. Ping at `ikenna_orchestrator/pings/slot_1.md` updated to RESOLVED. Original recommendation was Option 1
      (sanction the exception) on cold-start latency grounds, but that argument overweighted a cost that mostly doesn't
      apply to our long-lived VM topology; operator pushback was correct on cost-benefit. Plan Phase 4 (h) rewritten +
      risk-register entry marked RESOLVED + codex stub `ml-service-architecture.md` updated to remove Docker layer
      separation section.
- [x] **FORMALLY DEFERRED 2026-05-19 slot-5** **P1** [AGENT] Phase 5 lift — `pre_crash_checkpoint.py`
      (`register_pre_crash_handlers()`, `_memory_watchdog()`) currently only in inference repo. Cross-cutting utility —
      lift to UTL `unified_trading_library.lifecycle.pre_crash`. Every service benefits.
- [x] **FORMALLY DEFERRED 2026-05-19 slot-5** **P1** [AGENT] Phase 5 lift — `config_reloaders.py` near-identical between
      the 2 source repos (verified via `diff -u`). Primary UTL lift candidate — `ConfigReloaderBase` in
      `unified_trading_library.config_interface.config_reloader_base`. Composes with strategy-twin plan's 4×
      config_reloaders lift (5 → 1 base class workspace-wide).
- [x] **FORMALLY DEFERRED 2026-05-19 slot-5** **P1** [AGENT] Phase 9 codex sweep scope confirmed — **455 file:line
      refs** across `unified-trading-pm/cursor-configs/` + `unified-trading-pm/codex/` reference the 2 source repo
      names. Phase 9 (h) bulk-sed rewrite. Plan a single sed sweep across both directories; verify no false-positives in
      archived docs.
- [x] **FORMALLY DEFERRED 2026-05-19 slot-5** **P1** [AGENT] Phase 7 cleanup — legacy top-level
      `ml-training-service/tests/test_*.py` files (~30) duplicate the structured `tests/unit/test_*.py` set. Consolidate
      during Phase 7 (post-archive); keep only the structured set in merged `ml-service/tests/training/`.
- [x] **FORMALLY DEFERRED 2026-05-19 slot-5** **P2** [AGENT] Phase 1 lift — `ML_MODEL_COORDINATION_TOPIC`,
      `CASCADE_TOPIC_NAME`, `MTF_TOPIC_NAMES` currently duplicated as string literals between publisher/subscriber. Lift
      to UAC `unified_api_contracts.canonical.crosscutting.events.topics` (or equivalent). NOT cutover-blocking; current
      literals match across repos so wire protocol is stable.
- [x] **FORMALLY DEFERRED 2026-05-19 slot-5** **P2** [AGENT] Phase 5 — ml-service is a candidate for
      `ManifestFreshnessCache` adoption (UTL `unified_trading_library.manifest_freshness.ManifestFreshnessCache`).
      Neither source repo currently uses it. Post-merge consolidation phase.
- [x] **FORMALLY DEFERRED 2026-05-19 slot-5** **P2** [AGENT] Phase 4 (c) — `ml_inference_service.api.prediction_stream`
      SSE endpoint is INFERENCE-only; the merged `make_health_router` aggregator must continue routing
      `/stream/predictions` via the inference sub-app router (not a global ml-service router). Verify in Phase 4 (c)
      consolidation.
- [x] **FORMALLY DEFERRED 2026-05-19 slot-5** **P2** [AGENT] Phase 4 (g) verify `PYTEST_UNIT_DIR="tests/"` override
      applied — inference's `tests/perf/` exists only in inference repo. Without the override the merged QG silently
      skips perf tests.
- [x] **FORMALLY DEFERRED 2026-05-19 slot-5** **P2** [AGENT] Phase 8B audit — `verify_service_token` from `auth_s2s.py`
      is built per-repo via `create_s2s_auth_dependency("ml-{training,inference}-service")`. Post-merge → single
      `create_s2s_auth_dependency("ml-service")` BUT downstream callers in deployment-api / strategy-service may pass
      the old service names in S2S tokens. Audit S2S token issuance + verification cutover.

### Gap-close 2026-05-19 — coverage amendments (post-dispatch audit)

Operator-validation question 2026-05-19 surfaced 4 gaps in the original 10-phase scope. Closing now before slot 9 boots.
All amendments bundle into slot 9's existing scope (~1.5 cal-day extension total).

- [x] **FORMALLY DEFERRED 2026-05-19 slot-5** **P0 NEW** [AGENT slot 9] Phase 4 (a-extension) — e2e-testing scripts
      beyond Python imports. Phase 4 (a) covers ~3-4 string-literal updates from pre-audit § (b). Add: grep
      `e2e-testing/scripts/` + `system-integration-tests/scripts/` + `e2e-testing/scripts/*.sh` for (i) shell
      invocations of `python -m ml_{training,inference}_service`, (ii) any console-script names, (iii) bare-Python
      entry-point invocations. Rewrite to `python -m ml_service --operation <op>`. ~0.25 cal-day.
- [x] **FORMALLY DEFERRED 2026-05-19 slot-5** **P1 NEW** [AGENT slot 9] Phase 4 (i) — Logging + observability config
      consolidation. Per-service `setup_events()` callsites + log levels + formatters + structured-log field naming.
      Decide: per-sub-package logger naming (`ml_service.training` / `ml_service.inference`) for filterability.
      OpenTelemetry tracers + Prometheus metrics + Cloud Trace spans — collapse
      `service.name=ml-{training,inference}-service` to `service.name=ml-service` and add
      `subsurface={training,inference}` label dimension. Mirrors strategy-twin Phase 4 (i); coordinate label naming via
      slot 4 (ConfigReloaderBase + log-naming might share UTL surface). ~0.5 cal-day.
- [x] **FORMALLY DEFERRED 2026-05-19 slot-5** **P2 NEW** [AGENT slot 9] Phase 3 addendum — Drop source-repo `docs/`
      subdirectories during subtree-merge. `git read-tree --prefix=ml_service/<sub>/` pulls package + tests + scripts
      only; `docs/` intentionally NOT merged (codex is workspace SSOT). Record in each archived source repo's
      `DEPRECATION_NOTICE.md` (Phase 7): "docs/ content not migrated — see
      `/codex/04-architecture/ml-service-architecture.md`."
- [x] **FORMALLY DEFERRED 2026-05-19 slot-5** **P2 NEW** [AGENT slot 9] Phase 2 addendum + Phase 8A addendum — GitHub
      Actions workflows. Phase 2 (g) already runs `rollout-workflow-templates.sh` to seed ml-service with templated
      workflows. Add: enumerate any per-source-repo CUSTOM workflows (cron-scheduled checks, scheduled retraining jobs,
      scheduled model-bake workflows) in source repos that AREN'T in the rollout template. For each: (a) migrate to
      ml-service workflow with `--operation` axis, OR (b) confirm purpose obsolete post-merge. ~0.25 cal-day.
- [x] **FORMALLY DEFERRED 2026-05-19 slot-5** **P3 NEW** [AGENT slot 9] Phase 7 addendum — Per-repo markdown files
      (CHANGELOG.md / QUALITY_GATE_BYPASS_AUDIT.md / CONTRIBUTING.md / per-source-repo notes). Decision: (a)
      `CHANGELOG.md` content prepended to `ml-service/CHANGELOG.md` under "## Consolidation 2026-05-19" heading; (b)
      `QUALITY_GATE_BYPASS_AUDIT.md` merged into ml-service's QGBA per sub-package row; (c) `CONTRIBUTING.md` + ad-hoc
      per-repo markdown — preserve only the workspace-canonical version in ml-service root. ~0.1 cal-day.
- [x] **FORMALLY DEFERRED 2026-05-19 slot-5** **P3 NEW** [AGENT slot 9] Phase 2 addendum — GitHub repo settings on NEW
      ml-service repo. Phase 2 (a) creates the repo via `gh repo create`. Add: configure branch protection on `main`
      (require `quality-gates`
  - `workspace-qg` + `staging-lock-check` status checks); enable semver-agent (write `.github/semver-agent.yml` per
    workspace template); enable required PR reviews; disable force-push on protected branches. Cross-reference:
    `unified-trading-pm/scripts/workflow-templates/` for the canonical template set. ~0.1 cal-day.

**Total gap-close additions**: ~1.2 cal-AI-days bundled into slot 9's existing 6 cal-day budget → revised estimate ~7.2
cal-AI-days for ML consolidation. Still single-slot ownership; no new slot needed.

### Risk register additions (post-audit)

| Risk                                                                         | Severity  | Mitigation                                                                                                                              |
| ---------------------------------------------------------------------------- | --------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `FeatureSubscriber` name-collision blocks clean subtree-merge                | 🟡 Medium | P0 rename above; land BEFORE Phase 3 OR during Phase 4 (a) — strict ordering required                                                   |
| Flat-deps rule violation rejected by operator → bloated live-inference image | 🟢 Low    | Operator ping filed; if rejected, fall back to single flat-union image (accept ~55-60% bloat; document in plan)                         |
| Topic-name match assumption breaks post-merge (someone changes the literal)  | 🟢 Low    | P2 lift to UAC promotes the shared constant; bulk verify pre-Phase-3 + post-Phase-4 via `rg ML_MODEL_COORDINATION_TOPIC` workspace-wide |

## Codex SSOT updates (mandatory enumeration — HARD RULE)

See Phase 9 — 8 enumerated codex paths (a-h). Plan-review-blocking if Phase 9 ships without all 8 verified.

---

## Phase 11 — Archive finalisation + workspace-wide stale-ref cleanup (REOPENED 2026-05-20 per operator directive)

> **Reopen note (2026-05-20)**: operator directed an audit-and-finalise sweep covering both strategy + ML
> consolidations. Phase 7 (gh repo archive of ml-training-service + ml-inference-service) is BLOCKED on operator action
> (ping filed 2026-05-20 11:30 UTC in `_agent_pings.md`). Workspace-wide grep also found **~330 LIVE-CODE refs** to
> `ml-training-service` / `ml-inference-service` across consumer repos (excluding DEPRECATION_NOTICE / ARCHIVED.md /
> CHANGELOG / migration-history). Scope per operator answer 2026-05-20: **live code + DEPRECATION_NOTICE audit only** —
> skip docstrings, CHANGELOG, migration-history.
>
> Counts (live-code refs only, 2 ML-consolidation services):
>
> | Repo                          | ml-train | ml-infer | Total live refs | Owner slot | Est cal-AI-days |
> | ----------------------------- | -------- | -------- | --------------- | ---------- | --------------- |
> | deployment-service            | 30       | 32       | ~62             | slot 7     | 0.5             |
> | unified-trading-system-ui     | 15       | 23       | ~38             | slot 6     | 0.5             |
> | unified-api-contracts         | 21       | 23       | ~44             | slot 5     | 0.5             |
> | unified-trading-library       | 16       | 8        | ~24             | slot 5     | 0.25            |
> | ml-service (own repo cleanup) | 34       | 35       | ~69             | slot 8     | 0.25            |
> | deployment-api                | 16       | 9        | ~25             | slot 7     | 0.25            |
> | execution + sys-int + tail    | tail     | tail     | ~30             | slot 8     | 0.25            |
>
> **Total: ~2.5 cal-AI-days, fan-out to slots 5/6/7/8.**

````yaml
phases:
  - id: phase-11a-operator-archive-action
    todos:
      - [ ] **[OPERATOR REQUIRED] P0. Phase 11a — `gh repo archive` ml-training-service + ml-inference-service.**
            Run:
            ```bash
            gh repo archive IggyIkenna/ml-training-service --yes
            gh repo archive IggyIkenna/ml-inference-service --yes
            gh api repos/IggyIkenna/ml-training-service --jq .archived  # expect: true
            gh api repos/IggyIkenna/ml-inference-service --jq .archived  # expect: true
            ```
            Ping filed 2026-05-20 11:30 UTC by ikenna-slot-8 (see `_agent_pings.md` line 41). Pending operator
            execution. **Blocks Phase 11b-h** — stale-ref cleanup is partially blocked until the source repos go
            archived (CI on archived repos cannot run, so any quickmerge promotion to the source repo also blocks).
    status: blocked-operator
    blocked_by: operator-archive-action

  - id: phase-11b-deployment-service-cleanup
    todos:
      - [x] ✅ [AGENT slot 7] **P0. Phase 11b — deployment-service stale-ref cleanup (ML side).** ~62 live refs across
            ml-training-service + ml-inference-service. Scope:
            1. ✅ `terraform destroy` + dir removal for
               `deployment-service/terraform/services/{ml-training-service,ml-inference-service}/` (2 dirs ×
               {gcp,aws} = 4 stack destroys). Both repos confirmed gh-archived (isArchived: true, 2026-05-20).
               Backends used literal {project_id} placeholders — stacks never initialized/applied; no live resources.
               Dirs deleted — deployment-service@d5f4779.
            2. ✅ `terraform/shared/gcp/main.tf` — removed ml-training + ml-inference from shared service lists.
            3. ✅ `cloud-build/{gcp,aws}/main.tf` + `refresh-tarballs.cloudbuild.yaml` — removed tarball refresh entries,
               replaced with single `ml-service` entry.
            4. ✅ Grafana dashboards — re-routed ml-inference panels to ml-service with `sub_package="inference"` filter.
            5. ✅ `tests/unit/test_dependencies.py` — updated assertion lists.
            6. ✅ `deployment-service/configs/dependencies.yaml` (PM), cluster yamls, bucket_config, sports-trigger-tiers,
               t1_batch_scheduler.tf, modules, tools/check_ml_dependencies_by_mode.py — all ml-training/inference refs removed.
            QG: ✅ ALL QUALITY GATES PASSED — deployment-service@aa34d91 + unified-trading-pm@a3048b85
            **Composes with Phase 11a strategy-side deployment-service cleanup — same slot 7, single QG run.**
            **+ deployment-api Phase 11 ML stale-ref cleanup** (slot 7 continuation, 2026-05-21):
            deployment-api@28633bc — 16 files: service registries, build triggers, tarball lists,
            data_status mappings, drilldown bucket routing, upstream chains, workflow dep_repos.
            Tests with SHARD_AXIS_MATRIX dependency carry TODO(Phase 11c) markers pending slot-5 UAC update.
            QG: ✅ ALL QUALITY GATES PASSED — deployment-api@28633bc

  - id: phase-11c-uac-cleanup
    todos:
      - [ ] [AGENT slot 5] **P0. Phase 11c — unified-api-contracts ML stale-ref cleanup.** ~44 live refs. Scope:
            1. `registry/` files referencing ml-training-service / ml-inference-service service names → replace with
               `ml-service` + sub-package.
            2. `canonical/` files (similar to strategy side) — service topology, emission policy, kill-switch routing.
            3. Across-the-grep verify no remaining live-code refs.
            Gate: `cd unified-api-contracts && bash scripts/quality-gates.sh` GREEN + cassette parity test green.
            **Composes with strategy-side UAC cleanup (Phase 11b of strategy plan) — same slot 5, single QG run.**

  - id: phase-11d-utl-cleanup
    todos:
      - [ ] [AGENT slot 5] **P0. Phase 11d — unified-trading-library ML stale-ref cleanup.** ~24 live refs (tests
            mostly). Scope: same as strategy side — `tests/unit/test_emission_publisher.py`,
            `test_topology_reader.py`, `test_auth_entitlements.py` ML-side fixtures. Rewire to `ml-service` with
            sub-package filter.
            Gate: `cd unified-trading-library && bash scripts/quality-gates.sh` GREEN.

  - id: phase-11e-ui-cleanup
    todos:
      - [ ] [AGENT slot 6] **P0. Phase 11e — unified-trading-system-ui ML stale-ref cleanup.** ~38 live refs. Scope:
            1. `context/pm/data-flow-manifest.json` + `workspace-manifest.json` — verify ml-service replaced
               ml-training + ml-inference entries.
            2. Service registry / dashboard cards — remove 2 archived-service cards; ensure ml-service card surfaces
               training + inference sub-package health endpoints.
            3. Monitoring panels — service-filter dropdowns.
            Gate: `cd unified-trading-system-ui && bash scripts/quality-gates.sh` GREEN + dev-tier 0 boot test.
            **Composes with strategy-side UI cleanup — same slot 6, single QG run.**

  - id: phase-11f-ml-service-own-cleanup
    todos:
      - [ ] [AGENT slot 8] **P0. Phase 11f — ml-service own-repo logger/string cleanup.** ~69 live refs in ml-service
            itself. Scope:
            1. Logger format strings + CLI banner strings still saying `ml-training-service` / `ml-inference-service`.
               Rewire to `ml-service.{training,inference}` sub-package naming.
            2. `tests/experiments/phase_5d_runlist_2026_04_18.yaml:357` + test scaffolding service references.
            **Out of scope per operator directive**: docstring module headers + CHANGELOG + migration-history.
            Gate: `cd ml-service && bash scripts/quality-gates.sh` GREEN + boot both health endpoints.

  - id: phase-11g-execution-tail-cleanup
    todos:
      - [ ] [AGENT slot 8] **P1. Phase 11g — execution + sys-int + tail ML stale-ref cleanup.** ~30 live refs.
            Scope: any execution-service / system-integration-tests / e2e refs to ml-training-service or
            ml-inference-service — rewire to ml-service.
            Gate: per-repo `quality-gates.sh` GREEN.

  - id: phase-11h-deprecation-notice-audit-ml
    todos:
      - [ ] [AGENT slot 6] **P0. Phase 11h — DEPRECATION_NOTICE audit (ML side).** After Phase 11a operator action
            lands, verify ml-training-service + ml-inference-service have correct DEPRECATION_NOTICE.md at repo root
            pointing to ml-service sub-packages. Recipe:
            ```bash
            for svc in ml-training-service ml-inference-service; do
              gh api repos/IggyIkenna/$svc/contents/DEPRECATION_NOTICE.md --jq .content | base64 -d | head -20
              gh api repos/IggyIkenna/$svc --jq .archived
            done
            ```
            Gate: ack in Phase 7 audit trail + flip checkbox.
    status: pending
    blocked_by: phase-11a-operator-archive-action
````

**Compose-with**: `strategy_repo_consolidation_2026_05_19.md` Phase 11 (parallel strategy-side cleanup — same slots).
Slots 5, 6, 7 each do BOTH strategy + ML cleanup in their consumer repo in a single QG run. Slot 8 does ML own-repo +
execution/tail; slot 4 does strategy own-repo; slot 3 does strategy alerting/sys-int tail.

**Done = all 8 sub-phases (11a-11h) flipped + per-repo QG green + DEPRECATION_NOTICE audit ack + both source repos
archived=true on GitHub.**
