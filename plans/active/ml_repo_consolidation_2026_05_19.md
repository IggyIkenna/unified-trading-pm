---
name: ml-repo-consolidation-2026-05-19
overview:
  Merge `ml-training-service` + `ml-inference-service` into a single NEW `ml-service` repo with sub-packages
  `ml_service/training/` and `ml_service/inference/`; archive both source repos. ONE Docker image, ONE flat
  `pyproject.toml`, ONE Health-API exposing aggregated freshness, ONE CLI with `--operation` discriminating
  train / evaluate / hyperparam / batch-inference / live-inference / cascade-inference. Mirrors the
  `features-repo-consolidation-2026-05-08` pattern (10-phase: pre-audit → schema → skeleton → subtree-merge →
  fixup → lifts → parity → archive → downstream → codex → QG sweep). Motivation: training and inference are
  colocated activities in terms of deployment topology + share model registry + share UAC feature contracts +
  share archetype/strategy mapping — separate repos add coordination overhead without operational gain. Both
  source repos have zero direct Python imports of each other today (event-bus + GCS model registry decoupled),
  so subtree-merge has zero compile-time collisions. Pre-cutover race for 2026-05-23 live-DeFi launch — if Phase 6
  parity slips, plan flips to `BLOCKED-CUTOVER` and lands post-cutover; no late-binding hacks.
type: infra
epic: ml_and_features_master_2026_05_07
status: active

asset_group: cross-cutting
priority: P0
deadline: 2026-05-23
parent: master_to_live_defi_2026_05_23
locked_by: live-defi-rollout
locked_since: 2026-05-19
last_updated: 2026-05-19

estimate_class: infra
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 6

completion_gates:
  code: C5
  deployment: D2
  business: none

repo_gates:
  - repo: ml-service
    code: C0
    deployment: none
    business: none
  - repo: ml-service (training sub-package)
    code: C0
    deployment: none
    business: none
  - repo: ml-service (inference sub-package)
    code: C0
    deployment: none
    business: none
  - repo: ml-training-service
    code: C0
    deployment: none
    business: none
  - repo: ml-inference-service
    code: C0
    deployment: none
    business: none
  - repo: unified-api-contracts
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-library
    code: C0
    deployment: none
    business: none
  - repo: deployment-api
    code: C0
    deployment: none
    business: none
  - repo: deployment-ui
    code: C0
    deployment: none
    business: none
  - repo: deployment-service
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-pm
    code: C0
    deployment: none
    business: none

depends_on: []

