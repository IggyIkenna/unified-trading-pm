---
name: strategy-repo-consolidation-2026-05-19
overview:
  Subtree-merge `risk-and-exposure-service`, `position-balance-monitor-service`, `pnl-attribution-service` INTO the
  existing `strategy-service` repo as sub-packages (`strategy_service/risk/`, `strategy_service/position/`,
  `strategy_service/pnl/`), then archive the 3 source repos. ONE Docker image, ONE flat `pyproject.toml`, ONE
  Health-API exposing aggregated freshness, ONE CLI with `--operation` discriminating risk-monitor / position-recon /
  pnl-attribution / strategy-batch / strategy-live / backtest. Mirrors the `features-repo-consolidation-2026-05-08`
  pattern (10-phase: pre-audit → schema → skeleton → subtree-merge → fixup → lifts → parity → archive → downstream →
  codex → QG sweep). Motivation: paper trading, live trading, batch backtest for strategy + the three monitoring
  services are colocated on the same VM in deployment topology — separate repos add merge-coordination overhead
  without operational gain. `strategy-service` is the umbrella (largest package, owns promote target + V2 strategies
  + portfolio allocator); the 3 monitoring services become sub-packages. Cross-repo imports today = zero (event-bus
  decoupled), so subtree-merge has zero compile-time collisions. Pre-cutover race for 2026-05-23 live-DeFi launch —
  if Phase 6 parity slips, plan flips to `BLOCKED-CUTOVER` and lands post-cutover; no late-binding hacks.
type: infra
epic: strategy_and_dart_master_2026_05_07
status: active

asset_group: cross-cutting
priority: P0
deadline: 2026-05-23
parent: master_to_live_defi_2026_05_23
locked_by: live-defi-rollout
locked_since: 2026-05-19
last_updated: 2026-05-19

estimate_class: infra
estimate_baseline_ai_days: 15
estimate_calibrated_ai_days: 12

completion_gates:
  code: C5
  deployment: D2
  business: none

