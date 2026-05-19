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
      - [ ] [AGENT] P0. Phase 0 — Pre-audit manifest (read-only). Produce
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
    status: todo

  - id: phase-1-uac-utl-schema-prep
    content: |
      - [ ] [AGENT] P0. Phase 1 — UAC / UTL schema prep. Likely no new schema column needed — training-output
        events and inference-input events are already independent UAC types. Confirm by grepping UAC for
        existing data-type enums covering training-complete / model-promoted / prediction-emitted; if either
        source repo defined local event types not promoted to UAC (Phase 0 (e) finding), lift to UAC under
        `unified_api_contracts.canonical.crosscutting.lifecycle` or `unified_api_contracts.domain.ml`. Output:
        list of UAC PRs needed (likely 0-2 small) + UTL helper PRs for any kill-switch subscriber boilerplate
        lifts. Land BEFORE Phase 3 if non-empty.
    status: todo
    blocked_by: phase-0-pre-audit-manifest

  - id: phase-2-skeleton-new-repo
    content: |
      - [ ] [HUMAN+AGENT] P0. Phase 2 — Create NEW `ml-service` GitHub repo + bootstrap skeleton. Operator action:
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
    status: todo
    blocked_by: phase-1-uac-utl-schema-prep

  - id: phase-3-subtree-merge
    content: |
      - [ ] [AGENT] P0. Phase 3 — Subtree-merge both source repos into ml-service with full git history
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
    status: todo
    blocked_by: phase-2-skeleton-new-repo

  - id: phase-4-fix-imports-and-cli
    content: |
      - [ ] [AGENT] P0. Phase 4 — Fix internal imports + unify CLI + collapse `api/main.py` per sub-package.
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
        (h) **Docker layer separation** for inference-vs-training image weight: introduce conditional dep group
            (e.g. `[project.optional-dependencies] training = [...]`) so production live-inference Docker can build
            without sklearn/xgboost/optuna stack. Update Dockerfile build args accordingly. Verify image size
            regression vs ml-inference-service baseline is <30%.
    status: todo
    blocked_by: phase-3-subtree-merge

  - id: phase-5-lifts-to-utl
    content: |
      - [ ] [AGENT] P1. Phase 5 — Lift cross-cutting helpers to UTL where Phase 0 (f) audit identifies
        cross-source duplication. Specifically: model registry abstraction (`MlModelRegistry`), cloud feature
        provider (shared between training fit-time + inference predict-time), kill-switch bus subscriber for
        model-promotion events. Each lift = UTL PR + ml-service PR removing local copy. Defer to post-cutover if
        candidates <2 — lifts are correctness-neutral.
    status: todo
    blocked_by: phase-4-fix-imports-and-cli

  - id: phase-6-parity-test
    content: |
      - [ ] [AGENT] P0. Phase 6 — Symmetry / parity validation BEFORE archive. Three parity gates:
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
    status: todo
    blocked_by: phase-4-fix-imports-and-cli

  - id: phase-7-archive-source-repos
    content: |
      - [ ] [HUMAN+AGENT] P0. Phase 7 — Archive both source repos. Per-repo sequence:
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
    status: todo
    blocked_by: phase-6-parity-test

  - id: phase-8a-launcher-migration
    content: |
      - [ ] [AGENT] P0. Phase 8A — Launcher migration in `deployment-service/scripts/vm/`. `launch-ml-training-vm.sh`
        + `launch-ml-inference-vm.sh` collapse into a single `launch-ml-vm.sh` parameterised by `--operation`.
        Update `VM_PREFIX_TO_BUCKET` in `vm_zombie_watchdog.py` to drop ml-training / ml-inference prefixes and
        add ml-service prefix. Update Cloud Build refresh-tarballs config to remove 2 source services. Update
        Terraform service map — drop 2 entries, add ml-service.
    status: todo
    blocked_by: phase-7-archive-source-repos

  - id: phase-8b-deployment-api-ui
    content: |
      - [ ] [AGENT] P0. Phase 8B — `deployment-api` + `deployment-ui` updates. Service registry endpoints update
        to remove 2 source service IDs and expose per-operation health on ml-service. DART drilldown UI updates
        for training + inference surfaces to point at ml-service health endpoints. Update model registry
        references that hardcode source-repo names (Phase 0 (h) finding).
    status: todo
    blocked_by: phase-7-archive-source-repos

  - id: phase-9-codex-ssot-updates
    content: |
      - [ ] [AGENT] P0. Phase 9 — Codex SSOT updates. MANDATORY per HARD RULE "Post-Plan-Phase Codex Audit":
        (a) **NEW** `codex/04-architecture/ml-service-architecture.md` — full SSOT covering: 2 sub-packages
            (training + inference), CLI dispatch keyed by `--operation`, Health-API aggregator, model registry +
            promotion topology, feature-subscriber/prediction-publisher pub-sub wiring, ServiceBootstrap
            consolidation, deployment topology (single VM per asset-group × operation flavor with conditional
            training-deps Docker layer per Phase 4 (h)), migration history cross-link, anti-patterns.
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
    status: todo
    blocked_by: phase-8a-launcher-migration

  - id: phase-10-workspace-qg-sweep
    content: |
      - [ ] [AGENT] P0. Phase 10 — Workspace QG sweep + cross-plan coordination banner cleanup. Run QG in every
        workspace repo touched. Run inventory regenerator. Remove "🟡 IN-FLIGHT REFACTOR" banners added in
        pre-plan-Phase-0 announcement. Verify deployment-service end-to-end smoke (ml-service VM boots,
        completes `--operation train` + `--operation batch-inference` runs, STOPPED events emitted, manifest
        rows written, model promoted into registry, downstream strategy-service pulls promoted model). Final
        commit + push + plan-flip sweep.
    status: todo
    blocked_by: phase-9-codex-ssot-updates

  - id: phase-0-side-effect-soft-freeze-announcement
    content: |
      - [ ] [AGENT] P0. Phase 0 SIDE EFFECT — Cross-plan soft-freeze announcement on plans touching the 2
        affected repos. Banner:
        ```
        > **🟡 IN-FLIGHT REFACTOR — ml-repo-consolidation-2026-05-19** —
        > ml-training-service + ml-inference-service are being merged into new `ml-service` repo
        > 2026-05-19 → 2026-05-23. **Soft freeze**: NO new public-API surfaces, NO new top-level packages,
        > NO module renames in either source repo until Phase 7 archive lands. Internal bugfixes + test work +
        > plan-flip backfills continue.
        ```
        Banner-remove owned by this plan's Phase 10. Affected plan list per fact-report 2026-05-19 — enumerate
        in Phase 0 pre-audit artifact and link from each banner.
    status: todo
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