todos:
  - id: phase-0-pre-audit-manifest
    content: |
      - [x] ✅ [AGENT] P0. Phase 0 — Pre-audit manifest (read-only). Produce
        `plans/active/issues/ml_repo_consolidation_preaudit_2026_05_19.md` enumerating, per source repo
        (`ml-training-service`, `ml-inference-service`):
        (a) every Python module + class + public function + post-merge sub-package landing
            (`ml_service/training/`, `ml_service/inference/`);
        (b) every callsite OUTSIDE the source repo that imports from `ml_training_service.*` /
            `ml_inference_service.*` — grep across all sibling repos under `${WORKSPACE_ROOT}` (UAC / UTL / UCI /
            MTDS / MDPS / instruments-service / features-service / strategy-service / execution-service /
            unified-trading-pm / deployment-api / deployment-ui / deployment-service / e2e-testing). Fact-report
            2026-05-19 showed ZERO cross-repo Python imports, but verify and capture line-level evidence;
        (c) every script under `scripts/` per source repo + post-merge home;
        (d) every test under `tests/` per source repo + post-merge home (`ml-service/tests/training/`,
            `ml-service/tests/inference/`);
        (e) every UAC / UTL symbol the source repo redefines locally — especially around feature-subscriber
            schemas, model-promotion event contracts, prediction-publisher row schemas, ensemble metadata;
        (f) every cross-package helper duplicated across both source repos (lift-to-UTL candidates) —
            `ServiceBootstrap` patterns, kill-switch bus subscriber boilerplate, ManifestFreshnessCache adoption,
            `config_reloaders.py` typed-class wiring, cloud feature provider abstraction;
        (g) per-repo `pyproject.toml` dependency union — resolve version conflicts ahead of Phase 3 (likely
            non-trivial: ml-training pulls full sklearn/xgboost/lightgbm/optuna stack, ml-inference pulls leaner
            inference deps; flat union must avoid bloating live-inference Docker image — split via optional
            inference-only build flag if needed);
        (h) hardcoded service-name strings — `"ml-training-service"` / `"ml-inference-service"` as pub/sub topic
            prefixes, env-var prefixes (`ML_TRAINING_SERVICE_*` / `ML_INFERENCE_SERVICE_*`), GCS bucket subpaths,
            model registry references, deployment-service terraform refs. Topic-name compatibility decisions
            land here.
        Output drives every later phase. **Foot-gun**: model promotion topic-name changes invalidate
        ml-inference's `model_promotion_subscriber` until subscribers + publishers align — sequence Phase 4 (b)
        atomically.
        Evidence: slot-1 produced `plans/active/issues/ml_repo_consolidation_preaudit_2026_05_19.md` (2026-05-19).
        Key findings: 0 external Python imports workspace-wide; 35 unique dep union; config_reloaders.py near-identical
        (UTL lift candidate); ML_MODEL_COORDINATION_TOPIC is wire-protocol constant (no rename needed).
    status: done

  - id: phase-1-uac-utl-schema-prep
    content: |
      - [x] ✅ [AGENT] P0. Phase 1 — UAC / UTL schema prep. Likely no new schema column needed — training-output
        events and inference-input events are already independent UAC types. Confirm by grepping UAC for
        existing data-type enums covering training-complete / model-promoted / prediction-emitted; if either
        source repo defined local event types not promoted to UAC (Phase 0 (e) finding), lift to UAC under
        `unified_api_contracts.canonical.crosscutting.lifecycle` or `unified_api_contracts.domain.ml`. Output:
        list of UAC PRs needed (likely 0-2 small) + UTL helper PRs for any kill-switch subscriber boilerplate
        lifts. Land BEFORE Phase 3 if non-empty.
        **RESULT (2026-05-19 slot-8)**: 0 blocking PRs before Phase 3.
        - PredictionEvent (engine/schemas.py): CORRECT-LOCAL (docstring confirmed, not cross-service). Stays.
        - PredictionEventDict/PredictionMetadata (types.py): CORRECT-LOCAL comment present. Stays.
        - EnsembleConfig (ensemble_inference.py): DIFFERENT from UAC EnsembleConfig (runtime weights vs training
          config). Stays local.
        - ModelTrainedEvent + ModelPromotedEvent: dict-based wire protocols; DEFERRED to Phase 4 (f) as TypedDicts
          under `unified_api_contracts.internal.domain.ml`. Not blocking Phase 3 — both dicts already stable.
        - Kill-switch boilerplate: grep returned 0 hits in both repos. No UTL lift needed.
        - UAC `internal.domain.ml` already has: EnsembleConfig, ModelMetadata, InferenceRequest, InferenceResult.
        - UAC `internal.domain.ml_inference_service` already has: CascadeConfig, CascadePredictionEvent,
          PredictionSnapshot.
        - 0 UAC PRs + 0 UTL PRs needed before Phase 3.
    status: done

  - id: phase-2-skeleton-new-repo
    content: |
      - [x] **DEFERRED-OPERATOR-DECISION 2026-05-19 slot-5** [HUMAN+AGENT] P0. Phase 2 — Create NEW `ml-service` GitHub repo + bootstrap skeleton. Operator action:
        `gh repo create IggyIkenna/ml-service --private --add-readme` then operator pings agent. Agent then:
        (a) `git clone` ml-service locally into `.tabs/<N>/ml-service/`;
        (b) bootstrap directory structure mirroring features-service precedent: `ml_service/{api,cli,training,
            inference,common}/`, `tests/`, `scripts/`, `Dockerfile`, `pyproject.toml`, `buildspec.aws.yaml`,
            `cloudbuild.yaml`, `pyrightconfig.json`, `.pre-commit-config.yaml`, `.github/workflows/`;
        (c) seed `pyproject.toml` with the union of dependencies from both source repos (resolved per Phase 0 (g));
            flat list, no extras;
        (d) seed `ml_service/api/main.py` with `make_health_router` from UTL exposing
            `/health/{training,inference}` + aggregated freshness callback;
        (e) seed `ml_service/cli/main.py` with `--operation {train,evaluate,hyperparam,batch-inference,
            live-inference,cascade-inference}` dispatcher;
        (f) seed `ServiceBootstrap` at top level (STARTED / STOPPED / FAILED);
        (g) run `bash unified-trading-pm/scripts/workflow-templates/rollout-workflow-templates.sh` to copy
            workspace workflow templates into `ml-service/.github/workflows/`;
        (h) add `ml-service` to `unified-trading-system-repos.code-workspace` folders + `workspace-manifest.json`
            repo registry + `setup-tab-worktrees.sh` enumeration if explicit;
        (i) commit empty skeleton on `main`, push, verify CI green.
    status: deferred-operator-decision
    blocked_by: phase-1-uac-utl-schema-prep

  - id: phase-3-subtree-merge
    content: |
      - [x] **FORMALLY DEFERRED 2026-05-19 slot-5** [AGENT] P0. Phase 3 — Subtree-merge both source repos into ml-service with full git history
        preserved. For each of {ml-training-service, ml-inference-service}:
        ```bash
        cd ml-service
        git remote add -f <source>-remote ../<source>
        git merge -s ours --no-commit --allow-unrelated-histories <source>-remote/main
        git read-tree --prefix=ml_service/<sub>/ -u <source>-remote/main:<source_package>/
        git read-tree --prefix=tests/<sub>/ -u <source>-remote/main:tests/
        git read-tree --prefix=scripts/<sub>/ -u <source>-remote/main:scripts/
        git commit -m "feat(consolidation): subtree-merge <source> into ml_service/<sub>/"
        ```
        Each subtree-merge is ONE commit per source repo (2 total). Verify `git log --follow
        ml_service/training/<file>` reaches pre-merge history. **Foot-gun**: subtree-merge does NOT rewrite import
        statements — `ml_service/training/__init__.py` still imports `from ml_training_service.app.core import ...`
        until Phase 4. QG WILL fail between Phase 3 and Phase 4; keep Phase 4 in the same agent turn.
    status: formally-deferred
    blocked_by: phase-2-skeleton-new-repo

  - id: phase-4-fix-imports-and-cli
    content: |
      - [x] **FORMALLY DEFERRED 2026-05-19 slot-5** [AGENT] P0. Phase 4 — Fix internal imports + unify CLI + collapse `api/main.py` per sub-package.
        (a) sed-rewrite every `from ml_training_service.*` → `from ml_service.training.*` and `from
            ml_inference_service.*` → `from ml_service.inference.*` inside the merged tree;
        (b) collapse 2 source `cli/main.py` entrypoints into `ml_service/cli/main.py` dispatcher keyed by
            `--operation`; preserve every existing CLI flag verbatim;
        (c) consolidate 2 source `api/main.py` Health-API routers into ml-service's router with sub-paths
            (`/health/training`, `/health/inference`); per-surface `data_freshness` callbacks merge into single
            `make_health_router` call;
        (d) merge `config_reloaders.py` per source repo into ml-service's typed `MlServiceConfig` root (one
            sub-namespace per surface);
        (e) consolidate per-repo `ServiceBootstrap` invocations into ONE at ml-service top level;
        (f) merge per-repo `tests/conftest.py` fixtures — prefix on collision (`training_<fixture>`,
            `inference_<fixture>`);
        (g) run `bash scripts/quality-gates.sh` in ml-service — STEP 5.61 ServiceBootstrap, STEP 5.62
            api/main.py + make_health_router, STEP 5.34 typed config_reloaders, STEP 5.66 per-VM shard isolation,
            STEP 5.69 bucket-name SSOT must all pass;
        (h) **Single flat-deps Docker image** (operator decision 2026-05-19, Option 2 — hold the flat-deps line):
            ONE `pyproject.toml` with one flat `[project.dependencies]` list (35 deps); ONE Docker image
            (~1100-1200MB) regardless of `--operation`. NO conditional dep group, NO `INFERENCE_ONLY` build-arg.
            Rationale: live-inference runs on long-lived VMs (not scale-to-zero serverless); cold-start is a
            one-time cost per VM bringup, not per-prediction. 55-60% size win would not buy a meaningful
            operational benefit on this topology. Flat-deps rule per CLAUDE.md `### Dependencies + builds`
            preserved workspace-wide; no exceptions added. Image-size regression cap removed from Phase 6 parity.
    status: formally-deferred
    blocked_by: phase-3-subtree-merge

  - id: phase-5-lifts-to-utl
    content: |
      - [x] **FORMALLY DEFERRED 2026-05-19 slot-5** [AGENT] P1. Phase 5 — Lift cross-cutting helpers to UTL where Phase 0 (f) audit identifies
        cross-source duplication. Specifically: model registry abstraction (`MlModelRegistry`), cloud feature
        provider (shared between training fit-time + inference predict-time), kill-switch bus subscriber for
        model-promotion events. Each lift = UTL PR + ml-service PR removing local copy. Defer to post-cutover if
        candidates <2 — lifts are correctness-neutral.
    status: formally-deferred
    blocked_by: phase-4-fix-imports-and-cli

  - id: phase-6-parity-test
    content: |
      - [x] **FORMALLY DEFERRED 2026-05-19 slot-5** [AGENT] P0. Phase 6 — Symmetry / parity validation BEFORE archive. Three parity gates:
        (1) **Boot parity**: `python -m ml_service --operation <op> --asset-group <ag> --mode batch` boots for
            every {operation × asset_group} pair the 2 source repos previously supported. STARTED captured per
            case. Startup-time regression >2× is a stop.
        (2) **QG parity**: `bash scripts/quality-gates.sh` green in ml-service AND no regression vs source repos'
            last-pre-archive QG runs (record baselines pre-merge; STEP-by-STEP comparison post-merge).
        (3) **Functional parity**:
              - training: run hyperparam sweep + final-training on a 7-day archetype dataset; compare ensemble
                model metadata + cross-validation metrics to ml-training-service pre-archive output. Tolerance:
                model weights byte-identical (deterministic seeded run) OR cross-val score within `1e-6`.
              - inference: batch-inference + live-inference on a 1-day prediction request stream; compare
                prediction output row-by-row to ml-inference-service pre-archive output. Numerical equality
                within `1e-9`.
              - cascade-inference: 2-stage meta-signal cascade end-to-end on recorded feature stream; output
                equality.
            Write `scripts/dev/ml_parity_diff.py` (mirroring `feature_parity_diff.py` from features-service
            precedent) to automate. Any RED gate → plan flips to `BLOCKED-CUTOVER`; archive does NOT proceed.
    status: formally-deferred
    blocked_by: phase-4-fix-imports-and-cli

  - id: phase-7-archive-source-repos
    content: |
      - [x] **FORMALLY DEFERRED 2026-05-19 slot-5** [HUMAN+AGENT] P0. Phase 7 — Archive both source repos. Per-repo sequence:
        1. Add `DEPRECATION_NOTICE.md` banner: "**ARCHIVED 2026-05-XX** — code merged into ml-service via
           ml_repo_consolidation_2026_05_19.md. New work + bug fixes go to ml-service/ml_service/<training|inference>/."
        2. Final commit: `chore(archive): merged into ml-service per ml_repo_consolidation_2026_05_19`. Push to main.
        3. `gh repo archive IggyIkenna/ml-<training|inference>-service --confirm` (operator action; shared-state
           gate — agent files ping in `_agent_pings.md`).
        4. Remove from `unified-trading-system-repos.code-workspace` folders list.
        5. Remove from `workspace-manifest.json`; mark `status=consolidated-into-ml-service`,
           `archived_into=ml-service`, `archive_date=<date>`.
        6. Update `unified-trading-pm/scripts/dev/setup-tab-worktrees.sh` if 2 source repos enumerated explicitly.
        7. Verify `gh api repos/IggyIkenna/<repo> --jq .archived` returns `true` for both.
        **Foot-gun**: do NOT archive before Phase 6 parity green.
    status: formally-deferred
    blocked_by: phase-6-parity-test

  - id: phase-8a-launcher-migration
    content: |
      - [x] **FORMALLY DEFERRED 2026-05-19 slot-5** [AGENT] P0. Phase 8A — Launcher migration in `deployment-service/scripts/vm/`. `launch-ml-training-vm.sh`
        + `launch-ml-inference-vm.sh` collapse into a single `launch-ml-vm.sh` parameterised by `--operation`.
        Update `VM_PREFIX_TO_BUCKET` in `vm_zombie_watchdog.py` to drop ml-training / ml-inference prefixes and
        add ml-service prefix. Update Cloud Build refresh-tarballs config to remove 2 source services. Update
        Terraform service map — drop 2 entries, add ml-service.
    status: formally-deferred
    blocked_by: phase-7-archive-source-repos

  - id: phase-8b-deployment-api-ui
    content: |
      - [x] **FORMALLY DEFERRED 2026-05-19 slot-5** [AGENT] P0. Phase 8B — `deployment-api` + `deployment-ui` updates. Service registry endpoints update
        to remove 2 source service IDs and expose per-operation health on ml-service. DART drilldown UI updates
        for training + inference surfaces to point at ml-service health endpoints. Update model registry
        references that hardcode source-repo names (Phase 0 (h) finding).
    status: formally-deferred
    blocked_by: phase-7-archive-source-repos

  - id: phase-9-codex-ssot-updates
    content: |
      - [x] **FORMALLY DEFERRED 2026-05-19 slot-5** [AGENT] P0. Phase 9 — Codex SSOT updates. MANDATORY per HARD RULE "Post-Plan-Phase Codex Audit":
        (a) **NEW** `codex/04-architecture/ml-service-architecture.md` — full SSOT covering: 2 sub-packages
            (training + inference), CLI dispatch keyed by `--operation`, Health-API aggregator, model registry +
            promotion topology, feature-subscriber/prediction-publisher pub-sub wiring, ServiceBootstrap
            consolidation, deployment topology (single VM per asset-group × operation flavor with single
            flat-deps Docker image per operator decision 2026-05-19 Option 2), migration history cross-link,
            anti-patterns.
        (b) **UPDATE** `codex/00-SSOT-INDEX.md` — register new architecture page; drop 2 archived repos.
        (c) **UPDATE** `codex/02-data/README.md` — ML data lineage now references `ml-service` (was 2 repos).
        (d) **UPDATE** `codex/04-architecture/promote-workflow-architecture.md` — promote workflow references
            `ml-service` for inference-image pinning + model promotion gate.
        (e) **UPDATE** `codex/05-infrastructure/launcher-script-ssot.md` — 2-to-1 launcher collapse.
        (f) **UPDATE** `codex/05-infrastructure/vm-tarball-deployment.md` — single ml-service tarball.
        (g) **UPDATE** `codex/06-coding-standards/cli-convention.md` — `--operation` sub-command table for
            ml-service's 6+ operations.
        (h) **UPDATE** any other codex page surfaced by `rg "ml-training-service|ml-inference-service" codex/` —
            replace with `ml-service/<sub>/` or add SUPERSEDED banner.
    status: formally-deferred
    blocked_by: phase-8a-launcher-migration

  - id: phase-10-workspace-qg-sweep
    content: |
      - [x] **FORMALLY DEFERRED 2026-05-19 slot-5** [AGENT] P0. Phase 10 — Workspace QG sweep + cross-plan coordination banner cleanup. Run QG in every
        workspace repo touched. Run inventory regenerator. Remove "🟡 IN-FLIGHT REFACTOR" banners added in
        pre-plan-Phase-0 announcement. Verify deployment-service end-to-end smoke (ml-service VM boots,
        completes `--operation train` + `--operation batch-inference` runs, STOPPED events emitted, manifest
        rows written, model promoted into registry, downstream strategy-service pulls promoted model). Final
        commit + push + plan-flip sweep.
    status: formally-deferred
    blocked_by: phase-9-codex-ssot-updates

  - id: phase-0-side-effect-soft-freeze-announcement
    content: |
      - [x] ✅ [AGENT] P0. Phase 0 SIDE EFFECT — Cross-plan soft-freeze announcement on plans touching the 2
        affected repos. Banner inserted to 20 plans (2026-05-19) — ml-training-service + ml-inference-service. Banner:
        ```
        > **🟡 IN-FLIGHT REFACTOR — ml-repo-consolidation-2026-05-19** —
        > ml-training-service + ml-inference-service are being merged into new `ml-service` repo
        > 2026-05-19 → 2026-05-23. **Soft freeze**: NO new public-API surfaces, NO new top-level packages,
        > NO module renames in either source repo until Phase 7 archive lands. Internal bugfixes + test work +
        > plan-flip backfills continue.
        ```
        Banner-remove owned by this plan's Phase 10. Affected plan list per fact-report 2026-05-19 — enumerate
        in Phase 0 pre-audit artifact and link from each banner.
        Evidence: 20 plans patched 2026-05-19 (slot-8). Plans: AUDIT_2026_05_15_harsh_side_completion,
        alerting_service_live_rules_2026_05_07, bucket_name_ssot_canonicalisation_2026_05_10,
        codex_vs_citadel_infrastructure_audit_2026_05_10, compute_optimization_mock_data_2026_05_13,
        continuation_prompts_2026_05_13_harsh, continuation_prompts_harsh_2026_05_15,
        cross_cutting_may_23_deliverables_2026_05_08, deployment_and_qg_strategy_implementation_2026_05_13,
        expected_unattempted_propagation_chain_2026_05_12, features_repo_consolidation_2026_05_08,
        features_service_qg_cleanup_2026_05_11, master_to_live_defi_2026_05_23,
        mock_data_pipeline_benchmarking_2026_05_10, ruff_workspace_cleanup_2026_05_12,
        strategy_repo_consolidation_2026_05_19, work_split_2026_05_13_harsh, work_split_2026_05_18_ikenna,
        work_split_2026_05_19_ikenna, writegate_honest_coverage_endtoend_2026_05_06.
    status: done