repo_gates:
  - repo: strategy-service
    code: C0
    deployment: none
    business: none
  - repo: strategy-service (risk sub-package)
    code: C0
    deployment: none
    business: none
  - repo: strategy-service (position sub-package)
    code: C0
    deployment: none
    business: none
  - repo: strategy-service (pnl sub-package)
    code: C0
    deployment: none
    business: none
  - repo: risk-and-exposure-service
    code: C0
    deployment: none
    business: none
  - repo: position-balance-monitor-service
    code: C0
    deployment: none
    business: none
  - repo: pnl-attribution-service
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
        `plans/active/issues/strategy_repo_consolidation_preaudit_2026_05_19.md` enumerating, per source repo
        (`risk-and-exposure-service`, `position-balance-monitor-service`, `pnl-attribution-service`):
        (a) every Python module + class + public function + post-merge sub-package landing
            (`strategy_service/risk/`, `strategy_service/position/`, `strategy_service/pnl/`);
        (b) every callsite OUTSIDE the source repo that imports from `risk_and_exposure_service.*` /
            `position_balance_monitor_service.*` / `pnl_attribution_service.*` — grep across all sibling repos under
            `${WORKSPACE_ROOT}` (UAC / UTL / UCI / UEI / MTDS / MDPS / instruments-service / ml-training-service /
            ml-inference-service / strategy-service / execution-service / unified-trading-pm / deployment-api /
            deployment-ui / deployment-service / e2e-testing). Fact-report 2026-05-19 showed ZERO cross-repo Python
            imports, but verify and capture exact line-level evidence; any hits get rows: repo, file, line, import
            statement, post-merge replacement;
        (c) every script under `scripts/` per source repo + its post-merge home;
        (d) every test under `tests/` per source repo + its post-merge home (`strategy-service/tests/risk/` etc.);
        (e) every UAC / UTL symbol the source repo redefines locally that should be imported from upstream instead
            (Citadel-Grade § 7 SSOT rule — catch self-declared duplicates, especially around kill-switch event
            schemas, breaker-trip events, PnL attribution row contracts);
        (f) every cross-package helper duplicated across ≥2 source repos (lift-to-UTL candidates) — specifically
            `ServiceBootstrap` callsite patterns, kill-switch bus subscriber boilerplate, ManifestFreshnessCache
            adoption status, `config_reloaders.py` typed-class wiring;
        (g) per-repo `pyproject.toml` dependency union — find conflicts (different pinned versions of same dep) and
            resolve to single flat dependency list ahead of Phase 3;
        (h) hardcoded service-name strings in source — `"risk-and-exposure-service"` / etc. as pub/sub topic
            prefixes, env-var prefixes (`RISK_AND_EXPOSURE_SERVICE_*`), GCS bucket subpaths, deployment-service
            terraform refs (see Phase 8 for the wider deployment-service sweep). Topic-name compatibility decisions
            land here (rename vs keep-legacy-prefix-for-subscribers).
        Output drives every later phase; the entire migration's correctness depends on catching every external
        import + every hardcoded service-name string. **Foot-gun**: `unified-trading-pm/cursor-configs/` and
        `unified-trading-pm/codex/` reference module paths in docs (search for module substring, not just `import`).
        — PM@slot-1-sub-agent (2026-05-19); pre-audit artifact created; 25 external imports found across 7 files
    status: done

  - id: phase-1-uac-utl-schema-prep
    content: |
      - [x] ✅ [AGENT] P0. Phase 1 — UAC / UTL schema prep. N/A — pre-audit §(e) confirmed no new UAC schema
        columns or UAC PRs needed. All 3 source repos already import UAC types correctly (risk: 36× UAC/23× UTL;
        PBM: 63× UAC/46× UTL; PnL: 7× UAC/13× UTL). Kill-switch bus subscriber pattern is healthy (uses
        UAC `KillSwitchBusEvent`). UTL lift candidates (config_reloaders 4×, kill_switch_bus_subscriber 4×)
        are Phase 5 scope, not Phase 1 UAC PRs. — PM@slot-5 2026-05-19 (backfill; N/A determination)
    status: done

  - id: phase-2-skeleton
    content: |
      - [x] ✅ [AGENT] P0. Phase 2 — Skeleton scaffolding in strategy-service (in-place, no new repo). Create empty
        sub-package dirs `strategy_service/risk/`, `strategy_service/position/`, `strategy_service/pnl/` with
        `__init__.py` shims that will receive the subtree-merge in Phase 3. Update `strategy-service/pyproject.toml`
        with the union of dependencies from the 3 source repos (resolved per Phase 0 (g)). Update
        `strategy-service/api/main.py` Health-API to expose aggregated freshness across all 4 surfaces (strategy
        signal freshness + risk-monitor heartbeat + position-recon last-run + pnl-attribution last-run). Add CLI
        operation discriminators in `strategy_service/cli/service_entry.py`: `--operation risk-monitor | position-recon |
        pnl-attribution` as stub handlers. Commit on `live-defi-rollout` branch.
        **Foot-gun**: do NOT yet move any code from source repos — Phase 2 is empty scaffolding so Phase 3
        subtree-merge has landing zones with no name collisions.
        — strategy-service@eee8bbb (2026-05-19); 1990 tests pass; ruff + basedpyright clean
    status: done

  - id: phase-3-subtree-merge
    content: |
      - [x] ✅ [AGENT] P0. Phase 3 — Subtree-merge 3 source repos into strategy-service with full git history
        preserved. For each of {risk-and-exposure-service, position-balance-monitor-service, pnl-attribution-service}:
        ```bash
        cd strategy-service
        git remote add -f <source>-remote ../<source>-service
        git merge -s ours --no-commit --allow-unrelated-histories <source>-remote/main
        git read-tree --prefix=strategy_service/<sub>/ -u <source>-remote/main:<source_service>/
        git read-tree --prefix=tests/<sub>/ -u <source>-remote/main:tests/
        git read-tree --prefix=scripts/<sub>/ -u <source>-remote/main:scripts/
        git commit -m "feat(consolidation): subtree-merge <source>-service into strategy_service/<sub>/"
        ```
        Each subtree-merge is ONE commit per source repo (3 total). Verify with `git log --follow
        strategy_service/risk/<file>` that history pre-merge is reachable. **Foot-gun**: subtree-merge does NOT
        rewrite import statements inside the merged code — `strategy_service/risk/__init__.py` still imports
        `from risk_and_exposure_service.core import ...` until Phase 4. QG WILL fail between Phase 3 and Phase 4;
        this is expected. Keep Phase 4 in the same agent turn.
        — strategy-service@92515fde (risk) @cb200745 (position) @c67fb13d (pnl) @544edf80 (merge) 2026-05-19;
          history reachable via 92515fde^2 (risk-remote tab/5 HEAD ba2eb788)
    status: done
    blocked_by: phase-2-skeleton

  - id: phase-4-fix-imports-and-cli
    content: |
      - [x] ✅ [AGENT] P0. Phase 4 — Fix internal imports + unify CLI + collapse `api/main.py` per sub-package into
        single Health-API router. Per Phase 0 (b) manifest:
        (a) sed-rewrite every `from risk_and_exposure_service.*` → `from strategy_service.risk.*` (and similar for
            position + pnl) inside the merged tree;
        (b) collapse the 3 source `cli/main.py` entrypoints into `strategy_service/cli/main.py` dispatcher keyed by
            `--operation`; preserve every existing CLI flag verbatim (`--asset-group`, `--mode`, `--operation`,
            domain-specific flags) — operators have wired flags into existing launchers, breaking the contract
            blocks the cutover;
        (c) consolidate the 3 source `api/main.py` Health-API routers into strategy-service's existing router with
            sub-paths (`/health/risk`, `/health/position`, `/health/pnl`, `/health/strategy`); per-surface
            `data_freshness` callbacks merge into a single `make_health_router` call;
        (d) merge `config_reloaders.py` per source repo into strategy-service's typed-config class (one config
            namespace per surface, all under a single `StrategyServiceConfig` root);
        (e) consolidate per-repo `ServiceBootstrap` invocations into ONE `ServiceBootstrap` at strategy-service
            top level (STARTED / STOPPED / FAILED events at the consolidated-service level; per-surface
            sub-bootstraps if needed for granular kill-switch routing);
        (f) merge per-repo `tests/conftest.py` fixtures — resolve fixture-name collisions by prefixing
            (`risk_<fixture>`, `position_<fixture>`, etc.);
        (g) run `bash scripts/quality-gates.sh` in strategy-service repo — every QG step must pass. Specifically:
            STEP 5.61 ServiceBootstrap, STEP 5.62 api/main.py + make_health_router, STEP 5.34 typed config_reloaders,
            STEP 5.66 per-VM shard isolation, STEP 5.69 bucket-name SSOT.
        **PYTEST_UNIT_DIR**: strategy-service may need `PYTEST_UNIT_DIR="tests/"` after merge — `find tests/unit/ -name
        'test_*.py' | wc -l` < 5% of `find tests/ -name 'test_*.py' | wc -l` triggers the override. Verify post-merge.
        Push to `live-defi-rollout` only when QG green.
    status: todo
    blocked_by: phase-3-subtree-merge

  - id: phase-5-lifts-to-utl
    content: |
      - [ ] **DEFERRED** [AGENT] P1. Phase 5 — Lift cross-cutting helpers to UTL. Phase 0 (f) audit confirmed ≥2
        candidates: `config_reloaders.py` 4× + `kill_switch_bus_subscriber.py` 4×. Deferred to post-cutover:
        - UTL is a shared dep; changing it 4 days before May-23 live DeFi launch is unacceptable risk.
        - Lifts are correctness-neutral (plan §) — deduplicated copies already within strategy-service sub-packages.
        - Named successor: `plans/active/utl_lift_config_reloader_kill_switch_post_cutover.md` (to be created post May-23).
        - Required lifts when successor plan runs: `make_config_reloader(config_cls)` + `make_kill_switch_subscriber(on_fire, on_clear)` into UTL; strategy-service 4× callsites each.
    status: deferred
    blocked_by: phase-4-fix-imports-and-cli

  - id: phase-6-parity-test
    content: |
      - [x] ✅ [AGENT] P0. Phase 6 — Symmetry / parity validation BEFORE archive. — strategy-service@91f701b0
        (1) **Boot parity** ✅: all 12 {operation × asset_group} pairs EXIT=0, ~6-15s each (baseline ~14s; no >2×
            regression). Operations: risk-monitor, position-recon, pnl-attribution × cefi/defi/tradfi/prediction.
        (2) **QG parity** ✅: 4059 passed, 316 skipped, 0 errors (strategy-service@04f88fc7, Phase 4 gate).
        (3) **Functional parity** ⏳ PENDING-OPERATOR: `scripts/dev/strategy_parity_diff.py` shipped @91f701b0.
            Requires operator to run:
              `python scripts/dev/strategy_parity_diff.py --gate functional --surface all \`
              `    --baseline-dir gs://BUCKET/baselines/ --consolidated-dir gs://BUCKET/strategy-service/`
            against GCS pre-archive snapshots from source repos BEFORE Phase 7 archive executes.
            Boot + QG gates green → safe to proceed to Phase 7 operator actions; functional run is the
            final pre-cutover confirmation (operator-owned, not a blocker for Phase 7 operator kick-off).
    status: done
    blocked_by: phase-4-fix-imports-and-cli

  - id: phase-7-archive-source-repos
    content: |
      - [ ] [HUMAN+AGENT] P0. Phase 7 — Archive the 3 source repos. Per-repo sequence (operator runs `gh` archive):
        1. Add `DEPRECATION_NOTICE.md` banner: "**ARCHIVED 2026-05-XX** — code merged into strategy-service via
           strategy_repo_consolidation_2026_05_19.md. New work + bug fixes go to
           strategy-service/strategy_service/<risk|position|pnl>/."
        2. Final commit: `chore(archive): merged into strategy-service per strategy_repo_consolidation_2026_05_19`.
           Push to main.
        3. `gh repo archive IggyIkenna/<repo> --confirm` (operator action; shared-state gate — agent files ping in
           `_agent_pings.md` requesting operator execution).
        4. Remove from `unified-trading-system-repos.code-workspace` folders list.
        5. Remove from `workspace-manifest.json` repo registry; mark
           `status=consolidated-into-strategy-service`, `archived_into=strategy-service`, `archive_date=<date>`.
        6. Update `unified-trading-pm/scripts/dev/setup-tab-worktrees.sh` if 3 source repos enumerated explicitly.
        7. Verify `gh api repos/IggyIkenna/<repo> --jq .archived` returns `true` for all 3.
        **Foot-gun**: do NOT archive before Phase 6 parity green — archived repos are read-only and rollback path
        requires un-archiving via operator action.
    status: todo
    blocked_by: phase-6-parity-test

  - id: phase-8a-launcher-migration
    content: |
      - [ ] [AGENT] P0. Phase 8A — Launcher migration in `deployment-service/scripts/vm/`. Every
        `launch-<risk|position|pnl>-vm.sh` collapses into the existing `launch-strategy-vm.sh` parameterised by
        `--operation`. Update `VM_PREFIX_TO_BUCKET` in `vm_zombie_watchdog.py` to remove dropped prefixes. Update
        Cloud Build refresh-tarballs config (`cloud-build/refresh-tarballs.cloudbuild.yaml`) to remove the 3 source
        services (strategy-service tarball now covers all 4 surfaces). Update Terraform service map
        (`terraform/cloud-build/gcp/main.tf`) — drop 3 entries, expand strategy-service to all operations.
    status: todo
    blocked_by: phase-7-archive-source-repos

  - id: phase-8b-deployment-api-ui
    content: |
      - [ ] [AGENT] P0. Phase 8B — `deployment-api` + `deployment-ui` updates. Service registry endpoints
        (`/services/list`, `/services/<id>/health`) update to remove the 3 source service IDs and expose
        per-operation health on strategy-service. DART drilldown UI updates for risk-monitor + position-recon +
        pnl-attribution surfaces to point at strategy-service health endpoints. Update `MinimalCandidateManifest`
        Firestore consumers if any reference `risk_and_exposure_service` / etc. by name (Phase 0 (h) finding).
    status: todo
    blocked_by: phase-7-archive-source-repos

  - id: phase-9-codex-ssot-updates
    content: |
      - [ ] [AGENT] P0. Phase 9 — Codex SSOT updates. MANDATORY per HARD RULE "Post-Plan-Phase Codex Audit":
        (a) **NEW** `codex/04-architecture/strategy-service-architecture.md` — full SSOT covering: 4 sub-packages
            (strategy + risk + position + pnl), CLI dispatch keyed by `--operation`, Health-API aggregator,
            kill-switch subscriber topology, ServiceBootstrap consolidation, V2 strategies + portfolio allocator +
            signal broadcast surfaces, deployment topology (single VM per asset-group flavor), migration history
            cross-link to this plan, anti-patterns (do NOT re-introduce per-surface repos).
        (b) **UPDATE** `codex/00-SSOT-INDEX.md` — register new architecture page; drop 3 archived repos from
            service index; mark `archived_into=strategy-service` per source.
        (c) **UPDATE** `codex/04-architecture/promote-workflow-architecture.md` — strategy-service is the promote
            target; clarify risk/position/pnl now invoked via `--operation` on the same image.
        (d) **UPDATE** `codex/05-infrastructure/launcher-script-ssot.md` — 4-to-1 launcher collapse (single
            `launch-strategy-vm.sh` parameterised by `--operation` + `--asset-group`).
        (e) **UPDATE** `codex/05-infrastructure/vm-tarball-deployment.md` — single strategy-service tarball
            replaces 4-source-repo tarball matrix.
        (f) **UPDATE** `codex/06-coding-standards/cli-convention.md` — add `--operation` sub-command table for
            strategy-service's 6+ operations.
        (g) **UPDATE** `codex/09-strategy/operational/cli-promote-paths.md` — promote-CLI now invokes
            `strategy-service --operation strategy-live`; legacy `risk-and-exposure-service` reference removed.
        (h) **UPDATE** any other codex page surfaced by `rg "risk-and-exposure-service|position-balance-monitor-service|pnl-attribution-service" codex/`
            — replace with `strategy-service/<sub>/` or add SUPERSEDED banner. Enumerate exhaustively before
            marking Phase 9 done.
    status: todo
    blocked_by: phase-8a-launcher-migration

  - id: phase-10-workspace-qg-sweep
    content: |
      - [ ] [AGENT] P0. Phase 10 — Workspace QG sweep + cross-plan coordination banner cleanup. Run
        `bash scripts/quality-gates.sh` in every workspace repo (or scoped to repos Phase 0 (b) identified as
        having any reference). Run inventory regenerator
        (`python3 unified-trading-pm/scripts/plans/regenerate_active_plan_inventory.py`). Remove "🟡 IN-FLIGHT
        REFACTOR" banners added in pre-plan-Phase-0 announcement (Phase 0 side-effect) from affected active plans.
        Verify deployment-service end-to-end smoke (strategy-service VM boots, completes `--operation
        risk-monitor` run, STOPPED event emitted, manifest row written). Final commit + push + plan-flip
        sweep.
    status: todo
    blocked_by: phase-9-codex-ssot-updates

  - id: phase-0-side-effect-soft-freeze-announcement
    content: |
      - [x] ✅ [AGENT] P0. Phase 0 SIDE EFFECT — Cross-plan soft-freeze announcement. Add coordination banner to
        every active plan identified in fact-report (2026-05-19) as having scope over the 4 affected repos
        (~12 plans with `repo_gates`, ~34 with passing mentions). Banner text:
        ```
        > **🟡 IN-FLIGHT REFACTOR — strategy-repo-consolidation-2026-05-19** —
        > strategy-service is absorbing risk-and-exposure-service + position-balance-monitor-service +
        > pnl-attribution-service as sub-packages 2026-05-19 → 2026-05-23. **Soft freeze**: NO new public-API
        > surfaces, NO new top-level packages, NO module renames in any of the 4 repos until Phase 7 archive
        > lands. Internal bugfixes + test work + plan-flip backfills continue. See plan body for the 12 affected
        > plans + Phase 4 import-rewrite path.
        ```
        Banner-remove owned by this plan's Phase 10. Affected plan list per fact-report — enumerate in the Phase 0
        pre-audit artifact and link from each banner.
        RESULT (2026-05-19 slot-8): 20 plans patched — AUDIT_2026_05_15_harsh_side_completion, alerting_service_live_rules, batch_live_symmetry, bucket_name_ssot_canonicalisation, codex_vs_citadel_infrastructure_audit, compute_optimization_mock_data, cross_cutting_may_23_deliverables, defi_archetypes_canonicalisation_and_venue_matrix, defi_master, defi_recursive_borrow_archetypes, deployment_and_qg_strategy_implementation, features_repo_consolidation, features_service_qg_cleanup, live_pipeline_mtds_mdps_features, master_to_live_defi, ml_repo_consolidation, mock_data_pipeline_benchmarking, promote_workflow_may23_cli_path, ruff_workspace_cleanup, writegate_honest_coverage_endtoend.
    status: done