| Risk                                                                                            | Mitigation                                                                                                                    |
| ----------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| Phase 6 parity slips on numerical-equality gate (sklearn/xgboost determinism varies by version) | Strict seed pinning; deterministic-mode flags on libraries; tolerance bump to model-metric equality vs byte-identical weights |
| Live-inference Docker image bloat from training deps                                            | Phase 4 (h) conditional dep group + Dockerfile build-arg separation; size regression gate <30% vs baseline                    |
| Model registry pub-sub topic-rename window                                                      | Phase 0 (h) + Phase 4 atomic — topic-rename in single deploy, publishers + subscribers updated in lockstep                    |
| Operator delay on `gh repo create ml-service` blocks Phase 2                                    | Phase 2 is gated [HUMAN+AGENT]; agent pings via `_agent_pings.md` immediately on Phase 1 completion                           |
| Hidden cross-repo import surfaces Phase 0 misses                                                | Same as strategy twin — exhaustive grep + Phase 4 (g) verification                                                            |
| Other agents' in-flight work in the 2 repos                                                     | Soft-freeze banner per Phase 0 side-effect                                                                                    |

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

## Codex SSOT updates (mandatory enumeration — HARD RULE)

See Phase 9 — 8 enumerated codex paths (a-h). Plan-review-blocking if Phase 9 ships without all 8 verified.