---

> **🟡 IN-FLIGHT REFACTOR — strategy-repo-consolidation-2026-05-19** — strategy-service is absorbing risk-and-exposure-service + position-balance-monitor-service + pnl-attribution-service as sub-packages 2026-05-19 → 2026-05-23. **Soft freeze**: NO new public-API surfaces, NO new top-level packages, NO module renames in any of the 4 repos until Phase 7 archive lands. Internal bugfixes + test work + plan-flip backfills continue.


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
  2026-05-23 cutover; fold under existing `ml_and_features_master_2026_05_07` epic.
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
- [x] **FORMALLY DEFERRED 2026-05-19 slot-5** **P1** [AGENT] Phase 5 lift — `pre_crash_checkpoint.py` (`register_pre_crash_handlers()`, `_memory_watchdog()`)
      currently only in inference repo. Cross-cutting utility — lift to UTL
      `unified_trading_library.lifecycle.pre_crash`. Every service benefits.
- [x] **FORMALLY DEFERRED 2026-05-19 slot-5** **P1** [AGENT] Phase 5 lift — `config_reloaders.py` near-identical between the 2 source repos (verified via
      `diff -u`). Primary UTL lift candidate — `ConfigReloaderBase` in
      `unified_trading_library.config_interface.config_reloader_base`. Composes with strategy-twin plan's 4×
      config_reloaders lift (5 → 1 base class workspace-wide).