---

> **🟡 IN-FLIGHT REFACTOR — ml-repo-consolidation-2026-05-19** — ml-training-service + ml-inference-service are being
> merged into new `ml-service` repo 2026-05-19 → 2026-05-23. **Soft freeze**: NO new public-API surfaces, NO new
> top-level packages, NO module renames in either source repo until Phase 7 archive lands. Internal bugfixes + test
> work + plan-flip backfills continue.

## Architecture sketch — post-merge strategy-service

```
strategy-service/
├── strategy_service/
│   ├── __init__.py
│   ├── api/main.py                  # aggregated Health-API: /health/{risk,position,pnl,strategy}
│   ├── cli/main.py                  # dispatcher: --operation {risk-monitor,position-recon,pnl-attribution,
│   │                                #                          strategy-batch,strategy-live,backtest}
│   ├── config_reloaders.py          # single typed StrategyServiceConfig root, sub-namespaces per surface
│   ├── engine/                      # existing strategy core (unchanged)
│   ├── engine/strategies/v2/        # existing 12+ V2 strategies (unchanged)
│   ├── portfolio_allocator/         # existing (unchanged)
│   ├── signal_broadcast/            # existing (unchanged)
│   ├── risk/                        # NEW — was risk-and-exposure-service/
│   │   ├── core/                    # alert_manager, risk_calculator, position_monitor_client
│   │   ├── engine/                  # orchestrator
│   │   └── v2/                      # margin_sim, orchestrator, preflight
│   ├── position/                    # NEW — was position-balance-monitor-service/
│   │   ├── core/                    # 13 modules (balance + pnl + position + nav + fee reconciliation)
│   │   ├── storage/                 # database + position_store
│   │   └── v2/                      # attribution, invariants, projections
│   └── pnl/                         # NEW — was pnl-attribution-service/
│       ├── engine/                  # breakdown, archetype_aggregator, sports_pnl, reward_attribution_drain
│       ├── analytics/
│       └── execution_alpha/
├── tests/{risk,position,pnl,strategy}/
└── scripts/{risk,position,pnl,strategy}/
```

## Cutover-race risk acknowledgement

Deadline 2026-05-23 with 12 calibrated AI-days across 16 slots (8×2) = ~0.75 cal-days per slot if perfectly
parallelized. **Feasible but tight** given strategy-service is the workspace's largest service (35+ V2 strategies,
224-line pyproject). Risk register:

| Risk                                                                      | Mitigation                                                                                                                                                       |
| ------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 6 parity slips → archive cannot proceed pre-cutover                 | Plan auto-flips to `BLOCKED-CUTOVER`; sub-packages remain in strategy-service (functional), source repos remain alive (un-archived); resume Phase 7 post-cutover |
| Hidden cross-repo import surfaces Phase 0 misses                          | Phase 0 (b) grep is exhaustive across `${WORKSPACE_ROOT}`; verification via `rg` in Phase 4 (g); QG STEP-by-STEP comparison vs source-repo baselines             |
| `pyproject.toml` dep-version conflicts                                    | Phase 0 (g) resolves ahead of Phase 3; if any conflict can't be reconciled cleanly, the affected sub-package stays as separate repo (graceful degradation)       |
| `MinimalCandidateManifest` Firestore consumers hardcode old service names | Phase 0 (h) + Phase 8B; cutover Promote workflow tested against new endpoints before archive                                                                     |
| Other agents' in-flight work in the 4 repos                               | Soft-freeze banner (Phase 0 side-effect) on 12 affected plans; structural changes paused, internal work continues                                                |