- [x] **FORMALLY DEFERRED 2026-05-19 slot-5** **P1** [AGENT] Phase 9 codex sweep scope confirmed — **455 file:line refs** across
      `unified-trading-pm/cursor-configs/` + `unified-trading-pm/codex/` reference the 2 source repo names. Phase 9 (h)
      bulk-sed rewrite. Plan a single sed sweep across both directories; verify no false-positives in archived docs.
- [x] **FORMALLY DEFERRED 2026-05-19 slot-5** **P1** [AGENT] Phase 7 cleanup — legacy top-level `ml-training-service/tests/test_*.py` files (~30) duplicate the
      structured `tests/unit/test_*.py` set. Consolidate during Phase 7 (post-archive); keep only the structured set in
      merged `ml-service/tests/training/`.
- [x] **FORMALLY DEFERRED 2026-05-19 slot-5** **P2** [AGENT] Phase 1 lift — `ML_MODEL_COORDINATION_TOPIC`, `CASCADE_TOPIC_NAME`, `MTF_TOPIC_NAMES` currently
      duplicated as string literals between publisher/subscriber. Lift to UAC
      `unified_api_contracts.canonical.crosscutting.events.topics` (or equivalent). NOT cutover-blocking; current
      literals match across repos so wire protocol is stable.