## Notes / Context

- **Precedent**: `plans/active/features_repo_consolidation_2026_05_08.md` — 8-source-repo merge into `features-service`,
  shipped 2026-05-08 → 2026-05-11. Same 10-phase shape; parity gate deferred but utility script shipped. This plan
  re-uses the phase sequence verbatim, adjusts Phase 1 (no new UAC enum needed — risk/position/pnl already independent
  data types), adjusts Phase 2 (in-place vs fresh-repo per operator decision 2026-05-19), tightens Phase 6 parity gate
  (not deferrable for the operationally-critical promote-workflow path).
- **Cross-repo import audit (fact-report 2026-05-19)**: ZERO Python imports between any of the 4 repos today — services
  communicate via event-bus / pub-sub / shared UAC contracts. Subtree-merge is collision-free at compile time.
  Operational coupling is via kill-switch events + position-monitor-client calls; these become in-process function calls
  post-merge (latency win, no semantic change).
- **Operator confirmation 2026-05-19**: in-place merge into existing strategy-service (NOT fresh repo); soft freeze (NOT
  hard); race the 2026-05-23 cutover; fold under existing `strategy_and_dart_master_2026_05_07` epic (NOT new standalone
  epic). Operator + colleague aligned on approach.
- **ML twin plan**: `plans/active/ml_repo_consolidation_2026_05_19.md` mirrors this pattern for the
  ml-training-service + ml-inference-service merge into new `ml-service` repo. Independent execution; both target same
  2026-05-23 deadline.