- [x] **FORMALLY DEFERRED 2026-05-19 slot-5** **P2** [AGENT] Phase 5 — ml-service is a candidate for `ManifestFreshnessCache` adoption (UTL
      `unified_trading_library.manifest_freshness.ManifestFreshnessCache`). Neither source repo currently uses it.
      Post-merge consolidation phase.
- [x] **FORMALLY DEFERRED 2026-05-19 slot-5** **P2** [AGENT] Phase 4 (c) — `ml_inference_service.api.prediction_stream` SSE endpoint is INFERENCE-only; the
      merged `make_health_router` aggregator must continue routing `/stream/predictions` via the inference sub-app
      router (not a global ml-service router). Verify in Phase 4 (c) consolidation.
- [x] **FORMALLY DEFERRED 2026-05-19 slot-5** **P2** [AGENT] Phase 4 (g) verify `PYTEST_UNIT_DIR="tests/"` override applied — inference's `tests/perf/` exists
      only in inference repo. Without the override the merged QG silently skips perf tests.
- [x] **FORMALLY DEFERRED 2026-05-19 slot-5** **P2** [AGENT] Phase 8B audit — `verify_service_token` from `auth_s2s.py` is built per-repo via
      `create_s2s_auth_dependency("ml-{training,inference}-service")`. Post-merge → single
      `create_s2s_auth_dependency("ml-service")` BUT downstream callers in deployment-api / strategy-service may pass
      the old service names in S2S tokens. Audit S2S token issuance + verification cutover.

### Gap-close 2026-05-19 — coverage amendments (post-dispatch audit)

Operator-validation question 2026-05-19 surfaced 4 gaps in the original 10-phase scope. Closing now before
slot 9 boots. All amendments bundle into slot 9's existing scope (~1.5 cal-day extension total).

- [x] **FORMALLY DEFERRED 2026-05-19 slot-5** **P0 NEW** [AGENT slot 9] Phase 4 (a-extension) — e2e-testing scripts beyond Python imports. Phase 4 (a)
  covers ~3-4 string-literal updates from pre-audit § (b). Add: grep `e2e-testing/scripts/` +
  `system-integration-tests/scripts/` + `e2e-testing/scripts/*.sh` for (i) shell invocations of
  `python -m ml_{training,inference}_service`, (ii) any console-script names, (iii) bare-Python entry-point
  invocations. Rewrite to `python -m ml_service --operation <op>`. ~0.25 cal-day.
- [x] **FORMALLY DEFERRED 2026-05-19 slot-5** **P1 NEW** [AGENT slot 9] Phase 4 (i) — Logging + observability config consolidation. Per-service
  `setup_events()` callsites + log levels + formatters + structured-log field naming. Decide: per-sub-package
  logger naming (`ml_service.training` / `ml_service.inference`) for filterability. OpenTelemetry tracers +
  Prometheus metrics + Cloud Trace spans — collapse `service.name=ml-{training,inference}-service` to
  `service.name=ml-service` and add `subsurface={training,inference}` label dimension. Mirrors strategy-twin
  Phase 4 (i); coordinate label naming via slot 4 (ConfigReloaderBase + log-naming might share UTL surface).
  ~0.5 cal-day.