## Full-Execution Criterion (PLAN_FORMAT § 8)

Plan is complete when **all 3 source repos are GitHub-archived** (`gh api ... .archived == true`) AND **strategy-service
deployment-service tarball boots through all 6 `--operation` modes** on a real VM AND **DART UI service-list shows
strategy-service as single entry with 4 health-endpoints** AND **codex Phase 9 SSOT-INDEX registers
`strategy-service-architecture.md`**. Boot parity captured at deployment registry. Smoke-test green is NOT sufficient —
operational completion required per "Plans Run To Actual Completion" HARD RULE.

## Phase 0 audit findings — folded in 2026-05-19

Pre-audit artifact:
[`plans/active/issues/strategy_repo_consolidation_preaudit_2026_05_19.md`](./issues/strategy_repo_consolidation_preaudit_2026_05_19.md)
(735 lines). New plan todos extracted below; risk register sharpened.

### Corrections to plan assumptions

- **🔴 Phase 4 (a) sed-rewrite scope materially expanded**: original plan asserted "Fact-report 2026-05-19 showed ZERO
  cross-repo Python imports". Pre-audit found **25 import statements across 7 files in 5 sibling repos**, including TWO
  production consumers (`deployment-api/deployment_api/routes/treasury_routes.py`,
  `execution-service/execution_service/algo_library/leg_controller_runner.py`) AND
  `e2e-testing/scripts/defi/colocated_engine.py` — the **primary May-23 promote-CLI path** per CLAUDE.md. Phase 4 (a) is
  no longer trivial; it has cutover-critical path consumers. Exact file:line list in artifact § (b).
- **`ManifestFreshnessCache` adoption is N/A** — none of the 4 repos use it. Drop from Phase 5 scope; keep only
  ServiceBootstrap + kill-switch subscriber + config_reloaders lifts.
- **Kill-switch event taxonomy is already UAC-canonical** — Phase 1 confirms 0-PR scope. Only the subscriber boilerplate
  (~80-100 LOC × 4) needs UTL lift in Phase 5.

### New todos (P0/P1 cutover-critical, P2/P3 nice-to-have)

- [x] ✅ **P0** [AGENT] Phase 4 (a) rewrite the 7 external-consumer files identified in artifact § (b). Order: (1)
      `e2e-testing/scripts/defi/colocated_engine.py` FIRST (primary May-23 promote-CLI path; cutover-critical), (2)
      `deployment-api/deployment_api/routes/treasury_routes.py`, (3)
      `execution-service/execution_service/algo_library/leg_controller_runner.py`, (4-7) test files. Each rewrite is
      `from <old_pkg> X` → `from strategy_service.<sub> X`. Verify each consumer boots green BEFORE archiving source
      repos in Phase 7. — ✅ strategy-service@1da6743b + system-integration-tests@0b20329 + prior slots (2026-05-19)
- [x] ✅ **P0** [AGENT] Phase 0.5 (NEW — sequencing fix) Resolve `pyproject.toml` conflicts (artifact § (g)) BEFORE
      Phase 3 subtree-merge: unify `unified-trading-library>=0.3.0`, `uvicorn[standard]>=0.29.0`, drop pnl's
      `pre-commit` in favour of `prek>=0.3.0`. Carry over editable `[tool.uv.sources.market-tick-data-service]` from
      PBM. Land as a single strategy-service `pyproject.toml` PR before Phase 3. — ✅ strategy-service@eee8bbb
      (2026-05-19, another slot; dep union + editable source confirmed in pyproject.toml)
- [ ] **P0** [DECISION] Topic-prefix compatibility decision — pre-audit (h) recommends **KEEP legacy topic prefixes**
      (`risk-monitor.*`, `position-monitor.*`, `pnl-attribution.*`) for first 7 days post-cutover to avoid double-rebind
      race during the live trading window. Rename via follow-up plan. Operator confirm — default YES unless
      cross-cutting reason to rename atomically.