- [x] **FORMALLY DEFERRED 2026-05-19 slot-5** **P2 NEW** [AGENT slot 9] Phase 3 addendum — Drop source-repo `docs/` subdirectories during
  subtree-merge. `git read-tree --prefix=ml_service/<sub>/` pulls package + tests + scripts only; `docs/`
  intentionally NOT merged (codex is workspace SSOT). Record in each archived source repo's
  `DEPRECATION_NOTICE.md` (Phase 7): "docs/ content not migrated — see
  `codex/04-architecture/ml-service-architecture.md`."
- [x] **FORMALLY DEFERRED 2026-05-19 slot-5** **P2 NEW** [AGENT slot 9] Phase 2 addendum + Phase 8A addendum — GitHub Actions workflows. Phase 2 (g)
  already runs `rollout-workflow-templates.sh` to seed ml-service with templated workflows. Add: enumerate any
  per-source-repo CUSTOM workflows (cron-scheduled checks, scheduled retraining jobs, scheduled model-bake
  workflows) in source repos that AREN'T in the rollout template. For each: (a) migrate to ml-service workflow
  with `--operation` axis, OR (b) confirm purpose obsolete post-merge. ~0.25 cal-day.
- [x] **FORMALLY DEFERRED 2026-05-19 slot-5** **P3 NEW** [AGENT slot 9] Phase 7 addendum — Per-repo markdown files (CHANGELOG.md /
  QUALITY_GATE_BYPASS_AUDIT.md / CONTRIBUTING.md / per-source-repo notes). Decision: (a) `CHANGELOG.md`
  content prepended to `ml-service/CHANGELOG.md` under "## Consolidation 2026-05-19" heading; (b)
  `QUALITY_GATE_BYPASS_AUDIT.md` merged into ml-service's QGBA per sub-package row; (c) `CONTRIBUTING.md` +
  ad-hoc per-repo markdown — preserve only the workspace-canonical version in ml-service root. ~0.1 cal-day.
- [x] **FORMALLY DEFERRED 2026-05-19 slot-5** **P3 NEW** [AGENT slot 9] Phase 2 addendum — GitHub repo settings on NEW ml-service repo. Phase 2 (a)
  creates the repo via `gh repo create`. Add: configure branch protection on `main` (require `quality-gates`
  + `workspace-qg` + `staging-lock-check` status checks); enable semver-agent (write
  `.github/semver-agent.yml` per workspace template); enable required PR reviews; disable force-push on
  protected branches. Cross-reference: `unified-trading-pm/scripts/workflow-templates/` for the canonical
  template set. ~0.1 cal-day.

**Total gap-close additions**: ~1.2 cal-AI-days bundled into slot 9's existing 6 cal-day budget → revised
estimate ~7.2 cal-AI-days for ML consolidation. Still single-slot ownership; no new slot needed.

### Risk register additions (post-audit)

| Risk                                                                         | Severity  | Mitigation                                                                                                                              |
| ---------------------------------------------------------------------------- | --------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `FeatureSubscriber` name-collision blocks clean subtree-merge                | 🟡 Medium | P0 rename above; land BEFORE Phase 3 OR during Phase 4 (a) — strict ordering required                                                   |
| Flat-deps rule violation rejected by operator → bloated live-inference image | 🟢 Low    | Operator ping filed; if rejected, fall back to single flat-union image (accept ~55-60% bloat; document in plan)                         |
| Topic-name match assumption breaks post-merge (someone changes the literal)  | 🟢 Low    | P2 lift to UAC promotes the shared constant; bulk verify pre-Phase-3 + post-Phase-4 via `rg ML_MODEL_COORDINATION_TOPIC` workspace-wide |

## Codex SSOT updates (mandatory enumeration — HARD RULE)

See Phase 9 — 8 enumerated codex paths (a-h). Plan-review-blocking if Phase 9 ships without all 8 verified.