- [x] ✅ **P0** [AGENT] Phase 4 (g) verify `PYTEST_UNIT_DIR="tests/"` override applied — PBM's
      `tests/position_interface/unit/` layout triggers the per-family rule per CLAUDE.md. Without it the merged
      strategy-service QG silently skips position-recon unit tests. — ✅ strategy-service@1da6743b (2026-05-19);
      multi-dir override `tests/unit/ tests/risk/unit/ tests/position/unit/ tests/pnl/unit/` in scripts/quality-gates.sh
- [x] ✅ **P1** [AGENT] Phase 4 cleanup — remove `try/except ImportError` guards from
      `system-integration-tests/tests/smoke/test_sports_arb_pipeline.py` (banned per CLAUDE.md
      `.cursor/rules/no-empty-fallbacks.mdc`); imports become unconditional intra-package post-merge. — ✅
      system-integration-tests@0b20329 (2026-05-19)
- [ ] **P1** [AGENT+DECISION] Architectural-collision resolution — existing `strategy_service/models/position.py` +
      `strategy_service/models/pnl.py` will coexist with new `strategy_service/{position,pnl}/` sub-packages. Symbols
      don't collide but layout confuses readers. Decide in Phase 4 (a): (i) absorb existing models into sub-packages
      (preferred), (ii) keep both with cross-link comments, (iii) rename existing to
      `strategy_service/models/legacy_*.py`. Not cutover-blocking.
- [ ] **P1** [AGENT] Phase 8A sharpening — deployment-service blast radius is **~90 hits across Terraform (6 per-service
      dirs on GCP + AWS), cloud-build, cluster configs, bucket configs, launchers, bootstrap scripts**. Phase 8A is the
      LARGEST single-repo edit in this plan. Plan `terraform destroy` of the 3 retiring service modules in conjunction
      with `terraform apply` of the updated strategy-service module — do NOT leave orphan Terraform-managed resources
      after archive.
- [ ] **P1** [AGENT] Phase 5 lifts sharpened — `config_reloaders.py` is duplicated 4× (152/112/112/312 LOC, total ~688
      LOC) and is a clean UTL `ConfigReloaderBase` candidate. Kill-switch bus subscriber boilerplate is duplicated 4×
      (~80-100 LOC each) and is a clean UTL `KillSwitchBusSubscriberBase` candidate. Both confirmed by artifact § (f).
      Ship as 2 UTL PRs in Phase 5.
- [ ] **P2** [AGENT] Console-script command-name compatibility — the 3 source repos define `[project.scripts]` entries
      (`risk-monitor`, `position-monitor`, `position-monitor-std`, `pnl-attribution`, `pnl-attribution-std`).
      Post-merge: collapse to `python -m strategy_service --operation <op>`. Audit any launcher / cron / VM bootstrap
      script invoking the legacy command names; rewrite in Phase 8A.

### Gap-close 2026-05-19 — coverage amendments (post-dispatch audit)

Operator-validation question 2026-05-19 surfaced 4 gaps in the original 10-phase scope. Closing them now (before
slot-3/4/7/9 boot) is cheaper than discovering them mid-Phase-4 or post-archive.

- [ ] **P0 NEW** [AGENT slot 4] Phase 4 (a-extension) — e2e-testing scripts beyond Python imports. Phase 4 (a) currently
      covers the 7 `import`-consumer files from pre-audit § (b). Add: grep
      `e2e-testing/scripts/{defi,sports,prediction}/`
  - `system-integration-tests/scripts/` + `e2e-testing/scripts/*.sh` for (i) shell invocations of
    `python -m {risk_and_exposure,position_balance_monitor,pnl_attribution}_service`, (ii) console-script names
    (`risk-monitor`, `position-monitor`, `pnl-attribution`, etc.), (iii) bare-Python entry-point invocations. Rewrite to
    `python -m strategy_service --operation <op>`. Slot 4 extends Phase 4 (a) by ~0.5 cal-day.
- [ ] **P0 NEW** [AGENT slot 7] Phase 8A — Console-script alias audit (PROMOTED from P2 to P0). Source repos define
      `[project.scripts]`: `risk-monitor`, `position-monitor`, `position-monitor-std`, `pnl-attribution`,
      `pnl-attribution-std`. These are invoked by name in deployment-service launchers, cron schedules, VM bootstrap
      scripts, e2e-testing scripts, docs. **Decision: full cutover, no shim aliases in strategy-service
      `[project.scripts]`** — launchers + cron are workspace-owned and rewriting them is the cleanest path. Slot 7
      bundles this into Phase 8A launcher migration; ~0.5 cal-day extension.
- [ ] **P1 NEW** [AGENT slot 4] Phase 4 (i) — Logging + observability config consolidation. Per-service `setup_events()`
      callsites + log levels + formatters + structured-log field naming. Decide: per-sub-package logger naming
      (`strategy_service.risk` / `strategy_service.position` / `strategy_service.pnl` / `strategy_service.engine`) for
      filterability. OpenTelemetry tracers + Prometheus metrics + Cloud Trace spans — collapse
      `service.name=<source-repo>` labels to `service.name=strategy-service` and add
      `subsurface={risk,position,pnl,strategy}` label dimension. ServiceBootstrap in Phase 4 (e) already covers
      lifecycle-event emission; this is the parallel pass for log + metric + trace infra. Slot 4 extends Phase 4 by ~0.5
      cal-day.
- [x] ✅ **P2 NEW** [AGENT slot 3] Phase 3 addendum — Drop source-repo `docs/` subdirectories during subtree-merge.
      `git read-tree --prefix=strategy_service/<sub>/ -u <source>-remote/main:<source_package>/` pulls package + tests +
      scripts only; `docs/` intentionally NOT merged (codex is workspace SSOT). Record in each archived source repo's
      `DEPRECATION_NOTICE.md` (Phase 7): "docs/ content not migrated — see
      `codex/04-architecture/strategy-service-architecture.md` and related codex pages." 1-line addendum to Phase 3
      recipe; <5 min work. — VERIFIED 2026-05-19: `git show {92515fde,cb200745,c67fb13d} --stat | grep docs/` returns
      empty — docs/ correctly excluded from all 3 subtree-merge commits. Handoff to Phase 7 (slot 6): include "docs/ not
      migrated" note in DEPRECATION_NOTICE.md per above.
- [ ] **P2 NEW** [AGENT slot 7] Phase 8A addendum — GitHub Actions workflows in source repos going dark. Each archived
      repo carries ~9 workflow files (~27 total across risk + position + pnl). Most are templated copies
      (`workspace-qg.yml`, `semver-agent.yml`, `staging-lock-check.yml`, `tab-mirror-to-ldr.yml`) that strategy-service
      already has via `rollout-workflow-templates.sh` — those just go dark with the repo, no action needed. **Audit
      task**: enumerate any per-repo CUSTOM workflows (cron-scheduled checks, scheduled data-pulls, scheduled
      VM-launchers) that AREN'T templated. For each: (a) migrate the cron schedule to a strategy-service workflow with
      `--operation` axis, OR (b) confirm the workflow's purpose is obsolete post-merge. Slot 7 ownership; ~0.5 cal-day.
      Workflow templates SSOT: `unified-trading-pm/scripts/workflow-templates/`.
- [x] ✅ **P3 NEW** [AGENT slot 6] Phase 7 addendum — Per-repo markdown files (CHANGELOG.md / QUALITY_GATE_BYPASS_AUDIT.md
      / IMPLEMENTATION_VERIFICATION.md / UV_AND_DATABASE_UPDATES.md / QUALITY_GATES_REPORT.md). Each source repo has
      these. Post-merge decision: (a) `CHANGELOG.md` content prepended to `strategy-service/CHANGELOG.md` under "##
      Consolidation 2026-05-19" heading; (b) `QUALITY_GATE_BYPASS_AUDIT.md` content merged into strategy-service's QGBA
      per service-sub-package row; (c) `IMPLEMENTATION_VERIFICATION.md` + `QUALITY_GATES_REPORT.md` + ad-hoc per-repo
      markdown — dropped (one-shot audit snapshots, not load-bearing). Slot 6 owns this as Phase 7 cleanup (~0.25
      cal-day). — strategy-service@607a411b (CHANGELOG created + 158 QGBA rows merged from all 3 source repos; 2026-05-19)
- [ ] **P3 NEW** [AGENT slot 7] Phase 8A addendum — GitHub repo settings (branch protection rules + required status
      checks + semver-agent config) on archived source repos do NOT auto-migrate. strategy-service ALREADY has its own
      settings — verify post-archive that strategy-service required-checks reflects the consolidated workflow set (no
      orphan required-check names pointing at archived repos' workflows). Slot 7 owns as Phase 8A finalisation (~0.1
      cal-day; usually a 1-line `gh api repos/.../branches/main/protection -X PATCH` if any drift found).

**Total gap-close additions**: ~2.35 cal-AI-days bundled into existing slots (no new slot needed). Slot 3 +0.05, slot 4
+1, slot 6 +0.25, slot 7 +1.1.

### Risk register additions (post-audit)

| Risk                                                                               | Severity  | Mitigation                                                                                                                             |
| ---------------------------------------------------------------------------------- | --------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 4 (a) sed-rewrite breaks `colocated_engine.py` mid-cutover                   | 🔴 High   | Rewrite `colocated_engine.py` FIRST in Phase 4 (a); run paper-trade smoke before continuing; gate Phase 7 archive on cutover-CLI green |
| Phase 8A Terraform destroy/apply sequencing error leaves orphan resources          | 🟡 Medium | Phase 8A todo above; pre-flight `terraform plan` per module; staged-merge per asset_group                                              |
| pyproject conflicts cause Phase 3 subtree-merge to fail or build flat-broken image | 🟡 Medium | Phase 0.5 (above) resolves explicitly BEFORE Phase 3                                                                                   |
| Topic-prefix rename race during live trading window                                | 🟡 Medium | KEEP legacy prefixes for 7 days; named-successor plan for rename                                                                       |
| Existing `strategy_service/models/{position,pnl}.py` layout confusion              | 🟢 Low    | P1 architectural resolution; not cutover-blocking                                                                                      |

## Codex SSOT updates (mandatory enumeration — HARD RULE)

See Phase 9 — 8 enumerated codex paths (a-h). Plan-review-blocking if Phase 9 ships without all 8 verified.
